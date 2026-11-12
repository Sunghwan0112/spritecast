"""pixelgrid: pixel art an image model drew, read back on the grid it drew it on - the part of pixelart.py that does not know what the
picture is of, so a prop (proppixel.py) is read the same way as a character's frame.

The image model keeps "pixels" but not a ruler's grid: its squares are a size of its own (asked for 8 px it draws 7.4 to 10.8) and
drift a pixel or two across a figure. pitch_of finds the squares' size on a sheet; lines places grid lines that far apart, each let
drift a little, where the most colour change falls on them; read takes each square's middle colour, the head's rows on lines of their
own (top..bot of the figure's height: 0, 0 for a thing with no head).

Set before reading:  Z  the squares' size the guide asked for (pitch_of looks from 0.78 to 1.42 of it);  FACE_DETAIL  in the face a
small part that fills a good third of a square wins it;  PITCH_[0]  the size pitch_of found, which lines() then keeps to."""
import numpy as np
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
import pixelkit as P

Z = 8; FACE_DETAIL = True


def bbox(m): ys, xs = np.nonzero(m); return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

PITCH_XY = [None, None]   # the squares' size across and down, when a sheet's squares are not square (proppixel.py sets it; None: PITCH_[0] for both)
PITCH = []           # what read() found, per figure: the squares' size (head across, head down, body across, body down) px

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
    p = p or PITCH_[0]; n = len(g); D = 3; best = None; offs = np.arange(0, p, 0.5); cnt = ((n - 1 - offs) / p).astype(int) + 1; got = {}
    # (every starting place of the first line is tried; those with the same number of lines are worked out together - the same sums,
    # one pass of the chain for all of them instead of one each: a build spent most of its time here)
    for L in np.unique(cnt):
        if L < 2: continue
        ix = np.nonzero(cnt == L)[0]; base = offs[ix][:, None] + p * np.arange(L)[None]
        pos = np.clip(np.round(base[:, :, None] + np.arange(-D, D + 1)[None, None]).astype(int), 0, n - 1); val = g[pos]
        dp = val.copy(); arg = np.zeros(pos.shape, int); pad = np.full((len(ix), 2 * D + 3), -1e18)
        for k in range(1, L):
            pad[:, 1:-1] = dp[:, k - 1]; prev = np.stack([pad[:, :-2], pad[:, 1:-1], pad[:, 2:]])     # from one less, the same, one more drift
            arg[:, k] = prev.argmax(0) - 1; dp[:, k] = val[:, k] + prev.max(0)
        for j, i in enumerate(ix): got[int(i)] = (dp[j, -1].max() / L, pos[j], arg[j], dp[j, -1])
    for i in sorted(got):
        sc, pos, arg, last = got[i]
        if best is None or sc > best[0]: best = (sc, pos, arg, last)
    if best is None: return 0.0 if score else [1, n]
    if score: return best[0]
    sc, pos, arg, last = best; d = int(last.argmax()); out = []
    for k in range(len(pos) - 1, -1, -1): out.append(int(pos[k, d]) + 1); d = d + arg[k, d]
    return sorted(set(out))

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
    ink = c.min(2) < 0.93; rows_ = np.nonzero(ink.any(1))[0]; ys = np.array(lines(np.abs(np.diff(c, axis=0)).sum((1, 2)), PITCH_XY[1])); hgt = rows_.max() - rows_.min()
    ka = int(np.argmin(np.abs(ys - (rows_.min() + top * hgt)))) if top > 0.02 else 0; kb = max(ka + 2, int(np.argmin(np.abs(ys - (rows_.min() + bot * hgt)))))
    kb = min(kb, len(ys) - 2); ya, yb = ys[ka], ys[kb]
    gx = np.abs(np.diff(c, axis=1)).sum(2); xh, xb = lines(gx[ya:yb].sum(0), PITCH_XY[0]), lines(gx[:ya].sum(0) + gx[yb:].sum(0), PITCH_XY[0])
    # ... and within the head THE FACE decides (the user: "align before converting, to keep the detail"): the hair's many strand
    # edges outvote the few of an eye or a mouth, and a line half a square off the eyes is enough to smear them. The face = the
    # head's light kind of colour (two kinds: hair, skin - as face_of); inside its box only its own changes count, the rest of
    # the head's with a seventh of the weight (so the hair still falls on lines, where the face has nothing to say).
    fb = face_box(c[ya:yb])
    if fb is not None:
        y0_, y1_, x0_, x1_ = fb; slab = c[ya:yb]; gy = np.abs(np.diff(slab, axis=0)).sum(2); gxs = gx[ya:yb]
        wx = 0.15 * gxs.sum(0); wx[x0_:x1_] += gxs[y0_:y1_, x0_:x1_].sum(0); xh = lines(wx, PITCH_XY[0])
        wy = 0.15 * gy.sum(1); wy[y0_:y1_] += gy[y0_:y1_, x0_:x1_].sum(1); yh = [int(y) + ya for y in lines(wy, PITCH_XY[1])]; yh = [y for y in yh if ya + PITCH_[0] / 2 < y < yb - PITCH_[0] / 2]
        if len(yh) > 1: ys = np.array(list(ys[:ka + 1]) + yh + list(ys[kb:])); kb = ka + 1 + len(yh)
        fb = (y0_ + ya, y1_ + ya, x0_, x1_)
    PITCH.append((round(float(np.mean(np.diff(xh))), 2), round(float(np.mean(np.diff(ys[ka:kb + 1]))), 2), round(float(np.mean(np.diff(xb))), 2), round(float(np.mean(np.diff(np.concatenate([ys[:ka + 1], ys[kb:]])[1:] if ka else ys[kb:]))), 2)))
    def med3(px):          # the middle colour, channel by channel (np.median's own answer, without its overhead: it is asked half a million times a build)
        q = np.sort(px, 0); n = len(q); return q[n // 2] if n % 2 else (q[n // 2 - 1] + q[n // 2]) / 2
    cell = lambda a, b, e, f: med3(c[a + 1:max(a + 2, b - 1), e + 1:max(e + 2, f - 1)].reshape(-1, 3))
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
