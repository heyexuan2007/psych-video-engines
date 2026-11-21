// ============================================================
// POP 价签引擎：1920×1080 canvas，render(t) 是 t 的纯函数
// 视觉语法：超市手写 POP 海报。每个镜头是一张荧光卡纸；所有东西都是马克笔画的：
//   黑色粗描边 + 填色稍微错位（像随手涂的）+ 填色里有马克笔笔道；暗面用斜线排线。
//   数字是自己画的“泡泡字”（黑描边 + 彩色芯 + 白高光），可以一笔一笔写出来。
//   整幅画面每秒换 8 次轻微扭动（SVG 置换滤镜），像手绘动画的“沸腾线”。
// 页面约定（和 lemo-opuscar 的渲染工具一致）：window.render / DUR / EV / TEXTS / READY
// ============================================================
const QS = new URLSearchParams(location.search);
const W = +(QS.get('w') || 1920), H = +(QS.get('h') || 1080), FPS = 30;
window.DUR = 36.5;

const cv = document.getElementById('cv');
cv.width = W; cv.height = H; document.body.style.width = W + 'px'; document.body.style.height = H + 'px';
const MAIN = cv.getContext('2d');
let ctx = MAIN, T_NOW = 0;

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
  elastic: p => { p = clamp(p); return p === 0 || p === 1 ? p : Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * (2 * Math.PI) / 3) + 1; },
};
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = s + 0x6D2B79F5 | 0; let x = Math.imul(s ^ s >>> 15, 1 | s); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const shakeAt = (t, t0, amp = 10, k = 7) => { const d = t - t0; return d > 0 ? Math.sin(d * 55) * amp * Math.exp(-d * k) : 0; };
const pop = (t, t0, d = 0.22, k = 2.2) => E.back(seg(t, t0, t0 + d), k);

// ---------------- 色板与字体 ----------------
const C = {
  ink: '#171412', paper: '#fffdf5', white: '#fffdf5', cream: '#fff6dc',
  // 荧光卡纸
  Y: '#f8ee3c', O: '#ff8f2e', P: '#ff6eaa', G: '#a9ec46', B: '#4fd5ec', V: '#b88cff',
  // 价格红
  red: '#e8261e', redD: '#b3140f', redL: '#ff5a4a',
  // 角色（chars.js 用到的）
  skin: '#ffd9b8', skinD: '#f0b892', hair: '#2a211c', navy: '#3756a8', blue: '#3f8ef0', teal: '#1fb5a3', mustard: '#ffc533',
  olive: '#7fae3a', gray: '#9a98a2', grayD: '#5b5964', warm: '#ffd36b',
  wood: '#c98a4a', woodD: '#8f5a2c', woodL: '#e0a868', kraft: '#4a3b31', kraftD: '#2e241e',
};
const F = { sans: "'Noto Sans SC','Microsoft YaHei',sans-serif", serif: "'Noto Serif SC','SimSun',serif", lat: "'Arial Black','Arial',sans-serif" };
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }
function mixc(a, b, p) { const x = hexRgb(a), y = hexRgb(b); return '#' + x.map((v, i) => Math.round(lerp(v, y[i], clamp(p))).toString(16).padStart(2, '0')).join(''); }
const lum = (h) => { const [r, g, b] = hexRgb(h); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; };

// ---------------- 整体透明度与镜头 ----------------
let LA = 1;
function layer(a, fn) { if (a <= 0.003) return; const prev = LA; LA = prev * clamp(a); try { fn(); } finally { LA = prev; } }
function camera(cx, cy, s, fn, dx = 0, dy = 0, rot = 0) { ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); if (rot) ctx.rotate(rot); ctx.scale(s, s); ctx.translate(-cx, -cy); try { fn(); } finally { ctx.restore(); } }
function at(x, y, s, rot, fn) { ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot); if (s !== 1) ctx.scale(s, s); try { fn(); } finally { ctx.restore(); } }

// ---------------- 马克笔：描边、错位填色、笔道、排线 ----------------
const MW = 1.55;       // 描边粗细倍数（chars.js 里写的 4.5 → 实际 7）
let FOFF = 6;          // 填色错位（屏幕像素）
let STREAK = null, HATCH = null;
function makeMarker() {
  // 马克笔笔道：斜着的一条条，笔道边缘墨水多一点
  const c = document.createElement('canvas'); c.width = 420; c.height = 420; const g = c.getContext('2d'), r = rng(77);
  g.translate(210, 210); g.rotate(-0.42); g.translate(-420, -420);
  for (let x = 0; x < 840; x += 30 + r() * 10) {
    const w = 34 + r() * 8;
    g.fillStyle = `rgba(0,0,0,${0.035 + r() * 0.03})`; g.fillRect(x, 0, w, 840);
    g.fillStyle = `rgba(0,0,0,${0.07 + r() * 0.05})`; g.fillRect(x, 0, 2.5, 840); g.fillRect(x + w - 2.5, 0, 2.5, 840);
  }
  STREAK = MAIN.createPattern(c, 'repeat');
  const h = document.createElement('canvas'); h.width = 64; h.height = 64; const hg = h.getContext('2d');
  hg.strokeStyle = C.ink; hg.lineWidth = 3.2; hg.lineCap = 'round';
  for (let i = -64; i < 128; i += 16) { hg.beginPath(); hg.moveTo(i, 64); hg.lineTo(i + 64, 0); hg.stroke(); }
  HATCH = MAIN.createPattern(h, 'repeat');
}
function devPattern(p) { try { p.setTransform(ctx.getTransform().inverse()); } catch (e) {} return p; }
function path(pts, close = true) { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); if (close) ctx.closePath(); }
/** 形状：o.w 描边粗细, o.color 描边色, o.stroke=false 不描边, o.shade=[dx,dy] 暗面排线, o.off 填色错位, o.streak=false 不要笔道 */
function shape(build, fill, o = {}) {
  ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1);
  if (fill) {
    const off = o.off ?? FOFF;
    ctx.save();
    if (off) { const m = ctx.getTransform(); ctx.setTransform(1, 0, 0, 1, off * 0.8, off); ctx.transform(m.a, m.b, m.c, m.d, m.e, m.f); }
    ctx.beginPath(); build(); ctx.fillStyle = fill; ctx.fill();
    if (o.streak !== false && STREAK && fill[0] === '#' && fill !== C.skin && lum(fill) < 0.93) { ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = devPattern(STREAK); ctx.fill(); }
    ctx.restore();
  }
  if (o.shade) {
    ctx.save(); ctx.beginPath(); build(); ctx.clip();
    ctx.translate(o.shade[0], o.shade[1]); ctx.beginPath(); build(); ctx.rect(-6000, -6000, 12000, 12000);
    ctx.globalAlpha = LA * (o.alpha ?? 1) * 0.42; ctx.fillStyle = devPattern(HATCH); ctx.fill('evenodd');
    ctx.restore();
  }
  if (o.stroke !== false) { ctx.beginPath(); build(); ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.lineWidth = (o.w ?? 4.5) * MW; ctx.strokeStyle = o.color || C.ink; ctx.stroke(); }
  ctx.restore();
}
const circ = (x, y, r) => () => ctx.arc(x, y, r, 0, Math.PI * 2);
const oval = (x, y, rx, ry, rot = 0) => () => ctx.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot, 0, Math.PI * 2);
const box = (x, y, w, h, r = 0) => () => ctx.roundRect(x, y, w, h, r);
const poly = (pts) => () => pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
function line(pts, o = {}) { ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1); path(pts, false); ctx.lineCap = o.cap || 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = (o.w ?? 4.5) * (o.raw ? 1 : MW); ctx.strokeStyle = o.color || C.ink; if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); ctx.restore(); }
function tube(pts, w, col, o = {}) { line(pts, { w: w + 9 * MW, color: C.ink, alpha: o.alpha, raw: 1 }); line(pts, { w, color: col, alpha: o.alpha, raw: 1 }); }
function qd(p0, c, p1, n = 12) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * p0[0] + 2 * v * u * c[0] + u * u * p1[0], v * v * p0[1] + 2 * v * u * c[1] + u * u * p1[1]]); } return out; }
function bz(p0, c1, c2, p1, n = 16) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * v * p0[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u * u * u * p1[0], v * v * v * p0[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u * u * u * p1[1]]); } return out; }
function arcPts(cx, cy, rx, ry, a0, a1, n = 40) { const out = []; for (let i = 0; i <= n; i++) { const a = lerp(a0, a1, i / n); out.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); } return out; }
/** 折线截到前 p（0..1）那么长 */
function plen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
function cutTo(pts, len) {
  if (len <= 0) return []; const out = [pts[0]]; let L = 0;
  for (let i = 1; i < pts.length; i++) {
    const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (L + d >= len) { const u = (len - L) / d; out.push([lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)]); return out; }
    L += d; out.push(pts[i]);
  }
  return out;
}
/** 马克笔划一道（会写出来）：p 进度 */
function stroke(pts, p, o = {}) { const L = plen(pts); const q = cutTo(pts, L * clamp(p)); if (q.length > 1) line(q, o); }
/** 涂鸦划掉：来回两道红笔 */
function strike(x0, y0, x1, y1, p, o = {}) {
  const col = o.color || C.red, w = o.w ?? 12, gap = o.gap ?? 26;
  const a = [[x0, y0 - gap * 0.4], [x1, y1 - gap * 0.6]], b = [[x1 - 10, y1 + gap * 0.5], [x0 + 16, y0 + gap * 0.7]];
  stroke(a, seg(p, 0, 0.5), { w, color: col }); stroke(b, seg(p, 0.5, 1), { w, color: col });
}

// ---------------- 泡泡数字（自己画的笔画，单位格 110×160） ----------------
const R2 = Math.PI * 2, PI = Math.PI;
const GLYPH = {
  '0': { a: 104, s: [arcPts(55, 80, 31, 57, -PI / 2, PI * 1.5, 48)] },
  '1': { a: 78, s: [[[26, 44], [50, 20], [50, 140]]] },
  '2': { a: 104, s: [[...bz([22, 52], [24, 8], [90, 6], [86, 56]), ...bz([86, 56], [82, 88], [40, 112], [22, 140]).slice(1), [94, 140]]] },
  '3': { a: 104, s: [[...bz([22, 38], [38, 6], [90, 10], [84, 46]), ...bz([84, 46], [80, 72], [60, 78], [48, 78]).slice(1), ...bz([48, 78], [100, 76], [98, 142], [54, 142]).slice(1), ...bz([54, 142], [36, 143], [24, 134], [18, 122]).slice(1)]] },
  '4': { a: 108, s: [[[78, 142], [78, 20], [18, 106], [100, 106]]] },
  '5': { a: 104, s: [[[88, 20], [36, 20], [30, 74], ...bz([30, 74], [50, 58], [94, 62], [90, 104]).slice(1), ...bz([90, 104], [86, 146], [38, 150], [18, 126]).slice(1)]] },
  '6': { a: 104, s: [[...bz([84, 26], [52, 2], [22, 40], [24, 100]), ...arcPts(56, 106, 32, 36, PI, -PI, 40).slice(1)]] },
  '7': { a: 100, s: [[[16, 22], [92, 22], ...bz([92, 22], [72, 58], [54, 100], [50, 142]).slice(1)]] },
  '8': { a: 104, s: [arcPts(55, 46, 25, 27, PI / 2, PI * 2.5, 36), arcPts(55, 109, 31, 33, -PI / 2, PI * 1.5, 40)] },
  '9': { a: 104, s: [[...arcPts(54, 56, 31, 36, 0, -R2, 40), ...bz([85, 56], [88, 112], [70, 142], [28, 140]).slice(1)]] },
  '¥': { a: 104, s: [[[20, 22], [55, 78], [90, 22]], [[55, 78], [55, 146]], [[26, 100], [84, 100]]] },
  '%': { a: 136, s: [arcPts(32, 44, 20, 25, -PI / 2, PI * 1.5, 30), [[108, 18], [30, 144]], arcPts(104, 118, 20, 25, -PI / 2, PI * 1.5, 30)] },
  '.': { a: 46, s: [[[22, 136], [24, 140]]] },
  ' ': { a: 50, s: [] },
  '+': { a: 104, s: [[[55, 44], [55, 124]], [[18, 84], [92, 84]]] },
  '-': { a: 90, s: [[[16, 84], [74, 84]]] },
  '!': { a: 56, s: [[[28, 18], [28, 102]], [[28, 138], [29, 142]]] },
  '?': { a: 96, s: [[...bz([18, 44], [20, 4], [86, 0], [84, 44]), ...bz([84, 44], [82, 70], [48, 72], [48, 104]).slice(1)], [[48, 138], [49, 142]]] },
};
for (const k in GLYPH) GLYPH[k].L = GLYPH[k].s.map(plen);
function numWidth(str, h, sp = -0.04) { const k = h / 160; let w = 0; for (const ch of str) w += ((GLYPH[ch] || GLYPH[' ']).a + sp * 160) * k; return w - sp * 160 * k; }
/**
 * 泡泡数字。(x,y) 基线（字底），h 字高。o: color 芯色, p 写出进度, align, drop 影子, hi 高光, line 描边色, ox 描边粗细倍数
 * 返回总宽
 */
function popNum(str, x, y, h, o = {}) {
  const k = h / 160, sp = o.sp ?? -0.04, total = numWidth(str, h, sp), align = o.align || 'center';
  let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  const strokes = []; let sumL = 0;
  for (const ch of str) {
    const g = GLYPH[ch] || GLYPH[' '];
    g.s.forEach((pts, i) => { strokes.push({ pts: pts.map(([a, b]) => [cx + a * k, y - 160 * k + b * k]), L: g.L[i] * k }); sumL += g.L[i] * k; });
    cx += (g.a + sp * 160) * k;
  }
  const p = o.p ?? 1; let left = sumL * clamp(p);
  const parts = strokes.map(s => { const q = cutTo(s.pts, Math.min(s.L, left)); left -= s.L; return q.length > 1 ? q : (q.length === 1 ? [q[0], [q[0][0] + 0.1, q[0][1]]] : null); }).filter(Boolean);
  if (!parts.length) return total;
  const W1 = (o.ox ?? 1) * 36 * k, W2 = 21 * k, col = o.color || C.red, lc = o.line || C.ink;
  if (o.drop !== false) for (const q of parts) line(q.map(([a, b]) => [a + 7 * k, b + 9 * k]), { w: W1, color: lc, raw: 1, alpha: 0.9 });
  for (const q of parts) line(q, { w: W1, color: lc, raw: 1 });
  for (const q of parts) line(q, { w: W2, color: col, raw: 1 });
  if (o.hi !== false) for (const q of parts) { const L = plen(q); if (L < 20 * k) continue; const a = cutTo(q, L * 0.34), b = cutTo(q, L * 0.1); const hl = a.slice(b.length - 1); if (hl.length > 1) line(hl.map(([u, v]) => [u - 4 * k, v - 4 * k]), { w: 5.5 * k, color: '#ffffff', raw: 1, alpha: 0.85 }); }
  if (o.id && p > 0.9) FRAME_TEXTS.push({ id: o.id, text: str, ...devBox(x - (align === 'center' ? total / 2 : align === 'right' ? total : 0), y - h, total, h) });
  return total;
}

// ---------------- 字 ----------------
// 标记法：{{红字}}、((灰字))、[[白字]]
function parseMarks(str, base) {
  const out = []; let col = base, i = 0;
  while (i < str.length) {
    const two = str.slice(i, i + 2);
    if (two === '{{') { col = C.red; i += 2; continue; } if (two === '((') { col = '#7a746a'; i += 2; continue; } if (two === '[[') { col = C.white; i += 2; continue; }
    if (two === '}}' || two === '))' || two === ']]') { col = base; i += 2; continue; }
    const ch = String.fromCodePoint(str.codePointAt(i)); out.push({ ch, col }); i += ch.length;
  }
  return out;
}
const plain = (str) => str.replace(/\[\[|\]\]|\{\{|\}\}|\(\(|\)\)/g, '');
const FRAME_TEXTS = [];
const fontOf = (size, font, weight) => `${weight} ${size}px ${font}`;
function measure(str, size, font = F.sans, weight = 900, spacing = 0.02) {
  ctx.font = fontOf(size, font, weight); const chars = parseMarks(str, C.ink), ws = chars.map(c => ctx.measureText(c.ch).width);
  return { chars, ws, total: ws.reduce((a, b) => a + b, 0) + size * spacing * Math.max(0, chars.length - 1) };
}
/** 当前坐标下的矩形 → 屏幕坐标外框（给阅读检查用） */
function devBox(x, y, w, h) {
  const m = ctx.getTransform(), pts = [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([a, b]) => [m.a * a + m.c * b + m.e, m.b * a + m.d * b + m.f]);
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}
/**
 * POP 字：每个字随手歪一点、高低不齐。o: size, color 字芯, line 描边色, lw 描边粗细比例(0 不描), sticker 白外边,
 * align, t, t0, cps（逐字蹦出来）, jit 歪的程度, seed, id, alpha, weight, drop 硬影子
 */
function ptxt(str, x, y, o = {}) {
  const { size = 60, color = C.ink, align = 'center', font = F.sans, weight = 900, t = T_NOW, t0 = -99, cps = 0, alpha = 1, id = null, jit = 0.05, seed = 1, spacing = 0.02, lw = 0, line: lc = C.ink, sticker = 0, drop = 0, t1 = 1e9, out = 0.15 } = o;
  ctx.font = fontOf(size, font, weight);
  const chars = parseMarks(str, color), ws = chars.map(c => ctx.measureText(c.ch).width), sp = size * spacing, total = ws.reduce((a, b) => a + b, 0) + sp * Math.max(0, chars.length - 1);
  const fo = 1 - seg(t, t1 - out, t1);
  if (fo <= 0 || t < t0 || alpha <= 0.003) return total;
  const x0 = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  ctx.save(); ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'center'; ctx.font = fontOf(size, font, weight); ctx.lineJoin = 'round';
  let cx = x0; const items = [];
  chars.forEach((c, i) => {
    const s0 = t0 + i * cps, k = cps > 0 ? E.back(seg(t, s0, s0 + 0.16), 2.6) : 1;
    if (k > 0.01 && c.ch !== ' ') items.push({ c, x: cx + ws[i] / 2, k, r: (hash(seed * 13 + i * 7.1) - 0.5) * 2 * jit, dy: (hash(seed * 5 + i * 3.3) - 0.5) * size * 0.08 });
    cx += ws[i] + sp;
  });
  const a = fo * alpha * LA, cy = y - size * 0.36;
  const each = (fn) => items.forEach(it => { ctx.save(); ctx.translate(it.x, cy + it.dy); ctx.rotate(it.r); ctx.scale(it.k, it.k); ctx.translate(0, size * 0.36); fn(it); ctx.restore(); });
  ctx.globalAlpha = a;
  if (sticker) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = size * (lw ? 0.36 : 0.22); each(it => ctx.strokeText(it.c.ch, 0, 0)); }
  if (drop) { ctx.fillStyle = lc; ctx.strokeStyle = lc; ctx.lineWidth = size * lw; each(it => { ctx.translate(size * 0.05, size * 0.06); if (lw) ctx.strokeText(it.c.ch, 0, 0); ctx.fillText(it.c.ch, 0, 0); }); }
  if (lw) { ctx.strokeStyle = lc; ctx.lineWidth = size * lw; each(it => ctx.strokeText(it.c.ch, 0, 0)); }
  each(it => { ctx.fillStyle = it.c.col; ctx.fillText(it.c.ch, 0, 0); });
  ctx.restore();
  if (id && fo > 0.5) FRAME_TEXTS.push({ id, text: plain(str), ...devBox(x0, y - size, total, size * 1.3) });
  return total;
}
/** 小字（标注），不歪 */
function note(str, x, y, o = {}) { return ptxt(str, x, y, { size: 30, weight: 700, jit: 0, ...o }); }

// ---------------- 字幕：价签枪打出来的白标签（抖音安全区：x 134–1594，y 119–929） ----------------
const CAPX = 866, CAPY = 900;
function cap(str, t, a, b, id, o = {}) {
  if (t < a - 0.05 || t > b + 0.2) return;
  const size = o.size || 52, x = o.x ?? CAPX, y = o.y ?? CAPY;
  const { total } = measure(str, size, F.sans, 900), w = total + 84, h = size * 1.62;
  const k = a <= 0 ? 1 : E.back(seg(t, a - 0.05, a + 0.1), 2.2), al = a <= 0 ? 1 - seg(t, b + 0.05, b + 0.2) : Math.min(seg(t, a - 0.05, a + 0.02), 1 - seg(t, b + 0.05, b + 0.2));
  if (al <= 0) return;
  const rot = o.rot ?? (hash(id.length * 3.1 + a) - 0.5) * 0.016;
  layer(al, () => at(x, y - size * 0.34, k, rot, () => {
    shape(box(-w / 2 + 7, -h / 2 + 9, w, h, 14), C.ink, { stroke: false, off: 0, streak: false, alpha: 0.9 });
    shape(box(-w / 2, -h / 2, w, h, 14), C.white, { w: 4.5, off: 0 });
    // 价签枪标签两头的小锯齿
    for (const sx of [-1, 1]) for (let i = 0; i < 4; i++) shape(circ(sx * (w / 2 - 16), -h / 2 + h * (i + 0.5) / 4, 3.2), C.ink, { stroke: false, off: 0, alpha: 0.35 });
    ptxt(str, 0, size * 0.36, { t: 99, t0: 0, size, id, jit: 0.025, seed: id.length + a });
  }));
}

// ---------------- 卡纸背景 ----------------
let BG = C.Y;
/** 整张荧光卡纸 */
function card(col) { BG = col; ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = col; ctx.fillRect(0, 0, W, H); ctx.restore(); }

// ---------------- 镜头合成：沸腾线 + 纸纹 ----------------
function mk() { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; }
const SCN = mk(), BUF = [mk(), mk(), mk()];
let PAPER = null, BOIL = QS.get('boil') !== '0';
function shot(fn, t, target) {
  const s = SCN.getContext('2d'); ctx = s;
  s.setTransform(1, 0, 0, 1, 0, 0); s.globalAlpha = 1; s.globalCompositeOperation = 'source-over'; s.filter = 'none'; s.clearRect(0, 0, W, H);
  LA = 1; BG = C.Y; FOFF = 6;
  fn(t);
  const g = target.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  g.fillStyle = BG; g.fillRect(0, 0, W, H);
  g.filter = BOIL ? `url(#boil${Math.floor(t * 8) % 4})` : 'none';
  g.drawImage(SCN, 0, 0); g.filter = 'none';
  g.globalCompositeOperation = 'multiply'; g.drawImage(PAPER, 0, 0, W, H); g.globalCompositeOperation = 'source-over';
  ctx = MAIN; LA = 1;
  return target;
}
function makePaper() {
  PAPER = document.createElement('canvas'); PAPER.width = 960; PAPER.height = 540; const g = PAPER.getContext('2d'), r = rng(9);
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 960, 540);
  const im = g.getImageData(0, 0, 960, 540);
  for (let i = 0; i < im.data.length; i += 4) { const v = 255 - r() * r() * 26; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; }
  g.putImageData(im, 0, 0);
  // 纸纤维
  g.lineWidth = 0.7;
  for (let i = 0; i < 260; i++) { const x = r() * 960, y = r() * 540, a = r() * 6.28, l = 4 + r() * 14; g.strokeStyle = `rgba(120,110,100,${0.08 + r() * 0.12})`; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + Math.cos(a) * l * 0.5 + 3, y + Math.sin(a) * l * 0.5, x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
  // 卡纸拍照的光：中间亮、四角暗一点
  const v = g.createRadialGradient(400, 230, 120, 480, 270, 620); v.addColorStop(0, 'rgba(255,255,255,0)'); v.addColorStop(1, 'rgba(150,135,120,0.32)');
  g.fillStyle = v; g.fillRect(0, 0, 960, 540);
}

// ---------------- 转场 ----------------
function put(c, a = 1, m = null) { MAIN.setTransform(1, 0, 0, 1, 0, 0); if (m) MAIN.setTransform(m[0], m[1], m[2], m[3], m[4], m[5]); MAIN.globalAlpha = a; MAIN.drawImage(c, 0, 0); MAIN.globalAlpha = 1; MAIN.setTransform(1, 0, 0, 1, 0, 0); }
function veil(a, col = '#000') { if (a <= 0) return; MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = clamp(a); MAIN.fillStyle = col; MAIN.fillRect(0, 0, W, H); MAIN.globalAlpha = 1; }
function tableBg() { MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.fillStyle = C.kraft; MAIN.fillRect(0, 0, W, H); MAIN.globalAlpha = 0.5; MAIN.drawImage(PAPER, 0, 0, W, H); MAIN.globalAlpha = 1; }
function cardShadow(m, a = 0.45) { MAIN.save(); MAIN.setTransform(m[0], m[1], m[2], m[3], m[4] + 14, m[5] + 18); MAIN.globalAlpha = a; MAIN.fillStyle = '#000'; MAIN.filter = 'blur(14px)'; MAIN.fillRect(0, 0, W, H); MAIN.restore(); }
const T = {
  cut(p, A, B) { put(p < 0.5 ? A() : B()); },
  fade(p, A, B) { put(A()); put(B(), E.io(p)); },
  /** 翻卡片：A 绕竖轴转过去，背面就是 B */
  flip(p, A, B) {
    tableBg();
    const q = E.io(p), front = q < 0.5, sx = Math.abs(Math.cos(q * Math.PI)), sc = lerp(1, 0.82, Math.sin(q * Math.PI)), img = front ? A() : B();
    const m = [sx * sc, (front ? -1 : 1) * 0.06 * (1 - sx), 0, sc, W / 2 - W / 2 * sx * sc, H / 2 - H / 2 * sc];
    cardShadow(m, 0.5); put(img, 1, m);
    if (sx < 0.5) { MAIN.save(); MAIN.setTransform(m[0], m[1], m[2], m[3], m[4], m[5]); MAIN.globalAlpha = (0.5 - sx) * 0.7; MAIN.fillStyle = '#000'; MAIN.fillRect(0, 0, W, H); MAIN.restore(); }
  },
  /** 撕页：A 这一页从上面被撕下来飞走，露出下面的 B */
  tear(p, A, B) {
    put(B());
    if (p >= 1) return;
    const q = E.in(p), ang = -0.5 * q, dy = -H * 1.25 * q, dx = W * 0.35 * q;
    const c = Math.cos(ang), s = Math.sin(ang), m = [c, s, -s, c, dx + 60 * q, dy];
    // 撕下来的那页底边是毛的
    const img = A(), g = MAIN; g.save(); g.setTransform(m[0], m[1], m[2], m[3], m[4], m[5]);
    g.filter = 'blur(10px)'; g.globalAlpha = 0.35 * (1 - q); g.fillStyle = '#000'; g.fillRect(12, 16, W, H); g.filter = 'none'; g.globalAlpha = 1;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(W, 0); const r = rng(5); for (let x = W; x >= 0; x -= 24) g.lineTo(x, H - 6 - r() * 18); g.closePath(); g.clip();
    g.drawImage(img, 0, 0); g.restore();
  },
  /** 钻进脑袋：A 往一个点放大，B 从那个点长出来的爆炸贴形状里露出来 */
  burst(p, A, B, o = {}) {
    const x = o.x ?? W / 2, y = o.y ?? H / 2, k = lerp(1, 1.9, E.in(p));
    put(A(), 1, [k, 0, 0, k, x - x * k, y - y * k]);
    const R = 2700 * E.in(seg(p, 0.1, 1));
    if (R < 2) return;
    const img = B(), g = MAIN, n = 14, rr = rng(12), pts = [];
    for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2 + p * 0.7, rad = R * (i % 2 ? 0.72 : 1 + rr() * 0.12); pts.push([x + Math.cos(a) * rad, y + Math.sin(a) * rad]); }
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.beginPath(); pts.forEach(([a, b], i) => i ? g.lineTo(a, b) : g.moveTo(a, b)); g.closePath();
    g.save(); g.clip(); g.drawImage(img, 0, 0); g.restore();
    g.lineWidth = 12; g.strokeStyle = C.ink; g.lineJoin = 'round'; g.stroke(); g.restore();
  },
  /** 啪：B 像一张新海报拍上来（从大到小，带影子） */
  slap(p, A, B) {
    put(A());
    const q = seg(p, 0.15, 1), k = lerp(1.35, 1, E.out(q)), r = lerp(0.07, 0, E.back(q, 2)), a = seg(p, 0.1, 0.3);
    const c = Math.cos(r) * k, s = Math.sin(r) * k, m = [c, s, -s, c, W / 2 - (c * W / 2 - s * H / 2), H / 2 - (s * W / 2 + c * H / 2)];
    if (a > 0) { cardShadow(m, 0.45 * a * (1 - q)); put(B(), a, m); }
  },
  /** 马克笔涂满：一支粗马克笔 Z 字来回涂，涂到的地方变成 B */
  scribble(p, A, B, o = {}) {
    put(A());
    const g = MAIN, n = 7, q = E.io(p), wbr = H / n * 1.9;
    const pts = []; for (let i = 0; i <= n; i++) { const y = -60 + i * (H + 120) / n; pts.push(i % 2 ? [W + 200, y] : [-200, y]); }
    const L = plen(pts), cutp = cutTo(pts, L * q);
    if (cutp.length < 2) return;
    const img = B(); g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
    g.beginPath(); cutp.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.lineWidth = wbr; g.lineCap = 'round'; g.lineJoin = 'round';
    // 先画笔头那一道的颜色（B 的卡纸色），再用它做蒙版贴 B
    const mask = BUF[2].getContext('2d'); mask.setTransform(1, 0, 0, 1, 0, 0); mask.globalCompositeOperation = 'source-over'; mask.clearRect(0, 0, W, H);
    mask.beginPath(); cutp.forEach(([x, y], i) => i ? mask.lineTo(x, y) : mask.moveTo(x, y)); mask.lineWidth = wbr; mask.lineCap = 'round'; mask.lineJoin = 'round'; mask.strokeStyle = '#000'; mask.stroke();
    mask.globalCompositeOperation = 'source-in'; mask.drawImage(img, 0, 0); mask.globalCompositeOperation = 'source-over';
    g.drawImage(BUF[2], 0, 0);
    // 笔头
    const [hx, hy] = cutp[cutp.length - 1];
    g.translate(hx, hy); g.rotate(-0.5);
    if (q < 0.98) {
      const bw = 96, mc = o.col || '#fff'; g.lineJoin = 'round'; g.lineWidth = 7; g.strokeStyle = C.ink;
      g.beginPath(); g.moveTo(-bw * 0.32, -10); g.lineTo(bw * 0.32, -10); g.lineTo(bw * 0.2, -70); g.lineTo(-bw * 0.2, -70); g.closePath(); g.fillStyle = mc; g.fill(); g.stroke();   // 笔头
      g.beginPath(); g.roundRect(-bw / 2, -10, bw, 70, 10); g.fillStyle = mc; g.fill(); g.stroke();                                                                   // 笔口
      g.beginPath(); g.roundRect(-bw / 2, 56, bw, 330, 18); g.fillStyle = '#fffdf5'; g.fill(); g.stroke();                                                            // 笔杆
      g.fillStyle = mc; g.fillRect(-bw / 2 + 4, 150, bw - 8, 60); g.strokeRect(-bw / 2 + 4, 150, bw - 8, 60);
    }
    g.restore();
  },
};

// ---------------- 事件（音效）与场景 ----------------
const EV = []; window.EV = EV;
function ev(t, s, o = {}) { EV.push({ t: +t.toFixed(3), s, ...o }); }
const SCENES = [];
function render(t) {
  T_NOW = t; FRAME_TEXTS.length = 0; LA = 1; ctx = MAIN;
  MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over'; MAIN.filter = 'none';
  MAIN.fillStyle = C.kraft; MAIN.fillRect(0, 0, W, H);
  for (const s of SCENES) if (t >= s.t0 && t < s.t1) { ctx = MAIN; MAIN.save(); s.draw(t); MAIN.restore(); }
  // 字幕最后画（不扭动）
  for (const s of SCENES) if (t >= s.t0 && t < s.t1 && s.caps) { ctx = MAIN; MAIN.save(); MAIN.setTransform(1, 0, 0, 1, 0, 0); s.caps(t); MAIN.restore(); }
}
window.render = render;
window.TEXTS = (t) => { render(t); return FRAME_TEXTS.slice(); };

async function boot() {
  for (const f of ['900 60px "Noto Sans SC"', '700 60px "Noto Sans SC"', '400 60px "Noto Sans SC"', '900 60px "Noto Serif SC"']) { try { await document.fonts.load(f, '原价现价你觉得值吗转盘联合国非洲法官骰子判个月摊主隔壁同款关注0123456789%¥'); } catch (e) {} }
  await document.fonts.ready;
  makeMarker(); makePaper();
  EV.sort((a, b) => a.t - b.t);
  render(parseFloat(new URLSearchParams(location.search).get('t') || '0'));
  window.READY = true;
}
