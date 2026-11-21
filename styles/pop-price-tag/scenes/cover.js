// 封面：?cover=1&w=1440&h=1080（横 4:3）或 w=1080&h=1440（竖 3:4）
// 黄卡纸：上面大标题“这件 200，砍到 100 / 你赚了吗？”；下面吊牌 200 划掉 + 100 贴纸，绳子拴在摊主的铁锚上
(() => {
  window.DUR = 1;
  const tall = H > W;
  function cv(t) {
    card(C.Y);
    const s = tall ? W / 1080 : H / 1080;
    sparkle(W * 0.08, H * (tall ? 0.06 : 0.1), 0.9 * s, C.white, 0.3); sparkle(W * 0.93, H * (tall ? 0.33 : 0.5), 0.8 * s, C.P); sparkle(W * 0.1, H * (tall ? 0.6 : 0.88), 0.7 * s, C.O, 0.4);
    // 标题
    const ty = tall ? H * 0.12 : H * 0.15;
    ptxt('这件 200，砍到 100', W / 2, ty, { size: (tall ? 74 : 70) * s, t: 99, t0: 0, sticker: 1, seed: 3 });
    ptxt('你赚了吗？', W / 2, ty + (tall ? 190 : 170) * s, { size: (tall ? 160 : 150) * s, t: 99, t0: 0, color: C.red, lw: 0.1, sticker: 1, seed: 7, jit: 0.07 });
    // 锚 → 绳子 → 吊牌（绳子压在吊牌下面，像拴在牌子背后）
    const tw = (tall ? 380 : 360) * s, th = (tall ? 320 : 300) * s, k = tw / 300;
    const tg = tall ? [W * 0.34, H * 0.52] : [W * 0.3, H * 0.64], an = tall ? [W * 0.7, H * 0.8] : [W * 0.74, H * 0.72];
    const ring = anchorIcon(an[0], an[1], (tall ? 1.25 : 1.2) * s, 0.08);
    at(an[0] + (tall ? 170 : -20) * s, an[1] - (tall ? 150 : 180) * s, s, 0.06, () => { shape(box(-120, -40, 240, 80, 10), C.white, { w: 5 }); ptxt('摊主喊的', 0, 16, { size: 42, t: 99, t0: 0 }); });
    rope([tg[0], tg[1] - th / 2 + tw * 0.16 * 0.9], ring, 70 * s);
    priceTag(tg[0], tg[1], tw, th, -0.08, () => {
      popNum('200', 0, 82 * k, 104 * k, { color: C.ink, line: C.ink, hi: false, drop: false, ox: 0.7 });
      strike(-120 * k, 40 * k, 120 * k, 18 * k, 1, { w: 9 * k, gap: 22 * k });
      at(100 * k, 104 * k, k, -0.2, () => { shape(circ(0, 0, 66), C.P, { w: 5, off: 0 }); popNum('100', 0, 22, 48, { color: C.white, hi: false }); });
    }, { len: 0.01, bg: C.Y, hole: 14 * k });
    // 小标签
    at(tall ? W * 0.22 : W * 0.14, tall ? H * 0.9 : H * 0.9, s, -0.05, () => { shape(box(-130, -36, 260, 72, 10), C.white, { w: 5 }); ptxt('锚定效应', 0, 15, { size: 42, t: 99, t0: 0, color: C.red }); });
  }
  SCENES.push({ id: 'cover', t0: -1, t1: 99, draw(t) { put(shot(cv, 0.3, BUF[0])); } });
})();
