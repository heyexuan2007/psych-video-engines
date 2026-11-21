# -*- coding: utf-8 -*-
"""
第 13 镜「第十一句句示例歌」（成片 45.14–49.49，C 水墨）。
架子特写 → 往下摇到台面上的纸箱。
“相聚”（45.26）：墙上木架上两只马克杯挨在一起，把手朝着对方（和厨房里那两只同款：她的米白、他的青灰）。
架上还有那只空了的红豆罐（盖子拧回去了，贴着“红豆”的小标签）和一个插着两枝干花的小瓶。
“离开”（46.02）：她的右手从画面左下伸进来，握住他那只杯子的把手，拿起来——架子上只剩她那只，
原来放他杯子的地方留下一圈淡淡的杯底印子。
镜头往下摇（pen.view 平移，46.45–47.40），跟着杯子到台面上一只敞开的纸箱：里面已经放着他的藏青围巾和几本书；
“这一句”（47.42）杯子放进纸箱；她松手，48.2–49.2 先合上后面那片箱盖，再把前面垂着的那片翻上来合上。
窗光斜斜地落在墙上（窗棂的影子），光斑里有雪的影子往下飘、浮尘在动。台面上还有一卷胶带和一把剪刀。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒，默认 pen.t）
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
from core import W, H, densify, ell, bez, spline, tube, rng, clamp, ease_io, ease_out, ease_in
import hands

T0, T1 = 45.14, 49.49
T_REACH0, T_GRIP = 45.60, 46.00
T_LIFT = 46.34
T_TRAVEL = 47.28
T_IN = 47.55                      # 杯子落到箱子里
T_REL = 47.86                     # 松手
T_PAN0, T_PAN1 = 46.45, 47.40
T_BF0, T_BF1 = 48.20, 48.62       # 合上后面那片
T_FF0, T_FF1 = 48.72, 49.20       # 合上前面那片
DY = 1000.0                       # 往下摇多少（场景像素）
BG_BOIL = 0.4

# ---------------------------------------------------------------- 架子（镜头几乎平视：俯角 8°）
E1 = math.radians(8.0)
SHELF_BACK, SHELF_FRONT = 444.0, 482.0
BASE_Y = 466.0                    # 杯底中心
MUG_RX, MUG_H = 95.0, 230.0
HER_X, HIS_X = 760.0, 1090.0
L_HAND = 380.0

# ---------------------------------------------------------------- 台面和纸箱（俯角 35°）
E2 = math.radians(35.0)
C2, S2 = math.cos(E2), math.sin(E2)
BX0, BX1 = 660.0, 1260.0          # 箱子左右
BH, BD = 330.0, 380.0             # 箱高、箱深（真实尺寸）
Y_REF = 1800.0 - (BD / 2) * S2    # 让箱子前下沿落在 y=1800
LF = BD / 2                       # 长盖的长度（合上时两片在中间对齐）
SIDE_F = 110.0                    # 两片短盖（早已折进去）
WALL_Y = Y_REF - 400.0 * S2       # 墙和台面的交线（台面后沿）


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def bp(x, Y, Z):
    """纸箱 / 台面的 3D → 场景坐标（x 右，Y 上，Z 朝镜头；箱子底面中心为原点的深度）。"""
    return np.float32([x, Y_REF - Y * C2 + Z * S2])


# ================================================================= 表演
def pan_y(t):
    return -DY * ease_io((t - T_PAN0) / (T_PAN1 - T_PAN0))


def mug_path(t):
    """他那只杯子：(杯底中心 x, y, 俯角)。"""
    x0, y0 = HIS_X, BASE_Y
    if t < T_GRIP + 0.02:
        return x0, y0, E1
    if t < T_LIFT:
        k = ease_io((t - T_GRIP - 0.02) / (T_LIFT - T_GRIP - 0.02))
        return x0 + 26 * k, y0 - 22 * k, E1
    p_in = bp(960.0, 60.0, 0.0)            # 箱子里：落在围巾上
    above = p_in + np.float32([0, -250])
    if t < T_TRAVEL:
        k = ease_io((t - T_LIFT) / (T_TRAVEL - T_LIFT))
        a = np.float32([x0 + 26, y0 - 22])
        mid = (a + above) / 2 + np.float32([90, 0])
        q = (1 - k) ** 2 * a + 2 * (1 - k) * k * mid + k * k * above
        return float(q[0]), float(q[1]), E1 + (E2 - E1) * k
    k = ease_io((t - T_TRAVEL) / (T_IN - T_TRAVEL))
    q = above * (1 - k) + p_in * k
    return float(q[0]), float(q[1]), E2


def flap_angles(t):
    """后盖、前盖的开合角（度；0 = 合上）。"""
    th_b = 110.0 * (1 - ease_io((t - T_BF0) / (T_BF1 - T_BF0)))
    th_f = 200.0 * (1 - ease_io((t - T_FF0) / (T_FF1 - T_FF0)))
    return th_b, th_f


def flap_geom(which, th):
    """长盖的四个角（场景坐标）+ 盖尖中点 + 看到的是外面还是里面。"""
    a = math.radians(th)
    if which == 'back':
        z0 = -BD / 2
        d = (math.sin(a), math.cos(a))           # (Y, Z)
    else:
        z0 = BD / 2
        d = (math.sin(a), -math.cos(a))
    Yt, Zt = BH + LF * d[0], z0 + LF * d[1]
    h0, h1 = bp(BX0, BH, z0), bp(BX1, BH, z0)
    t0, t1 = bp(BX0 + 1, Yt, Zt), bp(BX1 - 1, Yt, Zt)
    # 法线（外面）·视线：外面朝上时（合上）可见
    nY, nZ = (d[1], -d[0]) if which == 'back' else (-d[1], d[0])
    if which == 'back':
        nY, nZ = math.cos(a), -math.sin(a)
    else:
        nY, nZ = math.cos(a), math.sin(a)
    outer = (nY * S2 + nZ * C2) > 0
    return np.vstack([h0, h1, t1, t0]), (t0 + t1) / 2, outer


def hand_plan(t):
    """右手：(锚点 x, y, reach, rot)；None = 不画。"""
    mx, my, el = mug_path(t)
    beam = mug_handle_beam(mx, my, el, -1)
    if t < T_REACH0:
        return None
    if t < T_REL:
        r = clamp((t - T_REACH0) / (T_GRIP - T_REACH0))
        rot = -18.0 + 14.0 * clamp((t - T_LIFT) / (T_IN - T_LIFT))
        return float(beam[0]), float(beam[1]), r, rot, 'grip'
    # 松手、离开把手 → 去压后盖 → 翻前盖
    th_b, th_f = flap_angles(t)
    _, tip_b, _ = flap_geom('back', th_b)
    _, tip_f, _ = flap_geom('front', th_f)
    rel = ease_io((t - T_REL) / 0.18)
    r_rel = 1.0 - 0.45 * rel
    if t < T_BF0:
        k = ease_io((t - T_REL - 0.1) / (T_BF0 - T_REL - 0.1))
        p = beam * (1 - k) + (tip_b + np.float32([-40, -10])) * k + np.float32([0, -30]) * math.sin(math.pi * k)
        return float(p[0]), float(p[1]), r_rel, -4.0 + 44.0 * k, 'push'
    if t < T_FF0:
        k = ease_io((t - T_BF1) / (T_FF0 - T_BF1))
        p = (tip_b + np.float32([-40, -10])) * (1 - k) + (tip_f + np.float32([-40, 10])) * k
        return float(p[0]), float(p[1]), 0.55, 40.0 - 50.0 * k, 'push'
    p = tip_f + np.float32([-40, 10])
    k = clamp((t - T_FF0) / (T_FF1 - T_FF0))
    return float(p[0]), float(p[1]), 0.55, -10.0 + 50.0 * k, 'push'


# ================================================================= 马克杯
def mug_dims(cx, by, el):
    hs = MUG_H * math.cos(el)
    ry = max(2.0, MUG_RX * math.sin(el))
    return hs, ry, by - hs


def mug_handle_beam(cx, by, el, side):
    hs, ry, yt = mug_dims(cx, by, el)
    return np.float32([cx + side * (MUG_RX + 50), yt + 0.47 * hs + ry * 0.2])


def mug(pen, cx, by, el, col, tone, side, seed, band=False):
    s = seed
    rx = MUG_RX
    hs, ry, yt = mug_dims(cx, by, el)
    body = np.vstack([ell(cx, yt, rx, ry, 180, 360, 24), ell(cx, by, rx, ry, 0, 180, 24)])
    # 把手（C 形，一根有宽度的管）
    a_t = (cx + side * (rx - 4), yt + 0.20 * hs + ry * 0.2)
    a_b = (cx + side * (rx - 4), yt + 0.74 * hs + ry * 0.2)
    path = [a_t, (cx + side * (rx + 36), yt + 0.22 * hs + ry * 0.2), (cx + side * (rx + 52), yt + 0.47 * hs + ry * 0.2),
            (cx + side * (rx + 36), yt + 0.72 * hs + ry * 0.2), a_b]
    hpoly, hl, hr = tube(path, [16, 18, 20, 18, 16])
    # 杯底在架子/箱子上的接触影
    pen.shade(ell(cx + 10, by + 2, rx * 1.05, ry * 0.9 + 3, n=30), amount=0.35, seed=(s, 'cs'), soft=5.0, hatch=False)
    pen.cover([body, hpoly], seed=(s, 'cv'), feather=0.7)
    pen.fill(hpoly, col, seed=(s, 'hf'), tone=tone, c_fade=False, broad=False, grad_auto=False)
    pen.fill(body, col, seed=(s, 'f'), tone=tone, c_fade=False, broad=False,
             grad=(cx - rx, 0, cx + rx, 0, 0.75, 1.25))
    # 暗面（右侧）、高光（左侧）
    pen.shade(np.vstack([ell(cx, yt, rx, ry, 300, 360, 8), ell(cx, by, rx, ry, 0, 60, 8)]), amount=0.32,
              seed=(s, 'sh'), angle=80)
    pen.lift(tube([(cx - rx * 0.62, yt + hs * 0.12 + ry), (cx - rx * 0.64, by - hs * 0.15)], [5, 9, 5])[0], amt=0.5,
             seed=(s, 'hl'), soft=2.0, dry=0.5, streak=0.4)
    if band:
        for k, f in enumerate((0.30, 0.37)):
            yy = yt + hs * f
            pen.line(ell(cx, yy, rx, ry, 0, 180, 24), 3.2, tone=0.55, seed=(s, 'band', k), role='detail',
                     taper=(0.05, 0.05))
    # 杯口：里面一圈暗、杯沿两道
    if ry > 3:
        inner = ell(cx, yt, rx * 0.92, ry * 0.86, 0, 360, 36)
        pen.fill(inner, 'ink', seed=(s, 'in'), tone=0.38, grad=(cx - rx, yt - ry, cx + rx, yt + ry, 1.2, 0.5),
                 c_fade=False, broad=False)
    pen.line(ell(cx, yt, rx, ry, 0, 360, 40), 4.0, tone=0.85, seed=(s, 'rim'), closed=True, taper=(0, 0))
    # 轮廓：受光一侧（左）浓、另一侧淡
    pen.line(D([(cx - rx, yt), (cx - rx - 1, (yt + by) / 2), (cx - rx, by)], 16), 6.0, tone=0.9, seed=(s, 'l'),
             taper=(0.05, 0.1), head=0.45, lift=0.2)
    pen.line(D([(cx + rx, yt), (cx + rx + 1, (yt + by) / 2), (cx + rx, by)], 16), 3.6, tone=0.65, seed=(s, 'r'),
             taper=(0.05, 0.2), head=0.2, dry=0.4, dry_from=0.6)
    pen.line(ell(cx, by, rx, ry, 0, 180, 24), 5.0, tone=0.85, seed=(s, 'b'), taper=(0.05, 0.1), head=0.3)
    pen.line(hl, 4.2, tone=0.85, seed=(s, 'h1'), taper=(0.15, 0.2), head=0.3)
    pen.line(hr[3:-3], 2.8, tone=0.6, seed=(s, 'h2'), taper=(0.15, 0.2), role='detail')
    return dict(beam=mug_handle_beam(cx, by, el, side), sil=[body, hpoly])


# ================================================================= 背景
def wall(pen):
    s = 100
    q = P([(-40, -40), (W + 40, -40), (W + 40, WALL_Y + 6), (-40, WALL_Y + 6)])
    pen.fill(q, 'wall', seed=s, tone=0.22, rgrad=(500, 100, 300, 2200, 0.4, 1.1), c_fade=False, broad=False,
             var=0.12, cell=110.0)
    # 窗光：斜斜的一块亮（窗在画面左边外），带窗棂的影子
    patch = P([(1180, 560), (1760, 520), (1860, 1180), (1270, 1230)])
    pen.lift(patch, amt=0.55, seed=s + 1, soft=16.0)
    a, b, c, d = patch
    mv0, mv1 = a + (b - a) * 0.52, d + (c - d) * 0.52
    pen.shade(tube([mv0, mv1], [16, 18])[0], amount=0.28, seed=s + 2, soft=6.0, hatch=False)
    mh0, mh1 = a + (d - a) * 0.40, b + (c - b) * 0.40
    pen.shade(tube([mh0, mh1], [14, 16])[0], amount=0.26, seed=s + 3, soft=6.0, hatch=False)
    # 插座（两孔）+ 墙上一道细裂纹
    ox, oy = 420.0, 1180.0
    sq = P([(ox, oy), (ox + 86, oy + 2), (ox + 85, oy + 92), (ox - 1, oy + 90)])
    pen.cover(sq, seed=s + 4, feather=0.8)
    pen.fill(sq, 'enamel', seed=s + 5, tone=0.06)
    pen.line(np.vstack([sq, sq[:1]]), 3.0, tone=0.7, seed=s + 6, taper=(0, 0))
    for k, dx in enumerate((28, 58)):
        pen.line(P([(ox + dx, oy + 36), (ox + dx, oy + 54)]), 3.4, tone=0.85, seed=(s, 7, k), role='detail',
                 taper=(0.1, 0.1))
    pen.line(P([(240, 640), (262, 700), (255, 760), (280, 830)]), 2.0, tone=0.3, seed=s + 8, role='detail',
             taper=(0.3, 0.5), dry=0.5, dry_from=0.3)


def shelf(pen):
    s = 200
    # 架子在墙上的影
    pen.shade(P([(150, SHELF_FRONT), (1800, SHELF_FRONT), (1830, SHELF_FRONT + 70), (180, SHELF_FRONT + 70)]),
              amount=0.35, seed=s, soft=16.0, hatch=False)
    topq = P([(140, SHELF_BACK), (1790, SHELF_BACK), (1800, SHELF_FRONT), (130, SHELF_FRONT)])
    front = P([(130, SHELF_FRONT), (1800, SHELF_FRONT), (1800, SHELF_FRONT + 32), (130, SHELF_FRONT + 32)])
    pen.cover([topq, front], seed=s + 1, feather=0.8)
    pen.fill(topq, 'wood', seed=s + 2, tone=0.32, c_fade=False, broad=False)
    pen.fill(front, 'wood_d', seed=s + 3, tone=0.55, c_fade=False, broad=False, grad=(130, 0, 1800, 0, 0.8, 1.2))
    pen.hatch(front, angle=1, spacing=6, tone=0.2, color='wood_d', seed=s + 4, partial=0.5)
    pen.line(D([(130, SHELF_FRONT), (900, SHELF_FRONT - 1), (1800, SHELF_FRONT + 1)], 30), 6, tone=0.85,
             color='wood_d', seed=s + 5, taper=(0.03, 0.05), head=0.4)
    pen.line(D([(128, SHELF_FRONT + 32), (900, SHELF_FRONT + 33), (1802, SHELF_FRONT + 31)], 30), 9, tone=0.9,
             color='wood_d', seed=s + 6, taper=(0.03, 0.08), head=0.6, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25)
    pen.line(D([(140, SHELF_BACK), (1790, SHELF_BACK)], 30), 3, tone=0.55, color='wood_d', seed=s + 7,
             taper=(0.05, 0.05))
    # 两个三角托架
    for k, x in enumerate((300, 1620)):
        br = P([(x - 12, SHELF_FRONT + 32), (x + 12, SHELF_FRONT + 32), (x + 12, SHELF_FRONT + 190)])
        br = P([(x - 14, SHELF_FRONT + 32), (x + 110, SHELF_FRONT + 32), (x + 110, SHELF_FRONT + 44),
                (x + 2, SHELF_FRONT + 170), (x - 14, SHELF_FRONT + 170)])
        pen.shade(br + P([18, 20]), amount=0.3, seed=(s, 8, k), soft=8.0, hatch=False)
        pen.cover(br, seed=(s, 9, k), feather=0.8)
        pen.fill(br, 'wood_d', seed=(s, 10, k), tone=0.6)
        pen.line(np.vstack([br, br[:1]]), 4.0, tone=0.85, seed=(s, 11, k), taper=(0.05, 0.05), head=0.3)
    # 杯底印子（他的杯子拿走以后才露出来；杯子在的时候被杯子挡住）
    pen.line(ell(HIS_X, BASE_Y, MUG_RX * 0.92, MUG_RX * math.sin(E1) * 0.92, 0, 360, 40), 3.4, tone=0.42,
             seed=s + 12, closed=True, role='detail', taper=(0, 0), dry=0.5, dry_from=0.2)
    pen.lift(ell(HIS_X, BASE_Y, MUG_RX * 0.84, MUG_RX * math.sin(E1) * 0.7, 0, 360, 30), amt=0.25, seed=s + 13,
             soft=3.0)


def shelf_jar(pen):
    """那只空了的红豆罐（盖子拧回去了）。"""
    s = 300
    cx, by, rx, h = 360.0, BASE_Y, 78.0, 196.0
    hs, ry = h * math.cos(E1), rx * math.sin(E1)
    yt = by - hs
    body = np.vstack([ell(cx, yt + 20, rx, ry, 180, 360, 20), ell(cx, by, rx, ry, 0, 180, 20)])
    pen.shade(ell(cx + 10, by + 2, rx * 1.05, ry + 3, n=24), amount=0.3, seed=s, soft=5.0, hatch=False)
    pen.fill(body, 'glass', seed=s + 1, tone=0.10, c_fade=False, broad=False, grad_auto=False)
    pen.line(D([(cx - rx, yt + 20), (cx - rx, by)], 16), 5.0, tone=0.85, seed=s + 2, taper=(0.05, 0.1), head=0.4)
    pen.line(D([(cx + rx, yt + 20), (cx + rx, by)], 16), 3.4, tone=0.6, seed=s + 3, taper=(0.05, 0.1))
    pen.line(D([(cx - rx + 8, yt + 26), (cx - rx + 8, by - 6)], 16), 2.0, tone=0.35, seed=s + 4, role='detail')
    pen.line(ell(cx, by, rx, ry, 0, 180, 20), 4.0, tone=0.8, seed=s + 5, taper=(0.05, 0.1))
    pen.fill(ell(cx, by - 8, rx * 0.95, ry * 0.9 + 4, 0, 360, 20), 'glass', seed=s + 6, tone=0.22)
    pen.lift(tube([(cx - rx * 0.55, yt + 40), (cx - rx * 0.55, by - 20)], [4, 9, 4])[0], amt=0.7, seed=s + 7, soft=2.0)
    lidq = P([(cx - rx - 3, yt), (cx + rx + 3, yt), (cx + rx + 2, yt + 22), (cx - rx - 2, yt + 22)])
    pen.cover(lidq, seed=s + 8, feather=0.8)
    pen.fill(lidq, 'wood_d', seed=s + 9, tone=0.6)
    pen.line(np.vstack([lidq, lidq[:1]]), 3.6, tone=0.85, seed=s + 10, taper=(0.05, 0.05))
    for k in range(10):
        x = cx - rx + 10 + k * (2 * rx - 20) / 9
        pen.line(P([(x, yt + 4), (x, yt + 18)]), 1.6, tone=0.45, seed=(s, 11, k), role='detail', taper=(0.1, 0.1))
    # 标签
    lq = P([(cx - 46, yt + 70), (cx + 46, yt + 70), (cx + 46, yt + 122), (cx - 46, yt + 122)])
    pen.cover(lq, seed=s + 12, feather=0.7)
    pen.fill(lq, 'cloth', seed=s + 13, tone=0.10)
    pen.line(np.vstack([lq, lq[:1]]), 2.2, tone=0.6, seed=s + 14, taper=(0.05, 0.05))
    m = text_mask('红豆', core.FONT_LYRIC, 40)
    pen.fill(mask=(m, int(cx - m.shape[1] / 2), int(yt + 96 - m.shape[0] / 2)), color='ink', tone=0.85,
             seed=s + 15, c_dens=1.0, soft=0.7, rough=0.05, bloom=0.0, rim=0.05, c_fade=False, broad=False,
             grad_auto=False)


def vase(pen):
    """小瓶子里插着两枝干花（满天星一样的小籽头）。"""
    s = 400
    cx, by = 1430.0, BASE_Y
    body = np.vstack([ell(cx, by - 70, 44, 8, 180, 360, 14), P([(cx + 46, by - 40), (cx + 40, by - 6)]),
                      ell(cx, by, 40, 6, 0, 180, 14), P([(cx - 40, by - 6), (cx - 46, by - 40)])])
    neck = P([(cx - 14, by - 150), (cx + 14, by - 150), (cx + 16, by - 72), (cx - 16, by - 72)])
    pen.shade(ell(cx + 10, by + 2, 46, 8, n=20), amount=0.3, seed=s, soft=5.0, hatch=False)
    pen.cover([body, neck], seed=s + 1, feather=0.8)
    pen.fill([body, neck], 'stone', seed=s + 2, tone=0.42, grad=(cx - 46, 0, cx + 46, 0, 0.7, 1.3), c_fade=False)
    pen.line(np.vstack([body, body[:1]]), 4.0, tone=0.85, seed=s + 3, taper=(0, 0), head=0.3)
    pen.line(np.vstack([neck[[3, 0]], neck[[1, 2]]]), 3.4, tone=0.8, seed=s + 4, taper=(0.05, 0.05))
    pen.lift(tube([(cx - 26, by - 60), (cx - 24, by - 16)], [3, 6, 3])[0], amt=0.5, seed=s + 5, soft=1.5)
    stems = [((cx - 4, by - 148), (cx - 40, by - 260), (cx - 70, by - 330)),
             ((cx + 4, by - 148), (cx + 20, by - 270), (cx + 58, by - 352)),
             ((cx, by - 148), (cx - 6, by - 250), (cx + 6, by - 300))]
    r = rng(s, 6)
    for k, (a, b, c) in enumerate(stems):
        pts = bez(a, b, c, 10)
        pen.line(pts, 2.6, tone=0.7, seed=(s, 7, k), role='detail', taper=(0.1, 0.5), dry=0.3, dry_from=0.6)
        for j in range(9):
            q = pts[-1] + P([r.uniform(-26, 26), r.uniform(-22, 18)])
            pen.line(P([pts[-3], q]), 1.4, tone=0.55, seed=(s, 8, k, j), role='detail', taper=(0.1, 0.3))
            pen.dot(q[0], q[1], r.uniform(3.0, 5.0), color='ink', tone=0.55, seed=(s, 9, k, j))


def counter(pen):
    s = 500
    top = P([(-40, WALL_Y), (W + 40, WALL_Y), (W + 40, bp(0, 0, 420)[1]), (-40, bp(0, 0, 420)[1])])
    pen.cover(top, seed=s)
    pen.fill(top, 'wood', seed=s + 1, tone=0.28, grad=(0, WALL_Y, 0, bp(0, 0, 420)[1], 0.75, 1.15), c_fade=False,
             broad=False, var=0.1)
    pen.hatch(top, angle=1.5, spacing=9, tone=0.15, color='wood_d', seed=s + 2, partial=0.45, bow=0.01)
    pen.line(D([(-40, WALL_Y), (900, WALL_Y - 2), (W + 40, WALL_Y + 1)], 40), 8, tone=0.85, color='wood_d',
             seed=s + 3, taper=(0.02, 0.05), head=0.4, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25)
    yf = bp(0, 0, 420)[1]
    pen.line(D([(-40, yf), (900, yf + 2), (W + 40, yf)], 40), 12, tone=0.9, color='wood_d', seed=s + 4,
             taper=(0.02, 0.05), head=0.5, lift=0.3, dry=0.5, dry_from=0.7, streak=0.3)
    cab = P([(-40, yf + 4), (W + 40, yf + 4), (W + 40, yf + 260), (-40, yf + 260)])
    pen.fill(cab, 'cabinet', seed=s + 5, grad=(0, yf + 10, 0, yf + 240, 0.8, 0.0))
    pen.light(900, WALL_Y + 160, 700, 220, amt=0.35, color='lamp', seed=s + 6)


def tape_roll(pen):
    s = 600
    c = bp(1490, 0, 120)
    rx, ry, th = 74.0, 74.0 * S2, 46.0 * C2
    pen.shade(ell(c[0] + 18, c[1] + 6, rx * 1.05, ry * 1.05, n=30), amount=0.35, seed=s, soft=8.0, hatch=False)
    side = np.vstack([ell(c[0], c[1] - th, rx, ry, 0, 180, 20), ell(c[0], c[1], rx, ry, 180, 0, 20)])
    topd = ell(c[0], c[1] - th, rx, ry, 0, 360, 36)
    hole = ell(c[0], c[1] - th, rx * 0.62, ry * 0.62, 0, 360, 30)
    pen.cover([side, topd], seed=s + 1, feather=0.8)
    pen.fill(side, 'wood', seed=s + 2, tone=0.30)
    pen.fill(topd, 'wood', seed=s + 3, tone=0.22, holes=[hole])
    pen.fill(hole, 'wood', seed=s + 4, tone=0.38)
    pen.line(topd, 3.6, tone=0.8, seed=s + 5, closed=True, taper=(0, 0))
    pen.line(hole, 2.8, tone=0.7, seed=s + 6, closed=True, taper=(0, 0))
    pen.line(ell(c[0], c[1], rx, ry, 5, 175, 20), 4.0, tone=0.85, seed=s + 7, taper=(0.05, 0.1))
    pen.lift(tube(ell(c[0], c[1] - th, rx * 0.82, ry * 0.82, 200, 250, 6), [2, 5, 2])[0], amt=0.5, seed=s + 8, soft=1.5)
    # 胶带头垂下来一截
    pen.line(P([(c[0] + rx - 6, c[1] - th + 4), (c[0] + rx + 10, c[1] + 20)]), 6, tone=0.3, seed=s + 9,
             taper=(0.05, 0.4), role='detail')


def scissors(pen):
    s = 650
    c = bp(380, 0, 160)
    for k, (dx, dy, rot) in enumerate(((0, 0, -20), (22, 30, 10))):
        ring = ell(c[0] + dx, c[1] + dy, 34, 20, 0, 360, 24, rot=rot)
        pen.line(ring, 7.0, tone=0.85, seed=(s, k), closed=True, taper=(0, 0))
    bl = P([(c[0] + 30, c[1] + 6), (c[0] + 240, c[1] - 70)])
    pen.line(bl, 9, tone=0.6, color='metal', seed=s + 2, taper=(0.05, 0.8))
    bl2 = P([(c[0] + 44, c[1] + 26), (c[0] + 246, c[1] - 52)])
    pen.line(bl2, 8, tone=0.5, color='metal', seed=s + 3, taper=(0.05, 0.8))
    pen.dot(c[0] + 52, c[1] + 10, 5, 5, color='ink', tone=0.9, seed=s + 4)


def box_back(pen):
    """纸箱：投影、里面的后壁、里面的东西（藏青围巾、几本书）、两片早已折进去的短盖。"""
    s = 700
    fl, fr = bp(BX0, 0, BD / 2), bp(BX1, 0, BD / 2)
    bl_, br_ = bp(BX0, 0, -BD / 2), bp(BX1, 0, -BD / 2)
    tbl, tbr = bp(BX0, BH, -BD / 2), bp(BX1, BH, -BD / 2)
    tfl, tfr = bp(BX0, BH, BD / 2), bp(BX1, BH, BD / 2)
    # 台面上的投影（光从左上来）
    pen.shade(P([fl + (40, 6), fr + (90, 6), br_ + (130, 0), tbr + (150, 40)]), amount=0.35, seed=s, soft=22.0,
              hatch=False)
    opening = np.vstack([tbl, tbr, tfr, tfl])
    pen.cover(opening, seed=s + 1, feather=0.8)
    # 里面的后壁（暗）
    pen.fill(opening, 'wood', seed=s + 2, tone=0.42, grad=(0, tbl[1], 0, tfl[1], 1.25, 0.8), c_fade=False,
             broad=False)
    pen.shade(P([tbl, tbr, tbr + (0, 60), tbl + (0, 60)]), amount=0.3, seed=s + 3, soft=10.0, hatch=False)
    # 几本书（竖着靠在后壁）
    r = rng(s, 4)
    x = BX0 + 130
    for k, (wb, hb, tn) in enumerate(((44, 250, 0.55), (58, 270, 0.25), (36, 232, 0.7), (50, 258, 0.4))):
        z = -BD / 2 + 40
        a, b = bp(x, hb, z), bp(x + wb, hb, z)
        q = np.vstack([a, b, bp(x + wb, 0, z), bp(x, 0, z)])
        q[:, 1] = np.minimum(q[:, 1], tfl[1] + 2)
        pen.cover(q, seed=(s, 5, k), feather=0.7)
        pen.fill(q, 'cloth' if tn < 0.3 else 'stone', seed=(s, 6, k), tone=tn, c_fade=False, broad=False)
        pen.line(np.vstack([q, q[:1]]), 3.0, tone=0.8, seed=(s, 7, k), taper=(0.05, 0.05))
        pen.line(P([(a[0] + wb * 0.5, a[1] + 14), (a[0] + wb * 0.5, a[1] + 60)]), 2.0, tone=0.5, seed=(s, 8, k),
                 role='detail', taper=(0.1, 0.1))
        x += wb + r.uniform(2, 6)
    # 藏青围巾：软软的一团叠在箱底前面，一头搭在左边箱沿外面
    sc = []
    cx = BX0 + 380
    for j in range(14):
        a_ = math.pi * 2 * j / 14
        rr = 1.0 + 0.08 * math.sin(3 * a_)
        sc.append(bp(cx + 220 * rr * math.cos(a_), 70 + 40 * math.sin(a_), 30 + 120 * rr * math.sin(a_)))
    sc = spline(P(sc), 4.0, closed=True)
    sc[:, 1] = np.minimum(sc[:, 1], tfl[1] + 30)
    pen.cover(sc, seed=s + 10, feather=0.7)
    pen.fill(sc, 'boy_sweater', seed=s + 11, tone=0.55, c_fade=False, broad=False,
             rgrad=(cx - 60, tfl[1] - 90, 10, 260, 0.8, 1.25))
    pen.hatch(sc, angle=80, spacing=7, tone=0.25, seed=s + 12, partial=0.6)
    for k in range(3):
        yy = tfl[1] - 90 + k * 34
        pen.line(P([(cx - 170 + 20 * k, yy), (cx - 40, yy - 8), (cx + 120, yy + 4), (cx + 190 - 20 * k, yy - 6)]),
                 3.0, tone=0.75, seed=(s, 13, k), role='detail', taper=(0.1, 0.2))
    pen.line(np.vstack([sc, sc[:1]]), 4.0, tone=0.85, seed=s + 14, taper=(0.02, 0.02), head=0.3)
    # 搭出去的那一头（带流苏）
    tail = P([tbl + (40, 40), tbl + (110, 56), fl + (-20, -80), fl + (-70, -40)])
    tail = P([(BX0 + 30, tfl[1] - 150), (BX0 + 120, tfl[1] - 140), (BX0 + 30, tfl[1] + 60), (BX0 - 40, tfl[1] + 40)])
    pen.cover(tail, seed=s + 15, feather=0.7)
    pen.fill(tail, 'boy_sweater', seed=s + 16, tone=0.55, c_fade=False, broad=False)
    pen.hatch(tail, angle=75, spacing=7, tone=0.25, seed=s + 17, partial=0.6)
    pen.line(np.vstack([tail, tail[:1]]), 4.0, tone=0.85, seed=s + 18, taper=(0.02, 0.02))
    for k in range(7):
        a = tail[3] + (tail[2] - tail[3]) * (k / 6.0)
        pen.line(P([a, a + (-6 + k, 34)]), 2.4, tone=0.7, seed=(s, 19, k), role='detail', taper=(0.05, 0.6))
    # 两片短盖（早已折进去，平压在两头）
    for k, (xa, xb) in enumerate(((BX0, BX0 + SIDE_F), (BX1 - SIDE_F, BX1))):
        q = np.vstack([bp(xa, BH, -BD / 2), bp(xb, BH, -BD / 2), bp(xb, BH, BD / 2), bp(xa, BH, BD / 2)])
        pen.cover(q, seed=(s, 20, k), feather=0.7)
        pen.fill(q, 'wood', seed=(s, 21, k), tone=0.28, c_fade=False, broad=False)
        pen.line(np.vstack([q, q[:1]]), 3.4, tone=0.75, seed=(s, 22, k), taper=(0.05, 0.05))


def box_front(pen):
    s = 800
    tfl, tfr = bp(BX0, BH, BD / 2), bp(BX1, BH, BD / 2)
    fl, fr = bp(BX0, 0, BD / 2), bp(BX1, 0, BD / 2)
    face = np.vstack([tfl, tfr, fr, fl])
    with pen.group('box_front', boil=0.4):
        pen.cover(face, seed=s, feather=0.8)
        pen.fill(face, 'wood', seed=s + 1, tone=0.30, grad=(BX0, 0, BX1, 0, 0.85, 1.15), c_fade=False, broad=False)
        pen.shade(P([fl + (0, -40), fr + (0, -40), fr, fl]), amount=0.25, seed=s + 2, soft=10.0, hatch=False)
        # 瓦楞纸的边：顶上一道双线
        pen.line(D([tfl, tfr], 30), 5.5, tone=0.88, seed=s + 3, taper=(0.03, 0.05), head=0.4)
        pen.line(D([tfl + (2, 6), tfr + (-2, 6)], 30), 2.0, tone=0.45, seed=s + 4, role='detail', taper=(0.05, 0.05))
        pen.line(D([tfl, fl], 20), 6.0, tone=0.9, seed=s + 5, taper=(0.05, 0.1), head=0.4)
        pen.line(D([tfr, fr], 20), 4.0, tone=0.7, seed=s + 6, taper=(0.05, 0.1), head=0.2, dry=0.4, dry_from=0.6)
        pen.line(D([fl, fr], 30), 6.5, tone=0.9, seed=s + 7, taper=(0.03, 0.06), head=0.4)
        # 两边的箱沿（从前上角到后上角）
        for k, x in enumerate((BX0, BX1)):
            pen.line(D([bp(x, BH, BD / 2), bp(x, BH, -BD / 2)], 20), 4.5 - k, tone=0.8, seed=(s, 8, k),
                     taper=(0.05, 0.05))
        pen.line(D([bp(BX0, BH, -BD / 2), bp(BX1, BH, -BD / 2)], 30), 3.2, tone=0.6, seed=s + 9, taper=(0.05, 0.05))
        # 记号笔写的几笔（看不清的字）+ 一条竖贴的旧胶带
        mx, my = BX0 + 380, tfl[1] + 120
        r = rng(s, 10)
        for k in range(3):
            xs = np.linspace(mx + k * 46, mx + k * 46 + 34, 5)
            ys = my + np.sin(xs * 0.3 + k) * 8 + r.normal(0, 2, 5)
            pen.line(np.stack([xs, ys], 1), 4.5, tone=0.8, seed=(s, 11, k), role='detail', taper=(0.1, 0.3))
        tq = P([(BX0 + 110, tfl[1]), (BX0 + 160, tfl[1]), (BX0 + 158, fl[1]), (BX0 + 112, fl[1])])
        pen.lift(tq, amt=0.25, seed=s + 12, soft=1.5)
        pen.line(D([tq[0], tq[3]], 20), 1.8, tone=0.4, seed=s + 13, role='detail')
        pen.line(D([tq[1], tq[2]], 20), 1.8, tone=0.4, seed=s + 14, role='detail')


def flap(pen, which, th, seed):
    q, tip, outer = flap_geom(which, th)
    if abs(q[0, 1] - q[3, 1]) < 2.5:
        pen.line(D([q[0], q[1]], 30), 5.0, tone=0.85, seed=(seed, 'edge'), taper=(0.03, 0.05))
        return
    pen.cover(q, seed=(seed, 'c'), feather=0.7)
    pen.fill(q, 'wood', seed=(seed, 'f'), tone=0.30 if outer else 0.20, c_fade=False, broad=False,
             grad=(0, float(q[0, 1]), 0, float(q[3, 1]), 1.1, 0.85))
    if not outer:
        pen.hatch(q, angle=0, spacing=10, tone=0.12, seed=(seed, 'h'), partial=0.5)
    pen.line(D([q[3], q[2]], 30), 4.6, tone=0.85, seed=(seed, 'tip'), taper=(0.03, 0.05), head=0.3)
    pen.line(D([q[0], q[3]], 20), 3.6, tone=0.75, seed=(seed, 'l'), taper=(0.05, 0.05))
    pen.line(D([q[1], q[2]], 20), 3.0, tone=0.6, seed=(seed, 'r'), taper=(0.05, 0.05))
    pen.line(D([q[0], q[1]], 30), 3.0, tone=0.6, seed=(seed, 'hinge'), taper=(0.05, 0.05), role='detail')


def text_mask(txt, font, size):
    key = (txt, font, size)
    if key not in _TXT:
        f = ImageFont.truetype(font, size)
        l, t_, r, b = f.getbbox(txt)
        im = Image.new('L', (r - l + 10, b - t_ + 10), 0)
        ImageDraw.Draw(im).text((5 - l, 5 - t_), txt, font=f, fill=255)
        _TXT[key] = np.asarray(im, np.float32) / 255.0
    return _TXT[key]


_TXT = {}


def background(pen):
    wall(pen)
    shelf(pen)
    shelf_jar(pen)
    vase(pen)
    counter(pen)
    tape_roll(pen)
    scissors(pen)
    box_back(pen)


# ================================================================= 动态
PATCH = P([(1180, 560), (1760, 520), (1860, 1180), (1270, 1230)])


def snow_shadows(pen, t):
    """窗光里雪的影子：一粒粒淡墨点斜着往下飘（只在光斑里）。"""
    r = rng(950)
    a, b, c, d = PATCH
    with pen.group('snow_sh', boil=0.5):
        for i in range(34):
            u = r.uniform(0, 1)
            v0 = r.uniform(0, 1)
            sp = r.uniform(0.10, 0.22)
            v = (v0 + sp * t) % 1.0
            u2 = (u - 0.04 * t * r.uniform(0.5, 1.5) + 0.02 * math.sin(2 * t + i)) % 1.0
            top = a + (b - a) * u2
            bot = d + (c - d) * u2
            p = top + (bot - top) * v
            fade = math.sin(math.pi * v)
            pen.dot(p[0], p[1], r.uniform(2.5, 5.0), color='ink', tone=0.22 * fade + 0.05, seed=('ssh', i))


def motes(pen, t):
    r = rng(960)
    a, b, c, d = PATCH
    with pen.group('motes', boil=0.3):
        for i in range(14):
            u = (r.uniform(0, 1) + 0.01 * math.sin(0.7 * t + i)) % 1.0
            v = (r.uniform(0, 1) - 0.02 * t * r.uniform(0.5, 1.5)) % 1.0
            top = a + (b - a) * u
            bot = d + (c - d) * u
            p = top + (bot - top) * v
            pen.dot(p[0], p[1], r.uniform(1.8, 3.2), color='snow', tone=0.0, seed=('smote', i))


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    oy = pan_y(t)
    with pen.view(1.0, 0.0, oy):
        cache = ('shelf', pen.d % 3, round(oy, 1))
        with pen.group('bg', boil=BG_BOIL, cache=cache):
            background(pen)
        snow_shadows(pen, t)
        motes(pen, t)
        with pen.group('mug_her', boil=0.45):
            mug(pen, HER_X, BASE_Y, E1, 'enamel', 0.05, +1, 'mug_her')
        mx, my, el = mug_path(t)
        in_box = t >= T_TRAVEL
        with pen.group('mug_his', boil=0.45):
            mug(pen, mx, my, el, 'cabinet', 0.34, -1, 'mug_his', band=True)
        if in_box or my > Y_REF - BH * C2 - 400:
            box_front(pen)
        th_b, th_f = flap_angles(t)
        with pen.group('flaps', boil=0.4):
            flap(pen, 'back', th_b, 'fb')
            flap(pen, 'front', th_f, 'ff')
        hp = hand_plan(t)
        if hp is not None:
            x, y, r, rot, mode = hp
            hands.hand_grip(pen, x, y, rot=rot, size=L_HAND, seed=('grip', 13), reach=r, frm=(-2.6, 0.9),
                            sleeve_len=2.2)
