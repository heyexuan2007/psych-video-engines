# ---------------- 音色（这一期新做：牌、颂钵、星盘齿轮、羽毛笔、月相风铃、旧书、牌海） ----------------
# 被 mix.py exec 进来，用的是 mix.py 里的 tt / mx / lp / hp / bp / ph / att / bell / rng / SR

def murmur(d=4.0):
    # 教室里的窃窃私语
    t = tt(d); out = np.zeros(len(t))
    for k in range(5):
        lo = 250 + 120 * k; x = bp(rng.standard_normal(len(t)), lo, lo * 2.4)
        env_ = np.clip(np.sin(2 * np.pi * (0.6 + 0.37 * k) * t + k * 1.3) * 0.5 + 0.5, 0, 1) ** 3
        out += x * env_
    return out * 0.32 * np.sin(np.pi * np.minimum(1, t / d)) ** 0.5 * np.minimum(1, t / 0.4)

def partials(f, d, ratios, decays, amps, beat=0.0):
    t = tt(d); s = np.zeros(len(t))
    for r, dc, a in zip(ratios, decays, amps):
        s += a * np.sin(2 * np.pi * f * r * t + beat * np.sin(2 * np.pi * 3.1 * t)) * np.exp(-t * dc)
    return s * att(t, 0.004)

def bowl(f=196, d=5.0):
    # 颂钵：非整数泛音 + 慢慢的拍频起伏
    s = partials(f, d, [1, 2.71, 5.12, 8.2], [0.55, 0.9, 1.6, 2.6], [1, 0.55, 0.25, 0.1], beat=0.6)
    t = tt(d); s *= 1 + 0.18 * np.sin(2 * np.pi * 4.3 * t) * np.exp(-t * 0.4)
    n = int(0.02 * SR); hit = lp(rng.standard_normal(n), 2500) * np.exp(-tt(0.02) * 200) * 0.3
    return mx(s * 0.5, hit)

def gong(d=5.5):
    # 低锣：低频主音 + 慢慢长起来的金属沙声
    t = tt(d); f0 = 82
    body = partials(f0, d, [1, 1.52, 2.03, 2.71, 3.6], [0.6, 0.9, 1.1, 1.6, 2.2], [1, 0.6, 0.5, 0.35, 0.2])
    shim = hp(rng.standard_normal(len(t)), 2500) * (np.minimum(1, t / 0.6) * np.exp(-t * 1.1)) * 0.12
    return mx(body * 0.6, shim, bowl(f0 * 4.02, 3.0) * 0.15)

def cardflip():
    # 翻牌：硬卡纸“啪”一下 + 一点空气
    t = tt(0.16); snap = bp(rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t * 55) * att(t, 0.0006)
    body = np.sin(2 * np.pi * 230 * t) * np.exp(-t * 70) * 0.4
    a = tt(0.12); air_ = bp(rng.standard_normal(len(a)), 600, 3000) * np.sin(np.pi * a / 0.12) ** 2 * 0.25
    out = np.zeros(int(0.25 * SR)); out[:len(air_)] += air_; i = int(0.07 * SR); out[i:i + len(snap)] += snap + body
    return out

def deal():
    # 发牌：牌面擦过的“嘶”，结尾轻轻落下
    d = 0.22; t = tt(d); x = bp(rng.standard_normal(len(t)), 2000, 9000) * np.sin(np.pi * t / d) ** 1.5 * 0.5
    l = tt(0.03); land = lp(rng.standard_normal(len(l)), 1800) * np.exp(-l * 120) * 0.4
    out = np.zeros(int(0.27 * SR)); out[:len(x)] += x; i = int(0.2 * SR); out[i:i + len(land)] += land
    return out

def riffle(d=0.9):
    # 洗牌：一串越来越密的小“咔”
    out = np.zeros(int((d + 0.3) * SR)); t0 = 0.0
    while t0 < d:
        c = cardflip()[int(0.07 * SR):int(0.11 * SR)] * (0.35 + 0.3 * rng.random())
        i = int(t0 * SR); out[i:i + len(c)] += c[:len(out) - i]
        t0 += 0.045 * (1 - 0.6 * t0 / d) + 0.006 * rng.random()
    return out

def quill(d=0.45):
    # 羽毛笔划一个勾：先短后长两笔
    out = np.zeros(int((d + 0.05) * SR))
    for a, b in [(0.0, 0.12), (0.14, d)]:
        t = tt(b - a); x = bp(rng.standard_normal(len(t)), 2500, 9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
        x *= np.sin(np.pi * t / (b - a)) ** 0.8 * 0.45; i = int(a * SR); out[i:i + len(x)] += x
    return out

def quillbed(d=2.6):
    # 39 个人一起写字
    out = np.zeros(int(d * SR))
    for k in range(70):
        q = quill(0.2 + 0.25 * rng.random()) * (0.15 + 0.15 * rng.random()); i = int(rng.random() * (d - 0.6) * SR)
        out[i:i + len(q)] += q[:len(out) - i]
    t = tt(d)
    return out[:len(t)] * np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.5)

def glint(f=1.0):
    # “说中了”亮起来：两颗高音水晶 + 一点颂钵尾巴
    return mx(bell(1760 * f, 1.4, 0.5) * 0.35, np.concatenate([np.zeros(int(0.06 * SR)), bell(2637 * f, 1.2, 0.4) * 0.25]), bowl(440 * f, 1.8) * 0.12)

def ratchet(d=1.5):
    # 星盘转动：黄铜齿轮的细碎咔哒 + 低低的转轴声
    out = np.zeros(int(d * SR)); n = int(d * 22)
    for k in range(n):
        tk = tt(0.02); c = (np.sin(2 * np.pi * 3100 * tk) + 0.6 * np.sin(2 * np.pi * 5200 * tk)) * np.exp(-tk * 400) * (0.25 + 0.15 * rng.random())
        i = int(k / n * d * SR); out[i:i + len(c)] += c[:len(out) - i]
    t = tt(d); hum = lp(rng.standard_normal(len(t)), 160) * 0.3
    return (out[:len(t)] + hum) * np.sin(np.pi * t / d) ** 0.6

def air(d=0.8, up=True):
    # 气流：比 whoosh 更软、更低的呼吸声
    t = tt(d); x = rng.standard_normal(len(t)); out = np.zeros(len(t)); blk = 1024
    for i in range(0, len(t), blk):
        p = i / len(t); fc = 220 + 1100 * (p if up else 1 - p)
        s_ = x[max(0, i - 4096):i + blk]; out[i:i + blk] = bp(s_, fc * 0.5, fc * 1.6)[-len(x[i:i + blk]):]
    return out * np.sin(np.pi * t / d) ** 2 * 0.8

def paperslip():
    t = tt(0.35); x = bp(rng.standard_normal(len(t)), 900, 6000) * np.exp(-((t - 0.12) / 0.07) ** 2) * 0.6
    l = tt(0.02); tap = lp(rng.standard_normal(len(l)), 1500) * np.exp(-l * 150) * 0.3
    out = x.copy(); i = int(0.25 * SR); out[i:i + len(tap)] += tap; return out

def chimes(d=1.6):
    # 月相一个个亮：七声风铃，往上走
    out = np.zeros(int((d + 1.6) * SR)); notes = [1175, 1319, 1480, 1568, 1760, 1976, 2349]
    for k, f in enumerate(notes):
        b = bell(f, 1.5, 0.6) * 0.2; i = int((k * 0.16 + 0.01 * rng.random()) * SR); out[i:i + len(b)] += b[:len(out) - i]
    return out

def paddles(d=1.6):
    # 学生一个个举牌：轻轻的木牌碰撞，散开的
    out = np.zeros(int((d + 0.2) * SR))
    for k in range(26):
        tk = tt(0.05); f = 600 + 400 * rng.random()
        c = (np.sin(2 * np.pi * f * tk) * 0.6 + lp(rng.standard_normal(len(tk)), 2500) * 0.4) * np.exp(-tk * 90) * (0.2 + 0.2 * rng.random())
        i = int(rng.random() * d * SR); out[i:i + len(c)] += c[:len(out) - i]
    return out

def counter(d=1.8):
    # 数字往上滚：越来越慢的小木轮咔哒，音高一点点升
    out = np.zeros(int((d + 0.2) * SR)); tk = 0.0
    while tk < d:
        p = tk / d; f = 900 + 900 * p; t0 = tt(0.03)
        c = np.sin(2 * np.pi * f * t0) * np.exp(-t0 * 160) * 0.35
        i = int(tk * SR); out[i:i + len(c)] += c[:len(out) - i]
        tk += 0.03 + 0.12 * p ** 2
    return out

def cascade(n=39, d=1.6):
    # 39 张牌一波翻开
    out = np.zeros(int((d + 0.4) * SR))
    for k in range(n):
        c = cardflip() * (0.25 + 0.15 * rng.random()); i = int((k / n) * d * SR + rng.random() * 0.02 * SR); out[i:i + len(c)] += c[:len(out) - i]
    return out

def revswell(d=0.5):
    t = tt(d); x = hp(rng.standard_normal(len(t)), 3000) * (t / d) ** 3 * 0.5
    return mx(x, bowl(392, d)[::-1] * 0.4)

def thud():
    t = tt(0.9); f = 55 * np.exp(-t * 3) + 38
    return mx(np.sin(ph(f)) * np.exp(-t * 4.5) * 0.9 * att(t, 0.002), lp(rng.standard_normal(len(t)), 300) * np.exp(-t * 18) * 0.4)

def choir(d=1.8):
    # 很轻的“啊”声垫底：锯齿波过元音共振峰
    t = tt(d); out = np.zeros(len(t))
    for f in (220, 277, 330, 440):
        v = 2 * ((f * t + 0.003 * np.sin(2 * np.pi * 5 * t)) % 1) - 1
        for fc, g in ((700, 1), (1220, 0.6), (2600, 0.25)): out += bp(v, fc * 0.9, fc * 1.1) * g
    return out * 0.18 * np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.8)

def bookdrop():
    t = tt(0.5); body = lp(rng.standard_normal(len(t)), 500) * np.exp(-t * 14) * 0.8
    dust = bp(rng.standard_normal(len(t)), 3000, 9000) * np.exp(-((t - 0.12) / 0.12) ** 2) * 0.15
    return body + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 12) * 0.5 + dust

def bookopen():
    # 旧书打开：书脊“吱”一声 + 一大张纸翻过去
    t = tt(0.45); f = 320 + 160 * np.sin(np.pi * t / 0.45)
    creak = np.sin(ph(f)) * (0.5 + 0.5 * np.sign(np.sin(ph(f * 0.11)))) * np.sin(np.pi * t / 0.45) * 0.12
    creak = bp(creak, 200, 2500)
    g = tt(0.6); pg = bp(rng.standard_normal(len(g)), 500, 5000) * np.sin(np.pi * g / 0.6) ** 2 * 0.45
    out = np.zeros(int(1.1 * SR)); out[:len(creak)] += creak; i = int(0.35 * SR); out[i:i + len(pg)] += pg
    return out

def marker(d=0.45):
    # 金色荧光笔划过：带一点玻璃感的摩擦
    t = tt(d); x = bp(rng.standard_normal(len(t)), 1500, 4500) * (0.7 + 0.3 * np.sin(2 * np.pi * 60 * t)) * np.sin(np.pi * t / d) * 0.4
    return mx(x, bell(2093 * (1 + 0.03 * rng.random()), 0.6, 0.3) * 0.05)

def flutter(d=1.8):
    # 牌海：成百上千张牌一起翻飞
    out = np.zeros(int((d + 0.4) * SR))
    for k in range(160):
        c = cardflip() * (0.08 + 0.1 * rng.random()); p = rng.random() ** 0.7; i = int(p * d * SR); out[i:i + len(c)] += c[:len(out) - i]
    t = tt(d + 0.4); wash = bp(rng.standard_normal(len(t)), 800, 6000) * np.sin(np.pi * t / (d + 0.4)) ** 2 * 0.12
    return out[:len(t)] + wash

def bed(d=39.0):
    # 环境底：烛火噼啪 + 很低的持续嗡声（两个五度，慢慢呼吸）+ 夜里的空气
    t = tt(d); n = len(t)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 0.4) + 0.25 * np.sin(2 * np.pi * 110.2 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 9.0)) * 0.11
    crack = np.zeros(n)
    for k in range(int(d * 2.2)):
        c = bp(rng.standard_normal(int(0.012 * SR)), 1500, 7000) * np.exp(-tt(0.012) * 300) * (0.05 + 0.12 * rng.random() ** 3)
        i = int(rng.random() * (n - len(c))); crack[i:i + len(c)] += c
    airn = lp(rng.standard_normal(n), 700) * 0.07 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 13))
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.6)
    return (drone + crack + airn) * fade

# 每次随机变调 ±5%；有音高、要和别的音对上的不变
NOVARY = {'bed', 'bowl', 'gong', 'chimes', 'counter', 'choir', 'revswell', 'glint', 'thud'}
SOUNDS = {
    'bed': lambda e: (bed(e.get('d', 39.0)), 0.9, 0.15),
    'bowl': lambda e: (bowl(e.get('f', 196)), 0.5, 0.6),
    'gong': lambda e: (gong(), 0.7, 0.55),
    'cardflip': lambda e: (cardflip(), 0.8, 0.25),
    'deal': lambda e: (deal(), 0.7, 0.2),
    'riffle': lambda e: (riffle(), 0.7, 0.25),
    'quill': lambda e: (quill(), 0.7, 0.2),
    'quillbed': lambda e: (quillbed(e.get('d', 2.6)), 0.6, 0.3),
    'glint': lambda e: (glint(e.get('f', 1.0)), 0.6, 0.6),
    'ratchet': lambda e: (ratchet(e.get('d', 1.5)), 0.5, 0.35),
    'air': lambda e: (air(e.get('d', 0.8), e.get('up', True)), 0.5, 0.4),
    'paperslip': lambda e: (paperslip(), 0.7, 0.25),
    'murmur': lambda e: (murmur(e.get('d', 4.0)), 0.5, 0.5),
    'chimes': lambda e: (chimes(e.get('d', 1.6)), 0.6, 0.65),
    'paddles': lambda e: (paddles(e.get('d', 1.6)), 0.6, 0.35),
    'counter': lambda e: (counter(e.get('d', 1.8)), 0.6, 0.3),
    'cascade': lambda e: (cascade(e.get('n', 39), e.get('d', 1.6)), 0.7, 0.35),
    'revswell': lambda e: (revswell(e.get('d', 0.5)), 0.6, 0.5),
    'thud': lambda e: (thud(), 0.8, 0.45),
    'choir': lambda e: (choir(e.get('d', 1.8)), 0.6, 0.7),
    'bookdrop': lambda e: (bookdrop(), 0.7, 0.35),
    'bookopen': lambda e: (bookopen(), 0.7, 0.35),
    'marker': lambda e: (marker(), 0.6, 0.25),
    'flutter': lambda e: (flutter(e.get('d', 1.8)), 0.7, 0.45),
}
