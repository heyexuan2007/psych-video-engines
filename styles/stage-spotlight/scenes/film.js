// 《全场都在看你吗？》整片：6 个镜头 + 5 种和“灯”有关的转场 + 字幕 + 音效事件
// 前 18 秒：Gilovich 等 2000 年的尴尬 T 恤实验（他猜 46%，实际 23%；换成体面的 T 恤也一样高估）；
// 后 17 秒：半夜回放说错的话、剪坏的刘海、拉远——每个人都站在自己的追光里。
// 不配音：信息全靠屏幕上的字。字都在抖音安全区里（x 134–1594，y 119–929）。
(() => {
  const GY = 800, ME = { hair: 5, shirt: C.pink, print: 'singer', seed: 685 };
  const NIGHT = '#2a2d44', LIT_ROOM = '#d9cfbf';
  const blink = (t, k) => { const ph = (t * 0.41 + hash(k * 3.7)) % 1; return ph < 0.05 ? 0.12 : 1; };

  // ---------- 镜头 A（0–8.4）：追光下的粉 T 恤，黑暗里一双双眼睛 → 你猜几个人注意到 → 定格盖章 ----------
  const FZ = 5.6;
  const DARK = [[200, 0, 520], [420, 3, 527], [1310, 1, 534], [1530, 4, 541]];
  const EYES = [[90, 470, 0.7], [640, 380, 0.6], [1120, 400, 0.6], [1700, 520, 0.75], [300, 300, 0.5], [1450, 300, 0.5], [760, 560, 0.5], [1000, 610, 0.5],
    [520, 250, 0.45], [1240, 240, 0.45], [150, 640, 0.65], [1640, 660, 0.7], [880, 300, 0.4], [1560, 400, 0.55], [380, 520, 0.6], [1800, 300, 0.5]];
  function shotA(t) {
    const ta = t < FZ ? t : t < FZ + 0.9 ? FZ : t - 0.9;
    const z = E.io(seg(t, 3.1, 5.4)), sh = shakeAt(t, 6.12, 9);
    camera(lerp(866, 866, z), lerp(540, 575, z), lerp(1, 1.13, z), () => {
      stage();
      DARK.forEach(([x, h, sd]) => drawKid(x, 790, 0.82, { t: ta, hair: h, shirt: C.gray, seed: sd, eyes: 'dot' }));
      spot(866, GY, { w: 175 });
      const cover = ta > 1.5 && ta < 3.1, dart = Math.floor(ta / 0.42) % 2;
      drawKid(866, GY, 1.05, { ...ME, t: ta, eyes: 'wide', mouth: ta < 0.8 ? 'o' : 'wave', brow: -0.8, blush: seg(ta, 0.5, 1.5), sweat: seg(ta, 0.8, 2.0),
        look: ta < 0.8 ? [0, 0] : dart ? [-1, 0] : [1, 0], armL: cover ? -0.62 : 0.35, armR: cover ? -0.62 : 0.35, shake: ta > 3.1 ? 1.4 : 0 });
      for (let i = 0; i < 9; i++) { const x = 40 + i * 230 + (i % 2) * 40, y = 1060 + (i % 2) * 30; shape(circ(x, y - 70, 74), '#1a1c26', { stroke: false }); shape(box(x - 110, y - 10, 220, 120, 50), '#1a1c26', { stroke: false }); }
      over(() => {
        DARK.forEach(([x], i) => eyePair(x, 790 - 0.82 * 262, 0.82, seg(t, 0.15 + i * 0.12, 0.35 + i * 0.12) * blink(ta, i), [x < 866 ? 1 : -1, 0]));
        EYES.forEach(([x, y, s], i) => { const t0 = 0.3 + i * 0.27; eyePair(x, y, s, seg(t, t0, t0 + 0.15) * blink(ta, i + 9), [x < 866 ? 1 : -1, 0.3]); });
        const q = seg(t, 3.3, 3.6) * (1 - seg(t, 5.45, 5.6));
        if (q > 0) at(1035, 400 + Math.sin(ta * 4) * 6, E.back(q, 2.2), 0.12, () => txt('？', 0, 0, { size: 170, font: F.serif, weight: 900, color: C.warm, glow: 1, t: 99, t0: 0, cps: 0 }));
      });
    }, -94, sh);
    over(() => {
      txt('全场都在看{{你}}？', 866, 205, { size: 128, font: F.serif, weight: 900, t, t0: -1, t1: 3.0, cps: 0, id: 'h1' });
      if (t >= FZ && t < FZ + 0.35) { ctx.save(); ctx.globalAlpha = (1 - seg(t, FZ, FZ + 0.35)) * 0.7; ctx.fillStyle = '#fff6e0'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
      const m = E.io(seg(t, 6.7, 7.3));
      stamp('2000 · 康奈尔大学', lerp(866, 400, m), lerp(250, 185, m), lerp(1, 0.6, m), -0.06, seg(t, 5.95, 6.15));
    });
  }

  // ---------- 教室布景（镜头 B、C 共用） ----------
  const CL = [{ x: 470, hair: 1, shirt: C.teal, act: 'phone', seed: 531 }, { x: 680, hair: 0, shirt: C.mustard, act: 'sleep', seed: 538 }, { x: 1060, hair: 3, shirt: C.olive, act: 'yawn', seed: 545 }, { x: 1270, hair: 6, shirt: C.blue, act: 'mirror', seed: 552 }];
  function classroom(t, o = {}) {
    stage({ wall: '#6a5a4a' });
    blackboard(250, 790, 0.95, () => txt('自习', 0, -300, { size: 70, font: F.serif, weight: 900, color: '#e8efe6', t: 99, t0: 0, cps: 0, shadow: 0 }));
    for (const c of CL) {
      const yawnUp = Math.max(0, Math.sin(t * 1.6 + 1)) ;
      const q = c.act === 'phone' ? { eyes: 'dot', mouth: 'smile', look: [0.3, 1], armR: 0.95, phone: 1, phoneOn: 1 }
        : c.act === 'sleep' ? { eyes: 'closed', mouth: 'flat', look: [0, 1], armL: 0.7, armR: 0.7, lean: 0.12 + Math.sin(t * 1.7) * 0.02 }
        : c.act === 'yawn' ? { eyes: 'closed', mouth: yawnUp > 0.3 ? 'yawn' : 'flat', armL: lerp(0.9, 2.95, yawnUp), armR: lerp(0.9, 2.95, yawnUp) }
        : { eyes: 'dot', mouth: 'smile', look: [-1, -0.5], armR: 2.2, blush: 0.6 };
      const r = drawKid(c.x, 800, 0.78, { hair: c.hair, shirt: c.shirt, seed: c.seed, t, ...q });
      if (c.act === 'mirror') mirror(r.handR[0] - 30, r.handR[1] - 40, 0.9);
      c.head = r.head;
    }
    if (o.me) o.me();
    [470, 680, 866, 1060, 1270].forEach(x => desk(x, 830, 0.86));
    over(() => { const c = CL[1]; if (o.zzz) zzz(c.head[0] + 50, c.head[1] - 40, t, 0.9); });
  }

  // ---------- 镜头 B（8.4–15.4）：大幕拉开，教室里一片黑，都在“看”他 → 开灯：谁都没在看 ----------
  const LU = 11.8;
  function shotB(t) {
    const lu = E.io(seg(t, LU, LU + 0.45));
    ambient(mixc(NIGHT, LIT_ROOM, lu));
    classroom(t, { zzz: lu > 0.5, me: () => {
      spot(866, 840, { w: 130, i: lerp(1, 0.55, lu), beam: lerp(1, 0.45, lu) });
      const sur = t > LU + 0.5;
      drawKid(866, 800, 0.78, { ...ME, t, eyes: 'wide', mouth: sur ? 'o' : 'wave', brow: sur ? 0.2 : -0.7, sweat: 1, blush: 1 - lu, look: sur ? (Math.floor(t / 0.45) % 2 ? [-1, 0] : [1, 0]) : [0, 0], armL: 0.4, armR: 0.4 });
    } });
    over(() => {
      CL.forEach((c, i) => eyePair(c.head[0], c.head[1], 0.78, seg(t, 8.9 + i * 0.15, 9.1 + i * 0.15) * (1 - lu) * blink(t, i + 30), [c.x < 866 ? 1 : -1, 0]));
      const bp = seg(t, 9.1, 9.4) * (1 - seg(t, LU + 0.25, LU + 0.45));
      if (bp > 0) { thought(1120, 380, 132, 82, bp, [[990, 470, 15], [952, 500, 9]]); if (bp > 0.6) { txt('46%', 1120, 405, { size: 74, font: F.lat, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0 }); txt('我猜', 1120, 340, { size: 30, color: C.grayD, t: 99, t0: 0, cps: 0, shadow: 0 }); } }
      const r1 = seg(t, LU + 0.35, LU + 0.6);
      if (r1 > 0) layer(r1, () => { txt('46%', 560, 230, { size: 120, font: F.lat, weight: 900, color: C.gray, t: 99, t0: 0, cps: 0, spacing: 0 }); txt('他猜的', 560, 292, { size: 40, t: 99, t0: 0, cps: 0 }); });
      line([[440, 205], [680, 175]], { w: 12, color: C.red, alpha: seg(t, LU + 0.6, LU + 0.75) });
      bigNum('23%', 1000, 290, t, LU + 0.85);
      if (t > LU + 1.2) txt('真正注意到的', 1000, 352, { size: 40, t, t0: LU + 1.2, cps: 0.03 });
      note('Gilovich, Medvec & Savitsky, 2000 · 穿者估计约 46% 的同学记得 T 恤上是谁，实际约 23%', 150, 950, { t, t0: LU + 1.3 });
    });
  }

  // ---------- 镜头 C（15.4–18.9）：换一件体面的，挺胸进来，还是没人抬头 ----------
  function shotC(t) {
    ambient(LIT_ROOM);
    const w = E.io(seg(t, 15.4, 17.0)), x = lerp(1640, 866, w), walking = w > 0 && w < 1, stop = t > 17.15, look = stop ? (Math.floor(t / 0.45) % 2 ? [-1, 0] : [1, 0]) : [0, 0];
    classroom(t, { zzz: true, me: () => {} });
    spot(x, 900, { w: 150, i: 0.7, beam: 0.5 });
    drawKid(x, 900, 0.9, { hair: 5, shirt: C.navy, print: 'star', seed: 685, t, eyes: stop ? 'dot' : 'happy', mouth: t > 17.6 ? 'flat' : 'grin', look, sweat: seg(t, 17.6, 18.0), lean: stop ? 0 : -0.05, hop: walking ? Math.abs(Math.sin(t * 8)) * 8 : 0, legs: walking ? t * 15 : 0, armL: 0.42, armR: 0.42, flip: walking ? -1 : 1 });
    over(() => {
      const sp = seg(t, 16.0, 16.3) * (1 - seg(t, 17.3, 17.5));
      if (sp > 0) for (const [dx, dy, k] of [[-120, -330, 1], [110, -300, 0.8], [140, -190, 0.7]]) at(x + dx, 900 + dy, k * E.back(sp, 2) * (0.7 + 0.3 * Math.sin(t * 10 + dx)), 0, () => shape(poly([[0, -22], [6, -6], [22, 0], [6, 6], [0, 22], [-6, 6], [-22, 0], [-6, -6]]), C.warm, { w: 3 }));
      note('原实验也换过印着名人的“体面”T 恤：穿的人同样高估了别人的注意', 150, 950, { t, t0: 15.9 });
    });
  }

  // ---------- 镜头 D（18.9–25.8）：半夜，追光打在床上；脑子里一遍遍回放说错的话 → 对面床的人睡得正香 ----------
  const KB = [560, 830], OB = [1420, 830];
  function shotD(t) {
    ambient('#232842');
    const pan = E.io(seg(t, 22.85, 23.55));
    camera(lerp(866, 1250, pan), 540, 1, () => {
      stage({ wall: '#1b2238' });
      windowMoon(980, 300, 0.8);
      spot(KB[0], KB[1], { w: 290, h: 260, i: 1 - 0.35 * pan });
      bed(KB[0], KB[1], 1, { eyes: 'wide', mouth: 'wave', brow: -0.6, look: [0.6, -1], blanket: C.pink });
      const on = seg(t, 23.2, 23.3);
      spot(OB[0], OB[1], { w: 270, h: 240, i: on, seed: 7 });
      bed(OB[0], OB[1], 0.85, { hair: 3, eyes: 'closed', mouth: 'smile', look: [0, 0], brow: 0, blanket: C.teal, blush: 0.7 });
      over(() => {
        zzz(OB[0] - 120, OB[1] - 220, t, 1.1);
        const bp = seg(t, 19.5, 19.8);
        if (bp > 0) {
          thought(760, 300, 240, 128, bp, [[470, 520, 18], [520, 470, 12]]);
          if (bp > 0.6) {
            const cy = Math.max(0, t - 19.85), k = cy % 1.3, n = Math.floor(cy / 1.3);
            txt('“我是说……呃……”', 760, 290, { size: 44, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
            if (k > 0.55) at(760, 270, E.back(seg(k, 0.55, 0.7), 2.5), -0.08, () => { line([[-70, -50], [70, 50]], { w: 14, color: C.red }); line([[70, -50], [-70, 50]], { w: 14, color: C.red }); });
            at(760, 365, 1, 0, () => { for (const dx of [-22, 8]) shape(poly([[dx + 22, -16], [dx + 22, 16], [dx - 6, 0]]), C.grayD, { stroke: false }); });
            txt('第 ' + (n + 1) + ' 遍', 860, 372, { size: 26, color: C.grayD, t: 99, t0: 0, cps: 0, shadow: 0, align: 'left' });
          }
        }
      });
    }, -94);
  }

  // ---------- 镜头 E（25.8–29.9）：剪坏的刘海，戴着帽子走了一路；摘帽——路人谁也没抬头 ----------
  const HAT = 28.2;
  function shotE(t) {
    ambient('#77708a');
    stage();
    const w = E.io(seg(t, 25.9, 28.0)), x = lerp(300, 866, w), walking = w > 0 && w < 1, off = t > HAT;
    // 路人：低头看手机，从右往左走
    for (let i = 0; i < 3; i++) { const px = 1700 + i * 420 - (t - 25.8) * 300; if (px < -200 || px > 2200) continue; drawKid(px, 745, 0.72, { hair: [4, 1, 0][i], shirt: [C.mustard, C.teal, C.red][i], seed: 600 + i * 11, t, flip: -1, legs: t * 13 + i, eyes: 'dot', mouth: 'flat', look: [0.5, 1], armR: 1.0, phone: 1, phoneOn: 1 }); }
    spot(x, GY, { w: 165 });
    const cringe = t > HAT && t < HAT + 0.6, around = t >= HAT + 0.6 && t < 29.3, relief = t >= 29.3;
    const r = drawKid(x, GY, 1.0, { ...ME, t, badcut: true, hat: off ? null : C.red, legs: walking ? t * 15 : 0, hop: walking ? Math.abs(Math.sin(t * 7.5)) * 6 : 0,
      eyes: cringe ? 'squint' : relief ? 'dot' : 'wide', mouth: cringe ? 'wave' : relief ? 'smile' : around ? 'o' : 'wave', brow: relief ? 0 : -0.7, sweat: relief ? 0 : 1, blush: cringe ? 1 : 0,
      look: around ? (Math.floor(t / 0.35) % 2 ? [-1, 0] : [1, 0]) : walking ? (Math.floor(t / 0.5) % 2 ? [-1, 0] : [1, 0]) : [0, 0],
      armL: off ? lerp(2.9, 0.35, seg(t, HAT + 0.15, HAT + 0.5)) : 2.72, armR: off ? lerp(3.05, 0.35, seg(t, HAT + 0.15, HAT + 0.5)) : 2.72 });
    if (off) { const k = Math.max(0, (t - HAT) / 0.9), hx = r.head[0] + 150 * k, hy = r.head[1] - 40 - 600 * k + 600 * k * k; if (hy < 1300) at(hx, hy, 1, k * 5, () => { shape(() => { ctx.ellipse(0, 0, 76, 64, 0, Math.PI, Math.PI * 2); ctx.closePath(); }, C.red); shape(box(-80, -14, 160, 30, 12), mixc(C.red, '#000000', 0.2)); shape(circ(0, -66, 14), C.cream); }); }
  }

  // ---------- 镜头 F（29.6–35.3）：拉远，一束一束灯亮起来——每个人都站在自己的追光里 ----------
  const PF = [[-330, 6, C.teal, 'mirror'], [-10, 3, C.olive, 'shirt'], [300, 1, C.mustard, 'phone'], [866, 5, C.pink, 'me'], [1430, 4, C.blue, 'hair'], [1750, 0, C.red, 'phone'], [2070, 2, C.cream, 'sweat']];
  const ORDER = [2, 4, 1, 5, 0, 6];
  function shotF(t) {
    const z = E.io(seg(t, 29.95, 31.3)), z2 = E.io(seg(t, 32.9, 34.4)), happy = t > 33.0;
    camera(866, lerp(540, 520, z) + 40 * z2, lerp(1, 0.6, z) + 0.12 * z2, () => {
      stage();
      ambient('#1c1e2c');
      PF.forEach(([x, h, col, k], i) => {
        const me = k === 'me', on = me ? 1 : seg(t, 30.5 + ORDER.indexOf(i) * 0.16, 30.58 + ORDER.indexOf(i) * 0.16);
        spot(x, GY, { w: me ? 170 : 160, i: on * (me ? 1 : 0.95), seed: i + 2, tx: x + (i - 3) * 30 });
        const r = drawKid(x, GY, 1, me
          ? { ...ME, t, badcut: true, eyes: happy ? 'happy' : 'wide', mouth: happy ? 'grin' : 'o', brow: happy ? 0 : -0.4, sweat: happy ? 0 : 1, look: happy ? [0, 0] : (t > 31.2 ? (Math.floor(t / 0.5) % 2 ? [-1, 0] : [1, 0]) : [0, 0]), hop: happy ? Math.abs(Math.sin((t - 33) * 7)) * 18 * Math.exp(-(t - 33) * 1.5) : 0, armL: happy ? 0.9 : 0.35, armR: happy ? 0.9 : 0.35 }
          : { hair: h, shirt: col, seed: 560 + i * 9, t, eyes: k === 'sweat' ? 'wide' : 'dot', mouth: k === 'sweat' ? 'wave' : 'flat', brow: -0.5, sweat: k === 'sweat' ? 1 : 0,
              look: k === 'shirt' ? [0, 1] : k === 'phone' ? [0.6, 0.6] : k === 'hair' ? [0, -1] : [1, -0.4], armR: k === 'phone' ? 1.0 : k === 'mirror' ? 2.2 : k === 'hair' ? 2.8 + Math.sin(t * 6) * 0.08 : 0.3, armL: k === 'hair' ? 2.8 - Math.sin(t * 6) * 0.08 : k === 'shirt' ? 0.6 : 0.3, phone: k === 'phone', phoneOn: 1, lean: k === 'shirt' ? 0.08 : 0 });
        if (k === 'mirror') mirror(r.handR[0] - 30, r.handR[1] - 40, 1);
      });
    }, -94);
  }

  // ---------- 合成 ----------
  const SH = [shotA, shotB, shotC, shotD, shotE, shotF];
  const TR = [[8.0, 8.9, 'curtain'], [15.15, 15.7, 'sweep'], [18.65, 19.25, 'blackout'], [25.4, 26.05, 'iris', { x: 869, y: 640, bx: 330, by: 540 }], [29.55, 29.95, 'fade']];
  const CAPS = [
    ['穿了件丢人的 T 恤进教室，', 0.2, 2.9, 'c1'],
    ['你猜，有几个人[[注意到了]]？', 3.2, 5.55, 'c2'],
    ['这是 2000 年的一个{{真实验}}。', 6.0, 8.35, 'c3'],
    ['他猜：差不多[[一半人]]注意到了。', 8.85, 11.7, 'c4'],
    ['实际：只有 [[23%]] 的人注意到。', 11.95, 15.1, 'c5'],
    ['换成一件体面的，照样{{高估}}。', 15.7, 18.55, 'c6'],
    ['你半夜还在回放说错的那句话，', 19.35, 22.85, 'c7'],
    ['别人[[早就忘了]]。', 23.2, 25.35, 'c8'],
    ['剪坏的刘海捂了一天，[[没人多看一眼]]。', 26.15, 29.45, 'c9'],
    ['因为每个人，都站在[[自己的聚光灯]]下。', 29.85, 33.1, 'c10'],
    ['{{没空}}看你。', 33.2, 99, 'c11'],
  ];
  const A = (i, t) => () => shot(SH[i], t, BUF[0]), B = (i, t) => () => shot(SH[i], t, BUF[1]);
  SCENES.push({
    id: 'film', t0: -1, t1: 999,
    draw(t) {
      let i = 0; while (i < TR.length && t >= TR[i][1]) i++;
      if (i < TR.length && t >= TR[i][0]) T[TR[i][2]](seg(t, TR[i][0], TR[i][1]), A(i, t), B(i + 1, t), TR[i][3]);
      else put(shot(SH[i], t, BUF[0]));
      ctx = MAIN; MAIN.setTransform(1, 0, 0, 1, 0, 0);
      for (const [s, a, b, id] of CAPS) cap(s, t, a, b, id);
      // 关注：叠在最后一个画面上，像一张戏票
      const fp = seg(t, 33.5, 33.8);
      if (fp > 0) at(640, lerp(-80, 196, E.back(fp, 1.3)), 1, -0.04, () => {
        const w = 580, h = 86;
        shape(box(-w / 2, -h / 2, w, h, 10), C.warm, { w: 4 });
        line([[-w / 2 + 92, -h / 2 + 8], [-w / 2 + 92, h / 2 - 8]], { w: 3, dash: [8, 7] });
        txt('★', -w / 2 + 46, 16, { size: 44, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
        txt('关注，看下一场心理实验', 46, 13, { size: 36, color: C.ink, t, t0: 33.65, cps: 0.02, shadow: 0 });
      });
    },
  });

  // ---------- 音效事件（这一期专门做的一套：剧场、教室、夜里、街上各有各的声音） ----------
  const pan = x => clamp((x - 866) / 900, -0.8, 0.8);
  // 镜头 A：剧场底噪 + 窃窃私语；一双双眼睛睁开是一个个“噗啾”；心跳越来越快；小军鼓滚奏到定格，镲一响盖章
  ev(0.0, 'clunk', { g: 1.1 }); ev(0.0, 'roomtone', { d: 8.4, g: 0.9 }); ev(0.1, 'whisper', { d: 5.4, n: 4, g: 0.5 });
  DARK.forEach(([x], i) => ev(0.15 + i * 0.12, 'plip', { f: 0.8 + i * 0.07, g: 0.5, pan: pan(x) }));
  EYES.forEach(([x], i) => ev(0.3 + i * 0.27, 'plip', { f: 0.75 + hash(i * 3.1) * 0.7, g: 0.32, pan: pan(x) }));
  for (const s of [1.0, 1.62, 2.18, 2.68, 3.12, 3.52, 3.88, 4.2, 4.5, 4.78, 5.04, 5.3]) ev(s, 'heart', { g: 0.85 });
  ev(1.5, 'cloth', { d: 0.3 }); ev(3.1, 'cloth', { d: 0.25, g: 0.6 });
  ev(3.1, 'drumroll', { d: 2.5 }); ev(3.3, 'glock', { f: 1760, g: 0.7, pan: 0.3 });
  ev(5.6, 'crash', { g: 0.9 }); ev(6.12, 'stamp', { f: 0.7, g: 1.6 }); ev(6.12, 'punch', { g: 0.6 });
  ev(8.0, 'curtain', { d: 0.5 }); ev(8.0, 'creak', { g: 0.5, pan: -0.5 }); ev(8.45, 'curtain', { d: 0.5 }); ev(8.5, 'creak', { g: 0.4, pan: 0.5 });
  // 镜头 B：黑着的教室，私语又起来；开灯是日光灯“啪滋滋”；猜错了是蜂鸣，23% 是一串钟琴
  ev(8.6, 'roomtone', { d: 6.8, g: 0.7 }); ev(8.8, 'whisper', { d: 3.0, n: 3, g: 0.45 });
  CL.forEach((c, i) => ev(8.9 + i * 0.15, 'plip', { f: 0.9 + i * 0.12, g: 0.4, pan: pan(c.x) }));
  ev(9.1, 'pop', { f: 0.7, pan: 0.3 }); for (const s of [9.5, 10.15, 10.8, 11.4]) ev(s, 'heart', { g: 0.8 });
  ev(LU, 'flick', { g: 1.1 }); ev(LU + 0.3, 'crickets', { d: 2.6, g: 0.8 });
  ev(LU + 0.6, 'buzzer', { d: 0.45, g: 0.8 }); ev(LU + 0.85, 'glockrun', { notes: [784, 988, 1175, 1568], g: 0.9 }); ev(LU + 1.0, 'boom', { g: 0.35 });
  ev(LU + 0.9, 'yawn', { g: 0.7, pan: pan(1060) }); ev(LU + 1.6, 'blip', { f: 1.0, g: 0.6, pan: pan(470) }); ev(LU + 2.0, 'snore', { d: 1.4, g: 0.35, pan: pan(680) });
  // 镜头 C：探照灯扫过 → 得意的小贝斯配木地板脚步；没人看，悲伤长号
  ev(15.15, 'whoosh', { d: 0.55 }); ev(15.3, 'glock', { f: 2093, g: 0.4 });
  ev(15.4, 'bassline', { g: 0.9 }); ev(15.4, 'woodstep', { d: 1.6, rate: 3.6, g: 0.8, pan: 0.3 });
  ev(16.0, 'shimmer', {}); ev(16.9, 'crickets', { d: 1.4, g: 0.8 }); ev(17.55, 'tromb', { g: 0.9 });
  // 镜头 D：熄灯；夜里的底（远处蟋蟀、钟）+ 猫头鹰；回放是倒带声 + 答错的蜂鸣；对面床的呼噜带小口哨
  ev(18.65, 'clunk', { g: 0.9, vary: 0.12 });
  ev(19.25, 'nightbed', { d: 6.5, g: 0.9 }); ev(19.25, 'ticktock', { d: 6.4, g: 0.7, pan: 0.25 }); ev(21.1, 'owl', { g: 0.6, pan: 0.6 });
  ev(19.5, 'pop', { f: 0.8, pan: -0.2 });
  for (let n = 0; n < 3; n++) { ev(19.85 + n * 1.3, 'rewind', { d: 0.45, g: 0.6 }); ev(19.85 + n * 1.3 + 0.55, 'buzzer', { d: 0.28, g: 0.55 }); }
  ev(22.85, 'whoosh', { d: 0.7, g: 0.6 }); ev(23.2, 'clunk', { g: 0.6, pan: 0.3, vary: 0.15 }); ev(23.4, 'snorew', { d: 2.2, g: 0.9, pan: 0.2 });
  // 镜头 E：街上的底；紧张的小碎步；路人手机此起彼伏；摘帽是滑哨 + 布料；没人理；松口气
  ev(25.4, 'sweep', { d: 0.6 });
  ev(25.9, 'streetbed', { d: 3.9, g: 0.9 }); ev(25.9, 'woodstep', { d: 2.1, rate: 4.4, f: 1.15, g: 0.7, pan: -0.2 });
  for (const s of [26.3, 26.85, 27.4, 27.9]) ev(s, 'heart', { g: 0.7 });
  [[26.4, 0.9], [27.25, 1.12], [28.05, 0.8]].forEach(([s, f], k) => ev(s, 'blip', { f, g: 0.5, pan: 0.6 - k * 0.3 }));
  ev(HAT, 'slide', { up: true, d: 0.5 }); ev(HAT, 'cloth', { d: 0.4 }); ev(HAT + 0.6, 'crickets', { d: 1.3, g: 0.8 }); ev(29.3, 'sigh', { g: 0.9 });
  // 镜头 F：一束束灯亮起来，每一束配一个竖琴音，连成一个和弦；最后暖和弦 + 检票的“咔嚓”
  ev(29.6, 'roomtone', { d: 5.7, g: 0.8 }); ev(29.6, 'swell', { d: 1.6, g: 0.4 });
  const ARP = [262, 330, 392, 494, 587, 659];
  ORDER.forEach((i, k) => { ev(30.5 + k * 0.16, 'clunk', { g: 0.45, pan: pan(PF[i][0] * 0.6 + 866 * 0.4), vary: 0.12 }); ev(30.52 + k * 0.16, 'harp', { f: ARP[k], g: 0.75, pan: pan(PF[i][0] * 0.6 + 866 * 0.4) }); });
  ev(33.0, 'pad', { fs: [131, 196, 262, 330, 392], d: 2.4, g: 0.8 }); ev(33.0, 'glock', { f: 1568, g: 0.5 }); ev(33.05, 'shimmer', { g: 0.8 });
  ev(33.5, 'whoosh', { d: 0.3, up: false, g: 0.6 }); ev(33.78, 'punch', { g: 0.9 });
})();
