# ================= 服从权威这一期专门做的音色：1961 年的实验室 + 老放映机 + 今天的手机 =================
# 被 mix.py 用 exec 读进来，共用 mix.py / sfx_stage.py 里的 tt / ph / lp / hp / bp / mx / att / rng / SR / saw / formants / env_adsr
def noise(n): return rng.standard_normal(n)

def projector(d=35.0):
    # 老放映机：24 格/秒的齿轮咔哒 + 马达低嗡 + 轻微的抖
    n = int(d * SR); t = np.arange(n) / SR
    hum = (np.sin(ph(np.full(n, 58.0))) * 0.25 + np.sin(ph(np.full(n, 116.0))) * 0.12) * (1 + 0.08 * np.sin(2 * np.pi * 0.7 * t))
    clk = np.zeros(n); k = int(SR / 24); burst = hp(noise(240), 2500) * np.exp(-np.arange(240) / SR * 900)
    for i in range(0, n - 240, k):
        clk[i:i + 240] += burst * (0.6 + 0.4 * ((i // k) % 2))
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.3)
    return (lp(hum, 400) * 0.5 + bp(clk, 1500, 6000) * 0.35 + lp(noise(n), 3000) * 0.015) * fade

def labtone(d=6.0):
    # 实验室：日光灯 120 Hz 嗡 + 空调风
    n = int(d * SR); t = np.arange(n) / SR
    s = np.sin(ph(np.full(n, 120.0))) * 0.05 + np.sin(ph(np.full(n, 240.0))) * 0.025 + lp(noise(n), 500) * 0.06
    return s * np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.25)

def toggle():
    # 拨杆：金属“咔-嗒”两下
    t = tt(0.09); a = bp(noise(len(t)), 1800, 7000) * np.exp(-t * 160) + np.sin(ph(np.full(len(t), 2600.0))) * np.exp(-t * 120) * 0.3
    out = np.zeros(int(0.14 * SR)); out[:len(a)] += a; j = int(0.04 * SR); out[j:j + len(a)] += a * 0.55
    return out * 0.9

def zap(d=0.35, f=1.0):
    # 电流：60 Hz 方波嗡 + 高频嗞嗞，越往后的开关越长越响
    n = int(d * SR); t = np.arange(n) / SR
    b = np.sign(np.sin(ph(np.full(n, 60.0 * f)))) * 0.25 + saw(np.full(n, 120.0 * f)) * 0.2
    crack = bp(noise(n), 3000, 9000) * (0.5 + 0.5 * (rng.random(n) > 0.97)) * 0.35
    env = np.minimum(1, t / 0.01) * np.exp(-t * (3 / d))
    return lp(b + crack, 6000) * env * 0.8

def yell(muffle=0):
    # 隔壁的喊叫（合成的“啊——”元音，滑音往上，墙后会闷掉）
    d = 0.9; n = int(d * SR); t = np.arange(n) / SR
    f0 = 260 + 120 * np.sin(np.pi * t / d) + 8 * np.sin(2 * np.pi * 6 * t)
    src = saw(f0) * 0.6 + noise(n) * 0.04
    v = formants(src, [(800, 1.0), (1200, 0.7), (2600, 0.3)], 1.2)
    env = np.minimum(1, t / 0.04) * np.minimum(1, (d - t) / 0.25)
    v = v * env
    v = lp(v, 900 if muffle else 1500)        # 墙后：高频没了
    return np.tanh(v * 3) * 0.6

def thump():
    # 拍墙的闷响
    t = tt(0.25); return (np.sin(ph(70 + 60 * np.exp(-t * 30))) * np.exp(-t * 18) + lp(noise(len(t)), 400) * np.exp(-t * 30) * 0.5) * 0.9

def pen():
    # 白大褂在夹板上记一笔
    t = tt(0.35); return bp(noise(len(t)), 2500, 6000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 9 * t))) * np.minimum(1, (0.35 - t) / 0.1) * 0.25

def jam():
    # 胶片卡住：放映机咔哒突然变慢 + 一声“嘣”
    out = np.zeros(int(0.7 * SR)); burst = hp(noise(300), 1500) * np.exp(-np.arange(300) / SR * 600)
    pos = 0.0; gap = 1 / 24
    while pos < 0.5: i = int(pos * SR); out[i:i + 300] += burst * 0.8; pos += gap; gap *= 1.35
    t = tt(0.3); out[:len(t)] += np.sin(ph(120 + 200 * np.exp(-t * 25))) * np.exp(-t * 12) * 0.6
    return out

def splice():
    # 胶片接头过片门：“嚓啪”
    t = tt(0.16); return (bp(noise(len(t)), 800, 6000) * np.exp(-t * 40) + np.sin(ph(np.full(len(t), 180.0))) * np.exp(-t * 50) * 0.4) * 0.8

def papertone(d=6.0):
    n = int(d * SR); t = np.arange(n) / SR
    return lp(noise(n), 700) * 0.05 * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.2)

def woodtap(f=1.0):
    t = tt(0.12); return (np.sin(ph(np.full(len(t), 520.0 * f))) * np.exp(-t * 45) + bp(noise(len(t)), 600, 2500) * np.exp(-t * 80) * 0.4) * 0.7

def chuckle():
    # 专家们“呵呵”的轻笑（三声短元音）
    out = np.zeros(int(0.8 * SR))
    for k in range(3):
        d = 0.13; n = int(d * SR); t = np.arange(n) / SR
        v = formants(saw(np.full(n, 150.0 - k * 6)) + noise(n) * 0.3, [(600, 1.0), (1000, 0.5)], 1.4) * np.sin(np.pi * t / d) ** 2
        i = int(k * 0.2 * SR); out[i:i + n] += v
    return np.tanh(out * 3) * 0.4

def typekey():
    # 打字机一键
    t = tt(0.07); return (bp(noise(len(t)), 1500, 5000) * np.exp(-t * 120) + np.sin(ph(np.full(len(t), 1100.0))) * np.exp(-t * 90) * 0.2) * 0.8

def tickzap(f=1.0):
    t = tt(0.07); return (bp(noise(len(t)), 3000, 8000) * np.exp(-t * 70) * 0.5 + np.sign(np.sin(ph(np.full(len(t), 120.0 * f)))) * np.exp(-t * 60) * 0.15)

def slam():
    # 65% 砸下来：低鼓 + 纸板拍
    t = tt(0.7); return (np.sin(ph(48 + 90 * np.exp(-t * 18))) * np.exp(-t * 5) + bp(noise(len(t)), 300, 3000) * np.exp(-t * 35) * 0.5) * 1.0

def scratchpen(d=0.25):
    t = tt(d); return bp(noise(len(t)), 1800, 7000) * np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.05) * 0.6

def pulley(d=0.7):
    # 墙升起来：滑轮吱呀 + 绳子
    n = int(d * SR); t = np.arange(n) / SR
    sq = saw(700 + 300 * np.sin(np.pi * t / d) + 40 * np.sin(2 * np.pi * 13 * t)) * 0.12
    return (bp(sq, 600, 3000) + lp(noise(n), 900) * 0.2) * np.sin(np.pi * t / d) ** 0.5

def reel(d=4.0):
    # 盘式录音机：磁带转动的沙沙声 + 马达
    n = int(d * SR); t = np.arange(n) / SR
    return (bp(noise(n), 2000, 7000) * 0.05 + np.sin(ph(np.full(n, 90.0))) * 0.06 * (1 + 0.3 * np.sin(2 * np.pi * 2.2 * t))) * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.3)

def rustle():
    t = tt(0.5); return bp(noise(len(t)), 900, 6000) * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 7 * t))) * np.sin(np.pi * t / 0.5) * 0.4

def nervlaugh():
    # 紧张的干笑：“嘿…嘿嘿”，发颤
    out = np.zeros(int(1.0 * SR))
    for k, (st, f) in enumerate([(0.0, 230), (0.32, 245), (0.5, 250)]):
        d = 0.15; n = int(d * SR); t = np.arange(n) / SR
        v = formants(saw(f + 15 * np.sin(2 * np.pi * 11 * t)) + noise(n) * 0.5, [(500, 1.0), (1700, 0.6)], 1.3) * np.sin(np.pi * t / d) ** 2
        i = int(st * SR); out[i:i + n] += v
    return np.tanh(out * 3) * 0.45

def pat():
    # 拍肩：布料上的两下闷拍
    out = np.zeros(int(0.45 * SR)); t = tt(0.1); a = lp(noise(len(t)), 1500) * np.exp(-t * 60)
    for st in (0.0, 0.22): i = int(st * SR); out[i:i + len(a)] += a
    return out * 0.9

def zoomin(d=0.5):
    # 冲进红灯：上滑的电流嗡
    n = int(d * SR); t = np.arange(n) / SR
    s = saw(80 * 2 ** (3 * t / d)) * 0.3 + bp(noise(n), 2000, 8000) * 0.1
    return lp(s, 5000) * (t / d) ** 1.5

def nightroom(d=3.0):
    # 深夜房间：冰箱低嗡
    n = int(d * SR); t = np.arange(n) / SR
    return (np.sin(ph(np.full(n, 50.0))) * 0.05 + lp(noise(n), 300) * 0.05) * np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.2)

def slideup():
    t = tt(0.3); return bp(noise(len(t)), 500, 3000) * np.sin(np.pi * t / 0.3) * 0.3

def phonevoice(d=2.4):
    # 电话那头的“警察”：不清楚的说话声（合成音节 + 电话带宽）
    n = int(d * SR); out = np.zeros(n); pos = 0.0
    while pos < d - 0.2:
        sd = 0.08 + rng.random() * 0.12; m = int(sd * SR); t = np.arange(m) / SR
        f0 = 120 + rng.random() * 30
        fs = [(400 + rng.random() * 500, 1.0), (1100 + rng.random() * 900, 0.6)]
        v = formants(saw(np.full(m, f0)) + noise(m) * 0.2, fs, 1.0) * np.sin(np.pi * t / sd) ** 2
        i = int(pos * SR); out[i:i + m] += v[: n - i]; pos += sd + (0.03 if rng.random() < 0.8 else 0.18)
    return np.tanh(bp(out, 350, 3200) * 3) * 0.35

def msg(f=1.0):
    t = tt(0.25); return (np.sin(ph(np.full(len(t), 1320.0 * f))) * np.exp(-t * 18) * 0.4 + np.sin(ph(np.full(len(t), 1980.0 * f))) * np.exp(-t * 25) * 0.2)

def shopbed(d=2.7):
    # 直播间：快节奏的小电子鼓点 + 远处叫卖人声
    n = int(d * SR); out = np.zeros(n); beat = 60 / 132
    k = 0; pos = 0.0
    while pos < d:
        i = int(pos * SR); t = tt(0.15)
        kick = np.sin(ph(60 + 100 * np.exp(-t * 40))) * np.exp(-t * 20) * 0.6
        hat = hp(noise(len(t)), 7000) * np.exp(-t * 80) * 0.15
        s = kick if k % 2 == 0 else hat
        out[i:i + len(s)] += s[: n - i]; pos += beat / 2; k += 1
    out += phonevoice(d) * 0.6
    t = np.arange(n) / SR
    return out * np.minimum(1, t / 0.1) * np.minimum(1, (d - t) / 0.2)

def ding(f=1.0):
    t = tt(0.5); return (np.sin(ph(np.full(len(t), 1568.0 * f))) + 0.4 * np.sin(ph(np.full(len(t), 3136.0 * f)))) * np.exp(-t * 9) * 0.35

def chairscrape(f=1.0):
    d = 0.4; n = int(d * SR); t = np.arange(n) / SR
    s = saw(180 * f + 60 * np.sin(np.pi * t / d)) * 0.25 + bp(noise(n), 400, 2000) * 0.2
    return lp(s, 2500) * np.sin(np.pi * t / d) ** 0.7

def counter(d=0.7):
    # 数字往下滚：越来越慢的机械翻牌声
    out = np.zeros(int((d + 0.1) * SR)); pos = 0.0; gap = 0.03; burst = bp(noise(400), 1500, 6000) * np.exp(-np.arange(400) / SR * 500)
    while pos < d: i = int(pos * SR); out[i:i + 400] += burst * 0.6; pos += gap; gap *= 1.12
    return out

def settledown():
    # 10% 落定：低沉的定音 + 一点余音
    t = tt(2.0); return (np.sin(ph(np.full(len(t), 65.0))) * 0.7 + np.sin(ph(np.full(len(t), 98.0))) * 0.35 + np.sin(ph(np.full(len(t), 196.0))) * 0.15) * np.exp(-t * 1.6) * att(t, 0.01)

def runout(d=0.5):
    # 片尾：胶片跑完，“哒哒哒”空转
    out = np.zeros(int((d + 0.1) * SR)); pos = 0.0; burst = hp(noise(240), 2000) * np.exp(-np.arange(240) / SR * 800)
    while pos < d: i = int(pos * SR); out[i:i + 240] += burst; pos += 1 / 24
    return out * 0.5

SOUNDS3 = {
    'projector': lambda e: (projector(e.get('d', 35.0)), 0.5, 0.15),
    'labtone': lambda e: (labtone(e.get('d', 6.0)), 0.6, 0.3),
    'toggle': lambda e: (toggle(), 0.75, 0.25),
    'zap': lambda e: (zap(e.get('d', 0.35), e.get('f', 1.0)), 0.5, 0.3),
    'yell': lambda e: (yell(e.get('muffle', 0)), 0.6, 0.5),
    'thump': lambda e: (thump(), 0.6, 0.4),
    'pen': lambda e: (pen(), 0.5, 0.2),
    'jam': lambda e: (jam(), 0.7, 0.3),
    'splice': lambda e: (splice(), 0.6, 0.2),
    'papertone': lambda e: (papertone(e.get('d', 6.0)), 0.6, 0.2),
    'woodtap': lambda e: (woodtap(e.get('f', 1.0)), 0.6, 0.3),
    'chuckle': lambda e: (chuckle(), 0.5, 0.35),
    'type': lambda e: (typekey(), 0.5, 0.2),
    'tickzap': lambda e: (tickzap(e.get('f', 1.0)), 0.5, 0.2),
    'slam': lambda e: (slam(), 0.7, 0.45),
    'scratchpen': lambda e: (scratchpen(e.get('d', 0.25)), 0.5, 0.2),
    'pulley': lambda e: (pulley(e.get('d', 0.7)), 0.6, 0.35),
    'reel': lambda e: (reel(e.get('d', 4.0)), 0.6, 0.2),
    'rustle': lambda e: (rustle(), 0.5, 0.2),
    'nervlaugh': lambda e: (nervlaugh(), 0.6, 0.3),
    'pat': lambda e: (pat(), 0.6, 0.2),
    'zoomin': lambda e: (zoomin(e.get('d', 0.5)), 0.5, 0.3),
    'nightroom': lambda e: (nightroom(e.get('d', 3.0)), 0.6, 0.2),
    'slideup': lambda e: (slideup(), 0.5, 0.2),
    'phonevoice': lambda e: (phonevoice(e.get('d', 2.4)), 0.6, 0.1),
    'msg': lambda e: (msg(e.get('f', 1.0)), 0.5, 0.3),
    'shopbed': lambda e: (shopbed(e.get('d', 2.7)), 0.55, 0.2),
    'ding': lambda e: (ding(e.get('f', 1.0)), 0.5, 0.35),
    'chairscrape': lambda e: (chairscrape(e.get('f', 1.0)), 0.55, 0.3),
    'counter': lambda e: (counter(e.get('d', 0.7)), 0.6, 0.25),
    'settledown': lambda e: (settledown(), 0.6, 0.55),
    'runout': lambda e: (runout(e.get('d', 0.5)), 0.6, 0.2),
}
NOVARY |= {'projector', 'labtone', 'papertone', 'reel', 'nightroom', 'phonevoice', 'shopbed', 'settledown'}
