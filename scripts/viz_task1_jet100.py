#!/usr/bin/env python
# Task 1 — 100-frame jet stream dynamics (zonal wind at jet level)
# ParaView: Python Shell > Reset > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
RAYTRACING = False  # set True ONLY when exporting
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.02, 0.02, 0.05]
view.OrientationAxesVisibility    = 0
try: view.UseFXAA = 1
except Exception: pass

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

jet = OpenDataFile(f"{B}/task1_atmosphere/jet100/jet100.pvd")
UpdatePipeline()

jd = Show(jet, view)
jd.SetRepresentationType("Surface")
ColorBy(jd, ("POINTS", "ZonalSpeed_ms"))
lut = GetColorTransferFunction("ZonalSpeed_ms")
lut.RGBPoints = [
      0, 0.12, 0.28, 0.78,   # calm       -> blue
     12, 0.25, 0.55, 0.88,   # background -> light blue (same as Task 0 ocean)
     30, 0.45, 0.82, 0.38,   # strong     -> green
     45, 0.95, 0.88, 0.18,   # jet edge   -> yellow
     60, 0.95, 0.48, 0.05,   # jet        -> orange
     80, 0.85, 0.10, 0.05,   # fast jet   -> red
    100, 1.00, 1.00, 1.00,   # extreme    -> white
]
lut.ColorSpace = "Lab"
jd.SetScalarBarVisibility(view, True)
sb = GetScalarBar(lut, view)
sb.Title = "Zonal Wind Speed (m/s), jet level"
sb.ComponentTitle = ""
sb.TitleColor = [0.85, 0.85, 0.85]; sb.LabelColor = [0.62, 0.62, 0.62]
try:
    sb.WindowLocation = "Any Location"
except Exception: pass
sb.Position = [0.935, 0.22]; sb.ScalarBarLength = 0.55

# jet core contours
ct = Contour(Input=jet)
ct.ContourBy   = ["POINTS", "ZonalSpeed_ms"]
ct.Isosurfaces = [40.0, 60.0, 80.0]
UpdatePipeline(proxy=ct)
cd = Show(ct, view)
cd.AmbientColor = [1, 1, 1]; cd.DiffuseColor = [1, 1, 1]
cd.LineWidth = 1.4; cd.Opacity = 0.8
cd.ColorArrayName = ["POINTS", ""]

# coastlines
coast = f"{B}/task1_atmosphere/global/world_coastlines.vtp"
if os.path.exists(coast):
    rd = XMLPolyDataReader(FileName=[coast]); UpdatePipeline(proxy=rd)
    dd = Show(rd, view)
    dd.AmbientColor = [0.55, 0.60, 0.68]; dd.DiffuseColor = [0.55, 0.60, 0.68]
    dd.LineWidth = 1.1; dd.Opacity = 0.8
    dd.ColorArrayName = ["POINTS", ""]

try:
    ttl = Text()
    ttl.Text = ("Jet Stream, 100 six-hourly GEOS snapshots (DYAMOND)\n"
                "Watch the jet meander, split and reform: weather-scale dynamics")
    tdd = Show(ttl, view)
    tdd.FontSize = 22; tdd.Color = [0.93, 0.93, 0.93]
    tdd.WindowLocation = "Upper Left Corner"
except Exception: pass

view.CameraParallelProjection = 1
ResetCamera(view)
# focus on NH
cam = GetActiveCamera()
fp = list(cam.GetFocalPoint()); fp[1] = 25.0; cam.SetFocalPoint(fp)
pos = list(cam.GetPosition()); pos[1] = 25.0; cam.SetPosition(pos)
view.CameraParallelScale = view.CameraParallelScale * 0.72

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
Render(view)
SaveScreenshot(f"{R}/stills/task1_jet100.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/task1_jet100.png")
print("Press Play: 100 frames. Export: MP4, 10 fps -> task1_jet100.mp4 (10 s clip)")
