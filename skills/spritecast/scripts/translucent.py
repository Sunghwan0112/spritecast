"""SpriteCast: a pixel sprite made see-through by its 3D model's thickness - a flame's tips, a ghost's tail, water's edge.
Free: the model (the prop's own Tripo GLB) is turned as the camera saw it (the spec's camera and model.yaw; then turned a few degrees
until its outline fits the sprite's best), a ray through each sprite pixel is measured - from the nearest surface to the farthest - and
alpha = 1 - exp(-k t) (t: the thickness over the body's own; light passing through, thin lets more of it), snapped to a few fixed
steps so it stays pixel art. Details inside the figure (eyes, a mouth - far from the body's colours, not on its rim) keep the most.
    python translucent.py PROP.json [KIND]                    # every out-pixel sprite of that prop; KIND: fire | ghost | water (presets/translucent.json)
    python translucent.py --glb MODEL.glb --sprite IN.png --out OUT.png [--kind fire] [--yaw 330] [--pitch 30]
or "translucent": "ghost" (or {"kind": "water", "cap": 0.9}) in the prop's spec, and proppixel.py does it after drawing.
SMOOTH (an illustrated sprite, not pixel art): --smooth, or "style": "smooth" in the spec (or in "translucent") - the alpha as it is, no steps.
WITH NO 3D MODEL (an effect's flame, a fireball, any drawing): --edge - the distance in from its edge stands for the thickness
    python translucent.py --edge --sprite IN.png --out OUT.png [--frames 4] [--cell W H]
  (--frames: a strip of that many, the waver baked in - for an engine that cannot set a sprite's alpha; --cell: IN is a sheet of
  frames that size, each softened on its own)
The sprite as drawn is kept beside it (sprite-solid.png)."""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parent
PRESET = json.loads((HERE.parent / 'presets/translucent.json').read_text(encoding='utf-8'))


def load_mesh(p):
    import trimesh
    s = trimesh.load(str(p)); return s.to_geometry() if hasattr(s, 'to_geometry') else s


def thickness(m, yaw, pitch, H):
    """the model seen from the camera, orthographic: per pixel, farthest surface - nearest (H pixels tall); and where it is"""
    v = m.vertices.copy(); a, b = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]]); Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    v = v @ Ry.T @ Rx.T; v = np.c_[v[:, 0], -v[:, 1], v[:, 2]]
    lo = v[:, :2].min(0); s = (H - 4) / (v[:, 1].max() - lo[1]); p = (v[:, :2] - lo) * s + 2
    W = int(np.ceil(p[:, 0].max())) + 3; zmin = np.full((H, W), np.inf); zmax = np.full((H, W), -np.inf)
    for f in m.faces:
        t = p[f]; z = v[f, 2]; x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0]) + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1])
        if abs(d) < 1e-12: continue
        l0 = ((t[1, 1] - t[2, 1]) * (xs - t[2, 0]) + (t[2, 0] - t[1, 0]) * (ys - t[2, 1])) / d
        l1 = ((t[2, 1] - t[0, 1]) * (xs - t[2, 0]) + (t[0, 0] - t[2, 0]) * (ys - t[2, 1])) / d; l2 = 1 - l0 - l1
        ins = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not ins.any(): continue
        zz = l0 * z[0] + l1 * z[1] + l2 * z[2]; yy = (ys[ins] - 0.5).astype(int); xx = (xs[ins] - 0.5).astype(int)
        np.minimum.at(zmin, (yy, xx), zz[ins]); np.maximum.at(zmax, (yy, xx), zz[ins])
    seen = np.isfinite(zmin); th = np.where(seen, zmax - zmin, 0); yy, xx = np.nonzero(seen)
    return th[yy.min():yy.max() + 1, xx.min():xx.max() + 1], seen[yy.min():yy.max() + 1, xx.min():xx.max() + 1]


def settings(kind=None, over=None):
    k = dict(PRESET['kinds'].get(kind or 'default') or PRESET['kinds']['default'])
    out = {'kind': kind or 'default', 'k': k['k'], 'floor': PRESET['floor'], 'cap': PRESET['cap'], 'levels': PRESET['levels']}
    if k.get('pulse'): out['pulse'] = k['pulse']
    out['style'] = 'pixel'
    out.update({x: y for x, y in (over or {}).items() if x in ('k', 'floor', 'cap', 'levels', 'pulse', 'style')}); return out


def at_frame(st, i, n):
    """the settings for frame i of n: with a "pulse", the thin parts see-through-er for part of the loop (k and the cap lowered by a wave)"""
    p = st.get('pulse')
    if not p or n < 2: return st
    import math
    w = 0.5 - 0.5 * math.cos(2 * math.pi * i / n); s = dict(st)
    s['k'] = st['k'] * (1 - p.get('depth', 0.6) * w); s['cap'] = st['cap'] * (1 - p.get('fade', 0.25) * w)
    s['levels'] = [l * s['cap'] / st['cap'] for l in st['levels']]; s['floor'] = st['floor']; return s


def apply(m, sprite, yaw, pitch, st, refine=True):
    """sprite (RGBA array) → (the same with alpha from the thickness, the yaw used, how well the outline fits)"""
    sp = sprite.copy(); op = sp[..., 3] > 0; ys, xs = np.nonzero(op); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; box = op[y0:y1, x0:x1]
    def fit(y, H=160):
        th, sil = thickness(m, y, pitch, H); S = np.asarray(Image.fromarray(sil.astype(np.uint8) * 255).resize(box.shape[::-1])) > 127
        return (S & box).sum() / max(1, (S | box).sum())
    if yaw is None: yaw = max(range(0, 360, 10), key=fit)
    if refine: yaw = max([yaw + d for d in range(-12, 13, 3)], key=fit)
    iou = fit(yaw)
    th, _ = thickness(m, yaw, pitch, max(400, 6 * box.shape[0]))
    T = np.zeros(op.shape); T[y0:y1, x0:x1] = np.asarray(Image.fromarray(th.astype(np.float32)).resize(box.shape[::-1], Image.BOX))
    t = T / max(1e-6, np.percentile(T[op], 90)); k = st['k']
    a = np.clip((1 - np.exp(-k * t)) / (1 - np.exp(-k)), st['floor'], 1) * st['cap']
    rgb = sp[..., :3].astype(float); far = np.abs(rgb - np.median(rgb[op], 0)).sum(-1) > 180          # details inside: eyes, a mouth
    inner = ndimage.distance_transform_cdt(op, metric='chessboard') > 1; keep = ndimage.binary_dilation(far & inner & op) & inner; a[keep] = np.maximum(a[keep], st['cap'])
    if st.get('style') == 'smooth': a = ndimage.gaussian_filter(a, 0.7)          # (smooth: the alpha as it is, a touch softened - for an illustrated sprite, not pixel art)
    else: LV = np.array(st['levels'], float); a = LV[np.abs(a[..., None] - LV).argmin(-1)]
    sp[..., 3] = (op * a * 255).astype(np.uint8); return sp, yaw % 360, iou


def for_prop(spec_path, kind=None):
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8')); d = Path(spec_path).resolve().parent / spec['name']
    if not spec.get('model'): sys.exit('translucent: the prop needs its 3D model (isoprop.py model)')
    tr = spec.get('translucent'); over = tr if isinstance(tr, dict) else {}
    kind = kind or over.get('kind') or (tr if isinstance(tr, str) else None)
    st = settings(kind, {**({'style': spec['style']} if spec.get('style') else {}), **over}); sys.path.insert(0, str(HERE)); import isoprop
    cam = isoprop.camera(spec); m = load_mesh(Path(spec_path).resolve().parent / spec['model']['glb'])
    out = d / 'out-pixel'; pj = json.loads((out / 'pixel.json').read_text())
    for v, e in pj['views'].items():
        f = out / e['file']; solid = f.with_name(f.stem + '-solid.png')
        if not solid.exists(): f.replace(solid)          # (as drawn, kept: what every later run starts from)
        im, yaw, iou = apply(m, np.asarray(Image.open(solid).convert('RGBA')), cam['yaw'] + spec['model'].get('yaw', 0) + int(v), cam['pitch'], st)
        Image.fromarray(im).save(f); e['translucent'] = {**st, 'yaw': yaw, 'outline_fit': round(float(iou), 2)}
        print(f'translucent: {f} - {st["kind"]}, alpha {st["floor"]}-{st["cap"]} (the model turned {yaw}°, outline fit {iou:.2f}; as drawn: {solid.name})')
    (out / 'pixel.json').write_text(json.dumps(pj, indent=1))


def edge(sprite, E=None, smooth=False):
    """no model: alpha by how far in from the edge (8-neighbour steps) - the rim, the next, inside; a bright core kept. smooth: a gradient
    from the rim in over 4 px instead of steps (an illustrated flame)"""
    E = E or PRESET['edge']; sp = sprite.copy(); op = sp[..., 3] > 0; l = sp[..., :3].astype(float).mean(-1)
    if smooth:
        d = ndimage.distance_transform_edt(op); a = E['rim'] + (E['inside'] - E['rim']) * np.clip((d - 0.5) / 4, 0, 1); a = np.where(l > E['core_light'], np.maximum(a, E['core'] * np.clip(d / 3, 0, 1)), a)
    else:
        d = ndimage.distance_transform_cdt(op, metric='chessboard')
        a = np.where(d <= 1, E['rim'], np.where(d == 2, E['next'], E['inside'])); a = np.where((l > E['core_light']) & (d > 1), E['core'], a)
    sp[..., 3] = (sp[..., 3] * np.where(op, a, 0)).round().astype(np.uint8); return sp


def edge_sheet(sheet, cell=None, frames=1, smooth=False):
    """each cell softened on its own; with frames > 1, a strip of the waver (the whole times each step; smooth: a sine, not steps)"""
    if cell:
        cw, ch = cell; out = sheet.copy()
        for y in range(0, sheet.shape[0], ch):
            for x in range(0, sheet.shape[1], cw): out[y:y + ch, x:x + cw] = edge(sheet[y:y + ch, x:x + cw], smooth=smooth)
    else: out = edge(sheet, smooth=smooth)
    if frames <= 1: return out
    W = PRESET['edge']['waver']; fr = []
    for i in range(frames):
        m = (0.83 + 0.17 * np.cos(2 * np.pi * i / frames)) if smooth else W[i * len(W) // frames % len(W)]
        f = out.copy(); f[..., 3] = (f[..., 3] * m).round().astype(np.uint8); fr.append(f)
    return np.concatenate(fr, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec', nargs='?'); ap.add_argument('kind', nargs='?'); ap.add_argument('--glb'); ap.add_argument('--sprite'); ap.add_argument('--out')
    ap.add_argument('--kind', dest='kind2'); ap.add_argument('--edge', action='store_true'); ap.add_argument('--frames', type=int, default=1); ap.add_argument('--cell', type=int, nargs=2); ap.add_argument('--smooth', action='store_true', help='an illustrated sprite: the alpha as it is (no steps), the waver a sine'); ap.add_argument('--yaw', type=float); ap.add_argument('--pitch', type=float, default=30)
    A = ap.parse_args()
    if A.edge:
        if not (A.sprite and A.out): ap.error('--edge needs --sprite and --out')
        im = edge_sheet(np.asarray(Image.open(A.sprite).convert('RGBA')), A.cell, A.frames, A.smooth); Image.fromarray(im).save(A.out)
        return print(f'translucent: {A.out} - by its edge (no model)' + (f', {A.frames} frames of the waver' if A.frames > 1 else ''))
    if A.spec: return for_prop(A.spec, A.kind or A.kind2)
    if not (A.glb and A.sprite and A.out): ap.error('PROP.json, or --glb --sprite --out')
    im, yaw, iou = apply(load_mesh(A.glb), np.asarray(Image.open(A.sprite).convert('RGBA')), A.yaw, A.pitch, settings(A.kind2, {'style': 'smooth'} if A.smooth else None))
    Image.fromarray(im).save(A.out); print(f'translucent: {A.out} - the model turned {yaw}°, outline fit {iou:.2f}')


if __name__ == '__main__': main()
