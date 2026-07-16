#!/usr/bin/env python
"""
build_spacetime_tubes.py — pure Python

The signature visualization: SPACE-TIME feature tracking.
  x, y = longitude, latitude
  z    = TIME (1950 at the map surface, 2025 at the top)

Every CEI extreme trajectory becomes a 3D tube rising through time:
  - tall vertical tubes  = long-lived persistent extremes (the dangerous ones)
  - short stubs          = transient noise
  - tilted tubes         = features that migrated geographically
  - the vertical axis IS the climate record

Filters (same hygiene as viz_task0_summary):
  persistence >= PERSIST_THRESH, no geographic jumps > MAX_SEG_DEG.

Outputs:
  outputs/spacetime_tracks.vtp   (polylines with z=time)
  outputs/spacetime_events.vtp   (birth/death markers in space-time)

Run: python scripts/build_spacetime_tubes.py
Then: viz_spacetime.py in ParaView.
"""
import os, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy
from collections import defaultdict

B   = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
IN  = f"{B}/outputs/task0_pd_trajectories.vtp"
OUT = f"{B}/outputs"

PERSIST_THRESH = 0.15    # keep meaningful features (lower than summary: 3D declutters)
MAX_SEG_DEG    = 12.0    # reject matcher jump artifacts
MIN_YEARS      = 5       # only tracks alive >= 5 years (the story is longevity)
Z_PER_YEAR     = 1.6     # vertical scale: 76 yr -> 120 units (map is 360 wide)

r = vtk.vtkXMLPolyDataReader(); r.SetFileName(IN); r.Update()
src = r.GetOutput()
pts  = vtk_to_numpy(src.GetPoints().GetData())
pd   = src.GetPointData()
ts   = vtk_to_numpy(pd.GetArray("TimeStep"))
tid  = vtk_to_numpy(pd.GetArray("TrajectoryID"))
per  = vtk_to_numpy(pd.GetArray("Persistence"))
ev   = vtk_to_numpy(pd.GetArray("EventType"))

traj = defaultdict(list)
for i in range(len(tid)):
    traj[int(tid[i])].append(i)

kept, dropped_jump, dropped_weak, dropped_short = 0, 0, 0, 0

o_pts   = vtk.vtkPoints()
o_lines = vtk.vtkCellArray()
a_per   = vtk.vtkFloatArray(); a_per.SetName("Persistence")
a_year  = vtk.vtkFloatArray(); a_year.SetName("Year")
a_life  = vtk.vtkFloatArray(); a_life.SetName("LifetimeYears")
a_ev    = vtk.vtkIntArray();   a_ev.SetName("EventType")

e_pts   = vtk.vtkPoints()
e_verts = vtk.vtkCellArray()
e_type  = vtk.vtkIntArray();   e_type.SetName("EventType")
e_year  = vtk.vtkFloatArray(); e_year.SetName("Year")

pid = 0; eid = 0
for t_id, idxs in traj.items():
    idxs = sorted(idxs, key=lambda i: int(ts[i]))
    if per[idxs].mean() < PERSIST_THRESH:
        dropped_weak += 1; continue
    P = pts[idxs]
    jumps = np.sqrt(((P[1:, :2] - P[:-1, :2]) ** 2).sum(axis=1))
    if len(jumps) and jumps.max() > MAX_SEG_DEG:
        dropped_jump += 1; continue
    lifetime = int(ts[idxs[-1]]) - int(ts[idxs[0]]) + 1
    if lifetime < MIN_YEARS:
        dropped_short += 1; continue

    kept += 1
    o_lines.InsertNextCell(len(idxs))
    for i in idxs:
        year = 1950 + int(ts[i])
        z = (year - 1950) * Z_PER_YEAR
        o_pts.InsertNextPoint(float(pts[i, 0]), float(pts[i, 1]), z)
        a_per.InsertNextValue(float(per[i]))
        a_year.InsertNextValue(float(year))
        a_life.InsertNextValue(float(lifetime))
        a_ev.InsertNextValue(int(ev[i]))
        o_lines.InsertCellPoint(pid); pid += 1

    # birth + death markers in space-time
    for j, marker in ((idxs[0], 1), (idxs[-1], 2)):
        year = 1950 + int(ts[j])
        e_pts.InsertNextPoint(float(pts[j, 0]), float(pts[j, 1]),
                              (year - 1950) * Z_PER_YEAR)
        e_verts.InsertNextCell(1); e_verts.InsertCellPoint(eid); eid += 1
        e_type.InsertNextValue(marker)
        e_year.InsertNextValue(float(year))

poly = vtk.vtkPolyData()
poly.SetPoints(o_pts); poly.SetLines(o_lines)
for a in (a_per, a_year, a_life, a_ev):
    poly.GetPointData().AddArray(a)
poly.GetPointData().SetActiveScalars("LifetimeYears")
w = vtk.vtkXMLPolyDataWriter()
w.SetFileName(f"{OUT}/spacetime_tracks.vtp"); w.SetInputData(poly); w.Write()

epoly = vtk.vtkPolyData()
epoly.SetPoints(e_pts); epoly.SetVerts(e_verts)
epoly.GetPointData().AddArray(e_type); epoly.GetPointData().AddArray(e_year)
epoly.GetPointData().SetActiveScalars("EventType")
w2 = vtk.vtkXMLPolyDataWriter()
w2.SetFileName(f"{OUT}/spacetime_events.vtp"); w2.SetInputData(epoly); w2.Write()

print(f"Kept {kept} tracks ({pid} points)   "
      f"[dropped: {dropped_weak} weak, {dropped_jump} jump-artifacts, "
      f"{dropped_short} short-lived]")
print(f"Z axis: 1950 = 0, 2025 = {75*Z_PER_YEAR:.0f} units ({Z_PER_YEAR}/yr)")
print(f"Wrote {OUT}/spacetime_tracks.vtp and spacetime_events.vtp")
