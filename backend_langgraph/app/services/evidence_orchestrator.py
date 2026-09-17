"""Agentic Evidence Retrieval：在工具、长上下文与混合检索之间动态路由。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence

from ..models.schemas import TripRequest
from .hybrid_retriever import HybridRetriever, RetrievalHit, get_hybrid_retriever, tokenize


@dataclass
class EvidenceDecision:
    strategy: str
    rationale: str
    queries: List[str]
    retrieval_rounds: int
    source_count: int
    candidate_chunks: int
    selected_chunks: int
    context_chars: int
    coverage: float
    sufficient: bool
    missing_aspects: List[str]
    fallback_used: bool = False


@dataclass
class EvidenceBundle:
    context: str
    hits: List[RetrievalHit]
    decision: EvidenceDecision


class EvidenceOrchestrator:
    """根据资料规模和问题复杂度选择证据获取策略，并检查上下文充分性。"""

    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        long_context_threshold: int = 12_000,
        max_context_chars: int = 18_000,
    ):
        self.retriever = retriever or get_hybrid_retriever()
        self.long_context_threshold = long_context_threshold
        self.max_context_chars = max_context_chars

    def collect(self, request: TripRequest) -> EvidenceBundle:
        chunks = self.retriever.list_chunks(request.knowledge_source_ids or None)
        source_count = len({chunk.source_id for chunk in chunks})
        total_chars = sum(len(chunk.text) for chunk in chunks)
        queries = self._decompose_query(request)

        if not request.knowledge_source_ids:
            decision = EvidenceDecision(
                strategy="tool_first",
                rationale="未指定私有资料，动态事实交由地图和天气工具获取",
                queries=queries,
                retrieval_rounds=0,
                source_count=0,
                candidate_chunks=0,
                selected_chunks=0,
                context_chars=0,
                coverage=1.0,
                sufficient=True,
                missing_aspects=[],
            )
            return EvidenceBundle("本次未提供私有资料；动态事实必须以工具结果为准。", [], decision)

        if total_chars <= self.long_context_threshold:
            hits = [
                RetrievalHit(
                    source_id=chunk.source_id,
                    source_name=chunk.source_name,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=1.0,
                )
                for chunk in chunks
            ]
            strategy = "long_context"
            rationale = f"资料总量 {total_chars} 字符，低于阈值，保留完整上下文避免切块召回遗漏"
            rounds = 1
            fallback = False
        else:
            hits = self._multi_query_search(queries, request.knowledge_source_ids, top_k_per_query=3)
            strategy = "hybrid_multi_query"
            rationale = f"资料总量 {total_chars} 字符，采用查询拆解与 BM25/Dense 融合召回"
            rounds = 1
            fallback = False

        coverage, missing = self._context_sufficiency(request, hits)
        if strategy == "hybrid_multi_query" and coverage < 0.6:
            broad_query = self._broad_query(request)
            expanded = self.retriever.search(broad_query, top_k=10, source_ids=request.knowledge_source_ids)
            hits = self._merge_hits(hits, expanded)
            coverage, missing = self._context_sufficiency(request, hits)
            rounds = 2
            fallback = True
            rationale += "；首轮上下文不足，已触发宽召回补检索"

        hits = self._fit_context_budget(hits)
        context = "\n\n".join(
            f"[证据 {index + 1} | {hit.source_name} | {hit.chunk_id} | {strategy}]\n{hit.text}"
            for index, hit in enumerate(hits)
        )
        decision = EvidenceDecision(
            strategy=strategy,
            rationale=rationale,
            queries=queries,
            retrieval_rounds=rounds,
            source_count=source_count,
            candidate_chunks=len(chunks),
            selected_chunks=len(hits),
            context_chars=len(context),
            coverage=coverage,
            sufficient=coverage >= 0.6,
            missing_aspects=missing,
            fallback_used=fallback,
        )
        return EvidenceBundle(context or "未从指定资料中获得可用证据。", hits, decision)

    @staticmethod
    def _decompose_query(request: TripRequest) -> List[str]:
        queries = [f"{request.city} 景点 开放时间 地址 门票"]
        if request.preferences:
            queries.append(f"{request.city} {' '.join(request.preferences)} 推荐")
        if request.accessibility_needs:
            queries.append(f"{request.city} {' '.join(request.accessibility_needs)} 注意事项")
        if request.max_budget is not None:
            queries.append(f"{request.city} 预算 费用 交通 酒店 {request.max_budget}元")
        if request.free_text_input:
            queries.append(f"{request.city} {request.free_text_input}")
        return list(dict.fromkeys(queries))

    @staticmethod
    def _broad_query(request: TripRequest) -> str:
        return " ".join(filter(None, [request.city, "行程 攻略 预约 时间 费用", *request.preferences, *request.accessibility_needs, request.free_text_input or ""]))

    def _multi_query_search(self, queries: Sequence[str], source_ids: List[str], top_k_per_query: int) -> List[RetrievalHit]:
        ranked: Dict[str, tuple[float, RetrievalHit]] = {}
        for query in queries:
            for rank, hit in enumerate(self.retriever.search(query, top_k=top_k_per_query, source_ids=source_ids), start=1):
                bonus = hit.score + 1.0 / (20 + rank)
                previous = ranked.get(hit.chunk_id)
                if previous is None or bonus > previous[0]:
                    ranked[hit.chunk_id] = (bonus, hit)
        return [pair[1] for pair in sorted(ranked.values(), key=lambda item: item[0], reverse=True)]

    @staticmethod
    def _merge_hits(primary: List[RetrievalHit], secondary: List[RetrievalHit]) -> List[RetrievalHit]:
        merged = {hit.chunk_id: hit for hit in [*primary, *secondary]}
        return sorted(merged.values(), key=lambda hit: hit.score, reverse=True)

    def _fit_context_budget(self, hits: List[RetrievalHit]) -> List[RetrievalHit]:
        selected: List[RetrievalHit] = []
        used = 0
        for hit in hits:
            if selected and used + len(hit.text) > self.max_context_chars:
                continue
            selected.append(hit)
            used += len(hit.text)
        return selected

    @staticmethod
    def _context_sufficiency(request: TripRequest, hits: List[RetrievalHit]) -> tuple[float, List[str]]:
        corpus_tokens = set(tokenize(" ".join(hit.text for hit in hits)))
        aspects: Dict[str, str] = {"目的地": request.city}
        if request.preferences:
            aspects["旅行偏好"] = " ".join(request.preferences)
        if request.accessibility_needs:
            aspects["特殊约束"] = " ".join(request.accessibility_needs)
        if request.free_text_input:
            aspects["额外要求"] = request.free_text_input
        covered = []
        for name, text in aspects.items():
            aspect_tokens = set(tokenize(text))
            covered.append(bool(aspect_tokens & corpus_tokens))
        missing = [name for (name, _), ok in zip(aspects.items(), covered) if not ok]
        return (sum(covered) / len(covered) if covered else 1.0), missing


def decision_dict(bundle: EvidenceBundle) -> dict:
    return asdict(bundle.decision)

