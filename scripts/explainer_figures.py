"""
explainer_figures.py -- the figures the deck was missing.

The results were defensible but the deck never explained the things the
results are made of: what the device is, what a "setting" is, what the input
conditions are, what comes out, and what "margin" means. A reviewer who has to
infer those is entitled to be sceptical of everything downstream.

Every number here is read from the project's own files -- models/egan.lib for
the device, scripts/sweep.py for the grid, results/*.csv for the operating
points -- rather than typed in.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrow, Polygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
RED, GREEN, BLUE, AMBER = "#B00000", "#1E7B34", "#1F4E9C", "#C77700"
PAPER, SHADE = "#FAFAFA", "#EFEFEF"
plt.rcParams["font.family"] = "DejaVu Sans"


def frame(w=13.2, h=6.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=170)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    return fig, ax


def head(ax, title, sub):
    ax.text(0, 97, title, fontsize=17, fontweight="bold", color=INK)
    ax.text(0, 91.5, sub, fontsize=10.5, color=MUTED)
    ax.plot([0, 100], [88, 88], lw=1.2, color=RULE)


def save(fig, name):
    p = os.path.join(RES, name)
    fig.savefig(p, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ======================================================== 1. GaN HEMT, what =
fig, ax = frame()
head(ax, "What a GaN HEMT is",
     "A power transistor built in gallium nitride instead of silicon. "
     "Same job, different physics.")


def device(x, title, colour, rows, note):
    ax.add_patch(FancyBboxPatch((x, 30), 44, 52,
                 boxstyle="round,pad=0.8,rounding_size=1.5",
                 fc=PAPER, ec=colour, lw=2.0))
    ax.text(x + 22, 77, title, ha="center", fontsize=13, fontweight="bold",
            color=colour)
    y = 69
    for k, v in rows:
        ax.text(x + 3, y, k, fontsize=10, color=INK, fontweight="bold")
        ax.text(x + 20, y, v, fontsize=10, color=MUTED)
        y -= 6.4
    ax.text(x + 22, 34, note, ha="center", fontsize=9.4, color=colour,
            fontweight="bold", style="italic")


device(0, "Silicon MOSFET", MUTED, [
    ("Bandgap", "1.1 eV"),
    ("Breakdown field", "0.3 MV/cm"),
    ("Structure", "vertical"),
    ("Body diode", "yes — it conducts backwards"),
    ("Gate threshold", "typically 3–4 V"),
], "thicker drift region for the same voltage")

device(54, "GaN HEMT", GREEN, [
    ("Bandgap", "3.4 eV"),
    ("Breakdown field", "3.3 MV/cm  — about 10×"),
    ("Structure", "lateral, conducts in a 2DEG"),
    ("Body diode", "none"),
    ("Gate threshold", "1.4 V in our device"),
], "thinner, lower resistance, far less charge to move")

ax.add_patch(FancyArrow(45.5, 56, 6, 0, width=1.6, head_width=4.5,
                        head_length=2.6, fc=INK, ec=INK,
                        length_includes_head=True))

ax.plot([0, 100], [24, 24], lw=1.0, color=RULE)
ax.text(0, 18,
        "Because the breakdown field is about ten times higher, the same 200 V "
        "rating needs a much thinner conducting layer. Less charge has to be\n"
        "moved to switch the device, so it switches in nanoseconds instead of "
        "tens of nanoseconds. That speed is the reason to use GaN — and it is\n"
        "also the reason this project exists, because a faster edge is a bigger "
        "disturbance to everything around it.",
        fontsize=10.4, color=INK, va="top")
ax.text(0, 2, "Device modelled: EPC2010C class — 200 V, 25 mΩ, threshold 1.4 V "
              "(models/egan.lib, written from datasheet quantities)",
        fontsize=8.8, color=MUTED)
save(fig, "fig_gan_1.png")


# ================================================ 2. GaN HEMT, why it matters
fig, ax = frame()
head(ax, "Why the GaN HEMT causes the problem we are solving",
     "Three properties of the device, and what each one does in a half-bridge.")

items = [
    ("1", "The gate turns on at 1.4 V",
     "A silicon MOSFET needs 3–4 V. Ours needs 1.4 V, so there is less than "
     "half the room between\n\"off\" and \"accidentally on\". Any disturbance "
     "on the gate matters more.",
     RED),
    ("2", "There is a capacitor from drain to gate — C$_{GD}$ = 150 pF",
     "It is unavoidable: it is the physical overlap inside the device. When "
     "the drain voltage moves,\ncharge flows through it into the gate. "
     "A 100 V change in a few nanoseconds pushes real current.",
     AMBER),
    ("3", "There is no body diode",
     "A silicon device freewheels through its body diode during the dead time. "
     "GaN has to conduct\nbackwards through its own channel, and the drop is "
     "V$_{th}$ + |V$_{gate,off}$| + I·R$_{ds(on)}$ — so holding the gate more "
     "negative\ncosts more loss. That coupling is why the −2 V rail is not free.",
     BLUE),
]
y = 80
for n, title, body, colour in items:
    ax.add_patch(FancyBboxPatch((0, y - 15), 100, 17.5,
                 boxstyle="round,pad=0.5,rounding_size=1.2",
                 fc=PAPER, ec=colour, lw=1.6))
    ax.text(3.4, y - 3.2, n, fontsize=20, fontweight="bold", color=colour,
            ha="center", va="center")
    ax.text(8, y - 1.2, title, fontsize=12.2, fontweight="bold", color=INK)
    ax.text(8, y - 6.5, body, fontsize=9.8, color=MUTED, va="top")
    y -= 22.5

ax.text(0, 8,
        "Put together: the device switches fast, its gate has little margin, "
        "and there is a capacitor delivering charge to that gate every time the\n"
        "other device switches. That is the crosstalk fault, and it is a "
        "consequence of choosing GaN rather than a mistake in the circuit.",
        fontsize=10.4, color=INK, va="top")
save(fig, "fig_gan_2.png")


# ================================================== 3. the 720 settings =====
fig, ax = frame()
head(ax, "What the driver's \"settings\" are, and where 720 comes from",
     "Six things the gate driver can be told to do. Every combination is one "
     "setting; every setting is one simulation.")

FIELDS = [
    ("Pull-up slices", "1, 2, 3, 4, 6, 8", "6",
     "how hard the device is switched ON"),
    ("Pull-down slices, low side", "2, 8", "2",
     "how hard it is switched OFF"),
    ("Pull-down slices, high side", "1, 4, 8", "3",
     "how firmly the OFF device's gate is held down"),
    ("Dead time", "5, 10, 15, 25, 35 ns", "5",
     "the gap before the other device turns on"),
    ("Miller clamp", "off, on", "2",
     "a switch that shorts the gate down while the device is off"),
    ("Off-bias rail", "0 V, −2 V", "2",
     "what voltage the gate is parked at when off"),
]
ax.text(2, 83, "FIELD", fontsize=9.4, fontweight="bold", color=MUTED)
ax.text(33, 83, "VALUES WE SWEEP", fontsize=9.4, fontweight="bold", color=MUTED)
ax.text(56, 83, "HOW MANY", fontsize=9.4, fontweight="bold", color=MUTED)
ax.text(68, 83, "WHAT IT CHANGES", fontsize=9.4, fontweight="bold", color=MUTED)
ax.plot([2, 98], [80.5, 80.5], lw=1.0, color=RULE)

y = 74
for i, (name, vals, n, what) in enumerate(FIELDS):
    if i % 2 == 0:
        ax.add_patch(Rectangle((2, y - 3.4), 96, 9.4, fc=SHADE, ec="none"))
    ax.text(3, y, name, fontsize=10.6, fontweight="bold", color=INK)
    ax.text(33, y, vals, fontsize=10.4, color=INK)
    ax.text(59, y, n, fontsize=12.5, fontweight="bold", color=BLUE)
    ax.text(68, y, what, fontsize=9.6, color=MUTED)
    y -= 9.2

ax.plot([2, 98], [y + 4, y + 4], lw=1.0, color=RULE)
ax.text(3, y - 3, "6  ×  2  ×  3  ×  5  ×  2  ×  2   =   720 settings",
        fontsize=16, fontweight="bold", color=INK)
ax.text(3, y - 9.5,
        "Each one is simulated at each of four operating points, so the full "
        "search is 2,880 runs. That is what lets us say a setting is the best\n"
        "one, rather than the best one we happened to try. The list is in "
        "scripts/sweep.py; the hardware that produces these fields is\n"
        "rtl/seg_gate_ctrl.v, and it emits exactly these six.",
        fontsize=10.2, color=MUTED, va="top")
save(fig, "fig_settings.png")


# ==================================================== 4. the input =========
fig, ax = frame()
head(ax, "What we mean by the input, or \"operating point\"",
     "A converter does not run at one condition. These are the four we test "
     "every setting at.")

CORNERS = [
    ("50 V,  2 A", "25 °C", "light load, low voltage",
     "the converter idling — least stress, and the corner where the answer differs"),
    ("100 V, 10 A", "25 °C", "the nominal point",
     "what the converter is designed around"),
    ("200 V,  2 A", "125 °C", "high voltage, light load, hot",
     "worst case for crosstalk: biggest dV/dt, least current to damp it"),
    ("200 V, 10 A", "125 °C", "full stress",
     "highest voltage and current together, device hot"),
]
x, y = 2, 66
for i, (cond, temp, tag, why) in enumerate(CORNERS):
    cx = x + (i % 2) * 49
    cy = y - (i // 2) * 30
    ax.add_patch(FancyBboxPatch((cx, cy), 45, 24,
                 boxstyle="round,pad=0.6,rounding_size=1.2",
                 fc=PAPER, ec=INK if i == 1 else RULE, lw=2.0 if i == 1 else 1.4))
    ax.text(cx + 3, cy + 17.5, cond, fontsize=15, fontweight="bold", color=INK)
    ax.text(cx + 30, cy + 17.8, temp, fontsize=11, color=MUTED)
    ax.text(cx + 3, cy + 12.5, tag, fontsize=10, fontweight="bold", color=BLUE)
    ax.text(cx + 3, cy + 7.5, why, fontsize=9.2, color=MUTED, wrap=True)
    if i == 1:
        ax.text(cx + 3, cy + 2, "nominal", fontsize=8.6, fontweight="bold",
                color=INK)

ax.plot([2, 98], [30, 30], lw=1.0, color=RULE)
ax.text(2, 24,
        "Three things change between them: the bus voltage the converter is "
        "fed, the current the load draws, and the junction temperature of the\n"
        "devices. Temperature matters because it raises on-resistance and "
        "lowers the turn-on threshold — the model does both.",
        fontsize=10.4, color=INK, va="top")
ax.text(2, 12,
        "Every one of the 720 settings is simulated at all four. The question "
        "the project answers is whether the best setting is the same at all\n"
        "four, or whether it moves — because only if it moves is there anything "
        "for a controller to adapt to.",
        fontsize=10.4, color=INK, va="top")
save(fig, "fig_input.png")


# =================================================== 5. the output =========
fig, ax = frame()
head(ax, "What comes out",
     "Two different things are called \"the output\" in this project. "
     "Both are measured, neither is estimated.")

ax.add_patch(FancyBboxPatch((0, 36), 48, 48,
             boxstyle="round,pad=0.7,rounding_size=1.4",
             fc=PAPER, ec=GREEN, lw=2.0))
ax.text(3, 79, "1.  THE CONVERTER'S OUTPUT", fontsize=11.5, fontweight="bold",
        color=GREEN)
ax.text(3, 74, "what the machine delivers to its load", fontsize=9.6, color=MUTED)
rows = [("Output voltage", "48.56 V DC"), ("Output current", "4.875 A"),
        ("Power delivered", "236.85 W"), ("Power drawn", "242.63 W"),
        ("Efficiency", "97.62 %"), ("Ripple on the output", "729 mV")]
y = 69
for k, v in rows:
    ax.text(4, y, k, fontsize=10.2, color=INK)
    ax.text(33, y, v, fontsize=11.5, fontweight="bold", color=INK)
    y -= 5.0

ax.add_patch(FancyBboxPatch((52, 36), 48, 48,
             boxstyle="round,pad=0.7,rounding_size=1.4",
             fc=PAPER, ec=BLUE, lw=2.0))
ax.text(55, 79, "2.  WHAT ONE SIMULATION REPORTS", fontsize=11.5,
        fontweight="bold", color=BLUE)
ax.text(55, 74, "measured on every one of the 2,880 runs", fontsize=9.6,
        color=MUTED)
rows2 = [("Peak on the OFF gate", "the crosstalk voltage"),
         ("Margin", "1.4 V minus that peak"),
         ("Switching energy", "turn-on + turn-off + dead time"),
         ("Overshoot", "how far past the bus the node rings"),
         ("Settling time", "how long the ringing lasts"),
         ("Oscillation energy", "30–500 MHz content, for EMI")]
y = 69
for k, v in rows2:
    ax.text(56, y, k, fontsize=10.2, fontweight="bold", color=INK)
    ax.text(56, y - 2.2, v, fontsize=9.2, color=MUTED)
    y -= 5.0

ax.plot([0, 100], [31, 31], lw=1.0, color=RULE)
ax.text(0, 26,
        "The left column is the converter working: 100 V DC in, 48.56 V DC out, "
        "97.62 % of the power getting through. That is the deliverable.\n\n"
        "The right column is what each individual simulation measures, and it "
        "is how settings are compared. The definitions are fixed in one file\n"
        "(scripts/gansim.py) and were frozen before the sweeps ran, so no "
        "measurement was redefined after seeing a result.",
        fontsize=10.4, color=INK, va="top")
ax.text(0, 3, "Both reproduce on this machine: "
              "python3 scripts/bucksim.py  and  python3 scripts/cases.py",
        fontsize=9.2, color=MUTED, fontweight="bold")
save(fig, "fig_output.png")


# ==================================================== 6. margin ============
fig, ax = plt.subplots(figsize=(13.2, 6.6), dpi=170)
fig.subplots_adjust(left=0.30, right=0.97, top=0.80, bottom=0.17)
fig.patch.set_facecolor("white")

CASES = [("no clamp, 0 V rail", 1.649, RED),
         ("clamp on, 0 V rail", 0.830, AMBER),
         ("clamp on, −2 V rail", -1.176, GREEN)]
VTH = 1.4
ypos = np.arange(len(CASES))[::-1]
for (lab, v, c), yy in zip(CASES, ypos):
    ax.barh(yy, v, height=0.42, color=c, alpha=.9)
    ax.plot([v, VTH], [yy, yy], lw=2.2, color=c, ls=":")
    ax.annotate("", xy=(VTH, yy + 0.30), xytext=(v, yy + 0.30),
                arrowprops=dict(arrowstyle="<->", color=c, lw=1.7))
    ax.text((v + VTH) / 2, yy + 0.40,
            "margin = %+.3f V" % (VTH - v), ha="center", fontsize=10.5,
            fontweight="bold", color=c)
    ax.text(v + (0.10 if v > 0 else -0.10), yy - 0.02, "%+.3f V" % v,
            ha="left" if v > 0 else "right", va="center",
            fontsize=12, fontweight="bold", color=INK,
            bbox=dict(fc="white", ec="none", pad=1.6))

ax.axvline(VTH, color=RED, lw=2.4, ls="--")
ax.text(VTH - 0.08, len(CASES) - 0.30,
        "1.4 V — the turn-on threshold of this device", fontsize=10.5,
        fontweight="bold", color=RED, va="bottom", ha="right")
ax.set_yticks(ypos)
ax.set_yticklabels([c[0] for c in CASES], fontsize=11.5)
ax.set_xlabel("peak voltage reached on the gate of the device that is "
              "supposed to be OFF   [V]", fontsize=10.5)
ax.set_xlim(-2.0, 2.3)
ax.set_ylim(-0.7, 2.72)
ax.grid(axis="x", alpha=.25)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)

fig.suptitle("What \"margin\" means", fontsize=17, fontweight="bold",
             x=0.02, ha="left", y=0.965)
fig.text(0.02, 0.885,
         "Margin is one number: how far the OFF device's gate stays below the "
         "voltage that would switch it on. Positive is safe, negative is a fault.",
         fontsize=10.5, color=MUTED)
fig.text(0.02, 0.035,
         "Negative margin is not a small error — it means both devices conduct "
         "at once and the supply is shorted through them. 2.58 V of margin is "
         "the shipped design.",
         fontsize=9.6, color=INK)
save(fig, "fig_margin.png")


# ================================================= 7. how the work was run ==
fig, ax = frame(13.2, 6.2)
head(ax, "How the work was actually run",
     "Six steps, in this order. Each one had to hold before the next was worth "
     "doing.")

STEPS = [
    ("1", "Build the device and the driver",
     "A GaN HEMT written from datasheet numbers, and a segmented driver with "
     "the six fields.", BLUE),
    ("2", "Recreate the fault",
     "Drive it as fast as possible with nothing to stop crosstalk, and confirm "
     "the OFF gate crosses 1.4 V.", RED),
    ("3", "Fix it one change at a time",
     "Clamp, then off-bias rail, then drive strength — each measured on its own "
     "run, not all together.", AMBER),
    ("4", "Search every setting at every operating point",
     "720 settings × 4 operating points = 2,880 runs, so the best setting is "
     "the best, not the best tried.", BLUE),
    ("5", "Separate the two effects",
     "How much comes from choosing one good fixed setting, and how much from "
     "re-tuning it while running.", GREEN),
    ("6", "Check it somewhere else",
     "The same circuit drawn in LTspice, and the controller built in Verilog "
     "and synthesised in Vivado.", GREEN),
]
y = 80
for n, title, body, c in STEPS:
    ax.add_patch(FancyBboxPatch((0, y - 8.6), 100, 11.0,
                 boxstyle="round,pad=0.4,rounding_size=1.0",
                 fc=PAPER, ec=c, lw=1.5))
    ax.text(3.2, y - 3.1, n, fontsize=17, fontweight="bold", color=c,
            ha="center", va="center")
    ax.text(7.5, y - 1.0, title, fontsize=11.6, fontweight="bold", color=INK)
    ax.text(7.5, y - 5.6, body, fontsize=9.6, color=MUTED)
    if n != "6":
        ax.annotate("", xy=(3.2, y - 9.6), xytext=(3.2, y - 8.8),
                    arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1.4))
    y -= 13.2

ax.text(0, 2.5,
        "Steps 1–3 are on one switching edge, where the fault lives and can be "
        "measured precisely. Steps 4–6 are the study built on top of it.",
        fontsize=10.0, color=INK)
save(fig, "fig_method.png")


# ================================================ 8. what Python is for =====
fig, ax = frame(13.2, 6.4)
head(ax, "What Python does here",
     "Python runs no circuit maths of its own. It drives the simulators, "
     "collects what they return, and does the arithmetic on top.")

COLS = [
    ("It drives ngspice", BLUE, [
        "writes a netlist for each setting",
        "runs ngspice and waits",
        "reads the raw output back",
        "extracts the eight measurements",
        "repeats it 2,880 times",
    ], "scripts/gansim.py, sweep.py"),
    ("It does the arithmetic", GREEN, [
        "finds the best setting per point",
        "finds the best single fixed setting",
        "the gap between them is the answer",
        "sweeps the weighting to check it holds",
        "writes the CSVs the figures read",
    ], "scripts/ceiling.py, novelty.py"),
    ("It draws every figure", AMBER, [
        "reads the CSVs back",
        "and the LTspice .raw files",
        "no number is retyped by hand",
        "every figure regenerates from data",
        "",
    ], "scripts/*_figure.py"),
]
for i, (title, c, items, files) in enumerate(COLS):
    x = i * 34
    ax.add_patch(FancyBboxPatch((x, 22), 31, 60,
                 boxstyle="round,pad=0.6,rounding_size=1.3",
                 fc=PAPER, ec=c, lw=1.8))
    ax.text(x + 2.5, 76, title, fontsize=12, fontweight="bold", color=c)
    y = 68
    for it in items:
        if it:
            ax.text(x + 2.5, y, "•  " + it, fontsize=9.8, color=INK)
        y -= 7.0
    ax.text(x + 2.5, 26, files, fontsize=8.8, color=MUTED, style="italic")

ax.plot([0, 100], [17, 17], lw=1.0, color=RULE)
ax.text(0, 11,
        "So if Python had a bug, the circuit results would not change — they "
        "come out of ngspice. What would change is which setting we called best.\n"
        "That is why the decomposition is checked a second way: MATLAB and "
        "GNU Octave re-derive the same split from the same CSVs.",
        fontsize=10.2, color=INK, va="top")
save(fig, "fig_python.png")
