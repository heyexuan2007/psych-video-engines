// 布景和道具：都搭在同一块舞台上。地板线 FLOOR=720（镜头 s=1 时），舞台世界宽 -640..2560。
const FLOOR = 720, SX0 = -1000, SW = 3900;
let BACKDROP = null, BOARDS = null;
function makeStage() {
  BACKDROP = document.createElement('canvas'); BACKDROP.width = SW; BACKDROP.height = FLOOR + 40;
  let g = BACKDROP.getContext('2d');
  for (let x = 0; x < SW; x++) { const k = 0.5 + 0.5 * Math.sin(x / 38 + Math.sin(x / 113) * 1.6); g.fillStyle = mixc('#3a0b14', '#8e2232', Math.pow(k, 1.5)); g.fillRect(x, 0, 1, FLOOR + 40); }
  let v = g.createLinearGradient(0, 0, 0, FLOOR + 40); v.addColorStop(0, 'rgba(0,0,0,0.5)'); v.addColorStop(0.5, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.25)'); g.fillStyle = v; g.fillRect(0, 0, SW, FLOOR + 40);
  BOARDS = document.createElement('canvas'); BOARDS.width = SW; BOARDS.height = 700;
  g = BOARDS.getContext('2d'); const r = rng(5), vx = SW / 2 - SX0 * 0 - 640 + 960, vy = -900;
  g.fillStyle = C.wood; g.fillRect(0, 0, SW, 700);
  for (let i = -60; i <= 60; i++) {   // 木板缝：往舞台深处收
    const xb = (SW / 2) + i * 120, xt = lerp(xb, SW / 2, 0.42);
    g.fillStyle = r() < 0.5 ? 'rgba(60,35,20,0.25)' : 'rgba(255,220,170,0.06)';
    g.beginPath(); g.moveTo(xt, 0); g.lineTo(xt + 50, 0); g.lineTo(xb + 120, 700); g.lineTo(xb, 700); g.closePath(); g.fill();
    g.strokeStyle = 'rgba(40,22,12,0.55)'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(xt, 0); g.lineTo(xb, 700); g.stroke();
  }
  for (let i = 0; i < 9000; i++) { g.fillStyle = r() < 0.5 ? 'rgba(40,20,10,0.08)' : 'rgba(255,230,190,0.05)'; g.fillRect(r() * SW, r() * 700, 2 + r() * 30, 1); }
  v = g.createLinearGradient(0, 0, 0, 700); v.addColorStop(0, 'rgba(0,0,0,0.35)'); v.addColorStop(0.25, 'rgba(0,0,0,0)'); g.fillStyle = v; g.fillRect(0, 0, SW, 700);
}
/** 舞台：天鹅绒背幕 + 木地板 */
function stage(o = {}) {
  if (!BACKDROP) makeStage();
  ctx.save(); ctx.globalAlpha = LA;
  if (o.wall) { ctx.fillStyle = o.wall; ctx.fillRect(SX0, -400, SW, FLOOR + 400); } else { ctx.fillStyle = '#3a0b14'; ctx.fillRect(SX0, -400, SW, 420); ctx.drawImage(BACKDROP, SX0, 0); }
  ctx.drawImage(BOARDS, SX0, FLOOR);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(SX0, FLOOR - 4, SW, 8);
  ctx.restore();
}

/** 课桌（正面）：桌面中心 (x, ty)，地面 gy */
function desk(x, gy, s = 1, col = C.woodL) {
  at(x, gy, s, 0, () => {
    shape(box(-96, -150, 192, 26, 6), col, { shade: [0, -6] });
    shape(box(-84, -126, 168, 60, 4), mixc(col, '#000000', 0.25));
    for (const sx of [-1, 1]) shape(box(sx * 78 - 7, -70, 14, 70, 3), C.grayD);
  });
}
/** 讲台上的立式黑板 */
function blackboard(x, gy, s = 1, write = null) {
  at(x, gy, s, 0, () => {
    for (const sx of [-1, 1]) line([[sx * 150, -10], [sx * 120, -260]], { w: 12, color: C.woodD });
    shape(box(-200, -440, 400, 240, 8), C.woodD);
    shape(box(-186, -426, 372, 212, 4), '#2f4a3e', { w: 3 });
    if (write) write();
  });
}
/** 布景门（一块立板） */
function doorFlat(x, gy, s = 1, open = 0) {
  at(x, gy, s, 0, () => {
    shape(box(-100, -360, 200, 360, 4), '#d8c7a6', { shade: [8, 0] });
    shape(box(-80, -340, 160, 340, 3), open > 0.05 ? '#120d10' : '#a87d52');
    if (open > 0.05) { const w = 160 * (1 - 0.75 * open); shape(poly([[-80, -340], [-80 + w, -330 + 18 * open], [-80 + w, -10 * open], [-80, 0]]), '#a87d52'); }
    else shape(circ(52, -170, 9), C.warm, { w: 3 });
  });
}
/** 床（侧面），人躺在里面：头在左。返回枕头上的头位置 */
function bed(x, gy, s = 1, o = {}) {
  let head = null;
  at(x, gy, s, 0, () => {
    shape(box(-300, -230, 34, 230, 6), C.woodD);
    shape(box(270, -150, 30, 150, 6), C.woodD);
    shape(box(-280, -120, 560, 70, 10), C.woodL, { shade: [0, -8] });
    shape(oval(-200, -150, 70, 30), C.white);
    head = [-196, -190];
    if (o.kid !== false) at(-196, -170, 0.62, 0.0, () => {
      shape(circ(0, -48, 68), C.skin, { shade: [-12, 4] });
      ctx.save(); ctx.translate(0, 214); drawHair({ hair: o.hair ?? 5, hairCol: o.hairCol }, 1); drawFace({ eyes: o.eyes || 'wide', mouth: o.mouth || 'wave', brow: o.brow ?? -0.6, look: o.look || [0, -1], blush: o.blush }, 1); ctx.restore();
    });
    shape(() => { ctx.moveTo(-150, -170); ctx.quadraticCurveTo(80, -200, 270, -150); ctx.lineTo(276, -96); ctx.lineTo(-150, -96); ctx.closePath(); }, o.blanket || C.blue, { shade: [0, 10] });
    for (const sx of [-1, 1]) shape(box(sx * 260 - 8, -50, 16, 50, 3), C.woodD);
  });
  return head;
}
/** 窗户 + 月亮（月亮是发光的） */
function windowMoon(x, y, s = 1) {
  at(x, y, s, 0, () => {
    shape(box(-120, -150, 240, 300, 6), '#16203a', { w: 10, color: C.woodD });
    line([[0, -150], [0, 150]], { w: 8, color: C.woodD }); line([[-120, 0], [120, 0]], { w: 8, color: C.woodD });
    glowLight(40, -70, 220, 240, { col: C.moon, i: 0.55 });
  });
  over(() => at(x, y, s, 0, () => { ctx.save(); ctx.shadowColor = C.moon; ctx.shadowBlur = 40; shape(circ(48, -78, 34), '#eef4ff', { stroke: false }); ctx.restore(); shape(circ(60, -88, 28), '#16203a', { stroke: false }); }));
}

/** 想法泡泡（发光层，暗处也看得清） */
function thought(cx, cy, rx, ry, p, tail = []) {
  if (p <= 0) return;
  for (const [x, y, r] of tail) shape(circ(x, y, r), C.white, { w: 4, alpha: clamp(p * 2) });
  at(cx, cy, 0.5 + 0.5 * E.back(clamp(p)), 0, () => {
    const pts = [], n = 64; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, k = 1 + 0.08 * Math.abs(Math.sin(a * 4.5)); pts.push([Math.cos(a) * rx * k, Math.sin(a) * ry * k]); }
    shape(poly(pts), C.white, { w: 4.5 });
  });
}
/** 说话气泡 */
function speech(cx, cy, w, h, p, o = {}) {
  if (p <= 0) return;
  at(cx, cy, 0.6 + 0.4 * E.back(clamp(p)), o.rot || 0, () => {
    const tx = o.tx ?? 0, fill = o.fill || C.white;
    shape(poly([[tx - 14, h / 2 - 3], [tx + (o.dir || 0) * 24, h / 2 + 30], [tx + 14, h / 2 - 3]]), fill, { w: 4.5 });
    shape(box(-w / 2, -h / 2, w, h, Math.min(w, h) * 0.36), fill, { w: 4.5 });
    line([[tx - 10, h / 2], [tx + 10, h / 2]], { w: 7, color: fill });
  });
}
/** 暗处的一双眼睛（发光层）。open 0..1 睁开的程度，look 看的方向 */
function eyePair(x, y, s, open, look = [0, 0], o = {}) {
  if (open <= 0.02) return;
  at(x, y, s, 0, () => {
    for (const sx of [-1, 1]) {
      ctx.save(); ctx.globalAlpha = LA; ctx.shadowColor = rgba(C.beam, 0.8); ctx.shadowBlur = 16;
      ctx.fillStyle = '#fff7e2'; ctx.beginPath(); ctx.ellipse(sx * 17, 0, 11, 12 * open, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      if (open > 0.4) shape(circ(sx * 17 + look[0] * 4, look[1] * 4, 5), C.ink, { stroke: false });
    }
  });
}
/** 红印章 */
function stamp(txt0, x, y, s, rot, p, alpha = 1) {
  if (p <= 0 || alpha <= 0.003) return;
  const k = lerp(2.2, 1, E.out(p)), size = 70, { total } = measure(txt0, size, F.serif, 900), w = total + 80, h = 124;
  layer(seg(p, 0, 0.25) * alpha, () => at(x, y, s * k, rot, () => {
    shape(box(-w / 2, -h / 2, w, h, 8), 'rgba(20,6,8,0.55)', { w: 7, color: C.red });
    shape(box(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 5), null, { w: 3, color: C.red });
    txt(txt0, 0, 25, { size, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, shadow: 0 });
  }));
}
/** 手机（剪纸）：中心 (x,y) */
function phone(x, y, s = 1, on = 1, rot = 0) {
  at(x, y, s, rot, () => { shape(box(-24, -44, 48, 88, 9), C.ink, { w: 3 }); shape(box(-18, -36, 36, 66, 4), on ? '#cfe6ff' : '#30343c', { stroke: false }); });
  if (on) glowLight(x, y, 60 * s, 70 * s, { col: '#bcd8ff', i: 0.5 * on });
}
/** 小镜子（手持） */
function mirror(x, y, s = 1) { at(x, y, s, 0, () => { line([[0, 30], [0, 70]], { w: 10, color: C.woodD }); shape(oval(0, 0, 30, 38), '#cfe0e8', { w: 4 }); line([[-12, -16], [-2, -26]], { w: 4, color: '#ffffff' }); }); }
/** 一圈小字：Zzz */
function zzz(x, y, t, s = 1) {
  for (let i = 0; i < 3; i++) { const ph = (t * 0.6 + i / 3) % 1; layer(Math.sin(Math.PI * ph), () => txt('Z', x + ph * 50 * s, y - ph * 90 * s, { size: (26 + i * 8) * s, font: F.lat, weight: 900, color: C.moon, t: 99, t0: 0, cps: 0, shadow: 0 })); }
}
