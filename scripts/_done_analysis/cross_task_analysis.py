#!/usr/bin/env python
"""
cross_task_analysis.py  (CORRECTED - honest timescale)

TIMESCALE NOTE: Task 0 (ACCESS-CM2) genuinely spans 1950-2025. Task 1 (GEOS
DYAMOND) is a short weather-scale period - the two CANNOT be correlated in
time, and no jet trend can be claimed from GEOS. This corrected version:

  Panel A: jet waviness across GEOS snapshots (weather-scale variability)
  Panel B: CEI topological persistence 1950-2025 (valid climate trend axis)
  Panel C: NH waviness distribution (the envelope the jet explores)

The Arctic-amplification LINK is cited from literature (Francis & Vavrus
2012, GRL) and illustrated by the combined visualization - it is NOT claimed
as a measured result of this work.

Outputs: renders/cross_task_main.png, renders/cross_task_jetprofile.png,
         outputs/cross_task_stats.txt
"""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import linregress

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
OUTDIR = f"{B}/renders/figures"; CSVOUT = f"{B}/outputs"

# -- Load ----------------------------------------------------------------------
wav = np.genfromtxt(f"{CSVOUT}/waviness.csv", delimiter=",", skip_header=1)
snap  = wav[:, 0]; w_NH = wav[:, 1]

t0 = np.genfromtxt(f"{CSVOUT}/topological_trends.csv", delimiter=",", skip_header=1)
t0_years, t0_avg = t0[:, 0], t0[:, 2]
okc = np.isfinite(t0_avg)
slp_c, int_c, r_c, p_c, _ = linregress(t0_years[okc], t0_avg[okc])

# -- Stats file (valid claims only) --------------------------------------------
with open(f"{CSVOUT}/cross_task_stats.txt", "w") as f:
    f.write("CROSS-TASK ANALYSIS (corrected for timescales)\n" + "="*60 + "\n\n")
    f.write("TASK 1 (GEOS DYAMOND, weather-scale snapshots - NOT 1950-2025):\n")
    f.write(f"  NH jet waviness: mean {w_NH.mean():.2f} deg, "
            f"range {w_NH.min():.2f}-{w_NH.max():.2f} deg, N={len(w_NH)} snapshots\n")
    f.write("  No multi-decade jet trend is assessable from this dataset.\n\n")
    f.write("TASK 0 (ACCESS-CM2, 1950-2025 - valid climate axis):\n")
    f.write(f"  CEI avg persistence trend: slope {slp_c:.6f}/yr, "
            f"r={r_c:.3f}, p={p_c:.4f} (flat - CEI is normalized per frame)\n")
    f.write("  Feature count ~750/yr; hotspots validate against IPCC AR6 regions "
            "(see regional_trends.csv: 1.13-1.27x elevation, all 6 regions).\n\n")
    f.write("LINK BETWEEN SCALES:\n")
    f.write("  Cited from literature: Francis & Vavrus (2012) associate Arctic\n")
    f.write("  amplification with wavier jets and more persistent surface extremes.\n")
    f.write("  Our contribution: visual/topological characterization at each scale\n")
    f.write("  and a combined visualization; no cross-scale correlation is claimed.\n")
print("Stats: outputs/cross_task_stats.txt")

# -- Main 3-panel figure -------------------------------------------------------
dark = "#0d0f14"
fig = plt.figure(figsize=(18, 5.6), facecolor=dark)
gs  = gridspec.GridSpec(1, 3, figure=fig, wspace=0.32)

def style(ax):
    ax.set_facecolor(dark)
    for sp in ax.spines.values(): sp.set_edgecolor("#444")
    ax.tick_params(colors="#888", labelsize=9)
    ax.xaxis.label.set_color("#aaa"); ax.yaxis.label.set_color("#aaa")
    ax.title.set_color("#eee")

# A - waviness per snapshot
ax1 = fig.add_subplot(gs[0]); style(ax1)
ax1.axhspan(w_NH.mean()-w_NH.std(), w_NH.mean()+w_NH.std(),
            color="#44aaff", alpha=0.10)
ax1.plot(snap, w_NH, "o-", color="#44aaff", lw=2, ms=6)
ax1.axhline(w_NH.mean(), color="#88ccff", lw=1, ls=":")
ax1.set_xlabel("GEOS snapshot # (6-hourly)")
ax1.set_ylabel("NH jet waviness (deg)")
ax1.set_title("A.  Jet waviness - weather scale\n(GEOS DYAMOND snapshots)", fontsize=10)

# B - CEI persistence 1950-2025 (the valid time axis)
ax2 = fig.add_subplot(gs[1]); style(ax2)
ax2.plot(t0_years[okc], t0_avg[okc], "-", color="#ff6622", lw=1.1, alpha=0.65,
         label="Annual")
roll = np.convolve(t0_avg[okc], np.ones(5)/5, "valid")
ax2.plot(t0_years[okc][2:-2], roll, color="white", lw=2.4, label="5-yr mean")
ax2.set_xlabel("Year"); ax2.set_ylabel("Avg CEI persistence")
ax2.set_title("B.  CEI topological persistence - climate scale\n"
              "(ACCESS-CM2, 1950-2025)", fontsize=10)
ax2.legend(fontsize=8, facecolor="#1a1c22", labelcolor="#ccc")

# C - waviness envelope
ax3 = fig.add_subplot(gs[2]); style(ax3)
ax3.hist(w_NH, bins=8, color="#44aaff", alpha=0.85, edgecolor=dark)
ax3.axvline(w_NH.mean(), color="white", lw=2)
ax3.set_xlabel("NH waviness (deg)"); ax3.set_ylabel("Snapshots")
ax3.set_title(f"C.  Waviness envelope\nmean {w_NH.mean():.1f} deg, "
              f"range {w_NH.min():.1f}-{w_NH.max():.1f} deg", fontsize=10)

plt.suptitle(
    "Two scales, one system: weather-scale jet variability (Task 1) and the "
    "climate-scale extremes record (Task 0)\n"
    "Coupling mechanism cited from Francis & Vavrus (2012); "
    "no cross-scale correlation is claimed from these datasets",
    color="#ccc", fontsize=10.5, y=1.06)
fig.savefig(f"{OUTDIR}/cross_task_main.png", dpi=180,
            bbox_inches="tight", facecolor=dark)
print("Figure: renders/cross_task_main.png")

# -- Jet profile figure (snapshot labels, not years) ---------------------------
REPO  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026"
U_all = np.load(f"{REPO}/_reproj_tmp/U_all.npy")
V_all = np.load(f"{REPO}/_reproj_tmp/V_all.npy")
NLAT, NLON = U_all.shape[1], U_all.shape[2]
lats = np.linspace(-89.75, 89.75, NLAT)
lons = np.linspace(-179.75, 179.75, NLON)
NH   = (lats >= 20) & (lats <= 80)

fig2, ax = plt.subplots(figsize=(14, 5), facecolor=dark)
style(ax)
picks = [(0, "#4488ff"), (5, "#88aaff"), (10, "#ffaa44"), (15, "#ff4422")]
for tidx, color in picks:
    spd = np.sqrt(U_all[tidx]**2 + V_all[tidx]**2)
    nh_spd = spd[NH, :]; nh_lats = lats[NH]
    jl = nh_lats[nh_spd.argmax(axis=0)]
    ax.plot(lons, jl, color=color, lw=1.8, alpha=0.9,
            label=f"snapshot {tidx+1}  (waviness={jl.std():.1f} deg)")
ax.axhline(50, color="#555", lw=0.7, ls=":")
ax.set_xlim(-180, 180); ax.set_ylim(20, 80)
ax.set_xlabel("Longitude"); ax.set_ylabel("Jet core latitude (deg N)")
ax.set_title("NH jet-core meander across GEOS weather-scale snapshots\n"
             "The jet explores straight and highly wavy states within days",
             fontsize=11)
ax.legend(facecolor="#1a1c22", labelcolor="#ccc", fontsize=9)
plt.tight_layout()
fig2.savefig(f"{OUTDIR}/cross_task_jetprofile.png", dpi=150,
             bbox_inches="tight", facecolor=dark)
print("Figure: renders/cross_task_jetprofile.png")
