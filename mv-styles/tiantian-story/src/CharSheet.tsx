import React from "react";
import { AbsoluteFill } from "remotion";
import { BunRig, Pose } from "./components/BunRig";
import { HER } from "./story/kit";
import { SANS } from "./lib/theme";

export const POSES: [string, Pose][] = [
  ["平静", { expr: "neutral" }],
  ["开心", { expr: "happy", armL: -40, armR: -40, pinch: 0.6 }],
  ["欢呼", { expr: "joy", armL: -80, armR: -80, pinch: 1, legs: "dangle", squash: -0.6, emote: "♪" }],
  ["心动", { expr: "love", armL: -30, armR: -30, blush: 1, emote: "♥" }],
  ["害羞", { expr: "shy", armL: 50, armR: 50, tilt: -6, lookX: -0.6 }],
  ["失落", { expr: "sad", armL: 60, armR: 60, squash: 0.4, tilt: 4, emote: "..." }],
  ["哭", { expr: "cry", armL: -60, armR: 40, pinch: 0.2, squash: 0.2 }],
  ["惊讶", { expr: "surprised", armL: -70, armR: -70, pinch: 1, squash: -0.4, emote: "!" }],
  ["叹气", { expr: "sigh", armL: 70, armR: 70, squash: 0.6, emote: "z" }],
  ["下定决心", { expr: "determined", armL: -20, armR: -100, pinch: 0.1, emote: "spark" }],
  ["紧张", { expr: "nervous", armL: 30, armR: 30, pinch: 0.8, emote: "sweat", tilt: 3 }],
  ["想念", { expr: "dreamy", lookY: -1, lookX: 0.5, armL: 20, armR: -30, emote: "?" }],
];

/** Expression sheet for checking the rig (not part of the MV). */
export const CharSheet: React.FC = () => (
  <AbsoluteFill style={{ background: "linear-gradient(180deg,#2b2f4a,#46405e)", padding: 60, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 30 }}>
    {POSES.map(([name, p], i) => (
      <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", gap: 24 }}>
        <div style={{ display: "flex", gap: 18, alignItems: "flex-end" }}>
          <BunRig size={200} t={1} blink={false} {...p} />
          {i % 3 === 0 ? <BunRig size={150} t={1} blink={false} color={HER} bow {...p} emote={null} /> : null}
        </div>
        <div style={{ fontFamily: SANS, fontSize: 30, color: "#fff", fontWeight: 700 }}>{name}</div>
      </div>
    ))}
  </AbsoluteFill>
);
