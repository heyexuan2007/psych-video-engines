// 道具：全部用 engine.js 的手绘笔画。配色只用墨线 + 红（你下的判断）+ 黄（便利贴）。
function bg() { ctx.save(); ctx.globalAlpha = 1; ctx.drawImage(PAPER, 0, 0); ctx.restore(); }

/** 地面：一条铅笔线 + 几撮短线 */
function ground(y, x0 = 60, x1 = 1680, seed = 40) {
  sk([[x0, y], [x1, y]], { w: 4, color: C.pencil, seed, amp: 3 });
  const n = Math.max(3, Math.round((x1 - x0) / 240));
  for (let i = 0; i < n; i++) { const x = lerp(x0 + 40, x1 - 40, hash(seed + i * 3.3)); sk([[x, y + 14], [x + 34, y + 12]], { w: 3, color: C.gray, seed: seed + i, amp: 1.5, dbl: false }); }
}

/** 桌子：盖住人的下半身 */
function drawTable(x0, x1, yt, yb, alpha = 1) {
  if (alpha <= 0.003) return;
  layer(alpha, () => {
    sk([[x0, yt], [x1, yt], [x1, yb], [x0, yb]], { close: true, fill: C.paperLo, w: 6, seed: 740, off: [0, 0] });
    if (yb - yt > 40) sk([[x0 + 14, yt + 20], [x1 - 14, yt + 20]], { w: 3.5, color: C.pencil, seed: 741, amp: 1.5, dbl: false });
  });
}

/** 便利贴：中心 (x,y)。o: size(字号) rot col(字的颜色) s alpha w h */
function stickyNote(x, y, txt, o = {}) {
  const { size = 38, rot = 0, col = C.ink, s = 1, alpha = 1, seed = 1300 } = o;
  if (alpha <= 0.003 || s <= 0.01) return;
  const n = [...txt].length, w = o.w ?? Math.max(size * 2.2, n * size * 1.04 + size * 0.7), h = o.h ?? size * 2.0;
  layer(alpha, () => at(x, y, s, rot, () => {
    sk(rr(-w / 2 + size * 0.12, -h / 2 + size * 0.17, w, h, 4), { fill: 'rgba(60,45,25,0.2)', stroke: false, seed, amp: 1, off: [0, 0] });
    sk(rr(-w / 2, -h / 2, w, h, 4), { close: true, fill: C.yellow, w: Math.max(2.5, size * 0.075), seed: seed + 1, amp: 1.2, off: [0, 0] });
    sk([[-w / 2 + 5, -h / 2 + h * 0.13], [w / 2 - 5, -h / 2 + h * 0.13]], { w: h * 0.17, color: 'rgba(214,150,20,0.32)', dbl: false, seed: seed + 2, amp: 0.8, cap: 'butt' });
    if (txt) hw(txt, 0, size * 0.44, { size, color: col, font: F.wei, bold: 1.2, seed: seed % 50 });
  }));
}

/** 你的手：胳膊从屏幕外的 (bx,by) 伸到 (x,y)。全片“你”只出现这只手 */
function drawHand(bx, by, x, y, o = {}) {
  const { seed = 1200, s = 1 } = o, dx = x - bx, dy = y - by, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, ang = Math.atan2(dy, dx);
  const wr = [x - ux * 62 * s, y - uy * 62 * s];
  tube([[bx, by], wr], 74 * s, C.pencil, { seed });
  tube([[wr[0] - ux * 26 * s, wr[1] - uy * 26 * s], wr], 82 * s, C.white, { seed: seed + 1 });
  sk(ell(x - ux * 26 * s, y - uy * 26 * s, 40 * s, 33 * s, 18, ang), { close: true, fill: C.paperHi, w: 5 * s, seed: seed + 2, off: [0, 0] });
  sk(ell(x - ux * 34 * s - uy * 34 * s, y - uy * 34 * s + ux * 34 * s, 22 * s, 13 * s, 12, ang + 0.7), { close: true, fill: C.paperHi, w: 4.5 * s, seed: seed + 3, off: [0, 0] });
}

/**
 * 拍便利贴：手从 from 拿着便利贴飞到 to，t0 拍上，再缩回去。
 * 拍上以后的便利贴由调用方自己画（贴在人身上的用 noteExtra，贴在画面上的用 stuck）
 */
function slap(t, t0, from, to, txt, o = {}) {
  const a = t0 - 0.3, b = t0 + 0.5; if (t < a || t > b) return;
  const dx = to[0] - from[0], dy = to[1] - from[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
  const e = t < t0 ? E.in(seg(t, a, t0)) : 1 - E.io(seg(t, t0 + 0.1, b));
  const hx = lerp(from[0], to[0], e), hy = lerp(from[1], to[1], e), hs = o.hs || 1;
  drawHand(from[0] - ux * 600, from[1] - uy * 600, hx - ux * 20 * hs, hy - uy * 20 * hs, { seed: o.hseed || 1200, s: hs });
  if (t < t0) stickyNote(hx, hy, txt, { ...o, rot: (o.rot || 0) + (1 - e) * 0.4, s: lerp(1.5, 1.05, e) });
  if (t >= t0 && t < t0 + 0.3) { const p = seg(t, t0, t0 + 0.3), k = o.bs || 1; burst(to[0], to[1], 70 * k, 135 * k, 9, { color: C.ink, w: 5, seed: 1250, p: E.out(p), alpha: 1 - p }); }
}
/** 已经拍在画面上的便利贴（带一下回弹） */
function stuck(t, t0, x, y, txt, o = {}) {
  if (t < t0) return;
  const k = t - t0; stickyNote(x, y, txt, { ...o, s: (o.s || 1) * (1 + 0.28 * Math.exp(-k * 12) * Math.cos(k * 28)) });
}

// 贴在新同事身上的 5 张（人物局部坐标：脚底 (0,0)，头心 (0,-236)）
const NOTES = [
  { txt: '散漫', x: -58, y: -140, rot: -0.12 },
  { txt: '高冷', x: 58, y: -136, rot: 0.1 },
  { txt: '装样子', x: 4, y: -296, rot: 0.05 },
  { txt: '挑剔', x: -34, y: -236, rot: -0.09 },
  { txt: '果然', x: 34, y: -222, rot: 0.11 },
];
/** 给 drawPerson 的 extra：画出 t 时刻已经贴上的便利贴；FALL 给了就按时间一张张飘落 */
function noteExtra(t, NT, FALL) {
  return () => NOTES.forEach((N, i) => {
    if (t < NT[i]) return;
    const k = t - NT[i]; let x = N.x, y = N.y, rot = N.rot, a = 1; const s = 1 + 0.3 * Math.exp(-k * 12) * Math.cos(k * 28);
    if (FALL && t > FALL[i]) { const f = t - FALL[i], d = i % 2 ? 1 : -1; y += 360 * f * f + 20 * f; x += d * (50 * f + Math.sin(f * 9) * 22); rot += d * f * 1.8 + Math.sin(f * 9) * 0.3; a = 1 - seg(f, 0.6, 0.95); }
    stickyNote(x, y, N.txt, { size: 36, rot, col: C.red, s, alpha: a, seed: 1310 + i * 7 });
  });
}

/** 说话气泡。o: tx（尾巴的横向位置）、dir（尾巴歪向哪边） */
function speech(cx, cy, w, h, p, o = {}) {
  if (p <= 0) return;
  at(cx, cy, 0.6 + 0.4 * E.back(clamp(p)), o.rot || 0, () => {
    const tx = o.tx ?? 0, sd = o.seed || 910;
    sk([[tx - 14, h / 2 - 4], [tx + (o.dir || 0) * 24, h / 2 + 30], [tx + 14, h / 2 - 4]], { fill: C.white, w: 5, seed: sd + 1, off: [0, 0] });
    sk(rr(-w / 2, -h / 2, w, h, Math.min(w, h) * 0.36), { close: true, fill: C.white, w: 5, seed: sd, off: [0, 0] });
    sk([[tx - 10, h / 2 - 1], [tx + 10, h / 2 - 1]], { w: 8, color: C.white, seed: sd + 2, amp: 0, dbl: false });
  });
}
function dots3(x, y, r = 7, gap = 24, col = C.gray) { for (let i = -1; i <= 1; i++) sk(ell(x + i * gap, y, r, r, 8), { fill: col, stroke: false, seed: 1012 + i, off: [0, 0] }); }

/** 手画的大问号 */
function drawQ(cx, cy, s, p, o = {}) {
  const pts = bz([-46, -70], [-50, -150], [60, -150], [50, -66], 14).concat(bz([50, -66], [44, -30], [0, -34], [0, 14], 10));
  at(cx, cy, s, o.rot || 0, () => { sk(pts, { color: o.color || C.red, w: 18, p: seg(p, 0, 0.8), seed: o.seed || 110, amp: 2 }); if (p > 0.82) sk(ell(0, 58, 13, 13, 12), { fill: o.color || C.red, color: o.color || C.red, close: true, w: 4, seed: 111, off: [0, 0] }); });
}

/** 窗户：中心 (cx,cy)。nt=0 白天（太阳），nt=1 夜里（月亮和星星） */
function drawWindow(cx, cy, w, h, nt = 0, seed = 1500) {
  const x0 = cx - w / 2, y0 = cy - h / 2;
  sk(rr(x0, y0, w, h, 6), { close: true, fill: mixc(C.paperHi, C.ink, nt * 0.82), w: 6, seed, off: [0, 0] });
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.clip();
  if (nt < 1) sk(ell(cx + w * 0.2, cy - h * 0.12 + nt * h * 0.9, w * 0.14, w * 0.14, 18), { close: true, fill: C.yellow, w: 4, seed: seed + 1, off: [0, 0], alpha: 1 - nt });
  if (nt > 0) {
    const my = cy - h * 0.1 + (1 - nt) * h * 0.8, r = w * 0.15;
    sk(ell(cx - w * 0.16, my, r, r, 18), { close: true, fill: C.yellow, color: C.yellow, w: 3, seed: seed + 2, off: [0, 0], alpha: nt });
    sk(ell(cx - w * 0.16 + r * 0.5, my - r * 0.25, r * 0.88, r * 0.88, 18), { fill: mixc(C.paperHi, C.ink, nt * 0.82), stroke: false, seed: seed + 3, off: [0, 0], alpha: nt });
    for (const [u, v] of [[0.26, -0.3], [0.34, 0.1], [0.08, 0.26], [-0.34, 0.3]]) sk(ell(cx + w * u, cy + h * v, 4, 4, 6), { fill: C.yellow, stroke: false, seed: seed + 4, off: [0, 0], alpha: nt });
  }
  ctx.restore();
  sk([[cx, y0], [cx, y0 + h]], { w: 4.5, seed: seed + 5, amp: 1 }); sk([[x0, cy], [x0 + w, cy]], { w: 4.5, seed: seed + 6, amp: 1 });
  sk([[x0 - 14, y0 + h + 6], [x0 + w + 14, y0 + h + 6]], { w: 7, seed: seed + 7, amp: 1.2 });
}

/** 台灯：底座在 (x,y)，灯头朝左。on>0 时有一片黄光 */
function drawLamp(x, y, s, on = 0, seed = 1520) {
  at(x, y, s, 0, () => {
    if (on > 0) sk([[-70, -122], [-290, 0], [40, 0], [-6, -122]], { close: true, fill: rgba(C.yellow, 0.42 * on), stroke: false, seed: seed + 5, off: [0, 0] });
    sk(ell(0, -5, 34, 9, 12), { close: true, fill: C.ink, w: 3, seed, off: [0, 0], dbl: false });
    sk([[0, -8], [14, -74], [-22, -128]], { w: 6, seed: seed + 1, amp: 1 });
    sk([[-78, -112], [-52, -152], [2, -150], [0, -112]], { close: true, fill: on > 0.5 ? C.yellow : C.white, w: 5, seed: seed + 2, off: [0, 0] });
  });
}

/** 桌上的笔记本电脑（看到的是屏幕背面）。(x,y) 是底边中点 */
function drawLaptop(x, y, s = 1, seed = 1530) {
  at(x, y, s, 0, () => {
    sk([[-88, 0], [-70, -122], [98, -122], [84, 0]], { close: true, fill: C.paperHi, w: 5, seed, off: [0, 0] });
    sk(ell(8, -62, 13, 13, 12), { close: true, color: C.pencil, w: 3.5, seed: seed + 1, dbl: false });
    sk([[-104, 2], [104, 2]], { w: 8, seed: seed + 2, amp: 1 });
  });
}

/** 白板：中心 (cx,cy)。几根柱子，hl 是他圈出来的那一处 */
function drawBoard(cx, cy, w, h, gy, hl = 0, seed = 1540) {
  const x0 = cx - w / 2, y0 = cy - h / 2, u = w / 640;
  for (const sx of [-1, 1]) sk([[cx + sx * w * 0.36, y0 + h], [cx + sx * w * 0.42, gy]], { w: 6 * u + 1, seed: seed + 9 + sx, color: C.pencil });
  sk(rr(x0 + 8, y0 + 10, w, h, 8), { fill: 'rgba(60,45,25,0.15)', stroke: false, seed, off: [0, 0] });
  sk(rr(x0, y0, w, h, 8), { close: true, fill: C.white, w: 5 * u + 1.5, seed: seed + 1, off: [0, 0] });
  sk([[x0 + 60 * u, y0 + 60 * u], [x0 + 330 * u, y0 + 56 * u]], { w: 12 * u, seed: seed + 2, amp: 1.2, dbl: false });
  const by = y0 + h - 60 * u;
  sk([[x0 + 60 * u, by], [x0 + w - 50 * u, by]], { w: 4 * u + 1, seed: seed + 3, color: C.pencil });
  [90, 150, 210, 96].forEach((bh, i) => { const x = x0 + (120 + i * 125) * u; sk([[x, by], [x, by - bh * u]], { w: 62 * u, color: i === 3 ? C.redL : C.paperLo, seed: seed + 4 + i, amp: 1.2, dbl: false, cap: 'butt' }); sk([[x - 31 * u, by], [x - 31 * u, by - bh * u], [x + 31 * u, by - bh * u], [x + 31 * u, by]], { w: 3 * u + 1, seed: seed + 14 + i, amp: 1, dbl: false }); });
  if (hl > 0) sk(ell(x0 + 495 * u, by - 70 * u, 80 * u, 100 * u, 30, 0, -2, 4.9), { color: C.red, w: 6 * u + 2, p: hl, seed: seed + 20, amp: 3 });
}

/** 显示器：(x,y) 是底座。ok=false 坏了（叉叉眼 + 冒烟），ok=true 修好了（笑脸） */
function drawMonitor(x, y, s, ok, t = 0, seed = 1560) {
  at(x, y, s, 0, () => {
    sk([[0, 0], [0, -34]], { w: 10, seed, amp: 0.8 }); sk([[-44, 0], [44, 0]], { w: 9, seed: seed + 1, amp: 0.8 });
    sk(rr(-104, -176, 208, 144, 10), { close: true, fill: ok ? C.yellow : C.paperLo, w: 6, seed: seed + 2, off: [0, 0] });
    for (const sx of [-1, 1]) {
      if (ok) sk(qd([sx * 40 - 14, -112], [sx * 40, -128], [sx * 40 + 14, -112]), { w: 6, seed: seed + 3 + sx, amp: 0.8 });
      else { sk([[sx * 40 - 12, -124], [sx * 40 + 12, -100]], { w: 6, seed: seed + 3 + sx, amp: 0.8 }); sk([[sx * 40 + 12, -124], [sx * 40 - 12, -100]], { w: 6, seed: seed + 5 + sx, amp: 0.8 }); }
    }
    if (ok) sk(qd([-26, -84], [0, -60], [26, -84]), { w: 6, seed: seed + 8, amp: 0.8 });
    else { sk([[-24, -72], [-12, -80], [0, -72], [12, -80], [24, -72]], { w: 6, seed: seed + 8, amp: 0.8 }); for (let i = 0; i < 2; i++) { const x0 = -30 + i * 60, ph = BOIL * 0.9 + i; sk([[x0, -186], [x0 + 9 * Math.sin(ph), -206], [x0 - 9 * Math.sin(ph), -226], [x0, -246]], { w: 5, color: C.gray, seed: seed + 10 + i, amp: 1, dbl: false }); } }
  });
}

/** 你举起来的手机（正面朝你）。(cx,cy) 是手机中心 */
function drawPhoneHand(cx, cy, t) {
  tube([[cx - 60, cy + 640], [cx - 8, cy + 300]], 150, C.pencil, { seed: 1580 });
  tube([[cx - 12, cy + 330], [cx - 6, cy + 286]], 162, C.white, { seed: 1581 });
  sk(ell(cx, cy + 226, 128, 84, 20), { close: true, fill: C.paperHi, w: 5, seed: 1582, off: [0, 0] });
  at(cx, cy, 1, -0.06, () => {
    const w = 270, h = 470;
    sk(rr(-w / 2, -h / 2, w, h, 30), { close: true, fill: C.ink, w: 6, seed: 1583, off: [0, 0] });
    const sw = w - 30, sh = h - 76;
    sk(rr(-sw / 2, -sh / 2, sw, sh, 8), { fill: C.white, stroke: false, seed: 1584, amp: 0.6, off: [0, 0] });
    ctx.save(); ctx.beginPath(); ctx.rect(-sw / 2, -sh / 2, sw, sh); ctx.clip();
    const pitch = 150, sc = (t * 170) % pitch;
    for (let i = -1; i < 4; i++) {
      const y = -sh / 2 + i * pitch + sc;
      sk(rr(-sw / 2 + 14, y + 12, sw - 28, 86, 8), { close: true, fill: C.paperLo, color: C.pencil, w: 3.5, seed: 1585, off: [0, 0] });
      sk([[-sw / 2 + 16, y + 116], [sw / 2 - 80, y + 116]], { w: 9, color: C.gray, seed: 1586, amp: 1, dbl: false });
      sk(ell(sw / 2 - 36, y + 116, 12, 10, 10), { close: true, fill: C.red, color: C.red, w: 3, seed: 1587, off: [0, 0] });
    }
    ctx.restore();
    // 拇指和另外几根手指
    sk(ell(w / 2 - 14, 70, 30, 62, 14, -0.25), { close: true, fill: C.paperHi, w: 5, seed: 1588, off: [0, 0] });
    for (let i = 0; i < 3; i++) sk(ell(-w / 2 - 2, 30 + i * 62, 26, 24, 12), { close: true, fill: C.paperHi, w: 5, seed: 1589 + i, off: [0, 0] });
  });
}

/** 医院：x 是左墙，gy 是地面 */
function drawHospital(x, gy, seed = 1700) {
  const w = 384, h = 500, y0 = gy - h;
  sk([[x, gy], [x, y0], [x + w, y0], [x + w, gy]], { fill: C.white, w: 6, seed, off: [0, 0] });
  sk(rr(x + 112, gy - 250, 164, 250, 6), { close: true, fill: '#4a4038', fa: 0.85, w: 5, seed: seed + 1, off: [0, 0] });
  sk([[x + 194, gy - 246], [x + 194, gy - 4]], { w: 4, color: C.paperHi, seed: seed + 2, dbl: false });
  for (const sx of [34, 300]) sk(rr(x + sx, gy - 220, 54, 76, 4), { close: true, fill: C.paperHi, w: 4, seed: seed + 3 + sx, off: [0, 0] });
  sk(rr(x + 34, y0 + 46, 316, 136, 10), { close: true, fill: C.paperHi, w: 5, seed: seed + 4, off: [0, 0] });
  for (const [a, b] of [[[x + 62, y0 + 114], [x + 138, y0 + 114]], [[x + 100, y0 + 76], [x + 100, y0 + 152]]]) sk([a, b], { w: 28, color: C.red, seed: seed + 5, amp: 1, dbl: false, cap: 'butt' });
  hw('医院', x + 244, y0 + 142, { size: 84, font: F.wei, bold: 1.2, seed: 62 });
}

/** 对照表中间的小图标（线稿）：0 不说话 1 加班 2 提意见 3 迟到 */
function drawIcon(k, x, y, lit = 0) {
  sk(ell(x, y, 38, 38, 22), { close: true, fill: mixc(C.white, C.yellow, lit), w: 4.5, seed: 1740 + k, off: [0, 0] });
  if (k === 0) dots3(x, y, 5, 16, C.ink);
  else if (k === 1) { sk(ell(x - 2, y, 19, 19, 16, 0, 0.9, 5.3), { w: 4.5, seed: 1751, amp: 0.8 }); sk(qd([x + 10, y - 15], [x - 6, y], [x + 10, y + 15], 8), { w: 4.5, seed: 1752, amp: 0.8 }); }
  else if (k === 2) { sk([[x - 2, y - 22], [x - 2, y + 6]], { w: 7, seed: 1753, amp: 0.6 }); sk(ell(x - 2, y + 19, 4.5, 4.5, 8), { fill: C.ink, stroke: false, seed: 1754, off: [0, 0] }); }
  else { sk(ell(x, y, 22, 22, 16), { close: true, w: 4, seed: 1755, amp: 0.8, dbl: false }); sk([[x, y - 13], [x, y], [x + 10, y + 5]], { w: 4, seed: 1756, amp: 0.5, dbl: false }); }
}
