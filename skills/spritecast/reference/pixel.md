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
default; any action in the spec), `--dirs` which facings (all eight by default), `--again NAME` one sheet anew (a name from the
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
  (30 %): the game lays it under the sprite at that alpha.
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
names, or a rest pose unlike either, comes out twisted - say so rather than draw it.

## The review, and drawing again

Every run checks every frame, as `finish` and `redraw` do for the illustrated ones, and ends with a line `REVIEW: N of M frames to
look at`:

- `pose 0.52` - the frame's outline covers its render's by less than `"redo_below"` (0.75 in the spec): the image model drew
  another pose (a throw's follow-through with the arm still out where the render has it down).
- `<thing> missing` / `<thing> drawn after it was let go` - the held thing is not where the render has it, or is there after the
  release.

`out-pixel<px>/review.png` has each marked frame beside its guide, and `pixel.json` lists them under `review`. **Show the user
review.png, not all the frames.** `PYTHON pixelart.py CHAR.json ... --redraw` says which sheets it would draw again and what that
costs; with `--yes` it draws them (twice at most a sheet) and keeps whichever drawing is better - fewer frames with the held
thing wrong first, then the higher lowest overlap; the other is kept as `<sheet>-out.try<N>.png`. A frame that is only a little
under 0.75 with the pose right is the user's call: show it and ask.

## Fixing by hand: `pixeledit.py`

Pixel art is not all to be had by rule: a patch of paper left where an arm crosses the body, a face that came out poorer in one
frame than in the next. `PYTHON pixeledit.py CHAR.json [--px 96] [--port 8766]` (free) serves a local page with every animation,
frame by frame, big, on a grid. **It is a server: run it in the background** (`--no-open` when no browser should open on this
machine), give the user the address, stop it when they say they are done. It saves as they draw.

| tool | does |
|---|---|
| erase (E), pencil (B) | a pixel at a time, or dragged; brush 1-6 px (`[` `]`); the palette is the animation's own colours, most used first |
| magic erase (W) | click a patch of one colour - white left between an arm and the body - and the whole patch goes. "alike": how near a colour counts as the same; "whole frame": every such pixel, not only the patch that touches |
| change colour (G) | click a colour in the frame: it becomes the chosen colour - that patch, the whole frame, or (ticked) every frame of the animation |
| pick colour (I, or Alt-click) | the colour under the pointer |
| select (M), move (V) | drag a box; move drags what is in it, the arrow keys nudge it a pixel |
| copy, paste (Ctrl+C / Ctrl+V) | a face that came out well in one frame, into another: paste, click to set it down - or "paste in every frame, same place" |
| bring back (R) | takes the edits off where it is rubbed; "this frame as it was" takes them all off |
| ◀ ▶ (← →), play (Enter), "the frame before, faint" | to see a fix in motion and against its neighbour |
| wheel, Space + drag, "behind" | zoom at the pointer, move the picture, the colour behind the sprite (white specks show on a dark one, dark specks on a light one) |

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

The image model draws its "pixels" about 7.5 px big whatever the guide asks, so what `--px` buys is limited: asked for 96 the
figure comes out about 94-100 px, asked for 128 only about 104. 96 is the size to offer. For 48-64 px a character needs a design
made for that size (a bigger head); below that it is hand work - say so.

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

## Other ways to a face (options; the default is the model's own face, read carefully)

`--face-patch`: one head per facing drawn on its own sheet at 16 px a pixel, its face cut out and laid on every frame's own face -
the same eyes in every frame, at the price of a paid sheet. `--heads`: that whole head on every frame (seams at the neck to mind).
`<character>/pixel/head-edits-<facing>.json` (the format in `facefix.py`) corrects such a head once for all its frames.
