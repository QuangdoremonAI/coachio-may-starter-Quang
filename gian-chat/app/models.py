"""Bảng dữ liệu. Cố tình ít bảng — đủ dùng, dễ đọc."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Session(Base):
    """Một phiên hội thoại. visitor_id sống lâu hơn session_id."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    visitor_id: Mapped[str] = mapped_column(String(64), index=True)
    channel: Mapped[str] = mapped_column(String(24), default="web")
    campaign: Mapped[str] = mapped_column(String(64), default="")

    turn_count: Mapped[int] = mapped_column(Integer, default=0)

    # Bot tự chấm — khách không thấy
    tag_tang: Mapped[str] = mapped_column(String(32), default="")
    tag_muc_do: Mapped[str] = mapped_column(String(32), default="")

    # Người thật đã tiếp quản phiên này chưa
    taken_over: Mapped[bool] = mapped_column(Boolean, default=False)
    # id tin brief trên Telegram — để map "reply" của anh về đúng phiên
    tg_message_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    first_url: Mapped[str] = mapped_column(Text, default="")
    utm_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Message(Base):
    """role: user | bot | agent (người thật) | system (tin ẩn [CONTEXT])."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    visitor_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    visitor_id: Mapped[str] = mapped_column(String(64), index=True)
    ten: Mapped[str] = mapped_column(String(128), default="")
    sdt: Mapped[str] = mapped_column(String(32), default="")
    email: Mapped[str] = mapped_column(String(128), default="")
    nhu_cau: Mapped[str] = mapped_column(Text, default="")
    nguon: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
