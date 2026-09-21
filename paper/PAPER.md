# Most of what a programmable gate driver buys, a single fixed setting already has

**A 720-word study of segmented gate drive for E-mode GaN, and the case against
adapting it**

Sanjay Kumar · Aamir Abdullah · Amritha S
School of Electronics Engineering (SENSE), VIT Chennai
Guide: Dr. Bindu

---

## Abstract

Segmented gate drivers let the drive strength of a GaN half-bridge be chosen
digitally, per operating point, rather than fixed by a resistor at design
time. The literature reports gains from doing so. It does not report how much
of that gain needs the adaptation, and how much a single well-chosen fixed
setting would have delivered anyway.

We built a 6-field, 720-word segmented driver for a 100 V / 500 kHz
synchronous buck converter, implemented the closest published driver
(Zhang *et al.*, ISPSD 2020) in the same testbench, and searched the whole
control-word space across 36 operating points — 60,533 transient
simulations in ngspice.

Choosing a better **fixed** word is worth **26.5 %** of the baseline.
**Adapting** that word per operating point adds **2.6 %** more — **8.9 %**
of the total gain, against a ceiling of 3.5 %. A single comparator on load
current captures 47 % of the adaptive part; two capture 61 %. That leaves
**4.7 % of the total gain** to justify a sense chain, an ADC and a lookup
table. Leave-one-corner-out gives the identical control word on 36 of 36
corners.

The practical conclusion is a design rule, not a driver: **build the
segmented output stage, strap the word, and spend the sensing budget
elsewhere.** The 65 % of controller logic saved by strapping is measured, not
estimated.

We also report two negative results that a simulation-only study is obliged
to report: the sign of the headline fault depends on which capacitance law
the device model uses, and a bus decoupling network that fixed a 100 V
overshoot caused shoot-through at 200 V until it was damped.

---

## I. Introduction

An E-mode GaN HEMT switches fast enough that the converter's own dv/dt turns
its partner device back on. Drain-to-gate capacitance couples the switching
edge into the gate of the device that is supposed to be off; with a 1.4 V
threshold and 150 pF of C_GD, the off gate in our converter reaches **1.65 V**
against that threshold. That is a shoot-through, and it is the reason a GaN
half-bridge is harder to build than a silicon one at the same power.

GaN is still the right device, and the margin is not small. Measured on the
same converter with only the device swapped:

| | GaN HEMT | Si MOSFET |
|---|---|---|
| Latency, PWM → switch node | **2.78 ns** | 17.55 ns |
| Edge, 10 → 90 % | **0.78 ns** | 6.65 ns |
| Power dissipated in devices | **2.598 W** | 8.601 W |
| Gate-drive power | **0.035 W** | 1.489 W |
| Efficiency | **97.42 %** | 95.06 % |
| Switch-node overshoot | 17.9 % | **−1.5 %** |

Silicon wins the last row, and it wins it for the same reason it loses the
other five: its edge is nine times slower. Speed and device stress are one
knob. Choosing GaN is choosing to manage the stress.

The managing is done by the gate driver, and the published direction of
travel is to make it programmable. The question nobody asks is whether the
programmability earns its silicon.

### Contribution

1. The full control-word space searched, not sampled: 720 words × 36
   operating points, 60,533 transients.
2. A decomposition of the gain into the part a fixed word captures and the
   part that genuinely requires adaptation.
3. A complexity ladder — constant word, one comparator, two comparators,
   full sense+ADC+LUT — with the marginal value of each rung measured.
4. A negative result stated as a design rule, with the conditions under which
   it does not hold.

---

## II. Method

### A. The converter and the device

`sim/buck.cir`: 100 V → 50 V synchronous buck, 500 kHz, 22 µH / 4.7 µF
output filter, 3 nH power-loop inductance, damped bus decoupling. Devices are
an EPC2010C-class E-mode GaN model (200 V, ~25 mΩ, V_th 1.4 V) with
charge-based (`Q=`) drain-gate capacitance.

Every number in this paper is measured on the converter, not on a driver in
isolation.

### B. The driver

Six fields — pull-up strength, pull-down strength, high-side and low-side
independently, dead time, active Miller clamp, and off-rail select (0 V or
−2 V) — giving **720 distinct control words**. Pull-up and pull-down are
8-slice thermometer-coded banks.

The controller is real RTL (`seg_gate_ctrl.v`), verified against eight
properties in Icarus Verilog and synthesised in Vivado 2024.1 for
`xc7a35tcpg236-1`: **20 LUTs, 20 flip-flops, 200 MHz register-to-register
timing met with 1.996 ns slack.** The RTL's VCD output drives the SPICE
slices directly in co-simulation; the two agree to 0.081 V.

### C. The baseline

`models/zhangdrv.lib` implements the base paper's scheme: seven slices in two
stages, the pattern selected by one bias resistor. It has no active clamp and
no negative off rail — their absence *is* the comparison. Slice sizing is not
given in the four-page ISPSD paper; equal slices and an N/(7−N) split are our
inference and are documented as such in the model file.

This is our implementation of their described scheme in our testbench. It is
not their measured silicon, and no claim here should be read as such.

### D. What is measured

Crosstalk margin (threshold minus the peak the off gate reaches **while the
other device conducts**), switching energy, peak drain-source voltage,
switch-node dv/dt, device dissipation, gate-drive power and efficiency.

Measuring the off gate over the whole cycle instead of only during the
aggressor's on-time reports the drive rail every time and hides the failure
being looked for. This matters: it is how the 200 V defect in §V-B stayed
invisible.

---

## III. Results

### A. The fault, and the fix, one change at a time

| configuration | off-gate peak | margin |
|---|---|---|
| fastest word, no clamp | 1.65 V | **−0.25 V** |
| + active Miller clamp | 0.83 V | +0.57 V |
| + −2 V off rail | −1.176 V | **+2.576 V** |

The clamp alone is worth +0.82 V; the negative rail adds a further +2.01 V.
On transistor-level SKY130 devices the clamp's own contribution falls to
+0.03 V — the ordering survives, the attribution does not. We state both.

### B. Against the base paper

Same converter, same device, same output stage; only the control changes.

| | Ours | Base paper |
|---|---|---|
| Latency | **2.78 ns** | 4.04 ns |
| Edge, 10 → 90 % | **0.78 ns** | 2.06 ns |
| Device dissipation | **2.598 W** | 2.928 W |
| Gate-drive power | 0.035 W | **0.031 W** |
| Efficiency | **97.42 %** | 97.31 % |
| Switch-node overshoot | 17.9 % | **2.9 %** |
| Crosstalk margin | **+2.576 V** | +0.407 V |

Two rows go against us, and they go together: we switch 2.5× faster, so we
spend 13 % more gate power and overshoot six times harder. They reduce
crosstalk by slowing the edge; we keep the edge and hold the gate down. The
margin is not bought with switching speed, and the overshoot is the price.

Across four corners spanning the envelope, with their driver re-optimised at
*every* corner — freedom their one-resistor design does not have — our single
fixed word still leads by 5.5× at the mildest corner and 12.4× at the
hottest, because their margin degrades with temperature and a clamp does not.

### C. The decomposition — the main result

Over 720 words × 36 operating points:

| | share of baseline |
|---|---|
| (A) choosing a better **fixed** word | **26.5 %** |
| (B) **adapting** it per operating point | **2.6 %** |
| (B) as a fraction of the total gain | **8.9 %** |
| ceiling on any scheduling scheme | 3.5 % |

### D. The complexity ladder

| rung | captures | left to justify more |
|---|---|---|
| constant word | — | 2.6 % |
| + one comparator (load current at 10 A) | 47 % of (B) | **4.7 %** of total |
| + two comparators | 61 % of (B) | **3.4 %** of total |
| full sense + ADC + LUT | 100 % of (B) | — |

Strapping the word instead of keeping all six fields live takes the
controller from 371 cells / 32 FF to 129 cells / 24 FF — **65 % of the logic
saved** — to recover, at most, 4.7 % of the total gain.

**Leave-one-corner-out returns the identical control word on 36 of 36
corners.** The fixed word is not overfitted to the grid that chose it.

### E. Which field matters

| field frozen | cost |
|---|---|
| pull-up drive strength | **0.00 %** |
| dead time | 5.45 % (0.00 % without the light-load corner) |
| active Miller clamp | worth 9.7 – 12.2 % |

The clamp and the off rail carry the result. The drive-strength segmentation
— the base paper's entire contribution, and the part everyone is building —
is the field that costs nothing to freeze.

---

### F. The converter across its envelope

Eight bus x load points, the converter measured at each rather than at the
one operating point the headline is quoted at:

| bus | load | peak v(sw) | overshoot | gate, HS on | margin | efficiency |
|---|---|---|---|---|---|---|
| 50 V | 2 A | 68.1 V | 36.1 % | -0.98 V | **+2.38 V** | 97.08 % |
| 50 V | 10 A | 61.8 V | 23.6 % | -1.12 V | **+2.52 V** | 92.86 % |
| 100 V | 2 A | 113.6 V | 13.6 % | -1.16 V | **+2.56 V** | 97.67 % |
| 100 V | 10 A | 110.1 V | 10.1 % | -1.21 V | **+2.61 V** | 96.02 % |
| 150 V | 2 A | 171.3 V | 14.2 % | -0.86 V | **+2.26 V** | 98.07 % |
| 150 V | 10 A | 164.6 V | 9.8 % | -1.09 V | **+2.49 V** | 97.11 % |
| 200 V | 2 A | 206.2 V | 3.1 % | -1.09 V | **+2.49 V** | 98.42 % |
| 200 V | 10 A | 208.2 V | 4.1 % | -0.74 V | **+2.14 V** | 97.65 % |

The margin column is the result: the off device stays off at every point,
worst case +2.14 V. Overshoot *falls* with bus voltage, because the inductive
kick is set by the load current and the 3 nH loop, not by the rail.

The two 200 V rows exceed the device's 200 V rating, by 6.2 V and 8.2 V.
That is not a driver failure -- their overshoot is the smallest in the sweep.
It is that a 200 V-rated part cannot run a 200 V bus, because any overshoot
at all then exceeds the rating. **The envelope is therefore stated as
50-150 V on this device**, where the worst-case peak is 171.3 V against a
200 V rating. Operating at 200 V requires a higher-rated part, not a
different driver.

The architecture figure previously said 50-200 V. It was claimed at one
point and measured at none. It now says what was measured.

---

## IV. Robustness

- **Device spread.** 24 devices with V_th, transconductance, C_GS and C_J
  varied jointly: worst-case margin **+1.895 V**, 0 of 24 false turn-on.
- **Capacitance law.** Behavioural `C=` against charge-based `Q=`: the
  ordering survives both.
- **Transistor level.** SKY130 open-PDK output stage: sign and ordering of
  the result both survive.
- **Loop inductance.** The 3 nH figure is our choice, and the conclusion is
  sensitive to it. Stated as a threat, not a result.

---

## V. Threats to validity

### A. This is a simulation study

No hardware has been measured. The title says so and the completion
accounting says so. Everything below follows from that.

### B. Two things a simulation study gets wrong, and how we found them

**The sign of the headline fault is model-dependent.** The no-clamp row
changes sign between capacitance laws. "The constant word causes false
turn-on" is therefore a statement about the model as much as the device.

**A fix at one operating point broke another.** A bus decoupling network was
added to cure a 168 V overshoot at 100 V. It did. It was an undamped series
L-C (Q ≈ 3.5 near 22 MHz) that the switching edges pumped once a cycle; at
200 V it crossed the low-side threshold and produced **112 A** of
shoot-through and a **464 V** peak on a 200 V-rated device. Damping it
(R 20 mΩ → 1 Ω) removed it, improved every metric at 100 V as well, and
brought the converter deck into agreement with the double-pulse deck to
within 1 V at 200 V.

It survived because the 36-corner study runs on the double-pulse deck, which
has no decoupling network and so could not see it. **A study that sweeps one
deck exhaustively is not the same as a study that sweeps the system.**

### C. The base-paper comparison is our reimplementation

Built from a four-page description, not from their netlist. We state the
inferences in the model file.

---

## VI. Conclusion

Segmented gate drive for GaN works, and this paper is not an argument against
building it. It is an argument against a specific and popular next step.

Of the gain available from controlling drive strength digitally, **89 % is
had by choosing one good fixed word**. The remaining 11 % is most of the
engineering: sensing, conversion, a lookup table, and 65 % more controller
logic. One comparator recovers about half of that remainder for almost
nothing.

**Build the segmented output stage. Strap the word. Add one comparator on
load current if the light-load corner matters. Spend the sensing budget
somewhere it buys more than 4.7 %.**

The one corner where that rule costs something, and the conditions under
which the model that produced it stops being trustworthy, are both stated
above rather than left for a reader to find.

---

## Reproducing

Every number regenerates from `results/RESULTS-SUMMARY.txt`, which names the
script for each. The study grid is `results/full_grid.csv`; the decomposition
is `scripts/novelty.py` and `scripts/grid_analyse.py`; the head-to-head is
`scripts/headtohead.py` and `scripts/panel_metrics.py`; the decoupling
finding is `scripts/decoupling_damping.py`.
