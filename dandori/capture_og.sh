#!/bin/bash
# 공유 미리보기(og:image) 1200x630 렌더 — 원본은 og.html
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIR="$(cd "$(dirname "$0")" && pwd)"
"$CHROME" --headless=new --disable-gpu --no-sandbox --window-size=1200,630 \
  --screenshot="$DIR/og.png" --hide-scrollbars --virtual-time-budget=5000 \
  "file://$DIR/og.html" 2>/dev/null
echo "→ $DIR/og.png"
