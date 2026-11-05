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
- **Cost**: one drawing at `high` ≈ $0.07 (gpt-image-2.5, 2026). `SPRITECAST_QUALITY=medium` ≈ $0.06 (most of the cost is the two
  input images), `low` looks rough. Try a new idea on one prop before many.
