# Walking characters (`charpipe.py`)

An 8-direction walk and standing views from one illustration of the character. The image model can't keep a pose or a body
from frame to frame on its own, so the motion comes from a rigged 3D model. The model only draws over its renders.

Three OKs: `turnaround`, `3d` (= `model` + `rig` + `render`), `draw` (then `finish` + `preview` by themselves). The steps:

| step | what | cost |
|---|---|---|
| `turnaround` | front / right / back drawn from the illustration (A-pose, hair behind the shoulders); the left view mirrored from the right | ~$0.09 OpenAI |
| `model` | Tripo multiview-to-model from the four views (turned to face front for the rig); or Meshy multi-image-to-3D with `"modeler": "meshy"` | ~30 Tripo credits (+10 if it comes back uncoloured; or ~30 Meshy) |
| `rig` | Tripo: rig check, rig (mixamo bones), walk + idle retargeted in place; bone names fixed, the walk's hips put back, feet planted as modelled | ~45 Tripo credits |
| `render` | the walk (8 frames × 8 facings) and the idle (8 facings: SpriteCast's own standing pose, `idleclip.py`, added to a copy of the rig - `"idle_from": "tripo"` for the rig's own), the head raised `head_up`° (a rig's walk looks down); each with its 3D shadow (`-s.png`) | free |
| `draw` | 4 frames a call on one sheet; the front first, every other sheet given it; a walk's second sheet given its first; every facing drawn (`"mirror": true` flips the west side from the east) | ~$0.10 a sheet, 18 sheets ≈ $2 (12 ≈ $1.3 with `"mirror": true`) |
| `finish` | each frame cut out (its cell cut wider), fitted onto its render (one upper-body size per sheet, the legs to the render's feet), heads steadied within a facing and sized to the 3D model's in every facing, `head_fit` applied, edges cleaned; strips and a shadow per frame | free |
| `preview` | every frame on one sheet, a GIF per facing, and every facing walking at once in `walk-all.mp4` (with ffmpeg) | free |
| actions | (optional) `"actions"` in the spec: each rendered, drawn and finished like the walk → `out/<name>-<facing>.png`, `"actions"` in `character.json`; `rig` asks Tripo for the presets (run, jump, slash, shoot, dive, climb, fall, hurt, turn; three beside walk and idle), your own rig gives any clip; `"hold"` puts a shape-built thing (an umbrella) in the right hand; `"head": "as_render"` draws the head bowed and turned as the render (the slash's default - the walk's "eyes ahead" lifted it); `"fps"` in an action sets its pace in the game in place of its clip's own (the rain girl's cuts: 14.3, 70 ms a frame, the joins before and after at 9 - the cut read as weak at the clip's pace; a pause on the frame that hits is the game's to add, when something is hit); `redraw` covers actions: a held thing in the wrong place (checked against the render's held thing alone) is redrawn by itself, a frame only a little off is listed for the user (`--low` redraws it too) | ~10 Tripo credits and ~$1.8 an action |
| `sit` | (optional) the rig seated in 8 facings (`render/sit-*`), then with `--draw` drawn and finished → `out/sit-<facing>.png`, `"sit"` in `character.json` (`frame`, and per facing `file`, `seat`, `seat_height`, `shadow`) | free; `--draw` ~$0.22 |
| `export.py <name>/out` | (its own script) the finished set as files an engine opens as they are → `out/export/`: `godot/` (a folder to drop into a Godot 4 project: `<name>.tscn` with Shadow and Body, two SpriteFrames, `<name>.gd` with `play("walk", "south-east")`), `phaser/` (`<name>.js`, an ES module for Phaser 3: `preload`, `create`, `add`), `aseprite/` (`<name>-<action>.aseprite`: a tag per facing, layers `shadow` and `body`, a slice `feet` with the pivot; a swing's effect as a layer `effect`), `unity/` (copy its contents into `Assets/`: an editor script builds `<name>.prefab` - Animator > Shadow, Body - with a clip per animation; `GetComponent<Animator>().Play("walk_south_east")`). Each animation's shadows become one strip with one offset; a swing's effect (`"trail"`) is a third sprite, Effect, over the body, at its own pace - its cells on sheets of at most 4096 px a side (several where one would pass it: `<key>-effect.png`, `-effect-2.png` ...), which Godot, Phaser and Unity read in order. `--only godot,aseprite`, `--to DIR`, `--name`. Checked by opening them in Godot 4.7, Phaser 3.90, Aseprite and Unity 6000.3; pixel sets (`pixel.json`) are not read yet | free |
| `pack` | frames/ → out/ strips again (after `touchup.py --apply`; `finish` packs too) | free |
| `touchup.py` | (optional) a local page to fix frames by hand: red clears, green brings pixels back from the drawing; `--apply` lays them on and packs; `finish` re-applies them | free |
| `facecheck` | (optional, needs mediapipe) one character's head for its height against another's, facing by facing, by face landmarks; `--apply` writes `head_fit` | free |

## The spec (`<name>.json`)

```json
{
  "name": "man",
  "design": "design.png",
  "face": "face.png",
  "photo": "photo.png",
  "description": "a young man with short dark wavy hair and a soft curly fringe, a pale sky-blue cable-knit sweater, dark indigo jeans with a black belt, black leather loafers",
  "notes": "",
  "head_up": 24,
  "frame_px": 256
}
```

| key | |
|---|---|
| `design` | one finished full-body illustration: the face, the outfit and the drawing style (required). **Facing front, standing straight with the arms down, no pose** (no hands in pockets, nothing held): a pose in it leaks into the turnaround and the frames |
| `face` | optional: the face seen strictly from the front, the same style |
| `photo` | optional: a photo for the likeness only |
| `description` | who they are and what they wear, in words, used in every prompt |
| `notes` | extra rules for every frame, e.g. "her hair falls in front of her left shoulder" or "no marks on the arms" |
| `modeler` | `"tripo"` (default: one 3D account for the model and the rig) or `"meshy"` (the author's way: Meshy's mesh and texture held up better on faces; needs `MESHY_API_KEY`) |
| `draw` | `true` (default); `false`: no image model draws the frames - the 3D renders are the frames (toon-shaded, the model's own texture), with the same 3D shadows: ~$0.09 + the 3D only, but softer (no drawn lines, a simpler face, blurrier fur). The image model still draws the turnaround (the ~$0.09); with your own `rig_glb` it draws nothing at all (`render`, `finish` and `preview`, all free) |
| `mix` | facings mixed frame by frame with their pair, e.g. `["north-east"]`: both drawn, each frame of each the better (by overlap with its render) of its own drawing and the other's flipped; what `redraw` settles a facing with after two tries |
| `facings` | `8` (default), `4` (or `"diagonal"`): the four diagonals only (south-east, south-west, north-east, north-west), or `"cardinal"`: south, east, north, west only - rendered, drawn, finished and packed; about half the drawing. The first (south-east, or south for the cardinals) is drawn first and the others follow it. `export.py` gives every engine a play() that takes all eight directions and shows the nearest drawn (between two as near, the one shown last; with none yet, the one turned more toward the viewer). `pixelart.py` draws these facings unless `--dirs` says others |
| `view` | `"above"` (default) or `"side"`: a side-scrolling game. The camera level and straight from the side (`pitch` 0), the head level (`head_up` 0), ONE facing drawn - east, walking to the right - and west flipped from it in `finish`, also with something in the hand (`"mirror": false` draws west too). West is east in a mirror about the picture's middle and nothing else: frame k of every animation - the walk, a loop, a one-shot, an in-between - is east's frame k mirrored (no half-cycle shift, so a `grab` that ends on the climb's first pose joins it the same way facing west), its trail and shadow are east's mirrored too, and `render` does not render it at all (an earlier render's west files are taken away). `pixelart.py --dirs east,west` then stops: west is drawn on its own only with `"mirror": "never"` (rendered again). A walk is 2 sheets, the standing view 1. The feet of every frame on one line; no shadow (a level camera sees the ground edge-on - the game draws its own). `facings` is not used. `pixelart.py` draws east only here (`--dirs east,west` for both). Not yet in this view: a jump cut into rise and fall; sitting (`sit --draw` stops - draw a seated pose as a `creature.py` sheet); a shadow. For monsters and townspeople, `creature.py` (creature.md) |
| `turn` | with `"view": "side"`: degrees the body is turned toward the viewer while it walks sideways - `0` a flat profile, `30` one eye showing, `45` (the default, as creature.py's people) both eyes (side-scrolling RPGs with big heads), `60` the stride closes up. A cut made ACROSS the body is hidden behind it at 0: turn 30-45 for a character that swings something. In a spin the render shows the back of the head in some frames and the drawing may give them a face: look, and draw those alone (`frame`) |
| `floor` | `true` in a side view, `false` otherwise: each pose whose feet the clip sinks under the ground is lifted until its lowest point stands on it (never lowered: a jump stays a jump). A side view shows the ground as ONE LINE, and the rain girl's cuts (Mixamo sword clips on a child's short legs) put her boots up to 5% of her height under it - the user: "her feet go through the ground for a moment". `render` says how far each action sinks (`render.json` → `"floor"`: every frame's lowest point before the lift). After it the 3D feet stood on one line in every frame. An action's drawn frame that reaches under its render's lowest point is lifted too (moved on a clear canvas - nothing wraps round to the bottom; where it ends is measured on its biggest piece and the pieces lying on the render, so a stray speck or a shadow drawn under the feet does not lift it); a frame can still sit a few px low - that is the drawing, look at it. |
| an action's own keys in a side view | `"fps"`: its pace (an attack at 14.3 = 70 ms a frame beside joins at 9). `"face": "away"` (or `"viewer"`, or degrees): seen from another side - a ladder climbed with her back to us. `"in_place": true`: the hips' height pinned (a climb's clip rises; the game moves her). `"air": true`: each pose's lowest point put ON the ground line either way - a jump's frames, moved by the game; a trail's pieces still splash, stop or die at the real ground under her (as far under her boots as the pose is up), not at her boots in mid-air. `"head_up"`: this action's own (a deep crouch bowed the head until only hair was drawn; 30 showed the face). `"canvas"`: a bigger picture for a reach that leaves it - `render` now warns when a figure or what it holds is cut by the picture's edge. `"hold": {..., "on": "back"}`: the held thing slung across the back, both hands empty |
| `mirror` | `false` (default): all eight drawn; a facing flipped only when `redraw` mixes a pair that stayed low (each frame the better of its own and its pair's flipped). `true`: west, north-west and south-west flipped from east, north-east and south-east - 6 of the 16 walk sheets not drawn (~$0.66 less), only for a design that is the same on both sides (not hair over one shoulder, a logo, a bag, one ear up); or a list of facings to flip from their pair, e.g. `["north-east"]`. A flipped facing is only as good as its pair (a raincoat girl's west flipped 0.75-0.80, drawn 0.83-0.93). Shadows stay each facing's own (a side view: the pair's, mirrored - west has no render). `"never"`: nothing is ever flipped, not by `redraw` either - a facing still low after two tries gets its low frames drawn alone, as south and north do. For a character that is NOT the same on both sides (a thing in one hand, an eye patch, one sleeve): flipped, it changes sides. Set by itself when the spec has a `hold` |
| `hold` | (optional) something the character **carries all the time**, in one hand: there through the walk, the standing views and every action that has no `hold` of its own (`"hold": false` in an action: the hand empty there). `{"kind": "pistol", "hand": "left"}` - `kind`: `pistol`, `watergun` or `umbrella` (built from shapes on the hand's bone at real size; `length` in metres, `color`, `handle`, and `grip` / `offset` to turn and place it - look at the renders). The hand closes on it: the fingers of the holding hand are bent round the handle in every frame, for whatever is held (`"curl": false` for an open hand, or the degrees at the three joints, e.g. `[60, 75, 55]`); `hand`: `"right"` (default) or `"left"`, in an action's own `hold` too. `words`: your own sentence for it. A thing that is already part of your rigged model (`rig_glb`): `{"in_model": true, "words": "In the LEFT hand: a black pistol ..."}` - nothing is attached, the drawing is told what it is and which hand, and nothing is flipped. With a `hold`, `mirror` is `"never"`, and `finish` checks the thing is where each render has it (`redraw` draws the sheets where it is not). Free to try: `render` again and look. Changing it means `draw` again (paid) |
| `kind` | `"person"` (default) or `"animal"`: a four-legged animal - no rig bought; its skeleton is found from the mesh and it walks in a cat's or a dog's gait (see Animals) |
| `model_glb` | an animal: your own static model in place of `3d` |
| `mannequin` | `true` renders the model as a pose to draw ANOTHER design on - one pale grey, the limbs of its right side red and of its left side blue (an animal's legs; a person's arms and legs: which is the near one reads in every frame), an animal's tail taken off (a stag drawn on a mannequin with a tail got a wolf's brush). `creature.py` uses it ([creature.md](creature.md)) |
| `fit` | an animal: `{"leg", "body", "nose_up", "nose_out"}` - its legs' length, its body's depth, how high and how far forward its nose is, each as a ratio to the distance between its fore and hind feet; the mesh is stretched to them before its skeleton is looked for (limits x0.25-2.5; the render prints the factors). A head carried under the back's line: the neck is only made as low as it goes |
| `rig_glb` | skip `turnaround`/`model`/`rig`: your own rigged GLB with clips named `walk` and `idle` |
| `head_up` | degrees the head is raised in the renders (24) |
| `white_shoes` | true for white (or very light) shoes: small holes inside the outline round the feet are filled after the AI cut-out (a lace or a sole the segmenter left out). Off otherwise - a heel's straps or a boot's laces have real gaps |
| `shoulder_up` | degrees each collar bone is turned up in the renders (15): squares the shoulders Tripo's rig slopes - see below; 16 for a broad-shouldered man, 0 to leave them |
| `shoulder_wide` | how far out the collar and arm bones are set (1.05; 1.1 for a man); small on its own |
| `pitch` | camera degrees down (30 = 2:1 isometric) |
| `frames` | walk frames (8) |
| `walk` / `idle` | clip names and times: `{"clip": "walk", "t0": 0, "t1": 1.1835}` (one stride of Tripo's walk), `{"clip": "idle_spritecast", "t": 0}` |
| `idle_from` | `"spritecast"` (default): the standing pose and the clip `idle_spritecast` are SpriteCast's own (`idleclip.py`: a relaxed stand, a 4 s loop of a breath and a sway, made here - set side by side with a Mixamo Standing Idle, the same to 1-3 % of the height); `<rig>-idle.glb` is made beside the rig, free. `"tripo"`: the rig's own `idle` clip. An action can use `"clip": "idle_spritecast"` to stand with something in hand (`"frames": 3, "loop": true`). A rig without Mixamo's bone names keeps its own idle, said aloud |
| `neck` | where the neck is, as a share of the figure's height from the top (0.16), for steadying the heads |
| `frame_px` | output frame height (256); `pack --px N` makes another set at N px in `out-Npx/` |
| `render_px` | the renders' and finished frames' size (1024; a project rendered at 512 before keeps that until you set it) |
| `light` | `"right"` (default: shadows fall up and to the left) or `"left"`, as for props |
| `shadow` | `"3d"` (default): each frame's shadow from the 3D body; `"none"` leaves them out |
| `anchor` | `"ground"` (default): the feet are the 3D ground under the character's middle; `"soles"`: the bottom of the shoes standing (2 px under the lowest painted pixel of the standing front). In this view the ground under the middle is 4-7 game px above the near sole, so next to characters anchored on their soles a `"ground"` one stands sunk in |
| `redo_below` | the overlap under which `finish` names a sheet for `redraw` (0.75). For people 0.8 was tried and was too high: of four outfits the frames that were really wrong scored 0.57-0.74, and the many at 0.75-0.79 looked fine walking - what the score can't see (a head growing and shrinking, ears the wrong way round) shows in `walk-all.mp4` |
| `head_fit` | `{facing: factor}`: the head rescaled about the neck by that much in `finish`, after the heads are sized to the 3D - written by `facecheck --apply` to match another character, or by hand |

## Output (`<name>/out/`)
`walk-<facing>.png` (a strip of `frames`), `idle-<facing>.png`, `shadows/walk-<facing>-<i>.png` and `shadows/idle-<facing>.png`
(black, its darkness in the alpha - draw it under everything at character.json's `shadow_alpha`: 0.56 for shadows as light falls, the default since 0.20; 0.3 for `"shadow": "flat"`, the one hard shape), `character.json` (frame size, anchor between the feet as a fraction of the
frame, fps, `shadows`: each frame's `{file, offset}` - its top-left from the frame's top-left in frame px, often negative: it falls
past the frame's edge - and the fit report), `sheet.png` and `walk-<facing>.gif` (with the shadows). Facings: south (toward the viewer), south-east, east,
north-east, north, north-west, west, south-west.

## Things learned the hard way
- **Show the turnaround before `model`.** Whatever is wrong there is baked into the 3D model. Both sides of the outfit the same;
  nothing hanging beside or over the arms: hair beside an arm gets painted onto the arm.
- **Give the modeler the left view** (mirrored): with only front/right/back Meshy guessed the left side and smeared colours there.
- **Tripo turns each model its own way.** A girl came out facing +x, a man -x - built facing backwards, so the front render
  showed the back of his head ("his face is painted black" was that). `rig` reads the way the skeleton's feet point (heel to toe,
  at rest) and turns the model to face +z, the renders' front. Look at `render/idle-south.png` before `draw`: the face, not hair.
  Meshy's models faced front every time.
- **Tripo sometimes sends the model back uncoloured** (asked for a texture, a flat grey one came back - a raincoat girl from four
  views, 2026-11-03; a man from three views was coloured). `model` checks and, if so, textures it again from the same four views
  (`/models/texture`, ~10 credits) → `model/textured.glb`. Tripo rigs only a generation task, so `rig` rigs the first one and lays
  the new texture on afterwards: the same triangles in another order and another UV layout, matched by their centres (to 1e-6).
- **Look at the model's thumbnails before `rig`.** Small texture marks can be left to the drawing: say in `notes` that they are
  errors. Patching a texture tends to spread them.
- **Raise the head** (`head_up` ~24): a rig's walk looks at the ground, and the drawing follows it, so the character comes out hunched.
- **Sloping shoulders: fix them in the render, not the model.** A rig made from a design often slopes from the neck, and
  from 30° above it looks worse; the drawing follows. `shoulder_up` turns the collar bones up (the arms turned back so they
  hang as before), `shoulder_wide` moves the shoulder and arm bones out. Arms keep their thickness and the bust stays as it
  is: only the shoulder tops and the armpits stretch. Free to try - re-run `render` and look before `draw`.
  - **The angle does most of it.** Raising the collar bones also carries the arms out, so it widens the silhouette by itself:
    15° gave +9-17 % at the shoulders, while `shoulder_wide` 1.0 → 1.15 added only 3-6 %. Pick the angle; the multiplier only trims.
  - **What looked natural** for the two leads this was made for: a man `shoulder_up` 16, `shoulder_wide` 1.1; a woman 15 and 1.05.
    Past ~25° it reads as a shrug; 10° keeps a softer, rounder shoulder.
  - **It's the rig, not the modeler.** In the A-pose both Meshy's and Tripo's meshes follow the design's shoulder line (Tripo's
    a little closer); the slope comes with Tripo's rig and its walk and idle, so a Tripo model needs it too - the same man from
    Tripo, 16 and 1.1, came out as wide as the design at the shoulders (127 vs 126 px at 19 % of his height).
  - **To choose:** render the front at eye level (`pitch` 0) and lay the design's outline over it at the same height - the
    shoulder line and the width are easy to compare there; judge by eye, not by an automatic width measure (hair and arms fool it).
- **Cutting the figure out of the white sheet: an AI segmenter, by default.** The old key took the white joined to the edge, so
  white sneakers or a light shirt touching the paper went with it, and lowering the threshold left the paper's specks behind.
  `finish` now uses BiRefNet, run with onnxruntime alone (rembg's export of it; rembg itself and its packages aren't needed - the same
  mask to the pixel): the white sneakers whole, no specks (with `white_shoes`, small holes inside the outline round the feet filled
  too). The lite model by default (224 MB, fetched once into ~/.cache/spritecast/models, ~3 s a frame on a CPU): within a pixel of
  the full one's outline (99.3-99.8 % overlap on the drawn sheets, the white sneakers too); `SPRITECAST_KEY_MODEL=general` (973 MB)
  for the full one. Of the models tried, ISNet left parts of the shoes half see-through and U2Net blurred the edge.
  `SPRITECAST_KEY=white` brings the old key back; without onnxruntime it is used anyway.
- **One upper-body size per facing, the legs to the render's feet.** GPT draws some frames of a walk a little taller, mostly by
  drawing a stride's legs longer. Fitting each frame by best overlap with a free scale made the head bob up (up to 27 px); fitting
  each frame whole to its render's height then made the body grow and shrink. `finish` scales the upper body (above 47 % of the
  figure) once for the whole facing - the median of render height / drawn height - and stretches only the legs to meet the
  render's feet, then searches sideways: the head steady, the feet where the render puts them.
- **Cells cut 64 px wider.** A stride's foot is sometimes drawn over the cell's edge; cut at the edge, the boot came out flat.
  Each cell is cut wider and only its own pieces are kept (a piece that runs to the wider cut's edge is the neighbour's).
- **Shadows from the 3D body, not the drawing.** Laying each drawn pixel down by its 3D height left holes wherever an arm hid the
  body behind it, and a lumpy edge. The 3D body pressed flat along the light is what that figure really casts: solid, the feet
  touching it, a lifted foot's shadow apart, the legs' shadows moving each on their own. The drawing follows the render's
  outline closely, so the two match.
- **Body shape comes from the 3D model**: the drawing follows its outline. Change the turnaround and remake the model, not the prompt.
- **One sheet drawn bigger than the other.** Each sheet of four is its own drawing, and the model drew a whole figure - hair, body and
  all - up to ~15 % bigger in one (an alien outfit's second sheets). Steadying only the heads then shrank the head and left the big hair
  and body: it read as the head growing and shrinking. `finish` now fits once, measures each sheet's heads, refits each sheet's upper
  body at its own size (`sheet_scales`), and only then steadies the heads.
- **The crown is the top of the head**, not of what stands on it: the first row as wide as 40 % of the head (`_figure`). An antenna's
  tip or a bunny ear, drawn taller in one sheet than another, threw the head's band and its neck off.
- **Heads sized to the 3D model in every facing** (`even_heads`): the facings are drawn one by one and came out up to ~15 % apart (an
  alien's side views). Sizing them to the front's was tried first - and the front was the big one (a face check showed it). Each
  facing's drawn head against its renders by the silhouette under the crown (`head_vs_render`, ~ the square root of the head's size, so
  the correction is squared and measured again), rescaled about the neck, at most 15 %.
- **Comparing two characters** (`facecheck`): hair fools any silhouette measure - one outfit's full waves read as a big head, and
  matching others to it made their fronts 12 % too big. Face landmarks (MediaPipe's Face Landmarker: forehead 10 to chin 152, over
  chin to the soles) don't see hair. Only fronts and three-quarters have a face to find; the backs and profiles are given the same
  drawn-to-3D head ratio the found facings have. A facing flipped from its pair takes its pair's factor.
- **Thin things on the head or body** (a headband, ears or antennae on it, a bow, straps) come out rough in the 3D model, and the
  drawing followed the render: bunny ears swapped side and showed their pink insides from behind, a headband's eyes showed pupils
  from behind. The prompt now says to draw them as the turnaround shows them, from behind only their backs. If a back view still has
  one the wrong way round and the back is otherwise symmetrical, take each frame from the one half a stride on, flipped and moved onto
  its render (`flip_onto`) - free, and the stride stays right.
- **Standing a little taller than walking** is the rig's own (its idle stands straighter): both match their renders within 0.5 %.
- **Refused drawings.** OpenAI's safety check now and then turns a sheet down (legs, a short skirt) at random: it is asked twice more,
  then that sheet is left as it was and the run goes on; draw it again later, or say less about skin and length in the description.
- **Back views**: the prompt says to show the back of the head and the back of the clothes, or a face can appear on a back view.
- `finish` prints each walk's overlap with its renders. Under ~0.7, look at that facing and redraw it:
  `draw --only <facing> --again --yes`.

## Animals (`"kind": "animal"`)
- **Why not Tripo's rig.** Its quadruped rig (v2.5, the only one for animals) put a cat's leg joints in place but had no backbone, a
  hind thigh named "Spine", the shoulders hanging off the neck, once a fifth foot; its one animal clip is a walk, no idle. So `3d` makes
  only the model (~30 Tripo credits) and `render` finds the skeleton itself (render_char.html `loadQuad`):
  - the feet: the vertices within 10 % of the height off the ground, in four clusters (k-means seeded at the four corners); fore / hind
    by the long axis, left / right by the side;
  - the belly: the lowest point of the middle between the legs; the back's top along the long axis; the legs' joints along each leg's own
    vertices at set fractions of the belly's height (fore: elbow 0.55, wrist 0.12; hind: knee 0.7 a little forward, hock 0.3);
  - the head: forward of the chest and up - its pivot behind the middle of what's there, its end at the nose (the frontmost point);
  - the tail: what lies behind the rump and above the hind paws, five bones out from its root by distance; none if there is none;
  - which way it faces: the body's long axis, the head's end the one whose top is broadest (ears and a head against a thin tail),
    then turned to face +z - checked on a model turned all four ways;
  - each vertex weighted to the nearest bones (1 / d⁴ over each bone's segment, a leg only on its own side, the upper legs not up into
    the back), the best four.
- **The walk** (`quadFrames`): the game cat's gait - the lateral sequence LH, LF, RH, RF a quarter cycle apart, stance 62 %, the paw
  lifted and the elbow / knee and hock folded in swing, the back bowing and swaying, the neck against it so the head stays on its line,
  the tail carried up and swaying once a stride; seen from behind the tail is carried off to one side (straight up it vanished against
  the back). The idle is the rest pose with the tail up.
- **Finishing**: one scale for the whole figure per facing, standing on the render's feet (no upper body over legs, no head steadying).
- **Clothes**: only snug ones - a vertex is weighted to the bones nearest it, so a cape or a scarf's loose end moves with a leg.
- Tripo's multiview once gave a cat five feet: look at the renders; make the model again, or use `"modeler": "meshy"`.
- **Redrawing what doesn't fit** (`redraw`, people too): a sheet with a frame under `redo_below` (0.75) is drawn again, up to twice; a
  facing still under it then is mixed with its mirror pair - the pair drawn too if it was being flipped, and each frame of both the better
  of its own drawing and the other's flipped (the cat's north-east 0.63-0.92 and north-west 0.82-0.93 → 0.87-0.92 and 0.85-0.93, each
  its own frames 1-4 and the other's 1-4 flipped; it walked more naturally than either flipped whole); kept in `draw/mirror.json` as
  "best" (in a spec: `"mix"`). South and north have no pair: a frame of theirs still under the line is drawn alone (its render in the second cell of an otherwise white sheet, so it comes out at the
  sheets' scale and is cut the same way - `draw/walk-<facing>-single-<k>.png`), once. Each time the drawing that fits better is kept.
  Stop after a sheet's second try and show it before drawing frames alone (they cost a sheet's price each). On the orange cat: of six
  sheets redrawn once, five improved (west 5-8 0.75 → 0.89, north-west 5-8 0.76 → 0.84) and one came out worse and was put back.
- **Fitting an animal's frames**: one scale a sheet (each sheet is its own drawing - one came out a little bigger than the other), the
  scale chosen by best overlap (0.8-1.2 of the height's): the height is mostly the tail, drawn a little higher or curled its own way, and
  fitting by it shrank a whole facing (south-west 0.63 → 0.79). A frame drawn alone gets its own scale.
- **Room for the shadow**: an animal is rendered with the bigger of its height and length 0.72 of the view - at 1 a cat with its tail up
  threw its shadow past the picture's edge.
- **Flipping a facing from its pair** (`mirror`): the renders of east / west (north-east / north-west, south-east / south-west) are
  mirror images about the figure (not the picture's middle: flipped where it stood a frame came out ~18 px off, 0.42-0.76 overlap - so
  each flipped frame is moved sideways onto its own render, `flip_onto`, 0.70-0.90), and flipping swaps the left and right legs, half a
  stride: frame k is the pair's frame k + n/2 flipped. Its shadow is its own render's (the light comes from one side).
  A SIDE VIEW is not this: west is the exact mirror about the picture's middle, frame k from east's frame k in every animation, and it is
  not rendered (half a cycle on, the climb's west started on the mirror of east's frame 4 while the grab before it ended on the mirror
  of frame 0 - the hands swapped at the join; and its trail, taken unshifted from east, ran half a cycle off the body).
  The orange cat's north-east, drawn twice at 0.63-0.70, flipped from north-west: 0.80-0.92 against its own renders.
- **`finish` again is quick**: each sheet's cells are cut out once and kept in `frames/cut/` by the sheet's name, cell and modification
  time, so after a `redraw` only the changed sheets are cut (the AI cut-out is ~3 s a cell on a CPU): the cat's first finish 211 s, the
  next with one sheet changed 28 s.

## Notes

The output has a shadow per frame from the 3D body (`out/shadows/`, offsets in `character.json`): tell the user to draw it under the
sprites at `character.json`'s `shadow_alpha` (0.56). Since 0.20 a shadow is light as it falls - deep under the feet, pale at its far
edge; `"shadow": "flat"` in the spec gives the old one hard shape at 0.3 (the render takes longer for the new one, ~9 min a character
with three actions). **How deep**: `"shadow_strength"`, the shadow as if laid that many times - a painted set's default is 1 (56 % at
its deepest), a pixel set's 1.5 (71 %: pixel art says things a little louder, so a figure stands on the ground). On dark ground offer
1.6-2, on a light floor where it looks heavy 1; `pack` (or `pixelart.py`) again is free and `shadow_alpha` goes with it. The same
number for the game's props, so they agree. If their game's other characters stand on the bottom of their shoes, set `"anchor": "soles"` (the default,
the 3D ground under the middle, stands 4-7 game px lower). **Several characters or outfits that should match** (the same person in
other clothes): `facecheck REF.json --with A.json,B.json` (free; needs mediapipe, Python 3.9-3.12) compares the face for the height,
facing by facing, by face landmarks - hair fools any outline measure - and `--apply` writes `head_fit` into their specs for `finish`. A rig rendered before this version has no `-s.png`: re-run `render` (free) before `finish`.
**The cut-out needs onnxruntime** (in requirements.txt): run every step with the `PYTHON=` doctor.py prints. A Python without it now
stops `finish` with a message instead of quietly cutting by the paper's white (which takes white clothes away and leaves paper between
the limbs); `SPRITECAST_KEY=white` cuts by white on purpose.

## A held thing: the hand closes on it - LOOK at the hand before `draw`

`render` (free) closes the holding hand on the handle by itself, for whatever is held, and shows it:

- **What it does.** The handle is laid against the palm with its far edge under the first joints of the fingers. Each finger then bends
  its three joints together, in a finger's own proportions, until some part of it touches the handle - so the fingers lie round it,
  not through it. The thumb comes round the other side, on the outside of the handle, its tip toward the fingertips:
  **fingers - handle - thumb**, the handle between them. A thing with no handle (a ball on the palm) leaves the hand open.
- **What it prints**, a line per held thing: each finger's three bends and how far its tip is off the handle's surface, then the thumb.
  Read it: a tip **under 0** is inside the handle; a thumb more than **0.5 %** of the height from its place did not reach;
  "never nearer the handle's middle than" **under 1** means the thumb goes through it. Any of these: do not draw yet.
- **What it saves: `render/hand-<walk or action>.png`** - the hand from six sides, from above and from below, with the thing (top row)
  and without (bottom row), the arm clear of the body. **Open it and look before `draw`.** In a frame the grip is a few pixels: the
  numbers said "reached" for a thumb that was folded into the fist, and only this picture showed it. Look for: the fingers on one
  side of the handle and the thumb on the other; no finger out straight beside a closed fist; no finger hooked at one joint only;
  the handle's ends showing either side of the hand.
- **When it is not right**, in this order, all free (`render` again each time):
  1. the handle is too thick to get the hand round → make it thinner: `"grip_r"` (its radius, as a share of the figure's height;
     the built-in guns' grips were a thick box and were made a thin cylinder for this);
  2. the fingers sit in it or stand off it → `"finger"` (half a finger's thickness, 0.009);
  3. the thumb is wrong → `"thumb_at"` (degrees round the handle from its wrist side where the thumb's last joint lies, 20);
  4. the whole thing sits wrong in the hand → `"grip"` (its turn in the hand) and `"offset"`, as before;
  5. `"curl": false` for an open hand, or `"curl": [45, 50, 40]` to set the three bends yourself.
- **A new kind of thing** (in `render_char.html` `HOLDS`) needs one line beyond its shapes: where the middle of its handle is and how
  thick - `g.userData.grip = { at: [x, y, z], r: radius }` (or `half: [along the fingers, off the palm]` for a box; `hl`: half its
  length). Everything above then works for it. Tell the user when a thing they ask for is not built in, and build it.
- Show the user `hand-*.png` with the renders, before the first paid sheet.

## The poses between two animations: `"between"`
A walk does not end in an attack's first pose: played one after the other, the body jumps (the user: "the change from the walk to
the attack stance is awkward - can we make the frames between? we have the 3D model"). An action with `"between"` is those frames:

    {"name": "ready",   "between": ["walk", "slash"],     "frames": 3}      the walk's first pose → the slash's first pose
    {"name": "recover", "between": ["slash:end", "walk"], "frames": 4}      the slash's LAST pose → the walk's first

- **How.** The rig plays both clips at once, each stopped at one moment, and the weight goes from the one to the other (eased: it
  leaves and arrives gently); the hips stay where each clip keeps them. `frames` poses strictly between the two ends: the ends
  themselves are the animations' own frames. An end is `walk`, `idle` or an action's name (its first pose), or `<action>:end`
  (its last: that action needs a `"t1"`).
- **Free to render** (`render --only ready`), and LOOK at the renders: a blend of two far-apart poses can pass an arm through the
  body. Then it is drawn like any action (`draw`, or `pixelart.py --clips ready`) - one sheet for three or four frames.
- **What is held**: the far end's `hold` (or the near end's, if the far end holds nothing), so the thing is in the hand all the way.
  For it to be there in the WALK too, the walk must carry it: `"hold"` in the spec itself, or an action on the walk's clip
  (`{"name": "carry", "clip": "walk", "t0": 0, "t1": <the walk's t1>, "loop": true, "hold": {...}}`) - otherwise the thing
  appears from nowhere in the first in-between.
- **In the game**: walk ... its first pose → `ready` → the attack → `recover` → the walk's first pose and on.
- Checked on the rain girl, south-east, drawn and as pixel art (walk with the umbrella, 3 down, the slash, 4 back up). Not checked:
  `pack`'s frame rate for it (it takes the walk's).

## Moves that join: `motion.py` - free, on the rig, nothing drawn
A combo is moves played one after another; how each joins the next is what the player feels. Each command (`ground`, `plant`, `link`, `blade`, `layer`, `join`; `preset` runs a recipe of them) writes a copy of the
rig (`rig/rig-<tag>.glb`) and print the spec's `"rig_glb"` line; render and LOOK after each (`charpipe.py render --only ...`).
- **`ground SPEC clip ...`** - the lower foot on the ground in every frame. A Mixamo clip carried onto a child's rig by `addclip.py` stood
  8-15 cm in the air and bobbed up through the swing.
- **`plant SPEC clip ...`** - the feet held where the clip's first frame has them; the hips' turn (up to 98 degrees in Mixamo's sword
  slashes) goes into the spine, so all above the waist moves as before. For a swing whose legs jump from stance to stance (the user:
  "the legs change too abruptly from pose to pose").
- **`layer SPEC A@t0-t1 B@t0-t1 NAME [--from Spine]`** - A from the `--from` bone up (the arms' swing) on B's legs (a jump): a cut made
  in the air from a standing cut and a jump, the two clips' times stretched to one length.
- **`link SPEC A@time B@t0-t1 NAME [--blend 0.4]`** - B started from the pose A is in at that time; the difference to B's own pose fades
  out over the blend, inside B's wind-up, so B's stroke is B's own. The way games join moves (inertialization). Better than `"between"`
  for attacks: in-between poses made a swing float, and cost frames. Link B from the time A's LAST DRAWN frame shows (`"t1"` of A's
  action), not the end of A's clip.
- **`blade SPEC clip --stroke t0-t1 [--bend 0.55] [--lag 0.9] [--max-turn 100]`** - an axe's chop made a sword's cut (the user, of Mixamo's
  "Standing Melee Attack Downward": "made for an axe - a bit unnatural for a sword"). The forward bend cut to `--bend` of itself (46 ->
  25 degrees; the thighs turned back so the feet stay); the wrist turned so the blade runs on from the arm through the stroke - at the
  hit the axe's blade pointed BEHIND her - and, with `--lag`, trails the hand early in the stroke and catches up at the hit: its tip on
  an arc round the shoulder (the user: "swing it more in an arc" - the tip 0.66-0.69 from the shoulder all through, its path 16 % longer).
- **`join SPEC NAME clip:t0:t1 ...`** - clips as one, to render a whole combo at 24 a second (`"frames"`: seconds x 24) and look at the
  joins: eight frames a move showed the user a stutter, not the motion.
- **What looks right**: real motion capture. Moves made here from key poses (an image model's poses on a colour-coded mannequin, fitted
  to the rig) and a clip played backwards read stiff beside a Mixamo move (the user: "only the backhand looks natural"). Ask for Mixamo
  moves of ONE set (one actor: "Standing Melee Attack Downward / Horizontal / Backhand / 360", "... Combo Attack Ver. 1-3"): they start
  and end in the same stance, and link with nothing to see. A sword-and-shield set swings the free arm as if it held a shield.
- **The same combo in one command: `motion.py preset SPEC.json rain-girl-combo [--fbx DIR]`** (free) - `presets/rain-girl-combo.json`
  keeps only what was done to Mixamo's moves (the steps below, their numbers, the two actions and what the game does with them),
  never the moves: the user downloads the two FBX files (steps 1), the preset carries them on and makes the same changes. Built from
  scratch on the rain girl's rig it matched the game's rig within 3 mm. Missing a file, it says which to download and how, with each move's link (`url` in `needs`: a Mixamo search for it - the user clicks, sees it play, downloads). A new
  preset is the same file for other moves: `needs` (the Mixamo name, file and `url`), `steps` (`blade`/`ground`/`plant`/`link`, as
  `run_steps` reads them), `actions`.
- **A combo from Mixamo, step by step** (how the rain girl's downward cut -> backhand was made; each step free but the last):
  1. On mixamo.com (free, an Adobe account), Animations: two moves of one set - `Standing Melee Attack Downward`, `Standing Melee
     Attack Backhand` - each downloaded as Format FBX Binary (.fbx), Frames per Second 30, Skin Without Skin (with works too), Keyframe
     Reduction none. **SpriteCast comes with no moves** - the user downloads them (Mixamo's may be used, not handed on); say so plainly
     (the user: "they'll think it's a preset"). Keep the files out of any public repository.
  2. Onto the rig, one clip each: `addclip.py CHAR.json "Standing Melee Attack Downward.fbx" downward` (and `backhand`); give the spec
     the `"rig_glb"` each prints, so the next works on it.
  3. Feet on the ground: `motion.py ground CHAR.json downward backhand`.
  4. A sword, not an axe (if it was made for one): `motion.py blade CHAR.json downward --stroke 0.75-1.25` - the stroke from when the
     hand is fastest; then `ground` again (the bend changed).
  5. Decide what each action shows (`"t0"`, `"t1"`, `"frames"`: the downward cut 0.35-1.40 s, 8 frames), then link the next one from
     the LAST frame shown: `motion.py link CHAR.json downward@1.40 backhand@0.3-2.0 backhand_after --blend 0.4`, and `ground` it.
  6. Look at it whole: `motion.py join CHAR.json combo downward:0:1.40 backhand_after:0:1.40`, an action `{"name": "combo", "clip":
     "combo", "t0": 0, "t1": 2.79, "frames": 67}`, `charpipe.py render --only combo`, and the frames played at 24 a second.
  7. The actions with `"hold"`, `"trail": "water"` (and `"trail_reach": 2` for water that carries), `charpipe.py render --only
     downward,backhand_after`, then `pixelart.py` - the paid step: say the cost it prints and wait for a yes. ~$0.65 a facing for each
     8-frame move held out this far (a sheet a frame); Rain Girl's two moves in four facings came to about $4.5.
  8. By hand, free: `pixeledit.py CHAR.json` with "3D shapes over" - a held thing drawn white or missing shows as red where it should be.
  9. Into the game - the set has ITS OWN frame size and feet (its bigger canvas): place it by its feet, not the walk's; lay the water's
     cells in a grid (a 24-cell row at reach 2 was 9168 px, past what a phone draws); a move's FIRST water cell can sit where the tip was
     a third of a frame before - off the umbrella (the user took it for the umbrella poking out): blank it if it floats free.
  10. Playing it: a press during the first move queues the second, which starts the moment the first ends (from its last pose - step 5);
     each move its own hit frames and reach (Rain Girl: the cut long and narrow ahead, 155 px, 42 degrees each side, frames 4-6; the
     backhand short and all round, 118 px, frames 4-7, a monster thrown away from her). The finisher's flourish from `fxpack.py`:
     `melee/spin-slash` and `impacts/shockwave-ring` at 2x - as wide as its reach - the ring round her cut at its middle, far half behind
     her; `water/bubble-burst` where the water strikes (round: no way it points). Rain Girl's game.js (`MOVES`, `swing()`, `fx()`) is
     the whole of it, in about 60 lines.
- The held thing points along the hand bone as the renderer holds it (the action's `"grip"`, or the kind's default).
- Never put a Mixamo file - or a rig with its motion in it - in a public repository: the moves may be used, not handed on.

## Seeing animations joined: `loop`
`charpipe.py loop SPEC --only walk,ready,slash,recover --facing south-east` (free) plays the finished frames of those animations one
after another as one GIF - `out/loop-<facing>.gif`, each frame with its 3D shadow and, for an action with `"trail"`, its effect - to see
the joins before anything is drawn again. A looping animation plays from its second frame round to its first (the pose a `between`
leaves from and comes back to); a one-shot once; each at its own pace (in-betweens 0.12 s a frame). It needs the frames finished
(`frames/`), not packed. The rain girl's walk → stance → slash → back up was looked at this way, and frame 5's floating fist found.

## One frame wrong: `frame_words`, and `frame` to draw it alone
When one frame of an action comes out wrong and the render is right, say what the render cannot show, for that frame only, and draw
that frame alone:

    "frame_words": {"5@south-east": "the LEFT hand grips the shaft beside the right fist, MOSTLY HIDDEN BEHIND HER HEAD: ..."}
    charpipe.py frame SPEC --only slash --facing south-east --frame 5 --yes        (~$0.08; the frame from 1)

A held thing of the body's own colour, pointing at the viewer, is left out: a yellow umbrella lying foreshortened across a yellow raincoat's shoulder was drawn as a bare handle in a wind-up's two frames; said in `frame_words` ("THE UMBRELLA IS THERE AND MUST BE DRAWN: it runs from her fist down and toward the viewer across her shoulder ... in front of the coat with its own clear outline") both came back with it, each drawn alone.
`frame_words` keys are the frame (from 1), or `<frame>@<facing>`; the sentence goes into that cell of the sheet's prompt (and of a frame
drawn alone, and of the pixel sheets - `pixelart.py --again <sheet>` draws that sheet anew). `frame` draws the one frame with its render in the second cell of an empty sheet, at the action's scale and beside its
drawn sheet for the style; `finish` then uses it in place of the sheet's cell (draw/<action>-<facing>-single-<k>.png; the one before is
kept as .before.png).

**A hand the head hides - the image model pulls it into sight.** The rain girl's slash, south-east frame 5: both hands up on the
umbrella, the left one (in the clip, a little off the shaft) behind her head. Drawn five times - the sheet again, alone, the fist
described ("closed round the shaft, the thumb over it"), with 2.5 and with 2.6, and with the 3D hand moved onto the shaft - and every
time the left fist sat ON TOP of the shaft, above the hair, as if put there to be seen. Told instead that the hand is mostly hidden
behind her head ("only the knuckles show over the shaft; do not draw the whole fist, do not move it up to show it"), 2.5 drew it right
the first time, from the clip's own render. The same habit as a snowball in a hand behind the head drawn at the chest
(reference/pixel.md). Moving the 3D hand did not help: from that camera a hand on the shaft is behind the head, and the drawing still
pulled it up.

## A swing's effect: `"trail"` - free, nothing drawn
`"trail"` in an action whose hand holds something (`{"name": "slash", "hold": "umbrella", "trail": "water"}`) gives the swing an effect:
a sprite of its own that the game lays OVER the body at the same moment. The body's frames are not touched and nothing is paid: an
action that is already drawn gets its effect with `render --only slash` and `pack`.

- **How.** The rig knows where the held thing's far end is at every moment; `render` reads it 200 times through the action (the PATH),
  finds the STROKE (the longest stretch over half its top speed - the swing, not the wind-up), and along it draws a BAND and lets go
  PIECES. A piece is born once and flies on - carried a little by the swing, the far end fastest, flung outward, falling or rising,
  turning - so a drop in one frame is the same drop further on in the next. The body and the held thing hide what is behind them.
- **The looks** (`skills/spritecast/effects/effects.json`): `plain` (a white band; `"color"`), `wind` (thin pale streaks), `water`,
  `fire`, `drops`, `flames`, `leaves`, `greenleaves`, `petals`, `snow`, `sparkle`. A name alone, or `{"style": "leaves", ...}` with
  anything of that look changed (`"alpha"`, `"span"`: how long a band, in frames; `"when": "always"`: the wind-up too;
  `"stroke": [t0, t1]`: the swing's own seconds of the clip, when the fastest stretch is not the swing - a cut laid over a jump
  (`motion.py layer`) went back up to its wind-up faster than it cut, and the water came off the return;
  `"frames_x"`; `"pieces"`: the whole list). A new look is one more entry in that file.
- **`water` and `fire` are ONE BODY, not loose pieces** (the user: "don't water and fire move as a mass?"). Their pieces are soft round
  weights added into a field, and only where the field passes a level is anything shown: close together they are one sheet, a neck
  forms as they part, and it breaks - water goes sheet → strings → drops, with mist rising after it; flame is white-yellow where
  much and new, through orange to a red rim that darkens and goes as it cools, with ash drifting up. `drops` and `flames` are the
  same two as loose pieces.
- **More effect frames than body frames.** `water` has `"frames_x": 3`, `fire` and the piece looks 2: that many effect cells to each body frame, played at
  that many times the fps over the same body frame. At one to one a sheet was whole in one frame and drops in the next - the tearing was
  never seen. The cells sit AROUND the body frame's moment, not after it (water's three: a third of a frame before, on it, a third
  after): the drawing holds one pose for all of them, and cells only after it had the water down at her feet while the drawn umbrella
  was still up - a fast swing's tip had gone on two thirds of a frame. Around it, the water is at most a third away, and behind the
  tip as often as ahead. A swing so fast that this still shows: an in-between frame there (`between`) is the real fix.
- **How far the water shows: `"trail_reach"`** in the action (1 by default; Rain Girl's combo 2 - the user: "twice as far"). The drops a
  swing throws fly on and on; in the pixel set they fade out with the distance from the figure, gone by 1.15 x reach of its height
  from its middle - never cut in a straight line at the frame's edge (the user saw the squares). The render's frame grows with it
  (1024 px x reach; 768 before for an action with a trail), and `render` says when a trail still runs off it. A game that packs the
  water's cells in one long row should lay them in a grid: at reach 2 a row was 9168 px, past the 8192 a phone draws. `export.py` does:
  as near square as they go, over several sheets where one would pass 4096 px a side (the side view's backhand: 24 cells of 1152 x 652,
  18 MP - no 4096 x 4096 texture holds it - now two sheets of 3456 x 2608); Godot, Phaser and Unity read them in order (Unity's
  importer slices each sheet and joins them into the one clip: the backhand's effect, 24 sprites from 2 sheets). Aseprite takes the
  cells from the strip.
  `character.json`: `"trail": {<facing>: {"file", "frame", "offset", "frames", "per_frame"}}` in the action - the cell
  size, its top-left from the body frame's top-left, how many cells, and how many of them to each body frame. `export.py` carries it
  into every engine as a third sprite.
- **Your own pieces**: `"image": "petals.png"` (beside the spec) - a strip of square cells, each a variant, drawn pointing up - in
  place of the look's first piece. The built-in ones are drawn from shapes by `effects/make_pieces.py`.
- **Any held thing.** The umbrella has its far end written down; for another thing it is the far corner of its box along its longest
  side. Only an action with a `hold` has a path.
- **An action drawn before 0.14 and rendered again**: the hand now closes on the handle, so the render's held thing sits a little
  off the one drawn then, and the effect with it. Small, and only on old sets.
- **Not checked**: `"image"` with a user's own strip; a thing other than the umbrella.

## A held thing: say it part by part

The umbrella's shaft and tip are silver; `"shaft": "#6b4423"` and `"tip": "#ffffff"` in its `hold` give them other colours (the render's
only - the built-in sentence still says silver: give your own `"words"` with them). Tried on the pixel walk to see whether a dark shaft
helps the image model find a yellow umbrella against a yellow coat: one sheet came out better, which a second drawing of the same might
have done too - not shown to help.

In pixel art (`pixelart.py`) these colours are kept frame to frame: each part of the held thing takes the same tones in every
frame, from `"handle"`/`"shaft"`/`"tip"`, or from one frame the user picks, `"colours_from": "carry-south-east-1"`; `"as_drawn"`
leaves frames as drawn - reference/pixel.md, "A held thing in the same colours in every frame".

The built-in sentence for an umbrella names its three parts and their colours; for anything else held (`"hold": {"kind": ...}`), or when a
drawing gets a part wrong, give the sentence yourself in the spec: `"hold": {"kind": "sword", "words": "In the RIGHT hand: ..."}`.

What goes wrong, and where: the parts **nearest the hand and the body** - a handle, a hilt, a grip, the first stretch of a shaft. They
are a few pixels of the render, half covered by fingers and lying against the coat, so the image model fills them in from habit: a shaft
silver on one sheet and brown on the next, a handle grown longer, two fists drawn together with the gap between them painted as handle.
The far end (a blade, a canopy, a tip) is big, clear of the body, and comes out right.

So write, in order from the hand outward: each part, its material and colour, how long it is ("exactly as long as that cell's render shows
it"), what it must NOT become ("bare metal: never brown, never wrapped"), and where the hands are ("as far apart as the render has them -
do not move them together"). One sheet of the rain girl's slash drawn with such a sentence had the handle, the shaft and the hands as the
render in all four frames; with "in the colour the render has" two of the four were wrong.

To redraw only what was wrong: move the sheets aside (`<character>/draw/<action>-<facing>-drawn-<n>.png`) and run
`charpipe.py draw CHAR.json --only <action>` - it draws what is missing (the cost is printed first) and finishes the strips.
A colour that still differs between frames can be evened without drawing: tell the user it can be made ONE colour (the stick all brown)
but not put where the drawing has no room for it (a silver shaft between two fists drawn touching).

## After `draw`: drawing sheets again
`finish` names the sheets with a frame fitting its render under `redo_below` (0.75). Each round is paid and asked for:
1. Show the user the renders beside the drawn frames for those facings (the overlap of each frame on it), and the cost.
2. `redraw --yes`: those sheets drawn again (up to twice each); each keeps whichever drawing fits better.
3. **Stop after a sheet's second try and show the result.** Only if the user says so, `redraw --yes` again: a facing still under the
   line is mixed with its mirror pair (east/west, north-east/north-west, south-east/south-west; not in a side view - there east's low
   frames are drawn alone: west is its mirror, and not rendered) - the pair drawn too if it was being
   flipped (2 sheets, ~$0.22; free if drawn already), then each frame the better of its own drawing and the other's flipped. South and
   north, which have no pair, get their low frames drawn one at a time (~$0.11 each, once each). Before agreeing to a mix on a design
   that is not the same on both sides, check that what is on one side stays on that side.

A low score is not always a bad drawing: lay the render's outline over the frame and look. For an animal the size is matched by overlap
per sheet (its height is mostly the tail), so a low score there is the drawing itself - a head turned another way, legs bunched.

## Actions: the head, `redraw`, the prompt
- **The head.** The walk's prompt keeps the eyes ahead and the chin level (a rig's walk looks down). For an action whose head bows or
  turns with the motion - a slash, a crouch, a shot aimed low - `"head": "as_render"` (the slash has it by default): drawn bowed and
  turned exactly as the render, in the facings where the face shows (south, south-east, south-west); side and back views keep the
  walk's words. Measured on the slash: the face-on facings went from 0.786 to 0.837 overlap (17 → 20 of 24 frames passing); the side
  and back views did slightly worse with it (0.791 → 0.771).
- **What `redraw` does with a held thing.** The render's held thing is rendered apart, so a frame is wrong when the drawing covers under
  half of where it sticks out of the body (`HELD_MIN`), or more than 8 % of the drawing lies well off the render's outline (`EXTRA_MAX`:
  the umbrella on the other side, or raised where the render has it low - seen from behind the model swaps the hands). Those are drawn
  again by themselves (twice at most, the better kept). A frame only a little off (a lower overlap, the pose right) is listed, not
  redrawn: show it beside its render and let the user choose; `redraw --low` redraws those too. A thin thing drawn a few degrees off
  misses its render's pixels: one pointing the same way (within 25°) from the same side passes.
- **The prompt** names the action only (`words`) and leaves the pose to the renders (`pose`: each cell one moment, the arm and the held
  thing where its render has them) - moves spelled out ("raise it overhead, swing it down") had it drawn overhead where the render has
  it at the side. Each cell gets the held thing's place in its render; where the body hides it the cell says so, and the checks count
  only the part that shows.
- Measured: the rain girl's run and jump fit at 0.78+ in every frame on the first drawing; the slash's lower frames are mostly deep bends
  drawn a touch upright - fine in motion: show them beside their renders and let the user keep them or redraw.
