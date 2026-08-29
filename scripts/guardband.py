"""
guardband.py -- does the ceiling hold for a CAUTIOUS designer?

Feasibility is defined elsewhere as crosstalk margin > 0. Nobody ships at
zero margin. This recomputes the ceiling requiring a guard band, because if
the conclusion only holds for a designer willing to sit on the threshold it
is not a useful conclusion.
"""
import csv, os, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS","NPD_LS","NPD_HS","DT","CLKEN","VNEG"]

def load(fn, tag=None):
    out=[]
    for r in csv.DictReader(open(os.path.join(ROOT,"results",fn))):
        for k,v in list(r.items()):
            if k in ("case","corner","DT","CLKDEL"): continue
            try: r[k]=float(v)
            except (ValueError,TypeError): pass
        if tag and "corner" not in r: r["corner"]=tag
        out.append(r)
    return out

def main(w_ov=0.05):
    rows = load("sweep_nominal.csv","100V_10A_25C") + load("full_corners.csv")
    word = lambda r: tuple(r[f] if f=="DT" else int(float(r[f])) for f in F)
    cost = lambda r: r["E_tot"]*1e6 + w_ov*r["ov_pct"]
    corners = sorted({r["corner"] for r in rows})
    per = defaultdict(dict)
    for r in rows: per[word(r)][r["corner"]] = r
    print("Ceiling vs required crosstalk guard band\n")
    print("  guard   universal words   ceiling   best fixed word")
    for gb in (0.0,0.2,0.5,1.0,1.5,2.0):
        univ=[k for k,d in per.items()
              if len(d)==len(corners) and all(x["margin"]>gb for x in d.values())]
        if not univ:
            print("  %4.1f V        %3d        no universal word -> scheduling REQUIRED"%(gb,0))
            continue
        fx=min(univ,key=lambda k: sum(cost(per[k][c]) for c in corners))
        cf=sum(cost(per[fx][c]) for c in corners)/len(corners)
        sched=[min((cost(r) for r in rows if r["corner"]==c and r["margin"]>gb), default=None)
               for c in corners]
        if any(s is None for s in sched):
            print("  %4.1f V        %3d        no feasible word at some corner"%(gb,len(univ)))
            continue
        cs=sum(sched)/len(sched)
        print("  %4.1f V        %3d       %6.2f%%   %s"
              % (gb,len(univ),100*(cf-cs)/cf,"%d/%d/%d/%s/%d/%+g"%fx))
    print("\n  The ceiling roughly DOUBLES between a zero guard band and 1 V,")
    print("  and the best fixed word switches to negative off-bias there.")
    print("  It is non-monotonic beyond that: at 2 V the feasible set has")
    print("  shrunk enough that the fixed word changes again.")

if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv)>1 else 0.05)
