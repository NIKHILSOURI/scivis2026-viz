#!/usr/bin/env python
# TASK 0 — polished scalar-field animation: Air Temperature + Compound Extremes
# Index evolving 1950 -> 2026. Output: renders/task0_animation.mp4
import numpy as np, vtk, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
from vtk.util.numpy_support import vtk_to_numpy

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
NF = 20
YEAR0, DYEAR = 1950, 4          # frames are every 4 years
SUB = 6                          # interpolated sub-frames between years (smoothness)
EXTENT = [-180, 180, -59.875, 89.875]

# --- load all frames ---
tas, cei = [], []
for i in range(NF):
    r = vtk.vtkXMLImageDataReader(); r.SetFileName(f"{B}/task0_climate/frames/task0_t{i:02d}.vti"); r.Update()
    o = r.GetOutput(); nx, ny, _ = o.GetDimensions()
    tas.append(vtk_to_numpy(o.GetPointData().GetArray("AirTemperature_C")).reshape(ny, nx))
    cei.append(vtk_to_numpy(o.GetPointData().GetArray("CompoundExtremesIndex")).reshape(ny, nx))
tas = np.array(tas); cei = np.array(cei)
land = (tas[0] != 0)                              # ocean was filled with 0
ocean = ~land

def interp(stack, f):
    """linear interpolation across the year axis at fractional index f."""
    i0 = int(np.floor(f)); i1 = min(i0 + 1, NF - 1); a = f - i0
    return (1 - a) * stack[i0] + a * stack[i1]

frames_f = np.linspace(0, NF - 1, (NF - 1) * SUB + 1)

# --- figure (dark, two panels) ---
plt.rcParams.update({"font.family": "DejaVu Sans"})
fig, (axT, axC) = plt.subplots(1, 2, figsize=(19, 6.2))
fig.patch.set_facecolor("#0d1017")
for ax in (axT, axC):
    ax.set_facecolor("#0d1017"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#333a47")

def masked(a):
    m = np.ma.masked_where(ocean, a); return m

imT = axT.imshow(masked(tas[0]), origin="lower", cmap="RdBu_r", extent=EXTENT,
                 vmin=-30, vmax=35, aspect="auto")
imC = axC.imshow(masked(cei[0]), origin="lower", cmap="inferno", extent=EXTENT,
                 vmin=0, vmax=0.9, aspect="auto")
# coastlines
for ax in (axT, axC):
    ax.contour(land.astype(float), levels=[0.5], colors="#0d1017", linewidths=0.7,
               extent=EXTENT, origin="lower")
axT.set_title("Air Temperature  (°C)", color="#e6edf7", fontsize=15, pad=8)
axC.set_title("Compound Extremes Index", color="#e6edf7", fontsize=15, pad=8)
cbT = fig.colorbar(imT, ax=axT, fraction=0.03, pad=0.01); cbT.ax.tick_params(colors="#aab2c0")
cbC = fig.colorbar(imC, ax=axC, fraction=0.03, pad=0.01); cbC.ax.tick_params(colors="#aab2c0")
year_txt = fig.text(0.5, 0.94, "", ha="center", color="#ffd166", fontsize=26, fontweight="bold")
fig.text(0.5, 0.02, "IEEE SciVis 2026 · Task 0 · CMIP6 climate (ACCESS-CM2)",
         ha="center", color="#66707f", fontsize=11)
fig.subplots_adjust(left=0.01, right=0.965, top=0.88, bottom=0.06, wspace=0.08)

def update(f):
    T = interp(tas, f); C = interp(cei, f)
    imT.set_data(masked(T)); imC.set_data(masked(C))
    yr = YEAR0 + DYEAR * f
    year_txt.set_text(f"{yr:.0f}")
    return imT, imC, year_txt

ani = animation.FuncAnimation(fig, update, frames=frames_f, blit=False)
out = f"{B}/renders/task0_animation.mp4"
ani.save(out, writer=animation.FFMpegWriter(fps=18, bitrate=6000), dpi=110)
print("saved", out, "-", len(frames_f), "frames")
