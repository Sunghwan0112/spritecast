# Drawing by hand in the ChatGPT app (`SPRITECAST_DRAW=manual`)

For a user with no OpenAI key, or who wants to spend nothing on drawing. Every script that draws through SpriteCast's one drawing call
takes it: `pixelart.py --manual`, and any other step run with `SPRITECAST_DRAW=manual` in its environment - `isoprop.py draw`,
`charpipe.py turnaround / draw / redraw / frame / sit --draw`, `creature.py design / walk / sheet`, `proppixel.py`, `propanim.py`
(`scripts/manualdraw.py`). Nothing is sent to OpenAI and nothing is paid for the drawing. `pixelart.py --manual` and `isoprop.py
draw` ask no `--yes`; the other scripts still want `--yes` to start, and the cost they print does not apply - say so. A Tripo step
(`charpipe.py 3d`, `isoprop.py model`) is still paid: it is not a drawing.

- Each picture becomes a job on a local page (http://127.0.0.1:8790, `SPRITECAST_MANUAL_PORT`): the pictures to attach and the prompt
  with a copy button. The user draws it in a NEW ChatGPT chat each time (an earlier picture in the same chat leaks into the next; the free
  plan works, within its limits), saves the answer, and drops it on the page - or lets it land in ~/Downloads (`SPRITECAST_DOWNLOADS`):
  the newest picture there after the job was shown is taken, fitted to the size asked for, and the run goes on.
- **A redraw on a guide's grid with reference pictures is TWO messages** in that chat, and the page shows both: first the reference
  pictures (the turnaround, the first sheet) with "do not draw yet, answer ready", then the guide ALONE with the prompt. Why: given the
  pictures together the app put them all on one canvas; given the guide alone it kept the layout but drew plainer (the coat lost its
  buttons); references first, guide second kept the layout and drew the buttons. If the first message is answered with a picture
  instead of "ready", they start a new chat.
- `SPRITECAST_MANUAL_GUIDE_ONLY=1`: one message, the guide alone. `SPRITECAST_MANUAL_ALL_IMAGES=1`: one message with every picture, as
  the API gets it.
- Tell the user what to expect: the same character, a little plainer than the API's, and a frame may need drawing again. Tried on
  pixel-art sheets (a first sheet with the turnaround; later sheets with two references not yet); the other steps work the same way,
  untested.
