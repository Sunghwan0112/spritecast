"""ground: the ground of a map at the game's own camera - a meadow of 3D plants with a path through it, the ground's gentle rise and
fall, puddles, or a 2D meadow from one grass tile. Free: nothing is drawn by an image model, everything is worked out here.

    python ground.py meadow  GROUND.json     <name>/ground.png (the whole map's ground, pixel art in your palette), ground-front.png + .json
                                             (the plants cut into strips by their roots: draw a strip over whoever stands behind it - feet in
                                             the grass, a tree's foot in it), preview.png
    python ground.py terrain GROUND.json     <name>/terrain.png: a 3D height map's slopes lit by the sun - lay it over the ground
    python ground.py puddles GROUND.json     <name>/puddle-0..4.png: a shallow hollow of water, big to nearly dry (one shape shrinking)
    python ground.py grass2d GROUND.json     <name>/ground.png from one seamless grass tile ("tile"): its tufts cut out and scattered by a
                                             Gaussian density on the iso ground - no repeat, no grid (no 3D)

GROUND.json (every key but "name" may be left out):
  "name": "forest_floor", "size": [960, 540] (px), "ppm": 74 (px a metre: your characters'), "pitch": 30 (the camera, degrees down),
  "sun": [0.42, 1, 0.78] (towards the sun, x right / up / towards the viewer: SpriteCast's light, as the props are baked),
  "plants": "realistic" (ground/realistic: grass, fern, wildflowers, clover - Tripo, textured, come with the skill)
            | [{"glb": "my.glb", "kind": "grass" | "fern" | "flower", "height": 0.3}, ...] (your own),
  "density": 22 (plants a square metre), "ferns": 0.12, "flowers": 0.08 (shares; flowers grow in patches of their own),
  "palette": "props/*.png" (a glob of your sprites: the meadow takes only their colours, as your trees and rocks have them) | a palette
             name or file (pixelkit, as proppixel.py --palette) | left out: 24 colours of its own,
  "tone": 0.58, "saturation": 0.78 (the textured plants darker / less yellow before the palette: a rainy forest; 1, 1: as they are),
  "path": {"points": [[x, y], ...] (screen px, along its middle), "half": 24 (px), "gravel": true, "earth": "dirt.png" (a tile; else a
           brown of its own)}: earth with two wheel ruts and 3D gravel, the plants kept off it and lower beside it,
  "terrain": {"amp": 0.35 (m), "seed": 5}, "puddles": {"sizes": [[65, 34], [59, 33], [48, 25], [32, 19], [19, 13]]},
  "tile": "grass.png" (grass2d), "seed": 3,
  "style": "pixel" (default: steps of light, one palette, a 1-px outline, no blur) | "smooth" (for an illustrated game: rendered at 3x and
           averaged, the light and the greens continuous, no palette; the front strips with soft edges; terrain and puddles as gradients)
WIN=x,y,w,h in the environment renders a window only (a quick look), DEBUG=1 also writes what each pixel is (ground, plant, path, stone).
reference/ground.md: what each one is for, how to use the front strips in an engine, what the user chose and why."""
import glob, json, math, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parent; KIT = HERE.parent / 'ground'
REAL_H = {'grass': 0.34, 'fern': 0.32, 'flowers': 0.26, 'clover': 0.12}          # (the realistic plants' heights, metres)
REAL_KIND = {'grass': 'grass', 'clover': 'grass', 'fern': 'fern', 'flowers': 'flower'}


def load_spec(p):
    p = Path(p); s = json.loads(p.read_text(encoding='utf-8')); s['_dir'] = p.resolve().parent
    s.setdefault('name', p.stem); s.setdefault('size', [960, 540]); s.setdefault('ppm', 74.0); s.setdefault('pitch', 30); s.setdefault('sun', [0.42, 1.0, 0.78])
    out = s['_dir'] / s['name']; out.mkdir(parents=True, exist_ok=True); s['_out'] = out; return s


def rel(s, f): return str(Path(f) if Path(f).is_absolute() else s['_dir'] / f)


def palette_of(s):
    """the palette asked for, as colours (n, 3) - or None"""
    pv = s.get('palette')
    if not pv: return None
    if any(ch in pv for ch in '*?'):
        files = [f for f in glob.glob(rel(s, pv)) if 'shade' not in f and 'clumps' not in f]
        if not files: sys.exit(f'ground: no pictures match "palette": {pv}')
        a = np.unique(np.concatenate([np.asarray(Image.open(f).convert('RGBA')).reshape(-1, 4) for f in files]), axis=0); return a[a[:, 3] == 255][:, :3].astype(float)
    sys.path.insert(0, str(HERE)); import pixelkit as P
    return np.asarray(P.load_palette(pv), float)


def to_pal(c, pal):
    u, inv = np.unique(np.round(c.reshape(-1, 3)).astype(int), axis=0, return_inverse=True)
    return pal[((u[:, None, :] - pal[None]) ** 2).sum(2).argmin(1)][inv.ravel()].reshape(c.shape)


def raster(P, faces, Hh, Ww):
    """front-most face per pixel centre (P: screen x, y, depth towards the viewer): face id and barycentrics. Faces under 40 px across are
    stamped all at once (points over each, as many as its area needs, the nearest kept per pixel) - a meadow is millions of faces"""
    zf = np.full((Hh, Ww), -np.inf); fid = np.full((Hh, Ww), -1); bc = np.zeros((Hh, Ww, 3))
    T3 = P[faces]; mn = np.floor(T3[:, :, :2].min(1) - 0.5).astype(int); mx = np.ceil(T3[:, :, :2].max(1) - 0.5).astype(int)
    ok = (mx[:, 0] >= 0) & (mx[:, 1] >= 0) & (mn[:, 0] < Ww) & (mn[:, 1] < Hh)
    span = (T3[:, :, :2].max(1) - T3[:, :, :2].min(1)).max(1); small = ok & (span < 40); ks = np.nonzero(small)[0]
    if len(ks):
        e1 = T3[ks, 1, :2] - T3[ks, 0, :2]; e2 = T3[ks, 2, :2] - T3[ks, 0, :2]; area = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2
        nS = np.clip(np.ceil(area * 2.5), 4, 400).astype(int); kk = np.repeat(ks, nS); r1 = np.random.default_rng(1).random((len(kk), 2)); fl = r1.sum(1) > 1; r1[fl] = 1 - r1[fl]
        first = np.r_[0, np.cumsum(nS)[:-1]]
        for c_, w_ in enumerate([(1 / 3, 1 / 3), (0.9, 0.05), (0.05, 0.9), (0.05, 0.05)]): r1[first + c_] = w_          # (its middle and corners always)
        ww = np.c_[1 - r1.sum(1), r1[:, 0], r1[:, 1]]
        for a0 in range(0, len(kk), 4_000_000):
            k_, w__ = kk[a0:a0 + 4_000_000], ww[a0:a0 + 4_000_000]; pts = np.einsum('nc,ncd->nd', w__, T3[k_])
            xi = np.floor(pts[:, 0]).astype(int); yi = np.floor(pts[:, 1]).astype(int); m = (xi >= 0) & (yi >= 0) & (xi < Ww) & (yi < Hh)
            xi, yi, z, k_, w__ = xi[m], yi[m], pts[m, 2], k_[m], w__[m]; pix = yi * Ww + xi; o = np.lexsort((-z, pix)); f1 = np.r_[True, pix[o][1:] != pix[o][:-1]]; o = o[f1]
            fz = zf.ravel(); w_ = z[o] > fz[pix[o]]; o = o[w_]; fz[pix[o]] = z[o]; fid.ravel()[pix[o]] = k_[o]; bc.reshape(-1, 3)[pix[o]] = w__[o]
    for k in np.nonzero(ok & ~small)[0]:
        t = T3[k]; x0, y0 = max(mn[k, 0], 0), max(mn[k, 1], 0); x1, y1 = min(mx[k, 0], Ww - 1), min(mx[k, 1], Hh - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        dd = (t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0]) + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1])
        if abs(dd) < 1e-12: continue
        l0 = ((t[1, 1] - t[2, 1]) * (xs - t[2, 0]) + (t[2, 0] - t[1, 0]) * (ys - t[2, 1])) / dd; l1 = ((t[2, 1] - t[0, 1]) * (xs - t[2, 0]) + (t[0, 0] - t[2, 0]) * (ys - t[2, 1])) / dd; l2 = 1 - l0 - l1
        ins = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not ins.any(): continue
        z = (l0 * t[0, 2] + l1 * t[1, 2] + l2 * t[2, 2])[ins]; yy = (ys - 0.5).astype(int)[ins]; xx = (xs - 0.5).astype(int)[ins]
        w = z > zf[yy, xx]; yy, xx, z = yy[w], xx[w], z[w]; zf[yy, xx] = z; fid[yy, xx] = k; bc[yy, xx] = np.stack([l0[ins][w], l1[ins][w], l2[ins][w]], -1)
    return fid, bc, zf


# --- meadow ----------------------------------------------------------------------------------------------------------------------------
def meadow(s):
    import trimesh
    W, H = s['size']; PPM = float(s['ppm']); PITCH = math.radians(s['pitch']); SMOOTH = s.get('style') == 'smooth'; SS = 3 if SMOOTH else 2; seed = int(s.get('seed', 3)); rng = np.random.default_rng(seed)
    SUN = np.array(s['sun'], float); SUN /= np.linalg.norm(SUN); out = s['_out']
    DENS, FERNS, FLOWERS = float(s.get('density', 22)), float(s.get('ferns', 0.12)), float(s.get('flowers', 0.08)); PAL = palette_of(s)
    # THE PLANTS: each kind's models, stood on the ground at their height
    pl = s.get('plants', 'realistic'); TEX = []
    if pl == 'realistic': items = [{'glb': str(KIT / 'realistic' / f'{n}.glb'), 'kind': REAL_KIND[n], 'height': REAL_H[n], 'textured': True, 'keep_light': n == 'flowers'} for n in REAL_H]
    else: items = [{**i, 'glb': rel(s, i['glb'])} for i in pl]
    def model(it):
        sc = trimesh.load(it['glb']); parts = []
        for node in sc.graph.nodes_geometry:
            M, gn = sc.graph[node]; g = sc.geometry[gn]; v = trimesh.transform_points(g.vertices, M); mat = getattr(g.visual, 'material', None)
            tex = getattr(mat, 'baseColorTexture', None) if mat is not None else None
            if tex is not None and getattr(g.visual, 'uv', None) is not None:          # textured (a Tripo plant): blurred - a face takes its part's colour, not the grain (pixel art wants clusters)
                t_ = ndimage.gaussian_filter(np.asarray(tex.convert('RGB').resize((512, 512) if SMOOTH else (256, 256), Image.BOX)).astype(float), (1, 1, 0) if SMOOTH else (3, 3, 0)); lum = t_.mean(-1)          # (smooth: its texture nearly as it is)
                if not it.get('keep_light'): t_ = t_ * (78.0 / max(1.0, lum[lum > 20].mean()))          # (every plant as light as the grass: a fern's lime brought down to it)
                TEX.append(t_); parts.append((v, g.faces, ('tex', len(TEX) - 1, g.visual.uv)))
            else:
                c = np.array((getattr(mat, 'baseColorFactor', None) if mat is not None else None) if mat is not None and getattr(mat, 'baseColorFactor', None) is not None else [120, 180, 90, 255], float)[:3]
                if c.max() <= 1.0: c = c * 255
                parts.append((v, g.faces, None if (c[1] > c[0] + 30 and c[1] > c[2] - 20) else c))          # (a green part: a leaf, coloured from the greens; else its own colour: a petal)
        lo = min(p[0][:, 1].min() for p in parts); hi = max(p[0][:, 1].max() for p in parts); k = it['height'] / (hi - lo) if it.get('height') else 1.0
        return [((v - [0, lo, 0]) * k, f, c) for v, f, c in parts]
    MODELS = {i: model(it) for i, it in enumerate(items)}; BYKIND = {k: [i for i, it in enumerate(items) if it['kind'] == k] for k in ('grass', 'fern', 'flower')}
    for k in ('fern', 'flower'):
        if not BYKIND[k]: BYKIND[k] = BYKIND['grass']
    # THE GREENS: for the leaves without a texture (dark to light) - the palette's own greens if there is one
    src = PAL if PAL is not None else np.array([[24, 40, 22], [36, 60, 30], [52, 82, 38], [72, 104, 48], [96, 128, 60], [128, 156, 80]], float)
    gr = src[(src[:, 1] > src[:, 0] + 6) & (src[:, 1] > src[:, 2])]; gr = gr if len(gr) >= 3 else src; gr = gr[np.argsort(gr.mean(1))]
    GREENS = gr[np.linspace(0, len(gr) - 1, 6).round().astype(int)]; GROUND = GREENS[0] * 0.85
    # THE DENSITY: Gaussian-blurred noise stretched along the ground, plus Gaussian clumps; the flowers' patches their own
    XW, ZD = W / PPM, H / (math.sin(PITCH) * PPM) + 1.0; GN = (int(ZD * 8), int(XW * 8))
    def field(sig, clumps, sh):
        r = np.random.default_rng(seed + sh); D = ndimage.gaussian_filter(r.standard_normal(GN), (sig, sig)); D = (D - D.mean()) / D.std(); zz, xx = np.mgrid[0:GN[0], 0:GN[1]] / 8.0
        for _ in range(clumps):
            cx, cz, sg, a = r.uniform(0, XW), r.uniform(0, ZD), r.uniform(0.4, 1.8), r.uniform(-0.6, 1.0); D += a * np.exp(-((xx - cx) ** 2 + (zz - cz) ** 2) / (2 * sg * sg))
        return 1 / (1 + np.exp(-1.6 * D))
    DEN, FLW = field(6, int(XW * ZD / 3), 0), field(4, int(XW * ZD / 6), 7); at = lambda F, x, z: F[np.clip((z * 8).astype(int), 0, GN[0] - 1), np.clip((x * 8).astype(int), 0, GN[1] - 1)]
    # THE PATH: how far a ground point is outside its edge, in px (< 0: on it); its edge ragged by a little noise. In ground metres, so it
    # is as wide across the 2:1 ground in every direction
    path = s.get('path'); _pn = ndimage.gaussian_filter(np.random.default_rng(seed + 21).standard_normal((H // 2 + 8, W // 2 + 8)), 1.2)
    if path:
        P_ = np.array(path['points'], float); PG = np.c_[P_[:, 0] / PPM, P_[:, 1] / (math.sin(PITCH) * PPM)]; HALF = float(path.get('half', 24))
    def pathd(x, z, rut=False):
        if not path: return np.full(np.shape(x), 99.0)
        x = np.asarray(x, float); z = np.asarray(z, float); best = np.full(x.shape, 1e9)
        for a, b in zip(PG[:-1], PG[1:]):
            ab = b - a; t = np.clip(((x - a[0]) * ab[0] + (z - a[1]) * ab[1]) / max(1e-9, ab @ ab), 0, 1); best = np.minimum(best, np.hypot(x - (a[0] + t * ab[0]), z - (a[1] + t * ab[1])))
        dpx = best * PPM
        if rut: return dpx
        sx, sy = x * PPM, z * math.sin(PITCH) * PPM; n = _pn[np.clip((sy / 2).astype(int), 0, _pn.shape[0] - 1), np.clip((sx / 2).astype(int), 0, _pn.shape[1] - 1)] * 4
        return dpx - HALF - n
    def front_of(x, z):          # (a point lower on the screen than the path just above or below it: in front of it, standing up over it)
        if not path: return np.zeros(np.shape(x), bool)
        sx = np.asarray(x) * PPM; py = np.interp(sx, P_[:, 0], P_[:, 1]) if np.all(np.diff(P_[:, 0]) > 0) else np.interp(sx, P_[::-1, 0], P_[::-1, 1]); return np.asarray(z) * math.sin(PITCH) * PPM > py
    N = int(XW * ZD * DENS * 1.6); px = rng.uniform(-0.3, XW + 0.3, N); pz = rng.uniform(-0.3, ZD, N); d = at(DEN, px, pz)
    keep = rng.random(N) < (0.3 + 0.7 * d ** 1.4) * np.clip((pathd(px, pz) - 3) / 5, 0, 1); px, pz, d = px[keep], pz[keep], d[keep]          # (none on the path; thinner at its edge)
    fl = at(FLW, px, pz); u = rng.random(len(px)); kind = np.where(u < FLOWERS * 3 * fl ** 3, 'flower', np.where(u < FLOWERS * 3 * fl ** 3 + FERNS, 'fern', 'grass'))
    if path and path.get('gravel', True):          # THE GRAVEL: little stones over the path, more at its edges and in two wheel ruts
        M2 = int(XW * ZD * 260); gx = rng.uniform(0, XW, M2); gz = rng.uniform(0, ZD, M2); pd = pathd(gx, gz); off = np.abs(pathd(gx, gz, rut=True) - HALF * 0.37)
        pk = (pd < 1) & (rng.random(M2) < 0.25 + 0.5 * np.exp(-off ** 2 / 18) + 0.45 * np.exp(-(pd + 2) ** 2 / 8)); gx, gz = gx[pk], gz[pk]
        px = np.r_[px, gx]; pz = np.r_[pz, gz]; d = np.r_[d, np.zeros(len(gx))]; kind = np.r_[kind, np.full(len(gx), 'pebble')]
    STONES = PAL[(PAL.mean(1) > 60) & (PAL.mean(1) < 170) & (PAL.max(1) - PAL.min(1) < 40)] if PAL is not None else np.array([[96, 92, 86], [120, 114, 104], [84, 76, 68], [140, 134, 124]], float)
    if not len(STONES): STONES = np.array([[96, 92, 86], [120, 114, 104]], float)
    V, F, C, I, UV, TI = [], [], [], [], [], []; nv = 0; ico = trimesh.creation.icosphere(subdivisions=1)
    for pi, (x, z, k, dd) in enumerate(zip(px, pz, kind, d)):
        if k == 'pebble':          # a stone: a lumpy, flattened ball, 2-6 cm, half sunk in the earth
            r_ = rng.uniform(0.012, 0.035) * (1.6 if rng.random() < 0.08 else 1); v = ico.vertices * (1 + rng.normal(0, 0.18, ico.vertices.shape)) * [r_ * rng.uniform(0.8, 1.4), r_ * rng.uniform(0.4, 0.7), r_ * rng.uniform(0.8, 1.4)]
            a = rng.uniform(0, 2 * math.pi); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
            V.append(v @ R.T + [x, r_ * 0.15, z]); F.append(ico.faces + nv); I.append(np.full(len(ico.faces), pi)); nv += len(v)
            C.append(np.tile(STONES[rng.integers(len(STONES))] * rng.uniform(0.85, 1.1), (len(ico.faces), 1))); UV.append(np.zeros((len(v), 2))); TI.append(np.full(len(ico.faces), -1)); continue
        mi = int(rng.choice(BYKIND[k])); a = rng.uniform(0, 2 * math.pi); pd1 = float(pathd(np.array([x]), np.array([z]))[0]); fr = bool(front_of(np.array([x]), np.array([z]))[0])
        near = float(np.clip(0.3 + pd1 / (70 if fr else 50), 0.3, 1)) if path else 1.0          # (lower by the path: trodden; and in front of it so it does not stand over it)
        sc_ = rng.uniform(0.8, 1.25) * (0.85 + 0.35 * dd) * (0.8 if k == 'flower' else 1) * near; R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        for v, f, c in MODELS[mi]:
            V.append(v @ R.T * sc_ + [x, 0, z]); F.append(f + nv); I.append(np.full(len(f), pi)); nv += len(v)
            if isinstance(c, tuple): C.append(np.full((len(f), 3), -3.0)); UV.append(c[2]); TI.append(np.full(len(f), c[1]))
            else: C.append(np.full((len(f), 3), -1.0) if c is None else np.tile(c, (len(f), 1))); UV.append(np.zeros((len(v), 2))); TI.append(np.full(len(f), -1))
    g = np.array([[-1, 0, -1], [XW + 1, 0, -1], [XW + 1, 0, ZD + 1], [-1, 0, ZD + 1]], float); V.append(g); F.append(np.array([[0, 2, 1], [0, 3, 2]]) + nv); C.append(np.full((2, 3), -2.0)); I.append(np.full(2, -1)); UV.append(np.zeros((4, 2))); TI.append(np.full(2, -1))
    V = np.concatenate(V); F = np.concatenate(F); C = np.concatenate(C); I = np.concatenate(I); UV = np.concatenate(UV); TI = np.concatenate(TI)
    print(f"ground: {int((kind != 'pebble').sum())} plants (grass {int((kind == 'grass').sum())}, ferns {int((kind == 'fern').sum())}, flowers {int((kind == 'flower').sum())}), {int((kind == 'pebble').sum())} stones, {len(F)} faces - rendering (minutes)", flush=True)
    # THE CAMERA: the game's (screen x = x, screen y = z sin - y cos, nearer = z cos + y sin), at SS times its pixels; the sun's view for the shadows
    sv_ = PPM * SS; cam = np.c_[V[:, 0] * sv_, (V[:, 2] * math.sin(PITCH) - V[:, 1] * math.cos(PITCH)) * sv_, V[:, 2] * math.cos(PITCH) + V[:, 1] * math.sin(PITCH)]
    WIN = [int(v) for v in os.environ['WIN'].split(',')] if os.environ.get('WIN') else None
    if WIN: cam[:, 0] -= WIN[0] * SS; cam[:, 1] -= WIN[1] * SS; W, H = WIN[2], WIN[3]
    HH, WW = H * SS, W * SS; fid, bc, _ = raster(cam, F, HH, WW)
    up = np.array([0, 1.0, 0]); ax = np.cross(up, SUN); ax /= np.linalg.norm(ax); ay = np.cross(SUN, ax); SR = 110.0
    sv = np.c_[V @ ax * SR, -(V @ ay) * SR, V @ SUN]; lo = sv[:, :2].min(0); sv[:, :2] -= lo - 2; shp = (int(sv[:, 1].max()) + 4, int(sv[:, 0].max()) + 4); _, _, szf = raster(sv, F, *shp)
    # LIGHT: a face's normal to the sun (both sides: blades are thin), whether the sun reaches it, and the sky's share
    seen = fid >= 0; f_ = fid[seen]; b_ = bc[seen]; P3 = (V[F[f_]] * b_[..., None]).sum(1)
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    lam = np.abs(nrm[f_] @ SUN); lam[C[f_, 0] == -2] = SUN[1]; q = np.c_[P3 @ ax * SR - lo[0] + 2, -(P3 @ ay) * SR - lo[1] + 2]; qi = np.clip(q.astype(int), 0, [shp[1] - 1, shp[0] - 1])
    lit = (P3 @ SUN) >= szf[qi[:, 1], qi[:, 0]] - 0.02; light = 0.32 + 0.68 * lam * lit
    col = np.zeros((len(f_), 3)); leaf = C[f_, 0] == -1; gnd = C[f_, 0] == -2; tex = C[f_, 0] == -3; own = C[f_, 0] >= 0
    li = np.clip((light[leaf] - 0.32) / 0.68 * 0.85 + np.clip(P3[leaf, 1] / 0.25, 0, 1) * 0.2 - 0.08, 0, 1) * (len(GREENS) - 1)
    if SMOOTH: i0 = np.floor(li).clip(0, len(GREENS) - 2).astype(int); fr_ = (li - i0)[:, None]; col[leaf] = GREENS[i0] * (1 - fr_) + GREENS[i0 + 1] * fr_          # (smooth: between the greens)
    else: col[leaf] = GREENS[np.round(li).astype(int)]
    col[gnd] = GROUND[None] * (0.7 + 0.25 * lit[gnd])[:, None]; col[own] = C[f_][own] * (0.62 + 0.38 * light[own, None])
    onpath = np.zeros(len(f_), bool)
    if path:          # THE EARTH: the tile (or a brown) by screen position, two wheel ruts darker, its edge darker under the grass, and a verge of trodden earth just outside
        gp = P3[gnd]; pd_ = pathd(gp[:, 0], gp[:, 2]); on = pd_ < 0; sxp = (gp[:, 0] * PPM).astype(int); syp = (gp[:, 2] * math.sin(PITCH) * PPM).astype(int)
        E = np.asarray(Image.open(rel(s, path['earth'])).convert('RGB')).astype(float) if path.get('earth') else (np.array([96, 76, 58.]) * (0.85 + 0.3 * np.random.default_rng(seed + 3).random((64, 64, 1))))
        dc = E[syp % E.shape[0], sxp % E.shape[1]]; rut = np.abs(pathd(gp[:, 0], gp[:, 2], rut=True) - HALF * 0.37) < 2.5
        shade = (0.78 + 0.25 * lit[gnd]) * np.where(rut, 0.8, 1.0) * np.where(pd_ > -3, 0.82, 1.0); verge = (pd_ >= 0) & (pd_ < 10)
        gc = col[gnd]; gc[on] = (dc * shade[:, None])[on]; gc[verge] = (dc * (0.62 + 0.18 * lit[gnd])[:, None] * 0.85 + GROUND[None] * 0.15)[verge]; col[gnd] = gc
        gi = np.nonzero(gnd)[0]; onpath[gi[on | verge]] = True; onpath |= own & (I[f_] >= 0) & (kind[np.clip(I[f_], 0, len(kind) - 1)] == 'pebble')
    if tex.any():          # a textured plant: its texture's colour at the face's middle, lit, in four steps of light (clusters)
        uv = UV[F[f_[tex]]].mean(1); ti = TI[f_[tex]]; tc = np.zeros((tex.sum(), 3))
        for k in np.unique(ti):
            m = ti == k; t_ = TEX[k]; th_, tw_ = t_.shape[:2]; tc[m] = t_[np.clip((1 - uv[m, 1] % 1) * th_, 0, th_ - 1).astype(int), np.clip((uv[m, 0] % 1) * tw_, 0, tw_ - 1).astype(int)]
        band = np.clip((light[tex] - 0.32) / 0.68 + np.clip(P3[tex, 1] / 0.25, 0, 1) * 0.3, 0, 1.2); band = band if SMOOTH else np.round(band * 3) / 3; col[tex] = tc * (0.75 + 0.75 * band)[:, None]
    img = np.zeros((HH, WW, 3)); img[seen] = col; PP = np.zeros((HH, WW), bool); PP[seen] = onpath
    if os.environ.get('DEBUG'):
        kk = np.zeros(len(f_), int); kk[gnd] = 1; kk[tex | leaf] = 2; kk[own] = 3; kk[gnd & onpath] = 4; dbg = np.zeros((HH, WW, 3), np.uint8)
        dbg[seen] = np.array([[0, 0, 0], [30, 40, 90], [40, 160, 40], [150, 150, 150], [150, 100, 50]])[kk]; Image.fromarray(dbg[SS // 2::SS, SS // 2::SS]).save(out / 'ground-debug.png')
    # DOWN TO THE GAME'S PIXELS (each pixel the block's middle: no blur), THE OUTLINE (a plant before another or the ground: one step darker)
    if SMOOTH:          # smooth: each pixel the block's average (no hard edges), the path where most of the block is path
        small = img[:H * SS, :W * SS].reshape(H, SS, W, SS, 3).mean((1, 3)); pp = PP[:H * SS, :W * SS].reshape(H, SS, W, SS).mean((1, 3)) > 0.5
    else: small = img[SS // 2::SS, SS // 2::SS][:H, :W].copy(); pp = PP[SS // 2::SS, SS // 2::SS][:H, :W]
    inst = np.full((HH, WW), -2); inst[seen] = I[f_]; inst = inst[SS // 2::SS, SS // 2::SS][:H, :W]
    dep = np.full((HH, WW), -9.0); dep[seen] = P3[:, 2] * math.cos(PITCH) + P3[:, 1] * math.sin(PITCH); dep = dep[SS // 2::SS, SS // 2::SS][:H, :W]; edge = np.zeros((H, W), bool)
    for dy, dx in ((1, 0), (0, 1), (0, -1)): edge |= (inst >= 0) & (np.roll(inst, (-dy, -dx), (0, 1)) != inst) & (np.roll(dep, (-dy, -dx), (0, 1)) < dep - 0.03)
    small[edge] = small[edge] * (0.9 if SMOOTH else 0.62)          # (smooth: only a hint of an outline)
    # TONE (the textured plants darker / less yellow: a rainy forest - the user chose 0.58 / 0.78 on the Rain Girl meadow), white flowers kept
    TK, TS = float(s.get('tone', 0.58)), float(s.get('saturation', 0.78))
    if tex.any() and (TK != 1 or TS != 1):
        q_ = small[~pp]; l_ = q_.mean(-1, keepdims=True); q2 = (l_ + (q_ - l_) * TS) * TK; wht = (q_.mean(-1) > 170) & (q_.max(-1) - q_.min(-1) < 50); q2[wht] = q_[wht]; small[~pp] = q2
    # THE PALETTE: the meadow its greens (and light colours: flowers); the path every colour, and the earth's own in shade (else shaded earth went green)
    if PAL is not None:
        meadow_pal = PAL[(PAL[:, 1] >= PAL[:, 0] - 4) | (PAL.mean(1) > 150)]; meadow_pal = meadow_pal if len(meadow_pal) >= 4 else PAL
        path_pal = np.vstack([PAL] + ([np.unique(np.asarray(Image.open(rel(s, path['earth'])).convert('RGB')).reshape(-1, 3), axis=0).astype(float) * k for k in (1, 0.8, 0.64)] if path and path.get('earth') else []))
        for sel, pal_ in ((~pp, meadow_pal), (pp, path_pal)):
            if not sel.any(): continue
            m_ = to_pal(small[sel], pal_)
            if SMOOTH:          # smooth: the palette's colour without its steps - each channel's mean and spread moved to the palette-mapped one's
                q_ = small[sel]; small[sel] = (q_ - q_.mean(0)) / (q_.std(0) + 1e-6) * m_.std(0) + m_.mean(0)
            else: small[sel] = m_
        res = Image.fromarray(np.clip(small, 0, 255).astype(np.uint8))
    elif SMOOTH: res = Image.fromarray(np.clip(small, 0, 255).astype(np.uint8))          # (smooth: its own colours, every one)
    else: res = Image.fromarray(np.clip(small, 0, 255).astype(np.uint8)).quantize(colors=24, method=Image.Quantize.MEDIANCUT, kmeans=2).convert('RGB')
    res.save(out / ('ground-window.png' if WIN else 'ground.png'), optimize=True)
    if WIN: return print(f'ground: {out / "ground-window.png"} (a window: no front strips)')
    # THE PLANTS IN FRONT: every plant's pixels cut into strips by where it is rooted (3 px of ground a strip); its depth is its root's y,
    # as a tree's is its foot's - an engine draws a strip over whoever stands behind those plants (reference/ground.md)
    fin = np.asarray(res.convert('RGB')); root = np.r_[pz * math.sin(PITCH) * PPM, -1]; R = np.where(inst >= 0, root[np.clip(inst, 0, len(px) - 1)], -1); yy = np.mgrid[0:H, 0:W][0]
    plant = (inst >= 0) & (yy <= R + 1) & ~pp; STEP = 3; strips = []; rows = []; aY = 0
    if SMOOTH:          # (smooth: a strip's alpha is how much of each pixel's block its plants cover - soft edges)
        instF = np.full((HH, WW), -1); instF[seen] = I[f_]; RF = np.where(instF >= 0, root[np.clip(instF, 0, len(px) - 1)], -1)[:H * SS, :W * SS]; yyF = (np.mgrid[0:H * SS, 0:W * SS][0] + 0.5) / SS
        plantF = (instF[:H * SS, :W * SS] >= 0) & (yyF <= RF + 1) & ~PP[:H * SS, :W * SS]
    for k in range(0, H + 40, STEP):
        if SMOOTH:
            r0, r1 = max(0, k - 80), min(H, k + STEP + 2); mf = plantF[r0 * SS:r1 * SS] & (RF[r0 * SS:r1 * SS] >= k) & (RF[r0 * SS:r1 * SS] < k + STEP)
            cov = np.zeros((H, W)); cov[r0:r1] = np.clip(mf.reshape(r1 - r0, SS, W, SS).mean((1, 3)) / 0.6, 0, 1); m = cov > 0.03          # (a pixel's colour is already the blade's mixed with what is behind: 60 % covered counts as whole, else thin blades over a foot looked washed out)
        else: m = plant & (R >= k) & (R < k + STEP); cov = m.astype(float)
        if not m.any(): continue
        ys_, xs_ = np.nonzero(m); x0, y0, x1, y1 = xs_.min(), ys_.min(), xs_.max() + 1, ys_.max() + 1
        t = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); t[..., :3] = fin[y0:y1, x0:x1]; t[..., 3] = (cov[y0:y1, x0:x1] * 255).round().astype(np.uint8)
        strips.append(t); rows.append([int(k + STEP), int(x0), int(y0), int(x1 - x0), int(y1 - y0), int(aY)]); aY += int(y1 - y0)
    atlas = np.zeros((max(1, aY), max([t.shape[1] for t in strips] or [1]), 4), np.uint8); a_ = 0
    for t in strips: atlas[a_:a_ + t.shape[0], :t.shape[1]] = t; a_ += t.shape[0]
    atlas[atlas[..., 3] == 0] = 0          # (the colour under alpha 0 cleared: smooth's atlas went from 17 MB to 4)
    (Image.fromarray(atlas) if SMOOTH else Image.fromarray(atlas).quantize(colors=64, method=Image.Quantize.FASTOCTREE)).save(out / 'ground-front.png', optimize=True)
    (out / 'ground-front.json').write_text(json.dumps({'what': 'the plants cut into strips by their roots: [depth (root y), x, y, w, h, y in ground-front.png]', 'strips': rows}))
    (out / 'ground-front.js').write_text('// the plants in front (ground.py): [depth (root y), x, y, w, h, y in ground-front.png]\nconst GROUNDFRONT = ' + json.dumps(rows) + ';\n')
    z = 2; pv = res.resize((W // 2 * z, H // 2 * z), Image.NEAREST) if W > 1200 else res.resize((W * z // 2 * 1, H * z // 2 * 1), Image.NEAREST); pv.save(out / 'preview.png')
    print(f'ground: {out / "ground.png"} ({W} x {H}); {len(rows)} front strips -> ground-front.png / .json / .js - look at preview.png')


# --- terrain ---------------------------------------------------------------------------------------------------------------------------
def terrain(s):
    W, H = s['size']; PPM = float(s['ppm']); PITCH = math.radians(s['pitch']); T = s.get('terrain', {}); AMP = float(T.get('amp', 0.35)); rng = np.random.default_rng(int(T.get('seed', 5)))
    SUN = np.array(s['sun'], float); SUN /= np.linalg.norm(SUN)
    y, x = np.mgrid[0:H, 0:W].astype(float); gx = x / PPM; gz = y / (math.sin(PITCH) * PPM); h = np.zeros_like(gx)
    for _ in range(max(1, int(W * H / 26000))):          # a few low Gaussian hills and hollows (tens of cm over metres: flat to walk on)
        cx, cz = rng.uniform(-2, W / PPM + 2), rng.uniform(-2, H / math.sin(PITCH) / PPM + 2); sg = rng.uniform(1.2, 3.5); a = rng.uniform(-1, 1) * AMP
        h += a * np.exp(-((gx - cx) ** 2 + (gz - cz) ** 2) / (2 * sg * sg))
    dz, dx = np.gradient(h, gz[:, 0], gx[0]); n = np.dstack([-dx, np.ones_like(h), -dz]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    f = (n @ SUN) / SUN[1]; f = f / np.median(f) + (rng.random((H // 2 + 1, W // 2 + 1))[y.astype(int) // 2, x.astype(int) // 2] - 0.5) * 0.02
    img = np.zeros((H, W, 4), np.uint8)
    if s.get('style') == 'smooth':          # smooth: a gradient, no steps, no dither
        f = (n @ SUN) / SUN[1]; f = f / np.median(f); dk = np.clip((1 - f) / 0.07, 0, 1) * 0.2; lt = np.clip((f - 1) / 0.07, 0, 1) * 0.12
        img[..., :3] = np.where((dk > lt)[..., None], np.array([12, 20, 14]), np.array([236, 240, 190])); img[..., 3] = (np.maximum(dk, lt) * 255).round().astype(np.uint8)
    else:
        for lo_, hi_, c, al in [(-9, 0.93, (12, 20, 14), 0.20), (0.93, 0.97, (12, 20, 14), 0.10), (1.03, 1.07, (236, 240, 190), 0.06), (1.07, 9, (236, 240, 190), 0.12)]:
            m = (f >= lo_) & (f < hi_); img[m, :3] = c; img[m, 3] = round(al * 255)
    Image.fromarray(img).save(s['_out'] / 'terrain.png', optimize=True)
    print(f"ground: {s['_out'] / 'terrain.png'} - the slopes lit by the sun, a third lit and a third shaded; lay it over the ground (and its path)")


# --- puddles ---------------------------------------------------------------------------------------------------------------------------
def puddles(s):
    sizes = s.get('puddles', {}).get('sizes', [[65, 34], [59, 33], [48, 25], [32, 19], [19, 13]]); rng = np.random.default_rng(4)
    K = 5; amp = rng.uniform(0.02, 0.06, K) / np.arange(1, K + 1) ** 0.8; ph = rng.uniform(0, 2 * math.pi, K); shape = lambda t: 1 + sum(a * np.cos((k + 2) * t + p) for k, (a, p) in enumerate(zip(amp, ph)))
    SKY, SHADE, DEEP, MUD, LIP = np.array([92, 108, 118.]), np.array([34, 46, 42.]), np.array([18, 26, 32.]), np.array([56, 48, 38.]), np.array([150, 166, 174.])
    fres = 0.02 + 0.98 * (1 - math.cos(math.radians(90 - s['pitch']))) ** 5 + 0.22          # (Schlick at the camera's angle off the water's normal, and the sky's sheen)
    for j, (W, H) in enumerate(sizes):
        y, x = np.mgrid[0:H, 0:W].astype(float) + 0.5; cx, cy = W / 2, H / 2; rx, ry = W / 2 - 3, H / 2 - 2
        dx, dy = (x - cx) / rx, (y - cy) / ry; t = np.arctan2(dy, dx); r = np.hypot(dx, dy) / shape(t); water = r < 1; ring = (r >= 1) & (r < 1 + 3.2 / max(rx, 1))
        depth = np.clip(1 - r ** 2, 0, 1) * (0.06 + 0.02 * (len(sizes) - j) / len(sizes))
        blob = np.sin(x / 7.0 + 1.3 * j) * np.cos(y / 4.0 - 0.7) * 0.5 + 0.5; refl = SKY * (1 - 0.6 * blob[..., None]) + SHADE * 0.6 * blob[..., None]
        col = (DEEP * (1 - np.exp(-depth / 0.03))[..., None] + MUD * np.exp(-depth / 0.03)[..., None]) * (1 - fres) + refl * fres
        row = int(cy + 0.15 * ry); gl = np.zeros((H, W), bool); g0, g1 = int(cx + 0.02 * rx), int(cx + 0.4 * rx); gl[row, g0:g1] = rng.random(max(0, g1 - g0)) < 0.7; gl &= water; col[gl] = col[gl] * 0.4 + LIP * 0.6
        bank = 1.1 + 0.7 * np.clip(-dy, 0, 1); rim = water & (r > 1 - bank / max(ry, 1)); col[rim] = col[rim] * 0.55 + MUD * 0.45
        near = water & ~rim & (r > 1 - (bank + 0.9) / max(ry, 1)) & (dy > 0.35); col[near] = col[near] * 0.65 + LIP * 0.35
        col[water] = col[water] * (0.82 + 0.3 * np.clip((dy[water] + 1) / 2, 0, 1))[:, None]
        a = np.zeros((H, W)); a[water] = 140 + 100 * np.clip(depth[water] / depth.max(), 0, 1) ** 0.7; wet = ring & (rng.random((H, W)) < 0.85); col[wet] = MUD * 0.7; a[wet] = 88
        img = np.zeros((H, W, 4), np.uint8); img[..., :3] = np.clip(col, 0, 255); img[..., 3] = a.astype(np.uint8)
        if s.get('style') == 'smooth':          # smooth: every colour kept, the water's edge and the wet rim fading softly (no 1-px ragged ring)
            col_s = ndimage.gaussian_filter(np.clip(col, 0, 255), (0.6, 0.6, 0)); aw = np.clip((1 - r) * max(ry, 1) / 1.5, 0, 1) * (140 + 100 * np.clip(depth / depth.max(), 0, 1) ** 0.7)
            ar = np.clip(1 - (r - 1) / (3.2 / max(rx, 1)), 0, 1) * 88 * (r >= 1); col_s[r >= 1] = MUD * 0.7; img = np.dstack([col_s, np.maximum(aw, ar)]).round().clip(0, 255).astype(np.uint8)
            Image.fromarray(img).save(s['_out'] / f'puddle-{j}.png', optimize=True); continue
        q = Image.fromarray(img).convert('RGB').quantize(colors=12, method=Image.Quantize.MEDIANCUT).convert('RGB')
        Image.fromarray(np.dstack([np.asarray(q), img[..., 3]])).save(s['_out'] / f'puddle-{j}.png', optimize=True)
    print(f"ground: {s['_out']}/puddle-0..{len(sizes) - 1}.png - water alpha over 128, the wet rim under 100 (read the water from the alpha)")


# --- grass2d ---------------------------------------------------------------------------------------------------------------------------
def grass2d(s):
    if not s.get('tile'): sys.exit('ground grass2d: give "tile": a seamless grass picture')
    W, H = s['size']; rng = np.random.default_rng(int(s.get('seed', 11))); DENS = float(s.get('density2d', 95)); SIG = float(s.get('patch', 22)); FLOOR = float(s.get('floor', 0.35))
    T = np.asarray(Image.open(rel(s, s['tile'])).convert('RGB')).astype(int); L = T.mean(-1); P = T.shape[0]
    TT = np.tile(T, (3, 3, 1)); LL = np.tile(L, (3, 3)); lab, _ = ndimage.label(LL > np.percentile(L, 55)); tufts = []
    for k, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None: continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if not (P <= y0 < 2 * P and P <= x0 < 2 * P): continue
        m = lab[sl] == k + 1
        if not 9 <= m.sum() <= 90: continue
        mm = np.zeros((y1 - y0 + 2, x1 - x0 + 2), bool); mm[1:-1, 1:-1] = m; mm = ndimage.binary_dilation(mm)
        t = np.zeros(mm.shape + (4,), np.uint8); t[..., :3] = TT[y0 - 1:y1 + 1, x0 - 1:x1 + 1]; t[..., 3] = mm * 255; tufts.append((t, float(TT[y0:y1, x0:x1][m].mean())))
    if not tufts: sys.exit('ground grass2d: no tufts found in the tile')
    tufts.sort(key=lambda q: q[1])
    D = ndimage.gaussian_filter(rng.standard_normal((H, W)), (SIG / 2, SIG)); D = (D - D.mean()) / D.std(); yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(int(W * H / 9000)):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H); sg = rng.uniform(8, 40); a = rng.uniform(-0.6, 1.0); D += a * np.exp(-(((xx - cx) / (2 * sg)) ** 2 + ((yy - cy) / sg) ** 2) / 2)
    D = 1 / (1 + np.exp(-1.6 * D)); base = np.median(T[L < np.percentile(L, 35)], 0)
    Dn = D + (rng.random((H // 2 + 1, W // 2 + 1))[yy // 2, xx // 2] - 0.5) * 0.12; img = np.clip(base[None, None] * np.where(Dn < 0.38, 0.78, np.where(Dn < 0.62, 0.92, 1.06))[..., None], 0, 255)
    M = int(W * H / 1000 * DENS); px = rng.uniform(-10, W + 10, M); py = rng.uniform(-10, H + 14, M); d = D[np.clip(py, 0, H - 1).astype(int), np.clip(px, 0, W - 1).astype(int)]
    kp = rng.random(M) < FLOOR + (1 - FLOOR) * d ** 1.5; px, py, d = px[kp], py[kp], d[kp]; o = np.argsort(py)
    for X_, Y_, dd in zip(px[o], py[o], d[o]):
        t = tufts[int(np.clip(dd * len(tufts) + rng.normal(0, len(tufts) * 0.2), 0, len(tufts) - 1))][0]; t = t[:, ::-1] if rng.random() < 0.5 else t
        h, w = t.shape[:2]; X = int(X_ - w / 2); Y = int(Y_ - h + 2); xs, ys = max(0, X), max(0, Y); xe, ye = min(W, X + w), min(H, Y + h)
        if xe <= xs or ye <= ys: continue
        sub = t[ys - Y:ye - Y, xs - X:xe - X]; m = sub[..., 3] > 0; img[ys:ye, xs:xe][m] = sub[..., :3][m]
    res = Image.fromarray(img.astype(np.uint8)); (res if s.get('style') == 'smooth' else res.quantize(colors=20, method=Image.Quantize.MEDIANCUT, kmeans=2)).save(s['_out'] / 'ground.png', optimize=True)
    print(f"ground: {s['_out'] / 'ground.png'} - {len(px)} tufts by a Gaussian density, no repeat")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('meadow', 'terrain', 'puddles', 'grass2d'): sys.exit(__doc__)
    s = load_spec(sys.argv[2]); {'meadow': meadow, 'terrain': terrain, 'puddles': puddles, 'grass2d': grass2d}[sys.argv[1]](s)


if __name__ == '__main__': main()
