# sim/

## gan_behavioural.lib — PLACEHOLDER, not a vendor model

Written from published GS66508B datasheet values so the sweep harness and loss model
can be developed before the real model is available. **Do not quote results from it.**

### Verified against theory

| Check | Expected | Model | |
|---|---|---|---|
| Forward, gate on | I = V / 50 mΩ = 20 A/V | 20.0 A/V | ok |
| Third quadrant, 1 A | −(1.7 + 1×0.05) = −1.75 V | −1.777 V | ok |
| Third quadrant, 26 A | −(1.7 + 26×0.05) = −3.00 V | −3.000 V | ok |
| Double-pulse, I at turn-off | L·I/V → 10 A at 5 µs | 10.02 A at 5.02 µs | ok |
| Double-pulse, V_DS peak | > 400 V rail | 410.6 V | ok |

The third-quadrant numbers are the point: **1.8–3.0 V of reverse drop against ~0.7 V for a
silicon body diode.** That is the physics novelty claim N2 rests on, and it is now
reproducible locally.

### What it does NOT model — read before believing any efficiency number

- **C_oss hysteresis loss (E_DISS).** Reference [19] shows soft switching is not lossless in
  GaN. This model treats C_oss as lossless, so it is **optimistic about soft-switching
  efficiency**. This matters directly: our whole argument is about where the soft-switching
  boundary sits.
- ngspice evaluates the nonlinear C_oss as `C(v)·dv/dt`, not `dQ/dt`, so stored energy is
  approximate.
- No dynamic Rds(on), no package inductance, no self-heating.

### Replace it

Free, needs a browser and a free account — the vendor sites block scripted download:

- GaN Systems / Navitas — gansystems.com → GS66508B → SPICE model
- EPC — epc-co.com → device → SPICE model

## Run

```
ngspice -b dpt_check.cir
```
