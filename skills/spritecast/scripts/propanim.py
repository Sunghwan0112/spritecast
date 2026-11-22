"""propanim: a prop's animation (proprig.py's poses) drawn as pixel art FOUR FRAMES TO A SHEET - drawn together, so they match - read
back cell by cell, each put where its pose's render is, then see-through by each pose's own 3D thickness ("translucent" in the spec,
with its "pulse": the thin parts fading once a loop).
    python propanim.py PROP.json            # the sheets and the cost - spends nothing
    python propanim.py PROP.json --yes      # draws (~$0.08 a sheet: 8 frames are 2), reads -> <prop>/out-pixel/anim.png (a strip),
                                            # anim-solid.png (as drawn), anim.json (frame size, frames, fps), preview-anim.gif
It needs proprig.py's poses and the prop drawn once as pixel art (proppixel.py: the sheets copy its colours, outline and face)."""
import sys, json, time
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import proppixel as PP, translucent as TL, trimesh

spec_p = Path(sys.argv[1]).resolve(); spec = json.loads(spec_p.read_text()); D = spec_p.parent / spec['name']; rig = D / 'rig'; YES = '--yes' in sys.argv
OUTP = D / 'out-pixel'; pj = json.loads((OUTP / 'pixel.json').read_text()); PPM = float(pj.get('px_per_m', 113))
RIG = spec.get('rig') or {}; CW, CH = 768, 512; SW, SH = 1536, 1024
poses = sorted([p for p in rig.glob('pose-*') if p.is_dir()], key=lambda p: int(p.name.split('-')[1]))
rend = [Image.open(p / 'render.png').convert('RGBA') for p in poses]; meta = json.loads((poses[0] / 'render.json').read_text())
box = rend[0].getbbox()
for r in rend[1:]: b = r.getbbox(); box = (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
crops = [r.crop(box) for r in rend]; k = PPM / meta.get('px_per_m', 256)
n_h = max(64, round(crops[0].height * k)); n_w = round(crops[0].width * n_h / crops[0].height)
Z = int(min(CW * 0.9 / n_w, CH * 0.9 / n_h))
if Z < 5: sys.exit(f'propanim: {n_w} x {n_h} squares do not fit four to a sheet with squares of 5 px or more - a smaller --ppm in proppixel.py')
print(f'propanim: {len(crops)} frames, {n_w} x {n_h} squares of {Z} px')


def pix(r):
    a = np.asarray(r, np.float32) / 255; pm = np.dstack([a[..., :3] * a[..., 3:], a[..., 3]])
    ch = [np.asarray(Image.fromarray(pm[..., j]).resize((n_w, n_h), Image.BOX)) for j in range(4)]
    al = ch[3]; rgb = np.clip(np.dstack(ch[:3]) / np.maximum(al, 1e-4)[..., None], 0, 1); return rgb, al >= 0.5


ox, oy = (CW - n_w * Z) // 2, (CH - n_h * Z) // 2
ref = Image.open(OUTP / ('sprite-solid.png' if (OUTP / 'sprite-solid.png').exists() else 'sprite.png')).convert('RGBA')
moves = ' and '.join(x for x in [('the tail sways a few pixels from side to side' if RIG.get('tail', True) else ''), ('the little arms swing a little ' + ('up and down' if (RIG.get('arms') or {}).get('swing') == 'up' else 'to and fro') if RIG.get('arms', True) else '')] if x) or 'parts of it move a little'
sheets = []
for s in range(0, len(crops), 4):
    o = rig / f'sheet-{s // 4}'; o.mkdir(exist_ok=True); sheets.append((o, list(range(s, min(s + 4, len(crops))))))
    gin = Image.new('RGB', (SW, SH), (255, 255, 255)); look = Image.new('RGB', (SW, SH), (255, 255, 255))
    for c, i in enumerate(range(s, min(s + 4, len(crops)))):
        cx, cy = (c % 2) * CW + ox, (c // 2) * CH + oy; rgb, m = pix(crops[i])
        g = np.ones((n_h, n_w, 3), np.float32); g[m] = rgb[m]
        gin.paste(Image.fromarray((g * 255).round().astype(np.uint8)).resize((n_w * Z, n_h * Z), Image.NEAREST), (cx, cy))
        lk = crops[i].resize((n_w * Z, n_h * Z), Image.LANCZOS); look.paste(lk, (cx, cy), lk)
    gin.save(o / 'in.png'); look.save(o / 'look.png')
    rf = Image.new('RGB', (ref.width * Z + 40, ref.height * Z + 40), (255, 255, 255)); rz = ref.resize((ref.width * Z, ref.height * Z), Image.NEAREST); rf.paste(rz, (20, 20), rz); rf.save(o / 'ref.png')
    text = (f"Image 1 is a SHEET OF FOUR ANIMATION FRAMES of ONE small game monster, in a 2x2 grid - one frame in each quarter of the picture, in reading order. "
            f"Each frame is a 3D model of it already reduced to LOW-RESOLUTION PIXELS: every square of {Z}x{Z} px is ONE sprite pixel, on a grid that starts at the picture's "
            f"top-left corner; the monster is {n_h} sprite pixels tall. The frames differ only a little: {moves}. Its shapes, angle and colours are right, but it is blurred: no outline, small parts run together.\n"
            f"Redraw EACH frame as FINISHED PIXEL ART for an arcade game, ON THE SAME GRID: every sprite pixel one flat {Z}x{Z} square of a single colour, its edges exactly on the "
            "grid - no anti-aliasing, no blur, no gradients, no dithering, no half-pixels. A dark outline one sprite pixel wide all round, as image 3 has it; each part in two or three flat tones "
            "in clean clusters, light from the upper right; the face as image 3 has it. About 24 colours.\n"
            "Keep every frame exactly where it is and exactly as big, at the same angle; do not turn, mirror or enlarge anything, add nothing between the frames. "
            "The FOUR FRAMES MUST BE THE SAME DRAWING - the same pixels everywhere - except exactly where the tail and the arms have moved: draw the head, the eyes, the mouth "
            "and the body identically in all four, and move only the pixels of the parts that move, as image 1 shows.\n"
            "Image 2 is the same four frames at full resolution, in the same places: what each part is and its colour - to read image 1 by; NOT its rendering style.\n"
            "Image 3 is this same monster ALREADY DRAWN AS PIXEL ART (at rest): copy its colours, its outline, its face and its way of drawing each part exactly.\n"
            f"The monster: {spec['description']}. Plain pure white background, nothing else on the sheet, no text, no grid lines.")
    (o / 'prompt.txt').write_text(text)
print(len(sheets), 'sheet(s), about $%.2f' % (0.08 * len(sheets)))
if not YES and any(not (o / 'out.png').exists() for o, _ in sheets): sys.exit('nothing spent - --yes to draw')
import charpipe as CP
for o, idx in sheets:
    if (o / 'out.png').exists(): continue
    t = time.time(); c = CP.gpt((o / 'prompt.txt').read_text(), [o / 'in.png', o / 'look.png', o / 'ref.png'], o / 'out.png', f'{SW}x{SH}')
    print(f'drawn {o.name} (${c:.3f}, {time.time() - t:.0f} s)', flush=True)
# READ each cell as proppixel reads one view, then put it where its pose's pixelized render is (best overlap)
frames = []
for o, idx in sheets:
    ans = Image.open(o / 'out.png').convert('RGB').resize((SW, SH))
    for c, i in enumerate(idx):
        cd = o / f'cell-{c}'; (cd / 'pixel').mkdir(parents=True, exist_ok=True)
        x0, y0 = (c % 2) * CW, (c // 2) * CH; ans.crop((x0, y0, x0 + CW, y0 + CH)).save(cd / 'pixel/out.png')
        crops[i].save(cd / 'render.png')
        (cd / 'pixel/meta.json').write_text(json.dumps({'squares': [n_w, n_h], 'asked_px': n_h, 'z': Z, 'size': f'{CW}x{CH}', 'ppm': PPM, 'anchor': [n_w / 2, n_h]}))
        im, info = PP.read(cd, [], 0, (), spec, PPM); a = np.asarray(im)
        _, gm = pix(crops[i]); best = None
        gy, gx = np.nonzero(gm); sy, sx = np.nonzero(a[..., 3] > 0)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                X, Y = gx.min() - sx.min() + dx, gy.min() - sy.min() + dy
                cv = np.zeros((n_h + 20, n_w + 20), bool); yy, xx = sy + Y + 10, sx + X + 10; ok = (yy >= 0) & (xx >= 0) & (yy < n_h + 20) & (xx < n_w + 20)
                cv[yy[ok], xx[ok]] = True; G = np.zeros_like(cv); G[10:10 + n_h, 10:10 + n_w] = gm
                sc = (cv & G).sum() / max(1, (cv | G).sum())
                if best is None or sc > best[0]: best = (sc, X, Y)
        fr = np.zeros((n_h + 20, n_w + 20, 4), np.uint8); Y, X = best[2] + 10, best[1] + 10
        fr[Y:Y + a.shape[0], X:X + a.shape[1]] = a[:max(0, min(a.shape[0], n_h + 20 - Y)), :max(0, min(a.shape[1], n_w + 20 - X))][:fr[Y:Y + a.shape[0]].shape[0], :fr[:, X:X + a.shape[1]].shape[1]]
        frames.append(fr); print(f'frame {i}: {a.shape[1]}x{a.shape[0]}, overlap with its render {best[0]:.2f}')
Image.fromarray(np.concatenate(frames, 1)).save(OUTP / 'anim-solid.png')
# the alpha, pose by pose, from that pose's own model (its anchor left out), the model turned as the camera saw it; with a "pulse" the thin
# parts fade once a loop
tr = spec.get('translucent'); over = tr if isinstance(tr, dict) else {}; kind = over.get('kind') or (tr if isinstance(tr, str) else None)
sys.path.insert(0, str(HERE)); import isoprop; cam = isoprop.camera(spec); YAW = cam['yaw'] + spec['model'].get('yaw', 0)
st = TL.settings(kind, over); alpha = []
for i, fr in enumerate(frames):
    if not tr: alpha.append(fr); continue
    sc = trimesh.load(rig / f'{i}.glb')
    if isinstance(sc, trimesh.Scene) and 'anchor' in sc.geometry: sc.delete_geometry('anchor')
    m = sc.to_geometry() if hasattr(sc, 'to_geometry') else sc
    a2, _, _ = TL.apply(m, fr, YAW, cam['pitch'], TL.at_frame(st, i, len(frames)), refine=False); alpha.append(a2)
strip = np.concatenate(alpha, 1); Image.fromarray(strip).save(OUTP / 'anim.png')
fw, fh = frames[0].shape[1], frames[0].shape[0]
# WHERE THE PROP'S OWN SPRITE SITS IN A FRAME (the rest pose drawn twice: once alone, once on the sheet - the best overlap), so an engine
# puts the frames where the sprite stood: propexport.py plays them in its place
sa = ref.split()[-1]; sm = np.asarray(sa) > 0; f0 = frames[0][..., 3] > 0; best = (-1, 0, 0)
for oy in range(0, max(1, fh - sm.shape[0] + 1)):
    for ox in range(0, max(1, fw - sm.shape[1] + 1)):
        w_ = f0[oy:oy + sm.shape[0], ox:ox + sm.shape[1]]
        if w_.shape != sm.shape: continue
        sc_ = (w_ & sm).sum() / max(1, (w_ | sm).sum())
        if sc_ > best[0]: best = (sc_, ox, oy)
(OUTP / 'anim.json').write_text(json.dumps({'file': 'anim.png', 'frames': len(frames), 'frame': [fw, fh], 'fps': 9, 'loop': True, 'sprite_at': [best[1], best[2]], 'sprite_fit': round(float(best[0]), 2), 'translucent': st if tr else None}, indent=1))
ims = []
for f in alpha:
    c = Image.new('RGBA', (fw, fh), (73, 87, 85, 255)); c.alpha_composite(Image.fromarray(f)); ims.append(c.resize((fw * 4, fh * 4), Image.NEAREST).convert('RGB'))
ims[0].save(OUTP / 'preview-anim.gif', save_all=True, append_images=ims[1:], duration=110, loop=0)
print(f'propanim: {OUTP / "anim.png"} - {len(frames)} frames of {fw} x {fh}; look at preview-anim.gif')
