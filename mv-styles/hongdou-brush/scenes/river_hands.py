# -*- coding: utf-8 -*-
"""
第 18 镜（69.81–72.80，B 油画棒）“示例歌词”：金色黄昏，河岸草地上两人的手（特写，从后上方看）。
左边她的右手、右边他的左手，手背朝上平放在草上。他的小指在“水”（70.43）前后慢慢抬起、伸过来，
勾住她的小指往下扣，她的小指也弯起来迎上；一根红线松松地绕在两根小指上，线头拖在草里。
逆光：手背压暗，朝着太阳（画面上方）的轮廓镶一圈暖金边，两只手的影子朝镜头这边拖。
身后是虚焦的河面：一颗颗光斑（河面反光）一闪一闪、慢慢顺水往右漂；远岸是一抹虚掉的紫；
中景几根芦苇的穗子在风里摆；前景几片草叶在风里晃（虚、暗、镶金边）；逆光里飘着发亮的绒絮。
“长流”（71.35–72.07）起镜头极慢地推近两根勾着的小指（pen.view，前景比手推得多一点，背景几乎不动）。
调色和 river.py 一致（梅紫的影、#FFA640 的金边、#FFD27A / #FFF4C8 的光）。

draw(pen, **kw)   kw（都可省）：t 覆盖时间；hook 0..1 覆盖勾手指；zoom 覆盖推镜倍数
"""
import math

import numpy as np

from core import densify, ell, bez, rect, spline, tube, rng, clamp, smooth01, ease_io, ease_out, lerp, W, H
import hands

# ---------------------------------------------------------------- 时间
T0, T1 = 69.81, 72.80
T_HOOK0, T_HOOK1 = 69.92, 70.95      # “水” 70.43 在中间
T_PUSH0, T_PUSH1 = 71.20, 72.80      # 长流：极慢推近
ZOOM1 = 1.20

# ---------------------------------------------------------------- 构图
HOOK = (960.0, 500.0)                # 两根小指指根之间
SIZE = 660.0
BANK_Y = 400.0                       # 近岸（虚焦）和草地的分界
RIVER = (60.0, 420.0)                # 河面（虚焦）的上下沿
BG_BOIL = 0.25


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


# ================================================================= 表演
def hook_amt(t):
    return float(ease_io((t - T_HOOK0) / (T_HOOK1 - T_HOOK0)))


def zoom_amt(t):
    return 1.0 + (ZOOM1 - 1.0) * float(ease_io((t - T_PUSH0) / (T_PUSH1 - T_PUSH0)))


# ================================================================= 背景（静态，缓存）
def _river(pen):
    """虚焦的河面和远岸：大块柔和的颜色，没有轮廓线。"""
    s = 8100
    top = rect(-30, -30, W + 30, BANK_Y + 60)
    pen.cover(top, seed=s)
    # 天边的一抹金（画面最上沿）
    pen.fill(top, '#F79A48', seed=s + 1, b_angle=4)
    pen.fill(rect(-30, -30, W + 30, 90), '#FFC75A', seed=s + 2, grad=(0, -30, 0, 90, 1.0, 0.2), b_angle=2)
    # 远岸：一抹虚掉的紫（上沿起伏很缓）
    bank = np.vstack([D([(-30, 74), (300, 62), (620, 80), (980, 58), (1300, 76), (1640, 60), (W + 30, 70)], 40),
                      [[W + 30, 136], [-30, 136]]])
    pen.fill(bank, '#7C5C9A', seed=s + 3, b_angle=6, b_size=1.6)
    pen.fill(bank, '#B85E4E', seed=s + 4, grad=(0, 60, 0, 136, 0.7, 0.0), b_angle=6, b_size=1.6)
    # 河面：深靛紫底 → 粉 → 橙，右上落日那边一条金色的光带
    riv = rect(-30, 118, W + 30, BANK_Y + 60)
    pen.fill(riv, '#2E2C74', seed=s + 5, b_angle=2, b_size=1.5)
    pen.fill(riv, '#C85A78', seed=s + 6, grad=(0, 120, 0, 330, 0.85, 0.0), b_angle=3, b_size=1.5)
    pen.fill(riv, '#FF9C4A', seed=s + 7, grad=(1500, 130, 900, 330, 0.9, 0.0), b_angle=3, b_size=1.5)
    path = spline(P([(1380, 118), (1560, 118), (1700, 230), (1820, 420), (1180, 420), (1300, 230)]), 8.0, closed=True)
    pen.fill(path, '#FFD25A', seed=s + 8, rgrad=(1500, 130, 30, 340, 1.0, 0.2), b_angle=2, b_size=1.6)
    pen.light(1500, 160, 520, 220, amt=0.45, color='#FFD66A', seed=s + 9)


def _grass(pen):
    """近处的草地：橄榄金底 + 两层排线（暗的竖向 + 逆光的金），往镜头这边越来越暗。"""
    s = 8200
    up = D([(-30, BANK_Y + 18), (400, BANK_Y + 6), (900, BANK_Y + 14), (1400, BANK_Y + 2), (W + 30, BANK_Y + 12)], 40)
    g = np.vstack([up, [[W + 30, H + 30], [-30, H + 30]]])
    pen.cover(g, seed=s)
    pen.fill(g, '#6A5A26', seed=s + 1, b_angle=84, grad=(0, BANK_Y, 0, H, 0.7, 1.0))
    pen.fill(g, '#E3A23E', seed=s + 2, grad=(0, BANK_Y, 0, 720, 1.0, 0.0), b_angle=86)
    pen.fill(g, '#F7C65C', seed=s + 3, rgrad=(1400, BANK_Y, 80, 700, 0.8, 0.0), b_angle=86)
    pen.hatch(g, angle=96, spacing=8, tone=0.55, color='#3A3A1A', seed=s + 4, grad=(0, 560, 0, H, 0.0, 1.0))
    pen.hatch(g, angle=80, spacing=10, tone=0.45, color='#FFD77A', seed=s + 5, grad=(0, BANK_Y, 0, 640, 1.0, 0.0))
    # 近岸那一溜虚焦的草尖被照成金色（分界处柔一点）
    pen.light(960, BANK_Y + 10, 1100, 60, amt=0.35, color='#FFC75A', seed=s + 6)
    # 前景压暗（暗角）
    pen.shade([rect(-40, 820, W + 40, H + 30)], amount=0.32, seed=s + 7, angle=6, grad=(0, 820, 0, H, 0.0, 1.0),
              color='#3A2448')
    pen.shade([rect(-40, -40, 260, H + 40)], amount=0.25, seed=s + 8, angle=90, grad=(-40, 0, 260, 0, 1.0, 0.0),
              color='#3A2448')
    pen.shade([rect(W - 260, -40, W + 40, H + 40)], amount=0.25, seed=s + 9, angle=90,
              grad=(W + 40, 0, W - 260, 0, 1.0, 0.0), color='#3A2448')
    # 草地上散着几朵小野花（远的虚）、一片落叶
    r = rng(8250)
    for k in range(16):
        x = r.uniform(80, W - 80)
        y = r.uniform(BANK_Y + 60, 860)
        if 600 < x < 1360 and y > 300:
            continue
        rr = 3.0 + 6.0 * (y - BANK_Y) / 500
        pen.dot(x, y, rr, color='#FFF0C0' if k % 3 else '#F4A9B8', tone=0.9, seed=(s + 20, k))
        pen.dot(x, y, rr * 0.4, color='#F2B45A', tone=0.9, seed=(s + 21, k))
    lf = (420.0, 720.0)
    leaf = spline(P([(lf[0] - 46, lf[1] + 6), (lf[0] - 10, lf[1] - 20), (lf[0] + 40, lf[1] - 14), (lf[0] + 50, lf[1]),
                     (lf[0] + 6, lf[1] + 16)]), 4.0, closed=True)
    pen.fill(leaf, '#C8642E', seed=s + 30, b_clean=True)
    pen.line(P([(lf[0] - 40, lf[1] + 4), (lf[0] + 46, lf[1] - 4)]), 2.0, tone=0.7, color='#7A3A1E', seed=s + 31,
             role='detail', taper=(0.1, 0.4))


def background(pen):
    _river(pen)
    _grass(pen)


# ================================================================= 动态
def bokeh(pen, t):
    """河面的光斑（虚焦的反光）：圆圆的一颗颗，亮起来、顺水往右漂一小段、暗下去，再在别处亮起；光带里最密最大。"""
    r = rng(8300)
    with pen.group('bokeh', boil=0.4):
        for i in range(56):
            in_path = i < 20
            life = r.uniform(1.2, 2.6)
            off = r.uniform(0, 1)
            cf = t / life + off
            cyc = math.floor(cf)
            ph = cf - cyc
            q = rng(8301, i, cyc)
            if in_path:
                yv = q.uniform(0, 1)
                x = 1500 + q.uniform(-1, 1) * (60 + 260 * yv)
                y = 140 + 250 * yv
                rad = q.uniform(14, 34) * (0.7 + 0.6 * yv)
            else:
                x = q.uniform(-20, W + 20)
                y = q.uniform(150, BANK_Y + 10)
                rad = q.uniform(8, 26) * (0.6 + 0.8 * (y - 150) / 270)
            x += 26.0 * ph                       # 顺水往右漂
            tw = 0.75 + 0.25 * math.sin(2 * math.pi * r.uniform(1.2, 2.6) * t + r.uniform(0, 6.3))
            a = math.sin(math.pi * ph) ** 1.3 * tw
            if a < 0.18:
                continue
            col = '#FFE9A8' if (in_path or a > 0.75) else '#FFC870'
            if rad > 24:
                pen.light(x, y, rad * 1.8, rad * 1.6, amt=0.22 * a, color='#FFD66A', seed=('bkl', i, cyc))
            pen.dot(x, y, rad * (0.6 + 0.3 * a), color=col, tone=0.9, seed=('bk', i, cyc), soft=3.0)


def _reed_specs():
    r = rng(8400)
    out = []
    # 近岸（虚焦）的芦苇：左右两小丛，在手的后面；穗子都在画面里
    for k in range(3):
        out.append((r.uniform(80, 520), BANK_Y + r.uniform(20, 60), r.uniform(240, 330), r.uniform(-0.10, 0.12),
                    r.uniform(0, 6.28)))
    for k in range(3):
        out.append((r.uniform(1420, 1860), BANK_Y + r.uniform(20, 60), r.uniform(200, 280), r.uniform(-0.06, 0.14),
                    r.uniform(0, 6.28)))
    return out


REEDS = _reed_specs()


def reeds(pen, t):
    """虚焦的芦苇：粗而软的暗茎、一大团逆光发亮的穗子（没有硬轮廓），在风里慢慢摆。"""
    with pen.group('reeds', boil=0.5):
        for k, (bx, by, h, lean0, ph) in enumerate(REEDS):
            gust = 0.07 * max(0.0, math.sin(2 * math.pi * 0.16 * t + bx * 0.002)) ** 2
            ang = lean0 + 0.06 * math.sin(2 * math.pi * 0.45 * t + ph) + gust
            tip = P([bx + h * math.sin(ang), by - h * math.cos(ang)])
            mid = P([bx + h * 0.5 * math.sin(ang * 0.4), by - h * 0.5 * math.cos(ang * 0.4)])
            stem = bez((bx, by), mid, tip, 10)
            pen.line(stem, 9.0, tone=0.55, color='#6A4630', seed=(8410, k), role='detail', taper=(0.05, 0.4),
                     b_width=1.3, dry=0.3)
            d = (tip - stem[-3]) / (np.hypot(*(tip - stem[-3])) + 1e-6)
            wind = P([1.0, 0.3])
            L = h * 0.42
            a = tip - d * L * 0.25
            c = tip + (d * 0.35 + wind * 0.8) * L * (0.85 + 0.2 * math.sin(t * 1.3 + ph))
            m = (a + c) / 2 + P([0, -L * 0.12])
            axis = bez(a, m, c, 8)
            plume, _, _ = tube(axis, [L * 0.12, L * 0.30, L * 0.28, L * 0.10])
            pen.light(float(m[0]), float(m[1]), L * 0.75, L * 0.5, amt=0.25, color='#FFD66A', seed=(8415, k))
            pen.fill(plume, '#F2C27A', seed=(8420, k), b_clean=True, b_size=1.6)
            # 穗子上细细的绒毛（顺风的几笔奶白）
            nn = len(axis)
            for j in range(6):
                q0 = axis[1 + j % (nn - 2)]
                tipj = q0 + (wind * 0.9 + d * 0.2) * L * (0.25 + 0.06 * j) + P([0, L * 0.04 * (j % 3 - 1)])
                pen.line(P([q0, (q0 + tipj) / 2 + P([0, -3]), tipj]), 2.2, tone=0.8, color='#FFF0C0',
                         seed=(8430, k, j), role='detail', taper=(0.1, 0.7))


def blades(pen, t):
    """前景的草叶：从画面下沿和两侧伸进来，暗、虚、镶金边，在风里晃。不挡勾着的小指。"""
    r = rng(8500)
    specs = []
    for k in range(6):          # 左下
        specs.append((r.uniform(-40, 420), H + 30, r.uniform(260, 520), r.uniform(-0.25, 0.35), r.uniform(0, 6.28)))
    for k in range(6):          # 右下
        specs.append((r.uniform(1500, 1960), H + 30, r.uniform(260, 520), r.uniform(-0.35, 0.25), r.uniform(0, 6.28)))
    for k in range(3):          # 中下（矮）
        specs.append((r.uniform(560, 1360), H + 30, r.uniform(90, 170), r.uniform(-0.3, 0.3), r.uniform(0, 6.28)))
    with pen.group('blades', boil=0.6):
        for k, (bx, by, h, lean0, ph) in enumerate(specs):
            ang = lean0 + 0.07 * math.sin(2 * math.pi * 0.5 * t + ph) + 0.03 * math.sin(2 * math.pi * 1.1 * t + ph * 2)
            bend = 0.35 * (1 if lean0 > 0 else -1)
            tip = P([bx + h * math.sin(ang + bend), by - h * math.cos(ang + bend)])
            mid = P([bx + h * 0.55 * math.sin(ang), by - h * 0.55 * math.cos(ang)])
            ax = bez((bx, by), mid, tip, 12)
            w0 = 16.0 + 10.0 * (h / 520)
            blade, _, _ = tube(ax, [w0, w0 * 0.9, w0 * 0.6, w0 * 0.2])
            pen.fill(blade, '#2E3418' if k % 3 else '#3A3A1A', seed=(8510, k), b_clean=True, b_size=1.3)
            # 朝光的一侧金边
            pen.line(ax[3:] + P([1.5, -1.0]), 3.0, tone=0.9, color='#FFA640', seed=(8520, k), role='detail',
                     taper=(0.2, 0.6))


def motes(pen, t):
    """逆光里飘着的绒絮（芦花、草籽），被夕阳照得发亮，慢慢往右上飘。"""
    r = rng(8600)
    with pen.group('motes', boil=0.4):
        for i in range(26):
            life = r.uniform(3.0, 5.5)
            off = r.uniform(0, 1)
            cf = t / life + off
            cyc = math.floor(cf)
            ph = cf - cyc
            q = rng(8601, i, cyc)
            x0, y0 = q.uniform(100, 1800), q.uniform(120, 900)
            x = x0 + 70 * ph + 9 * math.sin(t * 1.3 + i)
            y = y0 - 50 * ph + 6 * math.sin(t * 0.9 + 2 * i)
            a = math.sin(math.pi * ph) * (0.6 + 0.4 * math.sin(t * 3.1 + i * 1.7))
            if a < 0.25:
                continue
            rr = 2.0 + 3.0 * (y0 / 900)
            pen.dot(x, y, rr * (0.7 + 0.4 * a), color='#FFF0B8', tone=0.9, seed=('rmote', i, cyc))


def hand_shadow(pen, sil):
    """两只手的影子：太阳在河那边（画面上方），影子朝镜头这边（下方）拖。"""
    if not sil:
        return
    with pen.group('hshadow', boil=0.4):
        polys = [np.float32(p) * P([1.0, 1.0]) + P([18, 46]) for p in sil]
        pen.shade(polys, amount=0.55, seed=8700, angle=96, color='#3A2050', soft=10.0)


def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    h = float(kw['hook']) if kw.get('hook') is not None else hook_amt(t)
    z = float(kw['zoom']) if kw.get('zoom') is not None else zoom_amt(t)
    hx, hy = HOOK
    # 背景几乎不推（远、虚），只算 1/4 的推镜
    zb = 1.0 + (z - 1.0) * 0.25
    with pen.group('bg', boil=BG_BOIL, cache=('river_hands', pen.d % 3)):
        background(pen)                      # 远处、虚焦：推镜时不动（也让缓存一直有效）
    with pen.view(zb, hx * (1 - zb), hy * (1 - zb)):
        bokeh(pen, t)
        reeds(pen, t)
    with pen.view(z, hx * (1 - z), hy * (1 - z)):
        # 呼吸一样的微动
        rot = 0.8 * math.sin(t * 1.4)
        # 先画手、拿到剪影，再把影子的指令插到手的前面（影子在手下面）
        i0 = len(pen.ops)
        info = hands.pinky_hook2(pen, hx, hy, rot=rot, size=SIZE, seed=8000, hook=h, gap=0.18, pitch=42.0,
                                tail_len=0.6, backlit=0.6, thread_w=3.2, t=t)
        hand_ops = pen.ops[i0:]
        del pen.ops[i0:]
        hand_shadow(pen, info['sil'])
        pen.ops.extend(hand_ops)
    zf = 1.0 + (z - 1.0) * 1.4
    with pen.view(zf, hx * (1 - zf), hy * (1 - zf)):
        blades(pen, t)
        motes(pen, t)
