"""Cắt câu trả lời thành 2-3 tin ngắn.

Kỹ thuật lấy từ MONA: không stream từng chữ. Trả TRỌN từng tin, nghỉ giữa
các tin và bắn event `typing`. Cảm giác "người thật đang gõ" mạnh hơn hẳn.
"""
import re

from app.config import MAX_WORDS_PER_MSG

MAX_PARTS = 3


def _by_sentence(text: str, max_words: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?…])\s+", text.strip())
    out: list[str] = []
    cur: list[str] = []
    for s in sentences:
        if not s.strip():
            continue
        if cur and len(" ".join(cur).split()) + len(s.split()) > max_words:
            out.append(" ".join(cur))
            cur = [s]
        else:
            cur.append(s)
    if cur:
        out.append(" ".join(cur))
    return out


def split(text: str, max_words: int = MAX_WORDS_PER_MSG) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    # Model được dạy ngăn tin bằng dòng chỉ có "---"
    parts = [p.strip() for p in re.split(r"\n\s*-{3,}\s*\n", text) if p.strip()]

    # Model quên ngăn → tự cắt theo đoạn rồi theo câu
    if len(parts) == 1 and len(text.split()) > max_words:
        paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        parts = paras if len(paras) > 1 else _by_sentence(text, max_words)

    # Đoạn nào vẫn dài quá thì cắt tiếp
    final: list[str] = []
    for p in parts:
        final.extend(_by_sentence(p, max_words) if len(p.split()) > max_words else [p])

    # Quá nhiều tin thì dồn phần đuôi lại — đừng spam khách
    if len(final) > MAX_PARTS:
        final = final[:MAX_PARTS - 1] + [" ".join(final[MAX_PARTS - 1:])]

    return [p for p in final if p.strip()]


def typing_delay(text: str) -> float:
    """Thời gian 'gõ' giả cho một tin. Đủ thật, không đủ chán."""
    return min(0.45 + len(text) / 90.0, 2.2)
