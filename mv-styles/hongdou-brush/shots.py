# -*- coding: utf-8 -*-
"""分镜表（对应 ../分镜剧情.md）。时间是成片时间，切点 = 字时间 − 0.12 或拍点。

每个镜头：dict(t0, scene, kw, cam, note)
  scene  scenes/ 下的模块名（模块提供 draw(pen, **kw)；pen.t 成片时间，pen.lt 镜头内时间，pen.dur 镜头时长）
  kw     传给 draw 的参数
  cam    可选，位图镜头（只用于极小的推拉 ≤5%）：dict(z0, z1, cx, cy)；大的推拉请在场景里用 pen.view
还没写好的场景会用占位卡顶替（画面上写着场景名），方便先看节奏。
场景模块名不要和 Python 标准库重名（例如 calendar → calendar_cu）。
"""

SHOTS = [
    dict(t0=0.00, scene='kitchen', kw={}, cam=dict(z0=1.0, z1=1.03, cx=900, cy=480), note='1 第十七句一句示'),
    dict(t0=5.01, scene='pot', kw={}, note='2 第十八句句示例'),
    dict(t0=8.83, scene='table', kw=dict(mode='serve'), note='3 示例歌词'),
    dict(t0=11.97, scene='table_os', kw={}, note='4 示例歌词'),
    dict(t0=14.07, scene='table_cu', kw={}, note='5 第二十句例 + T1'),
    dict(t0=17.43, scene='memory_table', kw={}, note='6 第一句这是一句'),
    dict(t0=21.59, scene='window_kiss', kw={}, note='7 第二十一句歌词 + T2'),
    dict(t0=30.28, scene='kitchen', kw=dict(mode='door'), note='8 第二十三句'),
    dict(t0=34.20, scene='threshold', kw={}, note='9 雪脚印'),
    dict(t0=36.64, scene='clock', kw={}, note='10 有时候'),
    dict(t0=38.64, scene='calendar_cu', kw={}, note='11 有时候'),
    dict(t0=40.83, scene='jar', kw={}, note='12 第十句一句示例歌词'),
    dict(t0=45.14, scene='shelf', kw={}, note='13 第十一句句示例歌'),
    dict(t0=49.49, scene='candle', kw={}, note='14 第十二句示例歌词用'),
    dict(t0=53.76, scene='night_mcu', kw={}, note='15 第十三句例歌'),
    dict(t0=58.09, scene='thread_hands', kw={}, note='16 第十四句歌词用来演'),
    dict(t0=61.88, scene='window_back', kw={}, note='T3 第十五句这是一'),
    dict(t0=66.17, scene='river', kw=dict(mode='together'), note='17 示例歌词'),
    dict(t0=69.81, scene='river_hands', kw={}, note='18 示例歌词'),
    dict(t0=72.80, scene='river', kw=dict(mode='ending'), note='19 尾声 + T4 + 淡黑'),
]

# 转场时“新风格那一侧”画什么：T3 由窗前（C）涂成河边（B），两侧场景不同
TRANS_SCENE = {
    'patches': dict(scene='river', kw=dict(mode='together')),
}
# T1 水彩晕开的起点（屏幕坐标：碗里的红豆）。场景写好后按实际构图改。
BLOOM_CENTER = (760, 820)
