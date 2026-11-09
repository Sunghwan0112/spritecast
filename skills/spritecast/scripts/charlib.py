"""Helpers for charpipe.py: making Tripo's rigged GLB renderable (bone names, the walk's hips, feet planted as modelled), and finishing
drawn frames (cut out of their sheet, a walk fitted onto its renders, the heads' size steadied, the white left between the limbs and
round dark hair taken out) and the 3D shadows."""
import os, sys, json, struct
from collections import deque
import numpy as np
from PIL import Image
from scipy import ndimage


# --- GLB ------------------------------------------------------------------------------------------------------------------------------
def read_glb(path):
    b = open(path, 'rb').read(); L = struct.unpack_from('<I', b, 12)[0]
    return json.loads(b[20:20 + L]), bytearray(b[20 + L + 8:])


def write_glb(path, js, bin_):
    jb = json.dumps(js, separators=(',', ':')).encode(); jb += b' ' * (-len(jb) % 4); bb = bytes(bin_) + b'\0' * (-len(bin_) % 4)
    open(path, 'wb').write(b'glTF' + struct.pack('<II', 2, 12 + 8 + len(jb) + 8 + len(bb)) + struct.pack('<I', len(jb)) + b'JSON' + jb
                           + struct.pack('<I', len(bb)) + b'BIN\0' + bb)


def facing(src):
    """Degrees to turn the model about +Y so it faces +z (the renders' front), read off the skeleton at rest: each foot to its toe
    points forward. Tripo picks a model's orientation by itself - +x for one character, -x for another."""
    import math
    js, _ = read_glb(src); nodes = js['nodes']; parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
    def mat(n):
        x, y, z, w = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1]); m = np.eye(4)
        m[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                              [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * s
        m[:3, 3] = n.get('translation', [0, 0, 0]); return m
    def world(i):
        m = mat(nodes[i])
        while i in parent: i = parent[i]; m = mat(nodes[i]) @ m
        return m[:3, 3]
    name = {(n.get('name') or '').split(':')[-1]: i for i, n in enumerate(nodes)}
    v = sum(world(name[side + 'ToeBase']) - world(name[side + 'Foot']) for side in ('Left', 'Right'))
    return -math.degrees(math.atan2(v[0], v[2]))


def turn_root(src, dst, deg):
    """the scene's root nodes turned deg about +Y"""
    import math
    js, bin_ = read_glb(src); a = math.radians(deg); qx, qy, qz, qw = 0, math.sin(a / 2), 0, math.cos(a / 2)
    for i in js['scenes'][js.get('scene', 0)]['nodes']:
        n = js['nodes'][i]
        if 'matrix' in n:          # a node given as a matrix (column-major): the turn put in front of it (a rotation beside it is ignored)
            M = np.array(n['matrix'], float).reshape(4, 4).T; c, s_ = math.cos(a), math.sin(a)
            R = np.array([[c, 0, s_, 0], [0, 1, 0, 0], [-s_, 0, c, 0], [0, 0, 0, 1]]); n['matrix'] = (R @ M).T.reshape(-1).tolist(); continue
        x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        n['rotation'] = [qw * x + qx * w + qy * z - qz * y, qw * y - qx * z + qy * w + qz * x, qw * z + qx * y - qy * x + qz * w, qw * w - qx * x - qy * y - qz * z]
        if 'translation' in n: tx, ty, tz = n['translation']; n['translation'] = [tx * math.cos(a) + tz * math.sin(a), ty, -tx * math.sin(a) + tz * math.cos(a)]
    write_glb(dst, js, bin_)


def retexture(rig, tex, out):
    """A re-textured copy's texture laid onto the rig: the same triangles in another order with another UV layout - each rig triangle
    matched to the copy's by its centre, each corner given its UV; the mesh written per corner, so a vertex can take two UVs across a seam."""
    from scipy.spatial import cKDTree
    CT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}
    N = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    def acc(js, b, i):
        a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
        return np.frombuffer(b, CT[a['componentType']], a['count'] * N[a['type']], bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], -1).copy()
    rj, rb = read_glb(rig); tj, tb = read_glb(tex)
    rp = rj['meshes'][0]['primitives'][0]; tp = tj['meshes'][0]['primitives'][0]
    RI = acc(rj, rb, rp['indices']).reshape(-1, 3); TI = acc(tj, tb, tp['indices']).reshape(-1, 3)
    RP = acc(rj, rb, rp['attributes']['POSITION']); TP = acc(tj, tb, tp['attributes']['POSITION']); TUV = acc(tj, tb, tp['attributes']['TEXCOORD_0'])
    off = (RP.min(0) + RP.max(0)) / 2 - (TP.min(0) + TP.max(0)) / 2   # the rig stands on the ground, the copy is centred
    tc = TP[TI].mean(1); rc = RP[RI].mean(1) - off
    dist, j = cKDTree(tc).query(rc)
    corners = TP[TI[j]]                                    # (F, 3, 3) the matched triangles' corners
    rpos = RP[RI] - off                                    # (F, 3, 3)
    d = np.linalg.norm(rpos[:, :, None, :] - corners[:, None, :, :], axis=3); k = d.argmin(2)   # each rig corner → the copy's corner
    uv = TUV[TI[j][np.arange(len(j))[:, None], k]].reshape(-1, 2)
    flat = RI.reshape(-1); attrs = {}
    for name, i in rp['attributes'].items(): attrs[name] = acc(rj, rb, i)[flat]
    attrs['TEXCOORD_0'] = uv.astype(np.float32)
    bin_ = bytearray(rb)
    def add(arr, ref):
        while len(bin_) % 4: bin_.append(0)
        o = len(bin_); bin_.extend(arr.tobytes()); rj['bufferViews'].append({'buffer': 0, 'byteOffset': o, 'byteLength': arr.nbytes})
        a = dict(ref); a.pop('byteOffset', None); a.pop('sparse', None); a['bufferView'] = len(rj['bufferViews']) - 1; a['count'] = len(arr)
        if a['componentType'] == 5126 and a['type'] in ('VEC2', 'VEC3'): a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        else: a.pop('min', None); a.pop('max', None)
        rj['accessors'].append(a); return len(rj['accessors']) - 1
    for name, arr in attrs.items(): rp['attributes'][name] = add(arr, rj['accessors'][rp['attributes'][name]])
    idx = np.arange(len(flat), dtype=np.uint32); rp['indices'] = add(idx, {'componentType': 5125, 'type': 'SCALAR'})
    ti = tj['images'][0]; tbv = tj['bufferViews'][ti['bufferView']]; img = tb[tbv.get('byteOffset', 0): tbv.get('byteOffset', 0) + tbv['byteLength']]
    while len(bin_) % 4: bin_.append(0)
    o = len(bin_); bin_.extend(img); rj['bufferViews'].append({'buffer': 0, 'byteOffset': o, 'byteLength': len(img)})
    rj['images'][0] = {'bufferView': len(rj['bufferViews']) - 1, 'mimeType': ti.get('mimeType', 'image/png')}
    rj['buffers'][0]['byteLength'] = len(bin_)
    write_glb(out, rj, bin_)
    return float(dist.max())


def _acc(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]; o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    return np.frombuffer(bin_, dtype=np.float32, count=a['count'] * n, offset=o).reshape(-1, n), o


def fix_tripo(src, dst):
    """'mixamorig:' stripped from bone names; the in-place walk's hips moved back onto the rest position (Tripo leaves them ~1.5 m off)"""
    js, bin_ = read_glb(src); nodes = js['nodes']
    for nd in nodes:
        if nd.get('name', '').startswith('mixamorig:'): nd['name'] = nd['name'][len('mixamorig:'):]
    for an in js['animations']:
        for c in an['channels']:
            if nodes[c['target']['node']]['name'] == 'Hips' and c['target']['path'] == 'translation':
                a = js['accessors'][an['samplers'][c['sampler']]['output']]; v, o = _acc(js, bin_, an['samplers'][c['sampler']]['output']); v = v.copy()
                rest = np.array(nodes[c['target']['node']].get('translation', [0, 0, 0]))
                off = np.array([rest[0] - v[:, 0].mean(), 0, rest[2] - v[:, 2].mean()])
                if np.abs(off).max() > 0.05:
                    v += off; bin_[o:o + v.nbytes] = v.astype(np.float32).tobytes(); a['min'] = v.min(0).tolist(); a['max'] = v.max(0).tolist()
    write_glb(dst, js, bin_)
    return {an['name']: round(float(js['accessors'][an['samplers'][0]['input']]['max'][0]), 3) for an in js['animations']}


def _mul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz])


def _inv(q): return q * np.array([-1, -1, -1, 1.0])


def _R(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def plant_feet(src, dst):
    """Feet planted as modelled: retargeting twists the feet 20-40° out. In every clip each foot gets one constant correction so that,
    while it is on the ground (its lowest 40 % of keys), it has the bind pose's orientation; standing (idle), both flat every key; toes at rest."""
    js, bin_ = read_glb(src); nodes = js['nodes']
    parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}; by = {n['name']: i for i, n in enumerate(nodes)}
    rest = {i: {'t': np.array(n.get('translation', [0, 0, 0.])), 'r': np.array(n.get('rotation', [0, 0, 0, 1.]))} for i, n in enumerate(nodes)}

    def world(pose, i):
        q, p = pose[i]['r'], pose[i]['t']
        if i in parent: pq, pp = world(pose, parent[i]); return _mul(pq, q), pp + _R(pq) @ p
        return q, p
    report = {}
    for an in js['animations']:
        ch = {(c['target']['node'], c['target']['path']): c for c in an['channels']}
        keys = _acc(js, bin_, an['samplers'][an['channels'][0]['sampler']]['input'])[0][:, 0]

        def pose_at(k):
            P = {i: dict(r) for i, r in rest.items()}
            for (i, path), c in ch.items():
                if path in ('rotation', 'translation'):
                    v, _ = _acc(js, bin_, an['samplers'][c['sampler']]['output']); P[i]['rt'[path == 'translation']] = v[min(k, len(v) - 1)].astype(float)
            return P
        poses = [pose_at(k) for k in range(len(keys))]
        for side in ('Left', 'Right'):
            if side + 'Foot' not in by: continue
            f = by[side + 'Foot']
            if (f, 'rotation') not in ch: continue
            v, o = _acc(js, bin_, an['samplers'][ch[(f, 'rotation')]['sampler']]['output']); v = v.astype(float).copy()
            pb, _ = world(rest, parent[f]); target = _mul(pb, rest[f]['r'])
            h = np.array([world(P, f)[1][1] for P in poses]); stance = np.nonzero(h <= np.quantile(h, 0.4))[0]; ds = []
            for k in stance:
                pq, _ = world(poses[k], parent[f]); d = _mul(_inv(v[k]), _mul(_inv(pq), target)); ds.append(d if (not ds or d @ ds[0] >= 0) else -d)
            D = np.mean(ds, 0); D /= np.linalg.norm(D)
            v2 = (np.array([_mul(_inv(world(P, parent[f])[0]), target) for P in poses]) if an['name'] == 'idle' else np.array([_mul(q, D) for q in v]))
            v2 /= np.linalg.norm(v2, axis=1, keepdims=True)
            bin_[o:o + v2.size * 4] = v2.astype(np.float32).tobytes()
            report[f"{an['name']} {side}"] = round(float(np.degrees(2 * np.arccos(min(1, abs(D[3]))))), 1)
        an['channels'] = [c for c in an['channels'] if not ('ToeBase' in nodes[c['target']['node']]['name'] and c['target']['path'] == 'rotation')]
    write_glb(dst, js, bin_)
    return report


# --- frames ---------------------------------------------------------------------------------------------------------------------------
# --- the AI cut-out: BiRefNet (ONNX, MIT) run with onnxruntime alone - no rembg and its packages -------------------------------------
MODELS = {   # rembg's published exports of BiRefNet; lite is the default (224 MB; within 1 px of general's outline on the drawn sheets)
    'lite': ('https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx',
             '4fab47adc4ff364be1713e97b7e66334', 224005088, 'birefnet-general-lite'),
    'general': ('https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx',
                '7a35a0141cbbc80de11d9c9a28f52697', 972666916, 'birefnet-general')}
_SEG = None


def seg_model(which=None, fetch=True):
    """the model file: ~/.cache/spritecast/models/, or rembg's copy if it has one; fetched (and its md5 checked) when missing"""
    import hashlib, urllib.request
    from pathlib import Path
    which = which or os.environ.get('SPRITECAST_KEY_MODEL', 'lite'); url, md5, size, name = MODELS[which]
    for p in (Path.home() / '.cache/spritecast/models' / f'{name}.onnx', Path.home() / '.rembg/models' / name / f'{name}.onnx',
              Path(os.environ.get('U2NET_HOME', Path.home() / '.u2net')) / f'{name}.onnx'):
        if p.exists() and p.stat().st_size == size: return p
    if not fetch: return None
    p = Path.home() / '.cache/spritecast/models' / f'{name}.onnx'; p.parent.mkdir(parents=True, exist_ok=True); tmp = p.with_suffix('.part')
    print(f'cut-out model: downloading {name} ({size / 1e6:.0f} MB, once) ...', flush=True)
    h = hashlib.md5(); got = 0
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'spritecast'}), timeout=60) as r, open(tmp, 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b); h.update(b); got += len(b)
            if got % (50 << 20) < (1 << 20): print(f'  {got / 1e6:.0f} / {size / 1e6:.0f} MB', flush=True)
    if h.hexdigest() != md5: tmp.unlink(); raise SystemExit(f'cut-out model: {name} arrived damaged (md5) - run again')
    tmp.replace(p); return p


def ai_key(im):
    """the figure cut out by an AI segmenter (BiRefNet, run on the CPU): by what it is, not how white it is, so white sneakers or a
    white shirt on the sheet's white paper stay. None when onnxruntime isn't installed."""
    global _SEG
    if not _have_ort(): return None
    import onnxruntime as ort
    if _SEG is None: _SEG = ort.InferenceSession(str(seg_model()), providers=['CPUExecutionProvider'])
    x = np.asarray(im.convert('RGB').resize((1024, 1024), Image.LANCZOS)).astype(np.float64); x /= max(x.max(), 1e-6)
    x = ((x - (0.485, 0.456, 0.406)) / (0.229, 0.224, 0.225)).transpose(2, 0, 1)[None].astype(np.float32)
    p = 1 / (1 + np.exp(-_SEG.run(None, {_SEG.get_inputs()[0].name: x})[0][0, 0])); p = (p - p.min()) / max(p.max() - p.min(), 1e-6)
    return np.asarray(Image.fromarray((p * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)) > 127


NO_ORT = ('the AI cut-out needs onnxruntime, and this Python has none ({py}) - the white key it would fall back on cuts white clothes '
          'and leaves paper between the limbs. Run with the Python you installed requirements.txt into (`{py} -m pip install onnxruntime`), '
          'or set SPRITECAST_KEY=white to cut by the paper\'s white on purpose.')


def figure_key(im):
    """the AI segmenter (SPRITECAST_KEY=white: the white key, on purpose). It used to fall back on the white key by itself when
    onnxruntime was missing - a run from another Python cut a white bikini and a grey knit dress by the paper's white and nobody knew"""
    if os.environ.get('SPRITECAST_KEY') != 'white':
        if not _have_ort(): raise SystemExit(NO_ORT.format(py=sys.executable))
        m = ai_key(im)
        if m is not None: return fill_feet(m) if os.environ.get('SPRITECAST_WHITE_SHOES') == '1' else m
    return white_key(im)


def fill_feet(fg, band=0.16, max_hole=600):
    """round the feet, small holes inside the outline filled (a lace or a sole's highlight the segmenter left out) with the drawing's
    own colours; a gap between the legs is bigger and stays open"""
    ys = np.nonzero(fg.any(1))[0]
    if not len(ys): return fg
    t, b = ys[0], ys[-1]; low = np.zeros_like(fg); low[b - int(band * (b - t)):] = True
    holes = ndimage.binary_fill_holes(fg) & ~fg; lab, n = ndimage.label(holes)
    if n:
        size = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        for j in range(1, n + 1):
            m = lab == j
            if size[j - 1] < max_hole and (m & low).sum() > 0.5 * size[j - 1]: fg = fg | m
    return fg


def clear_white_unless_ai(im, ren=None):
    """the AI cut-out leaves no paper between the limbs, and clear_white would take the white between a white sneaker's laces for a
    hole: only after the white key"""
    if os.environ.get('SPRITECAST_KEY') != 'white' and _have_ort(): return im
    return clear_white(im, ren)


def _have_ort():
    try:
        import onnxruntime  # noqa: F401
        return True
    except ImportError:
        return False


def white_key(im):
    """the figure: everything but the near-white background joined to the picture's edge"""
    d = np.array(im.convert('RGB')).astype(int); near = (d.min(2) > 232) & ((d.max(2) - d.min(2)) < 18); H, W = near.shape
    bg = np.zeros((H, W), bool); q = deque()
    for yy, xx in [(0, x) for x in range(W)] + [(H - 1, x) for x in range(W)] + [(y, 0) for y in range(H)] + [(y, W - 1) for y in range(H)]:
        if near[yy, xx] and not bg[yy, xx]: bg[yy, xx] = True; q.append((yy, xx))
    while q:
        yy, xx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = yy + dy, xx + dx
            if 0 <= ny < H and 0 <= nx < W and near[ny, nx] and not bg[ny, nx]: bg[ny, nx] = True; q.append((ny, nx))
    return ~bg


MARGIN = 64   # each sheet cell is cut this much wider each side: a stride's foot drawn over the cell's edge is kept, not cut flat
SPLIT = 0.47  # where the upper body ends and the legs begin, as a share of the figure's height from the top


def cut_cell(sheet, n, cw, ch, margin=MARGIN):
    """cell n of a drawn sheet (RGB on white), cut `margin` px wider each side, the figure keyed out → its RGBA sprite cropped to the
    figure. Only pieces that belong to this cell are kept: the biggest, and the others that reach into the cell but not to the
    widened cut's edge (those are a neighbouring cell's hand or foot)"""
    x0 = max(0, n * cw - margin); x1 = min(sheet.width, (n + 1) * cw + margin); cell = sheet.crop((x0, 0, x1, ch))
    W = max(1024, cell.width); big = Image.new('RGB', (W, max(1024, ch)), (255, 255, 255)); ox = (W - cw) // 2 - (n * cw - x0)
    big.paste(cell, (ox, 0)); fg = figure_key(big)
    c0, c1 = ox + (n * cw - x0), ox + (n * cw - x0) + cw          # the cell itself in `big`
    lab, k = ndimage.label(fg)
    if k > 1:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, k + 1)); main = int(np.argmax(sizes)) + 1
        for j in range(1, k + 1):
            if j == main: continue
            xs = np.nonzero((lab == j).any(0))[0]
            if xs.max() < c0 or xs.min() >= c1 or xs.min() <= ox + 1 or xs.max() >= ox + cell.width - 2: fg[lab == j] = False
    ys, xs = np.nonzero(fg)
    return Image.fromarray(np.dstack([np.array(big), (fg * 255).astype(np.uint8)])).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def _box(rn):
    ys, xs = np.nonzero(rn[..., 3] > 0); return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)


def place(fig, ren, top):
    """fig (RGBA) laid on the render's canvas with its top at `top`, only the sideways place searched for the best silhouette overlap
    → (RGBA the render's size, overlap)"""
    rn = np.array(ren); S = rn.shape[0]; b0 = _box(rn); ra = rn[..., 3] > 128; sa = np.array(fig)[..., 3] > 127
    hh = min(fig.height, S - top); best = (-1, round((b0[0] + b0[2]) / 2 - fig.width / 2))
    s_in, r_all = int(sa[:hh].sum()), int(ra.sum())          # overlap = both / (figure + render - both): only the figure's window counted
    for dx in range(-60, 61, 2):
        x0 = round((b0[0] + b0[2]) / 2 - fig.width / 2 + dx)
        if x0 < 0 or x0 + fig.width > S: continue
        both = int((ra[top:top + hh, x0:x0 + fig.width] & sa[:hh]).sum())
        iou = both / max(1, s_in + r_all - both)
        if iou > best[0]: best = (iou, x0)
    o = Image.new('RGBA', (S, S), (0, 0, 0, 0)); o.alpha_composite(fig, (best[1], top))
    return o, round(float(best[0]), 3)


def fit_to_render(sp, ren):
    """one drawn figure (a cut_cell sprite) scaled to its render's height and laid with its top and feet on the render's (a standing
    view) → (RGBA the render's size, overlap)"""
    b0 = _box(np.array(ren)); k = (b0[3] - b0[1]) / sp.height
    sp = sp.resize((max(1, round(sp.width * k)), max(1, round(sp.height * k))), Image.LANCZOS)
    return place(sp, ren, b0[1])


def fit_walk(sprites, rens, split=SPLIT, own=(), mult=None):
    """a whole walk in one facing: the upper body at ONE scale for every frame (the median of render height / drawn height) and the
    legs alone stretched to reach the render's feet, each frame then placed sideways. Fitting every frame whole to its render's height
    made the body grow and shrink wherever the model drew a stride's legs longer; a free scale per frame made the head bob. `mult`: a
    factor per frame on that one scale (a sheet the model drew bigger than the other - see sheet_scales).
    → ([RGBA the render's size], [overlap])"""
    boxes = [_box(np.array(r)) for r in rens]
    ku = float(np.median([(b[3] - b[1]) / sp.height for sp, b in zip(sprites, boxes)])); out, ious = [], []
    if split is None:
        # an animal: no upper body over legs - the whole figure at ONE scale for the facing, standing on the render's feet. Its height is
        # mostly the tail, which the model draws a little higher or curled its own way, so the scale isn't taken from the height: the
        # one (0.8-1.2 of it) whose frames overlap their renders best on average
        # - and per sheet of four: each sheet is its own drawing, and the model drew one a little bigger than the other
        def at(k, idx):
            res = [place(sprites[i].resize((max(1, round(sprites[i].width * k)), max(1, round(sprites[i].height * k))), Image.LANCZOS), rens[i],
                         max(0, boxes[i][3] - round(sprites[i].height * k))) for i in idx]
            return float(np.mean([r[1] for r in res])), res
        out, ious = [None] * len(sprites), [None] * len(sprites)
        groups = [[i for i in range(g, min(g + 4, len(sprites))) if i not in own] for g in range(0, len(sprites), 4)] + [[i] for i in own]
        for idx in filter(None, groups):          # a frame drawn on its own (`own`) gets its own scale
            best = max((at(ku * f, idx) for f in np.arange(0.8, 1.201, 0.04)), key=lambda x: x[0])
            for i, r in zip(idx, best[1]): out[i], ious[i] = r
        return out, ious
    for i, (sp, ren, b0) in enumerate(zip(sprites, rens, boxes)):
        k = ku * (mult[i] if mult else 1); hu = round(sp.height * split); W2 = max(1, round(sp.width * k))
        up = sp.crop((0, 0, sp.width, hu)).resize((W2, max(1, round(hu * k))), Image.LANCZOS)
        hip = b0[1] + round((b0[3] - b0[1]) * split)
        lo = sp.crop((0, hu, sp.width, sp.height)).resize((W2, max(1, b0[3] - hip)), Image.LANCZOS)
        fig = Image.new('RGBA', (W2, up.height + lo.height), (0, 0, 0, 0)); fig.alpha_composite(up, (0, 0)); fig.alpha_composite(lo, (0, up.height))
        o, iou = place(fig, ren, max(0, hip - up.height)); out.append(o); ious.append(iou)
    return out, ious


def shadow_3d(spng, close=5):
    """the 3D figure's own shadow (render_char.html's flat pass) as a clean mask: gaps closed, no pinholes, no specks → (RGBA black with
    the shadow in alpha, its top-left corner in the render's px)"""
    from PIL import ImageFilter
    m = Image.fromarray(((np.array(Image.open(spng).convert('RGBA'))[..., 3] > 127) * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MaxFilter(close)).filter(ImageFilter.MinFilter(close))
    a = ndimage.binary_fill_holes(np.array(m) > 0); lab, n = ndimage.label(a)
    if n:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)); a = np.isin(lab, np.nonzero(sizes >= 0.02 * sizes.max())[0] + 1)
    m = Image.fromarray((a * 255).astype(np.uint8)); bb = m.getbbox()
    if bb is None: return None, (0, 0)
    sh = Image.new('RGBA', (bb[2] - bb[0], bb[3] - bb[1]), (0, 0, 0, 0)); sh.putalpha(m.crop(bb))
    return sh, (bb[0], bb[1])


def _figure(a):
    """(crown, feet-to-crown height): the crown is the top of the head itself, the first row as wide as 40 % of the head - what stands up
    off it (a headband's antennae, bunny ears) is left out, else their tips, drawn taller in one sheet than another, threw the head's
    band and its neck off (the alien's heads came out bigger in the second sheet)"""
    m = a[..., 3] > 100; ys = np.nonzero(m.any(1))[0]; w = m.sum(1)
    top = ys[0] + int(np.argmax(w[ys[0]:] >= 0.4 * w[ys[0]:ys[0] + int(0.15 * (ys[-1] - ys[0]))].max()))
    return top, ys[-1] - top


def head_scale(ref, img, neck):
    """how big img's head is against ref's: ref's head band searched over scale and shift in img"""
    A = np.array(ref).astype(float); B = np.array(img).astype(float); t0, H0 = _figure(A); t1, _ = _figure(B)
    R = A[max(0, t0 - 4):int(t0 + 0.92 * neck * H0)]; xs = np.nonzero((R[..., 3] > 100).any(0))[0]
    x0 = max(0, xs[0] - 6); R = R[:, x0:xs[-1] + 7]; rim = Image.fromarray(R.astype(np.uint8)); best = None

    def score(s, dx, dy):
        K = np.array(rim.resize((max(1, round(rim.width * s)), max(1, round(rim.height * s))), Image.BILINEAR)).astype(float)
        h, w = K.shape[:2]; y = t1 - round(4 * s) + dy; x = round(x0 + (rim.width - w) / 2) + dx
        if y < 0 or x < 0 or y + h > B.shape[0] or x + w > B.shape[1]: return None
        P = B[y:y + h, x:x + w]; m = (K[..., 3] > 100) | (P[..., 3] > 100)
        if not m.any(): return None
        return (np.abs(K[..., :3] - P[..., :3]).sum(2) * m).sum() / m.sum() + 2 * ((K[..., 3] > 100) != (P[..., 3] > 100)).mean() * 255
    for s in np.arange(0.86, 1.141, 0.01):
        for dy in range(-6, 7, 3):
            for dx in range(-40, 41, 4):
                e = score(s, dx, dy)
                if e is not None and (best is None or e < best[0]): best = (e, s, dx, dy)
    _, s0, dx0, dy0 = best
    for s in np.arange(s0 - 0.012, s0 + 0.0121, 0.003):
        for dy in range(dy0 - 2, dy0 + 3):
            for dx in range(dx0 - 3, dx0 + 4):
                e = score(s, dx, dy)
                if e is not None and e < best[0]: best = (e, s, dx, dy)
    return best[1]


def rescale_head(img, c, neck, band=0.06, order=3):
    """everything above the neck scaled by c about the neck's middle, tapering to 1 through the shoulders (no seam)"""
    a = np.array(img).astype(float); t, H = _figure(a); yn = t + neck * H; bh = band * H; rows = np.arange(a.shape[0]).astype(float)
    hb = a[int(t):int(yn), :, 3] > 100; xc = np.nonzero(hb.any(0))[0].mean() if hb.any() else a.shape[1] / 2
    fy = np.where(rows <= yn, c, np.where(rows >= yn + bh, 1.0, c + (1 - c) * (rows - yn) / bh))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float); sy = np.where(Y <= yn, yn + (Y - yn) / c, Y); sx = xc + (X - xc) / fy[:, None]
    pre = a.copy(); pre[..., :3] *= pre[..., 3:4] / 255
    out = np.stack([ndimage.map_coordinates(pre[..., ch], [sy, sx], order=order, mode='constant') for ch in range(4)], -1).clip(0, 255)
    al = out[..., 3:4]; out[..., :3] = np.where(al > 0, np.minimum(out[..., :3] * 255 / np.maximum(al, 1e-6), 255), 0)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def flip_onto(im, ren):
    """a frame flipped left to right, then moved sideways onto its own facing's render (the renders of a pair are mirror images about the
    figure, not about the picture's middle: flipped where it stood, a frame came out ~18 px off its render - 0.42-0.76 overlap where it
    fits at 0.83-0.90)"""
    a = np.asarray(im.convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT)); r = np.asarray(Image.open(ren).convert('RGBA'))[..., 3] > 128; m = a[..., 3] > 127
    dx = max(range(-60, 61), key=lambda s: (np.roll(m, s, 1) & r).sum() / max(1, (np.roll(m, s, 1) | r).sum()))
    out = np.zeros_like(a)
    if dx >= 0: out[:, dx:] = a[:, :a.shape[1] - dx]
    else: out[:, :dx] = a[:, -dx:]
    return Image.fromarray(out)


def head_vs_render(im, ren, band=0.13):
    """how big the drawn head is against the 3D model's in the same frame, heights matched: the square root of the area each has in the
    band under the crown - the facings are drawn one by one, and a side view's head came out up to ~9 % bigger than the front's"""
    def area(a):
        t, H = _figure(a.astype(float)); return (a[..., 3] > 100)[t:t + int(band * H)].sum(), H
    (af, hf), (ar, hr) = area(np.asarray(im.convert('RGBA'))), area(np.asarray(Image.open(ren).convert('RGBA')))
    return float(np.sqrt(af / max(ar, 1)) * hr / max(hf, 1))


def sheet_scales(scales, own=(), n=4):
    """steady's head scales → a factor per frame for fit_walk's `mult`: each sheet of four (a frame drawn alone on its own) at its
    frames' median. The model draws one sheet's whole figure a few % bigger than the other's (the alien's second sheets ~15 %): steady
    alone then shrank only the head, and the hair and the body stayed big - it read as the head growing and shrinking"""
    out = list(scales)
    for g in range(0, len(scales), n):
        idx = [i for i in range(g, min(g + n, len(scales))) if i not in own]
        if idx:
            m = float(np.median([scales[i] for i in idx]))
            for i in idx: out[i] = m
    return out


def steady(frames, neck=0.16):
    """a walk's heads to one size (each frame drawn on its own comes out a few % bigger or smaller): measured twice on quick previews,
    each frame rescaled once, sharply. → (frames, scales applied)"""
    total = [1.0] * len(frames); work = list(frames)
    for _ in range(2):
        ss = [1.0] + [head_scale(work[0], f, neck) for f in work[1:]]; med = float(np.median(ss))
        for i, s in enumerate(ss): total[i] *= med / s
        work = [rescale_head(f, c, neck, order=1) if abs(c - 1) >= 0.004 else f for f, c in zip(frames, total)]
    return [rescale_head(f, c, neck) if abs(c - 1) >= 0.004 else f for f, c in zip(frames, total)], total


def clear_white(im, ren=None, min_area=12):
    """the white background left enclosed between the arms and the body, between the legs (the key only floods from the edge).
    With the frame's render (`ren`), only where the render is empty (a gap in the 3D body): light clothes - grey sweatpants, a white
    shirt - are never taken for background"""
    a = np.array(im.convert('RGBA')).astype(float); rgb = a[..., :3]; al = a[..., 3]; mn, sp = rgb.min(2), rgb.max(2) - rgb.min(2)
    gap = np.ones(al.shape, bool) if ren is None else ~ndimage.binary_dilation(np.array(ren.convert('RGBA'))[..., 3] > 40, iterations=3)
    # a hole is ENCLOSED by the figure: the key already took all the white joined to the outside, so white touching the transparent
    # outside is the figure's own (white sneakers drawn a little past the render's feet were cut along its outline)
    outside = ndimage.binary_dilation(al == 0, iterations=2)
    def enclosed(lab, n):
        touch = np.zeros(n + 1, bool); touch[np.unique(lab[outside & (lab > 0)])] = True; return ~touch
    white = (mn > 228) & (sp < 22) & (al > 0) & gap; lab, n = ndimage.label(white)
    if n:
        size = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)); keep = np.zeros(n + 1, bool); keep[1:] = size >= min_area
        keep &= enclosed(lab, n); hole = keep[lab]
    else: hole = np.zeros_like(white)
    ys = np.nonzero((al > 0).any(1))[0]; cut = ys[0] + int(0.5 * (ys[-1] - ys[0]))
    grey = (mn > 165) & (sp < 24) & (al > 0) & gap; grey[:cut] = False; lab2, n2 = ndimage.label(grey)
    if n2:
        size2 = ndimage.sum(np.ones_like(lab2), lab2, range(1, n2 + 1)); keep2 = np.zeros(n2 + 1, bool); keep2[1:] = size2 >= 8
        keep2 &= enclosed(lab2, n2); hole |= keep2[lab2]
    if not hole.any(): return im
    rim = ndimage.binary_dilation(hole, iterations=2) & ~hole & (sp < 30) & (al > 0)
    w = np.clip((mn - 150) / (228 - 150), 0, 1); a[..., 3] = np.where(hole, 0, np.where(rim, al * (1 - w), al))
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def defringe(im, band=3, inner=4):
    """the white halo round dark outlines (hair): edge pixels unmixed against the colour a few px inside"""
    a = np.array(im.convert('RGBA')).astype(float); al = a[..., 3]; solid = al > 127
    d = ndimage.distance_transform_edt(solid); _, (iy, ix) = ndimage.distance_transform_edt(~(d >= inner), return_indices=True)
    F = a[iy, ix, :3]; lum = lambda c: c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114
    Lp, Lf = lum(a[..., :3]), lum(F); k = np.clip((255 - Lp) / np.maximum(255 - Lf, 1), 0, 1)
    pred = k[..., None] * F + (1 - k[..., None]) * 255; resid = np.abs(pred - a[..., :3]).max(2)
    use = solid & (d <= band) & (Lf < 150) & (Lp > Lf + 6) & (resid < 16)
    a[..., 3] = np.where(use, al * k, al); a[..., :3] = np.where(use[..., None], F, a[..., :3])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))
