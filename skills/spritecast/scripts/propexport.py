"""propexport: a finished pixel prop (`<name>/out-pixel/` with pixel.json) as files a game engine opens as they are - the sprite of
each side with what was worked out from its 3D model: the baked shadow, a lamp's light on the floor, the wind in it, where it is in the
way, and how to shade a character that walks into its shadow.

    python export.py <name>/out-pixel                 -> <name>/out-pixel/export/{godot,phaser}/      (export.py hands a prop on to here)
    python propexport.py <name>/out-pixel --to DIR --only phaser --name tree

Free: nothing is drawn or baked, the pictures are copied and their places written down.

  <name>.prop.json  in both: every side's layers, each with its place FROM THE FOOT (the middle of where the prop stands, on the
             ground) in pixels - so a game puts the foot at (x, y) and every layer at foot + offset, and reads no other table.
  phaser/    <name>.js, an ES module for Phaser 3: `preload(scene, base)`, `add(scene, x, y, side)` -> the prop: its light (ADD), its
             shadow, its body (playing the wind if it has one: `.wind(0 | 1 | 2)`), and `.solid(x, y)`, `.cover(x, y, h)`,
             `.shade(x, y, h)` for the game's rules; `shadeOf(props, x, y, h)` for a character among several.
  godot/     <name>.tscn + <name>.gd for Godot 4: a Node2D at the foot with Light, Shadow, Body (AnimatedSprite2D when it sways) and
             Solid (a StaticBody2D with the footprint's outline); `side`, `wind` to set; `cover_at()`, `shade_at()` to ask.
Not yet: Unity and Aseprite for props (characters have them - export.py)."""
import argparse, json, re, shutil, sys
from pathlib import Path
from PIL import Image


def ident(s): return re.sub(r'\W', '_', s)


def load(out):
    """pixel.json -> {ppm, sides: {key: layers...}, lamp, shadow, wind}: every place from the foot"""
    out = Path(out); f = out / 'pixel.json'
    if not f.exists(): sys.exit(f'{f} not found: give the folder proppixel.py wrote (<name>/out-pixel)')
    pj = json.loads(f.read_text())
    if 'views' not in pj: sys.exit(f'{f}: not a prop\'s pixel.json (no "views")')
    sides = {}
    for k, e in pj['views'].items():
        im = Image.open(out / e['file']); foot = (e.get('shadow') or {}).get('foot') or [im.width / 2, float(im.height)]
        rel = lambda at: [round(at[0] - foot[0], 1), round(at[1] - foot[1], 1)]
        s = {'sprite': {'file': e['file'], 'size': list(im.size), 'offset': rel([0, 0])}}
        if e.get('shadow') and (out / e['shadow']['file']).exists():
            sh = e['shadow']; s['shadow'] = {'file': sh['file'], 'offset': rel(sh['at']), 'height_m': sh.get('height_m'), 'per_m_up': sh.get('per_m_up')}
        if e.get('light') and (out / e['light']['file']).exists(): s['light'] = {'file': e['light']['file'], 'offset': rel(e['light']['at']), 'blend': 'add'}
        if e.get('lamp'): s['lamp'] = {'at': rel(e['lamp']['at']), 'spot': rel(e['lamp']['spot'])}
        if e.get('sway') and (out / e['sway']['sheet']).exists():
            w = e['sway']; s['sway'] = {'file': w['sheet'], 'frame': w['frame'], 'frames': w['frames'], 'rows': w['rows'], 'fps': w.get('fps', 4), 'offset': rel([-w['pad'], -w.get('top', 0)])}
        an = out / 'anim.json'
        if an.exists() and len(pj['views']) == 1 and 'sway' not in s:          # (propanim.py's loop - a ghost's tail and arms: played as the wind is, one row)
            A = json.loads(an.read_text()); s['sway'] = {'file': A['file'], 'frame': A['frame'], 'frames': A['frames'], 'rows': ['loop'], 'fps': A.get('fps', 9), 'offset': rel([-A['sprite_at'][0], -A['sprite_at'][1]])}
        if e.get('solid'): s['solid'] = {'file': e['solid']['file'], 'offset': rel(e['solid']['at']), 'hull': [rel(p) for p in e['solid']['hull']]}
        for c in e.get('cover', []): s.setdefault('cover', []).append({'file': c['file'], 'offset': rel(c['at']), 'height_m': c['height_m'], 'hull': [rel(p) for p in c['hull']]})
        sides[k] = s
    lamp = None
    if pj.get('lamp') and (out / pj['lamp']['file']).exists():
        L = pj['lamp']; lamp = {'file': L['file'], **({'middle': L['middle']} if 'middle' in L else {'foot': L['foot'], 'light': L['light']})}
    sh = pj.get('shadow') or {}
    return {'px_per_m': pj['px_per_m'], 'weather': sh.get('weather'), 'shadow_colour': sh.get('colour'), 'sides': sides, 'lamp': lamp}


def copy(P, out, dst):
    dst.mkdir(parents=True, exist_ok=True); files = set()
    for s in P['sides'].values():
        for k, v in s.items():
            for it in (v if isinstance(v, list) else [v]):
                if isinstance(it, dict) and it.get('file'): files.add(it['file'])
    if P['lamp']: files.add(P['lamp']['file'])
    for f in sorted(files): shutil.copyfile(out / f, dst / f)


# ---------------------------------------------------------------- Phaser 3
def phaser(P, out, dst, name):
    copy(P, out, dst); (dst / f'{name}.prop.json').write_text(json.dumps(P, indent=1)); n = ident(name)
    (dst / f'{name}.js').write_text(f'''// {name}, a pixel prop written by SpriteCast's export.py - an ES module for Phaser 3.
//   import * as {n} from './{name}.js'
//   preload() {{ {n}.preload(this, 'assets/{name}/') }}             // the folder this file and the pictures are in
//   create()  {{ this.tree = {n}.add(this, 400, 300, '0') }}       // x, y: its FOOT - the middle of where it stands, on the ground
//   this.tree.wind(2)                                              // 0 still air, 1 a breeze, 2 a gust (if it sways)
//   if (this.tree.solid(x, y)) ...                                 // a walker cannot stand at (x, y)
//   if (this.tree.cover(x, y, 0.55)) ...                           // a thing flying 0.55 m up over ground point (x, y) is stopped
//   const dark = {n}.shadeOf([this.tree, ...], x, y, 1.1)         // 0..1: how much of the light the props take from a point of
//                                                                  //   her 1.1 m up, standing at (x, y) - darken that part of her by it
// Sides: {', '.join(repr(k) for k in P['sides'])}. Everything is drawn in the sprite's own pixels: do not scale one layer without the others.
// Depth: the light and the shadow lie on the ground (depth `ground`, default -1); the body sorts by its foot's y.
export const NAME = {json.dumps(name)}
export const PROP = {json.dumps(P, indent=1)}

const key = (f) => NAME + ':' + f

export function preload(scene, base = '') {{
  for (const s of Object.values(PROP.sides)) {{
    for (const k of ['sprite', 'shadow', 'light', 'solid']) if (s[k]) scene.load.image(key(s[k].file), base + s[k].file)
    for (const c of s.cover || []) scene.load.image(key(c.file), base + c.file)
    if (s.sway) scene.load.spritesheet(key(s.sway.file), base + s.sway.file, {{ frameWidth: s.sway.frame[0], frameHeight: s.sway.frame[1] }})
  }}
  if (PROP.lamp) scene.load.image(key(PROP.lamp.file), base + PROP.lamp.file)
}}

const masks = {{}}
function mask(scene, file) {{          // a picture's alpha, read once
  if (masks[file]) return masks[file]
  const im = scene.textures.get(key(file)).getSourceImage(), c = document.createElement('canvas'); c.width = im.width; c.height = im.height
  const g = c.getContext('2d'); g.drawImage(im, 0, 0); const d = g.getImageData(0, 0, im.width, im.height).data, a = new Uint8Array(im.width * im.height)
  for (let i = 0; i < a.length; i++) a[i] = d[i * 4 + 3]
  return (masks[file] = {{ a, w: im.width, h: im.height }})
}}
function alphaAt(scene, layer, px, py) {{          // (px, py: from the foot)
  const m = mask(scene, layer.file), i = Math.floor(px - layer.offset[0]), j = Math.floor(py - layer.offset[1])
  return i < 0 || j < 0 || i >= m.w || j >= m.h ? 0 : m.a[j * m.w + i] / 255
}}

export function add(scene, x, y, side = Object.keys(PROP.sides)[0], opts = {{}}) {{
  const s = PROP.sides[side]; if (!s) throw new Error(NAME + ': no side ' + side + ' (it has ' + Object.keys(PROP.sides) + ')')
  const ground = opts.ground ?? -1, p = {{ x, y, side, layers: s, parts: [] }}
  const put = (k, layer, depth) => {{ const o = scene.add.image(x + layer.offset[0], y + layer.offset[1], key(layer.file)).setOrigin(0).setDepth(depth); p.parts.push([o, layer.offset]); return (p[k] = o) }}
  if (s.light) put('light', s.light, ground).setBlendMode('ADD')
  if (s.shadow) put('shadow', s.shadow, ground)
  if (s.sway) {{
    const w = s.sway; p.body = scene.add.sprite(x + w.offset[0], y + w.offset[1], key(w.file), 0).setOrigin(0).setDepth(y); p.parts.push([p.body, w.offset])
    w.rows.forEach((row, r) => {{ const k = key(w.file) + ':' + row; if (!scene.anims.exists(k)) scene.anims.create({{ key: k, frames: scene.anims.generateFrameNumbers(key(w.file), {{ start: r * w.frames, end: (r + 1) * w.frames - 1 }}), frameRate: w.fps, repeat: -1 }}) }})
  }} else put('body', s.sprite, y)
  if (PROP.lamp && s.lamp) {{          // the light itself: a glow with its middle on the light, or a lamp's picture with its foot on its spot
    const L = PROP.lamp, at = L.middle ? [s.lamp.at[0] - L.middle[0], s.lamp.at[1] - L.middle[1]] : [s.lamp.spot[0] - L.foot[0], s.lamp.spot[1] - L.foot[1]]
    p.lamp = scene.add.image(x + at[0], y + at[1], key(L.file)).setOrigin(0).setDepth(y + s.lamp.spot[1]); p.parts.push([p.lamp, at])
  }}
  // the wind: 0 still air, 1 a breeze, 2 a gust - the same beat goes on, only the row changes
  p.wind = (level = 0) => {{ if (!s.sway) return p; const f = p.body.anims.currentFrame ? p.body.anims.currentFrame.index - 1 : 0; p.body.play({{ key: key(s.sway.file) + ':' + s.sway.rows[Math.max(0, Math.min(s.sway.rows.length - 1, level))], startFrame: f }}, true); return p }}
  p.setPosition = (nx, ny) => {{ p.x = nx; p.y = ny; for (const [o, off] of p.parts) o.setPosition(nx + off[0], ny + off[1]); if (p.body) p.body.setDepth(ny); return p }}
  p.destroy = () => {{ for (const [o] of p.parts) o.destroy() }}
  // where it is in the way: a walker at ground point (wx, wy); a thing flying h metres up over (wx, wy) - the cut nearest that height
  p.solid = (wx, wy) => !!s.solid && alphaAt(scene, s.solid, wx - p.x, wy - p.y) > 0.5
  p.cover = (wx, wy, h) => {{ const c = (s.cover || []).slice().sort((a, b) => Math.abs(a.height_m - h) - Math.abs(b.height_m - h))[0]; return !!c && Math.abs(c.height_m - h) <= 0.15 && alphaAt(scene, c, wx - p.x, wy - p.y) > 0.5 }}
  // in its shade: how much of the light it takes (0..~0.56) from a point h metres up over ground point (wx, wy) - the shadow the ground
  // has where that point's own shadow would fall; nothing from a prop no taller than the point (a rock shades her feet, not her head)
  p.shade = (wx, wy, h = 0) => {{
    const sh = s.shadow; if (!sh || !sh.per_m_up || (sh.height_m ?? 99) <= h) return 0
    return alphaAt(scene, sh, wx - p.x + h * sh.per_m_up[0], wy - p.y + h * sh.per_m_up[1]) * (p.shadow ? p.shadow.alpha : 1)
  }}
  if (s.sway) p.wind(opts.wind ?? 0)
  return p
}}

// a character among several props: the light left is what each leaves in turn
export function shadeOf(props, wx, wy, h = 0) {{ let lit = 1; for (const p of props) lit *= 1 - p.shade(wx, wy, h); return 1 - lit }}
''')


# ---------------------------------------------------------------- Godot 4
def godot(P, out, dst, name):
    copy(P, out, dst); (dst / f'{name}.prop.json').write_text(json.dumps(P, indent=1))
    first = next(iter(P['sides']))
    (dst / f'{name}.gd').write_text(f'''extends Node2D
## {name}, a pixel prop written by SpriteCast's export.py. The node's position is its FOOT: the middle of where it stands, on the ground.
##   side = "90"                 which side shows: {', '.join(P['sides'])}
##   wind = 2                    0 still air, 1 a breeze, 2 a gust (if it sways)
##   cover_at(point, 0.55)       is a thing flying 0.55 m up over that ground point (global) stopped by it?
##   shade_at(point, 1.1)        0..1: how much of the light it takes from a point 1.1 m up over that ground point - darken that part
##                               of a character by it (feet, middle and head each ask for themselves)
## Solid: a StaticBody2D whose polygon is the outline of where it stands - a CharacterBody2D stops at it.
## Light and Shadow lie on the ground (z_index -1); give the node `y_sort_enabled` parents as usual and it sorts by its foot.

var PROP: Dictionary = {json.dumps(P)}          # (every layer's place from the foot, px - the same as {name}.prop.json)

@export var side: String = "{first}": set = set_side
@export_range(0, 2) var wind: int = 0: set = set_wind

var _dir: String
var _images := {{}}
var body: Node2D
var shadow: Sprite2D
var light: Sprite2D
var lamp: Sprite2D
var solid: StaticBody2D


func _ready() -> void:
	_dir = (get_script() as Script).resource_path.get_base_dir() + "/"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_build()


func set_side(v: String) -> void:
	side = v
	if is_inside_tree(): _build()


func set_wind(v: int) -> void:
	wind = v
	if body is AnimatedSprite2D:
		var rows: Array = PROP.sides[side].sway.rows
		var a := body as AnimatedSprite2D
		var f := a.frame
		a.play(rows[clampi(v, 0, rows.size() - 1)])
		a.frame = f          # (the same beat goes on, only the row changes)


func _sprite(layer: Dictionary, z: int, called: String) -> Sprite2D:
	var s := Sprite2D.new()
	s.name = called
	s.texture = load(_dir + layer.file)
	s.centered = false
	s.position = Vector2(layer.offset[0], layer.offset[1])
	s.z_index = z
	add_child(s)
	return s


func _build() -> void:
	for c in get_children(): remove_child(c); c.queue_free()
	body = null; shadow = null; light = null; lamp = null; solid = null
	if not PROP.sides.has(side): push_error("{name}: no side " + side); return
	var s: Dictionary = PROP.sides[side]
	if s.has("light"):
		light = _sprite(s.light, -1, "Light")
		var m := CanvasItemMaterial.new(); m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD; light.material = m
	if s.has("shadow"): shadow = _sprite(s.shadow, -1, "Shadow")
	if s.has("sway"):
		var w: Dictionary = s.sway
		var fr := SpriteFrames.new(); fr.remove_animation("default")
		var tex: Texture2D = load(_dir + w.file)
		for r in w.rows.size():
			fr.add_animation(w.rows[r]); fr.set_animation_speed(w.rows[r], w.fps); fr.set_animation_loop(w.rows[r], true)
			for i in int(w.frames):
				var at := AtlasTexture.new(); at.atlas = tex; at.region = Rect2(i * w.frame[0], r * w.frame[1], w.frame[0], w.frame[1])
				fr.add_frame(w.rows[r], at)
		var a := AnimatedSprite2D.new(); a.name = "Body"; a.sprite_frames = fr; a.centered = false; a.position = Vector2(w.offset[0], w.offset[1])
		add_child(a); body = a; set_wind(wind)
	else: body = _sprite(s.sprite, 0, "Body")
	if PROP.get("lamp") != null and s.has("lamp"):
		var L = PROP.lamp
		var at = [s.lamp.at[0] - L.middle[0], s.lamp.at[1] - L.middle[1]] if L.has("middle") else [s.lamp.spot[0] - L.foot[0], s.lamp.spot[1] - L.foot[1]]
		lamp = _sprite({{"file": L.file, "offset": at}}, 0, "Lamp")
	if s.has("solid") and s.solid.hull.size() >= 3:
		solid = StaticBody2D.new(); solid.name = "Solid"
		var poly := CollisionPolygon2D.new()
		var pts := PackedVector2Array()
		for q in s.solid.hull: pts.append(Vector2(q[0], q[1]))
		poly.polygon = pts; solid.add_child(poly); add_child(solid)


func _alpha(layer: Dictionary, p: Vector2) -> float:          # (p: from the foot)
	if not _images.has(layer.file): _images[layer.file] = (load(_dir + layer.file) as Texture2D).get_image()
	var im: Image = _images[layer.file]
	var i := int(floor(p.x - layer.offset[0])); var j := int(floor(p.y - layer.offset[1]))
	if i < 0 or j < 0 or i >= im.get_width() or j >= im.get_height(): return 0.0
	return im.get_pixel(i, j).a


## is a walker's ground point (global) inside where it stands?
func solid_at(point: Vector2) -> bool:
	var s: Dictionary = PROP.sides[side]
	return s.has("solid") and _alpha(s.solid, to_local(point)) > 0.5


## is a thing flying h metres up over this ground point (global) stopped? - the cut nearest that height, if within 0.15 m
func cover_at(point: Vector2, h: float) -> bool:
	var s: Dictionary = PROP.sides[side]
	var best = null
	for c in s.get("cover", []):
		if best == null or abs(c.height_m - h) < abs(best.height_m - h): best = c
	return best != null and abs(best.height_m - h) <= 0.15 and _alpha(best, to_local(point)) > 0.5


## how much of the light it takes (0..~0.56) from a point h metres up over this ground point (global): the shadow the ground has where
## that point's own shadow would fall; nothing from a prop no taller than the point (a rock shades her feet, not her head)
func shade_at(point: Vector2, h: float = 0.0) -> float:
	var s: Dictionary = PROP.sides[side]
	if not s.has("shadow") or s.shadow.per_m_up == null: return 0.0
	if s.shadow.height_m != null and s.shadow.height_m <= h: return 0.0
	return _alpha(s.shadow, to_local(point) + Vector2(s.shadow.per_m_up[0], s.shadow.per_m_up[1]) * h)
''')
    (dst / f'{name}.tscn').write_text(f'[gd_scene load_steps=2 format=3]\n\n[ext_resource type="Script" path="{name}.gd" id="1"]\n\n[node name="{name}" type="Node2D"]\nscript = ExtResource("1")\n')


MAKERS = {'godot': godot, 'phaser': phaser}


def run(out, to=None, only=None, name=None):
    out = Path(out).resolve(); P = load(out); name = ident(name or (out.parent.name if out.name == 'out-pixel' else out.name)); to = Path(to).resolve() if to else out / 'export'
    for k in (only or ','.join(MAKERS)).split(','):
        if k not in MAKERS: print(f'  {k}: not written for a prop yet (godot, phaser are)'); continue
        MAKERS[k](P, out, to / k, name)
    s = next(iter(P['sides'].values())); has = [k for k in ('shadow', 'light', 'sway', 'solid', 'cover') if k in s]
    print(f"{name}: {len(P['sides'])} side(s), each with {', '.join(has) or 'its sprite only'} -> {to}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out', help='the folder with pixel.json (<name>/out-pixel)'); ap.add_argument('--to'); ap.add_argument('--only'); ap.add_argument('--name')
    g = ap.parse_args(); run(g.out, g.to, g.only, g.name)
