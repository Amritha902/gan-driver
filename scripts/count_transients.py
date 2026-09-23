# -*- coding: utf-8 -*-
"""count_transients.py -- how many ngspice runs this project actually did,
derived from the result files rather than remembered.

    python3 scripts/count_transients.py

WHY THIS EXISTS
  The deck claimed 60,533 transients for six weeks. The real number is
  66,924. The claim was correct when it was typed, on 15 September; it
  stopped being correct the moment the device Monte-Carlo, the envelope
  sweep and the panel metrics were added, and nothing re-derived it.

  review/check_consistency.py passed it on every run, because what that
  check does is confirm the string "60533" appears both on a slide and in
  RESULTS-SUMMARY.txt. Text agreeing with text is not the same as either
  agreeing with the data. A number that is wrong in both places passes.

  So this recomputes it from the files and writes the answer where the deck
  reads it. A stale count is now a build failure rather than a slide.

WHAT COUNTS AS A TRANSIENT
  One row of a sweep CSV is one ngspice transient, because that is how the
  sweeps are written: one simulated operating point per row.

  Two files are counted twice per row, because they genuinely run two
  simulations per row and say so in their own source: panel_metrics.py and
  envelope_sweep.py each do a 150-cycle power run at 0.2 ns AND a 3-cycle
  edge run at 0.02 ns, since an averaged power and a sub-nanosecond edge
  cannot come off one transient.

WHAT IS EXCLUDED, AND WHY
  closedloop_wave.csv is 4,000 rows of ONE run's waveform -- time points,
  not simulations. Counting it would inflate the total by 4,000 and would
  be the single most dishonest thing in this repository.

  robust_all.csv duplicates robust.csv; sweep_matlab.csv is sweep_nominal.csv
  re-exported for MATLAB; the .csv.gz files are compressed copies of their
  .csv twins. Counting any of them would be double counting.
"""
import csv, gzip, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

# (file, runs-per-row, what it is)
COUNTED = [
    ("full_grid.csv",              1, "720 control words x 36 operating points"),
    ("robust.csv",                 1, "robustness sweep"),
    ("lloop_sweep.csv.gz",         1, "loop-inductance sweep"),
    ("robust_fix.csv",             1, "robustness re-run after the fix"),
    ("device_mc_full_dev18.csv.gz",1, "device 18 re-run on the full grid"),
    ("device_mc.csv",              1, "device Monte-Carlo, 24 devices"),
    ("full_corners.csv",           1, "corner sweep"),
    ("corners.csv",                1, "the original 4-corner study"),
    ("emi_sweep.csv.gz",           1, "EMI sweep"),
    ("sweep_nominal.csv",          1, "720 words at the nominal corner"),
    ("cases.csv",                  1, "named cases"),
    ("buck_sweep.csv",             1, "converter sweep"),
    ("envelope_sweep.csv",         2, "envelope sweep: one power + one edge run per point"),
    ("sky130_drive_strength.csv",  1, "SKY130 transistor-level characterisation"),
    ("headtohead.csv",             1, "head to head against the base paper"),
    ("panel_metrics.csv",          2, "panel metrics: one power + one edge run per config"),
]

EXCLUDED = [
    ("closedloop_wave.csv", "4,000 time points of ONE run's waveform, not 4,000 runs"),
    ("robust_all.csv",      "duplicate of robust.csv"),
    ("sweep_matlab.csv",    "sweep_nominal.csv re-exported for MATLAB"),
    ("full_grid.csv.gz",    "compressed copy of full_grid.csv"),
    ("device_mc.csv.gz",    "compressed copy of device_mc.csv"),
]


def rows(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as fh:
        return max(0, sum(1 for _ in fh) - 1)


def main():
    total, lines, missing = 0, [], []
    lines.append("")
    lines.append("  TRANSIENT COUNT -- derived from the result files, not typed")
    lines.append("  One row of a sweep CSV is one ngspice run. Two files run twice")
    lines.append("  per row (a power run and an edge run) and are marked x2.")
    lines.append("  " + "-" * 74)
    for f, mult, what in COUNTED:
        p = os.path.join(RES, f)
        if not os.path.exists(p):
            missing.append(f)
            lines.append("  %-30s   MISSING   %s" % (f, what))
            continue
        n = rows(p)
        total += n * mult
        lines.append("  %-30s %7d%s  %s"
                     % (f, n, "  x2" if mult == 2 else "    ", what))
    lines.append("  " + "-" * 74)
    lines.append("  TOTAL  %d transient simulations" % total)
    lines.append("")
    lines.append("  Excluded, and why:")
    for f, why in EXCLUDED:
        lines.append("    %-24s %s" % (f, why))
    lines.append("")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(RES, "transient_count.txt"), "w").write(txt + "\n")
    with open(os.path.join(RES, "transient_count.value"), "w") as fh:
        fh.write("%d\n" % total)
    print("  written: results/transient_count.txt and .value")
    if missing:
        print("  WARNING: %d file(s) missing; the total is a lower bound" % len(missing))
    return total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
