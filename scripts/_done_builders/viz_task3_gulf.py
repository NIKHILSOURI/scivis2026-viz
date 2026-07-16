#!/usr/bin/env python
# TASK 3 — Gulf Stream at FULL LLC4320 resolution (16 daily frames)
#
#   Left mental model: SST (warm river of the Gulf Stream + cold eddies)
#   Overlaid: SST GRADIENT ridges = ocean FRONTS (the topological skeleton
#   of the flow — eddies appear as closed gradient rings)
#
# Run: ParaView > Python Shell > Reset > Run Script
from paraview.simple import *
import os

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.01, 0.01, 0.04]
view.OrientationAxesVisibility    = 0
try: view.UseFXAA = 1
except Exception: pass

gulf = OpenDataFile(f"{B}/task3_ocean/gulfstream/gulf.pvd")
UpdatePipeline()

# ── SST base ──────────────────────────────────────────────────────────────────
gd = Show(gulf, view)
gd.SetRepresentationType("Surface")
ColorBy(gd, ("POINTS", "SST_C"))
tlut = GetColorTransferFunction("SST_C")
tlut.RGBPoints = [
     2, 0.05, 0.02, 0.22,   # cold  -> deep indigo
    10, 0.10, 0.20, 0.60,
    16, 0.05, 0.55, 0.65,
    20, 0.20, 0.80, 0.45,
    24, 0.95, 0.85, 0.20,
    28, 1.00, 0.45, 0.05,   # warm  -> orange
]
tlut.ColorSpace = "Lab"
tlut.NanColor   = [0.05, 0.05, 0.07]     # land
gd.SetScalarBarVisibility(view, True)
sb = GetScalarBar(tlut, view)
sb.Title = "Sea Surface Temperature (C)"
sb.ComponentTitle = ""
sb.TitleColor = [0.85, 0.85, 0.85]; sb.LabelColor = [0.62, 0.62, 0.62]
sb.Position = [0.02, 0.25]; sb.ScalarBarLength = 0.5

# ── Front ridges: contours of SST gradient ────────────────────────────────────
fr = Contour(Input=gulf)
fr.ContourBy   = ["POINTS", "SST_Gradient"]
fr.Isosurfaces = [0.35, 0.8]
UpdatePipeline(proxy=fr)
frd = Show(fr, view)
frd.AmbientColor   = [1.0, 1.0, 1.0]
frd.DiffuseColor   = [1.0, 1.0, 1.0]
frd.LineWidth      = 1.0
frd.Opacity        = 0.55
frd.ColorArrayName = ["POINTS", ""]

# ── Title + year of note ──────────────────────────────────────────────────────
try:
    ttl = Text()
    ttl.Text = ("Gulf Stream at native LLC4320 resolution (~2 km, 1280x1280)\n"
                "SST + frontal ridges | 16 daily steps — eddies pinch off in real time")
    tdd = Show(ttl, view)
    tdd.FontSize = 22; tdd.Color = [0.93, 0.93, 0.93]
    tdd.WindowLocation = "Upper Left Corner"
except Exception: pass

view.CameraParallelProjection = 1
ResetCamera(view)
scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
Render(view)
SaveScreenshot(f"{R}/task3_gulfstream.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/task3_gulfstream.png")
print("Press Play: 16 daily steps. Export: MP4, 4 fps -> task3_gulf.mp4")
