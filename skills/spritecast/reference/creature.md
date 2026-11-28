# Creatures and people for a side-scrolling game, drawn straight in 2D (`creature.py`)

A monster or an animal for a platformer or a side-view RPG, with no 3D model of it made: one design in the look of a picture of the
user's, then its animations drawn from that design. A four-legged one's **walk** is drawn on the poses of a plain **mannequin** - a
grey dog with no coat, no face and no tail, its near legs red and its far legs blue - that has first been given the design's own
proportions. Every other animation (struck, falling apart, a hop, a drift) is a **sheet of four moments said in words**.

Frames face right; a game flips them. `scripts/creature.py`, steps `design`, `mannequin`, `walk`, `sheet`, `cut`, `preview`.

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
| `mannequin` | `"dog"` (default), `"man"`, `"woman"`, `"child"` - all come with SpriteCast - an animal's `.glb` of your own, or `false`: no walk of this kind - a blob, a cloud, a thing that hops: `sheets` only |
| `noun` | `"character"` when the sheets are of a person who has no mannequin walk here - the game's own heroine, her standing picture put at `<name>/design.png` with `"mannequin": false`: struck and thrown back, worn out and sitting down, each a sheet |
| `turn` | a person: degrees the body is turned toward the viewer as it walks sideways (45; 0 a flat profile) - as a side-view character's `"turn"` |
| `sheets` | name → `{"moments": "...", "height": px of ITS first frame (left out: the walk's `height` - give it when the first moment is not standing up as the walk does: a crouch, a heap), "hang": true for a floating thing (frames hung from their tops - its rain falls under it)}`. **Every picture has its own scale**, from its own first figure: the model draws a figure at a different size in each (a person ~430 px tall in a walk's cell, 700-900 px on a sheet - the walk's scale made a sheet 1.6-2x too big) |

Files go to `<the spec's folder>/<name>/`: `design.png`, `walk-guide.png`, `walk-drawn.png`, `<sheet>-drawn.png`, and `out/walk.png`,
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
The mannequins are bald and plain, the right arm and leg red, the left blue. The steps are the same but **`mannequin` comes first**:
it renders the figure's walk (`walk-guide.png`) and its standing view (`mannequin/render/idle-east.png`; the mannequin is copied into
the folder as `mannequin-rig.glb`, and copied again - its standing clips with it - when the spec names another), and `design` then draws the
character standing as the mannequin stands and of its build. There is no fitting for people - the design is drawn to the mannequin,
so pick the body nearest the character (a child for a child: on an adult's legs a child's design would get them).

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

**Tried once in an isometric view** (not in the tool): the same guard, drawn only from his side at eye level, on the man's walk seen
from 30 degrees above - toward the lower right, to the right, and away to the upper right. All three came out seen from above, in the
poses, the back view with the cloak's back and the back of the head; overlap with the mannequin 0.59-0.73 after the heads were lined
up. So the view can be changed too; whether eight facings stay one character was not checked.

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
