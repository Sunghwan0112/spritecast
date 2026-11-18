"""SpriteCast's own standing idle, put into a character's rig as one more clip ("idle_spritecast") - made here from nothing, no one's
animation copied (a Mixamo idle could not be shipped: its files may not be handed on). Free; `charpipe.py render` adds it by itself.

    python idleclip.py RIG.glb OUT.glb [--head-down 24] [--seconds 4]

The stand: the feet side by side, hip-width apart, the toes a little out; the shoulders let down, the arms hanging close by the
body, the elbows a little bent. The motion, a seamless loop of 4 s: two breaths (the chest lifts), the hips moving from foot to foot
by 0.4 % of the height and dipping as the weight arrives, the pelvis tipping and the chest balancing it, the head tilting a little,
the arms swinging a little with the body. The arms and shoulders were set by looking at a Mixamo "Standing Idle" carried over by
addclip.py (the same to 1-3 % of the height); its stand on one foot was not kept (see FEET below); the motion is all made here.

How: every bone is given the direction it should point at each moment, in the body's own frame (right: one thigh to the other, up: the
hips to the head), and the rig is turned to it top-down from the hips - so it fits any rig with Mixamo's bone names (Tripo's), whatever
its rest pose. The renderer lifts every clip's head by the spec's "head_up" (a Tripo walk looks down): this clip is made level, so
that lift is taken off here (`--head-down`, the spec's head_up), as addclip.py does."""
import json, struct, sys
import numpy as np

CLIP = 'idle_spritecast'


# --- the GLB ---------------------------------------------------------------------------------------------------------------------
def load(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); o = 20 + n
    bl = struct.unpack('<I', b[o:o + 4])[0]; return j, bytearray(b[o + 8:o + 8 + bl])


def write(j, bin_, clip, path):
    """the GLB with one more animation (one of the same name replaced)"""
    name, grid, out = clip; j = json.loads(json.dumps(j)); bin_ = bytearray(bin_)
    j['animations'] = [a for a in j.get('animations', []) if a.get('name') != name]
    def add(arr, typ):
        while len(bin_) % 4: bin_.append(0)
        arr = np.ascontiguousarray(arr, np.float32); off = len(bin_); bin_.extend(arr.tobytes())
        j['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes})
        a = {'bufferView': len(j['bufferViews']) - 1, 'componentType': 5126, 'count': len(arr), 'type': typ}
        if typ == 'SCALAR': a['min'] = [float(arr.min())]; a['max'] = [float(arr.max())]
        j['accessors'].append(a); return len(j['accessors']) - 1
    ti = add(grid, 'SCALAR'); an = {'name': name, 'channels': [], 'samplers': []}
    for (node, path_), v in out.items():
        if path_ == 'rotation':          # the same turn has two signs: keep to the one nearer the frame before
            v = v.copy()
            for k in range(1, len(v)):
                if (v[k] * v[k - 1]).sum() < 0: v[k] = -v[k]
        an['samplers'].append({'input': ti, 'output': add(v, 'VEC4' if path_ == 'rotation' else 'VEC3'), 'interpolation': 'LINEAR'})
        an['channels'].append({'sampler': len(an['samplers']) - 1, 'target': {'node': node, 'path': path_}})
    j['animations'].append(an)
    while len(bin_) % 4: bin_.append(0)
    j['buffers'][0]['byteLength'] = len(bin_)
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_))); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bin_), 0x004E4942)); f.write(bin_)


# --- turns (quaternions x, y, z, w) and the skeleton ---------------------------------------------------------------------------
def qmul(a, b):
    x1, y1, z1, w1 = np.moveaxis(a, -1, 0); x2, y2, z2, w2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)
def qinv(a): return a * np.array([-1, -1, -1, 1.0])
def qrot(q, v):
    p = np.concatenate([v, np.zeros(v.shape[:-1] + (1,))], -1); return qmul(qmul(q, p), qinv(q))[..., :3]
def q_of(M):
    import scipy.spatial.transform as T; return T.Rotation.from_matrix(M).as_quat()
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v, axis=-1, keepdims=True)


def arc(a, b):
    """the shortest turn taking directions a to b (N x 3 each)"""
    a, b = unit(a), unit(b); q = np.concatenate([np.cross(a, b), 1 + (a * b).sum(-1, keepdims=True)], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def rot_axis(axis, ang):
    """turns about a body axis (0 right, 1 up, 2 forward), one per angle"""
    c, s = np.cos(ang), np.sin(ang); M = np.tile(np.eye(3), (len(ang), 1, 1)); i, k = [(1, 2), (2, 0), (0, 1)][axis]
    M[:, i, i] = c; M[:, i, k] = -s; M[:, k, i] = s; M[:, k, k] = c; return M


def skeleton(j):
    par = {c: i for i, n in enumerate(j['nodes']) for c in n.get('children', [])}
    def mat(n):
        t = np.array(n.get('translation', [0, 0, 0]), float); r = np.array(n.get('rotation', [0, 0, 0, 1]), float); s = np.array(n.get('scale', [1, 1, 1]), float)
        import scipy.spatial.transform as T; M = np.eye(4); M[:3, :3] = T.Rotation.from_quat(r).as_matrix() * s; M[:3, 3] = t; return M
    def world(i):
        M = np.eye(4)
        while i is not None: M = mat(j['nodes'][i]) @ M; i = par.get(i)
        return M
    return par, world


def make(j, T=4.0, head_down=24.0):
    N = int(round(T * 30)) + 1; t = np.linspace(0, T, N); ph = 2 * np.pi * t / T
    par, world = skeleton(j); idx = {n.get('name'): i for i, n in enumerate(j['nodes'])}
    joints = [j['nodes'][i]['name'] for i in j['skins'][0]['joints']]
    need = ['Hips', 'Head', 'LeftUpLeg', 'RightUpLeg', 'LeftFoot', 'RightFoot', 'LeftToeBase', 'LeftArm', 'RightArm']
    if any(n not in idx for n in need): raise ValueError('idleclip: the rig has not the bones of Mixamo\'s names (Hips, LeftUpLeg, ...)')
    wrot = lambda i: q_of(world(i)[:3, :3] / np.linalg.norm(world(i)[:3, :3], axis=0)) if i is not None else np.array([0, 0, 0, 1.0])
    P0 = {n: world(idx[n])[:3, 3] for n in joints}
    up = unit(P0['Head'] - P0['Hips']); right = P0['RightUpLeg'] - P0['LeftUpLeg']; right = unit(right - (right @ up) * up)
    F = np.stack([right, up, np.cross(right, up)], 1)                                    # the body's frame: columns right, up, forward
    H = P0['Head'][1] - P0['LeftFoot'][1]                                                # the figure's height, near enough
    # the motion (body frame)
    sway = 0.004 * H * np.sin(ph); bob = -0.0015 * H * (1 - np.cos(2 * ph)) / 2
    breath = np.sin(2 * ph + 0.6); hip_roll = np.radians(1.2) * np.sin(ph); chest_roll = -np.radians(1.0) * np.sin(ph + 0.4)
    chest_pitch = np.radians(1.2) * breath; head_roll = np.radians(2.5) * np.sin(ph + 1.2); head_pitch = np.radians(1.5) * np.sin(ph + 0.3)
    arm_swing = np.radians(2.5) * np.sin(ph + 0.9)          # (every term whole cycles of T: the loop has no seam)
    def turned(v, *mats):
        v = np.tile(unit(v), (N, 1))
        for M in mats: v = np.einsum('nij,nj->ni', M, v)
        return v @ F.T
    Rhip = rot_axis(2, hip_roll); Rch = rot_axis(2, hip_roll + chest_roll) @ rot_axis(0, -chest_pitch); Rhd = Rch @ rot_axis(2, head_roll) @ rot_axis(0, head_pitch)
    swingL, swingR = rot_axis(0, arm_swing), rot_axis(0, -arm_swing)
    want = {
        'Spine': turned([0, 1, 0], Rhip), 'Spine1': turned([0, 1, 0], rot_axis(2, hip_roll + chest_roll * 0.5)), 'Spine2': turned([0.03, 1, -0.03], Rch),
        'Neck': turned([0.04, 1, -0.12], Rch), 'Head': turned([0.04, 1, -0.08], Rhd),
        'LeftShoulder': turned([-0.9, -0.43, -0.04], Rch), 'RightShoulder': turned([0.89, -0.45, -0.09], Rch),
        'LeftArm': turned([-0.2, -0.98, -0.05], Rch, swingL), 'RightArm': turned([0.2, -0.98, 0.04], Rch, swingR),
        'LeftForeArm': turned([-0.13, -0.98, -0.18], Rch, swingL), 'RightForeArm': turned([0.09, -0.99, -0.1], Rch, swingR),
        'LeftHand': turned([-0.2, -0.85, -0.45], Rch, swingL), 'RightHand': turned([0.33, -0.85, -0.4], Rch, swingR),
    }
    toe = P0['LeftToeBase'] - P0['LeftFoot']; toe[1] = 0; toe = unit(toe)          # (the head-up lift taken off, toward where the toes point)
    for nm, a in (('Neck', 0.4 * head_down), ('Head', head_down)):
        a = np.radians(a); want[nm] = unit(want[nm] * np.cos(a) + toe[None] * np.sin(a))
    # the legs: the feet planted, the knees where a relaxed stand has them, moving half as far as the hips
    hip_pos = P0['Hips'][None] + np.stack([sway, bob, np.zeros(N)], 1) @ F.T
    # (the feet side by side, as far apart as the hips - not one foot back: with one back, the figure seen from the side of the held
    # thing's hand came out a fifth thinner than from the other side, the legs one behind the other)
    FEET = {'Left': [-0.072, -0.588, -0.045], 'Right': [0.072, -0.588, -0.045]}; KNEES = {'Left': [-0.07, -0.294, -0.055], 'Right': [0.07, -0.294, -0.055]}
    TOES = {'Left': [-0.26, -0.76, -0.6], 'Right': [0.26, -0.76, -0.6]}
    Rh = np.einsum('ij,njk,kl->nil', F, Rhip, F.T)
    for side in ('Left', 'Right'):
        hipj = hip_pos + np.einsum('nij,j->ni', Rh, P0[f'{side}UpLeg'] - P0['Hips'])
        foot = P0['Hips'] + F @ (np.array(FEET[side]) * H); knee = P0['Hips'][None] + (F @ (np.array(KNEES[side]) * H))[None] + 0.5 * (hip_pos - P0['Hips'][None])
        want[f'{side}UpLeg'] = knee - hipj; want[f'{side}Leg'] = foot[None] - knee; want[f'{side}Foot'] = np.tile(F @ unit(TOES[side]), (N, 1))
    child = {'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head', 'Head': 'HeadTop_End', 'LeftShoulder': 'LeftArm', 'RightShoulder': 'RightArm',
             'LeftArm': 'LeftForeArm', 'RightArm': 'RightForeArm', 'LeftForeArm': 'LeftHand', 'RightForeArm': 'RightHand', 'LeftHand': 'LeftHandMiddle1', 'RightHand': 'RightHandMiddle1',
             'LeftUpLeg': 'LeftLeg', 'RightUpLeg': 'RightLeg', 'LeftLeg': 'LeftFoot', 'RightLeg': 'RightFoot', 'LeftFoot': 'LeftToeBase', 'RightFoot': 'RightToeBase'}
    W = {}; out = {}
    for nm in joints:          # parents first (a skin's joints are listed so)
        i = idx[nm]; p = par.get(i); pn = j['nodes'][p]['name'] if p is not None else None
        pw = W[pn] if pn in W else np.tile(wrot(p), (N, 1))
        guess = qmul(pw, np.tile(np.array(j['nodes'][i].get('rotation', [0, 0, 0, 1]), float), (N, 1)))
        if nm == 'Hips': w = qmul(q_of(Rh), guess)
        elif nm in want and child.get(nm) in idx:
            off = np.array(j['nodes'][idx[child[nm]]].get('translation', [0, 0, 0]), float)
            w = qmul(arc(qrot(guess, np.tile(off, (N, 1))), want[nm]), guess)
        else: w = guess
        W[nm] = w; loc = qmul(qinv(pw), w); out[(i, 'rotation')] = loc / np.linalg.norm(loc, axis=1, keepdims=True)
    hp = par.get(idx['Hips']); Mt = world(hp) if hp is not None else np.eye(4)
    out[(idx['Hips'], 'translation')] = np.array(j['nodes'][idx['Hips']].get('translation', [0, 0, 0]), float) + (np.linalg.inv(Mt[:3, :3]) @ (hip_pos - P0['Hips'][None]).T).T
    return CLIP, t, out


def add(rig, out, head_down=24.0, seconds=4.0):
    j, b = load(rig); write(j, b, make(j, seconds, head_down), out)


if __name__ == '__main__':
    a = sys.argv[1:]; hd = float(a[a.index('--head-down') + 1]) if '--head-down' in a else 24.0; T = float(a[a.index('--seconds') + 1]) if '--seconds' in a else 4.0
    add(a[0], a[1], hd, T); print(f'idleclip: {a[1]}  "{CLIP}" {T:g} s')
