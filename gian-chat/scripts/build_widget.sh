#!/usr/bin/env bash
# Minify widget.js → widget.min.js
#
# Vì sao bắt buộc: bản nguồn còn nguyên comment giải thích từng kỹ thuật —
# tin ẩn [CONTEXT], ngưỡng nudge, cách chấm lead. MONA ship bản không minify
# và lộ sạch spec nội bộ lẫn số liệu kinh doanh thật. Đừng lặp lại.
#
# Chạy:  bash scripts/build_widget.sh
# Cần:   node (npx tự tải esbuild lần đầu)

set -euo pipefail
cd "$(dirname "$0")/.."

SRC="app/static/widget.js"
OUT="app/static/widget.min.js"

command -v npx >/dev/null || { echo "✗ Chưa có node/npx. Cài Node 20+ rồi chạy lại."; exit 1; }

echo "→ Minify $SRC"
npx --yes esbuild@0.24.0 "$SRC" \
  --minify \
  --legal-comments=none \
  --target=es2019 \
  --charset=utf8 \
  --outfile="$OUT"

node --check "$OUT"

before=$(wc -c < "$SRC")
after=$(wc -c < "$OUT")
echo "✓ $OUT — $((before / 1024))KB → $((after / 1024))KB"

# Token kiểu /_nudge_ thì PHẢI còn — đó là giao thức gửi lên server.
# Cái không được lọt là: nội dung prompt, comment giải thích cách hệ chạy.
leak=0
grep -q "\[CONTEXT\]" "$OUT" && { echo "✗ Lọt nội dung prompt [CONTEXT]"; leak=1; }
grep -qE "^\s*//|/\*" "$OUT" && { echo "✗ Còn sót comment"; leak=1; }
[ "$leak" = 1 ] && exit 1
echo "✓ Không lọt prompt, không sót comment"
echo "✓ Xong. Server sẽ tự ưu tiên bản .min.js này."
