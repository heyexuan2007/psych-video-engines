import React from "react";
import { AbsoluteFill } from "remotion";
import { Calendar } from "./components/Calendar";
import { SANS, SERIF } from "./lib/theme";
import { Actor, INK } from "./story/kit";
import { Cup, Umbrella } from "./story/props";

/**
 * Covers in the MV's screen-print look: yellow halftone ground, the two (original) characters sharing
 * one red umbrella with their lattes, the title with a red misregistration shadow.
 */
export const Cover: React.FC<{ portrait: boolean }> = ({ portrait }) => {
  const w = portrait ? 1080 : 1440;
  const h = portrait ? 1440 : 1080;
  const titleSize = portrait ? 300 : 280;
  // characters: centred low in portrait, right half in landscape
  const cx = portrait ? w / 2 : w * 0.7;
  const gy = portrait ? h - 150 : h - 120;
  const s = portrait ? 400 : 380;
  return (
    <AbsoluteFill style={{ background: "#ffd21f", overflow: "hidden" }}>
      {/* halftone dots, denser towards one corner like a screen print */}
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(27,26,20,0.22) 2px, transparent 2.6px) 0 0 / 11px 11px", WebkitMaskImage: "linear-gradient(135deg, black 0%, transparent 70%)" }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(215,38,61,0.25) 2px, transparent 2.6px) 5px 5px / 11px 11px", WebkitMaskImage: "linear-gradient(315deg, black 0%, transparent 55%)" }} />
      {/* rain streaks around the umbrella */}
      <svg width={w} height={h} style={{ position: "absolute", left: 0, top: 0 }}>
        {Array.from({ length: 46 }, (_, i) => {
          const x = ((i * 137) % w) + 10;
          const y = ((i * 89) % h) - 40;
          return <line key={i} x1={x} y1={y} x2={x - 10} y2={y + 46} stroke={INK} strokeWidth={3} strokeLinecap="round" opacity={0.18} />;
        })}
      </svg>
      {/* the two of them under one umbrella */}
      <div style={{ position: "absolute", left: 0, top: 0, width: w, height: h }}>
        <Umbrella x={cx + 10} y={gy - s * 1.19 + s * 1.1 * 0.95} size={s * 1.1} color="#d7263d" tilt={-6} />
        <Actor x={cx - s * 0.27} y={gy} size={s} t={2} expr="shy" blush={1} lookX={1} armL={30} armR={-20} />
        <Actor x={cx + s * 0.29} y={gy} size={s * 0.93} t={2} her flip expr="happy" blush={0.8} lookX={1} armL={30} armR={-20} />
        <Cup x={cx + s * 0.01} y={gy - s * 0.4} w={s * 0.15} t={2} paper />
      </div>
      {/* small tear-off calendar with a heart */}
      <div style={{ position: "absolute", left: portrait ? 90 : 90, top: portrait ? h * 0.47 : h * 0.6, rotate: "-8deg" }}>
        <Calendar t={0} flips={[]} x={0} y={0} w={portrait ? 180 : 170} startDay={14} heartFrom={0} />
      </div>
      {/* title block */}
      <div style={{ position: "absolute", left: portrait ? 0 : 90, right: portrait ? 0 : undefined, top: portrait ? 110 : 150, textAlign: portrait ? "center" : "left" }}>
        <div style={{ fontFamily: SERIF, fontWeight: 900, fontSize: titleSize, lineHeight: 1, color: INK, letterSpacing: titleSize * 0.06, textShadow: `${titleSize * 0.035}px ${titleSize * 0.035}px 0 #d7263d` }}>天天</div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 22, marginTop: 26, padding: "10px 28px", background: INK, transform: "rotate(-2deg)" }}>
          <span style={{ fontFamily: SANS, fontWeight: 900, fontSize: portrait ? 72 : 66, color: "#ffd21f", letterSpacing: 20 }}>演唱者</span>
        </div>
      </div>
      {/* thin ink frame */}
      <AbsoluteFill style={{ border: `14px solid ${INK}`, boxSizing: "border-box" }} />
    </AbsoluteFill>
  );
};
