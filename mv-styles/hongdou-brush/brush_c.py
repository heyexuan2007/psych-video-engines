# -*- coding: utf-8 -*-
"""
C 笔刷「水墨炭笔 · 留白一点红」—— 把 Pen 指令画成宣纸上的水墨 + 炭笔。

颜色模型（移植自 style_C/hd.py）：不是“在画布上涂颜色”，而是记录每个像素吸了多少颜料（密度），
最后按 Beer-Lambert 把纸色乘上透射率：  rgb = paper * exp(-(I*A_ink + R*A_red + C*A_char))
  I = 墨（暖黑，墨分五色 = I 的浓淡）   R = 朱砂（全片唯一彩色：红豆、红线…）   C = 炭笔/石墨（冷灰：排线、草稿）
叠墨会自然变深但永远到不了纯黑；白就是纸本身（留白）。

指令 → 材质：
  group  → Sheet 画层（局部包围盒），end 时 composite：先按 A 挖空后面，再叠颜料；bleed 向纸纤维洇墨
  cover  → cover_poly / cover_mask（挖空 + 同层先画的也被挡住）
  fill   → wash 墨晕（rim 水渍边 / bloom 水渍花 / fade_rough 淡出 / streak 笔痕 / grad / rgrad / offset）
           墨色浓度 = kw.tone 或 color.tone（都没有时按明度换算）；red → R 通道（按 Beer-Lambert 分解成 R+I）
           大面积的固有色会自动淡一些、并向一侧“画到一半就停”（留白），可用 c_fade=False 关掉
  shade  → I 通道淡墨晕 + C 通道炭笔排线（angle 方向）
  line   → 毛笔 stroke（距离场：head 起笔顿 / lift 行笔提 / taper 出锋 / dry 飞白 / fade / streak / rag / pool）
           role: contour / detail / feature 用墨；sketch / construct 用炭笔（C 通道）重复描 reps 遍、spread 离散、breaks 断开
           color 红 → R 通道；'graphite' → C 通道；很浅的颜色（雪、纸）→ 提白线
  hatch  → 炭笔排线（被纸纹打断）
  dot    → 不规则墨点；红豆 = 朱砂点 + 暗部 + 高光；很浅的点（雪）= 提白
  light  → 水墨里光 = 留白：以水提白（并挖开下面的画层）
  lift   → 提白 / 擦除
歌词 paint_text：横排行楷，未唱 = 墨色洇开，唱到 = 红豆红从字心洇开，纸色柔光衬底。
印章 seal(rgb, x, y, w, h, text)：独立函数，片头片尾用（歌词旁不再盖章）。
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
from core import (W, H, FONT_DIR, LYRIC_RED, LYRIC_SIZE, sd, rng, vnoise, smooth01, sstep, spline, poly_mask,
                  bbox_of, as_polys, hex2rgb)

FONT_SEAL = FONT_DIR + '/STLITI.TTF'      # 华文隶书（印章）

# =========================================================================== 颜色
PAPER = hex2rgb('#F4F1EA')


def absorb(c):
    """某颜料在 密度=1 时把纸色变成 c，所需的每通道吸收系数。c 为 '#RRGGBB' 或 rgb。"""
    rgb = hex2rgb(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return (-np.log(np.clip(rgb / PAPER, 1e-4, 1.0))).astype(np.float32)


A_INK = absorb('#2B2724')     # 焦墨：暖黑，不是 #000
A_RED = absorb('#B5302A')     # 朱砂
A_CHAR = absorb('#5A5E64')    # 炭笔/石墨：偏冷的灰
A_LYR = absorb(LYRIC_RED)     # 唱到的字：红豆红

BOIL_K = 1.0                  # 抖动系数：kw['boil'] × BOIL_K = 控制点抖动像素
_LUMA_PAPER = 0.299 * PAPER[0] + 0.587 * PAPER[1] + 0.114 * PAPER[2]
_LUMA_INK = float(0.299 * 0.1686 + 0.587 * 0.1529 + 0.114 * 0.1412)


def tone_to_dens(tone):
    """“墨色浓度”0..1 → I 通道密度。中间调压得淡一些（水墨偏向留白），浓墨保留（头发 0.86 → 0.65）；
    极淡的（皮肤 0.05）给一层看得见的暖灰，不是纸白面具；0 就是留白。"""
    t = float(np.clip(tone, 0.0, 1.2))
    if t <= 0.0:
        return 0.0
    bump = 0.03 * float(smooth01(t / 0.05)) * (1.0 - float(smooth01((t - 0.1) / 0.2)))
    return 0.78 * t ** 1.25 + bump


def luma_tone(rgb):
    """没有 tone 的颜色：按明度换算成墨色浓度（Beer-Lambert 反推，再淡一些——水墨偏向留白）。"""
    l = core.luma(rgb)
    I = -math.log(max(l, 1e-3) / _LUMA_PAPER) / -math.log(_LUMA_INK / _LUMA_PAPER)
    return float(np.clip(I * 0.85, 0.0, 1.0))


_RED_SPLIT = {}


def red_split(rgb):
    """红色系固有色 → (朱砂密度 R, 墨密度 I)：两种颜料的非负最小二乘，让 paper*exp(-(R*A_red+I*A_ink)) ≈ rgb。"""
    key = tuple(np.round(np.asarray(rgb, np.float32), 4))
    if key in _RED_SPLIT:
        return _RED_SPLIT[key]
    t = absorb(rgb)
    M = np.stack([A_RED, A_INK], 1)
    best = None
    for mode in ('both', 'r'):
        if mode == 'both':
            x, *_ = np.linalg.lstsq(M, t, rcond=None)
            if (x < 0).any():
                continue
        else:
            x = np.float32([max(0.0, float(A_RED @ t) / float(A_RED @ A_RED)), 0.0])
        err = float(np.sum((M @ x - t) ** 2))
        if best is None or err < best[0]:
            best = (err, x)
    r, i = best[1]
    out = (float(np.clip(r, 0.3, 1.6)), float(np.clip(i, 0.0, 0.6)))
    _RED_SPLIT[key] = out
    return out


# =========================================================================== 噪声 / 纸
def noise1(u, seed, freq=4.0, octaves=3):
    """一维平滑噪声（几组正弦），u 可为数组。范围约 [-1, 1]。"""
    r = rng(seed, 55)
    u = np.asarray(u, np.float32)
    out = np.zeros_like(u)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        f = freq * (2.13 ** o) * r.uniform(0.8, 1.25)
        out += amp * np.sin(2 * math.pi * (f * u + r.uniform(0, 1)))
        tot += amp
        amp *= 0.55
    return out / tot


_PAPER = {}


def paper_tex(seed=11):
    """宣纸：象牙白底 + 低频斑驳 + 长纤维 + 细纸纹（tooth）。整片固定不变（避免整图闪烁）。"""
    if seed in _PAPER:
        return _PAPER[seed]
    r = rng(seed, 1)
    mott = vnoise(H, W, 340, sd(seed, 2), octaves=4, persist=0.55)
    fd = np.zeros((H, W), np.uint8)
    fl = np.zeros((H, W), np.uint8)
    for i in range(3200):
        x, y = r.uniform(-80, W + 80), r.uniform(-80, H + 80)
        L = 20 + r.gamma(1.6, 55)
        a = r.uniform(0, 2 * math.pi)
        k = r.normal(0, 0.035)
        n = max(3, int(L / 9))
        pts = []
        for j in range(n):
            pts.append((x, y))
            a += k + r.normal(0, 0.06)
            x += 9 * math.cos(a)
            y += 9 * math.sin(a)
        pts = (np.array(pts) * 16).astype(np.int32)
        if r.random() < 0.62:
            cv2.polylines(fd, [pts], False, int(r.uniform(35, 120)), 1, cv2.LINE_AA, shift=4)
        else:
            cv2.polylines(fl, [pts], False, int(r.uniform(60, 160)), 1, cv2.LINE_AA, shift=4)
    fdf = cv2.GaussianBlur(fd.astype(np.float32) / 255.0, (0, 0), 0.55)
    flf = cv2.GaussianBlur(fl.astype(np.float32) / 255.0, (0, 0), 0.7)
    tooth = vnoise(H, W, 2.6, sd(seed, 3), octaves=2, persist=0.6)
    tooth = cv2.GaussianBlur(tooth, (0, 0), 0.45)
    tooth = np.clip(0.5 + tooth / (3.2 * tooth.std() + 1e-6), 0, 1).astype(np.float32)
    fiber_soft = cv2.GaussianBlur(fdf, (0, 0), 2.0)
    fiber_soft = fiber_soft / (fiber_soft.max() + 1e-6)
    tone = (1.0 + 0.014 * mott - 0.010 * (tooth - 0.5))[..., None]
    rgb = PAPER[None, None, :] * tone
    rgb = rgb - 0.045 * fdf[..., None] * np.array([1.0, 1.0, 1.08], np.float32)
    rgb = rgb + 0.022 * flf[..., None]
    rgb = np.clip(rgb, 0, 1).astype(np.float32)
    P = dict(
        rgb=rgb,
        tooth=tooth,
        fiber=fiber_soft.astype(np.float32),
        bleed=(0.72 + 0.56 * fiber_soft).astype(np.float32),                # 洇墨的纤维调制
        absI=(0.90 + 0.16 * tooth + 0.30 * fdf).astype(np.float32),         # 墨在纤维处略深
        absR=(0.88 + 0.22 * tooth).astype(np.float32),                       # 朱砂颗粒感
        absC=np.clip(0.25 + 1.35 * tooth, 0, 1.45).astype(np.float32),       # 炭笔只挂在纸纹凸起上
    )
    _PAPER[seed] = P
    return P


_PP = None


def pp():
    global _PP
    if _PP is None:
        _PP = paper_tex(11)
    return _PP


# =========================================================================== 画层
class Sheet:
    """一张局部画层：I/R/C 三种颜料密度 + A 遮盖（不透明度，用于挡住后面的东西）。坐标一律用全局像素坐标。"""

    def __init__(self, x0=0, y0=0, x1=W, y1=H):
        self.x0, self.y0 = int(max(0, math.floor(x0))), int(max(0, math.floor(y0)))
        self.x1, self.y1 = int(min(W, math.ceil(x1))), int(min(H, math.ceil(y1)))
        self.x1, self.y1 = max(self.x1, self.x0 + 1), max(self.y1, self.y0 + 1)
        h, w = self.y1 - self.y0, self.x1 - self.x0
        self.I = np.zeros((h, w), np.float32)
        self.R = np.zeros((h, w), np.float32)
        self.C = np.zeros((h, w), np.float32)
        self.A = np.zeros((h, w), np.float32)
        self.used = set()
        self.has_a = False

    def copy(self):
        s = Sheet.__new__(Sheet)
        s.x0, s.y0, s.x1, s.y1 = self.x0, self.y0, self.x1, self.y1
        s.I, s.R, s.C, s.A = self.I.copy(), self.R.copy(), self.C.copy(), self.A.copy()
        s.used = set(self.used)
        s.has_a = self.has_a
        return s

    def clip(self, bx0, by0, bx1, by1):
        x0, y0 = max(self.x0, int(math.floor(bx0))), max(self.y0, int(math.floor(by0)))
        x1, y1 = min(self.x1, int(math.ceil(bx1))), min(self.y1, int(math.ceil(by1)))
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1

    def view(self, ch, x0, y0, x1, y1):
        return getattr(self, ch)[y0 - self.y0:y1 - self.y0, x0 - self.x0:x1 - self.x0]

    def add(self, ch, alpha, gx0, gy0, k=0.55):
        """把密度 alpha（左上角在全局 gx0,gy0）叠到通道 ch 上：近似相加，浓处略饱和。"""
        h, w = alpha.shape
        c = self.clip(gx0, gy0, gx0 + w, gy0 + h)
        if c is None:
            return
        x0, y0, x1, y1 = c
        a = alpha[y0 - gy0:y1 - gy0, x0 - gx0:x1 - gx0]
        v = self.view(ch, x0, y0, x1, y1)
        if ch == 'A':
            np.maximum(v, a, out=v)
            self.has_a = True
        else:
            v += a - k * v * a
            self.used.add(ch)

    def mul(self, chs, factor, gx0, gy0):
        """各通道乘以 factor（用于提白/擦除/留白），factor 左上角在全局 gx0,gy0。"""
        h, w = factor.shape
        c = self.clip(gx0, gy0, gx0 + w, gy0 + h)
        if c is None:
            return
        x0, y0, x1, y1 = c
        f = factor[y0 - gy0:y1 - gy0, x0 - gx0:x1 - gx0]
        for ch in chs:
            if ch in self.used:
                v = self.view(ch, x0, y0, x1, y1)
                v *= f

    def erase(self, m, gx0, gy0, amt=1.0):
        """提白：本层颜料按 m 减少，并在 A 里记下（合成时也挖开下面的画层）。"""
        m = np.clip(m * amt, 0, 1).astype(np.float32)
        if self.used:
            self.mul(''.join(sorted(self.used)), 1.0 - m, gx0, gy0)
        self.add('A', m, gx0, gy0)


def composite(dst, src, bleed=0.0, gain=0.72, opacity=1.0, knock=True):
    """把画层 src 盖到 dst 上：先按 src.A 挖掉后面的颜料，再叠 src 的颜料；bleed>0 时颜料沿纸纤维向外洇开。"""
    c = dst.clip(src.x0, src.y0, src.x1, src.y1)
    if c is None:
        return
    x0, y0, x1, y1 = c
    sy, sx = slice(y0 - src.y0, y1 - src.y0), slice(x0 - src.x0, x1 - src.x0)
    A = src.A[sy, sx] if (knock and src.has_a) else None
    if A is not None and opacity != 1.0:
        A = A * opacity
    fib = None
    if bleed > 0 and src.used:
        fib = pp()['bleed'][y0:y1, x0:x1] * gain
    for ch in 'IRC':
        if A is not None and ch in dst.used:
            D = dst.view(ch, x0, y0, x1, y1)
            D *= (1.0 - A)
        if ch not in src.used:
            continue
        D = dst.view(ch, x0, y0, x1, y1)
        S = getattr(src, ch)[sy, sx]
        if fib is not None:
            B = cv2.GaussianBlur(S, (0, 0), bleed)
            S = np.maximum(S, B * fib)
        if opacity != 1.0:
            S = S * opacity
        D += S - 0.55 * D * S
        dst.used.add(ch)
    if A is not None:
        Ad = dst.view('A', x0, y0, x1, y1)
        np.maximum(Ad, A, out=Ad)
        dst.has_a = True


def to_rgb(cv):
    """密度 → 颜色（float32 0..1, H×W×3）。cv 必须是整幅画层。"""
    P = pp()
    I = np.minimum(cv.I, 1.22) * P['absI']
    tau = I[..., None] * A_INK
    if 'R' in cv.used:
        tau += (np.minimum(cv.R, 1.6) * P['absR'])[..., None] * A_RED
    if 'C' in cv.used:
        tau += (np.minimum(cv.C, 1.2) * P['absC'])[..., None] * A_CHAR
    np.exp(-tau, out=tau)
    tau *= P['rgb']
    return tau


# =========================================================================== 几何
def _ipoly(poly, ox, oy, sc=1.0):
    return (np.round((np.asarray(poly, np.float32) - (ox, oy)) * sc * 16)).astype(np.int32)


def wobble(P, amp, seed, d, salt=3, corr=16.0, closed=False):
    """控制点抖动（boil）。稀疏的控制点各自独立抖；稠密的折线按弧长每 corr 像素一个锚点抖，再插值——
    这样场景传进来 2px 间距的稠密线也不会抖成锯齿。种子 = (seed, d)。"""
    P = np.asarray(P, np.float32).reshape(-1, 2)
    n = len(P)
    if amp <= 0 or n == 0:
        return P
    r = rng(seed, d, salt)
    if n < 3:
        return P + r.normal(0, amp, P.shape).astype(np.float32)
    Q = np.vstack([P, P[:1]]) if closed else P
    seg = np.hypot(*np.diff(Q, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    L = float(s[-1])
    k = int(L / corr) + 2
    if k >= n:
        return P + r.normal(0, amp, P.shape).astype(np.float32)
    ua = np.linspace(0, L, k)
    va = r.normal(0, amp, (k, 2))
    if closed:
        va[-1] = va[0]
    off = np.stack([np.interp(s[:n], ua, va[:, 0]), np.interp(s[:n], ua, va[:, 1])], 1)
    return (P + off).astype(np.float32)


# =========================================================================== 毛笔笔触
_DRYTEX = {}


def _bristle_tex(seed, K, Ns):
    """每根笔毫沿笔画方向的含墨起伏（固定于 seed，用于飞白断丝）。值域约 0..1。"""
    key = (seed, K, Ns)
    t = _DRYTEX.get(key)
    if t is None:
        r = rng(seed, 21)
        g = r.standard_normal((K, Ns)).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), sigmaX=float(r.uniform(7.0, 12.0)), sigmaY=0.01)
        g = g / (g.std() + 1e-6) + 0.25 * cv2.GaussianBlur(r.standard_normal((K, Ns)).astype(np.float32), (0, 0),
                                                           sigmaX=1.2, sigmaY=0.01)
        g = (g - g.mean()) / (g.std() + 1e-6)
        t = np.clip(0.5 + 0.30 * g, 0, 1).astype(np.float32)
        ink_k = cv2.GaussianBlur(r.uniform(0.0, 1.0, (K, 1)).astype(np.float32), (0, 0), sigmaX=0.01, sigmaY=0.8)
        ink_k = (ink_k - ink_k.min()) / (ink_k.max() - ink_k.min() + 1e-6)
        t = (t, ink_k[:, 0])
        if len(_DRYTEX) > 4000:
            _DRYTEX.clear()
        _DRYTEX[key] = t
    return t


def stroke(sh, pts, w, ink=0.9, ch='I', seed=0, d=0, boil=1.0, taper=(0.12, 0.30), head=0.25,
           dry=0.0, dry_from=0.5, wn=0.10, closed=False, cover=0.0, spacing=2.0, minw=0.8,
           breaks=0.0, spline_pts=True, fade=0.0, lift=0.0, streak=0.0, rag=0.6, pool=0.0,
           wetedge=0.0, soft=1.0, out=None):
    """
    毛笔笔触（距离场渲染：每个像素都知道自己在笔画上的位置 u 和横向位置 v）。
      w 笔肚宽度（像素）；taper=(起笔渐粗占比, 收笔出锋占比)；head 起笔“顿”；lift 行笔“提”
      dry 飞白（外侧笔毫先干），dry_from 从哪里开始变干；fade 墨色沿笔画变淡；pool 起笔积墨；wetedge 湿边
      streak 笔毫纹；rag 纸纤维咬边；breaks 随机断开（被擦掉的草稿线）
      boil 控制点抖动（像素），种子 (seed, d)；飞白/笔毫纹按 seed 固定，只随 d 微移 → 活而不闪
      out='mask' 时不画到 sh 上，而是返回 (alpha, gx0, gy0)（用于提白线）
    """
    P = np.asarray(pts, np.float32).reshape(-1, 2)
    if len(P) < 2:
        return None
    if boil > 0:
        P = wobble(P, boil, seed, d, 3, corr=14.0 + 7.0 * boil, closed=closed)
    Cc = spline(P, spacing, closed) if spline_pts else P
    dv = np.diff(Cc, axis=0)
    seg = np.hypot(dv[:, 0], dv[:, 1])
    if (seg < 1e-3).any():
        keep = np.concatenate([[True], seg >= 1e-3])
        Cc = Cc[keep]
        dv = np.diff(Cc, axis=0)
        seg = np.hypot(dv[:, 0], dv[:, 1])
    n = len(Cc)
    if n < 2:
        return None
    s = np.concatenate([[0.0], np.cumsum(seg)]).astype(np.float32)
    Ltot = float(max(s[-1], 1e-3))
    u = s / Ltot

    # ---- 笔压：起笔顿、行笔提、收笔出锋
    t0, t1 = taper
    prof = np.ones(n, np.float32)
    if t0 > 0:
        prof *= 0.30 + 0.70 * smooth01(u / t0)
        prof += head * np.exp(-((u - t0 * 0.6) / (t0 * 0.55 + 1e-3)) ** 2)
    if t1 > 0:
        prof *= np.clip((1.0 - u) / t1, 0, 1) ** 0.8 * 0.95 + 0.05
    if lift > 0:
        prof *= 1.0 - lift * np.sin(np.pi * np.clip((u - 0.15) / 0.7, 0, 1)) ** 2
    jd = rng(seed, d, 9).uniform(-0.5, 0.5)
    prof *= 1.0 + wn * noise1(u * (0.6 + Ltot / 160.0) + 0.07 * jd, sd(seed, 7), freq=1.0, octaves=3)
    wv = np.maximum(w * prof, minw).astype(np.float32)
    hw = 0.5 * wv

    pad = float(hw.max()) + 4
    bx0, by0 = float(Cc[:, 0].min() - pad), float(Cc[:, 1].min() - pad)
    bx1, by1 = float(Cc[:, 0].max() + pad), float(Cc[:, 1].max() + pad)
    if sh is not None and sh.clip(bx0, by0, bx1, by1) is None:
        return None
    # 只算画面内的部分
    bx0, by0 = max(bx0, -2.0), max(by0, -2.0)
    bx1, by1 = min(bx1, W + 2.0), min(by1, H + 2.0)
    if bx1 <= bx0 or by1 <= by0:
        return None
    gx0, gy0 = int(math.floor(bx0)), int(math.floor(by0))
    bw, bh = int(math.ceil(bx1)) - gx0 + 1, int(math.ceil(by1)) - gy0 + 1
    if bw * bh > 9_000_000:
        return None

    # ---- 距离场：最近中心线采样点 → 精确到线段的距离、弧长、左右
    ci = np.rint(Cc - (gx0, gy0)).astype(np.int32)
    inside = (ci[:, 0] >= 0) & (ci[:, 0] < bw) & (ci[:, 1] >= 0) & (ci[:, 1] < bh)
    if not inside.any():
        # 中心线全在画面外（只有笔画边缘露进来）：退化为夹到边上
        pass
    ci[:, 0] = np.clip(ci[:, 0], 0, bw - 1)
    ci[:, 1] = np.clip(ci[:, 1], 0, bh - 1)
    src = np.ones((bh, bw), np.uint8)
    src[ci[:, 1], ci[:, 0]] = 0
    dist0, lab = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    idimg = np.full((bh, bw), -1, np.int32)
    idimg[ci[:, 1], ci[:, 0]] = np.arange(n, dtype=np.int32)
    zy, zx = np.nonzero(src == 0)
    lut = np.zeros(len(zy) + 1, np.int32)
    lut[1:] = idimg[zy, zx]
    py, px = np.nonzero(dist0 < pad)
    if len(py) == 0:
        return None
    j0 = lut[lab[py, px]]
    X = (px + gx0).astype(np.float32)
    Y = (py + gy0).astype(np.float32)

    def proj(j):
        j = np.clip(j, 0, n - 2)
        ax, ay = Cc[j, 0], Cc[j, 1]
        dx, dy = dv[j, 0], dv[j, 1]
        qx, qy = X - ax, Y - ay
        tt = np.clip((qx * dx + qy * dy) / (seg[j] ** 2 + 1e-9), 0, 1)
        ex, ey = qx - tt * dx, qy - tt * dy
        return j, tt, ex * ex + ey * ey, dx * qy - dy * qx

    jA, tA, dA, cA = proj(j0 - 1)
    jB, tB, dB, cB = proj(j0)
    ub = dB < dA
    j = np.where(ub, jB, jA)
    tt = np.where(ub, tB, tA)
    dist = np.sqrt(np.where(ub, dB, dA))
    side = np.sign(np.where(ub, cB, cA))
    sp = s[j] + tt * seg[j]
    up = sp / Ltot
    hwp = hw[j] * (1 - tt) + hw[j + 1] * tt

    # 纸纤维咬边（细线咬得少，粗笔咬得多）
    gxi = np.clip(X.astype(np.int32), 0, W - 1)
    gyi = np.clip(Y.astype(np.int32), 0, H - 1)
    ragp = rag * np.clip(hwp / 2.5, 0.2, 1.0) * 1.6
    hwe = hwp + ragp * (pp()['tooth'][gyi, gxi] - 0.5)
    vv = side * dist / np.maximum(hwp, 0.4)          # -1..1 横向位置
    drv = None
    if dry > 0:
        drv = dry * sstep(dry_from, 1.0, up)
        hwe = hwe * (1.0 - 0.16 * drv * (0.5 + 0.5 * noise1(sp / 60.0, sd(seed, 23), 1.0, 2)))
    alpha = np.clip((hwe - dist) / soft + 0.5, 0, 1)

    if dry > 0 or streak > 0:
        K = int(np.clip(w / 1.6, 5, 64))
        step = 1.5
        Ns = int(Ltot / step) + 3
        tex, ink_k = _bristle_tex(sd(seed, K), K, Ns)
        kf = np.clip((vv + 1) * 0.5 * (K - 1), 0, K - 1)
        kb = np.clip((kf + 0.5).astype(np.int32), 0, K - 1)
        si = np.clip((sp / step).astype(np.int32), 0, Ns - 1)
        if streak > 0:
            k0 = np.minimum(kf.astype(np.int32), K - 2) if K > 1 else np.zeros_like(kb)
            fk = kf - k0
            sv = ink_k[k0] * (1 - fk) + ink_k[np.minimum(k0 + 1, K - 1)] * fk
            sl = tex[kb, si]
            sv = 0.55 * sv + 0.45 * sl
            alpha = alpha * (1.0 - streak * (1.0 - sv))
        if dry > 0:
            sh_ = rng(seed, d, 22).uniform(-1.0, 1.0)
            si2 = np.clip(((sp + sh_) / step).astype(np.int32), 0, Ns - 1)
            tv = tex[kb, si2]
            thr = drv * (0.60 + 0.55 * np.abs(vv))
            on = np.clip((tv - thr) / 0.06 + 0.5, 0, 1)
            alpha = alpha * (on + (1 - on) * (1.0 - np.minimum(1.0, drv * 1.6)))
    if breaks > 0:
        nb = noise1(sp / 14.0, sd(seed, 31), freq=1.0, octaves=2) + 0.35 * noise1(sp / 5.0, sd(seed, d, 32), 1.0, 1)
        alpha = alpha * np.clip((nb - (-1.2 + 2.4 * breaks)) / 0.12 + 0.5, 0, 1)

    inkp = np.full_like(up, ink)
    if fade > 0:
        inkp = inkp * (1.0 - fade * up ** 0.9)
    if pool > 0:
        inkp = inkp * (1.0 + pool * np.exp(-(up / 0.09) ** 2))
    if wetedge > 0:
        inkp = inkp * (1.0 + wetedge * np.clip((np.abs(vv) - 0.55) / 0.4, 0, 1))

    res = np.zeros((bh, bw), np.float32)
    res[py, px] = alpha * inkp
    if out == 'mask':
        return res, gx0, gy0
    sh.add(ch, res, gx0, gy0)
    if cover > 0:
        oc = np.zeros((bh, bw), np.float32)
        oc[py, px] = np.minimum(np.clip(hwp - dist + 0.5, 0, 1) * 1.6, 1.0) * cover
        sh.add('A', oc, gx0, gy0)
    return None


def dot_mask(x, y, rx, ry=None, seed=0, d=0, boil=0.5, rot=0.0, soft=0.0):
    """不规则椭圆点的遮罩 → (a, gx0, gy0)。"""
    ry = rx if ry is None else ry
    rx, ry = max(rx, 0.5), max(ry, 0.5)
    r = rng(seed, d, 41)
    x, y = x + r.normal(0, boil), y + r.normal(0, boil)
    n = 12
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + rng(seed, 42).uniform(0, 1)
    irr = float(np.clip(8.0 / max(rx, ry), 0.12, 1.0))       # 大的点（月亮）不要坑坑洼洼
    k = 1.0 + irr * (0.12 * rng(seed, 43).standard_normal(n) + 0.05 * r.standard_normal(n))
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    px, py = rx * k * np.cos(a), ry * k * np.sin(a)
    poly = np.stack([x + px * cr - py * sr, y + px * sr + py * cr], 1)
    poly = spline(poly, 1.5, closed=True)
    pad = max(rx, ry) * 1.4 + 3 + soft * 3
    gx0, gy0 = int(x - pad), int(y - pad)
    sz = int(2 * pad) + 2
    m = np.zeros((sz, sz), np.uint8)
    cv2.fillPoly(m, [_ipoly(poly, gx0, gy0)], 255, cv2.LINE_AA, shift=4)
    a = m.astype(np.float32) / 255.0
    if soft > 0:
        a = cv2.GaussianBlur(a, (0, 0), soft)
    return a, gx0, gy0


def dot(sh, x, y, rx, ry=None, ink=0.9, ch='I', seed=0, d=0, boil=0.5, rot=0.0, soft=0.0):
    """点（豆子、眼珠、雪…）：不规则椭圆墨点。"""
    a, gx0, gy0 = dot_mask(x, y, rx, ry, seed, d, boil, rot, soft)
    sh.add(ch, a * ink, gx0, gy0)
    return a, gx0, gy0


# =========================================================================== 墨晕（填色）
def wash(sh, polys, dens=0.3, seed=0, d=0, soft=5.0, rough=0.22, cell=30.0, var=0.12, rim=0.18,
         grad=None, ch='I', sc=0.5, cover=0.0, jit=1.0, drift=0.22, holes=(), edge=2.4, offset=(0, 0),
         rgrad=None, bloom=0.0, fade_rough=0.0, streak=0.0, sangle=0.0, mask=None, chans=None):
    """
    墨晕/淡彩：区域内一层颜料，边缘经模糊+噪声扰动后像水墨向纸里洇开，内部浓淡不匀，干后边缘略深（水渍边）。
      grad=(x0,y0,x1,y1,g0,g1) 线性浓淡；rgrad=(cx,cy,r0,r1,g0,g1) 径向浓淡；fade_rough 渐变边被噪声打碎
      bloom 水渍花；streak/sangle 大笔刷痕；offset 手工上色的错位；d 只让边缘和浓淡轻微变化（drift）
      mask=(m, gx0, gy0) 直接给遮罩（float 0..1）；chans={'I':dens_I, 'R':dens_R} 一次铺多种颜料
    """
    if chans is None:
        chans = {ch: dens}
    chans = {k: v for k, v in chans.items() if v > 1e-4}
    if not chans:
        return None
    if mask is not None:
        m0, mx0, my0 = mask
        mx0, my0 = int(mx0 + offset[0]), int(my0 + offset[1])
        c = sh.clip(mx0, my0, mx0 + m0.shape[1], my0 + m0.shape[0])
        if c is None:
            return None
        x0, y0, x1, y1 = c
        m = m0[y0 - my0:y1 - my0, x0 - mx0:x1 - mx0]
        if sc != 1.0:
            m = cv2.resize(m, (max(1, int((x1 - x0) * sc)), max(1, int((y1 - y0) * sc))),
                           interpolation=cv2.INTER_AREA)
    else:
        polys = [np.asarray(p, np.float32) + np.float32(offset) for p in as_polys(polys)]
        if not polys:
            return None
        holes = [np.asarray(p, np.float32) + np.float32(offset) for p in as_polys(holes)]
        if jit > 0:
            polys = [wobble(p, jit, seed, d, 11 + i, corr=24.0, closed=True) for i, p in enumerate(polys)]
        pad = soft * 3 + 6
        bb = bbox_of(polys, pad)
        c = sh.clip(*bb)
        if c is None:
            return None
        x0, y0, x1, y1 = c
        m = poly_mask(polys, (x0, y0, x1, y1), sc, holes=holes).astype(np.float32) / 255.0
    lh, lw = m.shape
    if lh < 1 or lw < 1:
        return None
    if soft > 0:
        m = cv2.GaussianBlur(m, (0, 0), max(0.6, soft * sc))
    n1 = vnoise(lh, lw, cell * sc, sd(seed, 61), 2)
    if drift > 0:
        n1 = n1 + drift * vnoise(lh, lw, cell * sc * 0.8, sd(seed, d, 62), 1)
    e = np.clip((m - 0.5) * edge + 0.5 + rough * n1, 0, 1)
    e = e * e * (3 - 2 * e)
    n2 = vnoise(lh, lw, cell * sc * 2.6, sd(seed, 63), 2)
    body = 1.0 + var * (1.3 * n2 + 0.45 * n1)
    if streak > 0:
        # 顺着 sangle 方向拉长的噪声 = 大笔刷痕
        D = int(math.hypot(lh, lw)) + 4
        ns = vnoise(D, max(4, int(D / 8)), max(2.0, 2.0 * sc), sd(seed, 64), 2)
        ns = cv2.resize(ns, (D, D), interpolation=cv2.INTER_LINEAR)
        M = cv2.getRotationMatrix2D((D / 2, D / 2), -sangle, 1.0)
        M[0, 2] += lw / 2 - D / 2
        M[1, 2] += lh / 2 - D / 2
        ns = cv2.warpAffine(ns, M, (lw, lh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        body = body * (1.0 + streak * ns / (ns.std() + 1e-6) * 0.5)
    f = e * body
    if rim > 0:
        rb = cv2.GaussianBlur(e, (0, 0), max(0.8, 2.2 * sc))
        f += rim * np.clip(e - rb, 0, 1) * 3.0
    if bloom > 0:
        nb = vnoise(lh, lw, cell * sc * 1.6, sd(seed, 66), 3, 0.55)
        nb = nb / (nb.std() + 1e-6)
        inside = sstep(0.55, 0.85, nb)
        ring = np.exp(-((nb - 0.55) / 0.09) ** 2)
        f = f * (1.0 - 0.40 * bloom * inside) + bloom * 0.40 * ring * e
    if grad is not None or rgrad is not None:
        yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
        xx = x0 + xx / sc
        yy = y0 + yy / sc
        g = np.ones((lh, lw), np.float32)
        if grad is not None:
            gx0, gy0, gx1, gy1, g0, g1 = grad
            vx, vy = gx1 - gx0, gy1 - gy0
            tt = ((xx - gx0) * vx + (yy - gy0) * vy) / (vx * vx + vy * vy + 1e-6)
            if fade_rough > 0:
                tt = tt + fade_rough * (0.8 * n1 + 0.5 * n2)
            g *= g0 + (g1 - g0) * smooth01(tt)
        if rgrad is not None:
            cx, cy, r0, r1, g0, g1 = rgrad
            rr = (np.hypot(xx - cx, yy - cy) - r0) / (r1 - r0 + 1e-6)
            if fade_rough > 0:
                rr = rr + fade_rough * (0.8 * n1 + 0.5 * n2)
            g *= g0 + (g1 - g0) * smooth01(rr)
        if fade_rough > 0:
            # 淡出的边上留一道浅浅的水痕
            gb = cv2.GaussianBlur(g, (0, 0), max(0.8, 2.0 * sc))
            f = f * g + 0.6 * rim * np.clip(gb - g, 0, 1) * 4.0 * e
        else:
            f = f * g
    f = np.clip(f, 0, None)
    if sc != 1.0:
        f = cv2.resize(f, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
    for k, v in chans.items():
        sh.add(k, (f * v).astype(np.float32), x0, y0)
    if cover > 0:
        cm = e if sc == 1.0 else cv2.resize(e, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
        sh.add('A', np.clip(cm * 1.25, 0, 1) * cover, x0, y0)
    return (x0, y0, x1, y1)


def cover_poly(sh, polys, seed=0, d=0, feather=1.2, amount=1.0, jit=0.0, holes=()):
    """不透明遮盖（挖掉后面的颜料，让此处回到纸色）。"""
    polys = [wobble(p, jit, seed, d, 70 + i, corr=24.0, closed=True) for i, p in enumerate(as_polys(polys))]
    if not polys:
        return
    bb = bbox_of(polys, feather * 3 + 2)
    c = sh.clip(*bb)
    if c is None:
        return
    x0, y0, x1, y1 = c
    m = poly_mask(polys, (x0, y0, x1, y1), 1.0, holes=as_polys(holes)).astype(np.float32) / 255.0
    if feather > 0:
        m = cv2.GaussianBlur(m, (0, 0), feather)
        m = np.clip(m * 1.3, 0, 1)
    cover_mask(sh, m, x0, y0, amount)


def cover_mask(sh, m, gx0, gy0, amount=1.0):
    """用遮罩做不透明遮盖（m: float 0..1，左上角在全局 gx0, gy0）。同一画层里先画的东西也被挡住。"""
    m = np.clip(m * amount, 0, 1).astype(np.float32)
    if sh.used:
        sh.mul(''.join(sorted(sh.used)), 1.0 - m, gx0, gy0)
    sh.add('A', m, gx0, gy0)


# =========================================================================== 炭笔排线
def hatch_region(sh, reg, x0, y0, angle, spacing, dens=0.4, ch='C', seed=0, d=0, boil=0.5, lw=1, jit=0.3,
                 partial=0.35, bow=0.04, grad=None):
    """在区域遮罩 reg（float 0..1，左上角 x0,y0）内画平行排线（炭笔质感：线会被纸纹打断）。angle 为线的方向（度）。"""
    hh, ww = reg.shape
    if hh < 2 or ww < 2:
        return
    spacing = max(2.0, float(spacing))
    a = math.radians(angle)
    v = np.array([math.cos(a), math.sin(a)], np.float32)
    nv = np.array([-v[1], v[0]], np.float32)
    cx, cy = ww / 2, hh / 2
    R = math.hypot(cx, cy)
    r = rng(seed, 81)
    rd = rng(seed, d, 82)
    lines = []
    off = -R
    while off < R:
        base = np.array([cx, cy], np.float32) + nv * off
        a0 = -R + r.uniform(0, partial) * 2 * R
        a1 = R - r.uniform(0, partial) * 2 * R
        if a1 - a0 > 6:
            p0 = base + v * a0
            p2 = base + v * a1
            p1 = (p0 + p2) / 2 + nv * r.normal(0, bow) * (a1 - a0)
            pts = np.stack([p0, p1, p2]) + rd.normal(0, boil, (3, 2)).astype(np.float32)
            lines.append(np.round(spline(pts, 6.0) * 16).astype(np.int32))
        off += spacing * (1.0 + r.uniform(-jit, jit))
    if not lines:
        return
    m = np.zeros((hh, ww), np.uint8)
    cv2.polylines(m, lines, False, 255, lw, cv2.LINE_AA, shift=4)
    f = m.astype(np.float32) * (dens / 255.0) * reg
    if grad is not None:
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        gx0, gy0, gx1, gy1, g0, g1 = grad
        vx, vy = gx1 - gx0, gy1 - gy0
        tt = ((xx + x0 - gx0) * vx + (yy + y0 - gy0) * vy) / (vx * vx + vy * vy + 1e-6)
        f *= g0 + (g1 - g0) * smooth01(tt)
    sh.add(ch, f, x0, y0)


# =========================================================================== 光晕 / 提白
def glow_mask(cx, cy, rx, ry, seed=0, d=0, reach=2.6):
    """水墨的光 = 留白：中心提白的程度图（外圈噪声让边缘不是完美圆）→ (g, x0, y0)。"""
    x0, y0 = int(max(0, cx - reach * rx)), int(max(0, cy - reach * ry))
    x1, y1 = int(min(W, cx + reach * rx)), int(min(H, cy + reach * ry))
    if x1 <= x0 or y1 <= y0:
        return None
    hh, ww = y1 - y0, x1 - x0
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    n = vnoise(hh // 4 + 1, ww // 4 + 1, 14, sd(seed, 91), 2) + 0.15 * vnoise(hh // 4 + 1, ww // 4 + 1, 10,
                                                                               sd(seed, d, 92), 1)
    n = cv2.resize(n, (ww, hh), interpolation=cv2.INTER_LINEAR)
    rr = np.hypot((xx - cx) / max(rx, 1.0), (yy - cy) / max(ry, 1.0))
    g = np.exp(-(rr ** 2) * 0.9) * (1 + 0.25 * n)
    return np.clip(g, 0, 1).astype(np.float32), x0, y0


# =========================================================================== 草稿线（铅笔/炭笔）
def sketch_line(sh, pts, w, ink, seed, d, boil, reps=2, breaks=0.0, spread=1.8, taper=(0.15, 0.25), closed=False,
                ch='C'):
    """草稿线：同一条轮廓松散地重复描 reps 遍，每遍略偏、长度略不同（铅笔起稿的感觉）。"""
    P = np.asarray(pts, np.float32).reshape(-1, 2)
    if len(P) < 2:
        return
    for k in range(max(1, int(reps))):
        r = rng(seed, 900 + k)
        Q = P.copy()
        if k > 0:
            Q = Q + r.normal(0, spread, 2).astype(np.float32)
            Q = wobble(Q, spread * 0.35, seed, 0, 950 + k, corr=20.0, closed=closed)
            if len(Q) > 3 and not closed:
                a = int(r.integers(0, 2))
                b = len(Q) - int(r.integers(0, 2))
                Q = Q[a:b]
        if not closed and len(Q) > 1:
            ext = (Q[-1] - Q[-2])
            ext = ext / (np.hypot(*ext) + 1e-6) * min(float(np.hypot(*(Q[-1] - Q[-2]))), 30.0)
            Q = np.vstack([Q, Q[-1] + ext * r.uniform(0.05, 0.35)])
        stroke(sh, Q, w * (1.0 if k == 0 else 0.75), ink=ink * (1.0 if k == 0 else 0.6), ch=ch,
               seed=seed + 31 * k, d=d, boil=boil, taper=taper, head=0.0, wn=0.22, breaks=breaks, closed=closed,
               spacing=2.5, rag=0.4)


# =========================================================================== 指令 → 材质
ROLE = {
    #            起笔顿  行笔提  飞白   干起点   笔毫纹  积墨   咬边   宽度噪声 宽度系数 墨系数
    'contour': dict(head=0.55, lift=0.30, dry=0.60, dry_from=0.55, streak=0.28, pool=0.18, rag=0.7, wn=0.12, wk=1.0,
                    ik=1.0),
    'detail': dict(head=0.30, lift=0.18, dry=0.50, dry_from=0.45, streak=0.18, pool=0.0, rag=0.5, wn=0.10, wk=0.9,
                   ik=0.9),
    'feature': dict(head=0.05, lift=0.0, dry=0.0, dry_from=0.60, streak=0.0, pool=0.0, rag=0.2, wn=0.06, wk=1.0,
                    ik=1.0),
}


def _split_line(P, w, closed, split=True, corner=55.0):
    """一条线 → 若干笔（控制点数组列表）。尖角（转角 > corner 度）处断开，角上各出头一点；
    闭合线没有尖角时分成首尾相搭的两笔。"""
    P = np.asarray(P, np.float32).reshape(-1, 2)
    # 去掉重复点
    if len(P) > 1:
        keep = np.concatenate([[True], np.hypot(*np.diff(P, axis=0).T) > 1e-3])
        P = P[keep]
    if closed and len(P) > 2 and np.hypot(*(P[0] - P[-1])) < 1e-3:
        P = P[:-1]
    n = len(P)
    if n < 2:
        return [P]
    if not split or n < 3:
        if closed:
            return [np.vstack([P, P[:1]])]
        return [P]
    Q = np.vstack([P, P[:1]]) if closed else P
    seglen = np.hypot(*np.diff(Q, axis=0).T)
    L = float(seglen.sum())
    min_len = max(4.0 * w, 24.0)
    # 各顶点的转角
    if closed:
        a_in = P - np.roll(P, 1, axis=0)
        a_out = np.roll(P, -1, axis=0) - P
        idx = np.arange(n)
    else:
        a_in = P[1:-1] - P[:-2]
        a_out = P[2:] - P[1:-1]
        idx = np.arange(1, n - 1)
    na = np.hypot(*a_in.T) * np.hypot(*a_out.T) + 1e-9
    cosv = np.clip((a_in * a_out).sum(1) / na, -1, 1)
    turn = np.degrees(np.arccos(cosv))
    cands = [int(i) for i, t in zip(idx, turn) if t > corner]
    s = np.concatenate([[0.0], np.cumsum(seglen)])       # 顶点 i 的弧长 = s[i]
    ext = min(0.6 * w, 6.0)

    def extend(A, at_start, at_end):
        A = A.copy()
        if at_start and len(A) >= 2:
            v = A[0] - A[1]
            A = np.vstack([A[:1] + v / (np.hypot(*v) + 1e-6) * ext, A[1:]]) if np.hypot(*v) > 1e-3 else A
        if at_end and len(A) >= 2:
            v = A[-1] - A[-2]
            A = np.vstack([A[:-1], A[-1:] + v / (np.hypot(*v) + 1e-6) * ext]) if np.hypot(*v) > 1e-3 else A
        return A

    if not closed:
        cuts = []
        last = 0.0
        for c in cands:
            if s[c] - last >= min_len and L - s[c] >= min_len:
                cuts.append(c)
                last = s[c]
        if not cuts:
            return [P]
        bounds = [0] + cuts + [n - 1]
        out = []
        for j in range(len(bounds) - 1):
            A = P[bounds[j]:bounds[j + 1] + 1]
            out.append(extend(A, j > 0, j < len(bounds) - 2))
        return out
    # 闭合
    cuts = []
    for c in cands:
        if not cuts or s[c] - s[cuts[-1]] >= min_len:
            cuts.append(c)
    if len(cuts) >= 2 and (L - s[cuts[-1]] + s[cuts[0]]) < min_len:
        cuts.pop()
    if len(cuts) >= 2:
        out = []
        for j in range(len(cuts)):
            a, b = cuts[j], cuts[(j + 1) % len(cuts)]
            A = P[a:b + 1] if b > a else np.vstack([P[a:], P[:b + 1]])
            out.append(extend(A, True, True))
        return out
    # 没有（足够的）尖角：从 start 起分成两笔，首尾各搭一点
    start = cuts[0] if cuts else 0
    R = np.vstack([P[start:], P[:start], P[start:start + 1]])
    sr = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(R, axis=0).T))])
    if L < 3 * min_len:
        # 小圈：一笔画完，末端搭上起笔一点
        k = int(np.searchsorted(sr, 0.08 * L)) + 1
        return [np.vstack([R, R[1:k + 1]])]
    i1 = int(np.searchsorted(sr, 0.56 * L))
    i2 = int(np.searchsorted(sr, 0.48 * L))
    i3 = int(np.searchsorted(sr, 0.05 * L)) + 1
    A = R[:max(i1, 2) + 1]
    B = np.vstack([R[i2:], R[1:i3 + 1]])
    return [A, B]


def _hint(kw, k, dflt):
    v = kw.get('c_' + k)
    if v is None:
        v = kw.get(k)
    return dflt if v is None else v


def _op_bbox(kind, kw):
    """一条指令大概会画到哪里（用于给画层分配包围盒）。"""
    try:
        if kind in ('cover', 'fill', 'shade', 'hatch', 'lift'):
            pad = 3 * float(_hint(kw, 'soft', 5.0)) + 16 + 3 * kw.get('boil', 1.0)
            off = kw.get('offset') or (0, 0)
            if kw.get('mask') is not None:
                m, mx, my = kw['mask']
                m = np.asarray(m)
                return (mx - pad + off[0], my - pad + off[1], mx + m.shape[1] + pad + off[0],
                        my + m.shape[0] + pad + off[1])
            polys = as_polys(kw.get('polys'))
            if not polys:
                return None
            b = bbox_of(polys, pad)
            return (b[0] + min(0, off[0]), b[1] + min(0, off[1]), b[2] + max(0, off[0]), b[3] + max(0, off[1]))
        if kind == 'line':
            P = np.asarray(kw['pts'], np.float32).reshape(-1, 2)
            pad = kw['w'] * 1.6 + 4 * kw.get('boil', 1.0) + 14 + 4 * float(_hint(kw, 'spread', 1.8))
            return (P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if kind == 'dot':
            r = max(kw['rx'], kw['ry']) * 1.8 + 10 + 3 * kw.get('boil', 1.0)
            return (kw['x'] - r, kw['y'] - r, kw['x'] + r, kw['y'] + r)
        if kind == 'light':
            return (kw['cx'] - 2.7 * kw['rx'], kw['cy'] - 2.7 * kw['ry'], kw['cx'] + 2.7 * kw['rx'],
                    kw['cy'] + 2.7 * kw['ry'])
    except Exception:
        return (0, 0, W, H)
    return None


def _group_boxes(ops):
    """每个 group 的包围盒（含嵌套），以及 group 起点 → 对应 end 的下标。"""
    boxes, ends = {}, {}
    stack = []
    for i, (kind, kw) in enumerate(ops):
        if kind == 'group':
            stack.append([i, None])
        elif kind == 'end':
            if not stack:
                continue
            gi, bb = stack.pop()
            ends[gi] = i
            if bb is not None:
                bb = (bb[0] - 8, bb[1] - 8, bb[2] + 8, bb[3] + 8)
            boxes[gi] = bb
            if stack and bb is not None:
                p = stack[-1]
                p[1] = bb if p[1] is None else (min(p[1][0], bb[0]), min(p[1][1], bb[1]),
                                                max(p[1][2], bb[2]), max(p[1][3], bb[3]))
        else:
            if not stack:
                continue
            bb = _op_bbox(kind, kw)
            if bb is None:
                continue
            p = stack[-1]
            p[1] = bb if p[1] is None else (min(p[1][0], bb[0]), min(p[1][1], bb[1]),
                                            max(p[1][2], bb[2]), max(p[1][3], bb[3]))
    return boxes, ends


def _region(kw, pad=2.0, soft=0.0):
    """op 的区域 → (float 遮罩, x0, y0)，可选羽化。"""
    if kw.get('mask') is not None:
        r = core.region_mask(kw, pad)
        if r is None:
            return None
        m, x0, y0 = r
        if soft > 0:
            p = int(math.ceil(soft * 2.5))
            m = cv2.copyMakeBorder(m, p, p, p, p, cv2.BORDER_CONSTANT, value=0)
            m = cv2.GaussianBlur(m, (0, 0), soft)
            x0, y0 = x0 - p, y0 - p
        return m, x0, y0
    polys = as_polys(kw.get('polys'))
    if not polys:
        return None
    pad = pad + soft * 2.5
    bx0, by0, bx1, by1 = bbox_of(polys, pad)
    x0, y0 = int(math.floor(max(bx0, -pad))), int(math.floor(max(by0, -pad)))
    x1, y1 = int(math.ceil(min(bx1, W + pad))), int(math.ceil(min(by1, H + pad)))
    if x1 <= x0 or y1 <= y0:
        return None
    m = poly_mask(polys, (x0, y0, x1, y1), 1.0, as_polys(kw.get('holes', ()))).astype(np.float32) / 255.0
    if soft > 0:
        m = cv2.GaussianBlur(m, (0, 0), soft)
    return m, x0, y0


def _big_area(kw, bx, bw, bh, big, grad, rgrad, fade_rough, streak, sangle):
    """大面积区域：向一侧“画到一半就停”的淡出（大笔横扫由 broad_strokes 另画）。返回 (grad, fade_rough, streak, sangle)。"""
    if big <= 0:
        return grad, fade_rough, streak, sangle
    fade = kw.get('c_fade', True)          # 只认 c_fade（通用的 fade 是线的“沿笔画变淡”）
    ang_deg = float(fade) if isinstance(fade, (int, float)) and not isinstance(fade, bool) else 35.0
    if fade is not False and grad is None and rgrad is None:
        ang = math.radians(ang_deg)
        ux, uy = math.cos(ang), math.sin(ang)
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        half = 0.5 * (abs(ux) * bw + abs(uy) * bh)
        g1 = 1.0 - 0.8 * big
        grad = (cx - ux * half * 0.6, cy - uy * half * 0.6, cx + ux * half * 1.0, cy + uy * half * 1.0, 1.1, g1)
        if fade_rough is None:
            fade_rough = 0.15
    return grad, fade_rough, streak, sangle


def grad_map(x0, y0, ww, hh, grad=None, rgrad=None, rough=0.0, seed=0, sc=0.25):
    """线性/径向浓淡系数图（全尺寸 hh×ww），rough>0 时淡出边被噪声打碎。没有渐变时返回 None。"""
    if grad is None and rgrad is None:
        return None
    lh, lw = max(2, int(hh * sc)), max(2, int(ww * sc))
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    xx = x0 + (xx + 0.5) / sc
    yy = y0 + (yy + 0.5) / sc
    cell = float(np.clip(0.12 * math.sqrt(hh * ww), 30.0, 160.0))
    n = vnoise(lh, lw, cell * sc, sd(seed, 61), 2) if rough > 0 else 0.0
    g = np.ones((lh, lw), np.float32)
    if grad is not None:
        gx0, gy0, gx1, gy1, g0, g1 = grad
        vx, vy = gx1 - gx0, gy1 - gy0
        tt = ((xx - gx0) * vx + (yy - gy0) * vy) / (vx * vx + vy * vy + 1e-6) + rough * n
        g *= g0 + (g1 - g0) * smooth01(tt)
    if rgrad is not None:
        cx, cy, r0, r1, g0, g1 = rgrad
        rr = (np.hypot(xx - cx, yy - cy) - r0) / (r1 - r0 + 1e-6) + rough * n
        g *= g0 + (g1 - g0) * smooth01(rr)
    return cv2.resize(g, (ww, hh), interpolation=cv2.INTER_LINEAR)


def broad_strokes(x0, y0, ww, hh, seed, d, angle=0.0, boil=1.0, sc=0.5):
    """在 (x0,y0,ww,hh) 里铺几道大笔横扫：干笔、笔毫纹、写到头变淡变干（旧示意图窗外夜空的画法）。
    半分辨率画完再放大（大笔本来就软）。返回 hh×ww 的密度图（约 0..1）。"""
    a = math.radians(angle)
    v = np.float32([math.cos(a), math.sin(a)])
    nv = np.float32([-v[1], v[0]])
    cx, cy = ww / 2.0, hh / 2.0
    cs = np.float32([(-cx, -cy), (cx, -cy), (-cx, cy), (cx, cy)])
    al = cs @ v
    ac = cs @ nv
    a0, a1 = float(al.min()), float(al.max())
    c0, c1 = float(ac.min()), float(ac.max())
    span = c1 - c0
    sp = float(np.clip(span / 3.2, 46.0, 170.0))
    sw, shh = max(4, int(math.ceil(ww * sc))), max(4, int(math.ceil(hh * sc)))
    acc = np.zeros((shh, sw), np.float32)
    r = rng(seed, 'broad')
    off = c0 + sp * r.uniform(0.25, 0.5)
    k = 0
    while off < c1 + sp * 0.2 and k < 24:
        frac = r.uniform(0.6, 1.05)
        s0 = a0 - 30.0
        s1 = s0 + (a1 - a0 + 60.0) * frac
        ts = np.linspace(s0, s1, 3)
        perp = off + np.float32([r.normal(0, sp * 0.06), r.normal(0, sp * 0.12), r.normal(0, sp * 0.06)])
        pts = (np.float32([cx, cy])[None] + ts[:, None] * v[None] + perp[:, None] * nv[None]) * sc
        res = stroke(None, pts, sp * 1.35 * r.uniform(0.9, 1.1) * sc, ink=r.uniform(0.7, 0.95), ch='I',
                     seed=sd(seed, 'b', k), d=d, boil=boil * sc, taper=(0.0, 0.10), head=0.0,
                     dry=r.uniform(0.45, 0.75), dry_from=r.uniform(0.45, 0.75), streak=0.32, fade=0.3,
                     rag=3.0 * sc, soft=9.0 * sc, wn=0.08, out='mask')
        if res is not None:
            a, gx, gy = res
            c = Sheet(0, 0, sw, shh).clip(gx, gy, gx + a.shape[1], gy + a.shape[0])
            if c is not None:
                x0_, y0_, x1_, y1_ = c
                sub = acc[y0_:y1_, x0_:x1_]
                aa = a[y0_ - gy:y1_ - gy, x0_ - gx:x1_ - gx]
                sub += aa - sub * aa          # 叠笔像重新润湿：屏幕式合并，不会在交叠处黑成一条
        off += sp * r.uniform(0.85, 1.1)
        k += 1
    return cv2.resize(acc, (ww, hh), interpolation=cv2.INTER_LINEAR)


def _broad_overlay(sh, kw, chans, weight, grad, rgrad, fade_rough, seed, d, boil, bw, bh):
    """大面积 fill/shade 的大笔横扫层：broad_strokes × 区域遮罩 × 浓淡渐变。"""
    if weight <= 0.02:
        return
    r = _region(kw, 2.0, 4.0)
    if r is None:
        return
    m, x0, y0 = r
    hh, ww = m.shape
    ang = _hint(kw, 'sangle', None)
    ang = (2.0 if bw >= bh * 0.8 else 88.0) if ang is None else float(ang)
    f = broad_strokes(x0, y0, ww, hh, sd(seed, 'broad'), d, ang, boil)
    g = grad_map(x0, y0, ww, hh, grad, rgrad, fade_rough or 0.0, seed)
    f = f * m * weight
    if g is not None:
        f = f * g
    for k, v in chans.items():
        sh.add(k, (f * v).astype(np.float32), x0, y0)


_BG = {}            # 静态背景缓存（进程内）：('C', cache) → 合成完第一层后的整幅画层
_BG_MAX = 9


class BrushC:
    """C 水墨炭笔笔刷。"""
    key = 'C'

    def __init__(self):
        self.pp = pp()

    # ------------------------------------------------------------------ 纸
    def paper(self):
        return self.pp['rgb'].copy()

    # ------------------------------------------------------------------ 渲染
    def render(self, ops, d):
        boxes, ends = _group_boxes(ops)
        root = Sheet()
        cur = root
        stack = []
        save_key = None
        i = 0
        n = len(ops)
        dd = d
        while i < n:
            kind, kw = ops[i]
            if kind == 'group':
                cache = kw.get('cache')
                if i == 0 and cache is not None and kw.get('depth', 0) == 0 and i in ends:
                    try:
                        ckey = ('C',) + tuple(cache)
                        hash(ckey)
                    except TypeError:
                        ckey = None
                    if ckey is not None:
                        if ckey in _BG:
                            root = _BG[ckey].copy()
                            cur = root
                            i = ends[i] + 1
                            continue
                        save_key = ckey
                bb = boxes.get(i)
                sh = Sheet(*bb) if bb is not None else Sheet(0, 0, 1, 1)
                stack.append((cur, kw, dd, i))
                if i == 0 and save_key is not None:
                    # 缓存层用由缓存键决定的固定绘制序号（多进程渲染时三张循环也一致）
                    dd = sd('bgcache', *[str(c) for c in cache]) & 0xFFFF
                cur = sh
            elif kind == 'end':
                if stack:
                    parent, gkw, pdd, gi = stack.pop()
                    knock = gkw.get('knock', True)
                    bleed = gkw.get('bleed')
                    bleed = float(_hint(gkw, 'bleed', None) if gkw.get('c_bleed') is not None else
                                  (bleed if bleed is not None else (1.0 if knock else 0.7)))
                    gain = float(gkw.get('c_gain', 0.66 if knock else 0.5))
                    composite(parent, cur, bleed=bleed, gain=gain, opacity=float(gkw.get('opacity', 1.0)),
                              knock=knock)
                    cur = parent
                    dd = pdd
                    if gi == 0 and save_key is not None:
                        if len(_BG) >= _BG_MAX:
                            _BG.pop(next(iter(_BG)))
                        _BG[save_key] = root.copy()
                        save_key = None
            else:
                try:
                    getattr(self, '_' + kind)(cur, kw, dd)
                except AttributeError:
                    pass
            i += 1
        while stack:     # 没配对的 group：照样合成
            parent, gkw, pdd, gi = stack.pop()
            composite(parent, cur, bleed=1.0, gain=0.66, opacity=float(gkw.get('opacity', 1.0)),
                      knock=gkw.get('knock', True))
            cur = parent
        return to_rgb(root)

    # ------------------------------------------------------------------ 遮挡
    def _cover(self, sh, kw, d):
        amount = float(kw.get('amount', 1.0))
        feather = float(kw.get('feather', 1.0))
        if kw.get('mask') is not None:
            r = _region(kw, 2.0, feather * 0.8)
            if r is None:
                return
            m, x0, y0 = r
            cover_mask(sh, np.clip(m * 1.3, 0, 1), x0, y0, amount)
        else:
            cover_poly(sh, kw['polys'], seed=kw['seed'], d=d, feather=feather, amount=amount,
                       jit=float(kw.get('jit', 0.0)) * BOIL_K, holes=kw.get('holes', ()))

    # ------------------------------------------------------------------ 固有色
    def _fill(self, sh, kw, d):
        col = kw['color']
        seed = kw['seed']
        boil = kw['boil'] * BOIL_K
        tone = kw.get('tone')
        if col['red']:
            r_d, i_d = red_split(col['rgb'])
            k = 1.0 if tone is None else float(tone) / 0.9
            chans = {'R': r_d * k * float(_hint(kw, 'red', 1.0)), 'I': i_d * k}
            big = 0.0
        else:
            if kw.get('c_dens') is not None:
                dens = float(kw['c_dens'])
            else:
                t = tone if tone is not None else (col['tone'] if col.get('tone') is not None else luma_tone(col['rgb']))
                dens = tone_to_dens(t) * float(_hint(kw, 'ink', 1.0))
            if col.get('name') == 'blush':
                dens *= 0.35         # 水墨里没有腮红：只留一点点体温
            chans = {'I': dens}
            big = None
        if max(chans.values()) < 0.004:
            # 留白的固有色（亮着的窗、雪、太阳、米白毛衣…）：水墨里就是纸——把此处之前的墨提干净
            if not col['red'] and core.luma(col['rgb']) > 0.72 and _hint(kw, 'blank', True) is not False:
                r = _region(kw, 2.0, float(_hint(kw, 'soft', 1.2)))
                if r is not None:
                    m, x0, y0 = r
                    sh.erase(np.clip(m * 1.15, 0, 1), x0, y0, float(_hint(kw, 'amt', 0.92)))
            return
        # 区域大小
        if kw.get('mask') is not None:
            m = kw['mask'][0]
            bw, bh = m.shape[1], m.shape[0]
            bx = (kw['mask'][1], kw['mask'][2], kw['mask'][1] + bw, kw['mask'][2] + bh)
        else:
            polys = as_polys(kw.get('polys'))
            if not polys:
                return
            bx = bbox_of(polys)
            bw, bh = bx[2] - bx[0], bx[3] - bx[1]
        area = max(1.0, bw * bh)
        frac = area / float(W * H)
        grad, rgrad = kw.get('grad'), kw.get('rgrad')
        fade_rough = _hint(kw, 'fade_rough', None)
        streak = _hint(kw, 'streak', None)
        sangle = _hint(kw, 'sangle', None)
        if sangle is None and streak and 'hair' in str(col.get('name') or ''):
            sangle = 80.0          # 头发的笔痕顺着发流（竖向），不是横扫
        if big is None:
            # 大面积固有色：水墨不会平涂满一大块——整体淡一些，用大笔横扫（笔痕代替斑驳），
            # 并且“画到一半就停”（向一侧淡出到纸）。c_fade=False 关掉，c_fade=角度 改淡出方向。
            big = float(sstep(0.03, 0.30, frac))
            grad, fade_rough, streak, sangle = _big_area(kw, bx, bw, bh, big, grad, rgrad, fade_rough, streak,
                                                         sangle)
            chans = {k: v * (1.0 - 0.25 * big) for k, v in chans.items()}
            bwt = float(smooth01((big - 0.15) / 0.5)) if _hint(kw, 'broad', True) is not False else 0.0
            if bwt > 0:
                _broad_overlay(sh, kw, chans, 0.6 * bwt, grad, rgrad, fade_rough if fade_rough is not None else 0.3,
                               seed, d, boil, bw, bh)
                chans = {k: v * (1.0 - 0.45 * bwt) for k, v in chans.items()}
        if (grad is None and rgrad is None and not col['red'] and _hint(kw, 'grad_auto', True) is not False
                and 1200 < area):
            # 手工上色不会一样平：一侧浓一侧淡（方向由 seed 定，左右为主），淡的一侧被水冲开
            rr = rng(seed, 'lat')
            ang = math.radians((0.0 if rr.random() < 0.5 else 180.0) + rr.normal(0, 18))
            ux, uy = math.cos(ang), math.sin(ang)
            cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
            half = 0.5 * (abs(ux) * bw + abs(uy) * bh)
            grad = (cx - ux * half, cy - uy * half, cx + ux * half, cy + uy * half, 1.25, 0.62)
            if fade_rough is None:
                fade_rough = 0.18
        if fade_rough is None:
            fade_rough = 0.25 if (grad is not None or rgrad is not None) else 0.0
        dens_max = max(chans.values())
        soft = float(_hint(kw, 'soft', 1.8 if area < 40000 else 2.6))
        sc = 1.0 if area < 90000 else 0.5
        cell = float(_hint(kw, 'cell', float(np.clip(math.sqrt(area) / 6.0, 8.0, 40.0 + 80.0 * big))))
        bloom = float(_hint(kw, 'bloom', (0.3 if dens_max > 0.18 else 0.0) * (1.0 - big)))
        rim = float(_hint(kw, 'rim', 0.30 if dens_max > 0.03 else 0.15))
        wash(sh, kw.get('polys'), seed=seed, d=d, soft=soft, rough=float(_hint(kw, 'rough', 0.15)), cell=cell,
             var=float(_hint(kw, 'var', 0.26 * (1.0 - 0.55 * big))), rim=rim, grad=grad, rgrad=rgrad, sc=sc, jit=boil,
             drift=float(_hint(kw, 'drift', 0.15 * (1.0 - 0.6 * big))), holes=kw.get('holes', ()),
             offset=kw.get('offset') or (0, 0), bloom=bloom, fade_rough=float(fade_rough),
             streak=float(streak or 0.0), sangle=float(sangle or 0.0), edge=float(_hint(kw, 'edge', 2.4)),
             mask=self._mask_arg(kw), chans=chans)

    @staticmethod
    def _mask_arg(kw):
        if kw.get('mask') is None:
            return None
        r = core.region_mask(kw, 0)
        return r

    # ------------------------------------------------------------------ 体积阴影
    def _shade(self, sh, kw, d):
        amount = float(kw.get('amount', 0.3))
        if amount <= 0:
            return
        seed = kw['seed']
        boil = kw['boil'] * BOIL_K
        col = kw.get('color')
        polys = kw.get('polys')
        if kw.get('mask') is None and not as_polys(polys):
            return
        grad, rgrad = kw.get('grad'), kw.get('rgrad')
        cname = str(col.get('name') or '') if col is not None else ''
        do_hatch = _hint(kw, 'hatch', True) is not False
        if col is not None and col.get('red'):
            r_d, i_d = red_split(col['rgb'])
            chans = {'R': r_d * amount * 0.8, 'I': i_d * amount * 0.8}
            do_hatch = False
        elif cname == 'graphite':
            # 石墨蹭开的灰（橡皮擦过的地方）：只有炭笔通道，不排线
            chans = {'C': amount * 0.9 * float(_hint(kw, 'ink', 1.0))}
            do_hatch = False
        elif cname.startswith('skin') or cname in ('blush', 'lips'):
            # 皮肤上的影：只有极淡的墨晕（脸上不排线，否则显脏）
            chans = {'I': amount * 0.30 * float(_hint(kw, 'ink', 1.0))}
            do_hatch = _hint(kw, 'hatch', False) is True
        else:
            chans = {'I': amount * 0.42 * float(_hint(kw, 'ink', 1.0))}
        if kw.get('mask') is not None:
            m = kw['mask'][0]
            bw, bh = m.shape[1], m.shape[0]
            bx = (kw['mask'][1], kw['mask'][2], kw['mask'][1] + bw, kw['mask'][2] + bh)
        else:
            bx = bbox_of(as_polys(polys))
            bw, bh = bx[2] - bx[0], bx[3] - bx[1]
        area = max(1.0, bw * bh)
        big = float(sstep(0.03, 0.30, area / float(W * H)))
        fade_rough = _hint(kw, 'fade_rough', None)
        grad, fade_rough, streak, sangle = _big_area(kw, bx, bw, bh, big, grad, rgrad, fade_rough,
                                                     _hint(kw, 'streak', None), _hint(kw, 'sangle', None))
        if fade_rough is None:
            fade_rough = 0.3 if (grad is not None or rgrad is not None) else 0.0
        chans = {k: v * (1.0 - 0.55 * big) for k, v in chans.items()}
        bwt = float(smooth01((big - 0.15) / 0.5)) if _hint(kw, 'broad', True) is not False else 0.0
        if bwt > 0:
            _broad_overlay(sh, kw, chans, 0.7 * bwt, grad, rgrad, fade_rough, sd(seed, 'shade'), d, boil, bw, bh)
            chans = {k: v * (1.0 - 0.5 * bwt) for k, v in chans.items()}
            streak = 0.0
        sc = 1.0 if area < 90000 else 0.5
        wash(sh, polys, seed=sd(seed, 'shade'), d=d, soft=float(_hint(kw, 'soft', 5.0)),
             rough=float(_hint(kw, 'rough', 0.35)), cell=float(np.clip(math.sqrt(area) / 5, 10, 40 + 80 * big)),
             var=0.3 * (1.0 - 0.6 * big), rim=float(_hint(kw, 'rim', 0.22)), grad=grad, rgrad=rgrad, sc=sc,
             jit=boil * 0.6, drift=0.15 * (1.0 - 0.6 * big), holes=kw.get('holes', ()),
             offset=kw.get('offset') or (1, 1), bloom=float(_hint(kw, 'bloom', 0.3 * (1.0 - big))),
             fade_rough=float(fade_rough), streak=float(streak or 0.0), sangle=float(sangle or 0.0),
             mask=self._mask_arg(kw), chans=chans)
        if do_hatch and big < 0.95:
            ang = kw.get('angle')
            ang = 65.0 if ang is None else float(ang)
            r = _region(kw, 6.0, 3.0)
            if r is None:
                return
            m, x0, y0 = r
            # 大面积的阴影只在浓的一端排几道线（排线也“画到一半就停”）
            hatch_region(sh, m, x0, y0, ang, float(_hint(kw, 'spacing', 7.0)), dens=amount * 0.55 * (1 - big),
                         ch='C', seed=sd(seed, 'shade_h'), d=d, boil=boil * 0.5, partial=0.3 + 0.25 * big, grad=grad)

    # ------------------------------------------------------------------ 线
    def _line(self, sh, kw, d):
        pts = np.asarray(kw['pts'], np.float32).reshape(-1, 2)
        if len(pts) < 2:
            return
        role = kw.get('role', 'contour')
        w = float(kw['w']) * float(_hint(kw, 'wk', 1.0))
        tone = float(kw.get('tone', 0.85))
        col = kw.get('color')
        seed = kw['seed']
        boil = kw['boil'] * BOIL_K
        closed = bool(kw.get('closed', False))
        taper = tuple(kw.get('taper') or (0.0, 0.0))
        if role in ('sketch', 'construct'):
            sketch = role == 'sketch'
            ch = 'R' if (col is not None and col.get('red')) else 'C'
            ink = tone * (1.3 if sketch else 0.85) * float(_hint(kw, 'ink', 1.0))
            sketch_line(sh, pts, w * (0.95 if sketch else 0.8), ink, seed, d, boil,
                        reps=int(_hint(kw, 'reps', 2 if sketch else 1)),
                        breaks=float(_hint(kw, 'breaks', 0.0)),
                        spread=float(_hint(kw, 'spread', 1.8 if sketch else 2.8)),
                        taper=(max(taper[0], 0.1), max(taper[1], 0.2)) if taper != (0.0, 0.0) else (0.1, 0.2),
                        closed=closed, ch=ch)
            return
        rp = ROLE.get(role, ROLE['contour'])
        ch = 'I'
        ink = tone * rp['ik']
        white = False
        if col is not None:
            if col.get('red'):
                ch = 'R'
                ink = tone * 1.45
            elif col.get('name') == 'graphite':
                ch = 'C'
                ink = tone * 1.2
            elif core.luma(col['rgb']) > 0.86 and col.get('name') not in ('ink',):
                white = True
        ink *= float(_hint(kw, 'ink', 1.0))
        wd = w * rp['wk']
        # 毛笔不会一笔画完一个方框：在尖角处断成几笔（每笔有自己的起笔和收笔，角上略出头）；
        # 闭合的圆滑曲线分成首尾相搭的两笔。这样也避免同一笔自己重叠造成的笔毫纹错乱。
        split = _hint(kw, 'split', True) is not False and role != 'feature'
        pieces = _split_line(pts, wd, closed, split)
        drymul = float(np.clip((w - 1.5) / 3.0, 0.0, 1.0))      # 细线不飞白
        base = dict(w=wd, ink=ink, ch=ch, d=d, boil=boil,
                    head=float(_hint(kw, 'head', rp['head'])), lift=float(_hint(kw, 'lift', rp['lift'])),
                    dry=float(_hint(kw, 'dry', rp['dry'] * drymul)),
                    dry_from=float(_hint(kw, 'dry_from', rp['dry_from'])),
                    streak=float(_hint(kw, 'streak', rp['streak'] * drymul)),
                    pool=float(_hint(kw, 'pool', rp['pool'])),
                    rag=float(_hint(kw, 'rag', rp['rag'])), wn=float(_hint(kw, 'wn', rp['wn'])),
                    fade=float(_hint(kw, 'fade', 0.0)), breaks=float(_hint(kw, 'breaks', 0.0)),
                    wetedge=float(_hint(kw, 'wetedge', 0.0)), soft=float(_hint(kw, 'edge_soft', 1.0)))
        multi = len(pieces) > 1
        for k, P in enumerate(pieces):
            Lp = float(np.sum(np.hypot(*np.diff(spline(P, 6.0), axis=0).T)))
            tp = (min(taper[0], 0.10), min(taper[1], 0.20)) if multi else taper
            t0 = min(tp[0], max(0.03, 80.0 / max(Lp, 1.0))) if tp[0] > 0 else 0.0
            t1 = min(tp[1], max(0.06, 220.0 / max(Lp, 1.0))) if tp[1] > 0 else 0.0
            args = dict(base, seed=sd(seed, 'pc', k) if k else seed, taper=(t0, t1))
            if multi and k:
                args['head'] = args['head'] * 0.8
            if white:
                r = stroke(None, P, out='mask', **args)
                if r is not None:
                    m, gx, gy = r
                    sh.erase(np.clip(m / max(ink, 1e-3), 0, 1), gx, gy, min(1.0, 0.9 * max(tone, 0.5) / 0.85))
                continue
            stroke(sh, P, **args)

    # ------------------------------------------------------------------ 排线
    def _hatch(self, sh, kw, d):
        r = _region(kw, 6.0, float(_hint(kw, 'soft', 3.0)))
        if r is None:
            return
        m, x0, y0 = r
        col = kw.get('color')
        ch = 'C'
        dens = float(kw.get('tone', 0.3)) * 0.85
        if col is not None:
            if col.get('red'):
                ch = 'R'
                dens = float(kw.get('tone', 0.3)) * 1.2
            elif col.get('name') not in (None, 'graphite', 'ink') and _hint(kw, 'ink_hatch', False):
                ch = 'I'
        hatch_region(sh, m, x0, y0, float(kw.get('angle', 45.0)), float(kw.get('spacing', 6.0)),
                     dens=dens * float(_hint(kw, 'ink', 1.0)), ch=ch, seed=kw['seed'], d=d,
                     boil=kw['boil'] * BOIL_K * 0.5, lw=int(_hint(kw, 'lw', 1)), partial=float(_hint(kw, 'partial', 0.4)),
                     bow=float(_hint(kw, 'bow', 0.03)), grad=kw.get('grad'))

    # ------------------------------------------------------------------ 点
    def _dot(self, sh, kw, d):
        x, y, rx, ry = kw['x'], kw['y'], kw['rx'], kw['ry']
        col = kw['color']
        tone = float(kw.get('tone', 0.9))
        seed = kw['seed']
        boil = kw['boil'] * BOIL_K * 0.4
        rot = float(kw.get('rot', 0.0))
        if col['red']:
            # 红豆：朱砂点 + 一点墨的暗部 + 高光留白
            r_d, i_d = red_split(col['rgb'])
            k = float(np.clip(tone / 0.9, 0.3, 1.4))
            dot(sh, x, y, rx, ry, ink=1.3 * k * r_d / 1.1, ch='R', seed=seed, d=d, boil=boil, rot=rot)
            if i_d > 0.02:
                dot(sh, x, y, rx, ry, ink=i_d * k, ch='I', seed=seed, d=d, boil=boil, rot=rot)
            if min(rx, ry) >= 1.6 and _hint(kw, 'shine', True):
                cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
                ox, oy = 0.22 * rx, 0.33 * ry
                dot(sh, x + ox * cr - oy * sr, y + ox * sr + oy * cr, rx * 0.73, ry * 0.6, ink=0.25 * k, ch='I',
                    seed=sd(seed, 2), d=d, boil=boil * 0.5, rot=rot)
                ox, oy = -0.3 * rx, -0.28 * ry
                a, gx, gy = dot_mask(x + ox * cr - oy * sr, y + ox * sr + oy * cr, max(0.6, rx * 0.27),
                                     max(0.5, ry * 0.25), seed=sd(seed, 3), d=d, boil=boil * 0.5, rot=rot)
                sh.mul('RI', 1.0 - 0.85 * a, gx, gy)
            if _hint(kw, 'shadow', False):
                a, gx, gy = dot_mask(x + 1, y + ry * 1.0, rx * 1.05, ry * 0.45, seed=sd(seed, 4), d=d,
                                     boil=boil * 0.5, rot=rot, soft=1.2)
                sh.add('I', a * 0.12, gx, gy)
            return
        light_col = core.luma(col['rgb']) > 0.86 and col.get('name') != 'ink'
        if tone < 0.02 or (light_col and tone < 0.2):
            # 雪、星、高光：留白（提白，同时挖开下面）
            a, gx, gy = dot_mask(x, y, rx, ry, seed, d, boil, rot, soft=float(_hint(kw, 'soft', 0.6)))
            sh.erase(a, gx, gy, float(_hint(kw, 'amt', 0.92)))
            return
        if tone < 0.2:
            # 很淡的点（腮红、水渍）：一抹若有若无的淡墨晕
            soft = float(_hint(kw, 'soft', max(1.5, 0.5 * min(rx, ry))))
            dot(sh, x, y, rx * 1.1, ry * 1.1, ink=tone * 0.42 * float(_hint(kw, 'ink', 1.0)), ch='I', seed=seed,
                d=d, boil=boil, rot=rot, soft=soft)
            return
        ch = 'C' if col.get('name') == 'graphite' else 'I'
        dot(sh, x, y, rx, ry, ink=tone * float(_hint(kw, 'ink', 1.0)), ch=ch, seed=seed, d=d, boil=boil, rot=rot,
            soft=float(_hint(kw, 'soft', 0.0)))

    # ------------------------------------------------------------------ 光 = 留白
    def _light(self, sh, kw, d):
        amt = float(kw.get('amt', 0.5))
        if amt <= 0:
            return
        r = glow_mask(kw['cx'], kw['cy'], kw['rx'], kw['ry'], seed=kw['seed'], d=d)
        if r is None:
            return
        g, x0, y0 = r
        a = np.clip(amt * g, 0, 1)
        sh.mul('IC', 1.0 - a, x0, y0)
        sh.add('A', a, x0, y0)

    # ------------------------------------------------------------------ 提白
    def _lift(self, sh, kw, d):
        r = _region(kw, 3.0, float(kw.get('soft', 2.0)))
        if r is None:
            return
        m, x0, y0 = r
        dry = float(_hint(kw, 'dry', 0.0))
        streak = float(_hint(kw, 'streak', 0.0))
        if (dry > 0 or streak > 0) and m.shape[0] > 3 and m.shape[1] > 3:
            # 干笔提白：顺着提白区域的长轴拉出丝丝的笔毫纹，干处断开
            mo = cv2.moments((m > 0.3).astype(np.uint8), True)
            ang = float(_hint(kw, 'angle', None) or
                        (0.5 * math.degrees(math.atan2(2 * mo['mu11'], mo['mu20'] - mo['mu02'] + 1e-9))
                         if mo['m00'] > 0 else 0.0))
            hh, ww = m.shape
            D = int(math.hypot(hh, ww)) + 4
            ns = vnoise(D, max(4, D // 10), 1.6, sd(kw['seed'], 'lift'), 2)      # 横向拉长 = 沿 0° 的丝
            ns = cv2.resize(ns, (D, D), interpolation=cv2.INTER_LINEAR)
            M = cv2.getRotationMatrix2D((D / 2, D / 2), -ang, 1.0)
            M[0, 2] += ww / 2 - D / 2
            M[1, 2] += hh / 2 - D / 2
            ns = cv2.warpAffine(ns, M, (ww, hh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ns = ns / (ns.std() + 1e-6)
            tex = np.clip(0.5 + 0.35 * ns, 0, 1)
            m = m * (1.0 - streak * (1.0 - tex))
            if dry > 0:
                m = m * np.clip((tex - 0.55 * dry) / 0.12 + 0.5, 0, 1) ** 0.5
        sh.erase(m, x0, y0, float(kw.get('amt', 1.0)))

    # ------------------------------------------------------------------ 歌词
    def paint_text(self, rgb, items, d, halo=0.86):
        """横排行楷：未唱 = 墨色（字边向纸纤维洇开）；唱到 = 红豆红从字心洇开；纸色柔光衬底保证可读。"""
        if not items:
            return rgb
        P = self.pp
        pad = 30
        X0 = max(0, min(it['x'] for it in items) - pad)
        Y0 = max(0, min(it['y'] for it in items) - pad)
        X1 = min(W, max(it['x'] + it['mask'].shape[1] for it in items) + pad)
        Y1 = min(H, max(it['y'] + it['mask'].shape[0] for it in items) + pad)
        if X1 <= X0 or Y1 <= Y0:
            return rgb
        hh, ww = Y1 - Y0, X1 - X0
        I = np.zeros((hh, ww), np.float32)
        R = np.zeros((hh, ww), np.float32)
        halo_m = np.zeros((hh, ww), np.float32)
        fib = P['fiber'][Y0:Y1, X0:X1]
        for it in items:
            m = it['mask']
            a_in = float(it.get('alpha', 1.0))
            if a_in <= 0.003:
                continue
            sung = float(it.get('sung', 0.0))
            jr = rng(500, it.get('line', 0), it.get('i', 0), d)
            fx, fy = 0.5 + jr.normal(0, 0.22), 0.5 + jr.normal(0, 0.22)
            M = np.float32([[1, 0, fx], [0, 1, fy]])
            mh, mw = m.shape
            mm = cv2.warpAffine(m, M, (mw + 1, mh + 1), flags=cv2.INTER_LINEAR)
            lx, ly = int(it['x']) - X0, int(it['y']) - Y0
            sy0, sx0 = max(0, -ly), max(0, -lx)
            ey, ex = min(mh + 1, hh - ly), min(mw + 1, ww - lx)
            if ey <= sy0 or ex <= sx0:
                continue
            ccy, ccx = (mh + 1) * 0.5, (mw + 1) * 0.5
            mm = mm[sy0:ey, sx0:ex]
            ry0, rx0 = ly + sy0, lx + sx0
            ry1, rx1 = ry0 + mm.shape[0], rx0 + mm.shape[1]
            # 洇墨：字边向纸纤维里渗一点
            bl = cv2.GaussianBlur(mm, (0, 0), 1.6)
            ink = np.maximum(mm, bl * (0.5 + 0.35 * fib[ry0:ry1, rx0:rx1])) * a_in
            if sung > 0:
                if sung < 1:
                    yy, xx = np.mgrid[sy0:ey, sx0:ex].astype(np.float32)
                    dist = np.hypot(xx - ccx, yy - ccy) / (0.5 * max(mh, mw))
                    rad = sung * 1.35
                    red_part = np.clip((rad - dist) / 0.22, 0, 1)
                else:
                    red_part = 1.0
                R[ry0:ry1, rx0:rx1] += ink * 1.0 * red_part
                I[ry0:ry1, rx0:rx1] += ink * 0.95 * (1 - red_part) + ink * 0.04 * red_part
            else:
                I[ry0:ry1, rx0:rx1] += ink * 0.95
            sub = halo_m[ry0:ry1, rx0:rx1]
            np.maximum(sub, mm * a_in, out=sub)
        hk = cv2.dilate(halo_m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        hk = cv2.GaussianBlur(hk, (0, 0), 13)
        hk = np.clip(hk * 1.6, 0, 1) * halo
        sub = rgb[Y0:Y1, X0:X1]
        sub += (P['rgb'][Y0:Y1, X0:X1] - sub) * hk[..., None]
        tau = I[..., None] * A_INK + R[..., None] * A_LYR
        sub *= np.exp(-tau)
        return rgb


# =========================================================================== 印章（片头片尾用）
_SEAL = {}


def seal_mask(w, h, text='红豆', seed=7):
    """朱文印/白文印：红底白字，印边粗糙，印泥不匀（有小白点）。返回朱砂密度图。
    字数 ≤3 竖排一列；4 字两列（从右往左读）。"""
    key = (int(w), int(h), text, seed)
    if key in _SEAL:
        return _SEAL[key]
    w, h = int(w), int(h)
    S = 4
    big = Image.new('L', (w * S, h * S), 0)
    r = rng(seed, 1)
    n = 40
    pts = []
    for i in range(n):
        tt = i / n
        if tt < 0.25:
            x, y = tt / 0.25, 0
        elif tt < 0.5:
            x, y = 1, (tt - 0.25) / 0.25
        elif tt < 0.75:
            x, y = 1 - (tt - 0.5) / 0.25, 1
        else:
            x, y = 0, 1 - (tt - 0.75) / 0.25
        pts.append(((0.04 + 0.92 * x) * w * S + r.normal(0, 0.9) * S,
                    (0.03 + 0.94 * y) * h * S + r.normal(0, 0.9) * S))
    dr = ImageDraw.Draw(big)
    dr.polygon(pts, fill=255)
    chars = [c for c in text if not c.isspace() and c not in '·・.']
    if len(chars) == 4:
        cols = [chars[:2], chars[2:]]
        fs = int(min(h * S * 0.40, w * S * 0.42))
        f = ImageFont.truetype(FONT_SEAL, max(8, fs))
        for ci, col in enumerate(cols):
            cx = (0.73 - 0.46 * ci) * w * S
            for i, ch in enumerate(col):
                dr.text((cx, (0.27 + 0.46 * i) * h * S), ch, font=f, fill=0, anchor='mm')
    elif chars:
        k = len(chars)
        step = 0.92 / k
        fs = int(min(h * S * step * 0.86, w * S * 0.78))
        f = ImageFont.truetype(FONT_SEAL, max(8, fs))
        for i, ch in enumerate(chars):
            dr.text((w * S * 0.5, (0.04 + step * (i + 0.5)) * h * S), ch, font=f, fill=0, anchor='mm')
    m = np.asarray(big, np.float32) / 255.0
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    nz = vnoise(h, w, 3.0, sd(seed, 2), 2)
    speck = (nz > 0.55).astype(np.float32)
    m = m * (1 - 0.75 * speck) * (0.86 + 0.14 * vnoise(h, w, 12, sd(seed, 3), 1))
    for _ in range(5):
        cx, cy = r.uniform(0, w), r.choice([r.uniform(0, 3), r.uniform(h - 3, h)])
        cv2.circle(m, (int(cx), int(cy)), int(r.uniform(1, 3)), 0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 0.5)
    _SEAL[key] = m.astype(np.float32)
    return _SEAL[key]


def seal(rgb, x, y, w=58, h=104, text='红豆', seed=7, dens=1.05, alpha=1.0):
    """在 rgb（float32 H×W×3，就地修改）的 (x, y) 处盖一方朱印，w×h 像素。alpha 用于淡入淡出。"""
    m = seal_mask(w, h, text, seed)
    r = core.clip_box(int(x), int(y), m.shape[1], m.shape[0])
    if r is None:
        return rgb
    sx0, sy0, dx0, dy0, ww, hh = r
    sub = rgb[dy0:dy0 + hh, dx0:dx0 + ww]
    sub *= np.exp(-(m[sy0:sy0 + hh, sx0:sx0 + ww] * dens * alpha)[..., None] * A_RED)
    return rgb
