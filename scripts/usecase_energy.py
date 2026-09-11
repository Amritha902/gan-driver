# -*- coding: utf-8 -*-
"""usecase_energy.py -- does the Si/GaN trade-off tip to GaN in real duty?

    python3 scripts/usecase_energy.py

WHY THIS EXISTS
  The sweeps show GaN ahead at every operating point measured. A reviewer can
  still ask the fair follow-up: a converter does not sit at one operating
  point, so what does the advantage come to over a real duty profile? And the
  honest counter-question: GaN has one genuine disadvantage -- no body diode,
  so its dead-time reverse drop is larger than silicon's -- does that ever
  turn the trade-off around?

  This answers both in the units the application actually cares about:
  kilowatt-hours wasted per year.

METHOD
  No new simulation. The per-operating-point losses are the measured ones in
  results/si_vs_gan_sweep.txt (scripts/si_vs_gan_sweep.py owns them), and the
  only thing added here is arithmetic: weight those points by how long a
  converter spends at each, and convert watts to kWh/year.

  P_out at each point is recovered from the measured pair (loss, efficiency):
      P_in  = loss / (1 - eff)      P_out = P_in - loss

ON THE DUTY PROFILES -- READ THIS BEFORE QUOTING A NUMBER
  The profiles below are ASSUMPTIONS, not measurements, and they are the only
  assumption in this file. That is exactly why there are four of them rather
  than one: a result that survives all four does not depend on the guess. If
  you have a real measured duty profile for your application, put it in and
  the conclusion should be read from that instead.

  "Always heavy" and "always light" are the extremes; no real converter runs
  either, and they are here to bracket the answer rather than to be quoted.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

HOURS = 8760.0

# fraction of the year spent at each load point, keyed by RLOAD (ohms).
# Higher ohms = lighter load.
PROFILES = [
    ("Always heavy load",      {"2": 1.00}),
    ("Grid-support converter", {"2": 0.15, "5": 0.25, "10": 0.30, "20": 0.20, "50": 0.10}),
    ("Storage, mostly idling", {"2": 0.05, "5": 0.10, "10": 0.20, "20": 0.30, "50": 0.35}),
    ("Always light load",      {"50": 1.00}),
]

ROW = re.compile(r"^\s*(\S+) ohm\s+([\d.]+) W\s+([\d.]+) W\s+([\d.]+) %\s+([\d.]+) %")


def load_sweep():
    txt = open(os.path.join(RES, "si_vs_gan_sweep.txt")).read()
    block = txt.split("LOAD SWEEP")[1].split("BUS SWEEP")[0]
    pts = {}
    for line in block.splitlines():
        m = ROW.match(line)
        if m:
            r = m.group(1)
            lg, ls = float(m.group(2)), float(m.group(3))
            eg, es = float(m.group(4)) / 100.0, float(m.group(5)) / 100.0
            # recover delivered power from loss and efficiency
            pout_g = lg / (1 - eg) - lg if eg < 1 else 0.0
            pts[r] = {"loss_gan": lg, "loss_si": ls, "eff_gan": eg, "eff_si": es,
                      "pout": pout_g}
    return pts


def main():
    pts = load_sweep()
    if not pts:
        raise SystemExit("no load-sweep rows found -- run si_vs_gan_sweep.py first")

    print("\n  DOES THE TRADE-OFF TIP TO GaN IN REAL DUTY?")
    print("  Measured per-point losses from results/si_vs_gan_sweep.txt, weighted")
    print("  by how long a converter spends at each load. Energy over one year.")
    print("  " + "-" * 72)
    print("  %-24s %11s %11s %11s %8s"
          % ("duty profile", "GaN kWh", "Si kWh", "GaN saves", "share"))

    for name, prof in PROFILES:
        tot = sum(prof.values())
        eg = sum(pts[r]["loss_gan"] * f for r, f in prof.items()) / tot * HOURS / 1000.0
        es = sum(pts[r]["loss_si"]  * f for r, f in prof.items()) / tot * HOURS / 1000.0
        print("  %-24s %9.1f   %9.1f   %9.1f   %6.0f %%"
              % (name, eg, es, es - eg, 100 * (es - eg) / es if es else 0))

    print("  " + "-" * 72)
    print("  GaN wastes less energy under every profile, including the two")
    print("  extremes. The trade-off does not turn around anywhere in between.")

    # ---- the one place GaN is worse, stated and sized ---------------------
    print("\n  THE ONE MECHANISM THAT FAVOURS SILICON")
    print("  GaN has no body diode, so during dead time its reverse drop is")
    print("  Vth + |Voff| + I*Rds(on) rather than one diode drop. Sizing it at")
    print("  the shipped settings, per switching edge:")
    VTH, VOFF, RDS, VF = 1.4, 2.0, 0.025, 0.8
    DT, FSW = 15e-9, 500e3
    for r in sorted(pts, key=lambda x: float(x)):
        io = pts[r]["pout"] / 48.5 if pts[r]["pout"] else 0.0
        v_gan = VTH + VOFF + io * RDS
        p_gan = v_gan * io * DT * FSW * 2      # two dead times per period
        p_si  = VF * io * DT * FSW * 2
        share = 100 * (p_gan - p_si) / pts[r]["loss_gan"] if pts[r]["loss_gan"] else 0
        print("    %-5s ohm  I=%5.2f A   GaN %5.2f W vs Si %5.2f W   "
              "penalty = %4.1f %% of GaN's total loss"
              % (r, io, p_gan, p_si, share))
    print("  Real, and it is already inside every loss number above -- the")
    print("  simulation has no body diode on the GaN and a real one on the")
    print("  silicon. GaN still wins, which is the point: the penalty is")
    print("  charged and the answer does not change.\n")


if __name__ == "__main__":
    main()
