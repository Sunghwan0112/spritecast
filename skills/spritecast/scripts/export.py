"""export: a finished character (`<name>/out/` with character.json) as files a game engine or Aseprite opens as they are.

    python export.py <name>/out                 -> <name>/out/export/{godot,phaser,aseprite,unity}/
    python export.py <name>/out --to DIR --only godot,aseprite --name hero

Free: nothing is drawn, the strips are read and laid out again.

  godot/     a folder to drop anywhere in a Godot 4 project: <name>.tscn (a Node2D at the feet, with Shadow and Body), its two
             SpriteFrames, <name>.gd (`play("walk", "south-east")`), and the strips. Animations are named `walk_south_east`.
  phaser/    <name>.js, an ES module for Phaser 3 (`preload(scene, base)`, `create(scene)`, `add(scene, x, y)`), and the strips.
  aseprite/  <name>-<action>.aseprite, one per action (their frames differ in size): a tag per facing, the layers `shadow` (at the set's "shadow_alpha"),
             `body` and `effect`, the frame times from the fps, and a slice `feet` whose pivot is the point between the feet.
  unity/     copy its contents into Assets/: <name>/ (strips, <name>.spritecast.json) and SpriteCast/Editor/SpriteCastImporter.cs,
             which builds <name>.prefab (Animator > Shadow, Body), the controller and a clip per animation (`walk_south_east`);
             SpriteCast/SpriteCastFacing.cs: `SpriteCastFacing.Play(animator, "walk", "east")`.

A set drawn in four facings ("facings": 4 - the diagonals, or "cardinal" - south, east, north, west) still takes all eight: each engine's play() shows the nearest facing drawn
(Godot, Phaser, Unity's SpriteCastFacing), keeping the one shown last between two as near, so walking straight across does not flicker.

What character.json keeps apart is put together here: every animation's shadows become one strip of equal cells with ONE offset,
so an engine shows shadow frame i under body frame i and never reads a table. A swing's effect ("trail": water, flame, leaves ...)
goes along as a third sprite over the body, played at its own pace (it may have two cells to each body frame).

A pixel PROP (<name>/out-pixel, with pixel.json) is handed on to propexport.py: Godot and Phaser, with its baked shadow, a lamp's light,
the wind in it, where it is in the way and how to shade a character in its shadow."""
import argparse, json, re, shutil, struct, sys, zlib
from pathlib import Path
from PIL import Image

FACINGS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
SHADOW_ALPHA = 0.3


def load(out):
    """character.json -> the name-free list of animations: action, facing, strip, frames, cell, anchor (px in the cell), fps, loop,
    the shadows as [(file, offset)] per frame, and `fx`: a swing's effect ("trail"), a strip of its own with `per` cells to each frame"""
    out = Path(out); f = out / 'character.json'
    if not f.exists(): sys.exit(f'{f} not found: give the folder `finish` wrote (<name>/out). A pixel set (pixel.json) is not read yet.')
    d = json.loads(f.read_text()); an = []
    global SHADOW_ALPHA; SHADOW_ALPHA = d.get('shadow_alpha', 0.3)          # (0.56 for shadows as light falls - since 0.20; 0.3 for the old hard shape)
    def add(action, facing, file, cell, anchor, fps, loop, sh, fx=None):
        p = out / file
        if not p.exists(): return
        w = Image.open(p).width; n = max(1, round(w / cell[0]))
        if n * cell[0] != w: sys.exit(f'{p}: {w} px wide is not a whole number of {cell[0]}-px frames')
        sh = [sh] if isinstance(sh, dict) else list(sh or [])
        sh = [(out / x['file'], x['offset']) for x in sh if (out / x['file']).exists()]
        an.append(dict(action=action, facing=facing, file=p, n=n, cell=list(cell), anchor=[round(anchor[0] * cell[0], 1), round(anchor[1] * cell[1], 1)],
                       fps=fps, loop=loop, shadows=sh if len(sh) == n else [],
                       fx=dict(file=out / fx['file'], cell=fx['frame'], offset=fx['offset'], n=fx.get('frames', n), per=fx.get('per_frame', 1)) if fx and (out / fx['file']).exists() else None))
    S = d.get('shadows', {})
    for dr in FACINGS:
        if dr in d.get('walk', {}): add('walk', dr, d['walk'][dr], d['frame'], d['anchor'], d['fps'], True, S.get('walk', {}).get(dr))
        if dr in d.get('idle', {}): add('idle', dr, d['idle'][dr], d['frame'], d['anchor'], d['fps'], True, S.get('idle', {}).get(dr))
    for a, v in d.get('actions', {}).items():
        for dr in FACINGS:
            if dr in v.get('strips', {}): add(a, dr, v['strips'][dr], v['frame'], v['anchor'], v.get('fps', d['fps']), v.get('loop', True), v.get('shadows', {}).get(dr), v.get('trail', {}).get(dr))
    sit = d.get('sit')
    if sit:          # one seated frame a facing; its anchor is the SEAT (where the body rests), not the feet
        for dr in FACINGS:
            if dr in sit: add('sit', dr, sit[dr]['file'], sit['frame'], sit[dr]['seat'], d['fps'], True, sit[dr].get('shadow'))
    if not an: sys.exit(f'{f}: no strips found beside it')
    return an


def shadow_strip(a):
    """an animation's shadows as one strip of equal cells -> (image, cell, offset of the cell from the body frame's top-left)"""
    if not a['shadows']: return None
    ims = [(Image.open(p).convert('RGBA'), o) for p, o in a['shadows']]
    x0 = min(o[0] for _, o in ims); y0 = min(o[1] for _, o in ims)
    w = max(o[0] + im.width for im, o in ims) - x0; h = max(o[1] + im.height for im, o in ims) - y0
    st = Image.new('RGBA', (w * len(ims), h), (0, 0, 0, 0))
    for i, (im, o) in enumerate(ims): st.paste(im, (i * w + o[0] - x0, o[1] - y0))
    return st, [w, h], [x0, y0]


def prepare(an, dst):
    """copies the body strips into dst and writes the shadow strips beside them; every animation gains `png`, `shadow` ({png, cell, offset})
    and `effect` ({png, cell, offset, n, per, cols}: a swing's effect, laid over the body; `per` of its cells to each body frame; its
    sheet has `cols` cells a row), or None"""
    dst.mkdir(parents=True, exist_ok=True)
    for a in an:
        a['key'] = f"{a['action']}-{a['facing']}"; a['png'] = f"{a['key']}.png"
        shutil.copyfile(a['file'], dst / a['png'])
        s = a.get('_shadow', False)
        if s is False: s = a['_shadow'] = shadow_strip(a)
        a['shadow'] = None
        if s:
            s[0].save(dst / f"{a['key']}-shadow.png"); a['shadow'] = dict(png=f"{a['key']}-shadow.png", cell=s[1], offset=s[2])
        a['effect'] = None
        if a['fx']:
            # laid out again in rows no wider than 2048 px: sixteen cells side by side pass the 4096 px a phone's texture may be
            cw, chh = a['fx']['cell']; n = a['fx']['n']; cols = max(1, min(n, 2048 // cw)); src = Image.open(a['fx']['file']).convert('RGBA')
            sheet = Image.new('RGBA', (cols * cw, -(-n // cols) * chh), (0, 0, 0, 0))
            for i in range(n): sheet.paste(src.crop((i * cw, 0, (i + 1) * cw, chh)), ((i % cols) * cw, (i // cols) * chh))
            sheet.save(dst / f"{a['key']}-effect.png", optimize=True)
            a['effect'] = dict(png=f"{a['key']}-effect.png", cell=a['fx']['cell'], offset=a['fx']['offset'], n=n, per=a['fx']['per'], cols=cols)


def ident(s): return re.sub(r'\W', '_', s)


# ---------------------------------------------------------------- Godot 4
def godot(an, dst, name):
    prepare(an, dst)
    def frames(which):          # a SpriteFrames resource of the body strips, of the shadow strips, or of the effects' (at their own pace)
        ext, sub, anims = [], [], []
        for a in an:
            src = a if which == 'body' else (a[which] or {}); png, cell = src.get('png'), src.get('cell')
            fr = []; n, speed = (src['n'], round(a['fps'] * src['per'], 2)) if which == 'effect' and png else (a['n'], a['fps']); cols = src.get('cols', n) if which == 'effect' else n
            if png:
                e = len(ext) + 1; ext.append(f'[ext_resource type="Texture2D" path="{png}" id="{e}"]')
                for i in range(n):
                    s = f'a{len(sub) + 1}'
                    sub.append(f'[sub_resource type="AtlasTexture" id="{s}"]\natlas = ExtResource("{e}")\nregion = Rect2({(i % cols) * cell[0]}, {(i // cols) * cell[1]}, {cell[0]}, {cell[1]})\n')
                    fr.append('{\n"duration": 1.0,\n"texture": SubResource("%s")\n}' % s)
            anims.append('{\n"frames": [%s],\n"loop": %s,\n"name": &"%s",\n"speed": %s\n}' % (', '.join(fr), 'true' if a['loop'] else 'false', ident(a['key']), speed))
        return (f'[gd_resource type="SpriteFrames" load_steps={len(ext) + len(sub) + 1} format=3]\n\n' + '\n'.join(ext) + '\n\n' + '\n'.join(sub)
                + '\n[resource]\nanimations = [' + ', '.join(anims) + ']\n')
    (dst / f'{name}.tres').write_text(frames('body')); (dst / f'{name}_shadow.tres').write_text(frames('shadow')); (dst / f'{name}_effect.tres').write_text(frames('effect'))
    rows = []
    for a in an:
        so = a['shadow']['offset'] if a['shadow'] else [0, 0]; eo = a['effect']['offset'] if a['effect'] else [0, 0]
        rows.append(f'\t&"{ident(a["key"])}": [Vector2({-a["anchor"][0]}, {-a["anchor"][1]}), Vector2({so[0] - a["anchor"][0]}, {so[1] - a["anchor"][1]}), Vector2({eo[0] - a["anchor"][0]}, {eo[1] - a["anchor"][1]})],')
    first = ident(next((a for a in an if a['action'] == 'idle'), an[0])['key'])
    (dst / f'{name}.gd').write_text(f'''extends Node2D
## {name}, written by SpriteCast's export.py. The node's position is the point between the feet (on a seat: where the body rests).
##   play("walk", "south-east")      facings: south, south-east, east, north-east, north, north-west, west, south-west
## A facing the set has no drawing for (a set made with "facings": 4 has the diagonals only, "cardinal" the cardinals) shows the nearest one it
## has; between two as near (east, between south-east and north-east; south-east, between south and east) the one shown last stays, so walking straight across does not flicker;
## with none shown yet, the one turned more toward the viewer.
## Each animation has its own frame size, so the Body's, the Shadow's and the Effect's offsets are set per animation, from the table below.
## Effect: what a swing leaves in the air (water, flame, leaves ...), over the body; it runs at its own pace beside the body's frames.

const OFFSETS := {{   # animation: [body offset, shadow offset, effect offset] from the feet, px
{chr(10).join(rows)}
}}

@onready var body: AnimatedSprite2D = $Body
@onready var shadow: AnimatedSprite2D = $Shadow
@onready var effect: AnimatedSprite2D = $Effect

func _ready() -> void:
\tbody.frame_changed.connect(func(): shadow.frame = body.frame)
\tplay_named(&"{first}")

const FACINGS := ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"]
var facing_shown := ""

func has(action: String, facing: String) -> bool:
\treturn OFFSETS.has(StringName((action + "_" + facing).replace("-", "_")))

## the facing drawn for this action nearest to the one asked for (itself when it is drawn)
func nearest(action: String, facing: String) -> String:
\tif has(action, facing):
\t\treturn facing
\tvar i := FACINGS.find(facing)
\tvar best := ""
\tvar best_d := 99
\tfor j in FACINGS.size():
\t\tif not has(action, FACINGS[j]):
\t\t\tcontinue
\t\tvar dd: int = abs(i - j)
\t\tdd = min(dd, 8 - dd)
\t\t# between two as near: the one shown last, else the one turned more toward the viewer (west: south-west)
\t\tif dd < best_d or (dd == best_d and best != facing_shown and (FACINGS[j] == facing_shown or min(j, 8 - j) < min(FACINGS.find(best), 8 - FACINGS.find(best)))):
\t\t\tbest = FACINGS[j]
\t\t\tbest_d = dd
\treturn best

func play(action: String, facing: String, restart := false) -> void:
\tvar f := nearest(action, facing)
\tif f == "":
\t\treturn
\tfacing_shown = f
\tplay_named(StringName((action + "_" + f).replace("-", "_")), restart)

func play_named(anim: StringName, restart := false) -> void:
\tif not OFFSETS.has(anim) or (body.animation == anim and body.is_playing() and not restart):
\t\treturn
\tbody.offset = OFFSETS[anim][0]
\tshadow.offset = OFFSETS[anim][1]
\tshadow.visible = shadow.sprite_frames.get_frame_count(anim) > 0
\tshadow.animation = anim
\teffect.offset = OFFSETS[anim][2]
\teffect.visible = effect.sprite_frames.get_frame_count(anim) > 0
\tbody.play(anim)
\tbody.frame = 0
\tshadow.frame = 0
\tif effect.visible:
\t\teffect.play(anim)
\t\teffect.frame = 0
''')
    (dst / f'{name}.tscn').write_text(f'''[gd_scene load_steps=5 format=3]

[ext_resource type="SpriteFrames" path="{name}_shadow.tres" id="1"]
[ext_resource type="SpriteFrames" path="{name}.tres" id="2"]
[ext_resource type="Script" path="{name}.gd" id="3"]
[ext_resource type="SpriteFrames" path="{name}_effect.tres" id="4"]

[node name="{name}" type="Node2D"]
script = ExtResource("3")

[node name="Shadow" type="AnimatedSprite2D" parent="."]
modulate = Color(1, 1, 1, {SHADOW_ALPHA})
sprite_frames = ExtResource("1")
animation = &"{first}"
centered = false

[node name="Body" type="AnimatedSprite2D" parent="."]
sprite_frames = ExtResource("2")
animation = &"{first}"
centered = false

[node name="Effect" type="AnimatedSprite2D" parent="."]
visible = false
sprite_frames = ExtResource("4")
animation = &"{first}"
centered = false
''')


# ---------------------------------------------------------------- Phaser 3
def phaser(an, dst, name):
    prepare(an, dst)
    A = {a['key']: dict(png=a['png'], n=a['n'], cell=a['cell'], anchor=a['anchor'], fps=a['fps'], loop=a['loop'], shadow=a['shadow'], effect=a['effect']) for a in an}
    first = next((a for a in an if a['action'] == 'idle'), an[0])['key']
    (dst / f'{name}.js').write_text(f'''// {name}, written by SpriteCast's export.py - an ES module for Phaser 3.
//   import * as {ident(name)} from './{name}.js'
//   preload() {{ {ident(name)}.preload(this, 'assets/{name}/') }}        // the folder this file and the strips are in
//   create()  {{ {ident(name)}.create(this); this.girl = {ident(name)}.add(this, 400, 300) }}
//   this.girl.play('walk', 'south-east'); this.girl.setPosition(x, y)   // x, y: the point between the feet
// Facings: south, south-east, east, north-east, north, north-west, west, south-west. A facing the set has no drawing for (a set made
// with "facings": 4 has the diagonals only, "cardinal" the cardinals) shows the nearest one it has; between two as near (east: south-east
// or north-east; south-east: south or east) the one
// shown last stays, so walking straight across does not flicker; with none shown yet, the one turned more toward the viewer.
export const FACINGS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']
export const NAME = {json.dumps(name)}
export const SHADOW_ALPHA = {SHADOW_ALPHA}
export const ANIMS = {json.dumps(A, indent=1)}

const key = k => NAME + ':' + k

export function preload(scene, base = '') {{
  for (const [k, a] of Object.entries(ANIMS)) {{
    scene.load.spritesheet(key(k), base + a.png, {{ frameWidth: a.cell[0], frameHeight: a.cell[1] }})
    if (a.shadow) scene.load.spritesheet(key(k) + ':shadow', base + a.shadow.png, {{ frameWidth: a.shadow.cell[0], frameHeight: a.shadow.cell[1] }})
    if (a.effect) scene.load.spritesheet(key(k) + ':effect', base + a.effect.png, {{ frameWidth: a.effect.cell[0], frameHeight: a.effect.cell[1] }})
  }}
}}

export function create(scene) {{
  for (const [k, a] of Object.entries(ANIMS)) {{
    if (!scene.anims.exists(key(k)))
      scene.anims.create({{ key: key(k), frames: scene.anims.generateFrameNumbers(key(k), {{ start: 0, end: a.n - 1 }}), frameRate: a.fps, repeat: a.loop ? -1 : 0 }})
    if (a.effect && !scene.anims.exists(key(k) + ':effect'))          // a swing's effect: `per` cells to each body frame, so at `per` times the pace
      scene.anims.create({{ key: key(k) + ':effect', frames: scene.anims.generateFrameNumbers(key(k) + ':effect', {{ start: 0, end: a.effect.n - 1 }}), frameRate: a.fps * a.effect.per, repeat: a.loop ? -1 : 0 }})
  }}
}}

// A character on the scene: the body sprite, its shadow under it, and over it the effect of a swing (water, flame, leaves ...: shown
// only in the animations that have one). `depth` is the body's; the shadow is drawn at shadowDepth, the effect at effectDepth.
export function add(scene, x, y, {{ scale = 1, depth = 0, shadowDepth = -1, effectDepth = depth + 1 }} = {{}}) {{
  const shadow = scene.add.sprite(x, y, key({json.dumps(first)}) + ':shadow', 0).setAlpha(SHADOW_ALPHA).setDepth(shadowDepth)
  const body = scene.add.sprite(x, y, key({json.dumps(first)}), 0).setDepth(depth)
  const effect = scene.add.sprite(x, y, key({json.dumps(first)}), 0).setDepth(effectDepth).setVisible(false)
  const c = {{ body, shadow, effect, x, y, scale, current: null, facing: null,
    has(action, facing) {{ return (action + '-' + facing) in ANIMS }},
    // the facing drawn for this action nearest to the one asked for (itself when it is drawn)
    nearest(action, facing) {{
      if (c.has(action, facing)) return facing
      const i = FACINGS.indexOf(facing); let best = null, bd = 99
      FACINGS.forEach((f, j) => {{
        if (!c.has(action, f)) return
        const dd = Math.min(Math.abs(i - j), 8 - Math.abs(i - j))
        // between two as near: the one shown last, else the one turned more toward the viewer (west: south-west)
        const toViewer = x => {{ const k = FACINGS.indexOf(x); return Math.min(k, 8 - k) }}
        if (dd < bd || (dd === bd && best !== c.facing && (f === c.facing || toViewer(f) < toViewer(best)))) {{ best = f; bd = dd }}
      }})
      return best
    }},
    play(action, facing, restart = false) {{
      const f = c.nearest(action, facing)
      if (!f) return c
      c.facing = f
      const k = action + '-' + f, a = ANIMS[k]
      if (!a || (k === c.current && !restart && (a.loop || body.anims.isPlaying))) return c
      c.current = k
      body.setOrigin(a.anchor[0] / a.cell[0], a.anchor[1] / a.cell[1]).play(key(k), false)
      shadow.setVisible(!!a.shadow)
      if (a.shadow) shadow.setTexture(key(k) + ':shadow', 0).setOrigin((a.anchor[0] - a.shadow.offset[0]) / a.shadow.cell[0], (a.anchor[1] - a.shadow.offset[1]) / a.shadow.cell[1])
      effect.setVisible(!!a.effect)
      if (a.effect) effect.setOrigin((a.anchor[0] - a.effect.offset[0]) / a.effect.cell[0], (a.anchor[1] - a.effect.offset[1]) / a.effect.cell[1]).play(key(k) + ':effect', false)
      else effect.anims.stop()
      return c
    }},
    setPosition(nx, ny) {{ c.x = nx; c.y = ny; body.setPosition(nx, ny); shadow.setPosition(nx, ny); effect.setPosition(nx, ny); return c }},
    setScale(s) {{ c.scale = s; body.setScale(s); shadow.setScale(s); effect.setScale(s); return c }},
    setDepth(d, sd = shadowDepth, ed = d + 1) {{ body.setDepth(d); shadow.setDepth(sd); effect.setDepth(ed); return c }},
    destroy() {{ body.destroy(); shadow.destroy(); effect.destroy() }},
  }}
  // the shadow shows the body's frame, read every step (a paused or hand-set frame is followed too)
  const follow = () => {{ const f = body.anims.currentFrame; if (f && shadow.visible && shadow.frame.name !== f.index - 1) shadow.setFrame(f.index - 1) }}
  scene.events.on('postupdate', follow)
  body.once('destroy', () => scene.events.off('postupdate', follow))
  return c.setScale(scale).play({json.dumps(first.split('-', 1)[0])}, {json.dumps(first.split('-', 1)[1])})
}}
''')


# ---------------------------------------------------------------- Aseprite (.aseprite, written here: Aseprite itself is not needed)
def _s(s): b = s.encode(); return struct.pack('<H', len(b)) + b
def _chunk(kind, data): return struct.pack('<IH', len(data) + 6, kind) + data


def _cel(layer, im, at):          # a compressed-image cel, cut to what is drawn; None for an empty one
    box = im.getchannel('A').getbbox()
    if not box: return None
    im = im.crop(box)
    return _chunk(0x2005, struct.pack('<HhhBHh5x', layer, at[0] + box[0], at[1] + box[1], 255, 2, 0) + struct.pack('<HH', *im.size) + zlib.compress(im.tobytes(), 6))


def aseprite(an, dst, name):
    dst.mkdir(parents=True, exist_ok=True)
    for action in dict.fromkeys(a['action'] for a in an):
        A = [a for a in an if a['action'] == action]
        for a in A:
            if a.get('_shadow', False) is False: a['_shadow'] = shadow_strip(a)
        m = max([a['fx']['per'] for a in A if a['fx']] or [1])          # a swing's effect has `per` cells to each body frame: the file has that many frames to each, the body held
        # the canvas: the body frame, every shadow cell and every effect cell, measured from the anchor, so each facing's anchor falls on one pixel
        boxes = []
        for a in A:
            ax, ay = a['anchor']; boxes.append((-ax, -ay, a['cell'][0] - ax, a['cell'][1] - ay))
            for cellsz, off in ([(a['_shadow'][1], a['_shadow'][2])] if a['_shadow'] else []) + ([(a['fx']['cell'], a['fx']['offset'])] if a['fx'] else []):
                boxes.append((off[0] - ax, off[1] - ay, off[0] + cellsz[0] - ax, off[1] + cellsz[1] - ay))
        up = lambda v: int(-(-v // 1))
        L, T = up(-min(b[0] for b in boxes)), up(-min(b[1] for b in boxes)); W, H = L + up(max(b[2] for b in boxes)), T + up(max(b[3] for b in boxes))
        frames, tags, at = [], [], 0
        for a in A:
            ox, oy = L - round(a['anchor'][0]), T - round(a['anchor'][1])
            body = Image.open(a['file']).convert('RGBA'); sh = a['_shadow']; fx = a['fx']; fxim = Image.open(fx['file']).convert('RGBA') if fx else None
            for i in range(a['n']):
                for j in range(m):
                    ch = []
                    if not frames:          # the first frame carries the file's layers, tags and slice
                        ch += [_chunk(0x2007, struct.pack('<HHI8x', 1, 0, 0)),
                               _chunk(0x2004, struct.pack('<HHHHHHB3x', 3, 0, 0, 0, 0, 0, round(255 * SHADOW_ALPHA)) + _s('shadow')),
                               _chunk(0x2004, struct.pack('<HHHHHHB3x', 3, 0, 0, 0, 0, 0, 255) + _s('body')),
                               _chunk(0x2004, struct.pack('<HHHHHHB3x', 3, 0, 0, 0, 0, 0, 255) + _s('effect')), None,
                               _chunk(0x2022, struct.pack('<III', 1, 2, 0) + _s('feet') + struct.pack('<IiiIIii', 0, 0, 0, W, H, L, T))]
                    if sh:
                        c = _cel(0, sh[0].crop((i * sh[1][0], 0, (i + 1) * sh[1][0], sh[1][1])), (ox + sh[2][0], oy + sh[2][1]))
                        if c: ch.append(c)
                    c = _cel(1, body.crop((i * a['cell'][0], 0, (i + 1) * a['cell'][0], a['cell'][1])), (ox, oy))
                    if c: ch.append(c)
                    if fx:
                        q = i * fx['per'] + j * fx['per'] // m; fw_, fh_ = fx['cell']
                        c = _cel(2, fxim.crop((q * fw_, 0, (q + 1) * fw_, fh_)), (ox + fx['offset'][0], oy + fx['offset'][1])) if q < fx['n'] else None
                        if c: ch.append(c)
                    frames.append((ch, max(1, round(1000 / a['fps'] / m))))
            tags.append((at, at + a['n'] * m - 1, a['facing'], a['loop'])); at += a['n'] * m
        t = struct.pack('<H8x', len(tags))
        for f, to, nm, loop in tags: t += struct.pack('<HHBH6x3xB', f, to, 0, 0 if loop else 1, 0) + _s(nm)
        frames[0][0][4] = _chunk(0x2018, t)
        body_ = b''
        for ch, ms in frames:
            data = b''.join(ch)
            body_ += struct.pack('<IHHH2xI', len(data) + 16, 0xF1FA, min(len(ch), 0xFFFF), ms, len(ch)) + data
        head = struct.pack('<IHHHHHIHIIB3xHBBhhHH84x', 128 + len(body_), 0xA5E0, len(frames), W, H, 32, 1, frames[0][1], 0, 0, 0, 0, 1, 1, 0, 0, 16, 16)
        assert len(head) == 128
        (dst / f'{name}-{action}.aseprite').write_bytes(head + body_)


# ---------------------------------------------------------------- Unity
def unity(an, dst, name):
    """unity/<name>/ (the strips and <name>.spritecast.json) and unity/SpriteCast/Editor/SpriteCastImporter.cs, which builds the
    prefab, the Animator controller and the clips inside Unity when the folder is copied into Assets/"""
    prepare(an, dst / name)
    first = next((a for a in an if a['action'] == 'idle'), an[0])['key']
    (dst / name / f'{name}.spritecast.json').write_text(json.dumps(dict(
        name=name, pixels_per_unit=100, shadow_alpha=SHADOW_ALPHA, first=ident(first),
        anims=[dict(name=ident(a['key']), png=a['png'], n=a['n'], cell=a['cell'], anchor=a['anchor'], fps=a['fps'], loop=a['loop'],
                    shadow=a['shadow'] or dict(png='', cell=[0, 0], offset=[0, 0]),
                    effect=a['effect'] or dict(png='', cell=[0, 0], offset=[0, 0], n=0, per=1, cols=1)) for a in an]), indent=1))
    ed = dst / 'SpriteCast' / 'Editor'; ed.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).resolve().parent / 'unity' / 'SpriteCastImporter.cs', ed / 'SpriteCastImporter.cs')
    shutil.copyfile(Path(__file__).resolve().parent / 'unity' / 'SpriteCastFacing.cs', dst / 'SpriteCast' / 'SpriteCastFacing.cs')   # (runtime, not Editor/)


MAKERS = {'godot': godot, 'phaser': phaser, 'aseprite': aseprite, 'unity': unity}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out', help="the folder with character.json (<name>/out)")
    ap.add_argument('--to', help='where to write (default: <out>/export)')
    ap.add_argument('--only', default=','.join(MAKERS), help='which, comma-separated: ' + ', '.join(MAKERS))
    ap.add_argument('--name', help="the character's name in file and node names (default: the folder's name)")
    g = ap.parse_args()
    out = Path(g.out).resolve()
    if (out / 'pixel.json').exists() and not (out / 'character.json').exists() and 'views' in json.loads((out / 'pixel.json').read_text()):          # (a pixel prop: its own exporter)
        import propexport; propexport.run(out, g.to, g.only if g.only != ','.join(MAKERS) else None, g.name); sys.exit()
    an = load(out)
    name = ident(g.name or (out.parent.name if out.name == 'out' else out.name))
    to = Path(g.to).resolve() if g.to else out / 'export'
    for k in g.only.split(','):
        if k not in MAKERS: sys.exit(f'--only {k}: one of {", ".join(MAKERS)}')
        MAKERS[k](an, to / k, name)
    acts = list(dict.fromkeys(a['action'] for a in an))
    print(f'{name}: {len(an)} animations ({", ".join(acts)}) -> {to}/{{{g.only}}}')
    print(f'free: nothing was drawn. The shadows are strips now, one offset an animation; show them at {SHADOW_ALPHA:.0%} under everything.')
