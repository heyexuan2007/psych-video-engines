import React from "react";
import { SANS, SERIF } from "../lib/theme";
import { clamp01, easeIn, easeOut, hash } from "../lib/util";

const WEEK = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const WEEK_CN = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];

const Page: React.FC<{ day: number; w: number; h: number; accent: string; heart?: boolean }> = ({ day, w, h, accent, heart }) => {
  const wd = (day + 3) % 7;
  const red = wd === 0 || wd === 6;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg,#fffdf7 0%,#f4ede0 100%)",
        borderRadius: w * 0.04,
        boxShadow: "inset 0 -6px 18px rgba(80,50,20,0.12)",
        overflow: "hidden",
      }}
    >
      <div style={{ height: h * 0.2, background: accent, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 800, color: "#fff", fontSize: h * 0.085, letterSpacing: h * 0.02 }}>
        {WEEK[wd]}
      </div>
      <div style={{ textAlign: "center", fontFamily: SERIF, fontWeight: 900, fontSize: h * 0.5, lineHeight: 1.15, color: red ? "#d4483b" : "#2c2620", marginTop: h * 0.02 }}>{day}</div>
      <div style={{ textAlign: "center", fontFamily: SANS, fontWeight: 600, fontSize: h * 0.07, color: "#8a7a68", marginTop: -h * 0.02 }}>{WEEK_CN[wd]}</div>
      {heart ? (
        <div style={{ position: "absolute", right: w * 0.1, top: h * 0.26, fontSize: h * 0.13, color: "#e5486b", rotate: "12deg" }}>♥</div>
      ) : null}
    </div>
  );
};

/**
 * Tear-off desk calendar. `flips` = list of song-times when a page tears off; the day number counts up.
 */
export const Calendar: React.FC<{ t: number; flips: number[]; x: number; y: number; w: number; startDay?: number; accent?: string; heartFrom?: number }> = ({
  t,
  flips,
  x,
  y,
  w,
  startDay = 1,
  accent = "#e5486b",
  heartFrom = 999,
}) => {
  const h = w * 1.12;
  const done = flips.filter((f) => f <= t).length;
  const cur = flips[done - 1];
  const day = (n: number) => ((startDay - 1 + n) % 31) + 1;
  const tearP = cur !== undefined ? clamp01((t - cur) / 0.7) : 1;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h }}>
      {/* stand / rings */}
      <div style={{ position: "absolute", left: -w * 0.04, top: -h * 0.06, width: w * 1.08, height: h * 1.1, borderRadius: w * 0.06, background: "#3a2f2a", boxShadow: "0 30px 60px rgba(0,0,0,0.35)" }} />
      <div style={{ position: "absolute", inset: 0 }}>
        <Page day={day(done)} w={w} h={h} accent={accent} heart={done >= heartFrom} />
      </div>
      {/* page tearing off */}
      {cur !== undefined && tearP < 1 ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            transformOrigin: "50% 0%",
            transform: `perspective(${w * 4}px) rotateX(${easeIn(tearP) * 110}deg) translate(${(hash(done) - 0.5) * 2 * easeOut(tearP) * w * 0.6}px, ${easeIn(tearP) * h * 0.4}px) rotate(${(hash(done * 3) - 0.5) * 50 * tearP}deg)`,
            opacity: 1 - easeIn(tearP),
          }}
        >
          <Page day={day(done - 1)} w={w} h={h} accent={accent} heart={done - 1 >= heartFrom} />
        </div>
      ) : null}
      {[0.25, 0.5, 0.75].map((p) => (
        <div key={p} style={{ position: "absolute", left: w * p - w * 0.03, top: -h * 0.05, width: w * 0.06, height: h * 0.08, borderRadius: w * 0.03, background: "linear-gradient(90deg,#999,#eee,#888)" }} />
      ))}
    </div>
  );
};
