#!/usr/bin/env python3
"""go/<id>.html 생성 — 블로그·SNS 링크 카드용 앱별 연결 페이지.

메인 index.html의 APPS 목록·한국어 이름·상세 부제·배너를 읽어, 앱마다
링크 미리보기(og) 정보를 담고 열리면 ../?app=<id>(+받은 쿼리)로 넘어가는 페이지를 만든다.
새 앱을 index.html에 추가하면 이 스크립트만 다시 돌린다: python3 go/build.py
"""
import html, json, os, re, sys
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
                     url=f'{BASE}/go/{i}.html', icon=f'{BASE}/{ICON[i]}')
    open(os.path.join(ROOT, 'go', f'{i}.html'), 'w', encoding='utf-8').write(out)
    made.append(i)
print(f'{len(made)}개: ' + ' '.join(made))

# ── 앱 소개 페이지 /<id>/(ko)·/<id>/<lang>/ — 검색용(색인 허용, hreflang로 서로 묶음). go/는 공유 링크용이라 메인 시트로 넘긴다 ──
# 문구는 메인 index.html의 I18N·상세 시트(detail-<id>)에서 가져온다. 문구를 고치면 메인만 고치고 이 스크립트를 다시 돌린다
import subprocess
I18N = json.loads(subprocess.run(['node', '-e', 'process.stdout.write(JSON.stringify(eval("(" + require("fs").readFileSync(0, "utf8") + ")")))'],
                                 input=re.search(r'const I18N = (\{.*?\n        \});', src, re.S).group(1), capture_output=True, text=True, check=True).stdout)
LANGS = ['ko', 'en', 'es', 'ja']
BANNER_LANGS = json.loads(re.sub(r'(\w+):', r'"\1":', re.search(r'const BANNER_LANGS = (\{.*?\});', src).group(1).replace("'", '"')))
EXTRA = json.load(open(os.path.join(ROOT, 'go', 'app_pages.json'), encoding='utf-8'))  # 앱별 태그·주요 기능(언어별)
LABEL = {'ko': '한국어', 'en': 'English', 'es': 'Español', 'ja': '日本語'}
path = lambda i, l: f'/{i}/' + ('' if l == 'ko' else f'{l}/')

PAGE = """<!doctype html>
<html lang="{lang}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — {tagline} | CLPAK</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{alts}
<meta property="og:type" content="website">
<meta property="og:site_name" content="CLPAK">
<meta property="og:title" content="{name} — {tagline}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<link rel="icon" type="image/png" href="{icon}">
<link rel="apple-touch-icon" href="{icon}">
<script type="application/ld+json">{ld}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS77BLL0BN"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-QS77BLL0BN');
document.addEventListener('click',e=>{{const a=e.target.closest('a.link-badge');if(!a)return;const ios=a.href.includes('apps.apple.com');
gtag('event',ios?'app_store_click':'play_store_click',{{app_id:'{id}',language:'{lang}',store:ios?'app_store':'google_play',source:'app-page',transport_type:'beacon'}})}},true);</script>
<style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#1c1c1e;--sub:#6b7280;--line:#e5e7eb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111113;--fg:#f4f4f5;--sub:#a1a1aa;--line:#27272a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Hiragino Sans",sans-serif}}
nav{{max-width:640px;margin:0 auto;padding:16px 20px 0;display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:14px}}
nav a{{color:var(--sub);text-decoration:none}} .home{{display:flex;align-items:center;gap:8px;color:var(--fg);font-weight:700}} .home img{{width:24px;height:24px;border-radius:6px}}
.lng a{{margin-left:10px}} .lng a[aria-current]{{color:var(--fg);font-weight:600}}
main{{max-width:640px;margin:0 auto;padding:28px 20px 64px}}
header{{display:flex;gap:16px;align-items:center}} header img{{width:72px;height:72px;border-radius:18px}}
h1{{margin:0;font-size:26px}} .tag{{margin:2px 0 0;color:var(--sub)}}
.banner{{width:100%;border-radius:14px;margin:24px 0 8px;display:block}}
.app-links{{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}} .link-badge img{{height:44px;display:block}}
.meta,.langs{{color:var(--sub);font-size:14px}} .meta a,.more a{{color:inherit}} .separator{{margin:0 6px}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 0;padding:0;list-style:none}} .tags li{{font-size:13px;color:var(--sub);background:var(--line);border-radius:999px;padding:3px 10px}}
h2{{font-size:17px;margin:28px 0 8px}} .feat{{margin:0;padding-left:20px}} .feat li{{margin:4px 0}}
.more{{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);font-size:14px}} .more a{{color:var(--fg)}}
</style>
</head><body>
<nav><a class="home" href="{home}"><img src="{base}/clpak-icon.png" alt="">CLPAK</a><span class="lng">{lnav}</span></nav>
<main>
<header><img src="{icon}" alt=""><div><h1>{name}</h1><p class="tag">{tagline}</p></div></header>
{banner}<p>{desc}</p>
{{extra}}
{links}
{langs}
{meta}
<p class="more"><a href="{home}">{more} →</a></p>
</main></body></html>
"""

def block(i):
    m = re.search(r'<div class="app-detail" id="detail-%s"(.*?)(?=<div class="app-detail" id="detail-|</body>)' % i, src, re.S)
    return m.group(1) if m else ''

def localize(h, d):  # 시트 조각의 data-i18n 문구를 그 언어로
    return re.sub(r'data-i18n="([\w.]+)">[^<]*<', lambda m: f'data-i18n="{m.group(1)}">{html.escape(str(get(d, m.group(1)) or ""))}<', h)
get = lambda d, k: __import__('functools').reduce(lambda a, x: a.get(x) if isinstance(a, dict) else None, k.split('.'), d)

pages, urls = [], []
for i in made:
    b = block(i)
    if not (b and get(I18N['ko'], f'apps.{i}.detail_desc')):
        print(f'소개 페이지 건너뜀 {i}', file=sys.stderr); continue
    grab = lambda cls: (re.search(r'(<div class="%s">.*?</div>)' % cls, b, re.S) or [None, ''])[1]
    links = grab('app-links').replace('src="', f'src="{BASE}/')
    stores = re.findall(r'href="(https://(?:apps\.apple\.com|play\.google\.com)[^"]+)"', links)
    langs_here = [l for l in LANGS if get(I18N[l], f'apps.{i}.detail_desc')]
    alts = '\n'.join(f'<link rel="alternate" hreflang="{l}" href="{BASE}{path(i, l)}">' for l in langs_here) + f'\n<link rel="alternate" hreflang="x-default" href="{BASE}{path(i, "ko")}">'
    game = 'games' in re.search(r"\{ id: '%s'[^}]*" % i, src).group()
    for l in langs_here:
        d = I18N[l]; A = d['apps'][i]
        name, tag, desc = A['name'], A['detail_tagline'], A['detail_desc']
        url = BASE + path(i, l)
        ld = json.dumps({'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': name, 'description': desc, 'inLanguage': l,
                         'operatingSystem': ', '.join(x for x, k in (('iOS', 'apple'), ('Android', 'google')) if any(k in u for u in stores)),
                         'applicationCategory': 'GameApplication' if game else 'MobileApplication',
                         'url': url, 'image': f'{BASE}/{ICON[i]}', 'sameAs': stores,
                         'author': {'@type': 'Person', 'name': 'CLPAK', 'url': BASE + '/'}}, ensure_ascii=False)
        bl = 'en' if l == 'ja' else l
        bfile = f'{i}_{bl}.jpg' if bl in BANNER_LANGS.get(i, []) else f'{i}.jpg'
        has_banner = os.path.exists(os.path.join(ROOT, 'banners', bfile))
        home = BASE + '/' + ('' if l == 'ko' else f'?lang={l}')
        lnav = ''.join(f'<a href="{path(i, x)}" hreflang="{x}"' + (' aria-current="page"' if x == l else '') + f'>{LABEL[x]}</a>' for x in langs_here)
        out = PAGE.format(lang=l, id=i, name=html.escape(name), tagline=html.escape(tag), desc=html.escape(desc), url=url, base=BASE, alts=alts,
                          image=f'{BASE}/go/{i}.png?v=20261116', icon=f'{BASE}/{ICON[i]}', ld=ld.replace('</', '<\\/'), home=home, lnav=lnav,
                          more=html.escape(d['more_apps']),
                          banner=f'<img class="banner" src="{BASE}/banners/{bfile}" alt="">' if has_banner else '',
                          links=links, langs=localize(grab('app-langs'), d).replace('app-langs', 'langs'),
                          meta=localize(grab('app-meta-links'), d).replace('app-meta-links', 'meta'))
        x = EXTRA.get(i, {}).get(l)
        extra = (f'<h2>{EXTRA["_heading"][l]}</h2><ul class="feat">' + ''.join(f'<li>{html.escape(f)}</li>' for f in x['features']) + '</ul>'
                 + '<ul class="tags">' + ''.join(f'<li>#{html.escape(t)}</li>' for t in x['tags']) + '</ul>') if x else ''
        out = out.replace('{extra}', extra)
        os.makedirs(os.path.join(ROOT, path(i, l).strip('/')), exist_ok=True)
        open(os.path.join(ROOT, path(i, l).strip('/'), 'index.html'), 'w', encoding='utf-8').write(out)
        urls.append(url)
    pages.append(i)

sm = '\n'.join(f'  <url><loc>{u}</loc></url>' for u in [BASE + '/'] + urls)
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
    f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}\n</urlset>\n')
print(f'소개 페이지 {len(pages)}개 앱 · {len(urls)}쪽: ' + ' '.join(pages))
