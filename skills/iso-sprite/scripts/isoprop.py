"""iso-sprite: an isometric game prop at its real size and the exact 2:1 angle — a 3D block guide rendered with an isometric camera, an
image model redrawing it in your art style, then cut out, fitted back onto the guide, its shadow baked and its anchor measured.

    python isoprop.py render  SPEC.json            free: the guide (render.png), its shadow, the model's input (input.png)
    python isoprop.py draw    SPEC.json [--yes]    PAID: one image-model call → drawn.png (prints the cost; --yes to spend it)
    python isoprop.py finish  SPEC.json            sprite.png, shadow.png, sprite.json (anchor, footprint, scale, shadow offset)
    python isoprop.py preview SPEC.json            preview.png: the sprite and its shadow on a tiled floor
    python isoprop.py model   SPEC.json [--yes]    PAID (Tripo): a detailed 3D model from the description, put in the spec in place of the
                                                   blocks (kept as blocks_draft) at the same real size → then `yaws`, `render` as usual
    python isoprop.py yaws    SPEC.json            free: the model turned 0/90/180/270° side by side (yaws.png), to set model.yaw
    python isoprop.py try     [EXAMPLE] [--out DIR]  free, no key: a bundled example's guide rendered here and finished → preview.png

Output goes to <the spec's folder>/<spec name>/ (or --out DIR); a spec with several `views` gets a folder per view (turn-<deg>/).
`draw` never overwrites an existing drawn.png (pass --again).
Environment: OPENAI_API_KEY (draw only); TRIPO_API_KEY (model only); ISO_SPRITE_MODEL (default gpt-image-2.5-sunburst), ISO_SPRITE_QUALITY (low|medium|high, default high).
"""
import argparse, base64, json, math, os, sys, time, urllib.error, urllib.request, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import browser as BROWSER  # noqa: E402
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
STYLES = HERE.parent / 'styles'
MAGENTA = (255, 0, 255)
PRICE = {'image_in': 8e-6, 'text_in': 5e-6, 'image_out': 30e-6}       # USD per token (OpenAI, gpt-image-2.5)
# camera presets: pitch = degrees the camera looks down, yaw = how far the prop is turned (45: its footprint a diamond, 90: square on,
# its +y side toward the viewer); words = how the prompt names the view
CAMERAS = {
    'iso-2:1':  {'pitch': 30, 'yaw': 45, 'words': '2:1 isometric (dimetric) view - the floor tiles twice as wide as tall'},
    'isometric': {'pitch': 35.264, 'yaw': 45, 'words': 'true isometric view - the three axes 120 degrees apart'},
    'topdown':  {'pitch': 50, 'yaw': 90, 'words': 'three-quarter top-down view, its front square to the viewer'},
    'front':    {'pitch': 12, 'yaw': 90, 'words': 'front view from slightly above, as in a side-scrolling game'},
}


def camera(spec):
    c = spec.get('camera', 'iso-2:1')
    if isinstance(c, str):
        if c not in CAMERAS: sys.exit(f'camera: "{c}" - one of {", ".join(CAMERAS)} or {{"pitch": deg, "yaw": deg}}')
        return dict(CAMERAS[c])
    return {'pitch': c.get('pitch', 30), 'yaw': c.get('yaw', 45), 'words': f"a view {c.get('pitch', 30)} degrees from above, orthographic"}


def views(spec, d):
    """[(turn, its folder)]: one view in the prop's own folder, several in turn-<deg>/ folders (the first is drawn first)"""
    if spec.get('character') is not None:                       # turned so the total yaw is the facing's, whatever the preset
        ds = spec['character'].get('directions') or ['south-east', 'south-west', 'north-east', 'north-west']
        base = camera(spec)['yaw']
        return [(DIRS[x] - base, d / x) for x in ds]
    vs = spec.get('views') or [0]
    return [(v, d) for v in vs] if len(vs) == 1 else [(v, d / f'turn-{v}') for v in vs]


# a character's facing → the yaw that turns the mannequin (built facing +y) that way on screen
DIRS = {'south': 90, 'south-east': 135, 'east': 180, 'north-east': 225, 'north': 270, 'north-west': 315, 'west': 0, 'south-west': 45}
FACING_WORDS = {'south': 'facing straight toward the viewer', 'south-east': 'facing down-right, a three-quarter front view',
                'south-west': 'facing down-left, a three-quarter front view', 'east': 'facing right, seen from the side',
                'west': 'facing left, seen from the side', 'north-east': 'facing up-right, away from the viewer - a three-quarter back view',
                'north-west': 'facing up-left, away from the viewer - a three-quarter back view', 'north': 'facing straight away from the viewer, seen from the back'}


# a pose: per limb two directions, each (out, fwd) in degrees - first turned out to the side, then swung forward from hanging
# straight down: upper arm and forearm, thigh and shin. side +1 is the figure's left (its +x side), -1 its right
POSES = {
    'stand':  {'arm': {1: ((5, 0), (5, 5)), -1: ((5, 0), (5, 5))}},
    'wave':   {'arm': {1: ((80, 10), (165, 15)), -1: ((5, 0), (5, 5))}},
    'point':  {'arm': {1: ((8, 80), (8, 88)), -1: ((5, 0), (5, 5))}},
    'hold':   {'arm': {1: ((6, 8), (-35, 70)), -1: ((6, 8), (-35, 70))}},            # hands together in front: a cup, a tray, a book
    'arms-crossed': {'arm': {1: ((14, 22), (-72, 78)), -1: ((14, 22), (-72, 70))}},
    'walk':   {'arm': {1: ((6, -20), (6, -12)), -1: ((6, 22), (6, 40))},
               'leg': {1: ((2, 24), (2, 6)), -1: ((2, -16), (2, -40))}},                # mid-stride: the +x leg forward
}


SIDES = {'left': 1, 'right': -1}          # the figure's own left and right


def resolve_pose(p):
    """a preset name, or {"base": preset, "arm": {"left"|"right": [[out, fwd], [out, fwd]]}, "leg": {...}}: the preset with those limbs
    set - upper arm then forearm, thigh then shin, each turned `out` degrees to its side, then swung `fwd` degrees forward (negative:
    back, or across the body for `out`). So an agent can change a pose by numbers and check it in the free render"""
    if isinstance(p, str):
        if p not in POSES: sys.exit(f'character pose: one of {", ".join(POSES)}, or a dict (see spec.md)')
        return POSES[p]
    base = json.loads(json.dumps(resolve_pose(p.get('base', 'stand')), default=list))
    pose = {limb: {int(k): v for k, v in base.get(limb, {}).items()} for limb in ('arm', 'leg')}
    for limb in ('arm', 'leg'):
        for side, v in (p.get(limb) or {}).items():
            if side not in SIDES: sys.exit(f'character pose: {limb} sides are "left" and "right"')
            pose[limb][SIDES[side]] = (tuple(v[0]), tuple(v[1]))
    return pose


def _dir(out, fwd, s):
    """a limb's direction: hanging straight down, turned `out` degrees to its side (s), then swung `fwd` degrees forward (+y)"""
    o, f = math.radians(out), math.radians(fwd)
    vx, vy, vz = s * math.sin(o), 0.0, -math.cos(o)
    return vx, vy * math.cos(f) - vz * math.sin(f), vy * math.sin(f) + vz * math.cos(f)


def mannequin(c):
    """a plain figure of `height` m from blocks and limb segments, facing +y, centred on a 0.5 m footprint, in a `pose` (POSES).
    `build`: slim | average | broad"""
    H = float(c.get('height', 1.7)); w = {'slim': 0.88, 'average': 1.0, 'broad': 1.15}.get(c.get('build', 'average'), 1.0)
    pose = resolve_pose(c.get('pose', 'stand'))
    cx = cy = 0.25; skin, cloth, dark, shoe = '#e2b99a', '#8a94a6', '#4a4f5c', '#3a2e28'
    box = lambda x0, x1, y0, y1, h0, h1, col, **k: dict(box=[cx + x0, cx + x1, cy + y0, cy + y1, h0, h1], color=col, **k)
    ball = lambda p, r, col: dict(box=[cx + p[0] - r, cx + p[0] + r, cy + p[1] - r, cy + p[1] + r, p[2] - r, p[2] + r], color=col, shape='sphere')
    seg = lambda a, b_, r, col: dict(seg=[cx + a[0], cy + a[1], a[2], cx + b_[0], cy + b_[1], b_[2]], r=r, color=col)
    step = lambda p, d, l: (p[0] + d[0] * l, p[1] + d[1] * l, p[2] + d[2] * l)
    hip, sh, leg, arm = 0.052 * H * w, 0.118 * H * w, 0.036 * H * w, 0.022 * H * w
    b = [box(-0.098 * H * w, 0.098 * H * w, -0.055 * H, 0.055 * H, 0.46 * H, 0.60 * H, cloth),  # hips and waist
         box(-sh, sh, -0.06 * H, 0.06 * H, 0.58 * H, 0.82 * H, cloth),                        # chest and shoulders
         box(-0.022 * H, 0.022 * H, -0.022 * H, 0.022 * H, 0.81 * H, 0.86 * H, skin, axis='h'),  # neck
         box(-0.055 * H, 0.055 * H, -0.064 * H, 0.06 * H, 0.855 * H, H, skin, shape='sphere'),  # head
         box(-0.01 * H, 0.01 * H, 0.05 * H, 0.072 * H, 0.905 * H, 0.935 * H, skin)]            # nose: which way it faces
    for s in (1, -1):
        (o1, f1), (o2, f2) = pose.get('leg', {}).get(s, ((0, 0), (0, 0)))
        hp = (s * hip, 0.0, 0.48 * H); kn = step(hp, _dir(o1, f1, s), 0.225 * H); an = step(kn, _dir(o2, f2, s), 0.215 * H)
        b += [seg(hp, kn, leg, dark), ball(kn, leg, dark), seg(kn, an, leg * 0.92, dark),
              seg((an[0], an[1] - 0.03 * H, an[2] - 0.015 * H), (an[0], an[1] + 0.085 * H, an[2] - 0.015 * H), leg * 0.75, shoe)]   # the foot, toes forward
        (o1, f1), (o2, f2) = pose['arm'][s]
        sp = (s * (sh + arm * 0.5), 0.0, 0.8 * H); el = step(sp, _dir(o1, f1, s), 0.17 * H); wr = step(el, _dir(o2, f2, s), 0.15 * H)
        b += [ball(sp, arm * 1.15, cloth), seg(sp, el, arm, cloth), ball(el, arm, cloth), seg(el, wr, arm * 0.9, cloth),
              ball(step(wr, _dir(o2, f2, s), 0.03 * H), arm * 1.25, skin)]                    # the hand
    lo = min(min(x['box'][4], x['box'][5]) if 'box' in x else min(x['seg'][2], x['seg'][5]) - x['r'] for x in b)   # feet on the ground
    for x in b:
        if 'box' in x: x['box'][4] -= lo; x['box'][5] -= lo
        else: x['seg'][2] -= lo; x['seg'][5] -= lo
    return b


def load_spec(path):
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    if spec.get('character') is not None:                       # a person: the mannequin as the guide, one view per facing
        c = spec['character'] = spec['character'] or {}
        spec.setdefault('footprint', [0.5, 0.5]); spec['blocks'] = mannequin(c) + spec.get('blocks', [])
        spec.setdefault('loose', True); spec.setdefault('anchor', 'center')
        bad = [d for d in c.get('directions', []) if d not in DIRS]
        if bad: sys.exit(f'character directions: {bad} - use {", ".join(DIRS)}')
    for k in ('name', 'footprint', 'description'):
        if k not in spec: sys.exit(f'spec: "{k}" is missing')
    if not spec.get('blocks') and not spec.get('model'): sys.exit('spec: give "blocks" or a "model"')
    if spec.get('model'):
        g = Path(spec['model']['glb']); spec['model']['glb'] = str(g if g.is_absolute() else (Path(path).parent / g).resolve())
    return spec


def out_dir(args, spec):
    d = Path(args.out) if args.out else Path(args.spec).resolve().parent / spec['name']
    d.mkdir(parents=True, exist_ok=True); return d


# --- render (Playwright drives the page in render.html; files are served from memory, no web server) ----------------------------------
def render(spec, d):
    from playwright.sync_api import sync_playwright
    cam = camera(spec)
    glb = spec.get('model', {}).get('glb')
    page_spec = json.loads(json.dumps(spec))
    if glb: page_spec['model']['glb'] = 'http://iso-sprite.local/asset/model.glb'

    def serve(route):
        p = route.request.url.split('iso-sprite.local/', 1)[1]
        if p == 'asset/model.glb': return route.fulfill(path=glb, content_type='model/gltf-binary')
        f = (HERE / p).resolve()
        if HERE not in f.parents and f != HERE: return route.abort()
        route.fulfill(path=str(f), content_type='text/html' if f.suffix == '.html' else 'text/javascript')

    with sync_playwright() as pw:
        browser = BROWSER.launch(pw)
        page = browser.new_page()
        page.route('http://iso-sprite.local/**', serve)
        page.goto('http://iso-sprite.local/render.html')
        page.wait_for_function('window.ready === true', timeout=30000)
        W, D = spec['footprint']
        for turn, vd in views(spec, d):
            vd.mkdir(parents=True, exist_ok=True)
            page_spec['camera'] = {'pitch': cam['pitch'], 'yaw': cam['yaw'] + turn}
            info = page.evaluate('(s) => window.setup(s)', page_spec)
            save = lambda url, name: (vd / name).write_bytes(base64.b64decode(url.split(',', 1)[1]))
            save(page.evaluate('() => window.shot()'), 'render.png')
            save(page.evaluate('() => window.shadowShot()'), 'render-shadow.png')
            top = max([x['box'][5] if 'box' in x else max(x['seg'][2], x['seg'][5]) + x.get('r', 0) for x in spec.get('blocks') or []]
                      + ([spec['model']['size'][2]] if spec.get('model') else [])) + 0.05
            save(page.evaluate('(t) => window.heightShot(t)', top), 'render-height.png')
            corners = [page.evaluate('([x, y]) => window.toCanvas(x, y, 0)', c) for c in ([0, 0], [W, 0], [W, D], [0, D])]
            lo = sorted(corners, key=lambda p: -p[1])                           # the anchor: the footprint's lowest corner on screen,
            near = lo[0] if lo[0][1] - lo[1][1] > 1 else [(lo[0][0] + lo[1][0]) / 2, (lo[0][1] + lo[1][1]) / 2]   # or its front edge's middle
            if spec.get('anchor') == 'center': near = page.evaluate('([x, y]) => window.toCanvas(x, y, 0)', [W / 2, D / 2])   # a person: the feet
            meta = {'size': info['size'], 'near': near, 'height_top': top, 'footprint_px': corners, 'px_per_m': spec.get('px_per_m', 256),
                    'camera': {'pitch': cam['pitch'], 'yaw': cam['yaw'] + turn}, 'turn': turn, 'light': spec.get('light', 'right')}
            low = clip_blocks(spec.get('blocks') or [], CONTACT_H)
            if low:
                page.evaluate('(s) => window.setup(s)', {**page_spec, 'blocks': low, 'model': None, 'keepFrame': True})
                save(page.evaluate('() => window.shadowShot()'), 'render-contact.png')
                page.evaluate('(s) => window.setup(s)', page_spec)                          # (back to the whole prop)
            (vd / 'render.json').write_text(json.dumps(meta, indent=1))
            model_input(vd)
            print(f'render: {vd / "render.png"}  ({info["size"][0]}x{info["size"][1]} px)')
        browser.close()


def clip_blocks(blocks, top):
    """the blocks cut off `top` m above the floor (boxes lowered, limbs shortened, what starts higher dropped): what stands on it"""
    out = []
    for x in blocks:
        x = json.loads(json.dumps(x))
        if 'box' in x:
            if x['box'][4] >= top: continue
            x['box'][5] = min(x['box'][5], top)
        else:
            (ax, ay, ah, bx, by, bh), r = x['seg'], x.get('r', 0)
            if min(ah, bh) - r >= top: continue
            if max(ah, bh) > top and ah != bh:                                     # cut the limb where it crosses `top`
                k = (top - ah) / (bh - ah)
                if ah > bh: ax, ay, ah = ax + (bx - ax) * k, ay + (by - ay) * k, top
                else: bx, by, bh = ax + (bx - ax) * k, ay + (by - ay) * k, top
            x['seg'] = [ax, ay, ah, bx, by, bh]
        out.append(x)
    return out


def model_input(d):
    """the guide cropped and centred on magenta at the nearest size the image model takes (square, landscape or portrait)"""
    r = Image.open(d / 'render.png').convert('RGBA'); c = r.crop(r.getbbox())
    size = (1536, 1024) if c.width > c.height * 1.15 else (1024, 1536) if c.height > c.width * 1.15 else (1024, 1024)
    k = min(size[0] * 0.84 / c.width, size[1] * 0.84 / c.height); c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS)
    bg = Image.new('RGBA', size, MAGENTA + (255,)); bg.alpha_composite(c, ((size[0] - c.width) // 2, (size[1] - c.height) // 2))
    bg.convert('RGB').save(d / 'input.png')


# --- draw -----------------------------------------------------------------------------------------------------------------------------
def style_of(spec, spec_path):
    s = spec.get('style', 'cozy')
    p = STYLES / f'{s}.png' if (STYLES / f'{s}.png').exists() else Path(s) if Path(s).is_absolute() else Path(spec_path).parent / s
    if not p.exists(): sys.exit(f'style: {s} not found (a bundled name: {", ".join(x.stem for x in STYLES.glob("*.png"))}, or a path)')
    return p


def prompt_character(spec, first, yaw, light, look):
    name = next((k for k, v in DIRS.items() if v == yaw % 360), '')
    face = FACING_WORDS.get(name, 'turned as image 1')
    back = (' We see the character from BEHIND: the back of the head and hair, the back of every piece of clothing (straps, seams, hood, '
            'collar from behind) - NOT the face, NOT the front of the clothes; the whole body, head to feet, turned the same way.'
            if name.startswith('north') else '')
    again = (' Image 3 is this very character already drawn facing another way: draw exactly the same person - the same face, hair, '
             'body, clothes, colours and details - only turned as image 1 shows.') if first else ''
    return ("Image 1 is a 3D render of a plain mannequin standing, for a character sprite in a game, seen from the game's exact camera - "
            f"a {camera(spec)['words']}. The figure is {face}.{back}{again} Redraw the mannequin as {spec['description']} - standing relaxed "
            "in exactly the mannequin's pose: the same height and size on the canvas, the feet where its feet are, the body and the head "
            "turned exactly as the mannequin's (its small nose block shows where the face looks), arms hanging at the sides. Hair and "
            "clothes may go a little past the mannequin's outline, nothing else. "
            f"In exactly the art style of image 2: {look}. Take ONLY the style from image 2 - nothing of its content and NOT its camera "
            f"angle: the angle is image 1's. Light from the {light}. "
            "Only this one character on the plain flat solid magenta (#FF00FF) background, no floor, no shadow, no text.")


def prompt(spec, first=False, yaw=45):
    look = spec.get('look') or ('a clean, polished illustration halfway between pixel art and realism - believable material detail with smooth soft '
                                'shading and gentle highlights, crisp clean edges, a fine dark line only on the silhouette and main edges; '
                                'not pixel art, not a photograph')
    facing = f" ({spec['facing']})" if spec.get('facing') else ''
    light = 'upper left' if spec.get('light') == 'left' else 'upper right'
    if spec.get('character') is not None: return prompt_character(spec, first, yaw, light, look)
    again = (' Image 3 is this very object already drawn from another side: draw exactly that object - the same design, materials, '
             'colours and details - only seen from the side image 1 shows.') if first else ''
    return (f"Image 1 is a 3D render made of simple blocks of a prop for a game, seen from the game's exact camera - a "
            f"{camera(spec)['words']}{facing}.{again} "
            f"Redraw it as {spec['description']} - the piece fills the blocks of image 1 exactly: the same angle, size and position, every main "
            "edge where the blocks put it, nothing moved, turned or resized; round blocks are round things. "
            + (("The camera looks straight at the object's front: its front face is seen square on and its top from above; its left and "
                "right sides are NOT visible at all - no side faces, no corner turned toward the viewer. ") if yaw % 90 == 0 else '')
            + f"In exactly the art style of image 2: {look}. Take ONLY the style from image 2 - nothing of its content and NOT its camera "
            f"angle: the angle is image 1's. Light from the {light}. "
            "Only this one piece on the plain flat solid magenta (#FF00FF) background, no floor, no shadow, no text.")


def draw(spec, d, args):
    vs = views(spec, d); todo = [(t, vd) for t, vd in vs if args.again or not (vd / 'drawn.png').exists()]
    if args.only: todo = [(t, vd) for t, vd in todo if vd.name in args.only.split(',') or str(t) in args.only.split(',')]
    if not todo: return print('draw: every view is drawn already (--again to draw anew)')
    model = os.environ.get('ISO_SPRITE_MODEL', 'gpt-image-2.5-sunburst'); quality = os.environ.get('ISO_SPRITE_QUALITY', 'high')
    out_tok = {'low': 196, 'medium': 439, 'high': 1756}.get(quality, 1756)
    est = sum((2600 if vd == vs[0][1] else 3900) * PRICE['image_in'] + 450 * PRICE['text_in'] + out_tok * PRICE['image_out'] for _, vd in todo)
    print(f'draw: {len(todo)} view(s), {model}, quality {quality}, about ${est:.2f}')
    if not args.yes: return print('draw: not spent — run again with --yes')
    key = os.environ.get('OPENAI_API_KEY')
    if not key: sys.exit('draw: set OPENAI_API_KEY')
    for t, vd in todo:                                                         # the first view first: the others follow its drawing
        ref = vs[0][1] / 'drawn.png' if vd != vs[0][1] else None
        if ref is not None and not ref.exists(): sys.exit('draw: the first view has no drawing yet')
        draw_one(spec, vd, args, model, quality, key, ref)


def draw_one(spec, d, args, model, quality, key, ref):
    out = d / 'drawn.png'
    imgs = [d / 'input.png', style_of(spec, args.spec)] + ([ref] if ref else [])
    size = '%dx%d' % Image.open(imgs[0]).size
    yaw = json.loads((d / 'render.json').read_text()).get('camera', {}).get('yaw', 45)
    fields = {'model': model, 'prompt': prompt(spec, first=bool(ref), yaw=yaw), 'size': size, 'quality': quality, 'background': 'opaque', 'output_format': 'png', 'n': '1'}
    b = uuid.uuid4().hex; body = b''
    for k, v in fields.items(): body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for p in imgs:
        body += (f'--{b}\r\nContent-Disposition: form-data; name="image[]"; filename="{p.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                 + p.read_bytes() + b'\r\n')
    body += f'--{b}--\r\n'.encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': f'multipart/form-data; boundary={b}'})
    t = time.time()
    for attempt in range(4):
        try: j = json.load(urllib.request.urlopen(req, timeout=600)); break
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode(errors='replace')
            if e.code in (429, 500, 502, 503, 504) and attempt < 3: time.sleep(15 * (attempt + 1)); continue
            sys.exit(f'draw: HTTP {e.code} {msg}')
    out.write_bytes(base64.b64decode(j['data'][0]['b64_json']))
    u = j.get('usage', {}); i = u.get('input_tokens_details', {})
    cost = i.get('image_tokens', 0) * PRICE['image_in'] + i.get('text_tokens', 0) * PRICE['text_in'] + u.get('output_tokens', 0) * PRICE['image_out']
    print(f'draw: {out}  ({time.time() - t:.0f} s, ${cost:.3f})')


# --- a detailed 3D model (Tripo) in place of the blocks ----------------------------------------------------------------------------
TRIPO = 'https://openapi.tripo3d.ai/v3'


def tripo(method, path, key, body=None):
    req = urllib.request.Request(TRIPO + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={'Authorization': f'Bearer {key}', **({'Content-Type': 'application/json'} if body is not None else {})})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: sys.exit(f'model: Tripo HTTP {e.code} {e.read()[:300].decode(errors="replace")}')


def make_model(spec, d, args):
    """Tripo text-to-model from the description → <name>/tripo.glb; the spec file gets "model" (the blocks' real size) and its blocks
    become "blocks_draft". Arrangement and size still come from the blocks; the shape's detail from the model"""
    out = d / 'tripo.glb'
    if out.exists() and not args.again: return print(f'model: {out} is there already (--again to make it anew)')
    blocks = spec.get('blocks') or spec.get('blocks_draft') or []
    if spec.get('character') is not None or not blocks: sys.exit('model: needs a prop spec with blocks (they give its real size)')
    H = max(x['box'][5] if 'box' in x else max(x['seg'][2], x['seg'][5]) + x.get('r', 0) for x in blocks)
    W, D = spec['footprint']
    print(f'model: Tripo text-to-model {TRIPO_MODEL}, about 20-40 Tripo credits; fitted to {W} x {D} x {H:.2f} m')
    if not args.yes: return print('model: not spent - run again with --yes')
    key = os.environ.get('TRIPO_API_KEY')
    if not key: sys.exit('model: set TRIPO_API_KEY')
    prompt = (spec['description'] + '. A single object standing on its own: no base, no floor, no background, real-world proportions.')[:1024]
    tid = tripo('POST', '/generation/text-to-model', key, {'prompt': prompt, 'model': TRIPO_MODEL, 'texture': True, 'pbr': False,
                                                          'texture_quality': 'standard', 'face_limit': 80000})['data']['task_id']
    t0 = time.time()
    while True:
        r = tripo('GET', f'/tasks/{tid}', key)['data']; st = r.get('status')
        if st == 'success': break
        if st in ('failed', 'cancelled', 'banned', 'expired', 'unknown') or time.time() - t0 > 900: sys.exit(f'model: Tripo task {st}')
        time.sleep(8)
    url = r['output'].get('model_url') or r['output'].get('pbr_model') or r['output'].get('model')
    out.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=600).read())
    raw = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    raw['model'] = {'glb': f"{spec['name']}/tripo.glb", 'size': [W, D, round(H, 3)], 'yaw': 0}
    if 'blocks' in raw: raw['blocks_draft'] = raw.pop('blocks')
    Path(args.spec).write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"model: {out}  ({time.time() - t0:.0f} s, {r.get('credits_consumed', '?')} credits) - the spec now uses it; run `yaws` to turn it the right way")


def yaws(spec, d):
    """the model turned four ways, side by side, so its front can be put where the blocks had it (model.yaw)"""
    if not spec.get('model'): sys.exit('yaws: the spec has no model')
    cells = []
    for y in (0, 90, 180, 270):
        s = json.loads(json.dumps(spec)); s['model']['yaw'] = y; s.pop('views', None); s.pop('character', None)
        vd = d / f'yaw-{y}'; render(s, vd)
        im = Image.open(vd / 'render.png').convert('RGBA'); im = im.crop(im.getbbox()); cells.append((y, im))
    H = max(i.height for _, i in cells); W = sum(i.width for _, i in cells) + 40 * len(cells)
    sheet = Image.new('RGBA', (W, H + 40), (236, 228, 214, 255)); x = 20; dr = ImageDraw.Draw(sheet)
    for y, im in cells: sheet.alpha_composite(im, (x, 30 + H - im.height)); dr.text((x, 6), f'yaw {y}', fill=(0, 0, 0, 255)); x += im.width + 40
    sheet.convert('RGB').save(d / 'yaws.png'); print(f'yaws: {d / "yaws.png"} - set "model": {{"yaw": ...}} to the one facing as wanted')


# --- finish ---------------------------------------------------------------------------------------------------------------------------
TRIPO_MODEL = 'v3.1-20260211'
CONTACT_H = 0.12                       # m: what stands on the floor below this casts its shadow from the 3D guide (shoes, a pot's base)
ASPECT_OK, IOU_OK = 0.10, 0.80         # how far a drawing may stray from its guide before it is reported, not fitted


def soft_key(im, t0=28, t1=95):
    """the magenta out with a soft edge, its tint taken back out of the edge pixels (C = a·F + (1−a)·M)"""
    a = np.array(im.convert('RGB')).astype(float); H, W, _ = a.shape
    bg = np.median(np.array([a[2, 2], a[2, W - 3], a[H - 3, 2], a[H - 3, W - 3]]), 0)
    al = np.clip((np.abs(a - bg).max(2) - t0) / (t1 - t0), 0, 1)
    F = np.clip((a - (1 - al[..., None]) * bg) / np.maximum(al[..., None], 0.08), 0, 255)
    band = ndimage.distance_transform_edt(al > 0.5) <= 5                   # a red-and-blue cast left on the rim → grey
    tint = np.clip(np.minimum(F[..., 0], F[..., 2]) - F[..., 1], 0, None)
    k = np.where((band | (al < 0.95)) & (tint > 8), np.clip(tint / 40, 0, 1) * 0.85, 0)[..., None]   # the rim, and anything see-through (steam, glass)
    F = F * (1 - k) + (F @ np.array([0.299, 0.587, 0.114]))[..., None] * k
    al[al < 0.06] = 0
    return Image.fromarray(np.dstack([F, al * 255]).round().astype(np.uint8), 'RGBA')


def drop_specks(im, min_px=400):
    a = np.array(im); lab, n = ndimage.label(a[..., 3] > 0)
    if n > 1:
        sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        a[np.isin(lab, [j + 1 for j, z in enumerate(sz) if z < min_px])] = 0
    return Image.fromarray(a)


def drawn_shadow(alpha, heights, meta, gy, top):
    """the drawing's own silhouette laid on the ground with the guide's 3D heights: a point h m up casts its shadow a fixed step
    (h × the light's offset) away on screen, whatever its depth - so each drawn pixel takes the height of the guide under it (or of the
    nearest guide pixel, for hair or leaves past the guide) and is moved by that much. Both feet, a pot's base, every leg start their
    shadow exactly where they stand; the shape is the drawing's. Only what touches the floor has to be exact: higher up the height
    eases (from 10 % to 35 % of the object's height) into a smooth one read off the screen - how far above the feet' row (`gy`) a pixel
    is - so hair, hats and leaves cast a natural shadow instead of the blocks' corners. → (mask, margin) on the canvas grown by
    `margin` px every way"""
    P = math.radians(meta.get('camera', {}).get('pitch', 30)); pxm = meta['px_per_m']; side = -1 if meta.get('light') == 'left' else 1
    known = heights >= 0
    _, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
    hh = heights[iy, ix]                                                       # past the guide: the nearest guide pixel's height
    ys, xs = np.nonzero(alpha > 127); h3 = hh[ys, xs]
    flat = np.clip(gy - ys, 0, None) / (pxm * math.cos(P))                     # the smooth height: rows above the feet
    u = np.clip((h3 - 0.10 * top) / (0.25 * top), 0, 1); w = u * u * (3 - 2 * u)
    h = (1 - w) * h3 + w * flat
    sx = np.round(xs - 0.42 * side * h * pxm).astype(int)
    sy = np.round(ys + (math.cos(P) - 0.78 * math.sin(P)) * h * pxm).astype(int)
    M = int(pxm); out = np.zeros((alpha.shape[0] + 2 * M, alpha.shape[1] + 2 * M), bool)
    ok = (sx + M >= 0) & (sx + M < out.shape[1]) & (sy + M >= 0) & (sy + M < out.shape[0])
    out[sy[ok] + M, sx[ok] + M] = True
    return ndimage.binary_fill_holes(ndimage.binary_closing(out, iterations=2)), M


def finish(spec, d):
    meta = json.loads((d / 'render.json').read_text()); ren = Image.open(d / 'render.png').convert('RGBA')
    rb = ren.getbbox(); W, H = rb[2] - rb[0], rb[3] - rb[1]
    g = drop_specks(soft_key(Image.open(d / 'drawn.png')))
    g = g.crop(Image.fromarray((np.array(g)[..., 3] > 127).astype(np.uint8) * 255).getbbox())
    # laid back over the guide's box. A small difference in proportions is the drawing's own looseness: stretched away. A big one means
    # the model didn't follow the guide (drew another angle): never squeezed to fit - scaled evenly by height, centred, and reported
    off = (g.width / g.height) / (W / H) - 1
    if abs(off) <= ASPECT_OK and not spec.get('loose'): gw, gh, gx, gy = W, H, rb[0], rb[1]
    else: gh = H; gw = round(g.width * H / g.height); gx = rb[0] + (W - gw) // 2; gy = rb[1]
    g = g.convert('RGBa').resize((gw, gh), Image.LANCZOS).convert('RGBA')
    pad = max(0, -gx, gx + gw - ren.width)                                       # (a wider drawing may run past the render's canvas)
    canvas = Image.new('RGBA', (ren.width + 2 * pad, ren.height), (0, 0, 0, 0)); canvas.alpha_composite(g, (gx + pad, gy))
    ra = np.zeros((canvas.height, canvas.width), bool); ra[:, pad:pad + ren.width] = np.array(ren)[..., 3] > 0
    da = np.array(canvas)[..., 3] > 127; iou = float((ra & da).sum() / max(1, (ra | da).sum()))
    ok = (abs(off) <= ASPECT_OK or spec.get('loose')) and iou >= (IOU_OK if not spec.get('loose') else 0.6)
    nx, ny = meta['near']; nx += pad
    x0, y0, x1, y1 = min(rb[0] + pad, gx + pad), rb[1], max(rb[2] + pad, gx + pad + gw), max(rb[3], math.ceil(ny) + 1)
    if not ok:
        print(f'finish: WARNING - the drawing does not follow the guide (proportions {off:+.0%}, outline overlap {iou:.0%}); '
              'it was not squeezed to fit. Fix the description or the guide and draw again (--again).')
    canvas.crop((x0, y0, x1, y1)).save(d / 'sprite.png', optimize=True)
    mode = spec.get('shadow') or ('drawn' if spec.get('loose') else 'guide')
    if mode == 'drawn' and (d / 'render-height.png').exists():   # cast from the drawing with the guide's heights: hair, coats, leaves
        hm = np.array(Image.open(d / 'render-height.png').convert('RGBA')).astype(float)
        heights = np.full(canvas.size[::-1], -1.0)
        heights[:, pad:pad + hm.shape[1]] = np.where(hm[..., 3] > 250, (hm[..., 0] * 256 + hm[..., 1]) / 65535 * meta['height_top'], -1)
        m, M = drawn_shadow(np.array(canvas)[..., 3], heights, meta, ny, meta['height_top'] - 0.05)
        if (d / 'render-contact.png').exists():   # where it stands, the guide's own 3D shadow: it falls only away from the light
            ca = np.array(Image.open(d / 'render-contact.png').getchannel('A')) > 127
            m[M:M + ca.shape[0], M + pad:M + pad + ca.shape[1]] |= ca
        al = Image.fromarray(m.astype(np.uint8) * 255); sb = al.getbbox()
        sh = Image.new('RGBA', al.size, (0, 0, 0, 0)); sh.putalpha(al)
        sh.crop(sb).save(d / 'shadow.png', optimize=True); sb = (sb[0] - M, sb[1] - M, sb[2] - M, sb[3] - M)
    else:                                  # cast from the guide in 3D: exact for solid things
        mode = 'guide'
        sa = Image.open(d / 'render-shadow.png').getchannel('A'); sb = sa.getbbox()
        sh = Image.new('RGBA', sa.size, (0, 0, 0, 0)); sh.putalpha(sa.point(lambda v: 255 if v >= 128 else 0))
        sh.crop(sb).save(d / 'shadow.png', optimize=True); sb = (sb[0] + pad, sb[1], sb[2] + pad, sb[3])
    out = {
        'name': spec['name'], 'footprint_m': spec['footprint'], 'px_per_m': meta['px_per_m'],
        'camera': meta.get('camera'), 'turn': meta.get('turn', 0), 'light': meta.get('light', 'right'),
        'sprite': {'file': 'sprite.png', 'size': [x1 - x0, y1 - y0],
                   'anchor': [round((nx - x0) / (x1 - x0), 4), round((ny - y0) / (y1 - y0), 4)],
                   'anchor_px': [round(nx - x0, 1), round(ny - y0, 1)]},
        'shadow': {'file': 'shadow.png', 'from': mode, 'size': [sb[2] - sb[0], sb[3] - sb[1]], 'offset_px': [sb[0] - x0, sb[1] - y0]},
        'footprint_px': [[round(px + pad - x0, 1), round(py - y0, 1)] for px, py in meta['footprint_px']],
        'fit': {'ok': ok, 'proportions_off': round(off, 3), 'outline_overlap': round(iou, 3)},
        'notes': 'anchor = the footprint\'s lowest point on screen (its front corner, or the middle of its front edge when seen square on), '
                 'as a fraction of the sprite; footprint_px = the ground corners at (0,0), (W,0), (W,D), (0,D) in sprite px; draw shadow.png '
                 'at offset_px from the sprite\'s top-left, under everything.',
    }
    (d / 'sprite.json').write_text(json.dumps(out, indent=1))
    print(f'finish: {d / "sprite.png"}  {out["sprite"]["size"]} px, anchor {out["sprite"]["anchor"]}')


def preview(spec, d):
    """the sprite on a tiled floor (1 m tiles) with its shadow, for a quick look"""
    j = json.loads((d / 'sprite.json').read_text()); sp = Image.open(d / 'sprite.png'); sh = Image.open(d / 'shadow.png')
    pxm = j['px_per_m']; ox, oy = j['shadow']['offset_px']
    pad = int(pxm * 0.8); x0 = min(0, ox) - pad; y0 = min(0, oy) - pad; x1 = max(sp.width, ox + sh.width) + pad; y1 = max(sp.height, oy + sh.height) + pad
    im = Image.new('RGBA', (x1 - x0, y1 - y0), (236, 228, 214, 255)); dr = ImageDraw.Draw(im)
    (bx, by), (rx, ry), _, (lx, ly) = j['footprint_px']; W, D = j['footprint_m']
    ex, ey = ((rx - bx) / W, (ry - by) / W), ((lx - bx) / D, (ly - by) / D)   # a metre along each ground axis, on screen
    bx -= x0; by -= y0
    for i in range(-15, 16):
        for (u, v), (s, t) in ((ex, ey), (ey, ex)):
            p = (bx + i * u, by + i * v); dr.line([(p[0] - 30 * s, p[1] - 30 * t), (p[0] + 30 * s, p[1] + 30 * t)], fill=(214, 204, 188, 255), width=2)
    shadow = Image.new('RGBA', sh.size, (40, 30, 24, 0)); shadow.putalpha(sh.getchannel('A').point(lambda v: v * 0.32))
    im.alpha_composite(shadow, (ox - x0, oy - y0)); im.alpha_composite(sp, (-x0, -y0))
    im.convert('RGB').save(d / 'preview.png'); print(f'preview: {d / "preview.png"}')


def trial(name, out):
    """the whole way without a key: one of the bundled examples' specs, its guide rendered here, finished from the drawing that
    came with it (the only paid step, done once for the example) → preview.png"""
    import shutil
    ex = Path(__file__).resolve().parents[3] / 'examples'
    def ok(n):   # a single-view example with its drawing, and no 3D model it would need (the Tripo one's isn't in the repo)
        return (ex / f'{n}.json').exists() and (ex / n / 'drawn.webp').exists() and 'model' not in json.loads((ex / f'{n}.json').read_text())
    if not ok(name): sys.exit(f'try: no example "{name}" - one of ' + ', '.join(sorted(p.parent.name for p in ex.glob('*/drawn.webp') if ok(p.parent.name))))
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True); shutil.copy(ex / f'{name}.json', out / f'{name}.json')
    spec = load_spec(out / f'{name}.json'); d = out / name; d.mkdir(exist_ok=True)
    print(f'try: {name} - the guide is rendered here (free); the drawing is the one that came with the example')
    render(spec, d); Image.open(ex / name / 'drawn.webp').convert('RGB').save(d / 'drawn.png')   # kept as WebP in the repo (1/8 the size)
    finish(spec, d); preview(spec, d)
    print(f'try: done - open {d / "preview.png"} (the guide: {d / "render.png"}). Your own prop: write a spec like {out / (name + ".json")}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('step', choices=['render', 'draw', 'finish', 'preview', 'model', 'yaws', 'try'])
    ap.add_argument('spec', nargs='?', help='the spec (for `try`: an example name, reading_armchair by default)')
    ap.add_argument('--out'); ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', action='store_true')
    ap.add_argument('--only', help='draw only these views: facing names or turns, comma-separated (with --again to redraw one)')
    args = ap.parse_args()
    if args.step == 'try': trial(args.spec or 'reading_armchair', args.out or 'iso-sprite-try'); sys.exit()
    if not args.spec: ap.error('give the spec')
    spec = load_spec(args.spec); d = out_dir(args, spec)
    if args.step == 'model': make_model(spec, d, args)
    elif args.step == 'yaws': yaws(spec, d)
    elif args.step == 'render': render(spec, d)
    elif args.step == 'draw': draw(spec, d, args)
    else:
        for _, vd in views(spec, d): (finish if args.step == 'finish' else preview)(spec, vd)
