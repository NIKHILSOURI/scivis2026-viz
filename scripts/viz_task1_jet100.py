#!/usr/bin/env python
# Task 1 â€" 100-frame jet stream dynamics (zonal wind at jet level)
# ParaView: Python Shell > Reset > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
RAYTRACING      = False
SAVE_PDF_STILLS = True
PDF_RESOLUTION  = [3840, 2160]
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.96, 0.93, 0.86]
view.OrientationAxesVisibility    = 0
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
    100, 0.55, 0.00, 0.55,   # extreme    -> deep magenta (visible on cream)
]
lut.ColorSpace = "Lab"
jd.SetScalarBarVisibility(view, True)
sb = GetScalarBar(lut, view)
sb.Title = "Zonal Wind Speed (m/s), jet level"
sb.ComponentTitle = ""
sb.TitleColor = [0.10, 0.10, 0.10]; sb.LabelColor = [0.15, 0.15, 0.15]
try: sb.WindowLocation = "Any Location"
except Exception: pass
try: sb.Orientation = "Horizontal"
except Exception: pass
sb.Position = [0.03, 0.02]; sb.ScalarBarLength = 0.35
try: sb.ScalarBarThickness = 14; sb.Interactivity = 0
except Exception: pass
# jet core contours
ct = Contour(Input=jet)
ct.ContourBy   = ["POINTS", "ZonalSpeed_ms"]
ct.Isosurfaces = [40.0, 60.0, 80.0]
UpdatePipeline(proxy=ct)
cd = Show(ct, view)
cd.AmbientColor = [0.10, 0.10, 0.40]; cd.DiffuseColor = [0.10, 0.10, 0.40]
cd.LineWidth = 1.8; cd.Opacity = 0.9
cd.ColorArrayName = ["POINTS", ""]

# coastlines
coast = f"{B}/task1_atmosphere/global/world_coastlines.vtp"
if os.path.exists(coast):
    rd = XMLPolyDataReader(FileName=[coast]); UpdatePipeline(proxy=rd)
    dd = Show(rd, view)
    dd.AmbientColor = [0.15, 0.20, 0.30]; dd.DiffuseColor = [0.15, 0.20, 0.30]
    dd.LineWidth = 1.1; dd.Opacity = 0.8
    dd.ColorArrayName = ["POINTS", ""]


view.CameraParallelProjection = 1
cam = GetActiveCamera()
cam.SetPosition(0, 0, 1)
cam.SetFocalPoint(0, 0, 0)
cam.SetViewUp(0, 1, 0)
cam.SetParallelScale(103)   # ±180 lon × ±90 lat in 16:9 (width-constrained: 360/2/1.778=101)

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
Render(view)
os.makedirs(f"{R}/stills", exist_ok=True)
SaveScreenshot(f"{R}/stills/task1_jet100.png", view, ImageResolution=PDF_RESOLUTION)
print(f"Saved: {R}/stills/task1_jet100.png")
print("Press Play: 100 frames. Export: MP4, 10 fps -> task1_jet100.mp4 (10 s clip)")

if SAVE_PDF_STILLS:
    _pdf_dir = f"{R}/pdf_stills/task1_jet100"
    os.makedirs(_pdf_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = list(range(100))
    _web_res = [1920, 1080]
    print(f"\nExporting ALL {len(_ts)} jet100 frames  ->  {_pdf_dir}")
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = _t; UpdatePipeline()
        cam.SetPosition(0, 0, 1); cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 1, 0); cam.SetParallelScale(103)
        Render(view)
        _png = f"{_pdf_dir}/frame_{_i:02d}_t{_t:.0f}.png"
        SaveScreenshot(_png, view, ImageResolution=_web_res)
        print(f"  [{_i+1}/{len(_ts)}] t={_t:.1f}")
    print("Run  python export_pdf.py  to build the master paper PDF")


