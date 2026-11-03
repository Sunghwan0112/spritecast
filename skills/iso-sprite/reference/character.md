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
| `draw` | 4 frames a call on one sheet; the front first, every other sheet given it; a walk's second sheet given its first | ~$0.10 a sheet, 18 sheets ≈ $2 |
| `finish` | each frame cut out (its cell cut wider), fitted onto its render (one upper-body size per facing, the legs to the render's feet), heads steadied, edges cleaned; strips and a shadow per frame | free |
| `preview` | every frame on one sheet, a GIF per facing | free |

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
| `rig_glb` | skip `turnaround`/`model`/`rig`: your own rigged GLB with clips named `walk` and `idle` |
| `head_up` | degrees the head is raised in the renders (24) |
| `white_shoes` | true for white (or very light) shoes: small holes inside the outline round the feet are filled after the AI cut-out (a lace or a sole the segmenter left out). Off otherwise - a heel's straps or a boot's laces have real gaps |
| `shoulder_up` | degrees each collar bone is turned up in the renders (15): squares the shoulders Tripo's rig slopes - see below; 16 for a broad-shouldered man, 0 to leave them |
| `shoulder_wide` | how far out the collar and arm bones are set (1.05; 1.1 for a man); small on its own |
| `pitch` | camera degrees down (30 = 2:1 isometric) |
| `frames` | walk frames (8) |
| `walk` / `idle` | clip names and times: `{"clip": "walk", "t0": 0, "t1": 1.1835}` (one stride of Tripo's walk), `{"clip": "idle", "t": 0}` |
| `neck` | where the neck is, as a share of the figure's height from the top (0.16), for steadying the heads |
| `frame_px` | output frame height (256) |
| `light` | `"right"` (default: shadows fall up and to the left) or `"left"`, as for props |
| `shadow` | `"3d"` (default): each frame's shadow from the 3D body; `"none"` leaves them out |

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
  too). The lite model by default (224 MB, fetched once into ~/.cache/iso-sprite/models, ~3 s a frame on a CPU): within a pixel of
  the full one's outline (99.3-99.8 % overlap on the drawn sheets, the white sneakers too); `ISO_SPRITE_KEY_MODEL=general` (973 MB)
  for the full one. Of the models tried, ISNet left parts of the shoes half see-through and U2Net blurred the edge.
  `ISO_SPRITE_KEY=white` brings the old key back; without onnxruntime it is used anyway.
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
- **Back views**: the prompt says to show the back of the head and the back of the clothes, or a face can appear on a back view.
- `finish` prints each walk's overlap with its renders. Under ~0.7, look at that facing and redraw it:
  `draw --only <facing> --again --yes`.
