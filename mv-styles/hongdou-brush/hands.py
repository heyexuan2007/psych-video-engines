# -*- coding: utf-8 -*-
"""
《红豆》手绘版 · 手部特写（只调用 Pen 指令：cover / fill / shade / line / lift；三种笔刷都能画）

━━ 手的模型 ━━
  每只手是一个很小的 3D 骨架（正交投影），画的时候全部变成 2D 多边形和线交给 Pen，几何与笔刷无关：
    手掌：有厚度的圆角板 + 虎口的蹼；四根手指：各三节（近节/中节/远节），每节是两头粗细不同的胶囊；
    拇指：掌骨（连着大鱼际）+ 两节；手腕 → 前臂（椭圆柱）伸进袖口。
    她：手指纤细（指宽约 0.08 L），袖口是米白粗针罗纹高领毛衣 'sweater'（罗纹竖线、卷边口）；
    他：手大一号（size 默认 ×1.12）、更宽、指节更明显，藏青毛衣 'boy_sweater' 的罗纹袖口里露出一截白衬衫袖口 'boy_shirt'（带扣子）。
  局部坐标（右手）：原点 = 腕横纹中心；+Y 指尖方向；+X 拇指一侧；+Z 手背；单位 = 手长 L（腕横纹 → 中指尖）。
  关节角（度）：spread 张开（正 = 往拇指一侧）；flex = (掌指, 近指间, 远指间)，正 = 往掌心弯，负 = 往手背翘。

  画法（一次 _render）：按深度排序（远的先画）→ 整只手 cover 剪影 → 一层肤色 'skin' → 袖子/笔/红豆等实物各自上色
  → 受光反方向一侧的体积阴影（'skin_sh'）+ 弯曲的手指投在手掌上的影 → 受光边提白 → 指甲、指节褶纹、掌纹
  → 轮廓线。手指和手掌、拇指和大鱼际、手腕和前臂在接合处不画线（连成一体）；轮廓按受光方向分轻重
  （背光一侧粗重、受光一侧细淡）；被前面的手指挡住的线在遮挡处干脆地断开；红线等“3D 线”逐点做深度遮挡
  （缠在手指上的线：绕到手指前面的那半圈可见，绕到后面的被挡住）。

━━ 公共参数（每个函数都有）━━
  x, y      锚点（场景坐标；各函数的锚点不同，见下）
  rot       画面内旋转（度，顺时针为正），在各函数默认朝向上再转
  size      手长 L（像素）。她的手特写 ≈ 380–480（手占画面 1/3–1/2）；他的手 size 为 None 时按她的 1.12 倍
  seed      个体种子（同一只手固定）
  yaw/pitch 3D 朝向（度）。yaw 绕画面竖轴转（看到拇指侧 / 小指侧），pitch 绕画面横轴转（正 = 指尖往画面里倒）
  flip      True = 左手（镜像）
  who       'girl' | 'boy'
  light     画面里光从哪来（屏幕向量，指向光源），默认左上 (-0.55, -0.83)
  sleeve    True 画袖口；sleeve_len 袖子从手腕往肘部方向画多长（单位 L，默认 0.9，够出画就行）
  wrist     (屈, 偏) 手腕弯曲（度）：屈 >0 手往掌心弯；偏 >0 往拇指一侧偏
  boil      线条抖动（None = 继承当前画层）；group=True 时自己开一个画层（名字 'hand_<函数名>'）
  detail    0..1 细节量（指甲、褶纹、掌纹、袖口罗纹）。手很小（size < 120）时自动减少
返回 info 字典（坐标与 x, y 同一坐标系 = 场景坐标）：各函数的关键点（见下），以及
  tips 五个指尖（拇/食/中/无名/小）、wrist 手腕中心、sil 整只手（含袖子、实物）的剪影多边形列表、z 关键点深度。

━━ 函数 ━━
1. palm_up(pen, x, y, cup=0..1, tilt=40, bean=None, ...)                         第 12 镜：最后一颗红豆停在掌心
     她摊开的掌心（手背朝下、手指微曲、掌心朝镜头），tilt = 手掌往画面里倒的角度（平放在台面上、从斜上方看）。
     cup 0→1 四指从指根依次慢慢合拢（小指先动），拇指往里收。锚点 (x,y) = 掌心中心（掌面上）。
     bean：None 不画；True = 掌心中央一颗红豆；(bx, by) = 相对掌心中心的位置（单位 L，掌面局部坐标，by>0 往指根，
           bx>0 往拇指一侧）——场景可以让红豆在掌心里滚，手指合拢时会正确地挡住它；bean_r 红豆半径（L，默认 0.042）。
     返回 info['palm']（掌心中心）、info['bean']（红豆中心，没有则 None）、info['bean_r']（屏幕半径）。
     红豆还没落到掌心（在空中、从罐口滚下来）时由场景自己画在手的后面/前面；落进掌心后改用 bean= 交给这里画。
2. hand_pen(pen, x, y, lift=0, ...)                                             第 11 镜：在挂历上画叉
     她握笔（三指握法：食指压在笔杆上、拇指在另一侧、笔杆靠在虎口，无名指小指收起）。锚点 (x,y) = 笔尖（贴在纸面上），
     默认朝向：笔尖在左下，手在右上、手背朝镜头、指尖往画面里倒（对着墙上的挂历写字）。
     场景画叉时只要逐帧移动 (x,y)；lift 0..1 抬笔（两笔之间，手腕微微后仰），rot 跟着笔画方向微转更自然。
     pen_color 笔杆颜色（默认 'ink'），pen_len 笔长（L）。返回 info['tip']（= (x,y)）、info['pen_back'] 笔尾。
3. hand_grip(pen, x, y, reach=0..1, frm=(-0.85, 0.10), ...)                      第 13 镜：取下他的马克杯
     她伸手去握马克杯把手：锚点 (x,y) = 把手外侧竖梁的中点（握住时手指绕着它）。默认右手从画面左边伸过来（手背朝镜头、
     手指朝右、拇指压在把手上沿）；从右边伸过来用 flip=True。
     reach 0→0.7 手从 frm（相对锚点的偏移，单位 L，按 rot/flip 转）移到把手，手指半张；0.65→1 四指绕过竖梁收拢、拇指压上把手。
     bar_r 竖梁半径（L）。场景先画杯子和把手，再调这个函数（手指盖在把手前面）。
     握住之后要把杯子拿走：让 (x,y) 跟着杯子动即可。返回 info['grip']（= (x,y)）、info['hand']（当前手的位置）。
4. hand_thread(pen, x, y, wraps=0..3, clench=0..1, glow=0..1, out_angle=-25, ...) 第 16 镜：红线一圈圈缠在手指上
     她的手（手背朝镜头、略偏拇指侧，指尖朝上）。锚点 (x,y) = 手背中心。红线（PAL 'redline'）在四根手指的近节上
     螺旋地缠 wraps 圈（小数 = 正在缠的那一圈画到哪里），clench 0→1 四指慢慢攥成拳、拇指压上来，线跟着手指走。
     glow 0..1 红线变粗、更红、周围洇出一点红晕（“不放手”时蓄力）。tail=True 时手链的另一头（串着那颗红豆）
     从小指一侧垂下来，随 pen.t 轻轻晃。
     返回 info['out']（红线离开手的端点）、info['dir']（离开方向，单位向量，屏幕）——场景从 out 沿 dir 继续把红线
     画向窗缝；info['bean']（垂下的红豆）。out_angle = 离开方向（度，屏幕，0 = 向右，-90 = 向上）。
5. pinky_hook(pen, x, y, hook=0..1, gap=0.16, ...)                               第 18 镜：草地上小指勾小指（B 为主）
     草地上并排的两只手（手背朝上，从后上方看，指尖朝画面里）：左边是她的右手，右边是他的左手（大一号、藏青袖口+白衬衫）。
     锚点 (x,y) = 两根小指指根之间的中点。hook 0→1：他的小指抬起、伸过来，勾住她的小指往下扣，她的小指也微微弯起来迎上；
     两根小指上松松地绕着一圈红线（thread=True），线头顺着两只手之间垂到草地上往镜头这边拖（tail_len，L）。
     backlit 0..1：金色黄昏的逆光——手背整体压暗，朝着光（默认画面上方，light=(0.2,-1)）的轮廓镶一圈暖金边
     （B 里是 #FFA640 蜡笔 + 奶白高光，C 里是提白）。size = 她的手长；他的手 = size × boy_scale。
     返回 info['hook']（勾住的那一点）、info['girl']/info['boy']（两只手各自的 info）、info['tail_end']。
6. fist_bean(pen, x, y, squeeze=0..1, bean=0..1, ...)                            第 15 镜：攥紧红豆按在胸口
     她握拳，默认从拇指一侧看（yaw=90，指尖朝上 = 指节在上）；食指卷成的“小洞”里露出一点红豆的红（bean 0..1 露出多少）。
     锚点 (x,y) = 拳心（近节指骨中部）。squeeze 越攥越紧（手指再弯一点、指节更突出）。
     可缩放（size 60–150 时可以给 characters 当小拳头用：sleeve=False、detail 自动减少）。
     返回 info['fist']、info['bean']。

━━ 给场景的提示 ━━
  手的线宽 ≈ 0.0165 L（特写里约 7px），和人物身上的线一样是毛笔/蜡笔笔触；用 pen.view 推拉时线宽按 s**0.7 变。
  手的剪影（info['sil']）可以给场景做投影、留白光晕。手不带背景，场景先画背景、台面、杯子，再画手。
"""
import math
from contextlib import contextmanager

import cv2
import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from core import ell, clamp, smooth01, ease_io, ease_out

# =========================================================================== 手的尺寸（单位 L）
_GIRL = dict(
    who='girl',
    palm=[(-0.130, 0.000), (-0.148, 0.110), (-0.165, 0.250), (-0.170, 0.350), (-0.160, 0.418),
          (-0.122, 0.452), (-0.050, 0.472), (0.030, 0.476), (0.102, 0.462), (0.148, 0.432),
          (0.165, 0.385), (0.156, 0.300), (0.138, 0.170), (0.124, 0.060), (0.116, 0.000)],
    zt=0.036, zb=0.046,
    fb=[(0.116, 0.442), (0.036, 0.456), (-0.046, 0.444), (-0.122, 0.412)],          # 掌指关节 (x, y)
    fl=[(0.218, 0.132, 0.100), (0.240, 0.152, 0.108), (0.226, 0.144, 0.104), (0.176, 0.104, 0.090)],
    fr=[(0.040, 0.036, 0.032, 0.0285), (0.042, 0.038, 0.0335, 0.0295), (0.039, 0.035, 0.031, 0.0275),
        (0.033, 0.030, 0.027, 0.0245)],
    tb=(0.080, 0.070, -0.020), tl=(0.205, 0.145, 0.115), tr=(0.064, 0.046, 0.040, 0.0345),
    wrist=(0.126, 0.062), fore=(0.138, 0.072),
    lw=1.0, knuck=0.5,
    # 袖子：[(离腕距离, 半宽, 半厚)]
    cuff=0.075,
    sleeve=[[(0.075, 0.150, 0.100), (0.245, 0.145, 0.098)],
            [(0.225, 0.158, 0.110), (0.330, 0.180, 0.135), (0.60, 0.190, 0.146), (1.6, 0.20, 0.155)]],
    sleeve_col='sweater', sleeve_sh='sweater_sh', rib=(0.075, 0.245, 22),
)


def _boy_spec():
    g = _GIRL
    kx = 1.10
    b = dict(g)
    b.update(
        who='boy',
        palm=[(x * kx, y) for x, y in g['palm']],
        zt=0.040, zb=0.050,
        fb=[(x * kx, y) for x, y in g['fb']],
        fl=[tuple(v * 0.98 for v in L) for L in g['fl']],
        fr=[tuple(r * 1.14 for r in R) for R in g['fr']],
        tb=(0.088, 0.070, -0.022), tl=(0.205, 0.142, 0.112), tr=tuple(r * 1.12 for r in g['tr']),
        wrist=(0.138, 0.068), fore=(0.150, 0.080),
        lw=1.08, knuck=1.0,
        cuff=0.045,
        shirt=[(0.045, 0.150, 0.092), (0.165, 0.148, 0.092)],
        sleeve=[[(0.135, 0.170, 0.112), (0.285, 0.164, 0.108)],
                [(0.265, 0.180, 0.124), (0.40, 0.206, 0.150), (0.65, 0.220, 0.162), (1.6, 0.226, 0.17)]],
        sleeve_col='boy_sweater', sleeve_sh=None, rib=(0.135, 0.285, 18),
    )
    return b


_BOY = _boy_spec()


def _spec(who):
    return _BOY if who == 'boy' else _GIRL


# =========================================================================== 向量 / 朝向
def _nz(v):
    v = np.asarray(v, np.float64)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else v


def _Rx(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def _Ry(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def _Rz(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


# 基准朝向：手背朝镜头、指尖朝上（右手拇指在画面左边）。相机坐标：x 右、y 下、z 朝向观众。
_B0 = np.diag([-1.0, -1.0, 1.0])


def orient(rot=0.0, pitch=0.0, yaw=0.0):
    return _Rz(rot) @ _Rx(pitch) @ _Ry(yaw) @ _B0


def _rodrigues(v, k, ang):
    k = _nz(k)
    a = math.radians(ang)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * np.dot(k, v) * (1 - math.cos(a))


class _Rig:
    """局部 3D → 场景坐标（正交投影）。z 越大离镜头越近（像素）。"""

    def __init__(self, sp, M, size, flip, anchor, at):
        self.sp = sp
        self.M = np.asarray(M, np.float64)
        self.S = float(size)
        self.flip = bool(flip)
        self.o = np.zeros(2)
        self.o = np.float64(at) - self.cam(anchor)[:2] * self.S

    def cam(self, p):
        p = np.array(p, np.float64)
        if self.flip:
            p[..., 0] = -p[..., 0]
        return p @ self.M.T

    def scr(self, p):
        return self.cam(p)[..., :2] * self.S + self.o

    def z(self, p):
        return self.cam(p)[..., 2] * self.S

    def dirz(self, v):
        """局部方向向量的“朝镜头”分量（-1..1）。"""
        v = np.array(v, np.float64)
        if self.flip:
            v[..., 0] = -v[..., 0]
        return (v @ self.M.T)[..., 2]


# =========================================================================== 骨架
def _chain(base, d, n, lens, flex):
    pts = [np.asarray(base, np.float64)]
    frs = []
    for L_i, th in zip(lens, flex):
        a = math.radians(th)
        d, n = d * math.cos(a) - n * math.sin(a), n * math.cos(a) + d * math.sin(a)
        frs.append((d, n))
        pts.append(pts[-1] + d * L_i)
    return pts, frs


def _finger(sp, i, spread, mcp, pip, dip, twist=0.0):
    bx, by = sp['fb'][i]
    s = math.radians(spread)
    d0 = np.array([math.sin(s), math.cos(s), 0.0])
    n0 = np.array([0.0, 0.0, 1.0])
    if twist:
        n0 = _rodrigues(n0, d0, twist)
    pts, frs = _chain((bx, by, 0.0), d0, n0, sp['fl'][i], (mcp, pip, dip))
    return dict(j=pts, fr=frs, r=sp['fr'][i], L=sp['fl'][i], i=i)


def _thumb(sp, az, el, roll, cmc, mcp, ip):
    a, e, r = math.radians(az), math.radians(el), math.radians(roll)
    d = np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), -math.sin(e)])
    ref = np.array([math.sin(r), 0.0, math.cos(r)])
    n = _nz(ref - np.dot(ref, d) * d)
    pts, frs = _chain(sp['tb'], d, n, sp['tl'], (cmc, mcp, ip))
    return dict(j=pts, fr=frs, r=sp['tr'], L=sp['tl'], i=-1, ang=(az, el, roll, cmc, mcp, ip))


def _thumb_ik(sp, target, roll, flex, az=(-10.0, 80.0), el=(-10.0, 85.0), pad=0.0, flexes=None):
    """找拇指掌骨方向 (az, el)（以及 flexes 里最合适的一组弯曲），让拇指尖（往指腹方向偏 pad）落在 target。
    flexes=None → 返回 (az, el)；否则返回 (az, el, flex)。"""
    target = np.asarray(target, np.float64)
    cands = [tuple(flex)] if flexes is None else [tuple(f) for f in flexes]
    best = None
    for fx in cands:
        A = np.linspace(az[0], az[1], 19)
        E = np.linspace(el[0], el[1], 19)
        loc = None
        for _ in range(2):
            for a in A:
                for e in E:
                    T = _thumb(sp, a, e, roll, *fx)
                    tip = T['j'][-1] - T['fr'][-1][1] * pad
                    dd = float(np.sum((tip - target) ** 2))
                    if loc is None or dd < loc[0]:
                        loc = (dd, a, e)
            _, a0, e0 = loc
            sa, se = (A[1] - A[0]) * 1.5, (E[1] - E[0]) * 1.5
            A = np.linspace(a0 - sa, a0 + sa, 9)
            E = np.linspace(e0 - se, e0 + se, 9)
        if best is None or loc[0] < best[0] - 1e-6:
            best = (loc[0], loc[1], loc[2], fx)
    if flexes is None:
        return best[1], best[2]
    return best[1], best[2], best[3]


def _skeleton(sp, fingers, thumb):
    """fingers: 4 × (spread, mcp, pip, dip[, twist])；thumb: (az, el, roll, cmc, mcp, ip)。"""
    F = [_finger(sp, i, *f) for i, f in enumerate(fingers)]
    T = _thumb(sp, *thumb)
    return F, T


def _mix(a, b, t):
    return tuple(float(x) * (1 - t) + float(y) * t for x, y in zip(a, b))


# =========================================================================== 几何工具
def _circle(c, r, n=20):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)], 1)


def _hull(pts):
    pts = np.asarray(pts, np.float32).reshape(-1, 2)
    h = cv2.convexHull(pts).reshape(-1, 2).astype(np.float64)
    if len(h) < 3:
        return Polygon()
    return Polygon(h)


def _capsule(a, b, ra, rb, n=22):
    return _hull(np.vstack([_circle(a, ra, n), _circle(b, rb, n)]))


def _valid(g):
    if g is None or g.is_empty:
        return Polygon()
    if not g.is_valid:
        g = g.buffer(0)
    return g


def _polys(g, min_area=3.0):
    if g is None or g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        gs = [g]
    elif hasattr(g, 'geoms'):
        gs = []
        for q in g.geoms:
            gs.extend(_polys(q, min_area))
        return gs
    else:
        return []
    return [q for q in gs if q.area >= min_area]


def _pp(g, min_area=3.0):
    """shapely → (外轮廓列表, 洞列表)，float32 数组。"""
    ex, ho = [], []
    for q in _polys(g, min_area):
        ex.append(np.float32(q.exterior.coords)[:-1])
        for r in q.interiors:
            ho.append(np.float32(r.coords)[:-1])
    return ex, ho


def _resample(P, step, closed=True):
    P = np.asarray(P, np.float64).reshape(-1, 2)
    Q = np.vstack([P, P[:1]]) if closed else P
    seg = np.hypot(*np.diff(Q, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    L = float(s[-1])
    if L < 1e-6:
        return P[:1]
    n = max(4 if closed else 2, int(round(L / max(step, 0.5))) + (0 if closed else 1))
    t = np.linspace(0, L, n, endpoint=not closed)
    return np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], 1)


def _contains(g, P):
    if g is None or g.is_empty or len(P) == 0:
        return np.zeros(len(P), bool)
    return shapely.contains_xy(g, P[:, 0], P[:, 1])


def _runs(keep, min_pts=3):
    out = []
    n = len(keep)
    i = 0
    while i < n:
        if not keep[i]:
            i += 1
            continue
        j = i
        while j < n and keep[j]:
            j += 1
        if j - i >= min_pts:
            out.append((i, j, i > 0, j < n))
        i = j
    return out


def _sk(seed, *k):
    if isinstance(seed, (tuple, list)):
        return tuple(seed) + tuple(k)
    return (seed,) + tuple(k)


@contextmanager
def _nullctx():
    yield


# =========================================================================== 元素
def _elem(name, geom, z, color='skin', **kw):
    e = dict(name=name, geom=_valid(geom), z=float(z), color=color, segs=None, fuse=[], drop=[], lw=1.0,
             ltone=1.0, shk=None, shade_color='skin_sh', shade_amt=0.24, cast=0.0, hl=0.0, lcolor=None,
             fill_kw={}, rim=1.0)
    e.update(kw)
    if e['segs'] is None:
        e['segs'] = [(e['geom'], e['z'])]
    return e


def _finger_elems(rig, F, name, split=None, zoff=None):
    """一根手指 → 一个元素（三节胶囊的并集）；split=k 时在第 k 节前拆成两个元素（勾手指时前后交错用）。"""
    S = rig.S
    J = [rig.scr(p) for p in F['j']]
    Z = [float(rig.z(p)) for p in F['j']]
    R = [r * S for r in F['r']]
    segs = []
    for k in range(3):
        segs.append((_capsule(J[k], J[k + 1], R[k], R[k + 1]), (Z[k] + Z[k + 1]) / 2))
    cuts = [] if split is None else ([split] if np.isscalar(split) else list(split))
    bounds = [0] + cuts + [3]
    groups = [(bounds[q], bounds[q + 1]) for q in range(len(bounds) - 1)]
    out = []
    for gi, (a, b) in enumerate(groups):
        g = unary_union([segs[k][0] for k in range(a, b)])
        z = float(np.mean([segs[k][1] for k in range(a, b)]))
        nm = name if gi == 0 else name + '_' + 'xbc'[gi]
        out.append(_elem(nm, g, z, segs=[segs[k] for k in range(a, b)], shk=0.55 * R[1], cast=1.0, hl=1.0,
                         fid=F['i'], jsc=J, rsc=R, krange=(a, b)))
    for gi in range(len(groups) - 1):
        jn = J[groups[gi][1]]
        zone = Polygon(_circle(jn, R[groups[gi][1]] * 1.6, 24))
        out[gi]['fuse'].append((out[gi + 1]['name'], zone))
        out[gi + 1]['fuse'].append((out[gi]['name'], zone))
    return out


def _palm_elem(rig, sp, F, T, name='palm'):
    S = rig.S
    out = np.array(sp['palm'], np.float64)
    c = out.mean(0)
    pts3 = []
    for z, k in ((0.0, 1.0), (sp['zt'], 0.86), (-sp['zb'], 0.86), (sp['zt'] * 0.6, 0.97), (-sp['zb'] * 0.6, 0.97)):
        q = c + (out - c) * k
        pts3.append(np.column_stack([q, np.full(len(q), z)]))
    hull = _hull(rig.scr(np.vstack(pts3)))
    # 虎口的蹼：拇指掌指关节 → 食指指根之间一张微微凹进去的皮
    tj = T['j']
    ib = F[0]['j'][0]
    r0 = sp['fr'][0][0]
    A = tj[1] + (ib - tj[1]) * 0.12
    Ib = ib + np.array([r0 * 0.55, -0.015, 0.0])
    B = (A + Ib) / 2 + np.array([0.0, -0.045, 0.0])
    C = tj[0] + np.array([0.0, 0.03, 0.0])
    D = np.array([sp['palm'][10][0] * 0.9, sp['palm'][10][1] - 0.04, 0.0])
    web = Polygon(rig.scr(np.array([C, A, B, Ib, D]))).buffer(0)
    g = unary_union([hull, web])
    zc = float(rig.z(np.array([c[0], c[1], 0.0])))
    return _elem(name, g, zc, shk=0.06 * S, cast=0.0, hl=0.6, pc=c)


def _thumb_elem(rig, T, name='thumb'):
    S = rig.S
    J = [rig.scr(p) for p in T['j']]
    Z = [float(rig.z(p)) for p in T['j']]
    R = [r * S for r in T['r']]
    segs = [(_capsule(J[k], J[k + 1], R[k], R[k + 1]), (Z[k] + Z[k + 1]) / 2) for k in range(3)]
    g = unary_union([s[0] for s in segs])
    z = float(np.mean([s[1] for s in segs[1:]]))
    return _elem(name, g, z, segs=segs, shk=0.55 * R[2], cast=1.0, hl=1.0, fid=-1, jsc=J, rsc=R)


def _fuse(ea, eb, zone):
    """ea、eb 在 zone 里连成一体：彼此落在对方里面的轮廓不画。"""
    ea['fuse'].append((eb['name'], zone))
    eb['fuse'].append((ea['name'], zone))


# =========================================================================== 手臂 / 袖子
def _arm(rig, sp, wrist, sleeve, sleeve_len, seed, detail):
    """→ (元素列表, 线列表, 前臂元素)。"""
    S = rig.S
    wf, wd = wrist
    Rw = _Rx(wf) @ _Rz(wd)
    a = Rw @ np.array([0.0, -1.0, 0.0])
    u = Rw @ np.array([1.0, 0.0, 0.0])
    v = Rw @ np.array([0.0, 0.0, 1.0])
    o = np.array([0.0, 0.012, 0.0])

    def ring(dist, ax, az, n=30):
        t = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return o + a * dist + np.outer(np.cos(t), u * ax) + np.outer(np.sin(t), v * az)

    def tube_geom(spec):
        rs = [rig.scr(ring(*p)) for p in spec]
        return unary_union([_hull(np.vstack([rs[k], rs[k + 1]])) for k in range(len(rs) - 1)])

    def ctr(dist):
        return o + a * dist

    elems, lines = [], []
    cuff = sp['cuff'] if sleeve else 0.40
    wr, fo = sp['wrist'], sp['fore']
    fspec = [(-0.06, wr[0] * 0.92, wr[1] * 0.95), (0.0, wr[0], wr[1]), (cuff + 0.03, fo[0], fo[1])]
    fore = _elem('forearm', tube_geom(fspec), float(rig.z(ctr(cuff * 0.5))), shk=0.05 * S, cast=0.0, hl=0.5,
                 lw=0.95)
    elems.append(fore)
    if not sleeve:
        return elems, lines, fore, dict(a=a, u=u, v=v, o=o)
    facing_open = float(rig.dirz(-a))         # >0：袖口朝镜头（看得见袖子里面）
    # 衬衫袖口（他）
    if 'shirt' in sp:
        sh = sp['shirt']
        g = tube_geom(sh)
        e = _elem('shirt', g, float(rig.z(ctr((sh[0][0] + sh[1][0]) / 2))), color='boy_shirt', shade_color=None,
                  shade_amt=0.22, shk=0.04 * S, lw=0.9)
        elems.append(e)
        pts = ring(sh[0][0], sh[0][1], sh[0][2], 44)
        lines.append(dict(pts3=pts, closed=True, w=0.85, tone=0.85, role='contour', ignore=('shirt',),
                          front_only=facing_open < 0.15, ring_c=ctr(sh[0][0]), seed=_sk(seed, 'shirt_edge')))
        # 扣子：在朝镜头的一侧
        best = None
        for t in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            nv = math.cos(t) * u + math.sin(t) * v
            f = float(rig.dirz(nv))
            if best is None or f > best[0]:
                best = (f, t)
        t = best[1] + 0.9
        nv = math.cos(t) * u + math.sin(t) * v
        bp = ctr(sh[0][0] + 0.06) + nv * np.array([sh[0][1], sh[0][1], sh[0][1]]) * 1.0
        bp = ctr(sh[0][0] + 0.06) + math.cos(t) * u * sh[0][1] + math.sin(t) * v * sh[0][2]
        if float(rig.dirz(nv)) > 0.25:
            lines.append(dict(dot=bp, r=0.011, ignore=('shirt',), seed=_sk(seed, 'button')))
    # 毛衣袖子：罗纹袖口 + 袖身
    rib_spec, body_spec = sp['sleeve']
    body_spec = [p if p[0] < sleeve_len else (sleeve_len, p[1], p[2]) for p in body_spec]
    body_spec = [p for k, p in enumerate(body_spec) if k == 0 or p[0] > body_spec[k - 1][0]]
    g = unary_union([tube_geom(rib_spec), tube_geom(body_spec)])
    zs = float(rig.z(ctr(rib_spec[0][0] + 0.10)))
    sl = _elem('sleeve', g, zs, color=sp['sleeve_col'], shade_color=sp['sleeve_sh'], shade_amt=0.30,
               shk=0.07 * S, lw=1.0, hl=0.0)
    elems.append(sl)
    d0, ax0, az0 = rib_spec[0]
    # 袖口里面（朝镜头时看得见一圈暗）
    if facing_open > 0.05:
        inner = Polygon(rig.scr(ring(d0 + 0.01, ax0 * 0.90, az0 * 0.86, 40))).buffer(0)
        sl['inner'] = (inner, 0.55 * min(1.0, facing_open * 2.5))
    # 袖口的卷边（粗）+ 罗纹结束处（细）
    lines.append(dict(pts3=ring(d0, ax0, az0, 48), closed=True, w=1.15, tone=0.92, role='contour',
                      ignore=('sleeve',), front_only=facing_open < 0.15, ring_c=ctr(d0), seed=_sk(seed, 'cuff')))
    lines.append(dict(pts3=ring(d0 + 0.022, ax0 * 1.01, az0 * 1.01, 48), closed=True, w=0.45, tone=0.55,
                      role='detail', ignore=('sleeve',), front_only=True, ring_c=ctr(d0 + 0.022),
                      seed=_sk(seed, 'cuff2')))
    d1, ax1, az1 = rib_spec[1]
    lines.append(dict(pts3=ring(d1 - 0.01, ax1 * 1.03, az1 * 1.03, 48), closed=True, w=0.55, tone=0.6,
                      role='detail', ignore=('sleeve',), front_only=True, ring_c=ctr(d1 - 0.01),
                      seed=_sk(seed, 'cuff3')))
    # 罗纹竖线
    if detail > 0.3:
        r0_, r1_, nr = sp['rib']
        for k in range(nr):
            t = 2 * math.pi * (k + 0.5) / nr
            nv = math.cos(t) * u + math.sin(t) * v
            f = float(rig.dirz(nv))
            if f < 0.12:
                continue
            q0 = ctr(r0_ + 0.03) + math.cos(t) * u * ax0 * 1.02 + math.sin(t) * v * az0 * 1.02
            q1 = ctr(r1_ - 0.03) + math.cos(t) * u * ax1 * 1.02 + math.sin(t) * v * az1 * 1.02
            pts = np.array([q0, (q0 + q1) / 2, q1])
            lines.append(dict(pts3=pts, closed=False, w=0.38, tone=0.42 * min(1.0, f * 1.6) * detail,
                              role='detail', ignore=('sleeve',), seed=_sk(seed, 'rib', k), taper=(0.3, 0.3)))
    # 袖身堆在罗纹上面的两三道褶
    if detail > 0.3:
        bd = body_spec[0][0] + 0.03
        r = np.random.default_rng(abs(hash((sp['who'], 'fold'))) % (2 ** 31))
        for k in range(3):
            t0 = 2 * math.pi * (0.10 + 0.27 * k + r.uniform(-0.04, 0.04))
            ts = np.linspace(t0, t0 + 0.9, 6)
            nv = math.cos(t0 + 0.45) * u + math.sin(t0 + 0.45) * v
            if float(rig.dirz(nv)) < 0.2:
                continue
            dd = bd + 0.02 * k + 0.03 * np.sin(np.linspace(0, math.pi, 6))
            pts = np.array([ctr(di) + math.cos(ti) * u * body_spec[0][1] * 1.0 + math.sin(ti) * v * body_spec[0][2]
                            for di, ti in zip(dd, ts)])
            lines.append(dict(pts3=pts, closed=False, w=0.5, tone=0.5, role='detail', ignore=('sleeve',),
                              seed=_sk(seed, 'fold', k), taper=(0.35, 0.45)))
    # 前臂伸进袖口的那一截不画端线
    opening = Polygon(rig.scr(ring(cuff + 0.005, wr[0] * 1.6, wr[1] * 2.2, 40))).buffer(0)
    fore['drop'].append(opening)
    return elems, lines, fore, dict(a=a, u=u, v=v, o=o)


# =========================================================================== 细节：指甲、褶纹、掌纹
def _finger_details(rig, F, owners, detail, knuck=0.5, nail=True):
    """owners：三节各自归哪个元素（拆开的手指前后段不同）。"""
    S = rig.S
    out = []
    j, frs, R = F['j'], F['fr'], F['r']
    for k in range(3):
        d, n = frs[k]
        side = _nz(np.cross(d, n))
        fd = float(rig.dirz(n))           # 手背朝镜头
        fp = -fd                          # 指腹朝镜头
        # 远节：指甲
        if k == 2 and nail and fd > 0.12 and detail > 0.2:
            L3 = F['L'][2]
            r = R[2] * 0.98
            a0, a1 = 0.36, 0.93
            ts = np.linspace(-1, 1, 7)
            ang = ts * 0.95
            base = [j[2] + d * (L3 * a0) + (n * math.cos(q) + side * math.sin(q)) * r for q in ang]
            free = [j[2] + d * (L3 * a1) + (n * math.cos(q) + side * math.sin(q)) * r * 0.98 for q in ang]
            P = np.array([free[0]] + [j[2] + d * (L3 * (a0 + 0.5 * (a1 - a0))) + (n * math.cos(ang[0]) + side *
                                                                                  math.sin(ang[0])) * r]
                         + base + [j[2] + d * (L3 * (a0 + 0.5 * (a1 - a0))) + (n * math.cos(ang[-1]) + side *
                                                                               math.sin(ang[-1])) * r] + [free[-1]])
            vis = min(1.0, (fd - 0.12) / 0.3)
            out.append(dict(pts=rig.scr(P), owner=owners[2], w=0.36, tone=0.55 * vis, role='detail', taper=(0.35, 0.35),
                            inset=0.8))
            # 甲面一点高光
            hp = np.array([j[2] + d * (L3 * (a0 + 0.12)) + (n * math.cos(q) + side * math.sin(q)) * r * 1.0
                           for q in np.linspace(-0.55, -0.05, 4)])
            out.append(dict(lift=rig.scr(hp), owner=owners[2], w=0.022 * S * vis, amt=0.45 * vis))
        if k == 0:
            continue
        jp = j[k]        # 关节（近指间 k=1 / 远指间 k=2）
        dprev = frs[k - 1][0]
        dm = _nz(dprev + d)
        nm = _nz(frs[k - 1][1] + n)
        sm = _nz(np.cross(dm, nm))
        r = R[k]
        if fd > 0.2 and detail > 0.3:
            # 手背一侧的指节皱纹（近指间两三道小弧，远指间一道）
            nlines = 2 if k == 1 else 1
            for q in range(nlines):
                off = (q - 0.5 * (nlines - 1)) * r * 0.42
                c = jp + dm * off + nm * r * 0.98
                ww = r * (0.55 - 0.12 * q)
                P = np.array([c - sm * ww + nm * (-0.12 * r) + dm * 0.08 * r, c + dm * 0.16 * r,
                              c + sm * ww + nm * (-0.12 * r) + dm * 0.08 * r])
                vis = min(1.0, (fd - 0.2) / 0.3)
                out.append(dict(pts=rig.scr(P), owner=owners[k], w=0.30, tone=(0.42 + 0.15 * knuck) * vis * detail,
                                role='detail', taper=(0.35, 0.4), inset=0.5))
        if fp > 0.2 and detail > 0.3:
            # 掌面一侧的屈纹
            nlines = 2 if k == 1 else 1
            for q in range(nlines):
                off = (q - 0.5 * (nlines - 1)) * r * 0.30
                c = jp + dm * off - nm * r * 0.98
                ww = r * 0.62
                P = np.array([c - sm * ww + nm * 0.15 * r, c - dm * 0.06 * r, c + sm * ww + nm * 0.15 * r])
                vis = min(1.0, (fp - 0.2) / 0.3)
                out.append(dict(pts=rig.scr(P), owner=owners[k], w=0.30, tone=0.42 * vis * detail, role='detail',
                                taper=(0.35, 0.4), inset=0.6))
    # 指根（掌面）的指横纹
    d, n = frs[0]
    fp = -float(rig.dirz(n))
    if fp > 0.25 and detail > 0.3:
        sm = _nz(np.cross(d, n))
        c = j[0] + d * F['L'][0] * 0.22 - n * R[0] * 0.95
        P = np.array([c - sm * R[0] * 0.7, c - d * 0.01, c + sm * R[0] * 0.7])
        out.append(dict(pts=rig.scr(P), owner=owners[0], w=0.30, tone=0.36 * detail, role='detail', taper=(0.4, 0.4),
                        inset=0.6))
    return out


def _palm_details(rig, sp, T, detail):
    """掌纹（掌心朝镜头时）、手背的掌骨头（指节）小弧。"""
    out = []
    z = -sp['zb'] - 0.002
    fpalm = float(rig.dirz(np.array([0.0, 0.0, -1.0])))
    if fpalm > 0.2 and detail > 0.3:
        vis = min(1.0, (fpalm - 0.2) / 0.35) * detail
        kx = sp['palm'][3][0] / -0.170
        lines = [
            # 感情线（小指一侧 → 食指与中指之间）
            ([(-0.170, 0.360), (-0.10, 0.385), (-0.02, 0.398), (0.05, 0.418), (0.082, 0.442)], 0.36, 0.50),
            # 智慧线
            ([(0.148, 0.300), (0.08, 0.292), (0.0, 0.272), (-0.08, 0.240), (-0.125, 0.205)], 0.36, 0.48),
            # 生命线（绕着大鱼际）
            ([(0.150, 0.305), (0.098, 0.262), (0.068, 0.200), (0.060, 0.130), (0.072, 0.060)], 0.40, 0.55),
            # 一道很淡的竖纹
            ([(-0.010, 0.070), (-0.005, 0.160), (0.006, 0.240)], 0.26, 0.28),
        ]
        for pts, w, tn in lines:
            P = np.array([(x * kx, y, z) for x, y in pts])
            out.append(dict(pts=rig.scr(P), owner='palm', w=w, tone=tn * vis, role='detail', taper=(0.4, 0.5),
                            inset=0.8))
        # 腕横纹
        P = np.array([(-0.10 * kx, 0.018, z), (0.0, 0.010, z), (0.09 * kx, 0.016, z)])
        out.append(dict(pts=rig.scr(P), owner='palm', w=0.28, tone=0.30 * vis, role='detail', taper=(0.4, 0.4),
                        inset=0.6))
    return out


def _knuckle_details(rig, sp, F, detail, knuck):
    """手背朝镜头、手指弯下去时：掌骨头（拳峰）的小弧，和伸肌腱的一两道淡线。"""
    out = []
    fd = float(rig.dirz(np.array([0.0, 0.0, 1.0])))
    if fd < 0.15 or detail < 0.3:
        return out
    vis = min(1.0, (fd - 0.15) / 0.3) * detail
    for f in F:
        d, n = f['fr'][0]
        bend = max(0.0, float(np.dot(d, np.array([0.0, 1.0, 0.0])) < 0.98))
        r = f['r'][0]
        c = f['j'][0] + np.array([0.0, 0.0, sp['zt'] * 0.9]) + np.array([0.0, -0.01, 0.0])
        k = 0.35 + 0.65 * min(1.0, max(0.0, 1.0 - float(d[1])) * 3.0)
        q = np.linspace(-1, 1, 7)
        P = np.array([c + np.array([r * 0.62 * a, 0.006 - 0.016 * a * a, 0.004 * (1 - a * a)]) for a in q])
        out.append(dict(pts=rig.scr(P), owner='palm', w=0.32, tone=(0.25 + 0.3 * knuck) * k * vis, role='detail',
                        taper=(0.35, 0.4), inset=0.5))
        if f['i'] in (0, 1, 2) and knuck > 0.7:
            q0 = np.array([f['j'][0][0] * 0.7, 0.26, sp['zt']])
            q1 = f['j'][0] + np.array([0.0, -0.06, sp['zt'] * 0.9])
            out.append(dict(pts=rig.scr(np.array([q0, (q0 + q1) / 2 + np.array([0, 0, 0.004]), q1])),
                            owner='palm', w=0.24, tone=0.14 * vis, role='detail', taper=(0.5, 0.5), inset=0.8))
    return out


# =========================================================================== 红豆
def _bean_elem(rig, c3, r, name='bean', rot=-25.0, z=None):
    S = rig.S
    c = rig.scr(c3)
    rx, ry = r * S * 1.16, r * S * 0.84
    g = Polygon(ell(c[0], c[1], rx, ry, 0, 360, 36, rot=rot)).buffer(0)
    zz = float(rig.z(c3)) if z is None else z
    e = _elem(name, g, zz, color='bean', shade_color='bean_d', shade_amt=0.55, shk=0.45 * ry, lcolor='bean_d',
              lw=0.55, ltone=1.0, cast=1.4, hl=0.0, bean=(c, rx, ry, rot))
    return e


# =========================================================================== 渲染
def _normals(P, geom):
    n = len(P)
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    N = np.stack([T[:, 1], -T[:, 0]], 1)
    N /= (np.hypot(N[:, 0], N[:, 1])[:, None] + 1e-9)
    probe = P + N * 1.5
    ins = _contains(geom, probe)
    if ins.mean() > 0.5:
        N = -N
    return N


def _smooth1(f, k=3, closed=True):
    if len(f) < 3:
        return f
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    if closed:
        ff = np.concatenate([f[-k:], f, f[:k]])
        return np.convolve(ff, ker, 'valid')
    ff = np.concatenate([np.full(k, f[0]), f, np.full(k, f[-1])])
    return np.convolve(ff, ker, 'valid')


class _Ctx:
    def __init__(self, pen, S, seed, Lv, lw_px, detail, hints):
        self.pen, self.S, self.seed, self.Lv, self.lw, self.detail, self.hints = pen, S, seed, Lv, lw_px, detail, hints


def _stroke_outline(cx, P, keep, N, w, tone, seed, color=None, closed=True):
    """一圈轮廓（keep 标出可见的点）→ 若干笔：按受光方向分轻重。"""
    pen = cx.pen
    n = len(P)
    if n < 3:
        return
    f = _smooth1(N @ (-cx.Lv), 3, closed)
    if closed:
        if keep.all():
            k0 = int(np.argmin(f))
            P, N, keep, f = (np.roll(P, -k0, 0), np.roll(N, -k0, 0), np.roll(keep, -k0), np.roll(f, -k0))
            P = np.vstack([P, P[:2]])
            f = np.concatenate([f, f[:2]])
            keep = np.ones(len(P), bool)
            runs = [(0, len(P), False, False)]
        else:
            k0 = int(np.argmin(keep))
            P, keep, f = np.roll(P, -k0, 0), np.roll(keep, -k0), np.roll(f, -k0)
            runs = _runs(keep)
    else:
        runs = _runs(keep)
    for ri, (a, b, ca, cb) in enumerate(runs):
        seg = P[a:b]
        ff = f[a:b]
        cls = np.where(ff > 0.22, 2, np.where(ff < -0.40, 0, 1))
        # 分段（短段并入前一段）
        cuts = [0]
        for i in range(1, len(cls)):
            if cls[i] != cls[cuts[-1]] and i - cuts[-1] >= 5:
                cuts.append(i)
        cuts.append(len(cls))
        if len(cuts) > 2 and cuts[-1] - cuts[-2] < 5:
            cuts.pop(-2)
        for si in range(len(cuts) - 1):
            i0, i1 = cuts[si], cuts[si + 1]
            i0e, i1e = max(0, i0 - 1), min(len(seg), i1 + 1)
            sub = seg[i0e:i1e]
            if len(sub) < 2:
                continue
            c = int(np.round(np.mean(cls[i0:i1])))
            wk, tk = {2: (1.04, 0.90), 1: (0.86, 0.82), 0: (0.58, 0.64)}[c]
            t0 = (0.03 if ca else 0.16) if si == 0 else 0.06
            t1 = (0.03 if cb else 0.22) if si == len(cuts) - 2 else 0.06
            pen.line(sub, max(1.2, w * wk), tone=tone * tk, color=color, seed=_sk(seed, ri, si), taper=(t0, t1),
                     role='contour', head=0.32, lift=0.12, dry=0.18, dry_from=0.6, streak=0.12, pool=0.08,
                     **cx.hints)


def _point_hidden(P, zs, segs_all, ignore, eps):
    hid = np.zeros(len(P), bool)
    for name, g, z in segs_all:
        if name in ignore:
            continue
        m = _contains(g, P)
        if m.any():
            hid |= m & (z > zs + eps)
    return hid


def _render(pen, rig, elems, lines, seed, light=(-0.55, -0.83), detail=1.0, backlit=0.0, hint=None,
            extra=None):
    """elems：元素列表（见 _elem）；lines：细节线 / 3D 线。extra(pen, ctx) 在轮廓线之前调用（场景特效）。"""
    S = rig.S
    Lv = _nz(np.array(light, np.float64))
    lw_px = max(1.5, 0.0128 * S * rig.sp['lw'])
    hints = dict(hint or {})
    cx = _Ctx(pen, S, seed, Lv, lw_px, detail, hints)
    el = sorted([e for e in elems if not e['geom'].is_empty], key=lambda e: e['z'])
    n = len(el)
    byname = {e['name']: e for e in el}
    for e in el:
        shapely.prepare(e['geom'])
    nearer = [None] * n
    acc = None
    for i in range(n - 1, -1, -1):
        nearer[i] = acc
        acc = el[i]['geom'] if acc is None else acc.union(el[i]['geom'])
    allg = acc
    farther = [None] * n
    acc = None
    for i in range(n):
        farther[i] = acc
        acc = el[i]['geom'] if acc is None else acc.union(el[i]['geom'])
    vis = [e['geom'] if nearer[i] is None else _valid(e['geom'].difference(nearer[i])) for i, e in enumerate(el)]
    for i, e in enumerate(el):
        e['vis'] = vis[i]
    # ---- 1. 剪影挖空 + 一层肤色
    ex, ho = _pp(allg)
    if not ex:
        return allg
    pen.cover(ex, holes=ho, seed=_sk(seed, 'cov'), feather=0.7)
    skin = unary_union([e['geom'] for e in el if e['color'] == 'skin'])
    sx, sh_ = _pp(skin)
    if sx:
        bx0, by0, bx1, by1 = skin.bounds
        pen.fill(sx, 'skin', holes=sh_, seed=_sk(seed, 'skin'), c_fade=False, rim=0.12, bloom=0.0, b_clean=True,
                 rgrad=((bx0 + bx1) / 2 + Lv[0] * (bx1 - bx0) * 0.3, (by0 + by1) / 2 + Lv[1] * (by1 - by0) * 0.3,
                        0.0, max(bx1 - bx0, by1 - by0) * 0.9, 0.85, 1.12))
    # ---- 2. 实物（袖子、衬衫、笔、红豆…）
    for i, e in enumerate(el):
        if e['color'] == 'skin':
            continue
        px, ph = _pp(e['vis'])
        if not px:
            continue
        pen.cover(px, holes=ph, seed=_sk(seed, e['name'], 'c'), feather=0.6)
        pen.fill(px, e['color'], holes=ph, seed=_sk(seed, e['name'], 'f'), c_fade=False,
                 **dict(dict(b_clean=True), **e['fill_kw']))
    # ---- 3. 体积阴影 + 投影
    for i, e in enumerate(el):
        g, v = e['geom'], e['vis']
        if v.is_empty:
            continue
        k = e['shk'] if e['shk'] is not None else 0.03 * S
        if e['shade_amt'] > 0 and k > 0.5:
            cres = _valid(g.difference(affinity.translate(g, Lv[0] * k, Lv[1] * k))).intersection(v)
            px, ph = _pp(cres, 6.0)
            if px:
                pen.shade(px, holes=ph, amount=e['shade_amt'], color=e['shade_color'], seed=_sk(seed, e['name'], 's'),
                          angle=math.degrees(math.atan2(Lv[1], Lv[0])) + 90, soft=max(1.5, 0.15 * k))
        if 'inner' in e:
            ig, amt = e['inner']
            px, ph = _pp(_valid(ig.intersection(v)), 6.0)
            if px:
                pen.shade(px, holes=ph, amount=amt, color=e['shade_color'], seed=_sk(seed, e['name'], 'in'),
                          soft=3.0)
        if e['cast'] > 0 and farther[i] is not None:
            kc = 0.026 * S * e['cast']
            sg = affinity.translate(g, -Lv[0] * kc, -Lv[1] * kc)
            blk = g if nearer[i] is None else g.union(nearer[i])
            cs = _valid(sg.intersection(farther[i]).difference(blk))
            px, ph = _pp(cs, 8.0)
            if px:
                pen.shade(px, holes=ph, amount=0.20, color='skin_sh', seed=_sk(seed, e['name'], 'cs'),
                          soft=max(2.0, 0.006 * S))
    # ---- 4. 逆光（整体压暗 + 朝光的边镶金边）/ 受光边提白
    if backlit > 0:
        inner = _valid(allg.buffer(-0.009 * S))
        px, ph = _pp(inner, 10.0)
        if px:
            if pen.style == 'B':
                pen.shade(px, holes=ph, amount=0.28 * backlit, color='#5A3A6E', seed=_sk(seed, 'bl'))
            else:
                pen.shade(px, holes=ph, amount=0.14 * backlit, seed=_sk(seed, 'bl'), angle=80, soft=3.0)
    for i, e in enumerate(el):
        g, v = e['geom'], e['vis']
        if v.is_empty:
            continue
        if backlit > 0 and e['rim'] > 0:
            k = 0.010 * S
            rim = _valid(allg.difference(affinity.translate(allg, -Lv[0] * k, -Lv[1] * k))).intersection(v)
            px, ph = _pp(rim, 2.0)
            if px:
                if pen.style == 'B':
                    pen.fill(px, '#FFA640', holes=ph, seed=_sk(seed, e['name'], 'rim'), b_clean=True, b_size=0.5,
                             c_fade=False)
                    pen.lift(px, holes=ph, amt=0.30 * backlit, seed=_sk(seed, e['name'], 'rl'), soft=0.5)
                else:
                    pen.lift(px, holes=ph, amt=0.75 * backlit, seed=_sk(seed, e['name'], 'rl'), soft=0.6)
        elif e['hl'] > 0 and backlit <= 0:
            k = (e['shk'] or 0.02 * S) * 0.6
            lit = _valid(g.difference(affinity.translate(g, -Lv[0] * k, -Lv[1] * k))).intersection(v)
            lit = _valid(lit.buffer(-0.22 * k).buffer(0.08 * k))
            px, ph = _pp(lit, 6.0)
            if px:
                pen.lift(px, holes=ph, amt=0.28 * e['hl'], seed=_sk(seed, e['name'], 'hl'), soft=max(1.0, 0.2 * k))
    # ---- 5. 红豆：暗部、高光、豆脐
    for e in el:
        if 'bean' not in e or e['vis'].is_empty:
            continue
        c, rx, ry, rot = e['bean']
        hx, hy = c[0] + Lv[0] * rx * 0.38, c[1] + Lv[1] * ry * 0.42
        hlp = Polygon(ell(hx, hy, rx * 0.30, ry * 0.20, 0, 360, 16, rot=rot)).intersection(e['vis'])
        px, ph = _pp(hlp, 1.0)
        if px:
            pen.lift(px, amt=0.85, seed=_sk(seed, e['name'], 'h'), soft=max(0.6, 0.06 * rx))
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        p0 = (c[0] - 0.05 * rx * ca - 0.55 * ry * -sa, c[1] - 0.05 * rx * sa - 0.55 * ry * ca)
        hil = Polygon(ell(p0[0], p0[1], rx * 0.30, ry * 0.09, 0, 360, 14, rot=rot)).intersection(e['vis'])
        px, ph = _pp(hil, 1.0)
        if px and rx > 6:
            pen.lift(px, amt=0.55, seed=_sk(seed, e['name'], 'eye'), soft=0.6)
    if extra is not None:
        extra(pen, cx)
    # ---- 6. 细节线（指甲、褶纹、掌纹、3D 线）
    segs_all = []
    for e in el:
        for g, z in e['segs']:
            segs_all.append((e['name'], g, z))
    idx = {e['name']: i for i, e in enumerate(el)}
    for k, L in enumerate(lines):
        if 'pts3' in L:
            P3 = np.asarray(L['pts3'], np.float64)
            P = rig.scr(P3)
            zs = rig.z(P3)
            closed = L.get('closed', False)
            if closed:
                P = np.vstack([P, P[:1]])
                zs = np.append(zs, zs[:1])
            sp_ = max(1.5, 0.008 * S)
            # 加密（深度跟着插值）
            seg = np.hypot(*np.diff(P, axis=0).T)
            s = np.concatenate([[0.0], np.cumsum(seg)])
            m = max(2, int(s[-1] / sp_) + 1)
            tt = np.linspace(0, s[-1], m)
            P = np.stack([np.interp(tt, s, P[:, 0]), np.interp(tt, s, P[:, 1])], 1)
            zs = np.interp(tt, s, zs)
            keep = ~_point_hidden(P, zs, segs_all, L.get('ignore', ()), 0.004 * S)
            if L.get('front_only'):
                rc = L.get('ring_c')
                zc = float(rig.z(rc)) if rc is not None else float(np.mean(zs))
                keep &= zs >= zc - 0.002 * S
            if L.get('keep_extra') is not None:
                keep &= L['keep_extra'](P)
            w = lw_px * L.get('w', 0.5)
            tp = L.get('taper', (0.12, 0.2))
            for ri, (a, b, ca, cb) in enumerate(_runs(keep, 3)):
                sub = P[a:b]
                pen.line(sub, w, tone=L.get('tone', 0.8), color=L.get('color'), seed=_sk(L.get('seed', seed), ri),
                         taper=(0.03 if ca else tp[0], 0.03 if cb else tp[1]), role=L.get('role', 'detail'),
                         **dict(hints, **L.get('hints', {})))
            continue
        if 'dot' in L:
            p3 = np.asarray(L['dot'], np.float64)
            P = rig.scr(p3)[None]
            if _point_hidden(P, np.array([rig.z(p3)]), segs_all, L.get('ignore', ()), 0.004 * S)[0]:
                continue
            pen.dot(float(P[0, 0]), float(P[0, 1]), L['r'] * S, color=L.get('color', 'ink'), tone=0.7,
                    seed=L.get('seed', seed))
            continue
        own = L.get('owner')
        if own is not None and own not in idx:
            continue
        i = idx.get(own)
        P = np.asarray(L.get('pts', L.get('lift')), np.float64)
        sp_ = max(1.5, 0.006 * S)
        P = _resample(P, sp_, closed=False) if len(P) > 1 else P
        keep = np.ones(len(P), bool)
        if i is not None:
            if nearer[i] is not None:
                keep &= ~_contains(nearer[i], P)
            ins = L.get('inset', 0.0)
            if ins > 0:
                keep &= _contains(_valid(el[i]['geom'].buffer(-ins * lw_px)), P)
        if 'lift' in L:
            if keep.sum() >= 2:
                q = P[keep]
                tb = _valid(Polygon(np.vstack([q + 0.5 * L['w'] * np.array([0, 1.0]), (q - 0.5 * L['w'] *
                                                                                       np.array([0, 1.0]))[::-1]])))
                tb = tb.buffer(0.3 * L['w'])
                px, ph = _pp(tb, 1.0)
                if px:
                    pen.lift(px, amt=L.get('amt', 0.4), seed=_sk(seed, 'lf', k), soft=max(0.6, 0.25 * L['w']))
            continue
        w = lw_px * L.get('w', 0.4)
        tp = L.get('taper', (0.2, 0.3))
        for ri, (a, b, ca, cb) in enumerate(_runs(keep, 2)):
            pen.line(P[a:b], max(1.0, w), tone=L.get('tone', 0.6), color=L.get('color'), seed=_sk(seed, 'dl', k, ri),
                     taper=(0.05 if ca else tp[0], 0.05 if cb else tp[1]), role=L.get('role', 'detail'),
                     head=0.15, lift=0.1, dry=0.1, **hints)
    # ---- 7. 轮廓线
    for i, e in enumerate(el):
        g = e['geom']
        hide = None if nearer[i] is None else nearer[i].buffer(0.45 * lw_px)
        fz = []
        for oname, zone in e['fuse']:
            if oname in byname:
                fz.append(_valid(byname[oname]['geom'].buffer(0.6 * lw_px).intersection(zone)))
        for q in _polys(g, 4.0):
            for ring in [q.exterior] + list(q.interiors):
                R0 = np.asarray(ring.coords, np.float64)[:-1]
                P = _resample(R0, max(1.6, 0.010 * S), closed=True)
                if len(P) < 4:
                    continue
                keep = np.ones(len(P), bool)
                if hide is not None:
                    keep &= ~_contains(hide, P)
                for z_ in fz:
                    keep &= ~_contains(z_, P)
                for dz in e['drop']:
                    keep &= ~_contains(dz, P)
                if not keep.any():
                    continue
                N = _normals(P, g)
                _stroke_outline(cx, P, keep, N, lw_px * e['lw'], 0.88 * e['ltone'], _sk(seed, e['name'], 'o'),
                                color=e['lcolor'])
    return allg


# =========================================================================== 组装
def _hand_elems(rig, sp, F, T, seed, detail, sleeve=True, sleeve_len=0.9, wrist=(0.0, 0.0), prefix='',
                split=None, zoff=None, nails=True):
    """一整只手的元素和细节线。split={手指序号: 拆分节}、zoff={手指序号: (z 偏移…)}：勾手指时的前后交错。"""
    S = rig.S
    split = split or {}
    zoff = zoff or {}
    names = ['index', 'middle', 'ring', 'pinky']
    elems, lines = [], []
    palm = _palm_elem(rig, sp, F, T, prefix + 'palm')
    elems.append(palm)
    fe = []
    for f in F:
        es = _finger_elems(rig, f, prefix + names[f['i']], split.get(f['i']))
        fe.append(es)
        elems.extend(es)
        R0 = f['r'][0] * S
        zone = Polygon(_circle(rig.scr(f['j'][0]), R0 * 1.55, 24))
        _fuse(es[0], palm, zone)
    th = _thumb_elem(rig, T, prefix + 'thumb')
    elems.append(th)
    tz = _capsule(rig.scr(T['j'][0]), rig.scr(T['j'][1]), T['r'][0] * S * 1.25, T['r'][1] * S * 1.45)
    _fuse(th, palm, tz)
    # 相邻手指在指根处并在一起时也不要描出指根的小圆弧
    arm_e, arm_l, fore, af = _arm(rig, sp, wrist, sleeve, sleeve_len, seed, detail)
    for e in arm_e:
        e['name'] = prefix + e['name']
        e['fuse'] = []
    for L in arm_l:
        L['ignore'] = tuple(prefix + x for x in L.get('ignore', ()))
    elems.extend(arm_e)
    lines.extend(arm_l)
    wz = Polygon(_circle(rig.scr(np.array([0.0, 0.0, 0.0])), 0.24 * S, 32))
    _fuse(fore, palm, wz)
    tz2 = Polygon(_circle(rig.scr(np.array(sp['tb'])), T['r'][0] * S * 1.6, 24))
    _fuse(fore, th, tz2.union(wz))
    # 细节
    if detail > 0.05:
        for f, es in zip(F, fe):
            owners = [next(e['name'] for e in es if e['krange'][0] <= k < e['krange'][1]) for k in range(3)]
            lines.extend(_finger_details(rig, f, owners, detail, sp['knuck'], nail=nails))
        for L in _finger_details(rig, T, [th['name']] * 3, detail, sp['knuck'], nail=nails):
            lines.append(L)
        for L in _palm_details(rig, sp, T, detail) + _knuckle_details(rig, sp, F, detail, sp['knuck']):
            L['owner'] = prefix + L['owner']
            lines.append(L)
    return elems, lines, dict(palm=palm, fingers=fe, thumb=th, fore=fore, arm=af)


def _info(rig, F, T, allg):
    tips = [rig.scr(T['j'][-1])] + [rig.scr(f['j'][-1]) for f in F]
    ex, _ = _pp(allg)
    return dict(tips=[tuple(map(float, p)) for p in tips], wrist=tuple(map(float, rig.scr(np.zeros(3)))),
                sil=ex, M=rig.M, S=rig.S)


def _group(pen, name, group, boil):
    if group:
        return pen.group(name, boil=boil)
    return _nullctx()


def _size(size, who):
    if size is None:
        return 420.0 * (1.12 if who == 'boy' else 1.0)
    return float(size)


def _detail(detail, S):
    return float(detail) * float(np.clip((S - 70.0) / 110.0, 0.0, 1.0))


# =========================================================================== 1. 摊开的掌心
_PU_REST = [(4, 10, 16, 8), (0, 12, 19, 9), (-4, 15, 23, 11), (-9, 19, 27, 13)]
_PU_CUP = [(2, 58, 80, 44), (0, 62, 84, 46), (-2, 66, 88, 48), (-5, 70, 90, 50)]
_PU_TH_REST = (40, 38, 76, 0, 8, 14)
_PU_TH_CUP = (34, 50, 86, 10, 22, 30)


def palm_up(pen, x, y, rot=0.0, size=None, seed=0, cup=0.0, tilt=40.0, yaw=0.0, flip=False, who='girl',
            bean=None, bean_r=0.042, light=(-0.55, -0.83), sleeve=True, sleeve_len=0.9, wrist=(0.0, 0.0),
            boil=None, group=True, detail=1.0):
    """她摊开的掌心（见模块说明 1）。返回 info['palm'] 掌心中心、info['bean'] 红豆中心。"""
    sp = _spec(who)
    S = _size(size, who)
    det = _detail(detail, S)
    c = clamp(float(cup))
    fingers = []
    for i, (a, b) in enumerate(zip(_PU_REST, _PU_CUP)):
        ci = ease_io(clamp((c - 0.07 * (3 - i)) / 0.79))         # 小指先动，食指最后
        fingers.append(_mix(a, b, ci))
    th = _mix(_PU_TH_REST, _PU_TH_CUP, ease_io(clamp((c - 0.1) / 0.9)))
    F, T = _skeleton(sp, fingers, th)
    M = orient(rot, tilt, 180.0 + yaw)
    pc = np.array([0.0, 0.265, -sp['zb']])
    rig = _Rig(sp, M, S, flip, pc, (x, y))
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist)
    binfo = None
    if bean is not None and bean is not False:
        bx, by = (0.0, -0.01) if bean is True else (float(bean[0]), float(bean[1]))
        c3 = np.array([bx, 0.265 + by, -sp['zb'] - bean_r * 0.80])
        be = _bean_elem(rig, c3, bean_r, rot=-25.0 + rot)
        # 红豆的深度：在掌面上方；弯下来的手指在它前面
        be['z'] = float(rig.z(c3))
        be['segs'] = [(be['geom'], be['z'])]
        elems.append(be)
        binfo = be
    with _group(pen, 'hand_palm_up', group, boil):
        allg = _render(pen, rig, elems, lines, seed, light, det)
    info = _info(rig, F, T, allg)
    info['palm'] = tuple(map(float, rig.scr(pc)))
    info['bean'] = None if binfo is None else tuple(map(float, binfo['bean'][0]))
    info['bean_r'] = 0.0 if binfo is None else float(bean_r * S)
    return info


# =========================================================================== 2. 握笔
_PEN_F = [(1, 26, 40, 16), (-3, 44, 60, 26), (-8, 58, 82, 42), (-14, 64, 88, 44)]


def hand_pen(pen, x, y, rot=0.0, size=None, seed=0, lift=0.0, yaw=38.0, pitch=10.0, flip=False, who='girl',
             pen_len=0.62, pen_color='ink', pen_r=0.021, light=(-0.55, -0.83), sleeve=True, sleeve_len=0.9,
             wrist=(-12.0, 4.0), boil=None, group=True, detail=1.0):
    """她握着笔写字（见模块说明 2）。(x, y) = 笔尖。返回 info['tip']、info['pen_back']。"""
    sp = _spec(who)
    S = _size(size, who)
    det = _detail(detail, S)
    lf = clamp(float(lift))
    fingers = [list(f) for f in _PEN_F]
    fingers[0][2] -= 6 * lf
    F0 = [_finger(sp, i, *f) for i, f in enumerate(fingers)]
    # 笔：压在食指远节指腹下，靠在虎口（食指掌指关节的拇指一侧）
    f = F0[0]
    d3, n3 = f['fr'][2]
    s3 = _nz(np.cross(d3, n3))
    r3 = f['r'][2]
    pad = f['j'][2] + d3 * f['L'][2] * 0.52 - n3 * r3 * 0.85 + s3 * r3 * 0.35
    pc_ = pad - n3 * pen_r * 1.05
    d1, n1 = f['fr'][0]
    s1 = _nz(np.cross(d1, n1))
    web = f['j'][0] + s1 * (f['r'][0] + pen_r) * 0.95 + n1 * 0.006 - d1 * 0.02
    u = _nz(pc_ - web)
    tip = pc_ + u * 0.21
    back = web - u * (pen_len - 0.21 - float(np.linalg.norm(pc_ - web)))
    # 拇指：指腹贴在笔杆另一侧（比食指稍靠后）
    tgt = pc_ - u * 0.055 + s3 * pen_r * 1.3 - n3 * pen_r * 0.9
    roll = 80.0
    tflex = (6.0, 16.0, 18.0 + 6 * lf)
    az, el = _thumb_ik(sp, tgt, roll, tflex, az=(-10, 70), el=(0, 80), pad=sp['tr'][3] * 0.7)
    T = _thumb(sp, az, el, roll, *tflex)
    F = F0
    M = orient(rot - 45.0, pitch - 8.0 * lf, yaw)
    rig = _Rig(sp, M, S, flip, tip, (x, y))
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist)
    # 笔的元素
    cone0 = tip - u * 0.0
    cone1 = tip - u * 0.075
    grip1 = tip - u * 0.20
    a_, b_ = rig.scr(cone1), rig.scr(back)
    rp = pen_r * S
    body = _capsule(a_, b_, rp * 0.92, rp)
    cone = _hull(np.vstack([_circle(rig.scr(cone0), max(1.0, rp * 0.16), 10), _circle(a_, rp * 0.88, 16)]))
    gpen = unary_union([body, cone])
    zpen = float(rig.z((pc_ + web) / 2))
    pe = _elem('pen', gpen, zpen, color=pen_color, shade_color=None, shade_amt=0.35, shk=0.5 * rp, lw=0.8,
               ltone=1.0, cast=1.0, hl=0.0, fill_kw=dict(tone=0.62) if pen_color == 'ink' else {})
    pe['segs'] = [(body, float(rig.z((cone1 + back) / 2))), (cone, float(rig.z(cone1)))]
    elems.append(pe)
    # 笔杆上的高光、握笔处的一圈、笔夹
    hl_a = rig.scr(cone1 - u * 0.02)
    hl_b = rig.scr(back + u * 0.04)
    nrm = np.array([-(hl_b - hl_a)[1], (hl_b - hl_a)[0]])
    nrm = nrm / (np.linalg.norm(nrm) + 1e-9)
    if np.dot(nrm, np.asarray(light)) < 0:
        nrm = -nrm
    hl_line = np.array([hl_a + nrm * rp * 0.45, hl_b + nrm * rp * 0.45])
    pe['hl_line'] = hl_line
    for dd in (0.205, 0.215):
        q = tip - u * dd
        lines.append(dict(pts3=np.array([q + s3 * pen_r * 1.05, q + n3 * pen_r * 1.0, q - s3 * pen_r * 1.05]),
                          closed=False, w=0.35, tone=0.7, role='detail', ignore=('pen',), seed=_sk(seed, 'pring', dd)))
    clip0 = back + u * 0.02 + n3 * pen_r * 1.05
    clip1 = back + u * 0.17 + n3 * pen_r * 1.05

    def extra(pen_, cx):
        # 笔杆受光的一道高光（提白）
        e = pe
        if e.get('vis') is None or e['vis'].is_empty:
            return
        tb = Polygon(np.vstack([hl_line[0] + nrm * 1.2, hl_line[1] + nrm * 1.2, hl_line[1] - nrm * 1.6,
                                hl_line[0] - nrm * 1.6])).buffer(0).intersection(e['vis'])
        px, ph = _pp(tb, 1.0)
        if px:
            pen_.lift(px, amt=0.55, seed=_sk(seed, 'penhl'), soft=1.0)

    lines.append(dict(pts3=np.array([clip0, (clip0 + clip1) / 2 + n3 * 0.004, clip1]), closed=False, w=0.55,
                      tone=0.85, role='contour', ignore=('pen',), seed=_sk(seed, 'clip')))
    with _group(pen, 'hand_pen', group, boil):
        allg = _render(pen, rig, elems, lines, seed, light, det, extra=extra)
    info = _info(rig, F, T, allg)
    info['tip'] = (float(x), float(y))
    info['pen_back'] = tuple(map(float, rig.scr(back)))
    return info


# =========================================================================== 3. 握住马克杯把手
_GRIP_OPEN = [(8, 14, 18, 8), (1, 16, 20, 9), (-5, 18, 22, 10), (-12, 20, 24, 10)]
_GRIP_HOLD = [(2, 62, 98, 62), (0, 66, 100, 64), (-3, 74, 104, 64), (-7, 80, 106, 62)]


def hand_grip(pen, x, y, rot=0.0, size=None, seed=0, reach=1.0, frm=(-0.85, 0.10), yaw=28.0, pitch=-10.0,
              flip=False, who='girl', bar_r=0.034, light=(-0.55, -0.83), sleeve=True, sleeve_len=0.9,
              wrist=(4.0, -6.0), boil=None, group=True, detail=1.0):
    """伸手握住马克杯把手（见模块说明 3）。(x, y) = 把手外侧竖梁中点。返回 info['grip']、info['hand']。"""
    sp = _spec(who)
    S = _size(size, who)
    det = _detail(detail, S)
    r = clamp(float(reach))
    g = ease_io(clamp((r - 0.62) / 0.38))
    fingers = [_mix(a, b, ease_io(clamp(g * 1.15 - 0.05 * i))) for i, (a, b) in enumerate(zip(_GRIP_OPEN,
                                                                                               _GRIP_HOLD))]
    # 握住时的“竖梁”位置（局部坐标）：中指中节指腹外 bar_r 处 —— 用握紧的姿态算，张开时手的位置不跳
    Fh = [_finger(sp, i, *f) for i, f in enumerate(_GRIP_HOLD)]
    fm = Fh[1]
    d2, n2 = fm['fr'][1]
    G = fm['j'][1] + d2 * fm['L'][1] * 0.45 - n2 * (fm['r'][1] + bar_r) * 1.0
    # 拇指：压在把手上沿（竖梁顶端，往拇指一侧）
    s_ = _nz(np.cross(Fh[0]['fr'][0][0], Fh[0]['fr'][0][1]))
    roll = 70.0
    tgt_hold = G + s_ * 0.17 + n2 * 0.02 + np.array([0.0, -0.02, 0.03])
    az1, el1 = _thumb_ik(sp, tgt_hold, roll, (0.0, 8.0, 10.0), az=(-10, 70), el=(-20, 60))
    th = _mix((52, 22, 72, 0, 6, 10), (az1, el1, roll, 0.0, 8.0, 10.0), g)
    F, T = _skeleton(sp, fingers, th)
    e_ = ease_out(clamp(r / 0.72))
    sgn = -1.0 if flip else 1.0
    M = orient(rot + 90.0 * sgn, pitch, yaw * sgn)
    off = np.array([frm[0] * sgn, frm[1]]) * S * (1.0 - e_)
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    off = np.array([off[0] * cr - off[1] * sr, off[0] * sr + off[1] * cr])
    at = np.array([x, y]) + off
    rig = _Rig(sp, M, S, flip, G, at)
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist)
    with _group(pen, 'hand_grip', group, boil):
        allg = _render(pen, rig, elems, lines, seed, light, det)
    info = _info(rig, F, T, allg)
    info['grip'] = (float(x), float(y))
    info['hand'] = tuple(map(float, at))
    return info


# =========================================================================== 4. 手指上缠红线
_TH_OPEN = [(5, 8, 12, 6), (0, 9, 13, 6), (-5, 11, 15, 7), (-10, 13, 17, 8)]
_TH_FIST = [(2, 86, 100, 56), (0, 90, 104, 58), (-2, 92, 106, 58), (-5, 94, 106, 58)]


def _loop(F, t, th):
    """绕在四根手指近节 t 处的一圈（3D 闭合点列）：从小指外侧起，经掌面到食指外侧，再经手背回来。"""
    C, N, Sd, R = [], [], [], []
    for f in F:
        d, n = f['fr'][0]
        C.append(f['j'][0] + d * f['L'][0] * t)
        N.append(n)
        Sd.append(_nz(np.cross(d, n)))
        R.append(f['r'][0] * (1 - 0.1 * t) + th)
    pts = []
    # 小指外侧
    pts.append(C[3] - Sd[3] * R[3])
    # 掌面：小指 → 食指
    for i in (3, 2, 1, 0):
        pts.append(C[i] - N[i] * R[i] - Sd[i] * R[i] * 0.45)
        pts.append(C[i] - N[i] * R[i] + Sd[i] * R[i] * 0.45)
    pts.append(C[0] + Sd[0] * R[0])
    # 手背：食指 → 小指（指缝处稍稍陷下去）
    for i in (0, 1, 2, 3):
        pts.append(C[i] + N[i] * R[i] + Sd[i] * R[i] * 0.45)
        pts.append(C[i] + N[i] * R[i] - Sd[i] * R[i] * 0.45)
        if i < 3:
            m = (C[i] + C[i + 1]) / 2
            nm = _nz(N[i] + N[i + 1])
            pts.append(m + nm * (R[i] + R[i + 1]) * 0.30)
    return np.array(pts)


def _loop_resample(P, n):
    Q = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, Q[:, k]) for k in range(3)], 1)


def hand_thread(pen, x, y, rot=0.0, size=None, seed=0, wraps=3.0, clench=0.0, glow=0.0, out_angle=-25.0,
                out_len=0.10, tail=True, yaw=16.0, pitch=-8.0, flip=False, who='girl', thread_w=0.62,
                light=(-0.55, -0.83), sleeve=True, sleeve_len=0.9, wrist=(-6.0, 0.0), boil=None, group=True,
                detail=1.0, t=None):
    """手指上缠着红线、慢慢攥紧（见模块说明 4）。(x, y) = 手背中心。返回 info['out']、info['dir']、info['bean']。"""
    sp = _spec(who)
    S = _size(size, who)
    det = _detail(detail, S)
    tt = pen.t if t is None else float(t)
    c = clamp(float(clench))
    fingers = [_mix(a, b, ease_io(clamp(c * 1.12 - 0.04 * (3 - i)))) for i, (a, b) in
               enumerate(zip(_TH_OPEN, _TH_FIST))]
    F0 = [_finger(sp, i, *f) for i, f in enumerate(fingers)]
    # 拇指：张开 → 攥拳时压在食指、中指的中节外面
    roll = 82.0
    Ff = [_finger(sp, i, *f) for i, f in enumerate(_TH_FIST)]
    a2 = Ff[0]['j'][1] + Ff[0]['fr'][1][0] * Ff[0]['L'][1] * 0.55
    b2 = Ff[1]['j'][1] + Ff[1]['fr'][1][0] * Ff[1]['L'][1] * 0.55
    tgt = (a2 * 0.5 + b2 * 0.5) + Ff[0]['fr'][1][1] * (Ff[0]['r'][1] + sp['tr'][3] * 0.9)
    fl = [(c_, m_, i_) for c_ in (0.0, 15.0, 30.0) for m_ in (20.0, 35.0, 50.0) for i_ in (15.0, 30.0)]
    az1, el1, tflex = _thumb_ik(sp, tgt, roll, None, az=(-30, 70), el=(0, 90), flexes=fl)
    th = _mix((30, 34, 76, 0, 8, 12), (az1, el1, roll) + tuple(tflex), ease_io(clamp((c - 0.25) / 0.75)))
    T = _thumb(sp, *th)
    F = F0
    M = orient(rot, pitch, yaw)
    anchor = np.array([0.0, 0.26, sp['zt']])
    rig = _Rig(sp, M, S, flip, anchor, (x, y))
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist)
    # ---- 红线：螺旋地缠在近节上
    thw = 0.006
    nw = clamp(float(wraps), 0.0, 3.0)
    tks = [0.34 + 0.15 * k for k in range(4)]
    NL = 56
    loops = [_loop_resample(_loop(F, tk, thw), NL) for tk in tks]
    path = []
    kmax = int(math.ceil(nw - 1e-6))
    for k in range(kmax):
        frac = min(1.0, nw - k)
        m = max(2, int(round(NL * frac)))
        for j in range(m):
            q = j / NL
            path.append(loops[k][j] * (1 - q) + loops[k + 1][j % NL] * q if j < NL else loops[k + 1][0])
    w_th = thread_w * (1.0 + 0.7 * clamp(glow))
    tone_th = 0.92 + 0.08 * clamp(glow)
    start3 = loops[0][0]
    if len(path) >= 2:
        P3 = np.array(path)
        lines.append(dict(pts3=P3, closed=False, w=w_th, tone=tone_th, color='redline', role='contour',
                          seed=_sk(seed, 'thread'), taper=(0.02, 0.02), hints=dict(dry=0.0, head=0.1, lift=0.0)))
        end3 = P3[-1]
    else:
        end3 = start3
    # 离开手：从螺旋的末端沿 out_angle 方向出去
    oa = math.radians(out_angle)
    dvec = np.array([math.cos(oa), math.sin(oa)])
    E = rig.scr(end3)
    zE = float(rig.z(end3))
    allz = [e['z'] for e in elems]
    zf = max(allz) + 0.05 * S
    # 走到剪影外面
    sil = unary_union([e['geom'] for e in elems if e['name'] not in ('sleeve', 'shirt')])
    dist = 0.0
    step = 0.01 * S
    while dist < 1.2 * S and sil.contains(shapely.Point(*(E + dvec * dist))):
        dist += step
    out_pt = E + dvec * (dist + out_len * S)
    ns = 24
    seg2 = np.array([E + dvec * (dist + out_len * S) * k / (ns - 1) for k in range(ns)])
    zz = zE + (zf - zE) * smooth01(np.linspace(0, 1, ns) * 2.0)
    out_line = dict(seg=seg2, zs=zz)
    # 垂下的手链头（串着红豆）
    bean_pos = None
    tail_line = None
    if tail:
        S0 = rig.scr(start3)
        z0 = float(rig.z(start3))
        sway = 0.10 * math.sin(tt * 2.3 + 0.7) + 0.05 * math.sin(tt * 3.7)
        gdir = _nz(np.array([0.10 + sway, 1.0]))
        L_t = 0.24 * S
        k_ = np.linspace(0, 1, 18)
        bend = np.outer(np.sin(k_ * math.pi) * 0.04 * S, np.array([1.0, 0.0]))
        tp = S0 + np.outer(k_ * L_t, gdir) + bend
        tail_line = dict(seg=tp, zs=np.full(len(tp), z0 + 0.01 * S))
        bean_pos = tp[-1] + gdir * 0.030 * S
        br = 0.036
        bpoly = Polygon(ell(bean_pos[0], bean_pos[1], br * S * 0.86, br * S * 1.16, 0, 360, 30,
                            rot=math.degrees(math.atan2(gdir[1], gdir[0])) - 90)).buffer(0)
        be = _elem('tailbean', bpoly, z0 + 0.012 * S, color='bean', shade_color='bean_d', shade_amt=0.55,
                   shk=0.4 * br * S, lcolor='bean_d', lw=0.55, cast=0.0, hl=0.0,
                   bean=(bean_pos, br * S * 1.16, br * S * 0.86, math.degrees(math.atan2(gdir[1], gdir[0]))))
        elems.append(be)
    g = clamp(float(glow))

    def extra(pen_, cx):
        # 红线的红晕（蓄力）：线周围洇开一点红
        if g <= 0.02:
            return
        segs = []
        if len(path) >= 2:
            segs.append(rig.scr(np.array(path)))
        segs.append(out_line['seg'])
        from shapely.geometry import LineString
        halo = unary_union([LineString(s).buffer(0.018 * S * (0.6 + 0.6 * g)) for s in segs if len(s) >= 2])
        px, ph = _pp(halo, 4.0)
        if px:
            pen_.fill(px, 'redline', holes=ph, tone=0.10 + 0.12 * g, seed=_sk(seed, 'halo'), c_fade=False, rim=0.0,
                      soft=6.0, b_clean=False, b_size=0.6)

    for nm, Ld in (('out', out_line), ('tail', tail_line)):
        if Ld is None:
            continue
        sx = Ld['seg']
        # 把屏幕点反推成“伪 3D”：用 zs 做遮挡；这里直接给 2D 点 + 深度
        lines.append(dict(pts2=sx, zs=Ld['zs'], w=w_th if nm == 'out' else thread_w * 0.9,
                          tone=tone_th if nm == 'out' else 0.9, color='redline', role='contour',
                          seed=_sk(seed, nm), taper=(0.02, 0.05 if nm == 'out' else 0.02),
                          hints=dict(dry=0.0, head=0.1, lift=0.0)))
    with _group(pen, 'hand_thread', group, boil):
        allg = _render(pen, rig, elems, _pts2_to3(lines, rig), seed, light, det, extra=extra)
    info = _info(rig, F, T, allg)
    info['out'] = tuple(map(float, out_pt))
    info['dir'] = (float(dvec[0]), float(dvec[1]))
    info['bean'] = None if bean_pos is None else tuple(map(float, bean_pos))
    return info


def _pts2_to3(lines, rig):
    """把“屏幕点 + 深度”的线换成局部 3D 点（解 M 的逆），交给统一的逐点遮挡。"""
    Minv = np.linalg.inv(rig.M)
    out = []
    for L in lines:
        if 'pts2' not in L:
            out.append(L)
            continue
        P = np.asarray(L['pts2'], np.float64)
        zs = np.asarray(L['zs'], np.float64)
        cam = np.column_stack([(P - rig.o) / rig.S, zs / rig.S])
        loc = cam @ Minv.T
        if rig.flip:
            loc[:, 0] = -loc[:, 0]
        L2 = dict(L)
        L2.pop('pts2')
        L2.pop('zs')
        L2['pts3'] = loc
        out.append(L2)
    return out


# =========================================================================== 5. 小指勾小指
_PH_FLAT = [(4, 6, 10, 5), (0, 7, 11, 5), (-4, 8, 12, 6), (-10, 9, 12, 6)]


def pinky_hook(pen, x, y, rot=0.0, size=400.0, seed=0, hook=1.0, gap=0.20, pitch=42.0, yaw=0.0,
               boy_scale=1.12, thread=True, tail_len=0.55, backlit=1.0, light=(0.18, -1.0), sleeve=True,
               sleeve_len=1.0, boil=None, group=True, detail=1.0, t=None):
    """草地上她的右手和他的左手，他的小指勾住她的小指（见模块说明 5）。(x, y) = 两根小指指根之间的中点。"""
    S = float(size)
    det = _detail(detail, S)
    tt = pen.t if t is None else float(t)
    h = clamp(float(hook))
    h1 = ease_io(clamp(h / 0.55))            # 抬起、伸过去
    h2 = ease_io(clamp((h - 0.40) / 0.60))   # 扣下去
    sg, sb = _GIRL, _BOY
    # 她的右手（画面左），他的左手（画面右）
    gf = [list(f) for f in _PH_FLAT]
    gf[3] = [-12 - 10 * h1, 8 - 10 * h1 + 4 * h2, 12 + 26 * h2, 6 + 22 * h2]
    bf = [list(f) for f in _PH_FLAT]
    bf[3] = [-12 - 30 * h1 + 4 * h2, 8 - 26 * h1 + 30 * h2, 12 + 64 * h2, 6 + 52 * h2]
    gth = (24, 24, 72, 0, 6, 10)
    Fg, Tg = _skeleton(sg, gf, gth)
    Fb, Tb = _skeleton(sb, bf, gth)
    Sb = S * boy_scale
    Mg = orient(rot + 9.0, pitch, yaw)
    Mb = orient(rot - 9.0, pitch, yaw)
    gp = gap * S
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    ax = np.array([cr, sr])
    rg = _Rig(sg, Mg, S, False, Fg[3]['j'][0], np.array([x, y]) - ax * gp / 2)
    rb = _Rig(sb, Mb, Sb, True, Fb[3]['j'][0], np.array([x, y]) + ax * gp / 2)
    eg, lg, pg = _hand_elems(rg, sg, Fg, Tg, _sk(seed, 'g'), det, sleeve, sleeve_len, (6.0, 0.0), prefix='g_',
                             split={3: 2})
    eb, lb, pb = _hand_elems(rb, sb, Fb, Tb, _sk(seed, 'b'), det, sleeve, sleeve_len, (6.0, 0.0), prefix='b_',
                             split={3: 2})
    # 两只手放进同一个画面：深度换算到同一尺度（两只手离镜头差不多远）
    # 勾手指的前后：他的小指（近节+中节）压在她的小指上面，他的指尖扣到她的小指下面去
    def find(es, nm):
        for e in es:
            if e['name'] == nm:
                return e
        return None
    gp_ = find(eg, 'g_pinky')
    gt_ = find(eg, 'g_pinky_tip')
    bp_ = find(eb, 'b_pinky')
    bt_ = find(eb, 'b_pinky_tip')
    zb_top = max(e['z'] for e in eg + eb if e['color'] == 'skin') + 0.02 * S
    if h > 0.15:
        bp_['z'] = zb_top
        bp_['segs'] = [(g_, zb_top) for g_, _ in bp_['segs']]
        if h2 > 0.35:
            zlow = gp_['z'] - 0.03 * S
            bt_['z'] = zlow
            bt_['segs'] = [(g_, zlow) for g_, _ in bt_['segs']]
            gt_['z'] = zb_top + 0.01 * S
            gt_['segs'] = [(g_, gt_['z']) for g_, _ in gt_['segs']]
    elems = eg + eb
    lines = lg + lb
    # 勾住的点：他的小指中节与她的小指中节最接近处
    bj = [rb.scr(p) for p in Fb[3]['j']]
    gj = [rg.scr(p) for p in Fg[3]['j']]
    hk = (bj[2] * 0.5 + bj[1] * 0.5) * 0.5 + (gj[2] * 0.6 + gj[1] * 0.4) * 0.5
    # 红线：松松地绕在两根小指上一圈（屏幕上的椭圆，前半圈在手指上面，后半圈在下面），线头拖到草地上
    tl_lines = []
    if thread:
        dv = _nz(np.r_[(gj[2] - gj[1]) + (bj[2] - bj[1]), 0.0])[:2]
        nv = np.array([-dv[1], dv[0]])
        rx_ = (0.10 + 0.02 * (1 - h2)) * S
        ry_ = 0.045 * S
        ph = np.linspace(0, 2 * math.pi, 64)
        wob = 1.0 + 0.06 * np.sin(ph * 3 + 1.3)
        loop2 = hk + np.outer(np.cos(ph) * rx_ * wob, nv) + np.outer(np.sin(ph) * ry_ * wob, dv)
        zc = zb_top + 0.005 * S
        zl = zc + np.sin(ph) * 0.06 * S          # sin>0 一侧（朝指根/镜头）在前
        tl_lines.append(dict(pts2=loop2, zs=zl, w=0.55, tone=0.95, color='redline', role='contour',
                             seed=_sk(seed, 'loop'), taper=(0.02, 0.02), hints=dict(dry=0.0, head=0.1)))
        # 线头：从圈的下沿垂下来，沿两只手之间的草地往镜头这边拖
        k_ = np.linspace(0, 1, 30)
        p0 = loop2[16]
        down = np.array([-sr, cr])
        tail = (p0 + np.outer(k_ * tail_len * S, down) + np.outer(np.sin(k_ * 5.0 + 0.4 + 0.3 * math.sin(tt * 0.9))
                                                                   * 0.035 * S * k_, ax))
        tl_lines.append(dict(pts2=tail, zs=np.full(len(tail), zc), w=0.5, tone=0.92, color='redline',
                             role='contour', seed=_sk(seed, 'tail'), taper=(0.02, 0.35), hints=dict(dry=0.1)))
        tail_end = tail[-1]
    else:
        tail_end = hk
    # 用她的 rig 解 3D（两只手的深度已经在同一尺度：z 是像素）
    lines += _pts2_to3(tl_lines, rg)
    with _group(pen, 'hand_pinky_hook', group, boil):
        allg = _render(pen, rg, elems, lines, seed, light, det, backlit=backlit)
    info = dict(hook=tuple(map(float, hk)), tail_end=tuple(map(float, tail_end)),
                girl=_info(rg, Fg, Tg, unary_union([e['geom'] for e in eg])),
                boy=_info(rb, Fb, Tb, unary_union([e['geom'] for e in eb])))
    info['sil'] = _pp(allg)[0]
    return info


# =========================================================================== 6. 拳头里的红豆
_FIST = [(3, 92, 102, 56), (0, 94, 104, 58), (-3, 96, 106, 60), (-7, 98, 108, 60)]


def fist_bean(pen, x, y, rot=0.0, size=300.0, seed=0, squeeze=0.0, bean=1.0, yaw=40.0, pitch=0.0, flip=False,
              who='girl', light=(-0.55, -0.83), sleeve=True, sleeve_len=0.7, wrist=(10.0, 0.0), boil=None,
              group=True, detail=1.0):
    """握拳、拳缝里露出一点红豆（见模块说明 6）。(x, y) = 拳心。返回 info['fist']、info['bean']。"""
    sp = _spec(who)
    S = float(size)
    det = _detail(detail, S)
    q = clamp(float(squeeze))
    fingers = [(a, b + 6 * q, c + 5 * q, d_ + 4 * q) for (a, b, c, d_) in _FIST]
    F0 = [_finger(sp, i, *f) for i, f in enumerate(fingers)]
    roll = 84.0
    a2 = F0[0]['j'][1] + F0[0]['fr'][1][0] * F0[0]['L'][1] * 0.55
    b2 = F0[1]['j'][1] + F0[1]['fr'][1][0] * F0[1]['L'][1] * 0.55
    tgt = (a2 * 0.5 + b2 * 0.5) + F0[0]['fr'][1][1] * (F0[0]['r'][1] + sp['tr'][3] * 0.85)
    fl = [(c_, m_ + 6 * q, i_ + 6 * q) for c_ in (0.0, 15.0, 30.0) for m_ in (20.0, 35.0, 50.0) for i_ in (15.0, 30.0)]
    az, el, tflex = _thumb_ik(sp, tgt, roll, None, az=(-30, 70), el=(0, 90), flexes=fl)
    T = _thumb(sp, az, el, roll, *tflex)
    F = F0
    f0 = F[0]
    curl = (f0['j'][0] + f0['j'][1] + f0['j'][2] + f0['j'][3]) / 4.0
    anchor = (F[1]['j'][0] + F[1]['j'][1]) / 2
    M = orient(rot, pitch, yaw)
    rig = _Rig(sp, M, S, flip, anchor, (x, y))
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist,
                                      nails=True)
    binfo = None
    if bean > 0.02:
        # 食指卷起来的“小洞”里：在食指后面、中指前面
        c3 = curl + np.array([-0.012, 0.0, 0.0]) - f0['fr'][1][1] * 0.01
        br = 0.040 * (0.55 + 0.45 * clamp(float(bean)))
        be = _bean_elem(rig, c3, br, rot=rot + 60.0)
        zi = [e['z'] for e in elems if e['name'] == 'index'][0]
        zm = [e['z'] for e in elems if e['name'] == 'middle'][0]
        zt = [e['z'] for e in elems if e['name'] == 'thumb'][0]
        be['z'] = min(zi, zt) - 0.004 * S
        be['segs'] = [(be['geom'], be['z'])]
        be['cast'] = 0.0
        elems.append(be)
        binfo = be
    with _group(pen, 'hand_fist', group, boil):
        allg = _render(pen, rig, elems, lines, seed, light, det)
    info = _info(rig, F, T, allg)
    info['fist'] = (float(x), float(y))
    info['bean'] = None if binfo is None else tuple(map(float, binfo['bean'][0]))
    return info


# =========================================================================== 7. 握住玻璃罐（追加：第 12 镜，jar.py）
_JAR_OPEN = [(8, 14, 18, 8), (1, 16, 20, 9), (-5, 18, 22, 10), (-12, 20, 24, 10)]
_JAR_TH_OPEN = (52, 22, 72, 0, 6, 10)


def jar_grip_frame(axis, back=(-0.35, -0.45, 0.82), thumb_dir=1, flip=False):
    """罐子的轴向 → 手的朝向矩阵 M（列 = 局部 X 拇指 / Y 指尖 / Z 手背 在相机坐标里的方向）。
    axis：罐底 → 罐口的方向（相机坐标：x 右、y 下、z 朝镜头），back：希望手背大致朝哪边（会投影到与轴垂直的平面上）。
    thumb_dir=+1 拇指朝罐口一侧，-1 朝罐底一侧。flip=True（左手）时自动换向，保证拇指仍朝 thumb_dir 那头。"""
    A = _nz(np.asarray(axis, np.float64))
    X = A * float(thumb_dir) * (-1.0 if flip else 1.0)
    B = np.asarray(back, np.float64)
    Z = _nz(B - np.dot(B, X) * X)
    Y = np.cross(Z, X)
    return np.column_stack([X, Y, Z])


def hand_jar(pen, x, y, axis=(0.0, -1.0, 0.0), jar_r=0.30, size=None, seed=0, grip=1.0,
             back=(-0.35, -0.45, 0.82), thumb_dir=1, flip=False, who='girl', occ=None, light=(-0.55, -0.83),
             sleeve=True, sleeve_len=0.9, wrist=(0.0, 0.0), boil=None, group=True, detail=1.0):
    """她握住一只圆柱形的玻璃罐（四指从一侧绕过罐身、拇指从另一侧绕过来，手背朝镜头）。
    (x, y) = 罐子轴线上、正对掌心的那一点（场景坐标）；axis = 罐子轴向（相机坐标单位向量，罐底 → 罐口），
    jar_r = 罐身半径（单位 L = 手长）。手的朝向由 axis 和 back 决定（见 jar_grip_frame），不用 rot/yaw/pitch。
    grip 0→1：手指从半张开到绕紧罐身。
    occ：罐身的剪影（场景坐标多边形）——绕到罐子后面的指节在剪影里被挡住（不画）。
    返回 info['grip']（= (x, y)）、info['axis2']（轴向在画面上的单位向量）、info['jar_rs']（罐身半径，像素）、
    info['zA']（轴线深度，像素），以及通用的 tips / wrist / sil。
    场景先画罐子（轴线经过 (x, y)、半径 jar_r × size），再调这个函数。"""
    sp = _spec(who)
    S = _size(size, who)
    det = _detail(detail, S)
    g = ease_io(clamp(float(grip)))
    Rc = float(jar_r)
    yc = 0.30
    h = sp['zb'] + Rc
    # ---- 四指：沿着以罐轴为圆心的圆绕过去（每节当作一根弦）
    fingers = []
    for i in range(4):
        ky = sp['fb'][i][1]
        dy, dz = ky - yc, 0.0 + h
        rho = math.hypot(dy, dz)
        beta = math.degrees(math.atan2(dy, dz))
        dl = [2.0 * math.degrees(math.asin(min(0.999, l / (2.0 * rho)))) for l in sp['fl'][i]]
        wrap = (beta + dl[0] / 2.0, dl[0] / 2.0 + dl[1] / 2.0, dl[1] / 2.0 + dl[2] / 2.0)
        spread = (3.0, 0.0, -3.0, -7.0)[i]
        fingers.append(_mix(_JAR_OPEN[i], (spread,) + wrap, g))
    F = [_finger(sp, i, *f) for i, f in enumerate(fingers)]
    # ---- 拇指：从另一侧（手腕那边）绕过罐身
    roll = 70.0
    rho_t = Rc + sp['tr'][2] * 1.1
    gam = math.radians(-96.0)
    tgt = np.array([0.15, yc + rho_t * math.sin(gam), -h + rho_t * math.cos(gam)])
    az1, el1 = _thumb_ik(sp, tgt, roll, (0.0, 10.0, 14.0), az=(-20, 80), el=(-10, 89))
    th = _mix(_JAR_TH_OPEN, (az1, el1, roll, 0.0, 10.0, 14.0), g)
    T = _thumb(sp, *th)
    M = jar_grip_frame(axis, back, thumb_dir, flip)
    anchor = np.array([0.0, yc, -h])
    rig = _Rig(sp, M, S, flip, anchor, (x, y))
    elems, lines, parts = _hand_elems(rig, sp, F, T, seed, det, sleeve, sleeve_len, wrist)
    zA = float(rig.z(anchor))
    # ---- 绕到罐子后面的部分：在罐身剪影里挖掉
    if occ is not None:
        oc = _valid(Polygon(np.asarray(occ, np.float64)))
        cut = []
        for e in elems:
            if 'fid' not in e or not e.get('segs'):
                continue
            segs = []
            for gg, zz in e['segs']:
                if zz < zA - 0.01 * S:
                    gi = _valid(gg.intersection(oc))
                    if not gi.is_empty:
                        cut.append(gi)
                    gg = _valid(gg.difference(oc))
                segs.append((gg, zz))
            e['segs'] = [(gg, zz) for gg, zz in segs if not gg.is_empty] or [(Polygon(), e['z'])]
            e['geom'] = _valid(unary_union([gg for gg, _ in segs if not gg.is_empty])) if any(
                not gg.is_empty for gg, _ in segs) else Polygon()
        if cut:
            cutg = _valid(unary_union(cut).buffer(0.01 * S))
            keep_lines = []
            for L in lines:
                P2 = L.get('pts', L.get('lift'))
                if P2 is not None and 'pts3' not in L:
                    P2 = np.asarray(P2, np.float64).reshape(-1, 2)
                    if len(P2) and _contains(cutg, P2).any():
                        continue
                keep_lines.append(L)
            lines = keep_lines
    with _group(pen, 'hand_jar', group, boil):
        allg = _render(pen, rig, elems, lines, seed, light, det)
    info = _info(rig, F, T, allg)
    info['grip'] = (float(x), float(y))
    ax2 = np.asarray(axis, np.float64)[:2]
    info['axis2'] = tuple(map(float, ax2 / (np.linalg.norm(ax2) + 1e-9)))
    info['jar_rs'] = float(Rc * S)
    info['zA'] = zA
    return info


# =========================================================================== 追加（thread）：5b. 小指勾小指（修正版）
def pinky_hook2(pen, x, y, rot=0.0, size=400.0, seed=0, hook=1.0, gap=0.20, pitch=42.0, yaw=0.0,
               boy_scale=1.12, thread=True, tail_len=0.55, backlit=1.0, light=(0.18, -1.0), sleeve=True,
               sleeve_len=1.0, boil=None, group=True, detail=1.0, t=None, thread_w=1.0):
    """= pinky_hook，修正：小指拆成两段后，后一段元素名是 '<名>_b'（_finger_elems 的命名），
    原函数找的是 '_tip'，hook>0.65 时会拿到 None 报错。参数、返回值与 pinky_hook 相同，
    另加 thread_w：红线粗细倍数（特写里线要更醒目，第 18 镜用 1.5 左右）。"""
    S = float(size)
    det = _detail(detail, S)
    tt = pen.t if t is None else float(t)
    h = clamp(float(hook))
    h1 = ease_io(clamp(h / 0.55))            # 抬起、伸过去
    h2 = ease_io(clamp((h - 0.40) / 0.60))   # 扣下去
    sg, sb = _GIRL, _BOY
    # 她的右手（画面左），他的左手（画面右）
    gf = [list(f) for f in _PH_FLAT]
    gf[3] = [-12 - 10 * h1, 8 - 10 * h1 + 4 * h2, 12 + 26 * h2, 6 + 22 * h2]
    bf = [list(f) for f in _PH_FLAT]
    bf[3] = [-12 - 30 * h1 + 4 * h2, 8 - 26 * h1 + 30 * h2, 12 + 64 * h2, 6 + 52 * h2]
    gth = (24, 24, 72, 0, 6, 10)
    Fg, Tg = _skeleton(sg, gf, gth)
    Fb, Tb = _skeleton(sb, bf, gth)
    Sb = S * boy_scale
    Mg = orient(rot + 9.0, pitch, yaw)
    Mb = orient(rot - 9.0, pitch, yaw)
    gp = gap * S
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    ax = np.array([cr, sr])
    rg = _Rig(sg, Mg, S, False, Fg[3]['j'][0], np.array([x, y]) - ax * gp / 2)
    rb = _Rig(sb, Mb, Sb, True, Fb[3]['j'][0], np.array([x, y]) + ax * gp / 2)
    eg, lg, pg = _hand_elems(rg, sg, Fg, Tg, _sk(seed, 'g'), det, sleeve, sleeve_len, (6.0, 0.0), prefix='g_',
                             split={3: 2})
    eb, lb, pb = _hand_elems(rb, sb, Fb, Tb, _sk(seed, 'b'), det, sleeve, sleeve_len, (6.0, 0.0), prefix='b_',
                             split={3: 2})
    # 两只手放进同一个画面：深度换算到同一尺度（两只手离镜头差不多远）
    # 勾手指的前后：他的小指（近节+中节）压在她的小指上面，他的指尖扣到她的小指下面去
    def find(es, nm):
        for e in es:
            if e['name'] == nm:
                return e
        return None
    gp_ = find(eg, 'g_pinky')
    gt_ = find(eg, 'g_pinky_b') or find(eg, 'g_pinky_tip')
    bp_ = find(eb, 'b_pinky')
    bt_ = find(eb, 'b_pinky_b') or find(eb, 'b_pinky_tip')
    zb_top = max(e['z'] for e in eg + eb if e['color'] == 'skin') + 0.02 * S
    if h > 0.15:
        bp_['z'] = zb_top
        bp_['segs'] = [(g_, zb_top) for g_, _ in bp_['segs']]
        if h2 > 0.35:
            zlow = gp_['z'] - 0.03 * S
            bt_['z'] = zlow
            bt_['segs'] = [(g_, zlow) for g_, _ in bt_['segs']]
            gt_['z'] = zb_top + 0.01 * S
            gt_['segs'] = [(g_, gt_['z']) for g_, _ in gt_['segs']]
    elems = eg + eb
    lines = lg + lb
    # 勾住的点：他的小指中节与她的小指中节最接近处
    bj = [rb.scr(p) for p in Fb[3]['j']]
    gj = [rg.scr(p) for p in Fg[3]['j']]
    hk = (bj[2] * 0.5 + bj[1] * 0.5) * 0.5 + (gj[2] * 0.6 + gj[1] * 0.4) * 0.5
    # 红线：松松地绕在两根小指上一圈（屏幕上的椭圆，前半圈在手指上面，后半圈在下面），线头拖到草地上
    tl_lines = []
    if thread:
        dv = _nz(np.r_[(gj[2] - gj[1]) + (bj[2] - bj[1]), 0.0])[:2]
        nv = np.array([-dv[1], dv[0]])
        rx_ = (0.10 + 0.02 * (1 - h2)) * S
        ry_ = 0.045 * S
        ph = np.linspace(0, 2 * math.pi, 64)
        wob = 1.0 + 0.06 * np.sin(ph * 3 + 1.3)
        loop2 = hk + np.outer(np.cos(ph) * rx_ * wob, nv) + np.outer(np.sin(ph) * ry_ * wob, dv)
        zc = zb_top + 0.005 * S
        zl = zc + np.sin(ph) * 0.06 * S          # sin>0 一侧（朝指根/镜头）在前
        tl_lines.append(dict(pts2=loop2, zs=zl, w=0.55 * thread_w, tone=0.95, color='redline', role='contour',
                             seed=_sk(seed, 'loop'), taper=(0.02, 0.02), hints=dict(dry=0.0, head=0.1)))
        # 线头：从圈的下沿垂下来，沿两只手之间的草地往镜头这边拖
        k_ = np.linspace(0, 1, 30)
        p0 = loop2[16]
        down = np.array([-sr, cr])
        tail = (p0 + np.outer(k_ * tail_len * S, down) + np.outer(np.sin(k_ * 5.0 + 0.4 + 0.3 * math.sin(tt * 0.9))
                                                                   * 0.035 * S * k_, ax))
        tl_lines.append(dict(pts2=tail, zs=np.full(len(tail), zc), w=0.5 * thread_w, tone=0.92, color='redline',
                             role='contour', seed=_sk(seed, 'tail'), taper=(0.02, 0.35), hints=dict(dry=0.1)))
        tail_end = tail[-1]
    else:
        tail_end = hk
    # 用她的 rig 解 3D（两只手的深度已经在同一尺度：z 是像素）
    lines += _pts2_to3(tl_lines, rg)
    with _group(pen, 'hand_pinky_hook', group, boil):
        allg = _render(pen, rg, elems, lines, seed, light, det, backlit=backlit)
    info = dict(hook=tuple(map(float, hk)), tail_end=tuple(map(float, tail_end)),
                girl=_info(rg, Fg, Tg, unary_union([e['geom'] for e in eg])),
                boy=_info(rb, Fb, Tb, unary_union([e['geom'] for e in eb])))
    info['sil'] = _pp(allg)[0]
    return info
