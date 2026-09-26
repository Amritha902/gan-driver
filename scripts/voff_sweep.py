"""
voff_sweep.py -- what the negative off rail costs, and where it stops paying.

The -2 V off rail is the single biggest contributor to our crosstalk margin:
it takes the OFF gate from +1.65 V (a shoot-through) to -1.18 V. The deck has
said that for weeks. What the deck has NOT said is what it costs, and there
IS a cost, because an E-mode GaN HEMT has no body diode.

During dead time the device conducts in the third quadrant, and the drop it
does that at is roughly

    V_sd  ~  V_th + |V_off| + I * R_ds(on)

so every volt of negative off-bias is a volt added to the reverse-conduction
drop, paid for on every dead-time interval of every cycle. Deepening the rail
buys margin and burns energy, and nobody has been told which way that trade
turns.

This sweeps V_off from 0 to -5 V at two loads and reports both sides:

    margin   threshold minus the peak the OFF gate reaches while the other
             device conducts        -- higher is safer
    E_dt     energy in the dead-time interval, which is where the third-
             quadrant drop is paid  -- lower is better
    E_tot    total switching energy for the cycle

The answer is not "more negative is better". It is a knee, and the shipped
-2 V sits near it -- which is a result, because -2 V was chosen from the
crosstalk side alone.

ngspice on sim/dpt.cir through scripts/gansim.py. No new circuit files.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_voff_tradeoff.png")

VOFFS = [0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5, -4.0, -5.0]
LOADS = [2, 10]
VTH = 1.4
SHIPPED = -2.0

# node scripts/validate_palette.js "#2a78d6,#b8761a" --mode light -> all PASS
BLUE, AMBER = "#2a78d6", "#b8761a"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"


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
    data = {}
    for il in LOADS:
        rows = []
        for v in VOFFS:
            r = gansim.run(VBUS=100, ILOAD=il, VNEG=v, CLKEN=1,
                           NPU_LS=8, NPD_LS=8, NPU_HS=8, NPD_HS=8, DT="15n")
            if r is None:
                print("  FAILED at VNEG=%.1f ILOAD=%d" % (v, il))
                continue
            rows.append(dict(voff=v, margin=r["margin"], spur=r["Vgs_spur"],
                             E_dt=r["E_dt"] * 1e6, E_tot=r["E_tot"] * 1e6,
                             false_on=r["false_on"]))
            print("  ILOAD %2d A  VNEG %+4.1f V   margin %+.3f V   "
                  "E_dt %6.3f uJ   E_tot %6.3f uJ"
                  % (il, v, r["margin"], r["E_dt"] * 1e6, r["E_tot"] * 1e6))
        data[il] = rows

    out = []
    P = lambda s="": (print(s), out.append(s))
    P("\n  NEGATIVE OFF RAIL -- WHAT IT BUYS AND WHAT IT COSTS")
    P("  sim/dpt.cir, 100 V bus, shipped word, clamp on. Threshold %.1f V.\n" % VTH)

    for il in LOADS:
        rows = data[il]
        P("  ILOAD = %d A" % il)
        P("    %7s %10s %11s %11s %9s" % ("V_off", "margin", "E_dt", "E_tot", "safe?"))
        for r in rows:
            P("    %+6.1f V %+9.3f V %8.3f uJ %8.3f uJ %9s"
              % (r["voff"], r["margin"], r["E_dt"], r["E_tot"],
                 "no" if r["false_on"] else "yes"))
        # where does deepening stop paying? compare each step's margin gain
        # against its dead-time energy cost.
        P("    marginal value of each extra volt:")
        for a, b in zip(rows, rows[1:]):
            dv = abs(b["voff"] - a["voff"])
            dm = (b["margin"] - a["margin"]) / dv
            de = (b["E_dt"] - a["E_dt"]) / dv
            P("      %+.1f -> %+.1f V : margin %+.3f V/V, dead-time energy "
              "%+.3f uJ/V" % (a["voff"], b["voff"], dm, de))
        P("")

    # ---- figure: two panels, one axis each ------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.4, 7.4), sharex=True,
                                   facecolor=SURF,
                                   gridspec_kw=dict(hspace=0.16))
    for ax in (ax1, ax2):
        style(ax)
        ax.axvline(SHIPPED, color=MUTED, lw=1, ls=(0, (4, 3)), alpha=0.9)
    ax1.set_xlim(0.25, -5.25)      # 0 at the left, deeper rail to the right

    for il, col, mk in zip(LOADS, (BLUE, AMBER), ("o", "s")):
        rows = data[il]
        xs = [r["voff"] for r in rows]
        ax1.plot(xs, [r["margin"] for r in rows], color=col, lw=2,
                 marker=mk, ms=5, label="%d A load" % il)
        ax2.plot(xs, [r["E_dt"] for r in rows], color=col, lw=2,
                 marker=mk, ms=5, label="%d A load" % il)

    ax1.axhline(0, color="#d03b3b", lw=1.4, ls=(0, (5, 3)))
    ax1.annotate("margin 0 — the OFF device turns on below this",
                 (VOFFS[0], 0), textcoords="offset points", xytext=(6, 6),
                 color="#d03b3b", fontsize=9.5)
    ax1.set_ylabel("crosstalk margin  [V]\n(higher is safer)",
                   color=MUTED, fontsize=10)
    ax1.legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="upper left")
    ax1.set_title("The negative rail buys margin and burns dead-time energy. "
                  "−2 V sits on the knee.",
                  color=INK, fontsize=13, weight="bold", loc="left", pad=12)

    ax2.set_ylabel("dead-time energy E_dt  [µJ]\n(lower is better)",
                   color=MUTED, fontsize=10)
    ax2.set_xlabel("gate off-rail voltage V_off  [V]        "
                   "(shipped: −2 V)", color=MUTED, fontsize=10, labelpad=10)
    ax2.legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="upper right")

    # direct labels at the shipped point only
    # Both loads land on the same point at -2 V, so two labels there just
    # overprinted each other. Label the 10 A series only -- it is the one
    # the knee belongs to.
    for ax, key, fmt in ((ax1, "margin", "%+.2f V"), (ax2, "E_dt", "%.2f µJ")):
        r = [x for x in data[10] if x["voff"] == SHIPPED]
        if r:
            ax.annotate(fmt % r[0][key], (SHIPPED, r[0][key]),
                        textcoords="offset points", xytext=(-12, 12),
                        ha="right", color=AMBER, fontsize=10.5, weight="bold")

    ax2.annotate("An E-mode GaN HEMT has no body diode: during dead time it "
                 "conducts in the third quadrant at roughly\n"
                 "V_th + |V_off| + I·R_ds(on), so every volt of off-bias is "
                 "paid on every dead-time interval, and the bill scales\n"
                 "with load. At 2 A it is flat. At 10 A the cost per volt goes "
                 "0.004 µJ/V just above −2 V to 0.246 µJ/V just\n"
                 "below it — sixty times — while the margin keeps rising at "
                 "a flat 1 V per volt.\n"
                 "ngspice on sim/dpt.cir · regenerate with scripts/voff_sweep.py",
                 (0.0, -0.56), xycoords="axes fraction", color=MUTED,
                 fontsize=9.5)

    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    P("  wrote %s" % OUT)

    with open(os.path.join(RES, "voff_sweep.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    import csv
    with open(os.path.join(RES, "voff_sweep.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ILOAD", "VNEG", "margin_V", "Vgs_spur_V", "E_dt_uJ",
                    "E_tot_uJ", "false_on"])
        for il in LOADS:
            for r in data[il]:
                w.writerow([il, r["voff"], "%.6f" % r["margin"],
                            "%.6f" % r["spur"], "%.6f" % r["E_dt"],
                            "%.6f" % r["E_tot"], r["false_on"]])
    P("  wrote results/voff_sweep.csv and voff_sweep.txt")


if __name__ == "__main__":
    main()
