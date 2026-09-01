"""
arch_diagram.py -- the system architecture, drawn as boxes and text.

Deliberately plain: rectangles, labels, arrows, left-to-right signal flow in
four columns. No gradients, no shadows, no clip art. A reviewer should read
the path in five seconds.

The drawing has one job beyond showing the blocks: to make the project's
result visible. The dashed block is the sensing / lookup-table machinery that
per-operating-point adaptation requires. Every solid block is a fixed
configuration written once at power-up.

The percentages are IMPORTED from novelty.py rather than typed here. An
earlier version hardcoded 10.7 %, and when the mixed-denominator bug was
fixed and the figure moved to 13.4 % the diagram silently disagreed with the
slide that quoted it. Numbers a figure asserts should come from the script
that computes them.
"""
import contextlib, io, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import novelty
with contextlib.redirect_stdout(io.StringIO()):   # it prints a full report
    N = novelty.main()
OUT  = os.path.join(ROOT, "results", "fig_architecture.png")
INK, MUTED, RULE, SHADE = "#141414", "#5E5E5E", "#A8A8A8", "#ECECEC"

fig, ax = plt.subplots(figsize=(13.2, 6.3))
ax.set_xlim(0, 132); ax.set_ylim(0, 63); ax.axis("off")
FONT = "DejaVu Sans"

def box(x, y, w, h, title, subs=(), fc="#FFFFFF", ls="-", lw=1.35, fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.3,rounding_size=0.7",
                 fc=fc, ec=INK, lw=lw, linestyle=ls, zorder=2))
    n = len(subs)
    ty = y + h/2 + (2.0 + 1.4*(n-1)/2 if n else 0)
    ax.text(x + w/2, ty, title, ha="center", va="center", fontsize=fs,
            fontweight="bold", color=INK, zorder=3, family=FONT)
    for i, s in enumerate(subs):
        ax.text(x + w/2, ty - 3.4 - i*2.9, s, ha="center", va="center",
                fontsize=7.8, color=MUTED, zorder=3, family=FONT)

def arrow(p1, p2, ls="-", lw=1.35, rad=0.0, color=INK):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=12,
                 lw=lw, color=color, linestyle=ls, zorder=4,
                 connectionstyle="arc3,rad=%g" % rad))

def head(x, t):
    ax.text(x, 59.6, t, fontsize=8.2, color=MUTED, fontweight="bold", family=FONT)

# ---- columns --------------------------------------------------------------
head(3,  "COMMAND");  head(29, "CONTROL  (FPGA)")
head(62, "SEGMENTED DRIVER");  head(95, "POWER STAGE")

box(3, 45, 20, 11, "PWM in", ("duty / frequency",))

box(29, 41, 26, 15, "seg_gate_ctrl.v",
    ("dead_time_gen.v  ·  5–35 ns", "thermo_decode.v  ·  8+8 slices",
     "720-point control word"))

box(29, 22, 26, 12, "Sensing → ADC → LUT", ("operating-point scheduler",),
    fc=SHADE, ls=(0, (4, 2.2)))

for i, (t, s) in enumerate((("8 × pull-up slice",  "thermometer · strapped"),
                            ("8 × pull-down slice","thermometer · strapped"),
                            ("Active Miller clamp","always on"),
                            ("Off-bias mux",       "0 V / −2 V"))):
    box(62, 47 - i*11, 26, 9, t, (s,), fs=9.4)

box(95, 45, 32, 11, "GaN half-bridge", ("high side + low side",))
box(95, 30, 32, 11, "L$_{loop}$ = 3 nH", ("layout parasitic",))
box(95, 15, 32, 11, "Load", ("2–10 A  ·  50–200 V",))

# The switching node is the node the whole failure mechanism runs through, so
# it is named on the diagram instead of being implied by an unlabelled wire.
# both labels must sit in the 41-45 gap between the half-bridge and L_loop;
# anything lower lands inside the L_loop box
ax.plot([111], [43.0], marker="o", ms=5.5, color=INK, zorder=6)
ax.text(113.2, 44.0, "SW node", fontsize=8.6, fontweight="bold", color=INK,
        va="center", family=FONT)
ax.text(113.2, 41.9, "the dV/dt source", fontsize=7.4, color=MUTED,
        va="center", family=FONT)

# ---- arrows ---------------------------------------------------------------
arrow((23, 50.5), (29, 50.5))
for i in range(4):
    arrow((55, 48.5), (62, 51.5 - i*11), rad=0.06 if i else 0.0)
arrow((88, 51.5), (95, 50.5))
arrow((42, 34), (42, 41), ls=(0, (4, 2.2)))          # scheduler -> controller
arrow((111, 45), (111, 41))
arrow((111, 30), (111, 26))

# The failure mechanism: C_GD couples the switching node back into the gate of
# the device that is meant to be off. The arrow is the path; the callout below
# carries the text, because anywhere nearer would sit on top of a block.
arrow((110.2, 43.0), (88.5, 41.0), rad=-0.30, lw=1.8)
ax.add_patch(FancyBboxPatch((60, 1.2), 33, 10.0,
             boxstyle="round,pad=0.35,rounding_size=0.7",
             fc="#FFFFFF", ec=INK, lw=1.35, zorder=2))
ax.text(61.8, 8.9, "C$_{GD}$ CROSSTALK  (the curved path)", fontsize=8.4,
        fontweight="bold", color=INK, family=FONT)
ax.text(61.8, 5.9, "The switching node couples charge into the",
        fontsize=8, color=INK, family=FONT)
ax.text(61.8, 3.1, "off device: 1.65 V against a 1.40 V threshold.",
        fontsize=8, color=INK, family=FONT)
arrow((90, 11.2), (89.5, 40), rad=0.20, lw=1.0, color=RULE)

# ---- the corners: every result in the deck is measured at these ----------
ax.add_patch(FancyBboxPatch((95, 1.2), 32, 10.0,
             boxstyle="round,pad=0.35,rounding_size=0.7",
             fc="#FAFAFA", ec=RULE, lw=1.0, zorder=2))
ax.text(96.8, 8.9, "THE FOUR CORNERS", fontsize=8.2, fontweight="bold",
        color=INK, family=FONT)
ax.text(96.8, 6.1, "50 V/2 A/25 °C   ·   100 V/10 A/25 °C", fontsize=7.6,
        color=INK, family=FONT)
ax.text(96.8, 3.4, "200 V/2 A/125 °C   ·   200 V/10 A/125 °C", fontsize=7.6,
        color=INK, family=FONT)
arrow((111, 15), (111, 11.8), lw=1.0, color=RULE)

# ---- the annotation that carries the result -------------------------------
ax.text(42, 19.4, "worth %.1f %% of the total gain" % N["share"], fontsize=9.2,
        fontweight="bold", color=INK, ha="center", family=FONT)
ax.text(42, 16.6, "the only block that needs sensing", fontsize=7.9,
        color=MUTED, ha="center", family=FONT)

# ---- legend ---------------------------------------------------------------
# the legend must not spill into the crosstalk callout to its right, so the
# lines are wrapped by hand and the box grown to hold them
ax.add_patch(FancyBboxPatch((3, 1.4), 52, 11.6,
             boxstyle="round,pad=0.35,rounding_size=0.7",
             fc="#FAFAFA", ec=RULE, lw=1.0, zorder=2))
ax.text(5.5, 10.7, "WHAT THIS PROJECT MEASURES", fontsize=8.4,
        fontweight="bold", color=INK, family=FONT)
for dy, line in enumerate([
        "Solid blocks are set once at power-up — no sensing, no lookup table.",
        "The dashed block is the adaptive machinery: it buys %.1f %% of the" % N["share"],
        "total gain, and %.0f %% of even that needs only one comparator." % N["closed"]]):
    ax.text(5.5, 7.7 - 2.6 * dy, line, fontsize=8, color=INK, family=FONT)

fig.tight_layout(pad=0.3)
fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote", OUT)
