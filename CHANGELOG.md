# Changelog

What changed in each version. The version is the one in `.claude-plugin/plugin.json`; Claude Code offers an update when it goes up.
Changes made because of a report or a request are marked *(feedback)*.

## Unreleased

- The README is put **character-first**: what you can make (a walk, actions, pixel art, animals, sitting) at the top, props below;
  the pixel sprites are in `examples/rain_girl/pixel`. *(feedback)*
- **Pixel-art sprites** (`pixelart.py`, [reference/pixel.md](skills/spritecast/reference/pixel.md)): a character as real pixel art
  about 96 px tall, from its 3D renders - the renders pixelized into a guide, redrawn as pixel art by the image model, read back
  onto the grid it was drawn on, sized and placed by the render, cleaned by rule (stray white sorted out by what the guide has
  there, the outline closed), with each frame's 3D shadow. One command; it prints the plan and the cost before it spends. *(feedback)*
- **Pixel sprites fixed by hand** (`pixeledit.py`): a page in the browser, frame by frame - erase a patch of left-over white with a
  click, draw, change a colour, move a selection, copy a good face from one frame into another or into all of them; the edits are
  kept and laid on again by every later run. It and the run say how it was made: the AI's time, and the frames and pixels by hand. The run
  also reviews every frame (pose against the render, the held thing) and `--redraw` draws the marked sheets again, keeping the
  better. *(feedback)*
- **Something thrown**: a held thing can be let go (`"hold": {"until": "auto"}`) - a snowball, drawn in a colour that shows on white
  paper (`"color"`) and turned to its real one after (`"final"`); the thing's own sprites, and when, where and which way it leaves
  the hand in `pixel.json`. *(feedback)*
- **An animation from an FBX** (`addclip.py`): a Mixamo clip put into a copy of the rig as one more action, no credits. *(feedback)*

## 0.9.0 — 2026-11-10

- **Sharper at any size**: characters are rendered and fitted at 1024 px (`"render_px"`; it was 512, which kept about half of what
  was drawn), so `pack --px` gives sharp sets bigger than 256 too. Nothing is redrawn: a project rendered at 512 before keeps that
  until `render_px` is set and `render` + `finish` run again. *(feedback)*
- `finish` about twice as fast, with exactly the same frames: the head-size search compares every shift at once in whole numbers
  (it resized the head 2 million times), and the shadows' gap closing uses a separable filter.

## 0.8.0 — 2026-11-10

- **More actions**: `"actions"` in a character's spec - run, jump and a slash (Tripo's presets, or any clip in your own rig), each
  rendered, drawn and finished in 8 facings like the walk, in its own strips. `"hold"` puts something built from shapes in the right
  hand (a closed umbrella) for the slash, rendered on a wider canvas so it never runs off the frame; such frames are fitted by
  outline overlap without steadying the head (that warped the umbrella crossing it). `"head": "as_render"` (the slash's default)
  draws the head bowed as the render instead of the walk's eyes-ahead, and `redraw` covers the actions: a weapon drawn in the wrong
  place (on the other side, or raised where the render has it low) is redrawn by itself; a frame only a little off is left for you to
  look at (`redraw --low` redraws it too). *(feedback)*
- The action's prompt names it and leaves the pose to the renders: a slash spelled out ("raise it overhead, swing it down") had
  the umbrella drawn overhead where the render holds it at the side. Each cell is told where the held thing is in its render, and
  when the body hides it (seen from behind) not to draw it; the frame rules no longer say "nothing held" for an action that holds
  something. The weapon checks count only the part that shows and pass a thin thing drawn a few degrees off. *(feedback)*
- The rain girl example runs, jumps and slashes (`docs/actions.gif`).
- **Any frame size**, asked for by many: `pack --px 64` makes another set at that height from the same drawings (strips, shadows,
  `character.json` in `out-64px/`, `out/` untouched; `docs/actions-small.gif` shows 64 and 32 px). `pack` on its own now keeps the
  report in `character.json` (it had written an empty one). *(feedback)*

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
- The seated examples' front pieces were then touched up by hand (`"front_by": "painted by hand"` in their seat.json), and the girl moved on the pew and the dining chair's back.
- On the touch-up page a seated character is **dragged to where they should sit**; letting go re-makes the seat there. *(feedback)*
- A **polygon** on the touch-up page (P): click the corners, close it, and it is filled in the colour you are painting (or erased). *(feedback)*
- Curved blocks (`"arc"`) for round things like a curved bench.
- **API keys in the plugin's settings** (`userConfig`): Claude Code asks for them when SpriteCast is enabled and keeps them in the
  system's credential store; a session-start hook hands them to the scripts. A key in the environment still works when the settings
  have none.
- The skill reads lighter: sitting, seats and the touch-up page have their own reference files, SKILL.md says to run the touch-up
  page in the background, and the skill's description names walking, sitting, seats and fixing cut-outs so it is picked for them.
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
