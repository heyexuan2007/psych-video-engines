// 画风样帧：A1 第一帧 / A2 打勾卡 / A3 实验 4.26；B1–B3 同样三个镜头的烛光版
(() => {
  const N = QS.get('sample'); window.DUR = 1;
  const T0 = 2.2;
  const CARD1 = '你表面自律，心里却常常不安。', CARD2 = '你很想被人喜欢，又总对自己挑剔。';

  // ---------- A：老马戏海报 ----------
  function A1(t) {
    posterBG(t, { cx: 866, cy: 560 });
    archText('专属于你的性格报告', 866, 690, 440, -Math.PI * 0.8, -Math.PI * 0.2, { size: 72, col: PA.navy });
    for (const [x, y, r] of [[330, 470, 26], [1400, 470, 26], [360, 680, 18], [1370, 680, 18], [470, 820, 14], [1260, 820, 14]]) star(x, y, r, PA.mustard, PA.ink);
    envelope(866, 610, 0.9, { pal: PA.env, seal: '你', sealS: 1.35, rot: -0.03, stripes: [PA.red, PA.navy] });
  }
  function A2(t) {
    posterBG(t, { cx: 866, cy: 470, rayA: 0.55, glowR: 760 });
    traitCard(230, 250, CARD1, { pal: PA.cardPal, deco: 'ticket', w: 1300, h: 180, tick: 1, rot: -0.02, size: 58 });
    traitCard(250, 480, CARD2, { pal: PA.cardPal, deco: 'ticket', w: 1300, h: 180, tick: 0.55, rot: 0.015, size: 58 });
    // 打勾的钢笔
    at(536, 535, 1, 0.5, () => { shape(box(-14, -170, 28, 170, 6), PA.navy, { w: 4, color: PA.ink }); shape(poly([[-14, 0], [14, 0], [0, 40]]), PA.mustard, { w: 4, color: PA.ink }); });
  }
  function A3(t) {
    posterBG(t, { cx: 866, cy: 420, glowR: 620 });
    woodType('1948 · 福勒的课堂', 866, 245, { size: 58, col: PA.navy, depth: 4 });
    woodType('4.26', 1080, 540, { size: 270, col: PA.red, depth: 14, off: 7, font: F.lat, spacing: 0, align: 'right' });
    woodType('/ 5', 1110, 540, { size: 120, col: PA.navy, depth: 7, font: F.lat, spacing: 0, align: 'left' });
    txt('平均准确度', 866, 612, { size: 44, font: F.serif, weight: 900, color: PA.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    const cols = [PA.navy, PA.teal, PA.mustard, PA.red, PA.navyL, PA.teal, PA.navy];
    [5, 4, 5, 4, 4, 5, 4].forEach((n, i) => student(200 + i * 222, 1040, 0.8, { pal: PA.kid, col: cols[i], skin: '#f0c9a0', arm: i % 3 === 1 ? 0.7 : 1, num: n, seed: 40 + i * 7, smile: i % 2 }));
  }

  // ---------- B：占卜桌烛光 ----------
  function B1(t) {
    ambient(PB.amb);
    tableBG(t);
    tarotBack(1460, 300, 1, 0.35); tarotBack(220, 260, 0.9, -0.25);
    glowLight(900, 560, 520, 400, { i: 0.35, col: '#ffd9a0' });
    envelope(900, 560, 0.95, { pal: PB.env, seal: '你', sealS: 1.35, rot: 0.04 });
    candle(330, 820, 1.15, t, { reach: 1000 });
  }
  function B2(t) {
    ambient(PB.amb);
    tableBG(t);
    tarotBack(1520, 760, 0.9, -0.3);
    glowLight(900, 420, 780, 380, { i: 0.3, col: '#ffd9a0' });
    traitCard(300, 230, CARD1, { pal: PB.cardPal, w: 1220, h: 180, rot: -0.02, size: 58 });
    traitCard(320, 460, CARD2, { pal: PB.cardPal, w: 1220, h: 180, rot: 0.02, size: 58 });
    goldTick(300 + 102, 230 + 88, 1.05, 1); goldTick(320 + 102, 460 + 88, 1.05, 0.55);
    candle(170, 900, 1.0, t, { reach: 1100 });
  }
  function B3(t) {
    ambient(PB.amb);
    tableBG(t);
    candle(190, 900, 1.0, t, { reach: 800 }); candle(1540, 900, 0.85, t + 1.3, { reach: 700 });
    crystalBall(866, 520, 270, () => {
      const g = ctx.createLinearGradient(0, 250, 0, 790); g.addColorStop(0, '#6a7cc0'); g.addColorStop(1, '#2a2f5c'); ctx.fillStyle = g; ctx.fillRect(590, 250, 560, 560);
      // 黑板上粉笔写着 1948
      shape(box(730, 330, 272, 110, 6), '#2c4a3c', { w: 4, color: '#0d0a14' });
      txt('1948', 866, 408, { size: 58, font: F.serif, weight: 900, color: '#eef2e8', t: 99, t0: 0, cps: 0, shadow: 0 });
      [5, 4, 5, 4, 5].forEach((n, i) => student(646 + i * 110, 810, 0.55, { pal: PB.kid, col: '#151124', skin: '#151124', hair: '#151124', arm: 1, num: n, seed: 70 + i * 5, face: false }));
    }, { lit: 1 });
    over(() => {
      txt('4.26', 1000, 205, { size: 150, font: F.lat, weight: 900, color: PB.goldL, glow: 1, t: 99, t0: 0, cps: 0, spacing: 0, align: 'right' });
      txt('/ 5', 1020, 205, { size: 70, font: F.lat, weight: 900, color: PB.gold, t: 99, t0: 0, cps: 0, spacing: 0, align: 'left' });
    });
  }

  const CAPS = { A1: '刷到这条的你——', A3: '准不准？满分 5 分，平均打了 4.26。', B1: '刷到这条的你——', B3: '准不准？满分 5 分，平均打了 4.26。' };
  const FN = { A1, A2, A3, B1, B2, B3 };
  SCENES.push({ id: 's', t0: -1, t1: 99, draw(t) {
    if (N[0] === 'A') { FN[N](T0); if (CAPS[N]) ribbonCap(CAPS[N], 9, 0, 20, 'c'); paperOver(); }
    else if (N[0] === 'B') { put(shot(FN[N], T0, BUF[0])); if (CAPS[N]) candleCap(CAPS[N], 9, 0, 20, 'c'); }
  } });
})();

// ---------- B'：神秘塔罗 v2（外行也看得懂）：N1 第一帧 / N2 三牌阵 / N3 发牌 / N4 4.26 / N5 39 张一样 ----------
(() => {
  const N = QS.get('sample'); if (!N || N[0] !== 'N') return;
  const T0 = 2.2;
  const MASK = { num: 'XV', name: '面具', art: 'mask', lines: ['表面自律', '心里不安'] };
  const MIRROR = { num: 'VI', name: '镜子', art: 'mirror', lines: ['想被喜欢', '又挑剔自己'] };
  const SEED = { num: 'I', name: '种子', art: 'seed', lines: ['潜力很多', '还没发挥'] };
  const KID = { ink: PM.gold, hair: '#1a1f45', stick: PM.gold, paddle: '#f0e0bf', paddleInk: PM.crimson };
  const TCH = { ink: PM.gold, trouser: '#1a1f45', coat: '#1a1f45', tie: PM.crimson, skin: '#1a1f45', hairT: '#1a1f45' };
  const kid = (x, y, s, o = {}) => student(x, y, s, { pal: KID, col: '#1a1f45', skin: '#1a1f45', hair: '#1a1f45', face: false, ...o });

  function N1(t) {
    mysticBG(t, { cy: 460 });
    glowLight(866, 460, 420, 460, { i: 0.55, col: '#ffe2b8' });
    tarot(866, 455, 1.2, { back: { label: '致 · 你' }, lit: 0.55, rot: -0.02 });
    sideCandles(t);
    over(() => { smoke(t, 150, 700, 520, 1); smoke(t, 1600, 760, 480, 4); });
  }
  function N2(t) {
    mysticBG(t, { cy: 420, ringA: 0.3 });
    glowLight(866, 420, 700, 420, { i: 0.5, col: '#ffe2b8' });
    tarot(486, 400, 0.9, { face: MASK, flip: 1, lit: 0.6, check: 1, rot: -0.03 });
    tarot(866, 390, 0.9, { face: MIRROR, flip: 1, lit: 1, check: 0.6 });
    tarot(1246, 400, 0.9, { back: {}, flip: 0, rot: 0.03 });
    sideCandles(t, { ls: 0.8, rs: 0.7 });
    over(() => smoke(t, 1600, 800, 500, 2));
  }
  function N3(t) {
    mysticBG(t, { cy: 520, r: 560, ringA: 0.22 });
    glowLight(980, 560, 900, 420, { i: 0.45, col: '#d8d0ff' });
    const hand = [290 + 150 * 0.85, 800 - 330 * 0.85];
    teacher(290, 800, 0.85, { pal: TCH, papers: (x, y) => { for (let k = 0; k < 4; k++) tarot(x + k * 3, y - k * 4, 0.16, { back: {}, rot: 0.2 }); } });
    let n = 0;
    for (const ry of [430, 590, 750]) for (let i = 0; i < 13; i++, n++) {
      const x = 560 + i * 80;
      kid(x, ry, 0.36, { seed: 90 + n * 3 });
      const tgt = [x, ry - 22], fly = [0.3, 0.5, 0.7, 0.86][n - 35];
      if (fly == null) tarot(tgt[0], tgt[1], 0.1, { back: {}, rot: (hash(n) - 0.5) * 0.3 });
      else {
        const c = [(hand[0] + tgt[0]) / 2, Math.min(hand[1], tgt[1]) - 260], P = qd(hand, c, tgt, 30);
        line(P.slice(0, Math.round(fly * 30) + 1), { w: 2, color: PM.goldL, alpha: 0.6, dash: [6, 8] });
        const q = P[Math.round(fly * 30)]; tarot(q[0], q[1], 0.1, { back: {}, rot: fly * 6 });
      }
    }
    over(() => txt('1948 · 福勒的课堂 · 39 名学生', 1040, 250, { size: 40, font: F.serif, weight: 900, color: PM.lav, t: 99, t0: 0, cps: 0, spacing: 0.08 }));
    sideCandles(t, { ls: 0.75, rx: 1640, rs: 0.65 });
  }
  function N4(t) {
    mysticBG(t, { cy: 330, r: 240, ringA: 0.6 });
    glowLight(866, 330, 420, 320, { i: 0.4, col: '#c8c0ff' });
    glowLight(866, 760, 800, 260, { i: 0.4, col: '#ffe2b8' });
    [5, 4, 5, 4, 4, 5, 3, 5, 4, 5, 4].forEach((v, i) => kid(336 + i * 106, 840, 0.48, { arm: 1, num: v, seed: 140 + i * 7 }));
    sideCandles(t, { ls: 0.8, rs: 0.7 });
    over(() => {
      txt('1948 · 福勒的课堂', 866, 250, { size: 34, font: F.serif, weight: 900, color: PM.lav, t: 99, t0: 0, cps: 0, spacing: 0.1 });
      txt('4.26', 960, 390, { size: 150, font: F.lat, weight: 900, color: PM.goldL, glow: 1, t: 99, t0: 0, cps: 0, spacing: 0, align: 'right' });
      txt('/ 5', 980, 390, { size: 64, font: F.lat, weight: 900, color: PM.gold, t: 99, t0: 0, cps: 0, spacing: 0, align: 'left' });
      txt('39 人的平均准确度', 866, 455, { size: 32, font: F.serif, weight: 900, color: PM.parch, t: 99, t0: 0, cps: 0, spacing: 0.1 });
    });
  }
  function N5(t) {
    mysticBG(t, { cy: 450, r: 520, ringA: 0.25 });
    glowLight(866, 450, 900, 420, { i: 0.5, col: '#ffe2b8' });
    for (let j = 0; j < 3; j++) for (let i = 0; i < 13; i++) tarot(190 + i * 113, 255 + j * 200, 0.34, { face: MASK, flip: 1, lit: 0.25 });
  }
  const CAPS = { N1: '刷到这条的你——', N2: '你很想被人喜欢，又总对自己挑剔。', N3: '一周后，每人拿到一份“专属”分析。', N4: '准不准？满分 5 分，平均打了 4.26。', N5: '可这 39 份，一字不差。' };
  const FN = { N1, N2, N3, N4, N5 };
  SCENES.push({ id: 'n', t0: -1, t1: 99, draw(t) { put(shot(FN[N], T0, BUF[0])); mysticCap(CAPS[N], 9, 0, 20, 'c'); } });
})();
