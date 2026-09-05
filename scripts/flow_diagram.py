"""
flow_diagram.py -- ONE use case, followed all the way through.

The architecture diagram says what talks to what. The circuit diagram says
what is wired to what. Neither says what actually HAPPENS, in order, on a
single switching edge -- which is what a reviewer seeing this cold needs first.

Use case: a GaN half-bridge in a battery-storage converter, load falling from
10 A to 2 A as the pack nears full charge. Chosen deliberately: light load is
the ONLY one of the four corners where the best dead time differs, so it is
where the entire adaptive question is decided.

  Row 1  what the controller decides, every edge
  Row 2  what the circuit then does, and the two possible outcomes

Geometry note: every band is allocated an explicit y range and the row-to-row
connector is routed through a reserved empty band. The first draft let the
connector cross a heading and an outcome box, which is the exact fault this
figure is meant not to have.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "fig_flow.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
HOT, GOOD = "#B00000", "#1E7B34"
SHADE, LIVE = "#F1F1F1", "#FFF1CC"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.0, 6.6), dpi=170)
ax.set_xlim(0, 100)
ax.set_ylim(-1, 52)
ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, title, sub=None, fc="white", ec=INK, lw=1.5, tc=INK, fs=9.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.25,rounding_size=0.7",
                 fc=fc, ec=ec, lw=lw, zorder=4))
    if sub:
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=tc, zorder=5)
        ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center",
                fontsize=fs - 1.8, color=MUTED, zorder=5)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=tc, zorder=5)


def diamond(cx, cy, w, h, label, sub=None):
    ax.add_patch(Polygon([[cx, cy + h / 2], [cx + w / 2, cy],
                          [cx, cy - h / 2], [cx - w / 2, cy]],
                 closed=True, fc=LIVE, ec=INK, lw=1.7, zorder=4))
    ax.text(cx, cy + (1.1 if sub else 0), label, ha="center", va="center",
            fontsize=9.2, fontweight="bold", color=INK, zorder=5)
    if sub:
        ax.text(cx, cy - 2.3, sub, ha="center", va="center",
                fontsize=7.5, color=MUTED, zorder=5)


def arrow(x1, y1, x2, y2, color=INK, lw=1.7):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=13, lw=lw, color=color,
                 shrinkA=0, shrinkB=0, zorder=3))


def elbow(pts, color=INK, lw=1.7, head=True):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                lw=lw, color=color, zorder=3, solid_capstyle="round")
    a, b = pts[-2], pts[-1]
    if head:
        arrow(a[0], a[1], b[0], b[1], color=color, lw=lw)
    else:
        ax.plot([a[0], b[0]], [a[1], b[1]], lw=lw, color=color, zorder=3)


def tag(x, y, text, color=MUTED, fs=7.8, ha="center", b=False):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color,
            fontweight="bold" if b else "normal", zorder=6)


# ---------------------------------------------------------------- header ---
ax.text(0.5, 50.2, "USE CASE", fontsize=8.8, fontweight="bold", color=MUTED)
ax.text(0.5, 47.2,
        "Battery-storage converter — load falling 10 A → 2 A as the pack nears full charge.",
        fontsize=11.6, fontweight="bold", color=INK)
ax.text(0.5, 44.4,
        "Light load is the only one of the four corners where the best dead time differs. "
        "This is where the adaptive question is decided.",
        fontsize=8.6, color=MUTED)
ax.plot([0.5, 99.5], [42.4, 42.4], lw=1.0, color=RULE, zorder=1)

# ================================================== ROW 1  y 28 .. 40 ======
tag(0.5, 40.4, "EVERY SWITCHING EDGE   —   what the controller decides",
    color=INK, fs=9.0, ha="left", b=True)

box(0.5, 30.0, 17.0, 8.0, "Operating point", "50 V · 2 A · 25 °C", fc=SHADE)
arrow(17.5, 34.0, 21.5, 34.0)

diamond(30.0, 34.0, 16.0, 10.0, "Light load?")

# both branches leave to the right and separate vertically
elbow([(38.0, 34.0), (41.5, 34.0), (41.5, 36.8), (44.0, 36.8)])
tag(40.6, 36.2, "yes", color=HOT, fs=8.0, b=True, ha="right")
box(44.0, 34.6, 15.5, 4.4, "t_dead = 15 ns", ec=HOT, lw=1.8, tc=HOT, fs=9.4)

elbow([(38.0, 34.0), (41.5, 34.0), (41.5, 30.8), (44.0, 30.8)])
tag(40.6, 31.6, "no", color=INK, fs=8.0, b=True, ha="right")
box(44.0, 28.6, 15.5, 4.4, "t_dead = 5 ns", fs=9.4)

# the two branches rejoin
elbow([(59.5, 36.8), (61.4, 36.8), (61.4, 34.0), (63.0, 34.0)])
elbow([(59.5, 30.8), (61.4, 30.8), (61.4, 34.0), (63.0, 34.0)], head=False)

box(63.0, 29.5, 22.0, 9.0, "Everything else STRAPPED",
    "8+8 slices · clamp ON · −2 V rail", fc=SHADE, fs=9.0)
arrow(85.0, 34.0, 88.0, 34.0)
box(88.0, 30.0, 11.5, 8.0, "Gate drive", "8 + 8 slices")

tag(30.0, 27.2, "the ONLY live decision — one comparator", color=HOT, fs=8.2, b=True)
tag(74.0, 27.2, "set once at power-up — never re-decided", color=MUTED, fs=7.8)

# ============================ connector band  y 24 .. 25  (reserved empty) ==
elbow([(93.7, 30.0), (93.7, 24.6), (3.0, 24.6), (3.0, 17.0), (6.0, 17.0)])

# ================================================== ROW 2  y 8 .. 22 =======
tag(6.0, 22.6, "IN THE CIRCUIT   —   what physically follows",
    color=INK, fs=9.0, ha="left", b=True)

box(6.0, 12.8, 16.0, 8.4, "Low side turns on", "SW node falls 100 V")
arrow(22.0, 17.0, 25.5, 17.0)
box(25.5, 12.8, 18.5, 8.4, "dV/dt across C$_{GD}$", "charge into the OFF gate")
arrow(44.0, 17.0, 47.5, 17.0)

diamond(56.5, 17.0, 17.0, 11.0, "V$_{GS}$ > 1.4 V ?", "the threshold")

# failing outcome -- straight down into its own band, nothing else there
arrow(56.5, 11.5, 56.5, 8.4, color=HOT)
tag(59.4, 9.9, "yes", color=HOT, fs=8.0, b=True)
box(44.0, 3.6, 25.0, 4.8, "FALSE TURN-ON  —  shoot-through",
    ec=HOT, lw=1.9, tc=HOT, fs=9.4)
tag(56.5, 2.0, "fastest drive, no clamp:   +1.65 V", color=HOT, fs=8.0)

# shipped outcome
arrow(65.0, 17.0, 70.0, 17.0, color=GOOD)
tag(67.4, 18.6, "no", color=GOOD, fs=8.0, b=True)
box(70.0, 12.8, 19.5, 8.4, "SAFE", "clamp + −2 V rail:   −1.18 V",
    ec=GOOD, lw=2.0, tc=GOOD)
arrow(89.5, 17.0, 92.5, 17.0, color=GOOD)
ax.text(96.2, 18.2, "2.58 V", ha="center", va="center", fontsize=14.5,
        fontweight="bold", color=GOOD, zorder=6)
ax.text(96.2, 15.4, "of margin", ha="center", va="center", fontsize=8.2,
        color=MUTED, zorder=6)

# ---------------------------------------------------------------- footer ---
ax.plot([0.5, 99.5], [0.0, 0.0], lw=1.0, color=RULE, zorder=1)
ax.text(0.5, -0.9,
        "Everything adaptive reduces to the one shaded decision. Freezing it costs 5.45 % "
        "across four corners — and 0.00 % if the light-load corner is left out.",
        fontsize=9.0, color=INK, va="top")

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
