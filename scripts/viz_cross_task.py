#!/usr/bin/env python
# Cross-task: CEI surface (Task 0) + NH jet tube (Task 1) in one scene
# ParaView: View > Python Shell > Run Script (reset first)
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
RAYTRACING = False  # set True ONLY when exporting
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

# view
view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.02, 0.02, 0.05]
view.OrientationAxesVisibility    = 0
try:
    view.UseFXAA = 1
except Exception:
    pass

# ── Ray tracing — enabled only when RAYTRACING=True (export mode) ─────────────
if RAYTRACING:
    try:
        view.EnableRayTracing = 1
        for _backend in ("OptiX pathtracer", "OSPRay pathtracer", "OSPRay raycaster"):
            try: view.BackEnd = _backend; break
            except Exception: continue
        view.SamplesPerPixel = 8
        try: view.AmbientSamples = 8
        except Exception: pass
        try: view.LightScale     = 1.5
        except Exception: pass
        try: view.Shadows        = 1
        except Exception: pass
        try: view.Denoise        = 1
        except Exception: pass
        print(f"Ray tracing ON: backend={view.BackEnd}, spp={view.SamplesPerPixel}")
    except Exception as _rte:
        print(f"Ray tracing not available: {_rte}")
else:
    print("Ray tracing OFF (interactive mode) — set RAYTRACING=True before exporting")

# CEI surface
field = OpenDataFile(f"{B}/task0_climate/frames/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "CompoundExtremesIndex"))
fd.Opacity = 0.92
clut = GetColorTransferFunction("CompoundExtremesIndex")
clut.RGBPoints = [
    0.20, 0.25, 0.55, 0.88,   # ocean/calm    -> light blue (same as Task 0 ocean)
    0.45, 0.35, 0.68, 0.70,   # low land      -> blue-green
    0.60, 0.45, 0.82, 0.38,   # typical land  -> green (same as Task 0 mild land)
    0.72, 0.95, 0.88, 0.18,   # elevated      -> yellow
    0.82, 0.95, 0.48, 0.05,   # high          -> orange
    0.90, 0.85, 0.10, 0.05,   # severe        -> red
    0.97, 1.00, 1.00, 1.00,   # extreme       -> white
]
clut.ColorSpace = "Lab"
clut.NanColor   = [0.02, 0.02, 0.05]
fd.SetScalarBarVisibility(view, True)
csb = GetScalarBar(clut, view)
csb.Title = "Compound Extremes Index (surface)"
csb.ComponentTitle = ""
csb.TitleColor = [0.85, 0.85, 0.85]; csb.LabelColor = [0.60, 0.60, 0.60]
try:
    csb.WindowLocation = "Any Location"
except Exception: pass
csb.Position = [0.935, 0.08]; csb.ScalarBarLength = 0.46

# extreme maxima as red spheres
cp_pvd = f"{B}/task0_climate/cp_per_step/task0_cp.pvd"
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
    # same significance filter as viz_task0.py: only CEI hotspots > 0.70
    thr_val = Threshold(Input=thr)
    thr_val.Scalars = ["POINTS", "CEI_Value"]
    try:
        thr_val.LowerThreshold = 0.70; thr_val.UpperThreshold = 1.01
        thr_val.ThresholdMethod = "Between"
    except Exception:
        thr_val.ThresholdRange = [0.70, 1.01]
    UpdatePipeline(proxy=thr_val)
    gl = Glyph(Input=thr_val)
    gl.GlyphType        = "Sphere"
    gl.ScaleFactor      = 1.6
    gl.GlyphMode        = "All Points"
    gl.ScaleArray       = ["POINTS", "No scale array"]
    gl.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl)
    gd = Show(gl, view)
    # deep crimson — same dot color as Task 0 so both views read identically
    gd.AmbientColor   = [0.72, 0.02, 0.10]
    gd.DiffuseColor   = [0.72, 0.02, 0.10]
    gd.ColorArrayName = ["POINTS", ""]
    gd.Opacity        = 1.0
    print("Surface extreme maxima loaded (red spheres, animated)")

# jet core tube
jet_pvd = f"{B}/task1_atmosphere/jet_core/jet_core.pvd"
if os.path.exists(jet_pvd):
    jet = OpenDataFile(jet_pvd)
    UpdatePipeline()
    jtube = Tube(Input=jet)
    jtube.Radius        = 1.4
    jtube.NumberofSides = 12
    UpdatePipeline(proxy=jtube)
    jd = Show(jtube, view)
    ColorBy(jd, ("POINTS", "CoreWindSpeed_ms"))
    jlut = GetColorTransferFunction("CoreWindSpeed_ms")
    # identical anchors to the Task 1 wind maps — same speed = same color everywhere
    jlut.RGBPoints = [
         0, 0.12, 0.28, 0.78,
        12, 0.25, 0.55, 0.88,
        30, 0.45, 0.82, 0.38,
        45, 0.95, 0.88, 0.18,
        60, 0.95, 0.48, 0.05,
        80, 0.85, 0.10, 0.05,
       100, 1.00, 1.00, 1.00,
    ]
    jlut.ColorSpace = "Lab"
    jd.Opacity      = 1.0
    try:
        jd.Interpolation = "PBR"
        jd.Roughness     = 0.20   # smooth metallic tube
        jd.Metallic      = 0.60
    except Exception:
        jd.Specular      = 0.6
    jd.SetScalarBarVisibility(view, True)
    jsb = GetScalarBar(jlut, view)
    jsb.Title = "Jet Core Speed m/s (upper atm)"
    jsb.ComponentTitle = ""
    jsb.TitleColor = [0.85, 0.85, 0.85]; jsb.LabelColor = [0.60, 0.60, 0.60]
    try:
        jsb.WindowLocation = "Any Location"
    except Exception: pass
    jsb.Position = [0.935, 0.62]; jsb.ScalarBarLength = 0.22
    print("Jet core tube loaded (animates every 5 years)")
else:
    print("WARNING: jet_core.pvd missing — run build_jet_core_lines.py first")

# coastlines
G = f"{B}/task1_atmosphere/global"
for vf, c, lw in [(f"{G}/world_coastlines.vtp", [0.55, 0.60, 0.68], 1.3),
                  (f"{G}/world_countries.vtp",  [0.25, 0.30, 0.38], 0.6)]:
    if os.path.exists(vf):
        rd = XMLPolyDataReader(FileName=[vf])
        UpdatePipeline(proxy=rd)
        dd = Show(rd, view)
        dd.AmbientColor = c; dd.DiffuseColor = c
        dd.LineWidth = lw; dd.Opacity = 0.85
        dd.ColorArrayName = ["POINTS", ""]

# year label and title
for _name in ("AnnotateTimeFilter", "AnnotationTimeFilter"):
    _cls = globals().get(_name)
    if _cls is None: continue
    try:
        ann = _cls(Input=field)
        ann.Format = "Year: {time:.0f}"
        ad = Show(ann, view)
        ad.FontSize = 40; ad.Color = [1, 1, 1]
        ad.WindowLocation = "Upper Right Corner"
        break
    except Exception:
        pass
try:
    ttl = Text()
    ttl.Text = ("Upper-level jet meander over surface compound extremes\n"
                "Surface: ACCESS-CM2, 1950-2025  |  Jet: GEOS weather-scale states (illustrative)")
    tdd = Show(ttl, view)
    tdd.FontSize = 22; tdd.Color = [0.92, 0.92, 0.92]
    tdd.WindowLocation = "Upper Left Corner"
except Exception:
    pass

# camera — full globe (jet cores of both hemispheres are shown)
view.CameraParallelProjection = 1
ResetCamera(view)
view.CameraParallelScale = view.CameraParallelScale * 0.95

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation range: {scene.StartTime} -> {scene.EndTime} (1950 -> 2025)")

Render(view)
SaveScreenshot(f"{R}/stills/cross_task_hero.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/cross_task_hero.png")
print("Export: File > Save Animation > MP4, 6 fps, 2560x1340")
