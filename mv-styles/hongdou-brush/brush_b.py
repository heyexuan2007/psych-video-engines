# -*- coding: utf-8 -*-
"""
brush_b.py —— B 油画棒笔刷（“也许”：期盼和幻想。浓烈、厚涂、暖色）

材质（从 style_B/hd.py 移植并加厚）
  纸   深靛蓝色粉彩纸：蜂窝纸齿 + 竖条纹 + 浅色纤维 + 浮雕光照。纸齿高度 GRAIN（均匀分布 0..1）决定蜡能不能落进去。
  蜡   每一笔先画成“压力覆盖图”（两张交替缓冲相加，叠笔更实），再过纸齿响应
          a = clip((cov·gain + GRAIN·k − thr)·s)
       所以蜡总被纸齿打断，凹坑里透出深靛蓝。
  填色 fill = 薄薄的蜡底 + 主方向排线（密、全压）+ 斜向叠色（偏亮偏暖，成片）+ 少量深色/冷色碎笔（叠色）。
       排线每个绘制序号重画（种子含 d），纸齿不动，所以亮度稳定、只有笔触在“沸腾”。
  阴影 shade = 带方向的深色叠涂：在已有颜色上乘一个偏梅紫的暗色（暖色面→红棕，冷色面→深蓝紫）。
  线   line = 分段带收笔的蜡笔轮廓（会抬手、有重叠/小缺口、部分复描），默认深暖棕；
       sketch/construct = 白色粉笔草稿线（更粗颗粒、断得更多、可复描 reps 遍）。
  高光 lift = 奶白蜡笔短笔触；light = 被纸齿调制的暖光（screen 叠加）。
  点   dot = 蜡点；红色的点（红豆）自动加暗边和一个奶白高光。
  颜色 PAL 的固有色在 B 里换成更浓烈、偏暖的版本（_BPAL）；未登记的颜色走通用变换 _warmify。
       冷色（夜空、水、他的毛衣）保留色相、加深加饱和，和暖色形成强对比。red=True 的一律保持红。
  抖动 每个顶层 group 一个平滑位移场（同一个人的各部件一起动，不散架），幅度 = boil × 1.7px（比另两种笔刷略大）。
  缓存 第一个 group 带 cache 时，按 (B, cache, 指令内容哈希) 把渲染结果存在进程内 dict；
       缓存层内部的随机种子用 cache 键代替 d，所以无论哪个进程先渲染，同一个变体结果都一样。

识别的 hints（不认识的忽略）
  fill : b_angle(度) 排线方向 / b_size 笔触粗细倍数 / b_layers 叠色层数(1..3) / streak 头发类长条纹 / dry 更干更碎
  line : head 起笔重 / lift 收笔轻 / dry 干笔 / breaks 断线 / reps 复描遍数 / spread 复描离散 / fade 沿笔变淡
         b_width 线宽倍数 / b_color 覆盖线色
  shade: b_size / b_mode='color' 用 color 实涂而不是乘暗
  lift : b_mode='paper' 真的擦回纸色（默认是奶白高光）
"""
import colorsys
import math
import zlib

import cv2
import numpy as np

import core
from core import W, H, LYRIC_RED, region_mask, sd, spline

VERSION = 'b5'
BOIL_PX = 1.7           # boil=1 时的位移幅度（像素）
RELAYOUT_BOIL = 0.75    # boil 不小于它的层：排线每个绘制序号整片重画

# =========================================================================== 随机
_M64 = (1 << 64) - 1


def _flat(keys, out):
    for k in keys:
        if isinstance(k, (tuple, list)):
            _flat(k, out)
        elif isinstance(k, (bool, np.bool_)):
            out.append(int(k))
        elif isinstance(k, (int, np.integer)):
            out.append(int(k) & 0xFFFFFFFF)
        elif isinstance(k, (float, np.floating)):
            out.append(zlib.crc32(('%.4f' % float(k)).encode()))
        else:
            out.append(str(k))
    return out


def _R(*keys):
    return np.random.default_rng(sd(*_flat(keys, [])))


def _hx(c):
    return core.hex2rgb(c)


# =========================================================================== 噪声 / 纸
def _value_noise(h, w, cell, key):
    r = _R('vn', key)
    gh, gw = h // cell + 4, w // cell + 4
    g = r.random((gh, gw), dtype=np.float32)
    big = cv2.resize(g, (gw * cell, gh * cell), interpolation=cv2.INTER_CUBIC)
    return big[cell:cell + h, cell:cell + w]


def _fbm(h, w, cell, key, octaves=4, gain=0.5):
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        acc += amp * _value_noise(h, w, c, (key, o))
        tot += amp
        amp *= gain
    acc /= tot
    lo, hi = np.percentile(acc[::7, ::7], [1, 99])
    return np.clip((acc - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)


PAPER_LO = _hx('#171C3C')       # 深靛蓝
PAPER_HI = _hx('#262C5A')


def _make_paper(seed=11):
    h, w = H, W
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = (_fbm(h, w, 110, (seed, 'wx'), 3) - 0.5) * 3.2
    wy = (_fbm(h, w, 110, (seed, 'wy'), 3) - 0.5) * 3.2
    X = xx + wx
    Y = yy + wy
    # 抖动六角格的最近点距离 → 蜂窝纸齿
    a = 6.6
    s3 = math.sqrt(3.0)
    jj = Y / (a * s3 / 2)
    ii = (X - jj * a / 2) / a
    i0 = np.floor(ii).astype(np.int32)
    j0 = np.floor(jj).astype(np.int32)
    r = _R('paper', seed)
    NI, NJ = 420, 220
    oxt = r.uniform(-2.1, 2.1, (NI, NJ)).astype(np.float32)
    oyt = r.uniform(-2.1, 2.1, (NI, NJ)).astype(np.float32)
    best = np.full((h, w), 1e9, np.float32)
    for di in (0, 1):
        for dj in (0, 1):
            ci = i0 + di
            cj = j0 + dj
            ox = oxt[(ci + 150) % NI, (cj + 10) % NJ]
            oy = oyt[(ci + 150) % NI, (cj + 10) % NJ]
            cx = ci * a + cj * (a / 2) + ox
            cy = cj * (a * s3 / 2) + oy
            np.minimum(best, np.hypot(X - cx, Y - cy), out=best)
    honey = np.clip(best / (a * 0.5), 0, 1.15)            # 0 = 凹坑中心, 1 = 凸起的墙
    stripes = 0.5 + 0.5 * np.sin(2 * np.pi * (X / 13.0 + 0.35 * _fbm(h, w, 160, (seed, 'st'), 2)))
    fine = cv2.GaussianBlur(r.random((h, w), dtype=np.float32), (0, 0), 1.1)
    fine = (fine - fine.mean()) / (fine.std() + 1e-6)
    low = _fbm(h, w, 200, (seed, 'low'), 3)
    hgt = (0.46 * honey + 0.12 * stripes + 0.20 * fine + 0.16 * low).astype(np.float32)
    flat = hgt.ravel()
    order = np.argsort(flat, kind='stable')
    T = np.empty(flat.size, np.float32)
    T[order] = np.linspace(0, 1, flat.size, dtype=np.float32)
    T = T.reshape(h, w)
    # 纸面颜色
    mott = _fbm(h, w, 260, (seed, 'mott'), 4)
    g = np.clip((xx / w) * 0.30 + (1 - yy / h) * 0.40 + (mott - 0.5) * 0.5, 0, 1)
    paper = PAPER_LO[None, None, :] * (1 - g[..., None]) + PAPER_HI[None, None, :] * g[..., None]
    hs = cv2.GaussianBlur(honey, (0, 0), 0.7)
    paper = paper * (0.86 + 0.24 * hs[..., None] + 0.05 * stripes[..., None])
    em = (np.roll(np.roll(hs, 1, 0), 1, 1) - np.roll(np.roll(hs, -1, 0), -1, 1))
    em = em / (np.abs(em).max() + 1e-6)
    em = (em + 0.25 * (stripes - 0.5)).astype(np.float32)
    fib = np.zeros((h, w), np.float32)
    for _ in range(900):
        x0, y0 = r.uniform(0, w), r.uniform(0, h)
        ang = r.uniform(0, np.pi)
        ln = r.uniform(3, 9)
        p1 = (int(x0 * 4), int(y0 * 4))
        p2 = (int((x0 + math.cos(ang) * ln) * 4), int((y0 + math.sin(ang) * ln) * 4))
        cv2.line(fib, p1, p2, float(r.uniform(0.25, 0.6)), 1, cv2.LINE_AA, 2)
    paper = paper + fib[..., None] * np.float32([0.10, 0.11, 0.15])
    return T, paper.astype(np.float32), em


GRAIN = PAPER = EMBOSS = NOISE_A = NOISE_B = FINISH = DITHER = None


def _init_tex():
    global GRAIN, PAPER, EMBOSS, NOISE_A, NOISE_B, FINISH, DITHER
    if GRAIN is not None:
        return
    GRAIN, PAPER, EMBOSS = _make_paper()
    NOISE_A = (_fbm(H, W, 46, 'nA', 3) - 0.5).astype(np.float32)
    NOISE_B = (_fbm(H, W, 90, 'nB', 3) - 0.5).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = ((xx - W * 0.52) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.72)) ** 2
    vig = (1 - 0.20 * np.clip(dd - 0.35, 0, 1.2)).astype(np.float32)
    FINISH = ((1 + 0.10 * EMBOSS) * vig).astype(np.float32)
    DITHER = ((_R('dither').random((H, W), dtype=np.float32) - 0.5) / 255.0).astype(np.float32)


# 纸齿响应 (k, thr, s)：a = clip((cov·gain + GRAIN·k − thr)·s)
TOOTH = {
    'wax': (1.00, 1.01, 5.5),     # 油画棒：重压，单笔约 95% 覆盖，只在最深的纸坑里断开
    'base': (1.00, 0.92, 3.5),    # 蜡底：凹坑只是半透，不留硬黑点
    'soft': (1.00, 1.18, 4.0),    # 轻涂
    'heavy': (0.85, 0.78, 6.0),   # 重压，几乎盖满
    'chalk': (1.20, 1.30, 3.4),   # 粉笔：颗粒更粗、断得更多
}


def _tooth(cov, x0, y0, tooth='wax', gain=1.0):
    h, w = cov.shape
    k, thr, s = TOOTH[tooth]
    a = cov * np.float32(gain)
    a += GRAIN[y0:y0 + h, x0:x0 + w] * np.float32(k)
    a -= np.float32(thr)
    a *= np.float32(s)
    np.clip(a, 0, 1, out=a)
    return a


# =========================================================================== 颜色
_BPAL = {
    'ink': '#2A1418', 'paper': '#F3E2C2',
    'skin': '#F7C39A', 'skin_sh': '#DC8670', 'blush': '#F2706C', 'lips': '#CF3F52',
    'hair': '#1E1730', 'sweater': '#F6DFB2', 'sweater_sh': '#B98AA8', 'skirt': '#4B2C60',
    'eye': '#1C1016', 'tear': '#A6E2F6',
    'boy_hair': '#2B1D1E', 'boy_sweater': '#3557A8', 'boy_shirt': '#F4E6C8', 'boy_pants': '#4D4060',
    'graphite': '#E4E6EE',
    'wall': '#EE9E50', 'wood': '#D97B3A', 'wood_d': '#8E3B20', 'floor': '#A9532E',
    'cabinet': '#2C8C84', 'metal': '#A6B6CE', 'enamel': '#F6E9D0', 'glass': '#B4DDF2',
    'fridge': '#BFE2C4', 'plant': '#4AA548', 'terra': '#DC6434', 'cloth': '#F4E8D2',
    'lamp': '#FFC24A', 'lampshade': '#239C80',
    'night': '#1C2A72', 'night_l': '#5A78D8', 'snow': '#FCF5E8', 'roof': '#3D4596',
    'win_warm': '#FFC23C', 'sky': '#78B4EC', 'dusk': '#FF9550', 'sun': '#FFD246',
    'water': '#3C8ED0', 'water_d': '#1E529E', 'grass': '#A2B83E', 'grass_d': '#5E8A30',
    'stone': '#B9967C', 'reed': '#E8B656', 'tree': '#3A7A48',
    'bean': '#D7273A', 'bean_d': '#8E1226', 'soup': '#A0142A', 'hairpin': '#E62E30',
    'redline': '#E62E30', 'mark': '#E62E30',
}
_BPAL = {k: _hx(v) for k, v in _BPAL.items()}

LINE_COL = _hx('#2A1416')       # 默认蜡笔轮廓：深暖棕
CHALK = _hx('#ECEEF4')          # 草稿：白粉笔
CHALK2 = _hx('#C4CFEA')
CREAM = _hx('#FFF2D8')          # 奶白高光
LILAC = _hx('#9AA6E6')          # 深色上的高光（头发的光泽）
SHADE_MUL = np.float32([0.62, 0.38, 0.50])     # 阴影（中暗色上）：偏砖红/梅紫的乘暗（保持浓度，不发灰）
SHADE_MUL_LIGHT = np.float32([0.80, 0.64, 0.78])   # 阴影（浅色上：皮肤、毛衣、奶白）：玫瑰/淡紫，不发泥
LY_UNSUNG = _hx('#F4E8CE')
LY_SUNG = np.clip(LYRIC_RED * np.float32([1.42, 1.25, 1.25]), 0, 1).astype(np.float32)   # 红豆红（在深色纸上提亮）
LY_HALO = _hx('#0E0A1C')
HUE_VEC = np.float32([0.05, -0.012, -0.04])    # 色彩的低频偏移（暖↔冷）


def _hue_toward(h, target, k):
    dh = ((target - h + 0.5) % 1.0) - 0.5
    return (h + dh * k) % 1.0


def _warmify(rgb, red=False):
    r, g, b = [float(x) for x in np.clip(rgb, 0, 1)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if red:
        s = min(1.0, s * 1.3 + 0.05)
        l = min(0.62, max(l, 0.42))
        h = _hue_toward(h, 0.985, 0.5)
    elif s < 0.10:
        # 中性色：往奶油/暖灰/暖黑推
        if l > 0.70:
            return np.clip(np.float32([r, g, b]) * 0.5 + _hx('#F6E2BE') * 0.5, 0, 1)
        if l < 0.28:
            return np.clip(np.float32([r, g, b]) * 0.5 + _hx('#2A1A24') * 0.5, 0, 1)
        h, s = 0.06, 0.28
    else:
        hd = h * 360
        s = min(1.0, s * 1.5 + 0.08)
        if hd < 75 or hd > 300:
            h = _hue_toward(h, 28 / 360 if hd < 75 else 345 / 360, 0.25)
        elif hd < 165:
            h = _hue_toward(h, 95 / 360, 0.2)
        else:
            h = _hue_toward(h, 225 / 360, 0.15)
            l = l * 0.88
    return np.float32(colorsys.hls_to_rgb(h, l, s))


_CCACHE = {}


def bcolor(spec, default=None):
    """规范化颜色 dict → B 的颜色 rgb。"""
    if spec is None:
        return default
    name = spec.get('name')
    if name in _BPAL:
        return _BPAL[name]
    key = (tuple(np.round(spec['rgb'], 4)), bool(spec.get('red')))
    c = _CCACHE.get(key)
    if c is None:
        c = _CCACHE[key] = _warmify(spec['rgb'], spec.get('red', False))
    return c


def _variant(col, dl, hue_target, hk, ds=1.0, red=False):
    r, g, b = [float(x) for x in np.clip(col, 0, 1)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if red:
        hue_target, hk = 0.985, hk * 0.4
    if s > 0.06:
        h = _hue_toward(h, hue_target, hk)
    l = min(0.97, max(0.02, l + dl))
    s = min(1.0, s * ds)
    return np.float32(colorsys.hls_to_rgb(h, l, s))


def _is_cool(col):
    h, l, s = colorsys.rgb_to_hls(*[float(x) for x in np.clip(col, 0, 1)])
    return s > 0.12 and 0.45 < h < 0.80


def _light_var(col, red=False):
    if _is_cool(col):
        return _variant(col, 0.10, 200 / 360, 0.20, 1.05, red)     # 冷色的亮笔偏青，不发紫
    return _variant(col, 0.09, 46 / 360, 0.22, 1.08, red)


def _dark_var(col, red=False):
    return _variant(col, -0.15, 340 / 360, 0.22, 1.15, red)


def _cool_var(col, red=False):
    return _variant(col, -0.07, 250 / 360, 0.10, 1.0, red)


# =========================================================================== 几何
def _resample(P, step=4.0, closed=False):
    P = np.asarray(P, np.float64)
    if closed:
        P = np.concatenate([P, P[:1]])
    seg = np.hypot(*(P[1:] - P[:-1]).T)
    L = np.concatenate([[0], np.cumsum(seg)])
    if L[-1] < 1e-6:
        return P[:1].copy()
    n = max(2, int(L[-1] / step) + 1)
    s = np.linspace(0, L[-1], n, endpoint=not closed)
    return np.stack([np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])], 1)


def _normals(P):
    t = np.gradient(P, axis=0)
    t /= (np.hypot(t[:, 0], t[:, 1])[:, None] + 1e-9)
    return np.stack([-t[:, 1], t[:, 0]], 1)


class _Field:
    """平滑位移场（单位幅度）。一个顶层 group 共用一个，部件一起动。"""

    def __init__(self, key, d, wl=230.0, nw=3, trans=0.45):
        r = _R('boil', key, d)
        self.w = []
        for _ in range(nw):
            ang = r.uniform(0, 2 * np.pi)
            k = 2 * np.pi / (wl * r.uniform(0.7, 1.4))
            self.w.append((k * math.cos(ang), k * math.sin(ang), r.uniform(0, 2 * np.pi), r.uniform(0, 2 * np.pi),
                           r.normal(0, 0.62), r.normal(0, 0.62)))
        self.t = r.normal(0, trans, 2)

    def disp(self, P):
        P = np.asarray(P, np.float32).reshape(-1, 2)
        dx = np.full(len(P), self.t[0], np.float32)
        dy = np.full(len(P), self.t[1], np.float32)
        for kx, ky, p1, p2, ax, ay in self.w:
            ph = kx * P[:, 0] + ky * P[:, 1]
            dx += ax * np.sin(ph + p1)
            dy += ay * np.sin(ph + p2)
        return np.stack([dx, dy], 1)

    def __call__(self, P, amp):
        P = np.asarray(P, np.float32).reshape(-1, 2)
        if amp <= 0:
            return P
        return P + np.float32(amp) * self.disp(P)


# =========================================================================== 笔触生成
_U64 = np.uint64
_K1, _K2, _K3 = _U64(0x9E3779B97F4A7C15), _U64(0xBF58476D1CE4E5B9), _U64(0x94D049BB133111EB)


def _hu(salt, *keys):
    """向量化整数哈希 → 均匀分布 0..1（每条线/每段笔触自己的随机数，区域边界抖 1px 不会整片重新洗牌）。"""
    shape = np.broadcast(*[np.asarray(k) for k in keys]).shape if keys else ()
    with np.errstate(over='ignore'):
        h = np.full(shape, _U64(salt & 0xFFFFFFFFFFFF), np.uint64)
        for k in keys:
            h = (h ^ (np.asarray(k).astype(np.int64).astype(np.uint64) + _K1)) * _K2
            h ^= h >> _U64(31)
        h = (h ^ (h >> _U64(27))) * _K3
        h ^= h >> _U64(33)
    return (h >> _U64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)


def _hn(salt, *keys):
    """近似正态（4 个均匀数之和，方差归一）。"""
    return (_hu(salt, 1, *keys) + _hu(salt, 2, *keys) + _hu(salt, 3, *keys) + _hu(salt, 4, *keys) - 2.0) * 1.7320508


def _hatch(m, x0, y0, ang, sp, wd, pr, salt, seg=(40, 120), over=3.0, dens=None, step=2.5, bow=0.5, ajit=0.035,
           pjit=0.16, wjit=0.15, thr=0.43, minlen=None):
    """有方向的涂鸦排线（向量化）。m = 区域遮罩(0..1)，左上角 (x0,y0)；ang 弧度；salt 随机种子（整数）。
    排线锚定在世界坐标上，每条线、每段笔触的随机数由 (线号, 段起点, 段号) 哈希得到。
    → (P (N,4,2) 世界坐标, wd (N), pr (N), uid (N) 每笔一个稳定的 0..1 随机数)。"""
    h, w = m.shape
    ca, sa = math.cos(ang), math.sin(ang)
    cxs = np.float64([x0, x0 + w, x0, x0 + w])
    cys = np.float64([y0, y0, y0 + h, y0 + h])
    vc = -sa * cxs + ca * cys
    sc = ca * cxs + sa * cys
    phase = float(_hu(salt, 7)) * sp
    i0 = int(math.floor((vc.min() - phase) / sp)) - 1
    i1 = int(math.ceil((vc.max() - phase) / sp)) + 1
    lines = np.arange(i0, i1 + 1)
    nl = len(lines)
    v = phase + (lines + 0.5 + (_hu(salt, 11, lines) - 0.5) * 0.44) * sp
    step = max(step, 1.0)
    s0 = math.floor(sc.min() / step) * step
    ns = int((sc.max() - s0) / step) + 2
    s = s0 + np.arange(ns) * step
    X = (ca * s[None, :] - sa * v[:, None] - x0).astype(np.float32)
    Y = (sa * s[None, :] + ca * v[:, None] - y0).astype(np.float32)
    xi = np.rint(X).astype(np.int32)
    yi = np.rint(Y).astype(np.int32)
    inb = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    inside = np.zeros(inb.shape, bool)
    inside[inb] = m[yi[inb], xi[inb]] > thr
    pad = np.zeros((nl, 1), bool)
    dd = np.diff(np.concatenate([pad, inside, pad], 1).astype(np.int8), axis=1)
    li, si = np.nonzero(dd == 1)
    _, se = np.nonzero(dd == -1)
    empty = (np.zeros((0, 4, 2), np.float32), np.zeros(0, np.float32), np.zeros(0, np.float32), np.zeros(0))
    if len(li) == 0:
        return empty
    sa_ = s[si]
    sb_ = s[se - 1]
    L = sb_ - sa_
    lid = lines[li]
    rq = np.floor(sa_ / max(seg[0] * 0.5, 4.0)).astype(np.int64)      # 段起点量化：边界小抖不换随机数
    if minlen is None:
        minlen = wd * 0.6
    keep = (L >= minlen) | (_hu(salt, 13, lid, rq) < 0.3)
    li, lid, rq, sa_, L = li[keep], lid[keep], rq[keep], sa_[keep], L[keep]
    R = len(li)
    if R == 0:
        return empty
    lo, hi = seg
    segl = lo + (hi - lo) * _hu(salt, 17, lid, rq)
    k = np.maximum(1, np.rint(L / segl)).astype(np.int64)
    P = int(k.sum())
    ridx = np.repeat(np.arange(R), k)
    j = np.arange(P) - np.repeat(np.cumsum(k) - k, k)
    kk = k[ridx].astype(np.float64)
    pl, pq = lid[ridx], rq[ridx]
    plen = L[ridx] / kk
    pa = sa_[ridx] + j * plen
    u1, u2, u3 = _hu(salt, 19, pl, pq, j), _hu(salt, 23, pl, pq, j), _hu(salt, 29, pl, pq, j)
    pb = pa + plen * (1 + (u1 - 0.5) * 0.2)
    first = j == 0
    last = j == (k[ridx] - 1)
    pa = np.where(first, pa - (u2 * 1.4 - 0.4) * over, pa - (0.08 + 0.17 * u2) * plen)
    pb = np.where(last, sa_[ridx] + L[ridx] + (u3 * 1.4 - 0.4) * over, pb)
    ln = np.maximum(pb - pa, 1.0)
    pb = pa + ln
    prs = pr * (1 + pjit * _hn(salt, 31, pl, pq, j))
    wds = wd * (1 + wjit * _hn(salt, 37, pl, pq, j))
    slope = np.tan(_hn(salt, 41, pl, pq, j) * ajit)
    bw = _hn(salt, 43, pl, pq, j) * bow * ln * 0.02
    uid = _hu(salt, 47, pl, pq, j)
    t = np.float64([0.0, 0.2, 0.75, 1.0])
    ss = pa[:, None] + t[None, :] * ln[:, None]
    vk = v[li[ridx]]
    vv = vk[:, None] + slope[:, None] * (ss - ((pa + pb) / 2)[:, None]) + bw[:, None] * (1 - (2 * t - 1) ** 2)[None, :]
    px = ca * ss - sa * vv
    py = sa * ss + ca * vv
    pts = np.stack([px, py], 2).astype(np.float32)
    if dens is not None:
        sm = (pa + pb) / 2
        mx = np.clip(np.rint(ca * sm - sa * vk - x0), 0, w - 1).astype(np.int32)
        my = np.clip(np.rint(sa * sm + ca * vk - y0), 0, h - 1).astype(np.int32)
        g = dens[my, mx]
        ok = _hu(salt, 53, pl, pq, j) <= g * 1.15
        prs = prs * (0.6 + 0.4 * np.minimum(1.0, g))
        pts, wds, prs, uid = pts[ok], wds[ok], prs[ok], uid[ok]
    return pts, np.maximum(1.0, wds).astype(np.float32), np.clip(prs, 0.05, 1.25).astype(np.float32), uid


def _bbox_of(P, pad, clip=None):
    xs, ys = P[..., 0], P[..., 1]
    x0 = max(0, int(math.floor(float(xs.min()) - pad)))
    y0 = max(0, int(math.floor(float(ys.min()) - pad)))
    x1 = min(W, int(math.ceil(float(xs.max()) + pad)))
    y1 = min(H, int(math.ceil(float(ys.max()) + pad)))
    if clip is not None:
        cx0, cy0, cx1, cy1 = clip
        x0, y0, x1, y1 = max(x0, cx0), max(y0, cy0), min(x1, cx1), min(y1, cy1)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _vq(v):
    v = np.clip(v, 10, 255)
    return np.minimum(255, (v // 12) * 12 + 11).astype(np.int64)


def _draw_buckets(M, segs, par, val, th):
    key = (par.astype(np.int64) << 24) | (val.astype(np.int64) << 8) | th.astype(np.int64)
    order = np.argsort(key, kind='stable')
    ks = key[order]
    cuts = np.flatnonzero(np.diff(ks)) + 1
    for chunk in np.split(order, cuts):
        kk = int(key[chunk[0]])
        cv2.polylines(M[kk >> 24], segs[chunk], False, (kk >> 8) & 0xFFFF, kk & 0xFF, cv2.LINE_AA, 2)


def _raster_hatch(P, wd, pr, uid=None, tooth='wax', gain=1.0, streak=0.35, bbox=None):
    """排线笔触 → (纸齿后的 alpha, x0, y0)。"""
    if len(P) == 0:
        return None
    bb = _bbox_of(P, float(wd.max()) / 2 + 3, bbox)
    if bb is None:
        return None
    x0, y0, x1, y1 = bb
    h, w = y1 - y0, x1 - x0
    M = [np.zeros((h, w), np.uint8), np.zeros((h, w), np.uint8)]
    q = np.rint((P - np.float32([x0, y0])) * 4.0).astype(np.int32)
    N = len(q)
    v = pr * 255.0
    par = (np.arange(N) & 1)
    th = np.maximum(1, np.rint(wd)).astype(np.int64)
    th0 = np.maximum(1, np.rint(wd * 0.62)).astype(np.int64)
    th2 = np.maximum(1, np.rint(wd * 0.45)).astype(np.int64)
    segs = np.concatenate([q[:, 0:2], q[:, 1:3], q[:, 2:4]])
    _draw_buckets(M, segs, np.concatenate([par, par, par]),
                  np.concatenate([_vq(v * 0.85), _vq(v), _vq(v * 0.72)]), np.concatenate([th0, th, th2]))
    if streak:
        big = wd >= 4.5
        if big.any():
            qb = q[big]
            dv = (qb[:, -1] - qb[:, 0]).astype(np.float32)
            ln = np.hypot(dv[:, 0], dv[:, 1]) + 1e-6
            nx, ny = -dv[:, 1] / ln, dv[:, 0] / ln
            idx = np.flatnonzero(big)
            hsh = (idx * 2654435761) & 0xFFFF
            o1 = ((hsh & 0xFF) / 255.0 - 0.5) * wd[big] * 0.7 * 4
            sw = np.maximum(1, np.rint(wd[big] * 0.28)).astype(np.int64)
            off = np.stack([nx * o1, ny * o1], 1)[:, None, :].astype(np.int32)
            _draw_buckets(M, qb + off, 1 - par[big], _vq(v[big] * streak), sw)
    cov = M[0].astype(np.float32)
    cov += M[1]
    return _tooth(cov, x0, y0, tooth, gain / 255.0), x0, y0


def _raster_strokes(strokes, tooth='wax', gain=1.0, taper=True):
    """一般笔触列表 [(pts, wd, pr)] → (alpha, x0, y0)。用于轮廓线（点数不定）。"""
    if not strokes:
        return None
    allp = np.concatenate([s[0] for s in strokes])
    wmax = max(s[1] for s in strokes)
    bb = _bbox_of(allp, wmax / 2 + 3)
    if bb is None:
        return None
    x0, y0, x1, y1 = bb
    h, w = y1 - y0, x1 - x0
    M = [np.zeros((h, w), np.uint8), np.zeros((h, w), np.uint8)]
    buckets = {}
    off = np.float64([x0, y0])

    def put(mi, val, th, q):
        kk = (mi, int(_vq(np.float64(val))), int(th))
        buckets.setdefault(kk, []).append(q)

    for i, (pts, wd, pr) in enumerate(strokes):
        q = np.rint((np.asarray(pts, np.float64) - off) * 4.0).astype(np.int32)
        v = min(255.0, max(10.0, pr * 255.0))
        th = max(1, int(round(wd)))
        mi = i & 1
        nq = len(q)
        if taper and nq >= 4 and wd > 2.2:
            k1 = max(1, nq // 6)
            k2 = nq - 1 - max(1, nq // 4)
            if k2 <= k1:
                k2 = k1 + 1
            put(mi, v * 0.85, max(1, round(wd * 0.62)), q[:k1 + 1])
            put(mi, v, th, q[k1:k2 + 1])
            put(mi, v * 0.72, max(1, round(wd * 0.45)), q[k2:])
        else:
            put(mi, v, th, q)
    for (mi, val, th), lst in buckets.items():
        cv2.polylines(M[mi], lst, False, val, th, cv2.LINE_AA, 2)
    cov = M[0].astype(np.float32)
    cov += M[1]
    return _tooth(cov, x0, y0, tooth, gain / 255.0), x0, y0


def _contour(Q, closed, width, pressure, rs, seg=(45, 140), repass=0.55, wjit=0.2, gap=0.12, over=2.5,
             step=4.0, pjit=0.14, off2=1.2, taper=None, head=0.0, lift=0.0, breaks=0.0, fade=0.0):
    """轮廓 → 若干带收笔的笔触（手会抬起，有重叠/小缺口，部分笔再复描一遍）。"""
    Q = _resample(Q, step, closed)
    n = len(Q)
    if n < 2:
        return []
    if closed:
        st = int(rs.random() * n) % n
        Q = np.concatenate([Q[st:], Q[:st], Q[st:st + 1]])
        n = len(Q)
    nr = _normals(Q)
    out = []
    i = 0
    lo, hi = seg
    first = True
    while i < n - 1:
        ln = int(rs.uniform(lo, hi) / step)
        j = min(n - 1, i + max(2, ln))
        if n - 1 - j < lo / step * 0.4:
            j = n - 1
        pts = Q[i:j + 1].copy()
        if len(pts) >= 2:
            t0 = pts[0] - pts[1]
            t0 /= (np.hypot(*t0) + 1e-9)
            t1 = pts[-1] - pts[-2]
            t1 /= (np.hypot(*t1) + 1e-9)
            pts[0] += t0 * rs.uniform(-0.5, 1.0) * over
            pts[-1] += t1 * rs.uniform(-0.5, 1.0) * over
        u = (i + j) / 2 / max(1, n - 1)
        fac = 1.0
        if taper and not closed:
            ta, tb = taper
            fac = min(1.0, (u + 0.08) / (ta + 0.08), (1 - u + 0.08) / (tb + 0.08))
            fac = 0.5 + 0.5 * max(0.0, fac)
        pr = pressure * (1 + pjit * rs.normal()) * (1 - fade * u * 0.6)
        wd = width * (1 + wjit * rs.normal()) * fac
        if first and head:
            pr *= 1 + 0.3 * head
            wd *= 1 + 0.25 * head
        if j >= n - 1 and lift:
            pr *= 1 - 0.45 * lift
        drop = breaks > 0 and rs.random() < breaks * 0.45 and not first
        if not drop:
            out.append((pts, max(1.0, wd), pr))
            if rs.random() < repass:
                o = rs.normal(0, off2)
                a = int(rs.uniform(0, 0.3) * len(pts))
                b = len(pts) - int(rs.uniform(0, 0.3) * len(pts))
                if b - a >= 2 and i + b <= len(nr):
                    out.append((pts[a:b] + nr[i + a:i + b] * o, max(1.0, wd * 0.75), pr * 0.6))
        first = False
        if j >= n - 1:
            break
        back = int(rs.uniform(-gap * 3, 1.5) * 2)
        i = max(i + 1, j - back)
    return out


# =========================================================================== 缓存
_CACHE = {}
_CACHE_MAX = 9


def _hash_val(h, v):
    if isinstance(v, np.ndarray):
        return zlib.crc32(np.ascontiguousarray(v).view(np.uint8).ravel(), zlib.crc32(str(v.shape).encode(), h))
    if isinstance(v, dict):
        for k in sorted(v.keys(), key=str):
            h = zlib.crc32(str(k).encode(), h)
            h = _hash_val(h, v[k])
        return h
    if isinstance(v, (list, tuple)):
        for x in v:
            h = _hash_val(h, x)
        return h
    return zlib.crc32(repr(v).encode(), h)


def _ops_hash(ops):
    h = 0
    for kind, kw in ops:
        h = zlib.crc32(kind.encode(), h)
        h = _hash_val(h, kw)
    return h


# =========================================================================== 笔刷
class BrushB:
    key = 'B'

    def __init__(self):
        _init_tex()

    def paper(self):
        return np.clip(PAPER * FINISH[..., None] + DITHER[..., None], 0, 1).astype(np.float32)

    # ------------------------------------------------------------------ 主循环
    def render(self, ops, d):
        _init_tex()
        self.d = d
        self.deff = d
        self.cur = PAPER.copy()
        self.alpha = None
        self.top = ''
        self.fields = {}
        stack = []
        cache_key = None
        cache_depth = None
        seen_group = False
        i, n = 0, len(ops)
        while i < n:
            kind, kw = ops[i]
            if kind == 'group':
                depth = kw.get('depth', len(stack))
                if depth == 0:
                    self.top = str(kw.get('name'))
                if kw.get('cache') is not None and not seen_group and depth == 0:
                    j = self._match_end(ops, i)
                    ck = ('B', VERSION, _hash_val(0, kw.get('cache')), _ops_hash(ops[i:j + 1]))
                    if ck in _CACHE:
                        self.cur = _CACHE.pop(ck)
                        _CACHE[ck] = self.cur          # LRU：挪到最后
                        self.cur = self.cur.copy()
                        seen_group = True
                        i = j + 1
                        continue
                    cache_key, cache_depth = ck, len(stack)
                    self.deff = sd('cache', *_flat([kw.get('cache')], []))
                seen_group = True
                stack.append(self._push(kw))
            elif kind == 'end':
                if stack:
                    self._pop(stack.pop())
                if cache_key is not None and len(stack) == cache_depth:
                    _CACHE[cache_key] = self.cur.copy()
                    while len(_CACHE) > _CACHE_MAX:
                        _CACHE.pop(next(iter(_CACHE)))
                    cache_key = None
                    self.deff = d
            else:
                fn = getattr(self, '_op_' + kind, None)
                if fn is not None:
                    fn(kw)
            i += 1
        while stack:
            self._pop(stack.pop())
        out = self.cur * FINISH[..., None]
        out += DITHER[..., None]
        np.clip(out, 0, 1, out=out)
        return out.astype(np.float32)

    @staticmethod
    def _match_end(ops, i):
        dep = 0
        for j in range(i, len(ops)):
            k = ops[j][0]
            if k == 'group':
                dep += 1
            elif k == 'end':
                dep -= 1
                if dep == 0:
                    return j
        return len(ops) - 1

    def _push(self, kw):
        knock = kw.get('knock', True)
        op = float(kw.get('opacity', 1.0))
        if knock and op >= 0.999:
            return ('pass', kw, None, None)
        saved = (self.cur, self.alpha)
        if knock:
            self.cur = self.cur.copy()
            self.alpha = None if self.alpha is None else self.alpha.copy()
            return ('opacity', kw, saved, op)
        self.cur = np.zeros_like(self.cur)
        self.alpha = np.zeros((H, W), np.float32)
        return ('trans', kw, saved, op)

    def _pop(self, ent):
        mode, kw, saved, op = ent
        if mode == 'pass':
            return
        pcur, palpha = saved
        if mode == 'opacity':
            pcur += (self.cur - pcur) * np.float32(op)
            if palpha is not None and self.alpha is not None:
                palpha += (self.alpha - palpha) * np.float32(op)
        else:
            al = self.alpha * np.float32(op)
            ys, xs = np.nonzero(al[::8, ::8] > 0)
            if len(ys):
                y0, y1 = max(0, ys.min() * 8 - 8), min(H, ys.max() * 8 + 16)
                x0, x1 = max(0, xs.min() * 8 - 8), min(W, xs.max() * 8 + 16)
                a = al[y0:y1, x0:x1]
                sub = pcur[y0:y1, x0:x1]
                sub *= (1 - a)[..., None]
                sub += self.cur[y0:y1, x0:x1] * np.float32(op)
                if palpha is not None:
                    pa = palpha[y0:y1, x0:x1]
                    pa *= (1 - a)
                    pa += a
        self.cur, self.alpha = pcur, palpha

    # ------------------------------------------------------------------ 公用
    def _rng(self, kind, kw):
        """抖动大的层（人物，boil≥0.75）每个绘制序号整片重画；抖动小的层（背景）笔触布局固定，只做小幅抖动。"""
        boil = float(kw.get('boil', 1.0))
        self._sub = 0
        if boil >= RELAYOUT_BOIL:
            self._jit = None
            self._salt = sd(*_flat((kind, kw['seed'], self.deff), []))
            return _R(kind, kw['seed'], self.deff)
        self._jit = (_R(kind, 'j', kw['seed'], self.deff), 0.3 + 0.8 * boil)
        self._salt = sd(*_flat((kind, kw['seed']), []))
        return _R(kind, kw['seed'])

    def _hatchj(self, m, x0, y0, ang, sp, wd, pr, rs=None, **k):
        salt = sd(self._salt, self._sub)
        self._sub += 1
        P, wds, prs, uid = _hatch(m, x0, y0, ang, sp, wd, pr, salt, **k)
        if getattr(self, '_jit', None) is not None and len(P):
            rj, amp = self._jit
            P = P + rj.normal(0, amp, (len(P), 1, 2)).astype(np.float32)                 + rj.normal(0, amp * 0.35, P.shape).astype(np.float32)
        return P, wds, prs, uid

    def _field(self):
        f = self.fields.get(self.top)
        if f is None:
            f = self.fields[self.top] = _Field(('grp', self.top), self.deff)
        return f

    def _amp(self, kw, mul=1.0):
        return float(kw.get('boil', 1.0)) * BOIL_PX * mul

    def _region(self, kw, pad=2.0, extra=0.0):
        amp = self._amp(kw) + extra
        F = self._field()
        if kw.get('mask') is not None:
            m, mx, my = kw['mask']
            m = np.asarray(m, np.float32)
            dx, dy = (F.disp([(mx + m.shape[1] / 2, my + m.shape[0] / 2)])[0] * amp) if amp > 0 else (0, 0)
            r = region_mask(dict(mask=(m, int(round(mx + dx)), int(round(my + dy)))), pad)
            if r is None:
                return None
            mm = r[0]
            per = float(np.abs(np.diff(mm, axis=0)).sum() + np.abs(np.diff(mm, axis=1)).sum()) * 0.8
            return r + (per,)
        polys = kw.get('polys') or []
        if not polys:
            return None
        polys = [F(p, amp) for p in polys]
        holes = [F(p, amp) for p in (kw.get('holes') or [])]
        r = region_mask(dict(polys=polys, holes=holes), pad)
        if r is None:
            return None
        per = sum(float(np.hypot(*(np.roll(p, -1, 0) - p).T).sum()) for p in polys)
        return r + (per,)

    def _grad(self, kw, x0, y0, w, h):
        g = None
        if kw.get('grad') is not None:
            gx0, gy0, gx1, gy1, g0, g1 = kw['grad']
            dx, dy = gx1 - gx0, gy1 - gy0
            L2 = dx * dx + dy * dy + 1e-9
            xs = (np.arange(w, dtype=np.float32) + x0 - gx0) * (dx / L2)
            ys = (np.arange(h, dtype=np.float32) + y0 - gy0) * (dy / L2)
            t = np.clip(ys[:, None] + xs[None, :], 0, 1)
            g = g0 + (g1 - g0) * t
        if kw.get('rgrad') is not None:
            cx, cy, r0, r1, g0, g1 = kw['rgrad']
            xs = np.arange(w, dtype=np.float32) + x0 - cx
            ys = np.arange(h, dtype=np.float32) + y0 - cy
            dist = np.sqrt(ys[:, None] ** 2 + xs[None, :] ** 2)
            t = np.clip((dist - r0) / (r1 - r0 + 1e-6), 0, 1)
            g2 = g0 + (g1 - g0) * t
            g = g2 if g is None else g * g2
        return None if g is None else np.clip(g, 0, 1.5).astype(np.float32)

    def _paint(self, a, col, x0, y0, cvar=0.05, hue=None, op=1.0):
        if a is None:
            return
        h, w = a.shape
        if op != 1.0:
            a = a * np.float32(op)
        img = self.cur[y0:y0 + h, x0:x0 + w]
        col = np.asarray(col, np.float32)
        if cvar or hue is not None:
            nz = NOISE_A[y0:y0 + h, x0:x0 + w] * np.float32(cvar * 2)
            t = nz[..., None] * col                     # 颜色的低频浓淡（同一支笔压力不均）
            t += col
            if hue is not None:
                t += NOISE_B[y0:y0 + h, x0:x0 + w, None] * (np.asarray(hue, np.float32) * 2)
        else:
            t = np.empty((h, w, 3), np.float32)
            t[:] = col
        t -= img
        t *= a[..., None]
        img += t
        if self.alpha is not None:
            al = self.alpha[y0:y0 + h, x0:x0 + w]
            al += a * (1 - al)

    def _paint_mul(self, a, mul, x0, y0, strength=1.0, adapt=True):
        """在已有颜色上乘暗（深色叠涂）。adapt：浅色上换成玫瑰/淡紫的阴影色，深色上用砖红/梅紫。"""
        if a is None:
            return
        h, w = a.shape
        img = self.cur[y0:y0 + h, x0:x0 + w]
        mul = np.asarray(mul, np.float32)
        aa = a * np.float32(strength)
        if adapt:
            k = np.dot(img, np.float32([0.3, 0.59, 0.11]))
            k -= 0.45
            k *= 2.8
            np.clip(k, 0, 1, out=k)
            f = k[..., None] * (SHADE_MUL_LIGHT - mul)      # 乘数 m = mul + (light-mul)·k
            f += mul
        else:
            f = np.empty((h, w, 3), np.float32)
            f[:] = mul
        f -= 1                                             # f = m - 1
        f *= aa[..., None]
        f += 1                                             # f = 1 - aa·(1-m)
        img *= f

    def _clip_to(self, r, m, x0, y0, soft=1.5):
        """把笔触 alpha 限制在区域外扩 ~soft 像素以内（排线不会大片越界）。"""
        if r is None:
            return None
        a, ax, ay = r
        h, w = a.shape
        mh, mw = m.shape
        X0, Y0 = max(ax, x0), max(ay, y0)
        X1, Y1 = min(ax + w, x0 + mw), min(ay + h, y0 + mh)
        if X1 <= X0 or Y1 <= Y0:
            return None
        sub = a[Y0 - ay:Y1 - ay, X0 - ax:X1 - ax]
        mm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        if soft > 0:
            mm = np.clip(cv2.GaussianBlur(mm, (0, 0), soft) * 2.2, 0, 1)
        return sub * mm, X0, Y0

    def _sizes(self, area, per, kw, base=10.0, lo=2.2):
        thick = 2 * area / max(per, 1.0) if per else math.sqrt(area) * 0.6
        wd = float(np.clip(thick * 0.30, lo, base)) * float(kw.get('b_size', 1.0))
        return wd

    def _angle(self, seed, kw, key='b_angle', default=None, shape=None):
        if kw.get(key) is not None:
            return math.radians(float(kw[key]))
        if default is not None:
            return math.radians(default)
        r = _R('ang', seed)
        if shape is not None:
            h, w = shape
            if w > 2.0 * h:           # 扁长的（天空、墙、河、台面）：顺着长边涂
                return math.radians(22 + r.uniform(-12, 12))
            if h > 2.0 * w:           # 瘦高的（柜门、桌腿、芦苇）
                return math.radians(74 + r.uniform(-10, 10))
        return math.radians(56 + r.uniform(-18, 18))

    # ------------------------------------------------------------------ 指令
    def _op_cover(self, kw):
        r = self._region(kw, pad=3.0, extra=float(kw.get('jit', 0.0)))
        if r is None:
            return
        m, x0, y0 = r[:3]
        fe = float(kw.get('feather', 1.0))
        if fe > 0.3:
            m = cv2.GaussianBlur(m, (0, 0), fe * 0.6)
        a = m * np.float32(kw.get('amount', 1.0))
        h, w = a.shape
        img = self.cur[y0:y0 + h, x0:x0 + w]
        if self.alpha is not None:
            img *= (1 - a)[..., None]
            al = self.alpha[y0:y0 + h, x0:x0 + w]
            al *= 1 - a
        else:
            img += (PAPER[y0:y0 + h, x0:x0 + w] - img) * a[..., None]

    def _op_fill(self, kw):
        r = self._region(kw, pad=2.0)
        if r is None:
            return
        m, x0, y0 = r[:3]
        per = r[3] if len(r) > 3 else 0.0
        h, w = m.shape
        area = float(m.sum())
        if area < 2:
            return
        spec = kw['color']
        red = bool(spec.get('red'))
        col = bcolor(spec)
        seed, d = kw['seed'], self.deff
        g = self._grad(kw, x0, y0, w, h)
        dry = float(kw.get('dry', 0.0))
        streak = float(kw.get('streak', 0.0))
        wd = self._sizes(area, per, kw)
        ang = self._angle(seed, kw, shape=m.shape)
        if streak:
            ang = self._angle(seed, kw, default=78 + _R('ang', seed).uniform(-8, 8))
        layers = int(kw.get('b_layers', 3))
        rs = self._rng('fill', kw)
        thick = 2 * area / max(per, 1.0) if per else math.sqrt(area) * 0.6
        clean = kw.get('b_clean', thick < 130)       # 小块（脸、手、小物件）压得更实，不留脏点
        # 0) 蜡底：一层较实的底色（被纸齿打断，凹坑里透出纸），笔触缝里露的是它而不是纸
        base = m * np.float32((0.92 if clean else 1.0) - 0.3 * dry)
        a = _tooth(base, x0, y0, 'heavy' if clean else 'base')
        if g is not None:
            a *= np.sqrt(np.clip(g, 0, 1))     # 浓淡 = 这层蜡的透明度（平滑过渡，不是更多纸坑）
        self._paint(a, _variant(col, -0.07, 330 / 360, 0.06, 1.05, red), x0, y0, cvar=0.04)
        # 1) 主方向排线：密、全压；笔触分两组颜色（本色 / 略亮），一笔一笔看得出来
        sp = wd * 0.62
        seg = (max(10.0, wd * 5.0), max(26.0, wd * 14.0))
        stp = min(2.5, max(1.0, wd * 0.35))
        P, wds, prs, uid = self._hatchj(m, x0, y0, ang, sp, wd, 1.02 - 0.2 * dry, rs, seg=seg, over=wd * 0.4, dens=g,
                             step=stp, pjit=0.10)
        if len(P):
            grp = uid < 0.38
            c1b = _variant(col, 0.05, 46 / 360, 0.12, 1.06, red)
            for sel, cc, cv in ((~grp, col, 0.06), (grp, c1b, 0.05)):
                if sel.any():
                    rr = self._clip_to(_raster_hatch(P[sel], wds[sel], prs[sel], tooth='heavy' if clean else 'wax',
                                                     streak=0.32 + 0.3 * streak), m, x0, y0, soft=1.4)
                    if rr is not None:
                        self._paint(rr[0], cc, rr[1], rr[2], cvar=cv, hue=HUE_VEC)
        # 2) 斜向叠色：偏亮偏暖，成片出现（低频噪声控制密度）
        if layers >= 2:
            nb = NOISE_B[y0:y0 + h, x0:x0 + w]
            dens2 = np.clip(0.55 + nb * 2.4, 0.0, 1.0)
            if g is not None:
                dens2 = dens2 * g
            c2 = _light_var(col, red) if not streak else _variant(col, 0.16, 250 / 360, 0.2, 1.1, red)
            st = self._hatchj(m, x0, y0, ang + 0.55, sp * 1.35, wd * 0.85, 0.62, rs, seg=(seg[0] * 0.8, seg[1] * 0.8),
                        over=wd * 0.3, dens=dens2, step=stp)
            rr = self._clip_to(_raster_hatch(*st, tooth='wax', streak=0.2), m, x0, y0, soft=1.2)
            if rr is not None:
                self._paint(rr[0], c2, rr[1], rr[2], cvar=0.05)
        # 3) 深色/冷色碎笔（叠色），稀疏
        if layers >= 3 and wd >= 3.0:
            na = NOISE_A[y0:y0 + h, x0:x0 + w]
            dens3 = np.clip(-0.1 - na * 3.0, 0.0, 0.8)
            c3 = _dark_var(col, red) if (_R('c3', seed).random() < 0.6 or red) else _cool_var(col, red)
            st = self._hatchj(m, x0, y0, ang - 0.38, sp * 1.8, wd * 0.7, 0.5, rs, seg=(seg[0] * 0.6, seg[1] * 0.6),
                        over=wd * 0.2, dens=dens3, step=stp)
            rr = self._clip_to(_raster_hatch(*st, tooth='wax', streak=0.0), m, x0, y0, soft=1.0)
            if rr is not None:
                self._paint(rr[0], c3, rr[1], rr[2], cvar=0.04, op=0.75)

    def _op_shade(self, kw):
        r = self._region(kw, pad=2.0)
        if r is None:
            return
        m, x0, y0 = r[:3]
        per = r[3] if len(r) > 3 else 0.0
        h, w = m.shape
        area = float(m.sum())
        if area < 2:
            return
        amount = float(kw.get('amount', 0.3))
        g = self._grad(kw, x0, y0, w, h)
        wd = self._sizes(area, per, kw, base=7.0, lo=2.0)
        ang = self._angle(kw['seed'], kw, key='b_angle',
                          default=(kw.get('angle') if kw.get('angle') is not None else 35.0))
        rs = self._rng('shade', kw)
        strength = float(np.clip(amount * 1.5, 0.0, 1.0))
        dens = g if g is not None else None
        # 柔和的底（在纸齿里也压一点暗，不是平涂）
        soft = cv2.GaussianBlur(m, (0, 0), max(1.0, wd * 0.5))
        if g is not None:
            soft = soft * g
        a0 = _tooth(soft * np.float32(0.95), x0, y0, 'soft')
        st = self._hatchj(m, x0, y0, ang, wd * 0.75, wd, 0.95, rs, seg=(wd * 4, wd * 12), over=wd * 0.3, dens=dens,
                    step=min(2.5, max(1.0, wd * 0.35)))
        rr = self._clip_to(_raster_hatch(*st, tooth='wax', streak=0.25), m, x0, y0, soft=2.0)
        mode_color = kw.get('color') is not None and (kw.get('b_mode') == 'color' or kw['color'].get('red'))
        if mode_color:
            col = bcolor(kw['color'])
            self._paint(a0, col, x0, y0, op=strength * 0.5)
            if rr is not None:
                self._paint(rr[0], col, rr[1], rr[2], op=strength, cvar=0.04)
            return
        mul = SHADE_MUL
        if kw.get('color') is not None:
            c = bcolor(kw['color'])
            mul = np.clip(SHADE_MUL * 0.5 + c * 0.6, 0.2, 0.95).astype(np.float32)
        self._paint_mul(a0, mul, x0, y0, strength * 0.55)
        if rr is not None:
            self._paint_mul(rr[0], mul, rr[1], rr[2], strength)

    def _op_hatch(self, kw):
        r = self._region(kw, pad=2.0)
        if r is None:
            return
        m, x0, y0 = r[:3]
        h, w = m.shape
        sp = max(2.0, float(kw.get('spacing', 6.0)))
        tone = float(kw.get('tone', 0.3))
        g = self._grad(kw, x0, y0, w, h)
        rs = self._rng('hatch', kw)
        wd = float(np.clip(sp * 0.42, 1.6, 4.5))
        st = self._hatchj(m, x0, y0, math.radians(float(kw.get('angle', 45.0))), sp, wd, 0.55 + 0.6 * tone, rs,
                    seg=(sp * 6, sp * 20), over=sp * 0.4, dens=g, ajit=0.05, wjit=0.25)
        rr = self._clip_to(_raster_hatch(*st, tooth='wax', streak=0.0), m, x0, y0, soft=1.5)
        if rr is None:
            return
        if kw.get('color') is not None:
            self._paint(rr[0], bcolor(kw['color']), rr[1], rr[2], cvar=0.05, op=min(1.0, 0.5 + tone))
        else:
            self._paint_mul(rr[0], SHADE_MUL, rr[1], rr[2], min(1.0, 0.35 + tone))

    def _op_line(self, kw):
        role = kw.get('role', 'contour')
        P = np.asarray(kw['pts'], np.float32)
        closed = bool(kw.get('closed', False))
        sketch = role in ('sketch', 'construct')
        amp = self._amp(kw, 1.25 if sketch else 1.0)
        F = self._field()
        Q = spline(F(P, amp), 2.0, closed)
        if len(Q) < 2:
            return
        w = float(kw.get('w', 6.0)) * float(kw.get('b_width', 1.0))
        tone = float(kw.get('tone', 0.85))
        rs = self._rng('line', kw)
        dry = float(kw.get('dry', 0.0))
        taper = kw.get('taper')
        if taper is not None and not isinstance(taper, (tuple, list)):
            taper = (0.12, 0.30) if taper else None
        common = dict(taper=taper, head=float(kw.get('head', 0.0)), lift=float(kw.get('lift', 0.0)),
                      breaks=float(kw.get('breaks', 0.0)), fade=float(kw.get('fade', 0.0)))
        if sketch:
            wd = 0.48 * w + 0.9
            reps = max(1, int(kw.get('reps', 1)))
            spread = float(kw.get('spread', 1.5))
            strokes = []
            for k in range(reps):
                Qk = Q
                if k:
                    Qk = Q + rs.normal(0, spread, 2).astype(np.float32) + \
                         rs.normal(0, spread * 0.4, Q.shape).astype(np.float32)
                strokes += _contour(Qk, closed, wd * (1 - 0.15 * k), (0.55 + 0.5 * tone) * (1 - 0.2 * k), rs,
                                    seg=(30, 100), repass=0.3, gap=0.25, over=4.0, wjit=0.25, **common)
            col = CHALK if role == 'sketch' else CHALK2
            if kw.get('color') is not None and kw['color'].get('red'):
                col = bcolor(kw['color'])
            r = _raster_strokes(strokes, tooth='chalk', gain=1.05 - 0.3 * dry)
            if r is not None:
                self._paint(r[0], col, r[1], r[2], cvar=0.02)
            return
        if role == 'feature':
            wd = 0.62 * w + 1.0
            tooth = 'heavy'
            pr = 0.75 + 0.35 * tone
            seg = (24, 70)
            repass = 0.25
        else:
            wd = 0.56 * w + 1.3
            tooth = 'wax'
            pr = 0.62 + 0.42 * tone
            seg = (45, 140)
            repass = 0.55 if role == 'contour' else 0.35
        col = LINE_COL
        if kw.get('b_color') is not None:
            col = bcolor(core.resolve_color(kw['b_color']))
        elif kw.get('color') is not None:
            col = bcolor(kw['color'])
        if role == 'feature':
            strokes = _contour(Q, closed, wd, pr, rs, seg=seg, repass=repass, off2=0.45, over=1.0, wjit=0.12,
                               gap=0.05, **common)
        else:
            strokes = _contour(Q, closed, wd, pr, rs, seg=seg, repass=repass, off2=0.9 + 0.08 * wd, **common)
        r = _raster_strokes(strokes, tooth=tooth, gain=1.0 - 0.35 * dry)
        if r is not None:
            self._paint(r[0], col, r[1], r[2], cvar=0.03)

    def _op_dot(self, kw):
        F = self._field()
        amp = self._amp(kw)
        (x, y), = F([(kw['x'], kw['y'])], amp)
        rx, ry = max(0.5, float(kw['rx'])), max(0.5, float(kw['ry']))
        spec = kw['color']
        red = bool(spec.get('red'))
        col = bcolor(spec)
        tone = float(kw.get('tone', 0.9))
        rot = float(kw.get('rot', 0.0))
        rmax = max(rx, ry)
        pad = 3
        x0, y0 = int(math.floor(x - rmax - pad)), int(math.floor(y - rmax - pad))
        x1, y1 = int(math.ceil(x + rmax + pad)), int(math.ceil(y + rmax + pad))
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.ellipse(m, (int(round((x - x0) * 4)), int(round((y - y0) * 4))),
                    (max(1, int(round(rx * 4))), max(1, int(round(ry * 4)))), rot, 0, 360, 255, -1, cv2.LINE_AA, 2)
        mf = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32) / 255.0
        soft = tone < 0.35 and rmax >= 6 and not red
        if soft:
            rs = self._rng('dot', kw)
            wd = float(np.clip(rmax * 0.32, 2.0, 6.0))
            st = self._hatchj(mf, X0, Y0, math.radians(30 + _R('dang', kw['seed']).uniform(-15, 15)), wd * 0.7, wd, 0.8, rs,
                        seg=(wd * 2, wd * 5), over=wd * 0.3)
            rr = self._clip_to(_raster_hatch(*st, tooth='soft', streak=0.0), mf, X0, Y0, soft=1.5)
            if rr is not None:
                self._paint(rr[0], col, rr[1], rr[2], cvar=0.04, op=0.6 + 0.6 * tone)
            return
        if rmax >= 11:
            # 大的点（太阳、特写里的豆子）按填色画：有笔触，不是印章
            poly = core.ell(x, y, rx, ry, rot=rot, n=max(24, int(rmax * 1.2)))
            k2 = dict(kw)
            k2.update(polys=[poly], mask=None, holes=[], grad=None, rgrad=None, boil=0.0)
            self._op_fill(k2)
        else:
            gain = 1.15 if rmax >= 4 else 1.35
            a = _tooth(mf * np.float32(gain), X0, Y0, 'heavy' if rmax < 6 else 'wax')
            self._paint(a, col, X0, Y0, cvar=0.04)
        if red and rmax >= 2.5:
            # 暗边（右下）+ 奶白高光（左上）
            mm = np.zeros_like(m)
            cv2.ellipse(mm, (int(round((x - x0 - rx * 0.28) * 4)), int(round((y - y0 - ry * 0.3) * 4))),
                        (max(1, int(round(rx * 4))), max(1, int(round(ry * 4)))), rot, 0, 360, 255, -1,
                        cv2.LINE_AA, 2)
            rim = np.clip(m.astype(np.float32) - mm.astype(np.float32), 0, 255)[Y0 - y0:Y1 - y0,
                                                                                X0 - x0:X1 - x0] / 255.0
            self._paint(_tooth(rim * 1.1, X0, Y0, 'heavy'), _BPAL['bean_d'], X0, Y0, cvar=0.0, op=0.7)
            hr = max(0.7, rmax * 0.26)
            hm = np.zeros_like(m)
            cv2.ellipse(hm, (int(round((x - x0 - rx * 0.36) * 4)), int(round((y - y0 - ry * 0.4) * 4))),
                        (max(1, int(round(hr * 4))), max(1, int(round(hr * 0.8 * 4)))), rot, 0, 360, 255, -1,
                        cv2.LINE_AA, 2)
            hl = hm[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32) / 255.0
            self._paint(np.clip(hl * 1.25, 0, 1), CREAM, X0, Y0, cvar=0.0, op=0.92)

    def _op_light(self, kw):
        F = self._field()
        (cx, cy), = F([(kw['cx'], kw['cy'])], self._amp(kw) * 0.5)
        rx, ry = max(2.0, float(kw['rx'])), max(2.0, float(kw['ry']))
        amt = float(kw.get('amt', 0.5))
        col = bcolor(kw['color'])
        x0, y0 = max(0, int(cx - rx * 2.2)), max(0, int(cy - ry * 2.2))
        x1, y1 = min(W, int(cx + rx * 2.2)), min(H, int(cy + ry * 2.2))
        if x1 <= x0 or y1 <= y0:
            return
        xs = ((np.arange(x0, x1, dtype=np.float32) - cx) / rx) ** 2
        ys = ((np.arange(y0, y1, dtype=np.float32) - cy) / ry) ** 2
        g = np.exp(-(ys[:, None] + xs[None, :]) * 1.6) * np.float32(min(1.0, amt * 1.25))
        g *= 0.62 + 0.76 * GRAIN[y0:y1, x0:x1]
        img = self.cur[y0:y1, x0:x1]
        gc = g[..., None] * col[None, None, :]
        img[:] = 1 - (1 - img) * (1 - gc)
        # 光里再加一点暖：乘一个淡金色（让墙面在灯下更“烧”）
        img *= 1 + g[..., None] * np.float32([0.16, 0.06, -0.10])

    def _op_lift(self, kw):
        r = self._region(kw, pad=3.0)
        if r is None:
            return
        m, x0, y0 = r[:3]
        sft = float(kw.get('soft', 2.0))
        if sft > 0.3:
            m = cv2.GaussianBlur(m, (0, 0), sft * 0.7)
        amt = float(kw.get('amt', 1.0))
        h, w = m.shape
        if kw.get('b_mode') == 'paper':
            img = self.cur[y0:y0 + h, x0:x0 + w]
            img += (PAPER[y0:y0 + h, x0:x0 + w] - img) * (m * amt)[..., None]
            return
        rs = self._rng('lift', kw)
        area = float(m.sum())
        small = area < 500           # 眼睛高光这类小点：一笔奶白实点
        if small:
            a = _tooth(np.clip(m * 1.3, 0, 1), x0, y0, 'heavy')
            ax, ay = x0, y0
        else:
            wd = float(np.clip(math.sqrt(max(area, 1.0)) * 0.12, 2.0, 5.0))
            st = self._hatchj(m, x0, y0, self._angle(kw['seed'], kw), wd * 0.8, wd, 0.85, rs,
                              seg=(wd * 3, wd * 8), over=wd * 0.4, dens=np.clip(m * 1.4, 0, 1))
            rr = self._clip_to(_raster_hatch(*st, tooth='wax', streak=0.0), m, x0, y0, soft=1.0)
            if rr is None:
                return
            a, ax, ay = rr
        hh, ww = a.shape
        img = self.cur[ay:ay + hh, ax:ax + ww]
        if small:
            target = np.broadcast_to(CREAM[None, None, :], img.shape)
        else:
            lum = img[..., 0] * 0.3 + img[..., 1] * 0.59 + img[..., 2] * 0.11
            k = np.clip(lum * 2.2, 0, 1)[..., None]
            tint = LILAC[None, None, :] * (1 - k) + CREAM[None, None, :] * k
            target = img * 0.28 + tint * 0.72
        aa = (a * np.float32(min(1.0, amt * 0.8)))[..., None]
        img += (target - img) * aa
        if self.alpha is not None:
            al = self.alpha[ay:ay + hh, ax:ax + ww]
            al += aa[..., 0] * (1 - al)

    # ------------------------------------------------------------------ 歌词
    def paint_text(self, rgb, items, d):
        _init_tex()
        if not items:
            return rgb
        k, thr, s = TOOTH['wax']
        sh = (d % 4) * 3          # 每张换一块纸齿：蜡字的碎边轻轻“沸腾”，位置不动
        for it in items:
            m = it['mask']
            al = float(it['alpha'])
            if al <= 0.01:
                continue
            mg = 18
            gh, gw = m.shape
            x0, y0 = int(it['x']) - mg, int(it['y']) - mg
            big = np.zeros((gh + 2 * mg, gw + 2 * mg), np.float32)
            big[mg:mg + gh, mg:mg + gw] = m
            r = core.clip_box(x0, y0, big.shape[1], big.shape[0])
            if r is None:
                continue
            sx0, sy0, dx0, dy0, w, h = r
            sub = big[sy0:sy0 + h, sx0:sx0 + w]
            img = rgb[dy0:dy0 + h, dx0:dx0 + w]
            # 深色柔光衬底
            hm = cv2.dilate(sub, np.ones((5, 5), np.uint8))
            hm = cv2.GaussianBlur(hm, (0, 0), 7)
            hm = np.clip(hm * 1.7, 0, 1) * np.float32(0.62 * al)
            img += (LY_HALO[None, None, :] - img) * hm[..., None]
            # 蜡笔字（被纸齿打断）
            gy0 = min(max(dy0 + sh, 0), H - h)
            gx0 = min(max(dx0 + sh, 0), W - w)
            G = GRAIN[gy0:gy0 + h, gx0:gx0 + w]
            sung = float(it['sung'])
            pres = 1.08 + 0.14 * min(1.0, sung * 2)
            a = np.clip((sub * pres + G * k - thr) * s, 0, 1) * np.float32(al)
            if sung <= 0.0:
                col = LY_UNSUNG[None, None, :]
            elif sung >= 1.0:
                col = LY_SUNG[None, None, :]
            else:
                ys, xs = np.nonzero(sub > 0.3)
                if len(ys):
                    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
                    rmax = 0.5 * math.hypot(ys.max() - ys.min(), xs.max() - xs.min()) + 4
                else:
                    cy, cx, rmax = h / 2, w / 2, max(h, w) / 2
                yy = (np.arange(h, dtype=np.float32) - cy)[:, None]
                xx = (np.arange(w, dtype=np.float32) - cx)[None, :]
                dist = np.sqrt(yy * yy + xx * xx)
                rad = sung * rmax * 1.05
                wr = np.clip((rad - dist) / 7.0 + (G - 0.5) * 0.6, 0, 1)[..., None]
                col = LY_UNSUNG[None, None, :] * (1 - wr) + LY_SUNG[None, None, :] * wr
            img += (col - img) * a[..., None]
        # 唱到的字下面：一道粗蜡笔下划线（被纸齿打断），随演唱从左往右涂出来
        for it in items:
            u = core.underline_mask(it, width=7.0, wob=3.0, drop=0.2)
            if u is None:
                continue
            um, ux, uy = u
            r = core.clip_box(ux, uy, um.shape[1], um.shape[0])
            if r is None:
                continue
            sx0, sy0, dx0, dy0, w_, h_ = r
            sub = um[sy0:sy0 + h_, sx0:sx0 + w_]
            img = rgb[dy0:dy0 + h_, dx0:dx0 + w_]
            hm = np.clip(cv2.GaussianBlur(sub, (0, 0), 5) * 1.5, 0, 1) * 0.5
            img += (LY_HALO[None, None, :] - img) * hm[..., None]
            gy0 = min(max(dy0 + sh, 0), H - h_)
            gx0 = min(max(dx0 + sh, 0), W - w_)
            G = GRAIN[gy0:gy0 + h_, gx0:gx0 + w_]
            a = np.clip((sub * 1.15 + G * k - thr) * s, 0, 1)
            img += (LY_SUNG[None, None, :] - img) * a[..., None]
        return rgb
