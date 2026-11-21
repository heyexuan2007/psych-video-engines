import React from "react";
import { AbsoluteFill } from "remotion";
import { Skyline } from "../components/World";
import { SANS, moodAt } from "../lib/theme";
import { H, W, clamp01, easeIn, easeInOut, easeOut, easeOutBack, hash, lerp, prog, pulseAt, rgba } from "../lib/util";
import { CafeBack, MapView, ShotDef, Street, WindowBar } from "./act1";
import { Cabin, NavJam, Wheel, Windshield } from "./act2";
import { Actor, Cam, Glow, Grey, HeartBurst, Ls, RainFx, SpeedLines, Twinkles, handAt, kf, since, tw } from "./kit";
import { Bouquet, ChatScreen, Cup, Hand, LatteTop, Legs, Memory, MiniHead, Phone, Umbrella } from "./props";

/* ───────── verse 2: the same day, at night ───────── */

const verse2: ShotDef[] = [
  {
    name: "20 夜里出门，路灯下又撑开伞",
    a: 103.6,
    b: Ls(21) - 0.4,
    tin: "fade",
    dur: 0.6,
    draw: (t) => {
      const x = tw(t, [[103.6, 520], [Ls(21) - 0.4, 1000]]);
      const open = prog(t, Ls(20) + 0.6, Ls(20) + 1.2);
      const tip = handAt(300, 1, -70);
      return (
        <>
          <Street t={t} rain={1} night={1} />
          <RainFx t={t} amount={1} />
          {/* streetlight cone */}
          <div style={{ position: "absolute", left: 1180, top: 260, width: 16, height: 620, background: "#1a1a22" }} />
          <div style={{ position: "absolute", left: 1120, top: 250, width: 120, height: 26, borderRadius: 13, background: "#1a1a22" }} />
          <div style={{ position: "absolute", left: 880, top: 270, width: 600, height: 620, background: "linear-gradient(180deg, rgba(255,214,140,0.45), rgba(255,214,140,0.05))", clipPath: "polygon(45% 0, 55% 0, 100% 100%, 0 100%)" }} />
          <Glow x={1180} y={280} r={140} color="#ffd68c" a={0.9} />
          {/* long shadow stretching away from the lamp */}
          <div style={{ position: "absolute", left: x - 520, top: 868, width: 520, height: 40, borderRadius: "50%", background: "linear-gradient(90deg, transparent, rgba(0,0,0,0.45))", opacity: 0.8 }} />
          <Actor x={x} y={880} size={300} t={t} legs="walk" phase={t * 1.6} expr={kf(t, [[103.6, "neutral"], [Ls(20) + 1.6, "sigh"]])} emote={t > Ls(20) + 1.6 ? "..." : null} emoteT={t - Ls(20) - 1.6} armR={-70} armL={20} />
          <Umbrella x={x + tip.x} y={880 + tip.y + 20} size={300} open={open} color="#5a8fd9" />
        </>
      );
    },
  },
  {
    name: "21 夜里店里没人，店员直接递来同一杯",
    a: Ls(21) - 0.4,
    b: Ls(22) - 0.4,
    tin: "whip",
    draw: (t) => {
      const give = easeOut(prog(t, Ls(21) + 0.6, Ls(21) + 1.4));
      return (
        <>
          <CafeBack t={t} night={1} />
          <div style={{ position: "absolute", left: 1000, top: 560, width: 920, height: 520, background: "linear-gradient(180deg,#6a4a32,#3a2618)" }} />
          <div style={{ position: "absolute", left: 990, top: 545, width: 940, height: 28, background: "#b08a68" }} />
          <div style={{ position: "absolute", left: 0, top: 940, width: W, height: 140, background: "repeating-linear-gradient(90deg,#4a3428 0 120px,#40302a 120px 240px)" }} />
          {/* wall clock: late */}
          <div style={{ position: "absolute", left: 300, top: 160, width: 160, height: 160, borderRadius: "50%", background: "#fffaf2", border: "8px solid #3a2a20" }}>
            <div style={{ position: "absolute", left: 76, top: 26, width: 8, height: 56, background: "#333", rotate: "290deg", transformOrigin: "50% 100%" }} />
            <div style={{ position: "absolute", left: 77, top: 40, width: 6, height: 42, background: "#333", rotate: "240deg", transformOrigin: "50% 100%" }} />
          </div>
          {/* empty floor, chairs up on tables */}
          {[200, 600].map((x, i) => (
            <div key={i} style={{ position: "absolute", left: x, top: 700, width: 260, height: 20, borderRadius: 10, background: "#5a3b28" }}>
              <div style={{ position: "absolute", left: 120, top: 20, width: 20, height: 240, background: "#3a2618" }} />
            </div>
          ))}
          <Actor x={860} y={960} size={280} t={t} expr={kf(t, [[Ls(21) - 0.4, "neutral"], [Ls(21) + 0.6, "surprised"], [Ls(21) + 1.5, "happy"]])} emote={kf<"!" | "♥" | null>(t, [[Ls(21) - 0.4, null], [Ls(21) + 0.6, "!"], [Ls(21) + 1.5, "♥"]])} emoteT={since(t, [Ls(21) + 0.6, Ls(21) + 1.5])} lookX={1} lookY={-0.8} armL={t > Ls(21) + 1.4 ? -80 : 20} armR={t > Ls(21) + 1.4 ? -80 : 20} />
          <Hand x={lerp(1250, 1000, give)} y={lerp(420, 760, give)} s={160} sleeve="#2f4a3a" />
          <Cup x={lerp(1250, 1000, give) - 90} y={lerp(420, 760, give) + 40} w={90} t={t} paper />
          {/* a small heart doodled on the cup sleeve */}
          <div style={{ position: "absolute", left: lerp(1250, 1000, give) - 110, top: lerp(420, 760, give) - 30, color: "#e5486b", fontSize: 30 }}>♥</div>
        </>
      );
    },
  },
  {
    name: "22 同一个角落，多买的一杯放在对面",
    a: Ls(22) - 0.4,
    b: Ls(23) - 0.4,
    tin: "fade",
    dur: 0.6,
    draw: (t) => {
      const place = easeOutBack(prog(t, Ls(22) + 0.4, Ls(22) + 1.2), 1.5);
      return (
        <WindowBar t={t} rain={1}>
          <Cam s={tw(t, [[Ls(22) - 0.4, 1.0], [Ls(23), 1.22]])} ox={60} oy={70}>
            <Actor x={760} y={760} size={300} t={t} expr={kf(t, [[Ls(22) - 0.4, "happy"], [Ls(22) + 2.4, "dreamy"], [Ls(22) + 5.0, "sad"]])} emote={kf<"♪" | "?" | "..." | null>(t, [[Ls(22) - 0.4, "♪"], [Ls(22) + 2.4, "?"], [Ls(22) + 5.0, "..."]])} emoteT={since(t, [Ls(22) - 0.4, Ls(22) + 2.4, Ls(22) + 5.0])} lookX={kf(t, [[Ls(22) - 0.4, 1], [Ls(22) + 2.4, 1], [Ls(22) + 3.6, -0.6], [Ls(22) + 4.4, 1]])} armR={t < Ls(22) + 1.2 ? -20 : 30} armL={30} />
            <Cup x={980} y={760} w={110} t={t} />
            {/* the second cup, set down for her on the empty seat across */}
            <Cup x={lerp(900, 1320, Math.min(1, place))} y={760 - Math.sin(clamp01(place) * Math.PI) * 60} w={110} t={t} />
            <div style={{ position: "absolute", left: 1230, top: 800, width: 180, height: 30, borderRadius: 15, background: "#3a2a20" }} />
            <div style={{ position: "absolute", left: 1310, top: 830, width: 24, height: 250, background: "#2a1e18" }} />
          </Cam>
        </WindowBar>
      );
    },
  },
  {
    name: "23 窗外一对情侣共撑一把伞走过",
    a: Ls(23) - 0.4,
    b: Ls(24) - 0.4,
    tin: "blur",
    draw: (t) => {
      const walk = prog(t, Ls(23) - 0.4, Ls(24) - 0.2);
      const cx = lerp(-200, 2100, walk);
      return (
        <>
          <Street t={t} rain={1} night={1} />
          <RainFx t={t} amount={1} />
          {/* two people under one umbrella, walking past (legs + umbrella) */}
          <Legs x={cx - 50} y={900} h={420} t={t} walk={0.8} pants="#2a3448" shoes="#111" />
          <Legs x={cx + 60} y={900} h={400} t={t + 0.3} walk={0.8} pants="#8a3a4a" shoes="#eee" skirt />
          <Umbrella x={cx + 10} y={700} size={430} color="#d9455f" />
          <HeartBurst t={t} t0={Ls(23) + 0.6} x={cx} y={420} n={6} spread={160} dur={2.5} size={34} />
          {/* window glass + the hero inside, foreground blurred, watching */}
          <AbsoluteFill style={{ background: "linear-gradient(115deg, rgba(150,180,220,0.18), rgba(40,60,90,0.12))" }} />
          <div style={{ position: "absolute", inset: 0, filter: "blur(8px)" }}>
            <Actor x={300} y={1150} size={560} t={t} expr="sad" lookX={1} armL={40} armR={-10} shadow={false} />
          </div>
          <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 36, background: "#2c1c12" }} />
        </>
      );
    },
  },
  {
    name: "24 对面那杯的热气慢慢没了",
    a: Ls(24) - 0.4,
    b: Ls(25) - 0.5,
    tin: "zoom",
    draw: (t) => {
      const cool = easeInOut(prog(t, Ls(24), Ls(24) + 4.5));
      return (
        <>
          <AbsoluteFill style={{ background: "repeating-linear-gradient(90deg, rgba(0,0,0,0.05) 0 3px, transparent 3px 13px), linear-gradient(180deg,#6a4a32,#3e2a1c)" }} />
          <WarmSteam t={t} amount={1 - cool} />
          <LatteTop x={1180} y={640} r={230} cool={cool} />
          {/* clock reflection on the table: time passing */}
          <div style={{ position: "absolute", left: 1500, top: 260, fontFamily: SANS, fontWeight: 300, fontSize: 70, color: "rgba(255,240,220,0.6)" }}>{["21:40", "21:55", "22:10", "22:25"][Math.min(3, Math.floor(cool * 4))]}</div>
          <Actor x={540} y={1000} size={420} t={t} expr={kf(t, [[Ls(24) - 0.4, "sad"], [Ls(24) + 3.6, "cry"]])} lookX={1} lookY={0.4} squash={0.25 + cool * 0.2} armL={50} armR={30} emote={cool > 0.5 ? "..." : null} emoteT={t - Ls(24) - 2.2} />
        </>
      );
    },
  },
  {
    name: "25 打字「我想你」，删掉，又打",
    a: Ls(25) - 0.5,
    b: Ls(26) - 0.4,
    tin: "push",
    draw: (t) => {
      const full = "我想你";
      const t0 = Ls(25) - 0.2;
      // type 3 chars, pause, delete, pause, type again
      const n = t < t0 + 1.2 ? Math.floor(clamp01((t - t0) / 1.2) * 3.99) : t < t0 + 1.8 ? 3 : t < t0 + 2.4 ? 3 - Math.floor(clamp01((t - t0 - 1.8) / 0.6) * 3.99) : t < t0 + 2.7 ? 0 : Math.floor(clamp01((t - t0 - 2.7) / 0.9) * 3.99);
      return (
        <>
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 60% 40%, #3a2c40, #15111c)" }} />
          <Cam s={tw(t, [[Ls(25) - 0.5, 1.0], [Ls(26), 1.1]])}>
            <Phone x={1080} y={320} w={340} tilt={-3}>
              <ChatScreen w={380} t={t} title="她 ♡" msgs={[{ text: "晚安 🌙", at: 0 }]} typing={full.slice(0, n)} />
            </Phone>
            <Actor x={640} y={980} size={480} t={t} expr="nervous" emote="sweat" emoteT={t - Ls(25) + 0.5} lookX={1} lookY={-0.6} armR={-40 + Math.sin(t * 20) * 6} armL={30} tilt={Math.sin(t * 3) * 3} />
          </Cam>
        </>
      );
    },
  },
];

/** steam that thins out as the cup cools */
const WarmSteam: React.FC<{ t: number; amount: number }> = ({ t, amount }) => (
  <>
    {[0, 1, 2, 3].map((k) => (
      <div key={k} style={{ position: "absolute", left: 1100 + k * 40, top: 160 - ((t * 40 + k * 40) % 120), width: 40, height: 260, borderRadius: 20, background: "linear-gradient(180deg, rgba(255,255,255,0), rgba(255,255,255,0.35), rgba(255,255,255,0))", rotate: `${Math.sin(t * 1.3 + k) * 14}deg`, filter: "blur(10px)", opacity: amount }} />
    ))}
  </>
);

/* ───────── pre-chorus 2: both thinking of each other ───────── */

const pre2: ShotDef[] = [
  {
    name: "26-27 心再一次飞过夜里的城市",
    a: Ls(26) - 0.4,
    b: Ls(28) - 0.4,
    tin: "iris",
    draw: (t) => {
      const route = easeInOut(prog(t, Ls(26), Ls(27) + 3.4));
      return (
        <Cam s={tw(t, [[Ls(26) - 0.4, 1.5], [Ls(27), 1.25], [Ls(28), 1.1]])} ox={lerp(18, 82, route)} oy={lerp(78, 22, route)} r={tw(t, [[Ls(26) - 0.4, 4], [Ls(28), -2]])}>
          <MapView t={t} route={route} night={1} lit={easeOut(prog(t, Ls(27) + 2.8, Ls(27) + 3.6))} />
        </Cam>
      );
    },
  },
  {
    name: "28 分屏：两个人同时盯着手机",
    a: Ls(28) - 0.4,
    b: Ls(29) - 0.4,
    tin: "wipe",
    draw: (t) => {
      const seam = Math.max(0, 1 - Math.abs(t - Ls(28) - 0.3) * 3);
      const half = (her: boolean) => (
        <div style={{ position: "absolute", left: her ? W / 2 + 6 : 0, top: 0, width: W / 2 - 6, height: H, overflow: "hidden", background: her ? "radial-gradient(ellipse at 50% 60%, #7a4a5a, #2a1a24)" : "radial-gradient(ellipse at 50% 60%, #5a4a3a, #1e1a14)" }}>
          <Phone x={her ? 120 : 560} y={300} w={250} tilt={her ? 6 : -6}>
            <AbsoluteFill style={{ background: her ? "#ffe9d6" : "#ffe1ea", display: "flex", alignItems: "center", justifyContent: "center" }}>
              {/* the other one's avatar */}
              <div style={{ position: "relative", width: 150, height: 150 }}>
                <MiniHead x={0} y={0} s={150} her={!her} />
              </div>
            </AbsoluteFill>
          </Phone>
          <Actor x={her ? 640 : 320} y={1000} size={420} t={t} her={her} expr="dreamy" lookX={her ? -1 : 1} lookY={-0.6} armL={-30} armR={-30} emote="♥" emoteT={t - Ls(28) - (her ? 0.4 : 0)} blush={0.6} />
        </div>
      );
      return (
        <>
          <AbsoluteFill style={{ background: "#fff" }} />
          {half(false)}
          {half(true)}
          <AbsoluteFill style={{ background: `linear-gradient(90deg, transparent 47%, rgba(255,255,255,${seam}) 50%, transparent 53%)` }} />
          <Twinkles t={t} x={W / 2} y={540} r={200} n={10} color="#ffd0dc" />
        </>
      );
    },
  },
  {
    name: "29 按下发送，冲出咖啡店",
    a: Ls(29) - 0.4,
    b: 152.9,
    tin: "zoom",
    draw: (t) => {
      const press = Ls(29) + 0.5;
      const wave = prog(t, press, press + 0.8);
      const runAt = Ls(29) + 2.4;
      const run = prog(t, runAt, 152.9);
      if (t < runAt) {
        return (
          <>
            <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #3a3040, #15111c)" }} />
            <Cam s={tw(t, [[Ls(29) - 0.4, 1.3], [press, 1.0]])}>
              <Phone x={780} y={300} w={340} glow={wave > 0 ? 1 : 0.4}>
                <ChatScreen w={340} t={t} title="她 ♡" msgs={[{ text: "晚安 🌙", at: 0 }, { me: true, text: "我想你。我现在去找你！", at: press }]} typing={t < press ? "我想你。我现在去找你！" : ""} caret={t < press} />
              </Phone>
              {/* the send tap: a mitten pressing + shockwave */}
              <div style={{ position: "absolute", left: 1040, top: lerp(620, 760, Math.sin(clamp01((t - press + 0.2) / 0.4) * Math.PI)), width: 130, height: 110, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #fff3df, #ffe6c2 60%, #f0cfa0)", border: "6px solid #1b1a14", boxSizing: "border-box", boxShadow: "5px 5px 0 rgba(215,38,61,0.5)" }} />
              {wave > 0 && wave < 1 ? <div style={{ position: "absolute", left: 1100 - wave * 900, top: 840 - wave * 900, width: wave * 1800, height: wave * 1800, borderRadius: "50%", border: `${20 * (1 - wave)}px solid rgba(255,190,140,${1 - wave})` }} /> : null}
            </Cam>
          </>
        );
      }
      const x = lerp(700, 2200, easeIn(run));
      return (
        <WindowBar t={t} rain={1}>
          <Actor x={x} y={1000} size={300} t={t} legs="run" phase={t * 3.4} expr="determined" emote="spark" emoteT={t - runAt} armL={-40} armR={20} tilt={-8} />
          <SpeedLines t={t} cx={x} cy={850} opacity={0.8} />
          <Cup x={1320} y={760} w={110} t={t} steam={0} />
          {/* the bell over the door swinging */}
          <div style={{ position: "absolute", left: 1700, top: 60, rotate: `${Math.sin(t * 18) * 25 * (1 - run)}deg`, transformOrigin: "50% 0" }}>
            <div style={{ width: 4, height: 60, background: "#888", marginLeft: 38 }} />
            <div style={{ width: 80, height: 70, borderRadius: "40px 40px 10px 10px", background: "linear-gradient(90deg,#c9a03a,#f2d27a,#b08a2a)" }} />
          </div>
          <div style={{ position: "absolute", left: 1760, top: 150, fontFamily: SANS, fontWeight: 900, fontSize: 60, color: "#ffe08a", rotate: "12deg", opacity: 1 - run }}>叮铃!</div>
        </WindowBar>
      );
    },
  },
];

/* ───────── chorus 2: the night drive to her ───────── */

/** the hero's little car, side view; (x, y) = ground under the middle */
const LittleCar: React.FC<{ x: number; y: number; s: number; t: number; roof?: number; children?: React.ReactNode }> = ({ x, y, s, t, roof = 0, children }) => (
  <div style={{ position: "absolute", left: x - 260 * s, top: y - 250 * s, width: 520 * s, height: 250 * s }}>
    {children}
    <div style={{ position: "absolute", left: 90 * s, top: 20 * s, width: 320 * s, height: 110 * s, borderRadius: `${70 * s}px ${90 * s}px 0 0`, background: "linear-gradient(180deg,#ffd27a,#f2a94a)" }} />
    {/* sunroof hatch */}
    <div style={{ position: "absolute", left: 200 * s, top: 12 * s, width: 120 * s, height: 16 * s, borderRadius: 8 * s, background: "#c8862e", transformOrigin: "0 100%", rotate: `${-roof * 60}deg` }} />
    <div style={{ position: "absolute", left: 120 * s, top: 40 * s, width: 120 * s, height: 70 * s, borderRadius: `${40 * s}px 6px 0 0`, background: "linear-gradient(160deg,#cfe3ff,#4a5a7a)" }} />
    <div style={{ position: "absolute", left: 260 * s, top: 40 * s, width: 120 * s, height: 70 * s, borderRadius: `6px ${50 * s}px 0 0`, background: "linear-gradient(160deg,#cfe3ff,#4a5a7a)" }} />
    <div style={{ position: "absolute", left: 0, top: 110 * s, width: 520 * s, height: 100 * s, borderRadius: `${40 * s}px ${50 * s}px ${24 * s}px ${24 * s}px`, background: "linear-gradient(180deg,#ffe0a0,#f2b04a 40%,#c97a2a)" }} />
    {[100, 410].map((wx) => (
      <div key={wx} style={{ position: "absolute", left: (wx - 50) * s, top: 160 * s, width: 100 * s, height: 100 * s, borderRadius: "50%", background: "radial-gradient(circle, #bbb 0%, #555 30%, #111 40%)", rotate: `${t * 300}deg` }} />
    ))}
    <div style={{ position: "absolute", left: 500 * s, top: 130 * s, width: 30 * s, height: 26 * s, borderRadius: 8, background: "#fff6d0", boxShadow: "0 0 40px 16px rgba(255,246,208,0.6)" }} />
    <div style={{ position: "absolute", left: -6 * s, top: 130 * s, width: 22 * s, height: 26 * s, borderRadius: 8, background: "#ff3a4a", boxShadow: "0 0 30px 10px rgba(255,58,74,0.5)" }} />
  </div>
);

const chorus2: ShotDef[] = [
  {
    name: "30 夜里还是堵，霓虹映在湿挡风玻璃上",
    a: 152.9,
    b: Ls(31) - 0.4,
    tin: "flash",
    draw: (t) => (
      <>
        <Windshield t={t} night={1} neon={1} />
        <Cabin t={t} night={1} nav={<NavJam t={t} mins={25} text="前方拥堵" />}>
          <Actor x={760} y={805} size={300} t={t} expr="nervous" emote="sweat" emoteT={t - 153} armL={-20} armR={-20} lookX={Math.sin(t * 2) * 0.8} tilt={Math.sin(t * 4) * 3} />
        </Cabin>
        <Wheel x={760} y={960} rot={Math.sin(t * 3) * 6} />
      </>
    ),
  },
  {
    name: "31 路边花摊买一小束花",
    a: Ls(31) - 0.4,
    b: Ls(32) - 0.4,
    tin: "whip",
    draw: (t) => {
      const buy = Ls(31) + 1.2;
      const hold = t > buy;
      const tip = handAt(320, 1, -60);
      return (
        <>
          <Street t={t} rain={0.5} night={1} />
          <RainFx t={t} amount={0.5} />
          {/* flower stall with a string of lights */}
          <div style={{ position: "absolute", left: 900, top: 380, width: 820, height: 500, background: "linear-gradient(180deg,#3a2a30,#2a1e22)" }} />
          <div style={{ position: "absolute", left: 860, top: 330, width: 900, height: 90, background: "repeating-linear-gradient(90deg,#e86a7a 0 90px,#fff3e6 90px 180px)", clipPath: "polygon(0 0,100% 0,96% 100%,4% 100%)" }} />
          {Array.from({ length: 12 }, (_, i) => (
            <Glow key={i} x={900 + i * 72} y={430 + Math.sin(i) * 10} r={30} color="#ffd68c" a={0.6 + 0.4 * Math.sin(t * 3 + i)} />
          ))}
          {Array.from({ length: 6 }, (_, i) => (
            <div key={i} style={{ position: "absolute", left: 960 + i * 125, top: 700, width: 100, height: 160, borderRadius: "10px 10px 20px 20px", background: "#7a8a9a" }}>
              {Array.from({ length: 6 }, (_, k) => <div key={k} style={{ position: "absolute", left: 10 + (k % 3) * 28, top: -30 - Math.floor(k / 3) * 30, width: 30, height: 30, borderRadius: "50%", background: ["#ff6f91", "#ffc75f", "#ffffff", "#ff9671", "#c9a0ff", "#f9f871"][(i + k) % 6] }} />)}
            </div>
          ))}
          <Hand x={1300} y={lerp(560, 640, prog(t, buy - 0.6, buy))} s={150} sleeve="#6a4a5a" />
          <Actor x={tw(t, [[Ls(31) - 0.4, 500], [buy - 0.3, 760], [Ls(32) - 0.4, 640]])} y={900} size={320} t={t} legs={t < buy - 0.3 || t > buy + 0.8 ? "walk" : "stand"} phase={t * 2} flip={t > buy + 0.8} expr={hold ? "shy" : "determined"} blush={hold ? 0.8 : 0} emote={hold ? "♥" : null} emoteT={t - buy} armR={-60} armL={20} />
          {hold ? (
            <Bouquet x={tw(t, [[buy, 760], [Ls(32) - 0.4, 640]]) + (t > buy + 0.8 ? -tip.x : tip.x)} y={900 + tip.y + 20} s={200} t={t} />
          ) : (
            <Bouquet x={1220} y={640} s={200} t={t} />
          )}
        </>
      );
    },
  },
  {
    name: "32 黑白：红灯倒数 99 秒",
    a: Ls(32) - 0.4,
    b: Ls(33) - 0.3,
    tin: "fade",
    dur: 0.5,
    draw: (t) => {
      const n = Math.max(0, 99 - Math.floor((t - Ls(32) + 0.4) * 6));
      return (
        <>
          <Windshield t={t} night={1} neon={0.6} />
          <Cabin t={t} night={1} nav={<NavJam t={t} mins={25} text="红灯等待" />}>
            <Actor x={760} y={830} size={300} t={t} expr="sigh" emote="z" emoteT={t - Ls(32)} armL={70} armR={70} squash={0.5} tilt={-6} />
          </Cabin>
          <Wheel x={760} y={960} />
          {/* traffic light + countdown */}
          <div style={{ position: "absolute", left: 1300, top: 330, width: 300, height: 120, borderRadius: 20, background: "#111", display: "flex", alignItems: "center", justifyContent: "space-around", padding: "0 16px" }}>
            <div style={{ width: 80, height: 80, borderRadius: "50%", background: "#ff3a3a", boxShadow: "0 0 40px #ff3a3a" }} />
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 80, color: "#ff5a5a", width: 120, textAlign: "center" }}>{n}</div>
          </div>
          <Grey amount={easeOut(prog(t, Ls(32) - 0.4, Ls(32) + 0.4))} />
        </>
      );
    },
  },
  {
    name: "33 她回复「我在楼下等你」，绿灯亮，颜色回来",
    a: Ls(33) - 0.3,
    b: Ls(34) - 0.4,
    tin: "cut",
    draw: (t) => {
      const ping = Ls(33) + 0.1;
      const green = Ls(33) + 1.0;
      const sweep = easeInOut(prog(t, green, green + 1.0));
      return (
        <>
          <Windshield t={t} night={1} neon={1} />
          <Cabin t={t} night={1} nav={<NavJam t={t} mins={12} text="出发" color="#5fd08a" />}>
            <Actor x={760} y={805} size={300} t={t} expr={kf(t, [[Ls(33) - 0.3, "sigh"], [ping, "surprised"], [green, "joy"]])} emote={kf<"!" | "♪" | null>(t, [[Ls(33) - 0.3, null], [ping, "!"], [green, "♪"]])} emoteT={since(t, [ping, green])} armL={t > green ? -80 : 30} armR={t > green ? -80 : 30} legs={t > green ? "dangle" : "stand"} squash={t > ping && t < ping + 0.3 ? -0.6 : 0} />
          </Cabin>
          <Wheel x={760} y={960} />
          <Phone x={170} y={420} w={290} tilt={-6} glow={1}>
            <ChatScreen w={290} t={t} title="她 ♡" msgs={[{ me: true, text: "我想你。我现在去找你！", at: 0 }, { text: "我在楼下等你 ♡", at: ping }]} />
          </Phone>
          <div style={{ position: "absolute", left: 1300, top: 330, width: 300, height: 120, borderRadius: 20, background: "#111", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 80, height: 80, borderRadius: "50%", background: t > green ? "#3aff7a" : "#ff3a3a", boxShadow: `0 0 40px ${t > green ? "#3aff7a" : "#ff3a3a"}` }} />
          </div>
          {/* green light sweeping across the screen */}
          {sweep > 0 && sweep < 1 ? <AbsoluteFill style={{ background: `linear-gradient(90deg, transparent ${sweep * 120 - 30}%, rgba(80,255,140,0.35) ${sweep * 120 - 10}%, transparent ${sweep * 120}%)` }} /> : null}
          <Grey amount={1} reveal={easeInOut(prog(t, ping + 0.2, ping + 1.4))} cx={315} cy={720} />
        </>
      );
    },
  },
  {
    name: "34 导航剩余距离飞快减少",
    a: Ls(34) - 0.4,
    b: Ls(35) - 0.4,
    tin: "zoom",
    draw: (t) => {
      const km = lerp(3.2, 0.8, easeInOut(prog(t, Ls(34), Ls(35) - 0.6)));
      return (
        <>
          <Windshield t={t} night={1} neon={1} rain={0.3} />
          <SpeedLines t={t} cx={W / 2} cy={420} opacity={0.5} n={30} />
          <Cabin t={t} night={1} nav={<NavJam t={t} mins={Math.ceil(km * 3)} text="畅通" color="#5fd08a" />}>
            <Actor x={760} y={805} size={300} t={t} expr="determined" emote="spark" emoteT={t - Ls(34)} armL={-10} armR={-30} lookX={0.4} tilt={Math.sin(t * 2) * 4} />
          </Cabin>
          <Wheel x={760} y={960} rot={Math.sin(t * 1.5) * 25} />
          <div style={{ position: "absolute", left: 1200, top: 420, fontFamily: SANS, fontWeight: 900, fontSize: 150, color: "#5fd08a", textShadow: "0 0 30px rgba(95,208,138,0.7)" }}>{km.toFixed(1)}<span style={{ fontSize: 60 }}> km</span></div>
        </>
      );
    },
  },
  {
    name: "35 路过的橱窗里都是一起去过的地方",
    a: Ls(35) - 0.4,
    b: Ls(36) - 0.4,
    tin: "whip",
    draw: (t) => {
      const scroll = (t - Ls(35) + 0.4) * 520;
      const m = moodAt(t);
      return (
        <>
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${m.top}, ${m.mid})` }} />
          <Skyline m={m} t={t} layer={0} scroll={scroll * 0.2} base={520} />
          {/* row of shop windows sliding past, each framing a shared memory */}
          {Array.from({ length: 6 }, (_, i) => {
            const x = ((i * 520 - scroll) % 3120 + 3120) % 3120 - 400;
            return (
              <div key={i} style={{ position: "absolute", left: x, top: 330, width: 460, height: 460, background: "#2a2430", border: "16px solid #4a3a44" }}>
                <div style={{ position: "absolute", left: 30, top: 30, width: 368, height: 368, background: "#fff6e6", boxShadow: "0 0 60px rgba(255,214,140,0.6)" }}>
                  <Memory kind={i % 4} w={368} />
                </div>
                <div style={{ position: "absolute", left: -16, top: -70, width: 492, height: 60, background: ["#d9455f", "#5a8fd9", "#4a9a6a"][i % 3], clipPath: "polygon(0 0,100% 0,96% 100%,4% 100%)" }} />
              </div>
            );
          })}
          <div style={{ position: "absolute", left: 0, top: 820, width: W, height: 260, background: "#1e1c24" }} />
          <div style={{ position: "absolute", left: 0, top: 950, width: W, height: 0, borderTop: "6px dashed rgba(255,230,160,0.5)", transform: `translateX(${-(scroll % 120)}px)` }} />
          <LittleCar x={900} y={960} s={0.75} t={t}>
            <div style={{ position: "absolute", left: 140, top: 30 }}>
              <Actor x={80} y={110} size={150} t={t} expr="happy" lookX={-0.8} lookY={-0.6} emote="♥" emoteT={t - Ls(35)} />
            </div>
          </LittleCar>
        </>
      );
    },
  },
  {
    name: "36-38 天窗弹开，探出车顶大声唱，爱心飞出去",
    a: Ls(36) - 0.4,
    b: 186.6,
    tin: "flash",
    draw: (t) => {
      const roof = easeOutBack(prog(t, Ls(36) - 0.2, Ls(36) + 0.4), 1.6);
      const pop = easeOutBack(prog(t, Ls(36) + 0.2, Ls(36) + 0.8), 2);
      const beat = pulseAt(t);
      const m = moodAt(t);
      const scroll = (t - Ls(36)) * 300;
      return (
        <>
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${m.top}, ${m.mid} 70%, ${m.low})` }} />
          <Skyline m={m} t={t} layer={0} scroll={scroll * 0.15} base={760} litBoost={0.3} />
          <Skyline m={m} t={t} layer={1} scroll={scroll * 0.35} base={860} litBoost={0.3} />
          <div style={{ position: "absolute", left: 0, top: 860, width: W, height: 220, background: "#18161e" }} />
          <Cam s={tw(t, [[Ls(36) - 0.4, 1.2], [186.6, 1.0]])} oy={70} r={Math.sin(t * 0.7) * 1.5}>
            <LittleCar x={960} y={980} s={1.05 + beat * 0.03} t={t} roof={roof}>
              <div style={{ position: "absolute", left: 175, top: lerp(60, -160, clamp01(pop)) }}>
                <Actor x={110} y={200} size={220} t={t} expr={kf(t, [[Ls(36), "joy"], [Ls(38), "love"]])} emote="♪" emoteT={since(t, [Ls(36) + 0.3, Ls(37), Ls(38)])} armL={-80 + beat * 30} armR={-80 + beat * 30} pinch={1} squash={-beat * 0.3} />
              </div>
            </LittleCar>
          </Cam>
          {[Ls(36) + 0.5, Ls(37), Ls(38), Ls(38) + 2.2].map((tt, i) => (
            <HeartBurst key={i} t={t} t0={tt} x={960 + (i - 1.5) * 120} y={560} n={20} spread={700} dur={2.6} rise={420} />
          ))}
          <Twinkles t={t} x={960} y={500} r={600} n={16} />
        </>
      );
    },
  },
];

/* ───────── bridge: arrive, step into a puddle (slow motion) ───────── */

const bridge: ShotDef[] = [
  {
    name: "过门：车停下，小脚踩进水坑",
    a: 186.6,
    b: 190.7,
    tin: "fade",
    dur: 0.6,
    draw: (t) => {
      const step = 188.2;
      const splash = prog(t, step, step + 2.2); // slow motion
      return (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(180deg,#1e2240,#2e2a48)" }} />
          <RainFx t={t * 0.3} amount={0.8} />
          <div style={{ position: "absolute", left: 0, top: 760, width: W, height: 320, background: "linear-gradient(180deg,#3a3848,#22202a)" }} />
          {/* puddle with the city lights reflected */}
          <div style={{ position: "absolute", left: 560, top: 820, width: 800, height: 160, borderRadius: "50%", background: "radial-gradient(ellipse, rgba(255,207,115,0.5), rgba(120,140,200,0.35) 50%, rgba(60,70,110,0.3) 70%)" }} />
          {/* car door opening on the left */}
          <div style={{ position: "absolute", left: -40, top: 160, width: 560, height: 620, borderRadius: 30, background: "linear-gradient(90deg,#c97a2a,#f2b04a)", transformOrigin: "0 50%", transform: `perspective(1400px) rotateY(${-easeOut(prog(t, 186.8, 187.6)) * 50}deg)` }} />
          {/* the hero hops down from the car into the puddle */}
          <Actor
            x={tw(t, [[187.2, 480], [step, 960]], easeOut)}
            y={t < step ? 880 - Math.sin(prog(t, 187.2, step) * Math.PI) * 300 + (1 - prog(t, 187.2, step)) * -120 : 880}
            size={420}
            t={t}
            expr={kf(t, [[186.6, "determined"], [step, "surprised"], [step + 1.2, "joy"]])}
            emote={kf<"spark" | "!" | "♪" | null>(t, [[186.6, null], [187.2, "spark"], [step, "!"], [step + 1.2, "♪"]])}
            emoteT={since(t, [187.2, step, step + 1.2])}
            legs={t < step ? "dangle" : "stand"}
            squash={t > step && t < step + 0.4 ? 0.6 : t < step ? -0.3 : 0}
            armL={t < step ? -70 : -40}
            armR={t < step ? -70 : -40}
          />
          {splash > 0
            ? Array.from({ length: 22 }, (_, i) => {
                const a = -Math.PI * (0.1 + hash(i) * 0.8);
                const d = easeOut(splash) * (180 + hash(i * 3) * 260);
                const g = splash * splash * 400;
                return <div key={i} style={{ position: "absolute", left: 960 + Math.cos(a) * d, top: 860 + Math.sin(a) * d + g, width: 14 + hash(i) * 14, height: 18 + hash(i) * 16, borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%", background: "rgba(220,235,255,0.85)", opacity: 1 - splash }} />;
              })
            : null}
          {splash > 0 ? [0, 1].map((k) => <div key={k} style={{ position: "absolute", left: 960 - easeOut(clamp01(splash * 1.2 - k * 0.2)) * 400, top: 880 - easeOut(clamp01(splash * 1.2 - k * 0.2)) * 60, width: easeOut(clamp01(splash * 1.2 - k * 0.2)) * 800, height: easeOut(clamp01(splash * 1.2 - k * 0.2)) * 120, borderRadius: "50%", border: `4px solid rgba(255,255,255,${0.6 * (1 - splash)})` }} />) : null}
          <div style={{ position: "absolute", left: 1300, top: 200, fontFamily: SANS, fontWeight: 900, fontSize: 70, color: rgba("#dfe8ff", 0.9 * Math.sin(clamp01(splash * 1.5) * Math.PI)) }}>啪嗒…</div>
          <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 70%, transparent 35%, ${rgba("#000000", 0.55)})` }} />
        </>
      );
    },
  },
];

export const ACT3: ShotDef[] = [...verse2, ...pre2, ...chorus2, ...bridge];
