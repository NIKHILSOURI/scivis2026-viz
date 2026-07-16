#!/usr/bin/env python
"""
task0_ttk_pd_tracking.py  —  pvpython batch script
Tries TTK Tracking from Persistence Diagrams.
If it works  -> saves task0_ttk_pd_tracks.vtp  (use in viz instead of Hungarian)
If it crashes -> prints clear fallback instructions (use build_trajectories.py output)

Run:
  "C:\\Program Files\\ParaView 6.1.1\\bin\\pvpython.exe" ^
    scripts/task0_ttk_pd_tracking.py
"""
import sys, os, glob
from paraview.simple import *
from paraview import servermanager as sm
from vtk.util.numpy_support import vtk_to_numpy
import vtk

PLUG = ("C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/"
        "TopologyToolKit/TopologyToolKit.dll")
LoadPlugin(PLUG, remote=False, ns=globals())

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
FRAMES = f"{B}/task0_climate/frames"
OUTDIR = f"{B}/outputs"
PERSIST = 0.04

vti_files = sorted(f"{FRAMES}/{f}" for f in os.listdir(FRAMES)
                   if f.startswith("task0_t") and f.endswith(".vti"))
N = len(vti_files)
print(f"Found {N} VTI files for persistence diagram tracking")

# ── Stage 1: Compute persistence diagram per timestep ─────────────────────────
# Each diagram is stored as a VTP file so we can group them.
PD_DIR = f"{B}/task0_climate/persistence_diagrams"
os.makedirs(PD_DIR, exist_ok=True)

pd_files = []
print("Stage 1: computing persistence diagrams ...")
for idx, fpath in enumerate(vti_files):
    try:
        reader = XMLImageDataReader(FileName=[fpath])
        reader.UpdatePipeline()

        pre = TTKArrayPreconditioning(Input=reader)
        pre.PointDataArrays = ["CompoundExtremesIndex"]
        pre.UpdatePipeline()

        simp = TTKTopologicalSimplificationByPersistence(Input=pre)
        simp.InputArray           = ["POINTS", "CompoundExtremesIndex"]
        simp.PersistenceThreshold = PERSIST
        simp.UpdatePipeline()

        pd = TTKPersistenceDiagram(Input=simp)
        pd.ScalarField = ["POINTS", "CompoundExtremesIndex"]
        pd.UpdatePipeline()

        out = f"{PD_DIR}/pd_t{idx:02d}.vtp"
        w = XMLPolyDataWriter(Input=pd); w.FileName = out; w.UpdatePipeline()
        pd_files.append(out)
        print(f"  t{idx:02d} -> {out}")

        Delete(pd); Delete(simp); Delete(pre); Delete(reader)

    except Exception as e:
        print(f"  ERROR at t{idx:02d}: {e}")
        sys.exit(1)

print(f"Stage 1 done: {len(pd_files)} diagrams")

# ── Stage 2: Group all diagrams and apply TTK tracking ────────────────────────
print("\nStage 2: applying TTKTrackingFromPersistenceDiagrams ...")
try:
    readers = [XMLPolyDataReader(FileName=[f]) for f in pd_files]
    for r in readers:
        r.UpdatePipeline()

    group = GroupDatasets(Input=readers)
    group.UpdatePipeline()

    tracking = TTKTrackingFromPersistenceDiagrams(Input=group)
    tracking.UpdatePipeline()

    # Save full tracking output
    track_out = f"{OUTDIR}/task0_ttk_pd_tracks.vtp"
    w2 = XMLPolyDataWriter(Input=tracking)
    w2.FileName = track_out
    w2.UpdatePipeline()

    raw = sm.Fetch(tracking)
    n_pts = raw.GetNumberOfPoints()
    n_cells = raw.GetNumberOfCells()
    print(f"\nSUCCESS: {n_pts} points, {n_cells} tracks")
    print(f"Saved to: {track_out}")
    print("\nviz_task0.py will auto-load task0_ttk_pd_tracks.vtp if present.")

except Exception as e:
    print(f"\nTTKTrackingFromPersistenceDiagrams failed: {e}")
    print("\nFALLBACK: Use our Hungarian trajectory outputs instead.")
    print("  task0_CEI_trajectories.vtp  (already built by build_trajectories.py)")
    print("  viz_task0.py handles this automatically.")
