"""lightedit: move the light round a pixel prop and see its shadow - then keep it. A page on this computer only (127.0.0.1).

    python lightedit.py PROP.json                 opens the page (free: the shadow is baked from the prop's 3D model, as propshade.py does)
    python lightedit.py PROP.json --port 8796 --no-open

On the page: drag on the floor to move the lamp (its spot on the floor follows the pointer), the wheel or the slider for its height,
the size slider for how big it is (a bare bulb ~0.03 m: a sharp shadow; a lampshade ~0.15; a ceiling panel ~0.4: soft), or the sun /
a grey day instead. The shadow - and a lamp's light on the floor - is redrawn as you go (a quick bake); Save bakes every side properly, writes
them to out-pixel/ like propshade.py (shadow-<side>.png, light-<side>.png), and puts the light in the spec ("lamp" or "shadow"), so proppixel.py keeps it next time.

Needs: the prop's 3D model (isoprop.py model) and its pixel sprites (proppixel.py)."""
import argparse, base64, io, json, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, str(Path(__file__).resolve().parent))
import propshade as S

PAGE = r"""<!doctype html><meta charset="utf-8"><title>Light - %NAME%</title>
<style>
body{margin:0;background:#1d1b19;color:#e9e4dc;font:14px system-ui,sans-serif;display:flex;gap:16px;padding:14px}
#side{width:270px;display:flex;flex-direction:column;gap:12px}
h1{font-size:16px;margin:0}
.box{background:#2a2724;border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:8px}
label{display:flex;justify-content:space-between;gap:8px}
input[type=range]{width:100%}
button{font:inherit;padding:6px 10px;border-radius:6px;border:1px solid #5a534b;background:#3a3531;color:#e9e4dc;cursor:pointer}
button.on{background:#c8955a;color:#1d1b19;border-color:#c8955a}
.row{display:flex;gap:6px;flex-wrap:wrap}
#save{background:#4f7a4a;border-color:#4f7a4a}
#msg{min-height:1.4em;color:#bfe0b0}
small{color:#a49b90;line-height:1.4}
canvas{image-rendering:pixelated;background:#000;border-radius:6px;cursor:crosshair;max-height:calc(100vh - 28px)}
</style>
<div id="side">
<h1>%NAME% - the light</h1>
<div class="box"><b>Side</b><div class="row" id="views"></div></div>
<div class="box"><b>Light</b><div class="row">
 <button data-w="sun">Sun</button><button data-w="overcast">Grey day</button><button data-w="lamp">Lamp</button></div>
 <small id="hint"></small></div>
<div class="box" id="lampbox">
 <label>Height <span id="hv"></span></label><input id="h" type="range" min="0.2" max="3.5" step="0.05">
 <label>Size <span id="rv"></span></label><input id="r" type="range" min="0.01" max="0.6" step="0.01">
 <small>Drag on the floor to move it; the wheel lifts and lowers it. A bare bulb ~0.03 (sharp), a lampshade ~0.15, a ceiling panel ~0.4 (soft).</small>
 <label><span>Light on the floor</span><input id="pool" type="checkbox" checked></label>
</div>
<div class="box"><b>Look</b><div class="row"><button data-s="pixel">Pixel</button><button data-s="smooth">Smooth</button></div>
 <small>Pixel: the shadow, the glow and the floor's light in steps, dithered. Smooth: gradients (a game not in pixel art).</small></div>
<div class="box"><label>Shadow strength <span id="dv"></span></label><input id="d" type="range" min="0.5" max="2.5" step="0.1" value="1">
 <small>The shadow as if laid this many times. 1: as the light gives it. Pixel art starts at 1.5 - a little louder than it is, so things stand on the ground.</small></div>
<div class="box" id="picbox"><b>The lamp</b><div class="row" id="lamps"><button data-p="glow">A glow</button></div>
 <div class="row"><button data-p="own">Load a picture...</button><input id="lname" placeholder="its name (else the file's)" style="flex:1;min-width:0;font:inherit;padding:5px;border-radius:6px;border:1px solid #5a534b;background:#1d1b19;color:#e9e4dc"></div>
 <small>Your lamps are kept in ~/.spritecast/lamps (for every prop); the ones that come with SpriteCast too.</small>
 <input id="file" type="file" accept="image/*" style="display:none">
 <div id="pictools" style="display:none;flex-direction:column;gap:8px">
  <div class="row"><span style="align-self:center">On the lamp:</span><button data-k="move">Move</button><button data-k="light">Set its light</button><button data-k="foot">Set its foot</button></div>
  <label>Scale <span id="kv"></span></label><input id="k" type="range" min="0.05" max="3" step="0.05" value="1">
  <div class="row"><button id="k1">1 : 1</button><small id="tall" style="align-self:center"></small></div>
  <div class="row"><button id="savelamp" style="flex:1">Save this lamp's settings</button><button id="dellamp">Delete this lamp</button></div><small>Its scale, its foot, its light point and the light's size - kept with the lamp, next time it is chosen.</small>
 </div>
 <canvas id="pic" style="display:none;align-self:center;cursor:crosshair;background:#3a3531;border-radius:4px"></canvas>
 <small id="pichint">Or drop a PNG of your lamp on the page - at the prop's scale, see-through round it. Drag it (or the floor) to move it; "Set its light" / "Set its foot", then one click on the lamp (here or in the room). The ring is the light's size, the red cross where it stands.</small>
 <div id="picmsg" style="color:#ffd27a;min-height:1.2em"></div></div>
<button id="save">Bake &amp; save the scene</button><small>Every side's shadow (and a lamp's light on the floor) into out-pixel/, and the light into the spec - it opens like this next time.</small>
<div id="msg"></div>
</div>
<canvas id="c"></canvas>
<script>
const Z = 4, W = 260, H = 230, FX = 130, FY = 170;
const cv = document.getElementById('c'), x = cv.getContext('2d'); cv.width = W * Z; cv.height = H * Z; x.imageSmoothingEnabled = false;
const off = document.createElement('canvas'); off.width = W; off.height = H; const o = off.getContext('2d');
let info, view, sprites = {}, shade = null, pool = null, lampImg = null, busy = false, again = false;
let L = {w: 'lamp', x: -0.9, y: 2.0, z: -0.3, r: 0.05, d: 1.5, style: 'pixel', pic: null};          // pic: {file, foot, light} - a lamp picture of one's own
let picImg = null, pickWhat = 'move';          // (on the lamp: drag it about, or one click sets its light point / where it stands, then back to moving)
const $ = (id) => document.getElementById(id), msg = (t) => $('msg').textContent = t;
fetch('info').then(r => r.json()).then(j => {
  info = j; if (j.light) Object.assign(L, j.light); if (L.pic) { $('k').value = L.pic.scale || 1; loadPic(); }
  for (const v of j.views) {
    const b = document.createElement('button'); b.textContent = v.key + '°'; b.onclick = () => { view = v; mark(); ask(); }; b.dataset.k = v.key; $('views').appendChild(b);
    const im = new Image(); im.src = 'sprite/' + v.key; im.onload = draw; sprites[v.key] = im;
  }
  view = j.views[0]; $('h').value = L.y; $('r').value = L.r; $('d').value = L.d; mark(); ask();
});
function mark() {
  document.querySelectorAll('#views button').forEach(b => b.classList.toggle('on', b.dataset.k === view.key));
  document.querySelectorAll('[data-w]').forEach(b => b.classList.toggle('on', b.dataset.w === L.w));
  $('lampbox').style.opacity = L.w === 'lamp' ? 1 : 0.35; $('hv').textContent = (+L.y).toFixed(2) + ' m'; $('rv').textContent = (+L.r).toFixed(2) + ' m'; $('dv').textContent = (+L.d).toFixed(1) + ' x';
  document.querySelectorAll('[data-s]').forEach(b => b.classList.toggle('on', b.dataset.s === L.style));
  document.querySelectorAll('[data-p]').forEach(b => b.classList.toggle('on', b.dataset.p === (L.pic ? 'x-' + L.pic.from : 'glow')));
  $('h').disabled = !!L.pic; $('pic').style.display = L.pic ? 'block' : 'none'; $('pictools').style.display = L.pic ? 'flex' : 'none';
  document.querySelectorAll('[data-k]').forEach(b => b.classList.toggle('on', b.dataset.k === pickWhat));
  if (L.pic) { $('kv').textContent = (+L.pic.scale || 1).toFixed(2) + ' x'; if (picImg) $('tall').textContent = picImg.width + ' x ' + picImg.height + ' px - about ' + ((L.pic.foot[1] - lampTop()) / (C() * ppm())).toFixed(2) + ' m tall at this prop\'s scale'; }
  $('hint').textContent = L.w === 'sun' ? "SpriteCast's own sun, from the upper right." : L.w === 'overcast' ? 'No sun: only the soft dark round it.' : 'x ' + L.x.toFixed(2) + '  y ' + (+L.y).toFixed(2) + '  z ' + L.z.toFixed(2) + ' m from its foot';
}
document.querySelectorAll('[data-w]').forEach(b => b.onclick = () => { L.w = b.dataset.w; mark(); ask(); });
$('h').oninput = () => { L.y = +$('h').value; mark(); ask(); };
$('d').oninput = () => { L.d = +$('d').value; mark(); ask(); };
$('r').oninput = () => { L.r = +$('r').value; mark(); picUp(); draw(); ask(); };
$('pool').onchange = draw;
document.querySelectorAll('[data-s]').forEach(b => b.onclick = () => { L.style = b.dataset.s; mark(); ask(); });
document.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { if (b.dataset.p === 'glow') { L.pic = null; picImg = null; mark(); draw(); ask(); } else if (b.dataset.p === 'own') $('file').click(); });
function applyPic(j) {          // (a lamp chosen or loaded: its picture at its scale, its points, its light's size)
  if (j.error) { $('picmsg').textContent = j.error; return; }
  const k = j.scale || 1; L.pic = {file: j.file, from: j.name, scale: k, foot0: j.foot0, light0: j.light0, foot: [j.foot0[0] * k, j.foot0[1] * k], light: [j.light0[0] * k, j.light0[1] * k]};
  if (j.r) { L.r = j.r; $('r').value = j.r; } L.w = 'lamp'; $('k').value = k; pickWhat = 'move';
  $('picmsg').textContent = j.name.replace(/_/g, ' ') + (j.note || '') + (j.saved ? ' - with its saved settings' : '') + ' - ' + j.size[0] + ' x ' + j.size[1] + ' px'; loadPic();
}
const useLamp = (name) => fetch('lamp-use', {method: 'POST', body: JSON.stringify({name})}).then(r => r.json()).then(applyPic);
function sendPic(buf, fname) {          // (a picture of their own: kept in their lamps under its file's name - renamed below if wanted - and chosen)
  const name = $('lname').value.trim() || (fname || 'my lamp').replace(/\.[^.]+$/, ''); $('picmsg').textContent = 'loading ' + (fname || '') + '...';
  fetch('lamp-picture?name=' + encodeURIComponent(name), {method: 'POST', body: buf}).then(r => r.json()).then(j => { $('lname').value = ''; applyPic(j); if (!j.error) listLamps(); })
    .catch(err => { $('picmsg').textContent = 'could not send it: ' + err; });
}
$('file').onchange = () => { const f = $('file').files[0]; if (f) f.arrayBuffer().then(b => sendPic(b, f.name)); $('file').value = ''; };
addEventListener('dragover', (e) => e.preventDefault());
addEventListener('drop', (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) f.arrayBuffer().then(b => sendPic(b, f.name)); });
let lampList = [];
function listLamps() {          // (one button a lamp: SpriteCast's and theirs)
  fetch('lamps').then(r => r.json()).then(list => { lampList = list; document.querySelectorAll('#lamps [data-p^="x-"]').forEach(b => b.remove());
    for (const n of list) { const b = document.createElement('button'); b.textContent = n.name.replace(/_/g, ' ') + (n.mine ? ' *' : ''); b.title = n.mine ? 'one of your lamps' : 'comes with SpriteCast';
      b.dataset.p = 'x-' + n.name; b.onclick = () => useLamp(n.name); $('lamps').appendChild(b); } mark(); });
}
listLamps();
let delArmed = null;          // (delete asks twice: the button itself turns to "really?" - no browser dialog, which some browsers do not show)
$('dellamp').onclick = () => {
  if (!L.pic) return; const name = L.pic.from, mine = !!(lampList.find(n => n.name === name) || {}).mine, builtin = !!(lampList.find(n => n.name === name) || {}).builtin;
  if (delArmed !== name) { delArmed = name; $('dellamp').textContent = builtin ? 'Really? (back to as it came)' : 'Really delete it?'; setTimeout(() => { delArmed = null; $('dellamp').textContent = 'Delete this lamp'; }, 4000); return; }
  delArmed = null; $('dellamp').textContent = 'Delete this lamp';
  fetch('lamp-delete', {method: 'POST', body: JSON.stringify({name})}).then(r => r.json()).then(j => {
    $('picmsg').textContent = j.msg; listLamps();
    if (j.builtin) useLamp(name); else { L.pic = null; picImg = null; mark(); draw(); ask(); }
  });
};
$('savelamp').onclick = () => { if (!L.pic) return; fetch('lamp-save', {method: 'POST', body: JSON.stringify({name: L.pic.from, scale: L.pic.scale, foot0: L.pic.foot0, light0: L.pic.light0, r: L.r})})
  .then(r => r.text()).then(t => { $('picmsg').textContent = t; listLamps(); }); };
let picAlpha = null;          // (the lamp picture's own pixels: a click on the lamp, not beside it)
function loadPic() {          // the lamp picture: shown big beside, its foot (red) and its light (yellow); its light's height from it
  const im = new Image(); im.onload = () => { picImg = im; const c = $('pic'), k = Math.max(1, Math.floor(180 / im.height)); c.width = im.width * k; c.height = im.height * k; c.k = k;
    const t = document.createElement('canvas'); t.width = im.width; t.height = im.height; const g = t.getContext('2d'); g.drawImage(im, 0, 0); picAlpha = g.getImageData(0, 0, im.width, im.height);
    picUp(); mark(); draw(); ask(); };
  im.src = 'lamp-picture?' + Date.now();
}
function picUp() {
  if (!picImg) return; const c = $('pic'), g = c.getContext('2d'), k = c.k; g.imageSmoothingEnabled = false; g.clearRect(0, 0, c.width, c.height); g.drawImage(picImg, 0, 0, c.width, c.height);
  g.fillStyle = '#ff5050'; g.fillRect(L.pic.foot[0] * k - 2, L.pic.foot[1] * k - 2, 5, 5); g.fillStyle = '#ffe040'; g.fillRect(L.pic.light[0] * k - 2, L.pic.light[1] * k - 2, 5, 5);
  g.strokeStyle = '#ffe040'; g.lineWidth = 1; g.beginPath(); g.arc(L.pic.light[0] * k, L.pic.light[1] * k, Math.max(1.5, L.r * ppm()) * k, 0, 7); g.stroke();          // (the light's size)
  L.y = Math.max(0.05, (L.pic.foot[1] - L.pic.light[1]) / (C() * ppm())); $('h').value = L.y;
}
function setPoint(q) {          // (the light point or the foot, in the lamp picture's pixels; kept in the original's too, so a new scale keeps them)
  const k = +L.pic.scale || 1; L.pic[pickWhat] = q; L.pic[pickWhat + '0'] = [q[0] / k, q[1] / k]; pickWhat = 'move'; picUp(); mark(); draw(); ask();
}
const lampTop = () => { if (!picAlpha) return 0; for (let y = 0; y < picAlpha.height; y++) for (let x = 0; x < picAlpha.width; x++) if (picAlpha.data[(y * picAlpha.width + x) * 4 + 3] > 100) return y; return 0; };
$('pic').onclick = (e) => { if (pickWhat === 'move') pickWhat = 'light'; const c = $('pic'), b = c.getBoundingClientRect(); setPoint([(e.clientX - b.left) / b.width * picImg.width, (e.clientY - b.top) / b.height * picImg.height]); };
document.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { pickWhat = b.dataset.k; mark(); });
function rescale(k) {          // (the lamp picture at another size, made from its original: up by whole pixels, down by SpriteCast's pixel reducer)
  fetch('lamp-scale?k=' + k).then(r => r.json()).then(j => { if (j.error) { $('picmsg').textContent = j.error; return; }
    L.pic.scale = k; for (const n of ['foot', 'light']) { const p0 = L.pic[n + '0'] || L.pic[n]; if (!L.pic[n + '0']) L.pic[n + '0'] = p0; L.pic[n] = [p0[0] * k, p0[1] * k]; }
    L.pic.file = j.file; loadPic(); });
}
let kt = null; $('k').oninput = () => { $('kv').textContent = (+$('k').value).toFixed(2) + ' x'; clearTimeout(kt); kt = setTimeout(() => rescale(+$('k').value), 120); };
$('k1').onclick = () => { $('k').value = 1; rescale(1); };
function ask() {          // the quick shadow from the page's server; one at a time, the last asked wins
  if (busy) { again = true; return; } busy = true;
  const q = new URLSearchParams({v: view.key, w: L.w, x: L.x, y: L.y, z: L.z, r: L.r, s: L.style, d: L.d});
  fetch('shade?' + q).then(r => r.json()).then(j => {
    pool = null;
    if (j.lamp) { const li = new Image(); li.onload = () => { lampImg = {im: li, mid: j.lamp.mid}; draw(); }; li.src = 'data:image/png;base64,' + j.lamp.png; }
    if (j.pool) { const pi = new Image(); pi.onload = () => { const c = document.createElement('canvas'); c.width = pi.width; c.height = pi.height; const g = c.getContext('2d'); g.drawImage(pi, 0, 0);
      pool = {d: g.getImageData(0, 0, pi.width, pi.height), at: j.pool.at, w: pi.width, h: pi.height}; draw(); }; pi.src = 'data:image/png;base64,' + j.pool.png; }
    if (j.png) { const im = new Image(); im.onload = () => { shade = {im, at: j.at}; draw(); }; im.src = 'data:image/png;base64,' + j.png; } else { shade = null; draw(); }
  }).finally(() => { busy = false; if (again) { again = false; ask(); } });
}
const ppm = () => info.ppm, S = () => Math.sin(info.pitch), C = () => Math.cos(info.pitch);
const floorAt = (gx, gz) => [FX + gx * ppm(), FY + gz * S() * ppm()];
function draw() {
  if (!info || !view) return;
  const img = o.createImageData(W, H), d = img.data;
  for (let py = 0; py < H; py++) for (let px = 0; px < W; px++) {
    const gx = (px - FX) / ppm(), gz = (py - FY) / (S() * ppm());
    const a = (gx + gz) / Math.SQRT2 / 0.5, b = (gz - gx) / Math.SQRT2 / 0.5, fa = a - Math.floor(a), fb = b - Math.floor(b);
    const chk = (Math.floor(a) + Math.floor(b)) & 1, seam = fa < 0.03 || fb < 0.03;
    let r = chk ? 214 : 205, g = chk ? 200 : 190, bl = chk ? 178 : 168; if (seam) { r *= 0.88; g *= 0.88; bl *= 0.88; }
    let lr = L.w === 'overcast' ? 0.82 : L.w === 'lamp' ? 0.55 : 1, lg = lr, lb = lr;          // (the room's own light; a grey day dimmer)
    if (L.w === 'lamp' && pool && $('pool').checked) {          // (the lamp's light as baked: light-<side>.png, laid on with ADD)
      const sx = Math.round(FX - view.foot[0]) + pool.at[0], sy = Math.round(FY - view.foot[1]) + pool.at[1], qx = px - sx, qy = py - sy;
      if (qx >= 0 && qy >= 0 && qx < pool.w && qy < pool.h) { const k = (qy * pool.w + qx) * 4, a = pool.d.data[k + 3] / 255 * 0.9;
        lr += a * pool.d.data[k] / 255; lg += a * pool.d.data[k + 1] / 255; lb += a * pool.d.data[k + 2] / 255; }
    }
    const i = (py * W + px) * 4; d[i] = Math.min(255, r * lr); d[i + 1] = Math.min(255, g * lg); d[i + 2] = Math.min(255, bl * lb); d[i + 3] = 255;
  }
  o.putImageData(img, 0, 0);
  const sx = Math.round(FX - view.foot[0]), sy = Math.round(FY - view.foot[1]);
  if (shade) o.drawImage(shade.im, sx + shade.at[0], sy + shade.at[1]);
  const sp = sprites[view.key], [fx, fy] = floorAt(L.x, L.z), front = fy > FY;          // (whichever stands further forward is drawn last)
  const lampPic = () => { if (L.w === 'lamp' && L.pic && picImg) o.drawImage(picImg, Math.round(fx - L.pic.foot[0]), Math.round(fy - L.pic.foot[1])); };
  if (!front) lampPic();
  if (sp && sp.complete) o.drawImage(sp, sx, sy);
  if (front) lampPic();
  if (L.w === 'lamp' && L.pic && picImg) {          // (the light in the lamp: its point and its size, a ring)
    const lx = Math.round(fx - L.pic.foot[0] + L.pic.light[0]) + 0.5, ly = Math.round(fy - L.pic.foot[1] + L.pic.light[1]) + 0.5;
    o.strokeStyle = 'rgba(255,224,64,0.95)'; o.lineWidth = 1; o.beginPath(); o.arc(lx, ly, Math.max(1.5, L.r * ppm()), 0, 7); o.stroke(); o.fillStyle = '#ffe040'; o.fillRect(lx - 0.5, ly - 0.5, 1, 1);
    const ft = Math.round(fx) + 0.5, fl = Math.round(fy) + 0.5; o.strokeStyle = 'rgba(255,80,80,0.95)'; o.beginPath(); o.moveTo(ft - 3, fl); o.lineTo(ft + 3, fl); o.moveTo(ft, fl - 1.5); o.lineTo(ft, fl + 1.5); o.stroke();          // (where it stands: a red cross on the floor)
  }
  if (L.w === 'lamp' && !L.pic) {          // the light: its spot on the floor, a thread up to it, a round glow its size
    const ly = fy - L.y * C() * ppm(), rr = Math.max(1.5, L.r * ppm());
    o.strokeStyle = 'rgba(255,240,200,0.5)'; o.setLineDash([2, 2]); o.beginPath(); o.moveTo(fx + 0.5, fy); o.lineTo(fx + 0.5, ly); o.stroke(); o.setLineDash([]);
    o.fillStyle = 'rgba(60,40,20,0.6)'; o.beginPath(); o.ellipse(fx, fy, 3, 1.5, 0, 0, 7); o.fill();
    if (lampImg) o.drawImage(lampImg.im, Math.round(fx - lampImg.mid[0]), Math.round(ly - lampImg.mid[1]));          // (lamp.png, as a game would draw it)
  }
  x.drawImage(off, 0, 0, W * Z, H * Z);
}
let drag = false, grab = [0, 0];          // (grab: where on the floor the pointer was against the lamp's spot - so a lamp picked up by its shade does not jump)
const toFloor = (e) => { const b = cv.getBoundingClientRect(), px = (e.clientX - b.left) / b.width * W, py = (e.clientY - b.top) / b.height * H;
  L.x = (px - grab[0] - FX) / ppm(); L.z = (py - grab[1] - FY) / (S() * ppm()); };
function onLamp(e) {          // (a click on the lamp picture itself, in the room: where its light comes from)
  if (!(L.w === 'lamp' && L.pic && picAlpha)) return null; const b = cv.getBoundingClientRect(), px = (e.clientX - b.left) / b.width * W, py = (e.clientY - b.top) / b.height * H;
  const [fx, fy] = floorAt(L.x, L.z), qx = Math.floor(px - Math.round(fx - L.pic.foot[0])), qy = Math.floor(py - Math.round(fy - L.pic.foot[1]));
  if (qx < 0 || qy < 0 || qx >= picAlpha.width || qy >= picAlpha.height || picAlpha.data[(qy * picAlpha.width + qx) * 4 + 3] < 100) return null; return [qx + 0.5, qy + 0.5];
}
cv.onmousedown = (e) => {
  const hit = onLamp(e);
  if (hit && pickWhat !== 'move') { setPoint(hit); return; }
  const b = cv.getBoundingClientRect(), px = (e.clientX - b.left) / b.width * W, py = (e.clientY - b.top) / b.height * H, [fx, fy] = floorAt(L.x, L.z);
  grab = hit ? [px - fx, py - fy] : [0, 0];          // (on the lamp: carried from where it was held; on the floor: the lamp comes to the pointer)
  if (L.w !== 'lamp') { L.w = 'lamp'; } drag = true; toFloor(e); mark(); draw(); ask(); };
addEventListener('mousemove', (e) => { if (drag) { toFloor(e); mark(); draw(); ask(); } });
addEventListener('mouseup', () => drag = false);
cv.onwheel = (e) => { e.preventDefault(); if (L.w !== 'lamp' || L.pic) return;          // (a lamp picture of one's own has its own height)
  L.y = Math.min(3.5, Math.max(0.2, L.y - Math.sign(e.deltaY) * 0.05)); $('h').value = L.y; mark(); draw(); ask(); };
$('save').onclick = () => { msg('baking every side...'); fetch('save', {method: 'POST', body: JSON.stringify(L)}).then(r => r.text()).then(msg); };
</script>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--port', type=int, default=8796); ap.add_argument('--no-open', action='store_true'); A = ap.parse_args()
    spec_path = Path(A.spec).resolve(); print('reading the model and laying it on each side...', flush=True); prep = S.prepare(spec_path); lock = threading.Lock()
    spec = prep['spec']; lamp = S.lamp_of(spec)
    here = Path(__file__).resolve().parent.parent.parent.parent / 'examples' / 'lamps'          # (the lamps that come with SpriteCast: examples/lamps/<name>/out-pixel/sprite.png)
    LAMPS = {f.parent.parent.name: f for f in sorted(here.glob('*/out-pixel/sprite.png'))} if here.exists() else {}
    LIB = Path.home() / '.spritecast' / 'lamps'          # (their lamps, for every prop: <name>/source.png and lamp.json - its settings)
    D = spec_path.parent / spec['name']

    def lamp_src(name):
        f = LIB / name / 'source.png'; return f if f.exists() else LAMPS.get(name)

    def cut_out(im):          # (a picture with no see-through: what is the colour of its edge and joined to it goes - only that colour: a dark foot
        # next to a dark background stays. How near counts goes by how even the edge is: a flat background, within 8; a photo's, more)
        a = S.np.asarray(im).copy(); rgb = a[..., :3].astype(int); edge = S.np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]); bg = S.np.median(edge, 0)
        tol = min(28, max(8, 3 * float(S.np.abs(edge - bg).max(1).std()))); near = S.np.abs(rgb - bg).max(2) <= tol; lab, n = S.ndi.label(near); touch = set(S.np.unique(S.np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        a[S.np.isin(lab, list(touch)), 3] = 0; return S.Image.fromarray(a)

    def unscale(im):          # (pixel art shown enlarged - every pixel an N x N block: back to its own pixels, so scaling it is not done twice)
        a = S.np.asarray(im); runs = []
        for line in list(a[:: max(1, a.shape[0] // 40)]) + list(a[:, :: max(1, a.shape[1] // 40)].transpose(1, 0, 2)):
            ch = S.np.nonzero((line[1:] != line[:-1]).any(1))[0] + 1; e = S.np.concatenate([[0], ch, [len(line)]]); runs += list(S.np.diff(e)[1:-1])          # (the inner runs)
        if len(runs) < 20: return im, 1
        g = int(S.np.gcd.reduce(S.np.array(runs, int)))
        if g < 2: return im, 1
        return S.Image.fromarray(a[g // 2::g, g // 2::g].copy()), g

    def scaled(im, k):          # (bigger by whole pixels - nearest - smaller by pixelsmall's reducer, which keeps outlines)
        if abs(k - 1) < 1e-3: return im
        if k > 1: return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), S.Image.NEAREST)
        import pixelsmall; return S.Image.fromarray(pixelsmall.reduce(S.np.asarray(im), k))

    def use(name):          # (a lamp for this prop: its original beside the prop, a copy at its scale, its points and settings)
        src = lamp_src(name)
        if src is None: return {'error': f'no lamp called {name}'}
        im = S.Image.open(src).convert('RGBA'); im = im.crop(im.getbbox()); im.save(D / 'lamp-source.png'); foot, light = S.lamp_picture_points(im)
        st = json.loads((LIB / name / 'lamp.json').read_text()) if (LIB / name / 'lamp.json').exists() else {}
        k = float(st.get('scale', 1)); note = ''
        if not st:          # (first time: a picture far too big or small for the prop - an HD drawing - brought to ~1.5 m tall)
            tall = im.height / (S.math.cos(prep['views'][0]['pitch']) * prep['ppm'])
            if tall > 3.5 or tall < 0.3: k = round(min(4.0, max(0.05, 1.5 / tall)), 2); note = f' (it would stand {tall:.1f} m tall here: scaled {k}x)'
        out_ = scaled(im, k); out_.save(D / 'lamp-picture.png')
        return {'name': name, 'file': f"{spec['name']}/lamp-picture.png", 'foot0': st.get('foot0', foot), 'light0': st.get('light0', light), 'scale': k, 'r': st.get('r'),
                'saved': bool(st), 'size': list(out_.size), 'note': note}
    def info():          # (read from the spec each time the page opens: it opens as it was last saved)
        sp = json.loads(spec_path.read_text(encoding='utf-8')); lp = S.lamp_of(sp); pc = sp['lamp'].get('picture') if isinstance(sp.get('lamp'), dict) else None
        light = {'w': 'lamp', 'x': lp[0][0], 'y': lp[0][1], 'z': lp[0][2], 'r': lp[1], 'pic': pc} if lp else {'w': sp.get('shadow') or 'sun'}
        light['style'] = sp.get('light_style', 'pixel'); light['d'] = S.strength_of(sp.get('shadow_strength'), light['style'])
        return {'name': spec['name'], 'ppm': prep['ppm'], 'pitch': prep['views'][0]['pitch'], 'light': light, 'views': [{'key': v['key'], 'foot': v['foot']} for v in prep['views']]}

    class H(BaseHTTPRequestHandler):
        def send(self, body, kind, code=200):
            self.send_response(code); self.send_header('Content-Type', kind); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path == '/info': return self.send(json.dumps(info()).encode(), 'application/json')
            if u.path == '/lamp-scale':          # (from the original: bigger by whole pixels - nearest - smaller by pixelsmall's reducer, which keeps outlines)
                src = D / 'lamp-source.png'
                if not src.exists(): return self.send(json.dumps({'error': 'choose a lamp first'}).encode(), 'application/json')
                k = min(4.0, max(0.1, float(q.get('k', 1)))); out_ = scaled(S.Image.open(src).convert('RGBA'), k); out_.save(D / 'lamp-picture.png'); return self.send(json.dumps({'file': f"{spec['name']}/lamp-picture.png", 'size': list(out_.size)}).encode(), 'application/json')
            if u.path == '/lamps':
                mine = sorted(f.parent.name for f in LIB.glob('*/source.png')) if LIB.exists() else []
                return self.send(json.dumps([{'name': n, 'mine': False, 'builtin': True} for n in sorted(LAMPS) if n not in mine] + [{'name': n, 'mine': True, 'builtin': n in LAMPS} for n in mine]).encode(), 'application/json')
            if u.path == '/lamp-picture':
                f = spec_path.parent / spec['name'] / 'lamp-picture.png'
                return self.send(f.read_bytes(), 'image/png') if f.exists() else self.send(b'none', 'text/plain', 404)
            if u.path.startswith('/sprite/'):
                v = next((v for v in prep['views'] if v['key'] == u.path.split('/')[-1]), None)
                if v is None: return self.send(b'no such side', 'text/plain', 404)
                b = io.BytesIO(); v['sp'].save(b, 'PNG'); return self.send(b.getvalue(), 'image/png')
            if u.path == '/shade':
                v = next((v for v in prep['views'] if v['key'] == q.get('v')), prep['views'][0]); w = q.get('w', 'sun')
                lp = ([float(q['x']), max(0.05, float(q['y'])), float(q['z'])], max(0.005, float(q['r']))) if w == 'lamp' else None; st = q.get('s', 'pixel')
                with lock: S.STRENGTH = min(3.0, max(0.3, float(q.get('d', 1)))); got, pl = S.shadow_of(prep, v, w, lp, fast=True, with_pool=True, style=st)
                def enc(g): b = io.BytesIO(); g[0].save(b, 'PNG'); return {'png': base64.b64encode(b.getvalue()).decode(), 'at': g[1]}
                lm = S.lamp_sprite(lp[1], prep['ppm'], st) if lp else None          # (the light itself, as pixel art or smooth)
                return self.send(json.dumps({**(enc(got) if got else {}), **({'pool': enc(pl)} if pl else {}), **({'lamp': {**enc((lm[0], None)), 'mid': lm[1]}} if lm else {})}).encode(), 'application/json')
            return self.send(PAGE.replace('%NAME%', spec['name']).encode(), 'text/html; charset=utf-8')

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path == '/lamp-use': return self.send(json.dumps(use(json.loads(body)['name'])).encode(), 'application/json')
            if u.path == '/lamp-save':          # (a lamp's settings, kept with it; one of SpriteCast's becomes one of theirs, with them)
                j = json.loads(body); name = j['name']; src = lamp_src(name)
                if src is None: return self.send(b'no such lamp', 'text/plain', 404)
                (LIB / name).mkdir(parents=True, exist_ok=True)
                if not (LIB / name / 'source.png').exists(): (LIB / name / 'source.png').write_bytes(src.read_bytes())
                (LIB / name / 'lamp.json').write_text(json.dumps({'scale': round(float(j['scale'] or 1), 2), 'foot0': [round(v, 2) for v in j['foot0']], 'light0': [round(v, 2) for v in j['light0']], 'r': round(float(j['r']), 3)}, indent=1))
                return self.send(f"saved {name}'s settings - in {LIB / name}".encode(), 'text/plain; charset=utf-8')
            if u.path == '/lamp-delete':          # (one of theirs: gone from their lamps; one of SpriteCast's: its saved settings gone - back to as it came)
                name = json.loads(body)['name']; d = LIB / name
                if d.parent != LIB or not name: return self.send(json.dumps({'msg': 'no such lamp'}).encode(), 'application/json')
                import shutil; had = d.exists(); shutil.rmtree(d, ignore_errors=True); bi = name in LAMPS
                print(f'  lamp deleted: {name}' + (' (SpriteCast\'s: back to as it came)' if bi else ''), flush=True)
                return self.send(json.dumps({'builtin': bi, 'msg': (f"{name}: back to as it came with SpriteCast" if bi else f"{name} deleted from your lamps") if had or bi else f'{name} was not kept'}).encode(), 'application/json')
            if u.path == '/lamp-picture':          # (a lamp picture of their own: named, kept in their lamps, then used)
                name = ''.join(c for c in q.get('name', 'my lamp').strip() if c.isalnum() or c in ' _-').strip().replace(' ', '_') or 'my_lamp'
                try: im = S.Image.open(io.BytesIO(body)).convert('RGBA')
                except Exception as ex:
                    print(f'  lamp picture: could not read it ({len(body)} bytes): {ex}', flush=True)
                    return self.send(json.dumps({'error': 'not a picture this can read'}).encode(), 'application/json')
                cut = ''; im, blk = unscale(im)
                if blk > 1: cut += f' (pixel art shown {blk}x: back to its own pixels)'
                if im.getchannel('A').getextrema()[0] == 255:          # (not cut out: the background - the colour round its edge - taken away)
                    im = cut_out(im); cut += ' (its background cut away)'
                if im.getbbox() is None: return self.send(json.dumps({'error': 'nothing in it but background'}).encode(), 'application/json')
                print(f'  lamp picture: {name}, {im.size[0]} x {im.size[1]}{cut}', flush=True)
                (LIB / name).mkdir(parents=True, exist_ok=True); im.crop(im.getbbox()).save(LIB / name / 'source.png'); (LIB / name / 'lamp.json').unlink(missing_ok=True)
                got = use(name); got['note'] = cut + got.get('note', ''); return self.send(json.dumps(got).encode(), 'application/json')
            L = json.loads(body); raw = json.loads(spec_path.read_text(encoding='utf-8')); raw['light_style'] = L.get('style', 'pixel')
            if L['w'] == 'lamp':
                lp = ([round(float(L['x']), 3), round(max(0.05, float(L['y'])), 3), round(float(L['z']), 3)], round(max(0.005, float(L['r'])), 3))
                pc = L.get('pic'); raw['lamp'] = {'at': lp[0], 'size': lp[1], **({'picture': {'file': pc['file'], 'from': pc.get('from'), 'foot': [round(v, 1) for v in pc['foot']], 'light': [round(v, 1) for v in pc['light']],
                                                                                  'foot0': [round(v, 2) for v in pc['foot0']], 'light0': [round(v, 2) for v in pc['light0']], 'scale': round(float(pc.get('scale') or 1), 2)}} if pc else {})}; raw.pop('shadow', None)
            else: lp = None; raw.pop('lamp', None); raw['shadow'] = L['w']
            dk = round(min(3.0, max(0.3, float(L.get('d', 1)))), 2)
            raw['shadow_strength'] = dk          # (always said: the default is not the same for pixel art and a smooth shadow)
            spec_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            with lock: S.bake(spec_path, L['w'], quiet=True, lamp=lp, prep=prep)
            where = f"a lamp at {lp[0]} m, size {lp[1]} m" if lp else ('the sun' if L['w'] == 'sun' else 'a grey day')
            done = "every side's shadow under " + where + ' - out-pixel/shadow-*.png' + (', and its light on the floor - light-*.png' if lp else '')
            return self.send((f'saved: {done}' + f', at strength {dk:g}' + '; the light is in the spec').encode(), 'text/plain; charset=utf-8')

        def log_message(self, f, *a):          # (only what changes things, and what fails)
            line = f % a
            if 'POST' in line or ' 4' in line[-6:] or ' 5' in line[-6:]: print('  ' + line, flush=True)

        def handle_one_request(self):
            try: super().handle_one_request()
            except (BrokenPipeError, ConnectionResetError): pass          # (the page went on before an answer came: nothing wrong)

    url = f'http://127.0.0.1:{A.port}'; srv = ThreadingHTTPServer(('127.0.0.1', A.port), H); print(f'{url}  (ctrl-c to stop)', flush=True)
    if not A.no_open: webbrowser.open(url)
    srv.serve_forever()


if __name__ == '__main__': main()
