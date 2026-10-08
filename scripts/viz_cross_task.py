#!/usr/bin/env python
# Task 3 - Ocean-Atmosphere: CEI surface + jet core tube
# ParaView: View > Python Shell > Reset > Run Script
#
# VTI note: task0 data is a flat (1440x600x1) image with Z-extent=0.
# Use "Slice" representation (NOT "Surface") to see the 2D color map.
from paraview.simple import *
import os

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"

SAVE_ALL_FRAMES = True
SAVE_KEY_STILLS = True
R = B + "/renders"
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

# ── DHMI / CEI surface (VTI flat slab - MUST use Slice representation) ────────
field = OpenDataFile(B + "/task0_climate/frames/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Slice")   # "Surface" is invisible on Z=0 flat VTI
ColorBy(fd, ("POINTS", "CompoundExtremesIndex"))
fd.Opacity = 1.0

clut = GetColorTransferFunction("CompoundExtremesIndex")
clut.RGBPoints = [
    0.20, 0.25, 0.55, 0.88,
    0.45, 0.35, 0.68, 0.70,
    0.60, 0.45, 0.82, 0.38,
    0.72, 0.95, 0.88, 0.18,
    0.82, 0.95, 0.48, 0.05,
    0.90, 0.85, 0.10, 0.05,
    0.97, 0.55, 0.00, 0.55,
]
clut.ColorSpace = "Lab"
clut.NanColor   = [0.96, 0.93, 0.86]

fd.SetScalarBarVisibility(view, True)
csb = GetScalarBar(clut, view)
csb.Title          = "DHMI (Wu et al. 2019)"
csb.ComponentTitle = ""
csb.TitleColor     = [0.10, 0.10, 0.10]
csb.LabelColor     = [0.15, 0.15, 0.15]
try:    csb.WindowLocation = "Any Location"
except Exception: pass
try:    csb.Orientation = "Horizontal"
except Exception: pass
csb.Position          = [0.03, 0.02]
csb.ScalarBarLength   = 0.30
try:    csb.ScalarBarThickness = 12
except Exception: pass
try:    csb.Interactivity = 0
except Exception: pass

# ── CEI extreme maxima (red spheres) ─────────────────────────────────────────
cp_pvd = B + "/task0_climate/cp_per_step/task0_cp.pvd"
if os.path.exists(cp_pvd):
    cp = OpenDataFile(cp_pvd)
    UpdatePipeline()
    thr = Threshold(Input=cp)
    thr.Scalars = ["POINTS", "CriticalType"]
    try:
        thr.LowerThreshold = 3; thr.UpperThreshold = 3
        thr.ThresholdMethod = "Between"
    except Exception:
        thr.ThresholdRange = [3, 3]
    UpdatePipeline(proxy=thr)

    thr_val = Threshold(Input=thr)
    thr_val.Scalars = ["POINTS", "CEI_Value"]
    try:
        thr_val.LowerThreshold = 0.80; thr_val.UpperThreshold = 1.01
        thr_val.ThresholdMethod = "Between"
    except Exception:
        thr_val.ThresholdRange = [0.80, 1.01]
    UpdatePipeline(proxy=thr_val)

    gl = Glyph(Input=thr_val)
    gl.GlyphType        = "Sphere"
    gl.ScaleFactor      = 1.8
    gl.GlyphMode        = "All Points"
    gl.ScaleArray       = ["POINTS", "No scale array"]
    gl.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl)
    gd = Show(gl, view)
    gd.AmbientColor   = [0.72, 0.02, 0.10]
    gd.DiffuseColor   = [0.72, 0.02, 0.10]
    gd.ColorArrayName = ["POINTS", ""]
    gd.Opacity        = 1.0
    print("Critical points loaded")
else:
    print("NOTE: task0_cp.pvd not found - no critical points overlay")

# ── Jet core tube (optional) ──────────────────────────────────────────────────
jet_pvd = B + "/task1_atmosphere/jet_core/jet_core.pvd"
if os.path.exists(jet_pvd):
    jet = OpenDataFile(jet_pvd)
    UpdatePipeline()
    jtube = Tube(Input=jet)
    jtube.Radius        = 1.4
    jtube.NumberofSides = 12
    UpdatePipeline(proxy=jtube)
    jd = Show(jtube, view)
    ColorBy(jd, ("POINTS", "CoreWindSpeed_ms"))
    jd.Opacity = 1.0

    jlut = GetColorTransferFunction("CoreWindSpeed_ms")
    jlut.RGBPoints = [
         0, 0.12, 0.28, 0.78,
        12, 0.25, 0.55, 0.88,
        30, 0.45, 0.82, 0.38,
        45, 0.95, 0.88, 0.18,
        60, 0.95, 0.48, 0.05,
        80, 0.85, 0.10, 0.05,
       100, 0.55, 0.00, 0.55,
    ]
    jlut.ColorSpace = "Lab"

    jd.SetScalarBarVisibility(view, True)
    jsb = GetScalarBar(jlut, view)
    jsb.Title          = "Jet Core Speed m/s (upper atm)"
    jsb.ComponentTitle = ""
    jsb.TitleColor     = [0.10, 0.10, 0.10]
    jsb.LabelColor     = [0.15, 0.15, 0.15]
    try:    jsb.WindowLocation = "Any Location"
    except Exception: pass
    try:    jsb.Orientation = "Horizontal"
    except Exception: pass
    jsb.Position        = [0.65, 0.02]
    jsb.ScalarBarLength = 0.22
    try:    jsb.ScalarBarThickness = 12
    except Exception: pass
    try:    jsb.Interactivity = 0
    except Exception: pass
    print("Jet core tube loaded")
else:
    print("NOTE: jet_core.pvd not found - DHMI field only")

# ── Coastlines ────────────────────────────────────────────────────────────────
G = B + "/task1_atmosphere/global"
for vf, c, lw in [
    (G + "/world_coastlines.vtp", [0.15, 0.20, 0.30], 1.3),
    (G + "/world_countries.vtp",  [0.25, 0.30, 0.38], 0.6),
]:
    if os.path.exists(vf):
        rd = XMLPolyDataReader(FileName=[vf])
        UpdatePipeline(proxy=rd)
        dd = Show(rd, view)
        dd.AmbientColor = c; dd.DiffuseColor = c
        dd.LineWidth = lw; dd.Opacity = 0.85
        dd.ColorArrayName = ["POINTS", ""]

# ── Year annotation ───────────────────────────────────────────────────────────
for _name in ("AnnotateTimeFilter", "AnnotationTimeFilter"):
    _cls = globals().get(_name)
    if _cls is None: continue
    try:
        ann = _cls(Input=field)
        ann.Format = "Year: {time:.0f}"
        ad = Show(ann, view)
        ad.FontSize = 40; ad.Color = [0.10, 0.10, 0.10]
        ad.WindowLocation = "Upper Right Corner"
        print("Year label added via " + _name)
        break
    except Exception:
        pass

# ── Camera ────────────────────────────────────────────────────────────────────
view.CameraParallelProjection = 1
ResetCamera(view)
view.CameraParallelScale = view.CameraParallelScale * 0.95

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print("Timesteps: " + str(len(list(scene.TimeKeeper.TimestepValues))))

Render(view)
os.makedirs(R + "/stills", exist_ok=True)
SaveScreenshot(R + "/stills/cross_task_hero.png", view, ImageResolution=[1920, 1080])
print("Hero still saved.")

# ── Export 5 key-year stills ──────────────────────────────────────────────────
if SAVE_KEY_STILLS:
    _pdf_dir = R + "/pdf_stills/cross_task"
    os.makedirs(_pdf_dir, exist_ok=True)
    for _i, _t in enumerate([1950, 1969, 1988, 2006, 2025]):
        scene.AnimationTime = float(_t)
        UpdatePipeline(); Render(view)
        _png = _pdf_dir + "/frame_" + str(_i).zfill(2) + "_yr" + str(_t) + ".png"
        SaveScreenshot(_png, view, ImageResolution=[1920, 1080])
        print("  key year " + str(_t))

# ── Export ALL 76 frames ──────────────────────────────────────────────────────
if SAVE_ALL_FRAMES:
    _all_dir = R + "/pdf_stills/task3_frames"
    os.makedirs(_all_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = list(range(1950, 2026))
    print("Exporting " + str(len(_ts)) + " frames -> " + _all_dir)
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = float(_t)
        UpdatePipeline(); Render(view)
        _t_int = int(round(_t))
        _png = _all_dir + "/frame_" + str(_i).zfill(2) + "_t" + str(_t_int) + ".png"
        SaveScreenshot(_png, view, ImageResolution=[1920, 1080])
        if (_i % 10 == 0) or (_i == len(_ts) - 1):
            print("  [" + str(_i+1) + "/" + str(len(_ts)) + "] year " + str(_t_int))
    print("Done. Run deploy_task0_and_3_frames.py to convert to WebP.")
