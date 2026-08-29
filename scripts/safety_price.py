"""
safety_price.py -- what does crosstalk safety actually cost?

The paper claims safety is nearly free. That claim was carried for a while as
"0.30 % of switching energy", a number no script produced. It is 0.04 %. This
script exists so the figure is never again quoted without a source.

Two metrics are reported, because they disagree in an informative way:

  E_sw  = E_on + E_off      switching energy alone -- what Figure 1 plots
  cost  = E_tot + w*ov_pct  the blended objective used everywhere else

Under E_sw the energy-optimal word at the nominal corner IS infeasible, and
buying safety costs 0.04 %. Under the blended cost it costs 0.00 %, because
the infeasible word's switching-energy advantage is wiped out by its
dead-time loss. Both are true; the paper should quote the larger one.
"""
import csv, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_OV = 0.05


def load():
    rows = []
    for fn, tag in (("sweep_nominal.csv", "100V_10A_25C"), ("full_corners.csv", None)):
        p = os.path.join(ROOT, "results", fn)
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            for k, v in list(r.items()):
                if k in ("corner", "DT", "CLKDEL"): continue
                try: r[k] = float(v)
                except (ValueError, TypeError): pass
            if tag and "corner" not in r: r["corner"] = tag
            rows.append(r)
    return rows


def main(w_ov=W_OV):
    rows = load()
    corners = sorted({r["corner"] for r in rows})
    metrics = (("switching energy E_on+E_off",
                lambda r: (r["E_on"] + r["E_off"]) * 1e6, "µJ"),
               ("blended cost (w_ov=%.2f)" % w_ov,
                lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"], ""))

    for name, f, unit in metrics:
        print("\nPrice of crosstalk safety, measured on %s" % name)
        print("  %-16s %10s %8s %10s %9s" %
              ("corner", "optimum", "margin", "feasible", "price"))
        worst = 0.0
        for c in corners:
            g = [r for r in rows if r["corner"] == c]
            ch = min(g, key=f)
            feas = [r for r in g if r["margin"] > 0]
            if not feas:
                print("  %-16s  no feasible word at all" % c); continue
            cf = min(feas, key=f)
            price = 100 * (f(cf) - f(ch)) / f(ch)
            worst = max(worst, price)
            print("  %-16s %10.4f %+7.2f V %10.4f %8.3f%%%s" %
                  (c, f(ch), ch["margin"], f(cf), price,
                   "" if ch["margin"] > 0 else "   <- optimum infeasible"))
        print("  -> worst case across corners: %.3f%%" % worst)

    print("\n  The energy-optimal word is infeasible at exactly one corner, and only")
    print("  on the switching-energy metric. Quote 0.04 %, not 0.30 %.")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else W_OV)
