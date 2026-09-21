# RESOLVED — neither deck was lying; the decoupling network was undamped

Opened 2026-09-21 when `buck.cir` at 200 V rang to 464 V while `dpt.cir` at
the same bus said 207 V. Closed the same day. Kept because the way it was
found is worth more than the fix.

## The disagreement

| at a 200 V bus | `dpt.cir` | `buck.cir` |
|---|---|---|
| peak switch node | 207.3 V | **464.2 V** |
| low-side gate, HS on | −1.97 V | **+11.78 V** (vth = 1.4 V) |
| peak device current | — | **112 A** into a 10 A load |

Same devices, same driver, same control word.

## What it was not

- **Not the edge being measured.** First hypothesis: `dpt.cir`'s metric is
  `v(hsg) − v(sw)` over 2.015–2.10 µs, which starts at T4 — the *low-side*
  turn-on, high side as victim. `buck.cir` fails the other way round. But
  measuring `dpt.cir`'s low-side gate on the high-side edge gives −1.97 V at
  every corner. It is clean on both edges. Hypothesis dead.
- **Not the −2 V rail.** A 0 V rail gives 471 V, marginally worse.
- **Not the output filter.** `LOUT` 22 µH → `dpt`'s 100 µH: 451 V.
- **Not the dead time.** 15 ns → 30 ns: 462 V.

## What it was

The bus decoupling branch — `Ldec` 0.5 nH, `Cdec` 100 nF, `Rdec` **20 mΩ** —
is a series L-C with Q ≈ 3.5 near 22 MHz. The switching edges pump it once a
cycle. At 100 V the ringing is survivable. At 200 V it crosses the low-side
threshold, and the 464 V is the shoot-through collapsing through the 3 nH
loop.

`dpt.cir` has no decoupling network. That is the entire reason it looked
clean — not because it was right about the device, but because it was not
modelling the thing that was wrong.

**That branch was added earlier in this project to fix a 168 V overshoot at
100 V.** It did fix that. It was never damped and never checked at the top
of the bus range.

## The fix: `Rdec` 20 mΩ → 1 Ω

|  | 100 V bus | 200 V bus |
|---|---|---|
| peak v(sw) | 128.3 → **118.0 V** | 464.2 → **208.2 V** |
| LS gate while HS on | −0.27 → **−0.97 V** | +11.78 → **−0.74 V** |
| margin to vth | +1.67 → **+2.37 V** | false turn-on → **+2.14 V** |
| efficiency | 97.39 → **97.42 %** | |
| device dissipation | 2.800 → **2.598 W** | |

Costs nothing, better on every axis, and at 200 V brings `buck.cir` to
208.2 V against `dpt.cir`'s 207.3 V — **the two decks now agree to 1 V.**

Q drops below 1 somewhere above 100 mΩ. 1 Ω is overdamped rather than
critically damped, which is the right side to err on for a branch whose only
job is to keep the bus stiff.

## What this changes elsewhere

The apparent timestep sensitivity of the overshoot measurement (+4.1 points
between a 0.2 ns and a 0.02 ns step) was mostly this ringing being aliased.
Damped, it is +0.7 points. The −2 V rail is now the dominant term at +11.3
points — the crosstalk margin is not free, and the deck says so.

## What may now be claimed

Both. The 50–200 V envelope holds with the damped branch. The earlier
instruction not to claim it is withdrawn.

Reproduce: `python3 scripts/decoupling_damping.py`
