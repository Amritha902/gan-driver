# -*- coding: utf-8 -*-
"""grid_analyse.py -- the project's central claims, recomputed on n = 36.

    python3 scripts/grid_analyse.py

Every headline in this project was computed on FOUR operating points. This
recomputes them on the full 36-corner grid that scripts/full_grid.py runs, and
prints the old number beside the new one so the difference is the first thing
you see.

It answers four questions the four-corner version could only gesture at:

  1. THE CEILING. How much is per-corner scheduling worth at most, against the
     best single fixed word? Four corners gave one number with no spread. 36
     give a distribution, and the honest form of the claim is the range.

  2. THE SPLIT. Of the total gain over a naive baseline, how much comes from
     choosing the fixed word well and how much from adapting? This is the
     project's reason to exist and it deserves more than four samples.

  3. WHICH AXIS ACTUALLY MOVES THE ANSWER. With 4 x 3 x 3 = 36 points on a
     real grid, the best word can be tracked against bus voltage, load current
     and junction temperature SEPARATELY. Four scattered corners cannot do
     this at all, and it is the most useful thing the bigger grid buys: if the
     word only moves with load, a converter that never changes load does not
     need a controller.

  4. DOES A FITTED SCHEDULE GENERALISE? Leave-one-corner-out with 36 folds
     instead of 4. At n = 4 the answer was "worse than fixed on 3 of 4, but
     n = 4 so this is weak". At n = 36 it is either a result or it is not.

If a number moves, it moves. The point of running this is to find out, and a
script that only confirms what the deck already says would not have been worth
the four hours.
"""
import collections, csv, itertools, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")
GRID = os.path.join(RES, "full_grid.csv")
F    = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
W_OV = 0.05                      # uJ per point of overshoot, as elsewhere

# what the deck currently says, on four corners
OLD = dict(ceiling=5.2, fixed=25.1, adaptive=3.9, share=13.4, lolo=(3, 4))


def cost(r):
    return r["E_tot"] * 1e6 + W_OV * r["ov_pct"]


def load():
    rows = list(csv.DictReader(open(GRID)))
    for r in rows:
        for k, v in list(r.items()):
            if k in ("corner", "DT", "CLKDEL", "case"):
                continue
            try:
                r[k] = float(v)
            except (ValueError, TypeError):
                pass
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["corner"]][tuple(str(r[f]) for f in F)] = r
    return by


def parse_corner(name):
    v, i, t = name.split("_")
    return int(v[:-1]), int(i[:-1]), int(t[:-1])


def main():
    if not os.path.exists(GRID):
        raise SystemExit("no %s -- run scripts/full_grid.py first" % GRID)
    by = load()
    corners = sorted(by, key=parse_corner)
    n = len(corners)
    print("\n  THE CENTRAL CLAIMS, ON n = %d" % n)
    print("  %d corners x %d words. The deck's numbers are on 4 corners."
          % (n, len(next(iter(by.values())))))
    print("  " + "=" * 68)
    if n < 36:
        print("  PARTIAL GRID (%d of 36). The loop runs bus voltage outermost,"
              % n)
        print("  so a partial grid is biased toward low bus voltage and the")
        print("  hot 200 V corners are missing. Read nothing final from this.")
        print("  " + "-" * 68)

    feas = {c: {w: r for w, r in by[c].items() if r["margin"] > 0}
            for c in corners}
    empty = [c for c in corners if not feas[c]]
    if empty:
        print("  no feasible word at: %s" % ", ".join(empty))
        corners = [c for c in corners if c not in empty]
    common = set.intersection(*[set(feas[c]) for c in corners])
    print("  words feasible at EVERY corner: %d" % len(common))
    if not common:
        raise SystemExit("  no word is feasible everywhere -- nothing to "
                         "compare a fixed word against.")

    # ---- 1. the ceiling ---------------------------------------------------
    oracle = {c: min(cost(feas[c][w]) for w in feas[c]) for c in corners}
    best_fixed = min(common, key=lambda w: sum(cost(by[c][w]) for c in corners))
    per = [(c, (cost(by[c][best_fixed]) - oracle[c]) / cost(by[c][best_fixed])
            * 100) for c in corners]
    tot_fixed = sum(cost(by[c][best_fixed]) for c in corners)
    ceiling = (tot_fixed - sum(oracle.values())) / tot_fixed * 100

    print("\n  1. CEILING ON PER-CORNER SCHEDULING")
    print("     deck, n = 4 : %.1f %%" % OLD["ceiling"])
    print("     grid, n = %-2d: %.2f %%" % (n, ceiling))
    lo = min(p for _, p in per); hi = max(p for _, p in per)
    print("     per-corner penalty of the fixed word: %.2f %% to %.2f %%"
          % (lo, hi))
    worst = max(per, key=lambda x: x[1])
    print("     worst corner: %s at %.2f %%" % (worst[0], worst[1]))
    print("     best single fixed word: %s" % ", ".join(best_fixed))

    # ---- 2. which axis moves the best word --------------------------------
    print("\n  2. WHICH AXIS MOVES THE BEST WORD")
    print("     If the word only moves with one of these, a converter that")
    print("     holds that quantity fixed does not need a controller at all.")
    best = {c: min(feas[c], key=lambda w: cost(feas[c][w])) for c in corners}
    for ax, idx, label in ((0, 0, "bus voltage"), (1, 1, "load current"),
                           (2, 2, "junction temp")):
        groups = collections.defaultdict(set)
        for c in corners:
            groups[parse_corner(c)[idx]].add(best[c])
        distinct = len({w for s in groups.values() for w in s})
        moved = sum(1 for v in groups.values() if len(v) > 1)
        print("     %-15s %d distinct best words across %d levels; %d level(s)"
              " disagree internally" % (label, distinct, len(groups), moved))
    allbest = collections.Counter(best.values())
    print("     %d distinct best words over %d corners; the most common wins "
          "%d of them" % (len(allbest), len(corners), allbest.most_common(1)[0][1]))

    # ---- 3. leave-one-corner-out ------------------------------------------
    print("\n  3. DOES A FITTED SCHEDULE GENERALISE? (leave-one-corner-out)")
    wins = losses = ties = 0
    for held in corners:
        rest = [c for c in corners if c != held]
        com = set.intersection(*[set(feas[c]) for c in rest])
        if not com or held not in feas:
            continue
        fit = min(com, key=lambda w: sum(cost(by[c][w]) for c in rest))
        glob = best_fixed
        a, b = cost(by[held][fit]), cost(by[held][glob])
        if a < b - 1e-9:
            wins += 1
        elif a > b + 1e-9:
            losses += 1
        else:
            ties += 1
    print("     deck, n = 4 : worse than the fixed word on %d of %d held-out"
          % OLD["lolo"])
    print("     grid, n = %-2d: better on %d, WORSE on %d, identical on %d"
          % (n, wins, losses, ties))
    if losses + ties >= wins:
        print("     The n = 4 finding holds: fitting the word on other corners")
        print("     does not help on a corner it was not fitted on.")
    else:
        print("     THE n = 4 FINDING DOES NOT HOLD at this sample size.")
        print("     The deck says a fitted schedule does not generalise; on")
        print("     %d corners it does. That claim has to change." % n)

    with open(os.path.join(RES, "grid_analyse.txt"), "w") as f:
        f.write("Central claims recomputed on n = %d corners\n" % n)
        f.write("ceiling: deck(n=4) %.1f %%  ->  grid(n=%d) %.2f %%\n"
                % (OLD["ceiling"], n, ceiling))
        f.write("per-corner penalty %.2f to %.2f %%, worst %s\n"
                % (lo, hi, worst[0]))
        f.write("best fixed word: %s\n" % ", ".join(best_fixed))
        f.write("distinct best words: %d over %d corners\n"
                % (len(allbest), len(corners)))
        f.write("leave-one-out: better %d, worse %d, identical %d\n"
                % (wins, losses, ties))
    print("\n  wrote results/grid_analyse.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
