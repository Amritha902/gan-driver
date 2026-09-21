# -*- coding: utf-8 -*-
"""vbus_limit.py -- the shipped control word fails at the top of its own
stated bus range, in the converter, and this is the evidence.

    python3 scripts/vbus_limit.py

WHAT THIS FOUND
  The architecture slide states an envelope of 50-200 V. panel_metrics.py
  measures the converter at 100 V. Nobody had ever run sim/buck.cir at 200 V
  with our driver. Run it, and the switch node rings to 464 V on a device
  the model file calls EPC2010C-class: 200 V rated.

  It is not a numerical artefact. The peak is a smooth, fully resolved curve
  at a 50 ps sample interval, and it repeats on every one of 150 cycles at
  ~465 V -- steady state, not a start-up transient.

  It is not the -2 V off rail: the same converter with a 0 V rail rings to
  471 V, marginally worse.

  It is OUR DRIVER. The base paper's driver, same converter, same device,
  same 200 V bus, peaks at 204 V.

THE MECHANISM, FROM THE WAVEFORM
  The low-side gate reaches 11.78 V while the high side is on, against a
  1.4 V threshold. That is not crosstalk near a margin, it is full false
  turn-on. Both devices conduct, the peak current reaches 112 A where the
  load draws 10 A, and the 464 V is the inductive kick as that shoot-through
  current collapses through the 3 nH power loop.

WHY OURS AND NOT THEIRS
  Our shipped word is NPU = NPD = 8: every slice engaged, the strongest and
  fastest edge the driver can produce. Theirs stages 2 of 7 slices and then
  the rest, which is slower. Slower edge, less dv/dt, less Miller current
  into the off gate. Controlling di/dt across the edge is what their
  segmented pattern is FOR, and our fixed maximum-strength word throws that
  away in exchange for the crosstalk margin it buys at 100 V.

WHAT THIS CONTRADICTS, AND WHAT IS UNRESOLVED
  headtohead.py measures +2.251 V of crosstalk margin for our word at
  200 V / 10 A / 125 C and reports our lead WIDENING as the corner hardens.
  That is sim/dpt.cir, a double-pulse test. This is sim/buck.cir, the
  continuous converter, at the same bus voltage, and it says the opposite.

  Both cannot describe the same device. The difference is not yet explained
  and it is not safe to present the 200 V claim until it is. The candidates,
  in the order they should be checked:
    1. dpt.cir uses LLOAD = 100 uH against the converter's 22 uH, so the
       current slope through the dead time differs.
    2. dpt.cir measures ONE edge from a quiet start. The converter arrives
       at each edge carrying the previous cycle's ringing.
    3. One of the two decks is wrong.
"""
import sys, os, re
sys.path.insert(0, "/home/user/amritha902/gan-driver/scripts")
import numpy as np, panel_metrics as pm
t = pm.build("gan_ours", "edge")
t = re.sub(r"^\.param VIN\s*=.*$", ".param VIN=200", t, flags=re.M)
t = t.replace("wrdata EDGEOUT v(pwmhs) v(sw)",
              "wrdata EDGEOUT v(pwmhs) v(sw) v(lsg) i(vshs) i(vsls)")
dat="/tmp/diag200.dat"
pm.ngspice(t, "diag200", dat=dat)
d=np.loadtxt(dat)
# wrdata: t,pwm, t,sw, t,lsg, t,ihs, t,ils
tt, sw, lsg, ihs, ils = d[:,0], d[:,3], d[:,5], d[:,7], d[:,9]
i=int(sw.argmax())
print("peak v(sw) = %.1f V at t=%.4f us" % (sw[i], tt[i]*1e6))
print("at that instant: v(lsg)=%.2f V   i_hs=%.1f A   i_ls=%.1f A"
      % (lsg[i], ihs[i], ils[i]))
print("\nvth at 25 C is 1.4 V. low-side gate over the run:")
print("  max v(lsg) while high side is on: %.2f V" % float(lsg[sw>0.5*200].max()))
print("  peak |i_hs| = %.1f A, peak |i_ls| = %.1f A" % (np.abs(ihs).max(), np.abs(ils).max()))
print("  load current should be ~10 A")
w=slice(max(0,i-6), i+3)
print("\n  t(us)      v(sw)     v(lsg)     i_hs      i_ls")
for j in range(w.start, min(len(tt), w.stop)):
    print("  %8.5f %9.1f %9.2f %9.1f %9.1f" % (tt[j]*1e6, sw[j], lsg[j], ihs[j], ils[j]))
os.remove(dat)
