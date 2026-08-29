"""
verdict_stability.py -- does the FEASIBILITY verdict survive timestep refinement?

The robustness study's largest excursion is LLOOP_lo, which takes the ceiling
from 5.95 % to 13.54 %. That number is driven by the feasible set collapsing
from 474 words to 158 at the 200 V / 2 A / 125 degC corner. Feasibility is
margin = Vth - Vgs_spur > 0, and a spot check at that corner found Vgs_spur
drifting 26 % over a 25x timestep refinement - non-monotonically - while the
drain overshoot at the same operating point converged to 1.8 %.

So the quantity deciding the headline of Section IV may not be converged where
it matters. This tests that directly rather than by proxy: take the words
nearest the feasibility boundary, re-run each at the nominal timestep and at a
4x finer one, and count how many change verdict. A ceiling computed from a
feasible set that reshuffles under refinement is not a result.

Words far from the boundary cannot flip, so only |margin| < THRESH are tested.
"""
import csv, os, sys, re, subprocess, tempfile, shutil, time
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from flatten import inline

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THRESH = 0.6            # volts from the boundary
NSAMP  = 40             # words per case
FINE   = ("0.005n", "0.0125n")
COARSE = ("0.02n", "0.05n")
SUBS   = {"LLOOP_lo": ("LLOOP = 3n", "LLOOP = 1.5n"),
          "nominal":  None}
BASE = None


def build_base():
    global BASE
    BASE = inline(os.path.join(ROOT, "sim", "dpt.cir"))


def run(sub, step, tmax, p):
    src = BASE
    if sub:
        src = src.replace(sub[0], sub[1])
    block = "\n".join(".param %s=%s" % (k, v) for k, v in p.items())
    src = re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                 lambda m: m.group(1) + block + "\n" + m.group(2), src)
    src = re.sub(r"(?im)^\.tran\s+\S+(\s+\S+\s+\S+\s+)\S+(.*)$",
                 lambda m: ".tran %s%s%s%s" % (step, m.group(1), tmax, m.group(2)),
                 src, count=1)
    d = tempfile.mkdtemp(prefix="vstab_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=900)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        return gansim.metrics(np.loadtxt(f), p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def job(a):
    case, word = a
    p = dict(gansim.DEFAULTS)
    p.update(word); p.update(VBUS=200, ILOAD=2, TJ=125)
    sub = SUBS[case]
    c = run(sub, COARSE[0], COARSE[1], p)
    f = run(sub, FINE[0], FINE[1], p)
    if c is None or f is None:
        return None
    return dict(case=case, word=word,
                m_coarse=c["margin"], m_fine=f["margin"],
                v_coarse=c["Vgs_spur"], v_fine=f["Vgs_spur"])


def main():
    build_base()
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "robust.csv"))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        rows.append(r)

    jobs = []
    for case in SUBS:
        g = [r for r in rows if r["case"] == case and r["corner"] == "200V_2A_125C"]
        near = sorted(g, key=lambda r: abs(r["margin"]))[:NSAMP]
        for r in near:
            jobs.append((case, dict(NPU_LS=int(r["NPU_LS"]), NPD_LS=int(r["NPD_LS"]),
                                    NPD_HS=int(r["NPD_HS"]), DT=r["DT"],
                                    CLKEN=int(r["CLKEN"]), VNEG=int(r["VNEG"]))))
    print("testing %d words (%d per case) at 200V/2A/125C, %s vs %s"
          % (len(jobs), NSAMP, COARSE[1], FINE[1]), flush=True)

    t0, out = time.time(), []
    with Pool(2) as pool:                       # 2 workers: another run holds the rest
        for n, r in enumerate(pool.imap_unordered(job, jobs), 1):
            if r: out.append(r)
            if n % 20 == 0:
                print("  %d/%d  %.0fs" % (n, len(jobs), time.time() - t0), flush=True)

    print("\n  %-10s %7s %8s %10s   %s" % ("case", "tested", "flipped", "flip rate", "verdict"))
    for case in SUBS:
        g = [r for r in out if r["case"] == case]
        if not g: continue
        flips = [r for r in g if (r["m_coarse"] > 0) != (r["m_fine"] > 0)]
        rate = 100.0 * len(flips) / len(g)
        v = ("STABLE" if rate < 5 else
             "shaky" if rate < 15 else "UNSTABLE - feasible set is not determined")
        print("  %-10s %7d %8d %9.1f%%   %s" % (case, len(g), len(flips), rate, v))
        drift = sorted(abs(r["v_fine"] - r["v_coarse"]) for r in g)
        print("             median |dVgs_spur| %.4f V, worst %.4f V"
              % (drift[len(drift) // 2], drift[-1]))
    print("\n  These are the words NEAREST the boundary, so this is the worst case,")
    print("  not the average. A low flip rate here bounds the whole feasible set.")


if __name__ == "__main__":
    main()
