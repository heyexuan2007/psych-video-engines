# -*- coding: utf-8 -*-
"""
第 11 镜「有时候」（成片 38.64–40.83，C 水墨；唯一的红 = 很早以前用红笔圈起来的那一天）。
墙上挂历特写（和厨房里那本同款：顶上一道深色装订条、行楷“十二”月、7 列日期格）。
十二月：12 月 3 日被红笔圈着（第一行，留在很前面），4 日到 20 日每天一个叉，墨色深浅不一、大小歪斜各不相同。
她的右手握笔从画面右边伸进来：“有”（38.76）划掉 21 日，“时”（39.34）划掉 22 日，“候”（39.74）划掉 23 日
（最后一个划得慢一点）；然后笔移到 24 日上方，落下去一点、停住，没有落笔。
镜头极慢地往右横移（pen.view 平移，从那一片叉移向最新的一格）。
左边露出一角窗（夜色、雪），右边墙上钉着一张便条和一把挂在钉子上的钥匙；灯光里有几粒浮尘。
会动的：手和笔（和它在挂历上的影子）、新画出来的叉、窗外的雪、浮尘。

draw(pen, **kw)
  kw：t 覆盖表演时间（成片秒，默认 pen.t）；pan 横移总量（像素，默认 PAN）
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
from core import W, H, densify, ell, bez, spline, tube, rng, clamp, ease_io, ease_out
import hands

T0, T1 = 38.64, 40.83
PAN = 120.0                         # 横移总量（像素）
BG_BOIL = 0.35

# ---------------------------------------------------------------- 布局（场景坐标）
PAGE = (430, 46, 1650, 892)         # 挂历纸
GX0, GY0 = 462, 286                 # 日期格左上角
CW, RH = 168.0, 112.0               # 格子宽、高
ROWS = 5
FIRST_COL = 2                       # 12 月 1 日是星期二（第一列 = 星期日）
RED_DAY = 3                         # 红圈
CROSSED = range(4, 21)              # 早就划掉的
NEW = (21, 22, 23)                  # 这个镜头里划掉的
HOVER = 24                          # 最后停在上面、没有落笔的那一天
WIN_X1 = 236                        # 左边窗玻璃的右沿
NOTE = (1716, 252, 1880, 430)       # 便条
L_HAND = 430.0                      # 手长

FONT_NUM = core.FONT_LABEL          # 华文楷体：印刷的日期
FONT_TITLE = core.FONT_LYRIC        # 华文行楷：“十二”


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


def cell(day):
    """日期 → (行, 列, 格子中心)。"""
    k = day - 1 + FIRST_COL
    r, c = k // 7, k % 7
    return r, c, np.float32([GX0 + (c + 0.5) * CW, GY0 + (r + 0.5) * RH])


# ================================================================= 文字遮罩（缓存）
_TXT = {}


def text_mask(txt, font, size):
    key = (txt, font, size)
    if key not in _TXT:
        f = ImageFont.truetype(font, size)
        l, t_, r, b = f.getbbox(txt)
        w, h = r - l + 12, b - t_ + 12
        im = Image.new('L', (w, h), 0)
        ImageDraw.Draw(im).text((6 - l, 6 - t_), txt, font=f, fill=255)
        _TXT[key] = np.asarray(im, np.float32) / 255.0
    return _TXT[key]


def put_text(pen, txt, x, y, font, size, tone, seed, anchor='lt', **kw):
    m = text_mask(txt, font, size)
    h, w = m.shape
    if anchor == 'mm':
        x, y = x - w / 2, y - h / 2
    if size < 60:
        # 小字：不要洇得太开（细笔画会被冲没），直接给墨的浓度
        kw = dict(dict(c_dens=1.25 * tone, soft=0.6, rough=0.04, bloom=0.0, rim=0.05, edge=1.2), **kw)
    pen.fill(mask=(m, int(round(x)), int(round(y))), color='ink', tone=tone, seed=seed, grad_auto=False,
             c_fade=False, broad=False, **dict(dict(rim=0.15), **kw))


# ================================================================= 叉（每天一个，各不相同）
def cross_spec(day):
    r = rng('xday', day)
    _, _, c = cell(day)
    c = c + P([r.uniform(4, 14), r.uniform(8, 16)])
    hw, hh = r.uniform(38, 50), r.uniform(26, 34)
    rot = math.radians(r.uniform(-7, 7))
    cr, sr = math.cos(rot), math.sin(rot)

    def R(p):
        return c + P([p[0] * cr - p[1] * sr, p[0] * sr + p[1] * cr])

    a0, a1 = R((-hw, -hh)), R((hw * r.uniform(0.9, 1.08), hh * r.uniform(0.9, 1.1)))
    b0, b1 = R((hw * r.uniform(0.88, 1.05), -hh * r.uniform(0.9, 1.1))), R((-hw * r.uniform(0.9, 1.05), hh))
    tone = float(r.uniform(0.5, 0.95))
    w = float(r.uniform(5.0, 8.0))
    dry = float(r.uniform(0.2, 0.7))
    bow = float(r.uniform(-5, 5))
    return dict(a=(a0, a1), b=(b0, b1), tone=tone, w=w, dry=dry, bow=bow)


def _stroke_pts(p0, p1, bow, k=1.0):
    """一笔斜线（略带弧度），k = 画到哪里。"""
    k = clamp(k)
    q1 = p0 + (p1 - p0) * k
    m = (p0 + q1) / 2
    d = q1 - p0
    n = P([-d[1], d[0]]) / (float(np.hypot(*d)) + 1e-6)
    return np.vstack([p0, m + n * bow * k, q1])


def draw_cross(pen, day, ka=1.0, kb=1.0, fresh=False):
    sp = cross_spec(day)
    tone = 0.93 if fresh else sp['tone']
    for j, (key, kk) in enumerate((('a', ka), ('b', kb))):
        if kk <= 0.02:
            continue
        p0, p1 = sp[key]
        pts = _stroke_pts(p0, p1, sp['bow'] * (1 if j == 0 else -0.7), kk)
        pen.line(pts, sp['w'] * (1.08 if fresh else 1.0), tone=tone, seed=('x', day, j), role='detail',
                 taper=(0.06, 0.35 if kk > 0.97 else 0.05), head=0.55, lift=0.15, dry=sp['dry'] * (0.6 if fresh else 1),
                 dry_from=0.62, pool=0.3 if fresh else 0.15, boil=0.3)


# ================================================================= 笔的表演
def _x_plan():
    """每个新叉的时间：(日期, 第一笔开始, 第一笔时长, 抬笔, 第二笔时长)。"""
    return [(21, 38.76, 0.11, 0.05, 0.11),
            (22, 39.34, 0.11, 0.05, 0.11),
            (23, 39.74, 0.15, 0.07, 0.16)]


PLAN = _x_plan()


def stroke_progress(t, day):
    """→ (第一笔进度, 第二笔进度)。"""
    for d_, ts, d1, gp, d2 in PLAN:
        if d_ == day:
            ka = clamp((t - ts) / d1)
            kb = clamp((t - ts - d1 - gp) / d2)
            return ka, kb
    return 0.0, 0.0


def pen_state(t):
    """笔尖位置、抬笔量、手的微转。"""
    keys = []          # (时间, 位置, lift, rot)
    sp0 = cross_spec(NEW[0])
    a0 = sp0['a'][0]
    keys.append((T0 - 0.2, a0 + P([60, -50]), 0.9, 2.0))
    keys.append((PLAN[0][1] - 0.01, a0, 0.0, 0.0))
    for i, (d_, ts, d1, gp, d2) in enumerate(PLAN):
        sp = cross_spec(d_)
        (pa0, pa1), (pb0, pb1) = sp['a'], sp['b']
        keys.append((ts, pa0, 0.0, -1.0))
        keys.append((ts + d1, pa1, 0.0, 3.0))
        keys.append((ts + d1 + gp * 0.5, (pa1 + pb0) / 2 + P([0, -6]), 0.55, 1.0))
        keys.append((ts + d1 + gp, pb0, 0.0, -2.0))
        keys.append((ts + d1 + gp + d2, pb1, 0.0, -4.0))
        te = ts + d1 + gp + d2
        if i + 1 < len(PLAN):
            nxt = cross_spec(PLAN[i + 1][0])['a'][0]
            tn = PLAN[i + 1][1]
            keys.append((te + (tn - te) * 0.45, (pb1 + nxt) / 2 + P([0, -34]), 1.0, 1.0))
            keys.append((tn - 0.01, nxt, 0.0, 0.0))
        else:
            # 移到 24 日上方，落下去一点、停住
            _, _, ch = cell(HOVER)
            above = ch + P([-34, -22])
            keys.append((te + 0.16, (pb1 + above) / 2 + P([0, -40]), 1.0, 2.0))
            keys.append((te + 0.42, above + P([6, -10]), 0.85, 1.0))
            keys.append((te + 0.62, above, 0.42, 0.0))
            keys.append((T1 + 0.3, above + P([2, -2]), 0.46, 0.0))
    ts_ = [k[0] for k in keys]
    if t <= ts_[0]:
        k = keys[0]
        return k[1], k[2], k[3]
    for j in range(len(keys) - 1):
        if keys[j][0] <= t <= keys[j + 1][0]:
            u = (t - keys[j][0]) / max(1e-6, keys[j + 1][0] - keys[j][0])
            # 画线段时匀速（笔尖贴纸），抬笔移动时缓动
            if keys[j][2] < 0.01 and keys[j + 1][2] < 0.01:
                e = u
            else:
                e = ease_io(u)
            p = keys[j][1] * (1 - e) + keys[j + 1][1] * e
            lf = keys[j][2] * (1 - e) + keys[j + 1][2] * e
            ro = keys[j][3] * (1 - e) + keys[j + 1][3] * e
            return p, lf, ro
    k = keys[-1]
    return k[1], k[2], k[3]


def tip_now(t):
    """笔尖实际所在（画线时用笔画的终点，保证笔尖和墨线对得上）。"""
    for d_, ts, d1, gp, d2 in PLAN:
        sp = cross_spec(d_)
        if ts <= t <= ts + d1:
            ka = clamp((t - ts) / d1)
            return _stroke_pts(sp['a'][0], sp['a'][1], sp['bow'], ka)[-1]
        if ts + d1 + gp <= t <= ts + d1 + gp + d2:
            kb = clamp((t - ts - d1 - gp) / d2)
            return _stroke_pts(sp['b'][0], sp['b'][1], -0.7 * sp['bow'], kb)[-1]
    return None


# ================================================================= 背景（静态）
def wall(pen):
    s = 100
    q = P([(-60, -60), (W + 260, -60), (W + 260, H + 60), (-60, H + 60)])
    pen.fill(q, 'wall', seed=s, tone=0.24, rgrad=(560, 60, 260, 1700, 0.35, 1.05), c_fade=False, broad=False,
             var=0.12, cell=110.0)
    pen.light(640, 120, 620, 460, amt=0.30, color='lamp', seed=s + 1)
    # 墙上几处斑驳、一道细裂纹
    pen.line(P([(1880, 640), (1902, 700), (1894, 748), (1922, 812), (1916, 880)]), 2.2, tone=0.32, seed=s + 2,
             role='detail', taper=(0.3, 0.5), dry=0.5, dry_from=0.3)
    pen.shade(ell(1820, 980, 160, 50, n=24), amount=0.10, seed=s + 3, soft=26.0, hatch=False)


def window(pen):
    s = 200
    x1 = WIN_X1
    glass = P([(-80, -60), (x1, -60), (x1, 760), (-80, 760)])
    pen.cover(glass, seed=s)
    pen.fill(glass, 'night', seed=s + 1, grad=(0, 0, x1 + 60, 760, 1.0, 0.55), streak=0.4, sangle=88.0)
    roof = P([(-80, 640), (20, 612), (110, 600), (180, 618), (x1 + 10, 630)])
    body = np.vstack([roof, [[x1 + 10, 760], [-80, 760]]])
    pen.fill(body, 'roof', seed=s + 2, grad=(0, 600, 0, 780, 1.0, 0.5))
    pen.line(roof, 10, tone=0.9, color='snow', seed=s + 3, taper=(0.1, 0.2), role='detail', dry=0.45, dry_from=0.3)
    for i, (lx, ly) in enumerate([(40, 664), (130, 676)]):
        q = P([[lx, ly], [lx + 14, ly + 1], [lx + 13, ly + 17], [lx + 1, ly + 16]])
        pen.cover(q, seed=s + 10 + i, feather=0.8)
        pen.fill(q, 'win_warm', seed=s + 12 + i)
    pen.lift(ell(100, 744, 190, 40), amt=0.5, seed=s + 20, soft=12.0)
    pen.line(D([(x1 + 6, -40), (x1 + 2, 380), (x1 + 6, 772)], 30), 22, tone=0.9, color='wood_d', seed=s + 30,
             taper=(0.02, 0.1), head=0.4, lift=0.3, dry=0.5, dry_from=0.7, streak=0.25, pool=0.2)
    pen.line(D([(x1 + 30, -40), (x1 + 28, 420), (x1 + 31, 776)], 30), 5, tone=0.5, color='wood_d', seed=s + 31,
             taper=(0.05, 0.3), head=0.1, dry=0.7, dry_from=0.35, streak=0.2)
    pen.line(D([(60, -40), (58, 300), (61, 762)], 30), 10, tone=0.75, color='wood_d', seed=s + 32,
             taper=(0.02, 0.2), head=0.3, lift=0.3, dry=0.5, dry_from=0.6)
    sill = P([[-80, 760], [x1 + 60, 762], [x1 + 66, 800], [-80, 798]])
    pen.cover(sill, seed=s + 33)
    pen.fill(sill, 'wood', seed=s + 34, grad=(0, 0, x1 + 60, 0, 0.6, 1.0))
    pen.line(D([(-80, 762), (x1 + 70, 764)], 30), 16, tone=0.92, color='wood_d', seed=s + 35, taper=(0.02, 0.12),
             head=0.2, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(-80, 800), (x1 + 62, 801)], 30), 5, tone=0.55, color='wood_d', seed=s + 36, taper=(0.05, 0.4),
             dry=0.75, dry_from=0.35)
    pen.shade(P([[-80, 800], [x1 + 66, 801], [x1 + 90, 860], [-80, 862]]), amount=0.3, seed=s + 37, soft=10.0,
              hatch=False)
    # 窗台上一小盆绿萝（陶盆 + 几片没骨叶）
    cx, by = 150, 760
    potp = P([[cx - 32, by - 46], [cx + 32, by - 46], [cx + 25, by], [cx - 25, by]])
    pen.cover(potp, seed=s + 40, feather=0.8)
    pen.fill(potp, 'terra', seed=s + 41, grad=(cx - 30, 0, cx + 30, 0, 1.0, 0.6))
    pen.shade(P([[cx + 4, by - 46], [cx + 32, by - 46], [cx + 25, by], [cx + 2, by]]), amount=0.3, seed=s + 48)
    pen.line(D([(cx - 36, by - 46), (cx, by - 49), (cx + 36, by - 46)], 10), 6, tone=0.85, seed=s + 42,
             taper=(0.1, 0.2), head=0.4)
    pen.line([(cx - 31, by - 42), (cx - 24, by - 1)], 4, tone=0.7, seed=s + 43, taper=(0.1, 0.3))
    leaves = [((cx - 4, by - 48), (cx - 40, by - 96), (cx - 70, by - 104)), ((cx, by - 48), (cx - 6, by - 110), (cx + 8, by - 136)),
              ((cx + 4, by - 48), (cx + 40, by - 90), (cx + 62, by - 96)), ((cx - 2, by - 48), (cx - 30, by - 70), (cx - 58, by - 62)),
              ((cx + 6, by - 48), (cx + 30, by - 64), (cx + 52, by - 52)), ((cx + 2, by - 48), (cx + 16, by - 100), (cx + 30, by - 120))]
    for i, (a, b, c) in enumerate(leaves):
        pen.line(bez(a, b, c, 6), 15, tone=0.55 + 0.2 * (i % 2), color='plant', seed=s + 50 + i, role='detail',
                 taper=(0.35, 0.55), head=0.7, streak=0.3, dry=0.3, dry_from=0.75)


def note_key(pen):
    """右边墙上：一张图钉钉着的便条（几行草字），下面钉子上挂着一把钥匙。"""
    s = 300
    x0, y0, x1, y1 = NOTE
    q = P([(x0, y0 + 6), (x1, y0), (x1 + 4, y1 - 4), (x0 + 6, y1 + 2)])
    pen.shade(q + P([12, 14]), amount=0.35, seed=s, soft=8.0, hatch=False)
    pen.cover(q, seed=s + 1, feather=0.8)
    pen.fill(q, 'cloth', seed=s + 2, tone=0.04)
    pen.line(np.vstack([q, q[:1]]), 2.6, tone=0.55, seed=s + 3, taper=(0.05, 0.1), head=0.2)
    # 卷起来的下角
    cn = P([(x1 + 4, y1 - 4), (x1 - 26, y1 - 2), (x1 - 4, y1 - 30)])
    pen.fill(cn, 'cloth', seed=s + 4, tone=0.14)
    pen.line(cn[[1, 2]], 2.0, tone=0.5, seed=s + 5, role='detail', taper=(0.1, 0.1))
    r = rng(s, 6)
    for k in range(5):
        yy = y0 + 46 + k * 26
        xs = np.linspace(x0 + 20, x1 - 24 - r.uniform(0, 60) * (k == 4), 7)
        ys = yy + np.sin(xs * 0.11 + k) * 3 + r.normal(0, 1.2, len(xs))
        pen.line(np.stack([xs, ys], 1), 2.4, tone=0.62, seed=(s, 7, k), role='detail', taper=(0.1, 0.4), dry=0.3,
                 dry_from=0.6)
    pen.dot((x0 + x1) / 2, y0 + 12, 9, 8, color='ink', tone=0.85, seed=s + 8)
    pen.lift(ell((x0 + x1) / 2 - 3, y0 + 9, 3, 2, n=8), amt=0.8, seed=s + 9, soft=0.5)
    # 钉子 + 钥匙（他留下的那把）
    nx, ny = 1792, 520
    pen.dot(nx, ny, 5, 5, color='ink', tone=0.9, seed=s + 10)
    ring = ell(nx + 2, ny + 22, 15, 17, 0, 360, 24)
    pen.line(ring, 3.0, tone=0.8, color='metal', seed=s + 11, closed=True, taper=(0, 0))
    head = ell(nx + 4, ny + 62, 20, 22, 0, 360, 24)
    pen.shade(head + P([8, 10]), amount=0.3, seed=s + 12, soft=4.0, hatch=False)
    pen.cover(head, seed=s + 13, feather=0.7)
    pen.fill(head, 'metal', seed=s + 14, tone=0.32)
    pen.line(head, 3.4, tone=0.85, seed=s + 15, closed=True, taper=(0, 0))
    pen.dot(nx + 4, ny + 56, 5, 5, color='paper', tone=0.0, seed=s + 16)
    blade = P([(nx - 2, ny + 82), (nx + 10, ny + 82), (nx + 10, ny + 162), (nx + 2, ny + 172), (nx - 2, ny + 160),
               (nx - 10, ny + 150), (nx - 2, ny + 140), (nx - 9, ny + 128), (nx - 2, ny + 118)])
    pen.shade(blade + P([8, 10]), amount=0.3, seed=s + 17, soft=3.0, hatch=False)
    pen.cover(blade, seed=s + 18, feather=0.7)
    pen.fill(blade, 'metal', seed=s + 19, tone=0.30)
    pen.line(np.vstack([blade, blade[:1]]), 2.8, tone=0.85, seed=s + 20, taper=(0, 0))
    pen.lift(tube([(nx + 6, ny + 90), (nx + 6, ny + 150)], [2, 2])[0], amt=0.6, seed=s + 21, soft=0.8)


def page(pen):
    """挂历纸：投影、纸、装订条、撕掉的月份留下的毛边、月份、星期、日期格、数字。"""
    s = 400
    x0, y0, x1, y1 = PAGE
    # 挂绳 + 钉子（钉子在画面上沿外）
    nx = (x0 + x1) / 2
    for k, xa in enumerate((x0 + 200, x1 - 200)):
        pen.line(P([(xa, y0 + 4), (xa + (nx - xa) * 0.5, y0 - 44), (nx, -100)]), 2.6, tone=0.6, seed=s + k,
                 taper=(0.1, 0.0), head=0)
    # 投影（光从左上来）
    pg = P([(x0, y0), (x1, y0 + 3), (x1 + 2, y1), (x0 - 2, y1 - 2)])
    pen.shade(pg + P([26, 30]), amount=0.40, seed=s + 2, soft=18.0, hatch=False)
    pen.cover(pg, seed=s + 3, feather=0.8)
    pen.fill(pg, 'cloth', seed=s + 4, tone=0.08, c_fade=False, broad=False, grad=(x0, y0, x1, y1, 0.35, 1.5))
    # 纸面右下角微微翘起（一点影）
    pen.shade(P([(x1 - 260, y1), (x1 + 2, y1 - 120), (x1 + 2, y1)]), amount=0.14, seed=s + 5, soft=20.0,
              hatch=False)
    pen.line(D([(x0, y0), (x0 - 2, y1 - 2)], 30), 5, tone=0.8, seed=s + 6, taper=(0.05, 0.3), head=0.4)
    pen.line(D([(x1, y0 + 3), (x1 + 2, y1)], 30), 3.2, tone=0.55, seed=s + 7, taper=(0.05, 0.5), head=0, dry=0.6,
             dry_from=0.4)
    pen.line(D([(x0 - 2, y1 - 2), (x1 + 2, y1)], 30), 4, tone=0.66, seed=s + 8, taper=(0.1, 0.3), head=0.3, dry=0.4,
             dry_from=0.6)
    # 装订条（深色，和厨房那本一样）
    hdr = P([(x0 - 4, y0 - 6), (x1 + 4, y0 - 3), (x1 + 3, y0 + 30), (x0 - 3, y0 + 27)])
    pen.cover(hdr, seed=s + 9, feather=0.8)
    pen.fill(hdr, 'lampshade', seed=s + 10, tone=0.78, c_fade=False, broad=False)
    pen.line(D([(x0 - 6, y0 + 28), (x1 + 5, y0 + 31)], 30), 4.5, tone=0.9, seed=s + 11, taper=(0.05, 0.1), head=0.3)
    pen.lift(tube([(x0 + 40, y0 + 4), (x1 - 300, y0 + 6)], [2, 4, 2])[0], amt=0.35, seed=s + 12, soft=2.0)
    for k, xa in enumerate((x0 + 200, x1 - 200)):
        pen.dot(xa, y0 + 10, 6, 6, color='metal', tone=0.5, seed=(s, 13, k))
    # 撕掉的月份留下的一溜毛边
    r = rng(s, 14)
    xs = np.linspace(x0 + 2, x1 - 2, 120)
    ys = y0 + 36 + r.uniform(0, 9, len(xs))
    pen.fill(np.vstack([np.stack([xs, ys], 1), P([(x1 - 2, y0 + 30), (x0 + 2, y0 + 30)])]), 'cloth', seed=s + 15,
             tone=0.10)
    pen.line(np.stack([xs, ys], 1), 2.0, tone=0.45, seed=s + 16, role='detail', taper=(0.05, 0.05), boil=0.2)
    # 月份：行楷“十二”+ 小“月”，下面一行淡墨小字
    put_text(pen, '十二', x0 + 44, y0 + 58, FONT_TITLE, 132, 0.92, (s, 20))
    put_text(pen, '月', x0 + 330, y0 + 112, FONT_TITLE, 66, 0.85, (s, 21))
    put_text(pen, '二〇二六', x1 - 250, y0 + 120, FONT_NUM, 40, 0.8, (s, 22))
    pen.line(D([(x0 + 40, y0 + 206), (x1 - 40, y0 + 203)], 30), 2.6, tone=0.5, seed=s + 23, taper=(0.1, 0.3),
             role='detail', dry=0.5, dry_from=0.4)
    # 星期
    for c, wd in enumerate('日一二三四五六'):
        put_text(pen, wd, GX0 + (c + 0.5) * CW, GY0 - 28, FONT_NUM, 32, 0.85 if 0 < c < 6 else 1.0, (s, 30, c),
                 anchor='mm')
    # 格线
    gx1, gy1 = GX0 + 7 * CW, GY0 + ROWS * RH
    for r_ in range(ROWS + 1):
        y = GY0 + r_ * RH
        pen.line(D([(GX0, y), (gx1, y + 1.5)], 40), 2.4, tone=0.42, seed=(s, 40, r_), role='detail',
                 taper=(0.02, 0.05), boil=0.25)
    for c in range(8):
        x = GX0 + c * CW
        pen.line(D([(x, GY0), (x + 1, gy1)], 40), 2.2, tone=0.38, seed=(s, 41, c), role='detail',
                 taper=(0.02, 0.05), boil=0.25)
    # 数字（左上角）+ 下面一行“农历”小字（几笔淡墨）
    for day in range(1, 32):
        r_, c, _ = cell(day)
        xx, yy = GX0 + c * CW + 12, GY0 + r_ * RH + 8
        wk = c in (0, 6)
        put_text(pen, str(day), xx, yy, FONT_NUM, 42, 1.0 if wk else 0.9, (s, 50, day))
        q = rng(s, 51, day)
        lx = xx + 2
        pen.line(P([(lx, yy + 62), (lx + q.uniform(22, 34), yy + 62 + q.uniform(-1, 1))]), 2.0, tone=0.32,
                 seed=(s, 52, day), role='detail', taper=(0.2, 0.3), boil=0.15)
    # 被红笔圈起来的那一天（很早以前）
    _, _, c3 = cell(RED_DAY)
    cx, cy = float(c3[0]) - 4, float(c3[1]) - 2
    loop = [(cx + 66, cy - 30), (cx + 10, cy - 50), (cx - 56, cy - 38), (cx - 76, cy + 4), (cx - 40, cy + 44),
            (cx + 30, cy + 46), (cx + 74, cy + 14), (cx + 58, cy - 36), (cx + 6, cy - 56)]
    pen.line(loop, 6.5, tone=1.0, color='mark', seed=s + 60, taper=(0.15, 0.4), head=0.4, dry=0.35, dry_from=0.7,
             role='detail', boil=0.25)
    # 早就划掉的那些天
    for day in CROSSED:
        draw_cross(pen, day)


def background(pen):
    wall(pen)
    window(pen)
    note_key(pen)
    page(pen)


# ================================================================= 动态
def snow(pen, t):
    r = rng(600)
    with pen.group('snow', boil=0.6):
        for i in range(40):
            far = i < 22
            sp = r.uniform(24, 40) if far else r.uniform(46, 78)
            size = r.uniform(1.5, 2.6) if far else r.uniform(3.0, 5.0)
            amp = r.uniform(4, 12)
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-80, WIN_X1)
            ys = r.uniform(0, 760)
            yy = (ys + sp * t) % 780 - 20
            xx = (xs + 6 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (WIN_X1 + 100) - 90
            if not (-80 < xx < WIN_X1 - 8 and -10 < yy < 752):
                continue
            if abs(xx - 59) < 7 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', i))


def motes(pen, t):
    """灯光里慢慢飘的浮尘（墙色上的几粒提白）。"""
    r = rng(650)
    with pen.group('motes', boil=0.3):
        for i in range(16):
            x = r.uniform(260, 1900) + 14 * math.sin(0.6 * t + i)
            y = (r.uniform(0, 1000) - 9 * t * r.uniform(0.5, 1.5)) % 1000
            # 只落在墙上（不在挂历纸、便条上）
            x0, y0, x1, y1 = PAGE
            if x0 - 10 < x < x1 + 30 and y0 - 20 < y < y1 + 30:
                continue
            pen.dot(x, y, r.uniform(1.6, 3.0), color='snow', tone=0.0, seed=('mote', i))


def new_crosses(pen, t):
    with pen.group('ink_new', boil=0.3, bleed=0.4):
        for d_ in NEW:
            ka, kb = stroke_progress(t, d_)
            if ka > 0:
                draw_cross(pen, d_, ka, kb, fresh=True)


def hand_kw(t):
    p, lf, ro = pen_state(t)
    tn = tip_now(t)
    if tn is not None:
        p = tn
    return dict(x=float(p[0]), y=float(p[1]), lift=float(lf), rot=float(ro) - 6.0, size=L_HAND, seed=('hp', 11),
                yaw=34.0, pitch=12.0, sleeve_len=1.3)


def hand_shadow(pen, kw):
    """手和笔在挂历上的影：先在一支空笔上量出剪影，离纸越远（离笔尖越远）影子错得越开。"""
    dummy = core.Pen('C', pen.d)
    info = hands.hand_pen(dummy, **kw)
    tip = np.float32([kw['x'], kw['y']])
    lf = kw['lift']
    out = []
    for poly in info['sil']:
        q = np.asarray(poly, np.float32)
        dist = np.hypot(*(q - tip).T)
        k = np.clip(dist / 300.0, 0, 1)[:, None] + 0.3 * lf
        out.append(q + P([58, 64]) * k)
    with pen.group('hand_shadow', boil=0.3):
        pen.shade(out, amount=0.40, seed=('hsh', 11), soft=16.0, hatch=False)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    pan = float(kw.get('pan', PAN))
    u = ease_io(clamp((t - T0) / (T1 - T0)))
    with pen.view(1.0, -pan * u, 0.0):
        with pen.group('bg', boil=BG_BOIL):
            background(pen)
        snow(pen, t)
        motes(pen, t)
        new_crosses(pen, t)
        hk = hand_kw(t)
        hand_shadow(pen, hk)
        hands.hand_pen(pen, **hk)
