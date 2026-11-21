import React from "react";
import { SANS, SERIF } from "../lib/theme";
import { clamp01, easeOut, hash, lerp, mix, rgba } from "../lib/util";
import { INK, SKIN } from "./kit";

/* ───────── small objects ───────── */

/** tiny head of him / her in the screen-print style, for photos and avatars; (x, y) top-left, s = width */
export const MiniHead: React.FC<{ x: number; y: number; s: number; her?: boolean; body?: boolean }> = ({ x, y, s, her, body }) => (
  <div style={{ position: "absolute", left: x, top: y, width: s, height: s * (body ? 1.5 : 1) }}>
    {body ? <div style={{ position: "absolute", left: s * 0.2, top: s * 0.82, width: s * 0.6, height: s * 0.62, borderRadius: `${s * 0.15}px ${s * 0.15}px ${s * 0.06}px ${s * 0.06}px`, background: her ? "#d7263d" : "#262626", border: `${Math.max(1, s * 0.04)}px solid ${INK}`, boxSizing: "border-box" }}>
      {!her ? <div style={{ position: "absolute", left: "36%", top: 0, width: "28%", height: "100%", background: "#ffd21f" }} /> : null}
    </div> : null}
    {her ? <div style={{ position: "absolute", left: s * 0.78, top: s * 0.22, width: s * 0.22, height: s * 0.52, borderRadius: s * 0.12, background: INK }} /> : null}
    <div style={{ position: "absolute", left: 0, top: 0, width: s, height: s, borderRadius: "50%", background: SKIN, border: `${Math.max(1, s * 0.05)}px solid ${INK}`, boxSizing: "border-box", boxShadow: `${s * 0.04}px ${s * 0.04}px 0 rgba(215,38,61,0.5)` }} />
    <div style={{ position: "absolute", left: -s * 0.02, top: -s * 0.06, width: s * 1.04, height: s * 0.48, borderRadius: her ? `${s}px ${s}px ${s * 0.1}px ${s * 0.5}px` : `${s}px ${s}px ${s * 0.12}px ${s * 0.12}px`, background: INK }} />
    {her ? <div style={{ position: "absolute", left: s * 0.7, top: s * 0.08, width: s * 0.22, height: s * 0.16, background: "#ffd21f", clipPath: "polygon(0 0,50% 50%,0 100%,100% 0,50% 50%,100% 100%)" }} /> : null}
    <div style={{ position: "absolute", left: "30%", top: "52%", width: "9%", height: "15%", borderRadius: s, background: INK }} />
    <div style={{ position: "absolute", left: "61%", top: "52%", width: "9%", height: "15%", borderRadius: s, background: INK }} />
    <div style={{ position: "absolute", left: "20%", top: "70%", width: "14%", height: "8%", borderRadius: s, background: "rgba(215,38,61,0.6)" }} />
    <div style={{ position: "absolute", left: "66%", top: "70%", width: "14%", height: "8%", borderRadius: s, background: "rgba(215,38,61,0.6)" }} />
  </div>
);

/** umbrella; (x, y) = handle bottom. open 0..1 */
export const Umbrella: React.FC<{ x: number; y: number; size: number; open?: number; color?: string; tilt?: number }> = ({ x, y, size, open = 1, color = "#f2c14e", tilt = 0 }) => {
  const w = size * lerp(0.25, 1, easeOut(open));
  const h = size * 0.42;
  const dark = mix(color, "#000000", 0.25);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, rotate: `${tilt}deg`, transformOrigin: "0 0" }}>
      <div style={{ position: "absolute", left: -size * 0.012, top: -size * 0.95, width: size * 0.024, height: size * 0.95, background: "#3a2c24" }} />
      <div style={{ position: "absolute", left: -size * 0.012, top: -size * 0.06, width: size * 0.08, height: size * 0.06, borderRadius: `0 0 ${size * 0.05}px ${size * 0.05}px`, border: `${size * 0.018}px solid #3a2c24`, borderTop: "none" }} />
      <div
        style={{
          position: "absolute",
          left: -w / 2,
          top: -size * 0.95 - h,
          width: w,
          height: h,
          borderRadius: `${w / 2}px ${w / 2}px ${size * 0.04}px ${size * 0.04}px / ${h}px ${h}px ${size * 0.04}px ${size * 0.04}px`,
          background: `repeating-linear-gradient(90deg, ${color} 0 ${w / 6}px, ${dark} ${w / 6}px ${w / 3}px), ${color}`,
          boxShadow: `inset 0 ${-h * 0.25}px ${h * 0.3}px rgba(0,0,0,0.2), inset 0 ${h * 0.15}px ${h * 0.2}px rgba(255,255,255,0.35)`,
        }}
      />
      <div style={{ position: "absolute", left: -size * 0.02, top: -size * 0.95 - h - size * 0.06, width: size * 0.04, height: size * 0.07, background: "#3a2c24", borderRadius: size * 0.02 }} />
    </div>
  );
};

/** take-away / ceramic latte cup, side view. (x, y) = bottom centre */
export const Cup: React.FC<{ x: number; y: number; w: number; steam?: number; t?: number; paper?: boolean; color?: string }> = ({ x, y, w, steam = 1, t = 0, paper, color }) => {
  const h = w * 0.85;
  return (
    <div style={{ position: "absolute", left: x - w / 2, top: y - h, width: w, height: h }}>
      {steam > 0
        ? [0, 1, 2].map((k) => (
            <div
              key={k}
              style={{
                position: "absolute",
                left: w * (0.25 + k * 0.2),
                top: -w * 0.7 - ((t * 25 + k * 20) % (w * 0.4)),
                width: w * 0.12,
                height: w * 0.7,
                borderRadius: w,
                background: "linear-gradient(180deg, rgba(255,255,255,0), rgba(255,255,255,0.45), rgba(255,255,255,0))",
                rotate: `${Math.sin(t * 1.5 + k) * 16}deg`,
                filter: `blur(${w * 0.04}px)`,
                opacity: steam,
              }}
            />
          ))
        : null}
      {paper ? (
        <>
          <div style={{ position: "absolute", left: w * 0.08, top: h * 0.12, width: w * 0.84, height: h * 0.88, clipPath: "polygon(0 0, 100% 0, 88% 100%, 12% 100%)", background: `linear-gradient(90deg, #d9c7ae, #f5ead8 40%, #c9b394)` }} />
          <div style={{ position: "absolute", left: w * 0.16, top: h * 0.42, width: w * 0.68, height: h * 0.3, clipPath: "polygon(0 0, 100% 0, 96% 100%, 4% 100%)", background: color ?? "#7a4a2c" }} />
          <div style={{ position: "absolute", left: w * 0.02, top: 0, width: w * 0.96, height: h * 0.16, borderRadius: w * 0.04, background: "linear-gradient(180deg,#fdfaf4,#ddd2c2)" }} />
        </>
      ) : (
        <>
          <div style={{ position: "absolute", left: w * 0.82, top: h * 0.2, width: w * 0.36, height: w * 0.4, borderRadius: "50%", border: `${w * 0.09}px solid #e6dccd` }} />
          <div style={{ position: "absolute", left: 0, top: h * 0.08, width: w, height: h * 0.92, borderRadius: `${w * 0.06}px ${w * 0.06}px ${w * 0.42}px ${w * 0.42}px`, background: `linear-gradient(90deg,#d6cab9 0%,#fffdf8 30%,#f3ebe0 62%,#c4b6a4 100%)` }} />
          <div style={{ position: "absolute", left: w * 0.04, top: h * 0.06, width: w * 0.92, height: h * 0.15, borderRadius: "50%", background: `radial-gradient(ellipse at 45% 40%, ${color ?? "#b98557"}, #5b3420)` }} />
          <div style={{ position: "absolute", left: w * 0.13, top: h * 0.25, width: w * 0.09, height: h * 0.55, borderRadius: w, background: "rgba(255,255,255,0.75)", filter: `blur(${w * 0.015}px)` }} />
        </>
      )}
    </div>
  );
};

/** latte seen from above, with art that "pours" in (draw 0..1) */
export const LatteTop: React.FC<{ x: number; y: number; r: number; draw?: number; cool?: number }> = ({ x, y, r, draw = 1, cool = 0 }) => (
  <div style={{ position: "absolute", left: x - r * 1.35, top: y - r * 1.35, width: r * 2.7, height: r * 2.7 }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #ffffff, #e8ded0 60%, #cbbca8)", boxShadow: "0 20px 40px rgba(0,0,0,0.3)" }} />
    <div style={{ position: "absolute", left: r * 0.3, top: r * 0.3, width: r * 2.1, height: r * 2.1, borderRadius: "50%", background: "radial-gradient(circle at 45% 40%, #fbf6ee, #ece3d6)", boxShadow: "inset 0 4px 10px rgba(0,0,0,0.15)" }} />
    <div style={{ position: "absolute", left: r * 0.35, top: r * 0.35, width: r * 2, height: r * 2, borderRadius: "50%", background: `radial-gradient(circle at 50% 50%, ${mix("#b07a4f", "#6b4630", cool)} 0%, ${mix("#8a5532", "#4a2e1f", cool)} 70%, #5a3520 100%)` }} />
    <div
      style={{
        position: "absolute",
        left: r * 1.35 - r * 0.6,
        top: r * 1.35 - r * 0.62,
        width: r * 1.2,
        height: r * 1.2,
        fontSize: r * 1.25,
        lineHeight: `${r * 1.2}px`,
        textAlign: "center",
        color: mix("#fff6e6", "#c8b39a", cool),
        scale: String(0.2 + easeOut(draw) * 0.8),
        opacity: clamp01(draw * 2),
        filter: `blur(${r * 0.02 + cool * 3}px)`,
      }}
    >
      ♥
    </div>
  </div>
);

/** pixel heart (crisp) */
const HEART = [".XX...XX.", "XXXX.XXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."];
export const PixelHeart: React.FC<{ x: number; y: number; size: number; color?: string; glow?: number; style?: React.CSSProperties }> = ({ x, y, size, color = "#ff4d6d", glow = 0.6, style }) => (
  <svg viewBox="0 0 9 8" width={size} height={(size * 8) / 9} shapeRendering="crispEdges" style={{ position: "absolute", left: x - size / 2, top: y - (size * 4) / 9, overflow: "visible", filter: glow ? `drop-shadow(0 0 ${size * 0.15}px ${rgba(color, glow)})` : undefined, ...style }}>
    {HEART.flatMap((row, j) => [...row].map((c, i) => (c === "X" ? <rect key={`${i}-${j}`} x={i} y={j} width={1.02} height={1.02} fill={color} /> : null)))}
    <rect x={1} y={1} width={1} height={1} fill="rgba(255,255,255,0.6)" />
  </svg>
);

/** phone with a screen slot; (x, y) top-left */
export const Phone: React.FC<{ x: number; y: number; w: number; tilt?: number; children?: React.ReactNode; glow?: number; dark?: boolean }> = ({ x, y, w, tilt = 0, children, glow = 0.4, dark }) => {
  const h = w * 2.05;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, rotate: `${tilt}deg` }}>
      <div style={{ position: "absolute", inset: -w * 0.05, borderRadius: w * 0.17, background: "linear-gradient(135deg,#3b3f4a,#15171c)", boxShadow: `0 ${w * 0.08}px ${w * 0.2}px rgba(0,0,0,0.45), 0 0 ${w * 0.4}px ${rgba("#bcd6ff", glow * 0.5)}` }} />
      <div style={{ position: "absolute", inset: 0, borderRadius: w * 0.13, overflow: "hidden", background: dark ? "#10131c" : "#f4f1ec" }}>{children}</div>
      <div style={{ position: "absolute", left: w * 0.38, top: w * 0.03, width: w * 0.24, height: w * 0.06, borderRadius: w, background: "#111" }} />
    </div>
  );
};

export type Msg = { me?: boolean; text: string; at: number };
/** chat screen content (fills the phone screen, width w) */
export const ChatScreen: React.FC<{ w: number; t: number; title: string; msgs: Msg[]; typing?: string; typingAt?: number; caret?: boolean }> = ({ w, t, title, msgs, typing, caret = true }) => {
  const fs = w * 0.065;
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: SANS }}>
      <div style={{ height: w * 0.32, background: "#fbf8f3", borderBottom: "1px solid #e4ddd2", display: "flex", alignItems: "flex-end", padding: `0 ${w * 0.06}px ${w * 0.05}px`, gap: w * 0.04 }}>
        <div style={{ position: "relative", width: w * 0.13, height: w * 0.13 }}>
          <MiniHead x={0} y={0} s={w * 0.13} her />
        </div>
        <div style={{ fontSize: fs * 1.15, fontWeight: 800, color: "#333" }}>{title}</div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: w * 0.36, bottom: w * 0.3, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: w * 0.04, padding: w * 0.05 }}>
        {msgs.map((m, i) => {
          const p = clamp01((t - m.at) / 0.3);
          if (p <= 0) return null;
          return (
            <div
              key={i}
              style={{
                alignSelf: m.me ? "flex-end" : "flex-start",
                maxWidth: "78%",
                padding: `${w * 0.03}px ${w * 0.045}px`,
                borderRadius: w * 0.05,
                background: m.me ? "#ffb38a" : "#ffffff",
                color: "#2b2b2b",
                fontSize: fs,
                fontWeight: 600,
                boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
                scale: String(0.6 + easeOut(p) * 0.4),
                opacity: p,
                transformOrigin: m.me ? "100% 100%" : "0% 100%",
              }}
            >
              {m.text}
            </div>
          );
        })}
      </div>
      {typing !== undefined ? (
        <div style={{ position: "absolute", left: w * 0.05, right: w * 0.05, bottom: w * 0.08, height: w * 0.16, borderRadius: w * 0.08, background: "#fff", border: "1px solid #ddd", display: "flex", alignItems: "center", padding: `0 ${w * 0.05}px`, fontSize: fs, color: "#333", fontWeight: 600 }}>
          {typing}
          {caret && Math.floor(t * 2.5) % 2 === 0 ? <span style={{ width: 2, height: fs * 1.1, background: "#ff7a45", marginLeft: 2 }} /> : null}
        </div>
      ) : null}
    </div>
  );
};

/** tiny illustrated memory photos for Polaroids */
export const Memory: React.FC<{ kind: number; w: number }> = ({ kind, w }) => {
  const mini = (x: number, y: number, s: number, her: boolean) => <MiniHead x={x} y={y - s * 0.3} s={s * 0.62} her={her} body />;
  const scenes = [
    // ice cream at the park
    <>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#9fd3f5,#d9f0ff 60%,#9ad18b 60%)" }} />
      <div style={{ position: "absolute", left: w * 0.62, top: w * 0.18, width: w * 0.14, height: w * 0.14, borderRadius: "50%", background: "#fff3b0" }} />
      {mini(w * 0.15, w * 0.48, w * 0.3, false)}
      {mini(w * 0.52, w * 0.5, w * 0.28, true)}
      <div style={{ position: "absolute", left: w * 0.44, top: w * 0.36, width: w * 0.08, height: w * 0.08, borderRadius: "50%", background: "#ffb3c6" }} />
      <div style={{ position: "absolute", left: w * 0.455, top: w * 0.43, width: w * 0.05, height: w * 0.1, background: "#e3a35a", clipPath: "polygon(0 0,100% 0,50% 100%)" }} />
    </>,
    // the sea at sunset
    <>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#ff9e7a,#ffd39a 50%,#4a7fb5 50%,#2c4f80)" }} />
      <div style={{ position: "absolute", left: w * 0.38, top: w * 0.3, width: w * 0.24, height: w * 0.24, borderRadius: "50%", background: "#fff1c4", clipPath: "inset(0 0 50% 0)" }} />
      {mini(w * 0.18, w * 0.62, w * 0.26, false)}
      {mini(w * 0.5, w * 0.62, w * 0.26, true)}
    </>,
    // feeding a stray cat
    <>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#f3e2c9,#e9cfa9)" }} />
      <div style={{ position: "absolute", left: w * 0.55, top: w * 0.42, width: w * 0.3, height: w * 0.2, borderRadius: "50% 50% 40% 40%", background: "#555" }} />
      <div style={{ position: "absolute", left: w * 0.72, top: w * 0.32, width: w * 0.16, height: w * 0.15, borderRadius: "50%", background: "#555" }} />
      <div style={{ position: "absolute", left: w * 0.73, top: w * 0.27, width: w * 0.05, height: w * 0.07, background: "#555", clipPath: "polygon(50% 0,100% 100%,0 100%)" }} />
      <div style={{ position: "absolute", left: w * 0.82, top: w * 0.27, width: w * 0.05, height: w * 0.07, background: "#555", clipPath: "polygon(50% 0,100% 100%,0 100%)" }} />
      {mini(w * 0.08, w * 0.5, w * 0.26, false)}
      {mini(w * 0.3, w * 0.52, w * 0.24, true)}
    </>,
    // two lattes by the window
    <>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#8fb3d9,#c9dcef 70%,#8a5b3a 70%)" }} />
      {mini(w * 0.12, w * 0.5, w * 0.28, false)}
      {mini(w * 0.58, w * 0.5, w * 0.28, true)}
      <div style={{ position: "absolute", left: w * 0.43, top: w * 0.56, width: w * 0.14, height: w * 0.13, borderRadius: "0 0 40% 40%", background: "#fff" }} />
    </>,
  ];
  return <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>{scenes[kind % scenes.length]}</div>;
};

export const Polaroid: React.FC<{ x: number; y: number; w: number; kind: number; develop?: number; rot?: number; caption?: string }> = ({ x, y, w, kind, develop = 1, rot = 0, caption }) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, height: w * 1.2, rotate: `${rot}deg`, background: "#fbf8f1", boxShadow: "0 12px 26px rgba(0,0,0,0.35)", padding: w * 0.06, boxSizing: "border-box" }}>
    <div style={{ position: "relative", width: w * 0.88, height: w * 0.88, overflow: "hidden", background: "#1b1b1f" }}>
      <div style={{ position: "absolute", inset: 0, opacity: clamp01(develop), filter: `saturate(${develop}) brightness(${0.6 + develop * 0.4})` }}>
        <Memory kind={kind} w={w * 0.88} />
      </div>
    </div>
    {caption ? <div style={{ fontFamily: SERIF, fontSize: w * 0.09, color: "#6b5a4a", textAlign: "center", marginTop: w * 0.04 }}>{caption}</div> : null}
  </div>
);

export const Keys: React.FC<{ x: number; y: number; s: number; rot?: number }> = ({ x, y, s, rot = 0 }) => (
  <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, rotate: `${rot}deg` }}>
    <div style={{ position: "absolute", left: -s * 0.18, top: -s * 0.18, width: s * 0.36, height: s * 0.36, borderRadius: "50%", border: `${s * 0.05}px solid #d9c27a` }} />
    <div style={{ position: "absolute", left: s * 0.1, top: -s * 0.08, width: s * 0.75, height: s * 0.16, borderRadius: s * 0.03, background: "linear-gradient(180deg,#e8e8ee,#9a9aa6)" }} />
    <div style={{ position: "absolute", left: s * 0.55, top: s * 0.06, width: s * 0.08, height: s * 0.12, background: "#9a9aa6" }} />
    <div style={{ position: "absolute", left: s * 0.7, top: s * 0.06, width: s * 0.08, height: s * 0.08, background: "#9a9aa6" }} />
    <div style={{ position: "absolute", left: -s * 0.5, top: -s * 0.05, width: s * 0.36, height: s * 0.26, borderRadius: s * 0.08, background: "#ff7a45", rotate: "-20deg" }} />
  </div>
);

/** small bouquet; (x, y) = bottom of the stems */
export const Bouquet: React.FC<{ x: number; y: number; s: number; t?: number }> = ({ x, y, s, t = 0 }) => (
  <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0 }}>
    <div style={{ position: "absolute", left: -s * 0.22, top: -s * 0.6, width: s * 0.44, height: s * 0.6, background: "linear-gradient(90deg,#c9b8e8,#efe6ff,#b8a5dc)", clipPath: "polygon(0 0,100% 0,62% 100%,38% 100%)" }} />
    {Array.from({ length: 7 }, (_, i) => {
      const a = -0.9 + i * 0.3;
      const fx = Math.sin(a) * s * 0.34;
      const fy = -s * 0.62 - Math.cos(a) * s * 0.22 + Math.sin(t * 2 + i) * 2;
      const c = ["#ff6f91", "#ffc75f", "#ff9671", "#ffffff", "#ff6f91", "#f9f871", "#ff9671"][i];
      return (
        <div key={i} style={{ position: "absolute", left: fx - s * 0.11, top: fy - s * 0.11, width: s * 0.22, height: s * 0.22 }}>
          {[0, 1, 2, 3, 4].map((k) => (
            <div key={k} style={{ position: "absolute", left: s * 0.07, top: 0, width: s * 0.08, height: s * 0.11, borderRadius: "50%", background: c, rotate: `${k * 72}deg`, transformOrigin: `50% ${s * 0.11}px` }} />
          ))}
          <div style={{ position: "absolute", left: s * 0.08, top: s * 0.08, width: s * 0.06, height: s * 0.06, borderRadius: "50%", background: "#c47f1a" }} />
        </div>
      );
    })}
  </div>
);

/** bedside alarm clock; ring = shaking */
export const AlarmClock: React.FC<{ x: number; y: number; s: number; t: number; ring?: boolean; time?: string }> = ({ x, y, s, t, ring, time = "7:30" }) => {
  const sh = ring ? Math.sin(t * 60) * 6 : 0;
  return (
    <div style={{ position: "absolute", left: x - s / 2, top: y - s, width: s, height: s, rotate: `${sh}deg`, transformOrigin: "50% 100%" }}>
      {[-1, 1].map((d) => (
        <div key={d} style={{ position: "absolute", left: s / 2 + d * s * 0.32 - s * 0.14, top: -s * 0.06 + (ring ? Math.sin(t * 60 + d) * 3 : 0), width: s * 0.28, height: s * 0.2, borderRadius: `${s * 0.14}px ${s * 0.14}px 0 0`, background: "linear-gradient(180deg,#ffd9a0,#d8a25a)" }} />
      ))}
      <div style={{ position: "absolute", inset: `${s * 0.06}px 0 ${s * 0.08}px`, borderRadius: s * 0.18, background: "linear-gradient(160deg,#ff9b6b,#d9573a)", boxShadow: "0 10px 26px rgba(0,0,0,0.35)" }} />
      <div style={{ position: "absolute", left: s * 0.12, top: s * 0.22, width: s * 0.76, height: s * 0.44, borderRadius: s * 0.08, background: "#1d1d24", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 800, fontSize: s * 0.3, color: "#7dffb3", textShadow: "0 0 10px rgba(125,255,179,0.8)" }}>
        {time}
      </div>
      {[0.2, 0.8].map((p) => (
        <div key={p} style={{ position: "absolute", left: s * p - s * 0.05, top: s * 0.9, width: s * 0.1, height: s * 0.1, background: "#8a3a26" }} />
      ))}
      {ring
        ? [0, 1, 2].map((k) => (
            <div key={k} style={{ position: "absolute", left: s / 2 - s * (0.7 + k * 0.25), top: s / 2 - s * (0.7 + k * 0.25), width: s * (1.4 + k * 0.5), height: s * (1.4 + k * 0.5), borderRadius: "50%", border: "3px solid rgba(255,220,160,0.6)", opacity: ((t * 3 + k / 3) % 1) < 0.5 ? 0.7 - k * 0.2 : 0 }} />
          ))
        : null}
    </div>
  );
};

/* ───────── people (only legs / shoulders, original simple silhouettes) ───────── */

/** a pair of human legs walking or standing; (x, y) = ground point */
export const Legs: React.FC<{ x: number; y: number; h: number; t?: number; walk?: number; pants?: string; shoes?: string; skirt?: boolean }> = ({ x, y, h, t = 0, walk = 0, pants = "#3b4a6b", shoes = "#2a2a30", skirt }) => {
  const sw = Math.sin(t * 5 + x * 0.01) * 14 * walk;
  const leg = (dx: number, a: number) => (
    <div style={{ position: "absolute", left: dx, top: 0, width: h * 0.16, height: h, transformOrigin: "50% 0", rotate: `${a}deg` }}>
      <div style={{ position: "absolute", inset: `0 0 ${h * 0.06}px 0`, background: `linear-gradient(90deg, ${mix(pants, "#000", 0.25)}, ${pants} 40%, ${mix(pants, "#fff", 0.1)})`, borderRadius: `${h * 0.03}px` }} />
      <div style={{ position: "absolute", left: -h * 0.02, bottom: 0, width: h * 0.24, height: h * 0.07, borderRadius: `${h * 0.04}px ${h * 0.06}px ${h * 0.02}px ${h * 0.02}px`, background: shoes }} />
    </div>
  );
  return (
    <div style={{ position: "absolute", left: x - h * 0.2, top: y - h, width: h * 0.4, height: h }}>
      {leg(0, sw)}
      {leg(h * 0.2, -sw)}
      {skirt ? <div style={{ position: "absolute", left: -h * 0.08, top: -h * 0.05, width: h * 0.56, height: h * 0.35, background: pants, clipPath: "polygon(20% 0,80% 0,100% 100%,0 100%)" }} /> : null}
    </div>
  );
};

/** a person seen from behind / side at shoulder height; (x, y) = bottom centre */
export const Shoulders: React.FC<{ x: number; y: number; w: number; color: string; hair: string; lean?: number; longHair?: boolean; flip?: boolean }> = ({ x, y, w, color, hair, lean = 0, longHair, flip }) => (
  <div style={{ position: "absolute", left: x - w / 2, top: y - w * 1.15, width: w, height: w * 1.15, rotate: `${lean}deg`, transformOrigin: "50% 100%", scale: flip ? "-1 1" : undefined }}>
    <div style={{ position: "absolute", left: 0, top: w * 0.5, width: w, height: w * 0.7, borderRadius: `${w * 0.4}px ${w * 0.4}px 0 0`, background: `linear-gradient(90deg, ${mix(color, "#000", 0.2)}, ${color} 45%, ${mix(color, "#fff", 0.12)})` }} />
    <div style={{ position: "absolute", left: w * 0.31, top: w * 0.4, width: w * 0.16, height: w * 0.16, background: "#e9c3a0" }} />
    <div style={{ position: "absolute", left: w * 0.22, top: 0, width: w * 0.42, height: w * 0.48, borderRadius: "50%", background: "#f0cfae" }} />
    <div style={{ position: "absolute", left: w * 0.2, top: -w * 0.03, width: w * 0.46, height: longHair ? w * 0.75 : w * 0.3, borderRadius: longHair ? `${w * 0.25}px ${w * 0.25}px ${w * 0.08}px ${w * 0.08}px` : "50% 50% 30% 30%", background: hair }} />
  </div>
);

/** a hand (human) for handing things over; (x, y) = wrist, pointing left */
export const Hand: React.FC<{ x: number; y: number; s: number; sleeve?: string; flip?: boolean }> = ({ x, y, s, sleeve = "#3d5a80", flip }) => (
  <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, scale: flip ? "-1 1" : undefined }}>
    <div style={{ position: "absolute", left: 0, top: -s * 0.2, width: s * 1.4, height: s * 0.4, background: sleeve, borderRadius: s * 0.08 }} />
    <div style={{ position: "absolute", left: -s * 0.42, top: -s * 0.22, width: s * 0.5, height: s * 0.44, borderRadius: `${s * 0.22}px ${s * 0.1}px ${s * 0.1}px ${s * 0.22}px`, background: "#f0cfae" }} />
    <div style={{ position: "absolute", left: -s * 0.5, top: -s * 0.3, width: s * 0.2, height: s * 0.14, borderRadius: s * 0.07, background: "#e9c3a0" }} />
  </div>
);

/** rows of shop/café warm bokeh lights for interiors */
export const WarmBokeh: React.FC<{ t: number; n?: number; y0: number; y1: number; seed?: number; size?: number; opacity?: number }> = ({ t, n = 16, y0, y1, seed = 1, size = 1, opacity = 0.6 }) => (
  <>
    {Array.from({ length: n }, (_, i) => {
      const s = seed * 37 + i;
      const r = (20 + hash(s) * 50) * size;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: hash(s * 2.1) * 1920 - r + Math.sin(t * 0.3 + s) * 10,
            top: lerp(y0, y1, hash(s * 3.7)) - r,
            width: 2 * r,
            height: 2 * r,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${rgba(i % 3 ? "#ffcf8a" : "#ff9f6b", 0.5)} 0%, ${rgba("#ffcf8a", 0.25)} 60%, transparent 72%)`,
            opacity: opacity * (0.5 + hash(s * 5) * 0.5),
            mixBlendMode: "screen",
          }}
        />
      );
    })}
  </>
);
