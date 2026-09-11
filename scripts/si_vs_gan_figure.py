# -*- coding: utf-8 -*-
"""si_vs_gan_figure.py -- the Si-vs-GaN frequency sweep, drawn.

    python3 scripts/si_vs_gan_figure.py

Reads results/si_vs_gan_sweep.txt rather than carrying its own copy of the
numbers, so the figure cannot drift from the measurement that produced it.
scripts/si_vs_gan_sweep.py owns those numbers; this file only draws them.

WHY TWO PANELS AND NOT ONE
  Loss is in watts and efficiency is in per cent. Putting both on one pair
  of axes would need two y-scales, which is the one thing a chart must not
  do -- the reader cannot tell which line belongs to which scale, and the
  crossing point is an artefact of where the scales were pinned. Two panels
  sharing an x-axis says the same thing without the lie.

  Palette is the deck's existing pair (slots 1 and 2 of the validated
  theme), re-checked with the six-check validator: adjacent CVD dE 24.7
  protan / 32.7 tritan, normal-vision dE 33.6, all five checks PASS.
"""
import os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

# deck palette -- same two slots used by paper_figs.py
GAN, SI = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1a1a19", "#5c5c5a", "#dedddb"
plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": .5,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.6,
})

ROW = re.compile(r"^\s*(\S+)\s+([\d.]+) W\s+([\d.]+) W\s+([\d.]+) %\s+([\d.]+) %\s+(\d+) %")


def read(section):
    """Pull one sweep's rows out of the saved results file."""
    txt = open(os.path.join(RES, "si_vs_gan_sweep.txt")).read()
    block = txt.split(section)[1].split("SWEEP")[0]
    out = []
    for line in block.splitlines():
        m = ROW.match(line)
        if m:
            out.append((m.group(1), float(m.group(2)), float(m.group(3)),
                        float(m.group(4)), float(m.group(5)), int(m.group(6))))
    return out


def fhz(tag):
    t = tag.lower()
    return float(t.replace("meg", "")) * 1e6 if "meg" in t else float(t.replace("k", "")) * 1e3


def main():
    rows = read("FREQUENCY SWEEP")
    x  = [fhz(r[0]) / 1e3 for r in rows]          # kHz
    lg = [r[1] for r in rows]
    ls = [r[2] for r in rows]
    eg = [r[3] for r in rows]
    es = [r[4] for r in rows]

    fig, (a, b) = plt.subplots(1, 2, figsize=(10.0, 3.5))

    # ---- panel A : loss ------------------------------------------------
    a.plot(x, ls, color=SI,  marker="o", ms=4.5, label="Si MOSFET")
    a.plot(x, lg, color=GAN, marker="o", ms=4.5, label="GaN HEMT")
    a.set_xlabel("Switching frequency (kHz)")
    a.set_ylabel("Power wasted (W)")
    a.set_title("Silicon's loss grows with frequency. GaN's does not.", fontsize=9)
    a.set_ylim(0, max(ls) * 1.22)
    # direct labels: identity carried by position as well as hue, and the
    # legend below repeats it, so nothing rests on colour alone
    a.annotate("Si MOSFET", (x[-1], ls[-1]), color=SI, fontsize=8,
               xytext=(-6, 9), textcoords="offset points", ha="right",
               fontweight="bold")
    a.annotate("GaN HEMT", (x[-1], lg[-1]), color=GAN, fontsize=8,
               xytext=(-6, 9), textcoords="offset points", ha="right",
               fontweight="bold")
    a.annotate("%.1f W -> %.1f W\n%.1fx more" % (ls[0], ls[-1], ls[-1] / ls[0]),
               (x[-1], ls[-1]), color=MUTED, fontsize=7.5,
               xytext=(-8, -26), textcoords="offset points", ha="right")
    a.annotate("stays between %.1f and %.1f W" % (min(lg), max(lg)),
               (x[len(x) // 2], lg[len(x) // 2]), color=MUTED, fontsize=7.5,
               xytext=(0, -22), textcoords="offset points", ha="center")
    a.legend(loc="upper left", fontsize=7.5)

    # ---- panel B : efficiency -----------------------------------------
    b.plot(x, es, color=SI,  marker="o", ms=4.5, label="Si MOSFET")
    b.plot(x, eg, color=GAN, marker="o", ms=4.5, label="GaN HEMT")
    b.set_xlabel("Switching frequency (kHz)")
    b.set_ylabel("Converter efficiency (%)")
    b.set_title("So silicon's efficiency falls away and GaN's holds.", fontsize=9)
    b.set_ylim(min(es) - 3, 100)
    b.annotate("Si MOSFET", (x[-1], es[-1]), color=SI, fontsize=8,
               xytext=(-6, -14), textcoords="offset points", ha="right",
               fontweight="bold")
    b.annotate("GaN HEMT", (x[-1], eg[-1]), color=GAN, fontsize=8,
               xytext=(-6, 7), textcoords="offset points", ha="right",
               fontweight="bold")
    b.annotate("%.1f %% -> %.1f %%" % (es[0], es[-1]), (x[-1], es[-1]),
               color=MUTED, fontsize=7.5, xytext=(-8, -27),
               textcoords="offset points", ha="right")
    b.annotate("%.1f %% at 1 MHz" % eg[-1], (x[-1], eg[-1]), color=MUTED,
               fontsize=7.5, xytext=(-8, 20), textcoords="offset points",
               ha="right")
    b.legend(loc="lower left", fontsize=7.5)

    fig.tight_layout()
    out = os.path.join(RES, "fig_si_vs_gan.png")
    fig.savefig(out)
    plt.close(fig)
    print("fig_si_vs_gan.png")


if __name__ == "__main__":
    main()
