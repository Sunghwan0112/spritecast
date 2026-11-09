"""touchup: the finished pictures fixed by hand in the browser - paper left between the limbs cleared, a piece the cut-out took back
from the drawing, and a prop's front piece (what a person walking into it passes behind) painted.

    python touchup.py SPEC.json [--port 8765]    free: a local page with every finished picture of that character or prop; paint, it saves
    python touchup.py SPEC.json --apply          free: the paintings applied (then the strips packed again: charpipe.py pack / the prop's
                                                 sprite.json); `finish` applies them by itself, so a later `finish` keeps them

The colours, painted over the picture:
  red   - clear: made see-through (paper between an arm and the body, a speck, a halo)
  green - bring back: the pixels taken from the drawing itself (a white shirt on the white paper the cut-out took for paper)
  blue  - front piece (props): what stands in front of a person inside the thing → sprite-front.png beside sprite.png, the whole
          picture drawn behind them and the front piece over them (an arch, a gazebo's roof and near posts, a chair's armrest)
A prop with characters seated on it (seat.py) lists each seat too: drag the sitter (or the arrow keys, a pixel at a time) to where they
should sit; on letting go the seat is made again from there (seat/<…>/nudge.json) and its front piece worked out anew.

The paintings are kept in <the output folder>/touchup/ (masks/, base/ - each picture as it was when painted, state.json); a picture drawn
again since it was painted keeps its painting aside and says so, it is never laid on a different drawing.
Where a character's frame comes from: its drawn sheet's cell (frames/cut/, the drawing's own colours kept under the cut-out), laid on the
frame again by the scale and place that cover its outline best. A facing flipped from its pair has none (green is off there).
"""
import argparse, base64, hashlib, http.server, io, json, re, shutil, sys, threading, webbrowser
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import signal

HERE = Path(__file__).resolve().parent
FRONT = 'sprite-front.png'


# --- what there is to touch up ---------------------------------------------------------------------------------------------------------
def target(spec_path, out=None):
    """(kind, out folder, [(rel, file)]): a character's frames (frames/walk-*, frames/idle-*) or a prop's sprite.png (one per view)"""
    p = Path(spec_path).resolve(); s = json.loads(p.read_text(encoding='utf-8')); d = Path(out).resolve() if out else p.parent / s['name']
    if (d / 'frames').is_dir():
        files = sorted((d / 'frames').glob('walk-*.png'), key=_frame_order) + sorted((d / 'frames').glob('idle-*.png')) + sorted((d / 'frames').glob('sit-*.png'))
        return 'character', d, [(f'frames/{f.name}', f) for f in files]
    sp = sorted(d.glob('sprite.png')) + sorted(d.glob('turn-*/sprite.png')) + sorted(d.glob('*-*/sprite.png'))
    seen, out = set(), []
    for f in sp:
        rel = f.relative_to(d).as_posix()
        if rel not in seen: seen.add(rel); out.append((rel, f))
    if not out: sys.exit(f'touchup: nothing finished in {d} yet - run `finish` first')
    return 'prop', d, out


def seats_of(d):
    """the seated characters put on this prop by seat.py: [(rel of the seat's folder, its folder)]"""
    return [(p.parent.relative_to(d).as_posix(), p.parent) for p in sorted(d.glob('**/seat/*/seat.json'))]


def _frame_order(f):
    m = re.match(r'walk-(.+)-(\d+)\.png$', f.name); return (m.group(1), int(m.group(2))) if m else (f.name, 0)


def sha(path_or_bytes):
    b = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes(); return hashlib.sha1(b).hexdigest()


def state(d):
    p = d / 'touchup/state.json'; return json.loads(p.read_text()) if p.exists() else {}


def save_state(d, st):
    (d / 'touchup').mkdir(exist_ok=True); (d / 'touchup/state.json').write_text(json.dumps(st, indent=1))


def base_of(d, rel, f, st):
    """the picture as it was before any painting of it: touchup/base/<rel>. The file now is that (untouched), or what the painting made of
    it (applied), or something new (drawn again since: it becomes the base and an old painting is set aside)"""
    b = d / 'touchup/base' / rel; e = st.get(rel, {}); now = sha(f)
    if b.exists() and now in (e.get('base'), e.get('out')): return b
    if b.exists() and (d / 'touchup/masks' / rel).exists():
        aside = d / 'touchup/set-aside' / rel; aside.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(d / 'touchup/masks' / rel), aside)
        print(f'touchup: {rel} was drawn again since it was painted - its painting set aside in {aside.parent}')
    b.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, b); st[rel] = {'base': now}; return b


# --- where a character's frame came from -------------------------------------------------------------------------------------------------
def cells_for(d, rel):
    """the cut cells (frames/cut/: the drawing's colours kept under the cut-out's alpha) this frame can have come from, newest first"""
    name = Path(rel).name; cut = d / 'frames/cut'
    m = re.match(r'walk-(.+)-(\d+)\.png$', name)
    if m:
        dr, k = m.group(1), int(m.group(2)); g, n = k // 4, k % 4
        pats = [f'walk-{dr}-single-{k}-1-', f'walk-{dr}-drawn-{g}-{n}-']
    else:
        what, dr = re.match(r'(idle|sit)-(.+)\.png$', name).groups()
        groups = (['south', 'south-east', 'south-west', 'east'], ['west', 'north-east', 'north-west', 'north'])
        g = next(i for i, ds in enumerate(groups) if dr in ds); pats = [f'{what}-drawn-{g}-{groups[g].index(dr)}-']
    for p in pats:
        got = sorted(cut.glob(f'{p}*.png'), key=lambda f: f.stat().st_mtime, reverse=True)
        if got: return got
    return []


def fit(cell, fr):
    """the cell's scale and place on the frame where its outline overlaps the frame's most → (overlap, scale, x, y)"""
    fa = np.asarray(fr)[..., 3] > 128; ca = np.asarray(cell)[..., 3] > 128
    if not fa.any() or not ca.any(): return (0, 1, 0, 0)
    s0 = (np.ptp(np.nonzero(fa.any(1))[0]) + 1) / (np.ptp(np.nonzero(ca.any(1))[0]) + 1)
    best, q = (-1, 1, 0, 0), 2; F = fa[::q, ::q].astype(np.float32)
    for s in np.arange(s0 * 0.85, s0 * 1.15, s0 * 0.01):                      # searched at half size, then refined
        C = (np.asarray(cell.resize((max(1, round(cell.width * s / q)), max(1, round(cell.height * s / q))), Image.BILINEAR))[..., 3] > 128).astype(np.float32)
        cor = signal.fftconvolve(F, C[::-1, ::-1], mode='full'); iy, ix = np.unravel_index(np.argmax(cor), cor.shape)
        ty, tx = iy - (C.shape[0] - 1), ix - (C.shape[1] - 1)
        iou = _iou(F > 0, C > 0, tx, ty)
        if iou > best[0]: best = (iou, s, tx * q, ty * q)
    _, s, tx, ty = best; C = np.asarray(cell.resize((round(cell.width * s), round(cell.height * s)), Image.BILINEAR))[..., 3] > 128
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            iou = _iou(fa, C, tx + dx, ty + dy)
            if iou > best[0]: best = (iou, s, tx + dx, ty + dy)
    return best


def _iou(F, C, X, Y):
    canvas = np.zeros_like(F); y0, x0 = max(0, Y), max(0, X); y1, x1 = min(F.shape[0], Y + C.shape[0]), min(F.shape[1], X + C.shape[1])
    if y1 <= y0 or x1 <= x0: return 0.0
    canvas[y0:y1, x0:x1] = C[y0 - Y:y1 - Y, x0 - X:x1 - X]; return float((canvas & F).sum() / max(1, (canvas | F).sum()))


def source(d, rel, base):
    """the drawing behind this picture, on its canvas, opaque (the paper white where the drawing had nothing) - cached in touchup/src/;
    None when there is none (a flipped facing, a prop finished before this version)"""
    out = d / 'touchup/src' / rel
    if out.exists() and out.stat().st_mtime >= base.stat().st_mtime: return out
    fr = Image.open(base).convert('RGBA'); src = None
    if rel.startswith('frames/'):
        best = None
        for c in cells_for(d, rel)[:1]:
            cell = Image.open(c).convert('RGBA'); r = fit(cell, fr)
            if best is None or r[0] > best[0]: best = (*r, cell)
        if best and best[0] > 0.6:
            iou, s, X, Y, cell = best
            big = cell.convert('RGB').resize((round(cell.width * s), round(cell.height * s)), Image.LANCZOS)   # (the colours alone: an RGBA resize blackens what sits under alpha 0)
            src = Image.new('RGB', fr.size, (255, 255, 255)); src.paste(big, (X, Y))
    else:
        f = d / Path(rel).parent / 'sprite-src.png'
        if f.exists(): src = Image.open(f).convert('RGB')
    if src is None: return None
    out.parent.mkdir(parents=True, exist_ok=True); src.save(out); return out


# --- applying a painting -------------------------------------------------------------------------------------------------------------
def painted(mask):
    """the painting (RGBA, the colours above) → (clear, bring back, front) as boolean masks"""
    m = np.asarray(mask.convert('RGBA')).astype(int); a = m[..., 3] > 40
    r, g, b = m[..., 0], m[..., 1], m[..., 2]
    return a & (r > 150) & (g < 120) & (b < 120), a & (g > 150) & (r < 120) & (b < 120), a & (b > 150) & (r < 120) & (g < 160)


def apply_one(d, kind, rel, f, st, quiet=False):
    mp = d / 'touchup/masks' / rel
    if not mp.exists(): return False
    base = base_of(d, rel, f, st)
    if not mp.exists(): return False                                          # (set aside just now)
    im = np.asarray(Image.open(base).convert('RGBA')).copy(); clear, back, front = painted(Image.open(mp))
    if back.any():
        sp = source(d, rel, base)
        if sp is None: print(f'touchup: {rel} - nothing to bring back from (no drawing behind it): green left out')
        else:
            src = np.asarray(Image.open(sp).convert('RGB')); im[back, :3] = src[back]; im[back, 3] = 255
    im[clear] = 0
    out = Image.fromarray(im.astype(np.uint8)); out.save(f)
    if kind == 'prop':
        fp = f.parent / FRONT
        if front.any():
            fr = im.copy(); fr[~front] = 0; Image.fromarray(fr.astype(np.uint8)).save(fp)
        elif fp.exists(): fp.unlink()
        sj = f.parent / 'sprite.json'
        if sj.exists():
            j = json.loads(sj.read_text())
            if front.any(): j['front'] = {'file': FRONT, 'note': 'the same size and anchor as the sprite: draw the sprite behind whoever stands in the thing and this over them'}
            else: j.pop('front', None)
            sj.write_text(json.dumps(j, indent=1))
    st.setdefault(rel, {})['out'] = sha(f)
    if not quiet: print(f'touchup: {rel} - cleared {int(clear.sum())} px, brought back {int(back.sum())}, front piece {int(front.sum())}')
    return True


def apply(spec_path, quiet=False, out=None):
    """every painting laid on its picture (from the picture as it was before) → how many"""
    kind, d, items = target(spec_path, out); st = state(d); n = 0
    if not (d / 'touchup/masks').is_dir(): return 0
    for rel, f in items:
        try: n += apply_one(d, kind, rel, f, st, quiet)
        except Exception as e: print(f'touchup: {rel} - {e}')
    save_state(d, st)
    if n and not quiet: print(f'touchup: {n} pictures painted')
    return n


# --- the page --------------------------------------------------------------------------------------------------------------------------
def serve(spec_path, port, out=None):
    kind, d, items = target(spec_path, out); st = state(d)
    for rel, f in items: base_of(d, rel, f, st)
    save_state(d, st); files = dict(items); seats = dict(seats_of(d)) if kind == 'prop' else {}

    def png(path):
        return Path(path).read_bytes() if path and Path(path).exists() else None

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, code, body, ctype):
            self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            u = self.path.split('?')[0]
            if u == '/': return self.send(200, (HERE / 'touchup.html').read_bytes(), 'text/html; charset=utf-8')
            if u == '/list':
                out = [{'rel': rel, 'painted': (d / 'touchup/masks' / rel).exists()} for rel, _ in items]
                out += [{'rel': rel, 'seat': True, 'painted': bool(json.loads((sd / 'seat.json').read_text()).get('nudge_px', [0, 0]) != [0, 0])} for rel, sd in seats.items()]
                return self.send(200, json.dumps({'kind': kind, 'name': d.name, 'items': out}).encode(), 'application/json')
            m = re.match(r'/seat/(.+)/(info|sprite|frame|front)$', u)
            if m and m.group(1) in seats:
                sd = seats[m.group(1)]; j = json.loads((sd / 'seat.json').read_text()); vd = sd.parent.parent
                if m.group(2) == 'info': return self.send(200, json.dumps(j).encode(), 'application/json')
                p = {'sprite': vd / 'sprite.png', 'front': sd / 'front.png',
                     'frame': Path(j['made_by']['char']).parent / j['frame']}[m.group(2)]
                return self.send(200, p.read_bytes(), 'image/png')
            m = re.match(r'/(base|src|mask)/(.+)$', u)
            if m and m.group(2) in files:
                w, rel = m.groups()
                p = (d / 'touchup/base' / rel) if w == 'base' else (d / 'touchup/masks' / rel) if w == 'mask' else source(d, rel, d / 'touchup/base' / rel)
                b = png(p)
                return self.send(200, b, 'image/png') if b else self.send(404, b'none', 'text/plain')
            self.send(404, b'not found', 'text/plain')

        def do_POST(self):
            if self.path == '/nudge':                                    # a seated character moved on its seat: made again from there
                j = json.loads(self.rfile.read(int(self.headers['Content-Length']))); sd = seats.get(j.get('rel'))
                if not sd: return self.send(400, b'unknown seat', 'text/plain')
                (sd / 'nudge.json').write_text(json.dumps([int(j['dx']), int(j['dy'])]))
                import seat as SEAT; SEAT.rerun(sd)
                return self.send(200, b'{"ok":true}', 'application/json')
            if self.path != '/save': return self.send(404, b'', 'text/plain')
            j = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            rel = j.get('rel')
            if rel not in files: return self.send(400, b'unknown picture', 'text/plain')
            mp = d / 'touchup/masks' / rel; mp.parent.mkdir(parents=True, exist_ok=True)
            data = base64.b64decode(j['png'].split(',', 1)[1]); im = Image.open(io.BytesIO(data)).convert('RGBA')
            if np.asarray(im)[..., 3].any(): im.save(mp)
            elif mp.exists(): mp.unlink()
            self.send(200, b'{"ok":true}', 'application/json')

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H)
    url = f'http://127.0.0.1:{srv.server_address[1]}/'
    print(f'touchup: {url}  ({kind}, {len(items)} pictures) - paint, then Ctrl+C here and `touchup.py {spec_path} --apply`', flush=True)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\ntouchup: closed')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec'); ap.add_argument('--apply', action='store_true'); ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--no-open', action='store_true', help='do not open the browser')
    ap.add_argument('--out', help='a prop finished with isoprop.py --out DIR: that folder')
    a = ap.parse_args()
    if a.no_open: webbrowser.open = lambda *x, **k: None
    if a.apply:
        n = apply(a.spec, out=a.out)
        kind = target(a.spec, a.out)[0]
        if n and kind == 'character':
            import charpipe; s, d = charpipe.load(a.spec); charpipe.pack(s, d, {'touchup': n})
    else: serve(a.spec, a.port, a.out)
