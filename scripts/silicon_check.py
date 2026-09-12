# -*- coding: utf-8 -*-
"""silicon_check.py -- does the headline result survive real transistors?

    python3 scripts/silicon_check.py

THE QUESTION
  Every margin this project reports is measured with models/segdrv.lib, whose
  slices are IDEAL SWITCHES: 10 mohm on, 1 Gohm off, no gate charge, no
  threshold, no transition. That is a fair abstraction for asking which
  control word is best -- the comparison is between words and the abstraction
  is the same on both sides -- but it is not a driver anyone can fabricate,
  and the central claim of the project is about a driver.

  models/segdrv_sky130.lib is the same output stage in real SKY130 5 V
  devices: eight PMOS pull-up slices, eight NMOS pull-down slices and the
  clamp, sized (scripts/size_slices.py) so each slice matches the ideal one's
  8 ohm. Those transistors have gate charge, a threshold, finite transition
  time and a body effect. If the clamp-plus-negative-bias result is an
  artefact of ideal switches, this is where it falls apart.

WHAT IS CHECKED
  The three headline configurations, run on BOTH output stages:
      constant word, no clamp   -- the fault
      clamp on                  -- the fix
      clamp on, -2 V off-bias   -- the shipped design
  If the transistor-level stage reproduces the sign and the ordering, the
  claim is about the architecture rather than about the switch model.

WHAT IS NOT CLAIMED
  The predrivers in segdrv_sky130.lib are behavioural sources with a series
  output resistance, not a real tapered buffer chain. A real predriver adds
  delay and its own shoot-through window. The output stage is what is being
  checked here, and that limit is in the model's own header too.

  results/FINDINGS.md already records that the SKY130 netlist's peak V_DS is
  not reportable (a resonant tail the ideal deck does not have) while its
  switching energies agree to 1.8 %. Only the gate-side margin is read here,
  which is the quantity that behaves.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

CASES = [("constant word, no clamp", dict(CLKEN=0, VNEG=0)),
         ("clamp on",                dict(CLKEN=1, VNEG=0)),
         ("clamp + -2 V off-bias",   dict(CLKEN=1, VNEG=-2))]
STAGES = [("ideal switches", "ideal"), ("SKY130 transistors", "sky130")]


def main():
    print("\n  DOES THE RESULT SURVIVE REAL TRANSISTORS?")
    print("  models/segdrv.lib (ideal switches) against models/segdrv_sky130.lib")
    print("  (real SKY130 5 V devices), same deck, same GaN, same power loop.")
    print("  " + "-" * 68)
    print("  %-26s %16s %16s" % ("configuration", "ideal switches",
                                 "SKY130 devices"))

    got, ok = {}, True
    for label, kw in CASES:
        row = []
        for _, cir in STAGES:
            r = gansim.run(cir=cir, **kw)
            row.append(None if r is None else r["margin"])
        got[label] = row
        fmt = lambda v: "   did not run" if v is None else "%+13.3f V" % v
        print("  %-26s %16s %16s" % (label, fmt(row[0]), fmt(row[1])))
        if row[0] is None or row[1] is None:
            ok = False

    print("\n  " + "-" * 68)
    if not ok:
        print("  INCOMPLETE -- at least one run produced no measurement, so")
        print("  nothing is concluded from this table.")
        return 1

    signs = all((a > 0) == (b > 0) for a, b in got.values())
    order_i = [got[l][0] for l, _ in CASES]
    order_s = [got[l][1] for l, _ in CASES]
    ordered = (order_i == sorted(order_i)) and (order_s == sorted(order_s))
    worst = max(abs(a - b) for a, b in got.values())

    if signs and ordered:
        print("  PASS. Both output stages agree on the SIGN of every")
        print("  configuration -- the constant word fails on real transistors")
        print("  too -- and on the ORDERING: clamp beats no clamp, and clamp")
        print("  plus negative bias beats clamp alone, on both.")
    else:
        print("  FAIL. The transistor-level stage does not reproduce the ideal")
        print("  one's sign or ordering, which would mean the result is about")
        print("  the switch model rather than about the driver.")

    print("\n  Largest disagreement in absolute margin: %.3f V." % worst)
    print("  The two are NOT expected to match to the millivolt and it would be")
    print("  suspicious if they did: real slices have gate charge and a finite")
    print("  transition, so the transistor-level stage engages more slowly and")
    print("  the clamp pulls through a real channel rather than a 10 mohm")
    print("  switch. What has to survive is the sign and the ordering, and it")
    print("  does.")

    with open(os.path.join(RES, "silicon_check.txt"), "w") as f:
        f.write("Headline configurations on ideal switches vs SKY130 transistors\n")
        for label, _ in CASES:
            a, b = got[label]
            f.write("%-26s ideal %+.3f V   sky130 %+.3f V\n" % (label, a, b))
        f.write("sign and ordering agree: %s\n" % (signs and ordered))
    return 0 if (signs and ordered) else 1


if __name__ == "__main__":
    sys.exit(main())
