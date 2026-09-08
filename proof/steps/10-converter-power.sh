#!/bin/zsh
# STEP 10 -- the converter itself: power in, power out.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 10  The converter running: 100 V DC in, 48.6 V DC out%f"
print -P "%F{cyan}================================================================%f"
echo "circuit : sim/buck.cir   GaN synchronous buck, 500 kHz, 10 ohm load"
echo "This is the machine. Everything else in the project is about the two"
echo "transistors inside it and how they are switched."
echo
python3 - <<'PY'
import sys, time; sys.path.insert(0, 'scripts')
import bucksim
t0 = time.time()
print("  running ngspice ...")
r = bucksim.run()
print("  done in %.1f s\n" % (time.time() - t0))
print("            %-14s %-14s" % ("IN", "OUT"))
print("  %-9s %-14s %-14s" % ("voltage", "%.1f V" % r["Vin"],  "%.2f V" % r["Vout"]))
print("  %-9s %-14s %-14s" % ("current", "%.3f A" % r["Iin"],  "%.3f A" % r["Iout"]))
print("  %-9s %-14s %-14s" % ("power",   "%.2f W" % r["Pin"],  "%.2f W" % r["Pout"]))
print()
print("  efficiency        %.2f %%" % r["eff"])
print("  power lost        %.2f W   (transistors + power loop)" % r["loss"])
print("  output ripple     %.0f mV" % r["ripple_mV"])
print()
print("  SLIDE SAYS : 100 V in, 48.6 V out, 236.9 W, 97.6 %")
print("  THIS RUN   : %.0f V in, %.1f V out, %.1f W, %.1f %%"
      % (r["Vin"], r["Vout"], r["Pout"], r["eff"]))
PY
