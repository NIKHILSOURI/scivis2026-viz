#!/usr/bin/env python
"""
build_jet_core_lines.py  — pure Python

Extracts the jet stream CORE of BOTH hemispheres as polylines per Task 1
timestep: for each longitude, the latitude where wind speed peaks
(20-80N band and 20-80S band), smoothed along longitude (periodic).
The wavy NH line and the near-zonal SH line render together; the SH acts
as a visual control that makes the NH meander obvious.

This is THE visual link between Task 1 and Task 0:
  wavy jet line (upper atmosphere) drawn over the CEI extremes map (surface).

Outputs:
  task1_atmosphere/jet_core/jet_core_tXX.vtp   (16 files)
  task1_atmosphere/jet_core/jet_core.pvd       (timesteps = YEARS 1950..2025 step 5,
                                                so it animates in sync with task0.pvd)
Point arrays: CoreWindSpeed_ms (for colouring), Waviness (constant per frame).

Run: python scripts/build_jet_core_lines.py
"""
import os, numpy as np, vtk

B    = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
REPO = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026"
OUT  = f"{B}/task1_atmosphere/jet_core"
os.makedirs(OUT, exist_ok=True)

U_all = np.load(f"{REPO}/_reproj_tmp/U_all.npy")   # (16, 360, 720)
V_all = np.load(f"{REPO}/_reproj_tmp/V_all.npy")
T, NLAT, NLON = U_all.shape
lats = np.linspace(-89.75, 89.75, NLAT)
lons = np.linspace(-179.75, 179.75, NLON)
# Both hemispheres: the wavy NH jet plus the near-zonal SH jet as a visual control
BANDS = [
    ("NH", (lats >=  20) & (lats <=  80)),
    ("SH", (lats >= -80) & (lats <= -20)),
]

def periodic_smooth(y, win=21):
    """Smooth a periodic (longitude) signal with a running mean."""
    k = np.ones(win) / win
    ypad = np.concatenate([y[-win:], y, y[:win]])
    return np.convolve(ypad, k, "same")[win:-win]

pvd_entries = []
for t in range(T):
    year = 1950 + t * 5
    spd = np.sqrt(U_all[t]**2 + V_all[t]**2)

    pts   = vtk.vtkPoints()
    line  = vtk.vtkCellArray()
    a_spd = vtk.vtkFloatArray(); a_spd.SetName("CoreWindSpeed_ms")
    a_wav = vtk.vtkFloatArray(); a_wav.SetName("Waviness")

    msg = []
    k = 0
    for band_name, band in BANDS:
        band_lats = lats[band]
        b_spd     = spd[band, :]                    # (nBand, NLON)
        core_i    = b_spd.argmax(axis=0)            # per-longitude core index
        core_lat  = band_lats[core_i]
        core_spd  = b_spd[core_i, np.arange(NLON)]

        core_lat_s = periodic_smooth(core_lat, 55)  # heavier smoothing: elegant curve
        core_spd_s = periodic_smooth(core_spd, 55)
        waviness   = float(core_lat_s.std())

        line.InsertNextCell(NLON)
        for j in range(NLON):
            pts.InsertNextPoint(float(lons[j]), float(core_lat_s[j]), 0.06)
            a_spd.InsertNextValue(float(core_spd_s[j]))
            a_wav.InsertNextValue(waviness)
            line.InsertCellPoint(k); k += 1
        msg.append(f"{band_name} wav={waviness:.2f} max={core_spd_s.max():.0f} m/s")

    poly = vtk.vtkPolyData()
    poly.SetPoints(pts); poly.SetLines(line)
    poly.GetPointData().AddArray(a_spd)
    poly.GetPointData().AddArray(a_wav)
    poly.GetPointData().SetActiveScalars("CoreWindSpeed_ms")

    fp = f"{OUT}/jet_core_t{t:02d}.vtp"
    w = vtk.vtkXMLPolyDataWriter(); w.SetFileName(fp); w.SetInputData(poly); w.Write()
    pvd_entries.append((fp, float(year)))
    print(f"  t{t:02d} {year}: " + "  |  ".join(msg))

pvd = f"{OUT}/jet_core.pvd"
with open(pvd, "w", encoding="ascii") as f:
    f.write('<?xml version="1.0"?>\n<VTKFile type="Collection" version="0.1">\n  <Collection>\n')
    for fp, yr in pvd_entries:
        f.write(f'    <DataSet timestep="{yr}" file="{fp}"/>\n')
    f.write('  </Collection>\n</VTKFile>\n')
print(f"\nWrote {pvd}  (timesteps = years, syncs with task0.pvd)")
