"""Người thật tiếp quản.

Anh Quang reply thẳng vào tin brief trong group Telegram → tin đó hiện trong
khung chat của khách, VẪN avatar Bé Giản. Khách không thấy đứt mạch.

Widget không nhận được SSE khi anh gõ (SSE chỉ mở lúc khách gửi tin), nên
widget poll `/chat/agent-pull` mỗi 3 giây — đúng cách MONA làm.
"""
import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.config import TELEGRAM_WEBHOOK_SECRET
from app.core import telegram
from app.db import run_db
from app.models import Session
from app import store

log = logging.getLogger("gian.agent")
router = APIRouter()


@router.get("/chat/agent-pull")
async def agent_pull(session_id: str = Query(...), after_id: int = Query(0)):
    msgs = await run_db(store.agent_messages_after, session_id, after_id)
    return {"messages": msgs}


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
):
    if x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="sai secret")

    update = await request.json()
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    reply_to = msg.get("reply_to_message") or {}
    reply_id = reply_to.get("message_id")

    # Chỉ nhận tin REPLY vào brief. Tin chat vu vơ trong group thì kệ.
    if not text or not reply_id:
        return {"ok": True}

    sess = await run_db(store.session_by_tg_message, int(reply_id))
    if sess is None:
        await telegram.send("⚠️ Không tìm thấy phiên cho tin này. "
                            "Nhớ reply đúng vào tin brief nha.")
        return {"ok": True}

    # /tra hoặc /bot = trả quyền lại cho Bé Giản
    if text.lower() in ("/tra", "/bot", "/nha"):
        await run_db(_release, sess.id)
        await telegram.send(f"✅ Đã trả phiên <code>{sess.id}</code> lại cho Bé Giản.")
        return {"ok": True}

    await run_db(store.mark_taken_over, sess.id)
    await run_db(store.save_message, sess.id, sess.visitor_id, "agent", text)
    log.info("Người thật tiếp quản phiên %s", sess.id)
    return {"ok": True}


def _release(s, session_id: str) -> None:
    row = s.get(Session, session_id)
    if row:
        row.taken_over = False
