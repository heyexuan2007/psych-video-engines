// 《有人让你电陌生人，你按到第几个？》整片：7 个镜头 + 字幕 + 音效事件
// 米尔格拉姆 1961 年耶鲁实验：精神科医生预测约千分之一会按到 450V；实际 40 人里 26 人（65%）按到底；
// 被电的人是演员，惨叫是录音；按的人发抖、紧张发笑（40 人里 14 人）；“责任由我来负”；
// 今天：冒充公检法电话、直播间白大褂；结尾：两个同伴先拒绝，只剩 4/40（10%）按到底。
// 不配音：信息全靠屏幕上的字。字都在抖音安全区里（x 134–1594，y 119–929）。
(() => {
  window.DUR = 35.3;
  const SUBJ = { hair: 4, shirt: C.blue, tie: C.grayD, seed: 701 };          // 受试者（老师）
  const EXPR = { coat: C.white, under: C.cream, tie: C.grayD, hair: 0, glasses: 1, seed: 710 };   // 白大褂
  const LEARN = { hair: 3, shirt: C.olive, seed: 720 };                       // 隔壁的“学生”（演员）

  // ---------- 镜头 A（0–8.0）：电击发生器，手一个一个往右按 → 隔壁喊疼 → 请继续 → 定格盖章 ----------
  const PRESS = [0.9, 1.5, 2.05, 2.55, 5.05], FZ = 5.5;
  function shotA(t) {
    const ta = t < FZ ? t : FZ;
    const down = PRESS.filter(s => ta >= s + 0.08).length;
    const sh = shakeAt(t, 3.0, 8) + shakeAt(t, 5.13, 5);
    camera(866, 540, lerp(1, 1.04, seg(t, 0, 5.5)), () => {
      labRoom({ clock: false });
      const cry = ta >= 3.0, look = ta > 3.1 && ta < 3.5 ? [1, -0.3] : ta >= 3.5 && ta < 4.8 ? [0.4, 0.8] : [-0.6, 0.4];
      drawKid(560, 640, 1.25, { ...EXPR, t: ta, eyes: 'dot', mouth: 'flat', brow: 0.2, look, armL: 0.15, armR: 0.15 });
      say('请继续。', 860, 190, seg(ta, 3.6, 3.95) * (1 - seg(ta, 5.0, 5.2)), { tx: -90, ty: 100, size: 54 });
      const g = generator(866, 470, 46, { down, needleShake: cry && ta < 3.6 });
      red(() => txt('450V', 1372, 430, { size: 170, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
      burst('啊！好疼！', 1400, 200, seg(ta, 3.0, 3.25) * (1 - seg(ta, 4.6, 4.85)), { t0: 3.0, size: 50, seed: 3 });
      // 手：按 0..3 → 缩回、发抖 → 慢慢挪到第 5 个按下
      let i, hx, hy = 716, tr = 0;
      if (ta < 2.9) {
        i = Math.max(0, Math.min(3, PRESS.filter(s => ta >= s - 0.3).length - 1));
        const m = i > 0 ? E.io(seg(ta, PRESS[i] - 0.3, PRESS[i] - 0.08)) : 1;
        hx = lerp(g.sx(Math.max(0, i - 1)), g.sx(i), m);
        hy += 16 * Math.max(0, 1 - Math.abs(ta - PRESS[i]) / 0.12) - 18 * Math.sin(Math.PI * (i > 0 ? seg(ta, PRESS[i] - 0.3, PRESS[i] - 0.08) : 0));
      }
      else if (ta < 4.4) { hx = g.sx(3) - 30 * E.out(seg(ta, 3.0, 3.3)); hy = 716 + 70 * E.out(seg(ta, 3.0, 3.3)); tr = 3; }
      else { const m = E.io(seg(ta, 4.4, 4.95)); hx = lerp(g.sx(3) - 30, g.sx(4), m); hy = lerp(786, 716, m) + 16 * Math.max(0, 1 - Math.abs(ta - PRESS[4]) / 0.12); tr = 2.2; }
      hand(hx + 14 + Math.sin(ta * 37) * tr, hy + Math.cos(ta * 41) * tr * 0.6, 1.05, 0.08, { sleeve: '#b9c3cc' });
    }, sh, 0);
    if (t >= FZ && t < FZ + 0.3) { ctx.save(); ctx.globalAlpha = (1 - seg(t, FZ, FZ + 0.3)) * 0.8; ctx.fillStyle = '#fff4dc'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    const m = E.io(seg(t, 6.6, 7.1));
    stamp('1961 · 耶鲁大学', lerp(866, 930, m), lerp(300, 175, m), lerp(1.05, 0.68, m), -0.06, seg(t, 5.8, 6.0));
  }

  // ---------- 镜头 B（8.4–14.6）：专家举牌 0.1% → 40 个人，26 个变红 → 65% ----------
  const X0 = 700, DX = 92, Y0 = 470, DY = 128;
  function shotB(t) {
    shape(box(0, 0, W, H), C.paper, { stroke: false });
    for (let x = 0; x < W; x += 60) line([[x, 0], [x, H]], { w: 1.5, color: '#c9b99a', alpha: 0.6 });
    for (let y = 0; y < H; y += 60) line([[0, y], [W, y]], { w: 1.5, color: '#c9b99a', alpha: 0.6 });
    note('YALE 1961  ·  N = 40', 150, 180, { color: '#5a4a38', size: 28, font: F.mono, weight: 700 });
    // 三位专家举牌（10.5 起退场）
    const ex = 1 - seg(t, 10.45, 10.8);
    layer(ex, () => [[500, 0], [866, 1], [1232, 2]].forEach(([x, k]) => {
      const up = E.back(seg(t, 8.6 + k * 0.18, 8.95 + k * 0.18), 2), bob = Math.sin(t * 3 + k) * 4;
      drawKid(x, 860 + bob, 1.0, { hair: [0, 6, 2][k], shirt: [C.grayD, C.navy, C.gray][k], tie: C.ink, glasses: 1, seed: 730 + k * 5, eyes: 'happy', mouth: 'smile', armL: lerp(0.3, 2.95, up), armR: lerp(0.3, 2.95, up) });
      if (up > 0.02) placard('0.1%', x, lerp(760, 470, up) + bob, 1);
    }));
    // 左栏：专家预测
    const lp = seg(t, 10.6, 10.9);
    layer(lp, () => {
      txt('精神科医生预测', 330, 400, { size: 44, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
      txt('0.1%', 330, 560, { size: 150, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, spacing: 0, shadow: 0 });
      txt('会按到底', 330, 640, { size: 44, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
      line([[620, 260], [620, 860]], { w: 4, color: C.ink, alpha: 0.6 });
    });
    // 40 个人
    for (let i = 0; i < 40; i++) {
      const c = i % 10, r = Math.floor(i / 10), ap = seg(t, 10.85 + i * 0.014, 10.98 + i * 0.014);
      if (ap <= 0) continue;
      const red1 = i < 26 && t >= 11.6 + i * 0.05, k = red1 ? 1 + 0.25 * (1 - seg(t, 11.6 + i * 0.05, 11.75 + i * 0.05)) : E.back(ap, 2);
      pict(X0 + c * DX, Y0 + r * DY, k, red1 ? C.red : null);
    }
    const bn = seg(t, 13.0, 13.3);
    if (bn > 0) red(() => txt('65%', 1110, lerp(120, 330, E.out(bn)) + shakeAt(t, 13.3, 8), { size: 210, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
    const sp = E.out(seg(t, 13.35, 13.6));
    if (sp > 0) red(() => line([[170, 540], [lerp(170, 500, sp), lerp(540, 470, sp)]], { w: 12, color: C.red }));
  }

  // ---------- 镜头 C（15.0–20.4）：墙升起来——隔壁是演员在看报，惨叫是录音机放的 → 推到按开关的人：手在抖 ----------
  function shotC(t) {
    const wl = E.io(seg(t, 15.55, 16.25)), z = E.io(seg(t, 17.4, 18.1));
    camera(lerp(866, 560, z), lerp(540, 470, z), lerp(1, 1.85, z), () => {
      labRoom({ clock: false });
      // 右边：隔壁房间
      shape(box(1000, -200, 1200, 1020), '#a89c86', { stroke: false });
      chair(1420, 820, 1);
      drawKid(1420, 760, 1.0, { ...LEARN, t, eyes: 'dot', mouth: 'smile', look: [-0.3, 0.6], armL: 1.3, armR: 1.3 });
      newspaper(1420, 560, 0.95, -0.03);
      table(1720, 830, 260, 150);
      recorder(1720, 640, 0.9, t, 1);
      burst('啊！放我出去！', 1610, 400, seg(t, 15.05, 15.25) * (1 - seg(t, 17.2, 17.4)), { t0: 15.05, size: 40, seed: 5, rot: 0.04 });
      // 墙（往上升走）
      at(0, -wl * 1100, 1, 0, () => {
        shape(box(990, -200, 1200, 1022), C.wall, { w: 6 });
        shape(box(990, 520, 1200, 300), C.woodL, { stroke: false });
        shape(box(1250, 260, 220, 90, 6), C.paper, { w: 4 });
        txt('隔壁', 1360, 322, { size: 50, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
      });
      // 左边：受试者在发生器后面，白大褂站他身后
      drawKid(800, 650, 1.15, { ...EXPR, t, eyes: 'dot', mouth: 'flat', look: [-0.8, 0.5], armL: 0.15, armR: 0.15 });
      const nerv = seg(t, 16.6, 17.4);
      drawKid(470, 700, 1.15, { ...SUBJ, t, eyes: 'wide', mouth: nerv > 0.5 ? 'grin' : 'wave', brow: -0.7, look: t < 16.3 ? [1, 0] : [0.2, 0.5], sweat: 1, shake: 1.4 + nerv, armL: 0.3, armR: 0.3 });
      at(500, 600, 0.52, 0, () => { const g = generator(0, 0, 46, { down: 8, redTail: true }); if (z > 0.5) hand(g.sx(8) + 14 + Math.sin(t * 43) * 5, 246 + Math.cos(t * 39) * 4, 1.05, 0.08, { sleeve: C.blue }); });
    });
    stamp('演员', lerp(1420, 1420, 0), 300, 0.9, 0.08, seg(t, 16.3, 16.5) * (1 - seg(t, 17.3, 17.45)));
    const np = seg(t, 18.4, 18.7);
    if (np > 0) layer(np, () => { shape(box(1080, 150, 470, 120, 4), C.paper, { w: 3, color: '#5a4a38' }); note('实验记录：', 1105, 195, { color: '#3a2e22', size: 28, weight: 700, cps: 0 }); note('40 人里 14 人紧张得笑出声', 1105, 240, { color: '#3a2e22', size: 28, weight: 700, font: F.sans, cps: 0 }); });
  }

  // ---------- 镜头 D（20.4–23.6）：“出了事怎么办？”“责任由我来负。”→ 按下去 ----------
  const GD = { x: 866, y: 650, s: 0.62 }, lampAt = (i) => [GD.x + GD.s * (-730 + 40 + 46 * (i + 0.5)), GD.y + GD.s * 178];
  function shotD(t) {
    labRoom({ clockX: 1480 });
    const pat = E.io(seg(t, 21.55, 21.85)) * (1 - E.io(seg(t, 22.4, 22.7)));
    drawKid(1040, 690, 1.2, { ...EXPR, t, eyes: 'dot', mouth: t > 21.3 && t < 22.3 ? 'smile' : 'flat', look: [-1, 0.5], armL: lerp(0.15, 1.75, pat), armR: 0.15 });
    const turn = t > 20.5 && t < 22.5;
    drawKid(680, 720, 1.2, { ...SUBJ, t, eyes: 'wide', mouth: t < 21.3 ? 'open' : 'wave', brow: -0.6, look: turn ? [1, -0.6] : [0, 0.9], sweat: 1, shake: 1.2, hop: pat * 6, armL: 0.3, armR: lerp(0.3, 0.75, E.io(seg(t, 22.55, 22.9))) });
    const down = t >= 22.95 ? 9 : 8;
    at(GD.x, GD.y, GD.s, 0, () => { const g = generator(0, 0, 46, { down, needleShake: t > 22.95 && t < 23.4 }); });
    say('出了事怎么办？', 470, 250, seg(t, 20.6, 20.9) * (1 - seg(t, 21.9, 22.1)), { tx: 60, ty: 110, size: 46 });
    say('责任由我来负。', 1250, 230, seg(t, 21.35, 21.65) * (1 - seg(t, 23.0, 23.2)), { tx: -90, ty: 110, size: 46 });
    if (t > 22.95 && t < 23.25) { ctx.save(); ctx.globalAlpha = (1 - seg(t, 22.95, 23.25)) * 0.35; ctx.fillStyle = '#fff4dc'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  }

  // ---------- 镜头 E（24.1–27.0）：今天——冒充警察的电话，红按钮“转账到安全账户” ----------
  function shotE(t) {
    labRoom({ wall: '#7d7466', clock: false, gy: 860 });
    glowLight(1250, 470, 520, 520, { i: 0.7 });
    drawKid(470, 860, 1.25, { hair: 1, shirt: C.mustard, seed: 640, t, eyes: 'wide', mouth: 'wave', brow: -0.7, look: [1, 0], sweat: 1, shake: 1, armR: 2.45, armL: 0.3, phone: 1, phoneOn: 1 });
    table(470, 900, 520, 150);
    const pin = E.out(seg(t, 24.1, 24.45));
    bigPhone(1250, lerp(1300, 470, pin), 1.05, () => {
      txt('正在通话  03:47', 0, -250, { size: 26, font: F.sans, weight: 400, color: '#333', t: 99, t0: 0, cps: 0, shadow: 0 });
      shape(circ(0, -170, 46), '#9aa4aa', { stroke: false });
      txt('XX市公安局', 0, -86, { size: 44, color: '#111', t: 99, t0: 0, cps: 0, shadow: 0 });
      txt('刑侦支队 · 王警官', 0, -44, { size: 28, weight: 400, color: '#333', t: 99, t0: 0, cps: 0, shadow: 0 });
      const mp = seg(t, 24.6, 24.8);
      if (mp > 0) layer(mp, () => {
        shape(box(-130, 0, 260, 140, 18), '#ffffff', { w: 3, color: '#9aa4aa' });
        txt('你的账户涉嫌洗钱', 0, 56, { size: 30, color: '#111', t, t0: 24.65, cps: 0.04, shadow: 0 });
        txt('请立刻配合调查', 0, 104, { size: 30, color: '#111', t, t0: 25.0, cps: 0.04, shadow: 0 });
      });
      const bp = seg(t, 25.4, 25.6), pulse = 1 + 0.05 * Math.sin(t * 9) * seg(t, 25.6, 25.8);
      if (bp > 0) red(() => layer(bp, () => at(0, 230, pulse, 0, () => { shape(box(-130, -40, 260, 80, 40), C.red, { stroke: false }); txt('转账到安全账户', 0, 12, { size: 30, color: '#fff3ea', t: 99, t0: 0, cps: 0, shadow: 0 }); })));
    });
    const hp = E.io(seg(t, 25.9, 26.7));
    hand(1236 + Math.sin(t * 31) * 2, lerp(1100, 775, hp), 0.62, -0.05, { sleeve: C.mustard });
    note('2026', 150, 180, { color: C.sep, size: 30, font: F.mono, weight: 700 });
  }

  // ---------- 镜头 F（27.3–30.0）：直播间里的白大褂“专家” ----------
  const DANMU = ['专家说的肯定没错', '下单了', '已买三瓶', '医生推荐的放心', '下单了', '给爸妈也买了'];
  function shotF(t) {
    shape(box(0, 0, W, H), '#6f675b', { stroke: false });
    const S = 1.18, PX = 866, PY = 500;
    bigPhone(PX, PY, S, () => {
      ctx.save(); ctx.beginPath(); ctx.roundRect(-152, -318, 304, 636, 30); ctx.clip();
      shape(box(-160, -330, 320, 660), '#d9d2c4', { stroke: false });
      for (let i = 0; i < 5; i++) shape(box(-150 + i * 64, -240, 40, 150, 4), '#c3b9a6', { stroke: false });   // 背后的药柜
      drawKid(-10, 300, 0.78, { ...EXPR, t, eyes: 'happy', mouth: 'grin', look: [0, 0], armR: 1.9 + Math.sin(t * 6) * 0.15, armL: 0.4 });
      bottle(103, 80 + Math.sin(t * 6) * 6, 0.75);
      shape(box(-140, -300, 150, 36, 18), 'rgba(0,0,0,0.45)', { stroke: false });
      txt('直播中 · 3.2万', -65, -274, { size: 20, color: '#fff', t: 99, t0: 0, cps: 0, shadow: 0 });
      shape(box(-150, 60, 300, 100, 0), 'rgba(0,0,0,0.0)', { stroke: false });
      // 弹幕往上滚
      DANMU.forEach((d, i) => { const st = 27.5 + i * 0.32, y = 200 - (t - st) * 120; if (t > st && y > -40) { ctx.font = fontOf(22, F.sans, 700); const w = ctx.measureText(d).width + 24; shape(box(-140, y - 22, w, 32, 14), 'rgba(0,0,0,0.4)', { stroke: false }); txt(d, -128, y + 2, { size: 22, color: '#fff', align: 'left', t: 99, t0: 0, cps: 0, shadow: 0 }); } });
      red(() => { const p = 1 + 0.05 * Math.sin(t * 9); at(0, 270, p, 0, () => { shape(box(-120, -32, 240, 64, 32), C.red, { stroke: false }); txt('立即抢购', 0, 11, { size: 30, color: '#fff3ea', t: 99, t0: 0, cps: 0, shadow: 0 }); }); });
      ctx.restore();
    });
    // 左右两边：越来越多的“下单”提示
    for (let i = 0; i < 6; i++) { const st = 27.7 + i * 0.3; if (t < st) continue; const p = E.back(seg(t, st, st + 0.2), 2), L = i % 2 === 0, x = L ? 370 : 1360, y = 260 + Math.floor(i / 2) * 170; layer(seg(t, st, st + 0.1), () => at(x, y, p, L ? -0.04 : 0.04, () => { shape(box(-150, -40, 300, 80, 12), C.paper, { w: 4 }); txt('已下单 ×' + (i + 1), 0, 13, { size: 34, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 }); })); }
  }

  // ---------- 镜头 G（30.3–35.3）：两个同伴先说“我不干了”→ 手离开开关 → 65% 掉到 10% ----------
  function shotG(t) {
    labRoom({ clock: false });
    const go1 = E.in(seg(t, 31.0, 31.7)), go2 = E.in(seg(t, 31.45, 32.15));
    drawKid(1430, 700, 1.05, { ...EXPR, t, eyes: t > 31.2 ? 'wide' : 'dot', mouth: t > 31.2 ? 'o' : 'flat', look: [-1, 0.2], armL: 0.15, armR: 0.15 });
    drawKid(lerp(420, -300, go1), 720 - (t > 30.5 ? 20 : 0), 1.05, { hair: 2, shirt: C.teal, seed: 750, t, flip: go1 > 0 ? -1 : 1, eyes: 'dot', mouth: 'frown', brow: 0.6, armL: 0.3, armR: 0.3, legs: go1 > 0 ? t * 14 : 0, hop: go1 > 0 ? Math.abs(Math.sin(t * 14)) * 8 : 0 });
    drawKid(lerp(700, -300, go2), 720 - (t > 30.95 ? 20 : 0), 1.05, { hair: 6, shirt: C.navy, seed: 757, t, flip: go2 > 0 ? -1 : 1, eyes: 'dot', mouth: 'frown', brow: 0.6, armL: 0.3, armR: 0.3, legs: go2 > 0 ? t * 14 : 0, hop: go2 > 0 ? Math.abs(Math.sin(t * 14)) * 8 : 0 });
    const off = E.out(seg(t, 31.9, 32.3));
    drawKid(990, 720, 1.05, { ...SUBJ, t, eyes: off > 0.5 ? 'dot' : 'wide', mouth: off > 0.5 ? 'flat' : 'wave', look: t < 31.9 ? [-1, 0] : [0, 0], brow: off > 0.5 ? 0.3 : -0.5, sweat: 1 - off, armL: lerp(0.75, 1.6, off), armR: lerp(0.75, 1.6, off) });
    at(866, 640, 0.7, 0, () => { const g = generator(0, 0, 46, { down: 9 }); });
    say('我不干了。', 420, 300, seg(t, 30.5, 30.75) * (1 - seg(t, 31.6, 31.8)), { tx: -40, ty: 110, size: 46 });
    say('我也不干。', 760, 250, seg(t, 30.95, 31.2) * (1 - seg(t, 32.0, 32.2)), { tx: -40, ty: 110, size: 46 });
    // 65% → 10%
    const rp = seg(t, 32.0, 32.7), n = Math.round(lerp(65, 10, E.out(rp)));
    if (t > 31.8) red(() => layer(seg(t, 31.8, 32.0), () => txt(n + '%', 800, 330 + shakeAt(t, 32.7, 9), { size: 230, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 })));
  }

  const SH = [shotA, shotB, shotC, shotD, shotE, shotF, shotG];
  const TR = [[8.0, 8.4, 'splice'], [14.6, 15.0, 'splice'], [20.38, 20.42, 'cut'], [23.6, 24.1, 'zoom', { x: lampAt(8)[0], y: lampAt(8)[1], bx: 1250, by: 700 }], [27.0, 27.3, 'splice'], [30.0, 30.3, 'splice']];
  const CAPS = [
    ['有人让你电陌生人，你按到第几个？', 0.0, 3.0, 'c1', { cps: 0 }],
    ['隔壁在喊疼，他只说：请继续', 3.1, 5.45, 'c2'],
    ['1961 年，这个实验真做过', 5.85, 7.95, 'c3'],
    ['专家猜：千分之一按到底', 8.45, 10.75, 'c4'],
    ['结果 40 人里，{{26}} 个按到了底', 11.0, 14.55, 'c5'],
    ['电是假的，惨叫是录音', 15.25, 17.4, 'c6'],
    ['可按的人，手一直在抖', 17.55, 20.3, 'c7'],
    ['一句“出了事我负责”，就按了', 20.6, 23.55, 'c8'],
    ['今天它换了衣服：电话里的“警察”', 24.2, 27.0, 'c9'],
    ['直播间里的白大褂', 27.35, 29.95, 'c10'],
    ['身边有人先说“不”，按到底的只剩 {{10%}}', 30.35, 99, 'c11'],
  ];
  const A = (i, t) => () => shot(SH[i], t, BUF[0]), B = (i, t) => () => shot(SH[i], t, BUF[1]);
  SCENES.push({
    id: 'film', t0: -1, t1: 999,
    draw(t) {
      let i = 0; while (i < TR.length && t >= TR[i][1]) i++;
      if (i < TR.length && t >= TR[i][0]) T[TR[i][2]](seg(t, TR[i][0], TR[i][1]), A(i, t), B(i + 1, t), TR[i][3]);
      else film(shot(SH[i], t, BUF[0]));
    },
    caps(t) {
      for (const [s, a, b, id, o] of CAPS) cap(s, t, a, b, id, o);
      // 关注：一张贴在胶片上的档案标签，叠在最后一个画面
      const fp = seg(t, 33.1, 33.4);
      if (fp > 0) at(1340, lerp(-80, 190, E.back(fp, 1.3)), 1, 0.04, () => {
        const w = 480, h = 84;
        shape(box(-w / 2, -h / 2, w, h, 6), C.paper, { w: 4 });
        shape(box(-w / 2, -h / 2, 16, h, 0), C.red, { stroke: false });
        txt('关注，看下一个心理实验', 10, 12, { size: 34, color: C.ink, t, t0: 33.25, cps: 0.02, shadow: 0 });
      });
    },
  });

  // ---------- 音效事件 ----------
  const pan = x => clamp((x - 866) / 900, -0.8, 0.8);
  // A：放映机转动声贯穿全片；实验室底噪；每按一个开关：拨杆咔哒 + 电流嗡 + 电压表；墙那边的喊声是闷的；定格是胶片卡住 + 盖章
  ev(0.0, 'projector', { d: 35.3, g: 0.55 }); ev(0.0, 'labtone', { d: 8.0, g: 0.8 });
  PRESS.forEach((s, k) => { ev(s, 'toggle', { g: 0.9, pan: pan(160 + k * 46) }); ev(s + 0.02, 'zap', { d: 0.25 + k * 0.05, f: 1 + k * 0.08, g: 0.6 + k * 0.08 }); });
  ev(3.0, 'yell', { g: 0.9, pan: 0.6 }); ev(3.0, 'thump', { g: 0.8, pan: 0.7 }); ev(3.15, 'heart', { g: 0.8 }); ev(3.75, 'heart', { g: 0.8 });
  ev(3.6, 'pen', { g: 0.5, pan: -0.3 }); ev(4.4, 'heart', { g: 0.7 });
  ev(FZ, 'jam', { g: 0.9 }); ev(5.8, 'stamp', { f: 0.7, g: 1.5 });
  ev(7.95, 'splice', { g: 0.8 });
  // B：纸上的统计：举牌是木牌“哒”；小人一个个冒出来是打字机；变红是电流小“嗞”；65% 砸下来
  ev(8.4, 'papertone', { d: 6.2, g: 0.7 });
  [0, 1, 2].forEach(k => ev(8.6 + k * 0.18, 'woodtap', { f: 1 + k * 0.1, g: 0.7, pan: (k - 1) * 0.4 }));
  ev(9.2, 'chuckle', { g: 0.55 });
  ev(10.45, 'whoosh', { d: 0.35, up: false, g: 0.5 });
  for (let i = 0; i < 40; i += 2) ev(10.85 + i * 0.014, 'type', { g: 0.45, pan: pan(X0 + (i % 10) * DX) });
  for (let i = 0; i < 26; i++) ev(11.6 + i * 0.05, 'tickzap', { f: 0.9 + i * 0.02, g: 0.45, pan: pan(X0 + (i % 10) * DX) });
  ev(13.0, 'slam', { g: 1.0 }); ev(13.35, 'scratchpen', { d: 0.25, g: 0.7, pan: -0.6 });
  ev(14.55, 'splice', { g: 0.8 });
  // C：墙那边的录音（闷）→ 墙升起来是滑轮 + 磁带转动声清楚起来 → 报纸翻页 → 演员章；推近时心跳 + 紧张的笑
  ev(15.0, 'labtone', { d: 5.4, g: 0.7 }); ev(15.05, 'yell', { g: 0.7, pan: 0.7, muffle: 1 });
  ev(15.55, 'pulley', { d: 0.7, g: 0.8, pan: 0.5 }); ev(15.9, 'reel', { d: 4.4, g: 0.6, pan: 0.85 });
  ev(16.1, 'rustle', { g: 0.7, pan: 0.6 }); ev(16.3, 'stamp', { f: 0.8, g: 1.2, pan: 0.5 });
  ev(17.4, 'whoosh', { d: 0.6, g: 0.4 }); for (const s of [17.8, 18.3, 18.75, 19.2, 19.6, 20.0]) ev(s, 'heart', { g: 0.8 });
  ev(17.0, 'nervlaugh', { g: 0.75, pan: -0.4 }); ev(18.4, 'type', { g: 0.5, pan: 0.5 }); ev(18.5, 'type', { g: 0.45, pan: 0.5 });
  // D：一问一答，拍肩，按下
  ev(20.4, 'labtone', { d: 3.3, g: 0.7 }); ev(20.6, 'pop', { f: 0.9, pan: -0.4 }); ev(21.35, 'pop', { f: 0.75, pan: 0.4 });
  ev(21.7, 'pat', { g: 0.9, pan: 0.1 }); ev(22.92, 'toggle', { g: 1.0 }); ev(22.94, 'zap', { d: 0.5, f: 1.4, g: 1.0 });
  ev(23.6, 'zoomin', { d: 0.5, g: 0.8 });
  // E：深夜房间底（冰箱嗡）+ 电话里的“警察”（电话压缩音色的含糊人声）+ 提示音
  ev(24.1, 'nightroom', { d: 2.95, g: 0.8 }); ev(24.15, 'slideup', { g: 0.6 });
  ev(24.4, 'phonevoice', { d: 2.4, g: 0.6, pan: -0.5 }); ev(24.65, 'msg', { g: 0.6, pan: 0.4 }); ev(25.4, 'msg', { f: 1.3, g: 0.6, pan: 0.4 });
  for (const s of [24.5, 24.95, 25.4, 25.8, 26.15, 26.5]) ev(s, 'heart', { g: 0.7 });
  ev(26.95, 'splice', { g: 0.8 });
  // F：直播间的欢快吆喝 + 一串“叮”的下单提示
  ev(27.3, 'shopbed', { d: 2.7, g: 0.8 });
  for (let i = 0; i < 6; i++) ev(27.7 + i * 0.3, 'ding', { f: 1 + i * 0.06, g: 0.55, pan: i % 2 ? 0.5 : -0.5 });
  ev(29.95, 'splice', { g: 0.8 });
  // G：椅子挪开、脚步走远；手离开开关；数字往下滚，落地是一声低沉的定音
  ev(30.3, 'labtone', { d: 5.0, g: 0.8 });
  ev(30.45, 'chairscrape', { g: 0.8, pan: -0.5 }); ev(30.9, 'chairscrape', { g: 0.7, pan: -0.2, f: 1.1 });
  ev(31.0, 'woodstep', { d: 0.9, rate: 4.5, g: 0.6, pan: -0.6 }); ev(31.45, 'woodstep', { d: 0.9, rate: 4.8, f: 1.1, g: 0.55, pan: -0.4 });
  ev(31.95, 'cloth', { d: 0.3, g: 0.6 }); ev(32.0, 'counter', { d: 0.7, g: 0.8 }); ev(32.7, 'settledown', { g: 1.0 });
  ev(33.1, 'stamp', { f: 1.1, g: 0.7, pan: -0.3 }); ev(34.9, 'runout', { d: 0.5, g: 0.7 });
})();
