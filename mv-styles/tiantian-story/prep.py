"""Build src/data/lyrics.json (from word-timed LRC) and src/data/audio.json (energy/pulse) for the Remotion MV."""
import json, re, subprocess, sys
import numpy as np

LRC, MP3, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DUR = 258.85

def ts(m): return int(m[0]) * 60 + float(m[1])

lines = []
for raw in open(LRC, encoding="utf-8-sig"):
    m = re.match(r"\[(\d+):(\d+\.\d+)\](.*)", raw.strip())
    if not m: continue
    body = m.group(3)
    toks = re.findall(r"<(\d+):(\d+\.\d+)>([^<]*)", body)
    if not toks: continue
    chars = [{"c": c, "s": ts((a, b))} for a, b, c in toks if c != ""]
    lines.append({"start": ts(m.group(1, 2)), "chars": chars})
for i, l in enumerate(lines):
    nxt = lines[i + 1]["start"] if i + 1 < len(lines) else DUR
    cs = l["chars"]
    for k, c in enumerate(cs):
        c["e"] = cs[k + 1]["s"] if k + 1 < len(cs) else min(c["s"] + 0.7, nxt - 0.05)
    l["start"] = cs[0]["s"]
    l["end"] = cs[-1]["e"]
    l["text"] = "".join(c["c"] if not re.match(r"[A-Za-z]", c["c"]) else " " + c["c"] for c in cs).strip()
# repeat count per text -> chorus hint
cnt = {}
for l in lines: cnt[l["text"]] = cnt.get(l["text"], 0) + 1
for l in lines: l["rep"] = cnt[l["text"]]
json.dump({"lines": lines}, open(f"{OUT}/lyrics.json", "w", encoding="utf-8"), ensure_ascii=False)

# audio analysis @30fps
SR, FPS = 22050, 30
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", MP3, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(pcm, dtype=np.float32)
hop = SR // FPS
n = len(x) // hop
fr = x[: n * hop].reshape(n, hop)
rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms)
lo, hi = np.percentile(db, 5), np.percentile(db, 98)
energy = np.clip((db - lo) / (hi - lo), 0, 1)
energy = np.convolve(energy, np.ones(9) / 9, mode="same")
# low-band onset flux for beat pulses
win = 1024
spec = []
for i in range(n):
    seg = x[i * hop: i * hop + win]
    if len(seg) < win: seg = np.pad(seg, (0, win - len(seg)))
    spec.append(np.abs(np.fft.rfft(seg * np.hanning(win)))[:24])  # < ~500Hz
spec = np.log1p(np.array(spec) * 10)
flux = np.maximum(0, np.diff(spec, axis=0, prepend=spec[:1])).sum(1)
flux = flux / (np.percentile(flux, 99) + 1e-9)
thr = np.convolve(flux, np.ones(31) / 31, mode="same") * 1.4 + 0.08
peaks = [i for i in range(1, n - 1) if flux[i] > thr[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
keep, last = [], -99
for p in peaks:
    if p - last >= 7: keep.append(p); last = p
pulse = np.zeros(n)
for p in keep:
    a = min(1.0, flux[p])
    for k in range(0, 12):
        if p + k < n: pulse[p + k] = max(pulse[p + k], a * np.exp(-k / 3.5))
json.dump({"fps": FPS, "energy": [round(float(v), 3) for v in energy], "pulse": [round(float(v), 3) for v in pulse]},
          open(f"{OUT}/audio.json", "w"))
print("lines", len(lines), "frames", n, "beats", len(keep), "mean energy", round(float(energy.mean()), 3))
print("chorus-ish repeated lines:", sum(1 for l in lines if l["rep"] >= 3))
first = next(i for i in range(n) if energy[i] > 0.25)
print("first sound at", round(first / FPS, 2), "s; first lyric at", lines[0]["start"])
