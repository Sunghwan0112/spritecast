"""pixeledit: the pixel sprites fixed by hand in the browser, frame by frame - a white speck erased, a face redrawn, a face copied from
the frame where it came out best. What pixelart.py cannot settle by rule, the user's eye and a pencil can in a minute.

    python pixeledit.py CHAR.json [--px 96] [--port 8766] [--no-open]     free: a local page; it saves as you draw

The page is on THIS machine (127.0.0.1). A user who works on it from another computer (an editor's remote session, ssh) forwards the
port - VS Code: the Ports panel, "Forward a Port", 8766 - or, if they ask, `--host <an address of their private network>`.

It is a server: run it in the background, give the user the address, stop it when they are done.
What is drawn is kept in <character>/pixel/touch-<px>.json - per animation, per frame, the pixels set and the pixels cleared, in the
frame's own render coordinates - and the strips in out-pixel<px>/ are written again at once. pixelart.py lays the same edits on
whenever it builds the strips again; a frame drawn anew since it was edited (its outline changed) has its edits set aside, never
laid on another drawing."""
import argparse, base64, http.server, io, json, sys, threading, webbrowser
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def load_touch(p): return json.loads(p.read_text()) if p.exists() else {}


def lay(frame, e, origin):
    """a frame (RGBA array, changed in place) with its edits: `e` = {"set": [[x, y, r, g, b], ...], "clear": [[x, y], ...]} in render
    coordinates; `origin` = the frame's corner in those"""
    h, w = frame.shape[:2]
    for x, y in e.get('clear', []):
        x, y = x - origin[0], y - origin[1]
        if 0 <= x < w and 0 <= y < h: frame[y, x] = 0
    for x, y, r, g, b in e.get('set', []):
        x, y = x - origin[0], y - origin[1]
        if 0 <= x < w and 0 <= y < h: frame[y, x] = (r, g, b, 255)
    return frame


def outline_of(frame): return int((frame[..., 3] > 0).sum())


def serve(spec, px, port, open_, host='127.0.0.1'):
    s = json.loads(Path(spec).read_text(encoding='utf-8')); d = Path(spec).resolve().parent / s['name']; out = d / f'out-pixel{px}'; base = d / 'pixel' / f'base-{px}'
    tp = d / 'pixel' / f'touch-{px}.json'; tt = d / 'pixel' / f'touch-{px}-time.json'      # (the time at it, per animation: the editor counts it)
    prop = not (out / 'pixel.json').exists() and (d / 'out-pixel/pixel.json').exists()          # a PROP made by proppixel.py: its views are the frames of one strip, "views"
    if prop: out = d / 'out-pixel'; base = d / 'pixel-base'; tp = d / 'pixel-touch.json'; tt = d / 'pixel-touch-time.json'; px = 'prop'
    if not (out / 'pixel.json').exists() or not base.is_dir(): sys.exit(f'pixeledit: no pixel sprites at {px} px yet - run pixelart.py (a character) or proppixel.py (a prop) first')
    meta = json.loads((out / 'pixel.json').read_text()); fw, fh = meta['frame']; origin = meta.get('origin', [0, 0]); names = [n for n in meta['animations'] if (base / f'{n}.png').exists()]
    lock = threading.Lock()

    def write(name):          # the strip in out-pixel<px>/ = the base strip + this animation's edits
        t = load_touch(tp).get(name, {}); a = np.asarray(Image.open(base / f'{name}.png').convert('RGBA')).copy()
        for k, e in t.items():
            i = int(k); lay(a[:, i * fw:(i + 1) * fw], e, origin)
        Image.fromarray(a).save(out / f'{name}.png')
        if prop: import proppixel; proppixel.split(out)          # (the strip cut back into sprite-<view>.png)

    R = 4          # the 3D render is sent this many times the frame's size: it is there to be read, not to be a sprite
    refs = {}

    def ref(name, i):
        """the 3D RENDER a frame was drawn from, on the frame's own place (PNG, R times the frame) - to look at beside the sprite or under it"""
        if (name, i) in refs: return refs[(name, i)]
        im = Image.new('RGBA', (fw * R, fh * R))
        try:
            if prop:
                v, e = list(meta['views'].items())[i]; vd = d / f'turn-{v}' if (d / f'turn-{v}').exists() else d; r = Image.open(vd / 'render.png').convert('RGBA'); r = r.crop(r.getbbox())
                im.alpha_composite(r.resize((e['size'][0] * R, e['size'][1] * R), Image.LANCZOS), (e['in_frame'][0] * R, e['in_frame'][1] * R))
            else:
                clip, dr = name.split('-', 1); r = Image.open(d / f'render/{clip}-{dr}-{i}.png').convert('RGBA'); st = json.loads((d / 'pixel' / f'state-{px}.json').read_text())
                idle = Image.open(d / 'render/idle-south.png').convert('RGBA').getbbox(); k = round(px * st['scale']) / (idle[3] - idle[1])          # (the render at the sprite's size, as pixelart.py lays the sprite on it)
                r = r.resize((max(1, round(r.width * k * R)), max(1, round(r.height * k * R))), Image.LANCZOS); x, y = (64 - origin[0]) * R, (64 - origin[1]) * R
                big = Image.new('RGBA', (im.width + 2000, im.height + 2000)); big.alpha_composite(r, (x + 1000, y + 1000)); im = big.crop((1000, 1000, 1000 + im.width, 1000 + im.height))
        except Exception: pass          # (no render for it: an empty picture)
        b = io.BytesIO(); im.save(b, 'PNG'); refs[(name, i)] = b.getvalue(); return refs[(name, i)]

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, code, body, ctype):
            self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            u = self.path.split('?')[0]
            if u == '/': return self.send(200, (HERE / 'pixeledit.html').read_bytes(), 'text/html; charset=utf-8')
            if u == '/favicon.ico': return self.send(204, b'', 'image/x-icon')
            if u == '/data':
                t = load_touch(tp); m = json.loads((out / 'pixel.json').read_text()).get('made', {}); sec = load_touch(tt)
                return self.send(200, json.dumps({'name': d.name, 'px': px, 'frame': [fw, fh], 'origin': origin, 'review': meta.get('review', {}),
                                                  'animations': [{'name': n, 'frames': meta['animations'][n], 'edits': t.get(n, {}), 'made': m.get(n, {}), 'seconds': sec.get(n, 0)} for n in names]}).encode(), 'application/json')
            if u.startswith('/base/') and u[6:-4] in names: return self.send(200, (base / f'{u[6:-4]}.png').read_bytes(), 'image/png')
            if u.startswith('/ref/') and u.endswith('.png') and u[5:-4].rsplit('/', 1)[0] in names: n_, i_ = u[5:-4].rsplit('/', 1); return self.send(200, ref(n_, int(i_)), 'image/png')
            self.send(404, b'not found', 'text/plain')

        def do_POST(self):
            if self.path != '/save': return self.send(404, b'', 'text/plain')
            j = json.loads(self.rfile.read(int(self.headers['Content-Length']))); name, k = j.get('name'), str(j.get('frame'))
            if name not in names: return self.send(400, b'unknown animation', 'text/plain')
            with lock:
                t = load_touch(tp); a = np.asarray(Image.open(base / f'{name}.png').convert('RGBA')); i = int(k)
                e = {'set': [[int(v) for v in p] for p in j.get('set', [])], 'clear': [[int(v) for v in p] for p in j.get('clear', [])],
                     'outline': outline_of(a[:, i * fw:(i + 1) * fw])}            # (what the frame was when edited: a frame drawn anew sets its edits aside)
                if e['set'] or e['clear']: t.setdefault(name, {})[k] = e
                else: t.get(name, {}).pop(k, None)
                tp.write_text(json.dumps(t, separators=(',', ':'))); write(name)
                if j.get('seconds'): sec = load_touch(tt); sec[name] = max(int(j['seconds']), sec.get(name, 0)); tt.write_text(json.dumps(sec))
            self.send(200, b'{"ok":true}', 'application/json')

    srv = http.server.ThreadingHTTPServer((host, port), H); url = f'http://{host}:{srv.server_address[1]}/'
    print(f'pixeledit: {url}  ({d.name}, {px} px, {len(names)} animations) - draw; it saves as you go. Ctrl+C here when done.', flush=True)
    if open_: threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\npixeledit: closed')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--px', type=int, default=96); ap.add_argument('--port', type=int, default=8766)
    ap.add_argument('--no-open', action='store_true')
    ap.add_argument('--host', default='127.0.0.1', help='the address to listen on. 127.0.0.1 (this machine only) unless the user works on this machine from another one and asks: then an address of a private network they are on - anyone who can reach it can edit')
    a = ap.parse_args(); serve(a.spec, a.px, a.port, not a.no_open, a.host)
