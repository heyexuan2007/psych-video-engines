# -*- coding: utf-8 -*-
"""
第 9 镜（成片 34.20–36.64，C，句间）：门槛特写。
低机位贴着地板：上面是刚合上（还虚掩着一条缝）的门的下半截，门下沿和门槛之间透进一线冷光，右边门缝也是一道亮；
门槛内侧的木地板上留着他的三个雪脚印（鞋尖朝着门：他是走出去的）。时间快进：雪脚印慢慢塌下去、化成水，
湿的木头颜色变深，水面反着门缝的一点光；最后只剩几滩水印。门缝下还不断钻进来几片雪，往屋里滑一点就化了。
左边墙根是他留下的一双拖鞋（摆得整整齐齐），右边墙角靠着一把收起来的黑伞。

draw(pen, **kw)   kw：t 覆盖表演时间（成片秒，默认 pen.t）；melt 0..1 覆盖融化进度（三个脚印一起）
静态部分（墙、门、门槛、地板、拖鞋、伞）在第一个 group 里缓存（cache=('threshold', d % 3)）。
"""
import math

import cv2
import numpy as np

from core import densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, sstep, ease_io, lerp, W, H

T0, T1 = 34.20, 36.64
VP = (960.0, 300.0)                 # 地板缝的消失点（被门挡在后面）
DOOR_X = (240, 1676)                # 门扇左右
DOOR_BOT = 430                      # 门扇下沿
GAP = (430, 441)                    # 门下的缝
TH_TOP, TH_FRONT, FLOOR_Y = 441, 466, 494   # 门槛顶面、前沿、地板起点
CRACK_X = 1676                      # 右边虚掩的门缝
BG_BOIL = 0.4

# 三个雪脚印：中心、屏幕上的宽、高（透视压扁后）、旋转、左右脚、开始化的时刻
PRINTS = [
    dict(c=(1046, 562), w=62, h=78, rot=-5, side=1, t0=34.30),
    dict(c=(806, 664), w=78, h=100, rot=4, side=-1, t0=34.42),
    dict(c=(1094, 786), w=96, h=124, rot=-3, side=1, t0=34.55),
]
MELT_DUR = 1.75


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def P(pts):
    return np.float32(pts)


# ================================================================= 背景（静态）
def _wall(pen):
    s = 100
    wall = rect(-20, -20, W + 20, FLOOR_Y + 2)
    pen.fill(wall, 'wall', tone=0.62, seed=s, c_fade=False, grad=(0, 0, 0, FLOOR_Y, 1.0, 0.8), streak=0.2,
             sangle=88)
    # 踢脚线（门两边的墙根）
    for i, (x0, x1) in enumerate([(-20, 150), (1770, W + 20)]):
        b = P([[x0, FLOOR_Y - 34], [x1, FLOOR_Y - 34], [x1, FLOOR_Y], [x0, FLOOR_Y]])
        pen.cover(b, seed=s + 10 + i, feather=0.8)
        pen.fill(b, 'wood_d', tone=0.5, seed=s + 12 + i, c_fade=False)
        pen.line(D([(x0, FLOOR_Y - 34), (x1, FLOOR_Y - 35)], 30), 5, tone=0.8, color='wood_d', seed=s + 14 + i,
                 taper=(0.02, 0.2), head=0.3, dry=0.4, dry_from=0.6)


def _door(pen):
    s = 200
    x0, x1 = DOOR_X
    leaf = rect(x0, -20, x1, DOOR_BOT)
    pen.cover(leaf, seed=s, feather=0.6)
    pen.fill(leaf, 'wood', tone=0.60, seed=s + 1, c_fade=False, grad=(0, 0, 0, DOOR_BOT, 0.8, 1.0), streak=0.35,
             sangle=89)
    # 下面那块门板（凹进去）：下沿一道影、内框细线
    px0, px1, py1 = x0 + 150, x1 - 150, 278
    pen.shade(P([[px0, py1 - 18], [px1, py1 - 18], [px1, py1], [px0, py1]]), amount=0.35, seed=s + 2, hatch=False)
    pen.shade(P([[px0, -20], [px0 + 16, -20], [px0 + 16, py1], [px0, py1]]), amount=0.3, seed=s + 3, hatch=False)
    pen.line(D([(px0, -20), (px0 - 1, py1), (px1, py1 + 1), (px1 + 1, -20)], 30), 5, tone=0.7, color='wood_d',
             seed=s + 4, taper=(0.02, 0.05), head=0.3, dry=0.4, dry_from=0.6, split=False)
    pen.line(D([(px0 + 18, -20), (px0 + 17, py1 - 18), (px1 - 18, py1 - 17), (px1 - 17, -20)], 30), 2.4,
             tone=0.4, color='wood_d', seed=s + 5, taper=(0.02, 0.05), role='detail', dry=0.5, dry_from=0.4,
             split=False)
    # 木纹：几道长长的淡墨
    r = rng(s, 'grain')
    for k in range(7):
        y = r.uniform(300, 420) if k < 4 else r.uniform(10, 250)
        xa = r.uniform(x0 + 20, x0 + 400) if k % 2 else r.uniform(px0 + 40, px0 + 300)
        xb = xa + r.uniform(300, 700)
        pen.line(D([(xa, y), ((xa + xb) / 2, y + r.uniform(-3, 3)), (xb, y + r.uniform(-2, 2))], 40), 2.0,
                 tone=0.25, color='wood_d', seed=s + 10 + k, taper=(0.3, 0.4), role='detail', dry=0.7,
                 dry_from=0.2)
    # 门下沿：一道浓墨（门的厚度在阴影里）
    pen.fill(P([[x0, DOOR_BOT - 16], [x1, DOOR_BOT - 16], [x1, DOOR_BOT], [x0, DOOR_BOT]]), 'wood_d', tone=0.7,
             seed=s + 20, c_fade=False)
    pen.line(D([(x0 - 6, DOOR_BOT), (900, DOOR_BOT + 1), (x1 + 4, DOOR_BOT)], 30), 9, tone=0.92, color='wood_d',
             seed=s + 21, taper=(0.02, 0.1), head=0.5, lift=0.25, dry=0.45, dry_from=0.7, streak=0.25)
    # 门套（左右两条），落在地板上
    for i, (a, b) in enumerate([(150, x0), (x1 + 8, 1770)]):
        q = P([[a, -20], [b, -20], [b, FLOOR_Y - 2], [a, FLOOR_Y - 2]])
        pen.cover(q, seed=s + 30 + i, feather=0.6)
        pen.fill(q, 'wood', tone=0.5, seed=s + 32 + i, c_fade=False, grad=(a, 0, b, 0, 1.0, 0.75))
        pen.line(D([(a, -20), (a + 1, 240), (a, FLOOR_Y - 2)], 30), 10, tone=0.9, color='wood_d', seed=s + 34 + i,
                 taper=(0.02, 0.1), head=0.4, lift=0.3, dry=0.5, dry_from=0.6, streak=0.3)
        pen.line(D([(b, -20), (b - 1, 240), (b, FLOOR_Y - 2)], 30), 5, tone=0.7, color='wood_d', seed=s + 36 + i,
                 taper=(0.02, 0.2), head=0.2, dry=0.6, dry_from=0.5)


def _threshold(pen):
    s = 300
    top = P([[206, TH_TOP], [1712, TH_TOP], [1730, TH_FRONT], [188, TH_FRONT]])
    front = P([[188, TH_FRONT], [1730, TH_FRONT], [1730, FLOOR_Y + 2], [188, FLOOR_Y + 2]])
    pen.cover([top, front], seed=s, feather=0.6)
    pen.fill(top, 'wood', tone=0.30, seed=s + 1, c_fade=False, grad=(206, 0, 1712, 0, 1.0, 0.8))
    pen.fill(front, 'wood_d', tone=0.55, seed=s + 2, c_fade=False, grad=(0, TH_FRONT, 0, FLOOR_Y, 0.8, 1.0))
    pen.hatch(top, angle=1, spacing=5, tone=0.18, color='wood_d', seed=s + 3, partial=0.5)
    # 门槛被踩了多年：中间磨浅了一块
    pen.lift(ell(960, TH_TOP + 12, 380, 8), amt=0.35, seed=s + 4, soft=10.0)
    pen.line(D([(188, TH_FRONT), (900, TH_FRONT + 1), (1730, TH_FRONT)], 30), 10, tone=0.92, color='wood_d',
             seed=s + 5, taper=(0.02, 0.1), head=0.6, lift=0.3, dry=0.45, dry_from=0.7, streak=0.25, pool=0.2)
    pen.line(D([(188, FLOOR_Y + 2), (960, FLOOR_Y + 3), (1730, FLOOR_Y + 1)], 30), 6, tone=0.75, color='wood_d',
             seed=s + 6, taper=(0.02, 0.2), head=0.3, dry=0.6, dry_from=0.5)


def _floor(pen):
    s = 400
    fl = P([[-20, FLOOR_Y], [W + 20, FLOOR_Y], [W + 20, H + 20], [-20, H + 20]])
    # 地板：深夜的木头，往画面下沿淡出到纸（给歌词留白）
    pen.fill(fl, 'floor', tone=0.56, seed=s, c_fade=False, grad=(0, FLOOR_Y, 0, 980, 1.0, 0.22), streak=0.25,
             sangle=-2)
    vx, vy = VP
    # 地板缝：朝消失点汇聚，越往下越淡
    for k, xb in enumerate(np.arange(-900, 2900, 300)):
        ya, yb = FLOOR_Y + 2, 1000
        xa = vx + (xb - vx) * (ya - vy) / (H + 200 - vy)
        xb2 = vx + (xb - vx) * (yb - vy) / (H + 200 - vy)
        pen.line(D([(xa, ya), (xb2, yb)], 30), 3.2 + 2.0 * abs(xb - vx) / 1500, tone=0.55, color='wood_d',
                 seed=s + 10 + k, taper=(0.02, 0.7), head=0.1, dry=0.6, dry_from=0.35, fade=0.7, role='detail')
    # 错开的横缝（板头）
    r = rng(s, 'joint')
    for k in range(9):
        lane = r.integers(-3, 9)
        xb_a, xb_b = -900 + 300 * lane, -900 + 300 * (lane + 1)
        yy = r.uniform(520, 820)
        f = (yy - vy) / (H + 200 - vy)
        xa, xb_ = vx + (xb_a - vx) * f, vx + (xb_b - vx) * f
        pen.line(P([(xa + 3, yy), (xb_ - 3, yy + 1)]), 2.6, tone=0.42, color='wood_d', seed=s + 40 + k,
                 taper=(0.1, 0.2), role='detail', dry=0.5, dry_from=0.5)
    # 木纹
    for k in range(10):
        xb = r.uniform(-600, 2500)
        y0, y1 = r.uniform(500, 600), r.uniform(650, 900)
        f0, f1 = (y0 - vy) / (H + 200 - vy), (y1 - vy) / (H + 200 - vy)
        pen.line(D([(vx + (xb - vx) * f0, y0), (vx + (xb - vx) * f1, y1)], 30), 1.8, tone=0.22, color='wood_d',
                 seed=s + 60 + k, taper=(0.3, 0.4), role='detail', dry=0.7, dry_from=0.2)
    # 门槛在地板上投下一道窄影
    pen.shade(P([[180, FLOOR_Y], [1740, FLOOR_Y], [1760, FLOOR_Y + 22], [160, FLOOR_Y + 22]]), amount=0.35,
              seed=s + 80, hatch=False, soft=6.0)


def _slippers(pen):
    """他的一双拖鞋：摆在左边门套旁，鞋尖朝屋里，整整齐齐（他换了鞋走的）。"""
    s = 500
    for i, (ox, oy, sc) in enumerate([(318, 552, 0.92), (352, 612, 1.0)]):
        L, Hh = 230 * sc, 30 * sc
        x0, y0 = ox, oy
        sole = spline(P([[x0, y0 + 6], [x0 + 20, y0 - 6], [x0 + L * 0.5, y0 - 8], [x0 + L - 18, y0 - 10],
                         [x0 + L, y0], [x0 + L - 12, y0 + Hh * 0.55], [x0 + L * 0.5, y0 + Hh * 0.62],
                         [x0 + 16, y0 + Hh * 0.55]]), 3.0, closed=True)
        vamp = spline(P([[x0 + 4, y0 + 2], [x0 + 18, y0 - 30 * sc], [x0 + 70 * sc, y0 - 44 * sc],
                         [x0 + 128 * sc, y0 - 36 * sc], [x0 + 140 * sc, y0 - 4], [x0 + 60 * sc, y0 + 8]]), 3.0,
                      closed=True)
        pen.shade(ell(x0 + L * 0.55, y0 + Hh * 0.75, L * 0.55, 9 * sc), amount=0.4, seed=s + 10 * i, soft=5.0,
                  hatch=False)
        pen.cover([sole, vamp], seed=s + 10 * i + 1, feather=0.7)
        pen.fill(sole, 'cloth', tone=0.18, seed=s + 10 * i + 2, c_fade=False)
        pen.fill(P([[x0 + 10, y0 + Hh * 0.18], [x0 + L - 10, y0 + Hh * 0.10], [x0 + L - 14, y0 + Hh * 0.5],
                    [x0 + 14, y0 + Hh * 0.52]]), 'wood_d', tone=0.45, seed=s + 10 * i + 3, c_fade=False)
        pen.fill(vamp, 'boy_sweater', tone=0.55, seed=s + 10 * i + 4, c_fade=False)
        pen.shade(vamp, amount=0.3, seed=s + 10 * i + 5, angle=70, grad=(x0, 0, x0 + 140 * sc, 0, 0.2, 1.0))
        pen.line(sole[::2], 4.5, tone=0.85, seed=s + 10 * i + 6, closed=True, taper=(0, 0), head=0.3)
        pen.line(vamp[::2], 5, tone=0.9, seed=s + 10 * i + 7, closed=True, taper=(0, 0), head=0.4, dry=0.3,
                 dry_from=0.7)
        # 鞋面上的一道缝线
        pen.line(bez((x0 + 30 * sc, y0 - 18 * sc), (x0 + 70 * sc, y0 - 34 * sc), (x0 + 118 * sc, y0 - 22 * sc), 8),
                 2.0, tone=0.45, seed=s + 10 * i + 8, taper=(0.2, 0.2), role='detail')


def _umbrella(pen):
    """右边墙角靠着的一把收起来的黑伞（伞尖着地，伞柄出画）。"""
    s = 600
    tip = np.float32([1812, 640])
    top = np.float32([1858, -30])
    ax = top - tip
    n = np.float32([-ax[1], ax[0]]) / float(np.hypot(*ax))
    pts = []
    for u, wdt in [(0.0, 0), (0.06, 4), (0.25, 22), (0.55, 30), (0.8, 24), (1.0, 18)]:
        pts.append((tip + ax * u, wdt))
    left = [p + n * w for p, w in pts]
    right = [p - n * w for p, w in pts][::-1]
    body = spline(np.float32(left + right), 3.0, closed=True)
    pen.shade(ell(1822, 644, 40, 6), amount=0.4, seed=s, soft=4.0, hatch=False)
    pen.cover(body, seed=s + 1, feather=0.7)
    pen.fill(body, 'ink', tone=0.66, seed=s + 2, c_fade=False, grad=(1780, 0, 1890, 0, 1.0, 0.6))
    for k, u in enumerate((0.3, 0.5, 0.72)):
        a = tip + ax * u
        pen.line(P([a + n * 16, a + ax * 0.18 - n * 4]), 2.0, tone=0.35, seed=s + 10 + k, role='detail',
                 taper=(0.2, 0.3), color='graphite')
    band = tip + ax * 0.42
    pen.line(P([band + n * 30, band - n * 30]), 6, tone=0.9, seed=s + 20, taper=(0.1, 0.1))
    pen.lift(tube(P([tip + ax * 0.2 + n * 8, tip + ax * 0.95 + n * 12]), [1.5, 2.5])[0], amt=0.5, seed=s + 21,
             soft=1.0)
    pen.line(body[::3], 4, tone=0.9, seed=s + 22, closed=True, taper=(0, 0), head=0.3)
    pen.line(P([tip, tip - ax * 0.03]), 3, tone=0.9, seed=s + 23, taper=(0, 0.5))


def background(pen):
    _wall(pen)
    _door(pen)
    _floor(pen)
    _threshold(pen)
    _slippers(pen)
    _umbrella(pen)


# ================================================================= 动态
def cold_light(pen, t):
    """门下的缝、右边虚掩的门缝：一线冷光（水墨里光 = 留白），光落在门槛顶面和地板上。"""
    s = 700
    x0, x1 = DOOR_X
    with pen.group('coldlight', boil=0.5):
        gap = P([[x0, GAP[0]], [x1, GAP[0] - 1], [x1, GAP[1]], [x0, GAP[1] + 1]])
        pen.lift([gap], amt=0.96, seed=s, soft=1.2)
        crack = P([[CRACK_X - 3, -20], [CRACK_X + 6, -20], [CRACK_X + 8, GAP[1]], [CRACK_X - 2, GAP[1]]])
        pen.lift([crack], amt=0.95, seed=s + 1, soft=1.5)
        # 光漫到门槛顶面、门缝两侧
        pen.lift(P([[x0 + 40, TH_TOP], [x1 - 40, TH_TOP], [x1 - 10, TH_FRONT - 4], [x0 + 10, TH_FRONT - 4]]),
                 amt=0.62, seed=s + 2, soft=10.0)
        pen.lift(P([[x0 + 20, DOOR_BOT - 30], [x1 - 20, DOOR_BOT - 30], [x1, GAP[0]], [x0, GAP[0]]]), amt=0.25,
                 seed=s + 6, soft=12.0)
        pen.lift(P([[CRACK_X - 26, -20], [CRACK_X + 30, -20], [CRACK_X + 22, GAP[1]], [CRACK_X - 18, GAP[1]]]),
                 amt=0.22, seed=s + 3, soft=14.0)
        # 地板上：门缝那道光斜斜地铺到屋里
        wedge = P([[CRACK_X - 6, FLOOR_Y + 4], [CRACK_X + 12, FLOOR_Y + 4], [2080, H + 40], [1640, H + 40]])
        pen.lift([wedge], amt=0.42, seed=s + 4, soft=30.0)
        pen.lift(ell(960, FLOOR_Y + 40, 760, 60), amt=0.34, seed=s + 5, soft=30.0)


def _sole(pr, grow=0.0, rough=0.0, seed=0, n=56):
    """脚印轮廓（屏幕坐标）。鞋尖朝上（朝门）。grow 往外扩（像素，负 = 往里缩），rough 参差。"""
    cx, cy = pr['c']
    w, h = pr['w'], pr['h']
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    # 鞋底的极坐标轮廓：前掌宽、足弓收、脚跟圆
    v = -np.cos(th)                              # -1 鞋尖 … 1 脚跟
    half = 0.5 * w * (0.92 - 0.30 * np.exp(-((v - 0.25) / 0.22) ** 2) - 0.18 * np.clip(v - 0.55, 0, 1))
    side = np.sin(th)
    if pr['side'] < 0:                           # 左脚：足弓在右边
        arch = np.where(side > 0, 1.0, 0.82)
    else:
        arch = np.where(side < 0, 1.0, 0.82)
    x = half * side * np.where(np.abs(v - 0.25) < 0.35, arch, 1.0)
    y = 0.5 * h * v
    pts = np.stack([x, y], 1)
    nrm = pts / (np.hypot(pts[:, 0], pts[:, 1])[:, None] + 1e-6)
    if grow or rough:
        r = rng(seed, 'sole')
        ph = r.uniform(0, 6.28, 3)
        wob = (np.sin(3 * th + ph[0]) * 0.5 + np.sin(5 * th + ph[1]) * 0.3 + np.sin(9 * th + ph[2]) * 0.2)
        d = grow + rough * wob
        pts = pts + nrm * d[:, None]
    a = math.radians(pr['rot'])
    R = np.float32([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return (pts @ R.T + np.float32([cx, cy])).astype(np.float32)


def melt_of(pr, t, kw):
    if kw.get('melt') is not None:
        return float(kw['melt'])
    return float(ease_io((t - pr['t0']) / MELT_DUR))


def footprint(pen, pr, m, t, k):
    """一个雪脚印：m 0 = 刚踩下的雪印 → 1 = 一滩水印。"""
    s = 800 + 50 * k
    w = pr['w']
    with pen.group(f'print{k}', boil=0.6):
        # 1) 湿木头：水渍随融化往外洇开，木头颜色略深；水的边是一圈浓一点的墨（水墨画水 = 留白 + 边）
        if m > 0.04:
            wet = _sole(pr, grow=2 + 0.16 * w * m, rough=3 + 0.12 * w * m, seed=s)
            pen.shade([wet], amount=0.14 + 0.16 * m, seed=s + 1, hatch=False, soft=3.0 + 3 * m, rim=0.6)
            if m > 0.3:
                q = clamp((m - 0.3) / 0.4)
                pen.line(np.vstack([wet, wet[:1]]), 2.6, tone=0.50 * q, seed=s + 2, taper=(0.1, 0.1),
                         role='detail', dry=0.45, dry_from=0.35, split=False)
                # 水面：靠门那一半映着门缝的冷光（留白）
                cx, cy = pr['c']
                inner = _sole(pr, grow=-0.18 * w + 0.12 * w * m, rough=2 + 0.08 * w * m, seed=s + 11)
                inner = inner[inner[:, 1] < cy + 0.15 * pr['h']] if (inner[:, 1] < cy + 0.15 * pr['h']).sum() > 4                     else inner
                pen.lift([inner], amt=0.42 * q, seed=s + 12, soft=6.0)
        # 2) 雪：塌下去、缩小、边缘化开
        snow_amt = 1.0 - clamp(m / 0.82)
        if snow_amt > 0.02:
            sn = _sole(pr, grow=-0.42 * w * (1 - snow_amt) - 1, rough=2 + 0.10 * w * (1 - snow_amt), seed=s + 3)
            pen.lift([sn], amt=0.88 * (0.55 + 0.45 * snow_amt), seed=s + 4, soft=1.5 + 3 * (1 - snow_amt))
            # 鞋底纹（压出来的横纹），融化时先消失
            if snow_amt > 0.45:
                cx, cy = pr['c']
                a = math.radians(pr['rot'])
                cs, sn_ = math.cos(a), math.sin(a)
                for j, (v, hw) in enumerate([(-0.36, 0.30), (-0.24, 0.36), (-0.12, 0.37), (0.0, 0.33),
                                             (0.30, 0.22), (0.40, 0.24)]):
                    y = v * pr['h']
                    x0_, x1_ = -hw * w * 0.8, hw * w * 0.8
                    p0 = (cx + x0_ * cs - y * sn_, cy + x0_ * sn_ + y * cs)
                    p1 = (cx + x1_ * cs - y * sn_, cy + x1_ * sn_ + y * cs)
                    pen.line(P([p0, p1]), 2.2, tone=0.30 * (snow_amt - 0.45) / 0.55, seed=(s + 5, j),
                             taper=(0.2, 0.2), role='detail', color='graphite')
            # 边上的雪粒
            r = rng(s, 'grain')
            edge = _sole(pr, grow=-0.42 * w * (1 - snow_amt) + 2, seed=s + 3)
            for j in range(18):
                p = edge[r.integers(0, len(edge))] + r.normal(0, 2.5, 2)
                pen.dot(p[0], p[1], r.uniform(1.2, 2.6) * (0.4 + 0.6 * snow_amt), color='snow', tone=0.0,
                        seed=(s + 6, j))
            # 雪印的边：一笔淡墨（压实的雪和木头的分界）
            if snow_amt > 0.3:
                pen.line(np.vstack([sn, sn[:1]]), 2.0, tone=0.38 * snow_amt, seed=s + 7, taper=(0.1, 0.1),
                         role='detail', dry=0.5, dry_from=0.4, split=False)
        # 3) 水面反光：门缝的冷光在水里拉成一道细亮（朝门的方向），微微颤
        if m > 0.3:
            q = clamp((m - 0.3) / 0.45)
            cx, cy = pr['c']
            wob = 2.0 * math.sin(t * 7.0 + k * 1.7)
            hl = tube(P([(cx + 0.10 * w + wob, cy - 0.30 * pr['h']), (cx + 0.06 * w, cy - 0.02 * pr['h']),
                         (cx + 0.08 * w - wob * 0.5, cy + 0.20 * pr['h'])]), [0.6, 0.05 * w + 1.5, 0.6])[0]
            pen.lift([hl], amt=0.95 * q, seed=s + 8, soft=1.0)
            pen.lift(ell(cx - 0.18 * w, cy + 0.05 * pr['h'], 0.10 * w, 0.03 * pr['h'] + 1), amt=0.6 * q,
                     seed=s + 9, soft=1.5)


def flakes(pen, t):
    """门缝下钻进来的雪：贴着地板往屋里滑一小段，越近越大，然后化掉。"""
    with pen.group('flakes', boil=0.6):
        N, per = 26, 1.5
        for i in range(N):
            ph = (t + i * per / N) / per
            age = ph % 1.0
            cyc = math.floor(ph)
            r = rng(900, i, cyc)
            if r.random() < 0.25:
                continue
            x0 = r.uniform(320, 1620)
            vy = r.uniform(70, 170)
            vx = r.uniform(-50, 50) + (x0 - 960) * 0.05
            tt = age * per
            y = GAP[1] + 4 + vy * tt + 10 * tt * tt
            x = x0 + vx * tt + 8 * math.sin(3 * tt + i)
            if y < TH_TOP + 2:
                continue
            grow = 1.0 + 1.6 * clamp((y - GAP[1]) / 400)
            a = min(1.0, age / 0.12) * (1.0 - clamp((age - 0.6) / 0.4))
            if a < 0.08:
                continue
            sz = r.uniform(2.0, 3.6) * grow * (0.4 + 0.6 * a)
            pen.dot(x, y, sz, sz * 0.7, color='snow', tone=0.0, seed=('tf', i, cyc), rot=r.uniform(0, 180))
            # 化掉的地方留一个小湿点
            if age > 0.7:
                pen.shade(ell(x, y + 1, sz * 1.6, sz * 0.7, n=10), amount=0.25 * (age - 0.7) / 0.3,
                          seed=('tfw', i, cyc), hatch=False, soft=1.0)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    cache = ('threshold', pen.d % 3)
    if abs(pen.scale - 1.0) > 1e-6 or o.any():
        cache = cache + (round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))
    with pen.group('bg', boil=BG_BOIL, cache=cache):
        background(pen)
    cold_light(pen, t)
    for k, pr in enumerate(PRINTS):
        footprint(pen, pr, melt_of(pr, t, kw), t, k)
    flakes(pen, t)
