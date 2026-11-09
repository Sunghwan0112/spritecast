# Touching up by hand (`touchup.py`)

`touchup.py SPEC.json [--port 8765] [--out DIR]` (free) serves a local page with every finished picture of that prop or character - a
character's walk, standing and seated frames, a prop's sprite (each view), and a prop's seats from `seat.py`. **It is a server: run
it in the background** (it prints its address and keeps running), give the user the address, and stop it when they say they are done.
Pass `--no-open` when no browser should open on this machine. Everything is saved as they paint (`<out folder>/touchup/`).

| tool | does |
|---|---|
| red - clear (1) | made see-through: paper left between an arm and the body, a halo, a speck |
| green - bring back (2) | those pixels taken from the drawing itself: a white shirt or shoe the cut-out took for the paper. A character's frame: its sheet's cell laid on the frame again; a prop: the drawing laid like the sprite (`sprite-src.png`). Off for a flipped facing |
| blue - front piece (3, props) | what stands in front of a person inside the thing (an arch's near posts and curve, a gazebo's roof, a chair's near armrest) → `sprite-front.png` and `"front"` in `sprite.json`: the sprite drawn behind them, this over them |
| eraser (E) | takes paint off |
| ⬠ polygon (P) | corners clicked, closed with a double-click, Enter or the first corner - filled in the current colour (or erased); Backspace takes a corner back, Esc drops it |
| 🪑 a seat | drag the sitter, or the arrow keys a pixel at a time; letting go re-makes the seat from there (`nudge.json`) and works its front piece out anew |

"drawing under" shows the drawing green brings back from; "result" shows what applying will make.

Then `touchup.py SPEC.json --apply` (characters: the strips are packed again; a seat needs no apply - it is re-made as it is moved).
`finish` lays the paintings on again by itself, so they survive a later `finish`; a picture drawn again since it was painted gets its
painting set aside (`touchup/set-aside/`), never laid on a different drawing.

Painting by hand is the most accurate step - the automatic front pieces and placements are a start, the user's eye finishes them;
say so. Never paint for the user without asking, and never `--apply` paintings you made yourself without showing them first.
