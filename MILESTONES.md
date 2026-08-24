# Milestones — GaN DAB Converter

Two tracks run in parallel after M0. The plant simulation produces a characterisation
table; Vivado consumes it. They never co-simulate.

**Exit criterion** is what must be true to move on.

---

## M0 — Feasibility gate (2 days) — BLOCKING

| # | Task | Output |
|---|---|---|
| 0.1 | Build a DAB model: two full bridges, transformer + leakage L, GaN switches with nonlinear C_oss | `sim/dab.slx` or `.plecs` |
| 0.2 | Run single-phase-shift at nominal, confirm power transfer matches the analytical `P = nVV'φ(π-|φ|)/(2π²fL)` | waveform + number |
| 0.3 | Reproduce **one figure from the base paper** — a ZVS boundary with deadband | overlay plot |

**Exit criterion:** your simulated ZVS boundary matches Shi 2020 within a few per cent.

**Why 0.3 is the real gate.** If you cannot reproduce the base paper, you cannot extend it.
Reproducing it also tells the review you actually read it.

---

## M1 — Loss and ZVS model (2 weeks)

| # | Task | Output |
|---|---|---|
| 1.1 | Extract C_oss(v) from the vendor GaN model; fit a charge-equivalent curve | `data/coss.csv` |
| 1.2 | Implement the deadband-corrected ZVS criterion from the base paper | `scripts/zvs.py` |
| 1.3 | Loss model: conduction, switching, reverse-conduction during dead-time, transformer copper | `scripts/loss.py` |
| 1.4 | Validate 1.3 against simulated efficiency at 5 operating points | table |

**Exit criterion:** model efficiency within ~2 % of simulation across those 5 points.

---

## M2 — Characterisation sweep (2 weeks)

The output of this milestone is the only interface to the Vivado track.

| # | Task | Output |
|---|---|---|
| 2.1 | Grid: V_in × V_out × P_load × T_j × D₁ × D₂ × φ × t_dead | `scripts/grid.py` |
| 2.2 | Batch-run the plant model over the grid | raw logs |
| 2.3 | Extract per point: I_rms, I_peak, ZVS flag per bridge leg, P_loss, efficiency, reactive power | `data/characterisation.csv` |
| 2.4 | **Does optimal t_dead shift with (D₁, D₂, φ) and with load?** | plot |

**Exit criterion:** CSV complete, no NaNs.

**2.4 is RQ2 and it is the scientific core.** If dead-time optimum does not move, N1 is weak
— find that out here, at week 5, not at week 14.

---

## M3 — Pareto extraction (1 week)

| # | Task | Output |
|---|---|---|
| 3.1 | Per operating region, non-dominated set over (efficiency, I_rms, ZVS margin), subject to the deadband-corrected ZVS constraint | `scripts/pareto.py` |
| 3.2 | Quantise the front to a fixed number of points per region | `data/pareto_table.mem` |
| 3.3 | Front size vs region count — this sizes the BRAM | table |

**Exit criterion:** `pareto_table.mem` loads with `$readmemh`, fits the BRAM budget.

---

## M4 — RTL policy engine (3 weeks) — starts during M1

Unblocked by M0. Use a synthetic table until M3 delivers.

| # | Task | Output |
|---|---|---|
| 4.1 | Operating-point quantiser | `rtl/quantiser.v` *(already written — reused unchanged)* |
| 4.2 | Pareto table + BRAM inference | `rtl/pareto_table.v` |
| 4.3 | Mode arbiter (runtime objective weight) | `rtl/mode_arbiter.v` |
| 4.4 | Interpolator + hysteresis guard | `rtl/interp_hyst.v` |
| 4.5 | Top level | `rtl/policy_engine.v` |

**Exit criterion:** no limit-cycling when the operating point sits on a region boundary.

---

## M5 — Modulator (2 weeks)

| # | Task | Output |
|---|---|---|
| 5.1 | Four-variable MPS modulator: D₁, D₂, φ, t_dead → 8 gate signals | `rtl/mps_modulator.v` |
| 5.2 | Dead-time insertion per leg, independently programmable | `rtl/deadtime_gen.v` |
| 5.3 | Sub-ns edge placement via `OSERDESE2` 8:1 DDR @ 200 MHz | `rtl/fine_timing.v` |
| 5.4 | Measure achieved phase-shift and dead-time resolution | report |

**Exit criterion:** dead-time step ≤ 1 ns, phase-shift step ≤ 1 % of a switching period,
timing closes.

**If it does not close:** report the achieved step and fold it into the N6 study. Not a
failure.

---

## M6 — Closed-table verification (2 weeks)

| # | Task | Output |
|---|---|---|
| 6.1 | Behavioural Verilog plant driven by `characterisation.csv` in BRAM | `rtl/tb/plant_model.v` |
| 6.2 | System testbench: sweep the operating point, log the chosen vector | `rtl/tb/tb_system.v` |
| 6.3 | Baselines: fixed dead-time + optimal TPS, and classical-ZVS-constrained online TPS | — |

**Exit criterion:** proposed vs both baselines runs end to end and produces numbers.

**6.3 matters.** Two baselines, not one. Beating a fixed-modulation strawman proves nothing;
the honest comparison is against an online TPS controller using the classical ZVS boundary.

---

## M7 — Results (2 weeks)

| # | RQ | Output |
|---|---|---|
| 7.1 | RQ1 — penalty for fixing dead-time, across the envelope | plot |
| 7.2 | RQ2 — coupling between dead-time and phase shifts at the ZVS boundary | plot |
| 7.3 | RQ3 — efficiency / I_rms / ZVS-margin trade-off surface | plot |
| 7.4 | RQ4 — minimum useful bit-widths | plot |
| 7.5 | RQ5 — LUT / FF / BRAM / DSP / F_max / latency | Vivado report |

**Exit criterion:** every RQ has a figure, including any that returned null.

---

## This week

1. Get the base paper (Shi 2020, TPEL 35(9), 9888–9905) and read it properly.
2. Build the DAB model; reproduce one ZVS-boundary figure from it. — M0
3. Confirm with Dr. Bindu: DAB specifically, Vivado still required, simulation-only acceptable.
4. In parallel: `rtl/quantiser.v` needs no changes; start `rtl/pareto_table.v`.
