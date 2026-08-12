"""Khôi phục hội thoại cũ + reset phiên."""
from fastapi import APIRouter, Query

from app.db import run_db
from app import store

router = APIRouter()


@router.get("/history")
async def get_history(visitor_id: str = Query(...), limit: int = Query(50, le=200)):
    msgs = await run_db(store.history_for_visitor, visitor_id, limit)
    return {"messages": msgs}


@router.post("/chat/reset")
async def reset(visitor_id: str = Query(...)):
    """Khách bấm 'bắt đầu lại'. Không xoá dữ liệu — chỉ mở phiên mới."""
    return {"ok": True, "session_id": store.new_id("sess"), "visitor_id": visitor_id}
