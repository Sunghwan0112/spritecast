"""propshade: a pixel prop's SHADOW on the ground, baked from its 3D model - deep close by it, paler where it falls from high up.

    python propshade.py PROP.json                     every side's shadow (free; proppixel.py runs this itself when it is done)
    python propshade.py PROP.json --weather overcast  a grey day: no sun - only the sky shut out round it (soft, close in)
    python propshade.py PROP.json --weather none      no shadow
    python propshade.py PROP.json --lamp -1,2.2,-0.6 --lamp-size 0.1     INDOORS: a lamp 1 m left of it, 2.2 m up, 0.6 m back

The spec can say it once: "shadow": "sun" (the default), "overcast" or false; indoors "lamp": {"at": [x, y, z], "size": r}.
A SEE-THROUGH part - a wicker weave, a crown of leaves, a net, a lace curtain - lets some light through, but a model made from a
description is solid there (its weave is only painted on). "see_through": [{"colour": "#c8955a", "open": 0.35}] in the spec: the
parts painted near that colour (within 90 of it, or "within") let that share of the light through; the rest stays solid (a cushion).

INDOORS a lamp is where the user puts it, in metres from the prop's foot, fixed to the screen like the sun: x to the right, y up,
z towards the viewer (down the screen). Its size is the lamp's own (a bare bulb ~0.03, a lampshade ~0.15, a ceiling panel ~0.4): the
bigger, the softer the shadow's edge. The shadow falls away from the lamp, longer the lower the lamp, and fades with the light's
fall-off (1/distance squared) out across the floor; the rest of the room's light (ceiling, walls) is the sky's part. The lamp is fixed
to the room and the prop is not: a shadow is for the prop where it stands - another place, another bake.

How the light on the ground is worked out: the sun's part plus the sky's part, each as much of it as the thing leaves open. A ground
point sees the sun (or a bit of the sky) in a direction unless the model is in the way - that is, unless the point lies in the model
pressed flat onto the ground along that direction. So the model's surface is pressed along 16 directions over the sun's disc (the real sun's
size: a branch's shadow comes out sharp) and 48 over the sky (close by the thing much of the sky is shut out:
the ground darkens round its foot, all round, the front too). The darkness is then taken to five steps, as pixel art - or, with "light_style": "smooth" (--style smooth), left as it is: a gradient,
for a game drawn in another style.

The sun is SpriteCast's own light (the guide's: from the upper right, or "light": "left"), so the shade drawn on the prop and the
shadow on the ground agree. Needs the prop's model (isoprop.py model); the sprites from proppixel.py. The model is laid on each
sprite by its outline (the drawing is a little off the render in scale and place).

Writes <prop>/out-pixel/shadow[-<view>].png (the shadow colour, its darkness in the alpha), in pixel.json each view's
"shadow": {"file", "at": [x, y], "foot": [x, y]} (where the shadow picture's top-left is in the sprite's pixels - draw it first,
under the sprite - and the middle of the prop's footprint on the floor, where a lamp's place is measured from),
and preview-shadow.png.

THE WIND (--sway leaves, or "sway": "leaves" in the spec; free): the prop's leaves moving in clumps cut from the model - see sway().
    python propshade.py PROP.json --sway leaves      sway-<side>.png (12 frames x still / breeze / gust), clumps-<side>.png, preview-sway.gif"""
import argparse, json, math, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

COLOUR = (40, 30, 24)                     # (the shadow colour of SpriteCast's characters)
WEATHER = {'sun': ((0.65, 0.35), 0.62), 'overcast': ((0.0, 1.0), 0.8), 'lamp': ((0.7, 0.3), 0.66)}          # (the light's sun (lamp) part and sky (room) part; darkness 1 -> this alpha)
STEPS = np.array([0, 0.1, 0.2, 0.31, 0.43, 0.56])          # (the alpha in steps)
STRENGTH = 1.0            # ("shadow_strength" / --strength: the shadow as if laid this many times - 1 as the light gives it)
PIXEL_STRENGTH = 1.5      # (the default for pixel art, which wants things said a little louder than they are: 56 % at its deepest -> 71 %, 10 % at
                          # its far edge -> 15 %. A smooth shadow ("light_style": "smooth") stays at 1)


def strength_of(v, style='pixel'):
    """a spec's or a flag's strength -> the number, or the reason it is not one; none given: pixel art's 1.5, a smooth shadow's 1"""
    try: k = float((PIXEL_STRENGTH if style == 'pixel' else 1) if v is None else v)
    except (TypeError, ValueError): sys.exit(f'shadow strength: a number from 0.3 to 3 (1 as the light gives it; pixel art 1.5 by default), not {v!r}')
    if not 0.3 <= k <= 3: sys.exit(f'shadow strength: from 0.3 to 3 (1 as the light gives it; pixel art 1.5 by default), not {k:g}')
    return k


def deeper(a, k=None):
    """a darkness 0-1 -> as dark as it is laid k times over itself (k under 1: paler)"""
    k = STRENGTH if k is None else k; return a if k == 1 else 1 - (1 - np.clip(a, 0, 1)) ** k
SUN_DISC = 0.27           # (degrees from its middle: the real sun's - a branch's shadow comes out sharp, a crown's with the gaps between its leaves)
PAD = 14                  # (room round a sprite for the fit)
SS = 4                    # (outlines drawn 4x fine, then taken down)


def load_glb(path, looks=False):
    """a .glb's triangles in its scene's space: every mesh under every node, each node's matrix or turn/scale/move applied.
    looks=True: also what each is painted - (uv per vertex, the texture of each face (an index, -1: none), the textures as arrays)"""
    b = Path(path).read_bytes(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); o = 20 + n
    bin_ = b[o + 8:o + 8 + struct.unpack('<I', b[o:o + 4])[0]] if len(b) > o else b''
    DT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}

    def acc(i):
        a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; dt = np.dtype(DT[a['componentType']]); c = NC[a['type']]
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 0) or dt.itemsize * c
        raw = np.frombuffer(bin_, np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * c, offset=start)
        return np.lib.stride_tricks.as_strided(raw, (a['count'], dt.itemsize * c), (stride, 1)).copy().view(dt).reshape(a['count'], c)

    def local(nd):
        if 'matrix' in nd: return np.array(nd['matrix'], float).reshape(4, 4).T
        x, y, z, w = nd.get('rotation', [0, 0, 0, 1]); R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                                                                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                                                                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M = np.eye(4); M[:3, :3] = R * np.array(nd.get('scale', [1, 1, 1])); M[:3, 3] = nd.get('translation', [0, 0, 0]); return M
    V, F, UV, FT, TX = [], [], [], [], {}

    def texture(p):          # (the base colour picture of a primitive's material, kept once)
        try: t = j['materials'][p['material']]['pbrMetallicRoughness']['baseColorTexture']['index']; src = j['textures'][t]['source']
        except (KeyError, IndexError, TypeError): return -1
        if src not in TX:
            import io; bv = j['bufferViews'][j['images'][src]['bufferView']]; o_ = bv.get('byteOffset', 0)
            TX[src] = (len(TX), np.asarray(Image.open(io.BytesIO(bin_[o_:o_ + bv['byteLength']])).convert('RGB')))
        return TX[src][0]

    def walk(i, M):
        nd = j['nodes'][i]; M = M @ local(nd)
        for p in j['meshes'][nd['mesh']]['primitives'] if 'mesh' in nd else []:
            if p.get('mode', 4) != 4: continue
            v = acc(p['attributes']['POSITION']).astype(float); v = v @ M[:3, :3].T + M[:3, 3]
            f = acc(p['indices']).reshape(-1, 3).astype(np.int64) if 'indices' in p else np.arange(len(v)).reshape(-1, 3)
            F.append(f + sum(len(x) for x in V)); V.append(v)
            if looks: UV.append(acc(p['attributes']['TEXCOORD_0']).astype(float) if 'TEXCOORD_0' in p['attributes'] else np.zeros((len(v), 2))); FT.append(np.full(len(f), texture(p) if 'TEXCOORD_0' in p['attributes'] else -1))
        for c in nd.get('children', []): walk(c, M)
    for r in j['scenes'][j.get('scene', 0)]['nodes'] if 'scenes' in j else range(len(j['nodes'])): walk(r, np.eye(4))
    if looks: return np.concatenate(V), np.concatenate(F), (np.concatenate(UV), np.concatenate(FT), [a for _, a in sorted(TX.values(), key=lambda x: x[0])])
    return np.concatenate(V), np.concatenate(F)


def turn(v, deg):          # (three.js rotation.y)
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    return np.stack([v[:, 0] * c + v[:, 2] * s, v[:, 1], -v[:, 0] * s + v[:, 2] * c], 1)


def placed(spec_model, v):
    """the model sized and stood as render.html stands it: turned by its own yaw, then one scale by its height (or pressed into its
    box with "shape": "box"), centred over the origin, on y = 0"""
    W, D, H = spec_model['size']; v = turn(v, spec_model.get('yaw', 0)); lo, hi = v.min(0), v.max(0); e = hi - lo
    k = np.array([H / e[1]] * 3) if spec_model.get('shape') != 'box' else np.array([D / e[0], H / e[1], W / e[2]])
    return (v - [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]) * k


def fit(v, faces, spr, pitch, ppm):
    """the model laid on the sprite (its padded alpha) by its outline: the scale and place where they overlap best -> (scale, offset, overlap)"""
    p = np.stack([v[:, 0], -(v[:, 1] * math.cos(pitch) - v[:, 2] * math.sin(pitch))], 1); H, W = spr.shape
    ys, xs = np.nonzero(spr); sb = np.array([xs.min(), ys.min(), xs.max() + 1, ys.max() + 1], float); lo, hi = p.min(0), p.max(0)
    sc = ((sb[3] - sb[1]) / ppm / (hi[1] - lo[1]) + (sb[2] - sb[0]) / ppm / (hi[0] - lo[0])) / 2
    off = np.array([(sb[0] + sb[2]) / 2, sb[3]]) - np.array([(lo[0] + hi[0]) / 2, hi[1]]) * ppm * sc
    im = Image.new('L', (W * SS, H * SS)); d = ImageDraw.Draw(im); q = (p * ppm * sc + off) * SS
    for f in faces: d.polygon([tuple(q[i]) for i in f], fill=255)
    n = 4; sil = np.pad(np.asarray(im.resize((W, H), Image.BOX)) > 127, n); best = (-1, None)
    for dx in range(-n, n + 1):
        for dy in range(-n, n + 1):
            s = sil[n - dy:n - dy + H, n - dx:n - dx + W]; u = (s & spr).sum() / max(1, (s | spr).sum())
            if u > best[0]: best = (u, off + [dx, dy])
    return sc, best[1], best[0]


def surface(v, faces, n=260000, seed=1, look=None):
    """points spread over the model's surface by area -> points, and with look (load_glb's) each point's painted colour (or None)"""
    t = v[faces]; a = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1); rng = np.random.default_rng(seed)
    i = rng.choice(len(faces), n, p=a / a.sum()); r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1); w = np.stack([1 - s, s * (1 - r2), s * r2], 1)
    pts = (t[i] * w[..., None]).sum(1)
    if look is None: return pts, None
    uv, ft, tx = look; col = np.full((n, 3), -999.0); u = (uv[faces[i]] * w[..., None]).sum(1)
    for k, im in enumerate(tx):
        m = ft[i] == k; H, W = im.shape[:2]; col[m] = im[np.clip(((u[m, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[m, 0] % 1) * W).astype(int), 0, W - 1)]
    return pts, col


def layers(spec, base, d, vk, views, im, ppm, thick=0.06):
    """what the camera sees at each pixel of a drawn sprite (RGBA array), from the model laid on it: the front surface's painted colour
    and, behind it (more than `thick` m deeper), the next surface's - or none. For a weave: what shows between its strands, the cushion
    inside a wicker chair, the far side of it, or nothing (the floor). -> (front rgb, has a surface behind, behind rgb), each H x W"""
    vd = d / f'turn-{vk}' if views else d; rj = json.loads((vd / 'render.json').read_text()); pitch = math.radians(rj['camera']['pitch'])
    v0, faces, look = load_glb(base / spec['model']['glb'], looks=True); v = turn(placed(spec['model'], v0), rj['camera']['yaw'])
    sc, off, _ = fit(v, faces, np.pad(im[..., 3] > 0, PAD), pitch, ppm); pts, col = surface(v, faces, 1500000, look=look); H, W = im.shape[:2]
    x = np.round(pts[:, 0] * ppm * sc + off[0] - PAD).astype(int); y = np.round(-(pts[:, 1] * math.cos(pitch) - pts[:, 2] * math.sin(pitch)) * ppm * sc + off[1] - PAD).astype(int)
    near = pts[:, 1] * math.sin(pitch) + pts[:, 2] * math.cos(pitch); k = (x >= 0) & (x < W) & (y >= 0) & (y < H); x, y, near, col = x[k], y[k], near[k], col[k]; key = y * W + x
    front = np.full(H * W, -np.inf); np.maximum.at(front, key, near); deep = near < front[key] - thick
    second = np.full(H * W, -np.inf); np.maximum.at(second, key[deep], near[deep])
    fc = np.zeros((H * W, 3)); f = near == front[key]; fc[key[f]] = col[f]
    bc = np.zeros((H * W, 3)); b = deep & (near == second[key]); bc[key[b]] = col[b]
    return fc.reshape(H, W, 3), np.isfinite(second).reshape(H, W), bc.reshape(H, W, 3)


def golden(n): i = np.arange(n) + 0.5; return np.sqrt(i / n), i * math.pi * (3 - math.sqrt(5))


def darkness(pts, shape, sc, off, pitch, ppm, sun, light, lamp=None, opq=None, fast=False, pool=False):
    """1 - the light on each ground point (in the sprite's padded pixels): light = sun part x the sun seen + sky part x the sky seen;
    with a lamp (at, size) the lamp in the sun's place. opq: how much light each point stops (1, or less for a see-through weave)"""
    H, W = shape; up = pts[:, 1] > 0.004; P = pts[up]; O = np.ones(len(P)) if opq is None else opq[up]

    def stamp(gx, gz, o):          # (the points pressed onto the ground, each stopping its share of the light; small gaps closed)
        u = np.round(gx * ppm * sc + off[0]).astype(int); w = np.round(gz * math.sin(pitch) * ppm * sc + off[1]).astype(int)
        k = (u >= 0) & (u < W) & (w >= 0) & (w < H); m = np.zeros(H * W); np.maximum.at(m, w[k] * W + u[k], o[k]); m = m.reshape(H, W)
        return np.maximum(m, ndi.grey_closing(m, size=3))

    def from_point(L):          # (from a point: what the model hides of it)
        k = P[:, 1] < L[1] - 0.01; Q = P[k]; t = L[1] / (L[1] - Q[:, 1])
        return stamp(L[0] + (Q[:, 0] - L[0]) * t, L[2] + (Q[:, 2] - L[2]) * t, O[k])

    def pressed(d):          # (along a direction d: those points do not see d)
        return stamp(P[:, 0] - P[:, 1] * d[0] / d[1], P[:, 2] - P[:, 1] * d[2] / d[1], O)
    out = 0
    if lamp:          # the lamp: points over its ball; its light on the floor falls off as 1/d^2 (and slants: x its height / d) - as at the prop's foot = 1
        nl = 8 if fast else 16; at, size = np.array(lamp[0], float), float(lamp[1]); r, t = golden(nl); z = 1 - 2 * (np.arange(nl) + 0.5) / nl
        balls = at + size * np.stack([np.sqrt(1 - z * z) * np.cos(t), z, np.sqrt(1 - z * z) * np.sin(t)], 1)
        hid = np.mean([from_point(L) for L in balls], 0)
        gx = (np.arange(W) - off[0]) / (ppm * sc); gz = (np.arange(H) - off[1]) / (math.sin(pitch) * ppm * sc); GX, GZ = np.meshgrid(gx, gz)
        f = lambda x, z: at[1] / ((x - at[0]) ** 2 + at[1] ** 2 + (z - at[2]) ** 2) ** 1.5
        out = out + light[0] * hid * np.clip(f(GX, GZ) / f(0, 0), 0, 1.5)
        if pool:          # (the lamp's own light on the floor: brightest right under it, (h/d)^3 - the 1/d^2 and the slant - less what the thing hides)
            lit = (at[1] / np.sqrt((GX - at[0]) ** 2 + at[1] ** 2 + (GZ - at[2]) ** 2)) ** 3 * (1 - hid)
            return ndi.gaussian_filter(np.asarray(out, float), 1.2), ndi.gaussian_filter(lit, 0.8)
    elif light[0]:
        s = np.array(sun) / np.linalg.norm(sun); a = np.cross(s, [0, 0, 1]); a /= np.linalg.norm(a); b = np.cross(s, a)
        r, t = golden(8 if fast else 16); r = r * math.tan(math.radians(SUN_DISC))
        out = out + light[0] * np.mean([pressed(s + a * ri * math.cos(ti) + b * ri * math.sin(ti)) for ri, ti in zip(r, t)], 0)
    if light[1]:
        r, t = golden(20 if fast else 48); el = np.radians(20) + (np.pi / 2 - np.radians(20)) * (1 - r ** 2)          # (from 20 degrees up: the sky by the horizon gives little light)
        dirs = np.stack([np.cos(el) * np.cos(t), np.sin(el), np.cos(el) * np.sin(t)], 1); wt = np.sin(el)          # (more of the sky's light from high up)
        out = out + light[1] * sum(w * pressed(d) for w, d in zip(wt, dirs)) / wt.sum()
    return ndi.gaussian_filter(np.asarray(out, float), 1.2)          # (a touch smoothed: the directions are many but not endless - no ragged rims)


def lamp_of(spec, lamp=None):
    lamp = lamp or spec.get('lamp'); return (list(lamp['at']), lamp.get('size', 0.1)) if isinstance(lamp, dict) else lamp


def lamp_picture_points(im):
    """a lamp picture of the user's (RGBA): where it stands - the middle of its lowest row - and where its light seems to come from -
    as high as its brightest warm pixels (a lit shade, a bulb), across the middle of its upper part -> (foot, light), in its pixels"""
    a = np.asarray(im.convert('RGBA')).astype(float); m = a[..., 3] > 127; ys, xs = np.nonzero(m); yb = ys.max(); foot = [round(float(xs[ys >= yb - 1].mean()), 1), float(yb)]
    lum = (a[..., :3] @ [0.3, 0.59, 0.11]) * m; warm = lum + (a[..., 0] - a[..., 2]) * 0.2 * m; top = warm >= np.percentile(warm[m], 96)
    ly, lx = np.nonzero(top & m); up = ys < ys.min() + 0.35 * (yb - ys.min())          # (across: the middle of its upper part - a shade is lit on one side)
    return foot, [round(float(xs[up].mean()), 1), round(float(ly.mean()), 1)]


def prepare(spec_path, n=260000):
    """what every shadow of this prop needs, worked out once: each side's sprite, the model laid on it, its surface points (and how much
    light each lets through) -> {spec, out, pj, ppm, views: [...]}"""
    spec_path = Path(spec_path); spec = json.loads(spec_path.read_text(encoding='utf-8')); d = spec_path.resolve().parent / spec['name']; out = d / 'out-pixel'
    if not (out / 'pixel.json').exists(): sys.exit('propshade: no sprites yet - run proppixel.py first')
    if not spec.get('model'): sys.exit('propshade: no shadow - it is baked from the 3D model, and this prop has none (isoprop.py model makes one, ~20 Tripo credits)')
    pj = json.loads((out / 'pixel.json').read_text()); ppm = pj['px_per_m']; see = spec.get('see_through') or []
    got = load_glb(spec_path.resolve().parent / spec['model']['glb'], looks=bool(see)); v0, faces, look = got if see else (*got, None); v0 = placed(spec['model'], v0)
    views = spec.get('views') or []; vs = []
    for vk, e in pj['views'].items():
        vd = d / f'turn-{vk}' if views else d; rj = json.loads((vd / 'render.json').read_text()); pitch = math.radians(rj['camera']['pitch'])
        side = -1 if rj.get('light') == 'left' else 1; sun = (0.42 * side, 1.0, 0.78)          # (towards the sun: render.html's light, fixed to the screen)
        v = turn(v0, rj['camera']['yaw']); sp = Image.open(out / e['file']).convert('RGBA'); spr = np.pad(np.asarray(sp)[..., 3] > 0, PAD)
        sc, off, u = fit(v, faces, spr, pitch, ppm); pts, col = surface(v, faces, n, look=look); opq = None
        if see:          # a weave, leaves, a net: the parts painted near a colour let that share of the light through
            opq = np.ones(len(pts))
            for st in see:
                c = np.array([int(st['colour'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float); opq[np.linalg.norm(col - c, axis=1) < st.get('within', 90)] = 1 - st.get('open', 0.35)
        vs.append({'key': vk, 'e': e, 'sp': sp, 'shape': spr.shape, 'pitch': pitch, 'sun': sun, 'sc': sc, 'off': off, 'fit': u, 'pts': pts, 'opq': opq,
                   'foot': [round(float(off[0]) - PAD, 1), round(float(off[1]) - PAD, 1)]})
    return {'spec': spec, 'out': out, 'pj': pj, 'ppm': ppm, 'views': vs}


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - 0.47          # (ordered dithering: steps that blend, as a pixel artist would)
POOL = (255, 222, 164)          # (lamplight: warm)
POOL_STEPS = 7


def pool_of(lit, room, style='pixel'):
    """the lamp's light on the floor (0-1) as a picture: its colour, its strength in the alpha in a few steps, dithered where the steps
    meet -> (picture, where its top-left is in the sprite's pixels) - lay it on the floor with ADD (or 'lighter'/'screen')"""
    H, W = lit.shape; b = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]
    q = np.clip(np.floor(lit * POOL_STEPS + 0.5 + b), 0, POOL_STEPS) / POOL_STEPS if style == 'pixel' else np.clip(lit, 0, 1) * (lit > 0.02)          # (smooth: as it is)
    if not (q > 0).any(): return None
    ys, xs = np.nonzero(q > 0); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; c = q[y0:y1, x0:x1]
    img = np.zeros(c.shape + (4,), np.uint8); img[..., :3] = POOL; img[..., 3] = np.round(c * 200)
    return Image.fromarray(img), [int(x0) - PAD - room, int(y0) - PAD - room]


def lamp_sprite(size_m, ppm, style='pixel'):
    """the light itself as pixel art: a hot white core its own size, a warm rim, a glow round it in three steps that thin out by
    ordered dithering - no soft edge, no anti-aliasing -> (picture, its middle in it)"""
    rc = max(1.5, size_m * ppm); R = int(np.ceil(rc * 2.2 + 5)); n = 2 * R + 1; ys, xs = np.mgrid[0:n, 0:n] - R; d = np.hypot(xs, ys)
    if style != 'pixel':          # (smooth: a soft glow fading out, the core solid)
        img = np.zeros((n, n, 4), np.uint8); g = np.clip(1 - (d - rc) / (R - rc), 0, 1) ** 1.6; img[..., :3] = (255, 230, 170); img[..., 3] = np.round(g * 220)
        img[d <= rc] = (255, 251, 236, 255); return Image.fromarray(img), (R, R)
    b = np.tile(BAYER + 0.47, (n // 4 + 1, n // 4 + 1))[:n, :n]; img = np.zeros((n, n, 4), np.uint8)
    glow = np.clip(1 - (d - rc) / (R - rc), 0, 1)          # (1 at the rim, 0 at the picture's edge)
    for lvl, col, a in ((0.25, (255, 214, 140), 90), (0.55, (255, 226, 160), 150), (0.8, (255, 238, 190), 210)):
        m = (glow > lvl - 0.25 + b * 0.25) & (d > rc); img[m] = (*col, a)          # (each step dithered into the one outside it)
    img[(d <= rc) & (d > rc - 1.2)] = (255, 236, 168, 255)          # (the rim)
    img[d <= rc - 1.2 if rc > 2 else d <= rc] = (255, 252, 236, 255)          # (the core)
    return Image.fromarray(img), (R, R)


def lamp_place(view, lamp, ppm):
    """where the light and its spot on the floor are in a side's sprite pixels (from its footprint's middle; x right, y up, z towards the viewer)"""
    (x, y, z), k, p = lamp[0], ppm * view['sc'], view['pitch']; fx, fy = view['foot']
    return [round(fx + x * k, 1), round(fy + z * math.sin(p) * k - y * math.cos(p) * k, 1)], [round(fx + x * k, 1), round(fy + z * math.sin(p) * k, 1)]


def shadow_of(prep, view, weather, lamp=None, fast=False, with_pool=False, style='pixel'):
    """one side's shadow -> (its picture, RGBA, and where its top-left is in the sprite's pixels), or None"""
    light, dark = WEATHER[weather]; ppm = prep['ppm']; tall = prep['spec']['model']['size'][2]
    room = int(ppm * tall * 1.2) + 20          # (room for the shadow: as far aside as the thing is tall, and more)
    if lamp: room = max(room, int(ppm * (abs(lamp[0][0]) + abs(lamp[0][2]) + tall * 2.5)) + 20)          # (a low lamp throws a long shadow)
    if lamp and with_pool: room = max(room, int(ppm * (max(abs(lamp[0][0]), abs(lamp[0][2])) + 2.2 * lamp[0][1])) + 20)          # (and its light reaches out ~2 heights)
    sh = view['shape']; pts, opq = view['pts'], view['opq']
    if fast: pts, opq = pts[::3], (None if opq is None else opq[::3])
    want = with_pool and weather == 'lamp' and lamp
    got = darkness(pts, (sh[0] + 2 * room, sh[1] + 2 * room), view['sc'], view['off'] + room, view['pitch'], ppm, view['sun'], light, lamp if weather == 'lamp' else None, opq, fast, pool=bool(want))
    D, lit = got if want else (got, None); pl = pool_of(lit, room, style) if want else None
    al = STEPS[np.abs(D[..., None] * dark - STEPS).argmin(-1)] if style == 'pixel' else np.clip(D * dark, 0, STEPS[-1]) * (D * dark > 0.02)          # (pixel: in steps; smooth: as it is)
    al = deeper(al)
    if not (al > 0).any(): return (None, pl) if with_pool else None
    ys, xs = np.nonzero(al > 0); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; c = al[y0:y1, x0:x1]
    img = np.zeros(c.shape + (4,), np.uint8); img[..., :3] = COLOUR; img[..., 3] = np.round(c * 255)
    sh_ = (Image.fromarray(img), [int(x0) - PAD - room, int(y0) - PAD - room]); return (sh_, pl) if with_pool else sh_


def bake(spec_path, weather=None, quiet=False, lamp=None, prep=None, style=None, strength=None):
    global STRENGTH
    spec_path = Path(spec_path); spec = json.loads(spec_path.read_text(encoding='utf-8')); out = spec_path.resolve().parent / spec['name'] / 'out-pixel'
    STRENGTH = strength_of(spec.get('shadow_strength') if strength is None else strength, style or spec.get('light_style', 'pixel'))
    lamp = lamp_of(spec, lamp)
    weather = weather or ('lamp' if lamp else spec.get('shadow') if spec.get('shadow') is not None else 'sun'); weather = 'none' if weather is False else weather
    if weather == 'lamp' and not lamp: sys.exit('propshade: a lamp wants where it is: --lamp x,y,z (metres from the prop\'s foot) or "lamp": {"at": [x, y, z], "size": r}')
    if lamp and lamp[0][1] <= 0: sys.exit('propshade: the lamp has to be above the floor (its y, the middle number, over 0)')
    if not (out / 'pixel.json').exists(): sys.exit('propshade: no sprites yet - run proppixel.py first')
    pj = json.loads((out / 'pixel.json').read_text())
    if weather == 'none':
        for e in pj['views'].values(): e.pop('shadow', None)
        pj.pop('shadow', None); (out / 'pixel.json').write_text(json.dumps(pj, indent=1)); return
    if weather not in WEATHER: sys.exit(f'propshade: weather is one of {", ".join(WEATHER)}, none')
    if not spec.get('model'): print('propshade: no shadow - it is baked from the 3D model, and this prop has none (isoprop.py model makes one, ~20 Tripo credits)'); return
    prep = prep or prepare(spec_path); pj = prep['pj']; cells = []; style = style or spec.get('light_style', 'pixel')
    for view in prep['views']:
        e = pj['views'][view['key']]; got, pl = shadow_of(prep, view, weather, lamp, with_pool=True, style=style); e.pop('light', None)
        if pl is not None:          # (a lamp: its light on the floor, the thing's shadow cut out of it)
            ln = e['file'].replace('sprite', 'light'); pl[0].save(out / ln); e['light'] = {'file': ln, 'at': pl[1], 'blend': 'add'}
        else: (out / e['file'].replace('sprite', 'light')).unlink(missing_ok=True)          # (no lamp: no light picture left from one before)
        if got is None: e.pop('shadow', None); continue
        img, at = got; name = e['file'].replace('sprite', 'shadow'); img.save(out / name)
        e['shadow'] = {'file': name, 'at': at, 'foot': view['foot'], 'fit': round(float(view['fit']), 2), 'height_m': round(float(view['pts'][:, 1].max()), 2)}
        # (for shading a character that walks into it: a point h metres up is in the shade the ground has at its place moved by h x
        # per_m_up - the way back along the sun's ray. Sun only: a grey day's shade is the same at any height, a lamp's is not a shift)
        if weather == 'sun': e['shadow']['per_m_up'] = [round(-view['sun'][0] * prep['ppm'], 2), round(-view['sun'][2] * math.sin(view['pitch']) * prep['ppm'], 2)]
        elif weather == 'overcast': e['shadow']['per_m_up'] = [0, 0]
        if weather == 'lamp': e['lamp'] = dict(zip(('at', 'spot'), lamp_place(view, lamp, prep['ppm'])))          # (the light's middle and its spot on the floor, in the sprite's pixels)
        else: e.pop('lamp', None)          # (foot: the middle of its footprint on the floor, in the sprite's pixels - where a lamp's x, z are measured from)
        cells.append((view['sp'], img, at))
        if not quiet: print(f"  view {view['key']}: shadow {img.width} x {img.height} px (the model on the sprite: {view['fit']:.0%} overlap)")
    if weather == 'lamp':          # the light itself (a glow, or the user's own lamp picture), for a game to draw where pixel.json says (each side's "lamp": {"at", "spot"})
        own = (spec.get('lamp') or {}).get('picture') if isinstance(spec.get('lamp'), dict) else None
        if own:          # (their lamp: its foot on the spot, its light point at the light)
            src = Image.open(spec_path.resolve().parent / own['file']).convert('RGBA'); src.save(out / 'lamp.png')
            pj['lamp'] = {'at_m': list(lamp[0]), 'size_m': lamp[1], 'file': 'lamp.png', 'foot': own['foot'], 'light': own['light'], 'colour': list(POOL),
                          'draw': "floor, then light-<side>.png with ADD, shadow-<side>.png, then the sprite and lamp.png (its foot on the side's lamp.spot) - whichever stands further back first - all in the sprite's pixels"}
        else:
            li, mid = lamp_sprite(lamp[1], prep['ppm'], style); li.save(out / 'lamp.png')
            pj['lamp'] = {'at_m': list(lamp[0]), 'size_m': lamp[1], 'file': 'lamp.png', 'middle': list(mid), 'colour': list(POOL),
                      'draw': 'floor, then light-<side>.png with ADD, shadow-<side>.png, the sprite, lamp.png with its middle on the side\'s lamp.at - all in the sprite\'s pixels'}
    else: pj.pop('lamp', None); (out / 'lamp.png').unlink(missing_ok=True)
    pj['shadow'] = {'weather': weather, 'style': style, **({'lamp': {'at': list(lamp[0]), 'size': lamp[1]}} if weather == 'lamp' else {}), 'colour': list(COLOUR), 'strength': STRENGTH, 'steps': np.round(deeper(STEPS[1:]), 2).tolist(),
                    'on_a_character': "a point of her h metres up, standing at ground pixel (x, y): read this shadow's alpha at (x, y) + h x per_m_up - only if h < height_m (a rock shades her feet, not her head) - and darken that part of her by it. Feet, middle and head each read their own"}; (out / 'pixel.json').write_text(json.dumps(pj, indent=1))
    if cells:          # to look at: each side over its shadow, on a plain green ground
        boxes = [(min(0, at[0]), min(0, at[1]), max(sp.width, at[0] + sh.width), max(sp.height, at[1] + sh.height)) for sp, sh, at in cells]
        z = 2; H = max(b[3] - b[1] for b in boxes) * z + 32; pv = Image.new('RGBA', (sum((b[2] - b[0]) * z + 16 for b in boxes) + 16, H), (118, 138, 96, 255)); x = 16
        for (sp, sh, at), b in zip(cells, boxes):
            w, h = b[2] - b[0], b[3] - b[1]; t = Image.new('RGBA', (w, h)); t.alpha_composite(sh, (at[0] - b[0], at[1] - b[1])); t.alpha_composite(sp, (-b[0], -b[1]))
            pv.alpha_composite(t.resize((w * z, h * z), Image.NEAREST), (x, H - 16 - h * z)); x += w * z + 16
        pv.convert('RGB').save(out / 'preview-shadow.png')
        if not quiet: print(f'{out}: shadows ({weather}' + f', strength {STRENGTH:g}' + ') - look at preview-shadow.png')


WALK = 0.4                # (m: what a prop has below this is what it stands on - a trunk's foot, a table's legs; boughs hanging low are not)


def ground_cut(view, ppm, lo, hi):
    """the model between two heights (m) pressed straight down onto the ground, in the side's sprite pixels: its surface points in that
    band, closed and filled -> (mask over the padded sprite, or None)"""
    pts = view['pts']; m = (pts[:, 1] >= lo) & (pts[:, 1] <= hi)
    if m.sum() < 40: return None
    H, W = view['shape']; k = ppm * view['sc']; X = np.round(pts[m, 0] * k + view['off'][0]).astype(int); Y = np.round(pts[m, 2] * math.sin(view['pitch']) * k + view['off'][1]).astype(int)
    R = 40; g = np.zeros((H + 2 * R, W + 2 * R), bool); ok = (X >= -R) & (X < W + R) & (Y >= -R) & (Y < H + R); g[Y[ok] + R, X[ok] + R] = True
    g = ndi.binary_fill_holes(ndi.binary_closing(g, iterations=2)); g = ndi.binary_opening(g, iterations=1)
    lab, n = ndi.label(g)
    if not n: return None
    size = ndi.sum(g, lab, range(1, n + 1)); g = np.isin(lab, [j + 1 for j in range(n) if size[j] >= max(6, 0.12 * size.max())])          # (the body: a twig's speck off to the side left out)
    return g, R


def filled_hull(g):
    """a mask's convex outline filled in: four legs become the table they hold up"""
    from scipy.spatial import ConvexHull
    from PIL import ImageDraw
    ys, xs = np.nonzero(g); c = np.concatenate([np.stack([xs + dx, ys + dy], 1) for dx in (0, 1) for dy in (0, 1)]).astype(float)
    try: h = c[ConvexHull(c).vertices]
    except Exception: return g
    im = Image.new('L', (g.shape[1], g.shape[0])); ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in h], fill=255); return (np.asarray(im) > 0) | g


def hull_of(g, R):
    """a mask's convex outline, a few points, in the sprite's pixels - for an engine's collision polygon"""
    from scipy.spatial import ConvexHull
    ys, xs = np.nonzero(g); c = np.concatenate([np.stack([xs + dx, ys + dy], 1) for dx in (0, 1) for dy in (0, 1)]).astype(float)
    try: h = c[ConvexHull(c).vertices]
    except Exception: return []
    while len(h) > 10:          # (the corner that adds least goes, until ten are left)
        a, b, d = np.roll(h, 1, 0), h, np.roll(h, -1, 0); area = np.abs((b[:, 0] - a[:, 0]) * (d[:, 1] - a[:, 1]) - (d[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])); h = np.delete(h, area.argmin(), 0)
    return [[round(float(x) - R - PAD, 1), round(float(y) - R - PAD, 1)] for x, y in h]


def collide(spec_path, cover=None, quiet=False, prep=None):
    """WHERE IT IS IN THE WAY, from its 3D model - a side each, in the sprite's pixels, on the ground:
    solid-<side>.png: what stops a WALKER - where it stands: all of it below `walk` metres (0.4: a trunk's foot and its roots, not the
        boughs that hang low) pressed onto the ground, and what lies between (a table's four legs: the table);
    cover-<h>-<side>.png, for each height asked ("collide": {"cover": [0.55]}, --cover 0.55): what stops a thing FLYING at that height
        (a band 0.1 m each way) - a trunk stops an arrow at 0.55 m, the crown above does not, a mushroom is too low.
    Each a white-on-clear mask with where its top-left is (`at`), and its outline in a few points (`hull`) for a collision polygon.
    Written into pixel.json under each side's "solid" and "cover"."""
    spec_path = Path(spec_path); spec = json.loads(spec_path.read_text(encoding='utf-8')); cfg = spec.get('collide')
    if cfg is False or not spec.get('model'): return
    cfg = cfg if isinstance(cfg, dict) else {}; walk = float(cfg.get('walk', WALK)); cover = [float(h) for h in (cover if cover is not None else cfg.get('cover', []))]
    prep = prep or prepare(spec_path); out, ppm = prep['out'], prep['ppm']; pj = json.loads((out / 'pixel.json').read_text()); shown = []
    for old in [*out.glob('solid-*.png'), *out.glob('cover-*.png'), out / 'solid.png']: old.unlink(missing_ok=True)
    def write(view, lo, hi, name, whole=False):
        got = ground_cut(view, ppm, lo, hi)
        if got is None: return None
        g, R = got; g = filled_hull(g) if whole else g; ys, xs = np.nonzero(g); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        img = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); img[g[y0:y1, x0:x1]] = 255; Image.fromarray(img).save(out / name)
        return {'file': name, 'at': [int(x0) - R - PAD, int(y0) - R - PAD], 'size': [int(x1 - x0), int(y1 - y0)], 'hull': hull_of(g, R)}, (g, R)
    for view in prep['views']:
        e = pj['views'][view['key']]; tag = e['file'].replace('sprite', '{}'); e.pop('solid', None); e.pop('cover', None); cells = []
        got = write(view, 0.03, walk, tag.format('solid'), whole=True)
        if got: e['solid'] = {**got[0], 'below_m': walk}; cells.append(((230, 60, 60), got[1]))
        for h in cover:
            got = write(view, max(0.03, h - 0.1), h + 0.1, tag.format(f'cover-{h:g}'))
            if got: e.setdefault('cover', []).append({**got[0], 'height_m': h}); cells.append(((60, 150, 240), got[1]))
        shown.append((view, cells))
        if not quiet: print(f"  view {view['key']}: solid {e['solid']['size'] if 'solid' in e else 'nothing'}" + ''.join(f", cover at {c['height_m']:g} m {c['size']}" for c in e.get('cover', [])))
    pj['collide'] = {'walk_m': walk, 'cover_m': cover, 'note': "solid-<side>.png: where a walker cannot stand (where the prop stands: what it has below walk_m, on the ground, and what lies between); cover-<h>-<side>.png: where a thing flying h metres up is stopped. White = blocked; `at` is the mask's top-left in the sprite's pixels, `hull` its outline for a collision polygon. A thing in the air at height h over ground pixel (x, y) is tested at (x, y) itself: the masks are on the ground"}
    (out / 'pixel.json').write_text(json.dumps(pj, indent=1))
    z = 2; tiles = []          # to look at: each side, what is solid in red and each cover in blue, over the sprite
    for view, cells in shown:
        sp = view['sp']; R = 40; t = Image.new('RGBA', (sp.width + 2 * R, sp.height + 2 * R), (118, 138, 96, 255)); t.alpha_composite(sp, (R, R)); a = np.asarray(t).copy()
        for col, (g, R2) in cells:
            gg = g[PAD:PAD + a.shape[0], PAD:PAD + a.shape[1]]; a[gg, :3] = (a[gg, :3] * 0.45 + np.array(col) * 0.55).astype(np.uint8)
        tiles.append(Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST))
    if tiles:
        pv = Image.new('RGB', (sum(t.width for t in tiles), max(t.height for t in tiles)), (118, 138, 96)); x = 0
        for t in tiles: pv.paste(t.convert('RGB'), (x, pv.height - t.height)); x += t.width
        pv.save(out / 'preview-collide.png')
        if not quiet: print(f'{out}: where it is in the way - look at preview-collide.png (red: a walker; blue: a thing in the air)')


BEAT = 12                 # (frames in a crown's beat: each clump of leaves goes a pixel aside and back once in it)
SWAY_PAD = 4              # (room each side of a sway frame: a clump goes at most 3 px aside)
SWAY_TOP = 1              # (and a row above it: a clump lifts a pixel - a crown's top, a mushroom's cap, was cut off without it)
WINDS = ('still', 'breeze', 'gust')          # (the sheet's rows: the top clumps leaning 0, 1 and 2 steps)


def sway_parts(sp, what):
    """the pixels of a sprite that move in the wind: "leaves" - its green ones - or the ones near given colours [{"colour", "within"}]"""
    a = np.asarray(sp.convert('RGBA')).astype(int); on = a[..., 3] > 127
    if what == 'leaves' or what is True: return on & (a[..., 1] > a[..., 0] * 1.06) & (a[..., 1] > a[..., 2])
    if what == 'caps':          # (a mushroom's: its red - or orange - with the pale spots inside)
        return ndi.binary_fill_holes(on & (a[..., 0] > a[..., 1] * 1.3) & (a[..., 0] > a[..., 2] * 1.5) & (a[..., 0] > 90)) & on
    m = np.zeros(on.shape, bool)
    for st in what:
        c = np.array([int(st['colour'].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]); m |= np.linalg.norm(a[..., :3] - c, axis=2) < st.get('within', 60)
    return on & m


SMALL = 700               # (moving pixels: under this the model cannot tell one part from the next - the parts are read off the sprite)


def sway_patches(px, part):
    """a SMALL thing's moving parts, read off the sprite itself: each patch of the moving colour a part (two that touch told apart by
    their middles - the patch worn down until they part), the dark line round a part going with it; far ones (higher up) first
    -> (ids, [[across, up, 0] in pixels from the sprite's bottom middle])"""
    opq = px[..., 3] > 127; core = ndi.binary_erosion(part, iterations=2); lab0, n = ndi.label(core)
    keep = [j for j in range(1, n + 1) if (lab0 == j).sum() >= 4]; core = np.isin(lab0, keep)
    if core.any(): _, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True); lab = np.where(part, lab0[iy, ix], 0)
    else: lab, _ = ndi.label(part)
    big = [j for j in np.unique(lab) if j and (lab == j).sum() >= 8]; big.sort(key=lambda j: np.nonzero(lab == j)[0].max())
    ids = np.zeros(lab.shape, np.uint8); at = []; H, W = lab.shape
    for r, j in enumerate(big):
        m = lab == j; ids[m] = r + 1; ys, xs = np.nonzero(m); at.append([float(xs.mean() - W / 2), float(H - ys.mean()), 0.0])
    dark = opq & (px[..., :3].astype(int).sum(-1) < 170) & (ids == 0); ids = np.where(dark, ndi.grey_dilation(ids, size=3), ids).astype(np.uint8)
    # (a pale spot right on a part's edge - a toadstool's white dot at the rim of its cap - is not shut in by the part's colour, so it was
    # no part's: it stood where it was while the cap moved off, a white pixel left behind in the air. A SMALL pale patch that touches a
    # part goes with it; a big one - the stem - stands)
    pale = opq & (ids == 0) & (px[..., :3].min(-1) > 150); lab, n = ndi.label(pale, np.ones((3, 3)))
    for j in range(1, n + 1):
        m = lab == j
        if m.sum() <= 6:
            near = ids[ndi.binary_dilation(m, np.ones((3, 3))) & (ids > 0)]
            if len(near): ids[m] = np.bincount(near).argmax()
    return ids, at


def sway_frame(px, ids, at, lean, f, lift=False):
    """one frame of the wind in a sprite (RGBA array): the sprite as it stands, then each clump (ids: 1.. far to near, 0 still) laid
    over it whole, a pixel aside or up by its place in the beat; the top clumps a step more in a breeze, the middle ones too in a gust.
    Where a clump has gone from, what it left shows: right inside a crown (more leaves behind leaves), wrong at its edge (a second
    outline beside the moved one) - so what is left is taken off from the outside in, as far as a clump moves (3 px): the edge goes
    with its clump, the inside stays whole.
    lift: for a small smooth thing (a mushroom's cap), whose own shape left under the moved one shows as a second edge everywhere: the
    parts are taken off first and laid where they go; what a part leaves bare is what stands under it carried up (a stem), or nothing"""
    h, w = ids.shape; T = SWAY_TOP; out = np.zeros((h + T, w + 2 * SWAY_PAD, 4), np.uint8); out[T:, SWAY_PAD:SWAY_PAD + w] = px * (px[..., 3:] > 127)
    put = np.zeros(out.shape[:2], bool)          # (where a clump was laid)
    rose = np.zeros(ids.shape, bool)          # (the pixels of the parts that went up this frame)
    if lift: out[T:, SWAY_PAD:SWAY_PAD + w][ids > 0] = 0
    tall = max(c[1] for c in at)
    for k, (cx, cy, _) in enumerate(at):
        th = 2 * math.pi * (f / BEAT - cx * 0.55 - (k % 3) * 0.11); up = cy / tall
        ln = (1 if up > 0.72 else 0) if abs(lean) == 1 else ((2 if up > 0.72 else 1 if up > 0.45 else 0) if abs(lean) == 2 else 0)
        dx = int(math.floor(0.8 * math.sin(th) + 0.5)) + (1 if lean > 0 else -1 if lean < 0 else 0) * ln; dy = -1 if math.sin(th + 1.3) > 0.9 else 0
        ys, xs = np.nonzero(ids == k + 1); y2, x2 = ys + dy + T, xs + dx + SWAY_PAD; ok = (y2 >= 0) & (y2 < h + T) & (x2 >= 0) & (x2 < w + 2 * SWAY_PAD)
        if dx or dy or lift: out[y2[ok], x2[ok]] = px[ys[ok], xs[ok]]
        if dy < 0: rose[ys, xs] = True
        put[y2[ok], x2[ok]] = True
    if lift:
        P = SWAY_PAD; bare = np.zeros(put.shape, bool); bare[T:, P:P + w] = ids > 0; bare &= out[..., 3] == 0
        # (what a part leaves bare is the GROUND BEHIND IT - nothing, see-through - not a colour of the thing: a cap that swings aside
        # shows the air it was in front of. Two things only are filled: under a part that LIFTED, the stem it sits on goes up after it,
        # a pixel; and a slit shut in by parts (two halves of one cap gone a pixel apart), with a part's colour. Filled with the stem's pale colour wherever
        # a stem was below - as it was - a cap that swung aside left a white rim behind it)
        for y, x in zip(*np.nonzero(bare)):
            if rose[y - T, x - P] and y - T + 1 < h and ids[y - T + 1, x - P] == 0 and px[y - T + 1, x - P, 3] > 127: out[y, x] = px[y - T + 1, x - P]; continue
            nb = [q for q in ((y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x)) if 0 <= q[0] < h + T and 0 <= q[1] < out.shape[1] and out[q][3] > 0]
            part = [q for q in nb if put[q]]          # (shut in on three sides or four, a part among them: a slit between two parts of one cap - closed with the part's colour, and counted a part's for the next pixel along the slit)
            if len(nb) >= 3 and part: out[y, x] = out[part[0]]; put[y, x] = True
        return out
    left = np.zeros(put.shape, bool); left[T:, SWAY_PAD:SWAY_PAD + w] = ids > 0; left &= ~put
    for _ in range(3):
        if not left.any(): break
        c = np.pad(out[..., 3] == 0, 1, constant_values=True); off = left & (c[1:-1, :-2] | c[1:-1, 2:] | c[:-2, 1:-1] | c[2:, 1:-1])
        if not off.any(): break
        out[off] = 0; left &= ~off
    return out


def sway(spec_path, what=None, quiet=False, prep=None):
    """THE WIND IN A PROP, from its 3D model. A crown is boughs, not one sheet: each moving pixel of the sprite takes the model's point it
    shows (the nearest on its line of sight), the points are grouped by where they are in 3D (k-means: a clump is a bough's worth of
    leaves, the near ones apart from those behind them), and each clump moves whole - its shape kept, a pixel at a time - the far ones
    laid first. What stands (a trunk, branches) stands. Writes, a side: clumps-<side>.png (a pixel's clump, 1.. far to near; 0: still),
    sway-<side>.png (a sheet: BEAT frames across, a row each for still air, a breeze, a gust - play a row as a loop, ~4 frames a second,
    and go down a row as the wind rises; each frame SWAY_PAD wider each side than the sprite) and their place in pixel.json; and
    preview-sway.gif."""
    spec_path = Path(spec_path); spec = json.loads(spec_path.read_text(encoding='utf-8')); what = what or spec.get('sway'); by = None
    if not what: return
    if isinstance(what, dict): by = what.get('by'); what = what.get('parts', 'leaves')          # ({"parts": "caps" | "leaves" | [{colour, within}], "by": "patches" | "model"})
    prep = prep or prepare(spec_path); out, pj, ppm = prep['out'], json.loads((prep['out'] / 'pixel.json').read_text()), prep['ppm']; shown = []
    for view in prep['views']:
        e = pj['views'][view['key']]; sp = view['sp']; px = np.asarray(sp.convert('RGBA')); part = sway_parts(sp, what)
        if part.sum() < 30: e.pop('sway', None); continue
        tag = e['file'].replace('sprite', '{}'); fw = px.shape[1] + 2 * SWAY_PAD
        if by == 'patches' or (by != 'model' and part.sum() < SMALL):          # (a small thing: its parts off the sprite, lifted as they move)
            ids, at_px = sway_patches(px, part)
            if not at_px: e.pop('sway', None); continue
            at = [[round(a_ / ppm, 2), round(b_ / ppm, 2), 0] for a_, b_, _ in at_px]; Image.fromarray(ids).save(out / tag.format('clumps'))
            fh_ = px.shape[0] + SWAY_TOP; sheet = Image.new('RGBA', (fw * BEAT, fh_ * len(WINDS)))
            for r in range(len(WINDS)):
                for f in range(BEAT): sheet.paste(Image.fromarray(sway_frame(px, ids, at, r, f, lift=True)), (f * fw, r * fh_))
            sheet.save(out / tag.format('sway'))
            e['sway'] = {'clumps': tag.format('clumps'), 'at_m': at, 'sheet': tag.format('sway'), 'frame': [fw, px.shape[0] + SWAY_TOP], 'frames': BEAT, 'rows': list(WINDS), 'pad': SWAY_PAD, 'top': SWAY_TOP, 'fps': 2, 'lift': True}
            shown.append((px, ids, at, True))
            if not quiet: print(f"  view {view['key']}: {len(at)} parts of {int(part.sum())} moving px, read off the sprite (too small for the model to part them)")
            continue
        H, W = part.shape; pts, sc, off, pitch = view['pts'], view['sc'], view['off'], view['pitch']
        X = np.round(pts[:, 0] * ppm * sc + off[0] - PAD).astype(int); Y = np.round(-(pts[:, 1] * math.cos(pitch) - pts[:, 2] * math.sin(pitch)) * ppm * sc + off[1] - PAD).astype(int)
        near = pts[:, 1] * math.sin(pitch) + pts[:, 2] * math.cos(pitch); ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H); idx = Y[ok] * W + X[ok]
        best = np.full(W * H, -np.inf); np.maximum.at(best, idx, near[ok]); front = np.zeros((W * H, 3)); hit = near[ok] == best[idx]; front[idx[hit]] = pts[ok][hit]
        seen = np.isfinite(best).reshape(H, W); L = part & seen
        if L.sum() < 30: e.pop('sway', None); continue
        P3 = front.reshape(H, W, 3)[L]; k = int(np.clip(round(part.sum() / 900), 3, 12)); rng = np.random.default_rng(5); C = P3[rng.choice(len(P3), k, replace=False)]
        for _ in range(30):
            lab = ((P3[:, None, :] - C[None]) ** 2).sum(2).argmin(1); C = np.array([P3[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
        order = np.argsort(C[:, 1] * math.sin(pitch) + C[:, 2] * math.cos(pitch)); rank = np.empty(k, int); rank[order] = np.arange(k)          # (far ones first)
        ids = np.zeros((H, W), np.uint8); ids[L] = rank[lab] + 1
        _, (iy, ix) = ndi.distance_transform_edt(ids == 0, return_indices=True); ids = np.where(part, ids[iy, ix], 0).astype(np.uint8)          # (a part the model does not reach: its neighbour's clump)
        for _ in range(2):          # (no specks: a pixel goes with most of the moving ones round it)
            votes = np.stack([ndi.uniform_filter((ids == j + 1).astype(float), 5) for j in range(k)]); ids = np.where(part, votes.argmax(0) + 1, 0).astype(np.uint8)
        # the dark line round a crown is not a leaf's colour, so no clump has it - and it would stand where it was while its leaves moved
        # off. A pixel of the sprite at its edge, no clump's, with two or more clump pixels round it, goes with the clump most of them are
        opq = px[..., 3] > 127; c = np.pad(~opq, 1, constant_values=True); edge = opq & (ids == 0) & (c[1:-1, :-2] | c[1:-1, 2:] | c[:-2, 1:-1] | c[2:, 1:-1])
        votes = np.stack([ndi.uniform_filter((ids == j + 1).astype(float), 3, mode='constant') * 9 for j in range(k)]); ids = np.where(edge & (votes.sum(0) > 1.5), votes.argmax(0) + 1, ids).astype(np.uint8)
        at = [[round(float(C[j][0]), 2), round(float(C[j][1]), 2), round(float(C[j][2]), 2)] for j in order]
        Image.fromarray(ids).save(out / tag.format('clumps'))
        fh_ = H + SWAY_TOP; sheet = Image.new('RGBA', (fw * BEAT, fh_ * len(WINDS)))
        for r in range(len(WINDS)):
            for f in range(BEAT): sheet.paste(Image.fromarray(sway_frame(px, ids, at, r, f)), (f * fw, r * fh_))
        sheet.save(out / tag.format('sway'))
        e['sway'] = {'clumps': tag.format('clumps'), 'at_m': at, 'sheet': tag.format('sway'), 'frame': [fw, H + SWAY_TOP], 'frames': BEAT, 'rows': list(WINDS), 'pad': SWAY_PAD, 'top': SWAY_TOP, 'fps': 4}
        shown.append((px, ids, at, False))
        if not quiet: print(f"  view {view['key']}: {k} clumps of {int(part.sum())} moving px")
    pj['sway'] = {'what': what, 'beat': BEAT, 'note': 'play a row of sway-<side>.png as a loop (~4 frames a second); the row by the wind (still, breeze, gust; mirror the lean for wind from the right by using lean -1, -2 with clumps-<side>.png). Each frame is `pad` px wider each side than the sprite and `top` px taller above it: draw it `pad` px to the left and `top` px up'}
    (out / 'pixel.json').write_text(json.dumps(pj, indent=1))
    if shown:          # to look at: every side in a breeze, then a gust, and back
        z = max(2, 300 // max(p_[0].shape[0] for p_ in shown)); seq = [(0, f) for f in range(BEAT)] + [(1, f) for f in range(BEAT)] + [(2, f) for f in range(BEAT)] + [(1, f) for f in range(BEAT)]
        frames = []
        for r, f in seq:
            tiles = [Image.fromarray(sway_frame(p_, i_, a_, r, f, lift=l_)) for p_, i_, a_, l_ in shown]; Wd = sum(t.width for t in tiles) + 8 * (len(tiles) + 1); Hd = max(t.height for t in tiles) + 16
            fr = Image.new('RGBA', (Wd, Hd), (118, 138, 96, 255)); x = 8
            for t in tiles: fr.alpha_composite(t, (x, Hd - 8 - t.height)); x += t.width + 8
            frames.append(fr.convert('RGB').resize((Wd * z, Hd * z), Image.NEAREST).quantize(colors=128))
        frames[0].save(out / 'preview-sway.gif', save_all=True, append_images=frames[1:], duration=250, loop=0)
        if not quiet: print(f'{out}: the wind in it - look at preview-sway.gif')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--weather', choices=[*WEATHER, 'none'], default=None, help='sun (default, or the spec\'s "shadow"), overcast, none')
    ap.add_argument('--lamp', default='', help='indoors: where the lamp is, x,y,z metres from the prop\'s foot (x right, y up, z towards the viewer)')
    ap.add_argument('--style', choices=['pixel', 'smooth'], default=None, help='pixel (the shadow and a lamp\'s light in steps, dithered - the default, or the spec\'s "light_style") or smooth (gradients, for a game not in pixel art)')
    ap.add_argument('--sway', default=None, help='the wind in it: "leaves" (its green parts move, in clumps cut from the model) - or the spec\'s "sway"; writes sway-<side>.png, clumps-<side>.png, preview-sway.gif')
    ap.add_argument('--cover', default=None, help='heights (m, comma-separated) at which to cut the model for what stops a thing in the air: cover-<h>-<side>.png (or the spec\'s "collide": {"cover": [0.55]}); solid-<side>.png, what stops a walker, is always written')
    ap.add_argument('--lamp-size', type=float, default=0.1, help='the lamp\'s radius in metres: a bare bulb ~0.03, a lampshade ~0.15, a ceiling panel ~0.4 (bigger: softer)')
    ap.add_argument('--strength', type=float, default=None, help='how deep the shadow is, as if laid this many times: pixel art 1.5 by default (71 %% at its deepest), a smooth shadow 1 (56 %%: as the light gives it) - or the spec\'s "shadow_strength"; from 0.3 to 3')
    A = ap.parse_args(); bake(A.spec, A.weather, style=A.style, lamp=([float(x) for x in A.lamp.split(',')], A.lamp_size) if A.lamp else None, strength=A.strength)
    sway(A.spec, A.sway); collide(A.spec, [float(h) for h in A.cover.split(',')] if A.cover else None)


if __name__ == '__main__': main()
