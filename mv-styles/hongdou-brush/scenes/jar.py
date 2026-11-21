# -*- coding: utf-8 -*-
"""
第 12 镜「第十句一句示例歌词」（成片 40.83–45.14，C 水墨；红豆是唯一的红）。
台面中近景（镜头从斜上方约 50° 往下看）→ 掌心特写。
她的右手掌心朝上摊在台面上；左手握着装红豆的玻璃罐（盖子已经拧下来扣在台面上），罐里只剩最后一颗。
40.83 罐子还立着，那颗豆在罐底；41.0 她把罐子慢慢倒过来，对着掌心轻轻抖；豆顺着罐壁滑到罐口，
“一”（42.05）从罐口掉出来，“切”落进掌心、弹一下、滚到掌心中央停住；
42.9 她又抖了一下——什么都没有了；“有尽头”（43.25–44.07）罐子空空的（罐壁上什么都没有），慢慢抬起来；
镜头从 42.95 起慢慢推近到掌心特写（pen.view 推），她的手指一点点收拢，把那颗豆护在掌心里。
背景：瓷砖墙、木台面、扣着的罐盖、一只空碗、冒着热气的水壶（热气在动）、叠好的毛巾、一把木勺；灯光里有浮尘。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒，默认 pen.t）；zoom 推近的终点倍数（默认 ZOOM）
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
from core import W, H, densify, ell, bez, spline, tube, rng, clamp, ease_io, ease_out, ease_in, smooth01
import hands

T0, T1 = 40.83, 45.14
T_TILT0, T_TILT1 = 41.00, 41.75       # 倒罐
T_SLIDE0, T_RIM = 41.42, 42.00        # 豆顺着罐壁滑到罐口
T_OUT = 42.05                         # “一”：掉出罐口
T_LAND = 42.28                        # 落进掌心
T_REST = 42.65                        # “切”：在掌心中央停住
T_SHAKE2 = (42.88, 43.25)             # 再抖一下：空了
T_PUSH0 = 42.95                       # 推镜开始
ZOOM = 2.6
PHI_MAX = 128.0                       # 倒到多斜（度；90 = 横着）
BG_BOIL = 0.4

# ---------------------------------------------------------------- 布局（场景坐标）
ELEV = math.radians(50.0)
UP = np.array([0.0, -math.cos(ELEV), math.sin(ELEV)])        # 世界“上”（相机坐标）
RIGHT = np.array([1.0, 0.0, 0.0])
FRONT = np.array([0.0, math.sin(ELEV), math.cos(ELEV)])      # 水平指向镜头
DOWN = -UP
FS = math.cos(ELEV)                   # 竖直方向的缩短
EY = math.sin(ELEV)                   # 水平圆的椭圆扁率
BACK_Y = 330                          # 台面后沿（墙脚）
PALM = dict(x=1180.0, y=700.0, rot=58.0, size=330.0, yaw=-12.0, tilt=30.0)
L_JAR = 330.0                         # 握罐那只手的手长
JAR_R = 0.30                          # 罐身半径（单位：手长）
JAR_H = 236.0                         # 罐高（像素，沿轴）
JAR_FG = 0.42                         # 手握在离罐底多远（占罐高）
G0 = np.array([1118.0, 428.0])        # 握点（罐轴上）
BEAN_R = 0.042                        # 红豆半径（手长）
LAND_B = (0.035, 0.085)               # 落在掌心的位置（掌面局部，单位 L）
REST_B = (0.0, 0.0)
TARGET = (968.0, 470.0)               # 推近后掌心在画面上的位置
KETTLE = dict(cx=1660.0, base=372.0, rx=118.0)


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def nz(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


# ================================================================= 表演（时间 → 姿态）
def jar_tilt(t):
    """罐子倾角（度）+ 抖动 → (phi, 沿轴的小位移, 握点平移)。"""
    phi = PHI_MAX * ease_io((t - T_TILT0) / (T_TILT1 - T_TILT0))
    shift = 0.0
    lift = np.zeros(2)
    # 第一次抖：三下（倒过来以后），越抖越轻
    if 41.55 < t < 42.12:
        u = (t - 41.55) / 0.57
        env = math.sin(math.pi * u)
        phi += 4.5 * env * math.sin(2 * math.pi * 5.2 * (t - 41.55))
        shift = 7.0 * env * math.sin(2 * math.pi * 5.2 * (t - 41.55) + 0.8)
    # 第二次抖：空了
    a, b = T_SHAKE2
    if a < t < b:
        u = (t - a) / (b - a)
        env = math.sin(math.pi * u)
        phi += 5.5 * env * math.sin(2 * math.pi * 5.6 * (t - a))
        shift = 8.0 * env * math.sin(2 * math.pi * 5.6 * (t - a) + 0.8)
    # 之后慢慢抬起来、往回收一点
    k = ease_io((t - 43.30) / 1.8)
    phi -= 34.0 * k
    lift = np.array([-70.0, -90.0]) * k
    # 一开始拿着的时候手微微晃
    phi += 1.2 * math.sin(2 * math.pi * 0.7 * t)
    return phi, shift, lift


def jar_geom(t):
    phi, shift, lift = jar_tilt(t)
    f = math.radians(phi)
    A = nz(math.cos(f) * UP + math.sin(f) * RIGHT)
    Lv = math.cos(f) * (-RIGHT) + math.sin(f) * UP
    G = G0 + lift + A[:2] * shift
    R = JAR_R * L_JAR
    base = G - A[:2] * JAR_H * JAR_FG
    mouth = G + A[:2] * JAR_H * (1 - JAR_FG)
    a2 = A[:2] / (np.linalg.norm(A[:2]) + 1e-9)
    n2 = np.array([-a2[1], a2[0]])
    ry = max(1.5, R * abs(A[2]))
    ang = math.degrees(math.atan2(n2[1], n2[0]))
    psi = math.radians(40.0 - 80.0 * clamp(phi / PHI_MAX, -0.2, 1.2))     # 手绕罐身转：小臂始终伸向左上方
    back = nz(math.cos(psi) * Lv + math.sin(psi) * FRONT)
    # 轴向在罐内的“最低”方向（重力在与轴垂直的平面上的分量）
    dn = DOWN - np.dot(DOWN, A) * A
    if np.linalg.norm(dn) < 0.15:
        dn = dn + FRONT * 0.3
    dn = nz(dn)
    return dict(phi=phi, A=A, G=G, R=R, base=base, mouth=mouth, a2=a2, n2=n2, ry=ry, ang=ang, back=back, dn=dn,
                Lv=Lv, lift=float(np.linalg.norm(lift)))


def end_ellipse(c, g, scale=1.0, a0=0.0, a1=360.0, n=48):
    return ell(c[0], c[1], g['R'] * scale, g['ry'] * scale, a0, a1, n, rot=g['ang'])


def jar_sil(g):
    pts = np.vstack([end_ellipse(g['base'], g), end_ellipse(g['mouth'], g)])
    return cv2.convexHull(pts.astype(np.float32)).reshape(-1, 2).astype(np.float32)


def axis_pt(g, u, lat=0.0, dn=None):
    """罐轴上离罐底 u（像素）处，再沿“最低方向”偏 lat 像素 → 画面坐标。"""
    p = g['base'] + g['A'][:2] * u
    if lat:
        d = g['dn'] if dn is None else dn
        p = p + d[:2] * lat
    return p


def bean_state(t, g):
    """→ ('jar', 画面坐标) / ('fall', 画面坐标) / ('palm', (bx, by)) / None。"""
    rb = BEAN_R * L_JAR
    u0, u1 = rb + 12.0, JAR_H - rb * 0.7
    lat = g['R'] - rb - 6.0
    if t < T_OUT:
        k = ease_in(clamp((t - T_SLIDE0) / (T_RIM - T_SLIDE0)))
        u = u0 + (u1 - u0) * k
        # 罐还立着的时候：躺在罐底靠前一点，随手轻轻晃
        if t < T_SLIDE0:
            wob = 3.0 * math.sin(2 * math.pi * 1.3 * t)
            k0 = ease_io((t - T_TILT0) / (T_SLIDE0 - T_TILT0))
            far = axis_pt(g, u0) - FRONT[:2] * lat * 0.55          # 立着时：躺在罐底靠里的一边（不被手指挡住）
            low = axis_pt(g, u0, lat)
            return 'jar', far * (1 - k0) + low * k0 + g['n2'] * wob
        return 'jar', axis_pt(g, u, lat)
    if t < T_LAND:
        # 从罐口边上落下来（抛物线）落到掌心
        p0 = axis_pt(jar_geom(T_OUT), u1, lat)
        p1 = land_point()
        k = (t - T_OUT) / (T_LAND - T_OUT)
        x = p0[0] + (p1[0] - p0[0]) * k
        y = p0[1] + (p1[1] - p0[1]) * k * k
        return 'fall', np.array([x, y])
    if t < T_REST:
        k = ease_out((t - T_LAND) / (T_REST - T_LAND))
        bx = LAND_B[0] + (REST_B[0] - LAND_B[0]) * k
        by = LAND_B[1] + (REST_B[1] - LAND_B[1]) * k
        hop = 0.0
        if t < T_LAND + 0.16:
            hop = math.sin(math.pi * (t - T_LAND) / 0.16) * 0.05
        return 'palm', (bx, by, hop)
    return 'palm', (REST_B[0], REST_B[1], 0.0)


def palm_cup(t):
    return 0.5 * ease_io((t - 43.55) / 1.5)


_LAND = {}


def land_point():
    if 'p' not in _LAND:
        dummy = core.Pen('C', 0)
        info = hands.palm_up(dummy, PALM['x'], PALM['y'], rot=PALM['rot'], size=PALM['size'], tilt=PALM['tilt'],
                             yaw=PALM['yaw'], bean=LAND_B, bean_r=BEAN_R, seed=('palm', 12))
        _LAND['p'] = np.array(info['bean'])
        info = hands.palm_up(dummy, PALM['x'], PALM['y'], rot=PALM['rot'], size=PALM['size'], tilt=PALM['tilt'],
                             yaw=PALM['yaw'], bean=REST_B, bean_r=BEAN_R, seed=('palm', 12))
        _LAND['rest'] = np.array(info['bean'])
        _LAND['sil'] = info['sil']
    return _LAND['p']


def view_params(t, zoom=ZOOM):
    u = ease_io((t - T_PUSH0) / (T1 - T_PUSH0))
    s = 1.0 + (zoom - 1.0) * u
    land_point()
    p = _LAND['rest']
    c = np.array([p[0], p[1]]) * (1 - u) + np.array(TARGET) * u
    return s, float(c[0] - s * p[0]), float(c[1] - s * p[1])


# ================================================================= 背景
def wall(pen):
    s = 100
    q = P([(-40, -40), (W + 40, -40), (W + 40, BACK_Y + 4), (-40, BACK_Y + 4)])
    pen.fill(q, 'wall', seed=s, tone=0.20, rgrad=(620, 40, 200, 1500, 0.4, 1.1), c_fade=False, broad=False,
             var=0.10, cell=90.0)
    # 瓷砖：竖直墙面被俯视缩短，砖缝淡墨
    tw, th = 128.0, 128.0 * FS
    r = rng(s, 1)
    for k in range(int(BACK_Y / th) + 2):
        y = BACK_Y - k * th
        pen.line(D([(-30, y + r.uniform(-1, 1)), (W + 30, y + r.uniform(-1, 1))], 60), 2.2, tone=0.34,
                 seed=(s, 2, k), role='detail', taper=(0.02, 0.02), boil=0.25)
        off = (k % 2) * tw * 0.5
        for j in range(17):
            x = -tw + off + j * tw
            pen.line(P([(x, y - 2), (x + 0.5, y - th + 2)]), 2.0, tone=0.30, seed=(s, 3, k, j), role='detail',
                     taper=(0.05, 0.05), boil=0.25)
    # 一块砖上的高光（灯）
    pen.lift(ell(560, 150, 160, 60, n=24), amt=0.35, seed=s + 4, soft=24.0)
    # 墙脚：台面后沿的一道影
    pen.shade(P([(-40, BACK_Y - 26), (W + 40, BACK_Y - 26), (W + 40, BACK_Y + 2), (-40, BACK_Y + 2)]),
              amount=0.25, seed=s + 5, soft=10.0, hatch=False, grad=(0, BACK_Y - 26, 0, BACK_Y, 0.0, 1.0))


def counter(pen):
    s = 200
    top = P([(-40, BACK_Y), (W + 40, BACK_Y), (W + 40, H + 40), (-40, H + 40)])
    pen.cover(top, seed=s)
    pen.fill(top, 'wood', seed=s + 1, tone=0.26, grad=(0, BACK_Y, 0, H, 0.75, 1.15), c_fade=False, broad=False,
             var=0.1)
    pen.hatch(top, angle=1.5, spacing=9, tone=0.16, color='wood_d', seed=s + 2, partial=0.45, bow=0.01)
    # 木板接缝（两道）、几处木节
    for k, y in enumerate((560, 905)):
        pen.line(D([(-40, y), (700, y - 2), (W + 40, y + 2)], 40), 4.5, tone=0.5, color='wood_d', seed=(s, 3, k),
                 taper=(0.02, 0.02), head=0.2, dry=0.5, dry_from=0.5)
    # 后沿：一道浓墨
    pen.line(D([(-40, BACK_Y), (800, BACK_Y - 2), (W + 40, BACK_Y + 1)], 40), 9, tone=0.85, color='wood_d',
             seed=s + 6, taper=(0.02, 0.05), head=0.4, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25)
    # 灯光落在台面上（水墨里是留白）
    pen.light(820, 560, 520, 230, amt=0.42, color='lamp', seed=s + 7)
    # 掌心那一块再亮一点（推近以后画面的中心）
    pen.light(PALM['x'] + 10, PALM['y'] - 10, 300, 200, amt=0.35, color='lamp', seed=s + 8)


def bowl(pen):
    """后面一只空碗（白瓷，碗口一道蓝边——水墨里是淡墨边）。"""
    s = 300
    cx, cy, rx = 560.0, 388.0, 92.0
    ry = rx * EY * 0.85
    hgt = 58.0
    pen.shade(ell(cx + 26, cy + hgt + 8, rx * 0.9, ry * 0.55, n=30), amount=0.35, seed=s, soft=10.0, hatch=False)
    sil = np.vstack([ell(cx, cy, rx, ry, 180, 360, 24), ell(cx, cy + hgt, rx * 0.5, ry * 0.42, 0, 180, 16)[::-1]])
    sil = np.vstack([ell(cx, cy, rx, ry, 180, 360, 24), P([(cx + rx, cy), (cx + rx * 0.8, cy + hgt * 0.65)]),
                     ell(cx, cy + hgt, rx * 0.5, ry * 0.42, 0, 180, 16), P([(cx - rx * 0.8, cy + hgt * 0.65)])])
    pen.cover(sil, seed=s + 1, feather=0.8)
    pen.fill(sil, 'enamel', seed=s + 2, tone=0.05)
    pen.shade(np.vstack([ell(cx, cy, rx, ry, 0, 100, 14), ell(cx, cy + hgt, rx * 0.5, ry * 0.42, 100, 0, 8)]),
              amount=0.3, seed=s + 3)
    inner = ell(cx, cy + 3, rx * 0.93, ry * 0.86, 0, 360, 36)
    pen.fill(inner, 'enamel', seed=s + 4, tone=0.10, rgrad=(cx - 20, cy - 4, 0, rx, 0.6, 1.4))
    pen.line(ell(cx, cy, rx, ry, 0, 360, 48), 4.0, tone=0.8, seed=s + 5, closed=True, taper=(0, 0))
    pen.line(ell(cx, cy + 6, rx * 0.97, ry * 0.9, 20, 160, 20), 3.2, tone=0.45, color='lampshade', seed=s + 6,
             role='detail', taper=(0.1, 0.1))
    pen.line(P([(cx - rx, cy), (cx - rx * 0.78, cy + hgt * 0.6), (cx - rx * 0.5, cy + hgt)]), 4.5, tone=0.85,
             seed=s + 8, taper=(0.1, 0.2), head=0.4)
    pen.line(P([(cx + rx, cy), (cx + rx * 0.78, cy + hgt * 0.6), (cx + rx * 0.5, cy + hgt)]), 3.0, tone=0.6,
             seed=s + 9, taper=(0.1, 0.3), head=0.2)
    pen.line(ell(cx, cy + hgt, rx * 0.5, ry * 0.42, 10, 170, 14), 3.4, tone=0.7, seed=s + 10, taper=(0.1, 0.1))


def kettle(pen):
    s = 400
    cx, base, rx = KETTLE['cx'], KETTLE['base'], KETTLE['rx']
    ry = rx * EY
    hgt = 150.0 * FS * 1.35
    top = base - hgt
    pen.shade(ell(cx + 40, base + 10, rx * 1.05, ry * 0.6, n=30), amount=0.4, seed=s, soft=12.0, hatch=False)
    body = np.vstack([ell(cx, base, rx, ry * 0.9, 0, 180, 24), ell(cx, top + 24, rx * 0.72, ry * 0.6, 180, 360, 20)])
    pen.cover(body, seed=s + 1, feather=0.8)
    pen.fill(body, 'metal', seed=s + 2, tone=0.30, grad=(cx - rx, 0, cx + rx, 0, 0.7, 1.25), c_fade=False)
    pen.shade(np.vstack([ell(cx, base, rx, ry * 0.9, 0, 70, 10), P([(cx + rx * 0.4, top + 30)])]), amount=0.3,
              seed=s + 3, angle=75)
    pen.lift(tube([(cx - rx * 0.55, base - 10), (cx - rx * 0.45, top + 60), (cx - rx * 0.3, top + 30)], [4, 10, 4])[0],
             amt=0.6, seed=s + 4, soft=2.0, dry=0.6, streak=0.5)
    pen.line(P([(cx - rx, base - 4), (cx - rx * 0.95, base - hgt * 0.5), (cx - rx * 0.72, top + 24)]), 6.5, tone=0.9,
             seed=s + 5, taper=(0.1, 0.2), head=0.5)
    pen.line(P([(cx + rx, base - 4), (cx + rx * 0.95, base - hgt * 0.5), (cx + rx * 0.72, top + 24)]), 4.0, tone=0.65,
             seed=s + 6, taper=(0.1, 0.3), head=0.2)
    pen.line(ell(cx, base, rx, ry * 0.9, 5, 175, 24), 5.5, tone=0.85, seed=s + 7, taper=(0.05, 0.1), head=0.4)
    lid = ell(cx, top + 24, rx * 0.72, ry * 0.6, 0, 360, 30)
    pen.fill(lid, 'metal', seed=s + 8, tone=0.22)
    pen.line(lid, 4.0, tone=0.8, seed=s + 9, closed=True, taper=(0, 0))
    pen.dot(cx, top + 14, 12, 8, color='ink', tone=0.9, seed=s + 10)
    # 提手（黑色胶木）
    pen.line(P([(cx - rx * 0.6, top + 22), (cx - rx * 0.45, top - 58), (cx + rx * 0.45, top - 58),
                (cx + rx * 0.6, top + 22)]), 11, tone=0.9, seed=s + 11, taper=(0.15, 0.15), head=0.5, lift=0.3,
             dry=0.4, dry_from=0.6)
    # 壶嘴（朝左）
    sp = spout_tip()
    pen.line(P([(cx - rx * 0.85, base - hgt * 0.45), (cx - rx * 1.25, base - hgt * 0.7), sp]), 16, tone=0.6,
             color='metal', seed=s + 12, taper=(0.05, 0.4), head=0.4)
    pen.line(P([(cx - rx * 0.85, base - hgt * 0.38), (cx - rx * 1.25, base - hgt * 0.62), sp + P([4, 8])]), 3.5,
             tone=0.85, seed=s + 13, taper=(0.1, 0.4))


def spout_tip():
    cx, base, rx = KETTLE['cx'], KETTLE['base'], KETTLE['rx']
    hgt = 150.0 * FS * 1.35
    return np.float32([cx - rx * 1.52, base - hgt * 1.02])


def lid(pen):
    """拧下来的罐盖，扣在台面上（木盖：一圈螺纹的边 + 顶面）。"""
    s = 500
    cx, cy, rx = 380.0, 700.0, 104.0
    ry = rx * EY
    th = 26.0
    pen.shade(ell(cx + 22, cy + th + 6, rx * 1.02, ry * 0.9, n=36), amount=0.4, seed=s, soft=9.0, hatch=False)
    side = np.vstack([ell(cx, cy, rx, ry, 0, 180, 24), ell(cx, cy + th, rx, ry, 180, 0, 24)])
    pen.cover([side, ell(cx, cy, rx, ry, 0, 360, 40)], seed=s + 1, feather=0.8)
    pen.fill(side, 'wood_d', seed=s + 2, tone=0.62)
    topd = ell(cx, cy, rx, ry, 0, 360, 40)
    pen.fill(topd, 'wood', seed=s + 3, tone=0.40, rgrad=(cx - 30, cy - 10, 0, rx * 1.1, 0.7, 1.3))
    pen.hatch(topd, angle=4, spacing=7, tone=0.2, color='wood_d', seed=s + 4, partial=0.5, bow=0.05)
    pen.line(topd, 4.5, tone=0.85, seed=s + 5, closed=True, taper=(0, 0), head=0.3)
    pen.line(ell(cx, cy + th, rx, ry, 8, 172, 24), 5.5, tone=0.9, seed=s + 6, taper=(0.05, 0.1), head=0.4)
    for k in range(16):
        a = math.radians(8 + k * 10.5)
        x = cx + rx * math.cos(a)
        pen.line(P([(x, cy + ry * math.sin(a) + 3), (x, cy + th + ry * math.sin(a) - 3)]), 1.8, tone=0.5,
                 seed=(s, 7, k), role='detail', taper=(0.1, 0.1), boil=0.2)
    pen.lift(tube(ell(cx, cy, rx * 0.72, ry * 0.7, 200, 260, 8), [2, 6, 2])[0], amt=0.45, seed=s + 8, soft=2.0)


def towel(pen):
    s = 600
    q = P([(1520, 790), (1890, 772), (1930, 900), (1550, 930)])
    pen.shade(q + P([18, 16]), amount=0.35, seed=s, soft=12.0, hatch=False)
    pen.cover(q, seed=s + 1, feather=0.8)
    pen.fill(q, 'cloth', seed=s + 2, tone=0.06)
    for k, f in enumerate((0.3, 0.42)):
        a = q[0] + (q[3] - q[0]) * f
        b = q[1] + (q[2] - q[1]) * f
        band = np.vstack([a + P([0, -6]), b + P([0, -6]), b + P([0, 6]), a + P([0, 6])])
        pen.fill(band, 'lampshade', seed=(s, 3, k), tone=0.4)
    pen.line(D([q[0], q[1]], 20), 4, tone=0.75, seed=s + 4, taper=(0.05, 0.1), head=0.3)
    pen.line(D([q[0], q[3]], 20), 5, tone=0.8, seed=s + 5, taper=(0.05, 0.1), head=0.3)
    pen.line(D([q[3], q[2]], 20), 5.5, tone=0.85, seed=s + 6, taper=(0.05, 0.1), head=0.4, dry=0.4, dry_from=0.6)
    pen.line(D([(1540, 852), (1905, 832)], 20), 2.4, tone=0.45, seed=s + 7, role='detail', taper=(0.1, 0.2))


def spoon(pen):
    s = 700
    hx, hy = 190.0, 575.0
    path = [(232, 563), (330, 527), (446, 488)]
    hd = ell(hx, hy, 50, 28, 0, 360, 30, rot=-20)
    hp = tube(path, [12, 10, 8])[0]
    for k, g_ in enumerate((hp, hd)):
        pen.shade(g_ + P([14, 14]), amount=0.3, seed=(s, 0, k), soft=6.0, hatch=False)
    pen.cover([hp, hd], seed=s + 1, feather=0.8)
    pen.fill(hp, 'wood', seed=s + 2, tone=0.34)
    pen.fill(hd, 'wood', seed=s + 3, tone=0.30, rgrad=(hx - 10, hy - 5, 0, 55, 1.3, 0.7))
    pen.line(np.vstack([hd, hd[:1]]), 4.0, tone=0.85, seed=s + 4, taper=(0, 0), head=0.3)
    pen.line(P(path) + P([0, -5]), 3.4, tone=0.8, seed=s + 5, taper=(0.05, 0.3))
    pen.line(P(path) + P([1, 6]), 2.4, tone=0.55, seed=s + 6, taper=(0.05, 0.3))


def background(pen):
    wall(pen)
    counter(pen)
    bowl(pen)
    kettle(pen)
    lid(pen)
    spoon(pen)
    towel(pen)


# ================================================================= 动态
def steam(pen, t):
    """水壶嘴冒出来的热气：两缕，慢慢往上飘、扭动、淡出（水墨里是提白 + 很淡的墨边）。"""
    sp = spout_tip()
    with pen.group('steam', boil=0.6):
        for k in range(3):
            ph = k * 0.33
            pts = []
            n = 14
            for j in range(n):
                v = j / (n - 1)
                age = (t * 0.55 + ph + v * 0.9) % 1.0
                y = sp[1] - 8 - v * 300
                x = sp[0] - 10 - v * 40 + 22 * math.sin(2.4 * v * math.pi + 2.1 * t + k * 2.0) * (0.3 + v)
                pts.append((x, y))
            pts = np.float32(pts)
            pen.lift(tube(pts, [3, 9, 16, 22, 26, 22, 12])[0], amt=0.62 - 0.1 * k, seed=('steam', k), soft=7.0)
            pen.line(pts[2:] + P([10, 0]), 2.4, tone=0.30, seed=('steam_l', k), role='detail', taper=(0.4, 0.6),
                     dry=0.6, dry_from=0.2, boil=0.8)


def motes(pen, t):
    r = rng(810)
    with pen.group('motes', boil=0.3):
        for i in range(18):
            x = r.uniform(60, 1860) + 16 * math.sin(0.5 * t + i)
            y = (r.uniform(-20, 330) - 7 * t * r.uniform(0.5, 1.4)) % 330
            pen.dot(x, y, r.uniform(1.6, 3.0), color='snow', tone=0.0, seed=('mote', i))


def shadows(pen, t, g):
    with pen.group('shadows', boil=0.4):
        # 罐子在台面上的影（被举在空中：影子落在右下、软而淡）
        c = (g['base'] + g['mouth']) / 2 + np.array([70.0, 230.0])
        L2 = float(np.linalg.norm(g['mouth'] - g['base']))
        pen.shade(ell(c[0], c[1], max(g['R'] * 1.1, L2 * 0.62), g['R'] * 0.55, n=36,
                      rot=math.degrees(math.atan2(g['a2'][1], g['a2'][0])) * 0.4),
                  amount=0.20 * (1.0 - clamp(g['lift'] / 80.0)), seed='jar_sh', soft=22.0, hatch=False)
        # 摊开的手贴在台面上的影
        land_point()
        sil = [np.asarray(q, np.float32) + P([16, 20]) for q in _LAND['sil']]
        pen.shade(sil, amount=0.35, seed='palm_sh', soft=10.0, hatch=False)


def palm_hand(pen, t):
    st = bean_state(t, jar_geom(t))
    bean = None
    if st[0] == 'palm':
        bx, by, hop = st[1]
        bean = (bx, by)
    info = hands.palm_up(pen, PALM['x'], PALM['y'], rot=PALM['rot'], size=PALM['size'], tilt=PALM['tilt'], yaw=PALM['yaw'],
                         cup=palm_cup(t), bean=bean, bean_r=BEAN_R, seed=('palm', 12), sleeve_len=2.6)
    return info


def bean_dot(pen, p, seed, rot=20.0):
    rb = BEAN_R * L_JAR
    pen.dot(p[0], p[1], rb, rb * 0.72, color='bean', tone=1.0, seed=(seed, 0), rot=rot)
    pen.dot(p[0] + rb * 0.15, p[1] + rb * 0.2, rb * 0.72, rb * 0.42, color='bean_d', tone=1.0, seed=(seed, 1), rot=rot)
    pen.lift(ell(p[0] - rb * 0.32, p[1] - rb * 0.28, rb * 0.28, rb * 0.17, n=10, rot=rot), amt=0.85, seed=(seed, 2),
             soft=0.6)


_LABEL = {}


def label_mask():
    if 'm' not in _LABEL:
        f = ImageFont.truetype(core.FONT_LYRIC, 46)
        txt = '红豆'
        l, t_, r, b = f.getbbox(txt)
        im = Image.new('L', (r - l + 10, b - t_ + 10), 0)
        ImageDraw.Draw(im).text((5 - l, 5 - t_), txt, font=f, fill=255)
        _LABEL['m'] = np.asarray(im, np.float32) / 255.0
    return _LABEL['m']


def jar(pen, t, g):
    """玻璃罐：透明（knock=False 叠在后面的东西上），罐壁两侧厚玻璃、罐口一圈螺纹、厚底、竖的高光、小纸标签。"""
    s = 900
    sil = jar_sil(g)
    a2, n2, R = g['a2'], g['n2'], g['R']
    base, mouth = g['base'], g['mouth']
    with pen.group('jar_glass', boil=0.45, knock=False):
        pen.fill(sil, 'glass', seed=s, tone=0.07, c_fade=False, broad=False, grad_auto=False)
        # 厚玻璃底
        pen.fill(end_ellipse(base, g, 0.96), 'glass', seed=s + 1, tone=0.20, c_fade=False)
        pen.line(end_ellipse(base, g, 0.80), 2.6, tone=0.45, seed=s + 2, closed=True, role='detail', taper=(0, 0))
        # 远的那半圈罐口
        pen.line(end_ellipse(mouth, g, 1.0, 180, 360, 30), 3.0, tone=0.55, seed=s + 3, role='detail',
                 taper=(0.1, 0.1))
    # 罐里的红豆
    st = bean_state(t, g)
    if st[0] == 'jar':
        bean_dot(pen, st[1], 'bean_jar', rot=g['ang'] + 30)
    with pen.group('jar_front', boil=0.45, knock=False):
        # 两侧罐壁（厚玻璃：一浓一淡两道）
        for k, sg in enumerate((1.0, -1.0)):
            a = base + n2 * R * sg
            b = mouth + n2 * R * sg
            lit = sg < 0
            pen.line(D([a, b], 20), 6.0 if not lit else 4.0, tone=0.9 if not lit else 0.7, seed=(s, 10, k),
                     taper=(0.05, 0.08), head=0.4, dry=0.3, dry_from=0.7)
            pen.line(D([a - n2 * 8 * sg, b - n2 * 8 * sg], 20), 2.2, tone=0.35, seed=(s, 11, k), role='detail',
                     taper=(0.1, 0.1))
        # 底的近半圈、罐口近半圈 + 螺纹
        pen.line(end_ellipse(base, g, 1.0, 0, 180, 30), 5.0, tone=0.85, seed=s + 12, taper=(0.05, 0.05), head=0.3)
        pen.line(end_ellipse(base, g, 1.0, 180, 360, 30), 3.0, tone=0.6, seed=s + 13, taper=(0.05, 0.05))
        pen.line(end_ellipse(mouth, g, 1.0, 0, 180, 30), 5.0, tone=0.9, seed=s + 14, taper=(0.05, 0.05), head=0.3)
        pen.line(end_ellipse(mouth, g, 0.90, 0, 360, 36), 2.4, tone=0.55, seed=s + 15, closed=True, role='detail',
                 taper=(0, 0))
        for k in range(2):
            c = mouth - a2 * (16 + 11 * k)
            pen.line(end_ellipse(c, g, 1.005, 20, 160, 16), 2.2, tone=0.5, seed=(s, 16, k), role='detail',
                     taper=(0.2, 0.2))
        # 竖的高光（受光一侧宽，另一侧细）
        hl = [base + a2 * 30 - n2 * R * 0.55, mouth - a2 * 44 - n2 * R * 0.55]
        pen.lift(tube(hl, [5, 12, 5])[0], amt=0.75, seed=s + 17, soft=2.0)
        hl2 = [base + a2 * 50 + n2 * R * 0.66, mouth - a2 * 60 + n2 * R * 0.66]
        pen.lift(tube(hl2, [2, 4, 2])[0], amt=0.6, seed=s + 18, soft=1.0)
    # 小纸标签（贴在正面、靠罐底一侧）：手写“红豆”
    with pen.group('jar_label', boil=0.45):
        side = g['Lv'][:2]                       # 贴在罐子的“左侧”（倒过来时朝上，不挡住滑下去的豆）
        side = side - np.dot(side, a2) * a2
        side = side / (np.linalg.norm(side) + 1e-9)
        c = base + a2 * JAR_H * 0.55 + side * R * 0.40
        hw, hh = R * 0.40, JAR_H * 0.12
        q = np.vstack([c - n2 * hw - a2 * hh, c + n2 * hw - a2 * hh, c + n2 * hw + a2 * hh, c - n2 * hw + a2 * hh])
        pen.cover(q, seed=s + 20, feather=0.7)
        pen.fill(q, 'cloth', seed=s + 21, tone=0.10)
        pen.line(np.vstack([q, q[:1]]), 2.4, tone=0.6, seed=s + 22, taper=(0.05, 0.05))
        m = label_mask()
        ang = math.degrees(math.atan2(a2[1], a2[0])) + 90.0      # 字沿着罐身横排（罐底朝下时是正的）
        hgt, wid = m.shape
        Mx = cv2.getRotationMatrix2D((wid / 2, hgt / 2), -ang, 0.9)
        cs, sn = abs(Mx[0, 0]), abs(Mx[0, 1])
        nw, nh = int(hgt * sn + wid * cs) + 4, int(hgt * cs + wid * sn) + 4
        Mx[0, 2] += nw / 2 - wid / 2
        Mx[1, 2] += nh / 2 - hgt / 2
        mr = cv2.warpAffine(m, Mx, (nw, nh), flags=cv2.INTER_LINEAR)
        pen.fill(mask=(mr, int(round(c[0] - nw / 2)), int(round(c[1] - nh / 2))), color='ink', tone=0.85,
                 seed=s + 23, c_dens=1.0, soft=0.7, rough=0.05, bloom=0.0, rim=0.05, c_fade=False, broad=False,
                 grad_auto=False)
    return sil


def jar_hand(pen, t, g, sil):
    return hands.hand_jar(pen, g['G'][0], g['G'][1], axis=tuple(g['A']), jar_r=JAR_R, size=L_JAR,
                          seed=('jarhand', 12), occ=sil, thumb_dir=-1, flip=True, back=tuple(g['back']),
                          wrist=(0.0, 0.0), sleeve_len=1.8)


def falling_bean(pen, t, g):
    st = bean_state(t, g)
    if st[0] != 'fall':
        return
    p = st[1]
    with pen.group('bean_fall', boil=0.3):
        # 掌心上的影子：越近越实
        k = (t - T_OUT) / (T_LAND - T_OUT)
        lp = land_point()
        pen.shade(ell(lp[0] + 4, lp[1] + 5, 12 + 6 * (1 - k), 6 + 3 * (1 - k), n=16), amount=0.15 + 0.3 * k,
                  seed='bean_sh', soft=4.0, hatch=False)
        bean_dot(pen, p, 'bean_fall', rot=40 + 300 * k)
        # 一道很淡的下落拖影
        if k < 0.9:
            pen.line(P([p - np.array([0, 26]), p - np.array([0, 6])]), 3.0, tone=0.0, color='bean', seed='bean_tr',
                     taper=(0.6, 0.1), role='detail', dry=0.8, dry_from=0.0)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    s, ox, oy = view_params(t, float(kw.get('zoom', ZOOM)))
    with pen.view(s, ox, oy):
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        cache = None
        if abs(s - 1.0) < 1e-6:
            cache = ('jar', pen.d % 3, round(float(o[0]), 1), round(float(o[1]), 1))
        with pen.group('bg', boil=BG_BOIL, cache=cache):
            background(pen)
        steam(pen, t)
        motes(pen, t)
        g = jar_geom(t)
        shadows(pen, t, g)
        palm_hand(pen, t)
        sil = jar(pen, t, g)
        jar_hand(pen, t, g, sil)
        falling_bean(pen, t, g)
