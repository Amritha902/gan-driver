"""
circuit_diagram.py -- the actual SCHEMATIC, not a block diagram.

arch_diagram.py shows what talks to what. This shows the circuit that is
simulated: the two GaN devices, every parasitic the netlist contains, the
segmented output stage drawn as switches and resistors, the Miller clamp,
the off-bias mux, and the power loop with its inductance.

Every element drawn here exists in sim/dpt.cir. Nothing is decorative:
C_GD on the low-side device is the crosstalk path the whole project is
about, and L_loop is the one parameter that decides whether adaptive
control is worth building at all.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_circuit.png")
INK, MUTED, RULE, SHADE = "#141414", "#5A5A5A", "#9A9A9A", "#EDEDED"
HOT  = "#B00000"
FONT = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.2, 7.2))
ax.set_xlim(0, 158); ax.set_ylim(0, 88); ax.axis("off")
ax.set_aspect("equal")

def wire(pts, lw=1.5, color=INK, ls="-", z=3):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    # linestyle must be a KEYWORD: a dash tuple like (0,(3,2)) is not a valid
    # positional format string and matplotlib rejects it
    ax.plot(xs, ys, linestyle=ls, lw=lw, color=color,
            solid_capstyle="round", zorder=z)

def dot(x, y, r=1.0, color=INK):
    ax.plot([x], [y], marker="o", ms=r*5.2, color=color, zorder=6)

def txt(x, y, t, fs=8.2, b=False, color=INK, ha="left", va="center", it=False):
    ax.text(x, y, t, fontsize=fs, fontweight="bold" if b else "normal",
            style="italic" if it else "normal",
            color=color, ha=ha, va=va, family=FONT, zorder=7)

def res(x, y, w=8, h=3.2, label="", horiz=True, fs=7.8):
    """A box resistor - IEC style, and legible at slide size."""
    if horiz:
        ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                     boxstyle="square,pad=0", fc="white", ec=INK, lw=1.4, zorder=5))
        if label: txt(x, y + h/2 + 2.2, label, fs=fs, ha="center")
    else:
        ax.add_patch(FancyBboxPatch((x - h/2, y - w/2), h, w,
                     boxstyle="square,pad=0", fc="white", ec=INK, lw=1.4, zorder=5))
        if label: txt(x + h/2 + 1.6, y, label, fs=fs)

def cap(x, y, w=7.0, gap=2.0, label="", horiz=False, fs=7.8, color=INK, lab_dx=2.4):
    """Two plates. horiz=False means the plates are horizontal (vertical cap)."""
    if horiz:
        ax.plot([x - gap/2]*2, [y - w/2, y + w/2], lw=1.9, color=color, zorder=5)
        ax.plot([x + gap/2]*2, [y - w/2, y + w/2], lw=1.9, color=color, zorder=5)
        if label: txt(x, y + w/2 + 2.2, label, fs=fs, ha="center", color=color)
    else:
        ax.plot([x - w/2, x + w/2], [y + gap/2]*2, lw=1.9, color=color, zorder=5)
        ax.plot([x - w/2, x + w/2], [y - gap/2]*2, lw=1.9, color=color, zorder=5)
        if label: txt(x + w/2 + lab_dx, y, label, fs=fs, color=color)

def ind(x, y, h=10, label="", fs=7.8):
    """Vertical inductor: four bumps."""
    import numpy as np
    n = 4; seg = h / n
    for i in range(n):
        cy = y - h/2 + seg*(i + 0.5)
        th = np.linspace(-1.5708, 1.5708, 24)
        ax.plot(x + 2.6*np.cos(th), cy + (seg/2)*np.sin(th), lw=1.6,
                color=INK, zorder=5)
    if label: txt(x + 4.4, y, label, fs=fs)

def fet(x, y, name="", flip=False, hot=False):
    """Enhancement-mode GaN HEMT. Drawn as an e-mode FET with NO body diode,
    which is the whole reason negative off-bias is expensive here."""
    c = HOT if hot else INK
    gx = x - 7.0            # gate bar
    cx = x - 3.6            # channel bar
    ax.plot([gx, gx], [y - 5.4, y + 5.4], lw=1.8, color=c, zorder=5)
    for y0, y1 in ((y - 5.4, y - 2.0), (y - 1.4, y + 1.4), (y + 2.0, y + 5.4)):
        ax.plot([cx, cx], [y0, y1], lw=2.3, color=c, zorder=5)
    wire([(gx - 7, y), (gx, y)], color=c)                       # gate lead
    wire([(cx, y + 4.4), (x + 4, y + 4.4), (x + 4, y + 10)], color=c)   # drain
    wire([(cx, y - 4.4), (x + 4, y - 4.4), (x + 4, y - 10)], color=c)   # source
    ax.add_patch(Polygon([[cx + 0.2, y - 4.4], [cx + 3.2, y - 3.1],
                          [cx + 3.2, y - 5.7]], closed=True, fc=c, ec=c, zorder=6))
    if name: txt(x + 6.5, y, name, fs=9.0, b=True, color=c)
    return dict(g=(gx - 7, y), d=(x + 4, y + 10), s=(x + 4, y - 10))

# ============================ POWER STAGE ================================
VBUS, GND = 80.0, 8.0
XL = 118.0                      # the half-bridge leg
txt(96, 85.5, "POWER  STAGE   —   double-pulse half-bridge", fs=9.2, b=True, color=MUTED)

wire([(100, VBUS), (146, VBUS)], lw=2.0)                 # + rail
wire([(100, GND), (146, GND)], lw=2.0)                   # - rail
txt(99, VBUS, "V$_{DC}$", fs=9.0, b=True, ha="right")
txt(99, VBUS - 3.6, "50 – 200 V", fs=7.6, ha="right", color=MUTED)
txt(99, GND, "0 V", fs=8.4, b=True, ha="right")

cap(104, 44, w=9, gap=2.6, label="C$_{bus}$")            # bus decoupling
wire([(104, VBUS), (104, 45.3)]); wire([(104, 42.7), (104, GND)])

q1 = fet(XL, 62, "Q1  high side")
wire([(q1["d"][0], q1["d"][1]), (XL + 4, VBUS)])
SW = (XL + 4, 46.0)
wire([(q1["s"][0], q1["s"][1]), SW])
dot(*SW)
txt(SW[0] + 3.0, SW[1] + 2.4, "SW", fs=9.2, b=True)
txt(SW[0] + 3.0, SW[1] - 1.4, "the dV/dt node", fs=7.4, color=MUTED)

q2 = fet(XL, 26, "Q2  low side  (DUT)", hot=True)
wire([(q2["d"][0], q2["d"][1]), SW], color=HOT)
wire([(q2["s"][0], q2["s"][1]), (XL + 4, 14)], color=HOT)
ind(XL + 4, 11.0, h=6.0)
txt(XL + 9.0, 11.0, "L$_{loop}$ = 1 – 6 nH", fs=8.0, b=True)
txt(XL + 9.0, 4.2, "power-loop parasitic", fs=7.2, color=MUTED)
wire([(XL + 4, 8.0), (XL + 4, GND)])

# load branch off the switching node
wire([(SW[0], SW[1]), (140, SW[1])])
ind(140, 34, h=12, label="L$_{load}$")
wire([(140, 46), (140, 40)]); wire([(140, 28), (140, GND)])
txt(144, 22, "2 – 10 A", fs=7.8, color=MUTED)

# device capacitances -- these are the netlist's, not decoration
cap(XL - 12.5, 34.0, w=6.5, gap=2.2, horiz=True, color=HOT, label="")
txt(XL - 20.0, 34.0, "C$_{GD}$", fs=8.6, b=True, color=HOT, ha="right")
txt(XL - 20.0, 30.6, "the crosstalk path", fs=7.2, color=HOT, ha="right")
wire([(XL - 14.0, 26.0), (XL - 14.0, 34.0), (XL - 13.6, 34.0)], color=HOT)
wire([(XL - 11.4, 34.0), (XL + 4, 34.0), (XL + 4, 36.0)], color=HOT, ls="-")
cap(XL - 14.0, 18.0, w=6.5, gap=2.2, horiz=False, color=HOT, label="C$_{GS}$", lab_dx=1.8)
wire([(XL - 14.0, 26.0), (XL - 14.0, 19.0)], color=HOT)
wire([(XL - 14.0, 17.0), (XL - 14.0, 14.0), (XL + 4, 14.0)], color=HOT)
cap(XL - 12.5, 70.0, w=6.0, gap=2.0, horiz=True, label="")
txt(XL - 20.0, 70.0, "C$_{GD}$", fs=8.0, ha="right")
wire([(XL - 14.0, 62.0), (XL - 14.0, 70.0), (XL - 13.6, 70.0)])
wire([(XL - 11.4, 70.0), (XL + 4, 70.0)])

# ====================== SEGMENTED GATE DRIVER (Q2) =======================
txt(4, 85.5, "SEGMENTED  GATE  DRIVER   —   drawn for Q2; Q1 is identical",
    fs=9.2, b=True, color=MUTED)
ax.add_patch(FancyBboxPatch((3, 12), 84, 62, boxstyle="round,pad=0.6,rounding_size=1.4",
             fc="#FCFCFC", ec=RULE, lw=1.2, ls=(0, (5, 3)), zorder=1))

VDRV = 68.0
wire([(10, VDRV), (74, VDRV)], lw=2.0)
txt(9, VDRV, "V$_{DRV}$  +6 V", fs=8.4, b=True, ha="right")

GATE_X, GATE_Y = 78.0, 40.0          # the gate node of Q2

def slice_col(x, y_top, y_bot, n_label, rlabel, tag):
    """One drive slice: a control switch in series with its resistor."""
    ax.add_patch(FancyBboxPatch((x - 3.0, y_top - 9.0), 6.0, 5.0,
                 boxstyle="square,pad=0", fc="white", ec=INK, lw=1.4, zorder=5))
    wire([(x, y_top), (x, y_top - 4.0)])
    ax.plot([x - 2.2, x + 2.2], [y_top - 6.0, y_top - 7.4], lw=1.6, color=INK, zorder=6)
    dot(x - 2.2, y_top - 7.4, r=0.55); dot(x + 2.2, y_top - 6.0, r=0.55)
    wire([(x, y_top - 9.0), (x, y_top - 12.0)])
    res(x, y_top - 15.5, w=7.0, h=3.0, horiz=False)
    wire([(x, y_top - 19.0), (x, y_bot)])
    txt(x, y_top - 15.5 + 0.0, "", fs=7.0)
    return x

PU_X = [16, 26, 36]
for i, x in enumerate(PU_X):
    slice_col(x, VDRV, GATE_Y, "", "", "")
txt(46, VDRV - 8.0, "· · ·", fs=13, ha="center")
txt(46, VDRV - 16.0, "· · ·", fs=13, ha="center")
txt(26, VDRV + 3.2, "8 × PULL-UP slice   —   N$_{PU}$ of 8 enabled", fs=8.2, b=True, ha="center")
txt(26, VDRV - 22.5, "R$_{pu}$ each", fs=7.6, ha="center", color=MUTED)

wire([(16, GATE_Y), (56, GATE_Y)])
wire([(56, GATE_Y), (GATE_X, GATE_Y)])
dot(GATE_X, GATE_Y)
txt(GATE_X + 1.6, GATE_Y + 3.2, "GATE of Q2", fs=8.6, b=True, color=HOT)
wire([(GATE_X, GATE_Y), (XL - 14.0, GATE_Y), (XL - 14.0, 26.0)], color=HOT, lw=1.7)

VOFF = 12.0
PD_X = [16, 26, 36]
for x in PD_X:
    ax.add_patch(FancyBboxPatch((x - 3.0, GATE_Y - 9.0), 6.0, 5.0,
                 boxstyle="square,pad=0", fc="white", ec=INK, lw=1.4, zorder=5))
    wire([(x, GATE_Y), (x, GATE_Y - 4.0)])
    ax.plot([x - 2.2, x + 2.2], [GATE_Y - 6.0, GATE_Y - 7.4], lw=1.6, color=INK, zorder=6)
    dot(x - 2.2, GATE_Y - 7.4, r=0.55); dot(x + 2.2, GATE_Y - 6.0, r=0.55)
    wire([(x, GATE_Y - 9.0), (x, GATE_Y - 12.0)])
    res(x, GATE_Y - 15.5, w=7.0, h=3.0, horiz=False)
    wire([(x, GATE_Y - 19.0), (x, VOFF)])
txt(46, GATE_Y - 8.0, "· · ·", fs=13, ha="center")
txt(46, GATE_Y - 16.0, "· · ·", fs=13, ha="center")
txt(26, GATE_Y - 21.2, "8 × PULL-DOWN slice   —   N$_{PD}$ of 8 enabled", fs=8.2, b=True, ha="center")

# active Miller clamp: its own low-impedance path, gate straight to source
ax.add_patch(FancyBboxPatch((GATE_X - 15.0, 26.0), 6.0, 5.0,
             boxstyle="square,pad=0", fc="white", ec=INK, lw=1.4, zorder=5))
wire([(56, GATE_Y), (56, 31.0)])
ax.plot([56 - 2.2, 56 + 2.2], [29.0, 27.6], lw=1.6, color=INK, zorder=6)
dot(56 - 2.2, 27.6, r=0.55); dot(56 + 2.2, 29.0, r=0.55)
wire([(56, 26.0), (56, VOFF)])
txt(59.5, 28.5, "ACTIVE MILLER CLAMP", fs=8.0, b=True)
txt(59.5, 25.2, "CLK_EN  ·  shorts G to S", fs=7.2, color=MUTED)

wire([(10, VOFF), (74, VOFF)], lw=2.0)
txt(9, VOFF, "V$_{off}$", fs=8.4, b=True, ha="right")
txt(9, VOFF - 3.2, "0 V  /  −2 V", fs=7.6, ha="right", color=MUTED)
ax.add_patch(FancyBboxPatch((60, VOFF - 8.5), 16, 6.0,
             boxstyle="round,pad=0.25,rounding_size=0.6",
             fc=SHADE, ec=INK, lw=1.2, zorder=5))
txt(68, VOFF - 5.5, "OFF-BIAS MUX", fs=7.6, b=True, ha="center")
wire([(68, VOFF), (68, VOFF - 2.5)])
wire([(74, VOFF - 5.5), (GATE_X + 2, VOFF - 5.5), (GATE_X + 2, 14.0)])
wire([(GATE_X + 2, 14.0), (XL + 4, 14.0)])

# the control word
ax.add_patch(FancyBboxPatch((3.5, 76.0), 84, 8.0,
             boxstyle="round,pad=0.3,rounding_size=0.8",
             fc="#F2F2F2", ec=INK, lw=1.3, zorder=5))
txt(6, 80.0, "FPGA  seg_gate_ctrl.v   →   720-point control word:", fs=8.4, b=True)
txt(53, 80.0, "N$_{PU}$ · N$_{PD,LS}$ · N$_{PD,HS}$ · t$_{dead}$ · CLK_EN · V$_{neg}$",
    fs=8.4, b=True, color=HOT)
for x in (16, 26, 36, 56, 68):
    wire([(x, 76.0), (x, 72.5)], ls=(0, (3, 2)), lw=1.1, color=MUTED)

fig.text(0.012, 0.018,
         "Every element here is in sim/dpt.cir. Q2 is the device under test; C$_{GD}$ on Q2 is the "
         "crosstalk path that turns it on when Q1 switches. GaN has no body diode, so holding "
         "V$_{off}$ negative is paid for again across the dead time.",
         fontsize=8.0, color=MUTED, family=FONT)
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(OUT, dpi=190, facecolor="white")
print("wrote", OUT)
