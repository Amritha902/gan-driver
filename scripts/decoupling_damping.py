# -*- coding: utf-8 -*-
"""decoupling_damping.py -- why sim/buck.cir and sim/dpt.cir disagreed at
200 V, and the one-component change that reconciles them.

    python3 scripts/decoupling_damping.py

THE DISAGREEMENT
  dpt.cir at 200 V: switch node peaks at 207 V, low-side gate sits at
  -1.97 V, margin +3.2 V. Clean.
  buck.cir at 200 V: switch node rings to 464 V, low-side gate reaches
  +11.78 V against a 1.4 V threshold, 112 A through a 10 A load.

  Same devices, same driver, same control word. Both cannot be right.

WHAT IT WAS -- NOT THE DEVICES, NOT THE DRIVER
  Morphing buck.cir toward dpt.cir one element at a time: changing LOUT from
  22 uH to dpt's 100 uH does nothing (451 V). Doubling the dead time does
  nothing (462 V). Removing the bus decoupling network drops it to 259 V and
  the gate to its rail.

  The decoupling branch -- Ldec 0.5 nH, Cdec 100 nF, Rdec 20 mOhm from the
  bus to ground -- is a series L-C with Q about 3.5 near 22 MHz. The
  switching edges pump it once a cycle. At 100 V the ringing is survivable.
  At 200 V it crosses the threshold that turns the low side on, and then the
  464 V is the inductive kick of the shoot-through collapsing.

  dpt.cir has no decoupling network at all, which is exactly why the
  double-pulse deck showed none of this.

  That network was added to this project to fix a 168 V overshoot at 100 V.
  It did fix that. It was never checked at the top of the bus range, and it
  was never damped.

THE FIX, AND WHAT IT COSTS
  Rdec 20 mOhm -> 1 ohm. Nothing else changes.

                        100 V bus              200 V bus
    peak v(sw)          128.3 -> 118.0 V       464.2 -> 208.2 V
    LS gate, HS on      -0.27 -> -0.97 V       +11.78 -> -0.74 V
    margin to vth       +1.67 -> +2.37 V       false turn-on -> +2.14 V
    efficiency          97.39 -> 97.42 %
    device dissipation  2.800 -> 2.598 W

  It costs nothing. It is better on every measured axis at both bus
  voltages, and at 200 V it brings buck.cir to 208.2 V against dpt.cir's
  207.3 V -- the two decks agree to within a volt.

WHY 1 OHM AND NOT LESS
  Sweeping Rdec at 200 V: 20m gives 464 V, 100m gives 272 V, 300m gives
  235 V, 1 ohm gives 208 V. Q falls below 1 somewhere above 100 mOhm and the
  branch stops ringing. 1 ohm is overdamped rather than critically damped,
  which is the right side to err on for a network whose only job is to keep
  the bus stiff.
"""
import sys, os, re
sys.path.insert(0, "/home/user/amritha902/gan-driver/scripts")
import numpy as np, panel_metrics as pm

def gate_while_hs_on(vin, rdec):
    t = pm.build("gan_ours", "edge")
    t = re.sub(r"^\.param VIN\s*=.*$", ".param VIN=%d" % vin, t, flags=re.M)
    t = re.sub(r"^\.param RDEC\s*=.*$", ".param RDEC=%s" % rdec, t, flags=re.M)
    t = t.replace("wrdata EDGEOUT v(pwmhs) v(sw)",
                  "wrdata EDGEOUT v(pwmhs) v(sw) v(lsg)")
    tag = "cf_%d_%s" % (vin, str(rdec).replace(".", ""))
    dat = "/tmp/%s.dat" % tag
    pm.ngspice(t, tag, dat=dat)
    if not os.path.exists(dat): return None
    d = np.loadtxt(dat); m = d[:,0] > 2e-6
    sw, lsg = d[m,3], d[m,5]
    on = sw > 0.5*vin                      # high side conducting
    r = (float(sw.max()), float(lsg[on].max()) if on.any() else float("nan"))
    os.remove(dat); return r

print("LS gate measured ONLY while the high side is on. vth = 1.4 V.")
print("%-8s %-10s %-12s %-14s %s" % ("VIN","Rdec","peak v(sw)","LS gate (HS on)","verdict"))
for vin in (100, 200):
    for rdec in ("20m", "1"):
        r = gate_while_hs_on(vin, rdec)
        if r is None: print("%-8s %-10s NO WAVEFORM" % (vin, rdec)); continue
        pk, lg = r
        print("%-8s %-10s %-12s %-14s %s"
              % ("%dV"%vin, rdec, "%.1f V"%pk, "%.2f V"%lg,
                 "FALSE TURN-ON" if lg > 1.4 else "margin %+.2f V" % (1.4-lg)))

print("\nwhat the damping costs -- power run at 100 V:")
for rdec in ("20m", "1"):
    t = pm.build("gan_ours", "power")
    t = re.sub(r"^\.param RDEC\s*=.*$", ".param RDEC=%s" % rdec, t, flags=re.M)
    out = pm.ngspice(t, "cfp_" + rdec)
    g = pm.grab(out, ["p_in","p_out","p_hs","p_ls"])
    if g["p_in"]:
        print("  Rdec %-5s eff %.2f %%   P_device %.3f W"
              % (rdec, g["p_out"]/g["p_in"]*100, (g["p_hs"] or 0)+(g["p_ls"] or 0)))
    else:
        print("  Rdec %-5s NO MEASUREMENT" % rdec)
