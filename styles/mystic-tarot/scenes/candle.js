// 画风 B：占卜桌烛光。俯看一张铺着紫丝绒的桌子，只有蜡烛照到的地方有颜色，其余是深紫剪影。
// 用引擎的 shot()：实物层 × 光照图 + 发光层（火苗、金色勾、发光字）。

const PB = {
  cloth: '#5a2148', clothD: '#3a1230', gold: '#e2b45a', goldL: '#ffd98a', goldD: '#9a7232', ink: '#1a0f16', wax: '#f3e4c8', waxD: '#d8c19c',
  flame: '#ffcf6a', amb: '#241a30', glass: '#9fb8d8',
};
PB.env = { paper: '#efdcb8', paperD: '#d6bd90', ink: PB.ink, seal: '#8e1b24', sealD: '#5a0f16', sealInk: '#f0c680' };
PB.cardPal = { card: '#f0e0bf', ink: PB.ink, box: '#f7ecd6', text: '#3a1230', tick: 'rgba(0,0,0,0)', accent: PB.gold, edge: PB.goldD };
PB.kid = { ink: '#0d0a14', hair: '#0d0a14', stick: '#0d0a14', paddle: '#f6e7c4', paddleInk: '#7a1a24' };

/** 桌布：丝绒褶 + 暗纹 + 金流苏边 */
function tableBG(t, o = {}) {
  ctx.fillStyle = PB.cloth; ctx.fillRect(0, 0, W, H);
  // 丝绒的明暗褶
  for (let x = -100; x < W + 100; x += 6) { const k = 0.5 + 0.5 * Math.sin(x / 140 + Math.sin(x / 377) * 1.6); ctx.fillStyle = rgba(PB.clothD, 0.5 * Math.pow(k, 2)); ctx.fillRect(x, 0, 6, H); }
  // 暗纹：一圈圈星月
  ctx.save(); ctx.globalAlpha = 0.18;
  for (let j = 0; j < 6; j++) for (let i = 0; i < 9; i++) {
    const x = 120 + i * 220 + (j % 2) * 110, y = 90 + j * 190;
    star(x, y, 16, PB.goldD, null);
    ctx.beginPath(); ctx.arc(x + 60, y + 70, 18, 0, Math.PI * 2); ctx.arc(x + 68, y + 64, 15, 0, Math.PI * 2, true); ctx.fillStyle = PB.goldD; ctx.fill('evenodd');
  }
  ctx.restore();
  // 桌子的前沿：金流苏
  if (o.edge !== false) {
    const ey = o.edgeY ?? 1020;
    shape(box(-20, ey - 16, W + 40, 22, 0), PB.goldD, { stroke: false });
    for (let x = 0; x < W; x += 14) line([[x, ey], [x + 3, ey + 46 + (x % 28 ? 0 : 6)]], { w: 5, color: PB.gold });
  }
}
/** 蜡烛：底中心 (x,y)。火苗放进发光层，同时加一盏会抖的灯 */
function candle(x, y, s, t, o = {}) {
  const h = (o.h || 260) * s, w = 70 * s, fl = 0.85 + 0.1 * Math.sin(t * 13.7) + 0.05 * Math.sin(t * 31.1 + 1);
  glowLight(x, y - h - 40 * s, (o.reach || 900) * fl, (o.reach || 900) * 0.8 * fl, { i: 1, col: '#ffcf8a' });
  glowLight(x, y - h - 40 * s, 260 * fl, 220 * fl, { i: 0.7, col: '#fff0c8' });
  // 烛台
  shape(oval(x, y, w * 1.6, w * 0.45), PB.goldD, { w: 4, color: PB.ink });
  shape(oval(x, y - 10 * s, w * 1.2, w * 0.32), PB.gold, { w: 3, color: PB.ink });
  // 蜡身 + 蜡泪
  shape(() => { ctx.moveTo(x - w / 2, y - 10 * s); ctx.lineTo(x - w / 2, y - h); ctx.quadraticCurveTo(x, y - h - 14 * s, x + w / 2, y - h); ctx.lineTo(x + w / 2, y - 10 * s); ctx.closePath(); }, PB.wax, { w: 4, color: PB.ink, shade: [12, 0] });
  for (const [dx, len] of [[-0.3, 60], [0.15, 95], [0.38, 40]]) shape(() => { const xx = x + dx * w; ctx.moveTo(xx - 7 * s, y - h + 2); ctx.lineTo(xx - 7 * s, y - h + len * s); ctx.arc(xx, y - h + len * s, 7 * s, Math.PI, 0, true); ctx.lineTo(xx + 7 * s, y - h + 2); ctx.closePath(); }, PB.wax, { w: 3, color: PB.ink });
  line([[x, y - h - 4 * s], [x + 2, y - h - 22 * s]], { w: 4, color: PB.ink });
  over(() => {
    const fx = x + Math.sin(t * 7.3) * 3 * s, fy = y - h - 22 * s, fh = 70 * s * fl;
    const gr = ctx.createRadialGradient(fx, fy - fh * 0.3, 0, fx, fy - fh * 0.3, fh * 1.6); gr.addColorStop(0, 'rgba(255,214,130,0.55)'); gr.addColorStop(1, 'rgba(255,214,130,0)');
    ctx.fillStyle = gr; ctx.fillRect(fx - fh * 2, fy - fh * 2, fh * 4, fh * 4);
    shape(() => { ctx.moveTo(fx, fy - fh); ctx.bezierCurveTo(fx + 22 * s, fy - fh * 0.4, fx + 18 * s, fy + 8 * s, fx, fy + 8 * s); ctx.bezierCurveTo(fx - 18 * s, fy + 8 * s, fx - 22 * s, fy - fh * 0.4, fx, fy - fh); }, '#ffb648', { stroke: false });
    shape(() => { ctx.moveTo(fx, fy - fh * 0.62); ctx.bezierCurveTo(fx + 10 * s, fy - fh * 0.25, fx + 8 * s, fy + 4 * s, fx, fy + 4 * s); ctx.bezierCurveTo(fx - 8 * s, fy + 4 * s, fx - 10 * s, fy - fh * 0.25, fx, fy - fh * 0.62); }, '#fff4d2', { stroke: false });
    // 一缕烟
    ctx.save(); ctx.globalAlpha = 0.18 * LA; ctx.strokeStyle = '#d8c8e8'; ctx.lineWidth = 3; ctx.beginPath();
    for (let k = 0; k <= 30; k++) { const yy = fy - fh - k * 9 * s, xx = fx + Math.sin(k * 0.35 - t * 2) * k * 1.4 * s; k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); }
    ctx.stroke(); ctx.restore();
  });
}
/** 水晶球：中心 (x,y)，半径 r；inner() 在球里画（已裁切） */
function crystalBall(x, y, r, inner, o = {}) {
  // 底座
  shape(() => { ctx.moveTo(x - r * 0.62, y + r * 0.78); ctx.lineTo(x - r * 0.8, y + r * 1.12); ctx.lineTo(x + r * 0.8, y + r * 1.12); ctx.lineTo(x + r * 0.62, y + r * 0.78); ctx.closePath(); }, PB.goldD, { w: 4, color: PB.ink, shade: [14, 0] });
  shape(oval(x, y + r * 1.12, r * 0.86, r * 0.12), PB.gold, { w: 4, color: PB.ink });
  shape(circ(x, y, r), '#2a2440', { w: 5, color: PB.ink });
  if (inner) { ctx.save(); ctx.beginPath(); ctx.arc(x, y, r - 4, 0, Math.PI * 2); ctx.clip(); inner(); ctx.restore(); }
  if (o.lit !== false) glowLight(x, y, r * 1.3, r * 1.3, { i: o.lit ?? 0.8, col: '#bcd0ff' });
  over(() => {
    // 玻璃反光
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r - 4, 0, Math.PI * 2); ctx.clip();
    const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, 0, x, y, r); g.addColorStop(0, 'rgba(255,255,255,0.32)'); g.addColorStop(0.35, 'rgba(200,220,255,0.06)'); g.addColorStop(0.85, 'rgba(120,140,220,0.08)'); g.addColorStop(1, 'rgba(180,200,255,0.4)');
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
    ctx.globalAlpha = 0.55 * LA; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = r * 0.05; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(x, y, r * 0.82, Math.PI * 1.08, Math.PI * 1.34); ctx.stroke();
    ctx.restore();
  });
}
/** 塔罗牌背面（散在桌上做点缀） */
function tarotBack(x, y, s, rot) {
  at(x, y, s, rot, () => {
    shape(box(-90, -150, 180, 300, 12), '#2b1838', { w: 4, color: PB.gold });
    shape(box(-74, -134, 148, 268, 8), null, { w: 2, color: PB.gold });
    star(0, 0, 40, PB.gold, null);
    shape(circ(0, 0, 62), null, { w: 2, color: PB.gold });
    for (const [cx, cy] of [[0, -100], [0, 100]]) { ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, 16, 0, Math.PI * 2); ctx.arc(cx + 6, cy - 4, 13, 0, Math.PI * 2, true); ctx.fillStyle = PB.gold; ctx.fill('evenodd'); ctx.restore(); }
  });
}
/** 金色发光的勾（放进发光层） */
function goldTick(x, y, s, p) { over(() => { ctx.save(); ctx.shadowColor = 'rgba(255,200,90,0.95)'; ctx.shadowBlur = 22; tick(x, y, s, p, '#ffc23e', 17); ctx.shadowBlur = 0; tick(x, y, s, p, '#ffe08a', 7); ctx.restore(); }); }
/** 字幕：没有底条，金色衬线字 + 两侧小饰线，暖光晕 */
function candleCap(str, t, a, b, id, o = {}) {
  if (t < a - 0.1 || t > b + 0.3) return;
  const size = o.size || 56, x = o.x ?? CAPX, y = o.y ?? CAPY;
  const { total } = measure(str, size, F.serif, 900);
  const al = Math.min(seg(t, a - 0.1, a + 0.1), 1 - seg(t, b + 0.05, b + 0.3));
  layer(al, () => {
    const g = ctx.createLinearGradient(x - total / 2 - 160, 0, x + total / 2 + 160, 0); g.addColorStop(0, 'rgba(10,6,14,0)'); g.addColorStop(0.2, 'rgba(10,6,14,0.55)'); g.addColorStop(0.8, 'rgba(10,6,14,0.55)'); g.addColorStop(1, 'rgba(10,6,14,0)');
    ctx.save(); ctx.globalAlpha = LA; ctx.fillStyle = g; ctx.fillRect(x - total / 2 - 160, y - size * 1.15, total + 320, size * 1.75); ctx.restore();
    for (const s of [-1, 1]) { const ex = x + s * (total / 2 + 40); line([[ex, y - size * 0.32], [ex + s * 70, y - size * 0.32]], { w: 2.5, color: PB.gold }); star(ex + s * 84, y - size * 0.32, 9, PB.gold, null); }
    txt(str, x, y, { t, t0: a, t1: b + 0.3, size, font: F.serif, weight: 900, color: PB.goldL, id, cps: 0.022, shadow: 1, glow: 0 });
  });
}
