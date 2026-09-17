from pathlib import Path

from app.models.schemas import TripRequest
from app.services.evidence_orchestrator import EvidenceOrchestrator
from app.services.hybrid_retriever import HybridRetriever


def make_request(**updates) -> TripRequest:
    payload = {
        "city": "北京",
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "travel_days": 2,
        "transportation": "公共交通",
        "accommodation": "舒适型酒店",
        "preferences": ["历史文化"],
        "free_text_input": "希望参观博物馆",
        "max_daily_attractions": 3,
    }
    payload.update(updates)
    return TripRequest(**payload)


def test_no_private_material_routes_to_tools(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "false")
    orchestrator = EvidenceOrchestrator(HybridRetriever(tmp_path / "index.json"))

    bundle = orchestrator.collect(make_request())

    assert bundle.decision.strategy == "tool_first"
    assert bundle.decision.sufficient is True
    assert bundle.hits == []


def test_small_material_uses_complete_long_context(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "false")
    retriever = HybridRetriever(tmp_path / "index.json")
    source_id, chunk_count = retriever.add_document(
        "北京订单与攻略.md",
        "北京故宫适合历史文化旅行，故宫博物院周一闭馆，需要提前预约。\n\n用户希望参观博物馆。",
    )
    orchestrator = EvidenceOrchestrator(retriever, long_context_threshold=10_000)

    bundle = orchestrator.collect(make_request(knowledge_source_ids=[source_id]))

    assert bundle.decision.strategy == "long_context"
    assert bundle.decision.selected_chunks == chunk_count
    assert "周一闭馆" in bundle.context
    assert bundle.decision.coverage >= 0.6


def test_large_material_uses_multi_query_and_reports_rounds(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "false")
    retriever = HybridRetriever(tmp_path / "index.json")
    source_id, _ = retriever.add_document(
        "大型北京攻略.md",
        ("北京故宫历史文化博物馆需要预约，门票六十元。" * 80)
        + ("颐和园开放时间为早上九点，适合公共交通出行。" * 80),
    )
    orchestrator = EvidenceOrchestrator(retriever, long_context_threshold=100)

    bundle = orchestrator.collect(make_request(knowledge_source_ids=[source_id]))

    assert bundle.decision.strategy == "hybrid_multi_query"
    assert bundle.decision.retrieval_rounds in (1, 2)
    assert bundle.decision.selected_chunks > 0
    assert bundle.decision.queries

