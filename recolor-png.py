#!/usr/bin/env python3
"""Recolour accent pixels in PNG files.

usage: recolor-png.py [-m '#35a854 #4d7c0f'] [-e '#70737a #427b58'] FILE.png ...

-m (hue mode): every pixel whose hue is close to a source colour is moved to
the matching target colour: hue is replaced, saturation scaled, and lightness
remapped piecewise-linearly so that pixels darker or lighter than the source
(shadows, anti-aliased edges, blends with white) keep their relationship to the
accent. Grey and white pixels, and pixels of unrelated hues, are left alone.

-e (exact mode): for accents too grey for hue matching (Mint-Y-Grey's #70737a).
A pixel that is a blend of the source with any neutral grey (anti-aliasing
against white, the dark variants' backgrounds) becomes the same blend of the
target. A neutral source (r = g = b, give or take two) matches neutral pixels
of the same lightness, which lets grey assets take on a tint.

Alpha is preserved. Files are only rewritten when a pixel actually changed.
"""
import argparse
import colorsys
import sys
from PIL import Image

HUE_TOLERANCE = 40 / 360.0  # how far (in hue) from a source colour we still recolour
MIN_SATURATION = 0.10       # below this a pixel is treated as grey and left alone


def parse_hex(s):
    s = s.strip().lstrip('#')
    if len(s) != 6:
        raise ValueError(f'bad colour {s!r}')
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def hue_dist(a, b):
    d = abs(a - b)
    return min(d, 1.0 - d)


def build_mappings(specs):
    maps = []
    for spec in specs:
        parts = spec.replace(':', ' ').split()
        if len(parts) != 2:
            raise ValueError(f'mapping must be "FROM TO": {spec!r}')
        src, dst = (colorsys.rgb_to_hls(*parse_hex(p)) for p in parts)
        maps.append((src, dst))
    return maps


def remap(h, l, s, src, dst):
    sh, sl, ss = src
    dh, dl, ds = dst
    ns = min(1.0, s * (ds / ss)) if ss > 0 else s
    if l <= sl:
        nl = l * (dl / sl) if sl > 0 else l
    else:
        nl = dl + (l - sl) * (1.0 - dl) / (1.0 - sl)
    return dh, max(0.0, min(1.0, nl)), ns


EXACT_RESIDUAL = 2.5   # per-channel tolerance when decomposing a pixel into source + neutral
NEUTRAL_SPREAD = 2     # max(r,g,b) - min(r,g,b) at or below this is a neutral grey


def build_exact(specs):
    chromatic, neutral = [], []
    for spec in specs:
        parts = spec.replace(':', ' ').split()
        if len(parts) != 2:
            raise ValueError(f'mapping must be "FROM TO": {spec!r}')
        src = tuple(round(c * 255) for c in parse_hex(parts[0]))
        dst = tuple(round(c * 255) for c in parse_hex(parts[1]))
        m = sum(src) / 3.0
        cv = tuple(c - m for c in src)
        n2 = sum(c * c for c in cv)
        if max(src) - min(src) <= NEUTRAL_SPREAD:
            neutral.append((m, src, dst))
        else:
            chromatic.append((m, cv, n2, src, dst))
    return chromatic, neutral


def exact_neutral(rgb, neutral):
    """The target for a neutral pixel, keeping its small offset from the listed source."""
    if max(rgb) - min(rgb) > NEUTRAL_SPREAD or not neutral:
        return None
    pm = sum(rgb) / 3.0
    m, src, dst = min(neutral, key=lambda n: abs(n[0] - pm))
    if abs(m - pm) > 1.5:
        return None
    return tuple(max(0, min(255, d + (p - s))) for p, s, d in zip(rgb, src, dst))


def exact_remap(rgb, chromatic, neutral):
    pm = sum(rgb) / 3.0
    pv = tuple(c - pm for c in rgb)
    for m, cv, n2, src, dst in chromatic:
        t = sum(p * c for p, c in zip(pv, cv)) / n2
        if t < 0.08 or t > 1.15:
            continue
        if max(abs(p - t * c) for p, c in zip(pv, cv)) > EXACT_RESIDUAL:
            continue
        t = min(t, 1.0)
        k = (pm - t * m) / (1.0 - t) if t < 0.999 else 0.0
        k = max(0.0, min(255.0, k))
        grey = (round(k),) * 3
        grey = exact_neutral(grey, neutral) or grey
        return tuple(round(d * t + g * (1.0 - t)) for d, g in zip(dst, grey))
    return exact_neutral(rgb, neutral)


def recolor(path, maps, exact=((), ())):
    chromatic, neutral = exact
    im = Image.open(path)
    mode = im.mode
    rgba = im.convert('RGBA')
    px = rgba.load()
    w, hgt = rgba.size
    cache = {}
    changed = False
    for y in range(hgt):
        for x in range(w):
            r, g, b, a = px[x, y]
            key = (r, g, b)
            if key in cache:
                out = cache[key]
            else:
                out = key
                h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
                hit = exact_remap(key, chromatic, neutral) if (chromatic or neutral) else None
                if hit is not None:
                    out = hit
                elif maps and s >= MIN_SATURATION:
                    best = min(maps, key=lambda m: hue_dist(h, m[0][0]))
                    if hue_dist(h, best[0][0]) <= HUE_TOLERANCE:
                        nh, nl, ns = remap(h, l, s, best[0], best[1])
                        nr, ng, nb = colorsys.hls_to_rgb(nh, nl, ns)
                        out = (round(nr * 255), round(ng * 255), round(nb * 255))
                cache[key] = out
            if out != key:
                px[x, y] = (out[0], out[1], out[2], a)
                changed = True
    if changed:
        if mode in ('RGB', 'RGBA', 'LA', 'L', 'P'):
            rgba.save(path)
        else:
            rgba.convert(mode).save(path)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-m', '--map', action='append', default=[], help='"#from #to", hue mode (repeatable)')
    ap.add_argument('-e', '--exact', action='append', default=[], help='"#from #to", exact mode (repeatable)')
    ap.add_argument('files', nargs='+')
    args = ap.parse_args()
    if not args.map and not args.exact:
        ap.error('at least one -m or -e mapping is needed')
    maps = build_mappings(args.map)
    exact = build_exact(args.exact)
    n = 0
    for f in args.files:
        try:
            if recolor(f, maps, exact):
                n += 1
        except Exception as e:  # keep going; report at the end
            print(f'{f}: {e}', file=sys.stderr)
    print(f'recoloured {n} of {len(args.files)} PNG files')


if __name__ == '__main__':
    main()
