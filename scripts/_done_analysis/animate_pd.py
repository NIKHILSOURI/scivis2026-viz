#!/usr/bin/env python
"""
animate_pd.py — animated persistence diagram, 1950-2025.

For each year, plots the (Birth, Death) scatter of finite saddle-max pairs from
the pre-computed persistence diagrams. Points far from the diagonal = strong,
long-lived compound extremes. Watching the cloud drift up-right over 76 years
= the climate signal expressed in pure topology.

Writes 76 PNG frames, then assembles pd_evolution.mp4 if ffmpeg is available
(otherwise prints the ffmpeg command to run manually).

Run: python scripts/animate_pd.py
Outputs:
  renders/pd_frames/pd_evo_tXX.png  (76 frames, 1280x720)
  renders/pd_evolution.mp4          (if ffmpeg found)
"""
import os, subprocess, shutil, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
PD_DIR = f"{B}/task0_climate/persistence_diagrams"
FRAMES = f"{B}/renders/videos/_pd_frames"
os.makedirs(FRAMES, exist_ok=True)

dark = "#0d0f14"

# ── Load all diagrams first (fixed axes need global ranges) ───────────────────
diagrams = []
for idx in range(76):
    fp = f"{PD_DIR}/pd_t{idx:02d}.vtp"
    r = vtk.vtkXMLUnstructuredGridReader(); r.SetFileName(fp); r.Update()
    obj = r.GetOutput()
    if obj.GetNumberOfCells() == 0:
        diagrams.append(None); continue
    cd = obj.GetCellData()
    pt  = vtk_to_numpy(cd.GetArray("PairType"))
    per = vtk_to_numpy(cd.GetArray("Persistence"))
    bi  = vtk_to_numpy(cd.GetArray("Birth"))
    fin = vtk_to_numpy(cd.GetArray("IsFinite"))
    m = (pt == 1) & (fin == 1) & (per > 0.02)
    diagrams.append((bi[m], bi[m] + per[m], per[m]))

# t62 (2012) PD is empty from the corrupt source frame: reuse t61 so the
# animation doesn't blank for one year (matches the interpolated VTI fix).
if diagrams[62] is None:
    diagrams[62] = diagrams[61]
    print("t62 (2012): reusing 2011 diagram (source frame was corrupt)")

# ── Render frames ─────────────────────────────────────────────────────────────
BMIN, BMAX = 0.0, 0.75
DMIN, DMAX = 0.0, 1.05

for idx, dg in enumerate(diagrams):
    year = 1950 + idx
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100, facecolor=dark)
    ax.set_facecolor(dark)
    for sp in ax.spines.values(): sp.set_edgecolor("#555")
    ax.tick_params(colors="#999", labelsize=11)

    # diagonal + persistence guide bands
    ax.plot([0, 1.1], [0, 1.1], color="#666", lw=1.2)
    for g in (0.1, 0.2, 0.3):
        ax.plot([0, 1.1], [g, 1.1 + g], color="#333", lw=0.7, ls=":")
        ax.text(0.72, 0.735 + g, f"persistence {g:.1f}", color="#555",
                fontsize=8, rotation=38)

    if dg is not None:
        b, d, p = dg
        order = np.argsort(p)                       # strong points on top
        sc = ax.scatter(b[order], d[order], c=p[order], cmap="inferno",
                        vmin=0.02, vmax=0.45, s=14 + 220 * p[order],
                        alpha=0.85, edgecolors="none", zorder=3)
        cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
        cb.set_label("Persistence", color="#999")
        cb.ax.yaxis.set_tick_params(color="#777", labelsize=9)
        cb.outline.set_edgecolor("#555")
        plt.setp(cb.ax.axes.get_yticklabels(), color="#999")
        n_sig = int((p > 0.08).sum())
        ax.text(0.03, 0.97, f"{n_sig} significant features",
                transform=ax.transAxes, color="#ccc", fontsize=12, va="top")

    ax.set_xlim(BMIN, BMAX); ax.set_ylim(DMIN, DMAX)
    ax.set_xlabel("Birth (CEI value where feature appears)", color="#aaa", fontsize=12)
    ax.set_ylabel("Death (CEI value where feature merges)", color="#aaa", fontsize=12)
    ax.set_title(f"Persistence Diagram of Compound Extremes Index — {year}",
                 color="#eee", fontsize=15)
    ax.text(0.98, 0.03, "far from diagonal = strong, long-lived extreme",
            transform=ax.transAxes, color="#777", fontsize=10, ha="right")

    fig.savefig(f"{FRAMES}/pd_evo_t{idx:02d}.png",
                facecolor=dark, bbox_inches="tight")
    plt.close(fig)
    if idx % 10 == 0:
        print(f"  frame {idx:02d} ({year}) done")

print(f"76 frames in {FRAMES}")

# ── Assemble MP4 if ffmpeg available ──────────────────────────────────────────
ff = shutil.which("ffmpeg")
out_mp4 = f"{B}/renders/videos/pd_evolution.mp4"
cmd = [ff or "ffmpeg", "-y", "-framerate", "6",
       "-i", f"{FRAMES}/pd_evo_t%02d.png",
       "-c:v", "libx264", "-pix_fmt", "yuv420p",
       "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", out_mp4]
if ff:
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Video: {out_mp4}")
else:
    print("ffmpeg not found. Assemble manually with:")
    print("  " + " ".join(cmd))
