"""A character's attacks made to work together - free, on the rig's GLB, no drawing. Each command reads the spec's "rig_glb" (or
<character>/rig/rig.glb), writes a copy with the clip changed or added (<character>/rig/rig-<tag>.glb), and prints the spec's new
"rig_glb" line. Render (`charpipe.py render --only ...`) and LOOK after each.

    python motion.py ground SPEC.json downward [backhand ...]
        the lower foot on the ground in every frame: a Mixamo clip carried onto a child's rig stood 8-15 cm in the air, and bobbed
    python motion.py plant SPEC.json inward [outward ...]
        the feet held where the clip's first frame has them (the hips and legs held; the hips' turn handed to the spine, so all
        above the waist moves as before) - for a swing whose legs jump from stance to stance
    python motion.py link SPEC.json downward@1.40 backhand@0.3-2.0 NAME [--blend 0.4]
        clip B started from the pose clip A is in at that time, the difference to B's own pose fading out over --blend seconds
        (inside B's wind-up: its stroke is B's own). The way games join one move to the next; NAME is the new clip
    python motion.py blade SPEC.json downward --stroke 0.75-1.25 [--bend 0.55] [--lag 0.9] [--max-turn 100]
        an axe's chop made a sword's cut: the forward bend cut to --bend of itself (spine and hips, the thighs turned back so the
        feet stay); the wrist turned so the blade runs on from the arm through the stroke, and (--lag) trails the hand early in it
        and catches up at the hit - its tip on an arc round the shoulder
    python motion.py join SPEC.json NAME downward:0:2.26 bh:0:2.49 ...
        clips one after another as one (to render a whole combo smoothly, 24 a second, and look at the joins)
    python motion.py preset SPEC.json rain-girl-combo [--fbx DIR]
        a COMBO PRESET (presets/<name>.json): the Mixamo moves it names carried onto the character's rig from the FBX files the user
        downloaded (in DIR, or beside the spec), then the same changes with the same numbers, and its actions put in the spec (each
        keeping a "hold" the spec already gives it). A preset keeps only the changes - never the moves: Mixamo's may be used, not
        handed on. Missing a file, it says which move to download and how

The held thing points along the hand bone as the renderer holds it (the action's "grip", or the kind's default: an umbrella's
[0, 0, -90] - along the hand's x). Never put a Mixamo file - or a rig with its motion in - in a public repository."""
import json, struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Rot
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import charpipe as CP          # noqa: E402
from addclip import write as write_clip   # noqa: E402
FPS = 30


class Rig:
    """a glTF rig's clips sampled the way the renderer plays them (linear; turns by the shorter way), and its bones' places in the world"""
    def __init__(s, f):
        b = Path(f).read_bytes(); n = struct.unpack('<I', b[12:16])[0]; s.j = json.loads(b[20:20 + n]); s.bin0 = 20 + n + 8; s.b = b; s.path = Path(f)
        s.names = [x.get('name') for x in s.j['nodes']]; s.parent = {c: i for i, x in enumerate(s.j['nodes']) for c in x.get('children', [])}
        s._clips = {}

    def read(s, i):
        a = s.j['accessors'][i]; v = s.j['bufferViews'][a['bufferView']]; k = {'VEC4': 4, 'VEC3': 3, 'SCALAR': 1}[a['type']]
        o = s.bin0 + v.get('byteOffset', 0) + a.get('byteOffset', 0); return np.frombuffer(s.b[o:o + 4 * a['count'] * k], np.float32).reshape(a['count'], k).astype(float)

    def anim(s, name):
        a = [x for x in s.j.get('animations', []) if x['name'] == name]
        if not a: sys.exit(f'motion: no clip "{name}" in {s.path.name} ({", ".join(x["name"] for x in s.j.get("animations", []))})')
        return a[0]

    def clip(s, name):
        if name not in s._clips:
            a = s.anim(name); s._clips[name] = {(c['target']['node'], c['target']['path']): (s.read(a['samplers'][c['sampler']]['input'])[:, 0], s.read(a['samplers'][c['sampler']]['output'])) for c in a['channels']}
        return s._clips[name]

    def duration(s, name): return max(float(t[-1]) for t, _ in s.clip(name).values())

    def trs(s, i, ch, t):
        x = s.j['nodes'][i]; T = np.array(x.get('translation', [0, 0, 0]), float); R = np.array(x.get('rotation', [0, 0, 0, 1]), float); S = np.array(x.get('scale', [1, 1, 1]), float)
        def at(path, dflt):
            if (i, path) not in ch: return dflt
            tt, v = ch[(i, path)]; k = min(max(np.searchsorted(tt, t), 1), len(tt) - 1); u = np.clip((t - tt[k - 1]) / max(1e-9, tt[k] - tt[k - 1]), 0, 1)
            a, b = v[k - 1], v[k].copy()
            if path == 'rotation' and np.dot(a, b) < 0: b = -b
            r = a * (1 - u) + b * u; return r / np.linalg.norm(r) if path == 'rotation' else r
        return at('translation', T), Rot.from_quat(at('rotation', R)), at('scale', S)

    def local(s, i, ch, t):
        T, R, S = s.trs(i, ch, t); M = np.eye(4); M[:3, :3] = R.as_matrix() * S; M[:3, 3] = T; return M

    def world(s, i, ch, t):
        M = s.local(i, ch, t)
        while i in s.parent: i = s.parent[i]; M = s.local(i, ch, t) @ M
        return M

    def pos(s, bone, ch, t): return s.world(s.names.index(bone), ch, t)[:3, 3]

    def wrot(s, i, ch, t): M = s.world(i, ch, t)[:3, :3]; return Rot.from_matrix(M / np.linalg.norm(M, axis=0))

    def patch(s, name, fn):
        """each rotation channel of a clip through fn(bone, times, quats) -> new quats (or None: as it is); returns the new GLB's bytes"""
        b = bytearray(s.b); a = s.anim(name)
        for c in a['channels']:
            if c['target']['path'] != 'rotation': continue
            sm = a['samplers'][c['sampler']]; t = s.read(sm['input'])[:, 0]; out = fn(s.names[c['target']['node']], t, s.read(sm['output']))
            if out is None: continue
            out = np.array(out, float)
            for k in range(1, len(out)):
                if np.dot(out[k], out[k - 1]) < 0: out[k] = -out[k]
            acc = s.j['accessors'][sm['output']]; v = s.j['bufferViews'][acc['bufferView']]; o = s.bin0 + v.get('byteOffset', 0) + acc.get('byteOffset', 0)
            b[o:o + out.size * 4] = out.astype(np.float32).tobytes()
        return bytes(b)

    def patch_hips(s, name, fn):
        """the hips' place in each key of a clip through fn(times, places) -> new places; returns the new GLB's bytes"""
        b = bytearray(s.b); a = s.anim(name); hp = s.names.index('Hips')
        for c in a['channels']:
            if c['target']['node'] != hp or c['target']['path'] != 'translation': continue
            sm = a['samplers'][c['sampler']]; out = np.array(fn(s.read(sm['input'])[:, 0], s.read(sm['output'])), float)
            acc = s.j['accessors'][sm['output']]; v = s.j['bufferViews'][acc['bufferView']]; o = s.bin0 + v.get('byteOffset', 0) + acc.get('byteOffset', 0)
            b[o:o + out.size * 4] = out.astype(np.float32).tobytes()
        return bytes(b)


def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def stand_height(r):
    """how high the ankles are standing: the lower one in the first frame of the idle (or the walk, or the first clip)"""
    names = [a['name'] for a in r.j.get('animations', [])]; c = next((n for n in ('idle', 'idle_spritecast', 'walk') if n in names), names[0])
    ch = r.clip(c); return min(r.pos('LeftFoot', ch, 0)[1], r.pos('RightFoot', ch, 0)[1])


def ground(r, clips):
    data = r.b
    for c in clips:
        rr = Rig.__new__(Rig); rr.__dict__.update(r.__dict__); rr.b = data; rr._clips = {}
        ch = rr.clip(c); G = stand_height(rr); hp = rr.names.index('Hips'); A = rr.world(rr.parent[hp], ch, 0)[:3, :3]; Ai = np.linalg.inv(A); offs = []
        def fn(t, T):
            out = T.copy()
            for k, tt in enumerate(t):
                dy = min(rr.pos('LeftFoot', ch, tt)[1], rr.pos('RightFoot', ch, tt)[1]) - G; offs.append(dy); out[k] = T[k] - Ai @ np.array([0, dy, 0])
            return out
        data = rr.patch_hips(c, fn); print(f'motion: ground {c}: the lower foot was {min(offs):+.3f} to {max(offs):+.3f} off the ground - now on it')
    return data


def plant(r, clips):
    legs = [s + p for s in ('Left', 'Right') for p in ('UpLeg', 'Leg', 'Foot', 'ToeBase')]; data = r.b
    for c in clips:
        rr = Rig.__new__(Rig); rr.__dict__.update(r.__dict__); rr.b = data; rr._clips = {}
        a = rr.anim(c); ch = {(rr.names[x['target']['node']], x['target']['path']): a['samplers'][x['sampler']] for x in a['channels']}
        H = rr.read(ch[('Hips', 'rotation')]['output']); h0 = Rot.from_quat(H[0])
        if not np.allclose(rr.read(ch[('Hips', 'rotation')]['input']), rr.read(ch[('Spine', 'rotation')]['input'])): sys.exit('motion plant: the hips and the spine are keyed at different times')
        turn = max(np.degrees((h0.inv() * Rot.from_quat(q)).magnitude()) for q in H)
        def fn(bone, t, Q):
            if bone == 'Spine': return [(h0.inv() * Rot.from_quat(H[k]) * Rot.from_quat(Q[k])).as_quat() for k in range(len(Q))]
            if bone == 'Hips' or bone in legs: return np.tile(Q[0], (len(Q), 1))
        data = rr.patch(c, fn); rr.b = data; data = rr.patch_hips(c, lambda t, T: np.tile(T[0], (len(T), 1)))
        print(f'motion: plant {c}: feet held as in its first frame; the hips turned up to {turn:.0f} degrees - now the spine does')
    return data


def link(r, a_at, b_rng, name, blend):
    A, ta = a_at.split('@'); ta = float(ta); B, rng = b_rng.split('@'); t0, t1 = [float(x) for x in rng.split('-')]
    ca, cb = r.clip(A), r.clip(B); us = np.arange(0, t1 - t0 + 1e-6, 1 / FPS); bones = {}
    w = lambda u: ease(u / blend)
    for (i, path) in cb:
        if path != 'rotation': continue
        ov = (r.trs(i, cb, t0)[1].inv() * r.trs(i, ca, ta)[1]).as_rotvec()       # B's first pose -> A's, in the bone's own frame
        bones[r.names[i]] = np.array([(r.trs(i, cb, t0 + u)[1] * Rot.from_rotvec((1 - w(u)) * ov)).as_quat() for u in us]).ravel()
    hp = r.names.index('Hips'); dT = r.trs(hp, ca, ta)[0] - r.trs(hp, cb, t0)[0]
    hips = np.array([r.trs(hp, cb, t0 + u)[0] + (1 - w(u)) * dT for u in us]).ravel()
    tmp = r.path.with_name(r.path.stem + f'.{name}.tmp.glb'); write_clip(str(r.path), str(tmp), name, {'n': len(us), 'duration': float(us[-1]), 'bones': bones, 'hips': hips}, fps=FPS)
    data = tmp.read_bytes(); tmp.unlink()
    print(f'motion: link {name}: {A} at {ta:.2f} s -> {B} {t0:.2f}-{t1:.2f} s, the difference gone in {blend:.2f} s ({len(us)} keys)')
    return data


def grip_axis(s, clip):
    """the way the held thing points in the hand bone's frame: +y of the thing, turned by the action's grip (three's Euler, XYZ)"""
    act = next((a for a in s['actions'].values() if a.get('clip') == clip and a.get('hold')), None) if isinstance(s.get('actions'), dict) else None
    h = (act or {}).get('hold') or {}; h = {'kind': h} if isinstance(h, str) else h
    g = h.get('grip') or ([0, 0, -90] if h.get('kind', 'umbrella') == 'umbrella' else [0, 0, 0] if h.get('kind') in ('pistol', 'watergun') else [0, 0, 90])
    return Rot.from_euler('XYZ', g, degrees=True).apply([0, 1, 0])


def blade(r, s, clip, stroke, bend, lag, maxdeg):
    S0, S1 = stroke; ax = grip_axis(s, clip)
    a = r.anim(clip); chn = {(r.names[c['target']['node']], c['target']['path']): a['samplers'][c['sampler']] for c in a['channels']}
    HQ = r.read(chn[('Hips', 'rotation')]['output']); h0 = Rot.from_quat(HQ[0]); Hn = [h0 * Rot.from_rotvec(bend * (h0.inv() * Rot.from_quat(q)).as_rotvec()) for q in HQ]
    def less(bone, t, Q):
        if bone in ('Spine', 'Spine1', 'Spine2'): q0 = Rot.from_quat(Q[0]); return [(q0 * Rot.from_rotvec(bend * (q0.inv() * Rot.from_quat(q)).as_rotvec())).as_quat() for q in Q]
        if bone == 'Hips': return [q.as_quat() for q in Hn]
        if bone in ('LeftUpLeg', 'RightUpLeg'): return [(Hn[k].inv() * Rot.from_quat(HQ[k]) * Rot.from_quat(Q[k])).as_quat() for k in range(len(Q))]
    rr = Rig.__new__(Rig); rr.__dict__.update(r.__dict__); rr.b = r.patch(clip, less); rr._clips = {}
    ch = rr.clip(clip); hi = rr.names.index('RightHand'); pi = rr.parent[hi]; turned = []
    def W(t): return ease(min((t - (S0 - 0.25)) / 0.25, ((S1 + 0.3) - t) / 0.3))
    def unit(v): n = np.linalg.norm(v); return v / n if n > 1e-9 else v
    def wrist(bone, t, Q):
        if bone != 'RightHand': return None
        out = []
        for k, tt in enumerate(t):
            cur = unit(rr.wrot(hi, ch, tt).apply(ax)); arm = unit(rr.pos('RightHand', ch, tt) - rr.pos('RightArm', ch, tt))
            v = rr.pos('RightHand', ch, tt + 0.02) - rr.pos('RightHand', ch, tt - 0.02); p = np.clip((tt - (S0 - 0.15)) / (S1 - S0 + 0.15), 0, 1)
            aim = unit(arm - lag * (1 - p) ** 1.5 * unit(v)) if np.linalg.norm(v) > 1e-4 else arm       # the blade trails the hand early in the stroke
            want = unit((1 - W(tt)) * cur + W(tt) * aim); c_ = np.cross(cur, want); ang = min(np.arctan2(np.linalg.norm(c_), np.dot(cur, want)), np.radians(maxdeg))
            Rw = Rot.from_rotvec(unit(c_) * ang) if np.linalg.norm(c_) > 1e-6 else Rot.identity(); Pw = rr.wrot(pi, ch, tt)
            out.append((Pw.inv() * Rw * Pw * Rot.from_quat(Q[k])).as_quat()); turned.append(np.degrees(ang))
        return out
    data = rr.patch(clip, wrist)
    print(f'motion: blade {clip}: bend x{bend:.2f}; the wrist turned up to {max(turned):.0f} degrees through {S0:.2f}-{S1:.2f} s (lag {lag:.2f})')
    return data


def join(r, name, segs):
    frames = []
    for k, sg in enumerate(segs):
        c, t0, t1 = sg.split(':'); ts = np.arange(float(t0), float(t1) + 1e-6, 1 / FPS); frames += [(r.clip(c), t) for t in (ts if k == 0 else ts[1:])]
    first = r.clip(segs[0].split(':')[0]); hp = r.names.index('Hips')
    bones = {r.names[i]: np.array([r.trs(i, ch, t)[1].as_quat() for ch, t in frames]).ravel() for (i, p) in first if p == 'rotation'}
    hips = np.array([r.trs(hp, ch, t)[0] for ch, t in frames]).ravel(); dur = (len(frames) - 1) / FPS
    tmp = r.path.with_name(r.path.stem + f'.{name}.tmp.glb'); write_clip(str(r.path), str(tmp), name, {'n': len(frames), 'duration': dur, 'bones': bones, 'hips': hips}, fps=FPS)
    data = tmp.read_bytes(); tmp.unlink(); print(f'motion: join {name}: {" + ".join(segs)} = {dur:.2f} s'); return data


def run_steps(base, steps, s, work):
    """the steps one after another on the base rig (each from the last one's result, through a file in `work`) -> the final GLB's path.
    A step: {"op": "ground"|"plant", "clips": [...]} | {"op": "blade", "clip", "stroke": [t0, t1], "bend", "lag", "max_turn"} |
    {"op": "link", "a", "ta", "b", "t0", "t1", "name", "blend"} (to build a rig from a list of steps kept in a file)"""
    work = Path(work); work.mkdir(parents=True, exist_ok=True); cur = Path(base)
    for k, st in enumerate(steps):
        r = Rig(cur); op = st.get('op')
        if op == 'ground': data = ground(r, st['clips'])
        elif op == 'plant': data = plant(r, st['clips'])
        elif op == 'blade': data = blade(r, s, st['clip'], [float(x) for x in st['stroke']], float(st.get('bend', 0.55)), float(st.get('lag', 0.9)), float(st.get('max_turn', 100)))
        elif op == 'link': data = link(r, f"{st['a']}@{float(st['ta'])}", f"{st['b']}@{float(st['t0'])}-{float(st['t1'])}", st['name'], float(st.get('blend', 0.4)))
        else: raise ValueError(f'motion: no step "{op}"')
        cur = work / f'step-{k}.glb'; cur.write_bytes(data)
    return cur


def preset(spec, name, fbx_dir=''):
    """a combo preset applied to a character: its moves carried on from the user's FBX files, its steps run, its actions in the spec"""
    from addclip import retarget
    pf = Path(name) if name.endswith('.json') else HERE.parent / 'presets' / f'{name}.json'
    if not pf.exists(): sys.exit(f'motion preset: no preset "{name}" - there are: ' + ', '.join(p.stem for p in sorted((HERE.parent / 'presets').glob('*.json'))))
    P = json.loads(pf.read_text()); s, d = CP.load(spec); sp = Path(spec).resolve()
    glb = Path(s.get('rig_glb') or d / 'rig/rig.glb'); glb = glb if glb.is_absolute() else (sp.parent / glb if (sp.parent / glb).exists() else glb.resolve())
    dirs = [Path(fbx_dir)] if fbx_dir else []; dirs += [sp.parent, Path.cwd()]; miss = []
    found = {n['clip']: next((q / n['file'] for q in dirs if (q / n['file']).exists()), None) for n in P['needs']}
    for n in P['needs']:
        if not found[n['clip']]: miss.append(f'  - "{n["mixamo"]}" -> {n["file"]}' + (f'\n    {n["url"]}' if n.get('url') else ''))
    if miss: sys.exit(f'motion preset {P["name"]}: download these from Mixamo first (they cannot come with SpriteCast):\n' + '\n'.join(miss) + f'\n  how: {P["download"]}\n  then put them beside the spec (or --fbx DIR)')
    work = d / 'rig' / f'preset-{P["name"]}'; work.mkdir(parents=True, exist_ok=True); cur = glb
    for n in P['needs']:          # (each move onto the rig the last one left)
        r = retarget(cur, found[n['clip']].resolve(), head_down=s['head_up']); nxt = work / f'clip-{n["clip"]}.glb'; write_clip(cur, nxt, n['clip'], r); cur = nxt
        print(f'motion: preset {P["name"]}: "{n["mixamo"]}" carried on as "{n["clip"]}" ({r["duration"]:.2f} s)')
    final = run_steps(cur, P['steps'], s, work); out = d / 'rig' / f'rig-{P["name"]}.glb'; out.write_bytes(final.read_bytes())
    raw = json.loads(sp.read_text()); raw['rig_glb'] = str(out.resolve().relative_to(sp.parent)) if out.resolve().is_relative_to(sp.parent) else str(out)
    acts = raw.setdefault('actions', [])
    for a in P['actions']:
        a = dict(a); old = next((x for x in acts if isinstance(x, dict) and x.get('name') == a['name']), None)
        a['hold'] = (old or {}).get('hold') or dict(P.get('hold', {}))
        if old: acts[acts.index(old)] = a
        else: acts.append(a)
    sp.write_text(json.dumps(raw, indent=1, ensure_ascii=False) + '\n')
    print(f'motion: preset {P["name"]}: {out}  - the spec\'s "rig_glb" and actions {", ".join(a["name"] for a in P["actions"])} written')
    print(f'  next (free): charpipe.py render {spec} --only {",".join(a["name"] for a in P["actions"])} - LOOK; then pixelart.py (paid: it says the cost first)')
    if P.get('effects'): print(f'  effects round it: {P["effects"]}')


def main(argv):
    if len(argv) >= 3 and argv[0] == 'preset':
        rest = argv[3:]; fb = rest[rest.index('--fbx') + 1] if '--fbx' in rest else ''
        return preset(argv[1], argv[2], fb)
    if len(argv) < 3 or argv[0] not in ('ground', 'plant', 'link', 'blade', 'join'): sys.exit(__doc__)
    cmd, spec = argv[0], argv[1]; s, d = CP.load(spec); glb = Path(s.get('rig_glb') or d / 'rig/rig.glb')
    if not glb.is_absolute(): glb = (Path(spec).resolve().parent / glb) if not glb.exists() else glb.resolve()
    r = Rig(glb); rest = argv[2:]
    def opt(k, dflt):
        if k in rest: i = rest.index(k); v = rest[i + 1]; del rest[i:i + 2]; return type(dflt)(v)
        return dflt
    out_ = opt('--out', '')
    if cmd == 'ground': data, tag = ground(r, rest), 'ground'
    elif cmd == 'plant': data, tag = plant(r, rest), 'plant'
    elif cmd == 'link':
        blend = opt('--blend', 0.4); data, tag = link(r, rest[0], rest[1], rest[2], blend), rest[2]
    elif cmd == 'blade':
        st = opt('--stroke', ''); bend = opt('--bend', 0.55); lag = opt('--lag', 0.9); mx = opt('--max-turn', 100.0)
        if not st: sys.exit('motion blade: --stroke T0-T1 (when the stroke is fastest - render the clip and look, or watch the hand)')
        data, tag = blade(r, s, rest[0], [float(x) for x in st.split('-')], bend, lag, mx), rest[0] + '-blade'
    else: data, tag = join(r, rest[0], rest[1:]), rest[0]
    out = Path(out_) if out_ else d / f'rig/rig-{tag}.glb'; out.write_bytes(data)
    print(f'  -> {out}\n  in the spec: "rig_glb": "{out.resolve().relative_to(Path(spec).resolve().parent) if out.resolve().is_relative_to(Path(spec).resolve().parent) else out}"')


if __name__ == '__main__': main(sys.argv[1:])
