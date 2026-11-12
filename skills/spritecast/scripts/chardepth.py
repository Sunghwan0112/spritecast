"""For pixelart.py: a depth pass of a character's frames, and the renders of an action whose held thing render_char.html does not know.
render_char.html is patched in memory (the shipped file is not changed) and run through the same clips at the same poses:
    chardepth.py SPEC                  <character>/depth/<clip>-<facing>-<k>.png for WANT (16 bits: red high, green low = distance from
                                       the camera, 8..12 units; blue = the head, i.e. skinned to a head bone)
    chardepth.py SPEC render CLIP      one action in all eight facings: colour, shadow, held/body shots into render/, and its depth -
                                       with a held thing added here ("snowball") and let go at "until" seconds ("auto": when the
                                       right hand moves fastest)"""
import base64, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
import charpipe as CP, browser as BROWSER   # noqa: E402
CL = CP.CL
WANT = {'walk': ['south', 'south-east', 'east', 'south-west', 'west'], 'run': ['east'], 'slash': ['east', 'south-east']}

PASS = r"""
    if (window.wantDepth) {              // the same pose, each pixel's distance from the camera → window.depthShots
      if (!window._dm) window._dm = new THREE.ShaderMaterial({ side: THREE.DoubleSide, uniforms: { uHeads: { value: new THREE.Vector4(-1, -1, -1, -1) } },
        vertexShader: '#include <common>\n#include <skinning_pars_vertex>\nuniform vec4 uHeads; varying float vD; varying float vH; void main() {\n#include <skinbase_vertex>\n#include <begin_vertex>\n#include <skinning_vertex>\n vec4 v = viewMatrix * modelMatrix * vec4(transformed, 1.0); vD = (-v.z - 8.0) / 4.0; gl_Position = projectionMatrix * v; vH = 0.0;\n#ifdef USE_SKINNING\n for (int j = 0; j < 4; j++) vH += dot(skinWeight, vec4(equal(skinIndex, vec4(uHeads[j]))));\n#endif\n }',
        fragmentShader: 'varying float vD; varying float vH; void main() { float v = clamp(vD, 0.0, 1.0) * 65535.0; gl_FragColor = vec4(floor(v / 256.0) / 255.0, mod(floor(v), 256.0) / 255.0, step(0.5, vH), 1.0); }' });
      if (!window._heads) { let sk = null; root.traverse((o) => { if (o.isSkinnedMesh && !sk) sk = o.skeleton; });      // blue: the head (skinned to a head bone)
        const ix = sk ? sk.bones.map((b, i) => /head/i.test(b.name) ? i : -1).filter((i) => i >= 0).slice(0, 4) : []; while (ix.length < 4) ix.push(-1);
        window._heads = ix; window._dm.uniforms.uHeads = { value: new THREE.Vector4(...ix) }; }
      root.traverse((o) => { if (o.isMesh) o.material = window._dm; });
      renderer.render(scene, cam); window.depthShots.push(renderer.domElement.toDataURL('image/png'));
      root.traverse((o) => { if (o.isMesh) o.material = o.userData.toon; });
    }
"""

VIS = "    if (held) held.visible = !(window.holdUntil != null && t > window.holdUntil + 1e-6);\n"
BALL = r"""  snowball: (o) => {                              // a ball in the palm: packed snow, a little lumpy
    const g = new THREE.Group(), r = (o.radius || 0.05) / (o.size || 1.7);
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 2), new THREE.MeshToonMaterial({ color: new THREE.Color(o.color || '#eef4fb'), gradientMap: rampTex() }));
    m.position.set(0, r * 0.6, 0); g.add(m); return g;
  },
"""
SPEED = r"""// when the right hand moves fastest in a clip (a throw lets go there)
window.handFastest = (clipName, t0, t1) => {
  mixer.stopAllAction(); const clip = clips.find((c) => c.name === clipName); if (!clip || !bones.RightHand) return null; mixer.clipAction(clip).play();
  let best = [0, t0], prev = null;
  for (let i = 0; i <= 160; i++) { const t = t0 + (t1 - t0) * i / 160; mixer.setTime(t); root.updateMatrixWorld(true);
    const p = bones.RightHand.getWorldPosition(new THREE.Vector3()); if (prev) { const v = p.distanceTo(prev); if (v > best[0]) best = [v, t]; } prev = p; }
  return best[1];
};
"""

def patched():
    h = (REPO / 'render_char.html').read_text(encoding='utf-8')
    a = "window.shadowShots = []; window.heldShots = []; window.bodyShots = [];\n  root.rotation.y = FACING[dir]"
    b = "    if (shadows) {                       // the same pose, flat on the ground"
    assert h.count(a) == 1 and h.count(b) == 1, 'render_char.html has changed: the patch points are gone'
    h = h.replace(a, a.replace('window.bodyShots = [];', 'window.bodyShots = []; window.depthShots = [];'))
    h = h.replace(b, VIS + PASS + b)
    # something small held, and let go: a snowball (the repo's renderer knows an umbrella only), shown up to "until" seconds
    e = "const HOLDS = {\n"; f = "    mixer.setTime(t);\n"; g = "window.ready = true;"
    assert h.count(e) == 1 and h.count(f) == 1 and h.count(g) == 1, 'render_char.html has changed: the patch points are gone'
    h = h.replace(e, e + BALL).replace(f, f + VIS).replace(g, SPEED + g)
    # no antialiasing: a blended 16-bit value is no depth at all
    c = 'antialias: true'; assert h.count(c) == 1; return h.replace(c, 'antialias: false')

def main(spec, WANT=WANT, sd=None, colour=False):
    """colour=True: the colour frames, shadows and held/body shots too, into render/ (for a held thing the repo's renderer does not know)"""
    from playwright.sync_api import sync_playwright
    s, d = sd or CP.load(spec); glb = Path(s.get("rig_glb") or d / "rig/rig.glb"); out = d / "depth"; out.mkdir(exist_ok=True)
    html = patched()

    def serve(route):
        p = route.request.url.split('spritecast.local/', 1)[1]
        if p == 'asset/rig.glb': return route.fulfill(path=str(glb), content_type='model/gltf-binary')
        if p == 'render_char.html': return route.fulfill(body=html, content_type='text/html')
        f = (REPO / p).resolve()
        if REPO not in f.parents: return route.abort()
        route.fulfill(path=str(f), content_type='text/javascript')
    save = lambda url, p: Path(p).write_bytes(base64.b64decode(url.split(',', 1)[1]))
    with sync_playwright() as pw:
        br = BROWSER.launch(pw); pg = br.new_page(); pg.route('http://spritecast.local/**', serve); pg.goto('http://spritecast.local/render_char.html')
        pg.wait_for_function('window.ready === true', timeout=30000); pg.evaluate('(r) => window.setRes(r)', CL.PX)
        info = pg.evaluate('([u, p, l]) => window.load(u, p, l)', ['http://spritecast.local/asset/rig.glb', s['pitch'], s['light']])
        pg.evaluate('() => { window.wantDepth = true; }')
        clips = {c['name']: c['duration'] for c in info['clips']}; w = s['walk']
        pose = [s['head_up'], s['shoulder_up'], s['shoulder_wide'], bool(colour)]; ren = d / 'render'
        for dr in WANT.get('walk', []):
            pg.evaluate('(a) => window.frames(...a)', [w['clip'], dr, s['frames'], w['t0'], w['t1']] + pose)
            for k, u in enumerate(pg.evaluate('window.depthShots')): save(u, out / f'walk-{dr}-{k}.png')
        for name, a in s['actions'].items():           # as charpipe.render: the same times, canvas and held thing
            if name not in WANT or a['clip'] not in clips: continue
            t0, t1, n = a['t0'], a['t1'] if a['t1'] is not None else clips[a['clip']], a['frames']
            t1x = t1 if a['loop'] else t0 + (t1 - t0) * n / max(1, n - 1)
            hold = a.get('hold'); pg.evaluate('(px) => window.setCanvas(px)', a.get('canvas') or (768 if hold else 512))
            if hold:
                h = {'kind': hold} if isinstance(hold, str) else dict(hold)
                h.setdefault('size', s.get('height_m', 1.7)); h.setdefault('grip', [0, 0, -90])
                if not pg.evaluate('([k, o]) => window.setHold(k, o)', [h['kind'], h]): print(f"depth: {name}: cannot hold \"{h['kind']}\"")
                until = h.get('until')
                if until == 'auto': until = pg.evaluate('([c, a, b]) => window.handFastest(c, a, b)', [a['clip'], t0, t1]); print(f'depth: {name}: let go at {until:.2f} s (the hand at its fastest)')
                pg.evaluate('(u) => { window.holdUntil = u; }', until); pg.evaluate('(w) => { window.wantHeld = w; }', bool(colour))
            for dr in WANT[name]:
                shots = pg.evaluate('(a) => window.frames(...a)', [a['clip'], dr, n, t0, t1x] + pose)
                for k, u in enumerate(pg.evaluate('window.depthShots')): save(u, out / f'{name}-{dr}-{k}.png')
                if colour:
                    for k, u in enumerate(shots): save(u, ren / f'{name}-{dr}-{k}.png')
                    for k, u in enumerate(pg.evaluate('window.shadowShots')): save(u, ren / f'{name}-{dr}-{k}-s.png')
                    for k, u in enumerate(pg.evaluate('window.heldShots')): save(u, ren / f'{name}-{dr}-{k}-held.png')
                    for k, u in enumerate(pg.evaluate('window.bodyShots')): save(u, ren / f'{name}-{dr}-{k}-body.png')
            pg.evaluate('() => { window.clearHold(); window.holdUntil = null; window.wantHeld = false; }'); pg.evaluate('() => window.setCanvas(512)')
            print('depth:', name, WANT[name])
        print('depth: head bones', pg.evaluate('window._heads')); br.close()
    print('depth:', out)

if __name__ == '__main__':
    # depth.py SPEC                       the depth pass for WANT
    # depth.py SPEC render CLIP           colour frames + depth of one action, all eight facings (a held thing this renderer adds)
    if len(sys.argv) > 3 and sys.argv[2] == 'render': main(sys.argv[1], {sys.argv[3]: ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']}, colour=True)
    else: main(sys.argv[1])
