# -*- coding: utf-8 -*-
"""Content for the Review-1 deck. Every number here is produced by a script in
gan-driver/scripts/ and recorded in results/FINDINGS.md."""

B = True   # bold

SLIDE4 = [
    ([("Problem Statement:", B)], 0),
    ([("When one GaN transistor switches, its fast voltage swing pushes charge into "
       "the gate of the other transistor \u2014 the one that is supposed to stay OFF. "
       "That gate rises to ", False),
      ("1.65 V, and only 1.4 V is needed to turn it on", B),
      (". Both devices conduct at once and the supply shorts through them.", False)], 1),
    ([("Background & Significance:", B)], 0),
    ([("GaN half-bridges sit inside EV inverters and battery chargers. GaN is chosen "
       "because it switches fast \u2014 and that speed is exactly what causes this fault.",
       False)], 1),
    ([("Existing Solutions:", B)], 0),
    ([("Gate drivers that turn the device on in steps, clamp the off gate down, adjust "
       "the gap between the two switching edges, and hold the gate at \u22122 V "
       "[1]\u2013[4]. Reported: 30.5 % less overshoot, 75 % less turn-off loss "
       "[5]\u2013[7].", False)], 1),
    ([("Limitations / Research Gap:", B)], 0),
    ([("Nobody has measured what the re-tuning is worth.", B),
      (" Those gains mix two different things: picking one good setting, and changing "
       "the setting while the converter runs. Only the second needs a sensor, a lookup "
       "table and a controller.", False)], 1),
]


SLIDE6 = [
    ([("Aim:", B)], 0),
    ([("To measure how much of a gate driver\u2019s benefit comes from ", False),
      ("changing its settings while running", B),
      (", and how much comes from simply ", False),
      ("picking one good setting and leaving it", B),
      (". We test every setting instead of arguing the case.", False)], 1),
    ([("Proposed Solution:", B)], 0),
    ([("A GaN gate driver with 720 possible settings: 8 pull-up steps, 8 pull-down "
       "steps, dead time 5\u201335 ns, a gate clamp, and a \u22122 V off rail.",
       False)], 1),
    ([("Method: ", B), ("run all 720 settings at all four operating points, then compare "
       "the best-at-each-point against the best single setting. That difference is what "
       "re-tuning is worth, and nothing else.", False)], 1),
    ([("Methodology / Approach:", B)], 0),
    ([("Double-pulse test in ngspice, using a GaN model built from datasheet numbers.",
       False)], 1),
    ([("Eight measurements per run, taken by one script fixed early. Every number must "
       "stay the same when the timestep changes by 5\u00d7 \u2014 checked, not assumed.",
       False)], 1),
    ([("Project Scope:", B)], 0),
    ([("In scope: ", B), ("driver design, the setting search, transistor-level output "
       "stage in SKY130. ", False), ("Out of scope: ", B),
      ("making the GaN device, sensor hardware, PCB build.", False)], 1),
]

SLIDE7 = [
    ([("The fault is reproduced, and fixed.", B)], 0),
    ([("The off gate reaches 1.65 V against a 1.4 V threshold. With the clamp and the "
       "\u22122 V rail: 2.58 V of margin.", False)], 1),
    ([("Every setting has been tested.", B)], 0),
    ([("720 settings at each of four operating points \u2014 2,880 runs \u2014 so the "
       "best at each point is the true best, not the best of a short list.", False)], 1),
    ([("Stress-tested, not claimed.", B)], 0),
    ([("21,600 more runs across five device parameters: the answer stays between 4.3 % "
       "and 7.7 %. Board inductance and EMI were tested too.", False)], 1),
    ([("Checked in four tools.", B)], 0),
    ([("LTspice matches ngspice within 2 mV. MATLAB and Octave agree exactly. Vivado: "
       "20 LUTs, 200 MHz met.", False)], 1),
    ([("In total: ", B), ("34,622 simulation runs.", False)], 1),
]


SLIDE7B = [
    ([("Where we are", B)], 0),
    ([("Review-I is done. ", B),
      ("The fault is reproduced and fixed, all 720 settings have been tested at every "
       "operating point, and the answer has been stress-tested against the device model, "
       "the board layout and EMI.", False)], 1),
    ([("What we aim to do next", B)], 0),
    ([("Review-II \u2014 build it in silicon, not on an FPGA.", B),
      (" A 200 MHz FPGA can only move the dead time in 5 ns steps. Light load wants "
       "15 ns and everything else wants 5 ns, so the steps are too coarse exactly where "
       "the benefit is. Drawing the output stage transistor by transistor in SKY130 "
       "removes that limit.", False)], 1),
    ([("Review-III \u2014 measure one operating point on real hardware.", B),
      (" Build the half-bridge and measure the off-gate voltage against the simulated "
       "1.65 V. Until that exists this is a simulation study, and the title says so.",
       False)], 1),
    ([("The risk we already know.", B),
      (" A 1.8 V / 3.3 V teaching PDK cannot take a 5 V gate supply. Getting a "
       "5 V-capable PDK is the first milestone, and the one that can hold up the rest.",
       False)], 1),
    ([("Tools, and how to check any of it", B)], 0),
    ([("ngspice 42 \u00b7 LTspice 24 \u00b7 Icarus Verilog \u00b7 Xilinx Vivado 2024.1.2 "
       "\u00b7 Cadence \u00b7 SKY130 \u00b7 Python \u00b7 MATLAB and Octave. Every "
       "number can be regenerated by a named script at ", False),
      ("github.com/Amritha902/gan-driver", B), (".", False)], 1),
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
    ([("Three Verilog modules that produce exactly the 720 settings the SPICE model "
       "uses.", False)], 1),
    ([("Dead time is a ", False), ("live register", B), ("; drive strength is ", False),
      ("fixed at power-up", B), (" \u2014 worth 5.45 % against 0.00 %.", False)], 1),
    ([("Eight checks pass in Icarus Verilog, safe reset included. A deliberately broken "
       "version is caught 221 times (sh rtl/mutate.sh).", False)], 1),
    ([("Built in Vivado 2024.1.2", B), (" on an xc7a35t FPGA: ", False),
      ("20 LUTs, 20 flip-flops", B), (" \u2014 0.10 % of the chip. 200 MHz timing is ",
       False), ("met, with 1.996 ns to spare", B), (".", False)], 1),
    ([("The 34 failing paths are all chip-output paths against a placeholder 4 ns "
       "constraint \u2014 the output buffer alone takes 3.49 ns.", False)], 1),
]
