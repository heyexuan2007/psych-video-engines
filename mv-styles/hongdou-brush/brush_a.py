# -*- coding: utf-8 -*-
"""
brush_a.py · A 彩铅水彩笔刷（“回忆，或者想象中本来可以有的”）

从 style_A/hd.py 移植并按新含义调淡：
  奶油色冷压水彩纸（齿纹、纤维、斑驳）；
  彩铅线：压感粗细、两头收尖、转角出头、闭合轮廓分 2–3 笔接起来、铅笔颗粒只落在纸纹凸起处；
  透明水彩：乘法叠色、颜料不均、边缘积色、颗粒沉淀、水渍、与线稿错位 2–5px、留白；
  浅色固有色只在暗侧着色，其余留纸白；暗色先铺一层浅底色再上深色；
  彩铅排线（向量化）、暖光（罩染 + 提亮）；
  画面四周自然淡出到纸白：水彩停在一条不规则的边上，边上有颜料干后积出的水痕；铅笔线比颜色更靠外，渐渐变淡。

颜色：所有非红色颜料降饱和 + 往奶油色偏一点 + 浓度降低（褪色的回忆）；皮肤、腮红、嘴唇保留温度；
     red=True 的颜色原样保持红豆红、满浓度。

渲染模型：画布是反射率（0..1），颜料/铅笔是乘法（减色）叠在纸上；cover/lift 回到本层纸色。
提示（hints，均可选）：
  通用  dry head lift fade breaks reps spread rough bloom rim soft jit streak anchor
  A 专用 a_dens 浓度倍数  a_partial 留白比例(0..1)  a_side 暗侧方向(度)  a_off 错位(px)  a_hatch 阴影里加不加排线
        a_edge（写在 group 上）0 = 这一层不做四周淡出
"""
import math
from collections import OrderedDict

import cv2
import numpy as np

import core
from core import W, H, spline, luma, LYRIC_RED

def _flat(xs):
    for x in xs:
        if isinstance(x, (tuple, list)):
            yield from _flat(x)
        else:
            yield x


def sd(*xs):
    return core.sd(*_flat(xs))


def rng(*xs):
    """种子可以是嵌套元组（('bean', k), 'wash' …）。"""
    return np.random.default_rng(sd(*xs))

cv2.setNumThreads(1)


def hexc(s):
    return core.hex2rgb(s)


# =========================================================================== 常量 / 调色
PAPER_RGB = hexc('#F6EEDF')          # 奶油色水彩纸（比旧示意略亮）
INK = hexc('#553729')                # 人物彩铅：暖深褐
INK_BG = hexc('#8C6047')             # 背景彩铅：浅赭褐
GRAPHITE = hexc('#5C5F66')           # 石墨铅笔（草稿）
SHADOW = hexc('#A48E9A')             # 淡紫灰阴影罩染（回忆里阴影也不重）
CREAM = hexc('#F8F1E3')
GLOW = hexc('#FFE7B8')
TEXT_INK = hexc('#3F2A21')           # 歌词未唱：暖深褐
TEXT_RED_D = hexc('#7E1A24')

WARM_NAMES = {'skin', 'skin_sh', 'blush', 'lips', 'lamp', 'win_warm', 'sun', 'dusk', 'terra'}
GLAZE_NAMES = {'glass', 'tear', 'water', 'water_d'}      # 本来就是透明罩在别的东西上的
FADE = 0.80                          # 整体颜料浓度（回忆褪色）
DESAT = 0.20                         # 非暖色降饱和（按饱和度比例）
DESAT_WARM = 0.05
CREAM_TINT = 0.07                    # 往奶油色偏

LINE_BOIL = 0.42                     # 线条抖动系数（×group boil）
WASH_BOIL = 0.45

# 线宽换算（w = 毛笔笔肚宽）
ROLE = {
    #            a      b      alpha0  alpha1  grain  press
    'contour': (0.70, 0.255, 0.30, 0.62, 0.55, 0.30),
    'detail':  (0.55, 0.230, 0.25, 0.55, 0.55, 0.30),
    'feature': (0.55, 0.400, 0.35, 0.60, 0.40, 0.25),
    'sketch':  (0.45, 0.300, 0.20, 0.55, 0.62, 0.45),
    'construct': (0.40, 0.230, 0.14, 0.40, 0.65, 0.45),
}


# =========================================================================== 噪声 / 纸
def _fbm(h, w, seed, cells, weights):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    for c, wt in zip(cells, weights):
        gh, gw = int(math.ceil(h / c)) + 3, int(math.ceil(w / c)) + 3
        g = r.random((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (gw * c, gh * c), interpolation=cv2.INTER_CUBIC)
        oy, ox = int(r.integers(0, c)), int(r.integers(0, c))
        out += wt * up[oy:oy + h, ox:ox + w]
    out -= out.min()
    out /= max(float(out.max()), 1e-6)
    return out


def _make_paper():
    r = np.random.default_rng(7)
    tooth = _fbm(H, W, 11, [10, 6, 3], [0.45, 0.35, 0.20])
    fine = cv2.GaussianBlur(r.random((H, W)).astype(np.float32), (0, 0), 0.7)
    fine = (fine - fine.mean()) / (fine.std() + 1e-6)
    fl = np.zeros((H, W), np.uint8)
    fd = np.zeros((H, W), np.uint8)
    for _ in range(3200):
        x, y = r.uniform(0, W), r.uniform(0, H)
        L = r.uniform(6, 46)
        a = r.uniform(0, 2 * math.pi)
        cu = r.normal(0, 0.06)
        n = int(L / 2) + 2
        aa = a + cu * np.arange(n)
        xs = x + np.concatenate([[0], np.cumsum(2 * np.cos(aa[:-1]))])
        ys = y + np.concatenate([[0], np.cumsum(2 * np.sin(aa[:-1]))])
        tgt = fl if r.random() < 0.6 else fd
        cv2.polylines(tgt, [np.int32(np.stack([xs, ys], 1) * 4)], False, int(r.uniform(90, 255)), 1,
                      cv2.LINE_AA, shift=2)
    fib = (fl.astype(np.float32) - fd.astype(np.float32)) / 255.0
    fib = cv2.GaussianBlur(fib, (0, 0), 0.6)
    height = np.clip(0.5 + (tooth - 0.5) * 1.15 + fine * 0.07 + fib * 0.10, 0, 1).astype(np.float32)
    sh = np.roll(np.roll(height, 1, 0), 1, 1)
    emb = height - sh
    mott = _fbm(H, W, 31, [320, 160, 80], [0.5, 0.3, 0.2]) - 0.5
    mott2 = _fbm(H, W, 32, [260, 120], [0.6, 0.4]) - 0.5
    shade = 1.0 + 0.10 * emb + 0.009 * fine + 0.03 * fib + 0.026 * mott
    paper = np.empty((H, W, 3), np.float32)
    paper[..., 0] = PAPER_RGB[0] * shade * (1 + 0.010 * mott2)
    paper[..., 1] = PAPER_RGB[1] * shade
    paper[..., 2] = PAPER_RGB[2] * shade * (1 - 0.018 * mott2)
    return np.clip(paper, 0, 1), height


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _make_edges():
    """回忆的边：水彩停在一条不规则的边上（多数地方是干后的硬边 + 水痕，少数地方是渐淡的干笔），
    铅笔线比颜色更靠外。→ (VW 颜料浓度系数(含水痕), VL 铅笔系数)。"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.minimum(xx, W - 1 - xx)
    dy = np.minimum(yy, H - 1 - yy)
    k = 60.0
    dist = -k * np.log(np.exp(-dx / k) + np.exp(-dy / k) + 1e-12)       # 圆角
    n1 = _fbm(H, W, 41, [300, 150, 75], [0.55, 0.3, 0.15]) - 0.5
    n2 = _fbm(H, W, 42, [26, 13, 6], [0.5, 0.3, 0.2]) - 0.5
    n3 = _fbm(H, W, 43, [420, 210], [0.6, 0.4])
    dd = dist + n1 * 120.0 + n2 * 16.0
    m0 = 46.0
    feather = _smooth(0.55, 0.78, n3)                     # 1 = 渐淡的干笔边，0 = 干后硬边
    tw = 3.0 + 45.0 * feather
    VW = _smooth(m0 - tw, m0 + tw, dd)
    inner = 0.80 + 0.20 * _smooth(m0, m0 + 220.0, dd)      # 靠边的颜色更淡一点
    rim = np.exp(-((dd - m0 - 4.0) / 4.0) ** 2) * (1 - feather)
    VWE = VW * inner + 0.45 * rim * _smooth(m0 - 2, m0 + 2, dd)
    VL = 0.15 + 0.85 * _smooth(m0 * 0.15, m0 * 0.15 + 110.0, dd + n2 * 20)
    VL *= _smooth(2.0, 14.0, dist)
    return VWE.astype(np.float32), VL.astype(np.float32)


PAPER, HEIGHT = _make_paper()
PAPER_MEAN = PAPER.reshape(-1, 3).mean(0)
NLO = _fbm(1600, 2560, 21, [150, 75, 36], [0.5, 0.32, 0.18])
NMID = _fbm(1600, 2560, 22, [30, 15, 7], [0.5, 0.32, 0.18])
PGRAIN = np.clip(1.75 * HEIGHT - 0.22, 0, 1).astype(np.float32)     # 铅笔只碰到纸纹凸起
WGRAN = ((0.5 - HEIGHT) * 2.0).astype(np.float32)                    # 颜料沉在凹处
_sr = np.random.default_rng(77)
STREAK = cv2.GaussianBlur(_sr.random((1600, 2560)).astype(np.float32), (0, 0), sigmaX=1.6, sigmaY=14.0)
STREAK = (STREAK - STREAK.mean()) / (STREAK.std() + 1e-6)
VWE, VL = _make_edges()


def sample_tex(tex, key, x0, y0, w, h, anchor=(0.0, 0.0)):
    """从大噪声纹理里取一块，key 决定偏移；anchor 让纹理跟着物体走。"""
    r = rng('tex', key)
    th, tw = tex.shape
    oy = int(r.integers(0, th - H)) - int(anchor[1])
    ox = int(r.integers(0, tw - W)) - int(anchor[0])
    ya, xa = y0 + oy, x0 + ox
    if 0 <= ya and ya + h <= th and 0 <= xa and xa + w <= tw:
        return tex[ya:ya + h, xa:xa + w]
    ys = (np.arange(ya, ya + h)) % th
    xs = (np.arange(xa, xa + w)) % tw
    return tex[ys[:, None], xs[None, :]]


# =========================================================================== 颜色
def pigment(col):
    """固有色 → 本笔刷的颜料色（褪色的回忆）。"""
    rgb = np.asarray(col['rgb'], np.float32)
    if col.get('red'):
        return rgb.copy()
    name = col.get('name')
    mx, mn = float(rgb.max()), float(rgb.min())
    sat = (mx - mn) / (mx + 1e-6)
    ds = (DESAT_WARM if name in WARM_NAMES else DESAT) * min(1.0, sat / 0.35)   # 只褪掉“艳”的那部分
    l = luma(rgb)
    rgb = rgb + (l - rgb) * ds
    rgb = rgb * (1 - CREAM_TINT) + CREAM * CREAM_TINT
    return np.clip(rgb, 0, 1).astype(np.float32)


def trans_of(rgb):
    """颜料色 → 透射率（在纸上以浓度 1 画出来正好是这个颜色）。"""
    return np.clip(np.asarray(rgb, np.float32) / PAPER_RGB, 0.0, 1.0).astype(np.float32)


def pencil_color(col, default=INK):
    if col is None:
        return default
    rgb = np.asarray(col['rgb'], np.float32)
    if col.get('red'):
        return rgb * 0.92
    p = pigment(col)
    # 彩铅比水彩深一些
    return np.clip(p * 0.78, 0, 1)


# =========================================================================== 基础几何
def noise1d(u, knots, r, periodic=False):
    k = r.uniform(-1, 1, knots)
    if periodic:
        k[-1] = k[0]
    xs = np.linspace(0, 1, knots)
    v = np.interp(u, xs, k)
    if len(v) > 5:
        ksz = max(3, (len(v) // max(knots * 2, 1)) | 1)
        if ksz > 3:
            pad = ksz // 2
            vv = np.pad(v, pad, mode='wrap' if periodic else 'edge')
            v = np.convolve(vv, np.ones(ksz) / ksz, mode='valid')
    return v


def arclen(D):
    seg = np.hypot(*np.diff(D, axis=0).T)
    return np.concatenate([[0.0], np.cumsum(seg)])


def normals(D, closed=False):
    if closed:
        tg = np.roll(D, -1, 0) - np.roll(D, 1, 0)
    else:
        tg = np.gradient(D, axis=0)
    n = np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-9
    tg = tg / n
    return np.stack([-tg[:, 1], tg[:, 0]], 1), tg


def wobble_poly(P, seed, amp, spacing=10.0):
    """闭合多边形的边缘轻微起伏（水彩边不是几何线）。"""
    D = core.densify(P, spacing, closed=True).astype(np.float64)
    if amp <= 0 or len(D) < 4:
        return D
    s = arclen(np.vstack([D, D[:1]]))[:-1]
    L = s[-1] + np.hypot(*(D[0] - D[-1])) + 1e-6
    nz = noise1d(s / L, max(5, int(L / 30)), rng(seed, 'wob'), periodic=True)
    nrm, _ = normals(D, True)
    return D + nrm * (amp * nz)[:, None]


def _clip_bbox(x0, y0, x1, y1):
    x0, y0 = max(int(math.floor(x0)), 0), max(int(math.floor(y0)), 0)
    x1, y1 = min(int(math.ceil(x1)), W), min(int(math.ceil(y1)), H)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def rasterize(kw, off=(0.0, 0.0), wob=0.0, seed=0, pad=6, soft=0.0, holes=True):
    """op 的区域（polys 或 mask，可带 holes）→ (float 遮罩, x0, y0)，已错位 off、边缘起伏 wob、柔化 soft，裁到画面内。"""
    ox, oy = float(off[0]), float(off[1])
    if kw.get('mask') is not None:
        m, mx, my = kw['mask']
        m = np.asarray(m, np.float32)
        if m.max() > 1.5:
            m = m / 255.0
        p = int(pad)
        m = np.pad(m, p)
        X0, Y0 = int(round(mx + ox)) - p, int(round(my + oy)) - p
        if wob > 0:
            mb = cv2.GaussianBlur(m, (0, 0), 1.2)
            nz = sample_tex(NMID, (seed, 'mw'), 0, 0, m.shape[1], m.shape[0]) - 0.5
            m = np.clip((mb - 0.5 + nz * 0.5 * min(wob, 2.0)) / 0.3 + 0.5, 0, 1).astype(np.float32)
        h, w = m.shape
        bb = _clip_bbox(X0, Y0, X0 + w, Y0 + h)
        if bb is None:
            return None
        x0, y0, x1, y1 = bb
        m = m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        if soft > 0:
            m = cv2.GaussianBlur(m, (0, 0), soft)
    else:
        polys = kw.get('polys') or []
        if not polys:
            return None
        Ps = []
        for i, P in enumerate(polys):
            Q = wobble_poly(P, (seed, i), wob) if wob > 0 else np.asarray(P, np.float64)
            Ps.append(Q + (ox, oy))
        allp = np.vstack(Ps)
        bb = _clip_bbox(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad,
                        allp[:, 1].max() + pad)
        if bb is None:
            return None
        x0, y0, x1, y1 = bb
        mm = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for Q in Ps:
            cv2.fillPoly(mm, [np.int32(np.round((Q - (x0, y0)) * 8))], 255, cv2.LINE_AA, shift=3)
        if holes:
            for i, Hp in enumerate(kw.get('holes') or []):
                Q = wobble_poly(Hp, (seed, 'h', i), wob * 0.7) if wob > 0 else np.asarray(Hp, np.float64)
                Q = Q + (ox, oy)
                cv2.fillPoly(mm, [np.int32(np.round((Q - (x0, y0)) * 8))], 0, cv2.LINE_AA, shift=3)
        m = mm.astype(np.float32) * (1 / 255.0)
        if soft > 0:
            m = cv2.GaussianBlur(m, (0, 0), soft)
    if not m.any():
        return None
    return m, x0, y0


def region_size(kw):
    if kw.get('mask') is not None:
        m = kw['mask'][0]
        return float(m.shape[1]), float(m.shape[0])
    polys = kw.get('polys') or []
    if not polys:
        return 0.0, 0.0
    a = np.vstack(polys)
    return float(np.ptp(a[:, 0])), float(np.ptp(a[:, 1]))


def region_center(kw):
    if kw.get('mask') is not None:
        m, mx, my = kw['mask']
        return mx + m.shape[1] / 2, my + m.shape[0] / 2
    a = np.vstack(kw['polys'])
    return float(a[:, 0].mean()), float(a[:, 1].mean())


def grad_factor(x0, y0, h, w, grad=None, rgrad=None):
    f = None
    if grad is not None:
        gx0, gy0, gx1, gy1, g0, g1 = grad
        vx, vy = gx1 - gx0, gy1 - gy0
        xs = np.arange(x0, x0 + w, dtype=np.float32)[None, :]
        ys = np.arange(y0, y0 + h, dtype=np.float32)[:, None]
        tt = np.clip(((xs - gx0) * vx + (ys - gy0) * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
        tt = tt * tt * (3 - 2 * tt)
        f = g0 + (g1 - g0) * tt
    if rgrad is not None:
        cx, cy, r0, r1, g0, g1 = rgrad
        xs = np.arange(x0, x0 + w, dtype=np.float32)[None, :]
        ys = np.arange(y0, y0 + h, dtype=np.float32)[:, None]
        tt = np.clip((np.hypot(xs - cx, ys - cy) - r0) / max(r1 - r0, 1e-6), 0, 1)
        tt = tt * tt * (3 - 2 * tt)
        f2 = g0 + (g1 - g0) * tt
        f = f2 if f is None else f * f2
    return f


# =========================================================================== 上色
def deposit(cv, den, x0, y0, trans, edge_mask=None):
    """乘法（减色）叠一层颜料/铅笔：reg *= 1 - den·(1 - trans)。edge_mask: 'W' 颜料四周淡出、'L' 铅笔四周淡出。"""
    h, w = den.shape
    if h == 0 or w == 0:
        return
    if edge_mask is not None:
        den = den * edge_mask[y0:y0 + h, x0:x0 + w]
    reg = cv[y0:y0 + h, x0:x0 + w]
    k = 1.0 - den[..., None] * (1.0 - trans)
    np.maximum(k, 0.03, out=k)
    reg *= k


def deposit_norm(cv, a, x0, y0, color, edge_mask=None):
    h, w = a.shape
    if h == 0 or w == 0:
        return
    if edge_mask is not None:
        a = a * edge_mask[y0:y0 + h, x0:x0 + w]
    reg = cv[y0:y0 + h, x0:x0 + w]
    reg += a[..., None] * (np.asarray(color, np.float32) - reg)


def wash_core(cv, mf, x0, y0, trans, seed, dens, edge=0.55, edge_sigma=2.4, gran=0.22, var=0.3, bloom=0,
              partial=0.0, side=None, grad=None, rgrad=None, streak=0.0, anchor=(0.0, 0.0), vig=True):
    """一层透明水彩（mf 是已错位/起伏/柔化的区域遮罩）。"""
    h, w = mf.shape
    r = rng(seed, 'wash')
    paint = mf
    if partial > 0:
        # 浅色：只在暗侧着色，亮侧留纸（淡淡一层底色）；颜料停下的地方是硬边
        ang = math.radians(side if side is not None else 62.0)
        sx, sy = math.cos(ang), math.sin(ang)
        xs = (np.arange(w, dtype=np.float32) - w / 2)[None, :]
        ys = (np.arange(h, dtype=np.float32) - h / 2)[:, None]
        ext = max(abs(sx) * w + abs(sy) * h, 1.0) * 0.5
        ramp = (xs * sx + ys * sy) / ext                          # -1 亮侧 … 1 暗侧
        nl = sample_tex(NLO, (seed, 'pc'), x0, y0, w, h, anchor)
        field = 0.5 + 0.42 * ramp + 0.85 * (nl - 0.5)
        thr = 0.18 + 0.62 * partial
        cov = _smooth(thr - 0.035, thr + 0.035, field)
        floor = 0.30 * (1 - partial) + 0.10
        big = (w * h) / float(W * H)
        if big > 0.15:
            floor = floor + (0.55 - floor) * min(1.0, (big - 0.15) / 0.25)     # 整面墙：起伏更柔和
            edge = edge * 0.6
        paint = mf * (floor + (1 - floor) * cov)
    den = paint
    if var > 0:
        nl = sample_tex(NLO, (seed, 'lo'), x0, y0, w, h, anchor)
        nm = sample_tex(NMID, (seed, 'mid'), x0, y0, w, h, anchor)
        fa = r.uniform(0, 2 * math.pi)
        yy = (np.arange(h, dtype=np.float32) - h / 2)[:, None] / max(h, 1)
        xx = (np.arange(w, dtype=np.float32) - w / 2)[None, :] / max(w, 1)
        den = paint * (1 - var * 0.55 + var * 1.1 * nl + var * 0.22 * (nm - 0.5)) * \
            (1 + var * 0.6 * (xx * math.cos(fa) + yy * math.sin(fa)))
    if streak > 0:
        st = sample_tex(STREAK, (seed, 'st'), x0, y0, w, h, anchor)
        den = den * np.clip(1 - streak * 0.22 * st, 0.35, 1.3)
    if edge > 0:
        inner = cv2.GaussianBlur(paint, (0, 0), edge_sigma)
        den = den + edge * 2.0 * np.clip(paint - inner, 0, 1)
    if bloom:
        if True:
            for b in range(int(bloom)):
                # 位置按区域比例取（不随每帧遮罩像素数变化而跳动）
                bx, by = r.uniform(0.12, 0.88) * w, r.uniform(0.12, 0.88) * h
                br = r.uniform(10, 28) * min(1.0, 0.25 + max(w, h) / 300)
                if mf[min(h - 1, int(by)), min(w - 1, int(bx))] < 0.5:
                    continue
                n = 11
                a = np.linspace(0, 2 * math.pi, n, endpoint=False)
                rr = 1 + 0.22 * r.normal(0, 1, n)
                bp = np.stack([bx + br * rr * np.cos(a), by + br * r.uniform(0.7, 1.1) * rr * np.sin(a)], 1)
                bp = spline(bp, 2.0, closed=True)
                bm = np.zeros((h, w), np.uint8)
                cv2.fillPoly(bm, [np.int32(np.round(bp * 8))], 255, cv2.LINE_AA, shift=3)
                bmf = cv2.GaussianBlur(bm.astype(np.float32) / 255.0, (0, 0), 1.2)
                rim = np.clip(bmf - cv2.GaussianBlur(bmf, (0, 0), 2.5), 0, 1)
                den = den * (1 - 0.42 * bmf) + 0.9 * rim * paint
    if gran > 0:
        den = den * (1 + gran * WGRAN[y0:y0 + h, x0:x0 + w])
    f = grad_factor(x0, y0, h, w, grad, rgrad)
    if f is not None:
        den = den * f
    den = np.clip(den * dens, 0, 1.6)
    deposit(cv, den, x0, y0, trans, VWE if vig else None)


# =========================================================================== 彩铅线
def stroke_geom(P, w, seed, dd, boil, taper=(0.18, 0.25), tmin=0.06, over=1.5, press=0.3, closed=False,
                gaps=0.0, head=0.0, lift=0.0):
    P = np.asarray(P, np.float64).reshape(-1, 2).copy()
    if len(P) < 2:
        return None
    rs = rng(seed, 'st')
    if boil > 0:
        rd = rng(seed, dd, 'bo')
        P += rd.normal(0, boil * 0.45, 2)[None, :] + rd.normal(0, boil * 0.42, P.shape)
    if over and not closed:
        t0 = P[0] - P[1]
        t0 /= (np.hypot(*t0) + 1e-9)
        t1 = P[-1] - P[-2]
        t1 /= (np.hypot(*t1) + 1e-9)
        P[0] += t0 * over * rs.uniform(0.3, 1.3)
        P[-1] += t1 * over * rs.uniform(0.3, 1.3)
    D = spline(P, 2.0, closed).astype(np.float64)
    if len(D) < 2:
        return None
    s = arclen(D)
    L = s[-1]
    if L < 0.5:
        return None
    u = s / L
    if closed:
        prof = np.ones_like(u)
    else:
        ta, tb = taper
        tb = tb * (1 + 1.5 * lift)
        prof = _smooth(0, max(ta, 1e-3), u) * _smooth(0, max(tb, 1e-3), 1 - u)
        prof = tmin + (1 - tmin) * prof
        if head > 0:
            prof = prof * (1 + 0.45 * head * np.exp(-((u - 0.04) / 0.05) ** 2))
    pr = 1.0 + press * noise1d(u, max(3, int(L / 50) + 3), rs, periodic=closed)
    width = w * prof * pr
    if gaps > 0:
        gn = (noise1d(u, max(4, int(L / 16) + 4), rng(seed, 'gap')) + 1) * 0.5
        width = width * np.clip((gn - gaps) / 0.10, 0, 1)
    nrm, _ = normals(D, closed)
    Lp = D + nrm * (width[:, None] * 0.5)
    Rp = D - nrm * (width[:, None] * 0.5)
    return D, Lp, Rp, u


def fill_ribbon(mask, Lp, Rp, x0, y0, vals=None):
    """把带宽度的笔画（左右边线）填进 mask。分段填、段与段取最大值（避免抗锯齿接缝）。"""
    n = len(Lp)
    if n < 2:
        return
    CH = 48
    H_, W_ = mask.shape
    i = 0
    while i < n - 1:
        j = min(n, i + CH + 1)
        poly = np.vstack([Lp[i:j], Rp[i:j][::-1]]) - (x0, y0)
        v = 255 if vals is None else int(vals[min(n - 1, (i + j) // 2)])
        if v > 0:
            if i == 0 and j == n:
                cv2.fillPoly(mask, [np.int32(np.round(poly * 4))], v, cv2.LINE_AA, shift=2)
            else:
                bx0 = max(int(poly[:, 0].min()) - 2, 0)
                by0 = max(int(poly[:, 1].min()) - 2, 0)
                bx1 = min(int(poly[:, 0].max()) + 3, W_)
                by1 = min(int(poly[:, 1].max()) + 3, H_)
                if bx1 > bx0 and by1 > by0:
                    tmp = np.zeros((by1 - by0, bx1 - bx0), np.uint8)
                    cv2.fillPoly(tmp, [np.int32(np.round((poly - (bx0, by0)) * 4))], v, cv2.LINE_AA, shift=2)
                    np.maximum(mask[by0:by1, bx0:bx1], tmp, out=mask[by0:by1, bx0:bx1])
        i = j - 1


def pencil(cv, P, w, color, alpha, seed, dd, boil, taper=(0.18, 0.25), tmin=0.06, over=1.5, press=0.3,
           grain=0.55, closed=False, gaps=0.0, head=0.0, lift=0.0, fade=0.0, mode='mul', vig=True):
    g = stroke_geom(P, w, seed, dd, boil, taper, tmin, over, press, closed, gaps, head, lift)
    if g is None:
        return
    D, Lp, Rp, u = g
    allp = np.vstack([Lp, Rp])
    bb = _clip_bbox(allp[:, 0].min() - 3, allp[:, 1].min() - 3, allp[:, 0].max() + 3, allp[:, 1].max() + 3)
    if bb is None:
        return
    x0, y0, x1, y1 = bb
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    vals = None
    if fade > 0:
        vals = np.clip(255 * (1 - fade * u), 20, 255)
    fill_ribbon(m, Lp, Rp, x0, y0, vals)
    mf = m.astype(np.float32) * (1 / 255.0)
    if grain > 0:
        mf = mf * ((1 - grain) + grain * PGRAIN[y0:y1, x0:x1])
    if mode == 'mul':
        deposit(cv, mf * alpha, x0, y0, color, VL if vig else None)
    else:
        deposit_norm(cv, mf * alpha, x0, y0, color, VL if vig else None)


# =========================================================================== 排线（向量化）
def hatch_mask(pm, x0, y0, angle_deg, spacing, lw, seed, dd, boil, shorten=0.18, jitter=0.25):
    """在区域遮罩 pm 内生成一组手画平行排线 → 覆盖率遮罩（同尺寸）。"""
    h, w = pm.shape
    if h < 2 or w < 2:
        return None
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    spacing = max(spacing, 1.6)
    rs = rng(seed, 'ha')
    xs = np.arange(w, dtype=np.float32)[None, :] + x0
    ys = np.arange(h, dtype=np.float32)[:, None] + y0
    v = xs * nx + ys * ny
    s = xs * ux + ys * uy
    v0 = float(v.min()) - spacing * rs.uniform(0, 1)
    kf = (v - v0) / spacing
    K = int(math.ceil(float(kf.max()))) + 2
    k = np.floor(kf).astype(np.int32)
    inside = pm > 0.25
    if not inside.any():
        return None
    # 每根线在区域内的起止
    kk = k[inside]
    ss = s[inside]
    smin = np.full(K + 1, np.inf, np.float32)
    smax = np.full(K + 1, -np.inf, np.float32)
    np.minimum.at(smin, kk, ss)
    np.maximum.at(smax, kk, ss)
    rd = rng(seed, dd, 'hab')
    off = rs.uniform(-jitter, jitter, K + 2) * spacing + rd.normal(0, boil * 0.5, K + 2)
    wid = lw * rs.uniform(0.75, 1.2, K + 2)
    val = rs.uniform(0.6, 1.0, K + 2)
    bow = rs.normal(0, 0.7, K + 2)
    sh0 = rs.uniform(0, shorten, K + 2)
    sh1 = rs.uniform(0, shorten, K + 2)
    sb, vb = s, v
    out = np.zeros((h, w), np.float32)
    for dk in (-1, 0, 1):
        kn = np.clip(k + dk, 0, K)
        a0 = smin[kn]
        a1 = smax[kn]
        L = a1 - a0
        valid = np.isfinite(L) & (L > 3)
        L = np.where(valid, L, 1.0)
        a0 = np.where(valid, a0, 0.0)
        s0 = a0 + L * sh0[kn]
        s1 = a0 + L * (1 - sh1[kn])
        Ls = np.maximum(s1 - s0, 1e-3)
        t = (sb - s0) / Ls
        cen = v0 + (kn + 0.5) * spacing + off[kn] + bow[kn] * np.sin(np.pi * np.clip(t, 0, 1))
        prof = _smooth(0.0, 0.25, t) * _smooth(0.0, 0.3, 1 - t)
        prof = np.where((t > 0) & (t < 1) & valid, 0.05 + 0.95 * prof, 0.0)
        hw = 0.5 * wid[kn] * prof
        cov = np.clip(hw - np.abs(vb - cen) + 0.5, 0, 1) * val[kn]
        np.maximum(out, cov, out=out)
    return out * np.clip(pm * 1.3, 0, 1)


# =========================================================================== 笔刷
_CACHE = OrderedDict()
_CACHE_MAX = 8


class BrushA:
    key = 'A'

    def paper(self):
        return PAPER.copy()

    # ------------------------------------------------------------------ 渲染
    def render(self, ops, d):
        cur = PAPER.copy()
        stack = []          # (parent 或 None, gkw, base, dd 之前的值, vig)
        self._dd = d
        self._vig = True
        self._ink = INK
        base = PAPER
        i = 0
        n = len(ops)
        cache_key = None
        while i < n:
            kind, kw = ops[i]
            if kind == 'group':
                ck = kw.get('cache')
                if ck is not None and i == 0:
                    cache_key = ('A',) + tuple(ck if isinstance(ck, (tuple, list)) else (ck,))
                    if cache_key in _CACHE:
                        _CACHE.move_to_end(cache_key)
                        cur = _CACHE[cache_key].copy()
                        # 跳到配对的 end
                        depth = 0
                        while i < n:
                            k2 = ops[i][0]
                            if k2 == 'group':
                                depth += 1
                            elif k2 == 'end':
                                depth -= 1
                                if depth == 0:
                                    break
                            i += 1
                        i += 1
                        cache_key = None
                        continue
                prev_dd, prev_vig, prev_ink = self._dd, self._vig, self._ink
                if ck is not None and i == 0:
                    # 缓存层的抖动由变体决定，与先渲染哪一格无关；背景线用浅一点的赭褐
                    self._dd = sd('cache', repr(ck)) & 0xFFFF
                    self._ink = INK_BG
                if kw.get('a_ink') is not None:
                    self._ink = INK_BG if kw.get('a_ink') == 'bg' else (INK if kw.get('a_ink') == 'fg' else
                                                                          np.asarray(kw.get('a_ink'), np.float32))
                if kw.get('a_edge') is not None:
                    self._vig = bool(kw.get('a_edge'))
                knock = kw.get('knock', True)
                op_ = float(kw.get('opacity', 1.0))
                if not knock:
                    stack.append((cur, kw, base, prev_dd, prev_vig, prev_ink))
                    cur = PAPER.copy()
                    base = PAPER
                elif op_ < 0.999:
                    stack.append((cur, kw, base, prev_dd, prev_vig, prev_ink))
                    cur = cur.copy()
                else:
                    stack.append((None, kw, base, prev_dd, prev_vig, prev_ink))
                i += 1
                continue
            if kind == 'end':
                if not stack:
                    i += 1
                    continue
                parent, gkw, pbase, prev_dd, prev_vig, prev_ink = stack.pop()
                op_ = float(gkw.get('opacity', 1.0))
                if not gkw.get('knock', True):
                    # 透明叠加：只加深
                    tr = np.clip(cur / PAPER, 0, 1)
                    parent *= 1 - op_ * (1 - tr)
                    cur = parent
                elif parent is not None:
                    parent += (cur - parent) * op_
                    cur = parent
                base = pbase
                self._dd, self._vig, self._ink = prev_dd, prev_vig, prev_ink
                if cache_key is not None and not stack:
                    _CACHE[cache_key] = cur.copy()
                    while len(_CACHE) > _CACHE_MAX:
                        _CACHE.popitem(last=False)
                    cache_key = None
                i += 1
                continue
            fn = getattr(self, '_op_' + kind, None)
            if fn is not None:
                fn(cur, kw, base)
            i += 1
        while stack:        # 容错：没有配对的 group
            parent, gkw, pbase = stack.pop()[:3]
            if parent is not None:
                parent += (cur - parent) * float(gkw.get('opacity', 1.0))
                cur = parent
        return np.clip(cur, 0, 1).astype(np.float32)

    # ------------------------------------------------------------------ 指令
    def _boil(self, kw, k):
        return float(kw.get('boil', 1.0)) * k

    def _op_cover(self, cv, kw, base):
        jit = float(kw.get('jit', 0.0))
        soft = 0.6 * float(kw.get('feather', 1.0))
        r = rasterize(kw, (0, 0), wob=jit * 1.5, seed=kw['seed'], pad=4 + int(soft * 3), soft=soft)
        if r is None:
            return
        m, x0, y0 = r
        a = (m * float(kw.get('amount', 1.0)))[..., None]
        h, w = m.shape
        reg = cv[y0:y0 + h, x0:x0 + w]
        reg += a * (base[y0:y0 + h, x0:x0 + w] - reg)

    def _restore(self, cv, kw, base, amt, soft=0.7, seed=0, wob=0.0):
        r = rasterize(kw, (0, 0), wob=wob, seed=seed, pad=4 + int(soft * 3), soft=soft)
        if r is None:
            return
        m, x0, y0 = r
        h, w = m.shape
        reg = cv[y0:y0 + h, x0:x0 + w]
        reg += (m * amt)[..., None] * (base[y0:y0 + h, x0:x0 + w] - reg)

    def _under_luma(self, cv, kw):
        r = rasterize(kw, (0, 0), 0.0, 0, pad=0)
        if r is None:
            return None
        m, x0, y0 = r
        h, w = m.shape
        st = max(1, int(math.sqrt(h * w / 4000.0)))
        mm = m[::st, ::st]
        tot = float(mm.sum())
        if tot < 1e-3:
            return None
        reg = cv[y0:y0 + h:st, x0:x0 + w:st]
        lum = reg[..., 0] * 0.299 + reg[..., 1] * 0.587 + reg[..., 2] * 0.114
        return float((lum * mm).sum() / tot)

    def _op_lift(self, cv, kw, base):
        soft = float(kw.get('soft', 2.0))
        r = rasterize(kw, (0, 0), wob=0.8, seed=kw['seed'], pad=4 + int(soft * 3), soft=soft)
        if r is None:
            return
        m, x0, y0 = r
        a = (m * float(kw.get('amt', 1.0)) * 0.85)[..., None]
        h, w = m.shape
        reg = cv[y0:y0 + h, x0:x0 + w]
        reg += a * (base[y0:y0 + h, x0:x0 + w] - reg)

    def _offset(self, kw, size, key, lo=2.0, hi=5.0):
        if kw.get('a_off') is not None:
            o = kw['a_off']
            if isinstance(o, (tuple, list)):
                return float(o[0]), float(o[1])
            hi = lo = float(o)
        if kw.get('offset') is not None:
            o = kw['offset']
            if isinstance(o, (tuple, list)):
                return float(o[0]), float(o[1])
            hi = lo = float(o)
        r = rng(kw['seed'], key)
        ang = r.uniform(0, 2 * math.pi)
        rad = r.uniform(lo, hi)
        rad = min(rad, 0.06 * size + 0.4)
        return rad * math.cos(ang), rad * math.sin(ang)

    def _op_fill(self, cv, kw, base):
        col = kw['color']
        seed = kw['seed']
        pig = pigment(col)
        red = bool(col.get('red'))
        wsz, hsz = region_size(kw)
        size = min(wsz, hsz)
        rd = rng(seed, self._dd, 'wbo')
        boil = self._boil(kw, WASH_BOIL)
        off = self._offset(kw, size, 'off')
        off = (off[0] + rd.normal(0, boil * 0.5), off[1] + rd.normal(0, boil * 0.5))
        lum = luma(pig)
        lp = luma(PAPER_RGB)
        ratio = lum / lp
        # 浓度：深色浓一些、浅色淡一些；整体褪色
        if red:
            dens = 0.95
        elif ratio < 0.35:
            dens = 0.92 * FADE + 0.12
        elif ratio < 0.7:
            dens = 0.78 * FADE
        else:
            dens = 0.78 * FADE
        dens *= float(kw.get('a_dens', 1.0))
        partial = 0.0 if (red or col.get('name') in WARM_NAMES) else float(_smooth(0.80, 0.985, ratio)) * 0.62
        if kw.get('a_partial') is not None:
            partial = float(kw['a_partial'])
        soft = float(kw.get('soft', 0.8))
        wob = float(kw.get('rough', 1.0)) * min(1.4, 0.3 + size * 0.03)
        edge = float(kw.get('rim', 0.45))
        bloom = int(kw.get('bloom', 0) or 0)
        if bloom == 0 and size > 140 and not red:
            bloom = int(rng(seed, 'nb').integers(0, 3))
        pad = int(2.4 * 2 + soft * 3 + 6)
        streak = float(kw.get('streak', 0.0))
        anchor = kw.get('anchor', kw.get('a_anchor', (0.0, 0.0))) or (0.0, 0.0)
        # 暗色：先铺一层浅一些、冷一些的底色（不错位），留出深浅层次
        if ratio < 0.45 and not red:
            under = pig * 0.55 + PAPER_RGB * 0.45
            under = under + (luma(under) - under) * 0.15 + np.float32([-0.02, -0.01, 0.03])
            r0 = rasterize(kw, (0.0, 0.0), wob=wob * 0.8, seed=(seed, 'u'), pad=pad, soft=soft)
            if r0 is not None:
                m0, ux0, uy0 = r0
                wash_core(cv, m0, ux0, uy0, trans_of(under), (seed, 'u'), 0.55, edge=0.3, var=0.25, gran=0.1,
                          grad=kw.get('grad'), rgrad=kw.get('rgrad'), anchor=anchor, vig=self._vig)
            dens *= 0.92
        if red:
            # 红色线索任何时候都要是红的：先把底下“留白”（回到纸色），再上透明的红
            off = (off[0] * 0.35, off[1] * 0.35)
            self._restore(cv, kw, base, 0.88, soft=0.7, seed=seed)
        else:
            # 比底下还亮的颜色（深色夜空里的暖窗）：水彩不能往亮里画，画家会先把这块留白
            want = kw.get('a_reserve')
            if want is None:
                want = col.get('name') not in GLAZE_NAMES
            under = self._under_luma(cv, kw) if want else None
            if under is not None and lum > under + 0.15:
                self._restore(cv, kw, base, float(np.clip((lum - under - 0.15) / 0.25, 0, 0.92)), soft=0.7,
                              seed=seed, wob=0.6)
        r = rasterize(kw, off, wob=wob, seed=seed, pad=pad, soft=soft)
        if r is None:
            return
        m, x0, y0 = r
        side = kw.get('a_side')
        wash_core(cv, m, x0, y0, trans_of(pig), seed, dens, edge=edge, gran=0.30 if not red else 0.12,
                  var=0.36 if not red else 0.18, bloom=bloom, partial=partial, side=side, grad=kw.get('grad'),
                  rgrad=kw.get('rgrad'), streak=streak, anchor=anchor, vig=self._vig)

    def _op_shade(self, cv, kw, base):
        seed = kw['seed']
        col = kw.get('color')
        amount = float(kw.get('amount', 0.3))
        if col is not None:
            pig = pigment(col)
            if col.get('red'):
                pig = pig * 0.75
        else:
            pig = SHADOW
        wsz, hsz = region_size(kw)
        size = min(wsz, hsz)
        rd = rng(seed, self._dd, 'wbo')
        boil = self._boil(kw, WASH_BOIL)
        off = self._offset(kw, size, 'soff', 0.8, 2.2)
        off = (off[0] + rd.normal(0, boil * 0.4), off[1] + rd.normal(0, boil * 0.4))
        soft = float(kw.get('soft', 1.8))
        pad = int(2.4 * 2 + soft * 3 + 6)
        r = rasterize(kw, off, wob=min(1.2, 0.3 + size * 0.02), seed=seed, pad=pad, soft=soft)
        if r is None:
            return
        m, x0, y0 = r
        dens = min(1.2, amount * 1.15) * FADE * float(kw.get('a_dens', 1.0))
        big = (wsz * hsz) / float(W * H)
        if big > 0.12:
            dens *= 1.0 - 0.45 * min(1.0, (big - 0.12) / 0.3)       # 大面积的阴影更轻
        anchor = kw.get('anchor', kw.get('a_anchor', (0.0, 0.0))) or (0.0, 0.0)
        wash_core(cv, m, x0, y0, trans_of(pig), seed, dens, edge=float(kw.get('rim', 0.3)), gran=0.25, var=0.3,
                  grad=kw.get('grad'), rgrad=kw.get('rgrad'), anchor=anchor, vig=self._vig)
        # 彩铅排线：顺着建议方向，在阴影深处轻轻排几笔
        ang = kw.get('angle')
        want = kw.get('a_hatch', ang is not None)
        if want and size > 10 and big < 0.10:
            ang = 55.0 if ang is None else float(ang)
            hm = hatch_mask(m, x0, y0, ang, 6.5, 1.0, (seed, 'sh'), self._dd, self._boil(kw, 0.6))
            if hm is not None:
                f = grad_factor(x0, y0, m.shape[0], m.shape[1], kw.get('grad'), kw.get('rgrad'))
                if f is not None:
                    hm = hm * np.clip(f, 0, 1)
                hm = hm * ((0.45) + 0.55 * PGRAIN[y0:y0 + m.shape[0], x0:x0 + m.shape[1]])
                hc = np.clip(pig * 0.72, 0, 1)
                deposit(cv, hm * min(0.5, 0.18 + 0.5 * amount), x0, y0, hc, VL if self._vig else None)

    def _op_hatch(self, cv, kw, base):
        seed = kw['seed']
        col = kw.get('color')
        c = pencil_color(col, INK_BG) if col is not None else INK_BG
        r = rasterize(kw, (0, 0), wob=0.0, seed=seed, pad=4, soft=1.2)
        if r is None:
            return
        m, x0, y0 = r
        hm = hatch_mask(m, x0, y0, float(kw['angle']), float(kw['spacing']), 1.15, seed, self._dd,
                        self._boil(kw, 0.6))
        if hm is None:
            return
        f = grad_factor(x0, y0, m.shape[0], m.shape[1], kw.get('grad'), None)
        if f is not None:
            hm = hm * np.clip(f, 0, 1)
        hm = hm * (0.5 + 0.5 * PGRAIN[y0:y0 + m.shape[0], x0:x0 + m.shape[1]])
        alpha = 0.12 + 0.75 * float(kw.get('tone', 0.3))
        deposit(cv, hm * alpha, x0, y0, c, VL if self._vig else None)

    def _op_line(self, cv, kw, base):
        role = kw.get('role', 'contour')
        a_, b_, al0, al1, grain, press = ROLE.get(role, ROLE['contour'])
        col = kw.get('color')
        tone = float(kw.get('tone', 0.85))
        w = float(kw['w'])
        seed = kw['seed']
        dd = self._dd
        P = np.asarray(kw['pts'], np.float64)
        closed = bool(kw.get('closed', False))
        taper = kw.get('taper', (0.12, 0.30)) or (0.12, 0.30)
        boil = self._boil(kw, LINE_BOIL)
        dry = float(kw.get('dry', 0.0))
        grain = min(0.95, grain + 0.3 * dry)
        breaks = float(kw.get('breaks', 0.0))
        head = float(kw.get('head', 0.0))
        lift = float(kw.get('lift', 0.0))
        fade = float(kw.get('fade', 0.0))
        mode = 'mul'
        sketchy = role in ('sketch', 'construct')
        if sketchy:
            color = GRAPHITE if (col is None or not col.get('red')) else pencil_color(col)
        else:
            color = pencil_color(col, self._ink)
            if col is not None and col.get('red'):
                mode = 'norm'                                          # 红线：始终是红的
                color = np.asarray(col['rgb'], np.float32) * 0.96
            elif col is not None and luma(col['rgb']) > 0.86:
                mode = 'norm'                                          # 白色线：不透明白彩铅
                color = np.clip(col['rgb'] * 0.6 + CREAM * 0.4, 0, 1)
        red = col is not None and col.get('red')
        wpx = a_ + b_ * w
        if red:
            wpx = 0.6 + 0.42 * w
        alpha = al0 + al1 * tone
        if red:
            alpha = min(1.0, alpha + 0.15)
        if sketchy:
            reps = int(kw.get('reps', 2 if role == 'sketch' else 1))
            spread = float(kw.get('spread', 1.6))
            rs = rng(seed, 'sk')
            for k in range(max(1, reps)):
                Q = P + rs.normal(0, spread, P.shape) * (k > 0) + rs.normal(0, spread * 0.6, 2) * (k > 0)
                if not closed and len(Q) >= 2 and k > 0:
                    t = rs.uniform(0, 0.25)
                    if rs.random() < 0.5:
                        Q[0] = Q[0] + (Q[1] - Q[0]) * t
                    else:
                        Q[-1] = Q[-1] + (Q[-2] - Q[-1]) * t
                a = alpha * (1.0 if k == 0 else rs.uniform(0.35, 0.7))
                ww = wpx * (1.0 if k == 0 else rs.uniform(0.55, 0.85))
                pencil(cv, Q, ww, color, a, (seed, k), dd, boil * 1.4, taper=(0.12, 0.2),
                       over=5.0 * rs.uniform(0.5, 1.4) if not closed else 0.0, press=press, grain=grain,
                       closed=closed, gaps=breaks * 0.8, head=head, lift=lift, fade=fade, vig=self._vig)
            return
        if closed:
            # 闭合轮廓：分 2–3 笔画，接头处略有重叠/出头
            D = spline(P, 3.0, closed=True).astype(np.float64)
            if len(D) < 6:
                pencil(cv, P, wpx, color, alpha, seed, dd, boil, closed=True, press=press, grain=grain, mode=mode,
                       vig=self._vig)
                return
            L = float(arclen(np.vstack([D, D[:1]]))[-1])
            rs = rng(seed, 'split')
            nseg = 1 if L < 60 else (2 if L < 400 else 3)
            if nseg == 1:
                pencil(cv, D[::3], wpx, color, alpha, seed, dd, boil, closed=True, press=press, grain=grain,
                       gaps=breaks, mode=mode, vig=self._vig)
                return
            N = len(D)
            st = int(rs.integers(0, N))
            cuts = np.sort(rs.uniform(0, 1, nseg - 1)) if nseg > 2 else np.array([rs.uniform(0.4, 0.6)])
            bounds = [0] + [int(c * N) for c in cuts] + [N]
            ov = max(2, int(N * 0.03))
            for k in range(nseg):
                a0 = bounds[k] - (ov if k > 0 else ov // 2)
                a1 = bounds[k + 1] + ov
                idx = (np.arange(a0, a1) + st) % N
                seg = D[idx]
                if len(seg) < 3:
                    continue
                step = max(1, len(seg) // 24)
                pts = seg[::step]
                if not np.allclose(pts[-1], seg[-1]):
                    pts = np.vstack([pts, seg[-1:]])
                pencil(cv, pts, wpx * rs.uniform(0.88, 1.08), color, alpha * rs.uniform(0.9, 1.0), (seed, k), dd,
                       boil, taper=(0.06, 0.10), tmin=0.25, over=0.7, press=press, grain=grain, gaps=breaks,
                       head=head * 0.5, mode=mode, vig=self._vig)
            return
        pencil(cv, P, wpx, color, alpha, seed, dd, boil, taper=taper, over=1.5, press=press, grain=grain,
               gaps=breaks, head=head, lift=lift, fade=fade, mode=mode, vig=self._vig)

    def _op_dot(self, cv, kw, base):
        col = kw['color']
        seed = kw['seed']
        rx, ry = float(kw['rx']), float(kw['ry'])
        if rx < 0.4 and ry < 0.4:
            return
        rd = rng(seed, self._dd, 'dot')
        b = self._boil(kw, 0.25)
        x = float(kw['x']) + rd.normal(0, b)
        y = float(kw['y']) + rd.normal(0, b)
        rot = float(kw.get('rot', 0.0))
        tone = float(kw.get('tone', 0.9))
        red = bool(col.get('red'))
        rgb = np.asarray(col['rgb'], np.float32)
        rs = rng(seed, 'dshape')
        n = max(8, int((rx + ry) * 0.9))
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        rr = 1 + 0.07 * rs.normal(0, 1, n)
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        ex, ey = rx * rr * np.cos(a), ry * rr * np.sin(a)
        poly = np.stack([x + ex * cr - ey * sr, y + ex * sr + ey * cr], 1)
        r_ = max(rx, ry)
        if not red and luma(rgb) > 0.88:
            # 白点（雪、高光）：不透明白彩/留白
            soft = min(1.2, 0.25 * r_ + 0.3)
            r0 = rasterize(dict(polys=[poly]), (0, 0), 0.0, seed, pad=4, soft=soft)
            if r0 is None:
                return
            m, x0, y0 = r0
            c = np.clip(rgb * 0.5 + CREAM * 0.5, 0, 1)
            deposit_norm(cv, m * 0.92, x0, y0, c, None)
            return
        pig = pigment(col)
        if red:
            dens = 0.96
            soft, edge, var, gran = 0.35, 0.7, 0.15, 0.1
        elif tone < 0.3 or col.get('name') == 'blush':
            dens = (0.30 + 0.5 * tone) * FADE
            soft, edge, var, gran = max(1.0, 0.28 * r_), 0.0, 0.25, 0.1
        else:
            dens = (0.45 + 0.52 * tone) * (FADE if luma(pig) > 0.35 else 1.0)
            soft, edge, var, gran = 0.4, 0.5, 0.15, 0.15
        off = (0.0, 0.0)
        if r_ > 5:
            o = self._offset(kw, r_ * 2, 'doff', 0.5, 2.0)
            off = o
        if red:
            self._restore(cv, dict(polys=[poly]), base, 0.9, soft=0.5, seed=seed)
        r0 = rasterize(dict(polys=[poly]), off, 0.3, seed, pad=int(4 + soft * 3), soft=soft)
        if r0 is None:
            return
        m, x0, y0 = r0
        wash_core(cv, m, x0, y0, trans_of(pig), seed, dens, edge=edge, edge_sigma=min(2.4, 0.3 * r_ + 0.6),
                  gran=gran, var=var, vig=self._vig)
        if (tone < 0.3 or col.get('name') == 'blush') and r_ > 6:
            # 腮红：一小片彩铅排线
            hm = hatch_mask(m, x0, y0, 62.0 + rot, 3.4, 1.0, (seed, 'bh'), self._dd, self._boil(kw, 0.4),
                            shorten=0.25)
            if hm is not None:
                deposit(cv, hm * 0.42, x0, y0, np.clip(pig * 0.9, 0, 1), VL if self._vig else None)
        if red and r_ >= 2.6:
            # 红豆：小高光（留白）
            hx = x - 0.35 * rx * cr + 0.35 * ry * sr
            hy = y - 0.35 * rx * sr - 0.35 * ry * cr
            hp = np.stack([hx + 0.28 * rx * np.cos(a), hy + 0.22 * ry * np.sin(a)], 1)
            r1 = rasterize(dict(polys=[hp]), (0, 0), 0.0, seed, pad=3, soft=0.4)
            if r1 is not None:
                mh, hx0, hy0 = r1
                hh, ww = mh.shape
                reg = cv[hy0:hy0 + hh, hx0:hx0 + ww]
                reg += (mh * 0.55)[..., None] * (base[hy0:hy0 + hh, hx0:hx0 + ww] - reg)

    def _op_light(self, cv, kw, base):
        col = kw['color']
        cx, cy = float(kw['cx']), float(kw['cy'])
        rx, ry = max(1.0, float(kw['rx'])), max(1.0, float(kw['ry']))
        amt = float(kw.get('amt', 0.5))
        bb = _clip_bbox(cx - 2.2 * rx, cy - 2.2 * ry, cx + 2.2 * rx, cy + 2.2 * ry)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        xs = (np.arange(x0, x1, dtype=np.float32)[None, :] - cx) / rx
        ys = (np.arange(y0, y1, dtype=np.float32)[:, None] - cy) / ry
        g = np.exp(-(xs * xs + ys * ys) * 1.4)
        nl = sample_tex(NLO, (kw['seed'], 'light'), x0, y0, x1 - x0, y1 - y0)
        g = g * (0.85 + 0.3 * nl)
        lamp = pigment(col)
        glow = np.clip(lamp * 0.45 + GLOW * 0.55, 0, 1)
        if self._vig:
            g = g * np.clip(VWE[y0:y1, x0:x1], 0, 1)
        # 暖色罩染（水彩里的一层淡黄）+ 提亮（光把纸照亮）
        warm = trans_of(np.clip(lamp * 0.75 + PAPER_RGB * 0.25, 0, 1))
        reg = cv[y0:y1, x0:x1]
        reg *= 1 - (g * amt * 0.75)[..., None] * (1 - warm)            # 湿画法的一团暖黄
        reg += (g * g * amt * 0.55)[..., None] * glow * (1 - reg)       # 光把纸照亮

    # ------------------------------------------------------------------ 歌词
    def paint_text(self, rgb, items, d):
        if not items:
            return rgb
        bx0 = min(it['x'] for it in items) - 40
        by0 = min(it['y'] for it in items) - 40
        bx1 = max(it['x'] + it['mask'].shape[1] for it in items) + 40
        by1 = max(it['y'] + it['mask'].shape[0] for it in items) + 40
        bb = _clip_bbox(bx0, by0, bx1, by1)
        if bb is None:
            return rgb
        X0, Y0, X1, Y1 = bb
        hh, ww = Y1 - Y0, X1 - X0
        union = np.zeros((hh, ww), np.float32)
        placed = []
        for it in items:
            m = it['mask']
            dx0, dy0 = it['x'] - X0, it['y'] - Y0
            mh, mw = m.shape
            ax0, ay0 = max(dx0, 0), max(dy0, 0)
            ax1, ay1 = min(dx0 + mw, ww), min(dy0 + mh, hh)
            if ax1 <= ax0 or ay1 <= ay0:
                continue
            sub = m[ay0 - dy0:ay1 - dy0, ax0 - dx0:ax1 - dx0] * float(it['alpha'])
            np.maximum(union[ay0:ay1, ax0:ax1], sub, out=union[ay0:ay1, ax0:ax1])
            placed.append((it, sub, ax0, ay0, ax1, ay1))
        if not placed:
            return rgb
        # 奶油色柔光衬底（不是实心框）
        dil = cv2.dilate(union, np.ones((9, 9), np.uint8))
        h1 = cv2.GaussianBlur(dil, (0, 0), 8)
        h2 = cv2.GaussianBlur(dil, (0, 0), 20)
        hal = np.clip(h1 * 1.25 + h2 * 0.85, 0, 1)
        nz = sample_tex(NMID, 'halo', X0, Y0, ww, hh)
        hal = hal * (0.86 + 0.14 * nz)
        deposit_norm(rgb, hal * 0.80, X0, Y0, CREAM, None)
        grain = PGRAIN[Y0:Y1, X0:X1]
        for it, sub, ax0, ay0, ax1, ay1 in placed:
            s = float(it['sung'])
            g = grain[ay0:ay1, ax0:ax1]
            if s >= 0.999:
                red = sub
                brown = None
            elif s <= 0.001:
                red = None
                brown = sub
            else:
                # 红色从字心向外扩散
                h_, w_ = sub.shape
                tot = float(sub.sum()) + 1e-6
                yy = np.arange(h_, dtype=np.float32)[:, None]
                xx = np.arange(w_, dtype=np.float32)[None, :]
                cyy = float((sub * yy).sum()) / tot
                cxx = float((sub * xx).sum()) / tot
                dist = np.hypot(xx - cxx, yy - cyy)
                R = float(dist[sub > 0.3].max()) if (sub > 0.3).any() else 1.0
                rr = s * (R + 6.0)
                k = np.clip((rr - dist) / 5.0 + 0.5, 0, 1)
                red = sub * k
                brown = sub * (1 - k)
            if brown is not None:
                a = brown * (0.80 + 0.20 * g)
                deposit(rgb, a * 0.94, X0 + ax0, Y0 + ay0, trans_of(TEXT_INK), None)
                a2 = np.roll(brown, 1, axis=1) * 0.25 * g
                deposit(rgb, a2, X0 + ax0, Y0 + ay0, trans_of(TEXT_INK), None)
            if red is not None:
                a = red * (0.88 + 0.12 * g)
                deposit_norm(rgb, a, X0 + ax0, Y0 + ay0, LYRIC_RED, None)
                # 水彩干后的边：边缘略深
                inner = cv2.GaussianBlur(red, (0, 0), 1.6)
                rim = np.clip(red - inner, 0, 1) * 1.6
                deposit_norm(rgb, np.clip(rim, 0, 1) * 0.55, X0 + ax0, Y0 + ay0, TEXT_RED_D, None)
        # 唱到的字下面：一道红铅笔手绘下划线，随演唱从左往右画出来
        for it in items:
            u = core.underline_mask(it, width=3.0, wob=2.0)
            if u is None:
                continue
            um, ux, uy = u
            r = core.clip_box(ux, uy, um.shape[1], um.shape[0])
            if r is None:
                continue
            sx0, sy0, dx0, dy0, w_, h_ = r
            a = um[sy0:sy0 + h_, sx0:sx0 + w_] * (0.55 + 0.45 * PGRAIN[dy0:dy0 + h_, dx0:dx0 + w_])
            deposit_norm(rgb, a * 0.9, dx0, dy0, LYRIC_RED, None)
        return rgb
