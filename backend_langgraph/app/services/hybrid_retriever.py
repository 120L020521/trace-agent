"""证据检索底座：BM25 + dense embedding + RRF 融合。

默认使用可离线运行的稳定哈希向量；安装 sentence-transformers 且开启
USE_SENTENCE_TRANSFORMERS 后切换为神经网络语义向量。索引以 JSON 持久化，
适合个人旅行资料这种中小规模知识库，也方便在面试中完整解释检索链路。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np


_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text: str) -> List[str]:
    """兼顾中英文的无外部分词依赖 tokenizer。"""
    normalized = text.lower()
    tokens = _WORD_RE.findall(normalized)
    for block in _CJK_RE.findall(normalized):
        tokens.extend(block)
        tokens.extend(block[i : i + 2] for i in range(len(block) - 1))
    return tokens


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: List[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            chunks.append(buffer)
            prefix = buffer[-overlap:]
            buffer = f"{prefix}\n{paragraph}".strip()
        else:
            step = max(1, chunk_size - overlap)
            chunks.extend(paragraph[i : i + chunk_size] for i in range(0, len(paragraph), step))
            buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks


@dataclass
class KnowledgeChunk:
    source_id: str
    source_name: str
    chunk_id: str
    text: str
    media_type: str = "text/plain"
    metadata: dict | None = None


@dataclass
class RetrievalHit:
    source_id: str
    source_name: str
    chunk_id: str
    text: str
    score: float
    lexical_rank: Optional[int] = None
    semantic_rank: Optional[int] = None


class _HashEmbedding:
    """可复现、零下载的回退 embedding，用于本地开发和单测。"""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        rows = []
        for text in texts:
            vector = np.zeros(self.dimensions, dtype=np.float32)
            for token in tokenize(text):
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                raw = int.from_bytes(digest, "little")
                vector[raw % self.dimensions] += 1.0 if raw & 1 else -1.0
            norm = float(np.linalg.norm(vector))
            rows.append(vector / norm if norm else vector)
        return np.vstack(rows) if rows else np.empty((0, self.dimensions), dtype=np.float32)


class _SentenceTransformerEmbedding:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(list(texts), normalize_embeddings=True),
            dtype=np.float32,
        )


class HybridRetriever:
    """中小规模资料库的可持久化混合检索器。"""

    def __init__(self, index_path: Optional[Path] = None):
        default_path = Path(__file__).resolve().parents[2] / "data" / "knowledge_index.json"
        self.index_path = Path(index_path or os.getenv("KNOWLEDGE_INDEX_PATH", default_path))
        self._lock = threading.RLock()
        self.chunks: List[KnowledgeChunk] = []
        self._embedding = self._create_embedding_backend()
        self._dense_matrix = np.empty((0, 384), dtype=np.float32)
        self._load()

    @staticmethod
    def _create_embedding_backend():
        if os.getenv("USE_SENTENCE_TRANSFORMERS", "false").lower() == "true":
            model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
            try:
                return _SentenceTransformerEmbedding(model_name)
            except Exception as exc:
                print(f"⚠️ 语义模型加载失败，使用离线哈希向量: {exc}")
        return _HashEmbedding()

    def _load(self) -> None:
        if not self.index_path.exists():
            return
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.chunks = [KnowledgeChunk(**item) for item in payload.get("chunks", [])]
        self._rebuild_dense_matrix()

    def _persist(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.index_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps({"version": 1, "chunks": [asdict(item) for item in self.chunks]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.index_path)

    def _rebuild_dense_matrix(self) -> None:
        self._dense_matrix = self._embedding.encode(chunk.text for chunk in self.chunks)

    def add_document(
        self,
        source_name: str,
        text: str,
        media_type: str = "text/plain",
        metadata: Optional[dict] = None,
    ) -> tuple[str, int]:
        source_id = hashlib.sha256(f"{source_name}\n{text}".encode("utf-8")).hexdigest()[:16]
        pieces = chunk_text(text)
        if not pieces:
            raise ValueError("资料中没有可索引文本")
        with self._lock:
            self.chunks = [chunk for chunk in self.chunks if chunk.source_id != source_id]
            self.chunks.extend(
                KnowledgeChunk(
                    source_id=source_id,
                    source_name=source_name,
                    chunk_id=f"{source_id}-{index:03d}",
                    text=piece,
                    media_type=media_type,
                    metadata=metadata or {},
                )
                for index, piece in enumerate(pieces)
            )
            self._rebuild_dense_matrix()
            self._persist()
        return source_id, len(pieces)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_ids: Optional[List[str]] = None,
    ) -> List[RetrievalHit]:
        with self._lock:
            candidates = [
                (index, chunk)
                for index, chunk in enumerate(self.chunks)
                if not source_ids or chunk.source_id in source_ids
            ]
            if not query.strip() or not candidates:
                return []

            lexical = self._bm25_scores(query, [chunk.text for _, chunk in candidates])
            query_vector = self._embedding.encode([query])[0]
            dense = np.asarray(
                [float(np.dot(self._dense_matrix[index], query_vector)) for index, _ in candidates]
            )

            lexical_order = np.argsort(-lexical)
            semantic_order = np.argsort(-dense)
            lexical_rank = {int(position): rank + 1 for rank, position in enumerate(lexical_order)}
            semantic_rank = {int(position): rank + 1 for rank, position in enumerate(semantic_order)}

            fused = {
                position: 1.0 / (60 + lexical_rank[position]) + 1.0 / (60 + semantic_rank[position])
                for position in range(len(candidates))
            }
            best = sorted(fused, key=fused.get, reverse=True)[:top_k]
            max_score = max(fused.values()) or 1.0
            return [
                RetrievalHit(
                    source_id=candidates[position][1].source_id,
                    source_name=candidates[position][1].source_name,
                    chunk_id=candidates[position][1].chunk_id,
                    text=candidates[position][1].text,
                    score=round(fused[position] / max_score, 4),
                    lexical_rank=lexical_rank[position],
                    semantic_rank=semantic_rank[position],
                )
                for position in best
            ]

    def list_chunks(self, source_ids: Optional[List[str]] = None) -> List[KnowledgeChunk]:
        """返回指定资料的有序原文块，供 Long Context 路由使用。"""
        with self._lock:
            return [
                KnowledgeChunk(**asdict(chunk))
                for chunk in self.chunks
                if not source_ids or chunk.source_id in source_ids
            ]

    @staticmethod
    def _bm25_scores(query: str, documents: List[str], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        tokenized = [tokenize(document) for document in documents]
        query_tokens = tokenize(query)
        lengths = [len(tokens) for tokens in tokenized]
        average_length = sum(lengths) / max(len(lengths), 1)
        document_frequency = Counter(
            token for tokens in tokenized for token in set(tokens)
        )
        scores = np.zeros(len(documents), dtype=np.float32)
        total = len(documents)
        for index, tokens in enumerate(tokenized):
            frequencies = Counter(tokens)
            for token in query_tokens:
                frequency = frequencies[token]
                if not frequency:
                    continue
                idf = math.log(1 + (total - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
                denominator = frequency + k1 * (1 - b + b * lengths[index] / max(average_length, 1))
                scores[index] += idf * frequency * (k1 + 1) / denominator
        return scores

    def stats(self) -> dict:
        source_ids = {chunk.source_id for chunk in self.chunks}
        return {
            "sources": len(source_ids),
            "chunks": len(self.chunks),
            "embedding_backend": type(self._embedding).__name__,
            "index_path": str(self.index_path),
        }


_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
