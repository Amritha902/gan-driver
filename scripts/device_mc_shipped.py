# -*- coding: utf-8 -*-
"""device_mc_shipped.py -- the device-spread safety claim, on the word we ship.

    python3 scripts/device_mc_shipped.py

WHY THIS EXISTS, AND WHAT IT CORRECTS
device_mc.py samples 36 candidate words out of the 720 so that 24 devices can
be compared like with like. That set is a sample, not a cross product, and
checking it afterwards showed something nobody had checked while it ran: the
one configuration the project actually ships -- all eight slices, 15 ns dead
time, Miller clamp on, -2 V off rail, the word the headline +2.576 V margin is
measured on -- is NOT in it.

What device_mc.py labelled SHIPPED is (8, 8, 1, 25n, 1, -2): a weak high-side
pull-down and a longer dead time. It is a safe word, but it is not the one the
deck, the paper and sim/dpt.cir run. So the population-level safety claim was
resting on a neighbour of the shipped word rather than on the shipped word.

This runs the shipped word itself, on the same 24 sampled devices and the same
four corners -- 96 transients -- so the safety claim and the headline number
describe the same circuit. It writes a separate file and does not touch
device_mc.csv: that study's word set is what makes its devices comparable, and
adding one word to it after the fact would break that.

Scope: this is the SAFETY claim only (does any device false-turn-on). The
decomposition (A vs B) still needs the candidate set, and device_mc_analyse.py
still owns it.
"""
import csv, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import device_mc as MC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "device_mc_shipped.csv")

# The word every headline number in the deck and the paper is measured on.
SHIPPED_WORD = dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=1, VNEG=-2)
# What device_mc.py called SHIPPED, kept so the two can be compared directly.
MC_SHIPPED   = dict(NPU_LS=8, NPD_LS=8, NPD_HS=1, DT="25n", CLKEN=1, VNEG=-2)

FIELDS = ["word", "dev", "VBUS", "ILOAD", "TJ", "NPU_LS", "NPD_LS", "NPD_HS",
          "DT", "CLKEN", "VNEG", "E_tot", "ov_pct", "margin", "Vgs_spur_hs"]


def main():
    MC.build_base()
    devs = MC.sample_devices(MC.N_DEVICES)
    words = [("shipped", SHIPPED_WORD), ("device_mc_SHIPPED", MC_SHIPPED)]

    # Smoke-test one job before spending the rest. device_mc.py's first
    # version returned None for every metric while the run looked healthy;
    # one job checked up front is what catches that.
    probe = MC.job((devs[0], SHIPPED_WORD, MC.CORNERS[0]))
    if "error" in probe or probe.get("margin") is None:
        print("SMOKE TEST FAILED: %r" % (probe,)); return 1
    print("smoke test ok: margin %+.3f V" % float(probe["margin"]), flush=True)

    jobs = [(name, d, w, c) for name, w in words
            for d in devs for c in MC.CORNERS]
    print("%d transients (%d devices x %d corners x %d words)"
          % (len(jobs), len(devs), len(MC.CORNERS), len(words)), flush=True)

    t0 = time.time()
    with open(OUT, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        wr.writeheader()
        bad = 0
        with Pool(4) as pool:
            for (name, _, _, _), r in zip(
                    jobs, pool.imap(_run, jobs, chunksize=2)):
                if "error" in r:
                    bad += 1
                    print("  FAILED %s dev%s: %s" % (name, r.get("dev"),
                                                     r["error"]), flush=True)
                    continue
                r["word"] = name
                wr.writerow(r)
    print("%d failed of %d, %.0fs -> %s"
          % (bad, len(jobs), time.time() - t0, os.path.relpath(OUT, ROOT)))
    return 0


def _run(a):
    _, dev, word, corner = a
    return MC.job((dev, word, corner))


if __name__ == "__main__":
    sys.exit(main())
