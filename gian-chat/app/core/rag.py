"""Tìm đoạn tài liệu khớp câu hỏi.

Knowledge base nhỏ (vài trăm đoạn) nên KHÔNG cần pgvector, không cần
vector database. Nạp hết vào RAM lúc khởi động, chấm điểm lai:

    điểm = trùng từ khoá  +  khớp metadata `tra_loi_cho`  +  cosine embedding

Không có JINA_API_KEY thì bỏ vế embedding — vẫn chạy tốt vì KB tiếng Việt
và câu hỏi khách dùng gần đúng từ ngữ trong KB.
"""
import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from app.config import JINA_API_KEY, JINA_MODEL, KB_DIR, RAG_TOP_K

log = logging.getLogger("gian.rag")

CHUNK_WORDS = 320
OVERLAP_WORDS = 60

_STOP = {
    "là", "và", "của", "cho", "thì", "mà", "này", "kia", "đó", "các", "những",
    "được", "có", "không", "ở", "với", "một", "khi", "nếu", "để", "trong",
    "em", "anh", "chị", "mình", "ạ", "nha", "nhé", "vậy", "sao", "gì", "à",
}


def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def tokens(s: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", strip_accents(s.lower()))
    return {w for w in words if len(w) > 1 and w not in _STOP}


@dataclass
class Chunk:
    text: str
    source: str
    chu_de: str = ""
    tra_loi_cho: str = ""
    toks: set[str] = field(default_factory=set)
    hint_toks: set[str] = field(default_factory=set)
    vec: list[float] | None = None


_CHUNKS: list[Chunk] = []


# ─── Nạp & cắt tài liệu ───────────────────────────────────────────────
def _parse_front_matter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    meta = {}
    for line in raw[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, raw[end + 4:]


def _split_sections(body: str) -> list[str]:
    """Cắt theo heading `##` trước, đoạn nào dài quá thì cắt tiếp theo số từ."""
    parts = re.split(r"\n(?=##\s)", body)
    out: list[str] = []
    for part in parts:
        words = part.split()
        if len(words) <= CHUNK_WORDS:
            if part.strip():
                out.append(part.strip())
            continue
        step = CHUNK_WORDS - OVERLAP_WORDS
        for i in range(0, len(words), step):
            piece = " ".join(words[i:i + CHUNK_WORDS]).strip()
            if piece:
                out.append(piece)
            if i + CHUNK_WORDS >= len(words):
                break
    return out


def load_kb(kb_dir: Path = KB_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    if not kb_dir.exists():
        log.warning("Không thấy thư mục kb/ tại %s — bot sẽ không biết gì cả", kb_dir)
        return chunks

    for path in sorted(kb_dir.rglob("*.md")):
        if path.name.upper().startswith("README"):
            continue
        raw = path.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(raw)
        # Bỏ hẳn file mẫu chưa điền — thà bot không biết còn hơn nói bậy
        if body.count("<<<") > 3:
            log.warning("Bỏ qua %s — còn nhiều chỗ <<< ĐIỀN >>> chưa viết", path.name)
            continue
        # File đã điền gần hết: cắt nốt vài chỗ placeholder còn sót
        body = re.sub(r"<<<.*?>>>", "", body, flags=re.S)
        rel = str(path.relative_to(kb_dir))
        for text in _split_sections(body):
            chunks.append(Chunk(
                text=text,
                source=rel,
                chu_de=meta.get("chu_de", ""),
                tra_loi_cho=meta.get("tra_loi_cho", ""),
                toks=tokens(text),
                hint_toks=tokens(meta.get("chu_de", "") + " " + meta.get("tra_loi_cho", "")),
            ))
    log.info("Nạp KB: %d file → %d đoạn", len(list(kb_dir.rglob('*.md'))), len(chunks))
    return chunks


# ─── Embedding (tuỳ chọn) ─────────────────────────────────────────────
async def _embed(texts: list[str], task: str) -> list[list[float]] | None:
    if not JINA_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.jina.ai/v1/embeddings",
                headers={"Authorization": f"Bearer {JINA_API_KEY}"},
                json={"model": JINA_MODEL, "task": task, "input": texts},
            )
            r.raise_for_status()
            return [d["embedding"] for d in r.json()["data"]]
    except Exception as e:  # noqa: BLE001 — embedding hỏng thì vẫn phải chạy tiếp
        log.warning("Embedding lỗi (%s) — chuyển sang tìm bằng từ khoá", e)
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


async def warmup() -> None:
    """Gọi 1 lần lúc khởi động: nạp KB + tính embedding cho từng đoạn."""
    global _CHUNKS
    _CHUNKS = load_kb()
    if not _CHUNKS:
        return
    vecs = await _embed([c.text for c in _CHUNKS], task="retrieval.passage")
    if vecs:
        for c, v in zip(_CHUNKS, vecs):
            c.vec = v
        log.info("Đã tính embedding cho %d đoạn", len(vecs))


def stats() -> dict:
    return {
        "chunks": len(_CHUNKS),
        "files": len({c.source for c in _CHUNKS}),
        "embedded": sum(1 for c in _CHUNKS if c.vec),
    }


# ─── Tìm kiếm ─────────────────────────────────────────────────────────
async def search(query: str, recent_user_text: str = "", k: int = RAG_TOP_K) -> list[str]:
    if not _CHUNKS:
        return []

    q_toks = tokens(query) | tokens(recent_user_text)
    if not q_toks:
        return []

    qvec = None
    if any(c.vec for c in _CHUNKS):
        got = await _embed([query], task="retrieval.query")
        qvec = got[0] if got else None

    scored: list[tuple[float, Chunk]] = []
    for c in _CHUNKS:
        overlap = len(q_toks & c.toks) / (len(q_toks) ** 0.5)
        hint = 2.0 * len(q_toks & c.hint_toks) / (len(q_toks) ** 0.5)
        sem = 4.0 * _cosine(qvec, c.vec) if (qvec and c.vec) else 0.0
        score = overlap + hint + sem
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [f"[nguồn: {c.source}]\n{c.text}" for _, c in scored[:k]]
