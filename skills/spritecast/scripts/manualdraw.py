"""Drawing by hand in the ChatGPT app instead of the API (SPRITECAST_DRAW=manual): no key, no money - the app's own limits instead.
Each picture the pipeline would ask the API for becomes a job on a local page (http://127.0.0.1:8790, SPRITECAST_MANUAL_PORT): the
pictures to attach, the prompt with a copy button. Draw it in ChatGPT (a NEW chat for every job: an earlier picture in the same chat
leaks into the next), save the answer, then drop it on the page - or just let it land in ~/Downloads (SPRITECAST_DOWNLOADS): the
newest picture there after the job was shown is taken. It is fitted to the size the pipeline asked for and the run goes on.
A redraw on the guide's grid with reference pictures is TWO messages in that chat (for_app): the references first, to be answered
"ready", then the guide alone with the prompt."""
import json, os, re, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image

PORT = int(os.environ.get('SPRITECAST_MANUAL_PORT', 8790))
DL = Path(os.environ.get('SPRITECAST_DOWNLOADS', Path.home() / 'Downloads'))
EXT = ('.png', '.jpg', '.jpeg', '.webp')
_job = {}; _got = threading.Event(); _srv = [None]; _n = [0]

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>spritecast - draw by hand</title><style>
body{font:15px system-ui;margin:24px;max-width:1100px;background:#f6f6f2;color:#222}h1{font-size:20px}
.imgs{display:flex;gap:12px;flex-wrap:wrap}.imgs figure{margin:0;background:#fff;padding:8px;border:1px solid #ddd}
.imgs img{max-height:220px;display:block;image-rendering:pixelated}textarea{width:100%;height:220px;font:13px monospace}
button{font-size:15px;padding:8px 16px;margin:6px 0}#drop{border:3px dashed #999;padding:40px;text-align:center;margin-top:16px;background:#fff}
#drop.on{background:#e8f4e8;border-color:#4a4}.step{margin:14px 0}.done{color:#2a7a2a;font-weight:bold}</style></head><body>
<h1>Job <span id="n"></span>: <span id="name"></span></h1><div id="wait"></div>
<div id="pre" hidden>
<div class="step">1. Open a <b>new chat</b> in ChatGPT. FIRST message: attach <span id="prehow"></span> (drag, or right-click &gt; copy), paste this text and send:
 <button id="copypre">Copy first message</button></div>
<div class="imgs" id="preimgs"></div>
<textarea id="pretext" readonly style="height:110px"></textarea>
<div class="step">Wait for its answer: it should only say <b>ready</b>. (If it draws a picture here instead, do not save it - start again in a new chat.)</div>
</div>
<div class="step"><span id="s1"></span></div>
<div class="imgs" id="imgs"></div>
<div class="step"><span id="s2"></span> Paste the prompt: <button id="copy">Copy prompt</button> <span id="size"></span></div>
<textarea id="prompt" readonly></textarea>
<div class="step"><span id="s3"></span> Save ChatGPT's picture. It is taken from your Downloads folder by itself - or drop it here:</div>
<div id="drop">drop the picture here (or click to choose)<input type="file" id="file" accept="image/*" hidden></div>
<script>
let cur=null;
async function poll(){const j=await (await fetch('/job')).json();
 if(!j.name){document.getElementById('wait').innerHTML='<p class=done>Nothing to draw right now - the run is working (or finished).</p>';}
 else document.getElementById('wait').innerHTML='';
 if(j.n!==cur){cur=j.n;document.getElementById('n').textContent=j.n||'';document.getElementById('name').textContent=j.name||'';
  document.getElementById('prompt').value=j.prompt||'';document.getElementById('size').textContent=j.size?('(ask for a '+j.shape+' picture)'):'';
  const two=(j.pre_imgs||[]).length>0,one=(j.imgs||[]).length==1;document.getElementById('pre').hidden=!two;
  document.getElementById('pretext').value=j.pre||'';document.getElementById('prehow').textContent=(j.pre_imgs||[]).length>1?'these pictures in this order':'this picture';
  document.getElementById('preimgs').innerHTML=(j.pre_imgs||[]).map((x,i)=>`<figure><img src="/pre/${j.n}/${i}" draggable=true><figcaption>Picture ${i+1}: ${x}</figcaption></figure>`).join('');
  document.getElementById('s1').innerHTML=two?'2. SECOND message, <b>in the same chat</b>: attach this picture only:'
   :'1. Open a <b>new chat</b> in ChatGPT. Attach '+(one?'this picture':'these pictures <b>in this order</b>')+' (drag, or right-click &gt; copy):';
  document.getElementById('s2').textContent=two?'3.':'2.';document.getElementById('s3').textContent=two?'4.':'3.';
  document.getElementById('imgs').innerHTML=(j.imgs||[]).map((x,i)=>`<figure><img src="/img/${j.n}/${i}" draggable=true><figcaption>Image ${i+1}: ${x}</figcaption></figure>`).join('');}
 setTimeout(poll,1500);}
poll();
document.getElementById('copy').onclick=()=>{navigator.clipboard.writeText(document.getElementById('prompt').value);};
document.getElementById('copypre').onclick=()=>{navigator.clipboard.writeText(document.getElementById('pretext').value);};
const d=document.getElementById('drop'),f=document.getElementById('file');
d.onclick=()=>f.click();f.onchange=()=>send(f.files[0]);
d.ondragover=e=>{e.preventDefault();d.classList.add('on')};d.ondragleave=()=>d.classList.remove('on');
d.ondrop=e=>{e.preventDefault();d.classList.remove('on');send(e.dataTransfer.files[0])};
async function send(file){if(!file)return;const r=await fetch('/upload',{method:'POST',body:file});d.textContent=r.ok?'taken - next job coming':'not taken';}
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ctype):
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == '/': return self._send(200, PAGE.encode(), 'text/html; charset=utf-8')
        if self.path == '/job':
            j = {k: _job.get(k) for k in ('n', 'name', 'prompt', 'size', 'shape', 'pre')}
            for k in ('imgs', 'pre_imgs'): j[k] = [Path(p).name for p in _job.get(k, [])]
            return self._send(200, json.dumps(j).encode(), 'application/json')
        if self.path.startswith(('/img/', '/pre/')):
            _, kind, n, i = self.path.split('/'); ims = _job.get('imgs' if kind == 'img' else 'pre_imgs', [])
            if _job and str(_job.get('n')) == n and i.isdigit() and int(i) < len(ims):
                return self._send(200, Path(ims[int(i)]).read_bytes(), 'image/png')
        self._send(404, b'', 'text/plain')
    def do_POST(self):
        if self.path != '/upload' or not _job: return self._send(400, b'', 'text/plain')
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        tmp = Path(_job['out']).with_suffix('.upload'); tmp.write_bytes(data)
        try: _take(tmp)
        except Exception as e: tmp.unlink(missing_ok=True); return self._send(400, str(e).encode(), 'text/plain')
        self._send(200, b'ok', 'text/plain')


def _take(src):
    """the picture -> the size the pipeline asked for (the app may answer at another size): fitted whole, white around it"""
    im = Image.open(src).convert('RGB'); w, h = map(int, _job['size'].split('x'))
    if im.size != (w, h):
        s = min(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        cv = Image.new('RGB', (w, h), 'white'); cv.paste(im, ((w - im.width) // 2, (h - im.height) // 2)); im = cv
    im.save(_job['out']); Path(src).unlink(missing_ok=True) if str(src).endswith('.upload') else None
    print(f'  {Path(_job["out"]).name}: taken from {Path(src).name}', flush=True); _got.set()


def _start():
    if _srv[0]: return
    _srv[0] = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    threading.Thread(target=_srv[0].serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{PORT}'; print(f'\n  DRAWING BY HAND: open {url} - one job at a time, a new ChatGPT chat for each\n', flush=True)
    if not os.environ.get('SPRITECAST_NO_OPEN'):
        try: webbrowser.open(url)
        except Exception: pass


def for_app(prompt, imgs, shape):
    """the API's request -> what the app follows: (prompt, its pictures, an earlier message, that message's pictures).
    Given two pictures in one message, the app puts BOTH on its canvas (the guide's figures shrunk to the left, the turnaround redrawn
    beside them); given the guide alone, with the layout spelt out, it keeps every figure where it was - but draws plainer (Rain Girl's
    coat lost its buttons). So a redraw on the guide's grid is TWO messages: the reference pictures first ("do not draw yet, answer
    ready"), then the guide alone, its prompt pointing back at them - the layout kept AND the buttons drawn.
    SPRITECAST_MANUAL_GUIDE_ONLY=1: one message, the guide alone, the sentences about the other pictures cut.
    SPRITECAST_MANUAL_ALL_IMAGES=1: one message with every picture, as the API gets it."""
    keep_layout = bool(re.search(r'ON THE SAME GRID|exactly where it is', prompt)); pre, pre_imgs = '', []
    if keep_layout and len(imgs) > 1 and not os.environ.get('SPRITECAST_MANUAL_ALL_IMAGES'):
        if os.environ.get('SPRITECAST_MANUAL_GUIDE_ONLY'):
            cut = re.sub(r'(?m)^Image [2-9] (?:is|shows)\b[^\n]*\n?', '', prompt)
            if not re.search(r'\b[Ii]mages? [2-9]\b', cut): prompt, imgs = cut, imgs[:1]   # (only if nothing else still points at them)
        else:
            n = len(imgs) - 1; one = n == 1
            said = {int(m.group(1)) - 1: m.group(2) for m in re.finditer(r'(?m)^Image ([2-9]) (?:is|shows) ([^\n]*)', prompt)}
            def earlier(m):                                    # "Image 3" -> "picture 2 of my EARLIER message"
                w = 'the picture in my EARLIER message' if one else f'picture {int(m.group(2)) - 1} of my EARLIER message'
                return w[0].upper() + w[1:] if m.group(1) == 'I' else w
            lines = re.sub(r'\b([Ii])mage ([2-9])\b', earlier, prompt).split('\n')
            last = max((i for i, l in enumerate(lines) if re.match(r'(?:The picture in|Picture \d of) my EARLIER message', l)), default=len(lines) - 1)
            lines[last] = lines[last].rstrip() + (' Nothing of ' + ('that picture itself' if one else 'those pictures themselves') + ' goes in the result: only the '
                                                  'picture attached to THIS message is redrawn.')
            what = '\n'.join(('It is ' if one else f'Picture {k} is ') + re.sub(r'\b[Ii]mage 1\b', "my next message's picture", said[k])
                             for k in sorted(said) if k <= n)
            pre = ((f'This picture is a reference' if one else f'These {n} pictures are references') + ' for my next message. Do NOT draw or generate anything yet.\n'
                   + (what + '\n' if what else '') +
                   'In my next message I will attach another picture and ask you to redraw that one; ' + ('this picture is' if one else 'these pictures are') +
                   ' only for the character or object in it - its face, hair, outfit, small details (buttons, pockets, patterns) and colours - and nothing of '
                   + ('it' if one else 'them') + ' goes in the result. For now just answer: ready.')
            prompt, pre_imgs, imgs = '\n'.join(lines), imgs[1:], imgs[:1]
    if keep_layout:
        head = (f'Edit the attached picture. Return ONE picture only: the same {shape} canvas as the attached one, with everything in it at '
                'exactly the same place and the same size - do not shrink it, do not move it, do not add anything beside it (no extra views, no text).\n')
    else: head = f'Make a {shape} picture.\n'
    return head + prompt, imgs, pre, pre_imgs


def draw(prompt, imgs, out, size):
    """one picture, drawn by hand: blocks until it is dropped on the page or saved to Downloads. Returns 0 (dollars)."""
    _start(); _n[0] += 1; w, h = map(int, size.split('x'))
    shape = 'landscape (3:2)' if w > h else 'portrait (2:3)' if h > w else 'square'
    prompt, imgs, pre, pre_imgs = for_app(prompt, list(imgs), shape)
    _job.clear(); _job.update(n=_n[0], name=Path(out).name, prompt=prompt, imgs=[str(p) for p in imgs], out=str(out), size=size, shape=shape,
                              pre=pre, pre_imgs=[str(p) for p in pre_imgs])
    _got.clear(); t0 = time.time(); seen = {p: p.stat().st_mtime for p in DL.glob('*') if p.suffix.lower() in EXT} if DL.exists() else {}
    print(f'  job {_n[0]}: {Path(out).name} - waiting for its picture', flush=True)
    while not _got.wait(2):
        if not DL.exists(): continue
        new = [p for p in DL.glob('*') if p.suffix.lower() in EXT and p.stat().st_mtime > t0 and seen.get(p) != p.stat().st_mtime]
        new = [p for p in new if time.time() - p.stat().st_mtime > 1.5]          # (a download still being written)
        if new:
            try: _take(max(new, key=lambda p: p.stat().st_mtime))
            except Exception as e: print(f'  {new[0].name}: not a picture ({e}) - still waiting', flush=True); seen.update({p: p.stat().st_mtime for p in new})
    _job.clear(); return 0.0
