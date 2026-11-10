# Walking characters (`charpipe.py`)

An 8-direction walk and standing views from one illustration of the character. The image model can't keep a pose or a body
from frame to frame on its own, so the motion comes from a rigged 3D model. The model only draws over its renders.

Three OKs: `turnaround`, `3d` (= `model` + `rig` + `render`), `draw` (then `finish` + `preview` by themselves). The steps:

| step | what | cost |
|---|---|---|
| `turnaround` | front / right / back drawn from the illustration (A-pose, hair behind the shoulders); the left view mirrored from the right | ~$0.09 OpenAI |
| `model` | Tripo multiview-to-model from the four views (turned to face front for the rig); or Meshy multi-image-to-3D with `"modeler": "meshy"` | ~30 Tripo credits (+10 if it comes back uncoloured; or ~30 Meshy) |
| `rig` | Tripo: rig check, rig (mixamo bones), walk + idle retargeted in place; bone names fixed, the walk's hips put back, feet planted as modelled | ~45 Tripo credits |
| `render` | the walk (8 frames × 8 facings) and the idle (8 facings), the head raised `head_up`° (a rig's walk looks down); each with its 3D shadow (`-s.png`) | free |
| `draw` | 4 frames a call on one sheet; the front first, every other sheet given it; a walk's second sheet given its first; every facing drawn (`"mirror": true` flips the west side from the east) | ~$0.10 a sheet, 18 sheets ≈ $2 (12 ≈ $1.3 with `"mirror": true`) |
| `finish` | each frame cut out (its cell cut wider), fitted onto its render (one upper-body size per sheet, the legs to the render's feet), heads steadied within a facing and sized to the 3D model's in every facing, `head_fit` applied, edges cleaned; strips and a shadow per frame | free |
| `preview` | every frame on one sheet, a GIF per facing, and every facing walking at once in `walk-all.mp4` (with ffmpeg) | free |
| actions | (optional) `"actions"` in the spec: each rendered, drawn and finished like the walk → `out/<name>-<facing>.png`, `"actions"` in `character.json`; `rig` asks Tripo for the presets (run, jump, slash, shoot, dive, climb, fall, hurt, turn; three beside walk and idle), your own rig gives any clip; `"hold"` puts a shape-built thing (an umbrella) in the right hand; `"head": "as_render"` draws the head bowed and turned as the render (the slash's default - the walk's "eyes ahead" lifted it); `redraw` covers actions: a held thing in the wrong place (checked against the render's held thing alone) is redrawn by itself, a frame only a little off is listed for the user (`--low` redraws it too) | ~10 Tripo credits and ~$1.8 an action |
| `sit` | (optional) the rig seated in 8 facings (`render/sit-*`), then with `--draw` drawn and finished → `out/sit-<facing>.png`, `"sit"` in `character.json` (`frame`, and per facing `file`, `seat`, `seat_height`, `shadow`) | free; `--draw` ~$0.22 |
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
| `mirror` | `false` (default): all eight drawn; a facing flipped only when `redraw` mixes a pair that stayed low (each frame the better of its own and its pair's flipped). `true`: west, north-west and south-west flipped from east, north-east and south-east - 6 of the 16 walk sheets not drawn (~$0.66 less), only for a design that is the same on both sides (not hair over one shoulder, a logo, a bag, one ear up); or a list of facings to flip from their pair, e.g. `["north-east"]`. A flipped facing is only as good as its pair (a raincoat girl's west flipped 0.75-0.80, drawn 0.83-0.93). Shadows stay each facing's own |
| `kind` | `"person"` (default) or `"animal"`: a four-legged animal - no rig bought; its skeleton is found from the mesh and it walks in a cat's or a dog's gait (see Animals) |
| `model_glb` | an animal: your own static model in place of `3d` |
| `rig_glb` | skip `turnaround`/`model`/`rig`: your own rigged GLB with clips named `walk` and `idle` |
| `head_up` | degrees the head is raised in the renders (24) |
| `white_shoes` | true for white (or very light) shoes: small holes inside the outline round the feet are filled after the AI cut-out (a lace or a sole the segmenter left out). Off otherwise - a heel's straps or a boot's laces have real gaps |
| `shoulder_up` | degrees each collar bone is turned up in the renders (15): squares the shoulders Tripo's rig slopes - see below; 16 for a broad-shouldered man, 0 to leave them |
| `shoulder_wide` | how far out the collar and arm bones are set (1.05; 1.1 for a man); small on its own |
| `pitch` | camera degrees down (30 = 2:1 isometric) |
| `frames` | walk frames (8) |
| `walk` / `idle` | clip names and times: `{"clip": "walk", "t0": 0, "t1": 1.1835}` (one stride of Tripo's walk), `{"clip": "idle", "t": 0}` |
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
(solid black in alpha - draw at ~30 % under everything), `character.json` (frame size, anchor between the feet as a fraction of the
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
  The orange cat's north-east, drawn twice at 0.63-0.70, flipped from north-west: 0.80-0.92 against its own renders.
- **`finish` again is quick**: each sheet's cells are cut out once and kept in `frames/cut/` by the sheet's name, cell and modification
  time, so after a `redraw` only the changed sheets are cut (the AI cut-out is ~3 s a cell on a CPU): the cat's first finish 211 s, the
  next with one sheet changed 28 s.

## Notes

The output has a shadow per frame from the 3D body (`out/shadows/`, offsets in `character.json`): tell the user to draw it at
~30 % under the sprites. If their game's other characters stand on the bottom of their shoes, set `"anchor": "soles"` (the default,
the 3D ground under the middle, stands 4-7 game px lower). **Several characters or outfits that should match** (the same person in
other clothes): `facecheck REF.json --with A.json,B.json` (free; needs mediapipe, Python 3.9-3.12) compares the face for the height,
facing by facing, by face landmarks - hair fools any outline measure - and `--apply` writes `head_fit` into their specs for `finish`. A rig rendered before this version has no `-s.png`: re-run `render` (free) before `finish`.
**The cut-out needs onnxruntime** (in requirements.txt): run every step with the `PYTHON=` doctor.py prints. A Python without it now
stops `finish` with a message instead of quietly cutting by the paper's white (which takes white clothes away and leaves paper between
the limbs); `SPRITECAST_KEY=white` cuts by white on purpose.
