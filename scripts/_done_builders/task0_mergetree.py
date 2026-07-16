#!/usr/bin/env python
# =====================================================================
# TASK 0 — Merge-tree feature tracking (structural evolution)
# Adapted from TTK example: mergeTreeFeatureTracking.py
# The official example reads a Cinema .cdb; we load two frame .vti files
# directly (simpler, same MergeTree + BlockAggregator + Clustering chain).
# Run in ParaView:  View > Python Shell > Run Script
# =====================================================================
from paraview.simple import *
import os

BASE  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
FIELD = "CompoundExtremesIndex"
FRAME_A = f"{BASE}/task0_climate/frames/task0_t00.vti"   # 1950
FRAME_B = f"{BASE}/task0_climate/frames/task0_t18.vti"   # 2022
RENDERS = f"{BASE}/renders"; os.makedirs(RENDERS, exist_ok=True)


def merge_tree(path):
    r = XMLImageDataReader(FileName=[path])
    r.UpdatePipeline()
    mt = TTKMergeTree(Input=r)
    mt.ScalarField = ["POINTS", FIELD]
    mt.TreeType = "Split Tree"          # Split Tree tracks maxima basins
    mt.UpdatePipeline()
    return mt


mtA = merge_tree(FRAME_A)
mtB = merge_tree(FRAME_B)

# aggregate the 3 output ports (tree nodes / arcs / segmentation) of BOTH trees
agg = TTKBlockAggregator(Input=[
    mtA, OutputPort(mtA, 1), OutputPort(mtA, 2),
    mtB, OutputPort(mtB, 1), OutputPort(mtB, 2),
])
agg.FlattenInput = 0

clust = TTKMergeTreeClustering(Input=agg, OptionalInputclustering=None)
try:
    clust.Deterministic = 1
    clust.DimensionSpacing = 0.5
    clust.DimensionToshift = "Y"
    clust.PersistenceThreshold = 0.02
    clust.ImportantPairs = 20.0
except Exception as e:
    print("param note:", e)
clust.UpdatePipeline()

# ---------------------------------------------------------------------
# Visualize: planar tree layout (port 0) + matching lines (port 2)
# ---------------------------------------------------------------------
view = GetActiveViewOrCreate("RenderView")
view.Background = [0.05, 0.06, 0.09]
view.ViewSize = [1920, 1080]

trees = Show(clust, view)                       # tree layout
trees.SetRepresentationType("Surface")
try:
    ColorBy(trees, ("POINTS", "Persistence"))
except Exception:
    pass

matching = Show(OutputPort(clust, 2), view)     # correspondence lines
matching.SetRepresentationType("Surface")

ResetCamera(view); Render(view)
SaveScreenshot(f"{RENDERS}/task0_mergetree.png", view, ImageResolution=[1920, 1080])
SaveData(f"{BASE}/task0_climate/tracking/task0_matching_1950_2022.vtm",
         OutputPort(clust, 2))
print("Saved render + matching .vtm")
print("Tree layout shows CEI topology of 1950 vs 2022; lines match features that persist.")
