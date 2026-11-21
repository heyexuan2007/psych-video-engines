# -*- coding: utf-8 -*-
"""
厨房场景：冬夜，小公寓厨房兼餐桌一角（第 1 镜“第十七句一句示”，也给后面的镜头复用）。
只调用 Pen 指令；三种笔刷下几何完全相同。随 pen.style 变的只有“他”：C 里是铅笔草稿（想象），A/B 里是上色完成的人。

draw(pen, **kw)
  静态背景放在第一个 group（cache=('kitchen', d % 3)，boil 0.4）；动态层（雪、热气、汤、人物、桌上的碗）每帧画。
  kw（都可省）：
    girl_expr     她的表情（EXPR 名或参数 dict）；不写 = 默认表演
    girl_look     'pot' 低头看锅 / 'him' 抬头看他 / 'down' 垂眼 / (yaw, pitch, roll) 元组；不写 = 默认表演
    stir          True/False 是否在搅（False = 手搭在台面上）；stir_speed 每秒圈数（默认 0.59）
    blink         0..1 覆盖眨眼
    show_girl     默认 True
    show_boy      默认 True
    boy_mode      'sketch' / 'full'；不写 = C 草稿、A/B 上色
    boy_opacity   草稿透明度（默认按表演，约 0.64 → 淡出）
    boy_erase     0..1 被擦掉的程度（默认按表演，约 3.45 秒开始）
    boy_pose      'sit_chin'（默认）/'sit_eat'/'stand'
    boy_expr      他的表情（默认 'smile'）
    bowls         'two'（默认，桌上两只空碗）/'none'/'soup'（两碗红豆汤）
    t             覆盖表演时间（成片秒）；默认 pen.t
"""
import math

import cv2
import numpy as np

from core import (densify, ell, bez, rect, spline, tube, rng, sd, clamp, smooth01, sstep, ease_io, ease_out, ease_in,
                  lerp, W, H)
from characters import girl, boy, boy_act, girl_silhouette, mix_expr, EXPR

# ---------------------------------------------------------------- 布局常量（和 style_C 小样一致）
WIN = (380, 116, 900, 520)          # 窗框外沿
GLASS = (393, 129, 887, 507)        # 玻璃
MULL_X = 735                        # 竖棂
TRANS_Y = 252                       # 横棂
CTR_BACK, CTR_FRONT = 612, 648      # 台面后沿/前沿
POT = dict(cx=772, rim_y=546, rx=66, ry=15, bot=598)
SOUP = (772, 553, 57, 12.5)
TABLE = dict(cx=1360, cy=655, rx=262, ry=54)
LAMP = (1012, 120)
POT_COL = '#45474F'                 # 搪瓷小锅（深灰）
FRIDGE_X = 1840                     # 冰箱左沿（挪到画面右边缘，只露出一条，给门让位）
DOOR = dict(x0=1546, x1=1802, top=214, floor=950)    # 门洞（右侧墙上；合页在左、门把手在右，往外开）
HORIZON = 390.0                     # 视平线（门扇转开时的透视收缩中心）
FLOOR_T = 950.0                     # 第 8 镜里他脚下的地面 y

BG_BOIL = 0.4
GIRL_BOIL = 1.0
BOY_BOIL = 2.1


def D(pts, spacing=24.0, closed=False):
    """直边物件的线先加密再交给 line（样条平滑后仍然是直的）。"""
    return densify(np.float32(pts), spacing, closed)


def P(pts):
    return np.float32(pts)


# ================================================================= 背景
def _window(pen):
    s = 100
    x0, y0, x1, y1 = GLASS
    glass = P([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    pen.cover(glass, seed=s)
    # 夜色：上浓下淡、往右下渐淡
    pen.fill(glass, 'night', seed=s + 1, grad=(x0 + 60, y0, x1 + 40, y1 + 80, 1.0, 0.55), streak=0.4)
    # 远处的屋顶：深一些的块，顶上一道积雪（亮线），亮着的小窗
    roofs = [
        [(393, 446), (428, 420), (470, 400), (515, 420), (548, 440)],
        [(530, 455), (575, 430), (628, 410), (676, 428), (722, 452)],
        [(745, 430), (788, 406), (835, 390), (868, 402), (887, 412)],
    ]
    for i, top in enumerate(roofs):
        top = P(top)
        body = np.vstack([top, [[top[-1, 0], y1], [top[0, 0], y1]]])
        pen.fill(body, 'roof', seed=s + 20 + i, grad=(0, float(top[:, 1].min()), 0, y1 + 30, 1.0, 0.45))
        pen.line(top, 11, tone=0.9, color='snow', seed=s + 30 + i, taper=(0.1, 0.2), role='detail', dry=0.45,
                 dry_from=0.3)
        pen.line(top + P([0, 6]), 2.6, tone=0.42, color='roof', seed=s + 40 + i, taper=(0.1, 0.3), role='detail',
                 dry=0.5, dry_from=0.5)
    lit = [(430, 462, 13, 15), (480, 455, 11, 14), (606, 466, 14, 13), (652, 474, 11, 12), (796, 440, 13, 16),
           (842, 452, 11, 13)]
    for i, (lx, ly, lw, lh) in enumerate(lit):
        q = P([[lx, ly], [lx + lw, ly + 1], [lx + lw - 1, ly + lh], [lx + 1, ly + lh - 1]])
        pen.cover(q, seed=s + 50 + i, feather=0.8)
        pen.fill(q, 'win_warm', seed=s + 55 + i)
        pen.line([(lx + lw / 2, ly + 1), (lx + lw / 2 + 0.5, ly + lh - 1)], 1.6, tone=0.35, color='roof',
                 seed=s + 60 + i, taper=(0, 0), role='detail')
    # 玻璃下角起雾：提白成软软的一团
    for i, (cx, cy, rx, ry) in enumerate([(440, 500, 100, 46), (865, 498, 80, 40), (600, 507, 80, 16)]):
        pen.lift(ell(cx, cy, rx, ry), amt=0.55, seed=s + 70 + i, soft=10.0)
    # 窗框：左、上两笔浓（起笔顿、行笔提、收笔飞白），右边一笔淡而断
    pen.line(D([(383, 106), (379, 300), (382, 528)], 30), 15, tone=0.90, color='wood_d', seed=s + 80,
             taper=(0.08, 0.18), head=0.6, lift=0.3, dry=0.55, dry_from=0.62, streak=0.25, pool=0.25)
    pen.line(D([(366, 116), (520, 110), (700, 113), (912, 111)], 30), 16, tone=0.88, color='wood_d', seed=s + 81,
             taper=(0.05, 0.3), head=0.7, lift=0.35, dry=0.7, dry_from=0.55, streak=0.3, fade=0.2, pool=0.2)
    pen.line(D([(900, 124), (903, 260), (898, 420)], 30), 7, tone=0.55, color='wood_d', seed=s + 82,
             taper=(0.1, 0.6), head=0.3, dry=0.85, dry_from=0.15, streak=0.3, fade=0.4)
    pen.line(D([(394, 132), (392, 330)], 30), 3.5, tone=0.45, color='wood_d', seed=s + 83, taper=(0.1, 0.5),
             head=0.1, dry=0.6, dry_from=0.4, role='detail')
    pen.line(D([(398, 131), (620, 129)], 30), 3.2, tone=0.42, color='wood_d', seed=s + 84, taper=(0.1, 0.6),
             head=0.1, dry=0.6, dry_from=0.4, role='detail')
    # 窗棂
    pen.line(D([(MULL_X + 2, 128), (MULL_X - 1, 330), (MULL_X + 1, 506)], 30), 10, tone=0.80, color='wood_d',
             seed=s + 85, taper=(0.06, 0.2), head=0.45, lift=0.3, dry=0.45, dry_from=0.6, streak=0.2)
    pen.line(D([(392, TRANS_Y + 2), (600, TRANS_Y - 2), (888, TRANS_Y + 1)], 30), 9, tone=0.74, color='wood_d',
             seed=s + 86, taper=(0.05, 0.25), head=0.45, lift=0.3, dry=0.55, dry_from=0.55, streak=0.2)
    # 窗台：台面厚度 + 一道有力的横笔
    sill = P([[362, 512], [926, 514], [930, 534], [358, 532]])
    pen.cover(sill, seed=s + 89)
    pen.fill(sill, 'wood', seed=s + 90, grad=(360, 0, 930, 0, 1.0, 0.6))
    pen.shade(P([[362, 524], [926, 526], [930, 534], [358, 532]]), amount=0.3, seed=s + 93, angle=0)
    pen.line(D([(348, 513), (640, 509), (930, 515)], 30), 15, tone=0.92, color='wood_d', seed=s + 91,
             taper=(0.04, 0.15), head=0.7, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(362, 535), (640, 536), (918, 533)], 30), 5, tone=0.55, color='wood_d', seed=s + 92,
             taper=(0.1, 0.4), head=0.2, dry=0.75, dry_from=0.35, streak=0.2)


def _plant(pen):
    s = 200
    pot = P([[836, 470], [884, 470], [878, 507], [842, 507]])
    pen.cover(pot, seed=s, feather=0.8)
    pen.fill(pot, 'terra', seed=s + 4, grad=(836, 488, 884, 488, 1.0, 0.6))
    pen.shade(P([[862, 470], [884, 470], [878, 507], [860, 507]]), amount=0.3, seed=s + 5)
    pen.line(D([(832, 470), (860, 467), (888, 470)], 12), 6, tone=0.88, seed=s + 1, taper=(0.1, 0.2), head=0.4)
    pen.line([(838, 474), (843, 506)], 4, tone=0.7, seed=s + 2, taper=(0.1, 0.4), head=0.2, dry=0.5, dry_from=0.5)
    pen.line([(882, 474), (877, 506)], 3, tone=0.6, seed=s + 3, taper=(0.1, 0.4), head=0.1)
    # 叶：没骨写意，一笔一叶，起笔按、收笔尖
    leaves = [((858, 470), (835, 420), (816, 402)), ((860, 470), (852, 410), (858, 382)),
              ((862, 470), (882, 425), (900, 410)), ((857, 470), (840, 440), (820, 444)),
              ((864, 470), (878, 446), (892, 452)), ((860, 470), (866, 430), (874, 396))]
    for i, (a, b, c) in enumerate(leaves):
        pen.line(bez(a, b, c, 6), 13, tone=0.55 + 0.2 * (i % 2), color='plant', seed=s + 10 + i, role='detail',
                 taper=(0.35, 0.55), head=0.7, streak=0.3, dry=0.3, dry_from=0.75)
    for i, (a, b) in enumerate([((858, 469), (840, 430)), ((862, 469), (870, 420))]):
        pen.line([a, b], 1.6, tone=0.6, color='grass_d', seed=s + 30 + i, taper=(0.1, 0.3), role='detail')


def _shelf_mugs(pen):
    s = 300
    board = P([[88, 297], [360, 297], [360, 305], [88, 305]])
    pen.fill(board, 'wood', seed=s + 1)
    pen.line(D([(88, 301), (230, 297), (360, 302)], 24), 12, tone=0.88, color='wood_d', seed=s, taper=(0.04, 0.25),
             head=0.6, lift=0.25, dry=0.55, dry_from=0.6, streak=0.25, pool=0.2)
    pen.shade(P([[96, 305], [352, 305], [346, 342], [104, 338]]), amount=0.18, seed=s + 4,
              grad=(0, 305, 0, 342, 1.0, 0.0))
    pen.line([(116, 306), (120, 344), (150, 307)], 4, tone=0.55, color='wood_d', seed=s + 2, taper=(0.1, 0.3),
             head=0.2, dry=0.4, dry_from=0.5)
    pen.line([(326, 306), (322, 344), (296, 307)], 4, tone=0.55, color='wood_d', seed=s + 3, taper=(0.1, 0.3),
             head=0.2, dry=0.4, dry_from=0.5)
    # 两只马克杯：她的（米白）和他的（青绿）
    for i, (mx, h, col) in enumerate([(150, 54, 'enamel'), (232, 49, 'cabinet')]):
        bx0, bx1, top, bot = mx, mx + 48, 299 - h, 298
        body = P([[bx0, top + 4], [bx1, top + 3], [bx1 - 1, bot], [bx0 + 1, bot]])
        pen.cover(body, seed=s + 9 + i, feather=0.8)
        pen.fill(body, col, seed=s + 10 + i)
        pen.shade(P([[bx0 + 30, top + 4], [bx1, top + 3], [bx1 - 1, bot], [bx0 + 30, bot]]), amount=0.3,
                  seed=s + 18 + i)
        pen.line(ell(bx0 + 24, top + 4, 24, 5, 190, 520, 14), 3.0, tone=0.75, seed=s + 12 + i, taper=(0.1, 0.4),
                 head=0.2)
        pen.line(D([(bx0, top + 5), (bx0 - 1, (top + bot) / 2), (bx0 + 1, bot)], 12), 5, tone=0.88, seed=s + 14 + i,
                 taper=(0.1, 0.25), head=0.5, lift=0.2)
        pen.line([(bx1, top + 5), (bx1 + 1, (top + bot) / 2), (bx1 - 1, bot)], 3, tone=0.6, seed=s + 16 + i,
                 taper=(0.1, 0.4), head=0.2, dry=0.5, dry_from=0.5)
        hx = bx1 if i == 0 else bx0
        sg = 1 if i == 0 else -1
        pen.line([(hx, top + 14), (hx + 18 * sg, top + 17), (hx + 17 * sg, top + 34), (hx, top + 38)], 5.5,
                 tone=0.82, seed=s + 20 + i, taper=(0.2, 0.35), head=0.4, dry=0.3, dry_from=0.7)


def _counter(pen):
    s = 400
    # 柜体（往下淡出到纸，给歌词留白）
    cab = P([[66, CTR_FRONT + 4], [988, CTR_FRONT + 2], [985, 820], [64, 820]])
    pen.fill(cab, 'cabinet', seed=s + 70, grad=(0, CTR_FRONT + 10, 0, 815, 0.8, 0.0))
    # 台面：木色 + 木纹排线；前沿一道浓墨长笔
    top = P([[90, CTR_BACK], [962, CTR_BACK], [980, CTR_FRONT], [70, CTR_FRONT]])
    pen.cover(top, seed=s + 5)
    pen.fill(top, 'wood', seed=s, grad=(70, 630, 980, 630, 1.0, 0.75))
    pen.hatch(top, angle=2, spacing=6, tone=0.18, color='wood_d', seed=s + 1, partial=0.45, bow=0.01)
    pen.line(D([(86, CTR_BACK), (500, CTR_BACK - 2), (968, CTR_BACK + 1)], 30), 5, tone=0.62, color='wood_d',
             seed=s + 2, taper=(0.05, 0.3), head=0.2, dry=0.5, dry_from=0.6)
    # 台面厚度（一道深色，向下迅速淡出）
    pen.fill(P([[60, CTR_FRONT + 4], [990, CTR_FRONT + 2], [985, CTR_FRONT + 26], [62, CTR_FRONT + 28]]), 'wood_d',
             seed=s + 4, grad=(0, CTR_FRONT + 4, 0, CTR_FRONT + 28, 1.0, 0.5))
    pen.shade(P([[62, CTR_FRONT + 26], [985, CTR_FRONT + 24], [985, CTR_FRONT + 60], [62, CTR_FRONT + 62]]),
              amount=0.35, seed=s + 6, grad=(0, CTR_FRONT + 26, 0, CTR_FRONT + 60, 1.0, 0.0))
    pen.line(D([(52, CTR_FRONT + 1), (420, CTR_FRONT + 3), (720, CTR_FRONT - 1), (992, CTR_FRONT + 1)], 30), 17,
             tone=0.93, color='wood_d', seed=s + 3, taper=(0.03, 0.12), head=0.8, lift=0.4, dry=0.65,
             dry_from=0.66, streak=0.3, pool=0.25)
    # 柜门缝：三笔干笔竖线，越往下越干越淡
    for i, (x, yb) in enumerate([(338, 790), (598, 770), (858, 800)]):
        pen.line(D([(x, CTR_FRONT + 22), (x + 1, (CTR_FRONT + yb) / 2), (x - 1, yb)], 24), 7, tone=0.55,
                 seed=s + 10 + i, taper=(0.1, 0.6), head=0.4, dry=0.9, dry_from=0.15, streak=0.35, fade=0.6)
        pen.dot(x + 22, CTR_FRONT + 44, 4.2, 3.6, color='metal', tone=0.75, seed=s + 20 + i)
    pen.line(D([(72, CTR_FRONT + 6), (70, 720), (72, 800)], 24), 9, tone=0.6, seed=s + 40, taper=(0.05, 0.7),
             head=0.4, dry=0.9, dry_from=0.2, streak=0.35, fade=0.6)
    # 擦手巾：搭在台面前沿（白布 + 两道条纹 + 淡影）
    tw = P([[268, CTR_FRONT + 6], [330, CTR_FRONT + 4], [335, 752], [324, 776], [298, 784], [272, 772],
            [264, 700]])
    pen.cover(tw, seed=s + 50, feather=0.8)
    pen.fill(tw, 'cloth', seed=s + 51)
    pen.shade(P([[300, CTR_FRONT + 5], [330, CTR_FRONT + 4], [335, 752], [324, 776], [300, 784]]), amount=0.25,
              seed=s + 59, angle=80)
    for k, yy in enumerate([702, 718]):
        band = P([[265, yy - 3], [334, yy - 3], [334, yy + 3], [266, yy + 3]])
        pen.fill(band, 'lampshade', seed=s + 60 + k)
        pen.line(D([(266, yy), (300, yy + 3), (334, yy)], 12), 5, tone=0.5, color='lampshade', seed=s + 52 + k,
                 taper=(0.1, 0.2), head=0.3, dry=0.4, dry_from=0.6, role='detail')
    pen.line(D([(268, CTR_FRONT + 8), (264, 700), (270, 772), (296, 786)], 16), 5, tone=0.8, seed=s + 55,
             taper=(0.1, 0.3), head=0.4, lift=0.2, dry=0.4, dry_from=0.7)
    pen.line(D([(330, CTR_FRONT + 6), (335, 740), (324, 778)], 16), 3.5, tone=0.55, seed=s + 56, taper=(0.1, 0.4),
             head=0.1, dry=0.5, dry_from=0.5)
    pen.line([(260, CTR_FRONT + 4), (300, CTR_FRONT - 3), (340, CTR_FRONT + 3)], 6, tone=0.78, seed=s + 57,
             taper=(0.1, 0.25), head=0.5)


def _kettle(pen):
    s = 500
    cx, base = 228, CTR_BACK + 18
    body = np.vstack([ell(cx, base - 34, 58, 36, 180, 360, 20), P([[cx + 60, base], [cx - 60, base]])])
    pen.cover(body, seed=s + 10, feather=0.8)
    pen.fill(body, 'metal', seed=s, grad=(cx - 60, 0, cx + 60, 0, 1.0, 0.75))
    pen.shade(np.vstack([ell(cx, base - 34, 58, 36, 270, 360, 10), P([[cx + 60, base], [cx + 20, base]])]),
              amount=0.35, seed=s + 11, angle=70)
    pen.lift(tube([(cx - 28, base - 55), (cx - 30, base - 30), (cx - 26, base - 8)], [3, 7, 3])[0], amt=0.7,
             seed=s + 1, soft=1.5, dry=0.6)
    pen.line(ell(cx, base - 34, 58, 36, 183, 357, 14), 7, tone=0.9, seed=s + 2, taper=(0.08, 0.3), head=0.6,
             lift=0.3, dry=0.4, dry_from=0.7)
    pen.line([(cx - 60, base - 30), (cx - 61, base - 10), (cx - 56, base)], 6, tone=0.85, seed=s + 3,
             taper=(0.1, 0.2), head=0.4)
    pen.line([(cx + 58, base - 30), (cx + 60, base - 10), (cx + 56, base)], 3.5, tone=0.6, seed=s + 4,
             taper=(0.1, 0.3), head=0.1)
    pen.line(D([(cx - 60, base), (cx, base + 3), (cx + 60, base)], 12), 6, tone=0.8, seed=s + 5, taper=(0.1, 0.2),
             head=0.4, dry=0.4, dry_from=0.6)
    # 壶嘴（朝右）、壶盖钮、提手
    pen.line([(cx + 48, base - 30), (cx + 78, base - 46), (cx + 95, base - 66)], 12, tone=0.82, color='metal',
             seed=s + 6, taper=(0.1, 0.45), head=0.5, lift=0.2)
    pen.line([(cx + 48, base - 36), (cx + 78, base - 52), (cx + 93, base - 70)], 3, tone=0.8, seed=s + 12,
             taper=(0.1, 0.45))
    pen.dot(cx, base - 72, 7, 5, color='ink', tone=0.9, seed=s + 7)
    pen.line([(cx - 44, base - 52), (cx - 32, base - 100), (cx + 30, base - 100), (cx + 44, base - 52)], 7,
             tone=0.85, seed=s + 8, taper=(0.15, 0.2), head=0.5, lift=0.3, dry=0.6, dry_from=0.55, streak=0.3)
    pen.shade(ell(cx + 6, base + 2, 70, 6), amount=0.3, seed=s + 9, soft=4.0)


def _jar(pen):
    s = 600
    x0, x1, top, bot = 392, 462, CTR_BACK - 66, CTR_BACK + 16
    body = P([[x0 + 3, top + 12], [x1 - 3, top + 12], [x1, top + 22], [x1, bot - 4], [x1 - 6, bot],
              [x0 + 6, bot], [x0, bot - 4], [x0, top + 22]])
    pen.cover(body, seed=s, feather=0.8)
    pen.fill(body, 'glass', seed=s + 1)
    r = rng(s, 1)
    fill_top = top + 38
    for i in range(72):
        bx = r.uniform(x0 + 6, x1 - 6)
        by = r.uniform(fill_top + 3 * math.sin(bx * 0.2), bot - 5)
        rot = r.uniform(0, 180)
        pen.dot(bx, by, 4.3, 3.1, color='bean', tone=1.0, seed=(s, 10 + i), rot=rot)
    for i in range(22):
        hx, hy = r.uniform(x0 + 8, x1 - 8), r.uniform(fill_top + 6, bot - 8)
        pen.lift(ell(hx, hy, 1.3, 0.9, n=6), amt=0.8, seed=(s, 100 + i), soft=0.3)
    pen.shade(P([[x0 + 2, fill_top + 4], [x1 - 2, fill_top + 4], [x1 - 2, bot - 2], [x0 + 2, bot - 2]]),
              amount=0.15, seed=s + 2)
    pen.line(D([(x0, top + 22), (x0 - 1, (top + bot) / 2), (x0, bot - 4), (x0 + 8, bot)], 12), 5, tone=0.8,
             seed=s + 3, taper=(0.1, 0.25), head=0.5, lift=0.2)
    pen.line([(x1, top + 22), (x1 + 1, (top + bot) / 2 + 10), (x1, bot - 4), (x1 - 8, bot)], 3, tone=0.55,
             seed=s + 4, taper=(0.1, 0.4), head=0.1, dry=0.6, dry_from=0.3)
    pen.line([(x0 + 6, bot + 1), ((x0 + x1) / 2, bot + 3), (x1 - 6, bot + 1)], 3.5, tone=0.6, seed=s + 5,
             taper=(0.1, 0.2), head=0.2)
    pen.lift(tube([(x0 + 10, top + 26), (x0 + 9, bot - 14)], [2.5, 2.5])[0], amt=0.85, seed=s + 6, soft=1.0)
    pen.lift(tube([(x1 - 12, top + 30), (x1 - 12, top + 46)], [1.5, 1.5])[0], amt=0.85, seed=s + 7, soft=1.0)
    lid = P([[x0 + 2, top], [x1 - 2, top], [x1 - 1, top + 12], [x0 + 1, top + 12]])
    pen.cover(lid, seed=s + 10, feather=0.8)
    pen.fill(lid, 'wood_d', seed=s + 8)
    pen.line([(x0 - 1, top + 1), (x1 + 1, top)], 5, tone=0.88, seed=s + 9, taper=(0.1, 0.2), head=0.5)


def _beans_scatter(pen):
    s = 700
    pts = [(486, 628, 20), (503, 634, -15), (521, 626, 40), (540, 638, 10), (866, 640, -30), (889, 633, 25),
           (905, 643, 60), (466, 640, 80)]
    for i, (x, y, a) in enumerate(pts):
        pen.shade(ell(x + 2, y + 3.5, 5.5, 1.6, n=10), amount=0.35, seed=(s, 60 + i), soft=1.2)
        pen.dot(x, y, 5.2, 3.6, color='bean', tone=1.0, seed=(s, i), rot=a)
        pen.dot(x + 1, y + 1.2, 3.8, 2.2, color='bean_d', tone=1.0, seed=(s, 20 + i), rot=a)
        pen.lift(ell(x - 1.6, y - 1.0, 1.4, 0.9, n=6), amt=0.85, seed=(s, 40 + i), soft=0.3)


def _stove_pot(pen, night=False):
    s = 800
    box = P([[688, 602], [852, 602], [858, 638], [682, 638]])
    pen.cover(box, seed=s + 30, feather=0.8)
    pen.fill(box, 'metal', seed=s, grad=(680, 0, 860, 0, 0.6, 1.0))
    pen.line(D([(684, 602), (770, 600), (856, 602)], 16), 6, tone=0.85, seed=s + 1, taper=(0.1, 0.2), head=0.5)
    pen.line(D([(680, 639), (770, 641), (860, 638)], 16), 7, tone=0.88, seed=s + 2, taper=(0.1, 0.15), head=0.5,
             dry=0.4, dry_from=0.7)
    pen.line([(688, 603), (683, 637)], 4, tone=0.7, seed=s + 3, taper=(0.1, 0.2), head=0.2)
    pen.line([(852, 603), (858, 637)], 4, tone=0.7, seed=s + 4, taper=(0.1, 0.2), head=0.2)
    pen.dot(830, 620, 8, 8, color='ink', tone=0.75, seed=s + 5)
    pen.lift(ell(828, 618, 2.2, 2.2, n=6), amt=0.8, seed=s + 6, soft=0.3)
    # 小火苗（蓝）；深夜火关了
    for i, x in enumerate(range(728, 820, 13) if not night else ()):
        pen.line([(x, 601), (x + 2, 594), (x - 1, 587)], 3.5, tone=0.35, color='night_l', seed=s + 10 + i,
                 taper=(0.1, 0.8), role='detail')
    # 锅：深色搪瓷小锅，锅身一笔干笔提白
    cx, ry_, rx_ = POT['cx'], POT['ry'], POT['rx']
    rim_y, bot = POT['rim_y'], POT['bot']
    body = np.vstack([P([[cx + rx_, rim_y]]), P([[cx + rx_ - 5, bot - 6]]), ell(cx, bot - 6, rx_ - 5, 8, 0, 180, 16),
                      P([[cx - rx_, rim_y]]), ell(cx, rim_y, rx_, ry_, 180, 0, 20)])
    pen.shade(P([[cx - 60, bot - 6], [cx + 60, bot - 6], [cx + 56, 604], [cx - 56, 604]]), amount=0.4,
              seed=s + 26)
    pen.cover(body, seed=s + 31, feather=0.8)
    pen.fill(body, POT_COL, seed=s + 20, grad=(cx - rx_, 0, cx + rx_, 0, 0.85, 1.0))
    pen.shade(np.vstack([P([[cx + 10, rim_y + 4]]), P([[cx + rx_, rim_y]]), P([[cx + rx_ - 5, bot - 6]]),
                         ell(cx, bot - 6, rx_ - 5, 8, 0, 80, 8)]), amount=0.35, seed=s + 27)
    pen.lift(tube([(cx - 44, rim_y + 18), (cx - 43, (rim_y + bot) / 2), (cx - 41, bot - 9)], [3, 7, 3])[0],
             amt=0.5, seed=s + 21, soft=1.5, dry=0.7, streak=0.5)
    pen.line(ell(cx, rim_y, rx_, ry_, 0, 180, 18), 6.5, tone=0.95, seed=s + 22, taper=(0.1, 0.15), head=0.5)
    pen.line(ell(cx, rim_y, rx_, ry_, 180, 360, 18), 3.5, tone=0.8, seed=s + 23, taper=(0.1, 0.15), head=0.2)
    # 锅柄（朝右）
    pen.line([(cx + rx_ - 4, rim_y + 7), (cx + rx_ + 40, rim_y), (cx + rx_ + 88, rim_y - 10)], 13, tone=0.9,
             color='wood_d', seed=s + 25, taper=(0.05, 0.15), head=0.6, lift=0.25, dry=0.4, dry_from=0.75,
             streak=0.25)


def _lamp(pen, night=False):
    s = 900
    lx, ly = LAMP
    pen.line(D([(lx + 1, -5), (lx, 60), (lx, ly)], 30), 3.2, tone=0.75, seed=s, taper=(0.0, 0.05), head=0)
    shade = P([[lx - 20, ly - 2], [lx + 20, ly - 2], [lx + 44, ly + 16], [lx + 86, ly + 52],
               [lx - 86, ly + 52], [lx - 44, ly + 16]])
    shade = spline(shade, 3.0, closed=True)
    pen.cover(shade, seed=s + 10, feather=0.8)
    pen.fill(shade, 'lampshade', seed=s + 1, grad=(lx - 86, 0, lx + 86, 0, 1.0, 0.8))
    pen.shade(P([[lx + 10, ly - 2], [lx + 20, ly - 2], [lx + 44, ly + 16], [lx + 86, ly + 52], [lx + 30, ly + 52]]),
              amount=0.3, seed=s + 11)
    pen.lift(tube([(lx - 12, ly + 6), (lx - 40, ly + 32), (lx - 62, ly + 48)], [4, 9, 4])[0], amt=0.55,
             seed=s + 2, soft=1.5, dry=0.75, streak=0.5)
    pen.line(D([(lx - 92, ly + 53), (lx, ly + 58), (lx + 92, ly + 52)], 20), 9, tone=0.92, seed=s + 5,
             taper=(0.06, 0.2), head=0.6, lift=0.3, dry=0.35, dry_from=0.75)
    pen.line(ell(lx, ly + 62, 18, 12, 15, 165, 10), 2.8, tone=0.5, seed=s + 6, taper=(0.2, 0.4), head=0)
    # 灯光：水墨里是留白，水彩/油画棒是一团暖光（深夜灯关着）
    if not night:
        pen.light(lx, ly + 150, 300, 230, amt=0.45, color='lamp', seed=s + 8)


def _calendar(pen):
    s = 1000
    x0, y0, x1, y1 = 1102, 212, 1214, 362
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
    # 月份：一笔“十二”
    pen.line([(x0 + 30, y0 + 31), (x0 + 50, y0 + 29)], 4, tone=0.85, seed=s + 8, taper=(0.2, 0.35), head=0.5,
             role='detail')
    pen.line([(x0 + 40, y0 + 22), (x0 + 40, y0 + 43)], 3.8, tone=0.85, seed=s + 9, taper=(0.2, 0.4), head=0.5,
             role='detail')
    pen.line([(x0 + 60, y0 + 26), (x0 + 74, y0 + 25)], 3.6, tone=0.85, seed=s + 10, taper=(0.2, 0.35), head=0.5,
             role='detail')
    pen.line([(x0 + 57, y0 + 39), (x0 + 79, y0 + 37)], 4, tone=0.85, seed=s + 11, taper=(0.2, 0.35), head=0.5,
             role='detail')
    gx0, gy0 = x0 + 12, y0 + 58
    for r_ in range(5):
        for c in range(7):
            xx, yy = gx0 + c * 13.5, gy0 + r_ * 18
            k = r_ * 7 + c
            pen.line([(xx - 2.5, yy), (xx + 2.5, yy + 0.5)], 2.2, tone=0.42 + 0.25 * (c >= 5), seed=(s, 20 + k),
                     taper=(0.2, 0.3), head=0.2, role='detail', boil=0.15)
    # 被红笔圈起来的那一天
    cx, cy = gx0 + 4 * 13.5, gy0 + 3 * 18
    loop = [(cx + 9, cy - 5), (cx + 2, cy - 9), (cx - 8, cy - 6), (cx - 10, cy + 3), (cx - 3, cy + 9),
            (cx + 8, cy + 7), (cx + 11, cy - 1), (cx + 6, cy - 9), (cx - 1, cy - 11)]
    pen.line(loop, 3.4, tone=1.0, color='mark', seed=s + 60, taper=(0.15, 0.4), head=0.4, dry=0.35, dry_from=0.7,
             role='detail', boil=0.25)


def _fridge(pen):
    s = 1100
    x0 = FRIDGE_X
    side = P([[x0 + 4, 192], [1920, 192], [1920, 760], [x0 + 4, 760]])
    pen.cover(side, seed=s + 40)
    pen.fill(side, 'fridge', seed=s + 4, grad=(0, 360, 0, 760, 1.0, 0.0))
    pen.shade(P([[x0 + 4, 192], [x0 + 40, 192], [x0 + 40, 760], [x0 + 4, 760]]), amount=0.15, seed=s + 41,
              grad=(0, 300, 0, 760, 1.0, 0.0))
    pen.line(D([(x0 + 2, 186), (x0 - 3, 400), (x0 + 1, 580), (x0 - 2, 740)], 30), 12, tone=0.80, seed=s,
             taper=(0.04, 0.55), head=0.6, lift=0.3, dry=0.85, dry_from=0.4, streak=0.35, fade=0.5)
    pen.line(D([(x0 - 8, 190), (x0 + 30, 184), (1890, 187), (1930, 183)], 20), 11, tone=0.80, seed=s + 1,
             taper=(0.05, 0.0), head=0.6, lift=0.2, dry=0.4, dry_from=0.7)
    pen.line(D([(x0 + 6, 452), (1890, 455), (1925, 450)], 20), 5.5, tone=0.6, seed=s + 2, taper=(0.1, 0.0),
             head=0.3, dry=0.5, dry_from=0.5)
    pen.line(D([(x0 + 18, 478), (x0 + 16, 548), (x0 + 18, 616)], 20), 8, tone=0.85, color='metal', seed=s + 3,
             taper=(0.2, 0.3), head=0.6, lift=0.2)
    # 门上贴的照片（两个人影的草草几笔）：冰箱挪到画面右边缘后只露出一条，照片也小一点
    px0, py0, px1, py1 = x0 + 12, 256, x0 + 70, 330
    ph = P([[px0, py0 + 3], [px1, py0], [px1 + 2, py1], [px0 + 1, py1 + 2]])
    pen.cover(ph, seed=s + 5, feather=0.8)
    pen.fill(ph, 'cloth', seed=s + 6)
    pen.fill(P([[px0 + 6, py0 + 8], [px1 - 6, py0 + 6], [px1 - 4, py1 - 6], [px0 + 7, py1 - 4]]), 'sky',
             seed=s + 7, tone=0.06)
    pen.line(D([(px0, py0 + 3), (px1, py0), (px1 + 2, py1)], 16), 2.6, tone=0.62, seed=s + 10, taper=(0.1, 0.2),
             head=0.2)
    pen.line(D([(px1 + 2, py1), (px0 + 1, py1 + 2), (px0, py0 + 3)], 16), 3.0, tone=0.7, seed=s + 11,
             taper=(0.1, 0.2), head=0.3)
    for i, hx in enumerate([px0 + 19, px0 + 40]):
        pen.line(ell(hx, 282 + i * 2, 6, 7.5, 0, 330, 10), 2.0, tone=0.42, seed=s + 20 + i, taper=(0.1, 0.3),
                 head=0, role='detail', boil=0.2)
        pen.line([(hx - 9, 322), (hx - 7, 296 + i * 2), (hx + 7, 296 + i * 2), (hx + 9, 322)], 2.0, tone=0.38,
                 seed=s + 22 + i, taper=(0.1, 0.1), head=0, role='detail', boil=0.2)
    pen.dot((px0 + px1) / 2, py0 - 2, 6, 5, color='ink', tone=0.85, seed=s + 30)


def _table_chairs(pen):
    s = 1200
    cx, cy, rx, ry = TABLE['cx'], TABLE['cy'], TABLE['rx'], TABLE['ry']
    # 远处他的椅子：椅背在桌后露出（草稿的他是透明的，椅子透过他看得见；上色的他会挡住椅背）
    rail = P([[1304, 541], [1476, 540], [1476, 556], [1304, 557]])
    pen.cover(rail, seed=s + 40)
    pen.fill(rail, 'wood', seed=s + 41)
    for i, x in enumerate([1318, 1462]):
        post = P([[x - 4, 548], [x + 4, 548], [x + 4, cy - ry + 6], [x - 4, cy - ry + 6]])
        pen.fill(post, 'wood_d', seed=s + 42 + i)
        pen.line(D([(x, 546), (x + 1, 580), (x + 1, cy - ry + 6)], 16), 6, tone=0.5, seed=s + i, taper=(0.1, 0.15),
                 head=0.4, dry=0.4, dry_from=0.6)
    pen.line(D([(1304, 549), (1390, 541), (1476, 548)], 20), 11, tone=0.55, color='wood_d', seed=s + 2,
             taper=(0.1, 0.2), head=0.5, lift=0.3, dry=0.5, dry_from=0.6, streak=0.3)
    # 桌腿（中心柱）：向下渐淡，不落地，给歌词留白
    leg = P([[cx - 13, cy + ry - 4], [cx + 13, cy + ry - 4], [cx + 11, 850], [cx - 11, 850]])
    pen.fill(leg, 'wood_d', seed=s + 5, grad=(0, 720, 0, 845, 1.0, 0.0))
    pen.line(D([(cx - 13, cy + ry), (cx - 12, 770), (cx - 13, 850)], 20), 7, tone=0.8, seed=s + 6,
             taper=(0.05, 0.7), head=0.4, dry=0.85, dry_from=0.3, streak=0.35, fade=0.5)
    pen.line(D([(cx + 13, cy + ry), (cx + 12, 760), (cx + 12, 820)], 20), 4, tone=0.55, seed=s + 7,
             taper=(0.05, 0.7), head=0.1, dry=0.8, dry_from=0.3)
    # 桌面
    topp = ell(cx, cy, rx, ry, 0, 360, 64)
    edge = np.vstack([ell(cx, cy, rx, ry, 0, 180, 30), ell(cx, cy + 14, rx, ry, 180, 0, 30)])
    pen.cover([topp, edge], seed=s + 8, feather=0.8)
    pen.fill(edge, 'wood_d', seed=s + 11)
    pen.fill(topp, 'wood', seed=s + 9, grad=(cx - rx, 0, cx + rx, 0, 0.8, 1.0))
    pen.hatch(topp, angle=3, spacing=8, tone=0.16, color='wood_d', seed=s + 10, partial=0.45, bow=0.03)
    pen.light(cx - 70, cy - 8, 130, 32, amt=0.5, color='lamp', seed=s + 15)
    pen.line(ell(cx, cy, rx, ry, -10, 190, 40), 11, tone=0.92, color='wood_d', seed=s + 12, taper=(0.04, 0.12),
             head=0.7, lift=0.35, dry=0.5, dry_from=0.8, streak=0.3, pool=0.2)
    pen.line(ell(cx, cy, rx, ry, 195, 345, 30), 4, tone=0.55, color='wood_d', seed=s + 13, taper=(0.1, 0.4),
             head=0.2, dry=0.75, dry_from=0.3, streak=0.3)
    pen.line(ell(cx, cy + 14, rx, ry, 12, 168, 30), 6, tone=0.78, color='wood_d', seed=s + 14, taper=(0.1, 0.3),
             head=0.4, dry=0.5, dry_from=0.6)
    # 近处她的空椅子（左前）：几笔，椅腿淡出到纸
    c0 = 1078
    for i, (a, b) in enumerate([((c0 + 4, 798), (c0 + 2, 880)), ((c0 + 148, 788), (c0 + 152, 870)),
                                ((c0 + 124, 756), (c0 + 130, 830))]):
        pen.line(D([a, b], 16), 8 - 3 * (i == 2), tone=0.75 - 0.25 * (i == 2), color='wood_d', seed=s + 23 + i,
                 taper=(0.05, 0.7), head=0.4, dry=0.9, dry_from=0.25, streak=0.35, fade=0.5)
    seat = P([[c0 - 6, 760], [c0 + 128, 750], [c0 + 152, 784], [c0 + 6, 796]])
    pen.cover(seat, seed=s + 20, feather=0.8)
    pen.fill(seat, 'wood', seed=s + 27)
    pen.fill(P([[c0 - 6, 762], [c0 + 6, 796], [c0 + 152, 785], [c0 + 152, 792], [c0 + 6, 803], [c0 - 6, 768]]),
             'wood_d', seed=s + 28)
    pen.line(D([(c0 - 6, 760), (c0 + 128, 750), (c0 + 152, 784)], 16), 6, tone=0.85, color='wood_d',
             seed=s + 21, taper=(0.1, 0.2), head=0.5, lift=0.2)
    pen.line(D([(c0 - 6, 762), (c0 + 6, 796), (c0 + 152, 785)], 16), 8, tone=0.88, color='wood_d', seed=s + 22,
             taper=(0.1, 0.15), head=0.6, lift=0.3, dry=0.3, dry_from=0.75)
    for i, (a, b) in enumerate([((c0 + 2, 762), (c0 - 8, 610)), ((c0 + 124, 752), (c0 + 120, 600))]):
        pen.line(D([a, b], 16), 8, tone=0.85, color='wood_d', seed=s + 30 + i, taper=(0.1, 0.15), head=0.5,
                 lift=0.3, dry=0.3, dry_from=0.7)
    for i, x in enumerate([c0 + 26, c0 + 56, c0 + 88]):
        pen.line([(x, 640 - 0.18 * (x - c0)), (x + 1, 752 - 0.07 * (x - c0))], 4, tone=0.55, color='wood_d',
                 seed=s + 35 + i, taper=(0.1, 0.2), head=0.3, dry=0.6, dry_from=0.5)
    back = P([[c0 - 12, 606], [c0 + 56, 592], [c0 + 126, 596], [c0 + 124, 632], [c0 + 56, 628], [c0 - 10, 642]])
    pen.cover(back, seed=s + 38, feather=0.8)
    pen.fill(back, 'wood', seed=s + 32, grad=(c0, 0, c0 + 126, 0, 1.0, 0.75))
    pen.shade(P([[c0 - 10, 626], [c0 + 56, 614], [c0 + 124, 618], [c0 + 124, 632], [c0 + 56, 628],
                 [c0 - 10, 642]]), amount=0.3, seed=s + 39)
    pen.line(D([(c0 - 14, 607), (c0 + 56, 591), (c0 + 128, 596)], 16), 8, tone=0.9, color='wood_d', seed=s + 33,
             taper=(0.1, 0.15), head=0.6, lift=0.3, dry=0.3, dry_from=0.75)
    pen.line(D([(c0 - 10, 642), (c0 + 56, 628), (c0 + 124, 632)], 16), 4.5, tone=0.65, color='wood_d',
             seed=s + 34, taper=(0.1, 0.3), head=0.2, dry=0.5, dry_from=0.5)


# ================================================================= 门（右侧墙上；第 1 镜关着，第 8 镜他从这里出去）
def leaf_quad(theta):
    """门扇转开 theta 度（往外开、合页在左）时的四个角：左上、右上、右下、左下（场景坐标）。
    自由边往外转、离我们远了：以视平线为中心收缩一点。"""
    x0, x1, top, fl = DOOR['x0'], DOOR['x1'], DOOR['top'], DOOR['floor']
    th = math.radians(theta)
    k = 1.0 - 0.16 * math.sin(th)
    xf = x0 + (x1 - x0) * math.cos(th)
    return P([[x0, top], [xf, HORIZON + (top - HORIZON) * k], [xf, HORIZON + (fl - HORIZON) * k], [x0, fl]])


def leaf_pt(q, u, v):
    a = q[0] + (q[1] - q[0]) * u
    b = q[3] + (q[2] - q[3]) * u
    return a + (b - a) * v


def leaf_rect(q, u0, v0, u1, v1):
    return np.float32([leaf_pt(q, u0, v0), leaf_pt(q, u1, v0), leaf_pt(q, u1, v1), leaf_pt(q, u0, v1)])


def knob_pt(theta):
    return leaf_pt(leaf_quad(theta), 0.885, 0.47)


_TSIL = None


def table_sil():
    """桌子的剪影（桌面 + 桌沿厚度 + 中心柱），shapely 多边形。门和他在桌子后面，要被它挡住。"""
    global _TSIL
    if _TSIL is None:
        from shapely.geometry import Polygon as SP
        cx, cy, rx, ry = TABLE['cx'], TABLE['cy'], TABLE['rx'], TABLE['ry']
        top = SP(ell(cx, cy, rx + 5, ry + 5, 0, 360, 72))
        edge = SP(np.vstack([ell(cx, cy, rx + 5, ry + 5, 0, 180, 36), ell(cx, cy + 17, rx + 5, ry + 5, 180, 0, 36)]))
        leg = SP(rect(cx - 15, cy + ry - 8, cx + 15, 860))
        _TSIL = top.union(edge).union(leg).buffer(0)
    return _TSIL


def behind_table(polys):
    """多边形减去桌子剪影 → 多边形列表。"""
    from shapely.geometry import Polygon as SP
    out = []
    for p in polys:
        g = SP(np.asarray(p, np.float64)).buffer(0).difference(table_sil())
        for q in getattr(g, 'geoms', [g]):
            if q.geom_type == 'Polygon' and q.area > 2:
                out.append(np.asarray(q.exterior.coords, np.float32)[:-1])
    return out


def behind_table_line(pts):
    """线（先样条化）减去桌子剪影 → 线段列表。"""
    from shapely.geometry import LineString as SL
    sp = spline(np.float32(pts), 3.0)
    g = SL(np.asarray(sp, np.float64)).difference(table_sil())
    out = []
    for q in getattr(g, 'geoms', [g]):
        if q.geom_type == 'LineString' and q.length > 6:
            out.append(np.asarray(q.coords, np.float32))
    return out


_KEY = {}


def table_keyhole(under=False):
    """整个画面减去桌子剪影的“钥匙孔”多边形（给 clip_poly：他在桌子后面）。
    under=True：桌面以下（桌子底下暗处）也挡住——他坐着/起身时不画桌下的腿。"""
    if under in _KEY:
        return _KEY[under]
    geo = table_sil()
    if under:
        from shapely.geometry import Polygon as SP
        geo = geo.union(SP(rect(1080, 650, 1640, H + 40))).buffer(0)
    ext = np.asarray(geo.exterior.coords, np.float32)[:-1]
    i = int(np.argmin(ext[:, 0]))
    ring = np.vstack([ext[i:], ext[:i + 1]])
    lx, ly = ring[0]
    frame = P([[-60, ly], [-60, -60], [W + 60, -60], [W + 60, H + 60], [-60, H + 60], [-60, ly]])
    _KEY[under] = np.vstack([frame, ring, [[-60, ly]]]).astype(np.float32)
    return _KEY[under]


def _door_frame(pen, night=False):
    """门套（左、右、上三条木框）+ 墙上的电灯开关。门洞本身由 _door_leaf / door_outside 画。"""
    s = 1400
    x0, x1, top, fl = DOOR['x0'], DOOR['x1'], DOOR['top'], DOOR['floor']
    cw = 18
    left = P([[x0 - cw, top - cw], [x0, top - cw + 2], [x0, fl], [x0 - cw, fl]])
    right = P([[x1, top - cw + 2], [x1 + cw, top - cw], [x1 + cw, fl], [x1, fl]])
    lint = P([[x0 - cw - 8, top - cw - 10], [x1 + cw + 8, top - cw - 10], [x1 + cw, top], [x0 - cw, top]])
    for i, q in enumerate((left, right, lint)):
        pen.cover(q, seed=s + i, feather=0.8)
        pen.fill(q, 'wood', seed=s + 4 + i, tone=0.34, grad=(0, top - 30, 0, fl, 1.0, 0.12), c_fade=False)
    # 门洞内侧的进深（左边一窄条阴影：门是嵌在墙里的）
    pen.shade(P([[x0, top], [x0 + 9, top + 6], [x0 + 9, fl], [x0, fl]]), amount=0.35, seed=s + 8, angle=90,
              hatch=False)
    pen.shade(P([[x0, top], [x1, top], [x1 - 6, top + 9], [x0 + 6, top + 9]]), amount=0.35, seed=s + 9, angle=0,
              hatch=False)
    # 线：左框外沿、门楣两笔浓（起笔顿、收笔飞白），右框淡而断，下端都淡出到纸
    pen.line(D([(x0 - cw - 2, top - cw - 12), (x0 - cw, 520), (x0 - cw + 1, fl - 10)], 30), 12, tone=0.9,
             color='wood_d', seed=s + 10, taper=(0.04, 0.5), head=0.6, lift=0.3, dry=0.6, dry_from=0.55,
             streak=0.3, fade=0.55)
    pen.line(D([(x0 + 1, top + 2), (x0, 560), (x0 + 1, fl - 30)], 30), 4.5, tone=0.62, color='wood_d', seed=s + 11,
             taper=(0.05, 0.6), head=0.2, dry=0.6, dry_from=0.45, fade=0.5)
    pen.line(D([(x0 - cw - 16, top - cw - 11), (1680, top - cw - 14), (x1 + cw + 16, top - cw - 10)], 30), 14,
             tone=0.9, color='wood_d', seed=s + 12, taper=(0.04, 0.2), head=0.7, lift=0.3, dry=0.55, dry_from=0.6,
             streak=0.3, pool=0.2)
    pen.line(D([(x0 - cw, top + 1), (x1 + cw, top - 1)], 30), 4, tone=0.6, color='wood_d', seed=s + 13,
             taper=(0.1, 0.3), head=0.2, dry=0.5, dry_from=0.5)
    pen.line(D([(x1 + cw + 1, top - cw - 8), (x1 + cw - 1, 520), (x1 + cw + 1, fl - 40)], 30), 7, tone=0.62,
             color='wood_d', seed=s + 14, taper=(0.05, 0.6), head=0.3, dry=0.8, dry_from=0.3, streak=0.3, fade=0.55)
    pen.line(D([(x1 - 1, top + 2), (x1, 560), (x1 - 1, fl - 30)], 30), 3.5, tone=0.5, color='wood_d', seed=s + 15,
             taper=(0.05, 0.6), head=0.1, dry=0.7, dry_from=0.35, fade=0.5)


def _door_leaf(pen, theta, night=False, clip=False):
    """门扇。theta 0 = 关着；往外转开时自由边往左收、变窄，背光一侧变暗。clip=True：减去桌子剪影（动态层画在桌子之后时）。"""
    s = 1450
    x0, x1 = DOOR['x0'], DOOR['x1']
    q = leaf_quad(theta)
    sn = math.sin(math.radians(theta))
    if abs(float(q[1, 0] - q[0, 0])) < 3:
        return
    cp = behind_table if clip else (lambda ps: ps)
    cl = (lambda pts: behind_table_line(D(pts, 16))) if clip else (lambda pts: [D(pts, 16)])
    body = cp([q])
    if not body:
        return
    pen.cover(body, seed=s, feather=0.8)
    pen.fill(body, 'wood', seed=s + 1, tone=0.20 + 0.12 * night, grad=(0, DOOR['top'], 0, DOOR['floor'], 1.0, 0.25))
    if theta > 0.5:
        pen.shade(body, amount=0.12 + 0.45 * sn, seed=s + 2, angle=82, hatch=sn > 0.3)
    # 两块凹进去的门板：上沿、左沿一道影（斜面），内框一笔细线
    for k, (u0, v0, u1, v1) in enumerate([(0.16, 0.07, 0.84, 0.46), (0.16, 0.54, 0.84, 0.93)]):
        bev = cp([np.vstack([leaf_rect(q, u0, v0, u1, v0)[:2], leaf_pt(q, u1 - 0.03, v0 + 0.022)[None],
                             leaf_pt(q, u0 + 0.03, v0 + 0.022)[None]]),
                  np.vstack([leaf_pt(q, u0, v0)[None], leaf_pt(q, u0 + 0.03, v0 + 0.022)[None],
                             leaf_pt(q, u0 + 0.03, v1 - 0.01)[None], leaf_pt(q, u0, v1)[None]])])
        if bev:
            pen.shade(bev, amount=0.32, seed=s + 10 + k, hatch=False)
        rr = leaf_rect(q, u0, v0, u1, v1)
        for j, seg in enumerate(cl(np.vstack([rr, rr[:1]]))):
            pen.line(seg, 3.0, tone=0.58, color='wood_d', seed=(s + 20 + k, j), taper=(0.08, 0.15), role='detail',
                     head=0.3, dry=0.45, dry_from=0.6, split=False)
        ri = leaf_rect(q, u0 + 0.03, v0 + 0.022, u1 - 0.03, v1 - 0.01)
        for j, seg in enumerate(cl(np.vstack([ri, ri[:1]]))):
            pen.line(seg, 1.8, tone=0.36, color='wood_d', seed=(s + 30 + k, j), taper=(0.1, 0.2), role='detail',
                     dry=0.5, dry_from=0.4, split=False)
    # 边：合页边一笔浓、自由边（转开后露出门的厚度）
    for j, seg in enumerate(cl(D([q[0], q[3]], 30))):
        pen.line(seg, 6, tone=0.8, color='wood_d', seed=(s + 40, j), taper=(0.05, 0.4), head=0.4, dry=0.5,
                 dry_from=0.6, fade=0.4)
    pen.line(D([q[0], q[1]], 30), 5, tone=0.75, color='wood_d', seed=s + 41, taper=(0.1, 0.2), head=0.3)
    edge_w = 4 + 10 * sn
    for j, seg in enumerate(cl(D([q[1], q[2]], 30))):
        pen.line(seg, edge_w * 0.6 + 3, tone=0.85, color='wood_d', seed=(s + 42, j), taper=(0.05, 0.4), head=0.5,
                 dry=0.5, dry_from=0.6, fade=0.4)
    # 门把手（圆球）+ 锁孔
    kx, ky = leaf_pt(q, 0.885, 0.47)
    kr = 9.0 * (1.0 - 0.45 * sn)
    pen.shade(ell(kx + 3, ky + 7, kr * 1.2, 3.5), amount=0.3, seed=s + 50, soft=2.0, hatch=False)
    pen.dot(kx, ky, kr, 8.5, color='metal', tone=0.72, seed=s + 51)
    pen.lift(ell(kx - kr * 0.3, ky - 2.5, kr * 0.3, 2.0, n=8), amt=0.8, seed=s + 52, soft=0.6)
    kx2, ky2 = leaf_pt(q, 0.885, 0.52)
    pen.dot(kx2, ky2, 2.2 * (1 - 0.4 * sn), 3.2, color='ink', tone=0.8, seed=s + 53)


def _night_veil(pen):
    """深夜：吊灯关了，整个屋子压一层淡墨；窗（雪光）四周和窗下的台面留一点亮；
    画面下沿淡出到纸（歌词留白），只有门前的地面保留一点暗（门开时冷光落在那里）。"""
    sc = 0.25
    h, w = int(H * sc), int(W * sc)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) / sc
    x0, y0, x1, y1 = GLASS
    dx = np.maximum(np.maximum(x0 - xs, xs - x1), 0)
    dy = np.maximum(np.maximum(y0 - ys, ys - y1), 0)
    win = np.exp(-(np.hypot(dx, dy * 0.8) / 95.0) ** 2)
    half = (x1 - x0) / 2 + 60 + np.maximum(ys - y1, 0) * 0.5
    below = np.clip(1 - np.abs(xs - (x0 + x1) / 2) / half, 0, 1) * (ys > y1) * np.exp(-((ys - y1) / 150.0) ** 2)
    m = 1.0 - 0.66 * win - 0.32 * below
    fade = sstep(760, 930, ys) * (1.0 - 0.6 * sstep(1420, 1580, xs))
    m = np.clip(m * (1.0 - 0.92 * fade), 0, 1)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    pen.fill(mask=(m, 0, 0), color='night', tone=0.44, seed=1500, c_fade=False, streak=0.15, sangle=4)


def background(pen, night=False):
    _window(pen)
    _plant(pen)
    _shelf_mugs(pen)
    _door_frame(pen, night)
    if not night:
        _door_leaf(pen, 0.0)
    _table_chairs(pen)
    _calendar(pen)
    _fridge(pen)
    _counter(pen)
    _kettle(pen)
    _jar(pen)
    _stove_pot(pen, night)
    _beans_scatter(pen)
    _lamp(pen, night)
    if night:
        _night_veil(pen)


# ================================================================= 动态元素
def snow(pen, t):
    x0, y0, x1, y1 = GLASS
    r = rng(1600)
    n = 95
    with pen.group('snow', boil=0.6):
        for i in range(n):
            far = i < 60
            sp = r.uniform(18, 34) if far else r.uniform(40, 70)
            size = r.uniform(1.0, 2.1) if far else r.uniform(2.2, 4.0)
            amp = r.uniform(3, 10)
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-20, x1 - x0 + 20)
            ys = r.uniform(0, y1 - y0 + 20)
            hh = y1 - y0 + 20
            yy = (ys + sp * t) % hh - 10 + y0
            xx = (xs + 7 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - x0 + 40) - 20 + x0
            # 只在玻璃里，避开窗棂、横棂、盆栽
            if not (x0 + 3 < xx < x1 - 3 and y0 + 3 < yy < y1 - 3):
                continue
            if abs(xx - MULL_X) < 8 + size or abs(yy - TRANS_Y) < 7 + size:
                continue
            if 812 < xx < 905 and 378 < yy < 512:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', i))


def steam(pen, t, amt=1.0):
    cx = POT['cx']
    per = 2.6
    with pen.group('steam', boil=0.8):
        for k in range(7):
            age = ((t + k * per / 7) % per) / per
            a = amt * math.sin(math.pi * age) ** 1.3
            if a < 0.03:
                continue
            cyc = math.floor((t + k * per / 7) / per)
            r = rng(1700, k, cyc)
            bx = cx + r.uniform(-30, 30)
            yb = POT['rim_y'] - 6 - age * 250
            L = 70 + 90 * age
            ys = np.linspace(yb, yb - L, 7)
            ph = r.uniform(0, 6.28)
            curl = r.uniform(10, 22) * (0.5 + age)
            xs = bx + curl * np.sin((ys - POT['rim_y']) * 0.03 + ph + t * 1.1) + (POT['rim_y'] - ys) * 0.05
            path = np.stack([xs, ys], 1).astype(np.float32)
            w = 6 + 9 * age
            poly, _, _ = tube(path, [w * 0.4, w, w * 0.7, w * 0.3])
            pen.lift(poly, amt=0.6 * a, seed=(1710, k, cyc), soft=5.0)
            pen.line(path, w * 0.5, tone=0.14 * a, color='metal', seed=(1720, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.55, dry_from=0.1)


def soup(pen, t, theta, tip):
    cx, cy, rx, ry = SOUP
    inner = ell(POT['cx'], POT['rim_y'] + 1.5, POT['rx'] - 5, POT['ry'] - 3, n=40)
    with pen.group('soup', boil=0.5):
        pen.fill(inner, 'soup', seed=1801)
        pen.shade(ell(cx, cy - 3, rx * 0.95, ry * 0.55, 180, 360, 16), amount=0.3, seed=1802, color='bean_d')
        # 汤面的旋涡亮纹（随搅动转）
        for k, (rr, a0, ln) in enumerate([(0.75, 0, 80), (0.48, 140, 70), (0.25, 260, 90)]):
            a = math.degrees(theta) * (1.0 - 0.15 * k) + a0
            pts = ell(cx, cy, rx * rr, ry * rr, a, a + ln, 8)
            pen.lift(tube(pts, [0.5, 1.4, 0.5])[0], amt=0.35, seed=1810 + k, soft=0.8)
        # 豆子
        r = rng(1820)
        for i in range(16):
            rr = r.uniform(0.15, 0.9)
            a = r.uniform(0, 2 * math.pi) + theta * (1.1 - 0.6 * rr)
            bx, by = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
            pen.dot(bx, by, 3.6, 2.4, color='bean', tone=1.0, seed=(1830, i), rot=math.degrees(a) * 0.3)
            pen.dot(bx + 0.6, by + 0.6, 2.8, 1.8, color='bean_d', tone=1.0, seed=(1860, i))
            if i % 3 == 0:
                pen.lift(ell(bx - 1.0, by - 0.7, 1.0, 0.7, n=6), amt=0.75, seed=(1890, i), soft=0.3)
        # 勺子入汤处的一圈小涟漪
        pen.lift(tube(ell(tip[0], tip[1] + 1, 9, 2.6, 200, 340, 8), [0.4, 0.9, 0.4])[0], amt=0.5, seed=1900,
                 soft=0.5)


def bowls(pen, what='two'):
    if what == 'none':
        return
    s = 1300
    with pen.group('bowls', boil=0.5):
        for i, (bx, by, sc) in enumerate([(1468, 630, 0.92), (1238, 672, 1.0)]):
            rx, ry = 44 * sc, 11 * sc
            body = np.vstack([ell(bx, by, rx, ry, 180, 360, 16), P([[bx + rx, by]]),
                              bez((bx + rx, by), (bx + rx * 0.9, by + 30 * sc), (bx + rx * 0.4, by + 32 * sc), 8),
                              bez((bx - rx * 0.4, by + 32 * sc), (bx - rx * 0.9, by + 30 * sc), (bx - rx, by), 8)])
            pen.shade(ell(bx + 8, by + 36 * sc, rx * 0.8, 5), amount=0.35, seed=s + 26 + i, soft=3.0)
            pen.cover(body, seed=s + 40 + i, feather=0.8)
            pen.fill(body, 'enamel', seed=s + i)
            pen.shade(np.vstack([P([[bx + rx * 0.2, by]]), P([[bx + rx, by]]),
                                 bez((bx + rx, by), (bx + rx * 0.9, by + 30 * sc), (bx + rx * 0.4, by + 32 * sc), 8)]),
                      amount=0.3, seed=s + 30 + i)
            if what == 'soup':
                pen.fill(ell(bx, by + 1, rx * 0.86, ry * 0.7), 'soup', seed=s + 50 + i)
                for k in range(5):
                    a = k * 1.7 + i
                    pen.dot(bx + rx * 0.45 * math.cos(a), by + 1 + ry * 0.35 * math.sin(a), 2.6, 1.8, color='bean',
                            tone=1.0, seed=(s, 60 + 5 * i + k))
            else:
                pen.shade(ell(bx + rx * 0.15, by + 1, rx * 0.75, ry * 0.65), amount=0.15, seed=s + 18 + i)
            pen.line(ell(bx, by, rx, ry, 0, 360, 22), 3.6, tone=0.82, seed=s + 10 + i, taper=(0.05, 0.1), head=0.3,
                     closed=True)
            pen.line(bez((bx - rx, by + 1), (bx - rx * 0.9, by + 30 * sc), (bx - rx * 0.35, by + 32 * sc), 8), 5,
                     tone=0.85, seed=s + 12 + i, taper=(0.1, 0.25), head=0.5, lift=0.2)
            pen.line(bez((bx + rx, by + 1), (bx + rx * 0.9, by + 30 * sc), (bx + rx * 0.35, by + 32 * sc), 8), 3,
                     tone=0.6, seed=s + 14 + i, taper=(0.1, 0.35), head=0.2, dry=0.5, dry_from=0.5)
            pen.line([(bx - rx * 0.4, by + 33 * sc), (bx, by + 35 * sc), (bx + rx * 0.4, by + 33 * sc)], 3.6,
                     tone=0.7, seed=s + 16 + i, taper=(0.1, 0.2), head=0.3)
            # 勺
            sx, sy = bx + rx + 12, by + 14
            sp = ell(sx + 10, sy + 2, 12, 6, 0, 360, 14)
            pen.shade(ell(sx + 14, sy + 10, 16, 3), amount=0.25, seed=s + 24 + i, soft=2.0)
            pen.cover(sp, seed=s + 44 + i, feather=0.7)
            pen.fill(sp, 'metal', seed=s + 46 + i)
            pen.line(ell(sx + 10, sy + 2, 12, 6, 0, 360, 14), 2.6, tone=0.75, seed=s + 20 + i, taper=(0, 0), head=0,
                     closed=True)
            pen.line([(sx + 20, sy - 1), (sx + 34, sy - 7), (sx + 48, sy - 9)], 5, tone=0.8, color='metal',
                     seed=s + 22 + i, taper=(0.1, 0.45), head=0.4)


def halo(pen, sil, amt=0.30):
    """水墨的“让”：画家在人物轮廓外留一圈白，夜色在她身边淡开（只在窗玻璃上）。"""
    import cv2
    x0, y0, x1, y1 = GLASS
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    for p in sil:
        q = np.asarray(p, np.float32) - (x0, y0)
        cv2.fillPoly(m, [np.round(q * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    sc = 0.25
    a = cv2.resize(m.astype(np.float32) / 255, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    a = cv2.GaussianBlur(a, (0, 0), 18 * sc * 0.6)
    a = np.clip(a * 1.5 - 0.1, 0, 1)
    a = cv2.resize(a, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    a[:, MULL_X - x0 - 7:MULL_X - x0 + 8] = 0
    a[TRANS_Y - y0 - 6:TRANS_Y - y0 + 7, :] = 0
    pen.lift(mask=(a, x0, y0), amt=amt, seed=1650, soft=2.0)


# ================================================================= 默认表演（成片时间；0.5 秒开唱“第十七句一句示”）
# 旧小样用原曲时间 T0=103.8；成片 0 秒 = 原曲 103.95。
def _sg(song):
    return song - 103.95


def stir_phase(t):
    """搅动相位：看向他时手慢下来（相位 = 角速度积分）。"""
    ts = np.linspace(-1.15, t, 240)
    slow = 1.0 - 0.45 * (np.clip((ts - _sg(105.2)) / 0.6, 0, 1) - np.clip((ts - _sg(106.9)) / 0.6, 0, 1))
    w = 2 * math.pi / 1.7 * slow
    return float(np.trapezoid(w, ts)) if hasattr(np, 'trapezoid') else float(np.trapz(w, ts))


def blink_amt(t):
    b = 0.0
    for tb in (_sg(104.62), _sg(106.18)):
        x = abs(t - tb) / 0.11
        b = max(b, 1.0 - x)
    return float(np.clip(b, 0, 1))


LOOKS = {'pot': (38, 21, 3), 'him': (46, 7, -5), 'down': (41, 27, 6)}


def girl_pose(t, kw=None):
    kw = kw or {}
    u1 = ease_io((t - _sg(105.2)) / 0.55)          # 抬头转向他
    uf = ease_io((t - _sg(105.35)) / 0.6)          # 笑意略晚于转头
    u2 = ease_io((t - _sg(106.75)) / 0.45)         # 笑淡下去，眼睛垂下
    down = np.float32(LOOKS['pot'])
    look = np.float32(LOOKS['him'])
    sad = np.float32(LOOKS['down'])
    yaw, pitch, roll = lerp(lerp(down, look, u1), sad, u2)
    look_pot = dict(EXPR['neutral'], open=0.45, gy=0.9, gx=0.15)     # 低头看锅：眼皮垂着
    face = mix_expr(mix_expr(look_pot, 'wistful_smile', uf), 'sad_down', u2)
    lean = 0.15 * (1 - u1) + 0.2 * u2
    gl = kw.get('girl_look')
    if gl is not None:
        yaw, pitch, roll = LOOKS[gl] if isinstance(gl, str) else gl
        lean = {'pot': 0.15, 'him': 0.0, 'down': 0.2}.get(gl, 0.1) if isinstance(gl, str) else 0.1
    if kw.get('girl_expr') is not None:
        face = kw['girl_expr']
    th = stir_phase(t) * float(kw.get('stir_speed', 1.0 / 1.7)) * 1.7
    pose = dict(x=560, y=448, s=110, facing=1, yaw=float(yaw), pitch=float(pitch), roll=float(roll),
                face=face, blink=float(kw.get('blink', blink_amt(t))), breath=(t + 0.15) / 3.4,
                clip_y=CTR_BACK, lean=float(lean), seed=1000, boil=GIRL_BOIL)
    if kw.get('stir', True) in (True, 1, 1.0, 'True', 'true'):
        pose.update(arm='stir', arm_t=0.0, arm_args=dict(soup=SOUP, period=1.0, t0=-th / (2 * math.pi)))
    else:
        pose.update(arm='rest', arm_args=dict(hand=(706, 600), shape='flat'))
    return pose, th


def boy_pose(t, kw=None):
    kw = kw or {}
    er = 0.78 * ease_io((t - _sg(107.4)) / 1.25)
    if kw.get('boy_erase') is not None:
        er = float(kw['boy_erase'])
    cx, cy, rx, ry = TABLE['cx'], TABLE['cy'], TABLE['rx'], TABLE['ry']
    # 桌面后沿以上可见（他坐在桌后；搁在桌上的手臂不裁）
    xs = np.linspace(cx + rx, cx - rx, 40)
    arc = np.stack([xs, cy - ry * np.sqrt(np.clip(1 - ((xs - cx) / rx) ** 2, 0, 1)) + 3], 1)
    vis = np.vstack([[[cx + rx + 600, -50], [cx + rx + 600, cy]], arc, [[cx - rx - 600, cy], [cx - rx - 600, -50]]])
    return dict(x=1418, y=508, s=126, facing=-1, yaw=36, pitch=-7, roll=7, face=kw.get('boy_expr', 'smile'),
                erase=er, clip_poly=vis.astype(np.float32), pose=kw.get('boy_pose', 'sit_chin'), seed=2000,
                breath=(t + 0.9) / 3.9), er


def boy_opacity(er):
    return 0.64 * (1.0 - 0.42 * er)


# ================================================================= 场景
def draw(pen, **kw):
    if kw.get('mode') == 'door':
        return draw_door(pen, **kw)
    t = float(kw.get('t', pen.t))
    cache = ('kitchen', pen.d % 3)
    if abs(pen.scale - 1.0) > 1e-6 or pen.to_screen(np.zeros((1, 2), np.float32))[0].any():
        o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
        cache = ('kitchen', pen.d % 3, round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))
    with pen.group('bg', boil=BG_BOIL, cache=cache):
        background(pen)
    snow(pen, t)
    # 他（在桌后）
    if kw.get('show_boy', True) not in (False, 0, 0.0, 'False', 'false'):
        bp, er = boy_pose(t, kw)
        mode = kw.get('boy_mode') or ('sketch' if pen.style == 'C' else 'full')
        bp['opacity'] = float(kw.get('boy_opacity', boy_opacity(er)))
        bp['boil'] = BOY_BOIL if mode == 'sketch' else 1.0
        if mode != 'sketch':
            bp['erase'] = 0.0
        boy(pen, bp, mode=mode)
    bowls(pen, kw.get('bowls', 'two'))
    # 她
    if kw.get('show_girl', True) not in (False, 0, 0.0, 'False', 'false'):
        gp, th = girl_pose(t, kw)
        halo(pen, girl_silhouette(gp))
        info = girl(pen, gp, parts=('body', 'head'))
        tip = None
        if gp.get('arm') == 'stir':
            from characters import ARM_POSES
            tip = ARM_POSES['stir'](0.0, gp['arm_args'])['near']['tool'][1]
        soup(pen, t, th, tip if tip is not None else np.float32(SOUP[:2]))
        girl(pen, gp, parts=('arm',))
    else:
        soup(pen, t, stir_phase(t), np.float32(SOUP[:2]))
    steam(pen, t)


# ================================================================= 第 8 镜（mode='door'，30.28–34.20，C）“第二十三句”
# 深夜，同一个厨房（吊灯关着、火关着，只有窗外的雪光）。草稿的他从桌边站起，走到右边的门口，拉开门：
# 门外是雪夜，风雪灌进来；“自”他迈出门，背影的线条被风吹散成雪，倒卷回屋里；“由”门慢慢合上，只剩一道缝。
# 她站在灶台边，一只手按在胸口，眼睛跟着他，没有追。
T8 = dict(r0=30.28, r1=30.95,          # 起身
          w1=31.20,                    # 侧面走一步
          b1=31.36,                    # 转成背影走到门口
          g1=31.48, o1=31.95,          # 抓门把手 → 门往外转开（“孤独”31.36–31.9）
          rel0=31.95, rel1=32.25,      # 手松开垂下
          lb0=32.12, lb1=32.62,        # 犹豫：头往她那边偏一点，又转回去
          x0=32.71, x1=33.45,          # “自”迈出门
          d0=33.00, d1=33.70,          # 线条被风吹散成雪
          c0=33.68, c1=34.20)          # “由”门慢慢合上
OPEN_DEG, CLOSE_DEG = 78.0, 10.0
WIND = (-1.0, -0.14)                   # 风从门外往屋里灌（往左、略往上）


def door_theta(t):
    if t < T8['g1']:
        return 0.0
    if t < T8['c0']:
        return OPEN_DEG * float(ease_out((t - T8['g1']) / (T8['o1'] - T8['g1'])))
    return OPEN_DEG + (CLOSE_DEG - OPEN_DEG) * float(ease_io((t - T8['c0']) / (T8['c1'] - T8['c0'])))


def door_open(theta):
    """门开了多少（0..1，按露出来的门洞宽度）：冷光、灌进来的风雪都按它。"""
    q = leaf_quad(theta)
    return float(clamp((DOOR['x1'] - q[1, 0]) / (DOOR['x1'] - DOOR['x0'])))


def girl_door_pose(t):
    look = float(ease_io((t - 30.85) / 0.75))          # 眼睛、头跟着他移向门口
    pain = float(ease_io((t - 32.72) / 0.60))          # 他迈出去：眉头揪起来，眼里含泪
    low = float(ease_io((t - 33.72) / 0.45))           # 门合上：慢慢垂下眼
    wid = math.sin(math.pi * clamp((t - 31.50) / 0.60))  # 门打开的一瞬，眼睛微微睁大
    f0 = dict(EXPR['sad_down'], open=0.64, gx=0.36, gy=0.0, smile=-0.10, brow=0.50, brow_out=0.30, wet=0.55,
              blush=0.40)
    f1 = dict(f0, gx=0.66, gy=0.04)
    f2 = dict(f1, brow=0.88, brow_out=0.45, wet=1.0, smile=-0.32, mouth_open=0.07, open=0.58)
    f3 = dict(f2, gy=0.55, gx=0.42, open=0.40)
    face = mix_expr(mix_expr(mix_expr(f0, f1, look), f2, pain), f3, low)
    face['open'] = face['open'] + 0.12 * wid * (1 - pain)
    blink = float(np.clip(1.0 - abs(t - 32.08) / 0.10, 0, 1))
    hand = float(ease_io((t - 30.36) / 0.60))
    return dict(x=560, y=448, s=110, facing=1, yaw=46.0 + 9.0 * look, pitch=5.0 - 2.0 * look + 7.0 * low,
                roll=-4.0 + 3.0 * low, face=face, blink=blink, breath=(t + 0.15) / 3.4, clip_y=CTR_BACK,
                lean=0.04 + 0.04 * low, seed=1000, boil=GIRL_BOIL, arm=None, chest_u=hand)


def girl_chest_arm(pen, gp, t):
    """她近侧的手抬起来按在胸口。3/4 侧身时上臂、前臂朝镜头方向透视缩短，所以用短一些的投影长度画
    （characters 的 hand_chest 用全长 IK，肘会折到腰下、和前臂交叉成 X）。手从台面后面抬起来。"""
    import characters as ch
    R = ch._GirlRig(gp)
    u = float(gp.get('chest_u', 1.0))
    rest = R.TB([(0.05, 1.50)])[0]
    tgt = R.TB([(0.14, 0.47)])[0] + np.float32([0, 0.012 * R.S * math.sin(2 * math.pi * gp['breath'])])
    spec = dict(hand=lerp(rest, tgt, u), shape='flat', thumb=1, bend=R.f)
    ink = ch._Ink(pen, R.S, clip=R.clip)
    with pen.group('girl_arm', boil=R.boil, bleed=1.1):
        ch._girl_arm_at(pen, ink, R, ch._girl_shoulders(R)['near'], spec, R.seed + 40, l1=0.70, l2=0.74)


def boy_door_pose(t):
    """他（草稿）的动作。返回 boy_act 的 pose；t ≥ d1 时返回 None（已经散成雪）。"""
    if t >= T8['d1'] + 0.02:
        return None
    base = dict(face=dict(EXPR['neutral'], gy=0.45, open=0.5, smile=0.0), seed=2000, opacity=0.62,
                boil=BOY_BOIL, clip_poly=table_keyhole(), breath=(t + 0.9) / 3.9, y=0.0, floor=FLOOR_T)
    if t < T8['r1']:
        u = float(ease_io((t - T8['r0']) / (T8['r1'] - T8['r0'])))
        base['clip_poly'] = table_keyhole(under=True)
        return dict(base, act='rise', x=1495, s=126, facing=1, yaw=38 + 14 * u, pitch=12 - 8 * u, roll=3,
                    rise=u, table=(1452, 614))
    if t < T8['w1']:
        u = (t - T8['r1']) / (T8['w1'] - T8['r1'])
        return dict(base, act='walk', x=lerp(1515, 1585, u), s=lerp(126, 122, u), facing=1, yaw=70, pitch=6,
                    roll=0, gait=0.5 * u)
    if t < T8['b1']:
        u = (t - T8['w1']) / (T8['b1'] - T8['w1'])
        return dict(base, act='walk', back=True, x=lerp(1592, 1664, u), s=lerp(121, 117, u), yaw=172, pitch=-2,
                    gait=0.5 + 0.3 * u)
    if t < T8['x0']:
        th = door_theta(t)
        ug = float(ease_io((t - T8['b1']) / (T8['g1'] - T8['b1'])))
        rel = float(ease_io((t - T8['rel0']) / (T8['rel1'] - T8['rel0'])))
        lb = math.sin(math.pi * clamp((t - T8['lb0']) / (T8['lb1'] - T8['lb0'])))
        return dict(base, act='door', x=1666, s=117, handle=knob_pt(th), u=ug * (1 - rel), gait=0.0, step=0.4,
                    yaw=172 - 22 * lb, pitch=-2 + 4 * lb, roll=-2 * lb)
    u = (t - T8['x0']) / (T8['x1'] - T8['x0'])
    ue = float(ease_out(clamp(u)))
    p = dict(base, act='walk', back=True, x=lerp(1666, 1696, ue), floor=lerp(FLOOR_T, 902, ue),
             s=lerp(117, 97, ue), yaw=174, pitch=-4, gait=0.62 * u, step=0.8)
    p['dust'] = float(clamp((t - T8['d0']) / (T8['d1'] - T8['d0'])))
    p['dust_from'] = (p['x'] + 4, p['floor'] - 5.35 * p['s'])
    p['wind'] = WIND
    return p


def door_outside(pen, t, theta):
    """门外的雪夜（只在门开着时画；门扇随后画在上面挡住左边一条）。"""
    if door_open(theta) < 0.004:
        return
    s = 1600
    x0, x1, top, fl = DOOR['x0'], DOOR['x1'], DOOR['top'], DOOR['floor']
    hz = 470
    with pen.group('outside', boil=0.5):
        hole = behind_table([rect(x0, top, x1, fl)])
        pen.cover(hole, seed=s, feather=0.6)
        sky = behind_table([rect(x0, top, x1, hz)])
        pen.fill(sky, 'night', tone=0.80, seed=s + 1, grad=(0, top, 0, hz, 1.0, 0.42), c_fade=False, streak=0.3,
                 sangle=8)
        # 远处一排落满雪的屋顶和树（剪影），顶上一道雪
        ridge = P([(x0 - 5, 452), (1580, 430), (1606, 438), (1630, 412), (1668, 412), (1690, 440), (1712, 428),
                   (1738, 404), (1764, 430), (x1 + 5, 436)])
        body = np.vstack([ridge, [[x1 + 5, hz + 6], [x0 - 5, hz + 6]]])
        pen.fill(behind_table([body]), 'roof', tone=0.40, seed=s + 2, grad=(0, 400, 0, hz, 1.0, 0.55), c_fade=False)
        cap = np.vstack([ridge + P([0, -1.5]), (ridge + P([0, 6]))[::-1]])
        pen.lift([cap], amt=0.9, seed=s + 3, soft=1.0)
        # 一盏路灯：细杆 + 灯罩 + 一团冷光（水墨里就是留白）
        lx, ly = 1752, 318
        pen.line(D([(lx, ly + 6), (lx + 1, 480), (lx, 600)], 20), 4.5, tone=0.62, seed=s + 4, taper=(0.05, 0.3),
                 head=0.2, dry=0.4, dry_from=0.6)
        # 路灯的光晕：只在门洞里提白（pen.light 会把门框、墙也挖亮）
        gx0, gy0 = lx - 150, ly - 140
        yy, xx = np.mgrid[0:300, 0:300].astype(np.float32)
        g = np.exp(-((xx + gx0 - lx) ** 2 + (yy + gy0 - ly - 8) ** 2) / (2 * 80.0 ** 2))
        g *= ((xx + gx0) < x1 - 2) & ((yy + gy0) > top + 2) & ((xx + gx0) > x0 + 2)
        pen.lift(mask=(g, gx0, gy0), amt=0.9, seed=s + 5, soft=1.0)
        hood = P([[lx - 16, ly + 4], [lx - 6, ly - 8], [lx + 6, ly - 8], [lx + 16, ly + 4]])
        pen.fill(hood, 'ink', tone=0.8, seed=s + 6)
        pen.line(D([(lx - 17, ly + 4), (lx + 17, ly + 4)], 8), 3, tone=0.85, seed=s + 7, taper=(0.1, 0.1))
        # 雪地：纸白，几道冷灰的风吹雪痕；一道矮栅栏，栅栏顶上压着雪
        for k, (ya, yb) in enumerate([(540, 528), (606, 590), (700, 684)]):
            band = P([[x0, ya], [x1, yb], [x1, yb + 12 + 4 * k], [x0, ya + 16 + 5 * k]])
            pen.shade(behind_table([band]), amount=0.16, seed=s + 10 + k, hatch=False, soft=8.0)
        fy = 560
        for k, fx in enumerate((1572, 1626, 1680, 1734, 1788)):
            pen.line([(fx, fy - 30), (fx + 1, fy + 30)], 5, tone=0.55, seed=s + 20 + k, taper=(0.05, 0.2),
                     role='detail', dry=0.4, dry_from=0.6)
            pen.lift(ell(fx, fy - 32, 6, 3), amt=0.9, seed=s + 30 + k, soft=0.8)
        pen.line(D([(x0, fy - 12), (x1, fy - 15)], 30), 3.6, tone=0.5, seed=s + 40, taper=(0.02, 0.1),
                 role='detail', dry=0.5, dry_from=0.5)
        pen.line(D([(x0, fy + 10), (x1, fy + 8)], 30), 3.2, tone=0.45, seed=s + 41, taper=(0.02, 0.1),
                 role='detail', dry=0.5, dry_from=0.5)
        pen.lift(behind_table([P([[x0, fy - 15], [x1, fy - 18], [x1, fy - 13], [x0, fy - 10]])]), amt=0.8,
                 seed=s + 42, soft=1.0)
        # 门外斜着下的雪（被风吹向门里）
        r = rng(s, 'fl')
        for i in range(70):
            sp = r.uniform(160, 300)
            xx0, yy0 = r.uniform(0, 600), r.uniform(0, fl - top)
            xx = x1 + 30 - (xx0 + sp * 1.3 * t) % (x1 - x0 + 60)
            yy = top + (yy0 + sp * 0.45 * t + 6 * math.sin(t * 3 + i)) % (fl - top)
            if not (x0 + 3 < xx < x1 - 3):
                continue
            pen.dot(xx, yy, r.uniform(1.5, 3.4), color='snow', tone=0.0, seed=('dflake', i))


def door_light(pen, open_):
    """门口的一片冷光：门洞四周的墙、门前的地面被提亮（水墨里光 = 留白）。"""
    if open_ < 0.01:
        return
    q_open = open_ ** 0.8
    with pen.group('coldlight', boil=0.5):
        pen.light(1690, 880, 300, 170, amt=0.42 * q_open, color='snow', seed=1650)
        wedge = P([[1610, 948], [DOOR['x1'], 948], [1660, H + 30], [1150, H + 30]])
        pen.lift([wedge], amt=0.40 * q_open, seed=1651, soft=34.0)
        pen.light(1675, 560, 260, 420, amt=0.16 * q_open, color='snow', seed=1652)


def blown_snow(pen, t):
    """门开着时，风雪从门洞灌进屋里：雪片往左（往她那边）飞，越近越大，飘一阵就化掉。"""
    x1 = DOOR['x1']
    N, per = 96, 1.35
    with pen.group('blown', boil=0.6):
        for i in range(N):
            ph = (t + i * per / N) / per
            age = ph % 1.0
            cyc = math.floor(ph)
            ts = t - age * per
            r = rng(1660, i, cyc)
            op = door_open(door_theta(ts))
            if r.random() > op * 1.15:
                continue
            xf = float(leaf_quad(door_theta(ts))[1, 0])
            x0 = r.uniform(xf + 6, x1 - 4)
            y0 = r.uniform(300, 930)
            vx = -r.uniform(380, 720)
            vy = r.uniform(-60, 70)
            tt = age * per
            xx = x0 + vx * tt
            yy = y0 + vy * tt + 26 * math.sin(2.3 * tt + i) + 30 * tt * tt
            a = math.sin(math.pi * min(1.0, age * 1.25)) if age < 0.8 else max(0.0, (1 - age) / 0.2)
            if a < 0.1 or xx < 900:
                continue
            sz = r.uniform(1.8, 3.6) * (1 + 0.5 * clamp((x1 - xx) / 700)) * (0.5 + 0.5 * a)
            pen.dot(xx, yy, sz, sz * r.uniform(0.6, 1.0), color='snow', tone=0.0, seed=('blow', i, cyc),
                    rot=r.uniform(0, 180))


def dust_snow(pen, t, trace, p):
    """他散掉的线条变成白色的雪片，被风卷回屋里（和 boy_act 的灰同一个半径公式：先散的先飞）。"""
    if trace is None or len(trace) == 0 or t < T8['d0']:
        return
    T_ = np.asarray(trace, np.float32)
    o = np.float32(p['dust_from'])
    dist = np.hypot(*(T_ - o).T)
    maxd = float(dist.max()) + 1e-3
    dur = T8['d1'] - T8['d0']
    w = np.float32(WIND) / float(np.hypot(*WIND))
    r = rng(1680)
    idx = r.permutation(len(T_))[:170]
    with pen.group('dustsnow', boil=0.6):
        for j, i in enumerate(idx):
            td = T8['d0'] + dist[i] / (1.12 * maxd) * dur      # 这一点被吹散的时刻
            tau = t - td
            if tau <= 0 or tau > 1.1:
                continue
            rr = rng(1681, int(i))
            v = rr.uniform(260, 520)
            pos = T_[i] + w * v * tau + np.float32([0, -40]) * tau + \
                np.float32([math.sin(3 * tau + i), math.cos(2.5 * tau + i)]) * 14 * tau
            a = min(1.0, tau / 0.12) * (1.0 - clamp((tau - 0.6) / 0.5))
            if a < 0.08:
                continue
            sz = rr.uniform(1.6, 3.4) * (0.6 + 0.6 * a)
            pen.dot(pos[0], pos[1], sz, sz * rr.uniform(0.6, 1.0), color='snow', tone=0.0, seed=('dsn', int(i)),
                    rot=rr.uniform(0, 180))


def _girl_night(pen, ops, amt):
    """屋里暗：她的剪影内侧压一层淡墨（背后窗的雪光勾出一圈亮边），不排线（脸上排线显脏）。"""
    if amt <= 0.01:
        return
    sc = 0.5
    h, w = int(H * sc), int(W * sc)
    m = np.zeros((h, w), np.uint8)
    for kind, kw in ops:
        if kind != 'cover':
            continue
        if kw.get('mask') is not None:
            mm, mx, my = kw['mask']
            mm = np.asarray(mm, np.float32)
            ww, hh = max(1, int(round(mm.shape[1] * sc))), max(1, int(round(mm.shape[0] * sc)))
            small = (cv2.resize(mm, (ww, hh), interpolation=cv2.INTER_AREA) > 0.4).astype(np.uint8) * 255
            X0, Y0 = int(round(mx * sc)), int(round(my * sc))
            xa, ya, xb, yb = max(0, X0), max(0, Y0), min(w, X0 + ww), min(h, Y0 + hh)
            if xb > xa and yb > ya:
                m[ya:yb, xa:xb] = np.maximum(m[ya:yb, xa:xb], small[ya - Y0:yb - Y0, xa - X0:xb - X0])
            continue
        for p_ in (kw.get('polys') or []):
            cv2.fillPoly(m, [np.round(np.asarray(p_) * sc * 16).astype(np.int32)], 255, cv2.LINE_8, shift=4)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return
    y0, y1 = max(0, ys.min() - 4), min(h, ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(w, xs.max() + 5)
    sub = m[y0:y1, x0:x1].astype(np.float32) / 255.0
    inner = cv2.GaussianBlur(cv2.erode(sub, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))), (0, 0), 1.6)
    big = cv2.resize(inner, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_LINEAR)
    pen.shade(mask=(big, x0 * 2, y0 * 2), amount=amt, seed=1690, hatch=False, soft=2.0)


def _resting_spoon(pen):
    """木勺斜靠在锅里（她没在搅）。"""
    with pen.group('restspoon', boil=0.5):
        pen.line([(784, 556), (812, 528), (846, 494)], 8, tone=0.85, color='wood_d', seed=1695, taper=(0.15, 0.3),
                 head=0.4, dry=0.3, dry_from=0.7)
        pen.lift(tube([(806, 532), (836, 502)], [1.2, 1.2])[0], amt=0.5, seed=1696, soft=0.6)


def draw_door(pen, **kw):
    t = float(kw.get('t', pen.t))
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    cache = ('kitchen_night', pen.d % 3)
    if abs(pen.scale - 1.0) > 1e-6 or o.any():
        cache = cache + (round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))
    with pen.group('bg', boil=BG_BOIL, cache=cache):
        background(pen, night=True)
    snow(pen, t)
    th = door_theta(t)
    op = door_open(th)
    door_light(pen, op)
    door_outside(pen, t, th)
    with pen.group('leaf', boil=0.4):
        _door_leaf(pen, th, night=True, clip=True)
    # 她
    gp = girl_door_pose(t)
    halo(pen, girl_silhouette(gp), amt=0.22)
    i0 = len(pen.ops)
    girl(pen, gp, parts=('body', 'head'))
    soup(pen, t, 1.3, np.float32([786, 556]))
    _resting_spoon(pen)
    girl_chest_arm(pen, gp, t)
    _girl_night(pen, [op_ for op_ in pen.ops[i0:] if op_[0] == 'cover'], 0.30 * (1.0 - 0.35 * op))
    steam(pen, t, amt=0.45)
    # 他
    bp = boy_door_pose(t)
    trace = None
    if bp is not None:
        info = boy_act(pen, bp, mode='sketch')
        trace = info.get('trace')
    bowls(pen, kw.get('bowls', 'two'))
    if t >= T8['d0']:
        if trace is None or t > T8['d1'] - 0.02:
            from core import Pen
            dp = Pen('C', pen.d, t=min(t, T8['d1'] - 0.03))
            q = boy_door_pose(min(t, T8['d1'] - 0.03))
            q['dust'] = 0.0
            trace = boy_act(dp, q, mode='sketch').get('trace')
            bp = dict(q, dust_from=(q['x'] + 4, q['floor'] - 5.35 * q['s']))
        dust_snow(pen, t, trace, bp)
    blown_snow(pen, t)
