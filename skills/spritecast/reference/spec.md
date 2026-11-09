# The spec (`<name>.json`)

```json
{
  "name": "reading_armchair",
  "footprint": [0.82, 0.86],
  "facing": "its seat faces down-left, toward the viewer",
  "description": "a mid-century reading armchair: plump cognac-tan leather cushions ..., a solid walnut frame on four short tapered legs",
  "blocks": [
    {"box": [0.08, 0.74, 0.12, 0.84, 0.12, 0.40], "color": "#b06a3c"},
    {"box": [0.03, 0.09, 0.07, 0.13, 0.00, 0.12], "axis": "h", "color": "#5a3b25"}
  ],
  "style": "cozy",
  "px_per_m": 256
}
```

| key | |
|---|---|
| `name` | output folder name (next to the spec, or `--out`) |
| `footprint` | `[W, D]` metres: W along **x**, D along **y** |
| `blocks` | boxes `[x0, x1, y0, y1, h0, h1]` in metres; `"axis": "x" \| "y" \| "h"` makes the box a cylinder along that axis (round things must be cylinders); `color` any CSS colour; `{"arc": [cx, cy, r0, r1, a0, a1, h0, h1]}` a curved sector instead (a curved bench's seat or back: its circle's centre in the footprint's metres - it may lie outside it -, the radii, the angles in degrees from +x toward +y, the heights) |
| `model` | instead of / besides blocks: `{"glb": "path.glb", "size": [W, D, H], "yaw": 0}` - a 3D model scaled to that box, turned `yaw` degrees first. `isoprop.py model` makes one with Tripo and writes this for you (the blocks kept as `blocks_draft`); `yaws` shows the four turns to pick `yaw` |
| `description` | the finished object - materials, colours, details. What fills each block |
| `facing` | which way its front faces on screen, in words (helps the model) |
| `camera` | `"iso-2:1"` (default: 30° down, footprint a diamond, tiles 2:1), `"isometric"` (true isometric, 35.26°), `"topdown"` (3/4 top-down, 50°, square on), `"front"` (12°, square on, side-scroller), or `{"pitch": deg, "yaw": deg}` |
| `views` | turns to draw, e.g. `[0, 90, 180, 270]` for all four facings: one folder each (`turn-<deg>/`); the later ones are drawn with the first drawing as a reference, so it stays the same object |
| `light` | `"right"` (default: light from the upper right, shadows up-left) or `"left"` |
| `character` | a person instead of blocks: `{"height": 1.7, "build": "slim" \| "average" \| "broad", "pose": "stand" \| "wave" \| "point" \| "hold" \| "arms-crossed" \| "walk" or {"base": preset, "arm": {"left"\|"right": [[out, fwd], [out, fwd]]}, "leg": {...}}, "directions": [...]}` - a mannequin is built for you (footprint 0.5 m, anchor between the feet, `loose`); directions from `south` (toward the viewer), `south-east`, `east`, `north-east`, `north`, `north-west`, `west`, `south-west`; default the four diagonals. One folder per direction. Extra `blocks` (a bag, a hat brim) are added to the mannequin |
| `shadow` | `"guide"`: cast in 3D from the blocks, exact for solid things (the default). `"drawn"`: the finished drawing's silhouette, each pixel moved by the guide's 3D height under it (render-height.png) - the drawing's shape (hair, clothes, leaves), every foot and base starting its shadow where it stands; higher up (10-35 % of the height) easing into a smooth height read off the screen, for a natural shadow above; where it stands, the guide's own 3D shadow of its blocks up to 12 cm (render-contact.png) (the default for characters and `loose`) |
| `loose` | `true` for plants and other loose shapes that may spill past their guide: fitted by height, not checked for proportions |
| `style` | a bundled style name (`cozy`) or a path to your own style picture |
| `look` | optional: replaces the default words describing the style |
| `px_per_m` | render scale, default 256 (a 1 m tile edge is ~181 px across on screen) |

## Custom poses
`"pose": {"base": "stand", "arm": {"right": [[80, 10], [165, 15]]}}` - the base preset with those limbs replaced. Each limb is two
parts: upper arm then forearm, thigh then shin. Each part is `[out, fwd]` degrees from hanging straight down: first turned `out` to
its own side (negative: across the body), then swung `fwd` forward (negative: back). `left` and `right` are the figure's own (facing
the viewer, its right hand is on the screen's left). Examples: a raised hand `[[80, 10], [165, 15]]`, an arm pointing ahead
`[[8, 80], [8, 88]]`, hands on a cup `[[6, 8], [-35, 70]]`, a leg stepping forward `[[2, 24], [2, 6]]`.

## Axes
- **x** runs to the screen's lower right (↘), **y** to its lower left (↙), **h** up. Metres.
- The footprint's **back** corner (top of the diamond) is x = 0, y = 0; the **front** corner (bottom) is x = W, y = D.
- The faces you see are the ones toward +x (right face) and +y (left face). Put a thing's front on the +y side to face down-left,
  on the +x side to face down-right.
- The default camera looks 30° down at the prop turned 45°: a ground tile is exactly twice as wide as it is tall on screen. The
  square-on presets (`topdown`, `front`) turn it 90°: x runs to the right, the +y side faces the viewer.
- `views` turn the prop on its footprint (the camera stays): turn 90 brings the right (+x) face round to where the left one was.

## Output (`<name>/`)
| file | |
|---|---|
| `render.png`, `render-shadow.png`, `render-height.png` | the guide, its shadow, and its height map (each pixel's height above the floor, 16 bits in red and green, up to `height_top` m in render.json) (free) |
| `input.png` | what the image model gets (the guide on magenta) |
| `drawn.png` | the model's drawing (paid; never overwritten without `--again`) |
| `sprite.png` | the finished prop, transparent, laid exactly over the guide |
| `shadow.png` | its shadow, solid black alpha - draw it at ~30 % under everything |
| `sprite.json` | `anchor` (fraction) / `anchor_px`: the footprint's lowest point on screen (its front corner, or the middle of its front edge when square on); `footprint_px`: its four ground corners (back, right, front, left); `shadow.offset_px` from the sprite's top-left; `px_per_m` |
| `sprite.json` `shadow.from` | which shadow it got: `guide` or `drawn` |
| `sprite.json` `fit` | `ok`, `proportions_off`, `outline_overlap`: how well the drawing follows its guide. Off by more than 10 % (or overlap under 80 %) → not squeezed to fit, `ok: false`, a warning |
| `preview.png` | sprite and shadow on a 1 m floor grid |

Shadows fall up and to the left (light from the upper right; mirrored with `"light": "left"`): from the blocks in 3D for solid
things, from the drawing moved by the guide's heights for characters and `loose` things (`shadow`).
