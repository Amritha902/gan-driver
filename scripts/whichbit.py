"""
whichbit.py -- which control field is actually worth scheduling?

The claim that the benefit "collapses to one bit" rests so far on the LUT
pattern, which is suggestive rather than conclusive.  This measures it.

For each field in turn: FREEZE that field at its single best value across
all corners, let every other field adapt freely per corner, and see how much
worse the result gets.  A field that costs nothing to freeze is not worth
scheduling.  A field that costs a lot is.
"""
import csv, itertools, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
NICE = {"NPU_LS": "pull-up strength", "NPD_LS": "pull-down strength",
        "NPD_HS": "high-side pull-down", "DT": "dead time",
        "CLKEN": "Miller clamp", "VNEG": "gate off-bias"}


def load(fn, tag=None):
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", fn))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        if tag and "corner" not in r: r["corner"] = tag
        out.append(r)
    return out


def main(w_ov=0.05, guard=0.0):
    rows = load("sweep_nominal.csv", "100V_10A_25C") + load("full_corners.csv")
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    corners = sorted({r["corner"] for r in rows})
    feas = [r for r in rows if r["margin"] > guard]

    # full per-corner freedom: the reference
    best = {c: min((r for r in feas if r["corner"] == c), key=cost) for c in corners}
    c_free = sum(cost(best[c]) for c in corners) / len(corners)

    print("Cost of freezing each control field, guard band %.1f V.\n" % guard)
    print("  Reference: every field free to adapt per corner -> mean cost %.3f\n" % c_free)
    print("  %-22s %-16s %10s   %s" % ("field frozen", "frozen value", "penalty", "worth scheduling?"))
    out = []
    for f in F:
        vals = sorted({r[f] for r in feas}, key=str)
        bestpen, bestval = None, None
        for v in vals:
            sub = [r for r in feas if r[f] == v]
            per = {}
            ok = True
            for c in corners:
                cand = [r for r in sub if r["corner"] == c]
                if not cand: ok = False; break
                per[c] = min(cand, key=cost)
            if not ok: continue
            cc = sum(cost(per[c]) for c in corners) / len(corners)
            pen = 100 * (cc - c_free) / c_free
            if bestpen is None or pen < bestpen:
                bestpen, bestval = pen, v
        if bestpen is None:
            print("  %-22s %-16s %10s" % (NICE[f], "-", "no value works")); continue
        out.append((f, bestpen))
        verdict = "YES" if bestpen > 2.0 else ("marginal" if bestpen > 0.5 else "no")
        print("  %-22s %-16s %9.2f%%   %s"
              % (NICE[f], str(bestval), bestpen, verdict))
    out.sort(key=lambda x: -x[1])
    print("\n  Ranked: " + ", ".join("%s %.2f%%" % (NICE[f], p) for f, p in out))
    if out and out[0][1] > 2 * (out[1][1] if len(out) > 1 else 0):
        print("\n  -> %s dominates: freezing it costs %.1fx more than freezing"
              % (NICE[out[0][0]].upper(), out[0][1] / max(out[1][1], 1e-9)))
        print("     the next field. The benefit really does concentrate in one field.")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(float(a[0]) if a else 0.05, float(a[1]) if len(a) > 1 else 0.0)
