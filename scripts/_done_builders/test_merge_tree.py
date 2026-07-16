#!/usr/bin/env python
"""
test_merge_tree.py  — run in pvpython to test TTKMergeTree
Tests whether TTKMergeTree works on a single Task 0 CEI frame (it's a per-timestep
filter, not a tracking filter, so it should NOT crash like TTKTrackingFromFields did).

If it works: the tree structure shows which high-CEI regions merge as you raise the
threshold — a richer representation than just isolated maxima.

Usage:  pvpython scripts/test_merge_tree.py
Output: outputs/merge_tree_t50.vtu  (the merge tree for year 2000, t=50)
        outputs/merge_tree_t50_arcs.vtu
"""
import sys, os

# Load TTK plugin
try:
    from paraview.simple import *
    LoadPlugin("C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/"
               "TopologyToolKit/TopologyToolKit.dll", remote=False, ns=globals())
except Exception as e:
    print(f"Plugin load error: {e}")
    sys.exit(1)

B       = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
FRAMES  = f"{B}/task0_climate/frames"
OUT     = f"{B}/outputs"
os.makedirs(OUT, exist_ok=True)

# Use year 2000 (t=50) as test — interesting because it's in the "recent" high-event period
T_TEST  = 50
VTI     = f"{FRAMES}/task0_t{T_TEST:02d}.vti"

if not os.path.exists(VTI):
    # Try PVD-based loading instead
    pvd = f"{FRAMES}/task0.pvd"
    if not os.path.exists(pvd):
        print(f"ERROR: Neither {VTI} nor {pvd} found.")
        sys.exit(1)
    reader = OpenDataFile(pvd)
    animScene = GetAnimationScene()
    animScene.UpdateAnimationUsingDataTimeSteps()
    animScene.AnimationTime = T_TEST
    UpdatePipeline(proxy=reader)
    src = reader
else:
    src = XMLImageDataReader(FileName=[VTI])
    UpdatePipeline(proxy=src)

print("Source loaded. Applying TTKArrayPreconditioning ...")
pre = TTKArrayPreconditioning(Input=src)
pre.PointDataArrays = ["CompoundExtremesIndex"]
UpdatePipeline(proxy=pre)
print("  Preconditioning done.")

# ── Merge tree ────────────────────────────────────────────────────────────────
print("Applying TTKMergeTree ...")
try:
    mt = TTKMergeTree(Input=pre)
    mt.ScalarField    = ["POINTS", "CompoundExtremesIndex"]
    mt.TreeType       = 2   # 0=join, 1=split, 2=contour (join+split)
    UpdatePipeline(proxy=mt)
    print("  TTKMergeTree: SUCCESS")
    n_blocks = mt.GetDataInformation().GetNumberOfDataSets() if hasattr(
        mt.GetDataInformation(), 'GetNumberOfDataSets') else 1
    print(f"  Output blocks: {n_blocks}")

    # Write outputs
    for port_idx, name in enumerate(["merge_tree_nodes", "merge_tree_arcs",
                                      "merge_tree_seg"]):
        try:
            sel = GetOutputPort(mt, port_idx) if hasattr(GetOutputPort, '__call__') else mt
            w = servermanager.writers.XMLUnstructuredGridWriter(
                FileName=f"{OUT}/{name}_t{T_TEST:02d}.vtu",
                Input=mt, Port=port_idx)
            w.UpdatePipeline()
            print(f"  Wrote: {OUT}/{name}_t{T_TEST:02d}.vtu")
        except Exception as e2:
            # Fallback: SaveData for each output port
            try:
                SaveData(f"{OUT}/{name}_t{T_TEST:02d}.vtu", proxy=mt,
                         ChooseArraysToWrite=0, Port=port_idx)
                print(f"  Wrote (via SaveData): {OUT}/{name}_t{T_TEST:02d}.vtu")
            except Exception as e3:
                print(f"  Could not write port {port_idx}: {e3}")

except Exception as e:
    print(f"  TTKMergeTree FAILED: {e}")
    import traceback; traceback.print_exc()
    print("\n  -> Will NOT use merge tree in the visualization.")
    sys.exit(2)

# ── If success, print what to do next ────────────────────────────────────────
print()
print("TTKMergeTree works! Next steps:")
print("  1. Run build_merge_trees.py to compute all 76 frames -> PVD")
print("  2. Add merge tree arcs to viz_task0.py:")
print("     mt_reader = OpenDataFile('<OUT>/merge_trees/merge_tree_arcs.pvd')")
print("     mt_d = Show(mt_reader, view)")
print("     ColorBy(mt_d, ('POINTS', 'Persistence'))")
