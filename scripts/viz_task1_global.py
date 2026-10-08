#!/usr/bin/env python
# Task 1 â€" global jet-stream visualization, 16 timesteps
# ParaView: View > Python Shell > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
RAYTRACING      = False
SAVE_PDF_STILLS = True
PDF_RESOLUTION  = [3840, 2160]
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)
G = f"{B}/task1_atmosphere/global"

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode = "Single Color"
view.Background = [0.96, 0.93, 0.86]
view.OrientationAxesVisibility = 0
try: view.UseFXAA = 1
except Exception: pass

# â"€â"€ Ray tracing â€" enabled only when RAYTRACING=True (export mode) â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
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
    print("Ray tracing OFF (interactive mode) -- set RAYTRACING=True before exporting")

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
    100, 0.55, 0.00, 0.55,   # extreme    -> deep magenta (visible on cream)
]
lut.ColorSpace = "Lab"
lut.NanColor   = [0.96, 0.93, 0.86]

fd.SetScalarBarVisibility(view, True)
sb = GetScalarBar(lut, view)
sb.Title           = "Wind Speed (m/s)"
sb.ComponentTitle  = ""
sb.TitleColor      = [0.10, 0.10, 0.10]
sb.LabelColor      = [0.15, 0.15, 0.15]
try:
    sb.WindowLocation = "Any Location"
except Exception: pass
sb.Position        = [0.935, 0.22]
sb.ScalarBarLength = 0.55
try: sb.Interactivity = 0
except Exception: pass

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
    38, 0.85, 0.70, 0.00,   # 40 m/s -> dark gold
    40, 0.10, 0.10, 0.40,   # contour edge -> dark navy
    58, 0.75, 0.45, 0.00,   # 60 m/s -> dark amber
    60, 0.10, 0.10, 0.40,   # contour edge -> dark navy
    78, 0.70, 0.10, 0.00,   # 80 m/s -> dark red-orange
    80, 0.10, 0.10, 0.40,   # contour edge -> dark navy
    82, 0.70, 0.10, 0.00,
]
clut.ColorSpace = "RGB"
ctd.LineWidth = 2.5
ctd.Opacity   = 1.0

# coastlines
coast = XMLPolyDataReader(FileName=[f"{G}/world_coastlines.vtp"])
UpdatePipeline(proxy=coast)
coast_d = Show(coast, view)
coast_d.AmbientColor = [0.15, 0.20, 0.30]
coast_d.DiffuseColor = [0.15, 0.20, 0.30]
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

# 2D streamlines â€" wind trajectories
tracer = StreamTracer(Input=pvd, SeedType="Point Cloud")
tracer.Vectors                  = ["POINTS", "Wind_ms"]
tracer.MaximumStreamlineLength  = 120.0   # degrees â€" enough to trace a jet arc
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

# camera — explicit parallel scale to fill 16:9 canvas edge-to-edge
view.CameraParallelProjection = 1
cam = GetActiveCamera()
cam.SetPosition(0, 0, 1)
cam.SetFocalPoint(0, 0, 0)
cam.SetViewUp(0, 1, 0)
cam.SetParallelScale(103)   # ±180 lon × ±90 lat in 16:9 (width-constrained: 360/2/1.778=101)
Render(view)

os.makedirs(f"{R}/stills", exist_ok=True)
SaveScreenshot(f"{R}/stills/task1_global_hero.png", view, ImageResolution=PDF_RESOLUTION)
print("Saved:", f"{R}/stills/task1_global_hero.png")
print()
print("Press Play to animate all 16 timesteps")
print("Export: File > Save Animation > MP4, 3 fps, 1600x900")

if SAVE_PDF_STILLS:
    _pdf_dir = f"{R}/pdf_stills/task1_global"
    os.makedirs(_pdf_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = [scene.StartTime + i*(scene.EndTime-scene.StartTime)/15 for i in range(16)]
    _web_res = [1920, 1080]
    print(f"\nExporting ALL {len(_ts)} global wind frames  ->  {_pdf_dir}")
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = _t; UpdatePipeline()
        cam.SetPosition(0, 0, 1); cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 1, 0); cam.SetParallelScale(103)
        Render(view)
        _png = f"{_pdf_dir}/frame_{_i:02d}_t{_t:.0f}.png"
        SaveScreenshot(_png, view, ImageResolution=_web_res)
        print(f"  [{_i+1}/{len(_ts)}] t={_t:.1f}")
    print("Run  python export_pdf.py  to build the master paper PDF")


