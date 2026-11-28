# Changelog

What changed in each version. The version is the one in `.claude-plugin/plugin.json`; Claude Code offers an update when it goes up.
Changes made because of a report or a request are marked *(feedback)*.

## 0.29.0 — 2026-11-26

- **SKILL.md reorganised** *(feedback: "the skill is too long; costs differ from doc to doc; some flows stop")*: the money rule and
  one table of what each paid step costs (the figures the scripts' own gates print) at the top, a table from the user's ask to the
  script, its reference file, the keys and the paid steps; each flow's steps in order. 40 KB → 25 KB; the long passages moved to
  the reference files (drawing again after `draw`, an action's head, `redraw` and prompt → reference/character.md; drawing by hand →
  the new reference/manual.md). The description is back under the 1024-character limit (953).
- **A side view turns the body 45° toward the viewer by default** *(the user's choice)*, as `creature.py`'s people already did - both eyes
  show, and a swing across the body is not hidden behind it. `"turn": 0` for a strict profile.
- **Scenery for a side-scrolling game** (reference/tips.md, a row in SKILL.md's table) *(the user, on the example game's castle wall: "almost
  Picasso"; "not three-dimensional"; "just make it from a prompt")*: seen as the characters are (`"camera": {"pitch": 6, "yaw": 90}`), drawn
  over a lit Tripo model made from words - not over grey blocks (flat) nor from 12° above (wide floors beside side-view characters).
- **A review of the scripts, fixed** *(the user chose every item)*:
  - **A creature's walk `step` was 6-19 % off, so feet slid**: it is measured from the planted foot only now (an animal's paws in the
    frames they are down, fitted against the leg's phase; a person's heel while the sole is flat). Checked against 24-frame renders:
    within 1 %. guard 83.7 → 94.2 game px, herbalist 82.3 → 89.4, kid 44.2 → 47.4, stag 61.1 → 59.5; `cut` measures an old guide again.
  - **A side view's mirrored facing was half a cycle off its east one** (west climb started on east's frame 4: the hands swapped at
    grab → climb; a looped action's effect was off its body). West is now east's exact mirror, frame for frame, and is not rendered at
    all (a side-view action renders in about half the time).
  - **`creature.py` reused stale files before a paid drawing** (the man's rig kept after switching to "woman"; `walk` drawn on a guide
    fitted to the design before `design --again`): it copies again or refuses, before any cost is shown.
  - `creature.py`: stops when onnxruntime is missing instead of cutting by white alone; keeps a creature's loose pieces (drops, leaves);
    a sheet takes its own scale (one with no `height` was drawn 1.6-2× too big); a person's head is found under a hat or a spear's tip;
    an empty frame or a refused drawing gives a message, not a traceback.
  - An air action's water splashed on an invisible floor at her boots: it falls to the real ground now. The depth pass rendered on
    another canvas than `render` (a trail action's head mask 1.33× too big) and ignored `head_up`. Rendering "jump" deleted
    "jump-cut"'s trail renders. A frame touching the top edge wrapped round when lifted to the floor.
  - `export.py`: an effect sheet over 4096 px is split into sheets that fit (24 cells of a long water swing were one 4608×3912 sheet).
  - `isoprop.py`'s standing-person prompt said "arms hanging" and "its nose block" for every pose: it follows the pose and the body now.
  - Faster: the white key 19× (identical masks), the AI cut-out per cell only where paper is shut in, cached (`cut` 82-123 s → 35-79 s,
    a repeat 5-13 s), `flip_onto` 4×, a trail action's `finish` a quarter of the memory, a posed figure built once.
- **Fixed: `isoprop.py draw` ignored `SPRITECAST_DRAW=manual`** - it called the API directly (asking for a key) though the docs said
  every step could be drawn by hand. It now goes through the same hand-drawing page as the rest.
- **Fixed: `charpipe.py sit --draw` with `"facings": 4` or `"cardinal"`** always stopped asking for `render/sit-south.png`, and
  quoted two sheets where one is drawn. It checks the first facing's render and draws one sheet for four facings (~$0.11).
- **Costs agree everywhere** - the README, the guides and SKILL.md quote what each script's gate prints (a prop $0.08, a further facing
  $0.09; a walk's drawing ~$2.1; a side view's walk and standing ~$0.33); a side-scroller's monster ($0.18) and hero rows added.
- **README**: a second game made with it - *The Castle Wall*, a side-scroller made in about a day as an example of what you can build; the banner's second
  scene is that game (filmed from it, the title washed by its rain and wetted by her cut); the first picture gained a row of the
  side-scroller's creatures and people beside the mannequins they were drawn on; scenery seen from the side drawn over its own lit 3D
  model (drawn over grey blocks, the castle wall came out flat).

- **GPT Image 2.6 is the default** *(the user's decision: "switch everything to 2.6 - the earlier judgment that 2.5 was better
  looks like an error")*. `gpt-image-2.6-sunburst` draws everything (characters, props, pixel art);
  `SPRITECAST_MODEL=gpt-image-2.5-sunburst` is the one before. The same price per token, and the same cost a sheet where it was
  measured ($0.23 for three sheets, $0.36 for four, with either). On the rain girl in a side view it kept closer to the guide: a
  walk's overlap 0.94-0.96 against 0.90-0.94, a two-move umbrella combo 0.66-0.89 against 0.53-0.81, the held thing off its place
  in 1 frame against 5. One character, one run each; what 0.14.1 found against it (a walk's second sheet repeating the first
  half's arm) has not been drawn again ([reference/tips.md](skills/spritecast/reference/tips.md)).
- **A side view: `"view": "side"`** *(the user: "let's extend our way to 2D games")*. For a side-scrolling game: the camera level,
  straight from the side (`"pitch"` 0), the head level (`"head_up"` 0), ONE facing drawn - east, walking to the right - and west
  flipped from it, also with a thing in the hand (`"mirror": false` draws west too). A walk is 2 sheets and the standing view 1,
  where eight facings take 18. The feet of every frame come out on one line (1 px of 256 apart). No shadow: a level camera sees the
  ground edge-on. `"turn": 45` turns the body that many degrees toward the viewer while it walks sideways (0 a flat profile; at 30
  one eye shows, at 45 both, at 60 the stride closes up) - and a cut made across the body, hidden behind it in a flat profile,
  shows. Drawn for the rain girl at 0, 30 and 45: a walk's overlap 0.85-0.96. Not done yet: a jump cut into its rise and fall,
  the engines' files checked with it, sitting. `pixelart.py` draws east only in this view (it drew both facings: twice the cost for
  a facing the game flips); `charpipe.py sit --draw` stops with a message there instead of failing on a missing render.
- **A spin in a turned side view**: its frames with the back of the head in the render came back with a face. The prompt now
  says so; of four such frames 2.6 then drew two right, one half right. The guide is the cause that is left - a wide swing's
  figures are a quarter of their cell's height. `frame` draws one of them alone.
- **Fixed: a facing flipped from its pair (`"mirror"`) sat 60 px to the left of its render** since 0.9.0 - the reach of the search
  that lays it on its render had been written over the render itself, so every frame took the first shift tried. Overlap
  0.04-0.12 before, 0.78-0.90 after (a side view's west). `finish` again lays them right; nothing is drawn again.
- **Creatures for a side-scrolling game, drawn in 2D: `creature.py`** *(the user: "monsters straight in 2D"; then "could a plain
  mannequin - no fur, no detail, four legs - be baked for GPT to follow?"; then "the leg length changing is the biggest thing")*.
  One design in the look of a picture of the game; a four-legged creature's 8-frame walk drawn on the poses of a plain dog mannequin
  that comes with SpriteCast (`mannequins/dog.glb`: grey, near legs red, far legs blue, no tail), first stretched to the design's
  own leg length, body depth and neck (`mannequin`, free); any other animation as a sheet of four moments in words. ~$0.06 a
  picture, no 3D model per creature. A stone wolf's frames came out within 3 px of the mannequin's places. Drawn on the dog as it
  was, a boar and a stag both got a dog's legs; fitted (legs x0.44 and x2.32) each kept its build. A salamander did not work - what
  stands with its legs out to the sides needs its own mannequin and gait. In a character spec: `"mannequin": true`, `"fit"`
  ([reference/creature.md](skills/spritecast/reference/creature.md)).
- **People on mannequins too, and the block figure gone** *(the user: "man and woman mannequins too, bald, to see whether the motion is
  followed"; "put the mannequins in the skill and replace making a person from blocks"; "a child one too")*. Three bald, plain figures
  come with SpriteCast - `mannequins/man.glb`, `woman.glb`, `child.glb` (a GPT turnaround, Tripo's model and rig). `creature.py` draws
  a person's 8-frame walk on them (`"mannequin": "man"`...): a cloaked guard and a herbalist in a skirt followed every pose and kept
  their details; each frame is moved across so its head is over the mannequin's (the drawing sat 17-49 px off). And a standing person
  (`isoprop.py`, a `character` spec) is now one of these figures in the pose - `"body": "man" | "woman" | "child"` - where it was a
  figure of boxes and round limbs (`"body": "blocks"` keeps that). The poses are the same numbers, set on the rig's bones; a palm can be
  turned (`"palm"`; a wave's hand faces forward) and **an arm no longer passes through the body or the other arm**: what overlaps
  after the pose is set is pushed apart *(the user: "arms crossed, the hands go through each other - can that be stopped?")*. Drawn
  once this way: a waving boy on the child, front and back, finished with no warning. Tried
  once in an isometric view: the guard drawn on the man's walk seen from above came out in view and pose in three facings.
- `creature.py` cuts its figures out with the AI cut-out's help *(the user: "the white between her legs is still there - isn't the AI
  cut-out used here?")*: the paper shut in between limbs is told from white clothes by it, and loose pieces (drops, mist, leaves) are
  kept by the white key. A person also gets `out/stand.png`, and a sheet can be of a character (`"noun"`): the game's heroine struck,
  and worn out, were drawn from her standing picture.
- **A side view's actions**: an action's own `"fps"`, `"head_up"` and `"canvas"`; `"face": "away"` (a ladder climbed with the back to
  us); `"in_place"` (the hips' height pinned); `"air"` (a jump's frames, each on the ground line - the game moves her); a thing
  carried `"on": "back"`; `"floor"` (on in a side view: a pose whose feet the clip sinks under the ground is lifted onto it, in the
  render and again in `finish`); `motion.py layer` (one clip's upper body on another's legs). `render` warns when a figure or what
  it holds is cut by the picture's edge - a jump's raised umbrella was, and was drawn cut.
- **Fixed in a side view**: west is the exact mirror of east, frames and effect alike (laid onto its own render it jittered up to
  100 px a frame and left the water of a cut on the wrong side); an in-between action was packed as a loop (its mirrored frames in
  the wrong order); an effect's sheet came out one column and 15,000 px tall - `export.py` now lays it out near square.
- A side view's standing sheet says how many figures it has (one), and SpriteCast's idle clip is made once for each `"head_up"`
  (a spec whose `"head_up"` changed kept the clip made for the old one: the head bowed).

## 0.28.1 — 2026-11-26

- **Drawing by hand: the references first, then the guide** *(feedback: "give it one picture first, say we draw in that style, then
  the next")*. A sheet drawn in the ChatGPT app (`--manual`) is now two messages in one chat, both shown on the page with their own
  copy buttons: the reference pictures (the turnaround; for later sheets the first sheet too) with "do not draw yet, answer ready",
  then the guide alone with the prompt, which points back at "the picture in my EARLIER message". 0.28.0 sent the guide alone,
  because two pictures in one message were both put on the canvas - and the app then drew plainer than the API. Tried on Rain
  Girl's first walk sheet (the free plan): the three figures stayed where the guide has them, the turnaround did not come into the
  picture, and the coat got its buttons (about 47 tones against 41 with the guide alone, 50 through the API). The figures cover the
  guide a little less well (0.85, 0.84, 0.80 against 0.85, 0.87, 0.84) and the head turned a little more to the side. Not tried
  yet: a later sheet, whose first message carries two pictures. `SPRITECAST_MANUAL_GUIDE_ONLY=1` is 0.28.0's one message.

## 0.28.0 — 2026-11-26

- **No API key: draw in the ChatGPT app by hand** *(feedback: "people who subscribe to ChatGPT and want to save money")*.
  `pixelart.py CHAR.json --manual` (any other step: `SPRITECAST_DRAW=manual`) calls no API and spends nothing. Each sheet becomes a job
  on a local page (127.0.0.1:8790): the picture to attach and the prompt with a copy button. The user draws it in a new ChatGPT chat
  (the free plan works, within its limits) and saves the answer; it is taken from ~/Downloads by itself (or dropped on the page),
  fitted to the sheet's size, and the run goes on. Given two pictures the app put both on one canvas (the guide's figures shrunk to
  the left, the turnaround redrawn beside them), so a redraw on a guide goes with the guide alone, the sentences about the other
  pictures cut and the layout spelt out (`SPRITECAST_MANUAL_ALL_IMAGES=1` keeps them all). Tried on Rain Girl's walk (south-east,
  8 frames, three sheets, the free plan): the same character all through, read on the grid like the API's - but plainer (fewer
  shades, no buttons; the app draws coarser squares) and a frame came out a little small. `scripts/manualdraw.py`.

## 0.27.0 — 2026-11-23

- **Four facings, your four: `"facings": "cardinal"`** *(feedback: "some users will want only north, south, east and west")*. Beside
  `4` (the diagonals), a character can be drawn in south, east, north and west only - about half the drawing, like the diagonals. The
  exported character still takes all eight directions and shows the nearest drawn (south-east: south or east, the one shown last
  kept, so moving diagonally does not flicker). `touchup.py` now finds a four-facing set's standing views on their one sheet (it looked
  for them as if there were eight).

## 0.26.0 — 2026-11-21

- **Smooth versions of the new tools** *(feedback: "make smooth versions of everything")*, for a game drawn as illustration, not
  pixel art. `ground.py`: `"style": "smooth"` - the meadow rendered at 3x and averaged, light and greens continuous, the palette's
  colour without its steps, soft-edged front strips; terrain and puddles as gradients; grass2d unquantized. `translucent.py`:
  `--smooth` / `"style": "smooth"` - alpha from thickness without steps (a little blurred), the edge alpha a soft gradient.
  `propanim.py`: a smooth prop (finished with isoprop.py) or `--smooth` - the sheet is the poses' renders on magenta, the prop's own
  sprite the style to copy; each cell cut out softly, put back where its render was, each sheet's scale matched to its renders (a sheet drawn 5 % bigger made the loop pop).

## 0.25.0 — 2026-11-21

- **The ground: `ground.py meadow | terrain | puddles | grass2d`** *(feedback: "the grid should be iso and not show", "natural, like a
  meadow", "in the style of our trees")*. Free, nothing drawn by an image model. `meadow`: a meadow of 3D grass, ferns, wildflowers
  and clover - Tripo-made, coming with the skill in `ground/realistic` (MIT) - planted by a Gaussian density, a path of earth, wheel ruts
  and 3D gravel, lit by the props' sun with the plants' shadows, pixel art in the user's own palette; one picture of the whole map (no
  tile: no repeat, no grid). Its plants come cut into strips by their roots (`ground-front.*`), so the grass hides a character's feet
  and a tree's foot *(feedback)* - not a fire's or a ghost's. `terrain`: the ground's rise and fall from a 3D height map. `puddles`: a
  shallow hollow of water, five sizes of one shape. `grass2d`: one grass tile's tufts scattered the same way, no 3D. reference/ground.md.
- **See-through by 3D thickness: `"translucent": "fire" | "ghost" | "water"`** (`translucent.py`, presets/translucent.json) *(feedback:
  "fire could take an alpha", "lowest 0.05, highest 0.8")*: each pixel's alpha from its own 3D model's thickness, in fixed steps; a
  `"pulse"` lets the thin parts fade now and then; `--edge` for a drawing with no model (a flame, a fireball).
- **A creature that moves, from its own model: `proprig.py` + `propanim.py`** *(feedback: "a rig?", "side to side, a little, like a
  snail", "the arms to and fro, together")*: bones found in the mesh (a chain along the tail, the arms), a loop of poses rendered, drawn
  four frames to a sheet (they match), alpha pose by pose; exported to Phaser and Godot like the wind. What did not work, and is not
  offered: bending the drawn sprite itself by the model (it looked melted).

## 0.24.0 — 2026-11-21

- **Rain Girl's combo as a preset: `motion.py preset SPEC.json rain-girl-combo`** *(feedback: "keep only how much it changed, so others
  get mine by taking that preset")*. `presets/rain-girl-combo.json` keeps what was done to Mixamo's two moves - the axe chop made a
  sword cut (bend 0.55, lag 0.9, the stroke 0.75-1.25 s), the feet on the ground, the backhand started from the cut's pose at 1.40 s
  (its 0.3-2.0 s, blended over 0.4 s) - and the two actions; never the moves themselves (Mixamo's may be used, not handed on). The
  user downloads the two FBX files; the preset carries them on and makes the same changes. Built from scratch it matched the game's
  rig within 3 mm. Missing a file, it says which to download from Mixamo and how.
- The README says which Mixamo moves to download and with which settings, and that SpriteCast comes with no moves.

## 0.23.0 — 2026-11-21

- **A swing's effects as a set: `fxpack.py export --set water-swing | fire-swing`** *(feedback: "the right one looks better - keep this
  pairing, fire and water")*. What a swing round the character plays together, at 2x, with fx.json's `"sets"` saying when each starts
  and on which layer: water - the shockwave ring and the water's ripple on the ground (the ripple 100 ms after, from its third cell),
  the spin slash round her; fire - the pack's own flame ring (its flames stand up: the far half behind her, the near half in front) and
  the spin slash as fire. `preview --set NAME` shows them as the set plays them.
- **`fxpack.py --fire`**: an effect's lights and darks to a fire's colours. `--hue` turned the blue ring a washed-out pink.

## 0.22.2 — 2026-11-21

- **Fixed: `pixelart.py --again NAME` without `--yes` deleted the drawn sheet** and drew nothing - asking what a redraw would cost lost
  the sheet. The old sheet now stays until the new one is drawn (with `--yes`).

## 0.22.1 — 2026-11-20

- **A speck that came apart from the figure goes** *(feedback: "the umbrella's tip pokes out at the upper left for a moment" in the README's
  combo)*: a thin end made small (an umbrella's tip, a sword's point, a strand of hair) could be left as 1-3 pixels on their own beside the
  figure - and a pixel put in by hand in `pixeledit.py` stays where it was put when the frame is drawn again with the thing moved (grey
  painted on the umbrella's tip over a white speck, the swing then made again: the one the user saw). `pixelart.py` now takes off, after
  the hand's edits, whatever does not touch the figure, not even at a corner, and is 3 pixels or fewer, and says how many and how many of
  them were put in by hand. Kept with `--keep-specks` or `"keep_specks": true` in the spec (dust, sparks meant that small). A swing's water
  and the shadows keep their drops.

## 0.22.0 — 2026-11-20

- **Attacks that join** *(feedback: a second swing for Rain Girl's combo - "the moves between the attacks look odd", "the legs change too
  abruptly", "made for an axe")*: `motion.py`, free, on the rig. `ground` puts a carried Mixamo clip's feet on the ground (it stood 8-15
  cm in the air), `plant` holds the feet where they stand and gives the hips' turn to the spine, `link` starts one move from the pose the
  last one is in - its difference fading out inside the wind-up, the stroke untouched (how games join a combo) - `blade` makes an axe's
  chop a sword's cut (less bend; the blade running on from the arm on an arc round the shoulder), `join` makes a combo one clip to
  render at 24 frames a second and look at. reference/character.md, "Moves that join".
- **253 pixel effects come with SpriteCast** - [PVFX Foundry](https://nerijs.itch.io/pvfx-foundry) by Pixel VFX Studio, CC0 1.0, its
  strict tier (`effects/pvfx/`): hits, splashes, fire, explosions, ice, lightning, smoke, sword trails, projectiles, pickups. `fxpack.py`
  finds one, shows it, and writes it out for a game at the sprites' pixel size, in their colours if asked (`--palette`, `--hue`). Rain Girl
  plays nine of them; a ring round the girl is cut at its middle, the far half behind her. reference/pixel.md, "Effects from the pack".
- **A long thing swung far is drawn, not left out**: a frame too wide for two to a sheet gets a sheet of its own; a frame too tall (an
  umbrella straight up over the head) a sheet of its own standing up (1024x1536). Before, the whole facing was left out - and a frame
  that fitted no sheet ran on into the drawing and stopped it half paid; now it is named and left out.
- **A swing's water fades out with the distance from the figure** instead of being cut in a straight line where it ran off the render's
  frame; an action with `"trail"` renders in a 1024 px frame (768 before) and `render` says when its trail still runs off.
  `"trail_reach"` in the action sets how far it shows (Rain Girl's combo: 2, the user's "twice as far"; the frame grows with it).
- **Fixed: the first frame of a swing with a trail showed an arm raised straight up.** three's mixer writes a bone only when its value
  changed; the shoulders lifted after each pose were never undone on a bone the clip holds still, and tracing the trail poses the
  swing 200 times first. The pose is now put back before every new one (and after the hand's check shots). Renders without a trail
  come out the same to the pixel.
- The rain girl's downward cut and backhand, four facings, 64 frames with their water - one person throughout - made with all of it.
  The README's banner shows the combo now: the cut's water bursts on a mushroom, the backhand's ring sweeps round her and wets the title.

## 0.21.0 — 2026-11-19

- **How deep a shadow is can be set** *(feedback: on Rain Girl's dark, rainy ground the baked shadows were lost and the sprites looked
  as if they did not stand on it)*: `"shadow_strength"` in a prop's or a character's spec, `--shadow-strength` on `proppixel.py`,
  `--strength` on `propshade.py`, and a slider in the light editor (`lightedit.py`), kept in the spec on Save. The number is how many
  times the shadow is laid over itself: 1 as the light gives it, more for dark ground, under 1 paler. Free: nothing is drawn again. A
  character's `shadow_alpha` in character.json goes with it, so the exports show it right.
- **Pixel art's shadows are 1.5 times as deep by default** (56 % at their deepest -> 71 %, 10 % at their far edge -> 15 %): pixel art says
  things a little louder than they are. **It changes how a pixel prop's and a pixel character's shadow looks the next time it is
  baked** - `"shadow_strength": 1` gives the old one. Painted character sets and smooth shadows stay at 1. The README shows why, the same
  tree and character at 1, 1.5 and 2 on dark ground and on a pale floor.

## 0.20.0 — 2026-11-18

- **Rain Girl is playable**: the game made with SpriteCast runs in the browser, with a leaderboard - linked from the README
  ([play](https://sunghwan0112.github.io/rain-girl/), [code](https://github.com/Sunghwan0112/rain-girl)).
- **A character's shadow is light as it falls now**, like a prop's baked one: the posed 3D body is pressed onto the ground along 16
  directions across the sun's disc and 48 across the sky, and what each hides is added up - so it is deep where the feet stand and
  under the body, and pale out at its edge, not one hard shape at one strength. Frame by frame, free as before. character.json says how
  dark to show the strips (`"shadow_alpha": 0.56`); the Godot, Phaser, Unity and Aseprite exports read it. Pixel sets get it in five
  steps. **It changes how every new character's shadow looks, and the render takes longer** (64 passes a frame: ~9 minutes for a
  character with three actions, where it took about one). `"shadow": "flat"` in the spec keeps the old one. Sets made before stay as
  they are until rendered again; seated shadows are still the hard shape.
- **A prop's 3D model now gives the game its rules too** (free, baked with the shadow). `solid-<side>.png`: where a walker cannot stand -
  the prop's footprint, cut from the model below 0.4 m (a trunk's foot, a table by its four legs). `"collide": {"cover": [0.55]}`:
  `cover-<h>-<side>.png`, what stops a thing flying at that height - a trunk does, the crown over it does not. Each with its place and
  an outline for a collision polygon in pixel.json; `preview-collide.png` to look at. Made for Rain Girl, where fireballs break on
  trunks and rocks.
- **A character in a prop's shade**: every baked shadow now says how to read it for a point above the ground (`per_m_up`, `height_m`),
  so her feet, middle and head each darken by what stands between them and the sun.
- **Pixel props into an engine**: `export.py PROP/out-pixel` writes a Phaser 3 module and a Godot 4 scene with the shadow, a lamp's
  light, the wind, the footprint as a collision polygon, and `shade` / `cover` to ask. Opened and checked in Phaser 3.90 and Godot 4.7.
  Unity and Aseprite: characters only, as before.
- **The wind in a small thing** (`"sway": "caps"`; chosen by itself under 700 moving pixels): mushrooms nod at the cap. Their parts are
  read off the sprite - the model cannot part them at 20 px - and lifted as they move, so no second edge shows.
  [`examples/forest_mushrooms`](examples/forest_mushrooms).
- **The wind in a pixel prop, from its 3D model** (`"sway": "leaves"`, `propshade.py --sway leaves`; free): the crown's leaves are cut
  into clumps from the model - each leaf pixel takes the model's point it shows, the points grouped by where they are in 3D, the near
  boughs apart from those behind - and every clump moves whole, a pixel at a time, far ones laid first, the trunk still; a gust leans
  the top clumps. No warp of the picture, no drawn frames. A moved clump takes its edge with it - the dark line round
  the crown goes with the clump beside it, and the leaves a clump leaves behind are taken off at the crown's edge (kept inside it) -
  so no second outline shows. `sway-<side>.png` (12 frames x still / breeze / gust), `clumps-<side>.png`
  and each clump's place for a game that moves them itself, `preview-sway.gif`. Made for Rain Girl's forest, where a sheared and then
  a rippled crown both looked wrong. `examples/forest_tree` shows it, with leaves that let light through its shadow. *(feedback)*
- **A pixel prop's shadow, baked from its 3D model** (`propshade.py`; `proppixel.py` runs it itself, free, a few seconds a prop): the
  light on the ground is the sun's part and the sky's, each as much as the thing leaves open - so the shadow is deep close by (under a
  cart, round a trunk's foot) and paler where it falls from high up (a tree's crown, light coming through between its leaves), in
  five steps of pixel art; the sun the size of the real one, so a bare branch's shadow comes out sharp. The sun is
  the guide's own light, so the shade drawn on the prop and its shadow agree. `--shadow overcast` for a grey day (no sun: only the
  soft dark round it), `none`. `shadow-<view>.png`, where it sits in `pixel.json`, `preview-shadow.png`. Made for a rainy forest game,
  where a flat shadow of one strength looked pasted on. No new package: the model is read by the skill itself. *(feedback)*
- **Indoors, a lamp where you put it** (`--lamp x,y,z --lamp-size r`, or `"lamp"` in the spec): the shadow falls away from it,
  longer the lower it hangs, sharp from a bare bulb, soft from a big shade, fading with its light across the floor. Without it, the
  sun. *(feedback)*
- **See-through parts** (`"see_through": [{"colour", "open"}]`): a wicker weave or a crown of leaves is only painted on a model;
  the parts of that colour now let that share of the light through. A rattan peacock chair (`examples/rattan_peacock_chair`, a Tripo
  model, pixel art) shows it under six lights. *(feedback)*
- **`lightedit.py`: move the light yourself** - a page on your computer with the prop on a floor: drag the lamp, lift it, size it,
  and the shadow is redrawn as you go; Save bakes every side and keeps the light in the spec. propshade.py works it out once
  (`prepare`) and then each shadow in ~0.15 s; `pixel.json` now says where each side's footprint middle is (`"foot"`), where a
  lamp's place is measured from. *(feedback)*
- **A lamp's light on the floor, baked too**: `light-<side>.png` - brightest right under the lamp, falling off as it really does
  ((h/d)^3), the prop's shadow cut out of it, its steps dithered so no rings show; lay it on the floor with ADD. The light editor
  shows the floor lit by it. *(feedback)*
- **The lamp itself, for a game**: `lamp.png` (the light as pixel art: a core its size, a warm rim, a dithered glow) and where it
  is in every side's pixels (`pixel.json`: `lamp`, each view's `lamp.at` / `lamp.spot`), so a game can draw the floor, its light,
  the shadow, the prop and the lamp as the editor showed them. *(feedback)*
- **Your own lamp in the light editor**: load a picture of it, click where its light comes from, and drag it round the prop - it
  stands on the floor in front or behind as it should, its light from that point; saved in the spec and given to the game
  (`lamp.png` is then yours, with its foot and light point). Mark its light or its foot with a click on it (a ring shows the light's
  size, a red cross where it stands); scale it 0.25-3x - up by whole pixels, down by SpriteCast's pixel reducer - its height in
  metres shown. Lamps loaded are named and kept (`~/.spritecast/lamps`, for every prop), each a button; "Save this
  lamp's settings" keeps how it was set; "Bake & save the scene" and the page opens as it was saved. "Delete this lamp"
  (two clicks). Any picture loads (PNG, JPG, WebP): a plain background is cut away, pixel art shown enlarged goes back to its
  own pixels, one far too big or small starts at ~1.5 m. A pixel floor lamp to try (drawn by GPT from an iso block guide, `examples/lamps/floor_lamp.json`) is in `examples/lamps/floor_lamp/out-pixel/sprite.png`. *(feedback)*
- **Pixel or smooth light**: `"light_style": "pixel"` (steps, dithered - the default) or `"smooth"` (gradients) for the glow and the
  floor's light - and the shadow itself: five steps, or a gradient for a game not in pixel art (`--style smooth`); a switch in
  the editor. *(feedback)*
- **A weave is read with its model** (props with `see_through`): the palette had folded GPT's white paper into the rattan chair's
  cream, so the white-speck rule found none - and the AI cut-out had cut into the cushion where it met the arm. Now each pale pixel
  and each cut-out hole inside the thing asks the model what is there: the front surface, and what lies behind it. Pale where the
  model is not white is paper: the floor shows (see-through) if nothing is behind, else the cushion or the far side of the weave, in
  the sprite's own colour; a pale piece the model has white (the cushion) stays whole; a hole where the front is solid is filled. On
  props without `see_through` nothing changes (the forest props came out pixel for pixel the same). *(feedback)*

## 0.19.1 — 2026-11-17

- **A pixel prop's white specks are cleared by its render**, as a character's are: the AI cut-out took the gaps between a tree's leaves
  for leaves and left them white. White where the render has nothing is made see-through, white where it has the object in a dark
  colour is painted the colour beside it, a light part of the render stays. A forest tree in four views came out as clean as by hand. *(feedback)*

## 0.19.0 — 2026-11-17

- **SpriteCast's own standing idle, by default.** `idleclip.py` makes a relaxed stand - the feet side by side, the shoulders let down,
  the arms close by the body - and a seamless 4 s loop of a breath and a little sway, for any rig with Mixamo's bone names; `render`
  adds it to a copy of the rig by itself (`<rig>-idle.glb`, free) and the standing views use it. The arms and shoulders were set
  beside a Mixamo "Standing Idle" (the same to 1-3 % of the height); its stand on one foot was not kept - seen from the side of the
  held thing's hand the figure came out a fifth thinner, the legs one behind the other. The motion is all made here, nothing of
  anyone's animation in it (Mixamo's files may be used, not handed on). Still thinner from that side by the arm that holds the thing
  in front of the body (the rain girl, south-west against south-east) - one hand holding something is not symmetric. `"idle_from": "tripo"` keeps the rig's own. An action can stand with something in hand on it:
  `{"name": "stand", "clip": "idle_spritecast", "frames": 3, "loop": true, "hold": ...}`. *(feedback)*
- **addclip.py carries a Mixamo FBX over by direction**: each bone turned to point where the FBX's points, in the two bodies' frames.
  A download WITH its character (a skeleton per mesh, the bones out of their bind pose) held the arms out from the body before; it
  now stands as in Mixamo. The throw it was made for came out as before. *(feedback)*
- **A hand the body hides is not drawn raised**: the pixel sheets say a hand goes on a held thing only where the cell shows one; an
  action on the SpriteCast idle gets, in the facings that turn the holding hand away, a sentence of its own. *(feedback)*
- **pixelart.py names a swing effect missing in some facings**, with the free command that renders it. *(feedback)*

## 0.18.0 — 2026-11-17

- **A held thing in the same colours in every pixel frame.** `pixelart.py` gives each part of what is held - an umbrella's handle,
  shaft, canopy, tip, read off its render - the same tones in every frame, shaded as drawn. The rain girl's umbrella had come back
  in four yellows across her facings and its shaft silver in some. Only the thing is touched: not the hand round it, the hair, the
  coat beside it or the outline. Free, by default; `--held-as-drawn` leaves it as drawn. *(feedback)*
- **Its colours from the frame you like:** `"colours_from": "carry-south-east-1"` in the `hold` takes each part's colour as drawn
  (and edited by hand) in that frame; `"handle"`, `"shaft"`, `"tip"` still name one outright. `"as_drawn": [frames]` leaves frames
  as drawn, for painting by hand. *(feedback)*
- **pixeledit: the drawing as it was, beside it and under a brush.** "as drawn beside" (5) shows the frame before the held thing's
  colours, with the 3D render and the edited frame side by side as wanted; the *as drawn brush* (O) paints it back where it is
  rubbed. Every build keeps it in `pixel/drawn-<px>/`. *(feedback)*
- An action's `"frame_words"` now reach the pixel sheets too (`pixelart.py --again <sheet>` to draw one anew with them): the rain
  girl's south-west swing lost a hand across her chin with "BOTH hands hold the umbrella". *(feedback)*

## 0.17.0 — 2026-11-17

- **Four facings: about half the drawing.** `"facings": 4` in a character's spec renders, draws, finishes and packs only the four
  diagonals (south-east, south-west, north-east, north-west): a walk about $1 instead of $2, in pixel art about $0.7 instead of
  $1.35 (the rain girl's umbrella walk and swing: 21 pixel sheets, ~$1.57, instead of 48, ~$3.60). South-east is drawn first and the
  rest follow it. `pixelart.py` draws the spec's facings. *(feedback)*
- **Every engine still takes eight directions.** `export.py`'s play() - Godot's `<name>.gd`, Phaser's module, and for Unity the new
  `SpriteCast/SpriteCastFacing.cs` (`SpriteCastFacing.Play(animator, "walk", "east")`) - shows the nearest facing a set has. Between
  two as near (east: south-east or north-east) the one shown last stays, so walking straight across does not flicker; with none shown
  yet, the one turned more toward the viewer. Checked in Phaser 3.90 and Godot 4.7 with a four-facing set; the Unity script compiled
  against Unity 6000.3's own libraries. A set with all eight plays as before.

## 0.16.1 — 2026-11-17

- **A swing's effect stays with the drawn umbrella.** The effect's extra cells (water has three to each body frame) now sit around
  the body frame's moment - a third of a frame before it, on it, a third after - instead of all after it. The drawing holds one pose
  for all three, and with every cell after it a fast swing's water was already down at her feet while the drawn umbrella was still
  up. Now the water is at most a third of a frame away, and as often behind the tip as ahead. Free, nothing to change in a spec;
  render again to get it. *(feedback)*
- The rain girl example's water, 2D in all eight facings and the pixel one, rendered again this way. (Its drawings come from renders
  made before 0.14.0's hand closing on the handle, which sits the umbrella about 20 px further into the fist; its water was rendered
  with the umbrella where the drawings have it.) Its south-east swing, 2D and pixel, is now the redrawn one the README's loop already
  showed - the shaft as thick as the render, the left hand on it in frame 5 - and the README's effect pictures (`effects.gif`,
  `effects-pixel.gif`) and joined loop (`loop-2d.gif`) are made again from it with the new timing.
- The README's first picture: the "GPT alone" side smaller and stamped, each of its failures with what SpriteCast does instead; on
  the SpriteCast side a winter night behind the floor, a row of actions from the same 3D (run, jump, the swing with its water) and
  the pixel swing with its water.
- The README in four more languages: 简体中文 (`README.zh-CN.md`), 日本語 (`README.ja.md`), Español (`README.es.md`) and Português
  (`README.pt-BR.md`). Each links to all the others, and the pictures with words in them are in each language too, as the Korean
  ones were.
- **Animations that play one after another, fixed as one**: `pixeledit.py CHAR.json --join walk,ready,slash,recover --facing south-east`
  opens their frames end to end, to play the whole loop and fix a part where it jumps - across a join as well as inside one. Each
  edit goes to its own animation's frame. *(feedback)*
- The README's pixel hand-work said as it was: only the held umbrella was fixed (its tip and edge), the character not, beyond a few
  left-over white specks; a few minutes' work. The "about 60 minutes" in 0.16.0 counted edits lost when the editor was stopped
  under them and drawn again.
- The README's joined loop (`loop-2d.gif`) without the blotches on her face: one palette for every frame, the water's blues among
  it, had left the skin a few tones. Each frame now has its own - and so does `charpipe.py loop`'s GIF, where such blotches could be
  taken for the image model's and a frame drawn again for nothing.
- The README's banner: the swing at 0.85 of its speed, the letters hop where the snowball and the water hit, the wet ones drip, and a
  winter night stands behind it all.

## 0.16.0 — 2026-11-16

- **The frames between two animations**: `{"name": "ready", "between": ["walk", "slash"], "frames": 3}` - the 3D rig's poses
  part-way from the walk into the attack's first pose, and `["slash:end", "walk"]` back out of its last. Rendered free, drawn like
  any action. A walk into a swing no longer jumps. *(feedback)*
- **The pixel editor shows where the 3D has things** (key `4`): the held thing in red, the body's outline in blue, over the frame
  being drawn. *(feedback)*
- **Animations joined into one GIF**: `charpipe.py loop SPEC --only walk,ready,slash,recover --facing <f>` (free) - a walk into an
  attack and back out, with shadows and the swing's effect, to look at the joins.
- **One frame drawn again alone**: `charpipe.py frame SPEC --only <action> --facing <f> --frame <n>`, and `"frame_words"` in an action
  for what that frame's render cannot show. A hand hidden behind the head, which the image model pulled up into sight five times, came
  right once its frame said it was hidden. *(feedback)*
- The umbrella's shaft and tip can be given colours (`"shaft"`, `"tip"`).
- The README's banner: on the left the pixel rain girl now walks with her umbrella, swings it and throws water that wets the title.
- A new README example, all drawn: the rain girl walks with her umbrella, goes into the stance, swings with water, comes back up. And
  the same loop in pixel art, with what it took by hand said plainly (1,196 pixels of 51,442, 2.3 %, about 60 minutes by someone who
  does not draw).
- A drawn sheet of fewer than four frames is cut where its figures really are: the image model may spread three figures over the
  whole width, and the fixed quarters cut through two of them.
- The umbrella's sentence asks for the silver shaft as thick as the render has it, also where the coat hides part of it (it was
  drawn as a thin wire). Effect pieces (mist, sparks, snow) no longer have a grey rim on a light floor.
- Not checked: in-between frames for an action whose clip `pack` takes its frame rate from (it takes the walk's).

## 0.15.0 — 2026-11-16

- **Files your engine opens as they are.** `export.py <name>/out` (free) writes a Godot 4 scene, a Unity folder whose editor script
  builds the prefab and a clip per animation, an ES module for Phaser 3, and one `.aseprite` an action (a tag per facing, layers,
  the feet marked). Each animation's shadows become one strip with one offset. Opened to check in Godot 4.7, Unity 6000.3,
  Phaser 3.90 and Aseprite. Pixel sets are not exported yet.
- **Effects on a swing**: `"trail": "water"` in an action that holds something - `plain`, `wind`, `water`, `fire`, `drops`, `flames`,
  `leaves`, `greenleaves`, `petals`, `snow`, `sparkle`. Free, nothing drawn, and it follows the real motion: worked out from the
  path the held thing takes on the rig in that action and facing (not one stock arc), a sprite of its own over the body, so an
  action already drawn gets one. Pieces fly on from frame to frame; water and fire move as one
  body (a sheet that tears into strings and drops, with mist; a flame coloured by its heat, with ash); only the swing itself, not
  the wind-up; water and fire at twice the body's frames. In pixel art too (hard edges, mist see-through). The exports carry it as a
  third sprite. *(feedback)*
- The rain girl example has the water effect on her slash, and her pixel slash had white specks taken off by hand.
- Not checked: effects on a held thing other than the umbrella; your own piece pictures (`"image"`); a whole `pixelart.py` run
  writing the effect; Unity versions before 6.

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
