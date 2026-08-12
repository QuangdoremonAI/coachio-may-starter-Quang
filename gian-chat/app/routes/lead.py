"""Form để lại số điện thoại (đường dự phòng, không qua LLM)."""
import json
import logging

from fastapi import APIRouter

from app.core import telegram
from app.db import run_db
from app.schemas import LeadRequest
from app import store

log = logging.getLogger("gian.lead")
router = APIRouter()


@router.post("/lead")
async def submit_lead(req: LeadRequest):
    session_id = req.session_id or store.new_id("sess")
    lead = await run_db(
        store.upsert_lead, session_id, req.visitor_id,
        {"ten": req.ten, "sdt": req.sdt, "email": req.email, "nhu_cau": req.nhu_cau},
        req.page_url,
    )

    if telegram.enabled():
        utm = " · ".join(f"{k}={v}" for k, v in (req.utm or {}).items() if v) or "trực tiếp"
        await telegram.send(
            "📝 <b>LEAD TỪ FORM</b>\n─────────────────────\n"
            f"👤 {lead.ten or 'Chưa rõ tên'} · <code>{lead.sdt}</code>\n"
            f"✉️ {lead.email or '—'}\n"
            f"📝 {lead.nhu_cau or '—'}\n"
            f"🔗 {utm}\n"
            f"🌐 {req.page_url or '—'}\n\n<code>{session_id}</code>"
        )

    log.info("Lead mới: %s %s", lead.ten, lead.sdt)
    return {"ok": True, "session_id": session_id}
