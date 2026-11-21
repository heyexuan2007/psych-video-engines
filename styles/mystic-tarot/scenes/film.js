// 《巴纳姆效应》整片：神秘塔罗画风，39 秒，10 句字幕，镜头之间都是连续变形（牌缩小飞走、牌堆变书、书页飞出牌、拉远成牌海）
// 0–12 观众自己翻三张牌、打勾“说中了”；12–31.5 福勒 1948 实验（发牌 → 打分 4.26 → 39 张一模一样）；
// 31.5–35.5 原稿抄自星座书；35.5–39 三张牌复制成满屏牌海。字都在抖音安全区（x 134–1594，y 119–929）。
(() => {
  // 节奏表：画面和音效都按原始时间线（原长 39 秒）写；开头“说中你”的 0–12 秒压成 0–8 秒（1.5 倍），之后整体前移 4 秒
  const R0 = 12, R1 = 8;
  const tapeOf = t => t < R1 ? t * R0 / R1 : t + (R0 - R1);   // 真实时间 → 原始时间
  const timeOf = o => o < R0 ? o * R1 / R0 : o - (R0 - R1);   // 原始时间 → 真实时间
  window.DUR = 39.0 - (R0 - R1);
  const MASK = { num: 'XV', name: '面具', art: 'mask', lines: ['表面自律', '心里不安'] };
  const MIRROR = { num: 'VI', name: '镜子', art: 'mirror', lines: ['想被喜欢', '又挑剔自己'] };
  const SEED = { num: 'I', name: '种子', art: 'seed', lines: ['潜力很多', '还没发挥'] };
  const FACES = [MASK, MIRROR, SEED];
  const KID = { ink: PM.gold, hair: '#1a1f45', stick: PM.gold, paddle: '#f0e0bf', paddleInk: PM.crimson };
  const TCH = { ink: PM.gold, trouser: '#1a1f45', coat: '#1a1f45', tie: PM.crimson, skin: '#1a1f45', hairT: '#1a1f45' };
  const kid = (x, y, s, o = {}) => student(x, y, s, { pal: KID, col: '#1a1f45', skin: '#1a1f45', hair: '#1a1f45', face: false, ...o });

  // ---------- 三张牌的位置（开场） ----------
  const ROW = [[486, 400, -0.03], [866, 390, 0], [1246, 400, 0.03]];
  const FLIP = [3.0, 6.0, 9.0];           // 每张牌翻开的时刻
  const CHECK = [4.3, 7.4, 10.3];         // 打勾的时刻

  // ---------- 教室：39 个座位 ----------
  const SEAT = n => [560 + (n % 13) * 80, [430, 590, 750][Math.floor(n / 13)]];
  const HAND = [290 + 150 * 0.85, 800 - 330 * 0.85];
  // 39 个分数，平均 166/39 = 4.256 ≈ 4.26
  const SCORES = (() => { const a = [].concat(Array(18).fill(5), Array(14).fill(4), Array(6).fill(3), [2]); const r = rng(426); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; })();
  // 教室整体在第 7 句缩小下移，给星盘里的 4.26 让位
  const GA = [1040, 800];
  const classK = t => E.io(seg(t, 22.0, 22.8));
  const classG = t => lerp(1, 0.72, classK(t));
  const classTo = (t, x, y) => { const g = classG(t), ax = lerp(GA[0], 866, classK(t)); return [ax + (x - GA[0]) * g, GA[1] + (y - GA[1]) * g, g]; };
  function inClass(t, fn) { const g = classG(t), ax = lerp(GA[0], 866, classK(t)); at(ax, GA[1], g, 0, () => { ctx.translate(-GA[0], -GA[1]); fn(); }); }

  // ---------- 网格（第 8 句）：13 × 3 ----------
  const GRID = n => [190 + (n % 13) * 113, 255 + Math.floor(n / 13) * 200];

  // ---------- 星盘随镜头变化（关键帧插值） ----------
  // 每对相同的关键帧之间静止，不同的之间缓动
  const K = (t, cy, r, a) => [t, 866, cy, r, a];
  const RING = [K(0, 440, 470, 0.38), K(11.6, 440, 470, 0.38), K(13.2, 520, 560, 0.22), K(21.9, 520, 560, 0.22), K(23.0, 255, 175, 0.75), K(27.0, 255, 175, 0.75),
    K(28.2, 450, 520, 0.25), K(31.4, 450, 520, 0.25), K(32.6, 470, 470, 0.35), K(39, 470, 470, 0.35)];
  function ringAt(t) {
    for (let i = 0; i < RING.length - 1; i++) { const a = RING[i], b = RING[i + 1]; if (t <= b[0]) { const k = E.io(seg(t, a[0], b[0])); return a.map((v, j) => lerp(v, b[j], k)); } }
    return RING[RING.length - 1];
  }

  // ---------- 金线蜡烛 ----------
  function lineCandle(x, y, s, t, reach = 700) {
    const h = 250 * s, w = 64 * s, fl = 0.85 + 0.1 * Math.sin(t * 13.7 + x) + 0.05 * Math.sin(t * 31.1 + 1);
    glowLight(x, y - h - 40 * s, reach * fl, reach * 0.8 * fl, { i: 0.9, col: '#ffcf8a' });
    glowLight(x, y - h - 40 * s, 220 * fl, 190 * fl, { i: 0.6, col: '#fff0c8' });
    over(() => {
      // 烛台
      shape(oval(x, y, w * 1.7, w * 0.42), 'rgba(20,22,50,0.9)', { w: 2.5, color: PM.gold });
      shape(oval(x, y - 9 * s, w * 1.2, w * 0.3), 'rgba(20,22,50,0.9)', { w: 2, color: PM.gold });
      // 蜡身：深色填充 + 金线，蜡泪也是金线
      shape(() => { ctx.moveTo(x - w / 2, y - 10 * s); ctx.lineTo(x - w / 2, y - h); ctx.quadraticCurveTo(x, y - h - 12 * s, x + w / 2, y - h); ctx.lineTo(x + w / 2, y - 10 * s); ctx.closePath(); }, '#1c1f48', { w: 2.5, color: PM.goldL });
      for (const [dx, len] of [[-0.28, 60], [0.12, 96], [0.36, 38]]) line([[x + dx * w, y - h + 2], [x + dx * w, y - h + len * s]], { w: 2, color: PM.gold });
      for (let k = 1; k < 5; k++) line([[x - w / 2 + 6, y - h + k * h / 5], [x - w / 2 + 14, y - h + k * h / 5]], { w: 1.2, color: PM.gold, alpha: 0.5 });
      line([[x, y - h - 4 * s], [x + 2, y - h - 20 * s]], { w: 3, color: '#0b0d22' });
      const fx = x + Math.sin(t * 7.3 + x) * 3 * s, fy = y - h - 20 * s, fh = 66 * s * fl;
      const gr = ctx.createRadialGradient(fx, fy - fh * 0.3, 0, fx, fy - fh * 0.3, fh * 1.7); gr.addColorStop(0, 'rgba(255,214,130,0.5)'); gr.addColorStop(1, 'rgba(255,214,130,0)');
      ctx.save(); ctx.globalAlpha = LA; ctx.fillStyle = gr; ctx.fillRect(fx - fh * 2, fy - fh * 2, fh * 4, fh * 4); ctx.restore();
      shape(() => { ctx.moveTo(fx, fy - fh); ctx.bezierCurveTo(fx + 20 * s, fy - fh * 0.4, fx + 17 * s, fy + 8 * s, fx, fy + 8 * s); ctx.bezierCurveTo(fx - 17 * s, fy + 8 * s, fx - 20 * s, fy - fh * 0.4, fx, fy - fh); }, '#ffb648', { stroke: false });
      shape(() => { ctx.moveTo(fx, fy - fh * 0.6); ctx.bezierCurveTo(fx + 9 * s, fy - fh * 0.25, fx + 7 * s, fy + 4 * s, fx, fy + 4 * s); ctx.bezierCurveTo(fx - 7 * s, fy + 4 * s, fx - 9 * s, fy - fh * 0.25, fx, fy - fh * 0.6); }, '#fff4d2', { stroke: false });
      smoke(t, fx, fy - fh, 420 * s, x * 0.01, 0.12);
    });
  }
  function candles(t, a = 1) { layer(a, () => { lineCandle(150, 1010, 0.9, t, 720); lineCandle(1610, 1010, 0.75, t + 1.7, 620); }); }

  // ---------- 小纸条“你中了几句？” ----------
  function slip(t) {
    const p = E.back(seg(t, 10.0, 10.35)), out = seg(t, 11.7, 12.0);
    if (p <= 0 || out >= 1) return;
    over(() => layer(1 - out, () => at(1400, 175, p, 0.07, () => {
      shape(box(-170, -46, 340, 92, 4), PM.parch, { w: 2.5, color: PM.goldD });
      line([[-150, -30], [150, -30]], { w: 1, color: PM.goldD, alpha: 0.5, dash: [4, 6] });
      txt('你中了几句？', 0, 16, { size: 44, font: F.serif, weight: 900, color: '#3a1230', t: 99, t0: 0, cps: 0, shadow: 0 });
    })));
  }

  // ---------- 一周：七个月相从左划到右 ----------
  function moons(t) {
    const p = seg(t, 17.0, 18.6); if (p <= 0 || p >= 1) return;
    over(() => {
      for (let k = 0; k < 7; k++) {
        const a = seg(p, k * 0.1, k * 0.1 + 0.2) * (1 - seg(p, 0.82, 1)), x = 500 + k * 150, y = 160;
        if (a <= 0) continue;
        layer(a, () => {
          ctx.save(); ctx.shadowColor = PM.goldL; ctx.shadowBlur = 16;
          shape(circ(x, y, 26), '#f3e3b8', { w: 2, color: PM.goldL }); ctx.restore();
          const ph = -1 + k / 3;   // −1 新月 … +1 满月
          ctx.save(); ctx.globalAlpha = LA * 0.92; ctx.fillStyle = '#10133a'; ctx.beginPath(); ctx.arc(x, y, 27, 0, Math.PI * 2); ctx.ellipse(x + ph * 26, y, 27, 27, 0, 0, Math.PI * 2, true); ctx.fill('evenodd'); ctx.restore();
        });
      }
    });
  }

  // ---------- 书：closed→open（0..1），hl 高亮进度 ----------
  const PAGE_LINES = ['你表面自律，心里不安。', '你想被喜欢，又挑剔自己。', '你潜力很多，还没发挥。'];
  const PAGE_Y = [-120, 20, 160];
  function book(cx, cy, s, op, hl) {
    const o = E.io(op), spine = cx - 210 * s * (1 - o);
    const pageR = () => {
      shape(box(0, -280, 430, 560, 6), PM.parch, { w: 3, color: PM.goldD });
      txt('· 本月运势 ·', 215, -222, { size: 26, font: F.serif, weight: 900, color: '#7a5a3a', t: 99, t0: 0, cps: 0, shadow: 0 });
      for (let k = 0; k < 9; k++) { const y = -170 + k * 50; if (PAGE_Y.some(py => Math.abs(py - (y + 20)) < 30)) continue; line([[26, y + 8], [26 + 340 + hash(k) * 40, y + 8]], { w: 6, color: '#b9a582', alpha: 0.7 }); }
      PAGE_Y.forEach((py, i) => {
        const h = seg(hl, i * 0.25, i * 0.25 + 0.45);
        if (h > 0) shape(box(16, py - 30, 396 * h, 42, 4), rgba(PM.goldL, 0.55), { stroke: false });
        txt(PAGE_LINES[i], 24, py, { size: 25, font: F.serif, weight: 900, color: '#3a2412', align: 'left', t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0 });
      });
    };
    const pageL = () => {
      shape(box(-430, -280, 430, 560, 6), PM.parch, { w: 3, color: PM.goldD });
      at(-215, -60, 1, 0, () => { ctx.save(); ctx.globalAlpha = LA; astrolabeInk(0, 0, 130); ctx.restore(); });
      for (let k = 0; k < 4; k++) line([[-400, 130 + k * 36], [-60 - hash(k + 9) * 80, 130 + k * 36]], { w: 6, color: '#b9a582', alpha: 0.7 });
    };
    const cover = () => {
      shape(box(0, -290, 430, 580, 10), PM.purple, { w: 4, color: PM.gold, shade: [-14, 0] });
      shape(box(18, -272, 394, 544, 6), null, { w: 1.5, color: PM.gold });
      ctx.save(); ctx.globalAlpha = LA; astrolabe(215, -40, 140, 0.3, 0.9); ctx.restore();
      txt('星座运势', 215, 205, { size: 60, font: F.serif, weight: 900, color: PM.goldL, t: 99, t0: 0, cps: 0, shadow: 0, spacing: 0.2 });
    };
    at(spine, cy, s, 0, () => {
      shape(box(-6, -292, 12, 584, 4), PM.goldD, { stroke: false });
      if (o < 0.5) { pageR(); ctx.save(); ctx.scale(Math.max(0.02, Math.cos(Math.PI * o)), 1); cover(); ctx.restore(); }
      else { pageR(); ctx.save(); ctx.scale(Math.max(0.02, -Math.cos(Math.PI * o)), 1); pageL(); ctx.restore(); }
    });
    return (i) => [spine + 215 * s, cy + (PAGE_Y[i] - 10) * s];   // 第 i 行在屏幕上的位置
  }
  /** 书页上的墨线小星盘 */
  function astrolabeInk(x, y, r) {
    ctx.strokeStyle = '#7a5a3a'; ctx.lineWidth = 2;
    for (const rr of [r, r * 0.8, r * 0.4]) { ctx.beginPath(); ctx.arc(x, y, rr, 0, Math.PI * 2); ctx.stroke(); }
    for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r * 0.4, y + Math.sin(a) * r * 0.4); ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); ctx.stroke(); }
    for (let i = 0; i < 12; i++) { const a = (i + 0.5) / 12 * Math.PI * 2; glyph(i, x + Math.cos(a) * r * 0.9, y + Math.sin(a) * r * 0.9, 0.5, '#7a5a3a'); }
  }

  // ---------- 牌海用的贴图（三种牌面 + 下面的“说中了”） ----------
  const SPR = {};
  function sprite(i) {
    if (SPR[i]) return SPR[i];
    const c = document.createElement('canvas'); c.width = CW + 40; c.height = CH + 150; const g = c.getContext('2d');
    const keep = ctx; ctx = g; LA = 1;
    at(c.width / 2, CH / 2 + 20, 1, 0, () => {
      cardFace(FACES[i]);
      at(0, CH / 2 + 62, 1, 0, () => { shape(box(-104, -30, 60, 60, 8), rgba(PM.gold, 0.25), { w: 4, color: PM.goldL }); tick(-74, -2, 0.82, 1, PM.goldL, 10); txt('说中了', 14, 18, { size: 46, font: F.serif, weight: 900, color: PM.goldL, align: 'left', t: 99, t0: 0, cps: 0, shadow: 0 }); });
    });
    ctx = keep; SPR[i] = c; return c;
  }

  // ======================= 主镜头 =======================
  function scene(t) {
    const [, rcx, rcy, rr, ra] = ringAt(t);
    mysticBG(t, { cx: rcx, cy: rcy, r: rr, ringA: ra });

    // ---------------- 0–12：三张牌 ----------------
    if (t < 13.4) {
      const gather = E.io(seg(t, 12.0, 13.2));    // 第 5 句：三张牌收成一叠飞到老师手里
      glowLight(866, 420, 720, 440, { i: 0.5 * (1 - gather), col: '#ffe2b8' });
      // 第一帧的大牌：2.5–3.0 缩到左边位置，3.0 翻开
      FACES.forEach((f, i) => {
        let [x, y, rot] = ROW[i], s = 0.9, fl = seg(t, FLIP[i], FLIP[i] + 0.4), a = 1;
        if (i === 0) { const m = E.io(seg(t, 2.4, 3.0)); x = lerp(866, x, m); y = lerp(455, y, m); s = lerp(1.2, 0.9, m); rot = lerp(-0.02, rot, m); }
        else { const d = E.out(seg(t, 2.5 + i * 0.15, 3.0 + i * 0.15)); if (d <= 0) return; x = lerp(1700, x, d); y = lerp(1150, y, d); rot = lerp(0.6, rot, d); }
        if (gather > 0) { const q = E.io(seg(t, 12.0 + i * 0.08, 13.0 + i * 0.08)); x = lerp(x, HAND[0] + i * 3, q); y = lerp(y, HAND[1] - i * 4, q); s = lerp(s, 0.16, q); rot = lerp(rot, 0.2, q); }
        const lift = Math.sin(Math.PI * fl) * 0.06;
        const ck = seg(t, CHECK[i], CHECK[i] + 0.45), lit = seg(t, CHECK[i] + 0.4, CHECK[i] + 0.8) * (1 - gather);
        layer(a, () => tarot(x, y, s * (1 + lift), { face: f, back: i === 0 ? { label: '致 · 你' } : {}, flip: fl, rot, lit: i === 0 && t < 2.6 ? 0.55 * (1 - seg(t, 2.2, 2.6)) : lit * 0.8, check: fl >= 1 && gather < 0.05 ? ck : null }));
      });
      slip(t);
    }

    // ---------------- 12–27：教室 ----------------
    if (t >= 12.4 && t < 29.0) {
      const inA = seg(t, 12.4, 13.0), outT = seg(t, 22.0, 22.6);
      glowLight(980, 560, 900, 420, { i: 0.45, col: '#d8d0ff' });
      // 老师
      if (outT < 1) layer(inA * (1 - outT), () => teacher(290 - outT * 120, 800, 0.85, { pal: TCH, papers: (x, y) => { const left = 39 - Math.floor(clamp((t - 18.2) / 2.4) * 39); for (let k = 0; k < Math.min(4, Math.ceil(left / 10)); k++) tarot(x + k * 3, y - k * 4, 0.16, { back: {}, rot: 0.2 }); } }));
      const dim = 1 - 0.75 * seg(t, 27.3, 28.0) - 0.25 * seg(t, 28.4, 28.95);
      inClass(t, () => {
        for (let n = 0; n < 39; n++) {
          const [x, y] = SEAT(n), j = Math.floor(n / 13), app = E.out(seg(t, 12.8 + j * 0.35 + (n % 13) * 0.03, 13.3 + j * 0.35 + (n % 13) * 0.03));
          if (app <= 0) continue;
          const raise = E.out(seg(t, 23.0 + hash(n * 7.1) * 1.4, 23.4 + hash(n * 7.1) * 1.4)) * (1 - seg(t, 27.0, 27.4));
          layer(app * dim, () => kid(x, y + (1 - app) * 30, 0.36, { seed: 90 + n * 3, arm: raise, num: SCORES[n] }));
          // 第 5 句：写测试的小纸 + 金色笔迹
          const sheet = seg(t, 13.6, 13.9) * (1 - seg(t, 17.8, 18.2));
          if (sheet > 0) layer(sheet * app, () => {
            shape(box(x - 15, y - 44, 30, 36, 2), PM.parch, { w: 1.5, color: PM.goldD });
            const w = clamp((t - 14.0 - hash(n) * 0.8) / 1.6);
            for (let k = 0; k < 3; k++) { const ww = clamp(w * 3 - k); if (ww > 0) line([[x - 10, y - 34 + k * 9], [x - 10 + 20 * ww, y - 34 + k * 9 + Math.sin(k + n) * 1.5]], { w: 1.6, color: '#3a2412' }); }
          });
        }
      });
      // 第 6 句：发牌（每张牌从老师手里飞到座位）
      for (let n = 0; n < 39; n++) {
        const t0 = 18.2 + n * 0.062, p = seg(t, t0, t0 + 0.5);
        if (p <= 0 || t >= 27.2 + n * 0.018) continue;
        const [sx, sy] = SEAT(n), [tx, ty, g] = classTo(t, sx, sy - 22);
        if (p < 1) {
          const c = [(HAND[0] + tx) / 2, Math.min(HAND[1], ty) - 220], P = qd(HAND, c, [tx, ty], 24), q = P[Math.round(E.io(p) * 24)];
          tarot(q[0], q[1], 0.1, { back: {}, rot: p * 7 });
        } else tarot(tx, ty, 0.1 * g, { back: {}, rot: (hash(n) - 0.5) * 0.3 });
      }
      over(() => {
        const la = seg(t, 13.4, 13.9) * (1 - seg(t, 21.8, 22.3));
        if (la > 0) txt('1948 · 福勒的课堂 · 39 名学生', 1040, 250, { size: 40, font: F.serif, weight: 900, color: PM.lav, t: 99, t0: 0, cps: 0, spacing: 0.08, alpha: la });
      });
      moons(t);
      // 第 7 句：星盘里数到 4.26
      const na = seg(t, 23.0, 23.4) * (1 - seg(t, 27.0, 27.5));
      if (na > 0) over(() => layer(na, () => {
        const v = 4.26 * E.out(seg(t, 23.4, 25.2)), done = t >= 25.2;
        txt('1948 · 福勒的课堂', 866, 150, { size: 30, font: F.serif, weight: 900, color: PM.lav, t: 99, t0: 0, cps: 0, spacing: 0.1 });
        at(866, 302, 1 + 0.12 * Math.sin(Math.PI * seg(t, 25.2, 25.5)), 0, () => {
          txt(v.toFixed(2), 100, 0, { size: 140, font: F.lat, weight: 900, color: PM.goldL, glow: done ? 1 : 0.4, t: 99, t0: 0, cps: 0, spacing: 0, align: 'right' });
          txt('/ 5', 118, 0, { size: 60, font: F.lat, weight: 900, color: PM.gold, t: 99, t0: 0, cps: 0, spacing: 0, align: 'left', alpha: seg(t, 25.2, 25.5) });
        });
        txt('39 人的平均准确度', 866, 360, { size: 30, font: F.serif, weight: 900, color: PM.parch, t: 99, t0: 0, cps: 0, spacing: 0.1, alpha: seg(t, 25.4, 25.8) });
      }));
    }

    // ---------------- 27–32.4：39 张牌升到网格，一张张翻开，全是同一张 ----------------
    if (t >= 27.2 && t < 32.6) {
      glowLight(866, 450, 900, 420, { i: 0.5 * seg(t, 27.6, 28.4), col: '#ffe2b8' });
      for (let n = 0; n < 39; n++) {
        const i = n % 13, j = Math.floor(n / 13);
        const up = E.io(seg(t, 27.2 + n * 0.018, 28.0 + n * 0.018));
        const [sx, sy] = SEAT(n), [ax, ay, g] = classTo(t, sx, sy - 22), [gx, gy] = GRID(n);
        let x = lerp(ax, gx, up), y = lerp(ay, gy, up) - Math.sin(Math.PI * up) * 60, s = lerp(0.1 * g, 0.34, up);
        const fl = seg(t, 28.4 + i * 0.07 + j * 0.12, 28.75 + i * 0.07 + j * 0.12);
        const pile = E.io(seg(t, 31.5 + n * 0.012, 32.1 + n * 0.012));
        if (pile > 0) { x = lerp(x, 866 + (hash(n) - 0.5) * 20, pile); y = lerp(y, 470 + (hash(n + 3) - 0.5) * 20, pile); s = lerp(s, 0.3, pile); }
        const pulse = Math.max(0, Math.sin(Math.PI * seg(t, 29.9, 30.9)));
        layer(1 - seg(t, 32.1, 32.4), () => tarot(x, y, s, { face: MASK, back: {}, flip: fl, rot: lerp((hash(n) - 0.5) * 0.3, 0, up) + pile * (hash(n + 5) - 0.5) * 0.4, lit: fl >= 1 ? 0.2 + 0.5 * pulse : 0 }));
      }
    }

    // ---------------- 31.5–36.2：星座书 ----------------
    let lineAt = null;
    if (t >= 32.0 && t < 36.6) {
      const pop = E.back(seg(t, 32.0, 32.45)), out = seg(t, 35.6, 36.2);
      glowLight(866, 470, 700, 500, { i: 0.55, col: '#ffe2b8' });
      layer(1 - out, () => { lineAt = book(866, 480, 0.95 * pop, seg(t, 32.8, 33.5), seg(t, 33.7, 35.0)); });
      over(() => note('Forer, 1949 · 他发的人格描述共 13 句，大半取自报摊上的星座书', 300, 965, { t, t0: 33.8, alpha: 1 - out, color: '#a9a2c8' }));
    }

    // ---------------- 35.5–39：三句从书里飞出来变回三张牌 → 拉远成牌海 ----------------
    if (t >= 35.5) {
      const z = E.io(seg(t, 36.5, 38.2)), zs = lerp(1, 0.16, z);
      camera(866, 400, zs, () => {
        glowLight(866, 420, 720, 440, { i: 0.5, col: '#ffe2b8' });
        if (z > 0) {
          for (let j = -6; j <= 6; j++) for (let i = -17; i <= 17; i++) {
            if (j === 0 && Math.abs(i) <= 1) continue;
            const d = Math.hypot(i, j * 1.6), ap = seg(t, 36.5 + d * 0.06, 36.8 + d * 0.06);
            if (ap <= 0) continue;
            const S = sprite((((i + j) % 3) + 3) % 3), x = 866 + i * 380, y = 400 + j * 640;
            ctx.save(); ctx.globalAlpha = LA * ap; ctx.translate(x, y); ctx.scale(0.9, 0.9); ctx.drawImage(S, -S.width / 2, -CH / 2 - 20); ctx.restore();
          }
        }
        FACES.forEach((f, i) => {
          const fly = E.io(seg(t, 35.5 + i * 0.12, 36.3 + i * 0.12));
          const [rx, ry, rot] = ROW[i];
          const from = lineAt ? lineAt(i) : [866, 480];
          const x = lerp(from[0], rx, fly), y = lerp(from[1], ry, fly), s = lerp(0.12, 0.9, fly);
          tarot(x, y, s, { face: f, flip: 1, rot: lerp(0, rot, fly), lit: fly * (1 - z * 0.6), check: fly >= 1 ? 1 : null });
        });
      }, 866 - W / 2, 400 - H / 2);
      // 关注：叠在最后一个画面上
      const fa = seg(t, 37.4, 37.9);
      if (fa > 0) over(() => layer(fa, () => at(866, 190, E.back(fa), 0, () => {
        shape(box(-230, -44, 460, 88, 12), 'rgba(8,10,30,0.95)', { w: 2.5, color: PM.goldL });
        star(-195, 0, 12, PM.goldL, null); star(195, 0, 12, PM.goldL, null);
        txt('关注 · 下一张牌下期翻', 0, 14, { size: 40, font: F.serif, weight: 900, color: PM.goldL, t: 99, t0: 0, cps: 0, shadow: 0 });
      })));
    }

    candles(t, 1 - seg(t, 36.6, 37.6) * 0.7);
  }

  // ---------- 字幕 ----------
  // 字幕按真实时间写（开头三句改成牌上的短句，2 秒一句也读得完）
  const CAPS = [
    ['c1', -0.5, 1.7, '刷到这条的你——'],
    ['c2', 1.75, 3.75, '你表面自律，心里不安。'],
    ['c3', 3.8, 5.95, '你想被喜欢，又挑剔自己。'],
    ['c4', 6.0, 7.95, '你潜力很多，还没发挥。'],
    ['c5', 8.0, 12.9, '1948 年，福勒给 39 个学生做性格测试。'],
    ['c6', 13.0, 17.9, '一周后，每人拿到一份“专属”分析。'],
    ['c7', 18.0, 22.9, '准不准？满分 5 分，平均打了 4.26。'],
    ['c8', 23.0, 27.4, '可这 39 份，一字不差。'],
    ['c9', 27.5, 31.4, '大半是从星座书上抄的。'],
    ['c10', 31.5, 34.7, '刚才那三句，每个人刷到的都一样。'],
  ];

  SCENES.push({ id: 'film', t0: -1, t1: 99, draw(t) {
    put(shot(scene, tapeOf(t), BUF[0]));
    for (const [id, a, b, s] of CAPS) mysticCap(s, t, a, b, id);
    // 结尾 0.35 秒压暗收住（不一帧跳黑）
    veil(seg(t, 34.65, 35.0) * 0.85, '#05060f');
  } });

  // ---------- 音效事件 ----------
  const EV0 = EV.length;
  ev(0, 'bed', { d: 35.0, g: 1.0, at: 0 });
  ev(0.0, 'bowl', { f: 196, g: 0.8, vary: 0 });
  ev(0.3, 'ratchet', { d: 2.0, g: 0.35 });
  ev(2.4, 'air', { d: 0.7, g: 0.5 });
  ev(2.65, 'deal', { g: 0.7, pan: 0.5 }); ev(2.8, 'deal', { g: 0.7, pan: 0.6 });
  FLIP.forEach((f, i) => { ev(f, 'cardflip', { g: 0.9, pan: [-0.4, 0, 0.4][i] }); ev(CHECK[i], 'quill', { g: 0.8, pan: [-0.4, 0, 0.4][i] }); ev(CHECK[i] + 0.42, 'glint', { f: [1, 1.12, 1.26][i], g: 0.7, pan: [-0.4, 0, 0.4][i], vary: 0 }); });
  ev(10.0, 'paperslip', { g: 0.6, pan: 0.6 });
  ev(12.0, 'riffle', { g: 0.8, pan: -0.3 });
  ev(12.5, 'ratchet', { d: 1.0, g: 0.4 });
  ev(12.8, 'murmur', { d: 4.2, g: 0.35 });
  ev(14.0, 'quillbed', { d: 2.6, g: 0.55 });
  ev(17.0, 'chimes', { d: 1.6, g: 0.6, vary: 0 });
  for (let n = 0; n < 39; n++) ev(18.2 + n * 0.062, 'deal', { g: 0.32, pan: lerp(-0.4, 0.6, (n % 13) / 12) });
  ev(22.0, 'air', { d: 1.0, g: 0.5, up: false });
  ev(22.2, 'ratchet', { d: 0.9, g: 0.45 });
  ev(23.0, 'paddles', { d: 1.6, g: 0.6 });
  ev(23.4, 'counter', { d: 1.8, g: 0.5, vary: 0 });
  ev(25.2, 'gong', { g: 0.85, vary: 0 });
  ev(27.2, 'air', { d: 1.0, g: 0.5 });
  ev(28.4, 'cascade', { n: 39, d: 1.6, g: 0.65 });
  ev(29.4, 'revswell', { d: 0.5, g: 0.6, vary: 0 });
  ev(29.9, 'thud', { g: 0.85, vary: 0 });
  ev(29.9, 'choir', { d: 1.8, g: 0.45, vary: 0 });
  ev(31.5, 'riffle', { g: 0.8 });
  ev(32.0, 'bookdrop', { g: 0.75 });
  ev(32.8, 'bookopen', { g: 0.8 });
  for (let i = 0; i < 3; i++) ev(33.7 + i * 0.42, 'marker', { g: 0.55, pan: 0.2 });
  ev(35.5, 'air', { d: 0.9, g: 0.5 });
  ev(35.6, 'glint', { f: 1.26, g: 0.5, vary: 0 });
  ev(36.5, 'flutter', { d: 1.8, g: 0.6 });
  ev(36.6, 'bowl', { f: 147, g: 0.75, vary: 0 });
  // 事件时间换成真实时间（bed 本来就按真实时间）
  for (let i = EV0; i < EV.length; i++) if (EV[i].s !== 'bed') EV[i].t = +timeOf(EV[i].t).toFixed(3);
})();
