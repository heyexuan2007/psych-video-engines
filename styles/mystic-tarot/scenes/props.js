// 两种画风共用的道具：信封、性格卡、打勾、分数牌、学生。颜色由画风传进来（o.pal）。
// 全部原创形状。

/** 信封。中心 (x,y)，s=1 时 620×400。o: open 0..1 封舌翻开，pal {paper, edge, ink, seal, sealInk}, seal 印章字, glow */
function envelope(x, y, s, o = {}) {
  const P = o.pal, w = 620, h = 400, open = o.open ?? 0;
  at(x, y, s, o.rot || 0, () => {
    // 背面
    shape(box(-w / 2, -h / 2, w, h, 10), P.paperD, { w: 5, color: P.ink });
    // 翻开的封舌（在后面，往上翻）
    if (open > 0.5) { const k = (open - 0.5) * 2; shape(poly([[-w / 2, -h / 2], [w / 2, -h / 2], [0, -h / 2 - h * 0.55 * k]]), P.paperD, { w: 5, color: P.ink }); }
    // 里面露出的卡
    if (o.inner) o.inner();
    // 前面两侧和底部三角
    shape(poly([[-w / 2, -h / 2], [0, h * 0.06], [-w / 2, h / 2]]), P.paper, { w: 5, color: P.ink, shade: [8, 0] });
    shape(poly([[w / 2, -h / 2], [0, h * 0.06], [w / 2, h / 2]]), P.paper, { w: 5, color: P.ink, shade: [-8, 0] });
    shape(poly([[-w / 2, h / 2], [0, -h * 0.02], [w / 2, h / 2]]), P.paper, { w: 5, color: P.ink });
    // 航空信封那种斜条纹边
    if (o.stripes) {
      ctx.save(); ctx.beginPath(); ctx.rect(-w / 2, -h / 2, w, h); ctx.rect(-w / 2 + 22, -h / 2 + 22, w - 44, h - 44); ctx.clip('evenodd');
      for (let k = -40; k < 40; k++) { const x0 = k * 36; ctx.fillStyle = k % 2 ? o.stripes[0] : o.stripes[1]; ctx.beginPath(); ctx.moveTo(x0, -h); ctx.lineTo(x0 + 18, -h); ctx.lineTo(x0 + 18 - h * 2, h); ctx.lineTo(x0 - h * 2, h); ctx.closePath(); ctx.globalAlpha = LA; ctx.fill(); }
      ctx.restore();
      shape(box(-w / 2, -h / 2, w, h, 10), null, { w: 5, color: P.ink });
    }
    // 合着的封舌（往下）
    if (open <= 0.5) {
      const k = 1 - open * 2;
      shape(poly([[-w / 2, -h / 2], [w / 2, -h / 2], [0, -h / 2 + h * 0.62 * k]]), P.paper, { w: 5, color: P.ink, shade: [0, -8] });
      if (k > 0.6 && o.seal) waxSeal(0, -h / 2 + h * 0.62 * k - 6, o.sealS || 1, o.seal, P);
    }
  });
}
/** 火漆印：波浪边的圆，中间一个字 */
function waxSeal(x, y, s, ch, P) {
  at(x, y, s, 0, () => {
    const pts = []; for (let i = 0; i < 28; i++) { const a = i / 28 * Math.PI * 2, r = 74 + (i % 2 ? 6 : -4) + Math.sin(i * 2.3) * 3; pts.push([Math.cos(a) * r, Math.sin(a) * r]); }
    shape(poly(pts), P.seal, { w: 4, color: P.ink, shade: [6, 7] });
    shape(circ(0, 0, 52), P.sealD, { stroke: false, alpha: 0.55 });
    shape(circ(0, 0, 52), null, { w: 3, color: P.sealInk, alpha: 0.8 });
    txt(ch, 0, 26, { size: 76, font: F.serif, weight: 900, color: P.sealInk, t: 99, t0: 0, cps: 0, shadow: 0 });
  });
}

/** 打勾：一笔画出来，p 0..1 */
function tick(x, y, s, p, col, w = 13) {
  if (p <= 0) return;
  const pts = [[-34, 2], [-10, 30], [44, -46]], L1 = Math.hypot(24, 28), L2 = Math.hypot(54, 76), L = (L1 + L2) * clamp(p);
  at(x, y, s, 0, () => {
    const out = [pts[0]];
    if (L <= L1) out.push([lerp(pts[0][0], pts[1][0], L / L1), lerp(pts[0][1], pts[1][1], L / L1)]);
    else { out.push(pts[1]); const q = (L - L1) / L2; out.push([lerp(pts[1][0], pts[2][0], q), lerp(pts[1][1], pts[2][1], q)]); }
    line(out, { w, color: col });
  });
}

/** 性格卡：方框 + 一句话。左上角 (x,y)。o: w,h, pal, tick 0..1, rot, deco('ticket'|'tarot') */
function traitCard(x, y, str, o = {}) {
  const P = o.pal, w = o.w || 1100, h = o.h || 170;
  at(x, y, 1, o.rot || 0, () => {
    if (o.deco === 'ticket') {
      // 票根：两端半圆缺口 + 虚线撕口
      shape(() => { ctx.moveTo(0, 0); ctx.lineTo(w, 0); ctx.lineTo(w, h / 2 - 24); ctx.arc(w, h / 2, 24, -Math.PI / 2, Math.PI / 2, true); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.lineTo(0, h / 2 + 24); ctx.arc(0, h / 2, 24, Math.PI / 2, -Math.PI / 2, true); ctx.closePath(); }, P.card, { w: 5, color: P.ink, shade: [0, 0] });
      line([[170, 14], [170, h - 14]], { w: 4, color: P.ink, dash: [10, 12], alpha: 0.7 });
      // 左边小票根上的星
      star(85, h / 2, 34, P.accent, P.ink);
    } else {
      shape(box(0, 0, w, h, 14), P.card, { w: 3, color: P.edge });
      shape(box(12, 12, w - 24, h - 24, 8), null, { w: 2, color: P.edge, alpha: 0.7 });
      for (const [cx, cy] of [[30, 30], [w - 30, 30], [30, h - 30], [w - 30, h - 30]]) star(cx, cy, 9, P.edge, null);
    }
    const bx = o.deco === 'ticket' ? 215 : 60;
    shape(box(bx, h / 2 - 38, 76, 76, 6), P.box, { w: 5, color: P.ink });
    txt(str, bx + 112, h / 2 + 22, { size: o.size || 60, font: o.font || F.serif, weight: 900, color: P.text, align: 'left', t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0.02 });
    tick(bx + 42, h / 2 - 2, 1.05, o.tick ?? 0, P.tick, 14);
  });
}

/** 五角星 */
function star(x, y, r, fill, stroke) {
  const pts = []; for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
  shape(poly(pts), fill, stroke ? { w: 3, color: stroke } : { stroke: false });
}

/** 学生（剪影式半身，从下往上）：底边中点 (x,y)。o: col, skin, hair, arm 0..1 举牌, num 牌上数字, pal, seed, face */
function student(x, y, s, o = {}) {
  const P = o.pal, r = rng(o.seed || 1), hairK = Math.floor(r() * 4), tilt = (r() - 0.5) * 0.12;
  at(x, y, s, tilt, () => {
    const arm = o.arm ?? 0;
    // 举牌的胳膊和牌（在身后先画）
    if (arm > 0) {
      const hx = 70, hy = lerp(-120, -330, E.back(arm));
      tube([[52, -150], [hx, hy]], 22, o.col, {});
      at(hx, hy - 70, 1, (r() - 0.5) * 0.25, () => {
        line([[0, 70], [0, 30]], { w: 10, color: P.stick });
        shape(circ(0, 0, 58), P.paddle, { w: 5, color: P.ink });
        txt(String(o.num), 0, 26, { size: 76, font: F.serif, weight: 900, color: P.paddleInk, t: 99, t0: 0, cps: 0, shadow: 0 });
      });
    }
    shape(() => { ctx.moveTo(-95, 0); ctx.quadraticCurveTo(-92, -150, 0, -160); ctx.quadraticCurveTo(92, -150, 95, 0); ctx.closePath(); }, o.col, { w: 5, color: P.ink, shade: [10, 0] });
    shape(box(-20, -185, 40, 34, 8), o.skin, { w: 4, color: P.ink });
    shape(oval(0, -238, 58, 64), o.skin, { w: 5, color: P.ink });
    const hc = o.hair || P.hair;
    if (hairK === 0) shape(() => { ctx.ellipse(0, -258, 62, 50, 0, Math.PI, 0); ctx.lineTo(50, -250); ctx.quadraticCurveTo(0, -282, -50, -250); ctx.closePath(); }, hc, { w: 5, color: P.ink });
    if (hairK === 1) shape(() => { ctx.ellipse(0, -255, 64, 54, 0, Math.PI, 0); ctx.lineTo(64, -190); ctx.lineTo(50, -190); ctx.lineTo(48, -262); ctx.lineTo(-48, -262); ctx.lineTo(-50, -190); ctx.lineTo(-64, -190); ctx.closePath(); }, hc, { w: 5, color: P.ink });
    if (hairK === 2) { shape(() => ctx.ellipse(0, -262, 62, 46, 0, Math.PI, 0), hc, { w: 5, color: P.ink }); shape(circ(0, -318, 20), hc, { w: 4, color: P.ink }); }
    if (hairK === 3) shape(poly([[-62, -246], [-58, -290], [-36, -278], [-22, -312], [0, -286], [20, -314], [34, -280], [58, -292], [62, -246], [30, -270], [-30, -270]]), hc, { w: 5, color: P.ink });
    if (o.face !== false) {
      const look = o.look ?? 0;
      for (const sx of [-1, 1]) shape(oval(sx * 20 + look * 6, -236, 6.5, 8), P.ink, { stroke: false });
      line(o.smile ? qd([-12, -208], [0, -198], [12, -208]) : [[-9, -205], [9, -205]], { w: 4, color: P.ink });
    }
  });
}

/** 老师：站立全身，脚底 (x,y) */
function teacher(x, y, s, o = {}) {
  const P = o.pal;
  at(x, y, s, 0, () => {
    tube([[-24, -170], [-26, 0]], 26, P.trouser); tube([[24, -170], [28, 0]], 26, P.trouser);
    shape(() => { ctx.moveTo(-70, -150); ctx.lineTo(-60, -380); ctx.quadraticCurveTo(0, -410, 60, -380); ctx.lineTo(70, -150); ctx.closePath(); }, P.coat, { w: 5, color: P.ink, shade: [10, 0] });
    line([[0, -395], [0, -170]], { w: 4, color: P.ink });
    shape(poly([[-14, -398], [14, -398], [6, -340], [-6, -340]]), P.tie, { w: 3, color: P.ink });
    tube([[60, -370], [120, -280], [150, -300]], 22, P.coat); // 手里拿着一叠纸
    if (o.papers) o.papers(150, -330);
    tube([[-60, -370], [-80, -260], [-74, -170]], 22, P.coat);
    shape(oval(0, -455, 54, 60), P.skin, { w: 5, color: P.ink });
    shape(() => { ctx.ellipse(0, -478, 58, 42, 0, Math.PI, 0); ctx.closePath(); }, P.hairT, { w: 5, color: P.ink });
    // 圆眼镜
    for (const sx of [-1, 1]) shape(circ(sx * 22, -452, 15), 'rgba(255,255,255,0.25)', { w: 4, color: P.ink });
    line([[-7, -452], [7, -452]], { w: 4, color: P.ink });
    line([[-10, -420], [10, -420]], { w: 4, color: P.ink });
  });
}
