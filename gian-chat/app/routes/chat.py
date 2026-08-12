"""POST /chat — trái tim của hệ. Nhận tin, trả về luồng SSE.

Thứ tự event gửi về (giống MONA):
    session → typing → message → (typing → message)* → tag → done
"""
import asyncio
import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.config import HISTORY_TURNS
from app.core import guard, llm, prompt, rag, splitter, tagger, telegram
from app.db import run_db
from app.schemas import ChatRequest
from app import store

log = logging.getLogger("gian.chat")
router = APIRouter()

ERROR_TEXT = "Dạ em đang kẹt kết nối chút xíu, anh/chị nhắn lại giúp em sau 1 phút nha 🙏"
TAKEOVER_TEXT = "Dạ anh/chị chờ em chút xíu nha, em đang xem lại thông tin 🙏"


def sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


@router.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        # ── 1. Tin ẩn hệ thống ([CONTEXT]) hay tin thật của khách? ──────
        raw = (req.message or "").strip()
        hidden = raw in prompt.HIDDEN_MESSAGES
        message = prompt.HIDDEN_MESSAGES.get(raw, raw)
        if not message:
            yield sse("done", {})
            return

        # ── 2. Phiên ────────────────────────────────────────────────────
        sess = await run_db(store.get_or_create_session, req.visitor_id,
                            req.session_id, req.channel, req.context)
        yield sse("session", {"session_id": sess.id})

        # ── 3. Chặn đầu vào độc ─────────────────────────────────────────
        if not hidden and guard.block_input(message):
            log.warning("Chặn input đáng ngờ · session=%s", sess.id)
            await run_db(store.save_message, sess.id, req.visitor_id, "user", message)
            await run_db(store.save_message, sess.id, req.visitor_id, "bot", guard.SAFE_REPLY)
            yield sse("message", {"text": guard.SAFE_REPLY})
            yield sse("done", {})
            return

        await run_db(store.save_message, sess.id, req.visitor_id, "user", message, hidden)

        # ── 4. Người thật đang tiếp quản → bot IM LẶNG ──────────────────
        # Không có bước này thì bot nói chen vào lúc anh Quang đang gõ.
        if sess.taken_over:
            if telegram.enabled():
                await telegram.send(
                    f"💬 <b>Khách nhắn tiếp</b> (phiên đang do người tiếp quản)\n"
                    f"<code>{sess.id}</code>\n\n{message[:500]}"
                )
            yield sse("done", {})
            return

        # ── 5. Nạp ngữ cảnh ─────────────────────────────────────────────
        history = await run_db(store.load_history, sess.id, HISTORY_TURNS)
        lead = await run_db(store.get_lead, req.visitor_id)
        recent = " ".join(c for r, c in history[-4:] if r == "user")
        chunks = await rag.search(message, recent)

        # ── 6. Gọi model ────────────────────────────────────────────────
        messages = prompt.build(chunks, req.context, sess, lead, history, message)
        tier = llm.pick_tier(message, sess.turn_count)
        try:
            answer = await llm.complete(messages, tier=tier)
        except Exception:  # noqa: BLE001
            # Log đầy đủ cho mình; gửi ra trình duyệt CHỈ câu chung chung.
            # str(e) của httpx có URL nhà cung cấp, đôi khi cả header — không
            # có lý do gì để khách lạ đọc được nội bộ hệ thống.
            log.exception("LLM lỗi · session=%s · tier=%s", sess.id, tier)
            yield sse("message", {"text": ERROR_TEXT})
            yield sse("error", {"message": "upstream_error"})
            yield sse("done", {})
            return

        # ── 7. Tách dòng điều khiển TRƯỚC, rồi mới lọc nội dung ─────────
        spoken, control = tagger.extract(answer)
        spoken, blocked = guard.clean_output(spoken)
        if blocked:
            log.warning("Output bị chặn (%s) · session=%s · tier=%s", blocked, sess.id, tier)

        # ── 8. Cắt thành 2-3 tin + gõ giả ───────────────────────────────
        parts = splitter.split(spoken) or [TAKEOVER_TEXT]
        for i, part in enumerate(parts):
            if i:
                yield sse("typing", {})
                await asyncio.sleep(splitter.typing_delay(part))
            yield sse("message", {"text": part})
            await run_db(store.save_message, sess.id, req.visitor_id, "bot", part)

        await run_db(store.bump_turn, sess.id)

        # ── 9. Tag ngầm — khách không thấy ──────────────────────────────
        tag = control.get("tag", {})
        if tag:
            await run_db(store.set_tag, sess.id, tag)
            yield sse("tag", tag)

        # ── 10. Lead mới / cần người thật → brief sang Telegram ─────────
        got_lead = control.get("lead")
        need_human = control.get("chuyen_nguoi")
        hot = tag.get("muc_do") == "san-sang-mua"

        if got_lead:
            lead = await run_db(store.upsert_lead, sess.id, req.visitor_id, got_lead,
                                sess.first_url)

        if (got_lead or need_human or hot) and telegram.enabled():
            reason = ("🙋 KHÁCH CẦN NGƯỜI THẬT" if need_human
                      else "🔥 LEAD NÓNG" if got_lead or hot else "👀 Đáng chú ý")
            if need_human:
                reason += f" — {need_human}"
            last_msgs = await run_db(store.last_user_messages, sess.id, 3)
            brief = telegram.build_brief(sess, req.context, lead, tag, last_msgs, reason)
            mid = await telegram.send(brief)
            if mid:
                await run_db(store.set_tg_message, sess.id, mid)

        yield sse("done", {})

    return EventSourceResponse(stream())
