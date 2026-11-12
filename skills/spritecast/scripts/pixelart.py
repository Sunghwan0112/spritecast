"""Pixel-art sprites of a SpriteCast character, in one command.

    python pixelart.py SPEC.json                               what it would make and what that costs - spends nothing
    python pixelart.py SPEC.json --yes                         makes it
        --px 96             the figure's height asked for (96 or 128; the sprites come out ~1.1x that - see "scale" in pixel.json)
        --clips walk,run    which animations (default: walk)
        --dirs south-east   which facings (default: all eight)
        --again NAME        draw one sheet anew (a name from the plan, e.g. walk-south-east-0 or heads-0)
        --cut ai|white      what decides whether white SHUT IN by the figure is paper (between the legs) or figure (a snowball, an eye): the AI
                            cut-out the pipeline uses for characters (the default where onnxruntime is; ~3 s a frame, once), or rules on the guide
        --no-outline        leave the figure's rim as read (by default every rim pixel that is not dark takes the outline's colour: no gaps)
        --no-face-detail    in the face, a square takes its middle colour like everywhere else (by default a small thing - a glint, a brow, a mouth -
                            that fills a good third of a square wins it)
        --face-patch        ONE face per facing: a head drawn on its own (a paid sheet), its face cut out and laid on each frame's own face
        --heads             the same head sheet's whole head on every frame (one hair for all frames; seams at the neck to mind)
        --own-heads         no head put on: each frame as GPT drew it (to compare with)
        --hand-faces        the other way to a face: no head sheet; each frame keeps its own head and the features are drawn in by hand from
                            <character>/pixel/face-edits-<clip>-<dir>.json (facefix.py). Tried as the default: the eyes did not sit the same from frame to frame
        --facemap           print each frame's head as text, to place the features by
        --follow            the head follows each frame's own face (sits best on every neck, but nods by the 1-2 px GPT drew each frame off)
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
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = Path(__file__).resolve().parent; REPO = HERE
ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--px', type=int, default=96); ap.add_argument('--clips', default='walk')
ap.add_argument('--dirs', default=''); ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', default=''); ap.add_argument('--partial', action='store_true'); ap.add_argument('--follow', action='store_true'); ap.add_argument('--debug', action='store_true'); ap.add_argument('--own-heads', action='store_true'); ap.add_argument('--heads', action='store_true'); ap.add_argument('--hand-faces', action='store_true'); ap.add_argument('--face-patch', action='store_true'); ap.add_argument('--no-face-detail', action='store_true'); ap.add_argument('--no-outline', action='store_true'); ap.add_argument('--redraw', action='store_true'); ap.add_argument('--cut', choices=['white', 'ai'], default=None); ap.add_argument('--facemap', action='store_true'); ap.add_argument('--features', action='store_true'); ap.add_argument('--no-front', action='store_true'); A = ap.parse_args()
if A.cut is None:        # the AI cut-out (the pipeline's own, BiRefNet) wherever it can run; else the rules on white, said aloud
    import importlib.util
    A.cut = 'ai' if importlib.util.find_spec('onnxruntime') else 'white'
    if A.cut == 'white': print('no onnxruntime in this Python: white shut in by the figure is sorted by rule, not by the AI cut-out (doctor.py --fix --characters)')
A.features = A.face_patch      # (the default is neither: each frame keeps the face GPT drew - asked for in whole squares in the prompt, read on the head's own grid)
sys.path.insert(0, str(HERE))
import pixelkit as P, charpipe as CP, chardepth as DEPTH, facefix as FACE   # noqa: E402
s, d = CP.load(A.spec); W = d / 'pixel'; W.mkdir(exist_ok=True); H = A.px; PRICE = 0.075
# "px" is the STANDING figure's height: how tall it is in the character's own renders (it differs with the model: a coat's hem, big boots)
_idle = d / 'render/idle-south.png'
if _idle.exists():
    _b = Image.open(_idle).convert('RGBA').getbbox()
    if _b: P.FIG = float(_b[3] - _b[1])
ALL = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
DIRS = [x for x in (A.dirs.split(',') if A.dirs else ALL) if x in ALL]; CLIPS = A.clips.split(',')
FACED = ['south', 'south-east', 'east', 'south-west', 'west']        # facings whose face shows: a head of their own, four to a sheet, always in this order
HGROUPS = [g for g in range(2) if any(x in DIRS for x in FACED[g * 4:g * 4 + 4]) and (A.face_patch or A.heads or A.follow)]     # (only the sheets a wanted facing is on)
Z = 1024 // (H * 4 // 3); CWp, CHp = 384 // Z, 1024 // Z; FOOT = CHp - CHp // 12            # a body sheet's cell in sprite pixels
ZH = 16; CH_ = 512 // ZH                                                                   # a head sheet: 32 x 32 sprite pixels a head
NCOL = 24
FACE_DETAIL = not A.no_face_detail
LOST = []; DEBUG_DIR = None; FEAT = []; SIZES = []; HROWS = {}; SIZED = {}; HEADW = {}; PITCH = []; PITCHES = {}; GAPS = {}; EDGE = {}; FINAL = {}; REVIEW = {}; SPENT = [0.0]; BASES = {}; EDITED = []; ASIDE = []
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

def held_words(clip, dr, idx):
    """what is in the hand, cell by cell (told only "where a cell does not show it, do not draw it", GPT drew a snowball in the
    hand in frames after it had been thrown)"""
    k = hold_kind(clip)
    if not k: return ''
    has = []
    for i in idx:
        hp = d / f'render/{clip}-{dr}-{i}-held.png'; has.append(hp.exists() and (np.asarray(Image.open(hp).convert('RGBA'))[..., 3] > 128).sum() > 40)
    yes = [str(n + 1) for n, h in enumerate(has) if h]; no = [str(n + 1) for n, h in enumerate(has) if not h]
    if not yes: return f"THE HANDS ARE EMPTY in every cell: the {k} has been let go and is NOT in the picture - draw nothing in or near the hands.\n"
    return (f"IN THE HAND in cell{'s' if len(yes) > 1 else ''} {', '.join(yes)}: the {k} the cell shows - draw it as pixel art too, exactly where it is and just as big, in the "
            "colour the cell has it in (NOT pure white: it must show on the white paper), with the same one-square dark outline as the figure, closed all round. "
            + (f"In cell{'s' if len(no) > 1 else ''} {', '.join(no)} the hands are EMPTY: the {k} has been let go - draw nothing in or near the hands there.\n" if no else '\n'))

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
        hp = d / f'render/{clip}-{dr}-{idx[n]}-held.png'
        if hp.exists():
            hm_ = (P.down(Image.open(hp).convert('RGBA'), H)[1] >= 0.5)[y0:y1, x0:x1]
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

TURN = {'south': 'the head facing the viewer', 'south-east': "turned three-quarters to the viewer's right", 'east': 'in profile, facing right',
        'south-west': "turned three-quarters to the viewer's left", 'west': 'in profile, facing left'}
SPOT = ['Top left', 'Top right', 'Bottom left', 'Bottom right']
def head_cell(dr, hh):
    """the render's head for a facing, as it sits in its 32 x 32 cell: colours, mask, the head's own mask - and the head's top row and
    middle column in the cell (what a frame's head is lined up with)"""
    rgb, m, hm = ren('walk', dr, 0, hh); y0, y1, x0, x1 = bbox(hm); xc = (x0 + x1) // 2; t = (CH_ - (y1 - y0 + 4)) // 2
    ys = slice(y0 - t, y0 - t + CH_); xs = slice(xc - CH_ // 2, xc + CH_ // 2)
    return rgb[ys, xs], m[ys, xs], hm[ys, xs], t, CH_ // 2

def head_sheet(g, hh):
    drs = FACED[g * 4:g * 4 + 4]; sh = np.full((2 * CH_, 2 * CH_, 3), 1.0, np.float32)
    for n, dr in enumerate(drs):
        rgb, m, hm, _, _ = head_cell(dr, hh); m = m.copy(); m[np.nonzero(hm.any(1))[0].max() + 5:] = False          # the head and 4 rows of the collar
        sh[(n // 2) * CH_:(n // 2 + 1) * CH_, (n % 2) * CH_:(n % 2 + 1) * CH_][m] = rgb[m]
    Image.fromarray((sh * 255).round().astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(W / f'heads-{g}-{H}-in.png')
    (W / f'heads-{g}-{H}-prompt.txt').write_text(
        f"Image 1 holds {len(drs)} close-ups of the head of one game character, in a 2x2 arrangement, each a 3D render seen from a game camera a "
        "little above, already reduced to LOW-RESOLUTION PIXELS: every 16x16 px square of the picture is ONE sprite pixel, on a grid that "
        "starts at the picture's top-left corner (the picture is 64 x 64 sprite pixels). " + ' '.join(f'{SPOT[n]}: {TURN[dr]}.' for n, dr in enumerate(drs)) +
        " Under each head is the top of the clothes' collar. The renders are only a rough guide: the faces are blank.\n"
        "Redraw them all as FINISHED PIXEL ART for a 1990s arcade game sprite, ON THE SAME GRID: every sprite pixel one flat 16x16 square of a "
        "single colour with its edges exactly on the grid - no anti-aliasing, no blur, no gradients, no dithering, and NOTHING smaller than one "
        "square: an eye, a highlight, a mouth are made of WHOLE squares. Each head exactly where it is and exactly as big: the same squares "
        "covered by the hair and the face, the same turn of the head.\n"
        "The face must read clearly at this tiny size, drawn as a pixel artist would: large eyes two squares wide and three tall (the eye's own "
        "dark colour with one white square of highlight, a darker lash line on top), no nose or one square of shadow, a tiny mouth of one or two "
        "squares, a slightly pinker cheek; where two eyes show, both the same height and size. The hair exactly as the illustration has it - its "
        "cut, its length, straight or curled - in three flat tones (a few lighter strands, the base, a dark edge); a one-square dark outline "
        "around the whole head. The SAME person, the same colours and the same eyes in every head.\n"
        "Image 2 is the character as a finished illustration (a turnaround: front, right side, back): the face and the hair to match - NOT its "
        "drawing style.\n"
        f"The character: {s['description']} Plain pure white background, no text, no borders, no numbers.")
    return drs


# --- reading GPT's answer -----------------------------------------------------------------------------------------------------------
PITCH_ = [8.0]       # the size of the squares GPT drew on the sheet being read (px), found by pitch_of; lines() keeps to it

def pitch_of(crops):
    """the size of the squares GPT drew on a sheet: the spacing at which grid lines LOCK best onto its figures - the most colour
    change per line, lines() being let drift only a little. (The strongest regular spacing of the changes, by Fourier, and the
    commonest run between two changes were both tried: each was 8 % out on some sheets - 7.0 for squares of 7.7 - and a sheet
    read with the wrong size comes out a different size from its neighbour.) One number for across and down: squares are square."""
    sig = []
    for c in crops[:3]: sig += [np.abs(np.diff(c, axis=1)).sum((0, 2)), np.abs(np.diff(c, axis=0)).sum((1, 2))]
    def lock(p): return float(np.mean([lines(g, p, score=True) / (g.mean() + 1e-9) for g in sig]))
    ps = np.arange(Z * 0.78, Z * 1.42, 0.15); sc = [lock(p) for p in ps]; p = ps[int(np.argmax(sc))]
    ps = np.arange(p - 0.15, p + 0.16, 0.05); sc = [lock(q) for q in ps]; return float(ps[int(np.argmax(sc))])

def lines(g, p=None, score=False):
    """grid lines along one axis: lines `p` px apart (the sheet's squares), each let drift up to 3 px from its place and no more
    than 1 px against the one before - placed where the most colour change falls on them. GPT keeps "pixels" but not a ruler's
    grid: its squares drift a pixel or two across a figure.
    (It was: "a chain of lines Z-2..Z+1 px apart with the most change on it" - and the most change is always on the MOST lines.
    At 96 px that read 7.6 px squares as 7.3; at 128 px it read 6.6 px squares as 5.2 across and up to 7 down: a quarter too
    many pixels, and heads stretched.)"""
    p = p or PITCH_[0]; n = len(g); D = 3; best = None
    for o in np.arange(0, p, 0.5):
        base = o + p * np.arange(int((n - 1 - o) / p) + 1)
        if len(base) < 2: continue
        pos = np.clip(np.round(base[:, None] + np.arange(-D, D + 1)[None]).astype(int), 0, n - 1); val = g[pos]
        dp = val.copy(); arg = np.zeros(pos.shape, int)
        for k in range(1, len(base)):
            prev = np.stack([np.concatenate([[-1e18], dp[k - 1][:-1]]), dp[k - 1], np.concatenate([dp[k - 1][1:], [-1e18]])])     # from one less, the same, one more drift
            arg[k] = prev.argmax(0) - 1; dp[k] = val[k] + prev.max(0)
        sc = dp[-1].max() / len(base)
        if best is None or sc > best[0]:
            d = int(dp[-1].argmax()); out = []
            for k in range(len(base) - 1, -1, -1): out.append(int(pos[k, d]) + 1); d = d + arg[k, d]
            best = (sc, sorted(set(out)))
    if score: return best[0] if best else 0.0
    return best[1] if best else [1, n]

def paper(low):
    """the figure: not the paper's white (joined to the border, or a gap of 3 px and more inside - 1-2 px of white stay: an eye's)"""
    white = (low.min(2) > 0.90) & (low.max(2) - low.min(2) < 0.08); l2, k = ndi.label(white)
    edge = np.unique(np.concatenate([l2[0], l2[-1], l2[:, 0], l2[:, -1]])); m = ~np.isin(l2, edge[edge > 0])
    # (white shut INSIDE the figure is left solid here - it was made see-through when 3 px and more, for the gaps between legs and
    # arms, and a snowball in the hand came back as a ring with a hole. What each such patch is - paper, an eye, a held thing,
    # GPT's own - is settled in main(), where the render can be asked.)
    for _ in range(2): m &= ~((low.min(2) > 0.7) & (low.max(2) - low.min(2) < 0.08) & ndi.binary_dilation(~m))     # the paper's grey fringe
    m &= ~((low.min(2) > 0.5) & (low.max(2) - low.min(2) < 0.05) & ndi.binary_dilation(~m))                    # (and its darker greys, one pixel deep)
    l2, k = ndi.label(m, np.ones((3, 3))); sz = ndi.sum(m, l2, np.arange(1, k + 1)); return np.isin(l2, 1 + np.nonzero(sz >= max(12, 0.02 * sz.max()))[0])      # the figure and what it holds (it may not touch the hand); specks go

def face_box(h):
    """the face in a head's picture (px): its colours in two kinds, the lighter kind's biggest patch, 2 px in from its box"""
    from scipy.cluster.vq import kmeans2
    ink = h.min(2) < 0.93
    if ink.sum() < 200: return None
    px = h[ink]; L = P.lab(px[::7]); cen, _ = kmeans2(L, 2, minit='++', seed=0, iter=20); light = int(np.argmax(cen[:, 0]))
    d = np.sqrt(((P.lab(h.reshape(-1, 3))[:, None] - cen[None]) ** 2).sum(2)); m = (d.argmin(1) == light).reshape(h.shape[:2]) & ink
    m = ndi.binary_opening(m, np.ones((3, 3))); l2, n = ndi.label(m)
    if not n: return None
    m = l2 == (1 + np.argmax(ndi.sum(m, l2, np.arange(1, n + 1)))); ys_, xs_ = np.nonzero(m)
    if len(ys_) < 150: return None
    return ys_.min() + 2, ys_.max() - 1, xs_.min() + 2, xs_.max() - 1

def read(c, top=0.0, bot=0.27, fg=None):
    """a figure read on the grid GPT drew it on -> (colours, mask, (first, last+1) of the rows that are the head's).
    THE HEAD ON ITS OWN COLUMN LINES (the user: "the face itself is drawn well - the trouble is in the pixelizing; take the face
    and pixelize it separately, carefully"). The row lines of a figure are found from each row's own changes, but its column lines
    from the changes summed down the WHOLE figure - the coat's and the legs' edges decide them, and GPT's grid drifts by a pixel
    or two between the head and the feet: over the face the lines ran through the eyes (an eye came back as one dark pixel and a
    grey one). So the head's rows - `top`..`bot` of the figure's height, from the render (0..0.27 standing; lower when something
    is held up over the head) - get column lines from themselves, the rest from the rest."""
    ink = c.min(2) < 0.93; rows_ = np.nonzero(ink.any(1))[0]; ys = np.array(lines(np.abs(np.diff(c, axis=0)).sum((1, 2)))); hgt = rows_.max() - rows_.min()
    ka = int(np.argmin(np.abs(ys - (rows_.min() + top * hgt)))) if top > 0.02 else 0; kb = max(ka + 2, int(np.argmin(np.abs(ys - (rows_.min() + bot * hgt)))))
    kb = min(kb, len(ys) - 2); ya, yb = ys[ka], ys[kb]
    gx = np.abs(np.diff(c, axis=1)).sum(2); xh, xb = lines(gx[ya:yb].sum(0)), lines(gx[:ya].sum(0) + gx[yb:].sum(0))
    # ... and within the head THE FACE decides (the user: "align before converting, to keep the detail"): the hair's many strand
    # edges outvote the few of an eye or a mouth, and a line half a square off the eyes is enough to smear them. The face = the
    # head's light kind of colour (two kinds: hair, skin - as face_of); inside its box only its own changes count, the rest of
    # the head's with a seventh of the weight (so the hair still falls on lines, where the face has nothing to say).
    fb = face_box(c[ya:yb])
    if fb is not None:
        y0_, y1_, x0_, x1_ = fb; slab = c[ya:yb]; gy = np.abs(np.diff(slab, axis=0)).sum(2); gxs = gx[ya:yb]
        wx = 0.15 * gxs.sum(0); wx[x0_:x1_] += gxs[y0_:y1_, x0_:x1_].sum(0); xh = lines(wx)
        wy = 0.15 * gy.sum(1); wy[y0_:y1_] += gy[y0_:y1_, x0_:x1_].sum(1); yh = [int(y) + ya for y in lines(wy)]; yh = [y for y in yh if ya + PITCH_[0] / 2 < y < yb - PITCH_[0] / 2]
        if len(yh) > 1: ys = np.array(list(ys[:ka + 1]) + yh + list(ys[kb:])); kb = ka + 1 + len(yh)
        fb = (y0_ + ya, y1_ + ya, x0_, x1_)
    PITCH.append((round(float(np.mean(np.diff(xh))), 2), round(float(np.mean(np.diff(ys[ka:kb + 1]))), 2), round(float(np.mean(np.diff(xb))), 2), round(float(np.mean(np.diff(np.concatenate([ys[:ka + 1], ys[kb:]])[1:] if ka else ys[kb:]))), 2)))
    cell = lambda a, b, e, f: np.median(c[a + 1:max(a + 2, b - 1), e + 1:max(e + 2, f - 1)].reshape(-1, 3), 0)
    # In the face a small thing counts: GPT draws a glint, a brow, a mouth half a square big, and the middle colour of a square is the
    # skin around them - they vanish. There a square takes its SMALLER part's colour when that part is a good third of it and
    # stands well off the rest (a square that is skin with a third of mouth becomes mouth). Only inside the face's box: anywhere
    # else it would fatten every outline.
    def fcell(a, b, e, f):
        px = c[a:b, e:f].reshape(-1, 3); med = np.median(px, 0); far = np.abs(px - med).sum(1) > 0.30
        return np.median(px[far], 0) if FACE_DETAIL and 0.34 <= far.mean() < 0.5 else cell(a, b, e, f)
    inface = lambda a, b, e, f: fb is not None and fb[0] <= (a + b) / 2 <= fb[1] and fb[2] <= (e + f) / 2 <= fb[3]
    row = lambda a, b, xs_, face: [fcell(a, b, e, f) if face and inface(a, b, e, f) else cell(a, b, e, f) for e, f in zip(xs_, xs_[1:])]
    off = int(round((xh[0] - xb[0]) / float(np.mean(np.diff(xb))))); pad = abs(off) + 1; nb, nh = len(xb) - 1, len(xh) - 1          # the head's columns against the body's: whole columns
    low = np.ones((len(ys) - 1, max(nh, nb) + 2 * pad, 3))
    for r, (a, b) in enumerate(zip(ys, ys[1:])):
        if ka <= r < kb: low[r, pad + off:pad + off + nh] = row(a, b, xh, True)
        else: low[r, pad:pad + nb] = row(a, b, xb, False)
    if fg is None: m = paper(low)
    else:
        # THE FIGURE BY THE AI CUT-OUT (the user: "can't AI fix it? ... we have the one we already use" - BiRefNet, charlib.ai_key): a
        # square is figure when most of it is, whatever its colour - white things on the white paper stay, paper shut in between
        # the legs goes, and nothing has to be guessed from how white a patch is
        al_ = np.zeros(low.shape[:2])
        for r, (a, b) in enumerate(zip(ys, ys[1:])):
            xs_, o_ = (xh, pad + off) if ka <= r < kb else (xb, pad)
            al_[r, o_:o_ + len(xs_) - 1] = [fg[a:b, e:f].mean() if b > a and f > e else 0 for e, f in zip(xs_, xs_[1:])]
        # ... but only for what the white key cannot know. Tried alone, the AI cut the gaps between the legs and kept the snowball -
        # and in one frame of forty kept a block of bare paper beside a raised arm. White joined to the sheet's edge is paper,
        # always (the key); white SHUT IN by the figure is the question, and there the AI decides, patch by patch.
        m = paper(low); wh_ = m & (low.min(2) > 0.90) & (low.max(2) - low.min(2) < 0.08); l2, k_ = ndi.label(wh_, np.ones((3, 3)))
        for q_ in range(1, k_ + 1):
            if al_[l2 == q_].mean() < 0.5: m[l2 == q_] = False
        l2, k_ = ndi.label(m, np.ones((3, 3)))
        if k_: sz = ndi.sum(m, l2, np.arange(1, k_ + 1)); m = np.isin(l2, 1 + np.nonzero(sz >= max(12, 0.02 * sz.max()))[0])
    # NO HOLES IN THE HEAD (the user found it: "the eyes go grey because of the alpha"). `paper` takes 3 px and more of white shut
    # inside the figure for a gap - between the legs, between an arm and the body - and makes it see-through. In the head that is
    # the white of an eye: at 128 px the eyes had holes in them and showed whatever was behind (grey on the preview's background).
    # Whatever the head's rows shut in stays solid, in the colour GPT gave it.
    m[ka:kb] |= ndi.binary_fill_holes(m)[ka:kb]
    y0, y1, x0, x1 = bbox(m); return low[y0:y1, x0:x1], m[y0:y1, x0:x1], (max(0, ka - y0), max(0, kb - y0))

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

def read_heads(g, drs, hh):
    a = np.asarray(Image.open(W / f'heads-{g}-{H}-out.png').convert('RGB'), np.float32) / 255; n_ = 1024 // ZH
    un, oy, ox = min(((np.roll(a, (-y, -x), (0, 1))[:1024 - ZH, :1024 - ZH].reshape(n_ - 1, ZH, n_ - 1, ZH, 3).std((1, 3)).mean(), y, x) for y in range(ZH) for x in range(ZH)))
    low = np.median(np.roll(a, (-oy, -ox), (0, 1)).reshape(n_, ZH, n_, ZH, 3)[:, 3:-3, :, 3:-3].transpose(0, 2, 1, 3, 4).reshape(n_, n_, -1, 3), 2)
    white = (low.min(2) > 0.90) & (low.max(2) - low.min(2) < 0.08); l2, _ = ndi.label(white)
    ink = ~np.isin(l2, np.setdiff1d(np.unique(np.concatenate([l2[0], l2[-1], l2[:, 0], l2[:, -1]])), [0]))
    pale = (low.min(2) > 0.78) & (low.max(2) - low.min(2) < 0.1); out = {}
    for n, dr in enumerate(drs):
        sl = (slice((n // 2) * CH_, (n // 2 + 1) * CH_), slice((n % 2) * CH_, (n % 2 + 1) * CH_)); _, _, hm, t, xc = head_cell(dr, hh)
        # the head: GPT's ink within 3 px of where the render's head is, down to the render's chin (the collar and the neck are the body's)
        m = ink[sl] & ndi.binary_dilation(hm, iterations=3); m[np.nonzero(hm.any(1))[0].max() + 2:] = False
        l3, k = ndi.label(m); m = ndi.binary_fill_holes(l3 == (1 + np.argmax(ndi.sum(m, l3, np.arange(1, k + 1))))) & ink[sl]
        for _ in range(2): m &= ~(pale[sl] & ndi.binary_dilation(~m, np.ones((3, 3))))               # paper left at the rim (an eye's white is inside)
        # (the neck is NOT taken: the user - the frame's own neck is used, only the head changes place)
        # ... nor the clothes: the collar came along with the head (the render's "head" reaches down the neck, and 3 px around it is
        # hood). Clothes: a colour nearer to what GPT drew UNDER the head (the cell's rows below it) than to what it drew in the
        # head's middle. The head ends above the first row with 3 px of clothes in it; clothes beside the face above that go too.
        L = P.lab(low[sl]).reshape(CH_, CH_, 3); bot = np.nonzero(hm.any(1))[0].max()
        core = L[ndi.binary_erosion(hm, iterations=2) & ink[sl] & (np.arange(CH_)[:, None] < bot - 3)]; under = L[ink[sl] & ~ndi.binary_dilation(hm, iterations=3) & (np.arange(CH_)[:, None] > bot - 6)]     # (beside and below the head's lower end)
        if len(core) and len(under):
            dc = np.sqrt(((L[:, :, None] - core[None, None]) ** 2).sum(3)).min(2); du = np.sqrt(((L[:, :, None] - under[None, None]) ** 2).sum(3)).min(2)
            cloth = m & (du + 8 < dc); rows = np.nonzero(cloth.sum(1) >= 3)[0]
            if len(rows): m[rows.min():] = False
            m &= ~cloth; l3, k = ndi.label(m); m = l3 == (1 + np.argmax(ndi.sum(m, l3, np.arange(1, k + 1))))
        out[dr] = (low[sl], m, t, xc)
    return out


# --- putting it together ------------------------------------------------------------------------------------------------------------
def hull(m):
    """a patch with what lies between its ends, row by row and column by column (an eye touches the fringe: no hole to fill)"""
    r = np.maximum.accumulate(m, 1) & np.maximum.accumulate(m[:, ::-1], 1)[:, ::-1]; c = np.maximum.accumulate(m, 0) & np.maximum.accumulate(m[::-1], 0)[::-1]
    return r & c

def face_of(hd, hmk):
    """the face in a head piece, whatever colour the skin is: the piece's colours fall into two kinds (hair, skin); the face is the
    kind that keeps out of the head's top third; its biggest patch, with what lies inside it (the eyes, the mouth, the cheeks).
    (It was "the colour of the bottom row's middle, spread" - and once the piece was cut at the chin that pixel was the dark
    outline: the "face" was the hair, and the features-only mode stamped hair onto hair.)"""
    from scipy.cluster.vq import kmeans2
    ys, xs = np.nonzero(hmk); L = P.lab(hd[ys, xs][:, :3] / 255.0); _, lab_ = kmeans2(L, 2, minit='++', seed=0, iter=30)
    top = ys.min() + (ys.max() - ys.min()) / 3; best = None
    for k in (0, 1):
        m = np.zeros(hmk.shape, bool); m[ys[lab_ == k], xs[lab_ == k]] = True; l2, n = ndi.label(m)
        if not n: continue
        m = l2 == (1 + np.argmax(ndi.sum(m, l2, np.arange(1, n + 1)))); yy = np.nonzero(m)[0]; sc = (yy >= top).mean() - (yy < top).mean() + 1e-3 * m.sum()
        if best is None or sc > best[0]: best = (sc, m)
    # what lies inside it: in each row, from the leftmost to the rightmost skin of that row AND of the row above and the row below.
    # (Row by row and column by column alone, an eye whose lash runs into the hair at the side had no skin left of it in its own
    # row: the front view's eye row was left out of the face and came out as bare skin - slit eyes.)
    sk = best[1]; f = np.zeros(sk.shape, bool); rows = np.nonzero(sk.any(1))[0]
    for r in rows:
        near = [q for q in (r - 1, r, r + 1) if q in rows]; xs_ = np.nonzero(sk[near].any(0))[0]; f[r, xs_.min():xs_.max() + 1] = True
    f &= hmk
    # (the hair's edge beside the jaw comes in with that; in the face's lower third anything not skin that touches the patch's rim goes -
    # there are no eyes there to lose - or it is dark specks on the frame's cheek)
    ns = f & ~sk; l2, n = ndi.label(ns, np.ones((3, 3))); rim = f & ndi.binary_dilation(~f, np.ones((3, 3))); low_ = rows.min() + 2 * (rows.max() - rows.min()) // 3
    for k in range(1, n + 1):
        c = l2 == k
        if (c & rim).any() and np.nonzero(c)[0].min() >= low_: f &= ~c
    return (f, best[1]) if f.sum() >= 12 else (hmk, hmk)

def with_head(rgba, hs, head, fixed=None, rs=None):
    """a frame with the facing's one head in place of its own, FOLLOWING THE FRAME'S OWN FACE (the user: "the head only has to follow
    the neck - detect the face's centre and follow it"). `hs`: where the render's head is on this sprite - the place to start from.
    The new head's face (skin, eyes, mouth) is slid up to 5 px around it to where it best matches what the frame has drawn there:
    its eyes on the frame's eyes, its chin on the frame's chin - so it sits on that frame's neck and collar, which were drawn for
    a head just there. Returned with it: how far that was from the render's place (dy, dx)."""
    if not hs.any(): return rgba
    hy0, hy1, hx0, hx1 = bbox(hs); hd, hmk, t, xc = head; pad = CH_; body = np.pad(rgba, ((pad, pad), (pad, pad), (0, 0))); was = body[..., 3] > 0; orig = body.copy()
    ys, xs = np.nonzero(hmk); by, bx = ys - t + hy0 + pad, xs - xc + (hx0 + hx1) // 2 + pad
    face, fskin = face_of(hd, hmk); fy, fx = np.nonzero(face); gy, gx = fy - t + hy0 + pad, fx - xc + (hx0 + hx1) // 2 + pad
    labh = P.lab(hd[fy, fx][:, :3] / 255.0); labb = P.lab(body[..., :3].reshape(-1, 3) / 255.0).reshape(body.shape[:2] + (3,))
    # Where the frame's own face is: THE MIDDLE OF ITS SKIN (the user: "before it went by the eyes - now take the median of the face's
    # skin-coloured part"). The frame's skin = what is the piece's skin colour around where the piece's face would land; the piece
    # is moved so that the median of its own skin lies on the median of that. (By matching colours pixel on pixel - in effect the
    # eyes - it was pulled about by an eye GPT drew a pixel off or half shut.)
    sy, sx = np.nonzero(fskin); ky, kx = sy - t + hy0 + pad, sx - xc + (hx0 + hx1) // 2 + pad; seed_ = np.median(P.lab(hd[sy, sx][:, :3] / 255.0), 0)
    spot = np.zeros(was.shape, bool); spot[gy, gx] = True; area = ndi.binary_dilation(spot, np.ones((3, 3)), iterations=4)
    own_ = was & area & (np.sqrt(((labb - seed_) ** 2).sum(2)) < 24); l2, k = ndi.label(own_); best = (0, 0, 0)
    if k:
        own_ = l2 == (1 + np.argmax(ndi.sum(own_, l2, np.arange(1, k + 1))))       # (its biggest patch: not an ear, not a hand)
        top_ = np.nonzero(own_.any(1))[0].min(); own_[top_ + int(np.ptp(sy)) + 1:] = False; oy_, ox_ = np.nonzero(own_)      # (the face alone, not the neck under it: as many rows as the piece's face)
        best = (0, int(np.clip(round(float(np.median(oy_) - np.median(ky))), -6, 6)), int(np.clip(round(float(np.median(ox_) - np.median(kx))), -6, 6)))
    off = best[1:]; dy, dx = off if fixed is None else fixed
    # the frame's own head goes: around where it IS (its own face's place) and around where the new one goes - cleared around the new
    # place only, the old head's far edge stayed as a dark line behind the new one. No lower than the new head reaches: under it the
    # frame's own neck and collar stay (the render's "head" runs down the neck) ...
    wide = np.pad(ndi.binary_dilation(hs, iterations=7), pad); own = np.roll(wide, off, (0, 1)); old = own | np.roll(wide, (dy, dx), (0, 1))     # (7 px: GPT's hair stands out further than the render's)
    for o in (off, (dy, dx)):       # (and 3 px around the head piece itself at both places: its hair is wider than the render's head, the corners of a 7 px diamond miss it)
        t_ = np.zeros(was.shape, bool); t_[by + o[0], bx + o[1]] = True; old |= ndi.binary_dilation(t_, np.ones((3, 3)), iterations=3)
    low_ = ndi.binary_dilation(own, np.ones((3, 3)), iterations=2); low_[:by.max() + dy + 1] = False; old[by.max() + dy + 1:] = False
    # ... but for the old HAIR hanging lower than the new (behind the neck): what is there the hair's colour and not the face's
    hair = np.zeros(hmk.shape, bool); hair[ys, xs] = True; hair[fy, fx] = False; strands = None
    if hair.any() and low_.any():
        lh = P.lab(hd[hair][:, :3] / 255.0); lh = lh[::max(1, len(lh) // 60)]; py, px_ = np.nonzero(low_ & was); lp = labb[py, px_]
        isd = (np.sqrt(((lp[:, None] - lh[None]) ** 2).sum(2)).min(1) < 16) & (np.sqrt(((lp - np.median(labh, 0)) ** 2).sum(1)) > 25)       # (16: the body's palette is not the head's)
        tail = np.zeros(was.shape, bool); tail[py[isd], px_[isd]] = True
        tail[by.max() + dy + 8:] = False
        l2, k = ndi.label(tail | old, np.ones((3, 3))); tail &= np.isin(l2, np.unique(l2[old]))      # (only what hangs from the old head)
        # In the air it goes. Over the body as the render has it (the hood behind the neck) it stays as hair - but as THIS head's hair
        # (below): left as it was it is a flat dark band under a head with strands (the user: "it comes down as plain black - the
        # hair's pattern should carry on down, vertically").
        onbody = np.roll(np.pad(rs & ~ndi.binary_dilation(hs, iterations=2), pad), (1, 0), (0, 1)) if rs is not None else np.zeros(was.shape, bool)
        old |= tail & ~onbody; strands = tail & onbody
    new = np.zeros(was.shape, bool); new[by + dy, bx + dx] = True
    keep = ndi.binary_dilation(new, iterations=1); keep[:by.max() + dy - 1] = False; keep &= ~(old & low_); keep &= ~(strands if strands is not None else False)       # the frame's own pixels right against the new head's last two rows stay (no gap opens between chin and collar)
    old[:by.min() + dy, max(0, bx.min() + dx - 6):bx.max() + dx + 7] = True                            # (and whatever of the old hair stands above the new head)
    body[old & ~keep] = 0; body[by + dy, bx + dx] = hd[ys, xs]
    if strands is not None and strands.any():
        # each column of the old hair under the head carries the new head's strands on down: it takes that column's hair pixels from
        # just above the head's bottom edge (the nearest column that has hair, where it has none), the edge itself becomes hair
        # there, and the column's last row is the head's darkest colour - the edge again, lower down. (From the head's lowest
        # pixel it was the dark edge repeated: a flat black band.)
        hy_, hx_ = np.nonzero(hair); cx_ = hx_ - xc + (hx0 + hx1) // 2 + pad + dx; cy_ = hy_ - t + hy0 + pad + dy
        dark = hd[hy_, hx_][np.argmin(hd[hy_, hx_][:, :3].sum(1).astype(int))]; ck = np.unique(cx_)
        sy, sx = np.nonzero(strands)
        for x_ in np.unique(sx):
            col = ck[np.argmin(np.abs(ck - x_))]; rows = np.sort(hy_[cx_ == col]); src = [hd[r, col - (cx_[0] - hx_[0])] for r in rows[:-1]] or [hd[rows[-1], col - (cx_[0] - hx_[0])]]
            run = np.sort(sy[sx == x_])
            if col == x_ and len(rows) > 1 and run[0] == cy_[cx_ == col].max() + 1: body[run[0] - 1, x_] = src[-1]      # the head's edge pixel, now inside the hair
            for k_, y_ in enumerate(run): body[y_, x_] = dark if k_ == len(run) - 1 else src[max(0, len(src) - len(run) + k_)]
    # the neck, one shade in every frame: under the new chin the frame's own skin is left (its old chin, a shadow, a lighter throat -
    # different in each frame, and it flickers). What is skin there (like the face) within 5 rows becomes the face's colour a little darker.
    seed = np.median(labh, 0); r0 = gy.max() + dy + 1; sl = (slice(r0, r0 + 5), slice(gx.min() + dx - 2, gx.max() + dx + 3))
    neck = (body[sl][..., 3] > 0) & (np.sqrt(((P.lab(body[sl][..., :3].reshape(-1, 3) / 255.0).reshape(body[sl].shape[:2] + (3,)) - seed) ** 2).sum(2)) < 30) & ~new[sl]
    if neck.any(): body[sl][neck] = np.append((np.clip(P.lab2rgb((seed - [5, -1, -2])[None]), 0, 1)[0] * 255).round(), 255)
    # what the old head covered and the new one does not: a hole shut in on all sides takes the colour beside it; anything open to the outside is let go
    # (filled with skin it was a line of skin beside the neck)
    al = body[..., 3] > 0; hole = ndi.binary_fill_holes(al) & ~al & was
    if hole.any(): near = ndi.distance_transform_edt(~al, return_distances=False, return_indices=True); body[hole] = body[near[0][hole], near[1][hole]]
    l2, k = ndi.label(body[..., 3] > 0, np.ones((3, 3)))                                             # bits left hanging by themselves go
    if k > 1: body[np.isin(l2, 1 + np.nonzero(ndi.sum(body[..., 3] > 0, l2, np.arange(1, k + 1)) < 8)[0])] = 0
    # what of the CLOTHES went with the old head (neither the hair's colour nor the face's, and now gone or under the new head)
    lo = labb[was]; cloth = np.zeros(was.shape, bool)
    cloth[was] = (np.sqrt(((lo[:, None] - lh[None]) ** 2).sum(2)).min(1) > 16) & (np.sqrt(((lo - np.median(labh, 0)) ** 2).sum(1)) > 30) if hair.any() else False
    # the clothes stay whole: where the new head would lie over them (it is put on the render's path, and in a frame GPT drew the
    # collar higher its chin and hair ends came down over the collar - "isn't part of the raincoat cut off?") the clothes are in
    # front, the head tucked in behind them. Only at the head's lower end: higher up it is hair over the hood, as it should be.
    front = cloth & new; front[:by.max() + dy - 5] = False
    if A.no_front: front[:] = False                  # (--no-front: as it was before, to compare with)
    body[front] = orig[front]
    LOST.append((int((cloth & (body[..., 3] == 0)).sum()), int((cloth & new & ~front).sum()), int(front.sum())))
    if DEBUG_DIR:
        im = body.copy(); im[cloth & (body[..., 3] == 0)] = (255, 0, 255, 255); im[cloth & new & ~front] = (0, 255, 255, 255); Image.fromarray(im).save(DEBUG_DIR / f'lost-{len(LOST) - 1}.png')
    return body, off

def with_features(rgba, hs, head):
    """only the FACE cut out of the facing's head piece - its skin with the eyes, nose, mouth and cheeks in it - laid on the frame's own
    face (the user: "cut just the face and put it on the original picture's face"). The frame keeps its own hair, neck and collar:
    no seam at the neck, nothing of the clothes covered, no old head to clear away. Placed by the middle of the skin (as with_head).
    The frame's own features are first painted over with its own skin (one left beside the patch would be a third eye); the patch
    goes on wherever there is figure under it - over the frame's fringe too, where the piece's face is the wider."""
    if not hs.any(): return rgba
    hy0, hy1, hx0, hx1 = bbox(hs); hd, hmk, t, xc = head; pad = CH_; body = np.pad(rgba, ((pad, pad), (pad, pad), (0, 0))); was = body[..., 3] > 0
    face, fskin = face_of(hd, hmk); fy, fx = np.nonzero(face); gy, gx = fy - t + hy0 + pad, fx - xc + (hx0 + hx1) // 2 + pad
    labb = P.lab(body[..., :3].reshape(-1, 3) / 255.0).reshape(body.shape[:2] + (3,))
    sy, sx = np.nonzero(fskin); ky, kx = sy - t + hy0 + pad, sx - xc + (hx0 + hx1) // 2 + pad; seed = np.median(P.lab(hd[sy, sx][:, :3] / 255.0), 0)
    spot = np.zeros(was.shape, bool); spot[gy, gx] = True; area = ndi.binary_dilation(spot, np.ones((3, 3)), iterations=4)
    skin = was & area & (np.sqrt(((labb - seed) ** 2).sum(2)) < 24); l2, k = ndi.label(skin)
    if not k: return rgba
    skin = l2 == (1 + np.argmax(ndi.sum(skin, l2, np.arange(1, k + 1))))
    # THE FACE ALONE on both sides (the user: "go by the face part only, without the hair"): the frame's skin runs on down the neck
    # (15-17 rows against the piece's 12), which pulled its middle 2 px low. Only as many rows from its top as the piece's face has.
    top_ = np.nonzero(skin.any(1))[0].min(); skin[top_ + int(np.ptp(sy)) + 1:] = False; oy_, ox_ = np.nonzero(skin)
    dy = int(np.clip(round(float(np.median(oy_) - np.median(ky))), -6, 6)); dx = int(np.clip(round(float(np.median(ox_) - np.median(kx))), -6, 6))
    SIZES.append(((int(np.ptp(ox_)) + 1, int(np.ptp(oy_)) + 1, int(skin.sum())), (int(np.ptp(sx)) + 1, int(np.ptp(sy)) + 1, int(fskin.sum()))))
    # (tried: from there up to 2 px to where the patch's colours best match the frame's - it slid the front view's patch 3 rows down
    # onto the fringe's pixels and the eyes came out as slits. The skin's middle alone it is.)
    ty, tx = gy + dy, gx + dx
    # the frame's own features go under its own skin: whatever lies between skin in its row OR in its column (an eye right under
    # the fringe has no skin above it), within a pixel of where the patch lands
    foot = np.zeros(was.shape, bool); foot[ty, tx] = True
    rows_ = np.maximum.accumulate(skin, 1) & np.maximum.accumulate(skin[:, ::-1], 1)[:, ::-1]; cols_ = np.maximum.accumulate(skin, 0) & np.maximum.accumulate(skin[::-1], 0)[::-1]
    own = (rows_ | cols_) & was & ndi.binary_dilation(foot, np.ones((3, 3))); v, cnt = np.unique(body[skin][:, :3], axis=0, return_counts=True); body[own & ~skin, :3] = v[cnt.argmax()]
    ok = was[ty, tx]; body[ty[ok], tx[ok]] = hd[fy[ok], fx[ok]]
    FEAT.append((int(len(fy)), int(ok.sum())))
    return body[pad:-pad, pad:-pad], (dy, dx)

def main():
    for x_ in (GAPS, EDGE, FINAL, HEADW, SIZED, PITCHES, BASES): x_.clear()
    EDITED.clear(); ASIDE.clear(); T0 = time.time()
    FEAT.clear(); LOST.clear()
    todo = [(c, dr) for c in CLIPS for dr in DIRS]
    miss = [(c, dr) for c, dr in todo if not all((d / f'render/{c}-{dr}-{i}.png').exists() for i in range(nframes(c)))]
    if miss: sys.exit(f'no renders for {miss} - run `charpipe.py render` first')
    want = {}
    for c, dr in todo + [('walk', dr) for g in HGROUPS for dr in FACED[g * 4:g * 4 + 4]]:
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
    hgroups = HGROUPS
    for g in hgroups:
        if A.again == f'heads-{g}': (W / f'heads-{g}-{H}-out.png').unlink(missing_ok=True)
        if not (W / f'heads-{g}-{H}-out.png').exists(): paid.append((f'heads-{g}', '1024x1024'))
    print(f'{len(sheets)} body sheets, {len(hgroups)} head sheets; to draw: {len(paid)}' + (f' (about ${len(paid) * PRICE:.2f}): ' + ', '.join(n for n, _ in paid) if paid else ''))
    if paid and not A.yes:
        print('nothing spent - run again with --yes')
        if not A.partial: return
        sheets = [x for x in sheets if (W / f'{x[0]}-{x[1]}-{x[2]}-{H}-out.png').exists()]; hgroups = [g for g in hgroups if (W / f'heads-{g}-{H}-out.png').exists()]; paid = []
    turn = d / 'turnaround/turn.png'; turn = turn if turn.exists() else Path(s['design']); spent = 0
    for name, size in [p for p in paid if not p[0].startswith('heads-')]:
        first = W / f'{name.rsplit("-", 1)[0]}-0-{H}-out.png'      # a later sheet is shown the animation's first one (two sheets drawn apart came out with different coats)
        t0_ = time.time(); spent += CP.gpt((W / f'{name}-{H}-prompt.txt').read_text(), [W / f'{name}-{H}-in.png', turn] + ([first] if not name.endswith('-0') and first.exists() else []), W / f'{name}-{H}-out.png', size); TIMES['draw'][name] = round(time.time() - t0_, 1); print(f'  drawn: {name} ({TIMES["draw"][name]:.0f} s)', flush=True)
    bodies = {}
    for c, dr, g, idx in sheets:
        r = read_body(c, dr, g, idx)
        if r:
            for i, x in zip(idx, r): bodies[(c, dr, i)] = x
    if not bodies: sys.exit('no sheet could be read')
    STATE.write_text(json.dumps(state)); hh = round(H * state['scale'])       # the heads at the size the bodies came back at
    heads = {}
    for g in hgroups:
        drs = head_sheet(g, hh)
        if not (W / f'heads-{g}-{H}-out.png').exists():
            spent += CP.gpt((W / f'heads-{g}-{H}-prompt.txt').read_text(), [W / f'heads-{g}-{H}-in.png', turn], W / f'heads-{g}-{H}-out.png', '1024x1024'); print(f'  drawn: heads-{g}', flush=True)
        heads.update(read_heads(g, drs, hh))
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
    if heads:
        hp, hq = pal(np.concatenate([l[m] for l, m, _, _ in heads.values()]), 13); ncol += len(hp)
        heads = {dr: (rgba(l, m, hp, hq, False), m, t, xc) for dr, (l, m, t, xc) in heads.items()}
        # a head piece put right by hand: <character>/pixel/head-edits-<facing>.json (facefix.py's format, one frame, x y in the 32 x 32 piece).
        # ONE piece per facing, so one correction serves every frame of it (GPT drew the front view's glints mirrored: cross-eyed).
        for dr, (im, _, _, _) in heads.items():
            if (W / f'head-edits-{dr}.json').exists(): FACE.apply(im, json.loads((W / f'head-edits-{dr}.json').read_text()), 0); print(f'  head piece {dr}: corrected from head-edits-{dr}.json')
        for dr, (im, _, _, _) in heads.items(): Image.fromarray(im).save(W / f'head-{dr}-{H}.png')          # (to look at: what goes on every frame of the facing)
    # every frame on one canvas, where the render has it: the sprite laid on the render (at the sprite's scale) where the two shapes
    # overlap most. (By the bottom middle of its box it shifted with every hand or foot GPT drew a pixel longer.)
    out = d / f'out-pixel{H}'; out.mkdir(exist_ok=True); K = state['scale']; strips = {}; moved = {}; fit = {}; faces = []; nofaces = []
    # The head's path: the RENDER's (a real head's, a pixel at a time), moved as a whole by what the frames' own faces say (the
    # middle of their offsets) - so it sits on the necks as GPT drew them, on the whole, and does not jump with each frame's
    # 1-2 px of drawing error. (Following each frame's own face it sat well on every neck and nodded at random.)
    steady = {}
    for c, dr in todo:
        offs = []
        for i in range(nframes(c)):
            if (c, dr, i) not in bodies or dr not in heads or A.features: break
            low, m = bodies[(c, dr, i)]; _, rm, hm = ren(c, dr, i, hh); _, oy, ox = lay(m, rm)
            r = with_head(frame((c, dr, i)), np.pad(hm, 12)[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]], heads[dr], None, np.pad(rm, 12)[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]])
            if isinstance(r, tuple): offs.append(r[1])
        if offs and not A.follow: steady[(c, dr)] = tuple(int(np.round(np.median([o[k] for o in offs]) + 1e-6)) for k in (0, 1))
    global DEBUG_DIR
    FEAT.clear(); LOST.clear(); DEBUG_DIR = (W / 'debug') if A.debug else None
    if DEBUG_DIR: DEBUG_DIR.mkdir(exist_ok=True)
    for c, dr in todo:
        fr = []
        for i in range(nframes(c)):
            if (c, dr, i) not in bodies: break
            low, m = bodies[(c, dr, i)]; im = frame((c, dr, i)); pad = 0
            _, rm, hm = ren(c, dr, i, hh); iou, oy, ox = lay(m, rm); fit.setdefault(f'{c}-{dr}', []).append(round(float(iou), 2)); prot_ = np.zeros(m.shape, bool)
            # THE REVIEW, as the illustrated pipeline has it (`redo_below`, the held thing's checks): a frame whose outline covers
            # its render's by less than "redo_below" (0.75) has another pose than the guide; a held thing the render has and
            # the drawing has not (or the other way round) is wrong whatever the outline says
            why_ = REVIEW.setdefault((c, dr, i), [])
            if iou < s['redo_below']: why_.append(f'pose {iou:.2f}')
            hold_r = s['actions'].get(c, {}).get('hold'); hp_r = d / f'render/{c}-{dr}-{i}-held.png'
            if isinstance(hold_r, dict) and hold_r.get('color') and hp_r.exists():
                hc_r = np.array([[int(hold_r['color'][k_:k_ + 2], 16) / 255 for k_ in (1, 3, 5)]]); want_ = int((P.down(Image.open(hp_r).convert('RGBA'), hh)[1] >= 0.5).sum())
                got_ = int(((im[..., 3] > 0) & (np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(hc_r)) ** 2).sum(1)).reshape(m.shape) < 30)).sum())
                if want_ >= 6 and got_ < 0.3 * want_: why_.append(f"{hold_r['kind']} missing")
                if want_ < 3 and got_ > 12:         # one lump of it, not a scatter of pixels that happen to be near its colour (a pale shade on a sleeve)
                    lk_ = (im[..., 3] > 0) & (np.sqrt(((P.lab(im[..., :3].reshape(-1, 3) / 255.0) - P.lab(hc_r)) ** 2).sum(1)).reshape(m.shape) < 30); l2k, nk = ndi.label(lk_)
                    if nk and ndi.sum(lk_, l2k, np.arange(1, nk + 1)).max() >= 14: why_.append(f"{hold_r['kind']} drawn after it was let go")
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
            if dr in heads:
                hs = np.pad(hm, 12)[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]]
                r = with_features(im, hs, heads[dr]) if A.features else with_head(im, hs, heads[dr], steady.get((c, dr)), np.pad(rm, 12)[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]])
                if isinstance(r, tuple): pad = 0 if r[0].shape == im.shape else CH_; im, off = r; moved.setdefault(f'{c}-{dr}', []).append(off)
            S_ = max(rm.shape) + 4 * CH_; cv = Image.new('RGBA', (S_, S_)); cv.alpha_composite(Image.fromarray(im), (2 * CH_ + ox - pad, 2 * CH_ + oy - pad)); fr.append(cv)
        if not fr or (len(fr) != nframes(c) and not A.partial): continue
        box = None
        for f in fr: b = f.getbbox(); box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        # THE FACE (the default): each frame keeps the head GPT drew - hair, neck and collar all of one drawing, no seam - and the eyes,
        # nose and mouth are drawn in by hand from the character's design: <character>/pixel/face-edits-<clip>-<dir>.json (facefix.py),
        # written by whoever runs this (Claude) looking at faces/<clip>-<dir>.png and the map --facemap prints. x, y: in that strip's frame.
        ob = (box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1); (W / 'faces').mkdir(exist_ok=True); ef = W / f'face-edits-{c}-{dr}.json'
        st = Image.new('RGBA', ((ob[2] - ob[0]) * len(fr), ob[3] - ob[1]))
        for n_, f in enumerate(fr): st.paste(f.crop(ob), (n_ * (ob[2] - ob[0]), 0))
        st.save(W / 'faces' / f'{c}-{dr}.png')
        if A.hand_faces and dr not in heads and ef.exists():
            e = json.loads(ef.read_text())
            for n_, f in enumerate(fr):
                a_ = np.asarray(f.crop(ob)).copy(); FACE.apply(a_, e, n_); f.paste(Image.fromarray(a_), ob[:2])
            faces.append(f'{c}-{dr}')
        elif A.hand_faces and dr in FACED: nofaces.append(f'{c}-{dr}')
        if A.facemap and dr in FACED:
            print(f'--- {c}-{dr}: frames {ob[2] - ob[0]} x {ob[3] - ob[1]} (# dark, + middle, - light, . outside)')
            for n_, f in enumerate(fr):
                a_ = np.asarray(f.crop(ob)).astype(int); L = a_[..., :3].mean(2); ys_ = np.nonzero(a_[..., 3].any(1))[0]; t_ = ys_.min(); xs_ = np.nonzero(a_[t_:t_ + 30, :, 3].any(0))[0]
                print(f'frame {n_}: columns {xs_.min()}..{xs_.max()}\n    ' + ''.join(str(x % 10) for x in range(xs_.min(), xs_.max() + 1)))
                for y in range(t_, t_ + 30): print(f'{y:3d} ' + ''.join('.' if a_[y, x, 3] == 0 else '#' if L[y, x] < 75 else '+' if L[y, x] < 150 else '-' for x in range(xs_.min(), xs_.max() + 1)))
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
    for k, v in fit.items(): print(f'  {k}: the sprites on their renders, overlap', v, '- the frames\' own faces are off the render\'s head by (dy, dx)', moved.get(k, '-'), '- head moved by', steady.get(tuple(k.split('-', 1)), 'each frame\'s own'))
    if SIZES: print('  face skin (w, h, px): each frame\'s own', [x[0] for x in SIZES], '- the piece\'s', SIZES[0][1])
    if FEAT: print('  the face patch (its pixels, those that found figure to go on) per frame:', FEAT)
    if LOST: print('  clothes pixels per frame (gone, under the new head, kept in front of it):', LOST)
    for k_, v_ in PITCHES.items(): print('  squares (head across, head down, body across, body down) px:', k_, v_)
    if FINAL: print('  held thing put in its final colour (pixels per frame):', FINAL)
    print('  outline per frame (pixels on the rim, of them not dark -> given the outline\'s colour):', EDGE)
    print('  white per frame (pixels; of them: paper made see-through, GPT\'s own white painted over, a real light part given the guide\'s colour):', GAPS)
    print('  head width per frame (px):', {k: [v[i] for i in sorted(v)] for k, v in HEADW.items()})
    print('  drawn at (x the render\'s size per frame, the correction made to the sheet, its squares in px):', SIZED, '- the character\'s scale', state['scale'])
    if EDITED: print(f'  fixed by hand (pixeledit.py), laid on again: {len(EDITED)} frames')
    if ASIDE: print('  hand edits SET ASIDE - the frame was drawn anew since:', ', '.join(ASIDE), f'(still in {W}/touch-{H}.json)')
    if faces: print('  faces drawn in from', [f'face-edits-{x}.json' for x in faces])
    if nofaces: print('  NO FACE YET for', nofaces, f'- look at {W}/faces/<name>.png (and --facemap), write {W}/face-edits-<name>.json (see facefix.py), run again')
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
