"""creature: a monster, an animal or a person for a side-scrolling game, drawn straight in 2D - no 3D model of it is made. One design in the
look of a picture of yours; its walk drawn on the poses of a plain MANNEQUIN (a dog given the design's own proportions; a bald man, woman
or child); any other animation as a sheet of four moments said in words. Frames face right - a game flips them.

  a four-legged creature ("mannequin": "dog")                 a person ("mannequin": "man" | "woman" | "child")
    design → mannequin (LOOK) → walk → sheets                   mannequin → design → walk → sheets

    python creature.py design    MON.json [--yes] [--again]   PAID (OpenAI, ~$0.06): <name>/design.png, in the look of the spec's "style" picture
                                                              (a person: standing as the mannequin stands and of its build - `mannequin` first)
    python creature.py mannequin MON.json                     free: the mannequin's walk rendered (<name>/mannequin/render) and laid out as the guide
                                                              <name>/walk-guide.png. An animal: given the design's leg length, body depth and neck - LOOK
    python creature.py walk      MON.json [--yes] [--again]   PAID (~$0.06): the design drawn on the guide's poses -> out/walk.png
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
GRID = {4: (4, 1), 6: (3, 2), 8: (4, 2)}; SHEET = (1536, 1024)
HEAD_MAX = 64                                 # a person's frame is moved at most this far across to put its head over the mannequin's (px of the sheet)
STYLE = ("in exactly the drawing style of image 1: the same line - its weight and its colour - the same way of shading, the same colours and the same degree of realism. "
         "A finished illustration: not pixel art, not a 3D render")


def load(path):
    p = Path(path).resolve(); s = json.loads(p.read_text())
    for k in ('name', 'what'):
        if not s.get(k): sys.exit(f'spec: "{k}" is missing')
    s['height_given'] = bool(s.get('height'))
    s.setdefault('frames', 8); s.setdefault('mannequin', 'dog'); s.setdefault('sheets', {}); s.setdefault('height', 96); s.setdefault('turn', 45); s['person'] = s['mannequin'] in PEOPLE
    if s['frames'] not in GRID: sys.exit('spec: "frames" is 4, 6 or 8')
    d = p.parent / s['name']; d.mkdir(parents=True, exist_ok=True); (d / 'out').mkdir(exist_ok=True); return s, d, p.parent


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
        idle = d / 'mannequin/render/idle-east.png'
        if not idle.exists(): sys.exit('design: a person - `mannequin` first (the design is drawn standing as the mannequin stands)')
        imgs.append(idle)
        P = ("Image 1 is a character of a side-scrolling game, shown for its DRAWING STYLE only. Image 2 is a plain grey mannequin, shown for its VIEW and its BUILD only: the new "
             "character stands exactly as the mannequin stands - turned the same way, facing the same way, the arms hanging at the sides - and has the mannequin's height, proportions "
             f"and build under its clothes (the mannequin's red and blue only mark its right and left limbs). Draw a new CHARACTER for the same game {words}: {s['what']} "
             "ONE character, whole from head to feet, in the middle of the picture, small enough that there is white all round it. Plain pure white background, no ground, no shadow, "
             "no text, no frame, and nothing of image 1 or of the mannequin's grey, red or blue in the picture.")
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
    """an animal's step, px of its renders a whole step: each near paw's place (the red of each frame split into hind and fore leg by x; the leg's lowest part)
    in the frames where render_char.html's gait has that leg on the ground - its phase (k/n + PHASE) % 1 under STANCE - a straight line through its place
    against the phase; the fore and the hind paw's lines given one slope (least squares), the paws drawn planted then slide least. → (px, {leg: its own})"""
    n = len(fr); X = {leg: [] for leg in NEAR}
    for f in fr:
        _, al, rd = _red(f); ys, xs = np.nonzero(al & rd)
        cut = (xs.min() + xs.max()) / 2
        for _ in range(8): cut = (xs[xs < cut].mean() + xs[xs >= cut].mean()) / 2
        for leg, sel in (('fore', xs >= cut), ('hind', xs < cut)): y, x = ys[sel], xs[sel]; X[leg].append(float(x[y > y.max() - 6].mean()))
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
    for side, pick in (('near', lambda a, rd: rd), ('far', lambda a, rd: a[..., 2] > a[..., 0] + 60)):
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
    (d / 'walk-guide.json').write_text(json.dumps({'n': n, 'ground': gy, 'advance': adv, 'advance_by': how, 'mannequin': s['mannequin'], 'turn': s['turn'] if s['person'] else None, **extra}))
    print(f'mannequin: one whole step carries it {adv:.0f} px of the sheet - {how}'); return adv


def mannequin(s, d, root, args):
    """FREE. An animal: the mannequin with THIS creature's proportions - its legs' length, its body's depth, how its head is carried, each read off the design as a ratio
    to the distance between its fore and hind feet - walking in the side view. A person: the bald man, woman or child as it is, walking turned `turn` degrees toward the
    viewer (the design is then drawn to IT). Either way its frames are laid out as the guide the walk is drawn on"""
    if not s['mannequin']: sys.exit('mannequin: this spec has "mannequin": false - its animations are "sheets"')
    n = s['frames']; spec = d / 'mannequin.json'; base = {'name': 'mannequin', 'view': 'side', 'frames': n, 'mannequin': True, 'description': 'a plain mannequin'}
    if s['person']:
        rig, src = d / 'mannequin-rig.glb', HERE.parent / 'mannequins' / f"{s['mannequin']}.glb"     # (a copy: the render writes a standing clip beside the rig it is given)
        if not rig.exists() or not filecmp.cmp(src, rig, shallow=False):          # another mannequin than the copy's ("man" made "woman"): copied again, and
            for old in d.glob('mannequin-rig-idle*.glb'): old.unlink()            # the standing clips made from the old one go with it
            if rig.exists(): print(f'mannequin: the copy of the mannequin is not "{s["mannequin"]}" - copied again')
            shutil.copy(src, rig)
        spec.write_text(json.dumps({**base, 'turn': s['turn'], 'rig_glb': str(rig), 'design': blank(d).name}, indent=1)); charpipe_render(spec); adv = lay_out(s, d, {})
        return print(f'mannequin: {d / "walk-guide.png"} - {n} moments of one step, and mannequin/render/idle-east.png: the view the design is drawn in. Then `design`'
                     + (' (there is a design already: drawn to this mannequin? else `design --again`)' if (d / 'design.png').exists() else ''))
    if not (d / 'design.png').exists(): sys.exit('mannequin: `design` first (or put your own design at <name>/design.png: the creature from the side, facing right, on white)')
    B = build(d); L = B['L']; fit = {k: round(B[v] / L, 3) for k, v in (('leg', 'leg'), ('body', 'depth'), ('nose_up', 'nose_up'), ('nose_out', 'nose_out'))}
    glb = HERE.parent / 'mannequins' / f"{s['mannequin']}.glb" if not str(s['mannequin']).endswith('.glb') else (root / s['mannequin'])
    if not glb.exists(): sys.exit(f'mannequin: {glb} is not there ("mannequin": "dog", "man", "woman", "child", or an animal\'s .glb of your own)')
    spec.write_text(json.dumps({**base, 'kind': 'animal', 'fit': fit, 'model_glb': str(glb), 'design': 'design.png'}, indent=1))
    print(f'mannequin: the design asks for {fit} (each a ratio to the distance between its fore and hind feet)')
    print('\n'.join(l for l in charpipe_render(spec).splitlines() if 'fitted' in l)); adv = lay_out(s, d, {'fit': fit})
    print(f'mannequin: {d / "walk-guide.png"} - {n} moments of one step. LOOK: its legs as long and its body as deep as the design\'s? then `walk`')


def walk_prompt(n, person=False):
    if person: return person_prompt(n)
    c, r = GRID[n]; rows = f"in {r} row{'s' if r > 1 else ''} of {c} - {n} moments of one walking step, read left to right{', top row first' if r > 1 else ''}"
    return (f"Image 1 is a POSE SHEET: a plain MANNEQUIN of a four-legged animal shown {n} times, {rows}. It has no coat, no face and no tail - it shows only the pose. In every one it "
            "faces RIGHT. Its two legs on the side NEAREST the viewer are RED; its two legs on the FAR side are BLUE (half hidden behind the body and the near legs); the rest of it is "
            f"grey. Image 2 is a creature of a side-scrolling game. Draw the creature of image 2 {n} times - one in place of each mannequin, at that mannequin's place and size on the "
            "sheet, in exactly that mannequin's pose: every leg where the mannequin's leg of the same colour is and bent as it is bent, each paw exactly where the mannequin's paw is (a "
            "paw that is off the ground in the mannequin is off the ground by as much), the back, the chest and the neck where the mannequin's are. The legs that are red on the mannequin "
            "are drawn in front of the body; those that are blue behind it and a little darker. The mannequin has been given this creature's own proportions: its legs are exactly as "
            "LONG as the mannequin's legs, its body as deep, its back at the same height - do not make the legs longer or shorter than the mannequin's. It is the creature of image 2 "
            "with its own build, its own head and face, its own coat and markings - and its own TAIL, as in image 2, swaying a little from frame to frame. "
            f"It is the same creature in all {n}: the same colours, the same markings, the same drawing style and line as image 2, the same size - only its legs change, and its tail a "
            "little. NOTHING of the mannequin shows in the finished sheet: none of its grey, red or blue, none of its smooth bare shape - only the creatures. Each one whole, none "
            "touching another or the sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")


def person_prompt(n):
    c, r = GRID[n]; rows = f"in {r} row{'s' if r > 1 else ''} of {c} - {n} moments of one walking step, read left to right{', top row first' if r > 1 else ''}"
    return (f"Image 1 is a POSE SHEET: a plain bald MANNEQUIN of a person shown {n} times, {rows}. It has no hair, no face and no clothes - it shows only the pose. In every one it walks "
            "to the RIGHT, its body turned a little toward the viewer. Its RIGHT arm and RIGHT leg - the ones nearer the viewer - are RED; its LEFT arm and LEFT leg - the far ones - are "
            f"BLUE; the rest of it is grey. Image 2 is a character of a side-scrolling game. Draw the character of image 2 {n} times - one in place of each mannequin, at that mannequin's "
            "place and size on the sheet, in exactly that mannequin's pose: each arm and each leg where the mannequin's limb of the same colour is and bent as it is bent, each foot "
            "exactly where the mannequin's foot is (a foot that is off the ground in the mannequin is off the ground by as much), the head, the shoulders and the hips where the "
            "mannequin's are, the head turned as the mannequin's head is turned. The body under the clothes IS the mannequin's: the same height, legs and arms exactly as long. On it, "
            "the character of image 2 with its own head and face, its own hair, its own clothes and everything it wears, all as in image 2; hair and loose cloth (a cloak, a skirt, a "
            "braid, a strap) sway a little with the step and hang naturally over the moving limbs. "
            f"It is the same character in all {n}: the same face, the same hair, the same clothes and colours, the same drawing style and line as image 2, the same size. "
            "NOTHING of the mannequin shows in the finished sheet: none of its grey, red or blue, no bald head, no bare body - only the characters. Each one whole, none touching "
            "another or the sheet's edge. Plain pure white background: no ground, no shadow, no lines, no numbers, no text.")


def walk(s, d, root, args):
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
    with one between its forelegs, while this was the white key alone. `ai`: () → the AI cut-out of `im` (kept from an earlier `cut`: ai_mask), asked for only
    when some white of 12 px or more is shut in - with none, the AI could take nothing away. SPRITECAST_KEY=white: only white as pure as the paper is taken
    for paper. With no onnxruntime it stops (CL.NO_ORT), as a character's frames do: it fell back on the white key by itself and nobody knew."""
    m = CL.white_key(im); x = np.asarray(im.convert('RGB')).astype(int)
    if os.environ.get('SPRITECAST_KEY') == 'white':
        hl, hn = ndimage.label(m & (x.min(2) >= 246) & (x.max(2) - x.min(2) < 8)); big = np.bincount(hl.ravel()) >= 30; big[0] = False
        return m & ~big[hl]
    if not CL._have_ort(): sys.exit(CL.NO_ORT.format(py=sys.executable))
    paper = (x.min(2) > 232) & (x.max(2) - x.min(2) < 18); hl, hn = ndimage.label(m & paper)                  # (paper is white_key's own near-white: m & paper is
    if not hn or np.bincount(hl.ravel())[1:].max() < 12: return m                                             # exactly the white shut in)
    hl, hn = ndimage.label(m & paper & ~ndimage.binary_dilation(ai() if ai else CL.ai_key(im), iterations=3)); big = np.bincount(hl.ravel()) >= 12; big[0] = False
    return m & ~big[hl]


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


def cut_walk(s, d):
    """the drawn walk cut by the guide's cells: every frame keeps its place in its cell (the body does not jump about), its lowest point on the ground"""
    n = s['frames']; src = d / 'walk-drawn.png'; im = Image.open(src).convert('RGB'); info = json.loads((d / 'walk-guide.json').read_text())
    if info.get('n', n) != n: sys.exit(f'cut: walk-guide.png is of {info["n"]} frames, the spec\'s "frames" is {n} - put it back, or run `mannequin` and `walk --again`')
    if im.size != SHEET: im = im.resize(SHEET, Image.LANCZOS)
    fr = []; moved = []; guide = Image.open(d / 'walk-guide.png').convert('RGB')
    P = HEAD_MAX if s['person'] else 0                     # (a person's frames are moved across on a canvas this much wider each side: nothing is cut off)
    for i, (cx, cy, cw, ch) in enumerate(cells(n)):
        c = im.crop((cx, cy, cx + cw, cy + ch)); m = key(c, lambda: ai_mask(src, im, (cx, cy, cx + cw, cy + ch))); lab, cnt = ndimage.label(m)
        if cnt > 1:                   # every piece stays (a drop, a leaf, a wisp of mist) but the ones at the cell's left or right edge: a neighbour's nose or tail come over it
            size = np.bincount(lab.ravel()); size[0] = 0; edge = np.zeros(cnt + 1, bool); edge[np.concatenate([lab[:, 0], lab[:, -1]])] = True
            edge[0] = False; edge[int(np.argmax(size))] = False; m = m & ~edge[lab]
        if not lab.any() or np.bincount(lab[m])[1:].max(initial=0) < 0.05 * cw * ch:          # (a drawn figure fills its cell as the mannequin does: 15-25 % of it)
            sys.exit(f'cut: frame {i + 1} of the walk (row {i // GRID[n][0] + 1}, column {i % GRID[n][0] + 1} of walk-drawn.png) has no figure in it - the drawing has fewer '
                     f'than {n}, or one is out of its place. Look at walk-drawn.png; draw it again with `walk --again` (PAID)')
        f = cut_out(c, m); dx = 0
        if s['person']:               # a person's drawing sits where it likes across its cell (a cloak behind pushes the body forward, by a different amount each frame - 17 to 49 px
            gm = np.asarray(guide.crop((cx, cy, cx + cw, cy + ch))).min(2) < 245                     # on a guard and a herbalist): each frame is moved so that its HEAD is over the mannequin's
            ys = np.nonzero(gm.any(1))[0]; hw = max((w[1] - w[0] for w in map(widest, gm[ys[0]:ys[0] + round(0.15 * (ys[-1] - ys[0]))]) if w), default=0)
            hg, hm = head_x(gm, 0.4 * hw), head_x(m, 0.4 * hw)                                       # (the crown: a row 40 % as wide as the mannequin's bald head)
            dx = 0 if hg is None or hm is None else int(np.clip(round(hg - hm), -P, P)); moved.append(dx)
            w = Image.new('RGBA', (cw + 2 * P, ch), (0, 0, 0, 0)); w.paste(f, (P + dx, 0)); f = w
        fr.append((f, f.getbbox()))
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
    if (d / 'walk-drawn.png').exists(): cut_walk(s, d)
    if s['person'] and (d / 'design.png').exists(): cut_stand(s, d)
    for kind in s['sheets']:
        if (d / f'{kind}-drawn.png').exists(): cut_sheet(s, d, kind)


def preview(s, d, root, args):
    """out/preview.gif: the walk moving at its own step over marked ground (do its paws slide?), then each sheet's four frames"""
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
    ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', action='store_true'); A = ap.parse_args(); S, D, ROOT = load(A.spec)
    if A.step == 'sheet':
        if not A.kind: sys.exit('sheet: which one? `creature.py sheet MON.json hurt`')
        sheet(S, D, ROOT, A, A.kind)
    else: {'design': design, 'mannequin': mannequin, 'walk': walk, 'cut': cut, 'preview': preview}[A.step](S, D, ROOT, A)
