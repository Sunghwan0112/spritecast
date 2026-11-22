# The ground (`ground.py`)

The ground a map's sprites stand on, at the game's own camera and light: free, worked out on the user's computer, nothing drawn by an
image model. Four commands on one small spec (`GROUND.json`, keys in `ground.py --help`); each writes into `<name>/`.

| command | what | time |
|---|---|---|
| `meadow` | a meadow of 3D plants (grass, fern, wildflowers, clover - `ground/realistic`, Tripo-made, MIT) planted by a Gaussian density, with a path of earth, wheel ruts and 3D gravel; lit by the props' sun with every plant's shadow; pixel art in the user's palette; plus the plants cut into strips by their roots (`ground-front.*`) | ~5-10 min for 960 x 540 |
| `terrain` | a 3D height map's slopes (low Gaussian hills, tens of cm) lit by the same sun: `terrain.png`, laid OVER the ground and the path | 1 s |
| `puddles` | five puddles, big to nearly dry, one shape shrinking: a shallow hollow of water (see-through at the edge, deep in the middle, the sky and the trees' shade in it at the camera's angle, a wet rim) | 1 s |
| `grass2d` | no 3D: the tufts of one seamless grass tile cut out and scattered by a Gaussian density (thick patches and thin, stretched 2:1 along the ground) - no repeat, no grid | 1 s |

## What the user chose, and why (Rain Girl, 2026-11-21) - keep to it unless the user says otherwise
- **No tile.** A tile laid square showed its square grid and seams (flipped copies do not match) - "the grid should be iso and not show".
  So the ground is ONE picture of the whole map (`meadow` or `grass2d`), never a repeated square.
- **Realistic plants, the props' palette.** Low-poly kit plants looked like toys beside Tripo trees; the user asked for plants "in the
  style of our trees": Tripo plants, coloured from the props' own palette (`"palette": "props/*.png"`), darker and less yellow for a rainy
  forest (`tone` 0.58, `saturation` 0.78). Textures are blurred and the light cut into four steps: pixel-art clusters, not grain.
- **Contrast and density were raised on request** ("the grass's light and dark clearer", "thicker"). A Gaussian density, not even
  scatter: "natural, like a meadow".
- **The path.** Plants beside it are lower (trodden) and lower still in front of it - a plant in front of a path (lower on the screen) stands
  up over it in this view; a verge of trodden earth outside its edge (a bare strip there read as a dark band - debug with `DEBUG=1`,
  `WIN=x,y,w,h` before a full render). The earth keeps its own browns in shade (the props' palette alone turned shaded earth green).
- **Puddles sunk, not swelling.** A bright lip on the far edge made them look like glass domes; a dark band on the far side only looked
  wrong; the water was milky - it is dark now, the sky in it dim, a soft wet rim all round.
- **Feet in the grass.** Her feet hidden by the plants in front of her, a tree's foot in the grass; NOT a fire monster's or a ghost's
  ("the grass not in front of them": fire burns it, ghosts float). Not inside a puddle (the grass came up through the water).

## The plants in front, in an engine
`ground-front.json` (and `.js`, `GROUNDFRONT`): strips `[depth, x, y, w, h, ay]` - a strip is the plants rooted in 3 px of ground; `depth`
is their root's y (as a sprite's depth is its foot's y). Draw the whole meadow (`ground.png`) at the bottom; then, ONLY where it matters,
draw strips at their depth so they cover whoever stands behind them - drawing them all would cover the props' baked shadows on the grass:
- round a walker's feet, every frame: strips with `y < depth <= y + 10`, cropped to `x ± 14` (her feet; a reflection-free puddle cell: none);
- round a prop's foot, once: strips with `y < depth <= y + 12` (a trunk, a stump; 7 for a bush or a rock; none for something very low).

```js
// Phaser 3: ground.png at depth -1000; frames from ground-front.png
const t = this.textures.get('front'); GROUNDFRONT.forEach((r, i) => t.add('s' + i, 0, 0, r[5], r[3], r[4]));
const near = (x, y, half, reach) => GROUNDFRONT.flatMap((r, i) => r[0] > y && r[0] <= y + reach &&
  Math.min(r[1] + r[3], x + half) > Math.max(r[1], x - half) ? [[i, Math.max(r[1], x - half), Math.min(r[1] + r[3], x + half)]] : []);
for (const [i, a, b] of near(hero.x, hero.y, 14, 10)) {          // every frame, from a pool of images
  const r = GROUNDFRONT[i]; pool[n++].setFrame('s' + i).setPosition(r[1], r[2]).setOrigin(0).setCrop(a - r[1], 0, b - a, r[4]).setDepth(r[0] + 0.25).setVisible(true);
}
```
