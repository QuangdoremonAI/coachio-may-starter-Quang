"""Gửi brief lead sang Telegram + nhận anh Quang gõ trả lời (tiếp quản).

Cách hoạt động giống MONA: brief đẩy vào group, ai muốn tiếp quản thì
**reply thẳng vào tin brief đó**. Webhook map reply → đúng phiên chat.
"""
import html
import json
import logging

import httpx

from app.config import TELEGRAM_ALERT_CHAT_ID, TELEGRAM_ALERT_TOKEN

log = logging.getLogger("gian.telegram")

_TANG = {
    "dong-tien": "dòng tiền",
    "co-cau": "cơ cấu tổ chức",
    "nhan-su": "nhân sự / định biên",
    "ban-hang": "bán hàng",
    "tam-thuc": "tâm thức người lãnh đạo",
    "chua-ro": "chưa rõ",
}
_MUC_DO = {
    "dang-tim-hieu": "đang tìm hiểu",
    "dang-can-nhac": "đang cân nhắc",
    "san-sang-mua": "🔥 sẵn sàng mua",
}


def enabled() -> bool:
    return bool(TELEGRAM_ALERT_TOKEN and TELEGRAM_ALERT_CHAT_ID)


async def _api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{TELEGRAM_ALERT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


async def send(text: str) -> int:
    """Gửi tin vào group. Trả về message_id để map reply về sau."""
    if not enabled():
        log.info("Telegram chưa cấu hình — bỏ qua brief")
        return 0
    try:
        res = await _api("sendMessage", {
            "chat_id": TELEGRAM_ALERT_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        })
        return int(res.get("result", {}).get("message_id", 0))
    except Exception as e:  # noqa: BLE001 — Telegram hỏng không được làm sập chat
        log.warning("Gửi Telegram lỗi: %s", e)
        return 0


def _esc(s: str) -> str:
    return html.escape(str(s or ""))


def build_brief(sess, ctx, lead, tag: dict, last_msgs: list[str], reason: str) -> str:
    tang = _TANG.get(tag.get("tang", ""), "chưa rõ")
    muc_do = _MUC_DO.get(tag.get("muc_do", ""), "đang tìm hiểu")

    utm = {}
    try:
        utm = json.loads(sess.utm_json or "{}")
    except Exception:  # noqa: BLE001
        pass
    nguon = " · ".join(f"{k}={v}" for k, v in utm.items()
                       if k in ("source", "medium", "campaign") and v) or "trực tiếp"

    hanh_trinh = " → ".join(
        f"{(e.title or e.url)[:28]} ({e.duration_s}s)" for e in (ctx.clickstream or [])[-4:]
    ) or "—"

    lines = [
        f"<b>{_esc(reason)}</b>",
        "─────────────────────",
    ]
    if lead:
        who = f"👤 {_esc(lead.ten or 'Chưa rõ tên')}"
        if lead.sdt:
            who += f" · <code>{_esc(lead.sdt)}</code>"
        lines.append(who)
        if lead.nhu_cau:
            lines.append(f"📝 {_esc(lead.nhu_cau)}")
    else:
        lines.append("👤 Chưa để lại số")

    lines += [
        f"🎯 Tầng mắc: {_esc(tang)}",
        f"📊 Mức độ: {_esc(muc_do)}",
        f"🔗 Nguồn: {_esc(nguon)}",
        f"🕐 Hành trình: {_esc(hanh_trinh)}",
    ]

    if last_msgs:
        lines.append("")
        lines.append("💬 Khách vừa nói:")
        for m in last_msgs[-3:]:
            lines.append(f"  <i>“{_esc(m[:140])}”</i>")

    lines += [
        "",
        f"<code>{_esc(sess.id)}</code>",
        "▶️ <b>Reply thẳng vào tin này để tiếp quản</b>",
    ]
    return "\n".join(lines)


async def set_webhook(base_url: str, secret: str) -> None:
    """Trỏ Telegram về server. Gọi 1 lần lúc khởi động nếu có BASE_URL."""
    if not enabled() or not base_url:
        return
    try:
        await _api("setWebhook", {
            "url": f"{base_url.rstrip('/')}/webhook/telegram",
            "secret_token": secret,
            "allowed_updates": ["message"],
        })
        log.info("Đã trỏ webhook Telegram về %s", base_url)
    except Exception as e:  # noqa: BLE001
        log.warning("Không set được webhook Telegram: %s", e)
