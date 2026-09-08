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
    ([("To find out how much of a gate driver\u2019s benefit needs the driver to "
       "re-tune itself while the converter is running, and how much comes from "
       "choosing one good setting and leaving it fixed.", False)], 1),
    ([("Proposed Solution:", B)], 0),
    ([("A GaN buck converter driven by a ", False), ("segmented gate driver", B),
       (": 8 pull-up steps, 8 pull-down steps, an adjustable dead time, a Miller "
        "clamp and a \u22122 V off rail \u2014 every one of them a setting we can "
        "change and measure.", False)], 1),
    ([("How we approached it:", B)], 0),
    ([("1. Build the converter and check it converts.", B),
      (" 100 V DC in, 48.6 V DC out at 4.88 A \u2014 236.9 W delivered, 97.6 % "
       "efficient.", False)], 1),
    ([("2. Reproduce the fault.", B),
      (" At the fastest setting the gate that should be OFF reaches 1.65 V, "
       "against a 1.4 V turn-on threshold.", False)], 1),
    ([("3. Fix it one change at a time,", B),
      (" measuring each change on its own run, not all at once.", False)], 1),
    ([("4. Ask whether one fixed setting is enough,", B),
      (" by running the driver at two operating points and seeing whether the "
       "best setting moves.", False)], 1),
    ([("Scope and tools:", B)], 0),
    ([("In scope: ", B), ("the converter, the driver, its settings, and the FPGA "
       "controller. ", False), ("Out of scope: ", B), ("building hardware. ", False),
      ("Tools: ", B), ("ngspice for every simulation, LTspice to draw the "
       "circuit and re-check, Vivado for the FPGA.", False)], 1),
]

SLIDE7 = [
    ([("The converter is built and it runs.", B)], 0),
    ([("100 V DC in, 48.6 V DC out at 4.88 A \u2014 236.9 W into the load from "
       "242.6 W drawn, 97.6 % efficient.", False)], 1),
    ([("The fault is reproduced, and fixed.", B)], 0),
    ([("The off gate reaches 1.65 V against a 1.4 V threshold. With the clamp "
       "and the \u22122 V rail: 2.58 V of margin.", False)], 1),
    ([("Specific cases run and measured, one at a time.", B)], 0),
    ([("Five settings at full load, then the same driver swept at two operating "
       "points \u2014 every number below came off its own ngspice run.", False)], 1),
    ([("The setting measured on the converter itself.", B)], 0),
    ([("Across the same knob, power lost moves 4.5 % and peak device voltage "
       "moves 50 %, in opposite directions.", False)], 1),
    ([("The FPGA controller is written and verified.", B)], 0),
    ([("Eight checks pass in Icarus Verilog; 20 LUTs and 20 flip-flops in "
       "Vivado, 200 MHz met with 1.996 ns to spare.", False)], 1),
]


SLIDE7B = [
    ([("Where we are", B)], 0),
    ([("Review-I is done. ", B),
      ("The converter is built and converting, the crosstalk fault is "
       "reproduced and fixed, the named cases have been run, and the FPGA "
       "controller is written and verified.", False)], 1),
    ([("What we aim to do next", B)], 0),
    ([("Review-II \u2014 close the loop.", B),
      (" Add a feedback controller so the output holds its value when the load "
       "changes, then re-run the driver-setting study with the loop closed.",
       False)], 1),
    ([("Review-III \u2014 settle the light-load question.", B),
      (" The cheapest dead time is 15 ns at full load and 5 ns at light load. "
       "Run the converter at both and measure what a two-setting controller "
       "actually saves against one fixed setting \u2014 that is the number the "
       "whole project turns on.", False)], 1),
    ([("Same tools throughout.", B),
      (" ngspice for the circuit, Vivado for the FPGA, start to finish.",
       False)], 1),
    ([("The risk we already know.", B),
      (" Closing the loop changes where the converter actually operates, so the "
       "setting study has to be redone afterwards, not before. That ordering is "
       "the schedule risk.", False)], 1),
    ([("Everything is reproducible", B)], 0),
    ([("Every number in this deck is regenerated by a named script in ", False),
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
    ([("Timing is met where the logic runs. ", B),
      ("The paths that miss are chip-output paths, where the output pad alone "
       "takes 3.49 ns of a 4 ns budget \u2014 pad delay, not logic.", False)], 1),
]
