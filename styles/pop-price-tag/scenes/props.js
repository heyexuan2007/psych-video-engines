// 道具：吊牌、爆炸贴、转盘、骰子、法槌、举牌、T 恤、夜市摊、灯串、手、气泡、装饰。全部原创，全部马克笔画法。

/** 吊牌：(x,y) 是牌子中心，w×h，绳子往上拴到 (x+sx, y-h/2-len)。fn 在牌子局部坐标里画内容 */
function priceTag(x, y, w, h, rot, fn, o = {}) {
  const top = -h / 2, cut = w * 0.16, hole = [0, top + cut * 0.9];
  // 绳子（在牌子坐标外画，跟着旋转支点走）
  const len = o.len ?? 420, sx = o.sx ?? 0;
  at(x, y, o.s ?? 1, rot, () => {
    const hr = o.hole ?? 15;
    shape(poly([[-w / 2 + cut, top], [w / 2 - cut, top], [w / 2, top + cut], [w / 2, h / 2], [-w / 2, h / 2], [-w / 2, top + cut]]), o.fill || C.white, { w: 6 });
    shape(circ(hole[0], hole[1], hr), o.bg || C.Y, { w: 5, off: 0 });
    fn && fn();
    line(qd([hole[0], hole[1] - hr * 0.3], [sx * 0.5 + 30, top - len * 0.5], [sx, top - len]), { w: 4, color: o.cord || C.red });
  });
}

/** 爆炸贴：r 半径，n 个尖。fn 在中心画内容 */
function starburst(x, y, r, col, o = {}) {
  const n = o.n ?? 16, rr = rng(o.seed ?? 3), k = o.k ?? 1;
  at(x, y, k, o.rot ?? 0, () => {
    const pts = []; for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2, rad = i % 2 ? r * (0.76 + rr() * 0.05) : r * (1 + rr() * 0.12); pts.push([Math.cos(a) * rad, Math.sin(a) * rad * (o.squash ?? 1)]); }
    shape(poly(pts), col, { w: 6 });
    o.fn && o.fn();
  });
}

/** 小闪光（四角星）和强调线 */
function sparkle(x, y, s = 1, col = C.white, rot = 0) {
  at(x, y, s, rot, () => shape(poly([[0, -34], [8, -8], [34, 0], [8, 8], [0, 34], [-8, 8], [-34, 0], [-8, -8]]), col, { w: 4, off: 2 }));
}
function emph(x, y, r0, r1, n = 5, a0 = -2.4, a1 = -0.8, o = {}) {
  for (let i = 0; i < n; i++) { const a = lerp(a0, a1, n === 1 ? 0.5 : i / (n - 1)); line([[x + Math.cos(a) * r0, y + Math.sin(a) * r0], [x + Math.cos(a) * r1, y + Math.sin(a) * r1]], { w: o.w ?? 6, color: o.color || C.ink, alpha: o.alpha ?? 1 }); }
}

/** 转盘：中心 (x,y)，半径 r，ang 转角（弧度）。labels 每格上的数字；cols 每格颜色。返回停在指针（正上方）那格的序号 */
const WHEEL_COLS = [C.Y, C.B, C.O, C.white, C.G, C.P];
function wheel(x, y, r, ang, o = {}) {
  const labels = o.labels || Array.from({ length: 20 }, (_, i) => String(i * 5)), n = labels.length, cols = o.cols || WHEEL_COLS, da = Math.PI * 2 / n;
  // 支架
  if (o.stand !== false) {
    shape(poly([[-r * 0.08, 0], [r * 0.08, 0], [r * 0.5, r * 1.45], [r * 0.34, r * 1.45]].map(([a, b]) => [x + a, y + b])), C.woodD, { w: 5 });
    shape(poly([[-r * 0.08, 0], [r * 0.08, 0], [-r * 0.34, r * 1.45], [-r * 0.5, r * 1.45]].map(([a, b]) => [x + a, y + b])), C.wood, { w: 5 });
  }
  at(x, y, 1, 0, () => {
    shape(circ(0, 0, r * 1.09), C.red, { w: 6 });
    for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2 + (o.bulbSpin ?? 0); shape(circ(Math.cos(a) * r * 1.045, Math.sin(a) * r * 1.045, r * 0.026), (i + Math.floor((o.t ?? T_NOW) * 6)) % 2 ? '#fff6a8' : C.white, { w: 2.5, off: 0 }); }
    ctx.save(); ctx.rotate(ang);
    for (let i = 0; i < n; i++) {
      const a0 = -Math.PI / 2 - da / 2 + i * da;
      shape(() => { ctx.moveTo(0, 0); ctx.arc(0, 0, r, a0, a0 + da); ctx.closePath(); }, cols[i % cols.length], { w: 4, off: 0 });
      ctx.save(); ctx.rotate(a0 + da / 2 + Math.PI / 2);
      const lab = labels[i], hl = o.hl && o.hl(i);
      ptxt(lab, 0, -r * 0.74, { size: r * (lab.length > 2 ? 0.1 : 0.13), color: hl ? C.red : C.ink, t: 99, t0: 0, jit: 0 });
      ctx.restore();
    }
    ctx.restore();
    shape(circ(0, 0, r * 0.16), C.red, { w: 5 }); shape(circ(0, 0, r * 0.06), C.white, { w: 3, off: 0 });
  });
  // 指针
  if (o.pointer !== false) at(x, y - r * 1.07, 1, o.pRot || 0, () => shape(poly([[-r * 0.1, -r * 0.12], [r * 0.1, -r * 0.12], [0, r * 0.12]]), C.ink, { w: 4, color: C.ink }));
  const k = Math.round((-ang) / da); return ((k % n) + n) % n;
}

/** 骰子（正面看，带一点透视顶面） */
const PIPS = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]], 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]], 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };
function dice(x, y, s, face, rot = 0, o = {}) {
  at(x, y, s, rot, () => {
    shape(poly([[-50, -50], [-30, -72], [70, -72], [50, -50]]), '#e9e4d8', { w: 5, off: 0 });
    shape(poly([[50, -50], [70, -72], [70, 28], [50, 50]]), '#d2ccbe', { w: 5, off: 0 });
    shape(box(-50, -50, 100, 100, 14), C.white, { w: 5.5, off: 0 });
    for (const [a, b] of PIPS[face] || []) shape(circ(a * 26, b * 26, 9.5), face === 1 || o.red ? C.red : C.ink, { stroke: false, off: 0 });
  });
}

/** 法槌：手柄 + 槌头，(x,y) 槌头中心 */
function gavel(x, y, s = 1, rot = 0) {
  at(x, y, s, rot, () => {
    shape(box(-12, 0, 24, 190, 8), C.woodL, { w: 4.5 });
    shape(box(-80, -40, 160, 80, 22), C.woodD, { w: 5.5, shade: [0, -10] });
    for (const sx of [-1, 1]) shape(box(sx * 62 - 10, -44, 20, 88, 8), C.wood, { w: 4 });
  });
}
function block(x, y, s = 1) { at(x, y, s, 0, () => { shape(oval(0, 8, 90, 22), C.woodD, { w: 5 }); shape(oval(0, -6, 90, 22), C.woodL, { w: 5 }); }); }

/** 举牌：(x,y) 牌子中心；fn 画内容 */
function sign(x, y, w, h, rot = 0, fn, o = {}) {
  at(x, y, o.s ?? 1, rot, () => {
    if (o.stick !== false) shape(box(-9, h / 2 - 6, 18, o.stick ?? 170, 4), C.woodL, { w: 4 });
    shape(box(-w / 2, -h / 2, w, h, 10), o.fill || C.white, { w: 6 });
    fn && fn();
  });
}

/** T 恤（挂在衣架上），(x,y) 衣架钩顶 */
function tshirt(x, y, s = 1, col = C.P, o = {}) {
  at(x, y, s, o.rot ?? 0, () => {
    line([[0, 0], [0, 26]], { w: 5 }); line(qd([0, 0], [16, -16], [8, -26]), { w: 5 });
    line([[-86, 52], [0, 26], [86, 52]], { w: 6 });
    shape(() => { ctx.moveTo(-40, 40); ctx.quadraticCurveTo(0, 62, 40, 40); ctx.lineTo(96, 66); ctx.lineTo(122, 128); ctx.lineTo(84, 146); ctx.lineTo(74, 118); ctx.lineTo(74, 300); ctx.lineTo(-74, 300); ctx.lineTo(-74, 118); ctx.lineTo(-84, 146); ctx.lineTo(-122, 128); ctx.lineTo(-96, 66); ctx.closePath(); }, col, { w: 5.5, shade: [-12, 0] });
    line(qd([-30, 44], [0, 72], [30, 44]), { w: 4 });
    if (o.print) o.print();
  });
}

/** 夜市摊：棚子 + 桌子。gy 地面，x 中心，w 宽 */
function stall(x, gy, w, o = {}) {
  const top = gy - (o.h ?? 640), col = o.col || C.red;
  for (const sx of [-1, 1]) shape(box(x + sx * (w / 2 - 10) - 10, top, 20, gy - top, 4), C.woodD, { w: 4.5 });
  // 条纹棚子 + 波浪边
  const n = o.n ?? 6, sw = w / n;
  for (let i = 0; i < n; i++) shape(poly([[x - w / 2 + i * sw, top - 90], [x - w / 2 + (i + 1) * sw, top - 90], [x - w / 2 + (i + 1) * sw + 20, top], [x - w / 2 + i * sw + 20, top]]), i % 2 ? C.white : col, { w: 5, off: 0 });
  for (let i = 0; i < n; i++) shape(() => { const x0 = x - w / 2 + i * sw + 20; ctx.moveTo(x0, top); ctx.arc(x0 + sw / 2, top, sw / 2, 0, Math.PI); ctx.closePath(); }, i % 2 ? C.white : col, { w: 5, off: 0 });
  if (o.label) { const lx = x + (o.labelX ?? 0); shape(box(lx - 150, top - 170, 300, 74, 10), C.Y, { w: 5 }); ptxt(o.label, lx, top - 116, { size: 46, t: 99, t0: 0 }); }
  // 桌子
  if (o.table !== false) { shape(box(x - w / 2 + 30, gy - 200, w - 60, 34, 6), C.wood, { w: 5 }); shape(box(x - w / 2 + 50, gy - 166, w - 100, 166, 4), C.woodL, { w: 5, shade: [0, -14] }); }
}

/** 灯串：从 (x0,y0) 到 (x1,y1) 垂下来，n 个灯泡 */
function lights(x0, y0, x1, y1, sag, n, t = T_NOW, o = {}) {
  const pts = qd([x0, y0], [(x0 + x1) / 2, (y0 + y1) / 2 + sag * 2], [x1, y1], n * 2);
  line(pts, { w: 3.5 });
  for (let i = 1; i < n; i++) { const [px, py] = pts[i * 2], on = hash(i * 3.3 + Math.floor(t * 3)) > 0.25; shape(oval(px, py + 18, 11, 15), on ? (o.col || '#fff27a') : '#c9b85a', { w: 3, off: 0 }); }
}

/** 一只手（从画面下方伸进来，食指朝上）。(x,y) 指尖 */
function hand(x, y, s = 1, rot = 0, o = {}) {
  at(x, y, s, rot, () => {
    const sl = o.sleeve || C.cream;
    shape(box(-70, 190, 150, 400, 20), sl, { shade: [-12, 0] });
    shape(box(-76, 176, 162, 34, 8), mixc(sl, '#000000', 0.12));
    shape(() => { ctx.moveTo(-58, 186); ctx.quadraticCurveTo(-74, 120, -48, 82); ctx.lineTo(48, 70); ctx.quadraticCurveTo(80, 110, 66, 186); ctx.closePath(); }, C.skin, { shade: [-10, 0] });
    for (let i = 0; i < 3; i++) shape(box(-10 + i * 24, 66 + i * 4, 30, 54, 14), C.skin, { w: 4, off: 0 });
    shape(() => { ctx.moveTo(-50, 140); ctx.quadraticCurveTo(-92, 110, -78, 84); ctx.quadraticCurveTo(-60, 76, -40, 104); ctx.closePath(); }, C.skin, { w: 4.5, off: 0 });
    shape(box(-42, -6, 34, 108, 17), C.skin, { w: 4.5, off: 0 });
    shape(box(-37, 0, 24, 22, 9), '#ffeede', { w: 2.5, off: 0 });
  });
}

/** POP 气泡：白底粗边，尾巴指向 (tx,ty)（相对中心） */
function say(str, cx, cy, p, o = {}) {
  if (p <= 0) return;
  const size = o.size || 50; ctx.font = fontOf(size, F.sans, 900);
  const w = ctx.measureText(plain(str)).width + size * 1.3, h = size * 2.0, tx = o.tx ?? -w * 0.2, ty = o.ty ?? h / 2 + 46;
  layer(seg(p, 0, 0.3), () => at(cx, cy, E.back(p, 2), o.rot ?? -0.03, () => {
    shape(() => { ctx.roundRect(-w / 2, -h / 2, w, h, h * 0.45); }, o.fill || C.white, { w: 5.5, off: 0 });
    shape(poly([[tx - 22, h / 2 - 4], [tx + 22, h / 2 - 4], [tx * 1.1 - 4, ty]]), o.fill || C.white, { w: 5.5, off: 0 });
    line([[tx - 18, h / 2 - 1], [tx + 18, h / 2 - 1]], { w: 8, color: o.fill || C.white });
    ptxt(str, 0, size * 0.36, { size, t: 99, t0: 0, color: o.color || C.ink, seed: o.seed ?? 4 });
  }));
}

/** 圆形红章（年份） */
function roundStamp(str, x, y, s, rot, p) {
  if (p <= 0) return;
  const k = lerp(2.0, 1, E.out(p));
  layer(seg(p, 0, 0.25), () => at(x, y, s * k, rot, () => {
    shape(circ(0, 0, 96), null, { w: 7, color: C.red, off: 0 });
    shape(circ(0, 0, 80), null, { w: 3, color: C.red, off: 0 });
    ptxt(str, 0, 22, { size: 60, color: C.red, t: 99, t0: 0, jit: 0, font: F.serif });
  }));
}

/** 横幅（顶上挂着的白条），fn 画字 */
function banner(x, y, w, h, rot, fn, o = {}) {
  at(x, y, 1, rot, () => {
    for (const sx of [-1, 1]) line([[sx * (w / 2 - 30), -h / 2], [sx * (w / 2 - 10), -h / 2 - 300]], { w: 4 });
    shape(box(-w / 2, -h / 2, w, h, 8), o.fill || C.white, { w: 6 });
    fn && fn();
  });
}

/** 小人图标（统计用），col 填色 */
function pict(x, y, s, col) {
  at(x, y, s, 0, () => { shape(circ(0, -78, 18), col, { w: 3.5, off: 0 }); shape(() => { ctx.moveTo(-26, 0); ctx.lineTo(-26, -36); ctx.quadraticCurveTo(-26, -54, 0, -56); ctx.quadraticCurveTo(26, -54, 26, -36); ctx.lineTo(26, 0); ctx.closePath(); }, col, { w: 3.5, off: 0 }); });
}

/** 月亮（夜市） */
function moon(x, y, r) {
  // 月牙：外圆在内圆外面的那段 + 内圆在外圆里面的那段（反向）
  const ix = x + r * 0.45, iy = y - r * 0.2, ir = r * 0.85, out = [], inn = [];
  const a0 = Math.atan2(iy - y, ix - x);
  for (let i = 0; i <= 120; i++) { const a = a0 + i / 120 * Math.PI * 2, px = x + Math.cos(a) * r, py = y + Math.sin(a) * r; if (Math.hypot(px - ix, py - iy) > ir) out.push([px, py]); }
  const b0 = Math.atan2(y - iy, x - ix);
  for (let i = 0; i <= 120; i++) { const a = b0 - Math.PI + i / 120 * Math.PI * 2, px = ix + Math.cos(a) * ir, py = iy + Math.sin(a) * ir; if (Math.hypot(px - x, py - y) < r) inn.push([px, py]); }
  const last = out[out.length - 1], d0 = Math.hypot(inn[0][0] - last[0], inn[0][1] - last[1]), d1 = Math.hypot(inn[inn.length - 1][0] - last[0], inn[inn.length - 1][1] - last[1]);
  shape(poly(out.concat(d0 < d1 ? inn : inn.reverse())), C.Y, { w: 5 });
}

/** 铁锚：(x,y) 锚环圆心，s 大小。返回锚环位置（当前坐标） */
function anchorIcon(x, y, s = 1, rot = 0, o = {}) {
  const col = o.col || '#9aa3b2';
  at(x, y, s, rot, () => {
    // 两条弯臂 + 锚爪
    tube(arcPts(0, 70, 120, 110, 0.15, Math.PI - 0.15, 24), 26, col);
    for (const sx of [-1, 1]) { const a = sx > 0 ? 0.15 : Math.PI - 0.15, px = Math.cos(a) * 120, py = 70 + Math.sin(a) * 110; shape(poly([[px - 26, py + 10], [px + 26, py + 10], [px + sx * 6, py - 52]]), col, { w: 5, off: 0 }); }
    // 锚杆 + 横杆 + 锚环
    shape(box(-17, 28, 34, 160, 10), col, { w: 5, off: 0, shade: [8, 0] });
    shape(box(-78, 50, 156, 30, 12), col, { w: 5, off: 0 });
    shape(circ(0, 0, 30), null, { w: 14, color: C.ink, off: 0 }); shape(circ(0, 0, 30), null, { w: 7, color: col, off: 0 });
  });
  return [x, y - 30 * s];
}

/** 绳子：从 a 到 b，sag 下垂（0 = 绷直），带麻绳的斜纹 */
function rope(a, b, sag = 0, o = {}) {
  const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag], pts = qd(a, mid, b, 30);
  line(pts, { w: 15, color: C.ink, raw: 1, alpha: o.alpha });
  line(pts, { w: 9, color: o.col || '#d9a95b', raw: 1, alpha: o.alpha });
  const L = plen(pts);
  for (let d = 10; d < L; d += 16) { const q = cutTo(pts, d), [px, py] = q[q.length - 1], [qx, qy] = q[Math.max(0, q.length - 2)], ang = Math.atan2(py - qy, px - qx); line([[px - Math.cos(ang + 0.9) * 5, py - Math.sin(ang + 0.9) * 5], [px + Math.cos(ang + 0.9) * 5, py + Math.sin(ang + 0.9) * 5]], { w: 2.4, color: '#7a5420', raw: 1, alpha: o.alpha }); }
}

/** 大尺子：x0 处是 v0，x1 处是 v1，y 是尺子上沿；major 每隔多少写一个数 */
function ruler(x0, x1, y, v0, v1, o = {}) {
  const h = o.h ?? 80, step = o.step ?? 10, major = o.major ?? 50, X = v => lerp(x0, x1, (v - v0) / (v1 - v0));
  shape(box(x0 - 40, y, x1 - x0 + 80, h, 10), o.fill || C.white, { w: 6 });
  for (let v = v0; v <= v1 + 1e-6; v += step) { const big = Math.abs(v % major) < 1e-6; line([[X(v), y + 4], [X(v), y + (big ? 34 : 20)]], { w: big ? 5 : 3.5 }); if (big && o.nums !== false) ptxt(String(v), X(v), y + h - 10, { size: 32, t: 99, t0: 0, jit: 0 }); }
  return X;
}

/** 夹板（经纪人手里） */
function clipboard(x, y, s = 1, rot = 0) {
  at(x, y, s, rot, () => {
    shape(box(-34, -46, 68, 92, 6), C.woodL, { w: 4.5, off: 0 });
    shape(box(-26, -34, 52, 72, 3), C.white, { w: 3, off: 0 });
    shape(box(-14, -54, 28, 16, 4), C.grayD, { w: 3, off: 0 });
    for (let i = 0; i < 3; i++) line([[-18, -18 + i * 16], [18, -18 + i * 16]], { w: 2.5, alpha: 0.6 });
  });
}

/** 房子（正面） */
function house(x, y, s = 1) {
  at(x, y, s, 0, () => {
    shape(box(80, -150, 44, 90, 4), C.woodD, { w: 5 });
    shape(box(-150, -40, 300, 200, 6), C.cream, { w: 6, shade: [-16, 0] });
    shape(poly([[-190, -26], [0, -172], [190, -26]]), C.red, { w: 6 });
    shape(box(-30, 62, 60, 98, 6), C.woodL, { w: 5 });
    shape(circ(16, 112, 5), C.ink, { stroke: false, off: 0 });
    for (const sx of [-1, 1]) { shape(box(sx * 95 - 36, 14, 72, 62, 6), C.B, { w: 5 }); line([[sx * 95, 14], [sx * 95, 76]], { w: 3.5 }); line([[sx * 95 - 36, 45], [sx * 95 + 36, 45]], { w: 3.5 }); }
  });
}

/** 想法泡泡（云朵 + 三个小圆点拖到 (tx,ty)） */
function thought(x, y, w, h, p, tx, ty, fn) {
  if (p <= 0) return;
  layer(seg(p, 0, 0.3), () => {
    for (let i = 0; i < 3; i++) { const u = 0.25 + i * 0.22; if (p > i * 0.12) shape(circ(lerp(tx, x, u), lerp(ty, y + h * 0.45, u), 9 + i * 7), C.white, { w: 4, off: 0 }); }
    at(x, y, E.back(seg(p, 0.15, 1), 1.8), 0, () => {
      const n = 10, rad = Math.min(w, h) * 0.34, cs = [];
      for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2; cs.push([Math.cos(a) * w * 0.4, Math.sin(a) * h * 0.36, rad * (0.85 + 0.3 * hash(i * 3.7))]); }
      for (const [a, b, r] of cs) shape(circ(a, b, r), null, { w: 5.5, off: 0 });
      for (const [a, b, r] of cs) shape(circ(a, b, r), C.white, { stroke: false, off: 0 });
      shape(oval(0, 0, w * 0.42, h * 0.38), C.white, { stroke: false, off: 0 });
      fn && fn();
    });
  });
}

/** 打勾（绿芯黑边），p 写出进度 */
function check(x, y, s, p) {
  const pts = [[x - 22 * s, y], [x - 4 * s, y + 20 * s], [x + 30 * s, y - 24 * s]];
  stroke(pts, p, { w: 13 * s, color: C.ink, raw: 1 }); stroke(pts, p, { w: 7 * s, color: C.G, raw: 1 });
}

/** 灰尘小团（落地） */
function puff(x, y, p, dir = 1) {
  if (p <= 0 || p >= 1) return;
  for (let i = 0; i < 3; i++) { const q = E.out(p), r = 14 + i * 6; shape(circ(x + dir * (20 + i * 26) * q, y - 10 - i * 8 * q, r * (1 - p * 0.6)), C.white, { w: 3.5, off: 0, alpha: 1 - p }); }
}
