#!/usr/bin/env python
"""
build_merge_trees.py  — pvpython script
Computes TTKMergeTree for all 76 Task 0 CEI timesteps and writes:
  outputs/merge_trees/merge_tree_arcs_tXX.vtu   (76 files)
  outputs/merge_trees/merge_tree_arcs.pvd        (PVD for animation)

Run:  pvpython scripts/build_merge_trees.py
Time: ~1 min for 76 frames at full res.
"""
import sys, os

try:
    from paraview.simple import *
    LoadPlugin("C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/"
               "TopologyToolKit/TopologyToolKit.dll", remote=False, ns=globals())
except Exception as e:
    print(f"Plugin load error: {e}"); sys.exit(1)

B     = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
F     = f"{B}/task0_climate/frames"
MTOUT = f"{B}/outputs/merge_trees"
os.makedirs(MTOUT, exist_ok=True)

pvd_entries = []

for idx in range(76):
    year = 1950 + idx
    vti = f"{F}/task0_t{idx:02d}.vti"
    if not os.path.exists(vti):
        print(f"  SKIP t{idx:02d} {year}: VTI not found"); continue

    reader = XMLImageDataReader(FileName=[vti])
    UpdatePipeline(proxy=reader)

    pre = TTKArrayPreconditioning(Input=reader)
    pre.PointDataArrays = ["CompoundExtremesIndex"]
    UpdatePipeline(proxy=pre)

    try:
        mt = TTKMergeTree(Input=pre)
        mt.ScalarField = ["POINTS", "CompoundExtremesIndex"]
        mt.TreeType    = 2   # contour tree (join + split)
        UpdatePipeline(proxy=mt)
    except Exception as e:
        print(f"  t{idx:02d} {year}: TTKMergeTree FAILED: {e}")
        Delete(pre); Delete(reader); continue

    arc_file = f"{MTOUT}/merge_tree_arcs_t{idx:02d}.vtu"
    try:
        SaveData(arc_file, proxy=mt, ChooseArraysToWrite=0, Port=1)
    except Exception as e:
        print(f"  t{idx:02d} {year}: SaveData failed: {e}")
        Delete(mt); Delete(pre); Delete(reader); continue

    pvd_entries.append((arc_file, float(year)))
    Delete(mt); Delete(pre); Delete(reader)
    print(f"  t{idx:02d} {year}: OK -> {os.path.basename(arc_file)}")

# ── Write PVD ─────────────────────────────────────────────────────────────────
pvd_path = f"{MTOUT}/merge_tree_arcs.pvd"
with open(pvd_path, "w", encoding="ascii") as f:
    f.write('<?xml version="1.0"?>\n')
    f.write('<VTKFile type="Collection" version="0.1">\n')
    f.write('  <Collection>\n')
    for fpath, t in pvd_entries:
        f.write(f'    <DataSet timestep="{t}" file="{fpath}"/>\n')
    f.write('  </Collection>\n')
    f.write('</VTKFile>\n')

print(f"\nWrote {len(pvd_entries)} merge tree arc files.")
print(f"PVD: {pvd_path}")
print("\nTo visualise in viz_task0.py, add:")
print(f"  mt_reader = OpenDataFile('{pvd_path}')")
print("  mt_d = Show(mt_reader, view)")
print("  ColorBy(mt_d, ('CELLS', 'Persistence'))")
print("  GetColorTransferFunction('Persistence').ApplyPreset('Inferno', True)")
