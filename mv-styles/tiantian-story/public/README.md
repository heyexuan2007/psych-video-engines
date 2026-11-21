# 素材

仓库里没有附带歌曲和字体，请自己放到这个文件夹：

- `song.mp3`：你要做 MV 的歌曲音频（没有它也能渲染画面，只是没有声音）
- `sans.ttf`：Noto Sans SC，<https://github.com/google/fonts/tree/main/ofl/notosanssc>
- `serif.ttf`：Noto Serif SC，<https://github.com/google/fonts/tree/main/ofl/notoserifsc>

换歌时，用 `prep.py` 从你的逐字 LRC 和音频重新生成 `src/data/lyrics.json` 和 `src/data/audio.json`：

```bash
python prep.py 你的歌词.lrc public/song.mp3 src/data
```
