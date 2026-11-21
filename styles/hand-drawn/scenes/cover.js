// 封面：?cover=1&w=1440&h=1080（横 4:3）、?cover=1&w=1080&h=1440（竖 3:4）
(() => {
  window.DUR = 1; SCENES.length = 0;
  const tall = H > W;
  const L = tall ? { n: [300, 330, 300], m: [720, 318, 190], l2: [540, 500, 124], p: [470, 1424, 2.5], k: 0.68, from: [1500, 520] }
                 : { n: [300, 420, 320], m: [716, 408, 200], l2: null, p: [1000, 1056, 2.4], k: 0.7, from: [1720, 150] };
  const HIM = { seed: 1500, hair: 0, hairCol: C.ink, shirt: C.white, glasses: 1, badge: 1 };
  SCENES.push({ id: 'cover', t0: -1, t1: 99, draw() {
    const t = 30;
    hw('{{0.1}}', L.n[0], L.n[1], { size: L.n[2], font: F.lat, bold: 0.25, seed: 14, spacing: 0 });
    hw('秒', L.m[0], L.m[1], { size: L.m[2], font: F.wei, bold: 1.3, seed: 15 });
    if (tall) hw('你就给他[[打了分]]', L.l2[0], L.l2[1], { size: L.l2[2], font: F.wei, bold: 1.3, seed: 12, t: 9, t0: 0 });
    else { hw('你就给他', 430, 640, { size: 150, font: F.wei, bold: 1.3, seed: 12 }); hw('[[打了分]]', 430, 830, { size: 176, font: F.wei, bold: 1.3, seed: 13, t: 9, t0: 0 }); }
    const [px, py, ps] = L.p;
    const r = drawPerson(px, py, ps, { ...HIM, t, extra: noteExtra(t, [0, 0, 0, 0, 99], null), eyes: 'wide', mouth: 'wave', brow: -0.8, look: [1, -0.3], sweat: 1 });
    const N = NOTES[4], to = r.pt(N.x, N.y), fx = lerp(L.from[0], to[0], L.k), fy = lerp(L.from[1], to[1], L.k);
    drawHand(L.from[0], L.from[1], fx + (L.from[0] - to[0]) * 0.17, fy + (L.from[1] - to[1]) * 0.17, { s: ps * 0.6 });
    stickyNote(fx, fy, N.txt, { size: 36 * ps, rot: 0.22, col: C.red, seed: 1338 });
  } });
})();
