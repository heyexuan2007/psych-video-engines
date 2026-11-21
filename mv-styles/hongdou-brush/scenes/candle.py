# -*- coding: utf-8 -*-
"""
第 14 镜「第十二句示例歌词用」（成片 49.49–53.76，C 水墨；红色只给那两碗红豆汤）。
深夜的桌面特写：左边一根蜡烛立在搪瓷烛台上，右边是那两只盛着红豆汤的碗（她的、他的），汤早凉了。
时间快进：
  49.49–52.57 蜡烛从长烧到只剩一小截（一路有烛泪从烛口淌下来、凝在烛身上，积在烛台里越积越多）；
              火苗在摇（留白 + 一圈淡墨的光晕），烛光把墙和桌面照成纸白；
              火苗越来越低，碗在桌上的影子越拉越长（时间在走）；碗上最后一点热气在开头散掉（汤凉了）。
  52.40 火苗开始挣扎、变小；52.57「不」熄灭（光没了，画面整体暗下来，只剩窗外照进来的一块月光）；
  52.70 起一缕墨色的烟从烛芯升起：根部一根细的浓墨，往上慢慢卷成优雅的曲线，越往上越宽、越淡、边缘洇开；
  53.30 起烟离开烛芯，顶上散开。烟正好飘过墙上那块月光（所以烟的墨色读得清楚）。
其他道具：窗（左上，雪在下）、墙上的月光窗影、火柴盒和一根烧过的火柴（左下）、碗里的勺子。
镜头固定（时间快进的镜头不动才读得出“快”）。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒，默认 pen.t）
"""
import math

import cv2
import numpy as np

from core import W, H, densify, ell, bez, spline, tube, rng, clamp, smooth01, ease_io, ease_out, ease_in

# ---------------------------------------------------------------- 时间（成片秒）
T0, T1 = 49.49, 53.76
T_WEAK = 52.38          # 火苗开始挣扎
T_OUT = 52.57           # 「不」：熄灭
T_SMOKE = 52.68         # 冒烟（「朽」52.77 时已经看得见一截）
T_DETACH = 53.32        # 烟离开烛芯、顶上散开

# ---------------------------------------------------------------- 布局
TABLE_Y = 560                      # 桌面后沿
CX = 720.0                         # 蜡烛中心 x
RXC = 31.0                         # 蜡烛半径
CUP_Y = 742.0                      # 烛台杯口
Y_LONG, Y_SHORT = 236.0, 716.0     # 烛顶：开始 / 熄灭时
SAUCER = (720.0, 786.0, 132.0, 30.0)
BOWLS = [dict(c=(1330.0, 690.0), r=150.0, seed=1300, spoon='rim'),
         dict(c=(1748.0, 640.0), r=132.0, seed=1400, spoon='rim2')]
BOWL_K = 0.30
WIN = (-40, -40, 300, 470)         # 左上角的窗
MOON = [(520, 96), (930, 128), (910, 520), (498, 472)]     # 墙上的月光窗影
BG_BOIL = 0.4


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


# ================================================================= 时间 → 蜡烛
def y_top(t):
    u = clamp((t - T0) / (T_OUT - T0))
    return Y_LONG + (Y_SHORT - Y_LONG) * u


def flame_k(t, d):
    """火苗大小（含逐张抖动）；熄灭后 0。"""
    if t >= T_OUT:
        return 0.0
    r = rng(5100, d)
    k = 1.0 + 0.07 * r.standard_normal()
    weak = smooth01((t - T_WEAK) / (T_OUT - T_WEAK))
    k *= 1.0 - 0.75 * weak + 0.25 * weak * r.uniform(-1, 1)
    return float(max(0.05, k))


def light_amt(t, d):
    out = 1.0 - float(smooth01((t - (T_OUT - 0.06)) / 0.14))
    fl = 1.0 + 0.035 * rng(5101, d).standard_normal()
    weak = float(smooth01((t - T_WEAK) / (T_OUT - T_WEAK)))
    return 0.58 * out * fl * (1.0 - 0.35 * weak)


def wick_pt(t):
    yt = y_top(t)
    return np.float32([CX + 3.0, yt - 15.0])


# ================================================================= 背景（缓存）
def wall(pen):
    s = 100
    q = P([(-40, -40), (W + 40, -40), (W + 40, TABLE_Y + 6), (-40, TABLE_Y + 6)])
    pen.fill(q, 'wall', seed=s, tone=0.40, c_fade=False, broad=False, rgrad=(760, 300, 200, 1400, 0.85, 1.25),
             var=0.14, cell=120.0)
    # 墙上的月光窗影（冷光 = 留白），窗棂的影子是两道没提白的条
    m = P(MOON)
    pen.lift(m, amt=0.50, seed=s + 1, soft=10.0)
    bar_v = P([(712, 110), (736, 112), (716, 500), (692, 497)])
    bar_h = P([(512, 280), (922, 318), (921, 340), (510, 302)])
    pen.fill([bar_v, bar_h], 'wall', seed=s + 2, tone=0.30, c_fade=False, broad=False, soft=4.0)
    # 墙脚线
    pen.line(D([(-40, TABLE_Y - 40), (W + 40, TABLE_Y - 44)], 40), 4, tone=0.35, seed=s + 3, role='detail',
             taper=(0.1, 0.1), dry=0.6, dry_from=0.3)


def window(pen):
    s = 200
    x0, y0, x1, y1 = WIN
    glass = P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    pen.cover(glass, seed=s)
    pen.fill(glass, 'night', seed=s + 1, grad=(0, 0, x1, y1, 1.0, 0.6), streak=0.4, sangle=88.0)
    roof = P([(-40, 360), (60, 338), (150, 330), (240, 346), (x1 + 10, 356)])
    pen.fill(np.vstack([roof, [[x1 + 10, y1], [-40, y1]]]), 'roof', seed=s + 2, grad=(0, 330, 0, y1, 1.0, 0.5))
    pen.line(roof, 9, tone=0.9, color='snow', seed=s + 3, taper=(0.1, 0.2), role='detail', dry=0.45, dry_from=0.3)
    # 月亮（留白）
    pen.dot(210, 90, 26, 26, color='snow', tone=0.0, seed=s + 4)
    pen.lift(ell(210, 90, 70, 70), amt=0.25, seed=s + 5, soft=20.0)
    pen.lift(ell(150, y1 - 10, 160, 34), amt=0.45, seed=s + 6, soft=12.0)
    pen.line(D([(x1 + 6, -20), (x1 + 3, 240), (x1 + 6, y1 + 8)], 30), 20, tone=0.92, color='wood_d', seed=s + 7,
             taper=(0.02, 0.1), head=0.4, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25, pool=0.2)
    pen.line(D([(124, -20), (122, 200), (125, y1 + 2)], 30), 9, tone=0.78, color='wood_d', seed=s + 8,
             taper=(0.02, 0.2), head=0.3, lift=0.3, dry=0.5, dry_from=0.6)
    pen.line(D([(-20, 218), (150, 216), (x1 + 4, 219)], 30), 8, tone=0.75, color='wood_d', seed=s + 9,
             taper=(0.05, 0.2), head=0.3, dry=0.55, dry_from=0.5)
    sill = P([[-40, y1], [x1 + 50, y1 + 2], [x1 + 54, y1 + 30], [-40, y1 + 28]])
    pen.cover(sill, seed=s + 10)
    pen.fill(sill, 'wood', seed=s + 11)
    pen.line(D([(-40, y1 + 2), (x1 + 58, y1 + 4)], 30), 15, tone=0.92, color='wood_d', seed=s + 12,
             taper=(0.02, 0.12), head=0.2, lift=0.25, dry=0.45, dry_from=0.72, pool=0.25)


def table(pen):
    s = 300
    top = P([(-40, TABLE_Y), (W + 40, TABLE_Y), (W + 40, H + 40), (-40, H + 40)])
    pen.cover(top, seed=s)
    pen.fill(top, 'wood', seed=s + 1, tone=0.36, c_fade=False, broad=False, streak=0.5, sangle=2.0,
             rgrad=(CX, 760, 200, 1300, 0.8, 1.2))
    r = rng(s, 'grain')
    for k in range(6):
        y = TABLE_Y + 40 + k * 82 + r.uniform(-12, 12)
        x0 = r.uniform(-20, 400) if k % 2 == 0 else r.uniform(900, 1300)
        x1 = x0 + r.uniform(500, 800)
        pen.line(D([(x0, y), ((x0 + x1) / 2, y + r.uniform(-4, 4)), (x1, y + r.uniform(-3, 3))], 40), 2.4,
                 tone=0.3, color='wood_d', seed=s + 10 + k, taper=(0.3, 0.4), role='detail', dry=0.7, dry_from=0.2,
                 streak=0.3)
    pen.line(D([(-40, TABLE_Y + 1), (800, TABLE_Y - 2), (1500, TABLE_Y + 1), (W + 40, TABLE_Y - 1)], 30), 14,
             tone=0.9, color='wood_d', seed=s + 2, taper=(0.02, 0.2), head=0.4, lift=0.3, dry=0.5, dry_from=0.7,
             streak=0.25, pool=0.2)
    pen.line(D([(-40, TABLE_Y + 16), (900, TABLE_Y + 14), (W + 40, TABLE_Y + 17)], 30), 4, tone=0.4,
             color='wood_d', seed=s + 3, taper=(0.05, 0.5), head=0.1, dry=0.75, dry_from=0.3, streak=0.2)
    # 窗下桌面上一小块月光
    pen.lift(P([(-40, 600), (300, 610), (420, 760), (-40, 760)]), amt=0.22, seed=s + 4, soft=24.0)


def matchbox(pen):
    """左下：一盒火柴，旁边一根烧过的火柴（黑头、焦黑的一段）。"""
    s = 400
    box_top = P([(250, 800), (420, 790), (452, 826), (282, 838)])
    box_side = P([(282, 838), (452, 826), (452, 852), (283, 866)])
    box_end = P([(250, 800), (282, 838), (283, 866), (251, 826)])
    pen.shade(P([(256, 836), (460, 822), (480, 868), (270, 884)]), amount=0.45, seed=s, soft=8.0, hatch=False)
    pen.cover([box_top, box_side, box_end], seed=s + 1, feather=0.7)
    pen.fill(box_top, 'cloth', seed=s + 2)
    pen.fill(box_side, 'wood_d', seed=s + 3, tone=0.6)
    pen.fill(box_end, 'wood_d', seed=s + 4, tone=0.45)
    pen.hatch(box_side, angle=-4, spacing=4.0, tone=0.5, seed=s + 5)        # 擦火的砂面
    for poly in (box_top, box_side, box_end):
        pen.line(np.vstack([poly, poly[:1]]), 3.0, tone=0.85, seed=(s, 6, len(poly)), taper=(0.05, 0.05),
                 role='detail')
    pen.line(P([(300, 806), (396, 800), (420, 826), (322, 832), (300, 806)]), 2.0, tone=0.45, seed=s + 7,
             role='detail', taper=(0, 0))
    # 烧过的火柴
    pen.line(P([(470, 848), (520, 842), (560, 836)]), 6.0, tone=0.35, color='wood', seed=s + 8, taper=(0.0, 0.0),
             role='detail')
    pen.line(P([(560, 836), (574, 832), (586, 826)]), 7.0, tone=0.95, seed=s + 9, taper=(0.0, 0.5), role='detail')
    pen.dot(589, 825, 5.5, 4.5, color='ink', tone=0.95, seed=s + 10)


def bowl_geom(b):
    cx, cy = b['c']
    r = b['r']
    ry = r * BOWL_K
    side_l = bez((cx - r, cy), (cx - r * 0.97, cy + 0.62 * r), (cx - r * 0.44, cy + 0.68 * r), 14)
    side_r = bez((cx + r * 0.44, cy + 0.68 * r), (cx + r * 0.97, cy + 0.62 * r), (cx + r, cy), 14)
    foot = P([(cx - 0.40 * r, cy + 0.67 * r), (cx - 0.37 * r, cy + 0.77 * r), (cx + 0.37 * r, cy + 0.77 * r),
              (cx + 0.40 * r, cy + 0.67 * r)])
    body = np.vstack([ell(cx, cy, r, ry, 180, 360, 32), side_r[::-1], foot[::-1], side_l[::-1]])
    return dict(cx=cx, cy=cy, r=r, ry=ry, side_l=side_l, side_r=side_r, foot=foot, body=body)


def bowl(pen, b):
    """一只盛着凉了的红豆汤的碗（和第 5 镜一样的画法：搪瓷、碗口下一道青线）。"""
    g = bowl_geom(b)
    cx, cy, r, ry = g['cx'], g['cy'], g['r'], g['ry']
    s = b['seed']
    pen.cover(g['body'], seed=s + 2, feather=0.8)
    pen.fill(g['body'], 'enamel', seed=s + 3)
    pen.shade(np.vstack([g['side_r'][::-1], P([[cx + 0.30 * r, cy + 0.66 * r], [cx + 0.55 * r, cy + 0.2 * r],
                                              [cx + 0.6 * r, cy + 0.9 * ry]])]), amount=0.34, seed=s + 4, angle=70)
    band = np.vstack([ell(cx, cy + 0.10 * r, r * 0.985, ry * 1.02, 2, 178, 30),
                      ell(cx, cy + 0.135 * r, r * 0.975, ry * 1.02, 178, 2, 30)])
    pen.fill(band, 'night_l', seed=s + 6)
    pen.fill(ell(cx, cy + 0.6, r - 5.0, ry - 3.5, 0, 360, 64), 'enamel', seed=s + 7)
    soup = ell(cx, cy + 0.10 * r, r * 0.86, ry * 0.86, 0, 360, 56)
    pen.fill(soup, 'soup', seed=s + 10)
    pen.shade(np.vstack([ell(cx, cy + 0.10 * r, r * 0.86, ry * 0.86, 180, 360, 24),
                         ell(cx, cy + 0.10 * r + 0.25 * ry, r * 0.78, ry * 0.35, 360, 180, 24)]),
              amount=0.35, seed=s + 11, color='bean_d')
    rr = rng(s, 'beans')
    for k in range(16):
        a = rr.uniform(0, 2 * math.pi)
        q = math.sqrt(rr.uniform(0.05, 0.8))
        bx, by = cx + 0.82 * r * q * math.cos(a), cy + 0.10 * r + 0.80 * ry * q * math.sin(a)
        pen.dot(bx, by, 7.0, 4.4, color='bean', tone=1.0, seed=(s, 20 + k), rot=rr.uniform(-30, 30))
    # 汤面凝了一层（凉了）：一道暗暗的皱
    pen.line(ell(cx - 0.1 * r, cy + 0.12 * r, r * 0.5, ry * 0.4, 200, 320, 12), 2.2, tone=0.5, color='bean_d',
             seed=s + 12, role='detail', taper=(0.3, 0.3))
    pen.line(ell(cx, cy, r, ry, 0, 180, 32), 5.0, tone=0.88, seed=s + 13, taper=(0.06, 0.06), head=0.3, lift=0.2)
    pen.line(ell(cx, cy, r, ry, 180, 360, 32), 3.4, tone=0.66, seed=s + 14, taper=(0.1, 0.1), head=0.2, dry=0.4,
             dry_from=0.6)
    pen.line(g['side_l'], 6.0, tone=0.88, seed=s + 15, taper=(0.06, 0.25), head=0.5, lift=0.2)
    pen.line(g['side_r'], 4.5, tone=0.72, seed=s + 16, taper=(0.15, 0.2), head=0.3, dry=0.4, dry_from=0.55)
    pen.line(P([(cx - 0.38 * r, cy + 0.68 * r), (cx - 0.36 * r, cy + 0.77 * r), (cx, cy + 0.785 * r),
                (cx + 0.36 * r, cy + 0.77 * r), (cx + 0.38 * r, cy + 0.68 * r)]), 4.5, tone=0.8, seed=s + 17,
             taper=(0.1, 0.2), head=0.3)
    pen.lift(tube([(cx - 0.78 * r, cy + 0.20 * r), (cx - 0.70 * r, cy + 0.38 * r), (cx - 0.55 * r, cy + 0.52 * r)],
                  [4, 9, 3])[0], amt=0.7, seed=s + 18, soft=2.0)
    # 勺子：斜靠在碗沿上，柄朝右上
    ang = -28.0 if b['spoon'] == 'rim' else -36.0
    dv = np.float32([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    head = np.float32([cx + 0.30 * r, cy + 0.08 * r])
    sp = ell(head[0], head[1], 0.17 * r, 0.075 * r, 0, 360, 20, rot=ang)
    hdl, Lh, Rh = tube([head + dv * 0.14 * r, head + dv * 0.55 * r, head + dv * 1.05 * r], [8, 7, 10])
    pen.cover([sp, hdl], seed=s + 30, feather=0.6)
    pen.fill([sp, hdl], 'metal', seed=s + 31)
    pen.fill(ell(head[0] - dv[0] * 3, head[1] - dv[1] * 3, 0.12 * r, 0.05 * r, 0, 360, 14, rot=ang), 'soup',
             seed=s + 32, tone=0.8)
    pen.line(sp, 2.6, tone=0.8, seed=s + 33, closed=True, taper=(0, 0))
    pen.line(Lh[::5], 2.4, tone=0.75, seed=s + 34, taper=(0.1, 0.2))
    pen.line(Rh[::5], 2.0, tone=0.55, seed=s + 35, taper=(0.1, 0.2))


def background(pen):
    wall(pen)
    window(pen)
    table(pen)
    matchbox(pen)
    for b in BOWLS:
        bowl(pen, b)


# ================================================================= 光、影
def lights(pen, t, d):
    f = wick_pt(t)
    a = light_amt(t, d)
    with pen.group('light', boil=0.3):
        if a > 0.01:
            fy = f[1] - 30
            pen.light(CX, fy, 560, 470, amt=a, color='lamp', seed=5200)
            pen.light(CX, fy, 200, 170, amt=min(1.0, a * 1.3), color='lamp', seed=5201)


def bowl_shadows(pen, t, d):
    a = light_amt(t, d)
    if a < 0.02:
        return
    fy = wick_pt(t)[1] - 34
    hf = SAUCER[1] - fy                                   # 火苗离桌面的高度（屏幕像素）
    with pen.group('shadows', boil=0.4):
        for b in BOWLS:
            g = bowl_geom(b)
            cx, cy, r = g['cx'], g['cy'], g['r']
            hb = 0.80 * r
            dist = cx - CX
            L = hb * dist / max(hf - hb, 40.0)
            L = float(np.clip(L, 30.0, 1300.0))
            fx, fz = cy + 0.74 * r, (cy + 0.74 * r - SAUCER[1]) * 0.6
            dv = np.float32([dist, fz])
            dv /= np.hypot(*dv) + 1e-6
            nv = np.float32([-dv[1], dv[0]])
            base = np.float32([cx, fx])
            w0, w1 = 0.62 * r, 0.62 * r + 0.18 * L
            poly = P([base - nv * w0 * 0.5 - dv * 0.3 * r, base + nv * w0 * 0.5 - dv * 0.3 * r,
                      base + nv * w1 * 0.5 + dv * L, base - nv * w1 * 0.5 + dv * L])
            amt = 0.55 * a / 0.58 * (1.0 - 0.55 * clamp(L / 1300.0))
            pen.shade(poly, amount=amt, seed=(5300, b['seed']), soft=10.0 + 0.02 * L, hatch=False,
                      holes=[g['body']])


def bowl_steam(pen, t):
    """汤最后一点热气，在镜头开头一秒里散掉（汤凉了）。"""
    amt = 1.0 - float(smooth01((t - 49.6) / 1.1))
    if amt < 0.03:
        return
    with pen.group('steam', boil=0.8):
        for j, b in enumerate(BOWLS):
            cx, cy = b['c']
            for k in range(2):
                ph = (t * 0.6 + k * 0.5 + j * 0.3) % 1.0
                yb = cy - 10 - ph * 90
                ys = np.linspace(yb, yb - 90 - 50 * ph, 6)
                xs = cx - 30 + 60 * k + 12 * np.sin((ys - cy) * 0.05 + t * 2 + k) - (cy - ys) * 0.06
                path = np.stack([xs, ys], 1).astype(np.float32)
                w = 8 + 10 * ph
                pen.line(path, w * 0.4, tone=0.16 * amt * math.sin(math.pi * ph), color='metal',
                         seed=(5400, j, k), taper=(0.4, 0.5), role='detail', dry=0.55, dry_from=0.1)


# ================================================================= 蜡烛
DRIPS = None


def drip_specs():
    """烛泪：(开始时间, 横向位置 u, 最终长度, 速度, 宽)。"""
    global DRIPS
    if DRIPS is None:
        r = rng(5500)
        out = []
        tt = T0 - 0.6
        while tt < T_OUT - 0.25:
            tt += r.uniform(0.18, 0.42)
            out.append((tt, r.uniform(-0.85, 0.85), r.uniform(60, 260), r.uniform(220, 420), r.uniform(7, 12)))
        DRIPS = out
    return DRIPS


def holder_back(pen):
    """烛台：搪瓷小托盘（右边一个指环把手）+ 托盘中间的小杯（后半）。"""
    s = 5600
    sx, sy, srx, sry = SAUCER
    pen.shade(ell(sx + 16, sy + 16, srx + 6, sry + 6, n=40), amount=0.45, seed=s, soft=8.0, hatch=False)
    rim = ell(sx, sy, srx, sry, 0, 360, 48)
    pen.cover(rim, seed=s + 1, feather=0.8)
    pen.fill(rim, 'enamel', seed=s + 2)
    pen.fill(ell(sx, sy + 2, srx - 12, sry - 5, 0, 360, 48), 'enamel', seed=s + 3, tone=0.10)
    pen.line(ell(sx, sy, srx, sry, 0, 180, 30), 5.0, tone=0.88, seed=s + 4, taper=(0.06, 0.08), head=0.4)
    pen.line(ell(sx, sy, srx, sry, 180, 360, 30), 3.0, tone=0.65, seed=s + 5, taper=(0.1, 0.1))
    pen.line(ell(sx, sy + 5, srx, sry + 2, 10, 170, 24), 3.0, tone=0.55, seed=s + 6, taper=(0.2, 0.2),
             role='detail')
    # 指环把手
    pen.line(ell(sx + srx + 22, sy - 2, 26, 16, 0, 360, 24), 7.0, tone=0.85, seed=s + 7, closed=True, taper=(0, 0))
    # 小杯后半圈
    pen.fill(ell(sx, CUP_Y, 46, 11, 0, 360, 30), 'enamel', seed=s + 8, tone=0.15)
    pen.line(ell(sx, CUP_Y, 46, 11, 180, 360, 20), 3.0, tone=0.7, seed=s + 9, taper=(0.1, 0.1))


def wax_pool(pen, t):
    """积在烛台托盘里的蜡：越烧越多（不规则的一摊，边缘一道淡墨，靠杯的地方鼓起）。"""
    u = clamp((t - T0) / (T_OUT - T0))
    if u < 0.05:
        return
    sx, sy, srx, sry = SAUCER
    rr = rng(5650)
    n = 18
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    k = 1.0 + 0.16 * rr.standard_normal(n)
    rx = (50 + 62 * u) * k
    ry = (12 + 13 * u) * k
    poly = spline(np.stack([sx + 6 + rx * np.cos(a), sy - 2 + ry * np.sin(a)], 1).astype(np.float32), 3.0,
                  closed=True)
    pen.cover(poly, seed=5651, feather=0.8)
    pen.fill(poly, 'cloth', seed=5652)
    pen.shade(np.vstack([poly[len(poly) // 2:], poly[:2]]), amount=0.18, seed=5653, soft=3.0, hatch=False)
    pen.line(poly, 2.4, tone=0.55, seed=5654, closed=True, role='detail', taper=(0, 0))


def candle_body(pen, t, d):
    s = 5700
    yt = y_top(t)
    yb = CUP_Y + 4
    if t >= T_OUT:
        yt = Y_SHORT
    x0, x1 = CX - RXC, CX + RXC
    body = np.vstack([P([(x0, yt), (x0, yb)]), ell(CX, yb, RXC, 8, 180, 0, 12), P([(x1, yb), (x1, yt)])])
    pen.cover(body, seed=s, feather=0.6)
    pen.fill(body, 'cloth', seed=s + 1, c_fade=False, broad=False, grad_auto=False)
    # 右侧暗面（光在头顶：上亮下暗一点）
    pen.shade(P([(CX + 8, yt + 6), (x1, yt + 4), (x1, yb), (CX + 12, yb)]), amount=0.22, seed=s + 2, angle=90,
              spacing=7.0, grad=(0, yt, 0, yb, 0.6, 1.2))
    # 靠近火苗的一截蜡是透光的（提白）
    pen.lift(P([(x0 + 2, yt), (x1 - 2, yt), (x1 - 4, yt + 46), (x0 + 4, yt + 46)]), amt=0.6, seed=s + 3, soft=6.0)
    # 烛泪：凝在烛身上的一道道（顶上那截已经烧掉的就不见了）
    for i, (t0, u, lf, sp, wv) in enumerate(drip_specs()):
        if t < t0:
            continue
        y0 = y_top(t0) + 3
        L = min(lf, sp * (t - t0))
        y1 = min(y0 + L, CUP_Y - 2)
        ys = max(y0, yt + 4)
        if y1 - ys < 5:
            continue
        x = CX + u * RXC * 0.92
        xs = x + 1.5 * math.sin(i)
        path = P([(x, ys), (x + 0.5, (ys + y1) / 2), (xs, y1)])
        wv2 = wv * (0.55 + 0.45 * math.sqrt(1 - u * u))         # 侧面的看起来窄
        poly = tube(path, [wv2 * 0.8, wv2, wv2 * 1.25])[0]
        bead = ell(xs, y1, wv2 * 0.75, wv2 * 0.85, 0, 360, 12)
        pen.fill([poly, bead], 'enamel', seed=(s, 10, i), tone=0.04)
        side = 1.0 if u >= 0 else -1.0
        pen.line(np.vstack([poly[len(poly) // 2:][::-1][:-1], bead[2:9]]) if False else
                 P([(x + side * wv2 * 0.5, ys), (xs + side * wv2 * 0.6, y1 - 2), (xs, y1 + wv2 * 0.85)]),
                 1.8, tone=0.55, seed=(s, 11, i), role='detail', taper=(0.3, 0.1))
        pen.lift(ell(xs - wv2 * 0.25, y1 - wv2 * 0.3, wv2 * 0.22, wv2 * 0.3, n=8), amt=0.8, seed=(s, 12, i),
                 soft=0.5)
    # 轮廓
    pen.line(D([(x0, yt + 2), (x0 - 0.5, yb)], 20), 4.5, tone=0.85, seed=s + 4, taper=(0.05, 0.1), head=0.3,
             dry=0.3, dry_from=0.7)
    pen.line(D([(x1, yt + 2), (x1 + 0.5, yb)], 20), 3.4, tone=0.65, seed=s + 5, taper=(0.05, 0.1), head=0.2,
             dry=0.4, dry_from=0.6)
    # 烛口：融化的一圈（不平的边 + 中间凹下去的蜡池）
    rr = rng(s, 'lip', int(yt / 6))
    lip = ell(CX, yt, RXC, 7.5, 0, 360, 24)
    lip[:, 1] += np.float32(rr.normal(0, 1.2, len(lip))) * (np.sin(np.linspace(0, 2 * math.pi, len(lip))) < 0)
    pen.fill(lip, 'enamel', seed=s + 6, tone=0.06)
    pen.shade(ell(CX + 2, yt + 1, RXC * 0.72, 4.5, n=16), amount=0.25, seed=s + 7, soft=1.5, hatch=False)
    pen.line(lip, 2.6, tone=0.7, seed=s + 8, closed=True, role='detail', taper=(0, 0))
    # 杯的前半圈（盖住蜡烛的根）
    cup = np.vstack([ell(CX, CUP_Y, 46, 11, 0, 180, 16), P([(CX - 46, CUP_Y), (CX - 44, CUP_Y + 24)]),
                     ell(CX, CUP_Y + 24, 44, 10, 180, 0, 16), P([(CX + 44, CUP_Y + 24)])])
    pen.cover(cup, seed=s + 9, feather=0.6)
    pen.fill(cup, 'enamel', seed=s + 10)
    pen.fill(np.vstack([ell(CX, CUP_Y + 2, 46, 11, 0, 180, 16), ell(CX, CUP_Y + 8, 46, 11, 180, 0, 16)]),
             'night_l', seed=s + 11)
    pen.shade(P([(CX + 14, CUP_Y + 4), (CX + 46, CUP_Y), (CX + 44, CUP_Y + 24), (CX + 16, CUP_Y + 32)]),
              amount=0.3, seed=s + 12, hatch=False)
    pen.line(ell(CX, CUP_Y, 46, 11, 0, 180, 16), 3.6, tone=0.85, seed=s + 13, taper=(0.1, 0.1))
    pen.line(P([(CX - 46, CUP_Y), (CX - 44, CUP_Y + 24)]), 3.6, tone=0.85, seed=s + 14, taper=(0.1, 0.1))
    pen.line(P([(CX + 46, CUP_Y), (CX + 44, CUP_Y + 24)]), 3.0, tone=0.7, seed=s + 15, taper=(0.1, 0.1))


def wick(pen, t, d):
    s = 5800
    yt = Y_SHORT if t >= T_OUT else y_top(t)
    bend = 0.0 if t < T_OUT else 1.0
    p = P([(CX, yt + 2), (CX + 1.5, yt - 8), (CX + 3 + 4 * bend, yt - 15 + 2 * bend)])
    pen.line(p, 4.4, tone=0.95, seed=s, taper=(0.0, 0.3), role='feature')
    if t >= T_OUT:
        # 余烬：烛芯头上一点亮，很快暗下去
        e = 1.0 - clamp((t - T_OUT) / 0.45)
        if e > 0.05:
            pen.lift(ell(p[-1][0], p[-1][1], 3.0, 3.0, n=8), amt=0.9 * e, seed=s + 1, soft=0.8)
            pen.lift(ell(p[-1][0], p[-1][1], 10.0, 10.0, n=12), amt=0.35 * e, seed=s + 2, soft=4.0)


# ================================================================= 火苗
def flame(pen, t, d):
    k = flame_k(t, d)
    if t >= T_OUT or k <= 0.06:
        return
    s = 5900
    r = rng(5901, d)
    w = wick_pt(t)
    Hf = 86.0 * k
    Wf = 27.0 * min(1.0, 0.55 + 0.45 * k)
    sway = 7.0 * r.standard_normal() * (1.0 + 1.5 * float(smooth01((t - T_WEAK) / 0.2)))
    base = np.float32([w[0], w[1] + 6])
    tip = base + np.float32([sway, -Hf])
    belly = base + np.float32([sway * 0.15, -Hf * 0.20])
    pts = P([tip,
             belly + np.float32([Wf * 0.30 + sway * 0.4, -Hf * 0.45]),
             belly + np.float32([Wf * 0.52, -Hf * 0.05]),
             belly + np.float32([Wf * 0.38, Hf * 0.12]),
             base + np.float32([0, 2]),
             belly + np.float32([-Wf * 0.38, Hf * 0.12]),
             belly + np.float32([-Wf * 0.52, -Hf * 0.05]),
             belly + np.float32([-Wf * 0.30 + sway * 0.4, -Hf * 0.45])])
    poly = spline(pts, 1.5, closed=True)
    c = (base + tip) / 2
    with pen.group('flame', boil=0.6):
        # 一圈淡墨的光晕（像灯芯草纸上洇开的一圈）
        ring_o = ell(c[0], c[1], 92 * (0.7 + 0.3 * k), 108 * (0.7 + 0.3 * k), n=40)
        ring_i = ell(c[0], c[1], 62 * (0.7 + 0.3 * k), 78 * (0.7 + 0.3 * k), n=40)
        pen.fill(ring_o, 'ink', seed=s, c_dens=0.10, holes=[ring_i], soft=14.0, rim=0.0, bloom=0.0,
                 grad_auto=False)
        # 火苗：留白
        pen.lift(poly, amt=1.0, seed=s + 1, soft=1.2)
        pen.lift(ell(c[0], c[1] + Hf * 0.1, Wf * 1.4, Hf * 0.75, n=24), amt=0.6, seed=s + 2, soft=10.0)
        # 外焰一笔极淡的墨边（只在上半）+ 焰心
        pen.line(np.vstack([pts[6:], pts[:3]]), 1.8, tone=0.28, seed=s + 3, role='feature', taper=(0.4, 0.4))
        pen.fill(ell(base[0] + sway * 0.05, base[1] - Hf * 0.14, Wf * 0.22, Hf * 0.13, n=14), 'ink', seed=s + 4,
                 c_dens=0.16, rim=0.3, bloom=0.0, grad_auto=False)


# ================================================================= 烟（这个镜头的重点）
SMOKE_BOX = (380, -20, 1100, 720)


def _smoke_strand(t, a, phase, kamp, side, dens, n=90):
    """一缕烟：从烛芯出发，按“曲率随弧长变化”积分出曲线（往上走，越高摆得越大，顶上卷一个钩）。
    → (点, 宽, 浓度) 或 None。a = 冒烟以来的秒数。"""
    L = 470.0 * a - 40.0 * a * a
    if L < 8:
        return None
    w0 = wick_pt(T_OUT + 0.01)
    ss = np.linspace(0, L, n)
    ds = ss[1] - ss[0]
    u = ss / 520.0
    v = 430.0                                         # 烟上升（形状往上走）的速度
    lam = 250.0
    amp = kamp * (0.002 + 0.016 * smooth01((u - 0.06) / 0.45))
    kap = amp * np.sin(2 * math.pi * (ss - v * a) / lam + phase)
    # 顶上卷起的钩（最老的那一截）
    hook = smooth01((ss / max(L, 1.0) - 0.62) / 0.35) * 0.020 * side * kamp * clamp(a / 0.5)
    kap = kap + hook
    th = -math.pi / 2 + np.cumsum(kap) * ds
    th = th + 0.06 * side * smooth01(u / 0.5)
    pts = np.zeros((n, 2), np.float32)
    pts[0] = w0
    pts[1:] = w0 + np.cumsum(np.stack([np.cos(th[:-1]), np.sin(th[:-1])], 1) * ds, 0)
    q = ss / max(L, 1.0)
    # 宽度：根部细，往上变宽；散开时更宽
    disp = clamp((t - T_DETACH) / 0.6)
    wid = 3.0 + 26.0 * q ** 1.2 + 34.0 * disp * q ** 1.5 + 8.0 * clamp(a / 0.8) * q
    # 浓度：根部浓，越往上越淡；离开烛芯后根部变空
    den = dens * (1.0 - 0.80 * q ** 1.1) * (1.0 - 0.55 * disp * q)
    if t > T_DETACH:
        gone = 430.0 * (t - T_DETACH)                  # 根部空出来的长度
        den = den * smooth01((ss - gone) / 60.0)
    den = den * smooth01(ss / 14.0 + 0.2)
    return pts, wid, den


def smoke(pen, t, d):
    if t < T_SMOKE:
        return
    a = t - T_SMOKE
    X0, Y0, X1, Y1 = SMOKE_BOX
    sc = 0.5
    ww, hh = int((X1 - X0) * sc), int((Y1 - Y0) * sc)
    crisp = np.zeros((hh, ww), np.float32)
    soft = np.zeros((hh, ww), np.float32)
    strands = [(_smoke_strand(t, a, 0.0, 1.0, 1.0, 1.0), 1.0),
               (_smoke_strand(t, a, 0.9, 0.8, -1.0, 0.55), 0.8),
               (_smoke_strand(t, a, -1.3, 1.25, 1.0, 0.40), 1.2)]
    core_pts = None
    for k, (res, _) in enumerate(strands):
        if res is None:
            continue
        pts, wid, den = res
        if k == 0:
            core_pts = (pts, den)
        # 各缕之间随高度慢慢分开
        q = np.linspace(0, 1, len(pts))[:, None]
        pts = pts + np.float32([[(k - 1) * 22.0, 0]]) * q ** 1.5
        L = len(pts)
        for j in range(L - 1):
            if den[j] < 0.01:
                continue
            qq = j / (L - 1)
            wcr = 1.0 - smooth01((qq - 0.25) / 0.4)
            p0 = np.round((pts[j] - (X0, Y0)) * sc * 16).astype(np.int32)
            p1 = np.round((pts[j + 1] - (X0, Y0)) * sc * 16).astype(np.int32)
            th = max(1, int(round(wid[j] * sc)))
            for m, val in ((crisp, den[j] * wcr), (soft, den[j] * (1 - wcr * 0.7))):
                if val > 0.005:
                    cv2.line(m, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), float(val), th, cv2.LINE_AA,
                             shift=4)
    crisp = cv2.GaussianBlur(crisp, (0, 0), 1.2)
    soft = cv2.GaussianBlur(soft, (0, 0), 5.0)
    m = np.clip(np.maximum(crisp, soft * 0.95), 0, 1)
    m = cv2.resize(m, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_LINEAR)
    with pen.group('smoke', boil=0.5, bleed=2.2, c_gain=0.9):
        pen.fill(mask=(m, X0, Y0), color='ink', c_dens=0.62, edge=1.0, rim=0.10, bloom=0.0, rough=0.16,
                 var=0.22, cell=26.0, drift=0.35, c_fade=False, broad=False, grad_auto=False)
        # 根部一根细的浓墨丝（毛笔中锋），往上断开、变淡
        if core_pts is not None:
            pts, den = core_pts
            n = len(pts)
            if t > T_DETACH:
                gone = 430.0 * (t - T_DETACH)
                ss = np.linspace(0, 1, n) * (470.0 * a - 40.0 * a * a)
                pts = pts[ss > gone]
            if len(pts) >= 4:
                j1 = max(4, int(len(pts) * 0.55))
                pen.line(pts[:j1:2], 2.6, tone=0.85, seed=6001, role='detail', taper=(0.0, 0.6), fade=0.85,
                         breaks=0.25, dry=0.3, dry_from=0.5)


# ================================================================= 窗外的雪
def snow(pen, t):
    x0, y0, x1, y1 = WIN
    r = rng(6100)
    with pen.group('snow', boil=0.6):
        for i in range(36):
            far = i < 20
            sp = r.uniform(24, 40) if far else r.uniform(46, 78)
            size = r.uniform(1.5, 2.6) if far else r.uniform(3.0, 4.6)
            amp = r.uniform(4, 12)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-20, x1)
            ys = r.uniform(0, y1)
            yy = (ys + sp * t) % (y1 + 20) - 20
            xx = (xs + 6 * t + amp * math.sin(1.4 * t + ph)) % (x1 + 20) - 20
            if not (-10 < xx < x1 - 8 and -10 < yy < y1 - 6):
                continue
            if abs(xx - 123) < 7 + size or abs(yy - 218) < 6 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', i))


# ================================================================= 场景
def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    d = pen.d
    with pen.group('bg', boil=BG_BOIL, cache=('candle', pen.d % 3)):
        background(pen)
    snow(pen, t)
    lights(pen, t, d)
    bowl_shadows(pen, t, d)
    bowl_steam(pen, t)
    with pen.group('holder', boil=0.4):
        holder_back(pen)
        wax_pool(pen, t)
    with pen.group('candle', boil=0.45):
        candle_body(pen, t, d)
        wick(pen, t, d)
    flame(pen, t, d)
    smoke(pen, t, d)
