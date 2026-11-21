import React from "react";
import { AbsoluteFill } from "remotion";
import { Calendar } from "../components/Calendar";
import { Clouds, Skyline } from "../components/World";
import { Mood, SANS, SERIF, moodAt } from "../lib/theme";
import { H, W, clamp01, easeIn, easeInOut, easeOut, easeOutBack, hash, lerp, mix, prog, pulseAt, rgba } from "../lib/util";
import { Actor, Cam, Glow, HER, HeartBurst, Ls, RainFx, SpeedLines, Trans, Twinkles, handAt, kf, since, tw } from "./kit";
import { AlarmClock, ChatScreen, Cup, Hand, Keys, LatteTop, Legs, Memory, Phone, PixelHeart, Shoulders, Umbrella, WarmBokeh } from "./props";

export type ShotDef = { name: string; a: number; b: number; tin?: Trans; dur?: number; ix?: number; iy?: number; draw: (t: number, p: number) => React.ReactNode };

/* ───────── shared sets ───────── */

/** warm bedroom wall with a morning window on the left */
export const Bedroom: React.FC<{ t: number; light?: number }> = ({ t, light = 1 }) => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#f3e3cf 0%,#e9d2b8 100%)" }} />
    <AbsoluteFill style={{ background: "repeating-linear-gradient(90deg, rgba(160,110,70,0.05) 0 2px, transparent 2px 46px)" }} />
    {/* window light falling across the room */}
    <div style={{ position: "absolute", left: -200, top: -100, width: 1300, height: 1400, background: `linear-gradient(115deg, ${rgba("#fff2c8", 0.55 * light)} 0%, transparent 55%)`, clipPath: "polygon(15% 0, 45% 0, 90% 100%, 40% 100%)", mixBlendMode: "screen" }} />
    {Array.from({ length: 18 }, (_, i) => (
      <div key={i} style={{ position: "absolute", left: 300 + hash(i) * 500 + Math.sin(t * 0.4 + i) * 30, top: 100 + hash(i * 3) * 700 - ((t * 12 + i * 40) % 200), width: 4, height: 4, borderRadius: "50%", background: "#fff6d8", opacity: 0.6 * light, boxShadow: "0 0 8px #fff2c0" }} />
    ))}
  </AbsoluteFill>
);

/** outside street with a house door; sky tween sunny→rainy by `rain` */
export const Street: React.FC<{ t: number; rain: number; night?: number }> = ({ t, rain, night = 0 }) => {
  const sky = mix(mix("#8cc8f0", "#7d8796", rain), "#18213d", night);
  const sky2 = mix(mix("#fbe7b8", "#aab2bc", rain), "#2c3358", night);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `linear-gradient(180deg, ${sky} 0%, ${sky2} 75%)` }} />
      <Glow x={1500} y={170} r={260} color="#fff1b8" a={0.9 * (1 - rain) * (1 - night)} />
      <div style={{ position: "absolute", left: 1440, top: 110, width: 120, height: 120, borderRadius: "50%", background: "#fff6d6", opacity: (1 - rain) * (1 - night), boxShadow: "0 0 60px #ffe9a0" }} />
      {/* far houses */}
      {Array.from({ length: 9 }, (_, i) => (
        <div key={i} style={{ position: "absolute", left: i * 230 - 40, top: 470 - hash(i) * 120, width: 210, height: 420, background: mix(mix("#d9b99b", "#8a8f99", rain * 0.6), "#2a2f4a", night), borderRadius: "6px 6px 0 0" }}>
          <div style={{ position: "absolute", left: -12, top: -50, width: 234, height: 60, background: mix("#b5544a", "#3a2a3a", night), clipPath: "polygon(10% 100%, 50% 0, 90% 100%)" }} />
          {[0, 1].map((k) => (
            <div key={k} style={{ position: "absolute", left: 30 + k * 100, top: 60, width: 60, height: 70, background: night > 0.5 ? (hash(i * 4 + k) > 0.4 ? "#ffd27a" : "#3a4060") : "#9fc4e0", border: "6px solid #f5ede2", boxShadow: night > 0.5 ? "0 0 30px rgba(255,210,122,0.6)" : undefined }} />
          ))}
        </div>
      ))}
      {/* pavement */}
      <div style={{ position: "absolute", left: 0, top: 860, width: W, height: 220, background: `linear-gradient(180deg, ${mix("#b9aea0", "#6f7480", rain)} 0%, ${mix("#958a7c", "#4c515c", rain)} 100%)` }} />
      <div style={{ position: "absolute", left: 0, top: 860, width: W, height: 6, background: "rgba(255,255,255,0.3)" }} />
      {rain > 0.2
        ? [300, 900, 1500].map((x, i) => (
            <div key={i} style={{ position: "absolute", left: x - 140, top: 930 + i * 20, width: 280, height: 40, borderRadius: "50%", background: rgba("#c9d8ea", 0.35 * rain), boxShadow: "inset 0 4px 10px rgba(255,255,255,0.3)" }}>
              {[0, 1].map((k) => (
                <div key={k} style={{ position: "absolute", left: 140 - ((t * 60 + k * 50 + i * 20) % 120), top: 20 - ((t * 30 + k * 25) % 60) / 3, width: (t * 120 + k * 100 + i * 40) % 240, height: ((t * 120 + k * 100 + i * 40) % 240) * 0.2, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.5)", opacity: 1 - ((t * 0.5 + k * 0.5 + i * 0.2) % 1) }} />
              ))}
            </div>
          ))
        : null}
    </AbsoluteFill>
  );
};

/** café interior back wall: menu board, shelves, pendant lights */
export const CafeBack: React.FC<{ t: number; night?: number }> = ({ t, night = 0 }) => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${mix("#5a3f2e", "#2e2028", night)} 0%, ${mix("#7a5640", "#3c2a2c", night)} 70%)` }} />
    <AbsoluteFill style={{ background: "repeating-linear-gradient(90deg, rgba(0,0,0,0.06) 0 3px, transparent 3px 90px)" }} />
    {/* menu board */}
    <div style={{ position: "absolute", left: 620, top: 300, width: 680, height: 300, borderRadius: 14, background: "#24302a", border: "14px solid #6b4a32", boxShadow: "0 20px 40px rgba(0,0,0,0.4)", fontFamily: SERIF, color: "#efe7d6" }}>
      <div style={{ textAlign: "center", fontSize: 54, marginTop: 18 }}>☕ MENU</div>
      {["拿铁 Latte", "美式 Americano", "热可可 Cocoa"].map((s, i) => (
        <div key={i} style={{ fontSize: 30, marginLeft: 60, marginTop: 10, opacity: 0.85 }}>
          {s}
        </div>
      ))}
    </div>
    {/* shelves with jars */}
    {[0, 1].map((r) => (
      <div key={r} style={{ position: "absolute", left: 1380, top: 380 + r * 170, width: 460, height: 16, background: "#6b4a32", boxShadow: "0 8px 12px rgba(0,0,0,0.3)" }}>
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} style={{ position: "absolute", left: 20 + i * 72, top: -90 + (i % 2) * 10, width: 54, height: 90 - (i % 2) * 10, borderRadius: "10px 10px 6px 6px", background: ["#c98b5a", "#e8d6b8", "#7a4a2c", "#a7c4a0", "#e8c46a", "#d9a0a0"][(i + r) % 6], opacity: 0.9 }} />
        ))}
      </div>
    ))}
    {/* pendant lamps */}
    {[300, 960, 1600].map((x, i) => (
      <div key={i} style={{ position: "absolute", left: x, top: 0, rotate: `${Math.sin(t * 0.8 + i) * 2}deg`, transformOrigin: "0 0" }}>
        <div style={{ position: "absolute", left: -1, top: 0, width: 3, height: 70, background: "#222" }} />
        <div style={{ position: "absolute", left: -46, top: 66, width: 92, height: 46, borderRadius: "46px 46px 6px 6px", background: "linear-gradient(180deg,#2e3a33,#1c241f)" }} />
        <Glow x={0} y={120} r={220} color="#ffcf8a" a={0.65} />
      </div>
    ))}
    <WarmBokeh t={t} y0={120} y1={600} seed={3} opacity={0.5} />
  </AbsoluteFill>
);

/** the window-bar seat: big window (outside = city in the current mood), wooden bar top at y=780 */
export const WindowBar: React.FC<{ t: number; rain?: number; blurOut?: number; drops?: number; mood?: Mood; children?: React.ReactNode }> = ({ t, rain = 1, blurOut = 5, drops = 1, mood, children }) => {
  const m = mood ?? moodAt(t);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: `blur(${blurOut}px)` }}>
        <AbsoluteFill style={{ background: `linear-gradient(180deg, ${m.top}, ${m.mid} 60%, ${m.low})` }} />
        <Clouds m={m} t={t} seed={6} y={-40} h={420} speed={6} density={1 + rain * 0.4} />
        <Skyline m={m} t={t} layer={0} scroll={t * 3} base={720} />
        <Skyline m={m} t={t} layer={1} scroll={t * 5 + 400} base={800} />
        <RainFx t={t} amount={rain * 0.9} />
      </AbsoluteFill>
      {/* drops on the glass */}
      {drops > 0
        ? Array.from({ length: 40 }, (_, i) => {
            const life = 3 + hash(i * 1.7) * 5;
            const cyc = Math.floor((t + hash(i * 3.3) * life) / life);
            const ph = ((t + hash(i * 3.3) * life) % life) / life;
            const x = hash(i * 9.1 + cyc * 1.3) * W;
            const slide = ph > 0.6 ? easeOut((ph - 0.6) / 0.4) * (150 + hash(i) * 300) : 0;
            const y = hash(i * 5.7 + cyc) * 600 + slide;
            const r = 4 + Math.pow(hash(i * 2.9), 2) * 10;
            return (
              <div key={i} style={{ position: "absolute", left: x - r, top: y - r, width: r * 2, height: r * 2.3, borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%", background: "radial-gradient(circle at 35% 28%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.08) 30%), radial-gradient(circle at 50% 75%, rgba(255,235,200,0.3), transparent 60%)", opacity: drops * rain * Math.min(1, ph * 8) }} />
            );
          })
        : null}
      {/* frame + mullions */}
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: 40, background: "linear-gradient(180deg,#4a3121,#2c1c12)" }} />
      <div style={{ position: "absolute", left: 0, top: 690, width: W, height: 30, background: "linear-gradient(180deg,#4a3121,#2c1c12)" }} />
      {/* interior warm reflections on glass */}
      <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.35 }}>
        <Glow x={360} y={160} r={110} color="#ffc88a" />
        <Glow x={1300} y={130} r={90} color="#ffc88a" />
      </AbsoluteFill>
      {/* bar top */}
      <div style={{ position: "absolute", left: 0, top: 720, width: W, height: 360, background: "repeating-linear-gradient(90deg, rgba(0,0,0,0.05) 0 3px, transparent 3px 13px), linear-gradient(180deg,#9a6a45 0%,#7a5236 12%,#4a3020 100%)" }} />
      <div style={{ position: "absolute", left: 0, top: 720, width: W, height: 4, background: "rgba(255,220,180,0.6)" }} />
      <div style={{ position: "absolute", left: 0, top: 724, width: W, height: 80, background: `linear-gradient(180deg, ${rgba(m.mid, 0.35)}, transparent)` }} />
      {children}
    </AbsoluteFill>
  );
};

/* ───────── shots ───────── */

const intro: ShotDef[] = [
  {
    name: "闹钟",
    a: 0,
    b: 2.6,
    draw: (t) => (
      <>
        <Bedroom t={t} light={0.4} />
        <Cam s={tw(t, [[0, 1.25], [2.6, 1.05]])} oy={65}>
          <div style={{ position: "absolute", left: 560, top: 760, width: 800, height: 40, background: "linear-gradient(180deg,#a87650,#7a5236)", borderRadius: 8 }} />
          <AlarmClock x={960} y={770} s={360} t={t} ring={t < 2.15} time="7:30" />
          {/* the hero leaps in from the left and slaps the clock quiet */}
          {t > 1.4 ? (
            <Actor
              x={tw(t, [[1.4, -260], [2.1, 650], [2.6, 630]], easeOut)}
              y={770 - Math.sin(prog(t, 1.4, 2.1) * Math.PI) * 280}
              size={300}
              t={t}
              expr={t < 2.1 ? "sleepy" : "sigh"}
              armR={t < 2.05 ? -110 : 15}
              armL={-30}
              legs={t < 2.1 ? "dangle" : "stand"}
              squash={t > 2.1 && t < 2.3 ? 0.5 : t < 2.1 ? -0.3 : 0}
              emote={t > 2.15 ? "z" : null}
              emoteT={t - 2.15}
            />
          ) : null}
          {t > 2.1 && t < 2.5 ? <div style={{ position: "absolute", left: 800, top: 300, fontFamily: SANS, fontWeight: 900, fontSize: 90, color: "#fff", textShadow: "0 4px 0 #d9573a", rotate: "-8deg" }}>啪!</div> : null}
        </Cam>
        <AbsoluteFill style={{ background: "rgba(20,30,60,0.25)" }} />
      </>
    ),
  },
  {
    name: "从被子里弹出来",
    a: 2.6,
    b: 5.3,
    tin: "cut",
    draw: (t) => {
      const pop = since(t, [3.3]);
      const up = t < 3.3 ? 0 : easeOutBack(clamp01(pop / 0.45), 2.4);
      return (
        <>
          <Bedroom t={t} light={0.8} />
          <Cam s={tw(t, [[2.6, 1.0], [5.3, 1.12]])} oy={70}>
            {/* headboard + pillow */}
            <div style={{ position: "absolute", left: 360, top: 330, width: 1200, height: 420, borderRadius: "40px 40px 0 0", background: "linear-gradient(180deg,#b07a52,#8a5a3a)" }} />
            <div style={{ position: "absolute", left: 640, top: 560, width: 640, height: 170, borderRadius: 80, background: "linear-gradient(180deg,#ffffff,#e8e2da)" }} />
            <Actor x={960} y={lerp(840, 660, up)} size={360} t={t} expr={kf(t, [[2.6, "sleepy"], [4.1, "surprised"]])} emote={kf<"z" | "!" | null>(t, [[2.6, "z"], [3.3, null], [4.1, "!"]])} emoteT={since(t, [2.6, 4.1])} armL={kf(t, [[2.6, 40], [3.4, -60], [4.1, -80]])} armR={kf(t, [[2.6, 40], [3.4, -40], [4.1, -80]])} squash={t < 3.3 ? 0.5 : (1 - clamp01(pop / 0.5)) * -0.7} legs="dangle" />
            {/* quilt */}
            <div style={{ position: "absolute", left: 300, top: 700 + (t < 3.3 ? Math.sin(t * 3) * 6 : 20), width: 1320, height: 420, borderRadius: "80px 80px 0 0", background: "repeating-linear-gradient(45deg, #7aa6d6 0 40px, #6b97c8 40px 80px)", boxShadow: "inset 0 20px 40px rgba(255,255,255,0.3)" }} />
            {/* feathers */}
            {t > 3.3
              ? Array.from({ length: 10 }, (_, i) => {
                  const q = clamp01((t - 3.3) / 2);
                  return <div key={i} style={{ position: "absolute", left: 960 + (hash(i) - 0.5) * 900 * easeOut(q), top: 620 - easeOut(q) * 300 + q * q * 400, width: 40, height: 16, borderRadius: "50%", background: "#fff", rotate: `${t * 200 * (hash(i) - 0.5)}deg`, opacity: 1 - q }} />;
                })
              : null}
          </Cam>
        </>
      );
    },
  },
  {
    name: "雾窗写歌名",
    a: 5.3,
    b: 10.2,
    tin: "zoom",
    draw: (t) => {
      const w1 = prog(t, 5.6, 7.4); // 天天
      const w2 = prog(t, 7.6, 8.6); // 演唱者
      const writing = t < 7.4 ? w1 : t < 8.6 ? w2 : 1;
      const penX = t < 7.4 ? lerp(620, 1300, w1) : lerp(820, 1100, w2);
      const penY = t < 7.4 ? 400 + Math.sin(w1 * 30) * 60 : 640 + Math.sin(w2 * 26) * 30;
      const tip = handAt(380, 1, -60);
      const ax = penX - tip.x;
      const ay = penY - tip.y;
      return (
        <>
          {/* outside: bright morning street, seen through glass */}
          <AbsoluteFill style={{ filter: "blur(6px)" }}>
            <Street t={t} rain={0} />
          </AbsoluteFill>
          {/* fog with the wiped text as a cut-out */}
          <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0 }}>
            <defs>
              <mask id="fogText">
                <rect width={W} height={H} fill="white" />
                <clipPath id="w1c">
                  <rect x={0} y={0} width={lerp(560, 1360, w1)} height={560} />
                </clipPath>
                <clipPath id="w2c">
                  <rect x={0} y={560} width={lerp(780, 1140, w2)} height={300} />
                </clipPath>
                <text x={960} y={500} textAnchor="middle" fontFamily={SERIF} fontWeight={900} fontSize={300} fill="black" clipPath="url(#w1c)" letterSpacing={40}>
                  天天
                </text>
                <text x={960} y={720} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={110} fill="black" clipPath="url(#w2c)" letterSpacing={30}>
                  演唱者
                </text>
              </mask>
              <filter id="fogN">
                <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves={3} seed={4} />
                <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.35 0.5" />
              </filter>
            </defs>
            <g mask="url(#fogText)">
              <rect width={W} height={H} fill="rgba(235,240,245,0.72)" />
              <rect width={W} height={H} filter="url(#fogN)" opacity={0.6} />
            </g>
          </svg>
          {/* drips running from the letters */}
          {Array.from({ length: 9 }, (_, i) => {
            const st = 6.2 + i * 0.35;
            const q = clamp01((t - st) / 2.5);
            if (q <= 0) return null;
            return <div key={i} style={{ position: "absolute", left: 640 + i * 75, top: 470 + (i % 2) * 20, width: 8, height: easeOut(q) * (120 + hash(i) * 120), borderRadius: 4, background: "linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.6))" }} />;
          })}
          {/* window frame */}
          <div style={{ position: "absolute", inset: 0, border: "50px solid #5a3b28", boxShadow: "inset 0 0 40px rgba(0,0,0,0.5)" }} />
          <Actor x={ax} y={ay} size={380} t={t} expr={t < 8.8 ? "determined" : "joy"} armR={t < 8.8 ? -60 + Math.sin(t * 22) * 8 * (writing < 1 ? 1 : 0) : -70} armL={t < 8.8 ? 30 : -70} lookX={0.8} lookY={-0.4} emote={t > 8.8 ? "♪" : null} emoteT={t - 8.8} legs="dangle" />
          <Twinkles t={t} x={960} y={420} r={500} n={12} opacity={prog(t, 8.6, 9.2)} />
        </>
      );
    },
  },
  {
    name: "撕日历 + 锁屏",
    a: 10.2,
    b: 16.4,
    tin: "whip",
    draw: (t) => {
      const lock = prog(t, 12.6, 13.2);
      return (
        <>
          <Bedroom t={t} />
          {lock < 1 ? (
            <AbsoluteFill style={{ opacity: 1 - lock }}>
              <Cam s={tw(t, [[10.2, 1.0], [12.6, 1.15]])} ox={55} oy={50}>
                <div style={{ position: "absolute", left: 0, top: 0 }}>
                  <Calendar t={t} flips={[11.1]} x={760} y={200} w={420} startDay={31} />
                </div>
                <Actor x={560} y={980} size={420} t={t} expr={kf(t, [[10.2, "determined"], [11.2, "joy"]])} armR={tw(t, [[10.2, -20], [10.9, -75], [11.2, -10]])} armL={kf(t, [[10.2, 20], [11.2, -70]])} lookX={0.8} lookY={-0.8} squash={t > 11.1 && t < 11.4 ? 0.4 : 0} emote={t > 11.2 ? "♪" : null} emoteT={t - 11.2} />
              </Cam>
            </AbsoluteFill>
          ) : null}
          {lock > 0 ? (
            <AbsoluteFill style={{ opacity: lock }}>
              <AbsoluteFill style={{ background: "rgba(40,30,30,0.45)" }} />
              <Cam s={tw(t, [[12.6, 1.1], [16.4, 1.0]])}>
                <Phone x={1180} y={130} w={400} tilt={-4} glow={0.8}>
                  <div style={{ position: "absolute", inset: 0, filter: "brightness(0.9)" }}>
                    <Memory kind={1} w={400} />
                  </div>
                  <div style={{ position: "absolute", left: 0, right: 0, top: 120, textAlign: "center", fontFamily: SANS, fontWeight: 300, fontSize: 120, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.4)" }}>7:31</div>
                  <div style={{ position: "absolute", left: 0, right: 0, top: 260, textAlign: "center", fontFamily: SANS, fontSize: 26, color: "#fff" }}>星期一 · 小雨</div>
                </Phone>
                {/* mittens holding the phone */}
                <div style={{ position: "absolute", left: 1120, top: 820, width: 140, height: 120, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #fff3df, #ffe6c2 60%, #f0cfa0)", border: "6px solid #1b1a14", boxSizing: "border-box", boxShadow: "5px 5px 0 rgba(215,38,61,0.5)" }} />
                <div style={{ position: "absolute", left: 1520, top: 800, width: 140, height: 120, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #fff3df, #ffe6c2 60%, #f0cfa0)", border: "6px solid #1b1a14", boxSizing: "border-box", boxShadow: "5px 5px 0 rgba(215,38,61,0.5)" }} />
                <Twinkles t={t} x={1380} y={480} r={320} n={8} color="#ffd9e2" />
              </Cam>
            </AbsoluteFill>
          ) : null}
        </>
      );
    },
  },
];

/* ───────── verse 1: rainy café ───────── */

const verse1: ShotDef[] = [
  {
    name: "1 出门：晴转雨，撑伞",
    a: Ls(1) - 0.6,
    b: Ls(2) - 0.4,
    tin: "iris",
    ix: 50,
    iy: 60,
    draw: (t) => {
      const a0 = Ls(1) - 0.6;
      const door = easeInOut(prog(t, a0, a0 + 0.8));
      const rain = easeInOut(prog(t, Ls(1) + 1.6, Ls(1) + 2.4));
      const cloudX = tw(t, [[Ls(1) + 0.8, 2300], [Ls(1) + 2.2, 1300]], easeOut);
      const open = prog(t, Ls(1) + 2.6, Ls(1) + 3.1);
      const walkX = tw(t, [[a0 + 0.6, 760], [Ls(1) + 1.6, 900]]);
      const tip = handAt(320, 1, -70);
      return (
        <>
          <Street t={t} rain={rain} />
          {/* storm cloud sliding over the sun */}
          <div style={{ position: "absolute", left: cloudX, top: 40, width: 620, height: 260 }}>
            {[0, 1, 2, 3].map((k) => (
              <div key={k} style={{ position: "absolute", left: [0, 140, 300, 440][k], top: [90, 20, 0, 80][k], width: [240, 260, 280, 200][k], height: [170, 220, 240, 160][k], borderRadius: "50%", background: "radial-gradient(circle at 45% 35%, #a3a9b4, #6b717c)" }} />
            ))}
          </div>
          <RainFx t={t} amount={rain} />
          {/* front door of the house, opening */}
          <div style={{ position: "absolute", left: 560, top: 300, width: 420, height: 560, background: "#3a2a20", boxShadow: "inset 0 0 40px rgba(0,0,0,0.6)" }}>
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg,#ffdca0,#f0b070)", opacity: 0.5 }} />
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg,#3f7f6a,#2f6655)", transformOrigin: "0 50%", transform: `perspective(1600px) rotateY(${-door * 95}deg)`, border: "10px solid #2a5244" }}>
              <div style={{ position: "absolute", right: 30, top: 270, width: 26, height: 26, borderRadius: "50%", background: "#e8c46a" }} />
            </div>
          </div>
          <div style={{ position: "absolute", left: 540, top: 270, width: 460, height: 40, background: "#5a3b28" }} />
          <Actor
            x={walkX}
            y={880}
            size={320}
            t={t}
            legs={t < Ls(1) + 1.6 ? "walk" : "stand"}
            phase={t * 2}
            expr={kf(t, [[a0, "happy"], [Ls(1) + 1.8, "surprised"], [Ls(1) + 2.6, "sigh"], [Ls(1) + 3.2, "neutral"]])}
            lookY={kf(t, [[a0, 0], [Ls(1) + 1.3, -1]])}
            emote={kf<"♪" | "!" | "..." | null>(t, [[a0, "♪"], [Ls(1) + 1.8, "!"], [Ls(1) + 2.6, "..."]])}
            emoteT={since(t, [a0, Ls(1) + 1.8, Ls(1) + 2.6])}
            armR={t > Ls(1) + 2.4 ? -70 : 20}
            armL={kf(t, [[a0, -30], [Ls(1) + 1.8, -70], [Ls(1) + 2.4, 30]])}
          />
          {t > Ls(1) + 2.4 ? <Umbrella x={walkX + tip.x} y={880 + tip.y + 20} size={300} open={open} color="#f2c14e" /> : null}
        </>
      );
    },
  },
  {
    name: "2 咖啡店排队，人挤人",
    a: Ls(2) - 0.4,
    b: Ls(3) - 0.4,
    tin: "wipe",
    draw: (t) => {
      const a0 = Ls(2) - 0.4;
      const give = prog(t, Ls(2) + 2.0, Ls(2) + 2.6);
      const shuffle = Math.floor((t - a0) / 0.9);
      return (
        <>
          <CafeBack t={t} />
          {/* counter */}
          <div style={{ position: "absolute", left: 1200, top: 560, width: 720, height: 520, background: "linear-gradient(180deg,#8a5a3a,#5a3a26)", boxShadow: "0 -6px 20px rgba(0,0,0,0.4)" }} />
          <div style={{ position: "absolute", left: 1190, top: 545, width: 740, height: 28, background: "#c9a27c" }} />
          <div style={{ position: "absolute", left: 0, top: 940, width: W, height: 140, background: "repeating-linear-gradient(90deg,#6b4a34 0 120px,#5e4130 120px 240px)" }} />
          <Cam x={tw(t, [[a0, 0], [Ls(3) - 0.4, -80]])}>
            {/* queue of tall legs; the hero is squeezed in between */}
            {[
              { x: 220, pants: "#3b4a6b", shoes: "#2a2a30" },
              { x: 470, pants: "#8a5a5a", shoes: "#f2f2f2", skirt: true },
              { x: 1000, pants: "#4a6b4a", shoes: "#3a2a20" },
              { x: 1250, pants: "#2a2a34", shoes: "#c94a4a" },
            ].map((l, i) => (
              <Legs key={i} x={l.x + (shuffle % 2) * 6 + Math.sin(t * 2 + i) * 4} y={980} h={640} t={t} walk={0.15} pants={l.pants} shoes={l.shoes} skirt={l.skirt} />
            ))}
            <Actor x={760} y={980} size={240} t={t} expr={give < 0.5 ? "nervous" : "joy"} emote={give < 0.5 ? "sweat" : "♥"} emoteT={since(t, [a0, Ls(2) + 2.3])} squash={give < 0.5 ? 0.25 + Math.sin(t * 9) * 0.05 : -0.3} armL={give < 0.5 ? 50 : -80} armR={give < 0.5 ? 50 : -80} lookY={-1} tilt={give < 0.5 ? Math.sin(t * 7) * 3 : 0} />
            {/* barista hand lowering a tiny latte */}
            <Hand x={lerp(1250, 860, easeOut(give))} y={lerp(300, 600, easeOut(give))} s={160} sleeve="#2f4a3a" />
            <Cup x={lerp(1250, 860, easeOut(give)) - 90} y={lerp(300, 600, easeOut(give)) + 40} w={90} t={t} paper />
          </Cam>
        </>
      );
    },
  },
  {
    name: "3 端着咖啡找角落，爬上高脚凳",
    a: Ls(3) - 0.4,
    b: Ls(4) - 0.5,
    tin: "whip",
    draw: (t) => {
      const a0 = Ls(3) - 0.4;
      const climbAt = Ls(3) + 3.2;
      if (t < climbAt) {
        // weaving between legs, cup held high; foreground legs pass by
        return (
          <>
            <CafeBack t={t} />
            <div style={{ position: "absolute", left: 0, top: 940, width: W, height: 140, background: "repeating-linear-gradient(90deg,#6b4a34 0 120px,#5e4130 120px 240px)", backgroundPositionX: -t * 200 }} />
            {[0, 1, 2, 3, 4, 5].map((i) => {
              const x = ((i * 420 - (t - a0) * 520) % 2520 + 2520) % 2520 - 300;
              return <Legs key={i} x={x} y={1000} h={720} t={t} walk={0.8} pants={["#3b4a6b", "#6b3b4a", "#2a2a34", "#4a6b4a", "#7a6a4a", "#3a4a5a"][i]} shoes="#2a2a30" />;
            })}
            <Actor x={900 + Math.sin(t * 3) * 120} y={980} size={260} t={t} legs="run" phase={t * 3} expr="determined" armL={-85} armR={-85} lookX={Math.sin(t * 3) > 0 ? 0.8 : -0.8} emote="spark" emoteT={t - a0} />
            <Cup x={900 + Math.sin(t * 3) * 120} y={980 - 260 * 0.62 - 50} w={80} t={t} paper />
            <AbsoluteFill style={{ filter: "blur(10px)" }}>
              {[0, 1].map((i) => {
                const x = ((i * 1100 - (t - a0) * 900) % 2200 + 2200) % 2200 - 300;
                return <Legs key={i} x={x} y={1200} h={1100} t={t} walk={1} pants={i ? "#22303f" : "#5a2f2f"} shoes="#111" />;
              })}
            </AbsoluteFill>
          </>
        );
      }
      // climbing the stool at the window bar, then the latte art from above
      const art = t > Ls(3) + 5.6;
      if (art) {
        const d = prog(t, Ls(3) + 5.7, Ls(3) + 7.0);
        return (
          <AbsoluteFill style={{ background: "repeating-linear-gradient(90deg, rgba(0,0,0,0.05) 0 3px, transparent 3px 13px), linear-gradient(180deg,#8a5e3e,#6a4630)" }}>
            <Cam s={tw(t, [[Ls(3) + 5.6, 1.3], [Ls(4), 1.05]])}>
              <LatteTop x={960} y={650} r={250} draw={d} />
              <div style={{ position: "absolute", left: 960 - 500, top: 650, width: 150, height: 120, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #fff3df, #ffe6c2 60%, #f0cfa0)", border: "6px solid #1b1a14", boxSizing: "border-box", boxShadow: "5px 5px 0 rgba(215,38,61,0.5)" }} />
              <div style={{ position: "absolute", left: 960 + 350, top: 650, width: 150, height: 120, borderRadius: "50%", background: "radial-gradient(circle at 40% 35%, #fff3df, #ffe6c2 60%, #f0cfa0)", border: "6px solid #1b1a14", boxSizing: "border-box", boxShadow: "5px 5px 0 rgba(215,38,61,0.5)" }} />
              <Twinkles t={t} x={960} y={630} r={300} n={10} opacity={d} />
            </Cam>
          </AbsoluteFill>
        );
      }
      const hops = [climbAt, climbAt + 0.7, climbAt + 1.4];
      const k = Math.min(2, Math.floor((t - climbAt) / 0.7));
      const hp = clamp01((t - hops[k]) / 0.55);
      const levels = [980, 900, 830, 760];
      const y = lerp(levels[k], levels[k + 1], easeOut(hp)) - Math.sin(hp * Math.PI) * 120;
      return (
        <WindowBar t={t} rain={1}>
          <div style={{ position: "absolute", left: 760, top: 830, width: 320, height: 40, borderRadius: 20, background: "#3a2a20" }} />
          <div style={{ position: "absolute", left: 900, top: 860, width: 40, height: 220, background: "#2a1e18" }} />
          <div style={{ position: "absolute", left: 810, top: 900, width: 220, height: 24, borderRadius: 12, background: "#3a2a20" }} />
          <Actor x={920} y={y} size={300} t={t} expr={hp < 1 || k < 2 ? "determined" : "happy"} squash={hp < 0.15 ? 0.5 : hp > 0.9 ? 0.3 : -0.4} legs={hp < 1 && hp > 0.1 ? "dangle" : "stand"} armL={-60} armR={-60} emote={k === 2 && hp >= 1 ? "♪" : "sweat"} emoteT={since(t, [climbAt, hops[2] + 0.55])} />
          <Cup x={1180} y={760} w={110} t={t} />
        </WindowBar>
      );
    },
  },
  {
    name: "4 越过杯口偷看情侣",
    a: Ls(4) - 0.5,
    b: Ls(5) - 0.4,
    tin: "blur",
    draw: (t) => {
      const focus = prog(t, Ls(4) + 2.0, Ls(4) + 2.6); // 0 = couple sharp, 1 = hero sharp
      const lean = tw(t, [[Ls(4) - 0.5, 0], [Ls(4) + 1.6, 1]]);
      return (
        <>
          <CafeBack t={t} />
          <AbsoluteFill style={{ filter: `blur(${focus * 10}px)` }}>
            {/* next table: two people leaning in, sharing a cake */}
            <div style={{ position: "absolute", left: 640, top: 760, width: 760, height: 40, borderRadius: 20, background: "#6b4a32" }} />
            <Shoulders x={820 + lean * 50} y={790} w={330} color="#c96a5a" hair="#3a2a20" lean={lean * 12} />
            <Shoulders x={1220 - lean * 50} y={790} w={320} color="#e8d6b8" hair="#2a1e18" lean={-lean * 12} longHair flip />
            <div style={{ position: "absolute", left: 960, top: 720, width: 120, height: 50, borderRadius: "0 0 60px 60px", background: "#fff" }} />
            <div style={{ position: "absolute", left: 980, top: 680, width: 80, height: 50, background: "linear-gradient(180deg,#ffd0dc,#f5a3b8)", borderRadius: 8 }} />
            <div style={{ position: "absolute", left: 1010, top: 660, width: 20, height: 20, borderRadius: "50%", background: "#e0304a" }} />
            <HeartBurst t={t} t0={Ls(4) + 0.8} x={1020} y={560} n={8} spread={200} dur={2.5} size={40} />
          </AbsoluteFill>
          {/* foreground: the hero peeking over its cup (blurred until focus pulls) */}
          <AbsoluteFill style={{ filter: `blur(${(1 - focus) * 12}px)` }}>
            <Actor x={1560} y={1180} size={620} t={t} expr={focus < 0.5 ? "dreamy" : "sad"} lookX={-1} lookY={-0.2} blush={0.4} armL={-30} armR={40} emote={focus > 0.5 ? "..." : null} emoteT={t - Ls(4) - 2.3} shadow={false} />
            <Cup x={1290} y={1120} w={300} t={t} steam={0.6} />
          </AbsoluteFill>
        </>
      );
    },
  },
  {
    name: "5 慢慢转头看向窗外",
    a: Ls(5) - 0.4,
    b: Ls(6) - 0.5,
    tin: "fade",
    dur: 0.8,
    draw: (t) => {
      const turn = easeInOut(prog(t, Ls(5) + 0.2, Ls(5) + 2.6));
      return (
        <>
          {/* from outside the window, looking in: hero behind wet glass */}
          <AbsoluteFill style={{ background: "linear-gradient(180deg,#5a3f2e,#3a2a20)" }}>
            <WarmBokeh t={t} y0={100} y1={700} seed={9} size={1.2} opacity={0.8} />
          </AbsoluteFill>
          <Cam s={tw(t, [[Ls(5) - 0.4, 1.0], [Ls(6), 1.18]])} oy={60}>
            <div style={{ position: "absolute", left: 0, top: 760, width: W, height: 320, background: "linear-gradient(180deg,#8a5e3e,#4a3020)" }} />
            <Actor x={960} y={770} size={480} t={t} expr={turn < 0.5 ? "sad" : "sigh"} lookX={lerp(1, -0.1, turn)} lookY={0.3} squash={turn * 0.35} tilt={turn * 4} armL={60} armR={60} emote={turn > 0.6 ? "..." : null} emoteT={t - Ls(5) - 1.8} />
            <Cup x={1300} y={770} w={150} t={t} />
          </Cam>
          {/* the glass in front: cool tint, reflections, sliding drops */}
          <AbsoluteFill style={{ background: "linear-gradient(115deg, rgba(150,180,220,0.25), rgba(40,60,90,0.2))" }} />
          <RainFx t={t} amount={0.8} />
          {Array.from({ length: 26 }, (_, i) => {
            const ph = ((t * (0.12 + hash(i) * 0.1) + hash(i * 3)) % 1);
            const r = 6 + hash(i * 2) * 12;
            return <div key={i} style={{ position: "absolute", left: hash(i * 7) * W, top: -40 + ph * 1160, width: r * 2, height: r * 2.4, borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%", background: "radial-gradient(circle at 35% 28%, rgba(255,255,255,0.9), rgba(255,255,255,0.08) 35%)" }} />;
          })}
        </>
      );
    },
  },
  {
    name: "6 手机：置顶的她",
    a: Ls(6) - 0.5,
    b: Ls(7) - 0.5,
    tin: "zoom",
    draw: (t) => (
      <>
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 60% 40%, #6a4a3a, #2a1c16)" }}>
          <WarmBokeh t={t} y0={60} y1={900} seed={12} size={1.3} opacity={0.6} />
        </AbsoluteFill>
        <Cam s={tw(t, [[Ls(6) - 0.5, 1.0], [Ls(7), 1.08]])}>
          <Phone x={1080} y={120} w={400} tilt={3}>
            <ChatScreen
              w={400}
              t={t}
              title="她 ♡"
              msgs={[
                { text: "今天也下雨了吗", at: Ls(6) - 0.4 },
                { me: true, text: "嗯，下了一整天", at: Ls(6) - 0.2 },
                { text: "晚安 🌙", at: Ls(6) + 0.3 },
              ]}
              typing=""
            />
            <div style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center", fontFamily: SANS, fontSize: 18, color: "#999" }}>昨天 23:12</div>
          </Phone>
          <Actor x={620} y={980} size={520} t={t} expr={kf(t, [[Ls(6) - 0.5, "dreamy"], [Ls(6) + 2.0, "shy"]])} lookX={1} lookY={-0.8} blush={prog(t, Ls(6) + 1.6, Ls(6) + 2.4)} armR={-35} armL={30} emote={kf<"?" | "♥">(t, [[Ls(6) - 0.5, "?"], [Ls(6) + 2.0, "♥"]])} emoteT={since(t, [Ls(6) - 0.5, Ls(6) + 2.0])} />
        </Cam>
      </>
    ),
  },
];

/* ───────── pre-chorus 1: the heart flies across the city ───────── */

export const MapView: React.FC<{ t: number; route: number; night?: number; lit?: number }> = ({ t, route, night = 0, lit = 0 }) => {
  const ground = mix("#efe4cf", "#1c2238", night);
  const block = mix("#e2d3b8", "#2a3150", night);
  const park = mix("#b8d8a0", "#24402e", night);
  const road = mix("#fffaf0", "#4a5278", night);
  const pts: [number, number][] = [
    [300, 860],
    [300, 640],
    [760, 640],
    [760, 380],
    [1240, 380],
    [1240, 220],
    [1620, 220],
  ];
  const lens = pts.slice(1).map((p, i) => Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]));
  const total = lens.reduce((a, b) => a + b, 0);
  let left = route * total;
  let hx = pts[0][0];
  let hy = pts[0][1];
  const drawn: string[] = [`M${pts[0][0]} ${pts[0][1]}`];
  for (let i = 0; i < lens.length && left > 0; i++) {
    const f = Math.min(1, left / lens[i]);
    hx = lerp(pts[i][0], pts[i + 1][0], f);
    hy = lerp(pts[i][1], pts[i + 1][1], f);
    drawn.push(`L${hx} ${hy}`);
    left -= lens[i];
  }
  return (
    <AbsoluteFill style={{ background: ground }}>
      {/* city blocks */}
      {Array.from({ length: 8 }, (_, r) =>
        Array.from({ length: 12 }, (_, c) => {
          const x = c * 170 + 20;
          const y = r * 140 + 20;
          const isPark = hash(r * 31 + c) > 0.86;
          const near = Math.hypot(x + 70 - hx, y + 55 - hy) < 260;
          return (
            <div key={`${r}-${c}`} style={{ position: "absolute", left: x, top: y, width: 140, height: 110, borderRadius: 14, background: isPark ? park : block, boxShadow: near && route > 0 ? `0 0 40px ${rgba(night > 0.5 ? "#ffcf73" : "#ffb38a", 0.8)}` : "0 4px 0 rgba(0,0,0,0.08)" }}>
              {night > 0.5 && !isPark
                ? Array.from({ length: 6 }, (_, k) => <div key={k} style={{ position: "absolute", left: 14 + (k % 3) * 40, top: 16 + Math.floor(k / 3) * 44, width: 22, height: 20, background: hash(r * 9 + c * 3 + k) > 0.5 ? "#ffcf73" : "#3a4268", opacity: 0.8 }} />)
                : null}
            </div>
          );
        }),
      )}
      {/* river */}
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <path d="M-50 480 C 400 420, 600 560, 1000 500 S 1600 600, 1980 520" stroke={mix("#9cc8e8", "#2c4a78", night)} strokeWidth={70} fill="none" opacity={0.9} />
        <path d={drawn.join(" ")} stroke={night > 0.5 ? "#ff8fc0" : "#ff6f61"} strokeWidth={14} strokeDasharray="2 26" strokeLinecap="round" fill="none" />
        <path d={drawn.join(" ")} stroke={rgba(night > 0.5 ? "#ff8fc0" : "#ff6f61", 0.25)} strokeWidth={40} strokeLinecap="round" fill="none" />
      </svg>
      {/* roads between blocks */}
      <AbsoluteFill style={{ background: `repeating-linear-gradient(90deg, transparent 0 160px, ${road} 160px 170px), repeating-linear-gradient(180deg, transparent 0 130px, ${road} 130px 140px)`, opacity: 0.6 }} />
      {/* pins */}
      <div style={{ position: "absolute", left: 300 - 50, top: 860 - 120, width: 100, height: 120, fontSize: 80, textAlign: "center" }}>☕</div>
      <div style={{ position: "absolute", left: 1620 - 60, top: 220 - 140, width: 120, height: 120, borderRadius: "50% 50% 50% 0", rotate: "-45deg", background: HER, boxShadow: `0 0 ${30 + lit * 80}px ${rgba("#ffcf73", 0.4 + lit * 0.5)}` }} />
      <div style={{ position: "absolute", left: 1620 - 30, top: 220 - 110, width: 60, height: 60, fontSize: 44, textAlign: "center", color: "#fff" }}>⌂</div>
      {route > 0 && route < 1 ? <PixelHeart x={hx} y={hy - 30} size={90} glow={0.9} style={{ scale: String(1 + pulseAt(t) * 0.3) }} /> : null}
    </AbsoluteFill>
  );
};

const pre1: ShotDef[] = [
  {
    name: "7 心咚咚跳",
    a: Ls(7) - 0.5,
    b: Ls(8) - 0.5,
    tin: "iris",
    draw: (t) => {
      const grow = tw(t, [[Ls(7), 0.6], [Ls(8) - 0.6, 1.7]], easeIn);
      const beat = pulseAt(t);
      return (
        <>
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 55%, #6a3a40, #24141a)" }}>
            <WarmBokeh t={t} y0={0} y1={1080} seed={21} size={1.5} opacity={0.7} />
          </AbsoluteFill>
          <AbsoluteFill style={{ boxShadow: `inset 0 0 ${200 + beat * 200}px ${rgba("#ff5f8f", 0.35 + beat * 0.3)}` }} />
          <Actor x={960} y={1110} size={720} t={t} expr={kf(t, [[Ls(7) - 0.5, "surprised"], [Ls(7) + 1.2, "love"]])} blush={0.7} lookY={0.6} armL={50} armR={50} squash={-beat * 0.15} shadow={false} />
          <PixelHeart x={960} y={880} size={200 * grow * (1 + beat * 0.35)} glow={1} />
          {[0, 1].map((k) => {
            const q = ((t * 1.6 + k * 0.5) % 1);
            return <div key={k} style={{ position: "absolute", left: 960 - 200 * q * 2, top: 880 - 200 * q * 2, width: 400 * q * 2, height: 400 * q * 2, borderRadius: "50%", border: `6px solid ${rgba("#ff8fab", 1 - q)}` }} />;
          })}
          <div style={{ position: "absolute", left: 1300, top: 520, fontFamily: SANS, fontWeight: 900, fontSize: 90, color: "#ffd0dc", rotate: "12deg", opacity: beat, scale: String(0.8 + beat * 0.4) }}>咚!</div>
        </>
      );
    },
  },
  {
    name: "8 飞向远方（地图）",
    a: Ls(8) - 0.5,
    b: Ls(9) - 0.5,
    tin: "zoom",
    draw: (t) => {
      const route = easeInOut(prog(t, Ls(8), Ls(8) + 3.6));
      return (
        <Cam s={tw(t, [[Ls(8) - 0.5, 1.5], [Ls(8) + 1.5, 1.25], [Ls(9), 1.1]])} ox={lerp(18, 82, route)} oy={lerp(78, 22, route)} r={tw(t, [[Ls(8) - 0.5, -6], [Ls(9), 2]])}>
          <MapView t={t} route={route} lit={prog(t, Ls(8) + 3.4, Ls(8) + 4)} />
        </Cam>
      );
    },
  },
  {
    name: "9 她在窗边浇花，心贴上窗户",
    a: Ls(9) - 0.5,
    b: Ls(10) - 0.5,
    tin: "iris",
    ix: 70,
    iy: 30,
    draw: (t) => {
      const stick = easeOutBack(prog(t, Ls(9) + 0.2, Ls(9) + 0.9), 1.6);
      const fog = prog(t, Ls(9) + 1.0, Ls(9) + 2.2);
      return (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(180deg,#c9b6a8,#b39e90)" }} />
          {/* building wall + window */}
          <AbsoluteFill style={{ background: "repeating-linear-gradient(180deg, rgba(0,0,0,0.05) 0 2px, transparent 2px 60px)" }} />
          <div style={{ position: "absolute", left: 440, top: 260, width: 1040, height: 650, background: "linear-gradient(180deg,#ffe2b0,#f7c98a)", border: "30px solid #f4ede2", boxShadow: "0 0 140px rgba(255,200,120,0.6), inset 0 0 60px rgba(160,90,40,0.3)" }}>
            {/* curtain */}
            <div style={{ position: "absolute", left: -10, top: 0, width: 200, height: 590, background: "repeating-linear-gradient(90deg,#f7a8b8 0 30px,#f290a6 30px 60px)", borderRadius: "0 0 80px 0" }} />
            {/* plant */}
            <div style={{ position: "absolute", left: 620, top: 420, width: 140, height: 120, borderRadius: "10px 10px 40px 40px", background: "#d9774f" }} />
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} style={{ position: "absolute", left: 670, top: 420, width: 40, height: 140 + i * 10, borderRadius: "50% 50% 50% 50% / 80% 80% 20% 20%", background: i % 2 ? "#5aa055" : "#3f8a44", rotate: `${-50 + i * 20 + Math.sin(t + i) * 3}deg`, transformOrigin: "50% 100%", translate: `0 ${-140 - i * 10}px` }} />
            ))}
          </div>
          {/* her, watering */}
          <Actor x={900} y={830} size={360} t={t} her expr={kf(t, [[Ls(9) - 0.5, "happy"], [Ls(9) + 2.2, "surprised"]])} armR={-30} armL={20} emote={kf<"♪" | "?">(t, [[Ls(9) - 0.5, "♪"], [Ls(9) + 2.2, "?"]])} emoteT={since(t, [Ls(9) - 0.5, Ls(9) + 2.2])} lookX={kf(t, [[Ls(9) - 0.5, 1], [Ls(9) + 2.2, -0.6]])} tilt={Math.sin(t * 3) * 3} />
          {/* watering can + stream */}
          <div style={{ position: "absolute", left: 1040, top: 560, width: 120, height: 90, borderRadius: "20px 20px 30px 30px", background: "#7ab8d9", rotate: "25deg" }}>
            <div style={{ position: "absolute", left: 110, top: 10, width: 90, height: 16, background: "#7ab8d9", rotate: "-30deg", transformOrigin: "0 50%" }} />
          </div>
          {Array.from({ length: 8 }, (_, i) => <div key={i} style={{ position: "absolute", left: 1200 + i * 4, top: 560 + ((t * 300 + i * 30) % 120), width: 6, height: 14, borderRadius: 3, background: "#9fd6f5" }} />)}
          {/* fog heart on the glass around the stuck heart */}
          <div style={{ position: "absolute", left: 1180 - 160, top: 430 - 150, width: 320, height: 300, fontSize: 360, lineHeight: "300px", textAlign: "center", color: rgba("#ffffff", 0.5 * fog), filter: "blur(10px)" }}>♥</div>
          <PixelHeart x={lerp(2100, 1180, stick)} y={lerp(-200, 430, stick)} size={130} glow={0.9} style={{ scale: String(1 + pulseAt(t) * 0.2) }} />
        </>
      );
    },
  },
  {
    name: "10 一口喝完，抓起车钥匙冲出去",
    a: Ls(10) - 0.5,
    b: 65.9,
    tin: "whipL",
    draw: (t) => {
      const gulpEnd = Ls(10) + 1.6;
      const keysAt = Ls(10) + 2.4;
      const jumpAt = Ls(10) + 3.6;
      const keyFly = prog(t, keysAt, keysAt + 0.5);
      const jump = prog(t, jumpAt, jumpAt + 0.6);
      const run = prog(t, jumpAt + 0.6, 65.9);
      const x = t < jumpAt ? 900 : lerp(900, 1100, jump) + easeIn(run) * 1400;
      const y = t < jumpAt ? 760 : t < jumpAt + 0.6 ? lerp(760, 1000, jump) - Math.sin(jump * Math.PI) * 160 : 1000;
      const tip = handAt(300, 1, -25);
      return (
        <>
          <WindowBar t={t} rain={1}>
            <Actor
              x={x}
              y={y}
              size={300}
              t={t}
              expr={kf(t, [[Ls(10) - 0.5, "determined"], [gulpEnd, "joy"], [keysAt + 0.5, "determined"]])}
              armR={t < gulpEnd ? -100 : t < keysAt + 0.5 ? -20 : -25}
              armL={t < gulpEnd ? -60 : 30}
              tilt={t < gulpEnd ? -18 : 0}
              squash={t > gulpEnd && t < gulpEnd + 0.3 ? 0.5 : 0}
              legs={t > jumpAt + 0.6 ? "run" : t > jumpAt ? "dangle" : "stand"}
              phase={t * 3.2}
              emote={kf<"spark" | "!" | null>(t, [[Ls(10) - 0.5, null], [gulpEnd, "spark"], [keysAt, "!"]])}
              emoteT={since(t, [gulpEnd, keysAt])}
              lookY={t < gulpEnd ? -1 : 0}
            />
            {/* the cup tipping over its face while gulping, then set down */}
            {t < gulpEnd ? <div style={{ position: "absolute", left: x + 30, top: y - 110, rotate: `${140 + Math.sin(t * 8) * 6}deg` }}><Cup x={0} y={0} w={110} t={t} steam={0} /></div> : <Cup x={1180} y={760} w={110} t={t} steam={0} />}
            {/* keys flying into the hand with a light arc */}
            {t > keysAt ? (
              <>
                <Keys x={lerp(1450, x + tip.x + 20, easeOut(keyFly))} y={lerp(740, y + tip.y, easeOut(keyFly)) - Math.sin(keyFly * Math.PI) * 220} s={90} rot={keyFly * 540} />
                {keyFly < 1 ? <Twinkles t={t} x={lerp(1450, x + tip.x, keyFly)} y={lerp(700, y + tip.y, keyFly) - Math.sin(keyFly * Math.PI) * 220} r={60} n={6} color="#ffe08a" /> : null}
              </>
            ) : (
              <Keys x={1450} y={740} s={120} rot={-10} />
            )}
          </WindowBar>
          {t > jumpAt + 0.6 ? <SpeedLines t={t} cx={x} cy={y - 100} opacity={easeIn(run)} /> : null}
        </>
      );
    },
  },
];

export const ACT1: ShotDef[] = [...intro, ...verse1, ...pre1];
