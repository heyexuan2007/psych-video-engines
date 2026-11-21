# -*- coding: utf-8 -*-
"""
第 10 镜「有时候」（成片 36.64–38.64，C 水墨，没有红色）。
墙上挂钟特写：一只老式摆钟（圆钟面 + 下面带玻璃门的摆箱）偏右构图，钟面占画面大半；深夜 11:47。
秒针一拍跳一格（拍点 = core.beat_song(n) 换算成成片时间，提前 0.03 秒落格），跳的时候有一点回弹
（过冲 → 回摆 → 停稳，每一下都是一张画）；钟摆一拍摆到一头，和秒针同一个节奏。
分针、时针不动。钟面：行楷手写数字 + 刻度，玻璃一道弧形提白；钟在墙上投下一块软影。
左边：窗的一角（夜色、雪在下）；钟的左下挂着一个小相框（两个人的小像，和冰箱上那张一样）。
会动的：秒针（和它在钟面上的影子）、钟摆（和摆箱玻璃上的反光）、窗外的雪。
镜头固定（让跳格读得清楚）。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒）；sec0 镜头开始时秒针在第几秒（默认 14）
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
from core import W, H, densify, ell, spline, tube, rng, clamp, ease_io

T0, T1 = 36.64, 38.64
HOUR, MINUTE = 11, 47
SEC0 = 14
LEAD = 0.03                         # 秒针比拍点早 0.03 秒落格（一拍二：落在拍点所在的那张画上）
BOUNCE = (0.34, -0.13, 0.045)       # 落格后的三张画：过冲 / 回摆 / 再过一点（单位：秒格）

# 拍点（成片时间）
BEATS = [core.clip_t(core.beat_song(n)) for n in range(250, 275)]
SHOT_BEATS = [b for b in BEATS if T0 - 0.2 < b < T1 + 0.3]

# ---------------------------------------------------------------- 布局
CX, CY = 1330.0, 392.0              # 钟面中心
R_FACE = 286.0                      # 钟面半径（白）
R_RIM = 330.0                       # 木框外半径
PIVOT = (CX, 668.0)                 # 摆的悬点（在钟面后）
ROD = 292.0                         # 摆长（悬点 → 摆锤中心）
BOB_R = 40.0
SWING = 8.5                         # 摆幅（度）
CASE = (1206, 690, 1454, 1110)      # 摆箱
CASE_WIN = (1238, 724, 1422, 1110)  # 摆箱玻璃门
WIN_X1 = 286                        # 左边窗玻璃的右沿
FRAME = (628, 548, 812, 760)        # 小相框
BG_BOIL = 0.4
FONT_NUM = core.FONT_LYRIC          # 华文行楷：手写感的数字


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def dirv(deg):
    """钟面角度（0 = 12 点，顺时针）→ 单位向量（屏幕坐标）。"""
    a = math.radians(deg)
    return np.float32([math.sin(a), -math.cos(a)])


# ================================================================= 时间 → 指针
def sec_value(t):
    """秒针位置（单位：秒格，可带小数 = 回弹）。"""
    k, last = 0, None
    for b in SHOT_BEATS:
        if b - LEAD <= t + 1e-9:
            k += 1
            last = b
    v = SEC0 + k
    if last is not None:
        j = int(math.floor((t - (last - LEAD)) * core.DRAW_RATE + 1e-6))     # 落格后的第几张画
        if 0 <= j < len(BOUNCE):
            v += BOUNCE[j]
    return float(v)


def pendulum_angle(t):
    """摆角（度）：每个拍点摆到一头（左右交替），中间按正弦过。"""
    b0 = SHOT_BEATS[0]
    ph = (t - b0) / core.BEAT
    return SWING * math.cos(math.pi * ph)


# ================================================================= 背景（静态，缓存）
def wall(pen):
    s = 100
    q = P([(-40, -40), (W + 40, -40), (W + 40, H + 40), (-40, H + 40)])
    pen.fill(q, 'wall', seed=s, tone=0.24, rgrad=(760, 120, 300, 1500, 0.35, 1.05), c_fade=False, broad=False,
             var=0.12, cell=110.0)
    # 灯从左上照下来（水墨里光 = 留白）
    pen.light(820, 160, 520, 420, amt=0.32, color='lamp', seed=s + 1)
    # 墙上一道细裂纹 + 几处斑驳
    pen.line(P([(1720, 760), (1748, 812), (1741, 856), (1772, 920), (1766, 980)]), 2.2, tone=0.35, seed=s + 2,
             role='detail', taper=(0.3, 0.5), dry=0.5, dry_from=0.3)
    pen.line(P([(1748, 812), (1790, 830)]), 1.6, tone=0.28, seed=s + 3, role='detail', taper=(0.2, 0.6))
    for k, (x, y, rx, ry) in enumerate([(1700, 180, 120, 40)]):
        pen.shade(ell(x, y, rx, ry, n=24), amount=0.10, seed=(s, 10 + k), soft=26.0, hatch=False)


def window(pen):
    """左边：窗的一角。夜色、远处一道屋脊、玻璃下角起雾；窗框浓墨。"""
    s = 200
    x1 = WIN_X1
    glass = P([(-40, -40), (x1, -40), (x1, 760), (-40, 760)])
    pen.cover(glass, seed=s)
    pen.fill(glass, 'night', seed=s + 1, grad=(0, 0, x1 + 80, 760, 1.0, 0.55), streak=0.4, sangle=88.0)
    roof = P([(-40, 610), (40, 586), (120, 572), (210, 590), (x1 + 10, 606)])
    body = np.vstack([roof, [[x1 + 10, 760], [-40, 760]]])
    pen.fill(body, 'roof', seed=s + 2, grad=(0, 570, 0, 780, 1.0, 0.5))
    pen.line(roof, 10, tone=0.9, color='snow', seed=s + 3, taper=(0.1, 0.2), role='detail', dry=0.45, dry_from=0.3)
    for i, (lx, ly) in enumerate([(48, 640), (150, 652)]):
        q = P([[lx, ly], [lx + 14, ly + 1], [lx + 13, ly + 17], [lx + 1, ly + 16]])
        pen.cover(q, seed=s + 10 + i, feather=0.8)
        pen.fill(q, 'win_warm', seed=s + 12 + i)
    pen.lift(ell(150, 742, 190, 40), amt=0.5, seed=s + 20, soft=12.0)
    # 窗框：竖框 + 窗台
    pen.line(D([(x1 + 6, -20), (x1 + 2, 380), (x1 + 6, 772)], 30), 22, tone=0.9, color='wood_d', seed=s + 30,
             taper=(0.02, 0.1), head=0.4, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25, pool=0.2)
    pen.line(D([(x1 + 30, -20), (x1 + 28, 420), (x1 + 31, 776)], 30), 5, tone=0.5, color='wood_d', seed=s + 31,
             taper=(0.05, 0.3), head=0.1, dry=0.7, dry_from=0.35, streak=0.2)
    pen.line(D([(118, -20), (116, 300), (119, 762)], 30), 10, tone=0.75, color='wood_d', seed=s + 32,
             taper=(0.02, 0.2), head=0.3, lift=0.3, dry=0.5, dry_from=0.6)
    sill = P([[-40, 760], [x1 + 60, 762], [x1 + 66, 800], [-40, 798]])
    pen.cover(sill, seed=s + 33)
    pen.fill(sill, 'wood', seed=s + 34, grad=(0, 0, x1 + 60, 0, 0.6, 1.0))
    pen.line(D([(-40, 762), (x1 + 70, 764)], 30), 16, tone=0.92, color='wood_d', seed=s + 35, taper=(0.02, 0.12),
             head=0.2, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(-40, 800), (x1 + 62, 801)], 30), 5, tone=0.55, color='wood_d', seed=s + 36, taper=(0.05, 0.4),
             dry=0.75, dry_from=0.35)
    pen.shade(P([[-40, 800], [x1 + 66, 801], [x1 + 90, 860], [-40, 862]]), amount=0.3, seed=s + 37, soft=10.0,
              hatch=False)


def photo(pen):
    """钟左下的小相框：里面是两个人的小像（和冰箱上那张一样，简笔）。"""
    s = 300
    x0, y0, x1, y1 = FRAME
    # 挂绳 + 钉子
    nx, ny = (x0 + x1) / 2, y0 - 46
    pen.dot(nx, ny, 4, 4, color='ink', tone=0.9, seed=s)
    pen.line(P([(x0 + 26, y0 + 4), (nx, ny), (x1 - 26, y0 + 4)]), 2.0, tone=0.6, seed=s + 1, taper=(0.1, 0.1),
             head=0)
    pen.shade(P([(x0 + 10, y0 + 16), (x1 + 16, y0 + 16), (x1 + 16, y1 + 14), (x0 + 10, y1 + 14)]), amount=0.4,
              seed=s + 2, soft=8.0, hatch=False)
    outer = P([(x0, y0), (x1, y0 + 2), (x1 + 1, y1), (x0 - 1, y1 - 1)])
    pen.cover(outer, seed=s + 3, feather=0.8)
    pen.fill(outer, 'wood_d', seed=s + 4)
    inner = P([(x0 + 18, y0 + 18), (x1 - 18, y0 + 19), (x1 - 17, y1 - 18), (x0 + 17, y1 - 19)])
    pen.cover(inner, seed=s + 5, feather=0.8)
    pen.fill(inner, 'cloth', seed=s + 6)
    pen.line(np.vstack([outer, outer[:1]]), 4.5, tone=0.85, seed=s + 7, taper=(0.05, 0.1), head=0.3)
    pen.line(np.vstack([inner, inner[:1]]), 2.4, tone=0.6, seed=s + 8, taper=(0.05, 0.1), role='detail')
    # 照片：浅灰的底，两个人并肩（她：齐刘海短发；他：短发），头微微靠在一起
    pen.fill(inner, 'stone', seed=s + 9, tone=0.10, grad=(x0, y0, x1, y1, 1.2, 0.6))
    for k, (hx, hy, hr, who) in enumerate([(x0 + 70, y0 + 82, 17, 'her'), (x1 - 68, y0 + 74, 18, 'him')]):
        # 肩和身子（下面被相框挡住）
        sh_ = P([(hx - 40, y1 - 18), (hx - 34, hy + 40), (hx - 12, hy + 26), (hx + 12, hy + 26), (hx + 34, hy + 40),
                 (hx + 40, y1 - 18)])
        pen.fill(sh_, 'sweater' if who == 'her' else 'boy_sweater', seed=s + 20 + k, tone=0.12 if who == 'her' else 0.45)
        pen.line(sh_, 2.2, tone=0.7, seed=s + 22 + k, role='detail', taper=(0.1, 0.1))
        face = ell(hx, hy, hr * 0.86, hr, 0, 360, 16)
        pen.fill(face, 'skin', seed=s + 24 + k)
        pen.line(face, 2.0, tone=0.6, seed=s + 26 + k, closed=True, role='detail', taper=(0, 0))
        if who == 'her':
            hair = np.vstack([ell(hx, hy - 2, hr * 1.12, hr * 1.12, 180, 360, 12),
                              P([(hx + hr * 1.12, hy + hr * 0.8), (hx + hr * 0.6, hy + hr * 0.8), (hx + hr * 0.62, hy - 4),
                                 (hx - hr * 0.62, hy - 4), (hx - hr * 0.6, hy + hr * 0.8), (hx - hr * 1.12, hy + hr * 0.8)])])
        else:
            hair = np.vstack([ell(hx, hy - 3, hr * 1.02, hr * 1.06, 180, 360, 12),
                              P([(hx + hr * 0.9, hy - 2), (hx + hr * 0.3, hy - hr * 0.55), (hx - hr * 0.5, hy - hr * 0.45),
                                 (hx - hr * 0.95, hy - 2)])])
        pen.fill(hair, 'hair' if who == 'her' else 'boy_hair', seed=s + 28 + k, tone=0.7)
        for j in (-1, 1):
            pen.dot(hx + j * hr * 0.32, hy + hr * 0.12, 1.6, 1.4, color='ink', tone=0.8, seed=(s + 30 + k, j))
        pen.line(P([(hx - 4, hy + hr * 0.5), (hx, hy + hr * 0.58), (hx + 4, hy + hr * 0.5)]), 1.4, tone=0.6,
                 seed=s + 32 + k, role='feature', taper=(0.2, 0.2))
    # 玻璃反光
    pen.lift(tube([(x0 + 30, y1 - 30), (x0 + 70, y0 + 60), (x0 + 96, y0 + 26)], [2, 7, 3])[0], amt=0.5,
             seed=s + 16, soft=2.0)


def clock_body(pen):
    """钟：投影、木框、钟面、刻度、数字、时针分针（都不动 → 进缓存）。"""
    s = 400
    # 墙上的软影（光从左上来：影子落在右下）
    sh = np.vstack([ell(CX + 30, CY + 34, R_RIM + 6, R_RIM + 6, 200, 380, 40),
                    P([(CASE[2] + 30, CASE[1] + 40), (CASE[2] + 30, H + 40), (CASE[0] + 30, H + 40),
                       (CASE[0] + 30, CASE[1] + 40)])])
    pen.shade(ell(CX + 34, CY + 38, R_RIM + 8, R_RIM + 8, n=60), amount=0.42, seed=s, soft=22.0, hatch=False)
    pen.shade(P([(CASE[0] + 30, CASE[1] + 20), (CASE[2] + 30, CASE[1] + 20), (CASE[2] + 30, H + 40),
                 (CASE[0] + 30, H + 40)]), amount=0.40, seed=s + 1, soft=18.0, hatch=False)
    # 挂钟的钉子和绳
    pen.dot(CX, 18, 6, 6, color='ink', tone=0.9, seed=s + 2)
    pen.line(P([(CX - 70, 78), (CX, 18), (CX + 70, 78)]), 2.4, tone=0.65, seed=s + 3, taper=(0.1, 0.1), head=0)
    # 摆箱（木）：先画，钟面压在它上面
    x0, y0, x1, y1 = CASE
    case = P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    pen.cover(case, seed=s + 4, feather=0.8)
    pen.fill(case, 'wood_d', seed=s + 5, c_fade=False, broad=False)
    wx0, wy0, wx1, wy1 = CASE_WIN
    win = P([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)])
    pen.cover(win, seed=s + 6, feather=0.8)
    pen.fill(win, 'wood_d', seed=s + 7, tone=0.62, c_fade=False, broad=False, grad=(wx0, 0, wx1, 0, 1.2, 0.7))
    pen.line(D([(x0, y0 + 10), (x0 - 1, y1)], 30), 8, tone=0.9, seed=s + 8, taper=(0.05, 0.1), head=0.4)
    pen.line(D([(x1, y0 + 10), (x1 + 1, y1)], 30), 6, tone=0.8, seed=s + 9, taper=(0.05, 0.1), head=0.3, dry=0.4,
             dry_from=0.6)
    pen.line(D([(wx0, wy0), (wx0, wy1)], 30), 4, tone=0.7, seed=s + 10, taper=(0.05, 0.1), role='detail')
    pen.line(D([(wx1, wy0), (wx1, wy1)], 30), 4, tone=0.7, seed=s + 11, taper=(0.05, 0.1), role='detail')
    pen.line(D([(wx0, wy0), (wx1, wy0)], 30), 4, tone=0.7, seed=s + 12, taper=(0.05, 0.1), role='detail')
    # 木框：一圈深色木（外沿浓墨，内沿一道细）
    rim = np.vstack([ell(CX, CY, R_RIM, R_RIM, 0, 360, 120), ell(CX, CY, R_FACE, R_FACE, 360, 0, 120)])
    pen.cover(ell(CX, CY, R_RIM, R_RIM, 0, 360, 120), seed=s + 13, feather=0.8)
    pen.fill(rim, 'wood_d', seed=s + 14, c_dens=0.55, c_fade=False, broad=False, grad_auto=False,
             grad=(CX - R_RIM, CY - R_RIM, CX + R_RIM, CY + R_RIM, 0.75, 1.25))
    pen.lift(tube(ell(CX, CY, R_RIM - 18, R_RIM - 18, 215, 300, 20), [3, 12, 14, 4])[0], amt=0.55, seed=s + 15,
             soft=2.0, dry=0.6, streak=0.6)
    pen.line(ell(CX, CY, R_RIM, R_RIM, 0, 360, 90), 12, tone=0.95, seed=s + 16, closed=True, head=0.5,
             lift=0.2, dry=0.3, dry_from=0.7, pool=0.2)
    pen.line(ell(CX, CY, R_FACE + 2, R_FACE + 2, 0, 360, 90), 4.5, tone=0.8, seed=s + 17, closed=True,
             role='detail')
    # 钟面：米白，右下靠框处被框挡出一圈影
    face = ell(CX, CY, R_FACE, R_FACE, 0, 360, 120)
    pen.fill(face, 'enamel', seed=s + 18, c_fade=False, broad=False)
    pen.shade(np.vstack([ell(CX, CY, R_FACE, R_FACE, -30, 160, 40), ell(CX - 16, CY - 18, R_FACE - 6, R_FACE - 6,
                                                                       160, -30, 40)]),
              amount=0.32, seed=s + 19, soft=8.0, hatch=False)
    # 刻度
    for k in range(60):
        v = dirv(k * 6)
        big = k % 5 == 0
        r0 = R_FACE * (0.86 if big else 0.91)
        r1 = R_FACE * 0.955
        pen.line(P([(CX + v[0] * r0, CY + v[1] * r0), (CX + v[0] * r1, CY + v[1] * r1)]), 5.5 if big else 2.4,
                 tone=0.9 if big else 0.6, seed=(s, 30, k), role='detail' if not big else 'contour',
                 taper=(0.15, 0.2), boil=0.3)
    numerals(pen)
    # 钟面上一行小字（钟表厂的牌子位置），手写的淡墨
    pen.line(P([(CX - 46, CY + 118), (CX - 10, CY + 116), (CX + 30, CY + 118), (CX + 46, CY + 117)]), 2.0,
             tone=0.35, seed=s + 20, role='detail', taper=(0.2, 0.2), dry=0.5, dry_from=0.3)
    # 时针、分针（不动）
    hands_static(pen)


_NUM = None


def _numeral_masks():
    """12 个行楷数字的遮罩（场景坐标）。"""
    global _NUM
    if _NUM is not None:
        return _NUM
    f = ImageFont.truetype(FONT_NUM, 62)
    out = []
    for k in range(1, 13):
        txt = str(k)
        l, t_, r, b = f.getbbox(txt)
        w, h = r - l + 12, b - t_ + 12
        im = Image.new('L', (w, h), 0)
        ImageDraw.Draw(im).text((6 - l, 6 - t_), txt, font=f, fill=255)
        m = np.asarray(im, np.float32) / 255.0
        v = dirv(k * 30)
        rr = R_FACE * 0.71
        cx, cy = CX + v[0] * rr, CY + v[1] * rr
        out.append((m, int(round(cx - w / 2)), int(round(cy - h / 2))))
    _NUM = out
    return out


def numerals(pen):
    for k, (m, x0, y0) in enumerate(_numeral_masks()):
        pen.fill(mask=(m, x0, y0), color='ink', tone=0.88, seed=(450, k), rim=0.2, grad_auto=False)


def hand_poly(deg, length, w, tail=0.0, kind='hour'):
    v = dirv(deg)
    n = np.float32([-v[1], v[0]])
    c = np.float32([CX, CY])
    if kind == 'hour':
        pts = [c - v * tail + n * w * 0.5, c + v * length * 0.55 + n * w * 0.45, c + v * length * 0.72 + n * w * 1.0,
               c + v * length * 0.86 + n * w * 0.55, c + v * length, c + v * length * 0.86 - n * w * 0.55,
               c + v * length * 0.72 - n * w * 1.0, c + v * length * 0.55 - n * w * 0.45, c - v * tail - n * w * 0.5]
    else:
        pts = [c - v * tail + n * w * 0.5, c + v * length * 0.7 + n * w * 0.32, c + v * length,
               c + v * length * 0.7 - n * w * 0.32, c - v * tail - n * w * 0.5]
    return np.float32(pts)


def hands_static(pen):
    s = 470
    h_deg = (HOUR % 12 + MINUTE / 60.0) * 30.0
    m_deg = MINUTE * 6.0
    for k, (deg, L, w, tail, kind) in enumerate(((h_deg, R_FACE * 0.52, 15, 34, 'hour'),
                                                 (m_deg, R_FACE * 0.80, 13, 40, 'min'))):
        poly = hand_poly(deg, L, w, tail, kind)
        pen.shade(poly + np.float32([7, 9]), amount=0.35, seed=(s, 0, k), soft=4.0, hatch=False)
        pen.cover(poly, seed=(s, 1, k), feather=0.6)
        pen.fill(poly, 'ink', seed=(s, 2, k), tone=0.85, grad_auto=False)
        pen.line(np.vstack([poly, poly[:1]]), 2.6, tone=0.95, seed=(s, 3, k), taper=(0.05, 0.05), role='detail')


def lamp(pen):
    """画面上沿：厨房吊灯的灯罩露出下半截（灯亮着：水墨里灯下是留白）。"""
    s = 250
    lx, ly = 830, 70
    pen.line(D([(lx + 1, -30), (lx, ly - 40)], 20), 3.0, tone=0.7, seed=s, taper=(0, 0))
    shade = spline(P([[lx - 30, -30], [lx + 30, -30], [lx + 70, ly - 30], [lx + 132, ly - 2], [lx + 140, ly + 4],
                      [lx - 140, ly + 4], [lx - 132, ly - 2], [lx - 70, ly - 30]]), 3.0, closed=True)
    pen.cover(shade, seed=s + 1, feather=0.8)
    pen.fill(shade, 'lampshade', seed=s + 2, grad=(lx - 140, 0, lx + 140, 0, 1.0, 0.7))
    pen.lift(tube([(lx - 20, ly - 70), (lx - 60, ly - 34), (lx - 110, ly - 4)], [4, 9, 4])[0], amt=0.5, seed=s + 3,
             soft=1.5, dry=0.7, streak=0.5)
    pen.line(D([(lx - 146, ly + 5), (lx, ly + 10), (lx + 146, ly + 4)], 20), 10, tone=0.92, seed=s + 4,
             taper=(0.05, 0.18), head=0.5, lift=0.3, dry=0.35, dry_from=0.75)
    pen.line(spline(P([[lx - 30, -30], [lx - 70, ly - 30], [lx - 132, ly - 2]]), 3.0), 4.5, tone=0.75, seed=s + 5,
             taper=(0.1, 0.2), head=0.3)
    pen.line(ell(lx, ly + 12, 24, 14, 15, 165, 12), 2.6, tone=0.5, seed=s + 6, taper=(0.2, 0.4), head=0)


def background(pen):
    wall(pen)
    lamp(pen)
    window(pen)
    photo(pen)
    clock_body(pen)


# ================================================================= 动态
def snow(pen, t):
    r = rng(600)
    with pen.group('snow', boil=0.6):
        for i in range(46):
            far = i < 26
            sp = r.uniform(24, 40) if far else r.uniform(46, 78)
            size = r.uniform(1.5, 2.6) if far else r.uniform(3.0, 5.0)
            amp = r.uniform(4, 12)
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-20, WIN_X1)
            ys = r.uniform(0, 760)
            yy = (ys + sp * t) % 780 - 20
            xx = (xs + 6 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (WIN_X1 + 20) - 20
            if not (-10 < xx < WIN_X1 - 8 and -10 < yy < 752):
                continue
            if abs(xx - 117) < 8 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', i))


def pendulum(pen, t):
    """摆杆 + 摆锤（黄铜：留白 + 一圈淡墨 + 高光），在摆箱玻璃后面。"""
    s = 700
    ang = math.radians(pendulum_angle(t))
    v = np.float32([math.sin(ang), math.cos(ang)])
    piv = np.float32(PIVOT)
    bob = piv + v * ROD
    with pen.group('pendulum', boil=0.5):
        # 箱里的影子：摆锤在箱背板上的影（偏右下）
        pen.shade(ell(bob[0] + 14, bob[1] + 12, BOB_R, BOB_R, n=24), amount=0.35, seed=s, soft=6.0, hatch=False)
        # 摆杆只在玻璃门里看得见（悬点藏在钟面后面）
        top = piv + v * ((CASE_WIN[1] + 2 - piv[1]) / max(v[1], 1e-3))
        rod = tube([top, (top + bob) / 2, bob], [7, 7, 8])[0]
        pen.cover(rod, seed=s + 1, feather=0.5)
        pen.fill(rod, 'metal', seed=s + 2, tone=0.35)
        pen.line(P([top, bob - v * BOB_R]), 2.0, tone=0.7, seed=s + 3, role='detail', taper=(0.0, 0.1))
        disc = ell(bob[0], bob[1], BOB_R, BOB_R, 0, 360, 36)
        pen.cover(disc, seed=s + 4, feather=0.6)
        pen.fill(disc, 'metal', seed=s + 5, tone=0.22, rgrad=(bob[0] - 12, bob[1] - 12, 4, BOB_R * 1.3, 0.2, 1.4))
        pen.line(disc, 3.6, tone=0.85, seed=s + 6, closed=True, taper=(0, 0))
        pen.line(ell(bob[0], bob[1], BOB_R * 0.62, BOB_R * 0.62, 200, 330, 10), 2.0, tone=0.45, seed=s + 7,
                 role='detail', taper=(0.3, 0.3))
        pen.lift(ell(bob[0] - 13, bob[1] - 14, 9, 6, n=12, rot=-35), amt=0.9, seed=s + 8, soft=1.5)
    # 摆箱玻璃门：一道斜的反光（压在摆上）
    wx0, wy0, wx1, wy1 = CASE_WIN
    with pen.group('case_glass', boil=0.4):
        pen.lift(tube([(wx0 + 30, wy1), (wx0 + 70, wy0 + 160), (wx0 + 104, wy0 + 6)], [6, 16, 6])[0], amt=0.35,
                 seed=s + 10, soft=5.0)
        pen.lift(tube([(wx1 - 40, wy1), (wx1 - 22, wy0 + 120)], [3, 6])[0], amt=0.3, seed=s + 11, soft=2.0)


def second_hand(pen, t):
    s = 800
    deg = sec_value(t) * 6.0
    v = dirv(deg)
    n = np.float32([-v[1], v[0]])
    c = np.float32([CX, CY])
    L, tail = R_FACE * 0.90, R_FACE * 0.22
    with pen.group('second', boil=0.5):
        # 秒针投在钟面上的影（跟着跳）
        sh_off = np.float32([9, 11])
        pen.shade(tube([c - v * tail + sh_off, c + v * L + sh_off], [7, 4])[0], amount=0.35, seed=s, soft=3.5,
                  hatch=False)
        pen.line(P([c - v * tail, c + v * (L * 0.5), c + v * L]), 5.2, tone=0.98, seed=s + 1, taper=(0.0, 0.35),
                 head=0.1, role='detail')
        cw = c - v * tail * 0.78
        pen.dot(cw[0], cw[1], 11, 11, color='ink', tone=0.9, seed=s + 2)
        pen.lift(ell(cw[0], cw[1], 4.5, 4.5, n=10), amt=0.85, seed=s + 3, soft=0.6)
        # 中心轴帽
        pen.dot(CX, CY, 15, 15, color='ink', tone=0.95, seed=s + 4)
        pen.lift(ell(CX - 4, CY - 5, 4.5, 3.5, n=10), amt=0.8, seed=s + 5, soft=0.6)


def face_glass(pen):
    """钟面玻璃：左上一道弧形提白 + 一个小亮点（最上面一层）。"""
    s = 900
    with pen.group('face_glass', boil=0.4):
        arc = ell(CX, CY, R_FACE * 0.84, R_FACE * 0.84, 200, 262, 16)
        pen.lift(tube(arc, [3, 14, 22, 16, 4])[0], amt=0.62, seed=s, soft=3.0)
        arc2 = ell(CX, CY, R_FACE * 0.70, R_FACE * 0.70, 214, 240, 8)
        pen.lift(tube(arc2, [2, 6, 2])[0], amt=0.5, seed=s + 1, soft=1.5)
        pen.lift(ell(CX + R_FACE * 0.45, CY + R_FACE * 0.55, 10, 6, n=12, rot=-40), amt=0.5, seed=s + 2, soft=3.0)


def draw(pen, **kw):
    global SEC0
    t = float(kw.get('t', pen.t))
    if 'sec0' in kw:
        SEC0 = int(kw['sec0'])
    with pen.group('bg', boil=BG_BOIL, cache=('clock', pen.d % 3)):
        background(pen)
    snow(pen, t)
    pendulum(pen, t)
    second_hand(pen, t)
    face_glass(pen)
