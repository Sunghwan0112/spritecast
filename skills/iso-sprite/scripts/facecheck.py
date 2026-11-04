"""facecheck: is a character's head the same size for its height as another's? - facing by facing, by face landmarks (MediaPipe's
Face Landmarker, on this computer), so hair doesn't count: the painted area under the crown read one outfit's full waves as a big head
and made the others' heads 12 % too big when matched by it.

    python charpipe.py facecheck REF.json --with A.json,B.json [--apply]

Measures, on each character's finished strips (out/), the face - forehead (landmark 10) to chin (152) - over chin to the soles (the
lowest painted pixel), the median over the standing picture and the walk frames of each facing. A facing counts when a face is found
in at least 5 of its 9 pictures (the fronts and three-quarters; a profile or a back has none). For each of A, B…:
- the facings with a face found in both: the factor that brings its face ratio to REF's, measured again after each try;
- the rest: the factor that gives them the same drawn-to-3D head ratio its found facings then have (its own renders, `head_vs_render`).
Prints the table and the factors; --apply writes them into each spec as "head_fit" (multiplied into one there already), and `finish`
then rescales the heads about the neck. Needs `pip install mediapipe` (Python 3.9-3.12); the model (3.7 MB) is fetched once into
~/.cache/iso-sprite/models/."""
import json, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image
import charlib as CL

DIRS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
MODEL = Path.home() / '.cache' / 'iso-sprite' / 'models' / 'face_landmarker.task'
URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
MIN_FOUND = 5
PAIR = {'west': 'east', 'east': 'west', 'north-west': 'north-east', 'north-east': 'north-west', 'south-west': 'south-east', 'south-east': 'south-west'}


def detector():
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
    except ImportError:
        sys.exit('facecheck: needs mediapipe - `pip install mediapipe` in a Python 3.9-3.12 environment, and run charpipe.py with that python')
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True); print('facecheck: fetching the face model (3.7 MB) ...', flush=True); urllib.request.urlretrieve(URL, MODEL)
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL)), num_faces=1, min_face_detection_confidence=0.2, min_face_presence_confidence=0.2))

    def face(im):
        """forehead-to-chin over chin-to-soles, or None. The head cut out and made 640 px tall on white for the model"""
        a = np.asarray(im.convert('RGBA')); al = a[..., 3] > 100; ys = np.nonzero(al.any(1))[0]; top, sole = ys[0], ys[-1]
        hb = int(0.30 * (sole - top)); xs = np.nonzero(al[top:top + hb].any(0))[0]
        box = (max(0, xs[0] - 20), max(0, top - 20), min(im.width, xs[-1] + 20), top + hb)
        c = im.convert('RGBA').crop(box); k = 640 / c.height; c = c.resize((round(c.width * k), 640), Image.LANCZOS)
        bg = Image.new('RGB', c.size, (255, 255, 255)); bg.paste(c, (0, 0), c)
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(bg)))
        if not r.face_landmarks: return None
        L = r.face_landmarks[0]; pt = lambda i: (box[0] + L[i].x * bg.width / k, box[1] + L[i].y * bg.height / k)
        (fx, fy), (cx, cy) = pt(10), pt(152)
        return float(np.hypot(cx - fx, cy - fy) / max(1.0, sole - cy))
    return face


def character(spec):
    """(its folder, its spec, {facing: [(the drawn frame (512 canvas), its render)]}) - the frames and renders finish works on"""
    s = json.loads(Path(spec).read_text(encoding='utf-8')); d = Path(spec).resolve().parent / s['name']
    pics = {x: [(d / f'frames/idle-{x}.png', d / f'render/idle-{x}.png')] + [(d / f'frames/walk-{x}-{k}.png', d / f'render/walk-{x}-{k}.png')
                                                                         for k in range(s.get('frames', 8))] for x in DIRS}
    return d, s, {x: [(p, r) for p, r in v if p.exists() and r.exists()] for x, v in pics.items()}


def scaled(p, c, neck):
    im = Image.open(p).convert('RGBA'); return CL.rescale_head(im, c, neck, order=1) if abs(c - 1) > 1e-3 else im


def run(ref, others, apply=False):
    face = detector(); others = [o for o in others if o]
    if not others: sys.exit('facecheck: name the characters to compare with --with A.json,B.json')
    _, rs, rp = character(ref); yard = {}
    for x in DIRS:
        v = [f for f in (face(Image.open(p)) for p, _ in rp[x]) if f]
        if len(v) >= MIN_FOUND: yard[x] = float(np.median(v))
    if not yard: sys.exit(f'facecheck: no face found in {rs["name"]} - is it finished (frames/)?')
    print(f'facecheck: {rs["name"]} face / chin-to-soles: ' + ', '.join(f'{x} {v:.4f}' for x, v in yard.items()))
    for spec in others:
        d, s, pics = character(spec); neck = s.get('neck', 0.16); fit = {}; table = {}
        for x in yard:
            v = [f for f in (face(Image.open(p)) for p, _ in pics[x]) if f]
            if len(v) < MIN_FOUND: continue
            table[x] = float(np.median(v)) / yard[x]; c = 1.0
            for _ in range(3):
                now = [f for f in (face(scaled(p, c, neck)) for p, _ in pics[x]) if f]; c *= yard[x] / float(np.median(now))
            fit[x] = c
        if not fit: print(f'facecheck: {s["name"]}: no facing with a face found in both - nothing to compare'); continue
        k = float(np.median([CL.head_vs_render(scaled(p, fit[x], neck), r) for x in fit for p, r in pics[x]]))   # drawn to 3D, as the found ones are now
        m = s.get('mirror', True); mirrored = ['west', 'north-west', 'south-west'] if m is True else (m or [])
        for x in DIRS:
            if x in fit or not pics[x] or x in mirrored: continue
            c = 1.0
            for _ in range(3): c *= (k / float(np.median([CL.head_vs_render(scaled(p, c, neck), r) for p, r in pics[x]]))) ** 2
            fit[x] = c
        for x in mirrored:                        # flipped from its pair: the same head
            if x not in table and PAIR[x] in fit: fit[x] = fit[PAIR[x]]
        fit = {x: round(min(1.2, max(0.8, c)), 3) for x, c in fit.items()}
        print(f'facecheck: {s["name"]} against {rs["name"]} (1.00 = the same face for the height): '
              + ', '.join(f'{x} {v:.2f}' for x, v in table.items()))
        print(f'facecheck: {s["name"]} head factors (by face: {", ".join(table)}; the rest by its 3D): '
              + ', '.join(f'{x} x{c}' for x, c in fit.items()), flush=True)
        if apply:
            raw = json.loads(Path(spec).read_text(encoding='utf-8')); old = raw.get('head_fit') or {}
            raw['head_fit'] = {x: round(old.get(x, 1.0) * c, 3) for x, c in fit.items()}
            Path(spec).write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding='utf-8')
            print(f'facecheck: written into {spec} as "head_fit" - run `finish` to apply it')
