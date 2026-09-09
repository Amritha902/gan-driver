"""
netlist_figure.py -- what ngspice is actually handed.

The deck shows an LTspice schematic and calls it "the circuit". That is true,
but every headline number in the project comes out of ngspice, and ngspice is
not given a schematic -- it is given a netlist. A reader who asks "so what did
you simulate?" deserves to see the thing that was simulated.

This puts the power stage of sim/buck.cir on the page line by line, with what
each line is in plain English beside it, so the netlist and the drawing can be
recognised as the same converter.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_netlist.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
BLUE, GREEN, PAPER = "#1F4E9C", "#1E7B34", "#F7F7F7"
plt.rcParams["font.family"] = "DejaVu Sans"

# copied from sim/buck.cir, power stage and output filter, in file order
LINES = [
    ("Vin    vin 0 DC {VIN}",              "the 100 V DC supply"),
    ("Rloop  bus n1  0.3",                 "resistance of the power loop"),
    ("Lloop  n1  hstop {LLOOP}",           "and its 3 nH of stray inductance"),
    ("Xhs    hsd hsg sw  EGAN",            "the HIGH-SIDE GaN transistor"),
    ("Xls    lsd lsg 0   EGAN",            "the LOW-SIDE GaN transistor"),
    ("Lo     sw  nlo {LOUT}",              "output inductor, 22 µH"),
    ("Co     nc  0   {COUT}",              "output capacitor, 4.7 µF"),
    ("Rload  out 0   {RLOAD}",             "the 10 Ω load"),
    ("", ""),
    ("Xdrvhs ... SEGDRV",                  "segmented gate driver, high side"),
    ("Xdrvls ... SEGDRV",                  "segmented gate driver, low side"),
    ("", ""),
    (".tran 0.2n {TSTOP} 0 2n uic",        "run it, 0.2 ns steps"),
    (".meas TRAN vout AVG V(out) ...",     "and measure the output"),
]

fig, ax = plt.subplots(figsize=(13.2, 6.6), dpi=170)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

ax.text(0, 96, "What ngspice is actually given", fontsize=17, fontweight="bold",
        color=INK)
ax.text(0, 90.5,
        "ngspice has no schematic. It reads a netlist — the circuit written as "
        "text, one component per line. This is sim/buck.cir.",
        fontsize=10.6, color=MUTED)
ax.plot([0, 100], [87, 87], lw=1.2, color=RULE)

ax.add_patch(FancyBboxPatch((0, 14), 52, 70,
             boxstyle="round,pad=0.6,rounding_size=1.2",
             fc=PAPER, ec=BLUE, lw=1.8))
ax.text(2, 80.5, "sim/buck.cir", fontsize=11.5, fontweight="bold", color=BLUE)

y = 75
for code, meaning in LINES:
    if code:
        ax.text(2.4, y, code, fontsize=10.4, family="DejaVu Sans Mono",
                color=INK if not code.startswith(".") else BLUE)
        ax.text(56, y, meaning, fontsize=10.4, color=MUTED)
        ax.plot([52.6, 55.2], [y + 0.6, y + 0.6], lw=1.0, color=RULE)
    y -= 4.6

ax.plot([0, 100], [12, 12], lw=1.0, color=RULE)
ax.text(0, 9.0,
        "Each line names a component, the two nodes it sits between, and its "
        "value. \"Xhs hsd hsg sw EGAN\" is the high-side transistor with its "
        "drain on hsd,\nits gate on hsg and its source on sw — which is exactly "
        "what the schematic draws. Same converter, written two ways: ngspice "
        "gives 48.56 V, LTspice 48.84 V.",
        fontsize=10.4, color=INK, va="top")
ax.text(0, 1.2,
        "About 35,000 runs of netlists like this one produced every number in "
        "this presentation.",
        fontsize=10.0, color=GREEN, fontweight="bold")

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
