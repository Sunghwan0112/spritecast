# iso-sprite

**Game props, characters and 8-direction walks at their real size and the exact camera angle, drawn in your art style.** It's a Claude Code plugin.

[한국어](README.ko.md)

![a character walking in 8 facings, drawn over its 3D model](docs/character-walk.gif)

![guide → sprite](docs/showcase.png)

## What it does

Ask an image model for "an isometric armchair" and you get a nice picture at a slightly wrong angle. Ask again and you get a
different wrong angle and a different size. Put ten of them on one floor and nothing lines up.

A walking character is worse. Here GPT alone (the same model, the same character sheet, the walk asked for frame by frame in
words) against iso-sprite. Each of GPT's frames is a nice drawing, but it doesn't walk: the same leg is in front in all eight frames,
the arms twitch at random instead of swinging against the legs, the camera is at eye level instead of looking down at the game's 30°, and there is no shadow.
Both tries are shown as they came out.

![GPT alone, two tries, against iso-sprite: the same character walking south-east](docs/gpt-alone-vs-guide.gif)

iso-sprite gives the model something it can't misread:
1. Claude builds the object from simple blocks at its **real size in metres**.
2. The blocks are rendered with your game's **exact camera**.
3. The image model only redraws that guide in your **art style**.
4. The drawing is cut out and **laid back over the guide**, so its angle, size and footprint are exactly the guide's. It also gets a
   baked shadow and an anchor point for your engine.

**What you get from that:**
- **The angle and size are right.** Drawings in the examples stray from their guide by about 1 % (outline overlap 97–99 %).
  Props made months apart still line up on one floor.
- **Shadows that look right.** One light shared by every prop, so every shadow falls the same way. Solid props cast the 3D
  guide's exact shadow. Characters and plants cast a shadow in the drawing's own shape (the hood, the hair, the leaves), placed by
  the 3D model: each foot and a pot's base start their shadow exactly where they stand. Not a painted blob, not a blocky mannequin.
- **It checks itself.** After drawing, the result is compared with its guide. If the model drew another angle, nothing is squeezed to
  fit: you get a warning, and Claude suggests a fix before drawing again.
- **Your game's view and your style.** 2:1 isometric, true isometric, 3/4 top-down, front or any angle; all four facings of one
  object; the bundled `cozy` style or one picture of your own.

## How a session goes

![how a session goes](docs/session.png)

You describe the prop. Claude asks only for what's missing: the size, the facing, your game's view, your style. It renders the
guide for free and shows it to you. It tells you the cost and waits for your OK. Then you get `sprite.png`, `shadow.png` and
`sprite.json`.

## Install

In a terminal:
```
claude plugin marketplace add Sunghwan0112/iso-sprite
claude plugin install iso-sprite@iso-sprite
```
or inside Claude Code: `/plugin marketplace add Sunghwan0112/iso-sprite`, then `/plugin install iso-sprite@iso-sprite`.

**You also need** only Python 3.9+ and a browser (Chrome, or Edge - every Windows has it). The first time, Claude runs the setup
check (`doctor.py --fix`): it makes its own venv in `~/.cache/iso-sprite/` with the few packages (about 10 s), leaves your Python
alone, and tells you what each thing is for. Nothing to install by hand.

| what | for | needed? |
|---|---|---|
| Python 3.9+ | runs the scripts | yes |
| numpy, pillow, scipy | cutting out, fitting, shadows | yes (set up for you) |
| playwright + Chrome or Edge | renders the 3D guide on your computer (free) | yes (set up for you; a browser you have is used) |
| onnxruntime + a 224 MB model | characters only: the AI cut-out that keeps white shoes on white paper | characters (fetched once, by itself) |
| `OPENAI_API_KEY` | drawing, about $0.07 a prop | to draw |
| `TRIPO_API_KEY` | characters: the 3D model, its rig and walk | for walking characters |

**Try it first, free, no key:** ask Claude to *"try iso-sprite"*. It renders one of the examples' guides on your computer and
finishes it with the drawing that came with the example (`isoprop.py try`), so you see the whole way before paying for anything.

Keys:

```bash
export OPENAI_API_KEY=sk-...          # macOS / Linux (add it to ~/.zshrc or ~/.bashrc to keep it)
```
```powershell
setx OPENAI_API_KEY "sk-..."          # Windows (then open a new terminal)
```
Your key stays on your computer. It is only sent to OpenAI, and you pay OpenAI for each drawing (about $0.07).

## Things to ask for

- *"Make an isometric bookshelf, 1.8 m tall, full of books, in the cozy style."*
- *"Our game is 3/4 top-down. Make a wooden market stall with a striped awning."*
- *"Make this sofa in all four facings."* (`views`)
- *"Make a shopkeeper NPC, an old man in a brown cardigan, in four directions."*
- *"A street musician, waving, facing south-east."*
- *"Here's a prop from my game (props/barrel.png). Make a matching crate in that style."*

## Examples

All in [`examples/`](examples), each with its spec and the files it produced (the raw drawings as WebP, to keep the repo small).

| | | |
|---|---|---|
| ![](examples/reading_armchair/preview.png) | ![](examples/potted_monstera/preview.png) | ![](examples/arcade_cabinet/preview.png) |
| `reading_armchair`: 9 blocks: seat, back, arms, legs | `potted_monstera`: a pot, and the plant given as one volume | `arcade_cabinet`: its front faces down-left |

![four facings and a top-down view](docs/views.png)
`armchair_four_ways`: `views: [0, 90, 180, 270]`. The later views are drawn with the first one as a reference, so it stays the same
chair. `arcade_cabinet_topdown`: `camera: "topdown"`. `reading_armchair_tripo`: the same armchair from a Tripo model (below).

## More detail: a 3D model first (Tripo)

![blocks vs a Tripo model as the guide](docs/tripo.png)

Blocks are enough when what matters is where things stand and how big they are. For more detail (curved arms, tapered legs, buttons,
carving), let [Tripo](https://www.tripo3d.ai) make a real 3D model from the description first. It's fitted into the same real-size box
the blocks gave, so the arrangement doesn't change, and it becomes the guide. The image model then draws over a real shape, and the 3D
shadow is the model's own.

```
python isoprop.py model armchair.json --yes   # Tripo text-to-model (~20 Tripo credits, ~2 min); the spec now uses it
python isoprop.py yaws  armchair.json         # free: the model turned four ways; set "model": {"yaw": ...} to the right one
python isoprop.py render armchair.json        # then draw, finish as usual
```
Needs `TRIPO_API_KEY`. The blocks stay in the spec as `blocks_draft`.

## Characters

![a mannequin guide and two characters in four facings](docs/characters.png)

Standing characters work the same way. Claude poses a plain mannequin at the person's real height and renders it in each facing (4 or
8). The image model dresses it as you describe. The first facing is drawn first and the others follow it, so it stays the same person.

```json
{ "name": "barista",
  "character": { "height": 1.63, "build": "slim", "directions": ["south-east", "south-west", "north-east", "north-west"] },
  "description": "a cheerful young café barista: a short dark-brown bob, a cream cable-knit sweater under a forest-green apron, ..." }
```

The anchor is between the feet. About $0.07 for the first facing and $0.08 for each of the others.

**Poses.** The mannequin has joints. `"pose"` is one of `stand` (default), `wave`, `point`, `hold` (hands together in front: a cup,
a tray, a book), `arms-crossed` or `walk` (mid-stride). Describe what goes with it ("waving hello", "holding a coffee cup"). Or give the angles yourself, and Claude can adjust them
for you ("raise the arm higher") and check them in the free render:

```json
"pose": { "base": "stand", "arm": { "left": [[150, 10], [170, 10]], "right": [[150, 10], [170, 10]] } }
```
Each limb is two parts, upper and lower (`[out, forward]` degrees each): turned out to its side, then swung forward. `left` and
`right` are the figure's own.

![four poses](docs/poses.png)

**Single pictures.** These posed figures are one picture per facing; for a walk, see [Walking characters](#walking-characters). Look at every facing yourself: once a back view came out with the head turned away but the body facing front (now prevented in
the prompt), and the outline check can't see that. Redraw one facing with `draw <spec> --yes --again --only north-west`.

## Shadows that match the drawing

The 3D guide's shadow is exact for solid things like furniture. But a drawing has things the blocks don't: hair, a coat's hood,
leaves spilling out of a pot.

So iso-sprite also renders a **height map** of the guide: how high above the floor every pixel is. A point h metres up casts its
shadow a fixed step away on screen (h times the light's offset), whatever its depth. So each pixel of the drawing takes the height of
the guide under it, or of the nearest guide pixel for hair or leaves past the guide, and is moved by that step.

The shape is the drawing's. Where it starts is the 3D model's: each foot starts its own shadow, and a pot's shadow starts at its
base. Only what touches the floor has to be exact. Higher up (from 10 % to 35 % of the object's height) the height eases into a
smooth one read off the screen, so hair, hats and leaves cast a natural shadow instead of the mannequin's corners. Where it stands
(the blocks up to 12 cm: shoes, a pot's base) the guide's own 3D shadow is added, so the shadow meets the object as a real one
would: on the side away from the light, never in front of it. Characters and `loose` things get it; solid props keep the 3D shadow. Choose with `"shadow": "drawn" | "guide"`.

![shadows from the blocks and from the drawing](docs/shadows.png)

## Walking characters

![an illustration → 3D → drawn frames → an 8-facing walk](docs/character.png)

![walking in 8 facings](docs/character-walk.gif)

Give it one illustration of a character (facing front, standing straight, no pose) and you get a walk in 8 facings (8 frames each) and 8 standing views, in that
illustration's look. An image model can't keep a body and a pose from frame to frame, so the motion comes from 3D:
1. A turnaround is drawn from the illustration.
2. [Tripo](https://www.tripo3d.ai) makes the 3D model from it.
3. Tripo rigs it and gives it a walk and an idle.
4. The walk is rendered with the game's camera (free), and with every frame the 3D body's own shadow, pressed flat onto the ground
   along the light.
5. The image model draws over the renders, 4 frames a call. The front is drawn first and every other facing follows it, so it
   stays the same person.
6. Every frame is fitted back onto its render (the upper body at one size for the whole facing, the legs reaching the render's
   feet), the head sizes steadied, and the edges cleaned. You get strips, a shadow per frame (the feet touch it, a lifted foot
   casts its own) and an anchor.

```
python skills/iso-sprite/scripts/charpipe.py turnaround hero.json --yes   # then 3d (model, rig, renders) and draw (then finish, preview by themselves)
```
Cost per character: about $2.2 (OpenAI) and 75 Tripo credits (~$0.75). Two accounts in all: `OPENAI_API_KEY` and
`TRIPO_API_KEY`. Or bring your own rigged GLB (`"rig_glb"`) and skip to `render`.

**The author's way: Meshy for the model, Tripo for the rig.** The game this plugin came from made its leads this way. Set `"modeler": "meshy"`
(and `MESHY_API_KEY`) and `model` asks [Meshy](https://www.meshy.ai) instead (~30 Meshy credits); `rig` is still Tripo's.
Either works. Tripo turns each model its own way (one faced sideways, another backwards: its "dark face" was the back of his head)
and now and then sends one back uncoloured. Both are fixed for you: the model is turned to face front by its feet, and coloured
again if it comes back grey. Meshy's models faced front and came coloured every time.

 Details and lessons:
[reference/character.md](skills/iso-sprite/reference/character.md). The girl above is in
[`examples/rain_girl`](examples/rain_girl): her illustration, turnaround, spec, strips, shadows, `character.json` and the sheet.
She was made with Tripo alone: about $1.7 of drawing and 85 Tripo credits.

## Cameras

| `camera` | looks down | for |
|---|---|---|
| `"iso-2:1"` (default) | 30°, turned 45° | most isometric games; floor tiles twice as wide as tall |
| `"isometric"` | 35.26°, turned 45° | true isometric (120° between the axes) |
| `"topdown"` | 50°, square on | 3/4 top-down RPGs |
| `"front"` | 12°, square on | side-scrollers |
| `{"pitch": 40, "yaw": 30}` | anything | your own angle |

`"light": "left"` mirrors the light and the shadow.

## Putting it in your engine

`sprite.json` tells you where the prop touches the ground:

```json
"sprite": { "file": "sprite.png", "size": [299, 357], "anchor": [0.4993, 0.9966], "anchor_px": [149.3, 355.8] },
"shadow": { "file": "shadow.png", "offset_px": [-66, 116] },
"px_per_m": 256
```

- **anchor**: the footprint's front corner on the ground (the middle of its front edge in the square-on views). Put that point on
  the tile where the prop stands.
- **shadow**: draw `shadow.png` at `offset_px` from the sprite's top-left corner, at about 30 % opacity, under all sprites.
- **scale**: everything is drawn at `px_per_m` pixels per metre. For a 2:1 map whose tiles are 1 m and `T` px wide, scale by
  `T / 1.414 / px_per_m`.

| engine | how |
|---|---|
| Phaser | `this.add.image(x, y, 'armchair').setOrigin(anchor[0], anchor[1])` |
| Godot 4 | `Sprite2D`: `centered = false`, `offset = -anchor_px` |
| Unity | Sprite Editor → Pivot: Custom, `(anchor[0], 1 - anchor[1])` |

## How it works

| step | what | cost |
|---|---|---|
| spec | Claude writes `<name>.json`: footprint, blocks in metres, a description of the finished object | free |
| `render` | three.js in headless Chrome: the guide, its shadow and the model's input | free |
| `draw` | OpenAI Images (`gpt-image-2.5-sunburst` by default): the guide redrawn in your style | ~$0.07 |
| `finish` | magenta keyed out softly, fitted back onto the guide's box, shadow baked, anchor measured | free |
| `preview` | the sprite on a 1 m floor grid | free |

You can run the steps yourself too:
`python skills/iso-sprite/scripts/isoprop.py render|draw|finish|preview examples/reading_armchair.json`. `draw` only prints the cost
until you add `--yes`. The spec format is in [reference/spec.md](skills/iso-sprite/reference/spec.md). Tips for good guides are in
[reference/tips.md](skills/iso-sprite/reference/tips.md).

## If something goes wrong

| problem | fix |
|---|---|
| `No module named ...` | `python skills/iso-sprite/scripts/doctor.py --fix` (Claude runs it for you) |
| no browser | install Chrome, or `doctor.py --fix --browser` (Playwright's Chromium, ~150 MB) |
| `this Python cannot make a venv` | Debian/Ubuntu: `sudo apt install python3-venv`, or use another Python (python.org, conda) |
| `draw: set OPENAI_API_KEY` | set the key (above) and restart Claude Code |
| `HTTP 401` / `403` | the key is wrong, or OpenAI wants your organisation verified before it allows image models (platform.openai.com → Settings → Organization) |
| `finish: WARNING - the drawing does not follow the guide` | the model drew another angle or shape: make the description say what is seen from this camera, check the guide, draw again with `--again`. For plants and other loose shapes that may spill past their guide, set `"loose": true` |
| the drawing added things | say what must NOT be there in the description ("no rug, no logos"), then draw again |
| the shape is off | fix the blocks: the drawing follows the guide |

## What it sends and fetches

Everything runs on your computer except the steps below. Each paid step prints its cost and waits for your OK first.

| when | sent to | what |
|---|---|---|
| `draw` | OpenAI (`api.openai.com`) | the guide picture, your style picture and the text description, with your `OPENAI_API_KEY` |
| characters: `turnaround`, `draw` | OpenAI | the illustration, the turnaround and the 3D renders, with the same key |
| characters: `3d` | Tripo (`openapi.tripo3d.ai`) | the four turnaround views, with your `TRIPO_API_KEY`; the model, its rig and walk come back |
| `model` (props, optional) | Tripo | the text description |
| characters, `"modeler": "meshy"` (optional) | Meshy (`api.meshy.ai`) | the four views, with your `MESHY_API_KEY` |

The keys are read from your environment only, sent only to their own service, and never written to a file or printed. What is downloaded:

| what | from | when |
|---|---|---|
| numpy, pillow, scipy, playwright, onnxruntime | PyPI, into its own venv (`~/.cache/iso-sprite/venv`) | `doctor.py --fix`, once |
| Chromium (~150 MB) | Playwright's servers | only if there is no Chrome or Edge, and only after you say yes |
| the cut-out model, BiRefNet lite (224 MB, MIT) | [rembg's GitHub release](https://github.com/danielgatis/rembg/releases/tag/v0.0.0), its md5 checked | characters, the first `finish` |

The renders run in a headless browser on your computer with nothing loaded from the internet: three.js is bundled
(`skills/iso-sprite/scripts/vendor/three/`, MIT).

## Notes
- The output is yours.
- Leave real brands, logos and characters from existing games out of descriptions.
- Solid props get the 3D shadow of their blocks; characters and `loose` things a shadow in the drawing's own shape (see Shadows).
- Settings: `ISO_SPRITE_MODEL` and `ISO_SPRITE_QUALITY` (`low` | `medium` | `high`).

## License
MIT. three.js (bundled in `scripts/vendor/three`) is MIT, © three.js authors.
