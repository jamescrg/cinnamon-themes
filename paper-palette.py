#!/usr/bin/env python3
"""Generate Mint-Y-Paper.sed and Mint-Y-Paper.recolor from a built Mint-Y-Grey-Custom tree.

The palette is jamescraig.dev's: paper #f2f0ea, ink #3c3836 (gruvbox dark1),
a faded-aqua accent #427b58 (hover #2c6544) and tan borders (#bdae93). Every
grey in the stock theme keeps its lightness and takes on the paper's warmth;
the Mint-Y-Grey accent ramp (grey shades that correspond 1:1 to stock Mint-Y's
green shades) is remapped onto the aqua by relative lightness.

usage: paper-palette.py THEME_DIR --sed OUT.sed --recolor OUT.recolor [--strength 0.6] [--swatch out.png]
"""
import argparse, collections, math, os, re, sys

# ---- colour maths (sRGB <-> OKLCH) -------------------------------------------
def _lin(x): return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
def _gam(x):
    x = max(0.0, min(1.0, x))
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
def hex_to_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def rgb_to_hex(rgb): return '#%02x%02x%02x' % tuple(max(0, min(255, round(c))) for c in rgb)
def rgb_to_oklch(rgb):
    r, g, b = (_lin(c / 255) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (x ** (1 / 3) if x > 0 else 0 for x in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360
def oklch_to_rgb(L, C, h):
    a = C * math.cos(math.radians(h)); b = C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(_gam(x) * 255 for x in (r, g, bb))

# ---- the warm ramp ------------------------------------------------------------
# (L, chroma, hue) anchors along gruvbox's grey ramp as used by the blog:
# paper f2f0ea, light2 d5c4a1, light3 bdae93, light4 a89984, gray 928374,
# dark4 7c6f64, dark3 665c54, dark2 504945, dark1 3c3836, dark0 282828.
ANCHORS = [(0.999, 0.006, 91.5), (0.955, 0.008, 91.5), (0.90, 0.030, 88.0), (0.82, 0.050, 86.0),
           (0.756, 0.041, 82.3), (0.69, 0.029, 76.0), (0.62, 0.028, 70.0), (0.54, 0.021, 62.0),
           (0.47, 0.015, 55.0), (0.41, 0.011, 50.0), (0.344, 0.007, 48.4), (0.277, 0.003, 48.0), (0.0, 0.0, 48.0)]
GREY_CHROMA = 0.02          # colours at or below this chroma count as grey
PAPER_L = rgb_to_oklch(hex_to_rgb('#f2f0ea'))[0]
STONE_L = rgb_to_oklch(hex_to_rgb('#f5f5f4'))[0]

def warm(hexs, strength):
    """Same lightness (lights scaled so stone-100 lands on the paper), warm hue, chroma from the ramp."""
    L, C, h = rgb_to_oklch(hex_to_rgb(hexs))
    if L > 0.5:
        L = L * (PAPER_L / STONE_L)
    for (L1, C1, h1), (L0, C0, h0) in zip(ANCHORS, ANCHORS[1:]):
        if L0 <= L <= L1:
            t = (L - L0) / (L1 - L0) if L1 > L0 else 0
            C = (C0 + (C1 - C0) * t) * strength
            h = h0 + (h1 - h0) * t
            break
    return rgb_to_hex(oklch_to_rgb(L, C, h))

# ---- the accent ramp ----------------------------------------------------------
# stock Mint-Y green shade -> Mint-Y-Grey shade (same role); the aqua shade is
# derived from the green one by relative lightness and chroma, as recolor-png.py does.
GREEN_BASE = '#35a854'; AQUA_BASE = '#427b58'; AQUA_HOVER = '#2c6544'
ACCENT_PAIRS = [  # (green, grey)
    ('#35a854', '#70737a'), ('#2f954a', '#64666d'), ('#30974c', '#65686e'), ('#30984c', '#66696f'),
    ('#298141', '#585a5f'), ('#236e37', '#4b4d52'), ('#1d5a2d', '#3f4145'), ('#10341a', '#27282a'),
    ('#3bbb5e', '#7c8087'), ('#3ab85c', '#7a7d85'), ('#5acb78', '#94979d'), ('#71d28b', '#a4a7ac'),
    ('#86cb98', '#a9abaf'), ('#9ad4aa', '#b8b9bd'), ('#a4d8b2', '#bfc0c3'), ('#aedcbb', '#c6c7ca'),
    ('#c2e5cc', '#d4d5d7'), ('#d7eedd', '#e2e3e4'), ('#ebf6ee', '#f1f1f2'),
]
ACCENT_RGBA = {  # grey rgba prefixes -> green equivalents (same ramp)
    'rgba(112, 115, 122,': '#35a854', 'rgba(106, 109, 116,': '#2f954a',
    'rgba(88, 90, 95,': '#298141', 'rgba(63, 65, 69,': '#1d5a2d',
}
def aqua_for(green):
    Lg, Cg, _ = rgb_to_oklch(hex_to_rgb(green))
    Lb, Cb, _ = rgb_to_oklch(hex_to_rgb(GREEN_BASE))
    La, Ca, ha = rgb_to_oklch(hex_to_rgb(AQUA_BASE))
    if green == GREEN_BASE: return AQUA_BASE
    if green in ('#2f954a', '#30974c', '#30984c'): return AQUA_HOVER
    L = La * Lg / Lb if Lg <= Lb else La + (Lg - Lb) * (1 - La) / (1 - Lb)
    C = Ca * Cg / Cb
    return rgb_to_hex(oklch_to_rgb(L, min(C, 0.12), ha))

# ---- scan the theme -----------------------------------------------------------
TEXT_GLOB = ('.css', '.svg', '.xml', '.rc')
HEX_RE = re.compile(r'#([0-9a-fA-F]{6})\b')
RGBA_RE = re.compile(r'rgba\((\d+), (\d+), (\d+),')
def scan(theme):
    hexes = collections.Counter(); rgbas = collections.Counter()
    for root, _, files in os.walk(theme):
        for f in files:
            if f.endswith(TEXT_GLOB) or f in ('gtkrc', 'themerc'):
                with open(os.path.join(root, f), errors='replace') as fh:
                    s = fh.read()
                hexes.update('#' + m.lower() for m in HEX_RE.findall(s))
                rgbas.update(tuple(int(x) for x in m) for m in RGBA_RE.findall(s))
    return hexes, rgbas

def scan_png(theme, min_count=40):
    """Neutral (r=g=b, +-1) opaque colours in the PNG assets, for the exact recolour list."""
    try:
        from PIL import Image
    except ImportError:
        return {}
    tot = collections.Counter()
    for root, _, files in os.walk(theme):
        for f in files:
            if not f.endswith('.png'): continue
            im = Image.open(os.path.join(root, f)).convert('RGBA')
            for (r, g, b, a), n in collections.Counter(im.getdata()).items():
                if a > 0 and max(r, g, b) - min(r, g, b) <= 2 and 3 < r < 252:
                    tot[(r, g, b)] += n
    return {rgb_to_hex(k): n for k, n in tot.items() if n >= min_count}

def is_grey(hexs):
    L, C, _ = rgb_to_oklch(hex_to_rgb(hexs))
    return C <= GREY_CHROMA and 0.05 < L < 0.995

PANEL = '#c3c3c6'   # the Cinnamon panel from steps/panel.patch; it gets its own, lower chroma
# Window chrome, a step quieter than the rest but warmer than the panel: title
# bars and header bars (#dbdbdd, wm_bg, also the Cinnamon menu and libadwaita
# sidebars), unfocused title bars (#e3e3e4), Nemo's places sidebar (#e6e6e7)
# and the generic GTK sidebar (#eeeeee).
CHROME = {'#dbdbdd', '#e3e3e4', '#e6e6e7', '#eeeeee'}

def group_strength(h, strength, panel_strength, chrome_strength):
    if h == PANEL: return panel_strength
    if h in CHROME: return chrome_strength
    return strength

def build(theme, strength, panel_strength, base, chrome_strength):
    hexes, rgbas = scan(theme)
    accent = {grey: aqua_for(green) for green, grey in ACCENT_PAIRS}
    special = {'#303030': '#3c3836', '#f5f5f4': base}  # ink exactly; content surfaces to the chosen base
    rules = []                      # (source, target, comment)
    for grey, aqua in accent.items():
        if grey in hexes: rules.append((grey, aqua, 'accent'))
    for pre, green in ACCENT_RGBA.items():
        r, g, b = hex_to_rgb(aqua_for(green))
        rules.append((pre, f'rgba({r}, {g}, {b},', 'accent'))
    for src, dst in special.items():
        if src in hexes: rules.append((src, dst, 'anchor'))
    for h, n in sorted(hexes.items(), key=lambda kv: -kv[1]):
        if h in accent or h in special or not is_grey(h): continue
        w = warm(h, group_strength(h, strength, panel_strength, chrome_strength))
        if w != h: rules.append((h, w, f'{n}x'))
    for (r, g, b), n in sorted(rgbas.items(), key=lambda kv: -kv[1]):
        pre = f'rgba({r}, {g}, {b},'
        h = rgb_to_hex((r, g, b))
        if pre in ACCENT_RGBA or not is_grey(h): continue
        wr, wg, wb = hex_to_rgb(warm(h, group_strength(h, strength, panel_strength, chrome_strength)))
        if (wr, wg, wb) != (r, g, b): rules.append((pre, f'rgba({wr}, {wg}, {wb},', f'{n}x'))
    # sed applies rules in sequence, so a rule whose source is another rule's
    # target must run first; order by that and refuse cycles.
    ordered, pending = [], list(rules)
    while pending:
        progressed = False
        for rule in list(pending):
            s, t, _ = rule
            if not any(t == s2 for s2, _, _ in pending if s2 != s):
                ordered.append(rule); pending.remove(rule); progressed = True
        if not progressed: sys.exit('cyclic colour substitutions: ' + ', '.join(f'{s}->{t}' for s, t, _ in pending))
    ordered.reverse()
    for i, (s, t, _) in enumerate(ordered):
        for s2, _, _ in ordered[i + 1:]:
            if t == s2: sys.exit(f'ordering error {s}->{t} then {s2}')
    return ordered, accent

def write_sed(path, rules, strength):
    with open(path, 'w') as f:
        f.write(f"""# Mint-Y-Paper: generated by paper-palette.py (strength {strength}); do not edit by hand.
# The palette of jamescraig.dev: paper #f2f0ea, ink #3c3836, faded-aqua accent
# #427b58 (hover #2c6544), tan borders. Content surfaces take the blog's subtle
# shade; every other grey keeps its lightness and takes the paper's warmth, the
# window chrome and the panel at lower chroma; the Mint-Y-Grey accent ramp
# becomes the aqua ramp.
# Applied to every stylesheet, rc file and SVG after the shared steps.
""")
        for s, t, c in rules:
            if s.startswith('rgba'):
                f.write(f's/{re.escape(s)}/{t}/g\n'.replace('\\(', '(').replace('\\)', ')').replace('\\ ', ' '))
            else:
                f.write(f's/{s}/{t}/gI\n')

def write_recolor(path, theme, accent, strength):
    neutrals = scan_png(theme)
    with open(path, 'w') as f:
        f.write("""# Mint-Y-Paper PNG recolouring, generated by paper-palette.py; do not edit by hand.
# "<from> <to> exact": pixels that are a blend of <from> with any neutral grey
# (anti-aliasing, dark variants) move to the same blend of <to>; "<from> <to>"
# alone would use the hue-based mode, which cannot see Mint-Y-Grey's grey accent.
""")
        f.write(f'#70737a {accent["#70737a"]} exact\n')
        f.write('# neutral greys in the assets (checkbox borders, switch troughs, title bars) take the paper warmth\n')
        for h, n in sorted(neutrals.items(), key=lambda kv: kv[0]):
            w = warm(h, strength)
            if max(abs(a - b) for a, b in zip(hex_to_rgb(w), hex_to_rgb(h))) >= 2:
                f.write(f'{h} {w} exact\n')

def swatch(path, strengths, theme):
    from PIL import Image, ImageDraw
    roles = [('base', '#f5f5f4'), ('bg', '#e8e8e9'), ('header', '#dbdbdd'), ('panel', '#c3c3c6'), ('border', '#c8c8ce'),
             ('insens', '#a9a9ab'), ('text', '#303030'), ('menu-dark', '#2e2e33'), ('accent', '#70737a'), ('hover', '#64666d'),
             ('pressed', '#585a5f'), ('tint', '#b8b9bd'), ('tint-lt', '#e2e3e4')]
    blog = [('paper', '#f2f0ea'), ('subtle', '#edebe5'), ('code', '#e7e5df'), ('border', '#bdae93'), ('muted', '#6d6156'),
            ('text', '#6a6663'), ('strong', '#524e4c'), ('ink', '#3c3836'), ('accent', '#427b58'), ('hover', '#2c6544')]
    W = 90; H = 60
    rows = 1 + len(strengths)
    im = Image.new('RGB', (W * max(len(roles), len(blog)) + 120, H * rows + 10), '#f2f0ea'); d = ImageDraw.Draw(im)
    accent = {grey: aqua_for(green) for green, grey in ACCENT_PAIRS}
    special = {'#303030': '#3c3836', '#f5f5f4': '#edebe5'}
    for r, s in enumerate(['blog'] + strengths):
        d.text((4, r * H + 24), str(s), fill='#000000')
        cols = blog if s == 'blog' else roles
        for c, (name, h) in enumerate(cols):
            if s != 'blog':
                h = accent.get(h) or special.get(h) or warm(h, s)
            x = 110 + c * W; y = r * H + 5
            d.rectangle((x, y, x + W - 4, y + H - 4), fill=h)
            d.text((x + 3, y + 3), name, fill='#000000' if rgb_to_oklch(hex_to_rgb(h))[0] > 0.6 else '#ffffff')
            d.text((x + 3, y + H - 18), h, fill='#000000' if rgb_to_oklch(hex_to_rgb(h))[0] > 0.6 else '#ffffff')
    im.save(path)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('theme'); ap.add_argument('--sed'); ap.add_argument('--recolor')
    ap.add_argument('--strength', type=float, default=0.6, help='chroma of the warm greys relative to gruvbox (default 0.6)')
    ap.add_argument('--panel-strength', type=float, default=0.3, help='chroma of the Cinnamon panel (default 0.3, quieter than the rest)')
    ap.add_argument('--chrome-strength', type=float, default=0.45, help='chroma of title bars, header bars, sidebars and the Cinnamon menu (default 0.45)')
    ap.add_argument('--base', default='#edebe5', help="content surfaces (text views, lists, Nemo): the blog's subtle shade by default; #f2f0ea is its paper")
    ap.add_argument('--swatch'); ap.add_argument('--swatch-strengths', default='0.4,0.6,0.8,1.0')
    a = ap.parse_args()
    if a.swatch:
        swatch(a.swatch, [float(x) for x in a.swatch_strengths.split(',')], a.theme)
    if a.sed or a.recolor:
        rules, accent = build(a.theme, a.strength, a.panel_strength, a.base.lower(), a.chrome_strength)
        if a.sed: write_sed(a.sed, rules, a.strength); print(f'{a.sed}: {len(rules)} substitutions')
        if a.recolor: write_recolor(a.recolor, a.theme, accent, a.strength); print(f'{a.recolor} written')
