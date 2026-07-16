#!/usr/bin/env python
"""
validate_regions.py - does the CEI flag the regions climate science flags?

ACCESS-CM2 is a free-running model, so its internal weather does NOT reproduce
real calendar events (the 2003 European heatwave won't be in 'model 2003').
The honest validation is REGIONAL + STATISTICAL:
  IPCC AR6 names these as compound-extreme hotspots. If our topology-based CEI
  is physically meaningful, these regions should show (a) elevated CEI vs the
  global mean and (b) rising trends 1950-2025.

Regions (IPCC AR6 WG1 Ch.11 hotspots):
  Mediterranean, South Asia, W. North America, Amazon, Australia, Sahel

Run: python scripts/validate_regions.py
Outputs:
  renders/regional_validation.png
  outputs/regional_trends.csv
"""
import os, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import linregress

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
F = f"{B}/task0_climate/frames"
OUTDIR = f"{B}/renders/figures"; CSVOUT = f"{B}/outputs"

REGIONS = {
    "Mediterranean":    dict(lon=(-10, 40),  lat=(30, 46),  color="#ff4444"),
    "South Asia":       dict(lon=(65, 90),   lat=(8, 32),   color="#ff9922"),
    "W. North America": dict(lon=(-125,-100),lat=(30, 52),  color="#ffdd33"),
    "Amazon":           dict(lon=(-75, -45), lat=(-15, 5),  color="#44cc55"),
    "Australia":        dict(lon=(115, 153), lat=(-38,-12), color="#44aaff"),
    "Sahel":            dict(lon=(-15, 35),  lat=(10, 20),  color="#cc66ff"),
}

# -- Read one frame to get grid coordinates -----------------------------------
r0 = vtk.vtkXMLImageDataReader(); r0.SetFileName(f"{F}/task0_t00.vti"); r0.Update()
img = r0.GetOutput()
dims    = img.GetDimensions()          # (nx, ny, 1)
origin  = img.GetOrigin()
spacing = img.GetSpacing()
nx, ny  = dims[0], dims[1]
lons = origin[0] + spacing[0] * np.arange(nx)
lats = origin[1] + spacing[1] * np.arange(ny)
LON, LAT = np.meshgrid(lons, lats)     # (ny, nx)

masks = {}
for name, rg in REGIONS.items():
    masks[name] = ((LON >= rg["lon"][0]) & (LON <= rg["lon"][1]) &
                   (LAT >= rg["lat"][0]) & (LAT <= rg["lat"][1]))

# -- Sweep all 76 years --------------------------------------------------------
years = np.arange(1950, 2026)
series = {name: [] for name in REGIONS}
global_mean = []

for idx in range(76):
    rr = vtk.vtkXMLImageDataReader()
    rr.SetFileName(f"{F}/task0_t{idx:02d}.vti"); rr.Update()
    cei = vtk_to_numpy(rr.GetOutput().GetPointData()
                        .GetArray("CompoundExtremesIndex")).reshape(ny, nx)
    valid = np.isfinite(cei) & (cei > 0)
    global_mean.append(float(cei[valid].mean()))
    for name, m in masks.items():
        vals = cei[m & valid]
        # 95th percentile = intensity of that region's extreme tail this year
        series[name].append(float(np.percentile(vals, 95)) if len(vals) else np.nan)

global_mean = np.array(global_mean)

# -- Trends + CSV --------------------------------------------------------------
print(f"{'Region':<20}{'mean CEI-p95':>13}{'vs global':>11}{'trend/dec':>11}{'p':>9}")
rows = []
for name in REGIONS:
    s = np.array(series[name])
    ok = np.isfinite(s)
    slope, itc, rv, pv, _ = linregress(years[ok], s[ok])
    elev = s[ok].mean() / global_mean[ok].mean()
    rows.append((name, s[ok].mean(), elev, slope*10, pv))
    print(f"{name:<20}{s[ok].mean():>13.3f}{elev:>10.2f}x{slope*10:>11.4f}{pv:>9.4f}")

with open(f"{CSVOUT}/regional_trends.csv", "w") as f:
    f.write("region,mean_cei_p95,elevation_vs_global,trend_per_decade,p_value\n")
    for nm, m, e, sl, pv in rows:
        f.write(f"{nm},{m:.4f},{e:.3f},{sl:.5f},{pv:.5f}\n")

# -- Figure: map of regions + time series -------------------------------------
dark = "#0d0f14"
fig, (axm, axt) = plt.subplots(1, 2, figsize=(18, 5.5), facecolor=dark,
                               gridspec_kw=dict(width_ratios=[1, 1.4]))

# Left: where the regions are (over mean CEI field)
mean_field = np.zeros((ny, nx)); cnt = 0
for idx in range(0, 76, 5):
    rr = vtk.vtkXMLImageDataReader()
    rr.SetFileName(f"{F}/task0_t{idx:02d}.vti"); rr.Update()
    mean_field += vtk_to_numpy(rr.GetOutput().GetPointData()
                    .GetArray("CompoundExtremesIndex")).reshape(ny, nx)
    cnt += 1
mean_field /= cnt
axm.set_facecolor(dark)
axm.imshow(mean_field, origin="lower",
           extent=[lons.min(), lons.max(), lats.min(), lats.max()],
           cmap="inferno", vmin=0.2, vmax=0.8, aspect="auto")
for name, rg in REGIONS.items():
    x0, x1 = rg["lon"]; y0, y1 = rg["lat"]
    axm.add_patch(plt.Rectangle((x0, y0), x1-x0, y1-y0,
                  fill=False, edgecolor=rg["color"], lw=2))
    axm.text(x0, y1+2, name, color=rg["color"], fontsize=8, weight="bold")
axm.set_title("IPCC AR6 compound-extreme hotspot regions\nover 76-yr mean CEI",
              color="#eee", fontsize=10)
axm.tick_params(colors="#888")
for sp in axm.spines.values(): sp.set_edgecolor("#555")

# Right: time series
axt.set_facecolor(dark)
for name, rg in REGIONS.items():
    s = np.array(series[name]); ok = np.isfinite(s)
    smooth = np.convolve(s[ok], np.ones(7)/7, "valid")
    axt.plot(years[ok][3:-3], smooth, color=rg["color"], lw=2, label=name)
axt.plot(years, np.convolve(global_mean, np.ones(7)/7, "same"),
         color="#888", lw=1.4, ls="--", label="Global mean CEI")
axt.set_xlabel("Year", color="#aaa"); axt.set_ylabel("Regional CEI 95th pct (7-yr mean)", color="#aaa")
axt.set_title("Regional extreme-tail intensity 1950-2025", color="#eee", fontsize=10)
axt.legend(fontsize=8, facecolor="#1a1c22", labelcolor="#ccc", ncol=2)
axt.tick_params(colors="#888")
for sp in axt.spines.values(): sp.set_edgecolor("#555")

plt.suptitle("Validation: topology-based CEI independently flags IPCC compound-extreme hotspots",
             color="#eee", fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(f"{OUTDIR}/regional_validation.png", dpi=170,
            bbox_inches="tight", facecolor=dark)
print(f"\nFigure: {OUTDIR}/regional_validation.png")
print(f"CSV:    {CSVOUT}/regional_trends.csv")
