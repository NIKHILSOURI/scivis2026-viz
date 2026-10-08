"""Convert ParaView PNG renders to WebP and deploy to docs/renders/pdf_stills/."""
from PIL import Image
import os, pathlib

SRC  = pathlib.Path("D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New/renders/pdf_stills")
DEST = pathlib.Path("D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New/docs/renders/pdf_stills")
QUALITY = 82
MAX_SIZE = (1920, 1080)

TASKS = ["task0_frames", "task3_frames", "task1_3d", "task1_global", "task1_jet100"]

for task in TASKS:
    src_dir  = SRC  / task
    dest_dir = DEST / task
    dest_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(src_dir.glob("*.png"))
    print(f"{task}: converting {len(pngs)} PNGs -> WebP")
    for png in pngs:
        webp = dest_dir / (png.stem + ".webp")
        with Image.open(png) as img:
            if img.width > MAX_SIZE[0] or img.height > MAX_SIZE[1]:
                img.thumbnail(MAX_SIZE, Image.LANCZOS)
            img.save(webp, "WEBP", quality=QUALITY)
    print(f"  done -> {dest_dir}")

print("All tasks deployed.")
