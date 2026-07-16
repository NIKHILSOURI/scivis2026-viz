#!/usr/bin/env python
# =====================================================================
# TASK 1 — Merge-tree tracking of jet / storm structure (wind speed)
# Adapted from TTK example: mergeTreeFeatureTracking.py
# Run in ParaView:  View > Python Shell > Run Script
# =====================================================================
from paraview.simple import *
import os

BASE  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
FIELD = "WindSpeed_ms"
FRAME_A = f"{BASE}/task1_atmosphere/frames/task1_t00.vti"
FRAME_B = f"{BASE}/task1_atmosphere/frames/task1_t08.vti"
RENDERS = f"{BASE}/renders"; os.makedirs(RENDERS, exist_ok=True)


def merge_tree(path):
    r = XMLImageDataReader(FileName=[path]); r.UpdatePipeline()
    mt = TTKMergeTree(Input=r)
    mt.ScalarField = ["POINTS", FIELD]
    mt.TreeType = "Join Tree"           # Join Tree tracks maxima (jet cores)
    mt.UpdatePipeline()
    return mt


mtA, mtB = merge_tree(FRAME_A), merge_tree(FRAME_B)
agg = TTKBlockAggregator(Input=[
    mtA, OutputPort(mtA, 1), OutputPort(mtA, 2),
    mtB, OutputPort(mtB, 1), OutputPort(mtB, 2)])
agg.FlattenInput = 0

clust = TTKMergeTreeClustering(Input=agg, OptionalInputclustering=None)
try:
    clust.Deterministic = 1
    clust.DimensionSpacing = 0.5
    clust.DimensionToshift = "Y"
    clust.PersistenceThreshold = 2.0
    clust.ImportantPairs = 20.0
except Exception as e:
    print("param note:", e)
clust.UpdatePipeline()

view = GetActiveViewOrCreate("RenderView")
view.Background = [0.05, 0.06, 0.09]; view.ViewSize = [1920, 1080]
Show(clust, view)
Show(OutputPort(clust, 2), view)
ResetCamera(view); Render(view)
SaveScreenshot(f"{RENDERS}/task1_mergetree.png", view, ImageResolution=[1920, 1080])
print("Saved task1_mergetree.png — wind-speed topology evolution between two steps.")
