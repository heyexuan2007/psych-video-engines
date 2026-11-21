import React from "react";
import { AbsoluteFill } from "remotion";
import { Calendar } from "../components/Calendar";
import { Skyline } from "../components/World";
import { SANS, moodAt } from "../lib/theme";
import { H, W, clamp01, easeInOut, easeOut, energyAt, hash, lerp, mix, prog, pulseAt, rgba } from "../lib/util";
import { ShotDef } from "./act1";
import { Actor, Cam, Glow, Grey, HeartBurst, Le, Ls, RainFx, Twinkles, kf, since, tw } from "./kit";
import { ChatScreen, Phone, Polaroid, Shoulders } from "./props";

/* ───────── car interior (shared) ───────── */

/** brake lights / traffic seen through the windshield, with rain + wipers. night 0..1 */
export const Windshield: React.FC<{ t: number; night?: number; rain?: number; neon?: number }> = ({ t, night = 0.5, rain = 1, neon = 0 }) => {
  const m = moodAt(t);
  const wiper = (Math.sin(t * 2.6) + 1) / 2; // 0..1 sweep
  return (
    <AbsoluteFill style={{ clipPath: "polygon(4% 6%, 96% 6%, 100% 64%, 0% 64%)" }}>
      <AbsoluteFill style={{ background: `linear-gradient(180deg, ${m.top}, ${m.mid} 55%, ${m.low})` }} />
      <AbsoluteFill style={{ filter: "blur(3px)" }}>
        <Skyline m={m} t={t} layer={0} scroll={t * 2} base={560} />
        <Skyline m={m} t={t} layer={1} scroll={t * 3 + 500} base={620} />
        {/* road ahead + rows of cars' brake lights, slowly stop-and-go */}
        <div style={{ position: "absolute", left: 0, top: 560, width: W, height: 160, background: mix("#3a3640", "#1a1820", night) }} />
        {[0, 1, 2].map((row) =>
          Array.from({ length: 5 + row * 2 }, (_, i) => {
            const sc = [1, 0.62, 0.4][row];
            const x = 160 + i * (1600 / (5 + row * 2)) + Math.sin(t * 0.6 + i + row) * 6;
            const y = [600, 560, 535][row];
            const brake = 0.6 + 0.4 * Math.sin(t * 1.3 + i * 1.7);
            return (
              <div key={`${row}-${i}`} style={{ position: "absolute", left: x - 90 * sc, top: y - 50 * sc, width: 180 * sc, height: 70 * sc, borderRadius: 14 * sc, background: mix(["#5a5f78", "#7a4a4a", "#4a6a5a", "#888"][(i + row) % 4], "#111", night * 0.5) }}>
                {[0.08, 0.78].map((p) => (
                  <div key={p} style={{ position: "absolute", left: 180 * sc * p, top: 26 * sc, width: 26 * sc, height: 14 * sc, borderRadius: 4, background: "#ff2a3a", boxShadow: `0 0 ${30 * sc * brake}px ${12 * sc * brake}px rgba(255,40,60,${0.4 + brake * 0.4})` }} />
                ))}
              </div>
            );
          }),
        )}
        {neon > 0
          ? [200, 700, 1300, 1700].map((x, i) => <Glow key={i} x={x} y={330 + (i % 2) * 60} r={160} color={["#ff5fa8", "#5fd8ff", "#ffcf5f", "#b77bff"][i]} a={0.6 * neon} />)
          : null}
      </AbsoluteFill>
      <RainFx t={t} amount={rain * 0.9} angle={0.05} />
      {/* drops on the glass refracting the brake lights */}
      {Array.from({ length: 50 }, (_, i) => {
        const r = 5 + hash(i * 3.1) * 11;
        const wiped = Math.abs(hash(i * 7.7) - wiper) < 0.08;
        return <div key={i} style={{ position: "absolute", left: hash(i * 7.7) * W, top: 80 + hash(i * 2.3) * 560, width: r * 2, height: r * 2, borderRadius: "50%", background: `radial-gradient(circle at 40% 35%, rgba(255,255,255,0.85), ${rgba("#ff6070", 0.25)} 45%, transparent 70%)`, opacity: wiped ? 0 : rain * 0.9 }} />;
      })}
      {/* wipers */}
      {[520, 1300].map((px, k) => (
        <div key={k} style={{ position: "absolute", left: px, top: 690, width: 640, height: 14, borderRadius: 7, background: "#15151a", transformOrigin: "0 50%", rotate: `${-170 + wiper * 150 + k * 4}deg` }} />
      ))}
    </AbsoluteFill>
  );
};

/** dashboard, steering wheel, nav screen; the hero sits on a booster cushion behind the wheel */
export const Cabin: React.FC<{ t: number; nav?: React.ReactNode; children?: React.ReactNode; night?: number }> = ({ t, nav, children, night = 0.5 }) => (
  <AbsoluteFill>
    {/* roof + A-pillars */}
    <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 80, background: mix("#4a4048", "#1d1a22", night) }} />
    <div style={{ position: "absolute", left: 0, top: 0, width: 120, height: H, background: mix("#4a4048", "#1d1a22", night), clipPath: "polygon(0 0, 100% 0, 30% 100%, 0 100%)" }} />
    <div style={{ position: "absolute", right: 0, top: 0, width: 120, height: H, background: mix("#4a4048", "#1d1a22", night), clipPath: "polygon(0 0, 100% 0, 100% 100%, 70% 100%)" }} />
    {/* rear-view mirror */}
    <div style={{ position: "absolute", left: 1500, top: 70, width: 8, height: 60, background: "#222" }} />
    <div style={{ position: "absolute", left: 1380, top: 120, width: 260, height: 80, borderRadius: 20, background: "linear-gradient(180deg,#2a2a30,#121216)", border: "6px solid #333" }}>
      <div style={{ position: "absolute", inset: 8, borderRadius: 12, background: "linear-gradient(180deg,#6a7a9a,#3a4560)", opacity: 0.8 }} />
    </div>
    {children}
    {/* booster cushion peeking above the dash */}
    <div style={{ position: "absolute", left: 560, top: 690, width: 380, height: 30, borderRadius: 15, background: "linear-gradient(180deg,#e88a6a,#b85a44)" }} />
    {/* dashboard */}
    <div style={{ position: "absolute", left: 0, top: 690, width: W, height: 390, background: `linear-gradient(180deg, ${mix("#5a4a42", "#24202a", night)} 0%, ${mix("#3a302c", "#15131a", night)} 100%)`, borderRadius: "60px 60px 0 0", boxShadow: "0 -10px 30px rgba(0,0,0,0.45)" }} />
    <div style={{ position: "absolute", left: 0, top: 690, width: W, height: 4, background: "rgba(255,255,255,0.12)" }} />
    {/* nav screen */}
    <div style={{ position: "absolute", left: 1230, top: 740, width: 420, height: 250, borderRadius: 18, background: "#0f1622", border: "8px solid #222", boxShadow: "0 0 40px rgba(90,170,255,0.25)", overflow: "hidden" }}>{nav}</div>
  </AbsoluteFill>
);

/** steering wheel in front of the hero */
export const Wheel: React.FC<{ x: number; y: number; rot?: number }> = ({ x, y, rot = 0 }) => (
  <div style={{ position: "absolute", left: x - 230, top: y - 230, width: 460, height: 460, borderRadius: "50%", border: "38px solid #1e1e24", boxShadow: "inset 0 0 0 4px #333, 0 10px 30px rgba(0,0,0,0.5)", rotate: `${rot}deg` }}>
    <div style={{ position: "absolute", left: 150, top: 150, width: 84, height: 84, borderRadius: "50%", background: "#2a2a32" }} />
    <div style={{ position: "absolute", left: 0, top: 176, width: 384, height: 34, background: "#1e1e24" }} />
  </div>
);

export const NavJam: React.FC<{ t: number; mins: number; text: string; color?: string }> = ({ t, mins, text, color = "#ff5a5a" }) => (
  <AbsoluteFill style={{ fontFamily: SANS, color: "#fff", padding: 22 }}>
    <svg width={380} height={120} style={{ position: "absolute", left: 20, top: 20 }}>
      <path d="M10 100 C 80 90, 120 40, 200 50 S 330 20, 370 10" stroke="#3a4a66" strokeWidth={16} fill="none" strokeLinecap="round" />
      <path d="M10 100 C 80 90, 120 40, 200 50" stroke={color} strokeWidth={10} fill="none" strokeLinecap="round" strokeDasharray={`${8 + (t * 40) % 20} 6`} />
      <circle cx={10} cy={100} r={10} fill="#5fd0ff" />
    </svg>
    <div style={{ position: "absolute", left: 24, bottom: 20, fontSize: 34, fontWeight: 800, color }}>{text}</div>
    <div style={{ position: "absolute", right: 24, bottom: 20, fontSize: 30, fontWeight: 700 }}>{mins} 分钟</div>
  </AbsoluteFill>
);

/* ───────── chorus 1 ───────── */

const chorus1: ShotDef[] = [
  {
    name: "11 驾驶座：前方全是刹车灯",
    a: 65.9,
    b: Ls(12) - 0.4,
    tin: "flash",
    draw: (t) => (
      <>
        <Windshield t={t} night={0.4} />
        <Cabin t={t} nav={<NavJam t={t} mins={23} text="前方拥堵" />}>
          <Actor x={760} y={805} size={300} t={t} expr={kf(t, [[65.9, "determined"], [Ls(11) + 0.6, "surprised"], [Ls(11) + 2.2, "nervous"]])} emote={kf<"!" | "sweat" | null>(t, [[65.9, null], [Ls(11) + 0.6, "!"], [Ls(11) + 2.2, "sweat"]])} emoteT={since(t, [Ls(11) + 0.6, Ls(11) + 2.2])} armL={-20} armR={-20} lookY={-0.3} squash={t > Ls(11) + 0.6 && t < Ls(11) + 0.9 ? -0.5 : 0} />
        </Cabin>
        <Wheel x={760} y={960} rot={Math.sin(t * 1.4) * 4} />
      </>
    ),
  },
  {
    name: "12 三格分屏：打哈欠 / 按喇叭 / 跟着节拍敲方向盘",
    a: Ls(12) - 0.4,
    b: Ls(13) - 0.5,
    tin: "wipe",
    draw: (t) => {
      const beat = pulseAt(t);
      const pane = (i: number, child: React.ReactNode) => {
        const a0 = Ls(12) - 0.4 + i * 0.25;
        const p = easeOut(prog(t, a0, a0 + 0.4));
        return (
          <div key={i} style={{ position: "absolute", left: 30 + i * 630, top: 260 + (1 - p) * 700, width: 600, height: 760, borderRadius: 24, overflow: "hidden", border: "8px solid #fff", boxShadow: "0 20px 40px rgba(0,0,0,0.45)", scale: String(1 + (i === 1 ? beat * 0.04 : 0)), rotate: `${(i - 1) * 2}deg` }}>
            {child}
          </div>
        );
      };
      return (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(135deg,#2a2440,#4a2a40)" }} />
          <AbsoluteFill style={{ background: "repeating-linear-gradient(45deg, rgba(255,255,255,0.04) 0 20px, transparent 20px 40px)" }} />
          {pane(
            0,
            <AbsoluteFill style={{ background: "linear-gradient(180deg,#8aa0c0,#5a6a88)" }}>
              <Shoulders x={300} y={760} w={420} color="#4a6a9a" hair="#2a1e18" lean={-6} />
              {/* yawn */}
              <div style={{ position: "absolute", left: 220, top: 440, width: 56, height: 24 + Math.max(0, Math.sin(t * 2)) * 44, borderRadius: "50%", background: "#5a2a2a" }} />
              <div style={{ position: "absolute", left: 360, top: 300, fontFamily: SANS, fontSize: 60, fontWeight: 900, color: "#fff", opacity: Math.max(0, Math.sin(t * 2)) }}>哈~</div>
            </AbsoluteFill>,
          )}
          {pane(
            1,
            <AbsoluteFill style={{ background: "linear-gradient(180deg,#6a5a7a,#3a3048)" }}>
              <Actor x={300} y={660} size={330} t={t} expr="happy" emote="♪" emoteT={t - Ls(12)} armL={-30 + beat * 50} armR={-30 + beat * 50} squash={beat * 0.3} tilt={Math.sin(t * 6) * 5} />
              <div style={{ position: "absolute", left: 60, top: 520, width: 480, height: 480, borderRadius: "50%", border: "34px solid #1e1e24" }} />
            </AbsoluteFill>,
          )}
          {pane(
            2,
            <AbsoluteFill style={{ background: "linear-gradient(180deg,#c09a7a,#8a6a5a)" }}>
              <Shoulders x={300} y={760} w={420} color="#9a4a3a" hair="#1a1a1a" lean={8} flip />
              {[0, 1, 2].map((k) => {
                const q = (t * 2 + k / 3) % 1;
                return <div key={k} style={{ position: "absolute", left: 300 - q * 300, top: 250 - q * 300, width: q * 600, height: q * 600, borderRadius: "50%", border: `8px solid ${rgba("#ffffff", 1 - q)}` }} />;
              })}
              <div style={{ position: "absolute", left: 80, top: 120, fontFamily: SANS, fontSize: 80, fontWeight: 900, color: "#ffe14a", rotate: "-10deg", textShadow: "0 4px 0 #9a3a2a", scale: String(1 + Math.max(0, Math.sin(t * 12)) * 0.15) }}>叭叭!</div>
            </AbsoluteFill>,
          )}
        </>
      );
    },
  },
  {
    name: "13 黑白：趴在方向盘上叹气",
    a: Ls(13) - 0.5,
    b: Ls(14) - 0.3,
    tin: "fade",
    dur: 0.6,
    draw: (t) => (
      <>
        <Cam s={tw(t, [[Ls(13) - 0.5, 1.15], [Ls(14), 1.0]])} oy={65}>
          <Windshield t={t} night={0.5} />
          <Cabin t={t} nav={<NavJam t={t} mins={41} text="拥堵加剧" />}>
            <Actor x={760} y={830} size={300} t={t} expr="sigh" emote="z" emoteT={t - Ls(13)} armL={70} armR={70} squash={0.5} tilt={8} />
          </Cabin>
          <Wheel x={760} y={960} />
        </Cam>
        <Grey amount={easeOut(prog(t, Ls(13) - 0.5, Ls(13) + 0.3))} />
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 55%, transparent 40%, rgba(0,0,0,0.55))" }} />
      </>
    ),
  },
  {
    name: "14 她的消息亮起，颜色涌回来",
    a: Ls(14) - 0.3,
    b: Ls(15) - 0.4,
    tin: "cut",
    draw: (t) => {
      const ping = Ls(14) + 0.2;
      const reveal = easeInOut(prog(t, ping + 0.3, ping + 1.6));
      return (
        <>
          <Windshield t={t} night={0.4} />
          <Cabin t={t} nav={<NavJam t={t} mins={41} text="拥堵加剧" />}>
            <Actor x={760} y={805} size={300} t={t} expr={kf(t, [[Ls(14) - 0.3, "sigh"], [ping, "surprised"], [ping + 1.0, "joy"]])} emote={kf<"!" | "♪" | null>(t, [[Ls(14) - 0.3, null], [ping, "!"], [ping + 1.0, "♪"]])} emoteT={since(t, [ping, ping + 1.0])} armL={t > ping + 1 ? -80 : 40} armR={t > ping + 1 ? -80 : 40} squash={t > ping && t < ping + 0.3 ? -0.6 : 0} legs={t > ping + 1 ? "dangle" : "stand"} />
          </Cabin>
          <Wheel x={760} y={960} />
          {/* phone in the dash holder, lighting up */}
          <Phone x={170} y={420} w={290} tilt={-6} glow={t > ping ? 1 : 0.1}>
            <ChatScreen w={290} t={t} title="她 ♡" msgs={[{ text: "下雨了，记得带伞 ☂", at: ping }]} />
          </Phone>
          {t > ping ? <Glow x={315} y={720} r={260 + Math.sin(t * 8) * 20} color="#ffe8b0" a={0.5 * (1 - reveal * 0.6)} /> : null}
          <Grey amount={1} reveal={reveal} cx={315} cy={720} />
          <HeartBurst t={t} t0={ping + 1.0} x={760} y={520} n={22} spread={600} dur={2.4} />
        </>
      );
    },
  },
  {
    name: "15 副驾驶空座，她的虚影浮现",
    a: Ls(15) - 0.4,
    b: Ls(16) - 0.4,
    tin: "whip",
    draw: (t) => {
      const form = easeInOut(prog(t, Ls(15) + 0.3, Ls(15) + 2.0));
      const belt = prog(t, Ls(15) + 2.2, Ls(15) + 2.8);
      return (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(180deg,#3a3442,#241f2c)" }} />
          <Cam x={tw(t, [[Ls(15) - 0.4, 0], [Ls(16), -60]])}>
            {/* passenger seat */}
            <div style={{ position: "absolute", left: 1150, top: 90, width: 280, height: 150, borderRadius: 60, background: "linear-gradient(90deg,#5a4a52,#7a6a72 50%,#4a3a42)" }} />
            <div style={{ position: "absolute", left: 1240, top: 230, width: 22, height: 50, background: "#888" }} />
            <div style={{ position: "absolute", left: 1320, top: 230, width: 22, height: 50, background: "#888" }} />
            <div style={{ position: "absolute", left: 1000, top: 270, width: 580, height: 680, borderRadius: "120px 120px 40px 40px", background: "linear-gradient(90deg,#5a4a52,#7a6a72 50%,#4a3a42)", boxShadow: "inset 0 -20px 40px rgba(0,0,0,0.35)" }}>
              {[0.25, 0.5, 0.75].map((f) => (
                <div key={f} style={{ position: "absolute", left: 580 * f - 1, top: 60, width: 3, height: 560, background: "repeating-linear-gradient(180deg, rgba(255,255,255,0.18) 0 10px, transparent 10px 20px)" }} />
              ))}
            </div>
            <div style={{ position: "absolute", left: 940, top: 760, width: 700, height: 220, borderRadius: 40, background: "linear-gradient(180deg,#6a5a62,#4a3a42)" }} />
            {/* her, gathering from dots of light */}
            <div style={{ position: "absolute", inset: 0, opacity: form, filter: `blur(${(1 - form) * 6}px)` }}>
              <Actor x={1290} y={830} size={380} t={t} her legs="sit" expr={belt > 0.5 ? "happy" : "neutral"} lookX={-0.8} armL={-20} armR={30} shadow={false} />
            </div>
            {form < 1
              ? Array.from({ length: 40 }, (_, i) => {
                  const a = hash(i) * Math.PI * 2;
                  const d = (1 - form) * (200 + hash(i * 3) * 300);
                  return <div key={i} style={{ position: "absolute", left: 1290 + Math.cos(a) * d, top: 680 + Math.sin(a) * d * 0.7, width: 10, height: 10, borderRadius: "50%", background: "#ffd0dc", boxShadow: "0 0 12px #ff9fb8", opacity: 1 - form * 0.8 }} />;
                })
              : null}
            {/* seat belt sliding across */}
            <div style={{ position: "absolute", left: 1060, top: 240, width: 30, height: lerp(0, 700, easeOut(belt)), background: "#2a2a30", rotate: "-38deg", transformOrigin: "50% 0", opacity: form }} />
            <Twinkles t={t} x={1290} y={620} r={260} n={10} color="#ffd0dc" opacity={form} />
            {/* the hero, shy, peeking from the driver side */}
            <Actor x={420} y={900} size={360} t={t} expr={form > 0.5 ? "shy" : "surprised"} blush={form} lookX={1} armL={40} armR={-30} emote={form > 0.5 ? "♥" : "!"} emoteT={since(t, [Ls(15) - 0.2, Ls(15) + 1.2])} />
          </Cam>
        </>
      );
    },
  },
  {
    name: "16 后视镜上的拍立得一张张翻",
    a: Ls(16) - 0.4,
    b: Ls(17) - 0.4,
    tin: "push",
    draw: (t) => {
      const flips = [Ls(16) + 0.2, Ls(16) + 1.3, Ls(16) + 2.4];
      return (
        <>
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 30%, #5a4a5a, #1e1a24)" }} />
          {/* the mirror at the top, polaroids hanging on strings */}
          <div style={{ position: "absolute", left: 660, top: 330, width: 600, height: 150, borderRadius: 40, background: "linear-gradient(180deg,#2a2a30,#121216)", border: "10px solid #333" }}>
            <div style={{ position: "absolute", inset: 14, borderRadius: 26, background: "linear-gradient(180deg,#7a8aaa,#3a4560)" }} />
          </div>
          {flips.map((f, i) => {
            const p = easeOut(prog(t, f, f + 0.8));
            const swing = Math.sin((t - f) * 4) * 10 * Math.exp(-Math.max(0, t - f) * 1.2);
            const x = 520 + i * 330;
            return (
              <div key={i} style={{ position: "absolute", left: x, top: 470, width: 0, height: 0, rotate: `${swing + (i - 1) * 6}deg`, transformOrigin: "0 0" }}>
                <div style={{ position: "absolute", left: -1, top: 0, width: 2, height: 90, background: "#ddd" }} />
                <div style={{ position: "absolute", left: -140, top: 90, transform: `perspective(900px) rotateY(${(1 - p) * 180}deg)`, transformStyle: "preserve-3d" }}>
                  <Polaroid x={0} y={0} w={280} kind={i} develop={prog(t, f + 0.5, f + 1.6)} caption={["冰淇淋", "看海", "喂猫"][i]} />
                </div>
              </div>
            );
          })}
          <Actor x={1640} y={1000} size={320} t={t} expr="happy" lookX={-1} lookY={-0.8} emote="♥" emoteT={t - Ls(16)} armL={-60} armR={20} />
        </>
      );
    },
  },
  {
    name: "17-19 对着手机录语音，声波跟着唱，发出去",
    a: Ls(17) - 0.4,
    b: 100.2,
    tin: "zoom",
    draw: (t) => {
      const send = Le(19) - 0.2;
      const fly = prog(t, send, send + 1.4);
      const e = energyAt(t);
      const beat = pulseAt(t);
      return (
        <>
          <Windshield t={t} night={0.5} rain={0.6} />
          <Cabin t={t} nav={<NavJam t={t} mins={18} text="拥堵缓解" color="#ffb44a" />}>
            <Actor x={700} y={815} size={330} t={t} expr={kf(t, [[Ls(17) - 0.4, "joy"], [Ls(19), "love"], [send, "happy"]])} emote={kf<"♪" | "♥">(t, [[Ls(17) - 0.4, "♪"], [Ls(19), "♥"]])} emoteT={since(t, [Ls(17) - 0.4, Ls(19)])} armR={-80} armL={-40 + beat * 30} squash={beat * 0.25} tilt={Math.sin(t * 5) * 4} blush={0.5} />
          </Cabin>
          <Wheel x={700} y={960} />
          {/* recording phone held up */}
          <Phone x={960} y={430} w={220} tilt={8} dark>
            <AbsoluteFill style={{ fontFamily: SANS, color: "#fff", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 20 }}>
              <div style={{ fontSize: 22, opacity: 0.7 }}>发给 她 ♡</div>
              <div style={{ display: "flex", gap: 6, alignItems: "center", height: 140 }}>
                {Array.from({ length: 14 }, (_, i) => (
                  <div key={i} style={{ width: 8, height: 16 + (0.3 + e * 0.7) * 110 * Math.abs(Math.sin(t * 9 + i * 0.9)) * (0.5 + hash(i) * 0.5) + beat * 30, borderRadius: 4, background: i % 3 ? "#ff8fab" : "#ffd27a" }} />
                ))}
              </div>
              <div style={{ width: 70, height: 70, borderRadius: "50%", background: t < send ? "#ff4d6d" : "#5fd08a", boxShadow: `0 0 ${20 + beat * 30}px #ff4d6d` }} />
              <div style={{ fontSize: 24 }}>{t < send ? `0:${String(Math.floor(t - Ls(17) + 0.4)).padStart(2, "0")}` : "已发送 ✓"}</div>
            </AbsoluteFill>
          </Phone>
          {/* the voice bubble flying out of the window */}
          {fly > 0 && fly < 1 ? (
            <div style={{ position: "absolute", left: lerp(1060, 1900, easeInOut(fly)), top: lerp(470, 60, easeInOut(fly)) - Math.sin(fly * Math.PI) * 120, width: 220, height: 90, borderRadius: 45, background: "#ffb38a", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 800, fontSize: 30, color: "#fff", scale: String(1 - fly * 0.5), boxShadow: "0 0 40px rgba(255,179,138,0.8)" }}>
              ))) 0:09
            </div>
          ) : null}
          <HeartBurst t={t} t0={send} x={1080} y={470} n={16} spread={500} dur={2} />
        </>
      );
    },
  },
];

/* ───────── interlude: calendar 1 → 2, day turns to night ───────── */

const interlude: ShotDef[] = [
  {
    name: "间奏：撕日历，天黑了",
    a: 100.2,
    b: 103.6,
    tin: "iris",
    draw: (t) => {
      const night = easeInOut(prog(t, 100.4, 103.2));
      return (
        <>
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${mix("#f3b98a", "#141a36", night)}, ${mix("#f7dcb8", "#2a2448", night)})` }} />
          {Array.from({ length: 50 }, (_, i) => (
            <div key={i} style={{ position: "absolute", left: hash(i) * W, top: hash(i * 3) * 600, width: 3, height: 3, borderRadius: "50%", background: "#fff", opacity: night * hash(i * 7) }} />
          ))}
          <Glow x={1500} y={lerp(300, 900, night)} r={300} color="#ffd9a0" a={0.8 * (1 - night)} />
          <Glow x={400} y={lerp(900, 220, night)} r={200} color="#dfe8ff" a={0.7 * night} />
          <Cam s={tw(t, [[100.2, 1.25], [103.6, 1.0]])}>
            <Calendar t={t} flips={[100.9]} x={W / 2 - 220} y={250} w={440} startDay={1} />
          </Cam>
          {/* clock hands spinning fast = time passing */}
          <div style={{ position: "absolute", left: 1500 - 130, top: 620 - 130, width: 260, height: 260, borderRadius: "50%", background: "#fffaf2", border: "10px solid #5a3b28" }}>
            <div style={{ position: "absolute", left: 125, top: 40, width: 10, height: 90, background: "#333", transformOrigin: "50% 100%", rotate: `${(t - 100.2) * 720}deg` }} />
            <div style={{ position: "absolute", left: 126, top: 70, width: 8, height: 60, background: "#d9573a", transformOrigin: "50% 100%", rotate: `${(t - 100.2) * 60}deg` }} />
          </div>
          <AbsoluteFill style={{ opacity: clamp01(1 - Math.abs(t - 101) * 2) * 0.5, background: "#fff" }} />
        </>
      );
    },
  },
];

export const ACT2: ShotDef[] = [...chorus1, ...interlude];
