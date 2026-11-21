# -*- coding: utf-8 -*-
"""
河边（第 17 镜 66.17–69.81 “示例歌词”、T3 的新风格一侧、第 19 镜 72.80–79.65 尾声）。
金色黄昏，太阳压在远山上，河从左前方流过来、拐个弯流向远处的落日。两人并肩坐在近岸草地上的背影（她左他右），
逆光：背影压暗，朝着太阳的轮廓镶一圈金边，长长的影子朝镜头这边拖过来。芦苇随风摆，河面一闪一闪地往远处流。

draw(pen, mode='together'|'ending', **kw)
  together  第 17 镜（也是 T3 新风格一侧，那时 t<66.17：她还没靠过去、镜头停在 1.04）。
            唱到“陪”（68.33）她把头靠到他肩上；两只鸟并排飞过；一根红线松松地连着两人的手。
            镜头用 pen.view 在 66.17–69.81 从 1.04 极慢拉到 1.0（以两人为中心）。
  ending    第 19 镜：同一构图、固定机位（1.0）。73.12–75.27（T4）他的不透明度 1→0（B、C 两侧一样）；
            C 一侧他是铅笔草稿（现实里他从来没被画完）。他淡出后她慢慢坐直，红线从她手里垂进河里，
            顺水漂向下游，末端消失在下游（落日方向）的雾里；雾只在 C 一侧。
  kw：t 覆盖时间；lean 覆盖靠肩程度 0..1；boy_op 覆盖他的不透明度；zoom 覆盖镜头倍数
patch_regions(mode='together') → (polys_list, angles)：T3 的 8 块（屏幕坐标，按 T3 时的镜头 1.04）。
"""
import math

import cv2
import numpy as np

from core import (densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, ease_io, ease_out, lerp, W, H)
import characters as ch
from characters import girl, boy
import window_back as wb

# ---------------------------------------------------------------- 时间
T17, T18 = 66.17, 69.81           # 第 17 镜
T19 = 72.80
T4A, T4B = 73.12, 75.27           # T4 冲淡
T_LEAN = 68.33                    # “陪”
CAM_C = (930.0, 700.0)            # 拉镜头的中心（两人）

# ---------------------------------------------------------------- 构图（场景坐标）
HZ = 470
SUN = (1190.0, 430.0)
SUN_R = 42.0
VP = (1180.0, 475.0)
RIV_UP = [(-40, 606), (180, 592), (420, 572), (660, 548), (860, 524), (1010, 503), (1110, 486), (1150, 478),
          (1166, 475)]
RIV_LO = [(-40, 776), (260, 756), (560, 736), (820, 716), (1060, 692), (1240, 658), (1360, 618), (1404, 580),
          (1376, 545), (1306, 514), (1240, 492), (1206, 480), (1192, 475)]
PAIR = dict(x=905.0, y=822.0, s=92.0, gap=1.6)
LONE_TREE = (1592.0, 612.0)

BG_BOIL = 0.25


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def river_poly():
    up = spline(P(RIV_UP), 6.0)
    lo = spline(P(RIV_LO), 6.0)
    return np.vstack([up, lo[::-1]])


def _resample(poly, n):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(poly, axis=0).T))]
    u = np.linspace(0, d[-1], n)
    return np.stack([np.interp(u, d, poly[:, 0]), np.interp(u, d, poly[:, 1])], 1).astype(np.float32)


_RIV = {}


def riv_uv(u, v):
    """河面参数坐标 → 场景坐标。u 0（左前方）…1（远处落日下），v 0 远岸 … 1 近岸。"""
    if 'up' not in _RIV:
        _RIV['up'] = _resample(spline(P(RIV_UP), 4.0), 400)
        _RIV['lo'] = _resample(spline(P(RIV_LO), 4.0), 400)
    u = np.clip(np.asarray(u, np.float32), 0, 1)
    k = u * 399
    i0 = np.floor(k).astype(int)
    i1 = np.minimum(i0 + 1, 399)
    f = (k - i0)[..., None]
    up = _RIV['up'][i0] * (1 - f) + _RIV['up'][i1] * f
    lo = _RIV['lo'][i0] * (1 - f) + _RIV['lo'][i1] * f
    v = np.asarray(v, np.float32)[..., None]
    return up * (1 - v) + lo * v, np.hypot(*(lo - up).T)


# ================================================================= 表演
def cam_zoom(t, mode):
    if mode == 'ending':
        return 1.0
    return 1.04 - 0.04 * ease_io((t - T17) / (T18 - T17))


def lean_amt(t, mode):
    if mode == 'ending':
        return 1.0 - ease_io((t - 74.35) / 1.5)
    return ease_io((t - (T_LEAN - 0.18)) / 0.85)


def boy_op(t, mode):
    if mode != 'ending':
        return 1.0
    return 1.0 - ease_io((t - T4A) / (T4B - T4A))


def thread_amt(t):
    """尾声：红线顺水漂出去的长度（0..1）。"""
    return ease_io((t - 73.5) / (77.6 - 73.5))


# ================================================================= 背景：天空、远山、远岸、河、草地（静态）
def _sky(pen, C):
    s = 5000
    sky = rect(-30, -30, W + 30, HZ + 12)
    # 上方：黄昏的紫；往下是珊瑚红、橙、地平线上一条金
    pen.fill(sky, '#5B4592', tone=0.16, seed=s, grad=(0, -30, 0, HZ, 1.0, 0.25), c_fade=False, b_angle=6,
             streak=0.3, sangle=2)
    if not C:
        pen.fill(rect(-30, 60, W + 30, HZ + 12), '#E0705E', seed=s + 1, grad=(0, 60, 0, 330, 0.0, 1.0), b_angle=8)
        pen.fill(rect(-30, 230, W + 30, HZ + 12), '#F79A48', seed=s + 2, grad=(0, 230, 0, 430, 0.0, 1.0),
                 b_angle=4)
        pen.fill(rect(-30, 360, W + 30, HZ + 12), '#FFC75A', seed=s + 3, grad=(0, 360, 0, 460, 0.0, 1.0),
                 b_angle=2)
        # 太阳周围一大团金光
        pen.fill(ell(SUN[0], SUN[1] + 10, 520, 250), '#FFD66A', seed=s + 4,
                 rgrad=(SUN[0], SUN[1], 40, 480, 1.0, 0.0), b_angle=0)
    # 云：几条长长的横云，靠近太阳的下沿被照亮
    clouds = [((60, 156), 720, 26, 0.9), ((860, 268), 700, 20, 0.6), ((1380, 112), 600, 22, 0.8),
              ((280, 318), 380, 14, 0.5), ((1500, 356), 420, 12, 0.4)]
    r = rng(5010)
    for i, ((x0, y0), L, th, dk) in enumerate(clouds):
        xs = np.linspace(x0, x0 + L, 14)
        top = y0 - th * (0.5 + 0.5 * np.sin(np.linspace(0, math.pi, 14))) * r.uniform(0.7, 1.2, 14)
        bot = y0 + th * 0.35 * np.sin(np.linspace(0, math.pi, 14))
        poly = np.vstack([np.stack([xs, top], 1), np.stack([xs[::-1], bot[::-1]], 1)]).astype(np.float32)
        poly = spline(poly, 6.0, closed=True)
        near = 1.0 - min(1.0, abs((x0 + L / 2) - SUN[0]) / 900)
        if C:
            pen.fill(poly, 'ink', tone=0.05 + 0.04 * dk, seed=s + 20 + i, rim=0.45, bloom=0.4)
        else:
            pen.fill(poly, '#B65A86' if dk > 0.55 else '#E77A72', seed=s + 20 + i, b_angle=4)
            under = np.stack([xs[1:-1], bot[1:-1] - 1.0], 1).astype(np.float32)
            pen.line(under, 3.5 + 3 * near, tone=0.9, color='#FFD47A', seed=s + 30 + i, role='detail',
                     taper=(0.3, 0.3), b_width=1.0)
    # 太阳
    sun = ell(SUN[0], SUN[1], SUN_R, SUN_R * 0.98, n=48)
    if C:
        pen.lift(sun, amt=0.9, seed=s + 40, soft=2.0)
        pen.line(ell(SUN[0], SUN[1], SUN_R, SUN_R * 0.98, 200, 520, 30), 2.4, tone=0.28, seed=s + 41,
                 role='detail', taper=(0.3, 0.4), dry=0.5, dry_from=0.3)
    else:
        pen.fill(sun, '#FFF2B4', seed=s + 40, b_clean=True)
        pen.light(SUN[0], SUN[1], 300, 190, amt=0.55, color='sun', seed=s + 42)


def _mountains(pen, C):
    s = 5100
    far = [(-40, 420), (120, 398), (260, 410), (420, 384), (560, 400), (700, 418), (820, 432), (940, 446),
           (1060, 458), (1140, 466), (1250, 462), (1360, 446), (1480, 428), (1600, 408), (1720, 394), (1840, 404),
           (1960, 390)]
    mid_l = [(-40, 448), (90, 430), (220, 440), (360, 422), (500, 444), (640, 458), (780, 466), (900, 471),
             (960, 473)]
    mid_r = [(1290, 473), (1420, 462), (1540, 448), (1660, 434), (1780, 440), (1960, 424)]
    layers = [(far, '#B37FA6', 0.14, 0), (mid_l, '#7C5C9A', 0.30, 1), (mid_r, '#7C5C9A', 0.30, 2)]
    for ridge, col, tn, k in layers:
        top = spline(P(ridge), 6.0)
        poly = np.vstack([top, [[top[-1, 0], HZ + 8], [top[0, 0], HZ + 8]]])
        if C:
            pen.fill(poly, 'ink', tone=tn, seed=s + k, grad=(0, float(top[:, 1].min()), 0, HZ + 8, 1.0, 0.35),
                     c_fade=False, rim=0.35)
            pen.line(top, 2.6 + 1.6 * k, tone=0.25 + 0.15 * k, seed=s + 10 + k, role='detail', taper=(0.1, 0.4),
                     dry=0.6, dry_from=0.3)
        else:
            pen.fill(poly, col, seed=s + k, grad=(0, float(top[:, 1].min()), 0, HZ + 8, 1.0, 0.75), b_angle=10)
            # 朝着太阳的山脊镶一道暖光
            d = np.abs(top[:, 0] - SUN[0])
            sel = top[d < 700]
            if len(sel) > 3:
                pen.line(sel + P([0, 1.5]), 3.0, tone=0.8, color='#FF9E5A', seed=s + 10 + k, role='detail',
                         taper=(0.4, 0.4), fade=0.3)


def _far_bank(pen, C):
    """远岸：地平线到河的远岸之间的一条地，上面一溜树（逆光的剪影）。"""
    s = 5200
    up = spline(P(RIV_UP), 6.0)
    land = np.vstack([[[-40, HZ - 2], [1172, HZ - 2]], up[::-1]])
    if C:
        pen.fill(land, 'ink', tone=0.38, seed=s, grad=(0, HZ, 0, 606, 0.6, 1.0), c_fade=False)
    else:
        pen.fill(land, '#4A2E5C', seed=s, b_angle=8)
        pen.fill(land, '#B85E4E', seed=s + 1, grad=(0, HZ, 0, 520, 0.6, 0.0), b_angle=8)
    # 右边近岸延伸到地平线的那片草甸
    lo = spline(P(RIV_LO), 6.0)
    i_far = int(np.argmax(lo[:, 0]))
    mead = np.vstack([lo[i_far:], [[1172, HZ - 2], [W + 30, HZ - 2], [W + 30, 640]], lo[i_far:i_far + 1]])
    if C:
        pen.fill(mead, 'ink', tone=0.16, seed=s + 2, c_fade=False)
    else:
        pen.fill(mead, '#A8743E', seed=s + 2, grad=(0, HZ, 0, 640, 0.9, 1.0), b_angle=6)
        pen.fill(mead, '#F2A24E', seed=s + 3, grad=(SUN[0], HZ, SUN[0] + 700, HZ + 120, 1.0, 0.0), b_angle=6)
    # 树：远岸一溜（左边近一些、大一些），右边草甸上几棵
    r = rng(5230)
    trees = []
    x = -30.0
    while x < 1080:
        uy = float(np.interp(x, up[:, 0], up[:, 1]))
        ty = HZ + (uy - HZ) * r.uniform(0.15, 0.55)
        sc = 0.5 + 0.9 * (1 - x / 1100)
        trees.append((x, ty, sc))
        x += r.uniform(30, 90) * (0.6 + 0.6 * sc)
    for x in (1480, 1530, 1600, 1760, 1830):
        trees.append((x + r.uniform(-10, 10), HZ + r.uniform(4, 14), 0.55 + r.uniform(0, 0.2)))
    for i, (tx, ty, sc) in enumerate(trees):
        hh = r.uniform(26, 48) * sc
        ww = r.uniform(18, 34) * sc
        n = 14
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        rr = 1 + 0.18 * r.standard_normal(n)
        crown = np.stack([tx + ww * np.cos(a) * rr, ty - hh * 0.62 + hh * 0.5 * np.sin(a) * rr], 1)
        crown = spline(crown.astype(np.float32), 3.0, closed=True)
        if C:
            # 水墨的树：一簇横点（米点），上浓下淡
            for j in range(9):
                ax = tx + r.uniform(-0.8, 0.8) * ww
                ay = ty - hh * 0.62 + r.uniform(-0.7, 0.6) * hh * 0.5
                pen.dot(ax, ay, ww * r.uniform(0.28, 0.42), ww * r.uniform(0.18, 0.28), color='ink',
                        tone=0.45 + 0.3 * r.random(), seed=(s + 40, i, j), rot=r.uniform(-15, 15), soft=1.5)
        else:
            pen.fill(crown, '#2C2046', seed=(s + 40, i), b_clean=True)
            # 朝太阳一侧的树冠边：一点暖光
            if tx < SUN[0]:
                arc = ell(tx, ty - hh * 0.62, ww * 0.95, hh * 0.48, -80, 10, 8)
                pen.line(arc, 2.0, tone=0.8, color='#FF9A5A', seed=(s + 60, i), role='detail', taper=(0.3, 0.3))
        pen.line(P([(tx, ty - hh * 0.2), (tx + 1, ty + 2)]), 2.2 * sc + 1, tone=0.7, seed=(s + 80, i),
                 role='detail', taper=(0.1, 0.1), color=None if C else '#2A1E3A')


def _river(pen, C):
    s = 5300
    rv = river_poly()
    pen.cover(rv, seed=s)
    if C:
        pen.fill(rv, 'ink', tone=0.10, seed=s + 1, c_fade=False, grad=(0, 476, 0, 776, 0.4, 1.0), streak=0.4,
                 sangle=3)
    else:
        # 河面映着天：近处深紫蓝，往远处（落日下）越来越暖
        pen.fill(rv, '#2E2C74', seed=s + 1, b_angle=4)
        pen.fill(rv, '#C85A78', seed=s + 2, grad=(500, 740, 1150, 480, 0.0, 1.0), b_angle=3)
        pen.fill(rv, '#FF9C4A', seed=s + 3, grad=(950, 640, 1180, 478, 0.0, 1.0), b_angle=3)
        # 远岸下沿：亮的天空倒映在贴岸的一窄条水里
        up = spline(P(RIV_UP), 6.0)
        band = np.vstack([up + P([0, 1]), (up + P([0, 12]))[::-1]])
        pen.fill(band, '#F4A060', seed=s + 4, b_angle=2)
    # 落日在水里的金色光路：从远处的落日下面一路铺到近岸，越近越宽
    path = spline(P([(1176, 477), (1162, 520), (1140, 590), (1112, 650), (1092, 690), (1280, 654), (1262, 590),
                     (1226, 520), (1196, 477)]), 4.0, closed=True)
    if C:
        pen.lift(path, amt=0.8, seed=s + 5, soft=6.0)
    else:
        pen.fill(path, '#FFD25A', seed=s + 5, rgrad=(1186, 478, 10, 240, 1.0, 0.45), b_angle=2)
    # 水纹：一道道横的短笔（近处长、远处短），静态的那一层
    r = rng(5340)
    for i in range(70):
        u = r.uniform(0.0, 0.97)
        v = r.uniform(0.08, 0.95)
        (p,), (wd,) = riv_uv([u], [v])
        L = wd * r.uniform(0.15, 0.5)
        a = P([p[0] - L / 2, p[1]])
        b = P([p[0] + L / 2, p[1] + r.uniform(-1.5, 1.5)])
        wl = max(1.4, wd / 70)
        if C:
            pen.line(np.stack([a, (a + b) / 2 + P([0, 1]), b]), wl * 0.9, tone=0.22, seed=(s + 10, i),
                     role='detail', taper=(0.3, 0.6), dry=0.7, dry_from=0.15)
        else:
            dark = r.random() < 0.6
            pen.line(np.stack([a, (a + b) / 2 + P([0, 1]), b]), wl * 1.6, tone=0.8,
                     color='#4A3A8C' if dark else '#E88A6A', seed=(s + 10, i), role='detail', taper=(0.3, 0.5))
    # 两岸的水边线
    up = spline(P(RIV_UP), 6.0)
    lo = spline(P(RIV_LO), 6.0)
    pen.line(up[::3], 3.0, tone=0.55, seed=s + 20, role='detail', taper=(0.05, 0.4), dry=0.5, dry_from=0.5,
             color=None if C else '#3A2448')
    pen.line(lo[::3], 4.5, tone=0.7, seed=s + 21, role='contour', taper=(0.05, 0.3), head=0.3, dry=0.4,
             dry_from=0.6, color=None if C else '#3A2448')
    # 近岸在水里的倒影（一条暗边）
    refl = np.vstack([lo + P([0, -1]), (lo + P([0, -9]))[::-1]])
    pen.shade(refl, amount=0.25, seed=s + 22, angle=0, soft=3.0)


def _grass(pen, C):
    s = 5400
    lo = spline(P(RIV_LO), 6.0)
    i_far = int(np.argmax(lo[:, 0]))
    bank = np.vstack([lo[:i_far + 1], [[W + 30, 640], [W + 30, H + 30], [-40, H + 30]]])
    pen.cover(bank, seed=s)
    if C:
        pen.fill(bank, 'ink', tone=0.18, seed=s + 1, grad=(0, 620, 0, H, 0.35, 1.0), streak=0.3, sangle=6)
        # 草：几丛短短的干笔（近处大、远处小、越远越稀），大部分留白
        r = rng(5410)
        lx, ly = lo[:i_far + 1, 0], lo[:i_far + 1, 1]
        for i in range(34):
            cy = 720 + (H + 10 - 720) * r.random() ** 0.7
            cx = r.uniform(-20, W + 20)
            if cx < 1400 and cy < float(np.interp(cx, lx, ly)) + 14:
                continue
            dep = (cy - 640) / (H - 640)
            for q in range(int(r.integers(2, 6))):
                xx = cx + r.uniform(-50, 50) * (0.4 + dep)
                yy = cy + r.uniform(-8, 8) * (0.4 + dep)
                hgt = (8 + 30 * dep) * r.uniform(0.6, 1.3)
                for j in range(int(r.integers(2, 5))):
                    ang = r.uniform(-0.5, 0.5) + 0.12
                    bx = xx + r.uniform(-4, 4) * (0.4 + dep)
                    pts = P([(bx, yy), (bx + hgt * 0.35 * math.sin(ang), yy - hgt * 0.55),
                             (bx + hgt * math.sin(ang) * 0.95, yy - hgt * math.cos(ang))])
                    pen.line(pts, 1.0 + 2.0 * dep, tone=0.25 + 0.4 * dep * r.uniform(0.6, 1.0), seed=(s + 2, i, q, j),
                             role='detail', taper=(0.05, 0.9), dry=0.6, dry_from=0.3)
    else:
        pen.fill(bank, '#5C5424', seed=s + 1, b_angle=80, grad=(0, 620, 0, H, 0.8, 1.0))
        # 逆光：近水那一溜草尖被照成金色，往镜头这边很快暗下去
        pen.fill(bank, '#E3A23E', seed=s + 2, grad=(0, 660, 0, 860, 1.0, 0.0), b_angle=84)
        pen.fill(bank, '#F7C65C', seed=s + 3, rgrad=(SUN[0] - 60, 640, 60, 560, 0.9, 0.0), b_angle=84)
        pen.hatch(bank, angle=98, spacing=7, tone=0.55, color='#3A3A1A', seed=s + 4, grad=(0, 780, 0, H, 0.0, 1.0))
        pen.hatch(bank, angle=82, spacing=9, tone=0.45, color='#FFD77A', seed=s + 5, grad=(0, 680, 0, 830, 1.0, 0.0))
        # 前景压暗（画框的“暗角”，把视线推向河和两个人）
        pen.shade([rect(-40, 860, W + 40, H + 30)], amount=0.30, seed=s + 6, angle=6, grad=(0, 860, 0, H, 0.0, 1.0),
                  color='#3A2448')
    # 右边草甸上一棵孤零零的树（中景）和它朝镜头拖过来的长影子
    tx, ty = LONE_TREE
    shd = spline(P([(tx - 30, ty - 2), (tx + 34, ty), (tx - 60, ty + 60), (tx - 260, ty + 150), (tx - 330, ty + 150),
                    (tx - 150, ty + 50)]), 6.0, closed=True)
    pen.shade(shd, amount=0.45 if not C else 0.22, seed=s + 20, angle=150, color=None if C else '#4A2A58', soft=6.0,
              grad=(tx, ty, tx - 300, ty + 150, 1.0, 0.3))


def pair_shadows(pen, C, op):
    """两人的影子：太阳在他们身后，两道影子朝镜头这边（左下）拖得很长，挨在一起。他的那道跟着他淡出。"""
    s = 5420
    x, y = PAIR['x'], PAIR['y']
    with pen.group('pair_shadow', boil=0.4):
        for j, (dx, wd_, a) in enumerate(((-62, 1.0, 1.0), (60, 1.1, op))):
            if a <= 0.01:
                continue
            bx = x + dx
            sh = spline(P([(bx - 46 * wd_, y - 2), (bx + 48 * wd_, y - 1), (bx - 40, y + 70), (bx - 150, y + 170),
                           (bx - 250, H + 40), (bx - 360 * wd_, H + 40), (bx - 220, y + 150), (bx - 90, y + 60)]),
                        6.0, closed=True)
            pen.shade(sh, amount=(0.62 if not C else 0.22) * a, seed=s + j, angle=118,
                      grad=(bx, y, bx - 300, H, 1.0, 0.3), color=None if C else '#3A2050', soft=6.0)


def lone_tree(pen, t, C):
    """右边中景的一棵树：树冠逆光（暗），朝太阳那边镶一道亮边，树叶随风轻轻动。"""
    s = 5480
    tx, ty = LONE_TREE
    sway = 2.0 * math.sin(t * 0.7)
    with pen.group('tree', boil=0.6):
        trunk = P([(tx - 5, ty + 2), (tx - 3, ty - 50), (tx + 2, ty - 95)])
        pen.line(trunk, 10, tone=0.85, seed=s, taper=(0.0, 0.5), color=None if C else '#2A1A2E', head=0.4)
        for j, (a, b) in enumerate((((tx - 2, ty - 70), (tx - 40, ty - 110)), ((tx + 1, ty - 84), (tx + 36, ty - 122)))):
            pen.line(P([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 6), b]), 5, tone=0.8, seed=s + 1 + j,
                     taper=(0.1, 0.6), color=None if C else '#2A1A2E', role='detail')
        r = rng(5490)
        blobs = [(tx - 46, ty - 128, 52, 36), (tx + 30, ty - 140, 56, 40), (tx - 6, ty - 170, 60, 42),
                 (tx + 60, ty - 110, 36, 26), (tx - 70, ty - 100, 34, 24)]
        for j, (bx, by, rx, ry) in enumerate(blobs):
            n = 16
            a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            rr = 1 + 0.16 * r.standard_normal(n)
            crown = np.stack([bx + sway * (1 - (by - ty + 200) / 200) + rx * np.cos(a) * rr,
                              by + ry * np.sin(a) * rr], 1).astype(np.float32)
            crown = spline(crown, 3.0, closed=True)
            if C:
                for q in range(7):
                    ax = bx + sway * 0.5 + r.uniform(-0.75, 0.75) * rx
                    ay = by + r.uniform(-0.7, 0.7) * ry
                    pen.dot(ax, ay, rx * r.uniform(0.26, 0.38), ry * r.uniform(0.22, 0.32), color='ink',
                            tone=0.5 + 0.3 * r.random(), seed=(s + 10, j, q), rot=r.uniform(-20, 20), soft=1.5)
            else:
                pen.fill(crown, '#3A2A50', seed=(s + 10, j), b_clean=True)
        for j, (bx, by, rx, ry) in enumerate(blobs[:3]):
            arc = ell(bx + sway, by, rx * 0.96, ry * 0.92, -70, 30, 8)
            if C:
                pen.lift(tube(arc, [1, 4, 1])[0], amt=0.6, seed=(s + 30, j), soft=1.0)
            else:
                pen.line(arc, 3.0, tone=0.9, color='#FFA845', seed=(s + 30, j), role='detail', taper=(0.3, 0.3))


def background(pen, C):
    _sky(pen, C)
    _mountains(pen, C)
    _far_bank(pen, C)
    _river(pen, C)
    _grass(pen, C)


# ================================================================= 动态
def glints(pen, t, C):
    """河面的碎光：每一点有自己的“一生”——亮起来、顺水往远处漂一小段、暗下去，再在别处亮起（不会跳）。
    光路（落日正下方）里最密最亮。"""
    r = rng(5600)
    with pen.group('glints', boil=0.5):
        for i in range(96):
            in_path = i < 42
            life = r.uniform(1.1, 2.4)
            off = r.uniform(0, 1)
            cyc_f = t / life + off
            cyc = math.floor(cyc_f)
            ph = cyc_f - cyc                                  # 0..1：这一生走到哪了
            q = rng(5601, i, cyc)                             # 每一生换一个位置
            if in_path:
                yv = q.uniform(0, 1) ** 0.8
                x = 1186 + q.uniform(-1, 1) * (8 + 95 * yv)
                y = 478 + 205 * yv
                # 顺水往远处（光路上就是往上、往落日）漂
                x += 3.0 * ph
                y -= (4 + 10 * yv) * ph
                wd = 30 + 160 * yv
            else:
                u = q.uniform(0, 0.93)
                v = q.uniform(0.1, 0.92)
                (p,), (wd,) = riv_uv([min(0.98, u + 0.012 * ph)], [v])
                x, y = float(p[0]), float(p[1])
            tw = 0.75 + 0.25 * math.sin(2 * math.pi * r.uniform(1.5, 3.0) * t + r.uniform(0, 6.3))
            a = math.sin(math.pi * ph) ** 1.5 * tw
            if a < 0.15:
                continue
            L = max(4.0, wd * q.uniform(0.05, 0.12)) * (0.6 + 0.6 * a)
            w = max(1.6, wd / 70) * (0.8 + 0.5 * a)
            pts = P([(x - L / 2, y), (x, y - 0.6), (x + L / 2, y + 0.3)])
            if C:
                pen.line(pts, w * 1.2, tone=0.9, color='snow', seed=('gl', i, cyc), role='detail', taper=(0.3, 0.3))
            else:
                pen.line(pts, w * 1.25, tone=0.9, color='#FFF4C8' if in_path or a > 0.7 else '#FFD27A',
                         seed=('gl', i, cyc), role='detail', taper=(0.3, 0.3))


def _reed_specs():
    r = rng(5700)
    out = []
    # 左前景一丛（高）
    for k in range(13):
        out.append((r.uniform(10, 290), H + 20 - r.uniform(0, 30), r.uniform(330, 520), r.uniform(-0.12, 0.10),
                    1.0, r.uniform(0, 6.28)))
    # 右前景一丛
    for k in range(11):
        out.append((r.uniform(1630, 1910), H + 20 - r.uniform(0, 30), r.uniform(300, 470), r.uniform(-0.08, 0.14),
                    1.0, r.uniform(0, 6.28)))
    # 近岸水边一小丛（左）、远一点（右，拐弯处）
    for k in range(8):
        bx = r.uniform(360, 640)
        by = float(np.interp(bx, P(RIV_LO)[:6, 0], P(RIV_LO)[:6, 1])) + r.uniform(4, 16)
        out.append((bx, by, r.uniform(90, 150), r.uniform(-0.1, 0.12), 0.45, r.uniform(0, 6.28)))
    for k in range(6):
        bx = r.uniform(1300, 1440)
        by = 600 + (bx - 1300) * 0.1 + r.uniform(0, 30)
        out.append((bx, by, r.uniform(60, 100), r.uniform(-0.1, 0.12), 0.32, r.uniform(0, 6.28)))
    return out


REEDS = _reed_specs()


def reed_geom(spec, t, k):
    bx, by, h, lean0, sc, ph = spec
    gust = 0.07 * max(0.0, math.sin(2 * math.pi * 0.13 * t + bx * 0.0021)) ** 2
    ang = lean0 + 0.05 * math.sin(2 * math.pi * 0.42 * t + ph + bx * 0.004) + gust
    tip = P([bx + h * math.sin(ang), by - h * math.cos(ang)])
    mid = P([bx + h * 0.5 * math.sin(ang * 0.4), by - h * 0.5 * math.cos(ang * 0.4)])
    stem = bez((bx, by), mid, tip, 10)
    # 芦花：在梢头，顺风垂下（风往右吹）
    d = (tip - stem[-3]) / (np.hypot(*(tip - stem[-3])) + 1e-6)
    wind = P([1.0, 0.25])
    L = h * 0.20
    a = tip - d * L * 0.35
    c = tip + (d * 0.35 + wind * 0.85) * L * (0.8 + 0.3 * math.sin(t * 1.3 + ph))
    m = (a + c) / 2 + P([0, -L * 0.12])
    axis = bez(a, m, c, 8)
    plume, _, _ = tube(axis, [L * 0.10, L * 0.24, L * 0.20, L * 0.06])
    return stem, plume, axis


def reeds(pen, t, C):
    with pen.group('reeds', boil=0.5):
        for k, spec in enumerate(REEDS):
            stem, plume, axis = reed_geom(spec, t, k)
            sc = spec[4]
            bx, by, h = spec[:3]
            # 叶：从下部伸出的两片长叶
            r = rng(5750, k)
            for j in range(2 if sc > 0.5 else 1):
                i0 = int(r.integers(1, 4))
                p0 = stem[i0]
                sgn = 1 if r.random() < 0.5 else -1
                lv = h * r.uniform(0.25, 0.45)
                tipl = p0 + P([sgn * lv * 0.55, -lv * 0.65])
                leaf = bez(p0, p0 + P([sgn * lv * 0.15, -lv * 0.6]), tipl + P([sgn * lv * 0.2, lv * 0.25]), 8)
                pen.line(leaf, 4.0 * sc + 1.5, tone=0.75, seed=(5760, k, j), role='detail', taper=(0.1, 0.8),
                         color=None if C else '#3E3A1C', head=0.3)
            pen.line(stem, 3.0 * sc + 1.2, tone=0.8, seed=(5770, k), role='detail', taper=(0.05, 0.3),
                     color=None if C else '#4A3222', head=0.2)
            if C:
                pen.fill(plume, 'ink', tone=0.22, seed=(5780, k), c_fade=False, rim=0.2, bloom=0.5)
                pen.line(axis, 1.6 * sc + 0.8, tone=0.5, seed=(5790, k), role='detail', taper=(0.2, 0.5), dry=0.7,
                         dry_from=0.2)
            else:
                pen.fill(plume, '#E9B66A', seed=(5780, k), b_clean=True)
                # 逆光：芦花朝太阳的一边亮得发白
                pen.line(axis + P([0.6, -0.08 * h * 0.2]), 1.5 * sc + 1.0, tone=0.9, color='#FFF0C0',
                         seed=(5790, k), role='detail', taper=(0.3, 0.5))


def motes(pen, t, C):
    """逆光里飘着的细小绒絮（芦花、草籽），被夕阳照得发亮，慢慢往右上飘（只在油画棒里，水墨的尾声不要）。"""
    if C:
        return
    r = rng(5800)
    with pen.group('motes', boil=0.4):
        for i in range(34):
            life = r.uniform(3.0, 6.0)
            off = r.uniform(0, 1)
            cf = t / life + off
            cyc = math.floor(cf)
            ph = cf - cyc
            q = rng(5801, i, cyc)
            x0, y0 = q.uniform(200, 1700), q.uniform(420, 860)
            x = x0 + 60 * ph + 8 * math.sin(t * 1.3 + i)
            y = y0 - 40 * ph + 5 * math.sin(t * 0.9 + 2 * i)
            near = (y0 - 420) / 440
            a = math.sin(math.pi * ph) * (0.6 + 0.4 * math.sin(t * 3.1 + i * 1.7))
            if a < 0.25:
                continue
            rr = 1.4 + 2.2 * near
            pen.dot(x, y, rr * (0.7 + 0.4 * a), color='#FFF0B8', tone=0.9, seed=('mote', i, cyc))


def birds(pen, t, C):
    t0, t1 = 66.45, 70.10
    if not (t0 < t < t1):
        return
    u = (t - t0) / (t1 - t0)
    with pen.group('birds', boil=0.4):
        for i, (dx, dy, ph) in enumerate(((0.0, 0.0, 0.0), (-38.0, 16.0, 0.42))):
            x = 540 + 980 * u + dx
            y = 262 - 70 * u + dy + 5 * math.sin(2 * math.pi * 0.6 * t + i)
            fl = math.sin(2 * math.pi * 2.6 * t + ph * 2 * math.pi)
            span = 22.0 - 3.0 * u
            for sg in (-1, 1):
                pts = P([(x, y), (x + sg * span * 0.45, y - 5 - 6 * fl), (x + sg * span, y - 2 - 11 * fl)])
                pen.line(pts, 3.4, tone=0.85, seed=('bird', i, sg), role='detail', taper=(0.05, 0.6),
                         color=None if C else '#2A1A30')


# ================================================================= 两个人
def _arm_sit_inner(t, args, rig=None):
    """坐在草地上的背影：靠他那只手撑在两人中间的草地上（给 girl 用；场景自己注册，避免改 characters）。"""
    near = dict(hand=np.float32(args['hand']), shape='flat', thumb=1, straight=True)
    far = dict(hand=rig.T([(-0.74, 1.58)])[0], shape='flat', thumb=1, straight=True)
    return dict(near=near, far=far)


ch.ARM_POSES.setdefault('rv_sit_inner', _arm_sit_inner)


def pair_poses(t, lean):
    s, x, y, gap = PAIR['s'], PAIR['x'], PAIR['y'], PAIR['gap']
    sb = 1.08 * s
    xg, xb = x - gap / 2 * s, x + gap / 2 * s
    br = (t + 0.2) / 3.8
    hg = (x - 0.10 * s, y + 0.04 * s)          # 她靠他那只手
    hb = (x + 0.11 * s, y + 0.09 * s)          # 他靠她那只手
    bp = dict(x=xb, y=y - 1.62 * sb, s=sb, back=True, pose='ground', seed=2000, yaw=180 + 6 * lean, pitch=-2,
              roll=3 * lean, tilt=2.0 * lean, breath=br + 0.3, boil=1.0, light=1.0,
              arm_far=dict(hand=hb, shape='flat', thumb=1, straight=True))
    gp = dict(x=xg, y=y - 1.62 * s, s=s, back=True, body='ground', seed=1000, tilt=11.0 * lean, roll=31.0 * lean,
              yaw=180 - 8 * lean, pitch=4 * lean, breath=br, boil=1.0, light=1.0, arm='rv_sit_inner',
              arm_args=dict(hand=hg))
    return gp, bp, hg, hb


def _mask_bbox(m):
    ys, xs = np.nonzero(m > 0.5)
    if len(xs) == 0:
        return None
    return max(0, ys.min() - 6), min(m.shape[0], ys.max() + 7), max(0, xs.min() - 6), min(m.shape[1], xs.max() + 7)


def backlit(pen, ops, C, seed, amt=1.0):
    """逆光：背影整体压暗（朝太阳的边留出来），朝太阳那圈轮廓镶金边（C 里是提白）。遮罩按屏幕坐标算。"""
    sc = 0.5
    m = wb.ops_mask(ops, sc, kinds=('cover',))
    bb = _mask_bbox(m)
    if bb is None:
        return
    y0, y1, x0, x1 = bb
    sub = m[y0:y1, x0:x1]
    big = cv2.resize(sub, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_LINEAR)
    big = (big > 0.5).astype(np.float32)
    X0, Y0 = x0 * 2, y0 * 2
    # 太阳在右前方、压得很低：把剪影往太阳方向挪几个像素，剪影里“挪出去”的部分就是朝光的边（右沿和头顶）
    v = np.float32([1.0, -0.42])
    v /= np.hypot(*v)
    k = 3.2
    M = np.float32([[1, 0, -v[0] * k], [0, 1, -v[1] * k]])
    shifted = cv2.warpAffine(big, M, (big.shape[1], big.shape[0]), flags=cv2.INTER_LINEAR, borderValue=0)
    rim = np.clip(big - shifted, 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 0.8)
    # 只要上半身（头、肩、手臂外沿）亮，下面贴着草地的部分不亮
    gy = np.clip((np.arange(big.shape[0], dtype=np.float32) / big.shape[0] - 0.80) / -0.35, 0, 1)[:, None]
    rim *= gy
    inner = cv2.erode(big, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    inner = cv2.GaussianBlur(inner, (0, 0), 3.0)
    with wb.screen_space(pen):
        if C:
            pen.shade(mask=(inner * 0.8, X0, Y0), amount=0.16 * amt, seed=seed, angle=80, soft=3.0)
            pen.lift(mask=(np.clip(rim * 1.6, 0, 1), X0, Y0), amt=0.75 * amt, seed=seed + 1, soft=0.6)
        else:
            pen.shade(mask=(inner, X0, Y0), amount=0.30 * amt, seed=seed, angle=78, color='#5A3A6E')
            pen.fill(mask=(np.clip(rim * 1.6, 0, 1), X0, Y0), color='#FFA640', seed=seed + 1, b_clean=True,
                     b_size=0.55)
            pen.lift(mask=(np.clip(rim * 1.0, 0, 1), X0, Y0), amt=0.30 * amt, seed=seed + 2, soft=0.5)


def couple(pen, t, mode, C, lean, op):
    """→ dict(girl=info, boy=info, hg, hb)。他在 op<1 时整组淡出；C 尾声里他是铅笔草稿。"""
    gp, bp, hg, hb = pair_poses(t, lean)
    ib = None
    if op > 0.004:
        sketch = C and mode == 'ending'
        if sketch:
            bp.update(opacity=0.62 * op, boil=2.1, erase=0.35 * (1 - op))
            boy(pen, bp, mode='sketch')
        else:
            with pen.group('boy_fade', opacity=op, boil=1.0):
                i0 = len(pen.ops)
                ib = boy(pen, bp, mode='full')
                backlit(pen, pen.ops[i0:], C, 5900)
    i0 = len(pen.ops)
    ig = girl(pen, gp)
    backlit(pen, pen.ops[i0:], C, 5950)
    return dict(girl=ig, boy=ib, hg=np.float32(hg), hb=np.float32(hb))


# ================================================================= 红线
def hand_line_pts(hg, hb, t):
    a = np.float32(hg) + P([3, 2])
    b = np.float32(hb) + P([-3, 3])
    sw = 2.5 * math.sin(t * 0.8)
    pts = P([a, a + P([-10, 12]), a + P([-22, 30 + sw]), a + P([-6, 44]), (a + b) / 2 + P([6, 40 + sw]),
             b + P([22, 34]), b + P([20, 16]), b + P([6, 4]), b])
    return a, b, pts


def hands_line(pen, hg, hb, t, C, op=1.0):
    """两人之间：红线从她的小指绕出来，松松地落在草地上（弯成一道 S），再绕上他的小指。"""
    a, b, pts = hand_line_pts(hg, hb, t)
    # 绕在她小指上的那一圈一直在（尾声里红线还在她手里）；连到他手上的那段和他手上那圈跟着他淡出
    with pen.group('handloop', boil=0.5):
        pen.line(ell(a[0], a[1] - 1, 7.0, 3.4, 160, 390, 10), 3.2, tone=1.0, color='redline', seed=5991,
                 role='detail', taper=(0.2, 0.2), split=False)
    if op <= 0.004:
        return
    ctx = pen.group('handline', boil=0.5, opacity=op) if op < 0.999 else pen.group('handline', boil=0.5)
    with ctx:
        pen.line(pts, 5.0, tone=1.0, color='redline', seed=5990, role='detail', taper=(0.0, 0.0), split=False,
                 head=0.0)
        pen.line(ell(b[0], b[1] - 1, 7.0, 3.4, 160, 390, 10), 3.2, tone=1.0, color='redline', seed=5992,
                 role='detail', taper=(0.2, 0.2), split=False)


def _thread_path(t):
    """尾声：从她的手到河里，顺着水流往下游（落日方向）一路漂到雾里的折线（场景坐标）。"""
    hg = P(pair_poses(t, 0.0)[2])
    land = P([hg + P([5, 1]), hg + P([30, -8]), (952, 806), (968, 770), (978, 736), (984, 712)])
    us = np.linspace(0.70, 0.995, 26)
    vs = np.linspace(0.80, 0.55, 26)
    # 河里：贴着近岸那一侧，顺着河道拐弯漂向远处
    pw, wd = riv_uv(us, vs)
    water = np.vstack([P([(1000, 702), (1040, 696)]), pw])
    # 只取 x 比入水点靠右的部分（河道参数在近处是从左边开始的）
    water = water[water[:, 0] >= 990]
    return land, water


def drift_thread(pen, t, C, g):
    """红线顺水漂远：g 0..1 漂出去的长度。水里那段横向轻轻摆（波往下游传），越远越细；末端被雾吞掉。"""
    if g <= 0.002:
        return
    land, water = _thread_path(t)
    allp = np.vstack([land, water[1:]])
    dense = spline(allp, 3.0)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(dense, axis=0).T))]
    Ltot = d[-1]
    n_land = float(np.r_[0, np.cumsum(np.hypot(*np.diff(spline(land, 3.0), axis=0).T))][-1])
    Lshow = n_land * min(1.0, g / 0.25) + (Ltot - n_land) * clamp((g - 0.15) / 0.85)
    keep = d <= Lshow
    if keep.sum() < 3:
        return
    Q = dense[keep].copy()
    dq = d[keep]
    # 水里的部分：横向摆动，越往下游越小（透视），波往下游传
    inw = np.clip((dq - n_land) / 60.0, 0, 1)
    far = np.clip((dq - n_land) / max(1.0, Ltot - n_land), 0, 1)
    T = np.gradient(Q, axis=0)
    T /= (np.hypot(T[:, 0], T[:, 1]) + 1e-6)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    wave = np.sin(dq * 0.045 - t * 2.2) * 6.0 * (1 - far) ** 1.4 * inw
    Q = Q + N * wave[:, None]
    step = max(1, len(Q) // 60)
    Qs = Q[::step]
    if len(Qs) < 3:
        return
    with pen.group('thread', boil=0.5):
        n = len(Qs)
        # 分三段画：近处粗、远处细、最远淡出
        cuts = [0, int(n * 0.45), int(n * 0.8), n]
        ws = [3.4, 2.5, 1.6]
        for j in range(3):
            a, b = cuts[j], min(n, cuts[j + 1] + 1)
            if b - a < 2:
                continue
            seg = Qs[a:b]
            last = (b >= n)
            pen.line(seg, ws[j], tone=1.0 - 0.2 * j, color='redline', seed=6000 + j, role='detail',
                     taper=(0.0, 0.85 if last else 0.0), fade=0.7 if (last and g > 0.85) else 0.0, split=False)
        # 水里的那段：上下两侧一点点水的反光/涟漪（入水处一圈）
        if g > 0.2:
            ex, ey = 984, 712
            pen.line(ell(ex + 4, ey + 2, 12, 3.2, 190, 350, 8), 1.8, tone=0.8, color='snow' if C else '#FFE6A8',
                     seed=6010, role='detail', taper=(0.3, 0.3))


def fog(pen, t, C):
    """下游的雾（C）：落日下那段河、远山脚都被雾吃掉——留白。"""
    if not C:
        return
    s = 6100
    with pen.group('fog', boil=0.5):
        pen.lift(ell(VP[0] + 10, VP[1] + 6, 330, 64), amt=0.92, seed=s, soft=26.0)
        pen.lift(ell(VP[0] - 40, VP[1] + 26, 520, 40), amt=0.6, seed=s + 1, soft=22.0)
        for i, (cx, cy, rx, ry, a) in enumerate([(820, 470, 560, 16, 0.5), (1500, 468, 420, 14, 0.5),
                                                 (1240, 520, 260, 22, 0.55)]):
            dx = 12 * math.sin(t * 0.25 + i)
            pen.lift(ell(cx + dx, cy, rx, ry), amt=a, seed=s + 10 + i, soft=14.0, dry=0.3, streak=0.4)


# ================================================================= 场景
def draw(pen, mode='together', **kw):
    t = float(kw.get('t', pen.t))
    C = pen.style == 'C'
    z = float(kw['zoom']) if kw.get('zoom') is not None else cam_zoom(t, mode)
    lean = float(kw['lean']) if kw.get('lean') is not None else lean_amt(t, mode)
    op = float(kw['boy_op']) if kw.get('boy_op') is not None else boy_op(t, mode)
    cx, cy = CAM_C
    with pen.view(z, cx * (1 - z), cy * (1 - z)):
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        cache = ('river', C, pen.d % 3, round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))
        with pen.group('bg', boil=BG_BOIL, cache=cache):
            background(pen, C)
        glints(pen, t, C)
        lone_tree(pen, t, C)
        pair_shadows(pen, C, op)
        if mode == 'ending':
            drift_thread(pen, t, C, thread_amt(t))
        info = couple(pen, t, mode, C, lean, op)
        hands_line(pen, info['hg'], info['hb'], t, C, 1.0 if mode == 'together' else op)
        reeds(pen, t, C)
        motes(pen, t, C)
        if mode == 'together':
            birds(pen, t, C)
        if mode == 'ending':
            fog(pen, t, C)


# ================================================================= T3：油画棒逐拍涂块的 8 块区域
T3_T = 64.0                  # 取这一刻的窗前姿势（转场中段）当“她”的剪影
T3_ANGLES = [90.0, 0.0, 345.0, 270.0, 180.0, 90.0, 90.0, 0.0]
_PATCH = {}


def _poly_to_mask(polys, sc=0.25):
    h, w = int(round(H * sc)), int(round(W * sc))
    m = np.zeros((h, w), np.uint8)
    for p in polys:
        p = np.asarray(p, np.float32).reshape(-1, 2)
        if len(p) >= 3:
            cv2.fillPoly(m, [np.round(p * sc * 16).astype(np.int32)], 255, cv2.LINE_8, shift=4)
    return m > 0


def _mask_to_polys(m, sc=0.25):
    """1/4 分辨率的布尔遮罩 → 屏幕坐标多边形（只有外轮廓；调用前保证没有洞）。"""
    cs, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    holes = 0
    for i, c in enumerate(cs):
        if hier is not None and hier[0][i][3] >= 0:
            holes += 1
            continue
        if cv2.contourArea(c) < 1.0 and len(c) < 3:
            continue
        out.append(c.reshape(-1, 2).astype(np.float32) / sc)
    return out, holes


def _dil(m, r):
    if r <= 0:
        return m
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.dilate(m.astype(np.uint8), k) > 0


def _fill_holes(m):
    """把被别的区域整个包住的“洞”切开：从每个洞往下开一道 1 像素宽的竖缝到区域外（缝留给后面的区域）。"""
    cs, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None:
        return m
    m = m.copy()
    for i, c in enumerate(cs):
        if hier[0][i][3] < 0:
            continue
        c = c.reshape(-1, 2)
        j = int(np.argmax(c[:, 1]))
        x, y = int(c[j, 0]), int(c[j, 1])
        while y < m.shape[0] and m[y, x]:
            m[y, x] = False
            y += 1
    return m


def patch_regions(mode='together', sc=0.25):
    """T3（C 窗前 → B 河边）每一拍涂满的区域：① 晚霞天空 ② 远山 ③ 河面 ④ 芦苇 ⑤ 河岸草地 ⑥ 她 ⑦ 他 ⑧ 两人手间的红线。
    → (polys_list, angles)。屏幕坐标，镜头 = T3 时河边那一侧的 1.04。
    窗前站着的她（和她手里伸向窗缝的红线）在 ⑥ 之前一直留着（①–⑤ 都绕开她），到第 6 拍才变成坐在河边的她；
    他、两人手间的红线同理留到 ⑦、⑧。"""
    key = (mode, sc)
    if key in _PATCH:
        return _PATCH[key]
    import core
    z = cam_zoom(T17 - 0.01, 'together')
    cx, cy = CAM_C
    ox, oy = cx * (1 - z), cy * (1 - z)

    def S(p):
        return np.asarray(p, np.float32) * z + np.float32([ox, oy])

    # ---- 人物剪影（录指令再栅格化 cover 区域）
    d = core.draw_index(T3_T)
    pw = core.Pen('C', d)
    gpw = wb.girl_pose(T3_T)
    iw = girl(pw, gpw)
    stand = wb.ops_mask(pw.ops, sc, kinds=('cover',)) > 0.5
    fist = iw.get('hand')
    pts, out = wb.line_path(T3_T, fist)
    wline = _poly_to_mask([tube(np.vstack([pts]), [7, 7, 7])[0]], sc)
    pr = core.Pen('B', core.draw_index(T17 - 0.01))
    with pr.view(z, ox, oy):
        gp, bp, hg, hb = pair_poses(T17 - 0.01, 0.0)
        i0 = len(pr.ops)
        boy(pr, bp, mode='full')
        i1 = len(pr.ops)
        girl(pr, gp)
        i2 = len(pr.ops)
    boy_m = wb.ops_mask(pr.ops[i0:i1], sc, kinds=('cover',)) > 0.5
    sit_m = wb.ops_mask(pr.ops[i1:i2], sc, kinds=('cover',)) > 0.5
    _, _, hl = hand_line_pts(hg, hb, T17 - 0.01)
    line_m = _poly_to_mask([tube(S(spline(hl, 3.0)), [26, 26, 26])[0]], sc)

    her = _dil(stand | sit_m, 1) | wline
    him = _dil(boy_m, 1) & ~her
    red = _dil(line_m, 1)
    protect = her | him | red

    # ---- 风景（场景坐标的多边形 → 屏幕）
    mts = []
    for ridge in ([(-40, 420), (120, 398), (260, 410), (420, 384), (560, 400), (700, 418), (820, 432), (940, 446),
                   (1060, 458), (1140, 466), (1250, 462), (1360, 446), (1480, 428), (1600, 408), (1720, 394),
                   (1840, 404), (1960, 390)],):
        top = spline(P(ridge), 6.0)
        mts.append(S(np.vstack([top, [[top[-1, 0], HZ - 1], [top[0, 0], HZ - 1]]])))
    mts_m = _poly_to_mask(mts, sc)
    sky_m = _poly_to_mask([S(rect(-60, -60, W + 60, HZ - 1))], sc) & ~mts_m
    river_m = _poly_to_mask([S(river_poly())], sc)
    # 芦苇：每一根（茎 + 芦花 + 叶）外扩一圈
    rd = []
    for k, spec in enumerate(REEDS):
        stem, plume, axis = reed_geom(spec, T17 - 0.01, k)
        rd.append(S(tube(stem, [14 * spec[4] + 8] * 3)[0]))
        rd.append(S(plume))
        hull = cv2.convexHull(np.vstack([stem, plume]).astype(np.float32)).reshape(-1, 2)
        rd.append(S(hull))
    reeds_m = _dil(_poly_to_mask(rd, sc), 2)
    land_m = np.ones_like(sky_m)          # 剩下的地面（近岸草地、远岸、右边草甸、那棵树）

    regions = []
    covered = np.zeros_like(sky_m)
    for m in (sky_m, mts_m, river_m, reeds_m, land_m):
        r = m & ~protect & ~covered
        covered |= r
        regions.append(r)
    regions += [her & ~covered, him & ~covered, (red | protect) & ~covered]
    polys_list = []
    for k, r in enumerate(regions):
        if k < 5:
            # 风景块：外扩 1 格盖住接缝，但不碰后面才涂的人物；万一包住了人物（洞），从洞往下切一道缝
            rr = _fill_holes(_dil(r, 1) & ~protect)
        else:
            # 人物块：洞里的东西前面几拍已经涂过了，直接填上（重叠部分会被前面的块优先占掉）
            rr = _dil(r, 1)
            cs, hier = cv2.findContours(rr.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            rr = np.zeros(rr.shape, np.uint8)
            cv2.drawContours(rr, cs, -1, 1, -1)
            rr = rr > 0
        polys, holes = _mask_to_polys(rr, sc)
        polys_list.append(polys)
    _PATCH[key] = (polys_list, list(T3_ANGLES))
    return _PATCH[key]
