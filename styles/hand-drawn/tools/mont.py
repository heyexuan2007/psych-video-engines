# 把 stills 里的 t_*.jpg 拼成预览图：python mont.py <stills目录> [每张几格]
import sys, glob, os
from PIL import Image, ImageDraw
d = sys.argv[1]; per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
fs = sorted(glob.glob(os.path.join(d, 't_*.jpg')), key=lambda f: float(os.path.basename(f)[2:-4]))
def mont(files, out, cols=3, w=640):
    h = int(w * 9 / 16); rows = (len(files) + cols - 1) // cols
    M = Image.new('RGB', (cols * w, rows * (h + 24)), (30, 30, 30)); dr = ImageDraw.Draw(M)
    for i, f in enumerate(files):
        im = Image.open(f).resize((w, h)); x = (i % cols) * w; y = (i // cols) * (h + 24)
        M.paste(im, (x, y + 24)); dr.text((x + 6, y + 4), os.path.basename(f), fill=(255, 255, 0))
    M.save(out, quality=88)
for k in range(0, len(fs), per): mont(fs[k:k + per], os.path.join(d, f'm{k // per + 1}.jpg'))
print(len(fs))
