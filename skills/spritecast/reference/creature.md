# Creatures and people drawn straight in 2D on a mannequin's walk (`creature.py`)

A monster or an animal for a platformer or a side-view RPG, with no 3D model of it made: one design in the look of a picture of the
user's, then its animations drawn from that design. A four-legged one's **walk** is drawn on the poses of a plain **mannequin** - a
grey dog with no coat, no face and no tail, its near legs red (fore) and yellow (hind), its far legs blue and green - that has first been given the design's own
proportions. Every other animation (struck, falling apart, a hop, a drift) is a **sheet of four moments said in words**.

Frames face right; a game flips them. `scripts/creature.py`, steps `design`, `mannequin`, `walk`, `sheet`, `cut`, `preview`.
The same walk can be seen from above in 8 facings for an isometric or top-down game (`"view": "above"`), and drawn as pixel art
(`"pixel": 96`) - see the sections below.

## The spec (`<name>.json`)
```json
{
  "name": "boar",
  "style": "hero.png",
  "what": "a stout wild BOAR - a heavy barrel-shaped body carried low on four short thick legs, a big wedge-shaped head held low ... Standing on its four legs.",
  "height": 82,
  "sheets": {
    "hurt": {"height": 84, "moments": "it is struck and falls apart into wet leaves. FIRST: struck from the right - ... SECOND: ... THIRD: ... FOURTH: a low heap of wet leaves on the ground, still."}
  }
}
```
| key | what |
|---|---|
| `style` | a picture drawn in the look the creature is to have - a finished character of the same game is best. Only `design` reads it; everything after follows `design.png` |
| `style_words` | (optional) how that picture is drawn, in words, when the design drifts from it: "an anime film illustration with natural proportions: a thin fine dark line, smooth soft shading - not a cartoon mascot, no thick outline" took a first set of mascot-like monsters to the heroine's look |
| `what` | the creature, part by part, and how it stands. A walker: "standing on its four legs" |
| `height` | how tall the walk's FIRST frame is in the game, px (the heroine beside it: 144) - and a sheet's first frame, when the sheet gives none |
| `frames` | the walk's frames: 8 (default; two rows of four on the sheet), 6 or 4. A four-legged walk in 4 frames is the same four leg shapes handed round the legs - it reads as flicker; use 8 |
| `mannequin` | `"dog"` (any animal on four legs), `"man"`, `"woman"`, `"child"` - all come with SpriteCast - an animal's `.glb` of your own, or `false`: no walk of this kind - a blob, a cloud, a thing that hops: `sheets` only. **Left out, it is chosen from `what`**: the first of its words that names a man (or "he", "his"), a woman ("she", "her"), a child (a boy, a girl, a kid - or a man or a woman "of about eight", under 13) or an animal on four legs (a wolf, a boar, a horse ...); `mannequin` prints which word chose it. Words that name none of them (a slime, a ghost) stop `mannequin`: give it |
| `view` | `"side"` (default: a side-scrolling game, frames facing right) or `"above"`: a game seen from above (`"pitch"` 30°), every facing drawn - see Seen from above |
| `facings` | with `"view": "above"`: 8 (default), 4 (the diagonals) or `"cardinal"`. `"mirror": true` flips west, north-west and south-west from their pairs instead of drawing them (a figure the same on both sides) |
| `redo_below` | a person: 0.5 *(the user's figure, a rough one)*; **an animal has none - look at it** *(the user)*: its overlap is printed and kept, but antlers, a mane, a tail or a snout are not on the plain fitted dog, by a different amount for every animal. A walk's frame whose outline overlaps the mannequin's less than this is named by `cut` (LOW - look; `walk --again`) and the overlaps are kept in `creature.json`. Lower than a character's 0.75 (charpipe.py: a drawing over its OWN render) because clothes, hair and a cloak are not on the bare mannequin: the guard from the side 0.61-0.75; from above, 64 frames in eight facings 0.54-0.78 - all in the pose, the lowest with the cloak flared out wide behind (0.6 named five of them); as pixel art 0.72-0.86. A walk drawn on another guide than its own (a stag's, the mannequin fitted again after the drawing): 0.33 |
| `pixel` | the figure's height in sprite pixels (64-192): the walk drawn as PIXEL ART - see Pixel art. `"colours"` (32): the colours of the whole set; `"pixel_words"`: how the pixel art is drawn, in words |
| `noun` | `"character"` when the sheets are of a person who has no mannequin walk here - the game's own heroine, her standing picture put at `<name>/design.png` with `"mannequin": false`: struck and thrown back, worn out and sitting down, each a sheet |
| `turn` | a person: degrees the body is turned toward the viewer as it walks sideways (45; 0 a flat profile) - as a side-view character's `"turn"` |
| `sheets` | name → `{"moments": "...", "height": px of ITS first frame (left out: the walk's `height` - give it when the first moment is not standing up as the walk does: a crouch, a heap), "hang": true for a floating thing (frames hung from their tops - its rain falls under it)}`. **Every picture has its own scale**, from its own first figure: the model draws a figure at a different size in each (a person ~430 px tall in a walk's cell, 700-900 px on a sheet - the walk's scale made a sheet 1.6-2x too big) |

Files go to `<the spec's folder>/<name>/`: `design.png`, `walk-guide.png`, `walk-drawn.png` (seen from above or as pixel art: one of each
a facing - and a sheet - `walk-guide-<facing>[-<sheet>].png`), `<sheet>-drawn.png`, and `out/walk.png`,
`out/<sheet>.png` (strips of equal cells), a person's `out/stand.png` (the design cut out at the walk's height: what stands between walks), `out/creature.json` (each strip's cell, frames, `align`, and the walk's `step`).
`<picture>-ai.png` beside a drawing is its AI cut-out, kept (see The cut-out).

## Steps
1. **`design`** (PAID, ~$0.06). Look at it: from the side, facing right, all four feet on the ground, white all round.
2. **`mannequin`** (free). Reads the design's build off its picture - leg length (belly to ground), body depth (back to belly), how
   high and how far forward the nose is, each as a ratio to the distance between the fore and the hind feet - stretches the mannequin
   to it, renders its walk and lays the frames out as `walk-guide.png`. **Look at the guide beside the design**: legs as long, body
   as deep? This is the cheap step; the walk follows the guide. It also measures the walk's step (In the game) into `walk-guide.json`.
3. **`walk`** (PAID, ~$0.06). The creature drawn in place of each mannequin. `cut` prints how far the frames' middles are from their
   cells' (the stone wolf: 0-3 px; over ~15 the drawing left the guide). It will not draw on a stale guide: for an animal it stops
   when `design.png` is newer than `walk-guide.png` (a `design --again` after `mannequin`: the guide was fitted to the old design - run
   `mannequin` again), and for anyone when the guide is of other `frames`, another `mannequin` or another `turn` than the spec's now.
   A person's design is drawn FROM the mannequin, so there it only warns when `walk-guide.png` is newer than `design.png` (the mannequin
   rendered again after the design: fine if nothing about it changed, else `design --again` first). A drawing turned down by OpenAI's
   safety check three times stops with that said, the old picture left as it was.
   Every piece of a cell's drawing is kept (a drop, a leaf, a wisp) except those at the cell's left or right edge - a neighbour's nose or
   tail come over it. A cell with no figure in it (the model drew 7) stops `cut` with which frame it is: `walk --again`.
4. **`sheet <kind>`** (PAID, ~$0.06 each). Four moments in one row.
5. **`preview`** (free): `out/preview.gif` - the walk moving at its own step over marked ground, then each sheet.

Run a paid step without `--yes` first: it prints the cost. Say the total and wait for a yes. `--again` draws a step anew.

## A person (`"mannequin": "man" | "woman" | "child"`)
The mannequins are bald and plain: the right arm red and the right leg yellow, the left arm blue and the left leg green *(the user: with
an arm and a leg of one colour, an arm swung over the thigh of its side ran into it - "blue on blue")*. A guide made before is of the old
colours, its arm and leg one: `walk` stops and asks for `mannequin` again (free). An animal's the same way *(the user: seen from the front its
fore and hind leg of one side overlap)*: the fore legs red and blue, the hind legs yellow and green; its step is measured on the near
legs told apart by colour (by x on an old two-colour render). An animal is rendered straight from the side (`"turn": 0`): left to the side
view's 45° default it came out turned toward the viewer - the stag's step 203 px of the render where it walks 251. Drawn again on the four
colours: the stone wolf's legs on the mannequin's (overlap 0.51-0.55), the stag in the poses (0.34-0.41: its legs much thinner than the
mannequin's, and the antlers - why an animal is looked at, not held to a number). The steps are the same but **`mannequin` comes first**:
it renders the figure's walk (`walk-guide.png`) and its standing view (`mannequin/render/idle-east.png`; the mannequin is copied into
the folder as `mannequin-rig.glb`, and copied again - its standing clips with it - when the spec names another), and `design` then draws the
character standing as the mannequin stands and of its build. There is no fitting for people - the design is drawn to the mannequin,
so the body must be the nearest to the character (a child for a child: on an adult's legs a child's design would get them). Left out,
`"mannequin"` is chosen from `what` (*the user: a man on the man, a woman on the woman, a child, a boy or a girl on the child, an animal on
four legs on the dog*) - the first word in it that says which; check the line `mannequin` prints.

Measured on two characters (a guard: cloak, buckled jerkin, pouch and keys, boots; a herbalist: braid, bodice, skirt, satchel):
every frame took the mannequin's pose - leg crossing, arm swing - and kept its details through all 8 frames; cloak and skirt swayed.
But the drawing sat 17-49 px to one side of the mannequin, a different amount each frame (the cloak behind pushes the body forward of
its cell's middle). `cut` therefore moves each frame across until its head is over the mannequin's head, and prints the moves. The
head is the rows 5-18 % of the figure's height under its crown - the crown being the first row 40 % as wide as the mannequin's bald head,
so the tip of a spear, a feather or a tuft of hair above it is not taken for it - and in each row the widest run (a staff beside the head
is a run of its own), the median of their middles. A move is at most 64 px, made on a canvas that much wider (nothing is cut off), and
moves spread over more than 40 px are pointed out - look at the strip. (It was the mean of the top 12.5 % of the figure: a spear or a
ponytail on top pulled it off, unclamped, and what was pushed past the cell's edge was lost.)
A village boy on the child (drawn with this script end to end): the same - poses followed, frames 19-26 px off before the move. His
head came out smaller than the child mannequin's big one, in the design and in the walk alike: the build is followed loosely, the
pose closely.

## Seen from above (`"view": "above"`)
For an isometric or top-down game: the mannequin's walk rendered by a game camera 30° above (`"pitch"`), in all eight facings
(free, ~5 minutes; not rendered again while `mannequin.json` and the rig are the same), and each facing drawn on its own guide -
`walk-guide-<facing>.png`, one picture a facing (`walk --only south-east` for one; the gate names them and their cost). The prompt says
how the facing is seen ("toward the LOWER RIGHT - a three-quarter FRONT view"), and for the north facings that the character is seen
from BEHIND, the back of its hair and clothes drawn to belong to the design. The design can be drawn from the side as for a side
view - it shows WHO, not the view; a person's `design` is drawn to the mannequin standing in the south-east view.
- Every facing's guide has ONE scale, and the ground under the figure at one point of every cell: seen from above a step goes up and
  down the picture, so a frame is not stood on its lowest point. `cut` moves a person's frame across until its head is over the
  mannequin's and down until its nearer foot is on the mannequin's, brings each facing's figures to one size (the image model draws
  each picture at a size of its own: `cut` prints it when a facing is more than 3 % off), and makes the south-east facing's first frame
  `"height"` px tall.
- `out/walk-<facing>.png` - every facing on one cell size, with `"anchor"` in `creature.json`: the point of the cell that is the
  ground under the figure (where the game puts its position) - and `out/stand-<facing>.png`, the walk's frame in which the feet pass
  each other (the narrowest, measured on the mannequin): what stands still between walks. `"mirror": true` flips west, north-west
  and south-west from their pairs instead of drawing them.
- `step` is `[across, down]` px of a whole step on the picture: measured on the east facing as a side view's is, and turned for each
  facing on the ground seen 30° from above (south-east `[86.9, 43.4]`: 2:1, as an isometric ground). `preview` walks every facing over
  dotted ground.

Measured (the guard: cloak, buckled jerkin, pouch and keys; his design drawn from the side; GPT Image 2.6, $0.06 a facing): all eight
facings the same man - hair, beard, cloak, buckles - in the mannequin's poses, the north ones from behind with the cloak's back and the
back of the head. Moved 1-56 px across (the cloak behind pushes the body forward, as from the side) and up to 31 px down; 1.03-1.06x
the mannequin's height. Overlap 0.54-0.78; the five frames under 0.6 had the cloak flared out wide (in the pose). Drawn again on the
four-colour mannequin (the arms and the legs each their own colour): 0.55-0.83, the north-west that had been lowest 0.58-0.83. Its step against its height came
out as the side view's: 0.71 of a standing height a step with the 30° view's shortening allowed for, 0.72 from the side with its 45°
turn allowed for.
An animal from above: the fitted dog renders in all eight facings with its step measured on its paws (the boar: legs x0.44, body
x1.76, 110 px of the render a step); none has been drawn from above yet - draw one facing first and look.

## Pixel art (`"pixel": 96`)
The walk drawn as pixel art, as `pixelart.py` draws a character over its render: the mannequin's frames reduced to sprite pixels (the
figure standing `pixel` px tall), laid out as a few frames a sheet in squares of Z px (one sprite pixel), and the image model asked to
draw the design (an illustration - image 2: its face, hair, outfit and colours, not its style) as pixel art ON that grid; a second
sheet goes on from the first. Each facing has its own sheets: four frames a sheet where they fit, the squares made smaller down to 6 px
for that (8 at 96 px; an east stride is wide - at 8 px it was two frames a sheet, four sheets a facing). The answers are read back on
the grid they were drawn on (pixelgrid.py, pitch_of and read), the white shut in between the legs told from white things by the AI
cut-out, every sheet brought to the first one's size - measured by the figures' HEIGHT against the guide's, frame for its own frame - each
sprite laid where it covers the guide best; then one palette for the bodies
and one for the heads ("colours", 32: a third of it the heads' - with one palette for everything the guard's eyes and brows went), the
heads' rows not cleaned of lone pixels. Works with `"view": "side"` (out/walk.png, out/stand.png) and `"view": "above"`.

Measured (the guard, south-east, 96 px, two sheets $0.14): squares drawn 9.3-9.5 px for 8 asked, so the sprites are about 85 px tall;
overlap 0.72-0.86; the face, beard, cloak and boots read well, the buckles and keys lose some detail, and the second sheet - scaled
3.5 % to the first's size before reading - is a little softer. Drawn again on the four-colour mannequin: the two sheets' figures the same
height (747-766 px) but their squares read 8.09 and 8.59 px; sized by how the SHAPE fits (pixelart.py's way) the second came out 6 %
larger and was made smaller still - its sprites 84 px beside the first's 90-94. By height: 89-94 px, all eight. Other moves (`sheet`)
are still drawn as illustrations.

## In the game
- **The walk's frame is read off the distance walked**: `frame = floor(walked / step * n) % n`, `step` from `creature.json`. The paws
  then stay where they are set down whatever the creature's speed (a charge, a slow prowl).
- **How `step` is measured** (on the mannequin's renders, by `mannequin`): only in the frames in which a foot IS on the ground, its
  place against time fitted with a straight line. An animal: the near fore and hind paws, in the frames whose phase in the renderer's
  gait (render_char.html `legPose`: the near fore leg at `(k/n + 0.75) % 1`, the near hind at `+ 0.5`, down while under 0.62) has
  them down - one slope for both (they sweep 2-6 % differently: no one step holds both still, so it splits the slide). A person: the
  near foot's HEEL while the sole is flat on the ground (its lowest point on the figures' lowest line, its lowest band as wide as the
  foot); with fewer than two such frames (a 4-frame walk) every frame it is down in - the heel, or where the heel would be under the
  toe. Checked against a 24-frame render: the stag 251 px of the render from its 8 frames / 253 from 24, the guard 420 / 422; from 6
  frames within 3 %; from 4, an animal within 2 % and a person 6 % long. It used to be the foot's whole sweep over ALL frames / the
  share of the step it is down: the stag's least x came from a frame with the paw up (3 % long), a person's foot rolls heel to toe and
  its lowest point goes forward along it (people 7-11 % short), and 6 or 4 frames missed touch-down and lift-off. A `walk-guide.json`
  measured that way is measured again by `cut`, from the same renders, and `cut` says so.
- A sheet's four frames are the game's to time: struck → staggering while it is stunned, the last two when it is beaten.
- Strips stand on the bottom of their cells (`align: bottom`; 2 px of margin) or hang from the top (`top`).

## What was measured (one game, GPT Image 2.6)
- **The mannequin is followed closely** (a guide of stick skeletons was built too and never drawn from): the stone wolf's 8 frames came out at the mannequin's
  places within 3 px, near legs light, far legs dark, the same wolf in every frame.
- **Without fitting, every creature gets a dog's legs.** Drawn on the dog as it is, a short-legged boar and a long-legged stag both
  came out with legs of a dog's length - the drawing puts each paw where the mannequin's paw is. With the mannequin fitted (boar: legs
  x0.44, body x1.76; stag: legs x2.32) each kept its own build. Always `mannequin` (it fits) before `walk`.
- **The mannequin's tail leaked**: a stag with a short scut got a wolf's brush. The mannequin is rendered without a tail.
- **One mannequin per way of standing.** The dog serves what stands on straight legs under its body (wolf, boar, stag). A salamander -
  low, its legs out to the sides - came out standing tall on straight dog legs, and its build cannot be read off the design either
  (the feet are not under the body). A sprawler needs its own mannequin AND its own gait; neither exists yet - draw such a creature's
  movement as a `sheet`.
- A head carried under the back's line (a boar's): the mannequin's neck is only made as low as it goes; the head is the design's.
- **The cut-out.** The paper's white joined to the picture's edge goes (so a spray of drops, a wisp of mist, scattered leaves stay - an AI
  cut-out alone drops loose pieces), and the paper SHUT IN between limbs goes too: it is the white where SpriteCast's AI cut-out (BiRefNet,
  as for a character's frames) sees no figure, so white clothes and pale coats stay. With the white key alone a herbalist stood with a white
  panel between her legs and a stag walked with one between its forelegs. The AI is run on each cell (a sheet's figure) alone, as it
  always was, but only on a cell with white of 12 px or more shut in - with none it could take nothing away - and what it gives is kept
  beside the drawing (`walk-drawn-ai.png`, `<sheet>-drawn-ai.png`, `design-ai.png`, each cell's box written in; made again when the
  drawing changes), so a second `cut` runs it on nothing. (Run once on a whole walk or sheet, 1536 px squeezed into its 1024, it took
  the pale of a mist for paper: 710 px of holes in the stag's misty sheet.) **onnxruntime is needed**: without it `cut` stops and says so, as a character's `finish`
  does (`doctor.py`); `SPRITECAST_KEY=white` cuts by pure paper white alone, on purpose.
- A sheet's figures sometimes touch (a spray of drops reaching the next figure): the sheet is then cut at the emptiest columns near
  its quarter lines, and `cut` says so - look at the strip. Very pale things (mist) lose their faintest parts to the white.

## The mannequins, and making another
`mannequins/dog.glb` was made once: one picture ("a plain MANNEQUIN of a four-legged animal: a
featureless sculpted figure of a medium-sized dog of a wolf's build, all of one smooth matte light grey material ... NO fur, no eyes,
no nose, no mouth ... front, right side, back"), cut into views and given to Tripo's multiview model (30 credits). No rig is bought:
its skeleton is found from the mesh and it walks in SpriteCast's animal gait (character.md, Animals).
`man.glb`, `woman.glb`, `child.glb` the same way ("a featureless sculpted figure of an adult MAN ... COMPLETELY BALD ... a simple blank
face ... no clothes and no anatomy drawn: a smooth, plain, modest doll-like body", front / side / back in an A-pose), then Tripo's model
and rig with its walk and standing clip (75 credits each). `isoprop.py`'s standing person is the same three figures, posed.

Another build that also stands on straight legs does not need another mannequin - fitting covers it. For your own: an animal project
(`"kind": "animal"`) whose turnaround is a plain figure like that one → `charpipe.py model` → `"mannequin": "path/to/model.glb"` in
the creature's spec. In a character spec, `"mannequin": true` renders an animal as the grey figure with coloured legs and no tail,
and `"fit": {"leg": .., "body": .., "nose_up": .., "nose_out": ..}` stretches it; `creature.py mannequin` writes both.
