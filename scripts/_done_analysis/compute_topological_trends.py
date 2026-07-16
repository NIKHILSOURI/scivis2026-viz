#!/usr/bin/env python
"""
compute_topological_trends.py
Reads all 76 pre-computed persistence diagrams and extracts per-year statistics:
  - Number of significant CEI extrema (saddle-max pairs with persistence > threshold)
  - Average persistence per year
  - Maximum persistence per year
  - Betti-0 number (connected components of high-CEI regions, approximated)

If there is a rising trend post-1980, that is the climate change signal visible
through topology -- the key scientific result for the paper.

Run: python scripts/compute_topological_trends.py
Outputs: renders/topological_trends.png   (paper figure)
         outputs/topological_trends.csv   (raw numbers)
"""
import os, sys, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.stats import linregress

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
PD_DIR = f"{B}/task0_climate/persistence_diagrams"
OUTDIR = f"{B}/renders/figures"
CSVOUT = f"{B}/outputs"
os.makedirs(OUTDIR, exist_ok=True); os.makedirs(CSVOUT, exist_ok=True)

THRESHOLDS = [0.04, 0.08, 0.12]   # test multiple significance levels

results = {thr: dict(years=[], n=[], avg=[], mx=[]) for thr in THRESHOLDS}

for idx in range(76):
    year = 1950 + idx
    fpath = f"{PD_DIR}/pd_t{idx:02d}.vtp"
    if not os.path.exists(fpath):
        print(f"  MISSING: {fpath}"); continue

    r = vtk.vtkXMLUnstructuredGridReader()
    r.SetFileName(fpath); r.Update()
    obj = r.GetOutput()
    if obj.GetNumberOfCells() == 0:
        print(f"  t{idx:02d} {year}: empty (bad data year)")
        for thr in THRESHOLDS:
            results[thr]["years"].append(year)
            results[thr]["n"].append(0)
            results[thr]["avg"].append(np.nan)
            results[thr]["mx"].append(np.nan)
        continue

    cdd      = obj.GetCellData()
    ptype    = vtk_to_numpy(cdd.GetArray("PairType"))
    persist  = vtk_to_numpy(cdd.GetArray("Persistence"))
    finite   = vtk_to_numpy(cdd.GetArray("IsFinite"))

    for thr in THRESHOLDS:
        mask = (ptype == 1) & (finite == 1) & (persist > thr)
        p    = persist[mask]
        results[thr]["years"].append(year)
        results[thr]["n"].append(int(mask.sum()))
        results[thr]["avg"].append(float(p.mean()) if len(p) > 0 else np.nan)
        results[thr]["mx"].append(float(p.max())  if len(p) > 0 else np.nan)

    print(f"  t{idx:02d} {year}: "
          + "  ".join(f"p>{t:.2f}: {results[t]['n'][-1]}" for t in THRESHOLDS))

# -- Save CSV ------------------------------------------------------------------
thr = THRESHOLDS[1]   # 0.08 as the primary threshold
D = results[thr]
with open(f"{CSVOUT}/topological_trends.csv", "w") as f:
    f.write("year,n_features,avg_persistence,max_persistence\n")
    for i in range(len(D["years"])):
        f.write(f"{D['years'][i]},{D['n'][i]},{D['avg'][i]:.6f},{D['mx'][i]:.6f}\n")
print(f"\nCSV saved: {CSVOUT}/topological_trends.csv")

# -- Plot ----------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.patch.set_facecolor("#0d0f14")
for ax in axes:
    ax.set_facecolor("#0d0f14")
    ax.spines["bottom"].set_color("#555"); ax.spines["top"].set_color("#555")
    ax.spines["left"].set_color("#555");  ax.spines["right"].set_color("#555")
    ax.tick_params(colors="#aaa"); ax.yaxis.label.set_color("#ccc")
    ax.xaxis.label.set_color("#ccc"); ax.title.set_color("#eee")

colors = ["#44aaff", "#ffaa22", "#ff4488"]
titles = ["Number of significant CEI extrema",
          "Average persistence of CEI extrema",
          "Maximum persistence (strongest event)"]
keys   = ["n", "avg", "mx"]
ylabels= ["Count (features)", "Persistence (CEI units)", "Persistence (CEI units)"]

for ax, key, title, ylabel, c in zip(axes, keys, titles, ylabels, colors):
    yrs = np.array(results[THRESHOLDS[1]]["years"])
    vals = np.array(results[THRESHOLDS[1]][key], dtype=float)
    valid = ~np.isnan(vals)

    ax.plot(yrs[valid], vals[valid], color=c, lw=1.5, alpha=0.8, label="Annual")

    # 5-year rolling mean
    from numpy.lib.stride_tricks import sliding_window_view
    if valid.sum() > 5:
        yv, vv = yrs[valid], vals[valid]
        roll = np.convolve(vv, np.ones(5)/5, mode="valid")
        ax.plot(yv[2:-2], roll, color="white", lw=2.5, alpha=0.9, label="5-yr mean")

    # linear trend (post-1980)
    post80 = valid & (yrs >= 1980)
    if post80.sum() > 5:
        slope, intercept, r, p, _ = linregress(yrs[post80], vals[post80])
        x_fit = np.array([1980, 2025])
        ax.plot(x_fit, slope*x_fit + intercept, "--",
                color="#ff6666", lw=1.8, alpha=0.85,
                label=f"Trend 1980-2025 (r={r:.2f}, p={p:.3f})")
        # annotate the slope direction
        direction = "INCREASING" if slope > 0 else "DECREASING"
        significance = "SIGNIFICANT" if p < 0.05 else "not significant"
        ax.set_title(f"{title}\n{direction} trend ({significance})", fontsize=9)
    else:
        ax.set_title(title, fontsize=9)

    ax.axvline(1980, color="#888", lw=0.8, ls=":", alpha=0.6)
    ax.axvline(1990, color="#888", lw=0.8, ls=":", alpha=0.6)
    ax.set_xlabel("Year"); ax.set_ylabel(ylabel)
    ax.legend(fontsize=7, facecolor="#1a1c22", labelcolor="#ccc")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10))

plt.suptitle(
    f"Topological Analysis of Compound Climate Extremes (1950-2025)\n"
    f"Persistence threshold: {THRESHOLDS[1]:.2f} | Data: ACCESS-CM2 CMIP6",
    color="#eee", fontsize=11, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/topological_trends.png", dpi=180,
            bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Figure saved: {OUTDIR}/topological_trends.png")

# -- Print summary for paper ----------------------------------------------------
yrs  = np.array(results[THRESHOLDS[1]]["years"])
vals = np.array(results[THRESHOLDS[1]]["n"], dtype=float)
valid = ~np.isnan(vals)
early = valid & (yrs < 1980)
late  = valid & (yrs >= 2000)
print(f"\n--- KEY NUMBERS FOR PAPER ---")
print(f"Mean features 1950-1979: {vals[early].mean():.1f}")
print(f"Mean features 2000-2025: {vals[late].mean():.1f}")
print(f"Change: {(vals[late].mean()-vals[early].mean())/vals[early].mean()*100:.1f}%")
