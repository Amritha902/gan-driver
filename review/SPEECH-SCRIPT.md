# Review-I — what to say, slide by slide

25 slides. 10 minutes of talking. Backup slides are not spoken unless asked.
Times are targets, not limits; the two that matter are slide 4 (60 s) and
slide 18 (45 s). If you are running late, cut slide 13 and slide 16.

Say numbers exactly as written. Every one is reproducible from the repo, and
if a panel member asks "where does that come from", the script name is in
the caption on the slide itself.

---

## Slide 2 — Title (15 s)

"Good morning. This is Project-I: a segmented gate driver for GaN HEMTs.
The one-line version is that we built a driver whose behaviour is chosen by
a digital code, searched every setting of that code exhaustively, and
measured something the literature reports as a single number but which is
actually two separate things."

---

## Slide 4 — Problem statement (60 s) — the 2-mark slide

Land two things: the failure is real, and the gap is specific.

"In a GaN half-bridge, when one device switches, the voltage at the
switching node moves extremely fast. That dV/dt couples charge through the
gate-drain capacitance into the gate of the device that is supposed to be
off. If that spurious gate voltage crosses the threshold, the off device
turns partially on — both devices conduct, and you get shoot-through, extra
loss, and at worst destruction.

We measure that spurious pulse at 1.65 volts against a 1.4 volt threshold.
So it is not marginal; it fails.

GaN makes this worse for two reasons. It switches faster, which is the whole
reason you chose GaN. And it has no body diode, so if you hold the gate
negative to buy margin, you pay for that negative voltage again in
third-quadrant conduction, every dead time.

The gap is this. Active gate drivers exist, and they report large numbers —
thirty per cent less overshoot, seventy-five per cent less turn-off loss.
But those numbers conflate two different things: choosing better fixed
settings, and adapting settings per operating point. Only the second needs
sensing, an ADC and a lookup table. No published work separates them, so
nobody knows what the adaptation is actually worth."

---

## Slide 5 — Literature landscape (30 s)

Do not read the table.

"Thirteen references, grouped by what the driver does rather than by date.
Cluster A is passive and analogue crosstalk fixes — negative bias, Miller
clamps. Cluster B is closed-loop analogue adaptation. Cluster C is adaptive
dead-time control. Cluster D is digital and segmented drive, and that is
where this project sits. The important point is that only cluster D makes
the setting a digital code — which is what makes an exhaustive search
possible at all."

---

## Slide 6 — The five closest, and the base paper (25 s)

"Reference 9 is our base paper — Takayama and Hikihara, 2022. They build the
gate driver as a digital-to-analogue converter and drive the gate with a
multibit code. That code is the direct ancestor of our control word, and
because it is digital it can be implemented on an FPGA.

Reference 10 is the closest published architecture to ours — a segmented
driver on E-mode GaN. Eleven, twelve and thirteen are recent GaN work on
exactly our failure mode."

If asked why a SiC paper is the base: "Because the method is the ancestor,
not the device. We reproduce the method on GaN — that is part of the
contribution."

---

## Slide 7 — Proposed solution (30 s)

Open with the aim — the examiner is listening for it.

"The aim is to measure how much of an active gate driver's benefit actually
needs per-operating-point adaptation, and how much you get from simply
choosing a better fixed setting."

"The driver has six things you can set. We make all six a digital word, and
we search all 720 of them at every operating corner. Not a shortlist —
every one. That means each per-corner optimum is a true optimum, so when we
say adaptation is worth X, X is a real ceiling and not an artefact of which
words we happened to try."

---

## Slide 8 — Architecture (30 s)

Walk left to right in one sentence, then stop on the dashed block.

"PWM comes in, the FPGA holds the control word, the word sets the segmented
output stage, and that drives the half-bridge. Everything solid is
configured once at power-up. The dashed block — sensing, ADC, lookup table —
is the adaptive machinery, and the whole project is a measurement of what
that one block buys."

---

## Slide 9 — The circuit (30 s)

Trace the red path with your finger.

"This is what is actually simulated. Q1 switches, the SW node moves, charge
couples through C-G-D into Q2's gate, and Q2 turns on when it should be off.
The two things that fix it are here as well: the active Miller clamp, which
shorts gate to source, and the off-bias mux, which holds the gate below
threshold."

Do not read component values.

---

## Slide 10 — What is a control word (30 s)

Do not rush this. Everything after it is a comparison between words.

"A control word is one setting of six fields: how many pull-up slices, how
many pull-down slices on each side, the dead time, whether the Miller clamp
is on, and the gate off-bias. Multiply the ranges and you get 720 words.

The distinction that matters is this. A fixed word is strapped at power-up —
it costs nothing. Scheduling means sensing the operating point and switching
to a different word for it, and that needs the ADC and the lookup table.
The whole project measures the gap between those two."

---

## Slide 11 — Base paper vs this work (35 s)

Land three rows and move on.

"Against the base paper: they control one field, we control six, which is
720 words. They measure selected codes, we search exhaustively. And they
report one bundled number, where we split it into fixed versus adaptive.

Be clear about what we have not done — we have not re-run their SiC
experiment. This is a comparison of method and scope, not a claim that we
beat their result on their metric. That replication is the next step."

---

## Slide 12 — Work completed, 50 % (40 s)

"Crosstalk reproduced and fixed: 1.65 volts spurious becomes minus 1.18
volts with the clamp and negative bias, a 2.58 volt margin.

The exhaustive search is done — 720 words at four corners, plus a 36-point
operating grid.

Stress-tested: 21,600 further transients perturbing five device parameters;
the answer holds between 4.3 and 7.7 per cent.

And both objections to the result have been tested rather than argued. Loop
inductance, and EMI.

In total, close to 35,000 transient simulations."

---

## Slide 15 — Result 1, crosstalk (40 s)

Point at the red marker below the threshold line.

"Baseline, fastest drive, no clamp: 1.649 volts against a 1.4 volt
threshold — that is a false turn-on. Add the Miller clamp: 0.830 volts,
safe. Add minus 2 volt off-bias as well: minus 1.176 volts, with 2.576 volts
of margin.

And the price of that safety is 0.04 per cent in switching energy. Once the
clamp is present, crosstalk safety is nearly free."

---

## Slide 16 — MATLAB (35 s)

"Two things here. On the left, the full 720-word sweep: 504 are feasible,
and the Pareto front is only seven words wide — the choice really is that
constrained.

On the right, the model check. Two standard hand calculations for the same
spurious voltage disagree by a factor of 8.7 — one says 7.5 volts, the other
says 0.86. SPICE measures 1.65, inside the bracket. That gap is the argument
for simulating this rather than hand-calculating it."

---

## Slide 17 — Result 2, the ceiling (25 s)

Say it plainly. Do not soften it.

"Scheduling the control word across operating points is worth 5.2 per cent
against the best single fixed word. This is a negative result about the
adaptive premise, and we are reporting it rather than hiding it. The next
two slides do the real work."

---

## Slide 18 — Result 3, the novelty (45 s) — the sentence they should leave with

Build it in three steps.

"Choosing a better fixed word is worth 25.1 per cent.

Adapting that word per operating point adds only 3.9 per cent — a seventh of
the total.

And 72 per cent of even that 3.9 is captured by a single comparator on load
current, not a lookup table.

So a full sense, ADC and lookup-table chain is left justifying 3.7 per cent
of the achievable gain over a fixed word plus one comparator. That is the
number the adaptive hardware has to justify, and no published work states it,
because separating those two halves requires the exhaustive search rather
than a shortlist."

If asked why nobody found this: "Because they report one number."

---

## Slide 19 — Result 4, the design chart (35 s)

Do NOT call it a single crossover.

"Eight loop inductances, 7,200 transients. Adaptive control pays below about
2.5 nanohenries, peaking at 13.5 per cent at 1.5 nH — and then it falls back
to 8.1 per cent at 1.0 nH.

That fall-back is the interesting part. At 1.0 nH only 165 of the 720 words
are still safe, so the fixed word and the per-corner optima get squeezed into
the same narrow region and the gap shrinks. Below about 2 nH, feasibility is
what binds, not optimisation.

Loop inductance is board layout, not the transistor. So this is a layout
decision that determines whether the adaptive path is worth building at all,
and the literature does not state that trade-off."

---

## Slide 21 — Demo (30 s)

Play it. Do not talk over it. One sentence before:

"This is captured ngspice output — the failure, the fix, and the search
running."

---

## Slide 23 — Conclusion (35 s)

State the limits yourself before the panel finds them.

"What the data supports: choosing the word well matters enormously — roughly
fivefold in switching energy. Adapting it does not: 3.9 per cent, and one
comparator takes 72 per cent of that.

The benefit that does exist is carried by the dead time — and the dead time
in turn by the light-load corner alone. Drop that one corner and freezing
dead time costs nothing.

What we have now answered: the EMI objection. Pricing EMI makes scheduling
worth less, not more — 5.95 per cent falls to 0.15.

What remains: which EMI measure a designer should price is unsettled, no
silicon has been measured, and one device model underlies everything.
Review-II is the transistor-level stage in Cadence; Review-III is hardware."

---

# Likely questions

**"Why is the clamp worth more than scheduling?"**
Because the clamp removes a failure mode, and scheduling only trims a cost
that is already small. Different kinds of quantity.

**"Have you run real silicon?"**
No. This is a simulation study and the title says so. Review-III.

**"Did Cadence actually run?"**
No, and the deck states that. Everything is ngspice. The Spectre deck is a
port, not a cross-simulator check. For LTspice, open sim/dpt.cir — that is
the complete model and it carries the Miller clamp. The three ltspice/*.asc
sheets are teaching illustrations of the crosstalk mechanism and do NOT draw
the clamp; do not present them as the clamped design.

**"Your dead-time number depends on which corners you pick."**
Yes, and we found that ourselves. It is one light-load corner: drop
50 V / 2 A / 25 °C and freezing dead time costs 0.00 per cent instead of
5.45. The leave-one-out table is in FINDINGS.md section 32.

**"Doesn't EMI change your answer?"**
We ran it. 1,440 transients under objectives that price slew rate and band
energy. It makes scheduling worth less, not more.

**"Is eight references enough?"**
There are thirteen. Eight to ten was the stated minimum.

**"How do we know the numbers are right?"**
Ten wrong numbers were caught by our own convergence and resampling checks
before any of them reached the report. That is on the backup slide.

**"Show me the Miller clamp in the schematic."**
sim/dpt.cir with models/segdrv.lib — the clamp is `Sclk out nclk clk ref SWP`
with `Rclk nclk vn 0.5`, a 0.5 ohm switch from the off device's gate to the
negative rail, timed separately from the pull-down. Do not open the .asc
sheets for this; they don't have it.

**"Slide 17 says 5.2 per cent, slide 20 says nominal 5.95. Which is it?"**
Both, for different searches. 5.2 is the four-corner search — that is the
headline. 5.95 is the nominal of the perturbation study, which is a
two-corner search on its own sweep, so its absolute value isn't comparable;
its "vs nom." column is. Same cost weight in both, w_ov = 0.05, so the
difference is the corner set, not the weighting. And 5.2 per cent against the
best fixed word is the same thing as the 3.9 per cent of baseline in the
results summary — 3.9 divided by 74.9.
