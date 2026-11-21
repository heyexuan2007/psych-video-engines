import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Lyrics, Teaser } from "./components/Lyrics";
import { Finish, Sky } from "./components/World";
import { moodAt } from "./lib/theme";
import { beatsIn, energyAt, prog, pulseAt } from "./lib/util";
import { CafeScene, FlightScene, FlipScene, IntroScene, OutroScene, TrafficScene } from "./scenes/Scenes";

/** white flash + camera kick at section hits */
const HITS = [5.35, 66.1, 153.1, 190.9];

const useT = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps;
};

type Render = (t: number, a: number, b: number) => React.ReactNode;

const SceneBody: React.FC<{ a: number; b: number; render: Render }> = ({ a, b, render }) => {
  const local = useT();
  return <>{render(a + local, a, b)}</>;
};

/** Scenes are placed by song time; each one reads the absolute song time so timings line up with the LRC. */
const Scene: React.FC<{ name: string; a: number; b: number; render: Render }> = ({ name, a, b, render }) => {
  const { fps } = useVideoConfig();
  return (
    <Sequence name={name} from={Math.round(a * fps)} durationInFrames={Math.round((b - a) * fps)}>
      <SceneBody a={a} b={b} render={render} />
    </Sequence>
  );
};

export const MV: React.FC = () => {
  const t = useT();
  const m = moodAt(t);
  const e = energyAt(t);
  const kick = Math.max(...HITS.map((h) => (t >= h ? Math.exp(-(t - h) * 3) : 0)));
  const cam = 1.02 + pulseAt(t) * 0.012 + kick * 0.06;
  const flash = Math.max(...HITS.map((h) => (t >= h ? Math.exp(-(t - h) * 5) : 0)));
  return (
    <AbsoluteFill style={{ backgroundColor: "#05070d", overflow: "hidden" }}>
      <AbsoluteFill style={{ scale: String(cam), filter: `brightness(${0.9 + e * 0.14})` }}>
        <Sky m={m} t={t} />
        <Scene name="开场 · 天天" a={0} b={17.2} render={(tt, a, b) => <IntroScene t={tt} m={moodAt(tt)} t0={a} t1={b} beats={beatsIn(5.3, 16.2, 2)} />} />
        <Scene name="主歌1 · 咖啡店窗边" a={16.4} b={46.8} render={(tt, a, b) => <CafeScene t={tt} m={moodAt(tt)} t0={a} t1={b} rainFrom={18.6} couple={[31.6, 41.6]} />} />
        <Scene name="导歌1 · 飞向远方" a={46.0} b={66.4} render={(tt, a, b) => <FlightScene t={tt} m={moodAt(tt)} t0={a} t1={b} fly={[50.9, 55.6]} glow={55.8} />} />
        <Scene name="副歌1 · 马路" a={65.9} b={100.2} render={(tt, a, b) => <TrafficScene t={tt} m={moodAt(tt)} t0={a} t1={b} li={10} />} />
        <Scene name="间奏 · 翻日历" a={100.2} b={104.0} render={(tt, a, b) => <FlipScene t={tt} m={moodAt(tt)} t0={a} t1={b} beats={beatsIn(100.8, 103.4)} startDay={8} />} />
        <Scene name="主歌2 · 雨夜窗边" a={103.4} b={134.2} render={(tt, a, b) => <CafeScene t={tt} m={moodAt(tt)} t0={a} t1={b} rainFrom={103} couple={[119.4, 129.2]} second />} />
        <Scene name="导歌2 · 飞向远方" a={133.4} b={153.4} render={(tt, a, b) => <FlightScene t={tt} m={moodAt(tt)} t0={a} t1={b} fly={[138.2, 142.9]} glow={143.1} />} />
        <Scene name="副歌2 · 马路" a={152.9} b={187.6} render={(tt, a, b) => <TrafficScene t={tt} m={moodAt(tt)} t0={a} t1={b} li={29} />} />
        <Scene name="过门 · 翻日历" a={186.8} b={191.4} render={(tt, a, b) => <FlipScene t={tt} m={moodAt(tt)} t0={a} t1={b} beats={beatsIn(187, 190.8)} startDay={15} />} />
        <Scene name="副歌3 · 马路" a={190.6} b={226.6} render={(tt, a, b) => <TrafficScene t={tt} m={moodAt(tt)} t0={a} t1={b} li={38} />} />
        <Scene name="尾声 · 天亮了" a={225.6} b={258.85} render={(tt, a, b) => <OutroScene t={tt} m={moodAt(tt)} t0={a} t1={b} loveAt={243.3} cardAt={248} />} />
        <Finish t={t} m={m} />
      </AbsoluteFill>
      <Lyrics t={t} />
      {t < 15.6 ? <Teaser t={t} idx={18} from={7.4} to={15.6} /> : null}
      <AbsoluteFill style={{ backgroundColor: "#fff", opacity: flash * 0.75 }} />
      <AbsoluteFill style={{ backgroundColor: "#000", opacity: prog(t, 257.4, 258.8) }} />
      <Audio src={staticFile("song.mp3")} />
    </AbsoluteFill>
  );
};
