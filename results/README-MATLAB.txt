RUNNING THIS IN MATLAB ONLINE
=============================

1. Go to the Files pane (left side) in MATLAB Online.
2. Drag BOTH of these in:
       gan_analysis.m
       sweep_matlab.csv
3. In the Command Window, type:
       gan_analysis
   and press Enter.

No toolboxes needed -- core MATLAB only, so a basic MATLAB Online licence
is enough. Takes a couple of seconds.

WHAT IT PRINTS

  Part 1  Pareto analysis of the 720-point sweep
            504 of 720 words feasible, 7-point Pareto front,
            0.0390 uJ of loss per point of overshoot removed
  Part 2  Schedule LUT: the best control word under a stated cost function
  Part 3  Analytical crosstalk model checked against the SPICE result

WHAT IT SAVES
       pareto_matlab.png
       crosstalk_model_matlab.png
   Both go straight into the report.

WHY THIS IS WORTH DOING IN MATLAB
   It is an INDEPENDENT re-analysis. The same numbers were computed in
   Python from the same CSV; if MATLAB disagrees, one of them is wrong.
   It already earned its keep once: the MATLAB pass exposed that the
   "51 mV of margin per ns of dead time" figure was a straight line forced
   through a saturating curve. The real behaviour is that nearly all the
   benefit arrives between 5 and 10 ns and there is none past ~15 ns.

WHAT MATLAB IS *NOT* DOING HERE
   It is not running the circuit simulation. MATLAB cannot read SPICE
   netlists. The simulation is ngspice (or LTspice, or the browser page);
   MATLAB analyses its output. Do not let anyone believe otherwise in the
   viva -- say "simulated in SPICE, analysed in MATLAB".

TESTED
   This script was run in GNU Octave before being sent, which catches
   syntax and logic errors. Octave is not identical to MATLAB; if anything
   errors, paste the message back and I will fix it.
