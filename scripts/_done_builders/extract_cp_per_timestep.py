#!/usr/bin/env python
# Extract TTK critical points for each CEI timestep, write per-year VTPs + PVD.
# Run with pvpython: "C:\Program Files\ParaView 6.1.1\bin\pvpython.exe" scripts/_done_builders/extract_cp_per_timestep.py
import sys, os, glob, numpy as np
from paraview.simple import *
from paraview import servermanager as sm
from vtk.util.numpy_support import vtk_to_numpy
import vtk

PLUG = ("C:/Program Files/ParaView 6.1.1/bin/paraview-6.1/plugins/"
        "TopologyToolKit/TopologyToolKit.dll")
LoadPlugin(PLUG, remote=False, ns=globals())

B      = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
FRAMES = f"{B}/task0_climate/frames"
CPDIR  = f"{B}/task0_climate/cp_per_step"
OUTDIR = f"{B}/outputs"
os.makedirs(CPDIR, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

PERSIST = 0.10    # persistence threshold — 0.04 gave too many points; 0.10 keeps only significant features

vti_files = sorted(f for f in os.listdir(FRAMES)
                   if f.startswith("task0_t") and f.endswith(".vti"))
N = len(vti_files)
print(f"Processing {N} timesteps ...")

TYPE_COLOR = {
    0: (0.10, 0.20, 0.90),   # minimum  -> blue
    1: (0.10, 0.75, 0.10),   # saddle   -> green
    2: (0.55, 0.00, 0.80),   # saddle2  -> purple (rare in 2D)
    3: (0.90, 0.10, 0.10),   # maximum  -> red
}
TYPE_NAME = {0: "minimum", 1: "saddle", 2: "saddle2", 3: "maximum"}

cp_files, year_vals = [], []

for idx, fname in enumerate(vti_files):
    fpath = f"{FRAMES}/{fname}"

    reader = XMLImageDataReader(FileName=[fpath])
    reader.UpdatePipeline()

    # TTK requires a triangulated domain — convert regular grid to tetrahedra
    tet = Tetrahedralize(Input=reader)
    tet.UpdatePipeline()

    pre = TTKArrayPreconditioning(Input=tet)
    pre.PointDataArrays = ["CompoundExtremesIndex"]
    pre.UpdatePipeline()

    simp = TTKTopologicalSimplificationByPersistence(Input=pre)
    simp.InputArray            = ["POINTS", "CompoundExtremesIndex"]
    simp.PersistenceThreshold  = PERSIST
    simp.PairType              = 1   # saddle-max pairs (extremes only)
    simp.UpdatePipeline()

    cp = TTKScalarFieldCriticalPoints(Input=simp)
    cp.ScalarField = ["POINTS", "CompoundExtremesIndex"]
    cp.UpdatePipeline()

    raw = sm.Fetch(cp)
    pdd = raw.GetPointData()
    pts = vtk_to_numpy(raw.GetPoints().GetData())   # (x=lon, y=lat, z)
    ct  = vtk_to_numpy(pdd.GetArray("CriticalType"))

    # Find scalar value
    val_arr = None
    for cand in ("CompoundExtremesIndex", "Scalar", "ttkVertexScalarField"):
        a = pdd.GetArray(cand)
        if a is not None:
            val_arr = vtk_to_numpy(a); break
    if val_arr is None:
        val_arr = np.zeros(len(pts), np.float32)

    # Infer year from index (build_task0 uses stride=4 → annual from 1950)
    year = 1950 + idx

    # Skip bad-data timesteps (fill values give uniform fields with no CPs)
    if len(pts) == 0 or ct.max() == ct.min() == 0:
        print(f"  t{idx:02d} {year}: skipped (no critical points extracted)")
        # Write empty VTP so PVD has no gap
        empty = vtk.vtkPolyData()
        empty.SetPoints(vtk.vtkPoints())
        empty.SetVerts(vtk.vtkCellArray())
        out_path = f"{CPDIR}/task0_cp_t{idx:02d}.vtp"
        w = vtk.vtkXMLPolyDataWriter()
        w.SetFileName(out_path); w.SetInputData(empty); w.Write()
        cp_files.append(out_path); year_vals.append(float(year))
        Delete(cp); Delete(simp); Delete(pre); Delete(reader)
        continue

    # Build per-timestep VTP
    vtkPts  = vtk.vtkPoints()
    verts   = vtk.vtkCellArray()
    a_type  = vtk.vtkIntArray();   a_type.SetName("CriticalType")
    a_val   = vtk.vtkFloatArray(); a_val.SetName("CEI_Value")
    a_r     = vtk.vtkFloatArray(); a_r.SetName("ColorR")
    a_g     = vtk.vtkFloatArray(); a_g.SetName("ColorG")
    a_b     = vtk.vtkFloatArray(); a_b.SetName("ColorB")
    a_year  = vtk.vtkIntArray();   a_year.SetName("Year")

    k = 0
    for j in range(len(pts)):
        vtkPts.InsertNextPoint(float(pts[j,0]), float(pts[j,1]), 0.02)
        verts.InsertNextCell(1); verts.InsertCellPoint(k); k += 1
        t   = int(ct[j])
        r,g,b = TYPE_COLOR.get(t, (0.5, 0.5, 0.5))
        a_type.InsertNextValue(t)
        a_val.InsertNextValue(float(val_arr[j]))
        a_r.InsertNextValue(r); a_g.InsertNextValue(g); a_b.InsertNextValue(b)
        a_year.InsertNextValue(year)

    poly = vtk.vtkPolyData()
    poly.SetPoints(vtkPts); poly.SetVerts(verts)
    for arr in (a_type, a_val, a_r, a_g, a_b, a_year):
        poly.GetPointData().AddArray(arr)
    poly.GetPointData().SetActiveScalars("CriticalType")

    out_path = f"{CPDIR}/task0_cp_t{idx:02d}.vtp"
    w = vtk.vtkXMLPolyDataWriter()
    w.SetFileName(out_path); w.SetInputData(poly); w.Write()

    cp_files.append(out_path)
    year_vals.append(float(year))

    n_max = (ct == 3).sum(); n_min = (ct == 0).sum(); n_sad = (ct == 1).sum()
    print(f"  t{idx:02d} {year}: {n_max} maxima, {n_min} minima, {n_sad} saddles")

    Delete(cp); Delete(simp); Delete(pre); Delete(reader)

# Write PVD for per-timestep critical points
def write_pvd(path, files, times):
    lines = ['<?xml version="1.0"?>', '<VTKFile type="Collection" version="0.1">',
             '  <Collection>']
    for t, fn in zip(times, files):
        absp = os.path.abspath(fn).replace("\\", "/")
        lines.append(f'    <DataSet timestep="{t:.4f}" group="" part="0" file="{absp}"/>')
    lines += ['  </Collection>', '</VTKFile>']
    with open(path, "w") as f:
        f.write("\n".join(lines))

pvd_path = f"{CPDIR}/task0_cp.pvd"
write_pvd(pvd_path, cp_files, year_vals)
print(f"\nWrote {pvd_path}  ({N} entries)")
print("Done. Load task0_cp.pvd in viz_task0.py for animated critical points.")
