#!/usr/bin/env python3
"""go/<id>.html 생성 — 블로그·SNS 링크 카드용 앱별 연결 페이지.

메인 index.html의 APPS 목록·한국어 이름·상세 부제·배너를 읽어, 앱마다
링크 미리보기(og) 정보를 담고 열리면 ../?app=<id>(+받은 쿼리)로 넘어가는 페이지를 만든다.
새 앱을 index.html에 추가하면 이 스크립트만 다시 돌린다: python3 go/build.py
"""
import html, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://clpak.dev'
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

ids = re.findall(r"\{ id: '([a-z0-9]+)'", src)
assert ids, 'APPS를 못 찾음'

def ko(key):
    m = re.search(r'data-i18n="apps\.%s\.%s">([^<]+)<' % key, src)
    return html.unescape(m.group(1).strip()) if m else ''

TPL = '''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{name} - CLPAK</title>
<meta property="og:type" content="website">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<link rel="icon" type="image/png" href="{icon}">
<link rel="apple-touch-icon" href="{icon}">
<link rel="canonical" href="{target}">
<script>location.replace('../?app={id}' + (location.search ? '&' + location.search.slice(1) : '') );</script>
</head><body><a href="../?app={id}">{name} 보러 가기</a></body></html>
'''

# 링크 카드 이미지: 1200x630, 내용은 가운데 1000px 안에(네이버는 5:3로 가운데를 잘라 쓴다).
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'  # shortcut: macOS 전용 글꼴, 다른 OS에서 돌릴 땐 경로 교체
ACCENT = dict(re.findall(r"\{ id: '([a-z0-9]+)'[^}]*?accent: '(#[0-9a-fA-F]{6})'", src))
ICON = {i: (re.search(r"\{ id: '%s'[^}]*?icon: '([^']+)'" % i, src) or [None, f'{i}-icon.png'])[1] for i in ids}

def og_image(i, name, desc):
    banner = os.path.join(ROOT, 'banners', f'{i}.jpg')
    if os.path.exists(banner):
        # 스토어 배너를 가운데 1100px에 두고, 가장자리는 배너 색을 흐리게 이어 붙인다(네이버 5:3 잘림 안쪽)
        b = Image.open(banner).convert('RGB')
        c = b.resize((8, 4), Image.BOX).resize((1200, 630), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
        w = 1100; h = round(b.height * w / b.width)
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rectangle((24, 24, w - 25, h - 25), fill=255)
        c.paste(b.resize((w, h), Image.LANCZOS), ((1200 - w) // 2, (630 - h) // 2), m.filter(ImageFilter.GaussianBlur(14)))
        c.save(os.path.join(ROOT, 'go', f'{i}.png')); return
    bg = ACCENT.get(i, '#1c1c1e')
    c = Image.new('RGB', (1200, 630), bg)
    icon = Image.open(os.path.join(ROOT, ICON[i])).convert('RGBA').resize((220, 220), Image.LANCZOS)
    m = Image.new('L', icon.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 219, 219), 48, fill=255)
    c.paste(icon, (170, 205), m)
    d = ImageDraw.Draw(c)
    d.text((440, 250), name, font=ImageFont.truetype(FONT, 92, index=6), fill='white')
    f = ImageFont.truetype(FONT, 38, index=4)
    while d.textlength(desc, font=f) > 600 and len(desc) > 4: desc = desc[:-2] + '…'
    d.text((444, 375), desc, font=f, fill=(255, 255, 255, 200))
    c.save(os.path.join(ROOT, 'go', f'{i}.png'))

made = []
for i in ids:
    name, desc = ko((i, 'name')), ko((i, 'detail_tagline'))
    if not name:
        print(f'건너뜀 {i}: 이름 없음', file=sys.stderr); continue
    og_image(i, name, desc)
    img = f'{BASE}/go/{i}.png?v=20261116'
    out = TPL.format(id=i, name=html.escape(name), desc=html.escape(desc), image=img,
                     url=f'{BASE}/go/{i}.html', icon=f'{BASE}/{ICON[i]}', target=f'{BASE}/?app={i}')
    open(os.path.join(ROOT, 'go', f'{i}.html'), 'w', encoding='utf-8').write(out)
    made.append(i)
print(f'{len(made)}개: ' + ' '.join(made))
