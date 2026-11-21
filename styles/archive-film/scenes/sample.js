// 风格样帧：?sample=1 开场电击发生器 / 2 揭晓 65% / 3 今天：电话里的“警察”
(() => {
  const N = +QS.get('sample'); window.DUR = 1;
  function s1(t) {
    labRoom({ clockX: 1480 });
    // 身后的白大褂
    drawKid(560, 640, 1.25, { coat: C.white, under: C.cream, tie: C.grayD, hair: 0, glasses: 1, eyes: 'dot', mouth: 'flat', brow: 0.2, look: [-0.6, 0.4], armL: 0.15, armR: 0.15, seed: 610 });
    speech(860, 190, 300, 120, { tx: 760, ty: 290 });
    txt('请继续。', 860, 210, { size: 54, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    const g = generator(866, 470, 46, { down: 0 });
    // 右上大字 450V
    red(() => txt('450V', 1372, 430, { size: 170, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
    // 悬在第一个开关上的手，有点抖
    hand(g.sx(0) + 14 + Math.sin(t * 31) * 2, 716, 1.05, 0.08, { sleeve: '#b9c3cc' });
  }
  function s2(t) {
    shape(box(0, 0, W, H), C.paper, { stroke: false });
    for (let x = 0; x < W; x += 60) line([[x, 0], [x, H]], { w: 1.5, color: '#c9b99a', alpha: 0.6 });
    for (let y = 0; y < H; y += 60) line([[0, y], [W, y]], { w: 1.5, color: '#c9b99a', alpha: 0.6 });
    // 左：专家预测
    txt('精神科医生预测', 330, 400, { size: 44, font: F.sans, weight: 700, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    txt('0.1%', 330, 560, { size: 150, font: F.serif, weight: 900, color: C.ink, t: 99, t0: 0, cps: 0, spacing: 0, shadow: 0 });
    txt('会按到底', 330, 640, { size: 44, font: F.sans, weight: 700, color: C.ink, t: 99, t0: 0, cps: 0, shadow: 0 });
    red(() => line([[170, 540], [500, 470]], { w: 12, color: C.red }));
    // 右：40 个人，26 个按到了 450V
    const X0 = 700, DX = 92, Y0 = 470, DY = 128;
    for (let i = 0; i < 40; i++) { const c = i % 10, r = Math.floor(i / 10); pict(X0 + c * DX, Y0 + r * DY, 1, i < 26 ? C.red : null); }
    red(() => txt('65%', 1110, 330, { size: 210, font: F.serif, weight: 900, color: C.red, t: 99, t0: 0, cps: 0, spacing: 0 }));
    line([[620, 260], [620, 860]], { w: 4, color: C.ink, alpha: 0.6 });
    note('YALE 1961  ·  N = 40', 150, 180, { color: '#5a4a38', size: 28, font: F.mono, weight: 700 });
  }
  function s3(t) {
    labRoom({ wall: '#7d7466', clock: false, gy: 860 });
    glowLight(1250, 470, 520, 520, { i: 0.7 });
    // 打电话的人：手机贴耳朵，冒汗
    drawKid(470, 860, 1.25, { hair: 1, shirt: C.mustard, eyes: 'wide', mouth: 'wave', brow: -0.7, look: [1, 0], sweat: 1, armR: 2.45, armL: 0.3, phone: 1, phoneOn: 1, seed: 640 });
    table(470, 900, 520, 150);
    bigPhone(1250, 470, 1.05, () => {
      txt('正在通话  03:47', 0, -250, { size: 26, font: F.sans, weight: 400, color: '#333', t: 99, t0: 0, cps: 0, shadow: 0 });
      shape(circ(0, -170, 46), '#9aa4aa', { stroke: false });
      txt('XX市公安局', 0, -86, { size: 44, font: F.sans, weight: 700, color: '#111', t: 99, t0: 0, cps: 0, shadow: 0 });
      txt('刑侦支队 · 王警官', 0, -44, { size: 28, font: F.sans, weight: 400, color: '#333', t: 99, t0: 0, cps: 0, shadow: 0 });
      shape(box(-130, 0, 260, 140, 18), '#ffffff', { w: 3, color: '#9aa4aa' });
      txt('你的账户涉嫌洗钱', 0, 56, { size: 30, font: F.sans, weight: 700, color: '#111', t: 99, t0: 0, cps: 0, shadow: 0 });
      txt('请立刻配合调查', 0, 104, { size: 30, font: F.sans, weight: 700, color: '#111', t: 99, t0: 0, cps: 0, shadow: 0 });
      red(() => { shape(box(-130, 190, 260, 80, 40), C.red, { stroke: false }); txt('转账到安全账户', 0, 242, { size: 30, font: F.sans, weight: 700, color: '#fff3ea', t: 99, t0: 0, cps: 0, shadow: 0 }); });
    });
    hand(1236 + Math.sin(t * 31) * 2, 775, 0.62, -0.05, { sleeve: C.mustard });
    note('2026', 150, 180, { color: C.sep, size: 30, font: F.mono, weight: 700 });
  }
  const CAPS = ['', '有人让你电一个陌生人，你按到第几个？', '结果 40 人里，{{26}} 个按到了底', '今天它换了身衣服：电话里说“我是警察”'];
  SCENES.push({ id: 's', t0: -1, t1: 99, draw(t) { film(shot([null, s1, s2, s3][N], t, BUF[0])); }, caps(t) { cap(CAPS[N], 9, 0, 20, 'c'); } });
})();
