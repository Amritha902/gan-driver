# Run log — everything in this repo, executed and checked

Date of this run: 11 September 2026. Environment: Ubuntu 24.04, ngspice 42,
Python 3.11, Vivado reports pre-existing (run 5 Sep on Windows).

The point of this file is that a reader should not have to take the repo's
word for anything. Every simulation deck and every script was run, and what
follows is what actually happened, including the parts that failed.

---

## 1. Simulation decks — 8 of 10 run, 2 do not

Each deck in `sim/` run directly: `cd sim && ngspice -b <deck>.cir`.

| deck | result |
|---|---|
| `buck.cir` | runs — the converter, 100 V → 48.5 V |
| `dpt.cir` | runs — the double-pulse bench every headline number comes from |
| `dpt_c.cir` | runs |
| `dpt_dcload.cir` | runs |
| `dpt_sky130.cir` | runs (after the fix in §2) |
| `dpt_sky130_b.cir` | runs (after the fix in §2) |
| `dpt_hyb_hs_sky130.cir` | runs (after the fix in §2) |
| `dpt_hyb_ls_sky130.cir` | runs (after the fix in §2) |
| `dpt_dcload_c.cir` | **does not converge** — see §3 |
| `dpt_sky130_c.cir` | **does not converge** — see §3 |

## 2. Bug found and fixed: the SKY130 decks had a hard-coded path

All five `*sky130*.cir` decks began with

    .lib "/home/user/gan-driver/pdk/sky130_5v.lib" tt

an absolute path naming one particular clone location. Every other deck in
the repo uses a relative path (`../models/egan.lib`), so these five were the
odd ones out and failed on any checkout that was not at exactly that path —
including a plain `git clone` into any other directory. Changed to

    .lib "../pdk/sky130_5v.lib" tt

which is relative to `sim/`, matching every other deck. Four of the five then
ran; the fifth is §3.

The PDK itself is fetched per `PDK-NOTE.md` (19 MB, Apache-2.0, third-party)
and is **not** committed — `pdk/` is now in `.gitignore` so it cannot be added
by accident.

## 3. Known limitation: the `_c` model variant does not always converge

`models/egan_c.lib` is an alternative GaN model. It is identical to
`models/egan.lib` except that the two junction capacitances are written as
behavioural expressions instead of as non-conducting diodes:

    egan.lib     Dgd  g2 d  DGD                    (diode, C(V) law only)
    egan_c.lib   Cgd  g2 d  C={150p/pow(...,0.65)} (behavioural expression)

ngspice aborts on two of the three decks that use it:

    doAnalyses: TRAN: Timestep too small; initial timepoint:
    trouble with node "hstop"

It fails at the *initial* timepoint, so it is the model expression rather than
solver effort. Raising `itl1`/`itl4` and `gmin` does not help — tried, no
change. The obvious remaining lever, switching to Gear integration, is
deliberately **not** used: `dpt.cir` states that trapezoidal is chosen on
purpose because "Gear damps numerically and would quietly flatter the ringing
metric", and ringing is one of the measured objectives. Changing it to force
convergence would corrupt a reported number to fix a cosmetic failure.

**This affects nothing that is reported.** Checked explicitly: no script, no
result file, and no deck number references `dpt_dcload_c.cir`,
`dpt_sky130_c.cir` or `egan_c.lib`. They are orphaned cross-check variants.
Every published figure comes from the diode-based `egan.lib`, which runs
everywhere.

`egan.lib`'s own header already says why diodes are preferred — they port to
ngspice, LTspice and Spectre where behavioural `C=` does not. This run is
evidence for that choice rather than against it.

## 4. Analysis and result scripts — 17 of 17 run

`gansim` · `bucksim` · `cases` · `novelty` · `ceiling` · `decompose` ·
`weight_sensitivity` · `robust_analyse` · `lloop_analyse` · `summary` ·
`guardband` · `whichbit` · `howmanywords` · `design_rule` · `safety_price` ·
`scaling` · `verdict_stability` — all exit 0.

## 5. Figure generators — 14 of 14 run

`paper_figs` · `figures` · `si_vs_gan_figure` · `buck_figure` · `cases_figure` ·
`flow_diagram` · `arch_diagram` · `circuit_diagram` · `netlist_figure` ·
`tools_figure` · `vivado_figure` · `explainer_figures` · `howrun_figure` ·
`buck_tradeoff_figure` — all exit 0, all PNGs regenerated from current data.

---

# What the results mean

## The base paper, reproduced and beaten — but quote it fairly

`models/zhangdrv.lib` implements Zhang et al. (ISPSD 2020): seven slices
engaged as a timed pattern, pattern chosen by one bias resistor, no clamp, no
negative rail. Run in `sim/dpt.cir` with only the driver swapped.

| configuration | margin | |
|---|---|---|
| base paper, at its best setting | **+0.407 V** | safe |
| ours, constant code, no clamp | −0.249 V | FALSE TURN-ON |
| ours, clamp on | +0.570 V | safe |
| ours, clamp + −2 V off-bias | **+2.576 V** | safe |

**Ours is 6.3× their best.** Their margin runs from +0.407 V down to −0.278 V
across their own stated 0.5–5 ns pattern range, so whichever setting you hand
them decides how far ahead you look. `basepaper_compare.py` searches that
range and quotes their best point. Quoting them anywhere worse is choosing the
opponent, not measuring against one.

That the reproduction is real and not decorative is checkable: setting
`nseg=7` (all slices at once, no staging) gives −0.278 V, which reproduces our
own constant-code result of −0.249 V to within 0.03 V, independently.

## Why GaN and not silicon — the trade-off never turns around

`models/simosfet.lib` is a 200 V silicon MOSFET matched on R_DS(on)
(24.0 mΩ against the GaN's 25.0 mΩ), each driven at its own rated gate
voltage. Conduction loss is therefore equal by construction and what the
comparison exposes is switching, gate drive, and the body-diode reverse
recovery that GaN does not have.

At 500 kHz: **GaN wastes 5.93 W, silicon 17.34 W — 66 % less, 4.16
efficiency points.** And the lead widens everywhere it is pushed:

| sweep | GaN's lead |
|---|---|
| 100 kHz → 1 MHz | 24 % → **78 %** |
| heavy load → light load | 22 % → **90 %** |
| 50 V → 200 V bus | 56–69 %, no turning point |

The frequency row is the argument. Silicon's loss grows 3.6× from 100 kHz to
1 MHz and its efficiency falls 96.7 % → 88.6 %; GaN's stays between 5.1 and
7.7 W and holds ~97 %. **Raising the frequency to shrink the magnetics is
close to free on GaN and ruinous on silicon**, and that is the reason to
accept GaN's crosstalk problem and then solve it.

Over a year of real duty (`usecase_energy.py`), GaN saves **111–237 kWh**
depending on profile, and saves under *every* profile from always-heavy to
always-idle.

**GaN's one genuine disadvantage, stated rather than hidden:** it has no body
diode, so its dead-time reverse drop is V_th + |V_off| + I·R_DS(on) instead of
one diode drop. Sized at the shipped settings that penalty is **1.0–3.4 % of
GaN's own total loss** — real, already charged inside every number above, and
nowhere near enough to change the answer.

## How much controller is worth building — and a correction

The project's headline was that one comparator closes 72 % of the adaptive
gap. **It does not.** That search enumerated all 2ⁿ partitions of the four
corners, which permits splits no single threshold can produce. The winning
split isolates `200V_2A_125C`, and that corner shares its bus voltage with
`200V_10A_125C`, its load current with `50V_2A_25C`, and its junction
temperature with `200V_10A_125C`. No one threshold on one sensed quantity
separates it; selecting it takes **two** comparators.

Restricted to splits one comparator can actually build:

| controller | closes | residual a full LUT must justify |
|---|---|---|
| fixed word + **one** comparator (VBUS at 75 V) | **46 %** | **7.2 %** |
| fixed word + **two** comparators | 72 % | 3.7 % |
| full lookup table (oracle) | 100 % | — |

So **3.7 % is the two-comparator figure**; with one comparator the residual is
7.2 %. Both are now computed side by side in `novelty.py`, and the 2ⁿ search
is labelled as the upper bound it is. `controller_ladder.py` asks the same
question independently, as a complexity ladder from constant word to full
lookup table, and reaches 46 % on the same split — two implementations
agreeing is the reason to believe it.

The deck's description of it as a *light-load* comparator is also wrong: the
best single-comparator split is on **bus voltage**.

**And it does not generalise.** Leave-one-corner-out: a comparator fitted on
three corners is *worse* than simply using the fixed word on **3 of the 4**
held-out corners. n = 4, so this is weak evidence and is labelled as such —
but it points the same way as everything else here.

---

## What this all adds up to

1. GaN is the right device, and the trade-off never tips back to silicon.
2. Its speed is what causes false turn-on, which is the problem to solve.
3. The clamp plus a −2 V off-bias solves it — 6.3× the base paper's best.
4. Re-tuning the driver per operating point is worth little, most of that
   little is reachable with one comparator, and what remains does not survive
   being tested on an operating point it was not fitted to.

## Still open

- `dpt_dcload_c.cir` and `dpt_sky130_c.cir` do not converge (§3). Nothing
  depends on them; fixing would mean reworking `egan_c.lib`'s capacitance
  expressions, not changing solver settings.
- The silicon model's parameters are datasheet-*class* for a 200 V / 24 mΩ
  part, not transcribed from the IRFB4227PbF datasheet. The qualitative result
  does not depend on the third digit; the quantitative one does. Check before
  publication — this is stated in `models/simosfet.lib` too.
- The 100 kHz and 250 kHz sweep points reuse the 22 µH inductor sized for
  500 kHz, so those runs have very large ripple. The Si-vs-GaN comparison at
  each point is still like-for-like, but GaN's own absolute trend across
  frequency is confounded by it. Claim that silicon's loss clearly grows; do
  not claim GaN's is perfectly flat.

---

## Addendum — the RTL and the SPICE model now meet

The architecture was verified in two halves that never touched:
`seg_gate_ctrl.v` emits eight thermometer-coded wires per bank, and
`models/segdrv.lib` consumes an **integer** slice count, switching every slice
from one shared node and enabling each by its series resistance. So every
number in this project rested on an assumption nobody had tested — that
"npu = N" in SPICE faithfully stands in for whatever bus the FPGA drives. A
fault in `thermo_decode.v` could have passed the Icarus bench and stayed
invisible to every figure ngspice produced.

`scripts/rtl_cosim.py` now reads the RTL's own VCD and checks it:

| bank | configured → asserted |
|---|---|
| `ls_pu` | 0→0, 1→1, 2→2, 3→3, 4→4, 5→5, 6→6, 7→7, 8→8 |
| `ls_pd` | 8→8 |
| `hs_pu` | 0→0, 8→8 |
| `hs_pd` | 8→8 |

**Zero mismatches.** Every configured count asserts exactly that many slices,
on every bank. The abstraction is sound and the existing results stand.

### The power stage, driven by the RTL

The encoding check above is the narrow claim. The wide one — that the
parameterised driver every figure was measured with is the driver the FPGA
actually builds — is now tested where it matters. `sim/dpt.cir` is run twice.
Same deck, same devices, same `.meas` statements. The only difference is how
the low-side slices are chosen: by `segdrv.lib`'s `npu`/`npd` integers in one
run, and in the other by sixteen PWL sources generated from the RTL's own VCD
into `models/segdrv_bus.lib`, one per wire.

| | crosstalk margin, RTL bus | crosstalk margin, `.param` | difference |
|---|---|---|---|
| clamp off | **−0.242 V** | −0.249 V | 0.007 V |
| clamp on | **+0.651 V** | +0.570 V | 0.081 V |

Low-side gate excursion agrees to four significant figures in both runs
(8.231 V peak, identical). Worst disagreement anywhere: **0.081 V**.

So the abstraction holds, and the clamp's sign change — the project's central
claim — is reproduced by the actual logic rather than by a parameter. The
0.081 V on the clamp-on row is timing, not encoding: the deck's ideal stimulus
turns the low side on at T4 = 2.015 µs, while the RTL's dead-time generator
puts it at 2.0175 µs, so the switch-node transient the high-side gate sees is
displaced by 2.5 ns.

The high side keeps the parameterised driver in both runs. It is the victim
being measured, and holding it fixed is what keeps this margin comparable with
every other number in the project; driving it from the RTL too would need the
high-side level shifter `dpt.cir` deliberately models as ideal.

### The dead time is one cycle longer than dividing by the clock suggests

`rtl/seg_gate_ctrl_dpt_tb.v` was swept over `dt_cycles`, measuring both the
width of `dead_time_active` and the real bank-to-bank gap from `ls_pu`
releasing to `hs_pu` engaging. The two agree exactly, and both give

    dead time = (dt_cycles + 1) x 5 ns

    dt_cycles = 1 -> 10 ns      dt_cycles = 3 -> 20 ns
    dt_cycles = 2 -> 15 ns      dt_cycles = 4 -> 25 ns

`dead_time_gen` loads `cnt <= dt_cycles` and then counts down *through* zero,
so it spends `dt_cycles + 1` clocks in the dead state. `dpt.cir`'s DT = 15 ns
is therefore `dt_cycles = 2`, not the obvious 15/5 = 3, which gives 20 ns.

This matters beyond bookkeeping: anyone mapping the swept DT grid onto hardware
by dividing by the clock period builds a driver that is one cycle slow at every
operating point. Neither the Icarus bench nor the ngspice sweep could see it
alone — it is exactly the class of error co-simulating the two halves exists
to catch.

### What was attempted first and did not work, and why

Driving the power stage directly from those waveforms — each slice wire as its
own PWL source into `models/segdrv_bus.lib`, which has one control pin per
slice. It produced a 7 kV gate on a 5 V rail.

That is not a solver failure; ngspice reported no warnings and solved the
circuit correctly. It is a true answer to a meaningless question.
`seg_gate_ctrl_tb.v` is a **controller unit test** — it sweeps encoder
configurations, and its timeline has no relation to `dpt.cir`'s T1–T4
schedule. Its stimulus contains windows (35–45 ns among them) where
`ls_pu = 0`, `ls_pd = 0` and `ls_clamp = 0` together: all sixteen slices off
and no clamp. Played into the real power stage the gate is then held only
through the 1 GΩ off-switches, the 100 V transient couples in through C_GD,
and the node integrates to kilovolts.

Worth recording separately: the first version of that check asserted only
`V(lsg) > 0.9 × rail`, which passed 7158 V as happily as 5 V. A one-sided
bound is not a check. It now tests both rails.

The fix was not a solver setting. It was `rtl/seg_gate_ctrl_dpt_tb.v`: a
bench written for this purpose, reproducing `dpt.cir`'s double pulse at the
real 200 MHz clock, with the RTL's own dead-time generator making the T2 and
T4 edges rather than a testbench drawing them.

One further startup artifact had to be dealt with honestly. The controller
needs a few clocks to leave reset and load its word, and until it does it
commands neither device on. Start the SPICE run at that instant and the power
stage sees both GaN devices off with 10 A already in the load inductor: the
switch node slews to the rail, rings, and couples **59 V** into the low-side
gate. True, and meaningless — no converter is energised while its controller
is held in reset. The bench therefore offsets the whole double pulse by a
25 ns settle window (5 clock periods, so every edge stays clock-aligned) and
`rtl_cosim.py` subtracts it again, putting the reset before SPICE t = 0. The
low side is then already fully on at t = 0, exactly as `dpt.cir`'s own
stimulus has it.
