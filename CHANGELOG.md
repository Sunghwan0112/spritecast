# Changelog

What changed in each version. The version is the one in `.claude-plugin/plugin.json`; Claude Code offers an update when it goes up.
Changes made because of a report or a request are marked *(feedback)*.

## 0.7.0 — 2026-11-09

- **Touch-up page** (`touchup.py`): fix finished props and character frames by hand in the browser - red clears (paper left between
  the limbs, a halo, a speck), green brings pixels back from the drawing itself (a white shirt or shoe the cut-out took for the paper),
  blue paints a prop's **front piece** (`sprite-front.png`, `"front"` in `sprite.json`) so a character can stand inside an arch, a
  gazebo or a chair's armrests. Saved as you paint; `--apply` lays them on, and `finish` lays them on again by itself. *(feedback)*
- **Sitting** (`charpipe.py sit`): the rig bent into sitting in 8 facings (free), then drawn like the standing views (`--draw`, ~$0.22)
  → `out/sit-<facing>.png` with each facing's seat point, seat height and 3D shadow. The rain girl example has them.
- **Seats** (`seat.py`): a seated character put on a finished prop - the seat's height and facing found, sat back until the knees
  reach the seat's edge - and the prop's front piece for them worked out from the two heights, no painting. Examples: the rain girl on
  the four turns of the armchair, the Tripo armchair, and seats from the author's game (a dining chair from both sides, a church pew,
  a curved park bench from both sides - `examples/seated/`).
- On the touch-up page a seated character is **dragged to where they should sit**; letting go re-makes the seat there. *(feedback)*
- Curved blocks (`"arc"`) for round things like a curved bench.
- `charpipe.py pack`: the strips made again from frames/ without finishing again.
- **The cut-out no longer falls back quietly**: without onnxruntime, `finish` stops and says so, instead of cutting by the paper's
  white - a run from another Python had cut a white bikini and a grey knit dress that way, leaving paper between the arms. *(feedback)*
- Props keep their drawing laid like the sprite (`sprite-src.png`) for the touch-up's green.

## 0.6.0 — 2026-11-05

- **Renamed from iso-sprite to SpriteCast** (`spritecast`). Install with `claude plugin install spritecast@spritecast`.
- The cache folder is now `~/.cache/spritecast`, and the settings are `SPRITECAST_MODEL`, `SPRITECAST_QUALITY`, `SPRITECAST_KEY` and `SPRITECAST_KEY_MODEL`.
- The README opens with what it is (an isometric sprite generator for Claude Code). It has a roadmap and a way to send feedback.
- The examples' 3D models are credited to the Tripo API.
- The repository history is smaller (37 MB, was 125 MB): old versions of pictures were removed; every commit and every version of the code is kept.

## 0.5.0 — 2026-11-03 to 11-04

- **Four-legged animals** (`"kind": "animal"`): no bought rig; the skeleton is found from the 3D model itself. The tabby cat example.
- **Every facing drawn** by default (`"mirror": false`); a facing is flipped from its pair only when redrawing leaves it low.
- **Redraw rules**: a sheet with a frame that fits its render under `redo_below` (0.75) is drawn again, up to twice, and the better
  drawing is kept; a facing still low is settled frame by frame against its mirror pair (`"mix"`).
- **Heads sized to the 3D model** in every facing, and each sheet's whole figure sized first, so heads no longer grow and shrink between
  sheets. The crown is found below ears and antennae.
- Thin things on the head (headbands, ears, antennae) drawn as the turnaround shows them, not as the rough 3D model does.
- An anchor on the soles; flipped frames moved onto their own render; drawings refused by the image model's safety check are retried,
  then skipped with a note.
- `facecheck` (MediaPipe face landmarks): match one outfit's head size to another's.
- A 3D-only option: the renders themselves as the frames, no drawing.
- The preview makes `walk-all.mp4` (every facing walking).

## 0.4.0 — 2026-11-03

- Ready for the plugin directory: the examples' raw drawings stored as WebP (57 → 24 MiB; the finished results within a pixel).
- A README section on what is sent where and what is downloaded.
- Chromium is fetched only with `doctor.py --fix --browser`; an installed Chrome or Edge is used otherwise.
- The Tripo example's model included, so the free trial runs it too.
- The "GPT alone vs the 3D guide" comparison GIF, and the Korean README's pictures with Korean labels.

## 0.3.0 — 2026-11-03

- First version: game props and walking characters at their real size and the exact camera angle, drawn in your art style —
  a 3D guide rendered with your game's camera, redrawn by an image model, cut out and laid back on the guide, with a baked shadow and an
  anchor for your engine.
