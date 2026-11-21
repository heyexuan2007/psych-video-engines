import sys
from PIL import Image
out, fs = sys.argv[1], sys.argv[2:]
ims = [Image.open(f) for f in fs]
w, h = ims[0].size
cols = 3 if len(ims) > 4 else 2
rows = (len(ims) + cols - 1) // cols
s = Image.new("RGB", (w * cols, h * rows))
for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save(out, quality=85)
