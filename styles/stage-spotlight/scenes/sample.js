// 风格样帧：?sample=1 开场追光 / 2 开灯揭晓 / 3 结尾人人一束光
(() => {
  const N = +QS.get('sample'); window.DUR = 1;
  const GY = 800;
  function s1(t) {
    stage();
    const dark = [[200, 0], [420, 3], [1310, 1], [1530, 4]];
    dark.forEach(([x, h], i) => drawKid(x, 790, 0.82, { hair: h, shirt: C.gray, seed: 520 + i * 7, eyes: 'dot' }));
    spot(866, GY, { w: 175 });
    drawKid(866, GY, 1.05, { hair: 5, shirt: C.pink, print: 'singer', eyes: 'wide', mouth: 'wave', brow: -0.8, look: [-1, 0], sweat: 1, armL: 0.35, armR: 0.35, blush: 1 });
    // 前排观众的后脑勺
    for (let i = 0; i < 9; i++) { const x = 40 + i * 230 + (i % 2) * 40, y = 1060 + (i % 2) * 30; shape(circ(x, y - 70, 74), '#1a1c26', { stroke: false }); shape(box(x - 110, y - 10, 220, 120, 50), '#1a1c26', { stroke: false }); }
    over(() => {
      dark.forEach(([x], i) => eyePair(x, 790 - 0.82 * 262, 0.82, 1, [x < 866 ? 1 : -1, 0]));
      for (const [x, y, s] of [[90, 470, 0.7], [640, 380, 0.6], [1120, 400, 0.6], [1700, 520, 0.75], [300, 300, 0.5], [1450, 300, 0.5], [760, 560, 0.55], [1000, 600, 0.55]]) eyePair(x, y, s, 1, [x < 866 ? 1 : -1, 0.3]);
      txt('全场都在看{{你}}？', 866, 205, { size: 128, font: F.serif, weight: 900, t: 99, t0: 0, cps: 0 });
    });
  }
  function s2(t) {
    stage({ wall: '#6a5a4a' });
    ambient('#d9cfbf');
    blackboard(250, 790, 0.95, () => txt('自习', 0, -300, { size: 70, font: F.serif, weight: 900, color: '#e8efe6', t: 99, t0: 0, cps: 0, shadow: 0 }));
    const SX = [470, 680, 866, 1060, 1270];
    const r0 = drawKid(SX[0], 800, 0.78, { hair: 1, shirt: C.teal, eyes: 'dot', mouth: 'smile', look: [0, 1], armR: 0.9, phone: 1, phoneOn: 1, seed: 531 });
    drawKid(SX[1], 800, 0.78, { hair: 0, shirt: C.mustard, eyes: 'closed', mouth: 'flat', look: [0, 1], armL: 0.7, armR: 0.7, lean: 0.12, seed: 538 });
    spot(SX[2], 840, { w: 130, i: 0.6, beam: 0.5 });
    drawKid(SX[2], 800, 0.78, { hair: 5, shirt: C.pink, print: 'singer', eyes: 'wide', mouth: 'o', brow: -0.5, look: [1, 0], sweat: 1, armL: 0.4, armR: 0.4 });
    drawKid(SX[3], 800, 0.78, { hair: 3, shirt: C.olive, eyes: 'closed', mouth: 'yawn', armL: 2.9, armR: 2.9, seed: 545 });
    const r4 = drawKid(SX[4], 800, 0.78, { hair: 6, shirt: C.blue, eyes: 'dot', mouth: 'smile', look: [-1, -0.5], armR: 2.2, seed: 552 });
    mirror(r4.handR[0] - 30, r4.handR[1] - 40, 0.9);
    SX.forEach(x => desk(x, 830, 0.86));
    over(() => {
      txt('46%', 560, 230, { size: 120, font: F.lat, weight: 900, color: C.gray, t: 99, t0: 0, cps: 0, spacing: 0 });
      line([[440, 205], [680, 175]], { w: 12, color: C.red });
      bigNum('23%', 1000, 290, 9, 0);
      txt('他猜的', 560, 290, { size: 40, color: C.cream, t: 99, t0: 0, cps: 0 });
      txt('真正注意到的', 1000, 350, { size: 40, color: C.cream, t: 99, t0: 0, cps: 0 });
    });
  }
  function s3(t) {
    camera(866, 520, 0.6, () => {
      stage();
      ambient('#1c1e2c');
      const P = [[-330, 6, C.teal, 'mirror'], [-60, 3, C.olive, 'shirt'], [260, 1, C.mustard, 'phone'], [866, 5, C.pink, 'me'], [1470, 4, C.blue, 'hair'], [1790, 0, C.red, 'phone'], [2060, 2, C.cream, 'sweat']];
      P.forEach(([x, h, col, k], i) => {
        spot(x, 800, { w: 160, i: 0.95, seed: i + 2, tx: x + (i - 3) * 30 });
        const me = k === 'me';
        const r = drawKid(x, 800, 1, { hair: h, shirt: col, print: me ? 'singer' : null, seed: 560 + i * 9, eyes: me ? 'wide' : k === 'sweat' ? 'wide' : 'dot', mouth: me ? 'o' : k === 'sweat' ? 'wave' : 'flat', brow: -0.5, sweat: k === 'sweat' || me ? 1 : 0,
          look: k === 'shirt' ? [0, 1] : k === 'phone' ? [0.6, 0.6] : k === 'hair' ? [0, -1] : me ? [-1, 0] : [1, -0.4], armR: k === 'phone' ? 1.0 : k === 'mirror' ? 2.2 : k === 'hair' ? 2.8 : 0.3, armL: k === 'hair' ? 2.8 : k === 'shirt' ? 0.6 : 0.3, phone: k === 'phone', phoneOn: 1, lean: k === 'shirt' ? 0.08 : 0 });
        if (k === 'mirror') mirror(r.handR[0] - 30, r.handR[1] - 40, 1);
      });
    }, -94);
  }
  SCENES.push({ id: 's', t0: -1, t1: 99, draw(t) { put(shot([null, s1, s2, s3][N], 3.3, BUF[0])); if (N === 1) cap('穿了件丢人的 T 恤进教室，', 9, 0, 20, 'c'); if (N === 2) cap('实际：只有 [[23%]] 的人注意到。', 9, 0, 20, 'c'); if (N === 3) cap('因为每个人，都站在[[自己的聚光灯]]下。', 9, 0, 20, 'c'); } });
})();
