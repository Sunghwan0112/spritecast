"""creature: a monster, an animal or a person drawn straight in 2D - no 3D model of it is made. One design in the look of a picture of yours;
its walk drawn on the poses of a plain MANNEQUIN (a dog given the design's own proportions; a bald man, woman or child - chosen from "what"
when the spec leaves "mannequin" out); any other animation as a sheet of four moments said in words. A side-scrolling game's frames face
right - a game flips them; "view": "above" draws the walk seen from above in 8 facings (or 4), "pixel": 96 as pixel art.

  a four-legged creature ("mannequin": "dog")                 a person ("mannequin": "man" | "woman" | "child")
    design → mannequin (LOOK) → walk → sheets                   mannequin → design → walk → sheets

    python creature.py design    MON.json [--yes] [--again]   PAID (OpenAI, ~$0.06): <name>/design.png, in the look of the spec's "style" picture
                                                              (a person: standing as the mannequin stands and of its build - `mannequin` first)
    python creature.py mannequin MON.json                     free: the mannequin's walk rendered (<name>/mannequin/render) and laid out as the guide
                                                              <name>/walk-guide.png. An animal: given the design's leg length, body depth and neck - LOOK
    python creature.py walk      MON.json [--yes] [--again]   PAID (~$0.06): the design drawn on the guide's poses -> out/walk.png
                     [--only south-east,east]                 (from above or as pixel art: one picture a facing - a sheet - each ~$0.07; --only for some)
    python creature.py sheet     MON.json KIND [--yes] [--again]
                                                              PAID (~$0.06): the spec's "sheets"[KIND] - four moments in words -> out/KIND.png
    python creature.py cut       MON.json                     free: every drawn sheet cut again -> out/*.png, out/creature.json
    python creature.py preview   MON.json                     free: out/preview.gif - the walk moving at its own step over marked ground, then each sheet

The spec: {"name": "boar", "style": "hero.png", "what": "a stout wild boar ... standing on its four legs.", "height": 82,
           "frames": 8, "mannequin": "dog", "sheets": {"hurt": {"moments": "it is struck and ... FIRST: ... FOURTH: ...", "height": 84}}}
  height     how tall the walk's first frame is in the game, px; a sheet's own "height" is its FIRST frame's (0 or left out: the walk's "height" - give
             it when the sheet's first moment is not standing up as the walk does). Every picture is scaled on its own: the model draws its figures at
             a different size in each. "hang": true - a floating thing's frames hang from their tops instead of standing on their bottoms
  mannequin  "dog" (every animal that stands on straight legs under its body - a wolf, a boar, a stag), "man", "woman", "child", a .glb of
             your own (an animal's), or false for a creature with no walk of this kind (a blob, a cloud: sheets only)
  turn       a person: degrees the body is turned toward the viewer as it walks sideways (45; 0 a flat profile)
  view       "side" (default) or "above": a game seen from above ("pitch" 30) - "facings" 8 | 4 | "cardinal", "mirror": true flips the west ones
  pixel      the figure's height in sprite pixels (64-192): the walk drawn as pixel art, on the mannequin reduced to those pixels ("colours": 32)
  redo_below 0.5: a person's frame overlapping the mannequin less is named by `cut` (clothes and hair are not on the bare mannequin: 0.75 is a
             render's). An animal has none - look at it
  style_words  how the style picture is drawn, in words, if the drawing drifts from it

Files go to <the spec's folder>/<name>/. Reference: reference/creature.md."""
import argparse, filecmp, json, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from scipy import ndimage
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import charpipe as CP, charlib as CL          # noqa: E402
STANCE = 0.62                                 # of a step, each paw is on the ground (render_char.html legPose: phase < STANCE)
NEAR = {'fore': 0.75, 'hind': 0.5}            # the near legs' (red: the right ones, RF and RH) place in the step - render_char.html PHASE
PEOPLE = ('man', 'woman', 'child'); PACE = 0.6                # the person mannequins; of a person's step, each foot is on the ground (only a fallback now)
DIRS8 = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
ANGLE = {'east': 0, 'north-east': 45, 'north': 90, 'north-west': 135, 'west': 180, 'south-west': 225, 'south': 270, 'south-east': 315}   # on the ground, degrees
VIEWS = {'south': "walks straight toward the viewer, DOWN the picture - a FRONT view: we see its face and its front",
         'south-east': "walks toward the LOWER RIGHT of the picture - a three-quarter FRONT view: we see its front and its right side",
         'east': "walks to the RIGHT - seen from its right side",
         'north-east': "walks toward the UPPER RIGHT, AWAY from the viewer - a three-quarter BACK view: we see its back and its right side, the back of its head",
         'north': "walks straight AWAY from the viewer, UP the picture - a BACK view: we see its back and the back of its head",
         'north-west': "walks toward the UPPER LEFT, AWAY from the viewer - a three-quarter BACK view: we see its back and its left side, the back of its head",
         'west': "walks to the LEFT - seen from its left side",
         'south-west': "walks toward the LOWER LEFT of the picture - a three-quarter FRONT view: we see its front and its left side"}
GRID = {4: (4, 1), 6: (3, 2), 8: (4, 2)}; SHEET = (1536, 1024)
OVER = {}                                     # each facing's frames' overlap with the mannequin, as cut ("redo_below" - 0.5 - marks a frame that left the pose)
LIMBS_P = ("RIGHT arm is RED and its RIGHT leg YELLOW, its LEFT arm is BLUE and its LEFT leg GREEN")   # a person mannequin's limbs (render_char.html setPlain:
MARKS = "grey, red, yellow, blue or green"           # an arm and a leg of one colour ran into each other; an animal's fore legs as its arms - seen from the front they overlap)
LIMBS_A = "RIGHT fore leg is RED and its RIGHT hind leg YELLOW, its LEFT fore leg is BLUE and its LEFT hind leg GREEN"
PLAIN = 'a plain mannequin, every limb its own colour'      # (mannequin.json's words: a mannequin rendered before the four colours has other words - rendered again)
HEAD_MAX = 64                                 # a person's frame is moved at most this far across to put its head over the mannequin's (px of the sheet)
STYLE = ("in exactly the drawing style of image 1: the same line - its weight and its colour - the same way of shading, the same colours and the same degree of realism. "
         "A finished illustration: not pixel art, not a 3D render")


def load(path):
    p = Path(path).resolve(); s = json.loads(p.read_text())
    for k in ('name', 'what'):
        if not s.get(k): sys.exit(f'spec: "{k}" is missing')
    s['height_given'] = bool(s.get('height'))
    if 'mannequin' not in s: s['mannequin'], s['mannequin_by'] = CL.who_of(s['what'])          # left out: the one "what" names (a man, a woman, a child, a four-legged animal)
    s.setdefault('frames', 8); s.setdefault('sheets', {}); s.setdefault('height', 96); s.setdefault('redo_below', 0.5); s['person'] = s['mannequin'] in PEOPLE
    if s['frames'] not in GRID: sys.exit('spec: "frames" is 4, 6 or 8')
    s.setdefault('view', 'side')
    if s['view'] not in ('side', 'above'): sys.exit('spec: "view" is "side" (the default: a side-scrolling game, the frames facing right) or "above" (a game seen from above, '
                                                    '30° down: every facing drawn)')
    s['above'] = s['view'] == 'above'
    if s['above']:
        if 'turn' in s: sys.exit('spec: "turn" (the body turned toward the viewer) goes with "view": "side" - seen from above every facing is drawn')
        s['turn'] = None; s.setdefault('pitch', 30)
        fc = {8: 8, '8': 8, 4: 'diagonal', '4': 'diagonal', 'diagonal': 'diagonal', 'cardinal': 'cardinal'}.get(s.get('facings', 8))
        if fc is None: sys.exit('spec: "facings" is 8 (the default), 4 or "diagonal" (south-east, south-west, north-east, north-west) or "cardinal" (south, east, north, west)')
        s['dirs'] = list(CP.DIAGONALS) if fc == 'diagonal' else list(CP.CARDINALS) if fc == 'cardinal' else list(DIRS8)
        m = s.get('mirror', False); m = ['west', 'north-west', 'south-west'] if m is True else (m or [])
        s['mirrored'] = [x for x in m if x in s['dirs'] and CP.PAIR.get(x) in s['dirs']]
        bad = [x for x in s['mirrored'] if CP.PAIR[x] in s['mirrored']]
        if bad: sys.exit(f'spec: "mirror" lists facings flipped from their pair, not both of a pair: {bad}')
    else:
        s.setdefault('turn', 45); s['dirs'] = ['east']; s['mirrored'] = []
    s['drawn'] = [x for x in s['dirs'] if x not in s['mirrored']]
    s['pixel'] = int(s.get('pixel') or 0)
    if s['pixel'] and not 64 <= s['pixel'] <= 192: sys.exit('spec: "pixel" is the figure\'s height in sprite pixels, 64 to 192 (the image model keeps to its squares no smaller)')
    d = p.parent / s['name']; d.mkdir(parents=True, exist_ok=True); (d / 'out').mkdir(exist_ok=True); return s, d, p.parent


def design_facing(s):
    """the facing a person's design is drawn in: the side view's east; from above the three-quarter front (south-east), where face and side both show"""
    return 'east' if not s['above'] else 'south-east' if 'south-east' in s['dirs'] else s['dirs'][0]


def blank(d):
    g = d / 'blank.png'
    if not g.exists(): Image.new('RGB', SHEET, 'white').save(g)
    return g


def draw(what, P, imgs, out, size):
    """one OpenAI picture (charpipe's gpt); its safety check turning it down three times running stops the step with a word, not a traceback"""
    try: return CP.gpt(P, imgs, out, size)
    except CP.Refused: sys.exit(f'{what}: turned down by OpenAI\'s safety check three times - {out.name} left as it was. Run it again later, or say '
                                f'it in other words in the spec ("what", or the sheet\'s "moments")')


def design(s, d, root, args):
    out = d / 'design.png'
    if out.exists() and not args.again: return print(f'design: {out} is there (--again to draw it anew)')
    if not s.get('style'): sys.exit('spec: "style" is missing - a picture drawn in the look the creature is to have (a character of the game)')
    if not CP.gate(args, 'design: one OpenAI picture, about $0.06'): return
    words = STYLE + (f" ({s['style_words']})" if s.get('style_words') else ''); imgs = [root / s['style']]
    if s['person']:                       # a person is drawn to the mannequin: standing as it stands, of its build (an animal's mannequin is fitted to the design instead)
        idle = d / f'mannequin/render/idle-{design_facing(s)}.png'
        if not idle.exists(): sys.exit('design: a person - `mannequin` first (the design is drawn standing as the mannequin stands)')
        imgs.append(idle)
        game = 'game seen from above' if s['above'] else 'side-scrolling game'
        P = (f"Image 1 is a character of a {game}, shown for its DRAWING STYLE only. Image 2 is a plain grey mannequin, shown for its VIEW and its BUILD only: the new "
             "character stands exactly as the mannequin stands - seen from the same height, turned the same way, facing the same way, the arms hanging at the sides - and has the mannequin's height, proportions "
             f"and build under its clothes (the mannequin's colours only mark its limbs: its right arm red, right leg yellow, left arm blue, left leg green). Draw a new CHARACTER for the same game {words}: {s['what']} "
             "ONE character, whole from head to feet, in the middle of the picture, small enough that there is white all round it. Plain pure white background, no ground, no shadow, "
             "no text, no frame, and nothing of image 1 or of the mannequin's grey or colours in the picture.")
    else:
        P = (f"Image 1 is a character of a side-scrolling game, shown for its DRAWING STYLE only. Draw a CREATURE for the same game {words}: {s['what']} "
             "ONE creature, whole, seen from the side and FACING RIGHT, in the middle of the picture, small enough that there is white all round it. "
             "Drawn seriously as a real living thing with believable anatomy and materials - not a mascot, not a sticker; not gory or horrible either. "
             "Plain pure white background, no ground, no shadow, no text, no frame, and nothing of image 1 in the picture.")
    (d / 'design-prompt.txt').write_text(P); c = draw('design', P, imgs, out, '1024x1024'); print(f'design: {out}  ${c:.2f} - look at it before anything is drawn from it')
    if not s['person'] and (d / 'walk-guide.png').exists(): print('design: the walk guide was fitted to the design before this one - run `mannequin` again before `walk`')


# ---- the design's build, read off its picture ------------------------------------------------------------------------------------------
def build(d):
    """the design's build in its own picture's px (it faces right; y down): the ground, where its fore and hind feet stand, its back, its belly, its nose"""
    m = CL.white_key(Image.open(d / 'design.png').convert('RGB')); ys, xs = np.nonzero(m); x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1; H = y1 - y0
    foot = m[y1 - max(4, round(H * 0.035)):y1].any(0); runs = []; x = 0
    while x < len(foot):
        if foot[x]:
            a = x
            while x < len(foot) and foot[x]: x += 1
            if runs and a - runs[-1][1] < 6: runs[-1][1] = x
            else: runs.append([a, x])
        x += 1
    c = [(a + b) / 2 for a, b in runs]
    if len(c) < 2: sys.exit(f'mannequin: {len(c)} feet found on the ground in {d / "design.png"} - the design must stand on four legs, seen from the side')
    g = max(range(len(c) - 1), key=lambda i: c[i + 1] - c[i]); hx, fx = float(np.mean(c[:g + 1])), float(np.mean(c[g + 1:])); L = fx - hx
    col = np.nonzero(m[:, round((hx + fx) / 2)])[0]; back, belly = float(col.min()), float(col.max())
    nose = (x1 - 1.0, float(np.nonzero(m[:, x1 - 3])[0].mean()))
    return dict(L=L, leg=y1 - belly, depth=belly - back, nose_up=back - nose[1], nose_out=nose[0] - fx, height=H, width=x1 - x0)


def cells(n):
    c, r = GRID[n]; cw, ch = SHEET[0] // c, SHEET[1] // r; return [(i % c * cw, i // c * ch, cw, ch) for i in range(n)]


def _red(f):
    a = np.asarray(f.convert('RGBA')).astype(int); return a, a[..., 3] > 128, (a[..., 0] > a[..., 2] + 60)


def paw_step(fr):
    """an animal's step, px of its renders a whole step: each near paw's place (the leg's lowest part) in the frames where render_char.html's gait has that
    leg on the ground - its phase (k/n + PHASE) % 1 under STANCE - a straight line through its place against the phase; the fore and the hind paw's lines
    given one slope (least squares), the paws drawn planted then slide least. → (px, {leg: its own}). Which near leg is which: by its COLOUR - the fore red,
    the hind yellow (render_char.html setPlain). A mannequin rendered before the four colours has both red: split by x then (left of the middle the hind),
    which on the four-colour wolf gave the two paws 214 and 136 px a step - a leg reaching under the body was taken for the other"""
    n = len(fr); X = {leg: [] for leg in NEAR}
    for f in fr:
        a, al, rd = _red(f); ys, xs = np.nonzero(al & rd); yel = (a[ys, xs, 1] > 0.55 * a[ys, xs, 0]) & (a[ys, xs, 1] > a[ys, xs, 2] + 40)     # (yellow: its green well over its blue - red's and grey's are level)
        if yel.sum() > 30 and (~yel).sum() > 30: parts = (('fore', ~yel), ('hind', yel))
        else:
            cut = (xs.min() + xs.max()) / 2
            for _ in range(8): cut = (xs[xs < cut].mean() + xs[xs >= cut].mean()) / 2
            parts = (('fore', xs >= cut), ('hind', xs < cut))
        for leg, sel in parts: y, x = ys[sel], xs[sel]; X[leg].append(float(x[y > y.max() - 6].mean()))
    num = den = 0.0; own = {}
    for leg, p0 in NEAR.items():
        t = np.array([(k / n + p0) % 1 for k in range(n)]); on = t < STANCE; t, x = t[on], np.array(X[leg])[on]
        num += float(((t - t.mean()) * (x - x.mean())).sum()); den += float(((t - t.mean()) ** 2).sum()); own[leg] = -float(np.polyfit(t, x, 1)[0])
    return -num / den, own


def foot_step(fr):
    """a person's step, px of its renders a whole step: the near foot (the red; the far one, half hidden behind the near leg, only if the near one tells
    nothing) is followed through the frames in which its lowest point is on the ground (the figures' lowest line, a few px either way). While the sole is FLAT
    (its lowest band as wide as the foot) the heel is where it was set down: the heel's place against the frame, a straight line, its slope. With fewer than two
    flat frames (a 4-frame walk) every frame on the ground counts - the heel, or where the heel would be under a toe still down. → (px, words) or None"""
    A = [_red(f) for f in fr]; n = len(fr); bot = [int(np.nonzero(al.any(1))[0][-1]) for _, al, _ in A]; top = min(int(np.nonzero(al.any(1))[0][0]) for _, al, _ in A)
    ground = max(bot); H = ground - top; tol, band = max(2, round(H * 0.004)), max(3, round(H * 0.007))
    for side, pick in (('near', lambda a, rd: rd), ('far', lambda a, rd: np.maximum(a[..., 1], a[..., 2]) > a[..., 0] + 60)):
        R = []
        for a, al, rd in A:
            ys, xs = np.nonzero(al & pick(a, rd))
            if not len(ys): R.append(None); continue
            lo = int(ys.max()); b = xs[ys > lo - band]; shoe = xs[ys > lo - round(H * 0.04)]
            R.append(dict(on=lo >= ground - tol, x0=int(b.min()), x1=int(b.max()) + 1, mid=(int(shoe.min()) + int(shoe.max()) + 1) / 2))
        on = [bool(r and r['on']) for r in R]
        if all(on) or not any(on): continue
        L = max(R[k]['x1'] - R[k]['x0'] for k in range(n) if on[k]); s0 = next(k for k in range(n) if on[k] and not on[k - 1]); ks = []
        while on[(s0 + len(ks)) % n] and len(ks) < n: ks.append(s0 + len(ks))        # the frames it is down in, in order (round the end of the walk too)
        flat = [k for k in ks if R[k % n]['x1'] - R[k % n]['x0'] >= 0.8 * L]
        use, how = (flat, 'flat') if len(flat) >= 2 else (ks, 'down') if len(ks) >= 2 else (None, None)
        if not use: continue
        heel = [R[k % n]['x0'] if k in flat or (R[k % n]['x0'] + R[k % n]['x1']) / 2 < R[k % n]['mid'] else R[k % n]['x1'] - L for k in use]
        return -float(np.polyfit(use, heel, 1)[0]) * n, f'the {side} foot\'s heel in {len(use)} frames{" with the sole flat" if how == "flat" else " on the ground"}'
    return None


def step_of(fr, person=False):
    """how far ONE whole step carries the mannequin, px of its renders - what the game moves it while its walk goes round once, so that a foot on the
    ground stays where it was set down: measured only in the frames in which the foot IS on the ground (paw_step, foot_step). → (px, how it was measured)
    (It was a foot's whole sweep, max - min over ALL frames, / the share of the step it is down: the stag's least x came from a frame with the paw up - 3 %
    long; a person's foot rolls heel to toe, its lowest point going forward along it - 7-11 % short; and 6 or 4 frames missed touch-down and lift-off.)"""
    if not person:
        v, own = paw_step(fr); return v, f'the near paws in the frames they are down in (alone: the fore {own["fore"]:.0f}, the hind {own["hind"]:.0f} px of the render)'
    got = foot_step(fr)
    if got: return got
    xs = []
    for f in fr:
        _, al, rd = _red(f); ys, xx = np.nonzero(al & rd); xs.append(float(xx[ys > ys.max() - 6].mean()))
    return (max(xs) - min(xs)) / PACE, 'ROUGHLY: no foot was seen on the ground in two frames - the near foot\'s sweep / the share of the step it is down'


def render_once(spec, text, copied=False):
    """the mannequin rendered (charpipe.py render: ~5 minutes for eight facings) - unless its renders are there already, made from this same mannequin.json and rig
    (the guides laid out again for other "frames"... no: those change the json. For another "pixel", "mirror", "facings" or "height" nothing is rendered again)"""
    rj = spec.parent / 'mannequin/render/render.json'
    if not copied and spec.exists() and spec.read_text() == text and rj.exists() and rj.stat().st_mtime > spec.stat().st_mtime:
        print('mannequin: its renders are there, of this same mannequin - not rendered again (delete mannequin/render to render it anew)'); return ''
    spec.write_text(text); return charpipe_render(spec)


def charpipe_render(spec):
    r = subprocess.run([sys.executable, str(HERE / 'charpipe.py'), 'render', str(spec)], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stdout[-600:] + r.stderr[-600:])
    return r.stdout


def guide_frames(d, n):
    """the mannequin's rendered walk and the one scale the guide lays it out at: (frames, their boxes, the box round them all, scale)"""
    fr = [Image.open(d / f'mannequin/render/walk-east-{k}.png').convert('RGBA') for k in range(n)]; bb = [f.getbbox() for f in fr]
    x0 = min(b[0] for b in bb); y0 = min(b[1] for b in bb); x1 = max(b[2] for b in bb); y1 = max(b[3] for b in bb); _, _, cw, ch = cells(n)[0]
    return fr, bb, (x0, y0, x1, y1), min((cw - 60) / (x1 - x0), (ch - 80) / (y1 - y0))


def lay_out(s, d, extra):
    """the mannequin's rendered walk as the guide sheet: every frame at one scale, its own lowest point on its cell's ground line"""
    n = s['frames']; fr, bb, (x0, y0, x1, y1), k = guide_frames(d, n); _, _, cw, ch = cells(n)[0]; gy = ch - 30; g = Image.new('RGB', SHEET, 'white')
    for f, b, (cx, cy, _, _) in zip(fr, bb, cells(n)):
        c = f.crop((x0, y0, x1, b[3])); c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS); g.paste(c, (cx + (cw - c.width) // 2, cy + gy - c.height), c)
    g.save(d / 'walk-guide.png'); v, how = step_of(fr, s['person']); adv = v * k
    (d / 'walk-guide.json').write_text(json.dumps({'n': n, 'ground': gy, 'advance': adv, 'advance_by': how, 'mannequin': s['mannequin'], 'turn': s['turn'] if s['person'] else None, 'limbs': 4, **extra}))
    print(f'mannequin: one whole step carries it {adv:.0f} px of the sheet - {how}'); return adv


def mannequin(s, d, root, args):
    """FREE. An animal: the mannequin with THIS creature's proportions - its legs' length, its body's depth, how its head is carried, each read off the design as a ratio
    to the distance between its fore and hind feet - walking in the side view. A person: the bald man, woman or child as it is, walking turned `turn` degrees toward the
    viewer (the design is then drawn to IT). Either way its frames are laid out as the guide the walk is drawn on"""
    if s['mannequin'] is None: sys.exit('mannequin: the spec leaves "mannequin" out, and "what" names no man, woman, child (a boy, a girl) or animal on four legs to '
                                        'choose one by - give it: "mannequin": "man", "woman", "child", "dog" (any four-legged animal), an animal\'s .glb of yours, or '
                                        'false (no walk of this kind: sheets only)')
    if not s['mannequin']: sys.exit('mannequin: this spec has "mannequin": false - its animations are "sheets"')
    if s.get('mannequin_by'): print(f'mannequin: "{s["mannequin"]}" - the spec leaves "mannequin" out, and "what" says "{s["mannequin_by"]}" (give "mannequin" for another)')
    n = s['frames']; spec = d / 'mannequin.json'; base = {'name': 'mannequin', 'frames': n, 'mannequin': True, 'description': PLAIN}
    base.update({'facings': 8, 'pitch': s['pitch']} if s['above'] else {'view': 'side'})      # (from above all eight are rendered, free: the step is measured on east)
    if s['person']:
        rig, src = d / 'mannequin-rig.glb', HERE.parent / 'mannequins' / f"{s['mannequin']}.glb"     # (a copy: the render writes a standing clip beside the rig it is given)
        copied = not rig.exists() or not filecmp.cmp(src, rig, shallow=False)
        if copied:                                                               # another mannequin than the copy's ("man" made "woman"): copied again, and
            for old in d.glob('mannequin-rig-idle*.glb'): old.unlink()            # the standing clips made from the old one go with it
            if rig.exists(): print(f'mannequin: the copy of the mannequin is not "{s["mannequin"]}" - copied again')
            shutil.copy(src, rig)
        render_once(spec, json.dumps({**base, **({} if s['above'] else {'turn': s['turn']}), 'rig_glb': str(rig), 'design': blank(d).name}, indent=1), copied)
        lay_out_any(s, d, {})
        return print(f'mannequin: {guide_names(s, d)} - {n} moments of one step, and mannequin/render/idle-{design_facing(s)}.png: the view the design is drawn in. Then `design`'
                     + (' (there is a design already: drawn to this mannequin? else `design --again`)' if (d / 'design.png').exists() else ''))
    if not (d / 'design.png').exists(): sys.exit('mannequin: `design` first (or put your own design at <name>/design.png: the creature from the side, facing right, on white)')
    B = build(d); L = B['L']; fit = {k: round(B[v] / L, 3) for k, v in (('leg', 'leg'), ('body', 'depth'), ('nose_up', 'nose_up'), ('nose_out', 'nose_out'))}
    glb = HERE.parent / 'mannequins' / f"{s['mannequin']}.glb" if not str(s['mannequin']).endswith('.glb') else (root / s['mannequin'])
    if not glb.exists(): sys.exit(f'mannequin: {glb} is not there ("mannequin": "dog", "man", "woman", "child", or an animal\'s .glb of your own)')
    # ("turn": 0 - an animal is drawn straight from the side, as its design is: left to the side view's default, 45 since 0.29.0, the dog came
    # out turned toward the viewer - the stag's body short, its step 203 px of the render where it walks 251)
    print(f'mannequin: the design asks for {fit} (each a ratio to the distance between its fore and hind feet)')
    print('\n'.join(l for l in render_once(spec, json.dumps({**base, 'kind': 'animal', 'fit': fit, 'model_glb': str(glb), 'design': 'design.png', **({} if s['above'] else {'turn': 0})},
                                                         indent=1)).splitlines() if 'fitted' in l)); lay_out_any(s, d, {'fit': fit})
    print(f'mannequin: {guide_names(s, d)} - {n} moments of one step. LOOK: its legs as long and its body as deep as the design\'s? then `walk`')


def walk_prompt(n, person=False):
    if person: return person_prompt(n)
    c, r = GRID[n]; rows = f"in {r} row{'s' if r > 1 else ''} of {c} - {n} moments of one walking step, read left to right{', top row first' if r > 1 else ''}"
    return (f"Image 1 is a POSE SHEET: a plain MANNEQUIN of a four-legged animal shown {n} times, {rows}. It has no coat, no face and no tail - it shows only the pose. In every one it "
            "faces RIGHT. Its two legs on the side NEAREST the viewer are warm - the near FORE leg RED, the near HIND leg YELLOW; its two legs on the FAR side are cool - the far "
            f"FORE leg BLUE, the far HIND leg GREEN (half hidden behind the body and the near legs); the rest of it is grey. Image 2 is a creature of a side-scrolling game. Draw the creature of image 2 {n} times - one in place of each mannequin, at that mannequin's place and size on the "
            "sheet, in exactly that mannequin's pose: every leg where the mannequin's leg of the same colour is and bent as it is bent, each paw exactly where the mannequin's paw is (a "
            "paw that is off the ground in the mannequin is off the ground by as much), the back, the chest and the neck where the mannequin's are. The legs that are red and yellow on the "
            "mannequin are drawn in front of the body; those that are blue and green behind it and a little darker. The mannequin has been given this creature's own proportions: its legs are exactly as "
            "LONG as the mannequin's legs, its body as deep, its back at the same height - do not make the legs longer or shorter than the mannequin's. It is the creature of image 2 "
            "with its own build, its own head and face, its own coat and markings - and its own TAIL, as in image 2, swaying a little from frame to frame. "
            f"It is the same creature in all {n}: the same colours, the same markings, the same drawing style and line as image 2, the same size - only its legs change, and its tail a "
            f"little. NOTHING of the mannequin shows in the finished sheet: none of its {MARKS}, none of its smooth bare shape - only the creatures. Each one whole, none "
            "touching another or the sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")


def person_prompt(n):
    c, r = GRID[n]; rows = f"in {r} row{'s' if r > 1 else ''} of {c} - {n} moments of one walking step, read left to right{', top row first' if r > 1 else ''}"
    return (f"Image 1 is a POSE SHEET: a plain bald MANNEQUIN of a person shown {n} times, {rows}. It has no hair, no face and no clothes - it shows only the pose. In every one it walks "
            "to the RIGHT, its body turned a little toward the viewer. Its RIGHT arm is RED and its RIGHT leg YELLOW - the ones nearer the viewer; its LEFT arm is BLUE and its LEFT "
            f"leg GREEN - the far ones; the rest of it is grey. Image 2 is a character of a side-scrolling game. Draw the character of image 2 {n} times - one in place of each mannequin, at that mannequin's "
            "place and size on the sheet, in exactly that mannequin's pose: each arm and each leg where the mannequin's limb of the same colour is and bent as it is bent, each foot "
            "exactly where the mannequin's foot is (a foot that is off the ground in the mannequin is off the ground by as much), the head, the shoulders and the hips where the "
            "mannequin's are, the head turned as the mannequin's head is turned. The body under the clothes IS the mannequin's: the same height, legs and arms exactly as long. On it, "
            "the character of image 2 with its own head and face, its own hair, its own clothes and everything it wears, all as in image 2; hair and loose cloth (a cloak, a skirt, a "
            "braid, a strap) sway a little with the step and hang naturally over the moving limbs. "
            f"It is the same character in all {n}: the same face, the same hair, the same clothes and colours, the same drawing style and line as image 2, the same size. "
            f"NOTHING of the mannequin shows in the finished sheet: none of its {MARKS}, no bald head, no bare body - only the characters. Each one whole, none touching "
            "another or the sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")


def walk(s, d, root, args):
    if s['above'] or s['pixel']: return walk_grid(s, d, root, args)
    out = d / 'walk-drawn.png'
    if out.exists() and not args.again: cut_walk(s, d); return print(f'walk: {out} is there (--again to draw it anew); cut')
    g, gj, ds = d / 'walk-guide.png', d / 'walk-guide.json', d / 'design.png'
    if not g.exists() or not gj.exists(): sys.exit('walk: `mannequin` first - and look at walk-guide.png')
    if not ds.exists(): sys.exit('walk: `design` first - the walk is drawn as the design')
    info = json.loads(gj.read_text()); was = (info.get('n'), info.get('mannequin', s['mannequin']), info.get('turn', s['turn']) if s['person'] else None)
    if was != (s['frames'], s['mannequin'], s['turn'] if s['person'] else None):        # (an older guide has no "mannequin" and "turn": taken as the spec's)
        turned = lambda t: f' turned {t}°' if s['person'] else ''
        sys.exit(f'walk: walk-guide.png is of {was[0]} frames of "{was[1]}"{turned(was[2])} - the spec asks for {s["frames"]} of "{s["mannequin"]}"{turned(s["turn"])}: '
                 'run `mannequin` again (free) and look at the guide')
    if info.get('limbs') != 4: sys.exit(OLD_LIMBS)
    if not s['person'] and ds.stat().st_mtime > g.stat().st_mtime:      # an animal's guide is fitted to its design: one drawn after it is not this guide's
        sys.exit('walk: design.png is newer than walk-guide.png - the guide was fitted to the design before it (its legs, body and neck). Run `mannequin` again '
                 '(free), look at the guide, then `walk`')
    if s['person'] and g.stat().st_mtime > ds.stat().st_mtime:          # a person's design is drawn FROM the mannequin's standing view: a mannequin changed after it
        print('walk: NOTE - walk-guide.png was made after design.png. If the mannequin changed since the design was drawn to it (another "mannequin" or "turn"), '
              'draw the design again first (`design --again`); if `mannequin` was only run again as it was, this is fine')
    if not CP.gate(args, 'walk: one OpenAI picture, about $0.06'): return
    P = walk_prompt(s['frames'], s['person']); (d / 'walk-prompt.txt').write_text(P); c = draw('walk', P, [g, ds], out, f'{SHEET[0]}x{SHEET[1]}')
    print(f'walk: {out}  ${c:.2f}'); cut_walk(s, d); cut_stand(s, d) if s['person'] else None


def ai_mask(path, im, box):
    """the AI cut-out (CL.ai_key: BiRefNet) of ONE cell `box` of a drawn picture `im` (the picture at `path`, maybe resized) - run on that cell alone, as it always
    was - kept with the picture's other cells in <stem>-ai.png and made again only when the picture changes (its size and time, and each cell's box, are written
    into the kept one): run once per cell that needs it, not again on every `cut`. (Run once on the whole picture instead, 1536 px squeezed into BiRefNet's 1024
    took the pale of a mist for paper - 710 px of holes in a stag's misty sheet.)"""
    c = path.with_name(path.stem + '-ai.png'); st = path.stat(); tag = f'{st.st_size} {st.st_mtime_ns} {im.width}x{im.height}'; box = tuple(int(v) for v in box)
    x0, y0, x1, y1 = box; m, boxes = np.zeros((im.height, im.width), bool), []
    try:
        with Image.open(c) as k:
            if k.info.get('of') == tag and k.size == im.size:
                m = np.array(k.convert('L')) > 127; boxes = [tuple(int(v) for v in b.split(',')) for b in k.info.get('boxes', '').split(';') if b]
    except (OSError, ValueError): pass
    if box in boxes: return m[y0:y1, x0:x1]
    a = CL.ai_key(im.crop(box)); m[y0:y1, x0:x1] = a
    boxes = [b for b in boxes if b[2] <= x0 or b[0] >= x1 or b[3] <= y0 or b[1] >= y1] + [box]         # (a cell laid over another's place takes it)
    meta = PngInfo(); meta.add_text('of', tag); meta.add_text('boxes', ';'.join(','.join(map(str, b)) for b in boxes))
    Image.fromarray(m).save(c, pnginfo=meta, optimize=True); return a


def key(im, ai=None):
    """what of a picture is the figure. The paper's white joined to the picture's edge is not (so a spray of drops, a wisp of mist, a scattering of leaves all
    stay - an AI cut-out alone drops such loose pieces); and the paper SHUT IN between its limbs is not either - told from white clothes and pale coats by the AI
    cut-out (BiRefNet, as for a character's frames): paper is the white where IT sees no figure. A herbalist stood with a white panel between her legs, a stag walked
    with one between its forelegs, while this was the white key alone. `ai`: () → the AI cut-out of `im` (kept from an earlier `cut`: ai_mask), asked for
    whenever any near-white is shut in. SPRITECAST_KEY=white: only white as pure as the paper is taken
    for paper. With no onnxruntime it stops (CL.NO_ORT), as a character's frames do: it fell back on the white key by itself and nobody knew."""
    m = CL.white_key(im); x = np.asarray(im.convert('RGB')).astype(int)
    if os.environ.get('SPRITECAST_KEY') == 'white':
        hl, hn = ndimage.label(m & (x.min(2) >= 246) & (x.max(2) - x.min(2) < 8)); big = np.bincount(hl.ravel()) >= 30; big[0] = False
        return m & ~big[hl]
    if not CL._have_ort(): sys.exit(CL.NO_ORT.format(py=sys.executable))
    paper = (x.min(2) > 232) & (x.max(2) - x.min(2) < 18); hl, hn = ndimage.label(m & paper)                  # (paper is white_key's own near-white: m & paper is
    if not hn: return m                                                                                       # exactly the white shut in)
    A = ai() if ai else CL.ai_key(im)
    hl, hn = ndimage.label(m & paper & ~ndimage.binary_dilation(A, iterations=3)); big = np.bincount(hl.ravel()) >= 12; big[0] = False; m = m & ~big[hl]
    # WHAT IS LEFT OF THE PAPER AT A GAP'S EDGE (the user: "white pixels left on the new guard and the woman" - 14 and 37 of them, between the legs and by an
    # arm): the patches under 12 px, and the rim the 3 px of grace round the AI's figure kept. Near-white that the AI sees no figure in and that touches what is
    # not figure is peeled off, three passes; then any speck of near-white wholly outside the AI's figure. White clothes and the white of an eye are inside it.
    pale = (x.min(2) > 220) & (x.max(2) - x.min(2) < 20)
    for _ in range(3):
        rim = m & pale & ~A & ndimage.binary_dilation(~m)
        if not rim.any(): break
        m = m & ~rim
    hl, hn = ndimage.label(m & pale)
    if hn: inside = ndimage.maximum(A, hl, np.arange(1, hn + 1)) > 0; m = m & ~np.concatenate([[False], ~inside])[hl]
    return m


def cut_out(im, m):
    return CL.defringe(Image.fromarray(np.dstack([np.asarray(im.convert('RGB')), (m * 255).astype(np.uint8)])))


def widest(row):
    """the widest run of a mask's row: (start, end) or None"""
    e = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
    if not len(e): return None
    a, b = e[0::2], e[1::2]; i = int(np.argmax(b - a)); return int(a[i]), int(b[i])


def head_x(mk, minw):
    """the middle of a person's head across: in the rows 5-18 % of the figure's height under its crown - the crown the first row with a run `minw` wide (the tip
    of a spear, a feather or a tuft of hair standing above the head is not it) - each row's widest run (a staff or a spear beside the head is a run of its own),
    its middle; the median of those rows (a braid or a collar widening a few does not move it). None if there is no such row"""
    ys = np.nonzero(mk.any(1))[0]; top = next((y for y in ys if (w := widest(mk[y])) and w[1] - w[0] >= minw), None)
    if top is None: return None
    H = ys[-1] - top; mids = [(w[0] + w[1]) / 2 for w in (widest(r) for r in mk[top + round(0.05 * H):top + round(0.18 * H) + 1]) if w]
    return float(np.median(mids)) if mids else None


def walk_step(s, d, info):
    """the guide's step (walk-guide.json "advance"); a guide laid out before the step was measured in the frames a foot is down in has it measured again here
    from the same renders - the guide's frames and scale are those renders' - and walk-guide.json is given it"""
    if 'advance_by' in info: return info['advance'], None
    n = s['frames']; ren = [d / f'mannequin/render/walk-east-{k}.png' for k in range(n)]
    if not all(p.exists() for p in ren) or max(p.stat().st_mtime for p in ren) > (d / 'walk-guide.png').stat().st_mtime:
        print(f'  NOTE: walk-guide.json\'s step was measured the old way (a person\'s 7-11 % short) - run `mannequin` again (free) for the right one'); return info['advance'], None
    fr, _, _, k = guide_frames(d, n); v, how = step_of(fr, s['person']); old = info['advance']
    print(f'  the step measured again from mannequin/render (walk-guide.json had it the old way) - {how}')
    info.update(advance_old=old, advance=v * k, advance_by=how); (d / 'walk-guide.json').write_text(json.dumps(info)); return v * k, old


def low_overlap(s, what, ov, again):
    """a walk's frames' overlap with the mannequin (the drawn figure's outline against the mannequin's in the guide: 1 = the same shape), printed, and the frames under
    "redo_below" (0.5) named. Clothes, hair and a cloak are not on the bare mannequin, so a drawing in its pose overlaps it far less than a character's frame its own
    render (charpipe.py's 0.75): drawings in the pose came to 0.54-0.86 (the lowest a cloak flared wide), a walk drawn on another guide 0.33.
    AN ANIMAL HAS NO THRESHOLD (the user: "check it by eye"): antlers, a mane, a tail, a snout are not on the plain fitted dog, by a different
    amount for every animal - its overlap is printed and kept, and it is looked at"""
    if not s['person']:
        return print(f'  {what}: overlap with the mannequin {ov} (1 = the same shape) - an animal has no threshold: LOOK at the strip and preview.gif yourself '
                     f'(the legs where the mannequin\'s are, the same animal in every frame); {again} (PAID) to draw it anew')
    lo = [i + 1 for i, v in enumerate(ov) if v < s['redo_below']]
    print(f'  {what}: overlap with the mannequin {ov} (1 = the same shape)' + (f' - LOW, frame{"s" if len(lo) > 1 else ""} {lo} under {s["redo_below"]}: LOOK; {again} (PAID)' if lo else ''))


def figure_in_cell(src, im, box, i, n, again):
    """the figure drawn in one cell (cx, cy, cw, ch) of a walk's picture: (the cell's picture, its mask). Every piece stays (a drop, a leaf, a wisp of mist) but the
    ones at the cell's left or right edge - a neighbour's nose or tail come over it; a cell with no figure stops the step"""
    cx, cy, cw, ch = box; c = im.crop((cx, cy, cx + cw, cy + ch)); m = key(c, lambda: ai_mask(src, im, (cx, cy, cx + cw, cy + ch))); lab, cnt = ndimage.label(m)
    if cnt > 1:
        size = np.bincount(lab.ravel()); size[0] = 0; edge = np.zeros(cnt + 1, bool); edge[np.concatenate([lab[:, 0], lab[:, -1]])] = True
        edge[0] = False; edge[int(np.argmax(size))] = False; m = m & ~edge[lab]
    if not lab.any() or np.bincount(lab[m])[1:].max(initial=0) < 0.05 * cw * ch:          # (a drawn figure fills its cell as the mannequin does: 15-25 % of it)
        sys.exit(f'cut: frame {i + 1} of the walk (row {i // GRID[n][0] + 1}, column {i % GRID[n][0] + 1} of {src.name}) has no figure in it - the drawing has fewer '
                 f'than {n}, or one is out of its place. Look at {src.name}; draw it again with {again} (PAID)')
    return c, m


def head_dx(gm, m, P):
    """how far across a person's drawn frame (mask m) is moved to put its head over the mannequin's in the guide (mask gm), at most P px. (The crown: a row 40 %
    as wide as the mannequin's bald head)"""
    ys = np.nonzero(gm.any(1))[0]; hw = max((w[1] - w[0] for w in map(widest, gm[ys[0]:ys[0] + round(0.15 * (ys[-1] - ys[0]))]) if w), default=0)
    hg, hm = head_x(gm, 0.4 * hw), head_x(m, 0.4 * hw); return 0 if hg is None or hm is None else int(np.clip(round(hg - hm), -P, P))


def cut_walk(s, d):
    """the drawn walk cut by the guide's cells: every frame keeps its place in its cell (the body does not jump about), its lowest point on the ground"""
    n = s['frames']; src = d / 'walk-drawn.png'; im = Image.open(src).convert('RGB'); info = json.loads((d / 'walk-guide.json').read_text())
    if info.get('n', n) != n: sys.exit(f'cut: walk-guide.png is of {info["n"]} frames, the spec\'s "frames" is {n} - put it back, or run `mannequin` and `walk --again`')
    if im.size != SHEET: im = im.resize(SHEET, Image.LANCZOS)
    fr = []; moved = []; ov = []; guide = Image.open(d / 'walk-guide.png').convert('RGB')
    P = HEAD_MAX if s['person'] else 0                     # (a person's frames are moved across on a canvas this much wider each side: nothing is cut off)
    for i, (cx, cy, cw, ch) in enumerate(cells(n)):
        c, m = figure_in_cell(src, im, (cx, cy, cw, ch), i, n, '`walk --again`'); f = cut_out(c, m); dx = 0
        gm = np.asarray(guide.crop((cx, cy, cx + cw, cy + ch))).min(2) < 245
        if s['person']:               # a person's drawing sits where it likes across its cell (a cloak behind pushes the body forward, by a different amount each frame - 17 to 49 px
            dx = head_dx(gm, m, P); moved.append(dx)                                                   # on a guard and a herbalist): each frame is moved so that its HEAD is over the mannequin's
            w = Image.new('RGBA', (cw + 2 * P, ch), (0, 0, 0, 0)); w.paste(f, (P + dx, 0)); f = w
        m2 = np.asarray(f)[:, P:P + cw, 3] > 128; ov.append(round(float((m2 & gm).sum() / max(1, (m2 | gm).sum())), 2))
        fr.append((f, f.getbbox()))
    OVER['east'] = ov; low_overlap(s, 'walk', ov, '`walk --again`')
    if moved:
        print(f'  each frame moved across to put its head over the mannequin\'s: {moved} px')
        if max(moved) - min(moved) > 40 or max(map(abs, moved)) >= P:
            print(f'  NOTE: the moves spread over {max(moved) - min(moved)} px{" and reach the most allowed, " + str(P) if max(map(abs, moved)) >= P else ""} - something by the head '
                  '(a hood, a raised hand, loose hair) may have been taken for it: LOOK at out/walk.png, and at preview.gif')
    off = [abs((b[0] + b[2]) / 2 - (cells(n)[0][2] / 2 + P)) for _, b in fr]; tall = [b[3] - b[1] for _, b in fr]
    print(f'  frames {min(tall)}-{max(tall)} px tall on the sheet, their middles within {max(off):.0f} px of their cells\' (more than ~15: the drawing left the guide - look)')
    x0 = min(b[0] for _, b in fr); x1 = max(b[2] for _, b in fr); k = s['height'] / tall[0]; adv, old = walk_step(s, d, info)
    cw2, ch2 = round((x1 - x0) * k) + 4, round(max(tall) * k) + 4; strip = Image.new('RGBA', (cw2 * n, ch2), (0, 0, 0, 0))
    for i, (f, bb) in enumerate(fr):
        c = f.crop((x0, bb[1], x1, bb[3])); c = c.resize((max(1, round(c.width * k)), max(1, round(c.height * k))), Image.LANCZOS); strip.alpha_composite(c, (i * cw2 + 2, ch2 - 2 - c.height))
    strip.save(d / 'out/walk.png', optimize=True); meta = {'cell': [cw2, ch2], 'n': n, 'align': 'bottom', 'step': round(adv * k, 1)}; note(d, 'walk', meta)
    if old is not None: print(f'  the walk\'s step in the game: {round(old * k, 1)} px (the old measure) -> {meta["step"]} px')
    print(f'cut: {d / "out/walk.png"}  cell {cw2}x{ch2}, {n} frames, one whole step carries it {meta["step"]} px - show the frame for how far it has walked, and its paws do not slide')


# ---- seen from above, and pixel art: a guide for each facing (and each sheet of pixel art), the frames on one cell with the ground at one place ---
# "view": "above" - the walk seen from a game's camera 30° (the spec's "pitch") above, in 8 facings (or 4), each drawn on the mannequin walking that way.
# "pixel": N - the walk drawn as pixel art, the figure N sprite pixels tall, on the mannequin already reduced to those pixels (as pixelart.py draws a
# character over its render), read back on the grid the image model drew it on (pixelgrid.py). Either way a frame is not stood on its lowest point: seen
# from above a step goes up and down the picture. Every frame of every facing keeps the place the mannequin's has, the ground under it at one point
# of the cell ("anchor" in out/creature.json) - where the game puts the figure's position.
def guide_names(s, d):
    if not s['above'] and not s['pixel']: return str(d / 'walk-guide.png')
    return f'{d}/walk-guide-*.png ({len(list(d.glob("walk-guide-*.png")))} pictures)'


def lay_out_any(s, d, extra):
    return lay_out(s, d, extra) if not s['above'] and not s['pixel'] else lay_out_grid(s, d, extra)


def renders(d, x, n):
    return [Image.open(d / f'mannequin/render/walk-{x}-{k}.png').convert('RGBA') for k in range(n)]


def anchor_of(d, size):
    """the ground under the figure in its renders (px): the middle across, render.json's footY down (render_char.html: the camera looks at the ground's origin)"""
    return size[0] / 2, json.loads((d / 'mannequin/render/render.json').read_text())['footY'] * size[1]


def step_vec(s, v, x):
    """a whole step's move on the picture, (across, down) px, of a walk facing `x` that goes v px a step along the ground - the ground seen `pitch`° from above"""
    if not s['above']: return v, 0.0
    a = np.radians(ANGLE[x]); return v * np.cos(a), -v * np.sin(a) * np.sin(np.radians(s['pitch']))


def drawn_path(s, d, x, g=0):
    return d / (f'walk-drawn-{x}-{g}.png' if s['pixel'] else f'walk-drawn-{x}.png')


def guide_path(s, d, x, g=0):
    return d / (f'walk-guide-{x}-{g}.png' if s['pixel'] else f'walk-guide-{x}.png')


def lay_out_grid(s, d, extra):
    """FREE. A guide for each facing drawn: walk-guide-<facing>.png, its 8 moments at ONE scale for every facing, the ground under the figure at the same point of
    every cell - or for pixel art walk-guide-<facing>-<sheet>.png, a few frames a sheet already reduced to sprite pixels. The step is measured on east (rendered
    from above as all eight are), the frame the walk stands still in is its narrowest there: the feet passing each other"""
    n = s['frames']; fr = {x: renders(d, x, n) for x in s['drawn']}; east = fr['east'] if 'east' in fr else renders(d, 'east', n)
    W, H = east[0].size; ax, ay = anchor_of(d, (W, H)); bb = [f.getbbox() for v in fr.values() for f in v]
    half = max(max(ax - b[0], b[2] - ax) for b in bb); up = max(ay - b[1] for b in bb); dn = max(0.0, max(b[3] - ay for b in bb))
    v, how = step_of(east, s['person']); stand = int(np.argmin([f.getbbox()[2] - f.getbbox()[0] for f in east]))
    info = {'n': n, 'view': s['view'], 'mannequin': s['mannequin'], 'turn': s['turn'] if s['person'] else None, 'pixel': s['pixel'] or None, 'drawn': s['drawn'],
            'step_render': v, 'advance_by': how, 'stand': stand, 'limbs': 4, **extra}
    for old in d.glob('walk-guide-*.png'): old.unlink()
    (d / 'pixel-state.json').unlink(missing_ok=True)          # (the size the first sheet of pixel art was drawn at: of the old guides)
    if s['pixel']: info.update(pixel_guides(s, d, fr, (ax, ay), half, up, dn))
    else:
        _, _, cw, ch = cells(n)[0]; k = min((cw - 60) / (2 * half), (ch - 60) / (up + dn)); gx, gy = cw / 2, ch - 30 - dn * k
        for x, frs in fr.items():
            g = Image.new('RGB', SHEET, 'white')
            for f, (cx, cy, _, _) in zip(frs, cells(n)):
                b = f.getbbox(); c = f.crop(b); c = c.resize((max(1, round(c.width * k)), max(1, round(c.height * k))), Image.LANCZOS)
                g.paste(c, (cx + round(gx + (b[0] - ax) * k), cy + round(gy + (b[1] - ay) * k)), c)
            g.save(guide_path(s, d, x))
        info.update(k=k, anchor=[gx, gy])
    (d / 'walk-guide.json').write_text(json.dumps(info))
    print(f'mannequin: one whole step carries it {v:.0f} px of the renders along the ground - {how}; it stands still in frame {stand + 1}'); return v


def pixel_frames(s, d, fr, anchor):
    """the renders reduced to sprite pixels (area average, as pixelart.py's guide), the standing figure `pixel` px tall: {facing: [(rgb, mask)]}, the anchor, the factor"""
    ref = Image.open(d / f'mannequin/render/idle-{design_facing(s)}.png').convert('RGBA').getbbox(); q = s['pixel'] / (ref[3] - ref[1]); out = {}
    for x, frs in fr.items():
        out[x] = []
        for f in frs:
            a = np.asarray(f, np.float32) / 255; pm = np.dstack([a[..., :3] * a[..., 3:], a[..., 3]]); w, h = round(f.width * q), round(f.height * q)
            c = [np.asarray(Image.fromarray(pm[..., i]).resize((w, h), Image.BOX)) for i in range(4)]
            out[x].append((np.clip(np.dstack(c[:3]) / np.maximum(c[3], 1e-4)[..., None], 0, 1), c[3] >= 0.5))
    return out, (anchor[0] * q, anchor[1] * q), q


def put(dst, src, m, ox, oy):
    """src's pixels under mask m into dst at (ox, oy), what falls outside dst left out"""
    H, W = dst.shape[:2]; h, w = m.shape; x0, y0 = max(0, -ox), max(0, -oy); x1, y1 = min(w, W - ox), min(h, H - oy)
    if x1 <= x0 or y1 <= y0: return
    sub = dst[oy + y0:oy + y1, ox + x0:ox + x1]; mm = m[y0:y1, x0:x1]; sub[mm] = src[y0:y1, x0:x1][mm]


def pixel_guides(s, d, fr, anchor, half, up, dn):
    """the pixel art's sheets, each facing its own: as many frames side by side as fit (4 if they can), each in the middle of its cell, the ground under them on one
    line; squares of Z px (one sprite pixel) - pixelart.py's size (8 at 96 px; 6 at 128), made smaller down to 6 where that puts four frames on a sheet (a stride
    seen from the side is wide: 2 a sheet at 8 px - and every sheet is a picture paid for)"""
    pf, (pax, pay), q = pixel_frames(s, d, fr, anchor); H_ = s['pixel']; Zmax = 1024 // (H_ * 4 // 3); n = s['frames']; lay = {}
    for x, frs in pf.items():
        bb = [(lambda ys, xs: (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1))(*np.nonzero(m)) for _, m in frs]; w = max(b[1] - b[0] for b in bb)
        up_, dn_ = max(pay - b[2] for b in bb), max(0.0, max(b[3] - pay for b in bb))
        fit = [(p_, Z) for p_ in (4, 3, 2, 1) for Z in range(Zmax, min(6, Zmax) - 1, -1) if (1536 // Z) // p_ >= w + 4 and up_ + dn_ <= 1024 // Z - 6]
        if not fit: sys.exit(f'mannequin: a frame of {x} is too big for a sheet at "pixel": {H_} - a smaller "pixel"')
        per, Z = fit[0]; SW, SH = 1536 // Z, 1024 // Z; CWp = SW // per; gy = round(SH - SH // 12 - dn_)
        if gy - up_ < 2: gy = round(up_ + 2)
        ox = [int((CWp - (b[1] - b[0])) // 2 - b[0]) for b in bb]; oy = int(round(gy - pay)); sheets = -(-n // per)
        for g in range(sheets):
            sh = np.ones((SH, SW, 3), np.float32)
            for j, k in enumerate(range(g * per, min(n, g * per + per))): put(sh, frs[k][0], frs[k][1], j * CWp + ox[k], oy)
            Image.fromarray((sh * 255).round().astype(np.uint8)).resize((SW * Z, SH * Z), Image.NEAREST).save(guide_path(s, d, x, g))
        lay[x] = {'Z': Z, 'per': per, 'cwp': CWp, 'shp': SH, 'ox': ox, 'oy': oy, 'sheets': sheets}
        print(f'mannequin: {x} in pixel art - squares of {Z} px, {per} frames a sheet: {sheets} sheets')
    return {'px': lay, 'q': float(q), 'px_anchor': [float(pax), float(pay)]}


def sheets_of(info, x):
    return info['px'][x]['sheets'] if 'px' in info else 1


OLD_LIMBS = ('walk: the guide is of the mannequin as it was - its two limbs of one side one colour, the prompt now says four colours. Run `mannequin` again '
             '(free: rendered again), look at the guide, then `walk`')


def check_guide(s, info, name, drawing=True):
    if drawing and info.get('limbs') != 4: sys.exit(OLD_LIMBS)
    was = (info.get('n'), info.get('mannequin', s['mannequin']), info.get('view', 'side'), info.get('pixel'), info.get('turn', s['turn']) if s['person'] else None)
    now = (s['frames'], s['mannequin'], s['view'], s['pixel'] or None, s['turn'] if s['person'] else None)
    if was != now or (info.get('drawn') and not set(s['drawn']) <= set(info['drawn'])):
        sys.exit(f'walk: {name} was laid out for {was[0]} frames of "{was[1]}", view "{was[2]}"{", pixel " + str(was[3]) if was[3] else ""} - the spec asks for '
                 f'{now[0]} of "{now[1]}", view "{now[2]}"{", pixel " + str(now[3]) if now[3] else ""}{" (or other facings)" if was == now else ""}: run `mannequin` '
                 'again (free) and look at the guides')


def mannequin_words(s):
    return ('a plain bald MANNEQUIN of a person', 'hair, no face and no clothes') if s['person'] else ('a plain MANNEQUIN of a four-legged animal', 'coat, no face and no tail')


def limbs(s):
    return LIMBS_P if s['person'] else LIMBS_A


def marks(s):
    return MARKS


def pose_words(s):
    if s['person']: return ("Each arm and each leg where the mannequin's limb of the same colour is and bent as it is bent, each foot exactly where the mannequin's foot is, the "
                            "head, the shoulders and the hips where the mannequin's are. The body under the clothes IS the mannequin's. ")
    return ("Every leg where the mannequin's leg of the same colour is and bent as it is bent, each paw exactly where the mannequin's paw is, the back, the chest and the "
            "neck where the mannequin's are, the legs exactly as long as the mannequin's. ")


def own_words(s, x):
    back = s['above'] and x.startswith('north')
    if s['person']:
        return ("On it, the character of image 2: its own head and hair, its own clothes and everything it wears"
                + (" - seen from BEHIND: the back of its head and hair, the back of every garment, drawn as they must be to belong to what image 2 shows; its face does not show. "
                   if back else " - its face, its hair and every garment turned to this view. ")
                + "Hair and loose cloth (a cloak, a skirt, a braid, a strap) sway a little with the step. ")
    return ("It is the creature of image 2 with its own build, its own head and face, its own coat and markings and its own TAIL, swaying a little from frame to frame"
            + (" - seen from BEHIND: its back, its hindquarters and its tail, the back of its head; its face does not show. " if back else ". "))


def above_prompt(s, x):
    """the walk of ONE facing seen from above, drawn on its guide (image 1) as the design (image 2) - the sheet the user's isometric test drew a guard on"""
    n = s['frames']; c, r = GRID[n]; man, bare = mannequin_words(s); w = 'character' if s['person'] else 'creature'
    rows = f"in {r} row{'s' if r > 1 else ''} of {c} - {n} moments of one walking step, read left to right{', top row first' if r > 1 else ''}"
    return (f"Image 1 is a POSE SHEET: {man} shown {n} times, {rows}. It has no {bare} - it shows only the pose and the VIEW. It is seen by a game's camera from ABOVE, "
            f"looking about {s['pitch']} degrees down - {'the top of the head and the shoulders show' if s['person'] else 'the top of its back and of its head show'}, the "
            f"legs are a little shortened. In every one it {VIEWS[x]}. Its {limbs(s)}; the rest of it is grey. Image 2 is a {w} of a game, drawn standing - it shows WHO "
            f"it is, not the view. Draw the {w} of image 2 {n} times - one in place of each mannequin, at that mannequin's place and size on the sheet, in exactly that "
            "mannequin's pose AND seen exactly as the mannequin is seen: from the same height above, turned the same way. " + pose_words(s) + own_words(s, x)
            + f"It is the same {w} in all {n}: the same colours, the same drawing style and line as image 2, the same size. NOTHING of the mannequin shows in the finished "
            f"sheet: none of its {marks(s)}, none of its smooth bare shape{', no bald head' if s['person'] else ''} - only the {w}s. Each one whole, none touching "
            "another or the sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")


def pixel_prompt(s, info, x, g):
    """a sheet of the walk as pixel art, on the mannequin reduced to sprite pixels (image 1), as the design (image 2), going on from the first sheet (image 3)"""
    n = s['frames']; per = info['px'][x]['per']; idx = list(range(g * per, min(n, g * per + per))); Z = info['px'][x]['Z']; man, bare = mannequin_words(s); w = 'character' if s['person'] else 'creature'
    view = (f"seen by a game's camera from ABOVE, looking about {s['pitch']} degrees down; in every cell it {VIEWS[x]}" if s['above'] else
            "seen straight from the side; in every cell it walks to the RIGHT" + (", its body turned a little toward the viewer" if s['person'] else ''))
    return (f"Image 1 is a SHEET of {len(idx)} frames of one walking step, side by side, read left to right: {man} {view}, already reduced to LOW-RESOLUTION PIXELS - every "
            f"square of {Z}x{Z} px in the picture is ONE sprite pixel, on a grid that starts at the picture's top-left corner; the figure is about {s['pixel']} sprite pixels "
            f"tall. It has no {bare} - it shows only the pose and the view. Its {limbs(s)}; the rest of it is grey.\n"
            f"Redraw EVERY cell as FINISHED PIXEL ART of the {w} of image 2, ON THE SAME GRID: every sprite pixel one flat {Z}x{Z} square of a single colour, its edges "
            "exactly on the grid - no anti-aliasing, no blur, no gradients, no dithering, no half-pixels, no detail smaller than one square. Decide every pixel as a pixel "
            "artist would: a dark outline one sprite pixel wide around the whole figure; one-pixel darker lines INSIDE the figure wherever one part passes in front of "
            "another (an arm in front of the body, the near leg in front of the far one); each area in two or three flat tones (light, base, shadow) in clean large "
            f"clusters; {'a face that reads at this size; ' if s['person'] else ''}about 16 colours in all, the SAME colours in every cell"
            + (f" ({s['pixel_words']})" if s.get('pixel_words') else '') + ".\n"
            "Keep the sheet exactly as it is: the same cells, each figure at exactly the same position, size and pose - the same pixels covered. " + pose_words(s) + own_words(s, x)
            + f"The same {w} in every cell. NOTHING of the mannequin shows: none of its {marks(s)}{', no bald head' if s['person'] else ''}. Nothing between the cells, "
            "no borders, no numbers.\n"
            f"Image 2 is the {w} as a finished illustration: {'the face, the hair, the outfit' if s['person'] else 'the head, the coat, the markings'} and the colours to "
            "match - NOT its drawing style, NOT its pose and NOT its view.\n"
            + ("Image 3 is the FIRST frames of this same walk, already drawn as pixel art: continue it exactly - the same " + w + ", the same colours, outline and shading, "
               "the same size of square - but in the poses of THIS sheet's cells (image 1).\n" if g else '')
            + f"The {w}: {s['what']} Plain pure white background, no shadow on the ground, no text.")


def walk_grid(s, d, root, args):
    """PAID: each facing's walk (seen from above), or each sheet of pixel art, one OpenAI picture - `--only south-east,east` for some"""
    gj, ds = d / 'walk-guide.json', d / 'design.png'
    if not gj.exists(): sys.exit('walk: `mannequin` first - and look at the guides')
    if not ds.exists(): sys.exit('walk: `design` first - the walk is drawn as the design')
    info = json.loads(gj.read_text()); check_guide(s, info, 'the guides')
    only = args.only.split(',') if args.only else s['drawn']; bad = [x for x in only if x not in s['drawn']]
    if bad: sys.exit(f'walk: --only {",".join(bad)} - the facings drawn here are {", ".join(s["drawn"])}' + (f' ({", ".join(s["mirrored"])} flipped from their pairs)' if s['mirrored'] else ''))
    jobs = [(x, g) for x in only for g in range(sheets_of(info, x)) if args.again or not drawn_path(s, d, x, g).exists()]
    if not jobs: print('walk: every facing asked for is drawn (--again to draw anew); cut'); return cut_grid(s, d)
    if not CP.gate(args, f'walk: {len(jobs)} OpenAI picture{"s" if len(jobs) > 1 else ""}, about ${0.07 * len(jobs):.2f} - '
                         + ', '.join(f'{x}' + (f' sheet {g + 1}' if s['pixel'] else '') for x, g in jobs)): return
    spent = 0.0
    for x, g in jobs:
        out = drawn_path(s, d, x, g); P = pixel_prompt(s, info, x, g) if s['pixel'] else above_prompt(s, x)
        imgs = [guide_path(s, d, x, g), ds] + ([drawn_path(s, d, x, 0)] if s['pixel'] and g else [])
        out.with_name(out.stem.replace('drawn', 'prompt') + '.txt').write_text(P); c = draw(f'walk {x}', P, imgs, out, f'{SHEET[0]}x{SHEET[1]}'); spent += c
        print(f'walk: {out}  ${c:.2f}')
    print(f'walk: ${spent:.2f} spent'); cut_grid(s, d)


def head_dy(gm, m, P):
    """how far down a frame drawn from above is moved to put its lowest point (the nearer foot) on the mannequin's, at most P px"""
    a, b = np.nonzero(gm.any(1))[0], np.nonzero(m.any(1))[0]; return int(np.clip(int(a[-1]) - int(b[-1]), -P, P)) if len(a) and len(b) else 0


def cut_grid(s, d):
    """FREE: every facing drawn cut again -> out/walk-<facing>.png (a side view's pixel art: out/walk.png), out/stand-<facing>.png, out/creature.json"""
    info = json.loads((d / 'walk-guide.json').read_text()); check_guide(s, info, 'the guides', drawing=False)
    got = [x for x in s['drawn'] if all(drawn_path(s, d, x, g).exists() for g in range(sheets_of(info, x)))]
    if not got: return print('cut: no facing drawn yet - `walk`')
    front = design_facing(s) if design_facing(s) in got else got[0]; got = [front] + [x for x in got if x != front]
    fr = cut_pixel(s, d, info, got) if s['pixel'] else cut_above(s, d, info, got)
    assemble(s, d, info, fr)
    low = [x for x in got if s['person'] and min(OVER.get(x) or [1]) < s['redo_below']]
    if low: print(f'cut: {", ".join(low)} - a frame under {s["redo_below"]} overlap with the mannequin: LOOK at them; `walk --only {",".join(low)} --again` (PAID) draws them anew')


def cut_above(s, d, info, got):
    """each facing's painted walk cut by its guide's cells; a person's frame moved across to put its head over the mannequin's, every frame down to put its nearer foot
    on the mannequin's; each facing's figures brought to one size (the image model draws each picture at a size of its own), the first facing's first frame `height`"""
    n = s['frames']; gx, gy = info['anchor']; P = HEAD_MAX; out = {}; ratio = {}
    for x in got:
        src = drawn_path(s, d, x); im = Image.open(src).convert('RGB'); im = im if im.size == SHEET else im.resize(SHEET, Image.LANCZOS)
        guide = Image.open(guide_path(s, d, x)).convert('RGB'); fs, hs, gh, mv, iou = [], [], [], [], []
        for i, (cx, cy, cw, ch) in enumerate(cells(n)):
            c, m = figure_in_cell(src, im, (cx, cy, cw, ch), i, n, f'`walk --only {x} --again`'); gm = np.asarray(guide.crop((cx, cy, cx + cw, cy + ch))).min(2) < 245
            dx = head_dx(gm, m, P) if s['person'] else 0; dy = head_dy(gm, m, P); mv.append((dx, dy))
            w = Image.new('RGBA', (cw + 2 * P, ch + 2 * P), (0, 0, 0, 0)); w.paste(cut_out(c, m), (P + dx, P + dy)); fs.append(w)
            m2 = np.asarray(w)[P:P + ch, P:P + cw, 3] > 128; iou.append(round(float((m2 & gm).sum() / max(1, (m2 | gm).sum())), 2))
            hs.append(np.ptp(np.nonzero(m.any(1))[0])); gh.append(np.ptp(np.nonzero(gm.any(1))[0]))
        ratio[x] = float(np.median(hs) / np.median(gh)); out[x] = [(f, (gx + P, gy + P)) for f in fs]; OVER[x] = iou
        print(f'  {x}: moved {mv} px (across: the head over the mannequin\'s; down: the nearer foot on its); {ratio[x]:.2f}x the mannequin\'s height')
        low_overlap(s, x, iou, f'`walk --only {x} --again`')
    R = float(np.median(list(ratio.values()))); h0 = (lambda b: b[3] - b[1])(out[got[0]][0][0].getbbox()) * R / ratio[got[0]]; G = s['height'] / h0
    drift = {x: round(R / r, 3) for x, r in ratio.items() if abs(R / r - 1) > 0.03}
    if drift: print(f'  brought to one size - each facing\'s figures made this many times as big: {drift}')
    return {x: [(f, a, G * R / ratio[x]) for f, a in fl] for x, fl in out.items()} | {'_scale': G * info['k']}


def px_lay(m, rm):
    """a sprite's mask laid on the guide's where the two overlap most -> (overlap, row, column) (pixelart.py's lay)"""
    y0, y1, x0, x1 = (lambda ys, xs: (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1))(*np.nonzero(rm)); R = np.pad(rm, 12); best = (-1, 0, 0)
    for oy in range(y0 + (y1 - y0 - m.shape[0]) // 2 - 6, y0 + (y1 - y0 - m.shape[0]) // 2 + 7):
        for ox in range(x0 + (x1 - x0 - m.shape[1]) // 2 - 6, x0 + (x1 - x0 - m.shape[1]) // 2 + 7):
            w = R[oy + 12:oy + 12 + m.shape[0], ox + 12:ox + 12 + m.shape[1]]
            if w.shape != m.shape: continue
            sc = (w & m).sum() / (rm.sum() + m.sum() - (w & m).sum())
            if sc > best[0]: best = (sc, oy, ox)
    return best


def cut_pixel(s, d, info, got):
    """each sheet of pixel art read on the grid it was drawn on (pixelgrid.py, the white shut in between the legs told from white things by the AI cut-out), every sheet
    brought to the first's size, each sprite laid where it covers the guide's best; then one palette of "colours" (32) for every frame of every facing"""
    import pixelgrid as PG, pixelkit as PK
    n = s['frames']; pad = 12
    fr = {x: renders(d, x, n) for x in got}; size = fr[got[0]][0].size; pf, (pax, pay), _ = pixel_frames(s, d, fr, anchor_of(d, size))
    st = d / 'pixel-state.json'; state = json.loads(st.read_text()) if st.exists() else {}; out = {}; ref = None
    for x in got:
        fl = []; ovs = []; L = info['px'][x]; Z, per, CWp, SHp = L['Z'], L['per'], L['cwp'], L['shp']; PG.Z = Z
        for g in range(L['sheets']):
            src = drawn_path(s, d, x, g); im = Image.open(src).convert('RGB'); a = np.asarray(im, np.float32) / 255; idx = list(range(g * per, min(n, g * per + per)))
            lab, _ = ndimage.label(ndimage.binary_opening(a.min(2) < 0.93, np.ones((3, 3)))); cw = CWp * Z * im.width / SHEET[0]; boxes = [None] * len(idx); big = [0] * len(idx)
            for k, sl in enumerate(ndimage.find_objects(lab)):
                npx = int((lab[sl] == k + 1).sum()); c_ = int((sl[1].start + sl[1].stop) / 2 // cw)
                if npx < 40 or c_ >= len(idx): continue
                b = boxes[c_]; big[c_] = max(big[c_], npx); bx = (sl[0].start, sl[0].stop, sl[1].start, sl[1].stop)
                boxes[c_] = bx if b is None else (min(b[0], bx[0]), max(b[1], bx[1]), min(b[2], bx[2]), max(b[3], bx[3]))
            if min(big) < 4000: sys.exit(f'cut: {src.name} has {sum(v >= 4000 for v in big)} figures for {len(idx)} frames - look at it; `walk --only {x} --again` (PAID)')
            bxs = [(max(0, x0 - 12), max(0, y0 - 12), min(im.width, x1 + 12), min(im.height, y1 + 12)) for y0, y1, x0, x1 in boxes]
            crops = [a[b[1]:b[3], b[0]:b[2]] for b in bxs]; fgs = [ai_mask(src, im, b) for b in bxs]; PG.PITCH_[0] = PG.pitch_of(crops)
            gms = []; anc = []
            for i in idx:
                gm = np.zeros((SHp, CWp), bool); put(gm, np.ones_like(pf[x][i][1]), pf[x][i][1], L['ox'][i], L['oy']); gms.append(gm); anc.append((L['ox'][i] + pax, L['oy'] + pay))
            # each sheet's size against the guide BY HEIGHT, frame for its own frame (a walk stands upright in every frame): the figures of two sheets of one
            # facing were drawn the same height (747-766 px) but their squares read 8.09 and 8.59 px - by how the shape fits (pixelart.py's size_on_render) the
            # second came out 6 % LARGER and was made smaller still: its sprites 84 px tall beside the first's 90-94. By height it is read 0.94 and brought up
            reads = [PG.read(c, 0.0, 0.27, fg=q) for c, q in zip(crops, fgs)]
            rs = [r[1].shape[0] / (np.ptp(np.nonzero(gm.any(1))[0]) + 1) for r, gm in zip(reads, gms)]; rsh = float(np.median(rs))
            ref = state.setdefault('scale', round(rsh, 4)) if ref is None else ref; k_ = ref / rsh if abs(ref / rsh - 1) > 0.012 else 1.0
            if k_ != 1.0:
                sz = [(round(c.shape[1] * k_), round(c.shape[0] * k_)) for c in crops]
                crops = [np.asarray(Image.fromarray((c * 255).round().astype(np.uint8)).resize(z, Image.LANCZOS), np.float32) / 255 for c, z in zip(crops, sz)]
                fgs = [np.asarray(Image.fromarray(q).resize(z, Image.NEAREST)) for q, z in zip(fgs, sz)]; reads = [PG.read(c, 0.0, 0.27, fg=q) for c, q in zip(crops, fgs)]
            print(f'  {x} sheet {g + 1}: squares of {PG.PITCH_[0]:.2f} px (asked {Z}), drawn {rsh:.2f}x the guide' + (f' - brought to {ref:.2f}x' if k_ != 1.0 else ''))
            for (low, m, hr), gm, (ax, ay) in zip(reads, gms, anc):
                # the sprite is drawn about `ref` times the guide's size (the image model's own: ~1.1): laid on the guide's middle, its ground is the guide's anchor moved
                # out from that middle as much - so a sprite's feet stand on it, not 5 % under it
                _, oy, ox = px_lay(m, gm); ys, xs = np.nonzero(gm); my, mx = (ys.min() + ys.max() + 1) / 2, (xs.min() + xs.max() + 1) / 2
                cs = (SHp + 2 * pad, round(CWp * 1.3) + 2 * pad); sh_ = (cs[1] - 2 * pad - CWp) // 2
                big_ = np.asarray(Image.fromarray(gm).resize((round(gm.shape[1] * ref), round(gm.shape[0] * ref)), Image.NEAREST)); ovs.append(round(float(px_lay(m, big_)[0]), 2))
                fl.append((low, m, hr, cs, (ox + pad + sh_, oy + pad), (mx + (ax - mx) * ref + pad + sh_, my + (ay - my) * ref + pad)))
        out[x] = fl; OVER[x] = ovs; low_overlap(s, x, ovs, f'`walk --only {x} --again`')
    st.write_text(json.dumps(state))
    # ONE PALETTE FOR THE BODIES, ONE FOR THE HEADS (pixelart.py's way: among a body's colours a face's few - the eyes, a brow, a beard's edge - were lost, and a
    # face came back a blank of skin). The heads' rows are not cleaned of lone pixels either: an eye is one. White is kept white (k-means greys an eye's white)
    nb = int(s.get('colours', 32)); nh = min(13, max(3, round(nb * 0.36))); nb = max(3, nb - nh)
    def pal(pix, k):
        pl = PK.palette(pix, k)
        if (pix.min(1) > 0.9).sum() >= 2: pl = np.vstack([pl, PK.lab(np.ones((1, 3)))])
        return pl, np.clip(PK.lab2rgb(pl), 0, 1)
    body = lambda low, m, hr: np.concatenate([low[:hr[0]][m[:hr[0]]], low[hr[1]:][m[hr[1]:]]]); head = lambda low, m, hr: low[hr[0]:hr[1]][m[hr[0]:hr[1]]]
    bl, br = pal(np.concatenate([body(*f[:3]) for fl in out.values() for f in fl]), nb); hl, hrgb = pal(np.concatenate([head(*f[:3]) for fl in out.values() for f in fl]), nh)
    res = {}
    for x, fl in out.items():
        res[x] = []
        for low, m, hr, cs, (px0, py0), a in fl:
            ix = PK.clean(PK.snap(low, bl, br), m); rgb_ = br[ix]
            if hr[1] > hr[0]: rgb_[hr[0]:hr[1]] = hrgb[PK.snap(low[hr[0]:hr[1]], hl, hrgb)]
            c = np.zeros(cs + (4,), np.float32); put(c, np.dstack([rgb_, np.ones(m.shape)]), m, px0, py0)
            res[x].append((Image.fromarray((c * 255).round().astype(np.uint8)), a, 1.0))
    print(f'  {len(bl) + len(hl)} colours in all the frames ({len(hl)} of them the heads\')')
    return res | {'_scale': info['q'] * ref}


def assemble(s, d, info, fr):
    """the cut frames of every facing on ONE cell size, the ground under the figure at one point of it ("anchor"): out/walk-<facing>.png (the side view's pixel art:
    out/walk.png), a facing flipped from its pair where the spec says "mirror"; the frame the walk stands still in, out/stand-<facing>.png (stand.png); each
    facing's step - how far ONE whole step carries it on the picture, across and down - in out/creature.json"""
    n = s['frames']; scale = fr.pop('_scale'); L = {}
    for x, fl in fr.items():
        L[x] = []
        for img, (ax, ay), t in fl:
            if t != 1.0: img = img.resize((max(1, round(img.width * t)), max(1, round(img.height * t))), Image.LANCZOS); ax, ay = ax * t, ay * t
            b = img.getbbox(); L[x].append((img.crop(b), ax - b[0], ay - b[1]))
    half = max(max(ax, c.width - ax) for v in L.values() for c, ax, _ in v); up = max(ay for v in L.values() for _, _, ay in v)
    dn = max(c.height - ay for v in L.values() for c, _, ay in v); cw, ch = int(np.ceil(2 * half)) + 4, int(np.ceil(up + dn)) + 4; A = (cw / 2, up + 2)
    tag = (lambda x: f'-{x}') if s['above'] else (lambda x: '')
    for x in s['dirs']:
        src = x if x in L else CP.PAIR.get(x) if x in s['mirrored'] and CP.PAIR.get(x) in L else None
        if src is None: continue
        strip = Image.new('RGBA', (cw * n, ch), (0, 0, 0, 0)); fl = []
        for i, (c, ax, ay) in enumerate(L[src]):
            if src != x: c = c.transpose(Image.FLIP_LEFT_RIGHT); ax = c.width - ax
            fl.append((c, ax, ay)); strip.alpha_composite(c, (i * cw + round(A[0] - ax), round(A[1] - ay)))
        strip.save(d / f'out/walk{tag(x)}.png', optimize=True); st = [round(float(v * scale), 1) for v in step_vec(s, info["step_render"], x)]
        note(d, f'walk{tag(x)}', {'cell': [cw, ch], 'n': n, 'align': 'anchor', 'anchor': [round(A[0], 1), round(A[1], 1)], 'step': st if s['above'] else st[0], 'overlap': OVER.get(src, []),
                                 **({'flipped_from': src} if src != x else {}), **({'pixel': s['pixel']} if s['pixel'] else {})})
        c, ax, ay = fl[info['stand']]; one = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); one.alpha_composite(c, (round(A[0] - ax), round(A[1] - ay)))
        one.save(d / f'out/stand{tag(x)}.png', optimize=True); note(d, f'stand{tag(x)}', {'size': [cw, ch], 'align': 'anchor', 'anchor': [round(A[0], 1), round(A[1], 1)]})
        print(f'cut: {d / f"out/walk{tag(x)}.png"}  cell {cw}x{ch}, {n} frames, one whole step carries it {st} px' + (f' (flipped from {src})' if src != x else ''))


def preview_grid(s, d):
    """out/preview.gif: every facing walking at its own step over dotted ground (does a foot slide?) - pixel art shown 3 times its size, square for square"""
    j = json.loads((d / 'out/creature.json').read_text()); tag = (lambda x: f'walk-{x}') if s['above'] else (lambda x: 'walk')
    ws = [x for x in s['dirs'] if tag(x) in j and (d / f'out/{tag(x)}.png').exists()]
    if not ws: sys.exit('preview: no walk cut yet - `walk` or `cut` first')
    m0 = j[tag(ws[0])]; cw, ch = m0['cell']; n = m0['n']
    st = {x: (lambda v: v if isinstance(v, list) else [v, 0])(j[tag(x)]['step']) for x in ws}
    z = 3 if s['pixel'] else min(1.0, 1600 / (min(4, len(ws)) * (cw + 3.2 * max(abs(v[0]) for v in st.values())) + 80))     # (a painted set: 4 tiles in 1600 px)
    TW = round((cw + 3.2 * max(abs(v[0]) for v in st.values())) * z) + 20; TH = round((ch + 3.2 * max(abs(v[1]) for v in st.values())) * z) + 20
    cols = min(4, len(ws)); rows = -(-len(ws) // cols); frames = []
    strips = {x: Image.open(d / f'out/{tag(x)}.png').convert('RGBA') for x in ws}
    cell = lambda x, k: (lambda c: c if z == 1 else c.resize((round(cw * z), round(ch * z)), Image.NEAREST if s['pixel'] else Image.LANCZOS))(strips[x].crop((k * cw, 0, (k + 1) * cw, ch)))
    sin = np.sin(np.radians(s['pitch'])) if s['above'] else 0
    for i in range(3 * n):
        f = Image.new('RGBA', (TW * cols, TH * rows), (126, 140, 150, 255))
        for t, x in enumerate(ws):
            ox, oy = t % cols * TW, t // cols * TH; gxs, gys = max(4, round(28 * z)), max(1, round(28 * z * sin)) if sin else 0
            if gys:
                for yy in range(oy + 6, oy + TH - 6, gys):
                    for xx in range(ox + 6 + (yy // gys % 2) * gxs // 2, ox + TW - 6, gxs): f.paste((96, 108, 118, 255), (xx, yy, xx + 3, yy + 2))
            else:
                gy_ = oy + TH - 10; f.paste((70, 80, 90, 255), (ox, gy_, ox + TW, gy_ + 2))
                for xx in range(ox, ox + TW, gxs): f.paste((96, 108, 118, 255), (xx, gy_ + 2, xx + 3, gy_ + 10))
            ax, ay = j[tag(x)]['anchor']; vx, vy = st[x]; k_ = i / n - 1.5                      # (it walks 3 steps, from 1.5 before the tile's middle to 1.5 past it)
            px = ox + (TW - cw * z) / 2 + k_ * vx * z; py = oy + (TH - ch * z) / 2 + k_ * vy * z
            if not gys: py = oy + TH - 10 - ay * z
            f.alpha_composite(cell(x, i % n), (round(px), round(py)))
        frames.append(f.convert('RGB'))
    pal = frames[0].quantize(255, method=Image.MEDIANCUT, dither=Image.NONE); q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(d / 'out/preview.gif', save_all=True, append_images=q[1:], duration=110, loop=0); print(f'preview: {d / "out/preview.gif"}  ({", ".join(ws)})')


# ---- any other animation: four moments said in words ------------------------------------------------------------------------------------
def figures(im):
    """the drawn figures of a sheet, left to right: [x0, x1] of each run of columns with something in it"""
    m = CL.white_key(im); col = m.sum(0) > 2; out = []; x = 0
    while x < len(col):
        if col[x]:
            a = x
            while x < len(col) and col[x]: x += 1
            if out and a - out[-1][1] < 14: out[-1][1] = x
            else: out.append([a, x])
        x += 1
    return [b for b in out if b[1] - b[0] > 24], m


def sheet(s, d, root, args, kind):
    if kind not in s['sheets']: sys.exit(f'sheet: "{kind}" is not in the spec\'s "sheets" ({", ".join(s["sheets"]) or "none"})')
    out = d / f'{kind}-drawn.png'
    if out.exists() and not args.again: cut_sheet(s, d, kind); return print(f'sheet: {out} is there (--again to draw it anew); cut')
    if not (d / 'design.png').exists(): sys.exit('sheet: `design` first')
    if not CP.gate(args, f'sheet {kind}: one OpenAI picture, about $0.06'): return
    w = 'character' if s['person'] or s.get('noun') == 'character' else 'creature'            # ("noun": "character" - a person with no mannequin walk here: the game's own heroine, for a sheet of her struck)
    P = (f"Image 2 is a {w} of a side-scrolling game. Image 1 is the blank sheet to draw on. Draw the SAME {w} FOUR times in ONE ROW, side by side with clear white "
         f"space between them, read left to right - four moments of one animation: {s['sheets'][kind]['moments']} "
         f"It is the same {w} in all four: the same colours, the same face and markings, the same drawing style and line as image 2, the same size "
         "(only its shape changes as said), all four FACING RIGHT, their lowest points on one level line across the sheet. Each one whole, none touching another or the "
         "sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")
    (d / f'{kind}-prompt.txt').write_text(P); c = draw(f'sheet {kind}', P, [blank(d), d / 'design.png'], out, f'{SHEET[0]}x{SHEET[1]}'); print(f'sheet: {out}  ${c:.2f}'); cut_sheet(s, d, kind)


def cut_sheet(s, d, kind):
    """a sheet's four figures cut apart and scaled by ONE number (a squashed frame stays squashed), each stood on the bottom of its cell and centred on its own middle.
    The number is the sheet's own: its FIRST figure made "height" px tall (the sheet's, or the walk's - its first moment standing as the walk's first frame does).
    Each picture's figures are drawn at their own size - a person 430 px tall in a walk's cell, 700-900 px on a sheet - so the walk's scale made a sheet 1.6-2x too big"""
    o = s['sheets'][kind]; src = d / f'{kind}-drawn.png'; im = Image.open(src).convert('RGB'); bs, m = figures(im)
    h = o.get('height') or s['height']
    if not o.get('height') and not s['height_given'] and not s['mannequin']:
        sys.exit(f'cut: give "sheets"."{kind}"."height" (its first frame\'s height in the game, px), or the spec\'s "height"')
    if len(bs) != 4:                                  # figures that touch, or one in pieces (a spray of drops, a patch of mist): cut where there is least between them
        ink = m.sum(0).astype(float); W = im.width; cutx = [0]
        for i in (1, 2, 3):                           # near each quarter line (a tenth of the sheet either way), the emptiest column - the middle of the widest empty run
            lo, hi = round(W * (i / 4 - 0.1)), round(W * (i / 4 + 0.1)); seg = ink[lo:hi]; low = seg <= seg.min() + 1; lab, cnt = ndimage.label(low)
            best = max(range(1, cnt + 1), key=lambda r: (lab == r).sum()); xs = np.nonzero(lab == best)[0]; cutx.append(lo + int(xs.mean()))
        print(f'cut: {len(bs)} figures found, not 4 - cut at the emptiest columns near the quarter lines {cutx[1:]}; LOOK at out/{kind}.png'); bs = [[cutx[i], (cutx + [W])[i + 1]] for i in range(4)]
    fr = []
    for i, (x0, x1) in enumerate(bs):
        c = im.crop((x0, 0, x1, im.height)); f = cut_out(c, key(c, lambda: ai_mask(src, im, (x0, 0, x1, im.height)))); bb = f.getbbox()
        if bb is None: sys.exit(f'cut: figure {i + 1} of {kind}-drawn.png (columns {x0}-{x1}) is empty - the drawing has fewer than four. Look at it; draw it again with '
                                f'`sheet {kind} --again` (PAID)')
        fr.append(f.crop(bb))
    k = h / fr[0].height
    fr = [f.resize((max(1, round(f.width * k)), max(1, round(f.height * k))), Image.LANCZOS) for f in fr]; hang = bool(o.get('hang'))
    cw = max(f.width for f in fr) + 4; ch = max(f.height for f in fr) + 4; strip = Image.new('RGBA', (cw * 4, ch), (0, 0, 0, 0))
    for i, f in enumerate(fr): strip.alpha_composite(f, (i * cw + (cw - f.width) // 2, 2 if hang else ch - 2 - f.height))
    strip.save(d / f'out/{kind}.png', optimize=True); note(d, kind, {'cell': [cw, ch], 'n': 4, 'align': 'top' if hang else 'bottom'})
    print(f'cut: {d / f"out/{kind}.png"}  cell {cw}x{ch}, frames {[f.size for f in fr]}')


def cut_stand(s, d):
    """out/stand.png: the design itself cut out, as tall as the walk's first frame - what stands still between walks (it is drawn in the walk's own view)"""
    src = d / 'design.png'; im = Image.open(src).convert('RGB'); f = cut_out(im, key(im, lambda: ai_mask(src, im, (0, 0) + im.size))); bb = f.getbbox()
    if bb is None: sys.exit(f'cut: {src} is empty - nothing on its white')
    f = f.crop(bb); k = s['height'] / f.height
    f = f.resize((max(1, round(f.width * k)), s['height']), Image.LANCZOS); f.save(d / 'out/stand.png', optimize=True); note(d, 'stand', {'size': list(f.size), 'align': 'bottom'})
    print(f'cut: {d / "out/stand.png"}  {f.size[0]}x{f.size[1]}')


def note(d, kind, meta):
    p = d / 'out/creature.json'; j = json.loads(p.read_text()) if p.exists() else {}; j[kind] = meta; p.write_text(json.dumps(j, indent=1))
    if (d / 'scale.txt').exists(): (d / 'scale.txt').unlink()      # (the one scale every picture once shared: each has its own now)


def cut(s, d, root, args):
    if s['above'] or s['pixel']:
        if (d / 'walk-guide.json').exists(): cut_grid(s, d)
    else:
        if (d / 'walk-drawn.png').exists(): cut_walk(s, d)
        if s['person'] and (d / 'design.png').exists(): cut_stand(s, d)
    for kind in s['sheets']:
        if (d / f'{kind}-drawn.png').exists(): cut_sheet(s, d, kind)


def preview(s, d, root, args):
    """out/preview.gif: the walk moving at its own step over marked ground (do its paws slide?), then each sheet's four frames"""
    if s['above'] or s['pixel']: return preview_grid(s, d)
    j = {k: v for k, v in json.loads((d / 'out/creature.json').read_text()).items() if 'cell' in v} if (d / 'out/creature.json').exists() else {}
    if not j: sys.exit('preview: no strip cut yet - `walk`, `sheet` or `cut` first')
    W = max(m['cell'][0] for m in j.values()) + 260; H = max(m['cell'][1] for m in j.values()) + 34; frames = []
    def ground():
        f = Image.new('RGBA', (W, H), (126, 140, 150, 255)); f.paste((70, 80, 90, 255), (0, H - 26, W, H - 24))
        for gx in range(0, W, 28): f.paste((96, 108, 118, 255), (gx, H - 24, gx + 3, H))
        return f
    for kind, m in j.items():
        strip = Image.open(d / f'out/{kind}.png').convert('RGBA'); cw, ch = m['cell']
        for i in range(m['n'] * (3 if kind == 'walk' else 1)):
            f = ground(); x = 12 + (i * m['step'] / m['n'] if kind == 'walk' else 110)
            f.alpha_composite(strip.crop((i % m['n'] * cw, 0, i % m['n'] * cw + cw, ch)), (round(x), 4 if m['align'] == 'top' else H - 24 - ch)); frames.append((f.convert('RGB'), 110 if kind == 'walk' else 260))
    big = Image.new('RGB', (W, H * len(frames))); [big.paste(f, (0, i * H)) for i, (f, _) in enumerate(frames)]
    pal = big.quantize(255, method=Image.MEDIANCUT, dither=Image.NONE); q = [f.quantize(palette=pal, dither=Image.NONE) for f, _ in frames]
    q[0].save(d / 'out/preview.gif', save_all=True, append_images=q[1:], duration=[t for _, t in frames], loop=0); print(f'preview: {d / "out/preview.gif"}  ({", ".join(j)})')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('step', choices=['design', 'mannequin', 'walk', 'sheet', 'cut', 'preview']); ap.add_argument('spec'); ap.add_argument('kind', nargs='?')
    ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', action='store_true'); ap.add_argument('--only', default=''); A = ap.parse_args(); S, D, ROOT = load(A.spec)
    if A.step == 'sheet':
        if not A.kind: sys.exit('sheet: which one? `creature.py sheet MON.json hurt`')
        sheet(S, D, ROOT, A, A.kind)
    else: {'design': design, 'mannequin': mannequin, 'walk': walk, 'cut': cut, 'preview': preview}[A.step](S, D, ROOT, A)
