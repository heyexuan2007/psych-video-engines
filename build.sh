#!/bin/sh
# 一键生成：阅读速度检查 → 导出音效事件 → 渲染画面 → 合成音效 → 封装 mp4 → 导出字幕 → 封面
# 用法：sh build.sh <画风目录名> [输出文件名]
#   例：sh build.sh stage-spotlight 全场都在看你吗
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
STYLE=${1:?用法：sh build.sh <画风目录名> [输出文件名]}
NAME=${2:-$STYLE}
DIR="$ROOT/styles/$STYLE"
PY=${PYTHON:-python}
[ -f "$DIR/index.html" ] || { echo "找不到 $DIR/index.html"; exit 1; }
cd "$ROOT"
mkdir -p "$DIR/out/cover"
node render/readcheck.mjs "$DIR" --step 0.05 --cjk-cps 6 --pad 0.5 | grep -E "BAD|never" || echo "readcheck ok"
node render/events.mjs "$DIR"
node render/video.mjs "$DIR" --fps 30 --workers 4 --out "$DIR/out/video.mp4"
"$PY" "$DIR/mix.py"
ffmpeg -v error -y -i "$DIR/out/video.mp4" -i "$DIR/out/sfx.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart "$DIR/out/$NAME.mp4"
node "$DIR/tools/subs.mjs" "$DIR" "out/$NAME"
node render/still.mjs "$DIR" 0 --q "cover=1&w=1440&h=1080" --size 1440x1080 --prefix c43_ --out "$DIR/out/cover"
node render/still.mjs "$DIR" 0 --q "cover=1&w=1080&h=1440" --size 1080x1440 --prefix c34_ --out "$DIR/out/cover"
echo "完成：$DIR/out/$NAME.mp4"
