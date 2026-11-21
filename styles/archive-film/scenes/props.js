// 道具：实验室布景、电击发生器、手、小人图标、手机来电、印章。全部原创。

/** 实验室墙面：上半刷漆，下半木护墙板，地面 */
function labRoom(o = {}) {
  const gy = o.gy ?? 820;
  shape(box(-200, -200, W + 400, gy + 200), o.wall || C.wall, { stroke: false });
  shape(box(-200, gy - 300, W + 400, 300), C.woodL, { stroke: false });
  for (let x = -200; x < W + 200; x += 120) line([[x, gy - 300], [x, gy]], { w: 3, color: C.woodD, alpha: 0.6 });
  shape(box(-200, gy - 312, W + 400, 16), C.woodD, { stroke: false });
  shape(box(-200, gy, W + 400, 600), C.floor, { stroke: false });
  for (let x = -200; x < W + 200; x += 90) line([[x, gy], [x - 40, gy + 400]], { w: 2, color: '#4b3d2e', alpha: 0.5 });
  if (o.clock !== false) at(o.clockX ?? 300, 210, 1, 0, () => {
    shape(circ(0, 0, 58), C.white, { w: 6 });
    for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; line([[Math.cos(a) * 46, Math.sin(a) * 46], [Math.cos(a) * 52, Math.sin(a) * 52]], { w: 3 }); }
    const m = (o.t ?? T_NOW) * 0.5; line([[0, 0], [Math.cos(m - 1.6) * 40, Math.sin(m - 1.6) * 40]], { w: 3 }); line([[0, 0], [Math.cos(-0.6) * 28, Math.sin(-0.6) * 28]], { w: 5 });
  });
}

/** 电击发生器。中心 x，面板顶 y，u 每个开关的间距。o.down 已按下的个数，o.lit 亮着的红灯（默认等于 down），o.redTail 最后几个标红 */
const SW_LABELS = ['轻微电击', '中度电击', '强电击', '很强电击', '剧烈电击', '极剧烈电击', '危险：严重电击', 'XXX'];
function generator(cx, y, u = 46, o = {}) {
  const n = 30, w = u * n + 80, x0 = cx - w / 2, h = o.h ?? 330, down = o.down ?? 0, lit = o.lit ?? down;
  // 机箱
  shape(box(x0 - 14, y - 14, w + 28, h + 28, 14), C.bake, { w: 5 });
  shape(box(x0, y, w, h, 8), C.metal, { w: 4, shade: [0, -8] });
  for (const [sx, sy] of [[x0 + 20, y + 20], [x0 + w - 20, y + 20], [x0 + 20, y + h - 20], [x0 + w - 20, y + h - 20]]) shape(circ(sx, sy, 7), C.metalL, { w: 2.5 });
  // 铭牌
  shape(box(cx - 250, y + 22, 500, 54, 4), C.ink, { w: 3 });
  txt('电击发生器  ZLB 型', cx, y + 61, { size: 32, font: F.serif, weight: 900, color: C.metalL, t: 99, t0: 0, cps: 0, shadow: 0 });
  // 右上：电压表
  at(x0 + w - 130, y + 66, 1, 0, () => {
    shape(box(-80, -44, 160, 88, 8), C.paper, { w: 4 });
    for (let i = 0; i <= 10; i++) { const a = Math.PI * (1.15 + 0.7 * i / 10); line([[Math.cos(a) * 52, 36 + Math.sin(a) * 52], [Math.cos(a) * 62, 36 + Math.sin(a) * 62]], { w: 2.5 }); }
    const a = Math.PI * (1.15 + 0.7 * clamp(down / 30)) + (o.needleShake ? Math.sin(T_NOW * 40) * 0.02 : 0);
    line([[0, 36], [Math.cos(a) * 58, 36 + Math.sin(a) * 58]], { w: 4, color: C.ink });
  });
  // 左上：总开关
  at(x0 + 120, y + 66, 1, 0, () => { shape(box(-60, -30, 120, 60, 6), C.metalD, { w: 3 }); txt('电源', 0, 12, { size: 24, font: F.sans, weight: 700, color: C.metalL, t: 99, t0: 0, cps: 0, shadow: 0 }); });
  // 分组标签（每组 4 个，最后一组 2 个）
  const sx = (i) => x0 + 40 + u * (i + 0.5);
  for (let gI = 0; gI < 8; gI++) {
    const a = gI * 4, b = Math.min(29, a + 3), xa = sx(a) - u * 0.42, xb = sx(b) + u * 0.42, ly = y + 132;
    line([[xa, ly + 10], [xa, ly + 18], [xb, ly + 18], [xb, ly + 10]], { w: 2.5, color: C.ink });
    const lab = SW_LABELS[gI], isRed = gI >= 6 && o.redTail !== false;
    const sz = lab.length > 5 ? Math.min(22, (xb - xa) / lab.length * 1.05) : 24;
    if (isRed) red(() => txt(lab, (xa + xb) / 2, ly, { size: sz, font: F.sans, weight: 700, color: C.red, t: 99, t0: 0, cps: 0, shadow: 0 }));
    else txt(lab, (xa + xb) / 2, ly, { size: sz, font: F.sans, weight: 700, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
  }
  // 开关
  for (let i = 0; i < n; i++) {
    const x = sx(i), v = 15 * (i + 1), py = y + 172;
    // 指示灯
    shape(circ(x, py + 6, 8), '#4a2a26', { w: 2.5 });
    if (i < lit) red(() => { ctx.save(); ctx.globalAlpha = LA; ctx.fillStyle = C.redL; ctx.beginPath(); ctx.arc(x, py + 6, 8, 0, Math.PI * 2); ctx.fill(); ctx.restore(); });
    // 电压数字
    const vs = String(v), vsz = u < 50 ? 17 : 20;
    if (i >= 28 && o.redTail !== false) red(() => txt(vs, x, py + 44, { size: vsz, font: F.mono, weight: 700, color: C.red, t: 99, t0: 0, cps: 0, spacing: -0.05, shadow: 0 }));
    else txt(vs, x, py + 44, { size: vsz, font: F.mono, weight: 700, color: C.ink, t: 99, t0: 0, cps: 0, spacing: -0.05, shadow: 0 });
    // 拨杆：底座 + 杆（按下的朝下）
    const dn = i < down, bw = u * 0.62;
    shape(box(x - bw / 2, py + 60, bw, 70, 5), C.bake, { w: 3 });
    shape(box(x - bw / 2 + 5, dn ? py + 96 : py + 66, bw - 10, 28, 4), dn ? C.metalL : C.paper, { w: 2.5 });
    txt('V', x, py + 160, { size: 14, font: F.mono, weight: 700, color: C.metalD, t: 99, t0: 0, cps: 0, shadow: 0 });
  }
  return { sx, y: y + 232 };
}

/** 一只手（从画面下方伸进来，食指朝上方指着）。(x,y) 指尖，s 大小，rot 旋转。sleeve 袖子颜色 */
function hand(x, y, s = 1, rot = 0, o = {}) {
  at(x, y, s, rot, () => {
    const sl = o.sleeve || C.cream;
    // 袖子
    shape(box(-70, 190, 150, 400, 20), sl, { shade: [-12, 0] });
    shape(box(-76, 176, 162, 34, 8), mixc(sl, '#000000', 0.12));
    // 手掌 + 蜷着的三根手指
    shape(() => { ctx.moveTo(-58, 186); ctx.quadraticCurveTo(-74, 120, -48, 82); ctx.lineTo(48, 70); ctx.quadraticCurveTo(80, 110, 66, 186); ctx.closePath(); }, C.skin, { shade: [-10, 0] });
    for (let i = 0; i < 3; i++) shape(box(-10 + i * 24, 66 + i * 4, 30, 54, 14), C.skin, { w: 4 });
    // 大拇指
    shape(() => { ctx.moveTo(-50, 140); ctx.quadraticCurveTo(-92, 110, -78, 84); ctx.quadraticCurveTo(-60, 76, -40, 104); ctx.closePath(); }, C.skin, { w: 4.5 });
    // 食指
    shape(box(-42, -6, 34, 108, 17), C.skin, { w: 4.5 });
    line([[-34, 34], [-16, 34]], { w: 2.5, alpha: 0.5 });
    shape(box(-37, 0, 24, 22, 9), '#f8e4d2', { w: 2.5 });
    if (o.tremble) {}  // 抖动由调用方给 x/y 加
  });
}

/** 小人图标（统计用）：头 + 身子。col 为空就画实物层（会被去色），否则画在红色层 */
function pict(x, y, s, col) {
  const draw = (c) => at(x, y, s, 0, () => { shape(circ(0, -78, 18), c, { stroke: false }); shape(() => { ctx.moveTo(-26, 0); ctx.lineTo(-26, -36); ctx.quadraticCurveTo(-26, -54, 0, -56); ctx.quadraticCurveTo(26, -54, 26, -36); ctx.lineTo(26, 0); ctx.closePath(); }, c, { stroke: false }); });
  if (col) red(() => draw(col)); else draw('#6a5e50');
}

/** 印章（盖在胶片上的红章，画在红色层） */
function stamp(str, x, y, s, rot, p, o = {}) {
  if (p <= 0) return;
  const k = lerp(2.2, 1, E.out(p)), size = o.size || 70;
  red(() => layer(seg(p, 0, 0.25), () => at(x, y, s * k, rot, () => {
    const { total } = measure(str, size, F.serif, 900), w = total + 80, h = size * 1.75;
    shape(box(-w / 2, -h / 2, w, h, 8), null, { w: 7, color: C.red });
    shape(box(-w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 5), null, { w: 3, color: C.red });
    txt(str, 0, size * 0.36, { size, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, shadow: 0 });
  })));
}

/** 对话气泡（实物层） */
function speech(cx, cy, w, h, o = {}) {
  const tx = o.tx ?? cx - w * 0.25, ty = o.ty ?? cy + h / 2 + 40;
  shape(() => { ctx.roundRect(cx - w / 2, cy - h / 2, w, h, Math.min(w, h) * 0.3); }, o.fill || C.white, { w: 4.5 });
  shape(poly([[tx - 18, cy + h / 2 - 3], [tx + 18, cy + h / 2 - 3], [tx - 6, ty]]), o.fill || C.white, { w: 4.5 });
  line([[tx - 15, cy + h / 2], [tx + 15, cy + h / 2]], { w: 7, color: o.fill || C.white });
}

/** 大手机（来电/通话界面），中心 (x,y)，s 大小 */
function bigPhone(x, y, s, fn) {
  at(x, y, s, 0, () => {
    shape(box(-170, -340, 340, 680, 42), '#1d1b1a', { w: 6 });
    shape(box(-152, -318, 304, 636, 30), '#dfe6ea', { stroke: false });
    shape(box(-40, -306, 80, 18, 9), '#1d1b1a', { stroke: false });
    fn && fn();
  });
}

/** 桌子（侧面看的简单木桌） */
function table(x, gy, w, h = 140) {
  shape(box(x - w / 2, gy - h, w, 26, 4), C.wood, { w: 4.5 });
  for (const sx of [-1, 1]) shape(box(x + sx * (w / 2 - 40) - 12, gy - h + 26, 24, h - 26, 3), C.woodD, { w: 4 });
}

/** 尖角的喊叫气泡（实物层，白底黑字）。中心 (x,y)，p 出现 0..1 */
function burst(str, x, y, p, o = {}) {
  if (p <= 0) return;
  const size = o.size || 52, k = E.back(p, 2.4), rr = rng(o.seed || 7);
  ctx.font = fontOf(size, F.serif, 900); const tw = ctx.measureText(str).width + size * 0.4, rx = tw / 2 + 50, ry = size + 36;
  at(x + shakeAt(T_NOW, o.t0 ?? -9, 6), y, k, o.rot || -0.05, () => {
    const pts = []; for (let i = 0; i < 22; i++) { const a = i / 22 * Math.PI * 2, r = i % 2 ? 0.8 : 1.12 + rr() * 0.12; pts.push([Math.cos(a) * rx * r, Math.sin(a) * ry * r]); }
    shape(poly(pts), C.white, { w: 5 });
    txt(str, 0, size * 0.36, { size, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
  });
}

/** 气泡 + 字（实物层） */
function say(str, cx, cy, p, o = {}) {
  if (p <= 0) return;
  const size = o.size || 48; ctx.font = fontOf(size, F.serif, 900);
  const w = ctx.measureText(str).width + size * 1.4, h = size * 2.1;
  layer(seg(p, 0, 0.3), () => at(cx, cy, E.back(p, 1.6), 0, () => {
    speech(0, 0, w, h, { tx: o.tx ?? -w * 0.2, ty: o.ty ?? h / 2 + 40, fill: o.fill });
    txt(str, 0, size * 0.36, { size, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
  }));
}

/** 椅子（正面），座面高 sy */
function chair(x, gy, s = 1) {
  at(x, gy, s, 0, () => {
    shape(box(-80, -330, 160, 200, 14), C.woodD, { w: 4.5 });
    for (const sx of [-1, 1]) shape(box(sx * 68 - 9, -130, 18, 130, 3), C.woodD, { w: 4 });
    shape(box(-96, -150, 192, 30, 6), C.wood, { w: 4.5 });
  });
}

/** 盘式录音机：两盘磁带转着 */
function recorder(x, y, s = 1, t = T_NOW, spin = 1) {
  at(x, y, s, 0, () => {
    shape(box(-130, -90, 260, 150, 10), C.bake, { w: 4.5 });
    shape(box(-112, 16, 224, 32, 4), C.metalD, { w: 3 });
    for (const [cx, k] of [[-58, 1], [58, 1.3]]) {
      shape(circ(cx, -26, 46), C.metalL, { w: 4 });
      for (let i = 0; i < 3; i++) { const a = t * 5 * spin * k + i * Math.PI * 2 / 3; shape(circ(cx + Math.cos(a) * 24, -26 + Math.sin(a) * 24, 9), C.bake, { w: 2.5 }); }
      shape(circ(cx, -26, 7), C.ink, { stroke: false });
    }
    line([[-58, 20], [58, 20]], { w: 3, color: '#2a221c' });
  });
}

/** 报纸（双手举着），中心 (x,y) */
function newspaper(x, y, s = 1, rot = 0) {
  at(x, y, s, rot, () => {
    shape(box(-130, -90, 260, 180, 4), C.paper, { w: 4 });
    txt('晚报', -60, -42, { size: 40, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    for (let i = 0; i < 6; i++) line([[-110, -10 + i * 16], [i % 3 === 2 ? 20 : 110, -10 + i * 16]], { w: 4, color: '#8a7d68' });
    shape(box(30, -70, 80, 54, 2), '#8a7d68', { stroke: false });
  });
}

/** 举牌 */
function placard(str, x, y, s = 1) {
  at(x, y, s, 0, () => {
    line([[0, 40], [0, 150]], { w: 10, color: C.woodD });
    shape(box(-120, -60, 240, 110, 6), C.white, { w: 5 });
    txt(str, 0, 22, { size: 64, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, spacing: 0, shadow: 0 });
  });
}

/** 保健品瓶 */
function bottle(x, y, s = 1) {
  at(x, y, s, 0, () => {
    shape(box(-34, -86, 68, 26, 6), C.ink, { w: 3 });
    shape(box(-46, -62, 92, 130, 18), C.white, { w: 4 });
    shape(box(-40, -30, 80, 56, 4), C.mustard, { w: 3 });
    txt('神效', 0, 10, { size: 26, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
  });
}
