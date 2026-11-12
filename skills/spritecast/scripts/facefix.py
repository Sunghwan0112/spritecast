"""Faces drawn in by hand (by Claude, looking at the character's design and at each frame), on the frames as GPT drew them.
    python facefix.py STRIP.png EDITS.json OUT.png                (pixelart.py applies <character>/pixel/face-edits-<clip>-<dir>.json by itself)
EDITS.json - x, y are inside a frame of the animation's own strip (<character>/pixel/faces/<clip>-<dir>.png, what --facemap prints):
  "frames": N
  "colours": {"D": [r,g,b], ...}      taken from the character's design (the eye's dark, its brown, the mouth...)
  "stamps":  {"eye": [[dx, dy, "D"], ...], ...}       a feature as pixels from its top-left; a 4th item "skin" = only onto skin
  "place":   {"0": [["eye", x, y], ...], ...}         where each stamp goes in each frame
  "edits":   {"0": [[x, y, "S"], ...], ...}           single pixels; "S" = the frame's own skin colour there (to rub out the old eye)
  "flat":    {"4": [[x0, y0, x1, y1]], ...}           boxes whose skin (every light pixel) becomes the frame's one skin colour, before anything else
Nothing is painted outside the figure. "skin": only where the frame is light (skin), so a mouth never lands on hair or collar."""
import json, sys
import numpy as np
from PIL import Image

def apply(f, e, k):
    """frame k (RGBA array, changed in place)"""
    src = f.copy(); w = f.shape[1]
    for x0, y0, x1, y1 in e.get('flat', {}).get(str(k), []):          # (GPT shaded some frames' faces, and features sink into the shading)
        box = src[y0:y1 + 1, x0:x1 + 1]; lt = (box[..., 3] > 0) & (box[..., :3].min(2) > 100) & (box[..., 0] > 170)
        if lt.any(): v, cnt = np.unique(box[lt][:, :3], axis=0, return_counts=True); f[y0:y1 + 1, x0:x1 + 1][lt, :3] = v[cnt.argmax()]
    src = f.copy()
    px = [list(p) for p in e.get('edits', {}).get(str(k), [])]
    for name, x, y in e.get('place', {}).get(str(k), []): px += [[x + p[0], y + p[1]] + list(p[2:]) for p in e['stamps'][name]]
    for x, y, c, *opt in px:
        if not (0 <= y < f.shape[0] and 0 <= x < w) or src[y, x, 3] == 0: continue
        if 'skin' in opt and src[y, x, :3].min() < 140: continue
        if c == 'S':
            nb = src[max(0, y - 3):y + 4, max(0, x - 3):x + 4].reshape(-1, 4); nb = nb[(nb[:, 3] > 0) & (nb[:, :3].min(1) > 140)]
            if not len(nb): continue
            v, cnt = np.unique(nb[:, :3], axis=0, return_counts=True); f[y, x, :3] = v[cnt.argmax()]
        else: f[y, x, :3] = e['colours'][c]
    return f

if __name__ == '__main__':
    strip, edits, out = sys.argv[1:4]; e = json.loads(open(edits).read()); a = np.asarray(Image.open(strip).convert('RGBA')).copy(); n = e['frames']; w = a.shape[1] // n
    for k in range(n): apply(a[:, k * w:(k + 1) * w], e, k)
    Image.fromarray(a).save(out); print('facefix:', out)
