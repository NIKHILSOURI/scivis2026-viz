#!/usr/bin/env python
"""
build_tracking_graph.py  (v2 - "The Pulse of Compound Extremes")

v1 (70 barcode lanes) was unreadable: every long-lived track spans the whole
record, so lanes were identical yellow stripes. v2 aggregates to the readable
signal: ONE intensity curve per region = the mean topological persistence of
that region's tracked extremes, per year, smoothed. Stacked ridgeline.

What it shows: each region's compound-extreme "engine" pulsing over 76 years -
peaks = years the region's extremes were strongest. Peak year annotated.

Reads:  outputs/task0_pd_trajectories.vtp
Writes: renders/tracking_graph.png
Run:    python scripts/_done_analysis/build_tracking_graph.py
"""
import os, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"

REGIONS = [
    ("Europe",             -12,  45,  36,  66),
    ("Middle East",         35,  62,  12,  40),
    ("South Asia",          62,  92,   5,  36),
    ("East Asia",           92, 148,  20,  55),
    ("SE Asia",             92, 141, -10,  20),
    ("Australia",          112, 155, -45, -10),
    ("North America",     -168, -52,  15,  66),
    ("Central America",   -118, -60,   5,  25),
    ("South America",      -82, -34, -56,   5),
    ("North Africa",       -18,  35,  12,  36),
    ("Sub-Saharan Africa", -18,  52, -35,  12),
]
def region_of(lon, lat):
    for name, x0, x1, y0, y1 in REGIONS:
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            return name
    return None                      # oceans excluded: land story only

# -- Load tracking -------------------------------------------------------------
r = vtk.vtkXMLPolyDataReader()
r.SetFileName(f"{B}/outputs/task0_pd_trajectories.vtp"); r.Update()
obj = r.GetOutput()
pts = vtk_to_numpy(obj.GetPoints().GetData())
pd  = obj.GetPointData()
tid = vtk_to_numpy(pd.GetArray("TrajectoryID"))
ts  = vtk_to_numpy(pd.GetArray("TimeStep"))
per = vtk_to_numpy(pd.GetArray("Persistence"))

tracks = defaultdict(list)
for i in range(len(tid)):
    tracks[int(tid[i])].append(i)

# region -> year -> list of persistences (from tracks anchored in that region)
acc = {name: defaultdict(list) for name, *_ in REGIONS}
n_tracks = {name: 0 for name, *_ in REGIONS}
for t_id, idxs in tracks.items():
    idxs = sorted(idxs, key=lambda i: int(ts[i]))
    life = int(ts[idxs[-1]]) - int(ts[idxs[0]]) + 1
    if life < 20:
        continue
    P = pts[idxs]
    reg = region_of(float(P[:, 0].mean()), float(P[:, 1].mean()))
    if reg is None:
        continue
    n_tracks[reg] += 1
    for i in idxs:
        acc[reg][int(ts[i])].append(float(per[i]))

years = np.arange(1950, 2026)
series = {}
for name in acc:
    v = np.array([np.mean(acc[name][t]) if acc[name][t] else np.nan
                  for t in range(76)])
    if np.isfinite(v).sum() > 40:
        # 5-yr smoothing, NaN-tolerant
        k = np.ones(5)
        num = np.convolve(np.nan_to_num(v), k, "same")
        den = np.convolve(np.isfinite(v).astype(float), k, "same")
        series[name] = num / np.maximum(den, 1)
print("Regions with enough coverage:",
      ", ".join(f"{n}({n_tracks[n]})" for n in series))

# -- Ridgeline figure ----------------------------------------------------------
dark = "#0d0f14"
order = sorted(series, key=lambda n: -np.nanmean(series[n]))   # strongest on top
n = len(order)
fig, ax = plt.subplots(figsize=(15, 1.05 * n + 2), facecolor=dark)
ax.set_facecolor(dark)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(colors="#999")

palette = plt.cm.plasma(np.linspace(0.25, 0.9, n))
GAP, AMP = 1.0, 2.6      # lane spacing and curve amplitude

for k, name in enumerate(order):
    v = series[name]
    base = (n - 1 - k) * GAP
    vmin, vmax = np.nanmin(v), np.nanmax(v)
    vn = (v - vmin) / max(vmax - vmin, 1e-9)          # per-region normalised
    y = base + vn * AMP

    ax.fill_between(years, base, y, color=palette[k], alpha=0.55, zorder=2+k)
    ax.plot(years, y, color="white", lw=1.4, alpha=0.95, zorder=3+k)

    # region label + absolute mean
    ax.text(1947.5, base + 0.12, name, ha="right", va="bottom",
            color="#dde", fontsize=11, weight="bold")
    ax.text(2027.5, base + 0.12, f"mean {np.nanmean(v):.2f}",
            ha="left", va="bottom", color="#889", fontsize=9)

    # annotate the record year
    pk = int(np.nanargmax(v))
    ax.plot(years[pk], y[pk], "o", ms=6, color="white", zorder=5+k)
    ax.annotate(f"{1950+pk}", (years[pk], y[pk]),
                textcoords="offset points", xytext=(0, 7),
                color="#ffdd88", fontsize=9, ha="center", zorder=6+k)

for yr in (1960, 1980, 2000, 2020):
    ax.axvline(yr, color="#333", lw=0.7, zorder=1)

ax.set_xlim(1938, 2036)
ax.set_ylim(-0.6, n * GAP + AMP)
ax.set_yticks([])
ax.set_xticks([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020])
ax.set_xlabel("Year", color="#aaa", fontsize=12)
ax.set_title(
    "The Pulse of Compound Extremes, 1950-2025\n"
    "Per-region intensity of topologically tracked CEI extremes "
    "(mean persistence, 5-yr smoothed; dot = record year)",
    color="#eee", fontsize=14, pad=18)

plt.tight_layout()
fig.savefig(f"{B}/renders/figures/tracking_graph.png", dpi=170,
            bbox_inches="tight", facecolor=dark)
print(f"Figure: {B}/renders/tracking_graph.png")
for name in order:
    v = series[name]
    print(f"  {name:<20} record year {1950 + int(np.nanargmax(v))}   "
          f"mean {np.nanmean(v):.3f}")
