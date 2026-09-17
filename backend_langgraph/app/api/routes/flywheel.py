"""数据飞轮、用户反馈与端到端样本穿刺 API。"""

from fastapi import APIRouter, HTTPException, Query

from ...models.schemas import TripFeedbackRequest
from ...services.experience_store import get_experience_store


router = APIRouter(prefix="/flywheel", tags=["数据飞轮与链路穿刺"])


@router.post("/feedback", summary="提交行程接受/修改反馈")
async def submit_feedback(payload: TripFeedbackRequest):
    store = get_experience_store()
    trace = store.get_trace(payload.trace_id)
    if trace["episode"] is None:
        raise HTTPException(status_code=404, detail="未找到对应规划 Trace")
    feedback_id = store.add_feedback(
        trace_id=payload.trace_id,
        accepted=payload.accepted,
        rating=payload.rating,
        comment=payload.comment,
        corrected_plan=payload.corrected_plan,
    )
    store.record_event(
        payload.trace_id,
        "feedback",
        "user_feedback_received",
        {"feedback_id": feedback_id, "accepted": payload.accepted, "rating": payload.rating},
    )
    return {"success": True, "feedback_id": feedback_id}


@router.get("/trace/{trace_id}", summary="按 Trace ID 穿刺完整决策链")
async def inspect_trace(trace_id: str):
    trace = get_experience_store().get_trace(trace_id)
    if trace["episode"] is None and not trace["events"]:
        raise HTTPException(status_code=404, detail="Trace 不存在")
    return {"success": True, "data": trace}


@router.get("/hard-cases", summary="查看自动挖掘的飞轮难例")
async def hard_cases(limit: int = Query(default=50, ge=1, le=500)):
    return {"success": True, "data": get_experience_store().hard_cases(limit)}


@router.get("/stats", summary="查看数据飞轮质量信号")
async def flywheel_stats():
    return {"success": True, "data": get_experience_store().stats()}
