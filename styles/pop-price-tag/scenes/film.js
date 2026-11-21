// 《你以为是自己判断的》整片：5 个镜头 + 字幕 + 音效事件（41.5 秒；11-18 按用户要求把转盘段放慢了 5 秒）
// 一条线：夜市砍价 200→100，隔壁 50 → 钻进脑子里：摊主在 200 扔下铁锚，绳子拴着你，砍到“差不多”就停
// → 1974 转盘（10/65 → 猜 25%/45%），答案被锚拽着 → 1987 房产经纪人：挂价高估得就高，问依据几乎没人提挂价
// → 回到夜市：“我是自己判断的”，绳子连着摊主的锚。
// 反复出现的画面：尺子 + 铁锚 + 绳子。字都在抖音安全区里（x 134–1594，y 119–929）。
(() => {
  window.DUR = 41.5;
  const ME = { hair: 5, shirt: C.V, pants: C.navy, seed: 501 };
  const VEN = { hair: 3, shirt: C.O, apron: C.G, seed: 540 };
  const GUESS = [{ hair: 1, shirt: C.G, seed: 520 }, { hair: 3, shirt: C.Y, seed: 530 }];
  const AGENT = [{ hair: 0, shirt: C.white, tie: C.red, glasses: 1, seed: 560 }, { hair: 6, shirt: C.O, tie: C.navy, glasses: 1, seed: 570 }];
  const sayP = (t, a, b) => seg(t, a, a + 0.25) * (1 - seg(t, b, b + 0.15));
  const walkX = (t, a, b, x0, x1) => lerp(x0, x1, seg(t, a, b));
  const moving = (t, a, b) => t > a && t < b;
  const camScreen = (wx, wy, cx, cy, s) => [(wx - cx) * s + W / 2, (wy - cy) * s + H / 2];

  // ================= 夜市布景（A 和 E 共用） =================
  const GY = 980, TAG = { x: 470, y: 580 }, NEXT = 2250, ANC_E = { x: 1150, s: 0.95 }, MEX = 1700;
  function marketBack(t) {
    card(C.B);
    moon(1760, 130, 50);
    for (let k = 0; k < 5; k++) lights(-260 + k * 700, 100 + (k % 2) * 18, 440 + k * 700, 118 - (k % 2) * 18, 38, 7, t);
    stall(560, GY, 820, { label: '潮T 清仓', col: C.red, labelX: -230, table: false });
    tshirt(380, 360, 0.9, C.P);
    stall(NEXT, GY, 320, { n: 3, col: C.navy, h: 600, table: true });
    tshirt(NEXT, 420, 0.9, C.P);
  }
  function counter() {
    shape(box(180, GY - 200, 760, 34, 6), C.wood, { w: 5 });
    shape(box(200, GY - 166, 720, 166, 4), C.woodL, { w: 5, shade: [0, -14] });
    // 柜台上叠着的 T 恤
    for (const [x, col] of [[300, C.Y], [600, C.G], [820, C.P]]) for (let i = 0; i < 3; i++) shape(box(x - 60, GY - 222 - i * 18, 120, 20, 6), i % 2 ? C.white : col, { w: 3.5, off: 0 });
  }
  function tagA(t) {
    const st = seg(t, 3.3, 3.55), sk = seg(t, 3.62, 3.82);
    priceTag(TAG.x, TAG.y, 190, 160, 0.12 + Math.sin(t * 2.2) * 0.02, () => {
      popNum('200', 0, 56, 62, { color: C.ink, line: C.ink, hi: false, drop: false, ox: 0.7 });
      if (st > 0) strike(-74, 30, 74, 18, st, { w: 6, gap: 14 });
      if (sk > 0) at(56, 64, E.back(sk, 2.5), -0.2, () => { shape(circ(0, 0, 46), C.Y, { w: 4.5, off: 0 }); popNum('100', 0, 15, 32, { color: C.red, hi: false, drop: false }); });
    }, { len: 60, sx: -20, bg: C.P, hole: 10 });
  }

  // ---------- 镜头 A（0–9.2）：这件 200 → 你喊 100 → 行行行 → 拎着袋子得意 → 隔壁 50 ----------
  let HEADA = [W / 2, H / 2];
  function shotA(t) {
    const z = E.io(seg(t, 0.8, 2.6)), f = E.io(seg(t, 4.4, 6.5)), w = E.io(seg(t, 6.5, 7.1)), pz = E.out(seg(t, 7.5, 7.8));
    let cx = lerp(470, 760, z) + 260 * f, cy = lerp(560, 600, z), s = Math.exp(lerp(Math.log(2.5), 0, z));
    cx = lerp(cx, 1860, w); cx = lerp(cx, 1800, pz); cy = lerp(cy, 640, pz); s = lerp(s, 1.12, pz);
    const sh = shakeAt(t, 7.25, 6);
    camera(cx, cy, s, () => {
      marketBack(t);
      tagA(t);
      // 摊主
      const vSay = t > 1.55 && t < 2.6, vOk = t > 3.1 && t < 4.4, vWin = t >= 4.4;
      drawKid(700, 900, 0.95, { ...VEN, t, eyes: vOk ? 'closed' : vWin ? 'happy' : 'dot', mouth: vSay ? 'open' : vOk ? 'wave' : vWin ? 'smug' : 'smile', brow: vOk ? 0.5 : 0, look: vSay ? [-0.8, -0.2] : [0.8, 0], armL: vSay ? lerp(0.3, 2.0, E.out(seg(t, 1.55, 1.75))) : 0.3, armR: vOk ? 2.2 + Math.sin(t * 18) * 0.25 : vWin ? 1.2 + Math.sin(t * 9) * 0.3 : 0.3 });
      counter();
      // 隔壁的 50（7.2 拍上去）
      const k50 = seg(t, 7.2, 7.42);
      if (k50 > 0) starburst(NEXT, 700, 112, C.Y, { seed: 9, rot: -0.1, k: lerp(1.7, 1, E.back(k50, 2.4)), fn: () => popNum('50', 0, 40, 100, { color: C.red }) });
      // 你：先面朝摊主，4.1 转身往右走，7.4 停住
      const walking = moving(t, 4.3, 7.4), x = t < 4.3 ? 1150 : walkX(t, 4.3, 7.4, 1150, 1739);
      const deal = t > 3.2 && t < 4.2, frozen = t > 7.5;
      const me = drawKid(x, 960, 1.0, { ...ME, t, flip: t < 4.1 ? -1 : 1,
        eyes: frozen ? 'wide' : deal || (t >= 4.2) ? 'happy' : 'dot', mouth: frozen ? 'wave' : t > 2.1 && t < 3.2 ? 'open' : deal ? 'grin' : t >= 4.2 ? 'smug' : 'flat',
        brow: frozen ? -0.6 : t > 2.1 && t < 3.2 ? 0.6 : -0.2, look: frozen ? [1, 0] : t < 4.1 ? [1, -0.5] : [1, 0], sweat: frozen ? 1 : 0,
        armL: t > 2.1 && t < 3.2 ? lerp(0.3, 2.5, E.out(seg(t, 2.1, 2.3))) : 0.3, armR: walking ? 0.5 + Math.sin(t * 14) * 0.15 : 0.45,
        legs: walking ? t * 14 : 0, hop: walking ? Math.abs(Math.sin(t * 14)) * 8 : frozen ? 10 * Math.max(0, 1 - (t - 7.5) / 0.15) : 0, bag: t >= 4.0 ? 'R' : 0, bagCol: C.Y });
      HEADA = camScreen(me.head[0], me.head[1], cx, cy, s);
      // 惊：头上两道感叹号
      if (frozen) { const q = E.back(seg(t, 7.5, 7.7), 2.4); at(me.top[0] + 40, me.top[1] - 10, q, 0.15, () => popNum('!!', 0, 0, 90, { color: C.red })); }
      // 气泡
      say('这件 200！', 900, 470, sayP(t, 1.6, 2.6), { size: 44, tx: -120, ty: 100 });
      say('100，卖不卖？', 1270, 440, sayP(t, 2.15, 3.3), { size: 44, tx: -40, ty: 110, rot: 0.03 });
      say('行行行…', 880, 470, sayP(t, 3.2, 4.4), { size: 44, tx: -110, ty: 100 });
      thought(x - 30, 470, 400, 210, sayP(t, 4.5, 6.6), x - 10, 690, () => {
        ptxt('我心里有数', -40, -26, { size: 40, t: 99, t0: 0 });
        popNum('100', -40, 70, 74, { color: C.red });
        check(120, 0, 1.6, seg(t, 5.0, 5.3));
      });
    }, sh, 0);
  }

  // ---------- 镜头 B（9.2–16.4）：脑子里：尺子 0–200，摊主的锚砸在 200，绳子拴着你；往下砍到 100 就停 ----------
  const RB = { x0: 240, x1: 1440, y: 640 };
  function shotB(t) {
    card(C.Y);
    const pull = E.io(seg(t, 13.1, 13.8));
    camera(lerp(840, 840, pull), lerp(540, 520, pull), lerp(1.02, 0.95, pull), () => {
      sparkle(1560, 150, 0.8, C.white, 0.3); sparkle(170, 300, 0.7, C.O); sparkle(240, 860, 0.6, C.P, 0.5);
      const X = ruler(RB.x0, RB.x1, RB.y, 0, 200, { step: 10, major: 50 });
      // 你走的位置（数值）
      const v = t < 10.25 ? 186 : lerp(186, 100, E.io(seg(t, 10.25, 12.3)));
      // 脚印
      for (let u = 182; u > v + 6; u -= 9) shape(oval(X(u), 616 + (Math.round(u / 9) % 2 ? -6 : 6), 11, 6), C.ink, { stroke: false, off: 0, alpha: 0.45 });
      // 隔壁的 50（13.6 出现）
      const k50 = seg(t, 13.6, 13.85);
      if (k50 > 0) {
        starburst(X(50), 470, 92, C.P, { seed: 4, rot: 0.1, k: E.back(k50, 2.4), fn: () => popNum('50', 0, 34, 84, { color: C.white }) });
        layer(k50, () => { note('隔壁', X(50), 360, { size: 34, weight: 900 }); stroke([[X(50), 560], [X(50), 636]], 1, { w: 5, dash: [8, 12] }); });
      }
      // 锚：9.5 从天上掉下来，9.85 砸在 200
      const fall = E.in(seg(t, 9.45, 9.85)), ay = lerp(-420, 450, fall) + shakeAt(t, 9.85, 8, 9);
      if (fall < 1 && fall > 0) for (let i = 0; i < 3; i++) line([[X(200) - 60 + i * 60, ay - 260], [X(200) - 60 + i * 60, ay - 150]], { w: 5, alpha: 0.6 });
      const ring = anchorIcon(X(200), ay, 0.95);
      at(X(200) + 108, ay + 40, 1, 0.12, () => { shape(box(-62, -36, 124, 72, 10), C.white, { w: 5, off: 0 }); popNum('200', 0, 24, 46, { color: C.red, hi: false }); });
      puff(X(200) - 110, 636, seg(t, 9.85, 10.4), -1); puff(X(200) + 110, 636, seg(t, 9.85, 10.4), 1);
      const lab = seg(t, 13.2, 13.45);
      if (lab > 0) { layer(lab, () => line([[X(200), 340], [ring[0], ring[1] - 10]], { w: 4, dash: [4, 12] })); at(X(200), 300, E.back(lab, 2.4), 0.05, () => { shape(box(-150, -50, 300, 100, 10), C.white, { w: 6 }); ptxt('摊主喊的', 0, 18, { size: 48, t: 99, t0: 0 }); }); }
      // 你
      const walking = moving(t, 10.25, 12.3), yank = shakeAt(t, 12.3, 12, 8), proud = t > 14.0;
      const kx = X(v) + yank, startle = t > 9.85 && t < 10.25;
      drawKid(kx, 630, 0.78, { ...ME, t, flip: -1, lean: walking ? 0.12 : proud ? -0.05 : 0.04, eyes: startle ? 'wide' : proud ? 'happy' : t > 12.3 ? 'dot' : 'dot', mouth: startle ? 'o' : proud ? 'grin' : t > 12.3 ? 'flat' : 'flat',
        brow: walking ? 0.3 : 0, look: startle ? [1, -0.3] : [-1, 0], armL: walking ? 0.6 + Math.sin(t * 12) * 0.4 : proud ? 2.6 : 0.4, armR: walking ? 0.6 - Math.sin(t * 12) * 0.4 : 0.4,
        legs: walking ? t * 12 : 0, hop: walking ? Math.abs(Math.sin(t * 12)) * 6 : startle ? 14 * Math.sin(Math.PI * seg(t, 9.85, 10.15)) : 0, sweat: t > 12.3 && t < 14 ? 1 : 0 });
      if (t > 9.85) { const waist = [kx + 34, 630 - 116 * 0.78], d = ring[0] - waist[0]; rope(waist, ring, t > 12.3 ? 6 : lerp(130, 10, seg(d, 120, 640))); }
      // 你脑子里的声音
      say('太贵了', kx - 140, 330, sayP(t, 10.35, 11.1), { size: 42, tx: 60, ty: 90 });
      say('再低点…', kx - 150, 330, sayP(t, 11.2, 12.05), { size: 42, tx: 60, ty: 90, rot: 0.03 });
      say('差不多了吧', kx - 40, 250, sayP(t, 12.35, 13.7), { size: 42, tx: 20, ty: 110 });
      const pp = sayP(t, 14.0, 16.6);
      if (pp > 0) { say('我自己砍的价！', kx + 10, 240, pp, { size: 42, tx: -40, ty: 120 }); layer(seg(pp, 0, 0.3), () => check(kx + 10 + 215, 205, 1.4, seg(t, 14.3, 14.6))); }
    });
  }

  // ---------- 镜头 C（16.4–29.3）：1974 转盘慢慢停在 10 / 65 → 横幅出题 → 两人想一想 → 举牌 25% / 45% → 转盘缩成锚，答案被绳子拽着 ----------
  // 用户 11-18 说这段太快，整段放慢 5 秒：转盘转得更久、出题后留时间想、先念出 25%/45% 再变成锚
  const DA = Math.PI * 2 / 20, WDUR = 2.4;
  function wAng(t, target, t1, dur = WDUR, total = 6 * Math.PI) {
    const t0 = t1 - dur;
    if (t >= t1) return target;
    if (t >= t0) return target + total * Math.pow(1 - (t - t0) / dur, 3);
    return target + total + (t0 - t) * 3 * total / dur;
  }
  const RC = { x0: 170, x1: 1530, y: 720 }, XC = v => lerp(RC.x0, RC.x1, v / 100);
  const CT = { banner: 20.6, think: 21.1, thinkEnd: 22.8, up: 22.9, write: 23.05, morph: 25.6, hop: 25.95, anc: 26.0, ropeT: 26.45, strain: 26.7 };
  const WH = [{ x: 330, y: 500, stop: 19.6, tgt: -2 * DA, lab: '10', v: 10, guess: '25%', g: 25, gcol: C.B, kid: 640 }, { x: 1100, y: 500, stop: 20.1, tgt: -13 * DA, lab: '65', v: 65, guess: '45%', g: 45, gcol: C.O, kid: 1410 }];
  function shotC(t) {
    card(C.P);
    const morph = E.in(seg(t, CT.morph, CT.morph + 0.45)), hopP = seg(t, CT.hop, CT.hop + 0.5), rl = E.out(seg(t, CT.morph + 0.1, CT.morph + 0.45));
    layer(1 - seg(t, CT.morph - 0.1, CT.morph + 0.2), () => line([[866, 250], [866, 780]], { w: 6, dash: [26, 22] }));
    // 尺子从左往右画出来
    if (rl > 0) { ctx.save(); ctx.beginPath(); ctx.rect(RC.x0 - 60, 0, (RC.x1 - RC.x0 + 120) * rl, H); ctx.clip(); ruler(RC.x0, RC.x1, RC.y, 0, 100, { step: 5, major: 25 }); ctx.restore(); }
    WH.forEach((w, i) => {
      const ang = wAng(t, w.tgt, w.stop), stopped = t >= w.stop;
      const pr = stopped ? 0 : -0.32 * Math.pow((((-ang) / DA) % 1 + 1) % 1, 2);
      // 转盘：变形时缩小、飞到锚的位置
      const k = 1 - morph, wx = lerp(w.x, XC(w.v), morph), wy = lerp(w.y, 650, morph);
      if (k > 0.02) at(wx, wy, k, 0, () => wheel(0, 0, 165, ang, { hl: j => stopped && j === (i ? 13 : 2), pRot: pr, t }));
      // 转出来的数（写在指针上方），变形时跟着飞到锚旁边
      const wp = seg(t, w.stop, w.stop + 0.35);
      if (wp > 0) { const lx = lerp(w.x, XC(w.v) + (i ? 125 : -115), morph), ly = lerp(300, 600, morph); popNum(w.lab, lx, ly, lerp(76, 62, morph), { color: C.Y, p: wp }); }
      // 锚（转盘变的）
      const ap = seg(t, CT.anc, CT.anc + 0.25);
      let ring = null;
      if (ap > 0) at(XC(w.v), RC.y - 4, E.back(ap, 2.6), 0, () => { ring = anchorIcon(0, -132, 0.7); ring = [XC(w.v), RC.y - 4 + (ring[1])]; });
      // 举牌的人：先站在转盘旁边看它转 → 抬头看题、托着下巴想 → 举牌 → 跳到尺子上（猜的那个数的位置）
      const hx = lerp(w.kid, XC(w.g), E.io(hopP)), hy = lerp(840, 710, E.io(hopP)) - Math.sin(Math.PI * hopP) * 120, hs = lerp(0.82, 0.7, E.io(hopP));
      const up = E.back(seg(t, CT.up + i * 0.15, CT.up + 0.25 + i * 0.15), 1.8), strain = t > CT.strain;
      const thinking = t > CT.think + i * 0.2 && t < CT.thinkEnd;
      const lean = strain ? 0.16 + Math.sin(t * 9 + i) * 0.025 : 0, fl = i ? -1 : 1;
      const sxp = hx, syp = hy - 384 * hs;
      if (up > 0.02) sign(sxp, lerp(hy - 200 * hs, syp, up), 270, 160, (i ? -0.04 : 0.03) + lean * fl * 0.15, () => popNum(w.guess, 0, 58, 110, { color: w.gcol, p: seg(t, CT.write + i * 0.3, CT.write + 0.45 + i * 0.3) }), { stick: false, s: hs / 0.82 * lerp(1, 0.72, E.io(hopP)) });
      const kid = drawKid(hx, hy, hs, { ...GUESS[i], t, flip: strain ? fl : 1, lean, eyes: strain ? 'dot' : thinking ? 'dot' : 'dot', mouth: strain ? 'flat' : thinking ? 'flat' : i ? 'grin' : 'smile', brow: strain ? 0.4 : thinking ? -0.4 : 0,
        look: t < CT.banner ? [-0.9, 0.1] : thinking ? [i ? -0.5 : 0.5, -0.8] : [0, -0.6],
        armL: lerp(0.25, 2.85, up), armR: thinking ? -2.13 : lerp(0.25, 2.85, up), legs: strain ? t * 10 + i : 0, sweat: strain ? 1 : 0 });
      // 想的时候头上冒问号
      const qp = seg(t, CT.think + 0.2 + i * 0.2, CT.think + 0.4 + i * 0.2) * (1 - seg(t, CT.thinkEnd - 0.15, CT.thinkEnd));
      if (qp > 0) at(kid.top[0] + 46, kid.top[1] - 6 + Math.sin(t * 5 + i) * 5, E.back(qp, 2.4), 0.12, () => popNum('?', 0, 0, 84, { color: C.white }));
      if (t > CT.ropeT && ring) { const waist = [hx - fl * 34 * hs / 0.78, hy - 116 * hs], rp = E.out(seg(t, CT.ropeT, CT.ropeT + 0.25)); rope(waist, [lerp(waist[0], ring[0], rp), lerp(waist[1], ring[1], rp)], 4); }
    });
    roundStamp('1974', 170, 230, 0.7, -0.15, seg(t, 17.3, 17.5));
    // 题目横幅掉下来
    const bp = E.back(seg(t, CT.banner, CT.banner + 0.35), 1.6);
    if (bp > 0) banner(866, lerp(-160, 104, bp), 980, 100, -0.01, () => ptxt('非洲国家占联合国百分之几？', 0, 20, { size: 50, t: 99, t0: 0 }));
  }

  // 下面两段的镜头内部时间沿用原来的（24.3 起），整片里往后挪了 SL = 5 秒，调用时减掉
  const SL = 5;
  // ---------- 镜头 D（原 24.3–31.8，现 29.3–36.8）：1987 同一套房，挂价低/高两个锚拽着两个经纪人 → 问依据：地段、面积…没人提挂价 ----------
  const RD = { x0: 200, x1: 1500, y: 720 }, XD = u => lerp(RD.x0, RD.x1, u);
  function shotD(t) {
    card(C.G);
    house(866, 270, 0.75);
    at(1150, 205, 1, 0.08, () => { shape(box(-104, -36, 208, 72, 10), C.Y, { w: 5 }); ptxt('同一套房', 0, 16, { size: 40, t: 99, t0: 0 }); });
    roundStamp('1987', 170, 230, 0.7, -0.15, seg(t, 24.6, 24.8));
    ruler(RD.x0, RD.x1, RD.y, 0, 100, { step: 5, major: 25, nums: false });
    note('估得低', RD.x0 + 10, RD.y + 64, { size: 32, weight: 900, align: 'left' });
    note('估得高', RD.x1 - 10, RD.y + 64, { size: 32, weight: 900, align: 'right' });
    const ANC = [{ u: 0.2, lab: '挂牌价·低', drop: 25.0 }, { u: 0.88, lab: '挂牌价·高', drop: 25.2 }], AG = [0.34, 0.7];
    const rings = ANC.map((a, i) => {
      const f = E.in(seg(t, a.drop - 0.35, a.drop)), ay = lerp(-300, RD.y - 4 - 132, f) + shakeAt(t, a.drop, 7, 9);
      const r = anchorIcon(XD(a.u), ay, 0.7);
      if (t > a.drop) { puff(XD(a.u) - 80, RD.y - 4, seg(t, a.drop, a.drop + 0.5), -1); puff(XD(a.u) + 80, RD.y - 4, seg(t, a.drop, a.drop + 0.5), 1); }
      const lp = seg(t, a.drop + 0.1, a.drop + 0.3);
      if (lp > 0) at(XD(a.u), 482, E.back(lp, 2.4), i ? 0.05 : -0.05, () => { shape(box(-112, -36, 224, 72, 10), C.white, { w: 5 }); ptxt(a.lab, 0, 15, { size: 38, t: 99, t0: 0, color: i ? C.red : C.ink }); });
      return r;
    });
    // 经纪人
    const ask = t > 27.9, shrug = t > 30.6;
    AG.forEach((u, i) => {
      const ap = seg(t, 25.45 + i * 0.12, 25.7 + i * 0.12);
      if (ap <= 0) return;
      const x = XD(u), y = 710, s = 0.7 * E.back(ap, 2.2);
      const talking = (i === 0 && (t > 28.3 && t < 28.8 || t > 29.1 && t < 29.6)) || (i === 1 && (t > 28.7 && t < 29.2 || t > 29.5 && t < 30.0));
      const k = drawKid(x, y, s, { ...AGENT[i], t, eyes: shrug ? 'dot' : 'dot', mouth: shrug ? 'o' : talking ? 'open' : 'smile', brow: shrug ? -0.3 : 0, look: ask && !shrug ? [i ? -0.3 : 0.3, -0.8] : [0, 0],
        armL: shrug ? 1.5 : 0.3, armR: shrug ? 1.5 : ask ? 1.1 + Math.sin(t * 6 + i) * 0.1 : 0.6 });
      if (!shrug) clipboard(k.handR[0] + 6, k.handR[1] - 20, s / 0.7, -0.15);
      if (t > 25.75) { const waist = [x + (i ? 34 : -34) * s / 0.78, y - 116 * s], rp = E.out(seg(t, 25.75, 26.0)); rope(waist, [lerp(waist[0], rings[i][0], rp), lerp(waist[1], rings[i][1], rp)], 4); }
    });
    // 问：估价时你们看的是什么？
    const bp = E.back(seg(t, 27.9, 28.25), 1.6);
    if (bp > 0) banner(866, lerp(-160, 92, bp), 900, 96, 0.01, () => ptxt('估价时，你们看的是什么？', 0, 18, { size: 48, t: 99, t0: 0 }));
    say('地段！', 620, 380, sayP(t, 28.3, 29.0), { size: 44, tx: 10, ty: 90 });
    say('面积！', 1120, 380, sayP(t, 28.7, 29.4), { size: 44, tx: -10, ty: 90, rot: 0.03 });
    say('装修！', 620, 380, sayP(t, 29.1, 29.9), { size: 44, tx: 10, ty: 90, rot: 0.02 });
    say('楼层！', 1120, 380, sayP(t, 29.5, 30.1), { size: 44, tx: -10, ty: 90 });
    // 红笔圈住两个锚：挂牌价呢？
    ANC.forEach((a, i) => { const p = seg(t, 30.15 + i * 0.12, 30.45 + i * 0.12); if (p > 0) stroke(arcPts(XD(a.u), 600, 165, 190, -2.2, -2.2 + Math.PI * 2.15, 48), p, { w: 9, color: C.red }); });
    const qp = seg(t, 30.5, 30.7);
    if (qp > 0) at(876, 575, E.back(qp, 2.4), -0.04, () => ptxt('挂牌价呢？', 0, 0, { size: 54, color: C.red, sticker: 1, t: 99, t0: 0 }));
  }

  // ---------- 镜头 E（原 31.8–36.5，现 36.8–41.5）：回到夜市。“我？我是自己判断的。”镜头拉远：腰上的绳子连着摊主的锚 ----------
  function shotE(t) {
    const pb = E.io(seg(t, 33.6, 34.5));
    const cx = lerp(1720, 1250, pb), cy = lerp(700, 600, pb), s = lerp(2.0, 0.95, pb);
    camera(cx, cy, s, () => {
      marketBack(t);
      tagA(99);
      drawKid(700, 900, 0.95, { ...VEN, t, eyes: 'happy', mouth: 'smug', look: [1, 0], armL: 0.3, armR: 2.3 + Math.sin(t * 8) * 0.25 });
      counter();
      starburst(NEXT, 700, 112, C.Y, { seed: 9, rot: -0.1, fn: () => popNum('50', 0, 40, 100, { color: C.red }) });
      // 摊主的锚，挂着 200 的牌子
      const ring = anchorIcon(ANC_E.x, GY - 190 * ANC_E.s, ANC_E.s);
      at(ANC_E.x - 130, GY - 190, 1, -0.12, () => { shape(box(-62, -36, 124, 72, 10), C.white, { w: 5, off: 0 }); popNum('200', 0, 24, 46, { color: C.red, hi: false }); });
      const cp = seg(t, 34.25, 34.6);
      if (cp > 0) stroke(arcPts(ANC_E.x - 30, GY - 120, 210, 170, -2.4, -2.4 + Math.PI * 2.15, 48), cp, { w: 10, color: C.red });
      const me = drawKid(MEX, 960, 1.0, { ...ME, t, eyes: t < 34.0 ? 'happy' : 'happy', mouth: sayP(t, 32.5, 35.0) > 0.5 ? (Math.sin(t * 22) > 0 ? 'open' : 'smile') : 'smug',
        look: [0, 0], armL: 2.4 + Math.sin(t * 10) * 0.25, armR: 0.45, bag: 'R', bagCol: C.Y });
      rope([MEX - 40, 960 - 116], ring, 18);
      say('我？我是自己判断的。', 1490, 545, sayP(t, 32.5, 35.0), { size: 30, tx: 120, ty: 70 });
    });
  }

  const SH = [shotA, shotB, shotC, t => shotD(t - SL), t => shotE(t - SL)];
  const TR = [[9.2, 9.8, 'burst'], [16.4, 17.0, 'scribble', { col: C.P }], [29.3, 29.7, 'slap'], [36.8, 37.4, 'tear']];
  const CAPS = [
    ['这件 200，你砍到 100，赚了吗？', 0.0, 3.6, 'c1'],
    ['你觉得 100 是自己判断出来的', 3.75, 6.55, 'c2'],
    ['隔壁同款，只要 {{50}}', 6.8, 9.2, 'c3'],
    ['你是从 200 往下砍，砍到差不多就停', 9.85, 13.0, 'c4'],
    ['起点是他给的，你却以为是自己定的', 13.15, 16.4, 'c5'],
    ['1974 年，起点换成转盘随便转的数', 17.0, 20.4, 'c6'],
    ['然后问一道跟转盘无关的题', 20.6, 23.05, 'c6b'],
    ['转到 10 的猜 {{25%}}，转到 65 的猜 {{45%}}', 23.2, 26.25, 'c7a'],
    ['没人照抄转盘，答案却被拽了过去', 26.4, 29.3, 'c7'],
    ['同一套房，挂价高，经纪人就估得高', 29.6, 32.85, 'c8'],
    ['问他们靠什么估的，几乎没人提挂价', 33.0, 36.75, 'c9'],
    ['被拴住的人，都觉得是自己判断的', 37.55, 99, 'c10'],
  ];
  const A = (i, t) => () => shot(SH[i], t, BUF[0]), B = (i, t) => () => shot(SH[i], t, BUF[1]);
  SCENES.push({
    id: 'film', t0: -1, t1: 999,
    draw(t) {
      let i = 0; while (i < TR.length && t >= TR[i][1]) i++;
      if (i < TR.length && t >= TR[i][0]) {
        const o = { ...(TR[i][3] || {}) };
        if (TR[i][2] === 'burst') { A(i, t)(); o.x = HEADA[0]; o.y = HEADA[1]; }
        T[TR[i][2]](seg(t, TR[i][0], TR[i][1]), A(i, t), B(i + 1, t), o);
      }
      else put(shot(SH[i], t, BUF[0]));
    },
    caps(t) {
      for (const [s, a, b, id, o] of CAPS) cap(s, t, a, b, id, o);
      // 关注：一张爆炸贴拍在最后一个画面上
      const fp = seg(t, 39.6, 39.85);
      if (fp > 0) layer(seg(fp, 0, 0.3), () => starburst(1390, 260, 150, C.Y, { seed: 21, rot: 0.08, k: lerp(1.5, 1, E.back(fp, 2.2)), fn: () => {
        ptxt('关注我', 0, 0, { size: 60, t: 99, t0: 0, color: C.red, sticker: 1 });
        ptxt('看下一个心理实验', 0, 52, { size: 26, t: 99, t0: 0 });
      } }));
    },
  });

  // ---------- 音效事件 ----------
  const pan = x => clamp((x - 866) / 900, -0.8, 0.8);
  // A：夜市底（人声嘈杂 + 远处油锅 + 灯串电流）；吆喝；你还价；“行行行”；马克笔划掉 + 贴纸；塑料袋；脚步；甩镜头；50 拍上来；唱片刮停
  ev(0.0, 'market', { d: 9.4, g: 0.9 });
  ev(0.05, 'tagswing', { g: 0.5, pan: -0.3 });
  ev(1.6, 'vendor', { syl: 4, f: 1.0, g: 0.8, pan: 0.0 }); ev(1.6, 'bubble', { g: 0.45 });
  ev(2.15, 'buyer', { syl: 5, f: 1.25, g: 0.8, pan: 0.4 }); ev(2.15, 'bubble', { f: 1.15, g: 0.45, pan: 0.4 });
  ev(3.2, 'grumble', { g: 0.85, pan: 0.0 });
  ev(3.3, 'marker', { d: 0.25, g: 0.6, pan: -0.3 }); ev(3.43, 'marker', { d: 0.2, f: 1.1, g: 0.55, pan: -0.3 }); ev(3.62, 'sticker', { g: 0.8, pan: -0.3 });
  ev(3.25, 'register', { g: 0.5, pan: -0.1 });
  ev(4.0, 'bag', { g: 0.8, pan: 0.3 });
  for (let s = 4.35; s < 7.4; s += 0.225) ev(s, 'step', { g: 0.45, f: 0.95 + 0.1 * hash(s), pan: 0.2 });
  ev(4.5, 'thinkpop', { g: 0.55 }); ev(5.0, 'tick', { g: 0.7 });
  ev(6.45, 'whip', { d: 0.6, g: 0.75 });
  ev(7.2, 'slap', { g: 1.0, pan: 0.45 });
  ev(7.5, 'scratch', { g: 0.95 });
  // 转场：冲进脑袋
  ev(9.2, 'suck', { d: 0.6, g: 0.8 });
  // B：脑子里（低低的嗡 + 钟摆）；锚掉下来是下落哨音 + 金属砸地 + 铁链；脚步踩在尺子上是木头“嗒”；绳子绷直“嘣”
  ev(9.6, 'mindbed', { d: 6.9, g: 0.8 });
  ev(9.45, 'fallwhistle', { d: 0.4, g: 0.7, pan: 0.6 }); ev(9.85, 'clank', { g: 1.1, pan: 0.6 }); ev(9.9, 'chain', { d: 0.6, g: 0.6, pan: 0.6 });
  for (let s = 10.3; s < 12.3; s += 0.26) ev(s, 'rulerstep', { g: 0.55, f: 0.9 + 0.2 * hash(s * 3), pan: pan(lerp(1370, 840, (s - 10.3) / 2)) });
  ev(10.35, 'bubble', { g: 0.4, f: 0.9, pan: 0.1 }); ev(11.2, 'bubble', { g: 0.4, f: 1.0, pan: 0.0 });
  ev(11.5, 'creak', { d: 0.8, g: 0.6, pan: 0.3 });
  ev(12.3, 'twang', { g: 0.95, pan: 0.2 }); ev(12.35, 'bubble', { g: 0.4, f: 1.1, pan: -0.1 });
  ev(13.2, 'reveal', { g: 0.8, pan: 0.6 }); ev(13.6, 'boing', { g: 0.75, pan: -0.5 });
  ev(14.0, 'proud', { g: 0.7, pan: -0.1 }); ev(14.3, 'tick', { g: 0.6, pan: -0.1 });
  // 转场：马克笔涂满
  ev(16.4, 'scribble', { d: 0.6, g: 0.8 });
  // C：游戏节目底；两个转盘的棘轮咔咔减速（时长和画面同一公式）；停住叮；盖章；横幅落下；两人“嗯…”想；马克笔写数；转盘缩成锚“咻—当”；跳；绳子；使劲
  ev(16.6, 'showbed', { d: 12.9, g: 0.7 });
  ev(16.4, 'ratchet', { t1: WH[0].stop, wdur: WDUR, g: 0.7, pan: -0.5 }); ev(16.4, 'ratchet', { t1: WH[1].stop, wdur: WDUR, g: 0.6, f: 0.85, pan: 0.45 });
  ev(17.3, 'stamp', { g: 0.9, pan: -0.7 });
  ev(WH[0].stop, 'ding', { f: 1.0, g: 0.7, pan: -0.5 }); ev(WH[1].stop, 'ding', { f: 1.19, g: 0.7, pan: 0.45 });
  ev(WH[0].stop + 0.02, 'marker', { d: 0.3, g: 0.5, pan: -0.5 }); ev(WH[1].stop + 0.02, 'marker', { d: 0.3, g: 0.5, pan: 0.45 });
  ev(CT.banner, 'flap', { g: 0.8 });
  ev(CT.think + 0.15, 'hmm', { f: 1.0, g: 0.6, pan: -0.3 }); ev(CT.think + 0.45, 'hmm', { f: 0.85, g: 0.55, pan: 0.6 });
  ev(CT.think + 0.2, 'bubble', { g: 0.35, f: 0.85, pan: -0.3 }); ev(CT.think + 0.4, 'bubble', { g: 0.35, f: 0.95, pan: 0.6 });
  ev(CT.up, 'cloth', { g: 0.5, pan: -0.2 }); ev(CT.write, 'marker', { d: 0.45, g: 0.55, pan: -0.2 }); ev(CT.write + 0.3, 'marker', { d: 0.45, f: 1.1, g: 0.55, pan: 0.6 });
  ev(CT.morph, 'shrink', { d: 0.45, g: 0.7 }); ev(CT.anc, 'clank', { g: 0.8, f: 1.15, pan: -0.6 }); ev(CT.anc + 0.02, 'clank', { g: 0.75, f: 1.05, pan: 0.2 });
  ev(CT.hop, 'hop', { g: 0.6, pan: -0.3 }); ev(CT.hop + 0.05, 'hop', { g: 0.6, f: 1.1, pan: 0.0 });
  ev(CT.ropeT, 'ropetie', { g: 0.6, pan: -0.3 }); ev(CT.ropeT + 0.05, 'ropetie', { g: 0.6, pan: 0.1 });
  ev(CT.strain, 'strain', { d: 2.6, g: 0.6 }); ev(CT.strain + 0.1, 'creak', { d: 2.3, g: 0.45, pan: 0 });
  // D、E 两段的事件写的是原来的时间，evL 统一往后挪 SL 秒
  const evL = (t, n, o) => ev(t + SL, n, o);
  // 转场：新海报拍上来
  evL(24.3, 'slap', { g: 0.9 });
  // D：办公室底（空调 + 远处打印机）；盖章；两个锚砸地；经纪人冒出来；横幅；七嘴八舌数依据；红笔圈；疑问
  evL(24.5, 'officebed', { d: 7.5, g: 0.7 });
  evL(24.6, 'stamp', { g: 0.9, pan: -0.7 });
  evL(24.65, 'fallwhistle', { d: 0.35, g: 0.5, pan: -0.4 }); evL(25.0, 'clank', { g: 0.9, f: 1.1, pan: -0.4 }); evL(25.2, 'clank', { g: 0.9, f: 0.95, pan: 0.5 });
  evL(25.45, 'popup', { g: 0.6, pan: -0.15 }); evL(25.57, 'popup', { g: 0.6, f: 1.12, pan: 0.2 });
  evL(25.75, 'ropetie', { g: 0.5, pan: -0.3 }); evL(25.8, 'ropetie', { g: 0.5, pan: 0.3 });
  evL(26.1, 'marker', { d: 0.4, f: 1.3, g: 0.35, pan: -0.25 }); evL(26.5, 'marker', { d: 0.45, f: 1.2, g: 0.35, pan: 0.25 });
  evL(27.9, 'flap', { g: 0.8 });
  [[28.3, -0.5, 1.0], [28.7, 0.5, 1.2], [29.1, -0.5, 0.95], [29.5, 0.5, 1.15]].forEach(([s, p, f]) => { evL(s, 'agent', { syl: 2, f, g: 0.7, pan: p }); evL(s, 'bubble', { g: 0.35, f, pan: p }); });
  evL(30.15, 'circle', { d: 0.35, g: 0.6, pan: -0.4 }); evL(30.27, 'circle', { d: 0.35, g: 0.6, f: 1.1, pan: 0.5 });
  evL(30.5, 'huh', { g: 0.8 }); evL(30.65, 'shrugboing', { g: 0.6 });
  // 转场：撕页
  evL(31.8, 'tear', { d: 0.55, g: 0.9 });
  // E：夜市底；“我？我是自己判断的”；镜头拉远是绳子“吱—”+ 铁链；摊主偷笑；关注贴纸；收尾
  evL(32.2, 'market', { d: 4.6, g: 0.85 });
  evL(32.5, 'buyer', { syl: 8, f: 1.2, g: 0.75, pan: 0.2 }); evL(32.5, 'bubble', { g: 0.4 });
  evL(33.6, 'pullback', { d: 0.9, g: 0.6 }); evL(33.95, 'chain', { d: 0.7, g: 0.6, pan: -0.2 }); evL(34.0, 'creak', { d: 0.7, g: 0.5, pan: 0.0 });
  evL(34.2, 'chuckle', { g: 0.7, pan: -0.4 });
  evL(34.6, 'slap', { g: 0.85, pan: 0.5 }); evL(34.62, 'sparkle', { g: 0.5, pan: 0.5 });
  evL(35.9, 'button', { g: 0.8 });
})();
