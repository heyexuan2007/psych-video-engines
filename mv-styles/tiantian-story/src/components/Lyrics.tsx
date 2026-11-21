import React from "react";
import { AbsoluteFill } from "remotion";
import { SANS, SERIF, moodAt } from "../lib/theme";
import { LINES, Line, chorusRole, clamp01, easeIn, easeOut, easeOutBack, hash, isChorusLine, lerp, pulseAt, rgba, secAt } from "../lib/util";

/* Safe zone (Douyin UI): x 7%–83%, y 11%–86% of 1920×1080 */
const SX0 = 150;
const SX1 = 1580;
const SY0 = 130;
const SY1 = 915;
const MAXW = SX1 - SX0 - 40;

type Layout = "center" | "left" | "right" | "tilt" | "rows" | "vertical";
type Enter = "rise" | "drop" | "pop" | "karaoke" | "gather" | "type";
type Exit = "up" | "scatter" | "zoom" | "fade";

const LAYOUTS: Layout[] = ["center", "left", "right", "tilt", "rows", "vertical"];
const CHORUS_LAYOUTS: Layout[] = ["center", "tilt", "rows", "left", "right"];
const ENTERS: Enter[] = ["rise", "drop", "pop", "karaoke", "gather", "type"];
const EXITS: Exit[] = ["up", "scatter", "zoom", "fade"];

const isLatin = (s: string) => /^[A-Za-z']+$/.test(s);

type Plan = { layout: Layout; enter: Enter; exit: Exit; chorus: boolean; role: number };

/** deterministic per-line choices, never repeating the previous line's layout / entrance */
const PLANS: Plan[] = (() => {
  const out: Plan[] = [];
  LINES.forEach((l, i) => {
    const chorus = isChorusLine(i);
    const role = chorusRole(i);
    const pool = chorus ? CHORUS_LAYOUTS : LAYOUTS;
    const n = l.chars.length;
    let k = Math.floor(hash(i * 13.7 + 2) * pool.length);
    let layout = pool[k];
    for (let tries = 0; tries < pool.length; tries++) {
      const bad = (out[i - 1] && out[i - 1].layout === layout) || (layout === "vertical" && (n > 7 || l.chars.some((c) => isLatin(c.c))));
      if (!bad) break;
      k = (k + 1) % pool.length;
      layout = pool[k];
    }
    let e = Math.floor(hash(i * 5.3 + 9) * ENTERS.length);
    if (out[i - 1] && ENTERS[e] === out[i - 1].enter) e = (e + 1) % ENTERS.length;
    // the "say it every day" lines always light up karaoke-style, centred and big
    if (role >= 6) {
      layout = role === 7 ? "center" : role === 6 ? "rows" : "center";
      e = ENTERS.indexOf(role === 7 ? "pop" : "karaoke");
    }
    out.push({ layout, enter: ENTERS[e], exit: EXITS[Math.floor(hash(i * 7.9 + 4) * EXITS.length)], chorus, role });
  });
  return out;
})();

/** story version: same choices, but vertical columns become centred / tilted lines */
const STORY_PLANS: Plan[] = PLANS.map((p, i) => (p.layout === "vertical" ? { ...p, layout: (PLANS[i - 1]?.layout === "tilt" ? "center" : "tilt") as Layout } : p));

type U = { text: string; s: number; e: number; w: number; latin: boolean; x: number; y: number; accent: boolean };

const build = (line: Line, plan: Plan, size0: number, cy: number) => {
  const units: U[] = [];
  line.chars.forEach((c) => {
    const latin = isLatin(c.c);
    const prev = units[units.length - 1];
    const gap = latin && prev ? 0.3 : 0;
    units.push({ text: c.c, s: c.s, e: c.e, w: latin ? c.c.length * 0.56 + 0.1 : 1, latin, x: gap, y: 0, accent: plan.role >= 6 && c.c === "天" });
  });
  const totalEm = units.reduce((a, u) => a + u.w + u.x, 0);
  let size = Math.min(size0, MAXW / totalEm);
  const layout = plan.layout;
  if (layout === "vertical") {
    size = Math.min(size0, (SY1 - SY0 - 60) / units.length / 1.05);
    const colX = hash(line.start) > 0.5 ? SX0 + 140 : SX1 - 140 - size;
    const top = lerp(SY0 + 20, SY1 - units.length * size * 1.05 - 20, hash(line.start * 3));
    units.forEach((u, i) => {
      u.x = colX;
      u.y = top + i * size * 1.05;
    });
    return { units, size };
  }
  // rows: split in the middle for "rows", or when the line is too wide
  let rows: U[][] = [units];
  const twoRow = layout === "rows" || totalEm * size0 > MAXW * 1.05;
  if (twoRow && units.length >= 4) {
    const half = Math.ceil(units.length / 2);
    rows = [units.slice(0, half), units.slice(half)];
    const widest = Math.max(...rows.map((r) => r.reduce((a, u) => a + u.w + u.x, 0)));
    size = Math.min(size0 * (layout === "rows" ? 1.1 : 1), MAXW / (widest + (layout === "rows" ? 1.6 : 0)));
  }
  const lh = size * 1.3;
  const blockH = rows.length * lh;
  const top = Math.max(SY0, Math.min(SY1 - blockH, cy - blockH / 2));
  rows.forEach((r, ri) => {
    const rw = r.reduce((a, u) => a + (u.w + u.x) * size, 0);
    const stag = layout === "rows" ? (ri ? 0.8 : -0.8) * size : 0;
    let x =
      layout === "left"
        ? SX0 + 40 + ri * size * 0.6
        : layout === "right"
          ? SX1 - 40 - rw - (rows.length - 1 - ri) * size * 0.6
          : (SX0 + SX1) / 2 - rw / 2 + stag;
    r.forEach((u) => {
      x += u.x * size;
      u.x = x;
      u.y = top + ri * lh;
      x += u.w * size;
    });
  });
  return { units, size };
};

const LyricLine: React.FC<{ line: Line; plan: Plan; t: number; outAt: number; seed: number; cy: number; size: number; accentColor: string; textColor: string; print?: boolean }> = ({
  line,
  plan,
  t,
  outAt,
  seed,
  cy,
  size: size0,
  accentColor,
  textColor,
  print,
}) => {
  const { units, size } = build(line, plan, size0, cy);
  const appear = line.start - 0.35;
  if (t < appear - 0.5 || t > outAt + 1) return null;
  const pulse = plan.chorus ? pulseAt(t) : 0;
  const life = Math.max(0, t - line.start);
  const cx = units.reduce((a, u) => a + u.x + (u.w * size) / 2, 0) / units.length;
  const cyy = units.reduce((a, u) => a + u.y + size / 2, 0) / units.length;
  const drift = (hash(seed * 2.2) - 0.5) * 2;
  const tilt = plan.layout === "tilt" ? (hash(seed) > 0.5 ? -5 : 4) : 0;
  const font = plan.chorus ? SANS : SERIF;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        transformOrigin: `${cx}px ${cyy}px`,
        transform: `translate(${drift * life * 5}px, ${-life * 2}px) rotate(${tilt}deg) scale(${1 + life * 0.008 + pulse * 0.05})`,
      }}
    >
      {units.map((u, i) => {
        const r = (hash(seed * 31 + i) - 0.5) * 2;
        const lead = plan.enter === "karaoke" ? 0.35 : 0.06;
        const p = (t - (plan.enter === "karaoke" ? appear + i * 0.02 : u.s - lead)) / (plan.enter === "type" ? 0.08 : 0.32);
        if (p < 0) return null;
        const pin = clamp01(p);
        const eo = easeOut(pin);
        let tx = 0;
        let ty = 0;
        let sc = 1;
        let rot = 0;
        let blur = 0;
        let op = clamp01(p * 2.5);
        switch (plan.enter) {
          case "rise":
            ty = (1 - eo) * size * 0.6;
            blur = (1 - eo) * 10;
            break;
          case "drop":
            ty = (1 - easeOutBack(pin, 2.2)) * -size * 0.9;
            rot = r * 10 * (1 - eo);
            break;
          case "pop":
            sc = lerp(1.9, 1, easeOutBack(pin, 1.8));
            blur = (1 - eo) * 14;
            break;
          case "gather":
            tx = (1 - eo) * r * size * 2.2;
            ty = (1 - eo) * (hash(seed + i * 3) - 0.5) * size * 2;
            rot = r * 40 * (1 - eo);
            break;
          case "type":
            sc = lerp(1.25, 1, eo);
            break;
          case "karaoke":
            op = clamp01(p * 2) * 0.5;
            break;
        }
        // karaoke light-up when sung
        const sung = clamp01((t - u.s) / 0.18);
        if (plan.enter === "karaoke") {
          op = op + (1 - op) * sung;
          sc *= 1 + Math.sin(Math.PI * sung) * 0.12;
        }
        // exit
        const ox = easeOut(clamp01((t - outAt - i * 0.022) / 0.45));
        switch (plan.exit) {
          case "up":
            ty -= ox * size * 0.7;
            blur += ox * 10;
            break;
          case "scatter":
            tx += ox * r * size * 1.5;
            ty += ox * (hash(seed * 7 + i) - 0.6) * size * 1.8;
            rot += ox * r * 60;
            break;
          case "zoom":
            sc *= 1 + ox * 0.7;
            blur += ox * 14;
            break;
          case "fade":
            blur += ox * 4;
            break;
        }
        op *= 1 - easeIn(ox);
        const accent = u.accent || (plan.chorus && plan.role === 3);
        const col = accent ? accentColor : textColor;
        const glow = accent || (plan.enter === "karaoke" && sung > 0) ? `0 0 ${size * 0.25}px ${rgba(accentColor, 0.65)},` : "";
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: u.x,
              top: u.y,
              width: u.w * size,
              textAlign: "center",
              whiteSpace: "pre",
              fontFamily: font,
              fontWeight: 900,
              fontStyle: u.latin ? "italic" : "normal",
              fontSize: size,
              lineHeight: 1,
              color: col,
              opacity: op,
              filter: blur > 0.3 ? `blur(${blur}px)` : undefined,
              transform: `translate(${tx}px, ${ty}px) rotate(${rot}deg) scale(${sc})`,
              WebkitTextStroke: print ? `${Math.max(1.5, size * 0.022)}px #1b1a14` : undefined,
              paintOrder: print ? "stroke fill" : undefined,
              textShadow: print
                ? `${glow} ${size * 0.045}px ${size * 0.045}px 0 rgba(215,38,61,0.85), 0 ${size * 0.04}px ${size * 0.18}px rgba(0,0,0,0.4)`
                : `${glow} 0 ${size * 0.04}px ${size * 0.16}px rgba(0,0,0,0.65), 0 0 ${size * 0.5}px rgba(0,0,0,0.25), 0 0 2px rgba(0,0,0,0.6)`,
            }}
          >
            {u.text}
          </div>
        );
      })}
    </div>
  );
};

const outAtOf = (i: number) => {
  const l = LINES[i];
  const next = LINES[i + 1];
  if (!next) return l.end + 3.5;
  return next.start - l.end > 4 ? Math.min(l.end + 2.4, next.start - 3) : next.start - 0.25;
};

/** Where lines sit vertically, by section (keeps them off the calendar / cars). */
const cyFor = (i: number) => {
  const sec = secAt(LINES[i].start);
  if (sec === "c1" || sec === "c2" || sec === "c3") return chorusRole(i) >= 6 ? 500 : 400;
  if (sec === "outro") return 520;
  return 470;
};

export type LyricPlace = { cy?: number; layout?: Layout };

export const Lyrics: React.FC<{ t: number; story?: boolean; place?: Record<number, LyricPlace> }> = ({ t, story, place = {} }) => {
  const m = moodAt(t);
  const plans = story ? STORY_PLANS : PLANS;
  return (
    <AbsoluteFill>
      {LINES.map((line, i) => {
        if (!(t > line.start - 1 && t < outAtOf(i) + 1)) return null;
        const pl = place[i + 1] ?? {};
        const plan = pl.layout ? { ...plans[i], layout: pl.layout } : plans[i];
        const base = plan.chorus ? (plan.role >= 6 ? 150 : 128) : 112;
        return (
          <LyricLine
            key={i}
            line={line}
            plan={plan}
            t={t}
            outAt={outAtOf(i)}
            seed={i + 1}
            cy={pl.cy ?? (story ? 190 : cyFor(i))}
            size={story ? base * 0.82 : base}
            accentColor={story ? "#ffd21f" : m.accent}
            textColor={m.text}
            print={story}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Intro teaser: one chorus line, re-timed into the first 15 s, karaoke style on the left. */
export const Teaser: React.FC<{ t: number; idx: number; from: number; to: number; print?: boolean }> = ({ t, idx, from, to, print }) => {
  const src = LINES[idx];
  const span = src.end - src.start;
  const k = (to - from - 1.8) / span;
  const line: Line = {
    ...src,
    start: from,
    end: from + span * k,
    chars: src.chars.map((c) => ({ ...c, s: from + (c.s - src.start) * k, e: from + (c.e - src.start) * k })),
  };
  const plan: Plan = { layout: "left", enter: "karaoke", exit: "up", chorus: true, role: 6 };
  const m = moodAt(t);
  return <LyricLine line={line} plan={plan} t={t} outAt={to - 0.5} seed={99} cy={720} size={84} accentColor={print ? "#ffd21f" : m.accent} textColor={m.text} print={print} />;
};

