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

BEFORE RUNNING gan_master.m
   Section 8 (loop inductance) reads lloop_sweep.csv, which ships GZIPPED to
   keep the repo small. The script detects this and prints instructions rather
   than failing, but the section is skipped until you run:

       gunzip -k results/lloop_sweep.csv.gz

   gan_analysis.m does not need it.

gan_master.m IS A FUNCTION FILE, NOT A SCRIPT -- AND MUST STAY ONE
   Run it by typing its name at the prompt:

       gan_master

   In MATLAB Online that is all. From the Octave command line use
   `octave --eval gan_master`; plain `octave gan_master.m` only DEFINES it.

   Why a function file. MATLAB requires a script's local functions to appear
   AFTER all executable code ("Function definitions in a script must appear at
   the end of the file"). Octave does not hoist them, so at the end they are
   undefined when the body calls them. Both were verified on 5 Sep 2026:
   functions mid-file fails in MATLAB, functions at the end fails in Octave.
   The two rules cannot both be satisfied by a plain script. In a FUNCTION
   file, subfunctions are visible regardless of order in both tools -- so that
   is what this is. Do not convert it back to a script.

   gan_analysis.m is unaffected: it uses only anonymous functions, which are
   legal anywhere in both.

VERIFIED IN REAL MATLAB -- 5 September 2026
   Both scripts have now been run in MATLAB Online, not just Octave. MATLAB
   and Octave agree EXACTLY -- every printed figure identical to the last
   digit. The full output is in results/matlab_online/RUN-LOG.txt, with
   MATLAB's own figures alongside it.

   Those figures have black backgrounds because MATLAB Online runs a dark
   theme. The deck uses the white-background versions in results/. Do not swap
   them.
