# -*- coding: utf-8 -*-
"""
第 7 镜「第二十一句歌词」（成片 21.59–26.00，A 水彩回忆）+ T2（26.00–30.28，A→C 慢慢褪色）。
窗边双人中近景（腰部以上），白天：窗外是小雪和远处落了雪的屋顶，晨光从窗户照进来。她在左边朝右，他在右边朝左，
窗在他身后右侧。镜头全程极慢推近（pen.view 1.0 → 1.06，A、C 两侧同一个取景）。

表演（成片秒）：
  21.70 他低头靠近；22.75「亲」嘴唇贴到她额头，她闭眼；24.11「温」她睁开眼抬头看着他，温柔地笑（醒着的，不是梦）。
  25.75–26.5 她把脸靠在他胸口，闭着眼很安心（hug）；27.0–28.2 他的眼睛慢慢转向窗外；27.6 一只小鸟落在窗台上
  （他低头看它），28.7 飞走、飞出画面（他抬眼目送）；29.21–30.3「这一句」他的手臂慢慢松开、垂下。她还闭着眼。
画面上会动的东西：窗外的雪、窗台上茶杯的热气、光里浮着的光斑（尘）、右边纱帘轻轻摆、小鸟。
A：淡彩、留白多（笔刷自己把四周淡成纸白）；C（T2 褪色的目标）：同一画面的水墨版，红色只有她的红豆发夹，他也是上色完成的人。

draw(pen, **kw)  kw：t 覆盖表演时间；k / up / hug / away / loosen 覆盖表演参数（0..1，单独看某个姿势用）；zoom 覆盖推近量
"""
import math

import numpy as np

import characters as ch
from core import densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, ease_io, ease_out, ease_in, lerp, W, H

T0, T1 = 21.59, 30.28
ZOOM = (1.0, 1.06)
ZC = (930.0, 430.0)                  # 推近的中心（两人的头之间）
GIRL = dict(x=760.0, y=545.0, s=200.0)
WIN = (1210, 70, 1850, 792)          # 窗框外沿
GLASS = (1238, 98, 1822, 748)        # 玻璃
MULL_X = 1530                        # 竖棂
TRANS_Y = 300                        # 横棂
SILL = 748                           # 窗台面
LEDGE = (1238, 716, 1822, 748)       # 窗外的石头窗沿（透过玻璃看见），小鸟落在这里
BIRD_AT = (1606.0, 716.0)            # 小鸟落脚点（脚底）
T_BIRD_IN, T_BIRD_LAND, T_BIRD_OFF = 27.30, 27.60, 28.70
BG_BOIL = 0.4


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def P(pts):
    return np.float32(pts)


# ================================================================= 表演
def perf(t, kw=None):
    """→ couple() 的参数 dict + 鸟。"""
    kw = kw or {}
    k = float(ease_io((t - 21.70) / 1.05))                    # 21.70 → 22.75 嘴唇贴上
    up = float(ease_io((t - 24.00) / 0.55))                   # 24.11「温」睁眼抬头
    hug = float(ease_io((t - 25.75) / 0.80))                  # 靠进他怀里
    away = float(ease_io((t - 27.00) / 1.20))                 # 他望向窗外
    loosen = float(ease_io((t - 29.21) / 1.05))               # 手臂松开
    for nm in ('k', 'up', 'hug', 'away', 'loosen'):
        if kw.get(nm) is not None:
            v = float(kw[nm])
            k, up, hug, away, loosen = [v if nm == n else x for n, x in
                                        zip(('k', 'up', 'hug', 'away', 'loosen'), (k, up, hug, away, loosen))]
    p = dict(GIRL, k=k, look_up=up, hug=hug, look_away=away, loosen=loosen, breath=(t + 0.3) / 3.6, light=1,
             seed=1000, boy_seed=2000)
    # 她：亲完睁眼时眨一下；靠在怀里时安心地闭着眼
    p['blink'] = float(np.clip(1.0 - abs(t - 25.15) / 0.10, 0, 1)) * (1 - hug)
    # 他：抱着她时 gentle；转向窗外时出神，视线跟着鸟：先望雪 → 低头看窗台上的鸟 → 抬眼目送它飞走
    if hug > 0.01 and kw.get('his_face') is None:
        land = float(ease_io((t - T_BIRD_LAND + 0.15) / 0.4))
        off = float(ease_io((t - T_BIRD_OFF) / 0.5))
        gy = lerp(lerp(0.05, 0.55, land), -0.35, off)
        look = dict(ch.EXPR['distant'], gx=0.55, gy=gy, open=lerp(0.62, 0.72, off))
        p['his_face'] = ch.mix_expr('gentle', look, away)
        p['away_pitch'] = lerp(lerp(-4.0, 9.0, land), -12.0, off)
        p['away_yaw'] = -28.0 - 6.0 * off
        p['boy_blink'] = float(np.clip(1.0 - abs(t - 29.6) / 0.10, 0, 1))
    return p


def zoom_at(t, kw=None):
    if kw and kw.get('zoom') is not None:
        return float(kw['zoom'])
    u = clamp((t - T0) / (T1 - T0))
    return ZOOM[0] + (ZOOM[1] - ZOOM[0]) * float(0.5 * u + 0.5 * smooth01(u))


# ================================================================= 背景
def _wall(pen):
    s = 100
    pen.fill(rect(-20, -20, W + 20, H + 20), 'wall', seed=s, c_fade=False, tone=0.10,
             rgrad=(1300, 420, 300, 1500, 0.2, 1.0))
    # 墙上的小相框（两个人的合影，草草几笔）
    x0, y0, x1, y1 = 236, 168, 386, 318
    pen.shade(P([[x0 + 8, y1], [x1 + 8, y1], [x1 + 8, y1 + 8], [x0 + 8, y1 + 8]]), amount=0.25, seed=s + 1,
              hatch=False, soft=4.0)
    fr = P([[x0, y0], [x1, y0 + 2], [x1 + 1, y1], [x0 - 1, y1 - 1]])
    pen.cover(fr, seed=s + 2, feather=0.7)
    pen.fill(fr, 'wood', seed=s + 3, tone=0.30)
    inner = P([[x0 + 16, y0 + 16], [x1 - 16, y0 + 17], [x1 - 15, y1 - 16], [x0 + 15, y1 - 16]])
    pen.cover(inner, seed=s + 4, feather=0.6)
    pen.fill(inner, 'sky', seed=s + 5, tone=0.08)
    for i, hx in enumerate((x0 + 58, x0 + 92)):
        pen.line(ell(hx, y0 + 64 + 2 * i, 11, 13, 0, 330, 10), 2.4, tone=0.45, seed=s + 10 + i, role='detail',
                 taper=(0.1, 0.3))
        pen.line(P([(hx - 17, y1 - 18), (hx - 12, y0 + 84), (hx + 12, y0 + 84), (hx + 17, y1 - 18)]), 2.4,
                 tone=0.42, seed=s + 12 + i, role='detail', taper=(0.1, 0.1))
    pen.line(D([(x0, y0), (x1, y0 + 2), (x1 + 1, y1), (x0 - 1, y1 - 1)], 20, closed=True), 4.5, tone=0.8,
             color='wood_d', seed=s + 14, closed=True, taper=(0, 0), head=0.4)
    pen.line(P([(x0 + 30, y0), ((x0 + x1) / 2, y0 - 34), (x1 - 30, y0 + 2)]), 2.0, tone=0.5, seed=s + 15,
             taper=(0.1, 0.1), role='detail')
    pen.dot((x0 + x1) / 2, y0 - 35, 3.5, color='ink', tone=0.8, seed=s + 16)
    # 左边角落：一个木花架，上面一盆垂下来的绿萝
    pen.line(D([(150, 600), (152, 1100)], 30), 9, tone=0.7, color='wood_d', seed=s + 20, taper=(0.05, 0.6),
             fade=0.6, dry=0.5, dry_from=0.5)
    top = P([[90, 590], [250, 588], [252, 604], [88, 606]])
    pen.cover(top, seed=s + 21, feather=0.7)
    pen.fill(top, 'wood', seed=s + 22)
    pen.line(D([(86, 590), (254, 587)], 20), 6, tone=0.85, color='wood_d', seed=s + 23, taper=(0.05, 0.2))
    pot = P([[124, 536], [214, 536], [204, 590], [134, 590]])
    pen.cover(pot, seed=s + 24, feather=0.7)
    pen.fill(pot, 'terra', seed=s + 25, grad=(124, 0, 214, 0, 1.0, 0.7))
    pen.line(D([(120, 536), (218, 535)], 12), 5, tone=0.85, seed=s + 26, taper=(0.1, 0.2))
    pen.line(P([(126, 538), (134, 590)]), 3.5, tone=0.7, seed=s + 27, taper=(0.1, 0.3))
    pen.line(P([(212, 538), (204, 590)]), 3, tone=0.55, seed=s + 28, taper=(0.1, 0.3))
    r = rng(s, 'vine')
    for v in range(5):
        x = r.uniform(130, 210)
        L = r.uniform(120, 300)
        pts = P([(x, 540), (x + r.uniform(-30, 30), 560 + L * 0.4), (x + r.uniform(-50, 40), 540 + L)])
        pen.line(spline(pts, 6.0), 2.4, tone=0.55, color='grass_d', seed=s + 30 + v, role='detail', taper=(0.1, 0.5))
        sp = spline(pts, 6.0)
        for j in range(0, len(sp), 7):
            a = r.uniform(0, 360)
            pen.dot(sp[j, 0] + r.uniform(-6, 6), sp[j, 1], 9, 5.5, color='plant', tone=0.5, seed=(s + 40, v, j), rot=a)
    for j in range(6):
        a = r.uniform(-1.2, 1.2)
        pen.dot(170 + 40 * math.sin(a * 2), 528 - 10 * abs(a), 13, 7, color='plant', tone=0.55, seed=(s + 60, j),
                rot=math.degrees(a) * 40)


def _outside(pen):
    s = 200
    x0, y0, x1, y1 = GLASS
    g = rect(x0, y0, x1, y1)
    pen.cover(g, seed=s)
    pen.fill(g, 'sky', seed=s + 1, tone=0.26, grad=(0, y0, 0, y1, 1.0, 0.45), c_fade=False, streak=0.25)
    # 两排远处的房子（人字顶 / 长坡顶，直边），屋脊上一道雪，越远越淡
    r = rng(s, 'roofs')
    for i, (base, hmin, hmax, wmin, wmax, tn) in enumerate([(586, 34, 56, 70, 120, 0.06),
                                                             (650, 40, 64, 100, 160, 0.11)]):
        pts = []
        x = x0 - 20 - r.uniform(0, 50)
        while x < x1 + 10:
            w_ = r.uniform(wmin, wmax)
            h_ = r.uniform(hmin, hmax)
            b_ = base + r.uniform(-6, 6)
            if r.random() < 0.5:
                pk = x + w_ * r.uniform(0.45, 0.55)
                pts += [(x, b_), (pk, b_ - h_), (x + w_, b_)]
            else:
                q_ = r.uniform(0.18, 0.3)
                pts += [(x, b_), (x + w_ * q_, b_ - h_ * 0.8), (x + w_ * (1 - q_), b_ - h_ * 0.8), (x + w_, b_)]
            x += w_ + r.uniform(2, 24)
        top = densify(P(pts), 14)
        top[:, 0] = np.clip(top[:, 0], x0 - 4, x1 + 4)
        body = np.vstack([top, [[x1 + 4, LEDGE[1]], [x0 - 4, LEDGE[1]]]])
        pen.fill(body, 'night_l', seed=s + 10 + i, tone=tn, grad=(0, float(top[:, 1].min()), 0, LEDGE[1], 1.0, 0.7),
                 c_fade=False, a_dens=0.45 + 0.15 * i, b_dens=0.5)
        cap = np.vstack([top + P([0, -1.5]), (top + P([0, 6 + 2 * i]))[::-1]])
        pen.lift([cap], amt=0.92, seed=s + 12 + i, soft=1.0)
        pen.line(top + P([0, 7 + 2 * i]), 1.8, tone=0.28 + 0.1 * i, seed=s + 14 + i, taper=(0.05, 0.2),
                 role='detail', dry=0.5, dry_from=0.5, split=False)
        for j in range(5):
            lx = r.uniform(x0 + 20, x1 - 40)
            ly = base + 10 + 8 * i + r.uniform(0, 20)
            pen.fill(P([[lx, ly], [lx + 12, ly], [lx + 12, ly + 14], [lx, ly + 14]]), 'roof', tone=tn + 0.18,
                     seed=(s + 20, i, j), a_dens=0.6)
    # 右上角一根落了雪的树枝伸进来
    for k, (a, b, c, w_) in enumerate([((x1 + 20, 150), (1740, 175), (1650, 160), 9),
                                       ((1750, 172), (1712, 210), (1690, 236), 5),
                                       ((1700, 166), (1660, 130), (1630, 118), 4)]):
        pen.line(bez(a, b, c, 9), w_, tone=0.62, color='wood_d', seed=s + 30 + k, taper=(0.05, 0.6), dry=0.3,
                 dry_from=0.6)
        pen.line(bez(a, b, c, 9) + P([0, -w_ * 0.5]), w_ * 0.45, tone=0.9, color='snow', seed=s + 34 + k,
                 taper=(0.2, 0.5), role='detail')
    # 窗外的石头窗沿，上面一层积雪
    le = P([[x0, LEDGE[1]], [x1, LEDGE[1]], [x1, LEDGE[3]], [x0, LEDGE[3]]])
    pen.cover(le, seed=s + 40, feather=0.6)
    pen.fill(le, 'stone', seed=s + 41, tone=0.30, c_fade=False)
    pen.lift(P([[x0, LEDGE[1] - 3], [x1, LEDGE[1] - 4], [x1, LEDGE[1] + 6], [x0, LEDGE[1] + 7]]), amt=0.9,
             seed=s + 42, soft=1.0)
    pen.line(D([(x0, LEDGE[1] + 7), (x1, LEDGE[1] + 6)], 30), 2.4, tone=0.4, seed=s + 43, taper=(0.02, 0.1),
             role='detail', split=False)


def _frame(pen):
    s = 300
    x0, y0, x1, y1 = GLASS
    wd = 'wood_d'
    pen.line(D([(WIN[0] + 8, WIN[1] - 6), (WIN[0] + 5, 420), (WIN[0] + 8, SILL)], 30), 18, tone=0.9, color=wd,
             seed=s, taper=(0.04, 0.15), head=0.6, lift=0.3, dry=0.5, dry_from=0.66, streak=0.25, pool=0.2)
    pen.line(D([(WIN[0] - 14, WIN[1] + 6), (1530, WIN[1] + 1), (WIN[2] + 16, WIN[1] + 5)], 30), 19, tone=0.88,
             color=wd, seed=s + 1, taper=(0.04, 0.25), head=0.7, lift=0.35, dry=0.65, dry_from=0.6, streak=0.3,
             pool=0.2)
    pen.line(D([(WIN[2] - 8, WIN[1] + 10), (WIN[2] - 6, 420), (WIN[2] - 9, SILL)], 30), 10, tone=0.62, color=wd,
             seed=s + 2, taper=(0.1, 0.5), head=0.3, dry=0.8, dry_from=0.2, streak=0.3, fade=0.3)
    pen.line(D([(x0, TRANS_Y + 2), (1530, TRANS_Y - 2), (x1, TRANS_Y + 1)], 30), 11, tone=0.8, color=wd,
             seed=s + 3, taper=(0.05, 0.2), head=0.45, lift=0.3, dry=0.5, dry_from=0.6, streak=0.2)
    pen.line(D([(MULL_X + 1, y0), (MULL_X - 1, 420), (MULL_X + 1, y1)], 30), 11, tone=0.82, color=wd,
             seed=s + 4, taper=(0.05, 0.2), head=0.4, lift=0.3, dry=0.45, dry_from=0.62, streak=0.2)
    # 窗框内侧被雪光照亮的一条细边
    pen.lift(rect(x0 + 2, y0 + 2, x1 - 2, y0 + 7), amt=0.35, seed=s + 5, soft=2.0)
    # 室内窗台
    sill = P([[WIN[0] - 34, SILL], [WIN[2] + 34, SILL + 1], [WIN[2] + 40, SILL + 32], [WIN[0] - 40, SILL + 31]])
    pen.cover(sill, seed=s + 6)
    pen.fill(sill, 'wood', seed=s + 7, grad=(WIN[0], 0, WIN[2], 0, 0.7, 1.0))
    pen.shade(P([[WIN[0] - 40, SILL + 20], [WIN[2] + 40, SILL + 21], [WIN[2] + 40, SILL + 32],
                 [WIN[0] - 40, SILL + 31]]), amount=0.3, seed=s + 8, angle=0, hatch=False)
    pen.line(D([(WIN[0] - 46, SILL + 1), (1530, SILL - 2), (WIN[2] + 44, SILL + 2)], 30), 15, tone=0.92, color=wd,
             seed=s + 9, taper=(0.04, 0.15), head=0.7, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(WIN[0] - 36, SILL + 33), (1530, SILL + 34), (WIN[2] + 36, SILL + 32)], 30), 5, tone=0.55,
             color=wd, seed=s + 10, taper=(0.1, 0.4), head=0.2, dry=0.75, dry_from=0.35, streak=0.2)
    pen.shade(P([[WIN[0] - 40, SILL + 32], [WIN[2] + 40, SILL + 33], [WIN[2] + 60, SILL + 120],
                 [WIN[0] - 60, SILL + 118]]), amount=0.18, seed=s + 11, hatch=False,
              grad=(0, SILL + 32, 0, SILL + 120, 1.0, 0.0))


def _sill_props(pen):
    s = 400
    # 窗台右端：一小盆多肉
    cx, base = 1758, SILL + 2
    pot = P([[cx - 30, base - 44], [cx + 30, base - 44], [cx + 24, base], [cx - 24, base]])
    pen.cover(pot, seed=s, feather=0.7)
    pen.fill(pot, 'terra', seed=s + 1, grad=(cx - 30, 0, cx + 30, 0, 1.0, 0.65))
    pen.line(D([(cx - 33, base - 44), (cx + 33, base - 45)], 10), 5, tone=0.85, seed=s + 2, taper=(0.1, 0.2))
    pen.line(P([(cx - 30, base - 42), (cx - 24, base)]), 3.5, tone=0.7, seed=s + 3, taper=(0.1, 0.3))
    for j, (dx, dy, rx, ry, a) in enumerate([(-14, -58, 14, 9, -30), (12, -60, 14, 9, 30), (0, -70, 11, 13, 0),
                                             (-22, -50, 12, 7, -60), (22, -52, 12, 7, 60)]):
        pen.dot(cx + dx, base + dy, rx, ry, color='plant', tone=0.5, seed=(s + 10, j), rot=a)
    # 窗台左端：一只冒着热气的茶杯（米白搪瓷）
    cx, base = 1262, SILL + 2
    body = np.vstack([P([[cx - 26, base - 40]]), bez((cx - 26, base - 40), (cx - 26, base - 4), (cx, base), 6),
                      bez((cx, base), (cx + 26, base - 4), (cx + 26, base - 40), 6)])
    pen.shade(ell(cx + 6, base + 1, 34, 4), amount=0.3, seed=s + 20, soft=3.0, hatch=False)
    pen.cover(body, seed=s + 21, feather=0.7)
    pen.fill(body, 'enamel', seed=s + 22)
    pen.shade(np.vstack([P([[cx + 4, base - 40]]), bez((cx + 4, base - 40), (cx + 20, base - 6), (cx, base), 5),
                         bez((cx, base), (cx + 26, base - 4), (cx + 26, base - 40), 5)]), amount=0.3, seed=s + 23,
              hatch=False)
    pen.fill(ell(cx, base - 40, 24, 5), 'wood_d', tone=0.4, seed=s + 24)
    pen.line(ell(cx, base - 40, 26, 6), 3, tone=0.8, seed=s + 25, closed=True, taper=(0, 0))
    pen.line(np.vstack([bez((cx - 26, base - 40), (cx - 26, base - 4), (cx, base), 6),
                        bez((cx, base), (cx + 26, base - 4), (cx + 26, base - 40), 6)]), 4, tone=0.85, seed=s + 26,
             taper=(0.1, 0.2), head=0.3)
    pen.line(P([(cx + 25, base - 32), (cx + 40, base - 30), (cx + 38, base - 14), (cx + 23, base - 12)]), 4,
             tone=0.8, seed=s + 27, taper=(0.2, 0.3))


def background(pen):
    _wall(pen)
    _outside(pen)
    _frame(pen)
    _sill_props(pen)


# ================================================================= 动态
def snow(pen, t):
    x0, y0, x1, y1 = GLASS
    r = rng(2600)
    with pen.group('snow', boil=0.6):
        for i in range(70):
            far = i < 42
            sp = r.uniform(14, 26) if far else r.uniform(30, 52)
            size = r.uniform(1.6, 2.6) if far else r.uniform(2.8, 4.6)
            amp = r.uniform(4, 12)
            fq = r.uniform(0.2, 0.5)
            ph = r.uniform(0, 6.28)
            xs, ys = r.uniform(0, x1 - x0), r.uniform(0, y1 - y0)
            yy = (ys + sp * t) % (y1 - y0 + 20) - 10 + y0
            xx = (xs + 5 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - x0 + 40) - 20 + x0
            if not (x0 + 4 < xx < x1 - 4 and y0 + 4 < yy < LEDGE[1] - 2):
                continue
            if abs(xx - MULL_X) < 8 + size or abs(yy - TRANS_Y) < 8 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('wkf', i))


def steam(pen, t):
    cx = 1262
    per = 2.8
    with pen.group('steam', boil=0.8):
        for k in range(5):
            age = ((t + k * per / 5) % per) / per
            a = math.sin(math.pi * age) ** 1.3
            if a < 0.04:
                continue
            cyc = math.floor((t + k * per / 5) / per)
            r = rng(2700, k, cyc)
            bx = cx + r.uniform(-12, 12)
            yb = SILL - 44 - age * 150
            L = 50 + 60 * age
            ys = np.linspace(yb, yb - L, 6)
            ph = r.uniform(0, 6.28)
            xs = bx + (6 + 12 * age) * np.sin((ys - SILL) * 0.04 + ph + t * 1.2) + (SILL - ys) * 0.03
            path = np.stack([xs, ys], 1).astype(np.float32)
            w = 4 + 7 * age
            poly = tube(path, [w * 0.4, w, w * 0.7, w * 0.3])[0]
            pen.lift(poly, amt=0.5 * a, seed=(2710, k, cyc), soft=4.0)
            pen.line(path, w * 0.5, tone=0.12 * a, color='metal', seed=(2720, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.55, dry_from=0.1)


def light(pen, t):
    """晨光：从窗那边斜斜照进来（水彩 = 暖光罩染 + 提亮；水墨 = 留白），光里浮着几粒尘。"""
    with pen.group('sun', boil=0.4):
        pen.light(1240, 400, 760, 560, amt=0.42, color='sun', seed=2800)
        r = rng(2810)
        for i in range(22):
            x0, y0 = r.uniform(880, 1460), r.uniform(120, 720)
            ph = r.uniform(0, 6.28)
            xx = x0 + 18 * math.sin(0.35 * t + ph) - 6 * t % 40
            yy = y0 + 14 * math.sin(0.27 * t + 2 * ph) + 5 * math.sin(1.1 * t + ph)
            a = 0.5 + 0.5 * math.sin(0.9 * t + ph * 3)
            if a < 0.25:
                continue
            pen.light(xx, yy, r.uniform(4, 8), amt=0.55 * a, color='sun', seed=(2820, i))


def curtain(pen, t):
    """右边的纱帘：很轻地摆。"""
    s = 2900
    sw = 6.0 * math.sin(t * 0.8) + 3.0 * math.sin(t * 1.5 + 1.0)
    l = 1800
    top = 44
    edge_l = spline(P([(l + 10, top), (l + 4 + sw * 0.3, 360), (l - 6 + sw, 720), (l - 2 + sw * 1.3, H + 20)]), 8.0)
    poly = np.vstack([edge_l, P([(W + 20, H + 20), (W + 20, top)])])
    with pen.group('curtain', boil=0.6):
        pen.cover(poly, seed=s, feather=0.8, amount=0.55)
        pen.fill(poly, 'cloth', tone=0.12, seed=s + 1, grad=(l, 0, W, 0, 0.6, 1.0))
        for k, u in enumerate((0.2, 0.45, 0.72)):
            xa = l + 120 * u
            fold = P([(xa + 8, top + 20), (xa + 4 + sw * u * 0.4, 500), (xa + sw * u, H + 10)])
            pen.shade([tube(fold, [6, 10, 12])[0]], amount=0.18, seed=s + 10 + k, angle=88, soft=6.0, hatch=False)
            pen.line(fold, 2.4, tone=0.35, seed=s + 20 + k, role='detail', taper=(0.2, 0.3), dry=0.6, dry_from=0.3)
        pen.line(edge_l[::3], 4, tone=0.6, seed=s + 30, taper=(0.05, 0.3), head=0.2, dry=0.5, dry_from=0.5)
        pen.line(D([(l - 30, top - 4), (W + 20, top - 6)], 30), 8, tone=0.85, color='wood_d', seed=s + 31,
                 taper=(0.05, 0.0), head=0.4)


def bird_state(t):
    """→ (位置(脚底), 姿态) 或 None。姿态：'fly'（翅膀上/下）、'sit'、'hop'。"""
    bx, by = BIRD_AT
    if t < T_BIRD_IN:
        return None
    if t < T_BIRD_LAND:
        u = (t - T_BIRD_IN) / (T_BIRD_LAND - T_BIRD_IN)
        e = float(ease_out(u))
        x = lerp(1900, bx, e)
        y = lerp(560, by, e) - 30 * math.sin(math.pi * u)
        return np.float32([x, y]), 'fly', -1
    if t < T_BIRD_OFF:
        hop = max(0.0, math.sin(math.pi * clamp((t - 28.05) / 0.18))) * 10
        return np.float32([bx + (6 if t > 28.14 else 0), by - hop]), 'sit', -1
    u = (t - T_BIRD_OFF) / 0.45
    if u > 1.2:
        return None
    e = float(ease_in(clamp(u)))
    return np.float32([lerp(bx, 2000, e), lerp(by, 150, e) - 40 * math.sin(math.pi * clamp(u))]), 'fly', 1


def bird(pen, t, d):
    st = bird_state(t)
    if st is None:
        return
    (x, y), pose, fdir = st
    s = 3000
    sc = 1.0
    f = fdir          # -1 朝左（看着屋里），1 朝右
    with pen.group('bird', boil=0.7):
        if pose == 'sit':
            # 头偏一偏、尾巴翘一翘
            tilt = 8 * math.sin(t * 5.0) if 27.9 < t < 28.5 else 0.0
            body = ell(x, y - 22 * sc, 24 * sc, 15 * sc, rot=-12 * f)
            head_c = (x - 18 * f * sc, y - 38 * sc + tilt * 0.2)
            tail = P([(x + 16 * f, y - 22), (x + 40 * f, y - 30 - 4 * math.sin(t * 7)), (x + 42 * f, y - 22),
                      (x + 18 * f, y - 14)])
            pen.shade(ell(x, y + 1, 22, 3), amount=0.35, seed=s, soft=2.0, hatch=False)
            pen.cover([body, tail, ell(*head_c, 12 * sc, 11 * sc)], seed=s + 1, feather=0.6)
            pen.fill(tail, 'wood_d', tone=0.55, seed=s + 2)
            pen.fill(body, 'wood', tone=0.40, seed=s + 3, grad=(x - 24, 0, x + 24, 0, 1.0, 0.6))
            pen.fill(ell(x - 6 * f, y - 16, 15, 9), 'cloth', tone=0.10, seed=s + 4)
            pen.fill(ell(*head_c, 12 * sc, 11 * sc), 'wood_d', tone=0.5, seed=s + 5)
            pen.fill(ell(head_c[0] - 3 * f, head_c[1] + 5, 7, 5), 'cloth', tone=0.08, seed=s + 6)
            pen.line(P([(x + 2 * f, y - 30), (x + 14 * f, y - 20), (x + 24 * f, y - 24)]), 2.4, tone=0.6,
                     seed=s + 7, role='detail', taper=(0.1, 0.3))
            pen.line(body[::2], 3, tone=0.8, seed=s + 8, closed=True, taper=(0, 0))
            pen.line(ell(*head_c, 12, 11)[::2], 2.6, tone=0.8, seed=s + 9, closed=True, taper=(0, 0))
            pen.line(P([(head_c[0] - 11 * f, head_c[1] + 1), (head_c[0] - 20 * f, head_c[1] + 3),
                        (head_c[0] - 11 * f, head_c[1] + 5)]), 2.4, tone=0.85, seed=s + 10, taper=(0, 0))
            pen.dot(head_c[0] - 5 * f, head_c[1] - 1, 2.2, color='ink', tone=0.95, seed=s + 11)
            for j, dx in enumerate((-4, 5)):
                pen.line(P([(x + dx, y - 9), (x + dx + 1, y)]), 1.8, tone=0.7, seed=s + 12 + j, taper=(0, 0),
                         role='detail')
        else:
            flap = (d % 2) == 0
            body = ell(x, y - 24, 22, 11, rot=-18 * f)
            head_c = (x + 20 * f, y - 32)
            wy = -26 if flap else 16
            wing = P([(x - 4, y - 28), (x + 2 * f, y - 28 + wy), (x - 22 * f, y - 28 + wy * 0.8), (x - 14 * f, y - 24)])
            pen.cover([body, wing, ell(*head_c, 10, 9)], seed=s + 20, feather=0.6)
            pen.fill(body, 'wood', tone=0.40, seed=s + 21)
            pen.fill(wing, 'wood_d', tone=0.55, seed=s + 22)
            pen.fill(ell(*head_c, 10, 9), 'wood_d', tone=0.5, seed=s + 23)
            pen.line(body[::2], 2.6, tone=0.8, seed=s + 24, closed=True, taper=(0, 0))
            pen.line(wing, 2.6, tone=0.8, seed=s + 25, closed=True, taper=(0, 0))
            pen.line(P([(x - 18 * f, y - 22), (x - 36 * f, y - 18), (x - 34 * f, y - 26)]), 2.6, tone=0.8, seed=s + 26,
                     taper=(0, 0))
            pen.dot(head_c[0] + 3 * f, head_c[1] - 2, 2.0, color='ink', tone=0.95, seed=s + 27)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    z = zoom_at(t, kw)
    with pen.view(z, ZC[0] * (1 - z), ZC[1] * (1 - z)):
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        # 推近时每一帧取景都不同，缓存没有意义（还白白拷贝），只有固定取景（kw zoom）时才缓存
        cache = ('window_kiss', pen.d % 3, round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))             if kw.get('zoom') is not None else None
        with pen.group('bg', boil=BG_BOIL, cache=cache):
            background(pen)
        snow(pen, t)
        bird(pen, t, pen.d)
        curtain(pen, t)
        steam(pen, t)
        light(pen, t)
        ch.couple(pen, perf(t, kw))
