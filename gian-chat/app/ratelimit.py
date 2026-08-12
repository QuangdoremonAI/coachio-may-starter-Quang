"""Chặn spam đơn giản, giữ trong RAM.

Không có cái này thì một người rảnh rỗi có thể: gọi /chat vài nghìn lần đốt
sạch tiền API, hoặc bắn /lead liên tục làm ngập group Telegram của anh.

Đủ cho một site. Chạy nhiều instance thì mỗi instance đếm riêng — lúc đó
chuyển sang Redis, nhưng ở mức 1.000 hội thoại/tháng thì chưa cần.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

# đường dẫn → (số lượt, trong bao nhiêu giây)
LIMITS: dict[str, tuple[int, int]] = {
    "/chat": (20, 60),      # 20 tin/phút — người thật gõ không nhanh hơn được
    "/lead": (5, 300),      # 5 lần/5 phút
    "/history": (30, 60),
    "/chat/agent-pull": (40, 60),   # widget poll 3s = 20 lượt/phút
}

_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # Railway/Cloudflare đứng trước → IP thật nằm ở X-Forwarded-For
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(request: Request) -> None:
    rule = LIMITS.get(request.url.path)
    if not rule:
        return
    limit, window = rule
    key = (request.url.path, client_ip(request))
    now = time.time()

    q = _hits[key]
    while q and now - q[0] > window:
        q.popleft()

    if len(q) >= limit:
        raise HTTPException(status_code=429, detail="Chậm lại chút xíu nha")
    q.append(now)

    # Dọn định kỳ để dict không phình mãi
    if len(_hits) > 5000:
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > 3600]:
            _hits.pop(k, None)
