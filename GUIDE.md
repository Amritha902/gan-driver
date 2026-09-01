# Project guide — read this before the review

Everything below was re-verified by actually running it on 1 Sep 2026.
Numbers in **bold** were reproduced from scratch, not copied from notes.

---

## 1. The problem statement, in one sentence

> In a GaN half-bridge, switching one device fast enough to get low loss
> couples charge through the *other* device's Miller capacitance and can
> switch it on when it is supposed to be off — so **speed and safety fight
> each other**, and this project asks how much of that conflict can be
> resolved by making the gate driver *programmable* instead of fixed.

### The longer version

A half-bridge has two transistors in series across the DC bus. Only one may
conduct at a time; if both conduct, the bus is shorted through them
(shoot-through) and they are destroyed.

When the bottom device turns on, the switch node between them slews very fast
— GaN does this in a few nanoseconds, which is exactly why GaN is attractive.
But that fast `dV/dt` drives a current through the top device's gate–drain
capacitance `C_GD`. That current flows into the top device's gate and lifts
its gate voltage. If it lifts past the threshold (**1.4 V** for our device),
the top device partially turns on while the bottom one is already on. That is
**false turn-on** — the failure this project exists to remove.

The obvious fix is to slow the switching down. That works, and it costs you
the switching-loss advantage you bought GaN for in the first place. So the
real engineering question is not "how do we stop false turn-on" (easy) but
**"how do we stop it while keeping the speed"**.

---

## 2. Why this belongs to "power converters for energy storage systems"

This is the framing your guide asked for, and it is a genuine fit, not a
retrofit:

- A battery energy-storage system moves power between a battery and the grid
  through a bidirectional converter. That converter is built from
  **half-bridges** — the exact circuit studied here.
- Its efficiency is charged **twice** on every stored joule: once charging,
  once discharging. A 1% switching-loss improvement is therefore worth about
  twice what it is worth in a one-way converter.
- Storage converters run across a **very wide operating range** — full-rate
  charge, full-rate discharge, and long stretches at light load. A gate-driver
  setting that is optimal at full load is not optimal at light load. That is
  precisely the case for a *programmable* driver, and it is why the
  adaptation question in this project is a storage question specifically.
- GaN raises switching frequency, which shrinks the magnetics and the cabinet
  — a direct cost driver in grid-scale storage.

**Say this if asked "why energy storage":** the bidirectional half-bridge is
the core of a storage converter, its losses are paid on both charge and
discharge, and its operating range is wide enough that a single fixed gate
drive setting is provably not optimal everywhere.

---

## 3. What we built

An **8+8 slice thermometer-coded segmented gate driver**. Plain English:

- Instead of one fixed-strength gate driver, there are 8 pull-up slices and 8
  pull-down slices that can be switched in or out independently. Turning on
  more slices = stronger, faster drive. This makes drive strength a *number
  you can program* rather than a resistor you soldered.
- Plus a programmable **dead time** (the pause where both devices are off).
- Plus a programmable **negative off-bias** — instead of holding the off
  device's gate at 0 V, hold it at −2 V, so the Miller kick has further to
  climb before reaching the 1.4 V threshold.
- Plus a separately-timed **active Miller clamp** — a low-impedance switch
  (0.5 Ω) that shorts the off device's gate to its source during the
  dangerous window, so the injected charge is drained instead of accumulating.

Together those settings form a **control word**. The whole project is about
what the best control word is, and whether it needs to change during operation.

---

## 4. The results — all re-verified today

| What | Measured | Meaning |
|---|---|---|
| Fastest drive, no clamp, 0 V off-bias | margin **−0.249 V** | **FAILS** — false turn-on, spurious gate peak 1.65 V vs 1.4 V threshold |
| Miller clamp on | margin **+0.570 V** | Safe |
| Miller clamp + −2 V off-bias | margin **+2.576 V** | Safe, with 2.58 V of headroom |

Reproduce any of these in about a minute each:

```bash
cd gan-driver
python3 scripts/gansim.py CLKEN=0 VNEG=0     # the failure
python3 scripts/gansim.py CLKEN=1 VNEG=0     # clamp fixes it
python3 scripts/gansim.py CLKEN=1 VNEG=-2    # shipped configuration
```

### The finding that is actually novel

The control word was searched **exhaustively** — 720 words × 4 corners,
roughly 33,200 transient simulations. Splitting the benefit:

- Choosing a **better fixed** control word: **25.1%** of baseline loss.
- **Adapting** it per operating point on top of that: a further **3.9%**.

So adaptation is only about **13.4%** of the total gain — the large majority
comes from simply picking a better *fixed* setting. And 72% of even that small
adaptive part is captured by a **single comparator** (K=2), leaving ~3.7% of
the total to justify a full sense + ADC + lookup-table system.

**This is the contribution, and it is a negative-result finding — say so
confidently.** A lot of published work proposes elaborate adaptive gate
drivers. This project measures how much of their benefit actually requires
adaptation, and the answer is: much less than assumed. That is a more useful
and more honest result than another "we built an adaptive driver" paper.

---

## 5. Status — the 50% that is done

- [x] Literature survey and base paper identified
- [x] Behavioural GaN HEMT model, validated against datasheet (R_DS(on) 26.0 mΩ vs 25 mΩ target)
- [x] Segmented driver + Miller clamp model
- [x] Double-pulse testbench, FPGA-realistic timing
- [x] Problem reproduced (false turn-on) and fixed (2.58 V margin)
- [x] Full 720-word × 4-corner exhaustive search
- [x] Pareto / adaptation-value analysis in MATLAB
- [x] Verilog RTL for the controller (`rtl/`) with testbench
- [x] Review-I deck

## 6. The 50% that is left

1. **LTspice cross-check** — run `ltspice/dpt.cir` in real LTspice and confirm
   it agrees with ngspice. (Currently everything is verified in ngspice.)
2. **FPGA implementation** — synthesise `rtl/seg_gate_ctrl.v` onto the Xilinx
   board, and drive real gate-driver hardware from it. This is the natural
   next milestone and needs board access.
3. **Cadence / Spectre** — take the driver to a real PDK for layout and
   silicon-level numbers. Scripts are already staged in `cadence/`.
   **This needs remote Cadence access — ask your guide for it in this review.**
4. Thermal and reliability corners; closing the loop from measurement back to
   the control word.

---

## 7. How to walk through it in the viva

Open things in this order:

1. **`ltspice/dpt.cir`** — the real, complete circuit. Show the param block at
   the top; that is the control word. This is the file to present.
2. **Run the three commands in §4** — show the failure, then the fix, live.
3. **`results/gan_analysis.m`** — the MATLAB analysis. Runs in MATLAB or
   Octave, no toolboxes. Produces `pareto_matlab.png` (objectives conflict)
   and `crosstalk_model_matlab.png` (analytical model vs SPICE).
4. **`rtl/seg_gate_ctrl.v`** — the controller that would emit the control word
   on the FPGA. You can run its self-check live, and it is worth doing:

   ```bash
   cd rtl
   iverilog -g2012 -o /tmp/tb seg_gate_ctrl_tb.v seg_gate_ctrl.v \
            dead_time_gen.v thermo_decode.v && /tmp/tb
   #   -> ALL CHECKS PASSED   (properties T1-T8)
   sh mutate.sh
   #   -> injects a real shoot-through bug; bench catches it,
   #      221 failures across T1, T3, T8
   ```

   The mutation run is the stronger demo: it shows the testbench can actually
   fail, which a passing test alone never proves.
5. **`results/RESULTS-SUMMARY.txt`** — every number with the script that
   regenerates it.

---

## 8. Questions you should be ready for

**"Show me the Miller clamp in the schematic."**
Open `ltspice/dpt.cir` and `models/segdrv.lib` — the clamp is
`Sclk out nclk clk ref SWP` with `Rclk nclk vn 0.5`. Note: the three simplified
`.asc` sheets in `ltspice/` do **not** draw the clamp; they only illustrate the
crosstalk mechanism and gate-resistance effect. Their labels now say so. Do not
present the `.asc` files as the clamped design — use `dpt.cir`.

**"Is this simulated or measured?"**
Entirely simulation, in ngspice, with a behavioural GaN model validated against
datasheet values. Hardware is the next phase. Say this plainly — it is a Review-I
project and simulation is the expected stage.

**"Why not just slow it down?"**
That is the trivial fix and it discards the switching-loss benefit of GaN. The
project quantifies the trade rather than assuming it: the Pareto surface shows
switching loss, overshoot and crosstalk margin cannot be minimised together.

**"What is new here?"**
The decomposition in §4 — separating how much of an active gate driver's
benefit comes from a better *fixed* setting versus genuine *per-operating-point
adaptation*, measured by exhaustive search rather than argued.

**"Your 13.4 % depends on how you weighted overshoot."**
It does, and we measured exactly how much. Swept over 106 overshoot weights,
choosing a better fixed word is worth 23.4–29.0 % of baseline and adaptation
1.3–6.4 % (over the studied range 0 to 1.0). The magnitude of 13.4 % is
weight-dependent; the **ordering is not** — the fixed word beats adaptation at
every weight tested, out to a weight of 5.0, which is already physically
extreme. So the conclusion "most of the benefit needs no adaptive hardware"
does not rest on the weighting. `scripts/weight_sensitivity.py`, and
`results/fig_weight_sensitivity.png`.

**"What is the price of safety?"**
Under 0.04% of switching energy. Crosstalk safety is essentially free once the
clamp and off-bias are configured — that is itself a result worth stating.
