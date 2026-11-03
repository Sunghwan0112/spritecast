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
   in a line what is missing and run it again with `--fix` (a venv in ~/.cache/iso-sprite/, the packages, about 10 s; a browser only
   if there is no Chrome or Edge - Playwright's Chromium, ~150 MB: ask first). For characters add `--characters` (the 224 MB cut-out
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
renders by themselves - show the front and a side: the face, not the back of the head) → `draw` (~$2; when every facing is drawn,
`finish` and `preview` run by themselves - show `out/sheet.png` and a GIF). Every paid step prints its cost and needs `--yes`; ask the user for each one, and
never run the next paid step because the previous one "looked fine": a problem seen in one step is fixed there, not carried on.
The output has a shadow per frame from the 3D body (`out/shadows/`, offsets in `character.json`): tell the user to draw it at
~30 % under the sprites. A rig rendered before this version has no `-s.png`: re-run `render` (free) before `finish`.

## Rules
- Spend money only after the user agreed to that amount. Show the free render before any paid step.
- Keep everything in the user's project folder; don't touch other files.
- Real brands, logos and characters from existing games or films: leave them out of descriptions (write "no logos").
- The output is the user's; the bundled `cozy` style picture may be used freely (MIT).
