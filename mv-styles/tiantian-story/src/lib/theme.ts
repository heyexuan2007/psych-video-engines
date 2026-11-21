import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";
import { easeInOut, mix } from "./util";

export const SERIF = "MVSerif";
export const SANS = "MVSans";

loadFont({ family: SERIF, url: staticFile("serif.ttf"), weight: "200 900" });
loadFont({ family: SANS, url: staticFile("sans.ttf"), weight: "100 900" });

/** Sky + mood palette. The whole MV is one day: morning → rain → dusk → night → dawn. */
export type Mood = {
  top: string;
  mid: string;
  low: string;
  sun: string; // sun / main light colour
  city: string; // building silhouette
  win: string; // lit window colour
  text: string;
  accent: string;
  night: number; // 0 day … 1 night (window lights, stars)
  rain: number; // 0 … 1
};

const M = (m: Mood) => m;
export const MOODS = {
  dawn: M({ top: "#2b3c6e", mid: "#c77f8c", low: "#f6c08a", sun: "#ffd9a0", city: "#2a2440", win: "#ffd58a", text: "#fffaf2", accent: "#ffd27a", night: 0.35, rain: 0 }),
  sunny: M({ top: "#3d7fc4", mid: "#8fc3e6", low: "#f7e2b8", sun: "#fff1c4", city: "#3b4a6b", win: "#fff2c0", text: "#ffffff", accent: "#ffd45e", night: 0, rain: 0 }),
  rain: M({ top: "#2e3f55", mid: "#56697f", low: "#8d98a3", sun: "#d8e2ec", city: "#232f3f", win: "#ffd890", text: "#ffffff", accent: "#ffcf7a", night: 0.25, rain: 1 }),
  gold: M({ top: "#3a3a72", mid: "#d98b5f", low: "#f7c46c", sun: "#ffe0a0", city: "#2b2342", win: "#ffd27a", text: "#fffaf0", accent: "#ffe08a", night: 0.3, rain: 0 }),
  dusk: M({ top: "#1f2152", mid: "#a2466c", low: "#f08a5d", sun: "#ffb37a", city: "#1a1630", win: "#ffc46b", text: "#ffffff", accent: "#ffb0c8", night: 0.6, rain: 0 }),
  night: M({ top: "#070b1e", mid: "#17224a", low: "#3a3168", sun: "#9fb6ff", city: "#0c1024", win: "#ffcf73", text: "#ffffff", accent: "#ffcf73", night: 1, rain: 0.8 }),
  neon: M({ top: "#0b0620", mid: "#2b0f45", low: "#7a1f5e", sun: "#ff7ab8", city: "#0e0a1e", win: "#7fe3ff", text: "#ffffff", accent: "#ff8cc6", night: 1, rain: 0 }),
  late: M({ top: "#05040f", mid: "#1d0b2e", low: "#5a1a4a", sun: "#ff9a7a", city: "#0a0716", win: "#ffb36b", text: "#ffffff", accent: "#ff9bb8", night: 1, rain: 0.2 }),
};
export type MoodName = keyof typeof MOODS;

/** [time, mood] keys; the sky blends between neighbours over `blend` seconds before each key. */
const KEYS: [number, MoodName][] = [
  [0, "dawn"],
  [8, "sunny"],
  [18.8, "rain"],
  [46.2, "gold"],
  [65.9, "dusk"],
  [101.2, "night"],
  [152.9, "neon"],
  [188.7, "late"],
  [230, "late"],
  [246, "dawn"],
];

export const moodAt = (t: number): Mood => {
  let i = 0;
  while (i + 1 < KEYS.length && KEYS[i + 1][0] <= t) i++;
  const [t0, a] = KEYS[i];
  const next = KEYS[i + 1];
  if (!next) return MOODS[a];
  const [t1, b] = next;
  const blend = Math.min(4, (t1 - t0) * 0.5);
  const p = easeInOut((t - (t1 - blend)) / blend);
  if (p <= 0) return MOODS[a];
  const A = MOODS[a];
  const B = MOODS[b];
  const o = {} as Mood;
  (Object.keys(A) as (keyof Mood)[]).forEach((k) => {
    const va = A[k];
    const vb = B[k];
    (o as Record<string, unknown>)[k] = typeof va === "number" ? va + ((vb as number) - va) * p : mix(va as string, vb as string, p);
  });
  return o;
};
