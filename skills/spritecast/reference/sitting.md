# Sitting and seats (`charpipe.py sit`, `seat.py`)

## Seated views of a character (`charpipe.py sit`)
Needs the character's walk drawn first (its rig and drawings are what the seated views follow). People only.

| step | what | cost |
|---|---|---|
| `charpipe.py sit CHAR.json` | the rig bent into sitting - thighs level, knees bent, hands on the thighs - in 8 facings, each with its 3D shadow and a height map (`render/sit-<facing>.png`, `-s.png`, `-h.png`, `render/sit.json`), on nothing: the game's own chair goes under them | free |
| `charpipe.py sit CHAR.json --draw [--yes]` | two sheets of 4 drawn like the standing views, then finished: `out/sit-<facing>.png` (a box of their own), `"sit"` in `out/character.json` | ~$0.22 |

`"sit"` in `character.json`: `frame` ([w, h]) and per facing `file`, `seat` (the point to put on the chair's seat, a fraction of the
frame, like `anchor`), `seat_height` (in the figure's heights) and `shadow` (`file`, `offset` from the frame's top-left). Use the facing
the chair faces. `"sit": {"hip", "knee", "arm", "elbow"}` in the spec changes the pose (degrees; defaults 88, 88, 10, 50).

## On a prop (`seat.py`)
`seat.py PROP.json CHAR.json [--view turn-90] [--height 1.3] [--at X,Y[,Z]] [--facing south-west] [--sink 0.03]` (free)

- Needs the prop finished (`sprite.png`, `render.json`, `render-height.png` - re-run `isoprop.py render` if the height picture is
  missing) and the character's seated views drawn (`frames/sit-*`, `render/sit-*-h.png` - re-run `charpipe.py sit` for the heights).
- Finds the seat's height at the footprint's middle (or `--at`), which way it faces (away from the backrest, along the footprint's axes
  or a diagonal), and sits the character back until the knees are just past the seat's front edge (a child on a deep seat sits forward).
- Works out the prop's **front piece** for that sitter: where both have a pixel, the one nearer the camera is in front
  (y/s · cot θ + h/sin θ from each pixel's screen row and height). Where a drawing goes past its 3D outline the nearest 3D pixel stands in.
- → `<view>/seat/<char>-<facing>/`: `front.png` (the prop's picture where it stands in front of them; draw it over the sitter at the
  sprite's place), `seat.json` (`top_left_in_sprite`, `scale`, `frame_px`, how it was made), `preview.png`.
- Ask the character's height (`--height`, else the spec's `"height_m"`, else 1.7 m).
- A seat hidden behind its own back in this view, on a 3D model without blocks: `--at X,Y,Z` with the seat's height read from the
  front view.
- Several views of one prop (`turn-0` … ): one run per `--view`.
- Show the preview. A sitter a little off: move them on the touch-up page (reference/touchup.md) - it re-makes the seat from there.
