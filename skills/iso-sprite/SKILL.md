---
name: iso-sprite
description: Make an isometric (2:1, true isometric), 3/4 top-down or front-view game prop, furniture or character sprite - single standing figures, or walking characters in 8 facings at its real size and exact angle - Claude builds a 3D block guide from the description, renders it with an isometric camera, an image model redraws it in a chosen art style, then it is cut out, fitted back on the guide, given a baked shadow and an anchor. Use when the user asks for an isometric prop, furniture, decoration or object sprite for a game.
license: MIT
compatibility: Claude Code (runs Python, Playwright and a local Chrome/Chromium on the user's machine; calls the OpenAI Images API with the user's own key)
---

# iso-sprite: isometric props at true scale

Image models draw isometric objects at slightly wrong angles and sizes. This skill gives the model a guide it cannot misread: the
object built from simple blocks at its real size, rendered with an exact 2:1 isometric camera. The model only redraws the guide in the
art style of a reference picture; the result is laid back onto the guide, so the angle, size and footprint stay exact.

Scripts: `${CLAUDE_SKILL_DIR}/scripts/isoprop.py` (steps `render`, `draw`, `finish`, `preview`). The spec format is in
[reference/spec.md](reference/spec.md); how to build good guides in [reference/tips.md](reference/tips.md) - read both before writing a spec.

## Setup (once)
1. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/doctor.py` (any Python 3.9+; `python` on Windows). It lists what is there and what each
   thing is for; its last line `PYTHON=<path>` is the interpreter to use for every script below. If it says "not ready", tell the user
   in a line what is missing and run it again with `--fix` (a venv in ~/.cache/iso-sprite/, the packages, about 10 s). No Chrome or Edge: ask first, then `--fix --browser`
   (Playwright's Chromium, ~150 MB). For characters add `--characters` (the 224 MB cut-out
   model, once). If it says the Python cannot make a venv, pass on its one-line fix.
2. Keys in the environment: `OPENAI_API_KEY` for `draw`, `TRIPO_API_KEY` for characters. Never ask the user to paste a key into the
   chat, never write it into a file, never print it.
3. **A first-time user, or "try it" / "체험":** `PYTHON isoprop.py try [--out DIR]` - free, no key: an example's guide rendered on
   their computer and finished with the drawing that came with it → show them `preview.png` and `render.png`, then offer to make
   their own prop.

## Making a prop
1. **Ask only what is missing**: what it is, its real size if it matters, which way it faces, the game's view (`camera`: 2:1
   isometric by default, true isometric, 3/4 top-down, front; or their own angle), whether it must turn (`views`), and the art style (a bundled style name
   - `cozy` - or the user's own reference picture: one finished prop in the look they want, ideally on a flat background).
2. **Write the spec** (`<name>.json` in the user's asset folder): footprint in metres, the blocks at real size, a `description` of the
   finished object (materials, colours, details), `facing`. Real-world sizes matter: look them up if unsure (a dining chair seat
   ~45 cm, a door 2.0-2.1 m).
3. **Render the guide (free)**: `python ${CLAUDE_SKILL_DIR}/scripts/isoprop.py render <spec>`. Look at `render.png` and
   `render-shadow.png` yourself, then show the user `render.png`. Fix the blocks until the shape, proportions and facing are right -
   this is the cheap step; everything after it follows the guide.
4. **Draw (paid)**: run `draw <spec>` without `--yes` first - it prints the model and the cost (about $0.07 at `high`). Tell the user
   the cost and wait for a yes before running it with `--yes`. With `views`, the first view is drawn first and the others follow it
   (about $0.09 each) - check the first before drawing the rest when it is a new design. Several props: say the total. Never redraw without asking
   (`--again`); a drawing that came out wrong is usually a guide or description problem - fix that first.
5. **Finish and check**: `finish <spec>` then `preview <spec>`. If `finish` warns (or `sprite.json` `fit.ok` is false), the model
   drew another angle or shape: it was NOT squeezed to fit. Tell the user, say why (often an angled style picture pulled it off the
   guide's view), fix the description, and ask before drawing again. Look at `preview.png`; show it to the user. If the drawing added or
   moved parts, adjust the description (say what must NOT be there) and ask before drawing again.
6. Hand over `sprite.png`, `shadow.png`, `sprite.json` (anchor, footprint corners, px per metre, shadow offset) and say how to place it
   in their engine: put the sprite so its anchor sits on the footprint's front corner; draw the shadow under all sprites.

## More detail with a 3D model (Tripo)
When the user wants more detail than blocks give (curves, carving, tapered legs) and has `TRIPO_API_KEY`: after the block guide is
right, `model <spec>` (prints the cost; ~20 Tripo credits, ~2 min; ask first, then `--yes`) makes a Tripo model from the description
and puts it in the spec at the blocks' real size (blocks → `blocks_draft`). Then `yaws <spec>` (free): look at yaws.png and set
`model.yaw` to the turn whose front faces where the blocks' did. Then render, show, draw as usual. Blocks alone are fine when the
arrangement matters more than detail.

## Characters
A standing person: a `character` spec (see spec.md) instead of blocks - a mannequin at their real height, one view per facing, the
first facing drawn first and the rest from it. Ask the height, the build, the facings (4 diagonals unless their game uses 8) and what
they wear. Look at every facing yourself before showing them: the outline check can't see a body turned the wrong way inside a right
outline (a back view with the front of the clothes). Redraw just that one: `draw <spec> --yes --again --only <facing>` (ask first).
Poses (`character.pose`): stand, wave, point, hold, arms-crossed, walk (a single mid-stride picture) - say the pose in the description too
("waving hello"). Anything else, or "raise the arm higher": write the angles (`{"base": ..., "arm": {...}}`, spec.md "Custom poses"),
render (free), look, adjust the numbers, and only then draw. Their shadows are cast from the finished drawing (hair, clothes), each pixel moved by the 3D guide's height under it, so every foot starts its own shadow; solid props keep the 3D shadow. No animation: for
walk cycles or other animation say this plugin doesn't make them (it needs a rigged 3D model and every frame
drawn to match).

## Walking characters
For an animated character (an 8-direction walk and standing views), use `${CLAUDE_SKILL_DIR}/scripts/charpipe.py` and read
[reference/character.md](reference/character.md) first. It needs one finished illustration of the character - facing front, standing straight, arms down, no pose (if theirs is posed, draw a neutral one from it first and show it) - and TRIPO_API_KEY besides OPENAI_API_KEY (or the user's own rigged GLB as `rig_glb`). Tripo makes the model
and the rig; with `"modeler": "meshy"` (and MESHY_API_KEY) Meshy makes the model (the author's way). Offer it when they have a Meshy account. Three steps, the user's OK before each:
`turnaround` (~$0.09; show it: both sides the same, nothing over the arms) → `3d` (~75 Tripo credits: model, rig, walk, then the
renders by themselves - show the front and a side: the face, not the back of the head) → `draw` (~$2, every facing drawn; when every facing is drawn,
`finish` and `preview` run by themselves - show `out/sheet.png` and a GIF). Every paid step prints its cost and needs `--yes`; ask the user for each one, and
never run the next paid step because the previous one "looked fine": a problem seen in one step is fixed there, not carried on.
**A four-legged animal** (a cat, a dog, a fox...): `"kind": "animal"` in the spec. The same three steps, but `3d` makes only the model
(~30 Tripo credits - no rig: Tripo's animal rig is poor, so the skeleton is found from the mesh and walked in a cat's gait). The
turnaround on all four legs, each leg clear, the tail out behind; clothes only snug ones (a vest, not a cape or a scarf). Check the
renders before `draw`: four legs, the head forward, the tail behind.
**Cheaper, softer** (`"draw": false`): no image model - the 3D renders are the frames; after `3d` it finishes by itself. Offer it
when cost matters more than detail (prototypes, background walkers); say it is softer (no drawn lines, a simpler face).
**Every facing is drawn by default** (`"mirror": false`): a flipped facing is only as good as its pair and swaps anything that isn't
the same on both sides (hair over one shoulder, a logo, a bag, one bunny ear up). Flipping comes in only by the rules below - a facing
still under `redo_below` after two redraws is mixed frame by frame with its flipped pair - or when the user asks to save ~$0.66 on a
design that is the same on both sides (`"mirror": true`, or a list such as `["north-east"]`). Before agreeing to a mix on a design
that isn't symmetrical, check that what is on one side stays on that side.
After `draw` (people and animals alike), `finish` names the sheets with a frame fitting its render under `redo_below` (0.75). Show the user `out/walk-all.mp4` (every facing walking at once; with ffmpeg) - a head that grows and shrinks, a
jumping frame or an odd stride shows there, not in the numbers. Look at the back views yourself for anything worn on the head (ears,
antennae, a bow): each on its side and, from behind, only its back (the 3D model makes such things rough).
Then, asking for each paid round:
1. Show the user the renders beside the drawn frames for those facings (the overlap of each frame on it), and the cost.
2. `redraw --yes`: those sheets drawn again (up to twice each); each keeps whichever drawing fits better.
3. **Stop after a sheet's second try and show the result** before going on. Only if the user says so, `redraw --yes` again: a facing
   still under the line is mixed with its mirror pair (east/west, north-east/north-west, south-east/south-west) - the pair drawn too if
   it was being flipped (2 sheets, ~$0.22; free if it's drawn already), then each frame of both the better of its own drawing and the
   other's flipped; south and north, which have no pair, get their low frames drawn one at a time (~$0.11 each, once each).
A low score is not always a bad drawing: lay the render's outline over the frame and look. For an animal the size is matched by overlap
per sheet (its height is mostly the tail), so a low score there is the drawing itself - a head turned another way, legs bunched.
The output has a shadow per frame from the 3D body (`out/shadows/`, offsets in `character.json`): tell the user to draw it at
~30 % under the sprites. If their game's other characters stand on the bottom of their shoes, set `"anchor": "soles"` (the default,
the 3D ground under the middle, stands 4-7 game px lower). **Several characters or outfits that should match** (the same person in
other clothes): `facecheck REF.json --with A.json,B.json` (free; needs mediapipe, Python 3.9-3.12) compares the face for the height,
facing by facing, by face landmarks - hair fools any outline measure - and `--apply` writes `head_fit` into their specs for `finish`. A rig rendered before this version has no `-s.png`: re-run `render` (free) before `finish`.

## Rules
- Spend money only after the user agreed to that amount. Show the free render before any paid step.
- Keep everything in the user's project folder; don't touch other files.
- Real brands, logos and characters from existing games or films: leave them out of descriptions (write "no logos").
- The output is the user's; the bundled `cozy` style picture may be used freely (MIT).
