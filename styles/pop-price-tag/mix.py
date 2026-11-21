# 音效轨：读 events.json（画面里 ev() 登记的事件），合成夜市 / 脑子里 / 转盘节目 / 办公室四个场景的音效；不配音、不加 BGM
# 这期的音色全部新做（见记忆 sfx-variety：别每期都是 tick/pop/whoosh/bonk/heart）：
#   人声是共振峰合成的“咿咿呀呀”，听得出语气但不是真话；马克笔吱吱写字、价签贴纸、收银机、塑料袋、唱片急刹、
#   铁锚砸地 + 铁链、尺子上的木头脚步、麻绳吱嘎 + 绷直的“嘣”、转盘棘轮减速（和画面的转角同一个公式）、撕纸、结尾贝斯“嘣-嘣”。
# 用法：python mix.py  →  out/sfx.wav
import json, os, sys, re, subprocess, tempfile
import numpy as np
from scipy.signal import lfilter, butter, fftconvolve
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
EVF = json.load(open(os.path.join(HERE, 'events.json'), encoding='utf-8'))
SR = 48000
DUR = EVF['dur'] + 1.0
N = int(SR * DUR)
DRY = np.zeros((2, N)); WET = np.zeros((2, N))
rng = np.random.default_rng(1974)

# ---------------- 工具 ----------------
def tt(d): return np.arange(max(1, int(d * SR))) / SR
def noise(n): return rng.standard_normal(n)
def mx(*xs):
    o = np.zeros(max(len(x) for x in xs))
    for x in xs: o[:len(x)] += x
    return o
def lp(x, fc, o=2): b, a = butter(o, min(fc / (SR / 2), 0.99)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [max(lo, 20) / (SR / 2), min(hi / (SR / 2), 0.99)], 'band'); return lfilter(b, a, x)
def ph(f): return 2 * np.pi * np.cumsum(f) / SR
def att(t, a=0.004): return np.minimum(1, t / a)
def saw(f): p = np.cumsum(f) / SR; return 2 * (p % 1) - 1
def fade(x, a=0.3, b=0.3):
    n = len(x); t = np.arange(n) / SR; d = n / SR
    return x * np.minimum(1, t / max(a, 1e-3)) * np.minimum(1, (d - t) / max(b, 1e-3))
def smooth_rand(n, rate, lo=0.0, hi=1.0, r=None):
    r = r or rng; k = max(2, int(n / SR * rate) + 2)
    return np.interp(np.arange(n), np.linspace(0, n, k), lo + (hi - lo) * r.random(k))
def norm(x, g=0.7): return x / (np.abs(x).max() + 1e-9) * g

def add(sig, at, gain=1.0, pan=0.0, wet=0.3):
    i = int(at * SR)
    if i >= N or i < 0: return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
    DRY[0, i:i + len(sig)] += sig * l * (1 - wet * 0.5); DRY[1, i:i + len(sig)] += sig * r * (1 - wet * 0.5)
    WET[0, i:i + len(sig)] += sig * l * wet; WET[1, i:i + len(sig)] += sig * r * wet

# ---------------- 人声：共振峰合成的咿咿呀呀 ----------------
VOW = {'a': [(800, 1.0), (1200, 0.55), (2600, 0.22)], 'e': [(470, 1.0), (1900, 0.45), (2600, 0.2)], 'i': [(310, 1.0), (2300, 0.4), (3000, 0.18)],
       'o': [(520, 1.0), (860, 0.6), (2500, 0.12)], 'u': [(360, 1.0), (720, 0.45), (2400, 0.1)]}
def formant(src, v): return sum(bp(src, fc * 0.86, fc * 1.14) * g for fc, g in v)
def voice(syl=4, f0=150, rate=0.15, shout=0.0, contour=None, seed=0, breath=0.05, vowels=None):
    r = np.random.default_rng(seed)
    out = np.zeros(int((syl * rate + 0.4) * SR))
    for k in range(syl):
        d = rate * (0.85 + 0.35 * r.random()); n = int(d * SR); t = np.arange(n) / SR
        base = f0 * (contour[k] if contour is not None else (1 + 0.18 * (r.random() - 0.5)))
        f = base * (1 + 0.07 * np.sin(np.pi * t / d)) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
        src = saw(f) + noise(n) * breath
        v = VOW[vowels[k % len(vowels)]] if vowels else list(VOW.values())[r.integers(5)]
        s = formant(src, v)
        env = np.minimum(1, t / 0.012) * np.minimum(1, (d - t) / 0.035)
        cons = hp(noise(n), 2500) * np.exp(-t * 140) * 0.35 * (r.random() > 0.3)
        i = int(k * rate * SR); seg_ = s * env + cons
        out[i:i + n] += seg_[: len(out) - i]
    out = lp(out, 5200)
    if shout: out = np.tanh(norm(out, 1) * (1 + 3 * shout))
    return norm(out, 0.7)

def vendor(syl=4, f=1.0): return voice(syl, 150 * f, 0.15, shout=0.6, contour=[1.05, 1.1, 1.25, 0.95][:syl] if syl <= 4 else None, seed=3, vowels='eaea')
def buyer(syl=5, f=1.0): return voice(syl, 205 * f, 0.13, shout=0.35, contour=None, seed=int(syl * 7 + f * 10), vowels='ioaei')
def agent(syl=2, f=1.0): return voice(syl, 170 * f, 0.13, shout=0.2, contour=[1.15, 0.95], seed=int(f * 100), vowels='ia')
def grumble():
    # “行行行……”：三下往下掉的不情愿 + 最后一口叹气
    v = voice(3, 140, 0.17, shout=0.0, contour=[1.12, 1.0, 0.86], seed=8, breath=0.2, vowels='iii')
    t = tt(0.55); sigh = bp(noise(len(t)), 500, 2200) * np.sin(np.pi * t / 0.55) ** 2 * 0.25
    return mx(v, np.concatenate([np.zeros(int(0.5 * SR)), sigh]))
def huh():
    # “嗯？”往上挑
    t = tt(0.42); f = 120 * (1 + 0.9 * (t / 0.42) ** 2)
    s = formant(saw(f) + noise(len(t)) * 0.05, VOW['u']) * np.minimum(1, t / 0.03) * np.minimum(1, (0.42 - t) / 0.08)
    return norm(lp(s, 3000), 0.7)
def hmm(f=1.0):
    # 托着下巴想：“嗯……”闭着嘴哼，音高慢慢往下
    t = tt(0.75); fr = 165 * f * (1 - 0.12 * t / 0.75) * (1 + 0.01 * np.sin(2 * np.pi * 5 * t))
    s = formant(saw(fr) + noise(len(t)) * 0.04, [(260, 1.0), (1000, 0.15), (2300, 0.05)]) * np.minimum(1, t / 0.06) * np.minimum(1, (0.75 - t) / 0.2)
    return norm(lp(s, 1800), 0.55)
def chuckle():
    # 摊主偷笑：“嘿嘿嘿”，气声多
    out = np.zeros(int(0.7 * SR))
    for k in range(3):
        t = tt(0.09); f = 175 * (1.08 - k * 0.05) * np.ones(len(t))
        s = formant(saw(f) * 0.6 + noise(len(t)) * 0.5, VOW['e']) * np.sin(np.pi * t / 0.09)
        i = int(k * 0.15 * SR); out[i:i + len(s)] += s
    return norm(out, 0.65)
def strain(d=2.0):
    # 两个人使劲往前挣：“嗯——”憋着劲，带抖
    t = tt(d); f = 230 * (1 + 0.03 * np.sin(2 * np.pi * 7 * t)) * (1 + 0.04 * np.sin(2 * np.pi * 0.9 * t))
    a = formant(saw(f) + noise(len(t)) * 0.15, VOW['u']) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t) ** 2)
    f2 = 200 * (1 + 0.035 * np.sin(2 * np.pi * 6.1 * t + 1))
    b = formant(saw(f2) + noise(len(t)) * 0.15, VOW['i']) * (0.6 + 0.4 * np.cos(2 * np.pi * 1.3 * t) ** 2)
    return fade(norm(lp(a + b * 0.8, 3000), 0.5), 0.2, 0.3)

# ---------------- 场景底 ----------------
def market(d=9.0):
    # 夜市：一群人的嘈杂（几层带通噪声各自按说话节奏起伏）+ 远处油锅滋滋 + 灯串电流
    n = int(d * SR); out = np.zeros(n)
    for k in range(7):
        lo = 250 + 120 * k; layer = bp(noise(n), lo, lo * 3.2) * smooth_rand(n, 4 + k * 0.7, 0.1, 1.0) ** 2
        out += layer * (0.5 if k < 5 else 0.3)
    sizzle = lp(hp(noise(n), 4500), 9000) * (0.25 + (rng.random(n) > 0.9993) * 6) * 0.03
    hum = np.sin(ph(np.full(n, 100.0))) * 0.012
    return fade(lp(out, 3500) * 0.32 + sizzle + hum, 0.35, 0.4)
def mindbed(d=6.9):
    # 脑子里：很低的暖嗡（两个音慢慢拍）+ 木鱼一样的滴答（每秒两下，像在想）
    n = int(d * SR); t = np.arange(n) / SR
    drone = (np.sin(ph(np.full(n, 98.0))) + 0.7 * np.sin(ph(np.full(n, 147.3))) + 0.3 * np.sin(ph(np.full(n, 196.6)))) * 0.03 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t))
    tick = np.zeros(n)
    for k, s in enumerate(np.arange(0.25, d, 0.5)):
        tb = tt(0.06); w = bp(noise(len(tb)), 900, 2600) * np.exp(-tb * 90) + np.sin(ph(np.full(len(tb), 1250.0 if k % 2 else 940.0))) * np.exp(-tb * 70) * 0.6
        i = int(s * SR); tick[i:i + len(w)] += w[: n - i] * 0.12
    return fade(lp(drone, 800) + tick, 0.4, 0.4)
def showbed(d=7.9):
    # 演播室：观众低声嗡嗡 + 空间感，比夜市干净、更“室内”
    n = int(d * SR); out = np.zeros(n)
    for k in range(4):
        lo = 300 + 200 * k; out += bp(noise(n), lo, lo * 2.5) * smooth_rand(n, 3 + k, 0.2, 1.0) ** 2
    return fade(lp(out, 2500) * 0.14 + lp(noise(n), 200) * 0.03, 0.3, 0.4)
def officebed(d=7.5):
    # 办公室：空调风 + 远处稀疏的键盘声
    n = int(d * SR); ac = lp(noise(n), 350) * 0.09 + np.sin(ph(np.full(n, 50.0))) * 0.01
    keys = np.zeros(n); s = 0.3
    while s < d - 0.1:
        tb = tt(0.03); c = bp(noise(len(tb)), 1500, 6000) * np.exp(-tb * 220) * 0.06
        i = int(s * SR); keys[i:i + len(c)] += c[: n - i]; s += 0.08 + rng.random() * (0.6 if rng.random() > 0.7 else 0.12)
    return fade(ac + lp(keys, 4000) * 0.6, 0.3, 0.4)

# ---------------- 夜市里的小东西 ----------------
def tagswing(): t = tt(0.22); return bp(noise(len(t)), 800, 3000) * np.sin(np.pi * t / 0.22) ** 2 * 0.25
def bubble(f=1.0):
    # 对话框冒出来：短短一声“啵”往上挑
    t = tt(0.08); return np.sin(ph(380 * f + 700 * f * (t / 0.08))) * np.exp(-t * 40) * att(t, 0.002) * 0.45
def marker(d=0.3, f=1.0):
    # 马克笔在卡纸上：毛毡头的沙沙 + 一丝吱吱声
    t = tt(d); n = len(t)
    fel = bp(noise(n), 1800, 6500) * (0.6 + 0.4 * smooth_rand(n, 30, 0, 1))
    sq = np.sin(ph(1700 * f * (1 + 0.15 * np.sin(2 * np.pi * 11 * t)))) * smooth_rand(n, 18, 0, 1) ** 3 * 0.25
    return fade(fel * 0.5 + sq, 0.02, 0.05) * 0.8
def sticker():
    # 贴纸“啪”地按上去：纸的拍击 + 一点点粘胶的“嗒”
    t = tt(0.12); slap = bp(noise(len(t)), 900, 5000) * np.exp(-t * 70)
    thump = np.sin(ph(160 + 120 * np.exp(-t * 60))) * np.exp(-t * 35) * 0.5
    return (slap * 0.7 + thump) * att(t, 0.001)
def register():
    # 收银机：机械“咔哒”+“叮”
    t = tt(0.9); clunk = lp(noise(len(t)), 1800) * np.exp(-t * 60) * 0.6
    bell = (np.sin(2 * np.pi * 2093 * t) + 0.5 * np.sin(2 * np.pi * 3140 * t) + 0.25 * np.sin(2 * np.pi * 5230 * t)) * np.exp(-t * 4.5) * 0.35
    b = np.zeros(len(t)); j = int(0.09 * SR); b[j:] = bell[: len(t) - j]
    return clunk + b
def bag():
    # 塑料袋窸窸窣窣：稀疏的脆响
    t = tt(0.7); n = len(t); imp = (rng.random(n) > 0.995) * rng.standard_normal(n) * 3
    env = np.sin(np.pi * t / 0.7) ** 0.7
    return hp(lp(imp + noise(n) * 0.08, 9000), 1800) * env * 0.4
def step(f=1.0):
    t = tt(0.14); thud = np.sin(ph(np.full(len(t), 95.0 * f))) * np.exp(-t * 40)
    scuff = bp(noise(len(t)), 600, 3000) * np.exp(-t * 55) * 0.4
    return (thud + scuff) * att(t, 0.002) * 0.6
def thinkpop():
    # 想法泡泡：三个小圆点一个比一个大——“咕、咕、啵”
    out = np.zeros(int(0.5 * SR))
    for k, (f0, g) in enumerate([(500, 0.35), (650, 0.45), (820, 0.6)]):
        t = tt(0.09); s = np.sin(ph(f0 + f0 * 1.2 * (t / 0.09))) * np.exp(-t * 35) * g
        i = int(k * 0.09 * SR); out[i:i + len(s)] += s
    return out
def marimba(f, d=0.5): t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 30)) * np.exp(-t * 9) * att(t, 0.001)
def tick():
    # 打勾：木琴两个音往上一跳
    a = marimba(1319, 0.4) * 0.5; b = marimba(1760, 0.5) * 0.55; out = np.zeros(int(0.6 * SR)); out[:len(a)] += a; j = int(0.08 * SR); out[j:j + len(b)] += b
    return out
def whip(d=0.6):
    # 甩镜头：一道很快的风声，中间最尖
    t = tt(d); n = len(t); out = np.zeros(n); x = noise(n); blk = 512
    for i in range(0, n, blk):
        p = i / n; fc = 600 + 4500 * np.sin(np.pi * p)
        out[i:i + blk] = bp(x[max(0, i - 2048):i + blk], fc * 0.7, fc * 1.4)[-len(x[i:i + blk]):]
    return out * np.sin(np.pi * t / d) ** 3 * 0.9
def slap():
    # 一张大海报拍上来：低频“砰”+ 纸面炸开的噪声 + 一点房间
    t = tt(0.35); thump = np.sin(ph(70 + 90 * np.exp(-t * 30))) * np.exp(-t * 14)
    paper = bp(noise(len(t)), 700, 6000) * np.exp(-t * 45)
    return np.tanh((thump * 0.9 + paper * 0.8) * 1.5) * att(t, 0.001) * 0.8
def scratch():
    # 唱片急刹：带通的中心飞快地来回扫两下，然后戛然而止
    d = 0.42; t = tt(d); n = len(t); x = saw(np.full(n, 90.0)) * 0.5 + noise(n) * 0.5
    centre = 400 + 2200 * np.abs(np.sin(2 * np.pi * 2.4 * t)) ** 1.5
    out = np.zeros(n); blk = 256
    for i in range(0, n, blk):
        fc = centre[i]; out[i:i + blk] = bp(x[max(0, i - 1024):i + blk], fc * 0.8, fc * 1.25)[-len(x[i:i + blk]):]
    return np.tanh(out * 3) * np.minimum(1, (d - t) / 0.02) * 0.6

# ---------------- 钻进脑子 / 尺子 / 锚 / 绳子 ----------------
def suck(d=0.6):
    # 冲进脑袋：风声越来越尖越来越响，最后“噗”一下
    t = tt(d); n = len(t); out = np.zeros(n); x = noise(n); blk = 512
    for i in range(0, n, blk):
        p = i / n; fc = 300 + 4000 * p ** 2
        out[i:i + blk] = bp(x[max(0, i - 2048):i + blk], fc * 0.7, fc * 1.4)[-len(x[i:i + blk]):]
    body = out * (t / d) ** 2 * 0.9
    tb = tt(0.2); pf = np.sin(ph(90 + 120 * np.exp(-tb * 25))) * np.exp(-tb * 18) * 0.7
    return mx(body, np.concatenate([np.zeros(n - int(0.05 * SR)), pf]))
def fallwhistle(d=0.4):
    t = tt(d); f = 2100 - 1500 * (t / d) ** 0.8
    return np.sin(ph(f * (1 + 0.01 * np.sin(2 * np.pi * 12 * t)))) * np.minimum(1, t / 0.03) * 0.3
def clank(f=1.0):
    # 铁锚砸地：低频闷响 + 不成和弦的金属泛音 + 砂石
    t = tt(1.6); thud = np.sin(ph(60 + 80 * np.exp(-t * 25))) * np.exp(-t * 9)
    metal = sum(np.sin(2 * np.pi * fr * f * t) * np.exp(-t * dk) * g for fr, dk, g in [(187, 4, 0.5), (473, 5, 0.4), (1131, 7, 0.3), (1869, 9, 0.22), (2950, 12, 0.15)])
    grit = bp(noise(len(t)), 800, 5000) * np.exp(-t * 25) * 0.4
    return np.tanh((thud * 1.1 + metal * 0.7 + grit) * 1.2) * att(t, 0.001) * 0.8
def chain(d=0.6):
    # 铁链哗啦：一串小金属碰撞，越来越稀
    n = int((d + 0.2) * SR); out = np.zeros(n); s = 0.0
    while s < d:
        tb = tt(0.05); fr = 2200 + 2600 * rng.random()
        c = (np.sin(2 * np.pi * fr * tb) + 0.5 * np.sin(2 * np.pi * fr * 1.51 * tb)) * np.exp(-tb * 90) * (1 - s / d) * 0.4
        i = int(s * SR); out[i:i + len(c)] += c[: n - i]; s += 0.015 + 0.07 * (s / d) * rng.random()
    return out
def rulerstep(f=1.0):
    # 踩在木尺上：空心木头“哒”
    t = tt(0.12); body = bp(noise(len(t)), 700 * f, 1300 * f, 2) * np.exp(-t * 60) * 1.6
    tone = np.sin(2 * np.pi * 980 * f * t) * np.exp(-t * 70) * 0.4
    return (body + tone) * att(t, 0.001) * 0.6
def creak(d=0.8):
    # 麻绳吱嘎：不规则的一下下摩擦，过一个共振
    n = int(d * SR); imp = np.zeros(n); s = 0.0
    while s < d:
        i = int(s * SR); imp[i] = 1 + rng.random(); s += 1 / (35 + 45 * rng.random())
    out = bp(imp, 380, 1100, 2) * 6 + bp(imp, 1500, 2600, 2) * 2
    t = np.arange(n) / SR
    return out * np.sin(np.pi * t / d) ** 0.8 * 0.35
def ks(f, d=0.8, damp=0.996, bright=0.6):
    # Karplus-Strong 拨弦
    n = int(d * SR); L = int(SR / f); buf = noise(L) * 0.8; out = np.zeros(n)
    buf = lp(buf, 1500 + 6000 * bright)
    for i in range(n):
        out[i] = buf[i % L]; buf[i % L] = damp * 0.5 * (buf[i % L] + buf[(i + 1) % L])
    return out
def twang():
    # 绳子一下绷直：“嘣”一声低弦 + 闷响
    s = ks(82, 0.7, 0.994, 0.5) * 0.8; t = tt(0.25); th = np.sin(ph(70 + 50 * np.exp(-t * 30))) * np.exp(-t * 20) * 0.5
    return mx(s, th)
def reveal():
    # 牌子亮出来：“当当！”两声铜管味的短音
    out = np.zeros(int(0.7 * SR))
    for k, (f, d) in enumerate([(523, 0.12), (784, 0.42)]):
        t = tt(d); s = lp(saw(np.full(len(t), f)) + saw(np.full(len(t), f * 1.005)), 2800) * np.minimum(1, t / 0.01) * np.exp(-t * 3.5) * 0.4
        i = int(k * 0.12 * SR); out[i:i + len(s)] += s
    return out
def boing(f=1.0):
    # 弹簧“嘣~”，尾巴抖
    t = tt(0.5); fr = 230 * f * (1 + 0.35 * np.exp(-t * 6) * np.sin(2 * np.pi * 14 * t)) * (1 + 0.3 * t)
    return np.sin(ph(fr)) * np.exp(-t * 6) * att(t, 0.003) * 0.5
def kazoo(f, d):
    t = tt(d); s = saw(f * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))) + noise(len(t)) * 0.15
    return formant(s, VOW['u']) * np.minimum(1, t / 0.015) * np.minimum(1, (d - t) / 0.04)
def proud():
    # 得意：卡祖笛“哒-哒-哒——”
    out = np.zeros(int(0.9 * SR))
    for k, (f, d) in enumerate([(523, 0.11), (659, 0.11), (784, 0.4)]):
        s = kazoo(f, d); i = int(k * 0.12 * SR); out[i:i + len(s)] += s
    return norm(out, 0.5)
def scribble(d=0.6):
    # 一支大马克笔来回涂：每一道一声“唰”，方向换一次音高换一次
    n = int(d * SR); out = np.zeros(n); k = 7
    for j in range(k):
        a, b = int(j * n / k), int((j + 1) * n / k); m = b - a; t = np.arange(m) / SR
        fel = bp(noise(m), 1200 + 400 * (j % 2), 5000) * np.sin(np.pi * t / (m / SR)) ** 0.6
        out[a:b] += fel
    return out * 0.55

# ---------------- 转盘节目 ----------------
DA = 2 * np.pi / 20
def w_ang(u, t1, dur=1.7, total=6 * np.pi):
    t0 = t1 - dur
    if u >= t1: return 0.0
    if u >= t0: return total * (1 - (u - t0) / dur) ** 3
    return total + (t0 - u) * 3 * total / dur
def ratchet(t_start, t1, f=1.0, wdur=1.7):
    # 转盘的拨片打在钉子上：每过一格“嗒”一下，用和画面一样的转角公式，所以越转越慢、最后停在数上
    d = t1 - t_start; n = int((d + 0.1) * SR); out = np.zeros(n)
    tb = tt(0.012); clk = (hp(noise(len(tb)), 2500) * 0.6 + np.sin(2 * np.pi * 2600 * f * tb) * 0.5) * np.exp(-tb * 500)
    prev = np.floor(w_ang(t_start, t1, wdur) / DA)
    for i in range(0, n, 24):
        u = t_start + i / SR; c = np.floor(w_ang(u, t1, wdur) / DA)
        if c != prev: out[i:i + len(clk)] += clk[: n - i]; prev = c
    return out * 0.5
def ding(f=1.0):
    t = tt(1.4); f0 = 1568 * f
    return (np.sin(2 * np.pi * f0 * t) + 0.4 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t * 6) + 0.2 * np.sin(2 * np.pi * f0 * 5.4 * t) * np.exp(-t * 12)) * np.exp(-t * 3) * att(t, 0.001) * 0.35
def stamp():
    t = tt(0.3); th = np.sin(ph(110 + 90 * np.exp(-t * 40))) * np.exp(-t * 22)
    pap = bp(noise(len(t)), 500, 3500) * np.exp(-t * 50) * 0.5
    return (th + pap) * att(t, 0.001) * 0.8
def flap():
    # 横幅掉下来：布哗啦啦抖几下，最后“啪”绷住
    t = tt(0.45); fl = bp(noise(len(t)), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * t) ** 2) * np.exp(-t * 4)
    tb = tt(0.08); snap = bp(noise(len(tb)), 600, 4000) * np.exp(-tb * 70)
    return mx(fl * 0.4, np.concatenate([np.zeros(int(0.33 * SR)), snap * 0.6]))
def cloth(): t = tt(0.25); return bp(noise(len(t)), 400, 3000) * np.sin(np.pi * t / 0.25) ** 2 * 0.25
def shrink(d=0.45):
    t = tt(d); s = np.sin(ph(1300 * np.exp(-t * 5.5))) * np.exp(-t * 2) * 0.35
    return mx(s * att(t, 0.005), whip(d) * 0.4)
def hop(f=1.0): t = tt(0.16); return np.sin(ph(320 * f + 600 * f * (t / 0.16) ** 0.7)) * np.sin(np.pi * t / 0.16) * 0.4
def ropetie():
    t = tt(0.22); fr = bp(noise(len(t)), 900, 4000) * np.exp(-t * 14) * 0.35
    return mx(fr, creak(0.2) * 0.6)

# ---------------- 房产经纪人 ----------------
def popup(f=1.0):
    t = tt(0.18); s = np.sin(ph(180 * f + 260 * f * (t / 0.18))) * np.exp(-t * 18)
    puff = bp(noise(len(t)), 300, 1500) * np.exp(-t * 30) * 0.4
    return (s + puff) * att(t, 0.002) * 0.6
def circle(d=0.35, f=1.0):
    # 红笔画圈：吱吱声的音高跟着画圈起伏一圈
    t = tt(d); fel = bp(noise(len(t)), 2000, 6500) * 0.4
    sq = np.sin(ph(1500 * f * (1 + 0.25 * np.sin(2 * np.pi * t / d)))) * 0.25 * smooth_rand(len(t), 25, 0.3, 1)
    return fade(fel + sq, 0.02, 0.05) * 0.8
def shrugboing():
    # 摊手：木琴两个音往下“嘟-嘟”
    a = marimba(784, 0.3) * 0.45; b = marimba(587, 0.45) * 0.45; out = np.zeros(int(0.6 * SR)); out[:len(a)] += a; j = int(0.12 * SR); out[j:j + len(b)] += b
    return out

# ---------------- 结尾 ----------------
def tear(d=0.55):
    # 撕纸：一路噼里啪啦的纤维断裂
    t = tt(d); n = len(t); crack = (rng.random(n) > 0.985) * rng.standard_normal(n) * 2.5
    body = bp(noise(n) * 0.4 + crack, 900, 6000) * (0.4 + 0.6 * smooth_rand(n, 40, 0, 1))
    return fade(body, 0.02, 0.08) * np.minimum(1, 0.3 + t / d) * 0.6
def pullback(d=0.9):
    t = tt(d); n = len(t); out = np.zeros(n); x = noise(n); blk = 512
    for i in range(0, n, blk):
        p = i / n; fc = 3500 * (1 - p) ** 1.5 + 250
        out[i:i + blk] = bp(x[max(0, i - 2048):i + blk], fc * 0.7, fc * 1.4)[-len(x[i:i + blk]):]
    return out * np.sin(np.pi * t / d) ** 2 * 0.6
def sparkle():
    out = np.zeros(int(1.0 * SR))
    for k in range(7):
        f = 2600 + 2400 * rng.random(); t = tt(0.4); b = np.sin(2 * np.pi * f * t) * np.exp(-t * 14) * 0.12
        i = int(k * 0.05 * SR); out[i:i + len(b)] += b[: len(out) - i]
    return out
def button():
    # 收尾：低音贝斯“嘣-嘣”（五度下行）+ 一下轻轻的镲边
    a = ks(98, 0.5, 0.993, 0.3) * 0.7; b = ks(65.4, 0.9, 0.995, 0.3) * 0.8
    out = np.zeros(int(1.2 * SR)); out[:len(a)] += a; j = int(0.22 * SR); out[j:j + len(b)] += b
    tb = tt(0.12); rim = bp(noise(len(tb)), 2500, 8000) * np.exp(-tb * 45) * 0.25; out[j:j + len(rim)] += rim
    return out

# ---------------- 事件 → 声音（声音, 增益, 混响量） ----------------
SOUNDS = {
    'market': lambda e: (market(e.get('d', 9)), 0.9, 0.25),
    'mindbed': lambda e: (mindbed(e.get('d', 6.9)), 0.8, 0.5),
    'showbed': lambda e: (showbed(e.get('d', 7.9)), 0.8, 0.5),
    'officebed': lambda e: (officebed(e.get('d', 7.5)), 0.8, 0.3),
    'tagswing': lambda e: (tagswing(), 0.6, 0.2),
    'vendor': lambda e: (vendor(e.get('syl', 4), e.get('f', 1.0)), 0.55, 0.25),
    'buyer': lambda e: (buyer(e.get('syl', 5), e.get('f', 1.0)), 0.55, 0.25),
    'agent': lambda e: (agent(e.get('syl', 2), e.get('f', 1.0)), 0.5, 0.3),
    'grumble': lambda e: (grumble(), 0.55, 0.25),
    'huh': lambda e: (huh(), 0.5, 0.3),
    'chuckle': lambda e: (chuckle(), 0.5, 0.25),
    'strain': lambda e: (strain(e.get('d', 2.0)), 0.6, 0.3),
    'bubble': lambda e: (bubble(e.get('f', 1.0)), 0.5, 0.2),
    'marker': lambda e: (marker(e.get('d', 0.3), e.get('f', 1.0)), 0.55, 0.15),
    'sticker': lambda e: (sticker(), 0.7, 0.2),
    'register': lambda e: (register(), 0.5, 0.3),
    'bag': lambda e: (bag(), 0.7, 0.15),
    'step': lambda e: (step(e.get('f', 1.0)), 0.55, 0.15),
    'thinkpop': lambda e: (thinkpop(), 0.55, 0.3),
    'tick': lambda e: (tick(), 0.5, 0.3),
    'whip': lambda e: (whip(e.get('d', 0.6)), 0.6, 0.2),
    'slap': lambda e: (slap(), 0.8, 0.35),
    'scratch': lambda e: (scratch(), 0.65, 0.2),
    'suck': lambda e: (suck(e.get('d', 0.6)), 0.6, 0.3),
    'fallwhistle': lambda e: (fallwhistle(e.get('d', 0.4)), 0.5, 0.3),
    'clank': lambda e: (clank(e.get('f', 1.0)), 0.8, 0.45),
    'chain': lambda e: (chain(e.get('d', 0.6)), 0.6, 0.35),
    'rulerstep': lambda e: (rulerstep(e.get('f', 1.0)), 0.6, 0.35),
    'creak': lambda e: (creak(e.get('d', 0.8)), 0.6, 0.25),
    'twang': lambda e: (twang(), 0.75, 0.35),
    'reveal': lambda e: (reveal(), 0.55, 0.35),
    'boing': lambda e: (boing(e.get('f', 1.0)), 0.6, 0.3),
    'proud': lambda e: (proud(), 0.5, 0.3),
    'scribble': lambda e: (scribble(e.get('d', 0.6)), 0.6, 0.15),
    'ratchet': lambda e: (ratchet(e['t'], e['t1'], e.get('f', 1.0), e.get('wdur', 1.7)), 0.7, 0.3),
    'hmm': lambda e: (hmm(e.get('f', 1.0)), 0.5, 0.3),
    'ding': lambda e: (ding(e.get('f', 1.0)), 0.55, 0.45),
    'stamp': lambda e: (stamp(), 0.7, 0.3),
    'flap': lambda e: (flap(), 0.6, 0.3),
    'cloth': lambda e: (cloth(), 0.5, 0.2),
    'shrink': lambda e: (shrink(e.get('d', 0.45)), 0.55, 0.3),
    'hop': lambda e: (hop(e.get('f', 1.0)), 0.5, 0.25),
    'ropetie': lambda e: (ropetie(), 0.6, 0.2),
    'popup': lambda e: (popup(e.get('f', 1.0)), 0.55, 0.25),
    'circle': lambda e: (circle(e.get('d', 0.35), e.get('f', 1.0)), 0.55, 0.15),
    'shrugboing': lambda e: (shrugboing(), 0.5, 0.3),
    'tear': lambda e: (tear(e.get('d', 0.55)), 0.75, 0.2),
    'pullback': lambda e: (pullback(e.get('d', 0.9)), 0.55, 0.3),
    'sparkle': lambda e: (sparkle(), 0.5, 0.45),
    'button': lambda e: (button(), 0.7, 0.35),
}
# 有音高的（音阶、和画面同步的节奏）不随机变调
NOVARY = {'hmm', 'ratchet', 'ding', 'tick', 'reveal', 'proud', 'button', 'shrugboing', 'register', 'market', 'mindbed', 'showbed', 'officebed', 'vendor', 'buyer', 'agent', 'grumble'}
unknown = set()
for e in EVF['ev']:
    if e['s'] == 'cue': continue
    fn = SOUNDS.get(e['s'])
    if not fn: unknown.add(e['s']); continue
    sig, g, wet = fn(e)
    v = e.get('vary', 0.0 if e['s'] in NOVARY else 0.05)
    if v > 0:
        r = 1 + (rng.random() * 2 - 1) * v
        sig = np.interp(np.arange(0, len(sig) - 1, r), np.arange(len(sig)), sig)
    add(sig, e['t'], g * e.get('g', 1.0), e.get('pan', 0.0), wet)
if unknown: print('未映射的事件:', unknown)

# 很轻的空气底噪，让静场不“死”
t = np.arange(N) / SR
DRY += lp(rng.standard_normal(N), 900) * 0.05 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 17))

# 混响：指数衰减的噪声脉冲（短一点，纸面世界不要大厅感）
ir_t = tt(1.6); ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t * 3.6)
ir = np.stack([lp(ir[0], 6000), lp(ir[1], 6000)]) * 0.07
mix = DRY + np.stack([fftconvolve(WET[c], ir[c])[:N] for c in range(2)])
pk = np.abs(mix).max()
mix = np.tanh(mix / pk * 1.1) / np.tanh(1.1) * 10 ** (-3 / 20)
# 响度对齐到约 -16.5 LUFS，再软限幅把峰值压在 -1.2 dBFS 以下
def lufs_of(x):
    f = os.path.join(tempfile.gettempdir(), 'anchor_lufs.wav'); sf.write(f, x.T.astype(np.float32), SR)
    o = subprocess.run(['ffmpeg', '-v', 'info', '-nostats', '-i', f, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore').stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
ceil = 10 ** (-1.2 / 20)
def soft(x): k = ceil * 0.8; a = np.abs(x); return np.where(a > k, np.sign(x) * (k + (ceil - k) * np.tanh((a - k) / (ceil - k))), x)
for _ in range(2):
    l0 = lufs_of(mix); mix = soft(mix * 10 ** ((-16.5 - l0) / 20))
print('loudness', round(l0, 1), '->', round(lufs_of(mix), 1), 'LUFS')
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out', 'sfx.wav')
sf.write(out, mix.T.astype(np.float32), SR, subtype='PCM_24')
print('ok', out, f'{DUR:.1f}s', 'events', len(EVF['ev']))
