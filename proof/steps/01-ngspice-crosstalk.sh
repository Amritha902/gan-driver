#!/bin/zsh
# STEP 1 -- the fault, and the fix. Run in ngspice, live, right now.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 1  The crosstalk fault, simulated live in ngspice%f"
print -P "%F{cyan}================================================================%f"
echo "machine : $(hostname)   $(date '+%Y-%m-%d %H:%M:%S')"
echo "spice   : $(ngspice -b -o /dev/null /dev/null 2>&1 | grep -o 'ngspice-[0-9]*' | head -1)"
echo "circuit : sim/dpt.cir    device model: models/egan.lib"
echo
echo "Running TWO simulations of the same half-bridge:"
echo "  (a) fastest drive, NO Miller clamp, 0 V off-bias"
echo "  (b) same circuit, Miller clamp ON, -2 V off-bias"
echo
python3 - <<'PY'
import sys, time; sys.path.insert(0, 'scripts')
import gansim
t0 = time.time()
a = gansim.run(CLKEN=0, VNEG=0)
b = gansim.run(CLKEN=1, VNEG=-2)
print("  threshold of this GaN device (V_th)      : 1.400 V")
print()
print("  (a) no clamp, 0 V   -> gate of OFF device : %+.4f V" % a['Vgs_spur'])
print("      margin to threshold                  : %+.4f V   false_turn_on = %d"
      % (a['margin'], a['false_on']))
print()
print("  (b) clamp on, -2 V  -> gate of OFF device : %+.4f V" % b['Vgs_spur'])
print("      margin to threshold                  : %+.4f V   false_turn_on = %d"
      % (b['margin'], b['false_on']))
print()
print("  SLIDE SAYS : 1.65 V on the OFF gate, 2.58 V margin.")
print("  THIS RUN   : %.2f V on the OFF gate, %.2f V margin." % (a['Vgs_spur'], b['margin']))
print("  ngspice wall time for both runs: %.1f s" % (time.time()-t0))
PY
