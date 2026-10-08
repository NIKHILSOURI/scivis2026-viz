#!/usr/bin/env python
# Task 0 - DHMI compound extremes field 1950-2025
# ParaView: View > Python Shell > Reset > Run Script
#
# VTI note: task0 data is a flat (1440x600x1) image with Z-extent=0.
# Use "Slice" representation (NOT "Surface") to see the 2D color map.
from paraview.simple import *
import os

B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"

R  = B + "/renders"
F  = B + "/task0_climate/frames"
CP = B + "/task0_climate/cp_per_step"
os.makedirs(R, exist_ok=True)

# ── View setup ────────────────────────────────────────────────────────────────
view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [1920, 1080]
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.96, 0.93, 0.86]
view.OrientationAxesVisibility    = 0
try:
    view.UseFXAA = 1
except Exception:
    pass

# ── Temperature field (VTI flat slab - MUST use Slice representation) ─────────
field = OpenDataFile(F + "/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Slice")   # "Surface" is invisible on Z=0 flat VTI
ColorBy(fd, ("POINTS", "AirTemperature_C"))
fd.Opacity = 1.0

tlut = GetColorTransferFunction("AirTemperature_C")
tlut.RGBPoints = [
    -40, 0.08, 0.08, 0.38,
    -10, 0.12, 0.28, 0.78,
      0, 0.25, 0.55, 0.88,
     15, 0.45, 0.82, 0.38,
     25, 0.95, 0.88, 0.18,
     35, 0.95, 0.48, 0.05,
     45, 0.85, 0.10, 0.05,
     55, 0.55, 0.00, 0.55,
]
tlut.ColorSpace = "Lab"
tlut.NanColor   = [0.96, 0.93, 0.86]

fd.SetScalarBarVisibility(view, True)
tsb = GetScalarBar(tlut, view)
tsb.Title          = "Air Temperature (C)"
tsb.ComponentTitle = ""
tsb.TitleColor     = [0.10, 0.10, 0.10]
tsb.LabelColor     = [0.15, 0.15, 0.15]
try:    tsb.WindowLocation = "Any Location"
except Exception: pass
try:    tsb.Orientation = "Horizontal"
except Exception: pass
tsb.Position          = [0.03, 0.02]
tsb.ScalarBarLength   = 0.30
try:    tsb.ScalarBarThickness = 12
except Exception: pass
try:    tsb.Interactivity = 0
except Exception: pass

# ── CEI contour rings at 0.65 / 0.75 / 0.85 ─────────────────────────────────
ct = Contour(Input=field)
ct.ContourBy   = ["POINTS", "CompoundExtremesIndex"]
ct.Isosurfaces = [0.65, 0.75, 0.85]
UpdatePipeline(proxy=ct)
ctd = Show(ct, view)
ctd.AmbientColor   = [0.10, 0.10, 0.40]
ctd.DiffuseColor   = [0.10, 0.10, 0.40]
ctd.LineWidth      = 1.8
ctd.Opacity        = 0.90
ctd.ColorArrayName = ["POINTS", ""]

# ── Critical points ───────────────────────────────────────────────────────────
cp_pvd = CP + "/task0_cp.pvd"
if os.path.exists(cp_pvd):
    cp_reader = OpenDataFile(cp_pvd)
    UpdatePipeline()

    thr_max = Threshold(Input=cp_reader)
    thr_max.Scalars = ["POINTS", "CriticalType"]
    try:
        thr_max.LowerThreshold = 2.5; thr_max.UpperThreshold = 3.5
        thr_max.ThresholdMethod = "Between"
    except Exception:
        thr_max.ThresholdRange = [2.5, 3.5]
    UpdatePipeline(proxy=thr_max)

    thr_max_val = Threshold(Input=thr_max)
    thr_max_val.Scalars = ["POINTS", "CEI_Value"]
    try:
        thr_max_val.LowerThreshold = 0.80; thr_max_val.UpperThreshold = 1.01
        thr_max_val.ThresholdMethod = "Between"
    except Exception:
        thr_max_val.ThresholdRange = [0.80, 1.01]
    UpdatePipeline(proxy=thr_max_val)

    gl_max = Glyph(Input=thr_max_val)
    gl_max.GlyphType        = "Sphere"
    gl_max.ScaleFactor      = 2.2
    gl_max.GlyphMode        = "All Points"
    gl_max.ScaleArray       = ["POINTS", "No scale array"]
    gl_max.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl_max)
    d_max = Show(gl_max, view)
    d_max.AmbientColor   = [0.72, 0.02, 0.10]
    d_max.DiffuseColor   = [0.72, 0.02, 0.10]
    d_max.ColorArrayName = ["POINTS", ""]
    d_max.Opacity        = 1.0

    thr_min = Threshold(Input=cp_reader)
    thr_min.Scalars = ["POINTS", "CriticalType"]
    try:
        thr_min.LowerThreshold = -0.5; thr_min.UpperThreshold = 0.5
        thr_min.ThresholdMethod = "Between"
    except Exception:
        thr_min.ThresholdRange = [-0.5, 0.5]
    UpdatePipeline(proxy=thr_min)

    gl_min = Glyph(Input=thr_min)
    gl_min.GlyphType        = "Sphere"
    gl_min.ScaleFactor      = 2.2
    gl_min.GlyphMode        = "All Points"
    gl_min.ScaleArray       = ["POINTS", "No scale array"]
    gl_min.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl_min)
    d_min = Show(gl_min, view)
    d_min.AmbientColor   = [0.02, 0.10, 0.85]
    d_min.DiffuseColor   = [0.02, 0.10, 0.85]
    d_min.ColorArrayName = ["POINTS", ""]
    d_min.Opacity        = 1.0
    print("Critical points loaded")
else:
    print("WARNING: task0_cp.pvd not found")

# ── Coastlines ────────────────────────────────────────────────────────────────
G = B + "/task1_atmosphere/global"
for vtp, color, lw in [
    (G + "/world_coastlines.vtp", [0.15, 0.20, 0.30], 1.2),
    (G + "/world_countries.vtp",  [0.32, 0.38, 0.45], 0.7),
]:
    if os.path.exists(vtp):
        rd = XMLPolyDataReader(FileName=[vtp])
        UpdatePipeline(proxy=rd)
        dd = Show(rd, view)
        dd.AmbientColor = color; dd.DiffuseColor = color
        dd.LineWidth = lw; dd.Opacity = 0.80
        dd.ColorArrayName = ["POINTS", ""]
print("Coastlines loaded")

# ── Year annotation ───────────────────────────────────────────────────────────
for _name in ("AnnotateTimeFilter", "AnnotationTimeFilter"):
    _cls = globals().get(_name)
    if _cls is None: continue
    try:
        ann = _cls(Input=field)
        ann.Format = "Year: {time:.0f}"
        ann_d = Show(ann, view)
        ann_d.FontSize = 36
        ann_d.Color = [0.10, 0.10, 0.40]
        ann_d.WindowLocation = "Upper Left Corner"
        print("Year label added via " + _name)
        break
    except Exception as _e:
        print("  " + _name + ": " + str(_e))

# ── Camera ────────────────────────────────────────────────────────────────────
view.CameraParallelProjection = 1
ResetCamera(view)
try:
    _b = field.GetDataInformation().GetBounds()
    _cx, _cy = (_b[0]+_b[1])/2.0, (_b[2]+_b[3])/2.0
    _lon_ext, _lat_ext = _b[1]-_b[0], _b[3]-_b[2]
    _vw, _vh = float(view.ViewSize[0]), float(view.ViewSize[1])
    _ps = max(_lat_ext, _lon_ext / (_vw / _vh)) / 2.0 * 1.02
    cam = GetActiveCamera()
    cam.SetFocalPoint(_cx, _cy, 0); cam.SetPosition(_cx, _cy, 1); cam.SetViewUp(0, 1, 0)
    cam.SetParallelScale(_ps)
except Exception as _e:
    print("Camera auto-fit: " + str(_e))

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print("Timesteps: " + str(len(list(scene.TimeKeeper.TimestepValues))))

Render(view)
os.makedirs(R + "/stills", exist_ok=True)
SaveScreenshot(R + "/stills/task0_clean.png", view, ImageResolution=[1920, 1080])
print("Hero still saved: " + R + "/stills/task0_clean.png")

# ── Export 76 frames ──────────────────────────────────────────────────────────
_pdf_dir = R + "/pdf_stills/task0_frames"
os.makedirs(_pdf_dir, exist_ok=True)
try:
    _ts = list(scene.TimeKeeper.TimestepValues)
except Exception:
    _ts = list(range(1950, 2026))
print("Exporting " + str(len(_ts)) + " frames -> " + _pdf_dir)
for _i, _t in enumerate(_ts):
    scene.AnimationTime = float(_t)
    UpdatePipeline(); Render(view)
    _png = _pdf_dir + "/frame_" + str(_i).zfill(2) + "_t" + str(int(round(_t))) + ".png"
    SaveScreenshot(_png, view, ImageResolution=[1920, 1080])
    if (_i % 10 == 0) or (_i == len(_ts) - 1):
        print("  [" + str(_i+1) + "/" + str(len(_ts)) + "] year " + str(int(round(_t))))
print("Done. Tell Claude to deploy.")
