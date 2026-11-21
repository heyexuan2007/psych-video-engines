// 《0.1 秒，你就给他打了分》整片：7 个镜头 + 6 种转场 + 字幕 + 音效事件
// 一条线讲到底：新同事迟到 → 你一张张贴便利贴，直到看不见他的脸 → 分屏：换一个第一眼，同样的事贴的字全变了 → 那天他送邻居去医院。
// “你”全片只出现一只贴便利贴的手。不配音：信息全靠屏幕上的字，都在抖音安全区里（x 134–1594，y 119–929）。
(() => {
  const NT = [5.8, 8.7, 12.3, 16.0, 22.5];             // 五张便利贴拍上的时刻
  const FALL = [41.5, 41.35, 41.2, 41.05, 40.9];        // 结尾一张张飘落
  const HIM = { seed: 1500, hair: 0, hairCol: C.ink, shirt: C.white, glasses: 1, badge: 1 };
  const jolt = (t, t0, k = 7) => t > t0 ? Math.exp(-(t - t0) * 9) * k : 0;
  /** 新同事。q.clean=true 不画便利贴；q.fall=true 便利贴按 FALL 飘落 */
  function he(t, q) { return drawPerson(q.x, q.y, q.s, { ...HIM, t, extra: q.clean ? null : noteExtra(t, NT, q.fall ? FALL : null), ...q }); }
  function slapOn(t, i, r, s, from) { const N = NOTES[i]; slap(t, NT[i], from, r.pt(N.x, N.y), N.txt, { size: 36 * s, rot: N.rot, col: C.red, seed: 1310 + i * 7, bs: s }); }

  // ---------- 镜头 A（0–3 秒）：0.1 秒。门推开，新同事探进来 ----------
  function shotA(t) {
    bg();
    hw('{{0.1}}', 560, 612, { size: 420, font: F.lat, bold: 0.25, seed: 14, spacing: 0 });
    hw('秒', 1058, 596, { size: 250, font: F.wei, bold: 1.3, seed: 15 });
    sk([[226, 678], [1160, 660]], { color: C.red, w: 14, seed: 1401, amp: 4, p: E.out(seg(t, 0.4, 0.8)) });
    const X0 = 1268, X1 = 1572, Y0 = 246, Y1 = 772;
    ground(Y1, 1150, 1640, 43);
    sk([[X0, Y1], [X0, Y0], [X1, Y0], [X1, Y1]], { fill: C.paperLo, w: 7, seed: 1410, off: [0, 0] });
    sk([[X0, Y0], [X0 - 64, Y0 + 30], [X0 - 64, Y1 + 34], [X0, Y1]], { close: true, fill: C.white, w: 6, seed: 1411, off: [0, 0] });
    sk(ell(X0 - 44, 530, 8, 8, 10), { close: true, fill: C.ink, w: 3, seed: 1412, off: [0, 0] });
    const inn = E.out(seg(t, 0.3, 1.0)), hi = t > 1.25;
    ctx.save(); ctx.beginPath(); ctx.rect(X0 + 3, Y0 + 3, X1 - X0 - 6, Y1 - Y0); ctx.clip();
    const r = he(t, { x: lerp(1650, 1424, inn), y: Y1, s: 1.42, clean: true, lean: lerp(-0.2, 0, inn), eyes: hi ? 'happy' : 'wide', mouth: hi ? 'smile' : 'wave', look: [-1, 0], blush: 0.7, sweat: 0.8, armL: hi ? 2.45 + Math.sin(t * 13) * 0.28 : 0.3 });
    ctx.restore();
    circleMark(r.head[0], r.head[1] - 4, 126, 120, seg(t, 1.5, 1.85), { w: 9, seed: 27 });
    note('看一张脸只要 0.1 秒，印象就有了 · Willis & Todorov 2006', 150, 915, { t, t0: 0.9 });
  }

  // ---------- 镜头 B（3–7 秒）：迟到五分钟 → 第一张“散漫” ----------
  function shotB(t) {
    bg(); ground(768, 150, 1600, 45);
    hw('上班 9:00', 190, 236, { size: 56, color: C.pencil, bold: 0.7, seed: 21, align: 'left' });
    hw('9:{{05}}', 520, 520, { size: 300, font: F.lat, bold: 0.25, seed: 22, spacing: 0 });
    circleMark(672, 414, 232, 158, seg(t, 3.75, 4.1), { w: 10, seed: 26 });
    const N0 = NT[0], run = E.out(seg(t, 3.0, 3.6)), bowA = seg(t, 3.6, 3.85) * (1 - seg(t, N0, N0 + 0.15)), bow = Math.abs(Math.sin((t - 3.7) * 4.4)) * bowA, hit = t >= N0, sad = t > N0 + 0.7;
    const r = he(t, { x: lerp(1760, 1230, run), y: 768, s: 1.5, lean: -0.3 * bow, legs: run < 1 ? t * 16 : 0, shake: jolt(t, N0),
      eyes: sad ? 'dot' : hit ? 'wide' : bow > 0.5 ? 'closed' : 'dot', mouth: sad ? 'frown' : hit ? 'o' : 'open', brow: sad ? -0.7 : -0.3, look: hit ? [-0.7, 0.9] : [-1, 0], sweat: 1 });
    const bp = Math.min(seg(t, 3.9, 4.1), 1 - seg(t, N0 - 0.25, N0 - 0.05));
    if (bp > 0) layer(clamp(bp * 2), () => { speech(1440, 268, 236, 118, bp, { tx: -60, dir: -1, seed: 1420 }); if (bp > 0.3) hw('抱歉！', 1440, 290, { size: 62, bold: 1, seed: 23 }); });
    slapOn(t, 0, r, 1.5, [540, 1130]);
  }

  // ---------- 镜头 C（7–14 秒）：不说话 → “高冷”；天黑了还在加班 → “装样子” ----------
  function shotC(t) {
    bg();
    const nt = E.io(seg(t, 9.95, 10.5)), N1 = NT[1], N2 = NT[2];
    if (nt > 0) { ctx.save(); ctx.globalAlpha = 0.2 * nt; ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    drawWindow(345, 330, 300, 270, nt);
    hw('23:00', 345, 612, { size: 104, font: F.lat, bold: 0.25, seed: 31, spacing: 0, t, t0: 10.35, cps: 0.05 });
    const ch = 1 - seg(t, 9.55, 9.85);
    if (ch > 0) layer(ch, () => {
      [[660, 296, '哈哈哈', 7.45, 170], [800, 420, '哈哈', 7.75, 130]].forEach(([x, y, s, a, w], i) => {
        const p = seg(t, a, a + 0.2), by = y + Math.sin(t * 2.6 + i * 1.7) * 7; speech(x, by, w, 84, p, { tx: -30, dir: -1, seed: 1425 + i * 3, rot: (i ? 1 : -1) * 0.05 }); if (p > 0.6) hw(s, x, by + 17, { size: 46, color: C.pencil, bold: 0.8, seed: 32 + i });
      });
      const p = seg(t, 7.95, 8.15); speech(1318, 286, 132, 92, p, { tx: -44, dir: -1, seed: 1432 }); if (p > 0.6) dots3(1318, 286);
    });
    drawLamp(1420, 668, 1, nt);
    const yawn = t > 10.9 && t < 11.9, rub = t >= 11.9 && t < N2, hit1 = t >= N1 && t < N1 + 0.9, hit2 = t >= N2;
    const r = he(t, { x: 1090, y: 806, s: 1.5, shake: jolt(t, N1) + jolt(t, N2),
      eyes: hit2 ? 'wide' : yawn ? 'closed' : rub ? 'squint' : hit1 ? 'wide' : 'dot', mouth: hit2 ? 'wave' : yawn ? 'open' : hit1 ? 'o' : 'flat', brow: hit2 ? -0.7 : 0,
      look: hit2 ? [0, -1] : hit1 ? [0.8, 1] : [-0.7, 0.8], armL: yawn ? 2.5 : 0.3, armR: rub ? 2.62 + Math.sin(t * 16) * 0.08 : 0.3, sweat: hit2 ? 0.8 : 0 });
    drawTable(560, 1560, 668, 770);
    drawLaptop(850, 668, 1);
    slapOn(t, 1, r, 1.5, [620, 1130]);
    slapOn(t, 2, r, 1.5, [700, 1130]);
  }

  // ---------- 镜头 D（14–18 秒）：提意见 → “挑剔”，开始遮住脸 ----------
  function shotD(t) {
    bg(); ground(768, 150, 1600, 47);
    drawBoard(530, 410, 640, 440, 768, seg(t, 15.15, 15.5));
    const N3 = NT[3], hit = t >= N3, down = E.io(seg(t, N3 + 0.5, N3 + 1.2));
    const r = he(t, { x: 1150, y: 768, s: 1.5, shake: jolt(t, N3), armL: lerp(2.2 + (hit ? 0 : Math.sin(t * 9) * 0.05), 0.5, down),
      eyes: hit ? 'wide' : 'dot', mouth: hit ? 'wave' : 'open', brow: hit ? -0.8 : 0.3, look: hit ? [-0.5, 0.3] : [-1, -0.2], sweat: hit ? 1 : 0 });
    if (down < 0.5) sk([r.handL, [r.handL[0] - 150, r.handL[1] - 46]], { w: 7, seed: 1440, alpha: 1 - down * 2 });
    const bp = Math.min(seg(t, 14.7, 14.9), 1 - seg(t, N3 + 0.15, N3 + 0.5));
    if (bp > 0) layer(clamp(bp * 2), () => { speech(1400, 262, 300, 118, bp, { tx: -90, dir: -1, seed: 1442 }); if (bp > 0.6) hw('这里不对', 1400, 284, { size: 60, bold: 1, seed: 33 }); });
    slapOn(t, 3, r, 1.5, [600, 1130]);
  }

  // ---------- 镜头 E（18–24 秒）：你不理他 → 他也不再打招呼 → “果然” ----------
  function shotE(t, nobg) {
    if (!nobg) bg();
    ground(768, 150, 1600, 49);
    const la = 1 - seg(t, 23.5, 23.9);
    hw('一周后', 190, 250, { size: 76, color: C.pencil, font: F.wei, bold: 0.8, seed: 41, align: 'left', alpha: la });
    sk([[186, 274], [424, 268]], { w: 5, color: C.pencil, seed: 1450, alpha: la });
    const N4 = NT[4], hit = t >= N4, wv = t < 19.1, lower = E.io(seg(t, 19.7, 20.2)), wk = E.io(seg(t, 20.3, 21.8)), walking = wk > 0 && wk < 1, cold = t > 19.15;
    const r = he(t, { x: lerp(1150, 860, wk), y: 768, s: 1.45, shake: jolt(t, N4), armR: lerp(2.5 + (wv ? Math.sin(t * 13) * 0.3 : 0), 0.3, lower),
      eyes: cold ? 'dot' : 'happy', mouth: cold ? (t > 19.6 ? 'flat' : 'o') : 'smile', brow: cold ? -0.6 : 0, look: t > 20.2 ? [0, 1] : [-1, 0], sweat: cold && t < 20.3 ? 0.8 : 0,
      legs: walking ? t * 13 : 0, lean: walking ? -0.07 : 0 });
    // “早！”：没人接，掉下去
    const bp = seg(t, 18.15, 18.35), bf = seg(t, 19.3, 19.95);
    if (bp > 0 && bf < 1) layer(1 - bf, () => { speech(1395, 280 + bf * 50, 200, 124, bp, { tx: -50, dir: -1, seed: 1452, rot: bf * 0.14 }); if (bp > 0.6) hw('早！', 1395, 310 + bf * 50, { size: 84, font: F.wei, bold: 1.1, color: mixc(C.ink, C.gray, bf * 1.6), seed: 42 }); });
    const dq = Math.min(seg(t, 20.6, 20.8), 1 - seg(t, 21.9, 22.1));
    if (dq > 0) layer(dq, () => dots3(r.top[0], r.top[1] - 34, 7, 26));
    // 你举起手机
    const up = E.back(seg(t, 18.55, 18.95), 1.2) - E.io(seg(t, 21.8, 22.2));
    if (up > 0.01) drawPhoneHand(410, lerp(1340, 640, up), t);
    slapOn(t, 4, r, 1.45, [600, 1130]);
  }

  // ---------- 镜头 F（24–38 秒）：分屏。左边是你看到的他，右边换一个第一眼 ----------
  const DIV = 866, LX = 500, RX = 1232, PH = [24.0, 26.0, 28.0, 30.0, 32.0, 34.0];
  const LAB_L = ['高冷', '装样子', '挑剔', '散漫'], LAB_R = ['沉稳', '努力', '认真', ''];
  const ROWY = i => 392 + i * 100, dimA = t => lerp(1, 0.2, seg(t, 35.85, 36.2));

  /** 右边的第一眼：他在帮同事修电脑 */
  function fixScene(t, cx) {
    const ok = t >= 25.3, k = t - 25.3;
    drawPerson(cx - 218, 792, 0.9, { t, seed: 537, hair: 1, hairCol: C.kraftD, eyes: ok ? 'happy' : 'wide', mouth: ok ? 'open' : 'wave', brow: ok ? 0 : -0.8, look: [1, 0], sweat: ok ? 0 : 1, hop: ok ? Math.abs(Math.sin(k * 8)) * 18 * Math.exp(-k * 2) : 0, armL: ok ? 2.6 : 0.3, armR: ok ? 2.6 : 0.3 });
    const r = he(t, { x: cx + 218, y: 792, s: 0.9, clean: true, eyes: ok ? 'happy' : 'dot', mouth: ok ? 'smile' : 'flat', look: [-1, 0.3], armL: ok ? 0.5 : 1.75 + Math.sin(t * 18) * 0.12, brow: ok ? 0 : 0.3 });
    drawTable(cx - 320, cx + 320, 676, 768);
    drawMonitor(cx, 676, 0.9, ok, t);
    if (!ok) sk([r.handL, [r.handL[0] - 62, r.handL[1] + 14]], { w: 7, seed: 1472 });
    if (ok && k < 0.5) burst(cx, 572, 120, 200, 10, { color: C.yellow, w: 7, seed: 1474, p: E.out(k / 0.5), alpha: 1 - k / 0.5 });
  }

  /** 四件一模一样的事：0 不说话 1 加班 2 提意见 3 迟到。左右两边调用的是同一个函数，所以动作完全同步 */
  function vignette(k, cx, t, T0) {
    const u = t - T0, P = { clean: true, s: 0.95 };
    if (k === 0) {
      he(t, { ...P, x: cx + 70, y: 792, eyes: 'dot', mouth: 'flat', look: [-0.7, 0.8] });
      drawTable(cx - 300, cx + 280, 676, 768); drawLaptop(cx - 150, 676, 0.72);
      const p = seg(u, 0.35, 0.55); speech(cx + 236, 524, 104, 74, p, { tx: -30, dir: -1, seed: 1460 }); if (p > 0.6) dots3(cx + 236, 524, 6, 20);
    } else if (k === 1) {
      ctx.save(); ctx.globalAlpha = 0.18; ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H); ctx.restore();
      drawWindow(cx - 232, 530, 132, 132, 1);
      drawLamp(cx + 236, 676, 0.72, 1);
      const yawn = (u % 1.7) > 0.25 && (u % 1.7) < 1.1;
      he(t, { ...P, x: cx + 70, y: 792, eyes: yawn ? 'closed' : 'squint', mouth: yawn ? 'open' : 'flat', look: [-0.7, 0.8], armL: yawn ? 2.5 : 0.3 });
      drawTable(cx - 300, cx + 280, 676, 768); drawLaptop(cx - 150, 676, 0.72);
    } else if (k === 2) {
      ground(768, cx - 330, cx + 320, 57);
      drawBoard(cx - 175, 560, 250, 180, 768, seg(u, 0.4, 0.7));
      const r = he(t, { ...P, x: cx + 130, y: 768, armL: 2.2 + Math.sin(t * 9) * 0.05, eyes: 'dot', mouth: 'open', brow: 0.3, look: [-1, -0.2] });
      sk([r.handL, [r.handL[0] - 92, r.handL[1] - 22]], { w: 5, seed: 1440 });
    } else {
      ground(768, cx - 330, cx + 320, 57);
      hw('9:{{05}}', cx - 150, 650, { size: 124, font: F.lat, bold: 0.25, seed: 22, spacing: 0 });
      const bow = Math.abs(Math.sin(u * 4.4));
      he(t, { ...P, x: cx + 170, y: 768, lean: -0.3 * bow, eyes: bow > 0.5 ? 'closed' : 'dot', mouth: 'open', brow: -0.3, look: [-1, 0], sweat: 1 });
    }
  }

  /** 一个半屏在某一段里画什么。i: 0 开场 1–4 四件事 5 对照表 */
  function phase(i, side, t) {
    const cx = side ? RX : LX;
    if (i === 0) {
      if (side) fixScene(t, cx);
      else { ctx.save(); ctx.translate(LX - 860 * 0.7, 760 - 768 * 0.7); ctx.scale(0.7, 0.7); shotE(t, true); ctx.restore(); }
      return;
    }
    if (i === 5) {
      layer(dimA(t), () => (side ? LAB_R : LAB_L).forEach((txt, j) => {
        const a = PH[5] + 0.3 + j * 0.1;
        stickyNote(cx, ROWY(j), txt || '？', { size: 52, rot: (hash(j * 3 + side) - 0.5) * 0.08, col: side ? C.ink : C.red, s: E.back(seg(t, a, a + 0.22)), seed: 1620 + j * 2 + side });
      }));
      return;
    }
    const k = i - 1, T0 = PH[i], u = t - T0, ts = T0 + 0.7, lx = cx + 70, ly = 300, txt = (side ? LAB_R : LAB_L)[k];
    vignette(k, cx, t, T0);
    const o = { size: 76, rot: side ? 0.05 : -0.05, col: side ? C.ink : C.red, seed: 1600 + k * 2 + side, bs: 1.5, hs: 1.15 }, from = side ? [W + 100, 430] : [-100, 430];
    if (txt) { stuck(t, ts, lx, ly, txt, o); slap(t, ts, from, [lx, ly], txt, o); }
    else {   // 迟到：右边的你，手伸出去又缩了回来
      const e = 0.6 * (E.out(seg(u, 0.45, 0.8)) - E.io(seg(u, 1.3, 1.75)));
      if (e > 0.01) {
        const hx = lerp(from[0], lx, e) + (e > 0.55 ? Math.sin(t * 34) * 4 : 0), hy = lerp(from[1], ly, e);
        drawHand(from[0] + 590, from[1] + 107, hx + 20, hy + 4, { seed: 1200, s: 1.15 });
        stickyNote(hx, hy, '', { size: 76, rot: 0.2, s: 1.2, seed: 1606 });
      }
      drawQ(lx, ly + 48, 0.66, seg(u, 0.95, 1.45), { color: C.ink, seed: 1476 });
    }
  }
  function panel(side, t) {
    let i = 0; while (i < 5 && t >= PH[i + 1]) i++;
    const x0 = side ? DIV : 0, w = side ? W - DIV : DIV, dir = (side ? 1 : -1) * (i % 2 ? 1 : -1), tr = i > 0 ? seg(t, PH[i], PH[i] + 0.3) : 1;
    ctx.save(); ctx.beginPath(); ctx.rect(x0, 0, w, H); ctx.clip();
    if (tr < 1) { const e = E.io(tr); ctx.save(); ctx.translate(0, dir * H * e); phase(i - 1, side, t); ctx.restore(); ctx.save(); ctx.translate(0, -dir * H * (1 - e)); phase(i, side, t); ctx.restore(); }
    else phase(i, side, t);
    ctx.restore();
  }
  /** 钉在每个半屏左上角的“第一眼”小画；36 秒放大到中间 */
  function thumb(side, t) {
    const cx = side ? RX : LX, a = side ? 25.8 : 24.65; if (t < a) return;
    const z = E.io(seg(t, 35.9 + side * 0.25, 36.4 + side * 0.25)), pop = E.back(seg(t, a, a + 0.25));
    const x = lerp(cx - 225, cx, z), y = lerp(240, 505, z), s = lerp(1, 2.1, z) * (0.3 + 0.7 * pop);
    at(x, y, s, lerp(side ? 0.04 : -0.05, 0, z), () => {
      sk(rr(-89, -62, 190, 140, 6), { fill: 'rgba(60,45,25,0.18)', stroke: false, seed: 1480, off: [0, 0] });
      sk(rr(-95, -70, 190, 140, 6), { close: true, fill: C.white, w: 4.5, seed: 1481 + side, off: [0, 0] });
      ctx.save(); ctx.beginPath(); ctx.rect(-92, -67, 184, 134); ctx.clip();
      if (!side) { hw('9:05', -38, 14, { size: 46, font: F.lat, color: C.red, bold: 0.25, seed: 22, spacing: 0 }); drawPerson(54, 64, 0.34, { ...HIM, t, lean: -0.22, eyes: 'closed', mouth: 'open', sweat: 1 }); }
      else { drawMonitor(-38, 44, 0.42, true, t); drawPerson(54, 64, 0.34, { ...HIM, t, eyes: 'happy', mouth: 'smile', armL: 1.75 }); }
      ctx.restore();
      at(0, -70, 1, -0.05, () => sk(rr(-34, -11, 68, 22, 2), { fill: 'rgba(216,68,58,0.55)', stroke: false, seed: 1485, amp: 1, off: [0, 0] }));
    });
    hw('第一眼', cx - 225, 352, { size: 38, color: C.pencil, bold: 0.7, seed: 46 + side, alpha: (1 - seg(z, 0, 0.3)) * clamp(pop) });
    hw('{{第一眼}}', cx, 304, { size: 84, font: F.wei, bold: 1.3, seed: 44 + side, t, t0: 36.3 + side * 0.25 });
  }
  function shotF(t) {
    bg(); panel(0, t); panel(1, t);
    sk([[DIV, -20], [DIV, H + 20]], { w: 7, seed: 1470, amp: 3 });
    if (t >= PH[5]) layer(dimA(t), () => { for (let i = 0; i < 4; i++) {   // 同一件事，一一对上
      const a = PH[5] + 0.5 + i * 0.28, p = seg(t, a, a + 0.3), y = ROWY(i), ap = E.back(seg(t, PH[5] + 0.3 + i * 0.1, PH[5] + 0.52 + i * 0.1));
      if (p > 0) sk([[LX + 112, y], [RX - 84, y]], { w: 6, seed: 1730 + i, amp: 2, p });
      if (ap > 0) at(DIV, y, ap, 0, () => drawIcon(i, 0, 0, seg(p, 0.4, 0.7)));
    } });
    thumb(0, t); thumb(1, t);
    if (t > 34.4) note('同样的特点，先看到哪个，印象就不一样 · 阿希 1946', 150, 915, { t, t0: 34.5 });
  }
  /** 分屏推开：旧画面缩到左半边，右半边从屏幕外推进来 */
  function splitOpen(p, t) {
    const e = E.io(p), dv = lerp(W + 30, DIV, e), k = lerp(1, 0.7, e);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, dv, H); ctx.clip();
    ctx.translate(lerp(0, LX - 860 * 0.7, e), lerp(0, 760 - 768 * 0.7, e)); ctx.scale(k, k); shotE(t, true); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(dv, 0, W - dv, H); ctx.clip(); ctx.translate(dv - DIV, 0); phase(0, 1, t); ctx.restore();
    sk([[dv, -20], [dv, H + 20]], { w: 7, seed: 1470, amp: 3 });
  }

  // ---------- 镜头 G（38–43.3 秒）：那天早上。圆圈越开越大，露出他扶着的人和医院 ----------
  const TF = 41.95;
  function sceneG(t) {
    const mins = Math.round(lerp(545, 510, E.io(seg(t, 38.75, 39.45)))), clock = Math.floor(mins / 60) + ':' + String(mins % 60).padStart(2, '0');
    ground(768, 120, 1700, 53);
    hw(t >= 39.45 ? '{{' + clock + '}}' : clock, 440, 372, { size: 200, font: F.lat, bold: 0.25, seed: 61, spacing: 0 });
    hw('那天早上', 440, 196, { size: 58, color: C.pencil, bold: 0.8, seed: 63, t, t0: 39.5 });
    drawHospital(1240, 768);
    const st = Math.max(0, t - 39.6), clean = t > FALL[0] + 0.3;
    const g = drawPerson(1085, 768, 1.06, { t, seed: 910, hair: 2, hairCol: C.gray, eyes: 'happy', mouth: 'smile', lean: -0.07, armL: 1.5, armR: 0.25, hop: Math.abs(Math.sin(st * 2.6)) * 3, blush: 0.5 });
    sk([[g.handR[0] + 4, g.handR[1] - 22], [g.handR[0] + 10, 768]], { w: 7, seed: 1490 });
    sk(qd([g.handR[0] + 4, g.handR[1] - 22], [g.handR[0] - 8, g.handR[1] - 42], [g.handR[0] - 26, g.handR[1] - 24], 6), { w: 7, seed: 1491 });
    const r = he(t, { x: 830, y: 768, s: 1.3, fall: true, eyes: 'happy', mouth: 'smile', look: [1, 0], sweat: 0.7, blush: clean ? 0.6 : 0, armR: 1.45, hop: Math.abs(Math.sin(st * 2.6 + 1.2)) * 3 });
    const bk = t - (FALL[0] + 0.25);
    if (bk > 0 && bk < 0.5) burst(r.head[0], r.head[1], 120, 190, 12, { color: C.yellow, w: 7, seed: 1494, p: E.out(bk / 0.5), alpha: 1 - bk / 0.5, a0: Math.PI * 0.9, a1: Math.PI * 2.1 });
  }
  function shotG(t) {
    bg();
    const op = E.io(seg(t, 38.7, 39.5)), cxm = lerp(590, 866, op), cym = lerp(490, 540, op), r = lerp(415, 1750, op);
    if (op >= 1) sceneG(t);
    else { masked(() => sceneG(t), () => sk(ell(cxm, cym, r, r, 48), { fill: '#000', stroke: false, seed: 15, amp: 8, off: [0, 0] })); sk(ell(cxm, cym, r, r, 48), { close: true, w: 8, seed: 15, amp: 8, alpha: 1 - seg(op, 0.7, 1) }); }
    // 最后一张便利贴：关注我（叠在揭晓画面上，不另起一段）
    const o = { size: 92, rot: -0.05, col: C.ink, seed: 1650, bs: 1.6, hs: 1.2 };
    stuck(t, TF, 440, 590, '关注我', o);
    if (t >= TF) at(440 + 178, 590 - 94, E.back(seg(t, TF + 0.1, TF + 0.35)), 0, () => { sk(ell(0, 0, 34, 34, 18), { close: true, fill: C.red, color: C.red, w: 4, seed: 1652, off: [0, 0] }); sk([[-16, 0], [16, 0]], { w: 8, color: C.white, seed: 1653, amp: 0.5, dbl: false }); sk([[0, -16], [0, 16]], { w: 8, color: C.white, seed: 1654, amp: 0.5, dbl: false }); });
    slap(t, TF, [180, 1150], [440, 590], '关注我', o);
  }

  // ---------- 合成 ----------
  const SH = [shotA, shotB, shotC, shotD, shotE, shotF, shotG];
  const TR = [[2.95, 3.3, 'pushL'], [7.0, 7.35, 'flipUp'], [13.9, 14.3, 'peel'], [17.9, 18.25, 'pushU'], [24.0, 24.5, 'split'], [37.95, 38.4, 'tear', { x: DIV }]];
  const CAPS = [
    ['{{0.1}} 秒，你就给他[[打了分]]', 0.12, 2.85, 'c1'],
    ['第一天，他迟到[[五分钟]]', 3.2, 5.25, 'c2'],
    ['你记下：{{散漫}}', 5.6, 6.95, 'c3'],
    ['他不说话，你想：{{高冷}}', 7.35, 9.85, 'c4'],
    ['他加班，你想：{{装样子}}', 10.2, 13.85, 'c5'],
    ['他提意见，你想：{{挑剔}}', 14.35, 17.85, 'c6'],
    ['你不理他', 18.4, 19.8, 'c7'],
    ['他也不再打招呼', 20.15, 21.85, 'c8'],
    ['你想：{{果然}}', 22.2, 23.7, 'c9'],
    ['如果第一眼，是[[这个]]', 24.05, 26.0, 'c10'],
    ['不说话，是[[沉稳]]', 26.35, 27.95, 'c11'],
    ['加班，是[[努力]]', 28.3, 29.95, 'c12'],
    ['提意见，是[[认真]]', 30.3, 31.95, 'c13'],
    ['迟到？应该[[有事]]', 32.3, 33.9, 'c14'],
    ['事情一件没少', 34.25, 35.6, 'c15'],
    ['只是[[先看到的]]不一样', 35.95, 37.9, 'c16'],
    ['那天，他送邻居去[[医院]]', 38.7, 40.75, 'c17'],
    ['他没变，变的是[[第一眼]]', 41.1, 99, 'c18'],
  ];
  SCENES.push({
    id: 'film', t0: -1, t1: 999,
    draw(t) {
      let i = 0; while (i < TR.length && t >= TR[i][1]) i++;
      if (i < TR.length && t >= TR[i][0]) { const [a, b, kind, o] = TR[i], p = seg(t, a, b); if (kind === 'split') splitOpen(p, t); else T[kind](p, () => SH[i](t), () => SH[i + 1](t), o); }
      else SH[i](t);
      for (const [s, a, b, id] of CAPS) cap(s, t, a, b, id);
    },
  });

  // ---------- 音效事件（只有音效，没有配音和背景音乐） ----------
  for (const c of CAPS) ev(c[1], 'tick', { f: 700, g: 0.45 });
  const slapEv = (t0, pan = 0, g = 1) => { ev(t0 - 0.26, 'whoosh', { d: 0.25, up: false, pan, g: 0.8 * g }); ev(t0, 'stamp', { f: 1.25, g: 1.3 * g, pan }); ev(t0 + 0.02, 'pop', { f: 0.7, g: 0.6 * g, pan }); };
  NT.forEach(t0 => slapEv(t0, 0.2));
  ev(0.3, 'creak', { g: 0.6, pan: 0.5 }); ev(0.4, 'scribble', { d: 0.4 }); ev(1.25, 'boing', { f: 1.25, g: 0.5, pan: 0.5 }); ev(1.5, 'squeak', { d: 0.35, pan: 0.4 });
  ev(2.95, 'whoosh', { d: 0.4 }); ev(3.05, 'steps', { d: 0.55, pan: 0.5 }); ev(3.75, 'squeak', { d: 0.35, pan: -0.3 }); ev(3.9, 'pop', { f: 1.0, pan: 0.5 });
  ev(6.45, 'deflate', { g: 0.6, pan: 0.3 });
  ev(7.0, 'flip', { g: 1.2 }); ev(7.45, 'pop', { f: 1.1, g: 0.6, pan: -0.4 }); ev(7.75, 'pop', { f: 1.3, g: 0.6, pan: -0.3 }); ev(7.95, 'pop', { f: 0.6, g: 0.6, pan: 0.4 });
  ev(9.95, 'sweep', { d: 0.6, g: 0.5 }); ev(10.35, 'settle', { f: 660 }); ev(10.5, 'press', { pan: 0.5 }); ev(10.95, 'stretch', { d: 0.8, g: 0.5, pan: 0.2 }); ev(11.9, 'rub', { d: 0.4, g: 0.5, pan: 0.2 });
  ev(13.9, 'flip', { g: 1.2 }); ev(13.95, 'whoosh', { d: 0.4 }); ev(14.7, 'pop', { f: 1.0, pan: 0.4 }); ev(15.15, 'squeak', { d: 0.4, pan: -0.3 }); ev(16.6, 'deflate', { g: 0.5, pan: 0.3 });
  ev(17.9, 'whoosh', { d: 0.45 }); ev(18.15, 'pop', { f: 1.2, pan: 0.4 }); ev(18.55, 'whoosh', { d: 0.4, pan: -0.5 }); ev(19.0, 'notify', { g: 0.5, pan: -0.5 }); ev(19.35, 'deflate', { pan: 0.4 });
  ev(20.3, 'steps', { d: 1.5, g: 0.6, pan: 0.2 }); ev(21.8, 'whoosh', { d: 0.4, up: false, pan: -0.5 });
  ev(24.0, 'tear', { d: 0.5, g: 0.6 }); ev(24.65, 'pop', { f: 1.2, pan: -0.5 }); ev(25.3, 'chime', { f: 1320, g: 0.6, pan: 0.4 }); ev(25.35, 'boing', { f: 1.2, g: 0.4, pan: 0.3 }); ev(25.8, 'pop', { f: 1.2, pan: 0.3 });
  for (let k = 0; k < 4; k++) { const T0 = PH[k + 1]; ev(T0, 'flip', { g: 0.9 }); slapEv(T0 + 0.7, -0.5); if (k < 3) { slapEv(T0 + 0.7, 0.5); ev(T0 + 0.85, 'plink', { g: 0.6, pan: 0.4 }); } }
  ev(32.45, 'whoosh', { d: 0.3, up: false, pan: 0.6, g: 0.6 }); ev(32.95, 'squeak', { d: 0.5, f: 0.8, pan: 0.4 });
  ev(34.0, 'flip', { g: 0.9 }); for (let i = 0; i < 4; i++) { ev(34.3 + i * 0.1, 'pop', { f: 1.0 + i * 0.12, g: 0.5 }); ev(34.5 + i * 0.28, 'plink', { g: 0.8 }); }
  ev(35.9, 'whoosh', { d: 0.5 }); ev(36.4, 'settle', {}); ev(36.65, 'settle', { f: 990 });
  ev(37.95, 'tear', { d: 0.5, g: 0.7 }); ev(38.45, 'heart', {}); ev(38.7, 'sweep', { d: 0.8, g: 0.6 }); ev(38.75, 'roll', { d: 0.7 }); ev(39.45, 'settle', {}); ev(39.6, 'chime', { f: 880, g: 0.4 });
  ev(40.0, 'steps', { d: 0.8, g: 0.4, pan: 0.2 });
  FALL.forEach((t0, i) => ev(t0, 'flip', { g: 0.5, pan: (i % 2 ? 0.3 : -0.3) }));
  ev(FALL[0] + 0.25, 'shimmer', { g: 0.6 }); ev(FALL[0] + 0.3, 'chime', { f: 1320, g: 0.5 });
  slapEv(TF, -0.4); ev(TF + 0.25, 'chime', { f: 1760, g: 0.45, pan: -0.3 });
})();
