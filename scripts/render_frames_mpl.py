"""
Render Task 0 and Task 3 frames using vtk + matplotlib.
Reads VTI data directly; bypasses ParaView's flat-slab Surface/Slice render bug.
Run:  python scripts/render_frames_mpl.py
"""
import os
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import vtk
from vtk.util.numpy_support import vtk_to_numpy

B       = r"D:\STUDY\RESEARCH WORKS\IIIT HYD\sciviscontest2026\##ParaView_New"
PVD     = os.path.join(B, "task0_climate", "frames", "task0.pvd")
PVD_DIR = os.path.dirname(PVD)
G       = os.path.join(B, "task1_atmosphere", "global")
R       = os.path.join(B, "renders")
BG      = (0.96, 0.93, 0.86)   # cream — same as Task 1


# ── Parse PVD ─────────────────────────────────────────────────────────────────
datasets = sorted(
    [(float(d.get("timestep", 0)), d.get("file"))
     for d in ET.parse(PVD).findall(".//DataSet")],
    key=lambda x: x[0]
)
print(f"PVD: {len(datasets)} timesteps")


# ── Colormaps ─────────────────────────────────────────────────────────────────
def make_cmap(pts, name):
    vmin, vmax = pts[0][0], pts[-1][0]
    nv = [(v - vmin) / (vmax - vmin) for v, _ in pts]
    cd = {'red': [], 'green': [], 'blue': []}
    for n, (_, (r, g, b)) in zip(nv, pts):
        cd['red'].append((n, r, r))
        cd['green'].append((n, g, g))
        cd['blue'].append((n, b, b))
    cm = LinearSegmentedColormap(name, cd, N=512)
    cm.set_bad(color=BG)
    return cm, vmin, vmax

TEMP_CMAP, T_MIN, T_MAX = make_cmap([
    (-40, (0.08, 0.08, 0.38)), (-10, (0.12, 0.28, 0.78)),
    (  0, (0.25, 0.55, 0.88)), ( 15, (0.45, 0.82, 0.38)),
    ( 25, (0.95, 0.88, 0.18)), ( 35, (0.95, 0.48, 0.05)),
    ( 45, (0.85, 0.10, 0.05)), ( 55, (0.55, 0.00, 0.55)),
], "temp")

CEI_CMAP, C_MIN, C_MAX = make_cmap([
    (0.20, (0.25, 0.55, 0.88)), (0.45, (0.35, 0.68, 0.70)),
    (0.60, (0.45, 0.82, 0.38)), (0.72, (0.95, 0.88, 0.18)),
    (0.82, (0.95, 0.48, 0.05)), (0.90, (0.85, 0.10, 0.05)),
    (0.97, (0.55, 0.00, 0.55)),
], "dhmi")


# ── VTI reader ────────────────────────────────────────────────────────────────
def read_vti(path, *names):
    r = vtk.vtkXMLImageDataReader()
    r.SetFileName(path); r.Update()
    d = r.GetOutput()
    nx, ny, nz = d.GetDimensions()
    bds = d.GetBounds()
    out = {}
    for name in names:
        a = d.GetPointData().GetArray(name)
        out[name] = vtk_to_numpy(a).reshape(nz, ny, nx)[0] if a else None
    return out, bds


# ── Coastlines ────────────────────────────────────────────────────────────────
def load_vtp(path):
    if not os.path.exists(path):
        return []
    r = vtk.vtkXMLPolyDataReader(); r.SetFileName(path); r.Update()
    poly = r.GetOutput()
    pts  = poly.GetPoints()
    if pts is None: return []
    coords = vtk_to_numpy(pts.GetData())
    lines  = poly.GetLines()
    if lines is None: return []
    lines.InitTraversal(); segs = []; id_list = vtk.vtkIdList()
    while lines.GetNextCell(id_list):
        segs.append([(coords[id_list.GetId(j), 0], coords[id_list.GetId(j), 1])
                     for j in range(id_list.GetNumberOfIds())])
    return segs

coast   = load_vtp(os.path.join(G, "world_coastlines.vtp"))
borders = load_vtp(os.path.join(G, "world_countries.vtp"))
print(f"Coastlines: {len(coast)} segs  Borders: {len(borders)} segs")


# ── Draw coastlines helper ────────────────────────────────────────────────────
def draw_coasts(ax):
    for seg in coast:
        ax.plot([p[0] for p in seg], [p[1] for p in seg],
                color=(0.15, 0.20, 0.30), lw=0.9, alpha=0.85, rasterized=True)
    for seg in borders:
        ax.plot([p[0] for p in seg], [p[1] for p in seg],
                color=(0.32, 0.38, 0.45), lw=0.4, alpha=0.55, rasterized=True)


# ── Render one frame ──────────────────────────────────────────────────────────
def render_frame(arr_bg, cmap, vmin, vmax, bds, t_int,
                 overlay_arr, overlay_levels, cbar_label, out_png):
    lon0, lon1, lat0, lat1 = bds[0], bds[1], bds[2], bds[3]
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
    ax  = fig.add_axes([0, 0, 1, 1], facecolor=BG)

    im = ax.imshow(arr_bg, origin='lower',
                   extent=[lon0, lon1, lat0, lat1],
                   cmap=cmap, vmin=vmin, vmax=vmax,
                   aspect='auto', interpolation='bilinear',
                   rasterized=True)

    if overlay_arr is not None and overlay_levels:
        lons = np.linspace(lon0, lon1, arr_bg.shape[1])
        lats = np.linspace(lat0, lat1, arr_bg.shape[0])
        try:
            ax.contour(lons, lats, overlay_arr, levels=overlay_levels,
                       colors=[(0.10, 0.10, 0.40)], linewidths=1.4, alpha=0.85)
        except Exception:
            pass

    draw_coasts(ax)

    # colorbar
    cax = fig.add_axes([0.03, 0.055, 0.26, 0.020])
    cb  = plt.colorbar(im, cax=cax, orientation='horizontal')
    cb.set_label(cbar_label, color=(0.10, 0.10, 0.10), fontsize=9)
    cb.ax.tick_params(colors=(0.15, 0.15, 0.15), labelsize=7)

    # year label
    ax.text(0.012, 0.97, f"Year: {t_int}",
            transform=ax.transAxes, fontsize=28,
            color=(0.10, 0.10, 0.40), va='top', ha='left',
            fontweight='bold', fontfamily='monospace')

    ax.set_xlim(lon0, lon1); ax.set_ylim(lat0, lat1); ax.axis('off')
    fig.savefig(out_png, dpi=100, bbox_inches=None, facecolor=BG, pad_inches=0)
    plt.close(fig)


# ── Task 0: temperature + CEI contours ───────────────────────────────────────
t0_dir = os.path.join(R, "pdf_stills", "task0_frames")
os.makedirs(t0_dir, exist_ok=True)
print(f"\n=== Task 0: {len(datasets)} frames -> {t0_dir}")

for idx, (t, fname) in enumerate(datasets):
    t_int = int(round(t))
    out   = os.path.join(t0_dir, f"frame_{idx:02d}_t{t_int}.png")
    vti   = os.path.join(PVD_DIR, fname) if fname else ""
    if not os.path.exists(vti):
        print(f"  MISSING {fname}"); continue

    arrays, bds = read_vti(vti, "AirTemperature_C", "CompoundExtremesIndex")
    temp = arrays["AirTemperature_C"]
    cei  = arrays["CompoundExtremesIndex"]
    if temp is None:
        print(f"  AirTemperature_C missing in {fname}"); continue

    render_frame(temp, TEMP_CMAP, T_MIN, T_MAX, bds, t_int,
                 cei, [0.65, 0.75, 0.85], "Air Temperature (C)", out)

    if (idx % 10 == 0) or (idx == len(datasets) - 1):
        kb = os.path.getsize(out) // 1024
        print(f"  [{idx+1}/{len(datasets)}] year {t_int}  {kb} KB")

print("Task 0 done.")


# ── Task 3 (cross-task): DHMI / CEI field ─────────────────────────────────────
t3_dir = os.path.join(R, "pdf_stills", "task3_frames")
os.makedirs(t3_dir, exist_ok=True)
print(f"\n=== Task 3: {len(datasets)} frames -> {t3_dir}")

for idx, (t, fname) in enumerate(datasets):
    t_int = int(round(t))
    out   = os.path.join(t3_dir, f"frame_{idx:02d}_t{t_int}.png")
    vti   = os.path.join(PVD_DIR, fname) if fname else ""
    if not os.path.exists(vti):
        print(f"  MISSING {fname}"); continue

    arrays, bds = read_vti(vti, "CompoundExtremesIndex")
    cei = arrays["CompoundExtremesIndex"]
    if cei is None:
        print(f"  CompoundExtremesIndex missing in {fname}"); continue

    render_frame(cei, CEI_CMAP, C_MIN, C_MAX, bds, t_int,
                 None, None, "DHMI Compound Extremes Index", out)

    if (idx % 10 == 0) or (idx == len(datasets) - 1):
        kb = os.path.getsize(out) // 1024
        print(f"  [{idx+1}/{len(datasets)}] year {t_int}  {kb} KB")

print("Task 3 done.")
print("\nNow run: python scratchpad/deploy_task0_and_3_frames.py")
