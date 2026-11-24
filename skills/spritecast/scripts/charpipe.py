"""charpipe: an 8-direction walking (and standing) game character from one illustration of them - a turnaround drawn from it, a 3D model
(Tripo, or Meshy), a rig and walk/idle animation (Tripo), the walk rendered with an isometric camera in 8 facings, and every frame drawn over its
render by an image model, four frames per call, in the illustration's look; then fitted back onto the renders, heads steadied, edges
cleaned, packed into strips.

Three OKs: the turnaround, the 3D (with its renders), the drawing (with the strips and the preview). With "draw": false, two: the turnaround and
the 3D; the 3D renders are the frames, softer - no image model draws them (it still draws the turnaround, ~$0.09, unless you give your
own rigged model as "rig_glb").

    python charpipe.py turnaround CHAR.json [--yes]   PAID (OpenAI, ~$0.09): front / right / back turnaround; the left view mirrored from the right
    python charpipe.py 3d         CHAR.json [--yes]   PAID (Tripo ~75 credits): model + rig + walk and idle, then rendered (free) - look before `draw`
    python charpipe.py draw       CHAR.json [--yes] [--only south,east,idle] [--again]
                                                      PAID (OpenAI, ~$0.10 a sheet of 4, ~$2 in all - every facing drawn; ~$1.3 with
                                                      "mirror": true, the west side flipped from the east): front first, the rest follow it;
                                                      when every facing is drawn, `finish` and `preview` run by themselves
  the same steps one at a time:
    python charpipe.py model      CHAR.json [--yes]   PAID (~30 Tripo credits; or Meshy with "modeler": "meshy"): the 3D model from the four views
    python charpipe.py rig        CHAR.json [--yes]   PAID (Tripo, ~45 credits): rig + walk + idle, made renderable, feet planted; then render
    python charpipe.py render     CHAR.json           free: the walk (frames × 8 facings) and the idle (8 facings), each with its 3D shadow
                                                      ("facings": 4 in the spec: the four diagonals only, about half the drawing;
                                                       "facings": "cardinal": south, east, north, west only)
    python charpipe.py redraw     CHAR.json [--yes]   PAID (~$0.11 a sheet): the sheets with a frame fitting its render under `redo_below`
                                                      (0.75) drawn again, up to twice; a facing still under it then settled with its
                                                      mirror pair (the better of the two flipped onto the other; south / north: low
                                                      frames drawn alone, once); the better drawing kept each time
    python charpipe.py finish     CHAR.json           free: frames fitted, steadied, cleaned → out/ strips, 3D shadows + character.json
    python charpipe.py sit        CHAR.json           free: the rig seated in 8 facings (render/sit-*), on nothing - the game's chair goes under
    python charpipe.py sit        CHAR.json --draw [--yes]
                                                      PAID (~$0.22, two sheets of 4): drawn like the standing views → out/sit-<facing>.png,
                                                      "sit" in character.json (each facing's seat point and height)
    python charpipe.py pack       CHAR.json           free: frames/ → out/ strips again (after touchup.py --apply; finish does it too);
                                                      --px 64: frames 64 px tall into out-64px/ instead
    python charpipe.py preview    CHAR.json           free: out/sheet.png (every frame), out/walk-<facing>.gif, out/walk-all.mp4 (ffmpeg)
    python charpipe.py facecheck  REF.json --with A.json,B.json [--apply]
                                                      free (needs mediapipe): the head for the height of A, B… against REF's, facing by
                                                      facing, by face landmarks; --apply writes the factors as "head_fit", then `finish`

Look at each paid step's input before running it (the turnaround before `3d`; the renders before `draw`). Keys in the environment:
OPENAI_API_KEY and TRIPO_API_KEY (MESHY_API_KEY only with "modeler": "meshy"). Files go to <the spec's folder>/<name>/.
"""
import argparse, base64, json, os, shutil, sys, time, urllib.error, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import browser as BROWSER  # noqa: E402
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); import charlib as CL   # noqa: E402
import touchup as TU   # noqa: E402
SPEC_PATH = None
DIRS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
# "facings": 4 in the spec - the four diagonals only (about half the drawing), or "cardinal" - south, east, north, west only (a game
# moving up, down, left and right): a game moving in 8 directions shows the nearest of them (export.py writes that map into every
# engine's files). The first one drawn is the one the rest follow: the front (south), or with the diagonals south-east
DIAGONALS = ['south-east', 'south-west', 'north-east', 'north-west']
CARDINALS = ['south', 'east', 'north', 'west']
FRONT = 'south'
PAIR = {'east': 'west', 'west': 'east', 'north-east': 'north-west', 'north-west': 'north-east', 'south-east': 'south-west', 'south-west': 'south-east'}
CW, CH = 384, 1024                                                            # a sheet's cell (4 across a 1536×1024 picture)
PRICE = {'image_in': 8e-6, 'text_in': 5e-6, 'image_out': 30e-6}


def load(path):
    s = json.loads(Path(path).read_text(encoding='utf-8')); base = Path(path).resolve().parent
    for k in ('name', 'description', 'design'):
        if k not in s: sys.exit(f'spec: "{k}" is missing')
    for k in ('design', 'face', 'photo', 'rig_glb', 'model_glb'):
        if s.get(k): s[k] = str((base / s[k]).resolve())
    s.setdefault('white_shoes', False); os.environ['SPRITECAST_WHITE_SHOES'] = '1' if s.get('white_shoes') else '0'; s.setdefault('head_up', 24); s.setdefault('shoulder_up', 15); s.setdefault('shoulder_wide', 1.05); s.setdefault('pitch', 30); s.setdefault('frames', 8); s.setdefault('neck', 0.16)
    global DIRS, FRONT
    s.setdefault('facings', 8)
    fc = {4: 'diagonal', '4': 'diagonal', 'diagonal': 'diagonal', 'diagonals': 'diagonal', 'cardinal': 'cardinal', 'cardinals': 'cardinal', 8: 8, '8': 8}.get(s['facings'])
    if fc is None: sys.exit('spec: "facings" is 8 (the default), 4 or "diagonal" (south-east, south-west, north-east, north-west) or "cardinal" (south, east, north, west)')
    s['facings'] = fc; DIRS = list(DIAGONALS) if fc == 'diagonal' else list(CARDINALS) if fc == 'cardinal' else ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']; FRONT = DIRS[0]
    # THE STANDING POSE: SpriteCast's own idle by default (idleclip.py - a relaxed stand, made here, added to the rig when rendering);
    # "idle_from": "tripo" keeps the rig's own idle clip (Tripo's: arms held out from the body more, little motion). A spec's own
    # "idle" (a clip and a moment) is used as given.
    s.setdefault('idle_from', 'spritecast')
    if s['idle_from'] not in ('spritecast', 'tripo'): sys.exit('spec: "idle_from" is "spritecast" (the default) or "tripo"')
    s.setdefault('walk', {'clip': 'walk', 't0': 0, 't1': 1.1835}); s.setdefault('idle', {'clip': 'idle_spritecast' if s['idle_from'] == 'spritecast' else 'idle', 't': 0})
    s.setdefault('frame_px', 256); s.setdefault('light', 'right'); s.setdefault('shadow', '3d'); s.setdefault('modeler', 'tripo'); s.setdefault('kind', 'person'); s.setdefault('redo_below', 0.75); s.setdefault('draw', True)
    # HOW DEEP THE SHADOWS ARE ("shadow_strength"): 1 as the light gives them - the painted set's default; a pixel set's is 1.5 (pixelart.py). Free: `pack` writes them again
    try: CL.SHADOW_STRENGTH = float(s.get('shadow_strength', 1))
    except (TypeError, ValueError): sys.exit('spec: "shadow_strength" is a number from 0.3 to 3 (1 as the light gives it)')
    if not 0.3 <= CL.SHADOW_STRENGTH <= 3: sys.exit('spec: "shadow_strength" is from 0.3 to 3 (1 as the light gives it; pixel art 1.5 by default)')
    # SOMETHING CARRIED ALL THE TIME ("hold" in the spec itself, not in one action): in the hand through the walk, the standing views and
    # every action that has no "hold" of its own. A figure with a thing in one hand is not its own mirror image - flipped, the thing
    # changes hands - so nothing is ever flipped for it ("mirror": "never", which a symmetrical character can ask for too).
    if s.get('hold'):
        s['hold'] = {'kind': s['hold']} if isinstance(s['hold'], str) else dict(s['hold'])
        if s['hold'].get('in_model') and not s['hold'].get('words'): sys.exit('spec: "hold" with "in_model": true (the thing is part of the rigged model) needs "words": what it is and in which hand, e.g. "In the LEFT hand: a black pistol."')
        if s.get('mirror') not in (None, False, 'never'): sys.exit('spec: with "hold" (something carried in one hand) no facing can be flipped from its pair - the thing would change hands. Take "mirror" out, or set it to "never"')
        if s.get('mix'): sys.exit('spec: with "hold" (something carried in one hand) facings cannot be mixed with their flipped pair ("mix") - the thing would change hands')
        s['mirror'] = 'never'
    s['never_flip'] = s.get('mirror') == 'never'
    m = s.get('mirror', False); m = [] if s['never_flip'] else ['west', 'north-west', 'south-west'] if m is True else (m or [])   # default: every facing drawn
    m = [x for x in m if x in DIRS]                       # (with four facings there is no west to flip)
    bad = [x for x in m if x not in PAIR or PAIR[x] in m]
    if bad: sys.exit(f'spec: "mirror" lists facings flipped from their pair (east/west, north-east/north-west, south-east/south-west), not both of a pair: {bad}')
    if s['kind'] not in ('person', 'animal'): sys.exit('spec: "kind" is "person" or "animal"')
    s.setdefault('anchor', 'ground')
    if s['anchor'] not in ('ground', 'soles'): sys.exit('spec: "anchor" is "ground" (the 3D ground under the middle) or "soles" (the bottom of the shoes)')
    d = base / s['name']
    # the renders' size: 1024 (the drawings are ~850 px tall - at 512 half their detail went), or what an earlier render was made at, so a
    # project rendered before keeps working; "render_px" in the spec to change it (then `render` and `finish` again - nothing is redrawn)
    rj = d / 'render/render.json'
    s.setdefault('render_px', (json.loads(rj.read_text()).get('px', 512) if rj.exists() else 1024)); CL.PX = s['render_px'] / 512
    for sub in ('turnaround', 'model', 'rig', 'render', 'draw', 'frames', 'out'): (d / sub).mkdir(parents=True, exist_ok=True)
    s['mix'] = [sorted((x, PAIR[x])) for x in (s.get('mix') or []) if x in PAIR]     # pairs mixed frame by frame (both drawn)
    s['actions'] = actions_of(s)
    if s['never_flip'] and s['mix']: sys.exit('spec: "mirror": "never" and "mix" (facings mixed with their flipped pair) contradict each other')
    s['mirrored'] = [] if s['never_flip'] else [x for x in mirror_choices(d, m) if not any(x in p for p in s['mix'])]   # (never: what an earlier `redraw` chose is left aside too)
    return s, d


def front_words():
    return 'walking toward the viewer' if FRONT == 'south' else f'walking {FRONT.replace("-", " ")}, toward the viewer and to the right'


def idle_groups():
    """the standing views, 4 to a sheet: the eight in two sheets, four (the diagonals or the cardinals) in one"""
    return (list(DIRS),) if len(DIRS) == 4 else (['south', 'south-east', 'south-west', 'east'], ['west', 'north-east', 'north-west', 'north'])


def mirror_choices(d, m):
    """the facings flipped from their pair: the spec's, then what `redraw` chose for a pair (draw/mirror.json: "<a>|<b>" → the flipped one,
    or '' for both drawn)"""
    m = list(m); f = d / 'draw/mirror.json'
    for key, target in (json.loads(f.read_text()) if f.exists() else {}).items():
        m = [x for x in m if x not in key.split('|')] + ([target] if target and target != 'best' else [])
    return m


def best_pairs(d, s=None):
    if (s or {}).get('never_flip'): return []
    f = d / 'draw/mirror.json'
    out = [k.split('|') for k, v in (json.loads(f.read_text()) if f.exists() else {}).items() if v == 'best']
    return out + [p for p in ((s or {}).get('mix') or []) if p not in out]


def set_mirror(s, d, a, target):
    f = d / 'draw/mirror.json'; ch = json.loads(f.read_text()) if f.exists() else {}
    ch['|'.join(sorted((a, PAIR[a])))] = target; f.write_text(json.dumps(ch, indent=1)); s['mirrored'] = mirror_choices(d, [x for x in s['mirrored'] if x not in (a, PAIR[a])])
    # (target: the facing flipped from the other, '' both drawn as they are, 'best' both drawn and mixed frame by frame)


def need(var):
    v = os.environ.get(var)
    if not v: sys.exit(f'set {var}')
    return v


def gate(args, what):
    print(what)
    if not args.yes: print('not spent - run again with --yes'); return False
    return True


# --- OpenAI images --------------------------------------------------------------------------------------------------------------------
class Refused(Exception):
    """OpenAI's safety check turned a picture down three times running (it does now and then, at random, on legs and short skirts)"""


def gpt(prompt, imgs, out, size):
    key = need('OPENAI_API_KEY'); model = os.environ.get('SPRITECAST_MODEL', 'gpt-image-2.5-sunburst')
    fields = {'model': model, 'prompt': prompt, 'size': size, 'quality': os.environ.get('SPRITECAST_QUALITY', 'high'), 'background': 'opaque',
              'output_format': 'png', 'n': '1'}
    b = uuid.uuid4().hex; body = b''
    for k, v in fields.items(): body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for p in imgs:
        body += (f'--{b}\r\nContent-Disposition: form-data; name="image[]"; filename="{Path(p).name}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                 + Path(p).read_bytes() + b'\r\n')
    body += f'--{b}--\r\n'.encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': f'multipart/form-data; boundary={b}'})
    for attempt in range(4):
        try: j = json.load(urllib.request.urlopen(req, timeout=600)); break
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode(errors='replace')
            if e.code in (429, 500, 502, 503, 504) and attempt < 3: time.sleep(15 * (attempt + 1)); continue
            if e.code == 400 and 'safety' in msg:                  # the same request often passes the next time
                if attempt < 2: print(f'  {Path(out).name}: turned down by OpenAI\'s safety check - asking again', flush=True); time.sleep(5); continue
                raise Refused(msg)
            sys.exit(f'OpenAI HTTP {e.code} {msg}')
    Path(out).write_bytes(base64.b64decode(j['data'][0]['b64_json']))
    u = j.get('usage', {}); i = u.get('input_tokens_details', {})
    return i.get('image_tokens', 0) * PRICE['image_in'] + i.get('text_tokens', 0) * PRICE['text_in'] + u.get('output_tokens', 0) * PRICE['image_out']


# --- turnaround -----------------------------------------------------------------------------------------------------------------------
TURN = ("A character turnaround sheet for 3D modeling and rigging of the character in image 1{face}. Three full-body views side by side on a "
        "plain white background - the FRONT view on the left, the RIGHT SIDE view in profile (facing right) in the middle, the BACK view on "
        "the right, all the same height and scale, standing on one ground line.\n"
        "The same clean A-pose in all three: standing straight with weight even on both feet, feet a little apart, arms straight and angled "
        "about 40 degrees away from the body so that there is clear space between the arms and the torso, hands relaxed and open, fingers "
        "together. The head perfectly level and upright, facing straight at the viewer in the front view, straight to the right in the side "
        "view, straight away in the back view. Mouth closed. Nothing held, no bag.\n"
        "Keep the character exactly as in image 1: the same face, the same figure and body proportions, the same outfit and colours. The "
        "hair worn BEHIND the shoulders and down the back in all three views, so the shoulders, arms and the outfit's sides are clear - "
        "nothing hanging beside or over the arms. The outfit drawn simply and cleanly for 3D: every garment solid and whole, the same on the "
        "left and right, its sides and back as clear as its front; no logos, no lettering.\n"
        "The character: {desc}\n"
        "The same illustration style as image 1: clean line art with a fine dark outline and smooth soft cel shading, neutral even "
        "lighting, no shadows on the ground, no text, no labels.")

TURN_ANIMAL = ("A turnaround sheet for 3D modeling of the animal in image 1{face}. Three full-body views side by side on a plain white "
        "background - the FRONT view on the left (the face toward the viewer), the animal's RIGHT SIDE in profile in the middle - its head on the RIGHT of the picture, "
        "its tail on the left (GPT once drew it facing left) - the BACK view on the right, all the same scale, standing on one ground line.\n"
        "The same plain standing pose in all three: on all four legs, the legs straight and a little apart so that each leg is clear and "
        "separate from the others (none hidden behind another in the side view), the paws flat on the ground, the head level and looking "
        "straight ahead, the tail held up and out behind, clear of the legs and the body - not curled around. Mouth closed. Nothing held.\n"
        "Keep the animal exactly as in image 1: the same face, markings, colours, proportions and any clothes. Clothes drawn simply and "
        "snugly, the same on the left and right, nothing hanging loose; no logos, no lettering.\n"
        "The animal: {desc}\n"
        "The same illustration style as image 1: clean line art with a fine dark outline and smooth soft cel shading, neutral even "
        "lighting, no shadows on the ground, no text, no labels.")


def cut_views(d):
    im = Image.open(d / 'turnaround/turn.png').convert('RGB'); a = np.array(im).astype(int)
    ink = (a.min(2) < 235).any(0); runs, i = [], 0
    while i < len(ink):
        if ink[i]:
            s = i
            while i < len(ink) and ink[i]: i += 1
            if i - s > 80: runs.append((s, i))
        i += 1
    if len(runs) != 3: sys.exit(f'turnaround: expected three figures, found {len(runs)} - draw it again (--again)')
    for (x0, x1), n in zip(runs, ['front', 'side', 'back']):
        im.crop((max(0, x0 - 40), 0, min(im.width, x1 + 40), im.height)).save(d / f'turnaround/{n}.png')
    Image.open(d / 'turnaround/side.png').transpose(Image.FLIP_LEFT_RIGHT).save(d / 'turnaround/left.png')   # the outfit is symmetrical


def turnaround(s, d, args):
    out = d / 'turnaround/turn.png'
    if out.exists() and not args.again: cut_views(d); return print(f'turnaround: {out} is there (--again to draw anew); views cut')
    if not gate(args, 'turnaround: one OpenAI picture, about $0.09'): return
    imgs = [s['design']] + ([s['face']] if s.get('face') else [])
    cost = gpt((TURN_ANIMAL if s['kind'] == 'animal' else TURN).format(face='. Image 2 is a close-up of the face to reproduce exactly' if s.get('face') else '', desc=s['description']), imgs, out, '1536x1024')
    cut_views(d); print(f'turnaround: {out} (${cost:.3f}) - check it (both sides the same, nothing hanging over the arms) before `model`')


# --- Meshy ----------------------------------------------------------------------------------------------------------------------------
def meshy(method, path, body=None):
    req = urllib.request.Request('https://api.meshy.ai/openapi/v1' + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={'Authorization': f'Bearer {need("MESHY_API_KEY")}', 'Content-Type': 'application/json'})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: sys.exit(f'Meshy HTTP {e.code} {e.read()[:300].decode(errors="replace")}')


def model_meshy(s, d, args, out):
    if not gate(args, 'model: Meshy multi-image-to-3d, about 30 Meshy credits, a few minutes'): return
    uri = lambda p: 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
    body = {'image_urls': [uri(d / f'turnaround/{n}.png') for n in ('front', 'side', 'left', 'back')], 'ai_model': 'latest', 'should_texture': True,
            'enable_pbr': False, 'texture_resolution': '2k', 'should_remesh': True, 'topology': 'quad', 'target_polycount': 40000, 'pose_mode': 'a-pose',
            'target_formats': ['glb'], 'multi_view_thumbnails': True}
    tid = meshy('POST', '/multi-image-to-3d', body)['result']; t0 = time.time()
    while True:
        t = meshy('GET', f'/multi-image-to-3d/{tid}')
        if t.get('status') in ('SUCCEEDED', 'FAILED', 'CANCELED') or time.time() - t0 > 1800: break
        time.sleep(15)
    if t.get('status') != 'SUCCEEDED': sys.exit(f"model: Meshy {t.get('status')} {t.get('task_error')}")
    fetch = lambda u, p: Path(p).write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=600).read())
    fetch(t['model_urls']['glb'], out)
    for k, u in (t.get('thumbnail_urls') or {}).items(): fetch(u, d / f'model/thumb-{k}.png')
    print(f"model: {out} ({time.time() - t0:.0f} s, {t.get('consumed_credits')} credits) - look at model/thumb-*.png from every side before `rig`")


# --- Tripo ----------------------------------------------------------------------------------------------------------------------------
TRIPO = 'https://openapi.tripo3d.ai/v3'


def tripo(method, path, body=None, raw=None, ctype='application/json'):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(TRIPO + path, data=data, method=method,
                                 headers={'Authorization': f'Bearer {need("TRIPO_API_KEY")}', **({'Content-Type': ctype} if data is not None else {})})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: sys.exit(f'Tripo HTTP {e.code} {path} {e.read()[:300].decode(errors="replace")}')


def tripo_run(path, body):
    tid = tripo('POST', path, body)['data']['task_id']; t0 = time.time()
    while True:
        r = tripo('GET', f'/tasks/{tid}'); d = r.get('data', r)
        if d.get('status') in ('success', 'failed', 'cancelled', 'banned', 'expired', 'unknown') or time.time() - t0 > 1800: break
        time.sleep(8)
    if d.get('status') != 'success': sys.exit(f"rig: Tripo {path} {d.get('status')}")
    return tid, d


def upload(path, name, ctype):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n').encode() \
        + Path(path).read_bytes() + f'\r\n--{b}--\r\n'.encode()
    return tripo('POST', '/files', raw=body, ctype=f'multipart/form-data; boundary={b}')['data']['file_token']


def model_tripo(s, d, args, out):
    if not gate(args, 'model: Tripo multiview-to-model, about 30 Tripo credits (40 if it has to be coloured again), a few minutes'): return
    tok = {v: upload(d / f'turnaround/{f}.png', f'{f}.png', 'image/png') for v, f in (('front', 'front'), ('right', 'side'), ('left', 'left'), ('back', 'back'))}
    tid, t = tripo_run('/generation/multiview-to-model', {'inputs': [{v: k} for v, k in tok.items()], 'model': 'v3.1-20260211', 'texture': True,
                                                          'pbr': False, 'face_limit': 60000})
    fetch = lambda u, p: Path(p).write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=600).read())
    for k, u in (t.get('output') or {}).items():
        if isinstance(u, str) and u.startswith('http'): fetch(u, out if 'model' in k else d / f'model/thumb-{k}.png')
    (d / 'model/tripo-task.txt').write_text(tid)       # `rig` rigs this task directly (no upload)
    credits = t.get('credits_consumed') or 0
    if grey_texture(out):                              # it happens: texture asked for, a flat grey one sent back
        print('model: Tripo sent the model back uncoloured - texturing it again from the four views (about 10 Tripo credits)')
        _, t = tripo_run('/models/texture', {'input': tid, 'model': 'v3.5-20260815', 'texture_prompt': {'images': [{v: k} for v, k in tok.items()]},
                                             'texture_quality': 'standard', 'pbr': False})
        url = next(u for k, u in (t.get('output') or {}).items() if isinstance(u, str) and u.startswith('http') and 'model' in k)
        fetch(url, d / 'model/textured.glb'); credits += t.get('credits_consumed') or 0
        if grey_texture(d / 'model/textured.glb'): sys.exit('model: still uncoloured after texturing again - try `model --again`')
    print(f"model: {out} ({credits} credits) - look at model/thumb-*.png before `rig`")


def grey_texture(glb):
    """True when the model's texture is one flat colour (Tripo's untextured stand-in is a plain grey)"""
    import io
    js, b = CL.read_glb(glb)
    if not js.get('images'): return True
    bv = js['bufferViews'][js['images'][0]['bufferView']]; o = bv.get('byteOffset', 0)
    a = np.asarray(Image.open(io.BytesIO(bytes(b[o:o + bv['byteLength']]))).convert('RGB').resize((256, 256)))
    return float(a.reshape(-1, 3).std(0).max()) < 12


def model(s, d, args):
    """the 3D model from the four views: Tripo by default (one 3D account for model and rig), or Meshy ("modeler": "meshy")"""
    out = d / 'model/model.glb'
    if out.exists() and not args.again: return print(f'model: {out} is there (--again to make it anew)')
    if not (d / 'turnaround/left.png').exists(): sys.exit('model: run `turnaround` first')
    out.parent.mkdir(parents=True, exist_ok=True)
    for f in ('tripo-task.txt', 'textured.glb'): (d / 'model' / f).unlink(missing_ok=True)
    (model_meshy if s['modeler'] == 'meshy' else model_tripo)(s, d, args, out)


def rig(s, d, args):
    if s['kind'] == 'animal': return print('rig: an animal needs none - its skeleton is found from the model as `render` runs')
    out = d / 'rig/rig.glb'
    if out.exists() and not args.again: return print(f'rig: {out} is there (--again to make it anew)')
    if not (d / 'model/model.glb').exists(): sys.exit('rig: run `model` first')
    presets = [n for n in s['actions'] if s['actions'][n]['clip'] in TRIPO_PRESETS][:3]       # (five a call: walk, idle and three more)
    skipped = [n for n in s['actions'] if n not in presets]
    if skipped: print(f'rig: not a Tripo preset (or more than three): {skipped} - give your own rig with those clips ("rig_glb")')
    if not gate(args, f'rig: Tripo rig (25) + walk and idle (20)' + (f' + {", ".join(presets)} ({10 * len(presets)})' if presets else '') +
                f', about {45 + 10 * len(presets)} Tripo credits'): return
    task = d / 'model/tripo-task.txt'; own = task.exists() and s['modeler'] != 'meshy'
    tok = task.read_text().strip() if own else upload(d / 'model/model.glb', 'model.glb', 'model/gltf-binary')
    # the rig's task is kept beside the model's: if the animations then fail (no credits left, a time-out) the next run takes the rig
    # that is paid for already instead of buying it again
    kept = d / 'rig/tripo-rig-task.txt'; kept.parent.mkdir(exist_ok=True); was = kept.read_text().split() if kept.exists() and not args.again else []
    if len(was) == 2 and was[0] == tok: rid = was[1]; print('rig: the rig made before is used (its animations are what is still to make)')
    else:
        tripo_run('/animations/rig-check', {'input': tok})
        rid, _ = tripo_run('/animations/rig', {'input': tok, 'model': 'v3.0-20260909', 'rig_type': 'biped', 'spec': 'mixamo', 'out_format': 'glb'}); kept.write_text(f'{tok} {rid}')
    _, a = tripo_run('/animations/retarget', {'input': rid, 'animations': ['preset:walk', 'preset:idle'] + [f"preset:{s['actions'][n]['clip']}" for n in presets],
                                                    'out_format': 'glb', 'animate_in_place': True})
    url = next(v for k, v in (a.get('output') or {}).items() if isinstance(v, str) and v.startswith('http') and 'model' in k)
    raw = d / 'rig/tripo.glb'; raw.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=600).read())
    turn = round(CL.facing(raw) / 90) * 90 % 360        # Tripo turns each model its own way (+x, -x...); the renders want +z
    if turn: CL.turn_root(raw, raw, turn)
    clips = CL.fix_tripo(raw, d / 'rig/named.glb'); feet = CL.plant_feet(d / 'rig/named.glb', out)
    if own and (d / 'model/textured.glb').exists():   # the colours from the second texturing: rig takes only the first task
        CL.retexture(out, d / 'model/textured.glb', out)
    print(f'rig: {out}  clips {clips}  turned {turn}°  feet corrected {feet}')
    if not args.no_render: render(s, d)


# --- render ---------------------------------------------------------------------------------------------------------------------------
def rig_file(s, d):
    """the rig GLB to render from: the spec's ("rig_glb", or rig/rig.glb) - with SpriteCast's idle added (idleclip.py, free) unless
    "idle_from" is "tripo": a copy beside it, <rig>-idle.glb, made again when the rig or idleclip.py is newer. A rig without Mixamo's
    bone names gets none, and the standing views fall back to its own "idle" clip, said aloud."""
    glb = Path(s.get('rig_glb') or d / 'rig/rig.glb')
    if s.get('kind') == 'animal' or s.get('idle_from') == 'tripo' or not glb.exists() or glb.stem.endswith('-idle'): return glb
    out = glb.with_name(glb.stem + '-idle.glb'); src = HERE / 'idleclip.py'
    if not out.exists() or out.stat().st_mtime < max(glb.stat().st_mtime, src.stat().st_mtime):
        import idleclip
        try: idleclip.add(glb, out, s.get('head_up', 24)); print(f'render: SpriteCast\'s idle added ("{idleclip.CLIP}") -> {out.name}')
        except ValueError as e:
            print(f'render: {e} - the standing views from the rig\'s own "idle"'); s['idle_from'] = 'tripo'
            if s['idle'].get('clip') == 'idle_spritecast': s['idle'] = {'clip': 'idle', 't': 0}
            return glb
    return out


def render(s, d, only=None):
    from playwright.sync_api import sync_playwright
    animal = s['kind'] == 'animal'
    if animal:      # a static model (the coloured-again copy if there is one, or the user's own: "model_glb"); its skeleton is found here
        glb = Path(s.get('model_glb') or next((p for p in (d / 'model/textured.glb', d / 'model/model.glb') if p.exists()), d / 'model/model.glb'))
        if not glb.exists(): sys.exit('render: run `3d` first (or give "model_glb")')
    else:
        glb = Path(s.get('rig_glb') or d / 'rig/rig.glb')
        if not glb.exists(): sys.exit('render: run `rig` first (or give "rig_glb")')
        glb = rig_file(s, d)

    def serve(route):
        p = route.request.url.split('spritecast.local/', 1)[1]
        if p == 'asset/rig.glb': return route.fulfill(path=str(glb), content_type='model/gltf-binary')
        f = (HERE / p).resolve()
        if HERE not in f.parents: return route.abort()
        route.fulfill(path=str(f), content_type='text/html' if f.suffix == '.html' else 'text/javascript')
    save = lambda url, p: Path(p).write_bytes(base64.b64decode(url.split(',', 1)[1]))
    with sync_playwright() as pw:
        br = BROWSER.launch(pw)
        pg = br.new_page(); pg.route('http://spritecast.local/**', serve); pg.goto('http://spritecast.local/render_char.html'); pg.evaluate('(f) => { window.shadowFlat = f }', s.get('shadow') == 'flat')          # ("shadow": "flat" - the one hard shape, as before 0.20)
        pg.wait_for_function('window.ready === true', timeout=30000); pg.evaluate('(r) => window.setRes(r)', CL.PX)
        if animal:
            info = pg.evaluate('([u, p, l]) => window.loadQuad(u, p, l)', ['http://spritecast.local/asset/rig.glb', s['pitch'], s['light']])
            print('render: skeleton found -', json.dumps({k: info[k] for k in ('bones', 'tail', 'faced', 'height', 'length')}))
            for dr in DIRS:
                for k, u in enumerate(pg.evaluate('(a) => window.quadFrames(...a)', [dr, s['frames'], False, True])): save(u, d / f'render/walk-{dr}-{k}.png')
                for k, u in enumerate(pg.evaluate('window.shadowShots')): save(u, d / f'render/walk-{dr}-{k}-s.png')
                save(pg.evaluate('(a) => window.quadFrames(...a)', [dr, s['frames'], True, True])[0], d / f'render/idle-{dr}.png')
                save(pg.evaluate('window.shadowShots')[0], d / f'render/idle-{dr}-s.png')
            br.close(); info['px'] = s['render_px']; (d / 'render/render.json').write_text(json.dumps(info, indent=1))
            return print(f"render: {d / 'render'} - look at them (walk-{FRONT}-*: four legs, the head forward, the tail behind) before `draw`")
        info = pg.evaluate('([u, p, l]) => window.load(u, p, l)', ['http://spritecast.local/asset/rig.glb', s['pitch'], s['light']])
        w, i = s['walk'], s['idle']
        old = json.loads((d / 'render/render.json').read_text()) if only and (d / 'render/render.json').exists() else {}
        if old.get('actions'): info['actions'] = old['actions']
        def put(hold, name, clip=None, t=0):                                 # a held thing built from shapes (render_char.html HOLDS), at real size, on its hand's bone
            if not hold or (isinstance(hold, dict) and hold.get('in_model')): return False       # (in_model: the rig has it already)
            h = {'kind': hold} if isinstance(hold, str) else dict(hold)
            h.setdefault('size', s.get('height_m', 1.7))
            if h['kind'] == 'umbrella': h.setdefault('grip', [0, 0, -90])
            if pg.evaluate('([k, o]) => window.setHold(k, o)', [h['kind'], h]):
                hi = pg.evaluate('window.holdInfo') or {}; fi = hi.get('fingers') or {}
                if os.environ.get('SPRITECAST_HOLD_DEBUG'): print('render: hold', json.dumps({k: hi.get(k) for k in ('thumb_rest', 'thumb_got')}))
                if fi: print(f"render: {name}: the {h.get('hand', 'right')} hand closed on the {h['kind']} - " + ', '.join(f"{k.lower()} {'/'.join(str(v) for v in e['deg'])}° ({'as its neighbours' if e.get('as_neighbours') else 'tip ' + format(e['tip_off_surface'] * 100, '+.1f') + '% of the height off its surface'})" for k, e in fi.items()) + (f"; the thumb on the face opposite the fingers: its last joint {hi['thumb']['joint_to_side'] * 100:.1f}% of the height from its place, its tip {hi['thumb']['tip_to_outer'] * 100:.1f}% from its, never nearer the handle's middle than {hi['thumb']['nearest_to_middle_in_radii']} of its radius" if hi.get('thumb') else ''))
                yaws = [0, 60, 120, 180, 240, 300, 1000, 1001]; shots = pg.evaluate('(a) => window.handShots(...a)', [clip or i['clip'], t, yaws])
                if shots:                                    # the hand from all round, with the thing (top) and without (bottom): LOOK before `draw`
                    import io
                    ims = [Image.open(io.BytesIO(base64.b64decode(u.split(',', 1)[1]))).convert('RGBA').resize((360, 360), Image.LANCZOS) for u in shots]
                    sh = Image.new('RGBA', (360 * len(yaws), 720), (235, 235, 235, 255))
                    for n, im in enumerate(ims): sh.alpha_composite(im, ((n % len(yaws)) * 360, (n // len(yaws)) * 360))
                    sh.convert('RGB').save(d / f'render/hand-{name}.png'); print(f"render: {name}: the hand from all round → {d / f'render/hand-{name}.png'} - LOOK at it: the fingers on one face of the handle, the thumb on the face opposite, nothing through it")
                return True
            print(f"render: {name}: can't hold \"{h['kind']}\" (known: umbrella, pistol, watergun) or the rig has no {h.get('hand', 'right')} hand bone"); return False
        carried = (not only) and put(s.get('hold'), 'walk', i['clip'], i['t'])
        pg.evaluate('(w) => { window.wantHeld = w; }', bool(carried))
        for dr in ([] if only else DIRS):                    # (--only <actions>: those alone, the walk's renders kept)
            for k, u in enumerate(pg.evaluate('(a) => window.frames(...a)', [w['clip'], dr, s['frames'], w['t0'], w['t1'], s['head_up'], s['shoulder_up'], s['shoulder_wide'], True])):
                save(u, d / f'render/walk-{dr}-{k}.png')
            for k, u in enumerate(pg.evaluate('window.shadowShots')): save(u, d / f'render/walk-{dr}-{k}-s.png')   # each frame's 3D shadow
            if carried:
                for k, u in enumerate(pg.evaluate('window.heldShots')): save(u, d / f'render/walk-{dr}-{k}-held.png')     # the carried thing alone
                for k, u in enumerate(pg.evaluate('window.bodyShots')): save(u, d / f'render/walk-{dr}-{k}-body.png')    # the body alone
            save(pg.evaluate('(a) => window.frames(...a)', [i['clip'], dr, 1, i['t'], i['t'] + 1e-4, s['head_up'], s['shoulder_up'], s['shoulder_wide'], True])[0], d / f'render/idle-{dr}.png')
            save(pg.evaluate('window.shadowShots')[0], d / f'render/idle-{dr}-s.png')
            if carried: save(pg.evaluate('window.heldShots')[0], d / f'render/idle-{dr}-held.png'); save(pg.evaluate('window.bodyShots')[0], d / f'render/idle-{dr}-body.png')
        pg.evaluate('() => { window.wantHeld = false; }'); pg.evaluate('() => window.clearHold()')
        if not only and not carried:                         # an earlier render's carried thing is not this one's
            for f in list((d / 'render').glob('walk-*-held.png')) + list((d / 'render').glob('walk-*-body.png')) + list((d / 'render').glob('idle-*-held.png')) + list((d / 'render').glob('idle-*-body.png')): f.unlink()
        clips = {c['name']: c['duration'] for c in info['clips']}
        for name, a in [(n, x) for n, x in s['actions'].items() if not only or n in only]:   # each action through its clip (a one-shot one from its first frame to its last)
            bt = a.get('between')            # "between": [from, to] - the poses that join one animation to another's first pose (no clip has them)
            if bt: ends, a = between_ends(s, a)
            if a['clip'] not in clips: print(f"render: {name}: no clip \"{a['clip']}\" in the rig ({', '.join(clips)}) - left out"); continue
            t0, t1, n = a['t0'], a['t1'] if a['t1'] is not None else clips[a['clip']], a['frames']
            t1x = t1 if a['loop'] else t0 + (t1 - t0) * n / max(1, n - 1)
            hold = a.get('hold'); small = isinstance(hold, dict) and (hold.get('in_model') or hold.get('kind') in ('pistol', 'watergun'))
            canvas = a.get('canvas') or ((round(1024 * max(1.0, float(a.get('trail_reach', 1) or 1)) / 64) * 64 if a.get('trail') else 768) if hold and not small else 512)       # (a pistol stays inside the walk's frame; a swing's trail reaches past the held thing's tip - its arc was cut by the 768 frame's edge)
            pg.evaluate('(px) => window.setCanvas(px)', canvas)       # (a held thing reaches past the walk's 512 px frame: 768 at the same scale)
            shown = put(hold, name, a['clip'], t0)
            pg.evaluate('(w) => { window.wantHeld = w; }', bool(shown))
            tr = effect_of(a.get('trail'), d.parent) if shown else None                      # "trail": what the swing leaves in the air, a sprite of its own
            pg.evaluate('(c) => window.setTrail(c)', tr)
            for f in (d / 'render').glob(f'{name}-*-t.png'): f.unlink()
            for dr in action_dirs(s) + [x for x in s['mirrored']]:
                shots = (pg.evaluate('(a) => window.blendFrames(...a)', [ends[0][0], ends[0][1], ends[1][0], ends[1][1], dr, n, s['head_up'], s['shoulder_up'], s['shoulder_wide'], True]) if bt
                         else pg.evaluate('(a) => window.frames(...a)', [a['clip'], dr, n, t0, t1x, s['head_up'], s['shoulder_up'], s['shoulder_wide'], True]))
                for k, u in enumerate(shots):
                    save(u, d / f'render/{name}-{dr}-{k}.png')
                for k, u in enumerate(pg.evaluate('window.shadowShots')): save(u, d / f'render/{name}-{dr}-{k}-s.png')
                for k, u in enumerate(pg.evaluate('window.heldShots')): save(u, d / f'render/{name}-{dr}-{k}-held.png')     # the held thing alone
                for k, u in enumerate(pg.evaluate('window.bodyShots')): save(u, d / f'render/{name}-{dr}-{k}-body.png')    # the body alone
                for k, u in enumerate(pg.evaluate('window.trailShots')):                                                  # the swing's trail alone (a slow frame has none)
                    if u: save(u, d / f'render/{name}-{dr}-{k}-t.png')
            pg.evaluate('() => { window.wantHeld = false; return window.setTrail(null); }')
            pg.evaluate('() => window.clearHold()'); pg.evaluate('() => window.setCanvas(512)')
            cut_ = [f.name for f in sorted((d / 'render').glob(f'{name}-*-t.png')) if (lambda im, b: b and (b[0] == 0 or b[1] == 0 or b[2] == im.width or b[3] == im.height))(*(lambda im: (im, im.getbbox()))(Image.open(f)))]
            if cut_: print(f'render: {name}: the trail runs off the frame in {len(cut_)} cells ({cut_[0]} ...) - give the action a bigger "canvas" than {canvas} (same scale, more room)')
            info.setdefault('actions', {})[name] = {'clip': a['clip'], 't0': t0, 't1': t1, 'frames': n, 'loop': a['loop'], 'canvas': canvas}
            print(f'render: {name} - {n} frames of "{a["clip"]}" {t0:.2f}-{t1:.2f} s, {len(DIRS)} facings')
        br.close()
    info['px'] = s['render_px']; (d / 'render/render.json').write_text(json.dumps(info, indent=1))
    print(f"render: {d / 'render'}  clips {[c['name'] for c in info['clips']]} - look at them (walk-{FRONT}-*) before `draw`")


# --- draw -----------------------------------------------------------------------------------------------------------------------------
def head_as_render(dr):
    """for an action whose head bows and turns with the motion (a slash, a crouch): the walk's 'eyes ahead, chin level' made the model lift
    the face to the viewer where the render bows it. Only where the face shows (south, south-east, south-west): measured on the rain girl's
    slash, all 64 frames each way, it took those facings from 0.786 to 0.837 overlap (17 → 20 of 24 frames passing) but the side and back
    views from 0.791 to 0.771 (a bowed head barely changes their outline, and the old words served them)"""
    if dr.startswith('north'): return ('seen from BEHIND as in the render (the back of the head, not the face), bowed and turned exactly as the render - '
                                       'NOT lifted, NOT turned toward the viewer')
    return ('turned and tilted EXACTLY as the render: bowed down where the render bows it, looking where the render looks - NOT lifted to face '
            'the viewer, NOT straightened up')


def head_words(dr, animal=False):
    if animal:
        if dr == 'south': return 'facing the viewer as in the render, the face and both ears seen from the front'
        if dr.startswith('north'): return 'seen from BEHIND as in the render: the back of the head, the ears from behind, the back and the tail - NOT the face'
        if dr in ('east', 'west'): return 'in profile exactly as the render, looking where it walks, NOT turned toward the viewer'
        return 'a three-quarter view exactly as the render, looking where it walks, NOT turned toward the viewer'
    if dr == 'south': return 'square to the viewer, not tilted, not turned, the eyes open and looking straight ahead (not down)'
    if dr.startswith('north'):
        return ('seen from BEHIND as in the render: the back of the head and the hair, the back of the clothes - NOT the face, NOT the front of '
                'the clothes; the whole body, head to feet, turned the same way')
    if dr in ('east', 'west'): return 'in profile exactly as the render, looking where the body walks, NOT turned toward the viewer, the eyes open'
    return 'a three-quarter view exactly as the render, looking where the body goes, NOT turned toward the viewer, the eyes open, the chin level'


def hand_of(hold):
    return 'left' if isinstance(hold, dict) and hold.get('hand') == 'left' else 'right'


def stem_of(name, dr, k=None):
    return f'{name}-{dr}' if k is None else f'{name}-{dr}-{k}'          # the standing views have one render a facing: idle-<facing>


def held_where(d, stem, cell):
    """where the held thing is in one cell's render, in words (seen from behind the model swaps the hands) - '' with no render of it"""
    hp, bp = d / f'render/{stem}-held.png', d / f'render/{stem}-body.png'
    if not hp.exists() or not bp.exists(): return ''
    H = np.asarray(Image.open(hp))[..., 3] > 128; B = np.asarray(Image.open(bp))[..., 3] > 128
    if H.sum() < 60 * CL.PX ** 2 or not B.any(): return ''
    V = _visible(d, stem)
    if V.sum() < max(60 * CL.PX ** 2, 0.15 * H.sum()):        # the body is in front of it (seen from behind, held before her): said so, or it gets drawn sticking out somewhere
        return f'cell {cell}: hidden behind the body - from this side the body covers it completely, so do NOT draw it'
    hy, hx = [v.mean() for v in np.nonzero(V)]; by, bx = [v.mean() for v in np.nonzero(B)]; ys = np.nonzero(B.any(1))[0]
    lr = 'to the LEFT of the body (the left side of the picture)' if hx < bx - 8 * CL.PX else 'to the RIGHT of the body (the right side of the picture)' if hx > bx + 8 * CL.PX else 'in front of or behind the body'
    ud = 'raised above the head' if hy < ys.min() + 0.15 * (ys.max() - ys.min()) else 'held low' if hy > by else 'at chest height'
    part = ' (partly hidden behind the body: draw only the part the render shows)' if V.sum() < 0.6 * H.sum() else ''
    return f'cell {cell}: {lr}, {ud}{part}'


def held_words(hold, d, name, dr, sides):
    """the sentences about what is held: what it is and in which hand, its parts, and where each cell's render has it"""
    if not hold: return ''
    hk = hold if isinstance(hold, str) else hold.get('kind'); hand = hand_of(hold); own = isinstance(hold, dict) and hold.get('words')
    held = ' ' + (own or HOLD_WORDS.get(hk, f'In the {hand} hand: the {hk} the render shows.').replace('RIGHT hand', f'{hand.upper()} hand'))
    if not own and (hk not in HOLD_WORDS or (isinstance(hold, dict) and hold.get('parts'))): held += parts_words(hold, d, name, dr)      # (the umbrella's own sentence has its parts already)
    sides = [x for x in sides if x]
    if sides: held += ' Where it is in each cell, as the renders have it: ' + '; '.join(sides) + '.'
    return held


def frame_rules(s, held=False, hand='right'):
    if s['kind'] == 'animal':
        return ("For each cell, as for a single frame: redraw the render as a finished illustration in exactly the style of the character reference. "
                "The pose must match the render EXACTLY: the same position and size, the same body direction, the same angle of each of the four "
                "legs, of the tail and of the head, the same camera angle from above - nothing added, nothing moved. The paws exactly as in the "
                "render. Fur and loose clothes may go a little past the render's outline, nothing else. "
                f"The animal: {s['description']} " + (s.get('notes') or '') + " Plain white background, no shadow on the ground, no text.")
    return ("For each cell, as for a single frame: redraw the render as a finished illustration in exactly the style of the character reference. "
            "The pose must match the render EXACTLY: the same position and size, the same body direction, the same angle of every limb and of "
            "the head, the same camera angle from above - " + (f"nothing added but what the {hand} hand holds, nothing moved" if held else "nothing added, nothing held, nothing moved") + ". The feet and shoes exactly as in the render, "
            "flat and rigid. Hair and loose clothes may go a little past the render's outline, nothing else. "
            "Small or thin things worn on the head or the body (a headband, ears or antennae on it, a bow, a hat's brim, straps) are drawn as "
            "the turnaround shows them, NOT as the render does - the 3D model makes them rough: seen from behind, only their backs show "
            "(no faces, eyes or insides of ears), each on the side the turnaround's back view has it. "
            f"The character: {s['description']} " + (s.get('notes') or '') +
            " Plain white background, no shadow on the ground, no text.")


def sheet_of(paths, bbox, out):
    pad = 0.06; w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]; k = min(CW * (1 - 2 * pad) / w, CH * (1 - 2 * pad) / h)
    sh = Image.new('RGB', (CW * 4, CH), (255, 255, 255))
    for n, p in enumerate(paths):
        c = Image.open(p).convert('RGBA').crop(bbox).resize((round(w * k), round(h * k)), Image.LANCZOS)
        cell = Image.new('RGBA', (CW, CH), (255, 255, 255, 255)); cell.alpha_composite(c, ((CW - c.width) // 2, CH - round(CH * pad) - c.height))
        sh.paste(cell.convert('RGB'), (n * CW, 0))
    sh.save(out)


def union(paths):
    bb = [Image.open(p).getbbox() for p in paths]
    return (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))


def refs_and_words(s, d, extra):
    """[(image, what it is)] after image 1 → the images and the sentence naming them"""
    style = d / 'turnaround/turn.png'
    items = ([(s['face'], "the character's face seen from the front (what the face looks like - not its angle)")] if s.get('face') else [])
    items += [(style if style.exists() else s['design'],
               'the character as a finished illustration' + (' - a turnaround: front, right side, back' if style.exists() else '') +
               (': the drawing style, the face, the markings, the fur and any clothes to match (its pose is NOT to be copied)' if s['kind'] == 'animal'
                else ': the drawing style, the face, the hair and the outfit to match (its pose is NOT to be copied)'))]
    if s.get('photo'): items += [(s['photo'], 'a photo: ONLY what the face looks like - not its clothes, hair or pose')]
    items += extra
    words = ' '.join(f'Image {n + 2} is {w}.' for n, (_, w) in enumerate(items))
    return [p for p, _ in items], words


def draw_walk(s, d, dr, again, only_groups=None, name='walk'):
    a = dict(s['actions'].get(name) or {'frames': s['frames'], 'words': 'walking', 'hold': s.get('hold')}, _facing=dr)
    paths = [d / f'render/{name}-{dr}-{i}.png' for i in range(a['frames'])]; bb = union(paths); cost = 0
    groups = [list(range(i, min(i + 4, len(paths)))) for i in range(0, len(paths), 4)]
    front0 = d / f'draw/walk-{FRONT}-drawn-0.png'
    for g, idx in enumerate(groups):
        rs = d / f'draw/{name}-{dr}-renders-{g}.png'; sheet_of([paths[i] for i in idx], bb, rs); out = d / f'draw/{name}-{dr}-drawn-{g}.png'
        if only_groups is not None and g not in only_groups: continue
        if out.exists() and not again: continue
        who = 'animal' if s['kind'] == 'animal' else 'person'
        extra = ([] if dr == FRONT and name == 'walk' else [(front0, f'the same character already drawn {front_words()}: exactly the same {who} - face, ' + ('markings, fur' if who == 'animal' else 'hair') + ', clothes, colours, lines and shading')])
        extra += ([(d / f'draw/{name}-{dr}-drawn-0.png', 'the first half of this same animation, already drawn: continue it exactly - the same '
                    + who + ', but the legs and the stride of THIS sheet\'s renders (image 1), NOT the first half\'s poses')] if g else [])
        imgs, words = refs_and_words(s, d, extra)
        hold = a.get('hold')
        held = held_words(hold, d, name, dr, [held_where(d, stem_of(name, dr, k), n_ + 1) for n_, k in enumerate(idx)] if hold else []) + cell_words(a, idx)
        P = (f"Image 1 is a SHEET of {len(idx)} separate frames of one {a['words']} animation, side by side, read left to right - every cell a 3D render "
             f"of the same {who} in one moment of it, seen from a game camera from above. " + (a['pose'] + ' ' if a.get('pose') else '') + "Redraw EVERY cell as a finished illustration, "
             "keeping the sheet exactly as it is: the same cells, each figure at exactly the same position, size and pose - the legs, the stride, "
             + ("the tail" if who == 'animal' else "the arms") + f" exactly as each cell's render; nothing added between the cells, no borders, no numbers. The same {who} in every cell. "
             f"THE HEAD in every cell: {head_as_render(dr) if a.get('head') == 'as_render' and dr.startswith('south') else head_words(dr, who == 'animal')}.{held} {words}\n" + frame_rules(s, bool(hold), hand_of(hold)))
        (d / f'draw/{name}-{dr}-prompt-{g}.txt').write_text(P)
        try: cost += gpt(P, [rs] + imgs, out, '1536x1024')
        except Refused: print(f'draw: {out.name} turned down by OpenAI\'s safety check three times - left as it was; run it again later, or say less about skin and length in the description')
    return cost


def cell_words(a, idx, cell=None):
    """an action's "frame_words" ({"5": "...", "5@south-east": "..."} - frames from 1) for the frames on this sheet, said cell by cell. For
    what the render cannot show the image model: a hand the render has floating by the umbrella that holds it behind the head, say
    (it drew the fist pulled up into sight until it was told so). `cell`: the one cell a frame drawn alone sits in"""
    fw = a.get('frame_words') or {}; dr = a.get('_facing'); out = []
    auto = idle_hidden_hand(a, dr)
    for n_, k in enumerate(idx):
        w = fw.get(f'{k + 1}@{dr}') or fw.get(str(k + 1)) or auto
        if w: out.append(f' IN CELL {cell or n_ + 1} (frame {k + 1}): {w}')
    return ''.join(out)


# STANDING WITH SOMETHING IN HAND, SEEN FROM THE OTHER SIDE. SpriteCast's idle holds a thing low by the hip; turned away from the camera on
# the holding side (the right hand: north-west, west), the hand is behind the body and only the thing shows, past the far shoulder - and
# the image model, given a thing with no hand, raised an arm to the shoulder to hold it (the rain girl's umbrella, north-west: drawn
# wrong, then right with this said). Said by itself for those facings; the action's own "frame_words" for a frame still come first.
# (Checked on the right hand in north-west only; west and the left hand's mirror facings are the same case, not drawn yet.)
def idle_hidden_hand(a, dr):
    hold = a.get('hold')
    if a.get('clip') != 'idle_spritecast' or not hold or not dr: return ''
    left = isinstance(hold, dict) and hold.get('hand') == 'left'; k = hold if isinstance(hold, str) else hold.get('kind', 'thing')
    if dr not in (('north-east', 'east') if left else ('north-west', 'west')): return ''
    side, other = ('LEFT', 'RIGHT') if left else ('RIGHT', 'LEFT')
    return (f"the {k} is held in the {side} hand, which hangs down by the {side.lower()} hip on the far side of the body, hidden by it (at most the end the "
            f"hand holds shows beside the hip); the {k} points forward, away from the camera, so it shows past the {other} shoulder, going behind the body. "
            "BOTH arms hang down: no hand is up at the shoulder, no arm is raised to hold it.")


def draw_frame(s, d, name, dr, k):
    """ONE frame of an action drawn alone - its render in the second cell of a sheet (the rest white), at the action's own scale, the
    action's drawn sheet beside it for the style → draw/<name>-<facing>-single-<k>.png, which `finish` uses in place of the sheet's cell.
    For one frame that came out wrong: drawn alone, with its own "frame_words", the image model attends to that frame only"""
    a = dict(s['actions'][name], _facing=dr); paths = [d / f'render/{name}-{dr}-{i}.png' for i in range(a['frames'])]; bb = union(paths)
    blank = d / 'draw/blank.png'; Image.new('RGBA', Image.open(paths[k]).size, (0, 0, 0, 0)).save(blank)
    rs = d / f'draw/{name}-{dr}-single-{k}-render.png'; sheet_of([blank, paths[k], blank, blank], bb, rs)
    imgs, words = refs_and_words(s, d, [(d / f'draw/{name}-{dr}-drawn-{k // 4}.png', 'the rest of this action, already drawn: exactly the same person, size and style')])
    hold = a.get('hold'); held = held_words(hold, d, name, dr, [held_where(d, stem_of(name, dr, k), 2)] if hold else []) + cell_words(a, [k], cell=2)
    P = (f"Image 1 is a sheet of four cells with ONE figure in it, in the second cell: a 3D render of a person in one moment of {a['words']}, seen from a "
         "game camera from above. Redraw THAT figure as a finished illustration at exactly the same position, size and pose - the legs, the arms and "
         f"the head exactly as the render - and leave the other three cells plain white, nothing in them. THE HEAD: "
         f"{head_as_render(dr) if a.get('head') == 'as_render' and dr.startswith('south') else head_words(dr, False)}.{held} {words}\n" + frame_rules(s, bool(hold), hand_of(hold)))
    (d / f'draw/{name}-{dr}-single-{k}-prompt.txt').write_text(P); out = d / f'draw/{name}-{dr}-single-{k}.png'
    try: return gpt(P, [rs] + imgs, out, '1536x1024')
    except Refused: print(f'draw: {out.name} turned down by OpenAI\'s safety check three times - left as it was'); return 0


def frame_step(s, d, args):
    """`charpipe.py frame SPEC --only <action> --facing <facing> --frame <n>` (n from 1): that one frame drawn again alone (PAID, ~$0.08),
    then the action finished again with it. The earlier drawing of it is kept as .before.png"""
    name, dr, k = args.only, args.facing, (args.frame or 0) - 1
    if name not in s['actions'] or dr not in DIRS or not 0 <= k < s['actions'][name]['frames']: sys.exit('frame: --only <an action>, --facing <one of the 8>, --frame <1..its frames>')
    if not (d / f'draw/{name}-{dr}-drawn-{k // 4}.png').exists(): sys.exit(f'frame: draw {name} {dr} first (its sheet is the style the frame is drawn to)')
    if not gate(args, f'frame: {name} {dr} frame {k + 1} drawn alone, about $0.08 (OpenAI)'): return
    one = d / f'draw/{name}-{dr}-single-{k}.png'
    if one.exists(): shutil.copy2(one, one.with_suffix('.before.png'))
    print(f'frame: ${draw_frame(s, d, name, dr, k):.2f}'); rep_ = {}; finish_action(s, d, name, rep_); print(rep_.get(f'{name} {dr}'))


def loop_gif(s, d, names, dr, scale=0.42):
    """`charpipe.py loop SPEC --only walk,ready,slash,recover --facing south-east`: the finished frames of several animations played one
    after another as ONE looping GIF, each with its 3D shadow and, where the action has one, its swing's effect - to see a walk go into an
    attack and back out before anything is drawn again or packed (out/loop-<facing>.gif, free). A looping animation (the walk) plays from
    its second frame round to its first, the pose a "between" leaves from and comes back to; a one-shot plays once. Each at its own pace:
    the walk and the actions as `pack` times them, in-betweens 0.12 s a frame."""
    seq = []
    for nm in names:
        if nm == 'walk': a = {'frames': s['frames'], 'loop': True, 't0': s['walk']['t0'], 't1': s['walk']['t1']}
        elif nm in s['actions']: a = s['actions'][nm]
        else: sys.exit(f'loop: no animation "{nm}" (walk, or one of {", ".join(s["actions"])})')
        n = a['frames']; t0, t1 = a.get('t0') or 0, a.get('t1')
        ms = 120 if a.get('between') or not t1 else round(1000 * (t1 - t0) / (n if a.get('loop', True) else max(1, n - 1)))
        tr = effect_of(a.get('trail'), d.parent) if a.get('trail') else None; m = max(1, int((tr or {}).get('frames_x') or 1)) if tr else 1
        order = [(k + 1) % n for k in range(n)] if a.get('loop', True) and not a.get('between') else list(range(n))
        for k in order:
            for j in range(m): seq.append((nm, k, k * m + j if tr else None, ms // m))
    missing = sorted({f'{nm}-{dr}-{k}' for nm, k, _, _ in seq if not (d / f'frames/{nm}-{dr}-{k}.png').exists()})
    if missing: sys.exit(f'loop: not finished yet: {", ".join(missing[:6])}{" ..." if len(missing) > 6 else ""} - draw and finish them first')
    S = max(Image.open(d / f'frames/{nm}-{dr}-{k}.png').width for nm, k, _, _ in seq)          # (the walk's canvas is smaller: same middle, same scale)
    BG = (226, 230, 222); pics, boxes = [], []
    for nm, k, q, ms in seq:
        c = Image.new('RGBA', (S, S), BG + (255,))
        def lay(p, shade=False):
            if not p.exists(): return None
            im = Image.open(p).convert('RGBA')
            if shade: al_ = np.asarray(im)[..., 3]; a_ = np.round(CL.deeper(CL.shadow_share(al_) * CL.SHADOW_DARK) * 255).astype(np.uint8) if CL.is_graded(al_) else (al_ > 128).astype(np.uint8) * 77; im = Image.fromarray(np.dstack([np.full(a_.shape + (3,), (40, 30, 24), np.uint8), a_]))
            o = (S - im.width) // 2; c.alpha_composite(im, (o, o)); b = im.getchannel('A').getbbox(); return b and (b[0] + o, b[1] + o, b[2] + o, b[3] + o)
        bb = [lay(d / f'render/{nm}-{dr}-{k}-s.png', True), lay(d / f'frames/{nm}-{dr}-{k}.png')] + ([lay(d / f'render/{nm}-{dr}-{q}-t.png')] if q is not None else [])
        pics.append((c, ms)); boxes += [b for b in bb if b]
    x0, y0 = min(b[0] for b in boxes) - 30, min(b[1] for b in boxes) - 30; x1, y1 = max(b[2] for b in boxes) + 30, max(b[3] for b in boxes) + 30
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(S, x1), min(S, y1)
    out = [c.crop((x0, y0, x1, y1)).convert('RGB').resize((round((x1 - x0) * scale), round((y1 - y0) * scale)), Image.LANCZOS) for c, _ in pics]
    # each picture its own 256 colours: one palette for all of them (an effect's blues among it) left a face a few skin tones, and the
    # GIF showed blotches on it that the drawings do not have - to be taken for the image model's, and a frame drawn again for nothing
    f = d / f'out/loop-{dr}.gif'; f.parent.mkdir(exist_ok=True)
    q_ = [o.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for o in out]
    q_[0].save(f, save_all=True, append_images=q_[1:], duration=[ms for _, ms in pics], loop=0, optimize=True)
    print(f'loop: {f} - {" > ".join(names)}, {len(seq)} pictures, {sum(ms for _, ms in pics) / 1000:.1f} s round - look at the joins (free)')


def draw_idle(s, d, again):
    groups = idle_groups(); cost = 0
    bb = union([d / f'render/idle-{x}.png' for x in DIRS])
    for g, ds in enumerate(groups):
        rs = d / f'draw/idle-renders-{g}.png'; sheet_of([d / f'render/idle-{x}.png' for x in ds], bb, rs); out = d / f'draw/idle-drawn-{g}.png'
        if out.exists() and not again: continue
        who = 'animal' if s['kind'] == 'animal' else 'person'
        extra = [(d / f'draw/walk-{FRONT}-drawn-0.png', f'the same character already drawn {front_words()}: exactly the same {who}')]
        extra += ([(d / 'draw/idle-drawn-0.png', "the same character's other standing views, already drawn: exactly the same")] if g else [])
        imgs, words = refs_and_words(s, d, extra)
        turns = '; '.join(f'cell {n + 1}: {head_words(x, who == "animal")}' for n, x in enumerate(ds))
        hold = s.get('hold'); held = held_words(hold, d, 'walk', ds[0], [held_where(d, stem_of('idle', x), n + 1) for n, x in enumerate(ds)] if hold else [])
        P = (f"Image 1 is a SHEET of 4 separate figures side by side - every cell a 3D render of the same {who} standing still, each turned a "
             "different way, seen from a game camera from above. Redraw EVERY cell as a finished illustration, keeping the sheet exactly as it is: "
             f"each figure at exactly the same position, size, pose and turn; nothing added between the cells. The same {who} in all 4. "
             f"THE HEADS - {turns}.{held} {words}\n" + frame_rules(s, bool(hold), hand_of(hold)))
        (d / f'draw/idle-prompt-{g}.txt').write_text(P)
        try: cost += gpt(P, [rs] + imgs, out, '1536x1024')
        except Refused: print(f'draw: {out.name} turned down by OpenAI\'s safety check three times - left as it was; run it again later, or say less about skin and length in the description')
    return cost


# --- seated ---------------------------------------------------------------------------------------------------------------------------
def sit_render(s, d):
    """free: the rig bent into sitting (render_char.html sitFrames) in 8 facings, each with its 3D shadow → render/sit-<facing>.png,
    render/sit.json (the seat: its height in the figure's heights and its point on each picture)"""
    from playwright.sync_api import sync_playwright
    if s['kind'] == 'animal': sys.exit('sit: people only for now')
    glb = Path(s.get('rig_glb') or d / 'rig/rig.glb')
    if not glb.exists(): sys.exit('sit: run `rig` first (or give "rig_glb")')
    glb = rig_file(s, d)

    def serve(route):
        p = route.request.url.split('spritecast.local/', 1)[1]
        if p == 'asset/rig.glb': return route.fulfill(path=str(glb), content_type='model/gltf-binary')
        f = (HERE / p).resolve()
        if HERE not in f.parents: return route.abort()
        route.fulfill(path=str(f), content_type='text/html' if f.suffix == '.html' else 'text/javascript')
    save = lambda url, p: Path(p).write_bytes(base64.b64decode(url.split(',', 1)[1]))
    seats, o = {}, s.get('sit') or {}
    with sync_playwright() as pw:
        br = BROWSER.launch(pw); pg = br.new_page(); pg.route('http://spritecast.local/**', serve); pg.goto('http://spritecast.local/render_char.html'); pg.evaluate('(f) => { window.shadowFlat = f }', s.get('shadow') == 'flat')          # ("shadow": "flat" - the one hard shape, as before 0.20)
        pg.wait_for_function('window.ready === true', timeout=30000); pg.evaluate('(r) => window.setRes(r)', CL.PX)
        pg.evaluate('([u, p, l]) => window.load(u, p, l)', ['http://spritecast.local/asset/rig.glb', s['pitch'], s['light']])
        for dr in DIRS:
            save(pg.evaluate('(a) => window.sitFrames(...a)', [dr, s['head_up'], s['shoulder_up'], s['shoulder_wide'], o, True]), d / f'render/sit-{dr}.png')
            save(pg.evaluate('window.shadowShots')[0], d / f'render/sit-{dr}-s.png'); save(pg.evaluate('window.heightShot'), d / f'render/sit-{dr}-h.png')
            seats[dr] = pg.evaluate('window.seatInfo')
        br.close()
    seats['_'] = {'px': round(512 * CL.PX), 'view_h': 1.25, 'pitch': s['pitch'], 'heights': 'render/sit-<facing>-h.png: (R*256+G)/65535*view_h figure heights'}
    (d / 'render/sit.json').write_text(json.dumps(seats, indent=1))
    print(f"sit: {d / 'render'}/sit-*.png - seated on nothing, the seat {seats[FRONT]['seatY']:.2f} of the height up; look at them, then `sit --draw`")


def sit_draw(s, d, args):
    """PAID (~$0.22: two sheets of four): the seated renders drawn over like the standing views, then finished"""
    if not (d / 'render/sit-south.png').exists(): sys.exit('sit: run `sit` first (the renders)')
    if not (d / f'draw/walk-{FRONT}-drawn-0.png').exists(): sys.exit('sit: draw the walk first - the seated views follow its drawing')
    groups = idle_groups()
    todo = [g for g in (0, 1) if args.again or not (d / f'draw/sit-drawn-{g}.png').exists()]
    if todo and not gate(args, f'sit: {len(todo)} sheets of 4 seated views, about ${len(todo) * 0.11:.2f} (OpenAI)'): return
    bb = union([d / f'render/sit-{x}.png' for x in DIRS]); cost = 0; who = 'person'
    for g, ds in enumerate(groups):
        rs = d / f'draw/sit-renders-{g}.png'; sheet_of([d / f'render/sit-{x}.png' for x in ds], bb, rs); out = d / f'draw/sit-drawn-{g}.png'
        if g not in todo: continue
        extra = [(d / f'draw/walk-{FRONT}-drawn-0.png', f'the same character already drawn {front_words()}: exactly the same person')]
        extra += ([(d / 'draw/sit-drawn-0.png', "the same character's other seated views, already drawn: exactly the same")] if g else [])
        imgs, words = refs_and_words(s, d, extra)
        turns = '; '.join(f'cell {n + 1}: {head_words(x)}' for n, x in enumerate(ds))
        P = ("Image 1 is a SHEET of 4 separate figures side by side - every cell a 3D render of the same person SITTING, as on a chair or a "
             "bench that is not drawn (it will be the game's own), each turned a different way, seen from a game camera from above. Redraw EVERY "
             "cell as a finished illustration, keeping the sheet exactly as it is: each figure at exactly the same position, size, pose and turn - "
             "the thighs level, the knees bent, the feet as in the render; the hands resting on the thighs or the lap, relaxed (where the render "
             "holds a hand in the air, bring it down onto the thigh). NO chair, NO seat, NO bench, nothing under or behind them; nothing added "
             f"between the cells. The same person in all 4. THE HEADS - {turns}. {words}\n" + frame_rules(s))
        (d / f'draw/sit-prompt-{g}.txt').write_text(P)
        try: cost += gpt(P, [rs] + imgs, out, '1536x1024')
        except Refused: print(f'sit: {out.name} turned down by OpenAI\'s safety check three times - left as it was; run it again later')
    print(f'sit: drawn (${cost:.2f})'); sit_finish(s, d)


def sit_finish(s, d):
    """free: each seated view cut out, fitted onto its render, cleaned → frames/sit-<facing>.png; then the strips packed (out/sit-*)"""
    groups = idle_groups()
    for g, ds in enumerate(groups):
        if not (d / f'draw/sit-drawn-{g}.png').exists(): continue
        for n, x in enumerate(ds):
            ren = Image.open(d / f'render/sit-{x}.png').convert('RGBA')
            f, iou = CL.fit_to_render(cut(d, d / f'draw/sit-drawn-{g}.png', n), ren)
            CL.defringe(CL.clear_white_unless_ai(f, ren)).save(d / f'frames/sit-{x}.png')
            print(f'sit: {x} overlap {iou:.2f}' + ('  LOW - look at it' if iou < 0.7 else ''), flush=True)
    TU.apply(SPEC_PATH) if SPEC_PATH else None
    pack(s, d, {})


def draw(s, d, args):
    if not s['draw']: print('draw: "draw": false - the 3D renders are the frames, nothing to draw'); finish(s, d); return preview(s, d)
    only = args.only.split(',') if args.only else DIRS + ['idle']
    if args.only and set(only) <= set(s['actions']): only = only + ['__actions_only__']     # (--only run: that action alone)
    walks = [] if '__actions_only__' in only else [x for x in DIRS if x in only and x not in s['mirrored']]     # a mirrored facing is flipped from its pair in `finish`
    if not (d / f'render/walk-{FRONT}-0.png').exists(): sys.exit('draw: run `render` first')
    if walks and FRONT not in walks and not (d / f'draw/walk-{FRONT}-drawn-0.png').exists(): walks = [FRONT] + walks
    if s['actions'] and not walks and not (d / f'draw/walk-{FRONT}-drawn-0.png').exists(): walks = [FRONT]   # (the actions follow its drawing)
    todo = lambda f: args.again or not (d / f'draw/{f}').exists()     # sheets already drawn are kept (and not paid for again)
    n = sum(todo(f'walk-{x}-drawn-{k}.png') for x in walks for k in range(-(-s['frames'] // 4))) + (sum(todo(f'idle-drawn-{k}.png') for k in range(len(idle_groups()))) if 'idle' in only else 0)
    n += sum(todo(f'{nm}-{x}-drawn-{k}.png') for nm, a in s['actions'].items() if (nm in only or not args.only) and (d / f'render/{nm}-{FRONT}-0.png').exists()
             for x in action_dirs(s) for k in range(-(-a['frames'] // 4)))
    if n and not gate(args, f'draw: {n} sheets of 4 frames, about ${n * 0.11:.2f} (OpenAI)'): return
    cost = 0
    if FRONT in walks: cost += draw_walk(s, d, FRONT, args.again); walks.remove(FRONT)   # the front first: the rest follow it
    with ThreadPoolExecutor(6) as ex: cost += sum(ex.map(lambda x: draw_walk(s, d, x, args.again), walks))
    if 'idle' in only and '__actions_only__' not in only: cost += draw_idle(s, d, args.again)
    for name in [n for n in s['actions'] if n in only or not args.only]:             # the actions after the walk they follow
        if not (d / f'render/{name}-{FRONT}-0.png').exists(): print(f'draw: {name} has no renders - `render` (or `rig --again` for its clip) first'); continue
        dirs = action_dirs(s); cost += draw_walk(s, d, FRONT, args.again, name=name) if FRONT in dirs else 0
        with ThreadPoolExecutor(6) as ex: cost += sum(ex.map(lambda x: draw_walk(s, d, x, args.again, name=name), [x for x in dirs if x != FRONT]))
    print(f'draw: done (${cost:.2f})')
    if all_drawn(s, d): finish(s, d); preview(s, d)        # the rest is free: straight on to the strips and the preview
    else: print('draw: some facings are not drawn yet - draw them, then `finish`')


def all_drawn(s, d):
    sheets = -(-s['frames'] // 4)
    return all((d / f'draw/walk-{x}-drawn-{k}.png').exists() for x in DIRS if x not in s['mirrored'] for k in range(sheets)) and (d / 'draw/idle-drawn-0.png').exists()


def make3d(s, d, args):
    """model + rig + render in one go: one OK for the 3D, then the renders to look at before `draw`"""
    cost = ('Meshy ~30 credits' + ('' if s['kind'] == 'animal' else ' + Tripo ~45') if s['modeler'] == 'meshy'
            else 'Tripo ~30 credits (~40 if it has to be coloured again)' if s['kind'] == 'animal' else 'Tripo ~75 credits (~85 if it has to be coloured again)')
    if not gate(args, f'3d: the model, its rig and walk ({cost}), then the renders (free), a few minutes'): return
    if s['kind'] == 'animal':                            # no rig: its skeleton is found from the mesh as it renders
        model(s, d, args)
        if (d / 'model/model.glb').exists(): render(s, d)
    else:
        args.no_render = True; model(s, d, args); rig(s, d, args)
        if (d / 'rig/rig.glb').exists(): render(s, d)
    if not s['draw'] and (d / f'render/walk-{FRONT}-0.png').exists(): finish(s, d); preview(s, d)     # nothing to draw: done


# --- finish ---------------------------------------------------------------------------------------------------------------------------
def cell_width(path, cells):
    """how wide a drawn sheet's cells are. The guide puts its figures in fixed quarters; a sheet with fewer than four may come back with
    them spread over the whole width instead (three figures on thirds: the fixed cut went through the second and third - the rain
    girl's 3-frame in-between, 2026-11-16). Whichever grid - quarters, or the sheet in `cells` equal parts - lies closer to the
    middles of the ink actually drawn is taken."""
    if cells >= 4: return CW
    a = np.asarray(Image.open(path).convert('L')) < 200; col = a.sum(0) > 2
    runs, x = [], 0
    while x < len(col):
        if col[x]:
            x0 = x
            while x < len(col) and (col[x] or col[x:x + 25].any()): x += 1
            runs.append((x0, x))
        x += 1
    runs = sorted(sorted(runs, key=lambda r: r[0] - r[1])[:cells])
    if len(runs) != cells: return CW
    mids = [(r0 + r1) / 2 for r0, r1 in runs]; spread = len(col) / cells
    err = lambda w: sum(abs(m - (k + 0.5) * w) for k, m in enumerate(mids))
    return int(spread) if err(spread) < err(CW) else CW


def cut(d, path, n, cells=4):
    """cell n of a drawn sheet, cut out - kept in frames/cut/ by the sheet's name, cell and modification time, so a `finish` after
    `redraw` cuts only the sheets that changed (the AI cut-out takes ~3 s a cell on a CPU). `cells`: how many figures the sheet has"""
    path = Path(path); cw = cell_width(path, cells); key = d / f'frames/cut/{path.stem}-{n}-{path.stat().st_mtime_ns}{"" if cw == CW else f"-w{cw}"}.png'
    if key.exists(): return Image.open(key).convert('RGBA')
    for old in key.parent.glob(f'{path.stem}-{n}-*.png'): old.unlink()
    key.parent.mkdir(parents=True, exist_ok=True); sp = CL.cut_cell(Image.open(path).convert('RGB'), n, cw, CH); sp.save(key); return sp


HELD_MIN = 0.5      # a frame whose drawing covers under half of where the render has the held thing (off the body): drawn in the wrong place
EXTRA_MAX = 0.08    # ... or more than this share of the drawing lies well off the render's outline (the thing put where the render has none)


def held_visible(d, name, dr, k):
    """where the held thing shows in the render - not behind the body: its own render's pixels outside the body, or inside it where the full
    render differs from the body alone (the thing in front there)"""
    return _visible(d, stem_of(name, dr, k))


def _visible(d, stem):
    F = np.asarray(Image.open(d / f'render/{stem}.png').convert('RGBA')).astype(int)
    Bi = np.asarray(Image.open(d / f'render/{stem}-body.png').convert('RGBA')).astype(int)
    H = np.asarray(Image.open(d / f'render/{stem}-held.png'))[..., 3] > 128
    return H & ((Bi[..., 3] <= 128) | (np.abs(F - Bi)[..., :3].sum(-1) > 40))


def _axis(m):
    """a mask's middle and its long axis (unit vector)"""
    ys, xs = np.nonzero(m); c = np.array([xs.mean(), ys.mean()])
    w, v = np.linalg.eigh(np.cov(np.stack([xs - c[0], ys - c[1]]))); return c, v[:, -1]


def held_cover(frame, d, name, dr, k):
    """how much of the held thing's place in the render - where it shows and sticks out of the body - the drawn frame covers (1 when
    there's too little of it to judge). A thin thing drawn a few degrees off misses its render's pixels though it is right, so a drawing
    whose part off the body points the same way (within 25°) from the same side of the body counts as covering it"""
    from scipy import ndimage
    hp, bp = d / f'render/{name}-{dr}-{k}-held.png', d / f'render/{name}-{dr}-{k}-body.png'
    if not hp.exists() or not bp.exists(): return 1.0
    B0 = np.asarray(Image.open(bp))[..., 3] > 128; B = ndimage.binary_dilation(B0, iterations=round(6 * CL.PX))
    out = held_visible(d, name, dr, k) & ~B
    if out.sum() < 60 * CL.PX ** 2: return 1.0
    a = np.asarray(frame)[..., 3] > 100; A = ndimage.binary_dilation(a, iterations=round(4 * CL.PX))          # (a little slack: the drawing is thicker or thinner)
    cov = float((out & A).sum() / out.sum())
    if cov < HELD_MIN:
        lab, n = ndimage.label(a & ~B)
        if n:
            big = lab == (1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)))))
            if big.sum() >= 0.4 * out.sum():
                (cr, vr), (cd, vd) = _axis(out), _axis(big); bc = np.array([np.nonzero(B0)[1].mean(), np.nonzero(B0)[0].mean()])
                if abs(float(vr @ vd)) > np.cos(np.radians(25)) and float((cr - bc) @ (cd - bc)) > 0: cov = max(cov, HELD_MIN)
    return round(cov, 3)


def held_extra(frame, d, name, dr, k):
    """the share of the drawn frame lying well off the render's outline (10 px): a held thing put where the render has none - the rain girl's
    right frames measured 0-5 %, the ones with the umbrella on the wrong side 10-20 %"""
    from scipy import ndimage
    A = np.asarray(frame)[..., 3] > 100; R = np.asarray(Image.open(d / f'render/{name}-{dr}-{k}.png'))[..., 3] > 128
    return round(float((A & ~ndimage.binary_dilation(R, iterations=round(10 * CL.PX))).sum() / max(1, A.sum())), 3)


def held_fit(sprites, rens):
    """frames of an action with something held, fitted onto their renders: first each frame's own best scale and place by outline overlap
    (its height is no measure - the umbrella goes overhead), then ONE scale per sheet of four - the median of theirs: a scale of its own let
    the figure grow and shrink frame to frame - and each frame placed again at it. Pieces far from the render's outline are left out: the
    model's long umbrella from the next cell, which the cut keeps when it reaches into this one, is not this frame's"""
    from scipy import ndimage, signal
    first = [TU.fit(sp, r) for sp, r in zip(sprites, rens)]
    frames, ious = [], []
    for g in range(0, len(sprites), 4):
        k = float(np.median([f[1] for f in first[g:g + 4]]))
        for sp, r in zip(sprites[g:g + 4], rens[g:g + 4]):
            big = sp.resize((max(1, round(sp.width * k)), max(1, round(sp.height * k))), Image.LANCZOS)
            R = (np.asarray(r)[..., 3] > 128).astype(np.float32); A = (np.asarray(big)[..., 3] > 128).astype(np.float32)
            cor = signal.fftconvolve(R, A[::-1, ::-1], mode='full'); iy, ix = np.unravel_index(np.argmax(cor), cor.shape)
            y, x = iy - (A.shape[0] - 1), ix - (A.shape[1] - 1)
            f = Image.new('RGBA', r.size, (0, 0, 0, 0)); f.paste(big, (int(x), int(y)), big)
            fa = np.asarray(f).copy(); m = fa[..., 3] > 20
            near = ndimage.binary_dilation(R > 0, iterations=max(round(12 * CL.PX), round(0.04 * r.size[1])))          # (within ~4 % of the frame of the 3D outline)
            lab, nlab = ndimage.label(m)
            for j in range(1, nlab + 1):
                if not (near & (lab == j)).any(): fa[lab == j] = 0
            f = Image.fromarray(fa); a = fa[..., 3] > 127
            frames.append(f); ious.append(round(float((a & (R > 0)).sum() / max(1, (a | (R > 0)).sum())), 3))
    return frames, ious


FAMILY_WORDS = {'dark': 'black', 'grey': 'dark grey', 'silver': 'silver-grey (bare metal)', 'brown': 'dark brown', 'yellow': 'yellow', 'orange': 'orange',
                'red': 'red', 'green': 'green', 'blue': 'blue', 'purple': 'purple'}


def family(rgb):
    """a colour's kind, coarse enough that a painter's shading stays in it and a wrong material does not (brown wood / silver metal / yellow cloth)"""
    r, g, b = (rgb[..., k].astype(int) for k in range(3)); mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b); lum = 0.299 * r + 0.587 * g + 0.114 * b
    f = np.full(r.shape, 'grey', dtype='<U6'); sat = mx - mn
    f[(sat < 34) & (lum > 140)] = 'silver'; warm = (sat >= 34) & (r >= g) & (g >= b)
    f[warm & (g >= 0.74 * r)] = 'yellow'; f[warm & (g < 0.74 * r) & (g >= 0.45 * r)] = 'orange'; f[warm & (g < 0.45 * r)] = 'red'
    f[warm & (g < 0.74 * r) & (lum < 140)] = 'brown'
    f[(sat >= 34) & (g > r) & (g >= b)] = 'green'; f[(sat >= 34) & (b > r) & (b > g)] = 'blue'; f[(sat >= 34) & (r > g) & (b > g)] = 'purple'
    f[lum < 42] = 'dark'; return f


def held_parts(d, name, dr, k):
    """the held thing's PARTS as its own render has them: [(kind of colour, mask)] from the end at the hand outward. A thing built by
    render_char.html has each part in a colour of its own (an umbrella: brown handle, silver shaft, the canopy, a silver tip); so has
    most of what a rigged model carries. Parts are what the image model gets wrong one by one - and it is the end at the hand it
    guesses at - so they are told to it one by one (parts_words) and looked at one by one afterwards (held_colours)."""
    hp, bp = d / f'render/{name}-{dr}-{k}-held.png', d / f'render/{name}-{dr}-{k}-body.png'
    if not hp.exists() or not bp.exists(): return []
    h = np.asarray(Image.open(hp).convert('RGBA')); on = h[..., 3] > 200; B = np.asarray(Image.open(bp))[..., 3] > 128
    if on.sum() < 200 or not B.any(): return []
    fam = family(h[..., :3]); ys, xs = np.nonzero(on); c = np.array([xs.mean(), ys.mean()]); _, v = np.linalg.eigh(np.cov(np.stack([xs - c[0], ys - c[1]]))); ax = v[:, -1]
    by, bx = [q.mean() for q in np.nonzero(B)]; t = (xs - c[0]) * ax[0] + (ys - c[1]) * ax[1]
    if abs((bx - c[0]) * ax[0] + (by - c[1]) * ax[1] - t.min()) > abs((bx - c[0]) * ax[0] + (by - c[1]) * ax[1] - t.max()): ax = -ax; t = -t      # the axis runs from the end nearer the body
    T = np.full(on.shape, np.nan); T[ys, xs] = t; parts = []
    for name_ in np.unique(fam[on]):
        m = on & (fam == name_); l2, n = ndi.label(m)                       # one kind of colour in two places (a silver shaft and a silver tip) is two parts
        for q in range(1, n + 1):
            piece = l2 == q
            if piece.sum() >= max(60, 0.004 * on.sum()): parts.append((float(np.nanmedian(T[piece])), str(name_), piece))
    return [(f, m) for _, f, m in sorted(parts, key=lambda x: x[0])]


def parts_words(hold, d, name, dr):
    """the sentence that names a held thing's parts from the hand outward: the user's own ("hold": {"parts": ["a dark brown wooden grip",
    "a steel blade", ...]}) or, without them, the kinds of colour its render has - with the three things that went wrong when it was
    only told "as the render shows it": a part painted in its neighbour's colour, the part in the fist grown longer, two hands drawn together."""
    given = hold.get('parts') if isinstance(hold, dict) else None
    if not given:
        found = next((p for k in range(8) for p in [held_parts(d, name, dr, k)] if len(p) >= 2), [])
        given = [f'a part in {FAMILY_WORDS.get(f, f)}' for f, _ in found]
    if len(given) < 2: return ''
    return (f' It has {len(given)} PARTS, the same in every cell, from the hand outward: ' + '; then '.join(f'{n + 1}) {g}' for n, g in enumerate(given)) + '. '
            'Each part is exactly as long as that cell\'s render shows it and keeps its own colour and material in every cell - no part takes the colour of the one '
            'beside it, and the part in the fist is not made longer. Where the render shows a part between the two hands, draw that part there, the hands as far '
            'apart as the render has them - do not move the hands together.')


def held_colours(frame, d, name, dr, k):
    """the parts of the held thing the DRAWING may have in another kind of colour than its render: ['silver → brown', ...] - A POINTER, NOT
    A VERDICT. Run on the rain girl's slash it named 14 of 64 frames, and looked at one by one most were right: a shaft a few pixels
    wide and a drawing a few pixels off its render are enough to trip it. So it is printed for someone to look, and `redraw` - which
    costs money - does not act on it. A part counts
    when the camera sees enough of it; it passes when its kind of colour is there in the drawing near where the render has it (near: the
    drawing lies a few pixels off its render, and a shaft is a few pixels thick). Dark for brown passes: a handle painted near-black."""
    parts = held_parts(d, name, dr, k)
    if len(parts) < 2: return []
    vis = held_visible(d, name, dr, k); a = np.asarray(frame); fam = family(a[..., :3]); on = a[..., 3] > 128; out = []
    for f, m in parts:
        v = m & vis
        if v.sum() < 400 or v.sum() < 0.5 * m.sum(): continue          # (enough of it, and most of it, in sight: a tip, or a handle inside a fist, is no evidence)
        lum = a[..., :3] @ np.array([0.299, 0.587, 0.114]); near = ndi.binary_dilation(v, iterations=10) & on
        ok = (fam == f) | ((f == 'brown') & ((fam == 'dark') | ((fam == 'grey') & (lum < 110)))) | ((f == 'silver') & (fam == 'grey') & (lum > 120))
        if (near & ok).sum() >= 0.2 * v.sum(): continue
        got, cnt = np.unique(fam[ndi.binary_dilation(v, iterations=3) & on], return_counts=True)
        out.append(f"{FAMILY_WORDS.get(f, f)} → {FAMILY_WORDS.get(str(got[cnt.argmax()]), '?') if len(got) else 'nothing'}")
    return out


def finish_action(s, d, name, report):
    """an action's drawn sheets cut, fitted onto its renders and steadied like the walk → frames/<name>-<facing>-<k>.png; a mirrored
    facing flipped from its pair (half a cycle on for a loop, as the walk; the same moment for a one-shot)"""
    a = s['actions'][name]; n = a['frames']; groups = [list(range(i, min(i + 4, n))) for i in range(0, n, 4)]
    for dr in action_dirs(s):
        if not all((d / f'draw/{name}-{dr}-drawn-{g}.png').exists() for g in range(len(groups))): continue
        sprites = []
        for g, idx in enumerate(groups): sprites += [cut(d, d / f'draw/{name}-{dr}-drawn-{g}.png', k, len(idx)) for k in range(len(idx))]
        for k in [k for k in range(n) if (d / f'draw/{name}-{dr}-single-{k}.png').exists()]: sprites[k] = cut(d, d / f'draw/{name}-{dr}-single-{k}.png', 1)   # (a frame drawn alone: `frame`)
        rens = [Image.open(d / f'render/{name}-{dr}-{i}.png').convert('RGBA') for i in range(n)]
        if s['kind'] == 'animal': frames, ious = CL.fit_walk(sprites, rens, None)
        elif a.get('hold'):
            # something held goes overhead and out to the side: the walk's fit (the body's height) took it for a taller figure and
            # scaled frames up and down - fitted by the outline overlap instead (as the standing views), the heads then steadied
            # (by height it shrank a frame whose umbrella was overhead; steadying the head warped the umbrella crossing it: one scale and
            # place per frame where the outlines overlap most, the drawing itself left whole)
            frames, ious = held_fit(sprites, rens)
        else:
            frames, ious = CL.fit_walk(sprites, rens); _, scales = CL.steady(frames, s['neck'])
            frames, ious = CL.fit_walk(sprites, rens, mult=CL.sheet_scales(scales, [])); frames, _ = CL.steady(frames, s['neck'])
        for i, f in enumerate(frames): CL.defringe(CL.clear_white_unless_ai(f, Image.open(d / f'render/{name}-{dr}-{i}.png'))).save(d / f'frames/{name}-{dr}-{i}.png')
        report[f'{name} {dr}'] = {'overlap': ious}
        if a.get('hold'):
            cov = [held_cover(f, d, name, dr, i) for i, f in enumerate(frames)]; ext = [held_extra(f, d, name, dr, i) for i, f in enumerate(frames)]
            parts = [held_colours(f, d, name, dr, i) for i, f in enumerate(frames)]
            report[f'{name} {dr}'].update({'held': cov, 'extra': ext, 'parts': parts})
            wrong = [i + 1 for i, (c, x) in enumerate(zip(cov, ext)) if c < HELD_MIN or x > EXTRA_MAX]
            off = {i + 1: p_ for i, p_ in enumerate(parts) if p_}
            if off: print(f'finish: {name} {dr} - a part of the held thing in another colour than its render: ' + '; '.join(f'frame {i}: {", ".join(p_)}' for i, p_ in off.items()) + ' - LOOK at those frames beside their renders: this check points, it does not judge (it is not acted on by `redraw`)')
            if wrong: print(f'finish: {name} {dr} - the held thing not where the render has it in frames {wrong} (`redraw` draws those again)')
        print(f'finish: {name} {dr} overlap {min(ious):.2f}-{max(ious):.2f}', '  LOW - look at it' if min(ious) < 0.7 else '', flush=True)
    for dr in s['mirrored']:
        src = PAIR[dr]; off = n // 2 if a['loop'] else 0
        if not (d / f'frames/{name}-{src}-0.png').exists(): continue
        for k in range(n): CL.flip_onto(Image.open(d / f'frames/{name}-{src}-{(k + off) % n}.png'), d / f'render/{name}-{dr}-{k}.png').save(d / f'frames/{name}-{dr}-{k}.png')


def finish_3d(s, d):
    """`"draw": false` - no image model draws the frames: the 3D renders themselves are the frames (the toon-shaded model, its own texture), packed the same
    way with their 3D shadows. Nothing paid past the model, but softer: no drawn lines, the model's texture as it came"""
    if not (d / f'render/walk-{FRONT}-0.png').exists(): sys.exit('finish: run `3d` (or `render`) first')
    for f in (d / 'frames').glob('*.png'): f.unlink()
    for dr in DIRS:
        for k in range(s['frames']): shutil.copy(d / f'render/walk-{dr}-{k}.png', d / f'frames/walk-{dr}-{k}.png')
        shutil.copy(d / f'render/idle-{dr}.png', d / f'frames/idle-{dr}.png')
        for name, a in s['actions'].items():
            for k in range(a['frames']):
                if (d / f'render/{name}-{dr}-{k}.png').exists(): shutil.copy(d / f'render/{name}-{dr}-{k}.png', d / f'frames/{name}-{dr}-{k}.png')
    pack(s, d, {'draw': False})


def even_heads(s, d, report, what):
    """every facing's head the size of the 3D model's (steady evens them within a facing only): the facings are drawn one by one and
    came out up to ~10 % apart. Evening them to the front's was tried first - but the front was the big one (a face check said so).
    The drawn head against the 3D one by the silhouette under the crown (`head_vs_render`, ~ the square root of the head's size: hence
    the square, measured again after each try), the head and the hair round it rescaled about the neck, at most 15 %"""
    n = s['frames'] if what == 'walk' else 1
    path = (lambda x, k, kind: d / f'{kind}/walk-{x}-{k}.png') if what == 'walk' else (lambda x, k, kind: d / f'{kind}/idle-{x}.png')
    dirs = [x for x in DIRS if x not in s['mirrored'] or what == 'idle']
    dirs = [x for x in dirs if all(path(x, k, 'frames').exists() for k in range(n))]
    fix = {}
    for x in dirs:
        frames = [Image.open(path(x, k, 'frames')).convert('RGBA') for k in range(n)]; c = 1.0
        for _ in range(3):
            now = float(np.median([CL.head_vs_render(CL.rescale_head(f, c, s['neck'], order=1) if c != 1 else f, path(x, k, 'render')) for k, f in enumerate(frames)]))
            c = min(1.15, max(0.85, c / now ** 2))
        if abs(c - 1) < 0.015: continue
        for k, f in enumerate(frames): CL.rescale_head(f, c, s['neck']).save(path(x, k, 'frames'))
        fix[x] = round(c, 3)
    report[f'{what} heads to the 3D'] = fix
    if fix: print(f'finish: {what} heads to the 3D model\'s size: ' + ', '.join(f'{x} x{c}' for x, c in fix.items()), flush=True)


def head_fit(s, d, report, what):
    """`head_fit` in the spec ({facing: factor}, written by `facecheck --apply`): this character's head for its height made another's"""
    fit = s.get('head_fit') or {}; n = s['frames'] if what == 'walk' else 1
    for x, c in fit.items():
        if x not in DIRS or abs(c - 1) < 0.005 or (what == 'walk' and x in s['mirrored']): continue
        for k in range(n):
            p = d / (f'frames/walk-{x}-{k}.png' if what == 'walk' else f'frames/idle-{x}.png')
            if p.exists(): CL.rescale_head(Image.open(p).convert('RGBA'), c, s['neck']).save(p)
    if fit: report[f'{what} head_fit'] = fit


def finish(s, d):
    if not s['draw']: return finish_3d(s, d)
    report = {}
    for dr in DIRS:
        if dr in s['mirrored']: continue
        groups = [list(range(i, min(i + 4, s['frames']))) for i in range(0, s['frames'], 4)]
        if not all((d / f'draw/walk-{dr}-drawn-{g}.png').exists() for g in range(len(groups))): continue
        sprites = []
        for g, idx in enumerate(groups):
            sprites += [cut(d, d / f'draw/walk-{dr}-drawn-{g}.png', n) for n in range(len(idx))]
        single = [k for k in range(s['frames']) if (d / f'draw/walk-{dr}-single-{k}.png').exists()]   # frames drawn alone (redraw)
        for k in single: sprites[k] = cut(d, d / f'draw/walk-{dr}-single-{k}.png', 1)
        rens = [Image.open(d / f'render/walk-{dr}-{i}.png').convert('RGBA') for i in range(s['frames'])]
        if s['kind'] == 'animal': frames, ious = CL.fit_walk(sprites, rens, None, own=single); scales = [1.0] * len(frames)   # one scale a sheet, on the render's feet
        else:
            frames, ious = CL.fit_walk(sprites, rens)      # the upper body at one scale, the legs to the render's feet
            _, scales = CL.steady(frames, s['neck'])        # each sheet's whole figure to the same size first, then each head
            frames, ious = CL.fit_walk(sprites, rens, own=single, mult=CL.sheet_scales(scales, single))
            frames, scales = CL.steady(frames, s['neck'])
        for i, f in enumerate(frames): CL.defringe(CL.clear_white_unless_ai(f, Image.open(d / f'render/walk-{dr}-{i}.png'))).save(d / f'frames/walk-{dr}-{i}.png')
        report[dr] = {'overlap': ious, 'head_scale': [round(x, 3) for x in scales]}
        if s.get('hold') and (d / f'render/walk-{dr}-0-held.png').exists():      # the carried thing where its render has it, in every frame (as an action's)
            cov = [held_cover(f, d, 'walk', dr, i) for i, f in enumerate(frames)]; ext = [held_extra(f, d, 'walk', dr, i) for i, f in enumerate(frames)]
            report[dr].update({'held': cov, 'extra': ext}); wrong = [i + 1 for i, (c, x) in enumerate(zip(cov, ext)) if c < HELD_MIN or x > EXTRA_MAX]
            if wrong: print(f'finish: walk {dr} - the carried thing not where the render has it in frames {wrong} (`redraw` draws those sheets again)')
        print(f'finish: walk {dr} overlap {min(ious):.2f}-{max(ious):.2f}', '  LOW - look at it' if min(ious) < 0.7 else '', flush=True)
    for name in s['actions']: finish_action(s, d, name, report)
    if s['kind'] != 'animal': even_heads(s, d, report, 'walk'); head_fit(s, d, report, 'walk')
    for a, b in best_pairs(d, s):
        # both of a pair drawn: each frame the better of its own drawing and the pair's flipped (frame k + n/2 - flipping swaps the legs),
        # by overlap with this frame's render - the good half of each makes up for the other's poor one
        n = s['frames']
        if not all((d / f'frames/walk-{x}-{k}.png').exists() for x in (a, b) for k in range(n)): continue
        own = {x: [Image.open(d / f'frames/walk-{x}-{k}.png') for k in range(n)] for x in (a, b)}
        for x, y in ((a, b), (b, a)):
            src = []
            for k in range(n):
                r = np.asarray(Image.open(d / f'render/walk-{x}-{k}.png'))[..., 3] > 128
                cands = [(own[x][k], x), (CL.flip_onto(own[y][(k + n // 2) % n], d / f'render/walk-{x}-{k}.png'), y)]
                sc = [float(((np.asarray(c)[..., 3] > 127) & r).sum() / max(1, ((np.asarray(c)[..., 3] > 127) | r).sum())) for c, _ in cands]
                i = int(np.argmax(sc)); cands[i][0].save(d / f'frames/walk-{x}-{k}.png'); report[x]['overlap'][k] = round(sc[i], 3); src.append(cands[i][1])
            report[x]['from'] = src
            print(f'finish: walk {x} - each frame the better of its own and {y} flipped: {[("own" if t == x else "flip") for t in src]}, overlap {min(report[x]["overlap"]):.2f}-{max(report[x]["overlap"]):.2f}', flush=True)
    for dr in s['mirrored']:
        # a facing flipped from its pair (`mirror`): the renders of the two are mirror images about the figure (flip_onto moves it onto its own), but flipping swaps
        # the left and right legs - half a stride - so frame k is the pair's frame k + n/2 flipped; its shadow stays its own (the light
        # comes from one side)
        src, n = PAIR[dr], s['frames']
        if not (d / f'frames/walk-{src}-0.png').exists(): continue
        ious = []
        for k in range(n):
            f = CL.flip_onto(Image.open(d / f'frames/walk-{src}-{(k + n // 2) % n}.png'), d / f'render/walk-{dr}-{k}.png'); f.save(d / f'frames/walk-{dr}-{k}.png')
            a = np.asarray(f)[..., 3] > 127; r = np.asarray(Image.open(d / f'render/walk-{dr}-{k}.png'))[..., 3] > 128
            ious.append(float((a & r).sum() / max(1, (a | r).sum())))
        report[dr] = {'overlap': ious, 'head_scale': [1.0] * n, 'mirrored_from': src}
        print(f'finish: walk {dr} flipped from {src}, overlap {min(ious):.2f}-{max(ious):.2f}', flush=True)
    groups = idle_groups()
    for g, ds in enumerate(groups):
        if not (d / f'draw/idle-drawn-{g}.png').exists(): continue
        sh = Image.open(d / f'draw/idle-drawn-{g}.png').convert('RGB')
        for n, x in enumerate(ds):
            f, iou = CL.fit_to_render(cut(d, d / f'draw/idle-drawn-{g}.png', n), Image.open(d / f'render/idle-{x}.png').convert('RGBA'))
            CL.defringe(CL.clear_white_unless_ai(f, Image.open(d / f'render/idle-{x}.png'))).save(d / f'frames/idle-{x}.png'); report[f'idle {x}'] = iou
    if s['kind'] != 'animal': even_heads(s, d, report, 'idle'); head_fit(s, d, report, 'idle')
    n = TU.apply(SPEC_PATH) if SPEC_PATH else 0                              # what was painted in touchup.py, laid on again
    if n: report['touchup'] = n
    pack(s, d, report)
    low = low_sheets(s, d)
    if low: print(f"finish: {len(low)} sheets have a frame under {s['redo_below']} - look at them; `redraw` tries again (a sheet twice, then its low frames alone), keeping the better")


def low_sheets(s, d):
    """[(facing, sheet)] whose frames fit their renders worst: any frame under `redo_below` (0.75) - the model copied another half's
    poses, or drew the legs its own way"""
    rep = json.loads((d / 'out/character.json').read_text())['report']; out = []
    if rep.get('draw') is False: return out
    for dr in DIRS:
        if (rep.get(dr) or {}).get('mirrored_from') or (rep.get(dr) or {}).get('from'): continue
        ov = (rep.get(dr) or {}).get('overlap') or []; cov = (rep.get(dr) or {}).get('held') or [1.0] * len(ov); ext = (rep.get(dr) or {}).get('extra') or [0.0] * len(ov)
        for g in range(0, len(ov), 4):
            wrong = min(cov[g:g + 4]) < HELD_MIN or max(ext[g:g + 4]) > EXTRA_MAX            # the carried thing in the other hand, or where the render has none
            if min(ov[g:g + 4]) < s['redo_below'] or wrong: out.append((dr, g // 4, min(ov[g:g + 4]), sum(ov[g:g + 4]) / len(ov[g:g + 4])))
    return out


def tries(d, f):
    p = d / f'draw/{f}.tried'
    return int(p.read_text() or 1) if p.exists() else 0


def draw_single(s, d, dr, k):
    """one walk frame drawn alone: its render in the second cell of a sheet like the others (the rest left white), so it comes out at
    the sheets' scale and is cut the same way → draw/walk-<facing>-single-<k>.png"""
    paths = [d / f'render/walk-{dr}-{i}.png' for i in range(s['frames'])]; bb = union(paths)
    blank = Image.new('RGBA', Image.open(paths[k]).size, (0, 0, 0, 0)); bp = d / 'draw/blank.png'; blank.save(bp)
    rs = d / f'draw/walk-{dr}-single-{k}-render.png'; sheet_of([bp, paths[k], bp, bp], bb, rs)
    who = 'animal' if s['kind'] == 'animal' else 'person'
    imgs, words = refs_and_words(s, d, [(d / f'draw/walk-{dr}-drawn-{k // 4}.png', f'the rest of this walk, already drawn: exactly the same {who}, size and style')])
    hold = s.get('hold'); held = held_words(hold, d, 'walk', dr, [held_where(d, stem_of('walk', dr, k), 2)] if hold else [])
    P = (f"Image 1 is a sheet of four cells with ONE figure in it, in the second cell: a 3D render of a {who} in one moment of a walk, seen from a "
         "game camera from above. Redraw THAT figure as a finished illustration at exactly the same position, size and pose - the legs, the "
         + ("tail" if who == 'animal' else "arms") + " and the head exactly as the render - and leave the other three cells plain white, nothing in them. "
         f"THE HEAD: {head_words(dr, who == 'animal')}.{held} {words}\n" + frame_rules(s, bool(hold), hand_of(hold)))
    (d / f'draw/walk-{dr}-single-{k}-prompt.txt').write_text(P)
    out = d / f'draw/walk-{dr}-single-{k}.png'
    try: return gpt(P, [rs] + imgs, out, '1536x1024')
    except Refused: print(f'draw: {out.name} turned down by OpenAI\'s safety check three times - left as it was; run it again later, or say less about skin and length in the description'); return 0


def redraw_actions(s, d, args):
    """the actions' sheets with a frame under `redo_below` drawn again (up to twice each); each keeps whichever drawing fits better → how many"""
    rep = {}; todo = []; looked = []
    for name in s['actions']: finish_action(s, d, name, rep)          # (the overlaps as the frames are fitted now)
    for name, a in s['actions'].items():
        for dr in action_dirs(s):
            e = rep.get(f'{name} {dr}') or {}; ov = e.get('overlap') or []; cov = e.get('held') or [1.0] * len(ov); ext = e.get('extra') or [0.0] * len(ov)
            for g in range(0, len(ov), 4):
                wrong = min(cov[g:g + 4]) < HELD_MIN or max(ext[g:g + 4]) > EXTRA_MAX      # the weapon on the other side, or another moment's
                low = min(ov[g:g + 4]) < s['redo_below']
                if (wrong or (low and getattr(args, 'low', False))) and tries(d, f'{name}-{dr}-drawn-{g // 4}') < 2:
                    todo.append((name, dr, g // 4, sum(ov[g:g + 4]) / len(ov[g:g + 4]), min(ov[g:g + 4])))
                elif low: looked.append(f'{name} {dr} {g + 1}-{g + 4} ({min(ov[g:g + 4]):.2f})')
    if looked: print('redraw: a little off the render (left as drawn - look at them; `redraw --low` draws them again too): ' + ', '.join(looked))
    if not todo: return 0
    print('redraw: ' + ', '.join(f'{n} {dr} {g * 4 + 1}-{g * 4 + 4} (lowest {lo:.2f})' for n, dr, g, _, lo in todo))
    if not gate(args, f'redraw: {len(todo)} action sheets, about ${len(todo) * 0.11:.2f} (OpenAI)'): return 0
    for n, dr, g, _, _ in todo:
        f = d / f'draw/{n}-{dr}-drawn-{g}.png'; f.replace(f.with_suffix('.prev.png'))
        draw_walk(s, d, dr, False, [g], name=n)
        if not f.exists(): f.with_suffix('.prev.png').replace(f); continue
        (d / f'draw/{n}-{dr}-drawn-{g}.tried').write_text(str(tries(d, f'{n}-{dr}-drawn-{g}') + 1))
    new = {}
    for n in {x[0] for x in todo}: finish_action(s, d, n, new)
    back = []
    def wrongs(e, g):                                   # frames of a sheet with the held thing in the wrong place
        cov, ext = (e.get('held') or [1.0] * 8)[g * 4:g * 4 + 4], (e.get('extra') or [0.0] * 8)[g * 4:g * 4 + 4]
        return sum(c < HELD_MIN or x > EXTRA_MAX for c, x in zip(cov, ext))
    for n, dr, g, old, _ in todo:
        e = new.get(f'{n} {dr}') or {}; ov = e.get('overlap') or []; m = sum(ov[g * 4:g * 4 + 4]) / max(1, len(ov[g * 4:g * 4 + 4]))
        w0, w1 = wrongs(rep.get(f'{n} {dr}') or {}, g), wrongs(e, g)
        better = (w1, -m) <= (w0, -old)                  # fewer weapons in the wrong place first, then the better overlap
        print(f'redraw: {n} {dr} {g * 4 + 1}-{g * 4 + 4}: overlap {old:.2f} → {m:.2f}, weapon wrong in {w0} → {w1} frames', '' if better else ' - worse, the earlier drawing kept')
        if not better:
            f = d / f'draw/{n}-{dr}-drawn-{g}.png'
            if f.with_suffix('.prev.png').exists(): f.replace(f.with_suffix('.worse.png')); f.with_suffix('.prev.png').replace(f); back.append(n)
    for n in set(back): finish_action(s, d, n, new)
    whole = json.loads((d / 'out/character.json').read_text())['report']; whole.update(rep); whole.update(new); pack(s, d, whole)
    return len(todo)


def redraw(s, d, args):
    """a sheet with a frame under `redo_below` drawn again, up to twice; then a facing still under it is settled with its mirror pair
    (east/west, north-east/north-west, south-east/south-west): the pair drawn too if it was being flipped, and whichever of the two fits its
    renders better is flipped onto the other; south and north, which have no pair, get their low frames drawn alone (once).
    With "mirror": "never" (or a "hold" in the spec) nothing is flipped: every facing is settled as south and north are.
    Each time the drawing that fits better is kept."""
    if not (d / 'out/character.json').exists(): sys.exit('redraw: run `finish` first')
    if s['actions']: redraw_actions(s, d, args)
    rep = json.loads((d / 'out/character.json').read_text())['report']
    low = low_sheets(s, d)
    sheets = [x for x in low if tries(d, f'walk-{x[0]}-drawn-{x[1]}') < 2]
    done = {x[0] for x in low if tries(d, f'walk-{x[0]}-drawn-{x[1]}') >= 2}          # facings whose low sheets were drawn twice
    flip = not s['never_flip']                            # "mirror": "never" (or something carried): every facing is settled as south and north are - its low frames drawn alone
    pairs = sorted(x for x in done if flip and x in PAIR and not tries(d, f'pair-{x}'))
    singles = [(dr, k, rep[dr]['overlap'][k]) for dr, g, _, _ in low if dr in done and (dr not in PAIR or not flip) and tries(d, f'walk-{dr}-drawn-{g}') >= 2
               for k in range(g * 4, min(g * 4 + 4, s['frames'])) if rep[dr]['overlap'][k] < s['redo_below'] and not tries(d, f'walk-{dr}-single-{k}')]
    groups = -(-s['frames'] // 4)
    pair_sheets = {p: [g for g in range(groups) if not (d / f'draw/walk-{PAIR[p]}-drawn-{g}.png').exists()] for p in pairs}
    if not sheets and not pairs and not singles: return print(f"redraw: nothing under {s['redo_below']} left to try")
    if sheets: print('redraw: sheets ' + ', '.join(f'{dr} {g * 4 + 1}-{g * 4 + 4} (lowest {lo:.2f}, try {tries(d, f"walk-{dr}-drawn-{g}") + 1})' for dr, g, lo, _ in sheets))
    for p in pairs: print(f'redraw: {p} still low after two tries - its pair {PAIR[p]} ' + (f'drawn ({len(pair_sheets[p])} sheets) and ' if pair_sheets[p] else '') + 'the better of the two flipped onto the other')
    if singles: print('redraw: single frames ' + ', '.join(f'{dr} {k + 1} ({v:.2f})' for dr, k, v in singles))
    n = len(sheets) + sum(len(v) for v in pair_sheets.values()) + len(singles)
    if n and not gate(args, f'redraw: {n} drawings, about ${n * 0.11:.2f} (OpenAI)'): return
    before = {}
    for dr, g, lo, mean in sheets:
        f = d / f'draw/walk-{dr}-drawn-{g}.png'; f.replace(f.with_suffix('.prev.png'))
        draw_walk(s, d, dr, False, [g])
        if not f.exists(): f.with_suffix('.prev.png').replace(f); continue       # turned down: the drawing it had stays, not counted as a try
        before[('sheet', dr, g)] = mean; (d / f'draw/walk-{dr}-drawn-{g}.tried').write_text(str(tries(d, f'walk-{dr}-drawn-{g}') + 1))
    for p in pairs:
        if pair_sheets[p]: draw_walk(s, d, PAIR[p], False, pair_sheets[p])
        set_mirror(s, d, p, ''); (d / f'draw/pair-{p}.tried').write_text('1')               # both drawn, to compare
    for dr, k, v in singles:
        draw_single(s, d, dr, k)
        if (d / f'draw/walk-{dr}-single-{k}.png').exists(): (d / f'draw/walk-{dr}-single-{k}.tried').write_text('1'); before[('single', dr, k)] = v
    finish(s, d)
    rep = json.loads((d / 'out/character.json').read_text())['report']; again = False
    for p in pairs:
        a, b = p, PAIR[p]; ma, mb = (sum(rep[x]['overlap']) / len(rep[x]['overlap']) for x in (a, b))
        print(f'redraw: {a} {ma:.2f} / {b} {mb:.2f} - each frame of both: the better of its own and the other flipped'); set_mirror(s, d, a, 'best'); again = True
    for (kind, dr, x), old in before.items():
        ov = rep[dr]['overlap']; new = (sum(ov[x * 4:x * 4 + 4]) / len(ov[x * 4:x * 4 + 4])) if kind == 'sheet' else ov[x]
        name = f'{dr} {x * 4 + 1}-{x * 4 + 4}' if kind == 'sheet' else f'{dr} frame {x + 1}'
        print(f'redraw: {name}: {old:.2f} → {new:.2f}', '' if new >= old else ' - worse, the earlier drawing kept')
        if new < old:
            again = True
            if kind == 'sheet': f = d / f'draw/walk-{dr}-drawn-{x}.png'; f.replace(f.with_suffix(f'.worse{tries(d, f"walk-{dr}-drawn-{x}")}.png')); f.with_suffix('.prev.png').replace(f)   # the worse kept to look at
            else: (d / f'draw/walk-{dr}-single-{x}.png').replace(d / f'draw/walk-{dr}-single-{x}.worse.png')
    if again: finish(s, d)
    preview(s, d)


# --- more actions beside the walk ("actions": ["run", "jump"]) ------------------------------------------------------------------------
# Tripo's v3.0 biped presets: run, jump, dive, climb, fall, hurt, turn (slash and shoot hold a weapon the model hasn't got); with your own
# rig ("rig_glb") any clip in it, by name. Each is rendered, drawn and finished like the walk, in its own strips.
ACTION_DEFAULTS = {'run': {'loop': True, 'words': 'running (a quick run: both feet off the ground between strides, the back leg kicked up high behind '
                           'exactly as far as the render has it)'},
                   'jump': {'loop': False, 'words': 'jumping on the spot (crouch, push off, in the air, land)'},
                   'slash': {'loop': False, 't0': 0.6, 't1': 2.7, 'head': 'as_render',      # (Tripo's slash: its swing; the rest of its 6.6 s is standing)
                             'words': 'a slash with what is held in the right hand',       # (no moves spelled out: "raise it overhead, swing it down" had it drawn overhead where the render has it at the side)
                             'pose': 'Each cell is ONE moment of it: draw the arm and the held thing exactly where that cell\'s render has them - overhead '
                                     'only in the cells whose render has it overhead, out to the side or low where the render has it there.'},
                   'dive': {'loop': False}, 'climb': {'loop': True}, 'fall': {'loop': False}, 'hurt': {'loop': False}, 'turn': {'loop': False}}
# A HELD THING IS SAID PART BY PART, with each part's colour and what it must not become - above all the parts AT THE HAND. Told "draw it
# as the render shows it, in the colour the render has", the image model drew the umbrella's shaft silver on one sheet and brown on the
# next, and where both fists were on it moved them together and filled the gap with handle: the end near the body is small, half
# covered by fingers and next to the coat, and that is where it guesses. Named - "a dark brown handle in the fist; then a bare silver
# shaft as long as the render has it, never brown; the hands as far apart as the render" - it came right on the first drawing.
HOLD_WORDS = {'umbrella': 'In the RIGHT hand: a closed, furled umbrella held like a sword by its hooked handle - draw it exactly where and how the '
                         'render shows it, in the colours the render has. It has THREE PARTS, the same in every cell: a dark brown wooden J-shaped handle, in '
                         'the fist; then a straight bare SILVER METAL shaft, exactly as long as that cell\'s render shows it between the handle and the '
                         'canopy (bare metal: never brown, never wood, never wrapped in cloth), and AS THICK as the render shows it - a solid metal rod, never a thin line '
                         'or a wire; where the coat, a hand or a leg hides part of it, the part that shows keeps that same thickness; then the canopy wrapped tight, with a small silver tip. '
                         'Where the render shows the silver shaft between the two hands, draw the silver shaft there, the hands as far apart as the '
                         'render has them - do not move the hands together and do not lengthen the handle to fill the gap. '
                         'It is on the SAME side of the body and points the SAME way as in that cell\'s render, also when she is seen from '
                         'behind (do not swap it to the other hand or the other side), raised only where the render raises it.'}
HOLD_WORDS['pistol'] = ('In the RIGHT hand: a small handgun - draw it exactly where and how the render shows it, the same size, pointing the same way. '
                        'It has TWO PARTS, the same in every cell: a dark brown grip, in the fist; and above it a dark grey metal slide and barrel, as long as '
                        'the render has it (not longer, no silencer, no scope). It stays in the SAME hand and on the SAME side of the body as in that '
                        'cell\'s render, also when the figure is seen from behind (do not swap it to the other hand or the other side); the other hand is empty.')
HOLD_WORDS['watergun'] = ('In the RIGHT hand: a small toy water pistol, bright plastic - draw it exactly where and how the render shows it, the same size, pointing the '
                          'same way. Its PARTS, the same in every cell: an orange grip, in the fist; a bright blue body with a short orange nozzle at its end; and a small '
                          'round green water tank on top of the body. A toy: chunky and rounded, in the colours the render has - not a real gun, not black or metal. '
                          'It stays in the SAME hand and on the SAME side of the body as in that cell\'s render, also when the figure is seen from behind (do not swap '
                          'it to the other hand or the other side); the other hand is empty.')
TRIPO_PRESETS = {'run', 'jump', 'dive', 'climb', 'fall', 'hurt', 'turn', 'slash', 'shoot'}


EFFECTS = Path(__file__).resolve().parent.parent / 'effects'          # the looks that come with the skill (effects.json) and their pieces


def effect_of(tr, spec_dir):
    """an action's "trail" → what the renderer is handed, or None: true (the plain band), a style's name ("water"), or
    {"style": ..., and anything of that style to change: "color", "alpha", "span", "width", "band", "image" (the user's own strip of
    square cells in place of the style's first piece), "pieces" (the whole list)}. The pieces' pictures go as data URLs."""
    if not tr: return None
    tr = {} if tr is True else {'style': tr} if isinstance(tr, str) else dict(tr)
    looks = {k: v for k, v in json.loads((EFFECTS / 'effects.json').read_text()).items() if k != '_'}
    style = tr.pop('style', 'plain')
    if style not in looks: sys.exit(f'spec: "trail": no style "{style}" - one of {", ".join(looks)}')
    cfg = json.loads(json.dumps(looks[style])); own = tr.pop('image', None); cfg.update(tr)
    if own: cfg['pieces'] = [dict((cfg.get('pieces') or [{}])[0], image=own)] + list((cfg.get('pieces') or [])[1:])
    for p in cfg.get('pieces') or []:
        if p.get('blob'): continue          # (a body of water or flame: soft round weights, no picture)
        f = next((x for x in (Path(spec_dir) / p['image'], EFFECTS / p['image']) if x.exists()), None)
        if f is None: sys.exit(f'spec: "trail": the piece picture {p["image"]} was not found (beside the spec, or in {EFFECTS})')
        w, h = Image.open(f).size
        if w % h: sys.exit(f'spec: "trail": {f} is {w}x{h} - a strip of SQUARE cells is wanted (its width a multiple of its height)')
        p['cells'] = w // h; p['data'] = 'data:image/png;base64,' + base64.b64encode(f.read_bytes()).decode()
    return cfg


def actions_of(s):
    """the spec's "actions" → {name: {clip, t0, t1 (None: the whole clip), frames, loop, words}}; a name alone takes the defaults"""
    out = {}
    for a in s.get('actions') or []:
        a = {'name': a} if isinstance(a, str) else dict(a); n = a['name']
        if n in ('walk', 'idle', 'sit'): sys.exit(f'spec: "{n}" is made already - not an action')
        e = {'clip': n, 't0': 0, 't1': None, 'frames': s['frames'], 'loop': True, 'words': n}
        e.update(ACTION_DEFAULTS.get(n, {})); e.update({k: v for k, v in a.items() if k != 'name'})
        if 'hold' not in e and s.get('hold'): e['hold'] = s['hold']                  # what the character carries; "hold": false in an action: the hand empty there
        if not e.get('hold'): e.pop('hold', None)
        if hand_of(e.get('hold')) == 'left' and 'words' not in a: e['words'] = e['words'].replace('right hand', 'left hand')
        out[n] = e
    return out


def between_ends(s, a):
    """an action with "between": [from, to] → ([(clip, time) of each end], the action with an end's clip, held thing and canvas): its
    frames are the poses part-way from one pose to another. An end is "walk", "idle" or an action's name - its FIRST pose - or
    "<action>:end", its LAST (the pose an attack stops in: ["slash:end", "walk"] brings the body back up into the walk)."""
    def end(x):
        x, _, at = x.partition(':')
        if at not in ('', 'end'): sys.exit(f'spec: "between": "{x}:{at}" - only "<action>:end" (its last pose) is known')
        if x == 'walk': return s['walk']['clip'], s['walk']['t1' if at else 't0'], {}
        if x == 'idle': return s['idle']['clip'], s['idle']['t'], {}
        if x not in s['actions']: sys.exit(f'spec: "between": no action "{x}" (walk, idle or one of {", ".join(s["actions"])})')
        e = s['actions'][x]
        if at and e['t1'] is None: sys.exit(f'spec: "between": "{x}:end" needs that action\'s "t1" (where its clip is cut)')
        return e['clip'], e['t1'] if at else e['t0'], e
    ends = [end(x) for x in a['between']]
    a = dict(a, clip=ends[1][0], t0=0, t1=0, loop=False)
    for k in ('hold', 'canvas'):          # what is held, and the room for it: the far end's, or else the near end's
        v = ends[1][2].get(k) or ends[0][2].get(k)
        if v and k not in a: a[k] = v
    return [e[:2] for e in ends], a


def action_dirs(s):
    return [x for x in DIRS if x not in s['mirrored']]


def pack_px(s, d, px):
    """`pack`: out/ again from frames/, or with --px a smaller (or bigger) set in its own folder, the report kept"""
    old = d / 'out/character.json'; rep = json.loads(old.read_text()).get('report', {}) if old.exists() else {}
    if not px: return pack(s, d, rep)
    s['frame_px'] = px; (d / f'out-{px}px').mkdir(exist_ok=True); pack(s, d, rep, f'out-{px}px')


def pack(s, d, report, out='out'):
    """strips at frame_px: one box for every frame, so the feet stay put; the anchor is the 3D ground under the character's middle, or
    with "anchor": "soles" the bottom of its shoes standing (what a game whose other characters stand on their soles wants). `out`: the
    folder they go in (`pack --px 64` → out-64px/, from the same full-size frames)"""
    own = tuple(f'{n}-' for n in ['sit'] + list(s['actions']))
    files = [f for f in sorted((d / 'frames').glob('*.png')) if not f.name.startswith(own)]   # (seated views and actions get their own box below)
    if not files: sys.exit('finish: nothing drawn yet')
    S = Image.open(files[0]).size[0]; bb = union(files); info = json.loads((d / 'render/render.json').read_text())
    foot = info['footY'] * S
    if s['anchor'] == 'soles' and (d / 'frames/idle-south.png').exists():     # the bottom of the shoes standing, not the 3D ground under the
        foot = float(np.nonzero((np.asarray(Image.open(d / 'frames/idle-south.png'))[..., 3] > 100).any(1))[0][-1]) + 2   # middle (4-7 game px higher)
    box = [bb[0] - 4, bb[1] - 4, bb[2] + 4, max(bb[3] + 4, int(foot) + 2)]
    side = max(box[2] - box[0], box[3] - box[1]); cx = (box[0] + box[2]) / 2
    box = [round(cx - (box[2] - box[0]) / 2), box[1], round(cx + (box[2] - box[0]) / 2), box[3]]
    k = s['frame_px'] / (box[3] - box[1]); fw, fh = round((box[2] - box[0]) * k), s['frame_px']
    meta = {'frame': [fw, fh], 'anchor': [round((S / 2 - box[0]) / (box[2] - box[0]), 4), round((foot - box[1]) / (box[3] - box[1]), 4)], 'walk': {}, 'idle': {},
            'fps': round(s['frames'] / (s['walk']['t1'] - s['walk']['t0']), 2), 'shadows': {'walk': {}, 'idle': {}}, 'report': report}
    (d / out / 'shadows').mkdir(exist_ok=True)

    def shadow(src, name):
        """the frame's 3D shadow at the strips' scale → {file, offset}: its top-left from the frame's top-left, in frame px (it falls
        away from the light, often past the frame's edge)"""
        if s['shadow'] not in ('3d', 'flat') or not src.exists(): return None
        sh, (x0, y0) = CL.shadow_3d(src)
        if sh is None: return None
        sh = sh.resize((max(1, round(sh.width * k)), max(1, round(sh.height * k))), Image.LANCZOS); sh.save(d / out / f'shadows/{name}.png', optimize=True)
        return {'file': f'shadows/{name}.png', 'offset': [round((x0 - box[0]) * k), round((y0 - box[1]) * k)]}
    for dr in DIRS:
        fr = [d / f'frames/walk-{dr}-{i}.png' for i in range(s['frames'])]
        if all(p.exists() for p in fr):
            st = Image.new('RGBA', (fw * len(fr), fh), (0, 0, 0, 0))
            for i, p in enumerate(fr): st.alpha_composite(Image.open(p).crop(box).resize((fw, fh), Image.LANCZOS), (i * fw, 0))
            st.save(d / out / f'walk-{dr}.png'); meta['walk'][dr] = f'walk-{dr}.png'
            shs = [shadow(d / f'render/walk-{dr}-{i}-s.png', f'walk-{dr}-{i}') for i in range(len(fr))]
            if all(shs): meta['shadows']['walk'][dr] = shs
        p = d / f'frames/idle-{dr}.png'
        if p.exists():
            Image.open(p).crop(box).resize((fw, fh), Image.LANCZOS).save(d / out / f'idle-{dr}.png'); meta['idle'][dr] = f'idle-{dr}.png'
            sh = shadow(d / f'render/idle-{dr}-s.png', f'idle-{dr}')
            if sh: meta['shadows']['idle'][dr] = sh
    for name, a in s['actions'].items():
        fr = {dr: [d / f'frames/{name}-{dr}-{i}.png' for i in range(a['frames'])] for dr in DIRS}
        fr = {dr: ps for dr, ps in fr.items() if all(p.exists() for p in ps)}
        if not fr: continue
        Sa = Image.open(next(iter(fr.values()))[0]).size[0]; fa = foot + (Sa - S) / 2          # (a bigger canvas, the same middle and scale)
        ab = union([p for ps in fr.values() for p in ps]); ab = [ab[0] - 4, ab[1] - 4, ab[2] + 4, max(ab[3] + 4, int(fa) + 2)]
        aw, ah = round((ab[2] - ab[0]) * k), round((ab[3] - ab[1]) * k)
        e = {'frame': [aw, ah], 'anchor': [round((Sa / 2 - ab[0]) / (ab[2] - ab[0]), 4), round((fa - ab[1]) / (ab[3] - ab[1]), 4)], 'frames': a['frames'],
             'loop': a['loop'], 'fps': meta['fps'], 'strips': {}, 'shadows': {}}
        tm = (info.get('actions') or {}).get(name)
        if tm and tm['t1'] > tm['t0']: e['fps'] = round((a['frames'] if a['loop'] else a['frames'] - 1) / (tm['t1'] - tm['t0']), 2)   # the clip's own pace
        for dr, ps in fr.items():
            st = Image.new('RGBA', (aw * len(ps), ah), (0, 0, 0, 0))
            for i, p in enumerate(ps): st.alpha_composite(Image.open(p).crop(ab).resize((aw, ah), Image.LANCZOS), (i * aw, 0))
            st.save(d / out / f'{name}-{dr}.png'); e['strips'][dr] = f'{name}-{dr}.png'
            shs = []
            for i in range(len(ps)):
                src = d / f'render/{name}-{dr}-{i}-s.png'
                if s['shadow'] not in ('3d', 'flat') or not src.exists(): break
                shi, (x0, y0) = CL.shadow_3d(src)
                if shi is None: break
                shi = shi.resize((max(1, round(shi.width * k)), max(1, round(shi.height * k))), Image.LANCZOS); shi.save(d / out / f'shadows/{name}-{dr}-{i}.png', optimize=True)
                shs.append({'file': f'shadows/{name}-{dr}-{i}.png', 'offset': [round((x0 - ab[0]) * k), round((y0 - ab[1]) * k)]})
            if len(shs) == len(ps): e['shadows'][dr] = shs
            # the swing's trail ("trail"): one strip a facing, as many cells as the action has frames (empty where the swing is slow), in a
            # box of its own with its offset from the frame's top-left - laid OVER the body at the same frame number
            tx = max(1, int((a['trail'].get('frames_x') if isinstance(a.get('trail'), dict) else 0) or (effect_of(a.get('trail'), d.parent) or {}).get('frames_x') or 1))
            ts = {i: Image.open(d / f'render/{name}-{dr}-{i}-t.png').convert('RGBA') for i in range(len(ps) * tx) if (d / f'render/{name}-{dr}-{i}-t.png').exists()}
            bx = [t.getbbox() for t in ts.values() if t.getbbox()]
            if a.get('trail') and bx:
                tb = [min(b[0] for b in bx), min(b[1] for b in bx), max(b[2] for b in bx), max(b[3] for b in bx)]
                tw, th = max(1, round((tb[2] - tb[0]) * k)), max(1, round((tb[3] - tb[1]) * k))
                tst = Image.new('RGBA', (tw * len(ps) * tx, th), (0, 0, 0, 0))
                for i, t in ts.items(): tst.paste(t.crop(tb).resize((tw, th), Image.LANCZOS), (i * tw, 0))
                tst.save(d / out / f'{name}-{dr}-trail.png', optimize=True)
                e.setdefault('trail', {})[dr] = {'file': f'{name}-{dr}-trail.png', 'frame': [tw, th], 'offset': [round((tb[0] - ab[0]) * k), round((tb[1] - ab[1]) * k)], 'frames': len(ps) * tx, 'per_frame': tx}      # per_frame effect cells to each body frame: play it at per_frame times the fps
        meta.setdefault('actions', {})[name] = e
    # seated (charpipe sit): one frame a facing at the walk's scale, in a box of their own (the knees reach further); each with the seat's
    # point on it - put that on the chair's seat
    seats = json.loads((d / 'render/sit.json').read_text()) if (d / 'render/sit.json').exists() else {}
    sits = [d / f'frames/sit-{dr}.png' for dr in DIRS if (d / f'frames/sit-{dr}.png').exists()]
    if sits:
        sb = union(sits); sb = [sb[0] - 4, sb[1] - 4, sb[2] + 4, sb[3] + 4]; sw, shh = round((sb[2] - sb[0]) * k), round((sb[3] - sb[1]) * k)
        meta['sit'] = {'frame': [sw, shh]}
        for dr in DIRS:
            p = d / f'frames/sit-{dr}.png'
            if not p.exists(): continue
            Image.open(p).crop(sb).resize((sw, shh), Image.LANCZOS).save(d / out / f'sit-{dr}.png')
            e = {'file': f'sit-{dr}.png'}
            if dr in seats:
                sx, sy = seats[dr]['seat']; e['seat'] = [round((sx * S - sb[0]) / (sb[2] - sb[0]), 4), round((sy * S - sb[1]) / (sb[3] - sb[1]), 4)]
                e['seat_height'] = seats[dr]['seatY']
            src = d / f'render/sit-{dr}-s.png'
            if s['shadow'] in ('3d', 'flat') and src.exists():
                shi, (x0, y0) = CL.shadow_3d(src)
                if shi is not None:
                    if CL.GRADED: shi.putalpha(shi.getchannel('A').point(lambda v: round(v * 0.3 / CL.shadow_alpha())))          # (seated: the one hard shape still - kept as dark as it was under the set's new "shadow_alpha")
                    shi = shi.resize((max(1, round(shi.width * k)), max(1, round(shi.height * k))), Image.LANCZOS); shi.save(d / out / f'shadows/sit-{dr}.png', optimize=True)
                    e['shadow'] = {'file': f'shadows/sit-{dr}.png', 'offset': [round((x0 - sb[0]) * k), round((y0 - sb[1]) * k)]}
            meta['sit'][dr] = e
    # how dark to show the shadow strips: 0.56 for shadows as light falls (their alpha is the darkness against the deepest), 0.3 for the old hard shape
    meta['shadow_alpha'] = CL.shadow_alpha() if CL.GRADED else 0.3; meta['shadow_colour'] = [40, 30, 24]
    if CL.SHADOW_STRENGTH != 1: meta['shadow_strength'] = CL.SHADOW_STRENGTH
    (d / out / 'character.json').write_text(json.dumps(meta, indent=1))
    print(f"finish: {d / out}  {len(meta['walk'])} walks, {len(meta['idle'])} standing, frame {fw}x{fh}, anchor {meta['anchor']}, "
          f"3D shadows for {len(meta['shadows']['walk'])} walks" + ('' if meta['shadows']['walk'] else ' (none: re-run `render` for the -s.png shadows)'))


def with_shadow(d, frame, sh, pad, bg=(240, 236, 228, 255)):
    """one frame over its shadow (at the set's "shadow_alpha") on a backdrop the frame's size plus `pad` (left, top) - the shadow falls up and away"""
    pl, pt = pad; c = Image.new('RGBA', (frame.width + pl, frame.height + pt), bg)
    if sh:
        k_ = json.loads((d / 'out/character.json').read_text()).get('shadow_alpha', 0.3); a = Image.open(d / 'out' / sh['file']).getchannel('A').point(lambda v: v * k_)
        c.paste(Image.new('RGBA', a.size, (40, 30, 24, 255)), (sh['offset'][0] + pl, sh['offset'][1] + pt), a)
    c.alpha_composite(frame, (pl, pt)); return c


def preview(s, d):
    meta = json.loads((d / 'out/character.json').read_text()); fw, fh = meta['frame']; n = s['frames']
    S = meta.get('shadows') or {'walk': {}, 'idle': {}}
    every = [x for v in S['walk'].values() for x in v] + list(S['idle'].values())
    pad = (max([0] + [-x['offset'][0] for x in every]), max([0] + [-x['offset'][1] for x in every])); cw, ch = fw + pad[0], fh + pad[1]
    sheet = Image.new('RGBA', ((n + 1) * cw, len(DIRS) * ch), (240, 236, 228, 255))
    for r, dr in enumerate(DIRS):
        if dr in meta['walk']:
            st = Image.open(d / 'out' / meta['walk'][dr])
            for i in range(n): sheet.alpha_composite(with_shadow(d, st.crop((i * fw, 0, (i + 1) * fw, fh)), S['walk'].get(dr, [None] * n)[i], pad), (i * cw, r * ch))
        if dr in meta['idle']: sheet.alpha_composite(with_shadow(d, Image.open(d / 'out' / meta['idle'][dr]), S['idle'].get(dr), pad), (n * cw, r * ch))
    sheet.convert('RGB').save(d / 'out/sheet.png')
    for dr, f in meta['walk'].items():
        st = Image.open(d / 'out' / f)
        fr = [with_shadow(d, st.crop((i * fw, 0, (i + 1) * fw, fh)), S['walk'].get(dr, [None] * n)[i], pad).convert('RGB') for i in range(n)]
        fr[0].save(d / f'out/walk-{dr}.gif', save_all=True, append_images=fr[1:], duration=round(1000 / meta['fps']), loop=0)
    video(d, meta, S, pad)
    print(f"preview: {d / 'out/sheet.png'}, walk-*.gif" + (' and walk-all.mp4' if (d / 'out/walk-all.mp4').exists() else ''))


def video(d, meta, S, pad, loops=6):
    """every facing walking at once, side by side, at the walk's own speed (out/walk-all.mp4) - easier to judge than eight GIFs: a head
    that grows, a frame that jumps, a facing whose stride is off. Only with ffmpeg on the PATH"""
    import subprocess, tempfile
    if not shutil.which('ffmpeg') or not meta['walk']: return
    fw, fh = meta['frame']; dirs = [x for x in DIRS if x in meta['walk']]; strips = {x: Image.open(d / 'out' / meta['walk'][x]) for x in dirs}
    n = min(st.width // fw for st in strips.values()); k = min(1.0, 1600 / ((fw + pad[0]) * len(dirs)))
    with tempfile.TemporaryDirectory() as tmp:
        for f in range(n * loops):
            row = Image.new('RGB', ((fw + pad[0]) * len(dirs), fh + pad[1]), (240, 236, 228))
            for j, x in enumerate(dirs):
                i = f % n; row.paste(with_shadow(d, strips[x].crop((i * fw, 0, (i + 1) * fw, fh)), S['walk'].get(x, [None] * n)[i], pad).convert('RGB'), (j * (fw + pad[0]), 0))
            row.resize((round(row.width * k) // 2 * 2, round(row.height * k) // 2 * 2), Image.LANCZOS).save(f'{tmp}/{f:04d}.png')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(meta['fps']), '-i', f'{tmp}/%04d.png', '-vf', 'fps=30',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', str(d / 'out/walk-all.mp4')], check=False)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('step', choices=['turnaround', '3d', 'model', 'rig', 'render', 'draw', 'redraw', 'frame', 'loop', 'finish', 'pack', 'preview', 'facecheck', 'sit'])
    ap.add_argument('--draw', action='store_true', help='sit: draw the seated views (PAID, ~$0.22) and finish them')
    ap.add_argument('--low', action='store_true', help='redraw: an action\'s sheets that are only a little off the render too')
    ap.add_argument('spec'); ap.add_argument('--yes', action='store_true'); ap.add_argument('--again', action='store_true'); ap.add_argument('--only')
    ap.add_argument('--px', type=int, help='pack: frames this many px tall into out-<px>px/ (the drawings resized once; out/ left as it is)')
    ap.add_argument('--no-render', action='store_true', help='rig: stop before the renders')
    ap.add_argument('--facing', help='frame, loop: the facing'); ap.add_argument('--frame', type=int, help='frame: which frame, from 1')
    ap.add_argument('--with', dest='others', help='facecheck: the other characters\' specs, comma-separated')
    ap.add_argument('--apply', action='store_true', help='facecheck: write the factors into the other specs as "head_fit"')
    a = ap.parse_args(); s, d = load(a.spec); SPEC_PATH = a.spec
    {'turnaround': lambda: turnaround(s, d, a), '3d': lambda: make3d(s, d, a), 'model': lambda: model(s, d, a), 'rig': lambda: rig(s, d, a), 'render': lambda: render(s, d, a.only.split(',') if a.only else None),
     'draw': lambda: draw(s, d, a), 'redraw': lambda: redraw(s, d, a), 'frame': lambda: frame_step(s, d, a), 'loop': lambda: loop_gif(s, d, (a.only or 'walk').split(','), a.facing or FRONT), 'finish': lambda: finish(s, d), 'pack': lambda: pack_px(s, d, a.px), 'sit': lambda: sit_draw(s, d, a) if a.draw else sit_render(s, d), 'preview': lambda: preview(s, d),
     'facecheck': lambda: __import__('facecheck').run(a.spec, (a.others or '').split(','), a.apply)}[a.step]()
