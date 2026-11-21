// Render check frames: node tools/stills.mjs out/chk 1 3 10 ...  (args are song seconds)
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const [outDir, ...secs] = process.argv.slice(2);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const comp = await selectComposition({ serveUrl, id: process.env.COMP || "TianTianStory" });
for (const s of secs) {
  const frame = Math.round(Number(s) * comp.fps);
  await renderStill({ composition: comp, serveUrl, frame, output: path.join(outDir, `t${s}.jpg`), imageFormat: "jpeg", jpegQuality: 80, scale: 0.5 });
  console.log("still", s);
}
