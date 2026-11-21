import React from "react";
import { AbsoluteFill } from "remotion";
import { Pose } from "../components/BunRig";
import { PersonRig } from "../components/PersonRig";
import { H, LINES, W, clamp01, easeInOut, easeOut, hash, lerp, prog, rgba } from "../lib/util";

/* ───────── timing helpers ───────── */

/** start / end of lyric line n (1-based, matches the storyboard) */
export const Ls = (n: number) => LINES[n - 1].start;
export const Le = (n: number) => LINES[n - 1].end;

/** step keyframes: value of the last key whose time ≤ t */
export const kf = <T,>(t: number, keys: [number, T][]): T => {
  let v = keys[0][1];
  for (const [k, val] of keys) if (t >= k) v = val;
  return v;
};
/** time since the last key whose time ≤ t (for pop-in of emotes etc.) */
export const since = (t: number, times: number[]) => {
  let s = 99;
  for (const k of times) if (t >= k) s = t - k;
  return s;
};
/** eased numeric tween through keys */
export const tw = (t: number, keys: [number, number][], ease = easeInOut) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [a, va] = keys[i];
    const [b, vb] = keys[i + 1];
    if (t < b) return lerp(va, vb, ease((t - a) / (b - a)));
  }
  return keys[keys.length - 1][1];
};

/* ───────── shots + transitions ───────── */

export type Trans = "cut" | "fade" | "whip" | "whipL" | "iris" | "zoom" | "wipe" | "push" | "blur" | "flash";

/**
 * A shot lives in [a, b) of song time. It keeps rendering 0.6 s past b so the next shot can
 * transition over it (later shots are stacked on top).
 */
export const Shot: React.FC<{ t: number; a: number; b: number; tin?: Trans; dur?: number; ix?: number; iy?: number; name?: string; children: (t: number, p: number) => React.ReactNode }> = ({
  t,
  a,
  b,
  tin = "cut",
  dur = 0.5,
  ix = 50,
  iy = 50,
  children,
}) => {
  if (t < a || t > b + 0.6) return null;
  const p = clamp01((t - a) / dur);
  const e = easeOut(p);
  const st: React.CSSProperties = {};
  switch (tin) {
    case "fade":
      st.opacity = p;
      break;
    case "whip":
    case "whipL":
      st.transform = `translateX(${(1 - e) * W * 0.7 * (tin === "whip" ? 1 : -1)}px)`;
      st.filter = p < 1 ? `blur(${(1 - e) * 26}px)` : undefined;
      break;
    case "iris":
      st.clipPath = `circle(${easeInOut(p) * 120}% at ${ix}% ${iy}%)`;
      break;
    case "zoom":
      st.transform = `scale(${lerp(1.5, 1, e)})`;
      st.opacity = clamp01(p * 2);
      st.filter = p < 1 ? `blur(${(1 - e) * 16}px)` : undefined;
      break;
    case "wipe":
      st.clipPath = `inset(0 ${(1 - easeInOut(p)) * 100}% 0 0)`;
      break;
    case "push":
      st.transform = `translateY(${(1 - e) * H}px)`;
      break;
    case "blur":
      st.opacity = p;
      st.filter = p < 1 ? `blur(${(1 - p) * 24}px)` : undefined;
      break;
    default:
      break;
  }
  const flash = tin === "flash" ? Math.max(0, 1 - (t - a) / 0.35) : 0;
  return (
    <AbsoluteFill style={{ overflow: "hidden", ...st }}>
      {children(t, prog(t, a, b))}
      {flash > 0 ? <AbsoluteFill style={{ background: "#fff", opacity: flash }} /> : null}
    </AbsoluteFill>
  );
};

/** camera: scale/translate around a focus point */
export const Cam: React.FC<{ s?: number; x?: number; y?: number; r?: number; ox?: number; oy?: number; children: React.ReactNode }> = ({ s = 1, x = 0, y = 0, r = 0, ox = 50, oy = 50, children }) => (
  <AbsoluteFill style={{ transformOrigin: `${ox}% ${oy}%`, transform: `translate(${x}px, ${y}px) scale(${s}) rotate(${r}deg)` }}>{children}</AbsoluteFill>
);

/* ───────── actors ───────── */

/** accent colours for him (yellow tee) and her (red cardigan), used for avatars / pins */
export const LEAD = "#ffd21f";
export const HER = "#d7263d";
/** ink + skin of the screen-print characters */
export const INK = "#1b1a14";
export const SKIN = "#ffe6c2";

/** people are narrower than the old round character, so every actor is drawn this much bigger */
export const ACTOR_SCALE = 1.25;

/** character placed by its feet: (x, y) = bottom centre. */
export const Actor: React.FC<Pose & { x: number; y: number; size: number; t: number; her?: boolean; z?: number; style?: React.CSSProperties }> = ({ x, y, size, her, ...pose }) => (
  <div style={{ position: "absolute", left: x - (size * ACTOR_SCALE * 0.95) / 3, top: y - size * ACTOR_SCALE * 0.95, width: (size * ACTOR_SCALE * 0.95) / 1.5, height: size * ACTOR_SCALE * 0.95 }}>
    <PersonRig size={size * ACTOR_SCALE} bow={her} {...pose} />
  </div>
);

/** hand position (px) relative to an Actor's feet point, ignoring squash/tilt */
export const handAt = (size: number, side: -1 | 1, angle: number, flip = false) => {
  // PersonRig viewBox is 100 × 150 (feet at 150); shoulders at (32, 92) / (68, 92), hand 23 units out
  const k = (size * ACTOR_SCALE * 0.95) / 150;
  const a = (angle * Math.PI) / 180;
  let X = side < 0 ? 32 - 23 * Math.cos(a) : 68 + 23 * Math.cos(a);
  const Y = 92 + 23 * Math.sin(a);
  if (flip) X = 100 - X;
  return { x: (X - 50) * k, y: (Y - 150) * k };
};

/* ───────── effects ───────── */

export const SpeedLines: React.FC<{ t: number; cx?: number; cy?: number; n?: number; opacity?: number; color?: string }> = ({ t, cx = W / 2, cy = H / 2, n = 46, opacity = 1, color = "#ffffff" }) => (
  <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0, opacity }}>
    {Array.from({ length: n }, (_, i) => {
      const a = (i / n) * Math.PI * 2 + hash(i) * 0.1;
      const ph = (t * 3 + hash(i * 3)) % 1;
      const r0 = 380 + ph * 500 + hash(i * 7) * 200;
      const r1 = r0 + 160 + hash(i * 5) * 260;
      return (
        <line key={i} x1={cx + Math.cos(a) * r0} y1={cy + Math.sin(a) * r0} x2={cx + Math.cos(a) * r1} y2={cy + Math.sin(a) * r1} stroke={color} strokeWidth={2 + hash(i * 9) * 5} strokeLinecap="round" opacity={0.25 + hash(i * 2) * 0.5} />
      );
    })}
  </svg>
);

/** hearts bursting / floating from a point */
export const HeartBurst: React.FC<{ t: number; t0: number; x: number; y: number; n?: number; spread?: number; dur?: number; colors?: string[]; size?: number; rise?: number }> = ({
  t,
  t0,
  x,
  y,
  n = 18,
  spread = 420,
  dur = 2.2,
  colors = ["#ff4d6d", "#ff8fab", "#ffd27a"],
  size = 46,
  rise = 220,
}) => {
  const q0 = (t - t0) / dur;
  if (q0 < 0 || q0 > 1.3) return null;
  return (
    <>
      {Array.from({ length: n }, (_, i) => {
        const q = clamp01(q0 - hash(i * 3.3) * 0.25);
        if (q <= 0 || q >= 1) return null;
        const a = -Math.PI / 2 + (hash(i * 1.7) - 0.5) * Math.PI * 1.6;
        const d = spread * (0.4 + hash(i * 2.9) * 0.6) * easeOut(q);
        const c = colors[i % colors.length];
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + Math.cos(a) * d - size / 2,
              top: y + Math.sin(a) * d * 0.7 - q * rise - size / 2,
              fontSize: size * (0.6 + hash(i * 4.1) * 0.8),
              lineHeight: 1,
              color: c,
              opacity: Math.sin(Math.min(1, q * 1.3) * Math.PI) * 0.95,
              rotate: `${(hash(i) - 0.5) * 60 + Math.sin(t * 4 + i) * 12}deg`,
              filter: `drop-shadow(0 0 10px ${rgba(c, 0.7)})`,
            }}
          >
            ♥
          </div>
        );
      })}
    </>
  );
};

/** grey-out overlay; colour can come back as a circle growing from (cx, cy) */
export const Grey: React.FC<{ amount: number; reveal?: number; cx?: number; cy?: number }> = ({ amount, reveal = 0, cx = W / 2, cy = H / 2 }) => {
  if (amount <= 0.001) return null;
  const r = reveal * 2300;
  return (
    <AbsoluteFill
      style={{
        backdropFilter: `grayscale(${amount}) contrast(${1 + amount * 0.12}) brightness(${1 - amount * 0.12})`,
        WebkitMaskImage: reveal > 0 ? `radial-gradient(circle at ${cx}px ${cy}px, transparent ${r}px, black ${r + 60}px)` : undefined,
      }}
    />
  );
};

/** sparkle dots around a point */
export const Twinkles: React.FC<{ t: number; x: number; y: number; r?: number; n?: number; color?: string; opacity?: number }> = ({ t, x, y, r = 120, n = 8, color = "#ffe08a", opacity = 1 }) => (
  <>
    {Array.from({ length: n }, (_, i) => {
      const a = i * 2.4 + t * (0.4 + hash(i) * 0.5);
      const rr = r * (0.6 + 0.4 * Math.sin(t * 1.3 + i));
      const tw2 = Math.abs(Math.sin(t * (2 + hash(i * 3) * 2) + i));
      const s = 6 + hash(i * 5) * 10;
      return (
        <div key={i} style={{ position: "absolute", left: x + Math.cos(a) * rr - s / 2, top: y + Math.sin(a) * rr * 0.7 - s / 2, width: s, height: s, opacity: opacity * tw2, color, fontSize: s * 1.6, lineHeight: `${s}px`, textAlign: "center", textShadow: `0 0 8px ${color}` }}>
          ✦
        </div>
      );
    })}
  </>
);

/** speech / thought bubble */
export const Bubble: React.FC<{ x: number; y: number; w: number; h: number; p: number; tail?: "left" | "right" | "down"; think?: boolean; bg?: string; children?: React.ReactNode }> = ({
  x,
  y,
  w,
  h,
  p,
  tail = "down",
  think,
  bg = "#fffaf2",
  children,
}) => {
  if (p <= 0) return null;
  const s = 0.3 + easeOut(p) * 0.7 + Math.sin(clamp01(p) * Math.PI) * 0.08;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, scale: String(s), opacity: clamp01(p * 2.5), transformOrigin: tail === "left" ? "0% 100%" : tail === "right" ? "100% 100%" : "50% 100%" }}>
      <div style={{ position: "absolute", inset: 0, borderRadius: Math.min(w, h) * 0.45, background: bg, boxShadow: "0 10px 30px rgba(0,0,0,0.25)" }} />
      {think ? (
        <>
          <div style={{ position: "absolute", left: w * 0.3, top: h + 6, width: 26, height: 26, borderRadius: "50%", background: bg }} />
          <div style={{ position: "absolute", left: w * 0.24, top: h + 38, width: 14, height: 14, borderRadius: "50%", background: bg }} />
        </>
      ) : (
        <div
          style={{
            position: "absolute",
            left: tail === "left" ? 30 : tail === "right" ? w - 70 : w / 2 - 20,
            top: h - 4,
            width: 40,
            height: 34,
            background: bg,
            clipPath: tail === "right" ? "polygon(0 0, 100% 0, 90% 100%)" : tail === "left" ? "polygon(0 0, 100% 0, 10% 100%)" : "polygon(0 0, 100% 0, 50% 100%)",
          }}
        />
      )}
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>{children}</div>
    </div>
  );
};

/** falling rain streaks (cheap) */
export const RainFx: React.FC<{ t: number; amount: number; angle?: number; color?: string; n?: number }> = ({ t, amount, angle = 0.18, color = "#dfe9f5", n = 140 }) => {
  if (amount < 0.02) return null;
  return (
    <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
      {Array.from({ length: Math.round(n * amount) }, (_, i) => {
        const sp = 1300 * (0.7 + hash(i * 2.1) * 0.6);
        const len = 50 * (0.6 + hash(i * 4.3) * 0.8);
        const y = ((hash(i * 1.9) * (H + 200) + t * sp) % (H + 200)) - 100;
        const x = hash(i * 6.7) * (W + 300) - y * angle;
        return <line key={i} x1={x} y1={y} x2={x - len * angle} y2={y + len} stroke={color} strokeWidth={1.4} strokeLinecap="round" opacity={0.35 * amount * (0.5 + hash(i * 3.7) * 0.5)} />;
      })}
    </svg>
  );
};

/** soft light pool / glow */
export const Glow: React.FC<{ x: number; y: number; r: number; color: string; a?: number }> = ({ x, y, r, color, a = 0.6 }) => (
  <div style={{ position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: "50%", background: `radial-gradient(circle, ${rgba(color, a)} 0%, ${rgba(color, a * 0.3)} 40%, transparent 70%)`, pointerEvents: "none" }} />
);
