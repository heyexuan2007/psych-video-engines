// ============================================================
// 舞台引擎：1920×1080 canvas，render(t) 是 t 的纯函数（任何一帧都能单独渲染）
// 视觉语法：暗场 + 追光。每个镜头先画“实物”层（全彩），再乘一张光照图（只有被灯照到的地方有颜色，
// 其余都是深蓝的剪影），最后叠光束里的雾和灰尘、发光物（暗处的眼睛、气泡）和字。
// 所有场景都是舞台上的布景：教室、卧室、街角都搭在同一块木地板上。
// 页面约定（和 lemo-opuscar 的渲染工具一致）：window.render / DUR / EV / TEXTS / READY
// ============================================================
const QS = new URLSearchParams(location.search);
const W = +(QS.get('w') || 1920), H = +(QS.get('h') || 1080), FPS = 30;
window.DUR = 37.5;

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
  bounce: p => { p = clamp(p); const n = 7.5625, d = 2.75; if (p < 1 / d) return n * p * p; if (p < 2 / d) return n * (p -= 1.5 / d) * p + .75; if (p < 2.5 / d) return n * (p -= 2.25 / d) * p + .9375; return n * (p -= 2.625 / d) * p + .984375; },
};
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = s + 0x6D2B79F5 | 0; let x = Math.imul(s ^ s >>> 15, 1 | s); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const strHash = (s) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 9973; return h; };
const shakeAt = (t, t0, amp = 10, k = 7) => { const d = t - t0; return d > 0 ? Math.sin(d * 55) * amp * Math.exp(-d * k) : 0; };

// ---------------- 色板与字体 ----------------
const C = {
  ink: '#1b1512', cream: '#f6ecd8', white: '#fffaf0', warm: '#ffd36b', beam: '#ffe6ad', amber: '#ffb347',
  red: '#e0453a', velvet: '#6e1420', velvetD: '#3a0a12', wood: '#7a5234', woodD: '#4e3220', woodL: '#9a6a44',
  skin: '#f4d3b5', skinD: '#ddae86', hair: '#2b211b', pink: '#ff7aa8', pinkD: '#d9507f', navy: '#26355e', blue: '#4b7bd6',
  teal: '#2f9e94', mustard: '#e6b23a', olive: '#7b8a45', gray: '#8c8a92', grayD: '#55535c', paper: '#f3ead6', moon: '#bcd4ff',
};
const F = { serif: "'Noto Serif SC','STZhongsong','SimSun',serif", sans: "'Noto Sans SC','Microsoft YaHei',sans-serif", lat: "'Arial Black','Arial',sans-serif" };
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }
function mixc(a, b, p) { const x = hexRgb(a), y = hexRgb(b); return '#' + x.map((v, i) => Math.round(lerp(v, y[i], clamp(p))).toString(16).padStart(2, '0')).join(''); }

// ---------------- 整体透明度与镜头 ----------------
let LA = 1;
function layer(a, fn) { if (a <= 0.003) return; const prev = LA; LA = prev * clamp(a); try { fn(); } finally { LA = prev; } }
function camera(cx, cy, s, fn, dx = 0, dy = 0) { ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(s, s); ctx.translate(-cx, -cy); try { fn(); } finally { ctx.restore(); } }
function at(x, y, s, rot, fn) { ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot); if (s !== 1) ctx.scale(s, s); try { fn(); } finally { ctx.restore(); } }

// ---------------- 基本形状（干净的剪纸描边） ----------------
function path(pts, close = true) { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); if (close) ctx.closePath(); }
/** 填色 + 描边。build() 负责 beginPath 之后的路径 */
function shape(build, fill, o = {}) {
  ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1);
  ctx.beginPath(); build();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (o.shade) { ctx.save(); ctx.clip(); ctx.fillStyle = 'rgba(20,10,30,0.16)'; ctx.translate(o.shade[0], o.shade[1]); ctx.beginPath(); build(); ctx.rect(-4000, -4000, 8000, 8000); ctx.fill('evenodd'); ctx.restore(); ctx.beginPath(); build(); }
  if (o.stroke !== false) { ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.lineWidth = o.w ?? 4.5; ctx.strokeStyle = o.color || C.ink; ctx.stroke(); }
  ctx.restore();
}
const circ = (x, y, r) => () => ctx.arc(x, y, r, 0, Math.PI * 2);
const oval = (x, y, rx, ry, rot = 0) => () => ctx.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2);
const box = (x, y, w, h, r = 0) => () => ctx.roundRect(x, y, w, h, r);
const poly = (pts) => () => pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
/** 线（不闭合） */
function line(pts, o = {}) { ctx.save(); ctx.globalAlpha = LA * (o.alpha ?? 1); path(pts, false); ctx.lineCap = o.cap || 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = o.w ?? 4.5; ctx.strokeStyle = o.color || C.ink; if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); ctx.restore(); }
/** 带描边的粗管子（胳膊、腿） */
function tube(pts, w, col, o = {}) { line(pts, { w: w + 9, color: C.ink, alpha: o.alpha }); line(pts, { w, color: col, alpha: o.alpha }); }
function qd(p0, c, p1, n = 12) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * p0[0] + 2 * v * u * c[0] + u * u * p1[0], v * v * p0[1] + 2 * v * u * c[1] + u * u * p1[1]]); } return out; }
function bz(p0, c1, c2, p1, n = 16) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u; out.push([v * v * v * p0[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u * u * u * p1[0], v * v * v * p0[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u * u * u * p1[1]]); } return out; }

// ---------------- 光 ----------------
function mk() { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; }
const SCN = mk(), LIT = mk(), BUF = [mk(), mk()];
let LIGHTS = [], OVERS = [], AMB = '#2a2d44';
/** 环境光（暗场时是深蓝；“开灯”时调亮） */
function ambient(col) { AMB = col; }
/** 追光。x 光斑中心，gy 地面。o: w 光斑半宽, h 照亮的高度, i 强度 0..1, col, beam 光束雾 0..1, top 光源 y, tx 光源 x */
function spot(x, gy, o = {}) { LIGHTS.push({ m: ctx.getTransform(), x, gy, w: o.w ?? 170, h: o.h ?? 440, i: o.i ?? 1, col: o.col || C.beam, beam: o.beam ?? 1, top: o.top ?? -140, tx: o.tx ?? x, seed: o.seed ?? 1 }); }
/** 柔光（台灯、手机屏、月光）：椭圆 */
function glowLight(x, y, rx, ry, o = {}) { LIGHTS.push({ m: ctx.getTransform(), soft: true, x, y, rx, ry, i: o.i ?? 1, col: o.col || C.beam }); }
/** 发光层：画在光照之后，不会被压暗（暗处的眼睛、气泡、数字） */
function over(fn) { OVERS.push({ m: ctx.getTransform(), la: LA, fn }); }
function blob(g, x, y, rx, ry, col, i, hard) {
  if (i <= 0.003 || rx <= 0 || ry <= 0) return;
  g.save(); g.translate(x, y); g.scale(rx, ry);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, 1); gr.addColorStop(0, col); gr.addColorStop(hard, col); gr.addColorStop(1, rgba(col, 0));
  g.globalAlpha = clamp(i); g.fillStyle = gr; g.beginPath(); g.arc(0, 0, 1, 0, Math.PI * 2); g.fill(); g.restore();
}
function cone(g, L, k = 1) { g.beginPath(); g.moveTo(L.tx - 18 * k, L.top); g.lineTo(L.tx + 18 * k, L.top); g.lineTo(L.x + L.w * k, L.gy); g.lineTo(L.x - L.w * k, L.gy); g.closePath(); }
function drawLights(g) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  g.fillStyle = AMB; g.fillRect(0, 0, W, H);
  g.globalCompositeOperation = 'lighter';
  for (const L of LIGHTS) {
    g.setTransform(L.m);
    if (L.soft) { blob(g, L.x, L.y, L.rx, L.ry, L.col, L.i, 0.25); continue; }
    blob(g, L.x, L.gy - L.h * 0.5, L.w * 1.1, L.h * 0.62, L.col, L.i, 0.74);
    blob(g, L.x, L.gy, L.w * 1.18, L.w * 0.32, L.col, L.i, 0.72);
    g.save(); g.globalAlpha = 0.3 * clamp(L.i); g.fillStyle = L.col; cone(g, L); g.fill(); g.restore();
  }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
}
function drawBeams(g, t) {
  g.globalCompositeOperation = 'screen';
  for (const L of LIGHTS) {
    if (L.soft || L.beam <= 0 || L.i <= 0.01) continue;
    g.setTransform(L.m); const a = L.beam * clamp(L.i);
    let gr = g.createLinearGradient(0, L.top, 0, L.gy); gr.addColorStop(0, rgba(L.col, 0.34 * a)); gr.addColorStop(1, rgba(L.col, 0.07 * a));
    g.fillStyle = gr; cone(g, L); g.fill();
    gr = g.createLinearGradient(0, L.top, 0, L.gy); gr.addColorStop(0, rgba(L.col, 0.22 * a)); gr.addColorStop(1, rgba(L.col, 0.0));
    g.fillStyle = gr; cone(g, L, 0.45); g.fill();
    g.save(); g.translate(L.x, L.gy); g.scale(L.w * 1.05, L.w * 0.27); const rg = g.createRadialGradient(0, 0, 0, 0, 0, 1); rg.addColorStop(0, rgba(L.col, 0.3 * a)); rg.addColorStop(0.8, rgba(L.col, 0.18 * a)); rg.addColorStop(1, rgba(L.col, 0)); g.fillStyle = rg; g.beginPath(); g.arc(0, 0, 1, 0, Math.PI * 2); g.fill(); g.restore();
    // 光柱里的灰尘
    g.fillStyle = L.col;
    for (let k = 0; k < 30; k++) {
      const u = hash(L.seed * 13.1 + k), v = (hash(L.seed * 7.7 + k * 3.3) + t * 0.035 * (0.4 + hash(k * 1.9))) % 1;
      const y = lerp(L.top, L.gy, v), q = (y - L.top) / (L.gy - L.top), half = lerp(18, L.w, q);
      const x = lerp(L.tx, L.x, q) + (u * 2 - 1) * half * 0.85 + Math.sin(t * 0.8 + k * 1.7) * 7;
      g.globalAlpha = (0.25 + 0.55 * hash(k * 9.1 + L.seed)) * a * Math.sin(Math.PI * v); g.fillRect(x, y, 2.4, 2.4);
    }
    g.globalAlpha = 1;
  }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over';
}
/** 渲染一个镜头：实物 × 光照 + 光束 + 发光层，结果写进 target */
function shot(fn, t, target) {
  const s = SCN.getContext('2d'); ctx = s;
  s.setTransform(1, 0, 0, 1, 0, 0); s.globalAlpha = 1; s.globalCompositeOperation = 'source-over'; s.clearRect(0, 0, W, H);
  LIGHTS = []; OVERS = []; AMB = '#2a2d44'; LA = 1;
  fn(t);
  s.setTransform(1, 0, 0, 1, 0, 0);
  drawLights(LIT.getContext('2d'));
  const g = target.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  g.fillStyle = '#05060a'; g.fillRect(0, 0, W, H); g.drawImage(SCN, 0, 0);
  g.globalCompositeOperation = 'multiply'; g.drawImage(LIT, 0, 0); g.globalCompositeOperation = 'source-over';
  drawBeams(g, t);
  ctx = g;
  for (const o of OVERS) { g.save(); g.setTransform(o.m); LA = o.la; try { o.fn(); } finally { g.restore(); } }
  LA = 1; ctx = MAIN;
  return target;
}

// ---------------- 字 ----------------
// 标记法：[[暖黄发光]]、{{红字}}、((灰字))
function parseMarks(str, base) {
  const out = []; let col = base, glow = false, i = 0;
  while (i < str.length) {
    const two = str.slice(i, i + 2);
    if (two === '[[') { glow = true; col = C.warm; i += 2; continue; } if (two === ']]') { glow = false; col = base; i += 2; continue; }
    if (two === '{{') { col = C.red; i += 2; continue; } if (two === '((') { col = C.gray; i += 2; continue; }
    if (two === '}}' || two === '))') { col = base; i += 2; continue; }
    const ch = String.fromCodePoint(str.codePointAt(i)); out.push({ ch, col, glow }); i += ch.length;
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
/**
 * 字：逐字浮上来。o: size, color, align, font, weight, t, t0, t1, cps(每字间隔), out, alpha, id, glow(整行发光), rot, spacing, shadow
 */
function txt(str, x, y, o = {}) {
  const { size = 60, color = C.cream, align = 'center', font = F.sans, weight = 700, t = T_NOW, t0 = -99, t1 = 1e9, cps = 0.03, out = 0.2, alpha = 1, id = null, glow = 0, rot = 0, spacing = 0.03, shadow = 1 } = o;
  ctx.font = fontOf(size, font, weight);
  const chars = parseMarks(str, color), ws = chars.map(c => ctx.measureText(c.ch).width), sp = size * spacing, total = ws.reduce((a, b) => a + b, 0) + sp * Math.max(0, chars.length - 1);
  const fo = 1 - seg(t, t1 - out, t1);
  if (fo <= 0 || t < t0 || alpha <= 0.003) return total;
  const x0 = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  ctx.save(); if (rot) { ctx.translate(x, y); ctx.rotate(rot); ctx.translate(-x, -y); }
  ctx.textBaseline = 'alphabetic'; ctx.font = fontOf(size, font, weight);
  let cx = x0;
  chars.forEach((c, i) => {
    const s = t0 + i * cps, p = E.out(seg(t, s, s + 0.28)), a = seg(t, s, s + 0.14) * fo * alpha * LA, w = ws[i];
    if (a > 0.004) {
      ctx.save(); ctx.translate(cx + w / 2, y + (1 - p) * size * 0.25); const k = 0.9 + 0.1 * p; ctx.scale(k, k);
      ctx.globalAlpha = a;
      if (c.glow || glow) { ctx.shadowColor = rgba(C.amber, 0.9); ctx.shadowBlur = size * 0.45; ctx.fillStyle = c.col; ctx.fillText(c.ch, -w / 2, 0); }
      if (shadow) { ctx.shadowColor = 'rgba(0,0,0,0.75)'; ctx.shadowBlur = size * 0.16; ctx.shadowOffsetY = size * 0.05; }
      ctx.fillStyle = c.col; ctx.fillText(c.ch, -w / 2, 0);
      ctx.restore();
    }
    cx += w + sp;
  });
  ctx.restore();
  if (id && fo > 0.5) FRAME_TEXTS.push({ id, text: plain(str), x0, y0: y - size, x1: x0 + total, y1: y + size * 0.3 });
  return total;
}
/** 大数字：从上面砸下来，带一圈暖光 */
function bigNum(str, x, y, t, t0, o = {}) {
  const d = seg(t, t0, t0 + 0.45); if (d <= 0) return;
  const yy = lerp(y - 260, y, E.bounce(d)) + shakeAt(t, t0 + 0.17, 9), size = o.size || 220;
  layer(o.alpha ?? 1, () => txt(str, x, yy, { size, font: F.lat, weight: 900, color: o.color || C.warm, glow: o.glow ?? 1, t: 99, t0: 0, cps: 0, spacing: 0, align: o.align || 'center' }));
}

// ---------------- 字幕：舞台上方/下方的“字幕条”（抖音安全区：x 134–1594，y 119–929） ----------------
const CAPX = 866, CAPY = 884;
function cap(str, t, a, b, id, o = {}) {
  if (t < a - 0.1 || t > b + 0.3) return;
  const size = o.size || 54, x = o.x ?? CAPX, y = o.y ?? CAPY;
  ctx.font = fontOf(size, F.sans, 700);
  const { total } = measure(str, size, F.sans, 700), w = total + 110, h = size * 1.6;
  const al = Math.min(seg(t, a - 0.1, a + 0.08), 1 - seg(t, b + 0.05, b + 0.3));
  ctx.save(); ctx.globalAlpha = al * 0.62;
  const g = ctx.createLinearGradient(x - w / 2, 0, x + w / 2, 0); g.addColorStop(0, 'rgba(8,8,14,0)'); g.addColorStop(0.12, 'rgba(8,8,14,1)'); g.addColorStop(0.88, 'rgba(8,8,14,1)'); g.addColorStop(1, 'rgba(8,8,14,0)');
  ctx.fillStyle = g; ctx.fillRect(x - w / 2, y - size * 1.08, w, h);
  ctx.globalAlpha = al * 0.9; ctx.fillStyle = C.warm; ctx.fillRect(x - 46 * al, y + size * 0.48, 92 * al, 3);
  ctx.restore();
  txt(str, x, y, { t, t0: a, t1: b + 0.3, size, id, cps: 0.022 });
}
/** 角落小字（来源）：不进阅读检查 */
function note(str, x, y, o = {}) { txt(str, x, y, { size: 24, color: '#b8b2a6', align: 'left', weight: 400, cps: 0, shadow: 0, ...o }); }

// ---------------- 转场（都和“灯”有关） ----------------
let VEIL_COL = '#030305';
function put(c, a = 1) { MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = a; MAIN.drawImage(c, 0, 0); MAIN.globalAlpha = 1; }
function veil(a, col = VEIL_COL) { if (a <= 0) return; MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = clamp(a); MAIN.fillStyle = col; MAIN.fillRect(0, 0, W, H); MAIN.globalAlpha = 1; }
let CURT = null;
function makeCurtain() {
  CURT = document.createElement('canvas'); CURT.width = Math.ceil(W / 2) + 120; CURT.height = H + 40;
  const g = CURT.getContext('2d'), cw = CURT.width;
  for (let x = 0; x < cw; x++) { const k = 0.5 + 0.5 * Math.sin(x / 34 + Math.sin(x / 91) * 1.4); g.fillStyle = mixc('#2a050b', '#9a2232', Math.pow(k, 1.4)); g.fillRect(x, 0, 1, H + 40); }
  const v = g.createLinearGradient(0, 0, 0, H + 40); v.addColorStop(0, 'rgba(0,0,0,0.45)'); v.addColorStop(0.3, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.35)'); g.fillStyle = v; g.fillRect(0, 0, cw, H + 40);
  g.fillStyle = C.warm; g.globalAlpha = 0.85; for (let x = 0; x < cw; x += 22) g.fillRect(x, H + 6, 12, 26); g.globalAlpha = 1;
}
const T = {
  /** 灯灭了再亮：啪一下暗场 */
  blackout(p, A, B) { if (p < 0.5) { put(A()); veil(E.out(seg(p, 0, 0.3))); } else { put(B()); veil(1 - E.in(seg(p, 0.6, 1)) * 1); } },
  /** 大幕合上再拉开 */
  curtain(p, A, B) {
    put(p < 0.5 ? A() : B());
    const c = p < 0.5 ? E.io(seg(p, 0, 0.5)) : 1 - E.io(seg(p, 0.55, 1)), cw = CURT.width, sw = Math.sin(p * Math.PI) * 0.04;
    MAIN.setTransform(1, 0, 0, 1, 0, 0);
    MAIN.save(); MAIN.translate(-cw + c * (W / 2 + 60), -20); MAIN.transform(1, 0, sw, 1, 0, 0); MAIN.drawImage(CURT, 0, 0); MAIN.restore();
    MAIN.save(); MAIN.translate(W + cw - c * (W / 2 + 60), -20); MAIN.scale(-1, 1); MAIN.transform(1, 0, sw, 1, 0, 0); MAIN.drawImage(CURT, 0, 0); MAIN.restore();
  },
  /** 光圈收成一个点，再在下一幕张开 */
  iris(p, A, B, o = {}) {
    const ax = o.x ?? W / 2, ay = o.y ?? H / 2, bx = o.bx ?? ax, by = o.by ?? ay;
    const R = (x, y) => Math.hypot(Math.max(x, W - x), Math.max(y, H - y)) + 40;
    const a = p < 0.5, x = a ? ax : bx, y = a ? ay : by, r = a ? lerp(R(ax, ay), 0, E.in(seg(p, 0, 0.48))) : lerp(0, R(bx, by), E.out(seg(p, 0.52, 1)));
    put(a ? A() : B());
    MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.fillStyle = VEIL_COL; MAIN.beginPath(); MAIN.rect(0, 0, W, H); MAIN.arc(x, y, Math.max(0, r), 0, Math.PI * 2, true); MAIN.fill();
    if (r > 2) { MAIN.strokeStyle = rgba(C.beam, 0.6); MAIN.lineWidth = 5; MAIN.beginPath(); MAIN.arc(x, y, r, 0, Math.PI * 2); MAIN.stroke(); }
  },
  /** 一道探照光从左扫到右，光过去的地方换成下一幕 */
  sweep(p, A, B) {
    const x = lerp(-260, W + 260, E.io(p));
    put(A());
    MAIN.save(); MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.beginPath(); MAIN.rect(0, 0, Math.max(0, x), H); MAIN.clip(); MAIN.drawImage(B(), 0, 0); MAIN.restore();
    MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalCompositeOperation = 'screen';
    const g = MAIN.createLinearGradient(x - 220, 0, x + 220, 0); g.addColorStop(0, rgba(C.beam, 0)); g.addColorStop(0.5, rgba(C.beam, 0.75)); g.addColorStop(1, rgba(C.beam, 0));
    MAIN.fillStyle = g; MAIN.fillRect(x - 220, 0, 440, H); MAIN.globalCompositeOperation = 'source-over';
  },
  /** 叠化（只用在两幕画面几乎一样的地方） */
  fade(p, A, B) { put(A()); put(B(), E.io(p)); },
  pushL(p, A, B) { const e = E.io(p); MAIN.save(); MAIN.setTransform(1, 0, 0, 1, -W * e, 0); MAIN.drawImage(A(), 0, 0); MAIN.setTransform(1, 0, 0, 1, W * (1 - e), 0); MAIN.drawImage(B(), 0, 0); MAIN.restore(); },
};

// ---------------- 胶片质感：暗角 + 颗粒 ----------------
let FILM = null;
function makeFilm() {
  FILM = mk(); const g = FILM.getContext('2d'), r = rng(9);
  const v = g.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.42, W / 2, H / 2, Math.hypot(W, H) * 0.62);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.42)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 30000 * (W * H) / (1920 * 1080); i++) { g.fillStyle = r() < 0.5 ? `rgba(255,240,210,${0.02 + r() * 0.04})` : `rgba(0,0,0,${0.03 + r() * 0.05})`; g.fillRect(r() * W, r() * H, 1 + r() * 1.5, 1 + r() * 1.5); }
}

// ---------------- 事件（音效）与场景 ----------------
const EV = []; window.EV = EV;
function ev(t, s, o = {}) { EV.push({ t: +t.toFixed(3), s, ...o }); }
const SCENES = [];
function render(t) {
  T_NOW = t; FRAME_TEXTS.length = 0; LA = 1; ctx = MAIN;
  MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over';
  MAIN.fillStyle = '#05060a'; MAIN.fillRect(0, 0, W, H);
  for (const s of SCENES) if (t >= s.t0 && t < s.t1) { ctx = MAIN; MAIN.save(); s.draw(t); MAIN.restore(); }
  ctx = MAIN; MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over';
  MAIN.drawImage(FILM, 0, 0);
}
window.render = render;
window.TEXTS = (t) => { render(t); return FRAME_TEXTS.slice(); };

async function boot() {
  for (const f of ['900 60px "Noto Serif SC"', '700 60px "Noto Sans SC"', '400 60px "Noto Sans SC"', '900 60px "Arial Black"']) { try { await document.fonts.load(f, '刷到这条的你表面自律心里却常常不安福勒满分平均打了一字不差星座书专属分析0123456789.%'); } catch (e) {} }
  await document.fonts.ready;
  makeFilm(); makeCurtain();
  EV.sort((a, b) => a.t - b.t);
  render(parseFloat(new URLSearchParams(location.search).get('t') || '0'));
  window.READY = true;
}
