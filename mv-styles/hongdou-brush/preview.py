# -*- coding: utf-8 -*-
"""预览：python preview.py <场景模块> <笔刷 A|B|C|F> <成片时间秒> <输出.png> [key=value ...]
场景模块在 scenes/ 下，需提供 draw(pen, **kw)。额外的 key=value 原样传给 draw（数字自动转 float）。
F = 平涂调试笔刷（只看几何）。会同时画上该时刻的歌词。"""
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'scenes')]

import numpy as np
from PIL import Image

import core


def get_brush(key):
    if key == 'F':
        return core.FlatBrush()
    mod = importlib.import_module('brush_' + key.lower())
    return getattr(mod, 'Brush' + key.upper())()


def render(scene, brush_key, ct, lyrics=True, **kw):
    d = core.draw_index(ct)
    pen = core.Pen(brush_key if brush_key != 'F' else 'C', d)
    importlib.import_module(scene).draw(pen, **kw)
    b = get_brush(brush_key)
    img = b.render(pen.ops, d)
    if lyrics:
        img = b.paint_text(img, core.lyric_items(d, brush_key), d)
    return img


if __name__ == '__main__':
    scene, bk, ct, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    kw = {}
    for a in sys.argv[5:]:
        k, v = a.split('=', 1)
        try:
            v = float(v)
        except ValueError:
            pass
        kw[k] = v
    t0 = time.time()
    img = render(scene, bk, ct, **kw)
    Image.fromarray(core.to_u8(img)).save(out)
    print(f'{out}  {time.time() - t0:.2f}s')
