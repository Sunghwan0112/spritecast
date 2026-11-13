# Changelog

What changed in each version. The version is the one in `.claude-plugin/plugin.json`; Claude Code offers an update when it goes up.
Changes made because of a report or a request are marked *(feedback)*.

## 0.14.1 — 2026-11-13

- `SPRITECAST_MODEL=gpt-image-2.6-sunburst` draws with OpenAI's newer image model. **2.5 stays the default**: tried on seven
  sheets, 2.6 drew a held thing's colours and a walk's two halves better, a second half's arm worse (twice running), and pixel art
  no better ([reference/tips.md](skills/spritecast/reference/tips.md)).
- The left-hand example's west walk: its two halves had come out 6 % apart in size and the head stepped between them (26 px of
  1024). Its first half is drawn again; the step is 14 px, not gone.

## 0.14.0 — 2026-11-12

- **A character that is not the same on both sides.** `"mirror": "never"` in the spec: nothing is ever flipped from its pair - not by
  `redraw` either, which until now settled a facing that stayed low with its pair's frames flipped. Such a facing now gets its low
  frames drawn alone. *(feedback)*
- **Something carried all the time**: `"hold": {"kind": "pistol", "hand": "left"}` in the spec itself puts it in the hand through the
  walk, the standing views and every action; the drawing is told which hand and where each render has it, and `finish` checks it is
  there. `hand` works for an action's own `hold` too. A thing already in your rigged model: `{"in_model": true, "words": "..."}`.
  A `pistol` and a `watergun` are built in beside the umbrella. *(feedback)*
- **The hand closes on what it holds**, whatever it is: the handle goes into the fist, the four fingers bend round one side of it
  (joints together, in a finger's proportions, until they touch - not through it) and the thumb round the other. `render` prints
  each finger's bends and how far its tip is off the handle, and saves `render/hand-<name>.png`: the hand from all round, to look at
  before anything is drawn. The guns' grips are thin enough to get a hand round. *(feedback)*

## 0.13.0 — 2026-11-12

- **Palettes by name**: 15 come with the skill (`--palette pico8`, `gameboy`, `nes`, `c64`, `db32`, `endesga32`...), and
  `--palette list` shows them. Your own palette can be any file Aseprite reads: `.png` `.gif` `.bmp` `.pcx`, `.hex`, `.gpl`, `.pal`,
  `.act`, `.col`, `.aseprite`. *(feedback)*
- The pixel editor: **any colour added to the palette**, and **frames copied, deleted and moved** - a copy of a frame to draw an
  in-between on, a frame taken out, the order changed. The shadow strip and `pixel.json` follow, and every later build lays the
  same frames out again. *(feedback)*

## 0.12.0 — 2026-11-12

- **How many colours a pixel set has is yours to say**: `--colours N` (8 at least) on `pixelart.py` and `proppixel.py`, and
  `--palette FILE` for a palette you already have (a `.png` of it, or one hex colour a line). Free: nothing is drawn again.
  *(feedback)*

## 0.11.0 — 2026-11-12

- The pixel editor shows **the 3D render beside the sprite, or faint under it**, and opens a prop's views like a character's frames.
  *(feedback)*
- **Props as pixel art** (`proppixel.py`): a prop's 3D guide pixelized, redrawn and read back like a character's frame, at the pixel
  character's scale - from every side when the guide is a 3D model. New example: `examples/ramen_cart`, a street cart from four sides.
  The grid reading is now a module of its own (`pixelgrid.py`), shared by characters and props. *(feedback)*
- The rain girl's umbrella slash drawn again (seven facings' second halves) with the umbrella said part by part. *(feedback)*
- **A prop's 3D model keeps its own proportions**: it is made as tall as the blocks say with one scale, and the footprint it covers is
  reported. It was pressed into the blocks' box axis by axis, which squeezed a model whose shape the blocks only guessed (a cart's
  wheels came out oval). `"shape": "box"` is the old way. *(feedback)*
- **A held thing is described part by part**, most carefully at the hand: the umbrella's built-in sentence names its handle, its silver
  shaft and its canopy, with what each must not become. Told only "as the render shows it", the shaft changed colour between sheets and
  two fists were drawn together. `"hold": {"words": ...}` gives the sentence for anything else. *(feedback)*
- The README's first picture: GPT alone in one direction against the same character walking in eight on the game's floor, each with
  its shadow, and as pixel art. *(feedback)*
- **A held thing the figure hides** (a ball in the far hand, or in a hand raised behind a big head): the image model is told so, cell by
  cell, instead of "the ball is in the hand" - it had drawn the ball at the chest; the review counts only what the camera sees of it,
  and marks one drawn where it is hidden. *(feedback)*
- The banner: the title is under snow until the small character's snowball knocks it off. *(feedback)*
- **Small sizes.** 64 px works for a character designed small (about three heads tall, its own 3D model). **The image model is never
  asked for less than 64**: `pixelart.py --px 32` draws at 64 and `pixelsmall.py` makes the smaller set from it (strips, shadows,
  release data), free. 32 px asked for directly was tried four ways and is not offered. *(feedback)*
- A new example, `examples/rain_chibi`: the rain girl designed three heads tall, walking and throwing in eight facings at 64 px, and the
  32-px set made from it. *(feedback)*
- `addclip.py --clear-head DEG`: for a big-headed character, a hand raised past the ear swings its arm outward instead of going into
  the head. *(feedback)*
- The rig step keeps the rig it has paid for: if the animations then fail (no credits left), the next run does not buy the rig again.
- The README's banner throws a snowball at the title. *(feedback)*

## 0.10.0 — 2026-11-11

- The skill now says in its description that it makes **pixel art, actions and thrown things**, so a request for pixel sprites
  reaches it.
- A pixel build from kept drawings is **about 1.8 times as fast** (64 frames: 88 s → 50 s; the sprites are the same to the byte), and
  `pixelart.py` lost the face options that were tried and not kept (`--face-patch`, `--heads`, `--hand-faces`, `--follow`).
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
