# -*- coding: utf-8 -*-
"""
第 15 镜「可是我 有时候」（成片 53.76–58.09，C）：深夜，她坐在桌前的中近景，镜头极慢地推近。
屋里没开灯，只有右边窗外的月光：一道斜斜的冷光从窗口落到桌上、落在她脸的一侧，其余都沉在墨色里。
桌上是那两只碗（汤早凉了）和上一镜熄灭的蜡烛（烛芯还剩最后一缕烟）。
  53.76  低着头，看着摊开的掌心里那颗红豆（sad_down）
  53.88–54.90「可是我」  慢慢抬起脸，迎着月光：眼里含泪，眼神却定下来了（resolve）
  55.10–56.00  一滴泪顺着被月光照亮的脸颊流下来（亮的一道）
  56.10「有时候」  把那颗红豆攥紧（拳缝露出一点红），按在胸口；56.95 闭上眼用力按住，57.65 再睁开
动的东西：窗外月光里的雪、月光里浮着的微尘、蜡烛最后一缕烟、她的呼吸和眼泪。

draw(pen, **kw)   kw：t 覆盖表演时间（成片秒）。
"""
import math

import cv2
import numpy as np

from core import W, H, densify, ell, bez, spline, tube, rng, clamp, smooth01, ease_io, ease_out, lerp
import characters as ch
import table as tb3

T0, T1 = 53.76, 58.09
T_UP0, T_UP1 = 53.88, 54.90
T_TEAR0, T_TEAR1 = 55.10, 56.00
T_GRIP0, T_GRIP1 = 55.96, 56.16
T_RAISE0, T_RAISE1 = 56.12, 56.78
T_PRESS0, T_PRESS1 = 56.78, 57.30
T_SHUT0, T_SHUT1 = 56.95, 57.65

TABLE_Y = 786
GLASS = (1410, 64, 1852, 560)
MULL_X, TRANS_Y = 1630, 252
MOON = (1515, 160, 44)
GX, GY, S_G = 1000, 486, 238
BOWL_L, BOWL_R_, BOWL_SZ = (706, 828), (1316, 822), 64
CANDLE = (548, 806)


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


# ================================================================= 背景（夜：墙沉在墨里，窗是最亮的地方）
def _window_night(pen):
    s = 100
    x0, y0, x1, y1 = GLASS
    g = P([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    pen.cover(g, seed=s)
    pen.fill(g, 'night', seed=s + 1, tone=0.62, grad=(x0, y0, x1, y1, 1.0, 0.7), streak=0.4, c_fade=False)
    # 月亮：留白的圆 + 一圈淡淡的月晕
    mx, my, mr = MOON
    pen.light(mx, my, mr * 3.2, mr * 3.0, amt=0.30, color='snow', seed=s + 2)
    pen.lift(ell(mx, my, mr, mr, n=40), amt=1.0, seed=s + 3, soft=1.2)
    pen.line(ell(mx, my, mr, mr, 200, 320, 14), 2.2, tone=0.25, seed=s + 4, taper=(0.3, 0.3), role='detail')
    # 远处的屋顶（月光下积雪的屋脊发亮）
    w_, h_ = x1 - x0, y1 - y0
    tops = [[(0.0, 0.84), (0.12, 0.76), (0.26, 0.72), (0.38, 0.78), (0.46, 0.83)],
            [(0.42, 0.86), (0.56, 0.78), (0.70, 0.74), (0.84, 0.80), (1.0, 0.86)]]
    for i, top in enumerate(tops):
        tp = P([(x0 + a * w_, y0 + b * h_) for a, b in top])
        body = np.vstack([tp, [[tp[-1, 0], y1], [tp[0, 0], y1]]])
        pen.fill(body, 'roof', seed=s + 20 + i, tone=0.78, c_fade=False)
        pen.line(tp, 9, tone=0.9, color='snow', seed=s + 30 + i, taper=(0.1, 0.2), role='detail', dry=0.4,
                 dry_from=0.3)
    for i, (a, b) in enumerate([(0.16, 0.86), (0.64, 0.88)]):     # 只剩一两扇还亮着的小窗
        lx, ly = x0 + a * w_, y0 + b * h_
        q = P([[lx, ly], [lx + 12, ly + 1], [lx + 11, ly + 14], [lx + 1, ly + 13]])
        pen.cover(q, seed=s + 50 + i, feather=0.8)
        pen.fill(q, 'win_warm', seed=s + 55 + i)
    # 窗框
    pen.line(D([(x0 - 10, y0 - 12), (x0 - 13, (y0 + y1) / 2), (x0 - 9, y1 + 16)], 30), 16, tone=0.95,
             color='wood_d', seed=s + 80, taper=(0.08, 0.18), head=0.6, lift=0.3, dry=0.5, dry_from=0.62,
             streak=0.25, pool=0.25)
    pen.line(D([(x0 - 24, y0 - 8), ((x0 + x1) / 2, y0 - 13), (x1 + 20, y0 - 9)], 30), 16, tone=0.92,
             color='wood_d', seed=s + 81, taper=(0.05, 0.3), head=0.7, lift=0.35, dry=0.6, dry_from=0.55,
             streak=0.3, pool=0.2)
    pen.line(D([(MULL_X + 2, y0), (MULL_X - 1, (y0 + y1) / 2), (MULL_X + 1, y1)], 30), 11, tone=0.88,
             color='wood_d', seed=s + 85, taper=(0.06, 0.2), head=0.45, lift=0.3, dry=0.4, dry_from=0.6)
    pen.line(D([(x0, TRANS_Y + 2), ((x0 + x1) / 2, TRANS_Y - 2), (x1, TRANS_Y + 1)], 30), 10, tone=0.84,
             color='wood_d', seed=s + 86, taper=(0.05, 0.25), head=0.45, lift=0.3, dry=0.5, dry_from=0.55)
    sill = P([[x0 - 34, y1 + 6], [x1 + 30, y1 + 8], [x1 + 34, y1 + 30], [x0 - 38, y1 + 28]])
    pen.cover(sill, seed=s + 89)
    pen.fill(sill, 'wood_d', seed=s + 90, tone=0.55, c_fade=False)
    pen.lift(P([[x0 - 30, y1 + 7], [x1 + 28, y1 + 9], [x1 + 26, y1 + 16], [x0 - 30, y1 + 14]]), amt=0.55,
             seed=s + 93, soft=2.0)
    pen.line(D([(x0 - 46, y1 + 7), ((x0 + x1) / 2, y1 + 3), (x1 + 36, y1 + 9)], 30), 14, tone=0.92,
             color='wood_d', seed=s + 91, taper=(0.04, 0.15), head=0.7, lift=0.25, dry=0.45, dry_from=0.72)


def beam_poly():
    """月光从窗口斜斜落下的一道光（落到桌上、她的脸和肩）。"""
    x0, y0, x1, y1 = GLASS
    return P([[x0 + 10, y0 + 40], [x1 - 40, y0 + 20], [1180, H + 40], [620, H + 40]])


def background(pen):
    s = 700
    q = P([(-20, -20), (W + 20, -20), (W + 20, TABLE_Y + 6), (-20, TABLE_Y + 6)])
    pen.fill(q, 'wall', seed=s, tone=0.78, grad=(80, 0, 1500, 0, 1.0, 0.70), c_fade=False, broad=False)
    pen.shade(P([(-20, -20), (760, -20), (520, TABLE_Y + 6), (-20, TABLE_Y + 6)]), amount=0.5, seed=s + 1,
              hatch=False, grad=(0, 0, 760, 0, 1.0, 0.0))
    # 左边墙上，暗里一点点看得见的东西：挂历（第 11 镜被划掉的那些天）、搁板上只剩一只杯子
    tb3.calendar(pen, 150, 250, seed=1000)
    tb3.shelf_mugs(pen, 300, 470, w=200, mugs=1)
    _window_night(pen)
    # 月光落在墙上
    pen.lift(beam_poly(), amt=0.42, seed=s + 5, soft=40.0)
    # 桌子
    top = P([(-20, TABLE_Y), (W + 20, TABLE_Y), (W + 20, H + 20), (-20, H + 20)])
    pen.cover(top, seed=s + 10)
    pen.fill(top, 'wood_d', seed=s + 11, tone=0.62, grad=(0, TABLE_Y, 0, H, 0.8, 1.0), streak=0.22, sangle=2.0,
             c_fade=False, broad=False)
    r = rng(s, 'grain')
    for k in range(4):
        y = TABLE_Y + 40 + k * 66 + r.uniform(-8, 8)
        x0 = r.uniform(-20, 400) if k % 2 == 0 else r.uniform(1100, 1500)
        pen.line(D([(x0, y), (x0 + 300, y + r.uniform(-4, 4)), (x0 + r.uniform(500, 700), y + r.uniform(-3, 3))], 40),
                 2.4, tone=0.30, color='wood_d', seed=s + 20 + k, taper=(0.3, 0.4), role='detail', dry=0.7,
                 dry_from=0.2, streak=0.3)
    pen.lift(P([[760, TABLE_Y + 2], [1240, TABLE_Y + 2], [1330, H + 30], [700, H + 30]]), amt=0.38, seed=s + 12,
             soft=30.0)
    pen.line(D([(-20, TABLE_Y + 1), (700, TABLE_Y - 2), (1500, TABLE_Y + 1), (1940, TABLE_Y - 1)], 30), 14,
             tone=0.92, color='wood_d', seed=s + 13, taper=(0.02, 0.2), head=0.4, lift=0.3, dry=0.5, dry_from=0.7,
             streak=0.25, pool=0.2)


# ================================================================= 桌上的东西
def candle(pen, t):
    """熄灭的蜡烛：烧到只剩一截，烛泪淌在烛台上；烛芯上最后一缕烟慢慢散掉（54.8 前）。"""
    s = 1400
    cx, cy = CANDLE
    with pen.group('candle', boil=0.5):
        dish = ell(cx, cy + 22, 46, 11, n=36)
        pen.shade(ell(cx + 10, cy + 30, 50, 8, n=30), amount=0.35, seed=s, soft=4.0)
        pen.cover([dish], seed=s + 1, feather=0.8)
        pen.fill([dish], 'enamel', seed=s + 2, tone=0.30)
        pen.line(ell(cx, cy + 22, 46, 11, 0, 180, 20), 3.6, tone=0.85, seed=s + 3, taper=(0.1, 0.1), head=0.3)
        pen.line(ell(cx, cy + 22, 46, 11, 180, 360, 20), 2.2, tone=0.55, seed=s + 4, taper=(0.1, 0.1))
        body = P([[cx - 13, cy - 14], [cx + 13, cy - 16], [cx + 14, cy + 22], [cx - 14, cy + 22]])
        pen.cover([body], seed=s + 5, feather=0.7)
        pen.fill([body], 'enamel', seed=s + 6, tone=0.22)
        # 烛泪
        for k, (dx, L) in enumerate(((-9, 26), (3, 18), (10, 30))):
            pen.line([(cx + dx, cy - 12), (cx + dx + 1, cy - 12 + L * 0.6), (cx + dx, cy - 12 + L)], 4.5,
                     tone=0.35, seed=s + 10 + k, taper=(0.1, 0.0), role='detail', head=0.2)
        pen.line([(cx - 14, cy - 13), (cx - 15, cy + 4), (cx - 14, cy + 22)], 3.5, tone=0.85, seed=s + 7,
                 taper=(0.1, 0.2), head=0.3)
        pen.line([(cx + 13, cy - 15), (cx + 14, cy + 4), (cx + 14, cy + 22)], 2.5, tone=0.6, seed=s + 8,
                 taper=(0.1, 0.2))
        pen.line(ell(cx, cy - 15, 13, 3.5, 0, 360, 14), 2.0, tone=0.6, seed=s + 9, closed=True, taper=(0, 0))
        pen.line([(cx, cy - 16), (cx + 1, cy - 24), (cx + 3, cy - 29)], 2.6, tone=0.95, seed=s + 15,
                 taper=(0.0, 0.3))
        # 最后一缕烟
        a = 1.0 - smooth01((t - 54.0) / 0.8)
        if a > 0.03:
            ys = np.linspace(cy - 30, cy - 30 - 150, 12)
            xs = cx + 3 + 14 * np.sin((ys - cy) * 0.045 + t * 1.3) * np.linspace(0.2, 1.0, 12) + \
                np.linspace(0, 26, 12)
            pen.line(np.stack([xs, ys], 1), 2.6, tone=0.45 * a, seed=(s + 20, int(t * 12) % 3), taper=(0.1, 0.8),
                     role='detail', dry=0.5, dry_from=0.4)


def motes(pen, t):
    """月光里慢慢浮着的微尘（提白的小点，只在光柱里）。"""
    bp = beam_poly().reshape(-1, 1, 2)
    r = rng(1880)
    with pen.group('motes', boil=0.3):
        for i in range(34):
            x0, y0 = r.uniform(600, 1500), r.uniform(80, 900)
            ph = r.uniform(0, 6.28)
            x = x0 + 18 * math.sin(0.35 * t + ph) + 6 * t
            y = y0 - 9 * t + 10 * math.cos(0.27 * t + 2 * ph)
            y = (y - 80) % 820 + 80
            if cv2.pointPolygonTest(bp, (float(x), float(y)), True) < 6:
                continue
            sz = r.uniform(1.2, 2.6)
            pen.dot(x, y, sz, color='snow', tone=0.0, seed=('mote', i))


# ================================================================= 她的表演
def _blink(t, tb, dur=0.30):
    x = (t - tb) / dur
    if x <= 0 or x >= 1:
        return 0.0
    return float(smooth01(x / 0.35)) if x < 0.35 else float(1.0 - smooth01((x - 0.35) / 0.65))


def girl_pose(t):
    up = ease_io((t - T_UP0) / (T_UP1 - T_UP0))
    look_bean = dict(ch.EXPR['sad_down'], gy=1.0, gx=0.05, open=0.32)
    res = dict(ch.EXPR['resolve'], gx=0.28, gy=-0.05)
    face = ch.mix_expr(look_bean, res, up)
    face['tear'] = 0.10 + 0.55 * ease_io((t - T_TEAR0) / (T_TEAR1 - T_TEAR0))
    # 攥紧按在胸口：闭眼、眉头更紧、嘴抿住；再睁开
    shut = ease_io((t - T_SHUT0) / 0.25) * (1.0 - ease_io((t - (T_SHUT1 - 0.15)) / 0.35))
    face['open'] = face['open'] * (1.0 - shut)
    face['brow'] = face['brow'] + 0.25 * shut
    face['smile'] = face['smile'] - 0.08 * shut
    grip = 0.2 + 0.8 * smooth01((t - T_GRIP0) / (T_GRIP1 - T_GRIP0))
    u = ease_io((t - T_RAISE0) / (T_RAISE1 - T_RAISE0))
    press = ease_io((t - T_PRESS0) / (T_PRESS1 - T_PRESS0))
    yaw = 18 + 9 * up - 4 * press
    pitch = 30 - 28 * up + 4 * press
    roll = 6 - 4 * up + 2 * press
    blink = _blink(t, 55.55)
    sob = 0.6 * math.exp(-((t - 56.95) / 0.12) ** 2)
    rest = (GX + 0.12 * S_G, TABLE_Y - 0.30 * S_G)      # 掌心朝上捧在身前，低头看着那颗红豆
    return dict(x=GX, y=GY - 3.0 * sob + 2.0 * press, s=S_G, facing=1, yaw=yaw, pitch=pitch, roll=roll, face=face,
                blink=blink, breath=(t - T0) / 3.9 + 0.3, clip_y=TABLE_Y + 2, clip_arms=False, seed=1000, light=1,
                arm='fist_chest', arm_args=dict(u=u, grip=grip, press=press, rest=rest,
                                                   chest=(GX - 0.04 * S_G, GY + 0.40 * S_G)), boil=1.0)


def veil(pen):
    """月光照不到的地方：一层冷墨从左往右淡开（盖在她身上；窗那一侧的脸留着月光）。"""
    with pen.group('veil', boil=0.3):
        q = P([(-20, -20), (W + 20, -20), (W + 20, H + 20), (-20, H + 20)])
        pen.fill(q, 'ink', tone=0.55, seed=1950, grad=(760, 0, 1130, 0, 1.0, 0.0), c_fade=False, broad=False,
                 rim=0.0, bloom=0.0)


def tear_glint(pen, gp, t):
    """泪在月光下亮一点：近侧眼下的泪光 + 泪痕下端一颗亮点。"""
    k = float(gp['face']['tear'])
    if k < 0.15:
        return
    with pen.group('glint', boil=0.3):
        e = ch.girl_tear_point(gp, where='end')
        tw = 0.6 + 0.4 * math.sin(t * 5.0)
        pen.lift(ell(e[0], e[1], 3.4, 4.6, n=12), amt=0.85 * tw, seed=1960, soft=0.8)
        pen.light(e[0], e[1], 14, 16, amt=0.18 * tw, color='snow', seed=1961)


def draw(pen, t=None, **kw):
    t = float(pen.t if t is None else t)
    # 极慢地推近（只这一种运动）
    u = ease_io((t - T0) / (T1 - T0))
    z = 1.30 + 0.09 * u
    cx, cy = 1030, 522 - 12 * u
    with pen.view(z, W / 2 - z * cx, H / 2 - z * cy):
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        with pen.group('bg', boil=0.4, cache=('night_mcu', pen.d % 3, round(z, 4), round(float(o[0]), 1),
                                              round(float(o[1]), 1))):
            background(pen)
        tb3.snow(pen, t, GLASS, MULL_X, TRANS_Y, seed=1620, n=70,
                 avoid=lambda x, y: (x - MOON[0]) ** 2 + (y - MOON[1]) ** 2 < (MOON[2] + 6) ** 2)
        candle(pen, t)
        tb3.small_bowl(pen, BOWL_L, BOWL_SZ, fill=0.85, seed=1310, shadow=(0.3, 0.4))
        tb3.small_bowl(pen, BOWL_R_, BOWL_SZ, fill=0.85, seed=1340, shadow=(-0.3, 0.4))
        gp = girl_pose(t)
        ch.girl_front(pen, gp)
        veil(pen)
        motes(pen, t)
        tear_glint(pen, gp, t)
