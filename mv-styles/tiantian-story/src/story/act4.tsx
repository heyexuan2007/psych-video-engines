import React from "react";
import { AbsoluteFill } from "remotion";
import { Calendar } from "../components/Calendar";
import { Rays } from "../components/World";
import { MOODS, SANS, SERIF, moodAt } from "../lib/theme";
import { DURATION, H, W, clamp01, easeIn, easeInOut, easeOut, easeOutBack, hash, lerp, prog, pulseAt, rgba } from "../lib/util";
import { Bedroom, ShotDef, Street, WindowBar } from "./act1";
import { Actor, Cam, Glow, Grey, HeartBurst, Ls, RainFx, SpeedLines, Twinkles, handAt, kf, since, tw } from "./kit";
import { AlarmClock, Bouquet, Cup, Legs, Phone, Polaroid, Umbrella } from "./props";

/* ───────── her building entrance (shared) ───────── */

const Entrance: React.FC<{ t: number; rain: number }> = ({ t, rain }) => (
  <AbsoluteFill>
    <Street t={t} rain={rain} night={1} />
    {/* building front with a lit doorway + striped awning */}
    <div style={{ position: "absolute", left: 1040, top: 330, width: 760, height: 560, background: "linear-gradient(180deg,#4a3a52,#2e2436)" }} />
    <div style={{ position: "absolute", left: 1280, top: 520, width: 280, height: 370, background: "linear-gradient(180deg,#ffd9a0,#f0a860)", boxShadow: "0 0 120px rgba(255,190,120,0.7)" }} />
    <div style={{ position: "absolute", left: 1000, top: 430, width: 840, height: 100, background: "repeating-linear-gradient(90deg,#d9455f 0 70px,#fff1e6 70px 140px)", clipPath: "polygon(0 0,100% 0,97% 100%,3% 100%)", boxShadow: "0 12px 20px rgba(0,0,0,0.35)" }} />
    {Array.from({ length: 10 }, (_, i) => <Glow key={i} x={1040 + i * 84} y={540} r={26} color="#ffd68c" a={0.6 + 0.4 * Math.sin(t * 2 + i)} />)}
    <div style={{ position: "absolute", left: 1000, top: 880, width: 840, height: 40, background: "#5a4a5e" }} />
    {/* the room upstairs where her light was on */}
    <div style={{ position: "absolute", left: 1460, top: 360, width: 120, height: 50, background: "#ffd27a", boxShadow: "0 0 50px rgba(255,210,122,0.8)" }} />
  </AbsoluteFill>
);

/* ───────── chorus 3: meeting her ───────── */

const chorus3: ShotDef[] = [
  {
    name: "39 她在楼下撑伞等，抱着花跑过去",
    a: 190.7,
    b: Ls(40) - 0.4,
    tin: "flash",
    draw: (t) => {
      const run = prog(t, 190.7, Ls(39) + 2.4);
      const x = lerp(-200, 1060, easeOut(run));
      const tip = handAt(340, 1, -50);
      const herTip = handAt(340, -1, -70, true);
      return (
        <>
          <Entrance t={t} rain={1} />
          <RainFx t={t} amount={1} />
          <Actor x={1420} y={890} size={340} t={t} her flip expr={kf(t, [[190.7, "neutral"], [Ls(39) + 0.6, "surprised"], [Ls(39) + 2.4, "joy"]])} emote={kf<"?" | "!" | "♥">(t, [[190.7, "?"], [Ls(39) + 0.6, "!"], [Ls(39) + 2.4, "♥"]])} emoteT={since(t, [190.7, Ls(39) + 0.6, Ls(39) + 2.4])} lookX={1} armR={-70} armL={t > Ls(39) + 2.4 ? -80 : 20} />
          <Umbrella x={1420 + herTip.x} y={890 + herTip.y + 20} size={320} color="#ff8fab" />
          <Actor x={x} y={900} size={340} t={t} legs={run < 1 ? "run" : "stand"} phase={t * 3.2} expr={run < 1 ? "joy" : "shy"} blush={run} emote={run < 1 ? "♪" : "♥"} emoteT={since(t, [190.7, Ls(39) + 2.4])} armR={-50} armL={-30} tilt={run < 1 ? -8 : 0} />
          <Bouquet x={x + tip.x} y={900 + tip.y + 10} s={220} t={t} />
          {/* splashes at each step */}
          {run < 1
            ? Array.from({ length: 10 }, (_, i) => {
                const q = (t * 3.2 + i / 10) % 1;
                return <div key={i} style={{ position: "absolute", left: x - 60 + hash(i) * 120 - q * 80, top: 890 - Math.sin(q * Math.PI) * 80, width: 12, height: 16, borderRadius: "50%", background: "rgba(220,235,255,0.8)", opacity: 1 - q }} />;
              })
            : null}
          {run < 1 ? <SpeedLines t={t} cx={x} cy={760} opacity={0.35} n={24} /> : null}
        </>
      );
    },
  },
  {
    name: "40 屋檐下并排站着，路人匆匆，两个人像被定格",
    a: Ls(40) - 0.4,
    b: Ls(41) - 0.4,
    tin: "fade",
    dur: 0.5,
    draw: (t) => (
      <>
        <Entrance t={t} rain={1} />
        <RainFx t={t * 0.25} amount={1} />
        {/* passers-by streaking past (fast, blurred) while the two stay still */}
        <AbsoluteFill style={{ filter: "blur(6px)" }}>
          {Array.from({ length: 5 }, (_, i) => {
            const x = ((i * 520 + (t - Ls(40)) * 1400 * (i % 2 ? 1 : -1)) % 2600 + 2600) % 2600 - 340;
            return <Legs key={i} x={x} y={1000} h={560} t={t * 3} walk={1} pants={["#2a3448", "#4a2a3a", "#2a2a2a", "#3a4a3a", "#5a4a3a"][i]} shoes="#111" />;
          })}
        </AbsoluteFill>
        <Actor x={1250} y={880} size={300} t={t} expr="nervous" emote="sweat" emoteT={t - Ls(40)} lookX={1} armL={30} armR={30} blush={0.8} />
        <Actor x={1580} y={880} size={300} t={t} her flip expr="shy" lookX={1} armL={30} armR={30} blush={0.8} />
        <Bouquet x={1340} y={820} s={160} t={t} />
        <Twinkles t={t} x={1415} y={760} r={260} n={8} color="#ffd0dc" />
      </>
    ),
  },
  {
    name: "41 黑白漫画格：紧张得说不出话，她歪头",
    a: Ls(41) - 0.4,
    b: Ls(42) - 0.4,
    tin: "wipe",
    draw: (t) => {
      const p2 = easeOutBack(prog(t, Ls(41) + 1.4, Ls(41) + 1.9), 1.6);
      return (
        <>
          <AbsoluteFill style={{ background: "#f4f1ea" }} />
          <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(0,0,0,0.12) 2px, transparent 2.5px) 0 0 / 22px 22px" }} />
          {/* panel 1 */}
          <div style={{ position: "absolute", left: 120, top: 300, width: 820, height: 640, border: "10px solid #111", background: "#fff", overflow: "hidden", rotate: "-2deg" }}>
            <AbsoluteFill style={{ background: "repeating-conic-gradient(from 0deg at 50% 60%, rgba(0,0,0,0.08) 0deg 4deg, transparent 4deg 12deg)" }} />
            <Actor x={410} y={600} size={460} t={t} expr="nervous" emote="sweat" emoteT={t - Ls(41)} armL={40 + Math.sin(t * 14) * 8} armR={40 - Math.sin(t * 14) * 8} tilt={Math.sin(t * 12) * 3} blush={1} />
            <div style={{ position: "absolute", left: 520, top: 40, fontFamily: SANS, fontWeight: 900, fontSize: 80, color: "#111" }}>那个…</div>
          </div>
          {/* panel 2 */}
          <div style={{ position: "absolute", left: 1000, top: 300, width: 800, height: 640, border: "10px solid #111", background: "#fff", overflow: "hidden", rotate: "2deg", scale: String(clamp01(p2)), opacity: clamp01(p2 * 2) }}>
            <Actor x={400} y={600} size={440} t={t} her expr="neutral" emote="?" emoteT={t - Ls(41) - 1.6} tilt={-14} lookX={-0.6} armL={20} armR={-40} />
          </div>
          <Grey amount={1} />
        </>
      );
    },
  },
  {
    name: "42 她递来一杯拿铁：变回彩色，雨停了",
    a: Ls(42) - 0.4,
    b: Ls(43) - 0.4,
    tin: "cut",
    draw: (t) => {
      const give = easeOut(prog(t, Ls(42) - 0.2, Ls(42) + 0.6));
      const reveal = easeInOut(prog(t, Ls(42) + 0.5, Ls(42) + 2.0));
      const rain = 1 - easeInOut(prog(t, Ls(42) + 0.8, Ls(42) + 2.4));
      const m = moodAt(t);
      return (
        <>
          <Entrance t={t} rain={rain} />
          <RainFx t={t} amount={rain} />
          {/* moonlight breaking through as the rain stops */}
          <Glow x={500} y={180} r={420} color="#fff2d0" a={0.7 * (1 - rain)} />
          <Rays m={m} t={t} strength={0.6 * (1 - rain)} />
          <Actor x={1250} y={880} size={320} t={t} expr={kf(t, [[Ls(42) - 0.4, "nervous"], [Ls(42) + 0.6, "surprised"], [Ls(42) + 1.6, "love"]])} emote={kf<"!" | "♥" | null>(t, [[Ls(42) - 0.4, null], [Ls(42) + 0.6, "!"], [Ls(42) + 1.6, "♥"]])} emoteT={since(t, [Ls(42) + 0.6, Ls(42) + 1.6])} lookX={1} armR={-40} armL={30} />
          <Actor x={1580} y={880} size={320} t={t} her flip expr="happy" lookX={1} armR={-20} armL={20} emote="♪" emoteT={t - Ls(42)} />
          <Cup x={lerp(1500, 1380, give)} y={lerp(800, 740, give)} w={90} t={t} paper />
          <Grey amount={1} reveal={reveal} cx={1390} cy={700} />
        </>
      );
    },
  },
  {
    name: "43 肩靠肩（和第 4 句的情侣同一个构图）",
    a: Ls(43) - 0.4,
    b: Ls(44) - 0.4,
    tin: "blur",
    draw: (t) => {
      const lean = easeInOut(prog(t, Ls(43), Ls(43) + 1.6));
      return (
        <>
          <Entrance t={t} rain={0} />
          <Cam s={tw(t, [[Ls(43) - 0.4, 1.0], [Ls(44), 1.35]])} ox={72} oy={78}>
            <div style={{ position: "absolute", left: 1150, top: 870, width: 560, height: 30, borderRadius: 15, background: "#6a5a6e" }} />
            <Actor x={1300} y={880} size={300} t={t} legs="sit" expr="shy" blush={1} lookX={1} tilt={lean * 8} armR={30} armL={40} />
            <Cup x={1180} y={880} w={70} t={t} paper />
            <Actor x={1540 - lean * 40} y={880} size={290} t={t} her flip legs="sit" expr={lean > 0.6 ? "happy" : "shy"} blush={1} tilt={-lean * 14} armL={30} armR={30} />
            <HeartBurst t={t} t0={Ls(43) + 1.4} x={1420} y={700} n={10} spread={220} dur={2.4} size={44} />
          </Cam>
        </>
      );
    },
  },
  {
    name: "44 手机相册：照片飞出来排成心形",
    a: Ls(44) - 0.4,
    b: Ls(45) - 0.4,
    tin: "zoom",
    draw: (t) => {
      const N = 10;
      return (
        <>
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 55%, #5a3a5a, #1e1424)" }} />
          <Phone x={860} y={640} w={200} tilt={0} glow={1}>
            <AbsoluteFill style={{ background: "linear-gradient(180deg,#ffe9f0,#ffd6e2)" }} />
          </Phone>
          {Array.from({ length: N }, (_, i) => {
            const st = Ls(44) - 0.2 + i * 0.22;
            const q = easeOutBack(prog(t, st, st + 0.8), 1.3);
            const a = (i / N) * Math.PI * 2;
            // heart curve
            const hx = 16 * Math.pow(Math.sin(a), 3);
            const hy = -(13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a));
            const tx = 960 + hx * 22 - 80;
            const ty = 600 + hy * 20 - 90;
            return q > 0 ? <Polaroid key={i} x={lerp(880, tx, clamp01(q))} y={lerp(700, ty, clamp01(q))} w={160} kind={i % 4} rot={(hash(i) - 0.5) * 20} develop={prog(t, st + 0.4, st + 1.2)} /> : null;
          })}
          <Actor x={520} y={1020} size={300} t={t} expr="joy" emote="♪" emoteT={t - Ls(44)} lookX={1} lookY={-0.6} armL={-60} armR={-60} />
          <Actor x={1400} y={1020} size={290} t={t} her flip expr="love" emote="♥" emoteT={t - Ls(44) - 0.5} lookX={1} lookY={-0.6} armL={-60} armR={-60} />
        </>
      );
    },
  },
  {
    name: "45-47 一起唱「第十八」，雨滴变成爱心，镜头环绕",
    a: Ls(45) - 0.4,
    b: 226.6,
    tin: "flash",
    draw: (t) => {
      const morph = easeInOut(prog(t, Ls(45), Ls(46) + 1));
      const beat = pulseAt(t);
      const orbit = Math.sin((t - Ls(45)) * 0.35) * 6;
      return (
        <>
          <Entrance t={t} rain={0.4} />
          <Cam s={1.05 + beat * 0.02} r={orbit} x={Math.sin((t - Ls(45)) * 0.35) * 60}>
            <Actor x={1280} y={880} size={330} t={t} expr={kf(t, [[Ls(45), "joy"], [Ls(47), "love"]])} emote="♪" emoteT={since(t, [Ls(45), Ls(46), Ls(47)])} armL={-80 + beat * 30} armR={-80 + beat * 30} pinch={1} squash={-beat * 0.3} />
            <Actor x={1580} y={880} size={320} t={t} her flip expr={kf(t, [[Ls(45), "joy"], [Ls(47), "love"]])} emote="♥" emoteT={since(t, [Ls(45) + 0.3, Ls(46) + 0.3, Ls(47) + 0.3])} armL={-80 + beat * 30} armR={-80 + beat * 30} pinch={1} squash={-beat * 0.3} />
          </Cam>
          {/* rain → hearts */}
          {Array.from({ length: 70 }, (_, i) => {
            const sp = 260 + hash(i * 2.1) * 260;
            const y = ((hash(i * 1.9) * (H + 200) + t * sp) % (H + 200)) - 100;
            const x = hash(i * 6.7) * W;
            const k = clamp01(morph * 1.4 - hash(i * 3.3) * 0.4);
            return k < 0.5 ? (
              <div key={i} style={{ position: "absolute", left: x, top: y, width: 3, height: 40, borderRadius: 2, background: "rgba(220,235,255,0.6)", opacity: 1 - k * 2 }} />
            ) : (
              <div key={i} style={{ position: "absolute", left: x - 16, top: y - 16, fontSize: 26 + hash(i) * 30, color: ["#ff4d6d", "#ff8fab", "#ffd27a"][i % 3], opacity: (k - 0.5) * 2 * 0.9, rotate: `${Math.sin(t * 2 + i) * 20}deg`, filter: "drop-shadow(0 0 8px rgba(255,120,150,0.7))" }}>
                ♥
              </div>
            );
          })}
          {[Ls(46), Ls(47), Ls(47) + 2.4].map((tt, i) => (
            <HeartBurst key={i} t={t} t0={tt} x={1430} y={620} n={24} spread={760} dur={2.8} rise={380} />
          ))}
        </>
      );
    },
  },
];

/* ───────── outro: the next morning ───────── */

const outro: ShotDef[] = [
  {
    name: "尾声：第二天早上，撕到 3，上面画了心",
    a: 226.2,
    b: Ls(48) - 0.6,
    tin: "iris",
    draw: (t) => {
      const ring = t < 228.6;
      const tear = 231.5;
      return (
        <>
          <Bedroom t={t} light={1} />
          <Cam s={tw(t, [[226.2, 1.0], [Ls(48), 1.12]])} ox={55}>
            <div style={{ position: "absolute", left: 260, top: 820, width: 600, height: 36, background: "linear-gradient(180deg,#a87650,#7a5236)", borderRadius: 8 }} />
            <AlarmClock x={420} y={830} s={240} t={t} ring={ring} time="7:30" />
            {/* this time the hero is already up, and taps the alarm off happily */}
            <Actor x={tw(t, [[226.2, 700], [228.4, 600], [229.6, 720], [tear - 0.6, 980]])} y={830} size={300} t={t} legs={t > 229.6 && t < tear - 0.6 ? "walk" : "stand"} phase={t * 2} expr={kf(t, [[226.2, "happy"], [tear, "joy"]])} emote={kf<"♪" | "♥">(t, [[226.2, "♪"], [tear, "♥"]])} emoteT={since(t, [226.2, tear])} armL={t < 228.6 ? -100 : -30} armR={t > tear - 0.6 && t < tear + 0.3 ? -80 : -30} squash={Math.abs(Math.sin(t * 4)) * 0.15} />
            <div style={{ position: "absolute", left: 0, top: 0 }}>
              <Calendar t={t} flips={[tear]} x={1100} y={260} w={380} startDay={2} heartFrom={1} />
            </div>
          </Cam>
        </>
      );
    },
  },
  {
    name: "48 咖啡店角落：两杯拿铁并排，两个人一起喝",
    a: Ls(48) - 0.6,
    b: Ls(49) - 0.6,
    tin: "fade",
    dur: 0.8,
    draw: (t) => {
      const m = MOODS.sunny;
      return (
        <WindowBar t={t} rain={0} drops={0} blurOut={6} mood={m}>
          <Rays m={m} t={t} strength={1} />
          <Cam s={tw(t, [[Ls(48) - 0.6, 1.08], [Ls(49), 1.0]])}>
            <Actor x={780} y={760} size={300} t={t} expr={kf(t, [[Ls(48) - 0.6, "happy"], [Ls(48) + 2.2, "shy"]])} blush={0.6} lookX={1} armR={-40} armL={20} />
            <Actor x={1160} y={760} size={290} t={t} her flip expr="happy" lookX={1} armR={-40} armL={20} emote="♪" emoteT={t - Ls(48)} />
            <Cup x={920} y={760} w={100} t={t} />
            <Cup x={1030} y={760} w={100} t={t} />
            <HeartBurst t={t} t0={Ls(48) + 0.4} x={975} y={560} n={10} spread={200} dur={2.6} size={40} />
          </Cam>
        </WindowBar>
      );
    },
  },
  {
    name: "49 她在起雾的窗上画一颗心",
    a: Ls(49) - 0.6,
    b: 248.6,
    tin: "zoom",
    draw: (t) => {
      const d = easeInOut(prog(t, Ls(49) - 0.3, Ls(49) + 1.8));
      // heart path drawn as a stroke that reveals clear glass
      const heart = "M960 760 C 760 620, 700 440, 840 380 C 910 350, 950 400, 960 440 C 970 400, 1010 350, 1080 380 C 1220 440, 1160 620, 960 760 Z";
      const len = 1500;
      return (
        <>
          <AbsoluteFill style={{ filter: "blur(6px)" }}>
            <Street t={t} rain={0} />
          </AbsoluteFill>
          <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
            <defs>
              <mask id="fogHeart">
                <rect width={W} height={H} fill="white" />
                <path d={heart} fill="none" stroke="black" strokeWidth={46} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - d)} />
              </mask>
            </defs>
            <rect width={W} height={H} fill="rgba(235,240,245,0.7)" mask="url(#fogHeart)" />
          </svg>
          <div style={{ position: "absolute", inset: 0, border: "50px solid #5a3b28" }} />
          {/* her hand-tip following the stroke; the hero watching, blushing */}
          <Actor x={1360} y={940} size={340} t={t} her expr={d < 1 ? "happy" : "joy"} armL={-70} armR={20} lookX={-1} lookY={-0.6} emote={d >= 1 ? "♥" : null} emoteT={t - Ls(49) - 1.8} />
          <Actor x={560} y={960} size={330} t={t} expr={d < 0.6 ? "surprised" : "love"} blush={d} lookX={1} lookY={-0.6} armL={-30} armR={-30} emote={d > 0.6 ? "♥" : "!"} emoteT={since(t, [Ls(49) - 0.3, Ls(49) + 0.9])} />
          <Twinkles t={t} x={960} y={560} r={300} n={12} opacity={prog(t, Ls(49) + 1.6, Ls(49) + 2.2)} color="#ffd0dc" />
        </>
      );
    },
  },
  {
    name: "片尾：歌名 + 两个人挥手",
    a: 248.6,
    b: DURATION,
    tin: "fade",
    dur: 1.0,
    draw: (t) => {
      const c = easeOut(prog(t, 249, 250.4));
      const wave = Math.sin(t * 5) * 30;
      return (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(180deg,#2b3c6e 0%,#c77f8c 60%,#f6c08a 100%)" }} />
          <Glow x={1280} y={420} r={500} color="#ffd9a0" a={0.7} />
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 260 }}>
            <div style={{ fontFamily: SERIF, fontWeight: 900, fontSize: 210, color: "#fff", letterSpacing: 40, opacity: c, scale: String(lerp(1.2, 1, c)), filter: `blur(${(1 - c) * 12}px)`, textShadow: "0 10px 40px rgba(0,0,0,0.35)" }}>天天</div>
            <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 64, color: "#ffe2b0", letterSpacing: 24, opacity: easeOut(prog(t, 249.8, 251)), marginTop: 6 }}>演唱者</div>
          </AbsoluteFill>
          <Actor x={820} y={960} size={260} t={t} expr="joy" armL={-20} armR={-90 + wave} pinch={1} />
          <Actor x={1100} y={960} size={250} t={t} her flip expr="happy" armL={-20} armR={-90 - wave} pinch={1} blush={0.6} />
          <Twinkles t={t} x={960} y={420} r={600} n={14} />
          <AbsoluteFill style={{ background: rgba("#000000", easeIn(prog(t, 256.6, DURATION))) }} />
        </>
      );
    },
  },
];

export const ACT4: ShotDef[] = [...chorus3, ...outro];
