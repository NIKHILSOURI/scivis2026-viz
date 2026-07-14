#!/usr/bin/env python
# Task 1 — 3D layered atmosphere: 5 altitude shelves, self-lit
# ParaView: Python Shell > Reset > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
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
view.Background                   = [0.02, 0.02, 0.05]
view.OrientationAxesVisibility    = 0
try: view.UseFXAA = 1
except Exception: pass

vol = OpenDataFile(f"{B}/task1_atmosphere/global3d/task1_3d.pvd")
UpdatePipeline()

# colour scale for upper shelves (jet level)
jlut = GetColorTransferFunction("WindSpeed_ms")
jlut.RGBPoints = [
    10, 0.10, 0.15, 0.40,
    25, 0.05, 0.45, 0.80,
    45, 0.10, 0.85, 0.70,
    65, 0.95, 0.90, 0.25,
    85, 1.00, 0.55, 0.05,
   110, 1.00, 1.00, 0.95,
]
jlut.ColorSpace = "Lab"

# surface layer — separate 0-25 m/s colour scale so it doesn't go black
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
     0, 0.06, 0.07, 0.18,
     6, 0.10, 0.25, 0.50,
    12, 0.10, 0.55, 0.65,
    18, 0.55, 0.85, 0.45,
    25, 1.00, 0.95, 0.55,
]
slut.ColorSpace = "Lab"
sd.Opacity = 1.0
sd.Ambient = 1.0; sd.Diffuse = 0.0            # self-lit: full brightness
RenameSource("L0_SURFACE", calc)

# upper shelves — threshold out the calm air at each level
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
jsb.TitleColor = [0.85, 0.85, 0.85]; jsb.LabelColor = [0.62, 0.62, 0.62]
try:
    jsb.WindowLocation = "Any Location"
except Exception: pass
jsb.Position = [0.935, 0.50]; jsb.ScalarBarLength = 0.36

sd.SetScalarBarVisibility(view, True)
ssb = GetScalarBar(slut, view)
ssb.Title = "Surface wind (m/s)"
ssb.ComponentTitle = ""
ssb.TitleColor = [0.85, 0.85, 0.85]; ssb.LabelColor = [0.62, 0.62, 0.62]
try:
    ssb.WindowLocation = "Any Location"
except Exception: pass
ssb.Position = [0.935, 0.10]; ssb.ScalarBarLength = 0.28

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
    std.AmbientColor   = [0.92, 0.95, 1.00]         # light silver, not dark blue
    std.DiffuseColor   = [0.92, 0.95, 1.00]
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
        dd.AmbientColor = [0.75, 0.80, 0.88]; dd.DiffuseColor = [0.75, 0.80, 0.88]
        dd.LineWidth = 1.3; dd.Opacity = op
        dd.ColorArrayName = ["POINTS", ""]
        dd.Ambient = 1.0; dd.Diffuse = 0.0

# floating labels — use Translation not Position (Position crashes PV 6.1.1)
for k, (z, _m, label) in enumerate(LAYERS):
    try:
        t3 = Text3D()
        t3.Text = label
        td = Show(t3, view)
        td.Scale       = [9.0, 9.0, 9.0]
        td.Translation = [-330.0, 95.0, z]
        td.AmbientColor = [0.90, 0.92, 1.00]
        td.DiffuseColor = [0.90, 0.92, 1.00]
        td.Ambient = 1.0; td.Diffuse = 0.0
        td.Opacity = 0.95
    except Exception as e:
        print(f"Label '{label}' skipped: {e}")

# title
try:
    ttl = Text()
    ttl.Text = ("The atmosphere layer by layer: wind speed grows ~5x with altitude\n"
                "The jet stream exists ONLY aloft: bottom calm, top glowing")
    tdd = Show(ttl, view)
    tdd.FontSize = 24; tdd.Color = [0.94, 0.94, 0.94]
    tdd.WindowLocation = "Upper Left Corner"
except Exception: pass

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
SaveScreenshot(f"{R}/figures/task1_3d_layers.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/task1_3d_layers.png")
print("Press Play: 20 timesteps. Export: MP4, 4 fps -> task1_3d.mp4")
