# 心理学短视频画风引擎

用代码一帧一帧“画”出心理学科普短视频：不用剪辑软件，不用素材库。画面、角色、字幕、音效全部由程序生成，改一行台词就能重新出片。

仓库里是五套心理学短视频画风（每一套都做出过一集完整的抖音短视频，35–43 秒），外加两套音乐 MV 画风。

| 画风 | 效果 | 用在哪一集 |
|---|---|---|
| **舞台追光** `stage-spotlight` | ![](docs/images/stage-spotlight.jpg) | 聚光灯效应：全场都在看你吗 |
| **旧档案胶片** `archive-film` | ![](docs/images/archive-film.jpg) | 服从权威：你按到第几个 |
| **超市 POP 价签** `pop-price-tag` | ![](docs/images/pop-price-tag.jpg) | 锚定效应：你以为是自己判断的 |
| **神秘塔罗** `mystic-tarot` | ![](docs/images/mystic-tarot.jpg) | 巴纳姆效应：被说中不代表被看穿 |
| **拟手绘** `hand-drawn` | ![](docs/images/hand-drawn.jpg) | 第一印象：0.1 秒你就给他打了分 |

## 每套画风的做法

- **舞台追光**：每个镜头先画全彩的布景，再乘一张“光照图”。追光照到的地方有颜色，其余变成深蓝剪影，最后叠上光束里的雾和灰尘。
- **旧档案胶片**：整体去色成 1960 年代录像的棕黑色，只有电压表、红灯这类“红色发光层”保留颜色。再叠胶片颗粒、划痕、片门抖动和暗角。
- **超市 POP 价签**：荧光卡纸配马克笔。黑色粗描边，填色故意错位，数字是逐笔写出来的“泡泡字”。整个画面每秒轻微扭动 8 次，像手绘动画的“沸腾线”。
- **神秘塔罗**：在舞台追光的基础上做成占卜氛围，有星盘、原创塔罗牌、金线小人和烛光。
- **拟手绘**：米白纸面配铅笔线。线条每秒抖动 8 次，用蓝、红、黑三色，再加黄色荧光笔做强调。

## 音乐 MV 画风

另外两套是给歌曲做 MV 用的，放在 `mv-styles/` 里。

| 画风 | 效果 | |
|---|---|---|
| **三笔刷手绘** `hongdou-brush`（Python） | ![](docs/images/mv-hongdou-1.jpg) | ![](docs/images/mv-hongdou-2.jpg) |
| **团子故事版** `tiantian-story`（Remotion / React） | ![](docs/images/mv-tiantian-1.jpg) | ![](docs/images/mv-tiantian-2.jpg) |

- **三笔刷手绘**：水彩晕染、水墨、油画棒三支“笔刷”画同一套场景。歌曲进行中用遮罩转场切换笔刷（例如水彩从碗里的红豆晕开），歌词的样式也跟着画风变。画面按“一拍二”的节奏更新，像手绘动画。
- **团子故事版**：每句歌词对应一个小动作、小物件，讲一个人一天的故事。角色有 12 种表情，画面会跟着歌曲的能量起伏和节拍闪动。

> 这两套 MV 原本是为真实歌曲做的。仓库里**不含任何歌曲音频和原歌词**，歌词已经换成同样字数、同样时间点的示例句子。想做自己的 MV，就换上自己的歌曲和逐字 LRC 歌词（说明见 `mv-styles/tiantian-story/public/README.md`）。
> 三笔刷手绘的字幕用了 Windows 自带的华文行楷、华文楷体，在其他系统上需要改 `core.py` 里的字体路径。

```bash
# 三笔刷手绘：单帧 / 整片
cd mv-styles/hongdou-brush
python mv.py frame 20 out/frame.png
python mv.py render

# 团子故事版
cd mv-styles/tiantian-story
npm ci
npx remotion studio
```

## 设计思路

- **每一帧都能单独算**：`render(t)` 只依赖时间 `t`，所以可以多进程并行渲染，也能直接跳到任意一秒检查画面。
- **场景和引擎分开**：`engine.js` 是画风本身（画笔、光照、滤镜），`scenes/` 里是这一集的剧情。换一集只需要重写 `scenes/film.js`。
- **音效跟着画面走**：页面在关键动作处登记事件（`window.EV`），`mix.py` 按这些时间点用程序合成音效，不用任何音频素材。
- **自动检查字幕读速**：`render/readcheck.mjs` 会检查每句字幕停留的时间够不够读完（中文按每秒 6 个字算）。

## 目录结构

```
render/              渲染工具（无头浏览器逐帧截图 → ffmpeg 编码）
styles/<画风>/
  index.html         页面入口，1920×1080 canvas
  engine.js          画风引擎
  scenes/            角色、道具、剧情（film.js）、封面
  mix.py             按事件合成音效
  tools/             音效库、字幕导出等
mv-styles/
  hongdou-brush/     三笔刷手绘 MV（Python + OpenCV）
  tiantian-story/    团子故事版 MV（Remotion）
build.sh             一键出片
```

## 怎么运行

需要 Node.js 20+、Python 3.10+ 和 ffmpeg。

```bash
npm install
npm run setup
pip install -r requirements.txt
sh build.sh stage-spotlight 全场都在看你吗
```

成片、字幕和封面会输出到 `styles/<画风>/out/`。

只想看某一帧，可以单独截图：

```bash
node render/still.mjs styles/hand-drawn 6 --out styles/hand-drawn/out/stills
```

> “神秘塔罗”用到两款开源字体，需要自己下载，见 `styles/mystic-tarot/fonts/README.md`。

## 致谢

`render/` 中的逐帧渲染工具来自 [lemo-opuscar](render/LICENSE-lemo-opuscar)（MIT）。所有画风引擎、角色和剧情都是本仓库原创。

## 许可证

MIT
