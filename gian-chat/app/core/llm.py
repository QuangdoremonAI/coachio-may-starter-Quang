"""Gọi LLM. Hai tầng để tiết kiệm: DeepSeek cho câu thường, Haiku cho câu nặng."""
import logging

import httpx

from app.config import (ANTHROPIC_API_KEY, ANTHROPIC_BASE, ANTHROPIC_MODEL,
                        DEEPSEEK_API_KEY, DEEPSEEK_BASE, DEEPSEEK_MODEL,
                        LLM_TIMEOUT_S, MAX_TOKENS)

log = logging.getLogger("gian.llm")

# Câu chạm tới tiền / quyết định → dùng model khôn hơn, đáng tiền.
_HOT = ("học phí", "hoc phi", "giá", "bao nhiêu tiền", "đăng ký", "dang ky",
        "tư vấn 1-1", "khai giảng", "chuyển khoản", "đóng tiền", "học bổng",
        "hoàn tiền", "cam kết")


def pick_tier(message: str, turn_count: int) -> str:
    if not ANTHROPIC_API_KEY:
        return "fast"
    low = message.lower()
    if any(k in low for k in _HOT):
        return "smart"
    if turn_count >= 6:          # hội thoại đã sâu, đừng để hụt
        return "smart"
    if len(message) > 220:       # câu dài, nhiều ý
        return "smart"
    return "fast"


async def _deepseek(messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as client:
        r = await client.post(
            f"{DEEPSEEK_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "max_tokens": MAX_TOKENS,
                "temperature": 0.6,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _anthropic(messages: list[dict]) -> str:
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as client:
        r = await client.post(
            f"{ANTHROPIC_BASE}/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "system": system,
                "messages": turns,
                "max_tokens": MAX_TOKENS,
                "temperature": 0.6,
            },
        )
        r.raise_for_status()
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


async def complete(messages: list[dict], tier: str = "fast") -> str:
    """Gọi model. Tầng smart hỏng thì tụt xuống fast chứ không để khách chờ lỗi."""
    if tier == "smart" and ANTHROPIC_API_KEY:
        try:
            return await _anthropic(messages)
        except Exception as e:  # noqa: BLE001
            log.warning("Haiku lỗi (%s) — chuyển sang DeepSeek", e)
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("Chưa có DEEPSEEK_API_KEY")
    return await _deepseek(messages)
