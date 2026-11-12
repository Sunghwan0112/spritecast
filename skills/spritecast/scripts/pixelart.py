"""Pixel-art sprites of a SpriteCast character, in one command.

    python pixelart.py SPEC.json                               what it would make and what that costs - spends nothing
    python pixelart.py SPEC.json --yes                         makes it
        --px 96             the figure's height asked for (96; 64 for a character designed small - about three heads tall. The sprites come out
                            ~1.1x that. Under 64 - 32, 48 - it is drawn at 64 and made smaller from that set: out-pixel<px>/)
        --clips walk,run    which animations (default: walk)
        --dirs south-east   which facings (default: all eight)
        --again NAME        draw one sheet anew (a name from the plan, e.g. walk-south-east-0)
        --cut ai|white      what decides whether white SHUT IN by the figure is paper (between the legs) or figure (a snowball, an eye): the AI
                            cut-out the pipeline uses for characters (the default where onnxruntime is; ~3 s a frame, once), or rules on the guide
        --no-outline        leave the figure's rim as read (by default every rim pixel that is not dark takes the outline's colour: no gaps)
        --no-face-detail    in the face, a square takes its middle colour like everywhere else (by default a small thing - a glint, a brow, a mouth -
                            that fills a good third of a square wins it)
        (then, by hand: pixeledit.py CHAR.json - a page to erase a speck or redraw a face frame by frame; its edits are kept and laid on again here)
        --redraw            PAID with --yes: the sheets with a frame the review marks, drawn again (twice at most), the better kept
        --partial           with --yes left off: put together what is drawn already (an animation's first frames), to look at

Needs the character's `render/` (charpipe.py render - free with a rig) and OPENAI_API_KEY for the drawing (~$0.075 a sheet).
What it does:  render -> pixelized guide (4 frames a sheet) -> GPT redraws it as pixel art -> read back on the grid GPT drew
                  (the head on its own column lines and its own palette: the face comes back as GPT drew it)
               -> every frame the render's size, laid on its render
               -> strips + preview.gif
Files: <character>/pixel/ (guides, prompts, GPT's answers - kept, so a second run pays only for what is missing)
       <character>/out-pixel<px>/ (<clip>-<facing>.png strips, preview.gif, pixel.json)"""
import argparse, json, sys, time
if __name__ != '__main__': raise ImportError('pixelart.py is a command, not a module: it BUILDS on import (a script that imported it for its reader rebuilt a character with other options). The reader is pixelgrid.py.')
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = Path(__file__).resolve().parent; REPO = HERE
ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--px', type=int, default=96); ap.add_argument('--clips', default='walk')
ap.add_argument('--dirs', default=''); ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', default=''); ap.add_argument('--partial', action='store_true'); ap.add_argument('--no-face-detail', action='store_true'); ap.add_argument('--no-outline', action='store_true'); ap.add_argument('--redraw', action='store_true'); ap.add_argument('--cut', choices=['white', 'ai'], default=None); A = ap.parse_args()
if A.cut is None:        # the AI cut-out (the pipeline's own, BiRefNet) wherever it can run; else the rules on white, said aloud
    import importlib.util
    A.cut = 'ai' if importlib.util.find_spec('onnxruntime') else 'white'
    if A.cut == 'white': print('no onnxruntime in this Python: white shut in by the figure is sorted by rule, not by the AI cut-out (doctor.py --fix --characters)')
sys.path.insert(0, str(HERE))
import pixelkit as P, charpipe as CP, chardepth as DEPTH   # noqa: E402
# NEVER LESS THAN 64 ASKED OF THE IMAGE MODEL (the user, after 32 px had been tried four ways: "everything under 64 is prompted at 64 -
# it does not go lower"): a smaller size is drawn at 64 and made smaller from that set by pixelsmall.py, when the build is done.
SMALL = A.px if A.px < 64 else None
if SMALL: print(f'--px {SMALL}: drawn at 64 (the image model is never asked for less - under 64 it does not keep to the squares), then made {SMALL} px from that set'); A.px = 64
s, d = CP.load(A.spec); W = d / 'pixel'; W.mkdir(exist_ok=True); H = A.px; PRICE = 0.075
# "px" is the STANDING figure's height: how tall it is in the character's own renders (it differs with the model: a coat's hem, big boots)
_idle = d / 'render/idle-south.png'
if _idle.exists():
    _b = Image.open(_idle).convert('RGBA').getbbox()
    if _b: P.FIG = float(_b[3] - _b[1])
ALL = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
DIRS = [x for x in (A.dirs.split(',') if A.dirs else ALL) if x in ALL]; CLIPS = A.clips.split(',')
Z = 1024 // (H * 4 // 3); CWp, CHp = 384 // Z, 1024 // Z; FOOT = CHp - CHp // 12            # a body sheet's cell in sprite pixels
CH_ = 32          # the margin a sprite is given on its canvas, px
NCOL = 24
FACE_DETAIL = not A.no_face_detail
HROWS = {}; SIZED = {}; HEADW = {}; PITCH = []; PITCHES = {}; GAPS = {}; EDGE = {}; FINAL = {}; REVIEW = {}; SPENT = [0.0]; BASES = {}; EDITED = []; ASIDE = []
TOUCH = json.loads((W / f'touch-{H}.json').read_text()) if (W / f'touch-{H}.json').exists() else {}
# how long the machine took: every sheet's drawing and every frame's cut-out, timed when it is made (kept: a later run pays for neither)
TIMES = json.loads((W / f'times-{H}.json').read_text()) if (W / f'times-{H}.json').exists() else {}; TIMES.setdefault('draw', {}); TIMES.setdefault('cut', {})
STATE = W / f'state-{H}.json'; state = json.loads(STATE.read_text()) if STATE.exists() else {}


def nframes(clip): return s['frames'] if clip == 'walk' else s['actions'][clip]['frames']

_ren = {}
def ren(clip, dr, i, h=None):
    """a render at the sprite's size: colours, the figure's mask, the head's mask (from the depth pass)"""
    h = h or H; k = (clip, dr, i, h)
    if k not in _ren:
        rgb, al = P.down(Image.open(d / f'render/{clip}-{dr}-{i}.png').convert('RGBA'), h)
        hd = np.asarray(Image.open(d / f'depth/{clip}-{dr}-{i}.png'))[..., 2] > 127
        _ren[k] = (rgb, al >= 0.5, np.asarray(Image.fromarray(hd.astype(np.float32)).resize((rgb.shape[1], rgb.shape[0]), Image.BOX)) >= 0.5)
    return _ren[k]

def bbox(m): ys, xs = np.nonzero(m); return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


# --- the guides and the words -----------------------------------------------------------------------------------------------------
def hold_kind(clip):
    h = s['actions'].get(clip, {}).get('hold'); return (h if isinstance(h, str) else h.get('kind')) if h else None

def held_seen(clip, dr, i):
    """the held thing in a frame as the camera has it: (its pixels in all, those of them not hidden by the figure, the thing with
    what is hidden made see-through). A ball in the far hand, or in a hand raised behind a big head, is there to the rig and not to
    the eye. What shows is charpipe.held_visible - the same measure the illustrated frames' prompts and checks go by (a weapon behind
    the body): the pixel path had no such thing until a ball was drawn at the chest in a frame whose render has it behind the head."""
    hp = d / f'render/{clip}-{dr}-{i}-held.png'
    if not hp.exists(): return 0, 0, None
    h = np.asarray(Image.open(hp).convert('RGBA')); on = h[..., 3] > 128
    if (d / f'render/{clip}-{dr}-{i}-body.png').exists(): seen = CP.held_visible(d, clip, dr, i)
    else: c = np.asarray(Image.open(d / f'render/{clip}-{dr}-{i}.png').convert('RGBA')).astype(int); seen = on & (c[..., 3] > 128) & (np.abs(c[..., :3] - h[..., :3].astype(int)).sum(2) < 60)
    v = h.copy(); v[~seen] = 0; return int(on.sum()), int(seen.sum()), Image.fromarray(v)

def held_words(clip, dr, idx):
    """what is in the hand, cell by cell (told only "where a cell does not show it, do not draw it", GPT drew a snowball in the
    hand in frames after it had been thrown)"""
    k = hold_kind(clip)
    if not k: return ''
    has, hid = [], []
    for i in idx:
        n_all, n_seen, _ = held_seen(clip, dr, i); has.append(n_all > 40 and n_seen >= 0.5 * n_all); hid.append(n_all > 40 and n_seen < 0.5 * n_all)
    yes = [str(n + 1) for n, h in enumerate(has) if h]; no = [str(n + 1) for n, (h, q) in enumerate(zip(has, hid)) if not h and not q]; back = [str(n + 1) for n, q in enumerate(hid) if q]
    # (a third case: the thing is there to the rig but HIDDEN to the camera - in the far hand, or in a hand raised behind a big head.
    # Told "the ball is in the hand", the image model drew it in front of the body, at the chest.)
    behind = (f"In cell{'s' if len(back) > 1 else ''} {', '.join(back)} the {k} is HIDDEN BY THE FIGURE - it is in the hand on the far side of the body, or in a hand raised behind "
              f"the head: draw that arm exactly where the cell has it, and of the {k} only the little the cell shows past the figure, if any. Do NOT draw a {k} in front of the body, "
              "at the chest or in the near hand there.\n" if back else '')
    if not yes and not back: return f"THE HANDS ARE EMPTY in every cell: the {k} has been let go and is NOT in the picture - draw nothing in or near the hands.\n"
    return ((f"IN THE HAND in cell{'s' if len(yes) > 1 else ''} {', '.join(yes)}: the {k} the cell shows - draw it as pixel art too, exactly where it is and just as big, in the "
             "colour the cell has it in (NOT pure white: it must show on the white paper), with the same one-square dark outline as the figure, closed all round.\n" if yes else '')
            + behind + (f"In cell{'s' if len(no) > 1 else ''} {', '.join(no)} the hands are EMPTY: the {k} has been let go - draw nothing in or near the hands there.\n" if no else ''))

def per_sheet(clip, dr):
    """frames to a sheet: four 48-px cells (at 96 px) - or three, or two, wider ones where a frame is too wide for that (a side view's
    stride, something held)"""
    w = max(bbox(ren(clip, dr, i)[1])[3] - bbox(ren(clip, dr, i)[1])[2] for i in range(nframes(clip)))
    return next((p for p in (4, 3, 2) if w <= 1536 // p // Z - 2), None)

def body_sheet(clip, dr, g):
    per = per_sheet(clip, dr)
    if per is None: return None
    CWp = 1536 // per // Z
    idx = list(range(g * per, min(g * per + per, nframes(clip)))); fr = [ren(clip, dr, i) for i in idx]
    bbs = [bbox(m) for _, m, _ in fr]           # each frame in the middle of its cell, its feet on the cell's ground line (where it belongs comes back from the render)
    if any(x1 - x0 > CWp - 2 or y1 - y0 > FOOT - 1 for y0, y1, x0, x1 in bbs): return None            # (something held that reaches far: a sheet's cell is too narrow for it)
    sh = np.full((CHp, 1536 // Z, 3), 1.0, np.float32)
    for n, ((rgb, m, _), (y0, y1, x0, x1)) in enumerate(zip(fr, bbs)):
        m = m[y0:y1, x0:x1]; x, y = (CWp - (x1 - x0)) // 2, FOOT - (y1 - y0); sh[y:y + m.shape[0], n * CWp + x:n * CWp + x + m.shape[1]][m] = rgb[y0:y1, x0:x1][m]
        # a held thing gets a dark line round it in the GUIDE: a white snowball on the white paper was not there for GPT to see
        # (it drew the hand empty in the frame where the ball stands clear above the head, with nothing behind it)
        seen_ = held_seen(clip, dr, idx[n])[2]          # (the line goes round what of it the camera sees: round all of it, a ball behind the head was ringed on the head)
        if seen_ is not None:
            hm_ = (P.down(seen_, H)[1] >= 0.5)[y0:y1, x0:x1]
            if hm_.shape == m.shape and hm_.any():
                ring = ndi.binary_dilation(hm_, np.ones((3, 3))) & ~hm_ & ~(m & ~hm_); cell = sh[y:y + m.shape[0], n * CWp + x:n * CWp + x + m.shape[1]]; cell[ring] = (0.25, 0.25, 0.3)
    Image.fromarray((sh * 255).round().astype(np.uint8)).resize((1536, CHp * Z), Image.NEAREST).save(W / f'{clip}-{dr}-{g}-{H}-in.png')
    words = s['actions'].get(clip, {}).get('words', 'walking')
    (W / f'{clip}-{dr}-{g}-{H}-prompt.txt').write_text(
        f"Image 1 is a SHEET of {len(idx)} frames of one {words} animation, side by side, read left to right: a 3D render of one person seen from a game "
        f"camera from above, already reduced to LOW-RESOLUTION PIXELS - every square of {Z}x{Z} px in the picture is ONE sprite pixel, on a grid "
        f"that starts at the picture's top-left corner; the figure is {H} sprite pixels tall. It is only a rough guide: its colours are muddy, "
        "it has no outline, the face is blank and dark streaks on the clothes are mistakes of the 3D model.\n"
        "Redraw EVERY cell as FINISHED PIXEL ART for an arcade game (a 1990s belt-scroll / fighting game sprite), ON THE SAME GRID: "
        f"every sprite pixel one flat {Z}x{Z} square of a single colour, its edges exactly on the grid - no anti-aliasing, no blur, no gradients, "
        "no dithering, no half-pixels, no detail smaller than one square. Decide every pixel as a pixel artist would: "
        "a dark outline one sprite pixel wide around the whole figure; one-pixel darker lines INSIDE the figure wherever one part passes in "
        "front of another (an arm in front of the body, the near leg in front of the far one, the chin over the neck); each area in two or "
        "three flat tones (light, base, shadow) in clean large clusters, light from the upper right; "
        # (tried and taken out again - the user liked the earlier drawings better: "THE FACE ... made of WHOLE squares only: each eye a
        # dark block 2 squares wide and 3 tall with ONE light square of glint ... a mouth of 2 squares ... a cheek of one pinker square".
        # It gave big doll's eyes, the same in every cell; without it GPT draws the face its own way, closer to the design.)
        "a face that reads at this size; "
        "about 16 colours in all, the SAME colours in every cell.\n"
        + ("" if clip == 'walk' else "Each cell is ONE moment of the action, and the cells are NOT all the action's big moment: draw every arm and leg "
           "exactly where THAT cell shows it. A cell that shows the figure standing with the arms down - before the move, or after it "
           "is over - is drawn standing with the arms down, not in the middle of the move.\n") +
        "Keep the sheet exactly as it is: the same cells, each figure at exactly the same position, size and pose - the same pixels "
        "covered, the legs, the stride and the arms exactly as each cell shows; nothing added between the cells, no borders, no numbers. "
        f"The same person in every cell. THE HEAD in every cell: {CP.head_words(dr) if clip == 'walk' else 'turned and tilted exactly as each cell shows it (bowed where it is bowed) - ' + CP.head_words(dr)}.\n"
        + held_words(clip, dr, idx) +
        "Image 2 is the character as a finished illustration (a turnaround: front, right side, back): the face, the hair, the outfit and "
        "the colours to match - NOT its drawing style and NOT its pose.\n"
        + ("Image 3 is the FIRST frames of this same animation, already drawn as pixel art: continue it exactly - the same person, the same "
           "face, hair, clothes, buttons, colours, outline and shading, the same size of square - but the poses of THIS sheet's cells (image 1), "
           "not the first frames' poses.\n" if g else '') +
        f"The character: {s['description']} " + (s.get('notes') or '') + " Plain pure white background, no shadow on the ground, no text.")
    return idx

# --- reading GPT's answer -----------------------------------------------------------------------------------------------------------
# (pixelgrid.py: the reading itself - shared with proppixel.py, which reads a prop the same way)
import pixelgrid as GRID   # noqa: E402
GRID.Z = Z; GRID.FACE_DETAIL = FACE_DETAIL; PITCH = GRID.PITCH; PITCH_ = GRID.PITCH_
pitch_of, lines, paper, face_box, read = GRID.pitch_of, GRID.lines, GRID.paper, GRID.face_box, GRID.read


def lay(m, rm):
    """a sprite's mask laid on a render's where the two overlap most -> (overlap, row, column)"""
    y0, y1, x0, x1 = bbox(rm); R = np.pad(rm, 12); best = (-1, 0, 0)
    for oy in range(y0 + (y1 - y0 - m.shape[0]) // 2 - 6, y0 + (y1 - y0 - m.shape[0]) // 2 + 7):
        for ox in range(x0 + (x1 - x0 - m.shape[1]) // 2 - 6, x0 + (x1 - x0 - m.shape[1]) // 2 + 7):
            w = R[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]]
            if w.shape != m.shape: continue
            sc = (w & m).sum() / (rm.sum() + m.sum() - (w & m).sum())
            if sc > best[0]: best = (sc, oy, ox)
    return best

def size_on_render(m, rm):
    """how many times the render's size a figure was drawn: the render's mask made bigger and smaller until the figure lies on it best.
    (By the height of its box a crouch GPT drew less deep, or a stick held at another angle, passed for another size.)"""
    best = (-1, 1.0)
    for r in np.arange(0.86, 1.62, 0.02):
        R = np.asarray(Image.fromarray(rm).resize((max(2, round(rm.shape[1] * r)), max(2, round(rm.shape[0] * r))), Image.NEAREST)); sc = lay(m, R)[0]
        if sc > best[0]: best = (sc, float(r))
    return best[1]

def read_body(clip, dr, g, idx):
    a = np.asarray(Image.open(W / f'{clip}-{dr}-{g}-{H}-out.png').convert('RGB'), np.float32) / 255
    # a figure = everything drawn in its cell of the sheet, not its biggest piece alone: a held thing may not touch the hand
    # (the 128 px swing's third frame came back without its umbrella, and the person shrunk to fit the render with one)
    lab_, n_ = ndi.label(ndi.binary_opening(a.min(2) < 0.93, np.ones((3, 3)))); per = per_sheet(clip, dr); cw = a.shape[1] / per; boxes = [None] * per; big = [0] * per
    for k, sl in enumerate(ndi.find_objects(lab_)):
        n_px = int((lab_[sl] == k + 1).sum())
        if n_px < 40: continue
        c_ = min(per - 1, int((sl[1].start + sl[1].stop) / 2 // cw)); b = boxes[c_]; big[c_] = max(big[c_], n_px)
        boxes[c_] = (sl[0].start, sl[0].stop, sl[1].start, sl[1].stop) if b is None else (min(b[0], sl[0].start), max(b[1], sl[0].stop), min(b[2], sl[1].start), max(b[3], sl[1].stop))
    figs = [b for b, n_px in zip(boxes, big) if b is not None and n_px > 4000]
    if len(figs) != len(idx): print(f'  {clip}-{dr}-{g}: {len(figs)} figures in the answer for {len(idx)} frames - left out (--again {clip}-{dr}-{g})'); return None
    crops = [a[max(0, y0 - 12):y1 + 12, max(0, x0 - 12):x1 + 12] for y0, y1, x0, x1 in figs]
    p0 = pitch_of(crops); PITCH_[0] = p0
    def head_rows(i):       # where the head is in the figure's height, from the render (a held thing may stand above it)
        _, m, hm = ren(clip, dr, i); y0, y1, _, _ = bbox(m)
        if not hm.any(): return 0.0, 0.0
        hy = np.nonzero(hm.any(1))[0]; return max(0.0, (hy.min() - 2 - y0) / (y1 - y0)), min(1.0, (hy.max() + 2 - y0) / (y1 - y0))
    fr_ = [head_rows(i) for i in idx]
    # EVERY FRAME THE SAME PERSON'S SIZE. GPT redraws a figure at a size of its own: about 1.1x overall (its squares are ~7.6 px for
    # 8), and a crouching figure half as big again so that it fills its cell. How big each came out is measured against the
    # render's SHAPE; the first sheet's middle value is the character's scale; every figure is brought to that (scaled before it
    # is read, so squares stay squares). (It went by the height of the figure's box: right for a walk, and it shrank the person
    # in every crouched frame of the swing.)
    fgs = [None] * len(crops)
    if A.cut == 'ai':
        import charlib as CL
        for n_c, c in enumerate(crops):
            key = W / 'cut' / f'{clip}-{dr}-{g}-{H}-{n_c}-{(W / f"{clip}-{dr}-{g}-{H}-out.png").stat().st_mtime_ns}.png'; key.parent.mkdir(exist_ok=True)
            if not key.exists():
                t0_ = time.time(); S_ = max(1024, c.shape[0] + 40, c.shape[1] + 40); big = Image.new('RGB', (S_, S_), (255, 255, 255)); oy_, ox_ = (S_ - c.shape[0]) // 2, (S_ - c.shape[1]) // 2
                big.paste(Image.fromarray((c * 255).round().astype(np.uint8)), (ox_, oy_)); mk = CL.ai_key(big)
                if mk is None: sys.exit('--cut ai needs onnxruntime in this Python (doctor.py --fix --characters)')
                Image.fromarray((mk[oy_:oy_ + c.shape[0], ox_:ox_ + c.shape[1]] * 255).astype(np.uint8)).save(key)
                TIMES['cut'][f'{clip}-{dr}-{g}-{n_c}'] = round(time.time() - t0_, 1)
            fgs[n_c] = np.asarray(Image.open(key)) > 127
    rs = [size_on_render(read(c, *f, fg=q)[1], ren(clip, dr, i)[1]) for c, f, i, q in zip(crops, fr_, idx, fgs)]
    if 'scale' not in state: state['scale'] = round(float(np.median(rs)), 4)
    # ONE correction for the whole sheet, and none for a small difference (the user: "the head grows and shrinks - is the scaling
    # at fault?" - it was). The fit against the render is good to a few per cent only (a leg drawn further out moves it), so
    # corrected frame by frame the same head came out 28 px wide in one frame and 33 in the next. GPT draws the cells of one
    # sheet at one size: the sheet's middle value is used for all of its frames.
    # (the sheet is ALWAYS brought to the character's scale. It was left alone within 6 %, to keep a sheet as drawn - and then one
    # sheet measured 1.00 was scaled up 8 % while its neighbour at 1.02 was left: frames 8 % apart in one animation, "the new
    # frames' size jumps". One measure for a whole sheet is steady to a per cent or two; that is the difference left.)
    rsheet = float(np.median(rs)); k_ = state['scale'] / rsheet if abs(state['scale'] / rsheet - 1) > 0.012 else 1.0
    SIZED[f'{clip}-{dr}-{g}'] = ([round(r, 2) for r in rs], round(k_, 3), round(p0, 2)); out = []
    # (a corrected sheet is read at the SAME square size after it is scaled: that is what changes its size - its own squares no longer
    # fit the grid then, and it is the softer for it)
    for c, f_, q in zip(crops, fr_, fgs):
        if k_ != 1.0:
            im = Image.fromarray((c * 255).round().astype(np.uint8)); c = np.asarray(im.resize((round(im.width * k_), round(im.height * k_)), Image.LANCZOS), np.float32) / 255
            if q is not None: q = np.asarray(Image.fromarray(q).resize((c.shape[1], c.shape[0]), Image.NEAREST))
        out.append(read(c, *f_, fg=q))
    for i, x in zip(idx, out): HROWS[(clip, dr, i)] = x[2]
    PITCHES[f'{clip}-{dr}-{g}'] = PITCH[-len(idx):]
    return [x[:2] for x in out]

# --- putting it together ------------------------------------------------------------------------------------------------------------
def main():
    for x_ in (GAPS, EDGE, FINAL, HEADW, SIZED, PITCHES, BASES): x_.clear()
    EDITED.clear(); ASIDE.clear(); T0 = time.time()
    todo = [(c, dr) for c in CLIPS for dr in DIRS]
    miss = [(c, dr) for c, dr in todo if not all((d / f'render/{c}-{dr}-{i}.png').exists() for i in range(nframes(c)))]
    if miss: sys.exit(f'no renders for {miss} - run `charpipe.py render` first')
    want = {}
    for c, dr in todo:
        if not all((d / f'depth/{c}-{dr}-{i}.png').exists() for i in range(nframes(c))): want.setdefault(c, []).append(dr)
    if want: print('depth pass (free):', want); DEPTH.main(A.spec, {c: sorted(set(v)) for c, v in want.items()}, (s, d))
    # the body sheets
    sheets = []; paid = []
    for c, dr in todo:
        per = per_sheet(c, dr)
        if per is None: print(f'  {c}-{dr}: a frame is too wide even for two to a sheet (something long held?) - left out'); continue
        for g in range(-(-nframes(c) // per)):
            idx = body_sheet(c, dr, g); name = f'{c}-{dr}-{g}'
            sheets.append((c, dr, g, idx))
            if A.again == name: (W / f'{name}-{H}-out.png').unlink(missing_ok=True)
            if not (W / f'{name}-{H}-out.png').exists(): paid.append((name, '1536x1024'))
    print(f'{len(sheets)} sheets; to draw: {len(paid)}' + (f' (about ${len(paid) * PRICE:.2f}): ' + ', '.join(n for n, _ in paid) if paid else ''))
    if paid and not A.yes:
        print('nothing spent - run again with --yes')
        if not A.partial: return
        sheets = [x for x in sheets if (W / f'{x[0]}-{x[1]}-{x[2]}-{H}-out.png').exists()]; paid = []
    turn = d / 'turnaround/turn.png'; turn = turn if turn.exists() else Path(s['design']); spent = 0
    for name, size in paid:
        first = W / f'{name.rsplit("-", 1)[0]}-0-{H}-out.png'      # a later sheet is shown the animation's first one (two sheets drawn apart came out with different coats)
        t0_ = time.time(); spent += CP.gpt((W / f'{name}-{H}-prompt.txt').read_text(), [W / f'{name}-{H}-in.png', turn] + ([first] if not name.endswith('-0') and first.exists() else []), W / f'{name}-{H}-out.png', size); TIMES['draw'][name] = round(time.time() - t0_, 1); print(f'  drawn: {name} ({TIMES["draw"][name]:.0f} s)', flush=True)
    bodies = {}
    for c, dr, g, idx in sheets:
        r = read_body(c, dr, g, idx)
        if r:
            for i, x in zip(idx, r): bodies[(c, dr, i)] = x
    if not bodies: sys.exit('no sheet could be read')
    STATE.write_text(json.dumps(state)); hh = round(H * state['scale'])       # the size the bodies came back at
    # one palette for the bodies, one for the heads (the face's few colours would be lost among the body's)
    def pal(pix, n):
        pl = P.palette(pix, n)
        if (pix.min(1) > 0.9).sum() >= 2: pl = np.vstack([pl, P.lab(np.ones((1, 3)))])         # white kept white (k-means greys an eye's few white pixels)
        return pl, np.clip(P.lab2rgb(pl), 0, 1)
    def rgba(low, m, pl, pr, clean=True):
        idx = P.snap(low, pl, pr); idx = P.clean(idx, m) if clean else idx
        im = np.zeros(m.shape + (4,), np.uint8); im[..., :3] = (pr[idx] * 255).round(); im[..., 3] = m * 255; return im
    notb = lambda k, m: np.concatenate([m[:HROWS[k][0]], m[HROWS[k][1]:]]); hd_ = lambda k, m: m[HROWS[k][0]:HROWS[k][1]]
    pl, pr = pal(np.concatenate([notb(k, l)[notb(k, m)] for k, (l, m) in bodies.items()]), NCOL); ncol = len(pl)
    # a held thing's colour kept in the palette (a snowball is 50 pixels among 30 000: with three animations sharing the palette its
    # pale blue was given away to a grey, and then nothing was left to turn white)
    for c_ in CLIPS:
        h_ = s['actions'].get(c_, {}).get('hold')
        if isinstance(h_, dict) and h_.get('color'):
            hc_ = np.array([[int(h_['color'][k_:k_ + 2], 16) / 255 for k_ in (1, 3, 5)]])
            pl = np.vstack([pl, P.lab(hc_), P.lab(hc_ * 0.82)]); pr = np.clip(P.lab2rgb(pl), 0, 1); ncol = len(pl)
    # (the heads' rows have a palette of their own: among the body's colours the eyes' brown and their glint were lost)
    hpl, hpr = pal(np.concatenate([hd_(k, l)[hd_(k, m)] for k, (l, m) in bodies.items()]), 13); ncol += len(hpl)
    def frame(k):
        low, m = bodies[k]; a_, b_ = HROWS[k]; im = rgba(low, m, pl, pr)
        if b_ > a_ and m[a_:b_].any(): HEADW.setdefault(f'{k[0]}-{k[1]}', {})[k[2]] = int(m[a_:b_].sum(1).max())      # the head's width, to tell: it should not change from frame to frame
        if b_ > a_ and m[a_:b_].any(): im[a_:b_] = rgba(low[a_:b_], m[a_:b_], hpl, hpr, False)
        return im
    # every frame on one canvas, where the render has it: the sprite laid on the render (at the sprite's scale) where the two shapes
    # overlap most. (By the bottom middle of its box it shifted with every hand or foot GPT drew a pixel longer.)
    out = d / f'out-pixel{H}'; out.mkdir(exist_ok=True); K = state['scale']; strips = {}; fit = {}
    for c, dr in todo:
        fr = []
        for i in range(nframes(c)):
            if (c, dr, i) not in bodies: break
            low, m = bodies[(c, dr, i)]; im = frame((c, dr, i))
            _, rm, hm = ren(c, dr, i, hh); iou, oy, ox = lay(m, rm); fit.setdefault(f'{c}-{dr}', []).append(round(float(iou), 2)); prot_ = np.zeros(m.shape, bool)
            # THE REVIEW, as the illustrated pipeline has it (`redo_below`, the held thing's checks): a frame whose outline covers
            # its render's by less than "redo_below" (0.75) has another pose than the guide; a held thing the render has and
            # the drawing has not (or the other way round) is wrong whatever the outline says
            why_ = REVIEW.setdefault((c, dr, i), [])
            if iou < s['redo_below']: why_.append(f'pose {iou:.2f}')
            hold_r = s['actions'].get(c, {}).get('hold'); hp_r = d / f'render/{c}-{dr}-{i}-held.png'
            if isinstance(hold_r, dict) and hold_r.get('color') and hp_r.exists():
                hc_r = np.array([[int(hold_r['color'][k_:k_ + 2], 16) / 255 for k_ in (1, 3, 5)]]); all_r, _, seen_r = held_seen(c, dr, i); want_ = int((P.down(seen_r, hh)[1] >= 0.5).sum())          # (what of it the camera SEES: a ball behind the head is not missing from the drawing - and one drawn in front of the body then is wrong)
                got_ = int(((im[..., 3] > 0) & (np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(hc_r)) ** 2).sum(1)).reshape(m.shape) < 30)).sum())
                if want_ >= 6 and got_ < 0.3 * want_: why_.append(f"{hold_r['kind']} missing")
                if want_ < 3 and got_ > 12:         # one lump of it, not a scatter of pixels that happen to be near its colour (a pale shade on a sleeve)
                    lk_ = (im[..., 3] > 0) & (np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(hc_r)) ** 2).sum(1)).reshape(m.shape) < 30); l2k, nk = ndi.label(lk_)
                    if nk and ndi.sum(lk_, l2k, np.arange(1, nk + 1)).max() >= 14: why_.append(f"{hold_r['kind']} drawn " + ('where the figure hides it' if all_r > 40 else 'after it was let go'))
            # WHITE THAT SHOULD NOT BE THERE, sorted out by rule - no hand, this is a skill (the user pointed at two: white between
            # the coat's collar and the chin, white between the umbrella's shaft and the face). GPT leaves paper in small gaps and
            # now and then paints white of its own (a shirt at the neck). The GUIDE it was given says what each white patch is:
            #   - mostly on the render's HEAD: an eye's white, a glint -> kept
            #   - the guide has something light and colourless there (an umbrella's shaft, a white collar) -> kept
            #   - else it is not the character's: mostly where the render has nothing -> paper, made see-through;
            #     otherwise GPT's own white on the body -> painted in the colours next to it
            # Decided per patch, not per pixel: the sprite lies on its render to a pixel or two only.
            sl_ = (slice(oy + 12, oy + 12 + m.shape[0]), slice(ox + 12, ox + 12 + m.shape[1])); g_, _, _ = ren(c, dr, i, hh)
            R_ = np.pad(rm, 12)[sl_]; Hm_ = np.pad(hm, 12)[sl_]; G_ = np.pad(g_, ((12, 12), (12, 12), (0, 0)), constant_values=1.0)[sl_]
            if R_.shape == m.shape:
                wh_ = (im[..., 3] > 0) & (im[..., :3].min(2) > 205) & (im[..., :3].max(2).astype(int) - im[..., :3].min(2) < 30)
                # (white that touches the held thing's own colour is the held thing - its highlight - whatever the render has under it:
                # where GPT drew the arm a few pixels off, a snowball's light middle lay over nothing and was taken for paper - a ring again)
                hold0_ = s['actions'].get(c, {}).get('hold'); hp0_ = d / f'render/{c}-{dr}-{i}-held.png'
                if isinstance(hold0_, dict) and hold0_.get('color') and hp0_.exists():
                    hc0_ = np.array([[int(hold0_['color'][k_:k_ + 2], 16) / 255 for k_ in (1, 3, 5)]])
                    like_ = (im[..., 3] > 0) & (np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(hc0_)) ** 2).sum(1)).reshape(m.shape) < 30)
                    # (only in a frame where the thing IS held, and only around where the render has it: in the frames after a throw the
                    # paper between the legs, greyed a little blue at its edge by the model, passed for a snowball's highlight and stayed white)
                    hk0_ = np.pad(P.down(Image.open(hp0_).convert('RGBA'), hh)[1] >= 0.5, 12)[sl_]
                    if hk0_.sum() >= 3:
                        like_ &= ndi.binary_dilation(hk0_, np.ones((3, 3)), iterations=9)
                        lw_, nw_ = ndi.label(wh_, np.ones((3, 3))); t_ = np.unique(lw_[ndi.binary_dilation(like_, np.ones((3, 3))) & wh_]); hk3_ = ndi.binary_dilation(hk0_, np.ones((3, 3)), iterations=4)
                        # ... and a patch counts as the thing's only when most of it lies where the thing is (a snowball held down by the
                        # thigh: the paper between the legs touched it and stayed white)
                        t_ = [k_ for k_ in t_ if k_ > 0 and hk3_[lw_ == k_].mean() >= 0.5]; prot_ = np.isin(lw_, t_); wh_ &= ~prot_
                hp_ = d / f'render/{c}-{dr}-{i}-held.png'; Held_ = None
                if hp_.exists(): Held_ = ndi.binary_dilation(np.pad(P.down(Image.open(hp_).convert('RGBA'), hh)[1] >= 0.5, 12)[sl_], np.ones((3, 3)), iterations=2)
                light_ = ndi.binary_dilation(R_ & (G_.min(2) > 0.68) & (G_.max(2) - G_.min(2) < 0.12), np.ones((3, 3)), iterations=2)
                l2_, n_ = ndi.label(wh_, np.ones((3, 3))); tally = [int(wh_.sum()), 0, 0]
                if A.cut == 'ai': n_ = 0          # (cut out by the AI: what is white inside the figure is the figure's)
                for k_ in range(1, n_ + 1):
                    r_ = l2_ == k_
                    onhead_ = Hm_[r_].mean() >= 0.6
                    if onhead_ and not (Held_ is not None and Held_[r_].mean() >= 0.4): continue      # an eye's white, a glint (the render's own eyes are light too: on the head only a HELD thing passes for a light part)
                    if light_[r_].mean() >= 0.4:        # a real light thing: in the GUIDE's colour for it (a shaft is silver-grey there; GPT made it paper-white, and it read as a hole)
                        gl_ = ndi.binary_dilation(r_, np.ones((3, 3)), iterations=2) & R_ & (G_.min(2) > 0.68) & (G_.max(2) - G_.min(2) < 0.12)
                        if gl_.any(): im[r_, :3] = (np.median(G_[gl_], 0) * 255).round(); tally.append(int(r_.sum()))
                        continue
                    if (~ndi.binary_dilation(R_, np.ones((3, 3))))[r_].mean() >= 0.5: im[r_, 3] = 0; tally[1] += int(r_.sum())
                    else:
                        src_ = (im[..., 3] > 0) & ~wh_
                        if src_.any(): near_ = ndi.distance_transform_edt(~src_, return_distances=False, return_indices=True); im[r_, :3] = im[near_[0][r_], near_[1][r_], :3]; tally[2] += int(r_.sum())
                GAPS.setdefault(f'{c}-{dr}', []).append((tally[0], tally[1], tally[2], sum(tally[3:])))
            # A HELD THING IN ITS REAL COLOUR (the user: "when it is drawn again, draw the snowball white"). In the guide and in GPT's
            # drawing a white thing is pale blue with a dark line round it - on white paper it would not be there to see or to
            # cut out. Here, cut out and settled, it goes back: what is the guide's colour for it, where the render has the held
            # thing, is moved to the hold's "final" colour, its shading kept at a third.
            hold_ = s['actions'].get(c, {}).get('hold'); hp_ = d / f'render/{c}-{dr}-{i}-held.png'
            if isinstance(hold_, dict) and hold_.get('final') and hp_.exists() and R_.shape == m.shape:
                hrgb_, hal_ = P.down(Image.open(hp_).convert('RGBA'), hh); hmk_ = hal_ >= 0.5
                if hmk_.sum() >= 3:
                    gcol_ = np.median(hrgb_[hmk_], 0); near_ = ndi.binary_dilation(np.pad(hmk_, 12)[sl_], np.ones((3, 3)), iterations=9)       # (wide: the sprite lies on its render to a few pixels only where GPT moved an arm, and nothing else is this colour)
                    dE_ = np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(gcol_[None])) ** 2).sum(1)).reshape(m.shape)
                    ball_ = ((im[..., 3] > 0) & near_ & (dE_ < 30)) | prot_; fin_ = np.array([int(hold_['final'][k_:k_ + 2], 16) for k_ in (1, 3, 5)], float)
                    im[ball_, :3] = np.clip(fin_ + np.minimum(0, im[ball_, :3].astype(float) - gcol_ * 255) * 0.35, 0, 255).round(); FINAL.setdefault(f'{c}-{dr}', []).append(int(ball_.sum()))
            # THE OUTLINE WHOLE (the user: "it looks as if the yellow broke through the outline"). GPT's outline is thinner than a
            # square in places, and a square that is two thirds coat comes back coat: the dark line round the figure had gaps with
            # the coat's colour in them. Every pixel on the figure's rim that is not dark takes the outline's colour - the colour
            # GPT's own outline has in this frame (the middle one of the rim's dark pixels). Not where the figure is only a pixel or
            # two thick (an umbrella's tip, a finger): there it would turn the whole thing black.
            if not A.no_outline:
                op_ = im[..., 3] > 0; rim_ = op_ & ~ndi.binary_erosion(op_, [[0, 1, 0], [1, 1, 1], [0, 1, 0]], border_value=0)
                lum_ = im[..., :3].astype(int) @ np.array([0.299, 0.587, 0.114]); dark_ = rim_ & (lum_ < 70)
                if dark_.sum() >= 8:
                    inner_ = ndi.binary_dilation(op_ & ~rim_, np.ones((3, 3))); fix_ = rim_ & ~dark_ & inner_
                    im[fix_, :3] = np.median(im[dark_][:, :3], 0).round(); EDGE.setdefault(f'{c}-{dr}', []).append((int(rim_.sum()), int(fix_.sum())))
            S_ = max(rm.shape) + 4 * CH_; cv = Image.new('RGBA', (S_, S_)); cv.alpha_composite(Image.fromarray(im), (2 * CH_ + ox, 2 * CH_ + oy)); fr.append(cv)
        if not fr or (len(fr) != nframes(c) and not A.partial): continue
        box = None
        for f in fr: b = f.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        # WHAT WAS FIXED BY HAND (pixeledit.py: a speck erased, a face redrawn) is laid on again, frame by frame - kept in
        # <character>/pixel/touch-<px>.json in the frame's render coordinates, so it lands on the same pixels whatever else this run
        # makes. A frame whose outline is no longer the one that was edited (its sheet was drawn anew) has its edits set aside.
        BASES[(c, dr)] = [f.copy() for f in fr]; tj = TOUCH.get(f'{c}-{dr}', {})
        for k_, e_ in tj.items():
            n_ = int(k_)
            if n_ >= len(fr): continue
            a_ = np.asarray(fr[n_]).copy(); was_ = int((a_[..., 3] > 0).sum())
            if e_.get('outline') and abs(was_ - e_['outline']) > 0.02 * e_['outline']: ASIDE.append(f'{c}-{dr} {n_}'); continue
            for x_, y_ in e_.get('clear', []):
                if 0 <= y_ < a_.shape[0] and 0 <= x_ < a_.shape[1]: a_[y_, x_] = 0
            for x_, y_, r_, g_, b_ in e_.get('set', []):
                if 0 <= y_ < a_.shape[0] and 0 <= x_ < a_.shape[1]: a_[y_, x_] = (r_, g_, b_, 255)
            fr[n_] = Image.fromarray(a_); EDITED.append(f'{c}-{dr} {n_}')
        box = None
        for f in fr: b = f.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        strips[(c, dr)] = (fr, box)
    for k, v in fit.items(): print(f'  {k}: the sprites on their renders, overlap', v)
    for k_, v_ in PITCHES.items(): print('  squares (head across, head down, body across, body down) px:', k_, v_)
    if FINAL: print('  held thing put in its final colour (pixels per frame):', FINAL)
    print('  outline per frame (pixels on the rim, of them not dark -> given the outline\'s colour):', EDGE)
    print('  white per frame (pixels; of them: paper made see-through, GPT\'s own white painted over, a real light part given the guide\'s colour):', GAPS)
    print('  head width per frame (px):', {k: [v[i] for i in sorted(v)] for k, v in HEADW.items()})
    print('  drawn at (x the render\'s size per frame, the correction made to the sheet, its squares in px):', SIZED, '- the character\'s scale', state['scale'])
    if EDITED: print(f'  fixed by hand (pixeledit.py), laid on again: {len(EDITED)} frames')
    if ASIDE: print('  hand edits SET ASIDE - the frame was drawn anew since:', ', '.join(ASIDE), f'(still in {W}/touch-{H}.json)')
    if not strips: sys.exit('no animation is whole yet (a sheet left out above?)')
    box = (min(b[0] for _, b in strips.values()) - 1, min(b[1] for _, b in strips.values()) - 1, max(b[2] for _, b in strips.values()) + 1, max(b[3] for _, b in strips.values()) + 1)
    fw, fh = box[2] - box[0], box[3] - box[1]
    for (c, dr), (fr, _) in strips.items():
        st = Image.new('RGBA', (fw * len(fr), fh))
        for n, f in enumerate(fr): st.paste(f.crop(box), (n * fw, 0))
        st.save(out / f'{c}-{dr}.png')
        (W / f'base-{H}').mkdir(exist_ok=True); sb = Image.new('RGBA', (fw * len(fr), fh))
        for n, f in enumerate(BASES[(c, dr)]): sb.paste(f.crop(box), (n * fw, 0))
        sb.save(W / f'base-{H}' / f'{c}-{dr}.png')
    z = max(1, 480 // fh); cols = min(4, len(strips)); rows = -(-len(strips) // cols); gif = []
    for t in range(8):
        f = Image.new('RGBA', (cols * fw, rows * fh), (58, 62, 74, 255))
        for n, (fr, _) in enumerate(strips.values()): f.alpha_composite(fr[t % len(fr)].crop(box), ((n % cols) * fw, (n // cols) * fh))
        gif.append(f.convert('RGB').resize((f.width * z, f.height * z), Image.NEAREST))
    gif[0].save(out / 'preview.gif', save_all=True, append_images=gif[1:], duration=130, loop=0)
    hs = [np.nonzero(np.asarray(fr[0])[..., 3].any(1))[0] for fr, _ in strips.values()]
    # SOMETHING THROWN. An action whose held thing is let go ("until" in its hold): the game needs to know WHEN and WHERE to put the
    # thing into the world, and a sprite of the thing by itself. From the renderer's shots of the held thing alone:
    #   "release": the first frame without it, the point it was at in the frame before (in the frame's own pixels), and the way it
    #   goes on the screen (a unit step: the figure's facing);
    #   <thing>.png: the thing alone, pixelized from the render like the guide (no GPT: it is a few pixels), outlined.
    # THE SHADOWS, AS THE PIPELINE HAS THEM (the user, of the round blobs in the first demo: "why not our shadow style? we made it in
    # 3D"). The renderer already gives every frame its own shadow - the body pressed flat onto the ground along the light
    # (render/<clip>-<facing>-<i>-s.png) - and the pipeline lays it under the sprite in (40, 30, 24) at 30 %. The same here, at the
    # sprite's size, with hard edges: shadows/<clip>-<facing>.png, one frame under each of the animation's, and where its frame
    # goes against the sprite's ("shadows" in pixel.json: offset, frame).
    SHADE = (40, 30, 24, 77); shadows = {}; (out / 'shadows').mkdir(exist_ok=True)
    for (c, dr), (fr, _) in strips.items():
        ms_ = []
        for i in range(len(fr)):
            sp_ = d / f'render/{c}-{dr}-{i}-s.png'
            if not sp_.exists(): break
            ms_.append(P.down(Image.open(sp_).convert('RGBA'), hh)[1] >= 0.5)
        if len(ms_) != len(fr) or not any(m_.any() for m_ in ms_): continue
        sy0, sy1, sx0, sx1 = bbox(np.any(ms_, 0)); st_ = Image.new('RGBA', ((sx1 - sx0) * len(ms_), sy1 - sy0))
        for n_, m_ in enumerate(ms_):
            a_ = np.zeros(m_[sy0:sy1, sx0:sx1].shape + (4,), np.uint8); a_[m_[sy0:sy1, sx0:sx1]] = SHADE; st_.paste(Image.fromarray(a_), (n_ * (sx1 - sx0), 0))
        st_.save(out / 'shadows' / f'{c}-{dr}.png'); shadows[f'{c}-{dr}'] = {'file': f'shadows/{c}-{dr}.png', 'frame': [int(sx1 - sx0), int(sy1 - sy0)], 'offset': [int(sx0 + 2 * CH_ - box[0]), int(sy0 + 2 * CH_ - box[1])]}
    releases = {}
    for (c, dr), (fr, _) in strips.items():
        hold = s['actions'].get(c, {}).get('hold')
        if not isinstance(hold, dict) or hold.get('until') is None: continue
        pts = []
        for i in range(len(fr)):
            hp = d / f'render/{c}-{dr}-{i}-held.png'; hm_ = P.down(Image.open(hp).convert('RGBA'), hh) if hp.exists() else None
            if hm_ is None or (hm_[1] >= 0.5).sum() < 3: break
            yy, xx = np.nonzero(hm_[1] >= 0.5); pts.append((float(xx.mean()) + 2 * CH_ - box[0], float(yy.mean()) + 2 * CH_ - box[1], hm_))
        if not pts or len(pts) == len(fr): continue
        # which way it goes: the way the figure faces, as the camera sees it (east is right, south is down the screen, flattened by
        # the camera's pitch). Not the hand's last move: that is the end of the wind-up, up and back.
        yaw = {'south': 0, 'south-east': 45, 'east': 90, 'north-east': 135, 'north': 180, 'north-west': -135, 'west': -90, 'south-west': -45}[dr] * np.pi / 180
        v = [round(float(np.sin(yaw)), 2), round(float(np.cos(yaw) * np.sin(s['pitch'] * np.pi / 180)), 2)]
        releases[f'{c}-{dr}'] = {'thing': hold['kind'], 'frame': len(pts), 'at': [round(pts[-1][0]), round(pts[-1][1])], 'toward': v}
        if not (out / f"{hold['kind']}.png").exists() or True:
            rgb_, al_ = pts[-1][2]; m_ = al_ >= 0.5; y0_, y1_, x0_, x1_ = bbox(m_); m_ = np.pad(m_[y0_:y1_, x0_:x1_], 1); rgb_ = np.pad(rgb_[y0_:y1_, x0_:x1_], ((1, 1), (1, 1), (0, 0)))
            pl_ = P.palette(rgb_[m_], 3) if m_.sum() > 6 else P.lab(rgb_[m_][:1]); pr_ = np.clip(P.lab2rgb(pl_), 0, 1); im_ = np.zeros(m_.shape + (4,), np.uint8)
            im_[..., :3] = (pr_[P.snap(rgb_, pl_, pr_)] * 255).round(); im_[..., 3] = m_ * 255
            if hold.get('final'):
                fin_ = np.array([int(hold['final'][k_:k_ + 2], 16) for k_ in (1, 3, 5)], float); g_ = np.median(rgb_[m_], 0) * 255
                im_[m_, :3] = np.clip(fin_ + (im_[m_, :3].astype(float) - g_) * 0.35, 0, 255).round()
            ring_ = ndi.binary_dilation(m_, [[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~m_; im_[ring_] = (34, 27, 22, 255)             # an outline round it, as the figure has
            Image.fromarray(im_).save(out / f"{hold['kind']}.png")
    if releases:
        # to look at, and to take: the thing in flight, with some go in it (the user, of the first try - a white dot drifting off at
        # 9 px a frame: "the snow has no life in it"). What makes a thrown thing read as thrown: it is FAST (a fifth of the figure's
        # height a frame), stretched along its way, leaves two fading after-images, and bursts where it lands.
        #   <thing>-fly.png   the thing stretched along the way it goes, for each facing made (one frame each, named in pixel.json)
        #   <thing>-hit.png   the burst, 4 frames
        from PIL import ImageDraw
        dark_ = (34, 27, 22, 255)
        def blob(w_, h_, ang):           # the thing as a stretched ball: white, a pale shade under, the figure's dark line round it, turned to its way
            S_ = max(w_, h_) + 6; im_ = Image.new('RGBA', (S_ * 4, S_ * 4)); dr_ = ImageDraw.Draw(im_); c_ = S_ * 2
            dr_.ellipse((c_ - w_ * 2 - 4, c_ - h_ * 2 - 4, c_ + w_ * 2 + 3, c_ + h_ * 2 + 3), fill=dark_)
            dr_.ellipse((c_ - w_ * 2, c_ - h_ * 2, c_ + w_ * 2 - 1, c_ + h_ * 2 - 1), fill=(206, 224, 244, 255)); dr_.ellipse((c_ - w_ * 2, c_ - h_ * 2, c_ + w_ * 2 - 3, c_ + h_ * 2 - 5), fill=(255, 255, 255, 255))
            im_ = im_.rotate(-ang, Image.NEAREST).resize((S_, S_), Image.NEAREST); return im_.crop(im_.getbbox())
        hit_ = Image.new('RGBA', (4 * 25, 25)); rng_ = np.random.default_rng(3); bits_ = [(rng_.uniform(0, 2 * np.pi), rng_.uniform(0.6, 1.0)) for _ in range(9)]
        for n_ in range(4):
            dr_ = ImageDraw.Draw(hit_)
            if n_ < 2: dr_.ellipse((n_ * 25 + 12 - 4 - n_ * 2, 12 - 3 - n_, n_ * 25 + 12 + 4 + n_ * 2, 12 + 3 + n_), fill=(255, 255, 255, 255), outline=dark_)
            for a_, sp_ in bits_:
                r_ = (3 + n_ * 3.2) * sp_; x_, y_ = n_ * 25 + 12 + np.cos(a_) * r_, 12 + np.sin(a_) * r_ * 0.7 + 0.5 * n_ * n_; q_ = 2 if n_ < 2 else 1
                dr_.rectangle((int(x_), int(y_), int(x_) + q_ - 1, int(y_) + q_ - 1), fill=(255, 255, 255, 255) if n_ < 3 else (206, 224, 244, 255))
        fly_ = {}
        for k_, r_ in releases.items():
            c_, dr_ = k_.split('-', 1); ang_ = float(np.degrees(np.arctan2(r_['toward'][1] * 0.3 * 0.25 * fh - 0.06 * fh, r_['toward'][0] * 0.25 * fh))); fly_[dr_] = blob(16, 9, ang_)
            # THROWN UP AND OUT (the user: "let it go more upward - it goes down too much"): over the ground it goes the way the figure
            # faces (which on this camera is partly DOWN the screen), and it has a height of its own on top of that - up at "up" px a
            # frame, pulled back by "gravity" - until it is as far under the hand as the hand is above the feet.
            # (the user of the arc: "the floor is too far down, and faster at the start". Faster: a quarter of the frame's height a frame.
            # The floor: on this camera ground further south IS lower on the screen - by the camera's pitch - and a long throw to the
            # south-east ended a figure's height under the feet. "ground_slope" says how much of that the flight shows: 1 = as the
            # camera has it (a game drawn on this camera's ground), 0 = a flat line at the feet (a side-on game). 1 it is - the user asked which is right by the numbers: ground d further south
            # is d x sin(pitch) lower on the screen, so the facing's step IS "toward" - and the demo has the ground drawn under it, so that
            # a landing far down the screen reads as far away, not as fallen through the floor.)
            r_['speed'] = round(0.25 * fh, 1); r_['up'] = round(0.09 * fh, 1); r_['gravity'] = round(0.03 * fh, 2); r_['ground_slope'] = 1.0
            fr_, _ = strips[(c_, dr_)]; g_ = []; sp_ = r_['speed']
            feet_ = int(np.nonzero(np.asarray(fr_[0].crop(box))[..., 3].any(1))[0].max()); drop_ = feet_ - r_['at'][1]; r_['hand_above_feet'] = int(drop_)
            hgt_ = lambda n_: r_['up'] * n_ - 0.5 * r_['gravity'] * n_ * n_
            land_ = next(n_ for n_ in range(1, 80) if hgt_(n_) <= -drop_)
            gy_ = r_['toward'][1] * r_['ground_slope']
            # the picture big enough for the whole flight, whichever way it goes (to the left, up the screen for a throw to the north)
            px_ = [r_['at'][0] + r_['toward'][0] * sp_ * n_ for n_ in range(land_ + 1)]; py_ = [r_['at'][1] + gy_ * sp_ * n_ - hgt_(n_) for n_ in range(land_ + 1)]; gyy_ = [feet_ + gy_ * sp_ * n_ for n_ in range(land_ + 1)]
            X0 = int(max(fw * 0.6, 60 - min(px_))); top_ = int(max(40, 30 - min(py_), 90 - min(gyy_)))
            Wd = int(X0 + max(fw, max(px_) + 70)); Hd = int(top_ + max(feet_, max(gyy_)) + 44); z_ = max(1, 560 // Hd)
            # THE GROUND UNDER IT: blocks in the same camera and the same pixel style (the user: "lay iso blocks under it"). A square
            # tile set cornerwise to this camera is a diamond twice as wide as it is high (sin 30 = 1/2); each block has a top in one
            # of two tones, a dark line round it and a darker front. Drawn back to front. The figure's feet stand on a block's middle.
            a0_ = np.asarray(fr_[0].crop(box))[..., 3]; fx_ = float(np.nonzero(a0_[max(0, feet_ - 3):feet_ + 1].any(0))[0].mean()); G0 = (X0 + fx_, top_ + feet_ - 2)
            hw_, hh_, th_k = 22, 11, 7; floor_ = Image.new('RGBA', (Wd, Hd), (58, 62, 74, 255)); fd_ = ImageDraw.Draw(floor_); tiles_ = []
            for i_ in range(-14, 30):
                for j_ in range(-14, 30):
                    cx_, cy_ = G0[0] + (i_ - j_) * hw_, G0[1] + (i_ + j_) * hh_
                    if -hw_ < cx_ < Wd + hw_ and min(G0[1] - 7 * hh_, top_ + min(gyy_) - 5 * hh_) <= cy_ < Hd - th_k - 6: tiles_.append((cy_, cx_, (i_ + j_) % 2))      # (the ground runs on behind the figure: its shadow falls up and away)
            for cy_, cx_, odd_ in sorted(tiles_):
                top_c = (126, 142, 164, 255) if odd_ else (112, 128, 152, 255)
                fd_.polygon([(cx_ - hw_, cy_), (cx_, cy_ + hh_), (cx_, cy_ + hh_ + th_k), (cx_ - hw_, cy_ + th_k)], fill=(74, 86, 110, 255), outline=(34, 38, 52, 255))      # the front, left
                fd_.polygon([(cx_ + hw_, cy_), (cx_, cy_ + hh_), (cx_, cy_ + hh_ + th_k), (cx_ + hw_, cy_ + th_k)], fill=(60, 70, 92, 255), outline=(34, 38, 52, 255))      # the front, right
                fd_.polygon([(cx_, cy_ - hh_), (cx_ + hw_, cy_), (cx_, cy_ + hh_), (cx_ - hw_, cy_)], fill=top_c, outline=(34, 38, 52, 255))
                fd_.line([(cx_ - hw_ + 4, cy_ - 1), (cx_ - 1, cy_ - hh_ + 2)], fill=(150, 166, 186, 255))                                                               # a lit edge
            gnd_ = lambda n_: (X0 + r_['at'][0] + r_['toward'][0] * sp_ * n_, top_ + feet_ - 2 + gy_ * sp_ * n_)
            pos_ = lambda n_: (X0 + r_['at'][0] + r_['toward'][0] * sp_ * n_, top_ + r_['at'][1] + gy_ * sp_ * n_ - hgt_(n_))
            for t_ in range(len(fr_) + land_ + 2):
                f_ = floor_.copy(); n_ = t_ - r_['frame'] + 1; sh_ = shadows.get(k_)
                if sh_:                 # the figure's own 3D shadow for this frame
                    ss_ = Image.open(out / sh_['file']); q_ = min(t_, len(fr_) - 1); f_.alpha_composite(ss_.crop((q_ * sh_['frame'][0], 0, (q_ + 1) * sh_['frame'][0], sh_['frame'][1])), (X0 + sh_['offset'][0], top_ + sh_['offset'][1]))
                if 1 <= n_ < land_:
                    # the thing's shadow, by the same light: a point h above the ground is shadowed (-0.42 h, -0.78 h) away over the ground
                    # (the renderer's SHADOW; mirrored for a light from the left), which this camera shows as (-0.42 h, -0.78 h sin pitch);
                    # h is the screen height over cos(pitch). A flat ellipse, the pipeline's shadow colour.
                    sx_, sy_ = gnd_(n_); h_ = hgt_(n_) + drop_; h_ = max(0.0, h_) / np.cos(s['pitch'] * np.pi / 180); lx_ = 0.42 if s['light'] == 'left' else -0.42
                    sx_ += lx_ * h_; sy_ += -0.78 * h_ * np.sin(s['pitch'] * np.pi / 180); o_ = Image.new('RGBA', f_.size); ImageDraw.Draw(o_).ellipse((sx_ - 7, sy_ - 3, sx_ + 7, sy_ + 3), fill=SHADE); f_.alpha_composite(o_)
                f_.alpha_composite(fr_[min(t_, len(fr_) - 1)].crop(box), (X0, top_))
                if 1 <= n_ < land_:
                    for back_, small_ in ((2, 6), (1, 10)):                           # after-images: where it was, smaller
                        if n_ - back_ >= 1: x_, y_ = pos_(n_ - back_ * 0.5); b_ = blob(small_, max(3, small_ * 6 // 10), ang_); f_.alpha_composite(b_, (int(x_ - b_.width / 2), int(y_ - b_.height / 2)))
                    x_, y_ = pos_(n_); b_ = fly_[dr_]; f_.alpha_composite(b_, (int(x_ - b_.width / 2), int(y_ - b_.height / 2)))
                elif land_ <= n_ < land_ + 4:
                    x_, y_ = pos_(land_); f_.alpha_composite(hit_.crop(((n_ - land_) * 25, 0, (n_ - land_ + 1) * 25, 25)), (int(x_ - 12), int(y_ - 12)))
                g_.append(f_.convert('RGB').resize((f_.width * z_, f_.height * z_), Image.NEAREST))
            g_[0].save(out / f'{k_}-flying.gif', save_all=True, append_images=g_[1:], duration=90, loop=0)
        th_ = next(iter(releases.values()))['thing']; hit_.save(out / f'{th_}-hit.png')
        st_ = Image.new('RGBA', (sum(b_.width + 2 for b_ in fly_.values()), max(b_.height for b_ in fly_.values()))); x_ = 0
        for dr_, b_ in fly_.items(): st_.alpha_composite(b_, (x_, 0)); releases[f'{next(k for k in releases if k.endswith(dr_))}']['fly'] = [x_, 0, b_.width, b_.height]; x_ += b_.width + 2
        st_.save(out / f'{th_}-fly.png')
        print('  let go:', releases)
    (out / 'pixel.json').write_text(json.dumps({'asked_px': H, 'scale': K, 'figure_px': int(np.median([h.max() - h.min() + 1 for h in hs])), 'frame': [fw, fh], 'colours': ncol,
                                                'animations': {f'{c}-{dr}': len(fr) for (c, dr), (fr, _) in strips.items()}, 'origin': [int(box[0]), int(box[1])], 'release': releases, 'shadows': shadows, 'shadow_colour': [40, 30, 24], 'shadow_alpha': 0.3}, indent=1))
    # the review: which frames to look at, a picture of them beside their guides, the sheets a redraw would draw again
    bad = {k: v for k, v in REVIEW.items() if v and (k[0], k[1]) in strips}; rv = {}
    for (c, dr, i), v in sorted(bad.items()): rv.setdefault(f'{c}-{dr}', {})[str(i)] = v
    if bad:
        cells = []
        for (c, dr, i) in sorted(bad):
            g_ = Image.open(W / f'{c}-{dr}-{i // per_sheet(c, dr)}-{H}-in.png').convert('RGB'); cw_ = g_.width // per_sheet(c, dr); n_ = i % per_sheet(c, dr)
            gd = g_.crop((n_ * cw_, 0, (n_ + 1) * cw_, g_.height)); gd = gd.resize((max(1, gd.width * fh // gd.height), fh), Image.NEAREST)
            sp = Image.new('RGBA', (fw, fh), (58, 62, 74, 255)); sp.alpha_composite(strips[(c, dr)][0][i].crop(box)); cells.append((gd, sp.convert('RGB')))
        sh_ = Image.new('RGB', (sum(a.width + b.width + 8 for a, b in cells), fh), (20, 20, 24)); x_ = 0
        for a, b in cells: sh_.paste(a, (x_, 0)); sh_.paste(b, (x_ + a.width, 0)); x_ += a.width + b.width + 8
        sh_.resize((sh_.width * 2, sh_.height * 2), Image.NEAREST).save(out / 'review.png')
        print(f'  REVIEW: {len(bad)} of {sum(len(fr) for fr, _ in strips.values())} frames to look at (review.png: each beside its guide) -', '; '.join(f"{k} " + ', '.join(f"{i}: {'/'.join(v)}" for i, v in e.items()) for k, e in rv.items()))
    elif (out / 'review.png').exists(): (out / 'review.png').unlink()
    # HOW IT WAS MADE: the machine's time against the hand's work, per animation - the drawing (timed; a sheet drawn before times were
    # kept is put at what the sheets drawn one after another took, and said to be "about"), the AI cut-out (timed when made; None
    # for frames cut before times were kept), and what pixeledit.py changed: frames, pixels, and the time at it where the editor kept it.
    (W / f'times-{H}.json').write_text(json.dumps(TIMES)); made = {}; ms = sorted((W / f'{x[0]}-{x[1]}-{x[2]}-{H}-out.png').stat().st_mtime for x in sheets)
    guess = float(np.median(list(TIMES['draw'].values()) or [b - a for a, b in zip(ms, ms[1:]) if b - a < 90] or [30]))
    hand_s = json.loads((W / f'touch-{H}-time.json').read_text()) if (W / f'touch-{H}-time.json').exists() else {}
    for (c, dr), (fr, _) in strips.items():
        n = f'{c}-{dr}'; m = made[n] = {'frames': len(fr), 'sheets': 0, 'draw_s': 0.0, 'cut_s': None, 'hand_frames': 0, 'hand_px': 0, 'hand_s': hand_s.get(n), 'px': int(sum((np.asarray(f)[..., 3] > 0).sum() for f in fr))}
        for x in sheets:
            if (x[0], x[1]) != (c, dr): continue
            k = f'{n}-{x[2]}'; m['sheets'] += 1; m['draw_s'] = round(m['draw_s'] + TIMES['draw'].get(k, guess), 1)
            if k not in TIMES['draw']: m['estimated'] = True
            cs = [TIMES['cut'][f'{k}-{i}'] for i in range(len(x[3])) if f'{k}-{i}' in TIMES['cut']]
            if cs: m['cut_s'] = round((m['cut_s'] or 0) + sum(cs), 1)
        for e in EDITED:
            if e.rsplit(' ', 1)[0] == n: t = TOUCH[n][e.rsplit(' ', 1)[1]]; m['hand_frames'] += 1; m['hand_px'] += len(t.get('set', [])) + len(t.get('clear', []))
    dur = lambda v: 'not timed' if v is None else f'{v:.0f} s' if v < 90 else f'{v / 60:.1f} min'
    tot = lambda k: (lambda v: sum(v) if v else None)([m[k] for m in made.values() if m[k] is not None])
    print(f"  HOW IT WAS MADE: AI drawing {tot('sheets')} sheets {dur(tot('draw_s'))}" + (' (about: from when the sheets were written)' if any(m.get('estimated') for m in made.values()) else '')
          + f", AI cut-out {dur(tot('cut_s'))}, this run {time.time() - T0:.0f} s; by hand {tot('hand_frames')} of {tot('frames')} frames, {tot('hand_px')} pixels = {100 * tot('hand_px') / tot('px'):.2f} % of the sprites' pixels, {dur(tot('hand_s'))}")
    j_ = json.loads((out / 'pixel.json').read_text()); j_['review'] = rv; j_['made'] = made; (out / 'pixel.json').write_text(json.dumps(j_, indent=1))
    SPENT[0] += spent
    print(f'{out}: {len(strips)} animations, frame {fw}x{fh}, the figure ~{int(np.median([h.max() - h.min() + 1 for h in hs]))} px, {ncol} colours' + (f', ${spent:.2f} spent' if spent else ', nothing spent') + ' - look at preview.gif')
    if SMALL: import pixelsmall; pixelsmall.main(A.spec, 64, SMALL)


def sheets_of(review):
    """{sheet name: (frames wrong for the held thing, lowest overlap, mean overlap)} for the sheets with a frame to look at"""
    out = {}
    for (c, dr, i), v in review.items():
        if not v: continue
        out.setdefault(f'{c}-{dr}-{i // per_sheet(c, dr)}', None)
    for name in out:
        c, rest = name.split('-', 1); dr, g = rest.rsplit('-', 1); per = per_sheet(c, dr); fr = [(k, v) for k, v in review.items() if k[0] == c and k[1] == dr and k[2] // per == int(g)]
        ov = [float(x.split()[1]) for _, v in fr for x in v if x.startswith('pose')]
        out[name] = (sum(any(not x.startswith('pose') for x in v) for _, v in fr), min(ov) if ov else 1.0)
    return out


REVIEW.clear(); main()
if A.redraw:
    # the sheets with a frame to look at, drawn again (twice at most each), the better drawing kept: fewer frames with the held thing
    # wrong first, then the higher lowest overlap - as `charpipe.py redraw` does for the illustrated frames
    first = sheets_of(REVIEW); tries = lambda n: len(list(W.glob(f'{n}-{H}-out.try*.png')))
    todo = [n for n in first if tries(n) < 2 and (W / f'{n}-{H}-out.png').exists()]
    if not todo: print('redraw: nothing to draw again' + (' (every sheet with a frame to look at has been tried twice)' if first else ''))
    elif not A.yes: print(f'redraw: {len(todo)} sheets - {", ".join(todo)} - about ${len(todo) * PRICE:.2f}; nothing spent - add --yes')
    else:
        for n in todo: (W / f'{n}-{H}-out.png').replace(W / f'{n}-{H}-out.try{tries(n) + 1}.png')
        REVIEW.clear(); main(); second = sheets_of(REVIEW); back = 0
        for n in todo:
            old, new = first[n], second.get(n, (0, 1.0)); better = (new[0], -new[1]) <= (old[0], -old[1])
            print(f'redraw: {n}: held thing wrong in {old[0]} -> {new[0]} frames, lowest overlap {old[1]:.2f} -> {new[1]:.2f}' + ('' if better else ' - worse: the earlier drawing kept'))
            if not better:
                live = W / f'{n}-{H}-out.png'; prev = sorted(W.glob(f'{n}-{H}-out.try*.png'))[-1]; worse = W / f'{n}-{H}-out.worse{tries(n)}.png'
                live.replace(worse); prev.replace(live); worse.replace(prev); back += 1          # (the try's name keeps counting the tries)
        if back: REVIEW.clear(); main()
        print(f'redraw: ${SPENT[0]:.2f} spent')
