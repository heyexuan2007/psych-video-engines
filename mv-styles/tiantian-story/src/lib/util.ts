import audio from "../data/audio.json";
import lyrics from "../data/lyrics.json";

export const W = 1920;
export const H = 1080;
export const FPS = 30;
export const DURATION = 258.85;

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
export const prog = (t: number, a: number, b: number) => clamp01((t - a) / (b - a));
export const easeOut = (p: number) => 1 - Math.pow(1 - clamp01(p), 3);
export const easeIn = (p: number) => Math.pow(clamp01(p), 3);
export const easeInOut = (p: number) => {
  const x = clamp01(p);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
export const easeOutBack = (p: number, k = 1.9) => {
  const x = clamp01(p) - 1;
  return 1 + (k + 1) * x * x * x + k * x * x;
};
/** 0 -> 1 -> 0 window: fades in over `fi`, out over `fo`. */
export const win = (t: number, a: number, b: number, fi = 0.4, fo = 0.4) =>
  Math.min(easeOut(prog(t, a, a + fi)), 1 - easeIn(prog(t, b - fo, b)));

export const hash = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export type LChar = { c: string; s: number; e: number };
export type Line = { text: string; start: number; end: number; rep: number; chars: LChar[] };
/** seconds added to every lyric time (positive = later); the LRC is hand-timed, so 0 */
export const LYRIC_OFFSET = 0;
export const LINES: Line[] = (lyrics as { lines: Line[] }).lines.map((l) => ({
  ...l,
  start: l.start + LYRIC_OFFSET,
  end: l.end + LYRIC_OFFSET,
  chars: l.chars.map((c) => ({ ...c, s: c.s + LYRIC_OFFSET, e: c.e + LYRIC_OFFSET })),
}));

const A = audio as { fps: number; energy: number[]; pulse: number[] };
const at = (arr: number[], t: number) => arr[Math.max(0, Math.min(arr.length - 1, Math.round(t * A.fps)))] ?? 0;
export const energyAt = (t: number) => at(A.energy, t);
export const pulseAt = (t: number) => at(A.pulse, t);

/** Song structure (song seconds). Line indices are 0-based into LINES. */
export const SEC = {
  intro: [0, 16.4],
  v1: [16.4, 46.2],
  pre1: [46.2, 65.9],
  c1: [65.9, 101.2],
  v2: [101.2, 133.6],
  pre2: [133.6, 152.9],
  c2: [152.9, 188.7],
  c3: [188.7, 226.2],
  outro: [226.2, DURATION],
} as const;
export type SecName = keyof typeof SEC;
export const secAt = (t: number): SecName =>
  (Object.keys(SEC) as SecName[]).find((k) => t >= SEC[k][0] && t < SEC[k][1]) ?? "outro";

/** first line index of each chorus; chorus = 9 lines: traffic, crowd, grey, colour, want, share, say×3 */
export const CHORUS_STARTS = [10, 29, 38];
export const chorusRole = (i: number) => {
  for (const c of CHORUS_STARTS) if (i >= c && i < c + 9) return i - c;
  return -1;
};
export const isChorusLine = (i: number) => chorusRole(i) >= 0 || i >= 47;
/** span (with fades) of a line, by index */
export const lineSpan = (i: number) => [LINES[i].start, LINES[i].end] as const;

// colours
const hex = (c: string) => {
  const n = parseInt(c.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
export const mix = (a: string, b: string, p: number) => {
  const x = hex(a);
  const y = hex(b);
  const r = x.map((v, i) => Math.round(lerp(v, y[i], clamp01(p))));
  return "#" + r.map((v) => v.toString(16).padStart(2, "0")).join("");
};
export const rgba = (c: string, a: number) => {
  const [r, g, b] = hex(c);
  return `rgba(${r},${g},${b},${a})`;
};

/** strong beat times (seconds) from the pulse envelope */
export const BEATS: number[] = (() => {
  const out: number[] = [];
  const p = A.pulse;
  for (let i = 1; i < p.length - 1; i++) if (p[i] > 0.55 && p[i] >= p[i - 1] && p[i] > p[i + 1] && p[i - 1] < p[i]) out.push(i / A.fps);
  return out;
})();
/** beats in [a, b), keeping every `every`-th */
export const beatsIn = (a: number, b: number, every = 1) => BEATS.filter((x) => x >= a && x < b).filter((_, i) => i % every === 0);
