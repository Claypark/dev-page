"""나루 낚시 유형 테스트 — 글꼴 서브셋 + og 그림 + 공유용 r/<유형>/ 페이지 생성.
문구(i18n.json, 한·영·일·스페인어)를 바꾸면 다시 돌린다: cd dev-page/naru/type && python3 build.py
i18n.json은 index.html의 <script id="i18n">에 그대로 들어간다(페이지는 이 파일 하나로 동작)."""
import json, os, re, subprocess
from PIL import Image, ImageDraw, ImageFont

GAL = '/Users/clpak/workspace/mi-app/apps/naru/app/assets/fonts/Galmuri11.ttf'
html = open('index.html', encoding='utf-8').read()
I18N = json.load(open('i18n.json', encoding='utf-8'))
html = re.sub(r'(<script id="i18n" type="application/json">).*?(</script>)',
              lambda m: m.group(1) + json.dumps(I18N, ensure_ascii=False, separators=(',', ':')) + m.group(2), html, flags=re.S)

# 1) 글꼴 서브셋 (페이지에 나오는 글자만)
chars = set(html) | set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !?.,~/←·')
from fontTools.ttLib import TTFont
cmap = TTFont(GAL).getBestCmap()
miss = sorted({c for c in json.dumps(I18N, ensure_ascii=False) if ord(c) > 127 and ord(c) not in cmap})
assert not miss, f'Galmuri11에 없는 글자: {miss}'
open('/tmp/naru_type_chars.txt', 'w').write(''.join(sorted(chars)))
subprocess.run(['pyftsubset', GAL, '--text-file=/tmp/naru_type_chars.txt', '--flavor=woff2',
                '--output-file=galmuri11-sub.woff2'], check=True)
# 글꼴이 바뀌면 브라우저 캐시를 넘기도록 주소에 내용 해시를 붙인다
import hashlib
h = hashlib.md5(open('galmuri11-sub.woff2', 'rb').read()).hexdigest()[:8]
html = re.sub(r"url\('galmuri11-sub\.woff2[^']*'\)", f"url('galmuri11-sub.woff2?v={h}')", html)
open('index.html', 'w', encoding='utf-8').write(html)

# 2) 유형별 낚시꾼 번호는 index.html의 TYPES에서 읽는다 (한 곳에서만 관리)
types = {k: re.findall(r"'(\d+)'", a) for k, a in re.findall(r"(\w+): \{ anglers: (\[[^\]]*\])", html)}
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
    ImageDraw.Draw(out).line((tx, ty + 2, tx, fy + 2), fill=(225, 228, 238, 255), width=3)  # 불투명·굵게 — og는 0.57배로 줄여서 1px 선은 사라진다
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
import shutil
shutil.rmtree('og', ignore_errors=True)
shutil.rmtree('r', ignore_errors=True)
for l in I18N:
    if l != 'ko':
        shutil.rmtree(l, ignore_errors=True)


def fill(tpl, **v):
    return re.sub(r'\{([^}]+)\}', lambda m: v.get(m.group(1), ''), tpl)


def josa(n):
    return '를' if (ord(n[-1]) - 0xAC00) % 28 == 0 else '을'


def fit(d, text, maxw):
    """이름이 한 줄(33)에 안 들어가면 띄어쓰기에서 두 줄로, 그래도 넘치면 22로 줄인다."""
    if d.textlength(text, font=font(33)) <= maxw:
        return [text], 33
    words = text.split(' ')
    cuts = [[' '.join(words[:i]), ' '.join(words[i:])] for i in sorted(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))]
    if text.endswith('タイプ') and ' ' not in text:  # 일본어는 띄어쓰기가 없으니 '…タイプ' 앞에서 나눈다
        cuts.append([text[:-3], 'タイプ'])
    for size in (33, 22):
        for ls in cuts:
            if all(d.textlength(x, font=font(size)) <= maxw for x in ls):
                return ls, size
    return [text], 22


def og_path(l, name):
    return f'og/{name}.png' if l == 'ko' else f'og/{l}/{name}.png'


def head(l, title, desc, url, img):
    return f'''<!DOCTYPE html>
<html lang="{l}"><head><meta charset="UTF-8">
<title>{title} - {I18N[l]['docTitle'].split(' - ')[-1]}</title>
<meta property="og:type" content="website"><meta property="og:site_name" content="{I18N[l]['docTitle'].split(' - ')[-1]}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://clpak.dev/naru/type/{img}?v=3">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">'''


def redirect_page(path, l, title, desc, img, query):
    """크롤러용 og만 달고 본 페이지로 넘긴다(공유 링크의 ?p= 등은 그대로 붙여 넘긴다)."""
    os.makedirs(path, exist_ok=True)
    to = '/naru/type/?' + query + ('' if l == 'ko' else f'&lang={l}')
    open(f'{path}/index.html', 'w', encoding='utf-8').write(head(l, title, desc, f'https://clpak.dev/naru/type/{path}/', img) + f'''
<meta http-equiv="refresh" content="0; url={to}">
<script>location.replace('{to}' + (location.search ? '&' + location.search.slice(1) : ''));</script>
</head><body><a href="{to}">{I18N[l]['seeResult']}</a></body></html>
''')


for l, L in I18N.items():
    os.makedirs(os.path.dirname(og_path(l, 'x')), exist_ok=True)
    # 메인 og — 구성 그대로, 글씨만 크게(11 → 22·33, 사용자 11-23)
    im, d = base()
    d.text((40, 30), L['ogMain'][0], font=font(22), fill=SKY)
    d.text((40, 66), L['ogMain'][1], font=font(33), fill=(255, 255, 255))
    d.text((40, 106), L['ogMain'][2], font=font(33), fill=(255, 255, 255))
    d.line((340, 0, 340, H - 46), fill=(255, 255, 255, 90), width=1)
    d.rectangle((336, H - 50, 344, H - 46), fill=(255, 90, 90)); d.rectangle((336, H - 45, 344, H - 41), fill=(255, 255, 255))
    d.text((350, H - 80), '!', font=font(22), fill=GOLD)
    save(im, og_path(l, 'main'))
    if l != 'ko':  # 언어별 입구 clpak.dev/naru/type/<언어>/ — 그 언어 og로 보이고 본 페이지로 넘어간다
        redirect_page(l, l, L['ogMainTitle'], L['ogMainDesc'], og_path(l, 'main'), 'utm_source=lang_link')

    # 낚시꾼별 og + 공유 페이지 r/<유형>-<의상>/ (r/<유형>/ = 그 유형 첫 낚시꾼), 한국어 말고는 r/<언어>/…
    for t, ids in types.items():
        name, line = L['types'][t]['name'], L['types'][t]['line']
        for i, outfit in enumerate(ids):
            aname = L['anglers'][outfit]
            im, d = base()
            pre = fill(L['ogPre'], a=aname, **{'을': josa(aname)})
            sc = scene(t, outfit)
            sh = 140
            lines, size = fit(d, name, W - 40 - 30 - round(sc.width * sh / sc.height) - 8)
            if size < 33 or len(lines) > 1 or len(name) > 5:  # 이름이 길면 그림을 줄여 글자와 띄운다
                sh = 118
                lines, size = fit(d, name, W - 40 - 14 - round(sc.width * sh / sc.height) - 8)
            two = len(lines) > 1  # 두 줄이면 위로 당겨서 '해 보기'가 물에 안 닿게
            d.text((40, 24 if two else 30), pre, font=font(22), fill=(200, 205, 220))
            y = 56 if two else 64
            for ln in lines:
                d.text((40, y), ln, font=font(size), fill=(255, 255, 255))
                y += size + 2
            d.text((40, y + 8 if two else 120), L['ogCta'], font=font(22), fill=GOLD)
            sc = sc.resize((round(sc.width * sh / sc.height), sh), Image.NEAREST)
            im.alpha_composite(sc, (W - sc.width - (30 if sh == 140 else 14), H - 40 - sh + 14))
            img = og_path(l, f'{t}-{outfit}')
            save(im, img)
            title = fill(L['shareTitle'], a=aname, t=name, **{'을': josa(aname)})  # og 그림 문구와 같게('밤낚시꾼 낚시꾼' 겹침 방지)
            desc = fill(L['ogDesc'], line=line)
            q = f'r={t}&c={outfit}&utm_source=share&utm_medium=link&utm_campaign=naru_type'
            base_dir = 'r' if l == 'ko' else f'r/{l}'
            redirect_page(f'{base_dir}/{t}-{outfit}', l, title, desc, img, q)
            if i == 0:
                redirect_page(f'{base_dir}/{t}', l, title, desc, img, q)
print('ok', {t: [I18N['ko']['anglers'][o] for o in v] for t, v in types.items()})
