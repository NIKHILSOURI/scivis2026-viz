#!/usr/bin/env python
# Task 0 - DHMI compound extremes field 1950-2025
# ParaView: View > Python Shell > Reset > Run Script
from paraview.simple import *
import os

B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"

SAVE_ALL_FRAMES = True   # export all 76 years to renders/pdf_stills/task0_frames/
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

print("RAYTRACING OFF - using rasterizer with FXAA")

# ── Temperature background ────────────────────────────────────────────────────
field = OpenDataFile(F + "/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "AirTemperature_C"))
fd.Opacity = 0.85

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

    # Maxima: red spheres, CEI > 0.80
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

    # Minima: blue spheres, all
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

    print("Critical points loaded: red = maxima > 0.80 | blue = minima")
else:
    print("WARNING: task0_cp.pvd not found. Run extract_cp_per_timestep.py first.")

# ── Coastlines and borders ────────────────────────────────────────────────────
G = B + "/task1_atmosphere/global"
for vtp_file, color, lw in [
    (G + "/world_coastlines.vtp", [0.15, 0.20, 0.30], 1.2),
    (G + "/world_countries.vtp",  [0.32, 0.38, 0.45], 0.7),
]:
    if os.path.exists(vtp_file):
        coast = XMLPolyDataReader(FileName=[vtp_file])
        UpdatePipeline(proxy=coast)
        cd = Show(coast, view)
        cd.AmbientColor   = color
        cd.DiffuseColor   = color
        cd.LineWidth      = lw
        cd.Opacity        = 0.80
        cd.ColorArrayName = ["POINTS", ""]
print("Coastlines loaded")

# ── Year label ────────────────────────────────────────────────────────────────
_label_ok = False
for _name in ("AnnotateTimeFilter", "AnnotationTimeFilter"):
    _cls = globals().get(_name)
    if _cls is None:
        continue
    try:
        ann = _cls(Input=field)
        ann.Format = "Year: {time:.0f}"
        ann_d = Show(ann, view)
        ann_d.FontSize       = 36
        ann_d.Color          = [0.10, 0.10, 0.40]
        ann_d.WindowLocation = "Upper Left Corner"
        _label_ok = True
        break
    except Exception as _e:
        print("  " + _name + ": " + str(_e))

if not _label_ok:
    try:
        txt = Text()
        txt.Text = "Year: 1950"
        txt_d = Show(txt, view)
        txt_d.FontSize       = 36
        txt_d.Color          = [0.10, 0.10, 0.40]
        txt_d.WindowLocation = "Upper Left Corner"
        print("Year label: static text")
    except Exception as _e2:
        print("Year label skipped: " + str(_e2))

# ── Camera and animation ──────────────────────────────────────────────────────
view.CameraParallelProjection = 1
ResetCamera(view)

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print("Animation range: " + str(scene.StartTime) + " to " + str(scene.EndTime))

Render(view)
os.makedirs(R + "/stills", exist_ok=True)
SaveScreenshot(R + "/stills/task0_clean.png", view, ImageResolution=[1920, 1080])
print("Hero still saved.")

# ── Export ALL 76 frames ──────────────────────────────────────────────────────
if SAVE_ALL_FRAMES:
    _pdf_dir = R + "/pdf_stills/task0_frames"
    os.makedirs(_pdf_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = list(range(1950, 2026))
    print("Exporting ALL " + str(len(_ts)) + " Task 0 frames -> " + _pdf_dir)
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = float(_t)
        UpdatePipeline()
        Render(view)
        _t_int = int(round(_t))
        _png = _pdf_dir + "/frame_" + str(_i).zfill(2) + "_t" + str(_t_int) + ".png"
        SaveScreenshot(_png, view, ImageResolution=[1920, 1080])
        print("  [" + str(_i+1) + "/" + str(len(_ts)) + "] year " + str(_t_int))
    print("Done. Run deploy_task0_and_3_frames.py to convert to WebP and publish.")
else:
    print("Set SAVE_ALL_FRAMES=True to export all 76 frames.")
    print("Red dots   = CEI maxima > 0.80  (compound extreme hotspots)")
    print("Blue dots  = CEI minima")
    print("White rings= CEI contours at 0.65 / 0.75 / 0.85")
    print("Background = Air temperature | Gray background = paper-ready")
