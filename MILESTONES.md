# Milestones

Two tracks run in parallel after M0. Cadence produces a characterisation table; Vivado
consumes it. They never co-simulate.

**Exit criterion** is what must be true to move on. Do not start the next milestone until
it holds.

---

## M0 — Feasibility gate (2 days) — BLOCKING

Nothing else is worth building until this passes.

| # | Task | Output |
|---|---|---|
| 0.1 | Obtain a GaN HEMT model Spectre will parse. Try in order: GaN Systems GS66508B, EPC2010, Navitas. If none parse, build Verilog-A ASM-HEMT | `cadence/models/` |
| 0.2 | Run `cadence/dpt_gan.scs` — clamped inductive double-pulse test | V_DS and I_D waveforms |
| 0.3 | Confirm the waveform shows real turn-off overshoot and ring-down, not a convergence artefact | screenshot + notes |

**Exit criterion:** a double-pulse test converges and produces physically plausible
overshoot at 400 V / 10 A.

**If it fails:** stop. Report to Dr. Bindu. The Project-I transposed-convolution topic is
still available and already has a survey.

---

## M1 — Segmented driver in Cadence (2 weeks)

| # | Task | Output |
|---|---|---|
| 1.1 | N parallel pull-up / pull-down slices under an N-bit enable word | schematic |
| 1.2 | Miller clamp with programmable turn-on instant | schematic |
| 1.3 | Verify each strength code monotonically changes dV/dt | sweep plot |
| 1.4 | Parameterise N (start N=4, confirm 8 is buildable) | — |

**Exit criterion:** strength code 0..2^N-1 produces monotonic, non-overlapping dV/dt.

---

## M2 — Characterisation sweep (2 weeks)

The output of this milestone is the single artefact the whole Vivado track depends on.

| # | Task | Output |
|---|---|---|
| 2.1 | Define the grid: V_DC × I_load × T_j × strength × dead-time × clamp-delay | `scripts/grid.py` |
| 2.2 | Batch-run Spectre over the grid | raw logs |
| 2.3 | Extract per point: V_GS peak, V_GS undershoot, V_DS overshoot, E_on, E_off, crosstalk margin, t_commutation | `data/characterisation.csv` |
| 2.4 | Sanity-check: does optimal dead-time actually shift with strength? | plot |

**Exit criterion:** `data/characterisation.csv` complete, no NaNs, monotonic where expected.

**2.4 is RQ2 and it is the scientific core of the project.** If dead-time optimum does
*not* move with drive strength, novelty claim N1 is weak — report it and say so early.

---

## M3 — Pareto extraction (1 week)

| # | Task | Output |
|---|---|---|
| 3.1 | Per operating region, compute the non-dominated set over (V_DS overshoot, E_sw, crosstalk margin) | `scripts/pareto.py` |
| 3.2 | Quantise the front to a fixed number of points per region | `data/pareto_table.mem` |
| 3.3 | Report front size vs. region count — this sizes the BRAM | table |

**Exit criterion:** `pareto_table.mem` loads with `$readmemh` and is under the BRAM budget.

---

## M4 — RTL policy engine (3 weeks) — can start during M1

Unblocked by M0; does not wait for the CSV. Use a synthetic table until M3 delivers.

| # | Task | Output |
|---|---|---|
| 4.1 | Operating-point quantiser | `rtl/quantiser.v` |
| 4.2 | Pareto table + BRAM inference | `rtl/pareto_table.v` |
| 4.3 | Mode arbiter (runtime objective weight) | `rtl/mode_arbiter.v` |
| 4.4 | Interpolator + hysteresis guard | `rtl/interp_hyst.v` |
| 4.5 | Top level tying 4.1–4.4 | `rtl/policy_engine.v` |

**Exit criterion:** simulates clean, no limit-cycling when the operating point sits on a
region boundary.

---

## M5 — Edge timing (2 weeks)

| # | Task | Output |
|---|---|---|
| 5.1 | PWM modulator with programmable dead-time | `rtl/pwm_deadtime.v` |
| 5.2 | Sub-ns edge placement via `OSERDESE2` 8:1 DDR @ 200 MHz | `rtl/fine_timing.v` |
| 5.3 | Segment enable encoder | `rtl/seg_encoder.v` |
| 5.4 | Measure achieved resolution on hardware or in timing sim | report |

**Exit criterion:** dead-time programmable in steps ≤ 1 ns, timing closes.

**If 625 ps does not close:** not a failure. Report the achieved step and fold it into the
N6 resolution study.

---

## M6 — Closed-table verification (2 weeks)

| # | Task | Output |
|---|---|---|
| 6.1 | Behavioural Verilog power stage driven by `characterisation.csv` in BRAM | `rtl/tb/power_stage_model.v` |
| 6.2 | Full-system testbench: sweep the operating point, log the chosen vector | `rtl/tb/tb_system.v` |
| 6.3 | Fixed-vector baseline for comparison | — |

**Exit criterion:** scheduled vs. fixed comparison runs end to end and produces numbers.

---

## M7 — Results (2 weeks)

| # | Task | Output |
|---|---|---|
| 7.1 | RQ1 — penalty for staying fixed, across the envelope | plot |
| 7.2 | RQ2 — coupling strength between the three actuators | plot |
| 7.3 | RQ3 — achievable Pareto surface | plot |
| 7.4 | RQ4 — minimum useful N, M, K (resolution study) | plot |
| 7.5 | RQ5 — LUT / FF / BRAM / DSP / F_max / latency | Vivado report |

**Exit criterion:** every research question has a figure, including any that returned null.

---

## Order of work this week

1. `cadence/dpt_gan.scs` — get a model in, get it converging. Everything waits on this.
2. In parallel, `rtl/quantiser.v` — no dependency on Cadence.
3. Confirm the topic change with Dr. Bindu in writing.
