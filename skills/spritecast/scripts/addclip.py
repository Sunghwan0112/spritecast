"""An animation from an FBX (Mixamo's "without skin" download, any skeleton with the same bone names) put into a character's rig
as one more clip - so `charpipe.py render --only NAME`, the depth pass and pixelart.py use it like the clips the rig came with.
    python addclip.py SPEC.json Throw.fbx throw                -> <character>/rig/rig-<name>.glb  (give it to the spec as "rig_glb"
                                                                  and add the action; this prints both lines)
How: the FBX is read in the browser (three's FBXLoader, in vendor/), its motion carried over bone by bone:
  a bone's turn away from ITS rest pose, in world space, is applied to the rig's bone from the rig's rest pose - after the rig's
  rest pose has been turned to the FBX's (Mixamo rests in a T-pose, a rig made from a drawing in an A-pose: without that the arms
  hang 40 degrees low all through). The hips' travel is scaled by the two skeletons' hip heights.
Sampled at 30 a second and written into a copy of the rig's GLB as a new animation.
    python addclip.py SPEC.json Throw.fbx throw --clear-head 40   for a big-headed character: a hand raised past the ear swings its arm
                                                                  out by up to 40 degrees, so it does not go into the head"""
import base64, json, struct, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; REPO = HERE
sys.path.insert(0, str(REPO))
import charpipe as CP, browser as BROWSER   # noqa: E402

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{"imports": {"three": "./vendor/three/three.module.js", "three/addons/": "./vendor/three/addons/"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
const key = (n) => n.replace(/^mixamorig\d*:?/i, '');
window.retarget = async (rigUrl, fbxUrl, fps, headDown, clearHead) => {
  const g = await new GLTFLoader().loadAsync(rigUrl), fbx = await new FBXLoader().loadAsync(fbxUrl);
  const clip = fbx.animations.sort((a, b) => b.duration - a.duration)[0];
  const T = {}, S = {}; let skel = null;
  g.scene.traverse((o) => { if (o.isBone) T[key(o.name)] = o; if (o.isSkinnedMesh && !skel) skel = o.skeleton; });
  fbx.traverse((o) => { if (o.isBone || o.type === 'Bone') S[key(o.name)] = o; });
  if (skel) skel.pose();                                   // the rig in its rest pose
  g.scene.updateMatrixWorld(true); fbx.updateMatrixWorld(true);
  const names = Object.keys(T).filter((n) => S[n]);
  const wq = (o) => o.getWorldQuaternion(new THREE.Quaternion()), wp = (o) => o.getWorldPosition(new THREE.Vector3());
  // rest: world turns, and each bone's direction (to its first child that both skeletons have)
  const restS = {}, restT = {}, C = {};
  // a bone's direction: to the SAME child in both skeletons (their children come in different orders: the hips' first child was a
  // leg in one and the spine in the other, and the whole body was turned over) - up the spine where there is a choice
  const SPINE = ['Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'HeadTop_End'];
  const child = (n) => { const cs = T[n].children.map((x) => key(x.name)).filter((k) => T[k] && S[k] && S[k].parent === S[n]); return cs.find((k) => SPINE.includes(k)) || cs[0]; };
  const dir = (B, n) => { const c = child(n); return c ? wp(B[c]).sub(wp(B[n])).normalize() : null; };
  for (const n of names) { restS[n] = wq(S[n]); restT[n] = wq(T[n]); }
  const order = names.slice().sort((a, b) => { let da = 0, db = 0; for (let p = T[a]; p; p = p.parent) da++; for (let p = T[b]; p; p = p.parent) db++; return da - db; });
  for (const n of order) {
    const ds = dir(S, n), dt = dir(T, n), par = T[n].parent && key(T[n].parent.name);
    // only the limbs are turned to the FBX's rest (T-pose arms against A-pose arms); what hangs on a limb (hand, fingers, foot)
    // goes with it; the hips, the spine, the neck and the head stand the same in both and are left - the head's "direction" is to
    // a marker on top of the skull that each rig puts somewhere else (it tipped the head 40 degrees back)
    const limb = /(Shoulder|Arm|ForeArm|UpLeg|Leg)$/.test(n);
    C[n] = limb && ds && dt ? new THREE.Quaternion().setFromUnitVectors(dt, ds) : (C[par] && !/^(Hips|Spine\d?|Neck|Head)$/.test(par) ? C[par].clone() : new THREE.Quaternion());
  }
  const hipS0 = wp(S.Hips), hipT0 = wp(T.Hips), ground = (B) => Math.min(...['LeftToeBase', 'RightToeBase', 'LeftFoot', 'RightFoot'].filter((n) => B[n]).map((n) => wp(B[n]).y));
  const ratio = (hipT0.y - ground(T)) / (hipS0.y - ground(S));
  const mixer = new THREE.AnimationMixer(fbx); mixer.clipAction(clip).play();
  const n = Math.max(2, Math.round(clip.duration * fps) + 1), out = { duration: clip.duration, n, bones: {}, hips: [], names: order, ratio,
    facing: { rig: wp(T.LeftUpLeg).sub(wp(T.RightUpLeg)).normalize().toArray(), fbx: wp(S.LeftUpLeg).sub(wp(S.RightUpLeg)).normalize().toArray() } };
  for (const b of order) out.bones[b] = [];
  for (let i = 0; i < n; i++) {
    mixer.setTime(clip.duration * i / (n - 1)); fbx.updateMatrixWorld(true);
    const W = {};
    for (const b of order) {               // parents first: a bone's new world turn, then its local one
      const d = wq(S[b]).multiply(restS[b].clone().invert()); W[b] = d.multiply(C[b]).multiply(restT[b]);
      const par = T[b].parent, pk = par && key(par.name);
      const pw = W[pk] ? W[pk] : (par ? wq(par) : new THREE.Quaternion());
      const l = pw.clone().invert().multiply(W[b]);
      if (headDown && (b === 'Neck' || b === 'Head')) {      // the renderer lifts every clip's head by "head_up" (a Tripo walk looks down); this clip does not need it: taken off here
        const ax = new THREE.Vector3(-1, 0, 0).applyQuaternion(pw.clone().invert()).normalize(); l.premultiply(new THREE.Quaternion().setFromAxisAngle(ax, -(b === 'Neck' ? 0.4 : 0.6) * headDown * Math.PI / 180));
        W[b] = pw.clone().multiply(l);
      }
      out.bones[b].push(l.x, l.y, l.z, l.w);
    }
    const P = hipT0.clone().add(wp(S.Hips).sub(hipS0).multiplyScalar(ratio)); T.Hips.parent.worldToLocal(P); out.hips.push(P.x, P.y, P.z);
    // A BIG HEAD IN THE HAND'S WAY (a character three heads tall: the clip was made for a small head, and a hand raised past the ear
    // goes into the skull): while a hand is above the head's joint its upper arm is swung outward, away from the head, by up to
    // `clearHead` degrees - nothing below that height is changed, and the swing eases in and out with the hand's height. It is the line
    // from the shoulder to the HAND that is swung (the elbow is bent then: the upper arm alone swung out left the hand at the ear).
    if (clearHead && T.Head && T.HeadTop_End) {
      for (const b of order) { const q = out.bones[b]; T[b].quaternion.set(q[q.length - 4], q[q.length - 3], q[q.length - 2], q[q.length - 1]); }
      T.Hips.position.copy(P); g.scene.updateMatrixWorld(true);
      const head = wp(T.Head);
      for (const side of ['Right', 'Left']) {
        const A = T[side + 'Arm'], F = T[side + 'ForeArm'], Hd = T[side + 'Hand']; if (!A || !F || !Hd) continue;
        const sh = wp(A); let t = Math.max(0, Math.min(1, (wp(Hd).y - head.y) / Math.max(1e-6, head.y - sh.y))); t = t * t * (3 - 2 * t); if (t <= 0) continue;          // (eased in over a neck's length: the rig's marker on top of the head is no measure of a big head)
        const arm = wp(Hd).sub(sh).normalize(), outd = sh.clone().sub(head); outd.y = 0; outd.normalize();
        const axis = new THREE.Vector3().crossVectors(arm, outd); if (axis.lengthSq() < 1e-6) continue; axis.normalize();
        const l = wq(A.parent).invert().multiply(new THREE.Quaternion().setFromAxisAngle(axis, t * clearHead * Math.PI / 180).multiply(wq(A)));
        out.bones[side + 'Arm'].splice(-4, 4, l.x, l.y, l.z, l.w); out.spread = Math.max(out.spread || 0, t);
      }
    }
  }
  return out;
};
window.ready = true;
</script></body></html>"""


def retarget(glb, fbx, fps=30, head_down=0, clear_head=0):
    from playwright.sync_api import sync_playwright
    def serve(route):
        p = route.request.url.split('spritecast.local/', 1)[1]
        if p == 'page.html': return route.fulfill(body=PAGE, content_type='text/html')
        if p == 'asset/rig.glb': return route.fulfill(path=str(glb), content_type='model/gltf-binary')
        if p == 'asset/clip.fbx': return route.fulfill(path=str(fbx), content_type='application/octet-stream')
        f = (REPO / p).resolve()
        if not f.exists(): return route.abort()
        route.fulfill(path=str(f), content_type='text/javascript')
    with sync_playwright() as pw:
        br = BROWSER.launch(pw); pg = br.new_page(); logs = []; pg.on('console', lambda m: logs.append(m.text)); pg.on('pageerror', lambda e: logs.append(str(e)))
        pg.route('http://spritecast.local/**', serve); pg.goto('http://spritecast.local/page.html')
        try:
            pg.wait_for_function('window.ready === true', timeout=30000)
            out = pg.evaluate('([a, b, f, h, c]) => window.retarget(a, b, f, h, c)', ['http://spritecast.local/asset/rig.glb', 'http://spritecast.local/asset/clip.fbx', fps, head_down, clear_head])
        except Exception as e: sys.exit(f'addclip: {e}\n' + '\n'.join(logs[-8:]))
        br.close()
    return out


def write(glb, out, name, r, fps=30):
    """the rig's GLB with one more animation: every carried bone's turn, and the hips' place"""
    b = Path(glb).read_bytes(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); bin_ = bytearray(b[20 + n + 8:])
    node = {x.get('name'): i for i, x in enumerate(j['nodes'])}
    def add(arr, typ):
        while len(bin_) % 4: bin_.append(0)
        a = np.asarray(arr, np.float32); off = len(bin_); bin_.extend(a.tobytes())
        j['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': a.nbytes}); acc = {'bufferView': len(j['bufferViews']) - 1, 'componentType': 5126, 'count': len(a), 'type': typ}
        if typ == 'SCALAR': acc['min'], acc['max'] = [float(a.min())], [float(a.max())]
        j['accessors'].append(acc); return len(j['accessors']) - 1
    t = add(np.arange(r['n']) / fps * (r['duration'] * fps / (r['n'] - 1)), 'SCALAR'); samplers, channels = [], []
    for bone, q in r['bones'].items():
        if bone not in node: continue
        q = np.asarray(q, np.float32).reshape(-1, 4)
        for k in range(1, len(q)):                     # the same turn has two signs: keep to the one nearer the frame before
            if (q[k] * q[k - 1]).sum() < 0: q[k] = -q[k]
        samplers.append({'input': t, 'output': add(q, 'VEC4'), 'interpolation': 'LINEAR'}); channels.append({'sampler': len(samplers) - 1, 'target': {'node': node[bone], 'path': 'rotation'}})
    samplers.append({'input': t, 'output': add(np.asarray(r['hips'], np.float32).reshape(-1, 3), 'VEC3'), 'interpolation': 'LINEAR'})
    channels.append({'sampler': len(samplers) - 1, 'target': {'node': node['Hips'], 'path': 'translation'}})
    j['animations'] = [a for a in j.get('animations', []) if a.get('name') != name] + [{'name': name, 'samplers': samplers, 'channels': channels}]
    while len(bin_) % 4: bin_.append(0)
    j['buffers'][0]['byteLength'] = len(bin_); js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    Path(out).write_bytes(b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(bin_)) + b'BIN\x00' + bytes(bin_))


if __name__ == '__main__':
    spec, fbx, name = sys.argv[1:4]; clear = float(sys.argv[sys.argv.index('--clear-head') + 1]) if '--clear-head' in sys.argv else 0.0; s, d = CP.load(spec); glb = Path(s.get('rig_glb') or d / 'rig/rig.glb'); out = d / f'rig/rig-{name}.glb'
    r = retarget(glb, Path(fbx).resolve(), head_down=s['head_up'], clear_head=clear); write(glb, out, name, r)
    if clear: print(f'  --clear-head {clear:g}: the upper arms swung out while a hand is above the head\'s joint' + ('' if r.get('spread') else ' - no hand got that high in this clip'))
    print(f"addclip: {out}  \"{name}\" {r['duration']:.2f} s, {r['n']} samples, {len(r['bones'])} bones carried over, hips x{r['ratio']:.3f}")
    print('  facing (left hip - right hip): rig', [round(x, 2) for x in r['facing']['rig']], ' fbx', [round(x, 2) for x in r['facing']['fbx']])
    print(f'  in the spec: "rig_glb": "{out.relative_to(Path(spec).resolve().parent)}"   and in "actions": {{"name": "{name}", "loop": false}}')
