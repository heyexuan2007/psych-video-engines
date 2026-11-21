# -*- coding: utf-8 -*-
"""
第 2 镜「第十八句句示例」（成片 5.01–8.83，C 水墨，红色只给汤和豆）。
锅的俯拍大特写：深红的红豆汤占满画面，锅沿是一圈浓墨的搪瓷卷边（外深灰、里米白，内壁上一圈汤渍）。
她站在锅的左边：木勺从画面左上伸进来，在锅的左半边慢慢画圈（勺头没在汤里，只露出勺柄，柄上沾着汤的那截染红）。
汤面留下一圈圈螺旋纹：勺子划过的地方一道暗槽 + 两侧浅色的豆沙浪；汤绕着锅心转、中间慢外圈快，
尾迹被剪切成螺旋，3.6 秒才慢慢化开（缠绵）。汤面上的红豆跟着汤转；小气泡冒起、破开；热气在画面上方飘。
镜头：极慢推近（pen.view），以那颗会裂开的豆为中心，3.82 秒推近 16%（勺柄永远在豆的左边，不会挡住它）。
  6.40 那颗豆在滚汤里微微发胀、轻轻颤；6.93 豆皮上先出现一道细缝；
  7.01「伤」豆皮沿长边裂开（0.4 秒），露出浅粉的豆芯，周围荡开一小圈涟漪；
  7.83「口」从裂口冒起一缕热气，卷着往上飘。
四周的道具：锅的木柄（右）、电炉的边和旋钮（右下）、台面上散落的红豆、叠着的格子抹布（左下）。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒，默认 pen.t）；zoom 覆盖推近量（默认 0.16，0 = 不推）
KEY0：那颗豆在“伤”时的场景坐标（推近中心，屏幕上固定不动）。
"""
import math

import cv2
import numpy as np

from core import W, H, densify, ell, spline, tube, rng, clamp, smooth01, ease_out

try:
    from shapely.geometry import Polygon as _SPoly
except Exception:      # pragma: no cover
    _SPoly = None

# ---------------------------------------------------------------- 时间（成片秒）
T0, T1 = 5.01, 8.83
T_SWELL = 6.40         # 开始发胀、轻颤
T_HAIR = 6.93          # 细缝出现
T_CRACK = 7.01         # 「伤」：裂开（0.4 秒）
T_OPEN = 0.40
T_STEAM = 7.83         # 「口」：裂口冒热气
ZOOM = 0.16

# ---------------------------------------------------------------- 布局（场景坐标，推近前 = 屏幕坐标）
SC = (900.0, 330.0)            # 汤面椭圆中心
SRX, SRY = 800.0, 556.0        # 汤面椭圆半轴（俯视，略带透视）
RC = (900.0, 296.0)            # 锅沿椭圆中心（汤面比锅沿低，透视里往下挪）
LIP_IN = (812.0, 566.0)        # 锅沿内沿
LIP_OUT = (852.0, 598.0)       # 锅沿外沿
BODY_C = (900.0, 404.0)        # 锅底外沿椭圆中心（看得见锅身前面一窄条）
BODY_R = (838.0, 584.0)
PLATE = (40, -340, 1760, 1004)  # 电炉面板
POT_COL = '#45474F'            # 搪瓷小锅（深灰，和第 1 镜一致）

KEY_RX, KEY_RY, KEY_ROT = 44.0, 26.0, -12.0

BG_BOIL = 0.4

# ---------------------------------------------------------------- 汤的流动（圆坐标：汤面椭圆归一化到单位圆）
OMEGA_S = 2 * math.pi / 2.8          # 勺子一圈 2.8 秒（慢慢地搅）


def omega(r):
    """汤绕锅心转的角速度（顺时针）：勺子划过的那一圈（r≈0.40）最快，锅边几乎不动（那颗豆贴着锅边）。"""
    r = np.asarray(r, np.float64)
    return OMEGA_S * 0.35 * (0.04 + 0.96 * np.exp(-((r - 0.40) / 0.19) ** 2))


def spoon_rt(tau):
    """勺子入汤点（极坐标 r, th）。半径在 0.32–0.48 之间慢慢变，尾迹才会剪切成螺旋。"""
    tau = np.asarray(tau, np.float64)
    return 0.40 + 0.08 * np.sin(2 * math.pi * tau / 3.4 + 0.7), OMEGA_S * tau + 0.4


def spoon_c(tau):
    r, th = spoon_rt(tau)
    return np.stack([r * np.cos(th), r * np.sin(th)], -1)


def c2s(c):
    """圆坐标（笛卡尔）→ 场景坐标。"""
    c = np.asarray(c, np.float64)
    return np.stack([SC[0] + SRX * c[..., 0], SC[1] + SRY * c[..., 1]], -1).astype(np.float32)


def polar(r, th):
    r = np.asarray(r, np.float64)
    th = np.asarray(th, np.float64)
    return c2s(np.stack([r * np.cos(th), r * np.sin(th)], -1))


KEY_R, KEY_TH = 0.80, math.radians(40.0)      # 那颗豆：右下，贴着锅边、汤几乎不动的地方
KEY_DRIFT = 0.012                             # 它自己慢慢漂（弧度/秒）


def key_pos(t):
    p = polar(KEY_R, KEY_TH + KEY_DRIFT * (t - T_CRACK))
    return float(p[0]), float(p[1])


KEY0 = key_pos(T_CRACK)        # 推近中心


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def ering(c, r_out, r_in, a0=0.0, a1=360.0, n=96):
    """椭圆环（a0..a1 一段）→ 多边形。"""
    o = ell(c[0], c[1], r_out[0], r_out[1], a0, a1, n)
    i = ell(c[0], c[1], r_in[0], r_in[1], a1, a0, n)
    return np.vstack([o, i])


def pot_sil():
    return np.vstack([ell(RC[0], RC[1], LIP_OUT[0], LIP_OUT[1], 180, 360, 64),
                      ell(BODY_C[0], BODY_C[1], BODY_R[0], BODY_R[1], 0, 180, 64)])


def _minus(poly, cut, clip_box=(-60, -60, W + 60, H + 60)):
    """poly − cut，只留画面里的部分 → 多边形列表（锅挡住的地方不画，省时间）。"""
    if _SPoly is None:
        return [poly]
    g = _SPoly(np.asarray(poly, np.float64)).buffer(0).difference(_SPoly(np.asarray(cut, np.float64)).buffer(0))
    x0, y0, x1, y1 = clip_box
    g = g.intersection(_SPoly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    out = []
    for q in getattr(g, 'geoms', [g]):
        if q.geom_type == 'Polygon' and q.area > 50:
            out.append(np.float32(np.asarray(q.exterior.coords)[:-1]))
    return out


# ================================================================= 背景：台面、电炉、锅身
def counter(pen):
    s = 100
    x0, y0, x1, y1 = PLATE
    frame = P([(-40, -40), (W + 40, -40), (W + 40, H + 40), (-40, H + 40)])
    plate = P([(x0, y0), (x1, y0), (x1, y1 + 46), (x0, y1 + 46)])
    for k, q in enumerate(_minus(frame, plate)):
        pen.fill(q, 'wood', seed=(s, k), tone=0.24, c_fade=False, broad=False, streak=0.4, sangle=2.0)
    r = rng(s, 'grain')
    for k, (a0, b0, a1, b1) in enumerate([(-30, 1062, 420, 1070), (1500, 1066, 1960, 1058), (1768, 120, 1790, 600),
                                          (1786, 640, 1800, 980), (8, 200, 14, 700)]):
        pen.line(D([(a0, b0), ((a0 + a1) / 2 + r.uniform(-3, 3), (b0 + b1) / 2), (a1, b1)], 30), 2.4, tone=0.32,
                 color='wood_d', seed=s + 10 + k, taper=(0.3, 0.4), role='detail', dry=0.6, dry_from=0.2)


def stove(pen):
    """电炉：比锅大一圈的金属面板，四角露出来；右前方一个旋钮。"""
    s = 200
    x0, y0, x1, y1 = PLATE
    plate = P([(x0 + 30, y0), (x1 - 30, y0), (x1, y0 + 30), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1),
               (x0, y1 - 30), (x0, y0 + 30)])
    vis = _minus(plate, pot_sil())
    pen.cover(vis, seed=s, feather=1.0)
    for k, q in enumerate(vis):
        pen.fill(q, 'metal', seed=(s, 1, k), c_dens=0.20, c_fade=False, broad=False)
    # 面板上一圈圈的同心纹（电炉盘）露出的角
    for k, rr in enumerate((1.08, 1.13)):
        arc = ell(RC[0], RC[1] + 60, LIP_OUT[0] * rr, LIP_OUT[1] * rr, 100, 150, 20)
        pen.line(arc, 2.4, tone=0.35, seed=s + 20 + k, role='detail', taper=(0.3, 0.3), dry=0.5, dry_from=0.3)
        arc = ell(RC[0], RC[1] + 60, LIP_OUT[0] * rr, LIP_OUT[1] * rr, 30, 80, 20)
        pen.line(arc, 2.4, tone=0.35, seed=s + 24 + k, role='detail', taper=(0.3, 0.3), dry=0.5, dry_from=0.3)
    front = P([(x0 + 10, y1 - 2), (x1 - 10, y1 - 2), (x1 - 16, y1 + 44), (x0 + 16, y1 + 44)])
    pen.cover(front, seed=s + 2, feather=0.8)
    pen.fill(front, 'metal', seed=s + 3, c_dens=0.34, c_fade=False, broad=False)
    pen.line(D([(x0 + 4, y1 - 20), (x0 + 30, y1 + 1), ((x0 + x1) / 2, y1 + 3), (x1 - 30, y1 + 1), (x1 - 4, y1 - 20)],
               40), 7, tone=0.85, seed=s + 4, taper=(0.05, 0.12), head=0.4, dry=0.4, dry_from=0.7)
    pen.line(D([(x0 + 16, y1 + 44), (x1 - 16, y1 + 44)], 40), 5, tone=0.7, seed=s + 5, taper=(0.1, 0.2), dry=0.5,
             dry_from=0.5)
    pen.line(D([(x0, -40), (x0 + 1, y1 - 30)], 40), 6, tone=0.8, seed=s + 6, taper=(0.05, 0.2), head=0.3)
    pen.line(D([(x1, -40), (x1 - 1, y1 - 30)], 40), 5, tone=0.7, seed=s + 7, taper=(0.05, 0.2), head=0.2, dry=0.5,
             dry_from=0.6)
    # 旋钮（右前）
    kx, ky = 1640, 1026
    pen.shade(ell(kx + 10, ky + 12, 30, 12, n=20), amount=0.35, seed=s + 8, soft=3.0)
    pen.dot(kx, ky, 26, 17, color='ink', tone=0.75, seed=s + 9)
    pen.line(P([(kx - 3, ky - 14), (kx + 2, ky + 13)]), 4, tone=0.2, color='snow', seed=s + 10, role='detail')
    pen.lift(ell(kx - 9, ky - 7, 6, 3, n=8), amt=0.7, seed=s + 11, soft=0.6)


def pot_body(pen):
    """锅身外壁（深灰搪瓷）：俯视时只在前面露出一窄条。"""
    s = 300
    sil = pot_sil()
    pen.cover(sil, seed=s + 1, feather=1.0)
    band = np.vstack([ell(BODY_C[0], BODY_C[1], BODY_R[0], BODY_R[1], 0, 180, 64),
                      ell(RC[0], RC[1], LIP_OUT[0] - 10, LIP_OUT[1] - 10, 180, 0, 64)])
    pen.fill(band, POT_COL, seed=s + 2, c_dens=0.62, c_fade=False, broad=False)
    # 外壁上一道干笔提白（光从左上来）
    pen.lift(tube(ell(BODY_C[0], BODY_C[1] - 18, BODY_R[0] - 10, BODY_R[1] - 10, 120, 160, 12), [3, 12, 4])[0],
             amt=0.55, seed=s + 3, soft=2.0, dry=0.7, streak=0.5)
    pen.line(ell(BODY_C[0], BODY_C[1], BODY_R[0], BODY_R[1], 6, 174, 60), 9, tone=0.92, seed=s + 4,
             taper=(0.08, 0.12), head=0.4, lift=0.2, dry=0.35, dry_from=0.7)


def pot_handle(pen):
    """锅的木柄：从右边锅沿伸出画外（铆钉 + 金属卡座）。"""
    s = 350
    path = [(1742, 312), (1840, 292), (1960, 270)]
    poly, L, R = tube(path, [64, 54, 58])
    pen.shade(tube([(1752, 344), (1850, 326), (1970, 304)], [60, 52, 56])[0], amount=0.4, seed=s, soft=6.0,
              hatch=False)
    br = tube([(1730, 314), (1792, 303)], [74, 62])[0]
    pen.cover([poly, br], seed=s + 1, feather=0.8)
    pen.fill(poly, 'wood_d', seed=s + 2, c_fade=False, broad=False)
    pen.fill(br, POT_COL, seed=s + 3, c_dens=0.6, c_fade=False, broad=False)
    pen.shade(np.vstack([R, spline(path, 4.0)[::-1]]), amount=0.35, seed=s + 4, angle=10)
    pen.line(L[::6], 5, tone=0.85, seed=s + 5, taper=(0.05, 0.1), head=0.3)
    pen.line(R[::6], 6, tone=0.9, seed=s + 6, taper=(0.05, 0.1), head=0.4)
    for k in range(3):
        o = (k - 1) * 13
        pen.line(P([(1810, 298 + o), (1880, 285 + o), (1960, 272 + o)]), 2.0, tone=0.45, color='wood_d',
                 seed=s + 10 + k, role='detail', taper=(0.3, 0.3), dry=0.6, dry_from=0.2)
    for k, (x, y) in enumerate([(1756, 300), (1764, 324)]):
        pen.dot(x, y, 5, 5, color='ink', tone=0.85, seed=s + 20 + k)
        pen.lift(ell(x - 1.5, y - 1.5, 1.6, 1.2, n=6), amt=0.8, seed=s + 25 + k, soft=0.3)


def interior(pen):
    """锅的内壁（米白搪瓷）：只在汤面和锅沿之间露出一窄圈；汤面上方一圈红豆汤留下的汤渍。"""
    s = 400
    band = np.vstack([ell(RC[0], RC[1], LIP_IN[0] + 4, LIP_IN[1] + 4, 0, 360, 120),
                      ell(SC[0], SC[1], SRX - 6, SRY - 6, 360, 0, 120)])
    pen.cover(band, seed=s, feather=1.0)
    stain = ering(SC, (SRX * 1.012 + 8, SRY * 1.012 + 9), (SRX * 0.99, SRY * 0.99), 160, 380)
    pen.fill(stain, 'soup', seed=s + 3, tone=0.22, rim=0.6)


def beans_counter(pen):
    s = 500
    pts = [(250, 1060, 20), (318, 1068, -40), (1500, 1064, 70), (1560, 1056, 10), (1838, 640, 30), (1866, 706, -20),
           (1850, 820, 60), (1900, 560, -60), (20, 600, 80), (1590, 1072, -30), (1880, 930, 40)]
    for i, (x, y, a) in enumerate(pts):
        pen.dot(x, y, 15, 10, color='bean', tone=1.0, seed=(s, i), rot=a, shadow=True)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        pen.line(P([(x - 5 * ca + 6 * sa, y - 5 * sa - 6 * ca), (x + 5 * ca + 6 * sa, y + 5 * sa - 6 * ca)]), 2.6,
                 tone=0.8, color='snow', seed=(s, 30 + i), role='detail', taper=(0.3, 0.3))


def towel(pen):
    """左下角：叠起来的格子抹布（米白，两道深色条纹，折痕）。"""
    s = 550
    q = P([(-40, 846), (120, 862), (196, 900), (238, 1100), (-40, 1100)])
    q = spline(q, 4.0, closed=True)
    pen.shade(spline(P([(-40, 870), (150, 886), (226, 930), (268, 1100), (-40, 1100)]), 4.0, closed=True),
              amount=0.35, seed=s + 9, soft=10.0, hatch=False)
    pen.cover(q, seed=s, feather=1.0)
    pen.fill(q, 'cloth', seed=s + 1)
    pen.shade(P([(-40, 960), (182, 980), (238, 1100), (-40, 1100)]), amount=0.22, seed=s + 2, angle=80)
    for k, o in enumerate((40, 62, 150, 172)):
        pen.line(D([(-40, 846 + o), (150 + 0.3 * o, 864 + o * 0.95)], 30), 8 if k % 2 == 0 else 4, tone=0.55,
                 seed=s + 3 + k, role='detail', taper=(0.1, 0.2), dry=0.5, dry_from=0.4)
    for k, x in enumerate((40, 92)):
        pen.line(D([(x, 852), (x + 18, 1100)], 30), 5, tone=0.42, seed=s + 8 + k, role='detail', taper=(0.1, 0.2),
                 dry=0.6, dry_from=0.3)
    pen.line(D([(-40, 960), (120, 972), (186, 986)], 30), 3, tone=0.5, seed=s + 12, role='detail', taper=(0.2, 0.3))
    pen.line(q[::5], 5, tone=0.8, seed=s + 6, taper=(0.1, 0.2), head=0.3)


def background(pen):
    counter(pen)
    stove(pen)
    beans_counter(pen)
    towel(pen)
    pot_body(pen)
    pot_handle(pen)
    interior(pen)


# ================================================================= 汤
def soup_base(pen, t):
    s = 600
    soup = ell(SC[0], SC[1], SRX, SRY, 0, 360, 120)
    pen.cover(soup, seed=s, feather=1.2)
    pen.fill(soup, 'soup', seed=s + 1, tone=1.15, rgrad=(SC[0] - 60, SC[1] - 20, 80, 880, 0.80, 1.35), rim=0.12,
             bloom=0.0, var=0.16, cell=120.0, rough=0.10, drift=0.05)
    # 窗户的倒影：汤面左上一片柔和的反光（浅豆沙色）
    pen.lift(ell(SC[0] - 340, SC[1] - 250, 300, 110, n=40, rot=-12), amt=0.18, seed=s + 3, soft=40.0)
    pen.lift(tube(ell(SC[0] - 300, SC[1] - 260, 260, 100, 205, 300, 14), [5, 20, 7])[0], amt=0.24, seed=s + 4,
             soft=6.0, dry=0.6, streak=0.6)
    # 跟着汤转的浅色豆沙纹（浓淡变化，慢慢转）
    r = rng(s, 'swirl')
    for k in range(6):
        rr = r.uniform(0.30, 0.86)
        th0 = r.uniform(0, 2 * math.pi)
        ln = r.uniform(0.6, 1.1)
        th = th0 + float(omega(rr)) * t
        ths = np.linspace(th, th + ln, 14)
        rs = rr + 0.04 * np.sin(np.linspace(0, math.pi, 14) + k)
        pts = polar(rs, ths)
        wv = r.uniform(18, 40)
        pen.lift(tube(pts, [wv * 0.3, wv, wv * 0.8, wv * 0.25])[0], amt=r.uniform(0.10, 0.16), seed=(s, 10 + k),
                 soft=10.0)


# ---------------------------------------------------------------- 勺子划出的螺旋纹
T_TRAIL = 4.4
WAKE_BOX = (60, -30, 1740, 900)
# 更早搅出来的旧纹：几条正在被汤慢慢绕紧、化开的螺旋（r0, r1, 起始角, 圈数, 浓度）
OLD_SPIRALS = [(0.22, 0.62, 0.3, 1.15, 0.55), (0.30, 0.70, 2.6, 1.0, 0.42), (0.18, 0.50, 4.4, 0.8, 0.35)]


def wake_pts(t, dt=0.03):
    """尾迹：勺子在 τ 时刻经过的点，按汤的转动带到 t 时刻 → (中心线, 外侧浪, 内侧浪, 年龄)。"""
    taus = np.arange(t - T_TRAIL, t + 1e-6, dt)
    ages = t - taus
    c = spoon_c(taus)
    r = np.hypot(c[:, 0], c[:, 1])
    th = np.arctan2(c[:, 1], c[:, 0]) + omega(r) * ages
    u = ages / T_TRAIL
    pc = polar(r, th)
    po = polar(r + 0.020 + 0.03 * u, th - 0.025)
    pi = polar(np.maximum(0.02, r - 0.018 - 0.02 * u), th - 0.02)
    return pc, po, pi, ages


def wake(pen, t):
    """暗槽（深红）+ 外侧一道浅色豆沙浪，越老越宽越淡。"""
    X0, Y0, X1, Y1 = WAKE_BOX
    sc = 0.5
    ww, hh = int((X1 - X0) * sc), int((Y1 - Y0) * sc)
    dark = np.zeros((hh, ww), np.float32)
    light = np.zeros((hh, ww), np.float32)
    pc, po, pi, ages = wake_pts(t)
    off = np.float32([X0, Y0])
    # 旧纹：阿基米德螺旋，各点按自己半径的角速度转（于是越绕越紧），很淡、很宽
    for j, (r0, r1, a0, turns, val) in enumerate(OLD_SPIRALS):
        n = 90
        q = np.linspace(0, 1, n)
        rr = r0 + (r1 - r0) * q
        th = a0 + 2 * math.pi * turns * q + omega(rr) * t
        fade = np.sin(math.pi * q) ** 0.7
        for which, dr, wv, vv in ((dark, 0.0, 14, 0.55), (light, 0.025, 22, 0.75)):
            pts = np.round((polar(rr + dr, th) - off) * sc * 16).astype(np.int32)
            for k in range(n - 1):
                cv2.line(which, (int(pts[k, 0]), int(pts[k, 1])), (int(pts[k + 1, 0]), int(pts[k + 1, 1])),
                         float(val * vv * fade[k]), max(1, int(wv * sc)), cv2.LINE_AA, shift=4)
    for k in range(len(ages) - 1):
        a = ages[k]
        u = a / T_TRAIL
        amp = (1.0 - u) ** 1.25 * float(smooth01(a / 0.10 + 0.25))
        if amp < 0.02:
            continue
        wd = (7 + 26 * u) * sc
        wl = (12 + 40 * u) * sc
        for m, pts, wv, val in ((dark, pc, wd, amp), (light, po, wl, amp), (light, pi, wl * 0.6, amp * 0.5)):
            p0 = np.round((pts[k] - off) * sc * 16).astype(np.int32)
            p1 = np.round((pts[k + 1] - off) * sc * 16).astype(np.int32)
            cv2.line(m, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), float(val), max(1, int(round(wv))),
                     cv2.LINE_AA, shift=4)
    dark = cv2.GaussianBlur(dark, (0, 0), 2.0)
    light = cv2.GaussianBlur(light, (0, 0), 2.6)
    full = (int(X1 - X0), int(Y1 - Y0))
    dark = cv2.resize(dark, full, interpolation=cv2.INTER_LINEAR)
    light = cv2.resize(light, full, interpolation=cv2.INTER_LINEAR)
    pen.lift(mask=(light, X0, Y0), amt=0.62, seed=(650, 1), soft=1.0)
    pen.fill(mask=(dark, X0, Y0), color='bean_d', tone=0.85, seed=(650, 2), edge=1.0, rim=0.0, bloom=0.0, rough=0.06)


# ================================================================= 红豆
def _bean_specs():
    """汤面上的豆：(r, th0, rx, ry, rot0, depth, id)。th0 是 t=0 的角度。那颗豆附近整段镜头都留出一圈。"""
    r = rng(700)
    out = []
    ts = np.linspace(T0, T1, 9)
    kp = np.float32([key_pos(x) for x in ts])
    for _ in range(4000):
        if len(out) >= 175:
            break
        rr = math.sqrt(r.uniform(0.0, 0.96))
        th = r.uniform(0, 2 * math.pi)
        if rr < 0.30 and r.random() < 0.6:
            continue
        p = polar(rr, th + omega(rr) * ts)
        if np.min(np.hypot(p[:, 0] - kp[:, 0], p[:, 1] - kp[:, 1])) < 105:
            continue
        rx = r.uniform(17.0, 21.5)
        depth = r.random() ** 1.5
        out.append((rr, th, rx, rx * r.uniform(0.60, 0.68), r.uniform(0, 180), depth, len(out)))
    return out


BEANS = _bean_specs()


def bean_at(spec, t):
    rr, th0, rx, ry, rot0, depth, i = spec
    th = th0 + float(omega(rr)) * t
    p = polar(rr, th)
    rot = rot0 + math.degrees(th) * 0.6          # 豆子顺着流向慢慢转
    bob = 1.5 * math.sin(t * 2.3 + i)
    return float(p[0]), float(p[1] + bob), rot


def beans(pen, t):
    for spec in BEANS:
        x, y, rot = bean_at(spec, t)
        rr, th0, rx, ry, rot0, depth, i = spec
        if not (-40 < x < W + 40 and -40 < y < H + 40):
            continue
        if depth > 0.55:
            # 沉在汤里的：一团更深的红，没有高光
            pen.dot(x, y, rx * 0.95, ry * 0.95, color='bean_d', tone=0.5 + 0.25 * (1 - depth), seed=(710, i),
                    rot=rot, shine=False, soft=1.6)
            continue
        pen.dot(x, y, rx, ry, color='bean', tone=1.1, seed=(730, i), rot=rot, shadow=True)
        if i % 3 == 0:
            # 豆脐：一道小小的白
            a = math.radians(rot)
            ca, sa = math.cos(a), math.sin(a)
            cx, cy = x + 0.52 * ry * sa, y - 0.52 * ry * ca
            pen.line(P([(cx - 0.3 * rx * ca, cy - 0.3 * rx * sa), (cx + 0.3 * rx * ca, cy + 0.3 * rx * sa)]),
                     3.0, tone=0.75, color='snow', seed=(740, i), role='detail', taper=(0.3, 0.3))


# ---------------------------------------------------------------- 那颗裂开的豆（伤口）
def crack_open(t):
    if t < T_CRACK:
        return 0.0
    u = (t - T_CRACK) / T_OPEN
    if u < 1.0:
        return float(ease_out(u)) * (1.0 + 0.10 * math.sin(math.pi * u))
    return 1.0 + 0.10 * clamp((t - T_CRACK - T_OPEN) / 1.4)


def key_bean(pen, t):
    """那颗豆：豆皮沿上沿裂开，两片豆皮往两头卷回去，米白的豆芯从裂口鼓出来（不是对称的一条缝）。"""
    x, y = key_pos(t)
    o = crack_open(t)
    swell = 1.0 + 0.06 * float(smooth01((t - T_SWELL) / 0.6))
    rx, ry = KEY_RX * swell, KEY_RY * swell
    jig = 0.0
    if T_SWELL < t < T_CRACK + 0.15:
        jig = rng(760, int(t * 12)).uniform(-2.0, 2.0)          # 滚汤里轻轻地颤
    rot = math.radians(KEY_ROT + jig)
    ca, sa = math.cos(rot), math.sin(rot)

    def L2S(u, v):
        u = np.asarray(u, np.float64)
        v = np.asarray(v, np.float64)
        return np.stack([x + u * ca - v * sa, y + u * sa + v * ca], -1).astype(np.float32)

    Lc = 0.86 * rx

    def vtop(u):
        return -ry * np.sqrt(np.clip(1.0 - (np.asarray(u, np.float64) / rx) ** 2, 0, 1))

    def bulge(u):
        return np.clip(1.0 - (np.asarray(u, np.float64) / Lc) ** 2, 0, 1)

    def crack(u):
        return vtop(u) * (1.0 - 0.62 * bulge(u))

    def outline_arc(d0, d1, n):
        aa = np.radians(np.linspace(d0, d1, n))
        uo = rx * np.cos(aa)
        so = np.sin(aa)
        vo = ry * so * (1.0 - 0.13 * np.clip(so, 0, 1) ** 4)       # 下边（豆脐那边）略平，像肾形
        return uo, vo

    a_end = math.degrees(math.acos(Lc / rx))          # 裂缝两端在上沿轮廓上的角度：360-a_end / 180+a_end
    us = np.linspace(-Lc, Lc, 29)
    cr = L2S(us, crack(us))
    ub, vb = outline_arc(360 - a_end, 540 + a_end, 44)                  # 右端 → 下边 → 左端
    body = np.vstack([cr, L2S(ub, vb)])
    full = L2S(*outline_arc(0, 360, 72))
    deg = math.degrees(rot)
    with pen.group('key_bean', boil=0.35):
        pen.shade(ell(x + 6, y + 9, rx * 1.05, ry * 0.95, n=24, rot=deg), amount=0.6, seed=761, color='bean_d',
                  soft=4.0)
        if o <= 0.01:
            pen.cover(full, seed=762, feather=0.8)
            pen.fill(full, 'bean', seed=770, tone=1.05, rim=0.25)
        else:
            oc = min(o, 1.0)
            # 豆芯：米白，从裂口鼓出来（比原来的轮廓还高一点），中间一道两瓣之间的细缝
            top_c = crack(us) - o * 1.05 * ry * bulge(us) ** 0.8
            core = np.vstack([L2S(us, crack(us) + 0.06 * ry), L2S(us[::-1], top_c[::-1])])
            pen.cover([body, core], seed=762, feather=0.8)
            pen.fill(body, 'bean', seed=770, tone=1.05, rim=0.25)
            pen.fill(core, 'enamel', seed=763, tone=0.07, rim=0.4)
            pen.shade(np.vstack([L2S(us, crack(us) + 0.06 * ry),
                                 L2S(us[::-1], (crack(us) - 0.35 * o * ry * bulge(us))[::-1])]),
                      amount=0.20, seed=764, soft=2.0, hatch=False)
            mid = (crack(us) + top_c) / 2
            pen.line(L2S(us[6:-6], mid[6:-6]), 1.6, tone=0.35 * oc, seed=765, role='feature', taper=(0.4, 0.4))
            pen.line(L2S(us, top_c), 1.8, tone=0.30, seed=766, role='detail', taper=(0.2, 0.2))
            rr_ = rng(767)
            for k in range(5):
                uu = rr_.uniform(-0.55, 0.55) * Lc
                vv = float(crack(uu)) - rr_.uniform(0.2, 0.7) * o * 1.05 * ry * float(bulge(uu)) ** 0.8
                p = L2S([uu], [vv])[0]
                pen.dot(p[0], p[1], 1.2, 1.0, color='ink', tone=0.18, seed=(768, k))
            # 两片豆皮往两头卷回去（裂口越开，卷得越靠两端）
            uo = Lc * (0.10 + 0.55 * oc)
            for k, (ua, ub_) in enumerate(((-Lc, -uo), (uo, Lc))):
                uu = np.linspace(ua, ub_, 10)
                lift = 0.25 * o * ry * bulge(uu)
                flap = np.vstack([L2S(uu, vtop(uu) - lift), L2S(uu[::-1], (crack(uu) - lift)[::-1])])
                pen.cover(flap, seed=(769, k), feather=0.6)
                pen.fill(flap, 'bean', seed=(771, k), tone=1.0, rim=0.3)
                tip = ub_ if k == 0 else ua
                e = L2S([tip, tip], [float(vtop(tip) - 0.25 * o * ry * bulge(tip)),
                                     float(crack(tip) - 0.25 * o * ry * bulge(tip))])
                pen.line(e, 3.2, tone=1.0, color='bean_d', seed=(775, k), role='detail', taper=(0.2, 0.2))
                pen.line(L2S(uu, vtop(uu) - lift), 2.6, tone=0.9, color='bean_d', seed=(776, k), role='detail',
                         taper=(0.2, 0.2))
        # 暗部（下半）+ 高光
        uu = np.linspace(-rx * 0.92, rx * 0.92, 14)
        lo = L2S(uu, ry * np.sqrt(np.clip(1 - (uu / rx) ** 2, 0, 1)) * 0.86)
        pen.shade(np.vstack([L2S(uu, 0.30 * ry * np.sqrt(np.clip(1 - (uu / rx) ** 2, 0, 1))), lo[::-1]]),
                  amount=0.5, seed=772, color='bean_d', soft=3.0)
        hy = 0.0 if o > 0.01 else 1.0
        hl = L2S(np.linspace(-0.62 * rx, 0.1 * rx, 8), np.full(8, -0.18 * ry - 0.45 * ry * hy))
        pen.lift(tube(hl, [1.5, 5.0, 3.5, 1.0])[0], amt=0.75, seed=773, soft=1.0)
        # 轮廓（深红）：没裂之前是一整圈；裂开后只剩下面一半
        if o <= 0.01:
            pen.line(full, 3.2, tone=0.9, color='bean_d', seed=774, closed=True, taper=(0, 0), role='detail')
        else:
            pen.line(L2S(ub, vb), 3.2, tone=0.9, color='bean_d', seed=774, taper=(0.1, 0.1), role='detail')
            # 裂口下沿：参差的深红
            jag = crack(us) + 0.05 * ry * np.sin(us * 0.9 + 1.0) * bulge(us)
            pen.line(L2S(us, jag), 2.8, tone=1.0, color='bean_d', seed=777, role='detail', taper=(0.2, 0.2))
        # 豆脐（下边一道白）
        pen.line(L2S(np.linspace(-0.30 * rx, 0.30 * rx, 5), np.full(5, 0.70 * ry)), 3.4, tone=0.8,
                 color='snow', seed=778, role='detail', taper=(0.3, 0.3))
        if o <= 0.01 and t >= T_HAIR:
            # 细缝：从中间往两头裂
            k = float(ease_out((t - T_HAIR) / (T_CRACK - T_HAIR)))
            us3 = np.linspace(-Lc * 0.9 * k, Lc * 0.9 * k, 11)
            pen.line(L2S(us3, crack(us3)), 2.2, tone=1.0, color='ink', seed=779, taper=(0.4, 0.4), role='feature')


def crack_ripple(pen, t):
    """裂开那一下，豆子周围荡开一小圈涟漪。"""
    a = t - T_CRACK
    if not (0.0 <= a < 0.9):
        return
    x, y = key_pos(t)
    u = a / 0.9
    rr = 48 + 120 * ease_out(u)
    k = SRY / SRX
    amt = 0.55 * (1 - u) ** 1.3
    wv = 5 + 6 * u
    outer = ell(x, y, rr + wv, (rr + wv) * k, n=64)
    inner = ell(x, y, rr - wv, (rr - wv) * k, n=64)
    pen.lift(outer, amt=amt, seed=780, soft=2.5, holes=[inner])


# ---------------------------------------------------------------- 气泡
def bubbles(pen, t):
    kx, ky = key_pos(t)
    for k in range(11):
        r0 = rng(800, k)
        per = r0.uniform(1.0, 1.7)
        ph = r0.uniform(0, per)
        cyc = math.floor((t + ph) / per)
        u = ((t + ph) % per) / per
        rr_ = rng(801, k, cyc)
        rr = rr_.uniform(0.28, 0.9)
        th = rr_.uniform(0, 2 * math.pi)
        rb = rr_.uniform(7, 17)
        x, y = polar(rr, th + float(omega(rr)) * t)
        if math.hypot(x - kx, y - ky) < 110:
            continue
        seed = (810, k, cyc)
        if u < 0.72:
            g = float(ease_out(u / 0.72))
            rad = max(1.5, rb * g)
            pen.dot(x + 0.15 * rad, y + 0.3 * rad, rad, rad * 0.8, color='bean_d', tone=0.7, seed=seed, shine=False)
            ring_o = ell(x, y, rad + 1.6, (rad + 1.6) * 0.82, n=24)
            ring_i = ell(x + 0.2 * rad, y + 0.15 * rad, max(0.5, rad - 1.6), max(0.5, rad - 2.2) * 0.82, n=24)
            pen.lift(ring_o, amt=0.6, seed=seed + (1,), soft=0.6, holes=[ring_i])
            pen.lift(ell(x - 0.35 * rad, y - 0.35 * rad, 0.28 * rad + 0.6, 0.2 * rad + 0.5, n=8), amt=0.9,
                     seed=seed + (2,), soft=0.4)
        else:
            q = (u - 0.72) / 0.28
            rad = rb * (1.0 + 1.3 * ease_out(q))
            amt = 0.5 * (1 - q) ** 1.2
            if amt < 0.03:
                continue
            ring_o = ell(x, y, rad + 2.0, (rad + 2.0) * 0.8, n=28)
            ring_i = ell(x, y, max(0.5, rad - 1.2), max(0.5, rad - 1.2) * 0.8, n=28)
            pen.lift(ring_o, amt=amt, seed=seed + (3,), soft=0.8, holes=[ring_i])
            if q < 0.5:
                for j in range(3):
                    aa = 2 * math.pi * j / 3 + k
                    dd = rad * (0.6 + 0.8 * q)
                    pen.dot(x + dd * math.cos(aa), y + dd * 0.8 * math.sin(aa) - 6 * math.sin(math.pi * q * 2), 2.0,
                            color='snow', tone=0.0, seed=seed + (5 + j,))


# ================================================================= 锅沿（一圈浓墨）
def lip(pen):
    s = 900
    ring = ering(RC, LIP_OUT, LIP_IN)
    pen.cover(ring, seed=s, feather=0.8)
    pen.fill(ring, POT_COL, seed=s + 1, c_dens=0.78, c_fade=False, broad=False, rim=0.2, grad_auto=False)
    # 卷边上的高光（左上、光从窗来）
    mid = ((LIP_IN[0] + LIP_OUT[0]) / 2, (LIP_IN[1] + LIP_OUT[1]) / 2)
    pen.lift(tube(ell(RC[0], RC[1], mid[0], mid[1], 150, 215, 20), [3, 11, 13, 4])[0], amt=0.8, seed=s + 2,
             soft=1.5, dry=0.5, streak=0.6)
    pen.lift(tube(ell(RC[0], RC[1], mid[0], mid[1], 226, 252, 8), [2, 7, 2])[0], amt=0.65, seed=s + 3, soft=1.0)
    pen.lift(tube(ell(RC[0], RC[1], mid[0] - 4, mid[1] - 4, 60, 110, 14), [2, 6, 2])[0], amt=0.35, seed=s + 10,
             soft=1.5, dry=0.6, streak=0.5)
    # 内沿：近处浓、粗；远处淡
    pen.line(ell(RC[0], RC[1], LIP_IN[0], LIP_IN[1], 8, 172, 60), 15, tone=0.98, seed=s + 4, taper=(0.06, 0.10),
             head=0.5, lift=0.25, dry=0.3, dry_from=0.75, pool=0.2)
    pen.line(ell(RC[0], RC[1], LIP_IN[0], LIP_IN[1], 160, 205, 20), 11, tone=0.9, seed=s + 5, taper=(0.1, 0.2),
             head=0.3, dry=0.5, dry_from=0.5)
    pen.line(ell(RC[0], RC[1], LIP_IN[0], LIP_IN[1], -25, 20, 20), 11, tone=0.9, seed=s + 6, taper=(0.1, 0.2),
             head=0.3, dry=0.5, dry_from=0.5)
    # 外沿
    pen.line(ell(RC[0], RC[1], LIP_OUT[0], LIP_OUT[1], 12, 168, 60), 9, tone=0.9, seed=s + 7, taper=(0.06, 0.12),
             head=0.3, dry=0.45, dry_from=0.6)
    pen.line(ell(RC[0], RC[1], LIP_OUT[0], LIP_OUT[1], 160, 200, 16), 7, tone=0.8, seed=s + 8, taper=(0.1, 0.2),
             dry=0.5, dry_from=0.5)
    pen.line(ell(RC[0], RC[1], LIP_OUT[0], LIP_OUT[1], -20, 22, 16), 7, tone=0.8, seed=s + 9, taper=(0.1, 0.2),
             dry=0.5, dry_from=0.5)


# ================================================================= 木勺
HAND_C = (-380.0, -300.0)


def spoon_geom(t):
    """勺柄：入汤点 E（跟着勺头画圈）→ 她的手 Hd（画外左上，跟着画小圈）。→ (E, 勺柄方向, 法向, 运动方向)。"""
    E = c2s(spoon_c(t))
    E2 = c2s(spoon_c(t + 0.05))
    Hd = np.float32(HAND_C) + 0.30 * (E - np.float32(SC))
    dv = (Hd - E) / (np.hypot(*(Hd - E)) + 1e-6)
    nv = np.float32([-dv[1], dv[0]])
    mv = (E2 - E) / (np.hypot(*(E2 - E)) + 1e-6)
    return np.float32(E), dv.astype(np.float32), nv, mv.astype(np.float32)


def spoon_shadow(pen, t):
    E, dv, nv, mv = spoon_geom(t)
    off = np.float32([34, 42])
    path = [E + off * 0.3, E + dv * 260 + off, E + dv * 700 + off * 1.5]
    pen.shade(tube(path, [56, 70, 84])[0], amount=0.6, seed=950, color='bean_d', soft=12.0)


def spoon(pen, t):
    s = 960
    E, dv, nv, mv = spoon_geom(t)
    mn = np.float32([-mv[1], mv[0]])
    path = [E - dv * 6, E + dv * 300 + nv * 7, E + dv * 760 + nv * 9, E + dv * 1200]
    poly, L, R = tube(path, [50, 60, 80, 98])
    C = spline(path, 4.0)
    with pen.group('spoon', boil=0.6):
        # 汤下面隐约的勺颈和勺头（往入汤点的反方向斜下去）
        pen.fill(tube([E, E - dv * 70, E - dv * 150], [44, 52, 30])[0], 'bean_d', seed=s - 2, tone=0.30, rim=0.0,
                 soft=6.0)
        pen.fill(ell(*(E - dv * 210), 70, 50, n=24, rot=math.degrees(math.atan2(dv[1], dv[0]))), 'bean_d',
                 seed=s - 1, tone=0.22, rim=0.0, soft=10.0)
        # 船头浪：勺子往前推开的两道浅色浪
        for j, sg in enumerate((-1, 1)):
            p0 = E + mv * 32 + mn * sg * 24
            pts = [p0, p0 - mv * 40 + mn * sg * 40, p0 - mv * 110 + mn * sg * 62]
            pen.lift(tube(pts, [2, 8, 2])[0], amt=0.5, seed=(s, 1, j), soft=2.0)
        pen.cover(poly, seed=s + 2, feather=0.8)
        pen.fill(poly, 'wood', seed=s + 3, c_dens=0.30, c_fade=False, broad=False, grad_auto=False, streak=0.5)
        # 圆柄：一侧压暗（排线顺着柄），另一侧一道光
        side = np.vstack([L, (C + nv * 4)[::-1]])
        pen.shade(side, amount=0.45, seed=s + 5, angle=math.degrees(math.atan2(dv[1], dv[0])), spacing=6.0)
        pen.lift(tube([E + dv * 120 - nv * 12, E + dv * 520 - nv * 13, E + dv * 1000 - nv * 18], [2, 7, 4])[0],
                 amt=0.65, seed=s + 8, soft=1.5, dry=0.6, streak=0.5)
        # 木纹（微微波动的细线）
        for k, o in enumerate((-0.30, -0.02, 0.22)):
            a0, a1 = 110 + 110 * k, 620 + 160 * k
            q = np.linspace(0, 1, 6)
            pts = [E + dv * (a0 + (a1 - a0) * u) + nv * (o * (50 + 40 * u) + 3 * math.sin(7 * u + k)) for u in q]
            pen.line(P(pts), 2.0, tone=0.34, color='wood_d', seed=s + 10 + k, role='detail', taper=(0.3, 0.3),
                     dry=0.6, dry_from=0.2)
        # 浸过汤的那一截：染成红，越往上越淡；末端没进汤里（不画切口）
        wet = tube([E - dv * 8, E + dv * 80, E + dv * 170], [54, 56, 58])[0]
        pen.fill(wet, 'soup', seed=s + 4, tone=0.55, rim=0.3, rgrad=(E[0], E[1], 30, 170, 1.0, 0.0))
        sub = tube([E - dv * 14, E + dv * 10, E + dv * 40], [60, 58, 56])[0]
        pen.fill(sub, 'soup', seed=s + 20, tone=1.15, rim=0.0, soft=4.0, rgrad=(E[0], E[1], 0, 42, 1.0, 0.0))
        pen.line(R[::6], 7.0, tone=0.92, seed=s + 6, taper=(0.15, 0.1), head=0.4, lift=0.2, dry=0.35, dry_from=0.7)
        pen.line(L[::6], 5.0, tone=0.8, seed=s + 7, taper=(0.15, 0.1), head=0.3, dry=0.45, dry_from=0.6)
        # 水线两侧：汤被柄带起来的两道小弯月（湿亮）
        for j, sg in enumerate((-1, 1)):
            c0 = E + dv * 18 + nv * sg * 34
            arc_ = [c0 - dv * 20 + nv * sg * 2, c0, c0 + dv * 18 - nv * sg * 4]
            pen.lift(tube(arc_, [1.5, 5, 1.5])[0], amt=0.7, seed=(s, 22, j), soft=1.0)


# ================================================================= 热气
def steam(pen, t):
    with pen.group('steam', boil=0.8):
        per = 3.4
        for k in range(8):
            age = ((t + k * per / 8) % per) / per
            a = math.sin(math.pi * age) ** 1.2
            if a < 0.04:
                continue
            cyc = math.floor((t + k * per / 8) / per)
            r = rng(1000, k, cyc)
            bx = r.uniform(150, 1750)
            yb = r.uniform(360, 620) - age * 420
            Ls = 240 + 220 * age
            ys = np.linspace(yb, yb - Ls, 9)
            ph = r.uniform(0, 6.28)
            curl = r.uniform(22, 50) * (0.5 + age)
            xs = bx + curl * np.sin((ys - yb) * 0.012 + ph + t * 0.9) + (yb - ys) * 0.12 + 40 * age
            path = np.stack([xs, ys], 1).astype(np.float32)
            w = 30 + 60 * age
            pen.lift(tube(path, [w * 0.35, w, w * 0.8, w * 0.3])[0], amt=0.62 * a, seed=(1010, k, cyc), soft=12.0)
            pen.lift(tube(path, [w * 0.08, w * 0.25, w * 0.2, w * 0.05])[0], amt=0.55 * a, seed=(1015, k, cyc),
                     soft=4.0)
            pen.line(path, w * 0.22, tone=0.10 * a, color='metal', seed=(1020, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.6, dry_from=0.1)


def key_steam(pen, t):
    """「口」：从裂口冒起的一缕热气（比别的热气更清楚），一边升一边卷，越往上越宽越淡。"""
    a = t - T_STEAM
    if a < 0:
        return
    x, y = key_pos(t)
    grow = float(ease_out(a / 0.8))
    Ls = 40 + 360 * grow
    n = 16
    ss = np.linspace(0, 1, n)
    ys = y - 14 - Ls * ss - 50 * a * ss
    xs = x + 2 + (16 + 70 * ss) * np.sin(ss * 5.0 - a * 2.6) * ss ** 0.7 + 30 * ss * ss
    path = np.stack([xs, ys], 1).astype(np.float32)
    fade = 1.0 - 0.3 * clamp((a - 0.6) / 0.6)
    with pen.group('key_steam', boil=0.6):
        pen.lift(tube(path, [8, 24, 42, 58, 70, 66, 48])[0], amt=0.72 * fade, seed=1050, soft=10.0)
        pen.lift(tube(path[:12], [3, 9, 15, 16, 11, 4])[0], amt=0.85 * fade, seed=1051, soft=3.0)
        pen.line(path[:13], 3.0, tone=0.14 * fade, color='metal', seed=1052, taper=(0.2, 0.5), role='detail',
                 dry=0.5, dry_from=0.2)


# ================================================================= 场景
def view_params(t, zoom=ZOOM):
    u = clamp((t - T0) / (T1 - T0))
    s = 1.0 + zoom * u
    kx, ky = KEY0
    return s, kx * (1 - s), ky * (1 - s)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    s, ox, oy = view_params(t, float(kw.get('zoom', ZOOM)))
    with pen.view(s, ox, oy):
        with pen.group('bg', boil=BG_BOIL):
            background(pen)
        with pen.group('soup', boil=0.5, bleed=0.6):
            soup_base(pen, t)
            wake(pen, t)
        with pen.group('beans', boil=0.4):
            beans(pen, t)
            bubbles(pen, t)
            crack_ripple(pen, t)
            spoon_shadow(pen, t)
        key_bean(pen, t)
        with pen.group('lip', boil=BG_BOIL):
            lip(pen)
        spoon(pen, t)
        steam(pen, t)
        key_steam(pen, t)
