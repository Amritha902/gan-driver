RUNNING THIS IN LTSPICE
=======================

1. Put all three files in the SAME folder:
       dpt.cir      egan.lib     segdrv.lib

2. LTspice -> File -> Open.  Change the file-type dropdown to "All Files"
   (LTspice hides .cir by default).  Open dpt.cir.

3. Press Run (the little running man), or Simulate -> Run.

4. Plot these traces:
       V(sw)      switch node
       V(lsg)     low-side gate
       V(hsg)-V(sw)   high-side gate-source   <- THE ONE THAT MATTERS

WHAT YOU SHOULD SEE  (verified numbers -- if LTspice disagrees, something
is wrong with the port, tell me)

   gate on-state, at t = 0.9 us .............  5.00 V
   peak V(lsd) after turn-off at t = 1 us ...  122.4 V   (bus is 100 V)
   peak V(hsg)-V(sw), 2.015-2.10 us .........  1.65 V

   The threshold is 1.4 V.  1.65 V is ABOVE it: that is the false turn-on
   this whole project exists to fix.

TO FIX IT, edit the PARAM BLOCK near the top of dpt.cir:

   .param CLKEN=1        turns the active Miller clamp on
   .param VNEG=-2        adds negative off-bias

   With CLKEN=1 the peak drops to 0.83 V (margin +0.57 V).
   With CLKEN=1 and VNEG=-2 it drops to -1.18 V (margin +2.58 V).

CHANGING THE DRIVE STRENGTH
   The slice enables are baked in as literal numbers so LTspice has no
   conditionals to evaluate.  To change the control word, re-run:

       python3 scripts/to_ltspice.py --npu 4 --npd 8

   and re-open the regenerated files.

WHAT IS DIFFERENT FROM THE ngspice VERSION
   Nothing electrical.  The converter only: deletes the .control block
   (LTspice has no equivalent), turns ngspice's "$" end-of-line comments
   into ";", and bakes the slice enables to literals.  The conversion was
   checked by running the converted netlist and confirming it reproduces
   122.4 V / 5.00 V / 1.65 V exactly.
