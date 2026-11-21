// ============================================================
// 档案胶片引擎：1920×1080 canvas，render(t) 是 t 的纯函数
// 视觉语法：1961 年的实验录像。每个镜头先画“实物”层（正常颜色），合成时整体去色成棕黑、
// 加对比和闪烁；只有 red() 发光层里的东西（电压、红灯、转账按钮）保留红色，并带一圈胶片晕光。
// 最后叠胶片：颗粒（24 格/秒换一次）、划痕、灰尘毛发、片门抖动、暗角、圆角片框。
// 页面约定（和 lemo-opuscar 的渲染工具一致）：window.render / DUR / EV / TEXTS / READY
// ============================================================
const QS = new URLSearchParams(location.search);
const W = +(QS.get('w') || 1920), H = +(QS.get('h') || 1080), FPS = 30;
window.DUR = 35;

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
};
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = s + 0x6D2B79F5 | 0; let x = Math.imul(s ^ s >>> 15, 1 | s); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const shakeAt = (t, t0, amp = 10, k = 7) => { const d = t - t0; return d > 0 ? Math.sin(d * 55) * amp * Math.exp(-d * k) : 0; };

// ---------------- 色板与字体 ----------------
// 实物层照常用色，合成时会被去色；RED 系列只在 red() 层里用
const C = {
  ink: '#1b1512', cream: '#f2e6cc', white: '#fffaf0', paper: '#efe3c8', warm: '#ffd36b', beam: '#ffe6ad', amber: '#ffb347',
  red: '#e8322a', redD: '#9c1a16', redL: '#ff6a55',
  wood: '#7a5234', woodD: '#4e3220', woodL: '#9a6a44', metal: '#9aa0a2', metalD: '#5d6264', metalL: '#c8cdcd', bake: '#3a3633',
  skin: '#f4d3b5', skinD: '#ddae86', hair: '#2b211b', navy: '#26355e', blue: '#4b7bd6', teal: '#2f9e94', mustard: '#e6b23a',
  olive: '#7b8a45', gray: '#8c8a92', grayD: '#55535c', wall: '#b9ad97', floor: '#6d5a45',
  // 去色后屏幕上的字色（画在 red() 层或字幕里，不被去色）
  sep: '#efe0c2', sepD: '#8a7a62',
};
const F = { serif: "'Noto Serif SC','STZhongsong','SimSun',serif", sans: "'Noto Sans SC','Microsoft YaHei',sans-serif", mono: "'Courier New','Courier',monospace", lat: "'Arial Black','Arial',sans-serif" };
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }
function mixc(a, b, p) { const x = hexRgb(a), y = hexRgb(b); return '#' + x.map((v, i) => Math.round(lerp(v, y[i], clamp(p))).toString(16).padStart(2, '0')).join(''); }

// ---------------- 整体透明度与镜头 ----------------
let LA = 1;
function layer(a, fn) { if (a <= 0.003) return; const prev = LA; LA = prev * clamp(a); try { fn(); } finally { LA = prev; } }
function camera(cx, cy, s, fn, dx = 0, dy = 0) { ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(s, s); ctx.translate(-cx, -cy); try { fn(); } finally { ctx.restore(); } }
function at(x, y, s, rot, fn) { ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot); if (s !== 1) ctx.scale(s, s); try { fn(); } finally { ctx.restore(); } }

// ---------------- 基本形状 ----------------
function path(pts, close = true) { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); if (close) ctx.closePath(); }
function shape(build, fill, o = {}) {
  ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1);
  ctx.beginPath(); build();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (o.shade) { ctx.save(); ctx.clip(); ctx.fillStyle = 'rgba(20,10,30,0.18)'; ctx.translate(o.shade[0], o.shade[1]); ctx.beginPath(); build(); ctx.rect(-4000, -4000, 8000, 8000); ctx.fill('evenodd'); ctx.restore(); }
  if (o.stroke !== false) { ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.lineWidth = o.w ?? 4.5; ctx.strokeStyle = o.color || C.ink; ctx.stroke(); }
  ctx.restore();
}
const circ = (x, y, r) => () => ctx.arc(x, y, r, 0, Math.PI * 2);
const oval = (x, y, rx, ry, rot = 0) => () => ctx.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2);
const box = (x, y, w, h, r = 0) => () => ctx.roundRect(x, y, w, h, r);
const poly = (pts) => () => pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
function line(pts, o = {}) { ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1); path(pts, false); ctx.lineCap = o.cap || 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = o.w ?? 4.5; ctx.strokeStyle = o.color || C.ink; if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); ctx.restore(); }
function tube(pts, w, col, o = {}) { line(pts, { w: w + 9, color: C.ink, alpha: o.alpha }); line(pts, { w, color: col, alpha: o.alpha }); }
function qd(p0, c, p1, n = 12) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * p0[0] + 2 * v * u * c[0] + u * u * p1[0], v * v * p0[1] + 2 * v * u * c[1] + u * u * p1[1]]); } return out; }
function bz(p0, c1, c2, p1, n = 16) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * v * p0[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u * u * u * p1[0], v * v * v * p0[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u * u * u * p1[1]]); } return out; }

// ---------------- 镜头合成：实物层去色 + 红色层 ----------------
function mk() { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; }
const SCN = mk(), RED = mk(), BUF = [mk(), mk()];
let REDS = [], LIGHTS = [];
/** 红色层：画在去色之后，保留颜色并带晕光（电压、红灯、按钮、红字） */
function red(fn) { REDS.push({ m: ctx.getTransform(), la: LA, fn }); }
/** 局部提亮（台灯、手机屏）：去色后叠加，椭圆 */
function glowLight(x, y, rx, ry, o = {}) { LIGHTS.push({ m: ctx.getTransform(), x, y, rx, ry, i: o.i ?? 1, col: o.col || '#fff1d6' }); }
let TONE = { sepia: 0.75, contrast: 1.18, bright: 1 };
function shot(fn, t, target) {
  const s = SCN.getContext('2d'); ctx = s;
  s.setTransform(1, 0, 0, 1, 0, 0); s.globalAlpha = 1; s.globalCompositeOperation = 'source-over'; s.clearRect(0, 0, W, H);
  REDS = []; LIGHTS = []; LA = 1; TONE = { sepia: 0.75, contrast: 1.18, bright: 1 };
  fn(t);
  const g = target.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  g.fillStyle = '#120e0b'; g.fillRect(0, 0, W, H);
  // 胶片闪烁：亮度每格轻微变化
  const fr = Math.floor(t * 24), fl = 1 + (hash(fr * 3.7) - 0.5) * 0.06;
  g.filter = `grayscale(1) sepia(${TONE.sepia}) contrast(${TONE.contrast}) brightness(${(TONE.bright * fl).toFixed(3)})`;
  g.drawImage(SCN, 0, 0); g.filter = 'none';
  g.globalCompositeOperation = 'screen';
  for (const L of LIGHTS) { g.setTransform(L.m); g.save(); g.translate(L.x, L.y); g.scale(L.rx, L.ry); const gr = g.createRadialGradient(0, 0, 0, 0, 0, 1); gr.addColorStop(0, rgba(L.col, 0.55 * L.i)); gr.addColorStop(1, rgba(L.col, 0)); g.fillStyle = gr; g.beginPath(); g.arc(0, 0, 1, 0, Math.PI * 2); g.fill(); g.restore(); }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
  // 红色层：先画到 RED，再“晕光”叠一遍模糊版本
  if (REDS.length) {
    const r = RED.getContext('2d'); r.setTransform(1, 0, 0, 1, 0, 0); r.clearRect(0, 0, W, H); ctx = r;
    for (const o of REDS) { r.save(); r.setTransform(o.m); LA = o.la; try { o.fn(); } finally { r.restore(); } }
    LA = 1; r.setTransform(1, 0, 0, 1, 0, 0);
    g.globalCompositeOperation = 'screen'; g.filter = 'blur(18px)'; g.globalAlpha = 0.8; g.drawImage(RED, 0, 0); g.filter = 'none'; g.globalAlpha = 1;
    g.globalCompositeOperation = 'source-over'; g.drawImage(RED, 0, 0);
  }
  ctx = MAIN; LA = 1;
  return target;
}

// ---------------- 字 ----------------
// 标记法：{{红字}}、((灰字))、[[米白]]
function parseMarks(str, base) {
  const out = []; let col = base, i = 0;
  while (i < str.length) {
    const two = str.slice(i, i + 2);
    if (two === '{{') { col = C.red; i += 2; continue; } if (two === '((') { col = C.sepD; i += 2; continue; } if (two === '[[') { col = C.white; i += 2; continue; }
    if (two === '}}' || two === '))' || two === ']]') { col = base; i += 2; continue; }
    const ch = String.fromCodePoint(str.codePointAt(i)); out.push({ ch, col }); i += ch.length;
  }
  return out;
}
const plain = (str) => str.replace(/\[\[|\]\]|\{\{|\}\}|\(\(|\)\)/g, '');
const FRAME_TEXTS = [];
const fontOf = (size, font, weight) => `${weight} ${size}px ${font}`;
function measure(str, size, font = F.sans, weight = 700, spacing = 0.03) {
  ctx.font = fontOf(size, font, weight); const chars = parseMarks(str, C.cream), ws = chars.map(c => ctx.measureText(c.ch).width);
  return { chars, ws, total: ws.reduce((a, b) => a + b, 0) + size * spacing * Math.max(0, chars.length - 1) };
}
/** 字：逐字打出来（像打字机，一格一格跳，不浮动）。o: size, color, align, font, weight, t, t0, t1, cps, out, alpha, id, rot, spacing, shadow */
function txt(str, x, y, o = {}) {
  const { size = 60, color = C.cream, align = 'center', font = F.sans, weight = 700, t = T_NOW, t0 = -99, t1 = 1e9, cps = 0.03, out = 0.2, alpha = 1, id = null, rot = 0, spacing = 0.03, shadow = 1 } = o;
  ctx.font = fontOf(size, font, weight);
  const chars = parseMarks(str, color), ws = chars.map(c => ctx.measureText(c.ch).width), sp = size * spacing, total = ws.reduce((a, b) => a + b, 0) + sp * Math.max(0, chars.length - 1);
  const fo = 1 - seg(t, t1 - out, t1);
  if (fo <= 0 || t < t0 || alpha <= 0.003) return total;
  const x0 = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  ctx.save(); if (rot) { ctx.translate(x, y); ctx.rotate(rot); ctx.translate(-x, -y); }
  ctx.textBaseline = 'alphabetic'; ctx.font = fontOf(size, font, weight);
  let cx = x0;
  chars.forEach((c, i) => {
    const s = t0 + i * cps, a = (t >= s ? 1 : 0) * fo * alpha * LA, w = ws[i];
    if (a > 0.004) {
      ctx.save(); ctx.globalAlpha = a;
      if (shadow) { ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = size * 0.14; ctx.shadowOffsetY = size * 0.04; }
      ctx.fillStyle = c.col; ctx.fillText(c.ch, cx, y);
      ctx.restore();
    }
    cx += w + sp;
  });
  ctx.restore();
  if (id && fo > 0.5) FRAME_TEXTS.push({ id, text: plain(str), x0, y0: y - size, x1: x0 + total, y1: y + size * 0.3 });
  return total;
}

// ---------------- 字幕：老纪录片的下方字幕条（抖音安全区：x 134–1594，y 119–929） ----------------
const CAPX = 866, CAPY = 884;
function cap(str, t, a, b, id, o = {}) {
  if (t < a - 0.1 || t > b + 0.3) return;
  const size = o.size || 54, x = o.x ?? CAPX, y = o.y ?? CAPY;
  const { total } = measure(str, size, F.sans, 700), w = total + 90, h = size * 1.55;
  const al = a <= 0 ? 1 - seg(t, b + 0.05, b + 0.3) : Math.min(seg(t, a - 0.1, a + 0.06), 1 - seg(t, b + 0.05, b + 0.3));
  ctx.save(); ctx.globalAlpha = al * 0.78; ctx.fillStyle = '#0c0907'; ctx.fillRect(x - w / 2, y - size * 1.06, w, h);
  ctx.globalAlpha = al; ctx.fillStyle = C.red; ctx.fillRect(x - w / 2, y - size * 1.06, 8, h);
  ctx.restore();
  txt(str, x, y, { t, t0: a, t1: b + 0.3, size, id, cps: o.cps ?? 0.02, color: C.sep });
}
function note(str, x, y, o = {}) { txt(str, x, y, { size: 24, color: C.sepD, align: 'left', weight: 400, cps: 0, shadow: 0, font: F.mono, ...o }); }

// ---------------- 转场 ----------------
function put(c, a = 1, dx = 0, dy = 0) { MAIN.setTransform(1, 0, 0, 1, dx, dy); MAIN.globalAlpha = a; MAIN.drawImage(c, 0, 0); MAIN.globalAlpha = 1; MAIN.setTransform(1, 0, 0, 1, 0, 0); }
function veil(a, col = '#0a0806') { if (a <= 0) return; MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = clamp(a); MAIN.fillStyle = col; MAIN.fillRect(0, 0, W, H); MAIN.globalAlpha = 1; }
const T = {
  /** 胶片跳格：几格闪白 + 上下错位，再落到下一幕 */
  splice(p, A, B) { const a = p < 0.5; put(a ? A() : B(), 1, 0, a ? -H * 0.18 * E.in(seg(p, 0.3, 0.5)) : H * 0.18 * (1 - E.out(seg(p, 0.5, 0.7)))); veil(Math.sin(Math.PI * seg(p, 0.35, 0.65)) * 0.85, '#f4e6c8'); },
  fade(p, A, B) { put(A()); put(B(), E.io(p)); },
  /** 冲进一个点（红灯）：A 放大到那一点，红光一闪，B 从稍大落回原位 */
  zoom(p, A, B, o = {}) {
    const x = o.x ?? W / 2, y = o.y ?? H / 2;
    if (p < 0.5) { const k = lerp(1, 9, E.in(seg(p, 0, 0.5))); MAIN.setTransform(k, 0, 0, k, x - x * k, y - y * k); MAIN.drawImage(A(), 0, 0); MAIN.setTransform(1, 0, 0, 1, 0, 0); veil(E.in(seg(p, 0.25, 0.5)) * 0.9, C.red); }
    else { const k = lerp(1.18, 1, E.out(seg(p, 0.5, 1))), bx = o.bx ?? W / 2, by = o.by ?? H / 2; MAIN.setTransform(k, 0, 0, k, bx - bx * k, by - by * k); MAIN.drawImage(B(), 0, 0); MAIN.setTransform(1, 0, 0, 1, 0, 0); veil((1 - E.out(seg(p, 0.5, 0.85))) * 0.9, C.red); }
  },
  cut(p, A, B) { put(p < 0.5 ? A() : B()); },
};

// ---------------- 胶片层：颗粒、划痕、灰尘、暗角、片框 ----------------
let GRAIN = [], VIG = null;
function makeFilm() {
  for (let k = 0; k < 6; k++) {
    const c = document.createElement('canvas'); c.width = 640; c.height = 360; const g = c.getContext('2d'), im = g.createImageData(640, 360), r = rng(31 + k);
    for (let i = 0; i < im.data.length; i += 4) { const v = 128 + (r() + r() + r() - 1.5) * 120; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0); GRAIN.push(c);
  }
  VIG = mk(); const g = VIG.getContext('2d');
  const v = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.38, W / 2, H / 2, Math.hypot(W, H) * 0.6);
  v.addColorStop(0, 'rgba(10,6,3,0)'); v.addColorStop(1, 'rgba(10,6,3,0.62)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
  // 圆角片门
  g.fillStyle = '#050403'; g.beginPath(); g.rect(0, 0, W, H); g.roundRect(14, 10, W - 28, H - 20, 46); g.fill('evenodd');
}
function filmFX(t) {
  const fr = Math.floor(t * 24), g = MAIN, r = rng(1000 + fr);
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.32; g.imageSmoothingEnabled = true;
  g.drawImage(GRAIN[fr % 6], -r() * 40, -r() * 40, W + 80, H + 80); g.globalAlpha = 1;
  g.globalCompositeOperation = 'source-over';
  // 划痕：竖细线，有时一根有时两根
  const n = r() < 0.55 ? 1 : r() < 0.5 ? 2 : 0;
  for (let i = 0; i < n; i++) { const x = r() * W, a = 0.12 + r() * 0.22; g.fillStyle = r() < 0.6 ? `rgba(245,232,205,${a})` : `rgba(10,6,3,${a})`; g.fillRect(x, 0, 1 + r() * 1.6, H); }
  // 持续一段时间的长划痕
  const slow = Math.floor(t * 1.3); if (hash(slow * 5.1) < 0.5) { const x = hash(slow * 9.3) * W + Math.sin(t * 7) * 6; g.fillStyle = 'rgba(240,226,196,0.16)'; g.fillRect(x, 0, 2, H); }
  // 灰尘点和毛发
  for (let i = 0; i < 5; i++) { if (r() < 0.45) continue; const x = r() * W, y = r() * H, s = 1.5 + r() * 4; g.fillStyle = r() < 0.7 ? 'rgba(8,5,3,0.7)' : 'rgba(250,240,220,0.55)'; g.beginPath(); g.arc(x, y, s, 0, Math.PI * 2); g.fill(); }
  if (r() < 0.12) { const x = r() * W, y = r() * H; g.strokeStyle = 'rgba(8,5,3,0.6)'; g.lineWidth = 1.6; g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 30, y - 20, x + 10, y + 40, x + 50 + r() * 30, y + 20); g.stroke(); }
  g.drawImage(VIG, 0, 0);
}

// ---------------- 事件（音效）与场景 ----------------
const EV = []; window.EV = EV;
function ev(t, s, o = {}) { EV.push({ t: +t.toFixed(3), s, ...o }); }
const SCENES = [];
function render(t) {
  T_NOW = t; FRAME_TEXTS.length = 0; LA = 1; ctx = MAIN;
  MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over';
  MAIN.fillStyle = '#0a0806'; MAIN.fillRect(0, 0, W, H);
  // 片门抖动：整幅画面每格轻微错位
  const fr = Math.floor(t * 24), wx = (hash(fr * 1.3) - 0.5) * 2.4, wy = (hash(fr * 2.9) - 0.5) * 3.2;
  for (const s of SCENES) if (t >= s.t0 && t < s.t1) { ctx = MAIN; MAIN.save(); WEAVE = [wx, wy]; s.draw(t); MAIN.restore(); }
  ctx = MAIN; MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over';
  filmFX(t);
  // 字幕最后画（不抖、不被颗粒盖住）
  for (const s of SCENES) if (t >= s.t0 && t < s.t1 && s.caps) { ctx = MAIN; MAIN.save(); s.caps(t); MAIN.restore(); }
}
let WEAVE = [0, 0];
/** 场景里放镜头用这个，自带片门抖动 */
function film(c, a = 1) { put(c, a, WEAVE[0], WEAVE[1]); }
window.render = render;
window.TEXTS = (t) => { render(t); return FRAME_TEXTS.slice(); };

async function boot() {
  for (const f of ['900 60px "Noto Serif SC"', '700 60px "Noto Sans SC"', '400 60px "Noto Sans SC"', '700 60px "Courier New"', '900 60px "Arial Black"']) { try { await document.fonts.load(f, '有人让你电一个陌生人按到第几个0123456789%V'); } catch (e) {} }
  await document.fonts.ready;
  makeFilm();
  EV.sort((a, b) => a.t - b.t);
  render(parseFloat(new URLSearchParams(location.search).get('t') || '0'));
  window.READY = true;
}
