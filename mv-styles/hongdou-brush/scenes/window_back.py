# -*- coding: utf-8 -*-
"""
窗前背影（T3 61.88–66.17 的旧风格一侧，C 水墨；也可以给第 16 镜末尾用）。
深夜，屋里很暗，唯一的光是窗外雪地反上来的灰白。她站在窗前，背对镜头（中景，膝盖以下出画）。
右手攥着一根红线举在胸前，红线绷着，从右边那扇微微推开的窗缝穿出去，消失在窗外的雪夜里。
红线是画面里唯一的红：随时间越来越红、越来越粗、四周的墨被“提白”成一圈光晕（水墨里的“亮”就是留白）。

draw(pen, **kw)
  kw（都可省）：t 覆盖表演时间（成片秒）；red 0..1 覆盖红线强度；tug 0..1 覆盖攥紧程度
给 river.patch_regions 用的：girl_pose(t)、line_path(t)、ops_mask(ops, sc)（把一串指令里的 cover/fill 区域栅格化）。
"""
import math

import cv2
import numpy as np

from core import densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, ease_io, lerp, W, H, as_polys
from characters import girl

# ---------------------------------------------------------------- 布局
WIN = (470, 92, 1450, 716)        # 窗框外沿
GLASS = (494, 116, 1426, 692)     # 玻璃
MULL_L = 652                      # 左窄扇 | 中间固定扇
MULL_R = 1118                     # 中间固定扇 | 右扇（推开了一条缝）
TRANS_Y = 196                     # 上亮子横档
SLIT = 16                         # 窗缝宽
SILL_Y = 692
CURTAIN = (318, 478)              # 左侧窗帘的左右边
CORNER_X = 1712                   # 右边墙角

BG_BOIL = 0.4
T_RED0, T_RED1 = 58.6, 66.0       # 红线从暗红到最红最亮


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def P(pts):
    return np.float32(pts)


# ================================================================= 表演
def red_amt(t):
    return float(ease_io((t - T_RED0) / (T_RED1 - T_RED0)))


def tug_amt(t):
    return 0.35 + 0.6 * float(ease_io((t - 60.4) / 3.2))


def girl_pose(t, tug=None):
    tug = tug_amt(t) if tug is None else tug
    # 头微微转向窗缝那一侧（红线出去的方向），略抬头
    yaw = 172.0 - 3.0 * float(ease_io((t - 61.0) / 3.0))
    return dict(x=760, y=420, s=150, back=True, body='stand', seed=1000, arm='hold_line',
                arm_args=dict(side='right', tug=float(tug)), yaw=yaw, pitch=-4.0, roll=-2.0,
                breath=(t + 0.4) / 3.9, boil=1.0, light=1.0)


def slit_pt(t):
    return np.float32([MULL_R + SLIT * 0.5, 386.0])


def line_path(t, fist, k=None):
    """红线（窗内段 + 窗外段）的控制点。fist 拳头位置（场景坐标）。→ (窗内段, 窗外段)"""
    k = red_amt(t) if k is None else k
    a = np.float32(fist) + (10, -6)
    b = slit_pt(t)
    sag = 15.0 * (1.0 - 0.8 * k)
    wob = 1.6 * (1.0 - k) * math.sin(t * 2.1)            # 绷紧前还有一点点晃
    n = 9
    u = np.linspace(0, 1, n)[:, None]
    pts = a * (1 - u) + b * u
    pts[:, 1] += (sag + wob) * np.sin(np.pi * u[:, 0])
    # 窗外：从窗缝穿出去（被推开的右扇挡住一小段），转个弯往远处的雪夜里伸，越远越细越淡
    out = P([b + (30, -2), b + (90, 2), b + (170, 10), b + (250, 16)])
    out[:, 1] += 2.0 * np.sin(np.linspace(0, 3, 4) + t * 0.9) * (1 - k)
    return pts, out


# ================================================================= 背景（静态，缓存）
def _room(pen):
    s = 4100
    # 墙：一整片淡墨，靠窗处被雪光照得几乎留白，越往画面四角越暗（深夜的屋子）
    gl = rect(GLASS[0] + 6, GLASS[1] + 6, GLASS[2] - 6, GLASS[3] - 6)
    pen.fill([rect(-20, -20, W + 20, H + 20)], 'wall', tone=0.40, seed=s, holes=[gl], c_fade=False,
             rgrad=(960, 400, 380, 1250, 0.22, 1.15), streak=0.12, sangle=6, rough=0.08)
    # 右边墙角：右墙背光，再暗一层
    pen.line(D([(CORNER_X, -10), (CORNER_X + 3, 540), (CORNER_X + 6, H + 10)], 40), 6, tone=0.55, seed=s + 3,
             taper=(0.05, 0.3), head=0.2, dry=0.6, dry_from=0.4)
    pen.shade([P([[CORNER_X + 4, -20], [W + 20, -20], [W + 20, H + 20], [CORNER_X + 8, H + 20]])], amount=0.25,
              seed=s + 4, angle=86, grad=(CORNER_X, 0, W, 0, 0.6, 1.0), hatch=False)
    # 窗台下的墙：窗台挡住了雪光
    pen.shade([P([[WIN[0] - 30, SILL_Y + 24], [WIN[2] + 30, SILL_Y + 24], [WIN[2] + 150, H + 20],
                  [WIN[0] - 150, H + 20]])], amount=0.16, seed=s + 5, angle=4, grad=(0, SILL_Y + 24, 0, H, 1.0, 0.2),
              hatch=False)


def _roof_row(r, x0, x1, base, hmin, hmax, wmin, wmax):
    """一排屋顶的轮廓（直边）：人字顶（山墙朝我们）和长坡顶（屋脊横着）交替，偶尔有烟囱。"""
    pts = []
    x = x0 - 30 - r.uniform(0, 60)
    chim = []
    while x < x1 + 10:
        w = r.uniform(wmin, wmax)
        h = r.uniform(hmin, hmax)
        b = base + r.uniform(-8, 8)
        if r.random() < 0.45:                       # 人字顶
            pk = x + w * r.uniform(0.45, 0.55)
            pts += [(x, b), (pk, b - h), (x + w, b)]
        else:                                       # 长坡顶：两头斜、屋脊平
            k = r.uniform(0.18, 0.3)
            pts += [(x, b), (x + w * k, b - h * 0.8), (x + w * (1 - k), b - h * 0.8), (x + w, b)]
        if r.random() < 0.35:
            chim.append((x + w * r.uniform(0.6, 0.78), b - h * 0.62))
        x += w + r.uniform(4, 40)
        if r.random() < 0.35:                       # 两栋之间矮一截的平顶
            pts += [(x - 2, b + r.uniform(4, 12)), (x + r.uniform(20, 50), b + r.uniform(4, 12))]
            x = pts[-1][0] + 2
    return np.float32(pts), chim


def _outside(pen):
    s = 4200
    x0, y0, x1, y1 = GLASS
    glass = rect(x0, y0, x1, y1)
    pen.cover(glass, seed=s)
    # 夜空：上浓下淡（远处雪地反光），不是死黑
    pen.fill(glass, 'night', tone=0.50, seed=s + 1, grad=(0, y0, 0, y1, 1.0, 0.38), c_fade=False, streak=0.35,
             sangle=4)
    # 远处的屋顶（雪压着）：三排人字顶，越远越淡
    r = rng(4250)
    rows = [(0.18, 560, 26, 40, 70, 120), (0.32, 612, 34, 52, 90, 150), (0.50, 668, 44, 66, 120, 190)]
    for i, (tn, base, hmin, hmax, wmin, wmax) in enumerate(rows):
        top, chim = _roof_row(r, x0, x1, base, hmin, hmax, wmin, wmax)
        top = densify(top, 18)
        top[:, 0] = np.clip(top[:, 0], x0 - 4, x1 + 4)
        body = np.vstack([top, [[x1 + 4, y1], [x0 - 4, y1]]])
        pen.fill(body, 'roof', tone=tn, seed=s + 10 + i, grad=(0, float(top[:, 1].min()), 0, y1, 1.0, 0.75),
                 c_fade=False)
        for j, (cx, cy) in enumerate(chim):
            ch_ = rect(cx - 6 - i, cy - 14 - 3 * i, cx + 6 + i, cy + 10)
            pen.fill(ch_, 'roof', tone=tn + 0.1, seed=(s + 15, i, j), c_fade=False)
            pen.line(P([(cx - 7 - i, cy - 15 - 3 * i), (cx + 7 + i, cy - 15 - 3 * i)]), 4, tone=0.9, color='snow',
                     seed=(s + 16, i, j), role='detail', taper=(0.1, 0.1))
        # 屋顶上的积雪：顺着屋顶厚厚一层（提白），下沿一道淡墨的檐
        th = 7.0 + 3.0 * i
        cap = np.vstack([top + P([0, -1.5]), (top + P([0, th]))[::-1]])
        pen.lift([cap], amt=0.92, seed=s + 20 + i, soft=1.2)
        pen.line(top + P([0, th + 1]), 2.2 + 0.6 * i, tone=0.42 + 0.14 * i, seed=s + 30 + i, taper=(0.05, 0.2),
                 role='detail', dry=0.45, dry_from=0.55, split=False)
    # 亮着的小窗（水墨里 = 留白的小方块）：深夜只剩几盏
    lit = [(560, 600, 12, 14), (744, 616, 10, 12), (1012, 590, 12, 13), (1206, 586, 11, 14), (1372, 628, 12, 12),
           (880, 640, 10, 11)]
    for i, (lx, ly, lw, lh) in enumerate(lit):
        q = P([[lx, ly], [lx + lw, ly + 1], [lx + lw - 1, ly + lh], [lx + 1, ly + lh - 1]])
        pen.lift(q, amt=0.85, seed=s + 40 + i, soft=0.8)
    # 一棵落了雪的光秃秃的树（左扇里）
    tr = s + 60
    pen.line(P([(560, 690), (566, 600), (560, 520), (572, 430)]), 9, tone=0.62, seed=tr, taper=(0.02, 0.5),
             head=0.4, dry=0.4, dry_from=0.6)
    for k, (a, b, c) in enumerate([((563, 560), (530, 510), (504, 480)), ((566, 520), (604, 470), (630, 452)),
                                   ((569, 470), (548, 420), (540, 380)), ((571, 440), (598, 400), (616, 360)),
                                   ((562, 610), (600, 582), (636, 572))]):
        pen.line(bez(a, b, c, 7), 4.2 - 0.4 * (k % 2), tone=0.5, seed=tr + 1 + k, taper=(0.05, 0.6), role='detail',
                 dry=0.4, dry_from=0.5)
        pen.line(bez(a, b, c, 7) + P([0, -2.5]), 2.2, tone=0.9, color='snow', seed=tr + 10 + k, taper=(0.2, 0.5),
                 role='detail')
    # 窗缝：右扇被推开一点，缝里直接是外面（更深的夜）
    sx = MULL_R
    slit = rect(sx, TRANS_Y + 8, sx + SLIT, SILL_Y - 4)
    pen.fill(slit, 'night', tone=0.95, seed=s + 80, c_fade=False, rim=0.0)
    pen.shade(rect(sx + SLIT, TRANS_Y + 8, sx + SLIT + 26, SILL_Y - 4), amount=0.35, seed=s + 81, angle=90, soft=5.0)
    # 玻璃下沿起一点雾（提白）
    for i, (cx, cy, rx, ry) in enumerate([(560, 684, 90, 30), (1380, 682, 70, 26), (900, 690, 160, 14)]):
        pen.lift(ell(cx, cy, rx, ry), amt=0.45, seed=s + 90 + i, soft=10.0)


def _frame(pen):
    s = 4300
    x0, y0, x1, y1 = GLASS
    wd = 'wood_d'
    # 外框：左、上两笔浓，右边淡而断（水墨的“虚实”）
    pen.line(D([(WIN[0] + 10, WIN[1] - 6), (WIN[0] + 6, 400), (WIN[0] + 9, SILL_Y + 6)], 30), 20, tone=0.92,
             color=wd, seed=s, taper=(0.05, 0.15), head=0.6, lift=0.3, dry=0.5, dry_from=0.66, streak=0.25, pool=0.2)
    pen.line(D([(WIN[0] - 16, WIN[1] + 6), (800, WIN[1] + 1), (WIN[2] + 18, WIN[1] + 5)], 30), 21, tone=0.9,
             color=wd, seed=s + 1, taper=(0.04, 0.25), head=0.7, lift=0.35, dry=0.65, dry_from=0.6, streak=0.3,
             fade=0.15, pool=0.2)
    pen.line(D([(WIN[2] - 10, WIN[1] + 10), (WIN[2] - 7, 380), (WIN[2] - 11, SILL_Y)], 30), 11, tone=0.62,
             color=wd, seed=s + 2, taper=(0.1, 0.5), head=0.3, dry=0.8, dry_from=0.2, streak=0.3, fade=0.3)
    # 上亮子横档
    pen.line(D([(x0, TRANS_Y + 2), (900, TRANS_Y - 2), (x1, TRANS_Y + 1)], 30), 12, tone=0.82, color=wd,
             seed=s + 3, taper=(0.05, 0.2), head=0.45, lift=0.3, dry=0.5, dry_from=0.6, streak=0.2)
    # 竖棂：左
    pen.line(D([(MULL_L + 1, y0), (MULL_L - 1, 420), (MULL_L + 1, SILL_Y)], 30), 12, tone=0.84, color=wd,
             seed=s + 4, taper=(0.05, 0.2), head=0.4, lift=0.3, dry=0.45, dry_from=0.62, streak=0.2)
    # 中扇右边框（窗缝左沿）
    pen.line(D([(MULL_R - 3, y0), (MULL_R - 4, 420), (MULL_R - 3, SILL_Y)], 30), 10, tone=0.86, color=wd,
             seed=s + 5, taper=(0.05, 0.2), head=0.4, lift=0.3, dry=0.4, dry_from=0.65, streak=0.2)
    # 右扇推开了：它的内框边移到缝的另一侧，略斜、略细（往外开，离我们远了一点）
    pen.line(D([(MULL_R + SLIT + 4, TRANS_Y + 8), (MULL_R + SLIT + 6, 440), (MULL_R + SLIT + 8, SILL_Y - 6)], 30),
             8, tone=0.74, color=wd, seed=s + 6, taper=(0.05, 0.3), head=0.3, dry=0.5, dry_from=0.55, streak=0.2)
    pen.line(D([(MULL_R + SLIT + 12, TRANS_Y + 12), (MULL_R + SLIT + 13, 440), (MULL_R + SLIT + 15, SILL_Y - 8)],
               30), 2.4, tone=0.45, color=wd, seed=s + 7, taper=(0.1, 0.4), role='detail')
    # 右扇的把手（插销）
    hx, hy = MULL_R + SLIT + 20, 452
    pen.line(P([(hx, hy - 16), (hx + 2, hy + 18)]), 5, tone=0.75, color='metal', seed=s + 8, taper=(0.1, 0.2))
    # 窗台：一道有力的横笔 + 台面厚度
    sill = P([[WIN[0] - 26, SILL_Y], [WIN[2] + 26, SILL_Y + 2], [WIN[2] + 30, SILL_Y + 26], [WIN[0] - 30, SILL_Y + 24]])
    pen.cover(sill, seed=s + 9)
    pen.fill(sill, 'wood', tone=0.42, seed=s + 10, grad=(WIN[0], 0, WIN[2], 0, 1.0, 0.7), c_fade=False)
    pen.line(D([(WIN[0] - 40, SILL_Y + 1), (960, SILL_Y - 3), (WIN[2] + 34, SILL_Y + 2)], 30), 17, tone=0.93,
             color=wd, seed=s + 11, taper=(0.04, 0.15), head=0.7, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25,
             pool=0.25)
    pen.line(D([(WIN[0] - 28, SILL_Y + 27), (960, SILL_Y + 28), (WIN[2] + 26, SILL_Y + 26)], 30), 6, tone=0.6,
             color=wd, seed=s + 12, taper=(0.1, 0.4), head=0.2, dry=0.7, dry_from=0.35, streak=0.2)
    # 窗框内侧被雪光照亮的一条细边（提白）
    pen.lift([rect(x0 + 2, y0 + 2, x1 - 2, y0 + 7)], amt=0.35, seed=s + 13, soft=2.0)


def background(pen):
    _room(pen)
    _outside(pen)
    _frame(pen)


# ================================================================= 动态
def snow(pen, t):
    x0, y0, x1, y1 = GLASS
    r = rng(4600)
    with pen.group('snow', boil=0.6):
        for i in range(120):
            far = i < 75
            sp = r.uniform(16, 30) if far else r.uniform(38, 66)
            size = r.uniform(1.1, 2.2) if far else r.uniform(2.4, 4.2)
            amp = r.uniform(3, 11)
            fq = r.uniform(0.2, 0.6)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(0, x1 - x0)
            ys = r.uniform(0, y1 - y0)
            yy = (ys + sp * t) % (y1 - y0 + 20) - 10 + y0
            xx = (xs - 9 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 - x0 + 40) - 20 + x0
            if not (x0 + 4 < xx < x1 - 4 and y0 + 4 < yy < y1 - 6):
                continue
            if abs(xx - MULL_L) < 9 + size or abs(yy - TRANS_Y) < 9 + size:
                continue
            if MULL_R - 9 - size < xx < MULL_R + SLIT + 18 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('wflake', i))
        # 从窗缝钻进来的几片雪：往屋里飘一点，慢慢落下、化掉
        for i in range(5):
            per = 3.2
            age = ((t + i * per / 5) % per) / per
            cyc = math.floor((t + i * per / 5) / per)
            rr = rng(4650, i, cyc)
            yy0 = rr.uniform(300, 560)
            xx = MULL_R + SLIT * 0.5 - age * rr.uniform(40, 110)
            yy = yy0 + age * rr.uniform(50, 120) + 6 * math.sin(age * 6 + i)
            a = math.sin(math.pi * age)
            if a < 0.15:
                continue
            pen.dot(xx, yy, 2.6 * a + 0.8, color='snow', tone=0.0, seed=('inflake', i, cyc))


def curtain(pen, t):
    """左边的窗帘：从窗缝进来的风让它很轻地摆。"""
    s = 4700
    l, r = CURTAIN
    sw = 5.0 * math.sin(t * 0.9) + 2.5 * math.sin(t * 1.7 + 1.0)
    top = 70
    pts_r = P([(r - 4, top), (r + 2 + sw * 0.3, 360), (r + 10 + sw, 720), (r + 4 + sw * 1.3, H + 20)])
    edge_r = spline(pts_r, 8.0)
    edge_l = P([(l, H + 20), (l + 4, 600), (l - 2, top)])
    poly = np.vstack([edge_r, edge_l])
    with pen.group('curtain', boil=0.6):
        pen.cover(poly, seed=s, feather=0.8)
        pen.fill(poly, 'cloth', tone=0.46, seed=s + 1, grad=(l, 0, r + 10, 0, 1.15, 0.55), c_fade=False,
                 streak=0.4, sangle=88)
        # 褶：几条竖的淡墨 + 影
        for k, u in enumerate((0.22, 0.45, 0.68, 0.86)):
            xa = l + (r - l) * u
            fold = P([(xa, top + 20), (xa + 3 + sw * u * 0.4, 500), (xa + 6 + sw * u, H + 10)])
            band, _, _ = tube(fold, [10, 16, 20])
            pen.shade([band], amount=0.28, seed=s + 10 + k, angle=88, soft=6.0)
            pen.line(fold, 3.2, tone=0.5, seed=s + 20 + k, role='detail', taper=(0.2, 0.3), dry=0.6, dry_from=0.3)
        # 靠窗那一边被雪光照亮
        lit = tube(edge_r[::4] - P([9, 0]), [6, 12, 12, 8])[0]
        pen.lift([lit], amt=0.35, seed=s + 30, soft=4.0)
        pen.line(edge_r[::3], 6, tone=0.78, seed=s + 31, taper=(0.05, 0.3), head=0.3, dry=0.5, dry_from=0.5)
        # 窗帘杆
        pen.line(D([(l - 40, top - 4), (r + 40, top - 6)], 30), 9, tone=0.88, color='wood_d', seed=s + 32,
                 taper=(0.05, 0.1), head=0.5)
        for k, xr in enumerate(np.linspace(l + 12, r - 8, 6)):
            pen.line(ell(xr, top - 4, 7, 9, n=12), 2.4, tone=0.6, seed=s + 40 + k, closed=True, role='detail',
                     taper=(0, 0))


def ops_mask(ops, sc=0.25, kinds=('cover', 'fill')):
    """把指令里 cover/fill 的区域（polys 或 mask）按 sc 栅格化成全画面遮罩（float32 0..1，H*sc × W*sc）。"""
    h, w = int(round(H * sc)), int(round(W * sc))
    m = np.zeros((h, w), np.uint8)
    for kind, kw in ops:
        if kind not in kinds:
            continue
        if kw.get('mask') is not None:
            mm, mx, my = kw['mask']
            mm = np.asarray(mm, np.float32)
            if mm.max() > 1.5:
                mm = mm / 255.0
            ww, hh = max(1, int(round(mm.shape[1] * sc))), max(1, int(round(mm.shape[0] * sc)))
            small = cv2.resize(mm, (ww, hh), interpolation=cv2.INTER_AREA)
            X0, Y0 = int(round(mx * sc)), int(round(my * sc))
            xa, ya = max(0, X0), max(0, Y0)
            xb, yb = min(w, X0 + ww), min(h, Y0 + hh)
            if xb > xa and yb > ya:
                sub = (small[ya - Y0:yb - Y0, xa - X0:xb - X0] > 0.4).astype(np.uint8) * 255
                m[ya:yb, xa:xb] = np.maximum(m[ya:yb, xa:xb], sub)
            continue
        polys = as_polys(kw.get('polys'))
        holes = as_polys(kw.get('holes', ()))
        if not polys:
            continue
        tmp = np.zeros_like(m) if holes else m
        for p in polys:
            cv2.fillPoly(tmp, [np.round(p * sc * 16).astype(np.int32)], 255, cv2.LINE_8, shift=4)
        if holes:
            for p in holes:
                cv2.fillPoly(tmp, [np.round(p * sc * 16).astype(np.int32)], 0, cv2.LINE_8, shift=4)
            np.maximum(m, tmp, out=m)
    return m.astype(np.float32) / 255.0


class screen_space:
    """在当前取景下临时回到屏幕坐标（给按屏幕算好的遮罩用）。"""

    def __init__(self, pen):
        self.pen = pen

    def __enter__(self):
        S, OX, OY = self.pen._xf[-1]
        self.cm = self.pen.view(1.0 / S, -OX / S, -OY / S)
        return self.cm.__enter__()

    def __exit__(self, *a):
        return self.cm.__exit__(*a)


def _backlight(pen, ops, seed):
    """逆光：她的背在暗处——剪影内侧整体压一层淡墨，边缘留一圈亮（雪光勾出的轮廓）。"""
    sc = 0.5
    m = ops_mask(ops, sc, kinds=('cover',))
    ys, xs = np.nonzero(m > 0.5)
    if len(xs) == 0:
        return
    y0, y1 = max(0, ys.min() - 4), min(m.shape[0], ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(m.shape[1], xs.max() + 5)
    sub = m[y0:y1, x0:x1]
    inner = cv2.erode(sub, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    inner = cv2.GaussianBlur(inner, (0, 0), 2.0)
    big = cv2.resize(inner, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_LINEAR)
    # 上浓下淡一点（下半身更暗，头肩靠近窗光）
    gy = np.linspace(0.75, 1.15, big.shape[0], dtype=np.float32)[:, None]
    with screen_space(pen):
        pen.shade(mask=(np.clip(big * gy, 0, 1), x0 * 2, y0 * 2), amount=0.30, seed=seed, angle=80, soft=3.0)


def red_line(pen, t, fist, k):
    s = 4800
    pts, out = line_path(t, fist, k)
    with pen.group('redglow', boil=0.5):
        # 光晕：红线四周的墨被提白（越来越亮）
        tub = tube(np.vstack([pts, out[1:3]]), [10 + 26 * k, 14 + 30 * k, 12 + 26 * k, 6 + 10 * k])[0]
        pen.lift([tub], amt=0.18 + 0.55 * k, seed=s, soft=8.0 + 8.0 * k)
        tub2 = tube(pts, [4 + 8 * k, 6 + 10 * k, 4 + 8 * k])[0]
        pen.lift([tub2], amt=0.3 + 0.5 * k, seed=s + 1, soft=3.0)
    with pen.group('redline', boil=0.5):
        w = 3.0 + 3.6 * k
        tone = 0.62 + 0.42 * k
        pen.line(pts, w, tone=tone, color='redline', seed=s + 2, taper=(0.02, 0.06), head=0.2, role='detail',
                 dry=0.0, split=False)
        # 窗外段：越远越细越淡，消失在雪夜里
        pen.line(out, w * 0.75, tone=tone * 0.85, color='redline', seed=s + 3, taper=(0.0, 0.9), fade=0.85,
                 role='detail', dry=0.15, dry_from=0.6, split=False)
        # 缠在拳头上的两圈
        fx, fy = float(fist[0]), float(fist[1])
        for j in range(2):
            pen.line(ell(fx + 2, fy - 2 + 7 * j, 13, 4.5, 200, 340, 9), 2.2 + 1.4 * k, tone=tone, color='redline',
                     seed=s + 10 + j, taper=(0.2, 0.2), role='detail', split=False)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    k = float(kw['red']) if kw.get('red') is not None else red_amt(t)
    cache = ('window_back', pen.d % 3)
    o = pen.to_screen(np.zeros((1, 2), np.float32))[0]
    if abs(pen.scale - 1.0) > 1e-6 or o.any():
        cache = ('window_back', pen.d % 3, round(pen.scale, 4), round(float(o[0]), 1), round(float(o[1]), 1))
    with pen.group('bg', boil=BG_BOIL, cache=cache):
        background(pen)
    snow(pen, t)
    curtain(pen, t)
    gp = girl_pose(t, kw.get('tug'))
    i0 = len(pen.ops)
    info = girl(pen, gp)
    _backlight(pen, pen.ops[i0:], 4900)
    fist = info.get('hand')
    if fist is None:
        fist = np.float32([gp['x'] + 0.85 * gp['s'], gp['y'] + 0.63 * gp['s']])
    red_line(pen, t, np.float32(fist), k)
