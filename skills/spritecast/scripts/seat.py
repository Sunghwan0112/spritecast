"""seat: a seated character (charpipe.py sit) put on a finished prop (isoprop.py), and the prop's front piece for them worked out - what of
the chair stands in front of the sitter (an armrest, the seat's front edge, a table's near side) - from both of their heights, no painting.

    python seat.py PROP.json CHAR.json [--view turn-90] [--at X,Y] [--facing south-west] [--height 1.3] [--sink 0.03]

PROP.json  a prop finished with isoprop.py (its folder has sprite.png, render.json and render-height.png - re-run `render` if not)
CHAR.json  a character with its seated views drawn (charpipe.py sit --draw)
--view     which view of a prop with several (turn-<deg>, or a facing name for a character prop)
--at       where on the footprint the sitter's seat point goes, in metres from the footprint's corner (default: its middle); X,Y,Z also
           gives the seat's height (a model's seat hidden behind its back in this view)
--facing   which way the sitter faces (default: the way the seat opens - the side away from the highest part, the backrest)
--height   the character's standing height in metres (default: the spec's "height_m", else 1.7)
--sink     how far into a soft cushion they sink, metres (default 0.03)

→ <the prop's view folder>/seat/<character>-<facing>/: front.png (the prop's own picture where it stands in front of them - draw it over
the sitter, at the sprite's place), seat.json (where to draw the sitter's frame: its top-left in the sprite's px and its scale), and
preview.png (the prop, the sitter, the front piece).
How: every pixel of the prop's guide has its height (render-height.png), and every pixel of the seated figure too (render/sit-*-h.png);
with the camera's pitch θ a point's distance toward the camera is y/s·cot θ + h/sin θ (y its screen row, s px a metre, h its height).
Where both are, the nearer one is in front. Where the drawing goes past its 3D outline (hair, a cushion drawn plumper), the nearest
3D pixel's height stands in.
"""
import argparse, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

DIRS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
SCREEN = {'east': (1, 0), 'west': (-1, 0), 'south': (0, 1), 'north': (0, -1),               # a facing's direction on screen (2:1)
          'south-east': (2, 1), 'south-west': (-2, 1), 'north-east': (2, -1), 'north-west': (-2, -1)}


def heights(path, top):
    """a height picture (16 bits in red and green) → (heights, where something is)"""
    h = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    m = h[..., 3] > 250
    return np.where(m, (h[..., 0] * 256 + h[..., 1]) / 65535 * top, np.nan), m


def fill_nearest(z, have):
    """every pixel the value of the nearest pixel that has one"""
    if have.all(): return z
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    return z[iy, ix]


def facing_of(v):
    """a screen vector → the nearest of the 8 facings"""
    v = np.array(v, float); v /= np.linalg.norm(v)
    return max(DIRS, key=lambda d: float(np.dot(v, np.array(SCREEN[d], float) / np.linalg.norm(SCREEN[d]))))


def run(prop_spec, char_spec, view=None, at=None, facing=None, height=None, sink=0.03):
    ps = Path(prop_spec).resolve(); P = json.loads(ps.read_text()); pd = ps.parent / P['name']
    vd = pd / view if view else pd
    if not (vd / 'sprite.json').exists(): sys.exit(f'seat: {vd} has no sprite.json - finish the prop first (isoprop.py finish), or pick a --view')
    if not (vd / 'render-height.png').exists(): sys.exit(f'seat: {vd} has no render-height.png - re-run `isoprop.py render` (free)')
    sj = json.loads((vd / 'sprite.json').read_text()); rj = json.loads((vd / 'render.json').read_text())
    s = rj['px_per_m']; th = math.radians(rj['camera']['pitch']); W, D = P['footprint']
    # the prop's picture on the render's canvas: the sprite is a crop of it (the footprint's corners tell where)
    off = np.array(rj['footprint_px'][0]) - np.array(sj['footprint_px'][0])            # sprite px + off = render px
    spr = Image.open(vd / 'sprite.png').convert('RGBA'); sa = np.asarray(spr)
    zc, mc = heights(vd / 'render-height.png', rj['height_top'])
    fp = np.array(rj['footprint_px'], float)

    def proj(x, y, z):          # a point on/over the footprint (m) → render px
        p = fp[0] + x / W * (fp[1] - fp[0]) + y / D * (fp[3] - fp[0]); return np.array([p[0], p[1] - z * s * math.cos(th)])
    x, y = (at[0], at[1]) if at else (W / 2, D / 2)

    blocks = [b['box'] for b in (P.get('blocks') or P.get('blocks_draft') or []) if 'box' in b]
    arcs = [b['arc'] for b in (P.get('blocks') or []) if 'arc' in b]

    def surface(x, y):
        """the height of what the guide shows at (x, y): the height whose point lands on a pixel that high; hidden from this view (the
        seat of a chair seen from behind) the top of the spec's blocks there"""
        for z in np.arange(rj['height_top'], -0.001, -0.005):
            u, v = np.round(proj(x, y, z)).astype(int)
            if 0 <= v < zc.shape[0] and 0 <= u < zc.shape[1] and mc[v, u] and abs(zc[v, u] - z) < 0.02: return z
        tops = [b[5] for b in blocks if b[0] <= x <= b[1] and b[2] <= y <= b[3]]
        for cx, cy, r0, r1, a0, a1, h0, h1 in arcs:
            r, a = math.hypot(x - cx, y - cy), math.degrees(math.atan2(y - cy, x - cx)) % 360
            if r0 <= r <= r1 and (a - a0) % 360 <= (a1 - a0) % 360: tops.append(h1)
        return max(tops) if tops else None
    zs = at[2] if at and len(at) > 2 else surface(x, y)
    if zs is None: sys.exit(f'seat: nothing to sit on at {x:.2f}, {y:.2f} (the seat is hidden from this view and the spec has no blocks) - '
                            'pass --at X,Y,Z with the seat\'s height (from the prop\'s front view)')
    # which way the seat opens: away from the tallest part of the guide (the backrest) - its pixels taken down to the ground and back
    # onto the footprint, the way from them to the seat snapped to the footprint's nearest axis (a chair faces along one), then on screen
    if not facing:
        top = np.nanmax(np.where(mc, zc, np.nan)); ys, xs = np.nonzero(mc & (np.nan_to_num(zc) > max(zs + 0.15, top - 0.1)))
        if len(xs):
            g = np.stack([xs, ys + zc[ys, xs] * s * math.cos(th)], 1) - fp[0]
            M = np.linalg.inv(np.stack([(fp[1] - fp[0]) / W, (fp[3] - fp[0]) / D], 1)); bx, by = (M @ g.T).mean(1)
            vx, vy = x - bx, y - by; mx = max(abs(vx), abs(vy))
            axis = tuple(np.sign(v) if abs(v) > 0.6 * mx else 0 for v in (vx, vy))     # along an axis, or a diagonal (a curved bench)
            axis = tuple(a / math.hypot(*axis) for a in axis)
            facing = facing_of(proj(x + 0.1 * axis[0], y + 0.1 * axis[1], 0) - proj(x, y, 0))
        else: facing, axis = 'south', None
    else: axis = None
    # the sitter
    cs = Path(char_spec).resolve(); C = json.loads(cs.read_text()); cd = cs.parent / C['name']
    seats = json.loads((cd / 'render/sit.json').read_text()); info = seats.get('_', {'px': 512, 'view_h': 1.25})
    if not (cd / f'frames/sit-{facing}.png').exists(): sys.exit(f'seat: {cd} has no drawn seated view {facing} - charpipe.py sit --draw first')
    if not (cd / f'render/sit-{facing}-h.png').exists(): sys.exit('seat: re-run `charpipe.py sit` (free) for the heights of the seated views')
    H = height or C.get('height_m') or 1.7
    # the knees at the seat's front edge, the shins hanging past it (in the middle a short sitter's shins went into the cushion; on a deep
    # seat a child sits forward, as children do), the hips never into the backrest
    if not at and axis is not None and seats[facing].get('knee'):
        ax, ay = axis; step = lambda t_: (x + ax * t_, y + ay * t_)
        # (the front of the whole chair, not only its cushion: a base or a frame under the seat that stands further out would hide the shins)
        front_t = next((t_ for t_ in np.arange(0, 1.5, 0.01) if (lambda z: z is None or z < 0.15)(surface(*step(t_)))), 0)   # (not a splayed leg's foot)
        back_t = next((t_ for t_ in np.arange(0, -1.5, -0.01) if (lambda z: z is None or z > zs + 0.08)(surface(*step(t_)))), -0.2)
        t_ = max(back_t + 0.12, front_t - seats[facing]['knee'] * H + 0.09)        # (the knees past it: the boots' backs clear the front)
        x, y = step(t_); zs = surface(x, y) or zs
    k = s / (info['px'] / (info['view_h'] * H))                                          # sitter's render px → the prop's render px
    fr = Image.open(cd / f'frames/sit-{facing}.png').convert('RGBA'); zb, mb = heights(cd / f'render/sit-{facing}-h.png', info['view_h'])
    size = (round(fr.width * k), round(fr.height * k))
    fr = fr.resize(size, Image.LANCZOS)
    zb = Image.fromarray(np.nan_to_num(zb, nan=0).astype(np.float32)).resize(size, Image.NEAREST); mb = Image.fromarray(mb).resize(size, Image.NEAREST)
    zb = np.asarray(zb) * H; mb = np.asarray(mb)
    lift = zs - sink - seats[facing]['seatY'] * H                                           # the figure's floor to this seat
    zb = zb + lift
    sp = np.array(seats[facing]['seat']) * np.array(size); tp = proj(x, y, zs - sink)
    ox, oy = np.round(tp - sp).astype(int)                                                  # the frame's top-left on the render's canvas
    od = vd / 'seat' / f"{C['name']}-{facing}"; nudge = [0, 0]
    if (od / 'nudge.json').exists():                                                        # moved by hand on the touch-up page
        nudge = json.loads((od / 'nudge.json').read_text()); ox += int(nudge[0]); oy += int(nudge[1])
    # both on one canvas (the render's, grown to hold the sitter)
    Hc, Wc = zc.shape; sx0, sy0 = int(round(off[0])), int(round(off[1]))       # (a drawing wider than its guide makes the sprite stick out of the canvas)
    L, T = min(0, ox, sx0), min(0, oy, sy0); R, B = max(Wc, ox + size[0], sx0 + sa.shape[1]), max(Hc, oy + size[1], sy0 + sa.shape[0])
    cw, ch = R - L, B - T
    def place(a, x0, y0, fill):
        o = np.full((ch, cw) + a.shape[2:], fill, dtype=a.dtype); o[y0 - T:y0 - T + a.shape[0], x0 - L:x0 - L + a.shape[1]] = a; return o
    chair_a = place(sa[..., 3], int(round(off[0])), int(round(off[1])), 0) > 20
    chair_z = place(fill_nearest(np.nan_to_num(zc, nan=0), mc), 0, 0, 0.0)
    chair_3d = place(mc, 0, 0, False)
    body_a = place(np.asarray(fr)[..., 3], ox, oy, 0) > 20
    body_z = place(fill_nearest(zb, mb), ox, oy, 0.0)
    yy = np.arange(ch)[:, None] + T
    dist = lambda z: yy / s / math.tan(th) + z / math.sin(th)                               # toward the camera (m)
    # a chair pixel past the guide's own outline (the drawing plumper) takes the nearest guide pixel's height
    chair_z = np.where(chair_3d, chair_z, fill_nearest(np.where(chair_3d, chair_z, 0), chair_3d))
    front = chair_a & body_a & (dist(chair_z) > dist(body_z) + 0.04)
    front = ndimage.binary_opening(front, iterations=2)
    lab, n = ndimage.label(front)                                                           # no crumbs: the drawing and the 3D differ a little
    if n:
        sz = ndimage.sum(front, lab, range(1, n + 1)); front = np.isin(lab, 1 + np.nonzero(sz >= max(60, 0.002 * body_a.sum()))[0])
    front = ndimage.binary_fill_holes(front)
    front = ndimage.binary_dilation(front, iterations=2) & chair_a                          # (a little over the sitter's edge: no seam)
    # out: the front piece on the sprite's own canvas, where to draw the sitter, a preview
    x0, y0 = int(round(off[0])) - L, int(round(off[1])) - T
    fm = front[y0:y0 + sa.shape[0], x0:x0 + sa.shape[1]]
    piece = sa.copy(); piece[~fm] = 0
    od.mkdir(parents=True, exist_ok=True)
    Image.fromarray(piece).save(od / 'front.png', optimize=True)
    meta = {'sitter': C['name'], 'facing': facing, 'frame': f"{C['name']}/frames/sit-{facing}.png", 'scale': round(k, 5),
            'frame_px': [size[0], size[1]],
            'top_left_in_sprite': [int(ox - off[0]), int(oy - off[1])], 'seat_m': [round(x, 3), round(y, 3), round(zs, 3)],
            'front': 'front.png', 'front_px': int(fm.sum()), 'nudge_px': nudge,
            'made_by': {'prop': str(ps), 'char': str(cs), 'view': view, 'at': [round(x, 4), round(y, 4), round(zs, 4)], 'facing': facing, 'height': H, 'sink': sink},
            'note': 'draw the sprite, then the sitter\'s frame at top_left_in_sprite (scaled by `scale`), then front.png at the sprite\'s place'}
    (od / 'seat.json').write_text(json.dumps(meta, indent=1))
    pv = Image.new('RGBA', (cw + 40, ch + 40), (240, 236, 228, 255))
    if (vd / 'shadow.png').exists():
        shd = np.asarray(Image.open(vd / 'shadow.png').convert('RGBA')).copy(); shd[..., 3] = (shd[..., 3] * 0.3).astype(np.uint8)
        so = sj['shadow']['offset_px']; pv.alpha_composite(Image.fromarray(shd), (20 + x0 + so[0], 20 + y0 + so[1]))
    pv.alpha_composite(spr, (20 + x0, 20 + y0)); pv.alpha_composite(fr, (20 + ox - L, 20 + oy - T)); pv.alpha_composite(Image.fromarray(piece), (20 + x0, 20 + y0))
    pv.convert('RGB').save(od / 'preview.png')
    print(f'seat: {od} - {facing}, the seat {zs:.2f} m up at ({x:.2f}, {y:.2f}); front piece {int(fm.sum())} px')
    return od


def rerun(od):
    """the same seat made again (after nudge.json changed), with what made it the first time"""
    m = json.loads((Path(od) / 'seat.json').read_text())['made_by']
    return run(m['prop'], m['char'], m['view'], tuple(m['at']), m['facing'], m['height'], m['sink'])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('prop'); ap.add_argument('char'); ap.add_argument('--view'); ap.add_argument('--at'); ap.add_argument('--facing', choices=DIRS)
    ap.add_argument('--height', type=float); ap.add_argument('--sink', type=float, default=0.03)
    a = ap.parse_args()
    run(a.prop, a.char, a.view, tuple(float(v) for v in a.at.split(',')) if a.at else None, a.facing, a.height, a.sink)
