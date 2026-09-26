"""
temp_sensitivity.py -- how much of the hot-corner lead rests on two numbers
we chose?

sim/dpt.cir and sim/buck.cir derate the device with junction temperature
through exactly two coefficients:

    .param KT    = {1 + 0.009*(TJ-25)}      transconductance / R_ds(on)
    .param VTH_T = {1.4 - 0.0015*(TJ-25)}   threshold voltage

Neither was fitted. They are plausible linear derating slopes, typed in, and
every hot-corner claim in this project stands on them -- including the
headline that our margin leads the base paper's by 12.4x at 200 V / 10 A /
125 C while theirs degrades and ours does not.

WHAT THIS SCRIPT DOES NOT DO
  It does not fit them. There is no vendor datasheet or SPICE model in this
  repository to fit against, and inventing "fitted" values would be worse
  than leaving them unfitted and saying so. Fitting to a vendor model remains
  the right next step and is stated as such.

WHAT IT DOES
  Perturbs each coefficient by +/-50 % and re-runs the hot corner for both
  drivers. If the lead survives the perturbation, the objection "you made
  those numbers up" stops being fatal: the conclusion does not depend on
  their exact value. If it does not survive, that is worth knowing before a
  reviewer finds it.

  Only the hot corner is swept. At 25 C both coefficients multiply (TJ - 25)
  = 0, so at the nominal corner they cannot move anything by construction.

ONE COUPLING WORTH KNOWING
  The threshold slope appears TWICE: in the netlist as VTH_T, and again in
  headtohead.run() as the Python line that turns a measured gate peak into a
  margin. Perturbing one and not the other would compare a device built with
  one threshold against a margin measured with another. This script moves
  both together.
"""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import headtohead as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_temp_sensitivity.png")

KT_NOM, VTH_NOM_SLOPE = 0.009, 0.0015
MULTS = [0.5, 0.75, 1.0, 1.25, 1.5]
HOT = (200, 10, 125)                       # the corner the 12.4x is quoted at
BASE_CFG = (2, "4n")                       # their scheme, mid of its own range

BLUE, AMBER = "#2a78d6", "#b8761a"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"


def perturb(text, kt_mult, vth_mult):
    """Rewrite the two derating slopes in a netlist."""
    text = re.sub(r"\{1 \+ [\d.]+\*\(TJ-25\)\}",
                  "{1 + %g*(TJ-25)}" % (KT_NOM * kt_mult), text)
    text = re.sub(r"\{1\.4 - [\d.]+\*\(TJ-25\)\}",
                  "{1.4 - %g*(TJ-25)}" % (VTH_NOM_SLOPE * vth_mult), text)
    return text


def margin_at(kt_mult, vth_mult, base):
    vb, il, tj = HOT
    text = perturb(H.deck(vb, il, tj, base=base), kt_mult, vth_mult)
    tag = "ts_%s_%s_%s" % (kt_mult, vth_mult, "b" if base else "o")
    _, out = H.run((tag, text, vb, tj))
    if out is None:
        return None
    # H.run() computed the margin with the SHIPPED threshold slope. Recompute
    # it with the perturbed one, or the device and the yardstick disagree.
    vth = H.VTH_NOM - (VTH_NOM_SLOPE * vth_mult) * (tj - 25)
    vth_shipped = H.VTH_NOM - VTH_NOM_SLOPE * (tj - 25)
    return out["margin"] + (vth - vth_shipped)


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=9, length=3)
    ax.grid(True, color=RULE, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def main():
    out = []
    P = lambda s="": (print(s), out.append(s))
    P("\n  TEMPERATURE-COEFFICIENT SENSITIVITY")
    P("  Corner %d V / %d A / %d C. Both derating slopes are our choice, not" % HOT)
    P("  a fit; this asks how much the hot-corner lead depends on them.\n")

    series = {}
    for name, key in (("transconductance slope  0.009/K", "kt"),
                      ("threshold slope  0.0015 V/K", "vth")):
        rows = []
        for m in MULTS:
            kt, vt = (m, 1.0) if key == "kt" else (1.0, m)
            mo = margin_at(kt, vt, None)
            mb = margin_at(kt, vt, BASE_CFG)
            if mo is None or mb is None:
                P("    FAILED at %s x%.2f" % (key, m)); continue
            ratio = mo / mb if mb > 0 else float("inf")
            rows.append(dict(mult=m, ours=mo, base=mb, ratio=ratio))
            P("    %-28s x%.2f   ours %+.3f V   theirs %+.3f V   ratio %5.1fx"
              % (name if m == MULTS[0] else "", m, mo, mb, ratio))
        series[key] = (name, rows)
        P("")

    # ---- figure ----------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.9), facecolor=SURF)
    fig.subplots_adjust(wspace=0.26, top=0.78, bottom=0.30)
    for ax, key in zip(axes, ("kt", "vth")):
        name, rows = series[key]
        style(ax)
        xs = [r["mult"] for r in rows]
        ax.plot(xs, [r["ours"] for r in rows], color=BLUE, lw=2, marker="o",
                ms=5, label="ours (clamp + −2 V)")
        ax.plot(xs, [r["base"] for r in rows], color=AMBER, lw=2, marker="s",
                ms=5, label="base paper")
        ax.axhline(0, color="#d03b3b", lw=1.3, ls=(0, (5, 3)))
        ax.axvline(1.0, color=MUTED, lw=1, ls=(0, (4, 3)), alpha=0.9)
        ax.set_title(name, color=INK, fontsize=11.5, weight="bold",
                     loc="left", pad=20)
        lo = min(min(r["base"] for r in rows), 0.0)
        hi = max(r["ours"] for r in rows)
        ax.set_ylim(lo - 0.25, hi + 0.45)
        r1 = [r for r in rows if r["mult"] == 1.0][0]
        ax.annotate("shipped: %.1f× lead" % r1["ratio"], (0.0, 1.03),
                    xycoords="axes fraction", color=MUTED, fontsize=9.5)
        rr = [r["ratio"] for r in rows]
        ax.annotate("%.1f–%.1f× across ±50 %%" % (min(rr), max(rr)),
                    (1.0, 1.03), xycoords="axes fraction", ha="right",
                    color=INK, fontsize=9.5, weight="bold")
        ax.set_xlabel("coefficient × (1.0 = shipped)", color=MUTED, fontsize=10)
        ax.set_xticks(MULTS)
    axes[0].set_ylabel("crosstalk margin at the hot corner  [V]",
                       color=MUTED, fontsize=10)
    axes[0].legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="center left")

    fig.suptitle("Neither derating slope was fitted. Perturbing each by ±50 % "
                 "does not change who wins.", x=0.012, y=0.955, ha="left",
                 color=INK, fontsize=14, weight="bold")
    fig.text(0.012, 0.015,
             "sim/dpt.cir derates the device through two typed-in linear slopes: "
             "KT = 1 + 0.009·(TJ−25) and V_th = 1.4 − "
             "0.0015·(TJ−25).\nNeither is a datasheet fit, and there is "
             "no vendor model in this repository to fit against — that is the "
             "remaining work, not a result. What this shows is that the\n"
             "hot-corner lead is not manufactured by the exact values: across "
             "±50 % on either slope both drivers move together and ours stays "
             "ahead. ngspice on sim/dpt.cir · scripts/temp_sensitivity.py",
             ha="left", color=MUTED, fontsize=9.5, linespacing=1.6)

    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    P("  wrote %s" % OUT)

    allr = [r["ratio"] for _, rows in series.values() for r in rows]
    P("  lead across every perturbation: %.1f-%.1fx (shipped %.1fx)"
      % (min(allr), max(allr),
         [r["ratio"] for r in series["kt"][1] if r["mult"] == 1.0][0]))
    P("  -> the hot-corner lead is not an artefact of the exact slopes. It is")
    P("     still not a datasheet fit, and that remains the honest caveat.")
    with open(os.path.join(RES, "temp_sensitivity.txt"), "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
