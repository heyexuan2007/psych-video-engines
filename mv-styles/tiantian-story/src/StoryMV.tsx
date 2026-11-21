import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { LyricPlace, Lyrics, Teaser } from "./components/Lyrics";
import { Finish } from "./components/World";
import { moodAt } from "./lib/theme";
import { prog } from "./lib/util";
import { ACT1 } from "./story/act1";
import { ACT2 } from "./story/act2";
import { ACT3 } from "./story/act3";
import { ACT4 } from "./story/act4";
import { Shot } from "./story/kit";

const SHOTS = [...ACT1, ...ACT2, ...ACT3, ...ACT4];

/** lyric position overrides where the top band is busy (1-based line numbers) */
const PLACE: Record<number, LyricPlace> = {
  6: { layout: "left", cy: 300 }, // phone on the right
};

/** Story version of the MV: one concrete shot per lyric line, told through 小团子's day. */
export const StoryMV: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const m = moodAt(t);
  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0b10", overflow: "hidden" }}>
      {SHOTS.map((s, i) => (
        <Shot key={i} t={t} a={s.a} b={s.b} tin={s.tin} dur={s.dur} ix={s.ix} iy={s.iy} name={s.name}>
          {(tt, p) => s.draw(tt, p)}
        </Shot>
      ))}
      <Finish t={t} m={m} />
      {/* album-cover print finish: yellow warmth + halftone dot screen over everything */}
      <AbsoluteFill style={{ background: "#ffd21f", mixBlendMode: "soft-light", opacity: 0.22 }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(27,26,20,0.55) 1.4px, transparent 1.9px) 0 0 / 7px 7px", mixBlendMode: "multiply", opacity: 0.14 }} />
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(215,38,61,0.5) 1.2px, transparent 1.7px) 3px 3px / 7px 7px", mixBlendMode: "multiply", opacity: 0.05 }} />
      <Lyrics t={t} story place={PLACE} />
      {t < 15.6 ? <Teaser t={t} idx={18} from={12.8} to={16.2} print /> : null}
      <AbsoluteFill style={{ backgroundColor: "#000", opacity: prog(t, 257.4, 258.8) }} />
      <Audio src={staticFile("song.mp3")} />
    </AbsoluteFill>
  );
};
