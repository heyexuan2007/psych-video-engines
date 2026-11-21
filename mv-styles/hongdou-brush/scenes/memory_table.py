# -*- coding: utf-8 -*-
"""
第 6 镜「第一句这是一句」（成片 17.43–21.59，A 水彩回忆）。
开头一格和 T1 结束时（table_cu 的 A 一侧）是同一个构图、同一套场景坐标：他的手（藏青毛衣袖口）把一勺红豆汤
送到她嘴边，她闭眼笑。然后镜头用 pen.view 缓慢拉远（17.43–19.50，缓入缓出），露出坐在桌子右端的他
（上色，藏青毛衣、白衬衫领，温柔地看着她）和整张晨光里的圆木桌：窗外白天的小雪、桌上两碗红豆汤、
从窗那边照进来的一片暖光；19.50 之后镜头停住。
  17.55–17.90  她抿住勺子（嘴合上）
  18.25–19.00  他把空勺子收回来，手臂放松
  18.45        她吃下那口汤，笑得眯起眼（laugh），肩膀轻轻一颤；他也笑了（closed_smile）
  19.60        他睁眼看着她笑（gentle）；20.25 她睁开眼转向他，两个人对视着笑
动的东西：窗外的雪（两层）、两只碗的热气、阳光里浮着的微尘、两个人的呼吸。

透视：近景里那道笔直的桌沿其实是一张大圆桌的一段弧——拉远时桌沿弯成椭圆（ry/rx = 0.30，和碗口一致），
桌子的两端、桌下的地板、右边的他和他的椅子、墙上的挂历和搁板一点点进画。新出现的东西在开头一格都在画框外。

draw(pen, **kw)   kw：t 覆盖表演时间（成片秒）；z 覆盖拉远进度 0..1（调试用）。
"""
import math

import numpy as np

from core import W, H, densify, ell, bez, spline, tube, rng, clamp, smooth01, ease_io, ease_out, lerp, ik2
import characters as ch
import table_cu as cu
import table as tb3

T0, T1 = 17.43, 21.59
T_PULL1 = 19.50
S_END = 0.56
ANCHOR = np.float32([1150.0, 400.0])          # 她嘴边（场景坐标），拉远时这一点从原位移到 ANCHOR_END
ANCHOR_END = np.float32([860.0, 344.0])

# 拉远后整张桌子（场景坐标；后沿顶点仍在 table_cu 的 TABLE_Y）
TB_CX, TB_RX, TB_RY = 1450.0, 1250.0, 300.0     # 桌子加宽，他也整个人坐在桌子后面
TB_TH = 26.0                                    # 桌沿厚度
FLOOR_Y = 1330.0                                # 墙和地板的交线
GLASS_X0, GLASS_Y0 = -44.0, -118.0              # 窗玻璃往左、往上延伸（开头一格在画框外）
S_HIM = 300.0
HIS_BOWL = (1865.5, 853.9, 88.0)          # 他坐到桌子后面，碗在他身前的桌面上（和她对称）
SWITCH0, SWITCH1 = 17.62, 17.95      # 接 T1 的长臂淡出
BOY_IN0, BOY_IN1 = 17.75, 18.10      # 他（两臂搭在桌上）淡入      # 长臂淡出、换成他自己的手
CAL = (2560, 96)
SHELF = (2470, 420, 300)

TY = cu.TABLE_Y


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def pull(t):
    return float(ease_io((t - T0) / (T_PULL1 - T0)))


def view_of(u):
    s = 1.0 + (S_END - 1.0) * u
    a = ANCHOR + (ANCHOR_END - ANCHOR) * u
    return s, float(a[0] - ANCHOR[0] * s), float(a[1] - ANCHOR[1] * s)


# ================================================================= 会变弯的桌沿
def table_shape(k):
    """拉远进度 k → (cx, cy, rx, ry_back, ry_front)。k=0：后沿是 y=TABLE_Y 的直线（画框里看不出弯）；k=1：整张圆桌。"""
    kk = float(smooth01(k))
    rx = 1.0 / (1.0 / 9000.0 + (1.0 / TB_RX - 1.0 / 9000.0) * kk)
    ryb = TB_RY * (rx / TB_RX) ** 2 * kk if kk > 0 else 0.0
    ryb = min(ryb, TB_RY)
    ryf = TB_RY + (900.0 - TB_RY) * (1 - kk)
    return TB_CX, TY + ryb, rx, ryb, ryf


def back_y(x, k):
    cx, cy, rx, ryb, _ = table_shape(k)
    u = np.clip((np.asarray(x, np.float32) - cx) / rx, -1, 1)
    return cy - ryb * np.sqrt(1 - u * u)


def table_polys(k):
    cx, cy, rx, ryb, ryf = table_shape(k)
    a = np.linspace(180, 360, 90)
    top = np.stack([cx + rx * np.cos(np.radians(a)), cy + ryb * np.sin(np.radians(a))], 1)
    b = np.linspace(0, 180, 90)
    bot = np.stack([cx + rx * np.cos(np.radians(b)), cy + ryf * np.sin(np.radians(b))], 1)
    return np.vstack([top, bot]).astype(np.float32), bot.astype(np.float32)


def _vis_x(pen, pad=160.0):
    s = pen.scale
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    return (0 - o[0]) / s - pad, (W - o[0]) / s + pad


def table(pen, k, mem=True):
    s = 400
    cx, cy, rx, ryb, ryf = table_shape(k)
    poly, bot = table_polys(k)
    # 桌腿（中柱）和桌沿厚度：拉远以后才看得见
    if k > 0.02:
        leg_top = cy + ryf - 10
        leg = P([[cx - 60, leg_top], [cx + 60, leg_top], [cx + 48, FLOOR_Y + 260], [cx - 48, FLOOR_Y + 260]])
        pen.fill(leg, 'wood_d', seed=s + 30, grad=(0, leg_top, 0, FLOOR_Y + 250, 1.0, 0.1))
        pen.line(D([(cx - 60, leg_top), (cx - 52, FLOOR_Y + 120)], 30), 9, tone=0.7, color='wood_d', seed=s + 31,
                 taper=(0.05, 0.7), dry=0.8, dry_from=0.3, fade=0.5)
        band = np.vstack([bot, (bot + P([0, TB_TH]))[::-1]])
        pen.cover([band], seed=s + 32, feather=0.8)
        pen.fill([band], 'wood_d', seed=s + 33)
    pen.cover([poly], seed=s)
    pen.fill([poly], 'wood', seed=s + 1, rgrad=(cu.BOWL_C[0] - 200, cu.BOWL_C[1], 200, 1300, 0.55, 1.0),
             streak=0.5, sangle=2.0)
    # 木纹（table_cu 的五道，拉远以后只留在桌面里的部分）
    r = rng(s, 'grain')
    for j in range(5):
        y = TY + 46 + j * 64 + r.uniform(-10, 10)
        x0 = r.uniform(-20, 300) if j % 2 == 0 else r.uniform(1200, 1500)
        x1 = x0 + r.uniform(400, 700)
        pts = D([(x0, y), ((x0 + x1) / 2, y + r.uniform(-4, 4)), (x1, y + r.uniform(-3, 3))], 40)
        if k > 0:
            inside = ((pts[:, 0] - cx) / rx) ** 2 + ((pts[:, 1] - cy) / np.where(pts[:, 1] < cy, max(ryb, 1), ryf)) ** 2
            pts = pts[inside < 0.92]
        if len(pts) >= 2:
            pen.line(pts, 2.4, tone=0.24, color='wood_d', seed=s + 10 + j, taper=(0.3, 0.4), role='detail',
                     dry=0.7, dry_from=0.2, streak=0.3)
    # 桌面后沿：一道有力的横笔（顺着弧）；画框外的部分不画
    xa, xb = _vis_x(pen)
    xa, xb = max(xa, cx - rx * 0.999), min(xb, cx + rx * 0.999)
    if xb > xa:
        xs = np.linspace(xa, xb, max(8, int((xb - xa) / 40)))
        e = np.stack([xs, back_y(xs, k) + 1.0], 1)
        pen.line(e, 14, tone=0.9, color='wood_d', seed=s + 2, taper=(0.02, 0.2), head=0.4, lift=0.3, dry=0.5,
                 dry_from=0.7, streak=0.25, pool=0.2)
        pen.line(e + P([0, 15]), 4, tone=0.4, color='wood_d', seed=s + 3, taper=(0.05, 0.5), head=0.1, dry=0.75,
                 dry_from=0.3, streak=0.2)
    if k > 0.02:
        pen.line(bot, 12, tone=0.85, color='wood_d', seed=s + 4, taper=(0.04, 0.12), head=0.6, lift=0.3, dry=0.5,
                 dry_from=0.75, streak=0.3)
        pen.line(bot + P([0, TB_TH]), 6, tone=0.7, color='wood_d', seed=s + 5, taper=(0.1, 0.3), head=0.4,
                 dry=0.5, dry_from=0.6)


# ================================================================= 背景（table_cu 的早晨，往外延伸）
def wall_floor(pen):
    lx, ly = cu.LAMP
    q = P([(-1600, -1300), (3900, -1300), (3900, FLOOR_Y), (-1600, FLOOR_Y)])
    pen.fill(q, 'wall', seed=700, rgrad=(lx - 200, ly + 260, 300, 1500, 0.25, 1.0), c_fade=False)
    fl = P([(-1600, FLOOR_Y), (3900, FLOOR_Y), (3900, 2400), (-1600, 2400)])
    pen.fill(fl, 'floor', seed=710, grad=(0, FLOOR_Y, 0, 2000, 0.7, 0.3), streak=0.5, sangle=1.0)
    pen.line(D([(-1600, FLOOR_Y), (1000, FLOOR_Y - 4), (3900, FLOOR_Y + 2)], 60), 8, tone=0.6, color='wood_d',
             seed=711, taper=(0.05, 0.1), dry=0.6, dry_from=0.4, streak=0.3)
    # 她身后的竖边（table_cu 的门框线，往上下延伸）
    pen.line(D([(1712, -420), (1709, 300), (1713, FLOOR_Y)], 30), 7, tone=0.5, color='wood_d', seed=702,
             taper=(0.05, 0.4), head=0.2, dry=0.7, dry_from=0.3, streak=0.2, fade=0.3)
    pen.line(D([(1740, -420), (1738, 260), (1741, FLOOR_Y)], 30), 3, tone=0.32, color='wood_d', seed=703,
             taper=(0.05, 0.5), head=0.1, dry=0.75, dry_from=0.2)


def window_ext(pen):
    """table_cu 的窗（只露左上角的那扇），往左、往上补全：窗框上沿、左沿，屋顶延伸。"""
    s = 100
    x1, y1 = cu.WIN['x1'], cu.WIN['y1']
    glass = P([(GLASS_X0, GLASS_Y0), (x1, GLASS_Y0), (x1, y1), (GLASS_X0, y1)])
    pen.cover(glass, seed=s)
    pen.fill(glass, 'sky', seed=s + 1, grad=(x1, y1, 0, 0, 0.55, 1.0), streak=0.3)
    roofs = [[(GLASS_X0, 352), (-20, 368), (40, 338), (110, 318), (180, 340), (236, 362)],
             [(214, 380), (290, 350), (362, 330), (430, 350), (490, 374)],
             [(470, 360), (530, 336), (580, 326), (x1 + 10, 332)]]
    for i, top in enumerate(roofs):
        top = P(top)
        body = np.vstack([top, [[top[-1, 0], y1], [top[0, 0], y1]]])
        pen.fill(body, 'roof', seed=s + 20 + i, grad=(0, float(top[:, 1].min()), 0, y1 + 40, 1.0, 0.45),
                 a_dens=0.7)
        pen.line(top, 12, tone=0.9, color='snow', seed=s + 30 + i, taper=(0.1, 0.2), role='detail', dry=0.45,
                 dry_from=0.3)
    pen.lift(tube([(80, 300), (230, 120), (330, -10), (380, GLASS_Y0)], [20, 46, 26, 14])[0], amt=0.45,
             seed=s + 70, soft=12.0)
    # 窗框：右边竖框、中间竖棂、上沿、左沿、窗台
    pen.line(D([(x1 + 4, GLASS_Y0 - 10), (x1 + 1, 200), (x1 + 4, y1 + 6)], 30), 17, tone=0.90, color='wood_d',
             seed=s + 80, taper=(0.02, 0.12), head=0.3, lift=0.3, dry=0.5, dry_from=0.65, streak=0.25, pool=0.2)
    pen.line(D([(x1 + 22, GLASS_Y0 - 4), (x1 + 21, 220), (x1 + 23, y1 + 16)], 30), 5, tone=0.5, color='wood_d',
             seed=s + 81, taper=(0.05, 0.3), head=0.1, dry=0.7, dry_from=0.35, streak=0.2)
    pen.line(D([(282, GLASS_Y0 - 6), (279, 200), (283, y1 + 2)], 30), 10, tone=0.78, color='wood_d', seed=s + 82,
             taper=(0.02, 0.2), head=0.3, lift=0.3, dry=0.5, dry_from=0.6, streak=0.2)
    pen.line(D([(GLASS_X0 - 18, GLASS_Y0 - 6), (300, GLASS_Y0 - 11), (x1 + 30, GLASS_Y0 - 7)], 30), 17, tone=0.88,
             color='wood_d', seed=s + 83, taper=(0.04, 0.2), head=0.6, lift=0.3, dry=0.6, dry_from=0.55,
             streak=0.3, pool=0.2)
    pen.line(D([(GLASS_X0 - 6, GLASS_Y0 - 14), (GLASS_X0 - 9, 160), (GLASS_X0 - 5, y1 + 10)], 30), 16, tone=0.88,
             color='wood_d', seed=s + 84, taper=(0.04, 0.2), head=0.6, lift=0.3, dry=0.55, dry_from=0.6,
             streak=0.25, pool=0.2)
    sill = P([[GLASS_X0 - 40, y1 + 2], [x1 + 46, y1 + 4], [x1 + 50, y1 + 30], [GLASS_X0 - 40, y1 + 28]])
    pen.cover(sill, seed=s + 89)
    pen.fill(sill, 'wood', seed=s + 90, grad=(0, 0, x1 + 50, 0, 0.6, 1.0))
    pen.shade(P([[GLASS_X0 - 40, y1 + 18], [x1 + 48, y1 + 20], [x1 + 50, y1 + 30], [GLASS_X0 - 40, y1 + 28]]),
              amount=0.3, seed=s + 93, angle=0)
    pen.line(D([(GLASS_X0 - 50, y1 + 4), (300, y1), (x1 + 56, y1 + 5)], 30), 17, tone=0.92, color='wood_d',
             seed=s + 91, taper=(0.02, 0.12), head=0.2, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(GLASS_X0 - 40, y1 + 31), (300, y1 + 32), (x1 + 44, y1 + 30)], 30), 5, tone=0.55, color='wood_d',
             seed=s + 92, taper=(0.05, 0.4), head=0.1, dry=0.75, dry_from=0.35, streak=0.2)


def lamp(pen):
    """table_cu 的吊灯（早晨关着），灯线往上一直通到天花板。"""
    lx, ly = cu.LAMP
    pen.line(D([(lx + 1, -760), (lx + 1, -40)], 40), 3.0, tone=0.7, seed=905, taper=(0, 0))
    cu._lamp(pen, True)


def right_wall(pen):
    """他身后的墙：挂历（红圈圈着的那一天）、搁板上两只马克杯。"""
    tb3.calendar(pen, CAL[0], CAL[1], w=150, h=200, seed=1000)
    tb3.shelf_mugs(pen, SHELF[0], SHELF[1], w=SHELF[2], seed=300)


def his_chair(pen):
    s = 1250
    x0, x1, top = 2400, 2470, 600
    for i, x in enumerate((x0, x1)):
        post = P([[x - 9, top], [x + 9, top - 4], [x + 9, 1060], [x - 9, 1060]])
        pen.cover(post, seed=s + 40 + i, feather=0.8)
        pen.fill(post, 'wood_d', seed=s + 42 + i)
        pen.line(D([(x - 9, top + 4), (x - 8, 840), (x - 9, 1060)], 20), 7, tone=0.8, seed=s + i, taper=(0.1, 0.3),
                 head=0.4, dry=0.4, dry_from=0.6)
    rail = P([[x0 - 16, top - 10], [x1 + 18, top - 16], [x1 + 18, top + 22], [x0 - 16, top + 26]])
    pen.cover(rail, seed=s + 20, feather=0.8)
    pen.fill(rail, 'wood', seed=s + 21)
    pen.line(D([(x0 - 18, top - 10), (x1 + 20, top - 16)], 20), 9, tone=0.88, color='wood_d', seed=s + 23,
             taper=(0.1, 0.15), head=0.6, lift=0.3, dry=0.4, dry_from=0.7)


def background(pen, k):
    wall_floor(pen)
    window_ext(pen)
    right_wall(pen)
    lamp(pen)
    table(pen, k)
    # 晨光：table_cu 的那一片 + 拉远后桌面上的一片暖光
    pen.light(380, 470, 900, 560, amt=0.55, color='sun', seed=960)
    if k > 0.02:
        pen.light(1080, 930, 760, 230, amt=0.45 * k, color='sun', seed=961)
        beam = P([[GLASS_X0, GLASS_Y0 + 60], [cu.WIN['x1'], GLASS_Y0], [1500, 1000], [400, 1100]])
        pen.lift(beam, amt=0.18 * k, seed=962, soft=60.0)


# ================================================================= 动态
def snow_ext(pen, t):
    """延伸出来的那一圈玻璃上的雪（table_cu.snow 只管开头画框里的那块）。"""
    x1, y1 = cu.WIN['x1'], cu.WIN['y1']
    r = rng(1655)
    with pen.group('snow2', boil=0.6):
        for i in range(40):
            far = i < 24
            sp = (r.uniform(22, 40) if far else r.uniform(48, 80)) * 0.8
            size = r.uniform(1.4, 2.6) if far else r.uniform(2.8, 4.8)
            amp = r.uniform(4, 12)
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(0, x1 - GLASS_X0)
            ys = r.uniform(0, y1 - GLASS_Y0)
            yy = (ys + sp * t) % (y1 - GLASS_Y0) + GLASS_Y0
            xx = (xs + 8 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - GLASS_X0) + GLASS_X0
            if xx > -20 and yy > -20:
                continue                    # 原画框里的那块由 table_cu.snow 画
            if xx < GLASS_X0 + 6 or xx > x1 - 6 or yy < GLASS_Y0 + 6 or yy > y1 - 6 or abs(xx - 281) < 9 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake2', i))


def motes(pen, t, k):
    """阳光里浮着的微尘（只在拉远以后，光里慢慢飘）。"""
    if k < 0.3:
        return
    r = rng(1890)
    with pen.group('motes', boil=0.3):
        for i in range(26):
            x0, y0 = r.uniform(300, 1500), r.uniform(150, 900)
            ph = r.uniform(0, 6.28)
            x = x0 + 30 * math.sin(0.30 * t + ph) + 10 * t
            y = y0 - 12 * t + 14 * math.cos(0.25 * t + 2 * ph)
            y = (y - 150) % 750 + 150
            pen.dot(x, y, r.uniform(2.0, 3.6), color='sun', tone=0.0, seed=('mote', i))


# ================================================================= 她
def girl_pose(t):
    gp = cu.girl_pose_a(min(t, T0 + 0.03))
    if t <= T0 + 0.03:
        return gp
    face = dict(gp['face'])
    sip = ease_io((t - 17.55) / 0.35)
    face['mouth_open'] = 0.22 * (1 - sip) + 0.03 * sip
    face['smile'] = face['smile'] + 0.10 * sip
    laugh = ease_io((t - 18.42) / 0.28) * (1.0 - 0.6 * ease_io((t - 19.4) / 0.7))
    face = ch.mix_expr(face, dict(ch.EXPR['laugh'], mouth_open=0.40, blush=0.9), laugh)
    look = ease_io((t - 20.25) / 0.40)
    face = ch.mix_expr(face, dict(ch.EXPR['smile'], gx=0.55, gy=0.0, open=0.60, happy=0.65, blush=0.85,
                                  smile=0.75), look)
    bounce = 3.0 * math.sin(2 * math.pi * 3.4 * (t - 18.45)) * laugh * (1.0 - ease_io((t - 19.0) / 0.6))
    gp = dict(gp)
    gp['face'] = face
    gp['pitch'] = 5.0 - 7.0 * laugh + 6.0 * look
    gp['yaw'] = -16.0 + 6.0 * laugh - 8.0 * look
    gp['roll'] = -6.0 + 7.0 * laugh - 6.0 * look
    gp['lean'] = gp['lean'] - 0.10 * ease_io((t - 18.3) / 0.6)
    gp['y'] = gp['y'] + bounce
    gp['breath'] = (t - cu.T0) / 3.6 + 0.2
    # 拉远后不再把手臂藏在桌下：近侧的手扶着自己那碗汤的碗沿
    hold = ease_io((t - 18.45) / 0.55)
    if hold > 0:
        gp['clip_arms'] = False
        gp['arm'] = 'bowl_rim'
        gp['arm_args'] = dict(bowl=cu.BOWL_C, r=cu.BOWL_R, u=hold)
    return gp


# ================================================================= 他
def boy_pose(t, k):
    """和她一样坐在桌子后面：胸口以下被桌面挡住，面朝她，两只手扶着自己的碗。"""
    lean = 0.35
    laugh = ease_io((t - 18.55) / 0.3) * (1.0 - ease_io((t - 19.55) / 0.4))
    warm = ease_io((t - 20.30) / 0.4)
    face = ch.mix_expr(dict(ch.EXPR['gentle'], gx=-0.45, gy=-0.10), dict(ch.EXPR['closed_smile'], smile=0.7), laugh)
    face = ch.mix_expr(face, dict(ch.EXPR['smile'], gx=-0.45, gy=-0.05, blush=0.6), warm)
    sg = cu.S_GIRL
    bx = 2010.0          # 开头一格（未拉远）时他在画框右边外面，远侧肩正好接上 T1 那只手臂
    by = back_y(bx, 1.0) - (cu.TABLE_Y - cu.GIRL_XY[1]) * 1.08
    edge = back_y(bx, 1.0)
    bp = dict(x=bx, y=by, s=1.08 * sg, facing=-1, yaw=34 - 4 * laugh, pitch=4 + 4 * laugh, roll=4 + 2 * laugh,
              face=face, act='sit', pose='sit_x', seed=2000, lean=lean, breath=(t - T0) / 3.9 + 0.6,
              clip_y=edge - 4)
    # 和她一样：两条前臂往前平搭在桌面上（手在各自肩膀的正前方、桌沿里一点）
    R0 = ch._BoyRig(dict(bp, pose='sit_x'))
    shf, shn = R0.TB([(0.44, 0.20), (-0.44, 0.20)])
    S = bp['s']
    # 手臂各走各的一侧，不横穿胸口：靠她那一侧（左）的前臂往前搭在桌上扶着碗，另一侧的前臂顺着身体落在桌沿上
    def hand_for(sh):
        # 手离肩约 1.6 s（手臂几乎伸直），前臂往前平放在桌面上，手肘不会横着支出去
        if sh[0] <= min(shf[0], shn[0]) + 1e-3:
            return np.float32([sh[0] - 0.55 * S, sh[1] + 1.45 * S])
        return np.float32([sh[0] - 0.45 * S, sh[1] + 1.50 * S])
    bp['arm_far'] = dict(hand=hand_for(shf), shape='flat', thumb=-1, bend=1.0)
    bp['arm_near'] = dict(hand=hand_for(shn), shape='flat', thumb=-1, bend=-1.0)
    R = ch._BoyRig(dict(bp, pose='sit_x'))
    return bp, R.TB([(0.44, 0.20)])[0]


def spoon_state(t, mpt):
    """勺头中心 c、方向 dv、勺里还有没有汤。"""
    c0, dv0 = cu.spoon_pose(min(t, T0 + 0.03), mpt)
    if t <= 18.25:
        return c0, dv0, 1.0 - smooth01((t - 17.70) / 0.35)
    w = ease_io((t - 18.25) / 0.75)
    a0 = math.degrees(math.atan2(dv0[1], dv0[0]))
    a = a0 + 14.0 * w
    dv = np.float32([math.cos(math.radians(a)), math.sin(math.radians(a))])
    # 喂完以后：手带着勺子收回到他自己的碗边（不再停在桌子中间，手臂也就不会被拉成一根长管）
    c_end = np.float32([HIS_BOWL[0] - 250.0, HIS_BOWL[1] - 95.0])
    c = lerp(c0, c_end, w) + np.float32([0, 6.0 * math.sin(2 * math.pi * 0.5 * (t - 19.0))]) * w
    return c, dv, 0.0


def spoon_arm(pen, c, dv, shoulder, l1, l2, wk, hsize, soup):
    """table_cu.his_hand 的参数化版本：参数等于 table_cu 的值时，画出来的指令完全一样（开头一格接上）。"""
    S = cu.S_BOY
    nv = np.float32([dv[1], -dv[0]])
    sp_len, sp_w = 30.0, 20.0
    fist = c + dv * 150.0
    ang = math.degrees(math.atan2(dv[1], dv[0])) + 178.0
    hv = np.float32([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    hk = hsize / 1.9
    wrist = fist - hv * 0.30 * S * hk
    elbow, wr = ik2(np.float32(shoulder), wrist, l1, l2, bend=1.0)
    ink = ch._Ink(pen, S)
    rig = cu._Rig(S)
    with pen.group('his_hand', boil=1.0):
        handle, Lh, Rh = tube([c + dv * (sp_len - 4), c + dv * 100.0, fist + dv * 20.0], [7.0, 8.0, 10.0])
        pen.cover([handle], seed=2101, feather=0.6)
        pen.fill([handle], 'metal', seed=2102)
        pen.line(Lh[::5], 2.6, tone=0.75, seed=2103, taper=(0.1, 0.2))
        pen.line(Rh[::5], 2.0, tone=0.5, seed=2104, taper=(0.1, 0.2))
        shoulder = np.float32(shoulder)
        path = [shoulder + (shoulder - elbow) * 0.15, elbow, (elbow + wr) / 2, wr]
        arm, La, Ra = tube(path, [0.44 * S * wk, 0.40 * S * wk, 0.34 * S * wk, 0.29 * S * wk])
        pen.cover([arm], seed=2110, feather=0.8)
        pen.fill([arm], 'boy_sweater', seed=2111)
        pen.shade([np.vstack([Ra, spline(path, 2.0)[::-1]])], amount=0.35, seed=2112, angle=120)
        pen.line(La[::6], 0.040 * S, tone=0.85, seed=2113, taper=(0.1, 0.25), head=0.4, dry=0.4, dry_from=0.6)
        pen.line(Ra[::6], 0.034 * S, tone=0.72, seed=2114, taper=(0.1, 0.25), head=0.3, dry=0.5, dry_from=0.5)
        fv = (wr - elbow) / (np.hypot(*(wr - elbow)) + 1e-6)
        fn = np.float32([-fv[1], fv[0]])
        for j, o in enumerate((0.06, 0.20)):
            p0 = elbow + fv * o * S - fn * 0.10 * S
            pen.line(P([p0, p0 + fv * 0.06 * S + fn * 0.06 * S, p0 + fv * 0.07 * S + fn * 0.13 * S]), 0.018 * S,
                     tone=0.5, seed=2118 + j, role='detail', taper=(0.3, 0.5), dry=0.5, dry_from=0.4)
        cw = 0.150 * S * wk
        cc = wr - fv * 0.09 * S
        shirt = P([wr - fn * cw * 0.92, wr + fn * cw * 0.92, wr + fn * cw * 0.85 + fv * 0.06 * S,
                   wr - fn * cw * 0.85 + fv * 0.06 * S])
        pen.cover(shirt, seed=2121, feather=0.7)
        pen.fill(shirt, 'boy_shirt', seed=2122)
        pen.line(P([wr - fn * cw * 0.85 + fv * 0.06 * S, wr + fn * cw * 0.85 + fv * 0.06 * S]), 2.4, tone=0.55,
                 seed=2123, taper=(0.1, 0.1), role='detail')
        cuff = P([cc - fn * cw - fv * 0.07 * S, cc + fn * cw - fv * 0.07 * S, cc + fn * cw * 0.96 + fv * 0.08 * S,
                  cc - fn * cw * 0.96 + fv * 0.08 * S])
        pen.cover(cuff, seed=2124, feather=0.7)
        pen.fill(cuff, 'boy_sweater', seed=2115)
        pen.shade(cuff, amount=0.15, seed=2125)
        for j in range(8):
            q = (j + 0.5) / 8 * 2 - 1
            p0 = cc + fn * cw * q * 0.95 - fv * 0.06 * S
            pen.line(P([p0, p0 + fv * 0.13 * S]), 1.8, tone=0.42, seed=(2116, j), role='detail', taper=(0.2, 0.2))
        pen.line(P([cc - fn * cw - fv * 0.07 * S, cc + fn * cw - fv * 0.07 * S]), 3.0, tone=0.7, seed=2117,
                 taper=(0.1, 0.1), role='detail')
        pen.line(P([cc - fn * cw * 0.96 + fv * 0.08 * S, cc + fn * cw * 0.96 + fv * 0.08 * S]), 3.0, tone=0.75,
                 seed=2126, taper=(0.1, 0.1))
        ch._hand(ink, rig, wr + fv * 0.04 * S, fist, shape='fist', thumb=1, seed=2120, size=hsize)
        rot = math.degrees(math.atan2(dv[1], dv[0]))
        bowl_s = ell(c[0], c[1], sp_len, sp_w * 0.62, 0, 360, 28, rot=rot)
        pen.cover([bowl_s], seed=2130, feather=0.6)
        pen.fill([bowl_s], 'metal', seed=2131)
        if soup > 0.5:
            inner = ell(c[0] - dv[0] * 2 + nv[0], c[1] - dv[1] * 2 + nv[1], sp_len * 0.78, sp_w * 0.42, 0, 360, 24,
                        rot=rot)
            pen.fill([inner], 'soup', seed=2132)
            for j, (a, b) in enumerate(((-0.35, 0.05), (0.12, -0.10), (0.42, 0.12))):
                bx = c + dv * (a * sp_len) + nv * (b * sp_w)
                pen.dot(bx[0], bx[1], 5.4, 3.6, color='bean', tone=1.0, seed=(2133, j), rot=rot + 20 * j)
        else:
            pen.shade([ell(c[0] + dv[0] * 3, c[1] + dv[1] * 3, sp_len * 0.7, sp_w * 0.35, 0, 360, 20, rot=rot)],
                      amount=0.25, seed=2136)
        pen.line(bowl_s, 2.6, tone=0.8, seed=2134, closed=True, taper=(0, 0))
        pen.lift(ell(c[0] - dv[0] * 12 + nv[0] * 6, c[1] - dv[1] * 12 + nv[1] * 6, 6, 2.5, n=10), amt=0.7,
                 seed=2135, soft=0.8)


# ================================================================= 场景
def draw(pen, t=None, **kw):
    t = float(pen.t if t is None else t)
    u = float(kw['z']) if 'z' in kw else pull(t)
    s, ox, oy = view_of(u)
    with pen.view(s, ox, oy):
        _draw(pen, t, u)


def _draw(pen, t, k):
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    with pen.group('bg', boil=cu.BG_BOIL, cache=('memory_table', pen.d % 3, round(pen.scale, 4),
                                                  round(float(o[0]), 1), round(float(o[1]), 1))):
        background(pen, k)
    cu.snow(pen, t, True)
    snow_ext(pen, t)
    cu.bowl(pen, t, True)
    cu.steam(pen, t, amt=1.0)
    # 他的碗（桌子右端，开头一格在画框外）
    if k > 0.01:
        tb3.small_bowl(pen, HIS_BOWL[:2], HIS_BOWL[2], fill=0.8, seed=1340, k=0.30)
        tb3.steam(pen, t, (HIS_BOWL[0], HIS_BOWL[1] + 8), w=48, h=260, seed=1765, amt=0.9, n=3, per=2.8)
    gp = girl_pose(t)
    ch.girl(pen, gp)
    mpt = cu.mouth_point(gp)
    bp, far_sh = boy_pose(t, k)
    a_in = float(ease_io((t - BOY_IN0) / (BOY_IN1 - BOY_IN0)))
    if k > 0.01 and a_in > 0.01:
        with pen.group('boy_in', opacity=a_in):
            ch.boy_act(pen, bp, mode='full')
    # 他的手臂：开头一格完全是 table_cu.his_hand；之后肩膀落到他身上、手和袖子慢慢变回他本来的比例
    m = float(ease_io((t - T0) / 0.9))
    c, dv, soup = spoon_state(t, mpt)
    shoulder = lerp(np.float32([2030.0, 780.0]), np.float32(far_sh), m)
    # 手臂长度：开头一格沿用 table_cu 那只够得着她嘴边的长臂，收回时缩回他身体（s=S_HIM）对应的正常比例
    m2 = float(ease_io((t - 18.25) / 0.9))
    l1 = (1.62 - 0.22 * m2) * cu.S_BOY
    l2 = (1.62 - 0.37 * m2) * cu.S_BOY
    # 喂完那口汤，长臂（接 T1 的那只）在 SWITCH0–SWITCH1 淡出，换成他身体自己的手捧碗
    fade = 1.0 - float(ease_io((t - SWITCH0) / (SWITCH1 - SWITCH0)))
    if fade > 0.01:
        with pen.group('spoon_arm_fade', opacity=fade):
            spoon_arm(pen, c, dv, shoulder, l1, l2, 1.0 - 0.12 * m,
                      1.9 - 0.45 * float(ease_io((t - 17.6) / 1.0)), soup)
    motes(pen, t, k)
