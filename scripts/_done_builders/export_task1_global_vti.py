#!/usr/bin/env python
# Export the global jet-stream reprojected wind to VTI+PVD for ParaView.
# Reads cached numpy arrays from _reproj_tmp/ (built by make_task1_animation.py).
# Outputs:
#   task1_atmosphere/global_frames/task1_global_t00.vti  ...t15.vti
#   task1_atmosphere/global_frames/task1_global.pvd      (time series index)
# Fields per VTI:
#   WindSpeed_ms  — scalar (for colour / persistence / TTK)
#   Wind_ms       — 3-component vector (U, V, 0) for streamlines / LIC in ParaView

import sys, os, numpy as np
from scipy.ndimage import gaussian_filter

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026"
sys.path.insert(0, f"{B}/##ParaView_New")
from _vtizlib import write_frame_vti, write_pvd

CACHE_U = f"{B}/_reproj_tmp/U_all.npy"
CACHE_V = f"{B}/_reproj_tmp/V_all.npy"

if not os.path.exists(CACHE_U):
    print("ERROR: run make_task1_animation.py first to build the cached arrays.")
    sys.exit(1)

print("Loading cached reprojected wind ...")
U_all = np.load(CACHE_U)          # (16, 360, 720)  raw (unsmoothed)
V_all = np.load(CACHE_V)
NF, NLAT, NLON = U_all.shape
print(f"  {NF} steps, {NLON}x{NLAT} grid")

OUTDIR = f"{B}/##ParaView_New/task1_atmosphere/global_frames"
os.makedirs(OUTDIR, exist_ok=True)

# Grid metadata matching the lat/lon extent
ORIGIN  = (-179.75, -89.75)        # lower-left corner (lon, lat)
SPACING = (360.0 / NLON, 180.0 / NLAT)   # ~0.5 deg per pixel

frame_files, times = [], []

for t in range(NF):
    U = gaussian_filter(U_all[t].astype(np.float32), sigma=6)
    V = gaussian_filter(V_all[t].astype(np.float32), sigma=6)
    spd = np.sqrt(U*U + V*V)

    scalars = {"WindSpeed_ms": spd}
    vectors = {"Wind_ms": (U, V, np.zeros_like(U))}

    fp = f"{OUTDIR}/task1_global_t{t:02d}.vti"
    sz = write_frame_vti(fp, scalars, NLON, NLAT, ORIGIN, SPACING, vectors=vectors)
    frame_files.append(fp)
    times.append(float(t))
    print(f"  t{t:02d}  speed_max={spd.max():.1f}  {sz/1e6:.1f} MB  -> {os.path.basename(fp)}")

pvd = f"{OUTDIR}/task1_global.pvd"
write_pvd(pvd, frame_files, times)
print(f"\nPVD index -> {pvd}")
print(f"Load in ParaView: File > Open > task1_global.pvd")
print(f"Colour by: WindSpeed_ms (Inferno or Plasma)")
print(f"Streamlines: Filters > Alphabetical > Stream Tracer  (use Wind_ms vector)")
