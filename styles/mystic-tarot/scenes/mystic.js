// 画风 B'：神秘塔罗。夜空深蓝 + 慢慢转的金线星盘 + 星座连线 + 烟 + 蜡烛；所有内容都是塔罗牌。
// 牌面是深蓝底金色刻线插画（原创牌：面具 / 镜子 / 种子），牌背是紫底“三角之眼”。

const PM = {
  night: '#070818', deep: '#11142e', navy: '#151a3a', arch: '#1c2250', purple: '#24123a', purpleL: '#3a1f5a',
  gold: '#d8b066', goldL: '#f6d993', goldD: '#8c6a34', lav: '#b9a8e8', crimson: '#8e1b2a', parch: '#e8d9b6',
};
const GOLD_LINE = (pts, w = 3, a = 1) => line(pts, { w, color: PM.gold, alpha: a });

/** 夜空：渐变 + 星星（会闪）+ 几组星座连线 */
function nightSky(t, o = {}) {
  const g = ctx.createRadialGradient(o.cx ?? 866, o.cy ?? 480, 0, o.cx ?? 866, o.cy ?? 480, 1300);
  g.addColorStop(0, '#1d1a44'); g.addColorStop(0.45, PM.deep); g.addColorStop(1, PM.night);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const r = rng(77);
  for (let i = 0; i < 260; i++) {
    const x = r() * W, y = r() * H, s = r() < 0.08 ? 2.6 : 1.2 + r(), tw = 0.55 + 0.45 * Math.sin(t * (1 + r() * 2) + i);
    ctx.globalAlpha = LA * (0.35 + 0.5 * r()) * tw; ctx.fillStyle = r() < 0.2 ? PM.goldL : '#dfe4ff'; ctx.fillRect(x, y, s, s);
  }
  ctx.globalAlpha = 1;
}
/** 星座连线（发光层里画，不被压暗） */
function constellations(t) {
  const sets = [[[150, 170], [230, 120], [300, 160], [360, 110], [420, 190]], [[1380, 150], [1450, 230], [1530, 190], [1580, 280]], [[120, 760], [200, 700], [260, 780], [190, 860]], [[1480, 760], [1560, 690], [1640, 740]]];
  for (const pts of sets) {
    line(pts, { w: 1.5, color: PM.lav, alpha: 0.35, dash: [6, 8] });
    pts.forEach(([x, y], i) => { const k = 0.6 + 0.4 * Math.sin(t * 2 + i * 1.7 + x); ctx.save(); ctx.globalAlpha = LA * k; ctx.shadowColor = PM.goldL; ctx.shadowBlur = 12; ctx.fillStyle = '#fff6dc'; ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill(); ctx.restore(); });
  }
}
/** 12 个自造的星符（不是真实的星座符号，用基本形拼） */
function glyph(i, x, y, s, col) {
  at(x, y, s, 0, () => {
    const o = { w: 2.6, color: col };
    const k = i % 12;
    if (k === 0) { shape(circ(0, 0, 9), null, o); shape(circ(0, 0, 2.5), col, { stroke: false }); }
    if (k === 1) { line(qd([-10, -10], [0, 8], [10, -10]), o); line([[0, 0], [0, 14]], o); line([[-5, 9], [5, 9]], o); }
    if (k === 2) { shape(circ(0, -5, 7), null, o); line([[0, 2], [0, 14]], o); line([[-6, 8], [6, 8]], o); }
    if (k === 3) { line([[-10, 10], [0, -10], [10, 10], [-10, 10]], o); }
    if (k === 4) { line(qd([-8, -10], [6, 0], [-8, 10]), o); line([[2, -12], [2, 12]], o); shape(circ(-8, 0, 3), col, { stroke: false }); }
    if (k === 5) { line([[-10, 0], [10, 0]], o); line([[0, -10], [0, 10]], o); shape(circ(0, 0, 4), null, o); }
    if (k === 6) { line([[-10, -6], [10, -6]], o); line([[-10, 6], [10, 6]], o); line([[-4, -12], [4, 12]], o); }
    if (k === 7) { line(qd([-10, 6], [0, -16], [10, 6]), o); line([[-12, 10], [12, 10]], o); shape(circ(0, -2, 2.5), col, { stroke: false }); }
    if (k === 8) { shape(circ(-4, 0, 6), null, o); shape(circ(5, 0, 6), null, o); }
    if (k === 9) { shape(circ(0, -6, 6), null, o); line([[0, 0], [0, 14]], o); line([[-6, 8], [6, 8]], o); line(qd([-8, -14], [0, -8], [8, -14]), o); }
    if (k === 10) { line([[0, -12], [11, 8], [-11, 8], [0, -12]], o); line([[-6, -1], [6, -1]], o); }
    if (k === 11) { line([[-10, -10], [10, 10]], o); line([[10, -10], [-10, 10]], o); shape(circ(0, 0, 5), null, o); }
  });
}
/** 星盘：几圈金线 + 刻度 + 星符 + 内部的七角星几何。r 外圈半径，rot 转角，a 透明度（发光层里画） */
function astrolabe(x, y, r, rot, a = 0.45) {
  ctx.save(); ctx.globalAlpha = LA * a; ctx.translate(x, y);
  ctx.strokeStyle = PM.gold; ctx.shadowColor = rgba(PM.goldL, 0.6); ctx.shadowBlur = 8;
  for (const [rr, w] of [[r, 2.5], [r * 0.93, 1.2], [r * 0.78, 2], [r * 0.5, 1.2]]) { ctx.lineWidth = w; ctx.beginPath(); ctx.arc(0, 0, rr, 0, Math.PI * 2); ctx.stroke(); }
  ctx.rotate(rot);
  for (let i = 0; i < 120; i++) { const an = i / 120 * Math.PI * 2, l = i % 10 === 0 ? 0.07 : 0.03; ctx.lineWidth = i % 10 ? 1 : 2; ctx.beginPath(); ctx.moveTo(Math.cos(an) * r * 0.93, Math.sin(an) * r * 0.93); ctx.lineTo(Math.cos(an) * r * (0.93 - l), Math.sin(an) * r * (0.93 - l)); ctx.stroke(); }
  ctx.restore();
  for (let i = 0; i < 12; i++) { const an = rot + (i + 0.5) / 12 * Math.PI * 2, rr = r * 0.855; layer(a * 1.6, () => glyph(i, x + Math.cos(an) * rr, y + Math.sin(an) * rr, r / 380, PM.gold)); }
  // 12 条分隔线 + 内部七角星
  ctx.save(); ctx.globalAlpha = LA * a * 0.8; ctx.translate(x, y); ctx.rotate(rot); ctx.strokeStyle = PM.gold; ctx.lineWidth = 1.2;
  for (let i = 0; i < 12; i++) { const an = i / 12 * Math.PI * 2; ctx.beginPath(); ctx.moveTo(Math.cos(an) * r * 0.78, Math.sin(an) * r * 0.78); ctx.lineTo(Math.cos(an) * r * 0.93, Math.sin(an) * r * 0.93); ctx.stroke(); }
  ctx.rotate(-rot * 2.2); ctx.beginPath();
  for (let i = 0; i <= 7; i++) { const an = -Math.PI / 2 + (i * 3 % 7) / 7 * Math.PI * 2; i ? ctx.lineTo(Math.cos(an) * r * 0.76, Math.sin(an) * r * 0.76) : ctx.moveTo(Math.cos(an) * r * 0.76, Math.sin(an) * r * 0.76); }
  ctx.stroke(); ctx.restore();
}
/** 一缕一缕的烟（发光层） */
function smoke(t, x, y, h, seed = 1, a = 0.16) {
  ctx.save();
  for (let j = 0; j < 3; j++) {
    ctx.globalAlpha = LA * a * (1 - j * 0.25); ctx.strokeStyle = PM.lav; ctx.lineWidth = 10 - j * 3; ctx.lineCap = 'round'; ctx.filter = 'blur(3px)'; ctx.beginPath();
    for (let k = 0; k <= 40; k++) { const q = k / 40, yy = y - q * h, xx = x + Math.sin(q * 6 + t * 0.9 + seed + j) * 40 * q + Math.sin(q * 13 - t * 1.6 + j) * 10 * q; k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); }
    ctx.stroke();
  }
  ctx.filter = 'none'; ctx.restore();
}
/** 整体背景：夜空（实物层）+ 星盘/星座/烟（发光层） */
function mysticBG(t, o = {}) {
  ambient(o.amb || '#8a82b8');
  nightSky(t, o);
  const cx = o.cx ?? 866, cy = o.cy ?? 480;
  // 星盘画在实物层（会被牌挡住），透明度调高抵消光照压暗
  astrolabe(cx, cy, o.r || 470, t * 0.04 + (o.rot0 || 0), Math.min(1, (o.ringA ?? 0.42) * 1.8));
  over(() => constellations(t));
}

// ---------------- 塔罗牌 ----------------
const CW = 300, CH = 520;
function heart(x, y, s, col, fill) { at(x, y, s, 0, () => shape(() => { ctx.moveTo(0, 8); ctx.bezierCurveTo(-18, -6, -10, -20, 0, -10); ctx.bezierCurveTo(10, -20, 18, -6, 0, 8); }, fill || null, { w: 2.4, color: col })); }
function hatch(x0, y0, x1, y1, gap, a = 0.5) { for (let x = x0; x < x1; x += gap) line([[x, y0], [x + (y1 - y0) * 0.3, y1]], { w: 1.2, color: PM.gold, alpha: a }); }

const ART = {
  /** 面具：外面一张平静的脸，裂缝后面露出一只发慌的眼睛 */
  mask() {
    GOLD_LINE([[-90, -150], [90, -150]], 1, 0.4);
    shape(() => { ctx.moveTo(0, -150); ctx.arc(0, -150, 18, 0, Math.PI * 2); }, null, { w: 2, color: PM.gold });
    shape(() => { ctx.ellipse(0, -10, 78, 104, 0, 0, Math.PI * 2); }, '#252c62', { w: 3.4, color: PM.gold });
    // 平静的闭眼和微笑
    line(qd([-46, -30], [-28, -18], [-12, -30]), { w: 3, color: PM.goldL });
    line(qd([12, -30], [28, -18], [46, -30]), { w: 3, color: PM.goldL });
    line(qd([-24, 40], [0, 56], [24, 40]), { w: 3, color: PM.goldL });
    line([[0, -10], [-6, 18], [4, 20]], { w: 2, color: PM.gold });
    // 裂缝
    line([[30, -112], [40, -78], [26, -54], [46, -20], [32, 10], [52, 44], [40, 90]], { w: 2.6, color: PM.goldL });
    // 裂缝后面的眼睛：睁大、往旁边看，一滴汗
    ctx.save(); ctx.beginPath(); ctx.ellipse(0, -10, 78, 104, 0, 0, Math.PI * 2); ctx.clip();
    shape(() => { ctx.moveTo(40, -78); ctx.lineTo(26, -54); ctx.lineTo(46, -20); ctx.lineTo(80, -20); ctx.lineTo(80, -90); ctx.closePath(); }, '#0b0d22', { stroke: false });
    shape(oval(58, -48, 12, 15), '#f2e6c8', { w: 2, color: PM.goldL }); shape(circ(62, -46, 5), '#0b0d22', { stroke: false });
    ctx.restore();
    shape(() => { ctx.moveTo(86, -64); ctx.quadraticCurveTo(94, -50, 86, -44); ctx.quadraticCurveTo(78, -50, 86, -64); }, PM.lav, { w: 1.5, color: PM.goldL });
    // 系带
    line(qd([-78, -20], [-104, -40], [-110, -10]), { w: 2.4, color: PM.gold }); line(qd([78, -20], [104, -40], [110, -10]), { w: 2.4, color: PM.gold });
    hatch(-100, 110, 100, 160, 9, 0.35);
  },
  /** 镜子：手镜里一张皱眉的脸，外面飘着一颗颗心 */
  mirror() {
    shape(box(-12, 50, 24, 100, 8), '#252c62', { w: 3, color: PM.gold });
    shape(oval(0, -40, 74, 94), '#252c62', { w: 3.4, color: PM.gold });
    shape(oval(0, -40, 60, 80), '#2e3672', { w: 2, color: PM.gold });
    // 镜子里的脸：皱眉
    shape(oval(0, -36, 30, 36), null, { w: 2.4, color: PM.goldL });
    for (const sx of [-1, 1]) { shape(circ(sx * 11, -40, 3), PM.goldL, { stroke: false }); line([[sx * 4, -52], [sx * 18, -48]], { w: 2.4, color: PM.goldL }); }
    line(qd([-10, -16], [0, -24], [10, -16]), { w: 2.4, color: PM.goldL });
    line([[-38, -96], [-22, -110]], { w: 3, color: '#ffffff', alpha: 0.5 });
    // 心
    for (const [x, y, s] of [[-96, -110, 1.3], [96, -70, 1], [-100, 10, 0.9], [92, 40, 1.4], [-80, 110, 1.1], [70, 120, 0.8]]) heart(x, y, s, PM.goldL, rgba(PM.crimson, 0.6));
  },
  /** 种子：土里一颗种子发芽，上面一颗还很远的星 */
  seed() {
    star8(0, -112, 46, 18);
    line([[0, -60], [0, 50]], { w: 1.6, color: PM.gold, alpha: 0.55, dash: [5, 7] });
    shape(box(-130, 70, 260, 120, 0), '#1a1e44', { stroke: false });
    line([[-130, 70], [130, 70]], { w: 3, color: PM.gold });
    for (let i = 0; i < 9; i++) line([[-120 + i * 30, 84 + (i % 2) * 14], [-104 + i * 30, 84 + (i % 2) * 14]], { w: 1.6, color: PM.gold, alpha: 0.5 });
    shape(oval(0, 116, 22, 15), '#3a2a20', { w: 2.6, color: PM.goldL });
    line(bz([0, 104], [4, 80], [-6, 60], [0, 24]), { w: 3, color: PM.goldL });
    shape(() => { ctx.moveTo(0, 40); ctx.quadraticCurveTo(-30, 14, -44, 28); ctx.quadraticCurveTo(-26, 50, 0, 40); }, '#2a4a3a', { w: 2.4, color: PM.goldL });
    shape(() => { ctx.moveTo(0, 30); ctx.quadraticCurveTo(30, 4, 44, 18); ctx.quadraticCurveTo(26, 40, 0, 30); }, '#2a4a3a', { w: 2.4, color: PM.goldL });
  },
};
/** 八芒星（带光芒） */
function star8(x, y, r, inner) {
  const pts = []; for (let i = 0; i < 16; i++) { const a = -Math.PI / 2 + i * Math.PI / 8, rr = i % 2 ? inner : (i % 4 ? r * 0.7 : r); pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
  shape(poly(pts), PM.goldL, { w: 2, color: PM.gold });
}
/** 牌背：紫底，三角之眼 + 日月 + 碎星；label 写在底部铭牌上 */
function cardBack(o = {}) {
  shape(box(-CW / 2, -CH / 2, CW, CH, 16), PM.purple, { w: 3.5, color: PM.gold });
  shape(box(-CW / 2 + 14, -CH / 2 + 14, CW - 28, CH - 28, 10), null, { w: 1.5, color: PM.gold });
  const r = rng(5); for (let i = 0; i < 40; i++) { const x = (r() - 0.5) * (CW - 50), y = (r() - 0.5) * (CH - 50); ctx.save(); ctx.globalAlpha = LA * 0.6; ctx.fillStyle = PM.goldL; ctx.fillRect(x, y, 2, 2); ctx.restore(); }
  for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; line([[Math.cos(a) * 88, -20 + Math.sin(a) * 88], [Math.cos(a) * (i % 2 ? 104 : 120), -20 + Math.sin(a) * (i % 2 ? 104 : 120)]], { w: 2, color: PM.gold }); }
  shape(circ(0, -20, 84), PM.purpleL, { w: 2.5, color: PM.gold });
  shape(poly([[0, -96], [70, 24], [-70, 24]]), null, { w: 2.5, color: PM.goldL });
  shape(() => { ctx.moveTo(-34, -6); ctx.quadraticCurveTo(0, -36, 34, -6); ctx.quadraticCurveTo(0, 22, -34, -6); }, '#f2e6c8', { w: 2.4, color: PM.goldL });
  shape(circ(0, -6, 11), PM.purple, { w: 2, color: PM.goldL }); shape(circ(-3, -9, 3), '#ffffff', { stroke: false });
  // 上下日月
  shape(circ(0, -196, 16), null, { w: 2, color: PM.gold }); for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; line([[Math.cos(a) * 20, -196 + Math.sin(a) * 20], [Math.cos(a) * 28, -196 + Math.sin(a) * 28]], { w: 2, color: PM.gold }); }
  ctx.save(); ctx.beginPath(); ctx.arc(0, 150, 18, 0, Math.PI * 2); ctx.arc(7, 144, 15, 0, Math.PI * 2, true); ctx.fillStyle = PM.gold; ctx.globalAlpha = LA; ctx.fill('evenodd'); ctx.restore();
  if (o.label) { shape(box(-80, 186, 160, 50, 8), PM.deep, { w: 2, color: PM.gold }); txt(o.label, 0, 224, { size: 34, font: F.serif, weight: 900, color: PM.goldL, t: 99, t0: 0, cps: 0, shadow: 0 }); }
}
/** 牌面：深蓝底、拱形画窗，下面一块铭牌直接写这张牌说的话（两行大白话）；牌名和罗马数字缩小放顶上当装饰 */
function cardFace(o) {
  shape(box(-CW / 2, -CH / 2, CW, CH, 16), PM.navy, { w: 3.5, color: PM.gold });
  shape(box(-CW / 2 + 14, -CH / 2 + 14, CW - 28, CH - 28, 10), null, { w: 1.5, color: PM.gold });
  const arch = () => { ctx.moveTo(-118, 64); ctx.lineTo(-118, -84); ctx.arc(0, -84, 118, Math.PI, 0); ctx.lineTo(118, 64); ctx.closePath(); };
  shape(arch, PM.arch, { w: 2.5, color: PM.gold });
  ctx.save(); ctx.beginPath(); arch(); ctx.clip(); at(0, -62, 0.72, 0, () => ART[o.art]()); ctx.restore();
  for (const [x, y] of [[-124, -236], [124, -236], [-124, 236], [124, 236]]) star(x, y, 7, PM.gold, null);
  txt(o.num + ' · ' + o.name, 0, -216, { size: 22, font: F.serif, weight: 900, color: PM.gold, t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0.15 });
  shape(box(-122, 82, 244, 146, 10), PM.deep, { w: 2, color: PM.gold });
  (o.lines || []).forEach((l, i) => txt(l, 0, 142 + i * 54, { size: 40, font: F.serif, weight: 900, color: PM.goldL, t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0.06 }));
}
/** 一张牌：中心 (x,y)。o: flip 0 背 → 1 面, face {num,name,art}, back {label}, rot, lit 被说中的光（0..1） */
function tarot(x, y, s, o = {}) {
  const fl = o.flip ?? 0, sx = Math.abs(Math.cos(Math.PI * fl)), showFace = fl > 0.5;
  if (o.lit) over(() => at(x, y, s, o.rot || 0, () => {
    // 背后放射的光
    ctx.save(); ctx.beginPath(); ctx.rect(-2000, -2000, 4000, 4000); ctx.roundRect(-CW / 2 - 4, -CH / 2 - 4, CW + 8, CH + 8, 18); ctx.clip('evenodd'); ctx.globalAlpha = LA * o.lit * 0.45; ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 18; i++) { const a = i / 18 * Math.PI * 2 + T_NOW * 0.2, l = i % 2 ? 330 : 400; const g = ctx.createLinearGradient(0, 0, Math.cos(a) * l, Math.sin(a) * l); g.addColorStop(0, rgba(PM.goldL, 0.7)); g.addColorStop(1, rgba(PM.goldL, 0)); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a - 0.05) * l, Math.sin(a - 0.05) * l); ctx.lineTo(Math.cos(a + 0.05) * l, Math.sin(a + 0.05) * l); ctx.closePath(); ctx.fill(); }
    ctx.restore();
  }));
  at(x, y, s, o.rot || 0, () => {
    // 牌的影子
    ctx.save(); ctx.scale(Math.max(0.02, sx), 1);
    shape(box(-CW / 2 + 12, -CH / 2 + 16, CW, CH, 16), 'rgba(0,0,0,0.45)', { stroke: false });
    if (showFace) cardFace(o.face); else cardBack(o.back || {});
    ctx.restore();
  });
  if (o.lit) over(() => at(x, y, s, o.rot || 0, () => {
    ctx.save(); ctx.globalAlpha = LA * o.lit; ctx.shadowColor = PM.goldL; ctx.shadowBlur = 30; ctx.strokeStyle = PM.goldL; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.roundRect(-CW / 2, -CH / 2, CW, CH, 16); ctx.stroke(); ctx.restore();
  }));
  // 牌下面的“说中了”勾选框：p 0..1（勾画到一半时 p≈0.6）
  if (o.check != null) over(() => at(x, y + (CH / 2 + 62) * s, s, 0, () => {
    const p = o.check, on = p >= 0.98;
    ctx.save(); if (on) { ctx.shadowColor = PM.goldL; ctx.shadowBlur = 22; }
    shape(box(-104, -30, 60, 60, 8), on ? rgba(PM.gold, 0.25) : 'rgba(10,12,30,0.6)', { w: 4, color: PM.goldL });
    ctx.restore();
    tick(-74, -2, 0.82, p, PM.goldL, 10);
    txt('说中了', 14, 18, { size: 46, font: F.serif, weight: 900, color: on ? PM.goldL : rgba(PM.goldL, 0.35), align: 'left', t: 99, t0: 0, cps: 0, glow: on ? 1 : 0, shadow: 0 });
  }));
}
/** 蜡烛（重用烛光版，但火苗更小、更远） */
function sideCandles(t, o = {}) {
  candle(o.lx ?? 150, o.ly ?? 1000, o.ls ?? 0.95, t, { reach: 720 });
  candle(o.rx ?? 1600, o.ry ?? 1000, o.rs ?? 0.8, t + 1.7, { reach: 620 });
}
/** 字幕：金字 + 两侧星饰（沿用 candleCap） */
const mysticCap = candleCap;
