# 音效轨：读 events.json（画面里 ev() 登记的事件），合成神秘塔罗片的音效（牌、颂钵、星盘、羽毛笔、旧书）；不加 BGM（用户自己配），不配音
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


# ---------------- 基础音色 ----------------
def bell(f, d=2.2, bright=1.0):
    t = tt(d)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.35 * bright * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 4)
         + 0.18 * bright * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 7) + 0.08 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 11))
    return s * att(t, 0.003)


exec(open(os.path.join(HERE, 'tools', 'sounds.py'), encoding='utf-8').read())
unknown = set()
for e in EVF['ev']:
    if e['s'] == 'cue': continue
    fn = SOUNDS.get(e['s'])
    if not fn: unknown.add(e['s']); continue
    sig, g, wet = fn(e)
    v = e.get('vary', 0.0 if e['s'] in NOVARY else 0.05)
    if v > 0:   # 每次触发略微变一下音高
        r = 1 + (rng.random() * 2 - 1) * v
        sig = np.interp(np.arange(0, len(sig) - 1, r), np.arange(len(sig)), sig)
    add(sig, e['t'], g * e.get('g', 1.0), e.get('pan', 0.0), wet)
if unknown: print('未映射的事件:', unknown)

# 混响：指数衰减的噪声脉冲
ir_t = tt(2.6); ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t * 2.4)
ir = np.stack([lp(ir[0], 5000), lp(ir[1], 5000)]) * 0.06
mix = DRY + np.stack([fftconvolve(WET[c], ir[c])[:N] for c in range(2)])
pk = np.abs(mix).max()
mix = np.tanh(mix / pk * 1.1) / np.tanh(1.1) * 10 ** (-3 / 20)
# 按响度对齐到约 -16.5 LUFS（用 ffmpeg 的 ebur128 量），再用软限幅把峰值压在 -1.2 dBFS 以下
import subprocess, tempfile, re
def lufs_of(x):
    f = os.path.join(tempfile.gettempdir(), 'barnum_lufs.wav'); sf.write(f, x.T.astype(np.float32), SR)
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
