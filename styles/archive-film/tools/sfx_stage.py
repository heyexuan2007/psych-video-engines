
# ================= 舞台片第二批：每个场景专门做的音色（不再复用通用那几个） =================
# 这个文件被 mix.py 用 exec 读进来，共用 mix.py 里的 tt / ph / lp / hp / bp / mx / att / bell / snore / rng / SR
def saw(f):
    p = ph(f) / (2 * np.pi); return 2 * (p % 1) - 1
def env_adsr(n, a=0.01, r=0.1):
    t = np.arange(n) / SR; d = n / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
def ks(f, d=1.5, bright=0.5, damp=0.996):
    # Karplus-Strong 拨弦：竖琴、贝斯
    n = int(d * SR); L = max(2, int(SR / f)); b = rng.standard_normal(L) * 0.5
    if L > 20: b = lp(b, 800 + 6000 * bright)
    out = np.zeros(n); b = list(b); idx = 0
    for i in range(n):
        j = idx % L; nx = (idx + 1) % L
        out[i] = b[j]; b[j] = damp * 0.5 * (b[j] + b[nx]); idx += 1
    return out * att(np.arange(n) / SR, 0.002)
def formants(x, fs, bw=1.0):
    return sum(bp(x, f * (1 - 0.12 * bw), f * (1 + 0.12 * bw)) * g for f, g in fs)

def snare(g=1.0):
    t = tt(0.2); n = hp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 26)
    body = np.sin(ph(200 + 60 * np.exp(-t * 50))) * np.exp(-t * 30) * 0.6
    return (n * 0.7 + body) * g * att(t, 0.0008)
def drumroll(d=2.4):
    # 小军鼓滚奏：越来越密、越来越响，最后一下重击
    out = np.zeros(int((d + 0.4) * SR)); tp = 0.0
    while tp < d:
        p = tp / d; i = int(tp * SR); s = snare(0.18 + 0.75 * p ** 1.6) * (0.85 + 0.3 * rng.random())
        out[i:i + len(s)] += s[: len(out) - i]; tp += 1 / (11 + 15 * p) * (0.9 + 0.2 * rng.random())
    s = snare(1.3); i = int(d * SR); out[i:i + len(s)] += s[: len(out) - i]
    return out
def crash(d=2.6):
    # 镲片：亮的噪声 + 一堆不和谐的金属泛音
    t = tt(d); n = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 1.7) * 0.6
    metal = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * (1.2 + k * 0.5)) for k, f in enumerate([3170, 4123, 5277, 6611, 7934, 9120])) * 0.06
    hit = bp(rng.standard_normal(len(t)), 800, 5000) * np.exp(-t * 30) * 0.5
    return (n + metal + hit) * att(t, 0.001)
def whisper(d=4.0, voices=4):
    # 窃窃私语：一个个“丝丝/嘶嘶”的音节，几个人错开说
    out = np.zeros(int(d * SR))
    for v in range(voices):
        tp = rng.random() * 0.3
        while tp < d - 0.2:
            L = 0.06 + rng.random() * 0.14; t = tt(L); n = rng.standard_normal(len(t)); kind = rng.random()
            if kind < 0.4: s = bp(n, 4200, 8000)
            elif kind < 0.7: s = bp(n, 1800, 3800)
            else: s = formants(n, [(700 + 300 * rng.random(), 1), (1500 + 600 * rng.random(), 0.6)], 1.4)
            s = s * np.sin(np.pi * t / L) ** 1.5 * (0.5 + 0.5 * rng.random()); i = int(tp * SR)
            out[i:i + len(s)] += s[: len(out) - i]
            tp += L + (0.03 + rng.random() * 0.12) + (0.4 * rng.random() if rng.random() < 0.15 else 0)
    t = tt(d); return out * 0.5 * np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6)
def plip(f=1.0):
    # 睁眼：短短一声水滴似的“噗啾”
    t = tt(0.12); fr = (1100 + 1700 * (1 - np.exp(-t * 70))) * f
    return np.sin(ph(fr)) * np.exp(-t * 38) * att(t, 0.002) * 0.6
def glock(f=1568):
    # 钟琴：亮、短、带一点金属
    t = tt(1.4); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 9) + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 18)) * att(t, 0.001) * 0.6
def glock_run(notes=(1047, 1319, 1568, 2093), gap=0.07):
    out = np.zeros(int((gap * len(notes) + 1.5) * SR))
    for k, f in enumerate(notes):
        s = glock(f) * (0.7 + 0.1 * k); i = int(k * gap * SR); out[i:i + len(s)] += s[: len(out) - i]
    return out
def flick():
    # 日光灯启动：啪、滋滋闪几下，最后稳定成一点嗡声
    out = np.zeros(int(1.6 * SR))
    for tp in [0, 0.09, 0.15, 0.32, 0.4, 0.58]:
        t = tt(0.06); c = mx(hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 90) * 0.6, np.sin(2 * np.pi * 120 * t) * 0.25 * np.exp(-t * 30))
        i = int(tp * SR); out[i:i + len(c)] += c[: len(out) - i]
    t = tt(1.6); hum = (np.sin(2 * np.pi * 120 * t) + 0.5 * np.sin(2 * np.pi * 240 * t) + 0.2 * np.sin(2 * np.pi * 360 * t)) * 0.05 * (t > 0.6) * np.exp(-(t - 0.6).clip(0) * 1.2)
    thump = np.sin(ph(60 + 40 * np.exp(-t * 30))) * np.exp(-t * 10) * 0.7
    return out + hum + thump
def buzzer(d=0.5):
    # 答错了：综艺节目的低音蜂鸣
    t = tt(d); s = (np.sign(np.sin(2 * np.pi * 98 * t)) + np.sign(np.sin(2 * np.pi * 104 * t))) * 0.18
    return lp(s, 1600) * env_adsr(len(t), 0.005, 0.06)
def tromb():
    # 悲伤长号：“哇——哇——哇——哇~~~”
    out = []
    for k, (f, d) in enumerate([(233, 0.36), (220, 0.36), (208, 0.36), (196, 1.2)]):
        t = tt(d); vib = 1 + (0.012 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.3) if k == 3 else 0)
        fr = f * vib * (1 - 0.03 * np.exp(-t * 25)); e = env_adsr(len(t), 0.03, 0.08 if k < 3 else 0.5)
        s = saw(fr); s = lp(s, 1540) * 0.5 + lp(s, 300) * 0.4
        wah = 0.55 + 0.45 * np.sin(np.pi * np.minimum(1, t / d))
        out.append(np.tanh(s * 1.6 * wah) * e * 0.4)
    return np.concatenate(out)
def slide(up=True, d=0.55):
    # 滑哨：往上“咻~”
    t = tt(d); p = t / d; fr = (500 + 1500 * (p if up else 1 - p) ** 1.2) * (1 + 0.02 * np.sin(2 * np.pi * 9 * t))
    return (np.sin(ph(fr)) * 0.5 + bp(rng.standard_normal(len(t)), 1500, 4000) * 0.05) * env_adsr(len(t), 0.02, 0.08)
def cloth(d=0.35):
    # 布料一抖：快速扑簌
    t = tt(d); return bp(rng.standard_normal(len(t)), 600, 4500) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) * np.exp(-t * 6) * 0.7
def woodstep(d=1.6, rate=3.2, f=1.0):
    # 踩在舞台木地板上：空心的“咚、咚”，偶尔板子吱一下
    out = np.zeros(int((d + 0.3) * SR)); tp = 0.0; k = 0
    while tp < d:
        t = tt(0.16); knock = np.sin(ph((140 + 30 * (k % 2)) * f + 80 * np.exp(-t * 60))) * np.exp(-t * 32) * 0.7 + bp(rng.standard_normal(len(t)), 500, 1600) * np.exp(-t * 55) * 0.35
        i = int(tp * SR); out[i:i + len(knock)] += knock[: len(out) - i] * (0.8 + 0.3 * rng.random())
        if rng.random() < 0.18:
            t2 = tt(0.18); cr = bp(np.sign(np.sin(ph(330 + 120 * t2 / 0.18))) * 0.1, 300, 2000) * np.sin(np.pi * t2 / 0.18); j = i + int(0.04 * SR); out[j:j + len(cr)] += cr[: len(out) - j]
        tp += 1 / rate * (0.92 + 0.16 * rng.random()); k += 1
    return out
def bassline(notes=(98, 123, 147, 165, 147, 123, 110, 98), gap=0.2):
    # 得意走路的小贝斯
    out = np.zeros(int((gap * len(notes) + 0.8) * SR))
    for k, f in enumerate(notes):
        s = lp(ks(f, 0.5, 0.25, 0.993), 900) * 1.4; i = int(k * gap * SR); out[i:i + len(s)] += s[: len(out) - i]
        if k % 2 == 0: c = snare(0.12) * 0.6; out[i:i + len(c)] += c[: len(out) - i]
    return out
def tick_tock(d=6.0):
    # 墙上的钟：滴、答
    out = np.zeros(int(d * SR)); tp = 0.0; k = 0
    while tp < d - 0.1:
        t = tt(0.05); f = 2600 if k % 2 == 0 else 1900
        c = (np.sin(2 * np.pi * f * t) * 0.5 + bp(rng.standard_normal(len(t)), f * 0.7, f * 1.4) * 0.5) * np.exp(-t * 120)
        i = int(tp * SR); out[i:i + len(c)] += c[: len(out) - i]; tp += 0.5; k += 1
    return out * 0.5
def owl():
    # 远处猫头鹰：“咕——咕咕”
    out = []
    for f, d in [(390, 0.5), (0, 0.12), (370, 0.22), (0, 0.06), (370, 0.32)]:
        t = tt(d)
        if f == 0: out.append(np.zeros(len(t))); continue
        fr = f * (1 + 0.06 * np.sin(np.pi * t / d)); s = np.sin(ph(fr)) + 0.25 * np.sin(ph(fr * 2))
        out.append(lp(s, 900) * np.sin(np.pi * t / d) ** 1.3 * 0.35)
    return np.concatenate(out)
def nightbed(d=6.0):
    # 夜里的底：远处几只蟋蟀（不同音高、不同节奏）+ 很低的空调声
    t = tt(d); out = lp(rng.standard_normal(len(t)), 180) * 0.12
    for k, (fc, per) in enumerate([(3800, 0.9), (4700, 1.3), (4200, 0.7)]):
        car = np.sin(2 * np.pi * fc * t); q = (t + k * 0.31) % per
        gate = lp(((q < 0.16) & ((q % 0.045) < 0.02)).astype(float), 300)
        out += car * gate * 0.07
    return out * np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.8)
def streetbed(d=4.0):
    # 街上的底：远处车流一阵一阵
    t = tt(d); x = lp(rng.standard_normal(len(t)), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 2.7) ** 2)
    hiss = bp(rng.standard_normal(len(t)), 2000, 6000) * 0.04
    return (x * 0.35 + hiss) * np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.5)
def roomtone(d=8.0):
    # 剧场里的底：很低的空气声 + 一点点人在座位上动的窸窣
    t = tt(d); x = lp(rng.standard_normal(len(t)), 260) * 0.18
    for _ in range(int(d * 1.2)):
        L = 0.15 + rng.random() * 0.3; n = int(L * SR); s = bp(rng.standard_normal(n), 800, 3000) * np.sin(np.pi * np.arange(n) / n) * 0.05
        i = int(rng.random() * (d - L) * SR); x[i:i + n] += s
    return x * np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.5)
def yawn():
    # 打哈欠：“啊——”往下滑，带气声
    t = tt(1.1); f0 = 210 - 90 * (t / 1.1); g = saw(f0) * 0.6 + rng.standard_normal(len(t)) * 0.25
    return formants(g, [(780, 1.0), (1250, 0.6), (2600, 0.25)]) * np.sin(np.pi * t / 1.1) ** 1.2 * 0.6
def sigh():
    # 松一口气：“呼——”
    t = tt(0.8); n = rng.standard_normal(len(t)); return formants(n, [(600, 1), (1100, 0.5)], 1.6) * np.sin(np.pi * t / 0.8) ** 1.5 * np.exp(-t * 0.8) * 0.8
def blip(f=1.0):
    # 路人手机的提示音：每个人不一样
    return mx(bell(1320 * f, 0.4, 0.3) * 0.4, np.concatenate([np.zeros(int(0.08 * SR)), bell(1760 * f, 0.5, 0.3) * 0.35]))
def harp(f=262):
    return lp(ks(f, 2.2, 0.55, 0.998), 5000) * 0.9
def pad(fs=(131, 165, 196, 247, 294), d=2.6):
    # 暖和弦：几把微微走音的锯齿，慢起慢收
    t = tt(d); s = sum(saw(np.full(len(t), f * (1 + dt))) for f in fs for dt in (-0.004, 0.004)) / (len(fs) * 2)
    return lp(s, 1400) * np.minimum(1, t / 0.6) * np.minimum(1, (d - t) / 0.9) * 0.6
def punch():
    # 检票钳打孔：咔、嚓
    t = tt(0.25); c1 = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 200) * 0.7
    c2 = np.concatenate([np.zeros(int(0.06 * SR)), bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 80) * 0.5])
    return mx(c1, c2, np.sin(2 * np.pi * 900 * t) * np.exp(-t * 90) * 0.2)
def snorew(d=2.4):
    # 呼噜 + 呼气时的小口哨
    t = tt(d); base = snore(d); q = (t % (d / 2)) / (d / 2)
    w = np.sin(ph(1400 + 300 * np.sin(np.pi * q))) * 0.06 * (q > 0.6) * np.sin(np.pi * q)
    return base + w

SOUNDS2 = {
    'snare': lambda e: (snare(1.0), 0.6, 0.3),
    'drumroll': lambda e: (drumroll(e.get('d', 2.4)), 0.55, 0.35),
    'crash': lambda e: (crash(e.get('d', 2.6)), 0.45, 0.5),
    'whisper': lambda e: (whisper(e.get('d', 4.0), e.get('n', 4)), 0.55, 0.45),
    'plip': lambda e: (plip(e.get('f', 1.0)), 0.4, 0.4),
    'glock': lambda e: (glock(e.get('f', 1568)), 0.45, 0.55),
    'glockrun': lambda e: (glock_run(tuple(e.get('notes', (1047, 1319, 1568, 2093)))), 0.45, 0.55),
    'flick': lambda e: (flick(), 0.7, 0.4),
    'buzzer': lambda e: (buzzer(e.get('d', 0.5)), 0.5, 0.25),
    'tromb': lambda e: (tromb(), 0.6, 0.4),
    'slide': lambda e: (slide(e.get('up', True), e.get('d', 0.55)), 0.45, 0.3),
    'cloth': lambda e: (cloth(e.get('d', 0.35)), 0.5, 0.2),
    'woodstep': lambda e: (woodstep(e.get('d', 1.6), e.get('rate', 3.2), e.get('f', 1.0)), 0.55, 0.3),
    'bassline': lambda e: (bassline(), 0.6, 0.3),
    'ticktock': lambda e: (tick_tock(e.get('d', 6.0)), 0.5, 0.45),
    'owl': lambda e: (owl(), 0.45, 0.7),
    'nightbed': lambda e: (nightbed(e.get('d', 6.0)), 0.6, 0.5),
    'streetbed': lambda e: (streetbed(e.get('d', 4.0)), 0.6, 0.4),
    'roomtone': lambda e: (roomtone(e.get('d', 8.0)), 0.6, 0.5),
    'yawn': lambda e: (yawn(), 0.5, 0.35),
    'sigh': lambda e: (sigh(), 0.55, 0.35),
    'blip': lambda e: (blip(e.get('f', 1.0)), 0.4, 0.3),
    'harp': lambda e: (harp(e.get('f', 262)), 0.55, 0.6),
    'pad': lambda e: (pad(tuple(e.get('fs', (131, 165, 196, 247, 294))), e.get('d', 2.6)), 0.5, 0.6),
    'punch': lambda e: (punch(), 0.6, 0.25),
    'snorew': lambda e: (snorew(e.get('d', 2.4)), 0.55, 0.3),
}
# 这些是有音高/节奏的，不做随机变调
NOVARY = {'drumroll', 'tromb', 'bassline', 'harp', 'pad', 'glockrun', 'ticktock', 'nightbed', 'streetbed', 'roomtone', 'whisper', 'murmur', 'crickets', 'glock', 'chime'}
