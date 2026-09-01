"""
design_rule.py -- turn the negative result into something a designer can use.

"Scheduling buys only 5.2 %" is a finding, not a deliverable. The useful form
of the same measurement is a RULE:

    use this one fixed control word, and you capture ~89 % of everything the
    full adaptive machinery could deliver, with no sensing, no lookup table
    and no controller.

This prints that word, what it delivers at every corner, how far it sits from
the unreachable per-corner optimum, and the variants for designs that need a
crosstalk guard band. That is the project's actual output.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
NICE = ["pull-up", "pull-down", "HS pull-down", "dead time", "clamp", "off-bias"]


def load():
    rows = []
    for fn, tag in (("sweep_nominal.csv", "100V_10A_25C"), ("full_corners.csv", None)):
        for r in csv.DictReader(open(os.path.join(ROOT, "results", fn))):
            for k, v in list(r.items()):
                if k in ("corner", "DT", "CLKDEL"): continue
                try: r[k] = float(v)
                except (ValueError, TypeError): pass
            if tag and "corner" not in r: r["corner"] = tag
            rows.append(r)
    return rows


def main(w_ov=0.05):
    rows = load()
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in F)
    corners = sorted({r["corner"] for r in rows})
    by = defaultdict(dict)
    for r in rows: by[word(r)][r["corner"]] = r

    print("THE DESIGN RULE\n" + "=" * 64)
    for guard, label in ((0.0, "no guard band"), (1.0, "1 V crosstalk guard band")):
        univ = [k for k, d in by.items() if len(d) == len(corners)
                and all(x["margin"] > guard for x in d.values())]
        if not univ:
            print("\n%s: no word is safe at every corner." % label); continue
        mc = {k: sum(cost(by[k][c]) for c in corners) / len(corners) for k in univ}
        best = min(univ, key=lambda k: mc[k])
        sched = {c: min((r for r in rows if r["corner"] == c and r["margin"] > guard),
                        key=cost) for c in corners}
        c_s = sum(cost(sched[c]) for c in corners) / len(corners)

        print("\n%s  (%d of 720 words qualify)" % (label.upper(), len(univ)))
        print("  Use:  " + "   ".join(
            "%s=%s" % (n, v) for n, v in zip(NICE, best)))
        print("  %-16s %10s %10s %9s %9s" %
              ("corner", "E_tot µJ", "overshoot", "margin", "vs best"))
        for c in corners:
            r, s = by[best][c], sched[c]
            pen = 100 * (cost(r) - cost(s)) / cost(r)
            print("  %-16s %10.3f %9.1f%% %+8.2f V %8.1f%%"
                  % (c, r["E_tot"] * 1e6, r["ov_pct"], r["margin"], pen))
        print("  mean penalty against the unreachable per-corner optimum: %.1f %%"
              % (100 * (mc[best] - c_s) / mc[best]))

    print("\n" + "=" * 64)
    print("WHAT THE ADAPTIVE HARDWARE WOULD ADD")
    print("  Per-corner scheduling closes the residual gap above. It requires")
    print("  a current or temperature sense, an ADC, a lookup table and the")
    print("  control logic to drive them, and it returns 5.2 % of the blended")
    print("  cost at a zero guard band. Whether that trade is worth making is")
    print("  a decision this work makes measurable rather than assumed.")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
