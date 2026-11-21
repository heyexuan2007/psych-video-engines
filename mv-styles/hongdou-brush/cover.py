# -*- coding: utf-8 -*-
"""封面：python cover.py [输出目录]
  cover_4x3.png（1440×1080）：全片高潮（油画棒河边，她靠在他肩上）裁成 4:3，上方压大标题。
  cover_3x4.png（1080×1440）：宣纸底，上方标题，中间河边主图，下面并排三张小图（水墨 / 水彩 / 油画棒），底部一句歌词。
画面都是不带歌词的场景渲染。"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'scenes')]

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import core

TITLE_FONT = os.path.join(core.FONT_DIR, 'STXINGKA.TTF')
SUB_FONT = os.path.join(core.FONT_DIR, 'STKAITI.TTF')
RED = (168, 38, 46)
CREAM = (250, 242, 226)
INK = (43, 39, 36)

# 封面用的画面：(场景, 笔刷, 成片秒, kw, 取景中心 x)
HERO = ('river', 'B', 69.2, dict(mode='together'), 940)
THUMBS = [('table_cu', 'C', 15.6, {}, '水墨 · 现在'), ('memory_table', 'A', 19.5, {}, '水彩 · 回忆'),
          ('river', 'B', 69.2, dict(mode='together'), '油画棒 · 也许')]


def render_scene(name, key, ct, kw):
    d = core.draw_index(ct)
    pen = core.Pen(key, d)
    pen.lt, pen.dur = 1.0, 3.0
    try:
        mod = importlib.import_module(name)
    except ModuleNotFoundError:
        mod = importlib.import_module('table_cu')     # 场景还没做好时的替身
        kw = {}
    mod.draw(pen, **kw)
    b = getattr(importlib.import_module('brush_' + key.lower()), 'Brush' + key)()
    return Image.fromarray(core.to_u8(b.render(pen.ops, d)))


def glow_text(img, xy, text, font, fill, glow=(18, 12, 26), glow_r=14, glow_a=200, anchor='mm', spacing=0):
    """带柔和暗色光晕的字（不是实心框），保证压在复杂画面上也认得出。"""
    W, H = img.size
    lay = Image.new('L', (W, H), 0)
    ImageDraw.Draw(lay).text(xy, text, font=font, fill=255, anchor=anchor, spacing=spacing)
    halo = lay.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(glow_r))
    halo = halo.point(lambda v: min(255, int(v * glow_a / 255 * 1.6)))
    img.paste(Image.new('RGB', (W, H), glow), (0, 0), halo)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor=anchor, spacing=spacing)


def cover_4x3(hero, out):
    cx = HERO[4]
    x0 = int(min(max(cx - 720, 0), 1920 - 1440))
    im = hero.crop((x0, 0, x0 + 1440, 1080))
    # 顶部压暗一点，让标题更清楚
    arr = np.asarray(im, np.float32)
    g = np.clip(1 - np.arange(1080) / 420.0, 0, 1)[:, None, None] ** 1.6
    arr = arr * (1 - 0.35 * g)
    im = Image.fromarray(arr.astype(np.uint8))
    glow_text(im, (720, 170), '红 豆', ImageFont.truetype(TITLE_FONT, 230), CREAM, glow_r=18)
    glow_text(im, (720, 318), '演唱者  ·  逐帧手绘 MV', ImageFont.truetype(SUB_FONT, 52), CREAM, glow_r=10)
    glow_text(im, (720, 1000), '第十六句是一句示例歌词', ImageFont.truetype(TITLE_FONT, 66), (255, 214, 190),
              glow_r=12)
    im.save(out)
    return out


def cover_3x4(hero, thumbs, out):
    W, H = 1080, 1440
    paper = (np.asarray(Image.new('RGB', (W, H), (244, 241, 234)), np.float32)
             + 6 * core.vnoise(H, W, 3, 77, 2)[..., None])
    im = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 150), '红 豆', font=ImageFont.truetype(TITLE_FONT, 210), fill=RED, anchor='mm')
    d.text((W / 2, 290), '演唱者  ·  逐帧手绘 MV', font=ImageFont.truetype(SUB_FONT, 48), fill=INK, anchor='mm')
    # 主图：河边
    cx = HERO[4]
    hx0 = int(min(max(cx - 840, 0), 1920 - 1680))
    h = hero.crop((hx0, 60, hx0 + 1680, 1005)).resize((1000, 562), Image.LANCZOS)
    im.paste(h, (40, 350))
    # 三张小图
    tw, th = 320, 180
    for k, (t_im, label) in enumerate(thumbs):
        x = 40 + k * (tw + 20)
        im.paste(t_im.resize((tw, th), Image.LANCZOS), (x, 950))
        d.text((x + tw / 2, 1160), label, font=ImageFont.truetype(SUB_FONT, 38), fill=INK, anchor='mm')
    d.text((W / 2, 1290), '第十六句是一句示例歌词', font=ImageFont.truetype(TITLE_FONT, 70), fill=RED, anchor='mm')
    d.text((W / 2, 1375), '水墨是现在  水彩是回忆  油画棒是“也许”', font=ImageFont.truetype(SUB_FONT, 36),
           fill=(110, 100, 96), anchor='mm')
    im.save(out)
    return out


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(core.ROOT, 'out')
    os.makedirs(out_dir, exist_ok=True)
    hero = render_scene(*HERO[:4])
    thumbs = [(render_scene(n, k, t, kw), lab) for n, k, t, kw, lab in THUMBS]
    print(cover_4x3(hero, os.path.join(out_dir, 'cover_4x3.png')))
    print(cover_3x4(hero, thumbs, os.path.join(out_dir, 'cover_3x4.png')))
