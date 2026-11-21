import React from "react";
import { AbsoluteFill } from "remotion";
import { Mood } from "../lib/theme";
import { H, W, clamp01, energyAt, hash, lerp, mix, rgba } from "../lib/util";

export const SUN_X = 1280;
export const sunY = (m: Mood, t: number) => lerp(300, 640, m.night) + Math.sin(t * 0.05) * 20;

/** Gradient sky + sun bloom + stars. */
export const Sky: React.FC<{ m: Mood; t: number }> = ({ m, t }) => {
  const e = energyAt(t);
  const sy = sunY(m, t);
  const vis = 1 - m.rain * 0.8;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${m.top} 0%, ${mix(m.top, m.mid, 0.6)} 30%, ${m.mid} 62%, ${m.low} 100%)` }}>
      {/* horizon glow */}
      <div style={{ position: "absolute", left: -200, top: H * 0.45, width: W + 400, height: H * 0.7, background: `radial-gradient(ellipse 60% 50% at ${(SUN_X / W) * 100}% 40%, ${rgba(m.low, 0.9)} 0%, transparent 70%)` }} />
      {/* stars */}
      {m.night > 0.4
        ? Array.from({ length: 160 }, (_, i) => {
            const tw = 0.5 + 0.5 * Math.sin(t * (1 + hash(i) * 2) + i);
            const big = hash(i * 9.1) > 0.93;
            return (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: hash(i * 3.1) * W,
                  top: Math.pow(hash(i * 7.7 + 1), 1.6) * H * 0.6,
                  width: big ? 4 : 1.2 + hash(i * 1.3) * 2,
                  height: big ? 4 : 1.2 + hash(i * 1.3) * 2,
                  borderRadius: "50%",
                  background: i % 9 ? "#fff" : "#ffd9b0",
                  boxShadow: big ? "0 0 8px 2px rgba(255,255,255,0.6)" : undefined,
                  opacity: clamp01((m.night - 0.4) * 1.6) * (0.25 + tw * 0.65) * (1 - m.rain * 0.85),
                }}
              />
            );
          })
        : null}
      {/* sun / moon: wide bloom, core, tight halo */}
      <div style={{ position: "absolute", left: SUN_X - 700, top: sy - 700, width: 1400, height: 1400, borderRadius: "50%", background: `radial-gradient(circle, ${rgba(m.sun, 0.42 + e * 0.12)} 0%, ${rgba(m.sun, 0.14)} 22%, ${rgba(m.sun, 0.04)} 45%, transparent 65%)`, opacity: vis }} />
      <div style={{ position: "absolute", left: SUN_X - 90, top: sy - 90, width: 180, height: 180, borderRadius: "50%", background: `radial-gradient(circle, #ffffff 0%, ${m.sun} 45%, ${rgba(m.sun, 0)} 72%)`, opacity: vis }} />
      <div style={{ position: "absolute", left: SUN_X - 56, top: sy - 56, width: 112, height: 112, borderRadius: "50%", background: `radial-gradient(circle at 42% 40%, #fffdf5, ${mix(m.sun, "#ffffff", 0.5)})`, boxShadow: `0 0 60px 20px ${rgba(m.sun, 0.7)}`, opacity: vis * 0.95 }} />
    </AbsoluteFill>
  );
};

/** Soft volumetric clouds from fractal noise, lit from the top. Drifts with time. */
export const Clouds: React.FC<{ m: Mood; t: number; seed?: number; y?: number; h?: number; speed?: number; density?: number; opacity?: number }> = ({
  m,
  t,
  seed = 3,
  y = 0,
  h = 560,
  speed = 6,
  density = 1,
  opacity = 1,
}) => {
  const id = `cl${seed}`;
  const lit = mix(m.sun, "#ffffff", 0.35 - m.night * 0.3);
  const body = mix(m.mid, m.top, 0.25 + m.rain * 0.3);
  const shade = mix(m.top, "#000000", 0.15);
  const cut = (1.25 - density * 0.15).toFixed(2);
  // render at 1/2 scale and upscale: cheaper and softer
  const sw = W;
  const sh = h / 2;
  return (
    <div style={{ position: "absolute", left: 0, top: y, width: W, height: h, opacity, WebkitMaskImage: "linear-gradient(180deg, black 0%, black 55%, transparent 100%)" }}>
      <svg width={sw} height={sh} viewBox={`0 0 ${sw} ${sh}`} style={{ width: W * 2, height: h, translate: `${-((t * speed) % W)}px 0` }} preserveAspectRatio="none">
        <defs>
          <filter id={id} x="0" y="0" width="1" height="1" colorInterpolationFilters="sRGB">
            <feTurbulence type="fractalNoise" baseFrequency="0.0042 0.016" numOctaves={5} seed={seed} stitchTiles="stitch" result="n" />
            <feColorMatrix in="n" type="matrix" values={`0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  3.2 0 0 0 -${cut}`} result="a" />
            <feOffset in="a" dy={5} result="ad" />
            <feComposite in="a" in2="ad" operator="out" result="rimA" />
            <feGaussianBlur in="rimA" stdDeviation={2.5} result="rimB" />
            <feFlood floodColor={body} result="fb" />
            <feComposite in="fb" in2="a" operator="in" result="bodyC" />
            <feFlood floodColor={shade} floodOpacity={0.55} result="fs" />
            <feOffset in="a" dy={-6} result="au" />
            <feComposite in="a" in2="au" operator="out" result="belly" />
            <feGaussianBlur in="belly" stdDeviation={4} result="bellyB" />
            <feComposite in="fs" in2="bellyB" operator="in" result="shadeC" />
            <feFlood floodColor={lit} result="fl" />
            <feComposite in="fl" in2="rimB" operator="in" result="litC" />
            <feMerge>
              <feMergeNode in="bodyC" />
              <feMergeNode in="shadeC" />
              <feMergeNode in="litC" />
            </feMerge>
          </filter>
        </defs>
        <rect width={sw} height={sh} filter={`url(#${id})`} />
      </svg>
    </div>
  );
};

/** Sun rays + lens flare ghosts; screen-blended. */
export const Rays: React.FC<{ m: Mood; t: number; strength?: number }> = ({ m, t, strength = 1 }) => {
  const sy = sunY(m, t);
  const k = strength * (1 - m.rain) * (1 - m.night * 0.6);
  if (k < 0.03) return null;
  const cx = W / 2;
  const cy = H / 2;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: SUN_X - 1400,
          top: sy - 1400,
          width: 2800,
          height: 2800,
          borderRadius: "50%",
          background: `repeating-conic-gradient(from ${t * 2}deg, ${rgba(m.sun, 0.13)} 0deg, transparent 3deg, transparent 9deg, ${rgba(m.sun, 0.07)} 12deg, transparent 15deg, transparent 23deg)`,
          WebkitMaskImage: "radial-gradient(circle, black 0%, rgba(0,0,0,0.5) 20%, transparent 50%)",
          opacity: k,
        }}
      />
      {[0.35, 0.7, 1.15, 1.5].map((f, i) => {
        const x = lerp(SUN_X, cx, f * 1.4);
        const y = lerp(sy, cy, f * 1.4);
        const r = [40, 90, 28, 140][i];
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - r,
              top: y - r,
              width: 2 * r,
              height: 2 * r,
              borderRadius: "50%",
              background: i === 3 ? `radial-gradient(circle, transparent 60%, ${rgba(m.sun, 0.12)} 75%, transparent 80%)` : `radial-gradient(circle, ${rgba(i % 2 ? "#9fd0ff" : m.sun, 0.14)}, transparent 70%)`,
              opacity: k,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

type Bld = { x: number; w: number; h: number; s: number; kind: number };

/**
 * Procedural skyline with lit/shadow faces, rim light, rooftop details, aerial haze and glowing windows.
 * `layer` 0 = far, 1 = mid, 2 = near. `scroll` in px.
 */
export const Skyline: React.FC<{ m: Mood; t: number; layer: number; scroll?: number; base?: number; litBoost?: number }> = ({
  m,
  t,
  layer,
  scroll = 0,
  base = H,
  litBoost = 0,
}) => {
  const n = [30, 22, 15][layer];
  const scale = [0.55, 0.78, 1][layer];
  const wTotal = W * 1.6;
  const haze = [0.55, 0.3, 0.08][layer];
  const hazeCol = mix(m.mid, m.top, 0.25);
  const cool = mix(m.city, "#1c2350", 0.35);
  const face = mix(cool, hazeCol, haze);
  const faceTop = mix(face, m.sun, (1 - m.night) * 0.1 + 0.03);
  const side = mix(face, "#000000", 0.28 - haze * 0.2);
  const rim = mix(m.sun, "#ffffff", 0.3);
  const gid = `bf${layer}`;
  const sid = `bs${layer}`;
  const buildings: Bld[] = Array.from({ length: n }, (_, i) => {
    const s = layer * 100 + i;
    return {
      x: (i / n) * wTotal + hash(s * 5.1) * 50,
      w: (80 + hash(s * 1.7) * 150) * scale * 1.4,
      h: (170 + Math.pow(hash(s * 2.3), 1.4) * 520) * scale,
      s,
      kind: Math.floor(hash(s * 8.8) * 5),
    };
  });
  const off = ((scroll % wTotal) + wTotal) % wTotal;
  const lit = clamp01(m.night * 1.25 + litBoost);
  const blink = Math.sin(t * 3) > 0.2 ? 1 : 0.15;
  const glowId = `wg${layer}`;
  const visible: { b: Bld; x: number }[] = [];
  [0, 1].forEach((rep) =>
    buildings.forEach((b) => {
      const x = b.x - off + rep * wTotal - W * 0.3;
      if (x > W + 20 || x + b.w < -20) return;
      visible.push({ b, x });
    }),
  );
  const windows = (b: Bld, x: number, top: number, sideW: number) => {
    const fw = b.w - sideW;
    const cols = Math.max(2, Math.floor(fw / (24 * scale)));
    const rows = Math.max(3, Math.floor((b.h - 30 * scale) / (30 * scale)));
    const cw = (fw - 14 * scale) / cols;
    const rh = (b.h - 24 * scale) / rows;
    const out: React.ReactNode[] = [];
    for (let k = 0; k < rows * cols; k++) {
      const r = Math.floor(k / cols);
      const c = k % cols;
      const h = hash(b.s * 31 + k * 1.37);
      const dens = 0.35 + hash(b.s * 4.4) * 0.5 + layer * 0.06; // some towers mostly dark, some busy
      const on = h > dens - litBoost * 0.3 || (h > dens - 0.08 && Math.sin(t * 0.25 + k * 1.7) > 0.85);
      if (!on) continue;
      const warm = hash(k * 3.3 + b.s) > 0.25;
      out.push(
        <rect
          key={k}
          x={x + sideW + 7 * scale + c * cw}
          y={top + 14 * scale + r * rh}
          width={cw * (b.kind === 2 ? 0.85 : 0.55)}
          height={rh * (b.kind === 2 ? 0.28 : 0.52)}
          rx={1}
          fill={warm ? m.win : "#cfe3ff"}
          opacity={(0.35 + hash(k + b.s) * 0.6) * (1 - haze * 0.6)}
        />,
      );
    }
    return out;
  };
  return (
    <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={faceTop} />
          <stop offset="0.6" stopColor={face} />
          <stop offset="1" stopColor={mix(face, hazeCol, 0.25)} />
        </linearGradient>
        <linearGradient id={sid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={mix(side, faceTop, 0.2)} />
          <stop offset="1" stopColor={side} />
        </linearGradient>
        <filter id={glowId} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation={3 * scale + 1} result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {visible.map(({ b, x }) => {
        const top = base - b.h;
        const sideW = b.w * 0.16;
        const setback = b.kind === 1 ? b.h * 0.18 : 0;
        return (
          <g key={`${x.toFixed(0)}-${b.s}`}>
            {/* setback crown */}
            {setback ? <rect x={x + b.w * 0.2} y={top - setback} width={b.w * 0.6} height={setback + 2} fill={`url(#${gid})`} /> : null}
            {b.kind === 3 ? <polygon points={`${x + b.w * 0.15},${top} ${x + b.w * 0.5},${top - b.h * 0.12} ${x + b.w * 0.85},${top}`} fill={faceTop} /> : null}
            <rect x={x} y={top} width={sideW} height={b.h + 4} fill={`url(#${sid})`} />
            <rect x={x + sideW} y={top} width={b.w - sideW} height={b.h + 4} fill={`url(#${gid})`} />
            {/* rim light along the top + sun-facing edge */}
            <rect x={x + sideW} y={top} width={b.w - sideW} height={2} fill={rim} opacity={(1 - m.night * 0.7) * (1 - haze) * 0.8} />
            <rect x={x + b.w - 2} y={top} width={2} height={b.h} fill={rim} opacity={(1 - m.night * 0.8) * (1 - haze) * 0.35} />
            {/* roof details */}
            {b.kind === 0 ? (
              <g>
                <rect x={x + b.w * 0.55} y={top - 46 * scale} width={3 * scale + 1} height={46 * scale} fill={side} />
                <circle cx={x + b.w * 0.55 + 1.5 * scale} cy={top - 46 * scale} r={4 * scale + 1} fill="#ff3b3b" opacity={m.night * blink} />
                <circle cx={x + b.w * 0.55 + 1.5 * scale} cy={top - 46 * scale} r={14 * scale + 2} fill="#ff3b3b" opacity={m.night * blink * 0.25} />
              </g>
            ) : null}
            {b.kind === 4 ? (
              <g>
                <rect x={x + b.w * 0.25} y={top - 30 * scale} width={30 * scale} height={22 * scale} rx={3} fill={side} />
                <rect x={x + b.w * 0.25 + 4 * scale} y={top - 8 * scale} width={3 * scale} height={8 * scale} fill={side} />
                <rect x={x + b.w * 0.25 + 23 * scale} y={top - 8 * scale} width={3 * scale} height={8 * scale} fill={side} />
              </g>
            ) : null}
            {/* daytime glass strips */}
            {m.night < 0.6 && b.kind === 2
              ? Array.from({ length: 6 }, (_, k) => (
                  <rect key={k} x={x + sideW + 6} y={top + 20 + k * (b.h / 6)} width={b.w - sideW - 12} height={3} fill={rim} opacity={0.12 * (1 - haze)} />
                ))
              : null}
          </g>
        );
      })}
      {lit > 0.04 ? (
        <g filter={`url(#${glowId})`} opacity={lit}>
          {visible.map(({ b, x }) => (
            <g key={`w${x.toFixed(0)}-${b.s}`}>{windows(b, x, base - b.h, b.w * 0.16)}</g>
          ))}
        </g>
      ) : null}
      {/* haze band at the foot of this layer */}
      <rect x={0} y={base - 160 * scale} width={W} height={160 * scale + 10} fill={`url(#hz${layer})`} />
      <defs>
        <linearGradient id={`hz${layer}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={hazeCol} stopOpacity={0} />
          <stop offset="1" stopColor={hazeCol} stopOpacity={0.35 + haze * 0.3} />
        </linearGradient>
      </defs>
    </svg>
  );
};

/** Diagonal rain streaks. */
export const Rain: React.FC<{ t: number; amount: number; near?: boolean }> = ({ t, amount, near }) => {
  if (amount < 0.02) return null;
  const n = Math.round((near ? 70 : 150) * amount);
  return (
    <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
      <defs>
        <linearGradient id={near ? "rn" : "rf"} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e6eef8" stopOpacity={0} />
          <stop offset="1" stopColor="#e6eef8" stopOpacity={1} />
        </linearGradient>
      </defs>
      {Array.from({ length: n }, (_, i) => {
        const sp = (near ? 1900 : 1300) * (0.7 + hash(i * 2.1) * 0.6);
        const len = (near ? 90 : 52) * (0.6 + hash(i * 4.3) * 0.8);
        const y = ((hash(i * 1.9) * (H + 200) + t * sp) % (H + 200)) - 100;
        const x = hash(i * 6.7) * (W + 300) - y * 0.18;
        return (
          <line
            key={i}
            x1={x}
            y1={y}
            x2={x - len * 0.18}
            y2={y + len}
            stroke={`url(#${near ? "rn" : "rf"})`}
            strokeWidth={near ? 2.2 : 1.3}
            strokeLinecap="round"
            opacity={(near ? 0.4 : 0.32) * amount * (0.5 + hash(i * 3.7) * 0.5)}
          />
        );
      })}
    </svg>
  );
};

/** Soft round bokeh discs with bright rims (lens-like). */
export const Bokeh: React.FC<{ t: number; colors: string[]; n?: number; y0?: number; y1?: number; seed?: number; drift?: number; size?: number; opacity?: number }> = ({
  t,
  colors,
  n = 26,
  y0 = 0,
  y1 = H,
  seed = 1,
  drift = 12,
  size = 1,
  opacity = 1,
}) => (
  <AbsoluteFill style={{ mixBlendMode: "screen" }}>
    {Array.from({ length: n }, (_, i) => {
      const s = seed * 97 + i;
      const r = (26 + Math.pow(hash(s * 1.3), 1.5) * 100) * size;
      const x = ((hash(s * 2.7) * (W + 2 * r) + t * drift * (0.5 + hash(s))) % (W + 2 * r)) - r;
      const y = lerp(y0, y1, hash(s * 3.9)) + Math.sin(t * 0.6 + s) * 14;
      const c = colors[i % colors.length];
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x - r,
            top: y - r,
            width: 2 * r,
            height: 2 * r,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${rgba(c, 0.32)} 0%, ${rgba(c, 0.4)} 62%, ${rgba(c, 0.7)} 68%, ${rgba(c, 0)} 72%)`,
            opacity: opacity * (0.35 + hash(s * 5.5) * 0.55),
          }}
        />
      );
    })}
  </AbsoluteFill>
);

/** Floating light motes / dust in the air. */
export const Motes: React.FC<{ t: number; color: string; n?: number; opacity?: number; seed?: number }> = ({ t, color, n = 40, opacity = 1, seed = 1 }) => (
  <AbsoluteFill style={{ mixBlendMode: "screen" }}>
    {Array.from({ length: n }, (_, i) => {
      const s = seed * 51 + i;
      const r = 1.5 + hash(s * 2.2) * 4;
      const x = (hash(s * 1.1) * W + Math.sin(t * 0.3 + s) * 60 + t * 8) % W;
      const y = ((hash(s * 3.3) * H - t * (6 + hash(s) * 14)) % H + H) % H;
      const tw = 0.4 + 0.6 * Math.abs(Math.sin(t * (0.6 + hash(s)) + s));
      return <div key={i} style={{ position: "absolute", left: x, top: y, width: r * 2, height: r * 2, borderRadius: "50%", background: color, boxShadow: `0 0 ${r * 4}px ${r}px ${rgba(color, 0.5)}`, opacity: opacity * tw * 0.7 }} />;
    })}
  </AbsoluteFill>
);

/** Drifting fog band. */
export const Fog: React.FC<{ m: Mood; t: number; y: number; h?: number; opacity?: number }> = ({ m, t, y, h = 260, opacity = 0.5 }) => (
  <div
    style={{
      position: "absolute",
      left: -W * 0.25 + Math.sin(t * 0.07) * 120,
      top: y - h / 2,
      width: W * 1.5,
      height: h,
      background: `radial-gradient(ellipse 50% 50% at 30% 50%, ${rgba(mix(m.low, "#ffffff", 0.2), 0.8)}, transparent 70%), radial-gradient(ellipse 45% 45% at 75% 55%, ${rgba(mix(m.mid, "#ffffff", 0.2), 0.7)}, transparent 70%)`,
      filter: "blur(30px)",
      opacity,
    }}
  />
);

/** Colour grade, light leaks, vignette and grain; sits on top of the picture (below lyrics). */
export const Finish: React.FC<{ t: number; m: Mood }> = ({ t, m }) => {
  const f = Math.floor(t * 30);
  const leak = 0.18 + 0.12 * Math.sin(t * 0.21) + 0.05 * Math.sin(t * 0.53);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* soft-light split tone: cool shadows on top, warm at the bottom */}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, ${rgba("#3a5cc8", 0.5)} 0%, transparent 45%, ${rgba("#ff9a5a", 0.45)} 100%)`, mixBlendMode: "soft-light" }} />
      {/* light leaks */}
      <AbsoluteFill
        style={{
          mixBlendMode: "screen",
          opacity: leak,
          background: `radial-gradient(ellipse 40% 55% at ${8 + Math.sin(t * 0.13) * 6}% ${20 + Math.cos(t * 0.11) * 10}%, ${rgba("#ff8a4c", 0.9)}, transparent 70%), radial-gradient(ellipse 35% 45% at ${92 + Math.sin(t * 0.09) * 5}% 85%, ${rgba(m.accent, 0.7)}, transparent 70%)`,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 75% at 50% 50%, transparent 50%, rgba(0,0,0,0.55) 100%)" }} />
      <svg width={W} height={H} style={{ position: "absolute", opacity: 0.09, mixBlendMode: "overlay" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={f % 48} />
        </filter>
        <rect width={W} height={H} filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};
