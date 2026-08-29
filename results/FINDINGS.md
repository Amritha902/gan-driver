# Findings — nominal corner, 100 V / 10 A / 25 °C

720 control words, 0 convergence failures, 341 s on 4 cores.

All numbers below come from `results/sweep_nominal.csv`. Every claim that
required an interpretation was tested with a separate control run rather
than asserted from the trend.

## 1. The problem is real

| Configuration | Peak V_GS on the off device | Margin to V_th |
|---|---|---|
| Fastest driver, no clamp, 0 V off-bias | 1.65 V | **−0.25 V — false turn-on** |
| Miller clamp on, −2 V off-bias | −1.18 V | +2.58 V |

504 of 720 words (70%) are feasible, i.e. do not false-turn-on.

## 2. Pull-up and pull-down are not one knob

Drain overshoot moves by 0.0004 percentage points across the entire
pull-up range and by 8.6 points across the pull-down range. Overshoot
happens at turn-off; crosstalk on the opposite device is driven by this
device's turn-on dV/dt. They answer to different codes, which is why the
driver has separate pull-up and pull-down fields rather than one
"drive strength" number.

The pull-up code crosses into false turn-on between N_PU = 5 and 6.

## 3. Dead time and pull-down strength are coupled

This is the finding that justifies joint control.

At 5 ns dead time:

- `N_PD = 2`: overshoot 46.4%, E_off 1.78 µJ
- `N_PD = 8`: overshoot 22.5%, E_off 0.62 µJ

Same dead time, 2.9x the turn-off energy. Verified by a control run: at
`N_PD = 1` the overshoot is 25.8 % with 15 ns dead time but 17.6 % with
60 ns, while `N_PD` = 2..8 are identical at both. The apparent overshoot
minimum at `N_PD` = 3-4 is therefore a dead-time artefact at weak
pull-down, not an intrinsic property of the pull-down code.

**The minimum usable dead time is set by the pull-down code.** Choosing
the two independently — as a four-preset lookup table would — is wrong.

## 4. The GaN-specific trade, quantified

| Off-bias | Dead time | Crosstalk margin | E_dt |
|---|---|---|---|
| 0 V | 5 ns | -2.32 V | 0.33 µJ |
| 0 V | 35 ns | -0.80 V | 1.10 µJ |
| -2 V | 5 ns | -0.21 V | 0.40 µJ |
| -2 V | 35 ns | +1.08 V | 2.38 µJ |

At 35 ns, going from 0 V to −2 V off-bias buys **1.88 V of crosstalk
margin** and costs **1.28 µJ of third-quadrant conduction** — 0.68 µJ per
volt of margin. This coupling is specific to GaN: the reverse-conduction
drop is V_th + |V_GS,off| + I·R because there is no body diode. The SiC
literature this project builds on does not pay this cost.

Dead time buys crosstalk margin, but **the relationship saturates hard** and
a single slope is a misleading summary of it:

| Dead time | Mean margin | Marginal gain |
|---|---|---|
| 5 ns | −2.320 V | — |
| 10 ns | −0.974 V | **+269 mV/ns** |
| 15 ns | −0.816 V | +32 mV/ns |
| 25 ns | −0.798 V | +1.8 mV/ns |
| 35 ns | −0.797 V | +0.1 mV/ns |

**Essentially all the benefit arrives between 5 and 10 ns. Past about 15 ns,
dead time buys no margin at all and costs pure conduction loss.** That is the
actionable statement, and it also explains why total loss is minimised at
10-15 ns (Section 6).

(An earlier version of this document quoted "51 mV per ns", an endpoint slope
across 5-35 ns. An independent re-analysis in MATLAB produced 37 mV/ns from a
least-squares fit to the same data. Both are artefacts of forcing a straight
line through a saturating curve; the table above replaces them.)

## 5. Exchange rate along the Pareto front

Within the feasible region, the front trades **0.039 µJ of total loss per
percentage point of drain overshoot removed** — at a 100 V bus, 0.039 µJ
per volt. Seven words sit on the front.

## 6. Total loss has an optimum dead time

| Dead time | Mean total loss |
|---|---|
| 5 ns | 6.78 µJ |
| 10 ns | 5.89 µJ |
| 15 ns | 5.79 µJ |
| 25 ns | 6.18 µJ |
| 35 ns | 6.91 µJ |

Minimum at 10-15 ns. Shorter costs incomplete turn-off; longer costs
third-quadrant conduction.

## What this does not show

- Open loop. Nothing measures the ringing; this is scheduling, not adaptation.
- One corner only. The 36-point operating grid is not yet swept.
- Behavioural device and ideal driver switches. See README limitations.


---

# Part 2 — Real silicon: SKY130 transistor-level output stage

The ideal-switch slices were replaced with **real SKY130 5 V devices**
(`nfet_g5v0d10v5` / `pfet_g5v0d10v5`) from the open SkyWater PDK, simulated in
ngspice. No Cadence, no lab, no licence.

## 7. Why a 5 V-only driver — decided from data, not preference

| Configuration | Feasible words | Median margin |
|---|---|---|
| No clamp, 0 V off-bias | 36 / 180 | −0.44 V |
| **Clamp on, 0 V off-bias** | **180 / 180** | **+0.73 V** |
| Clamp on, −2 V off-bias | 180 / 180 | +2.73 V |

With the active Miller clamp, **every** control word is safe at 0 V off-bias.
So the negative supply can be dropped entirely, the rail is 0–5 V, and the
design fits a 5 V device. Cost of dropping it: median margin falls from
+2.73 V to +0.73 V. That is the trade, stated explicitly, and it removes a
whole power supply plus the dead-time conduction penalty of Finding 4.

## 8. Slice sizing, measured

| Device | W=100 µm, L=0.5 µm | For 8 Ω/slice |
|---|---|---|
| `nfet_g5v0d10v5` | 16.89 Ω | m=2 → 8.45 Ω |
| `pfet_g5v0d10v5` | 46.88 Ω | m=6 → 7.81 Ω |

PMOS is 2.78× weaker for equal width, so the pull-up bank is 3× the area of
the pull-down bank for equal strength. Total gate width ≈ 7.6 mm
(pull-up 4800 µm, pull-down 1600 µm, clamp 1200 µm).

## 9. The actuator is monotonic in real silicon

| Code | Pull-up | Pull-down | Ideal 8/N |
|---|---|---|---|
| 1 | 7.81 Ω | 8.45 Ω | 8.00 |
| 2 | 3.91 Ω | 4.22 Ω | 4.00 |
| 4 | 1.95 Ω | 2.11 Ω | 2.00 |
| 8 | 0.98 Ω | 1.06 Ω | 1.00 |

Monotonic in both banks, exactly 8:1 range, tracking the ideal target within
6 %. The behavioural model was a fair stand-in for DC drive strength.

## 10. RETRACTED — the transistor-level TRANSIENT is not converged

**An earlier version of this document claimed that with real devices the
dominant drain stress moves from the low-side turn-off to the high-side
turn-on, based on a 47 % whole-cycle overshoot. That claim is withdrawn. It
was numerical noise, not physics.**

What gave it away: at the reported peak, consecutive samples alternate
143.9, 66.5, 149.0, 66.2, 148.9, 65.4, 148.3, 64.7 and then return to 106.4,
with the timestep collapsed to ~4 ps. That is an oscillation about the true
value, not a transient.

## 11. Timestep convergence study — the decisive test

A real transient converges as the timestep shrinks. An artefact does not.
Simulated to 1.1 µs (covering turn-off at 1.00 µs and high-side turn-on at
1.03 µs), 30 ns dead time, all codes at 8:

| maxstep | ideal switches | SKY130 |
|---|---|---|
| 0.05 ns | 122.4 V | 149.0 V |
| 0.02 ns | 122.5 V | 147.5 V |
| 0.01 ns | 122.5 V | **452.1 V** |
| 0.005 ns | 122.5 V | did not complete |
| 0.002 ns | 122.5 V | did not complete |

The ideal-switch netlist is converged across a 25x timestep range — 122.5 V,
flat. **Every Part 1 result is therefore trustworthy.**

The SKY130 netlist does not converge at all. 452 V on a 200 V device is
physically impossible. No transient number from that netlist is reportable,
including the 17.3 % turn-off figure previously quoted in its favour.

Two attempted fixes failed: softening the logic edges from 0.1 ns to 2 ns
(realistic — no FPGA emits a 100 ps edge) and switching to Gear integration.
Both still diverge.

## 12. Where the instability actually is

Isolation test — the same SKY130 driver into a plain 360 pF load, no GaN
model, no half-bridge, no loop inductance:

| maxstep | peak v(out) | min v(out) |
|---|---|---|
| 0.05 ns | 5.010 V | −0.013 V |
| 0.02 ns | 5.011 V | −0.013 V |
| 0.01 ns | 5.016 V | −0.021 V |
| 0.005 ns | 5.019 V | −0.022 V |

**The driver is fine.** Converged across 10x in timestep, rails cleanly.

So the instability is in the **interaction between the BSIM4 devices and the
behavioural GaN model**, and the prime suspect is the diode-based C(V) trick:
`IS=1e-30, N=40` gives essentially zero conductance with a strongly nonlinear
capacitance. That was numerically harmless against ideal switches and is not
harmless against BSIM4.

Fix path, in order: replace the diode-based capacitances with an explicit
charge-based behavioural capacitor; failing that, add a small parallel
conductance across each; failing that, move to a proper Verilog-A GaN model.

**Status: the transistor-level output stage is built, sized and characterised
(Findings 8 and 9 stand — they are DC, and the isolation test above confirms
the driver transient is sound). Co-simulating it against the GaN half-bridge
does not yet produce numbers worth reporting.**

## Getting the tools

```bash
apt-get install ngspice
pip install numpy matplotlib
git clone --depth 1 --filter=blob:none --no-checkout \
    https://github.com/google/skywater-pdk-libs-sky130_fd_pr.git
cd skywater-pdk-libs-sky130_fd_pr
git sparse-checkout init --cone
git sparse-checkout set models cells/nfet_g5v0d10v5 cells/pfet_g5v0d10v5
git checkout          # 19 MB, not the ~1 GB full PDK
```

Three things had to be fixed before the transistor-level netlist converged,
all recorded in `sim/dpt_sky130.cir`: `rshunt=1e9` for the near-zero-conduction
GaN capacitance diodes, a real DC load operating point in place of `UIC`, and
a 20 Ω predriver output impedance so the slice gates are not driven from zero
ohms while the whole high-side driver slews 100 V.


---

# Part 3 — The 36-corner sweep, and a negative result on the core thesis

1,512 transients (42 candidate control words x 36 operating corners:
V_bus 50/100/150/200 V, I 2/5/10 A, T_j 25/75/125 C). One convergence
failure. Ideal-switch netlist, the one verified converged.

## 13. The schedule LUT exists, but it barely moves

Across 36 corners the cost-optimal control word takes only **4 distinct
values**, and one of them covers 19 corners:

| Word (PU/PD/PDHS/DT/CLK/VNEG) | Corners |
|---|---|
| `8/8/1/15n/1/+0` | 19 |
| `8/8/8/5n/1/+0` | 12 |
| `8/2/8/5n/1/+0` | 4 |
| `4/2/8/10n/0/+0` | 1 |

## 14. Operating-point scheduling is NOT worth the FPGA

This is the finding that matters, and it contradicts the project's own
framing.

| | Mean cost |
|---|---|
| Best single fixed word, applied at every corner | 5.551 |
| Per-corner scheduling (the LUT) | 5.443 |
| **Scheduling buys** | **2.0 %** |

It is robust to the cost function. Sweeping the overshoot weight from 0 to
1.0 uJ per point gives a scheduling gain of 0.9 %, 3.1 %, 2.0 %, 1.5 %,
2.0 %, 4.9 %, 8.4 % — only an extreme overshoot weighting gets past 5 %.

It is not rescued by feasibility: **34 of 42 candidate words are feasible at
all 36 corners**, so no word is forced by the operating grid.

It is not rescued by margin either. The best fixed word for worst-case
crosstalk margin reaches **+2.60 V**, which is *exactly* what per-corner
scheduling achieves. Scheduling buys zero margin.

**A single fixed control word is as good as the schedule.** The
"operating-point-adaptive" premise is not supported by our own data.

## 15. What does pay: the active Miller clamp

| | Result |
|---|---|
| Mean cost advantage of clamping over not clamping | **14.7 %** |
| Scheduling advantage over a fixed word | 2.0 % |

The clamp is worth roughly **seven times** what scheduling is worth, and it
is a static architecture choice requiring no FPGA at all. It appears in the
optimal word at 35 of 36 corners.

The corner data also exposes two distinct viable design points, which is a
better contribution than the schedule was going to be:

| Design point | Worst-case margin | Character |
|---|---|---|
| Clamp on, 0 V off-bias | +0.29 V | cheap, adequate, fast words |
| Clamp off, −2 V off-bias | +2.60 V | expensive, very safe, slow words |

## 16. What this means for the project

Say this plainly rather than letting a reviewer find it:

- The **actuator** is real, built, and characterised. That stands.
- The **trade-offs are quantified**. That stands.
- The **scheduling thesis does not survive contact with the data.** A fixed
  word is within 2 %.
- The **Miller clamp is where the benefit lives**, at 14.7 %.

The honest reframing is to drop "operating-point-adaptive" from the title
and report the scheduling result as a negative finding: *we tested whether
per-corner scheduling pays, and it does not, because the active Miller clamp
captures nearly all the available benefit statically.* That is a real result
and more useful than a marginal positive one.

### Caveat on the method

The 42 candidate words were selected at the nominal corner. A full per-corner
sweep might find corner-specific words that widen the gap. The comparison is
apples-to-apples (fixed and scheduled both drawn from the same candidate set),
but the ceiling on scheduling has not been established — only that it is low
for a candidate set chosen this way. Establishing it properly means a full
720-word sweep at several corners. (An earlier version of this note estimated
that at ~6 hours of compute. That was wrong by an order of magnitude: the
720-word sweep takes 341 s, so three extra corners is about 17 minutes. The
sweep was run -- see section 17.)


## 17. The ceiling on scheduling, established

2,160 transients, zero failures, 1,044 s. The **full 720-word sweep** was run
at three extreme corners; combined with the nominal corner's existing full
sweep that gives four corners where the per-corner optimum is the TRUE
optimum, not the best of a pre-selected candidate list.

| Corner | True optimum (PU/PD/PDHS/DT/CLK/VNEG) | Cost | Margin |
|---|---|---|---|
| 100 V / 10 A / 25 °C | `8/8/8/5n/1/+0` | 5.047 | +0.50 V |
| 200 V / 10 A / 125 °C | `8/8/8/5n/1/+0` | 12.699 | +0.24 V |
| 200 V / 2 A / 125 °C | `8/2/1/5n/1/−2` | 6.858 | +1.58 V |
| 50 V / 2 A / 25 °C | `8/2/8/15n/1/+0` | 0.858 | +0.85 V |

474 of 720 words are feasible at all four corners. Best fixed word:
`8/8/1/25n/1/+0`, mean cost 6.712 against 6.365 for per-corner optimisation.

**Ceiling on scheduling: 5.2 %** at the stated cost weight; 2.1 – 8.5 % across
weights from 0 to 1.0.

This is 2.6x the 2.0 % measured with the restricted candidate set, so the
caveat in section 16 was justified — the restricted set did understate it.
The conclusion is unchanged in kind: scheduling buys single-digit percent.

### But the gain is NOT uniform, and that is the useful part

| Corner | Penalty for using the fixed word |
|---|---|
| 100 V / 10 A / 25 °C | 1.1 % |
| 200 V / 10 A / 125 °C | 2.3 % |
| 50 V / 2 A / 25 °C | 3.8 % |
| **200 V / 2 A / 125 °C** | **12.7 %** |

Three corners barely care. One cares a lot — and the reason is specific:
**at high voltage, light load and hot, the optimum switches to negative
off-bias** (`VNEG = −2`), which no other corner's optimum uses. At that
corner the best word with −2 V costs 6.86 against 7.51 for the best word at
0 V, a 9 % difference.

### The design conclusion

The thing worth scheduling is **not** drive strength and **not** dead time.
It is the **off-bias rail** — a one-bit decision.

That is a much simpler machine than this project proposed. It does not need a
16-bit control word, a 36-entry LUT, or an FPGA. It needs a comparator on bus
voltage and load current selecting between two gate-drive rails. The
segmented driver still earns its place as the actuator that made the
trade-offs measurable, but the *scheduling* contribution collapses to one bit.

Report it that way. "We built the full 16-bit scheduled actuator, measured
what scheduling can possibly buy, and found it collapses to a single off-bias
bit at extreme corners" is a stronger and more honest result than a 5 %
average dressed up as adaptation.


---

# Part 4 — The convergence failure, localised and partly solved

Branch `gan-convergence-fix`.

## 18. Four fixes on the wrong suspect

FINDINGS 12 blamed the GaN model's diode-based capacitances. Two more fixes
were tried on that basis and **both failed**:

- Behavioural capacitors instead of diode C(V): made it *worse* (died at
  t = 0.1 ns instead of running-but-unconverged).
- 100 MΩ parallel conductance across each cap-diode: **no effect whatsoever**
  — 149.0 / 147.5 / 452.3 V, numerically identical to the original.

The second result is the informative one. If ill-conditioning at those nodes
were the cause, a parallel conductance would have changed *something*. It
changed nothing, so the diagnosis in section 12 was wrong.

## 19. Bisection finds it in one step

Instead of guessing again, the circuit was bisected: one driver SKY130, the
other ideal, and vice versa.

| Which driver is SKY130 | 0.05 ns | 0.02 ns | 0.01 ns | |
|---|---|---|---|---|
| **Low side** (ground-referenced) | 117.3 V | 117.3 V | 117.3 V | converged |
| **High side** (floating on SW) | 150.0 V | 146.5 V | 474.0 V | diverges |

**The floating high-side driver is the sole cause.** Not the GaN model, not
BSIM4 in general, not the capacitance implementation. Its supply rails are
ideal sources riding a node that slews 100 V in about 2 ns, so every device
capacitance referenced to those rails is driven from zero impedance.

Replacing them with a bootstrap capacitor and finite source resistance —
which is what a real high-side supply is — did not work either (the runs die
almost immediately, most likely a capacitor-initialisation problem that was
not chased further). That is fix attempt five. It is recorded as open.

## 20. What this salvages: a converged transistor-level result

The low-side hybrid — **real SKY130 transistors on the switching device**,
behavioural high-side — is converged:

| maxstep | 0.1 ns | 0.05 ns | 0.02 ns | 0.01 ns | 0.005 ns |
|---|---|---|---|---|---|
| peak V_DS | 117.3 V | 117.3 V | 117.3 V | 117.3 V | 117.3 V |

Spread 0.05 V across a **20x** timestep range: 0.04 %. This is the project's
first trustworthy transistor-level transient, and it covers the device that
actually matters for turn-off energy and overshoot.

### What real silicon changes

| | Ideal switches | SKY130 low side |
|---|---|---|
| Turn-off overshoot | 22.4 % | **17.3 %** |
| Turn-off energy | 0.63 µJ | **0.71 µJ** (+13 %) |
| Crosstalk peak | 1.65 V | **1.39 V** |

Slower edge, less L·di/dt overshoot, more overlap loss. Exactly what a
current-limited device should do, and it is the trade the ideal resistor
model cannot show.

## 21. A caveat this forces on the headline result

**The crosstalk peak falls from 1.65 V to 1.39 V against a 1.40 V threshold.**

The headline "false turn-on" was computed with ideal switches. With real
low-side silicon the baseline sits *at* the threshold — nominally passing by
0.01 V, which is 0.7 % and therefore meaningless either way. The honest
statement is that the baseline is **marginal**, not that it definitively
fails.

What is unaffected: the clamp still takes it to 0.71 V, an unambiguous
margin, and that is the result the project rests on. But the baseline should
be described as "at or below the threshold depending on driver model" rather
than "false turn-on", and the driver-model sensitivity should be stated.


## 22. Bootstrap rails: attempted, failed, and a process error worth recording

Five high-side rail variants were tested against the timestep-convergence
criterion (window 1.05 us, covering the turn-off):

| Rail model | 0.05 ns | 0.02 ns | 0.01 ns |
|---|---|---|---|
| Ideal sources (reference) | 149.0 | 147.5 | 452.1 |
| Series R 0.5 Ω | 150.9 | 149.0 | did not complete |
| Series R 5 Ω | 153.1 | 149.1 | did not complete |
| R 0.5 Ω + C 1 nF | 149.2 | 153.0 | 401.6 |
| R 0.5 Ω + L 1 nH | 148.8 | 150.5 | 189.4 |

**None converge.** Giving the floating rails finite impedance does not fix
it, so the mechanism is not simply that they are ideal voltage sources. The
last untested element in the floating path is the ideal level-shifter
B-sources feeding the high-side logic; that is where to look next.

Six fix attempts are now on record for this one failure: rshunt, DC-load
operating point, predriver output impedance, softened logic edges, Gear
integration, behavioural capacitors, parallel conductance, and five rail
variants. The honest summary is that the floating transistor-level driver is
**unresolved**, and the low-side hybrid (section 20) is the usable result.

### A process error, recorded because it nearly produced a false claim

Midway through this work a direct run of the bootstrap netlist appeared to
complete 3 us successfully with sane numbers. It had not. The `out.dat` being
read was **stale** — written at 03:41 by an earlier run of a different
netlist, while the bootstrap netlist was created at 14:04. The mismatch was
only caught by checking file modification times against the netlist.

The sweep harness writes each run into its own temporary directory precisely
to avoid this, and the harness result (failure at 1.000 us) was correct all
along. The lesson is specific: **when running a simulator by hand in a shared
directory, verify the output file is newer than the input**, or the previous
run's results will be read as the current run's.


## 23. CORRECTION — the transient converges; the metric did not

Sections 10-12 and 18-22 state that the SKY130 transistor-level transient
"does not converge". **That is too strong and is corrected here.** The
convergence test was run on peak V_DS, which is the least robust statistic
available: one bad sample moves it by hundreds of volts.

Re-run on an integral instead:

| Netlist | E_off @ 0.05 ns | @ 0.02 ns | @ 0.01 ns | spread |
|---|---|---|---|---|
| Ideal switches | 0.661 µJ | 0.660 | 0.660 | 0.1 % |
| **SKY130, both drivers** | **0.737 µJ** | **0.737** | **0.750** | **1.8 %** |

**The energy metrics are converged.** E_on, E_off and E_dt from the full
transistor-level netlist are reportable, and they show real silicon costing
about 12 % more turn-off energy than ideal resistors (0.74 vs 0.66 µJ).

### What is still not reportable, and why

The voltage waveform is a different matter. At maxstep = 0.01 ns a ~450 V
excursion appears that is absent at coarser steps. It is **not** an isolated
spike: it survives a 5-sample median filter (452.0 V) and even the 99.5th
percentile (450.9 V), so more than 0.5 % of samples are up there.

That it appears only at one step size means it is numerical, not physical.
And it explains how energy can converge while voltage does not: the excursion
occurs when the current is near zero, so it contributes almost nothing to
∫v·i even though it dominates max(v).

### Revised standing

| Quantity | Source | Status |
|---|---|---|
| Transistor-level E_on / E_off / E_dt | full SKY130 netlist | **reportable**, 1.8 % |
| Transistor-level peak V_DS | full SKY130 netlist | not reportable |
| Transistor-level peak V_DS | low-side hybrid (§20) | **reportable**, 0.04 % |
| All Part 1 results | ideal-switch netlist | reportable, 0.1 % |

### The lesson, which is worth more than the fix

Six fix attempts — rshunt, DC-load operating point, predriver impedance,
softened edges, Gear, behavioural capacitors, parallel conductance, five rail
variants, level-shifter RC, smoothed comparisons — were spent trying to make
a **statistic** converge that was never going to, because it was the wrong
statistic. The solver was doing its job the whole time.

**Choose a convergence metric that is robust before concluding a simulation
has failed.** Integrals converge; peaks of a noisy signal do not.

## 24. The convergence criterion earns its keep a second time

Section 23 established the rule the hard way: on a ringing node, **integrals
converge with timestep refinement and peaks do not**. That rule was derived
while chasing a high-side result and it cost six wasted fixes to find. This
section is the first time it was applied *before* a number went into the paper
rather than after, and it caught one.

**The setting.** The freeze test (§17) says pull-up drive strength is worth
0.00 % to schedule. That contradicts the active-gate-driver literature, which
schedules drive strength precisely for EMI — a quantity our cost function
never prices. So the claim needed a bound: does pull-up move the EMI measures,
even though it does not move the cost?

`scripts/emi_check.py` measured it. First attempt windowed the **turn-off**
event, which pull-up does not govern — invalid, thrown away. Re-measured at
turn-on, `T4 = T3 + DT`, the window tracking DT rather than pinned to a fixed
time. Two measures came out:

| N_PU | turn-on ringing energy (30–500 MHz) | peak dV/dt |
|---|---|---|
| 1 | 46.0 | 89.6 V/ns |
| 8 | 20.2 | 126.9 V/ns |
| **span** | **128 %** | **42 %** |

Both went into the paper. Then the rule from §23 was applied: *peak dV/dt is a
peak of a ringing node.*

**The check.** `scripts/emi_converge.py` refines the print step and the maximum
internal step together over a 25× span. Both matter — the print step sets the
sample spacing the gradient and the FFT actually see, the max step sets solver
accuracy — and refining only one would not have settled anything.

| tstep / tmax | E_osc_on | dvdt_pk | dvdt_1090 |
|---|---|---|---|
| 0.05n / 0.125n | 20.69 | 118.17 | 27.89 |
| 0.02n / 0.05n (nominal) | 20.20 | 126.92 | 27.99 |
| 0.01n / 0.025n | 20.08 | 128.69 | 28.02 |
| 0.005n / 0.0125n | 20.13 | 129.10 | 28.03 |
| 0.002n / 0.005n | 20.21 | **159.89** | 28.03 |
| **spread vs finest** | **3.0 %** | **26.1 %** | **0.5 %** |

Peak dV/dt drifts 26 % and is *still climbing* at the finest step — it is
chasing an ever-sharper numerical edge, exactly as §23 predicts. The band
energy (an integral) holds to 3.0 %. The 10–90 % slew (an interval measure)
holds to **0.5 %**.

**The correction, and why it matters more than a tidier number.** Re-measured
on the convergent metric:

| N_PU | turn-on ringing energy | 10–90 % slew |
|---|---|---|
| 1 | 46.0 | 12.5 V/ns |
| 2 | 35.4 | 19.1 V/ns |
| 3 | 29.4 | 21.9 V/ns |
| 4 | 26.0 | 23.8 V/ns |
| 6 | 22.2 | 26.3 V/ns |
| 8 | 20.2 | 28.0 V/ns |
| **span** | **128 %** | **123 %** |

The non-convergent measure reported 42 % where the convergent one reports
**123 %** — it understated the effect **three-fold**. So the correction makes
the finding *stronger*, not weaker. That is worth stating plainly, because the
temptation with a convergence check is to run it only when a result looks too
good; here it was run on a result that looked fine and the unconverged number
was the conservative one. A metric that does not converge is not merely noisy
in a direction that flatters you.

**What it establishes.** Both convergent EMI measures span >120 % across the
pull-up range, and they move in **opposite directions**: the fastest pull-up
gives the highest slew rate but the *lowest* ringing energy — faster
commutation spends less time in the resonant region. "EMI" is not one
quantity. The 0.00 % scheduling value of pull-up is therefore scoped to a
loss-and-overshoot objective, and a design bound by conducted emissions could
land elsewhere. `scripts/emi_sweep.py` and `scripts/emi_analyse.py` are
written to settle that by re-running the full 720-word search with the EMI
measures recorded and recomputing the ceiling under
`cost = (1−α)·loss + α·EMI`; they are queued behind the robustness study,
which is holding all four cores.

**Process note.** `robust.py` accumulates all 15 840 rows in memory and writes
the CSV only at the end, so a crash at row 15 000 loses the whole run.
`emi_sweep.py` checkpoints to a `.part` file every 500 points. The robustness
run was already an hour in when this was noticed and killing it to add a
checkpoint would have cost more than the risk; the fix went into the new
script instead.

## 25. Audit: every number in the paper traced to the script that makes it

After §24 caught a bad metric, the obvious next question was whether anything
else in the manuscript was quoted rather than produced. Every numeric claim
was re-derived from the scripts. Most held exactly. Three did not.

### What held

| Claim | Script | Verdict |
|---|---|---|
| Ceiling 5.2 %; per-corner 1.1 / 2.3 / 3.8 / 12.7 % | `ceiling.py` | exact |
| Cost-weight range 2.1 – 8.5 % | `ceiling.py` swept | exact |
| Freeze test, all six fields, both guard bands | `whichbit.py` | exact |
| Guard-band table, all six rows and their fixed words | `guardband.py` | exact |
| Grid-density 0.00 / 3.99 / 4.65 / 5.17 %, hardest pair 11.49 % | `scaling.py` | exact |

### Finding 1 — the price of crosstalk safety was 8× too high

The paper said **0.30 %** in three places. No script produced it. It is
**0.04 %**.

The mechanism is worth recording because it is not a typo. At 100 V / 10 A /
25 °C the energy-optimal word costs 3.3338 µJ and the cheapest feasible word
3.3350 µJ. Printed to two decimal places those are 3.34 and 3.33 — which reads
as a gap of about 0.3 %. The rounded display, not the data, produced the
number, and it then propagated into the abstract and the figure caption.

Two further points, both uncomfortable:

- The correction makes the paper's claim **stronger** (safety is 8× cheaper
  than stated). A number that flatters your argument is the one you are least
  likely to check. This one survived several passes for exactly that reason.
- On the **blended cost** the price is **0.00 %**, because the infeasible
  word's switching-energy advantage is spent again in dead-time loss. Both
  numbers are true; the paper now quotes the larger one and says why.

`scripts/safety_price.py` computes both metrics at all four corners.

### Finding 2 — the clamp's value was one pick from a 2.5-point spread

The paper said the Miller clamp is worth **10.3 %**. Also unsourced. It is
reproducible, but only under one of four defensible definitions:

| baseline | averaging | value |
|---|---|---|
| best fixed word | % of the means | 9.74 % |
| best fixed word | mean of the %s | 12.22 % |
| per-corner optimum | % of the means | 11.92 % |
| **per-corner optimum** | **mean of the %s** | **10.26 %** |

Neither choice is obviously right, and the answer moves 2.5 points between
them. The paper now reports **9.7 – 12.2 %**, the way it already reports the
cost-weight sensitivity as a range. The claim that survives all four — the
clamp is worth roughly a tenth of the cost, about twice what scheduling is
worth, from a static choice needing no controller — is the one worth making.
`scripts/clampvalue.py` prints all four.

### Finding 3 — a script that hardcoded its own result

`decompose.py` printed `price of crosstalk safety ...... 0%` as a **string
literal**, not a computation. It happened to be right on the blended cost and
wrong on switching energy. It now computes both. A script that prints a
constant is worse than no script: it looks like corroboration.

### Two figures existed and were in no draft

`paper_fig2_ceiling.png` and `paper_fig3_offbias.png` were generated, shipped
in the handover folder, and referenced by nothing. Figure 3's title still read
*"Where the one bit that matters shows up"* — the off-bias claim that §17's
freeze test corrected to dead time. It was retitled, and its caption now says
the effect it shows is real but the inference drawn from it was wrong. A hash
check now confirms figure N in the paper is `paper_figN` on disk; before this
audit, the paper's "Figure 2" was `paper_fig4` and nobody would have noticed.

### The generalisation

Of the three bad numbers, none came from a wrong simulation. One came from
rounding, one from an undeclared choice among four averaging conventions, and
one from a `print` statement. The simulations were never the weak link. **The
weak link was every number that reached the manuscript without a script behind
it** — so every number in the paper now has one, and `ceiling.py`,
`scaling.py`, `robust_analyse.py` and `emi_analyse.py` were checked to be
using the same denominator (`/fixed`) so their percentages mean the same thing.
`emi_analyse.py` was not, and was fixed.

## 26. The rule, tested against the paper's own headline metrics

Section 24's rule — on a ringing node, integrals converge and peaks do not —
has an uncomfortable consequence that had to be faced rather than assumed
away. The cost function is

    cost = E_tot + w_ov · ov_pct        ov_pct is a PEAK of V_DS
    feasible ⟺ margin > 0               margin = V_th − Vgs_spur, also a PEAK

Both quantities every headline rests on are peaks. If they drift the way peak
dV/dt does, the 5.2 % ceiling, the freeze test and the guard-band table all
inherit that drift. `scripts/metric_converge.py` refines the timestep 25× on
the ideal-switch deck, at two words: the one the ceiling result selects, and
the marginal word (no clamp, fastest drive) where a false-turn-on verdict is
decided by tenths of a volt.

| Quantity | Selected word | Marginal word | Absolute drift |
|---|---|---|---|
| E_tot | 0.70 % | 0.74 % | — |
| E_off | 0.31 % | 0.49 % | — |
| Drain overshoot `ov_pct` | 1.14 % | 1.06 % | 0.24 V |
| Spurious gate peak `Vgs_spur` | 0.04 % | 0.32 % | **0.005 V** |
| Crosstalk margin | 0.14 % | 2.11 % | **0.005 V** |

**They converge.** The margin's 2.11 % is an artefact of expressing a small
difference of two larger numbers as a percentage — in volts it drifts by
0.005 V, against the 0.36 V and 1 V scales this project works at. Reporting
only the percentage there would have manufactured a problem that does not
exist, which is the mirror image of the §24 error.

### What the rule actually says

Not *peak versus integral*. **Whether the peak is of a ringing signal.**

| Measure | What it is a peak of | Converges? |
|---|---|---|
| `ov_pct` | first and largest excursion after turn-off | yes, 1.1 % |
| `Vgs_spur` | a single capacitively-coupled hump | yes, 0.04 % |
| `dvdt_pk` | a slew rate on the ringing edge | **no, 26 %** |
| SKY130 peak V_DS (§23) | a resonant tail | **no** |

The two that fail are measured *on* the resonance; the two that pass are
measured on a single, physically-located excursion. That is the distinction,
and it is now stated in the paper as Table I rather than left as a rule of
thumb derived from one bad experience.

### One more thing worth recording

At the finest step (0.002 ns print / 0.005 ns max) the spurious gate peak
reads **1.6486 V**. The project's very first result — the one that motivated
the whole thing — was **1.65 V** against a 1.4 V threshold. It reproduces at a
25× finer timestep than it was originally measured. The false-turn-on finding
was never in doubt; it is good to have that on the record rather than assumed.
