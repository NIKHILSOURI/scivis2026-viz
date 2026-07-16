#!/usr/bin/env python
"""
fix_t62_frame.py — repair the corrupt 2012 frame (t62).

ACCESS-CM2 fill values made t62 uniform (-273 C, CEI=0.40): the animation
visibly flashes for one year. Replace every point array in task0_t62.vti with
the average of t61 (2011) and t63 (2013).

A backup of the original is kept as task0_t62.vti.bad.

Run: python scripts/fix_t62_frame.py
"""
import os, shutil, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

F = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New/task0_climate/frames"

def read_vti(path):
    r = vtk.vtkXMLImageDataReader(); r.SetFileName(path); r.Update()
    return r.GetOutput()

t61 = read_vti(f"{F}/task0_t61.vti")
t63 = read_vti(f"{F}/task0_t63.vti")
t62_path = f"{F}/task0_t62.vti"

# backup once
bak = f"{t62_path}.bad"
if not os.path.exists(bak):
    shutil.copy2(t62_path, bak)
    print(f"Backup: {bak}")

out = vtk.vtkImageData()
out.DeepCopy(t61)                     # geometry + arrays from t61

pd61, pd63 = t61.GetPointData(), t63.GetPointData()
for i in range(pd61.GetNumberOfArrays()):
    name = pd61.GetArrayName(i)
    a61  = vtk_to_numpy(pd61.GetArray(name)).astype(np.float64)
    a63v = pd63.GetArray(name)
    if a63v is None:
        print(f"  {name}: missing in t63, kept t61 copy"); continue
    a63  = vtk_to_numpy(a63v).astype(np.float64)
    avg  = ((a61 + a63) / 2.0).astype(np.float32)
    varr = numpy_to_vtk(avg, deep=1); varr.SetName(name)
    out.GetPointData().RemoveArray(name)
    out.GetPointData().AddArray(varr)
    print(f"  {name}: interpolated  range [{avg.min():.2f}, {avg.max():.2f}]")

# preserve/repair the TimeValue field array (2012)
fdata = out.GetFieldData()
tv = fdata.GetArray("TimeValue")
if tv is not None:
    tv.SetTuple1(0, 2012.0)
    print("  TimeValue field set to 2012")

w = vtk.vtkXMLImageDataWriter()
w.SetFileName(t62_path); w.SetInputData(out); w.Write()
print(f"\nRepaired: {t62_path}  (2012 = average of 2011 and 2013)")
print("NOTE: analysis CSVs already skip t62; this fix is for animation smoothness.")
