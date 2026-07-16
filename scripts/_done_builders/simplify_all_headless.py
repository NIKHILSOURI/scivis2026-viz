#!/usr/bin/env python
# Headless: simplify EVERY time-step array at full res (professor's step 1),
# write a new *_simplified.vti with all simplified arrays.
# args: INFILE NSTEPS PERSIST OUTFILE
import sys, os
import numpy as np
from paraview.simple import *
from paraview import servermanager as sm
from vtk.util.numpy_support import vtk_to_numpy

sys.path.insert(0, "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New")
from _vtizlib import write_tracking_vti

PLUG = "C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/TopologyToolKit/TopologyToolKit.dll"
LoadPlugin(PLUG, remote=False, ns=globals())

INFILE, NSTEPS, PERSIST, OUTFILE = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
arrays = [f"field_{i:04d}" for i in range(NSTEPS)]

reader = XMLImageDataReader(FileName=[INFILE])
reader.PointArrayStatus = arrays
reader.UpdatePipeline()
img = sm.Fetch(reader)
nx, ny, _ = img.GetDimensions()
org = img.GetOrigin(); spc = img.GetSpacing()

pre = TTKArrayPreconditioning(Input=reader)
pre.PointDataArrays = arrays
pre.UpdatePipeline()

simplified = []
for i, nm in enumerate(arrays):
    s = TTKTopologicalSimplificationByPersistence(Input=pre)
    s.InputArray = ["POINTS", nm]
    s.PersistenceThreshold = PERSIST
    s.UpdatePipeline()
    d = sm.Fetch(s)
    a = vtk_to_numpy(d.GetPointData().GetArray(nm)).reshape(ny, nx)
    simplified.append(a.astype(np.float32))
    Delete(s)
    print(f"  simplified {nm}", flush=True)

write_tracking_vti(OUTFILE, simplified, nx, ny,
                   origin=(org[0], org[1]), spacing=(spc[0], spc[1]), prefix="field")
print(f"SUCCESS wrote {OUTFILE}  ({nx}x{ny}, {NSTEPS} arrays)")
