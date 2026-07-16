#!/usr/bin/env python
# TASK 1 — SPACE-TIME hero visualization (LOAD-ONLY, no TTK => never crashes).
# The vorticity field is the flat "floor"; vortex trajectories rise in Z with
# time, so you SEE the cyclones/anticyclones move through space-time.
# Run in ParaView GUI (View > Python Shell > Run Script) OR headless via pvpython.
from paraview.simple import *
import os
B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)
O = f"{B}/outputs"
ZWARP = 45.0          # how tall the time-stack is (bigger = taller cube)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [1600, 1400]
view.UseColorPaletteForBackground = 0          # let our dark background win
view.BackgroundColorMode = "Single Color"
view.Background = [0.02, 0.03, 0.06]
view.OrientationAxesVisibility = 0

# --- vorticity floor (time step 0) ---
field = XMLImageDataReader(FileName=[f"{B}/task1_atmosphere/tracking/FACE2_VORT_tracking.vti"])
field.PointArrayStatus = ["field_0000"]
fd = Show(field, view); fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "field_0000")); fd.Opacity = 0.9
vlut = GetColorTransferFunction("field_0000"); vlut.ApplyPreset("Cool to Warm", True)
vlut.RescaleTransferFunction(-1.0, 1.0)
fd.SetScalarBarVisibility(view, False)

def lift(src_vtp):
    """load a .vtp and displace each point in +Z by its TimeStep (space-time)."""
    r = XMLPolyDataReader(FileName=[src_vtp])
    w = WarpByScalar(Input=r)
    w.Scalars = ["POINTS", "TimeStep"]
    w.UseNormal = 1; w.Normal = [0.0, 0.0, 1.0]
    w.ScaleFactor = ZWARP
    w.UpdatePipeline()
    return w

def tracks(vtp, radius=7.0):
    tb = Tube(Input=lift(vtp)); tb.Radius = radius
    d = Show(tb, view); ColorBy(d, ("POINTS", "TimeStep"))
    GetColorTransferFunction("TimeStep").ApplyPreset("Viridis", True)
    return d

def nodes(vtp, scale=16.0):
    g = Glyph(Input=lift(vtp), GlyphType="Sphere")
    g.ScaleFactor = scale; g.GlyphMode = "All Points"
    d = Show(g, view); ColorBy(d, ("POINTS", "TimeStep"))
    GetColorTransferFunction("TimeStep").ApplyPreset("Viridis", True)
    return d

d1 = tracks(f"{O}/task1_vortex_anti_trajectories.vtp")
tracks(f"{O}/task1_vortex_cyc_trajectories.vtp")
nodes(f"{O}/task1_vortex_anti_nodes.vtp")
nodes(f"{O}/task1_vortex_cyc_nodes.vtp")
d1.SetScalarBarVisibility(view, True)

# 3D perspective looking across the time-stack
view.CameraParallelProjection = 0
ResetCamera(view)
cam = GetActiveCamera()
cam.Elevation(-62)        # tilt down to reveal the vertical time axis
cam.Azimuth(28)
view.CenterOfRotation = view.CameraFocalPoint
ResetCamera(view)
cam.Elevation(-62); cam.Azimuth(28); cam.Dolly(1.15)
Render(view)
SaveScreenshot(f"{R}/task1_hero.png", view, ImageResolution=[1600, 1400])
print("saved", f"{R}/task1_hero.png")
