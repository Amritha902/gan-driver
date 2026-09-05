# -*- coding: utf-8 -*-
"""Content for the Review-1 deck. Every number here is produced by a script in
gan-driver/scripts/ and recorded in results/FINDINGS.md."""

B = True   # bold

SLIDE4 = [
    ([("Problem Statement:", B)], 0),
    ([("One device's dV/dt couples through C", False), ("GD", False),
      (" into the gate of the device that is supposed to be OFF. It reaches ", False),
      ("1.65 V against a 1.4 V threshold", B),
      (" \u2014 false turn-on, and a shoot-through path.", False)], 1),
    ([("Background & Significance:", B)], 0),
    ([("GaN half-bridges are the core of EV traction inverters and battery storage "
       "converters. The whole reason to choose GaN is speed \u2014 which is exactly what "
       "makes this failure worse.", False)], 1),
    ([("Existing Solutions:", B)], 0),
    ([("Active gate drivers: segmented drive, Miller clamps, programmable dead time, "
       "negative off-bias [1]\u2013[4]. Closed-loop designs report 30.5 % less overshoot "
       "and 75 % less turn-off loss [5]\u2013[7].", False)], 1),
    ([("Limitations / Research Gap:", B)], 0),
    ([("No published work has measured what the adaptation is worth.", B),
      (" Those gains bundle a design-time choice with a runtime capability. Only the "
       "second needs sensing, a lookup table and a controller.", False)], 1),
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
    ([("The problem, reproduced and fixed.", B)], 0),
    ([("1.65 V spurious against a 1.4 V threshold. Clamp on with \u22122 V off-bias: "
       "2.58 V of margin.", False)], 1),
    ([("The exhaustive search is complete.", B)], 0),
    ([("720 words at each of four corners \u2014 2,880 transients \u2014 so every "
       "per-corner optimum is a true optimum, not the best of a shortlist.", False)], 1),
    ([("Stress-tested, not asserted.", B)], 0),
    ([("21,600 further transients across five device parameters: the ceiling holds between "
       "4.3 % and 7.7 %. Loop inductance and EMI were tested, not argued.", False)], 1),
    ([("Cross-checked in four tools.", B)], 0),
    ([("LTspice matches ngspice within 2 mV. MATLAB and Octave agree exactly. Vivado: "
       "20 LUTs, 200 MHz met.", False)], 1),
    ([("In total: ", B), ("nearly 35,000 transient simulations.", False)], 1),
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
    ([("ngspice 42 (every sweep) · LTspice 24, in which the port was re-run · "
       "Icarus Verilog (RTL, 8 asserted properties) · Xilinx Vivado 2024.1.2, synthesised · "
       "Cadence Spectre / OCEAN · SKY130 PDK (BSIM4) · Python / NumPy / Matplotlib · "
       "MATLAB Online, an independent cross-check of the Pareto analysis · Git", False)], 1),
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
      ("strapped", B), (" \u2014 5.45 % vs 0.00 % to schedule.", False)], 1),
    ([("Eight asserted properties pass under Icarus, safe reset included; a shoot-through "
       "mutant is caught 221\u00d7 (sh rtl/mutate.sh).", False)], 1),
    ([("Implemented in Vivado 2024.1.2", B), (" on xc7a35t: ", False),
      ("20 LUTs, 20 flip-flops", B), (" \u2014 0.10 % of the part. Register-to-register "
       "timing at 200 MHz is ", False), ("MET, 1.996 ns slack", B), (".", False)], 1),
    ([("The 34 failing paths are all clock-to-pin against a placeholder 4 ns I/O constraint "
       "\u2014 the output buffer alone is 3.49 ns.", False)], 1),
]

