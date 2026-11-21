# -*- coding: utf-8 -*-
"""
第 16 镜（58.09–61.88，C 水墨）“第十四句歌词用来演”：深夜，窗前书桌上她的手（特写，从她身后看手背）。
她的右手立在窗玻璃前，一根红豆手链（红线 + 一颗红豆）的红线一圈圈缠上手指；红线另一头垂到桌面上、
拖过桌面，再升起来，从右边那扇推开一条缝的窗户（window_back.py 同款窗，放大 WB_S 倍）伸进外面的雪夜。
  “这一句”（58.21–58.91）缠线 wraps 0→2.5（手腕跟着轻轻拧）；
  “留恋”    （59.15–60.75）镜头沿着红线往右慢摇（pen.view 平移 PAN），摇到窗缝；
  “不放手”  （60.65–61.33）她攥紧（clench 0→1），红线一下子绷直（离开桌面，带一点回弹的颤），
             越来越红、越来越粗，周围的墨被提白成一圈光（为 T3 蓄力）。
红线是画面里唯一的颜色。结束时：拳头在画面左边，红线向右上绷到窗缝 —— 接 window_back 的背影。

draw(pen, **kw)   kw（都可省）：t 覆盖时间；wraps / clench / taut / glow / pan 覆盖各自的表演量
"""
import math

import numpy as np

from core import densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, ease_io, ease_in, ease_out, lerp, W, H
import hands
import window_back as wb

# ---------------------------------------------------------------- 时间
T0, T1 = 58.09, 61.88
T_WRAP0, T_WRAP1 = 58.21, 58.91     # 这一句
T_PAN0, T_PAN1 = 59.15, 60.75       # 留恋 → 摇到窗缝
T_GRIP = 60.65                      # 不放手

# ---------------------------------------------------------------- 构图（场景坐标；镜头 = pen.view(1, -pan, 0)）
PAN = 600.0
WB_S = 2.0                          # window_back 的窗框放大倍数（窗外的远景另画，远处的东西放大得少）
WB_OX, WB_OY = -242.0, -744.0       # → 窗缝在 x≈2010，窗台在 y≈640
DESK_Y = 692.0                      # 桌面后沿（窗台下沿）
HAND = (925.0, 470.0)               # 手背中心
HAND_L = 440.0
SLIT_X = (wb.MULL_R + wb.SLIT * 0.5) * WB_S + WB_OX
GL = tuple(np.float32(wb.GLASS) * WB_S + np.float32([WB_OX, WB_OY, WB_OX, WB_OY]))   # 玻璃（场景坐标）
MULL_L_X = wb.MULL_L * WB_S + WB_OX
SLIT_L = wb.MULL_R * WB_S + WB_OX
SLIT_R = SLIT_L + wb.SLIT * WB_S
K_PT = np.float32([SLIT_X, 150.0])  # 红线穿过窗缝的点
CURT = (430.0, 680.0)               # 左边窗帘
CANDLE = (300.0, 792.0)
TIN = (1290.0, 774.0)
MUG = (1630.0, 744.0)
BOOKS = (2250.0, 770.0)
POT = (2420.0, 640.0)
LAMP = (1500.0, 470.0)              # 窗外远处的一盏路灯

BG_BOIL = 0.4


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


# ================================================================= 表演
def wraps_amt(t):
    # 缠满 3 圈：线头正好回到小指外侧，出线不会横穿手背
    return 3.0 * float(ease_io((t - T_WRAP0) / (T_WRAP1 - T_WRAP0)))


def pan_amt(t):
    return PAN * float(ease_io((t - T_PAN0) / (T_PAN1 - T_PAN0)))


def clench_amt(t):
    a = ease_out(clamp((t - T_GRIP) / 0.42))
    b = ease_io(clamp((t - T_GRIP - 0.4) / 0.9))
    return float(0.82 * a + 0.18 * b)


def taut_amt(t):
    """红线绷直：0 松（拖在桌上）→ 1 直。'不'字一出来就猛地一拽。"""
    return float(ease_in(clamp((t - T_GRIP - 0.02) / 0.24)) ** 0.8)


def glow_amt(t):
    # 进镜头时已经有一点红，攥紧之后越来越红越亮
    return float(0.12 + 0.18 * ease_io((t - T0) / (T_GRIP - T0)) + 0.62 * ease_io((t - T_GRIP) / 1.1))


def hand_rot(t, w):
    """缠线时手腕跟着一圈圈轻轻拧；留恋时手慢慢往窗那边偏一点。"""
    twist = 4.0 * math.sin(2 * math.pi * w) * (1 - smooth01(w / 3.0) * 0.5)
    lean = 5.0 * float(ease_io((t - 59.0) / 1.8))
    return -2.0 + twist + lean


# ================================================================= 背景（静态）
def _desk(pen):
    s = 6100
    top = P([(-60, DESK_Y), (2600, DESK_Y), (2600, H + 30), (-60, H + 30)])
    pen.cover(top, seed=s)
    # 夜里的桌面：雪光从窗那边来，靠窗一溜亮、往镜头这边暗下去
    pen.fill(top, 'wood', tone=0.30, seed=s + 1, grad=(0, DESK_Y, 0, H, 0.45, 1.15), c_fade=False, streak=0.45,
             sangle=1.5)
    r = rng(s, 'grain')
    for k in range(7):
        y = DESK_Y + 40 + k * 52 + r.uniform(-8, 8)
        x0 = r.uniform(-60, 600) + (k % 3) * 500
        x1 = x0 + r.uniform(500, 900)
        pen.line(D([(x0, y), ((x0 + x1) / 2, y + r.uniform(-4, 4)), (x1, y + r.uniform(-3, 3))], 40), 2.6,
                 tone=0.26, color='wood_d', seed=s + 10 + k, taper=(0.3, 0.4), role='detail', dry=0.7, dry_from=0.2,
                 streak=0.3)
    # 桌面后沿：窗台的影子压在桌面上
    pen.shade([P([(-60, DESK_Y), (2600, DESK_Y), (2600, DESK_Y + 34), (-60, DESK_Y + 30)])], amount=0.35, seed=s + 2,
              angle=2, grad=(0, DESK_Y, 0, DESK_Y + 34, 1.0, 0.0), hatch=False)
    pen.line(D([(-60, DESK_Y + 1), (900, DESK_Y - 1), (1800, DESK_Y + 2), (2700, DESK_Y)], 40), 5, tone=0.7,
             color='wood_d', seed=s + 3, taper=(0.02, 0.1), head=0.3, lift=0.3, dry=0.6, dry_from=0.5, streak=0.25)


def _candle(pen):
    """烧到尽头的蜡烛（第 14 镜那根）：碟子里只剩一小截和一摊凝固的蜡。"""
    s = 6200
    cx, cy = CANDLE
    sau = ell(cx, cy, 104, 26)
    pen.cover(sau, seed=s)
    pen.fill(sau, 'enamel', tone=0.10, seed=s + 1, grad=(cx - 100, 0, cx + 100, 0, 0.4, 1.0), c_fade=False)
    pen.line(ell(cx, cy, 104, 26), 4.0, tone=0.78, seed=s + 2, closed=True, taper=(0, 0), head=0.3, dry=0.3,
             dry_from=0.6)
    pen.line(ell(cx, cy - 2, 78, 18, 10, 170, 14), 2.2, tone=0.4, seed=s + 3, role='detail', taper=(0.2, 0.2))
    # 凝固的蜡摊 + 一小截蜡烛
    pool = spline(P([(cx - 58, cy - 4), (cx - 20, cy - 16), (cx + 34, cy - 14), (cx + 62, cy - 2), (cx + 30, cy + 9),
                     (cx - 30, cy + 8)]), 4.0, closed=True)
    pen.fill(pool, 'cloth', tone=0.06, seed=s + 4, c_fade=False)
    pen.line(np.vstack([pool, pool[:1]]), 2.4, tone=0.5, seed=s + 5, role='detail', taper=(0, 0))
    stub = P([(cx - 22, cy - 46), (cx + 22, cy - 46), (cx + 24, cy - 6), (cx - 24, cy - 6)])
    pen.cover(stub, seed=s + 6)
    pen.fill(stub, 'cloth', tone=0.08, seed=s + 7, grad=(cx - 24, 0, cx + 24, 0, 0.3, 1.0), c_fade=False)
    pen.line(P([(cx - 22, cy - 46), (cx - 24, cy - 8)]), 3.0, tone=0.7, seed=s + 8, taper=(0.1, 0.2))
    pen.line(P([(cx + 22, cy - 46), (cx + 24, cy - 8)]), 3.4, tone=0.8, seed=s + 9, taper=(0.1, 0.2))
    pen.line(ell(cx, cy - 46, 22, 6), 2.6, tone=0.7, seed=s + 10, closed=True, taper=(0, 0))
    # 流下来的蜡泪
    pen.line(P([(cx + 10, cy - 44), (cx + 13, cy - 30), (cx + 11, cy - 22)]), 5.0, tone=0.25, seed=s + 11,
             role='detail', taper=(0.1, 0.6))
    # 烧黑弯倒的灯芯
    pen.line(P([(cx + 1, cy - 47), (cx + 3, cy - 58), (cx + 9, cy - 63)]), 3.2, tone=0.95, seed=s + 12,
             taper=(0.1, 0.4))


def _tin(pen):
    """装手链的小圆铁盒：盖子打开斜靠在一边，盒里垫着一块叠好的手帕，空了。"""
    s = 6300
    cx, cy = TIN
    rx, ry, h = 92.0, 30.0, 46.0
    body = np.vstack([ell(cx, cy - h, rx, ry, 180, 360, 20), ell(cx, cy, rx, ry, 0, 180, 20)])
    pen.cover(body, seed=s)
    pen.fill(body, 'metal', tone=0.32, seed=s + 1, grad=(cx - rx, 0, cx + rx, 0, 0.5, 1.2), c_fade=False,
             streak=0.4, sangle=90)
    # 盒身上一圈花纹带
    pen.line(ell(cx, cy - h * 0.45, rx, ry, 0, 180, 20), 2.4, tone=0.5, seed=s + 2, role='detail', taper=(0.1, 0.1))
    for k in range(9):
        a = math.radians(15 + k * 18)
        x = cx + rx * math.cos(a) * 0.98
        y = cy - h * 0.45 + ry * math.sin(a) * 0.98
        pen.dot(x, y + 7, 3.2, color='ink', tone=0.45, seed=(s + 3, k))
    # 盒口：里面是暗的，垫着手帕
    mouth = ell(cx, cy - h, rx - 3, ry - 2)
    pen.fill(mouth, 'ink', tone=0.55, seed=s + 4, c_fade=False)
    cloth = spline(P([(cx - 70, cy - h + 2), (cx - 30, cy - h - 18), (cx + 20, cy - h - 20), (cx + 70, cy - h - 6),
                      (cx + 50, cy - h + 14), (cx - 20, cy - h + 18)]), 4.0, closed=True)
    pen.fill(cloth, 'cloth', tone=0.05, seed=s + 5, c_fade=False)
    pen.line(np.vstack([cloth, cloth[:1]]), 2.2, tone=0.45, seed=s + 6, role='detail', taper=(0, 0))
    pen.line(bez((cx - 40, cy - h - 4), (cx, cy - h - 12), (cx + 44, cy - h - 2), 8), 1.8, tone=0.35, seed=s + 7,
             role='detail', taper=(0.2, 0.3))
    pen.line(ell(cx, cy - h, rx, ry), 3.8, tone=0.85, seed=s + 8, closed=True, taper=(0, 0), head=0.2)
    pen.line(P([(cx - rx, cy - h), (cx - rx + 1, cy)]), 3.6, tone=0.8, seed=s + 9, taper=(0.05, 0.1))
    pen.line(P([(cx + rx, cy - h), (cx + rx - 1, cy)]), 4.2, tone=0.9, seed=s + 10, taper=(0.05, 0.1))
    pen.line(ell(cx, cy, rx, ry, 0, 180, 20), 4.2, tone=0.88, seed=s + 11, taper=(0.05, 0.05), head=0.3)
    # 盖子：斜靠在盒子右边（一个倾斜的扁椭圆盘）
    lx, ly = cx + 132, cy - 22
    lid = ell(lx, ly, 34, 74, rot=14)
    pen.cover(lid, seed=s + 12)
    pen.fill(lid, 'metal', tone=0.24, seed=s + 13, grad=(lx - 30, 0, lx + 30, 0, 0.6, 1.1), c_fade=False)
    pen.line(ell(lx, ly, 34, 74, rot=14), 3.6, tone=0.85, seed=s + 14, closed=True, taper=(0, 0))
    pen.line(ell(lx - 3, ly, 24, 62, rot=14), 2.0, tone=0.45, seed=s + 15, closed=True, taper=(0, 0), role='detail')
    # 盒子和盖子在桌上的影
    pen.shade(ell(cx + 20, cy + 6, rx + 30, ry * 0.7), amount=0.3, seed=s + 16, angle=4, hatch=False, soft=6.0)


def _mug(pen):
    """她自己的杯子（他的那只已经收进纸箱了），茶还温着。"""
    s = 6400
    cx, cy = MUG
    rw, ry, h = 62.0, 16.0, 118.0
    body = np.vstack([ell(cx, cy - h, rw, ry, 180, 360, 18), P([(cx + rw, cy - h), (cx + rw - 4, cy)]),
                      ell(cx, cy, rw - 4, ry, 0, 180, 18), P([(cx - rw + 4, cy), (cx - rw, cy - h)])])
    pen.shade(ell(cx + 24, cy + 4, rw + 34, ry + 6), amount=0.3, seed=s, angle=4, hatch=False, soft=6.0)
    pen.cover(body, seed=s + 1)
    pen.fill(body, 'enamel', tone=0.12, seed=s + 2, grad=(cx - rw, 0, cx + rw, 0, 0.2, 1.0), c_fade=False)
    pen.shade([body], amount=0.22, seed=s + 3, angle=88, grad=(cx - rw, 0, cx + rw, 0, 0.0, 1.0))
    # 杯身上一道细线装饰
    pen.line(ell(cx, cy - h * 0.72, rw - 1, ry, 0, 180, 16), 2.0, tone=0.42, seed=s + 4, role='detail',
             taper=(0.1, 0.1))
    # 杯口 + 茶面
    pen.fill(ell(cx, cy - h, rw - 5, ry - 3), 'ink', tone=0.42, seed=s + 5, c_fade=False)
    pen.line(ell(cx, cy - h, rw, ry), 3.6, tone=0.85, seed=s + 6, closed=True, taper=(0, 0))
    pen.line(P([(cx - rw, cy - h), (cx - rw + 4, cy - 4)]), 3.4, tone=0.75, seed=s + 7, taper=(0.05, 0.1))
    pen.line(P([(cx + rw, cy - h), (cx + rw - 4, cy - 4)]), 4.2, tone=0.9, seed=s + 8, taper=(0.05, 0.1))
    pen.line(ell(cx, cy, rw - 4, ry, 0, 180, 18), 4.0, tone=0.88, seed=s + 9, taper=(0.05, 0.05))
    # 把手（右边）
    hd = ell(cx + rw + 4, cy - h * 0.52, 30, 36, -80, 80, 14)
    pen.line(hd, 12, tone=0.82, seed=s + 10, taper=(0.1, 0.1))
    pen.lift(tube(hd[2:-2] + P([-3, 0]), [1, 3, 1])[0], amt=0.5, seed=s + 11, soft=1.0)


def _books(pen):
    s = 6500
    bx, by = BOOKS
    for k, (dx, w, h, tn, rot) in enumerate(((0, 300, 34, 0.38, -1.0), (18, 270, 30, 0.22, 2.0))):
        y = by - k * 34
        c = math.cos(math.radians(rot)) * 0 + 1
        q = P([(bx - w / 2 + dx, y - h), (bx + w / 2 + dx, y - h + rot * 2), (bx + w / 2 + dx, y + rot * 2),
               (bx - w / 2 + dx, y)])
        pen.cover(q, seed=(s, k))
        pen.fill(q, 'cloth' if k else 'skirt', tone=tn, seed=(s + 1, k), c_fade=False)
        pen.line(np.vstack([q, q[:1]]), 3.4, tone=0.82, seed=(s + 2, k), taper=(0, 0))
        # 书页的线
        for j in range(3):
            yy = y - h + 8 + j * (h - 14) / 2
            pen.line(P([(bx + w / 2 + dx - 30, yy), (bx + w / 2 + dx - 4, yy + rot)]), 1.4, tone=0.35,
                     seed=(s + 3, k, j), role='detail', taper=(0.2, 0.2))
    # 书上一支铅笔
    pen.line(P([(bx - 110, by - 74), (bx + 60, by - 84)]), 7, tone=0.55, seed=s + 9, taper=(0.0, 0.0))
    pen.line(P([(bx + 60, by - 84), (bx + 82, by - 85)]), 4, tone=0.85, seed=s + 10, taper=(0.0, 0.9))
    pen.shade(P([(bx - 170, by + 2), (bx + 180, by + 2), (bx + 210, by + 22), (bx - 150, by + 20)]), amount=0.25,
              seed=s + 11, angle=2, hatch=False, soft=6.0)


def _pot(pen):
    """窗台上一小盆干了的满天星。"""
    s = 6600
    px, py = POT
    pot = P([(px - 40, py - 62), (px + 40, py - 62), (px + 30, py), (px - 30, py)])
    pen.cover(pot, seed=s)
    pen.fill(pot, 'terra', tone=0.34, seed=s + 1, grad=(px - 40, 0, px + 40, 0, 0.5, 1.1), c_fade=False)
    pen.line(np.vstack([pot, pot[:1]]), 3.4, tone=0.8, seed=s + 2, taper=(0, 0))
    pen.line(P([(px - 44, py - 62), (px + 44, py - 62)]), 8, tone=0.8, seed=s + 3, taper=(0, 0))
    r = rng(s, 'st')
    for k in range(9):
        a = r.uniform(-0.5, 0.5)
        L = r.uniform(70, 130)
        b0 = (px + r.uniform(-14, 14), py - 64)
        tip = (b0[0] + L * math.sin(a), b0[1] - L * math.cos(a))
        pen.line(bez(b0, (b0[0] + L * 0.3 * math.sin(a), b0[1] - L * 0.5), tip, 6), 2.0, tone=0.6, seed=(s + 4, k),
                 role='detail', taper=(0.05, 0.6))
        for j in range(4):
            pen.dot(tip[0] + r.uniform(-12, 12), tip[1] + r.uniform(-10, 8), r.uniform(2.6, 4.4), color='snow',
                    tone=0.0, seed=(s + 5, k, j))
            pen.dot(tip[0] + r.uniform(-12, 12), tip[1] + r.uniform(-10, 8), 1.6, color='ink', tone=0.5,
                    seed=(s + 6, k, j))


def _outside(pen):
    """窗外（场景坐标）：夜空、远处一排排压着雪的屋顶、几盏没睡的灯、一盏路灯。远景放大得少，所以比窗框“小”。"""
    s = 6000 + 200
    x0, y0, x1, y1 = GL
    glass = rect(x0, y0, x1, y1)
    pen.cover(glass, seed=s)
    pen.fill(glass, 'night', tone=0.52, seed=s + 1, grad=(0, -100, 0, y1, 1.0, 0.36), c_fade=False, streak=0.35,
             sangle=4)
    r = rng(6250)
    rows = [(0.14, 506, 14, 30, 50, 120), (0.28, 566, 22, 44, 70, 160), (0.46, 630, 30, 62, 90, 210)]
    for i, (tn, base, hmin, hmax, wmin, wmax) in enumerate(rows):
        top, chim = wb._roof_row(r, x0, x1, base, hmin, hmax, wmin, wmax)
        top = densify(top, 18)
        top[:, 0] = np.clip(top[:, 0], x0 - 4, x1 + 4)
        body = np.vstack([top, [[x1 + 4, y1 + 4], [x0 - 4, y1 + 4]]])
        pen.fill(body, 'roof', tone=tn, seed=s + 10 + i, grad=(0, float(top[:, 1].min()), 0, y1, 1.0, 0.75),
                 c_fade=False)
        for j, (cx, cy) in enumerate(chim):
            ch_ = rect(cx - 5 - i, cy - 12 - 3 * i, cx + 5 + i, cy + 10)
            pen.fill(ch_, 'roof', tone=tn + 0.1, seed=(s + 15, i, j), c_fade=False)
            pen.line(P([(cx - 6 - i, cy - 13 - 3 * i), (cx + 6 + i, cy - 13 - 3 * i)]), 3.5, tone=0.9, color='snow',
                     seed=(s + 16, i, j), role='detail', taper=(0.1, 0.1))
        th = 6.0 + 3.0 * i
        cap = np.vstack([top + P([0, -1.5]), (top + P([0, th]))[::-1]])
        pen.lift([cap], amt=0.92, seed=s + 20 + i, soft=1.2)
        pen.line(top + P([0, th + 1]), 2.0 + 0.6 * i, tone=0.40 + 0.14 * i, seed=s + 30 + i, taper=(0.05, 0.2),
                 role='detail', dry=0.45, dry_from=0.55, split=False)
        if i < 2:
            # 两排屋顶之间起一层雪雾（远的更淡）
            pen.lift([rect(x0, base + 6, x1, base + 40 + 10 * i)], amt=0.35, seed=s + 35 + i, soft=16.0)
    # 没睡的几盏灯（留白小方块）
    for i, (lx, ly, lw, lh) in enumerate([(1210, 560, 11, 13), (1730, 588, 10, 12), (2140, 556, 12, 13),
                                          (2380, 600, 11, 12), (860, 600, 10, 11), (1940, 610, 9, 10)]):
        q = P([[lx, ly], [lx + lw, ly + 1], [lx + lw - 1, ly + lh], [lx + 1, ly + lh - 1]])
        pen.lift(q, amt=0.85, seed=s + 40 + i, soft=0.8)
    # 远处一盏路灯：一圈被雪雾晕开的光
    lx, ly = LAMP
    pen.lift(ell(lx, ly, 120, 110), amt=0.42, seed=s + 50, soft=40.0)
    pen.lift(ell(lx, ly, 34, 30), amt=0.85, seed=s + 51, soft=8.0)
    pen.line(P([(lx + 2, ly + 6), (lx + 4, ly + 120), (lx + 5, 640)]), 4.0, tone=0.6, seed=s + 52, taper=(0.05, 0.1))
    pen.line(P([(lx - 10, ly + 2), (lx + 12, ly + 1)]), 5.0, tone=0.7, seed=s + 53, taper=(0.1, 0.1))
    # 窗缝：右扇推开一点，缝里是更深的夜
    sl = rect(SLIT_L, y0 + 8, SLIT_R, y1 - 4)
    pen.fill(sl, 'night', tone=0.95, seed=s + 80, c_fade=False, rim=0.0)
    pen.shade(rect(SLIT_R, y0 + 8, SLIT_R + 40, y1 - 4), amount=0.35, seed=s + 81, angle=90, soft=6.0)
    # 玻璃下沿的雾
    for i, (cx, cy, rx, ry) in enumerate([(900, 630, 200, 40), (1500, 636, 260, 26), (2300, 628, 220, 40)]):
        pen.lift(ell(cx, cy, rx, ry), amt=0.45, seed=s + 90 + i, soft=14.0)
    # 玻璃角上一点霜花（细细的提白枝杈）
    rr = rng(6290)
    for k in range(14):
        bx, by = (x0 + 6, y1 - 6) if k < 7 else (x1 - 6, y1 - 8)
        sg = 1 if k < 7 else -1
        a = rr.uniform(-1.4, -0.2)
        L = rr.uniform(30, 80)
        tip = (bx + sg * L * abs(math.cos(a)), by + L * math.sin(a))
        pen.line(P([(bx, by), tip]), 2.2, tone=0.9, color='snow', seed=(s + 95, k), role='detail', taper=(0.1, 0.8))


def _wall(pen):
    """墙（只画桌面以上看得见的部分）：靠窗处被雪光照得几乎留白，越往四角越暗。"""
    gl = rect(GL[0] + 6, GL[1] + 6, GL[2] - 6, GL[3] - 6)
    pen.fill([rect(-60, -20, 2720, DESK_Y + 6)], 'wall', tone=0.40, seed=6050, holes=[gl], c_fade=False,
             rgrad=(1678, 56, 760, 2500, 0.22, 1.15), streak=0.12, sangle=6, rough=0.08)


def background(pen):
    _wall(pen)
    _outside(pen)
    with pen.view(WB_S, WB_OX, WB_OY):
        wb._frame(pen)
    photo(pen)
    _desk(pen)
    _candle(pen)
    _tin(pen)
    _mug(pen)
    _books(pen)
    _pot(pen)


# ================================================================= 动态
def snow(pen, t):
    x0, y0, x1, y1 = GL
    r = rng(6600)
    with pen.group('snow', boil=0.6):
        for i in range(150):
            far = i < 95
            sp = r.uniform(20, 36) if far else r.uniform(50, 86)
            size = r.uniform(1.4, 2.6) if far else r.uniform(3.0, 5.4)
            amp = r.uniform(4, 14)
            fq = r.uniform(0.2, 0.6)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(0, x1 - x0)
            ys = r.uniform(0, 900)
            yy = (ys + sp * t) % 920 - 270
            xx = (xs - 12 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - x0 + 40) - 20 + x0
            if not (x0 + 4 < xx < x1 - 4 and yy < y1 - 6):
                continue
            if abs(xx - MULL_L_X) < 12 + size or SLIT_L - 12 - size < xx < SLIT_R + 22 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('tflake', i))
        # 从窗缝钻进来的几片雪：往屋里飘一点，慢慢落下、化掉
        for i in range(6):
            per = 3.0
            age = ((t + i * per / 6) % per) / per
            cyc = math.floor((t + i * per / 6) / per)
            rr = rng(6650, i, cyc)
            yy0 = rr.uniform(-40, 520)
            xx = SLIT_X - age * rr.uniform(60, 200)
            yy = yy0 + age * rr.uniform(60, 160) + 8 * math.sin(age * 6 + i)
            a = math.sin(math.pi * age)
            if a < 0.15:
                continue
            pen.dot(xx, yy, 3.6 * a + 1.0, color='snow', tone=0.0, seed=('tin', i, cyc))


def curtain(pen, t):
    """左边的窗帘：在半腰用一根布带束起来（上面垂、下面散开），从窗缝进来的风让下摆很轻地摆。下沿被桌子挡住。"""
    s = 6750
    l, r = CURT
    sw = 7.0 * math.sin(t * 0.9) + 3.0 * math.sin(t * 1.7 + 1.0)
    top, tie_y = -40, 400
    tie_x = l + (r - l) * 0.52
    edge_r = spline(P([(r + 6, top), (r - 10, 160), (tie_x + 26, tie_y - 30), (tie_x + 18, tie_y),
                       (tie_x + 40 + sw * 0.3, tie_y + 90), (r - 6 + sw * 0.8, 600), (r + 4 + sw, DESK_Y + 4)]), 6.0)
    edge_l = P([(l - 10, DESK_Y + 4), (l - 4, 400), (l - 12, top)])
    poly = np.vstack([edge_r, edge_l])
    with pen.group('curtain', boil=0.6):
        pen.cover(poly, seed=s, feather=0.8)
        pen.fill(poly, 'cloth', tone=0.26, seed=s + 1, grad=(l, 0, r, 0, 1.15, 0.55), c_fade=False, streak=0.1,
                 sangle=88)
        # 褶：上半截收向布带，下半截从布带散开
        for k, u in enumerate((0.18, 0.40, 0.62, 0.84)):
            xa = l + (r - l) * u
            xm = l + (tie_x - l) * (0.25 + 0.7 * u)
            up = bez((xa, top), (xa - 4, 200), (xm, tie_y - 6), 8)
            dn = bez((xm, tie_y + 6), (xm + 10 * u, tie_y + 120), (l + (r - l + sw) * u * 1.02, DESK_Y + 2), 8)
            for j, f in enumerate((up, dn)):
                band, _, _ = tube(f, [4, 14, 18] if j else [16, 12, 4])
                pen.shade([band], amount=0.16, seed=(s + 10, k, j), angle=88, soft=7.0, hatch=False)
                pen.line(f, 2.4, tone=0.30, seed=(s + 20, k, j), role='detail', taper=(0.2, 0.2), dry=0.6,
                         dry_from=0.35)
        lit = tube(edge_r[::4] - P([9, 0]), [4, 10, 10, 10, 6])[0]
        pen.lift([lit], amt=0.35, seed=s + 30, soft=4.0)
        pen.line(edge_r[::2], 5.5, tone=0.75, seed=s + 31, taper=(0.05, 0.05), head=0.3, dry=0.5, dry_from=0.5)
        # 布带
        band = spline(P([(l - 12, tie_y - 10), (tie_x, tie_y - 14), (tie_x + 24, tie_y - 4), (tie_x + 22, tie_y + 12),
                         (tie_x, tie_y + 10), (l - 12, tie_y + 14)]), 4.0, closed=True)
        pen.fill(band, 'cloth', tone=0.42, seed=s + 33, c_fade=False)
        pen.line(np.vstack([band, band[:1]]), 3.0, tone=0.7, seed=s + 34, taper=(0, 0))
        pen.line(bez((tie_x + 14, tie_y + 8), (tie_x + 22, tie_y + 40), (tie_x + 12 + sw * 0.4, tie_y + 70), 6), 3.0,
                 tone=0.6, seed=s + 35, role='detail', taper=(0.1, 0.5))
        # 窗帘被桌面挡住的下沿：一道影
        pen.shade([rect(l - 14, DESK_Y - 30, r + 16 + sw, DESK_Y + 2)], amount=0.22, seed=s + 32, angle=2,
                  grad=(0, DESK_Y - 30, 0, DESK_Y, 0.0, 1.0), hatch=False)


def photo(pen):
    """墙上一个小相框：两个人头挨着头的一张旧照（只用淡墨勾个影子）。"""
    s = 6780
    cx, cy, w, h = 190.0, 300.0, 150.0, 186.0
    fr = P([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2 + 3), (cx + w / 2 - 2, cy + h / 2), (cx - w / 2 + 1,
                                                                                                 cy + h / 2 - 2)])
    pen.cover(fr, seed=s)
    pen.fill(fr, 'wood_d', tone=0.55, seed=s + 1, c_fade=False)
    inner = P([(cx - w / 2 + 16, cy - h / 2 + 17), (cx + w / 2 - 16, cy - h / 2 + 19), (cx + w / 2 - 17, cy + h / 2 - 16),
               (cx - w / 2 + 16, cy + h / 2 - 17)])
    pen.fill(inner, 'paper', tone=0.0, seed=s + 2, c_fade=False)
    pen.cover(inner, seed=s + 3, amount=0.9)
    pen.fill(inner, 'ink', tone=0.16, seed=s + 4, grad=(0, cy - h / 2, 0, cy + h / 2, 0.4, 1.0), c_fade=False)
    # 两个头挨着：她（齐刘海短发）偏左、他偏右，肩膀连在一起
    for j, (hx, hy, rr, tn) in enumerate(((cx - 18, cy - 8, 22, 0.55), (cx + 20, cy - 14, 24, 0.5))):
        pen.fill(ell(hx, hy, rr, rr * 1.12), 'ink', tone=tn, seed=(s + 5, j), c_fade=False, rim=0.3)
    sh = spline(P([(cx - 58, cy + 76), (cx - 50, cy + 30), (cx - 10, cy + 16), (cx + 30, cy + 12), (cx + 56, cy + 30),
                   (cx + 60, cy + 76)]), 4.0)
    pen.fill(np.vstack([sh, [[cx + 60, cy + 78], [cx - 58, cy + 78]]]), 'ink', tone=0.32, seed=s + 6, c_fade=False)
    pen.line(np.vstack([fr, fr[:1]]), 3.6, tone=0.85, seed=s + 7, taper=(0, 0), head=0.2)
    pen.line(np.vstack([inner, inner[:1]]), 2.0, tone=0.6, seed=s + 8, taper=(0, 0), role='detail')
    # 挂绳和钉子
    pen.line(P([(cx - 40, cy - h / 2 + 2), (cx, cy - h / 2 - 40), (cx + 40, cy - h / 2 + 4)]), 2.0, tone=0.55,
             seed=s + 9, role='detail', taper=(0.1, 0.1))
    pen.dot(cx, cy - h / 2 - 40, 4.0, color='ink', tone=0.8, seed=s + 10)
    pen.shade(P([(cx - w / 2 + 6, cy + h / 2), (cx + w / 2 + 2, cy + h / 2 + 2), (cx + w / 2 + 12, cy + h / 2 + 14),
                 (cx - w / 2 + 14, cy + h / 2 + 12)]), amount=0.25, seed=s + 11, angle=2, hatch=False, soft=5.0)


def steam(pen, t):
    cx, cy = MUG
    per = 3.4
    with pen.group('steam', boil=0.8):
        for k in range(3):
            age = ((t + k * per / 3) % per) / per
            a = math.sin(math.pi * age) ** 1.4
            if a < 0.05:
                continue
            cyc = math.floor((t + k * per / 3) / per)
            r = rng(6700, k, cyc)
            bx = cx + r.uniform(-34, 30)
            yb = cy - 128 - age * 120
            L = 70 + 70 * age
            ys = np.linspace(yb, yb - L, 7)
            ph = r.uniform(0, 6.28)
            curl = r.uniform(8, 16) * (0.5 + age)
            xs = bx + curl * np.sin((ys - cy) * 0.035 + ph + t * 1.0) + (cy - ys) * 0.05
            path = np.stack([xs, ys], 1).astype(np.float32)
            w = 7 + 9 * age
            pen.lift(tube(path, [w * 0.4, w, w * 0.7, w * 0.3])[0], amt=0.45 * a, seed=(6710, k, cyc), soft=5.0)
            pen.line(path, w * 0.45, tone=0.12 * a, color='metal', seed=(6720, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.55, dry_from=0.1)


def smoke(pen, t):
    """灭了的蜡烛芯上最后一缕细烟，慢慢打着卷往上散。"""
    cx, cy = CANDLE
    x0, y0 = cx + 9, cy - 64
    with pen.group('smoke', boil=0.7):
        n = 26
        u = np.linspace(0, 1, n)
        ys = y0 - u * 330
        xs = x0 + 26 * u * np.sin(u * 7.0 - t * 1.6) + 40 * u ** 2 * math.sin(t * 0.5)
        path = np.stack([xs, ys], 1).astype(np.float32)
        pen.line(path[: int(n * 0.55)], 2.4, tone=0.45, seed=6800, role='detail', taper=(0.05, 0.6), dry=0.3,
                 dry_from=0.4)
        pen.line(path[int(n * 0.4):], 3.6, tone=0.24, seed=6801, role='detail', taper=(0.3, 0.9), dry=0.7,
                 dry_from=0.1, fade=0.7)


def _resample(Pp, n):
    seg = np.linalg.norm(np.diff(Pp, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], n)
    return np.stack([np.interp(u, s, Pp[:, 0]), np.interp(u, s, Pp[:, 1])], 1).astype(np.float32)


def thread_path(t, O, taut, glow):
    """红线从手上离开的点 O → 窗缝 K。松：垂到桌面上拖过去再升到窗缝；紧：一条直线（带一点回弹的颤）。
    → (窗内段 N×2, 在桌面上的程度 N, 窗外段)"""
    O = np.float32(O)
    K = K_PT
    pull = 0.25 * float(ease_io((t - 59.3) / 1.2))       # 留恋：她轻轻往回收了一点，桌上的线短了一点
    sway = 4.0 * math.sin(t * 1.3)
    slack = P([O, O + (55, 110), (O[0] + 130, 814), (1190 + 60 * pull, 834), (1450 + 40 * pull, 842 - 4 * pull),
               (1730 + 20 * pull, 826), (1880 + sway, 730 - 30 * pull), (1965 + sway * 0.5, 430), K])
    slack = spline(slack, 6.0)
    n = 90
    S = _resample(slack, n)
    on_desk = np.clip((S[:, 1] - 790) / 20.0, 0, 1)
    u = np.linspace(0, 1, n)[:, None]
    k = float(taut)
    # 一拽：线从手这头开始一段段离开桌面 —— 离地点 i* 沿着松线往窗缝走，手到离地点之间拉成直线
    fi = k * (n - 1)
    i0 = int(min(n - 1, math.floor(fi)))
    A = S[i0] + (S[min(n - 1, i0 + 1)] - S[i0]) * (fi - i0)
    m = i0 + 1
    if k <= 0:
        Pp = S.copy()
    else:
        q = np.linspace(0, 1, m)[:, None]
        Pp = np.vstack([O * (1 - q) + A * q, S[m:]]) if m < n else (O * (1 - u) + K * u)
        Pp = _resample(Pp.astype(np.float32), n)
    # 绷直的一瞬：沿线垂直方向衰减的颤
    tt = t - T_GRIP - 0.26
    if k >= 0.999 and -0.01 < tt < 0.7:
        # 绷直的一瞬“嗡”地颤几下（一拍二的画，每张换一边，越来越小）
        dv = K - O
        nv = np.float32([-dv[1], dv[0]]) / (np.hypot(*dv) + 1e-6)
        amp = 15.0 * math.exp(-max(tt, 0.0) * 6.0) * math.cos(max(tt, 0.0) * 12.0 * math.pi)
        Pp = Pp + np.outer(np.sin(np.pi * u[:, 0]) * amp, nv)
    on_desk = on_desk * (np.arange(n) >= m)
    # 窗外：从窗缝伸出去，往右上远处的雪夜里，越远越细越淡
    sag = 26.0 * (1 - k)
    out = P([K, K + (130, -10 + sag * 0.5), K + (300, -24 + sag), K + (520, -40 + sag * 0.6)])
    return Pp, on_desk, out


def red_line(pen, t, O, taut, glow):
    s = 6900
    Pp, on_desk, out = thread_path(t, O, taut, glow)
    g = glow
    # 桌面上的线投下一道淡影
    idx = np.nonzero(on_desk > 0.5)[0]
    if len(idx) > 4 and taut < 0.9:
        sh = Pp[idx[0]:idx[-1] + 1] + P([3, 6])
        with pen.group('thread_shadow', boil=0.5):
            pen.line(sh, 5.0, tone=0.28 * (1 - taut), seed=s, role='detail', taper=(0.2, 0.2), dry=0.3)
    with pen.group('redglow', boil=0.5):
        # 光晕：水墨里“亮”就是留白 —— 用半透明的 cover 把红线四周的墨挖淡（lift 只擦本层，挖不到下面）
        allp = np.vstack([Pp, out[1:3]])
        tub = tube(allp[::3], [8 + 30 * g, 12 + 42 * g, 12 + 42 * g, 6 + 14 * g])[0]
        pen.cover([tub], feather=8.0 + 18.0 * g, amount=0.08 + 0.72 * g, seed=s + 1)
        tub2 = tube(Pp[::3], [3 + 8 * g, 5 + 12 * g, 3 + 8 * g])[0]
        pen.cover([tub2], feather=3.0 + 3.0 * g, amount=0.12 + 0.6 * g, seed=s + 2)
        if g > 0.3:
            # 线芯周围洇出一点点红（微微发光）
            pen.fill([tub2], 'redline', tone=0.16 * (g - 0.3) / 0.7, seed=s + 6, c_fade=False, rim=0.0, soft=7.0)
    with pen.group('redline', boil=0.5):
        w = 4.6 + 5.4 * g
        tone = 0.70 + 0.34 * g
        pen.line(Pp, w, tone=tone, color='redline', seed=s + 3, taper=(0.0, 0.03), head=0.1, role='detail',
                 dry=0.0, split=False)
        pen.line(out, w * 0.8, tone=tone * 0.85, color='redline', seed=s + 4, taper=(0.0, 0.9), fade=0.85,
                 role='detail', dry=0.15, dry_from=0.6, split=False)
        if g > 0.4:
            # 最亮时线芯再压一道更浓的红
            pen.line(Pp, w * 0.45, tone=min(1.0, 0.6 + 0.5 * (g - 0.4)), color='redline', seed=s + 5,
                     taper=(0.02, 0.05), role='detail', dry=0.0, split=False)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    w = float(kw['wraps']) if kw.get('wraps') is not None else wraps_amt(t)
    c = float(kw['clench']) if kw.get('clench') is not None else clench_amt(t)
    k = float(kw['taut']) if kw.get('taut') is not None else taut_amt(t)
    g = float(kw['glow']) if kw.get('glow') is not None else glow_amt(t)
    pan = float(kw['pan']) if kw.get('pan') is not None else pan_amt(t)
    with pen.view(1.0, -pan, 0.0):
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        cache = ('thread_hands', pen.d % 3, round(float(o[0]), 1))
        with pen.group('bg', boil=BG_BOIL, cache=cache):
            background(pen)
        snow(pen, t)
        curtain(pen, t)
        steam(pen, t)
        smoke(pen, t)
        # 手：出线方向从“垂向桌面”转到“指向窗缝”；攥拳时手腕往拇指一侧拧过来（看得见拇指压住缠着线的四指）
        hx, hy = HAND
        rot = hand_rot(t, w)
        breath = 3.0 * math.sin(t * 1.6)
        yaw = 16.0 + 24.0 * float(ease_io(clamp(c * 1.2)))
        guess_out = np.float32([hx + 110, hy - 110])
        aim = math.degrees(math.atan2(K_PT[1] - guess_out[1], K_PT[0] - guess_out[0]))
        out_angle = lerp(62.0, aim, k)
        # 手上的线只加粗，不要手的红晕（红晕会把整个拳头染粉）；光晕由 red_line 的提白负责
        info = hands.hand_thread(pen, hx, hy + breath, rot=rot, size=HAND_L, seed=6000, wraps=w, clench=c,
                                 glow=0.0, thread_w=0.62 * (1.0 + 0.9 * g), out_angle=out_angle, out_len=0.06,
                                 tail=c < 0.45, yaw=yaw, sleeve_len=1.5, t=t)   # 攥紧后红豆被握进拳心
        red_line(pen, t, info['out'], k, g)
