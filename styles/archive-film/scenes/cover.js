// 封面：?cover=1&w=1440&h=1080（横 4:3）或 w=1080&h=1440（竖 3:4）
(() => {
  window.DUR = 1;
  const tall = H > W;
  function cv(t) {
    labRoom({ clock: false, gy: tall ? H * 0.72 : H * 0.78 });
    const s = (W - 60) / 1620, gy = tall ? H * 0.5 : H * 0.48;
    drawKid(W * 0.26, gy + 120 * s / 0.85, 1.15 * s / 0.85, { coat: C.white, under: C.cream, tie: C.grayD, hair: 0, glasses: 1, eyes: 'dot', mouth: 'flat', look: [0.6, 0.5], armL: 0.15, armR: 0.15, seed: 710 });
    at(W / 2, gy, s, 0, () => { const g = generator(0, 0, 46, { down: 9 }); hand(g.sx(9) + 14, 246, 1.05, 0.08, { sleeve: '#b9c3cc' }); });
    const ty = tall ? H * 0.17 : H * 0.17;
    red(() => txt('450V', W * (tall ? 0.5 : 0.72), tall ? H * 0.36 : H * 0.4, { size: tall ? 200 : 170, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
    txt('有人让你电一个陌生人', W / 2, ty - (tall ? 110 : 95), { size: tall ? 62 : 56, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    red(() => txt('你按到第几个？', W / 2, ty + (tall ? 30 : 20), { size: tall ? 120 : 110, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
  }
  SCENES.push({ id: 'cover', t0: -1, t1: 99, draw(t) { film(shot(cv, 2.0, BUF[0])); } });
})();
