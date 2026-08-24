# Proposal — GaN-Based Power Converter

**Title**
> Online Deadband-Aware ZVS-Constrained Modulation Scheduling for a GaN Dual-Active-Bridge Converter on FPGA

Shorter, if the guide wants it tighter:
> *FPGA-Scheduled Joint Modulation and Dead-Time Control for a GaN Dual-Active-Bridge Converter*

---

## 1. Base paper

> **H. Shi, H. Wen, Y. Hu**, "Deadband Effect and Accurate ZVS Boundaries of GaN-Based
> Dual-Active-Bridge Converters With Multiple-Phase-Shift Control," *IEEE Transactions on
> Power Electronics*, vol. 35, no. 9, pp. 9888–9905, September 2020.
> DOI: 10.1109/TPEL.2020.2972629

Verified on IEEE Xplore. It is a journal research paper, not a review, not a magazine article.

**Why this one.** It is GaN-specific, it is about a converter (not a gate driver), it is
theory plus experiment, and it is *analysis without a controller* — which is exactly the
kind of base paper you can extend rather than merely re-implement.

**What it establishes.** With multiple-phase-shift (MPS) control, the deadband shifts the
true ZVS boundary away from the classical analytical boundary. It derives accurate
boundaries between ZVS, partial-ZVS and hard switching, and proposes a deadband
compensation strategy. The effect worsens as switching frequency rises — which is the whole
reason to use GaN.

**What it does not do.**
- No online controller. The compensation is applied at design time.
- Dead-time is treated as a *parameter to compensate for*, never as a control variable.
- No implementation on hardware logic; no resource or latency cost reported.
- Single objective at a time; no explicit trade-off between efficiency, current stress and
  ZVS margin.

---

## 2. Research gap

Be careful here, because two neighbouring claims are **not** available:

| Claim | Status |
|---|---|
| "Optimising triple-phase-shift modulation" | **Taken.** Analytical, metaheuristic, AI and deep-RL TPS optimisers all published (2021–2026). |
| "Accounting for dead-time and nonlinear C_oss in ZVS" | **Taken.** Recent 2024–2025 work performs multi-objective global optimisation including dead-time and C_oss. |
| "Using an FPGA for DAB control" | **Taken.** Standard practice. |

What survives, and it is narrow on purpose:

> The optimisers that account for the deadband-corrected ZVS boundary run **offline, at
> design time**, and produce one modulation law. The controllers that run **online** use the
> **classical** ZVS constraint, which the base paper proves is wrong for GaN at high
> frequency. Nobody has put the deadband-corrected constraint inside an online scheduler,
> and nobody treats dead-time as a runtime control variable alongside the phase shifts.

So the gap is the **intersection**: deadband-corrected ZVS constraint × online × dead-time
as a fourth control variable × on FPGA with reported cost.

---

## 3. Novelty

Ordered by how well each survives challenge. Each is stated against what exists.

**N1 — Dead-time as a fourth control variable, not a fixed constant.**
Every MPS/TPS controller fixes dead-time and solves for (D₁, D₂, φ). The base paper proves
dead-time *moves the ZVS boundary*, so holding it fixed discards a control degree of freedom
that directly sets whether ZVS is achieved. The proposal schedules **(D₁, D₂, φ, t_dead)**
jointly.

**N2 — The penalty is first-order in GaN, not second-order.**
GaN has no body diode: reverse conduction during dead-time costs several volts against
~0.7 V for a silicon diode. Excess dead-time is therefore far more expensive, and C_oss is
strongly nonlinear. The approximation that lets silicon and SiC designs fix dead-time does
not hold here. **N2 is what turns N1 from a combination nobody tried into one that matters.**

**N3 — The deadband-corrected ZVS boundary enforced online.**
Online TPS controllers enforce the classical boundary. This enforces the base paper's
corrected boundary, at runtime, across the operating envelope.

**N4 — Pareto set resident at runtime with a selectable objective weight.**
Existing multi-objective work computes a front offline and deploys one point. Keeping the
front in BRAM lets the converter be told what to prioritise per operating region —
efficiency at high load, current-stress limiting near the device rating, ZVS margin during
transients.

**N5 — The policy in RTL, with its cost reported.**
AI and deep-RL TPS work runs offline or on a host PC. No published LUT/FF/BRAM/DSP, F_max
or decision-latency figures exist for a deadband-aware modulation policy in fabric.

**N6 — Minimum useful resolution.**
How many bits of phase-shift and dead-time resolution before the benefit disappears into
quantisation? Not reported anywhere.

**Not claimed:** TPS modulation, ZVS analysis, dead-time compensation, multi-objective
optimisation of DAB, or the use of an FPGA. All are published.

---

## 4. Research questions

**RQ1** Across the operating envelope (V_in, V_out, P_load, T_j), how far does the jointly
optimal (D₁, D₂, φ, t_dead) move from the fixed-dead-time solution, and what is the penalty
in RMS current, ZVS coverage and efficiency for holding dead-time fixed?

**RQ2** How strong is the coupling between dead-time and the phase shifts at the ZVS
boundary — and is it larger in GaN than the silicon/SiC literature assumes? *(the empirical
test of N1 and N2, and the core of the project)*

**RQ3** What is the achievable trade-off surface between efficiency, RMS current stress and
ZVS margin, and where does each become the binding constraint?

**RQ4** What are the minimum useful bit-widths for phase shift and dead-time? *(= N6)*

**RQ5** Can the policy close timing in RTL at a practical update rate, and at what cost?
*(= N5)*

> **If RQ2 returns weak coupling, report it.** That would establish that fixing dead-time is
> justified — which nobody has actually shown either. Decide this now, not later.

---

## 5. What carries over from the gate-driver work

The pivot is at the *plant*, not the *method*. Reusable as-is:

- the FPGA policy-engine architecture (quantiser → Pareto table → arbiter → interpolator);
- `rtl/quantiser.v`, unchanged — it bins an operating point regardless of what is downstream;
- the characterisation-table composition methodology (sweep the plant offline, verify RTL
  against the resulting table, never co-simulate);
- the milestone structure and the discipline of a blocking feasibility gate.

Discarded: the segmented gate-driver output stage, the Cadence transistor-level track, and
the crosstalk objective.

---

## 6. Tooling

| Purpose | Tool |
|---|---|
| Plant simulation and sweep | MATLAB/Simulink + Simscape Electrical, **or** PLECS, **or** LTspice |
| Control policy | **Xilinx Vivado** — Zynq-7000 |
| Analysis and Pareto extraction | Python (NumPy, pandas, matplotlib) |
| GaN device model | vendor SPICE (GaN Systems GS66508B / EPC) for C_oss(v) extraction |

Cadence is no longer required — this is a converter-level project. Confirm that is
acceptable, since the earlier topic assumed it.

---

## 7. Confirm before building

1. Dr. Bindu approves DAB specifically, rather than another GaN converter (totem-pole PFC,
   LLC and flying-capacitor multilevel are the alternatives; DAB is chosen because it has
   the most control degrees of freedom, which is what the method needs).
2. Vivado is still mandatory.
3. Simulation-only is acceptable, or hardware is expected.
