"""Tách các dòng điều khiển [TAG] / [LEAD] / [CHUYEN_NGUOI] khỏi lời thoại.

Dùng dòng điều khiển thay vì tool-calling để chạy được trên MỌI nhà cung cấp
model (DeepSeek, Anthropic, ...) mà không phải viết hai đường code.
"""
import re

_LINE_RE = re.compile(r"^\s*\[(TAG|LEAD|CHUYEN_NGUOI)\]\s*(.*)$", re.I | re.M)

VALID_TANG = {"dong-tien", "co-cau", "nhan-su", "ban-hang", "tam-thuc", "chua-ro"}
VALID_MUC_DO = {"dang-tim-hieu", "dang-can-nhac", "san-sang-mua"}


def _kv(payload: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in payload.split(";"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            v = v.strip()
            if v and v not in ("<>", "?", "-"):
                out[k.strip().lower()] = v
    return out


def extract(raw: str) -> tuple[str, dict]:
    """Trả về (lời thoại đã sạch, dict điều khiển)."""
    control: dict = {}

    for kind, payload in _LINE_RE.findall(raw):
        data = _kv(payload)
        kind = kind.upper()

        if kind == "TAG":
            tang = data.get("tang", "")
            muc_do = data.get("muc_do", "")
            tag = {}
            if tang in VALID_TANG:
                tag["tang"] = tang
            if muc_do in VALID_MUC_DO:
                tag["muc_do"] = muc_do
            if tag:
                control["tag"] = tag

        elif kind == "LEAD":
            sdt = re.sub(r"[^\d+]", "", data.get("sdt", ""))
            # Số VN hợp lệ: 9-11 chữ số. Ngắn hơn là model bịa.
            if len(re.sub(r"\D", "", sdt)) >= 9:
                control["lead"] = {
                    "ten": data.get("ten", "")[:128],
                    "sdt": sdt[:32],
                    "email": data.get("email", "")[:128],
                    "nhu_cau": data.get("nhu_cau", "")[:500],
                }

        elif kind == "CHUYEN_NGUOI":
            control["chuyen_nguoi"] = data.get("ly_do", "khách cần người thật")[:300]

    spoken = _LINE_RE.sub("", raw).strip()
    # Model đôi khi để lại dòng trống thừa chỗ vừa cắt
    spoken = re.sub(r"\n{3,}", "\n\n", spoken)
    return spoken, control
