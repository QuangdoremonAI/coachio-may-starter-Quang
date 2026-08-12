"""Hình dạng dữ liệu đi vào/ra API."""
from typing import Any

from pydantic import BaseModel, Field


class ClickstreamEntry(BaseModel):
    url: str = ""
    host: str = ""
    title: str = ""
    ts: int = 0
    duration_s: int = 0


class ChatContext(BaseModel):
    current_url: str = ""
    current_title: str = ""
    referrer: str = ""
    lang: str = "vi"
    device: str = "desktop"
    clickstream: list[ClickstreamEntry] = Field(default_factory=list)
    utm: dict[str, Any] = Field(default_factory=dict)
    campaign: str = ""


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    visitor_id: str
    context: ChatContext = Field(default_factory=ChatContext)
    channel: str = "web"


class LeadRequest(BaseModel):
    session_id: str | None = None
    visitor_id: str
    ten: str = ""
    sdt: str = ""
    email: str = ""
    nhu_cau: str = ""
    page_url: str = ""
    utm: dict[str, Any] = Field(default_factory=dict)
