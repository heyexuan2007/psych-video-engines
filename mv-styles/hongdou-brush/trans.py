# -*- coding: utf-8 -*-
"""
风格转场遮罩。每个函数返回 float32 H×W 的遮罩 m（0 = 旧风格，1 = 新风格），可选再返回一张“边缘”图，
合成器用它给新画面加一点材质上的过渡痕迹（水彩前沿的颜料堆积、冲刷的水痕等）。
所有噪声只用固定种子，进度 p 由绘制时间决定，所以遮罩逐帧连续、不闪。

  T1 bloom   水彩从一点（红豆）向外晕开，前沿不规则、带颜料堆积的深边
  T2 drain   颜色一块块、慢慢地流失（不是划过去的擦除），整体跟随进度
  T3 patches 油画棒逐拍涂块：第 k 拍把第 k 块区域用涂鸦笔触扫满
  T4 rinse   像被水从上往下冲淡：冲刷前沿带下淌的水痕
"""
import math
from functools import lru_cache

import cv2
import numpy as np

from core import W, H, vnoise, sd, smooth01, ease_io, ease_out, clamp

SC = 4                      # 遮罩先在 1/4 分辨率上算，再放大（又快又软）
w4, h4 = W // SC, H // SC


def _up(m):
    return cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)


@lru_cache(maxsize=8)
def _noise(seed, cell, octaves=3):
    n = vnoise(h4, w4, cell, sd(seed, 'tr'), octaves, 0.55)
    return (n / (np.abs(n).max() + 1e-6)).astype(np.float32)


@lru_cache(maxsize=4)
def _grid():
    yy, xx = np.mgrid[0:h4, 0:w4].astype(np.float32)
    return xx * SC, yy * SC


# --------------------------------------------------------------------------- T1 水彩晕开
def bloom(p, center, seed=11, soft=26.0):
    """p 0..1。center=(x,y) 晕开的起点（屏幕坐标，例如碗里的红豆）。→ (m, edge)。
    前沿 = 半径随进度增长的不规则圆：低频噪声决定大轮廓，中频噪声做出“菜花状”水渍边。"""
    xx, yy = _grid()
    cx, cy = center
    dist = np.hypot(xx - cx, yy - cy)
    far = float(max(np.hypot(cx - x, cy - y) for x in (0, W) for y in (0, H)))
    # 水彩晕开：开头略快、后面慢慢渗到边角（整个过程都看得见在扩散）
    R = (far * 1.18 + 60) * (1 - (1 - clamp(p)) ** 1.3)
    n = 0.20 * _noise(seed, 48) + 0.08 * _noise(seed + 1, 14)
    front = R * (1 + n) - dist
    m = smooth01(front / soft * 0.5 + 0.5)
    # 前沿的颜料堆积（新画面一侧边缘略深）
    edge = np.exp(-((front - soft * 0.6) / (soft * 0.9)) ** 2) * (1 - clamp(p) ** 3)
    return _up(m), _up(edge)


# --------------------------------------------------------------------------- T2 慢慢褪色
def drain(p, seed=23):
    """p 0..1。颜色一块块流失：低频噪声决定哪里先褪，但整体紧跟进度（不会出现明显的擦除边）。"""
    n = 0.5 * _noise(seed, 90) + 0.25 * _noise(seed + 1, 30)
    q = ease_io(p)
    m = np.clip((q * 1.6 - 0.3) + 0.45 * n, 0, 1)
    m = smooth01(m)
    return _up(m), None


# --------------------------------------------------------------------------- T3 油画棒逐拍涂块
def patches(beats, regions, seed=37, angles=None):
    """beats：从转场开始算的拍数（0..len(regions)，可为小数）。regions：按涂的顺序给出的全画面 float 遮罩（H×W 或 1/4 分辨率），
    最后一块之后剩下没被任何区域覆盖的地方也会在最后一拍涂满。
    第 k 拍内（beats ∈ [k, k+1)），第 k 块区域被一道道来回的涂鸦笔触扫满（沿 angles[k] 方向推进）。→ (m, edge)。"""
    n = len(regions)
    xx, yy = _grid()
    m = np.zeros((h4, w4), np.float32)
    edge = np.zeros((h4, w4), np.float32)
    covered = np.zeros((h4, w4), np.float32)
    for k in range(n):
        R = regions[k]
        if R.shape != (h4, w4):
            R = cv2.resize(R.astype(np.float32), (w4, h4), interpolation=cv2.INTER_AREA)
        R = np.clip(R - covered, 0, 1) if k < n - 1 else np.clip(1 - covered, 0, 1)   # 最后一块兜底
        covered = np.maximum(covered, R)
        u = clamp(beats - k)
        if u <= 0:
            continue
        if u >= 1:
            m = np.clip(m + R, 0, 1)
            continue
        a = math.radians(angles[k] if angles else (k * 67) % 180)
        # 推进坐标：区域内沿方向 a 从一头扫到另一头
        s = xx * math.cos(a) + yy * math.sin(a)
        ys, xs = np.nonzero(R > 0.5)
        if len(xs) == 0:
            continue
        sv = s[ys, xs]
        s0, s1 = float(sv.min()), float(sv.max())
        sn = (s - s0) / (s1 - s0 + 1e-6)
        # 涂鸦：斜着的一道道蜡笔笔触（与推进方向成 70°），两种宽度的笔触叠在一起，
        # 每道伸出去的长度不同 → 前沿是参差、倾斜的笔触末端，而不是一排整齐的竖条
        b = a + math.radians(70)
        tcoord = -xx * math.sin(b) + yy * math.cos(b)
        def _bands(w, salt):
            band = np.floor(tcoord / w)
            return np.modf(np.abs(np.sin(band * 12.9898 + salt * 78.233 + k * 3.17)) * 43758.5453)[0]
        rag = 0.6 * _bands(17.0, 1) + 0.4 * _bands(7.0, 2)
        front = (0.04 + 1.12 * u) - sn + 0.10 * (rag - 0.5) + 0.025 * _noise(seed + k, 10)
        mk = smooth01(front / 0.035) * R
        m = np.clip(m + mk, 0, 1)          # 各块互不重叠，相加不会在交界留缝
        edge = np.maximum(edge, np.exp(-(front / 0.03) ** 2) * R)
    return _up(m), _up(edge)


# --------------------------------------------------------------------------- T4 被水冲淡
def rinse(p, seed=51):
    """p 0..1。冲刷前沿从上往下，横向有起伏，前面有几道先流下去的水痕。→ (m, edge)。"""
    xx, yy = _grid()
    q = ease_io(p)
    nx = _noise(seed, 70)[h4 // 2]                           # 每一列的前沿起伏
    drip = np.clip(_noise(seed + 1, 6)[h4 // 3], 0, 1) ** 2  # 先流下去的水痕
    front_y = (-0.15 + 1.35 * q) * H + 90 * nx + 260 * drip * math.sin(math.pi * clamp(q * 1.2))
    front = front_y[None, :] - yy
    m = smooth01(front / 40.0 * 0.5 + 0.5)
    edge = np.exp(-((front - 20) / 30.0) ** 2) * (1 - q)
    return _up(m), _up(edge)


def region_from_polys(polys):
    """多边形 → 1/4 分辨率区域遮罩（给 patches 用）。"""
    m = np.zeros((h4, w4), np.uint8)
    for P in polys:
        P = np.asarray(P, np.float32) / SC
        cv2.fillPoly(m, [np.round(P * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255.0
