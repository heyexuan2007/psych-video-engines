# -*- coding: utf-8 -*-
"""
第 4 镜「示例歌词」（成片 11.97–14.07，C）：过肩镜头。
她坐在桌前，背影在左下前景（大）；桌子对面是他那把空椅子，碗里的红豆汤冒着热气，碗边摆着她刚放好的勺子。
  12.00–12.60  椅子上，铅笔草稿的“他”一笔一笔浮现（先是起形的辅助线、再是轮廓）；她的头轻轻抬起来
  12.60–13.40  他伸手去拿碗边那把勺子；13.05 抬眼看她，笑了一下
  13.43「白」  指尖碰到勺子的一瞬间，线条从指尖开始像灰一样散掉，炭笔碎屑往上飘（13.43–13.95）
  13.95–14.07  只剩那碗汤在冒热气；她的头慢慢低下去
动的东西：窗外的雪、锅和碗的热气、草稿浮现/化灰的碎屑。

draw(pen, **kw)   kw：t 覆盖表演时间（成片秒）。
"""
import math

import numpy as np

from core import W, H, densify, ell, spline, rng, clamp, smooth01, ease_io, ease_out, lerp
import characters as ch
import table as tb3

T0, T1 = 11.97, 14.07
T_APPEAR0, T_APPEAR1 = 12.00, 12.60
T_REACH0, T_REACH1 = 12.60, 13.40
T_TOUCH = 13.43
T_GONE = 13.95

TABLE = dict(cx=1000, cy=1010, rx=1250, ry=370)       # 桌子很大（离得近），后沿是一道缓缓的弧
GLASS = (70, 96, 450, 400)
MULL_X, TRANS_Y = 262, 214
LAMP = (1040, 118)
BOWL_C, BOWL_R = (1372, 716), 70
SPOON_C, SPOON_ANG = (1150, 744), -14.0           # 勺头中心、勺头 → 勺柄方向（柄朝他那边）
POT_C, POT_RX = (812, 688), 74
S_BOY = 152
BOY_X = 1238
CHAIR = (1116, 1352, 486)


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def spoon_touch_point():
    a = math.radians(SPOON_ANG)
    dv = np.float32([math.cos(a), math.sin(a)])
    return np.float32(SPOON_C) + dv * 70.0          # 勺柄中段


# ================================================================= 背景
def background(pen):
    tb3.wall(pen, (LAMP[0], LAMP[1] + 330), tone=0.22, r0=300, r1=1300)
    tb3.window(pen, GLASS, MULL_X, TRANS_Y, seed=100)
    tb3.calendar(pen, 1500, 250)
    tb3.shelf_mugs(pen, 1650, 330, w=230)
    tb3.chair_back(pen, *CHAIR, tb=TABLE)
    tb3.round_table(pen, TABLE, th=0)
    tb3.lamp(pen, LAMP[0], LAMP[1], k=1.1, light=(330, 260, 0.45))


# ================================================================= 草稿一笔一笔浮现
def reveal(ops, n0, p):
    """把 ops[n0:]（他的草稿画层）里的线按画的顺序只留前 p 比例：已画完的完整保留，正在画的那一笔截短，其余去掉。"""
    if p >= 1.0:
        return
    idx = [i for i in range(n0, len(ops)) if ops[i][0] == 'line']
    n = len(idx)
    if n == 0:
        return
    k = p * n
    full = int(math.floor(k))
    frac = k - full
    drop = set()
    for j, i in enumerate(idx):
        if j < full:
            continue
        if j == full and frac > 0.08:
            kw = dict(ops[i][1])
            pts = kw['pts']
            m = max(2, int(round(len(pts) * frac)))
            kw['pts'] = pts[:m]
            ops[i] = ('line', kw)
            continue
        drop.add(i)
    # 草稿里的其它小东西（橡皮擦痕、碎屑）在线画完之前不出现
    for i in range(n0, len(ops)):
        if ops[i][0] in ('dot', 'lift', 'hatch', 'fill', 'shade') and p < 0.9:
            drop.add(i)
    ops[n0:] = [op for i, op in enumerate(ops[n0:], start=n0) if i not in drop]


def boy_pose(t):
    u = ease_io((t - T_REACH0) / (T_REACH1 - T_REACH0))
    look_her = ease_io((t - 13.02) / 0.22)
    face = ch.mix_expr(dict(ch.EXPR['gentle'], gy=0.55, gx=0.35), dict(ch.EXPR['smile'], gx=-0.30, gy=0.05),
                       look_her)
    vis = tb3.behind_table_poly(TABLE)
    by = float(tb3.back_edge_y(BOY_X, TABLE)) - 1.15 * S_BOY
    dust = clamp((t - T_TOUCH) / (T_GONE - T_TOUCH))
    return dict(x=BOY_X, y=by, s=S_BOY, facing=-1, yaw=22 + 6 * look_her, pitch=9 - 5 * look_her,
                roll=4, face=face, act='reach', target=spoon_touch_point(), u=u, clip_poly=vis, seed=2000,
                opacity=0.72, boil=2.1, erase=0.0, dust=float(ease_out(dust)), wind=(0.25, -1.0),
                breath=(t - T0) / 3.6 + 0.3)


def girl_pose(t):
    up = ease_io((t - 12.10) / 0.55)
    down = ease_io((t - 13.60) / 0.45)
    pitch = 11 - 7 * up + 9 * down
    roll = 3 - 2 * up + 5 * down
    yaw = 150 - 3 * up + 2 * down
    return dict(x=430, y=760 + 3 * down, s=300, back=True, body='sit', yaw=yaw, pitch=pitch, roll=roll,
                seed=1000, arm='back_table', breath=(t - T0) / 3.8 + 0.1, light=-1)


def draw(pen, t=None, **kw):
    t = float(pen.t if t is None else t)
    with pen.group('bg', boil=0.4, cache=('table_os', pen.d % 3)):
        background(pen)
    tb3.snow(pen, t, GLASS, MULL_X, TRANS_Y, seed=1610, n=80)
    # 锅（左边，她手边）和锅里搁着的汤勺
    tb3.pot(pen, POT_C, POT_RX, seed=800, swirl=0.0)
    tb3.ladle_rest(pen, (POT_C[0] + 8, POT_C[1] + 5), (POT_C[0] - 90, POT_C[1] - 66), S=170)
    tb3.steam(pen, t, (POT_C[0], POT_C[1] - 2), w=40, h=200, seed=1700, amt=0.7, n=3, per=3.0, tone=0.22)
    # 对面：碗和勺子
    tb3.small_bowl(pen, BOWL_C, BOWL_R, fill=1.0, seed=1340)
    tb3.table_spoon(pen, SPOON_C, ang=SPOON_ANG, L=1.12, seed=1500)
    # 他：只在 12.00–13.95 之间
    if T_APPEAR0 <= t < T_GONE + 0.05:
        p = clamp((t - T_APPEAR0) / (T_APPEAR1 - T_APPEAR0))
        bp = boy_pose(t)
        bp['opacity'] = 0.74 * (0.55 + 0.45 * p)
        n0 = len(pen.ops)
        ch.boy_act(pen, bp, mode=kw.get('boy_mode', 'sketch'))
        reveal(pen.ops, n0, float(smooth01(p) * 0.15 + p * 0.85))
    # 碗里的热气（在他前面）
    tb3.steam(pen, t, (BOWL_C[0], BOWL_C[1] + 6), w=30, h=190, seed=1760, amt=1.0, n=3, per=2.6, tone=0.28)
    # 她的背影（前景）
    ch.girl(pen, girl_pose(t))
