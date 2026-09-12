# The examiner's report

Written against this project as if by the reviewer who wants to fail it, then
answered. Nothing here is softened, and where the answer is "you are right,
that is a real weakness", it says so and the weakness is stated on a slide
rather than buried.

Round 1 of this was run on 12 September 2026 after the closed-loop converter,
the transistor-level check and the head-to-head comparison were added. Each
finding below is marked **FIXED**, **STATED** (a real limit, now said out
loud in the deck instead of being left for the examiner to find) or **OPEN**.

---

## The findings that changed the work

### J1. "The clamp fixes it" is not true on real transistors — **FIXED**

The deck's Result 1 says *crosstalk is real; the clamp fixes it*, on the
strength of the margin going from −0.249 V to +0.570 V. That number comes
from an output stage whose slices are ideal switches: 10 mΩ on, 1 GΩ off, no
gate charge, no threshold, no transition time.

Run the identical configuration on `models/segdrv_sky130.lib` — the same
output stage in real SKY130 5 V devices — and the clamp alone gives
**+0.031 V**. That is not a fix. It is the difference between a device that
turns on and one that does not, measured in millivolts, at one corner, with
nothing left for temperature or a worse layout.

| configuration | ideal switches | SKY130 transistors |
|---|---|---|
| constant word, no clamp | −0.249 V | −0.563 V |
| clamp on | +0.570 V | **+0.031 V** |
| clamp + −2 V off-bias | +2.576 V | **+2.032 V** |

The architecture survives — the sign and the ordering are the same on both
stages, which is what had to hold — but the *reason* it survives changes. The
clamp is not the fix. **The −2 V off-bias is the fix, and the clamp is what
makes the off-bias hold.** The ideal-switch model was flattering the clamp
because an ideal switch pulls the gate down through 10 mΩ; a real NMOS pulls
it through a channel that has to be turned on first.

This is now a slide, and `scripts/silicon_check.py` is the script that owns it.

### J2. A bug that made every transistor-level run through `gansim.py` return nothing — **FIXED**

`gansim.py` copies a deck into a temporary directory and rewrites
`.include ../models/` to an absolute path. The SKY130 decks also pull in the
PDK with `.lib "../pdk/sky130_5v.lib"`, which was **not** rewritten. From a
temp directory that path resolves to nothing, ngspice carries on without the
transistor models, and the run exits zero having measured nothing.

It fails safe — callers got `None` rather than a wrong number, so no published
figure is affected — but it silently made the transistor-level stage
unreachable through the one interface every other script uses. Found by
building J1 and watching three rows come back blank against a deck that runs
perfectly from `sim/`. Fixed by rewriting the `.lib` path too.

### J3. The loop was unstable, twice, before it worked — **FIXED, and the failures are on the record**

The first compensator period-doubled: a 4 µs triangle on a 2 µs switching
period, which is the textbook f_sw/2 limit cycle. The second, a type-II
designed properly around a 10 µF plant, could not be made to work at all:
crossing over above the LC corner gives negative phase margin no matter where
the single zero goes, and crossing below it leaves a loop too slow to settle
between two disturbances. Measured, not assumed — 10.4 µS still climbing at
340 µs, 30 µS drifting 23 V, 100 µS railing 98 V.

Type III fixed it. The deck header carries all of it, because a design that
only shows its final values is not reproducible.

### J3b. An efficiency above 100 %, and the averaging bug behind it — **FIXED**

The first efficiency numbers out of `closedloop.py` were 107.8 %. Energy is
not being created; the average was.

ngspice's timestep is adaptive. It takes tiny steps through every switching
edge, where the input current spikes, and long ones in between. A plain
`.mean()` over those samples therefore weights the edges hundreds of times too
heavily, and it put the measured input power at 230 W against 249 W delivered.
Replaced with trapezoidal integration over the real time axis.

Worth saying that the rest of the project already did this correctly:
`gansim.py` and `bucksim.py` both integrate with `np.trapezoid`, and
`si_vs_gan.py` uses ngspice's own `meas ... AVG`, which is time-weighted in
the simulator. The bug was confined to the script written today — checked, not
assumed.

The lesson generalises: **an impossible number is the cheapest bug to find,
and the same mistake in a plausible number is invisible.** The output voltage
averages were biased by the same amount and nobody would ever have noticed.

### J4. The analytic design was 4× out, and the deck now says so — **STATED**

The K-factor design predicted a 33 kHz crossover. The measured step response
said about 2 kHz: 109 % overshoot, 119 µs to settle. The feedback branch was
scaled empirically and re-measured at each step; ×4 is shipped.

A design procedure that needs a 4× correction should say so rather than
present the analytic values as though they had been achieved. The averaged
model neglects the driver, the dead time and the device losses, and that is
the size of the gap.

### J5. "Phase margin 59°" was never measured — **STATED**

It came out of the averaged model, which J4 shows is wrong by 4× in gain. No
phase margin is measured anywhere in this project: it needs an AC analysis
about a periodic operating point, which ngspice cannot do on a switching
deck. The deck header now says this in those words. **Do not quote 59° as a
result.** What is demonstrated is weaker and is stated as such: one fixed set
of component values is stable through both disturbances.

### J5b. Soft-start overshoot of 10.9 % — **FIXED**

Reported on its own slide as "the one number here we are not proud of", which
is honest and was also a reason not to fix it. It is the loop absorbing the
step in dv/dt at the end of the reference ramp, so it depends on how fast the
ramp is. Measured at three lengths: 200 µs gives 10.8 %, 400 µs gives 5.5 %,
600 µs gives 3.6 %. 600 µs is shipped. Three runs was the whole cost.

### J6. The base paper is reproduced from its description, not its netlist — **STATED**

`models/zhangdrv.lib` is our reading of Zhang et al.'s scheme: seven slices
engaged as a timed pattern, the pattern selected by one bias resistor, no
clamp, no negative rail. It is not their netlist, which is not published, and
it is not their silicon.

So "6.3× the base paper" means *6.3× our implementation of their described
scheme, in our testbench, with our parasitics*. It does **not** mean 6.3×
their measured result. Anyone who reads it the second way has been misled, and
the deck now says which one it is. The reproduction is checked where it can
be — setting `nseg=7` collapses their scheme to a constant code and gives
−0.278 V against our own constant-code −0.249 V, which is independent
agreement to 0.03 V — but that checks the implementation, not the paper.

### J7. The comparison quoted them at one setting we chose — **FIXED earlier, and extended**

Already corrected once: `basepaper_compare.py` now searches their stated range
and quotes their best. `scripts/headtohead.py` goes further and gives them a
freedom their own paper does not have — **re-optimised at every corner**,
against our one fixed word — and reports both that and the single fixed
setting their design actually builds.

---

## The findings that are real and are not going away

### J8. It is entirely simulation — **OPEN**

No silicon measured, no bench, no scope trace. This is the honest ceiling on
every number in the project and it is why the title says "simulation study".
It is the 7 % of the completion table that no amount of further simulating
can close.

### J9. One behavioural GaN model underlies everything — **OPEN**

`models/egan.lib` is EPC2010C-class. J1 shows the *driver* side survives being
rebuilt out of real transistors; there is no equivalent check on the GaN side,
because there is no open PDK for a 200 V GaN HEMT. If that model is wrong in
its C_GD or its threshold, every margin in this project moves together.

### J10. n = 4 — **STATED**

Four corners. The leave-one-corner-out test that says a fitted schedule does
not generalise is three training points and one held-out point, four times
over. It points the same way as everything else here, and it is weak evidence,
and the deck says "n = 4, weak" on its face rather than letting the conclusion
travel further than the data.

### J11. The silicon MOSFET model is datasheet-*class* — **OPEN**

200 V / 24 mΩ, IRFB4227-class, not transcribed from the datasheet. The
qualitative Si-vs-GaN result does not depend on the third digit; the
quantitative one does. Flagged in `models/simosfet.lib` and in RUN-LOG.md.

### J12. The predrivers are behavioural — **STATED**

`segdrv_sky130.lib` has real output devices and behavioural predrivers with a
series output resistance. A real tapered buffer chain adds delay and its own
shoot-through window. The output stage is what J1 checks, and the model's own
header says this.

### J13. Two decks did not converge, and fixing them found something — **FIXED, and it produced J14**

`dpt_dcload_c.cir` and `dpt_sky130_c.cir` had never run, so the
behavioural-capacitance cross-check they exist for had never been performed.
RUN-LOG recorded that as a known limitation that "affects nothing that is
reported" — true, and it also meant nobody had ever checked whether the
capacitance formulation mattered.

Two causes, both real:

1. The capacitances were written `C={...}`, which asks ngspice to build the
   charge itself out of a capacitance that moves with the voltage it is
   solving for. Rewritten as `Q={...}` — the integral of the same law — they
   converge. The first attempt at that integral dropped the forward-bias
   branch, which makes the Miller capacitance vanish exactly when the device
   is on; `dpt_c.cir`, which had always run, stopped converging at 20 ps and
   said so. Caught by re-running all three rather than only the two that were
   broken.
2. ngspice realises a `Q=` capacitor as an internal subcircuit with its own
   node and branch, and under `uic` those have no DC path: *singular matrix,
   check nodes l.xhs.lcds#branch and xhs.cds_int1*. `rshunt=1e12` gives them
   one — three orders below the 1 GΩ off-switches already in the driver, and
   the same technique `dpt_sky130.cir` already used.

All three `_c` decks now run, and `scripts/capmodel_check.py` finally performs
the cross-check.

### J14. The sign of the headline fault depends on the capacitance law — **STATED, and it is the most useful thing found today**

With the cross-check working, the two formulations were compared:

| configuration | junction diodes | behavioural charge | difference |
|---|---|---|---|
| constant word, no clamp | **−0.249 V** | **+0.115 V** | +0.364 V |
| clamp on | +0.570 V | +0.800 V | +0.230 V |
| clamp + −2 V off-bias | +2.576 V | +2.710 V | +0.134 V |

The ordering holds under both — every change still buys what the project says
it buys. But **the constant-word row changes sign.** Diodes say false turn-on;
the charge form says it just survives.

The two are not the same law and never were. Under reverse bias, where the
victim sits during the crosstalk event, both give C0/(1+u)^m. Under forward
bias a SPICE diode applies its FC extrapolation above 0.5 V and keeps
climbing, while the behavioural form saturates at C0 — and the *aggressor* is
forward-biased through its own turn-on, so it gets a different C_GD, a
different slew rate, and different coupling.

So "the constant word causes false turn-on" is model-dependent and should be
said that way. It is not a measurement.

**And this is an argument for the design rather than against the result.** The
shipped configuration is safe under both laws with more than 2.5 V of room. It
is the only one of the three whose verdict survives changing a modelling
assumption underneath it — which is a better reason to build it than the
headline ratio.

### J15. Nine QA flags carried as "known-good" were six real defects — **FIXED**

The deck's geometry checker had reported nine flags for weeks, described in
HANDOFF.md as "the known-good baseline, all investigated false positives". Six
of them were not.

- **Four** full-width caption boxes ran under the page number. The text did
  not reach that far, so it looked fine; one caption a word longer would have
  printed over the slide number.
- **Two** were slide 34's body text box, 5.40 in tall, with the VCD
  screenshot laid over it from 4.05 in down. `build.py`'s own comment says
  that text was written to fit 2.45 in — the box was simply never resized. One
  added sentence from text under a picture.
- **Three** were genuine false positives: labels deliberately placed inside
  the signature panel on the title page.

Fixed in all three kinds, and generally rather than per-slide: `rebuild_pass.py`
now keeps text off the page number and out from under pictures as a final
pass, and `qa.py` knows that text inside a blank panel is a layout rather than
a collision. Extending `qa.py` to check all three output decks — it had only
ever checked the full one, never the file that actually goes on the projector
— immediately found a tenth defect nobody had seen, a caption overlapping a
figure by 0.07 in.

**All three decks now report zero.** The real lesson is the one in the
original note: a checker that cries wolf nine times is a checker nobody reads,
and the nine were dismissed as a batch because they always appeared as a
batch.



---

## Round 2 — what the second pass changed

Round 1 found thirteen things. Round 2 was run against the fixes, and the
pattern in what it found is worth naming: **every one of the new findings was
something that had been looked at before and filed as acceptable.** The nine
QA flags had a name — "the known-good baseline". The two non-converging decks
had a paragraph in RUN-LOG explaining why they did not matter. The soft-start
overshoot had a sentence on a slide owning it.

All three were wrong, and all three were wrong in the same way: the cost of
investigating was higher than the cost of writing down a reason not to, so a
reason got written down. The `_c` decks are the sharpest case — the paragraph
saying they affect nothing that is reported was true, and the thing they
existed to check had therefore never been checked, and when it finally was it
changed a headline claim from a measurement into a model-dependent one.

## Verdict

The project does what it says. The gaps it claims to close are closed and the
evidence is runnable. Two of the findings above changed a claim rather than a
word — the clamp is not the fix, and the loop needed a type-III compensator —
and both are now on slides.

What it is not is measured. Everything here is a simulation of a converter
that has never been built, and the right way to present it is as exactly that.
