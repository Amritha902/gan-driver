# Segmented GaN Gate Driver — simulation prototype

Working double-pulse-test model of a GaN half-bridge driven by an
**8+8 slice thermometer-coded segmented gate driver** with programmable
dead-time, programmable negative off-bias, and a separately-timed active
Miller clamp. Runs end-to-end in **ngspice** (free, cross-platform) and is
written to port to LTspice and later to Cadence Spectre.

Built because lab/Cadence access wasn't available yet. Everything here is
reproducible on a laptop.

> **Two phases live in this repo.** Everything at the top level is the
> **segmented gate driver** — the phase with the finished Review-I deck and
> results. `dab/` is the **DAB converter** phase that followed it: it carried
> over the FPGA policy-engine architecture, `quantiser.v` and the
> characterisation-table methodology, and deliberately dropped the segmented
> output stage, the Cadence track and the crosstalk objective
> (`dab/PROPOSAL.md`, section 5). Different base papers, so read them
> separately: Takayama *et al.* here, Shi *et al.* 2020 in `dab/`.

## What it demonstrates

1. **The problem is real and reproduced.** With the fastest driver setting,
   no Miller clamp and 0 V off-bias, the off-side device's gate is pushed to
   **1.65 V against a 1.4 V threshold — false turn-on.**
2. **The actuator works.** Enabling the Miller clamp and −2 V off-bias
   restores **2.58 V of crosstalk margin.**
3. **The objectives genuinely conflict.** The Pareto surface over the control
   word shows you cannot minimise switching loss, overshoot and crosstalk
   margin at once — which is why the project is framed as *joint
   optimisation*, not "simultaneous suppression".

## Layout

```
models/egan.lib      behavioural e-mode GaN HEMT (EPC2010C-class)
models/segdrv.lib    8+8 slice segmented driver + Miller clamp
sim/dpt.cir          double-pulse testbench, all timing FPGA-style
scripts/gansim.py    run one point, extract the 8 metrics  <- definitions live here
scripts/sweep.py     720-point sweep of the control word
scripts/figures.py   report figures
results/             CSV + PNGs
```

## Run it

```bash
sudo apt-get install ngspice            # Linux
pip install numpy matplotlib

cd sim && ngspice -b dpt.cir            # single run -> out.dat
python3 scripts/gansim.py NPU_LS=4 CLKEN=1 VNEG=-2   # one point, metrics
python3 scripts/sweep.py                # 720 points, ~6 min on 4 cores
python3 scripts/figures.py              # figures into results/
```

## Model validation

Every number below was checked against a hand calculation, not eyeballed:

| Quantity | Simulated | Expected | Source of expectation |
|---|---|---|---|
| R_DS(on) @ V_GS=5 V | 26.0 mΩ | 25 mΩ | datasheet target, sets β |
| Gate on-state | 5.00 V | 5.00 V | drive rail |
| 3rd-quadrant drop @ 10.5 A | −2.81 V | −2.78 V | V_th + √(I/β) |
| Ring frequency | ~325 MHz | 1/(2π√(L_loop·C_oss)) | 3 nH, ~80 pF |
| Overshoot @ 100 V | ~20 % | L·di/dt over the loop | — |

### Two modelling decisions worth defending in the viva

**The channel is symmetric on purpose.** GaN has no body diode; reverse
conduction *is* channel conduction. A symmetric square law makes the
third-quadrant drop `V_th + |V_GS,off| + I·R` fall out of the physics rather
than being bolted on. That term is the whole reason negative off-bias costs
dead-time energy, which is the project's central trade — it must not be an
approximation.

**Capacitances are modelled as non-conducting diodes.** `C_GD(V)` and
`C_DS(V)` use junction-capacitance laws (`CJO/VJ/M`) with `IS=1e-30` and
`N=40`. The large ideality factor is not cosmetic: with `N=1` the gate-drain
"capacitor" forward-conducts as soon as `V_G > V_D` — i.e. whenever the
device is on — and clamps the gate to 3.5 V instead of 5 V. This was a real
bug during development. Diode-based C(V) is portable to LTspice and Spectre,
unlike behavioural `C=` expressions.

## Known limitations — state these before a reviewer finds them

- **Behavioural device model, not a vendor model.** Parameters follow
  EPC2010C datasheet quantities but this is not EPC's model. Re-validate
  against the vendor model once tool access exists.
- **Square-law channel, no velocity saturation.** Saturation current is
  optimistic, so switching transitions are slightly faster than reality.
- **Ideal level shifter** on the high-side driver (a VCVS). A real HV level
  shifter has propagation delay and its own dV/dt immunity problem.
- **Driver slices are ideal switches with a series resistor**, not sized
  transistors. That is exactly the block Cadence is for; the netlist is
  structured so each slice maps 1:1 onto a sized device.
- **Loop resistance is 0.3 Ω**, chosen so ring decay matches published GaN
  half-bridge waveforms (~6 cycles). It is not extracted from a real layout.
- **Trapezoidal integration on purpose.** Gear damps numerically and would
  quietly flatter the ringing metric, which is one of the objectives.

## Porting to LTspice (Windows)

The netlists are deliberately dialect-neutral. Expected differences:

- `.include` paths use forward slashes; LTspice accepts them.
- ngspice runs `.control ... .endc`; in LTspice delete that block and use the
  `.tran` line, which is already a plain netlist card.
- `$` end-of-line comments are ngspice; LTspice wants `;`.
- Ternary `{a>=b ? x : y}` in component values works in both.

A conversion helper is in `scripts/to_ltspice.py`.

## Next

Cadence replaces `models/segdrv.lib` with sized transistors. Nothing else in
the flow changes — same testbench, same extractor, same sweep, so results
stay comparable across the swap.
