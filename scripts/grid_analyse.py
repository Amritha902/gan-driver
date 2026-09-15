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

    # ---- 4. the split, and what one comparator buys -----------------------
    # This is the number the deck leads with: of the total gain over a naive
    # baseline, how much is choosing the fixed word well (A) and how much is
    # adapting per corner (B)? And of B, how much can ONE real comparator on
    # ONE sensed quantity actually take? At n = 4 the answer was 25.1 / 3.9,
    # with one comparator taking 46 % of the 3.9.
    print("\n  4. THE SPLIT, AND WHAT ONE COMPARATOR BUYS")
    # THE BASELINE IS THE MEDIAN SAFE FIXED WORD, and getting this wrong
    # changes the answer by a factor of fifty.
    #
    # The first version measured the gain against the CONVENTIONAL word
    # (8,8,8,15n, no clamp, 0 V) and got (A) = 0.46 % against the deck's
    # 25.1 %. That is not a correction to the deck, it is a different
    # question asked badly: the conventional word is SAFE AT ONLY 9 OF THESE
    # 36 CORNERS, and scripts/decompose.py says in as many words that gains
    # against it are meaningless, because a driver that destroys the device
    # is not a cheaper driver.
    #
    # novelty.py -- which owns the 25.1 / 3.9 split -- uses the median of the
    # words that are safe EVERYWHERE, and says why: one baseline for every
    # percentage, because mixing baselines is how a share stops meaning
    # anything. Same baseline here.
    from statistics import median
    mean_cost = {w: sum(cost(by[c][w]) for c in corners) / len(corners)
                 for w in common}
    c_best = mean_cost[best_fixed]
    c_med = median(mean_cost.values())
    c_orc = sum(oracle.values()) / len(corners)
    base = c_med
    A = (c_med - c_best) / base * 100
    B = (c_best - c_orc) / base * 100
    print("     (A) choosing the fixed word well : %.2f %%   [deck: %.1f %%]"
          % (A, OLD["fixed"]))
    print("     (B) adapting per corner          : %.2f %%   [deck: %.1f %%]"
          % (B, OLD["adaptive"]))
    print("     B as a share of the total gain   : %.2f %%   [deck: %.1f %%]"
          % (B / (A + B) * 100 if A + B else 0, OLD["share"]))

    # one comparator: one threshold on one sensed quantity, two words
    best_split, best_gain = None, 0.0
    for idx, axis in ((0, "VBUS"), (1, "ILOAD"), (2, "TJ")):
        levels = sorted({parse_corner(c)[idx] for c in corners})
        for k in range(1, len(levels)):
            thr = levels[k]
            # `lo`/`hi` are taken: they hold the per-corner penalty range
            below = [c for c in corners if parse_corner(c)[idx] < thr]
            above = [c for c in corners if parse_corner(c)[idx] >= thr]
            if not below or not above:
                continue
            fl = set.intersection(*[set(feas[c]) for c in below])
            fh = set.intersection(*[set(feas[c]) for c in above])
            if not fl or not fh:
                continue
            wl = min(fl, key=lambda w: sum(cost(by[c][w]) for c in below))
            wh = min(fh, key=lambda w: sum(cost(by[c][w]) for c in above))
            tot = sum(cost(by[c][wl]) for c in below) + \
                  sum(cost(by[c][wh]) for c in above)
            gain = (c_best - tot / len(corners)) / base * 100
            if gain > best_gain:
                best_gain, best_split = gain, (axis, thr, wl, wh)
    if best_split:
        axis, thr, wl, wh = best_split
        print("     one comparator, %s at %s: takes %.2f %% of the %.2f %%"
              % (axis, thr, best_gain, B))
        print("       = %.0f %% of the adaptive part   [deck: 46 %%]"
              % (best_gain / B * 100 if B else 0))
        print("       below: %s" % ", ".join(wl))
        print("       above: %s" % ", ".join(wh))
        # The deck expresses the residual as a share of the TOTAL gain
        # (A + B), not of baseline -- that is where its 7.2 % comes from.
        # Quote it the same way or the two cannot be compared.
        tot_gain = A + B
        print("     residual a full sense + ADC + LUT must justify: %.2f %% of"
              % (B - best_gain))
        print("       baseline, = %.1f %% of the total gain   [deck: 7.2 %%]"
              % ((B - best_gain) / tot_gain * 100 if tot_gain else 0))

        # two comparators: two thresholds on any two axes, four regions. The
        # deck quotes 72 % from the four-corner study and it is the figure a
        # reviewer will press on, so it has to move with the rest.
        two_gain, two_desc = 0.0, None
        axes = ((0, "VBUS"), (1, "ILOAD"), (2, "TJ"))
        for (i1, a1), (i2, a2) in itertools.combinations(axes, 2):
            l1 = sorted({parse_corner(c)[i1] for c in corners})
            l2 = sorted({parse_corner(c)[i2] for c in corners})
            for t1 in l1[1:]:
                for t2 in l2[1:]:
                    regions, ok = [], True
                    for p1 in (False, True):
                        for p2 in (False, True):
                            g = [c for c in corners
                                 if (parse_corner(c)[i1] >= t1) == p1
                                 and (parse_corner(c)[i2] >= t2) == p2]
                            if not g:
                                continue
                            fs = set.intersection(*[set(feas[c]) for c in g])
                            if not fs:
                                ok = False
                                break
                            w = min(fs, key=lambda w: sum(cost(by[c][w])
                                                          for c in g))
                            regions.append(sum(cost(by[c][w]) for c in g))
                        if not ok:
                            break
                    if not ok:
                        continue
                    g2 = (c_best - sum(regions) / len(corners)) / base * 100
                    if g2 > two_gain:
                        two_gain, two_desc = g2, (a1, t1, a2, t2)
        if two_desc:
            a1, t1, a2, t2 = two_desc
            print("     two comparators, %s at %s and %s at %s: %.2f %% of "
                  "the %.2f %%" % (a1, t1, a2, t2, two_gain, B))
            print("       = %.0f %% of the adaptive part   [deck: 72 %%]"
                  % (two_gain / B * 100 if B else 0))
            print("       residual after two: %.2f %% of baseline, = %.1f %% "
                  "of the total gain   [deck: 3.7 %%]"
                  % (B - two_gain, (B - two_gain) / tot_gain * 100
                     if tot_gain else 0))
    else:
        print("     no single threshold splits these corners usefully")

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
        f.write("split: fixed %.2f %%, adaptive %.2f %% (deck: %.1f / %.1f)\n"
                % (A, B, OLD["fixed"], OLD["adaptive"]))
        if best_split:
            f.write("one comparator on %s at %s takes %.2f %% of the %.2f %%"
                    " (%.0f %%); residual %.2f %%\n"
                    % (best_split[0], best_split[1], best_gain, B,
                       best_gain / B * 100 if B else 0, B - best_gain))
    print("\n  wrote results/grid_analyse.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
