# -*- coding: utf-8 -*-
"""测试卡：把 Pen 的每种指令都用一遍，给笔刷作者在真实场景就绪前检查材质用。不是正片场景。"""
import math

import numpy as np

from core import Pen, densify, ell, rect, spline, tube, W, H


def draw(pen):
    t = pen.t
    # 背景（可缓存的静态底层）
    with pen.group('bg', boil=0.4, cache=('testcard', pen.d % 3)):
        pen.fill(rect(0, 0, W, 760), 'wall', seed='wall')
        pen.fill(rect(0, 760, W, H), 'floor', seed='floor')
        pen.shade(rect(0, 0, W, 760), amount=0.25, seed='wall_sh', grad=(0, 0, 0, 760, 0.0, 1.0), angle=60)
        pen.line([(0, 760), (700, 756), (1400, 762), (W, 758)], 6, tone=0.7, seed='floorline')
        # 窗
        win = rect(240, 120, 760, 520)
        pen.cover(win, seed='win_c')
        pen.fill(win, 'night', seed='win')
        pen.fill([(240, 430), (360, 380), (470, 410), (600, 360), (760, 420), (760, 520), (240, 520)], 'roof',
                 seed='roofs')
        for k, (x, y) in enumerate([(300, 470), (420, 455), (650, 440)]):
            pen.fill(rect(x, y, x + 16, y + 20), 'win_warm', seed=('lit', k))
        pen.line(densify(win, 40, closed=True), 9, tone=0.85, color='wood_d', closed=True, seed='winframe',
                 head=0.4, dry=0.3)
        pen.line([(500, 120), (500, 520)], 7, tone=0.8, color='wood_d', seed='mullion')
        # 灯
        pen.line([(1180, 0), (1180, 150)], 3, tone=0.6, seed='cord')
        shade_poly = np.float32([(1120, 200), (1240, 200), (1210, 150), (1150, 150)])
        pen.fill(shade_poly, 'lampshade', seed='lampshade')
        pen.line(densify(shade_poly, 30, closed=True), 5, tone=0.85, closed=True, seed='lampshade_l')
        pen.light(1180, 260, 260, 200, amt=0.55, seed='lamp')
        # 桌子
        top = ell(1250, 700, 300, 60)
        pen.cover(top, seed='table_c')
        pen.fill(top, 'wood', seed='table')
        pen.shade(ell(1250, 712, 290, 48, 0, 180), amount=0.35, seed='table_sh', angle=20)
        pen.line(ell(1250, 700, 300, 60), 7, tone=0.85, closed=True, seed='table_l', head=0.3, dry=0.4)
        for k, x in enumerate((1020, 1480)):
            leg = rect(x - 9, 740, x + 9, 1000)
            pen.cover(leg, seed=('leg_c', k))
            pen.fill(leg, 'wood_d', seed=('leg', k))
            pen.line([(x - 9, 745), (x - 10, 1000)], 5, tone=0.8, seed=('legl', k))
        # 碗 + 红豆
        bowl = ell(1180, 682, 70, 22, 0, 180)
        pen.cover(np.vstack([ell(1180, 670, 70, 16), bowl]), seed='bowl_c')
        pen.fill(np.vstack([ell(1180, 670, 70, 16, 180, 360), bowl]), 'enamel', seed='bowl')
        pen.fill(ell(1180, 670, 60, 12), 'soup', seed='bowl_soup')
        for k in range(14):
            a = k * 2.4
            pen.dot(1180 + 44 * math.cos(a) * (k / 14), 670 + 8 * math.sin(a) * (k / 14), 4.5, 3.4, 'bean',
                    seed=('bean', k), rot=k * 30)
        pen.line(ell(1180, 670, 70, 16), 4, tone=0.8, closed=True, seed='bowl_l')
        pen.line(bowl, 5, tone=0.8, seed='bowl_l2')
        # 排线质感
        pen.hatch(rect(60, 800, 600, 1040), angle=-30, spacing=9, tone=0.35, seed='floor_hatch')

    # 雪（会动的层）
    with pen.group('snow', boil=0.6):
        r = np.random.default_rng(7)
        for k in range(40):
            x = 250 + r.uniform(0, 500)
            y = 120 + (r.uniform(0, 400) + t * (30 + 20 * r.random())) % 400
            pen.dot(x, y, 2.6, color='snow', tone=0.0, seed=('flake', k))

    # 上色完成的人（固有色 + 阴影 + 轮廓 + 五官 + 红豆发夹）
    with pen.group('girl', boil=1.0, bleed=1.0):
        cx, cy = 820, 330
        body = np.float32([(cx - 70, cy + 70), (cx + 70, cy + 70), (cx + 110, cy + 420), (cx - 110, cy + 420)])
        pen.cover(body, seed='g_body_c')
        pen.fill(body, 'sweater', seed='g_body')
        pen.shade(np.float32([(cx - 70, cy + 70), (cx - 10, cy + 70), (cx - 40, cy + 420), (cx - 110, cy + 420)]),
                  amount=0.4, seed='g_body_sh', angle=70)
        pen.line(densify(body, 40, closed=True), 9, tone=0.9, closed=True, seed='g_body_l', head=0.5, lift=0.3, dry=0.5)
        head = ell(cx, cy, 52, 64)
        pen.cover(head, seed='g_head_c')
        pen.fill(head, 'skin', seed='g_face')
        hair = np.vstack([ell(cx, cy - 6, 60, 70, 180, 360), np.float32([(cx + 62, cy + 40), (cx + 40, cy - 10),
                                                                          (cx - 40, cy - 10), (cx - 62, cy + 40)])])
        pen.fill(hair, 'hair', seed='g_hair', streak=0.4)
        pen.line(ell(cx, cy, 52, 64, 20, 160), 6, tone=0.85, seed='g_jaw')
        for s in (-1, 1):
            pen.dot(cx + s * 20, cy + 14, 4.5, 6, 'eye', seed=('g_eye', s))
            pen.line([(cx + s * 30, cy - 2), (cx + s * 18, cy - 5)], 2.5, tone=0.7, role='feature', seed=('g_brow', s))
            pen.dot(cx + s * 30, cy + 34, 9, 5, 'blush', tone=0.1, seed=('g_blush', s))
        pen.line([(cx - 9, cy + 42), (cx, cy + 46), (cx + 9, cy + 42)], 2.5, tone=0.75, color='lips', role='feature',
                 seed='g_mouth')
        pen.dot(cx - 40, cy - 30, 7, 5, 'hairpin', seed='g_pin')
        pen.dot(cx - 30, cy - 33, 7, 5, 'hairpin', seed='g_pin2')
        pen.lift(ell(cx + 18, cy - 40, 18, 6), amt=0.5, seed='g_hair_hi')

    # 铅笔草稿的人（透明、不挡后面）
    with pen.group('sketch', boil=2.2, knock=False, opacity=0.62):
        bx, by = 1420, 420
        pen.line(ell(bx, by, 50, 62), 3, tone=0.6, closed=True, role='construct', seed='s_head', reps=2)
        pen.line([(bx, by - 62), (bx + 4, by + 62)], 2, tone=0.45, role='construct', seed='s_cross_v')
        pen.line([(bx - 50, by + 6), (bx + 50, by + 2)], 2, tone=0.45, role='construct', seed='s_cross_h')
        pen.line([(bx, by + 62), (bx - 10, by + 200), (bx + 10, by + 330)], 2.5, tone=0.5, role='construct',
                 seed='s_spine')
        pen.line([(bx - 100, by + 110), (bx - 40, by + 80), (bx + 50, by + 82), (bx + 110, by + 115)], 3.5, tone=0.6,
                 role='sketch', seed='s_shoulder', reps=3, spread=2.0)
        pen.line([(bx - 20, by + 10), (bx - 12, by + 18)], 2.5, tone=0.6, role='sketch', seed='s_eye')
        pen.line([(bx + 14, by + 34), (bx + 26, by + 40), (bx + 36, by + 34)], 2.5, tone=0.6, role='sketch',
                 seed='s_smile')
