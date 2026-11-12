"""proppixel: a PROP as pixel art, from every side its spec has - the way pixelart.py makes a character's frames.

    python proppixel.py PROP.json                    what it would draw and what that costs - spends nothing
    python proppixel.py PROP.json --yes              draws what is missing (one picture a view, ~$0.07-0.10), reads all
    python proppixel.py PROP.json --ppm 54           pixels per metre (default 54: a 1.3 m character 70 px tall - give the pixel
                                                     character's own: its figure_px / its height in metres - so they stand on one floor)
    python proppixel.py PROP.json --again 90         that view drawn anew

It needs the prop's guide (isoprop.py render; with "views": [0, 90, 180, 270] in the spec, one per side) and OPENAI_API_KEY.
    guide (3D) -> pixelized -> the image model redraws it as pixel art on the same grid -> read back on the grid it drew
    -> brought to the guide's size -> <prop>/out-pixel/sprite[-<view>].png, pixel.json (size, anchor), preview.png

FROM SEVERAL SIDES, THE GUIDE HAS TO BE A 3D MODEL (isoprop.py model - Tripo, ~20 credits - then yaws, render). A block guide shows
where the thing stands and how big it is, not which face has the screen on it: an arcade cabinet drawn from blocks came out with its
screen on the wrong face in one view of four and its top another colour in two. From a model every side has its own things on it, and
the image model is shown the same view at full size beside the pixelized one to read it by: a ramen cart came out right from all four.

Never under 64 squares: a prop that would be smaller at this scale is drawn 64 tall and made smaller afterwards (as pixelart.py does)."""
import argparse, json, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
PRICE = 0.08
TURN = {0: 'It is seen from its FRONT-LEFT: its front faces down-left, toward the viewer.', 90: 'It is turned a quarter: its front faces down-RIGHT, toward the viewer - the front and the other side show.',
        180: 'It is seen from BEHIND: its front faces up-right, away from the viewer - draw its BACK and one side; nothing of the front is to be seen except what sticks out past its edge.',
        270: 'It is seen from BEHIND, from the other side: its front faces up-left, away from the viewer - draw its BACK and the other side; nothing of the front is to be seen except what sticks out past its edge.'}


def vdir(d, views, v): return d / f'turn-{v}' if views else d


def guide(spec, d, views, v, ppm, first):
    """the view's render pixelized -> <view>/pixel/in.png, prompt.txt, meta.json; (how many squares, their size)"""
    vd = vdir(d, views, v); o = vd / 'pixel'; o.mkdir(parents=True, exist_ok=True); meta = json.loads((vd / 'render.json').read_text())
    full = Image.open(vd / 'render.png').convert('RGBA'); box = full.getbbox(); r = full.crop(box); k = ppm / meta.get('px_per_m', 256); want = round(r.height * k); n_h = max(64, want); n_w = round(r.width * n_h / r.height)
    a = np.asarray(r, np.float32) / 255; pm = np.dstack([a[..., :3] * a[..., 3:], a[..., 3]]); ch = [np.asarray(Image.fromarray(pm[..., j]).resize((n_w, n_h), Image.BOX)) for j in range(4)]
    al = ch[3]; rgb = np.clip(np.dstack(ch[:3]) / np.maximum(al, 1e-4)[..., None], 0, 1); m = al >= 0.5
    tall = n_h > 1.15 * n_w; wide = n_w > 1.15 * n_h; CW, CH = (1024, 1536) if tall else (1536, 1024) if wide else (1024, 1024); Z = int(min(CW * 0.82 / n_w, CH * 0.82 / n_h)); gw, gh = CW // Z, CH // Z
    sh = np.ones((gh, gw, 3), np.float32); x, y = (gw - n_w) // 2, (gh - n_h) // 2; sh[y:y + n_h, x:x + n_w][m] = rgb[m]; Image.fromarray((sh * 255).round().astype(np.uint8)).resize((gw * Z, gh * Z), Image.NEAREST).save(o / 'in.png')
    near = meta.get('near') or [box[0] + r.width / 2, box[3]]          # the anchor (the footprint's near corner) in the sprite's own pixels
    model = bool(spec.get('model')); look = None
    if model: r.save(o / 'look.png'); look = o / 'look.png'
    elif (vd / 'sprite.png').exists(): look = vd / 'sprite.png'
    elif (d / 'sprite.png').exists(): look = d / 'sprite.png'
    (o / 'meta.json').write_text(json.dumps({'squares': [n_w, n_h], 'asked_px': want, 'z': Z, 'size': f'{CW}x{CH}', 'ppm': ppm, 'anchor': [round((near[0] - box[0]) * n_w / r.width, 1), round((near[1] - box[1]) * n_h / r.height, 1)],
                                             'look': str(look) if look else None}))
    rules = (f"Redraw it as FINISHED PIXEL ART for an arcade game (a 1990s 16-bit isometric game prop), ON THE SAME GRID: every sprite pixel one flat {Z}x{Z} square of a single colour, "
             "its edges exactly on the grid - no anti-aliasing, no blur, no gradients, no dithering, no half-pixels, no detail smaller than one square. Decide every pixel as a pixel "
             "artist would: a dark outline one sprite pixel wide around the whole object; one-pixel darker lines where one part passes in front of another; each surface in two or "
             "three flat tones in clean clusters, light from the upper right; about 28 colours in all.")
    head = (f"Image 1 is ONE object for a game, seen from the game's camera from above: a 3D {'model' if model else 'guide'} of it already reduced to LOW-RESOLUTION PIXELS - every "
            f"square of {Z}x{Z} px in the picture is ONE sprite pixel, on a grid that starts at the picture's top-left corner; the object is {n_h} sprite pixels tall. ")
    if model:
        text = (head + "Its shapes, its angle and its colours are right, but it is blurred: it has no outline and its small parts have run together.\n" + rules +
                " Small parts are simplified to what a few squares can say (a bottle is two or three squares, a spoke is one line of squares) - but every part that is there stays "
                "there, in its place.\n"
                "Keep it exactly where it is and exactly as big, at the SAME ANGLE: every part exactly where image 1 has it - the same side toward the viewer, the same things on the "
                "left and on the right; do not turn it, do not mirror it, do not enlarge it to fill the picture, add nothing beside it.\n"
                "Image 2 is the same 3D model from the SAME angle at full resolution: what each part is, its material and its colour - to read image 1 by. NOT its rendering style "
                "(this is pixel art) and not its size.\n")
    else:
        text = (head + "It is only a guide: plain blocks in flat colours, no outline, no detail.\n" + rules + "\n"
                "Keep it exactly where it is and exactly as big: the same footprint on the ground, the same height, the SAME ANGLE - every edge of the guide's blocks runs the way it "
                "runs in the guide; do not turn it, do not enlarge it to fill the picture, add nothing beside it. " + (TURN.get(v % 360, '') if views else '') + "\n"
                + ("Image 2 is the same object as a finished illustration" + (", seen from its front-left" if views else "") + ": its materials, colours and details to match - "
                   "NOT its drawing style (this is pixel art), not its size" + (", and NOT its angle (image 1 has the angle)" if views else "") + ".\n" if look else ''))
    n_img = 2 + bool(look)
    text += (f"Image {n_img} is this same object already drawn as pixel art from another side: exactly the same object - the same colours, the same outline, the same size of square, "
             "the same way of drawing each part.\n" if first else '')
    (o / 'prompt.txt').write_text(text + f"The object: {spec['description']}. " + (spec.get('facing', '') + '. ' if not views and spec.get('facing') else '') + "Plain pure white background, no shadow on the ground, no text.")
    return n_w, n_h, Z


def read(d, views, v):
    """the answer -> the sprite (RGBA), read on the grid it was drawn on and brought to the guide's size"""
    import pixelgrid as G, pixelkit as P, charlib as CL
    o = vdir(d, views, v) / 'pixel'; mt = json.loads((o / 'meta.json').read_text()); G.Z = mt['z']; a = np.asarray(Image.open(o / 'out.png').convert('RGB'), np.float32) / 255
    ys, xs = np.nonzero(ndi.binary_opening(a.min(2) < 0.93, np.ones((3, 3)))); c = a[max(0, ys.min() - 12):ys.max() + 13, max(0, xs.min() - 12):xs.max() + 13]; p0 = G.pitch_of([c]); G.PITCH_[0] = p0
    # the squares are not square, nor the size asked: one spacing across and one down for the picture, looked for near the size found
    cand = np.arange(p0 * 0.88, p0 * 1.12 + 0.01, 0.05); pxy = [None, None]
    for ax, q in ((1, 0), (0, 1)): g = np.abs(np.diff(c, axis=ax)).sum((1 - ax, 2)); pxy[q] = float(cand[int(np.argmax([G.lines(g, float(t), True) for t in cand]))])
    # the guide's size: the object comes back up to a third bigger or smaller than asked; it is scaled to the guide's height in squares
    k = mt['squares'][1] * pxy[1] / (ys.max() - ys.min() + 1)
    # white shut in by the object - the air under a roof, between spokes - is paper; a stack of bowls is not: the AI cut-out tells them apart
    S = max(1024, c.shape[0] + 40, c.shape[1] + 40); big = Image.new('RGB', (S, S), (255, 255, 255)); oy, ox = (S - c.shape[0]) // 2, (S - c.shape[1]) // 2
    big.paste(Image.fromarray((c * 255).round().astype(np.uint8)), (ox, oy)); mk = CL.ai_key(big); fg = None if mk is None else Image.fromarray((mk[oy:oy + c.shape[0], ox:ox + c.shape[1]] * 255).astype(np.uint8))
    if abs(k - 1) > 0.02:
        sz = (round(c.shape[1] * k), round(c.shape[0] * k)); c = np.asarray(Image.fromarray((c * 255).round().astype(np.uint8)).resize(sz, Image.LANCZOS), np.float32) / 255; fg = fg.resize(sz, Image.NEAREST) if fg is not None else None
    G.PITCH_XY[:] = pxy
    try: low, m = G.read(c, 0.0, 0.0, fg=None if fg is None else np.asarray(fg) > 127)[:2]
    finally: G.PITCH_XY[:] = [None, None]
    pl = P.palette(low[m], 28); rgb = (np.clip(P.lab2rgb(pl), 0, 1)[((P.lab(low.reshape(-1, 3))[:, None, :] - pl[None]) ** 2).sum(2).argmin(1)].reshape(low.shape) * 255).round().astype(np.uint8)
    y0, y1 = np.nonzero(m.any(1))[0][[0, -1]]; x0, x1 = np.nonzero(m.any(0))[0][[0, -1]]; im = Image.fromarray(np.dstack([rgb, (m * 255).astype(np.uint8)])[y0:y1 + 1, x0:x1 + 1])
    return im, {'squares_px': [round(pxy[0], 2), round(pxy[1], 2)], 'scaled': round(k, 2), 'ai_cut': mk is not None}


def split(out):
    """out-pixel/views.png (the views side by side, each on the same frame - what pixeledit.py edits) cut back into sprite[-<view>].png"""
    j = json.loads((out / 'pixel.json').read_text()); st = Image.open(out / 'views.png').convert('RGBA'); fw, fh = j['frame']
    for n, (v, e) in enumerate(j['views'].items()):
        x, y = e['in_frame']; w, h = e['size']; st.crop((n * fw + x, y, n * fw + x + w, y + h)).save(out / e['file'])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--yes', action='store_true'); ap.add_argument('--ppm', type=float, default=54.0); ap.add_argument('--again', default=''); ap.add_argument('--colours', type=int, default=0, help='how many colours the object has, all its sides together (default: about 28 a side). Free: nothing is drawn again')
    ap.add_argument('--palette', default='', help="a palette you already have: a .png of it, or a text file with one hex colour a line. Every pixel takes its nearest colour in it. Free")
    A = ap.parse_args(); spec = json.loads(Path(A.spec).read_text(encoding='utf-8')); d = Path(A.spec).resolve().parent / spec['name']; views = spec.get('views') or []; vs = views or [0]
    if not all((vdir(d, views, v) / 'render.png').exists() for v in vs): sys.exit('proppixel: no guide yet - run `isoprop.py render` on this spec first')
    if len(vs) > 1 and not spec.get('model'): print('NOTE: several views from a BLOCK guide - the image model cannot tell from blocks which face has what on it (it put a screen on the wrong face '
                                                     'in one view of four). For a thing whose sides differ, make its 3D model first (isoprop.py model, ~20 Tripo credits).')
    for v in vs:
        if A.again and str(v) == A.again: (vdir(d, views, v) / 'pixel/out.png').unlink(missing_ok=True)
    todo = [v for v in vs if not (vdir(d, views, v) / 'pixel/out.png').exists()]
    for n, v in enumerate(vs):
        w, h, z = guide(spec, d, views, v, A.ppm, first=n > 0); mt = json.loads((vdir(d, views, v) / 'pixel/meta.json').read_text())
        print(f"  view {v}: {w} x {h} squares of {z} px" + (f" (asked {mt['asked_px']} px: under 64 - drawn 64 tall, made smaller afterwards)" if mt['asked_px'] < 64 else ''))
    print(f'{len(vs)} view(s); to draw: {len(todo)}' + (f' (about ${len(todo) * PRICE:.2f}): views {todo}' if todo else ''))
    if todo and not A.yes: print('nothing spent - run again with --yes'); todo = []
    if todo:
        import charpipe as CP
        for v in vs:          # (in order: the first view's answer is shown to the others)
            o = vdir(d, views, v) / 'pixel'
            if (o / 'out.png').exists(): continue
            mt = json.loads((o / 'meta.json').read_text()); first = vdir(d, views, vs[0]) / 'pixel/out.png'; imgs = [o / 'in.png'] + ([Path(mt['look'])] if mt.get('look') else []) + ([first] if v != vs[0] and first.exists() else [])
            t = time.time(); c = CP.gpt((o / 'prompt.txt').read_text(), imgs, o / 'out.png', mt['size']); print(f'  drawn: view {v} (${c:.3f}, {time.time() - t:.0f} s)', flush=True)
    out = d / 'out-pixel'; out.mkdir(exist_ok=True); done = {}; cells = []
    for v in vs:
        o = vdir(d, views, v) / 'pixel'
        if not (o / 'out.png').exists(): continue
        im, info = read(d, views, v); mt = json.loads((o / 'meta.json').read_text()); name = f'sprite-{v}.png' if views else 'sprite.png'
        if mt['asked_px'] < 64:          # never asked under 64: made smaller here, from what was drawn
            import pixelsmall; im = Image.fromarray(pixelsmall.reduce(np.asarray(im), mt['asked_px'] / 64)); info['made_smaller'] = round(mt['asked_px'] / 64, 2)
        im.save(out / name); f = im.width / mt['squares'][0] if mt['asked_px'] >= 64 else im.height / 64
        done[str(v)] = {'file': name, 'size': list(im.size), 'anchor_px': [round(mt['anchor'][0] * im.width / mt['squares'][0], 1), round(mt['anchor'][1] * im.height / mt['squares'][1], 1)], **info}; cells.append(im)
        print(f"  view {v}: {im.width} x {im.height} px (asked {mt['squares'][0]} x {mt['squares'][1]}; squares drawn {info['squares_px']} px, scaled {info['scaled']})")
    if not done: return
    GP = None          # (the palette asked for, if one: what the hand put in takes its colours too)
    if A.palette:
        import pixelkit as P; gp = GP = P.load_palette(A.palette)
        for n, (e, c) in enumerate(zip(done.values(), cells)): cells[n] = Image.fromarray(P.to_palette(c, gp)); cells[n].save(out / e['file'])
        print(f'  --palette: {len(gp)} colours in {A.palette}')
    elif A.colours:          # ONE palette for every side of it, of the size asked
        import pixelkit as P; pix = np.concatenate([np.asarray(c)[np.asarray(c)[..., 3] > 0][:, :3] for c in cells]).astype(np.float32) / 255; pl = P.palette(pix, max(2, A.colours)); pr = GP = (np.clip(P.lab2rgb(pl), 0, 1) * 255).round().astype(np.uint8)
        for n, (e, c) in enumerate(zip(done.values(), cells)):
            a = np.asarray(c).copy(); mk = a[..., 3] > 0; a[mk, :3] = pr[((P.lab(a[mk, :3].astype(np.float32) / 255)[:, None, :] - pl[None]) ** 2).sum(2).argmin(1)]; cells[n] = Image.fromarray(a); cells[n].save(out / e['file'])
        print(f'  {len(pl)} colours for all {len(cells)} side(s)')
    # the views on ONE STRIP, each in the same frame, for pixeledit.py (the page built for a character's frames: a view is a frame) - a
    # speck of paper erased or a gap opened by hand there is kept in <prop>/pixel-touch.json and laid on again every time this runs
    import pixeledit
    fw, fh = max(c.width for c in cells) + 8, max(c.height for c in cells) + 8; strip = Image.new('RGBA', (fw * len(cells), fh))
    for n, ((v, e), c) in enumerate(zip(done.items(), cells)): e['in_frame'] = [(fw - c.width) // 2, fh - 4 - c.height]; strip.paste(c, (n * fw + e['in_frame'][0], e['in_frame'][1]))
    (d / 'pixel-base').mkdir(exist_ok=True); strip.save(d / 'pixel-base/views.png'); a_ = np.asarray(strip).copy(); tp = d / 'pixel-touch.json'; touch = json.loads(tp.read_text()).get('views', {}) if tp.exists() else {}; laid = aside = 0
    for kf, e in touch.items():
        i = int(kf)
        if i >= len(cells): continue
        fr = a_[:, i * fw:(i + 1) * fw]
        if e.get('outline') and abs(pixeledit.outline_of(fr) - e['outline']) > 0.02 * e['outline']: aside += 1; continue          # (drawn anew since: its edits are not laid on another drawing)
        pixeledit.lay(fr, e, [0, 0]); laid += 1
    if GP is not None and laid: a_ = P.to_palette(a_, GP)
    Image.fromarray(a_).save(out / 'views.png')
    (out / 'pixel.json').write_text(json.dumps({'px_per_m': A.ppm, 'views': done, 'frame': [fw, fh], 'animations': {'views': len(cells)}, 'origin': [0, 0], 'review': {}}, indent=1)); split(out)
    cells = [Image.open(out / e['file']).convert('RGBA') for e in done.values()]
    if laid or aside: print(f'  fixed by hand (pixeledit.py), laid on again: {laid} view(s)' + (f'; set aside - the view was drawn anew since: {aside}' if aside else ''))
    z = max(2, 360 // max(c.height for c in cells)); pv = Image.new('RGB', (sum(c.width * z + 24 for c in cells) + 24, max(c.height for c in cells) * z + 48), (58, 62, 74)); x = 24
    for c in cells: g = c.resize((c.width * z, c.height * z), Image.NEAREST); pv.paste(g, (x, pv.height - 24 - g.height), g); x += g.width + 24
    pv.save(out / 'preview.png'); print(f'{out}: {len(done)} sprite(s) at {A.ppm:g} px a metre - look at preview.png. To fix a cut-out or a pixel by hand: pixeledit.py {Path(A.spec).name}')


if __name__ == '__main__': main()
