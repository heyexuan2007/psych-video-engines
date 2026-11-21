# -*- coding: utf-8 -*-
"""人物测试场景（定妆）：python preview.py _castsheet <A|B|C|F> 0 out.png kind=face expr=wistful_smile zoom=3
kind:
  face      她的上半身特写（厨房同款角度），expr 表情名，look=pot|him|down|front 或 yaw/pitch/roll
  him       他（托腮，sit_chin），mode=sketch|full
  sit_side  她坐在餐桌前的侧面近景（低头看碗，一只手扶碗沿），expr，drop 0..1 泪滴下落进度
  back_stand 她站在窗前的背影（一只手在胸前攥着红线，另一只垂着）
  back_pair  她和他并肩坐在草地上的背影，lean 0..1 她把头靠到他肩上，boy_mode
zoom/cx/cy：用 pen.view 把 (cx, cy) 放大 zoom 倍放到画面中心（不写 = 按 kind 自动）。"""
import math

import numpy as np

from core import rect, ell, spline, W, H
import characters as ch

LOOK = {'pot': (38, 21, 3), 'him': (46, 7, -5), 'down': (41, 27, 6), 'front': (30, 4, 0), 'side': (70, 8, 0)}


def _bg(pen, kind):
    with pen.group('bg', boil=0.3):
        pen.fill([rect(-10, -10, W + 10, H + 10)], 'wall', seed=1)
        if kind in ('face', 'him'):
            pen.fill([rect(-10, -10, W + 10, 300)], 'night', seed=2)
            pen.line([(-10, 300), (W + 10, 300)], 6, seed=3)
        if kind == 'back_pair':
            pen.fill([rect(-10, -10, W + 10, 430)], 'dusk', seed=4)
            pen.fill([rect(-10, 430, W + 10, 640)], 'water', seed=5)
            pen.fill([rect(-10, 640, W + 10, H + 10)], 'grass', seed=6)
        if kind == 'back_stand':
            pen.fill([rect(560, 120, 1360, 760)], 'night', seed=7)
            pen.line(np.float32([(560, 120), (1360, 120), (1360, 760), (560, 760), (560, 120)]), 10, seed=8)
        if kind == 'sit_side':
            pen.fill([rect(-10, 720, W + 10, H + 10)], 'wood', seed=9)
            pen.line([(-10, 720), (W + 10, 720)], 8, seed=10)


def girl_face_pose(expr='neutral', look='pot', **kw):
    yaw, pitch, roll = LOOK[look] if isinstance(look, str) else look
    p = dict(x=560, y=448, s=110, facing=1, yaw=float(kw.get('yaw', yaw)), pitch=float(kw.get('pitch', pitch)),
             roll=float(kw.get('roll', roll)), face=expr, clip_y=448 + 1.25 * 110, seed=1000, lean=0.05)
    return p


def _auto_view(kind, kw, info_pt):
    z = float(kw.get('zoom', 1.0))
    cx = float(kw.get('cx', info_pt[0]))
    cy = float(kw.get('cy', info_pt[1]))
    return z, W / 2 - z * cx, H / 2 - z * cy


def draw(pen, kind='face', **kw):
    _bg(pen, kind)
    if kind == 'face':
        expr = kw.get('expr', 'neutral')
        look = kw.get('look', {'neutral': 'pot', 'wistful_smile': 'him', 'sad_down': 'down', 'closed_smile': 'front',
                               'cry': 'down'}.get(expr, 'front'))
        p = girl_face_pose(expr, look, **{k: v for k, v in kw.items() if k in ('yaw', 'pitch', 'roll')})
        R = ch._GirlRig(p)
        hc = R.proj(np.float32([[0.0, 0.08, 0.0]]))[0]
        z, ox, oy = _auto_view(kind, kw, hc)
        with pen.view(z, ox, oy):
            _bg_local(pen)
            ch.girl(pen, p)
    elif kind == 'him':
        p = dict(x=1418, y=508, s=126, facing=-1, yaw=36, pitch=-7, roll=7, face=kw.get('expr', 'smile'),
                 pose='sit_chin', seed=2000, clip_y=508 + 1.15 * 126)
        mode = kw.get('mode', 'full')
        R = ch._BoyRig(p)
        hc = R.proj(np.float32([[0.0, 0.25, 0.0]]))[0]
        z, ox, oy = _auto_view(kind, kw, hc + np.float32([float(kw.get('dx', 10)), float(kw.get('dy', 70))]))
        with pen.view(z, ox, oy):
            if mode == 'sketch':
                p['opacity'] = 0.64
                p['boil'] = 2.1
            ch.boy(pen, p, mode=mode)
    elif kind == 'sit_side':
        # 第 5 镜：侧面近景，她低头看着面前的碗，手扶碗沿，流泪；泪滴由场景控制
        table_y = 735
        bc, br_ = (975, 845), 112
        p = dict(x=800, y=470, s=215, facing=1, yaw=float(kw.get('yaw', 48)), pitch=float(kw.get('pitch', 31)),
                 roll=float(kw.get('roll', 5)), face=kw.get('expr', 'cry'), seed=1000, lean=0.30,
                 clip_y=table_y + 2, clip_arms=False, arm='bowl_rim', arm_args=dict(bowl=bc, r=br_))
        z, ox, oy = _auto_view(kind, kw, (W / 2, H / 2))
        with pen.view(z, ox, oy):
            with pen.group('table', boil=0.4):
                pen.fill([rect(-10, table_y, W + 10, H + 10)], 'wood', seed=11)
                pen.line([(-10, table_y), (W + 10, table_y)], 7, seed=12)
            ch.bowl(pen, bc, br_, seed=300)
            ch.girl(pen, p)
            drop = float(kw.get('drop', 0.5))
            if drop > 0:
                t0 = ch.girl_tear_point(p)
                y1 = bc[1] - 6
                yy = t0[1] + (y1 - t0[1]) * drop ** 1.6
                ch.tear_drop(pen, t0[0] + 4 * drop, yy, 0.045 * p['s'], seed=901, stretch=min(1.0, drop * 1.5))
    elif kind == 'back_stand':
        p = dict(x=960, y=330, s=100, back=True, body='stand', seed=1000, arm='hold_line', yaw=float(kw.get('yaw', 168)),
                 arm_args=dict(tug=float(kw.get('tug', 0.3))))
        z, ox, oy = _auto_view(kind, kw, (W / 2, H / 2))
        with pen.view(z, ox, oy):
            info = ch.girl(pen, p)
            h = info.get('hand')
            if h is not None:
                pen.line(np.float32([h + (6, -4), (h[0] + 140, h[1] - 70), (1330, 300)]), 4, color='redline',
                         seed=77, role='detail')
    elif kind == 'back_pair':
        z, ox, oy = _auto_view(kind, kw, (W / 2, H / 2))
        with pen.view(z, ox, oy):
            ch.pair_sit_back(pen, dict(x=960, y=900, s=150, lean=float(kw.get('lean', 1.0)),
                                       boy_mode=kw.get('boy_mode', 'full'), seed=1000))
    else:
        raise ValueError(kind)


def _bg_local(pen):
    pass
