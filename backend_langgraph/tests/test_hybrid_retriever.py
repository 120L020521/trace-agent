from pathlib import Path

from app.services.hybrid_retriever import HybridRetriever


def test_hybrid_search_returns_grounded_source(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "false")
    retriever = HybridRetriever(tmp_path / "index.json")
    source_id, chunk_count = retriever.add_document(
        "北京攻略.md",
        "故宫博物院周一闭馆。建议提前预约，入口位于午门。\n\n颐和园适合半日游览。",
    )

    hits = retriever.search("故宫什么时候闭馆", top_k=2)

    assert chunk_count >= 1
    assert hits[0].source_id == source_id
    assert "周一闭馆" in hits[0].text
    assert hits[0].lexical_rank is not None
    assert hits[0].semantic_rank is not None


def test_source_filter_is_respected(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("USE_SENTENCE_TRANSFORMERS", "false")
    retriever = HybridRetriever(tmp_path / "index.json")
    beijing_id, _ = retriever.add_document("北京.txt", "故宫需要预约")
    shanghai_id, _ = retriever.add_document("上海.txt", "外滩夜景开放")

    hits = retriever.search("夜景", source_ids=[beijing_id])

    assert hits
    assert {hit.source_id for hit in hits} == {beijing_id}
    assert shanghai_id not in {hit.source_id for hit in hits}
