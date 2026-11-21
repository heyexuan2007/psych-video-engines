// 字幕：每 0.1 秒问一次页面 TEXTS(t)，把字幕条（id 以 c 或 h 开头）收集成 .srt
// 用法：node styles/<画风>/tools/subs.mjs styles/<画风> <输出名>
import { openDemo, closeServer } from '../../../render/page.mjs';
import fs from 'node:fs'; import path from 'node:path';
const dir = process.argv[2], name = process.argv[3] || 'subs';
const { browser, page } = await openDemo(dir, { w: 1920, h: 1080, q: '' });
const spans = await page.evaluate(() => {
  const seen = {};
  for (let t = 0; t <= window.DUR; t += 0.1) for (const b of window.TEXTS(t)) {
    if (!/^[ch]\d/.test(b.id)) continue;
    const s = seen[b.id] ??= { text: b.text, a: t, b: t }; s.b = Math.min(window.DUR, t + 0.1);
  }
  return Object.values(seen);
});
await browser.close(); closeServer();
spans.sort((x, y) => x.a - y.a);
const ts = s => { const ms = Math.round(s * 1000); return `${String(Math.floor(ms / 3600000)).padStart(2, '0')}:${String(Math.floor(ms / 60000) % 60).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
fs.writeFileSync(path.join(dir, name + '.srt'), spans.map((s, i) => `${i + 1}\n${ts(s.a)} --> ${ts(s.b)}\n${s.text}\n`).join('\n'), 'utf8');
console.log(spans.length, 'cues');
