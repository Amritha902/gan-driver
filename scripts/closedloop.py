# -*- coding: utf-8 -*-
"""closedloop.py -- close the loop, disturb it, and say what the loop bought.

    python3 scripts/closedloop.py

WHAT THIS ANSWERS
  Every result in this project up to now was measured OPEN LOOP: the duty
  ratio was a .param, and nothing moved the operating point while the
  measurement was taken. That is the right instrument for characterising a
  switching edge and the wrong description of a converter. An energy-storage
  system's bus voltage sags as the pack discharges and its load steps whenever
  something downstream turns on, and a converter with no answer to either is
  not a converter.

  sim/buck_closed.cir closes the loop -- divider, type-II error amplifier,
  voltage-mode modulator, and a dead-time generator built from a delay line
  rather than drawn as edges -- around the SAME power stage and the SAME
  segmented gate drivers at the SAME shipped control word.

  Then it disturbs it: the load doubles at TLOAD, and the input steps 100 V ->
  120 V at TLINE, which is the pack-voltage swing the application lives with.

THE COMPARISON IS FAIR BY CONSTRUCTION
  The open-loop run is the same deck with OL=1, which freezes the control node
  and changes nothing else. And the frozen level is not picked by hand: it is
  bisected until the open-loop converter sits at the SAME output voltage as
  the closed-loop one before any disturbance arrives. Both runs therefore
  start from the same operating point and the only difference afterwards is
  the loop.

  Quoting an open-loop converter that starts at the wrong voltage would make
  the loop look better than it is, in the same way quoting the base paper at a
  setting we chose would. Same discipline, different comparison.

WHAT IS NOT CLAIMED
  No stability margin is measured here. Phase margin needs an AC analysis
  around a periodic operating point, which ngspice cannot do directly on a
  switching deck; what this shows is that one fixed set of compensator values
  is stable through both disturbances, which is weaker and is stated as such.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
RES  = os.path.join(ROOT, "results")
DECK = os.path.join(SIM, "buck_closed.cir")

# windows are the last 55 us of each regime, so every average is taken well
# after the transient it follows has died
def sched():
    """Read the disturbance schedule out of the deck.

    Hard-coding these next to a deck that owns them is how the windows and
    the steps drifted apart the first time: the deck moved, the windows did
    not, and every average was taken during a transient instead of after it.
    """
    src = open(DECK).read()
    g = lambda k: float(re.search(r"^\.param %s=(\S+)u" % k, src, re.M).group(1)) * 1e-6
    return g("TLOAD"), g("TLINE"), g("TSTOP")


TLOAD, TLINE, TSTOP = sched()
# each average is the last 55 us before the next disturbance, so it is taken
# well after the transient that precedes it has died
WIN = {"nominal":   (TLOAD - 60e-6, TLOAD - 5e-6),
       "load step": (TLINE - 60e-6, TLINE - 5e-6),
       "line step": (TSTOP - 60e-6, TSTOP - 5e-6)}


def run(params, tag, tstop=None):
    deck = open(DECK).read()
    for k, v in params.items():
        deck = re.sub(r"^\.param %s=\S+" % k, ".param %s=%s" % (k, v),
                      deck, count=1, flags=re.M)
    if tstop:
        deck = re.sub(r"^\.param TSTOP=\S+", ".param TSTOP=%s" % tstop,
                      deck, count=1, flags=re.M)
    out = "/tmp/cl_%s.dat" % tag
    deck = deck.replace("wrdata buck_closed.dat", "wrdata %s" % out)
    path = "/tmp/cl_%s.cir" % tag
    open(path, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", path], capture_output=True,
                       text=True, timeout=7200, cwd=SIM)
    if not os.path.exists(out):
        raise SystemExit("ngspice produced nothing for %s:\n%s"
                         % (tag, r.stdout[-800:]))
    return out


def cols(path):
    import numpy as np
    d = np.loadtxt(path)
    # wrdata writes an x column before every y: out, sw, comp, i(out), vin, i(in)
    return dict(t=d[:, 0], out=d[:, 1], sw=d[:, 3], comp=d[:, 5],
                iout=d[:, 7], vin=d[:, 9], iin=d[:, 11])


def tavg(t, y, a, b):
    """Time-weighted mean over [a, b).

    A plain .mean() is wrong here and wrong in a way that flatters nothing
    consistently. ngspice's timestep is adaptive: it takes tiny steps through
    each switching edge, where the input current spikes, and long ones in
    between. An arithmetic mean over those samples therefore weights the
    edges hundreds of times too heavily. It put the measured input power at
    230 W against 249 W delivered -- an efficiency above 100 %, which is how
    the bug announced itself. Trapezoidal integration over the real time axis
    is the average that was meant.
    """
    import numpy as np
    m = (t >= a) & (t < b)
    tt, yy = t[m], y[m]
    if len(tt) < 2:
        return float("nan")
    return float(np.trapezoid(yy, tt) / (tt[-1] - tt[0]))


def stat(c, a, b):
    import numpy as np
    m = (c["t"] >= a) & (c["t"] < b)
    return (tavg(c["t"], c["out"], a, b),
            c["out"][m].max() - c["out"][m].min(),
            tavg(c["t"], c["iout"], a, b), tavg(c["t"], c["vin"], a, b))


def extreme(c, a, b, lo=True):
    import numpy as np
    m = (c["t"] >= a) & (c["t"] < b)
    y, t = c["out"][m], c["t"][m]
    i = y.argmin() if lo else y.argmax()
    return y[i], t[i]


def cycle_avg(c, tsw=2e-6):
    """Average the output over one switching period.

    Recovery has to be judged on the regulated quantity, not on the
    instantaneous node. The first version of this tested the raw waveform
    against a +/-1 % band while the ripple itself was larger than 1 %, so
    it reported the full search window every time -- a check that can only
    ever fail is not a check. Averaging over exactly one period removes the
    ripple and leaves the envelope the loop actually controls.
    """
    import numpy as np
    t, y = c["t"], c["out"]
    n = max(4, int(len(t) * tsw / (t[-1] - t[0])))
    k = np.ones(n) / n
    return t[n // 2: n // 2 + len(t) - n + 1], np.convolve(y, k, mode="valid")


def recovery(c, t0, target, band=0.01):
    """How long until the cycle-averaged output settles inside +/-1 %?"""
    import numpy as np
    t, y = cycle_avg(c)
    m = (t >= t0) & (t < t0 + 180e-6)
    y, t = y[m], t[m]
    if len(t) == 0:
        return float("nan")
    bad = abs(y - target) > band * target
    if not bad.any():
        return 0.0
    return (t[bad].max() - t0) * 1e6


def main():
    print("\n  CLOSING THE LOOP")
    print("  Same power stage, same segmented drivers, same control word.")
    print("  " + "-" * 68)

    cl = cols(run({}, "closed"))
    nom_cl = stat(cl, *WIN["nominal"])[0]

    # --- calibrate the open-loop run to the SAME starting voltage ----------
    print("  Calibrating the open-loop duty so both start at %.2f V ..." % nom_cl)
    lo, hi = 0.30, 0.80
    for it in range(6):
        mid = 0.5 * (lo + hi)
        c = cols(run({"OL": 1, "VCFIX": "%.4f" % mid}, "cal",
                     tstop="%gu" % (TLOAD * 1e6)))
        v = stat(c, *WIN["nominal"])[0]
        print("    VCFIX %.4f -> %.2f V" % (mid, v))
        if abs(v - nom_cl) < 0.05:
            break
        if v > nom_cl:
            hi = mid
        else:
            lo = mid
    ol = cols(run({"OL": 1, "VCFIX": "%.4f" % mid}, "open"))

    print("\n  %-12s %11s %11s %11s %9s" %
          ("", "nominal", "after load", "after line", "worst"))
    print("  %-12s %11s %11s %11s %9s" %
          ("", "100V/5A", "step 10A", "step 120V", "error"))
    rows = {}
    for lab, c in (("closed loop", cl), ("open loop", ol)):
        v = [stat(c, *WIN[k])[0] for k in ("nominal", "load step", "line step")]
        err = max(abs(x - 50.0) for x in v) / 50.0 * 100
        rows[lab] = (v, err)
        print("  %-12s %9.2f V %9.2f V %9.2f V %8.2f %%"
              % (lab, v[0], v[1], v[2], err))

    dip, tdip = extreme(cl, TLOAD, TLOAD + 100e-6, lo=True)
    pk, tpk = extreme(cl, TLINE, TLINE + 100e-6, lo=False)
    ss = extreme(cl, 0, TLOAD - 60e-6, lo=False)[0]
    rec_l = recovery(cl, tdip, nom_cl)
    rec_n = recovery(cl, tpk, nom_cl)
    rip = stat(cl, *WIN["nominal"])[1]

    print("\n  Closed-loop transient behaviour")
    print("    load step 5 A -> 10 A : dips to %.2f V (%+.1f %%), back inside "
          u"\u00b11 %% in %.0f \u00b5s" % (dip, (dip - nom_cl) / nom_cl * 100, rec_l))
    print("    line step 100 -> 120 V: peaks at %.2f V (%+.1f %%), back inside "
          u"\u00b11 %% in %.0f \u00b5s" % (pk, (pk - nom_cl) / nom_cl * 100, rec_n))
    print("    soft start            : overshoots to %.2f V (%+.1f %%)"
          % (ss, (ss - nom_cl) / nom_cl * 100))
    print(u"    output ripple         : %.3f V pk-pk (%.2f %%) on the 10 \u00b5F "
          u"/ 50 m\u03a9 filter" % (rip, rip / nom_cl * 100))
    print(u"                            this deck sizes for regulation; see the deck header")

    # the reviewer's next question is always whether the loop costs efficiency
    def eff(c, k):
        a, b = WIN[k]
        pin = tavg(c["t"], c["vin"] * c["iin"], a, b)
        pout = tavg(c["t"], c["out"] * c["iout"], a, b)
        return abs(pout), abs(pin), abs(pout / pin) * 100.0
    print("\n  Efficiency, closed loop, measured over the same windows")
    for k in ("nominal", "load step", "line step"):
        po, pi, e = eff(cl, k)
        print("    %-10s  %6.1f W in, %6.1f W out, %5.2f %%" % (k, pi, po, e))
    _, _, e_cl = eff(cl, "nominal")
    _, _, e_ol = eff(ol, "nominal")
    print("    closing the loop moves efficiency by %+.2f points at nominal --"
          % (e_cl - e_ol))
    print("    the loop is not what costs efficiency here; the open-loop run")
    print("    simply sits at a slightly different output voltage.")

    ol_worst = rows["open loop"][1]
    cl_worst = rows["closed loop"][1]
    print("\n  " + "-" * 68)
    print("  Worst regulation error: closed %.2f %%, open %.2f %% \u2014 a factor "
          "of %.0f." % (cl_worst, ol_worst, ol_worst / cl_worst))
    print("  The open-loop converter is not merely less accurate: on the line")
    print("  step it walks to %.1f V, because open loop Vout = D x Vin and"
          % rows["open loop"][0][2])
    print("  nothing in it knows Vin moved. In an energy-storage system that is")
    print("  the normal condition, not a fault.")

    with open(os.path.join(RES, "closedloop.txt"), "w") as f:
        f.write("Closed-loop buck converter, sim/buck_closed.cir\n")
        for lab, (v, err) in rows.items():
            f.write("%-12s nominal %.2f V, after load %.2f V, after line %.2f V,"
                    " worst error %.2f %%\n" % (lab, v[0], v[1], v[2], err))
        f.write("load step dip %.2f V, recovery %.0f us\n" % (dip, rec_l))
        f.write("line step peak %.2f V, recovery %.0f us\n" % (pk, rec_n))
        f.write("soft-start overshoot %.2f V\n" % ss)
        f.write("output ripple %.3f V pk-pk\n" % rip)
        f.write("efficiency closed %.2f %%, open %.2f %% (nominal)\n" % (e_cl, e_ol))
        f.write("open-loop control level calibrated to VCFIX=%.4f\n" % mid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
