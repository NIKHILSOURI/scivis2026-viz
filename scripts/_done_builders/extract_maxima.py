#!/usr/bin/env python
# STAGE A (pvpython + TTK): per time step, simplify at full res then extract
# maxima (spatial coords + scalar value). Saves an .npz for Stage B matching.
# args: INFILE NSTEPS PERSIST OUTNPZ
import sys, numpy as np
from paraview.simple import *
from paraview import servermanager as sm
from vtk.util.numpy_support import vtk_to_numpy

PLUG = "C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/TopologyToolKit/TopologyToolKit.dll"
LoadPlugin(PLUG, remote=False, ns=globals())

INFILE, NSTEPS, PERSIST, OUTNPZ = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
arrays = [f"field_{i:04d}" for i in range(NSTEPS)]

reader = XMLImageDataReader(FileName=[INFILE]); reader.PointArrayStatus = arrays
reader.UpdatePipeline()
pre = TTKArrayPreconditioning(Input=reader); pre.PointDataArrays = arrays
pre.UpdatePipeline()

per_step = {}
for i, nm in enumerate(arrays):
    simp = TTKTopologicalSimplificationByPersistence(Input=pre)
    simp.InputArray = ["POINTS", nm]; simp.PersistenceThreshold = PERSIST
    cp = TTKScalarFieldCriticalPoints(Input=simp)
    cp.ScalarField = ["POINTS", nm]
    cp.UpdatePipeline()
    d = sm.Fetch(cp)
    pdd = d.GetPointData()
    ct_raw  = pdd.GetArray("CriticalType")
    pts_raw = d.GetPoints()
    if ct_raw is None or pts_raw is None or ct_raw.GetNumberOfTuples() == 0:
        print(f"  t{i:02d} {nm}: 0 points (uniform/bad data — skipped)", flush=True)
        per_step[f"x_{i}"] = np.array([], np.float32)
        per_step[f"y_{i}"] = np.array([], np.float32)
        per_step[f"v_{i}"] = np.array([], np.float32)
        Delete(cp); Delete(simp); continue
    ct  = vtk_to_numpy(ct_raw)
    pts = vtk_to_numpy(pts_raw.GetData())              # world coords (x=lon,y=lat,z)
    # scalar value at each CP (array named like the field, or 'Scalar')
    val = None
    for cand in (nm, "Scalar", "ttkVertexScalarField"):
        a = pdd.GetArray(cand)
        if a is not None:
            val = vtk_to_numpy(a); break
    if len(ct) == 0:
        per_step[f"x_{i}"] = np.array([], np.float32)
        per_step[f"y_{i}"] = np.array([], np.float32)
        per_step[f"v_{i}"] = np.array([], np.float32)
        Delete(cp); Delete(simp); continue
    maxtype = int(ct.max())                             # maxima = highest CriticalType
    m = ct == maxtype
    xs, ys = pts[m, 0], pts[m, 1]
    vs = val[m] if val is not None else np.zeros(m.sum())
    per_step[f"x_{i}"] = xs.astype(np.float32)
    per_step[f"y_{i}"] = ys.astype(np.float32)
    per_step[f"v_{i}"] = np.asarray(vs, np.float32)
    print(f"  t{i:02d} {nm}: {m.sum()} maxima (CriticalType=={maxtype})", flush=True)
    Delete(cp); Delete(simp)

per_step["nsteps"] = np.array([NSTEPS])
np.savez(OUTNPZ, **per_step)
print(f"SUCCESS saved {OUTNPZ}")
