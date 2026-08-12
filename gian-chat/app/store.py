"""Mọi thao tác chạm DB gom về đây — route không tự viết query."""
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.models import Lead, Message, Session


def _now():
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


# ─── Phiên ────────────────────────────────────────────────────────────
def get_or_create_session(s, visitor_id: str, session_id: str | None,
                          channel: str, ctx) -> Session:
    sess = None
    if session_id:
        sess = s.get(Session, session_id)
    if sess is None:
        sess = Session(
            id=session_id or new_id("sess"),
            visitor_id=visitor_id,
            channel=channel,
            campaign=getattr(ctx, "campaign", "") or "",
            first_url=getattr(ctx, "current_url", "") or "",
            utm_json=json.dumps(getattr(ctx, "utm", {}) or {}, ensure_ascii=False),
        )
        s.add(sess)
        s.flush()
    else:
        sess.last_at = _now()
    return sess


def bump_turn(s, session_id: str) -> None:
    sess = s.get(Session, session_id)
    if sess:
        sess.turn_count += 1
        sess.last_at = _now()


def set_tag(s, session_id: str, tag: dict) -> None:
    sess = s.get(Session, session_id)
    if not sess:
        return
    if tag.get("tang"):
        sess.tag_tang = tag["tang"]
    if tag.get("muc_do"):
        sess.tag_muc_do = tag["muc_do"]


def set_tg_message(s, session_id: str, message_id: int) -> None:
    sess = s.get(Session, session_id)
    if sess and message_id:
        sess.tg_message_id = message_id


def session_by_tg_message(s, message_id: int) -> Session | None:
    return s.scalars(
        select(Session).where(Session.tg_message_id == message_id)
    ).first()


def mark_taken_over(s, session_id: str) -> None:
    sess = s.get(Session, session_id)
    if sess:
        sess.taken_over = True


# ─── Tin nhắn ─────────────────────────────────────────────────────────
def save_message(s, session_id: str, visitor_id: str, role: str, content: str,
                 hidden: bool = False) -> int:
    m = Message(session_id=session_id, visitor_id=visitor_id, role=role,
                content=content, hidden=hidden)
    s.add(m)
    s.flush()
    return m.id


def load_history(s, session_id: str, limit: int) -> list[tuple[str, str]]:
    """Lịch sử nạp vào prompt. Bỏ tin ẩn hệ thống để prompt khỏi rác."""
    rows = s.scalars(
        select(Message)
        .where(Message.session_id == session_id, Message.hidden.is_(False))
        .order_by(Message.id.desc())
        .limit(limit)
    ).all()
    return [(m.role, m.content) for m in reversed(rows)]


def last_user_messages(s, session_id: str, n: int = 3) -> list[str]:
    rows = s.scalars(
        select(Message)
        .where(Message.session_id == session_id, Message.role == "user",
               Message.hidden.is_(False))
        .order_by(Message.id.desc())
        .limit(n)
    ).all()
    return [m.content for m in reversed(rows)]


def history_for_visitor(s, visitor_id: str, limit: int) -> list[dict]:
    """Khôi phục khung chat khi khách quay lại — xuyên phiên, xuyên ngày."""
    rows = s.scalars(
        select(Message)
        .where(Message.visitor_id == visitor_id, Message.hidden.is_(False))
        .order_by(Message.id.desc())
        .limit(limit)
    ).all()
    return [
        {"role": "user" if m.role == "user" else "bot", "content": m.content}
        for m in reversed(rows)
    ]


def agent_messages_after(s, session_id: str, after_id: int) -> list[dict]:
    rows = s.scalars(
        select(Message)
        .where(Message.session_id == session_id, Message.role == "agent",
               Message.id > after_id)
        .order_by(Message.id)
    ).all()
    return [{"id": m.id, "text": m.content} for m in rows]


# ─── Lead ─────────────────────────────────────────────────────────────
def get_lead(s, visitor_id: str) -> Lead | None:
    return s.scalars(
        select(Lead).where(Lead.visitor_id == visitor_id).order_by(Lead.id.desc())
    ).first()


def upsert_lead(s, session_id: str, visitor_id: str, data: dict, nguon: str = "") -> Lead:
    lead = get_lead(s, visitor_id)
    if lead is None:
        lead = Lead(session_id=session_id, visitor_id=visitor_id, nguon=nguon)
        s.add(lead)
    for field in ("ten", "sdt", "email", "nhu_cau"):
        val = (data.get(field) or "").strip()
        if val:
            setattr(lead, field, val)
    if nguon and not lead.nguon:
        lead.nguon = nguon
    s.flush()
    return lead
