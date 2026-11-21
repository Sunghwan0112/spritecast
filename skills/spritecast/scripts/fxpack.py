"""Pixel-art effects for the game round the sprites - free, nothing drawn: the 253 effects of PVFX Foundry (CC0 1.0, by Pixel VFX Studio)
that come with SpriteCast (effects/pvfx/: its strict tier - binary alpha, a limited palette), found, looked at, and written out for a
game at its sprites' pixel size and, if asked, in their colours.

    python fxpack.py list [--search water] [--category impacts]      what there is (id, size, frames, what it shows)
    python fxpack.py preview water/bubble-burst impacts/hit-spark ... -> fx-preview.png: eight frames of each, at 2x
    python fxpack.py export water/bubble-burst --out assets/fx [--as hit] [--scale 2] [--palette CHAR.json | FILE] [--hue 200] [--fire]
    python fxpack.py export --set water-swing --out assets/fx       a SWING'S SET: the effects a swing round the character plays
    python fxpack.py preview --set fire-swing                        together, each with when and on which layer (sets, below)
        -> <out>/<as>.png (the sheet, a grid) and <out>/fx.json (each effect written there: w, h, pivot px/py, frames n, columns,
           ms a frame, loop, where it came from) - one fx.json for all, what a game reads to play them (Rain Girl's game.js: fx())

  --scale     whole times only, so a pixel stays a pixel (a ring drawn at 2x was as wide as the backhand it marked)
  --palette   every pixel to the nearest colour of a character's pixel set (its out-pixel*/ strips: CHAR.json) or of a palette file
              (a .png's colours, or a name `pixelart.py --palette list` knows) - the effect in the game's own colours
  --hue       turn the effect's hues to this one (0-360), its lights and darks kept: a blue fire from the red one
  --fire      its lights and darks to a fire's colours (ember red, orange, yellow, white-hot) - a steel or water effect as fire; --hue on
              a blue ring gave a washed-out pink, not a flame (the user saw it)

SETS (--set): what a swing round the character plays together, at 2x (the scale the game draws a ring at), the user's choice for Rain
Girl's backhand (2026-11-21: "the right one looks better - keep this pairing, fire and water"):
  water-swing  impacts/shockwave-ring (on the ground, from the swing's start) + water/ripple (on the ground, 100 ms after it, from its
               third cell - its first two are a drop falling) + melee/spin-slash (round her at the waist, cut at its pivot's line)
  fire-swing   fire/flame-ring (its flames stand up: cut at its pivot's line, the far half behind her, the near half in front) +
               melee/spin-slash --fire (the pack has no fire spin)
  fx.json gets "sets": {name: [{"fx", "at" ms after the swing's start, "layer": ground | split, "y": px from her feet to the pivot}]}.
  Water has no ring of its own in the pack (water/: splash, ripple, whirlpool, a geyser): the shockwave ring is a blue one and reads as
  water.

How to use one in a game: play the sheet's cells in order at "ms", from the pivot (where it happens: a hit's point, a ring's middle),
once (or round and round when "loop"). A thing that flies (projectiles/*-flight) is drawn going right: turn it the way it goes.
A RING round a character (melee/spin-slash, impacts/shockwave-ring at waist height) is cut at the pivot's line: the half above drawn
behind the character, the half below in front - drawn whole in front, the ring went through her body (the user saw it).
The pack's licence (CC0 1.0) is effects/pvfx/LICENSE.txt; its names and marks are its own - say where an effect came from."""
import argparse, colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; PACK = HERE.parent / 'effects' / 'pvfx'
SETS = {          # a swing's effects together: (effect, its name in fx.json, ms after the swing's start, layer, px above her feet, cells skipped, fire)
    'water-swing': [('impacts/shockwave-ring', 'ring', 0, 'ground', 0, 0, False), ('water/ripple', 'ripple', 100, 'ground', 0, 2, False),
                    ('melee/spin-slash', 'spin', 0, 'split', 26, 0, False)],
    'fire-swing': [('fire/flame-ring', 'flamering', 0, 'split', 0, 0, False), ('melee/spin-slash', 'spin-fire', 0, 'split', 26, 0, True)],
}
FIRE = np.array([[90, 18, 10], [176, 40, 14], [236, 96, 20], [252, 168, 40], [255, 226, 120], [255, 250, 220]], float)          # ember to white-hot


def index():
    if not (PACK / 'index.json').exists(): sys.exit(f'fxpack: no effects at {PACK}')
    return json.loads((PACK / 'index.json').read_text())['effects']


def sheet(eid):
    d = PACK / eid
    if not (d / 'manifest.json').exists():
        near = [e['id'] for e in index() if eid.split('/')[-1] in e['id']]
        sys.exit(f'fxpack: no effect "{eid}"' + (f' - did you mean {", ".join(near[:6])}?' if near else ' - `fxpack.py list --search ...`'))
    m = json.loads((d / 'manifest.json').read_text()); im = Image.open(d / 'sheet.png').convert('RGBA'); w, h = m['source_size']
    ms = round(sum(f['duration']['numerator_ms'] / f['duration']['denominator'] for f in m['frames']) / len(m['frames']))
    return im, {'w': w, 'h': h, 'px': m['pivot'][0], 'py': m['pivot'][1], 'n': len(m['frames']), 'cols': im.width // w, 'ms': ms, 'loop': m.get('loop_mode') not in (None, 'none')}


def cells(im, e): return [im.crop(((i % e['cols']) * e['w'], (i // e['cols']) * e['h'], (i % e['cols'] + 1) * e['w'], (i // e['cols'] + 1) * e['h'])) for i in range(e['n'])]


def palette_of(arg):
    p = Path(arg)
    if p.suffix == '.json' and p.exists():          # a character: the colours of its pixel set
        s = json.loads(p.read_text()); d = p.resolve().parent / s['name']; outs = sorted(d.glob('out-pixel*/'))
        if not outs: sys.exit(f'fxpack: {p.name} has no pixel set yet (out-pixel*/) - run pixelart.py first, or give a palette')
        cols = set()
        for f in outs[0].glob('*.png'):
            a = np.asarray(Image.open(f).convert('RGBA')); cols.update(map(tuple, a[a[..., 3] == 255][:, :3]))
        return np.array(sorted(cols), float)
    sys.path.insert(0, str(HERE)); import pixelkit as P          # a palette file (what Aseprite reads) or one by name, as pixelart.py --palette knows them
    return np.array(P.load_palette(arg), float)


def to_palette(im, P):
    a = np.asarray(im).copy(); m = a[..., 3] > 0; px = a[m][:, :3].astype(float)
    if not len(px): return im
    u, inv = np.unique(px, axis=0, return_inverse=True); j = ((u[:, None] - P[None]) ** 2).sum(2).argmin(1)
    a[m, :3] = P[j][inv.ravel()].astype(np.uint8); return Image.fromarray(a)


def to_hue(im, hue):
    a = np.asarray(im).copy(); m = a[..., 3] > 0
    for y, x in zip(*np.nonzero(m)):
        r, g, b = a[y, x, :3] / 255.0; _, l, s = colorsys.rgb_to_hls(r, g, b); a[y, x, :3] = np.round(np.array(colorsys.hls_to_rgb(hue / 360, l, s)) * 255)
    return Image.fromarray(a)


def to_fire(cs):
    """the cells' lights and darks to a fire's colours - the lightness taken over all the cells, so a cell fading out goes to embers"""
    a = [np.asarray(c).copy() for c in cs]; Ls = [x[..., :3].astype(float).mean(-1) / 255 for x in a]; on = np.concatenate([L[x[..., 3] > 0] for L, x in zip(Ls, a)])
    lo, span = (on.min(), max(1e-6, np.ptp(on))) if len(on) else (0, 1); out = []
    for x, L in zip(a, Ls):
        t = np.clip((L - lo) / span, 0, 1) * (len(FIRE) - 1); i0 = np.floor(t).astype(int).clip(0, len(FIRE) - 2); f = (t - i0)[..., None]
        x[..., :3] = (FIRE[i0] * (1 - f) + FIRE[i0 + 1] * f).round().astype(np.uint8); out.append(Image.fromarray(x))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument('cmd', choices=['list', 'preview', 'export'])
    ap.add_argument('ids', nargs='*'); ap.add_argument('--search', default=''); ap.add_argument('--category', default=''); ap.add_argument('--out', default='')
    ap.add_argument('--as', dest='as_', default=''); ap.add_argument('--scale', type=int, default=1); ap.add_argument('--palette', default=''); ap.add_argument('--hue', type=float, default=None)
    ap.add_argument('--fire', action='store_true'); ap.add_argument('--set', dest='set_', default='', choices=[''] + list(SETS))
    A = ap.parse_args()
    if A.cmd == 'list':
        q = A.search.lower(); n = 0
        for e in index():
            if A.category and e['category'] != A.category: continue
            if q and q not in (e['id'] + ' ' + e.get('name', '') + ' ' + ' '.join(e.get('tags') or []) + ' ' + e.get('description', '')).lower(): continue
            print(f"{e['id']:34s} {e['size'][0]}x{e['size'][1]:<4} {e['frames']:>3}f {'loop' if e.get('loop') else '    '}  {e.get('description', '')[:90]}"); n += 1
        print(f'{n} effects (PVFX Foundry, CC0 1.0)'); return
    if A.set_:
        if A.cmd == 'preview': A.ids = [e for e, *_ in SETS[A.set_]]
        else: return export_set(A)
    if not A.ids: sys.exit('fxpack: name an effect (fxpack.py list) or a set (--set water-swing | fire-swing)')
    if A.cmd == 'preview':
        rows = [(i, *sheet(i)) for i in A.ids]; CW = 2 * max(e['w'] for _, _, e in rows) + 8; H = sum(2 * e['h'] + 10 for _, _, e in rows)
        from PIL import ImageDraw
        o = Image.new('RGB', (8 * CW + 10, H), (58, 74, 52)); d = ImageDraw.Draw(o); y = 0
        for i, im, e in rows:
            cs = cells(im, e)
            if A.set_: _f = [m for m in SETS[A.set_] if m[0] == i][0]; cs = cs[_f[5]:]; cs = to_fire(cs) if _f[6] else cs; e = dict(e, n=len(cs))          # (a set's effect as the set plays it)
            elif A.fire: cs = to_fire(cs)
            pick = [round(k * (e['n'] - 1) / 7) for k in range(8)] if e['n'] > 8 else range(e['n'])
            for k, c in enumerate(pick): b = cs[c].resize((2 * e['w'], 2 * e['h']), Image.NEAREST); o.paste(b, (5 + k * CW, y), b)
            d.text((5, y + 2), f"{i}  {e['w']}x{e['h']} {e['n']}f {e['ms']}ms", fill=(240, 240, 230)); y += 2 * e['h'] + 10
        out = Path(A.out or 'fx-preview.png'); o.save(out); print(f'preview: {out}'); return
    if not A.out: sys.exit('fxpack export: --out DIR (where the game keeps its effects)')
    out = Path(A.out); out.mkdir(parents=True, exist_ok=True); fj = out / 'fx.json'; meta = json.loads(fj.read_text()) if fj.exists() else {}
    P = palette_of(A.palette) if A.palette else None
    for i in A.ids:
        im, e = sheet(i); name = (A.as_ if len(A.ids) == 1 and A.as_ else i.split('/')[-1]); cs = cells(im, e)
        if A.hue is not None: cs = [to_hue(c, A.hue) for c in cs]
        if A.fire: cs = to_fire(cs)
        if P is not None: cs = [to_palette(c, P) for c in cs]
        k = max(1, A.scale); w, h = e['w'] * k, e['h'] * k; g = Image.new('RGBA', (w * e['cols'], h * (-(-e['n'] // e['cols']))))
        for c_, c in enumerate(cs): g.paste(c.resize((w, h), Image.NEAREST), ((c_ % e['cols']) * w, (c_ // e['cols']) * h))
        g.save(out / f'{name}.png', optimize=True)
        meta[name] = dict(e, w=w, h=h, px=e['px'] * k, py=e['py'] * k, src=f'PVFX Foundry {i} (CC0 1.0)')
        print(f"export: {name}.png  {w}x{h} x{e['n']} ({e['cols']} a row), pivot {e['px'] * k},{e['py'] * k}, {e['ms']} ms a frame" + (' (loops)' if e['loop'] else ''))
    fj.write_text(json.dumps(meta, indent=1)); print(f'  -> {fj} - where it came from is in each entry ("src"); the pack\'s licence: {PACK / "LICENSE.txt"}')


def export_set(A):
    """a swing's set: each effect written as `export` writes one (at --scale, 2 unless given), and fx.json's "sets" saying when and where"""
    if not A.out: sys.exit('fxpack export --set: --out DIR (where the game keeps its effects)')
    out = Path(A.out); out.mkdir(parents=True, exist_ok=True); fj = out / 'fx.json'; meta = json.loads(fj.read_text()) if fj.exists() else {}
    k = A.scale if A.scale > 1 else 2; plan = []
    for eid, name, at, layer, y, skip, fire in SETS[A.set_]:
        im, e = sheet(eid); cs = cells(im, e)[skip:]
        if fire: cs = to_fire(cs)
        w, h = e['w'] * k, e['h'] * k; n = len(cs); g = Image.new('RGBA', (w * e['cols'], h * (-(-n // e['cols']))))
        for c_, c in enumerate(cs): g.paste(c.resize((w, h), Image.NEAREST), ((c_ % e['cols']) * w, (c_ // e['cols']) * h))
        g.save(out / f'{name}.png', optimize=True)
        meta[name] = dict(e, w=w, h=h, px=e['px'] * k, py=e['py'] * k, n=n, loop=False, src=f'PVFX Foundry {eid} (CC0 1.0)' + (' - as fire' if fire else '') + (f' - from cell {skip + 1}' if skip else ''))
        plan.append({'fx': name, 'at': at, 'layer': layer, 'y': y * k})
        print(f"export: {name}.png  {w}x{h} x{n}, at {at} ms, {'on the ground' if layer == 'ground' else 'cut at its pivot: far half behind her, near half in front'}" + (f', {y * k} px above her feet' if y else ''))
    meta.setdefault('sets', {})[A.set_] = plan; fj.write_text(json.dumps(meta, indent=1))
    print(f'  -> {fj} "sets"/{A.set_}: play each from the swing\'s start + "at", its pivot "y" px above her feet; "ground" under her shadow, "split" cut at the pivot\'s line')


if __name__ == '__main__': main()
