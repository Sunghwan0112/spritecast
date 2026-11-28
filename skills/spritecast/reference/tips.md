# Building guides that draw well

Learned making a few hundred props for an isometric life-sim.

- **Real sizes.** Look things up: a seat 42-46 cm high, a table 74 cm, a counter 90 cm, a door 2.0-2.1 m, a person 1.6-1.8 m. A prop
  that is "about right" in metres looks right next to everything else; one sized by eye on screen never does.
- **Round things are cylinders** (`"axis"`): plates, legs, pots, lamps, bars. A square block drawn "as round" comes back muddled.
- **One block per part the model should see**: a seat, a back, each arm, each leg. The model follows the blocks' edges, so a part
  without a block tends to vanish and a block without a part in the description turns into something odd.
- **Mind the screen columns.** On screen, things at the same x − y line up vertically: a tall part right behind another part's front
  end hides behind it. Move it a little, or the drawing will merge the two.
- **Give organic things a volume, not a shape**: a plant's leaves as one cylinder, a pile of cushions as one box. Say in the
  description that it fills that volume, and set `"loose": true` so leaves that spill past it aren't squeezed back in.
- **Square-on views** (`topdown`, `front`): a style picture drawn at an angle pulls the model toward that angle. The prompt says so,
  and `finish` catches it, but a style picture seen from the same view works best.
- **Say what must not be there** when the model adds things: "no rug, no books on top, no logos, no text".
- **Colours in the blocks are hints**: close to the final colours helps the model keep the materials apart.
- **Facing**: the visible faces are +x (right) and +y (left). Things meant to face the viewer put their front on one of those.
- **Big and flat things** (rugs, floor decals) don't need this - draw them top-down and skew them onto the floor.
- **Tall things** (trees, lamp posts, buildings) work the same; raise `px_per_m` only if details get lost, lower it for buildings.
- **Your own style**: one finished prop in the look you want, alone, on a flat background, is the best reference. A whole scene
  works less well - the model copies its content.
- **A 3D model** (`"model"`) beats blocks for complex shapes (a car, a statue); blocks are enough for furniture.
- **Cost**: one drawing at `high` ≈ $0.07 (gpt-image-2.6, 2026). `SPRITECAST_QUALITY=medium` ≈ $0.06 (most of the cost is the two
  input images), `low` looks rough. Try a new idea on one prop before many.

- **Which image model**: `gpt-image-2.6-sunburst` is the default since 0.29.0 (the user's decision, 2026-11-26: "the earlier
  judgment that 2.5 was better looks like an error"). `SPRITECAST_MODEL=gpt-image-2.5-sunburst` draws with the one before - the
  same price per token, and in what was measured the same cost a sheet ($0.07-0.10). `SPRITECAST_MODEL` applies to every drawing
  in the run: do not mix the two into one set without looking.
  - **What decided it** (the rain girl in a side view, 2026-11-26, seven sheets with each): 2.6 kept closer to the guide - a walk's
    overlap 0.94-0.96 against 0.90-0.94, the head nearer the 3D model's size (x0.96 against x0.92), a two-move umbrella combo
    0.66-0.89 against 0.53-0.81, the held thing off its place in 1 frame against 5 - at the same $0.23 and $0.36. It shades more
    (folds and gloss on a raincoat). One character, one run each.
  - **What the first comparison found** (2026-11-13, seven sheets, 2.5 kept then): 2.6 better at a held thing's own colours and at
    the two sheets of one walk coming out the same size; worse once - the second sheet of a walk with a thing in the hand repeated
    the first half's arm, twice running - and pixel art no better (a heavier outline, black hair a little brown). That arm has
    not been drawn again with 2.6 since: if a second sheet copies the first one's arm, draw that sheet with 2.5 and compare.
  - The checks' thresholds were tuned on 2.5's drawings. Nothing has shown them wrong for 2.6, and nothing has been measured.

## Scenery for a side-scrolling game (a castle wall, a house front)
Learned on the castle wall of the side-view example game; the user turned down the first three tries.
- **Seen as the characters are**: from the side, nearly level - `"camera": {"pitch": 6, "yaw": 90}`. Of a top only a thin strip shows.
  Rendered 12° from above, its tops became wide floors - scenery seen from above beside characters seen from the side ("almost Picasso").
- **Over a lit 3D model, not grey blocks.** Over blocks the drawing came out flat: a guide with no light gives the image model nothing to
  model stone by. `isoprop.py model` (Tripo from words, ~20 credits) with a description that says where things are ("merlons ONLY along
  the back edge, the walk open in front of them"). A model made from a drawing (its front, and its mirror for a back) put battlements on
  both edges and left crooked corners - prefer words.
- **Tripo builds in its own proportions** (the wall came out barely longer than its tower) and may stand a little crooked. On the render,
  before drawing: level it, mirror it if the light should come from the other side, and lengthen it by repeating one period (crenel middle
  to crenel middle). Check the platforms against the render: at `px_per_m` 96 one render pixel was one game pixel, so the walk and the
  tower's roof could be read straight off it.
- What characters go behind (a tower's front parapet) is a picture of its own over them; in the example game it is painted as a mask, and
  goes see-through while the player is behind it.

