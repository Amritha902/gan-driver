"""
metric_converge.py -- do the metrics the CONCLUSIONS rest on converge?

Section 24 rejected peak dV/dt because peaks of a ringing node do not converge.
That rule has an uncomfortable consequence that has to be faced directly:

    cost     = E_tot + w_ov * ov_pct        <- ov_pct is a PEAK of V_DS
    feasible = margin > 0, margin = Vth - Vgs_spur   <- also a PEAK

Both are peaks. Every headline in the paper - the 5.2 % ceiling, the freeze
test, the guard-band table - is computed from them. If they drift with
timestep the way peak dV/dt does, the conclusions inherit that drift.

The difference the rule actually turns on is not "peak vs integral" but
whether the quantity is a peak OF A RINGING SIGNAL. The V_DS overshoot peak
lands on the first, largest excursion after turn-off, and the spurious gate
peak is a single capacitively-coupled hump, not a resonant tail. Both should
be far better behaved than a slew rate measured on the ringing edge. This
checks whether that reasoning survives contact with the solver, over the same
25x refinement used in Section 24.
"""
import os, re, subprocess, sys, tempfile, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

STEPS = [("0.05n", "0.125n"), ("0.02n", "0.05n"), ("0.01n", "0.025n"),
         ("0.005n", "0.0125n"), ("0.002n", "0.005n")]
# E_tot/E_off are in joules; scale to uJ so the printed table is readable.
KEYS  = ["E_tot", "E_off", "ov_pct", "Vds_pk", "margin", "Vgs_spur"]
SCALE = {"E_tot": 1e6, "E_off": 1e6}


def run_at(step, tmax, **kw):
    p = dict(gansim.DEFAULTS); p.update(kw)
    src = gansim._netlist(p, "ideal")
    src, n = re.subn(r"(?im)^\.tran\s+\S+(\s+\S+\s+\S+\s+)\S+(.*)$",
                     lambda m: ".tran %s%s%s%s" % (step, m.group(1), tmax, m.group(2)),
                     src, count=1)
    if not n: sys.exit("could not find the .tran line")
    d = tempfile.mkdtemp(prefix="ganmc_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=3600)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000: return None
        return gansim.metrics(np.loadtxt(f), p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    # the word the ceiling result actually selects, at the nominal corner
    kw = dict(NPU_LS=8, NPD_LS=8, NPD_HS=1, DT="25n", CLKEN=1, VNEG=0)
    if len(sys.argv) > 1 and sys.argv[1] == "worstcase":
        # the marginal word: no clamp, fastest drive - where a false-turn-on
        # verdict is decided by tenths of a volt
        kw = dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=0, VNEG=0)
    print("Timestep convergence of the metrics the conclusions rest on.")
    print("word: %s\n" % kw)
    print("  %-18s" % "tstep / tmax"
          + "".join("%11s" % (k + " uJ" if k in SCALE else k) for k in KEYS))
    got = []
    for st, tm in STEPS:
        m = run_at(st, tm, **kw)
        lab = "%s / %s" % (st, tm)
        if m is None:
            print("  %-18s  FAILED" % lab); continue
        got.append(m)
        print("  %-18s" % lab + "".join("%11.4f" % (m[k] * SCALE.get(k, 1))
                                        for k in KEYS), flush=True)
    if len(got) < 3: sys.exit("\ntoo few points")
    print("\n  spread relative to the finest step:")
    for k in KEYS:
        v = [m[k] for m in got]
        ref = abs(got[-1][k]) or 1.0
        sp = 100 * (max(v) - min(v)) / ref
        verdict = "converged" if sp < 5 else ("marginal" if sp < 15 else "NOT converged")
        # margin is Vth - Vgs_spur, a small difference of two larger numbers, so
        # a percentage of it exaggerates. Give the absolute drift as well: that
        # is what a feasibility verdict at a 0.36 V or 1 V guard band cares about.
        extra = ""
        if k in ("margin", "Vgs_spur", "ov_pct", "Vds_pk"):
            extra = "   (%.4f absolute)" % (max(v) - min(v))
        print("    %-10s %8.2f%%   %-13s%s" % (k, sp, verdict, extra))
