#!/usr/bin/env python
"""
density_atlas.py
Builds geographic density heatmaps from the PD-Wasserstein tracking nodes:
  1. Hot-spot atlas: spatial accumulation of ALL CEI maxima 1950-2025
  2. Event density: creation / destruction positions (where features born/die)
  3. Decade-split: 1950s vs 2010s hot-spot shift (shows geographic trend)

Run: python scripts/density_atlas.py
Outputs: renders/density_atlas.png
         renders/density_decades.png
"""
import os, sys, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.ndimage import gaussian_filter

B       = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
NODES   = f"{B}/outputs/task0_pd_nodes.vtp"
OUTDIR  = f"{B}/renders"
os.makedirs(OUTDIR, exist_ok=True)

# ── Read nodes VTP ────────────────────────────────────────────────────────────
r = vtk.vtkXMLPolyDataReader()
r.SetFileName(NODES); r.Update()
obj = r.GetOutput()
if obj.GetNumberOfPoints() == 0:
    print(f"ERROR: {NODES} is empty or not found."); sys.exit(1)

pts   = vtk_to_numpy(obj.GetPoints().GetData())   # (N,3)
pd    = obj.GetPointData()
event = vtk_to_numpy(pd.GetArray("EventType"))
ts    = vtk_to_numpy(pd.GetArray("TimeStep"))

x, y = pts[:, 0], pts[:, 1]
print(f"Loaded {len(x)} nodes from {NODES}")
print(f"  lon range: [{x.min():.1f}, {x.max():.1f}]")
print(f"  lat range: [{y.min():.1f}, {y.max():.1f}]")

# ── Grid parameters matching ACCESS-CM2 grid ─────────────────────────────────
LON_MIN, LON_MAX = -180, 180
LAT_MIN, LAT_MAX =  -90,  90
GRID_W, GRID_H   =  360, 180
SIGMA             = 3.5   # Gaussian blur radius (degrees)

def to_grid(xv, yv):
    xi = ((xv - LON_MIN) / (LON_MAX - LON_MIN) * GRID_W).astype(int).clip(0, GRID_W-1)
    yi = ((yv - LAT_MIN) / (LAT_MAX - LAT_MIN) * GRID_H).astype(int).clip(0, GRID_H-1)
    g  = np.zeros((GRID_H, GRID_W), dtype=float)
    np.add.at(g, (yi, xi), 1)
    return gaussian_filter(g, sigma=SIGMA)

# ── ① Full-period hot-spot atlas ──────────────────────────────────────────────
g_all  = to_grid(x, y)
g_cre  = to_grid(x[event == 1], y[event == 1])
g_des  = to_grid(x[event == 2], y[event == 2])
g_spl  = to_grid(x[event == 3], y[event == 3])
g_mrg  = to_grid(x[event == 4], y[event == 4])

dark_bg   = "#0d0f14"
event_names  = ["Creation", "Destruction", "Split", "Merge"]
event_grids  = [g_cre, g_des, g_spl, g_mrg]
event_cmaps  = ["GnBu", "OrRd", "YlOrBr", "Purples"]

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor(dark_bg)
axes = axes.flatten()

def plot_density(ax, grid, title, cmap, subtitle=""):
    ax.set_facecolor(dark_bg)
    ext = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
    im  = ax.imshow(grid, origin="lower", extent=ext,
                    cmap=cmap, interpolation="bilinear", aspect="auto")
    cb  = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.ax.yaxis.set_tick_params(color="#888"); cb.outline.set_edgecolor("#888")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#888")
    ax.set_title(title, color="#eee", fontsize=10)
    if subtitle:
        ax.set_xlabel(subtitle, color="#888", fontsize=8)
    ax.tick_params(colors="#888")
    ax.axhline(0,  color="#555", lw=0.5, ls=":")
    ax.axvline(0,  color="#555", lw=0.5, ls=":")
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
    for sp in ax.spines.values(): sp.set_edgecolor("#555")

plot_density(axes[0], g_all, "CEI Extrema Density 1950-2025 (all events)", "hot")
for i, (name, grid, cm) in enumerate(zip(event_names, event_grids, event_cmaps)):
    plot_density(axes[i+1], grid, f"Event Density: {name}", cm)
axes[5].set_visible(False)

plt.suptitle("Geographic Density Atlas of CEI Compound Extremes (ACCESS-CM2, 1950-2025)",
             color="#eee", fontsize=12)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/density_atlas.png", dpi=150,
            bbox_inches="tight", facecolor=dark_bg)
print(f"Saved {OUTDIR}/density_atlas.png")

# ── ② Decade shift: 1950-1979 vs 2000-2025 ───────────────────────────────────
early = ts < 30         # years 0-29 = 1950-1979
late  = ts >= 50        # years 50-75 = 2000-2025
g_early = to_grid(x[early], y[early])
g_late  = to_grid(x[late],  y[late])
g_diff  = g_late - g_early
norm_late  = g_late  / (g_late.max()  + 1e-9)
norm_early = g_early / (g_early.max() + 1e-9)
g_norm_diff = norm_late - norm_early

fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))
fig2.patch.set_facecolor(dark_bg)
plot_density(axes2[0], g_early, "CEI Extrema 1950-1979", "Blues_r", "Early period")
plot_density(axes2[1], g_late,  "CEI Extrema 2000-2025", "Reds",    "Recent period")

axes2[2].set_facecolor(dark_bg)
ext = [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX]
vmax = max(abs(g_norm_diff.min()), abs(g_norm_diff.max()))
im = axes2[2].imshow(g_norm_diff, origin="lower", extent=ext,
                     cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                     interpolation="bilinear", aspect="auto")
cb = fig2.colorbar(im, ax=axes2[2], fraction=0.025, pad=0.02)
cb.ax.yaxis.set_tick_params(color="#888"); cb.outline.set_edgecolor("#888")
plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#888")
axes2[2].set_title("Geographic Shift (Recent - Early)\nRed = more extreme events; Blue = fewer",
                   color="#eee", fontsize=9)
axes2[2].axhline(0, color="#555", lw=0.5, ls=":")
axes2[2].axvline(0, color="#555", lw=0.5, ls=":")
axes2[2].tick_params(colors="#888")
for sp in axes2[2].spines.values(): sp.set_edgecolor("#555")

plt.suptitle("Decade Shift in CEI Extreme Hot-Spots (ACCESS-CM2 CMIP6)",
             color="#eee", fontsize=12)
plt.tight_layout()
fig2.savefig(f"{OUTDIR}/density_decades.png", dpi=150,
             bbox_inches="tight", facecolor=dark_bg)
print(f"Saved {OUTDIR}/density_decades.png")

# ── Print top hot-spot regions ────────────────────────────────────────────────
print("\n--- TOP HOT-SPOT REGIONS (full period) ---")
flat_idx = g_all.flatten().argsort()[-10:][::-1]
for idx in flat_idx:
    ri, ci = divmod(idx, GRID_W)
    lon = LON_MIN + (ci / GRID_W) * (LON_MAX - LON_MIN)
    lat = LAT_MIN + (ri / GRID_H) * (LAT_MAX - LAT_MIN)
    print(f"  lon={lon:+.0f}  lat={lat:+.0f}  density={g_all.flat[idx]:.3f}")
