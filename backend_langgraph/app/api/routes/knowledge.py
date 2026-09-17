"""个人旅行资料库 API。"""

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ...services.document_ingestion import extract_document
from ...services.hybrid_retriever import get_hybrid_retriever
from ...services.evidence_orchestrator import EvidenceOrchestrator, decision_dict
from ...models.schemas import TripRequest


router = APIRouter(prefix="/knowledge", tags=["多模态旅行知识库"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    source_ids: Optional[List[str]] = None


@router.post("/upload", summary="上传攻略、订单、票据或旅行笔记")
async def upload_knowledge(
    file: UploadFile = File(...),
    category: str = Form(default="travel-material"),
):
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="单个文件不能超过 10MB")
    try:
        text, extraction_metadata = extract_document(
            file.filename or "unnamed",
            file.content_type or "application/octet-stream",
            payload,
        )
        retriever = get_hybrid_retriever()
        source_id, chunks = retriever.add_document(
            source_name=file.filename or "unnamed",
            text=text,
            media_type=file.content_type or "application/octet-stream",
            metadata={"category": category, **extraction_metadata},
        )
        return {
            "success": True,
            "source_id": source_id,
            "source_name": file.filename,
            "chunks": chunks,
            "extractor": extraction_metadata["extractor"],
            "preview": text[:300],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"资料处理失败: {exc}") from exc


@router.post("/search", summary="调试 Hybrid RAG 检索结果")
async def search_knowledge(request: KnowledgeSearchRequest):
    hits = get_hybrid_retriever().search(
        query=request.query,
        top_k=request.top_k,
        source_ids=request.source_ids,
    )
    return {"success": True, "data": [hit.__dict__ for hit in hits]}


@router.post("/evidence/route", summary="调试 Agentic Evidence 路由与充分性判断")
async def route_evidence(request: TripRequest):
    bundle = EvidenceOrchestrator().collect(request)
    return {
        "success": True,
        "data": {
            "decision": decision_dict(bundle),
            "hits": [hit.__dict__ for hit in bundle.hits],
            "context_preview": bundle.context[:1000],
        },
    }


@router.get("/stats", summary="查看知识库状态")
async def knowledge_stats():
    return {"success": True, "data": get_hybrid_retriever().stats()}
