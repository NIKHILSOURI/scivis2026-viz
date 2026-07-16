#!/usr/bin/env python
"""
compute_waviness.py  (CORRECTED - honest timescale)

GEOS DYAMOND is a SHORT simulation (weeks of model time, 6-hourly output).
Its 16 snapshots do NOT span 1950-2025 - earlier versions of this script
mapped snapshots to years, which was wrong and is removed here.

What this computes (valid claims only):
  - NH/SH jet waviness per GEOS snapshot = std of the jet-core latitude
    across longitudes (weather-scale variability of jet meandering)
  - The waviness RANGE the jet explores at weather timescales

Outputs:
  renders/waviness_trend.png   (snapshot axis, no year axis)
  outputs/waviness.csv         (column 'snapshot', not 'year')
"""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
REPO   = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026"
OUTDIR = f"{B}/renders/figures"; CSVOUT = f"{B}/outputs"

U_all = np.load(f"{REPO}/_reproj_tmp/U_all.npy")
V_all = np.load(f"{REPO}/_reproj_tmp/V_all.npy")
T, NLAT, NLON = U_all.shape
lats = np.linspace(-90 + 90/NLAT, 90 - 90/NLAT, NLAT)

NH = (lats >= 20) & (lats <= 80)
SH = (lats <= -20) & (lats >= -80)

rows = []
for t in range(T):
    spd = np.sqrt(U_all[t]**2 + V_all[t]**2)
    out = [t]
    for mask in (NH, SH):
        s = spd[mask, :]; ml = lats[mask]
        jl = ml[s.argmax(axis=0)]
        out += [float(jl.std()), float(jl.mean())]
    rows.append(out)
    print(f"  snapshot {t:02d}: NH waviness={out[1]:.2f}  SH waviness={out[3]:.2f}")

rows = np.array(rows)
wNH, latNH, wSH, latSH = rows[:,1], rows[:,2], rows[:,3], rows[:,4]

with open(f"{CSVOUT}/waviness.csv", "w") as f:
    f.write("snapshot,waviness_NH,waviness_SH,jet_lat_NH,jet_lat_SH\n")
    for r in rows:
        f.write(f"{int(r[0])},{r[1]:.4f},{r[3]:.4f},{r[2]:.2f},{r[4]:.2f}\n")
print(f"CSV: {CSVOUT}/waviness.csv")

# -- Figure: variability, NOT trend --------------------------------------------
dark = "#0d0f14"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor=dark,
                               gridspec_kw=dict(width_ratios=[1.5, 1]))
for ax in (ax1, ax2):
    ax.set_facecolor(dark); ax.tick_params(colors="#999")
    for sp in ax.spines.values(): sp.set_edgecolor("#555")

x = rows[:, 0]
ax1.axhspan(wNH.mean()-wNH.std(), wNH.mean()+wNH.std(), color="#44aaff", alpha=0.10)
ax1.plot(x, wNH, "o-", color="#44aaff", lw=2, ms=6, label="NH jet")
ax1.plot(x, wSH, "s--", color="#ff8844", lw=1.5, ms=5, label="SH jet")
ax1.axhline(wNH.mean(), color="#88ccff", lw=1, ls=":")
ax1.set_xlabel("GEOS snapshot # (6-hourly, DYAMOND period)", color="#aaa")
ax1.set_ylabel("Waviness (std of jet-core latitude, deg)", color="#aaa")
ax1.set_title("Jet-stream waviness across weather-scale snapshots",
              color="#eee", fontsize=11)
ax1.legend(facecolor="#1a1c22", labelcolor="#ccc")

ax2.hist(wNH, bins=8, color="#44aaff", alpha=0.8, edgecolor="#0d0f14")
ax2.axvline(wNH.mean(), color="white", lw=2)
ax2.set_xlabel("NH waviness (deg)", color="#aaa")
ax2.set_ylabel("Snapshots", color="#aaa")
ax2.set_title(f"NH waviness envelope\nmean {wNH.mean():.1f} deg | "
              f"range {wNH.min():.1f}-{wNH.max():.1f} deg",
              color="#eee", fontsize=10)

plt.suptitle("Weather-scale jet variability (GEOS DYAMOND) - no multi-decade "
             "trend is assessable from this period", color="#bbb", fontsize=10, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/waviness_trend.png", dpi=160,
            bbox_inches="tight", facecolor=dark)
print(f"Figure: {OUTDIR}/waviness_trend.png")
print(f"\nVALID CLAIM: NH jet waviness varies {wNH.min():.1f}-{wNH.max():.1f} deg "
      f"(mean {wNH.mean():.1f}) across GEOS weather-scale snapshots.")
