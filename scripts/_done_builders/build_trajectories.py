#!/usr/bin/env python
# STAGE B (python + scipy + vtk): match maxima across time (optimal assignment)
# and build trajectory polylines + node points as .vtp.
# Now includes topological event detection: Creation, Continuation, Destruction,
# near-Split, near-Merge — these are encoded as EventType per point.
#
# EventType values:
#   0 = Continuation   (middle of a track)
#   1 = Creation       (track appears at t > 0, i.e. feature born mid-series)
#   2 = Destruction    (track ends at t < N-1, i.e. feature vanishes)
#   3 = Split          (two tracks start close together after being near one source)
#   4 = Merge          (two tracks end close together before merging to one successor)
#
# args: MAXNPZ OUTDIR TAG  [TOPN DMAX MINLEN]
import sys, numpy as np
from scipy.optimize import linear_sum_assignment
import vtk

NPZ, OUTDIR, TAG = sys.argv[1], sys.argv[2], sys.argv[3]
TOPN   = int(sys.argv[4])   if len(sys.argv) > 4 else 15
DMAX   = float(sys.argv[5]) if len(sys.argv) > 5 else 25.0
MINLEN = int(sys.argv[6])   if len(sys.argv) > 6 else 2
SPLIT_THRESH = 8.0   # degrees — two chain-starts within this → near-Split

d = np.load(NPZ)
N = int(d["nsteps"][0])

# top-N strongest maxima per time step
frames = []
for t in range(N):
    x, y, v = d[f"x_{t}"], d[f"y_{t}"], d[f"v_{t}"]
    order = np.argsort(v)[::-1][:TOPN]
    frames.append(np.column_stack([x[order], y[order], v[order]]))

# optimal assignment between consecutive frames (gated)
fwd = [dict() for _ in range(N)]      # fwd[t][i] = j in t+1
for t in range(N - 1):
    A, B = frames[t], frames[t + 1]
    if len(A) == 0 or len(B) == 0:
        continue
    cost = np.sqrt(((A[:, None, :2] - B[None, :, :2]) ** 2).sum(-1))
    ri, ci = linear_sum_assignment(cost)
    for i, j in zip(ri, ci):
        if cost[i, j] <= DMAX:
            fwd[t][i] = j

# build trajectories by following chains
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
        if len(chain) >= MINLEN:
            trajectories.append(chain)

print(f"{TAG}: {len(trajectories)} trajectories (>= {MINLEN} steps), "
      f"top-{TOPN}/step, gate {DMAX} deg")

# ── Event detection ────────────────────────────────────────────────────────────
# Collect start positions of all chains (for split detection)
chain_starts = {}  # tid -> (t0, x0, y0)
for tid, chain in enumerate(trajectories):
    t0, i0 = chain[0]
    x0, y0 = frames[t0][i0][0], frames[t0][i0][1]
    chain_starts[tid] = (t0, x0, y0)

# For each chain, tag each point with EventType
def get_event_type(tid, pos_in_chain, chain):
    t, i = chain[pos_in_chain]
    is_start = (pos_in_chain == 0)
    is_end   = (pos_in_chain == len(chain) - 1)

    if is_start and t > 0:
        # Check if any other chain also starts at t0 nearby → Split
        t0, x0, y0 = chain_starts[tid]
        for tid2, (t2, x2, y2) in chain_starts.items():
            if tid2 == tid:
                continue
            if t2 == t0:
                dist = np.sqrt((x0 - x2)**2 + (y0 - y2)**2)
                if dist < SPLIT_THRESH:
                    return 3  # Split
        return 1  # Creation

    if is_end and t < N - 1:
        # Check if any other chain ends here nearby → Merge
        x_end, y_end = frames[t][i][0], frames[t][i][1]
        for tid2, chain2 in enumerate(trajectories):
            if tid2 == tid:
                continue
            t2_end, i2_end = chain2[-1]
            if t2_end == t and t2_end < N - 1:
                x2e, y2e = frames[t2_end][i2_end][0], frames[t2_end][i2_end][1]
                dist = np.sqrt((x_end - x2e)**2 + (y_end - y2e)**2)
                if dist < SPLIT_THRESH:
                    return 4  # Merge
        return 2  # Destruction

    return 0  # Continuation

# ── Write trajectories .vtp ────────────────────────────────────────────────────
pts   = vtk.vtkPoints()
lines = vtk.vtkCellArray()
a_tid   = vtk.vtkIntArray();   a_tid.SetName("TrajectoryID")
a_ts    = vtk.vtkIntArray();   a_ts.SetName("TimeStep")
a_val   = vtk.vtkFloatArray(); a_val.SetName("Value")
a_event = vtk.vtkIntArray();   a_event.SetName("EventType")
# EventType legend as FieldData string
legend = vtk.vtkStringArray(); legend.SetName("EventLegend")
for s in ["0=Continuation","1=Creation","2=Destruction","3=Split","4=Merge"]:
    legend.InsertNextValue(s)

pid = 0
for tid, chain in enumerate(trajectories):
    lines.InsertNextCell(len(chain))
    for pos, (t, i) in enumerate(chain):
        x, y, v = frames[t][i]
        pts.InsertNextPoint(float(x), float(y), 0.01)
        a_tid.InsertNextValue(tid)
        a_ts.InsertNextValue(t)
        a_val.InsertNextValue(float(v))
        a_event.InsertNextValue(get_event_type(tid, pos, chain))
        lines.InsertCellPoint(pid); pid += 1

poly = vtk.vtkPolyData()
poly.SetPoints(pts); poly.SetLines(lines)
poly.GetPointData().AddArray(a_tid)
poly.GetPointData().AddArray(a_ts)
poly.GetPointData().AddArray(a_val)
poly.GetPointData().AddArray(a_event)
poly.GetPointData().SetActiveScalars("EventType")
poly.GetFieldData().AddArray(legend)

w = vtk.vtkXMLPolyDataWriter()
w.SetFileName(f"{OUTDIR}/{TAG}_trajectories.vtp")
w.SetInputData(poly); w.Write()

# ── Write nodes .vtp (trajectory-member points only) ──────────────────────────
npts  = vtk.vtkPoints()
verts = vtk.vtkCellArray()
n_ts    = vtk.vtkIntArray();   n_ts.SetName("TimeStep")
n_v     = vtk.vtkFloatArray(); n_v.SetName("Value")
n_event = vtk.vtkIntArray();   n_event.SetName("EventType")
k = 0
for tid, chain in enumerate(trajectories):
    for pos, (t, i) in enumerate(chain):
        x, y, v = frames[t][i]
        npts.InsertNextPoint(float(x), float(y), 0.02)
        verts.InsertNextCell(1); verts.InsertCellPoint(k); k += 1
        n_ts.InsertNextValue(t)
        n_v.InsertNextValue(float(v))
        n_event.InsertNextValue(get_event_type(tid, pos, chain))

npoly = vtk.vtkPolyData()
npoly.SetPoints(npts); npoly.SetVerts(verts)
npoly.GetPointData().AddArray(n_ts)
npoly.GetPointData().AddArray(n_v)
npoly.GetPointData().AddArray(n_event)
npoly.GetPointData().SetActiveScalars("EventType")

w2 = vtk.vtkXMLPolyDataWriter()
w2.SetFileName(f"{OUTDIR}/{TAG}_nodes.vtp")
w2.SetInputData(npoly); w2.Write()

# Count events
ev = np.array([get_event_type(tid, pos, ch)
               for tid, ch in enumerate(trajectories)
               for pos in range(len(ch))])
print(f"  Events: {(ev==1).sum()} creation, {(ev==2).sum()} destruction, "
      f"{(ev==3).sum()} split, {(ev==4).sum()} merge, {(ev==0).sum()} continuation")
print(f"wrote {TAG}_trajectories.vtp ({poly.GetNumberOfLines()} lines) "
      f"and {TAG}_nodes.vtp ({npoly.GetNumberOfPoints()} nodes)")
