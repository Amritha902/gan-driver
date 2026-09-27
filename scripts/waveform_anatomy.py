"""
waveform_anatomy.py -- measure what the crosstalk waveform is actually doing.

The crosstalk slide showed two peaks and a threshold. A reviewer looking at it
asks what the trace is DOING, and "the gate goes up" is not an answer when the
question is why.

This measures the mechanism from the same two runs:

  the aggressor   how far and how fast the switch node falls -- the dv/dt that
                  drives current through C_GD into the other device's gate
  the victim      where that gate RESTS, how far the coupling LIFTS it, and
                  where it ends up

Splitting rest from rise matters, and is the thing the slide could not say
before. The negative rail and the clamp are not the same mechanism:

  the rail  moves the resting point down, so the same lift lands lower
  the clamp shortens the lift itself, by giving the injected charge a 0.5 ohm
            path out instead of leaving it on C_GS

Measured here, they are 1.941 V of offset and a lift more than halved --
1.643 V down to 0.765 V. Two effects, separately sized, from two runs.

Writes results/waveform_anatomy.txt, which the deck's caption renders from.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "waveform_anatomy.txt")
T0, T1 = 2.010e-6, 2.075e-6          # the window around the commutation edge


def trace(**kw):
    d, _ = gansim.run_raw(**kw)
    t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
    vgs = vhsg - vsw                  # gate-source of the OFF (high-side) device
    m = (t >= T0) & (t <= T1)
    return (t[m] - T0) * 1e9, vsw[m], vgs[m]


def main():
    t, vsw, vgs_bad = trace(CLKEN=0, VNEG=0)
    _, _, vgs_good = trace(CLKEN=1, VNEG=-2)

    v0 = float(vsw[:20].mean())
    hi, lo = 0.9 * v0, 0.1 * v0
    i1, i2 = int(np.argmax(vsw < hi)), int(np.argmax(vsw < lo))
    fall = float(t[i2] - t[i1])
    w = max(2, int(0.2 / np.median(np.diff(t))))
    peak_slew = float(np.abs((vsw[w:] - vsw[:-w]) / (t[w:] - t[:-w])).max())

    rows = []
    for tag, v in (("no clamp, 0 V rail", vgs_bad), ("clamp on, -2 V rail", vgs_good)):
        rest = float(v[:20].mean())
        pk = float(v.max())
        rows.append((tag, rest, pk, pk - rest))

    L = []
    P = lambda s="": (print(s), L.append(s))
    P("\n  WAVEFORM ANATOMY -- sim/dpt.cir, the commutation edge\n")
    P("  THE AGGRESSOR   switch node V(sw)")
    P("    starts at                      %7.1f V" % v0)
    P("    falls 90%% -> 10%% in            %7.2f ns" % fall)
    P("    mean slew over that fall       %7.0f V/ns" % ((hi - lo) / fall))
    P("    peak slew (0.2 ns window)      %7.0f V/ns" % peak_slew)
    P("    -> this dv/dt drives i = C_GD * dv/dt into the OFF device's gate\n")
    P("  THE VICTIM      OFF-device gate V(gs)")
    P("    %-22s %9s %9s %9s" % ("", "rests at", "peaks at", "LIFT"))
    for tag, rest, pk, lift in rows:
        P("    %-22s %+8.3f V %+8.3f V %+8.3f V" % (tag, rest, pk, lift))
    P("")
    P("    offset from the rail           %+7.3f V" % (rows[1][1] - rows[0][1]))
    P("    lift removed by the clamp      %+7.3f V  (%.3f -> %.3f)"
      % (rows[1][3] - rows[0][3], rows[0][3], rows[1][3]))
    P("    -> the rail lowers where it starts; the clamp shortens the lift.")
    P("       Two mechanisms, not one, and they are separately measurable.\n")
    open(OUT, "w").write("\n".join(L) + "\n")
    P("  wrote %s" % OUT)


if __name__ == "__main__":
    main()
