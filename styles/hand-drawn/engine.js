// ============================================================
// 拟手绘引擎：1920×1080 canvas，render(t) 是 t 的纯函数（任何一帧都能单独渲染）
// 视觉语法：米白纸面 + 铅笔/马克笔抖动线（每秒换 8 次笔迹）+ 蓝红黑三色 + 黄色荧光笔
// 场景文件只用这里的 API；每个场景登记 SCENES.push({ id, t0, t1, draw(t) })
// 页面约定（和 lemo-opuscar 的渲染工具一致）：window.render / DUR / EV / TEXTS / READY
// ============================================================
const QS = new URLSearchParams(location.search);
const W = +(QS.get('w') || 1920), H = +(QS.get('h') || 1080), FPS = 30;
window.DUR = 43.3;

const cv = document.getElementById('cv');
cv.width = W; cv.height = H; document.body.style.width = W + 'px'; document.body.style.height = H + 'px';
const MAIN = cv.getContext('2d');
let ctx = MAIN;

// ---------------- 数学与缓动 ----------------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  out: p => 1 - Math.pow(1 - clamp(p), 3),
  in: p => Math.pow(clamp(p), 3),
  io: p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; },
  sine: p => -(Math.cos(Math.PI * clamp(p)) - 1) / 2,
  back: (p, k = 1.7) => { p = clamp(p) - 1; return 1 + (k + 1) * p * p * p + k * p * p; },
  bounce: p => { p = clamp(p); const n = 7.5625, d = 2.75; if (p < 1 / d) return n * p * p; if (p < 2 / d) return n * (p -= 1.5 / d) * p + .75; if (p < 2.5 / d) return n * (p -= 2.25 / d) * p + .9375; return n * (p -= 2.625 / d) * p + .984375; },
};
const win = (t, a, b, fi = 0.25, fo = 0.25) => Math.min(seg(t, a, a + fi), 1 - seg(t, b - fo, b));
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = s + 0x6D2B79F5 | 0; let x = Math.imul(s ^ s >>> 15, 1 | s); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
function noise(x, seed = 0) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i + seed * 57.3), hash(i + 1 + seed * 57.3), u) * 2 - 1; }
const strHash = (s) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 9973; return h; };

// ---------------- 色板与字体 ----------------
const C = {
  paper: '#f5eedc', paperHi: '#fffaf0', paperLo: '#e4dac2', ink: '#2b2622', pencil: '#6a625a', gray: '#9a938a',
  blue: '#2f66c9', blueL: '#8db4f2', bluePale: '#dbe7fb', red: '#d8443a', redL: '#f29a8e', redPale: '#fbe0db',
  yellow: '#ffd94a', white: '#fffdf6', kraft: '#c9a36b', kraftD: '#a8824c', green: '#4c9a5b', pink: '#f4a6b4',
};
const F = { kai: "'STKaiti','KaiTi','楷体'", wei: "'STXinwei','STKaiti','KaiTi'", lat: "'Arial Black','Arial',sans-serif" };
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }
function mixc(a, b, p) { const x = hexRgb(a), y = hexRgb(b); return '#' + x.map((v, i) => Math.round(lerp(v, y[i], clamp(p))).toString(16).padStart(2, '0')).join(''); }

// ---------------- 整体透明度（可嵌套）与镜头 ----------------
let LA = 1;
function layer(a, fn) { if (a <= 0.003) return; const prev = LA; LA = prev * clamp(a); try { fn(); } finally { LA = prev; } }
function camera(cx, cy, s, fn, dx = 0, dy = 0) { ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(s, s); ctx.translate(-cx, -cy); try { fn(); } finally { ctx.restore(); } }
function at(x, y, s, rot, fn) { ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot); if (s !== 1) ctx.scale(s, s); try { fn(); } finally { ctx.restore(); } }

// ---------------- 纸面 ----------------
let PAPER = null, GRAIN = null;
function makePaper() {
  PAPER = document.createElement('canvas'); PAPER.width = W; PAPER.height = H;
  const g = PAPER.getContext('2d'), r = rng(42);
  g.fillStyle = C.paper; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 26000 * (W * H) / (1920 * 1080); i++) { const d = r() < 0.5; g.fillStyle = d ? `rgba(120,100,70,${0.03 + r() * 0.05})` : `rgba(255,255,255,${0.1 + r() * 0.25})`; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  g.lineCap = 'round';
  for (let i = 0; i < 700; i++) { const x = r() * W, y = r() * H, a = r() * 6.28, l = 6 + r() * 22; g.strokeStyle = `rgba(140,118,84,${0.04 + r() * 0.07})`; g.lineWidth = 0.6 + r(); g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
  const v = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.45, W / 2, H / 2, Math.hypot(W, H) * 0.62);
  v.addColorStop(0, 'rgba(150,120,70,0)'); v.addColorStop(1, 'rgba(150,120,70,0.2)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
  // 颗粒：盖在所有笔迹上面，让色块像干马克笔
  GRAIN = document.createElement('canvas'); GRAIN.width = W; GRAIN.height = H;
  const q = GRAIN.getContext('2d'), r2 = rng(77);
  for (let i = 0; i < 52000 * (W * H) / (1920 * 1080); i++) { q.fillStyle = `rgba(245,238,220,${0.12 + r2() * 0.3})`; q.fillRect(r2() * W, r2() * H, 1 + r2() * 1.6, 1 + r2() * 1.6); }
}
function paper() { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.drawImage(PAPER, 0, 0); ctx.restore(); }

// ---------------- 抖动线 ----------------
let BOIL = 0;   // 每秒换 8 次
function disp(x, y, d, seed, amp) { const b = BOIL * 1.37; return [x + noise(d / 46 + seed * 9.13 + b, seed + 1) * amp, y + noise(d / 46 + seed * 4.71 + b, seed + 2) * amp]; }
/** 把折线细分并加上手抖 */
function wob(pts, seed = 1, amp = 2.4, close = false) {
  const src = close ? pts.concat([pts[0]]) : pts, out = []; let d = 0;
  for (let i = 0; i < src.length; i++) {
    const [x, y] = src[i];
    if (i === 0) { out.push(disp(x, y, 0, seed, amp)); continue; }
    const [px, py] = src[i - 1], L = Math.hypot(x - px, y - py), n = Math.max(1, Math.round(L / 20));
    for (let k = 1; k <= n; k++) { const u = k / n; d += L / n; out.push(disp(lerp(px, x, u), lerp(py, y, u), d, seed, amp)); }
  }
  if (close) out[out.length - 1] = out[0];
  return out;
}
function pathOf(P, p0, p1) {
  let L = 0; const sl = [];
  for (let i = 1; i < P.length; i++) { const l = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); sl.push(l); L += l; }
  const a = L * clamp(p0), b = L * clamp(p1); let acc = 0, started = false;
  ctx.beginPath();
  for (let i = 1; i < P.length; i++) {
    const l = sl[i - 1] || 1e-6, s0 = acc, s1 = acc + l; acc = s1;
    if (s1 < a) continue; if (s0 > b) break;
    const u0 = clamp((a - s0) / l), u1 = clamp((b - s0) / l);
    if (!started) { ctx.moveTo(lerp(P[i - 1][0], P[i][0], u0), lerp(P[i - 1][1], P[i][1], u0)); started = true; }
    ctx.lineTo(lerp(P[i - 1][0], P[i][0], u1), lerp(P[i - 1][1], P[i][1], u1));
  }
  return started;
}
/** 折线上 p 处的点 */
function along(pts, p) {
  let L = 0; const sl = [];
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); sl.push(l); L += l; }
  let left = L * clamp(p);
  for (let i = 1; i < pts.length; i++) { if (left <= sl[i - 1]) { const u = left / (sl[i - 1] || 1); return [lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)]; } left -= sl[i - 1]; }
  return pts[pts.length - 1];
}
/**
 * 手绘笔画。pts: [[x,y],...]
 * o: color, w(线宽), p(画到哪 0..1), p0, seed, amp, close, fill(颜色), fa, alpha, dbl(复描一遍), stroke(false 只填色), off(填色错位), cap
 */
function sk(pts, o = {}) {
  const { color = C.ink, w = 5, p = 1, p0 = 0, seed = 1, amp = 2.4, close = false, fill = null, fa = 1, alpha = 1, dbl = true, stroke = true, off = [2.5, 2.5], cap = 'round', comp = null } = o;
  if (alpha <= 0.003 || p <= 0 || pts.length < 2) return;
  ctx.save();
  if (comp) ctx.globalCompositeOperation = comp;
  if (fill) {
    const a = fa * alpha * (stroke ? seg(p, 0.55, 1) : 1);
    if (a > 0.003) {
      const Fp = wob(pts, seed + 31, amp * 1.4, true);
      ctx.globalAlpha = a * LA; ctx.fillStyle = fill; ctx.beginPath();
      Fp.forEach(([x, y], i) => i ? ctx.lineTo(x + off[0], y + off[1]) : ctx.moveTo(x + off[0], y + off[1]));
      ctx.closePath(); ctx.fill();
    }
  }
  if (stroke && w > 0) {
    ctx.lineCap = cap; ctx.lineJoin = 'round'; ctx.strokeStyle = color;
    ctx.globalAlpha = alpha * LA; ctx.lineWidth = w;
    if (pathOf(wob(pts, seed, amp, close), p0, p)) ctx.stroke();
    if (dbl) { ctx.globalAlpha = alpha * LA * 0.4; ctx.lineWidth = Math.max(1.2, w * 0.4); if (pathOf(wob(pts, seed + 57, amp * 1.5, close), p0, p)) ctx.stroke(); }
  }
  ctx.restore();
}
/** 带描边的粗管子（胳膊、腿、象鼻）：先画墨线再画里面的颜色，两遍用同一个抖动 */
function tube(pts, w, color, o = {}) {
  const { seed = 1, amp = 2, lw = 5, alpha = 1, p = 1 } = o;
  sk(pts, { w: w, color: C.ink, seed, amp, dbl: false, alpha, p });
  sk(pts, { w: w - lw * 2, color, seed, amp, dbl: false, alpha, p });
}

// ---------------- 形状点列 ----------------
function ell(cx, cy, rx, ry, n = 30, rot = 0, a0 = 0, a1 = Math.PI * 2) {
  const out = [], c = Math.cos(rot), s = Math.sin(rot);
  for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n, x = Math.cos(a) * rx, y = Math.sin(a) * ry; out.push([cx + x * c - y * s, cy + x * s + y * c]); }
  if (Math.abs(a1 - a0 - Math.PI * 2) < 1e-6) out.pop();
  return out;
}
function rr(x, y, w, h, r = 12, n = 5) {
  const out = [], corner = (cx, cy, a0) => { for (let i = 0; i <= n; i++) { const a = a0 + Math.PI / 2 * i / n; out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } };
  corner(x + w - r, y + r, -Math.PI / 2); corner(x + w - r, y + h - r, 0); corner(x + r, y + h - r, Math.PI / 2); corner(x + r, y + r, Math.PI);
  return out;
}
function bz(p0, c1, c2, p1, n = 16) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * v * p0[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u * u * u * p1[0], v * v * v * p0[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u * u * u * p1[1]]); } return out; }
function qd(p0, c, p1, n = 12) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * p0[0] + 2 * v * u * c[0] + u * u * p1[0], v * v * p0[1] + 2 * v * u * c[1] + u * u * p1[1]]); } return out; }
/** 放射短线（撞击、惊讶、庆祝） */
function burst(cx, cy, r0, r1, n, o = {}) {
  const { seed = 5, a0 = 0, a1 = Math.PI * 2, p = 1 } = o;
  for (let i = 0; i < n; i++) { const a = a0 + (a1 - a0) * (i + 0.5) / n + (hash(seed + i) - 0.5) * 0.25, k = 0.8 + hash(seed * 3 + i) * 0.4; sk([[cx + Math.cos(a) * r0, cy + Math.sin(a) * r0], [cx + Math.cos(a) * lerp(r0, r1 * k, p), cy + Math.sin(a) * lerp(r0, r1 * k, p)]], { ...o, seed: seed + i, p: 1, dbl: false }); }
}
/** 蜡笔来回涂满一个形状：clip 到形状里，之字形笔画按 p 推进 */
function scribble(shape, color, p, o = {}) {
  const { seed = 9, gap = 26, w = 34, alpha = 0.82, ang = -0.5 } = o;
  if (p <= 0) return;
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const [x, y] of shape) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.hypot(x1 - x0, y1 - y0) / 2 + 20, pts = [], c = Math.cos(ang), s = Math.sin(ang);
  for (let k = 0, v = -R; v <= R; v += gap, k++) { const u = (k % 2 ? 1 : -1) * R; pts.push([cx + u * c - v * s, cy + u * s + v * c]); }
  ctx.save(); ctx.beginPath(); shape.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.clip();
  sk(pts, { color, w, p, seed, amp: 7, alpha, dbl: false, cap: 'round' });
  sk(pts, { color, w: w * 0.5, p, seed: seed + 3, amp: 12, alpha: alpha * 0.5, dbl: false });
  ctx.restore();
}
/** 荧光笔划一道 */
function hlStroke(x0, y, x1, p, o = {}) { sk([[x0, y], [x1, y + (o.dy || 0)]], { color: o.color || C.yellow, w: o.w || 34, p, seed: o.seed || 4, amp: 3, alpha: o.alpha ?? 0.75, dbl: false, cap: 'butt', comp: 'multiply' }); }
/** 红笔圈一圈（多画一小段，像真的手圈） */
function circleMark(cx, cy, rx, ry, p, o = {}) {
  const pts = []; const n = 44, turns = 1.13;
  for (let i = 0; i <= n; i++) { const u = i / n, a = -2.2 + u * turns * Math.PI * 2, k = 1 + u * 0.07; pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]); }
  sk(pts, { color: o.color || C.red, w: o.w || 7, p, seed: o.seed || 6, amp: 4 });
}

// ---------------- 手写字 ----------------
// 标记法：[[荧光笔划线]]、{{红字}}、<<蓝字>>、((灰字))
function parseMarks(str, base) {
  const out = []; let col = base, hl = false, i = 0;
  while (i < str.length) {
    const two = str.slice(i, i + 2);
    if (two === '[[') { hl = true; i += 2; continue; } if (two === ']]') { hl = false; i += 2; continue; }
    if (two === '{{') { col = C.red; i += 2; continue; } if (two === '<<') { col = C.blue; i += 2; continue; } if (two === '((') { col = C.gray; i += 2; continue; }
    if (two === '}}' || two === '>>' || two === '))') { col = base; i += 2; continue; }
    const ch = String.fromCodePoint(str.codePointAt(i)); out.push({ ch, col, hl }); i += ch.length;
  }
  return out;
}
const plain = (str) => str.replace(/\[\[|\]\]|\{\{|\}\}|<<|>>|\(\(|\)\)/g, '');
const FRAME_TEXTS = [];
function hwMeasure(str, size, font = F.kai, spacing = 0.02, base = C.ink) {
  ctx.font = `${size}px ${font}`; const chars = parseMarks(str, base), ws = chars.map(c => ctx.measureText(c.ch).width);
  return { chars, ws, total: ws.reduce((a, b) => a + b, 0) + size * spacing * Math.max(0, chars.length - 1) };
}
/**
 * 手写字：逐字写出来，每个字有一点歪、一点高低。
 * o: size, color, align, font, t, t0, t1, cps(每字间隔秒), out, alpha, id, bold(0..2), seed, rot, spacing
 */
function hw(str, x, y, o = {}) {
  const { size = 60, color = C.ink, align = 'center', font = F.kai, t = 0, t0 = -99, t1 = 1e9, cps = 0.03, out = 0.18, alpha = 1, id = null, bold = 1, seed = 3, rot = 0, spacing = 0.02 } = o;
  const { chars, ws, total } = hwMeasure(str, size, font, spacing, color);
  const fo = 1 - seg(t, t1 - out, t1);
  if (fo <= 0 || t < t0 || alpha <= 0.003) return total;
  const sp = size * spacing, x0 = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  ctx.save();
  if (rot) { ctx.translate(x, y); ctx.rotate(rot); ctx.translate(-x, -y); }
  ctx.textBaseline = 'alphabetic'; ctx.lineJoin = 'round';
  // 荧光笔：一段连续的 hl 字画一道
  let cx = x0, run = null; const runs = [];
  chars.forEach((c, i) => { if (c.hl) { if (!run) { run = { a: cx, i0: i }; runs.push(run); } run.b = cx + ws[i]; run.i1 = i; } else run = null; cx += ws[i] + sp; });
  for (const r of runs) { const s = t0 + r.i1 * cps + 0.12, p = E.out(seg(t, s, s + 0.3)); if (p > 0) layer(fo * alpha, () => hlStroke(r.a - size * 0.08, y - size * 0.3, r.b + size * 0.08, p, { w: size * 0.62, seed: seed + r.i0, dy: -size * 0.03 })); }
  cx = x0;
  chars.forEach((c, i) => {
    const s = t0 + i * cps, p = E.back(seg(t, s, s + 0.14)), a = seg(t, s, s + 0.06) * fo * alpha, w = ws[i];
    if (a > 0.004) {
      const jx = (hash(seed * 3.1 + i) - 0.5) * size * 0.05, jy = (hash(seed * 5.3 + i * 1.7) - 0.5) * size * 0.08 + (hash(i * 3.7 + BOIL * 1.3 + seed) - 0.5) * 1.6, r = (hash(seed * 7.7 + i * 2.3) - 0.5) * 0.08;
      ctx.save(); ctx.translate(cx + w / 2 + jx, y + jy); ctx.rotate(r); const k = 0.55 + 0.45 * p; ctx.scale(k, k);
      ctx.globalAlpha = a * LA; ctx.font = `${size}px ${font}`; ctx.fillStyle = c.col; ctx.fillText(c.ch, -w / 2, 0);
      if (bold > 0) { ctx.strokeStyle = c.col; ctx.lineWidth = size * 0.032 * bold; ctx.strokeText(c.ch, -w / 2, 0); }
      ctx.restore();
    }
    cx += w + sp;
  });
  ctx.restore();
  if (id && fo > 0.5) FRAME_TEXTS.push({ id, text: plain(str), x0, y0: y - size, x1: x0 + total, y1: y + size * 0.3 });
  return total;
}

// ---------------- 字幕条：一张贴在纸上的小纸条（抖音安全区内：x 134–1594，y 119–929） ----------------
const CAPX = 866, CAPY = 846;
function cap(str, t, a, b, id, o = {}) {
  if (t < a - 0.1 || t > b + 0.25) return;
  const size = o.size || 62, x = o.x ?? CAPX, y = o.y ?? CAPY, sd = strHash(id);
  const { total } = hwMeasure(str, size), pad = 46, w = total + pad * 2, h = size * 1.5;
  const al = Math.min(seg(t, a - 0.1, a + 0.02), 1 - seg(t, b + 0.05, b + 0.25)), pin = E.back(seg(t, a - 0.1, a + 0.12));
  const rot = (hash(sd) - 0.5) * 0.025;
  layer(al, () => at(x, y - size * 0.32, 0.9 + 0.1 * pin, rot, () => {
    sk(rr(-w / 2 + 7, -h / 2 + 9, w, h, 10), { fill: 'rgba(60,45,25,0.16)', stroke: false, seed: sd, amp: 1.5, off: [0, 0] });
    sk(rr(-w / 2, -h / 2, w, h, 10), { fill: C.paperHi, color: C.ink, w: 3.2, seed: sd, amp: 1.8, close: true, off: [0, 0] });
    // 两段胶带
    for (const sx of [-1, 1]) at(sx * (w / 2 - 30), -h / 2 + 2, 1, sx * -0.5, () => sk(rr(-34, -11, 68, 22, 2), { fill: 'rgba(255,217,74,0.6)', stroke: false, seed: sd + sx, amp: 1, off: [0, 0] }));
  }));
  hw(str, x, y, { t, t0: a, t1: b + 0.25, size, id, seed: sd, rot, cps: 0.028 });
}
/** 角落小字（来源、日期）：不进字幕、不进阅读检查 */
function note(str, x, y, o = {}) { hw(str, x, y, { size: 28, color: C.pencil, align: 'left', bold: 0.6, cps: 0, ...o }); }

// ---------------- 离屏缓冲与转场 ----------------
const BUF = [];
function buf(i) { if (!BUF[i]) { const c = document.createElement('canvas'); c.width = W; c.height = H; BUF[i] = c; } return BUF[i]; }
function into(c, fn) { const prev = ctx; ctx = c.getContext('2d'); ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; try { fn(); } finally { ctx.restore(); ctx = prev; } }
/** 只在 maskFn 画过的地方露出 drawB */
function masked(drawB, maskFn) {
  const m = buf(1), b = buf(0);
  into(m, () => { ctx.clearRect(0, 0, W, H); maskFn(); });
  into(b, () => { ctx.clearRect(0, 0, W, H); drawB(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'destination-in'; ctx.drawImage(m, 0, 0); });
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.drawImage(b, 0, 0); ctx.restore();
}
const TEAR = (() => { const r = rng(88), pts = []; for (let y = -40; y <= 1120; y += 58) pts.push([(r() - 0.5) * 90, y]); return pts; })();
const T = {
  /** 橡皮擦：之字形擦掉旧画面 */
  erase(p, A, B) {
    A(); if (p <= 0) return;
    const path = []; for (let k = 0; k < 6; k++) { const y = -60 + k * 240; path.push(k % 2 ? [W + 160, y - 60] : [-160, y + 60]); } path.push([W / 2, H + 260]);
    const q = E.io(p);
    masked(B, () => sk(path, { color: '#000', w: 330, p: q, seed: 2, amp: 14, dbl: false }));
    if (p < 0.97) { const [ex, ey] = along(path, q); at(ex, ey, 1, 0.5 + Math.sin(p * 40) * 0.12, () => { sk(rr(-70, -40, 140, 80, 14), { fill: C.pink, color: C.ink, w: 5, seed: 3, close: true }); sk(rr(-70, -40, 56, 80, 10), { fill: C.blueL, color: C.ink, w: 4, seed: 4, close: true }); }); }
  },
  pushL(p, A, B) { const e = E.io(p); ctx.save(); ctx.translate(-W * e, 0); A(); ctx.restore(); if (p > 0) { ctx.save(); ctx.translate(W * (1 - e), 0); B(); ctx.restore(); } },
  pushU(p, A, B) { const e = E.io(p); ctx.save(); ctx.translate(0, -H * e); A(); ctx.restore(); if (p > 0) { ctx.save(); ctx.translate(0, H * (1 - e)); B(); ctx.restore(); } },
  /** 翻页：从右往左揭开 */
  peel(p, A, B) {
    if (p <= 0) { A(); return; }
    const e = E.io(p), xe = lerp(W + 320, -420, e), sl = 230, curl = 60 + 150 * Math.sin(Math.PI * e);
    B();
    ctx.save(); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(xe + sl, 0); ctx.lineTo(xe - sl, H); ctx.lineTo(0, H); ctx.closePath(); ctx.clip(); A(); ctx.restore();
    // 卷起来的纸背和影子
    ctx.save();
    const g2 = ctx.createLinearGradient(xe + curl, 0, xe + curl + 160, 0); g2.addColorStop(0, 'rgba(60,45,25,0.28)'); g2.addColorStop(1, 'rgba(60,45,25,0)');
    ctx.fillStyle = g2; ctx.beginPath(); ctx.moveTo(xe + sl + curl, 0); ctx.lineTo(xe + sl + curl + 160, 0); ctx.lineTo(xe - sl + curl + 160, H); ctx.lineTo(xe - sl + curl, H); ctx.closePath(); ctx.fill();
    const g = ctx.createLinearGradient(xe, 0, xe + curl, 0); g.addColorStop(0, C.paperLo); g.addColorStop(0.45, C.paperHi); g.addColorStop(1, '#d9cdb2');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(xe + sl, 0); ctx.lineTo(xe + sl + curl, 0); ctx.lineTo(xe - sl + curl, H); ctx.lineTo(xe - sl, H); ctx.closePath(); ctx.fill();
    ctx.restore();
    sk([[xe + sl, -10], [xe - sl, H + 10]], { w: 3.5, seed: 12, amp: 2 }); sk([[xe + sl + curl, -10], [xe - sl + curl, H + 10]], { w: 3.5, seed: 13, amp: 2 });
  },
  /** 撕开：沿中间的裂缝撕成两半 */
  tear(p, A, B, o = {}) {
    if (p <= 0) { A(); return; }
    const cx = o.x ?? W / 2, e = E.in(p), d = e * W * 0.62, line = TEAR.map(([x, y]) => [cx + x, y]);
    B();
    for (const sgn of [-1, 1]) {
      ctx.save(); ctx.translate(sgn * d, e * 60); ctx.translate(cx, H / 2); ctx.rotate(sgn * e * 0.07); ctx.translate(-cx, -H / 2);
      ctx.save(); ctx.beginPath(); ctx.moveTo(sgn < 0 ? -400 : W + 400, -200); line.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(sgn < 0 ? -400 : W + 400, H + 200); ctx.closePath(); ctx.clip(); A(); ctx.restore();
      ctx.strokeStyle = C.white; ctx.lineWidth = 12; ctx.lineJoin = 'round'; ctx.beginPath(); line.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
      ctx.strokeStyle = C.pencil; ctx.lineWidth = 2.5; ctx.beginPath(); line.forEach(([x, y], i) => i ? ctx.lineTo(x + sgn * 5, y) : ctx.moveTo(x + sgn * 5, y)); ctx.stroke();
      ctx.restore();
    }
  },
  /** 手画的圆圈展开 */
  iris(p, A, B, o = {}) {
    A(); if (p <= 0) return;
    const cx = o.x ?? W / 2, cy = o.y ?? H / 2, R = Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) + 60, r = E.io(p) * R;
    masked(B, () => sk(ell(cx, cy, r, r, 40), { fill: '#000', stroke: false, seed: 15, amp: 10, off: [0, 0] }));
    sk(ell(cx, cy, r, r, 40), { w: 7, seed: 15, amp: 10, close: true, alpha: 1 - seg(p, 0.8, 1) });
  },
  /** 蓝红两色马克笔刷满再刷开 */
  marker(p, A, B) {
    const N = 6, bands = (k) => [[-200, H * (k + 0.5) / N + 90], [W + 200, H * (k + 0.5) / N - 90]];
    if (p < 0.5) { A(); const q = p / 0.5; for (let k = 0; k < N; k++) { const pk = E.io(clamp(q * 1.5 - k * 0.1)); sk(k % 2 ? bands(k).reverse() : bands(k), { color: k % 2 ? C.red : C.blue, w: H / N + 60, p: pk, seed: 20 + k, amp: 8, dbl: false, cap: 'butt' }); } }
    else { B(); const q = (p - 0.5) / 0.5; for (let k = 0; k < N; k++) { const pk = E.io(clamp(q * 1.5 - k * 0.1)); if (pk < 1) sk(k % 2 ? bands(k).reverse() : bands(k), { color: k % 2 ? C.red : C.blue, w: H / N + 60, p0: pk, p: 1, seed: 20 + k, amp: 8, dbl: false, cap: 'butt' }); } }
  },
  /** 便签本往上翻一页 */
  flipUp(p, A, B) {
    if (p <= 0) { A(); return; }
    const e = E.in(p), sy = Math.cos(e * Math.PI / 2);
    B();
    const g = ctx.createLinearGradient(0, H * sy, 0, H * sy + 140); g.addColorStop(0, `rgba(60,45,25,${0.3 * (1 - e)})`); g.addColorStop(1, 'rgba(60,45,25,0)'); ctx.fillStyle = g; ctx.fillRect(0, H * sy, W, 140);
    if (sy > 0.01) { ctx.save(); ctx.transform(1, 0, -0.12 * e, sy, 0.12 * e * 300, 0); A(); ctx.fillStyle = `rgba(60,45,25,${0.3 * e})`; ctx.fillRect(-200, 0, W + 400, H); ctx.restore(); sk([[0, H * sy], [W, H * sy]], { w: 4, seed: 17, amp: 2 }); }
  },
  /** 铅笔排线越排越密，露出新画面 */
  hatch(p, A, B) {
    A(); if (p <= 0) return;
    const N = 30, gap = (W + H) / N;
    masked(B, () => { for (let i = 0; i < N + 2; i++) { const wk = clamp(p * 1.7 - (i / N) * 0.7) * gap * 1.25; if (wk > 0.5) { const x = i * gap; sk([[x, -40], [x - H - 80, H + 40]], { color: '#000', w: wk, seed: 30 + i, amp: 6, dbl: false, cap: 'butt' }); } } });
  },
};

// ---------------- 事件（音效）与场景 ----------------
const EV = []; window.EV = EV;
function ev(t, s, o = {}) { EV.push({ t: +t.toFixed(3), s, ...o }); }
const SCENES = [];

function render(t) {
  BOIL = Math.floor(t * 8 + 1e-6);
  FRAME_TEXTS.length = 0; LA = 1; ctx = MAIN;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  paper();
  for (const s of SCENES) if (t >= s.t0 && t < s.t1) { ctx.save(); s.draw(t); ctx.restore(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; }
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.drawImage(GRAIN, 0, 0);
}
window.render = render;
window.TEXTS = (t) => { render(t); return FRAME_TEXTS.slice(); };

async function boot() {
  for (const f of ['60px STKaiti', '60px STXinwei', '60px KaiTi']) { try { await document.fonts.load(f, '美国民主党共和党0123456789AI'); } catch (e) {} }
  await document.fonts.ready;
  makePaper();
  EV.sort((a, b) => a.t - b.t);
  render(parseFloat(new URLSearchParams(location.search).get('t') || '0'));
  window.READY = true;
}
