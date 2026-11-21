# 音效轨：读 events.json（画面里 ev() 登记的事件），合成手绘片的纸笔音效；不加 BGM（用户自己配），不配音
# 用法：python mix.py  →  out/sfx.wav
import json, os, sys
import numpy as np
from scipy.signal import lfilter, butter, fftconvolve
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
EVF = json.load(open(os.path.join(HERE, 'events.json'), encoding='utf-8'))
SR = 48000
DUR = EVF['dur'] + 1.5
N = int(SR * DUR)
DRY = np.zeros((2, N)); WET = np.zeros((2, N))
rng = np.random.default_rng(21)

def tt(d): return np.arange(int(d * SR)) / SR
def mx(*xs):
    o = np.zeros(max(len(x) for x in xs))
    for x in xs: o[:len(x)] += x
    return o
def lp(x, fc, o=2): b, a = butter(o, min(fc / (SR / 2), 0.99)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), min(hi / (SR / 2), 0.99)], 'band'); return lfilter(b, a, x)
def ph(f): return 2 * np.pi * np.cumsum(f) / SR
def att(t, a=0.004): return np.minimum(1, t / a)

def add(sig, at, gain=1.0, pan=0.0, wet=0.35):
    i = int(at * SR)
    if i >= N or i < 0: return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
    DRY[0, i:i + len(sig)] += sig * l * (1 - wet * 0.5); DRY[1, i:i + len(sig)] += sig * r * (1 - wet * 0.5)
    WET[0, i:i + len(sig)] += sig * l * wet; WET[1, i:i + len(sig)] += sig * r * wet

# ---------------- 音色 ----------------
def whoosh(d=1.1, up=True):
    t = tt(d); x = rng.standard_normal(len(t)); out = np.zeros(len(t)); blk = 1024
    for i in range(0, len(t), blk):
        p = i / len(t); fc = 300 + 2600 * (p if up else 1 - p) ** 1.3
        out[i:i + blk] = bp(x[max(0, i - 4096):i + blk], fc * 0.6, fc * 1.5)[-len(x[i:i + blk]):]
    return out * np.sin(np.pi * t / d) ** 2 * 0.9

def bell(f, d=2.2, bright=1.0):
    t = tt(d)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.35 * bright * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 4)
         + 0.18 * bright * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 7) + 0.08 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 11))
    return s * att(t, 0.003)

def shimmer(f=1800):
    out = np.zeros(int(1.6 * SR))
    for k in range(9):
        b = bell(f * (1 + 0.5 * rng.random()), 1.0, 0.4) * 0.12 * (1 - k / 12); i = int(k * 0.05 * SR)
        out[i:i + len(b)] += b[: len(out) - i]
    t = tt(1.6); air = hp(rng.standard_normal(len(t)), 6000) * np.sin(np.pi * np.minimum(1, t / 1.2)) ** 2 * np.exp(-t * 1.5) * 0.05
    return mx(out, air)

def tick(f=1200):
    t = tt(0.09); return (np.sin(2 * np.pi * f * t) * 0.6 + 0.4 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t * 60) * att(t, 0.0008) * 0.6

def roll(d=1.4):
    out = np.zeros(int((d + 0.2) * SR)); k = 0; tpos = 0.0
    while tpos < d:
        p = tpos / d; i = int(tpos * SR); c = tick(2200 + 600 * np.sin(k)) * 0.35 * (0.6 + 0.4 * np.sin(np.pi * p))
        out[i:i + len(c)] += c[: len(out) - i]; tpos += 0.025 + 0.06 * p ** 2; k += 1
    return out

def settle(f=880):
    t = tt(0.5); return mx(bell(f, 0.5, 0.6) * 0.5, lp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 60) * 0.3)

def boom():
    t = tt(3.0)
    sub = np.sin(ph(38 + 50 * np.exp(-t * 6))) * np.exp(-t * 1.6)
    body = lp(rng.standard_normal(len(t)), 220) * np.exp(-t * 3) * 0.6
    return np.tanh((sub + body) * 1.4) * att(t, 0.01)

def chime(f=1320):
    return mx(bell(f, 2.5, 0.8) * 0.5, bell(f * 1.5, 2.0, 0.5) * 0.25)

def drop(f=900):
    t = tt(0.14); return np.sin(ph(f * (1 + 0.6 * np.exp(-t * 50)))) * np.exp(-t * 30) * att(t, 0.001) * 0.5

def sweep(d=1.2):
    t = tt(d); x = hp(rng.standard_normal(len(t)), 3000)
    return mx(x * np.sin(np.pi * t / d) ** 3 * 0.18, bell(2640, d, 0.3) * 0.08)

def dim():
    t = tt(1.8)
    tone = np.sin(ph(220 * np.exp(-t * 0.8) + 60)) * np.exp(-t * 1.8) * 0.5
    return lp(tone + lp(rng.standard_normal(len(t)), 400) * np.exp(-t * 3) * 0.2, 1200) * att(t, 0.02)

def heart():
    # 两下心跳：低频正弦打底，再加一层 150–900 Hz 的闷响和谐波，手机喇叭也听得见
    out = np.zeros(int(1.0 * SR))
    for off, g in ((0, 1), (0.22, 0.7)):
        t = tt(0.3); s = np.sin(ph(55 + 30 * np.exp(-t * 20))) * np.exp(-t * 14) * g
        s = np.tanh(s * 2.5) / np.tanh(2.5)                                       # 谐波
        knock = bp(rng.standard_normal(len(t)), 150, 900) * np.exp(-t * 60) * 0.45 * g
        s = s * 0.85 + knock; i = int(off * SR)
        out[i:i + len(s)] += s[: len(out) - i]
    return out * 0.9

def shot():
    # 远处的一声枪响：很短的噪声爆点 + 低频回声拖尾（远距离，高频被吃掉）
    t = tt(2.4)
    crack = bp(rng.standard_normal(len(t)), 500, 5000) * np.exp(-t * 25) * 1.3
    slap = np.zeros(len(t)); j = int(0.075 * SR); slap[j:] = crack[: len(t) - j] * 0.45   # 远处墙面的一下回声
    crack = crack + slap
    thump = np.sin(ph(70 + 60 * np.exp(-t * 30))) * np.exp(-t * 9) * 0.8
    tail = lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 2.2) * 0.25 * np.minimum(1, t / 0.05)
    return np.tanh((crack + thump + tail) * 1.3) * att(t, 0.001)

def hold(d=3.0):
    # 定格时的长音：很轻的低频持续音 + 高频空气声，0.5 秒淡入、最后 0.4 秒淡出，片尾不会变成死寂
    t = tt(d)
    drone = (np.sin(2 * np.pi * 73.4 * t) + 0.5 * np.sin(2 * np.pi * 110 * t) + 0.25 * np.sin(2 * np.pi * 146.8 * t * (1 + 0.002 * np.sin(2 * np.pi * 0.3 * t)))) * 0.25
    air = hp(rng.standard_normal(len(t)), 5000) * 0.03
    env_ = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.4).clip(0, 1)
    return (lp(drone, 900) + air) * env_


# ---------------- 第一集新加的音色 ----------------
def notify():
    # 手机提示音：两声短促的上行“叮”（开头、结尾同一声，循环时接得上）
    return mx(bell(1568, 0.6, 0.5) * 0.5, np.concatenate([np.zeros(int(0.11 * SR)), bell(2093, 0.7, 0.5) * 0.45]))

def boing(f=1.0):
    # 叶子“嘣”地弹起来：弹簧声，音高快速上扬再抖几下
    t = tt(0.55); fr = (180 + 520 * (1 - np.exp(-t * 18))) * f * (1 + 0.08 * np.sin(2 * np.pi * 22 * t) * np.exp(-t * 6))
    return np.sin(ph(fr)) * np.exp(-t * 6) * att(t, 0.003) * 0.7

def deflate():
    # 泄气：音高往下滑的气声
    t = tt(0.9); fr = 520 * np.exp(-t * 2.2) + 90
    tone = np.sin(ph(fr)) * 0.35 + bp(rng.standard_normal(len(t)), 300, 2000) * 0.25
    return lp(tone, 2500) * np.sin(np.pi * np.minimum(1, t / 0.9)) ** 1.5

def sob():
    # 抽泣：三下短促的下行小音
    out = np.zeros(int(1.2 * SR))
    for k, (off, f) in enumerate(((0, 660), (0.28, 620), (0.5, 560))):
        t = tt(0.22); s = np.sin(ph(f * np.exp(-t * 3))) * np.exp(-t * 14) * (0.5 - 0.1 * k)
        i = int(off * SR); out[i:i + len(s)] += s[: len(out) - i]
    return out

def rewind(d=0.8):
    # 倒带：磁带高速倒转的“叽——”，带一点颤
    t = tt(d); fr = 900 + 1800 * (t / d) + 120 * np.sin(2 * np.pi * 31 * t)
    s = np.sin(ph(fr)) * 0.25 + bp(rng.standard_normal(len(t)), 1500, 6000) * 0.2
    return s * np.sin(np.pi * t / d) ** 0.7

def steps(d=2.0):
    # 一群小脚步：密集的轻“哒哒”声
    out = np.zeros(int((d + 0.2) * SR)); r = np.random.default_rng(int(d * 100))
    for _ in range(int(d * 26)):
        tp = r.random() * d; c = tick(500 + r.random() * 500) * (0.25 + 0.25 * r.random()) * np.sin(np.pi * tp / d)
        i = int(tp * SR); out[i:i + len(c)] += c[: len(out) - i]
    return lp(out, 3500)

def press():
    # 按下按钮：咔哒 + 低一点的回弹
    return mx(tick(1100) * 1.2, np.concatenate([np.zeros(int(0.05 * SR)), drop(400) * 1.2]))

def swell(d=2.0):
    # 慢慢升起来的低频暖音（大手出现）
    t = tt(d); s = (np.sin(2 * np.pi * 98 * t) + 0.5 * np.sin(2 * np.pi * 147 * t) + 0.3 * np.sin(2 * np.pi * 196 * t)) * 0.3
    return lp(s, 1200) * np.sin(np.pi * np.minimum(1, t / d) * 0.5) ** 2 * np.minimum(1, (d - t) / 0.3 + 0.0).clip(0, 1)

def glide(d=1.6, up=True):
    # 走势往上拉 / 往下砸：滑音 + 气声
    t = tt(d); p = t / d; fr = 220 * 2 ** ((2.2 * p) if up else (-1.6 * p) + 1.2)
    s = np.sin(ph(fr)) * 0.3 + bp(rng.standard_normal(len(t)), 400, 3000) * 0.08
    return s * np.sin(np.pi * p) ** 1.2

def coin(f=2000):
    t = tt(0.35)
    return (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 1.5 * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 16) * att(t, 0.001) * 0.4

def leaf():
    # 叶子飘落：很轻的沙沙声 + 落地一声小“嗒”
    t = tt(1.8); rustle = bp(rng.standard_normal(len(t)), 2000, 7000) * 0.07 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) * np.exp(-t * 1.2)
    tap = np.zeros(len(t)); c = tick(700) * 0.8; i = int(1.75 * SR) - len(c); tap[i:i + len(c)] += c
    return rustle + tap


# ---------------- 第二集新加 ----------------
def snore(d=2.4):
    # 两声慢呼噜：低频噪声按呼吸起伏
    t = tt(d); env_ = np.maximum(0, np.sin(2 * np.pi * t / (d / 2))) ** 2
    x = lp(rng.standard_normal(len(t)), 260) * (1 + 0.6 * np.sin(2 * np.pi * 34 * t))
    return x * env_ * 0.5

def buzz(d=0.9):
    # 手机震动：两下 170Hz 方波嗡嗡
    t = tt(d); g = ((t % 0.42) < 0.3).astype(float) * np.exp(-0 * t)
    x = np.sign(np.sin(2 * np.pi * 170 * t)) * 0.25 + np.sin(2 * np.pi * 340 * t) * 0.15
    return lp(x, 1800) * g * att(t, 0.01)

def wind(d=2.5):
    t = tt(d); x = rng.standard_normal(len(t)); out = np.zeros(len(t)); blk = 1024
    for i in range(0, len(t), blk):
        p = i / len(t); fc = 500 + 700 * np.sin(np.pi * p) + 200 * np.sin(2 * np.pi * 3 * p)
        out[i:i + blk] = bp(x[max(0, i - 4096):i + blk], fc * 0.5, fc * 1.6)[-len(x[i:i + blk]):]
    return out * np.sin(np.pi * t / d) ** 1.5 * 0.9

def pop(f=1.0):
    t = tt(0.12); return np.sin(ph(900 * f * (1 + 1.2 * np.exp(-t * 60)))) * np.exp(-t * 40) * att(t, 0.001) * 0.5

def clack(d=2.0):
    # 过山车爬坡：越来越慢的咔哒声
    out = np.zeros(int((d + 0.2) * SR)); tpos = 0.0; k = 0
    while tpos < d:
        i = int(tpos * SR); c = mx(tick(520 + 40 * (k % 2)) * 0.9, lp(rng.standard_normal(int(0.03 * SR)), 900) * 0.2)
        out[i:i + len(c)] += c[: len(out) - i]; tpos += 0.11 + 0.08 * (tpos / d); k += 1
    return out

def clank():
    # 天平重重砸下：低沉金属
    t = tt(1.4); return mx(bell(220, 1.4, 1.2) * 0.6, bell(330, 1.0, 0.8) * 0.3, lp(rng.standard_normal(len(t)), 400) * np.exp(-t * 18) * 0.6)

def plink():
    return bell(1760, 0.8, 0.5) * 0.4

def stamp(f=1.0):
    # 脚印：软软的“噗”
    t = tt(0.18); return mx(np.sin(ph(160 * f + 120 * np.exp(-t * 40))) * np.exp(-t * 25) * 0.7, lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 50) * 0.25) * att(t, 0.002)

def pour(d=1.2):
    # 倒茶：细水流的嘶嘶声 + 越来越高的水声
    t = tt(d); x = bp(rng.standard_normal(len(t)), 1500, 5000) * 0.18
    gl = np.sin(ph(500 + 500 * t / d)) * 0.08 * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t))
    return (x + gl) * np.sin(np.pi * t / d) ** 0.6

def flip():
    # 翻卡片：纸张“唰”一下 + 轻轻落定
    t = tt(0.3); x = bp(rng.standard_normal(len(t)), 1800, 6000) * np.exp(-t * 18) * 0.5
    return mx(x, tick(900) * 0.4)

# ---------------- 手绘科普片新加 ----------------
def scribble(d=1.0):
    # 铅笔在纸上写画：一下一下的沙沙声
    t = tt(d); x = bp(rng.standard_normal(len(t)), 1800, 7000)
    am = 0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 7.5 * t + 0.6 * np.sin(2 * np.pi * 1.3 * t)))
    return x * am * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05).clip(0, 1) * 0.3

def crayon(d=2.0):
    # 蜡笔来回涂：比铅笔低、粗
    t = tt(d); x = bp(rng.standard_normal(len(t)), 600, 3200)
    am = 0.25 + 0.75 * np.abs(np.sin(2 * np.pi * 4.2 * t))
    return x * am * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.1).clip(0, 1) * 0.35

def rub(d=0.6):
    # 橡皮擦
    t = tt(d); x = bp(rng.standard_normal(len(t)), 400, 2200)
    return x * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 6 * t))) * np.sin(np.pi * t / d) ** 0.6 * 0.4

def squeak(d=0.5, f=1.0):
    # 马克笔 / 荧光笔划过去的“吱”
    t = tt(d); fr = (1500 + 500 * np.sin(np.pi * t / d)) * f * (1 + 0.02 * np.sin(2 * np.pi * 37 * t))
    s = np.sin(ph(fr)) * 0.10 + bp(rng.standard_normal(len(t)), 2500, 8000) * 0.22
    return s * np.sin(np.pi * t / d) ** 0.8

def tear(d=0.7):
    # 撕纸：一串密集的小爆点 + 高频嘶声
    t = tt(d); x = hp(rng.standard_normal(len(t)), 1200)
    cr = (rng.random(len(t)) > 0.985).astype(float); cr = lfilter([1], [1, -0.995], cr); cr = cr / (cr.max() + 1e-9)
    return x * (0.25 + 0.9 * cr) * np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.08).clip(0, 1) * 0.5

def honk(f=1.0):
    # 卡通喇叭：两个音叠在一起的“叭”
    t = tt(0.32); s = np.sign(np.sin(2 * np.pi * 370 * f * t)) * 0.5 + np.sign(np.sin(2 * np.pi * 466 * f * t)) * 0.5
    return lp(s, 2600) * att(t, 0.01) * np.minimum(1, (0.32 - t) / 0.04).clip(0, 1) * 0.35

def squeal():
    # 急刹车：轮胎尖叫，音高慢慢往下掉
    t = tt(0.7); fr = (1900 - 500 * t / 0.7) * (1 + 0.015 * np.sin(2 * np.pi * 45 * t))
    s = np.sin(ph(fr)) * 0.25 + np.sin(ph(fr * 1.5)) * 0.1 + bp(rng.standard_normal(len(t)), 1500, 4000) * 0.15
    return s * att(t, 0.01) * np.exp(-t * 2.5)

def rev(d=1.2, sweep=0):
    # 发动机：锯齿波低音往上拉；sweep=1 时是一辆车开过去（音高先升后降）
    t = tt(d); p = t / d
    fr = (70 + 110 * np.sin(np.pi * p)) * (1.25 if sweep else 1.0) if sweep else 60 + 120 * p ** 0.7
    saw = 2 * ((np.cumsum(fr) / SR) % 1) - 1
    s = lp(saw, 900) * 0.5 + lp(rng.standard_normal(len(t)), 300) * 0.25
    s = s * (1 + 0.3 * np.sin(2 * np.pi * 27 * t))
    return np.tanh(s * 1.6) * np.sin(np.pi * p) ** (1.0 if sweep else 0.5) * 0.6

def creak():
    # 开门：吱呀一声 + 轻轻一磕
    t = tt(0.4); fr = 420 + 380 * t / 0.4 + 30 * np.sin(2 * np.pi * 50 * t)
    s = np.sign(np.sin(ph(fr))) * 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * 60 * t))
    return mx(bp(s, 300, 3000) * np.sin(np.pi * t / 0.4), np.concatenate([np.zeros(int(0.3 * SR)), stamp(1.2) * 0.6]))

def bonk():
    # 撞上去：空心木头“咚”
    t = tt(0.3); s = np.sin(ph(210 + 260 * np.exp(-t * 35))) * np.exp(-t * 16) + bp(rng.standard_normal(len(t)), 300, 1800) * np.exp(-t * 45) * 0.5
    return np.tanh(s * 1.5) * att(t, 0.002) * 0.8

def stretch(d=0.6):
    # 拉橡皮筋：音高往上的颤音
    t = tt(d); fr = (240 + 320 * (t / d) ** 1.5) * (1 + 0.04 * np.sin(2 * np.pi * 19 * t))
    return (np.sin(ph(fr)) * 0.35 + np.sin(ph(fr * 2)) * 0.12) * np.sin(np.pi * t / d) ** 0.7


# ---------------- 舞台片新加 ----------------
def clunk():
    # 追光灯开关：低沉的“咚” + 金属咔哒 + 一点电流嗡
    t = tt(0.9)
    thump = np.sin(ph(70 + 60 * np.exp(-t * 30))) * np.exp(-t * 12) * 0.9
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 140) * 0.55
    ring = np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 28) * 0.12 + np.sin(2 * np.pi * 2480 * t) * np.exp(-t * 40) * 0.06
    hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t)) * 0.05 * np.exp(-t * 3) * np.minimum(1, t / 0.05)
    return mx(thump, click, ring, hum) * att(t, 0.001)

def murmur(d=4.0):
    # 人群窃窃私语：几路带通噪声，各自慢慢起伏
    t = tt(d); out = np.zeros(len(t))
    for k in range(5):
        lo = 250 + 120 * k; x = bp(rng.standard_normal(len(t)), lo, lo * 2.4)
        env_ = np.clip(np.sin(2 * np.pi * (0.6 + 0.37 * k) * t + k * 1.3) * 0.5 + 0.5, 0, 1) ** 3
        out += x * env_
    return out * 0.32 * np.sin(np.pi * np.minimum(1, t / d)) ** 0.5 * np.minimum(1, t / 0.4)

def crickets(d=2.0):
    # 蟋蟀：没人搭理你的那种安静
    t = tt(d); car = np.sin(2 * np.pi * 4400 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t))
    ph_ = t % 0.75; gate = ((ph_ < 0.2) & ((ph_ % 0.05) < 0.022)).astype(float)
    gate = lp(gate, 400)
    return car * gate * 0.22 * np.sin(np.pi * t / d) ** 0.4

def curtain(d=0.9):
    # 大幕拉动：布料的唰唰声 + 低低的轨道声
    t = tt(d); x = bp(rng.standard_normal(len(t)), 400, 3200) * (0.7 + 0.3 * np.sin(2 * np.pi * 13 * t))
    rum = lp(rng.standard_normal(len(t)), 120) * 0.5
    return mx(x * 0.5, rum) * np.sin(np.pi * t / d) ** 1.2

SOUNDS = {
    'shot': lambda e: (shot(), 0.9, 0.65),
    'hold': lambda e: (hold(e.get('d', 3.0)), 0.5, 0.6),
    'whoosh': lambda e: (whoosh(e.get('d', 1.1), e.get('up', True)), 0.45, 0.4),
    'shimmer': lambda e: (shimmer(e.get('f', 1800)), 0.55, 0.6),
    'tick': lambda e: (tick(e.get('f', 1200)), 0.4, 0.3),
    'roll': lambda e: (roll(e.get('d', 1.4)), 0.4, 0.25),
    'settle': lambda e: (settle(e.get('f', 880)), 0.4, 0.45),
    'boom': lambda e: (boom(), 0.55, 0.5),
    'chime': lambda e: (chime(e.get('f', 1320)), 0.4, 0.6),
    'drop': lambda e: (drop(e.get('f', 900)), 0.22, 0.35),
    'sweep': lambda e: (sweep(e.get('d', 1.2)), 0.45, 0.5),
    'dim': lambda e: (dim(), 0.5, 0.5),
    'heart': lambda e: (heart(), 0.6, 0.3),
    'notify': lambda e: (notify(), 0.6, 0.35),
    'boing': lambda e: (boing(e.get('f', 1.0)), 0.55, 0.3),
    'deflate': lambda e: (deflate(), 0.5, 0.35),
    'sob': lambda e: (sob(), 0.45, 0.4),
    'rewind': lambda e: (rewind(e.get('d', 0.8)), 0.5, 0.3),
    'steps': lambda e: (steps(e.get('d', 2.0)), 0.5, 0.25),
    'press': lambda e: (press(), 0.6, 0.3),
    'swell': lambda e: (swell(e.get('d', 2.0)), 0.55, 0.5),
    'rise': lambda e: (glide(e.get('d', 1.6), True), 0.5, 0.4),
    'fall': lambda e: (glide(e.get('d', 1.6), False), 0.5, 0.4),
    'coin': lambda e: (coin(e.get('f', 2000)), 0.35, 0.4),
    'leaf': lambda e: (leaf(), 0.6, 0.4),
    'snore': lambda e: (snore(e.get('d', 2.4)), 0.5, 0.3),
    'buzz': lambda e: (buzz(e.get('d', 0.9)), 0.55, 0.2),
    'wind': lambda e: (wind(e.get('d', 2.5)), 0.5, 0.45),
    'pop': lambda e: (pop(e.get('f', 1.0)), 0.35, 0.3),
    'clack': lambda e: (clack(e.get('d', 2.0)), 0.5, 0.3),
    'clank': lambda e: (clank(), 0.6, 0.5),
    'plink': lambda e: (plink(), 0.45, 0.5),
    'stamp': lambda e: (stamp(e.get('f', 1.0)), 0.5, 0.3),
    'pour': lambda e: (pour(e.get('d', 1.2)), 0.5, 0.35),
    'flip': lambda e: (flip(), 0.5, 0.3),
    'scribble': lambda e: (scribble(e.get('d', 1.0)), 0.55, 0.15),
    'crayon': lambda e: (crayon(e.get('d', 2.0)), 0.55, 0.15),
    'rub': lambda e: (rub(e.get('d', 0.6)), 0.55, 0.15),
    'squeak': lambda e: (squeak(e.get('d', 0.5), e.get('f', 1.0)), 0.45, 0.2),
    'tear': lambda e: (tear(e.get('d', 0.7)), 0.7, 0.2),
    'honk': lambda e: (honk(e.get('f', 1.0)), 0.5, 0.25),
    'squeal': lambda e: (squeal(), 0.45, 0.3),
    'rev': lambda e: (rev(e.get('d', 1.2), e.get('sweep', 0)), 0.5, 0.2),
    'creak': lambda e: (creak(), 0.6, 0.25),
    'bonk': lambda e: (bonk(), 0.7, 0.3),
    'stretch': lambda e: (stretch(e.get('d', 0.6)), 0.4, 0.2),
    'clunk': lambda e: (clunk(), 0.75, 0.45),
    'murmur': lambda e: (murmur(e.get('d', 4.0)), 0.5, 0.5),
    'crickets': lambda e: (crickets(e.get('d', 2.0)), 0.5, 0.5),
    'curtain': lambda e: (curtain(e.get('d', 0.9)), 0.6, 0.35),
}

exec(open(os.path.join(HERE, 'tools', 'sfx_stage.py'), encoding='utf-8').read())
SOUNDS.update(SOUNDS2)
unknown = set()
for e in EVF['ev']:
    if e['s'] == 'cue': continue
    fn = SOUNDS.get(e['s'])
    if not fn: unknown.add(e['s']); continue
    sig, g, wet = fn(e)
    v = e.get('vary', 0.0 if e['s'] in NOVARY else 0.05)
    if v > 0:   # 每次触发都略微变一下音高，同一种声音不会一模一样
        r = 1 + (rng.random() * 2 - 1) * v
        sig = np.interp(np.arange(0, len(sig) - 1, r), np.arange(len(sig)), sig)
    add(sig, e['t'], g * e.get('g', 1.0), e.get('pan', 0.0), wet)
if unknown: print('未映射的事件:', unknown)

# 很轻的空气底噪，让静场不“死”（−45 dB 左右，不是音乐）
t = np.arange(N) / SR
air = lp(rng.standard_normal(N), 900) * 0.06 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 17))
DRY += air

# 混响：指数衰减的噪声脉冲
ir_t = tt(2.6); ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t * 2.4)
ir = np.stack([lp(ir[0], 5000), lp(ir[1], 5000)]) * 0.06
mix = DRY + np.stack([fftconvolve(WET[c], ir[c])[:N] for c in range(2)])
pk = np.abs(mix).max()
mix = np.tanh(mix / pk * 1.1) / np.tanh(1.1) * 10 ** (-3 / 20)
# 按响度对齐到约 -16.5 LUFS（用 ffmpeg 的 ebur128 量），再用软限幅把峰值压在 -1.2 dBFS 以下
import subprocess, tempfile, re
def lufs_of(x):
    f = os.path.join(tempfile.gettempdir(), 'ai_pause_lufs.wav'); sf.write(f, x.T.astype(np.float32), SR)
    o = subprocess.run(['ffmpeg', '-v', 'info', '-nostats', '-i', f, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore').stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
ceil = 10 ** (-1.2 / 20)
def soft(x): k = ceil * 0.8; a = np.abs(x); return np.where(a > k, np.sign(x) * (k + (ceil - k) * np.tanh((a - k) / (ceil - k))), x)
for _ in range(2):   # 限幅会吃掉一点响度，量两次
    l0 = lufs_of(mix); mix = soft(mix * 10 ** ((-16.5 - l0) / 20))
print('loudness', round(l0, 1), '->', round(lufs_of(mix), 1), 'LUFS')
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out', 'sfx.wav')
sf.write(out, mix.T.astype(np.float32), SR, subtype='PCM_24')
print('ok', out, f'{DUR:.1f}s', 'events', len(EVF['ev']))
