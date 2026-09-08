"""
ltspice_annotated_figure.py -- the LTspice result, with the meaning written on it.

A waveform is only evidence to somebody who already knows which trace to look
at and what number matters. This draws LTspice's own output and says, on the
picture: this fall is the cause, this rise is the effect, this line is where
the device turns on, and this is the number.

Data comes from the .raw files LTspice wrote, read by ltspice_raw.py -- not
from an ngspice re-run that happens to agree.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ltspice_raw

def provenance(path):
    """Read the .raw header back so the figure can state, on its face, which
    program wrote the data and when. A redrawn plot that merely CLAIMS a
    source is worth nothing; this quotes the file."""
    blob = open(path, "rb").read(4096)
    i = blob.find(u"Binary:\n".encode("utf-16-le"))
    head = blob[:i if i != -1 else 3700].decode("utf-16-le", errors="ignore")
    got = {}
    for line in head.splitlines():
        for key in ("Title:", "Date:", "Command:"):
            if line.startswith(key):
                got[key.rstrip(":")] = line[len(key):].strip()
    return got


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LT   = os.path.join(ROOT, "ltspice")
OUT  = os.path.join(ROOT, "results", "fig_ltspice_annotated.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
RED, GREEN, BLUE = "#B00000", "#1E7B34", "#1F4E9C"
VTH = 1.4
# The plot window starts after the dead time. At 2.000 us the high side is
# still being turned OFF and its gate is at +5 V; including that makes the
# largest value in frame the turn-off itself rather than the crosstalk kick,
# and every "peak" annotation lands on the wrong feature.
T0, T1 = 2.0125e-6, 2.115e-6
TMEAS  = 2.015e-6                     # the window .meas uses, and so does this
plt.rcParams["font.family"] = "DejaVu Sans"

CASES = [
    ("A_design_no_clamp_FAILS.raw",
     "A  —  no Miller clamp, gate held at 0 V when off", RED, False),
    ("C_design_clamp_and_neg_bias.raw",
     "C  —  Miller clamp on, gate held at −2 V when off", GREEN, True),
]

fig, ax = plt.subplots(2, 2, figsize=(13.2, 7.0), dpi=170, sharex="col")
fig.subplots_adjust(left=0.062, right=0.985, top=0.80, bottom=0.115,
                    hspace=0.16, wspace=0.17)

for col, (fname, title, colour, safe) in enumerate(CASES):
    d = ltspice_raw.read(os.path.join(LT, fname))
    t = d["time"]
    sw = d["V(sw)"]
    g = d["V(hsg)"] - d["V(sw)"]
    m = (t >= T0) & (t <= T1)
    tu = (t[m] - T0) * 1e9                      # ns from the start of the window

    # ---------------- top: the cause ------------------------------------
    a = ax[0][col]
    a.plot(tu, sw[m], lw=1.5, color=BLUE)
    a.set_title(title, fontsize=11, fontweight="bold", loc="left", color=colour)
    a.set_ylabel("switch node\nV(sw)   [V]", fontsize=9.5)
    a.grid(alpha=.25)
    a.set_ylim(-25, 135)
    a.set_xlim(0, (T1 - T0) * 1e9)

    i_fall = int(np.argmax(np.abs(np.diff(sw[m]))))
    t_fall = tu[i_fall]
    a.annotate("the low-side device turns on\nand this node falls 100 V\nin a few nanoseconds",
               xy=(t_fall, 55), xytext=(t_fall + 26, 96),
               fontsize=9, color=INK,
               arrowprops=dict(arrowstyle="->", color=INK, lw=1.4))
    a.text(1.5, 108, "THIS IS THE CAUSE", fontsize=8.6, fontweight="bold",
           color=MUTED)

    # ---------------- bottom: the effect ---------------------------------
    b = ax[1][col]
    b.plot(tu, g[m], lw=1.6, color=colour)
    b.axhline(VTH, ls="--", lw=1.6, color=RED)
    b.set_ylabel("gate of the device that\nis supposed to be OFF\nV(hsg,sw)   [V]", fontsize=9.5)
    b.set_xlabel("time from %.3f µs   [ns]" % (T0 * 1e6), fontsize=9.5)
    b.grid(alpha=.25)
    b.set_ylim(-3.0, 2.6)
    b.set_xlim(0, (T1 - T0) * 1e9)

    b.text((T1 - T0) * 1e9 - 2, VTH + 0.16,
           "1.4 V — above this line the device turns ON",
           fontsize=8.8, fontweight="bold", color=RED, ha="right")

    mm = (t[m] >= TMEAS)
    pk = float(np.nanmax(g[m][mm]))
    ipk = int(np.arange(len(tu))[mm][int(np.nanargmax(g[m][mm]))])
    b.plot([tu[ipk]], [pk], "o", ms=8, color=colour, zorder=5)
    b.annotate("%+.3f V" % pk, (tu[ipk], pk), textcoords="offset points",
               xytext=(14, 10 if safe else 6), fontsize=13, fontweight="bold",
               color=colour)

    if safe:
        b.annotate("", xy=(tu[ipk], pk), xytext=(tu[ipk], VTH),
                   arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.8))
        b.text(tu[ipk] + 5, (pk + VTH) / 2 - 0.12,
               "%.2f V of margin\nthe device stays off" % (VTH - pk),
               fontsize=9.6, fontweight="bold", color=GREEN)
        b.text(1.5, -2.72, "the −2 V rail parks the gate down here, so the same "
                           "kick lands far below the line",
               fontsize=8.8, color=MUTED)
    else:
        b.annotate("it crosses the line:\nthe device turns on when\nit must not — shoot-through",
                   xy=(tu[ipk], pk), xytext=(tu[ipk] + 22, -1.5),
                   fontsize=9.2, fontweight="bold", color=RED,
                   arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
        b.text(1.5, -2.72, "the gate is parked at 0 V, so the kick starts from "
                           "0 V and only needs 1.4 V to do damage",
               fontsize=8.8, color=MUTED)
    b.text(1.5, 2.15, "THIS IS THE EFFECT", fontsize=8.6, fontweight="bold",
           color=MUTED)

pv = provenance(os.path.join(LT, CASES[0][0]))
fig.suptitle("LTspice output — redrawn from its own .raw file so it can be "
             "labelled", fontsize=13, fontweight="bold", y=0.978)
fig.text(0.5, 0.925,
         "This is not a screenshot. The traces are LTspice's data, read out of "
         "the file it wrote, and replotted so the meaning can be marked on it. "
         "The screenshots of LTspice itself are alongside.",
         ha="center", fontsize=9.6, color=MUTED)
fig.text(0.5, 0.885,
         "Same circuit both sides; the only difference is the Miller clamp and "
         "the off-bias rail. LTspice measures +1.647556 V and −1.176857 V — "
         "ngspice measures +1.6486 V and −1.1757 V on the same netlist.",
         ha="center", fontsize=9.4, color=MUTED)
fig.text(0.012, 0.012,
         "Source:  %s\nWritten by:  %s        %s"
         % (os.path.basename(pv.get("Title", "?")),
            pv.get("Command", "?"), pv.get("Date", "?")),
         ha="left", va="bottom", fontsize=8.0, color=MUTED,
         family="DejaVu Sans Mono")
fig.savefig(OUT, dpi=170, facecolor="white")
print("wrote", OUT)
