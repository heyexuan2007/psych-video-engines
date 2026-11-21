import React from "react";
import { AbsoluteFill } from "remotion";
import { POSES } from "./CharSheet";
import { PersonRig } from "./components/PersonRig";
import { SANS } from "./lib/theme";

/** Expression sheet for the screen-print style characters (not part of the MV). */
export const PersonSheet: React.FC = () => (
  <AbsoluteFill style={{ background: "#ffd21f" }}>
    <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(27,26,20,0.16) 1.6px, transparent 2px) 0 0 / 9px 9px" }} />
    <AbsoluteFill style={{ padding: "40px 60px", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gridTemplateRows: "1fr 1fr 1fr", gap: 6 }}>
      {POSES.map(([name, p], i) => (
        <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 0 }}>
            <PersonRig size={250} t={1} blink={false} {...p} />
            <PersonRig size={225} t={1} blink={false} bow {...p} emote={null} flip />
          </div>
          <div style={{ fontFamily: SANS, fontSize: 24, color: "#1b1a14", fontWeight: 800 }}>{name}</div>
        </div>
      ))}
    </AbsoluteFill>
  </AbsoluteFill>
);
