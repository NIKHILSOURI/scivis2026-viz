#!/usr/bin/env python
# Cross-task: CEI surface (Task 0) + NH jet tube (Task 1) in one scene
# ParaView: View > Python Shell > Run Script (reset first)
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

# view
view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.01, 0.01, 0.04]
view.OrientationAxesVisibility    = 0
try:
    view.UseFXAA = 1
except Exception:
    pass

# CEI surface
field = OpenDataFile(f"{B}/task0_climate/frames/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "CompoundExtremesIndex"))
fd.Opacity = 0.92
clut = GetColorTransferFunction("CompoundExtremesIndex")
clut.RGBPoints = [
    0.20, 0.03, 0.03, 0.10,   # calm      -> near-black blue
    0.40, 0.10, 0.08, 0.25,   # mild      -> dark violet
    0.55, 0.45, 0.10, 0.30,   # elevated  -> maroon
    0.70, 0.85, 0.25, 0.05,   # high      -> orange
    0.85, 1.00, 0.65, 0.10,   # severe    -> amber
    0.95, 1.00, 1.00, 0.75,   # extreme   -> hot white
]
clut.ColorSpace = "Lab"
clut.NanColor   = [0.01, 0.01, 0.04]
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
    gl = Glyph(Input=thr)
    gl.GlyphType        = "Sphere"
    gl.ScaleFactor      = 1.6
    gl.GlyphMode        = "All Points"
    gl.ScaleArray       = ["POINTS", "No scale array"]
    gl.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl)
    gd = Show(gl, view)
    gd.AmbientColor   = [1.00, 0.15, 0.10]
    gd.DiffuseColor   = [1.00, 0.15, 0.10]
    gd.ColorArrayName = ["POINTS", ""]
    gd.Opacity        = 0.95
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
    jlut.RGBPoints = [
        20, 1.00, 0.45, 0.05,   # slow jet  -> orange (danger: blocking)
        45, 0.60, 0.85, 1.00,   # moderate  -> light blue
        70, 0.90, 0.97, 1.00,   # fast      -> icy white
        95, 1.00, 1.00, 1.00,
    ]
    jlut.ColorSpace = "Lab"
    jd.Opacity      = 1.0
    jd.Specular     = 0.6
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

# camera — focus on NH
view.CameraParallelProjection = 1
ResetCamera(view)
cam = GetActiveCamera()
fp = list(cam.GetFocalPoint()); fp[1] = 18.0    # shift view north
cam.SetFocalPoint(fp)
pos = list(cam.GetPosition()); pos[1] = 18.0
cam.SetPosition(pos)
view.CameraParallelScale = view.CameraParallelScale * 0.82

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation range: {scene.StartTime} -> {scene.EndTime} (1950 -> 2025)")

Render(view)
SaveScreenshot(f"{R}/stills/cross_task_hero.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/cross_task_hero.png")
print("Export: File > Save Animation > MP4, 6 fps, 2560x1340")
