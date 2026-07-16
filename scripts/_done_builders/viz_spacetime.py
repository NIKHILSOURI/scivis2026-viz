#!/usr/bin/env python
# SPACE-TIME TOWER — the signature still image of the submission.
#
#   Base (z=0):    the world map with 76-yr mean-period CEI + coastlines
#   Rising tubes:  every CEI extreme trajectory, z = time (1950 bottom, 2025 top)
#                  coloured by LIFETIME — gold tubes = decades-long extremes
#   Spheres:       cyan = feature birth, red = feature death (in space-time)
#
# Read it like tree rings: the vertical axis IS the climate record.
# Persistent extremes form tall columns; you can see WHERE the atmosphere
# keeps producing compound extremes and WHEN new columns appear.
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
view.Background                   = [0.015, 0.015, 0.045]
view.OrientationAxesVisibility    = 0
try: view.UseFXAA = 1
except Exception: pass

# ── Base map: CEI field frozen at 2025, dimmed ────────────────────────────────
field = OpenDataFile(f"{B}/task0_climate/frames/task0.pvd")
scene = GetAnimationScene(); scene.UpdateAnimationUsingDataTimeSteps()
scene.AnimationTime = 2025.0
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "CompoundExtremesIndex"))
fd.Opacity = 0.50
clut = GetColorTransferFunction("CompoundExtremesIndex")
clut.ApplyPreset("Inferno", True)
clut.RescaleTransferFunction(0.30, 0.95)
fd.SetScalarBarVisibility(view, False)

# ── Coastlines on the base ────────────────────────────────────────────────────
G = f"{B}/task1_atmosphere/global"
for vf, c, lw in [(f"{G}/world_coastlines.vtp", [0.60, 0.65, 0.72], 1.4),
                  (f"{G}/world_countries.vtp",  [0.28, 0.33, 0.40], 0.6)]:
    if os.path.exists(vf):
        rd = XMLPolyDataReader(FileName=[vf]); UpdatePipeline(proxy=rd)
        dd = Show(rd, view)
        dd.AmbientColor = c; dd.DiffuseColor = c
        dd.LineWidth = lw; dd.Opacity = 0.9
        dd.ColorArrayName = ["POINTS", ""]

# ── Space-time tubes coloured by lifetime ─────────────────────────────────────
tr = XMLPolyDataReader(FileName=[f"{B}/outputs/spacetime_tracks.vtp"])
UpdatePipeline(proxy=tr)
tube = Tube(Input=tr)
tube.Radius        = 0.45
tube.NumberofSides = 10
UpdatePipeline(proxy=tube)
td = Show(tube, view)
ColorBy(td, ("POINTS", "LifetimeYears"))
llut = GetColorTransferFunction("LifetimeYears")
llut.RGBPoints = [
     5, 0.15, 0.15, 0.35,   # short-lived -> dim slate
    15, 0.20, 0.45, 0.85,   # decade      -> blue
    30, 0.20, 0.85, 0.75,   # 30 yr       -> teal
    50, 1.00, 0.80, 0.15,   # 50 yr       -> gold
    76, 1.00, 1.00, 0.85,   # whole record-> white-gold
]
llut.ColorSpace = "Lab"
td.Opacity  = 0.85
td.Specular = 0.4
td.SetScalarBarVisibility(view, True)
lsb = GetScalarBar(llut, view)
lsb.Title = "Feature Lifetime (years)"
lsb.ComponentTitle = ""
lsb.TitleColor = [0.85, 0.85, 0.85]; lsb.LabelColor = [0.62, 0.62, 0.62]
lsb.Position = [0.02, 0.32]; lsb.ScalarBarLength = 0.40

# ── Birth / death markers ─────────────────────────────────────────────────────
evr = XMLPolyDataReader(FileName=[f"{B}/outputs/spacetime_events.vtp"])
UpdatePipeline(proxy=evr)
egl = Glyph(Input=evr)
egl.GlyphType        = "Sphere"
egl.ScaleFactor      = 1.1
egl.GlyphMode        = "All Points"
egl.ScaleArray       = ["POINTS", "No scale array"]
egl.OrientationArray = ["POINTS", "No orientation array"]
UpdatePipeline(proxy=egl)
ed = Show(egl, view)
ColorBy(ed, ("POINTS", "EventType"))
elut = GetColorTransferFunction("EventType")
elut.InterpretValuesAsCategories = 1
elut.Annotations      = ["1", "Birth", "2", "Death"]
elut.IndexedColors    = [0.05, 0.90, 0.95,   1.00, 0.25, 0.15]
elut.IndexedOpacities = [1.0, 1.0]
ed.Opacity = 0.75

# ── Title ─────────────────────────────────────────────────────────────────────
try:
    ttl = Text()
    ttl.Text = ("The Space-Time Record of Compound Climate Extremes  (1950 base -> 2025 top)\n"
                "Gold columns = extremes persisting for decades")
    tdd = Show(ttl, view)
    tdd.FontSize = 24; tdd.Color = [0.93, 0.93, 0.93]
    tdd.WindowLocation = "Upper Left Corner"
except Exception: pass

# ── 3/4 perspective camera ────────────────────────────────────────────────────
view.CameraParallelProjection = 0
cam = GetActiveCamera()
cam.SetFocalPoint(0.0, 5.0, 48.0)
cam.SetPosition(-95.0, -330.0, 215.0)
cam.SetViewUp(0.0, 0.0, 1.0)
view.CameraViewAngle = 30
Render(view)

SaveScreenshot(f"{R}/spacetime_tower.png", view, ImageResolution=[2560, 1440])
print(f"Saved: {R}/spacetime_tower.png")
print()
print("TIPS:")
print("  - Rotate interactively: the structure reads best while moving.")
print("  - For the video: right-click view > Camera > Orbit for a slow orbit shot,")
print("    or File > Save Animation with a Camera orbit track (~10 s at 30 fps).")
print("  - Too dense? Filters > Threshold on LifetimeYears > 15 to keep only")
print("    the multi-decade columns.")
