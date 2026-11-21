// 角色：新同事（圆眼镜 + 黄工牌）、同事、邻居奶奶。全部原创。
// 局部坐标：脚底 (0,0)，头顶约 -300。s=1 时身高约 300 像素。
// 返回 { handL, handR, head, top }（画布坐标，已算上 x/y/s/flip；不含外层 camera）

function drawFace(o, ex, ey, mx, my, seed) {
  const { eyes = 'dot', mouth = 'smile', brow = 0, look = [0, 0], blush = 0 } = o;
  const lx = look[0] * 6, ly = look[1] * 4;
  for (const sx of [-1, 1]) {
    const x = sx * ex + lx, y = ey + ly;
    if (eyes === 'dot') { sk(ell(x, y, 7, 8, 12), { fill: C.ink, w: 3, close: true, seed: seed + sx, amp: 0.8, dbl: false, off: [0, 0] }); sk(ell(x - 2.2, y - 2.6, 2, 2, 8), { fill: C.white, stroke: false, seed, amp: 0.3, off: [0, 0] }); }
    else if (eyes === 'wide') { sk(ell(x, y, 14, 16, 16), { fill: C.white, w: 3.5, close: true, seed: seed + sx, amp: 1, off: [0, 0] }); sk(ell(x + look[0] * 5, y + look[1] * 5, 5, 5.5, 10), { fill: C.ink, w: 2, close: true, seed: seed + 3, amp: 0.5, dbl: false, off: [0, 0] }); }
    else if (eyes === 'happy') sk(qd([x - 11, y + 4], [x, y - 12], [x + 11, y + 4]), { w: 4.5, seed: seed + sx, amp: 1 });
    else if (eyes === 'closed') sk(qd([x - 11, y - 2], [x, y + 9], [x + 11, y - 2]), { w: 4.5, seed: seed + sx, amp: 1 });
    else if (eyes === 'squint') sk([[x - 11, y], [x + 11, y]], { w: 5, seed: seed + sx, amp: 1 });
    else if (eyes === 'x') sk([[x - sx * 10, y - 8], [x + sx * 6, y], [x - sx * 10, y + 8]], { w: 4.5, seed: seed + sx, amp: 1 });
    if (brow) sk([[x + sx * 14, y - 22 - brow * 8], [x - sx * 12, y - 22 + brow * 8]], { w: 4.5, seed: seed + 7 + sx, amp: 1 });
    if (blush) sk(ell(sx * (ex + 18), ey + 22, 13, 8, 12), { fill: rgba(C.red, 0.3 * blush), stroke: false, seed: seed + 9, amp: 1, off: [0, 0] });
  }
  if (mouth === 'smile') sk(qd([mx - 14, my - 3], [mx, my + 11], [mx + 14, my - 3]), { w: 4.5, seed: seed + 11, amp: 1 });
  else if (mouth === 'frown') sk(qd([mx - 13, my + 6], [mx, my - 8], [mx + 13, my + 6]), { w: 4.5, seed: seed + 11, amp: 1 });
  else if (mouth === 'flat') sk([[mx - 12, my], [mx + 12, my]], { w: 4.5, seed: seed + 11, amp: 1.2 });
  else if (mouth === 'open') { sk(ell(mx, my + 2, 15, 12, 14), { fill: '#5a2a2a', w: 4, close: true, seed: seed + 11, amp: 1, off: [0, 0] }); sk(ell(mx, my + 8, 8, 4, 10), { fill: C.redL, stroke: false, seed: seed + 12, amp: 0.5, off: [0, 0] }); }
  else if (mouth === 'o') sk(ell(mx, my + 2, 7, 8, 12), { fill: '#5a2a2a', w: 4, close: true, seed: seed + 11, amp: 0.8, off: [0, 0] });
  else if (mouth === 'wave') sk([[mx - 16, my], [mx - 8, my - 5], [mx, my + 2], [mx + 8, my - 5], [mx + 16, my]], { w: 4.5, seed: seed + 11, amp: 1 });
}

/** 发型：0 短发 1 波波头 2 丸子头 3 刺猬头 4 光头三根毛 5 卷发 6 受试者（薄刘海 + 呆毛） */
function drawHair(kind, col, seed) {
  const cap = (a0, a1, fr) => ell(0, -236, 69, 67, 14, 0, Math.PI * a0, Math.PI * a1).concat(fr);
  const f = { close: true, fill: col, color: C.ink, w: 4, seed, amp: 1.4, off: [0, 0] };
  if (kind === 0 || kind === 2 || kind === 5) sk(cap(1.08, 1.92, [[42, -266], [14, -260], [-16, -269], [-44, -260]]), f);
  if (kind === 2) sk(ell(0, -316, 25, 22, 14), { ...f, seed: seed + 1 });
  if (kind === 5) for (const [x, y, r] of [[-56, -274, 23], [56, -274, 23], [-22, -298, 24], [24, -298, 24]]) sk(ell(x, y, r, r, 12), { ...f, seed: seed + 2 + x });
  if (kind === 1) sk(ell(0, -236, 74, 72, 22, 0, Math.PI * 0.86, Math.PI * 2.14).concat([[54, -206], [52, -262], [-52, -262], [-54, -206]]), f);
  if (kind === 3) sk([[-67, -244], [-64, -292], [-46, -272], [-36, -314], [-15, -284], [0, -322], [16, -284], [37, -314], [47, -272], [65, -292], [67, -244], [40, -262], [0, -268], [-40, -262]], f);
  if (kind === 4) for (const [x, r] of [[-14, -0.25], [0, 0], [14, 0.25]]) sk([[x, -298], [x + r * 40, -322]], { w: 4.5, seed: seed + x, amp: 1, color: C.ink });
  if (kind === 6) { sk(cap(1.2, 1.8, [[30, -280], [0, -274], [-30, -282]]), f); sk(bz([2, -298], [-10, -334], [30, -348], [24, -318], 10), { w: 5.5, seed: seed + 5, amp: 1, color: C.ink }); }
}

function drawPerson(x, y, s, o = {}) {
  const { t = 0, flip = 1, armL = 0.3, armR = 0.3, lean = 0, hop = 0, legs = 0, alpha = 1, hair = 0, hairCol = C.ink, shirt = C.white, sweat = 0, seed = 500, shake = 0, phones = 0, hat = 0, glasses = 0, badge = 0, extra = null } = o;
  const hx = (sx, a) => [sx * (50 + Math.sin(a) * 80), -150 + Math.cos(a) * 80];
  const hL = hx(-1, armL), hR = hx(1, armR), jx = shake ? Math.sin(t * 61 + seed) * shake : 0;
  const wx = (px, py) => { const c = Math.cos(lean), sn = Math.sin(lean); return [x + jx + (px * c - py * sn) * s * flip, y - hop + (px * sn + py * c) * s]; };
  layer(alpha, () => {
    ctx.save(); ctx.translate(x + jx, y - hop); ctx.scale(flip, 1); ctx.rotate(lean); ctx.scale(s, s);
    const lp = Math.sin(legs) * 16;
    // 腿和鞋
    tube([[-22, -70], [-24 + lp, -10]], 28, C.pencil, { seed: seed + 1 }); tube([[22, -70], [24 - lp, -10]], 28, C.pencil, { seed: seed + 2 });
    sk(ell(-28 + lp, -5, 21, 10, 12), { fill: C.ink, w: 3, close: true, seed: seed + 3, amp: 1, dbl: false, off: [0, 0] });
    sk(ell(28 - lp, -5, 21, 10, 12), { fill: C.ink, w: 3, close: true, seed: seed + 4, amp: 1, dbl: false, off: [0, 0] });
    // 上身
    sk(rr(-58, -188, 116, 132, 44), { close: true, fill: shirt, seed: seed + 5, w: 5 });
    if (badge) {   // 工牌
      sk([[-20, -182], [0, -128], [20, -182]], { w: 3.5, color: C.red, seed: seed + 70, amp: 0.8, dbl: false });
      sk(rr(-15, -130, 30, 38, 4), { close: true, fill: C.yellow, w: 3.5, seed: seed + 71, amp: 0.6, off: [0, 0] });
      sk([[-7, -108], [7, -108]], { w: 3, seed: seed + 72, amp: 0.4, dbl: false });
    }
    // 头、耳朵、头发、脸
    for (const sx of [-1, 1]) sk(ell(sx * 66, -230, 10, 13, 10), { close: true, fill: C.paperHi, seed: seed + 6 + sx, w: 4, amp: 0.8, off: [0, 0] });
    sk(ell(0, -236, 66, 64), { close: true, fill: C.paperHi, seed: seed + 8, w: 5 });
    drawHair(hair, hairCol, seed + 10);
    drawFace(o, 25, -238, 0, -204, seed + 50);
    if (glasses) {
      for (const sx of [-1, 1]) { sk(ell(sx * 26, -238, 22, 22, 18), { close: true, w: 4, seed: seed + 74 + sx, amp: 0.8, dbl: false }); sk([[sx * 48, -240], [sx * 63, -246]], { w: 3.5, seed: seed + 77 + sx, amp: 0.5, dbl: false }); }
      sk(qd([-5, -240], [0, -245], [5, -240], 4), { w: 4, seed: seed + 79, amp: 0.4, dbl: false });
    }
    if (hat) { sk(ell(0, -322, 60, 34, 20), { close: true, fill: C.white, seed: seed + 20, w: 5, off: [0, 0] }); sk(rr(-44, -312, 88, 34, 6), { close: true, fill: C.white, seed: seed + 21, w: 5, off: [0, 0] }); }
    if (phones > 0) layer(phones, () => {
      sk(ell(0, -236, 78, 80, 16, 0, Math.PI * 1.06, Math.PI * 1.94), { w: 10, seed: seed + 24, amp: 1 });
      for (const sx of [-1, 1]) sk(rr(sx * 76 - 13, -262, 26, 56, 10), { close: true, fill: C.red, seed: seed + 25 + sx, w: 4.5, off: [0, 0] });
    });
    // 胳膊和手
    for (const [sx, a, h, sd] of [[-1, armL, hL, 30], [1, armR, hR, 32]]) {
      const sh = [sx * 50, -150], mid = [(sh[0] + h[0]) / 2 + sx * Math.cos(a) * 10, (sh[1] + h[1]) / 2 + 6];
      tube(qd(sh, mid, h), 24, shirt, { seed: seed + sd });
      sk(ell(h[0], h[1], 14, 14, 12), { close: true, fill: C.paperHi, seed: seed + sd + 1, w: 4.5, off: [0, 0] });
    }
    // 汗
    if (sweat > 0) for (let i = 0; i < 2; i++) { const ph = (t * 1.3 + i * 0.5) % 1, a2 = sweat * Math.sin(Math.PI * ph); at(82 + i * 14, -284 + i * 34 + ph * 30, 1, 0, () => sk([[0, -12], [8, 3], [0, 10], [-8, 3]], { close: true, fill: C.white, w: 3.5, seed: seed + 60 + i, amp: 0.6, alpha: a2, off: [0, 0] })); }
    if (extra) extra();   // 贴在身上的东西（局部坐标），跟着人一起动
    ctx.restore();
  });
  return { handL: wx(hL[0], hL[1]), handR: wx(hR[0], hR[1]), head: wx(0, -236), top: wx(0, -310), pt: wx };
}
