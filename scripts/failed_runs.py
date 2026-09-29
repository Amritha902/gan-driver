# -*- coding: utf-8 -*-
"""failed_runs.py -- account for every run the full grid did not produce.

results/full_grid.csv holds 25,911 rows where 720 words x 36 corners is
25,920. That gap sat in RESULTS-SUMMARY.txt as a bare count for weeks with
no explanation, which is the worst form for it to take: an examiner who
finds it before you do concludes the runs were dropped because they were
inconvenient.

This finds them, re-runs them, and reports what ngspice actually says.

    python3 scripts/failed_runs.py            # identify and diagnose
    python3 scripts/failed_runs.py --quick    # identify only, no re-run

What it found on 29.09.2026, and what the deck now states:

  * All 9 are reproducible. Re-running them fails again, every time, so they
    are not timeouts, not flakes and not a scheduling artefact.
  * The failure is the same in each: ngspice aborts the transient with
    "Timestep too small ... trouble with node hsg" at t ~ 2.004 us, which is
    the commutation instant. The solver cannot resolve the high-side gate
    node through that edge at those settings.
  * All 9 are HALF-FIXED settings -- clamp enabled with the off rail at 0 V,
    or the -2 V rail with the clamp disabled. None of the nine is the
    shipped configuration, which is both together.

That last point is why the gap does not touch the reported result: the
shipped word completes at all 36 corners. It is still a real limit on the
sweep and is stated as one.
"""
import collections
import csv
import os
import subprocess
import sys
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

GRID = os.path.join(ROOT, "results", "full_grid.csv")
OUT = os.path.join(ROOT, "results", "failed_runs.txt")

# The columns that together name one point in the sweep. NPU_HS, RUNIT and
# VDRV are constant across the grid but are included so that a future sweep
# that varies them cannot make two different points look like one.
ALL = ["NPU_LS", "NPD_LS", "NPU_HS", "NPD_HS", "DT", "CLKDEL",
       "CLKEN", "VNEG", "RUNIT", "VDRV"]
# The subset gansim.run() actually takes.
ARGS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]

EXPECT_WORDS, EXPECT_CORNERS = 720, 36


def find_missing():
    """Every (corner, setting) in the grid's own cross product with no row."""
    rows = list(csv.DictReader(open(GRID)))
    words = {tuple(r[f] for f in ALL) for r in rows}
    corners = sorted({r["corner"] for r in rows})
    if len(words) != EXPECT_WORDS or len(corners) != EXPECT_CORNERS:
        raise SystemExit("failed_runs: grid is %d words x %d corners, not "
                         "%d x %d -- the sweep changed shape, so this "
                         "accounting is stale"
                         % (len(words), len(corners),
                            EXPECT_WORDS, EXPECT_CORNERS))
    per = collections.Counter(r["corner"] for r in rows)
    missing = []
    for c in corners:
        if per[c] == EXPECT_WORDS:
            continue
        have = {tuple(r[f] for f in ALL) for r in rows if r["corner"] == c}
        for m in sorted(words - have):
            missing.append((c, dict(zip(ALL, m))))
    expected = EXPECT_WORDS * EXPECT_CORNERS
    if len(rows) + len(missing) != expected:
        raise SystemExit("failed_runs: %d rows + %d missing != %d -- there "
                         "are duplicate rows in the grid"
                         % (len(rows), len(missing), expected))
    return rows, missing


def diagnose(corner, word):
    """Re-run one point and return (reproduced, ngspice's own complaint)."""
    import gansim
    vb, il, tj = corner.split("_")
    p = dict(gansim.DEFAULTS)
    p.update({f: (word[f] if f == "DT" else int(float(word[f])))
              for f in ARGS})
    p.update(VBUS=int(vb[:-1]), ILOAD=int(il[:-1]), TJ=int(tj[:-1]))
    d = tempfile.mkdtemp(prefix="failed_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(gansim._netlist(p, None))
        r = subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                           capture_output=True, text=True, timeout=900)
        why = ""
        for line in (r.stderr or "").splitlines():
            if "Timestep too small" in line or "aborted" in line:
                why = line.strip()
                if "Timestep too small" in line:
                    break
        # A point that now succeeds is a different and worse problem than
        # one that fails: it would mean the grid is not reproducible.
        f = os.path.join(d, "out.dat")
        ok = os.path.exists(f) and os.path.getsize(f) > 1000 and not why
        return ok, why or "(no ngspice error; run completed)"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv):
    quick = "--quick" in argv
    rows, missing = find_missing()
    total = EXPECT_WORDS * EXPECT_CORNERS

    out = []
    def say(s=""):
        print(s, flush=True)
        out.append(s)

    say("  RUNS ACCOUNTED FOR")
    say("  " + "-" * 68)
    say("  %d of %d completed; %d did not (%.3f %%)"
        % (len(rows), total, len(missing), 100.0 * len(missing) / total))
    say()

    shipped = [m for _, m in missing
               if int(float(m["CLKEN"])) == 1 and float(m["VNEG"]) < 0]
    say("  of the %d: %d are the shipped configuration "
        "(clamp on AND -2 V rail)" % (len(missing), len(shipped)))
    say("               %d are clamp on with the off rail at 0 V"
        % len([m for _, m in missing
               if int(float(m["CLKEN"])) == 1 and float(m["VNEG"]) == 0]))
    say("               %d are the -2 V rail with the clamp off"
        % len([m for _, m in missing
               if int(float(m["CLKEN"])) == 0 and float(m["VNEG"]) < 0]))
    say()

    if quick:
        for c, m in missing:
            say("  %-16s  %s" % (c, "  ".join("%s=%s" % (k, m[k])
                                              for k in ARGS)))
        say()
        say("  (--quick: not re-run)")
    else:
        say("  re-running each one:")
        reproduced = 0
        whys = collections.Counter()
        for c, m in missing:
            ok, why = diagnose(c, m)
            reproduced += not ok
            whys[why.split(";")[0][:60]] += 1
            say("  %-16s  %-46s  %s"
                % (c, "  ".join("%s=%s" % (k, m[k]) for k in ARGS),
                   "completed this time" if ok else "failed again"))
        say()
        say("  %d of %d failed again -- reproducible, not flaky"
            % (reproduced, len(missing)))
        say()
        say("  what ngspice says:")
        for why, n in whys.most_common():
            say("    %2d x  %s" % (n, why))

    say()
    if shipped:
        say("  WARNING: %d of the aborted runs ARE the shipped "
            "configuration. The reported result rests on runs that did "
            "not all complete." % len(shipped))
    else:
        say("  None of the aborted runs is the shipped configuration, so "
            "the reported result does not rest on any of them. The gap is "
            "a real limit on the SWEEP's coverage and is stated as one.")

    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n  wrote %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
