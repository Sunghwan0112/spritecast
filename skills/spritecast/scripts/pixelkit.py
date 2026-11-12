"""Pixel helpers for pixelart.py: area-average downscale, Lab, one palette by k-means, nearest colour, stray-pixel clean-up."""
from pathlib import Path
import numpy as np
from PIL import Image
FIG = 770.0          # the standing figure's height in the render's frames, px (pixelart.py measures it from the character's own render)

def down(im, h):     # area average, premultiplied
    k = h / FIG; a = np.asarray(im, np.float32) / 255
    pm = np.dstack([a[..., :3] * a[..., 3:], a[..., 3]])
    w, hh = round(im.width * k), round(im.height * k)
    ch = [np.asarray(Image.fromarray(pm[..., i]).resize((w, hh), Image.BOX)) for i in range(4)]
    al = ch[3]; rgb = np.dstack(ch[:3]) / np.maximum(al, 1e-4)[..., None]
    return np.clip(rgb, 0, 1), al

_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_W = np.array([0.95047, 1.0, 1.08883])
def lab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    x = c.reshape(-1, 3) @ _M.T / _W
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)
def lab2rgb(L):
    fy = (L[:, 0] + 16) / 116; fx = fy + L[:, 1] / 500; fz = fy - L[:, 2] / 200
    f = np.stack([fx, fy, fz], 1)
    x = np.where(f > 0.206893, f ** 3, (f - 16 / 116) / 7.787) * _W
    c = x @ np.linalg.inv(_M).T
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)

def palette(pix, n, seed=0):   # k-means in Lab over every frame's pixels
    from scipy.cluster.vq import kmeans2
    L = lab(pix); rng = np.random.default_rng(seed)
    if len(L) > 60000: L = L[rng.choice(len(L), 60000, replace=False)]
    c, _ = kmeans2(L, n, minit='++', seed=seed, iter=40)
    return c[~np.isnan(c).any(1)]

def snap(rgb, pal_lab, pal_rgb):
    L = lab(rgb); d = ((L[:, None, :] - pal_lab[None]) ** 2).sum(2)
    return d.argmin(1).reshape(rgb.shape[:2])

def clean(idx, m):   # a pixel none of whose 4 neighbours shares its colour takes its neighbours' commonest
    out = idx.copy(); H, W = idx.shape
    for y, x in zip(*np.nonzero(m)):
        nb = [idx[j, i] for j, i in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)) if 0 <= j < H and 0 <= i < W and m[j, i]]
        if nb and idx[y, x] not in nb:
            v, c = np.unique(nb, return_counts=True); out[y, x] = v[c.argmax()]
    return out


PALETTES = Path(__file__).resolve().parent.parent / 'palettes'          # the palettes that come with the skill: <name>.hex, its first line says whose it is


def palettes():
    """the palettes that come with the skill -> [(name, colours, what its first line says)]"""
    return [(f.stem, len(_text(f.read_text())), f.read_text().splitlines()[0].lstrip('; ').strip()) for f in sorted(PALETTES.glob('*.hex'))]


def _text(s):          # one hex colour a line (.hex, Lospec), or "r g b" lines (.gpl of GIMP, .pal of JASC / Paint Shop Pro); other lines are passed over
    import re
    c = []
    for line in s.splitlines():
        m = re.fullmatch(r'\s*#?([0-9a-fA-F]{6})\s*', line); g = re.match(r'\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})(\s|$)', line)
        if m: c.append([int(m.group(1)[k:k + 2], 16) for k in (0, 2, 4)])
        elif g and all(int(v) < 256 for v in g.groups()[:3]): c.append([int(v) for v in g.groups()[:3]])
    return c


def _aseprite(b):          # an Aseprite sprite (.aseprite / .ase): its palette chunk - the new one (0x2019), or the old (0x0004)
    import struct
    new, old = {}, []; n_frames = struct.unpack_from('<H', b, 6)[0]; at = 128
    for _ in range(n_frames):
        size, magic, n_old, _dur, _r, n_new = struct.unpack_from('<IHHH2sI', b, at)
        if magic != 0xF1FA: break
        q = at + 16
        for _ in range(n_new or n_old):
            cs, ct = struct.unpack_from('<IH', b, q)
            if ct == 0x2019:
                _n, first, last = struct.unpack_from('<III', b, q + 6); r = q + 6 + 20
                for k in range(first, last + 1):
                    fl, cr, cg, cb, _a = struct.unpack_from('<HBBBB', b, r); r += 6; new[k] = [cr, cg, cb]
                    if fl & 1: r += 2 + struct.unpack_from('<H', b, r)[0]
            elif ct == 0x0004 and not old:
                packets = struct.unpack_from('<H', b, q + 6)[0]; r = q + 8
                for _ in range(packets):
                    _skip, n = b[r], b[r + 1] or 256; r += 2; old += [list(b[r + 3 * k:r + 3 * k + 3]) for k in range(n)]; r += 3 * n
            q += cs
        at += size
    return [new[k] for k in sorted(new)] or old


def _swatch(b):          # Adobe Swatch Exchange (also ".ase"): its RGB and Gray swatches
    import struct
    c = []; at = 12
    for _ in range(struct.unpack_from('>I', b, 8)[0]):
        kind, ln = struct.unpack_from('>HI', b, at); q = at + 6; at = q + ln
        if kind != 1: continue
        q += 2 + 2 * struct.unpack_from('>H', b, q)[0]; model = b[q:q + 4]; q += 4
        if model == b'RGB ': c.append([round(255 * v) for v in struct.unpack_from('>3f', b, q)])
        elif model == b'Gray': c.append([round(255 * struct.unpack_from('>f', b, q)[0])] * 3)
    return c


def load_palette(path):
    """a palette: one that comes with the skill by its NAME (pico8, gameboy, ... - `palettes()`), or the user's own FILE, in what Aseprite
    reads: an image of it (.png .gif .bmp .pcx: every colour in it), .hex (one hex colour a line - Lospec), .gpl (GIMP), .pal (JASC text,
    or Microsoft RIFF), .act (Adobe colour table), .col (Animator / Animator Pro), .aseprite / .ase (the sprite's own palette; or an Adobe
    swatch file)  ->  its colours, uint8 (n, 3), each once, in the file's order"""
    import struct
    from PIL import Image
    p = Path(path)
    if not p.exists() and (PALETTES / f'{str(path).lower()}.hex').exists(): p = PALETTES / f'{str(path).lower()}.hex'
    if not p.exists(): raise SystemExit(f"--palette {path}: no such file, and no palette of that name comes with the skill ({', '.join(n for n, _, _ in palettes())} - `--palette list` shows them)")
    b = p.read_bytes(); ext = p.suffix.lower()
    if ext in ('.png', '.gif', '.bmp', '.pcx', '.jpg', '.jpeg', '.webp'):
        a = np.asarray(Image.open(p).convert('RGBA')).reshape(-1, 4); a = a[a[:, 3] > 0][:, :3]; _, first = np.unique(a, axis=0, return_index=True); c = a[np.sort(first)].tolist()
    elif b[:4] == b'RIFF':          # Microsoft .pal: RIFF, "PAL ", a "data" chunk = version, count, then r g b flags
        q = b.index(b'data') + 8; n = struct.unpack_from('<H', b, q + 2)[0]; c = [list(b[q + 4 + 4 * k:q + 4 + 4 * k + 3]) for k in range(n)]
    elif b[:4] == b'ASEF': c = _swatch(b)
    elif ext in ('.ase', '.aseprite') or (len(b) > 6 and b[4:6] == b'\xe0\xa5'): c = _aseprite(b)
    elif ext == '.act':          # 256 r g b; then, in some, how many of them are used (2 bytes) and the transparent one
        n = struct.unpack_from('>H', b, 768)[0] if len(b) >= 772 else 256; c = [list(b[3 * k:3 * k + 3]) for k in range(min(n, 256) or 256)]
    elif ext == '.col':          # Animator: 256 r g b of 0-63. Animator Pro: an 8-byte head (size, 0xB123, version), then r g b of 0-255
        if len(b) == 768: c = [[min(255, v * 255 // 63) for v in b[3 * k:3 * k + 3]] for k in range(256)]
        else: c = [list(b[8 + 3 * k:8 + 3 * k + 3]) for k in range((len(b) - 8) // 3)]
    else:
        try: c = _text(b.decode('utf-8', 'ignore'))
        except Exception: c = []
    c = np.array(c, np.int64).reshape(-1, 3).clip(0, 255).astype(np.uint8)
    if len(c): _, first = np.unique(c, axis=0, return_index=True); c = c[np.sort(first)]          # (each colour once: an .act is padded with black to 256)
    if not 2 <= len(c) <= 256: raise SystemExit(f'--palette {path}: {len(c)} colours read from it (2 to 256 wanted). It reads .png .gif .bmp .pcx, .hex, .gpl, .pal, .act, .col, .aseprite / .ase')
    return c


def show_palettes():
    """`--palette list`: what comes with the skill, said in the terminal"""
    print('palettes that come with the skill (--palette NAME); a picture of them: ' + str(PALETTES / 'preview.png'))
    for n, k, what in palettes(): print(f'  {n:12} {k:3} colours   {what.split(" - ")[0]} ({what.split(" - ")[1]})')
    print('or your own file: --palette FILE  (.png .gif .bmp .pcx, .hex, .gpl, .pal, .act, .col, .aseprite / .ase)')


def to_palette(rgba, pal):
    """a sprite (RGBA uint8 array) with every pixel given the palette's nearest colour (nearest to the eye: in Lab)"""
    a = np.asarray(rgba).copy(); m = a[..., 3] > 0
    if not m.any(): return a
    u, inv = np.unique(a[m][:, :3], axis=0, return_inverse=True); L = lab(pal.astype(np.float32) / 255)
    a[m, :3] = pal[((lab(u.astype(np.float32) / 255)[:, None, :] - L[None]) ** 2).sum(2).argmin(1)][inv.reshape(-1)]; return a
