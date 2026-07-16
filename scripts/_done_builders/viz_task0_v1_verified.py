#!/usr/bin/env python
# TASK 0 — Clean climate extremes visualization
#
# WHAT YOU SEE (4 layers only, all animated per year 1950-2025):
#   1. Air Temperature background  — climate context
#   2. CEI stress contour rings    — compound extreme zones (0.65 / 0.75 / 0.85)
#   3. Critical points             — CEI maxima (red), minima (blue), saddles (green)
#   4. Coastlines + borders        — geographic reference
#
# The trajectory tubes are NOT shown in the animation (they span all 76 years
# and are confusing when overlaid). See viz_task0_summary.py for a static
# summary view showing trajectories.
#
# Run: View > Python Shell > Run Script  (in ParaView)
from paraview.simple import *
import os

B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
R  = f"{B}/renders";                   os.makedirs(R, exist_ok=True)
F  = f"{B}/task0_climate/frames"
CP = f"{B}/task0_climate/cp_per_step"

# ── View setup ────────────────────────────────────────────────────────────────
view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1340]
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.02, 0.02, 0.05]
view.OrientationAxesVisibility    = 0
try:
    view.UseFXAA = 1          # anti-aliasing: smooth glyph and contour edges
except Exception:
    pass

# ── 1. Air Temperature background ─────────────────────────────────────────────
field = OpenDataFile(f"{F}/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "AirTemperature_C"))
fd.Opacity = 0.85

tlut = GetColorTransferFunction("AirTemperature_C")
tlut.RGBPoints = [
    -40, 0.08, 0.08, 0.38,
    -10, 0.12, 0.28, 0.78,
      0, 0.25, 0.55, 0.88,
     15, 0.45, 0.82, 0.38,
     25, 0.95, 0.88, 0.18,
     35, 0.95, 0.48, 0.05,
     45, 0.85, 0.10, 0.05,
     55, 1.00, 1.00, 1.00,
]
tlut.ColorSpace = "Lab"
tlut.NanColor   = [0.02, 0.02, 0.05]
fd.SetScalarBarVisibility(view, True)
tsb = GetScalarBar(tlut, view)
tsb.Title           = "Air Temperature (C)"
tsb.ComponentTitle  = ""
tsb.TitleColor      = [0.80, 0.80, 0.80]
tsb.LabelColor      = [0.60, 0.60, 0.60]
tsb.Position        = [0.01, 0.10]
tsb.ScalarBarLength = 0.70

# ── 2. CEI stress contour rings (0.65 / 0.75 / 0.85) ─────────────────────────
ct = Contour(Input=field)
ct.ContourBy   = ["POINTS", "CompoundExtremesIndex"]
ct.Isosurfaces = [0.65, 0.75, 0.85]
UpdatePipeline(proxy=ct)
ctd = Show(ct, view)
ctd.AmbientColor      = [1.0, 1.0, 1.0]
ctd.DiffuseColor      = [1.0, 1.0, 1.0]
ctd.LineWidth         = 1.8
ctd.Opacity           = 0.90
ctd.ColorArrayName    = ["POINTS", ""]   # solid color in PV 6.1.1

# ── 3. Animated critical points (per-year VTPs from task0_cp.pvd) ─────────────
cp_pvd = f"{CP}/task0_cp.pvd"
if os.path.exists(cp_pvd):
    cp_reader = OpenDataFile(cp_pvd)
    UpdatePipeline()

    # Glyphs — sphere per critical point
    cp_gl = Glyph(Input=cp_reader)
    cp_gl.GlyphType        = "Sphere"
    cp_gl.ScaleFactor      = 1.2
    cp_gl.GlyphMode        = "All Points"
    cp_gl.ScaleArray       = ["POINTS", "No scale array"]
    cp_gl.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=cp_gl)

    cp_d = Show(cp_gl, view)
    ColorBy(cp_d, ("POINTS", "CriticalType"))

    cp_lut = GetColorTransferFunction("CriticalType")
    cp_lut.InterpretValuesAsCategories = 1
    cp_lut.Annotations      = ["0", "Minimum", "1", "Saddle", "3", "Maximum"]
    cp_lut.IndexedColors    = [
        0.10, 0.30, 0.95,   # 0 = minimum  -> blue
        0.10, 0.80, 0.10,   # 1 = saddle   -> green
        0.95, 0.10, 0.10,   # 3 = maximum  -> red
    ]
    cp_lut.IndexedOpacities = [1.0, 0.5, 1.0]   # saddles semi-transparent
    cp_lut.ColorSpace       = "RGB"
    cp_d.Opacity = 1.0

    cp_d.SetScalarBarVisibility(view, True)
    cpsb = GetScalarBar(cp_lut, view)
    cpsb.Title           = "Critical Point"
    cpsb.ComponentTitle  = ""
    cpsb.TitleColor      = [0.80, 0.80, 0.80]
    cpsb.LabelColor      = [0.60, 0.60, 0.60]
    cpsb.DrawAnnotations = 1
    cpsb.Position        = [0.86, 0.10]
    cpsb.ScalarBarLength = 0.35
    print("Critical points loaded (animates per year)")
else:
    print("WARNING: task0_cp.pvd not found. Run extract_cp_per_timestep.py first.")

# ── 4. Coastlines + country borders ───────────────────────────────────────────
G = f"{B}/task1_atmosphere/global"
for vtp_file, color, lw in [
        (f"{G}/world_coastlines.vtp", [0.65, 0.70, 0.75], 1.2),
        (f"{G}/world_countries.vtp",  [0.32, 0.38, 0.45], 0.7)]:
    if os.path.exists(vtp_file):
        coast = XMLPolyDataReader(FileName=[vtp_file])
        UpdatePipeline(proxy=coast)
        cd = Show(coast, view)
        cd.AmbientColor    = color
        cd.DiffuseColor    = color
        cd.LineWidth       = lw
        cd.Opacity         = 0.80
        cd.ColorArrayName  = ["POINTS", ""]   # solid color in PV 6.1.1
print("Coastlines loaded")

# ── 5. Year label ─────────────────────────────────────────────────────────────
# AnnotateTimeFilter prints the current animation time value.
# task0.pvd has timestep values = 1950..2025, so the label shows the year.
_label_ok = False
for _name in ("AnnotateTimeFilter", "AnnotationTimeFilter"):
    _cls = globals().get(_name)
    if _cls is None:
        continue
    try:
        ann = _cls(Input=field)
        ann.Format = "Year: {time:.0f}"
        ann_d = Show(ann, view)
        ann_d.FontSize       = 36
        ann_d.Color          = [1.0, 1.0, 1.0]
        ann_d.WindowLocation = "Upper Right Corner"
        _label_ok = True
        print(f"Year label added via {_name}")
        break
    except Exception as _e:
        print(f"  {_name}: {_e}")

if not _label_ok:
    # Fallback: static text (user updates manually)
    try:
        txt = Text()
        txt.Text = "Year: 1950"
        txt_d = Show(txt, view)
        txt_d.FontSize       = 36
        txt_d.Color          = [1.0, 1.0, 1.0]
        txt_d.WindowLocation = "Upper Right Corner"
        print("Year label: static text (AnnotateTimeFilter not available)")
    except Exception as _e2:
        print(f"Year label skipped: {_e2}")

# ── Camera + animation ────────────────────────────────────────────────────────
view.CameraParallelProjection = 1
ResetCamera(view)

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation range: {scene.StartTime} to {scene.EndTime}  (should be 1950 to 2025)")

Render(view)
SaveScreenshot(f"{R}/task0_clean.png", view, ImageResolution=[2560, 1340])
print(f"Screenshot: {R}/task0_clean.png")
print()
print("What you see:")
print("  Red dots   = CEI maxima  (compound extreme hot-spots)")
print("  Blue dots  = CEI minima")
print("  Green dots = Saddle points")
print("  White rings= CEI stress zones (0.65 / 0.75 / 0.85)")
print("  Background = Air temperature")
print()
print("Press Play to animate 1950->2025")
print("Export: File > Save Animation > MP4, 6 fps, 2560x1340")
