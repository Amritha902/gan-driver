# -*- coding: utf-8 -*-
"""full_grid.py -- every control word at every operating point. n = 36.

    python3 scripts/full_grid.py           # resumes if interrupted

WHY THIS EXISTS
  The central claim of this project is a number: re-tuning the gate driver per
  operating point is worth 3.9 % of baseline, and most of that is reachable
  with one comparator. It was computed on FOUR corners.

  Four. And the leave-one-corner-out test that says a fitted schedule does not
  generalise is three training points and one held-out point, four times over.
  The deck says "n = 4, so this is weak evidence" and that is honest, but
  honesty about a weakness is not a substitute for removing it. No reviewer
  should be convinced by four points, and no amount of work on the slides
  changes that.

  scripts/corners.py already defines the full envelope -- VBUS x ILOAD x TJ =
  4 x 3 x 3 = 36 corners -- and then samples 4 of them. This runs all 36, at
  all 720 control words: 25,920 transients, about 4.4 hours on four cores.
  Compute is the cheapest thing this project has.

WHAT IT CHANGES
  Everything downstream gets a real sample instead of a token one:
    - the 3.9 % adaptive figure gets a spread across 36 points, not 4
    - the ceiling on scheduling stops being an average of four numbers
    - leave-one-corner-out becomes 36 folds instead of 4, which is the
      difference between a hint and a result
    - "does the best word move with the operating point" can be answered
      per axis -- bus, load, temperature -- instead of in aggregate

CHECKPOINTING IS NOT OPTIONAL
  This is a four-hour job in a container that has already been restarted once
  mid-run. Every completed corner is appended to the CSV and the header is
  written once, so a restart resumes at the corner boundary instead of
  starting over. A run that cannot survive its environment is a run that will
  not finish.
"""
import csv, itertools, os, sys, time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOM  = os.path.join(ROOT, "results", "sweep_nominal.csv")
OUT  = os.path.join(ROOT, "results", "full_grid.csv")

VBUS  = [50, 100, 150, 200]
ILOAD = [2, 5, 10]
TJ    = [25, 75, 125]
FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


def all_words():
    """Every distinct control word in the nominal sweep -- all 720."""
    words, seen = [], set()
    for r in csv.DictReader(open(NOM)):
        w = tuple(r[f] for f in FIELDS)
        if w in seen:
            continue
        seen.add(w)
        words.append({f: (r[f] if f == "DT" else int(float(r[f])))
                      for f in FIELDS})
    return words


def done_corners():
    if not os.path.exists(OUT):
        return set()
    return {r["corner"] for r in csv.DictReader(open(OUT))}


def job(a):
    word, vb, il, tj = a
    r = gansim.run(VBUS=vb, ILOAD=il, TJ=tj, **word)
    if r is None:
        return None
    r["corner"] = "%dV_%dA_%dC" % (vb, il, tj)
    return r


def main():
    words = all_words()
    corners = list(itertools.product(VBUS, ILOAD, TJ))
    have = done_corners()
    todo = [c for c in corners
            if "%dV_%dA_%dC" % c not in have]

    print("\n  THE FULL GRID")
    print("  %d control words x %d corners = %d transients"
          % (len(words), len(corners), len(words) * len(corners)))
    if have:
        print("  resuming: %d corner(s) already in %s"
              % (len(have), os.path.basename(OUT)))
    print("  %d corner(s) to run\n" % len(todo), flush=True)

    t0, total_bad = time.time(), 0
    for n, (vb, il, tj) in enumerate(todo, 1):
        name = "%dV_%dA_%dC" % (vb, il, tj)
        jobs = [(w, vb, il, tj) for w in words]
        rows, bad = [], 0
        with Pool(4) as pool:
            for r in pool.imap_unordered(job, jobs, chunksize=8):
                if r is None:
                    bad += 1
                else:
                    rows.append(r)
        total_bad += bad
        if not rows:
            print("  %-16s produced NOTHING -- not written" % name, flush=True)
            continue
        new = not os.path.exists(OUT)
        with open(OUT, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        el = time.time() - t0
        print("  %-16s %4d ok, %3d failed   [%d/%d, %.0f min elapsed, "
              "~%.0f min left]"
              % (name, len(rows), bad, n, len(todo), el / 60,
                 (el / n) * (len(todo) - n) / 60), flush=True)

    have = done_corners()
    print("\n  %d corners in %s, %d failed transients overall"
          % (len(have), os.path.basename(OUT), total_bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
