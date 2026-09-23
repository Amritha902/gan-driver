# Methodology — what we did, in the order we did it

Every number here regenerates from `results/RESULTS-SUMMARY.txt`, which names
the script that produces it. Nothing in this document is quoted from memory;
where a figure is uncertain or a run failed, it says so.

---

## 0. The question

Segmented gate drivers let drive strength be chosen digitally per operating
point instead of fixed by a resistor. The literature reports gains from doing
so. **Nobody reports how much of that gain needs the adaptation and how much
one well-chosen fixed setting would have delivered anyway.** That gap is the
project.

---

## 1. Build the converter, and check it converts

`sim/buck.cir` — 100 V → 50 V synchronous buck, 500 kHz, 22 µH / 4.7 µF
output filter, 3 nH power-loop inductance, damped bus decoupling.

Verified: 100.0 V and 2.426 A in, 48.56 V and 4.876 A out — **97.70 %
efficient**. Measured over the last 20 of 150 whole cycles by trapezoidal
integration, not by averaging samples.

> *Why that matters:* an early version used `numpy.mean()` over ngspice's
> adaptive timestep and reported **107.8 % efficiency**. Densely-sampled fast
> regions were over-weighted. Time-weighted integration fixed it. The bug is
> recorded rather than quietly removed.

## 2. Reproduce the fault

Double-pulse test, `sim/dpt.cir`. Fastest drive word, no clamp: the OFF
device's gate reaches **1.65 V against a 1.4 V threshold** — margin
**−0.249 V**. That is a shoot-through, and it is why a GaN half-bridge is
harder to build than a silicon one.

**Definition that matters:** margin is the threshold minus the highest the off
gate reaches *while the other device is conducting*. Measuring across the
whole cycle instead reports the drive rail every time and hides the failure.
This is not pedantry — it is how the 200 V defect in §8 stayed invisible.

## 3. Fix it one change at a time

| configuration | off-gate peak | margin |
|---|---|---|
| fastest word, no clamp | 1.65 V | **−0.249 V** |
| + active Miller clamp | 0.83 V | +0.57 V |
| + −2 V off rail | −1.176 V | **+2.576 V** |

One change per run, so each is attributable. Clamp +0.82 V, negative rail a
further +2.01 V.

## 4. Implement the base paper, don't just cite it

`models/zhangdrv.lib` — Zhang *et al.*, ISPSD 2020: seven slices per bank in
two stages, the split set by one external bias resistor. **No clamp, no
negative rail** — their absence *is* the comparison.

Drawn as a schematic too (`kicad/gan_zhangdrv.kicad_sch`, 70 components) so
the reimplementation can be checked against the model line by line.

**Stated, not hidden:** the ISPSD paper is four pages and gives no slice
sizing. Equal slices and an nseg/(7−nseg) split are our inference. Both are
the most generous simple reading of "pattern control", so neither favours us.

## 5. Search the whole control-word space

Six fields — pull-up and pull-down strength for each side, dead time, clamp
enable, off-rail select — giving **720 distinct control words**.

Run at **36 operating points** (bus × load × junction temperature).

- 36 × 720 = 25,920 intended
- **25,911 rows produced a measurement**
- **9 runs produced none** and are reported rather than back-filled

Across all studies: **66,924 transient simulations**, derived by
`scripts/count_transients.py` from the result files. *(This number was wrong —
the deck said 60,533 for six weeks. See §10.)*

## 6. Decompose the gain — the main result

| | share of baseline |
|---|---|
| (A) choosing a better **fixed** word | **26.5 %** |
| (B) **adapting** it per operating point | **2.6 %** |
| (B) as a fraction of total gain | **8.9 %** |
| ceiling on any scheduling scheme | 3.5 % |

Then a **complexity ladder** — how much of (B) each rung of hardware buys:

| rung | captures | left to justify more |
|---|---|---|
| constant word | — | 2.6 % |
| + one comparator (load current at 10 A) | 47 % of (B) | **4.7 %** of total |
| + two comparators | 61 % of (B) | **3.4 %** of total |
| full sense + ADC + LUT | 100 % | — |

**Leave-one-corner-out returns the identical word on 36 of 36 corners.** The
fixed word is not overfitted to the grid that chose it.

**Which field carries it:** clamp worth 9.7–12.2 %; dead time frozen costs
5.45 % (0.00 % without the light-load corner); **pull-up drive strength frozen
costs 0.00 %** — the field everyone builds is the one free to freeze.

## 7. Test the conclusion against what would break it

- **Device spread** — 24 devices, Vth/transconductance/Cgs/Cj varied jointly:
  worst margin **+1.895 V**, 0 of 24 false turn-on.
- **Capacitance law** — behavioural `C=` vs charge-based `Q=`: ordering
  survives; **the sign of the no-clamp row does not.** Stated as a limit.
- **Transistor level** — SKY130 open PDK output stage: sign and ordering both
  survive. But the clamp's *own* contribution falls to +0.03 V there, so the
  ordering survives and the attribution does not.
- **Loop inductance** — 3 nH is our choice and the conclusion is sensitive to
  it. Listed as a threat, not a result.

## 8. Sweep the converter across the envelope it claims

8 bus × load points. Off-gate margin **positive at every point, +2.14 V at
worst**.

The two 200 V points exceed the device's 200 V rating — **not a driver
failure**: their overshoot is the *smallest* in the sweep (3.1 %, 4.1 %). A
200 V-rated part cannot run a 200 V bus, because any overshoot then exceeds
the rating. **Envelope corrected to 50–150 V on this device.**

> *How this was found:* the first 200 V run shoot-throughed — 464 V peak,
> low-side gate at +11.78 V, **112 A through a 10 A load**. Cause was a bus
> decoupling branch *we had added ourselves* to cure a different problem, left
> undamped: a series L-C with Q ≈ 3.5 near 22 MHz that the switching edges
> pumped once a cycle. `Rdec` 20 mΩ → 1 Ω fixed it and improved every metric
> at 100 V as well. `sim/dpt.cir` never showed it because the double-pulse
> deck has no decoupling network at all.

## 9. Make the two halves meet

`rtl/seg_gate_ctrl.v` — real RTL, 8 properties verified in Icarus Verilog,
synthesised in **Vivado 2024.1 on xc7a35tcpg236-1: 20 LUTs, 20 flip-flops,
200 MHz register-to-register met with 1.996 ns slack.**

The RTL's VCD output drives the SPICE slices directly in co-simulation; the
two **agree to 0.081 V**.

**Said plainly:** the same Vivado report contains the line *"Timing
constraints are not met"* — 34 register-to-output-pin paths against a
placeholder 4 ns constraint, pre-placement, with placeholder pin assignments.
The logic meets 200 MHz; the I/O paths are unconstrained until place-and-route.

## 10. Audit the process itself

Run 23 September. Two defects, one in the data and one in the method meant to
catch it:

1. **The transient count was stale.** Deck said 60,533; true figure 66,924.
   Correct when typed, wrong the moment three new studies were added.
2. **The check that guarded it could not fail.** `check_consistency.py`
   verified that the *string* "60533" appeared in two files. Text agreeing
   with text is not either agreeing with the data. Worse, a number absent from
   *both* passed silently.

Fixed: `scripts/count_transients.py` derives the count from the CSVs; the
check reads it and **absence is now a failure**. Verified both directions — a
wrong count fails, the right one passes.

---

## What this methodology does not cover

**No hardware has been measured.** Everything above is simulation, one
behavioural GaN model underlies all of it, and the sign of the headline fault
is model-dependent. The title says simulation study and the completion
accounting says 90 %.
