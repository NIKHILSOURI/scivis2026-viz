#!/usr/bin/env python
"""
compose_final_video.py — assemble the submission video with ffmpeg.

Layout: main map animation (left, 2/3 width) + persistence diagram evolution
(right, 1/3 width), both playing 1950-2025 in sync at 6 fps.

Prerequisites (export from ParaView first, 6 fps):
  renders/cross_task_hero.mp4   <- from viz_cross_task.py scene   (the headline)
  renders/task0_main.mp4        <- from viz_task0.py scene        (optional 2nd video)
pd_evolution.mp4 is already built by animate_pd.py.

Run: python scripts/compose_final_video.py
Output: renders/FINAL_submission.mp4
"""
import os, shutil, subprocess, sys

B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
R  = f"{B}/renders"

MAIN = f"{R}/cross_task_hero.mp4"     # export from ParaView with this exact name
PD   = f"{R}/pd_evolution.mp4"
OUT  = f"{R}/FINAL_submission.mp4"

ff = shutil.which("ffmpeg")
if not ff:
    sys.exit("ffmpeg not found on PATH")
if not os.path.exists(MAIN):
    sys.exit(f"Missing {MAIN}\nExport it from ParaView: File > Save Animation > "
             f"MP4, 6 fps, filename cross_task_hero.mp4 in the renders folder.")
if not os.path.exists(PD):
    sys.exit(f"Missing {PD} — run animate_pd.py first")

# Scale both to common height (1080), main gets ~2/3 width, PD panel the rest.
# fps=6 on both inputs keeps the 76 frames aligned year-for-year.
filt = (
    "[0:v]fps=6,scale=-2:1080[left];"
    "[1:v]fps=6,scale=-2:1080[right];"
    "[left][right]hstack=inputs=2,pad=ceil(iw/2)*2:ceil(ih/2)*2[v]"
)
cmd = [ff, "-y",
       "-i", MAIN, "-i", PD,
       "-filter_complex", filt, "-map", "[v]",
       "-c:v", "libx264", "-crf", "18", "-preset", "slow",
       "-pix_fmt", "yuv420p", OUT]
print("Running ffmpeg ...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print(res.stderr[-3000:]); sys.exit(1)
sz = os.path.getsize(OUT) / 1e6
print(f"Done: {OUT}  ({sz:.1f} MB)")
print("Left: map animation | Right: persistence diagram, same year in both panels.")
