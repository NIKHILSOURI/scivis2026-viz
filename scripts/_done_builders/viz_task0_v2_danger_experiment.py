#!/usr/bin/env python
# TASK 0 v2 — "THE DANGER MAP"
#
# What changed vs v1 (plain temperature + all critical points):
#   HERO      : the Compound Extremes Index itself, dark glowing palette
#   EXTREMA   : only SIGNIFICANT features (persistence >= 0.08), sphere size
#               and colour scale with topological persistence — big glowing
#               sphere = major long-lived event, tiny = marginal
#   TOP EVENT : each year the single strongest feature gets an amber halo —
#               your eye follows the worst event on Earth, year by year
#   OPTIONAL  : USE_ANOMALY = True -> background shows CEI change vs the
#               1950-1979 baseline (the map visibly reddens = climate change)
#
# Run: ParaView > Python Shell > Reset > Run Script
from paraview.simple import *
import os

USE_ANOMALY = False    # True = anomaly background (warming arc), False = CEI

B = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
R = f"{B}/renders"; os.makedirs(R, exist_ok=True)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1340]
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.01, 0.01, 0.04]
view.OrientationAxesVisibility    = 0
try: view.UseFXAA = 1
except Exception: pass

# ── 1. Background: CEI hero (or anomaly) ──────────────────────────────────────
field = OpenDataFile(f"{B}/task0_climate/frames/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
fd.Ambient = 1.0; fd.Diffuse = 0.0

if USE_ANOMALY:
    ColorBy(fd, ("POINTS", "CEI_Anomaly"))
    alut = GetColorTransferFunction("CEI_Anomaly")
    alut.RGBPoints = [
        -0.15, 0.10, 0.30, 0.85,   # cooler/less extreme -> blue
        -0.04, 0.05, 0.08, 0.22,
         0.00, 0.04, 0.04, 0.09,   # no change           -> near-black
         0.04, 0.30, 0.08, 0.06,
         0.15, 1.00, 0.35, 0.05,   # more extreme        -> hot orange
    ]
    alut.ColorSpace = "Lab"; alut.NanColor = [0.01, 0.01, 0.04]
    fd.SetScalarBarVisibility(view, True)
    bsb = GetScalarBar(alut, view)
    bsb.Title = "CEI change vs 1950-1979"
else:
    ColorBy(fd, ("POINTS", "CompoundExtremesIndex"))
    clut = GetColorTransferFunction("CompoundExtremesIndex")
    clut.RGBPoints = [
        0.20, 0.03, 0.03, 0.10,
        0.40, 0.10, 0.08, 0.25,
        0.55, 0.45, 0.10, 0.30,
        0.70, 0.85, 0.25, 0.05,
        0.85, 1.00, 0.65, 0.10,
        0.95, 1.00, 1.00, 0.75,
    ]
    clut.ColorSpace = "Lab"; clut.NanColor = [0.01, 0.01, 0.04]
    fd.SetScalarBarVisibility(view, True)
    bsb = GetScalarBar(clut, view)
    bsb.Title = "Compound Extremes Index"
bsb.ComponentTitle = ""
bsb.TitleColor = [0.85, 0.85, 0.85]; bsb.LabelColor = [0.62, 0.62, 0.62]
bsb.Position = [0.015, 0.10]; bsb.ScalarBarLength = 0.55
fd.Opacity = 1.0

# ── 2. Severe-stress contours (0.75 / 0.85 only — less clutter) ───────────────
ct = Contour(Input=field)
ct.ContourBy   = ["POINTS", "CompoundExtremesIndex"]
ct.Isosurfaces = [0.75, 0.85]
UpdatePipeline(proxy=ct)
ctd = Show(ct, view)
ctd.AmbientColor = [1.0, 1.0, 1.0]; ctd.DiffuseColor = [1.0, 1.0, 1.0]
ctd.LineWidth = 1.3; ctd.Opacity = 0.55
ctd.ColorArrayName = ["POINTS", ""]
ctd.Ambient = 1.0; ctd.Diffuse = 0.0

# ── 3. TOP-30 extrema of each year, sized + coloured by RANK ──────────────────
# (all top-30 have persistence 0.87-0.97, so rank is the informative encoding)
sig = OpenDataFile(f"{B}/task0_climate/sig_top30/sig30.pvd")
UpdatePipeline()
calc = Calculator(Input=sig)
calc.AttributeType   = "Point Data"
calc.ResultArrayName = "GlyphSize"
calc.Function        = "1.0/sqrt(Rank)"        # rank 1 -> 1.0, rank 30 -> 0.18
UpdatePipeline(proxy=calc)

gl = Glyph(Input=calc)
gl.GlyphType        = "Sphere"
gl.GlyphMode        = "All Points"
gl.ScaleArray       = ["POINTS", "GlyphSize"]
gl.ScaleFactor      = 8.0
gl.OrientationArray = ["POINTS", "No orientation array"]
UpdatePipeline(proxy=gl)
gd = Show(gl, view)
ColorBy(gd, ("POINTS", "Rank"))
plut = GetColorTransferFunction("Rank")
plut.RGBPoints = [
     1, 1.00, 1.00, 1.00,   # strongest  -> white (pops on orange land)
     5, 0.60, 0.95, 1.00,   #            -> pale cyan
    12, 0.10, 0.75, 0.95,   #            -> cyan
    30, 0.05, 0.30, 0.65,   # rank 30    -> deep blue
]
plut.ColorSpace = "Lab"
gd.Opacity = 0.95
gd.Ambient = 1.0; gd.Diffuse = 0.0
gd.SetScalarBarVisibility(view, True)
psb = GetScalarBar(plut, view)
psb.Title = "Event rank (1 = strongest)"
psb.ComponentTitle = ""
psb.TitleColor = [0.85, 0.85, 0.85]; psb.LabelColor = [0.62, 0.62, 0.62]
psb.Position = [0.90, 0.35]; psb.ScalarBarLength = 0.40
print("Top-30 extrema per year loaded (rank-encoded)")

# ── 4. Top event halo (the year's strongest feature) ──────────────────────────
top = OpenDataFile(f"{B}/task0_climate/top_event/top.pvd")
UpdatePipeline()
halo = Glyph(Input=top)
halo.GlyphType        = "Sphere"
halo.GlyphMode        = "All Points"
halo.ScaleArray       = ["POINTS", "No scale array"]
halo.ScaleFactor      = 16.0
halo.OrientationArray = ["POINTS", "No orientation array"]
UpdatePipeline(proxy=halo)
hd = Show(halo, view)
hd.AmbientColor = [1.00, 0.72, 0.15]; hd.DiffuseColor = [1.00, 0.72, 0.15]
hd.ColorArrayName = ["POINTS", ""]
hd.Opacity = 0.28
hd.Ambient = 1.0; hd.Diffuse = 0.0

core = Glyph(Input=top)
core.GlyphType        = "Sphere"
core.GlyphMode        = "All Points"
core.ScaleArray       = ["POINTS", "No scale array"]
core.ScaleFactor      = 4.5
core.OrientationArray = ["POINTS", "No orientation array"]
UpdatePipeline(proxy=core)
cd2 = Show(core, view)
cd2.AmbientColor = [1.00, 0.85, 0.30]; cd2.DiffuseColor = [1.00, 0.85, 0.30]
cd2.ColorArrayName = ["POINTS", ""]
cd2.Opacity = 0.95
cd2.Ambient = 1.0; cd2.Diffuse = 0.0
print("Top-event halo loaded (amber = strongest feature of the year)")

# ── 5. Coastlines ─────────────────────────────────────────────────────────────
G = f"{B}/task1_atmosphere/global"
for vf, c, lw in [(f"{G}/world_coastlines.vtp", [0.55, 0.60, 0.68], 1.2),
                  (f"{G}/world_countries.vtp",  [0.26, 0.30, 0.38], 0.6)]:
    if os.path.exists(vf):
        rd = XMLPolyDataReader(FileName=[vf]); UpdatePipeline(proxy=rd)
        dd = Show(rd, view)
        dd.AmbientColor = c; dd.DiffuseColor = c
        dd.LineWidth = lw; dd.Opacity = 0.85
        dd.ColorArrayName = ["POINTS", ""]
        dd.Ambient = 1.0; dd.Diffuse = 0.0

# ── 6. Year label + title ─────────────────────────────────────────────────────
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
    except Exception: pass
try:
    ttl = Text()
    mode = "CEI anomaly vs 1950-1979" if USE_ANOMALY else "Compound Extremes Index"
    ttl.Text = (f"Compound climate extremes, 1950-2025  |  {mode}\n"
                "Sphere size = topological persistence   |   amber halo = strongest event of the year")
    tdd = Show(ttl, view)
    tdd.FontSize = 22; tdd.Color = [0.93, 0.93, 0.93]
    tdd.WindowLocation = "Upper Left Corner"
except Exception: pass

# ── Camera + animation ────────────────────────────────────────────────────────
view.CameraParallelProjection = 1
ResetCamera(view)
scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation: {scene.StartTime:.0f} -> {scene.EndTime:.0f} (must be 1950 -> 2025)")

Render(view)
SaveScreenshot(f"{R}/task0_danger_map.png", view, ImageResolution=[2560, 1340])
print(f"Saved: {R}/task0_danger_map.png")
print()
print("Press Play. Export: MP4, 6 fps -> task0_main.mp4")
print("Tip: set USE_ANOMALY = True at the top for the warming-arc version.")
