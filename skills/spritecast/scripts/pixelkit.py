"""Pixel helpers for pixelart.py: area-average downscale, Lab, one palette by k-means, nearest colour, stray-pixel clean-up."""
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


def load_palette(path):
    """a palette the user HAS (their game's): a .png / .gif (every colour in it), or a text file with one hex colour a line
    (#1d2b53 or 1d2b53; a .hex from Lospec, a .gpl's "r g b" lines too) -> its colours, uint8 (n, 3)"""
    import re
    from pathlib import Path
    from PIL import Image
    p = Path(path)
    if p.suffix.lower() in ('.png', '.gif', '.bmp'):
        a = np.asarray(Image.open(p).convert('RGBA')).reshape(-1, 4); c = np.unique(a[a[:, 3] > 0][:, :3], axis=0)
    else:
        c = []
        for line in p.read_text().splitlines():
            m = re.fullmatch(r'\s*#?([0-9a-fA-F]{6})\s*', line); g = re.match(r'\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\b', line)
            if m: c.append([int(m.group(1)[k:k + 2], 16) for k in (0, 2, 4)])
            elif g: c.append([int(v) for v in g.groups()])
        c = np.array(c, np.uint8).reshape(-1, 3)
    if not 2 <= len(c) <= 256: raise SystemExit(f'--palette {path}: {len(c)} colours read from it (2 to 256 wanted: a .png of the palette, or a text file with one hex colour a line)')
    return c


def to_palette(rgba, pal):
    """a sprite (RGBA uint8 array) with every pixel given the palette's nearest colour (nearest to the eye: in Lab)"""
    a = np.asarray(rgba).copy(); m = a[..., 3] > 0
    if not m.any(): return a
    u, inv = np.unique(a[m][:, :3], axis=0, return_inverse=True); L = lab(pal.astype(np.float32) / 255)
    a[m, :3] = pal[((lab(u.astype(np.float32) / 255)[:, None, :] - L[None]) ** 2).sum(2).argmin(1)][inv.reshape(-1)]; return a
