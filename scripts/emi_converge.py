"""
emi_converge.py -- do the EMI measures converge with timestep?

This project's own convergence finding is that integrals of a ringing node
converge with timestep refinement while PEAKS of it do not.  dvdt_pk is a
peak measure, so it is suspect by that rule; dvdt_1090 is an interval measure
and E_osc_on is a band integral, so both should hold up.  If dvdt_pk drifts
while the other two hold, no conclusion may rest on dvdt_pk.

Refines the maximum timestep over a decade and reports the spread of each
measure as a percentage of its own value at the finest step.
"""
import os, re, subprocess, sys, tempfile, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from emi_sweep import emi_metrics

# (print step, max internal step).  BOTH matter: the print step sets the
# sample spacing the gradient and the FFT see, the max step sets solver
# accuracy.  Nominal is the second row; the span is 25x.
STEPS = [("0.05n", "0.125n"),
         ("0.02n", "0.05n"),      # nominal, as used by every sweep
         ("0.01n", "0.025n"),
         ("0.005n", "0.0125n"),
         ("0.002n", "0.005n")]


def run_at(step, tmax, **kw):
    p = dict(gansim.DEFAULTS); p.update(kw)
    src = gansim._netlist(p, "ideal")
    src, n = re.subn(r"(?im)^\.tran\s+\S+(\s+\S+\s+\S+\s+)\S+(.*)$",
                     lambda m: ".tran %s%s%s%s" % (step, m.group(1), tmax, m.group(2)),
                     src, count=1)
    if not n:
        sys.exit("could not find the .tran line to refine")
    d = tempfile.mkdtemp(prefix="ganconv_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=3600)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        return emi_metrics(np.loadtxt(f), p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    npu = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    print("Timestep convergence of the turn-on EMI measures (N_PU=%d).\n" % npu)
    print("  %-18s %12s %12s %12s" % ("tstep / tmax", "E_osc_on", "dvdt_pk", "dvdt_1090"))
    got = []
    for st, tm in STEPS:
        lab = "%s / %s" % (st, tm)
        m = run_at(st, tm, NPU_LS=npu, NPD_LS=8, NPD_HS=8, CLKEN=1, VNEG=0, DT="15n")
        if m is None:
            print("  %-18s  FAILED" % lab); continue
        got.append((lab, m))
        print("  %-18s %12.2f %12.2f %12.2f"
              % (lab, m["E_osc_on"], m["dvdt_pk"], m["dvdt_1090"]), flush=True)
    if len(got) < 3:
        sys.exit("\ntoo few points to judge convergence")
    print("\n  spread relative to the finest step:")
    ref = got[-1][1]
    for k in ("E_osc_on", "dvdt_pk", "dvdt_1090"):
        v = [m[k] for _, m in got]
        sp = 100 * (max(v) - min(v)) / abs(ref[k]) if ref[k] else float("nan")
        verdict = "converged" if sp < 5 else ("marginal" if sp < 15 else "NOT converged")
        print("    %-12s %7.1f%%   %s" % (k, sp, verdict))
