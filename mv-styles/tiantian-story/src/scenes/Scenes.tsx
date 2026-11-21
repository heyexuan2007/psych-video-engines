import React from "react";
import { AbsoluteFill } from "remotion";
import { Calendar } from "../components/Calendar";
import { Bokeh, Clouds, Fog, Motes, Rain, Rays, Skyline } from "../components/World";
import { Mood, SANS, SERIF } from "../lib/theme";
import { H, LINES, W, clamp01, easeInOut, easeOut, easeOutBack, energyAt, hash, lerp, mix, prog, pulseAt, rgba, win } from "../lib/util";

type P = { t: number; m: Mood; t0: number; t1: number };

/* ───────────── Intro: dawn, title hook, calendar tearing on the beat ───────────── */

export const IntroScene: React.FC<P & { beats: number[] }> = ({ t, m, t0, t1, beats }) => {
  const fade = win(t, t0, t1, 0.01, 0.8);
  const title = "示例";
  const artist = "演唱者";
  const lift = easeInOut(prog(t, 5.0, 6.6)); // title moves to the left column when the beat comes in
  const ty = lerp(330, 230, lift);
  const ts = lerp(260, 170, lift);
  const tx = lerp(0, -330, lift);
  const calIn = easeOutBack(prog(t, 5.3, 6.3), 1.4);
  const rule = easeOut(prog(t, 1.1, 2.2));
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Clouds m={m} t={t} seed={4} y={-40} h={620} speed={10} />
      <Rays m={m} t={t} strength={0.9} />
      <Skyline m={m} t={t} layer={0} scroll={t * 8} base={H - 60} />
      <Fog m={m} t={t} y={H - 120} opacity={0.35} />
      <Skyline m={m} t={t} layer={1} scroll={t * 16 + 300} base={H + 40} />
      <Skyline m={m} t={t} layer={2} scroll={t * 30 + 900} base={H + 230} />
      <Motes t={t} color={m.sun} n={36} seed={2} opacity={0.8} />
      {/* calendar */}
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, opacity: calIn, translate: `${(1 - calIn) * 500}px 0` }}>
        <Calendar t={t} flips={beats} x={1150} y={290} w={320} startDay={1} />
      </div>
      {/* title */}
      <div style={{ position: "absolute", left: tx, width: W * 0.9, top: ty, textAlign: "center", fontFamily: SERIF, fontWeight: 900, fontSize: ts, color: "#fff", letterSpacing: ts * 0.12 }}>
        {title.split("").map((c, i) => {
          const p = prog(t, 0.05 + i * 0.28, 0.5 + i * 0.28);
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                scale: String(lerp(2.4, 1, easeOutBack(p, 1.7))),
                opacity: clamp01(p * 3),
                filter: `blur(${(1 - easeOut(p)) * 18}px)`,
                rotate: `${(1 - easeOut(p)) * (i ? 14 : -14)}deg`,
                textShadow: `0 10px 40px rgba(0,0,0,0.45), 0 0 60px ${rgba(m.accent, 0.55)}`,
              }}
            >
              {c}
            </span>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: tx, width: W * 0.9, top: ty + ts * 1.16, display: "flex", alignItems: "center", justifyContent: "center", gap: 26 }}>
        <div style={{ width: 120 * rule, height: 2, background: `linear-gradient(90deg, transparent, ${m.accent})` }} />
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: lerp(72, 52, lift), color: m.accent, letterSpacing: 18 }}>
          {artist.split("").map((c, i) => {
            const p = easeOut(prog(t, 0.75, 1.5));
            return (
              <span key={i} style={{ display: "inline-block", opacity: p, translate: `${(1 - p) * (i ? 260 : -260)}px 0`, textShadow: "0 4px 18px rgba(0,0,0,0.5)" }}>
                {c}
              </span>
            );
          })}
        </div>
        <div style={{ width: 120 * rule, height: 2, background: `linear-gradient(90deg, ${m.accent}, transparent)` }} />
      </div>
      <div style={{ position: "absolute", left: tx, width: W * 0.9, top: ty + ts * 1.16 + lerp(100, 78, lift), textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 22, letterSpacing: 14, color: rgba("#ffffff", 0.75 * rule) }}>
        TIAN TIAN · DAVID TAO
      </div>
    </AbsoluteFill>
  );
};

/* ───────────── Verse: café window, sun then rain, couple outside ───────────── */

const Drops: React.FC<{ t: number; amount: number }> = ({ t, amount }) => (
  <AbsoluteFill>
    {Array.from({ length: Math.round(80 * amount) }, (_, i) => {
      const life = 3 + hash(i * 1.7) * 5;
      const cyc = Math.floor((t + hash(i * 3.3) * life) / life);
      const ph = ((t + hash(i * 3.3) * life) % life) / life;
      const x = hash(i * 9.1 + cyc * 1.3) * W;
      const slide = ph > 0.55 ? easeOut((ph - 0.55) / 0.45) * (200 + hash(i) * 400) : 0;
      const y = hash(i * 5.7 + cyc) * H * 0.8 + slide;
      const r = 4 + Math.pow(hash(i * 2.9), 2) * 12;
      return (
        <React.Fragment key={i}>
          {slide > 0 ? <div style={{ position: "absolute", left: x - r * 0.22, top: y - slide, width: r * 0.44, height: slide, background: "linear-gradient(180deg, rgba(255,255,255,0), rgba(255,255,255,0.16))", borderRadius: r }} /> : null}
          <div
            style={{
              position: "absolute",
              left: x - r,
              top: y - r * 1.15,
              width: r * 2,
              height: r * 2.3,
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              background: "radial-gradient(circle at 50% 70%, rgba(255,240,215,0.35) 0%, rgba(255,255,255,0.06) 50%), radial-gradient(circle at 35% 28%, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 22%)",
              boxShadow: `inset 0 -${r * 0.3}px ${r * 0.4}px rgba(0,0,0,0.25), 0 ${r * 0.15}px ${r * 0.3}px rgba(0,0,0,0.15)`,
              opacity: amount * Math.min(1, ph * 8),
            }}
          />
        </React.Fragment>
      );
    })}
  </AbsoluteFill>
);

/** Original simple silhouette figures; `umbrella` = share one umbrella. */
const Couple: React.FC<{ x: number; t: number; umbrella: number }> = ({ x, t, umbrella }) => {
  const fig = (dx: number, h: number, phase: number, col: string) => {
    const sw = Math.sin(t * 4 + phase);
    const bob = Math.abs(sw) * h * 0.025;
    return (
      <div style={{ position: "absolute", left: dx - h * 0.17, top: -h - bob, width: h * 0.34, height: h }}>
        <div style={{ position: "absolute", left: h * 0.07, top: 0, width: h * 0.2, height: h * 0.21, borderRadius: "50%", background: col }} />
        <div style={{ position: "absolute", left: 0, top: h * 0.23, width: h * 0.34, height: h * 0.5, borderRadius: `${h * 0.15}px ${h * 0.15}px ${h * 0.06}px ${h * 0.06}px`, background: col }} />
        <div style={{ position: "absolute", left: h * 0.05, top: h * 0.7, width: h * 0.1, height: h * 0.3, borderRadius: h * 0.05, background: col, rotate: `${sw * 16}deg`, transformOrigin: "50% 0" }} />
        <div style={{ position: "absolute", left: h * 0.19, top: h * 0.7, width: h * 0.1, height: h * 0.3, borderRadius: h * 0.05, background: col, rotate: `${-sw * 16}deg`, transformOrigin: "50% 0" }} />
      </div>
    );
  };
  return (
    <div style={{ position: "absolute", left: x, top: 830 }}>
      {fig(0, 300, 0, "#1a1624")}
      {fig(88, 272, 1.3, "#241c30")}
      {umbrella > 0 ? (
        <div style={{ position: "absolute", left: -150, top: -400, width: 330, height: 120, opacity: umbrella }}>
          <div style={{ position: "absolute", inset: 0, borderRadius: "165px 165px 20px 20px / 120px 120px 20px 20px", background: "linear-gradient(180deg,#d9455f,#9e2a44)" }} />
          {[0.2, 0.4, 0.6, 0.8].map((p) => (
            <div key={p} style={{ position: "absolute", left: 330 * p, top: 10, width: 2, height: 108, background: "rgba(0,0,0,0.25)", rotate: `${(p - 0.5) * 50}deg`, transformOrigin: "50% 100%" }} />
          ))}
          <div style={{ position: "absolute", left: 163, top: 110, width: 5, height: 170, background: "#2a2026" }} />
        </div>
      ) : null}
    </div>
  );
};

const Plant: React.FC<{ x: number; y: number; t: number }> = ({ x, y, t }) => (
  <div style={{ position: "absolute", left: x, top: y }}>
    {Array.from({ length: 9 }, (_, i) => {
      const a = -70 + i * 17 + Math.sin(t * 0.8 + i) * 2;
      const len = 90 + hash(i * 3.1) * 70;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 60,
            top: 10,
            width: 34,
            height: len,
            borderRadius: "50% 50% 50% 50% / 80% 80% 20% 20%",
            background: `linear-gradient(90deg, #1f4a2c, ${i % 2 ? "#3f8a4e" : "#2f6e3e"})`,
            rotate: `${a}deg`,
            transformOrigin: "50% 100%",
            translate: `0 ${-len}px`,
          }}
        />
      );
    })}
    <div style={{ position: "absolute", left: 18, top: 0, width: 120, height: 100, borderRadius: "8px 8px 30px 30px", background: "linear-gradient(90deg,#b5603e,#e08a62 45%,#9a4a2e)" }} />
    <div style={{ position: "absolute", left: 10, top: -6, width: 136, height: 22, borderRadius: 6, background: "linear-gradient(90deg,#a35634,#d88058,#8f4428)" }} />
  </div>
);

const Wood = (dir: string) => `linear-gradient(${dir}, #4a3121 0%, #2c1c12 45%, #1d120b 100%)`;

export const CafeScene: React.FC<P & { rainFrom: number; couple: [number, number]; second?: boolean }> = ({ t, m, t0, t1, rainFrom, couple, second }) => {
  const fade = win(t, t0, t1, 0.8, 0.8);
  const rain = second ? 1 : clamp01((t - rainFrom) / 2.5);
  const push = 1.06 + prog(t, t0, t1) * 0.06;
  const cp = prog(t, couple[0], couple[1]);
  const away = easeInOut(prog(t, couple[1] - 4, couple[1]));
  const sun = 1 - rain;
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      {/* outside, seen through the glass (depth of field) */}
      <AbsoluteFill style={{ scale: String(push), filter: `blur(${3 + away * 6}px) saturate(1.1)` }}>
        <Clouds m={m} t={t} seed={second ? 9 : 6} y={-60} h={560} speed={7} density={1 + rain * 0.6} opacity={0.95} />
        <Skyline m={m} t={t} layer={0} scroll={t * 4} base={H - 260} />
        <Fog m={m} t={t} y={H - 290} opacity={0.2 + rain * 0.15} />
        <Skyline m={m} t={t} layer={1} scroll={t * 7 + 300} base={H - 170} />
        {/* street + wet sidewalk sheen */}
        <div style={{ position: "absolute", left: 0, top: 820, width: W, height: H - 820, background: `linear-gradient(180deg, ${mix(m.city, m.low, 0.25 + rain * 0.2)}, ${mix(m.city, "#000000", 0.3)})` }} />
        <div style={{ position: "absolute", left: 0, top: 822, width: W, height: 90, background: `linear-gradient(180deg, ${rgba(m.low, 0.5 * rain)}, transparent)` }} />
        <Bokeh t={t} colors={[m.win, m.sun, "#ff9d6b", "#7fb8ff"]} n={26} y0={620} y1={860} seed={second ? 4 : 2} drift={6} size={0.45} opacity={0.45 + m.night * 0.45} />
        {cp > 0 && cp < 1 ? <Couple x={lerp(-260, W + 200, cp)} t={t} umbrella={rain} /> : null}
        <Rain t={t} amount={rain * Math.max(0.6, m.rain)} />
      </AbsoluteFill>
      {/* sunbeam through the glass */}
      <AbsoluteFill style={{ mixBlendMode: "screen", background: `linear-gradient(115deg, ${rgba(m.sun, 0.32 * sun)} 0%, transparent 32%, ${rgba(m.sun, 0.1 * sun)} 45%, transparent 58%)` }} />
      {/* interior reflections on the glass: pendant lamps + warm spill */}
      <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.35 + rain * 0.35 }}>
        {[260, 720, 1180].map((x, i) => (
          <div key={i} style={{ position: "absolute", left: x - 70, top: 120 + (i % 2) * 30, width: 140, height: 140, borderRadius: "50%", background: "radial-gradient(circle, rgba(255,200,130,0.55) 0%, rgba(255,170,90,0.18) 45%, transparent 70%)" }} />
        ))}
        <div style={{ position: "absolute", left: -200, top: H - 520, width: 900, height: 600, background: "radial-gradient(ellipse at 30% 80%, rgba(255,170,90,0.35), transparent 65%)" }} />
      </AbsoluteFill>
      {/* condensation at the bottom of the glass */}
      <div style={{ position: "absolute", left: 0, top: H - 360, width: W, height: 260, background: `linear-gradient(180deg, transparent, ${rgba("#dfe8f0", 0.08 + rain * 0.08)})` }} />
      <Drops t={t} amount={rain} />
      {/* window frame: wood with bevels */}
      <AbsoluteFill>
        <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 54, background: Wood("180deg"), boxShadow: "0 6px 14px rgba(0,0,0,0.45)" }} />
        <div style={{ position: "absolute", left: 0, top: 84, width: W, height: 18, background: Wood("180deg"), boxShadow: "0 4px 10px rgba(0,0,0,0.35)" }} />
        <div style={{ position: "absolute", left: 0, top: 0, width: 58, height: H, background: Wood("90deg"), boxShadow: "6px 0 14px rgba(0,0,0,0.45)" }} />
        <div style={{ position: "absolute", right: 0, top: 0, width: 58, height: H, background: Wood("270deg"), boxShadow: "-6px 0 14px rgba(0,0,0,0.45)" }} />
        <div style={{ position: "absolute", left: 58, top: 54, width: W - 116, height: 1.5, background: "rgba(255,220,180,0.25)" }} />
        {/* sill */}
        <div style={{ position: "absolute", left: 0, top: H - 118, width: W, height: 118, background: "repeating-linear-gradient(90deg, rgba(0,0,0,0.05) 0 3px, transparent 3px 11px), linear-gradient(180deg,#7a5236 0%,#5b3b26 18%,#3a2416 100%)", boxShadow: "0 -8px 24px rgba(0,0,0,0.45)" }} />
        <div style={{ position: "absolute", left: 0, top: H - 118, width: W, height: 3, background: "rgba(255,214,170,0.55)" }} />
      </AbsoluteFill>
      <Plant x={90} y={H - 210} t={t} />
      {/* coffee cup on the sill, with steam */}
      <div style={{ position: "absolute", left: 1640, top: H - 252 }}>
        {[0, 1, 2].map((k) => (
          <div
            key={k}
            style={{
              position: "absolute",
              left: 40 + k * 26,
              top: -100 - ((t * 30 + k * 30) % 60),
              width: 20,
              height: 100,
              borderRadius: 10,
              background: "linear-gradient(180deg, rgba(255,255,255,0), rgba(255,255,255,0.35), rgba(255,255,255,0))",
              rotate: `${Math.sin(t * 1.4 + k) * 14}deg`,
              filter: "blur(5px)",
            }}
          />
        ))}
        <div style={{ position: "absolute", left: -46, top: 120, width: 242, height: 26, borderRadius: "50%", background: "radial-gradient(ellipse, rgba(0,0,0,0.45), transparent 70%)" }} />
        <div style={{ position: "absolute", left: -36, top: 112, width: 222, height: 24, borderRadius: "50%", background: "linear-gradient(180deg,#fffaf2,#d6cabb)" }} />
        <div style={{ position: "absolute", left: 136, top: 22, width: 58, height: 64, borderRadius: "50%", border: "15px solid #e9e0d2" }} />
        <div style={{ position: "absolute", left: 0, top: 0, width: 150, height: 128, borderRadius: "10px 10px 64px 64px", background: "linear-gradient(90deg,#d8cdbf 0%,#fffdf8 30%,#f4ece1 60%,#c7baa9 100%)" }} />
        <div style={{ position: "absolute", left: 22, top: 18, width: 14, height: 80, borderRadius: 7, background: "rgba(255,255,255,0.8)", filter: "blur(2px)" }} />
        <div style={{ position: "absolute", left: 5, top: 3, width: 140, height: 20, borderRadius: "50%", background: "radial-gradient(ellipse at 40% 40%, #8a5a36, #3d2213)" }} />
      </div>
    </AbsoluteFill>
  );
};

/* ───────────── Pre-chorus: heart flies across the city to a lit window ───────────── */

export const FlightScene: React.FC<P & { fly: [number, number]; glow: number }> = ({ t, m, t0, t1, fly, glow }) => {
  const fade = win(t, t0, t1, 0.8, 0.6);
  const p = easeInOut(prog(t, fly[0], fly[1]));
  const pan = lerp(0, 700, prog(t, t0, t1));
  const ax = 160;
  const bx = 1700;
  const path = (q: number) => ({ x: lerp(ax, bx, q), y: 640 - Math.sin(q * Math.PI) * 380 });
  const hp = path(p);
  const g = easeOut(prog(t, glow, glow + 1.2));
  const pulse = pulseAt(t);
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Clouds m={m} t={t} seed={12} y={-30} h={600} speed={9} />
      <Rays m={m} t={t} strength={0.8} />
      <Skyline m={m} t={t} layer={0} scroll={pan * 0.3} base={H - 150} litBoost={0.15} />
      <Fog m={m} t={t} y={H - 200} opacity={0.4} />
      <Skyline m={m} t={t} layer={1} scroll={pan * 0.6 + 200} base={H + 10} litBoost={0.1} />
      {/* glowing dotted flight path */}
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <defs>
          <filter id="pathGlow" x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation={5} result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g filter="url(#pathGlow)">
          {Array.from({ length: 70 }, (_, i) => {
            const q = i / 69;
            if (q > p) return null;
            const pt = path(q);
            return <circle key={i} cx={pt.x} cy={pt.y} r={3.5} fill={mix(m.accent, "#ffffff", 0.3)} opacity={0.85 * (1 - (p - q) * 0.5)} />;
          })}
        </g>
      </svg>
      {/* sparkle trail */}
      {p > 0 && p < 1
        ? Array.from({ length: 14 }, (_, i) => {
            const q = Math.max(0, p - i * 0.012);
            const pt = path(q);
            return <div key={i} style={{ position: "absolute", left: pt.x - 4 + (hash(i) - 0.5) * 30, top: pt.y - 4 + (hash(i * 2) - 0.5) * 30 + i * 2, width: 8, height: 8, borderRadius: "50%", background: "#fff", boxShadow: "0 0 12px 4px rgba(255,180,200,0.7)", opacity: 1 - i / 14 }} />;
          })
        : null}
      {/* the far window lighting up */}
      <div style={{ position: "absolute", left: bx - 60, top: 640 - 50, width: 120, height: 100, borderRadius: 8, background: `linear-gradient(180deg, ${mix(m.win, "#ffffff", 0.4)}, ${m.win})`, opacity: clamp01(p * 3) * (0.3 + g * 0.7), boxShadow: `0 0 ${60 + g * 180}px ${20 + g * 40}px ${rgba(m.win, 0.35 + g * 0.45)}` }} />
      <div style={{ position: "absolute", left: bx - 3, top: 590, width: 6, height: 100, background: m.city, opacity: clamp01(p * 3) }} />
      {/* heart */}
      {p > 0 && (p < 1 || t < glow + 0.4) ? (
        <div
          style={{
            position: "absolute",
            left: hp.x - 60,
            top: hp.y - 60,
            width: 120,
            height: 120,
            fontSize: 110,
            lineHeight: "120px",
            textAlign: "center",
            color: "#ff5a7d",
            scale: String(1 + pulse * 0.25),
            filter: `drop-shadow(0 0 24px ${rgba("#ff5a7d", 0.9)})`,
            opacity: 1 - prog(t, glow, glow + 0.4),
          }}
        >
          ♥
        </div>
      ) : null}
      <Skyline m={m} t={t} layer={2} scroll={pan + 600} base={H + 200} litBoost={0.1} />
      <Motes t={t} color={m.win} n={30} seed={5} opacity={0.7} />
    </AbsoluteFill>
  );
};

/* ───────────── Chorus: traffic jam, black-and-white, colour bursts back, 每天 wall ───────────── */

const Car: React.FC<{ x: number; y: number; s: number; color: string; tail: boolean; brake: number }> = ({ x, y, s, color, tail, brake }) => {
  const hi = mix(color, "#ffffff", 0.35);
  const lo = mix(color, "#000000", 0.45);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 260 * s, height: 100 * s }}>
      {/* headlight beam (oncoming lane faces right) */}
      {!tail ? <div style={{ position: "absolute", left: 250 * s, top: 20 * s, width: 420 * s, height: 70 * s, background: "linear-gradient(90deg, rgba(255,246,208,0.45), transparent)", clipPath: "polygon(0 40%, 100% 0, 100% 100%, 0 60%)", filter: `blur(${6 * s}px)` }} /> : null}
      <div style={{ position: "absolute", left: 52 * s, top: 0, width: 146 * s, height: 48 * s, borderRadius: `${32 * s}px ${44 * s}px 0 0`, background: `linear-gradient(180deg, ${hi}, ${color})` }} />
      {/* windows */}
      <div style={{ position: "absolute", left: 66 * s, top: 8 * s, width: 56 * s, height: 30 * s, borderRadius: `${20 * s}px 4px 0 0`, background: "linear-gradient(160deg, #9fb4d0 0%, #2a3448 55%, #151b28 100%)" }} />
      <div style={{ position: "absolute", left: 128 * s, top: 8 * s, width: 56 * s, height: 30 * s, borderRadius: `4px ${26 * s}px 0 0`, background: "linear-gradient(160deg, #9fb4d0 0%, #2a3448 55%, #151b28 100%)" }} />
      <div style={{ position: "absolute", left: 0, top: 38 * s, width: 260 * s, height: 42 * s, borderRadius: `${18 * s}px ${22 * s}px ${12 * s}px ${12 * s}px`, background: `linear-gradient(180deg, ${hi} 0%, ${color} 35%, ${lo} 100%)` }} />
      <div style={{ position: "absolute", left: 10 * s, top: 46 * s, width: 240 * s, height: 2 * s, background: "rgba(255,255,255,0.45)" }} />
      {[46, 186].map((wx) => (
        <div key={wx} style={{ position: "absolute", left: wx * s, top: 60 * s, width: 40 * s, height: 40 * s, borderRadius: "50%", background: "radial-gradient(circle, #9aa0aa 0%, #4a4e57 30%, #0b0b10 38%)" }} />
      ))}
      <div
        style={{
          position: "absolute",
          left: tail ? -4 * s : 246 * s,
          top: 44 * s,
          width: 18 * s,
          height: 14 * s,
          borderRadius: 4 * s,
          background: tail ? "#ff2a3a" : "#fff6d0",
          boxShadow: tail ? `0 0 ${30 + brake * 50}px ${10 + brake * 14}px rgba(255,40,60,${0.45 + brake * 0.4})` : "0 0 40px 14px rgba(255,246,208,0.55)",
        }}
      />
    </div>
  );
};

export const TrafficScene: React.FC<P & { li: number }> = ({ t, m, t0, t1, li }) => {
  const fade = win(t, t0, t1, 0.25, 0.8);
  const L = (k: number) => LINES[li + k];
  // roles: 0 road jammed, 1 everyone waiting, 2 black & white, 3 colour back, 4-5 want / share, 6-8 say it every day
  const grey = win(t, L(2).start - 0.5, L(3).start + 0.15, 0.6, 0.3);
  const burst = prog(t, L(3).start, L(3).start + 1.6);
  const sayFrom = L(6).start - 0.3;
  const sayP = easeOut(prog(t, sayFrom, sayFrom + 1));
  const e = energyAt(t);
  const pulse = pulseAt(t);
  const crawl = t * 22 + Math.sin(t * 0.7) * 20; // stop-and-go
  const lanes = [
    { y: 758, s: 0.8, n: 7, dir: 1, tail: true, seed: 1 },
    { y: 852, s: 1.12, n: 5, dir: -1, tail: false, seed: 2 },
  ];
  const palette = ["#b4504f", "#3f5f96", "#c49a48", "#d9d3c9", "#4d8068", "#2a2a34", "#7b6a9a"].map((c) => mix(c, "#6a6a72", 0.2));
  const cars = lanes.flatMap((ln) =>
    Array.from({ length: ln.n }, (_, i) => {
      const span = W + 600;
      const base = i * (span / ln.n) + hash(ln.seed * 10 + i) * 60;
      const x = ((base + ln.dir * crawl * (ln.dir > 0 ? 0.6 : 1)) % span + span) % span - 300;
      const brake = clamp01(Math.sin(t * 1.3 + i) * 2) * 0.6 + pulse * 0.4;
      return { ...ln, i, x, brake, color: palette[(i + ln.seed * 3) % palette.length] };
    }),
  );
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <AbsoluteFill style={{ filter: `grayscale(${grey}) contrast(${1 + grey * 0.2})` }}>
        <Clouds m={m} t={t} seed={15} y={-40} h={520} speed={5} opacity={0.85} />
        <Rays m={m} t={t} strength={0.6} />
        <Skyline m={m} t={t} layer={0} scroll={t * 5} base={H - 300} />
        <Fog m={m} t={t} y={H - 330} opacity={0.35} />
        <Skyline m={m} t={t} layer={1} scroll={t * 9 + 500} base={H - 284} />
        {/* wet asphalt with a sky-tinted sheen */}
        <div style={{ position: "absolute", left: 0, top: H - 290, width: W, height: 290, background: `linear-gradient(180deg, ${mix("#26232e", m.low, 0.3)} 0%, #1b1922 30%, #0f0e14 100%)` }} />
        <div style={{ position: "absolute", left: 0, top: H - 290, width: W, height: 4, background: rgba(m.low, 0.6) }} />
        <div style={{ position: "absolute", left: 0, top: H - 236, width: W, height: 0, borderTop: "4px dashed rgba(255,230,160,0.4)" }} />
        {/* streetlights */}
        {Array.from({ length: 6 }, (_, i) => {
          const x = ((i * 420 - t * 30) % 2520 + 2520) % 2520 - 300;
          return (
            <div key={i} style={{ position: "absolute", left: x, top: H - 640, width: 10, height: 350, background: "linear-gradient(90deg,#222,#3a3a44,#111)" }}>
              <div style={{ position: "absolute", left: -6, top: -12, width: 70, height: 14, borderRadius: 7, background: "#1a1a22" }} />
              <div style={{ position: "absolute", left: -40, top: -60, width: 180, height: 180, borderRadius: "50%", background: `radial-gradient(circle, ${rgba(m.win, 0.7)}, ${rgba(m.win, 0.15)} 35%, transparent 70%)` }} />
              <div style={{ position: "absolute", left: -60, top: 0, width: 200, height: 360, background: `linear-gradient(180deg, ${rgba(m.win, 0.16)}, transparent)`, clipPath: "polygon(40% 0, 60% 0, 100% 100%, 0 100%)" }} />
            </div>
          );
        })}
        {/* light reflections on the wet road */}
        {cars.map((c) => {
          const lx = c.x + (c.tail ? 4 : 256) * c.s;
          return (
            <div
              key={`r${c.seed}-${c.i}`}
              style={{
                position: "absolute",
                left: lx - 16 * c.s,
                top: c.y + 96 * c.s,
                width: 32 * c.s,
                height: 150 * c.s,
                background: `linear-gradient(180deg, ${c.tail ? `rgba(255,50,70,${0.45 + c.brake * 0.3})` : "rgba(255,240,200,0.4)"}, transparent)`,
                filter: "blur(6px)",
                borderRadius: 20,
              }}
            />
          );
        })}
        {cars.map((c) => (
          <Car key={`${c.seed}-${c.i}`} x={c.x} y={c.y} s={c.s} color={c.color} tail={c.tail} brake={c.brake} />
        ))}
        <Bokeh t={t} colors={["#ff3a4a", "#ff8a3a", "#fff1c0"]} n={20} y0={620} y1={1040} seed={11} drift={3} size={0.9} opacity={0.35 + e * 0.35} />
      </AbsoluteFill>
      {/* colour burst: hearts rise after the grey line */}
      {burst > 0 && t < sayFrom + 0.6
        ? Array.from({ length: 26 }, (_, i) => {
            const d = hash(i * 4.1) * 0.8;
            const q = clamp01((t - L(3).start - d) / 6);
            if (q <= 0 || q >= 1) return null;
            const col = [m.accent, "#ff5a7d", "#ffd27a"][i % 3];
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: hash(i * 2.3) * W,
                  top: lerp(H + 50, -100, q),
                  fontSize: 40 + hash(i * 7) * 70,
                  color: col,
                  filter: `drop-shadow(0 0 14px ${rgba(col, 0.8)})`,
                  opacity: Math.sin(q * Math.PI) * 0.85,
                  rotate: `${Math.sin(t * 2 + i) * 20}deg`,
                }}
              >
                ♥
              </div>
            );
          })
        : null}
      {/* 每天 wall for the "say it every day" lines */}
      {sayP > 0 ? (
        <AbsoluteFill style={{ opacity: sayP * 0.92, background: `radial-gradient(ellipse at 50% 50%, ${rgba(m.mid, 0.6)}, ${rgba(m.top, 0.9)})` }}>
          <Bokeh t={t} colors={[m.accent, "#ff5a7d", "#ffd27a"]} n={18} seed={31} drift={10} size={0.7} opacity={0.6} />
          {Array.from({ length: 7 }, (_, r) => (
            <div
              key={r}
              style={{
                position: "absolute",
                top: -40 + r * 170,
                left: ((((r % 2 ? -1 : 1) * (t - sayFrom) * 90) % 640) + 640) % 640 - 640,
                whiteSpace: "nowrap",
                fontFamily: SERIF,
                fontWeight: 900,
                fontSize: 150,
                color: "transparent",
                WebkitTextStroke: `2px ${rgba(r % 3 === 1 ? m.accent : "#ffffff", 0.16 + (r % 3 === 1 ? pulse * 0.3 : 0))}`,
                letterSpacing: 30,
              }}
            >
              {"每天 ".repeat(16)}
            </div>
          ))}
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

/* ───────────── Interlude: calendar flip montage between sections ───────────── */

export const FlipScene: React.FC<P & { beats: number[]; startDay: number }> = ({ t, m, t0, t1, beats, startDay }) => {
  const fade = win(t, t0, t1, 0.3, 0.5);
  const zoom = lerp(1.25, 1, easeOut(prog(t, t0, t0 + 1)));
  return (
    <AbsoluteFill style={{ opacity: fade, background: `radial-gradient(ellipse at 50% 55%, ${rgba(m.mid, 0.7)}, ${rgba(m.top, 0.92)})` }}>
      <Bokeh t={t} colors={[m.accent, m.win, "#ffffff"]} n={20} seed={41} drift={14} size={0.8} opacity={0.7} />
      <div style={{ position: "absolute", inset: 0, scale: String(zoom) }}>
        <Calendar t={t} flips={beats} x={W / 2 - 210} y={270} w={420} startDay={startDay} />
      </div>
    </AbsoluteFill>
  );
};

/* ───────────── Outro: night → dawn, calendar to the next day, end card ───────────── */

export const OutroScene: React.FC<P & { loveAt: number; cardAt: number }> = ({ t, m, t0, t1, loveAt, cardAt }) => {
  const fade = win(t, t0, t1, 1.2, 2.2);
  const card = easeOut(prog(t, cardAt, cardAt + 1.5));
  const calOut = easeInOut(prog(t, cardAt - 0.5, cardAt + 0.8));
  const love = prog(t, loveAt, loveAt + 3);
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Clouds m={m} t={t} seed={21} y={-30} h={600} speed={6} />
      <Rays m={m} t={t} strength={1} />
      <Skyline m={m} t={t} layer={0} scroll={t * 3} base={H - 120} />
      <Fog m={m} t={t} y={H - 160} opacity={0.4} />
      <Skyline m={m} t={t} layer={1} scroll={t * 6 + 300} base={H - 40} />
      <Motes t={t} color={m.sun} n={40} seed={8} opacity={0.8} />
      <div style={{ position: "absolute", inset: 0, opacity: 1 - calOut, translate: `0 ${calOut * 120}px` }}>
        <Calendar t={t} flips={[t0 + 2, t0 + 5, t0 + 8, loveAt]} x={1250} y={300} w={300} startDay={14} heartFrom={4} />
      </div>
      {/* heart bloom for the final line */}
      {love > 0 && t < cardAt + 1 ? (
        <div
          style={{
            position: "absolute",
            left: W / 2 - 400,
            top: H / 2 - 420,
            width: 800,
            height: 800,
            textAlign: "center",
            lineHeight: "800px",
            fontSize: 700,
            color: rgba("#ff5a7d", 0.22 * Math.sin(love * Math.PI)),
            filter: "blur(4px)",
            scale: String(0.6 + easeOut(love) * 0.5),
          }}
        >
          ♥
        </div>
      ) : null}
      {card > 0 ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 60 }}>
          <div style={{ fontFamily: SERIF, fontWeight: 900, fontSize: 200, color: "#fff", letterSpacing: 40, opacity: card, scale: String(lerp(1.2, 1, card)), filter: `blur(${(1 - card) * 12}px)`, textShadow: `0 10px 40px rgba(0,0,0,0.4), 0 0 70px ${rgba(m.accent, 0.5)}` }}>
            天天
          </div>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 64, color: m.accent, letterSpacing: 24, opacity: easeOut(prog(t, cardAt + 0.6, cardAt + 1.8)), marginTop: 10, textShadow: "0 4px 18px rgba(0,0,0,0.5)" }}>演唱者</div>
          <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 22, letterSpacing: 14, color: "rgba(255,255,255,0.75)", opacity: easeOut(prog(t, cardAt + 1.2, cardAt + 2.4)), marginTop: 22 }}>TIAN TIAN · DAVID TAO</div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
