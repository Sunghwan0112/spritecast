"""proprig: a prop's 3D model given a few bones and moved - a ghost's tail swaying, its little arms swinging - each pose written as a
GLB with the model's own texture and rendered at the game's camera (isoprop.py render), for propanim.py to draw as pixel art. Free.
    python proprig.py PROP.json                 # <prop>/rig/<i>.glb and rig/pose-<i>/render.png, rig/poses.png, rig/poses.gif
The bones are found from the mesh: its long axis (the head at the end with the most round it, the tail at the thin end) with a chain of
four along the tail, and the arms - what sticks out of the body's round at its sides. "rig" in the spec, every key optional:
    "rig": {"frames": 8, "tail": {"amp": 5, "lag": 0.9}, "arms": {"amp": 8, "swing": "fore-aft", "front": -1, "together": true}}
  tail: a wave down it from side to side, each joint "lag" later than the one before, "amp" degrees at a joint (5: a snail's slither)
  arms: "fore-aft" (to and fro) or "up" (up and down), "amp" degrees, once a loop with the tail; "together" or one against the other;
        "front": which way is the thing's front (-1 or 1: look at rig/poses.png - the arm that comes towards the viewer is right)
Every pose is scaled and placed the same (an unseen anchor at the box round them all), so the frames line up."""
import sys, json, math, subprocess, numpy as np, trimesh
from pathlib import Path

spec_p = Path(sys.argv[1]).resolve(); spec = json.loads(spec_p.read_text()); out = spec_p.parent / spec['name'] / 'rig'; out.mkdir(parents=True, exist_ok=True)
RIG = spec.get('rig') or {}; TAIL = {'amp': 5.0, 'lag': 0.9, **(RIG.get('tail') or {})}; ARMC = {'amp': 8.0, 'swing': 'fore-aft', 'front': -1, 'together': True, **(RIG.get('arms') or {})}
NF = int(RIG.get('frames', 8))
scene = trimesh.load(spec_p.parent / spec['model']['glb'])
if not isinstance(scene, trimesh.Scene): scene = trimesh.Scene(scene)
nodes = [(n, scene.graph[n]) for n in scene.graph.nodes_geometry]          # (node, (transform, geometry name))
allv = np.vstack([trimesh.transform_points(scene.geometry[g].vertices, T) for n, (T, g) in nodes])

# THE AXIS: the long one; the head at the end with the most round it, the tail at the thin end
c = allv.mean(0); ax = np.linalg.svd(allv - c, full_matrices=False)[2][0]; t = (allv - c) @ ax
r = np.linalg.norm((allv - c) - np.outer(t, ax), axis=1)
if r[t > np.percentile(t, 85)].mean() > r[t < np.percentile(t, 15)].mean(): ax = -ax; t = -t
up = np.array([0, 1.0, 0]); side = np.cross(ax, up); side /= np.linalg.norm(side); bend = np.cross(side, ax); bend /= np.linalg.norm(bend)          # bending about this: the tail goes from side to side
t0, t1 = np.percentile(t, 35), t.max()          # the tail: from a little behind the middle to the tip
NB = 4; js = np.linspace(t0, t1, NB + 1)[:-1]          # joints along the tail
print('axis', ax.round(3), 'tail from', round(t0, 3), 'to', round(t1, 3), 'joints', js.round(3))


# THE ARMS: what sticks out of the body's round at the sides (the head's half); each turns about its root - a wiggle, up and down
bins = np.linspace(t.min(), t.max(), 40); bi = np.clip(np.digitize(t, bins) - 1, 0, 38)
base = np.array([np.percentile(r[bi == i], 60) if (bi == i).sum() > 20 else 0 for i in range(39)]); outr = r - base[bi]
ARMS = []
for sgn in (-1, 1):
    m_ = (outr > 0.05) & (t < np.percentile(t, 70)) & (np.sign((allv - c) @ side) == sgn)
    if m_.sum() < 50: continue
    tipc = allv[m_ & (outr > np.percentile(outr[m_], 70))].mean(0); rootc = allv[m_ & (outr < np.percentile(outr[m_], 25))].mean(0)
    d_ = tipc - rootc; L = np.linalg.norm(d_); ARMS.append({'root': rootc, 'dir': d_ / L, 'len': L, 'centre': allv[m_].mean(0), 'sgn': sgn})
print('arms', [(a_['sgn'], a_['root'].round(3), round(a_['len'], 3)) for a_ in ARMS])


def arm_weights(V):
    tv = (V - c) @ ax; rv = np.linalg.norm((V - c) - np.outer(tv, ax), axis=1); bv = np.clip(np.digitize(tv, bins) - 1, 0, 38); ov = rv - base[bv]
    ws = []
    for a_ in ARMS:
        near = np.linalg.norm(V - a_['centre'], axis=1) < 0.9 * a_['len']; along = (V - a_['root']) @ a_['dir']
        w = np.clip(along / a_['len'], 0, 1) * np.clip((ov - 0.035) / 0.07, 0, 1) * near * (np.sign((V - c) @ side) == a_['sgn'])
        ws.append(w ** 0.7)
    return ws


def arms_move(V, angs):
    out = V.copy(); ws = arm_weights(V)
    for a_, w, ang in zip(ARMS, ws, angs):
        u = up.copy() if ARMC['swing'] == 'up' else ARMC['front'] * np.cross(side, ax); u = u - (u @ a_['dir']) * a_['dir']; u /= np.linalg.norm(u)          # towards the front: a swing to and fro
        k = np.cross(a_['dir'], u); k /= np.linalg.norm(k); m = w > 0
        for i in np.nonzero(m)[0]: out[i] = a_['root'] + rotm(k, ang * w[i]) @ (V[i] - a_['root'])
    return out


def rotm(axis, ang):
    a = np.radians(ang); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def deform(V, angles):
    """the tail bends along a curve: joint i adds angles[i] (degrees, about `bend`) spread over its segment, so the bend grows smooth
    from root to tip; each vertex keeps its offset from the axis, turned with the curve where it is"""
    seg = (t1 - js[0]) / NB
    xs = np.linspace(js[0], t1 + 1e-3, 400)
    A = sum(a_ * np.clip((xs - j_) / seg, 0, 1) for a_, j_ in zip(angles, js))          # the angle along the tail
    dirs = np.stack([rotm(bend, a_) @ ax for a_ in A]); dx = np.diff(xs, prepend=xs[0])
    curve = c + ax * js[0] + np.cumsum(dirs * dx[:, None], 0)
    tv = (V - c) @ ax; out = V.copy(); m = tv > js[0]
    k = np.clip(np.searchsorted(xs, tv[m]), 0, len(xs) - 1)
    off = V[m] - (c + np.outer(tv[m], ax))
    out[m] = curve[k] + np.einsum('nij,nj->ni', np.stack([rotm(bend, A[i]) for i in k]), off)
    return out


# THE POSES, one loop: the tail's wave, the arms once with it
ARMP = {f'{i}': [ARMC['amp'] * math.sin(2 * math.pi * i / NF), ARMC['amp'] * math.sin(2 * math.pi * i / NF) * (1 if ARMC['together'] else -1)] for i in range(NF)}
POSES = {f'{i}': [TAIL['amp'] * math.sin(2 * math.pi * i / NF - TAIL['lag'] * j) * (0.6 + 0.4 * j / (NB - 1)) for j in range(NB)] for i in range(NF)}
deformed = {}
for name, ang in POSES.items():
    deformed[name] = [trimesh.transform_points(deform(arms_move(trimesh.transform_points(scene.geometry[g].vertices, T), ARMP.get(name, [0, 0])), ang), np.linalg.inv(T)) for n, (T, g) in nodes]
# ONE BOX for every pose (an unseen anchor at its corners), so the renderer scales and centres them all the same and they line up
allp = np.vstack([trimesh.transform_points(v, T) for name in POSES for v, (n, (T, g)) in zip(deformed[name], nodes)])
lo, hi = allp.min(0), allp.max(0)
for name in POSES:
    s = scene.copy()
    for v, (n, (T, g)) in zip(deformed[name], nodes): s.geometry[g].vertices = v
    anchor = trimesh.Trimesh(vertices=[lo, lo, lo + 1e-6 * 0, hi, hi, hi], faces=[[0, 1, 2], [3, 4, 5]], process=False)
    s.add_geometry(anchor, geom_name='anchor')
    s.export(out / f'{name}.glb'); print('pose', name)
json.dump({'poses': list(POSES), 'box': [lo.tolist(), hi.tolist()]}, open(out / 'poses.json', 'w'))

# EACH POSE RENDERED as the prop is (its camera, its turn, its light), in rig/pose-<i>/
for i in range(NF):
    ps = json.loads(json.dumps(spec)); ps['name'] = f'pose-{i}'; ps['model']['glb'] = f'{i}.glb'; ps.pop('translucent', None); ps.pop('rig', None)
    pp = out / f'pose-{i}.json'; pp.write_text(json.dumps(ps, indent=1))
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'isoprop.py'), 'render', str(pp)], check=True, capture_output=True)
from PIL import Image
fr = []
for i in range(NF):
    im = Image.open(out / f'pose-{i}/render.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (73, 87, 85, 255)); bg.alpha_composite(im); fr.append(bg.convert('RGB'))
fr[0].save(out / 'poses.gif', save_all=True, append_images=fr[1:], duration=110, loop=0)
W, H = fr[0].size; sh = Image.new('RGB', (W * 4, H * ((NF + 3) // 4)))
for i, f in enumerate(fr): sh.paste(f, ((i % 4) * W, (i // 4) * H))
sh.save(out / 'poses.png'); print(f'proprig: {NF} poses rendered - look at {out / "poses.gif"}; then propanim.py {spec_p.name} (it says the cost)')
