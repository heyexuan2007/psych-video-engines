# -*- coding: utf-8 -*-
"""人物定妆 2（cast3 追加的姿势）：python preview.py _castsheet2 <A|B|C|F> 0 out.png kind=serve u=0.7
kind:
  serve    第 3 镜：她站在桌边盛汤（mode=ladle，u 0..1 一勺的进度）/ 推碗（mode=push，u）/ 摆勺子（mode=place）
  os       第 4 镜：过肩——她的背影在左下前景，桌子对面草稿的他伸手够勺子（u 伸手，dust 化灰，erase）
  reach    第 4 镜：他（草稿）伸手够勺子的近景（u, dust）
  feed     第 6 镜：他（上色）喂她，她 eat（u 0 吹凉 → 1 送到嘴边）
  kiss     第 7 镜：窗边，他低头亲她额头（k, look_up）
  hug      T2：她靠在他胸口（hug, look_away, loosen）
  walk     第 8 镜：一排小人——她站着按胸口看门（look 0..1）、他起身（rise）、侧面走（gait）、背面走、背对开门（u）
  night    第 15 镜：她正面近景，低头 → 抬脸 resolve → 攥着红豆的拳头按在胸口（a 0..1 表演进度）
zoom/cx/cy：用 pen.view 放大（不写 = 1）。"""
import math

import numpy as np

import characters as ch

from core import rect, ell, spline, tube, densify, smooth01, clamp, lerp, W, H


def D(pts, sp=20.0):
    return densify(np.float32(pts), sp)


def _paper(pen, col='wall'):
    with pen.group('bg', boil=0.3):
        pen.fill([rect(-10, -10, W + 10, H + 10)], col, seed=1)


def _table(pen, y, x0=-10, x1=W + 10, col='wood', seed=10):
    with pen.group('table', boil=0.4):
        pen.cover([rect(x0, y, x1, H + 10)], seed=seed)
        pen.fill([rect(x0, y, x1, H + 10)], col, seed=seed + 1, grad=(0, y, 0, H, 1.0, 0.7))
        pen.line(D([(x0, y), (x1, y)], 30), 7, tone=0.85, color='wood_d', seed=seed + 2, taper=(0.02, 0.05))


def _pot(pen, c, rx, seed=40):
    cx, cy = c
    ry = rx * 0.26
    with pen.group('pot', boil=0.5):
        body = np.vstack([ell(cx, cy, rx, ry, 180, 360, 20), [[cx + rx, cy + rx * 0.75], [cx - rx, cy + rx * 0.75]]])
        pen.cover([body], seed=seed)
        pen.fill([body], '#45474F', seed=seed + 1)
        pen.shade([body], amount=0.3, seed=seed + 2, grad=(cx - rx, 0, cx + rx, 0, 1.0, 0.2))
        pen.fill([ell(cx, cy + 2, rx * 0.88, ry * 0.7)], 'soup', seed=seed + 3)
        for k in range(7):
            a = k * 2.3
            pen.dot(cx + rx * 0.6 * math.cos(a) * (0.3 + 0.1 * k), cy + 2 + ry * 0.4 * math.sin(a), rx * 0.06,
                    rx * 0.045, 'bean', seed=seed + 10 + k, rot=k * 30)
        pen.line(ell(cx, cy, rx, ry), 5, tone=0.85, seed=seed + 4, closed=True, taper=(0, 0))
        pen.line(D([(cx - rx, cy), (cx - rx, cy + rx * 0.75), (cx + rx, cy + rx * 0.75), (cx + rx, cy)], 16), 6,
                 tone=0.9, seed=seed + 5)


def draw(pen, kind='serve', **kw):
    z = float(kw.get('zoom', 1.0))
    cx, cy = float(kw.get('cx', W / 2)), float(kw.get('cy', H / 2))
    with pen.view(z, W / 2 - z * cx, H / 2 - z * cy):
        globals()['k_' + kind](pen, **kw)


# ------------------------------------------------------------------ 第 3 镜
def k_serve(pen, **kw):
    _paper(pen)
    ty = 610
    _table(pen, ty)
    mode = kw.get('mode', 'ladle')
    u = float(kw.get('u', 0.7))
    s = 150
    gp = dict(x=760, y=390, s=s, facing=1, yaw=float(kw.get('yaw', 34)), pitch=float(kw.get('pitch', 24)),
              roll=3, lean=float(kw.get('lean', 0.22)), face=kw.get('expr', 'neutral'), clip_y=ty + 2, clip_arms=False,
              seed=1000,
              breath=0.2)
    pot_c, bowl_c, br = (905, 612), (1065, 646), 58
    if mode == 'ladle':
        gp.update(arm='ladle', arm_args=dict(pot=(pot_c[0], pot_c[1] + 4), bowl=bowl_c, r=br, u=u))

        def props(pen):
            _pot(pen, pot_c, 92)
            ch.bowl(pen, bowl_c, br, seed=301)
        ch.girl_with(pen, gp, props)
    elif mode == 'push':
        args = dict(bowl=(900, 650), to=(1040, 636), r=br, u=u)
        gp.update(arm='push', arm_args=args, face=kw.get('expr', 'wistful_smile'), lean=0.15 + 0.35 * u)
        pos = lerp(np.float32(args['bowl']), np.float32(args['to']), float(smooth01(u)))

        def props(pen):
            _pot(pen, (1260, 600), 100)
            ch.bowl(pen, pos, br, seed=302)
        ch.girl_with(pen, gp, props)
    else:
        args = dict(spoon=(960, 640), to=(1120, 655), u=u)
        gp.update(arm='place', arm_args=args, face=kw.get('expr', 'wistful_smile'))

        def props(pen):
            ch.bowl(pen, (1230, 640), br, seed=302)
        ch.girl_with(pen, gp, props)


# ------------------------------------------------------------------ 第 4 镜
def _spoon_on_table(pen, c, L=70, ang=-160, seed=60, sketchy=False):
    c = np.float32(c)
    dv = np.float32([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    with pen.group('spoon', boil=0.5):
        sp = ell(c[0], c[1], L * 0.22, L * 0.11, 0, 360, 20, rot=ang)
        hd, Lh, Rh = tube([c + dv * L * 0.2, c + dv * L * 0.6, c + dv * L], [5, 5, 7])
        pen.cover([sp, hd], seed=seed)
        pen.fill([sp, hd], 'metal', seed=seed + 1)
        pen.line(sp, 2.5, tone=0.8, seed=seed + 2, closed=True, taper=(0, 0))
        pen.line(Lh[::5], 2.2, tone=0.7, seed=seed + 3)


def k_os(pen, **kw):
    _paper(pen)
    u = float(kw.get('u', 1.0))
    # 桌面（远处，略俯视）
    with pen.group('table', boil=0.4):
        top = np.float32([(-10, 640), (W + 10, 640), (W + 10, H + 10), (-10, H + 10)])
        pen.cover([top], seed=10)
        pen.fill([top], 'wood', seed=11, grad=(0, 640, 0, H, 0.8, 1.0))
        pen.line(D([(-10, 640), (W + 10, 640)], 30), 8, tone=0.85, color='wood_d', seed=12)
    sp = (1150, 700)
    by = 640 - 1.18 * 96
    vis = np.float32([(-50, -50), (W + 50, -50), (W + 50, 642), (-50, 642)])
    with pen.group('bowl', boil=0.5):
        ch.bowl(pen, (1290, 690), 62, seed=330)
    _spoon_on_table(pen, sp)
    bp = dict(x=1200, y=by, s=96, facing=-1, yaw=float(kw.get('byaw', 22)), pitch=8, roll=4, face='gentle',
              act='reach', target=sp, u=u, clip_poly=vis, seed=2000, opacity=0.62, boil=2.1,
              erase=float(kw.get('erase', 0.0)), dust=float(kw.get('dust', 0.0)), breath=0.3)
    ch.boy_act(pen, bp, mode=kw.get('boy_mode', 'sketch'))
    # 她的背影（过肩，左下前景）
    gp = dict(x=430, y=760, s=300, back=True, body='sit', yaw=float(kw.get('yaw', 152)), pitch=float(kw.get('pitch', 6)),
              roll=float(kw.get('roll', 4)), seed=1000, arm='back_table', breath=0.1, light=-1)
    ch.girl(pen, gp)


def k_reach(pen, **kw):
    _paper(pen)
    _table(pen, 700)
    sp = (930, 760)
    _spoon_on_table(pen, sp, L=110)
    vis = np.float32([(-50, -50), (W + 50, -50), (W + 50, 702), (-50, 702)])
    bp = dict(x=1000, y=700 - 1.18 * 170, s=170, facing=-1, yaw=float(kw.get('byaw', 24)), pitch=10, roll=4,
              face=kw.get('expr', 'gentle'), act='reach', target=sp, u=float(kw.get('u', 1.0)), clip_poly=vis,
              seed=2000, opacity=0.64, boil=2.1, erase=float(kw.get('erase', 0.0)), dust=float(kw.get('dust', 0.0)))
    ch.boy_act(pen, bp, mode=kw.get('boy_mode', 'sketch'))


# ------------------------------------------------------------------ 第 6 镜
def k_feed(pen, **kw):
    _paper(pen)
    ty = 600
    _table(pen, ty)
    u = float(kw.get('u', 1.0))
    gp = dict(x=760, y=420, s=150, facing=1, yaw=float(kw.get('yaw', 50)), pitch=float(kw.get('pitch', 2)), roll=-4,
              lean=0.32, face=kw.get('expr', 'eat'), clip_y=ty + 2, clip_arms=False, seed=1000, arm='catch',
              arm_args=dict(u=float(kw.get('catch', 1.0))), breath=0.3)
    ch.bowl(pen, (850, 640), 66, seed=303)
    ch.girl(pen, gp)
    mt = ch.girl_mouth_point(gp)
    bp = dict(x=1250, y=415, s=162, facing=-1, yaw=float(kw.get('byaw', 48)), pitch=float(kw.get('bpitch', 6)),
              roll=5, face=kw.get('bexpr', 'gentle' if u > 0.3 else 'blow'), act='feed', target=mt, u=u,
              bowl=(1120, 640), bowl_r=0.24 * 162, clip_y=ty + 2, seed=2000, breath=0.6, lean=0.18)
    ch.boy_act(pen, bp, mode=kw.get('boy_mode', 'full'))


# ------------------------------------------------------------------ 第 7 镜 / T2
def _window_bg(pen):
    with pen.group('bg', boil=0.3, cache=('cs2_win', pen.d % 3)):
        pen.fill([rect(-10, -10, W + 10, H + 10)], 'wall', seed=1)
        g = rect(1180, 80, 1820, 760)
        pen.cover([g], seed=20)
        pen.fill([g], 'sky', seed=21)
        pen.line(D([(1180, 80), (1820, 80), (1820, 760), (1180, 760), (1180, 80)], 30), 12, seed=22, tone=0.9)
        pen.line(D([(1500, 80), (1500, 760)], 30), 9, seed=23, tone=0.85)


def k_kiss(pen, **kw):
    _window_bg(pen)
    p = dict(x=760, y=520, s=200, k=float(kw.get('k', 1.0)), look_up=float(kw.get('up', 0.0)),
             breath=0.2, light=1, seed=1000)
    info = ch.couple(pen, p)
    if kw.get('mark'):
        f = info['forehead']
        pen.dot(f[0], f[1], 4, color='bean')


def k_hug(pen, **kw):
    _window_bg(pen)
    p = dict(x=760, y=520, s=200, hug=float(kw.get('hug', 1.0)), look_away=float(kw.get('away', 0.0)),
             loosen=float(kw.get('loosen', 0.0)), breath=0.2, light=1, seed=1000)
    ch.couple(pen, p)


# ------------------------------------------------------------------ 第 8 镜
def k_walk(pen, **kw):
    _paper(pen)
    fl = 900
    with pen.group('floor', boil=0.4):
        pen.line(D([(-10, fl), (W + 10, fl)], 30), 5, tone=0.6, seed=5)
    sk = kw.get('boy_mode', 'sketch')
    s = 56
    look = float(kw.get('look', 0.5))
    face = ch.mix_expr('sad_down', dict(ch.EXPR['sad_down'], gx=0.6, gy=0.1, open=0.55), look)
    gp = dict(x=170, y=fl - 4.69 * s, s=s, body='stand', facing=1, yaw=40 + 15 * look, pitch=18 - 14 * look, roll=3,
              face=face, arm='hand_chest', arm_args=dict(u=1.0), seed=1000, breath=0.3)
    ch.girl(pen, gp)
    Sb = 1.08 * s
    ch.boy_act(pen, dict(x=520, y=0, floor=fl, s=Sb, facing=1, yaw=40, pitch=10, act='rise',
                         rise=float(kw.get('rise', 0.5)), table=(600, fl - 3.0 * Sb), face='neutral', seed=2000), sk)
    for k, g_ in enumerate((0.0, 0.25, 0.5, 0.75)):
        if k > 1 and not kw.get('all'):
            break
        ch.boy_act(pen, dict(x=830 + 230 * k, y=0, floor=fl, s=Sb, facing=1, yaw=62, pitch=4, act='walk',
                             gait=float(kw.get('gait', g_)) if k == 0 else g_, face='neutral', seed=2000), sk)
    ch.boy_act(pen, dict(x=1390, y=fl - 4.79 * Sb, s=Sb, back=True, act='walk', gait=float(kw.get('gait', 0.25)),
                         face='neutral', seed=2000, yaw=172), sk)
    with pen.group('door', boil=0.4):
        pen.line(D([(1790, fl), (1790, fl - 6.6 * Sb), (1640, fl - 6.6 * Sb - 20), (1640, fl + 20)], 20), 6,
                 tone=0.8, seed=6)
    ch.boy_act(pen, dict(x=1660, y=fl - 4.79 * Sb, s=Sb, act='door', handle=(1750, fl - 3.3 * Sb),
                         u=float(kw.get('u', 1.0)), gait=0.0, step=0.4, face='neutral', seed=2000, yaw=170,
                         dust=float(kw.get('dust', 0.0)), wind=(-1.0, -0.3)), sk)


# ------------------------------------------------------------------ 第 15 镜
def k_night(pen, **kw):
    _paper(pen)
    ty = 900
    _table(pen, ty, col='wood_d')
    a = float(kw.get('a', 1.0))
    up = float(smooth01(a / 0.35))
    fist = float(smooth01((a - 0.45) / 0.45))
    face = ch.mix_expr('sad_down', 'resolve', up)
    gp = dict(x=960, y=520, s=230, facing=1, yaw=float(kw.get('yaw', 20)), pitch=lerp(30, 2, up), roll=lerp(6, 2, up),
              face=kw.get('expr', face), clip_y=ty + 2, clip_arms=False, seed=1000, light=-1,
              arm='fist_chest', arm_args=dict(u=fist, grip=float(kw.get('grip', 0.3 + 0.7 * fist)),
                                              press=float(kw.get('press', fist))), breath=0.25)
    ch.girl_front(pen, gp)
