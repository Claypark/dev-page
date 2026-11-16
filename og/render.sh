#!/bin/bash
# og.html → ../clpak-og.png (1200×630). 바꾼 뒤 index.html og:image의 ?v= 값도 올린다.
cd "$(dirname "$0")"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1200,630 --virtual-time-budget=4000 --screenshot="$PWD/../clpak-og.png" "file://$PWD/og.html" 2>/dev/null
