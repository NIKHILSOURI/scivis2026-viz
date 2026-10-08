#!/usr/bin/env python
# Task 1 â€" 3D layered atmosphere: 5 altitude shelves, self-lit
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

Z_STEP = 40.0
LAYERS = [   # (z, min speed shown, label)
    (0.0,        None, "SURFACE  (calm, <25 m/s)"),
    (1 * Z_STEP, 16.0, "LOWER TROPOSPHERE"),
    (2 * Z_STEP, 24.0, "MID TROPOSPHERE"),
    (3 * Z_STEP, 34.0, "UPPER TROPOSPHERE"),
    (4 * Z_STEP, 45.0, "JET LEVEL  (up to ~110 m/s)"),
]

view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]
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
    print("Ray tracing OFF (interactive mode) â€" set RAYTRACING=True before exporting")

vol = OpenDataFile(f"{B}/task1_atmosphere/global3d/task1_3d.pvd")
UpdatePipeline()

# colour scale for upper shelves â€" same theme as task1_global (max 110 m/s here)
jlut = GetColorTransferFunction("WindSpeed_ms")
jlut.RGBPoints = [
      0, 0.12, 0.28, 0.78,   # calm       -> blue
     12, 0.25, 0.55, 0.88,   # background -> light blue (same as Task 0 ocean)
     30, 0.45, 0.82, 0.38,   # strong     -> green
     45, 0.95, 0.88, 0.18,   # jet edge   -> yellow
     60, 0.95, 0.48, 0.05,   # jet        -> orange
     80, 0.85, 0.10, 0.05,   # fast jet   -> red
    100, 0.55, 0.00, 0.55,   # extreme    -> white
]
jlut.ColorSpace = "Lab"

# surface layer â€" separate 0-25 m/s colour scale so it doesn't go black
surf_slice = Slice(Input=vol)
surf_slice.SliceType = "Plane"
surf_slice.SliceType.Origin = [0.0, 0.0, 0.0]
surf_slice.SliceType.Normal = [0.0, 0.0, 1.0]
calc = Calculator(Input=surf_slice)
calc.AttributeType   = "Point Data"
calc.ResultArrayName = "SurfaceWind_ms"
calc.Function        = "WindSpeed_ms"
UpdatePipeline(proxy=calc)
sd = Show(calc, view)
ColorBy(sd, ("POINTS", "SurfaceWind_ms"))
slut = GetColorTransferFunction("SurfaceWind_ms")
slut.RGBPoints = [
     0, 0.12, 0.28, 0.78,   # calm       -> blue
     5, 0.25, 0.55, 0.88,   # background -> light blue (same as Task 0 ocean)
    11, 0.45, 0.82, 0.38,   #            -> green
    16, 0.95, 0.88, 0.18,   #            -> yellow
    20, 0.95, 0.48, 0.05,   #            -> orange
    25, 0.85, 0.10, 0.05,   # strongest  -> red (no white: 25 m/s is not extreme)
]
slut.ColorSpace = "Lab"
sd.Opacity = 1.0
sd.Ambient = 1.0; sd.Diffuse = 0.0            # self-lit: full brightness
RenameSource("L0_SURFACE", calc)

# upper shelves â€" threshold out the calm air at each level
last = None
for k, (z, min_spd, label) in enumerate(LAYERS[1:], start=1):
    sl = Slice(Input=vol)
    sl.SliceType = "Plane"
    sl.SliceType.Origin = [0.0, 0.0, z]
    sl.SliceType.Normal = [0.0, 0.0, 1.0]
    thr = Threshold(Input=sl)
    thr.Scalars = ["POINTS", "WindSpeed_ms"]
    try:
        thr.LowerThreshold = min_spd; thr.UpperThreshold = 500.0
        thr.ThresholdMethod = "Between"
    except Exception:
        thr.ThresholdRange = [min_spd, 500.0]
    UpdatePipeline(proxy=thr)
    d = Show(thr, view)
    ColorBy(d, ("POINTS", "WindSpeed_ms"))
    d.Opacity = 0.95
    d.Ambient = 1.0; d.Diffuse = 0.0          # self-lit
    RenameSource(f"L{k}_{label.split('  ')[0].replace(' ', '_')}", thr)
    last = d

last.SetScalarBarVisibility(view, True)
jsb = GetScalarBar(jlut, view)
jsb.Title = "Wind Speed aloft (m/s)"
jsb.ComponentTitle = ""
jsb.TitleColor = [0.10, 0.10, 0.10]; jsb.LabelColor = [0.62, 0.62, 0.62]
try:
    jsb.WindowLocation = "Any Location"
except Exception: pass
jsb.Position = [0.935, 0.50]; jsb.ScalarBarLength = 0.36

try: jsb.Interactivity = 0
except Exception: pass
sd.SetScalarBarVisibility(view, True)
ssb = GetScalarBar(slut, view)
ssb.Title = "Surface wind (m/s)"
ssb.ComponentTitle = ""
ssb.TitleColor = [0.10, 0.10, 0.10]; ssb.LabelColor = [0.62, 0.62, 0.62]
try:
    ssb.WindowLocation = "Any Location"
except Exception: pass
ssb.Position = [0.935, 0.10]; ssb.ScalarBarLength = 0.28

try: ssb.Interactivity = 0
except Exception: pass
# bounding box
ob = Show(vol, view)
ob.SetRepresentationType("Outline")
ob.AmbientColor = [0.40, 0.44, 0.52]
ob.LineWidth = 1.2

# 3D streamlines along the jet axis
try:
    st = StreamTracer(Input=vol, SeedType="Point Cloud")
    st.Vectors = ["POINTS", "Wind3D"]
    st.SeedType.Center = [0.0, 45.0, 3 * Z_STEP]   # seed near the jet, NH only
    st.SeedType.Radius = 80.0
    st.SeedType.NumberOfPoints = 40
    st.MaximumStreamlineLength = 700
    st.IntegrationDirection = "BOTH"
    UpdatePipeline(proxy=st)
    stube = Tube(Input=st)
    stube.Radius = 0.4; stube.NumberofSides = 8
    UpdatePipeline(proxy=stube)
    std = Show(stube, view)
    std.AmbientColor   = [0.30, 0.35, 0.50]         # light silver, not dark blue
    std.DiffuseColor   = [0.30, 0.35, 0.50]
    std.ColorArrayName = ["POINTS", ""]
    std.Opacity = 0.45
    std.Ambient = 1.0; std.Diffuse = 0.0
    print("3D streamlines OK (40 silver accents near the jet)")
except Exception as e:
    print(f"Streamlines skipped: {e}")

# coastlines at surface level and under the top shelf
coast = f"{B}/task1_atmosphere/global/world_coastlines.vtp"
if os.path.exists(coast):
    for z, op in ((0.4, 0.95), (4 * Z_STEP - 0.4, 0.35)):
        rd = XMLPolyDataReader(FileName=[coast]); UpdatePipeline(proxy=rd)
        tf = Transform(Input=rd)
        tf.Transform.Translate = [0.0, 0.0, z]
        UpdatePipeline(proxy=tf)
        dd = Show(tf, view)
        dd.AmbientColor = [0.25, 0.30, 0.45]; dd.DiffuseColor = [0.25, 0.30, 0.45]
        dd.LineWidth = 1.3; dd.Opacity = op
        dd.ColorArrayName = ["POINTS", ""]
        dd.Ambient = 1.0; dd.Diffuse = 0.0

# floating labels â€" use Translation not Position (Position crashes PV 6.1.1)
for k, (z, _m, label) in enumerate(LAYERS):
    try:
        t3 = Text3D()
        t3.Text = label
        td = Show(t3, view)
        td.Scale       = [9.0, 9.0, 9.0]
        td.Translation = [-330.0, 95.0, z]
        td.AmbientColor = [0.30, 0.35, 0.50]
        td.DiffuseColor = [0.30, 0.35, 0.50]
        td.Ambient = 1.0; td.Diffuse = 0.0
        td.Opacity = 0.95
    except Exception as e:
        print(f"Label '{label}' skipped: {e}")


# camera
view.CameraParallelProjection = 0
cam = GetActiveCamera()
cam.SetFocalPoint(0.0, 10.0, 80.0)
cam.SetPosition(-140.0, -390.0, 300.0)
cam.SetViewUp(0.0, 0.0, 1.0)
view.CameraViewAngle = 30

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
Render(view)
os.makedirs(f"{R}/stills", exist_ok=True)
SaveScreenshot(f"{R}/stills/task1_3d_layers.png", view, ImageResolution=PDF_RESOLUTION)
print(f"Saved: {R}/stills/task1_3d_layers.png")
print("Press Play: 20 timesteps. Export: MP4, 4 fps -> task1_3d.mp4")

if SAVE_PDF_STILLS:
    _pdf_dir = f"{R}/pdf_stills/task1_3d"
    os.makedirs(_pdf_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = [scene.StartTime + i*(scene.EndTime-scene.StartTime)/19 for i in range(20)]
    _web_res = [1920, 1080]
    print(f"\nExporting ALL {len(_ts)} 3D atmosphere frames  ->  {_pdf_dir}")
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = _t; UpdatePipeline(); Render(view)
        _png = f"{_pdf_dir}/frame_{_i:02d}_t{_t:.0f}.png"
        SaveScreenshot(_png, view, ImageResolution=_web_res)
        print(f"  [{_i+1}/{len(_ts)}] t={_t:.1f}")
    print("Run  python export_pdf.py  to build the master paper PDF")


