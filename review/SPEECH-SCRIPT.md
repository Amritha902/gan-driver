# Review-I speech script — 28 slides, ~10 minutes

Timings are the budget, not a target to hit exactly. Total ≈ 10 min 35 s,
which leaves slack in a 10-minute slot because you will talk faster than this
reads. **Slides 7, 13 and 20 are the ones that matter.** If you are running
out of time, cut 15, 18 and 22, never those three.

Numbers in **bold** were re-verified by running the script that produces them.

---

## 1–3 — Title, signature, agenda (30 s)

Do not read these. Get the signed title slide on screen, say the project name
once, and move.

> "This is a segmented gate driver for GaN HEMTs. The question the project
> asks is how much of an active gate driver's benefit actually needs the
> adaptive hardware everyone builds for it."

---

## 4 — Problem statement (45 s)

> "In a GaN half-bridge, when the bottom device turns on the switch node
> slews in a few nanoseconds. That dV/dt drives current through the top
> device's gate–drain capacitance and lifts its gate. If it passes the
> threshold — **1.4 V** on our device — the top device partially turns on
> while the bottom one is already on. That's false turn-on, and it's a
> shoot-through path."
>
> "The easy fix is to slow the switching down. That works, and it throws away
> the switching-loss advantage you bought GaN for. So the real question isn't
> how to stop false turn-on. It's how to stop it while keeping the speed."

If asked why energy storage: the bidirectional half-bridge is the core of a
storage converter, its losses are paid twice — once charging, once
discharging — and its operating range is wide enough that one fixed gate
setting is provably not optimal everywhere.

---

## 5 — Literature landscape (30 s)

> "Thirteen references, grouped by what the driver *does*, not by date. Three
> clusters choose a setting or regulate it in analogue. Only cluster D makes
> the setting a digital code — and that's what makes an exhaustive search
> possible at all. That's where we sit."

---

## 6 — The five closest (40 s)

Walk the columns once, then stop on the last one.

> "Title, author, what each paper set out to do, and then the column that
> matters: the gap we found in it and the part of that gap we fill."
>
> "[10] is the closest published driver architecturally — a segmented driver
> for e-mode GaN, seven slices, pattern timing half a nanosecond to five. But
> it's an ASIC with a fixed pattern set. It doesn't ask what the pattern space
> is worth."

If asked why a SiC paper is the base: because the method is the ancestor. A
gate waveform chosen by a multibit digital code — that's the idea we take to
GaN, where the device has no body diode and the trade changes.

---

## 7 — THE GAP (60 s) — **core slide, do not rush**

> "Every active gate driver paper reports one number: the improvement over a
> conventional driver. That number bundles two completely different things."
>
> "Effect one: choosing a better fixed setting. You do it once, at design
> time. It costs nothing at run time — no sensor, no ADC, no lookup table."
>
> "Effect two: adapting that setting as load, bus voltage and temperature
> move. *This* is the one that needs the sensing hardware the whole
> architecture is sold on."
>
> "Nobody separates them. Not because it isn't interesting, but because
> separating them needs an exhaustive search of the control word at every
> corner, and nobody has run one. That's the gap. And it matters because only
> effect two justifies the hardware — so if it's small, the field is paying
> for something a design-time choice already gives you."

---

## 8 — Proposed solution and aim (40 s)

Open with the aim. The examiner is listening for it.

> "The aim is to measure how much of an active gate driver's benefit actually
> requires per-operating-point adaptation, and how much comes from simply
> choosing a better fixed setting."
>
> "The driver has six things you can set. We make all six a digital word —
> 720 of them — and we search every one at every corner. Not a shortlist.
> That's what makes each per-corner optimum a true optimum."

---

## 9–10 — Architecture and circuit (45 s)

Slide 9 left to right in one sentence, then stop on the dashed block.

> "PWM in, the FPGA holds the control word, the word sets the segmented output
> stage, that drives the half-bridge. Everything solid is configured once at
> power-up. The dashed block — sensing, ADC, lookup table — is the adaptive
> machinery, and this whole project is a measurement of what that one block
> buys."

Slide 10 is the real circuit.

> "Every element here is in sim/dpt.cir. Eight pull-up slices, eight
> pull-down, the active Miller clamp, the off-bias mux. C_GD on Q2, in red, is
> the crosstalk path."

---

## 11 — What a control word is (25 s)

> "Six fields: pull-up strength, two pull-down strengths, dead time, clamp
> enable, and the off-bias rail. 720 combinations. Everything in the rest of
> this deck is measured over these."

---

## 12 — Base paper vs this work (30 s)

> "The base paper shows a gate waveform can be chosen by a digital code. It,
> and every active gate driver paper after it, reports one number against a
> conventional driver."

---

## 13 — WE IMPLEMENTED THE BASE PAPER (60 s) — **core slide**

This is the slide that separates you from a literature review. Be fair to
them; the comparison is stronger when you are.

> "Citing a base paper isn't a comparison, so we built theirs. Their driver is
> a multibit code that changes *during* the switching edge — a shaped gate
> waveform. No Miller clamp, no negative rail, because those are ours. We ran
> it inside our own testbench, byte-identical except for the driver."
>
> "Their approach works. **Plus 0.533 volts** of margin — their sequenced code
> alone clears the threshold. And it beats our own fast fixed code, which
> false-turns-on at **minus 0.249**. So their contribution is real and we
> reproduce it."
>
> "Our Miller clamp gets **plus 0.570** — only marginally past them. The
> clamp alone is not the story. It's the negative off-bias that does the work:
> **plus 2.576 volts**, about **4.8 times** their margin."

If asked what's genuinely new: not the multibit code, that's theirs. Ours is
the two actuators they don't have, and the exhaustive search that lets us
price adaptation — which their paper can't do.

---

## 14 — Work completed, 50 % (30 s)

> "The problem is reproduced and fixed. The full search is done: 720 words at
> four corners, about 34,600 transients across every study."

---

## 15 — Timeline and tools (20 s) — *cut this first if short on time*

> "ngspice for the simulation, LTspice for the portable schematic, Icarus for
> the RTL, Yosys for synthesis, MATLAB for the analysis. Cadence is Review-II
> and needs remote access — that's the ask."

---

## 16 — FPGA controller (35 s)

> "Three modules emitting exactly the control word the SPICE model consumes.
> Dead time gets a live register; drive strength is strapped — that's the
> study's own result built into the hardware."
>
> "Eight properties, all passing. And we mutation-tested it: inject a real
> shoot-through bug and the bench catches it 221 times. A passing test doesn't
> prove much; a test that can fail does."
>
> "Synthesised to real Artix-7 primitives: strapping the word instead of
> leaving all six fields live takes the controller from **53 LUTs to 27**, and
> 33 flip-flops to 25. Half the fabric, for the 3.9 % that adaptation buys."
>
> "The Vivado export is written too — top level, timing constraints and a
> build script, with its own bench passing under Icarus. Not yet run: Vivado
> is Windows and Linux only, so that is a Review-II item."

If asked *why not Vivado*: the free WebPACK edition covers the Artix-7 part
but there is no macOS build. These ARE real Xilinx primitives — LUT2..LUT6,
FDCE, CARRY4 — mapped by yosys `synth_xilinx`, not technology-independent
gates. What is still missing is place-and-route and timing closure, which only
Vivado gives, and the slide says exactly that. Reproduce with
`sh scripts/synth_cost.sh`.

---

## 17 — Result 1, crosstalk (30 s)

> "Fastest drive, no clamp: **1.65 V** spurious against a 1.4 V threshold.
> That's the failure. Clamp on with −2 V off-bias: **−1.18 V**, a **2.58 V**
> margin."

---

## 18 — MATLAB (25 s) — *cut second if short*

> "720 words, **504 feasible**, a seven-word Pareto front. The objectives
> genuinely conflict — you cannot minimise loss, overshoot and crosstalk
> margin together."

---

## 19 — Result 2, the ceiling (45 s)

> "Full search at every corner. The ceiling on operating-point scheduling is
> **5.2 %** against the best single fixed word. And it isn't spread out —
> three corners lose one to four percent, one loses **12.7**. It's carried by
> the dead time, and the dead time by one light-load corner. Freeze pull-up
> drive strength and it costs **zero** — and drive strength is what the
> literature actually schedules."
>
> "And 5.2 % is the generous figure. On the denser 36-point operating grid a
> fixed word loses only **2.0 %**. We quote the larger one because it is the
> number that argues against our own conclusion."

**If asked which number is right:** both, for different questions. 5.2 % is the
ceiling over four deliberately spread corners — the widest spacing we test.
2.0 % is what a real converter sees sweeping a dense grid. Reproduce either
with `scripts/ceiling.py` and `scripts/lut.py`. Quoting only the smaller one
would be self-serving; quoting only the larger one hides that the effect is
even weaker in practice.

---

## 20 — Result 3, the decomposition (45 s) — **core slide**

> "Here's the split nobody separates. Choosing a better fixed word: **25.1 %**
> of baseline. Adapting it per operating point on top of that: **3.9 %**. So
> adaptation is **13.4 %** of the total gain — the other 86.6 % needs no
> sensing, no ADC, no lookup table."
>
> "And one comparator takes 72 % of even that 3.9. A full sense-plus-ADC-plus-
> lookup-table system is left justifying **3.7 %**."

Say plainly: this is a negative result about the adaptive premise, and it is
the contribution.

---

## 21 — Result 4, loop inductance (25 s)

> "Adaptive control pays only below about **2.5 nH** of loop inductance. Above
> that a fixed word is nearly as good. And loop inductance is board layout,
> not the transistor."

---

## 22 — Backup (skip unless asked)

Only open this if challenged on robustness. Across 21,600 transients no device
parameter moves the ceiling outside **4.3–7.7 %**.

---

## 23 — DEMO (45 s)

The clip runs **22 s**. Play it and stay quiet for the first five seconds —
the switch node falling is the whole setup, and narrating over it just
competes with the picture. The peak labels only appear once each trace
reaches its peak, so nothing on screen contradicts you before it happens.

> "This is real captured ngspice output, not an animation. Watch the high-side
> gate. On the left, the fastest drive with no clamp — the gate is pushed
> above the threshold line and the device turns on when it shouldn't. On the
> right, same word, clamp on and −2 V off-bias — the same event now sits two
> and a half volts below threshold."

---

## 24 — Why the numbers hold (20 s)

> "Every number survives a 25× timestep refinement. Ten wrong numbers were
> caught by our own convergence checks before they reached the report."

---

## 25 — Conclusion and next steps (40 s)

> "Choosing the control word well matters enormously — roughly fivefold in
> switching energy. Adapting it does not: 3.9 %, and one comparator takes most
> of that."
>
> "Stated positively, and this is the deliverable: use the recommended fixed
> word with a light-load comparator, and the full adaptive system is left
> justifying 3.7 % of the achievable gain."
>
> "What it does not support: no silicon has been measured, and one device
> model underlies everything. Review-II is the transistor-level output stage
> in Cadence — and sub-nanosecond dead-time control needs silicon, not fabric:
> the 2025 driver we cite reaches 0.19 ns where a 200 MHz FPGA grid is 5 ns.
> That's why we need Cadence access."

---

## 26–28 — References, thanks (10 s)

> "Thirty references, against a minimum of eight to ten. All thirty are
> verified against the publisher record — authors, volume, issue and pages
> resolved by DOI, not typed in. Thank you."

If asked how they are organised: four clusters by what the driver *does*,
not by date. A–C choose or regulate the setting in analogue; only D makes it
a digital code, which is what makes an exhaustive search possible.

---

# Likely questions

**"Show me the Miller clamp in the schematic."**
sim/dpt.cir with models/segdrv.lib — `Sclk out nclk clk ref SWP` with
`Rclk nclk vn 0.5`, a half-ohm switch from the off device's gate to the
negative rail, timed separately from the pull-down. It clamps to the negative
rail, not the source — clamping to source would fight the −2 V bias. Do not
open the .asc sheets for this; they're teaching drawings and don't have it.

**"Did you actually implement the base paper or just cite it?"**
Implemented. models/basedrv.lib, run in our own testbench. Slide 13 is the
result. Their approach works — +0.533 V — and beats our fast fixed code.

**"Isn't 13.4 % an artefact of your cost function?"**
Partly, and we quantified it rather than defending it. Over 106 overshoot
weights the fixed word is worth 23 to 29 per cent and adaptation 1.3 to 6.4.
The number moves; the ordering doesn't. The fixed word wins at every weight
we tested, out to five, which is already an extreme price on overshoot.

**"Slide 19 says 5.2 %, slide 22 says nominal 5.95. Which is it?"**
Both, for different searches. 5.2 is the four-corner search — that's the
headline. 5.95 is the nominal of the perturbation study, a two-corner search
on its own sweep, so its absolute value isn't comparable; its "vs nom." column
is. Same cost weight in both. And 5.2 % against the best fixed word is the
same thing as 3.9 % of baseline: 3.9 divided by 74.9.

**"Is this simulated or measured?"**
Entirely simulation, in ngspice, with a behavioural GaN model validated
against datasheet values — R_DS(on) 26.0 mΩ against a 25 mΩ target. Hardware
is the next phase. Say it plainly; it's a Review-I project.

**"Why not just slow it down?"**
That's the trivial fix and it discards the switching-loss benefit of GaN. The
Pareto front on slide 18 shows loss, overshoot and crosstalk margin cannot be
minimised together.

**"Did Cadence actually run?"**
No, and the deck says so. Everything is ngspice. For LTspice open
sim/dpt.cir — that's the complete model and it carries the clamp.

**"Your dead-time number depends on which corners you pick."**
Yes, and we found that ourselves. It's one light-load corner: drop
50 V / 2 A / 25 °C and freezing dead time costs 0.00 per cent instead of 5.45.
The leave-one-out table is in FINDINGS.md section 32.

**"How do we know the numbers are right?"**
Ten wrong numbers were caught by our own convergence and resampling checks
before any reached the report. And the MATLAB analysis is an independent
reimplementation of the Python — it reproduces 5.2 %, 25.1, 3.9 and 13.4 to
the decimal.
