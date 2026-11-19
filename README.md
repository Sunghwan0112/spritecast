<h1 align="center"><img src="docs/banner.gif" alt="SpriteCast" width="100%"></h1>

<p align="center"><b>One illustration in. A game character out.</b><br>
An isometric sprite generator for Claude Code: 8-direction walks, actions and pixel art<br>
at your game's camera angle, with a 3D shadow under every frame - and the props to stand beside them.</p>

<p align="center"><a href="https://github.com/Sunghwan0112/spritecast/stargazers"><img src="https://img.shields.io/github/stars/Sunghwan0112/spritecast?style=social" alt="GitHub stars"></a></p>

<p align="center">
<a href="#what-you-can-make">What you can make</a> ·
<a href="#walking-characters">Characters</a> ·
<a href="#pixel-art-arcade-size">Pixel art</a> ·
<a href="#props-and-scenery">Props</a> ·
<a href="#install">Install</a> ·
<a href="#faq">FAQ</a> ·
<a href="README.ko.md">한국어</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a>
</p>

![GPT alone: one direction, the same leg always in front, no shadow. SpriteCast: the same character walking in eight directions on the game's floor, each with its shadow; a row of actions from the same 3D, the swing throwing water; and as pixel art](docs/hero.gif)

<p align="center"><i>The same image model, the same character sheet. Left: GPT asked for a walk, as it came out. Right: what the 3D adds.</i></p>

![a ramen street cart as a 3D model from four sides, and the same four sides as pixel-art sprites beside the small pixel character](docs/pixel-props.png)

<p align="center"><i>And things, not only people: any object as pixel art, from any side, at the character's scale. <a href="#pixel-art-props-any-object-any-side">How</a>.</i></p>

```
claude plugin marketplace add Sunghwan0112/spritecast
claude plugin install spritecast@spritecast
```

Then just ask: *"Here's my character (hero.png). Make her walk in 8 directions."*
**To try it free, with no key**, ask Claude to *"try SpriteCast"*.

An image model (OpenAI's, with your own key) does the drawing. The body, the motion, the angle and the shadow come from 3D - so
every frame is the same person, and she actually walks.

| | you give | you get | you pay |
|---|---|---|---|
| **A walking character** | one illustration | a walk in 8 facings, standing views, a shadow per frame | about $2.2 + 75 Tripo credits |
| **More actions** | a name, or a Mixamo FBX | run, jump, slash, throw... in 8 facings | about 10 Tripo credits each (an FBX: none) + the drawing |
| **Pixel art** | a character that walks | pixel sprites about 100 px tall | about $0.075 a sheet (a walk, 8 facings: ~$1.35) |
| **An animal** | one illustration | a four-legged walk in 8 facings | 30 Tripo credits + the drawing |
| **Sitting** | a character that walks | seated in 8 facings, placed on your props | about $0.22 |
| **A prop, or a posed NPC** | a description | a sprite, its shadow, its anchor | about $0.07 (+ $0.08 a further facing) |
| **A pixel-art prop** | a description | pixel sprites from every side, at the pixel character's scale | about 20 Tripo credits + $0.08 a side |

Free and MIT. You pay OpenAI and Tripo directly; every paid step shows its cost and waits for your OK.

**Half the drawing: four facings.** `"facings": 4` in the spec draws only the diagonals (south-east, south-west, north-east,
north-west) - about half the drawing cost (a walk: ~$1 instead of ~$2; in pixel art ~$0.7 instead of ~$1.35). The exported character
still walks in all eight directions: asked for east, it shows the nearest facing drawn and keeps it, so walking straight across does not flicker.

## What you can make

| | |
|---|---|
| ![walking in 8 facings](docs/character-walk.gif) | ![running, jumping and slashing with an umbrella](docs/actions.gif) |
| **[A walk in 8 facings](#walking-characters)** from one illustration, a shadow per frame | **[Actions](#more-actions-run-jump-slash)**: run, jump, slash - or any Mixamo clip |
| ![pixel-art sprites throwing snowballs five ways on an isometric floor](docs/pixel-throw.gif) | ![an orange tabby in a yellow raincoat walking in 8 facings](docs/animal-walk.gif) |
| **[Pixel art](#pixel-art-arcade-size)**, about 100 px tall, with things that are held and thrown | **[Four-legged animals](#four-legged-animals)**, with no bought rig |
| ![the rain girl seated on ten different seats](docs/seats.png) | ![guide → sprite](docs/showcase.png) |
| **[Sitting](#sitting)** on your props, the armrest in front of her worked out in 3D | **[Props](#props-and-scenery)** at their real size, all on one floor |
| ![a rattan peacock chair as pixel art under the sun, on a grey day, under a bare bulb, a lamp in front and behind it, and a big light above, on an oak floor lit by each - each shadow baked from its 3D model, the weave letting light through](docs/indoor-shadows.png) | ![a pixel-art tree from two sides swaying in the wind - clumps of leaves moving a pixel at a time, the trunk still, a gust leaning the top - and the same clumps in colours, cut from its 3D model](docs/sway.gif) |
| **[Shadows baked from the 3D model](#light-shadow-wind)**: the sun, a grey day, or a lamp you place yourself | **[Wind in the leaves](#light-shadow-wind)**, bough by bough, from the same model |

## Things to ask for

- *"Here's my character (hero.png). Make her walk in 8 directions."*
- *"Add a run and a jump. And a throw - here's a Mixamo clip (Throw.fbx); put a snowball in her hand."*
- *"Our game is pixel art. Make her walk and throw as pixel sprites, about 96 px tall."*
- *"Make her sit, and put her on this armchair."*
- *"Make a shopkeeper NPC, an old man in a brown cardigan, in four directions."* (a posed figure: a description is enough)
- *"Make an isometric bookshelf, 1.8 m tall, full of books, in the cozy style."*
- *"Here's a prop from my game (props/barrel.png). Make a matching crate in that style."*

## Why it works

An image model can't keep a body and a pose from one frame to the next. Asked for a walk in words, it gives eight nice drawings
that don't walk - the left of the picture at the top, as it came out:

| GPT alone | SpriteCast |
|---|---|
| the same leg in front in all eight frames | the legs come from a 3D walk |
| the arms twitch at random | the arms swing against the legs |
| the camera at eye level | your game's camera (30° down by default) |
| no shadow | the 3D body's own shadow, frame by frame |

So SpriteCast never asks it to. **3D does the moving; the image model only redraws** each rendered frame in your illustration's
look. Every drawing is then fitted back onto its render and checked against it: a frame drawn in another pose is flagged and can
be redrawn, never squeezed to fit. Props work the same way, with blocks at real size in place of the rig.

**What you get from that:**
- **The angle and size are right.** The solid props in the examples land on their guide at 95–99 % outline overlap; the plant,
  drawn loosely on purpose, at 87 %, and the dressed figures at 69–88 % (clothes and hair go past the plain mannequin). Walking
  characters are scored frame by frame (below). The camera and the scale are fixed, so props made at different times line up on one floor.
- **Shadows that look right.** One light shared by every prop, so every shadow falls the same way. Solid props cast the 3D
  guide's own shadow. Posed figures and plants cast a shadow in the drawing's own shape (the hood, the hair, the leaves), placed by
  the 3D model, so a foot or a pot's base starts its shadow where it stands. Walking characters cast their 3D body's own shadow,
  frame by frame. Not a painted blob, not a blocky mannequin.
- **It checks itself.** After drawing, the result is compared with its guide. If the model drew another angle, nothing is squeezed to
  fit: you get a warning, and Claude suggests a fix before drawing again.
- **Your game's view and your style.** 2:1 isometric, true isometric, 3/4 top-down, front or any angle; all four facings of one
  object; the bundled `cozy` style or one picture of your own.
- **Light that agrees.** Every guide is lit by the same sun, fixed to the screen, and the image model draws over that render: the
  light and shade on a thing come from its 3D shape, the same way on every side of every prop. Nothing is shaded by hand
  ([in a game](#made-with-it-rain-girl)).

## Made with it: Rain Girl

<p align="center"><a href="https://sunghwan0112.github.io/rain-girl/"><img src="docs/rain-girl-play.gif" alt="Rain Girl: a girl in a yellow raincoat among pixel-art trees, rocks and bushes, with red, green and purple fire monsters and burning ground" width="100%"></a></p>

<p align="center"><a href="https://sunghwan0112.github.io/rain-girl/"><b>▶ Play it in your browser</b></a> &nbsp;·&nbsp; <a href="https://github.com/Sunghwan0112/rain-girl">the game's code</a><br>No install, no account. Post your score and you are on the board below.</p>

<p align="center"><a href="https://sunghwan0112.github.io/rain-girl/"><img src="https://raw.githubusercontent.com/Sunghwan0112/rain-girl/main/leaderboard.svg" alt="Rain Girl's leaderboard: this month's best ten and the best three ever, redrawn every half hour"></a></p>

<p align="center"><i>Rain Girl, a small pixel action game: a girl in a yellow raincoat puts out fire monsters with her umbrella's
water before the forest burns. The girl and every prop in it came out of SpriteCast.</i></p>

- **The girl.** One illustration; a Tripo model, rigged and rendered at the game's camera (2:1, 30° down): a walk with her umbrella,
  the swing and standing, in the four diagonal facings (`"facings": 4`), every frame redrawn as 96 px pixel art. The water she throws
  is the swing's effect, rendered in 3D and drawn the same way; the standing loop is `idleclip.py`.
- **The forest.** Seven props - a tree, a half-burnt tree, a burnt tree, a bush, a burnt stump, a rock, mushrooms - each a Tripo model
  rendered from four sides at the girl's scale (74 px a metre: a 2.4 m tree is about 175 px tall) and drawn as pixel art: 28 sprites.
  The game shows each prop from one side at random; a tree that burns goes half-burnt, then burnt, from the side it stood.
- **One light, no shading by hand.** All 28 are lit from the upper right, as their 3D guides were. Below, every side of every prop:

![the 28 prop sprites on the game's grass: four sides each of a tree, a half-burnt tree, a burnt tree, a bush, a stump, a rock and mushrooms, all lit from the upper right](docs/rain-girl-props.png)

- **One palette.** Afterwards the props and the grass tile were put on one 48-colour palette (from 755), so a tree's greens and a
  bush's are the same greens.
- **The 3D keeps working in the game.** The shadows on the ground are baked from each prop's model ([how](#light-shadow-wind)), and the girl darkens in a prop's shade - her
  feet, middle and head each by what lies between them and the sun. Where a fireball breaks on cover comes from each prop's own model, cut at the fireball's
  height (0.55 m), for the side that is showing: a trunk stops it, the crown above does not, a mushroom is too low.
- **The wind is the model's too.** The crowns sway bough by bough: the leaves are grouped into clumps by where they are on the 3D
  model, and each clump moves whole, a pixel at a time - with the round's wind, harder in a gust ([how](#light-shadow-wind)).
- **A prop's cost:** about 20 Tripo credits for the model and about $0.3 to draw its four sides.

## Walking characters

![an illustration → 3D → drawn frames → an 8-facing walk](docs/character.png)

Give it one illustration of a character (facing front, standing straight, no pose) and you get a walk in 8 facings (8 frames each) and 8 standing views, in that
illustration's look. An image model can't keep a body and a pose from frame to frame, so the motion comes from 3D:
1. A turnaround is drawn from the illustration.
2. [Tripo](https://www.tripo3d.ai) makes the 3D model from it, rigs it and gives it a walk and an idle.
3. The walk is rendered with the game's camera (free), each frame with the 3D body's own shadow, pressed flat onto the ground
   along the light.
4. The image model draws over the renders, 4 frames a call. The front is drawn first and every other facing follows it, so it
   stays the same person.
5. Every frame is fitted back onto its render, the head sizes steadied and the edges cleaned. You get strips, a shadow per frame
   (the feet touch it, a lifted foot casts its own) and an anchor.

```
$PYTHON skills/spritecast/scripts/charpipe.py turnaround hero.json --yes   # then 3d (model, rig, renders) and draw (then finish, preview by themselves)
```
All eight facings are drawn by default. A design that is the same on both sides can set `"mirror": true` to flip the west facings
from the east ones (each keeping its own shadow), about $0.66 less.
Or `"facings": 4`: the four diagonals only, about half the drawing; the exported character shows the nearest of them for any of the eight directions.

Cost per character: about $2.2 (OpenAI; ~$1.5 with `"mirror": true`) and 75 Tripo credits (~$0.75; an animal 30). Or bring your
own rigged GLB (`"rig_glb"`) and skip to `render`.

<details>
<summary><b>More: the preview video, Meshy, and the example character with her rig</b></summary>

`preview` also makes `walk-all.mp4` (every facing walking at once, with ffmpeg): the quickest way to see a head that grows and
shrinks or a frame that jumps. Tripo sometimes sends a model back turned sideways or uncoloured; both are fixed for you.
`"modeler": "meshy"` (and `MESHY_API_KEY`) has [Meshy](https://www.meshy.ai) make the model instead (~30 Meshy credits); the rig
is still Tripo's.

More options (several outfits, anchoring on the soles) and lessons:
[reference/character.md](skills/spritecast/reference/character.md). The girl above is in
[`examples/rain_girl`](examples/rain_girl): her illustration, turnaround, spec, strips, shadows, `character.json` and the sheet.
She was made with Tripo alone: about $1.7 of drawing and 85 Tripo credits. Her rigged model is there too (`rig.glb`, with its walk,
run, jump and slash, MIT like the rest of the repo), so you can try the whole 3D side with no keys and nothing paid: copy the folder,
add `"draw": false` to the spec and run `charpipe.py render rain_girl.json` then `finish` - the strips, shadows and anchors come
from the 3D model itself. Her spec also shows what `"notes"` is for: the 3D render had dark streaks down the raincoat's sides and
inside the arms, and one line in `notes` ("no dark line, stripe or seam on it anywhere... leave them out") had them drawn out of
every frame - a flaw in the model fixed in the drawing, not in 3D.

</details>

### Four-legged animals

Tripo's rig for four-legged animals walks badly (no backbone, the shoulders hung off the neck), so an animal gets no bought rig.
With `"kind": "animal"` the 3D model alone (Tripo, ~30 credits) is enough: its skeleton is found from the mesh (the feet, the
back, the head, the tail, and which way it faces), it walks in a cat's or a dog's gait, and it gets the same drawing, fitting and
3D shadows as a person.

The turnaround is drawn on all four legs, each leg clear of the others, the tail out behind; clothes only snug ones (a knit vest, not a
cape or a scarf - anything hanging moves with the nearest leg). Check the renders before drawing: four legs, the head forward, the tail
behind. If Tripo's model grows an extra leg, make it again or use Meshy (`"modeler": "meshy"`).

![an orange tabby in a yellow raincoat walking in 8 facings](docs/animal-walk.gif)

The cat is in [`examples/tabby_cat`](examples/tabby_cat): an orange tabby in a little yellow raincoat (the girl's), its design,
turnaround, spec, strips, shadows and sheet - 30 Tripo credits and about $2.5 of drawing, redraws and design tries included. Its
frames fit their renders at 0.76-0.97 (north-east and north-west mixed frame by frame with `"mix"`, see reference/character.md).

### More actions: run, jump, slash

Beside the walk, a character can run, jump or swing something. List them in the spec, `"actions": ["run", "jump", {"name": "slash",
"hold": "umbrella"}]`: the rig gets those animations from Tripo (about 10 credits each; run, jump, slash, shoot, dive, climb, fall,
hurt and turn are there), and each is rendered, drawn and finished in 8 facings like the walk, into its own strips with a shadow per
frame. A slash needs something in the hand: `"hold"` builds it from simple shapes and puts it in the hand, so it moves with
every frame (an umbrella, a pistol or a water pistol for now; the right hand, or `"hand": "left"`). With your own rigged model, any clip in it can be an action. A held thing is described to the
image model part by part - most carefully the end at the hand (the handle, the first stretch of the shaft), which is small and against
the body and is where it guesses otherwise.

![the rain girl running, jumping and slashing with her umbrella - the slash seen from the side](docs/actions.gif)

**Most of it comes out in one go.** The rain girl's walk, run and jump fit their 3D renders at 0.78 or better in every frame, all
drawn once. The umbrella slash is harder (a thin thing that swings round the body): a weapon drawn in the wrong place is redrawn by
itself, and what is left fits a little looser where she bends deep - a pose drawn a touch more upright, which reads fine in motion.
Those frames are listed for you to look at; keep them or redraw them.

**Something carried all the time, in either hand** (you asked). Put `"hold"` in the spec itself instead of in one action -
`"hold": {"kind": "watergun", "hand": "left"}` - and the character has it through the walk, the standing views and every action.
Below, a water pistol in the left hand: the 3D guide above, the drawn frames under it.

![a water pistol carried in the left hand: walking west, walking east and running, the 3D guide above the drawn frames](docs/carry-left-hand.gif)

- **It stays in that hand.** A character with a thing in one hand is not the same on both sides, so no frame is ever made by
  flipping another - flipped, the thing would change hands. (`"mirror": "never"` asks for the same for any character that is not
  symmetrical: an eye patch, one sleeve.) Each sheet is told which hand and where its render has the thing, and afterwards every
  frame is checked against its render: of the 24 frames above, one was named for you to look at.
- **The hand closes on the handle.** A rig's fingers are out straight, and a drawing over that has an open hand beside a floating
  gun. So the guide bends the holding hand itself: the handle goes into the fist, the four fingers come round one side of it and
  the thumb round the other, each finger bent only until it touches. A thick handle gets a looser hand; one too thick to get a
  hand round is made thinner.
- **Look at the hand before anything is drawn.** In a frame the grip is a few pixels, so the free `render` step also saves the hand
  from all round, close up (`render/hand-walk.png`), and prints how far each fingertip is off the handle. Fix it there, at no cost.
- A thing that is already part of your own rigged model: `"hold": {"in_model": true, "words": "In the LEFT hand: a black pistol."}`.

The example above cost about $0.7 to draw (8 sheets: the walk from three sides and the run from one).

<details>
<summary><b>Other sizes: 512, 64 and 32 px from the same drawings</b></summary>

**Any size you need** (you asked): frames come out 256 px tall, and `charpipe.py pack CHAR.json --px 64` makes another set at
any height from the same drawings - larger than 256 stays sharp too, the frames are kept at the drawings' own detail - strips, shadows and `character.json` at that size, in `out-64px/`, with
nothing redrawn and `out/` left as it is (`"frame_px"` in the spec sets the default). Below, 512, 256 (the default), 64 and 32 px tall, each shown at the same size (enlarged pixel for pixel). At 64 the hair, raincoat,
boots and umbrella all read; at 32 the pose and colours hold, but the face is mostly gone - a plain resize, nothing made for that size
yet (see the [Roadmap](#roadmap)).

![the run, jump and slash at 512, 256 (default), 64 and 32 px tall, shown at the same size](docs/actions-small.gif)

</details>

### Effects on a swing: water, fire, leaves

A swing can leave something in the air. Add `"trail"` to the action - `{"name": "slash", "hold": "umbrella", "trail": "water"}` - and
you get the effect as a sprite of its own, laid over the body. **It is free and nothing is drawn again**: the 3D rig knows where the
umbrella's tip is at every moment, so the effect is worked out from that path. A slash you already have gets one without touching
its frames.

![the rain girl's umbrella slash with eight effects: plain, wind, water, fire, leaves, petals, snow, sparkle](docs/effects.gif)

- **It follows the real motion.** An image model asked for a slash invents one arc and repeats it; a stock effect is one shape pasted
  on every swing. Here the band and the pieces come off the path this character's umbrella takes in this action, seen from each
  of the 8 facings, and the body and the umbrella hide the part that passes behind them. Change the motion and the effect changes.
- **Eleven looks**: `plain`, `wind`, `water`, `fire`, `drops`, `flames`, `leaves`, `greenleaves`, `petals`, `snow`, `sparkle`. Colours,
  amounts and speeds can be changed, a new look is one more entry in a file, and you can give your own little pictures to be
  scattered (`"image": "mine.png"`).
- **Pieces fly on from frame to frame.** A leaf is let go once, is carried a little by the swing, turns, sways and settles on the
  ground - the same leaf in every frame, not a new scatter each time.
- **Water and fire move as one body** (you asked). Water comes off as a sheet, stretches into strings, breaks into drops and leaves
  mist; flame is white-yellow at its heart, orange, then a red rim that darkens as it cools, with ash drifting up.
- **Water looks like water.** Thin water is pale and see-through, deep water darker, with a bright rim and a highlight from the
  same light as the character; fast drops are drawn long along their way, and a few burst on the floor in a ring and a splash.
- **Only the swing itself.** Nothing comes off while the umbrella is being raised: the fast stretch of the motion is found by itself.
- **More frames than the body.** The body is drawn 8 times, but water has 24 effect frames (three to each) and fire 16 (two), played
  faster over them - at 8 the sheet was whole in one frame and already drops in the next. They sit around each body frame
  (a third of a frame before it, on it, a third after), so the water stays with the drawn umbrella instead of running ahead of it.
- **In pixel art too**, at the sprite's size: solid things keep hard edges, mist stays see-through.

![the same slash as 96-px pixel art, with water and with fire](docs/effects-pixel.gif)

**Honestly:** these are worked out, not painted, so they are clean rather than hand-drawn. The path
is the held thing's, so an action needs something in the hand. Made and looked at on the umbrella slash only.

### Joining two animations: into a swing and back out

A walk does not end in an attack's first pose, and an attack does not end in the walk's: played one after the other, the body jumps.
The 3D rig makes the frames between (you asked): `{"name": "ready", "between": ["walk", "slash"], "frames": 3}` and
`{"name": "recover", "between": ["slash:end", "walk"], "frames": 4}`. Below, all drawn: she walks with her umbrella, goes down into
the stance (3 frames from the rig), swings with the water effect, comes back up (4 more) and walks on.

![the rain girl walking with her umbrella, going down into a stance, swinging it with a splash of water and mist, coming back up and walking on](docs/loop-2d.gif)

- **How.** The rig plays both animations at once, each stopped at one moment, and goes from the one to the other, easing in and
  out. `"slash:end"` starts from an attack's last pose instead of its first.
- **Free to render, drawn like any action** - one sheet for three or four frames, about $0.08.
- **Look at them joined**: `charpipe.py loop hero.json --only walk,ready,slash,recover --facing south-east` (free) makes a GIF like the
  one above from the finished frames, so a frame that jumps is seen before anything is drawn again. A pixel set
  can be fixed that way too, all the frames end to end in the editor: `pixeledit.py hero.json --join walk,ready,slash,recover --facing south-east`.
- **One frame wrong? Draw it alone.** `charpipe.py frame hero.json --only slash --facing south-east --frame 5 --yes` (~$0.08) draws
  just that frame again; `"frame_words"` in the action tells the image model what that frame's render cannot. Frame 5 above had the
  left fist floating over the umbrella five times running; told the hand is mostly hidden behind her head, it came out right.
- **The thing in the hand stays in the hand.** For it to be there in the walk too, the walk carries it (here an action on the walk's
  clip with the umbrella); otherwise it would appear from nowhere in the first in-between.

### Pixel art (arcade size)

![five facings of the rain girl throwing a snowball, each ball flying its own way over an isometric floor](docs/pixel-throw.gif)

For a game drawn in pixels - a belt-scroller, a fighter, an arcade platformer - the same character as real pixel art, about 100 px
tall: one colour a pixel, a palette of about 40, a dark outline, no blur, and each frame's 3D shadow. Not a resize of the painted
frames: the order is the other way round.

![one frame four ways: the 3D render, the pixelized guide, the model's drawing, the sprite](docs/pixel-steps.png)

The 3D render is pixelized into a guide, the image model redraws it as pixel art, and the drawing is **read back on the grid the
model drew it on** - the head on grid lines of its own, so the eyes and mouth survive - then sized and placed by the render.

```
$PYTHON skills/spritecast/scripts/pixelart.py hero.json                        # the plan and its cost - spends nothing
$PYTHON skills/spritecast/scripts/pixelart.py hero.json --clips walk,throw --yes
```
About $0.075 a sheet: a walk in all eight facings is 18 sheets (about $1.35); the throw above, five facings, was 14.

- **Things held and thrown.** `"hold": {"kind": "snowball", "until": "auto"}` puts it in the hand and lets it go when the hand
  moves fastest. `pixel.json` then says which frame, where in the frame, which way and how fast - enough for your engine to spawn
  the projectile - and you get the ball, its flight shape and a 4-frame burst. The picture above is that data played back.
- **Any Mixamo animation.** `addclip.py hero.json Throw.fbx throw` carries an FBX clip onto the character's rig, free. The throw
  above came in that way.
- **It reviews itself.** Every frame is checked against its render (the pose, the held thing); `--redraw` draws the marked sheets
  again and keeps the better drawing. The throw's 40 frames all passed after one redraw.
- **Then a pixel editor for the last bit.** Pixel art is not all to be had by rule. `pixeledit.py hero.json` opens every frame in
  the browser: magic-erase a patch of left-over white, pencil, change a colour, move a selection, copy a good face into the other
  frames. Add any colour to the palette; and the frames themselves can be copied (an in-between to draw on - 8 frames made 9),
  deleted and moved: the shadow and the game's data follow. The edits are kept and laid on again by every later build.
  Animations played one after another can be opened as one, to play the whole loop and fix it where it jumps:
  `pixeledit.py hero.json --join walk,ready,slash,recover --facing south-east`.

![the pixel editor: a frame on a grid, the frame before shown faint, the tools, and how much was done by AI and by hand](docs/pixel-edit.png)

And the 3D render the frame was drawn from can be shown beside it (key `3`) or faint under it - so you can see what a doubtful
pixel is meant to be before you touch it:

![the pixel editor with a 64 px character about to throw a snowball, seen from the side, on the left and the 3D render of the same frame on the right](docs/pixel-edit-character.png)

How much is left to the hand: very little. For the 40 throw frames, about 6 minutes of AI drawing and 2 of AI cut-out; then the only
hand work was the magic eraser - a click on each speck of left-over white, in 10 of the 40 frames (131 pixels, 0.15 % of the
sprites). No face was touched: they are as the pipeline made them. The build prints those numbers every time.

**A harder set, and what the hand did.** With something held - a weapon, an umbrella - its details need a little fixing by hand:
a few pixels a frame, with an eraser and a pencil, no drawing skill. The same loop as the one under "Joining two animations", in pixel
art: she walks with her umbrella, goes down into the stance, swings, comes back up and walks on - four animations joined, 23 frames.
Only the umbrella was fixed by hand: its tip and edge made the same from frame to frame. The character was not; a few left-over white
specks were erased, nothing more. In all 1,196 pixels of 51,442 (2.3 %), by someone who does not draw, in a few minutes. What made it quick, and what matters most in pixel art: looking at all 23 frames in a row, playing, not one at a time - a fix is
making sure no part's pixels change a lot from one frame to the next. Not fixed: in two walk frames
the umbrella is drawn a little off the 3D one's angle and length.


- **The editor shows where the 3D has things** (key `4`): the held thing in red and the body's outline in blue, over the frame you
  are drawing - so an umbrella drawn too long or at the wrong angle is seen at once.

![the pixel editor with the 3D umbrella laid in red and the 3D body's outline in blue over a walk frame: the drawn umbrella lies on the red one](docs/pixel-edit-shapes.png)

**How many colours.** A set comes out with about 40 colours. `--colours 16` gives it 16 at most (8 is the least), and
`--palette` gives every pixel its nearest colour in a set palette: one of the 15 that come with the skill, by name
(`--palette pico8`; `--palette list` shows them), or your own file in what Aseprite reads - `.png` `.gif` `.bmp` `.pcx`, `.hex`
(Lospec), `.gpl`, `.pal`, `.act`, `.col`, `.aseprite`. Both are free: nothing is drawn again, the same drawings are read with
another palette. Props take the same two options. Down to 16 the character holds up well; at 8 close colours merge (her navy legs
go black), and a palette with nothing near one of her colours will change that colour - look at the result before you keep it.

![the same three sprites with the default 43 colours, with --colours 32, 16 and 8, and in the 16-colour PICO-8 palette](docs/pixel-colours.png)

The palettes that come with it, on the same two sprites - a yellow coat needs a yellow in the palette (`c64`, `gameboy`,
`slso8` and `sweetie16` have none):

![the rain girl and the ramen cart in each of the 16 palettes: aap64, apollo, c64, cga, db16, db32, endesga32, endesga64, gameboy, nes, pico8, resurrect64, slso8, sweetie16, wada094, zx](docs/pixel-palettes.png)

*The palettes are their authors': AAP-64 by Adigun A. Polack, Apollo by AdamCYounis, DawnBringer 16/32 by DawnBringer, Endesga 32/64
by ENDESGA, Resurrect 64 by Kerrie Lake, SLSO8 by Luis Miguel Maldonado, Sweetie 16 by GrafxKid, Wada Plate 094 by Sanzo Wada
(1930s colour research, via TKC's design system) - taken from [Lospec](https://lospec.com/palette-list).*

**Sizes.** 96 px is the size for a character of ordinary proportions. **64 px works for a character designed small** - about three
heads tall, with its own 3D model - and comes out about 70 px. Under that, the image model is never asked: it does not keep to so
few squares (32 px was tried four ways). `--px 32` draws at 64 and makes the 32 set from it, free - the same motion and frames, with
rougher faces. 64 is the one that comes out well.

![the small character walking and throwing in eight facings at 64 px, and the 32-px set made from it](docs/pixel-small.gif)

Both sets are in [`examples/rain_chibi`](examples/rain_chibi): the three-heads design drawn from the rain girl, its turnaround, the
spec, `pixel64/` (walk and throw in eight facings, 128 frames, each with its shadow; no pixel was touched by hand) and `pixel32/` made from it. Her throw is a Mixamo clip put on with `addclip.py --clear-head 55`; the clip and the
rig are not in the repo.

![the same small character five ways: drawn at 64 px, a 32-px set made from it, and three ways of asking the image model for 32 px](docs/pixel-sizes.png)

**Why not ask for 32 px?** The image model (GPT) does not do small pixel art well under 64. It draws its "pixels" at a size of its
own - asked for 8-px squares it drew anything from 7.4 to 10.8 - and at 32 squares one square off is an eye gone. Above: the top row
is what it draws at 64; the three red rows are 32 px asked for directly, each a different sheet layout, all of the same walk. So the
skill asks for 64 and makes 32 from that (the green row). The details: [reference/pixel.md](skills/spritecast/reference/pixel.md).

The sprites above are in [`examples/rain_girl/pixel`](examples/rain_girl/pixel): the throw in five facings, a walk in two and the
umbrella slash as strips, their shadows, the snowball with its flight shape and burst, and `pixel.json` with the release data.

### Pixel-art props: any object, any side

![a ramen street cart as a 3D model from four sides, and the same four sides as pixel-art sprites](docs/pixel-props.png)

The same way round as a character, for a thing: its 3D guide is pixelized, the image model redraws it as pixel art on the same grid,
and the drawing is read back on that grid and brought to the guide's size. The angle is the camera's, so a thing turned four ways is
four sprites of ONE thing - the same roof, the same wheels, each side with what belongs on it.

```
$PYTHON skills/spritecast/scripts/isoprop.py model cart.json --yes    # Tripo makes the 3D model from the description (~20 credits)
$PYTHON skills/spritecast/scripts/isoprop.py render cart.json         # free: the guide from each side ("views": [0, 90, 180, 270])
$PYTHON skills/spritecast/scripts/proppixel.py cart.json --yes        # ~$0.08 a side → out-pixel/sprite-<side>.png
```

- **A real 3D model is what makes the sides come out right.** From blocks alone the image model cannot tell which face has what on it:
  an arcade cabinet came out with its screen on the wrong face in one view of four. The cart above is a Tripo model; all four sides
  matched it on the first drawing. One view of a simple thing (a chair, a crate) is fine from blocks.
- **The same scale as the character.** `--ppm` is pixels per metre: the pixel character's height in pixels over its height in metres
  (54 for the small example character), so the prop and the character stand on one floor in the same size of pixel.
- **The cut-out is yours to finish.** The air under a roof and between spokes is cleared by the AI cut-out; what it leaves, open in the
  same pixel editor as the characters (`pixeledit.py cart.json`): the four sides are four frames, the 3D render can be shown beside
  or under the sprite, and what you erase is kept. The cart above had 122 pixels finished that way.
- The cart is in [`examples/ramen_cart`](examples/ramen_cart): the spec, the Tripo model, the four guides
  and the four sprites.

<a name="light-shadow-wind"></a>
### Light, shadow and wind from the 3D model

The model that gave a prop its sides also knows where its light is blocked and where its boughs are. So its shadow, a lamp's light
on the floor and the wind in its leaves are worked out from it - free, on your computer, with no drawing.

- **Its shadow, baked from its 3D model** (free, a few seconds, done by itself): the sun's light and the sky's on the ground, each
  as much as the thing leaves open - so it is deep close by (under the cart, round a trunk's foot) and paler where it falls
  from high up (a crown's, the light coming through between its leaves), in five steps of pixel art. The sun is the guide's own light, so the shade drawn on the prop and the shadow
  on the ground agree. `--shadow overcast` (or `"shadow": "overcast"` in the spec) for a grey day: no sun, only the soft dark round it.
  `out-pixel/shadow-<side>.png` and where it sits in `pixel.json`; draw it under the sprite.

![the ramen cart from four sides, each with its shadow baked from the 3D model; below, a tree's shadow in sun (dark by the trunk, soft under the crown) and on a grey day (only soft, close round it)](docs/prop-shadows.png)

- **Indoors, a lamp where you put it.** `--lamp -1,2.4,-0.2 --lamp-size 0.03` (metres from the prop's foot: right, up, towards the
  viewer; the lamp's own size) - the shadow falls away from it, longer the lower it hangs, sharp from a bare bulb and soft from a big
  shade, and fades as its light does across the floor. Its light on the floor comes too - `light-<side>.png`, brightest under it, the
  thing's shadow cut out, dithered in steps - to lay on the floor with ADD - and the lamp itself as pixel art (`lamp.png`) with where it is in each side's
  pixels in `pixel.json`, so a game draws the floor, its light, the shadow, the prop and the lamp right where the editor showed them. Leave it out and the sun is used. **See-through parts** (a wicker weave, leaves,
  a net) are painted on a model, not cut: `"see_through": [{"colour": "#c8955a", "open": 0.35}]` lets the parts of that colour pass
  that share of the light. A rattan peacock chair ([`examples/rattan_peacock_chair`](examples/rattan_peacock_chair)) under six lights:

![a rattan peacock chair as pixel art under the sun, on a grey day, under a bare bulb, a lamp in front and behind it, and a big light above, on an oak floor lit by each - each shadow baked from its 3D model, the weave letting light through](docs/indoor-shadows.png)

- **Move the light yourself**: `lightedit.py PROP.json` opens a page on your computer: drag the lamp across the floor, lift it with
  the wheel, size it - the shadow and the lamp's light on the floor are redrawn as you go; Save bakes every side with it and keeps it in the spec.
  **Your own lamp**: load a picture of it (a cut-out PNG at the prop's scale), click where its light comes from - it stands where you
  drag it, in front of or behind the prop as it should, and its light comes from there. The shadow, the glow and the floor's light come
  as pixel art (steps, dithered) or smooth (gradients, for a game in another style: `"light_style": "smooth"`). Below: a pixel floor lamp (`examples/lamps/floor_lamp/out-pixel/sprite.png`) in front, behind, and smooth.

![the light editor at work: a pixel floor lamp dragged all the way round a rattan chair on a tiled floor - the chair's shadow swinging round to the side away from the lamp, longer and shorter, the lamp's light on the floor going with it, the lamp passing behind the chair and in front of it](docs/light-editor.gif)

![a pixel-art floor lamp moved round the rattan chair in the light editor: in front of it on the right (the shadow falls back left), behind it on the left (the shadow falls forward right), and with the smooth look](docs/own-lamp.png)

- **The wind in it, from its 3D model** (`"sway": "leaves"` in the spec, or `propshade.py PROP.json --sway leaves`; free): a crown is
  boughs, not one sheet. Each leaf pixel takes the model's point it shows, the points are grouped by where they are in 3D - the near
  boughs apart from those behind them - and every clump moves whole, a pixel at a time, far ones laid first; the trunk stands. No
  warping, no hand-drawn frames. You get `sway-<side>.png` (12 frames x still air / breeze / gust - play a row as a loop),
  `clumps-<side>.png` with each clump's place in 3D to move them yourself, and `preview-sway.gif`. The tree is in
  [`examples/forest_tree`](examples/forest_tree); its leaves also let light through its shadow.

![a pixel-art tree from two sides swaying in the wind - clumps of leaves moving a pixel at a time, the trunk still, a gust leaning the top - and the same clumps in colours, cut from its 3D model](docs/sway.gif)

- **Where it is in the way, from the same model** (free, baked with the shadow): `solid-<side>.png` is where a walker cannot stand -
  the prop's footprint, cut from the model near the ground (a trunk's foot, a table by its four legs) - and `"collide": {"cover": [0.55]}`
  adds what stops a thing flying at that height: a trunk stops a fireball, the crown above it does not. Each comes with its place and
  an outline for a collision polygon. And **a character darkens in its shade**: every shadow says how to read it for a point above the
  ground, so her feet, middle and head each take what stands between them and the sun.
- **Into your engine**: `export.py PROP/out-pixel` writes a Phaser 3 module and a Godot 4 scene - the shadow, a lamp's light, the wind,
  the footprint as a collision polygon, and `shade()` / `cover()` to ask (opened and checked in Phaser 3.90 and Godot 4.7; Unity and
  Aseprite are for characters only so far). A small thing sways too: mushrooms nod at the cap (`"sway": "caps"`,
  [`examples/forest_mushrooms`](examples/forest_mushrooms)).

![two pixel-art trees and three patches of mushrooms exported to Phaser, on grass: their baked shadows, the crowns swaying as a gust passes, the rain girl walking through and darkening in a tree's shade, balls flying knee-high - one stopped by a trunk, one passing under the crown - and at the end what the model says is in the way: red where a walker cannot stand, blue what stops a thing in the air](docs/prop-scene.gif)

### Skipping the drawing: the 3D renders as the frames

With `"draw": false` in the spec, no image model draws the frames: the 3D model's own renders (toon-shaded, its own texture) are
the frames, with the same 3D shadows and anchors. The image model draws only the turnaround (~$0.09); with your own rigged GLB
(`"rig_glb"`; an animal: its model, `"model_glb"`) it draws nothing at all. A character then costs the turnaround and the 3D
(75 Tripo credits, an animal 30) - two OKs, done as soon as `3d` is. The trade-off is sharpness: no drawn lines, a simpler face,
the model's texture as it came (blurrier fur and folds).

![the same girl and cat walking: the 3D renders alone against the drawn frames](docs/render-vs-drawn.gif)

![close-up at the strips' own pixels: 3D only against drawn](docs/render-vs-drawn-zoom.png)

## Sitting

![The rain girl seated in 8 facings, and in the example armchair under its front piece](docs/sitting.png)

Once a character walks, ask Claude to *"make her sit"*. Her 3D model is bent into sitting (thighs level, knees bent, hands on the
thighs) in 8 facings for free; you look at those renders, then they are drawn like the standing views (two sheets, about $0.22). She
sits on nothing - your game's chair goes under her. `character.json` gets a `sit` block: for each facing the file, the **seat point**
(put it on the chair's seat; a fraction of the frame, like `anchor`), the seat's height and the shadow. To put her on one of
your props, `seat.py` places her on its seat and works out the prop's **front piece for her** (an armrest, a pew's back, a bench's
backrest) from both of their 3D heights - no painting:

![The rain girl seated on ten seats: an armchair from four sides, the Tripo armchair, a dining chair from both sides, a pew, a curved bench from both sides](docs/seats.png)

It finds the seat's height and which way it faces, and sits her back until her knees reach the seat's edge. If she sits a little off,
drag her on the touch-up page (below): letting go works the front piece out again from there.
The details: [reference/sitting.md](skills/spritecast/reference/sitting.md).

```
$PYTHON skills/spritecast/scripts/charpipe.py sit <name>.json            # free: the seated renders
$PYTHON skills/spritecast/scripts/charpipe.py sit <name>.json --draw     # ~$0.22: drawn and finished
$PYTHON skills/spritecast/scripts/seat.py <prop>.json <name>.json --height 1.3   # free: on a prop, its front piece worked out
```

## Fixing things by hand

![Three seats: the front piece worked out automatically beside the same seat painted and moved by hand](docs/touchup.png)

The automatic steps get you most of the way; the last bit is best done by eye. **Painting by hand is more accurate than any of the
automatic steps**: above, the pew's back hid the whole girl until it was painted and she was moved up, and the dining chair's and the
armchair's backs cut her in the wrong places. Cut-outs are not perfect either: a little paper left between an arm and the body, a white
shirt the cut-out took for the paper. Ask Claude to
open the touch-up page (or run `$PYTHON skills/spritecast/scripts/touchup.py <spec>.json`): every finished picture of that prop or
character, painted in the browser and saved as you go.

| colour | does |
|---|---|
| red | clears: made see-through |
| green | brings back: those pixels taken from the drawing itself (turn on "drawing under" to see it) |
| blue (props) | the **front piece**: what stands in front of a character inside the thing - an arch's near posts, a gazebo's roof, a chair's near armrest |
| ⬠ polygon (P) | click the corners and close it (double-click, Enter, or the first corner): filled in the colour you are painting, or erased |
| 🪑 (a seat) | drag the seated character (or the arrow keys); letting go re-makes the seat and its front piece from there |

Then `touchup.py <spec>.json --apply` (a character's strips are packed again). A prop with a front piece gets `sprite-front.png` and
`"front"` in `sprite.json`: draw the sprite behind whoever stands in it and the front piece over them. `finish` lays the paintings on
again by itself; a picture drawn again since it was painted keeps its painting aside instead of laying it on a different drawing.

**Pixel sprites** have an editor of their own, pixel by pixel - see [Pixel art](#pixel-art-arcade-size).

## Props and scenery

![guide → sprite](docs/showcase.png)

Ask an image model for "an isometric armchair" and you get a nice picture at a slightly wrong angle. Ask again and you get a
different wrong angle and a different size. Put ten of them on one floor and nothing lines up.

SpriteCast gives the model a guide that is hard to misread (and when it does misread, you're told):
1. Claude builds the object from simple blocks at its **real size in metres**.
2. The blocks are rendered with your game's **exact camera**.
3. The image model only redraws that guide in your **art style**.
4. The drawing is cut out and **fitted to the guide's box**, so its size and footprint are the guide's; a drawing whose outline
   doesn't follow the guide is flagged, not forced. It also gets a baked shadow and an anchor point for your engine.

The props come out painted (the `cozy` look: smooth shading, fine outlines), or in the style of one picture of your own.

## How a session goes

![how a session goes](docs/session.png)

You describe the prop. Claude asks only for what's missing: the size, the facing, your game's view, your style. It renders the
guide for free and shows it to you. It tells you the cost and waits for your OK. Then you get `sprite.png`, `shadow.png` and
`sprite.json`.

## Examples

All in [`examples/`](examples), each with its spec and the files it produced (the raw drawings as WebP, to keep the repo small).

| | | |
|---|---|---|
| ![](examples/reading_armchair/preview.png) | ![](examples/potted_monstera/preview.png) | ![](examples/arcade_cabinet/preview.png) |
| `reading_armchair`: 9 blocks: seat, back, arms, legs | `potted_monstera`: a pot, and the plant given as one volume | `arcade_cabinet`: its front faces down-left |

![four facings and a top-down view](docs/views.png)
`armchair_four_ways`: `views: [0, 90, 180, 270]`. The later views are drawn with the first one as a reference, so it stays the same
chair. `arcade_cabinet_topdown`: `camera: "topdown"`. `reading_armchair_tripo`: the same armchair from a Tripo model (below).

The examples' 3D models (`reading_armchair_tripo`, and the walking characters' meshes and rigs) were generated with the [Tripo](https://www.tripo3d.ai) API.

## More detail: a 3D model first (Tripo)

![blocks vs a Tripo model as the guide](docs/tripo.png)

Blocks are enough when what matters is where things stand and how big they are. For more detail (curved arms, tapered legs, buttons,
carving), let [Tripo](https://www.tripo3d.ai) make a real 3D model from the description first. It is made as tall as the blocks say and
keeps its own proportions (the footprint it then covers is written to `sprite.json`; `"shape": "box"` presses it into the blocks' box
instead), and it becomes the guide. The image model then draws over a real shape, and the 3D
shadow is the model's own.

```
$PYTHON skills/spritecast/scripts/isoprop.py model  armchair.json --yes   # Tripo text-to-model (~20-40 Tripo credits, ~2 min); the spec now uses it
$PYTHON skills/spritecast/scripts/isoprop.py yaws   armchair.json         # free: the model turned four ways; set "model": {"yaw": ...} to the right one
$PYTHON skills/spritecast/scripts/isoprop.py render armchair.json         # then draw, finish as usual
```
Needs `TRIPO_API_KEY`. The blocks stay in the spec as `blocks_draft`.

## Posed characters (from a description)

![a mannequin guide and two characters in four facings](docs/characters.png)

An NPC that only stands needs no illustration and no rig: it works like a prop. Claude poses a plain mannequin at the person's real height and renders it in each facing (4 or
8). The image model dresses it as you describe. The first facing is drawn first and the others follow it, so it stays the same person.

```json
{ "name": "barista",
  "character": { "height": 1.63, "build": "slim", "directions": ["south-east", "south-west", "north-east", "north-west"] },
  "description": "a cheerful young café barista: a short dark-brown bob, a cream cable-knit sweater under a forest-green apron, ..." }
```

The anchor is between the feet. About $0.07 for the first facing and $0.08 for each of the others.

<details>
<summary><b>Poses, your own angles, and redrawing one facing</b></summary>

**Poses.** The mannequin has joints. `"pose"` is one of `stand` (default), `wave`, `point`, `hold` (hands together in front: a cup,
a tray, a book), `arms-crossed` or `walk` (mid-stride). Describe what goes with it ("waving hello", "holding a coffee cup"). Or give the angles yourself, and Claude can adjust them
for you ("raise the arm higher") and check them in the free render:

```json
"pose": { "base": "stand", "arm": { "left": [[150, 10], [170, 10]], "right": [[150, 10], [170, 10]] } }
```
Each limb is two parts, upper and lower (`[out, forward]` degrees each): turned out to its side, then swung forward. `left` and
`right` are the figure's own.

![four poses](docs/poses.png)

**Single pictures.** These posed figures are one picture per facing; for a walk, see [Walking characters](#walking-characters).
Look at every facing yourself (the outline check can't see a head turned the wrong way); redraw one with
`draw <spec> --yes --again --only north-west`.

</details>

## Shadows that match the drawing

The 3D guide's shadow is right for solid things like furniture. But a drawing has things the blocks don't: hair, a coat's hood,
leaves spilling out of a pot.

<details>
<summary><b>How the shadow is worked out</b></summary>

So SpriteCast also renders a **height map** of the guide: how high above the floor every pixel is. A point h metres up casts its
shadow a fixed step away on screen (h times the light's offset), whatever its depth. So each pixel of the drawing takes the height of
the guide under it, or of the nearest guide pixel for hair or leaves past the guide, and is moved by that step.

The shape is the drawing's. Where it starts is the 3D model's: each foot starts its own shadow, and a pot's shadow starts at its
base. Only what touches the floor has to be exact. Higher up (from 10 % to 35 % of the object's height) the height eases into a
smooth one read off the screen, so hair, hats and leaves cast a natural shadow instead of the mannequin's corners. Where it stands
(the blocks up to 12 cm: shoes, a pot's base) the guide's own 3D shadow is added, so the shadow meets the object as a real one
would: on the side away from the light, never in front of it. Posed figures and `loose` things get it; solid props keep the 3D
shadow, and walking characters cast their 3D body's own (above). Choose with `"shadow": "drawn" | "guide"`.

</details>

![shadows from the blocks and from the drawing](docs/shadows.png)

**A walking character's shadow is light as it falls** (since 0.20): the posed 3D body is pressed onto the ground along 16 directions across the sun's disc and 48
across the sky, and what each hides is added up - the same sum as [a prop's baked shadow](#light-shadow-wind). So it is deep where
the feet stand and under the body and pale at its far edge, and it changes with every frame's pose. The strips are shown at
character.json's `shadow_alpha` (0.56); pixel sets get the shadow in five steps. `"shadow": "flat"` in the spec keeps the one hard shape of before.

![the rain girl walking, running and jumping over her shadow - left, as it was: one hard shape at one strength; right, as light falls: deep under the feet, soft and pale at its edge](docs/character-shadow.png)

## Cameras

| `camera` | looks down | for |
|---|---|---|
| `"iso-2:1"` (default) | 30°, turned 45° | most isometric games; floor tiles twice as wide as tall |
| `"isometric"` | 35.26°, turned 45° | true isometric (120° between the axes) |
| `"topdown"` | 50°, square on | 3/4 top-down RPGs |
| `"front"` | 12°, square on | side-scrollers |
| `{"pitch": 40, "yaw": 30}` | anything | your own angle |

`"light": "left"` mirrors the light and the shadow.

Walking characters take `"pitch"` alone, not `camera`: 30 (default, 2:1), 35.26 (true isometric), 50 (3/4 top-down), 12 (front);
their 8 facings are 45° apart. `camera` covers props and posed figures.

## Putting it in your engine

**Ready-made files for Godot, Unity, Phaser and Aseprite.** `export.py <name>/out` (free) writes `out/export/`:

| | what you get | how you use it |
|---|---|---|
| `godot/` | a scene with Shadow, Body and Effect, and a small script | drop the folder into a Godot 4 project; `play("walk", "south-east")` |
| `unity/` | the strips and an editor script | copy into `Assets/`; a prefab and a clip per animation build themselves; `GetComponent<Animator>().Play("walk_south_east")` |
| `phaser/` | an ES module for Phaser 3 | `preload(this, base)`, `create(this)`, `add(this, x, y).play('walk', 'south-east')` |
| `aseprite/` | one `.aseprite` per action | a tag per facing, layers `shadow`, `body`, `effect`, a slice marking the feet |

The character stands where you put it (the point between the feet), the shadow keeps step with the body, and a swing's effect
plays over it. Each was opened to check: Godot 4.7, Unity 6000.3, Phaser 3.90 and Aseprite. Pixel sets are not exported yet.

To do it yourself, the numbers are all in the JSON:

`sprite.json` tells you where the prop touches the ground:

```json
"sprite": { "file": "sprite.png", "size": [299, 357], "anchor": [0.4993, 0.9966], "anchor_px": [149.3, 355.8] },
"shadow": { "file": "shadow.png", "offset_px": [-66, 116] },
"px_per_m": 256
```

- **anchor**: the footprint's front corner on the ground (the middle of its front edge in the square-on views). Put that point on
  the tile where the prop stands.
- **shadow**: draw `shadow.png` at `offset_px` from the sprite's top-left corner, at about 30 % opacity, under all sprites.
- **scale**: everything is drawn at `px_per_m` pixels per metre. For a 2:1 map whose tiles are 1 m and `T` px wide, scale by
  `T / 1.414 / px_per_m`.

| engine | how |
|---|---|
| Phaser | `this.add.image(x, y, 'armchair').setOrigin(anchor[0], anchor[1])` |
| Godot 4 | `Sprite2D`: `centered = false`, `offset = -anchor_px` |
| Unity | Sprite Editor → Pivot: Custom, `(anchor[0], 1 - anchor[1])` |

**Walking characters.** `character.json` gives `frame` (`[w, h]` in px), `anchor` (between the feet, as a fraction of the frame)
and `fps`. Each `walk-<facing>.png` is a strip of 8 frames side by side, and each `idle-<facing>.png` one frame. Shadow `i` of a
facing, `shadows.walk[facing][i]`, is drawn at its `offset` from frame `i`'s top-left corner, under everything, at `shadow_alpha` (0.56: the shadow's darkness is in its own alpha - deep under the feet, pale at its far edge; 0.3 for a set made with `"shadow": "flat"`).
There is no `px_per_m`: scale the frames to the height you want your character to stand. In Phaser, with `rain_girl`'s numbers:

```js
this.load.spritesheet('girl-se', 'walk-south-east.png', { frameWidth: 165, frameHeight: 256 });
this.anims.create({ key: 'walk-se', frames: this.anims.generateFrameNumbers('girl-se'), frameRate: 6.76, repeat: -1 });
this.add.sprite(x, y, 'girl-se').setOrigin(0.4926, 0.8839).play('walk-se');
```
The full format: [reference/character.md](skills/spritecast/reference/character.md#output-nameout).

## Install

In a terminal:
```
claude plugin marketplace add Sunghwan0112/spritecast
claude plugin install spritecast@spritecast
```
or inside Claude Code: `/plugin marketplace add Sunghwan0112/spritecast`, then `/plugin install spritecast@spritecast`.

**You also need** only Python 3.9+ and a browser (Chrome, or Edge - every Windows has it). The first time, Claude runs the setup
check (`doctor.py --fix`): it makes its own venv in `~/.cache/spritecast/` with the few packages (about 10 s), leaves your Python
alone, and tells you what each thing is for. Nothing to install by hand.

<details>
<summary><b>Running the scripts yourself</b></summary>

**Running the scripts yourself.** Claude runs them for you. To run them by hand from a clone of this repo, use the Python that
`doctor.py` prints on its last line (`PYTHON=...`); after `--fix` it is `~/.cache/spritecast/venv/bin/python` (Windows:
`%USERPROFILE%\.cache\spritecast\venv\Scripts\python.exe`). A plain `python` may not have the packages (`No module named ...`). The commands below
write it as `$PYTHON`:
```bash
python3 skills/spritecast/scripts/doctor.py --fix
PYTHON=$(python3 skills/spritecast/scripts/doctor.py | sed -n 's/^PYTHON=//p')
$PYTHON skills/spritecast/scripts/isoprop.py --help
```
On Windows, in PowerShell:
```powershell
python skills/spritecast/scripts/doctor.py --fix
$PYTHON = "$env:USERPROFILE\.cache\spritecast\venv\Scripts\python.exe"
& $PYTHON skills/spritecast/scripts/isoprop.py --help
```
There, run the `$PYTHON ...` commands below as `& $PYTHON ...`.

</details>

| what | for | needed? |
|---|---|---|
| Python 3.9+ | runs the scripts | yes |
| numpy, pillow, scipy | cutting out, fitting, shadows | yes (set up for you) |
| playwright + Chrome or Edge | renders the 3D guide on your computer (free) | yes (set up for you; a browser you have is used) |
| onnxruntime + a 224 MB model | characters only: the AI cut-out that keeps white shoes on white paper | characters (fetched once, by itself) |
| `OPENAI_API_KEY` | drawing, about $0.07 a prop | to draw |
| `TRIPO_API_KEY` | characters: the 3D model, its rig and walk | for walking characters |

**Try it first, free, no key:** ask Claude to *"try SpriteCast"*. It renders one of the examples' guides on your computer and
finishes it with the drawing that came with the example (`isoprop.py try`), so you see the whole way before paying for anything.

<details>
<summary><b>Keys: where they go, and OpenAI's verification</b></summary>

Keys: **in the plugin's settings.** When you enable SpriteCast, Claude Code asks for them (`/plugin` → SpriteCast → configure,
to change them later): the OpenAI key, and the Tripo key if you make walking characters. They are kept in your system's credential
store, masked, and handed to SpriteCast's scripts when a session starts (restart Claude Code after changing one). A key already in your
environment still works when the settings have none:

```bash
export OPENAI_API_KEY=sk-...          # macOS / Linux (add it to ~/.zshrc or ~/.bashrc to keep it)
```
```powershell
setx OPENAI_API_KEY "sk-..."          # Windows (then open a new terminal)
```
On Windows the settings reach the scripts only when Claude Code runs its commands in Git Bash (its default when Git is installed); in
PowerShell use the environment. Your key stays on your computer. It is only sent to OpenAI, and you pay OpenAI for each drawing (about $0.07).

OpenAI may ask you to verify your organisation before a key can use image models (platform.openai.com → Settings →
Organization): do it once before your first drawing. Set the key before you start Claude Code; a key set while it runs is seen
only after a restart. Walking characters also need `TRIPO_API_KEY`, from Tripo's API platform, where API credits are bought
(75 a character, 30 an animal).

</details>

## How it works

| step | what | cost |
|---|---|---|
| spec | Claude writes `<name>.json`: footprint, blocks in metres, a description of the finished object | free |
| `render` | three.js in headless Chrome: the guide, its shadow and the model's input | free |
| `draw` | OpenAI Images (`gpt-image-2.5-sunburst` by default): the guide redrawn in your style | ~$0.07 |
| `finish` | magenta keyed out softly, fitted back onto the guide's box, shadow baked, anchor measured | free |
| `preview` | the sprite on a 1 m floor grid | free |

You can run the steps yourself too:
`$PYTHON skills/spritecast/scripts/isoprop.py render|draw|finish|preview examples/reading_armchair.json` (`$PYTHON`: see
[Install](#install)). `draw` only prints the cost
until you add `--yes`. The spec format is in [reference/spec.md](skills/spritecast/reference/spec.md). Tips for good guides are in
[reference/tips.md](skills/spritecast/reference/tips.md).

## If something goes wrong

| problem | fix |
|---|---|
| `No module named ...` | run the script with the `PYTHON=` that `python3 skills/spritecast/scripts/doctor.py` prints (`--fix` first if it says not ready; Claude does this for you) |
| no browser | install Chrome, or `doctor.py --fix --browser` (Playwright's Chromium, ~150 MB) |
| `this Python cannot make a venv` | Debian/Ubuntu: `sudo apt install python3-venv`, or use another Python (python.org, conda) |
| `draw: set OPENAI_API_KEY` | give the key in the plugin's settings (`/plugin` → SpriteCast), or set it in the environment (above), and restart Claude Code |
| `HTTP 401` / `403` | the key is wrong, or OpenAI wants your organisation verified before it allows image models (platform.openai.com → Settings → Organization) |
| `finish: WARNING - the drawing does not follow the guide` | the model drew another angle or shape: make the description say what is seen from this camera, check the guide, draw again with `--again`. For plants and other loose shapes that may spill past their guide, set `"loose": true` |
| the drawing added things | say what must NOT be there in the description ("no rug, no logos"), then draw again |
| the shape is off | fix the blocks: the drawing follows the guide |

## What it sends and fetches

<details>
<summary><b>What is sent where, and what is downloaded</b></summary>

Everything runs on your computer except the steps below. Each paid step prints its cost and waits for your OK first.

| when | sent to | what |
|---|---|---|
| `draw` | OpenAI (`api.openai.com`) | the guide picture, your style picture and the text description, with your `OPENAI_API_KEY` |
| characters: `turnaround`, `draw` | OpenAI | the illustration, the turnaround and the 3D renders, with the same key |
| characters: `3d` | Tripo (`openapi.tripo3d.ai`) | the four turnaround views, with your `TRIPO_API_KEY`; the model, its rig and walk come back |
| `model` (props, optional) | Tripo | the text description |
| characters, `"modeler": "meshy"` (optional) | Meshy (`api.meshy.ai`) | the four views, with your `MESHY_API_KEY` |

The keys are read from your environment only, sent only to their own service, and never written to a file or printed. What is downloaded:

| what | from | when |
|---|---|---|
| numpy, pillow, scipy, playwright, onnxruntime | PyPI, into its own venv (`~/.cache/spritecast/venv`) | `doctor.py --fix`, once |
| Chromium (~150 MB) | Playwright's servers | only if there is no Chrome or Edge, and only after you say yes |
| the cut-out model, BiRefNet lite (224 MB, MIT), or the full one (973 MB) with `SPRITECAST_KEY_MODEL=general` | [rembg's GitHub release](https://github.com/danielgatis/rembg/releases/tag/v0.0.0), its md5 checked | characters, the first `finish` |
| MediaPipe Face Landmarker (3.7 MB, Apache-2.0); `mediapipe` itself is a separate `pip install` | Google (`storage.googleapis.com/mediapipe-models`) | only `facecheck` (optional), the first time |

The renders run in a headless browser on your computer with nothing loaded from the internet: three.js is bundled
(`skills/spritecast/scripts/vendor/three/`, MIT).

</details>

## Roadmap

What is planned next, roughly in this order (no dates - it moves with feedback):
- **Seat-fitted poses, and riding** (sitting itself is done - see Sitting): a pose shaped to each seat (leaning back on a deep sofa, feet
  on a ride's footrest) instead of one seated pose for every chair, and characters riding in carts and vehicles.
- **Turning objects**: a vehicle or a ride rotated through many angles, so it turns smoothly instead of snapping between 8 facings.
- **Night versions**: a mask of what gives light (windows, bulbs, neon), so your engine can light just those parts after dark.
- **Walk-through props, automatic**: the front piece worked out from the 3D guide (today it is painted by hand on the touch-up page).
- **More actions and things to hold**: run, jump and slash are in, and any Mixamo clip can be added (a throw, with a snowball that is let go); next, more held things (a sword, a staff) and an idle breath.
- **Small sprites**: pixel art at 96 px, and at 64 px for a character designed small, is in (see Pixel art); a 32-px set is made from
  the 64 one. Next: making the small design from the ordinary one in one step, and a face at 32 px that needs no hand.
- **Engine exports**: Godot, Unity, Phaser and Aseprite files are in (see Putting it in your engine). Next: pixel sets.
- **Effects**: a swing's water, fire, leaves and more are in (see Effects on a swing). Next: effects with no held thing (a kick, a
  footstep's splash), and painted pieces.

See [CHANGELOG.md](CHANGELOG.md) for what each version changed.

## Feedback

Feedback decides what comes next, and what changed because of it is marked in the changelog.
- **Something broke**: open an [issue](https://github.com/Sunghwan0112/spritecast/issues/new/choose) with the bug form - your OS, Python version,
  the command and the message help most.
- **An idea or a missing feature**: the feature form in [issues](https://github.com/Sunghwan0112/spritecast/issues/new/choose).
- **Show what you made, or ask how**: [Discussions](https://github.com/Sunghwan0112/spritecast/discussions).

## Notes
- The output is yours.
- Leave real brands, logos and characters from existing games out of descriptions.
- Don't use a living artist's work as your style picture without their permission.
- A `photo` for a character's likeness: only of someone who agreed to it.
- Solid props get the 3D shadow of their blocks; posed figures and `loose` things a shadow in the drawing's own shape (see Shadows);
  walking characters their 3D body's.
- Settings: `SPRITECAST_MODEL` (e.g. `gpt-image-2.6-sunburst` to try the newer model; the default is what the checks were tuned on) and `SPRITECAST_QUALITY` (`low` | `medium` | `high`).

## FAQ
- **What does it cost?** The guides, finishing and the `try` are free. About $0.07 a prop, $0.08 for each further facing; a walking
  character about $2.2 of drawing (~$1.5 with `"mirror": true`) and 75 Tripo credits (an animal 30). Each paid step shows its cost
  and waits for your OK. The plugin is free; you pay OpenAI and Tripo directly, nothing goes to the author.
- **Which keys do I need?** `OPENAI_API_KEY` to draw, `TRIPO_API_KEY` for walking characters and animals (Meshy optional). OpenAI may
  ask you to verify your organisation first. See [Keys](#install).
- **Isn't this AI art?** Yes: an image model does the painting. What SpriteCast adds is the geometry: the size, the camera angle, the
  walk and the shadows come from 3D. You can give your own art as the style, or set `"draw": false` so no image model draws a walking
  character's frames: the 3D renders are the frames. The turnaround is still drawn, unless you bring your own rigged model
  ([Skipping the drawing](#skipping-the-drawing-the-3d-renders-as-the-frames)).
- **What doesn't it do?** Walking characters start from an illustration facing front, standing straight. Pixel art works at 96 px, and at 64 px for a character
  designed small; a 32-px set is made from the 64 one, with rougher faces
  ([Roadmap](#roadmap)). Posed single pictures (wave, point, hold...) need only a description. Big flat things like rugs are better drawn top-down and skewed onto the floor
  ([tips](skills/spritecast/reference/tips.md)). Look at the results yourself: the outline check can't see a head turned the wrong way.
- **Which engine?** Any that takes PNGs: you get the sprite, its shadow and the anchor in JSON. See
  [Putting it in your engine](#putting-it-in-your-engine) for Phaser, Godot and Unity.

## License
MIT - the code and the examples (pictures, strips and the rain girl's rigged model alike). three.js (bundled in `skills/spritecast/scripts/vendor/three`) is MIT, © three.js authors.
