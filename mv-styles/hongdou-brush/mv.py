# -*- coding: utf-8 -*-
"""
成片合成与渲染（第二段主歌 + 副歌，成片 79.65 秒）。

  python mv.py shots                      打印分镜时间表
  python mv.py frame <成片秒> out.png      单帧
  python mv.py sheet out.png [t …]        抽帧拼图（不给时间就每个镜头取一帧）
  python mv.py clip <t0> <t1> out.mp4      带原曲音频的片段（测试转场用）
  python mv.py render [--out f.mp4] [--workers 12]

每一帧：按 core.TIMELINE 决定风格 → 纯风格就用那支笔刷画；转场就用两支笔刷各画一遍（场景按 pen.style 可以画不同内容），
各自过同一个镜头、画上歌词，再用 trans 里的遮罩混合。画面一拍二：同一个绘制序号只渲染一次。
"""
import importlib
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'scenes')]

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import core
import trans
from core import W, H, FPS, CUT_LEN, CUT_START, draw_index, draw_time, style_at, clamp, ease_io
from shots import SHOTS, TRANS_SCENE, BLOOM_CENTER

OUT_DIR = os.path.join(core.ROOT, 'out')

# ---------------------------------------------------------------- 笔刷与场景（按需加载）
_BRUSH = {}
_SCENE = {}


def brush(key):
    if key not in _BRUSH:
        if key == 'F':
            _BRUSH[key] = core.FlatBrush()
        else:
            mod = importlib.import_module('brush_' + key.lower())
            _BRUSH[key] = getattr(mod, 'Brush' + key.upper())()
    return _BRUSH[key]


def scene(name):
    if name not in _SCENE:
        try:
            _SCENE[name] = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
            _SCENE[name] = None
    return _SCENE[name]


def shot_index(ct):
    i = 0
    while i + 1 < len(SHOTS) and SHOTS[i + 1]['t0'] <= ct + 1e-9:
        i += 1
    return i


def shot_span(i):
    t1 = SHOTS[i + 1]['t0'] if i + 1 < len(SHOTS) else CUT_LEN
    return SHOTS[i]['t0'], t1


# ---------------------------------------------------------------- 占位卡（场景还没写好时）
_FONT = None


def placeholder(name, note, style, lt):
    global _FONT
    if _FONT is None:
        _FONT = ImageFont.truetype(core.FONT_LABEL, 54)
    bg = {'A': (238, 228, 210), 'B': (52, 58, 88), 'C': (232, 229, 222)}.get(style, (220, 220, 220))
    fg = (60, 50, 50) if style != 'B' else (240, 230, 210)
    im = Image.new('RGB', (W, H), bg)
    dr = ImageDraw.Draw(im)
    dr.text((W / 2, H / 2 - 80), f'【{style}】{note}', font=_FONT, fill=fg, anchor='mm')
    dr.text((W / 2, H / 2), f'场景 {name} 尚未完成 · 镜头内 {lt:.2f}s', font=_FONT, fill=fg, anchor='mm')
    return np.asarray(im, np.float32) / 255.0


# ---------------------------------------------------------------- 单风格画面
def render_style(style, shot, d, lt, dur, scene_override=None):
    name = shot['scene'] if scene_override is None else scene_override['scene']
    kw = dict(shot.get('kw', {}) if scene_override is None else scene_override.get('kw', {}))
    mod = scene(name)
    if mod is None:
        img = placeholder(name, shot.get('note', ''), style, lt)
    else:
        pen = core.Pen(style, d)
        pen.lt, pen.dur = lt, dur
        mod.draw(pen, **kw)
        img = brush(style).render(pen.ops, d)
    cam = shot.get('cam')
    if cam:
        u = ease_io(lt / max(dur, 1e-3))
        img = core.camera(img, cam['z0'] + (cam['z1'] - cam['z0']) * u, cam.get('cx', W / 2), cam.get('cy', H / 2))
    if style in ('A', 'B', 'C') and _has_brush(style):
        img = brush(style).paint_text(img, core.lyric_items(d, style), d)
    else:
        img = core.FlatBrush().paint_text(img, core.lyric_items(d, style), d)
    return img


def _has_brush(style):
    try:
        brush(style)
        return True
    except ModuleNotFoundError:
        return False


def _regions_for(i):
    """T3 的 8 块：由“新风格一侧”的场景模块提供 patch_regions() → (多边形列表的列表, 角度列表)。"""
    ov = TRANS_SCENE.get('patches')
    mod = scene(ov['scene']) if ov else None
    if mod is not None and hasattr(mod, 'patch_regions'):
        polys, angles = mod.patch_regions(**ov.get('kw', {}))
        return [trans.region_from_polys(p) for p in polys], angles
    # 兜底：横向 8 条
    return [trans.region_from_polys([core.rect(0, H * k / 8, W, H * (k + 1) / 8)]) for k in range(8)], None


_REG = None


def compose_d(d):
    """绘制序号 → 一帧 float RGB。"""
    global _REG
    td = draw_time(d)
    seg, p = style_at(td)
    i = shot_index(td)
    shot = SHOTS[i]
    s0, s1 = shot_span(i)
    lt, dur = td - s0, s1 - s0
    if seg['kind'] == 'style':
        out = render_style(seg['style'], shot, d, lt, dur)
    else:
        a, b, kind = seg['a'], seg['b'], seg['mask']
        ia = render_style(a, shot, d, lt, dur)
        ib = render_style(b, shot, d, lt, dur, scene_override=TRANS_SCENE.get(kind))
        if kind == 'bloom':
            mod = scene(shot['scene'])
            m, edge = trans.bloom(p, getattr(mod, 'BLOOM_CENTER', BLOOM_CENTER))
        elif kind == 'drain':
            m, edge = trans.drain(p)
        elif kind == 'patches':
            if _REG is None:
                _REG = _regions_for(i)
            beats = (td - seg['t0']) / core.BEAT
            m, edge = trans.patches(beats, _REG[0], angles=_REG[1])
        else:
            m, edge = trans.rinse(p)
        m3 = m[..., None]
        out = ia * (1 - m3) + ib * m3
        if edge is not None:
            # 新材质的前沿：水彩前沿颜料堆积 / 油画棒笔触末端 / 冲刷的水痕，都表现为轻微加深
            out *= 1 - 0.18 * edge[..., None] * m3
    # 片头：右上角一方小朱印“红豆演唱者”（两列，从右往左读），前 4.5 秒淡入淡出
    if td < 4.5 and _has_brush('C'):
        a = clamp(td / 0.4) * clamp((4.5 - td) / 0.9)
        importlib.import_module('brush_c').seal(out, 1758, 54, w=104, h=104, text='红豆演唱者', alpha=a)
    # 片尾淡黑
    f0, f1 = core.PIC_FADE
    if td > f0:
        out = out * (1 - clamp((td - f0) / (f1 - f0)))
    return out


# ---------------------------------------------------------------- 输出
def _ff_writer(path, fps=FPS):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '2',
           '-g', '48', path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _chunk(args):
    """渲染一段绘制序号 [d0, d1)，每张画写两帧（一拍二）。"""
    d0, d1, path = args
    pr = _ff_writer(path)
    for d in range(d0, d1):
        fr = core.to_u8(compose_d(d)).tobytes()
        pr.stdin.write(fr)
        pr.stdin.write(fr)
    pr.stdin.close()
    pr.wait()
    return path


def render_range(t0, t1, out, workers=12, audio=True):
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    tmp = os.path.join(HERE, '_chunks')
    os.makedirs(tmp, exist_ok=True)
    d0, d1 = draw_index(t0), int(math.ceil(t1 * core.DRAW_RATE - 1e-6))
    n = max(1, min(workers * 3, (d1 - d0) // 12))
    edges = [d0 + (d1 - d0) * k // n for k in range(n + 1)]
    jobs = [(edges[k], edges[k + 1], os.path.join(tmp, f'c{k:03d}.mp4')) for k in range(n)]
    t_start = time.time()
    with Pool(workers) as pool:
        for k, _ in enumerate(pool.imap(_chunk, jobs)):
            print(f'chunk {k + 1}/{n}  {time.time() - t_start:.0f}s', flush=True)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as fh:
        for _, _, pth in jobs:
            fh.write(f"file '{pth}'\n")
    vt0 = d0 / core.DRAW_RATE
    dur = d1 / core.DRAW_RATE - vt0
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst]
    if audio and os.path.exists(core.SONG):   # 没有歌曲音频时只出无声画面
        a0 = CUT_START + vt0
        af = 'afade=t=in:d=0.03'
        fo, fd = core.AUDIO_FADE
        if vt0 + dur > fo:
            af += f',afade=t=out:st={fo - vt0:.3f}:d={fd:.3f}'
        cmd += ['-ss', f'{a0:.3f}', '-t', f'{dur:.3f}', '-i', core.SONG, '-map', '0:v', '-map', '1:a', '-af', af,
                '-c:a', 'aac', '-b:a', '256k', '-shortest']
    cmd += ['-c:v', 'copy', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('OUT', out, f'{time.time() - t_start:.0f}s')


def sheet(times, path, cols=4, w=480):
    h = w * 9 // 16
    rows = (len(times) + cols - 1) // cols
    S = Image.new('RGB', (cols * w, rows * h))
    dr = ImageDraw.Draw(S)
    for k, t in enumerate(times):
        d = draw_index(t)
        im = Image.fromarray(core.to_u8(compose_d(d))).resize((w, h), Image.LANCZOS)
        S.paste(im, ((k % cols) * w, (k // cols) * h))
        dr.text(((k % cols) * w + 6, (k // cols) * h + 4), f'{t:.2f} {SHOTS[shot_index(t)]["scene"]}',
                fill=(255, 40, 40))
    S.save(path)
    print('SHEET', path)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'shots'
    if cmd == 'shots':
        for k, s in enumerate(SHOTS):
            a, b = shot_span(k)
            seg, _ = style_at(a + 0.01)
            print(f'{k:2d} {a:6.2f}–{b:6.2f} {b - a:5.2f}s  {s["scene"]:13s} {seg.get("style", seg.get("a", ""))}  '
                  f'{s.get("note", "")}  {"" if scene(s["scene"]) else "(占位)"}')
    elif cmd == 'frame':
        t = float(sys.argv[2])
        Image.fromarray(core.to_u8(compose_d(draw_index(t)))).save(sys.argv[3])
        print(sys.argv[3])
    elif cmd == 'sheet':
        out = sys.argv[2]
        ts = [float(x) for x in sys.argv[3:]]
        if not ts:
            ts = [shot_span(k)[0] + min(1.5, (shot_span(k)[1] - shot_span(k)[0]) * 0.6) for k in range(len(SHOTS))]
        sheet(ts, out)
    elif cmd == 'clip':
        render_range(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4],
                     workers=int(sys.argv[5]) if len(sys.argv) > 5 else 8)
    elif cmd == 'render':
        a = sys.argv[2:]
        kw = {a[j].lstrip('-'): a[j + 1] for j in range(0, len(a), 2)}
        render_range(0.0, CUT_LEN, kw.get('out', os.path.join(OUT_DIR, '红豆_手绘_第二段.mp4')),
                     int(kw.get('workers', 12)))
