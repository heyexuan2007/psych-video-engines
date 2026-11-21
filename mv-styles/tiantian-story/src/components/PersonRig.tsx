import React, { useId } from "react";
import { Expr, Pose } from "./BunRig";

/**
 * Original chibi characters drawn in a late-90s screen-print style: black ink outlines,
 * halftone-dot shading, yellow / black / red palette and a slight red print-misregistration offset.
 * He: messy black hair, black jacket over a yellow tee, red sneakers.
 * She (bow = true): side-swept fringe and a side ponytail tied with a yellow bow, red cardigan, black skirt.
 * viewBox 100 × 150, feet at y = 150. Same Pose API as BunRig.
 */

const INK = "#1b1a14";
const SKIN = "#ffe6c2";
const RED = "#d7263d";
const YEL = "#ffd21f";

const Eye: React.FC<{ ex: number; e: Expr; lx: number; ly: number; blink: boolean; left: boolean }> = ({ ex, e, lx, ly, blink, left }) => {
  const ey = 52;
  const cx = ex + lx * 2.2;
  const cy = ey + ly * 2;
  const st = { stroke: INK, strokeWidth: 2.2, fill: "none", strokeLinecap: "round" as const };
  const pupil = (rx: number, ry: number, dy = 0) => (
    <>
      <ellipse cx={cx} cy={cy + dy} rx={rx} ry={ry} fill={INK} />
      <circle cx={cx - rx * 0.35} cy={cy + dy - ry * 0.4} r={Math.max(0.9, rx * 0.38)} fill="#fff" />
    </>
  );
  const brow = (inner: number, outer: number) => {
    // inner = y of the end near the nose, outer = y of the far end
    const xi = left ? ex + 4 : ex - 4;
    const xo = left ? ex - 5 : ex + 5;
    return <path d={`M${xo} ${outer} L${xi} ${inner}`} {...st} strokeWidth={2} />;
  };
  if (blink && e !== "love" && e !== "happy" && e !== "joy") return <path d={`M${ex - 4} ${ey + 1} Q${ex} ${ey + 2.5} ${ex + 4} ${ey + 1}`} {...st} />;
  switch (e) {
    case "happy":
    case "joy":
      return <path d={`M${ex - 4.2} ${ey + 1.5} Q${ex} ${ey - 4.5} ${ex + 4.2} ${ey + 1.5}`} {...st} />;
    case "sad":
      return (
        <>
          {pupil(2.8, 3.5, 1.5)}
          {brow(ey - 11.5, ey - 8)}
        </>
      );
    case "cry":
      return (
        <>
          <path d={`M${ex - 4} ${ey} Q${ex} ${ey + 3.5} ${ex + 4} ${ey}`} {...st} />
          <path d={`M${ex + (left ? -2 : 2)} ${ey + 3} q-1.6 4 0 6 q1.6 -2 0 -6`} fill="#5fb8ff" stroke={INK} strokeWidth={0.8} />
          {brow(ey - 10.5, ey - 7)}
        </>
      );
    case "surprised":
      return (
        <>
          {pupil(3.9, 5.2)}
          {brow(ey - 11.5, ey - 11.5)}
        </>
      );
    case "love":
      return <path d={`M${ex} ${ey + 5} L${ex - 4.6} ${ey - 0.2} Q${ex - 6} ${ey - 5} ${ex - 2.2} ${ey - 4.6} Q${ex - 0.6} ${ey - 4.4} ${ex} ${ey - 2.4} Q${ex + 0.6} ${ey - 4.4} ${ex + 2.2} ${ey - 4.6} Q${ex + 6} ${ey - 5} ${ex + 4.6} ${ey - 0.2} Z`} fill={RED} stroke={INK} strokeWidth={1} />;
    case "shy":
      return <path d={`M${ex - 3.6} ${ey + 2.5} Q${ex} ${ey + 0.5} ${ex + 3.6} ${ey + 2.5}`} {...st} />;
    case "sleepy":
    case "sigh":
      return <path d={`M${ex - 4} ${ey + 1} Q${ex} ${ey + 3.5} ${ex + 4} ${ey + 1}`} {...st} />;
    case "determined":
      return (
        <>
          {pupil(2.8, 3.7, 1)}
          {brow(ey - 7.5, ey - 11)}
        </>
      );
    case "nervous":
      return (
        <>
          {pupil(2.1, 2.9)}
          {brow(ey - 10.5, ey - 8.5)}
        </>
      );
    case "dreamy":
      return (
        <>
          {pupil(2.9, 3.9, -0.5)}
          <rect x={cx - 4} y={cy - 5.2} width={8} height={3.6} fill={SKIN} />
          <path d={`M${cx - 4} ${cy - 1.8} L${cx + 4} ${cy - 1.8}`} {...st} strokeWidth={1.6} />
        </>
      );
    default:
      return pupil(3, 4.2);
  }
};

const Mouth: React.FC<{ e: Expr }> = ({ e }) => {
  const st = { stroke: INK, strokeWidth: 2, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (e) {
    case "joy":
      return <path d="M43 63 Q50 75 57 63 Z" fill="#7a1f22" stroke={INK} strokeWidth={1.6} />;
    case "happy":
    case "love":
    case "dreamy":
      return <path d="M44.5 63.5 Q50 69 55.5 63.5" {...st} />;
    case "surprised":
      return <ellipse cx={50} cy={66} rx={2.6} ry={3.4} fill="#7a1f22" stroke={INK} strokeWidth={1.4} />;
    case "sad":
    case "cry":
    case "sigh":
      return <path d="M45.5 67 Q50 63 54.5 67" {...st} />;
    case "nervous":
      return <path d="M44 65.5 L46.5 63.5 L49 65.5 L51.5 63.5 L54 65.5 L56 63.8" {...st} strokeWidth={1.6} />;
    case "determined":
      return <path d="M45.5 65 L54.5 65" {...st} />;
    case "shy":
      return <path d="M47 65 Q50 66.5 53 65" {...st} strokeWidth={1.6} />;
    default:
      return <path d="M46.5 64 Q50 66 53.5 64" {...st} strokeWidth={1.8} />;
  }
};

/** pop-art blush: a little patch of red halftone dots */
const Blush: React.FC<{ x: number; y: number; o: number }> = ({ x, y, o }) => (
  <g opacity={o}>
    {[-3.4, 0, 3.4].flatMap((dx, i) => [-1.6, 1.6].map((dy, j) => <circle key={`${i}-${j}`} cx={x + dx + (j ? 1.7 : 0)} cy={y + dy} r={1.25} fill={RED} />))}
  </g>
);

const footRot = (legs: Pose["legs"], i: number, phase: number, t: number) => {
  const s = Math.sin(phase * Math.PI * 2 + (i ? Math.PI : 0));
  switch (legs) {
    case "walk":
      return s * 18;
    case "run":
      return s * 34;
    case "tiptoe":
      return s * 8;
    case "dangle":
      return Math.sin(t * 6 + i * 2) * 16;
    default:
      return 0;
  }
};

export const PersonRig: React.FC<Pose & { size: number; t?: number; style?: React.CSSProperties }> = ({
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
  bow = false,
  shadow = true,
  style,
}) => {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const ht = `ht${uid}`;
  const htR = `htr${uid}`;
  const mis = `mis${uid}`;
  const headClip = `hc${uid}`;
  const h = size * 0.95; // rendered height (px)
  const w = h / 1.5;
  const breath = Math.sin(t * 2.4) * 0.025;
  const autoBlink = blink ?? (t % 3.7 < 0.12 || (t + 1.3) % 6.1 < 0.1);
  const sit = legs === "sit";
  const bounce = legs === "run" ? Math.abs(Math.sin(phase * Math.PI * 2)) * 6 : legs === "walk" ? Math.abs(Math.sin(phase * Math.PI * 2)) * 2 : 0;
  const sq = squash + breath;
  const sx = (flip ? -1 : 1) * (1 + sq * 0.12);
  const sy = 1 - sq * 0.14;
  const ep = Math.min(1, emoteT / 0.25);
  const jacket = bow ? RED : "#262626";
  const jacketHi = bow ? "#ef4a5c" : "#3a3a3a";
  const lower = bow ? INK : "#2e3440";
  const shoe = bow ? INK : RED;
  const lx = flip ? -lookX : lookX;
  const bodyDrop = sit ? 10 : 0;
  const arm = (side: -1 | 1, angle: number) => (
    <g transform={`translate(${side < 0 ? 32 : 68} ${92 + bodyDrop}) rotate(${side * angle})`}>
      <rect x={side < 0 ? -21 : 0} y={-5} width={21} height={10} rx={5} fill={jacket} stroke={INK} strokeWidth={2} />
      <rect x={side < 0 ? -21 : 0} y={-5} width={21} height={10} rx={5} fill={`url(#${ht})`} opacity={0.35} />
      <g transform={`translate(${side * 23} 0) scale(${1 + pinch * 0.15})`}>
        <circle r={6} fill={SKIN} stroke={INK} strokeWidth={2} />
        {pinch > 0.3 ? <path d={`M${side * 3} -5 l${side * 3} -3 M${side * 5} -1 l${side * 4} -1 M${side * 4} 3 l${side * 3} 2`} stroke={INK} strokeWidth={1.6} strokeLinecap="round" /> : null}
      </g>
    </g>
  );
  return (
    <div style={{ position: "relative", width: w, height: h, ...style }}>
      {shadow ? <div style={{ position: "absolute", left: w * 0.18, bottom: -h * 0.02, width: w * 0.64, height: h * 0.05, borderRadius: "50%", background: "rgba(0,0,0,0.28)", filter: `blur(${h * 0.01}px)`, scale: String(1 - bounce * 0.03) }} /> : null}
      <svg viewBox="0 0 100 150" width={w} height={h} style={{ position: "absolute", left: 0, bottom: 0, overflow: "visible" }}>
        <defs>
          <pattern id={ht} width={3.2} height={3.2} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <circle cx={1.6} cy={1.6} r={1} fill={INK} />
          </pattern>
          <pattern id={htR} width={3.2} height={3.2} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <circle cx={1.6} cy={1.6} r={0.8} fill="#fff" />
          </pattern>
          <clipPath id={headClip}>
            <circle cx={50} cy={50} r={34} />
          </clipPath>
          {/* screen-print misregistration: a red copy of the silhouette, slightly offset */}
          <filter id={mis} x="-20%" y="-20%" width="140%" height="140%">
            <feFlood floodColor={RED} floodOpacity={0.5} />
            <feComposite in2="SourceAlpha" operator="in" />
            <feOffset dx={2.4} dy={2.2} result="r" />
            <feMerge>
              <feMergeNode in="r" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g filter={`url(#${mis})`} transform={`translate(50 ${150 - bounce}) rotate(${tilt}) scale(${sx} ${sy}) translate(-50 -150)`}>
          {/* legs + shoes */}
          {[43, 57].map((hx, i) => (
            <g key={i} transform={`translate(${hx} ${120 + bodyDrop}) rotate(${footRot(legs, i, phase, t) * (i ? -1 : 1)})`}>
              <rect x={-4.5} y={0} width={9} height={sit ? 12 : 24} rx={4} fill={lower} stroke={INK} strokeWidth={2} />
              <ellipse cx={i ? 2 : -2} cy={sit ? 14 : 26} rx={7} ry={4.5} fill={shoe} stroke={INK} strokeWidth={2} />
              {!bow ? <rect x={i ? -2 : -6} y={sit ? 12.5 : 24.5} width={8} height={1.6} fill="#fff" /> : null}
            </g>
          ))}
          {/* hair behind the head (her bob) */}
          {bow ? (
            <>
              <path d="M14 52 C 10 14, 90 14, 86 52 L 86 64 Q 80 70 76 62 L 24 62 Q 20 70 14 64 Z" fill={INK} />
              <path d={`M78 28 C 97 26, ${104 + Math.sin(t * 3) * 2} 52, 95 80 C 92 87, 85 84, 88 75 C 94 56, 88 40, 75 36 Z`} fill={INK} />
            </>
          ) : null}
          {arm(-1, armL)}
          {arm(1, armR)}
          {/* torso */}
          <path d={`M31 ${84 + bodyDrop} Q31 ${78 + bodyDrop} 40 ${78 + bodyDrop} L60 ${78 + bodyDrop} Q69 ${78 + bodyDrop} 69 ${84 + bodyDrop} L70 ${122 + bodyDrop} Q50 ${126 + bodyDrop} 30 ${122 + bodyDrop} Z`} fill={jacket} stroke={INK} strokeWidth={2.2} />
          {bow ? (
            <>
              {/* white collar + buttons + skirt */}
              <path d={`M42 ${79 + bodyDrop} L50 ${87 + bodyDrop} L58 ${79 + bodyDrop}`} fill="#fff" stroke={INK} strokeWidth={1.6} />
              {[93, 101, 109].map((y) => <circle key={y} cx={50} cy={y + bodyDrop} r={1.4} fill={YEL} stroke={INK} strokeWidth={0.8} />)}
              <path d={`M30 ${112 + bodyDrop} L70 ${112 + bodyDrop} L74 ${126 + bodyDrop} L26 ${126 + bodyDrop} Z`} fill={INK} stroke={INK} strokeWidth={2} />
              <path d={`M30 ${112 + bodyDrop} L70 ${112 + bodyDrop} L74 ${126 + bodyDrop} L26 ${126 + bodyDrop} Z`} fill={`url(#${htR})`} opacity={0.35} />
            </>
          ) : (
            <>
              {/* yellow tee showing under the open jacket */}
              <path d={`M43 ${79 + bodyDrop} L57 ${79 + bodyDrop} L56 ${123 + bodyDrop} L44 ${123 + bodyDrop} Z`} fill={YEL} stroke={INK} strokeWidth={1.6} />
              <path d={`M43 ${79 + bodyDrop} L50 ${86 + bodyDrop} L57 ${79 + bodyDrop}`} fill="none" stroke={INK} strokeWidth={1.4} />
            </>
          )}
          {/* halftone shading on the shadow side of the torso */}
          <path d={`M58 ${80 + bodyDrop} L69 ${84 + bodyDrop} L70 ${122 + bodyDrop} L58 ${124 + bodyDrop} Z`} fill={`url(#${ht})`} opacity={0.4} />
          <path d={`M33 ${86 + bodyDrop} L37 ${84 + bodyDrop} L36 ${110 + bodyDrop} L33 ${112 + bodyDrop} Z`} fill={jacketHi} opacity={0.7} />
          {/* head */}
          {!bow ? (
            <>
              <circle cx={16.5} cy={55} r={5} fill={SKIN} stroke={INK} strokeWidth={2} />
              <circle cx={83.5} cy={55} r={5} fill={SKIN} stroke={INK} strokeWidth={2} />
            </>
          ) : null}
          <circle cx={50} cy={50} r={34} fill={SKIN} stroke={INK} strokeWidth={2.4} />
          {/* halftone crescent on the lower right of the face */}
          <g clipPath={`url(#${headClip})`}>
            <circle cx={66} cy={64} r={30} fill="none" stroke={`url(#${ht})`} strokeWidth={14} opacity={0.32} />
          </g>
          {/* hair */}
          {bow ? (
            <>
              <path d="M15 47 C 13 13, 87 11, 86 44 C 74 30, 54 25, 32 40 C 27 43, 21 46, 15 47 Z" fill={INK} />
              <path d="M36 20 Q 50 14 64 18" stroke="#4a4a4a" strokeWidth={2.4} fill="none" strokeLinecap="round" />
              {/* yellow bow tying the side ponytail */}
              <g transform="translate(81 29) rotate(28)">
                <path d="M0 0 L-8 -5 Q-9.5 0 -8 5 Z" fill={YEL} stroke={INK} strokeWidth={1.4} />
                <path d="M0 0 L8 -5 Q9.5 0 8 5 Z" fill={YEL} stroke={INK} strokeWidth={1.4} />
                <circle r={2.2} fill={RED} stroke={INK} strokeWidth={1} />
              </g>
            </>
          ) : (
            <>
              <path d="M15 56 C 8 22, 36 4, 58 8 C 84 12, 94 34, 86 56 L 82 42 L 75 47 L 69 34 L 60 43 L 52 31 L 44 42 L 35 33 L 28 45 L 22 38 Z" fill={INK} />
              <path d="M40 14 Q 54 9 68 15" stroke="#4a4a4a" strokeWidth={2.4} fill="none" strokeLinecap="round" />
              <path d="M58 6 q 4 -6 9 -5" stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round" />
            </>
          )}
          {/* face */}
          <Eye ex={38} e={expr} lx={lx} ly={lookY} blink={autoBlink} left />
          <Eye ex={62} e={expr} lx={lx} ly={lookY} blink={autoBlink} left={false} />
          <Mouth e={expr} />
          <Blush x={29} y={61} o={Math.max(blush, expr === "shy" ? 0.95 : expr === "love" ? 0.7 : 0.25)} />
          <Blush x={71} y={61} o={Math.max(blush, expr === "shy" ? 0.95 : expr === "love" ? 0.7 : 0.25)} />
        </g>
      </svg>
      {emote ? (
        <div
          style={{
            position: "absolute",
            left: w * 0.72,
            top: -h * 0.12,
            fontSize: h * 0.2,
            lineHeight: 1,
            fontWeight: 900,
            fontFamily: "sans-serif",
            color: emote === "♥" ? RED : emote === "anger" ? RED : emote === "sweat" ? "#5fb8ff" : YEL,
            WebkitTextStroke: emote === "sweat" || emote === "anger" || emote === "spark" ? undefined : `${Math.max(1, h * 0.006)}px ${INK}`,
            textShadow: `${h * 0.008}px ${h * 0.008}px 0 ${RED}`,
            scale: String(0.4 + ep * 0.6 + Math.sin(ep * Math.PI) * 0.3),
            opacity: ep,
            translate: `0 ${Math.sin(t * 3) * h * 0.012}px`,
          }}
        >
          {emote === "sweat" ? "💧" : emote === "spark" ? "✦" : emote === "anger" ? "💢" : emote === "z" ? "z Z" : emote}
        </div>
      ) : null}
    </div>
  );
};
