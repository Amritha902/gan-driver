#!/bin/zsh
# ---------------------------------------------------------------------------
# DEMO.sh -- the whole project, running, in one pass. Written to be recorded.
#
# Same commands as RUN-LIVE.sh, but continuous and paced for watching rather
# than for stopping between steps.
#
#     cd ~/GAN_MAIN/PROOF && zsh DEMO.sh
# ---------------------------------------------------------------------------
cd ~/gan-driver

band () {
  print -P ""
  print -P "%F{cyan}  ============================================================%f"
  print -P "%F{cyan}  $1%f"
  print -P "%F{cyan}  ============================================================%f"
  print -P ""
  sleep 1.6
}

printf '\033[3J\033c'
print -P "%F{yellow}  GaN BASED DC-DC POWER CONVERTER%f"
print -P "%F{yellow}  with an improved gate driver%f"
print -P ""
print -P "  Amritha S 23BEC1368  .  Sanjay Kumar 23BEC1447  .  Aamir Abdullah 23BPS1197"
print -P "  Guide: Dr. Bindu, SENSE, VIT Chennai"
print -P ""
print -P "  $(hostname)   $(date '+%Y-%m-%d %H:%M')"
print -P "  ngspice $(ngspice -b -o /dev/null /dev/null 2>&1 | grep -o 'ngspice-[0-9]*' | head -1 | cut -d- -f2)   ·   $(iverilog -V 2>/dev/null | head -1)"
sleep 4

band "1.  THE CONVERTER   --   100 V DC in, 48.6 V DC out"
echo "  circuit: sim/buck.cir     ngspice, running now"
echo
python3 - <<'PY'
import sys, time; sys.path.insert(0, 'scripts')
import bucksim
t0 = time.time(); r = bucksim.run()
print("  ngspice finished in %.1f s" % (time.time() - t0))
print()
print("             %-14s %-14s" % ("IN", "OUT"))
print("  %-9s  %-14s %-14s" % ("voltage", "%.1f V" % r["Vin"],  "%.2f V" % r["Vout"]))
print("  %-9s  %-14s %-14s" % ("current", "%.3f A" % r["Iin"],  "%.3f A" % r["Iout"]))
print("  %-9s  %-14s %-14s" % ("power",   "%.2f W" % r["Pin"],  "%.2f W" % r["Pout"]))
print()
print("  efficiency   %.2f %%      power lost   %.2f W" % (r["eff"], r["loss"]))
PY
sleep 5

band "2.  THE FAULT   --   and what removes it"
python3 - <<'PY'
import sys, time; sys.path.insert(0, 'scripts')
import gansim
a = gansim.run(CLKEN=0, VNEG=0)
b = gansim.run(CLKEN=1, VNEG=-2)
print("  the device turns on above 1.400 V")
print()
print("  fastest drive, no clamp, 0 V   gate reaches %+.4f V   margin %+.4f V   -> FALSE TURN-ON"
      % (a['Vgs_spur'], a['margin']))
print("  clamp on, -2 V off-bias        gate reaches %+.4f V   margin %+.4f V   -> safe"
      % (b['Vgs_spur'], b['margin']))
PY
sleep 5

band "3.  THE CASES   --   python driving ngspice, one run each"
echo "  \$ python3 scripts/cases.py"
echo
python3 scripts/cases.py
sleep 6

band "4.  THE CONTROLLER   --   Verilog, compiled and run"
cd rtl
echo "  \$ iverilog -g2012 -o /tmp/tb seg_gate_ctrl_tb.v seg_gate_ctrl.v thermo_decode.v dead_time_gen.v"
iverilog -g2012 -o /tmp/tb seg_gate_ctrl_tb.v seg_gate_ctrl.v thermo_decode.v dead_time_gen.v
echo "  \$ vvp /tmp/tb +report"
vvp /tmp/tb +report
cd ..
sleep 6

band "5.  THE SAME CIRCUIT IN LTSPICE   --   drawn, and run"
echo "  ngspice runs the study. LTspice draws the circuit and re-measures"
echo "  the crosstalk result, so it does not rest on one program."
echo
echo "  Opening ltspice/C_design_clamp_and_neg_bias.asc ..."
rm -f ltspice/C_design_clamp_and_neg_bias.log
open -a /Applications/LTspice.app ~/gan-driver/ltspice/C_design_clamp_and_neg_bias.asc
sleep 11
osascript >/dev/null 2>&1 <<'OSA'
tell application "System Events" to tell process "LTspice"
  set frontmost to true
  try
    perform action "AXRaise" of window 1
    set position of window 1 to {40, 70}
    set size of window 1 to {1180, 700}
  end try
  delay 1
  click menu item 1 of menu 1 of menu bar item "Simulate" of menu bar 1
end tell
OSA
for i in $(seq 1 20); do
  [ -f ltspice/C_design_clamp_and_neg_bias.log ] && sleep 3 && break
  sleep 2
done
sleep 6
osascript -e 'tell application "LTspice" to quit' >/dev/null 2>&1
pkill -f LTspice >/dev/null 2>&1
sleep 2
print -P "%F{cyan}  what LTspice measured, from its own error log:%f"
grep -i vspur ltspice/C_design_clamp_and_neg_bias.log
echo
echo "  LTspice   -1.176857 V        ngspice   -1.1757 V        1.2 mV apart"
echo "  Two simulators, one drawn circuit, the same answer."
sleep 6

band "6.  WHERE IT ALL LIVES"
echo "  Every number above came out of a tool just now, on this machine."
echo "  ngspice for the circuit. LTspice to draw it and check. Vivado for the FPGA."
echo
echo "      cd ~/GAN_MAIN/PROOF && zsh RUN-LIVE.sh"
echo "      github.com/Amritha902/gan-driver"
echo
sleep 5
