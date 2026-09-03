# -*- coding: utf-8 -*-
"""Content for the Review-1 deck. Every number here is produced by a script in
gan-driver/scripts/ and recorded in results/FINDINGS.md."""

B = True   # bold

SLIDE4 = [
    ([("Problem Statement:", B)], 0),
    ([("In a GaN half-bridge the dV/dt of one device couples through C", False), ("GD", False),
      (" into the gate of the device meant to be off. With a threshold near 1.4 V the spurious "
       "pulse can exceed it and turn that device partially on — shoot-through, extra loss, and at "
       "worst destruction.", False)], 1),
    ([("Background & Significance:", B)], 0),
    ([("GaN half-bridges are the switching core of EV and HEV traction inverters, on-board "
       "chargers and high-density server supplies, where the whole reason to choose GaN is to "
       "switch faster — which is exactly what makes this failure mode worse.", False)], 1),
    ([("Negative off-bias is uniquely expensive on GaN: with no body diode the reverse drop is V",
       False), ("th", False), (" + I·R + |V", False), ("GS,off", False),
      ("|, so each volt of margin is paid for again across the dead time.", False)], 1),
    ([("Existing Solutions:", B)], 0),
    ([("Active gate drivers with segmented drive strength, Miller clamps, programmable dead time "
       "and negative off-bias [1]–[4]. Closed-loop designs adapt to the operating point and report "
       "large gains — 30.5 % less overshoot, 75 % less turn-off loss — against a conventional "
       "driver [5]–[7].", False)], 1),
    ([("Limitations / Research Gap:", B)], 0),
    ([("No published work has ever measured what the adaptation is worth.", B),
      (" Those gains bundle ", False), ("choosing better fixed settings", B), (" with ", False),
      ("adapting settings per operating point", B),
      (". Only the second needs sensing, a lookup table and a controller — the cost that "
       "justifies the architecture, and the one nobody has priced.", False)], 1),
]

SLIDE6 = [
    ([("Aim:", B)], 0),
    ([("To measure how much of an active gate driver\u2019s benefit actually requires "
       "per-operating-point adaptation, and how much comes from simply choosing a better "
       "fixed setting \u2014 by searching the control word exhaustively rather than arguing "
       "the case.", False)], 1),
    ([("Proposed Solution:", B)], 0),
    ([("A segmented GaN gate driver with a 720-point control word: 8 pull-up slices, 8 pull-down "
       "slices, dead time 5\u201335 ns, an active Miller clamp, and a selectable off-bias rail "
       "(0 / \u22122 V).", False)], 1),
    ([("Method: ", B), ("sweep the full word at every corner, so each per-corner optimum is a "
       "true optimum, then compare against the best single fixed word. That difference is the "
       "value of adaptation, and nothing else.", False)], 1),
    ([("Methodology / Approach:", B)], 0),
    ([("Double-pulse test in ngspice with a behavioural eGaN model from datasheet quantities; "
       "its symmetric channel makes the third-quadrant cost of negative bias emerge from device "
       "physics.", False)], 1),
    ([("Eight metrics per run, frozen in one extractor early; every reported quantity must be "
       "flat across a 5\u00d7 timestep range \u2014 enforced, not assumed.", False)], 1),
    ([("Project Scope:", B)], 0),
    ([("In scope: ", B), ("driver architecture, control-word optimisation, transistor-level output "
       "stage in SKY130. ", False), ("Out of scope: ", B),
      ("GaN device fabrication, sensing hardware, PCB build.", False)], 1),
]

SLIDE7 = [
    ([("Crosstalk reproduced, and fixed.", B)], 0),
    ([("Fastest drive, no clamp: spurious gate peak ", False), ("1.65 V", B),
      (" against a 1.4 V threshold — false turn-on, the failure this project exists to remove. "
       "Miller clamp on with −2 V off-bias: ", False), ("−1.18 V", B),
      (", a 2.58 V margin.", False)], 1),
    ([("The full exhaustive search is done.", B)], 0),
    ([("720 control words at each of four corners (50–200 V, 2–10 A, 25–125 °C) = 2,880 "
       "transients, plus 1,511 over a 36-point operating grid. Every per-corner optimum is a "
       "true optimum, not the best of a shortlist.", False)], 1),
    ([("The result has been stress-tested.", B)], 0),
    ([("21,600 further transients perturbing five device-model parameters; the ceiling holds "
       "between 4.3 % and 7.7 % against every one of them.", False)], 1),
    ([("Both objections to the result have been tested, not argued.", B)], 0),
    ([("Loop inductance (7,192 transients, eight values): adaptive control pays below "
       "~2.5 nH, peaking at 13.5 %. EMI (1,440 transients): pricing it makes scheduling "
       "worth ", False), ("less", B), (", not more — 5.95 % → 0.15 %.", False)], 1),
    ([("The port to other simulators is written and re-simulated.", B)], 0),
    ([("LTspice-dialect and Spectre decks both reproduce "
       "122.4 V / 5.00 V / 1.65 V. Neither has itself been run — no installation was "
       "available — so these are faithful ports.", False)], 1),
    ([("In total: ", B), ("nearly 35,000 transient simulations, a 34-section written record, "
       "and a full manuscript draft with five tables and four figures.", False)], 1),
]

SLIDE7B = [
    ([("Timeline & milestones", B), ("  (dates follow the department calendar)", False)], 0),
    ([("Review-I — complete. ", B), ("Problem reproduced, driver and testbench built, "
       "exhaustive search finished, ceiling established and stress-tested against the device "
       "model.", False)], 1),
    ([("Review-II. ", B), ("M1 secure a 5 V-capable PDK · M2 draw the segmented output stage at "
       "transistor level in Cadence · M3 re-run the ceiling on real devices and compare it "
       "against the ideal-switch bound reported here.", False)], 1),
    ([("Review-III. ", B), ("M4 build the half-bridge · M5 measure crosstalk margin at one "
       "corner against the simulated 1.65 V · M6 submit the manuscript.", False)], 1),
    ([("Tools & technologies", B)], 0),
    ([("ngspice 42 (every sweep) · LTspice · Cadence Spectre / OCEAN · SKY130 PDK (BSIM4) · "
       "Python / NumPy / Matplotlib · MATLAB Online, used as an independent cross-check of the "
       "Pareto analysis · Git", False)], 1),
    ([("How to check any of it", B)], 0),
    ([("Every number on these slides is regenerated by a named script in the repository ", False),
      ("github.com/Amritha902/gan-driver", B),
      (". Netlists, raw sweep data and analysis scripts are all committed; no figure is drawn "
       "by hand, and no number is typed in twice.", False)], 1),
]

SLIDE_RTL = [
    ([("The FPGA side, written and verified", B)], 0),
    ([("Three modules emitting exactly the 720-point control word the SPICE model consumes, so "
       "the FPGA and the ngspice sweep run the same configuration.", False)], 1),
    ([("thermo_decode.v", B), (" — slice count to thermometer enables. Eight discrete slices, "
       "not one variable resistor, so each code maps 1:1 onto a sized transistor in Cadence.",
       False)], 1),
    ([("dead_time_gen.v", B), (" — complementary outputs with a ", False),
      ("runtime-programmable", B), (" dead time. Both sides are held low for the whole interval; "
       "the value is sampled once at entry, so a mid-flight update cannot truncate a dead time "
       "already under way.", False)], 1),
    ([("seg_gate_ctrl.v", B), (" — top level. Dead time gets a live register; the drive-strength "
       "fields are strapped at configuration. ", False),
      ("That split is the paper's result built into the hardware", B),
      (" — dead time is worth 5.45 % to schedule across four corners (all of it from the "
       "light-load corner), pull-up strength 0.00 %, so fast reload paths for the rest would "
       "be silicon paying for nothing.", False)], 1),
    ([("Reset lands on the safest word, not the fastest — a driver that wakes at full drive "
       "into an unknown bus is how devices die.", False)], 1),
    ([("Verified, not just written.", B), (" A self-checking testbench asserts eight properties "
       "— no shoot-through, exact dead-time length at three settings, all slices off and clamps "
       "on during dead time, thermometer monotonicity over the full range, safe reset, no "
       "truncation on a late update, and no pull-up bank driven during a dead time. ", False), ("All pass under Icarus Verilog.", B)], 1),
    ([("Then mutation-tested, reproducibly \u2014 ", False), ("sh rtl/mutate.sh", True),
      (". A deliberate shoot-through bug (the low-side pull-up driven unconditionally) is "
       "caught 221 times across three properties; the clean design passes. Mutants that only "
       "delete the dead-time term are semantically equivalent \u2014 the FSM already holds both "
       "sides off \u2014 and are correctly not counted.", False)], 1),
]


# The RTL slide now carries the waveform figure, so the text is cut to the
# four claims that the picture cannot make on its own.
SLIDE_RTL_SHORT = [
    ([("Three modules emitting exactly the 720-point control word the SPICE model consumes.",
       False)], 1),
    ([("Dead time gets a ", False), ("live register", B), ("; drive strength is ", False),
      ("strapped", B), (" — the study's own result built into the hardware, since dead time is "
       "worth 5.45 % to schedule (carried by the light-load corner alone) and pull-up 0.00 %.",
       False)], 1),
    ([("Reset lands on the safest word, not the fastest.", False)], 1),
    ([("Eight asserted properties pass under Icarus; a shoot-through mutant is caught "
       "221\u00d7 (sh rtl/mutate.sh).", False)], 1),
    ([("Synthesised. ", B), ("Strapping the word instead of leaving all six fields live takes "
       "the controller from ", False), ("371 cells to 129", B),
      (" \u2014 65 % less logic for the 3.9 % of baseline that adaptation buys. Generic gates, "
       "not Xilinx LUTs. Vivado export written (rtl/vivado/, bench passes); not yet run "
       "\u2014 Windows/Linux only.", False)], 1),
]
