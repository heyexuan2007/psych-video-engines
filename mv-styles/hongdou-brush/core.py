# -*- coding: utf-8 -*-
"""
《红豆》手绘版 · 统一引擎核心：一套场景和人物，三种笔刷。

━━ 总体结构 ━━
  场景 / 人物只通过 Pen（本文件）作画。Pen 不直接画像素，而是把每次调用录成一条指令（op），
  得到一个与笔刷无关的指令列表 pen.ops。
  笔刷 brush_c.py（水墨炭笔）、brush_a.py（彩铅水彩）、brush_b.py（油画棒）各自实现
      Brush.render(ops, d) -> float32 H×W×3（0..1 线性 sRGB 值，直接 ×255 输出）
  转场 = 同一帧两种笔刷各渲染一遍，再用 transition 遮罩混合。
  人物、场景、动作只定义一次；风格只决定“用什么材质画”，不决定“画什么形状”。
  例外：场景可以按 pen.style 改变内容（例如“他”在 C 里是铅笔草稿，在 A/B 里是上色完成的人），
  但同一个东西在不同笔刷下的几何（位置、轮廓、比例）必须相同。

━━ 坐标与时间 ━━
  画面 1920×1080，像素坐标，y 向下。镜头推拉在笔刷渲染之后由 camera() 统一做（两种笔刷用同一个镜头）。
  成片时间 clip_t（0 … CUT_LEN），原曲时间 song_t = CUT_START + clip_t。
  逐帧手绘：输出 24fps，画面一拍二。绘制序号 d = floor(clip_t * 12)。所有随机抖动以 (seed, d) 为种子，
  同一 d 的两帧完全相同。动画时间统一取 draw_time(d)（该绘制格的中点）。

━━ Pen 指令（场景作者用）━━
  所有指令都带 seed（元素 id，整数或字符串，决定该元素的固定随机形态）；抖动幅度 boil 不写时继承当前 group 的 boil。
  颜色 color 用调色板名字（PAL 里的键，推荐）或 RGB 元组/十六进制串。红色系（PAL 里 red=True 的，如 'bean'）
  在任何笔刷下都保持红色——这是全片的视觉线索。

  with pen.group(name, boil=1.0, opacity=1.0, knock=True, bleed=None, cache=None): ...
        画层。按顺序从后往前叠。knock=False 表示透明叠加、不挡住后面（如铅笔草稿的“他”）；opacity 整层透明度。
        cache=(场景名, 变体) 时，笔刷可以缓存这一层的渲染结果（只允许用在最底层的静态背景上，且必须是第一个 group）。
        bleed 只是给水墨笔刷的提示（画层合成时向纸纤维洇开的程度）。
  pen.cover(polys | mask=(m,x0,y0), feather=1.0, amount=1.0, jit=0.0)
        不透明遮挡：此处之前画的东西被挡住，回到纸面（画家算法）。每个实体物件一般先 cover 自己的剪影再上色。
  pen.fill(polys | mask, color, tone=None, holes=(), grad=None, rgrad=None, offset=None, **hints)
        固有色区域（物体本身的颜色）。tone 可选，强制水墨笔刷的墨色浓度（0 留白 … 1 焦墨）；不写就由笔刷按颜色明度换算。
        grad=(x0,y0,x1,y1,g0,g1) 线性浓淡；rgrad=(cx,cy,r0,r1,g0,g1) 径向浓淡。
  pen.shade(polys | mask, amount=0.3, color=None, grad=None, angle=None, **hints)
        体积阴影：在已有颜色上压暗（水墨=墨晕+排线，水彩=冷色罩染，油画棒=深色叠涂）。angle 是建议的排线方向（度）。
  pen.line(pts, w, tone=0.85, color=None, closed=False, taper=(0.12, 0.30), role='contour', **hints)
        线。pts 是控制点（会被 Catmull-Rom 平滑）；w 是“毛笔笔肚”宽度（像素），各笔刷按自身材质换算成实际线宽。
        role: 'contour' 外轮廓 / 'detail' 内部细节线 / 'feature' 五官 / 'sketch' 铅笔草稿线 / 'construct' 起形辅助线。
        color 不写 = 笔刷默认线色；红色物件的线可以写 color='bean'。
  pen.hatch(polys | mask, angle, spacing, tone=0.3, color=None, grad=None, **hints)   质感排线（角度为线的方向，度）
  pen.dot(x, y, rx, ry=None, color='ink', tone=0.9, rot=0.0, **hints)                  点（豆子、眼珠、雪花…）
  pen.light(cx, cy, rx, ry=None, amt=0.5, color='lamp', **hints)                       光（水墨=提白留纸，水彩/油画棒=暖光）
  pen.lift(polys | mask, amt=1.0, soft=2.0, **hints)                                   提白/擦除（回到纸色的程度 amt）
  **hints：写给某种笔刷的可选参数，笔刷不认识的提示一律忽略。约定前缀：
        通用：dry 飞白/干笔 0..1、head 起笔顿、lift 行笔提、fade 沿笔画变淡、streak 笔毫纹、pool 起笔积墨、
              breaks 断线 0..1、reps 草稿重复描几遍、spread 重复线的离散、rough/bloom/rim/soft 晕染边缘、jit 轮廓抖动
        c_xxx / a_xxx / b_xxx 只给对应笔刷。

━━ 笔刷约定（笔刷作者用）━━
  class Brush:
      key = 'A' | 'B' | 'C'
      def render(self, ops, d) -> np.ndarray      # float32 H×W×3
      def paint_text(self, rgb, items, d) -> rgb  # 歌词（items 来自 lyric_items），就地画到 rgb 上并返回
      def paper(self) -> np.ndarray               # 这种笔刷的空白纸（float32 H×W×3）
  遍历 ops：('group', kw) ('end', {}) ('cover', kw) ('fill', kw) ('shade', kw) ('line', kw) ('hatch', kw) ('dot', kw)
  ('light', kw) ('lift', kw)。kw 里已经解析好：seed（整数）、boil（数值）、color（规范化成 color_spec 字典，见 resolve_color）。
  抖动幅度 = kw['boil'] × 笔刷自己的系数（油画棒可以大一些），抖动种子 = (seed, d)。
"""
import math
import os
import zlib
from contextlib import contextmanager

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# =========================================================================== 常量
W, H = 1920, 1080
FPS = 24
DRAW_RATE = 12
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
ASSETS = os.path.join(ROOT, 'assets')
SONG = os.path.join(ASSETS, 'song.wav')       # 自己放入歌曲音频（仓库不附带）
LRC = os.path.join(ASSETS, 'demo.lrc')        # 换成你自己的逐字 LRC
CACHE_DIR = os.path.join(HERE, '_cache')
FONT_DIR = r'C:/Windows/Fonts'
FONT_LYRIC = os.path.join(FONT_DIR, 'STXINGKA.TTF')    # 华文行楷（全片统一）
FONT_LABEL = os.path.join(FONT_DIR, 'STKAITI.TTF')

# 成片 = 原曲 103.95 → 183.60
CUT_START = 103.95
CUT_END = 183.60
CUT_LEN = CUT_END - CUT_START           # 79.65
PIC_FADE = (182.43 - CUT_START, CUT_LEN)    # 画面淡黑（成片时间）
AUDIO_FADE = (181.10 - CUT_START, 2.5)      # 音频淡出起点、时长

# 节拍：112 BPM，原曲拍点 = 0.36 + n × BEAT
BPM = 112.0
BEAT = 0.5355          # 用户时间轴文档实测值（60/112 会在 200 多拍后漂 0.05 秒）
BEAT0 = 0.36


def beat_song(n):
    return BEAT0 + n * BEAT


def beat_index(song_t):
    return (song_t - BEAT0) / BEAT


def song_t(clip_t):
    return CUT_START + clip_t


def clip_t(song_t_):
    return song_t_ - CUT_START


def draw_index(ct):
    """成片时间 → 绘制序号（一拍二）。"""
    return int(math.floor(ct * DRAW_RATE + 1e-6))


def draw_time(d):
    """绘制序号 → 该格中点的成片时间。"""
    return (d + 0.5) / DRAW_RATE


# 风格时间轴（成片时间）。kind: 'style' 纯风格；'trans' 转场（from→to，mask 形状）
TIMELINE = [
    dict(kind='style', style='C', t0=0.00, t1=16.36),
    dict(kind='trans', a='C', b='A', t0=16.36, t1=17.43, mask='bloom'),     # T1 水彩从红豆处晕开（2 拍）
    dict(kind='style', style='A', t0=17.43, t1=26.00),
    dict(kind='trans', a='A', b='C', t0=26.00, t1=30.28, mask='drain'),     # T2 慢慢褪色（8 拍）
    dict(kind='style', style='C', t0=30.28, t1=61.88),
    dict(kind='trans', a='C', b='B', t0=61.88, t1=66.17, mask='patches'),   # T3 油画棒逐拍涂块（8 拍）
    dict(kind='style', style='B', t0=66.17, t1=73.12),
    dict(kind='trans', a='B', b='C', t0=73.12, t1=75.27, mask='rinse'),     # T4 像被水冲淡（4 拍）
    dict(kind='style', style='C', t0=75.27, t1=CUT_LEN),
]


def style_at(ct):
    """→ (样式段 dict, 段内进度 0..1)。"""
    for seg in TIMELINE:
        if seg['t0'] <= ct < seg['t1']:
            return seg, (ct - seg['t0']) / (seg['t1'] - seg['t0'])
    return TIMELINE[-1], 1.0


# =========================================================================== 随机 / 缓动
def sd(*xs):
    """把 (元素id, 绘制序号, ...) 混成 32 位种子；字符串用 crc32，跨进程可复现。"""
    h = 0x811C9DC5
    for x in xs:
        if isinstance(x, str):
            x = zlib.crc32(x.encode('utf-8'))
        x = int(x) & 0xFFFFFFFF
        for k in range(4):
            h ^= (x >> (8 * k)) & 0xFF
            h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def rng(*xs):
    return np.random.default_rng(sd(*xs))


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def sstep(a, b, x):
    return smooth01((np.asarray(x, np.float32) - a) / (b - a + 1e-9))


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def lerp(a, b, t):
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def vnoise(h, w, cell, seed, octaves=2, persist=0.5):
    """值噪声：随机小网格三次插值放大，多倍频叠加。float32，均值≈0，std≈0.5。"""
    h, w = max(1, int(h)), max(1, int(w))
    r = rng(seed, 101)
    out = np.zeros((h, w), np.float32)
    amp, tot, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        c = max(c, 1.5)
        gh, gw = int(h / c) + 3, int(w / c) + 3
        g = r.standard_normal((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (int(round(gw * c)), int(round(gh * c))), interpolation=cv2.INTER_CUBIC)
        oy = int(r.integers(0, max(1, up.shape[0] - h)))
        ox = int(r.integers(0, max(1, up.shape[1] - w)))
        out += amp * up[oy:oy + h, ox:ox + w]
        tot += amp
        amp *= persist
        c *= 0.5
    return out / tot


# =========================================================================== 几何
def spline(P, spacing=2.0, closed=False):
    """Catmull-Rom 加密：控制点 → 间距约 spacing 像素的稠密折线。"""
    P = np.asarray(P, np.float64).reshape(-1, 2)
    if len(P) < 2:
        return P.astype(np.float32)
    if len(P) == 2 and not closed:
        L = float(np.hypot(*(P[1] - P[0])))
        n = max(2, int(math.ceil(L / spacing)) + 1)
        t = np.linspace(0, 1, n)[:, None]
        return (P[0] * (1 - t) + P[1] * t).astype(np.float32)
    if closed:
        Q = np.vstack([P[-1:], P, P[:2]])
    else:
        Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    p0, p1, p2, p3 = Q[:-3], Q[1:-2], Q[2:-1], Q[3:]
    L = np.hypot(*(p2 - p1).T)
    ns = np.maximum(1, np.ceil(L / spacing).astype(np.int64))
    idx = np.repeat(np.arange(len(ns)), ns)
    starts = np.repeat(np.cumsum(ns) - ns, ns)
    t = ((np.arange(ns.sum()) - starts) / np.repeat(ns, ns))[:, None]
    a, b, c, d = p0[idx], p1[idx], p2[idx], p3[idx]
    t2, t3 = t * t, t * t * t
    out = 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
    end = P[0:1] if closed else P[-1:]
    return np.vstack([out, end]).astype(np.float32)


def ell(cx, cy, rx, ry, a0=0.0, a1=360.0, n=None, rot=0.0):
    """椭圆弧上的点（角度制，0°=右，90°=下）。"""
    if n is None:
        n = max(6, int(abs(a1 - a0) / 360 * (rx + ry) * 0.35))
    a = np.radians(np.linspace(a0, a1, n))
    x, y = rx * np.cos(a), ry * np.sin(a)
    if rot:
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        x, y = x * cr - y * sr, x * sr + y * cr
    return np.stack([cx + x, cy + y], 1).astype(np.float32)


def bez(p0, p1, p2, n=16):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(p, np.float32) for p in (p0, p1, p2))
    return ((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2).astype(np.float32)


def rect(x0, y0, x1, y1):
    return np.float32([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def densify(P, spacing=24.0, closed=False):
    """折线按直线段加密（不做平滑）。直边物件（窗框、柜子）先 densify 再交给 line()，样条平滑后仍是直的。"""
    P = np.asarray(P, np.float32).reshape(-1, 2)
    if closed:
        P = np.vstack([P, P[:1]])
    out = []
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(math.ceil(float(np.hypot(*(b - a))) / spacing)))
        for k in range(n):
            out.append(a + (b - a) * (k / n))
    if not closed:
        out.append(P[-1])
    return np.float32(out)


def tube(path, widths, spacing=2.0):
    """沿折线生成带宽度的管状多边形（袖子、脖子、勺柄）→ (多边形, 左边线, 右边线)。"""
    C = spline(path, spacing)
    n = len(C)
    u = np.linspace(0, 1, n)
    wv = np.interp(u, np.linspace(0, 1, len(widths)), widths)
    T = np.gradient(C, axis=0)
    T /= (np.hypot(T[:, 0], T[:, 1]) + 1e-6)[:, None]
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    L = C + N * (wv / 2)[:, None]
    R = C - N * (wv / 2)[:, None]
    return np.vstack([L, R[::-1]]), L, R


def ik2(sh_pt, target, l1, l2, bend=1.0):
    """两节手臂/腿的简易 IK：→ (肘, 腕)。bend=±1 决定弯向哪一侧。"""
    s = np.float32(sh_pt)
    t = np.float32(target)
    dv = t - s
    dist = float(np.clip(np.hypot(*dv), 1e-3, l1 + l2 - 1e-3))
    a = math.acos(np.clip((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1))
    base = math.atan2(dv[1], dv[0])
    ang = base + bend * a
    e = s + l1 * np.float32([math.cos(ang), math.sin(ang)])
    wv = t - e
    wv = wv / (np.hypot(*wv) + 1e-6) * l2
    return e, e + wv


def jitter(pts, amp, seed, d, salt=0):
    pts = np.asarray(pts, np.float32)
    if amp <= 0:
        return pts
    return pts + rng(seed, d, salt).normal(0, amp, pts.shape).astype(np.float32)


def _ipoly(poly, ox, oy, sc=1.0):
    return (np.round((np.asarray(poly, np.float32) - (ox, oy)) * sc * 16)).astype(np.int32)


def as_polys(polys):
    if polys is None:
        return []
    if isinstance(polys, np.ndarray) and polys.ndim == 2:
        return [polys.astype(np.float32)]
    out = []
    for p in polys:
        if p is None:
            continue
        p = np.asarray(p, np.float32).reshape(-1, 2)
        if len(p) >= 3:
            out.append(p)
    return out


def poly_mask(polys, bbox, sc=1.0, holes=()):
    """多边形（并集）光栅化到 bbox=(x0,y0,x1,y1) 的 uint8 遮罩。"""
    x0, y0, x1, y1 = bbox
    w, h = max(1, int(math.ceil((x1 - x0) * sc))), max(1, int(math.ceil((y1 - y0) * sc)))
    m = np.zeros((h, w), np.uint8)
    for p in as_polys(polys):
        cv2.fillPoly(m, [_ipoly(p, x0, y0, sc)], 255, cv2.LINE_AA, shift=4)
    for p in as_polys(holes):
        cv2.fillPoly(m, [_ipoly(p, x0, y0, sc)], 0, cv2.LINE_AA, shift=4)
    return m


def bbox_of(polys, pad=0.0):
    allp = np.vstack([np.asarray(p, np.float32).reshape(-1, 2) for p in polys if p is not None and len(p)])
    return (float(allp[:, 0].min() - pad), float(allp[:, 1].min() - pad),
            float(allp[:, 0].max() + pad), float(allp[:, 1].max() + pad))


def region_mask(kw, pad=2.0):
    """把 op 的区域参数（polys 或 mask=(m,x0,y0)，可带 holes）统一成 (float 遮罩 0..1, x0, y0)；空区域返回 None。
    遮罩裁到画面内。笔刷可以直接用它，也可以自己用 polys 做更讲究的处理。"""
    if kw.get('mask') is not None:
        m, mx, my = kw['mask']
        m = np.asarray(m, np.float32)
        if m.max() > 1.5:
            m = m / 255.0
        x0, y0 = int(mx), int(my)
    else:
        polys = as_polys(kw.get('polys'))
        if not polys:
            return None
        bx0, by0, bx1, by1 = bbox_of(polys, pad)
        x0, y0 = int(math.floor(bx0)), int(math.floor(by0))
        x1, y1 = int(math.ceil(bx1)), int(math.ceil(by1))
        m = poly_mask(polys, (x0, y0, x1, y1), 1.0, kw.get('holes', ())).astype(np.float32) / 255.0
    # 裁到画面
    h, w = m.shape
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x0 + w), min(H, y0 + h)
    if cx1 <= cx0 or cy1 <= cy0:
        return None
    m = m[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    if not m.any():
        return None
    return m, cx0, cy0


# =========================================================================== 调色板
def hex2rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


# 物体的“固有色”。笔刷按自己的材质解释：水墨→墨色浓淡（红色系除外），水彩→淡彩，油画棒→浓烈暖调。
# tone 是水墨笔刷的建议墨色浓度（不写就按明度换算）。red=True 的在任何笔刷下都保持红色。
PAL = {
    'ink':          dict(hex='#2B2724', tone=0.95),
    'paper':        dict(hex='#F4F1EA', tone=0.0),
    # 她
    'skin':         dict(hex='#F1CFB4', tone=0.05),
    'skin_sh':      dict(hex='#D9A68E', tone=0.14),
    'blush':        dict(hex='#E8938A', tone=0.08),
    'lips':         dict(hex='#C9656A', tone=0.30),
    'hair':         dict(hex='#25222B', tone=0.86),
    'sweater':      dict(hex='#EFE6D5', tone=0.0),
    'sweater_sh':   dict(hex='#BDB3BA', tone=0.16),
    'skirt':        dict(hex='#3C4054', tone=0.62),
    'eye':          dict(hex='#231C1E', tone=0.95),
    'tear':         dict(hex='#BFD3E6', tone=0.10),
    # 他
    'boy_hair':     dict(hex='#2F2A28', tone=0.82),
    'boy_sweater':  dict(hex='#4D5E7D', tone=0.50),
    'boy_shirt':    dict(hex='#EEEEE8', tone=0.0),
    'boy_pants':    dict(hex='#58565E', tone=0.55),
    'graphite':     dict(hex='#5A5E64', tone=0.55),
    # 室内
    'wall':         dict(hex='#E6D6BE', tone=0.0),
    'wood':         dict(hex='#C08A58', tone=0.30),
    'wood_d':       dict(hex='#8E6240', tone=0.50),
    'floor':        dict(hex='#B88C63', tone=0.22),
    'cabinet':      dict(hex='#6F9690', tone=0.30),
    'metal':        dict(hex='#9AA3AD', tone=0.30),
    'enamel':       dict(hex='#ECE6DA', tone=0.04),
    'glass':        dict(hex='#C8D3D8', tone=0.08),
    'fridge':       dict(hex='#D5DCC6', tone=0.06),
    'plant':        dict(hex='#6F8F55', tone=0.45),
    'terra':        dict(hex='#C88A5E', tone=0.30),
    'cloth':        dict(hex='#E9E4DA', tone=0.03),
    'lamp':         dict(hex='#F2B45A', tone=0.0),
    'lampshade':    dict(hex='#5E8C7A', tone=0.55),
    # 室外
    'night':        dict(hex='#3E4A72', tone=0.55),
    'night_l':      dict(hex='#7C8DB5', tone=0.30),
    'snow':         dict(hex='#F6F8FB', tone=0.0),
    'roof':         dict(hex='#4E5A86', tone=0.50),
    'win_warm':     dict(hex='#F4C463', tone=0.0),
    'sky':          dict(hex='#A9C4DC', tone=0.10),
    'dusk':         dict(hex='#F0B27A', tone=0.08),
    'sun':          dict(hex='#F9D27C', tone=0.0),
    'water':        dict(hex='#7FA3B8', tone=0.25),
    'water_d':      dict(hex='#4F7189', tone=0.45),
    'grass':        dict(hex='#8FA764', tone=0.30),
    'grass_d':      dict(hex='#5F7A45', tone=0.48),
    'stone':        dict(hex='#9C968C', tone=0.30),
    'reed':         dict(hex='#C9B47E', tone=0.25),
    'tree':         dict(hex='#55704A', tone=0.55),
    # 红色线索（任何笔刷都保持红色）
    'bean':         dict(hex='#A8262E', tone=0.0, red=True),
    'bean_d':       dict(hex='#7E1A24', tone=0.0, red=True),
    'soup':         dict(hex='#8E1F28', tone=0.0, red=True),
    'hairpin':      dict(hex='#B5302A', tone=0.0, red=True),
    'redline':      dict(hex='#B5302A', tone=0.0, red=True),
    'mark':         dict(hex='#B5302A', tone=0.0, red=True),
}
LYRIC_RED = hex2rgb('#A8262E')      # 唱到的字：红豆红


def resolve_color(c, default='ink'):
    """→ 规范化颜色：dict(name, rgb(float3), tone, red)。c 可以是 PAL 名字、'#RRGGBB'、RGB 元组（0..1 或 0..255）、或已规范化的 dict。"""
    if c is None:
        c = default
    if isinstance(c, dict) and 'rgb' in c:
        return c
    if isinstance(c, str) and c in PAL:
        p = PAL[c]
        return dict(name=c, rgb=hex2rgb(p['hex']), tone=p.get('tone'), red=bool(p.get('red', False)))
    if isinstance(c, str):
        rgb = hex2rgb(c)
    else:
        rgb = np.asarray(c, np.float32)
        if rgb.max() > 1.5:
            rgb = rgb / 255.0
    return dict(name=None, rgb=rgb.astype(np.float32), tone=None, red=False)


def luma(rgb):
    return float(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])


# =========================================================================== Pen（指令录制）
def _seed(s):
    """seed 可以是整数、字符串或它们的元组（如 ('bean', k)）。"""
    if isinstance(s, (tuple, list)):
        return sd(*s) & 0x7FFFFFFF
    if isinstance(s, str):
        return zlib.crc32(s.encode('utf-8')) & 0x7FFFFFFF
    return int(s) & 0x7FFFFFFF


class Pen:
    """场景作画接口。只录指令，不画像素。style 是这一遍录制面向的风格（'A'/'B'/'C'），场景可据此改变内容。"""

    def __init__(self, style, d, t=None):
        self.style = style
        self.d = d
        self.t = draw_time(d) if t is None else t      # 成片时间（动画用）
        self.ops = []
        self._boil = [1.0]
        self._depth = 0
        self._xf = [(1.0, 0.0, 0.0)]    # 取景变换栈：p → p*s + (ox, oy)

    # ---------------------------------------------------------------- 画层
    @contextmanager
    def group(self, name, boil=None, opacity=1.0, knock=True, bleed=None, cache=None, **hints):
        b = self._boil[-1] if boil is None else float(boil)
        self.ops.append(('group', dict(name=name, boil=b, opacity=float(opacity), knock=knock, bleed=bleed,
                                       cache=cache, depth=self._depth, **hints)))
        self._boil.append(b)
        self._depth += 1
        try:
            yield self
        finally:
            self._depth -= 1
            self._boil.pop()
            self.ops.append(('end', dict(name=name)))

    # ---------------------------------------------------------------- 取景（画家把同一场景画大/画小）
    @contextmanager
    def view(self, s=1.0, ox=0.0, oy=0.0):
        """在这个上下文里，场景坐标 p 被画到 p*s + (ox, oy)。用来拍特写或在镜头里连续推拉，而不是把位图放大：
        几何按 s 缩放，线宽按 s**0.7（画特写时笔稍粗，但不会像位图放大那样变糊变肥），纸纹/排线间距等材质保持屏幕尺度。
        可嵌套。"""
        S, OX, OY = self._xf[-1]
        self._xf.append((S * s, OX + S * ox, OY + S * oy))
        try:
            yield self
        finally:
            self._xf.pop()

    @property
    def scale(self):
        return self._xf[-1][0]

    def to_screen(self, pts):
        """场景坐标 → 屏幕坐标（按当前取景）。"""
        s, ox, oy = self._xf[-1]
        return np.asarray(pts, np.float32) * s + np.float32([ox, oy])

    def _apply_view(self, kw):
        s, ox, oy = self._xf[-1]
        if s == 1.0 and ox == 0.0 and oy == 0.0:
            return
        o = np.float32([ox, oy])
        for k in ('polys', 'holes'):
            if kw.get(k):
                kw[k] = [p * s + o for p in kw[k]]
        if kw.get('mask') is not None:
            m, mx, my = kw['mask']
            m = np.asarray(m, np.float32)
            if s != 1.0:
                m = cv2.resize(m, (max(1, int(round(m.shape[1] * s))), max(1, int(round(m.shape[0] * s)))),
                               interpolation=cv2.INTER_LINEAR if s > 1 else cv2.INTER_AREA)
            kw['mask'] = (m, mx * s + ox, my * s + oy)
        if 'pts' in kw:
            kw['pts'] = kw['pts'] * s + o
        if 'w' in kw:
            kw['w'] = kw['w'] * s ** 0.7
        if kw.get('grad') is not None:
            x0, y0, x1, y1, g0, g1 = kw['grad']
            kw['grad'] = (x0 * s + ox, y0 * s + oy, x1 * s + ox, y1 * s + oy, g0, g1)
        if kw.get('rgrad') is not None:
            cx, cy, r0, r1, g0, g1 = kw['rgrad']
            kw['rgrad'] = (cx * s + ox, cy * s + oy, r0 * s, r1 * s, g0, g1)
        for kx, ky in (('x', 'y'), ('cx', 'cy')):
            if kx in kw and ky in kw:
                kw[kx] = kw[kx] * s + ox
                kw[ky] = kw[ky] * s + oy
        for k in ('rx', 'ry'):
            if k in kw:
                kw[k] = kw[k] * s

    def _kw(self, kw, seed, boil, color=None, default_color='ink'):
        kw['seed'] = _seed(seed)
        kw['boil'] = self._boil[-1] if boil is None else float(boil)
        if color is not False:
            kw['color'] = resolve_color(color, default_color) if color is not None else None
        self._apply_view(kw)
        return kw

    # ---------------------------------------------------------------- 指令
    def cover(self, polys=None, mask=None, seed=0, feather=1.0, amount=1.0, jit=0.0, holes=(), boil=None, **hints):
        self.ops.append(('cover', self._kw(dict(polys=as_polys(polys), mask=mask, feather=feather, amount=amount,
                                                jit=jit, holes=as_polys(holes), **hints), seed, boil, False)))

    def fill(self, polys=None, color='ink', seed=0, mask=None, tone=None, holes=(), grad=None, rgrad=None,
             offset=None, boil=None, **hints):
        kw = self._kw(dict(polys=as_polys(polys), mask=mask, tone=tone, holes=as_polys(holes), grad=grad,
                           rgrad=rgrad, offset=offset, **hints), seed, boil)
        kw['color'] = resolve_color(color)
        self.ops.append(('fill', kw))

    def shade(self, polys=None, amount=0.3, seed=0, mask=None, color=None, holes=(), grad=None, rgrad=None,
              angle=None, boil=None, **hints):
        self.ops.append(('shade', self._kw(dict(polys=as_polys(polys), mask=mask, amount=amount, holes=as_polys(holes),
                                                grad=grad, rgrad=rgrad, angle=angle, **hints), seed, boil, color)))

    def line(self, pts, w, tone=0.85, color=None, seed=0, closed=False, taper=(0.12, 0.30), role='contour',
             boil=None, **hints):
        P = np.asarray(pts, np.float32).reshape(-1, 2)
        if len(P) < 2:
            return
        self.ops.append(('line', self._kw(dict(pts=P, w=float(w), tone=float(tone), closed=closed, taper=taper,
                                               role=role, **hints), seed, boil, color)))

    def hatch(self, polys=None, angle=45.0, spacing=6.0, tone=0.3, color=None, seed=0, mask=None, grad=None,
              holes=(), boil=None, **hints):
        self.ops.append(('hatch', self._kw(dict(polys=as_polys(polys), mask=mask, angle=float(angle),
                                                spacing=float(spacing), tone=float(tone), grad=grad,
                                                holes=as_polys(holes), **hints), seed, boil, color)))

    def dot(self, x, y, rx, ry=None, color='ink', tone=0.9, seed=0, rot=0.0, boil=None, **hints):
        kw = self._kw(dict(x=float(x), y=float(y), rx=float(rx), ry=float(rx if ry is None else ry),
                           tone=float(tone), rot=float(rot), **hints), seed, boil)
        kw['color'] = resolve_color(color)
        self.ops.append(('dot', kw))

    def light(self, cx, cy, rx, ry=None, amt=0.5, color='lamp', seed=0, boil=None, **hints):
        kw = self._kw(dict(cx=float(cx), cy=float(cy), rx=float(rx), ry=float(rx if ry is None else ry),
                           amt=float(amt), **hints), seed, boil)
        kw['color'] = resolve_color(color)
        self.ops.append(('light', kw))

    def lift(self, polys=None, amt=1.0, seed=0, mask=None, soft=2.0, holes=(), boil=None, **hints):
        self.ops.append(('lift', self._kw(dict(polys=as_polys(polys), mask=mask, amt=float(amt), soft=float(soft),
                                               holes=as_polys(holes), **hints), seed, boil, False)))


# =========================================================================== 调试笔刷（平涂，只用来看几何）
class FlatBrush:
    """最简单的笔刷：固有色平涂 + 匀宽线。用来检查人物和场景的几何、遮挡、动作，不代表任何最终风格。"""
    key = 'F'

    def paper(self):
        return np.ones((H, W, 3), np.float32) * hex2rgb('#F4F1EA')

    def render(self, ops, d):
        img = self.paper()
        base = self.paper()
        stack = []
        cur = img
        for kind, kw in ops:
            if kind == 'group':
                stack.append((cur, kw))
                cur = cur.copy() if kw.get('knock', True) else np.zeros_like(cur) + base
                continue
            if kind == 'end':
                parent, gkw = stack.pop()
                op = gkw.get('opacity', 1.0)
                if not gkw.get('knock', True):
                    # 透明叠加：只取比纸暗的部分
                    dark = np.clip(base - cur, 0, 1)
                    cur = np.clip(parent - dark * op, 0, 1)
                elif op < 1.0:
                    cur = parent * (1 - op) + cur * op
                continue
            if kind in ('cover', 'fill', 'shade', 'lift', 'hatch'):
                r = region_mask(kw)
                if r is None:
                    continue
                m, x0, y0 = r
                sub = cur[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
                mm = m[..., None]
                if kind in ('cover', 'lift'):
                    a = kw.get('amount', kw.get('amt', 1.0))
                    sub += (base[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] - sub) * mm * a
                elif kind == 'fill':
                    sub += (kw['color']['rgb'] - sub) * mm
                elif kind == 'shade':
                    sub *= 1 - mm * 0.6 * kw['amount']
                elif kind == 'hatch':
                    sub *= 1 - mm * 0.25 * kw['tone']
            elif kind == 'line':
                P = spline(kw['pts'], 2.0, kw['closed'])
                col = kw['color']['rgb'] if kw.get('color') else hex2rgb('#2B2724')
                wpx = max(1, int(round(kw['w'] * 0.35)))
                cv2.polylines(cur, [np.round(P * 16).astype(np.int32)], kw['closed'], col.tolist(), wpx,
                              cv2.LINE_AA, shift=4)
            elif kind == 'dot':
                cv2.ellipse(cur, (int(kw['x'] * 16), int(kw['y'] * 16)), (int(kw['rx'] * 16), int(kw['ry'] * 16)),
                            kw['rot'], 0, 360, kw['color']['rgb'].tolist(), -1, cv2.LINE_AA, shift=4)
            elif kind == 'light':
                pass
        return np.clip(cur, 0, 1)

    def paint_text(self, rgb, items, d):
        for it in items:
            m, x0, y0 = it['mask'], it['x'], it['y']
            r = _clip_box(x0, y0, m.shape[1], m.shape[0])
            if r is None:
                continue
            sx0, sy0, dx0, dy0, w, h = r
            mm = (m[sy0:sy0 + h, sx0:sx0 + w] * it['alpha'])[..., None]
            col = lerp(hex2rgb('#2B2724'), LYRIC_RED, it['sung'])
            sub = rgb[dy0:dy0 + h, dx0:dx0 + w]
            sub += (col - sub) * mm
        return rgb


def _clip_box(x0, y0, w, h):
    """把左上角 (x0,y0)、尺寸 w×h 的贴图裁到画面内 → (源x, 源y, 目标x, 目标y, 宽, 高)。"""
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return None
    return dx0 - x0, dy0 - y0, dx0, dy0, dx1 - dx0, dy1 - dy0


clip_box = _clip_box


# =========================================================================== 歌词（统一字体与位置，质感由笔刷决定）
LEAD = 0.6          # 整句比第一个字提前出现
GAP_AFTER = 0.3     # 不早于上一句最后一个字之后
TYPE_GAP = 0.025    # 整句快速打出
LYRIC_SIZE = 78
LYRIC_TRACK = 8
LYRIC_CX = 960
LYRIC_BASE = 948


def parse_lrc(path=LRC):
    """逐字 LRC → [dict(t=行时间, text, times=[每字时间])]（原曲时间）。"""
    import re
    out = []
    tm = lambda m, s: int(m) * 60 + float(s)
    for line in open(path, encoding='utf-8').read().splitlines():
        m = re.match(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)', line)
        if not m or not m.group(3).strip():
            continue
        lt = tm(m.group(1), m.group(2))
        pairs = re.findall(r'<(\d+):(\d+(?:\.\d+)?)>([^<]*)', m.group(3))
        text, times = '', []
        for mm, ss, ch in pairs:
            for c in ch.strip():
                text += c
                times.append(tm(mm, ss))
        if text:
            out.append(dict(t=lt, text=text, times=times))
    return out


def build_lines(path=LRC):
    """套用歌词同步规则，换算成成片时间。每句 dict(text, times, start, end, appear[每字出现时间], idx)。"""
    raw = parse_lrc(path)
    lines = []
    for i, L in enumerate(raw):
        first, last = L['times'][0], L['times'][-1]
        start = min(L['t'], first - LEAD)
        if i > 0:
            start = max(start, raw[i - 1]['times'][-1] + GAP_AFTER)
        lines.append(dict(idx=i, text=L['text'], times=list(L['times']), start=start, first=first, last=last))
    for i, L in enumerate(lines):
        nxt = lines[i + 1]['start'] if i + 1 < len(lines) else 1e9
        L['end'] = L['last'] + 3.2 if nxt - L['last'] > 6 else nxt - 0.02
    # 成片时间
    out = []
    for L in lines:
        c = dict(L)
        for k in ('start', 'first', 'last', 'end'):
            c[k] = L[k] - CUT_START
        c['times'] = [x - CUT_START for x in L['times']]
        c['appear'] = [c['start'] + TYPE_GAP * j for j in range(len(c['times']))]
        if c['end'] > 0 and c['start'] < CUT_LEN:
            out.append(c)
    return out


_LINES = None


def lines():
    global _LINES
    if _LINES is None:
        _LINES = build_lines()
    return _LINES


# 歌词样式随画面风格变化（用户 2026-10-24 要求）：位置统一在底部居中，字体与质感跟着笔刷走
LYRIC_STYLE = {
    'C': dict(font=os.path.join(FONT_DIR, 'STXINGKA.TTF'), size=78, track=8),    # 华文行楷：毛笔墨字
    'A': dict(font=os.path.join(FONT_DIR, 'STKAITI.TTF'), size=74, track=12),    # 华文楷体：彩铅手写
    'B': dict(font=os.path.join(FONT_DIR, 'FZSTK.TTF'), size=80, track=8),       # 方正舒体：圆润的蜡笔字
}
LYRIC_STYLE['F'] = LYRIC_STYLE['C']

_GLYPHS = {}
_FONTS = {}


def glyph(ch, font=FONT_LYRIC, size=LYRIC_SIZE):
    """字形遮罩 (m float32 0..1, 左偏移, 上偏移(相对基线), 步进)。"""
    key = (ch, font, size)
    if key in _GLYPHS:
        return _GLYPHS[key]
    if (font, size) not in _FONTS:
        _FONTS[(font, size)] = ImageFont.truetype(font, size)
    f = _FONTS[(font, size)]
    l, t, r, b = f.getbbox(ch, anchor='ls')
    pad = int(size * 0.25)
    w, h = (r - l) + 2 * pad, (b - t) + 2 * pad
    im = Image.new('L', (max(1, w), max(1, h)), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), ch, font=f, fill=255, anchor='ls')
    g = (np.asarray(im, np.float32) / 255.0, l - pad, t - pad, f.getlength(ch))
    _GLYPHS[key] = g
    return g


def lyric_items(d, style='C', cx=LYRIC_CX, base=LYRIC_BASE):
    """当前绘制序号要显示的歌词字 → [dict(mask, x, y, sung 0..1, hop, alpha, i, char, line, base, adv, x0)]。
    style 决定字体/字号/字距（LYRIC_STYLE），质感由笔刷的 paint_text 决定。
    sung：0 未唱 … 1 已唱（唱到时 0.3 秒内从字心向外变红，笔刷可用作红色扩散半径或下划线进度）；
    状态按该绘制格的中点时间判断（与画面同步，最多提前/滞后 1/24 秒）。
    base 是基线 y；x0、adv 是这个字的步进起点和宽度（画下划线用）。"""
    st = LYRIC_STYLE.get(style, LYRIC_STYLE['C'])
    font, size, track = st['font'], st['size'], st['track']
    t = draw_time(d)
    items = []
    for L in lines():
        if not (L['start'] <= t < L['end']):
            continue
        fade = clamp((L['end'] - t) / 0.25)
        gl = [glyph(c, font, size) for c in L['text']]
        total = sum(g[3] for g in gl) + track * (len(gl) - 1)
        x = cx - total / 2
        for j, (g, c) in enumerate(zip(gl, L['text'])):
            m, ox, oy, adv = g
            if t >= L['appear'][j]:
                u = clamp((t - L['times'][j]) / 0.30) if t >= L['times'][j] else 0.0
                sung = 1.0 if t >= L['times'][j] + 0.30 else (u if t >= L['times'][j] else 0.0)
                hop = -0.085 * size * math.sin(math.pi * u) if 0 < u < 1 else 0.0
                a_in = clamp((t - L['appear'][j]) / 0.06 + 0.55, 0.55, 1.0)
                items.append(dict(mask=m, x=int(round(x + ox)), y=int(round(base + oy + hop)), sung=float(sung),
                                  hop=hop, alpha=a_in * fade, i=j, char=c, line=L['idx'], base=base,
                                  x0=float(x), adv=float(adv), size=size, track=track))
            x += adv + track
    return items


def underline_mask(it, width=3.0, wob=2.2, extra=6.0, drop=0.17):
    """唱到的字下方的手绘下划线：随 sung 从左往右画出来。起伏按绝对 x 计算，一句里各字的线段连成一条。
    → (float 遮罩 0..1（已乘 alpha），x0, y0) 或 None。笔刷用自己的材质去画它。"""
    s = float(it['sung'])
    if s <= 0.001 or 'adv' not in it:
        return None
    tr = float(it.get('track', extra))
    x0 = it['x0'] - tr * 0.5 - 1.0                      # 每段多盖住半个字距，相邻字的线段首尾相接
    x1 = x0 + (it['adv'] + tr + 2.0) * s
    yb = it['base'] + drop * it['size']
    n = max(2, int((x1 - x0) / 4) + 1)
    xs = np.linspace(x0, x1, n)
    ph = it['line'] * 1.7
    ys = yb + wob * np.sin(xs / 41.0 + ph) + 0.8 * np.sin(xs / 13.0 + 2 * ph)
    pad = int(width * 2 + wob * 2 + 4)
    X0, Y0 = int(math.floor(x0)) - pad, int(yb) - pad
    w, h = int(math.ceil(x1)) - X0 + pad + 1, 2 * pad
    m = np.zeros((h, w), np.uint8)
    pts = np.stack([xs - X0, ys - Y0], 1)
    cv2.polylines(m, [np.round(pts * 16).astype(np.int32)], False, 255, max(1, int(round(width))), cv2.LINE_AA,
                  shift=4)
    return m.astype(np.float32) / 255.0 * float(it['alpha']), X0, Y0


# =========================================================================== 镜头
def camera(rgb, zoom=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    """以 (cx,cy) 为中心缩放（zoom≥1），再平移 (dx,dy)。只做缓慢推拉/摇移，不做抖动。"""
    if abs(zoom - 1.0) < 1e-5 and abs(dx) < 1e-3 and abs(dy) < 1e-3:
        return rgb
    M = np.float32([[zoom, 0, cx * (1 - zoom) + dx], [0, zoom, cy * (1 - zoom) + dy]])
    return cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def to_u8(rgb):
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
