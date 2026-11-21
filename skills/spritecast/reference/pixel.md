# Pixel-art sprites (arcade size)

For a game drawn in pixels - a belt-scroller, a fighter, an arcade platformer - the character as real pixel art, about 96 px tall:
one colour a pixel, a palette, a dark outline, no blur. It needs a character that already has its 3D renders (`charpipe.py render`;
free with a rig) and `OPENAI_API_KEY`. It does not use the illustrated frames: the order is the other way round.

    renders (3D) → pixelized guide → the image model redraws it as pixel art → read back on the grid it drew → sprites

## The command

```
PYTHON pixelart.py CHAR.json                         # the plan and its cost - spends nothing
PYTHON pixelart.py CHAR.json --dirs south-east --yes # draws what is missing
```

`--px 96` the standing figure's height (96 is what works; see "Sizes"), `--clips walk,slash,throw` which animations (walk by
default; any action in the spec), `--dirs` which facings (the spec's: all eight, or the four diagonals with `"facings": 4`), `--again NAME` one sheet anew (a name from the
plan: `walk-south-east-1`), `--partial` put together what is drawn already, to look at.

**Always show the plan first** (the run without `--yes`): it lists the sheets and the cost (~$0.075 a sheet). Then one facing of one
animation as the sample, shown to the user, before the rest. A walk is 2 sheets a facing (4 frames a sheet), 3 for a side view
(a wide stride: 3 frames a sheet); an action with something held, or with the arms wide, is 4 (2 frames a sheet). All eight facings
of a walk: 18 sheets, about $1.35. The answers are kept in `<character>/pixel/`: a second run pays only for what is missing, and
everything after the drawing (reading, sizing, cleaning, packing) is free to run again.

## What comes out: `<character>/out-pixel<px>/`

- `<clip>-<facing>.png` - a strip, one frame after another, all the same size (`frame` in `pixel.json`), transparent around.
- `shadows/<clip>-<facing>.png` - each frame's own shadow, from the 3D render (the body flat on the ground along the light), hard-edged,
  one colour. `pixel.json` says where its frame goes against the sprite's (`shadows.<name>.offset`), the colour and the strength
  (30 %): the game lays it under the sprite at that alpha. Since 0.20 a set made anew has the shadow as light falls, in five steps
  (10-56 %, each pixel's own alpha in the strip - lay it as it is): deep under the feet, pale at its far edge.
- `preview.gif` - everything made, playing. Show this.
- `pixel.json` - `figure_px` (the height it really came out at), `frame`, `colours`, `animations`, `shadows`, `release`.

## Something held, something thrown

A held thing is part of the action in the spec (`"hold"`), built from shapes in the right hand and drawn where each render has it.

```json
{"name": "throw", "loop": false, "t0": 0.15, "t1": 1.45, "canvas": 512,
 "hold": {"kind": "snowball", "radius": 0.055, "color": "#bcd6f2", "final": "#ffffff", "until": "auto"}}
```

- `"color"` is the colour it is DRAWN in, `"final"` the colour it ends up. A white thing on the white paper is not there for the
  image model to see (it drew the hand empty) nor for the cut-out to keep: give a white or very pale thing a pale blue `color` and
  `"final": "#ffffff"`. The guide also gets a dark line round whatever is held.
- `"until"` lets it go: the seconds into the clip after which the hand is empty; `"auto"` is the moment the right hand moves fastest
  (a throw's release). The prompt then says, cell by cell, which hands hold it and which are empty.
- **A held thing the figure hides.** In some facings the thing is in the hand on the far side of the body, or in a hand raised behind
  the head (a big-headed character's wind-up): there to the rig, not to the camera. The run works out for every frame how much of it
  the camera sees. Where more than half is hidden the prompt says so for that cell ("hidden by the figure ... do NOT draw it in front
  of the body") and the guide's dark line goes round the seen part only. Told just "the ball is in the hand", the image model drew it
  at the chest. It is the same measure the illustrated frames go by for a weapon behind the body (`charpipe.held_visible`). Nothing to
  set: it is automatic. If a user points at such a frame, `--again <that sheet>` draws it with this wording.
- An action with `until` is rendered by `PYTHON chardepth.py CHAR.json render <action>` (it knows `snowball`; `charpipe.py render`
  knows `umbrella`). Look at the renders before drawing.
- For a thing let go the folder also gets `<thing>.png` (the thing alone), `<thing>-fly.png` (stretched along its way),
  `<thing>-hit.png` (a 4-frame burst), `<clip>-<facing>-flying.gif` (the throw with the thing in flight over a floor of blocks, its
  shadows by the same light - show this), and in `pixel.json`:

```json
"release": {"throw-south-east": {"thing": "snowball", "frame": 4, "at": [30, 3], "toward": [0.71, 0.35],
            "speed": 36.0, "up": 13.0, "gravity": 4.32, "ground_slope": 1.0, "hand_above_feet": 102}}
```

  `frame`: the first frame without it - spawn it then, at `at` (pixels in the sprite's frame). `toward` is the facing as the camera
  sees it: ground `d` further south is `d × sin(pitch)` lower on the screen, so a throw to the south-east goes right and down - that
  is right for a game drawn on this camera's ground (`ground_slope` 1; 0 would be a flat line at the feet, a side-on game). Height is
  apart from that: up at `up` px a frame, pulled back by `gravity`, landing when it is `hand_above_feet` under where it left.
  `speed`, `up`, `gravity` are a start, in px a frame at this sprite size: tell the user they are theirs to tune.

## An animation the rig does not have

`PYTHON addclip.py CHAR.json Throw.fbx throw` puts an FBX animation (Mixamo's "without skin" download; any skeleton with the same
bone names as the rig - Tripo's rigs are Mixamo-named) into a copy of the rig as one more clip → `rig/rig-throw.glb`; it prints
the two lines for the spec (`"rig_glb"`, and the action). No credits. Render it and LOOK before drawing: the motion is carried bone
by bone from each skeleton's own rest pose, limbs first turned from the rig's A-pose to the FBX's T-pose; a rig with other bone
names, or a rest pose unlike either, comes out twisted - say so rather than draw it. For a big-headed character (three heads
tall) add `--clear-head 55`: a clip made for a small head puts a hand raised past the ear inside the skull; while a hand is above the
head's joint its arm is swung outward by up to that many degrees, and nothing else is changed. Render and look, then raise or lower it.

## The review, and drawing again

Every run checks every frame, as `finish` and `redraw` do for the illustrated ones, and ends with a line `REVIEW: N of M frames to
look at`:

- `pose 0.52` - the frame's outline covers its render's by less than `"redo_below"` (0.75 in the spec): the image model drew
  another pose (a throw's follow-through with the arm still out where the render has it down).
- `<thing> missing` / `<thing> drawn after it was let go` - the held thing is not where the render has it, or is there after the
  release. Only what the camera SEES of it counts: a ball behind the head is not "missing".
- `<thing> drawn where the figure hides it` - the drawing shows the thing in a frame whose render has it behind the body or the head.
  Whether that is wrong is the user's call (a ball that shows before the throw reads well): show the frames and ask, then `--again`.

`out-pixel<px>/review.png` has each marked frame beside its guide, and `pixel.json` lists them under `review`. **Show the user
review.png, not all the frames.** `PYTHON pixelart.py CHAR.json ... --redraw` says which sheets it would draw again and what that
costs; with `--yes` it draws them (twice at most a sheet) and keeps whichever drawing is better - fewer frames with the held
thing wrong first, then the higher lowest overlap; the other is kept as `<sheet>-out.try<N>.png`. A frame that is only a little
under 0.75 with the pose right is the user's call: show it and ask.

## How much hand work to expect - say it honestly
Pixel art needs some fixing by hand, and the user should be told so before, not after: a few pixels a frame with the eraser and the
pencil, which someone who does not draw can do. Two measured cases on the rain girl at 96 px: the throw, 40 frames - 131 pixels in 10
frames (0.15 %), only left-over white; the walk-with-umbrella → stance → slash → back up, 23 frames - 1,196 pixels in all 23 frames
(2.3 %), a few minutes' work by the user: a held umbrella's tip and edge made the same from frame to frame (the only real fixing - the
character itself was not touched beyond a few left-over white specks). A long
thin held thing is where most of it goes. What made that one quick: all 23 frames looked at in a row, playing - in pixel art a fix
is making sure no part's pixels change a lot from one frame to the next (an umbrella tip that jumps, an edge that grows and
shrinks). Tell the user to play the animation (Enter) and look for such a part, not to go through frames one by one. Offer the editor every time, with "3D shapes over" on for a set that holds something.

## A swing's effect in pixel art
An action with `"trail"` (reference/character.md, "A swing's effect") has its effect in the pixel set too: `pixelart.py` reads the same
renders (`render/<clip>-<facing>-<i>-t.png`) and writes `trails/<clip>-<facing>.png`, with `"trails"` in `pixel.json` (`file`, `frame`,
`offset` from the sprite's frame, `frames`, `per_frame`: effect cells to each frame of the figure). Free.
- Made smaller by area like the figure, its colours brought to ten.
- **Solid things keep hard edges, thin things stay see-through.** A pixel beside a solid one (water, flame, a leaf) is there or not.
  Mist and a fading band have no solid pixel next to them: they keep one of three steps of see-through (about 28, 47, 69 %) - made
  solid, mist was a lump of cotton (the user: "use see-through"). A dot of four pixels or fewer (a drop, a flake of ash) is never
  see-through: solid, or not there.
- A game that draws pixel art with see-through off (alpha test) shows mist as lumps or not at all.
- **Faded out with the distance from the figure**: the drops a swing throws fly on and on and ran off the render's frame at any size -
  cut in a straight line (the user saw the squares). Full near the figure, gone by 1.15 of its height from its middle (or just inside
  the frame's edge, if that comes first) - times the action's `"trail_reach"` (2: twice as far, the frame rendered bigger to hold it). `charpipe.py render` gives an action with `"trail"` a 1024 px frame by default (768 before)
  and says when the trail still runs off it.
- A whole `pixelart.py` run writing `"trails"`: the rain girl's downward cut and backhand, four facings, 64 frames (2026-11-20).

## A long thing swung far: a sheet of one frame, wide or standing up
Four frames go on a sheet (48-px cells at 96 px), or three, or two, wider. A sword's arc held out at arm's length is wider than half a
sheet, and an umbrella raised straight up over the head taller than a cell: such a frame was left out, and the facing with it.
- **Too wide for two**: one frame to a sheet, the sheet's whole width (192 px at 96).
- **Too tall**: one frame to a sheet, and that sheet drawn standing up (1024x1536 - 176 px for the figure from the feet up, at 96).
  The other frames of the animation stay on landscape sheets; every frame is read back at the one scale.
- A frame that still does not fit is left out with a line that says so (it went on into the drawing and stopped there, after paying
  for the sheets before it): render that moment a little earlier or later (`"t0"`, `"t1"`).
- One frame to a sheet costs a sheet a frame (~$0.075): a facing of an 8-frame swing ~$0.60. GPT keeps the set's look across them from
  the turnaround and the animation's first sheet (the rain girl's 64 frames of two swings: one person throughout).

## Effects from the pack: `fxpack.py` (PVFX Foundry, CC0) - free
253 pixel-art effects by Pixel VFX Studio come with SpriteCast in `effects/pvfx/<category>/<effect>/` (`sheet.png`, a grid; `manifest.json`;
`index.json` lists them all with what each shows). Their strict tier: binary alpha, a limited palette - pixel art that sits with the sprites.
CC0 1.0 for the sheets and manifests (`effects/pvfx/LICENSE.txt`, `THIRD_PARTY_NOTICES.txt`); the names and marks are not - say where one came from.
- `fxpack.py list [--search q] [--category c]`, `preview ID ...` -> fx-preview.png, `export ID ... --out DIR [--as NAME] [--scale N]
  [--palette CHAR.json|FILE|name] [--hue H]` -> `<DIR>/<name>.png` and `<DIR>/fx.json` (w, h, px, py, n, cols, ms, loop, src).
- Whole scales only (`--scale 2` keeps a pixel a pixel): a ring drawn at 2x was as wide as the backhand it marked.
- `--palette CHAR.json`: every pixel to the nearest colour of the character's pixel set; `--hue`: the hues turned, lights and darks kept.
- **In the game**: play the cells in order at `ms` from the pivot, once (or looping when `loop`). A thing in flight (`projectiles/*-flight`)
  is drawn going right: turn it the way it flies. A RING round a character (`melee/spin-slash`, at the waist) is cut at the pivot's line -
  the half above at a depth behind her, the half below in front (drawn whole in front, it went through her body: the user saw it).
- Rain Girl plays nine: `water/bubble-burst` (a hit - round, so no way it points; the directional `water-bolt-impact` looked odd),
  `impacts/death-poof`, `water/drip-splash`, `fire/fireball-impact` (from its burst, frame 4), `projectiles/fireball-flight` (each
  monster's colour by the game's own recolour), `ui/heart-pickup`, `ui/mana-pickup`, and for the backhand `melee/spin-slash` and
  `impacts/shockwave-ring` at 2x.

## A held thing in the same colours in every frame
GPT draws each sheet's held thing in whichever of the set's colours it lands on: the rain girl's umbrella came back in four different
yellows from facing to facing (its yellow lies close to the coat's), its shaft silver in some sheets and dark in others. `pixelart.py`
now gives **each part of the held thing** - from its render: an umbrella's handle, shaft, canopy, tip - **the same tones in every
frame**, lit and shaded as the drawing had it. Free; by default; `--held-as-drawn` leaves it as drawn.
- **Its colours**, per part, the first that is there: the `hold`'s own (`"handle"`, `"shaft"`, `"tip"`: `"shaft": "#3f2917"` makes a
  silver shaft the handle's dark brown) → **`"colours_from": "<clip>-<facing>-<frame>"`** (frame from 1) - each part in the colour it
  is DRAWN in, hand edits included, in the one frame the user picks as right (a part that frame does not show is taken from the
  animation's next frames that do; an umbrella's shaft that none shows goes with the handle) → the umbrella's defaults, or for any
  other held thing its render's own colour for that part. `"color"` stays the render's: with `colours_from` the canopy is the frame's.
- **Only the thing**: pixels near where its render has each part and of that part's kind of colour - not the hand round it (skin has
  a brown handle's hue, much lighter), not the hair (a handle's hue and lightness: nothing on the head is touched), not the coat
  beside the canopy, not the outline. A silver shaft the image model drew a pixel or three off its render, or above the fist where
  the render has the hand, is still the shaft's.
- **`"as_drawn": ["slash-south-west-5"]`** in the `hold` (frames from 1): those frames left as drawn, for the user to paint by hand.
  Nothing is lost by the colouring: `pixel/drawn-<px>/` keeps every frame as drawn, which `pixeledit.py` shows beside the frame and
  paints back with its *as drawn brush*.
- The build prints the colours it took (`held thing's colours from carry-south-east-0: {...}`) and the pixels changed per frame.
- Checked on the rain girl's umbrella walk and swing in four facings (64 frames). Not checked: a thing other than the umbrella, a
  thing with `"final"` (a snowball: skipped, its own rule).
- An action's `"frame_words"` now go into the pixel sheets' prompts too (they were the illustrated sheets' only): the rain girl's
  south-west swing had a hand across her chin until `"5@south-west": "BOTH hands hold the umbrella ..."` was said.

## A hand the body hides, an effect missing in a facing
- **The hand that holds a thing, hidden by the body** (seen from behind on the holding side): the image model drew an arm raised to the
  shoulder to hold an umbrella that showed past it (the rain girl standing, north-west). Every pixel sheet now says: a hand on the thing
  only where the cell shows one. For an action on SpriteCast's idle (`"clip": "idle_spritecast"`) with something held, the facings that
  turn the holding side away (right hand: north-west, west; left: north-east, east) get a sentence of their own: the hand down by the far
  hip, hidden, the thing passing behind the body; both arms down. Drawn and checked for the right hand, north-west.
- **A swing's effect missing in some facings**: `pixelart.py` names the facings an action with `"trail"` has no effect in, and the free
  command that renders it (`charpipe.py render SPEC --only <action>`). (A pixel swing went into a game with its water in one facing of four.)

- **A speck beside the figure** (a thin end made small - an umbrella's tip, a sword's point - left as 1-3 pixels on their own; or a pixel
  put in by hand in `pixeledit.py`, left in the air when the frame was drawn again with the thing moved): taken off by `pixelart.py`, after
  the hand's edits (it says how many, and how many were put in by hand). If the user says one was meant (dust, a spark, something that
  small let go), run it again with `--keep-specks` or put `"keep_specks": true` in the spec.

## Fixing by hand: `pixeledit.py`

Pixel art is not all to be had by rule: a patch of paper left where an arm crosses the body, a face that came out poorer in one
frame than in the next. `PYTHON pixeledit.py CHAR.json [--px 96] [--port 8766]` (free) serves a local page with every animation,
frame by frame, big, on a grid. **It is a server: run it in the background** (`--no-open` when no browser should open on this
machine), give the user the address, stop it when they say they are done. It saves as they draw.

**Animations that play one after another, as one**: `pixeledit.py CHAR.json --join walk,ready,slash,recover --facing south-east`
(free) - the page shows ONLY that: their frames end to end, in each one's own order, played through with Enter. A part that jumps
is as often across a join (the walk's last frame into the stance) as inside one, and one animation at a time never shows it. Each
edit goes to its own animation's frame - the same touch file, the same strips written again - so it is as if made there; the 3D
views and shapes are each frame's own. Frames are not copied, deleted or moved here (open the animation by itself for that).
Offer it whenever a set has more than one animation that a game plays in a row.

| tool | does |
|---|---|
| erase (E), pencil (B) | a pixel at a time, or dragged; brush 1-6 px (`[` `]`); the palette is the animation's own colours, most used first |
| magic erase (W) | click a patch of one colour - white left between an arm and the body - and the whole patch goes. "alike": how near a colour counts as the same; "whole frame": every such pixel, not only the patch that touches |
| change colour (G) | click a colour in the frame: it becomes the chosen colour - that patch, the whole frame, or (ticked) every frame of the animation |
| pick colour (I, or Alt-click) | the colour under the pointer |
| "+ add this colour" | any colour, chosen in the colour box, put in the palette and kept for next time (`pixel/colours-<px>.json`); Shift-click takes it out again |
| frames: "+ copy", "delete", "◀ move", "move ▶" | **the animation's frames themselves**. "+ copy": a copy of this frame after it (dashed blue) - an in-between to draw on, 8 frames made 9. "delete": the frame left out. "move": a place earlier or later. "the pipeline's frames again" undoes all of it. A character only (a prop's frames are its sides) |
| select (M), move (V) | drag a box; move drags what is in it, the arrow keys nudge it a pixel |
| copy, paste (Ctrl+C / Ctrl+V) | a face that came out well in one frame, into another: paste, click to set it down - or "paste in every frame, same place" |
| bring back (R) | takes the edits off where it is rubbed; "this frame as it was" takes them all off |
| as drawn brush (O) | paints back the frame **as drawn** where it is rubbed: the held thing in GPT's own colours, before they were made the same in every frame (`pixel/drawn-<px>/`, kept by every build) - nothing of the drawing is lost |
| ◀ ▶ (← →), play (Enter), "the frame before, faint" | to see a fix in motion and against its neighbour |
| "as drawn beside" (5), "edited" | the frame as drawn (before the held thing's colours) beside the frame being drawn; with "edited" off, the drawing alone. With "3D render beside" on too: the render, the drawing and the edited frame side by side |
| "3D render beside" (3), "3D render under, faint" | the render the frame was drawn from, at the frame's size and place: beside the sprite, or under it. To tell paper from a real gap, and to see what a pose or a part should be |
| "3D shapes over" (4) | where the 3D has things, over the frame being drawn: the held thing filled red (`render/<clip>-<facing>-<i>-held.png`), the body's outline blue with a faint blue fill (`-body.png`; with neither, the whole render as the body). A held thing drawn too long, too short or at another angle shows at once - the image model does that to a thin thing the colour of the clothes (the rain girl's umbrella: 2 of 8 walk frames). Not saved into the sprite |
| wheel, Space + drag, "behind" | zoom at the pointer, move the picture, the colour behind the sprite (white specks show on a dark one, dark specks on a light one) |

**Frames changed by hand are kept like the edits**: the touch file has `_order` (the pipeline's frames by number, the copies by
name) and `_added`; the base strips stay the pipeline's. The strip, the shadow strip and `pixel.json` follow at once - the frame
count, `release.frame` moved to where that frame now is (`null` if the user deleted it: say so, the game has nothing to spawn
then), and `frames_by_hand`. `pixelart.py` lays the same order out again at the end of every build (its `preview.gif` shows the
pipeline's frames only). A set built before 0.13 needs one more build first: the page says so. Undo does not reach across a
change of frames.

Undo (Ctrl+Z) takes back a change made to many frames in one step. The left panel's "how it was made" has, for the animation and for
everything: the AI's drawing time, the AI cut-out's time, the time spent by hand, the frames touched and the pixels changed by hand
(and what share of the sprite's pixels that is). `pixelart.py` prints the same as `HOW IT WAS MADE` and keeps it in `pixel.json`
(`made`); **give the user that line after a build** - it is how they see what the hand tool cost them against the machine. Sheets drawn
or frames cut before times were kept say "about" / "not timed".

Frames the review marked have a red bar, edited ones a green one. The edits are kept in `<character>/pixel/touch-<px>.json` (per
frame: the pixels set and the pixels cleared, in the frame's render coordinates), the strips in `out-pixel<px>/` are written again
at once, and `pixelart.py` lays the same edits on every time it builds them - whatever else that run makes. A frame drawn anew
since it was edited (its outline is another) has its edits set aside and says so; they are never laid on another drawing.
Offer it after the review and a redraw have done what they can; never draw for the user without asking.

## What the run prints (read it; it is how to tell without looking at every frame)

- `the sprites on their renders, overlap [...]` - each frame's outline against its render's. 0.8+ is a good frame; under 0.7 the
  image model drew the pose differently (often a deep crouch drawn more upright): show those frames beside their renders.
- `drawn at (× the render's size per frame, the correction made to the sheet, its squares in px)` - the image model redraws at a size
  of its own, and a sheet of crouched frames a third bigger; a sheet more than 6 % off the character's scale is brought back (and
  comes out a little softer for it).
- `head width per frame` - should hardly change within an animation (walk: ±1 px). If it swings, a sheet was read at the wrong
  square size: run `--again` for that sheet.
- `white per frame (pixels; paper made see-through, the model's own white painted over, a real light part given the guide's colour)`
  and `outline per frame (rim pixels, not dark → given the outline's colour)` - what the clean-up did.
- `N figures in the answer for M frames - left out` - the image model merged or dropped a figure: `--again <that sheet>`.

## Sizes

| asked (`--px`) | what to do | what comes out |
|---|---|---|
| 96 | the size to offer for a character of ordinary proportions | 94-100 px |
| 128 | say it buys little | about 104 px |
| 64 | only for a character DESIGNED small: about three heads tall, with its own 3D model (below) | about 70 px |
| under 64 (32, 48) | drawn at 64, then made smaller from that set by `pixelsmall.py` - `pixelart.py` does both by itself | 32 → about 36 px |

**The image model is never asked for less than 64.** It draws its "pixels" at a size of its own (asked for 8-px squares it drew
7.4 to 10.8), and with few squares one square off is an eye gone. 32 px was tried four ways - eight frames a sheet (squashed by a
fifth and more), three frames in big squares (spiky hair, faces lost), four frames in 16-px squares (clean drawings, but 45 px tall,
a face on the back of a head, some sheets with squares twice the size), and reduced from 64 - and only the last keeps the same
person, motion and frames in every facing. So `--px 32` prints that it draws at 64, builds `out-pixel64/` and then writes
`out-pixel32/` from it (strips, shadows, the thrown thing, `pixel.json` with the release data made smaller; free, and
`PYTHON pixelsmall.py CHAR.json --to 32` does it again). Tell the user plainly: 64 is what comes out well; the smaller set has
rougher faces, to be fixed in the 64 set with `pixeledit.py` and reduced again.

**A character for 64 px.** The ordinary design at 64 comes out about 81 px and loses its face: the head is too small a part of it.
Make the small character its own: one more drawing of the design as a super-deformed figure about three heads tall (a big head,
short thick arms held away from the body, big boots), its own turnaround, its own 3D model and rig (`charpipe.py` as for any
character: the turnaround shown and OK'd first, then about 75 Tripo credits). Scaling the head bone of the ordinary rig is not a
substitute: a raised hand goes into the head. A clip from an FBX then takes `addclip.py ... --clear-head 55`.

## How many colours: `--colours N`, `--palette FILE`

A set has about 40 colours by default (24 for the bodies, 13 for the faces, a held thing's). Both options are **free** - the kept
drawings are read again with another palette - and both work on `pixelart.py` and `proppixel.py`:

- `--colours N` - N colours at most in the whole set (8 at least; a prop: all its sides together). The faces keep a good third of
  them, and a colour's share of the pixels counts for less than usual, so a small part (navy legs beside a big yellow coat) is not
  the first to go. Down to 16 a character holds up; at 8 near colours merge. Say so, and show the result.
- `--palette NAME` - one of the 15 that come with the skill (`skills/spritecast/palettes/`): `pico8` 16, `gameboy` 4, `nes` 55,
  `c64` 16, `cga` 16, `zx` 15, `sweetie16`, `db16`, `db32`, `endesga32`, `endesga64`, `resurrect64`, `apollo` 46, `aap64`, `slso8` 8.
  `--palette list` (no spec needed) prints them and points at `palettes/preview.png`, their colours - show the user that picture
  when they are choosing.
- `--palette FILE` - the user's own palette (their game's), in what Aseprite reads: an image of it (`.png` `.gif` `.bmp` `.pcx`),
  `.hex` (one hex colour a line - Lospec), `.gpl` (GIMP), `.pal` (JASC or RIFF), `.act`, `.col`, `.aseprite`/`.ase` (the sprite's own
  palette; an Adobe swatch `.ase` too). Checked on real `.gpl` and `.aseprite` files; the others on files written to their format.
- Either way every pixel takes its nearest colour in the palette; the run prints how many of the palette's colours were used. A palette with nothing near one of the character's colours changes that colour (a yellow coat in a
  palette without a yellow): show the result, do not promise it.
- Colours put in by hand in the editor follow the same palette. The options are not remembered: give them again on every build, or
  the set goes back to its default colours.
- A user who says "retro", "NES", "Game Boy", "PICO-8", "few colours", or names a palette: ask how many colours or which palette
  file, then use these.

## What it does to the drawing, in order (all of it automatic)

1. Finds the size of the squares on each sheet (the spacing at which grid lines lock onto the drawing best) and reads every figure on
   lines that far apart, each allowed to drift a pixel or three.
2. The head gets column lines of its own, placed by the face (the hair's strands outvote an eye otherwise), its own palette, and
   small features that fill a third of a square win it. Nothing the head shuts in is made see-through (the white of an eye).
3. One palette for the whole character; a held thing's colour kept in it.
4. Every sprite is laid on its render where the outlines overlap most - that is its place in the frame.
5. What is paper and what is figure. White joined to the sheet's edge is paper. White SHUT IN by the figure - between the legs,
   between an arm and the face, or a snowball, the white of an eye - is decided by the AI cut-out the pipeline uses for characters
   (BiRefNet; `--cut ai`, the default wherever onnxruntime is installed: `doctor.py --fix --characters`; about 3 s a frame, once,
   kept in `<character>/pixel/cut/`). Alone the AI kept a block of bare paper beside a raised arm in one frame of forty, and the
   colour key alone cannot tell a snowball from paper: each does what it is sure of. Without onnxruntime (`--cut white`, said when
   it happens) the shut-in white is sorted by rule, patch by patch, by the guide: a real light part (the guide has one there) takes the guide's
   colour; white on the render's head stays (an eye); white where the render has nothing is paper and goes; other white (a shirt the
   model invented at the neck) takes the colours next to it.
6. A held thing goes to its `final` colour. The outline is closed: a rim pixel that is not dark takes the outline's colour.

## Props as pixel art: `proppixel.py`

The same way round as a character, for a thing: its 3D guide pixelized, redrawn as pixel art on the same grid, read back on the grid
the image model drew, brought to the guide's size. It needs the prop's guide (`isoprop.py render`) and `OPENAI_API_KEY`.

```
PYTHON proppixel.py PROP.json                # the plan and its cost - spends nothing
PYTHON proppixel.py PROP.json --yes          # one picture a view (~$0.07-0.10), then reads all → <prop>/out-pixel/
PYTHON proppixel.py PROP.json --ppm 54       # pixels per metre
```

- **`--ppm` is what puts the prop and the character on one floor**: the pixel character's `figure_px` (in its `pixel.json`) over its
  height in metres (`height_m` in its spec). The small example character is 70 px for 1.3 m: 54, the default. Say the number you used.
- **From several sides, make the 3D model first** (`isoprop.py model` - Tripo, ~20 credits - then `yaws`, `"views": [0, 90, 180, 270]`,
  `render`). Blocks say where a thing stands and how big it is, not which face has what on it: an arcade cabinet from blocks came out
  with its screen on the wrong face in one view of four and its top another colour in two. From a model each side has its own things
  on it, and the image model is shown the same view at full size beside the pixelized one: a ramen cart - tiled roof, spoked wheels,
  bottles, bowls, a lantern - came out right from all four. The run says so when a spec has several views and no model.
- **One view of a simple thing** (a chair, a crate) is fine from blocks; the finished illustration (`sprite.png`), if there is one, is
  shown for its materials and colours.
- Out: `sprite-<view>.png` (or `sprite.png`), `pixel.json` (`px_per_m`, each view's `size`, `anchor_px` - the footprint's near corner
  in the sprite's pixels; it can lie outside the picture for a thing on wheels or legs - what the squares came out at, the correction
  made), `preview.png`. **Show preview.png beside the guide's renders.** A view that is wrong: `--again <view>`.
- White shut in by the object (the air under a roof, between spokes) is cleared by the AI cut-out, as for characters; a white thing
  (a stack of bowls) stays. What the cut-out keeps that it should not (it took the gaps between a tree's leaves for leaves) goes by the
  render, as a character's frames do: white where the render has nothing is made see-through; white where the render has the object
  in a dark colour is painted the colour beside it; white where the render is light too is a real light part and stays. `pixel.json`
  says how many pixels each view had of the first two (`paper_px`). A tree came out clean with nothing done by hand. Never under 64 squares: a small prop is drawn 64 tall and made smaller.
- **Its shadow is baked from its 3D model** (`propshade.py`, free, a few seconds - `proppixel.py` runs it itself when the prop has a
  model): the sun's light and the sky's on the ground, each as much as the thing leaves open - deep close by it (under a cart, round a
  trunk's foot), paler where it falls from high up (a crown's, light coming through between its leaves), in five steps of alpha;
  the sun as big as the real one, so a branch's shadow is sharp. The sun is the guide's own light (upper
  right, or `"light": "left"`), so the shade drawn on the prop and the shadow agree. Out: `shadow-<view>.png` (the shadow colour, its
  darkness in the alpha), each view's `"shadow": {"file", "at": [x, y]}` in `pixel.json` (the picture's top-left in the sprite's
  pixels: draw it under the sprite), `preview-shadow.png` - **show it**. The weather: `--shadow overcast` / `"shadow": "overcast"` (a
  grey day: no sun, only soft dark round it - a rainy scene), `none`, or again without drawing: `PYTHON propshade.py PROP.json
  --weather overcast`. The model is laid on each sprite by its outline (`fit` in pixel.json: under ~0.75 the shadow may sit a little
  off - say so). From blocks alone there is no shadow yet: say so. **How deep it is**: `--shadow-strength K` / `"shadow_strength": K` (or
  `propshade.py PROP.json --strength K`, free) - the shadow as if laid K times over itself: **1.5 by default for pixel art** (71 % at its
  deepest, 15 % at its far edge - a little louder than it is, so things stand on the ground; `"light_style": "smooth"` 1), 1 as the
  light gives it (56 % and 10 %: for a light floor where 1.5 looks heavy), more for dark ground; from 0.3 to 3. The steps
  stay five, each deeper; `pixel.json`'s `shadow.strength` and `shadow.steps` say what was baked. A character's spec takes the same
  `"shadow_strength"` (then `charpipe.py CHAR.json pack`, or `pixelart.py` for a pixel set - whose default is 1.5 too; a painted set's is 1), so a game's props and people agree. A
  character walking into a deeper shadow is darkened by more too (`on_a_character` reads this alpha).
- **Indoors**: `--lamp x,y,z --lamp-size r` on `propshade.py` (or `"lamp": {"at": [x, y, z], "size": r}` in the spec) - metres from the
  prop's foot, fixed to the screen like the sun (x right, y up, z towards the viewer); the size is the lamp's own: a bare bulb ~0.03
  (sharp), a lampshade ~0.15-0.3, a ceiling panel ~0.4 (soft). The shadow falls away from it, longer the lower it is, and fades with
  its light (1/d^2) across the floor; the room's other light is the sky's part. A lamp is fixed to the room, the prop is not: the
  shadow is for the prop where it stands. Ask where the lamp is when the user says indoors; else the sun.
- **A lamp's light on the floor comes too**: `light-<view>.png` (its colour warm, its strength in the alpha: brightest under the lamp,
  (h/d)^3 - the 1/d^2 and the slant - the prop's shadow cut out of it, in 7 steps dithered where they meet) and each view's
  `"light": {"file", "at", "blend": "add"}` in pixel.json: lay it on the floor with ADD (or screen), under the shadow and the sprite.
- **The lamp itself, for the game**: `lamp.png` (the light as pixel art - a white core its size, a warm rim, a dithered glow) and in
  pixel.json `"lamp": {"at_m", "size_m", "file", "middle", "colour"}` plus each view's `"lamp": {"at", "spot"}` - the light's middle
  and its spot on the floor in that sprite's pixels. A game draws, all from the sprite's top-left:
  ```js
  const v = pj.views[side];                                   // pj = out-pixel/pixel.json
  draw('light-' + side + '.png', x + v.light.at[0], y + v.light.at[1], 'add');   // the floor lit (ADD / 'lighter')
  draw(v.shadow.file, x + v.shadow.at[0], y + v.shadow.at[1]);                 // the shadow
  draw(v.file, x, y);                                                           // the prop
  draw(pj.lamp.file, x + v.lamp.at[0] - pj.lamp.middle[0], y + v.lamp.at[1] - pj.lamp.middle[1]);   // the lamp
  ```
- **The wind in a prop** (`"sway": "leaves"` in the spec or `propshade.py PROP.json --sway leaves`; free, `proppixel.py` runs it
  itself): the sprite's leaves (its green pixels; or `"sway": [{"colour": "#hex", "within": 60}]` for a flag, a curtain) are cut into
  clumps from the 3D model - each moving pixel takes the model's point it shows, the points are grouped by where they are in 3D
  (3-12 clumps by how much moves, the near ones apart from those behind) - and each clump moves whole, a pixel at a time, far ones
  laid first; what stands, stands. A clump takes the crown's dark edge with it and leaves nothing behind at the edge (inside the crown
  what it left stays: leaves behind leaves), so no second outline shows. Out, a side: `sway-<view>.png` (a sheet: 12 frames across, rows still / breeze / gust; each frame
  4 px wider each side than the sprite and 1 px taller above it (`pad`, `top`: a part lifts a pixel) - draw it 4 px to the left and 1 up; play a row at ~4 fps, go down a row as the wind rises),
  `clumps-<view>.png` (a pixel's clump, 1.. far to near, 0 still) with `"sway": {"at_m": [[across, up, towards], ...], ...}` in
  pixel.json for a game that moves them itself, and `preview-sway.gif` - **show it**. Offer it for trees, bushes, plants. Not a warp
  of the picture and not drawn frames: the picture's own pixels, moved by the model's boughs.
- **A small thing in the wind** (`"sway": "caps"` for mushrooms; or any sway whose moving part is under 700 pixels; force either way with
  `"sway": {"parts": "caps" | "leaves" | [{colour, within}], "by": "patches" | "model"}`): at 20 px across the model cannot tell one cap's
  pixels from the next, so the parts are read off the sprite - each patch of the moving colour a part, two that touch told apart by their
  middles, the dark line round a part going with it. A smooth cap left under its moved self would show as a second edge, so the parts are
  lifted first (`"lift": true` in pixel.json): what a cap leaves bare is the stem under it carried up, or nothing. 2 frames a second.
- **Where it is in the way** (free, with the shadow; `"collide": false` to leave out): `solid-<view>.png` - what stops a walker: the prop
  below 0.4 m (`"collide": {"walk": 0.4}`) pressed onto the ground and what lies between (four legs: the table; a trunk's foot, not the
  boughs that hang low); and for `"collide": {"cover": [0.55, ...]}` (or `propshade.py --cover 0.55`) `cover-<h>-<view>.png` - the model
  0.1 m each way of that height, pressed down: what stops an arrow, a ball, a fireball flying that high (a trunk; not the crown above;
  a mushroom is too low and has none). White = blocked. In pixel.json each view's `"solid"` / `"cover"`: `file`, `at` (its top-left in
  the sprite's pixels), `hull` (its outline, up to 10 points, for a collision polygon). Both lie ON THE GROUND: test a flying thing at
  the ground point under it. Look at `preview-collide.png` (red: a walker; blue: in the air) and **show it**.
- **A character in its shade**: each view's `"shadow"` has `height_m` (the prop's) and, in sun, `per_m_up` [dx, dy]. A point of her
  h metres up, standing at ground pixel (x, y), is shaded by the shadow's alpha at (x, y) + h x per_m_up - only if h < height_m (a rock
  shades her feet, not her head). Feet (~0.05 m), middle (~0.6) and head (~1.1) each ask; darken that part by about 0.95 x the alpha
  (in Phaser a four-corner tint: top = head and middle, bottom = middle and feet). Several props: the light left is what each leaves
  in turn. A grey day: `per_m_up` is [0, 0]; a lamp: not given (its shade is not a shift).
- **Into an engine**: `export.py PROP/out-pixel` (free; it hands a prop on to `propexport.py`) -> `export/phaser/<name>.js`
  (`preload(scene, base)`, `add(scene, x, y, side)` -> the prop at its FOOT: light with ADD, shadow, body playing the wind; `.wind(0|1|2)`,
  `.solid(x, y)`, `.cover(x, y, h)`, `.shade(x, y, h)`; `shadeOf(props, x, y, h)`) and `export/godot/<name>.tscn` + `.gd` (a Node2D at the
  foot: Light, Shadow, Body - an AnimatedSprite2D when it sways - and Solid, a StaticBody2D with the footprint's polygon; `side`, `wind`;
  `solid_at()`, `cover_at()`, `shade_at()`), both with `<name>.prop.json`: every layer's place from the foot. Checked by opening them:
  Phaser 3.90 and Godot 4.7. **Unity and Aseprite are not written for props yet** (characters have them).
- **A character in a prop's shade** (the game's part, from the shadow pictures): for a point of the character h m up, read the prop's
  shadow on the floor where the line from it away from the sun comes down - from its feet, (-0.42 h, -0.39 h) x px_per_m on screen
  for SpriteCast's sun - counting only props taller than h (a rock shades the feet, not the head), and darken the character there.
  Rain Girl reads feet, middle and head (0.05, 0.6, 1.1 m) and tints her top and bottom in steps (`shadeOn` in its game.js).
- **Moving the light by hand**: `PYTHON lightedit.py PROP.json` (free) opens a page on 127.0.0.1: drag on the floor to move the lamp,
  the wheel for its height, a slider for its size, or the sun / a grey day; the shadow is redrawn as it moves (a quick bake, ~0.15 s).
  Save bakes every side properly into out-pixel/ and writes the light into the spec (`"lamp"` or `"shadow"`), so proppixel.py keeps
  it. Offer it to a user placing a prop in a lit room, or who is not sure where the light should be.
  **Their own lamp**: "Your lamp..." loads a picture of it (a cut-out PNG at the prop's scale); its foot is found (the middle of its
  lowest row), its light point guessed (as high as its brightest warm pixels) and set by a click on it; it stands where it is dragged,
  drawn in front of or behind the prop by where it stands, its light's height from the picture. Saved as `"lamp": {"at", "size",
  "picture": {"file", "foot", "light"}}`; `lamp.png` is then their picture and pixel.json's `lamp` has its `foot` and `light` (draw
  it with its foot on the side's `lamp.spot`). A click on the lamp sets its light point or its foot (a switch); a red cross shows where it
  stands, a yellow ring the light's size. **Scale**: 0.25-3x from the picture as loaded (kept as `lamp-source.png`) - bigger by whole
  pixels (nearest), smaller by pixelsmall's reducer (outlines kept) - with its height in metres at the prop's scale shown, to match.
  **Their lamps**: a picture loaded is named and kept in `~/.spritecast/lamps/<name>/` (for every prop), a button of its own beside
  SpriteCast's (`examples/lamps/`); "Save this lamp's settings" keeps its scale, foot, light point and light size with it
  (`lamp.json`) - one of SpriteCast's saved so becomes theirs. "Bake & save the scene" bakes and writes the spec; the page opens as saved.
  "Delete this lamp" (two clicks) takes one of theirs out of their lamps, or puts one of SpriteCast's back as it came. A picture
  loaded may be any kind (PNG, JPG, WebP): without see-through its background - the colour round its edge - is cut away; pixel art
  shown enlarged (every pixel an N x N block) is taken back to its own pixels first; one far too big or small starts at ~1.5 m. **The look**: `"light_style": "pixel"` (the glow and the floor's light in steps,
  dithered - the default) or `"smooth"` (gradients), a switch on the page - the shadow too: in five steps, or a gradient for a
  game not drawn in pixel art (`propshade.py --style smooth`). A pixel floor lamp to try: `examples/lamps/floor_lamp/out-pixel/sprite.png`.
- **See-through parts**: a model from a description is solid where a weave, leaves or a net would let light through (it is painted on).
  `"see_through": [{"colour": "#c8955a", "open": 0.35, "within": 90}]` - the parts painted near that colour pass that share of the
  light; the rest stays solid. Offer it for wicker, a tree's crown, a lace curtain, a fence.
- **By hand**: `PYTHON pixeledit.py PROP.json` opens the same page as for a character - the views are the frames of one strip,
  "views" - for the user to finish a cut-out (magic erase) or fix a pixel. Kept in `<prop>/pixel-touch.json`, laid on again by every run of
  `proppixel.py`; a view drawn anew has its edits set aside. Offer it; a user who wants the cut-out their own way asks for exactly this.

