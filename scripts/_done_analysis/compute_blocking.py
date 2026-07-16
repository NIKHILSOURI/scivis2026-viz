#!/usr/bin/env python
"""
compute_blocking.py — the MECHANISM figure: do persistent anticyclones
(blocking highs) sit over the regions where compound extremes concentrate?

Method (spatial co-location, honest about timescales):
  1. Load 16 GEOS vorticity fields (task1_global VTIs, weather-scale snapshots).
  2. NH band 35-75N: cell is "anticyclonic" when vorticity < 5th percentile.
  3. Blocking-likeness B(x,y) = fraction of snapshots the cell is anticyclonic
     (persistent high = blocking signature).
  4. Load 76-yr mean CEI from Task 0 (climate-scale hotspot climatology).
  5. Test: is CEI significantly elevated under high-B cells vs the NH band mean?

Note for the paper: GEOS is weather-scale (DYAMOND period), ACCESS-CM2 is
climate-scale. This is a SPATIAL correspondence test, not a temporal one.

Run: python scripts/_done_analysis/compute_blocking.py
Out: renders/blocking_mechanism.png, outputs/blocking_stats.txt
"""
import os, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, mannwhitneyu
from scipy.ndimage import gaussian_filter

B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
G  = f"{B}/task1_atmosphere/global"
F  = f"{B}/task0_climate/frames"
R  = f"{B}/renders"; O = f"{B}/outputs"

def read_vti_array(path, name, ny, nx):
    r = vtk.vtkXMLImageDataReader(); r.SetFileName(path); r.Update()
    return vtk_to_numpy(r.GetOutput().GetPointData().GetArray(name)).reshape(ny, nx)

# ── 1-3: blocking-likeness from 16 vorticity snapshots ────────────────────────
NLAT, NLON = 360, 720
lats = np.linspace(-89.75, 89.75, NLAT)
lons = np.linspace(-179.75, 179.75, NLON)
band = (lats >= 35) & (lats <= 75)

anti_count = np.zeros((NLAT, NLON))
for t in range(16):
    vort = read_vti_array(f"{G}/task1_global_t{t:02d}.vti", "Vorticity_s-1", NLAT, NLON)
    thr = np.percentile(vort[band, :], 5)          # strongly anticyclonic (NH)
    anti_count += (vort < thr)
Bmap = anti_count / 16.0                            # 0..1 fraction of snapshots

# ── 4: 76-yr mean CEI from Task 0 ─────────────────────────────────────────────
# Task 0 grid differs; read one frame for its dims
r0 = vtk.vtkXMLImageDataReader(); r0.SetFileName(f"{F}/task0_t00.vti"); r0.Update()
d0 = r0.GetOutput().GetDimensions()
nx0, ny0 = d0[0], d0[1]
cei_mean = np.zeros((ny0, nx0))
n = 0
for idx in range(0, 76, 4):
    cei_mean += read_vti_array(f"{F}/task0_t{idx:02d}.vti", "CompoundExtremesIndex", ny0, nx0)
    n += 1
cei_mean /= n
# resample CEI to the vorticity grid (simple index mapping)
o0 = r0.GetOutput().GetOrigin(); s0 = r0.GetOutput().GetSpacing()
cei_on_v = np.full((NLAT, NLON), np.nan)
for iy in range(NLAT):
    jy = int(round((lats[iy] - o0[1]) / s0[1]))
    if jy < 0 or jy >= ny0: continue
    for_ix = ((lons - o0[0]) / s0[0]).round().astype(int)
    ok = (for_ix >= 0) & (for_ix < nx0)
    cei_on_v[iy, ok] = cei_mean[jy, for_ix[ok]]

# ── 5: co-location statistics in the NH band ──────────────────────────────────
bm  = Bmap[band, :].ravel()
cm  = cei_on_v[band, :].ravel()
ok  = np.isfinite(cm) & (cm > 0)
bm, cm = bm[ok], cm[ok]

r_sp, p_sp = pearsonr(bm, cm)
hiB  = bm >= np.percentile(bm, 90)                 # top-10% blocking cells
u, p_mw = mannwhitneyu(cm[hiB], cm[~hiB], alternative="greater")
lift = cm[hiB].mean() / cm[~hiB].mean()

txt = (f"Blocking-CEI spatial co-location (NH 35-75N)\n"
       f"  Spatial Pearson r = {r_sp:.3f} (p = {p_sp:.2e}, N = {ok.sum()})\n"
       f"  Mean CEI under top-10% blocking cells: {cm[hiB].mean():.3f}\n"
       f"  Mean CEI elsewhere in band:            {cm[~hiB].mean():.3f}\n"
       f"  Lift = {lift:.3f}x   Mann-Whitney p = {p_mw:.2e}\n")
print(txt)
with open(f"{O}/blocking_stats.txt", "w") as f:
    f.write(txt)

# ── Figure ────────────────────────────────────────────────────────────────────
dark = "#0d0f14"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 5.2), facecolor=dark,
                               gridspec_kw=dict(width_ratios=[1.5, 1]))
for ax in (ax1, ax2):
    ax.set_facecolor(dark); ax.tick_params(colors="#888")
    for sp in ax.spines.values(): sp.set_edgecolor("#555")

ext = [-180, 180, 35, 75]
Bs = gaussian_filter(Bmap, 2)[band, :]
im = ax1.imshow(Bs, origin="lower", extent=ext, cmap="cividis", aspect="auto")
cb = fig.colorbar(im, ax=ax1, fraction=0.03, pad=0.02)
cb.set_label("Blocking-likeness (fraction of snapshots)", color="#999")
cb.ax.yaxis.set_tick_params(color="#777")
plt.setp(cb.ax.axes.get_yticklabels(), color="#999")
cb.outline.set_edgecolor("#555")
# CEI hotspot contours on top
cei_band = np.where(np.isfinite(cei_on_v), cei_on_v, 0)[band, :]
cs = ax1.contour(np.linspace(-180, 180, NLON), lats[band],
                 gaussian_filter(cei_band, 2),
                 levels=[np.nanpercentile(cm, 75), np.nanpercentile(cm, 90)],
                 colors=["#ff8844", "#ff3322"], linewidths=[1.2, 1.8])
ax1.set_title("Persistent anticyclones (background) vs CEI hotspots (red contours)\n"
              "NH 35-75N | GEOS weather-scale blocking x ACCESS-CM2 climate CEI",
              color="#eee", fontsize=10)
ax1.set_xlabel("Longitude", color="#aaa"); ax1.set_ylabel("Latitude", color="#aaa")

ax2.boxplot([cm[~hiB], cm[hiB]], tick_labels=["Other cells", "Top-10%\nblocking"],
            patch_artist=True,
            boxprops=dict(facecolor="#28466e", color="#89b"),
            medianprops=dict(color="#ffdd44", lw=2),
            whiskerprops=dict(color="#89b"), capprops=dict(color="#89b"),
            flierprops=dict(marker=".", markersize=2, markerfacecolor="#456"))
ax2.set_ylabel("76-yr mean CEI", color="#aaa")
ax2.set_title(f"CEI is {lift:.2f}x higher under\npersistent anticyclones (p={p_mw:.1e})",
              color="#eee", fontsize=10)
plt.setp(ax2.get_xticklabels(), color="#aaa")

plt.suptitle("Mechanism: blocking highs spatially co-locate with compound-extreme hotspots",
             color="#eee", fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(f"{R}/blocking_mechanism.png", dpi=170, bbox_inches="tight", facecolor=dark)
print(f"Figure: {R}/blocking_mechanism.png")
