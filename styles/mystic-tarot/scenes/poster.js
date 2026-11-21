// 画风 A：老马戏海报。米色旧纸 + 红色放射线 + 灯泡边框 + 木刻大字（带墨块投影）+ 套色错位 + 半调网点。
// 不走光照，直接画在主画布上；最后叠一层纸纹（正片叠底）。

const PA = {
  paper: '#f6e6c6', paperD: '#e8d2a6', cream: '#f3e1bd', red: '#c4282e', redD: '#8a1820', navy: '#1e2a4a', navyL: '#33456e',
  mustard: '#e7a537', teal: '#2a7471', ink: '#24181a', bulb: '#ffe7a3',
};
// 道具用的色板
PA.env = { paper: '#f7ead2', paperD: '#e2cba0', ink: PA.ink, seal: PA.red, sealD: PA.redD, sealInk: '#f6dcb4' };
PA.cardPal = { card: '#fbf1dc', ink: PA.ink, box: '#fffaf0', text: PA.navy, tick: PA.red, accent: PA.mustard, edge: PA.ink };
PA.kid = { ink: PA.ink, hair: '#2b1d18', stick: '#7a5234', paddle: '#fbf1dc', paddleInk: PA.red };
PA.tch = { ink: PA.ink, trouser: PA.navy, coat: '#6b5a48', tie: PA.red, skin: '#f0c9a0', hairT: '#5a5150' };

let PAPER = null;
function makePaper() {
  PAPER = mk(); const g = PAPER.getContext('2d'), r = rng(31);
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, W, H);
  // 纤维和斑点
  for (let i = 0; i < 26000; i++) { const v = 200 + r() * 55; g.fillStyle = `rgba(${v},${v - 12},${v - 34},${0.08 + r() * 0.12})`; g.fillRect(r() * W, r() * H, 1 + r() * 3, 1 + r() * 2); }
  for (let i = 0; i < 40; i++) { const x = r() * W, y = r() * H, rr = 20 + r() * 120, gr = g.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, `rgba(190,150,90,${0.06 + r() * 0.08})`); gr.addColorStop(1, 'rgba(190,150,90,0)'); g.fillStyle = gr; g.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
  // 两道折痕
  for (const [x0, y0, x1, y1] of [[W * 0.5, 0, W * 0.5 + 6, H], [0, H * 0.5, W, H * 0.5 - 4]]) {
    g.strokeStyle = 'rgba(150,120,80,0.22)'; g.lineWidth = 3; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    g.strokeStyle = 'rgba(255,255,255,0.5)'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x0 + 3, y0 + 3); g.lineTo(x1 + 3, y1 + 3); g.stroke();
  }
  // 四角发黄
  const v = g.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, Math.hypot(W, H) * 0.6); v.addColorStop(0, 'rgba(160,110,50,0)'); v.addColorStop(1, 'rgba(160,110,50,0.35)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
}
function paperOver() { if (!PAPER) makePaper(); MAIN.setTransform(1, 0, 0, 1, 0, 0); MAIN.globalCompositeOperation = 'multiply'; MAIN.drawImage(PAPER, 0, 0); MAIN.globalCompositeOperation = 'source-over'; }

/** 半调网点：在一个区域里，点的大小随 f(x,y) 0..1 变 */
function halftone(x0, y0, x1, y1, step, col, f, alpha = 1) {
  ctx.save(); ctx.globalAlpha = LA * alpha; ctx.fillStyle = col;
  for (let y = y0; y < y1; y += step) for (let x = x0 + ((y / step) % 2 ? step / 2 : 0); x < x1; x += step) { const k = f(x, y); if (k > 0.03) { ctx.beginPath(); ctx.arc(x, y, step * 0.5 * clamp(k), 0, Math.PI * 2); ctx.fill(); } }
  ctx.restore();
}

/** 海报底：放射线 + 中心亮圈 + 网点 + 帷幕 + 灯泡边框 */
function posterBG(t, o = {}) {
  const cx = o.cx ?? 866, cy = o.cy ?? 500, A = o.rays || [PA.red, PA.cream], n = 28, rot = t * 0.03;
  ctx.fillStyle = PA.cream; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < n; i++) {
    if (i % 2) continue; const a0 = rot + i / n * Math.PI * 2, a1 = a0 + Math.PI * 2 / n;
    shape(poly([[cx, cy], [cx + Math.cos(a0) * 2600, cy + Math.sin(a0) * 2600], [cx + Math.cos(a1) * 2600, cy + Math.sin(a1) * 2600]]), A[0], { stroke: false, alpha: o.rayA ?? 0.9 });
  }
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, o.glowR ?? 560); g.addColorStop(0, PA.paper); g.addColorStop(0.55, rgba(PA.paper, 0.95)); g.addColorStop(1, rgba(PA.paper, 0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 角落网点（深蓝）
  halftone(0, 0, W, H, 18, PA.navy, (x, y) => { const d = Math.hypot((x - cx) / W, (y - cy) / H); return (d - 0.5) * 2.2; }, 0.55);
  if (o.curtain !== false) posterCurtain(t);
  bulbFrame(t, o.frame ?? 34);
}
/** 两侧帷幕 + 顶上的波浪帘头 */
function posterCurtain(t) {
  for (const side of [-1, 1]) {
    const x0 = side < 0 ? 0 : W, wv = 210;
    for (let k = 0; k < 5; k++) {
      const xa = x0 - side * k * wv / 5, xb = x0 - side * (k + 1) * wv / 5;
      shape(() => { ctx.moveTo(xa, 0); ctx.lineTo(xb, 0); ctx.quadraticCurveTo(xb - side * 10, H * 0.6, xb + side * (30 - k * 4), H); ctx.lineTo(xa, H); ctx.closePath(); }, k % 2 ? PA.red : PA.redD, { w: 4, color: PA.ink });
    }
    // 绑带
    shape(box(side < 0 ? 0 : W - 230, 600, 230, 34, 10), PA.mustard, { w: 4, color: PA.ink });
  }
  // 帘头波浪
  shape(() => { ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, 70); for (let x = W; x >= 0; x -= 120) ctx.quadraticCurveTo(x - 60, 150, x - 120, 70); ctx.closePath(); }, PA.red, { w: 5, color: PA.ink, shade: [0, -10] });
  for (let x = 60; x < W; x += 120) shape(circ(x, 122, 10), PA.mustard, { w: 3, color: PA.ink });
}
/** 灯泡边框：内框一圈深蓝带子，灯泡依次亮 */
function bulbFrame(t, m) {
  ctx.save(); ctx.lineWidth = m; ctx.strokeStyle = PA.navy; ctx.strokeRect(m / 2, m / 2, W - m, H - m); ctx.restore();
  const pts = [], st = 64;
  for (let x = st / 2; x < W; x += st) { pts.push([x, m / 2]); pts.push([x, H - m / 2]); }
  for (let y = st / 2 + st; y < H - st; y += st) { pts.push([m / 2, y]); pts.push([W - m / 2, y]); }
  pts.forEach(([x, y], i) => {
    const on = (Math.floor(t * 6) + i) % 3 !== 0;
    if (on) { const gr = ctx.createRadialGradient(x, y, 0, x, y, 26); gr.addColorStop(0, rgba(PA.bulb, 0.9)); gr.addColorStop(1, rgba(PA.bulb, 0)); ctx.fillStyle = gr; ctx.fillRect(x - 26, y - 26, 52, 52); }
    shape(circ(x, y, 9), on ? PA.bulb : '#b8a37a', { w: 2.5, color: PA.ink });
  });
}

/** 木刻大字：墨块投影 + 套色错位。o: size, col, shadow 投影色, depth, off 错位 */
function woodType(str, x, y, o = {}) {
  const size = o.size || 140, col = o.col || PA.red, d = o.depth ?? Math.round(size * 0.06), font = o.font || F.serif;
  for (let k = d; k >= 1; k--) txt(str, x + k, y + k, { size, font, weight: 900, color: o.shadow || PA.ink, t: 99, t0: 0, cps: 0, shadow: 0, align: o.align || 'center', spacing: o.spacing ?? 0.02 });
  if (o.off) txt(str, x - o.off, y - o.off * 0.6, { size, font, weight: 900, color: o.offCol || PA.mustard, t: 99, t0: 0, cps: 0, shadow: 0, align: o.align || 'center', spacing: o.spacing ?? 0.02, alpha: 0.9 });
  return txt(str, x, y, { size, font, weight: 900, color: col, t: 99, t0: 0, cps: 0, shadow: 0, align: o.align || 'center', spacing: o.spacing ?? 0.02, id: o.id });
}
/** 沿弧排字（海报顶上的拱形标题） */
function archText(str, cx, cy, R, a0, a1, o = {}) {
  const chars = [...str], n = chars.length;
  chars.forEach((ch, i) => {
    const a = lerp(a0, a1, n === 1 ? 0.5 : i / (n - 1));
    at(cx + Math.cos(a) * R, cy + Math.sin(a) * R, 1, a + Math.PI / 2, () => woodType(ch, 0, 0, { size: o.size || 70, col: o.col || PA.navy, depth: 4, spacing: 0 }));
  });
}
/** 字幕：红色绶带，两头折进去，奶油色字 */
function ribbonCap(str, t, a, b, id, o = {}) {
  if (t < a - 0.1 || t > b + 0.3) return;
  const size = o.size || 54, x = o.x ?? CAPX, y = o.y ?? CAPY;
  const { total } = measure(str, size, F.serif, 900), w = total + 120, h = size * 1.55, y0 = y - size * 1.05;
  const al = Math.min(seg(t, a - 0.1, a + 0.1), 1 - seg(t, b + 0.05, b + 0.3));
  layer(al, () => {
    // 两头的燕尾
    for (const s of [-1, 1]) {
      const ex = x + s * w / 2;
      shape(poly([[ex - s * 10, y0 + 22], [ex + s * 70, y0 + 22], [ex + s * 44, y0 + 22 + h / 2], [ex + s * 70, y0 + 22 + h], [ex - s * 10, y0 + 22 + h]]), PA.redD, { w: 4, color: PA.ink });
    }
    shape(box(x - w / 2, y0, w, h, 4), PA.red, { w: 5, color: PA.ink, shade: [0, -8] });
    line([[x - w / 2 + 16, y0 + 10], [x + w / 2 - 16, y0 + 10]], { w: 2, color: PA.cream, dash: [8, 8], alpha: 0.7 });
    line([[x - w / 2 + 16, y0 + h - 10], [x + w / 2 - 16, y0 + h - 10]], { w: 2, color: PA.cream, dash: [8, 8], alpha: 0.7 });
    txt(str, x, y, { t, t0: a, t1: b + 0.3, size, font: F.serif, weight: 900, color: PA.cream, id, cps: 0.022, shadow: 0 });
  });
}
