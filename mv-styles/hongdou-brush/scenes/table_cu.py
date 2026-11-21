# -*- coding: utf-8 -*-
"""
第 5 镜「第二十句例」（成片 14.07–16.36，C）+ T1（16.36–17.43，C→A：水彩从碗里的红豆晕开）。
侧面近景：她坐在桌前、俯身看着面前那碗红豆汤；脸在画面右上，碗在脸的左下方；
背景是夜里厨房的局部（左上角的窗、雪、吊灯的光），水墨下大量留白。

draw(pen, **kw)
  pen.style == 'C'（现在）：
      14.07 低头看着自己那碗汤，眼里慢慢含泪、眼眶泛红（sad_down → cry）；14.70 慢慢眨一下眼，
      泪顺着脸颊流到下颌（一道湿亮的泪痕）；15.62 泪在下颌聚成一颗；16.01「哀」落下；
      16.31「愁」落进碗里的红豆（16.29 那一格碰到汤面），荡开一圈圈涟漪。落下之后她慢慢闭上眼、头微微抬起。
      桌上碗边放着一把没动过的勺子。
  pen.style == 'A' / 'B'（回忆的早晨，T1 水彩那一侧）：
      同一构图；窗外是白天的小雪，晨光从窗那边照进来，吊灯关着；她闭眼笑（closed_smile），
      头转向右边迎上去（这时看得见红豆发夹）；他的手（藏青毛衣袖口）从画面右边把一勺红豆汤递到她嘴边，
      17.0 秒到位、她微微张嘴。桌上那把勺子此时在他手里。碗里的涟漪在 T1 里接着荡开（和水墨那一侧对上）。
  kw：t 覆盖表演时间（成片秒，默认 pen.t）；style 覆盖内容（'C' / 'A'），单独看某一侧用。

BLOOM_CENTER：泪滴落进碗里的那一点（碗里的红豆，屏幕坐标），T1 的水彩从这里晕开。
注意：泪是竖直落下的，所以碗必须在她下颌的正下方；碗比分镜草案（x 650–950）往右挪了一些。
"""
import math

import cv2
import numpy as np

from core import W, H, densify, ell, bez, spline, tube, rng, clamp, smooth01, ease_io, ease_out, ik2
import characters as ch

try:
    from shapely.geometry import Polygon as _SPoly
except Exception:      # pragma: no cover
    _SPoly = None

# ---------------------------------------------------------------- 时间（成片秒）
T0 = 14.07            # 镜头开始
T_BLINK = 14.66       # 慢慢眨一下眼（之后泪流下来）
T_RUN = 14.80         # 泪痕从眼下流到下颌（0.65 秒）
T_SWELL = 15.62       # 下颌的泪珠慢慢聚大
T_DROP = 15.98        # “哀”（16.01）：泪珠离开下颌
T_HIT = 16.26         # “愁”（16.31）：落进汤里（16.29 那一格就碰到汤面）
T_T1 = 16.36          # T1 开始
T_END = 17.43         # T1 结束
T_SPOON = 17.00       # A：勺子到嘴边

# ---------------------------------------------------------------- 布局（场景坐标 = 屏幕坐标）
TABLE_Y = 690                      # 她的身体在这条线以下被桌面挡住（桌面后沿）
S_GIRL = 215
GIRL_XY = (1192, 462)              # 颈根
LEAN = 0.9                         # 俯身看碗
BOWL_R = 160                       # 碗口半径
BOWL_K = 0.30                      # 碗口椭圆 ry/rx（镜头略高于桌面）
WIN = dict(x1=600, y1=430)         # 窗玻璃的右下角（窗只露出左上一角）
LAMP = (800, 118)                  # 吊灯灯罩下沿中心
TEAR_R = 0.058 * S_GIRL            # 落下那颗泪的大小

BG_BOIL = 0.4


def P(pts):
    return np.float32(pts)


def D(pts, spacing=24.0, closed=False):
    return densify(np.float32(pts), spacing, closed)


# ================================================================= 她的表演
def _blink(t, tb, dur=0.30):
    """0..1：一次慢眨眼（闭得快、睁得慢）。"""
    x = (t - tb) / dur
    if x <= 0 or x >= 1:
        return 0.0
    return float(smooth01(x / 0.35)) if x < 0.35 else float(1.0 - smooth01((x - 0.35) / 0.65))


def girl_pose_c(t):
    """现在：俯身低头看碗，慢慢哭。泪痕由场景自己画（tear_track），表情里 tear=0。"""
    u = ease_io((t - (T0 + 0.10)) / 1.50)                 # sad_down → cry
    face = ch.mix_expr('sad_down', 'cry', u)
    face['tear'] = 0.0
    face['wet'] = 1.0
    face['open'] = 0.28 - 0.03 * u                        # 眼皮半垂，眼神落在碗里（左下）
    face['gy'] = 1.0
    face['gx'] = -0.45                                    # 朝左的人 gx<0 = 往画面左边看
    face['mouth_open'] = 0.05 + 0.03 * u + 0.02 * math.sin(t * 8.0) * u
    # 落下之后：慢慢闭上眼（像在想起从前），眉头松一点
    shut = ease_io((t - (T_HIT + 0.08)) / 0.45)
    face['open'] = face['open'] * (1.0 - shut)
    face['brow'] = face['brow'] * (1.0 - 0.35 * shut)
    face['smile'] = face['smile'] * (1.0 - 0.45 * shut)
    blink = max(_blink(t, T_BLINK, 0.36), 0.5 * _blink(t, T_DROP - 0.12, 0.26))
    # 头：慢慢再低一点；泪落下时轻轻一顿；落进碗里之后微微抬起
    pitch = 19.0 + 2.0 * ease_io((t - T0) / 1.9) - 1.0 * ease_io((t - (T_DROP - 0.1)) / 0.2) \
        + 1.0 * ease_io((t - T_DROP) / 0.3) - 4.0 * ease_io((t - (T_HIT + 0.12)) / 0.8)
    yaw = 32.0 - 2.0 * ease_io((t - T0) / 2.0) - 4.0 * ease_io((t - (T_HIT + 0.12)) / 0.8)
    roll = 4.0 + 1.0 * ease_io((t - T0) / 2.0)
    # 抽泣：肩头轻轻一提
    sob = math.exp(-((t - 15.40) / 0.10) ** 2) + 0.6 * math.exp(-((t - 16.06) / 0.09) ** 2)
    x, y = GIRL_XY
    return dict(x=x, y=y - 2.5 * sob, s=S_GIRL, facing=-1, yaw=yaw, pitch=pitch, roll=roll, lean=LEAN,
                face=face, blink=blink, breath=(t - T0) / 3.6 + 0.2, clip_y=TABLE_Y + 2, clip_arms=True,
                arm='rest', arm_args=dict(hand=(x + 30, TABLE_Y + 190), shape='flat'), seed=1000, boil=1.0)


def girl_pose_a(t):
    """回忆：闭眼笑，头转向右边迎上那一勺。"""
    face = ch.expr('closed_smile')
    a = ease_io((t - (T_SPOON - 0.30)) / 0.30)            # 勺子快到时微微张嘴
    face['mouth_open'] = 0.22 * a
    face['smile'] = 0.62 - 0.14 * a
    face['blush'] = 0.80
    up = ease_io((t - T_T1) / (T_SPOON - T_T1))           # 抬头、转向他
    pitch = 15.0 - 10.0 * up
    yaw = 18.0 - 34.0 * up
    roll = 2.0 - 8.0 * up
    x, y = GIRL_XY
    return dict(x=x, y=y, s=S_GIRL, facing=-1, yaw=yaw, pitch=pitch, roll=roll, lean=LEAN - 0.25 * up,
                face=face, breath=(t - T0) / 3.6 + 0.2, clip_y=TABLE_Y + 2, clip_arms=True,
                arm='rest', arm_args=dict(hand=(x + 30, TABLE_Y + 190), shape='flat'), seed=1000, boil=1.0)


def _near_side(R):
    sty = ch.GIRL_FEAT
    best = None
    for side in (-1, 1):
        p3 = ch._surf(R.face_tab, sty['y_in'] + 0.045, (sty['ph_in'] + 14) * side)
        _, z = R.proj(p3[None], with_z=True)
        if best is None or z[0] > best[1]:
            best = (side, float(z[0]))
    return best[0]


Y_JAW = 0.43        # 泪痕流到的位置（脸的纵向坐标；下巴 = 0.47）


def tear_path(pose, k=1.0, n=10):
    """近侧脸颊上的泪痕：从下眼睑下方顺着脸颊流到下颌。k 0..1 流到哪里。→ 场景坐标点列。"""
    R = ch._GirlRig(pose)
    sty = ch.GIRL_FEAT
    side = _near_side(R)
    y0 = sty['y_in'] + 0.05
    ys = np.linspace(y0, y0 + (Y_JAW - y0) * max(k, 1e-3), n)
    ph = (sty['ph_in'] + 15 + 6 * np.linspace(0, 1, n) * k) * side
    return R.proj(ch._surf(R.face_tab, ys, ph, dz=0.006))


def _tear_geom():
    """落下的那颗泪：起点（挂在下颌的泪珠圆肚中心）→ 落点（汤面）。"""
    end = tear_path(girl_pose_c(T_DROP))[-1]
    start = np.float32([end[0], end[1] + 1.5 * TEAR_R])
    return start


_TS = _tear_geom()
# 碗：落点在汤面中间偏右（碗口中心往右 0.50 r），碗在她下颌的正下方偏左
SOUP_DY = 0.10 * BOWL_R            # 汤面比碗口低一点（透视里中心往下）
SOUP_K = 0.88                      # 汤面椭圆相对碗口的大小
_LX = float(_TS[0]) - 6.0
BOWL_C = (_LX - 0.50 * BOWL_R, 716.0)
LAND = (_LX, float(BOWL_C[1] + SOUP_DY - 0.12 * BOWL_R * BOWL_K))
BLOOM_CENTER = (int(round(LAND[0])), int(round(LAND[1])))


# ================================================================= 小工具
def _isect(a, b):
    """两个多边形的交（取最大的一块）。"""
    if _SPoly is None:
        return np.float32(a)
    g = _SPoly(np.asarray(a, np.float64)).buffer(0).intersection(_SPoly(np.asarray(b, np.float64)).buffer(0))
    if g.is_empty:
        return None
    if g.geom_type != 'Polygon':
        g = max(getattr(g, 'geoms', [g]), key=lambda q: q.area)
    return np.float32(np.asarray(g.exterior.coords)[:-1])


def _mask(polys, x0, y0, w, h, holes=(), blur=0.0):
    m = np.zeros((h, w), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round((np.asarray(p) - (x0, y0)) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    for p in holes:
        cv2.fillPoly(m, [np.round((np.asarray(p) - (x0, y0)) * 16).astype(np.int32)], 0, cv2.LINE_AA, shift=4)
    m = m.astype(np.float32) / 255.0
    if blur > 0:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    return m


def bowl_geom():
    cx, cy = BOWL_C
    r = BOWL_R
    ry = r * BOWL_K
    side_l = bez((cx - r, cy), (cx - r * 0.97, cy + 0.62 * r), (cx - r * 0.44, cy + 0.68 * r), 14)
    side_r = bez((cx + r * 0.44, cy + 0.68 * r), (cx + r * 0.97, cy + 0.62 * r), (cx + r, cy), 14)
    foot = P([(cx - 0.40 * r, cy + 0.67 * r), (cx - 0.37 * r, cy + 0.77 * r), (cx + 0.37 * r, cy + 0.77 * r),
              (cx + 0.40 * r, cy + 0.67 * r)])
    body = np.vstack([ell(cx, cy, r, ry, 180, 360, 32), side_r[::-1], foot[::-1], side_l[::-1]])
    soup = ell(cx, cy + SOUP_DY, r * SOUP_K, ry * SOUP_K, 0, 360, 56)
    lip = ell(cx, cy + 0.6, r - 6.0, ry - 4.0, 0, 360, 56)
    return dict(cx=cx, cy=cy, r=r, ry=ry, front=ell(cx, cy, r, ry, 0, 180, 32), side_l=side_l, side_r=side_r,
                foot=foot, body=body, soup=soup, soup_vis=_isect(soup, lip))


# ================================================================= 背景
def _wall(pen, mem):
    """墙：夜里一层很淡的墨，吊灯照到的地方留白（灯光就是纸）；早晨是暖墙色。"""
    q = P([(-20, -20), (W + 20, -20), (W + 20, TABLE_Y + 4), (-20, TABLE_Y + 4)])
    lx, ly = LAMP
    if mem:
        pen.fill(q, 'wall', seed=700, rgrad=(lx - 200, ly + 260, 300, 1500, 0.25, 1.0), c_fade=False)
    else:
        pen.fill(q, 'wall', seed=700, tone=0.20, rgrad=(lx, ly + 300, 330, 1250, 0.0, 1.0), c_fade=False,
                 broad=False)
    # 她身后的门框（一条淡淡的竖边）
    pen.line(D([(1712, -20), (1709, 300), (1713, TABLE_Y - 4)], 30), 7, tone=0.5, color='wood_d', seed=702,
             taper=(0.05, 0.4), head=0.2, dry=0.7, dry_from=0.3, streak=0.2, fade=0.3)
    pen.line(D([(1740, -20), (1738, 260), (1741, TABLE_Y - 30)], 30), 3, tone=0.32, color='wood_d', seed=703,
             taper=(0.05, 0.5), head=0.1, dry=0.75, dry_from=0.2)


def _window(pen, mem):
    """窗的左上一角：夜（C）/ 白天的小雪（A）。"""
    s = 100
    x1, y1 = WIN['x1'], WIN['y1']
    glass = P([(-20, -20), (x1, -20), (x1, y1), (-20, y1)])
    pen.cover(glass, seed=s)
    if mem:
        pen.fill(glass, 'sky', seed=s + 1, grad=(x1, y1, 0, 0, 0.55, 1.0), streak=0.3)
    else:
        pen.fill(glass, 'night', seed=s + 1, grad=(60, 0, x1 + 60, y1 + 60, 1.0, 0.50), streak=0.4)
    # 远处的屋顶（积雪的屋脊 + 亮着的小窗）
    roofs = [[(-20, 368), (40, 338), (110, 318), (180, 340), (236, 362)],
             [(214, 380), (290, 350), (362, 330), (430, 350), (490, 374)],
             [(470, 360), (530, 336), (580, 326), (x1 + 10, 332)]]
    for i, top in enumerate(roofs):
        top = P(top)
        body = np.vstack([top, [[top[-1, 0], y1], [top[0, 0], y1]]])
        pen.fill(body, 'roof', seed=s + 20 + i, grad=(0, float(top[:, 1].min()), 0, y1 + 40, 1.0, 0.45),
                 a_dens=0.7)
        pen.line(top, 12, tone=0.9, color='snow', seed=s + 30 + i, taper=(0.1, 0.2), role='detail', dry=0.45,
                 dry_from=0.3)
    if not mem:
        for i, (lx, ly, lw, lh) in enumerate([(60, 382, 15, 18), (122, 372, 13, 16), (330, 392, 16, 15),
                                              (384, 386, 12, 16), (546, 372, 14, 18)]):
            q = P([[lx, ly], [lx + lw, ly + 1], [lx + lw - 1, ly + lh], [lx + 1, ly + lh - 1]])
            pen.cover(q, seed=s + 50 + i, feather=0.8)
            pen.fill(q, 'win_warm', seed=s + 55 + i)
    if mem:
        # 玻璃上的一道反光
        pen.lift(tube([(80, 300), (230, 120), (330, -10)], [20, 46, 26])[0], amt=0.45, seed=s + 70, soft=12.0)
    else:
        # 玻璃下角起雾
        pen.lift(ell(540, y1 - 8, 120, 40), amt=0.5, seed=s + 70, soft=12.0)
        pen.lift(ell(120, y1 - 6, 160, 30), amt=0.4, seed=s + 71, soft=12.0)
    # 窗框：右边竖框、下边窗台，中间一根竖棂
    pen.line(D([(x1 + 4, -12), (x1 + 1, 200), (x1 + 4, y1 + 6)], 30), 17, tone=0.90, color='wood_d', seed=s + 80,
             taper=(0.02, 0.12), head=0.3, lift=0.3, dry=0.5, dry_from=0.65, streak=0.25, pool=0.2)
    pen.line(D([(x1 + 22, -12), (x1 + 21, 220), (x1 + 23, y1 + 16)], 30), 5, tone=0.5, color='wood_d',
             seed=s + 81, taper=(0.05, 0.3), head=0.1, dry=0.7, dry_from=0.35, streak=0.2)
    pen.line(D([(282, -12), (279, 200), (283, y1 + 2)], 30), 10, tone=0.78, color='wood_d', seed=s + 82,
             taper=(0.02, 0.2), head=0.3, lift=0.3, dry=0.5, dry_from=0.6, streak=0.2)
    sill = P([[-20, y1 + 2], [x1 + 46, y1 + 4], [x1 + 50, y1 + 30], [-20, y1 + 28]])
    pen.cover(sill, seed=s + 89)
    pen.fill(sill, 'wood', seed=s + 90, grad=(0, 0, x1 + 50, 0, 0.6, 1.0))
    pen.shade(P([[-20, y1 + 18], [x1 + 48, y1 + 20], [x1 + 50, y1 + 30], [-20, y1 + 28]]), amount=0.3,
              seed=s + 93, angle=0)
    pen.line(D([(-20, y1 + 4), (300, y1), (x1 + 56, y1 + 5)], 30), 17, tone=0.92, color='wood_d', seed=s + 91,
             taper=(0.02, 0.12), head=0.2, lift=0.25, dry=0.45, dry_from=0.72, streak=0.25, pool=0.25)
    pen.line(D([(-20, y1 + 31), (300, y1 + 32), (x1 + 44, y1 + 30)], 30), 5, tone=0.55, color='wood_d',
             seed=s + 92, taper=(0.05, 0.4), head=0.1, dry=0.75, dry_from=0.35, streak=0.2)


def _lamp(pen, mem):
    """吊灯：灯罩从画面上沿垂下来；夜里亮着（水墨 = 留白），早晨关着。"""
    s = 900
    lx, ly = LAMP
    pen.line(D([(lx + 1, -30), (lx, ly - 60)], 20), 3.0, tone=0.7, seed=s, taper=(0, 0))
    shade = spline(P([[lx - 22, ly - 64], [lx + 22, ly - 64], [lx + 52, ly - 40], [lx + 104, ly - 6],
                      [lx + 112, ly], [lx - 112, ly], [lx - 104, ly - 6], [lx - 52, ly - 40]]), 3.0, closed=True)
    pen.cover(shade, seed=s + 10, feather=0.8)
    pen.fill(shade, 'lampshade', seed=s + 1, grad=(lx - 112, 0, lx + 112, 0, 1.0, 0.75))
    pen.shade(P([[lx + 8, ly - 64], [lx + 22, ly - 64], [lx + 52, ly - 40], [lx + 104, ly - 6], [lx + 112, ly],
                 [lx + 40, ly]]), amount=0.3, seed=s + 11)
    pen.lift(tube([(lx - 16, ly - 56), (lx - 50, ly - 32), (lx - 88, ly - 8)], [4, 9, 4])[0], amt=0.55,
             seed=s + 2, soft=1.5, dry=0.75, streak=0.5)
    pen.line(D([(lx - 118, ly + 1), (lx, ly + 6), (lx + 118, ly)], 20), 10, tone=0.92, seed=s + 5,
             taper=(0.05, 0.18), head=0.5, lift=0.3, dry=0.35, dry_from=0.75)
    pen.line(spline(P([[lx - 22, ly - 64], [lx - 52, ly - 40], [lx - 104, ly - 6]]), 3.0), 4.5, tone=0.75,
             seed=s + 6, taper=(0.1, 0.2), head=0.3)
    pen.line(ell(lx, ly + 8, 22, 13, 15, 165, 12), 2.6, tone=0.5, seed=s + 7, taper=(0.2, 0.4), head=0)
    if not mem:
        # 灯光：水墨里是留白（把附近的墨提开）
        pen.light(lx, ly + 260, 500, 360, amt=0.40, color='lamp', seed=s + 8)


def _table(pen, mem):
    s = 400
    top = P([(-20, TABLE_Y), (W + 20, TABLE_Y), (W + 20, H + 20), (-20, H + 20)])
    cx, cy = BOWL_C
    pen.cover(top, seed=s)
    if mem:
        pen.fill(top, 'wood', seed=s + 1, rgrad=(cx - 200, cy, 200, 1300, 0.55, 1.0), streak=0.5, sangle=2.0)
    else:
        pen.fill(top, 'wood', seed=s + 1, tone=0.22, rgrad=(cx - 60, cy - 40, 200, 1150, 0.25, 1.0), streak=0.5,
                 sangle=2.0, broad=False)
    # 木纹
    r = rng(s, 'grain')
    for k in range(5):
        y = TABLE_Y + 46 + k * 64 + r.uniform(-10, 10)
        x0 = r.uniform(-20, 300) if k % 2 == 0 else r.uniform(1200, 1500)
        x1 = x0 + r.uniform(400, 700)
        pen.line(D([(x0, y), ((x0 + x1) / 2, y + r.uniform(-4, 4)), (x1, y + r.uniform(-3, 3))], 40), 2.4,
                 tone=0.24, color='wood_d', seed=s + 10 + k, taper=(0.3, 0.4), role='detail', dry=0.7,
                 dry_from=0.2, streak=0.3)
    # 桌面后沿：一道有力的横笔
    pen.line(D([(-20, TABLE_Y + 1), (700, TABLE_Y - 2), (1500, TABLE_Y + 1), (1880, TABLE_Y - 1)], 30), 14,
             tone=0.9, color='wood_d', seed=s + 2, taper=(0.02, 0.2), head=0.4, lift=0.3, dry=0.5, dry_from=0.7,
             streak=0.25, pool=0.2)
    pen.line(D([(-20, TABLE_Y + 16), (900, TABLE_Y + 14), (1700, TABLE_Y + 17)], 30), 4, tone=0.4,
             color='wood_d', seed=s + 3, taper=(0.05, 0.5), head=0.1, dry=0.75, dry_from=0.3, streak=0.2)


def background(pen, mem):
    _wall(pen, mem)
    _window(pen, mem)
    _table(pen, mem)
    _lamp(pen, mem)
    if mem:
        # 晨光从窗那边照进来（水彩：暖光罩染 + 提亮）
        pen.light(380, 470, 900, 560, amt=0.55, color='sun', seed=960)


# ================================================================= 动态元素
def snow(pen, t, mem):
    x1, y1 = WIN['x1'], WIN['y1']
    r = rng(1600 if not mem else 1650)
    with pen.group('snow', boil=0.6):
        for i in range(70 if not mem else 46):
            far = i < 40
            sp = (r.uniform(22, 40) if far else r.uniform(48, 80)) * (0.8 if mem else 1.0)
            size = r.uniform(1.4, 2.6) if far else r.uniform(2.8, 4.8)
            amp = r.uniform(4, 12)
            fq = r.uniform(0.25, 0.7)
            ph = r.uniform(0, 6.28)
            xs = r.uniform(-20, x1 + 20)
            ys = r.uniform(0, y1 + 40)
            yy = (ys + sp * t) % (y1 + 40) - 20
            xx = (xs + 8 * t + amp * math.sin(2 * math.pi * fq * t + ph)) % (x1 + 40) - 20
            if not (-10 < xx < x1 - 6 and -10 < yy < y1 - 6):
                continue
            if abs(xx - 281) < 9 + size:
                continue
            pen.dot(xx, yy, size, color='snow', tone=0.0, seed=('flake', i, int(mem)))


def steam(pen, t, amt=1.0):
    """碗上很淡的几缕热气（夜里那碗快凉了，只剩一点）。"""
    cx, cy = BOWL_C
    per = 3.2
    with pen.group('steam', boil=0.8):
        for k in range(3):
            age = ((t + k * per / 3) % per) / per
            a = math.sin(math.pi * age) ** 1.4 * amt
            if a < 0.04:
                continue
            cyc = math.floor((t + k * per / 3) / per)
            r = rng(1700, k, cyc)
            bx = cx + r.uniform(-110, -10)
            yb = cy + SOUP_DY - 8 - age * 110
            L = 60 + 60 * age
            ys = np.linspace(yb, yb - L, 7)
            ph = r.uniform(0, 6.28)
            curl = r.uniform(8, 16) * (0.5 + age)
            xs = bx + curl * np.sin((ys - cy) * 0.035 + ph + t * 1.0) - (cy - ys) * 0.08
            path = np.stack([xs, ys], 1).astype(np.float32)
            w = 6 + 8 * age
            pen.lift(tube(path, [w * 0.4, w, w * 0.7, w * 0.3])[0], amt=0.5 * a, seed=(1710, k, cyc), soft=5.0)
            pen.line(path, w * 0.45, tone=0.13 * a, color='metal', seed=(1720, k, cyc), taper=(0.4, 0.5),
                     role='detail', dry=0.55, dry_from=0.1)


def _beans(g):
    """汤面上的红豆：固定的随机分布（在汤面可见区域里）。→ [(x, y, rx, ry, rot, k)]"""
    cx, cy = g['cx'], g['cy'] + SOUP_DY
    rx, ry = g['r'] * SOUP_K, g['ry'] * SOUP_K
    r = rng(1820)
    out = []
    vis = g['soup_vis'].reshape(-1, 1, 2)
    for _ in range(500):
        if len(out) >= 34:
            break
        a = r.uniform(0, 2 * math.pi)
        rr = math.sqrt(r.uniform(0.02, 0.92))
        x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
        if cv2.pointPolygonTest(vis, (float(x), float(y)), True) < 7:
            continue
        if math.hypot(x - LAND[0], (y - LAND[1]) / 0.55) < 13:      # 落点留出一小块汤面
            continue
        if any((x - q[0]) ** 2 + ((y - q[1]) / 0.55) ** 2 < 15.5 ** 2 for q in out):
            continue
        bx = r.uniform(7.2, 8.6)
        out.append((x, y, bx, bx * r.uniform(0.56, 0.66), r.uniform(-35, 35), len(out)))
    return out


def ripple_age(t, mem):
    """涟漪的“年龄”（秒）；没有涟漪 → None。回忆一侧只在 T1 里接着荡开、慢慢平息。"""
    a = t - T_HIT
    if a < -0.02:
        return None
    if mem and not (T_T1 <= t < T_END + 0.2):
        return None
    return a


def bowl(pen, t, mem):
    g = bowl_geom()
    cx, cy, r, ry = g['cx'], g['cy'], g['r'], g['ry']
    s = 1300
    age = ripple_age(t, mem)
    with pen.group('bowl', boil=0.5):
        # 桌上的影子（光从左上来：影子落在右下）
        pen.shade(ell(cx + 0.22 * r, cy + 0.74 * r, 0.80 * r, 0.11 * r, n=40), amount=0.32, seed=s + 1, soft=8.0)
        pen.cover(g['body'], seed=s + 2, feather=0.8)
        pen.fill(g['body'], 'enamel', seed=s + 3)
        # 碗身的暗面（右侧、下半）
        pen.shade(np.vstack([g['side_r'][::-1], P([[cx + 0.30 * r, cy + 0.66 * r], [cx + 0.55 * r, cy + 0.2 * r],
                                                  [cx + 0.6 * r, cy + 0.9 * ry]])]),
                  amount=0.34, seed=s + 4, angle=70)
        pen.shade(np.vstack([g['foot'], P([[cx + 0.40 * r, cy + 0.60 * r], [cx - 0.40 * r, cy + 0.60 * r]])]),
                  amount=0.25, seed=s + 5)
        # 碗口下一道细细的青花线
        band = np.vstack([ell(cx, cy + 0.10 * r, r * 0.985, ry * 1.02, 2, 178, 30),
                          ell(cx, cy + 0.135 * r, r * 0.975, ry * 1.02, 178, 2, 30)])
        pen.fill(band, 'night_l', seed=s + 6, a_dens=1.2)
        # 碗里的内壁（后半圈，汤面以上）
        pen.fill(ell(cx, cy + 0.6, r - 5.0, ry - 3.5, 0, 360, 64), 'enamel', seed=s + 7)
        pen.shade(np.vstack([ell(cx, cy, r - 6, ry - 4, 185, 300, 18),
                             ell(cx - 0.05 * r, cy + 0.02 * ry, 0.8 * r, 0.55 * ry, 300, 185, 18)]),
                  amount=0.22, seed=s + 8, angle=10)
        # 汤
        vis = g['soup_vis']
        pen.fill(vis, 'soup', seed=s + 10)
        pen.shade(np.vstack([ell(cx, cy + SOUP_DY, r * SOUP_K, ry * SOUP_K, 180, 360, 24),
                             ell(cx, cy + SOUP_DY + 0.25 * ry, r * 0.8, ry * 0.35, 360, 180, 24)]),
                  amount=0.35, seed=s + 11, color='bean_d')
        # 汤面上灯光的倒影（一抹提亮）
        pen.lift(ell(cx - 0.38 * r, cy + SOUP_DY - 0.30 * ry, 0.22 * r, 0.10 * ry, n=24), amt=0.45, seed=s + 12,
                 soft=4.0)
        # 红豆（涟漪经过时轻轻一浮一沉）
        for (bx, by, brx, bry, rot, k) in _beans(g):
            dy = 0.0
            if age is not None and age > 0:
                dist = math.hypot(bx - LAND[0], (by - LAND[1]) / BOWL_K)
                front = 14 + 112 * ease_out(clamp(age / 1.2))
                dy = 2.4 * math.exp(-((dist - front) / 16.0) ** 2) * (1 - clamp(age / 1.4)) \
                    * math.sin((dist - front) * 0.30)
            pen.dot(bx, by + dy, brx, bry, color='bean', tone=1.0, seed=(1830, k), rot=rot)
            pen.dot(bx + 1.0, by + dy + 1.2, brx * 0.78, bry * 0.70, color='bean_d', tone=0.7, seed=(1860, k),
                    rot=rot, shine=False)
        if age is not None:
            ripple(pen, age, vis, amp=1.0 if not mem else (1.0 - clamp((t - T_T1) / 0.9)))
        # 碗口：一圈线（前沿浓、后沿淡）+ 碗身两侧 + 圈足
        pen.line(g['front'], 5.0, tone=0.88, seed=s + 20, taper=(0.06, 0.06), head=0.3, lift=0.2)
        pen.line(ell(cx, cy, r, ry, 180, 360, 32), 3.4, tone=0.66, seed=s + 21, taper=(0.1, 0.1), head=0.2,
                 dry=0.4, dry_from=0.6)
        pen.line(ell(cx, cy + 1.5, r - 7, ry - 4.5, 190, 350, 26), 2.2, tone=0.30, seed=s + 22, taper=(0.3, 0.3),
                 role='detail')
        pen.line(g['side_l'], 6.5, tone=0.88, seed=s + 23, taper=(0.06, 0.25), head=0.5, lift=0.2)
        pen.line(g['side_r'], 4.5, tone=0.72, seed=s + 24, taper=(0.15, 0.2), head=0.3, dry=0.4, dry_from=0.55)
        pen.line(P([(cx - 0.38 * r, cy + 0.68 * r), (cx - 0.36 * r, cy + 0.77 * r), (cx, cy + 0.785 * r),
                    (cx + 0.36 * r, cy + 0.77 * r), (cx + 0.38 * r, cy + 0.68 * r)]), 4.5, tone=0.8, seed=s + 25,
                 taper=(0.1, 0.2), head=0.3)
        pen.line(ell(cx, cy + 0.672 * r, 0.40 * r, 0.04 * r, 15, 165, 12), 2.4, tone=0.45, seed=s + 26,
                 taper=(0.2, 0.3), role='detail')
        # 釉面高光（左侧一笔提白）
        pen.lift(tube([(cx - 0.78 * r, cy + 0.20 * r), (cx - 0.70 * r, cy + 0.38 * r), (cx - 0.55 * r, cy + 0.52 * r)],
                      [4, 9, 3])[0], amt=0.7, seed=s + 27, soft=2.0)


def ripple(pen, age, vis, amp=1.0):
    """泪滴落进汤里：落点一下溅起，一圈圈涟漪荡开（只在汤面上）。amp 整体强度。"""
    if amp <= 0.02:
        return
    lx, ly = LAND
    x0, y0 = int(vis[:, 0].min()) - 4, int(vis[:, 1].min()) - 30
    x1, y1 = int(vis[:, 0].max()) + 5, int(vis[:, 1].max()) + 5
    w, h = x1 - x0, y1 - y0
    soup_m = cv2.erode(_mask([vis], x0, y0, w, h), np.ones((3, 3), np.uint8))
    light = np.zeros((h, w), np.float32)
    dark = np.zeros((h, w), np.float32)
    a_pos = max(age, 0.0)
    for k, (delay, rmax, wid) in enumerate(((0.0, 118.0, 4.4), (0.15, 88.0, 3.6), (0.32, 60.0, 3.0))):
        a = a_pos - delay
        if a <= 0 and not (k == 0 and age > -0.02):
            continue
        u = clamp(a / 1.2)
        rr = 17.0 + rmax * ease_out(u)
        fade = (1.0 - u) ** 1.1
        if fade < 0.03:
            continue
        ww = wid * (1.0 + 0.5 * u)
        outer = ell(lx, ly, rr + ww, (rr + ww) * BOWL_K, n=72)
        inner = ell(lx, ly, max(0.5, rr - ww), max(0.5, rr - ww) * BOWL_K, n=72)
        light = np.maximum(light, _mask([outer], x0, y0, w, h, holes=[inner], blur=1.0) * fade)
        # 波峰外侧的暗边
        o2 = ell(lx, ly + 1.5, rr + ww * 2.6, (rr + ww * 2.6) * BOWL_K, n=72)
        dark = np.maximum(dark, _mask([o2], x0, y0, w, h, holes=[outer], blur=1.2) * fade)
    # 落点：一下子亮起的一小片水花，很快收掉
    if age < 0.35:
        q = 1.0 - clamp(a_pos / 0.35)
        rr = 7 + 8 * (1 - q)
        light = np.maximum(light, _mask([ell(lx, ly, rr, rr * BOWL_K * 1.4, n=24)], x0, y0, w, h, blur=1.5) * q)
    light *= soup_m * amp
    dark *= soup_m * amp
    if dark.max() > 0.02:
        pen.shade(mask=(dark * 0.9, x0, y0), amount=0.45, seed=(1950, 0), color='bean_d')
    if light.max() > 0.02:
        pen.lift(mask=(light, x0, y0), amt=0.85, seed=(1950, 1), soft=0.8)
    # 溅起的小水珠：中间一颗往上跳，两边两颗小的
    if age < 0.26 and amp > 0.5:
        u = clamp(a_pos / 0.26)
        hop = math.sin(math.pi * min(1.0, 0.25 + 0.75 * u))
        for k, (dx, hh, sz) in enumerate(((0.0, 34.0, 5.2), (-18.0, 16.0, 3.4), (17.0, 14.0, 3.2),
                                          (-8.0, 22.0, 2.4), (9.0, 20.0, 2.2))):
            ch.tear_drop(pen, lx + dx * (0.6 + 0.8 * u), ly - 3 - hh * hop, sz, seed=1960 + 7 * k, stretch=0.0,
                         boil=0.3)


def tear_track(pen, pose, t):
    """近侧脸颊上那道湿亮的泪痕（水墨里是提白 + 一道很淡的水痕边）。"""
    k = float(ease_io((t - T_RUN) / 0.65))
    if k < 0.03:
        return
    p = tear_path(pose, k)
    with pen.group('tear_track', boil=0.4):
        L = len(p)
        wv = [2.0] + [4.2] * (L - 2) + [3.2]
        pen.lift(tube(p, wv)[0], amt=0.62, seed=880, soft=1.2)
        pen.line(p + P([1.8, 0.6]), 1.5, tone=0.20, color='water_d', seed=881, taper=(0.4, 0.2), role='detail',
                 dry=0.3, dry_from=0.6)
        # 泪痕下端的一点水光
        e = p[-1]
        pen.lift(ell(e[0] - 0.8, e[1] - 1.0, 2.6, 3.4, n=10), amt=0.9, seed=882, soft=0.5)


def tear(pen, t, pose):
    """那一颗泪：在下颌慢慢聚起来（15.62–15.98），落下（→ 16.26 碰到汤面）。"""
    if t < T_SWELL or t >= T_HIT:
        return
    size = TEAR_R
    if t < T_DROP:
        e = tear_path(pose, 1.0)[-1]
        k = float(ease_io((t - T_SWELL) / (T_DROP - T_SWELL)))
        sz = size * (0.45 + 0.55 * k)
        ch.tear_drop(pen, float(e[0]), float(e[1]) + 1.5 * sz, sz, seed=901, stretch=0.30 * k)
        return
    sx, sy = float(_TS[0]), float(_TS[1])
    u = (t - T_DROP) / (T_HIT - T_DROP)
    lx, ly = LAND
    y = sy + (ly - 8 - sy) * u * u
    x = sx + (lx - sx) * u
    # 下落的轨迹：一道很淡的水线（只在半空中）
    if u > 0.12:
        tail = P([(sx + (x - sx) * 0.4, sy + (y - sy) * 0.55), (x, y - size * 2.4)])
        pen.line(tail, 2.0, tone=0.22, color='water_d', seed=(902, 1), taper=(0.7, 0.05), role='detail',
                 dry=0.5, dry_from=0.0)
    with pen.group('tear_halo', boil=0.3):
        pen.lift(ell(x, y - 0.6 * size, size * 1.7, size * 2.4, n=20), amt=0.35, seed=903, soft=3.0)
    ch.tear_drop(pen, x, y, size, seed=901, stretch=min(1.0, 0.45 + 1.1 * u))


def eye_redness(pen, info, pose, t):
    """眼眶发红：两只眼的下眼睑一抹很淡的红（水墨里唯一的颜色就是红豆红，这一抹更淡）。"""
    k = float(ease_io((t - (T0 + 0.2)) / 1.6))
    if k < 0.03:
        return
    R = ch._GirlRig(pose)
    up = R.head_up
    ang = math.degrees(math.atan2(up[0], -up[1]))
    for j, e in enumerate(info.get('eye') or ()):
        if e is None:
            continue
        c = np.float32(e) - up * 0.042 * S_GIRL
        rx = 0.070 * S_GIRL
        ry = 0.026 * S_GIRL
        poly = ell(c[0], c[1], rx, ry, 0, 360, 24, rot=ang)
        x0, y0 = int(c[0] - rx - 14), int(c[1] - rx - 14)
        m = _mask([poly], x0, y0, int(2 * rx + 28), int(2 * rx + 28), blur=0.35 * ry)
        pen.fill(mask=(m * 0.9, x0, y0), color='bean', tone=0.09 * k, seed=(870, j), rim=0.0, bloom=0.0)


def table_spoon(pen):
    """碗边那把没动过的勺子（只在“现在”里；回忆里它在他手里）。"""
    s = 1500
    cx, cy = BOWL_C
    c = np.float32([cx - BOWL_R - 70, cy + 0.62 * BOWL_R])
    dv = np.float32([-math.cos(math.radians(14)), math.sin(math.radians(14))])
    with pen.group('spoon', boil=0.5):
        pen.shade(ell(c[0] - 40, c[1] + 12, 120, 8, n=30), amount=0.2, seed=s, soft=4.0)
        sp = ell(c[0], c[1], 30, 13, 0, 360, 24, rot=-14)
        handle, Lh, Rh = tube([c + dv * 26, c + dv * 90, c + dv * 150], [8, 7, 10])
        pen.cover([sp, handle], seed=s + 1, feather=0.7)
        pen.fill([sp, handle], 'metal', seed=s + 2)
        pen.shade(ell(c[0] + 4, c[1] + 2, 22, 8, 0, 360, 18, rot=-14), amount=0.3, seed=s + 3)
        pen.line(sp, 3.0, tone=0.8, seed=s + 4, closed=True, taper=(0, 0))
        pen.line(Lh[::5], 2.6, tone=0.75, seed=s + 5, taper=(0.1, 0.2))
        pen.line(Rh[::5], 2.2, tone=0.6, seed=s + 6, taper=(0.1, 0.2))
        pen.lift(ell(c[0] - 8, c[1] - 4, 9, 3, n=10, rot=-14), amt=0.7, seed=s + 7, soft=0.8)


# ================================================================= 他的手（回忆里）
class _Rig:
    def __init__(self, S):
        self.S = S


S_BOY = 1.08 * S_GIRL


def mouth_point(pose):
    R = ch._GirlRig(pose)
    return R.proj(ch._surf(ch.GIRL_FACE, ch.GIRL_FEAT['mouth_y'], 0.0, dz=0.01)[None])[0]


def spoon_pose(t, mpt):
    """勺头中心 c、方向 dv（勺头 → 勺柄，指向右下）。mpt = 她的嘴。"""
    arrive = ease_out((t - T_T1) / (T_SPOON - T_T1))
    ang = 22.0 + 10.0 * (1.0 - arrive)
    dv = np.float32([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    c_final = np.float32(mpt) + dv * 36.0 + np.float32([0, 11.0])     # 勺尖碰到下唇，嘴唇露出来
    nudge = 4.0 * math.sin(math.pi * clamp((t - T_SPOON) / 0.35))       # 到位后轻轻往前一送
    c = c_final + np.float32([330.0, 170.0]) * (1.0 - arrive) - dv * nudge
    return c, dv


def his_hand(pen, t, mpt):
    S = S_BOY
    c, dv = spoon_pose(t, mpt)
    nv = np.float32([dv[1], -dv[0]])           # 勺头“上方”
    sp_len, sp_w = 30.0, 20.0                  # 勺头半长、半宽
    fist = c + dv * 150.0
    hv = np.float32([math.cos(math.radians(200)), math.sin(math.radians(200))])    # 腕 → 拳（朝左上）
    wrist = fist - hv * 0.30 * S
    shoulder = np.float32([2030.0, 780.0])
    l1 = l2 = 1.62 * S
    elbow, wr = ik2(shoulder, wrist, l1, l2, bend=1.0)
    ink = ch._Ink(pen, S)
    rig = _Rig(S)
    with pen.group('his_hand', boil=1.0):
        # 勺柄（在拳头后面穿出来）
        handle, Lh, Rh = tube([c + dv * (sp_len - 4), c + dv * 100.0, fist + dv * 20.0], [7.0, 8.0, 10.0])
        pen.cover([handle], seed=2101, feather=0.6)
        pen.fill([handle], 'metal', seed=2102)
        pen.line(Lh[::5], 2.6, tone=0.75, seed=2103, taper=(0.1, 0.2))
        pen.line(Rh[::5], 2.0, tone=0.5, seed=2104, taper=(0.1, 0.2))
        # 手臂（藏青毛衣）：从画面右边伸进来，肘微弯
        path = [shoulder + (shoulder - elbow) * 0.15, elbow, (elbow + wr) / 2, wr]
        arm, La, Ra = tube(path, [0.44 * S, 0.40 * S, 0.34 * S, 0.29 * S])
        pen.cover([arm], seed=2110, feather=0.8)
        pen.fill([arm], 'boy_sweater', seed=2111)
        pen.shade([np.vstack([Ra, spline(path, 2.0)[::-1]])], amount=0.35, seed=2112, angle=120)
        pen.line(La[::6], 0.040 * S, tone=0.85, seed=2113, taper=(0.1, 0.25), head=0.4, dry=0.4, dry_from=0.6)
        pen.line(Ra[::6], 0.034 * S, tone=0.72, seed=2114, taper=(0.1, 0.25), head=0.3, dry=0.5, dry_from=0.5)
        # 肘弯的两道褶
        fv = (wr - elbow) / (np.hypot(*(wr - elbow)) + 1e-6)
        fn = np.float32([-fv[1], fv[0]])
        for k, o in enumerate((0.06, 0.20)):
            p0 = elbow + fv * o * S - fn * 0.10 * S
            pen.line(P([p0, p0 + fv * 0.06 * S + fn * 0.06 * S, p0 + fv * 0.07 * S + fn * 0.13 * S]), 0.018 * S,
                     tone=0.5, seed=2118 + k, role='detail', taper=(0.3, 0.5), dry=0.5, dry_from=0.4)
        # 罗纹袖口 + 里面露出一点白衬衫袖口
        cw = 0.150 * S
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
        for k in range(8):
            q = (k + 0.5) / 8 * 2 - 1
            p0 = cc + fn * cw * q * 0.95 - fv * 0.06 * S
            pen.line(P([p0, p0 + fv * 0.13 * S]), 1.8, tone=0.42, seed=(2116, k), role='detail', taper=(0.2, 0.2))
        pen.line(P([cc - fn * cw - fv * 0.07 * S, cc + fn * cw - fv * 0.07 * S]), 3.0, tone=0.7, seed=2117,
                 taper=(0.1, 0.1), role='detail')
        pen.line(P([cc - fn * cw * 0.96 + fv * 0.08 * S, cc + fn * cw * 0.96 + fv * 0.08 * S]), 3.0, tone=0.75,
                 seed=2126, taper=(0.1, 0.1))
        # 手：握着勺柄（拇指压在柄上）
        ch._hand(ink, rig, wr + fv * 0.04 * S, fist, shape='fist', thumb=1, seed=2120, size=1.9)
        # 勺头（在她嘴边）：一勺红豆汤
        rot = math.degrees(math.atan2(dv[1], dv[0]))
        bowl_s = ell(c[0], c[1], sp_len, sp_w * 0.62, 0, 360, 28, rot=rot)
        pen.cover([bowl_s], seed=2130, feather=0.6)
        pen.fill([bowl_s], 'metal', seed=2131)
        inner = ell(c[0] - dv[0] * 2 + nv[0], c[1] - dv[1] * 2 + nv[1], sp_len * 0.78, sp_w * 0.42, 0, 360, 24,
                    rot=rot)
        pen.fill([inner], 'soup', seed=2132)
        for k, (a, b) in enumerate(((-0.35, 0.05), (0.12, -0.10), (0.42, 0.12))):
            bx = c + dv * (a * sp_len) + nv * (b * sp_w)
            pen.dot(bx[0], bx[1], 5.4, 3.6, color='bean', tone=1.0, seed=(2133, k), rot=rot + 20 * k)
        pen.line(bowl_s, 2.6, tone=0.8, seed=2134, closed=True, taper=(0, 0))
        pen.lift(ell(c[0] - dv[0] * 12 + nv[0] * 6, c[1] - dv[1] * 12 + nv[1] * 6, 6, 2.5, n=10), amt=0.7,
                 seed=2135, soft=0.8)


# ================================================================= 场景
def draw(pen, **kw):
    t = float(kw.get('t', pen.t))
    style = kw.get('style', pen.style)
    mem = style != 'C'
    with pen.group('bg', boil=BG_BOIL, cache=('table_cu', 'A' if mem else 'C', pen.d % 3)):
        background(pen, mem)
    snow(pen, t, mem)
    if not mem:
        table_spoon(pen)
    bowl(pen, t, mem)
    steam(pen, t, amt=1.0 if mem else 0.6)
    if mem:
        gp = girl_pose_a(t)
        ch.girl(pen, gp)
        his_hand(pen, t, mouth_point(gp))
    else:
        gp = girl_pose_c(t)
        info = ch.girl(pen, gp)
        eye_redness(pen, info, gp, t)
        tear_track(pen, gp, t)
        tear(pen, t, gp)
