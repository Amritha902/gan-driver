# The shipped word fails at 200 V in the converter

Found 2026-09-21, while answering the Review-1 panel's request for measured
GaN-vs-silicon and theirs-vs-ours numbers. Recorded here because it is not
yet resolved and it affects what may honestly be claimed.

## What was measured

`sim/buck.cir`, shipped control word, bus swept. Switch-node peak, edge
resolved at a 0.02 ns step. Device is EPC2010C-class, **200 V rated**.

| bus | peak v(sw) | vs rating |
|-----|-----------|-----------|
| 100 V | 128.3 V | 72 V margin |
| 150 V | 188.7 V | 11 V margin |
| 200 V | **464.2 V** | **over by 264 V** |

Steady, not start-up: the per-cycle peak sits at ~465 V on every one of 150
cycles. Fully resolved: 50 ps samples, smooth curve through the peak.

## It is our driver, not the rail and not the converter

| configuration at 200 V | peak |
|---|---|
| ours, shipped (−2 V rail) | 464.2 V |
| ours, 0 V off rail | 470.7 V |
| **base paper's driver** | **204.1 V** |

## Mechanism

Low-side gate reaches **11.78 V** against a 1.4 V threshold while the high
side is on — full false turn-on, not a near miss. Peak current **112 A**
against a 10 A load. The 464 V is the inductive kick as that shoot-through
collapses through the 3 nH loop.

Our word is NPU = NPD = 8 — every slice, the fastest edge available. Theirs
stages 2-of-7 then the rest. Slower edge, less dv/dt, less Miller current
into the off gate. Staging di/dt is what their segmented pattern is *for*.

## The contradiction, unresolved

`headtohead.py` measures **+2.251 V** crosstalk margin for our word at
200 V / 10 A / 125 C on `sim/dpt.cir`, and the deck says our lead widens as
the corner hardens. `buck.cir` at 200 V says the opposite. Both cannot be
right about the same device.

To check, in order:
1. `dpt.cir` uses LLOAD = 100 µH; the converter uses 22 µH. Different
   current slope through the dead time.
2. `dpt.cir` measures one edge from a quiet start. The converter arrives at
   each edge carrying the previous cycle's ringing.
3. One of the two decks is wrong.

## What must not be claimed until this is resolved

- that the design is safe across the stated 50–200 V envelope
- that our lead widens as the corner gets harder

The 100 V results are unaffected — that is where the converter is
characterised and where every headline number is measured.

Reproduce: `python3 scripts/vbus_limit.py`
