"""pixelsmall: a pixel set smaller than 64 px, made from the 64-px set (free). pixelart.py runs it by itself for --px under 64.

    python pixelsmall.py CHAR.json [--to 32] [--from 64]     -> <character>/out-pixel<to>/  (strips, shadows, pixel.json, preview.gif)

THE IMAGE MODEL IS NEVER ASKED FOR LESS THAN 64. It draws its squares at a size of its own, and with few squares one square off is
an eye gone: asked for 32 directly, figures came back squashed, or 45 px tall, or with a face on the back of a head - by every
sheet layout tried. A set drawn at 64 for a character DESIGNED small (about three heads tall) is clean; reduced, it keeps the same
motion, the same person in every facing and the same frames - with a rougher face, which pixeledit.py is for (edit the 64 set, run
this again).

How: every block of the big set becomes one pixel in the block's commonest colour (a tie: the stronger tone - an eye, a line - over
the flat one); a block on the figure's rim that holds any of the outline's dark stays dark, so the outline stays one pixel wide
instead of thinning away; a block less than a third covered, with no dark in it, is dropped. The feet's row is kept."""
import argparse, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

LUM = np.array([0.299, 0.587, 0.114])


def edges(n, k):          # where each small pixel's block starts in the big frame, counted from the END (the feet, the right side stay whole blocks' worth)
    m = max(1, round(n * k)); e = np.round(n - (m - np.arange(m + 1)) / k).astype(int); e[0] = max(e[0], 0); return np.maximum.accumulate(np.clip(e, 0, n))


def reduce(a, k):
    ys, xs = edges(a.shape[0], k), np.round(np.arange(max(1, round(a.shape[1] * k)) + 1) / k).astype(int).clip(0, a.shape[1]); out = np.zeros((len(ys) - 1, len(xs) - 1, 4), np.uint8)
    for y in range(len(ys) - 1):
        for x in range(len(xs) - 1):
            b = a[ys[y]:max(ys[y] + 1, ys[y + 1]), xs[x]:max(xs[x] + 1, xs[x + 1])].reshape(-1, 4); op = b[:, 3] > 0; n = int(op.sum())
            if n == 0: continue
            cols = [tuple(int(v) for v in c[:3]) for c in b[op]]; dark = [c for c in cols if np.dot(c, LUM) < 70]
            if n * 3 < len(b) and not dark: continue
            if n < len(b) and dark: c = Counter(dark).most_common(1)[0][0]
            else:
                cnt = Counter(cols).most_common(); c = max((c for c, q in cnt if q == cnt[0][1]), key=lambda q: abs(np.dot(q, LUM) - 128))
            out[y, x] = (*c, 255)
    return out


def shade(a, k):          # a shadow's frame: a pixel where half its block or more is shadow, the colour and strength kept
    ys, xs = edges(a.shape[0], k), np.round(np.arange(max(1, round(a.shape[1] * k)) + 1) / k).astype(int).clip(0, a.shape[1]); out = np.zeros((len(ys) - 1, len(xs) - 1, 4), np.uint8); on = a[..., 3] > 0
    if not on.any(): return out
    c = a[on][0]
    for y in range(len(ys) - 1):
        for x in range(len(xs) - 1):
            b = on[ys[y]:max(ys[y] + 1, ys[y + 1]), xs[x]:max(xs[x] + 1, xs[x + 1])]
            if b.mean() >= 0.5: out[y, x] = c
    return out


def strip(p, fw, fn, k):
    a = np.asarray(Image.open(p).convert('RGBA')); return [fn(a[:, i * fw:(i + 1) * fw], k) for i in range(a.shape[1] // fw)]


def main(spec, src_px=64, to=32):
    s = json.loads(Path(spec).read_text(encoding='utf-8')); d = Path(spec).resolve().parent / s['name']; src = d / f'out-pixel{src_px}'; out = d / f'out-pixel{to}'; k = to / src_px
    if to >= src_px: sys.exit(f'pixelsmall: {to} is not smaller than {src_px}')
    if not (src / 'pixel.json').exists(): sys.exit(f'pixelsmall: no pixel set at {src_px} px yet - run pixelart.py CHAR.json --px {src_px} first')
    j = json.loads((src / 'pixel.json').read_text()); fw, fh = j['frame']; out.mkdir(exist_ok=True); (out / 'shadows').mkdir(exist_ok=True); frames = {}
    for name in j['animations']:
        fr = strip(src / f'{name}.png', fw, reduce, k); frames[name] = fr; Image.fromarray(np.concatenate(fr, 1)).save(out / f'{name}.png')
    first = frames[next(iter(frames))][0]; w2, h2 = first.shape[1], first.shape[0]; sh = {}
    for name, v in j.get('shadows', {}).items():
        if name not in frames or not (src / v['file']).exists(): continue
        fr = strip(src / v['file'], v['frame'][0], shade, k); Image.fromarray(np.concatenate(fr, 1)).save(out / v['file'])
        # (both are kept by their bottom rows: the shadow's place against the sprite is the same distance from the two bottoms, made smaller)
        sh[name] = {'file': v['file'], 'frame': [fr[0].shape[1], fr[0].shape[0]], 'offset': [round(v['offset'][0] * k), h2 - fr[0].shape[0] - round((fh - v['frame'][1] - v['offset'][1]) * k)]}
    rel = {}
    for name, r in j.get('release', {}).items():          # the thing let go: the same frame and way, the place and every speed made smaller
        rel[name] = {q: r[q] for q in ('thing', 'frame', 'toward', 'ground_slope') if q in r}
        rel[name].update(at=[round(r['at'][0] * k), h2 - round((fh - r['at'][1]) * k)], speed=round(r['speed'] * k, 1), up=round(r['up'] * k, 1), gravity=round(r['gravity'] * k, 2), hand_above_feet=round(r['hand_above_feet'] * k))
        t = src / f"{r['thing']}.png"
        if t.exists(): Image.fromarray(reduce(np.asarray(Image.open(t).convert('RGBA')), k)).save(out / t.name)
    fig = int(np.median([np.ptp(np.nonzero(fr[0][..., 3].any(1))[0]) + 1 for fr in frames.values()]))
    (out / 'pixel.json').write_text(json.dumps({'made_from': f'out-pixel{src_px}', 'asked_px': to, 'figure_px': fig, 'frame': [w2, h2], 'animations': j['animations'], 'shadows': sh, 'release': rel,
                                                'shadow_colour': j.get('shadow_colour'), 'shadow_alpha': j.get('shadow_alpha')}, indent=1))
    z = max(2, 300 // h2); names = list(frames); cols = min(4, len(names)); rows = (len(names) + cols - 1) // cols; gif = []
    for i in range(max(len(f) for f in frames.values())):
        g = Image.new('RGB', (cols * (w2 + 4) * z, rows * (h2 + 4) * z), (58, 62, 74))
        for q, name in enumerate(names):
            f = Image.fromarray(frames[name][min(i, len(frames[name]) - 1)]).resize((w2 * z, h2 * z), Image.NEAREST); g.paste(f, ((q % cols) * (w2 + 4) * z + 2 * z, (q // cols) * (h2 + 4) * z + 2 * z), f)
        gif.append(g)
    gif[0].save(out / 'preview.gif', save_all=True, append_images=gif[1:], duration=120, loop=0)
    print(f'{out}: {len(frames)} animations made from the {src_px}-px set (the image model is never asked for less than 64): frame {w2}x{h2}, the figure ~{fig} px - look at preview.gif. '
          f'Faces are rougher at this size: fix them in the {src_px} set (pixeledit.py) and run this again.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--to', type=int, default=32); ap.add_argument('--from', dest='src', type=int, default=64); a = ap.parse_args(); main(a.spec, a.src, a.to)
