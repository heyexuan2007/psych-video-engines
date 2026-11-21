import React from "react";

/**
 * 小团子 (Tuanzi): an original, posable lead character for this MV — a round mochi-shaped creature
 * with a leaf sprout, short arms with mitten hands and two stubby feet. Her version swaps the sprout
 * for a bow. Units: the viewBox is 12 wide; the face sits on the same grid as before so every
 * expression keeps working.
 */
export type Expr =
  | "neutral"
  | "happy" // ^ ^
  | "joy" // ^ ^ + open smile
  | "sad"
  | "cry"
  | "surprised"
  | "love" // heart eyes
  | "shy" // looks down + blush
  | "sleepy"
  | "determined"
  | "sigh" // eyes closed, droopy
  | "nervous"
  | "dreamy"; // half-lidded, looking up
export type Emote = "!" | "?" | "♪" | "♥" | "..." | "z" | "sweat" | "spark" | "anger" | null;
export type Legs = "stand" | "walk" | "run" | "sit" | "dangle" | "tiptoe";

export type Pose = {
  expr?: Expr;
  /** pupil direction, -1..1 */
  lookX?: number;
  lookY?: number;
  blink?: boolean;
  blush?: number; // 0..1
  /** arm angles in degrees (0 = straight out sideways, negative = raised) */
  armL?: number;
  armR?: number;
  /** hand open (spread mitten) 0..1 */
  pinch?: number;
  legs?: Legs;
  phase?: number; // walk / run phase (cycles)
  squash?: number; // -1 stretch … 1 squash
  tilt?: number; // deg
  flip?: boolean;
  emote?: Emote;
  emoteT?: number; // seconds since emote appeared (for pop-in)
  color?: string;
  /** her: bow instead of the leaf sprout */
  bow?: boolean;
  shadow?: boolean;
};

const DARK = "#3a2618";

const shade = (c: string, k: number) => {
  const n = parseInt(c.slice(1), 16);
  const f = (v: number) => Math.max(0, Math.min(255, Math.round(v * (1 + k))));
  return `rgb(${f((n >> 16) & 255)},${f((n >> 8) & 255)},${f(n & 255)})`;
};

const Eye: React.FC<{ x: number; e: Expr; lx: number; ly: number; blink: boolean; left: boolean }> = ({ x, e, lx, ly, blink, left }) => {
  const px = x + lx * 0.35;
  const py = 1.2 + ly * 0.3;
  const r = (xx: number, yy: number, w: number, h: number, f = DARK, k = "") => <rect key={k + xx + "-" + yy} x={xx} y={yy} width={w} height={h} rx={Math.min(w, h) * 0.45} fill={f} />;
  const out: React.ReactNode[] = [];
  if (blink && e !== "love" && e !== "happy" && e !== "joy") {
    out.push(r(px - 0.1, 2.05, 1.2, 0.3));
    return <>{out}</>;
  }
  switch (e) {
    case "happy":
    case "joy":
      out.push(<path key="h" d={`M${x - 0.2} ${2.3} Q${x + 0.5} ${1.2} ${x + 1.2} ${2.3}`} stroke={DARK} strokeWidth={0.32} fill="none" strokeLinecap="round" />);
      break;
    case "sad":
      out.push(r(px, py + 0.4, 1, 1.3));
      out.push(r(px + 0.15, py + 0.5, 0.35, 0.35, "#fff"));
      out.push(<path key="b" d={left ? `M${x - 0.3} ${0.95} L${x + 0.9} ${0.55}` : `M${x + 0.1} ${0.55} L${x + 1.3} ${0.95}`} stroke={DARK} strokeWidth={0.25} strokeLinecap="round" />);
      break;
    case "cry":
      out.push(<path key="c" d={`M${x - 0.2} ${2.0} Q${x + 0.5} ${2.6} ${x + 1.2} ${2.0}`} stroke={DARK} strokeWidth={0.3} fill="none" strokeLinecap="round" />);
      out.push(<ellipse key="tear" cx={x + (left ? 0.1 : 0.9)} cy={3.0} rx={0.22} ry={0.42} fill="#7fc8ff" />);
      out.push(<path key="b" d={left ? `M${x - 0.3} ${1.15} L${x + 0.9} ${0.75}` : `M${x + 0.1} ${0.75} L${x + 1.3} ${1.15}`} stroke={DARK} strokeWidth={0.25} strokeLinecap="round" />);
      break;
    case "surprised":
      out.push(<ellipse key="s" cx={px + 0.5} cy={py + 0.9} rx={0.75} ry={1.05} fill={DARK} />);
      out.push(<circle key="sh" cx={px + 0.3} cy={py + 0.5} r={0.28} fill="#fff" />);
      break;
    case "love":
      out.push(
        <path key="h" d={`M${x + 0.5} ${2.9} L${x - 0.35} ${1.95} Q${x - 0.6} ${1.2} ${x} ${1.15} Q${x + 0.35} ${1.15} ${x + 0.5} ${1.5} Q${x + 0.65} ${1.15} ${x + 1} ${1.15} Q${x + 1.6} ${1.2} ${x + 1.35} ${1.95} Z`} fill="#ff4d6d" />,
      );
      break;
    case "shy":
      out.push(r(px, 2.0, 1, 0.8));
      break;
    case "sleepy":
    case "sigh":
      out.push(<path key="z" d={`M${x - 0.2} ${2.0} Q${x + 0.5} ${2.5} ${x + 1.2} ${2.0}`} stroke={DARK} strokeWidth={0.28} fill="none" strokeLinecap="round" />);
      break;
    case "determined":
      out.push(r(px, py + 0.4, 1, 1.3));
      out.push(r(px + 0.5, py + 0.5, 0.35, 0.35, "#fff"));
      out.push(<path key="b" d={left ? `M${x - 0.2} ${0.55} L${x + 1.1} ${0.95}` : `M${x - 0.1} ${0.95} L${x + 1.2} ${0.55}`} stroke={DARK} strokeWidth={0.28} strokeLinecap="round" />);
      break;
    case "nervous":
      out.push(r(px + 0.1, py + 0.2, 0.8, 1.1));
      out.push(r(px + 0.25, py + 0.3, 0.3, 0.3, "#fff"));
      break;
    case "dreamy":
      out.push(r(px, 1.3, 1, 1.0));
      out.push(<rect key="lid" x={px - 0.15} y={1.05} width={1.3} height={0.45} fill="currentColor" />);
      out.push(r(px + 0.12, 1.5, 0.32, 0.32, "#fff"));
      break;
    default:
      out.push(r(px, py, 1, 1.7));
      out.push(r(px + 0.15, py + 0.15, 0.4, 0.4, "#fff"));
  }
  return <>{out}</>;
};

const Mouth: React.FC<{ e: Expr }> = ({ e }) => {
  const c = DARK;
  const st = { stroke: c, strokeWidth: 0.26, fill: "none", strokeLinecap: "round" as const };
  switch (e) {
    case "joy":
      return <path d="M4.9 3.3 Q6 4.9 7.1 3.3 Z" fill="#7a2c2c" stroke={c} strokeWidth={0.2} />;
    case "happy":
    case "love":
    case "dreamy":
      return <path d="M5.3 3.45 Q5.65 3.9 6 3.5 Q6.35 3.9 6.7 3.45" {...st} />;
    case "surprised":
      return <ellipse cx={6} cy={3.65} rx={0.38} ry={0.48} fill={c} />;
    case "sad":
    case "cry":
    case "sigh":
      return <path d="M5.3 3.95 Q6 3.4 6.7 3.95" {...st} />;
    case "nervous":
      return <path d="M5 3.7 L5.4 3.45 L5.8 3.7 L6.2 3.45 L6.6 3.7 L7 3.45" {...st} />;
    case "determined":
      return <path d="M5.4 3.65 L6.6 3.65" {...st} />;
    case "shy":
      return <path d="M5.65 3.65 Q6 3.85 6.35 3.65" {...st} />;
    default:
      return <path d="M5.6 3.55 Q6 3.8 6.4 3.55" {...st} />;
  }
};

/** short arm with a round mitten hand, pivoting at the body side */
const Arm: React.FC<{ side: -1 | 1; angle: number; open: number; color: string }> = ({ side, angle, open, color }) => (
  <g transform={`translate(${side < 0 ? 1.8 : 10.2} 2.6) rotate(${side * angle})`}>
    <rect x={side < 0 ? -1.7 : 0} y={-0.38} width={1.7} height={0.76} rx={0.38} fill={color} />
    <ellipse cx={side * 1.85} cy={0} rx={0.62 + open * 0.15} ry={0.62 - open * 0.08} fill={color} />
    <ellipse cx={side * 1.75} cy={-0.5 - open * 0.15} rx={0.22} ry={0.3} fill={color} transform={`rotate(${side * (20 + open * 25)} ${side * 1.75} -0.4)`} />
    <ellipse cx={side * 1.95} cy={0.25} rx={0.42} ry={0.2} fill="rgba(0,0,0,0.1)" />
  </g>
);

const footY = (legs: Legs, i: number, phase: number) => {
  const s = Math.sin(phase * Math.PI * 2 + (i ? Math.PI : 0));
  switch (legs) {
    case "walk":
      return -Math.max(0, s) * 0.45;
    case "run":
      return -Math.max(0, s) * 0.9;
    case "tiptoe":
      return -0.2 - Math.max(0, s) * 0.2;
    default:
      return 0;
  }
};

export const BunRig: React.FC<Pose & { size: number; t?: number; style?: React.CSSProperties }> = ({
  size,
  t = 0,
  expr = "neutral",
  lookX = 0,
  lookY = 0,
  blink,
  blush = 0,
  armL = 0,
  armR = 0,
  pinch = 0,
  legs = "stand",
  phase = 0,
  squash = 0,
  tilt = 0,
  flip = false,
  emote = null,
  emoteT = 1,
  color = "#F3C66B",
  bow = false,
  shadow = true,
  style,
}) => {
  const u = size / 12;
  const breath = Math.sin(t * 2.4) * 0.025;
  const autoBlink = blink ?? (t % 3.7 < 0.12 || (t + 1.3) % 6.1 < 0.1);
  const sit = legs === "sit";
  const dangle = legs === "dangle";
  const bounce = legs === "run" ? Math.abs(Math.sin(phase * Math.PI * 2)) * 0.5 : legs === "walk" ? Math.abs(Math.sin(phase * Math.PI * 2)) * 0.15 : 0;
  const sq = squash + breath;
  const sx = 1 + sq * 0.16;
  const sy = 1 - sq * 0.18;
  const ep = Math.min(1, emoteT / 0.25);
  const gid = `bun${color.slice(1)}`;
  const sway = Math.sin(t * 2.2) * 6;
  return (
    <div style={{ position: "relative", width: size, height: size * 0.62, ...style }}>
      {shadow ? <div style={{ position: "absolute", left: size * 0.16, bottom: -size * 0.04, width: size * 0.68, height: size * 0.08, borderRadius: "50%", background: "rgba(0,0,0,0.28)", filter: `blur(${size * 0.015}px)`, scale: String(1 - bounce * 0.3) }} /> : null}
      <svg
        viewBox="0 -1.5 12 8"
        width={size}
        height={(size / 12) * 8}
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          overflow: "visible",
          color,
          transformOrigin: "50% 92%",
          transform: `translateY(${-bounce * u}px) rotate(${tilt}deg) scale(${(flip ? -1 : 1) * sx}, ${sy})`,
        }}
      >
        <defs>
          <radialGradient id={gid} cx="40%" cy="30%" r="80%">
            <stop offset="0" stopColor={shade(color, 0.18)} />
            <stop offset="0.6" stopColor={color} />
            <stop offset="1" stopColor={shade(color, -0.18)} />
          </radialGradient>
        </defs>
        {/* feet */}
        {sit
          ? [3.4, 7.6].map((x, i) => <ellipse key={i} cx={x + 0.5} cy={5.15} rx={0.9} ry={0.42} fill={shade(color, -0.1)} />)
          : [3.6, 7.4].map((x, i) => (
              <ellipse
                key={i}
                cx={x + 0.5}
                cy={5.3 + (dangle ? 0.35 : footY(legs, i, phase))}
                rx={0.85}
                ry={0.5}
                fill={shade(color, -0.1)}
                transform={dangle ? `rotate(${Math.sin(t * 6 + i * 2) * 14} ${x + 0.5} 5)` : undefined}
              />
            ))}
        <Arm side={-1} angle={armL} open={pinch} color={shade(color, -0.04)} />
        <Arm side={1} angle={armR} open={pinch} color={shade(color, -0.04)} />
        {/* mochi body: domed top, soft wide bottom */}
        <path d="M1.7 3.4 C1.6 0.6 3.6 -0.6 6 -0.6 C8.4 -0.6 10.4 0.6 10.3 3.4 C10.3 4.9 9 5.4 6 5.4 C3 5.4 1.7 4.9 1.7 3.4 Z" fill={`url(#${gid})`} />
        <ellipse cx={4.2} cy={0.4} rx={1.3} ry={0.45} fill="rgba(255,255,255,0.35)" transform="rotate(-15 4.2 0.4)" />
        {bow ? (
          <g transform="translate(8.6 -0.2) rotate(15)">
            <path d="M0 0 L-1.1 -0.6 Q-1.3 0 -1.1 0.6 Z" fill="#ff5f8f" />
            <path d="M0 0 L1.1 -0.6 Q1.3 0 1.1 0.6 Z" fill="#ff5f8f" />
            <circle cx={0} cy={0} r={0.3} fill="#e23e70" />
          </g>
        ) : (
          <g transform={`translate(6 -0.55) rotate(${sway})`}>
            <path d="M0 0 L0 -0.9" stroke="#5c8f3a" strokeWidth={0.22} strokeLinecap="round" />
            <path d="M0 -0.8 Q-1.2 -1.5 -1.3 -0.6 Q-0.6 -0.4 0 -0.8 Z" fill="#7cc24e" />
            <path d="M0 -0.9 Q1.1 -1.8 1.4 -0.9 Q0.7 -0.5 0 -0.9 Z" fill="#8fd35e" />
          </g>
        )}
        {/* face */}
        <Eye x={3.3} e={expr} lx={flip ? -lookX : lookX} ly={lookY} blink={autoBlink} left />
        <Eye x={7.7} e={expr} lx={flip ? -lookX : lookX} ly={lookY} blink={autoBlink} left={false} />
        <Mouth e={expr} />
        {blush > 0 || expr === "shy" || expr === "love" ? (
          <g opacity={Math.max(blush, expr === "shy" ? 0.9 : 0.6)}>
            <ellipse cx={3.1} cy={3.45} rx={0.75} ry={0.35} fill="#ff7a8a" />
            <ellipse cx={8.9} cy={3.45} rx={0.75} ry={0.35} fill="#ff7a8a" />
          </g>
        ) : null}
      </svg>
      {emote ? (
        <div
          style={{
            position: "absolute",
            left: size * 0.66,
            top: -size * 0.46,
            fontSize: size * 0.26,
            lineHeight: 1,
            fontWeight: 900,
            fontFamily: "sans-serif",
            color: emote === "♥" ? "#ff4d6d" : emote === "anger" ? "#ff4d4d" : emote === "sweat" ? "#7fc8ff" : "#ffffff",
            textShadow: "0 2px 6px rgba(0,0,0,0.45)",
            scale: String(0.4 + ep * 0.6 + Math.sin(ep * Math.PI) * 0.3),
            opacity: ep,
            translate: `0 ${Math.sin(t * 3) * size * 0.02}px`,
          }}
        >
          {emote === "sweat" ? "💧" : emote === "spark" ? "✦" : emote === "anger" ? "💢" : emote === "z" ? "z Z" : emote}
        </div>
      ) : null}
    </div>
  );
};
