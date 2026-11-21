// 封面：?cover=1&w=1440&h=1080（横 4:3）、?cover=1&w=1080&h=1440（竖 3:4）
(() => {
  window.DUR = 1;
  const tall = H > W;
  const L = tall
    ? { cx: W / 2, cy: 880, card: [W / 2, 900, 1.2], t1: [W / 2, 235], t2: [W / 2, 385], size: 118, align: 'center', sub: [W / 2, 1345] }
    : { cx: 420, cy: 540, card: [400, 560, 1.18], t1: [960, 420], t2: [960, 575], size: 112, align: 'center', sub: [960, 700] };
  function scene(t) {
    mysticBG(t, { cx: L.cx, cy: L.cy, r: tall ? 470 : 430, ringA: 0.45 });
    glowLight(L.card[0], L.card[1], 520, 560, { i: 0.6, col: '#ffe2b8' });
    tarot(L.card[0], L.card[1], L.card[2], { back: { label: '致 · 你' }, lit: 0.6, rot: -0.04 });
    over(() => {
      txt('被说中，', L.t1[0], L.t1[1], { size: L.size, font: F.serif, weight: 900, color: PM.parch, t: 99, t0: 0, cps: 0 });
      txt('[[不代表被看穿]]', L.t2[0], L.t2[1], { size: L.size, font: F.serif, weight: 900, color: PM.goldL, t: 99, t0: 0, cps: 0 });
      txt('巴纳姆效应 · 1948 福勒实验', L.sub[0], L.sub[1], { size: 44, font: F.serif, weight: 900, color: PM.lav, t: 99, t0: 0, cps: 0, spacing: 0.06 });
    });
  }
  SCENES.push({ id: 'cover', t0: -1, t1: 99, draw(t) { put(shot(scene, 3.3, BUF[0])); } });
})();
