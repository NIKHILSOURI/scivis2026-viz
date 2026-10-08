"""Convert task0_frames and task3_frames PNGs to WebP and copy to docs/renders."""
from PIL import Image
import os, re

B = r"D:\STUDY\RESEARCH WORKS\IIIT HYD\sciviscontest2026\##ParaView_New"
SRC  = os.path.join(B, "renders", "pdf_stills")
DOCS = os.path.join(B, "docs", "renders", "pdf_stills")
MAX_W, MAX_H, QUALITY = 1920, 1080, 82
PAT = re.compile(r'^frame_(\d+)_t(\d+)\.png$')

for task in ("task0_frames", "task3_frames"):
    src_dir  = os.path.join(SRC,  task)
    docs_dir = os.path.join(DOCS, task)
    os.makedirs(docs_dir, exist_ok=True)
    frames = sorted(f for f in os.listdir(src_dir) if PAT.match(f))
    print(f"\n{task}: {len(frames)} frames")
    for f in os.listdir(docs_dir):
        if f.endswith('.webp'):
            os.remove(os.path.join(docs_dir, f))
    for fname in frames:
        src = os.path.join(src_dir, fname)
        dst = os.path.join(docs_dir, fname.replace('.png', '.webp'))
        img = Image.open(src)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        if img.width > MAX_W or img.height > MAX_H:
            img.thumbnail((MAX_W, MAX_H), Image.LANCZOS)
        img.save(dst, "WEBP", quality=QUALITY, method=6)
    if frames:
        sizes = [os.path.getsize(os.path.join(docs_dir, f.replace('.png','.webp'))) for f in frames]
        print(f"  avg {sum(sizes)//len(sizes)//1024} KB  total {sum(sizes)//1024//1024} MB")
print("\nDone.")
