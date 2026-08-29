"""
emi_check.py -- does pull-up strength matter for quantities the cost ignores?

The paper claims drive-strength scheduling is worth 0.00 %. That claim is only
honest if drive strength also fails to move the things the cost function
leaves out - EMI and dV/dt - which is exactly what active gate drivers are
usually scheduled for.

Note the window: pull-up governs TURN-ON, so the oscillation energy must be
measured there. The project's standard E_osc metric windows the turn-off
event and cannot detect a pull-up effect at all.

Note also WHICH slew measure. scripts/emi_converge.py shows that peak dV/dt
does not converge with timestep (26 % spread over a 25x refinement) while the
10-90 % slew converges to 0.5 %. The peak is a peak of a ringing node, and
this project has already established that such peaks do not converge. Only
dvdt_1090 is quoted in any conclusion; dvdt_pk is printed for contrast, to
show that the non-convergent measure UNDERSTATES the effect three-fold.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from emi_sweep import emi_metrics
from multiprocessing import Pool


def job(npu):
    d, p = gansim.run_raw(cir="ideal", NPU_LS=npu, NPD_LS=8, NPD_HS=8,
                          CLKEN=1, VNEG=0, DT="15n")
    m = emi_metrics(d, p)
    return npu, m["E_osc_on"], m["dvdt_1090"], m["dvdt_pk"]


if __name__ == "__main__":
    print("  N_PU   turn-on E_osc   dV/dt 10-90%   (peak dV/dt)")
    with Pool(3) as p:
        res = sorted(p.map(job, [1, 2, 3, 4, 6, 8]))
    for n, e, d90, dpk in res:
        print("   %d        %8.1f       %7.1f V/ns     %7.1f" % (n, e, d90, dpk))
    span = lambda v: 100 * (max(v) - min(v)) / min(v)
    e, d90, dpk = ([r[i] for r in res] for i in (1, 2, 3))
    print("\n  across the pull-up range:")
    print("    turn-on ringing energy   spans %5.0f%%   (converged, 3.0%%)" % span(e))
    print("    10-90%% switch-node slew  spans %5.0f%%   (converged, 0.5%%)" % span(d90))
    print("    peak dV/dt               spans %5.0f%%   NOT CONVERGED - not quoted" % span(dpk))
    print("\n  Both convergent measures are absent from the cost function, and they")
    print("  move in OPPOSITE directions: the fastest pull-up gives the highest")
    print("  slew rate but the lowest ringing energy. The 0.00% scheduling value")
    print("  of pull-up is therefore scoped to a loss-and-overshoot objective and")
    print("  must be stated that way.")
