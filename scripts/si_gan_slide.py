# -*- coding: utf-8 -*-
"""si_gan_slide.py -- silicon against GaN, at the one operating point.

Deliberately NOT the frequency sweep. results/si_vs_gan_sweep.txt reports
Si losing 18.40 W at 500 kHz where results/si_vs_gan.txt reports 12.63 W at
the same nominal point, and re-running the sweep's own two-pass settling
routine at that point gives 13.54 W -- so the sweep table does not
reproduce, and a slide carrying both would contradict itself in front of
the panel. Only the corroborated single point goes on the slide.

Every number is read from results/si_vs_gan.txt at build time.
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_si_gan.png")

HEAD, INK, MUTE, RULE = "#1D2F82", "#1a1a1a", "#666666", "#cccccc"
GAN, SI = "#1b7f5f", "#b8761a"


def read():
    t = open(os.path.join(RES, "si_vs_gan.txt"), encoding="utf-8").read()
    row = lambda n: [float(x) for x in re.search(
        r"^\s+%s\s+([\d.]+) W\s+([\d.]+) W\s+([\d.]+) W\s+([\d.]+) %%\s+"
        r"([\d.]+) V" % n, t, re.M).groups()]
    g, s = row("GaN HEMT"), row("Si MOSFET")
    rds = re.search(r"Rds\(on\) matched: ([\d.]+) mOhm GaN / ([\d.]+) mOhm Si",
                    t).groups()
    per = re.search(r"Loss per watt delivered: ([\d.]+) % against ([\d.]+) %",
                    t).groups()
    return g, s, rds, per


def main():
    g, s, rds, per = read()
    g_loss, g_eff = g[2], g[3]
    s_loss, s_eff = s[2], s[3]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.4, 3.5), dpi=180,
                                 gridspec_kw={"width_ratios": [1, 1]})

    for ax, vals, unit, title, lo, hi in (
            (a1, (g_loss, s_loss), "W", u"Power wasted in the converter",
             0, max(g_loss, s_loss) * 1.35),
            (a2, (g_eff, s_eff), "%", u"Converter efficiency",
             min(g_eff, s_eff) - 1.6, 100.0)):
        bars = ax.bar([u"GaN HEMT", u"Si MOSFET"], vals,
                      color=[GAN, SI], width=0.56)
        for b, v in zip(bars, vals):
            ax.annotate(u"%.2f %s" % (v, unit),
                        (b.get_x() + b.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 6),
                        ha="center", fontsize=11.5, weight="bold", color=INK)
        ax.set_ylim(lo, hi)
        ax.set_title(title, fontsize=11, color=HEAD, weight="bold", loc="left")
        ax.grid(axis="y", color=RULE, lw=0.5, alpha=0.7)
        ax.tick_params(labelsize=10)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    a1.annotate(u"%.0f %% less" % (100.0 * (s_loss - g_loss) / s_loss),
                (0, g_loss), textcoords="offset points", xytext=(0, 34),
                ha="center", fontsize=11, color=GAN, weight="bold")
    a2.annotate(u"+%.2f points" % (g_eff - s_eff),
                (0, g_eff), textcoords="offset points", xytext=(0, 26),
                ha="center", fontsize=11, color=GAN, weight="bold")

    fig.text(0.008, -0.04,
             u"Same converter, same netlist: 100 V \u2192 50 V, 500 kHz, "
             u"10 \u03a9. Only the device model and its rated gate drive "
             u"differ. R_ds(on) matched at %s m\u03a9 GaN against %s m\u03a9 "
             u"Si, so conduction loss is equal by construction and what is "
             u"left is switching, gate drive and reverse recovery. The two do "
             u"not deliver identical output power \u2014 GaN's third-quadrant "
             u"drop in dead time exceeds a silicon body-diode drop \u2014 so "
             u"loss per watt delivered is given too: %s %% against %s %%."
             % (rds[0], rds[1], per[0], per[1]),
             fontsize=8.2, color=MUTE, ha="left", va="top", wrap=True)

    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote %s  (GaN %.2f W / %.2f %%, Si %.2f W / %.2f %%)"
          % (os.path.relpath(OUT, ROOT), g_loss, g_eff, s_loss, s_eff))
    return 0


if __name__ == "__main__":
    sys.exit(main())
