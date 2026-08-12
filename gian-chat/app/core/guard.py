"""Lằn ranh cứng. Chặn ở CODE, không chỉ trông vào prompt.

Bot mang tên anh Quang — nó nói gì thì anh chịu trách nhiệm. Prompt có thể
bị model lờ đi; mấy hàm dưới đây thì không.
"""
import logging
import re

from app.config import KB_DIR
from app.core.rag import strip_accents

log = logging.getLogger("gian.guard")

SAFE_REPLY = ("Dạ cái này em xin phép không tư vấn qua chat được ạ 🙏 "
              "Anh/chị để lại số điện thoại, bên em gọi lại trao đổi kỹ hơn nha.")

PRICE_REPLY = ("Dạ học phí em xin gửi bảng chính thức để không sai con số nha 🙏 "
               "Anh/chị cho em xin số điện thoại, em gửi ngay ạ.")

# ─── 1. Chặn đầu vào ──────────────────────────────────────────────────
_INJECTION = [
    r"ignore (all |the )?(previous|above|prior)",
    r"bỏ qua (mọi |tất cả )?(chỉ dẫn|hướng dẫn|lệnh)",
    r"(in|show|print|reveal|repeat) (your |the )?(system )?prompt",
    r"(system prompt|prompt hệ thống|chỉ dẫn hệ thống)",
    r"you are now|từ giờ (bạn|em) là|giả vờ (bạn|em) là",
    r"developer mode|jailbreak|DAN mode",
]
_INJECTION_RE = [re.compile(p, re.I) for p in _INJECTION]


def block_input(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_RE)


# ─── 2. Chặn hứa hẹn ──────────────────────────────────────────────────
_PROMISE = [
    r"(chắc chắn|đảm bảo|cam kết|bảo đảm)[^.\n]{0,25}(lãi|lời|hết lỗ|thành công|x\d)",
    r"x\s?\d+\s*(doanh thu|lợi nhuận)",
    r"(hoàn tiền 100%|cam kết hoàn tiền)",
    r"(chắc chắn|đảm bảo) (sẽ )?(giàu|thành công|hết lỗ)",
]
_PROMISE_RE = [re.compile(p, re.I) for p in _PROMISE]

_OFF_TOPIC = [
    r"\b(uống|liều|thuốc|kê đơn|chẩn đoán)\b.{0,30}\b(mg|viên|ngày)\b",
    r"(trốn thuế|lách thuế|né thuế)",
]
_OFF_TOPIC_RE = [re.compile(p, re.I) for p in _OFF_TOPIC]


# ─── 3. Khoá bảng giá ─────────────────────────────────────────────────
# Mọi con số tiền bot nói ra PHẢI có trong kb/. Không có = bịa = chặn.
_MONEY_RE = re.compile(
    r"(\d[\d.,]*)\s*(triệu|trieu|tr\b|nghìn|nghin|ngàn|ngan|k\b|đồng|dong|đ\b|vnd|₫)",
    re.I,
)
_BIG_NUMBER_RE = re.compile(r"\b\d{1,3}(?:[.,]\d{3}){1,3}\b")

_ALLOWED: set[str] = set()

# Chỗ <<< ĐIỀN ... >>> trong file mẫu hay có số ví dụ — không được tính là giá thật
_PLACEHOLDER_RE = re.compile(r"<<<.*?>>>", re.S)


def _norm_money(num: str, unit: str = "") -> str:
    digits = re.sub(r"[.,]", "", num)
    unit = strip_accents(unit.lower().strip())
    unit = {"tr": "trieu", "trieu": "trieu", "ngan": "nghin", "nghin": "nghin",
            "k": "nghin", "dong": "d", "vnd": "d", "₫": "d", "d": "d"}.get(unit, unit)
    return f"{digits}{unit}"


def load_price_whitelist() -> set[str]:
    """Quét toàn bộ kb/ lấy mọi con số tiền hợp lệ."""
    allowed: set[str] = set()
    if not KB_DIR.exists():
        return allowed
    for path in KB_DIR.rglob("*.md"):
        text = _PLACEHOLDER_RE.sub(" ", path.read_text(encoding="utf-8"))
        for num, unit in _MONEY_RE.findall(text):
            allowed.add(_norm_money(num, unit))
            allowed.add(_norm_money(num))          # cho phép nói trống đơn vị
        for num in _BIG_NUMBER_RE.findall(text):
            allowed.add(_norm_money(num))
    log.info("Bảng giá hợp lệ: %d con số lấy từ kb/", len(allowed))
    return allowed


def warmup() -> None:
    global _ALLOWED
    _ALLOWED = load_price_whitelist()


def _has_unlisted_price(text: str) -> bool:
    for num, unit in _MONEY_RE.findall(text):
        digits = re.sub(r"[.,]", "", num)
        # Bỏ qua số nhỏ vô hại: "3 tháng", "5 người" không match vì cần đơn vị tiền,
        # nhưng "2 triệu" phải kiểm. Số < 10 kèm "k" cũng bỏ qua (vd "8k lượt").
        if not digits.isdigit():
            continue
        if _norm_money(num, unit) in _ALLOWED or _norm_money(num) in _ALLOWED:
            continue
        return True
    for num in _BIG_NUMBER_RE.findall(text):
        if _norm_money(num) not in _ALLOWED:
            return True
    return False


# ─── 4. Làm sạch đầu ra ───────────────────────────────────────────────
def clean_output(text: str) -> tuple[str, str | None]:
    """Trả về (nội dung đã sạch, lý do bị chặn nếu có)."""
    if any(p.search(text) for p in _PROMISE_RE):
        log.warning("Chặn output: hứa hẹn kết quả")
        return SAFE_REPLY, "hua-hen"

    if any(p.search(text) for p in _OFF_TOPIC_RE):
        log.warning("Chặn output: ngoài phạm vi")
        return SAFE_REPLY, "ngoai-pham-vi"

    if _ALLOWED and _has_unlisted_price(text):
        log.warning("Chặn output: con số tiền không có trong kb/")
        return PRICE_REPLY, "gia-bia"

    # Cắt bỏ thẻ HTML model lỡ nhả ra
    text = re.sub(r"<\s*/?\s*(br|p|div|span|hr)\b[^>]*>", "\n", text, flags=re.I)
    return text.strip(), None
