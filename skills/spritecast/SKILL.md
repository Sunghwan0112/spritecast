---
name: spritecast
description: Make 2D game sprites at their real size and exact camera angle, in the user's art style, from a 3D guide that an image model redraws. Use when the user asks for an isometric or top-down prop, furniture or object sprite (painted or pixel art, from any side, with its shadow); a standing NPC from a description; a character walking in 8 or 4 facings from one illustration, or its run, jump, attack, throw or a Mixamo FBX clip; pixel-art sprites or a sprite sheet of a character; a seated or sitting character, or one put on a chair or bench; a character for a side-scrolling game or platformer; monsters, enemies, animals or townspeople drawn straight in 2D on a mannequin's walk with no 3D model each (side view, from above in 8 facings, or pixel art); a four-legged animal's walk; a swing's effect, a meadow ground, or files for Godot, Unity, Phaser or Aseprite; or fixing a sprite by hand - pixel sprites in a local editor, a cut-out, a halo or what covers what on a touch-up page.
license: MIT
compatibility: Claude Code (runs Python, Playwright and a local Chrome/Chromium on the user's machine; calls the OpenAI Images API with the user's own key)
---

# SpriteCast: game sprites at true size and angle, from a 3D guide

Asked for a game sprite, an image model draws it at a slightly wrong angle and size, and a walk that does not walk. SpriteCast gives
the model a guide it cannot misread - blocks at real size, a 3D model or a posed mannequin, rendered by the game's own camera - lets it
redraw only the look, and lays the answer back on the guide: cut out, fitted, with a baked shadow and an anchor.

Scripts are in `${CLAUDE_SKILL_DIR}/scripts/`; `PYTHON` below is the interpreter `doctor.py` prints. **Find the flow in the table
below and read its reference file before the first step** - this file says what to ask and in which order; the reference has the spec.

## Money: the rule for every flow
- A paid step run **without `--yes` prints its cost and spends nothing**. Say that cost - and the total when there are several - wait
  for a yes to THAT amount, then run it with `--yes`. One paid step at a time: never the next one because the last "looked fine".
- Show the free render (the guide) before the paid drawing. Everything after follows the guide: a problem seen there is fixed there.
- Never draw again (`--again`, `redraw`, `--redraw`) without asking. A drawing that came out wrong is usually the guide or the words.
- What the scripts' gates say (OpenAI at quality `high`; the bill is usually a little under):

| step | about |
|---|---|
| a prop's or a standing person's drawing (`isoprop.py draw`) | $0.08 the first view, $0.09 each further one |
| a character's turnaround | $0.09 |
| a sheet of 4 frames (`charpipe.py draw`, `redraw`, `sit --draw`) | $0.11 - a walk with its standing views is 18 sheets in eight facings (~$2), 9 in four (~$1), 3 in a side view (~$0.33) |
| one frame drawn alone (`charpipe.py frame`) | $0.08 |
| a pixel-art sheet (`pixelart.py`) | $0.075 - a walk is 2 sheets a facing (~$1.35 in eight); an action with something held 4 |
| a pixel prop's view (`proppixel.py`), a sheet of a prop's poses (`propanim.py`) | $0.08 |
| a creature's design, its walk, a sheet of four moments (`creature.py`) | $0.06 each (a walk seen from above: each facing; as pixel art: ~$0.07 a sheet, two a facing) |
| Tripo | a character's model + rig + walk ~75 credits (~85 if it comes back uncoloured), each extra action ~10; an animal's model ~30 (~40); a prop's model 20-40 |

## Setup (once)
1. `python3 ${CLAUDE_SKILL_DIR}/scripts/doctor.py` (any Python 3.9+; `python` on Windows) lists what is there and what each thing is
   for; its last line `PYTHON=<path>` is the interpreter for every script. "not ready": say in a line what is missing and run it again
   with `--fix` (a venv in ~/.cache/spritecast/, ~10 s). No Chrome or Edge: ask first, then `--fix --browser` (Playwright's Chromium,
   ~150 MB). For characters and creatures add `--characters` (the 224 MB cut-out model, once).
2. Keys: `OPENAI_API_KEY` for every drawing; `TRIPO_API_KEY` only for a 3D model - a walking character's model and rig, a prop's
   detailed model (not for props from blocks, standing people or `creature.py`). They come from the plugin's settings (`/plugin` →
   SpriteCast; a session-start hook hands them to the scripts), else from the environment. Missing: tell the user to put it in the
   plugin's settings and restart Claude Code. Never ask for a key in the chat, never write one into a file, never print one.
3. **No OpenAI key, or nothing to spend on drawing:** every drawing step can be done by hand in the ChatGPT app - `pixelart.py --manual`,
   any other script with `SPRITECAST_DRAW=manual` in its environment. Each picture becomes a job on a local page (127.0.0.1:8790) with
   what to attach and the prompt; the answer is taken from ~/Downloads. Read [reference/manual.md](reference/manual.md) and tell the
   user what to expect: the same character a little plainer than the API's, a frame may need drawing again, the app's own limits.
4. **A first-time user, or "try it" / "체험":** `PYTHON isoprop.py try [--out DIR]` - free, no key: an example's guide rendered on
   their computer and finished with the drawing that came with it → show `preview.png` and `render.png`, then offer their own prop.

## Which flow

| the user wants | script | read first | keys | what is paid |
|---|---|---|---|---|
| a prop, furniture, an object - isometric, top-down or front | `isoprop.py` | spec.md, tips.md | OpenAI | `draw`; `model` (Tripo) only for more detail |
| scenery for a side-scrolling game (a wall, a house front) | `isoprop.py`, `"camera": {"pitch": 6, "yaw": 90}`, over a Tripo model | tips.md "Scenery for a side-scrolling game" | OpenAI + Tripo | `model`, `draw` |
| a standing person in a pose (an NPC) | `isoprop.py`, a `character` spec | spec.md | OpenAI | `draw` |
| a character that walks in 8 or 4 facings; its run, jump, attack | `charpipe.py` | character.md | OpenAI + Tripo | `turnaround`, `3d`, `draw`, `redraw` |
| a four-legged animal walking in 8 facings | `charpipe.py`, `"kind": "animal"` | character.md "Animals" | OpenAI + Tripo | the same |
| a side-scrolling game's hero - many moves, a thing in the hand | `charpipe.py`, `"view": "side"` | character.md | OpenAI + Tripo | the same, 3 sheets a walk |
| monsters, animals, townspeople with no 3D model each - a side-scrolling game's, or walking in 8 facings seen from above, or as pixel art | `creature.py` | creature.md | OpenAI | `design`, `walk`, `sheet` |
| pixel art of a character; of a prop | `pixelart.py`; `proppixel.py` | pixel.md | OpenAI (Tripo for a prop seen from several sides) | the sheets |
| an isometric prop that moves (a ghost's arms); see-through; wind; a lamp's light; where it blocks | `proprig.py` + `propanim.py`; spec keys; `propshade.py`, `lightedit.py` | pixel.md | OpenAI for `propanim.py` only | `propanim.py`'s sheets |
| a character sitting, or put on the user's chair | `charpipe.py sit`, `seat.py` | sitting.md | OpenAI | `sit --draw` |
| the ground of a map | `ground.py` | ground.md | - | nothing |
| hits, splashes, fire round the sprites | `fxpack.py` | pixel.md "Effects from the pack" | - | nothing |
| a Mixamo move on the rig; attacks that join into a combo | `addclip.py`, `motion.py` | character.md "Moves that join" | - | nothing |
| files for Godot, Unity, Phaser, Aseprite | `export.py` | below | - | nothing |
| fixing by hand | `touchup.py`; `pixeledit.py` | touchup.md; pixel.md "Fixing by hand" | - | nothing |

Two flows are called a creature: a monster for a SIDE view, drawn in 2D with no 3D model of it, is `creature.py`; an ISOMETRIC prop
whose parts move (a ghost) is `proprig.py` + `propanim.py`.

## A prop (`isoprop.py`: `render`, `draw`, `finish`, `preview`)
1. **Ask only what is missing**: what it is, its real size if it matters, which way it faces, the game's view (`camera`: 2:1 isometric
   by default, true isometric, 3/4 top-down, front, or their own angle), whether it must turn (`views`), and the art style (`cozy`,
   or their own reference picture: one finished prop in the look they want, on a flat background).
2. **Write the spec** (`<name>.json` in their asset folder): footprint in metres, the blocks at real size, a `description` of the
   finished object (materials, colours, details), `facing`. Look real sizes up if unsure (a chair's seat ~45 cm, a door 2.0-2.1 m).
3. **`render <spec>` (free).** Look at `render.png` and `render-shadow.png` yourself, then show `render.png`. Fix the blocks until
   shape, proportions and facing are right.
4. **`draw <spec>` (paid).** With `views`, the first is drawn first and the others follow it - for a new design, check the first
   before drawing the rest.
5. **`finish <spec>`, `preview <spec>`.** If `finish` warns (`sprite.json` `fit.ok` false) the model drew another angle or shape and
   it was NOT squeezed to fit: tell the user, say why (often an angled style picture), fix the description, ask before drawing again.
   Look at `preview.png` and show it. Parts added or moved: say in the description what must NOT be there.
6. Hand over `sprite.png`, `shadow.png`, `sprite.json` (anchor, footprint corners, px per metre, shadow offset): the sprite's anchor
   goes on the footprint's front corner; shadows are drawn under all sprites.

**More detail than blocks give** (curves, carving) and the user has a Tripo key: once the blocks are right, `model <spec>` (Tripo;
~2 min) makes a model from the description at the blocks' HEIGHT in its own proportions (blocks → `blocks_draft`), then `yaws <spec>`
(free): set `model.yaw` to the turn whose front faces where the blocks' did; render, show, draw as usual. Blocks alone are right when
the arrangement and exact sizes matter more than surface detail. From several sides in pixel art the guide must be a model.

## A standing person (`isoprop.py`, a `character` spec)
One of SpriteCast's mannequins (`"body"`: `"man"`, `"woman"`, `"child"` - bald, plain, a real figure) at their real height, put in the
pose, one view a facing, the first drawn first and the rest from it. The body is chosen from the description when `"body"` is left
out (a man, a woman, a child - a boy or a girl); ask the height, the build, what they wear, and the
facings (4 diagonals unless their game uses 8; the 4 cardinals for a game that moves up, down, left, right). Poses: stand, wave,
point, hold, arms-crossed, walk (one mid-stride picture) - say the pose in the description too. Anything else: write the angles
(spec.md "Custom poses"), render, look, adjust, and only then draw. A palm can be turned (`"palm"`); limbs that overlap are pushed
apart, and `render` warns when a pose could not be freed. **Look at every facing yourself before showing them**: the outline check
cannot see a body turned the wrong way inside a right outline (a back view with the front of the clothes) - redraw that one with
`draw <spec> --yes --again --only <facing>` (ask first). Shadows are cast from the finished drawing. These are single pictures: an
animation is `charpipe.py`, or in a side view `creature.py` on the same mannequins.

## A walking character (`charpipe.py`) - [reference/character.md](reference/character.md)
**Ask first:**
- **Eight facings or four.** `"facings": 4` draws only the diagonals - about half the drawing; most isometric games use only these.
  `"facings": "cardinal"` draws south, east, north, west for a game that moves that way. The exported character still answers all
  eight directions with the nearest facing drawn. Offer four whenever cost matters.
- **The illustration**: one finished picture of the character facing front, standing straight, arms down. If theirs is posed, draw a
  neutral one from it first and show it.
- **How tall on screen**: 512, 256 (default), 128 or 64 as `"frame_px"`; another size later is `pack --px` (free).
- **The game's view** as `pitch`, not `camera`: 30 (2:1, default), 35.26 true isometric, 50 3/4 top-down, 12 front.

Three paid steps, a yes before each: **`turnaround`** (show it: both sides the same, nothing over the arms) → **`3d`** (Tripo: model,
rig, walk, then the free renders - show the front and a side: the face, not the back of the head) → **`draw`** (every facing; then
`finish` and `preview` run by themselves - show `out/sheet.png` and a GIF). `"modeler": "meshy"` with MESHY_API_KEY makes the model
with Meshy; the user's own rigged GLB is `rig_glb`.

- **A four-legged animal**: `"kind": "animal"`. `3d` makes only the model - no rig is bought, the skeleton is found from the mesh and
  walked in a cat's gait. The turnaround on all four legs, each leg clear, the tail out behind; only snug clothes. Check the renders
  before `draw`: four legs, the head forward, the tail behind.
- **Cheaper, softer**: `"draw": false` - the 3D renders are the frames (the turnaround is still drawn unless they bring a rigged GLB).
  Offer it for prototypes and background walkers; say it is softer.
- **Every facing is drawn by default.** A flipped facing swaps whatever is not the same on both sides (hair over one shoulder, a bag).
  `"mirror": true` saves ~$0.66 on a design that is the same on both sides - only when the user asks.
- **After `draw`**: `finish` names the sheets with a frame under `redo_below` (0.75). Show `out/walk-all.mp4` (every facing at once):
  a head that grows and shrinks or a jumping frame shows there, not in the numbers. Look at the back views yourself for things worn
  on the head. Drawing sheets again is a round the user agrees to each time - the procedure, and when a facing is mixed with its
  mirror, is in character.md "After `draw`".
- **Shadows** are per frame (`out/shadows/`), drawn under the sprites at `character.json`'s `shadow_alpha` (0.56). `"shadow_strength"`
  makes them deeper or paler (painted sets 1, pixel sets 1.5; the same number for the game's props) - `pack` again is free.

**A side-scrolling game: `"view": "side"`.** One facing is drawn (east) and west is its mirror: a walk and the standing view are 3
sheets. The body is turned 45° toward the viewer by default (`"turn": 45`: both eyes show, and a swing across the body is not hidden);
`"turn": 0` is a flat profile - offer it for a game drawn in strict profile, and show the free renders at both angles if they are not
sure. No shadow in this view; no sitting yet (`sit --draw` stops); pixel art draws east only. For what a side-view game needs MANY of -
monsters, townspeople - use `creature.py` below, not a 3D model each.

**More actions** (`"actions": ["run", "jump", {"name": "slash", "hold": "umbrella"}]`, before `3d` or `rig --again`):
- **Which source - say it when they ask for an action.** Tripo to save time: one step, and moves with empty hands (walk, run, jump)
  come out fine (presets: run, jump, slash, shoot, dive, climb, fall, hurt, turn; three at most). **Mixamo when the result matters,
  attacks above all** - motion capture, free, and one set's attacks share a stance so they join into combos. Mixamo has no API: give
  the search link `https://www.mixamo.com/#/?page=1&query=<words+joined+by+plus>&type=Motion%2CMotionPack`, the download settings (FBX
  Binary, 30 fps, Without Skin, no keyframe reduction), then `addclip.py CHAR.json Move.fbx name` (free). **Never put a Mixamo file,
  or a rig carrying its motion, in a public repository.**
- `render` renders each action in every facing, `draw` draws them after the walk (2 sheets a facing), `finish` packs →
  `out/<name>-<facing>.png` and `"actions"` in `character.json`. Show the renders first; a clip with a long still tail takes
  `"t0"` / `"t1"`.
- **Something in the hand**: `"hold"` builds it on the hand (`umbrella`, `pistol`, `watergun`, or its own shape), so it is in every
  render. **Open `render/hand-<name>.png` and read the line `render` prints before any paid sheet** (character.md "the hand closes on
  it"), and describe the thing part by part (character.md "A held thing: say it part by part").
- **Joining two animations**: `{"name": "ready", "between": ["walk", "slash"], "frames": 3}`; see them joined with
  `charpipe.py loop SPEC --only walk,ready,slash --facing <f>` (free) → `out/loop-<f>.gif`.
- **One frame wrong**: `"frame_words": {"5@south-east": "..."}`, then `charpipe.py frame SPEC --only <action> --facing <f> --frame <n>`.
- **A swing's effect**: `"trail": "water"` (also `plain`, `wind`, `drops`, `fire`, `flames`, `leaves`, `greenleaves`, `petals`,
  `snow`, `sparkle`) - free, nothing drawn: read off the held thing's path on the rig, a sprite of its own over the body. Offer it for
  a slash.
- The head in an action, what `redraw` does with a held thing, and what the prompt says: character.md "Actions: the head, `redraw`,
  the prompt".

## Monsters, animals and people on a mannequin's walk (`creature.py`) - [reference/creature.md](reference/creature.md)
For what a game needs many of, no 3D model of each is made. A spec with `"style"` (a finished character of the game),
`"what"`, `"height"` (px in the game) and `"sheets"`. **A person goes in another order than an animal - decide which first.**
- **A four-legged one on straight legs** (wolf, boar, deer): `design` (PAID - one picture from the side, in the style picture's look;
  show it) → `mannequin` (free: SpriteCast's plain dog is given the design's leg length, body depth and neck, and its walk laid out as
  `walk-guide.png` - **look at it beside the design before paying**: on a mannequin that was not fitted every creature came out with
  a dog's legs) → `walk` (PAID: 8 frames on those poses).
- **A person** (`"mannequin": "man" | "woman" | "child"`): `mannequin` FIRST (free: the bald figure walking, and standing in the view
  the design is drawn in) → `design` (PAID: the character drawn standing as the mannequin stands, of its build) → `walk` (PAID). No
  fitting for people. Left out, `"mannequin"` is chosen from `"what"` - a man, a woman, a child (a boy, a girl), an animal on four legs
  (the dog); `mannequin` prints the word that chose it.
- **Seen from above** (`"view": "above"`, an isometric or top-down game): the walk in 8 facings (`"facings"`: 4, `"cardinal"`), ONE
  PAID picture a facing (~$0.06 each; `walk --only south-east` first, show it, then the rest), the design may be the side view's.
  `out/walk-<facing>.png`, `out/stand-<facing>.png`, an `anchor` (the ground under the figure) and a `[across, down]` step each.
- **As pixel art** (`"pixel": 96`, the figure's sprite pixels; with either view): the mannequin reduced to sprite pixels, drawn over
  as pixel art and read back on its grid - two PAID sheets a facing (~$0.07 each). Other moves (`sheet`) stay illustrations.
- `cut` names a person's walk frame overlapping the mannequin under `"redo_below"` (0.5): look at it; `walk --again` (`--only` a
  facing). An animal has no threshold: ALWAYS look at its strip and `preview.gif` yourself, and show them.
- **Anything else it does** - struck, falling apart, a hop, a drift: `sheet <spec> <kind>` (PAID each), four moments said in words
  (FIRST ... FOURTH). A creature with no such walk (a blob, a cloud; `"mannequin": false`) is sheets only - then give each sheet its
  own `"height"`. What stands another way (a lizard, a spider) has no mannequin yet: its movement is a sheet.
- `preview` (free) → `out/preview.gif`. Hand over `out/*.png` and `out/creature.json` (`export.py` does not read these) and say: show
  the walk's frame for the DISTANCE walked (`step` px a whole step), so the feet do not slide.
- The game's main character - many actions, a thing in the hand - is still `charpipe.py` with `"view": "side"`: a mannequin gives a
  walk, not a rig of the character.

## Pixel art - [reference/pixel.md](reference/pixel.md)
Not a filter over the illustrated frames: the 3D renders are pixelized into a guide, the image model redraws the guide as pixel art,
and the answer is read back onto the grid it was drawn on. It needs the character's renders only (`charpipe.py render`).

**A character: `PYTHON pixelart.py CHAR.json`** prints the plan and the cost and spends nothing; `--yes` draws.
- Offer **96 px** (`--px`; 128 comes out about 104 - say so). **64 only for a character designed small** (about three heads tall, its
  own 3D model: pixel.md "Sizes"); `--px 32` draws at 64 and makes the 32 set from it.
- **One facing of one animation first**, as the sample: show `out-pixel96/preview.gif`, then the rest. It draws the spec's facings; a
  side view draws east only (the game flips it).
- Every run ends with its review (`REVIEW: N of M frames to look at`): show `review.png`, each marked frame beside its guide.
  `--redraw` says what drawing those sheets again would cost; `--again <sheet>` redraws one.
- Fewer colours or the game's own palette: `--colours N`, `--palette NAME|FILE` (free; `--palette list`).
- **By hand, for what is left**: `PYTHON pixeledit.py CHAR.json` - a local page (a server: run it in the background, give the
  address) to erase, draw or copy a good face into another frame; edits are kept across later runs. `--join walk,ready,slash
  --facing south-east` shows animations a game plays one after another as one.
- Something thrown (`"hold"` with `"until": "auto"`), an animation the rig lacks (`addclip.py`), attacks that join
  (`motion.py`: `ground`, `plant`, `link`, `blade`, `layer`, `join`, `preset`), a swing's water reaching further (`"trail_reach"`),
  and the standing loop: pixel.md and character.md "Moves that join". No moves come with SpriteCast - only the changes made to them.

**A prop: `PYTHON proppixel.py PROP.json`** - the prop's guide pixelized and redrawn the same way, at the pixel character's pixels per
metre (`--ppm` = its `figure_px` / its `height_m`) so they stand on one floor. One view of a simple thing works from blocks; **from
several sides the guide must be a 3D model** (`isoprop.py model`: say the cost and wait). Show `out-pixel/preview.png` beside the
renders. With a model, all of this is free and baked from it (pixel.md "Props as pixel art"):
- **Shadow**: `out-pixel/preview-shadow.png`; `--shadow overcast` for a grey scene; `--shadow-strength` (1.5 by default in pixel art;
  1 on a light floor, 1.6-2 on dark ground). Indoors: `propshade.py PROP.json --lamp x,y,z --lamp-size r`, or `lightedit.py PROP.json`
  (a local page where the user drags a lamp and sees the shadow and the floor's light).
- **Wind**: `"sway": "leaves"` for a tree or a bush, `"caps"` for small things - show `preview-sway.gif`.
- **The game's rules**: `solid-<side>.png` (where a walker cannot stand), `"collide": {"cover": [0.55]}` (what stops a thing flying
  at that height), and how to darken a character in its shade.
- **See-through** (a flame, a ghost, water): `"translucent": "fire" | "ghost" | "water"`. **Parts that move** (a ghost's tail):
  `proprig.py PROP.json` (free: bones from the mesh, show `rig/poses.gif`) then `propanim.py PROP.json` (paid sheets).
- **Into the engine**: `export.py PROP/out-pixel` → Godot and Phaser. Unity and Aseprite: not for props yet - say so.

**Effects round the sprites** (`fxpack.py`, free): 253 pixel effects of PVFX Foundry (CC0) come with SpriteCast - `list --search water`,
`preview ID`, `export ID --out assets/fx --as hit [--scale 2] [--palette CHAR.json]`, or a set (`--set water-swing`, `--set fire-swing`).
Say where an effect came from (effects/pvfx/LICENSE.txt).

## One angle for everything, and the ground
Pickups and anything lying in the world (a heart, a potion) are props too - made at the game's camera with their shadow, never
front-on icons beside an isometric character; only what is fixed to the screen (a HUD) may be front-on. Suggest it when a user brings
flat icons into an isometric game (reference/tips.md). **The ground** (free, [reference/ground.md](reference/ground.md)):
`ground.py meadow GROUND.json` - one picture of the whole map's ground, 3D grass and flowers planted over it, lit by the props' sun,
with strips so the grass hides feet; `terrain`, `puddles`, `grass2d`. Never a repeated square tile.

## Sitting (people) - [reference/sitting.md](reference/sitting.md)
Offer it once a character walks (not in a side view). `charpipe.py sit CHAR.json` (free): the rig seated in its facings, on nothing -
show the renders. `sit CHAR.json --draw` (two sheets in eight facings, one in four): drawn and finished → `out/sit-<facing>.png` and
`"sit"` in `character.json`. On one of their props: `seat.py PROP.json CHAR.json --height <m>` (free; ask the character's height) →
`<view>/seat/<char>-<facing>/` with the prop's front piece for that sitter. Show the preview.

## Into the user's engine
A finished character, and the user names their engine: `export.py <name>/out` (free) → `out/export/godot/` (a scene for Godot 4),
`phaser/` (an ES module for Phaser 3), `aseprite/` (one file an action, a tag a facing), `unity/` (copy into `Assets/`: the prefab and
clips build themselves). A swing's effect goes along as a third sprite. Not read yet: a character's pixel set (give the numbers in
`pixel.json`) and `creature.py`'s strips (`creature.json`).

## Touching up by hand - [reference/touchup.md](reference/touchup.md)
`touchup.py SPEC.json` (free) is a local page where the user paints fixes: red clears (paper between limbs, a halo), green brings
pixels back (a white shirt the cut-out took for paper), blue paints a prop's front piece, a polygon, and dragging a seated character
into place. **It is a server: start it in the background**, give the address, stop it when they are done; then `touchup.py SPEC.json
--apply`. Offer it whenever a cut-out, a front piece or a seat looks off - painting by hand is the most accurate step. Never paint for
them without asking.

## Rules
- Money: the rule at the top. Spend only what the user agreed to; show the free render first.
- Keep everything in the user's project folder; do not touch other files.
- Real brands, logos, and characters from existing games or films stay out of descriptions (write "no logos").
- Mixamo files and rigs carrying Mixamo motion never go into a public repository.
- The output is the user's; the bundled `cozy` style picture may be used freely (MIT).
