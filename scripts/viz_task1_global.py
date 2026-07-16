#!/usr/bin/env python
# Task 1 — global jet-stream visualization, 16 timesteps
# ParaView: View > Python Shell > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
RAYTRACING = False  # set True ONLY when exporting
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)
G = f"{B}/task1_atmosphere/global"

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode = "Single Color"
view.Background = [0.02, 0.02, 0.05]
view.OrientationAxesVisibility = 0
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

# wind speed field
pvd = OpenDataFile(f"{G}/task1_global.pvd")
UpdatePipeline()
fd = Show(pvd, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "WindSpeed_ms"))

lut = GetColorTransferFunction("WindSpeed_ms")
lut.RGBPoints = [
      0, 0.12, 0.28, 0.78,   # calm       -> blue
     12, 0.25, 0.55, 0.88,   # background -> light blue (same as Task 0 ocean)
     30, 0.45, 0.82, 0.38,   # strong     -> green (same as Task 0 mild land)
     45, 0.95, 0.88, 0.18,   # jet edge   -> yellow
     60, 0.95, 0.48, 0.05,   # jet        -> orange
     80, 0.85, 0.10, 0.05,   # fast jet   -> red
    100, 1.00, 1.00, 1.00,   # extreme    -> white
]
lut.ColorSpace = "Lab"
lut.NanColor   = [0.02, 0.02, 0.05]

fd.SetScalarBarVisibility(view, True)
sb = GetScalarBar(lut, view)
sb.Title           = "Wind Speed (m/s)"
sb.ComponentTitle  = ""
sb.TitleColor      = [0.85, 0.90, 0.95]
sb.LabelColor      = [0.65, 0.72, 0.80]
try:
    sb.WindowLocation = "Any Location"
except Exception: pass
sb.Position        = [0.935, 0.22]
sb.ScalarBarLength = 0.55

# jet contour lines at 40 / 60 / 80 m/s
ct = Contour(Input=pvd)
ct.ContourBy   = ["POINTS", "WindSpeed_ms"]
ct.Isosurfaces = [40.0, 60.0, 80.0]
# rename via Calculator so contours get their own colour table
calc_ct = Calculator(Input=ct)
calc_ct.AttributeType  = "Point Data"
calc_ct.ResultArrayName = "ContourLevel"
calc_ct.Function        = "WindSpeed_ms"
UpdatePipeline(proxy=calc_ct)
ctd = Show(calc_ct, view)
ColorBy(ctd, ("POINTS", "ContourLevel"))
clut = GetColorTransferFunction("ContourLevel")
clut.RGBPoints = [
    38, 1.00, 1.00, 0.70,   # 40 m/s -> pale yellow
    40, 1.00, 1.00, 1.00,
    58, 1.00, 0.92, 0.20,   # 60 m/s -> golden yellow
    60, 1.00, 1.00, 1.00,
    78, 1.00, 0.50, 0.00,   # 80 m/s -> orange
    80, 1.00, 1.00, 1.00,
    82, 1.00, 0.50, 0.00,
]
clut.ColorSpace = "RGB"
ctd.LineWidth = 2.5
ctd.Opacity   = 1.0

# coastlines
coast = XMLPolyDataReader(FileName=[f"{G}/world_coastlines.vtp"])
UpdatePipeline(proxy=coast)
coast_d = Show(coast, view)
coast_d.AmbientColor = [0.55, 0.65, 0.75]
coast_d.DiffuseColor = [0.55, 0.65, 0.75]
coast_d.LineWidth    = 1.3
coast_d.Opacity      = 0.90

# country borders
borders = XMLPolyDataReader(FileName=[f"{G}/world_countries.vtp"])
UpdatePipeline(proxy=borders)
borders_d = Show(borders, view)
borders_d.AmbientColor = [0.28, 0.36, 0.46]
borders_d.DiffuseColor = [0.28, 0.36, 0.46]
borders_d.LineWidth    = 0.8
borders_d.Opacity      = 0.70

# 2D streamlines — wind trajectories
tracer = StreamTracer(Input=pvd, SeedType="Point Cloud")
tracer.Vectors                  = ["POINTS", "Wind_ms"]
tracer.MaximumStreamlineLength  = 120.0   # degrees — enough to trace a jet arc
tracer.IntegrationDirection     = "BOTH"
tracer.IntegratorType           = "Runge-Kutta 4-5"
tracer.MaximumError             = 1e-6
seed = tracer.SeedType
seed.Center           = [0.0, 0.0, 0.0]
seed.Radius           = 165.0            # covers the globe (map extent ~180 deg)
seed.NumberOfPoints   = 600             # enough coverage without clutter
UpdatePipeline(proxy=tracer)

sl_tube = Tube(Input=tracer)
sl_tube.Radius        = 0.18
sl_tube.NumberofSides = 8
UpdatePipeline(proxy=sl_tube)

sl_d = Show(sl_tube, view)
ColorBy(sl_d, ("POINTS", "WindSpeed_ms"))
GetColorTransferFunction("WindSpeed_ms")
sl_d.Opacity = 0.55
sl_d.SetScalarBarVisibility(view, False)   # scalar bar already shown for field

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation range: {scene.StartTime} to {scene.EndTime}")

# camera
view.CameraParallelProjection = 1
ResetCamera(view)
cam = GetActiveCamera()
cam.SetPosition(0, 0, 1)
cam.SetFocalPoint(0, 0, 0)
cam.SetViewUp(0, 1, 0)
ResetCamera(view)
Render(view)

SaveScreenshot(f"{R}/stills/task1_global_hero.png", view, ImageResolution=[2560, 1440])
print("Saved:", f"{R}/task1_global_hero.png")
print()
print("Press Play to animate all 16 timesteps")
print("Export: File > Save Animation > MP4, 3 fps, 1600x900")
