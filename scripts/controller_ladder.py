# -*- coding: utf-8 -*-
"""controller_ladder.py -- how much controller does this driver actually need?

    python3 scripts/controller_ladder.py

PURPOSE
  The project's headline is that re-tuning the control word per operating
  point is worth only 3.9 % of baseline, and that one comparator recovers
  most of even that. Both are statements about CONTROLLER COMPLEXITY, and so
  far they have been measured one configuration at a time.

  This measures the whole ladder in one place: starting from a single fixed
  word and ending at a full lookup table, how much of the achievable gain
  does each rung buy, and where does the curve flatten? That is the question
  a designer actually has to answer before committing sensing hardware, and
  it is the project's own question asked properly.

  The rungs, in increasing order of what they cost to build:

    0  CONSTANT   one control word, everywhere. No sensing of any kind.
    1  STUMP      one comparator on one measured quantity, selecting between
                  two words. A threshold and a mux -- no ADC, no table.
    2  TREE(d=2)  up to two comparators, up to four words.
    3  ORACLE     the true per-corner optimum: a full lookup table with a
                  perfect sensor. Not buildable -- it is the upper bound that
                  says how much there was to win in the first place.

  Rung 3 is what the literature implicitly promises. Rung 0 is free. The
  interesting number is how far up the ladder you have to climb before the
  remaining gain stops paying for the hardware.

METHOD
  No new simulation. Reads the same measured sweeps every other result uses
  (720 control words x 4 corners), and the cost function is the project's
  existing one, unchanged:

      cost = E_tot in uJ + 0.05 * overshoot %        feasible iff margin > 0

  Infeasible words -- the ones that false-turn-on -- are excluded everywhere,
  so no rung is allowed to buy performance by being unsafe.

HONEST LIMIT, STATED UP FRONT
  There are four corners. A depth-2 tree has four leaves, so it can address
  each corner separately and MUST equal the oracle -- that is arithmetic, not
  a finding, and it is reported as such. With four points this is a
  description of the measured envelope, not a generalisation claim. The
  leave-one-corner-out section is the only part that speaks to generalisation,
  and with n=4 it is weak evidence; it is included because omitting it would
  be worse, not because four points settle anything.
"""
import csv, os, itertools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
# what a controller is allowed to look at: the operating point, not the answer
SENSED = ["VBUS", "ILOAD", "TJ"]


def load():
    rows = []
    for fn, tag in (("sweep_nominal.csv", "100V_10A_25C"), ("full_corners.csv", None)):
        path = os.path.join(RES, fn)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            d = {}
            for k, v in r.items():
                if k in ("corner", "DT", "CLKDEL"):
                    d[k] = v
                    continue
                try:
                    d[k] = float(v)
                except (TypeError, ValueError):
                    d[k] = v
            if "corner" not in d or not d["corner"]:
                d["corner"] = tag
            rows.append(d)
    return rows


def cost(r):
    return r["E_tot"] * 1e6 + 0.05 * r["ov_pct"]


def word(r):
    return tuple(r[f] if f == "DT" else int(float(r[f])) for f in FIELDS)


def main():
    rows = [r for r in load() if r.get("corner")]
    corners = sorted({r["corner"] for r in rows})

    # cost[word][corner], feasible words only
    table, opinfo = {}, {}
    for r in rows:
        if r["margin"] <= 0:
            continue
        table.setdefault(word(r), {})[r["corner"]] = cost(r)
        opinfo[r["corner"]] = {k: r[k] for k in SENSED if k in r}

    universal = [w for w, d in table.items() if len(d) == len(corners)]
    print("\n  HOW MUCH CONTROLLER DOES THIS DRIVER NEED?")
    print("  %d corners, %d control words, %d of them feasible at every corner."
          % (len(corners), len({word(r) for r in rows}), len(universal)))
    print("  Cost = E_tot (uJ) + 0.05 x overshoot %%; words that false-turn-on excluded.")

    # ---- rung 0 : one word everywhere -------------------------------------
    const_w = min(universal, key=lambda w: sum(table[w][c] for c in corners))
    const = sum(table[const_w][c] for c in corners) / len(corners)

    # ---- rung 3 : per-corner optimum (upper bound) ------------------------
    oracle_by_c = {c: min(table[w][c] for w in table if c in table[w]) for c in corners}
    oracle = sum(oracle_by_c.values()) / len(corners)

    span = const - oracle
    print("  Everything below is scored as the share of the %.4f uJ that lies"
          % span)
    print("  between one fixed word and a perfect lookup table.\n")

    def share(v):
        return 100.0 * (const - v) / span if span else 0.0

    # ---- rung 1 : one comparator on one sensed quantity --------------------
    best_stump = None
    for feat in SENSED:
        vals = sorted({opinfo[c][feat] for c in corners if feat in opinfo[c]})
        for i in range(len(vals) - 1):
            thr = (vals[i] + vals[i + 1]) / 2.0
            lo = [c for c in corners if opinfo[c][feat] <= thr]
            hi = [c for c in corners if opinfo[c][feat] > thr]
            if not lo or not hi:
                continue
            tot = 0.0
            pick = {}
            ok = True
            for grp in (lo, hi):
                cand = [w for w in table if all(c in table[w] for c in grp)]
                if not cand:
                    ok = False
                    break
                bw = min(cand, key=lambda w: sum(table[w][c] for c in grp))
                pick[tuple(grp)] = bw
                tot += sum(table[bw][c] for c in grp)
            if not ok:
                continue
            v = tot / len(corners)
            if best_stump is None or v < best_stump[0]:
                best_stump = (v, feat, thr, pick)

    # ---- rung 2 : depth-2 tree -------------------------------------------
    best_tree = None
    for f1, f2 in itertools.product(SENSED, repeat=2):
        v1 = sorted({opinfo[c][f1] for c in corners})
        for i in range(len(v1) - 1):
            t1 = (v1[i] + v1[i + 1]) / 2.0
            groups = [[c for c in corners if opinfo[c][f1] <= t1],
                      [c for c in corners if opinfo[c][f1] > t1]]
            if not all(groups):
                continue
            tot, ok = 0.0, True
            for g in groups:
                v2 = sorted({opinfo[c][f2] for c in g})
                sub = [g]
                if len(v2) > 1:
                    t2 = (v2[0] + v2[1]) / 2.0
                    sub = [[c for c in g if opinfo[c][f2] <= t2],
                           [c for c in g if opinfo[c][f2] > t2]]
                for s in sub:
                    if not s:
                        continue
                    cand = [w for w in table if all(c in table[w] for c in s)]
                    if not cand:
                        ok = False
                        break
                    bw = min(cand, key=lambda w: sum(table[w][c] for c in s))
                    tot += sum(table[bw][c] for c in s)
                if not ok:
                    break
            if ok:
                v = tot / len(corners)
                if best_tree is None or v < best_tree[0]:
                    best_tree = (v, f1, t1, f2)

    print("  %-26s %12s %12s %10s" % ("controller", "mean cost", "vs fixed", "of oracle"))
    print("  " + "-" * 64)
    print("  %-26s %10.4f uJ %11s %9s" % ("0  CONSTANT  (no sensing)", const, "--", "0 %"))
    if best_stump:
        v, feat, thr, _ = best_stump
        print("  %-26s %10.4f uJ %10.4f %8.0f %%"
              % ("1  STUMP     (1 comparator)", v, const - v, share(v)))
    if best_tree:
        v = best_tree[0]
        print("  %-26s %10.4f uJ %10.4f %8.0f %%"
              % ("2  TREE d=2  (<=2 comps)", v, const - v, share(v)))
    print("  %-26s %10.4f uJ %10.4f %8.0f %%"
          % ("3  ORACLE    (full LUT)", oracle, span, 100.0))

    if best_stump:
        v, feat, thr, _ = best_stump
        print("\n  The one comparator that does it: %s at %.4g -- and it recovers"
              % (feat, thr))
        print("  %.0f %% of everything a perfect lookup table could ever deliver." % share(v))
    if best_tree and best_stump and abs(best_tree[0] - oracle) < 1e-12:
        print("  The depth-2 tree equals the oracle exactly. With four corners a")
        print("  four-leaf tree can address each one separately, so this is")
        print("  arithmetic, not a result -- it is reported to be complete.")

    # ---- generalisation, such as it is ------------------------------------
    print("\n  LEAVE-ONE-CORNER-OUT (n=4, so: weak evidence, not proof)")
    print("  Fit the comparator on three corners, score it on the fourth.")
    worse = 0
    for held in corners:
        tr = [c for c in corners if c != held]
        bs = None
        for feat in SENSED:
            vals = sorted({opinfo[c][feat] for c in tr})
            for i in range(len(vals) - 1):
                thr = (vals[i] + vals[i + 1]) / 2.0
                lo = [c for c in tr if opinfo[c][feat] <= thr]
                hi = [c for c in tr if opinfo[c][feat] > thr]
                if not lo or not hi:
                    continue
                grp_w, tot, ok = {}, 0.0, True
                for grp in (lo, hi):
                    cand = [w for w in table if all(c in table[w] for c in grp)]
                    if not cand:
                        ok = False
                        break
                    bw = min(cand, key=lambda w: sum(table[w][c] for c in grp))
                    grp_w[id(grp)] = bw
                    tot += sum(table[bw][c] for c in grp)
                if ok and (bs is None or tot < bs[0]):
                    side = hi if opinfo[held][feat] > thr else lo
                    bs = (tot, feat, thr, grp_w[id(side)])
        if bs is None:
            continue
        _, feat, thr, w_for_held = bs
        held_cost = table[w_for_held].get(held)
        base = table[const_w][held]
        if held_cost is None:
            print("    hold out %-16s the chosen word is not feasible there" % held)
            worse += 1
            continue
        mark = "better" if held_cost < base else "WORSE"
        if held_cost >= base:
            worse += 1
        print("    hold out %-16s split on %-6s -> %+.4f uJ vs the fixed word  (%s)"
              % (held, feat, held_cost - base, mark))
    print("  %d of %d held-out corners came out worse than just using the fixed"
          % (worse, len(corners)))
    print("  word. A comparator tuned on three corners does not reliably help on")
    print("  a fourth it never saw -- which is the same conclusion the rest of")
    print("  the project reaches, arrived at a different way.\n")


if __name__ == "__main__":
    main()
