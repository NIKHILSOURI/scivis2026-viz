#!/usr/bin/env python
"""
build_active_trajectory_frames.py  -- pure Python, no pvpython needed

Problem: task0_pd_trajectories.vtp shows ALL 76 years of tracks at once --
a frozen spaghetti that fights the animated critical points.

Solution: for each year t, write a VTP that contains ONLY the trajectory
segments of features that are ALIVE at year t, i.e. their trail from
birth up to and including year t.  This gives a "growing trail" animation
that changes every frame in sync with the critical point glyphs.

Each per-year VTP contains:
  - Polylines: one per active trajectory, showing points from birth -> year t
  - Point arrays: Persistence, Birth, EventType, TrajectoryID, AgeYears
  - Colouring by Persistence (older/stronger = brighter)

Output:
  task0_climate/active_traj/active_traj_tXX.vtp  (76 files)
  task0_climate/active_traj/active_traj.pvd

Run: python scripts/build_active_trajectory_frames.py
"""
import os, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

B       = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
IN_VTP  = f"{B}/outputs/task0_pd_trajectories.vtp"
OUTDIR  = f"{B}/task0_climate/active_traj"
os.makedirs(OUTDIR, exist_ok=True)

# ── Load full trajectory VTP ──────────────────────────────────────────────────
r = vtk.vtkXMLPolyDataReader(); r.SetFileName(IN_VTP); r.Update()
src = r.GetOutput()

pd        = src.GetPointData()
all_pts   = vtk_to_numpy(src.GetPoints().GetData())   # (N,3)
ts_arr    = vtk_to_numpy(pd.GetArray("TimeStep"))      # int per point
tid_arr   = vtk_to_numpy(pd.GetArray("TrajectoryID"))
pers_arr  = vtk_to_numpy(pd.GetArray("Persistence"))
birth_arr = vtk_to_numpy(pd.GetArray("Birth"))
ev_arr    = vtk_to_numpy(pd.GetArray("EventType"))

# Group points by TrajectoryID -> ordered list of (timestep, point_index)
from collections import defaultdict
traj_points = defaultdict(list)   # tid -> [(t, global_idx)]
for i in range(len(ts_arr)):
    traj_points[int(tid_arr[i])].append((int(ts_arr[i]), i))
for tid in traj_points:
    traj_points[tid].sort(key=lambda x: x[0])   # ensure time order

print(f"Loaded {len(all_pts)} points from {len(traj_points)} trajectories")
N = 76

pvd_entries = []

for t_current in range(N):
    year = 1950 + t_current

    pts   = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    a_pers  = vtk.vtkFloatArray(); a_pers.SetName("Persistence")
    a_birth = vtk.vtkFloatArray(); a_birth.SetName("Birth")
    a_ev    = vtk.vtkIntArray();   a_ev.SetName("EventType")
    a_tid   = vtk.vtkIntArray();   a_tid.SetName("TrajectoryID")
    a_age   = vtk.vtkIntArray();   a_age.SetName("AgeYears")

    pid = 0
    for tid, ordered in traj_points.items():
        # Only include segments alive at or before t_current
        trail = [(t, gi) for t, gi in ordered if t <= t_current]
        if len(trail) < 1:
            continue

        # Show up to last 10 years of trail (avoid long visual tails)
        TAIL = 10
        trail = trail[-TAIL:]

        lines.InsertNextCell(len(trail))
        for t_pt, gi in trail:
            pts.InsertNextPoint(all_pts[gi])
            age = t_current - t_pt
            a_pers.InsertNextValue(float(pers_arr[gi]))
            a_birth.InsertNextValue(float(birth_arr[gi]))
            a_ev.InsertNextValue(int(ev_arr[gi]))
            a_tid.InsertNextValue(tid)
            a_age.InsertNextValue(age)
            lines.InsertCellPoint(pid); pid += 1

    poly = vtk.vtkPolyData()
    poly.SetPoints(pts); poly.SetLines(lines)
    for a in (a_pers, a_birth, a_ev, a_tid, a_age):
        poly.GetPointData().AddArray(a)
    poly.GetPointData().SetActiveScalars("Persistence")

    fpath = f"{OUTDIR}/active_traj_t{t_current:02d}.vtp"
    w = vtk.vtkXMLPolyDataWriter()
    w.SetFileName(fpath); w.SetInputData(poly); w.Write()
    pvd_entries.append((fpath, float(year)))

    n_active = sum(1 for ordered in traj_points.values()
                   if any(t <= t_current for t, _ in ordered))
    print(f"  t{t_current:02d} {year}: {n_active} active trajectories, {pid} pts")

# ── Write PVD ─────────────────────────────────────────────────────────────────
pvd_path = f"{OUTDIR}/active_traj.pvd"
with open(pvd_path, "w", encoding="ascii") as f:
    f.write('<?xml version="1.0"?>\n<VTKFile type="Collection" version="0.1">\n')
    f.write('  <Collection>\n')
    for fp, t in pvd_entries:
        f.write(f'    <DataSet timestep="{t}" file="{fp}"/>\n')
    f.write('  </Collection>\n</VTKFile>\n')

print(f"\nDone. PVD: {pvd_path}")
print(f"76 per-year VTPs in: {OUTDIR}")
print("Now update viz_task0.py: replace TTK_TRACKS with this PVD")
