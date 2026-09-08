"""
ngspice_explained.py -- run ngspice and put what it did on screen, in words.

ngspice has no GUI. Everything it produces in this project arrives as numbers
in a terminal, which is fine for a script and useless for explaining the work
to somebody: a number does not say which trace it came from or why that trace
matters. LTspice gets to show a window; this gives ngspice the same.

Runs the two cases live, then opens a window that says what was solved, what
was measured, and what the answer means -- with the meaning drawn onto the
traces rather than left in a caption.

    python3 scripts/ngspice_explained.py          # opens a window
    python3 scripts/ngspice_explained.py --save   # writes the PNG only
"""
import os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
if "--save" in sys.argv:
    matplotlib.use("Agg")
else:
    matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_ngspice_explained.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
RED, GREEN, BLUE = "#B00000", "#1E7B34", "#1F4E9C"
VTH = 1.4
T0, T1, TMEAS = 2.0125e-6, 2.115e-6, 2.015e-6
plt.rcParams["font.family"] = "DejaVu Sans"


def version():
    r = subprocess.run(["ngspice", "-b", "-o", "/dev/null", "/dev/null"],
                       capture_output=True, text=True)
    for tok in (r.stdout + r.stderr).split():
        if tok.startswith("ngspice-"):
            return tok
    return "ngspice"


print("running ngspice ...")
t0 = time.time()
A, pa = gansim.run_raw(CLKEN=0, VNEG=0)
B, pb = gansim.run_raw(CLKEN=1, VNEG=-2)
wall = time.time() - t0
npts = A.shape[0]
print("  done in %.1f s, %d time points per run" % (wall, npts))

fig = plt.figure(figsize=(13.4, 7.6), dpi=150)
try:
    fig.canvas.manager.set_window_title("ngspice — what it just did")
except Exception:
    pass
gs = fig.add_gridspec(3, 2, height_ratios=[0.62, 1, 1], hspace=0.30, wspace=0.17,
                      left=0.065, right=0.985, top=0.925, bottom=0.075)

# --------------------------------------------------- what ngspice just did --
ax = fig.add_subplot(gs[0, :]); ax.axis("off")
ax.set_xlim(0, 100); ax.set_ylim(0, 10)
ax.text(0, 9.0, "WHAT NGSPICE JUST DID", fontsize=10, fontweight="bold", color=MUTED)
ax.plot([0, 100], [8.0, 8.0], lw=1.0, color=RULE)
rows = [
    ("Solved",   "sim/dpt.cir — a GaN half-bridge, twice: once without the fix, once with it"),
    ("Using",    "models/egan.lib (the transistor) and models/segdrv.lib (the gate driver)"),
    ("Computed", "%s time points per run, %.1f s of wall time for both" % (f"{npts:,}", wall)),
    ("Measured", "V(hsg,sw) — the gate-to-source voltage of the device that is switched OFF"),
    ("Window",   "2.015–2.100 µs, the 85 ns after the other device turns on"),
]
y = 6.6
for k, v in rows:
    ax.text(0, y, k, fontsize=10.2, fontweight="bold", color=INK)
    ax.text(11, y, v, fontsize=10.0, color=MUTED)
    y -= 1.55

# ------------------------------------------------------------- the panels --
for col, (d, p, title, colour, safe) in enumerate((
        (A, pa, "no clamp, gate held at 0 V when off", RED, False),
        (B, pb, "clamp on, gate held at −2 V when off", GREEN, True))):
    t = d[:, 0]
    sw = d[:, 1]
    g = d[:, 7] - d[:, 1]
    m = (t >= T0) & (t <= T1)
    tu = (t[m] - T0) * 1e9

    a = fig.add_subplot(gs[1, col])
    a.plot(tu, sw[m], lw=1.5, color=BLUE)
    a.set_title(title, fontsize=11, fontweight="bold", loc="left", color=colour)
    a.set_ylabel("switch node  [V]", fontsize=9.5)
    a.set_ylim(-25, 135); a.set_xlim(0, (T1 - T0) * 1e9); a.grid(alpha=.25)
    i_fall = int(np.argmax(np.abs(np.diff(sw[m]))))
    a.annotate("the other device turns on here,\nand this node drops 100 V",
               xy=(tu[i_fall], 55), xytext=(tu[i_fall] + 24, 98), fontsize=9,
               color=INK, arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    a.text(1.5, 112, "CAUSE", fontsize=8.6, fontweight="bold", color=MUTED)

    b = fig.add_subplot(gs[2, col])
    b.plot(tu, g[m], lw=1.6, color=colour)
    b.axhline(VTH, ls="--", lw=1.6, color=RED)
    b.set_ylabel("gate of the OFF device  [V]", fontsize=9.5)
    b.set_xlabel("time from %.3f µs   [ns]" % (T0 * 1e6), fontsize=9.5)
    b.set_ylim(-3.0, 2.6); b.set_xlim(0, (T1 - T0) * 1e9); b.grid(alpha=.25)
    b.text((T1 - T0) * 1e9 - 2, VTH + 0.16, "1.4 V — it switches on above this",
           fontsize=8.8, fontweight="bold", color=RED, ha="right")
    b.text(1.5, -2.85, "EFFECT", fontsize=8.6, fontweight="bold", color=MUTED)

    mm = tu >= (TMEAS - T0) * 1e9
    pk = float(np.nanmax(g[m][mm]))
    ipk = int(np.arange(len(tu))[mm][int(np.nanargmax(g[m][mm]))])
    b.plot([tu[ipk]], [pk], "o", ms=8, color=colour, zorder=5)
    b.annotate("%+.3f V" % pk, (tu[ipk], pk), textcoords="offset points",
               xytext=(14, 8), fontsize=13, fontweight="bold", color=colour)
    if safe:
        b.annotate("", xy=(tu[ipk], pk), xytext=(tu[ipk], VTH),
                   arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.8))
        b.text(tu[ipk] + 5, (pk + VTH) / 2 - 0.12,
               "%.2f V of margin — it stays off" % (VTH - pk),
               fontsize=9.6, fontweight="bold", color=GREEN)
    else:
        b.annotate("above the line: it switches on\nwhen it must not",
                   xy=(tu[ipk], pk), xytext=(tu[ipk] + 22, -1.6), fontsize=9.4,
                   fontweight="bold", color=RED,
                   arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))

fig.suptitle("ngspice %s  —  run just now on this machine, from sim/dpt.cir"
             % version(), fontsize=12.5, fontweight="bold", y=0.978)
fig.savefig(OUT, dpi=150, facecolor="white")
print("wrote", OUT)
if "--save" not in sys.argv:
    print("close the window to finish")
    plt.show()
