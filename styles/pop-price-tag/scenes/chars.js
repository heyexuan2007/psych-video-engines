// 角色：马克笔小人（粗黑描边 + 错位填色 + 暗面排线）。从 obey-ep1 的剪纸小人改来，全部原创。
// 新加：robe 法袍（黑袍白领）、apron 围裙、bag 手里拎的购物袋
// 局部坐标：脚底 (0,0)，s=1 时身高约 330。返回 { head, handL, handR, top, chest }（当前坐标系，已算 x/y/s/flip）
// 主角：一撮呆毛 + 乱刘海；hair: 0 短发 1 波波头 2 丸子头 3 刺猬头 4 卷发 5 主角 6 长发

function drawFace(o, seed) {
  const { eyes = 'dot', mouth = 'smile', brow = 0, look = [0, 0], blush = 0 } = o;
  const f0 = FOFF; FOFF = 0;
  const lx = look[0] * 7, ly = look[1] * 5, ey = -262, my = -226;
  for (const sx of [-1, 1]) {
    const x = sx * 25 + lx, y = ey + ly;
    if (eyes === 'dot') { shape(oval(x, y, 7.5, 9), C.ink, { w: 2 }); shape(circ(x - 2.4, y - 3, 2.3), C.white, { stroke: false }); }
    else if (eyes === 'wide') { shape(oval(x, y, 15, 17), C.white, { w: 3.5 }); shape(circ(x + look[0] * 5, y + look[1] * 5, 6), C.ink, { stroke: false }); }
    else if (eyes === 'happy') line(qd([x - 11, y + 4], [x, y - 12], [x + 11, y + 4]), { w: 4.5 });
    else if (eyes === 'closed') line(qd([x - 11, y - 2], [x, y + 9], [x + 11, y - 2]), { w: 4.5 });
    else if (eyes === 'squint') line([[x - 11, y], [x + 11, y]], { w: 5 });
    else if (eyes === 'side') { shape(oval(x, y, 13, 9), C.white, { w: 3 }); shape(circ(x + sx * 0 + (look[0] >= 0 ? 6 : -6), y + 1, 5), C.ink, { stroke: false }); }
    if (brow) line([[x + sx * 14, y - 23 - brow * 8], [x - sx * 12, y - 23 + brow * 8]], { w: 4.5 });
    if (blush) shape(oval(sx * 44, ey + 22, 13, 8), rgba(C.red, 0.35 * blush), { stroke: false });
  }
  if (mouth === 'smile') line(qd([-14, my - 3], [0, my + 11], [14, my - 3]), { w: 4.5 });
  else if (mouth === 'grin') { shape(() => { ctx.moveTo(-18, my - 4); ctx.quadraticCurveTo(0, my + 22, 18, my - 4); ctx.closePath(); }, '#5a2a2a', { w: 4 }); }
  else if (mouth === 'frown') line(qd([-13, my + 6], [0, my - 8], [13, my + 6]), { w: 4.5 });
  else if (mouth === 'flat') line([[-12, my], [12, my]], { w: 4.5 });
  else if (mouth === 'open') shape(oval(0, my + 2, 15, 12), '#5a2a2a', { w: 4 });
  else if (mouth === 'o') shape(oval(0, my + 2, 7, 8), '#5a2a2a', { w: 4 });
  else if (mouth === 'wave') line([[-16, my], [-8, my - 5], [0, my + 2], [8, my - 5], [16, my]], { w: 4.5 });
  else if (mouth === 'yawn') shape(oval(0, my + 6, 12, 18), '#5a2a2a', { w: 4 });
  else if (mouth === 'smug') line(qd([-16, my - 2], [6, my + 8], [18, my - 10]), { w: 4.5 });
  FOFF = f0;
}

function drawHair(o, seed) {
  const kind = o.hair ?? 0, col = o.hairCol || C.hair, sh = { shade: [-10, 6] };
  const capPts = (fr) => { const pts = []; for (let i = 0; i <= 16; i++) { const a = Math.PI * (1.06 + 0.88 * i / 16); pts.push([Math.cos(a) * 71, -262 + Math.sin(a) * 69]); } return pts.concat(fr); };
  if (kind === 0 || kind === 2) shape(poly(capPts([[44, -292], [16, -284], [-14, -293], [-44, -284]])), col, sh);
  if (kind === 2) shape(circ(0, -344, 24), col);
  if (kind === 1) shape(poly(capPts([[66, -212], [52, -212], [50, -282], [-50, -282], [-52, -212], [-66, -212]])), col, sh);
  if (kind === 6) shape(poly(capPts([[70, -160], [52, -160], [50, -280], [-50, -280], [-52, -160], [-70, -160]])), col, sh);
  if (kind === 3) shape(poly([[-70, -268], [-66, -318], [-46, -298], [-36, -342], [-14, -310], [0, -350], [16, -310], [38, -342], [48, -298], [68, -318], [70, -268], [40, -288], [0, -294], [-40, -288]]), col, sh);
  if (kind === 4) { shape(poly(capPts([[44, -292], [0, -286], [-44, -292]])), col); for (const [x, y, r] of [[-58, -298, 24], [58, -298, 24], [-26, -326, 26], [24, -328, 26], [-66, -262, 18], [66, -262, 18]]) shape(circ(x, y, r), col); }
  if (kind === 5) {
    if (o.badcut) {   // 剪坏了：短短一截、参差不齐的刘海
      shape(poly(capPts([[50, -312], [36, -298], [24, -316], [10, -300], [-6, -318], [-20, -302], [-34, -314], [-50, -306]])), col, sh);
    } else shape(poly(capPts([[48, -286], [30, -278], [22, -292], [2, -276], [-12, -292], [-30, -278], [-48, -288]])), col, sh);
    line(bz([4, -326], [-8, -366], [34, -380], [28, -346], 12), { w: 6, color: col });
  }
}

/** 主角和所有路人共用的小人 */
function drawKid(x, y, s, o = {}) {
  const { t = T_NOW, flip = 1, armL = 0.25, armR = 0.25, lean = 0, hop = 0, legs = 0, alpha = 1, shirt = C.cream, pants = C.navy, skin = C.skin, sweat = 0, shake = 0, seed = 500 } = o;
  const arm = (sx, a) => [sx * (58 + Math.sin(a) * 92), -186 + Math.cos(a) * 92];
  const hL = arm(-1, armL), hR = arm(1, armR), jx = shake ? Math.sin(t * 61 + seed) * shake : 0;
  const wx = (px, py) => { const c = Math.cos(lean), sn = Math.sin(lean); return [x + jx + (px * c - py * sn) * s * flip, y - hop + (px * sn + py * c) * s]; };
  layer(alpha, () => {
    ctx.save(); ctx.translate(x + jx, y - hop); ctx.scale(flip, 1); ctx.rotate(lean); ctx.scale(s, s);
    // 地上的影子
    shape(oval(0, 2, 70, 12), 'rgba(0,0,0,0.25)', { stroke: false });
    const lp = Math.sin(legs) * 18;
    tube([[-24, -96], [-26 + lp, -16]], 30, pants); tube([[24, -96], [26 - lp, -16]], 30, pants);
    shape(oval(-30 + lp, -8, 23, 11), C.ink, { w: 2 }); shape(oval(30 - lp, -8, 23, 11), C.ink, { w: 2 });
    // 上身 + 衣服上的图案
    if (o.coat) {   // 白大褂：长到膝盖，V 领里露出衬衫和领带
      shape(() => { ctx.moveTo(-60, -214); ctx.lineTo(60, -214); ctx.quadraticCurveTo(78, -210, 80, -170); ctx.lineTo(88, -46); ctx.lineTo(-88, -46); ctx.lineTo(-80, -170); ctx.quadraticCurveTo(-78, -210, -60, -214); ctx.closePath(); }, o.coat, { shade: [-12, 0] });
      shape(poly([[-30, -214], [30, -214], [0, -150]]), o.under || C.cream, { w: 3 });
      if (o.tie) shape(poly([[-7, -208], [7, -208], [10, -170], [0, -152], [-10, -170]]), o.tie, { w: 3 });
      line([[-30, -214], [-8, -150], [0, -46]], { w: 4 }); line([[30, -214], [8, -150]], { w: 4 });
      shape(box(30, -128, 32, 6, 2), C.ink, { stroke: false }); line([[40, -136], [40, -122]], { w: 4, color: '#3a3a3a' });
      shape(circ(-4, -124, 4), C.ink, { stroke: false }); shape(circ(-2, -92, 4), C.ink, { stroke: false });
    } else shape(box(-64, -214, 128, 132, 44), shirt, { shade: [-12, 0] });
    if (o.robe) {   // 法袍：黑袍到脚踝、宽袖、白色领巾
      shape(() => { ctx.moveTo(-62, -214); ctx.lineTo(62, -214); ctx.quadraticCurveTo(84, -208, 88, -160); ctx.lineTo(104, -20); ctx.lineTo(-104, -20); ctx.lineTo(-88, -160); ctx.quadraticCurveTo(-84, -208, -62, -214); ctx.closePath(); }, o.robe, { shade: [-14, 0] });
      shape(box(-30, -214, 60, 72, 10), C.white, { w: 3.5 });
      line([[0, -206], [0, -150]], { w: 3 });
      for (const sx of [-1, 1]) line([[sx * 36, -200], [sx * 30, -24]], { w: 3, color: '#4a4650' });
    }
    if (o.apron) {   // 围裙：带胸兜
      shape(() => { ctx.moveTo(-46, -196); ctx.lineTo(46, -196); ctx.lineTo(56, -58); ctx.lineTo(-56, -58); ctx.closePath(); }, o.apron, { w: 4 });
      shape(box(-30, -150, 60, 34, 6), mixc(o.apron, '#000000', 0.12), { w: 3 });
      for (const sx of [-1, 1]) line([[sx * 40, -196], [sx * 48, -214]], { w: 4 });
    }
    if (o.tie && !o.coat) shape(poly([[-8, -210], [8, -210], [11, -160], [0, -138], [-11, -160]]), o.tie, { w: 3 });
    if (o.print) at(0, -150, 1, 0, () => PRINTS[o.print](t));
    // 头
    for (const sx of [-1, 1]) shape(oval(sx * 70, -256, 11, 14), skin, { w: 4 });
    shape(circ(0, -262, 68), skin, { shade: [-12, 4] });
    drawHair(o, seed);
    drawFace(o, seed);
    if (o.glasses) for (const sx of [-1, 1]) { shape(box(sx * 25 - 19, -276, 38, 28, 6), 'rgba(255,255,255,0.12)', { w: 4 }); line([[-6, -264], [6, -264]], { w: 4 }); }
    if (o.hat) { shape(() => { ctx.ellipse(0, -284, 76, 64, 0, Math.PI, Math.PI * 2); ctx.closePath(); }, o.hat, { shade: [-10, 0] }); shape(box(-80, -298, 160, 30, 12), mixc(o.hat, '#000000', 0.2)); shape(circ(0, -350, 14), C.cream); }
    // 胳膊和手
    for (const [sx, a, h, col] of [[-1, armL, hL, o.robe || o.coat || shirt], [1, armR, hR, o.robe || o.coat || shirt]]) {
      const sh = [sx * 56, -186], mid = [(sh[0] + h[0]) / 2 + sx * Math.cos(a) * 12, (sh[1] + h[1]) / 2 + 6];
      tube(qd(sh, mid, h), 26, col);
      shape(circ(h[0], h[1], 15), skin, { w: 4 });
    }
    if (o.bag) { const [bx, by] = o.bag === 'L' ? hL : hR; line(qd([bx - 22, by + 34], [bx, by - 14], [bx + 22, by + 34]), { w: 4 }); shape(box(bx - 44, by + 30, 88, 96, 8), o.bagCol || C.white, { w: 4 }); }
    if (o.phone) { const [px, py] = hR; shape(box(px - 20, py - 66, 40, 70, 8), C.ink, { w: 3 }); shape(box(px - 14, py - 58, 28, 50, 4), o.phoneOn ? '#cfe6ff' : '#30343c', { stroke: false }); shape(circ(px, py, 15), skin, { w: 4 }); }
    if (sweat > 0) for (let i = 0; i < 2; i++) { const ph = (t * 1.3 + i * 0.5) % 1, a2 = sweat * Math.sin(Math.PI * ph); at(86 + i * 16, -316 + i * 36 + ph * 30, 1, 0, () => shape(poly([[0, -12], [8, 3], [0, 10], [-8, 3]]), '#dff2ff', { w: 3, alpha: a2 })); }
    ctx.restore();
  });
  return { head: wx(0, -262), top: wx(0, -340), chest: wx(0, -150), handL: wx(hL[0], hL[1]), handR: wx(hR[0], hR[1]), eyes: [wx(-25, -262), wx(25, -262)] };
}

/** 衣服上的图案（中心在胸口） */
const PRINTS = {
  /** 过气歌手的大头：爆炸头、墨镜、亮片、爱心。纯虚构 */
  singer(t) {
    for (const [x, y, r] of [[-30, -18, 20], [30, -18, 20], [-16, -38, 22], [16, -38, 22], [-38, 4, 15], [38, 4, 15]]) shape(circ(x, y, r), '#7a4a2a', { w: 3 });
    shape(oval(0, 0, 30, 34), C.skin, { w: 3 });
    shape(box(-28, -10, 25, 15, 6), C.ink, { w: 2 }); shape(box(3, -10, 25, 15, 6), C.ink, { w: 2 }); line([[-3, -4], [3, -4]], { w: 3 });
    shape(() => { ctx.moveTo(-12, 12); ctx.quadraticCurveTo(0, 26, 12, 12); ctx.closePath(); }, '#fff', { w: 3 });
    const tw = 0.6 + 0.4 * Math.sin(t * 9);
    for (const [x, y, k] of [[-46, -46, 1], [44, -40, 0.8], [40, 34, 0.9]]) at(x, y, k * tw, 0, () => shape(poly([[0, -10], [3, -3], [10, 0], [3, 3], [0, 10], [-3, 3], [-10, 0], [-3, -3]]), C.warm, { w: 2 }));
    at(-44, 32, 1, 0, () => shape(() => { ctx.moveTo(0, 6); ctx.bezierCurveTo(-14, -4, -6, -16, 0, -8); ctx.bezierCurveTo(6, -16, 14, -4, 0, 6); }, C.red, { w: 2.5 }));
  },
  /** 体面的那件：一颗大白星 */
  star() {
    const pts = []; for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 17 : 40; pts.push([Math.cos(a) * r, Math.sin(a) * r + 2]); }
    shape(poly(pts), C.white, { w: 3.5 });
  },
};
