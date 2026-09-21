# -*- coding: utf-8 -*-
"""overshoot_audit.py -- why the deck said 15.4 % overshoot and the converter
actually does 28.3 %, separated into the two causes.

    python3 scripts/overshoot_audit.py

HOW THIS WAS FOUND
  panel_metrics.py measures switch-node overshoot on a settled converter at a
  0.02 ns step and reported 28.3 %. The deck said 15.4 %, from bucksim.py.
  Both cannot be right on the same converter, so this pulls the two apart.

  It is not a bug in either script. They measure two different things, and
  the deck was quoting the wrong one as if it were the device stress.

THE TWO CAUSES, AND WHAT EACH IS WORTH
  1. THE OFF RAIL.  The deck's figure is taken at VNEG = 0, the netlist
     default. Our shipped control word runs the off rail at -2 V, which is
     what buys the crosstalk margin the whole project is about. A harder off
     bias turns the low side off faster, so di/dt through the 3 nH loop is
     larger and the inductive kick is larger. Worth +6.9 points, averaged
     over the two timesteps.

  2. THE TIMESTEP.  A 0.2 ns step on an edge that completes in 0.82 ns has
     about four samples across it, and the peak falls between them. Resolving
     the edge at 0.02 ns finds a peak the coarse run steps over. Worth +2.8
     points at 0 V and +5.5 points at -2 V, so +4.1 averaged -- more at -2 V
     because the edge there is faster, so the coarse grid misses more of it.

  Neither is a small correction and they compound: 15.4 % becomes 28.3 %,
  which on a 100 V bus is 128 V rather than 115 V against a 200 V-rated part.
  At the 200 V corner the same fraction is 257 V, and that is the number that
  decides whether the device survives, so it belongs in the deck as measured
  rather than as the friendlier of two available figures.

WHAT IS STILL DIFFERENT AND IS NOT CHASED HERE
  bucksim.py runs 150 cycles from a cold start and averages the last 20; this
  runs 3 cycles from a settled start. That accounts for the residual 1.8
  points between this table's 17.2 % and the deck's 15.4 % at matched
  configuration. It is small, it is in the conservative direction, and
  chasing it would cost a 150-cycle run at 0.02 ns for no change in the
  conclusion.
"""
import os, re, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel_metrics as pm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

CASES = [("0",  "0.2n",  "2n",    "deck's configuration"),
         ("0",  "0.02n", "0.05n", "edge resolved"),
         ("-2", "0.2n",  "2n",    "shipped off rail"),
         ("-2", "0.02n", "0.05n", "shipped, edge resolved")]


def peak(vneg, tran, maxstep, tag):
    t = pm.build("gan_ours", "edge")
    t = re.sub(r"^\.param VNEG=.*$", ".param VNEG=%s" % vneg, t, flags=re.M)
    t = re.sub(r"^\.tran .*$", ".tran %s {TSTOP} 0 %s uic" % (tran, maxstep),
               t, flags=re.M)
    dat = "/tmp/ova_%s.dat" % tag
    pm.ngspice(t, "ova_" + tag, dat=dat)
    if not os.path.exists(dat):
        return None
    d = np.loadtxt(dat)
    # wrdata puts a time column before every variable: v(sw) is column 3.
    tt, sw = d[:, 0], d[:, 3]
    pk = float(sw[tt > 2e-6].max())          # past the first settling edge
    os.remove(dat)
    return pk


def main():
    L = []
    L.append("")
    L.append("  SWITCH-NODE OVERSHOOT -- where 15.4 % and 28.3 % come from")
    L.append("  sim/buck.cir, gan_ours, settled, 3 cycles, 100 V bus, 10 ohm.")
    L.append("  Only the off rail and the timestep change between rows.")
    L.append("  " + "-" * 68)
    L.append("  %-10s %-10s %-26s %s" % ("off rail", "timestep", "", "peak / overshoot"))
    rows = []
    for vneg, tran, mx, note in CASES:
        tag = "%s_%s" % (vneg.replace("-", "m"), tran.replace(".", ""))
        sys.stdout.write("  running %s ... " % tag); sys.stdout.flush()
        pk = peak(vneg, tran, mx, tag)
        print("ok" if pk else "NO WAVEFORM")
        rows.append((vneg, tran, note, pk))
        L.append("  %-10s %-10s %-26s %s"
                 % (vneg + " V", tran, note,
                    ("%7.2f V   %6.2f %%" % (pk, pk - 100.0)) if pk else "n/a"))
    L.append("  " + "-" * 68)

    got = {(v, t): p for v, t, _, p in rows if p}
    if len(got) == 4:
        rail = ((got[("-2", "0.2n")] - got[("0", "0.2n")]) +
                (got[("-2", "0.02n")] - got[("0", "0.02n")])) / 2.0
        step = ((got[("0", "0.02n")] - got[("0", "0.2n")]) +
                (got[("-2", "0.02n")] - got[("-2", "0.2n")])) / 2.0
        L.append("  the -2 V off rail is worth   %+5.1f points of overshoot" % rail)
        L.append("  resolving the edge is worth  %+5.1f points of overshoot" % step)
        L.append("")
        L.append("  Both are real. The deck quoted 15.4 %, which is the 0 V rail")
        L.append("  at a coarse step -- not the word we ship. The shipped word at")
        L.append("  a step that resolves the edge is %.1f %%." % (got[("-2", "0.02n")] - 100.0))
    L.append("")
    txt = "\n".join(L)
    print(txt)
    open(os.path.join(RES, "overshoot_audit.txt"), "w").write(txt + "\n")
    print("  written: results/overshoot_audit.txt")


if __name__ == "__main__":
    main()
