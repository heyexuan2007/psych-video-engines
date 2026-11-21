// 风格样帧：?sample=1 开场价签 / 2 转盘实验 / 3 夜市砍价 / 4 锚 + 绳子 + 尺子
(() => {
  const N = +QS.get('sample'); window.DUR = 1;
  const ME = { hair: 5, shirt: C.B, pants: C.navy, seed: 501 };

  // 1：黄卡纸。吊牌上“原价 ¥999”被红笔划掉，橙色爆炸贴“现价 ¥299”拍在上面；右边“你”托着下巴
  function s1(t) {
    card(C.Y);
    sparkle(220, 230, 1.1, C.white, 0.2); sparkle(1500, 170, 0.8, C.O); sparkle(170, 640, 0.7, C.P, 0.4);
    priceTag(640, 470, 620, 640, -0.05, () => {
      ptxt('原价', -170, -150, { size: 64, t: 99, t0: 0 });
      popNum('¥999', -6, 100, 200, { color: C.ink, line: C.ink, hi: false, ox: 0.6, drop: false });
      strike(-240, 10, 240, -16, 1, { w: 14, gap: 30 });
      line([[-230, 200], [230, 200]], { w: 4, dash: [2, 18] });
      note('货号 A-0999', -230, 262, { size: 30, align: 'left' });
    }, { len: 500, sx: 40 });
    starburst(1130, 430, 250, C.O, { seed: 7, rot: 0.08, fn: () => {
      ptxt('现价', 0, -96, { size: 58, color: C.white, lw: 0.16, t: 99, t0: 0 });
      popNum('¥299', 0, 96, 170, { color: C.red });
    } });
    drawKid(1440, 860, 1.05, { ...ME, t, eyes: 'dot', mouth: 'flat', brow: -0.4, look: [-1, -0.4], armL: 0.25, armR: -2.13 });
    popNum('?', 1530, 460, 110, { color: C.white });
  }

  // 2：粉卡纸，左右两组：转盘停在 10 / 65，下面的人举牌 25% / 45%
  function s2(t) {
    card(C.P);
    line([[866, 250], [866, 780]], { w: 6, dash: [26, 22] });
    banner(866, 104, 980, 100, -0.01, () => ptxt('非洲国家占联合国百分之几？', 0, 20, { size: 50, t: 99, t0: 0 }));
    const da = Math.PI * 2 / 20;
    wheel(330, 500, 165, -2 * da, { hl: i => i === 2 });
    wheel(1100, 500, 165, -13 * da, { hl: i => i === 13 });
    popNum('10', 330, 300, 76, { color: C.Y });
    popNum('65', 1100, 300, 76, { color: C.Y });
    sign(640, 525, 270, 160, 0.03, () => popNum('25%', 0, 58, 110, { color: C.B }), { stick: false });
    drawKid(640, 840, 0.82, { hair: 1, shirt: C.G, seed: 520, t, eyes: 'dot', mouth: 'smile', look: [0, -0.6], armL: 2.85, armR: 2.85 });
    sign(1410, 525, 270, 160, -0.04, () => popNum('45%', 0, 58, 110, { color: C.O }), { stick: false });
    drawKid(1410, 840, 0.82, { hair: 3, shirt: C.Y, seed: 530, t, eyes: 'dot', mouth: 'grin', look: [0, -0.6], armL: 2.85, armR: 2.85 });
    roundStamp('1974', 170, 230, 0.7, -0.15, 1);
  }

  // 3：青卡纸当夜空。左边摊主“行行行”，你拎着袋子得意；右边隔壁摊同款挂着 50
  function s3(t) {
    card(C.B);
    moon(1480, 170, 56);
    lights(-40, 120, 1960, 150, 70, 14, t);
    stall(560, 980, 820, { label: '潮T 清仓', col: C.red, labelX: -230 });
    tshirt(380, 360, 0.9, C.P);
    priceTag(470, 580, 190, 160, 0.12, () => { popNum('200', 0, 56, 62, { color: C.ink, line: C.ink, hi: false, drop: false, ox: 0.7 }); strike(-74, 30, 74, 18, 1, { w: 6, gap: 14 }); }, { len: 60, sx: -20, bg: C.P, hole: 10 });
    drawKid(700, 760, 0.95, { hair: 3, shirt: C.O, apron: C.G, seed: 540, t, eyes: 'closed', mouth: 'wave', brow: 0.4, look: [0.6, 0], armL: 0.3, armR: 2.2 });
    say('行行行，100 拿走！', 800, 300, 1, { size: 42, tx: -90, ty: 120 });
    drawKid(1030, 900, 1.0, { ...ME, t, eyes: 'happy', mouth: 'smug', look: [1, 0], armL: 0.3, armR: 0.5, bag: 'R', bagCol: C.Y });
    stall(1460, 980, 300, { n: 3, col: C.navy, h: 600, table: true });
    tshirt(1460, 420, 0.9, C.P);
    starburst(1460, 700, 110, C.Y, { seed: 9, rot: -0.1, fn: () => popNum('50', 0, 40, 100, { color: C.red }) });
  }

  // 4：钻进你脑子里：一把 0–200 的尺子，摊主在 200 扔下铁锚，绳子拴着你；你往下砍到 100 就停了，50 在更远的地方
  function s4(t) {
    card(C.Y);
    sparkle(1500, 150, 0.8, C.white, 0.3); sparkle(180, 300, 0.7, C.O);
    const X = ruler(240, 1440, 640, 0, 200, { step: 10, major: 50 });
    // 摊主扔下的锚（200 处）+ 标签
    const ring = anchorIcon(1440, 450, 0.95);
    sign(1440, 250, 270, 150, 0.05, () => { ptxt('摊主喊的', 0, -22, { size: 40, t: 99, t0: 0 }); popNum('200', 0, 62, 70, { color: C.red }); }, { stick: false });
    // 你从 200 一路往左走到 100：脚印
    for (let v = 190; v > 104; v -= 9) shape(oval(X(v), 616 + (Math.round(v / 9) % 2 ? -6 : 6), 11, 6), C.ink, { stroke: false, off: 0, alpha: 0.45 });
    // 隔壁的 50：虚线圈 + 小爆炸贴
    starburst(X(50), 470, 92, C.P, { seed: 4, rot: 0.1, fn: () => popNum('50', 0, 34, 84, { color: C.white }) });
    note('隔壁', X(50), 360, { size: 34, weight: 900 });
    stroke([[X(50), 560], [X(50), 636]], 1, { w: 5, dash: [8, 12] });
    // 你：脸朝左想再往下走，被腰上的绳子拽住
    const kid = drawKid(X(100), 630, 0.78, { hair: 5, shirt: C.B, pants: C.navy, seed: 501, t, flip: -1, lean: 0.22, eyes: 'dot', mouth: 'flat', brow: 0.3, look: [-1, 0], armL: 1.4, armR: 1.1, legs: 0.7, sweat: 1 });
    rope([X(100) + 34, 630 - 116 * 0.78], ring, 6);
    say('差不多了吧', X(100) - 170, 270, 1, { size: 40, tx: 70, ty: 90 });
  }
  const CAPS = ['', '原价 999，现价 299，你觉得值吗？', '转到 10 的猜 {{25%}}，转到 65 的猜 {{45%}}', '隔壁同款，只要 {{50}}', '起点是他给的，你却以为是自己定的'];
  SCENES.push({ id: 's', t0: -1, t1: 99, draw(t) { put(shot([null, s1, s2, s3, s4][N], t, BUF[0])); }, caps(t) { cap(CAPS[N], 9, 0, 20, 'c'); } });
})();
