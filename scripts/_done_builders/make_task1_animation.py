#!/usr/bin/env python
# TASK 1 — polished global jet-stream animation
# Proper gnomonic cubed-sphere reprojection -> lat/lon grid
# + cartopy world map + streamlines + 16-frame MP4
# Output: renders/task1_animation.mp4

import numpy as np, os, subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter

B       = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026"
RAW     = f"{B}/data/task1_geos_fullres"
OUT_DIR = f"{B}/##ParaView_New/renders"
TMP_DIR = f"{B}/##ParaView_New/renders/task1_frames"
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

N   = 1440   # face pixels per side
NF  = 16     # time steps

# Output lat/lon grid
NLAT, NLON = 360, 720
lats = np.linspace(-89.75, 89.75, NLAT)
lons = np.linspace(-179.75, 179.75, NLON)

# ─── Gnomonic equiangular cubed-sphere → lat/lon reprojection ─────────────────

def _pq_to_pix(p, q, N):
    """Equiangular gnomonic (p,q) in [-1,1] → float pixel coords in [0,N)."""
    alpha = np.arctan(np.clip(p, -1.0, 1.0))
    beta  = np.arctan(np.clip(q, -1.0, 1.0))
    i = (alpha / (np.pi / 4) + 1.0) * 0.5 * N - 0.5
    j = (beta  / (np.pi / 4) + 1.0) * 0.5 * N - 0.5
    return i, j


def reproject_one(face_arrays, N=N):
    """
    face_arrays: list of 6 (N,N) arrays for one timestep.
    Returns global (NLAT, NLON) array using gnomonic equiangular projection.
    Face normals: 0=+X, 1=+Y, 2=-X, 3=-Y, 4=+Z (north), 5=-Z (south).
    """
    LON_g, LAT_g = np.meshgrid(lons, lats)
    lr = np.radians(LON_g); lr2 = np.radians(LAT_g)
    X = np.cos(lr2) * np.cos(lr)
    Y = np.cos(lr2) * np.sin(lr)
    Z = np.sin(lr2)
    aX, aY, aZ = np.abs(X), np.abs(Y), np.abs(Z)

    out = np.zeros((NLAT, NLON), np.float32)

    face_defs = [
        # (mask_expr, p_expr, q_expr)
        # Face 0: +X dominant
        (lambda: (X > 0) & (X >= aY) & (X >= aZ),
         lambda m: Y[m] / X[m], lambda m: Z[m] / X[m]),
        # Face 1: +Y dominant
        (lambda: (Y > 0) & (Y > aX) & (Y >= aZ),
         lambda m: -X[m] / Y[m], lambda m: Z[m] / Y[m]),
        # Face 2: -X dominant  (q uses -Z/X so North is positive)
        (lambda: (X < 0) & (-X > aY) & (-X > aZ),
         lambda m: Y[m] / X[m], lambda m: -Z[m] / X[m]),
        # Face 3: -Y dominant  (q uses -Z/Y so North is positive)
        (lambda: (Y < 0) & (-Y > aX) & (-Y >= aZ),
         lambda m: -X[m] / Y[m], lambda m: -Z[m] / Y[m]),
        # Face 4: +Z dominant (north polar)
        (lambda: (Z > 0) & (Z > aX) & (Z > aY),
         lambda m: X[m] / Z[m], lambda m: Y[m] / Z[m]),
        # Face 5: -Z dominant (south polar)
        (lambda: (Z < 0) & (-Z > aX) & (-Z > aY),
         lambda m: X[m] / (-Z[m]), lambda m: Y[m] / (-Z[m])),
    ]

    for f, (mask_fn, p_fn, q_fn) in enumerate(face_defs):
        m   = mask_fn()
        p   = p_fn(m)
        q   = q_fn(m)
        fi, fj = _pq_to_pix(p, q, N)

        face = face_arrays[f]
        fi = np.clip(fi, 0, N - 1.001)
        fj = np.clip(fj, 0, N - 1.001)
        i0 = fi.astype(int); i1 = np.minimum(i0 + 1, N - 1)
        j0 = fj.astype(int); j1 = np.minimum(j0 + 1, N - 1)
        wi = fi - i0;  wj = fj - j0

        vals = ((1-wi)*(1-wj)*face[j0, i0]
              + wi   *(1-wj)*face[j0, i1]
              + (1-wi)*  wj *face[j1, i0]
              + wi   *  wj *face[j1, i1])
        out[m] = vals

    return out

# ─── Load and reproject all timesteps ─────────────────────────────────────────

print("Loading GEOS face data ...")
u_faces = [np.load(f"{RAW}/u_face{f}.npy") for f in range(6)]   # (16,1440,1440)
v_faces = [np.load(f"{RAW}/v_face{f}.npy") for f in range(6)]
print(f"  shape: {u_faces[0].shape}  u-range: {u_faces[0].min():.1f}..{u_faces[0].max():.1f}")

U_all = np.zeros((NF, NLAT, NLON), np.float32)
V_all = np.zeros((NF, NLAT, NLON), np.float32)

CACHE_U = f"{B}/_reproj_tmp/U_all.npy"
CACHE_V = f"{B}/_reproj_tmp/V_all.npy"

if os.path.exists(CACHE_U) and os.path.exists(CACHE_V):
    print("Loading cached reprojected arrays...")
    U_all = np.load(CACHE_U)
    V_all = np.load(CACHE_V)
    # Re-apply smoothing (more than before to hide face seams)
    for t in range(NF):
        U_all[t] = gaussian_filter(U_all[t], sigma=6)
        V_all[t] = gaussian_filter(V_all[t], sigma=6)
    print("  Done.")
else:
    for t in range(NF):
        print(f"  Reprojecting t{t:02d}/{NF-1} ...", end="", flush=True)
        U_all[t] = reproject_one([u_faces[f][t] for f in range(6)])
        V_all[t] = reproject_one([v_faces[f][t] for f in range(6)])
        spd_max = np.sqrt(U_all[t]**2 + V_all[t]**2).max()
        print(f"  speed_max={spd_max:.1f} m/s")
    os.makedirs(f"{B}/_reproj_tmp", exist_ok=True)
    np.save(CACHE_U, U_all)
    np.save(CACHE_V, V_all)
    print("  Cached raw arrays.")
    # Apply smoothing
    for t in range(NF):
        U_all[t] = gaussian_filter(U_all[t], sigma=6)
        V_all[t] = gaussian_filter(V_all[t], sigma=6)

speed_all = np.sqrt(U_all**2 + V_all**2)
vmax_global = float(np.percentile(speed_all, 99.5))
print(f"\nGlobal 99.5th percentile wind speed: {vmax_global:.1f} m/s\n")

# ─── Cartopy features (load once) ─────────────────────────────────────────────

PROJ    = ccrs.PlateCarree()
land    = cfeature.NaturalEarthFeature("physical", "land", "110m",
                                        facecolor="#0d1520", edgecolor="none")
coast   = cfeature.NaturalEarthFeature("physical", "coastline", "110m",
                                        facecolor="none", edgecolor="#3a5070")
borders = cfeature.NaturalEarthFeature("cultural", "admin_0_boundary_lines_land",
                                        "110m", facecolor="none", edgecolor="#1e2a40")

# Custom colormap: deep blue-black for calm, vivid magenta/yellow for jet
JET_CMAP = mcolors.LinearSegmentedColormap.from_list("jet_wind", [
    "#040810",   # 0 m/s  — near black
    "#091840",   # 10     — deep navy
    "#1a3a80",   # 20     — royal blue
    "#0e6ea8",   # 30     — ocean blue
    "#22b0c0",   # 40     — cyan
    "#66cc44",   # 50     — green
    "#ddcc00",   # 60     — yellow-gold
    "#ff8800",   # 70     — amber
    "#ff2200",   # 80     — red
    "#ffffff",   # 90+    — white core
], N=256)

NORM = mcolors.Normalize(vmin=0, vmax=min(vmax_global, 90))

# Subsampling stride for streamplot (needs regular grid, best with ~90×45 pts)
SS = 8   # every 8 grid cells → 90×45

lats_s = lats[::SS]
lons_s = lons[::SS]

# ─── Render frames ────────────────────────────────────────────────────────────

for t in range(NF):
    print(f"Rendering frame {t:02d}/{NF-1} ...", end="", flush=True)

    U = U_all[t]; V = V_all[t]; spd = speed_all[t]
    U_s = U[::SS, ::SS]; V_s = V[::SS, ::SS]; spd_s = spd[::SS, ::SS]

    fig = plt.figure(figsize=(18, 9.5), facecolor="#04080f")
    ax  = fig.add_subplot(1, 1, 1, projection=PROJ)
    ax.set_global()
    ax.set_facecolor("#04080f")
    ax.set_extent([-180, 180, -90, 90], crs=PROJ)

    # 1. Ocean fill
    ax.add_feature(cfeature.OCEAN, facecolor="#04080f", zorder=0)

    # 2. Wind speed background
    LON_2d, LAT_2d = np.meshgrid(lons, lats)
    cf = ax.contourf(LON_2d, LAT_2d, spd,
                     levels=np.linspace(0, 90, 64),
                     cmap=JET_CMAP, norm=NORM,
                     extend="max", transform=PROJ, zorder=1)

    # 3. Land overlay (dark, semi-transparent so wind shows through borders)
    ax.add_feature(land, zorder=2, alpha=0.45)

    # 4. Jet stream glow: bright filled band at 50–90+ m/s
    ax.contourf(LON_2d, LAT_2d, spd,
                levels=[55, 65, 75, 90],
                colors=["#ffd700aa", "#ffaa00bb", "#ffffff88"],
                transform=PROJ, zorder=3, alpha=0.55)

    # 5. Jet stream contour lines
    cs = ax.contour(LON_2d, LAT_2d, spd,
                    levels=[40, 55, 70],
                    colors=["#88aaff", "#ffd700", "#ffffff"],
                    linewidths=[0.6, 1.2, 2.0],
                    transform=PROJ, zorder=4, alpha=0.85)

    # 6. Streamlines (subsampled grid, compatible with cartopy PlateCarree)
    lw_s = np.clip(spd_s / 25.0, 0.3, 3.0)
    try:
        strm = ax.streamplot(lons_s, lats_s, U_s, V_s,
                             color=spd_s, cmap="YlOrRd",
                             linewidth=lw_s,
                             density=[2.0, 1.2],
                             arrowstyle="-", arrowsize=0.5,
                             transform=PROJ, zorder=5,
                             norm=mcolors.Normalize(0, 80))
    except Exception:
        # Fallback: quiver if streamplot fails with cartopy
        ax.quiver(lons_s, lats_s, U_s, V_s,
                  spd_s, cmap="YlOrRd", norm=mcolors.Normalize(0, 80),
                  scale=2500, width=0.0015,
                  transform=PROJ, zorder=5, alpha=0.8)

    # 7. Coastlines and borders
    ax.add_feature(coast, linewidth=0.7, zorder=6)
    ax.add_feature(borders, linewidth=0.35, zorder=6)

    # 8. Grid lines
    gl = ax.gridlines(draw_labels=False, linewidth=0.25, color="#1a2840",
                      alpha=0.7, linestyle="--", zorder=7)
    gl.xlocator = plt.FixedLocator(range(-180, 181, 30))
    gl.ylocator = plt.FixedLocator(range(-90, 91, 30))

    # 9. Colorbar
    sm = plt.cm.ScalarMappable(cmap=JET_CMAP, norm=NORM)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal",
                        fraction=0.028, pad=0.035, shrink=0.55, aspect=35,
                        ticks=[0, 20, 40, 60, 80])
    cbar.set_label("Wind Speed  (m/s)", color="#9aadc0", fontsize=11)
    cbar.ax.tick_params(colors="#9aadc0", labelsize=9)
    cbar.ax.set_facecolor("#04080f")
    cbar.outline.set_edgecolor("#2a3a55")

    # 10. Title and step label
    ax.set_title("Global Jet Streams · GEOS-FP Atmosphere",
                 color="#d0e4f7", fontsize=17, fontweight="bold", pad=10,
                 path_effects=[pe.withStroke(linewidth=2, foreground="#04080f")])
    ax.text(0.985, 0.975, f"Step {t+1:02d} / {NF}",
            transform=ax.transAxes, ha="right", va="top",
            color="#ffd166", fontsize=14, fontweight="bold",
            path_effects=[pe.withStroke(linewidth=3, foreground="#04080f")])
    fig.text(0.5, 0.01,
             "IEEE SciVis Contest 2026  ·  Task 1  ·  GEOS-FP Surface Winds",
             ha="center", color="#3a5070", fontsize=9.5)

    # Reduce whitespace
    fig.subplots_adjust(left=0.005, right=0.995, top=0.94, bottom=0.06)

    fp = f"{TMP_DIR}/frame_{t:02d}.png"
    fig.savefig(fp, dpi=120, bbox_inches="tight", facecolor="#04080f")
    plt.close(fig)
    print(f"  saved {fp}")

# ─── Combine with ffmpeg ───────────────────────────────────────────────────────

out_mp4 = f"{OUT_DIR}/task1_animation.mp4"
cmd = (
    f'ffmpeg -y -framerate 3 -i "{TMP_DIR}/frame_%02d.png"'
    f' -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p'
    f' -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"'
    f' "{out_mp4}"'
)
print(f"\nCombining frames -> {out_mp4}")
subprocess.run(cmd, shell=True, check=True)

# Also save first frame as hero image
import shutil
shutil.copy(f"{TMP_DIR}/frame_00.png",
            f"{B}/##ParaView_New/renders/task1_jetstream_hero.png")
print(f"Hero image: renders/task1_jetstream_hero.png")
print(f"Animation:  renders/task1_animation.mp4  ({NF} frames, 3 fps)")
