# -*- coding: utf-8 -*-
"""
第 3 镜「示例歌词」（成片 8.83–11.97，C）：餐桌中景。
冬夜的厨房一角：左墙的窗外下着雪，吊灯垂在圆木桌正上方（灯光 = 水墨留白），墙上挂历、搁板上两只马克杯。
她站在桌子后沿（左），桌上一只搪瓷小锅、两只白瓷小碗；桌子后沿右边是他那把空椅子。
  8.95  用长柄木汤勺从锅里舀汤，倒进她面前的第一只碗（扶着碗）
  10.15 舀第二勺，倒进第二只碗
  10.86 把汤勺放回锅里；10.95–11.35 把第二只碗往空椅子那边推过去（身子跟着前倾）
  11.42–11.72 把一把勺子摆到那只碗旁边
  11.30–11.90 看着那只碗，轻轻笑了一下（wistful_smile）
动的东西：窗外的雪（两层）、锅和两只碗的热气、她的呼吸/眨眼。

draw(pen, **kw)   kw：t 覆盖表演时间（成片秒）；mode 保留（shots.py 传 'serve'）。

本文件同时是餐桌组（table_os / night_mcu / memory_table）共用的小道具库：
  window(pen, glass, mull_x, trans_y, mem)    窗（夜/白天）       snow(pen, t, glass, mull_x, trans_y, seed, n)
  lamp(pen, x, y, k, on)                       吊灯               round_table(pen, cx, cy, rx, ry, ...)
  small_bowl(pen, c, r, fill, seed)            白瓷碗（和 table_cu 同一画法：青花线、红豆汤）
  table_spoon(pen, c, ang, L, seed)            桌上的金属勺       steam(pen, t, c, w, h, seed, amt)
  pot(pen, c, rx, seed)                        搪瓷小锅（汤 + 红豆）  ladle_rest(pen, pot_c, rx, seed)
  chair_back(pen, x0, x1, top, bot, seed)      他那把椅子的椅背     calendar / shelf_mugs  墙上的小物件
"""
import math

import numpy as np

from core import W, H, densify, ell, bez, spline, tube, rng, clamp, smooth01, ease_io, lerp
import characters as ch

T0, T1 = 8.83, 11.97
# 表演时间点（成片秒）
T_L1, T_L1E = 8.95, 10.00        # 第一勺（u 0→1）
T_L2, T_L2E = 10.18, 10.78       # 第二勺
T_BACK = 10.86                   # 汤勺放回锅里
T_P0, T_P1 = 10.95, 11.35        # 推碗
T_S0, T_S1 = 11.42, 11.72        # 摆勺子
T_SMILE = 11.30                  # 轻轻笑

# 布局（场景坐标 = 屏幕坐标）
TABLE = dict(cx=1000, cy=702, rx=410, ry=90)
GLASS = (118, 150, 540, 500)
MULL_X, TRANS_Y = 330, 270
LAMP = (1000, 196)
VIEW_Z, VIEW_C = 1.32, (1010, 560)    # 取景：把这一角拍近一些（静止镜头）
S_G = 150
GIRL_X = 840
POT_C = (790, 652)
POT_RX = 72
BOWL_R = 42
BOWL_A = (888, 716)
BOWL_B0 = (1000, 684)
BOWL_B1 = (1075, 670)
SPOON0 = (1012, 730)     # 勺头中心（勺子原来放在第二只碗的右前方）
SPOON1 = (1112, 714)     # 摆到推过去的那只碗的前面
SPOON_ANG0 = 195.4       # 勺头 → 勺柄方向（度；和手里拿着时的方向一致）
CHAIR = (1170, 1352, 506)  # 他那把椅子：椅背左右、上沿


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def back_edge_y(x, tb=TABLE):
    u = (np.asarray(x, np.float32) - tb['cx']) / tb['rx']
    return tb['cy'] - tb['ry'] * np.sqrt(np.clip(1 - u * u, 0, 1))


def behind_table_poly(tb=TABLE, pad=3.0):
    """桌子后沿以上的可见区域（人站/坐在桌后时用作 clip_poly）。"""
    cx, cy, rx, ry = tb['cx'], tb['cy'], tb['rx'], tb['ry']
    xs = np.linspace(cx + rx, cx - rx, 48)
    arc = np.stack([xs, back_edge_y(xs, tb) + pad], 1)
    return np.vstack([[[cx + rx + 900, -60], [cx + rx + 900, cy]], arc,
                      [[cx - rx - 900, cy], [cx - rx - 900, -60]]]).astype(np.float32)


# ================================================================= 公用小道具
def wall(pen, light_c, tone=0.20, r0=330, r1=1250, rect_=(-20, -20, W + 20, H + 20), seed=700, mem=False):
    x0, y0, x1, y1 = rect_
    q = P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    lx, ly = light_c
    if mem:
        pen.fill(q, 'wall', seed=seed, rgrad=(lx, ly, r0, r1, 0.25, 1.0), c_fade=False)
    else:
        pen.fill(q, 'wall', seed=seed, tone=tone, rgrad=(lx, ly, r0, r1, 0.0, 1.0), c_fade=False, broad=False)


def window(pen, glass=GLASS, mull_x=MULL_X, trans_y=TRANS_Y, mem=False, seed=100, roofs=True, frame_w=1.0):
    """窗（kitchen.py 同一画法）：夜色 + 远处积雪的屋顶和亮着的小窗；mem=True 白天的雪景。"""
    s = seed
    x0, y0, x1, y1 = glass
    g = P([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    pen.cover(g, seed=s)
    if mem:
        pen.fill(g, 'sky', seed=s + 1, grad=(x1, y1, x0, y0, 0.55, 1.0), streak=0.3)
    else:
        pen.fill(g, 'night', seed=s + 1, grad=(x0 + 60, y0, x1 + 40, y1 + 80, 1.0, 0.55), streak=0.4)
    if roofs:
        w_, h_ = x1 - x0, y1 - y0
        tops = [[(0.00, 0.80), (0.08, 0.73), (0.18, 0.68), (0.28, 0.73), (0.36, 0.78)],
                [(0.33, 0.83), (0.44, 0.76), (0.56, 0.71), (0.66, 0.75), (0.76, 0.82)],
                [(0.74, 0.77), (0.84, 0.70), (0.93, 0.66), (1.00, 0.69)]]
        for i, top in enumerate(tops):
            tp = P([(x0 + a * w_, y0 + b * h_) for a, b in top])
            body = np.vstack([tp, [[tp[-1, 0], y1], [tp[0, 0], y1]]])
            pen.fill(body, 'roof', seed=s + 20 + i, grad=(0, float(tp[:, 1].min()), 0, y1 + 30, 1.0, 0.45))
            pen.line(tp, 10, tone=0.9, color='snow', seed=s + 30 + i, taper=(0.1, 0.2), role='detail', dry=0.45,
                     dry_from=0.3)
        if not mem:
            for i, (a, b) in enumerate([(0.09, 0.84), (0.21, 0.82), (0.47, 0.86), (0.58, 0.84), (0.86, 0.80),
                                        (0.94, 0.83)]):
                lx, ly = x0 + a * w_, y0 + b * h_
                q = P([[lx, ly], [lx + 13, ly + 1], [lx + 12, ly + 15], [lx + 1, ly + 14]])
                pen.cover(q, seed=s + 50 + i, feather=0.8)
                pen.fill(q, 'win_warm', seed=s + 55 + i)
    if mem:
        pen.lift(tube([(x0 + 40, y1 - 60), (x0 + 0.45 * (x1 - x0), y0 + 60), (x0 + 0.6 * (x1 - x0), y0 - 10)],
                      [16, 40, 20])[0], amt=0.4, seed=s + 70, soft=12.0)
    else:
        for i, (a, rx_, ry_) in enumerate([(0.12, 90, 40), (0.88, 76, 36), (0.5, 80, 15)]):
            pen.lift(ell(x0 + a * (x1 - x0), y1 - 6, rx_, ry_), amt=0.5, seed=s + 70 + i, soft=10.0)
    fw = frame_w
    pen.line(D([(x0 - 9, y0 - 14), (x0 - 13, (y0 + y1) / 2), (x0 - 10, y1 + 18)], 30), 15 * fw, tone=0.90,
             color='wood_d', seed=s + 80, taper=(0.08, 0.18), head=0.6, lift=0.3, dry=0.55, dry_from=0.62,
             streak=0.25, pool=0.25)
    pen.line(D([(x0 - 26, y0 - 6), ((x0 + x1) / 2, y0 - 12), (x1 + 24, y0 - 9)], 30), 16 * fw, tone=0.88,
             color='wood_d', seed=s + 81, taper=(0.05, 0.3), head=0.7, lift=0.35, dry=0.7, dry_from=0.55,
             streak=0.3, fade=0.2, pool=0.2)
    pen.line(D([(x1 + 12, y0 + 2), (x1 + 15, (y0 + y1) / 2), (x1 + 10, y1 - 30)], 30), 7 * fw, tone=0.55,
             color='wood_d', seed=s + 82, taper=(0.1, 0.6), head=0.3, dry=0.85, dry_from=0.15, streak=0.3,
             fade=0.4)
    pen.line(D([(mull_x + 2, y0 - 2), (mull_x - 1, (y0 + y1) / 2), (mull_x + 1, y1)], 30), 10 * fw, tone=0.80,
             color='wood_d', seed=s + 85, taper=(0.06, 0.2), head=0.45, lift=0.3, dry=0.45, dry_from=0.6,
             streak=0.2)
    pen.line(D([(x0 - 1, trans_y + 2), ((x0 + x1) / 2, trans_y - 2), (x1 + 1, trans_y + 1)], 30), 9 * fw,
             tone=0.74, color='wood_d', seed=s + 86, taper=(0.05, 0.25), head=0.45, lift=0.3, dry=0.55,
             dry_from=0.55, streak=0.2)
    sill = P([[x0 - 30, y1 + 5], [x1 + 38, y1 + 7], [x1 + 42, y1 + 27], [x0 - 34, y1 + 25]])
    pen.cover(sill, seed=s + 89)
    pen.fill(sill, 'wood', seed=s + 90, grad=(x0 - 30, 0, x1 + 40, 0, 1.0, 0.6))
    pen.shade(P([[x0 - 30, y1 + 17], [x1 + 38, y1 + 19], [x1 + 42, y1 + 27], [x0 - 34, y1 + 25]]), amount=0.3,
              seed=s + 93, angle=0)
    pen.line(D([(x0 - 44, y1 + 6), ((x0 + x1) / 2, y1 + 2), (x1 + 42, y1 + 8)], 30), 15 * fw, tone=0.92,
             color='wood_d', seed=s + 91, taper=(0.04, 0.15), head=0.7, lift=0.25, dry=0.45, dry_from=0.72,
             streak=0.25, pool=0.25)
    pen.line(D([(x0 - 30, y1 + 28), ((x0 + x1) / 2, y1 + 29), (x1 + 30, y1 + 26)], 30), 5 * fw, tone=0.55,
             color='wood_d', seed=s + 92, taper=(0.1, 0.4), head=0.2, dry=0.75, dry_from=0.35, streak=0.2)


def snow(pen, t, glass=GLASS, mull_x=MULL_X, trans_y=TRANS_Y, seed=1600, n=90, k=1.0, avoid=None):
    """窗外的雪：远处小而慢、近处大而快（两层），只在玻璃里，避开窗棂。k 尺寸系数。"""
    x0, y0, x1, y1 = glass
    r = rng(seed)
    with pen.group('snow', boil=0.6):
        for i in range(n):
            far = i < int(n * 0.62)
            sp = (r.uniform(18, 34) if far else r.uniform(40, 72)) * k
            size = (r.uniform(1.0, 2.1) if far else r.uniform(2.2, 4.0)) * k
            amp = r.uniform(3, 10) * k
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-20, x1 - x0 + 20)
            ys = r.uniform(0, y1 - y0 + 20)
            hh = y1 - y0 + 20
            yy = (ys + sp * t) % hh - 10 + y0
            xx = (xs + 7 * k * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - x0 + 40) - 20 + x0
            if not (x0 + 3 < xx < x1 - 3 and y0 + 3 < yy < y1 - 3):
                continue
            if (mull_x is not None and abs(xx - mull_x) < 8 * k + size) or \
                    (trans_y is not None and abs(yy - trans_y) < 7 * k + size):
                continue
            if avoid is not None and avoid(xx, yy):
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', seed, i))


def lamp(pen, x=LAMP[0], y=LAMP[1], k=1.0, on=True, seed=900, light=(300, 230, 0.45), top=-30):
    """吊灯（kitchen.py 同一画法）：灯罩、灯泡；on=True 时一团灯光（水墨 = 留白）。"""
    s = seed
    lx, ly = x, y
    pen.line(D([(lx + 1, top), (lx, ly - 2)], 30), 3.2 * k ** 0.7, tone=0.75, seed=s, taper=(0.0, 0.05), head=0)
    shade = P([[lx - 20 * k, ly - 2], [lx + 20 * k, ly - 2], [lx + 44 * k, ly + 16 * k], [lx + 86 * k, ly + 52 * k],
               [lx - 86 * k, ly + 52 * k], [lx - 44 * k, ly + 16 * k]])
    shade = spline(shade, 3.0, closed=True)
    pen.cover(shade, seed=s + 10, feather=0.8)
    pen.fill(shade, 'lampshade', seed=s + 1, grad=(lx - 86 * k, 0, lx + 86 * k, 0, 1.0, 0.8))
    pen.shade(P([[lx + 10 * k, ly - 2], [lx + 20 * k, ly - 2], [lx + 44 * k, ly + 16 * k], [lx + 86 * k, ly + 52 * k],
                 [lx + 30 * k, ly + 52 * k]]), amount=0.3, seed=s + 11)
    pen.lift(tube([(lx - 12 * k, ly + 6 * k), (lx - 40 * k, ly + 32 * k), (lx - 62 * k, ly + 48 * k)],
                  [4 * k, 9 * k, 4 * k])[0], amt=0.55, seed=s + 2, soft=1.5, dry=0.75, streak=0.5)
    pen.line(D([(lx - 92 * k, ly + 53 * k), (lx, ly + 58 * k), (lx + 92 * k, ly + 52 * k)], 20), 9 * k ** 0.7,
             tone=0.92, seed=s + 5, taper=(0.06, 0.2), head=0.6, lift=0.3, dry=0.35, dry_from=0.75)
    pen.line(spline(P([[lx - 20 * k, ly - 2], [lx - 44 * k, ly + 16 * k], [lx - 86 * k, ly + 52 * k]]), 3.0),
             4.5 * k ** 0.7, tone=0.75, seed=s + 6, taper=(0.1, 0.2), head=0.3)
    pen.line(ell(lx, ly + 62 * k, 18 * k, 12 * k, 15, 165, 10), 2.8 * k ** 0.7, tone=0.5, seed=s + 7,
             taper=(0.2, 0.4), head=0)
    if on:
        rx_, ry_, amt = light
        pen.light(lx, ly + 150 * k, rx_ * k, ry_ * k, amt=amt, color='lamp', seed=s + 8)


def round_table(pen, tb=TABLE, seed=1200, th=16, leg_bot=880, light=True, night=False, mem=False):
    """圆木桌（kitchen.py 同一画法）：桌面木色 + 木纹排线 + 灯光一抹；桌沿厚度；中心桌腿往下淡出（给歌词留白）。"""
    s = seed
    cx, cy, rx, ry = tb['cx'], tb['cy'], tb['rx'], tb['ry']
    leg = P([[cx - 16, cy + ry - 4], [cx + 16, cy + ry - 4], [cx + 13, leg_bot], [cx - 13, leg_bot]])
    pen.fill(leg, 'wood_d', seed=s + 5, grad=(0, cy + ry, 0, leg_bot - 5, 1.0, 0.0))
    pen.line(D([(cx - 16, cy + ry), (cx - 15, (cy + ry + leg_bot) / 2), (cx - 16, leg_bot)], 20), 7, tone=0.8,
             seed=s + 6, taper=(0.05, 0.7), head=0.4, dry=0.85, dry_from=0.3, streak=0.35, fade=0.5)
    pen.line(D([(cx + 16, cy + ry), (cx + 15, cy + ry + 70), (cx + 15, leg_bot - 40)], 20), 4, tone=0.55,
             seed=s + 7, taper=(0.05, 0.7), head=0.1, dry=0.8, dry_from=0.3)
    topp = ell(cx, cy, rx, ry, 0, 360, 80)
    edge = np.vstack([ell(cx, cy, rx, ry, 0, 180, 40), ell(cx, cy + th, rx, ry, 180, 0, 40)])
    pen.cover([topp, edge], seed=s + 8, feather=0.8)
    pen.fill(edge, 'wood_d', seed=s + 11)
    if mem:
        pen.fill(topp, 'wood', seed=s + 9, grad=(cx - rx, 0, cx + rx, 0, 0.75, 1.0), streak=0.4)
    else:
        pen.fill(topp, 'wood', seed=s + 9, grad=(cx - rx, 0, cx + rx, 0, 0.8, 1.0),
                 tone=0.34 if night else None)
    pen.hatch(topp, angle=3, spacing=8, tone=0.16, color='wood_d', seed=s + 10, partial=0.45, bow=0.03)
    if light:
        pen.light(cx - 0.18 * rx, cy - 0.06 * ry, 0.42 * rx, 0.42 * ry, amt=0.5, color='lamp', seed=s + 15)
    pen.line(ell(cx, cy, rx, ry, -10, 190, 48), 11, tone=0.92, color='wood_d', seed=s + 12, taper=(0.04, 0.12),
             head=0.7, lift=0.35, dry=0.5, dry_from=0.8, streak=0.3, pool=0.2)
    pen.line(ell(cx, cy, rx, ry, 195, 345, 36), 4.5, tone=0.6, color='wood_d', seed=s + 13, taper=(0.1, 0.4),
             head=0.2, dry=0.75, dry_from=0.3, streak=0.3)
    pen.line(ell(cx, cy + th, rx, ry, 12, 168, 36), 6, tone=0.78, color='wood_d', seed=s + 14, taper=(0.1, 0.3),
             head=0.4, dry=0.5, dry_from=0.6)


def chair_back(pen, x0=CHAIR[0], x1=CHAIR[1], top=CHAIR[2], bot=None, seed=1250, tb=TABLE):
    """他那把椅子：椅背从桌子后沿露出来（两根立柱 + 弯弯的顶档 + 两根细竖档）。"""
    s = seed
    if bot is None:
        bot = float(back_edge_y((x0 + x1) / 2, tb)) + 6
    rail = np.vstack([bez((x0 - 6, top + 8), ((x0 + x1) / 2, top - 6), (x1 + 6, top + 8), 14),
                      bez((x1 + 6, top + 30), ((x0 + x1) / 2, top + 16), (x0 - 6, top + 30), 14)])
    for i, x in enumerate((x0 + 10, x1 - 10)):
        post = P([[x - 6, top + 18], [x + 6, top + 18], [x + 6, bot], [x - 6, bot]])
        pen.cover(post, seed=s + 40 + i, feather=0.8)
        pen.fill(post, 'wood_d', seed=s + 42 + i)
        pen.line(D([(x - 6, top + 20), (x - 5, (top + bot) / 2), (x - 6, bot)], 16), 6, tone=0.8, seed=s + i,
                 taper=(0.1, 0.15), head=0.4, dry=0.4, dry_from=0.6)
        pen.line(D([(x + 6, top + 22), (x + 6, bot)], 16), 3, tone=0.5, seed=s + 4 + i, taper=(0.1, 0.3))
    for i, x in enumerate((x0 + 0.38 * (x1 - x0), x0 + 0.62 * (x1 - x0))):
        pen.line(D([(x, top + 28), (x + 1, top + 70), (x, bot)], 16), 4.5, tone=0.55, color='wood_d',
                 seed=s + 10 + i, taper=(0.1, 0.4), head=0.3, dry=0.6, dry_from=0.4)
    pen.cover(rail, seed=s + 20, feather=0.8)
    pen.fill(rail, 'wood', seed=s + 21, grad=(x0, 0, x1, 0, 1.0, 0.7))
    pen.shade(np.vstack([bez((x0, top + 22), ((x0 + x1) / 2, top + 9), (x1, top + 22), 10),
                         bez((x1 + 6, top + 30), ((x0 + x1) / 2, top + 16), (x0 - 6, top + 30), 10)]), amount=0.3,
              seed=s + 22)
    pen.line(bez((x0 - 8, top + 9), ((x0 + x1) / 2, top - 7), (x1 + 8, top + 9), 14), 9, tone=0.9, color='wood_d',
             seed=s + 23, taper=(0.1, 0.15), head=0.6, lift=0.3, dry=0.4, dry_from=0.7, streak=0.3)
    pen.line(bez((x0 - 4, top + 30), ((x0 + x1) / 2, top + 17), (x1 + 4, top + 30), 14), 4, tone=0.6,
             color='wood_d', seed=s + 24, taper=(0.1, 0.3), head=0.2, dry=0.5, dry_from=0.5)


def calendar(pen, x0=1520, y0=300, w=112, h=150, seed=1000, crossed=0, mem=False):
    """挂历（kitchen.py 同一画法）：十二月，红圈圈着的那一天；crossed 划掉的天数（第 11 镜的伏笔，这里 0）。"""
    s = seed
    x1, y1 = x0 + w, y0 + h
    pen.dot((x0 + x1) / 2, y0 - 22, 3.5, 3.5, color='ink', tone=0.9, seed=s)
    pen.line([(x0 + 18, y0 + 2), ((x0 + x1) / 2, y0 - 22), (x1 - 18, y0 + 2)], 2.2, tone=0.6, seed=s + 1,
             taper=(0.1, 0.1), head=0)
    page = P([[x0, y0], [x1, y0 + 2], [x1 + 1, y1], [x0 - 1, y1 - 1]])
    pen.cover(page, seed=s + 12, feather=0.8)
    pen.fill(page, 'cloth', seed=s + 2)
    pen.shade(P([[x0 + 70, y0 + 13], [x1, y0 + 14], [x1 + 1, y1], [x0 + 80, y1]]), amount=0.08, seed=s + 13)
    pen.line(D([(x0, y0), (x0 - 1, y1)], 20), 4, tone=0.75, seed=s + 3, taper=(0.05, 0.3), head=0.4)
    pen.line(D([(x1, y0 + 2), (x1 + 1, y1)], 20), 2.6, tone=0.5, seed=s + 5, taper=(0.05, 0.5), head=0,
             dry=0.6, dry_from=0.4)
    pen.line(D([(x0 - 1, y1), (x1 + 1, y1)], 20), 3.4, tone=0.62, seed=s + 6, taper=(0.1, 0.3), head=0.3,
             dry=0.4, dry_from=0.6)
    hdr = P([[x0 - 1, y0 - 1], [x1 + 1, y0 + 1], [x1, y0 + 13], [x0, y0 + 11]])
    pen.fill(hdr, 'lampshade', seed=s + 7, tone=0.78)
    for k_, (a, b) in enumerate((((30, 31), (50, 29)), ((40, 22), (40, 43)), ((60, 26), (74, 25)),
                                 ((57, 39), (79, 37)))):
        pen.line([(x0 + a[0], y0 + a[1]), (x0 + b[0], y0 + b[1])], 4, tone=0.85, seed=s + 8 + k_,
                 taper=(0.2, 0.35), head=0.5, role='detail')
    gx0, gy0 = x0 + 12, y0 + 58
    for r_ in range(5):
        for c in range(7):
            xx, yy = gx0 + c * 13.5, gy0 + r_ * 18
            k_ = r_ * 7 + c
            pen.line([(xx - 2.5, yy), (xx + 2.5, yy + 0.5)], 2.2, tone=0.42 + 0.25 * (c >= 5), seed=(s, 20 + k_),
                     taper=(0.2, 0.3), head=0.2, role='detail', boil=0.15)
    cx, cy = gx0 + 4 * 13.5, gy0 + 3 * 18
    loop = [(cx + 9, cy - 5), (cx + 2, cy - 9), (cx - 8, cy - 6), (cx - 10, cy + 3), (cx - 3, cy + 9),
            (cx + 8, cy + 7), (cx + 11, cy - 1), (cx + 6, cy - 9), (cx - 1, cy - 11)]
    pen.line(loop, 3.4, tone=1.0, color='mark', seed=s + 60, taper=(0.15, 0.4), head=0.4, dry=0.35, dry_from=0.7,
             role='detail', boil=0.25)


def shelf_mugs(pen, x0=1660, y=330, w=250, seed=300, mugs=2):
    """搁板 + 两只马克杯：她的（米白）和他的（青绿）——第 13 镜他那只会被收进纸箱。"""
    s = seed
    x1 = x0 + w
    board = P([[x0, y - 4], [x1, y - 4], [x1, y + 4], [x0, y + 4]])
    pen.fill(board, 'wood', seed=s + 1)
    pen.line(D([(x0, y), ((x0 + x1) / 2, y - 4), (x1, y + 1)], 24), 12, tone=0.88, color='wood_d', seed=s,
             taper=(0.04, 0.25), head=0.6, lift=0.25, dry=0.55, dry_from=0.6, streak=0.25, pool=0.2)
    pen.shade(P([[x0 + 8, y + 4], [x1 - 8, y + 4], [x1 - 14, y + 40], [x0 + 16, y + 36]]), amount=0.18, seed=s + 4,
              grad=(0, y + 4, 0, y + 40, 1.0, 0.0))
    pen.line([(x0 + 28, y + 5), (x0 + 32, y + 43), (x0 + 62, y + 6)], 4, tone=0.55, color='wood_d', seed=s + 2,
             taper=(0.1, 0.3), head=0.2, dry=0.4, dry_from=0.5)
    pen.line([(x1 - 34, y + 5), (x1 - 38, y + 43), (x1 - 64, y + 6)], 4, tone=0.55, color='wood_d', seed=s + 3,
             taper=(0.1, 0.3), head=0.2, dry=0.4, dry_from=0.5)
    for i, (dx, h, col) in enumerate([(52, 54, 'enamel'), (134, 49, 'cabinet')][:mugs]):
        bx0, bx1, tp, bt = x0 + dx, x0 + dx + 48, y - 2 - h, y - 3
        body = P([[bx0, tp + 4], [bx1, tp + 3], [bx1 - 1, bt], [bx0 + 1, bt]])
        pen.cover(body, seed=s + 9 + i, feather=0.8)
        pen.fill(body, col, seed=s + 10 + i)
        pen.shade(P([[bx0 + 30, tp + 4], [bx1, tp + 3], [bx1 - 1, bt], [bx0 + 30, bt]]), amount=0.3, seed=s + 18 + i)
        pen.line(ell(bx0 + 24, tp + 4, 24, 5, 190, 520, 14), 3.0, tone=0.75, seed=s + 12 + i, taper=(0.1, 0.4),
                 head=0.2)
        pen.line(D([(bx0, tp + 5), (bx0 - 1, (tp + bt) / 2), (bx0 + 1, bt)], 12), 5, tone=0.88, seed=s + 14 + i,
                 taper=(0.1, 0.25), head=0.5, lift=0.2)
        pen.line([(bx1, tp + 5), (bx1 + 1, (tp + bt) / 2), (bx1 - 1, bt)], 3, tone=0.6, seed=s + 16 + i,
                 taper=(0.1, 0.4), head=0.2, dry=0.5, dry_from=0.5)
        hx = bx1 if i == 0 else bx0
        sg = 1 if i == 0 else -1
        pen.line([(hx, tp + 14), (hx + 18 * sg, tp + 17), (hx + 17 * sg, tp + 34), (hx, tp + 38)], 5.5,
                 tone=0.82, seed=s + 20 + i, taper=(0.2, 0.35), head=0.4, dry=0.3, dry_from=0.7)


def pot(pen, c=POT_C, rx=POT_RX, seed=800, swirl=0.0):
    """搪瓷小锅（kitchen.py 的深灰小锅）：c = 锅口中心；汤面 + 红豆；锅柄朝左后。"""
    s = seed
    cx, rim_y = c
    ry_ = rx * 0.24
    bot = rim_y + rx * 0.80
    body = np.vstack([P([[cx + rx, rim_y]]), P([[cx + rx - 5, bot - 6]]), ell(cx, bot - 6, rx - 5, 8, 0, 180, 16),
                      P([[cx - rx, rim_y]]), ell(cx, rim_y, rx, ry_, 180, 0, 20)])
    pen.shade(ell(cx + 12, bot, rx * 0.95, 9, n=30), amount=0.4, seed=s + 26, soft=5.0)
    pen.cover(body, seed=s + 31, feather=0.8)
    pen.fill(body, '#45474F', seed=s + 20, grad=(cx - rx, 0, cx + rx, 0, 0.85, 1.0))
    pen.shade(np.vstack([P([[cx + 10, rim_y + 4]]), P([[cx + rx, rim_y]]), P([[cx + rx - 5, bot - 6]]),
                         ell(cx, bot - 6, rx - 5, 8, 0, 80, 8)]), amount=0.35, seed=s + 27)
    pen.lift(tube([(cx - 0.66 * rx, rim_y + 18), (cx - 0.65 * rx, (rim_y + bot) / 2), (cx - 0.62 * rx, bot - 9)],
                  [3, 7, 3])[0], amt=0.5, seed=s + 21, soft=1.5, dry=0.7, streak=0.5)
    inner = ell(cx, rim_y + 1.5, rx - 6, ry_ - 3, n=44)
    pen.fill(inner, 'soup', seed=s + 1)
    pen.shade(ell(cx, rim_y - 2, rx * 0.86, ry_ * 0.5, 180, 360, 16), amount=0.3, seed=s + 2, color='bean_d')
    for k, (rr, a0, ln) in enumerate([(0.72, 0, 80), (0.45, 140, 70)]):
        a = math.degrees(swirl) * (1.0 - 0.2 * k) + a0
        pts = ell(cx, rim_y + 2, (rx - 8) * rr, (ry_ - 3) * rr, a, a + ln, 8)
        pen.lift(tube(pts, [0.5, 1.4, 0.5])[0], amt=0.35, seed=s + 3 + k, soft=0.8)
    r = rng(s, 'beans')
    for i in range(14):
        rr = math.sqrt(r.uniform(0.04, 0.85))
        a = r.uniform(0, 2 * math.pi) + swirl * 0.5
        bx, by = cx + (rx - 10) * rr * math.cos(a), rim_y + 2 + (ry_ - 4) * rr * math.sin(a)
        pen.dot(bx, by, 4.0, 2.7, color='bean', tone=1.0, seed=(s, 30 + i), rot=math.degrees(a) * 0.3)
        pen.dot(bx + 0.6, by + 0.6, 3.0, 1.9, color='bean_d', tone=1.0, seed=(s, 60 + i))
    pen.line(ell(cx, rim_y, rx, ry_, 0, 180, 20), 6.5, tone=0.95, seed=s + 22, taper=(0.1, 0.15), head=0.5)
    pen.line(ell(cx, rim_y, rx, ry_, 180, 360, 20), 3.5, tone=0.8, seed=s + 23, taper=(0.1, 0.15), head=0.2)
    pen.line([(cx - rx, rim_y + 2), (cx - rx + 3, (rim_y + bot) / 2), (cx - rx + 6, bot - 4)], 6, tone=0.88,
             seed=s + 24, taper=(0.1, 0.2), head=0.4)
    pen.line([(cx + rx, rim_y + 2), (cx + rx - 2, (rim_y + bot) / 2), (cx + rx - 5, bot - 4)], 3.5, tone=0.6,
             seed=s + 28, taper=(0.1, 0.3), head=0.2)
    pen.line(ell(cx, bot - 6, rx - 5, 8, 10, 170, 14), 5, tone=0.8, seed=s + 29, taper=(0.1, 0.2), head=0.3)
    # 锅柄（朝左后）
    pen.line([(cx - rx + 4, rim_y + 5), (cx - rx - 40, rim_y - 4), (cx - rx - 84, rim_y - 16)], 13, tone=0.9,
             color='wood_d', seed=s + 25, taper=(0.05, 0.15), head=0.6, lift=0.25, dry=0.4, dry_from=0.75,
             streak=0.25)


class _Rig:
    def __init__(self, S, f=1):
        self.S, self.f = S, f


def ladle_rest(pen, tip, hand, S=S_G, f=1, seed=1070):
    """松开手的长柄木汤勺：和她手里拿着时同一画法、同一位置（勺斗在锅里，长柄斜靠在锅沿上）。"""
    with pen.group('ladle_rest', boil=0.6):
        ch._tool_ladle(ch._Ink(pen, S), _Rig(S, f), np.float32(hand), np.float32(tip), 0.0, None, seed)


def small_bowl(pen, c, r, fill=1.0, seed=1300, k=0.30, beans=12, shadow=(0.22, 0.32), band=True):
    """白瓷碗（和 table_cu 的大碗同一画法：碗口青花线、圈足、釉面高光），盛着 fill 0..1 的红豆汤。c = 碗口中心。"""
    s = seed
    cx, cy = float(c[0]), float(c[1])
    ry = r * k
    side_l = bez((cx - r, cy), (cx - r * 0.97, cy + 0.62 * r), (cx - r * 0.44, cy + 0.68 * r), 12)
    side_r = bez((cx + r * 0.44, cy + 0.68 * r), (cx + r * 0.97, cy + 0.62 * r), (cx + r, cy), 12)
    foot = P([(cx - 0.40 * r, cy + 0.67 * r), (cx - 0.37 * r, cy + 0.77 * r), (cx + 0.37 * r, cy + 0.77 * r),
              (cx + 0.40 * r, cy + 0.67 * r)])
    body = np.vstack([ell(cx, cy, r, ry, 180, 360, 28), side_r[::-1], foot[::-1], side_l[::-1]])
    with pen.group('bowl', boil=0.5):
        if shadow:
            pen.shade(ell(cx + shadow[0] * r, cy + 0.74 * r, 0.80 * r, 0.12 * r, n=36), amount=shadow[1],
                      seed=s + 1, soft=max(3.0, 0.05 * r))
        pen.cover(body, seed=s + 2, feather=0.8)
        pen.fill(body, 'enamel', seed=s + 3)
        pen.shade(np.vstack([side_r[::-1], P([[cx + 0.30 * r, cy + 0.66 * r], [cx + 0.55 * r, cy + 0.2 * r],
                                              [cx + 0.6 * r, cy + 0.9 * ry]])]), amount=0.34, seed=s + 4, angle=70)
        if band:
            bd = np.vstack([ell(cx, cy + 0.10 * r, r * 0.985, ry * 1.02, 2, 178, 24),
                            ell(cx, cy + 0.14 * r, r * 0.975, ry * 1.02, 178, 2, 24)])
            pen.fill(bd, 'night_l', seed=s + 6, a_dens=1.2)
        pen.fill(ell(cx, cy + 0.6, r - 0.03 * r - 1.5, ry - 0.022 * r - 1.0, 0, 360, 48), 'enamel', seed=s + 7)
        pen.shade(np.vstack([ell(cx, cy, r * 0.96, ry * 0.9, 185, 300, 14),
                             ell(cx - 0.05 * r, cy + 0.02 * ry, 0.8 * r, 0.55 * ry, 300, 185, 14)]), amount=0.22,
                  seed=s + 8, angle=10)
        fl = float(clamp(fill))
        if fl > 0.02:
            sk = 0.62 + 0.26 * fl                       # 汤越满，汤面越大、越靠近碗口
            dy = 0.10 * r + 0.16 * r * (1 - fl)
            soup = ell(cx, cy + dy, r * sk, ry * sk, 0, 360, 44)
            pen.fill(soup, 'soup', seed=s + 10)
            pen.shade(np.vstack([ell(cx, cy + dy, r * sk, ry * sk, 180, 360, 20),
                                 ell(cx, cy + dy + 0.25 * ry * sk, r * sk * 0.9, ry * sk * 0.4, 360, 180, 20)]),
                      amount=0.35, seed=s + 11, color='bean_d')
            pen.lift(ell(cx - 0.38 * r * sk, cy + dy - 0.30 * ry * sk, 0.22 * r * sk, 0.10 * ry * sk + 0.5, n=20),
                     amt=0.45, seed=s + 12, soft=max(1.0, 0.025 * r))
            rb = rng(s, 'beans')
            nb = int(round(beans * min(1.0, 0.3 + fl)))
            pts = []
            for _ in range(200):
                if len(pts) >= nb:
                    break
                a = rb.uniform(0, 2 * math.pi)
                rr = math.sqrt(rb.uniform(0.0, 0.78))
                x, y = cx + r * sk * rr * math.cos(a), cy + dy + ry * sk * rr * math.sin(a)
                if any((x - q[0]) ** 2 + ((y - q[1]) / 0.55) ** 2 < (0.11 * r) ** 2 for q in pts):
                    continue
                pts.append((x, y))
            bs = 0.052 * r
            for j, (x, y) in enumerate(pts):
                rot = float(rb.uniform(-35, 35))
                pen.dot(x, y, bs, bs * 0.62, color='bean', tone=1.0, seed=(s, 30 + j), rot=rot)
                pen.dot(x + 0.12 * bs, y + 0.15 * bs, bs * 0.78, bs * 0.45, color='bean_d', tone=0.7,
                        seed=(s, 60 + j), rot=rot, shine=False)
        w0 = max(2.0, 0.031 * r)
        pen.line(ell(cx, cy, r, ry, 0, 180, 28), w0 * 1.6, tone=0.88, seed=s + 20, taper=(0.06, 0.06), head=0.3,
                 lift=0.2)
        pen.line(ell(cx, cy, r, ry, 180, 360, 28), w0 * 1.1, tone=0.66, seed=s + 21, taper=(0.1, 0.1), head=0.2,
                 dry=0.4, dry_from=0.6)
        pen.line(side_l, w0 * 2.0, tone=0.88, seed=s + 23, taper=(0.06, 0.25), head=0.5, lift=0.2)
        pen.line(side_r, w0 * 1.4, tone=0.72, seed=s + 24, taper=(0.15, 0.2), head=0.3, dry=0.4, dry_from=0.55)
        pen.line(P([(cx - 0.38 * r, cy + 0.68 * r), (cx - 0.36 * r, cy + 0.77 * r), (cx, cy + 0.785 * r),
                    (cx + 0.36 * r, cy + 0.77 * r), (cx + 0.38 * r, cy + 0.68 * r)]), w0 * 1.4, tone=0.8,
                 seed=s + 25, taper=(0.1, 0.2), head=0.3)
        pen.lift(tube([(cx - 0.78 * r, cy + 0.20 * r), (cx - 0.70 * r, cy + 0.38 * r), (cx - 0.55 * r, cy + 0.52 * r)],
                      [0.025 * r, 0.056 * r, 0.02 * r])[0], amt=0.7, seed=s + 27, soft=1.5)


def table_spoon(pen, c, ang=SPOON_ANG0, L=1.0, seed=1500, shadow=True):
    """桌上的金属汤勺（table_cu 同一把）：c 勺头中心；ang 勺头 → 勺柄的方向（度）；L 尺寸系数（1 ≈ 勺长 120px）。"""
    s = seed
    c = np.float32(c)
    a = math.radians(ang)
    dv = np.float32([math.cos(a), math.sin(a)])
    with pen.group('spoon', boil=0.5):
        if shadow:
            pen.shade(ell(c[0] + dv[0] * 40 * L, c[1] + 8 * L, 70 * L, 6 * L, n=24, rot=math.degrees(a) * 0.15),
                      amount=0.2, seed=s, soft=3.0)
        sp = ell(c[0], c[1], 21 * L, 9.5 * L, 0, 360, 22, rot=ang)
        handle, Lh, Rh = tube([c + dv * 18 * L, c + dv * 62 * L, c + dv * 104 * L], [6 * L, 5 * L, 7 * L])
        pen.cover([sp, handle], seed=s + 1, feather=0.7)
        pen.fill([sp, handle], 'metal', seed=s + 2)
        pen.shade(ell(c[0] + 3 * L, c[1] + 1.5 * L, 15 * L, 6 * L, 0, 360, 16, rot=ang), amount=0.3, seed=s + 3)
        pen.line(sp, 2.6 * L ** 0.7, tone=0.8, seed=s + 4, closed=True, taper=(0, 0))
        pen.line(Lh[::5], 2.3 * L ** 0.7, tone=0.75, seed=s + 5, taper=(0.1, 0.2))
        pen.line(Rh[::5], 1.9 * L ** 0.7, tone=0.6, seed=s + 6, taper=(0.1, 0.2))
        pen.lift(ell(c[0] - 6 * L, c[1] - 3 * L, 6.5 * L, 2.2 * L, n=10, rot=ang), amt=0.7, seed=s + 7, soft=0.8)


def steam(pen, t, c, w=40.0, h=150.0, seed=1700, amt=1.0, n=3, per=3.0, mem=False, tone=0.14):
    """热气：从 c（汤面中心）升起的几缕。水墨里 = 提白 + 极淡的一笔；水彩里同样（提亮的淡痕）。"""
    cx, cy = float(c[0]), float(c[1])
    if amt <= 0.02:
        return
    with pen.group('steam', boil=0.8):
        for k in range(n):
            age = ((t + k * per / n) % per) / per
            a = math.sin(math.pi * age) ** 1.4 * amt
            if a < 0.04:
                continue
            cyc = math.floor((t + k * per / n) / per)
            r = rng(seed, k, cyc)
            bx = cx + r.uniform(-w, w)
            yb = cy - 6 - age * h * 0.75
            L = h * (0.4 + 0.45 * age)
            ys = np.linspace(yb, yb - L, 7)
            ph = r.uniform(0, 6.28)
            curl = r.uniform(0.18, 0.36) * w * (0.5 + age)
            xs = bx + curl * np.sin((ys - cy) * 0.035 + ph + t * 1.0) + (cy - ys) * 0.05
            path = np.stack([xs, ys], 1).astype(np.float32)
            ww = (0.12 + 0.20 * age) * w
            pen.lift(tube(path, [ww * 0.4, ww, ww * 0.7, ww * 0.3])[0], amt=0.55 * a, seed=(seed + 10, k, cyc),
                     soft=0.12 * w)
            pen.line(path, ww * 0.45, tone=tone * a, color='metal', seed=(seed + 20, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.55, dry_from=0.1)


# ================================================================= 她的手臂（盛汤 → 放回汤勺 → 推碗 → 摆勺子）
def _ladle(bw, u, R, r=BOWL_R):
    return ch.ARM_POSES['ladle'](0.0, dict(pot=(POT_C[0], POT_C[1] + 4), bowl=bw, r=r, u=u), R)


NEAR_REST = dict(hand=np.float32([742, 662]), shape='flat', thumb=-1, bend=1.0)


def _as_far(sp):
    """把 arm_push / arm_place 给近侧手的描述改给远侧手（她的左手，在身体前面）。"""
    o = dict(sp)
    o['front'] = True
    o['thumb'] = 1
    o['bend'] = -1.0
    return o


def _push(u, R):
    return _as_far(ch.ARM_POSES['push'](0.0, dict(bowl=BOWL_B0, to=BOWL_B1, r=BOWL_R, u=u), R)['near'])


def _place(u, R):
    return _as_far(ch.ARM_POSES['place'](0.0, dict(spoon=SPOON0, to=SPOON1, u=u, lift=0.14), R)['near'])


def _mix(a, b, w):
    """两个手臂描述之间过渡（手的位置线性插值；道具/手形在中点切换）。"""
    if a is None or b is None:
        return b if w >= 0.5 else a
    w = float(smooth01(w))
    o = dict(b if w >= 0.5 else a)
    o['hand'] = lerp(np.float32(a['hand']), np.float32(b['hand']), w)
    ta, tb = a.get('tool'), b.get('tool')
    if ta and tb and ta[0] == tb[0] == 'ladle':
        o['tool'] = ('ladle', lerp(ta[1], tb[1], w), ta[2] * (1 - w) + tb[2] * w, tb[3])
    return o


def arm_specs(t, R):
    """近侧手（右手）握汤勺盛两碗，然后把汤勺搁回锅里一直握着；远侧手（左手）扶碗 → 推碗 → 摆勺子。
    → (specs dict(near, far), 状态 dict(push_u, spoon_held, spoon_u))。"""
    st = dict(push_u=0.0, spoon_u=0.0, spoon_held=False, ladle_held=True)
    rest_ladle = _ladle(BOWL_B0, 0.06, R)['near']
    st['ladle_tip'], st['ladle_hand'] = rest_ladle['tool'][1], rest_ladle['hand']
    if t >= T_BACK:
        # 松开汤勺：右手落到锅左边的桌沿上
        st['ladle_held'] = False
        w = clamp((t - T_BACK) / 0.22)
        rest_ladle = _mix(dict(rest_ladle, tool=None, shape='fist'), dict(NEAR_REST), w)
    if t < T_L1E:
        sp = _ladle(BOWL_A, clamp((t - T_L1) / (T_L1E - T_L1)), R)
    elif t < T_L2:
        w = (t - T_L1E) / (T_L2 - T_L1E)
        a, b = _ladle(BOWL_A, 1.0, R), _ladle(BOWL_B0, 0.0, R)
        sp = dict(near=_mix(a['near'], b['near'], w), far=_mix(a['far'], b['far'], w))
    elif t < T_L2E:
        sp = _ladle(BOWL_B0, (t - T_L2) / (T_L2E - T_L2), R)
    elif t < T_BACK:
        w = (t - T_L2E) / (T_BACK - T_L2E)
        a = _ladle(BOWL_B0, 1.0, R)
        sp = dict(near=_mix(a['near'], rest_ladle, w), far=a['far'])
    elif t < T_P0:
        w = (t - T_BACK) / (T_P0 - T_BACK)
        sp = dict(near=rest_ladle, far=_mix(_ladle(BOWL_B0, 1.0, R)['far'], _push(0.0, R), w))
    elif t < T_P1 + 0.03:
        u = clamp((t - T_P0) / (T_P1 - T_P0))
        st['push_u'] = u
        sp = dict(near=rest_ladle, far=_push(u, R))
    elif t < T_S0:
        st['push_u'] = 1.0
        w = (t - (T_P1 + 0.03)) / (T_S0 - T_P1 - 0.03)
        b = _place(0.0, R)
        if w >= 0.5:
            st['spoon_held'] = True
        sp = dict(near=rest_ladle, far=_mix(_push(1.0, R), b if w >= 0.5 else dict(b, tool=None), w))
    else:
        st['push_u'] = 1.0
        st['spoon_held'] = True
        u = clamp((t - T_S0) / (T_S1 - T_S0))
        st['spoon_u'] = u
        fb = _place(u, R)
        if t > T_S1 + 0.08:
            # 摆好了：手指离开勺子，往回收一点
            w = clamp((t - T_S1 - 0.08) / 0.28)
            st['spoon_held'] = False
            free = dict(fb, tool=None, shape='flat')
            fb = _mix(free, dict(free, hand=np.float32(fb['hand']) + np.float32([-30, -14])), w)
        sp = dict(near=rest_ladle, far=fb)
    return sp, st


def _arm_pose(t, args, rig=None):
    return arm_specs(args['t'], rig)[0]


ch.ARM_POSES['_table3'] = _arm_pose      # 只在本场景里用的私有姿态名（运行时注册，不改 characters.py）


# ================================================================= 她的表演
def _blink(t, tb, dur=0.26):
    x = (t - tb) / dur
    if x <= 0 or x >= 1:
        return 0.0
    return float(smooth01(x / 0.35)) if x < 0.35 else float(1.0 - smooth01((x - 0.35) / 0.65))


def girl_pose(t):
    look = dict(ch.EXPR['neutral'], open=0.38, gy=0.95, gx=0.30, smile=-0.02, brow=0.16, blush=0.35)
    look_b = dict(ch.EXPR['neutral'], open=0.50, gy=0.72, gx=0.55, smile=0.08, brow=0.22, blush=0.45)
    wist = dict(ch.EXPR['wistful_smile'], gy=0.50, gx=0.55, open=0.48, smile=0.56, happy=0.55)
    face = ch.mix_expr(look, look_b, ease_io((t - (T_P0 - 0.1)) / 0.35))
    face = ch.mix_expr(face, wist, ease_io((t - T_SMILE) / 0.45))
    # 笑意慢慢浮上来，到 11.75 再淡一点（想起来对面是空的）
    face['smile'] = face['smile'] - 0.10 * ease_io((t - 11.78) / 0.2)
    blink = max(_blink(t, 9.66), _blink(t, 10.92, 0.22))
    lean = 0.20 + 0.05 * math.sin(math.pi * clamp((t - T_L1) / (T_L1E - T_L1))) \
        + 0.20 * ease_io((t - T_P0) / (T_P1 - T_P0)) - 0.06 * ease_io((t - T_S1) / 0.3)
    yaw = 34 + 6 * ease_io((t - T_P0) / 0.5) + 6 * ease_io((t - T_SMILE) / 0.5)
    pitch = 25 - 3 * ease_io((t - T_P0) / 0.5) - 7 * ease_io((t - T_SMILE) / 0.5)
    roll = 3 + 5 * ease_io((t - T_SMILE) / 0.6)
    x = GIRL_X
    y = float(back_edge_y(x)) - 1.45 * S_G
    return dict(x=x, y=y, s=S_G, facing=1, yaw=yaw, pitch=pitch, roll=roll, lean=lean, face=face, blink=blink,
                breath=(t - T0) / 3.3 + 0.1, clip_poly=behind_table_poly(), clip_arms=False, seed=1000, boil=1.0,
                arm='_table3', arm_args=dict(t=t))


# ================================================================= 场景
def background(pen):
    wall(pen, (LAMP[0], LAMP[1] + 330))
    # 地脚线（很淡）
    pen.line(D([(-20, 884), (700, 880), (1940, 886)], 40), 4, tone=0.30, color='wood_d', seed=720,
             taper=(0.05, 0.3), dry=0.8, dry_from=0.2, streak=0.3, fade=0.4)
    window(pen)
    calendar(pen, 1420, 300)
    shelf_mugs(pen, 1556, 372, w=220)
    chair_back(pen)
    round_table(pen)
    lamp(pen)


def draw(pen, t=None, mode='serve', **kw):
    t = float(pen.t if t is None else t)
    z = VIEW_Z
    with pen.view(z, W / 2 - z * VIEW_C[0], H / 2 - z * VIEW_C[1]):
        _draw(pen, t)


def _draw(pen, t):
    with pen.group('bg', boil=0.4, cache=('table3', pen.d % 3)):
        background(pen)
    snow(pen, t)
    gp = girl_pose(t)
    R = ch._GirlRig(gp)
    _, st = arm_specs(t, R)
    fa = clamp((t - (T_L1 + 0.55 * (T_L1E - T_L1))) / (0.32 * (T_L1E - T_L1)))
    fb = clamp((t - (T_L2 + 0.55 * (T_L2E - T_L2))) / (0.32 * (T_L2E - T_L2)))
    bpos = lerp(np.float32(BOWL_B0), np.float32(BOWL_B1), float(smooth01(st['push_u'])))

    def props(pen):
        pot(pen, swirl=0.6 * t)
        if not st['ladle_held']:
            ladle_rest(pen, st['ladle_tip'], st['ladle_hand'])
        if not st['spoon_held']:
            if st['spoon_u'] >= 1.0:
                table_spoon(pen, SPOON1, ang=SPOON_ANG0, L=0.92)
            else:
                table_spoon(pen, SPOON0, ang=SPOON_ANG0, L=0.92)
        small_bowl(pen, BOWL_A, BOWL_R, fill=fa, seed=1310)
        small_bowl(pen, bpos, BOWL_R, fill=fb, seed=1340)

    ch.girl_with(pen, gp, props)
    # 热气：锅一直冒；碗盛上汤以后冒
    steam(pen, t, (POT_C[0], POT_C[1] - 2), w=44, h=210, seed=1700, amt=0.9, n=4, per=2.8, tone=0.24)
    steam(pen, t, BOWL_A, w=22, h=120, seed=1730, amt=0.8 * fa, n=2, per=2.6, tone=0.26)
    steam(pen, t, bpos, w=22, h=130, seed=1760, amt=0.9 * fb, n=3, per=2.4, tone=0.26)
