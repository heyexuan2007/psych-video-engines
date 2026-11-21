// 封面：?cover=1&w=1440&h=1080（横 4:3）、?cover=1&w=1080&h=1440（竖 3:4）
(() => {
  window.DUR = 1;
  const tall = H > W, cx = W / 2;
  const L = tall ? { y1: 250, y2: 405, size: 132, s: 1.25, gy: 1230, sub: 1345, eyes: [[150, 640], [930, 600], [210, 900], [880, 880], [120, 1120], [960, 1120], [330, 560], [760, 520]] }
                 : { y1: 190, y2: 335, size: 124, s: 1.1, gy: 950, sub: 0, eyes: [[150, 520], [1290, 500], [260, 760], [1180, 740], [380, 420], [1060, 420], [120, 900], [1320, 900]] };
  function scene(t) {
    camera(cx, H / 2, 1, () => {
      ctx.save(); ctx.translate(cx - 866, 0); stage(); ctx.restore();
      spot(cx, L.gy, { w: 200 * L.s / 1.1, h: 470 * L.s, top: -200 });
      drawKid(cx, L.gy, L.s, { hair: 5, shirt: C.pink, print: 'singer', seed: 685, t: 3.3, eyes: 'wide', mouth: 'wave', brow: -0.8, blush: 1, sweat: 1, look: [-1, 0], armL: -0.62, armR: -0.62, shake: 0 });
      over(() => {
        L.eyes.forEach(([x, y], i) => eyePair(x, y, 0.85, 1, [x < cx ? 1 : -1, 0.2]));
        txt('全场都在看{{你}}', cx, L.y1, { size: L.size, font: F.serif, weight: 900, t: 99, t0: 0, cps: 0 });
        txt('[[吗？]]', cx, L.y2, { size: L.size, font: F.serif, weight: 900, t: 99, t0: 0, cps: 0 });
        if (L.sub) txt('2000 · 尴尬 T 恤实验', cx, L.sub, { size: 46, weight: 400, color: '#d8cfbf', t: 99, t0: 0, cps: 0 });
      });
    }, 0);
  }
  SCENES.push({ id: 'cover', t0: -1, t1: 99, draw(t) { put(shot(scene, 3.3, BUF[0])); } });
})();
