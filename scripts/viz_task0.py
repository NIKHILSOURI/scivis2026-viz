#!/usr/bin/env python
# Task 0 visualization â€” compound extremes 1950-2025
# ParaView: View > Python Shell > Run Script
from paraview.simple import *
import os

# ---- CHANGE THIS to wherever you put the sample_for_prof folder ----
B  = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
# --------------------------------------------------------------------
# Set True ONLY when exporting â€” ray tracing is too slow for interactive use
RAYTRACING      = True   # RTX enabled — disable for interactive, enable for export
SAVE_ALL_FRAMES = True   # export all 76 years to renders/pdf_stills/task0_frames/
R  = f"{B}/renders";                   os.makedirs(R, exist_ok=True)
F  = f"{B}/task0_climate/frames"
CP = f"{B}/task0_climate/cp_per_step"

# view
view = GetActiveViewOrCreate("RenderView")
view.ViewSize                     = [2560, 1440]   # 16:9
view.UseColorPaletteForBackground = 0
view.BackgroundColorMode          = "Single Color"
view.Background                   = [0.96, 0.93, 0.86]
view.OrientationAxesVisibility    = 0
try:
    view.UseFXAA = 1
except Exception:
    pass

# â”€â”€ Ray tracing â€” enabled only when RAYTRACING=True (export mode) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if RAYTRACING:
    try:
        view.EnableRayTracing = 1
        for _backend in ("OptiX pathtracer", "OSPRay pathtracer", "OSPRay raycaster"):
            try: view.BackEnd = _backend; break
            except Exception: continue
        view.SamplesPerPixel = 16   # 16 spp for RTX export quality
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
    print("Ray tracing OFF (interactive mode) â€” set RAYTRACING=True before exporting")

# temperature background
field = OpenDataFile(f"{F}/task0.pvd")
UpdatePipeline()
fd = Show(field, view)
fd.SetRepresentationType("Surface")
ColorBy(fd, ("POINTS", "AirTemperature_C"))
fd.Opacity = 0.85

tlut = GetColorTransferFunction("AirTemperature_C")
tlut.RGBPoints = [
    -40, 0.08, 0.08, 0.38,   # deep cold   -> dark blue
    -10, 0.12, 0.28, 0.78,   # cold        -> blue
      0, 0.25, 0.55, 0.88,   # cool/ocean  -> light blue
     15, 0.45, 0.82, 0.38,   # mild        -> green
     25, 0.95, 0.88, 0.18,   # warm        -> yellow
     35, 0.95, 0.48, 0.05,   # hot         -> orange
     45, 0.85, 0.10, 0.05,   # very hot    -> red
     55, 0.55, 0.00, 0.55,   # extreme     -> white
]
tlut.ColorSpace = "Lab"
tlut.NanColor   = [0.96, 0.93, 0.86]
fd.SetScalarBarVisibility(view, True)
tsb = GetScalarBar(tlut, view)
tsb.Title           = "Air Temperature (C)"
tsb.ComponentTitle  = ""
tsb.TitleColor = [0.10, 0.10, 0.10]
tsb.LabelColor      = [0.60, 0.60, 0.60]
try:
    tsb.WindowLocation = "Any Location"
except Exception: pass
try:
    tsb.Orientation = "Horizontal"
except Exception: pass
tsb.Position        = [0.03, 0.02]
tsb.ScalarBarLength = 0.30
try:
    tsb.ScalarBarThickness = 12
except Exception: pass
try: tsb.Interactivity = 0
except Exception: pass

# CEI contour rings at 0.65 / 0.75 / 0.85
ct = Contour(Input=field)
ct.ContourBy   = ["POINTS", "CompoundExtremesIndex"]
ct.Isosurfaces = [0.65, 0.75, 0.85]
UpdatePipeline(proxy=ct)
ctd = Show(ct, view)
ctd.AmbientColor      = [0.10, 0.10, 0.40]
ctd.DiffuseColor      = [0.10, 0.10, 0.40]
ctd.LineWidth         = 1.8
ctd.Opacity           = 0.90
ctd.ColorArrayName    = ["POINTS", ""]

# critical points per year
cp_pvd = f"{CP}/task0_cp.pvd"
if os.path.exists(cp_pvd):
    cp_reader = OpenDataFile(cp_pvd)
    UpdatePipeline()

    # â”€â”€ Maxima (red) â€” only significant hotspots, CEI_Value > 0.70 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    thr_max = Threshold(Input=cp_reader)
    thr_max.Scalars = ["POINTS", "CriticalType"]
    try:
        thr_max.LowerThreshold = 2.5; thr_max.UpperThreshold = 3.5
        thr_max.ThresholdMethod = "Between"
    except Exception:
        thr_max.ThresholdRange = [2.5, 3.5]
    UpdatePipeline(proxy=thr_max)

    thr_max_val = Threshold(Input=thr_max)
    thr_max_val.Scalars = ["POINTS", "CEI_Value"]
    try:
        thr_max_val.LowerThreshold = 0.80; thr_max_val.UpperThreshold = 1.01
        thr_max_val.ThresholdMethod = "Between"
    except Exception:
        thr_max_val.ThresholdRange = [0.80, 1.01]
    UpdatePipeline(proxy=thr_max_val)

    gl_max = Glyph(Input=thr_max_val)
    gl_max.GlyphType = "Sphere"; gl_max.ScaleFactor = 2.2
    gl_max.GlyphMode = "All Points"
    gl_max.ScaleArray = ["POINTS", "No scale array"]
    gl_max.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl_max)
    d_max = Show(gl_max, view)
    # deep crimson â€” darker than the land's red-orange so dots stay visible on hot regions
    d_max.AmbientColor = [0.72, 0.02, 0.10]; d_max.DiffuseColor = [0.72, 0.02, 0.10]
    d_max.ColorArrayName = ["POINTS", ""]; d_max.Opacity = 1.0
    try:
        d_max.Interpolation = "PBR"; d_max.Roughness = 0.15; d_max.Metallic = 0.25
    except Exception: pass

    # â”€â”€ Minima (blue) â€” all of them (~250 per year, shows calm cool spots) â”€â”€â”€â”€â”€â”€â”€
    thr_min = Threshold(Input=cp_reader)
    thr_min.Scalars = ["POINTS", "CriticalType"]
    try:
        thr_min.LowerThreshold = -0.5; thr_min.UpperThreshold = 0.5
        thr_min.ThresholdMethod = "Between"
    except Exception:
        thr_min.ThresholdRange = [-0.5, 0.5]
    UpdatePipeline(proxy=thr_min)

    gl_min = Glyph(Input=thr_min)
    gl_min.GlyphType = "Sphere"; gl_min.ScaleFactor = 2.2
    gl_min.GlyphMode = "All Points"
    gl_min.ScaleArray = ["POINTS", "No scale array"]
    gl_min.OrientationArray = ["POINTS", "No orientation array"]
    UpdatePipeline(proxy=gl_min)
    d_min = Show(gl_min, view)
    # saturated navy â€” darker than the light-blue ocean so dots stay visible on water
    d_min.AmbientColor = [0.02, 0.10, 0.85]; d_min.DiffuseColor = [0.02, 0.10, 0.85]
    d_min.ColorArrayName = ["POINTS", ""]; d_min.Opacity = 1.0
    try:
        d_min.Interpolation = "PBR"; d_min.Roughness = 0.20; d_min.Metallic = 0.15
    except Exception: pass

    print("Critical points: red = CEI maxima > 0.80  |  blue = CEI minima (all)")
else:
    print("WARNING: task0_cp.pvd not found. Run extract_cp_per_timestep.py first.")

# Tracking note: the TTK pipeline (Tetrahedralize â†’ PersistenceSimplification â†’
# CriticalPoints) produces consistently-matched features across all 76 years.
# The animation of the dots IS the tracking â€” press Play to see maxima/minima
# persist and shift across 1950â†’2025. Static tube overlays from Wasserstein
# matching produce fan artifacts and are excluded from this view.
print("Tracking: animated critical points show TTK-tracked compound extremes (1950-2025)")

# coastlines and borders
G = f"{B}/task1_atmosphere/global"
for vtp_file, color, lw in [
        (f"{G}/world_coastlines.vtp", [0.15, 0.20, 0.30], 1.2),
        (f"{G}/world_countries.vtp",  [0.32, 0.38, 0.45], 0.7)]:
    if os.path.exists(vtp_file):
        coast = XMLPolyDataReader(FileName=[vtp_file])
        UpdatePipeline(proxy=coast)
        cd = Show(coast, view)
        cd.AmbientColor    = color
        cd.DiffuseColor    = color
        cd.LineWidth       = lw
        cd.Opacity         = 0.80
        cd.ColorArrayName  = ["POINTS", ""]
print("Coastlines loaded")

# year label â€” PVD timestep values are 1950..2025 so it shows the year directly
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
        ann_d.Color          = [0.10, 0.10, 0.40]
        ann_d.WindowLocation = "Upper Left Corner"
        _label_ok = True
        print(f"Year label added via {_name}")
        break
    except Exception as _e:
        print(f"  {_name}: {_e}")

if not _label_ok:
    try:
        txt = Text()
        txt.Text = "Year: 1950"
        txt_d = Show(txt, view)
        txt_d.FontSize       = 36
        txt_d.Color          = [0.10, 0.10, 0.40]
        txt_d.WindowLocation = "Upper Left Corner"
        print("Year label: static text (AnnotateTimeFilter not available)")
    except Exception as _e2:
        print(f"Year label skipped: {_e2}")

# camera and animation
view.CameraParallelProjection = 1
ResetCamera(view)

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
print(f"Animation range: {scene.StartTime} to {scene.EndTime}")

Render(view)
os.makedirs(f"{R}/stills", exist_ok=True)
SaveScreenshot(f"{R}/stills/task0_clean.png", view, ImageResolution=[2560, 1440])
print(f"Screenshot: {R}/stills/task0_clean.png")

if SAVE_ALL_FRAMES:
    _pdf_dir = f”{R}/pdf_stills/task0_frames”
    os.makedirs(_pdf_dir, exist_ok=True)
    try:
        _ts = list(scene.TimeKeeper.TimestepValues)
    except Exception:
        _ts = list(range(1950, 2026))
    _web_res = [1920, 1080]
    print(f”\nExporting ALL {len(_ts)} Task 0 frames  ->  {_pdf_dir}”)
    for _i, _t in enumerate(_ts):
        scene.AnimationTime = float(_t); UpdatePipeline(); Render(view)
        _png = f”{_pdf_dir}/frame_{_i:02d}_t{_t:.0f}.png”
        SaveScreenshot(_png, view, ImageResolution=_web_res)
        print(f”  [{_i+1}/{len(_ts)}] year {_t:.0f}”)
    print(f”Done. Run deploy_task0_frames.py to convert to WebP and publish.”)
else:
    print()
    print(“Press Play to animate critical points 1950->2025”)
    print(“Set SAVE_ALL_FRAMES=True to export all 76 frames.”)
    print(“  Red dots   = CEI maxima > 0.80  (compound extreme hot-spots)”)
    print(“  Blue dots  = CEI minima”)
    print(“  White rings= CEI contours at 0.65 / 0.75 / 0.85”)
    print(“  Background = Air temperature  |  Gray background = paper-ready”)


