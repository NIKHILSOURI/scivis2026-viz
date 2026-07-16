#!/usr/bin/env python
"""
build_pd_trajectories.py  — pure Python (no pvpython required)

Implements what TTKTrackingFromPersistenceDiagrams does, but in Python because
that TTK filter crashes in PV 6.1.1.

Algorithm (same as Lacombe et al. 2018 / TTK PD tracking):
  For each consecutive pair of persistence diagrams (PD_t, PD_{t+1}):
    1. Extract finite saddle-max pairs (PairType==1) from both diagrams.
       Each pair = (Birth, Death) in topological space + (x_max, y_max) in domain.
    2. Build cost matrix:
         cost(i,j) = alpha * ||p_i - p_j||_BD + (1-alpha) * ||pos_i - pos_j|| / scale
       where BD-distance is L2 in (Birth, Death) space and pos is geographic (lon,lat).
    3. Add "death" rows/columns: unmatched pairs are sent to the diagonal
       (cost = persistence/2 = distance to diagonal in L∞ norm).
    4. Run Hungarian matching (scipy.optimize.linear_sum_assignment).
    5. Filter matches by maximum allowable cost.
  Chain matched pairs across time → trajectory polylines.

Run:
  python scripts/build_pd_trajectories.py

Outputs (in ##ParaView_New/outputs/):
  task0_pd_trajectories.vtp   — polylines coloured by EventType (same encoding as Hungarian)
  task0_pd_nodes.vtp          — per-point spheres for event markers
"""
import os, sys, numpy as np, vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from scipy.optimize import linear_sum_assignment

B       = "D:/STUDY/RESEARCH WORKS/IIIT HYD/sciviscontest2026/##ParaView_New"
PD_DIR  = f"{B}/task0_climate/persistence_diagrams"
OUT     = f"{B}/outputs"
os.makedirs(OUT, exist_ok=True)

# ── Matching hyper-parameters ─────────────────────────────────────────────────
ALPHA        = 0.6    # weight on topological (BD) distance vs geographic distance
GEO_SCALE    = 30.0   # normalise geographic distance (degrees)
MAX_COST     = 0.30   # reject matches above this total cost
DIAG_PENALTY = None   # auto: half the persistence of each unmatched pair
MIN_PERSIST  = 0.04   # only track pairs with persistence > threshold
MIN_LEN      = 2      # minimum trajectory length (timesteps)
SPLIT_THRESH = 8.0    # degrees for near-split/merge detection

# ── Load one PD VTP → list of dicts {birth, death, persist, x, y} ─────────────
def load_pd(path):
    r = vtk.vtkXMLUnstructuredGridReader()
    r.SetFileName(path)
    r.Update()
    obj = r.GetOutput()
    if obj.GetNumberOfCells() == 0:
        return []

    pdd = obj.GetPointData()
    cdd = obj.GetCellData()

    ct       = vtk_to_numpy(pdd.GetArray("CriticalType"))
    coords   = vtk_to_numpy(pdd.GetArray("Coordinates"))    # (x,y,z) per point
    birth_a  = vtk_to_numpy(cdd.GetArray("Birth"))
    persist_a= vtk_to_numpy(cdd.GetArray("Persistence"))
    ptype_a  = vtk_to_numpy(cdd.GetArray("PairType"))
    finite_a = vtk_to_numpy(cdd.GetArray("IsFinite"))

    pairs = []
    for c in range(obj.GetNumberOfCells()):
        if ptype_a[c] != 1:
            continue          # only saddle-max pairs
        if not finite_a[c]:
            continue          # skip the infinite pair
        b = float(birth_a[c])
        p = float(persist_a[c])
        d = b + p             # Death = Birth + Persistence
        if p < MIN_PERSIST:
            continue          # noise

        # find which point is the maximum (CriticalType==3)
        cell = obj.GetCell(c)
        pid0, pid1 = cell.GetPointId(0), cell.GetPointId(1)
        if int(ct[pid1]) == 3:
            max_pid = pid1
        else:
            max_pid = pid0
        x_max = float(coords[max_pid, 0])
        y_max = float(coords[max_pid, 1])
        pairs.append(dict(birth=b, death=d, persist=p, x=x_max, y=y_max))
    return pairs

# ── Optimal assignment between two PDs with diagonal "death" option ────────────
def match_pds(pA, pB):
    """Return list of (iA, iB) matches (both -1 = unmatched on diagonal)."""
    nA, nB = len(pA), len(pB)
    if nA == 0 or nB == 0:
        return []

    A_bd  = np.array([[p["birth"], p["death"]]  for p in pA])  # (nA,2)
    B_bd  = np.array([[p["birth"], p["death"]]  for p in pB])
    A_pos = np.array([[p["x"],     p["y"]]      for p in pA])
    B_pos = np.array([[p["x"],     p["y"]]      for p in pB])

    # cost between actual pair i and pair j
    bd_dist  = np.sqrt(((A_bd[:, None] - B_bd[None, :]) ** 2).sum(-1))  # (nA,nB)
    geo_dist = np.sqrt(((A_pos[:, None] - B_pos[None, :]) ** 2).sum(-1)) / GEO_SCALE
    cost_real = ALPHA * bd_dist + (1 - ALPHA) * geo_dist                 # (nA,nB)

    # cost of sending pair i to its diagonal projection
    diag_A = np.array([p["persist"] / 2.0 for p in pA])  # (nA,)
    diag_B = np.array([p["persist"] / 2.0 for p in pB])  # (nB,)

    # Build augmented cost matrix with diagonal sinks
    # size: (nA + nB) x (nA + nB)
    n = nA + nB
    C = np.full((n, n), 1e9)
    C[:nA, :nB] = cost_real          # A→B
    for i in range(nA):
        C[i, nB + i] = diag_A[i]    # A_i → diagonal
    for j in range(nB):
        C[nA + j, j] = diag_B[j]    # diagonal → B_j
    # diagonal→diagonal is free
    for k in range(max(nA, nB)):
        if nA + k < n and nB + k < n:
            C[nA + k, nB + k] = 0.0

    ri, ci = linear_sum_assignment(C)
    matches = []
    for i, j in zip(ri, ci):
        iA = i if i < nA else -1
        iB = j if j < nB else -1
        if iA == -1 and iB == -1:
            continue
        raw_cost = C[i, j]
        if raw_cost > MAX_COST:
            continue
        matches.append((iA, iB))
    return matches

# ── Load all PDs ──────────────────────────────────────────────────────────────
pd_files = sorted(f for f in os.listdir(PD_DIR)
                  if f.startswith("pd_t") and f.endswith(".vtp"))
N = len(pd_files)
print(f"Loading {N} persistence diagrams ...")
frames = [load_pd(f"{PD_DIR}/{f}") for f in pd_files]
for i, fr in enumerate(frames):
    print(f"  t{i:02d}: {len(fr)} finite saddle-max pairs (persist>={MIN_PERSIST})")

# ── Match consecutive diagrams ─────────────────────────────────────────────────
print("\nMatching consecutive PDs (Wasserstein-like) ...")
fwd = [dict() for _ in range(N)]   # fwd[t][i] = j in t+1
for t in range(N - 1):
    matches = match_pds(frames[t], frames[t + 1])
    for iA, iB in matches:
        if iA >= 0 and iB >= 0:
            fwd[t][iA] = iB
    n_match = sum(1 for iA, iB in matches if iA >= 0 and iB >= 0)
    print(f"  t{t:02d}→t{t+1:02d}: {len(frames[t])} → {len(frames[t+1])} "
          f"pairs   matched={n_match}")

# ── Chain to trajectories ──────────────────────────────────────────────────────
incoming = [set() for _ in range(N)]
for t in range(N - 1):
    for i, j in fwd[t].items():
        incoming[t + 1].add(j)

trajectories = []
for t0 in range(N):
    for i0 in range(len(frames[t0])):
        if i0 in incoming[t0]:
            continue
        chain, t, i = [], t0, i0
        while True:
            chain.append((t, i))
            if t < N - 1 and i in fwd[t]:
                i = fwd[t][i]; t += 1
            else:
                break
        if len(chain) >= MIN_LEN:
            trajectories.append(chain)

print(f"\n{len(trajectories)} trajectories (>= {MIN_LEN} steps)")

# ── Event detection (same logic as build_trajectories.py) ─────────────────────
chain_starts = {tid: (chain[0][0], frames[chain[0][0]][chain[0][1]]["x"],
                      frames[chain[0][0]][chain[0][1]]["y"])
                for tid, chain in enumerate(trajectories)}

def event_type(tid, pos, chain):
    t, i = chain[pos]
    is_start = (pos == 0)
    is_end   = (pos == len(chain) - 1)
    if is_start and t > 0:
        t0, x0, y0 = chain_starts[tid]
        for tid2, (t2, x2, y2) in chain_starts.items():
            if tid2 != tid and t2 == t0:
                if np.hypot(x0 - x2, y0 - y2) < SPLIT_THRESH:
                    return 3  # Split
        return 1  # Creation
    if is_end and t < N - 1:
        p = frames[t][i]
        for tid2, chain2 in enumerate(trajectories):
            if tid2 == tid:
                continue
            t2e, i2e = chain2[-1]
            if t2e == t < N - 1:
                p2 = frames[t2e][i2e]
                if np.hypot(p["x"] - p2["x"], p["y"] - p2["y"]) < SPLIT_THRESH:
                    return 4  # Merge
        return 2  # Destruction
    return 0  # Continuation

ev_counts = [0, 0, 0, 0, 0]

# ── Write trajectories VTP ────────────────────────────────────────────────────
pts     = vtk.vtkPoints()
lines   = vtk.vtkCellArray()
a_tid   = vtk.vtkIntArray();   a_tid.SetName("TrajectoryID")
a_ts    = vtk.vtkIntArray();   a_ts.SetName("TimeStep")
a_birth = vtk.vtkFloatArray(); a_birth.SetName("Birth")
a_death = vtk.vtkFloatArray(); a_death.SetName("Death")
a_pers  = vtk.vtkFloatArray(); a_pers.SetName("Persistence")
a_event = vtk.vtkIntArray();   a_event.SetName("EventType")

pid = 0
for tid, chain in enumerate(trajectories):
    lines.InsertNextCell(len(chain))
    for pos, (t, i) in enumerate(chain):
        p = frames[t][i]
        pts.InsertNextPoint(p["x"], p["y"], 0.01)
        ev = event_type(tid, pos, chain)
        ev_counts[ev] += 1
        a_tid.InsertNextValue(tid)
        a_ts.InsertNextValue(t)
        a_birth.InsertNextValue(p["birth"])
        a_death.InsertNextValue(p["death"])
        a_pers.InsertNextValue(p["persist"])
        a_event.InsertNextValue(ev)
        lines.InsertCellPoint(pid); pid += 1

poly = vtk.vtkPolyData()
poly.SetPoints(pts); poly.SetLines(lines)
for a in (a_tid, a_ts, a_birth, a_death, a_pers, a_event):
    poly.GetPointData().AddArray(a)
poly.GetPointData().SetActiveScalars("EventType")
w = vtk.vtkXMLPolyDataWriter()
w.SetFileName(f"{OUT}/task0_pd_trajectories.vtp")
w.SetInputData(poly); w.Write()

# ── Write nodes VTP ───────────────────────────────────────────────────────────
npts  = vtk.vtkPoints()
verts = vtk.vtkCellArray()
n_ts    = vtk.vtkIntArray();   n_ts.SetName("TimeStep")
n_b     = vtk.vtkFloatArray(); n_b.SetName("Birth")
n_d     = vtk.vtkFloatArray(); n_d.SetName("Death")
n_event = vtk.vtkIntArray();   n_event.SetName("EventType")
k = 0
for tid, chain in enumerate(trajectories):
    for pos, (t, i) in enumerate(chain):
        p = frames[t][i]
        npts.InsertNextPoint(p["x"], p["y"], 0.02)
        verts.InsertNextCell(1); verts.InsertCellPoint(k); k += 1
        n_ts.InsertNextValue(t)
        n_b.InsertNextValue(p["birth"])
        n_d.InsertNextValue(p["death"])
        n_event.InsertNextValue(event_type(tid, pos, chain))

npoly = vtk.vtkPolyData()
npoly.SetPoints(npts); npoly.SetVerts(verts)
for a in (n_ts, n_b, n_d, n_event):
    npoly.GetPointData().AddArray(a)
npoly.GetPointData().SetActiveScalars("EventType")
w2 = vtk.vtkXMLPolyDataWriter()
w2.SetFileName(f"{OUT}/task0_pd_nodes.vtp")
w2.SetInputData(npoly); w2.Write()

print(f"\nEvents: {ev_counts[1]} creation, {ev_counts[2]} destruction, "
      f"{ev_counts[3]} split, {ev_counts[4]} merge, {ev_counts[0]} continuation")
print(f"Wrote task0_pd_trajectories.vtp ({len(trajectories)} tracks, {pid} pts)")
print(f"Wrote task0_pd_nodes.vtp ({npoly.GetNumberOfPoints()} nodes)")
print("\nTo use in viz_task0.py: change TTK_TRACKS to task0_pd_trajectories.vtp")
