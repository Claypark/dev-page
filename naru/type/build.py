"""나루 낚시 유형 테스트 — 글꼴 서브셋 + og 그림 + 공유용 r/<유형>/ 페이지 생성.
index.html 문구를 바꾸면 다시 돌린다: cd dev-page/naru/type && python3 build.py"""
import json, os, re, subprocess
from PIL import Image, ImageDraw, ImageFont

GAL = '/Users/clpak/workspace/mi-app/apps/naru/app/assets/fonts/Galmuri11.ttf'
html = open('index.html', encoding='utf-8').read()

# 1) 글꼴 서브셋 (페이지에 나오는 글자만)
chars = set(html) | set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !?.,~/←·')
open('/tmp/naru_type_chars.txt', 'w').write(''.join(sorted(chars)))
subprocess.run(['pyftsubset', GAL, '--text-file=/tmp/naru_type_chars.txt', '--flavor=woff2',
                '--output-file=galmuri11-sub.woff2'], check=True)
# 글꼴이 바뀌면 브라우저 캐시를 넘기도록 주소에 내용 해시를 붙인다
import hashlib
h = hashlib.md5(open('galmuri11-sub.woff2', 'rb').read()).hexdigest()[:8]
html = re.sub(r"url\('galmuri11-sub\.woff2[^']*'\)", f"url('galmuri11-sub.woff2?v={h}')", html)
open('index.html', 'w', encoding='utf-8').write(html)

# 2) 유형 목록은 index.html의 TYPES에서 읽는다 (한 곳에서만 관리)
types = {k: (n, l, re.findall(r"\['(\d+)', '([^']+)'\]", a)) for k, n, a, l in re.findall(r"(\w+):\s*\{ name: '([^']+)', anglers: (\[.*?\]\]), line: '([^']+)'", html)}
assert len(types) == 8, types

BG, WATER, SKY, GOLD = (26, 26, 46), (31, 59, 92), (79, 195, 247), (255, 213, 79)
W, H, S = 400, 210, 3  # 1배로 그리고 3배 → 1200x630


def font(px):
    return ImageFont.truetype(GAL, px)


def base():
    im = Image.new('RGBA', (W, H), BG + (255,))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.rectangle((0, H - 40, W, H), fill=WATER)
    for x in range(0, W, 8):
        d.rectangle((x, H - 40, x + 3, H - 39), fill=(76, 123, 168))
    for x, y in [(30, 20), (90, 50), (150, 14), (250, 34), (330, 18), (370, 60), (210, 70)]:
        d.point((x, y), fill=(180, 190, 210))
    return im, d


def sprite(path, h):
    s = Image.open(path).convert('RGBA')
    s = s.crop(s.getbbox())
    w = round(s.width * h / s.height)
    return s.resize((w, h), Image.NEAREST)


def save(im, path):
    im.resize((W * S, H * S), Image.NEAREST).convert('RGB').quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)


# og 장면 = 잡는 자세 캐릭터 + 낚싯대 끝에 매달린 물고기(머리 위로)
def tip(im):
    """낚싯대 끝 = 위쪽 절반에서 가장 오른쪽 불투명 픽셀(모자 꼭대기를 잡지 않게)."""
    a = im.getchannel('A')
    best = None
    for y in range(im.height // 2):
        for x in range(im.width - 1, -1, -1):
            if a.getpixel((x, y)) > 128:
                if best is None or x > best[0]:
                    best = (x, y)
                break
    return best


def scene(t, outfit):
    c = Image.open(f'_build/k_{outfit}.png').convert('RGBA')  # 잡는 자세
    f = Image.open(f'img/f_{t}.webp').convert('RGBA')
    f = f.crop(f.getbbox()).rotate(90, expand=True, resample=Image.NEAREST)  # 머리가 위로
    k = 92 / max(f.size)
    f = f.resize((max(1, round(f.width * k)), max(1, round(f.height * k))), Image.NEAREST)
    tx, ty = tip(c)
    W2 = max(c.width, tx + f.width // 2 + 4)
    out = Image.new('RGBA', (W2, c.height), (0, 0, 0, 0))
    out.alpha_composite(c, (0, 0))
    fy = ty + 46
    ImageDraw.Draw(out).line((tx, ty + 2, tx, fy + 2), fill=(225, 228, 238, 255), width=1)  # 불투명 — 반투명이면 og 팔레트 압축 때 사라진다
    out.alpha_composite(f, (tx - f.width // 2, fy))
    return out


# 첫 화면 실루엣 = 물고기 낚아 올리는 장면(잡는 자세 + 매달린 물고기)을 어둡게 + 밝은 테두리
def silhouette():
    c = Image.open('_build/k_03.png').convert('RGBA')
    f = Image.open('/Users/clpak/workspace/mi-app/apps/naru/app/assets/catalog/sprites/fish_1.png').convert('RGBA')
    f = f.crop(f.getbbox()).rotate(90, expand=True, resample=Image.NEAREST)
    k = 92 / max(f.size)
    f = f.resize((round(f.width * k), round(f.height * k)), Image.NEAREST)
    tx, ty = tip(c)
    out = Image.new('RGBA', (max(c.width, tx + f.width // 2 + 4), c.height))
    out.alpha_composite(c)
    ImageDraw.Draw(out).line((tx, ty + 2, tx, ty + 48), fill=(255, 255, 255, 255), width=2)
    out.alpha_composite(f, (tx - f.width // 2, ty + 46))
    a = out.getchannel('A').point(lambda v: 255 if v > 100 else 0)
    W2, H2 = out.size
    sil = Image.new('RGBA', (W2 + 4, H2 + 4))
    rim = Image.new('RGBA', (W2, H2), (140, 160, 210, 255))
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        sil.paste(rim, (2 + dx, 2 + dy), a)
    sil.paste(Image.new('RGBA', (W2, H2), (16, 20, 42, 255)), (2, 2), a)
    sil.save('img/silhouette.webp', 'WEBP', lossless=True, method=6)


silhouette()
os.makedirs('og', exist_ok=True)
# 메인 og
im, d = base()
# 아까 구성 그대로, 글씨만 크게(11 → 22·33, 사용자 11-23)
d.text((40, 30), '나루 · 낚시 유형 테스트', font=font(22), fill=SKY)
d.text((40, 66), '나는 어떤', font=font(33), fill=(255, 255, 255))
d.text((40, 106), '낚시꾼일까?', font=font(33), fill=(255, 255, 255))
d.line((340, 0, 340, H - 46), fill=(255, 255, 255, 90), width=1)
d.rectangle((336, H - 50, 344, H - 46), fill=(255, 90, 90)); d.rectangle((336, H - 45, 344, H - 41), fill=(255, 255, 255))
d.text((350, H - 80), '!', font=font(22), fill=GOLD)
save(im, 'og/main.png')

# 낚시꾼별 og + 공유 페이지 r/<유형>-<의상>/ (r/<유형>/ = 그 유형 첫 낚시꾼)
import shutil
shutil.rmtree('r', ignore_errors=True)
for f in os.listdir('og'):
    if f != 'main.png':
        os.remove(os.path.join('og', f))


def share_page(slug, t, outfit, title, line):
    os.makedirs(f'r/{slug}', exist_ok=True)
    open(f'r/{slug}/index.html', 'w', encoding='utf-8').write(f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>{title} - 나루</title>
<meta property="og:type" content="website"><meta property="og:site_name" content="나루">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{line}. 나는 어떤 낚시꾼일까? 질문 7개로 알아보세요.">
<meta property="og:url" content="https://clpak.dev/naru/type/r/{slug}/">
<meta property="og:image" content="https://clpak.dev/naru/type/og/{t}-{outfit}.png?v=2">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0; url=../../?r={t}&c={outfit}&utm_source=share&utm_medium=link&utm_campaign=naru_type">
</head><body><a href="../../?r={t}&c={outfit}">결과 보기</a></body></html>
''')


for t, (name, line, anglers) in types.items():
    for i, (outfit, aname) in enumerate(anglers):
        im, d = base()
        josa = '를' if (ord(aname[-1]) - 0xAC00) % 28 == 0 else '을'
        d.text((40, 30), f'나는 {aname}{josa} 닮은', font=font(22), fill=(200, 205, 220))
        d.text((40, 64), name, font=font(33), fill=(255, 255, 255))
        d.text((40, 120), '나도 해 보기 →', font=font(22), fill=GOLD)
        sc = scene(t, outfit)
        sh = 140 if len(name) <= 5 else 118  # 이름이 길면(수조 꾸미기형) 그림을 줄여 글자와 띄운다
        sc = sc.resize((round(sc.width * sh / sc.height), sh), Image.NEAREST)
        im.alpha_composite(sc, (W - sc.width - (30 if sh == 140 else 14), H - 40 - sh + 14))
        save(im, f'og/{t}-{outfit}.png')
        share_page(f'{t}-{outfit}', t, outfit, f'나는 {name} 낚시꾼 {aname}', line)
        if i == 0:
            share_page(t, t, outfit, f'나는 {name} 낚시꾼', line)
print('ok', {t: [a[1] for a in v[2]] for t, v in types.items()})
