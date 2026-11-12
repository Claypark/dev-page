#!/usr/bin/env python3
"""go/<id>.html 생성 — 블로그·SNS 링크 카드용 앱별 연결 페이지.

메인 index.html의 APPS 목록·한국어 이름·상세 부제·배너를 읽어, 앱마다
링크 미리보기(og) 정보를 담고 열리면 ../?app=<id>(+받은 쿼리)로 넘어가는 페이지를 만든다.
새 앱을 index.html에 추가하면 이 스크립트만 다시 돌린다: python3 go/build.py
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://claypark.github.io/dev-page'
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
<link rel="canonical" href="{target}">
<script>location.replace('../?app={id}' + (location.search ? '&' + location.search.slice(1) : '') );</script>
</head><body><a href="../?app={id}">{name} 보러 가기</a></body></html>
'''

made = []
for i in ids:
    name, desc = ko((i, 'name')), ko((i, 'detail_tagline'))
    if not name:
        print(f'건너뜀 {i}: 이름 없음', file=sys.stderr); continue
    img = f'{BASE}/banners/{i}.jpg' if os.path.exists(os.path.join(ROOT, 'banners', f'{i}.jpg')) else f'{BASE}/clpak-og.png'
    out = TPL.format(id=i, name=html.escape(name), desc=html.escape(desc), image=img,
                     url=f'{BASE}/go/{i}.html', target=f'{BASE}/?app={i}')
    open(os.path.join(ROOT, 'go', f'{i}.html'), 'w', encoding='utf-8').write(out)
    made.append(i)
print(f'{len(made)}개: ' + ' '.join(made))
