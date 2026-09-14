# -*- coding: utf-8 -*-
"""output_audit.py -- look at what ngspice actually wrote, not what it printed.

    python3 scripts/output_audit.py

WHY
  Every number this project reports comes from a `.meas` statement: a maximum
  over a window, an integral over a window. Those are scalars, and a scalar
  cannot tell you that the waveform it came from is wrong. A run can converge,
  exit zero, print a plausible number, and still be describing something that
  could not happen -- a gate 60 V above its own rail, a drain past the device's
  rating, a transient that never reached the end of the analysis.

  The only way to know is to open the waveform. This does that for every deck
  in sim/, on every column it writes, and states what it found. It is not a
  pass/fail gate for the build; several of the findings below are real physics
  that belongs in the report rather than bugs to remove. What it removes is the
  possibility of NOT KNOWING.

WHAT IS CHECKED, AND WHY EACH ONE IS WORTH CHECKING
  finite         a NaN or an inf anywhere means the solver produced garbage and
                 the .meas over it is meaningless. Silent: meas skips them.
  time           strictly increasing, and the run reaches the analysis stop
                 time. A transient that stops early still writes a file, and a
                 measurement window past the truncation quietly measures the
                 last point instead.
  gate rails     V_GS outside [VNEG - 1, VDRV + 1] is either real gate-loop
                 ringing (reportable) or a floating node (a bug). Both matter
                 and they look identical in a scalar.
  device rating  V_DS above the 200 V class rating of the modelled device.
                 A simulation will happily run a device past destruction.
  switch node    between one reverse drop below ground and the bus plus its
                 overshoot. Outside that, something is not connected.
  currents       bounded by a generous multiple of the load. Runaway current is
                 how a shoot-through shows up in a deck that still converges.
  timestep       the smallest step the solver took. Orders below the nominal
                 means it was crawling somewhere, and that region is where to
                 look if a number is surprising.

EVERY EXCURSION IS REPORTED WITH ITS TIME AND ITS DURATION, AND THAT IS THE
POINT. The first version of this printed "v(sw) peaks at 4850 V on a 100 V
bus" for sim/dpt.cir -- the deck every headline number in the project comes
from -- which reads like the whole study is worthless. It is one sample, at
t = 2e-13 s, gone by the next timepoint: the solver's first Newton step under
`uic`, where the 10 A inductor initial condition and the forced v(sw)=0 are
not yet consistent. From 5 ns onward the node is physical.

A number without its time is not a finding. So SETTLE_T marks the start-up
window, anything inside it is labelled a settling artifact rather than a
result, and the report says how long each excursion actually lasts -- because
"peaks at 4850 V for 0.2 ps, once, before any measurement window opens" and
"peaks at 4850 V" are different sentences and only one of them is true.
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
RES  = os.path.join(ROOT, "results")

VDRV_RAIL, VTH_CLASS, VDS_RATING = 5.0, 1.4, 200.0
# Everything before this is the solver settling from inconsistent initial
# conditions, not circuit behaviour. Every measurement window in the project
# opens at 1 us or later, so nothing reported can come from in here.
SETTLE_T = 5e-9


def decks():
    return sorted(f for f in os.listdir(SIM) if f.endswith(".cir"))


def param(src, name, default=None):
    m = re.search(r"^\.param\s+%s\s*=\s*([^\s$]+)" % name, src, re.M)
    if not m:
        return default
    v = m.group(1)
    mult = {"n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "p": 1e-12}
    if v and v[-1] in mult:
        try:
            return float(v[:-1]) * mult[v[-1]]
        except ValueError:
            return default
    try:
        return float(v)
    except ValueError:
        return default


def run(deck):
    """Run one deck in a scratch dir and return (columns, array, stdout)."""
    src = open(os.path.join(SIM, deck)).read()
    m = re.search(r"^wrdata\s+(\S+)\s+(.*)$", src, re.M)
    if not m:
        return None, None, None, "no wrdata line -- this deck writes no waveform"
    cols = m.group(2).split()
    out = "/tmp/audit_%s.dat" % deck[:-4]
    text = src.replace(m.group(0), "wrdata %s %s" % (out, m.group(2)))
    path = "/tmp/audit_%s.cir" % deck[:-4]
    open(path, "w").write(text)
    r = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True,
                       timeout=7200, cwd=SIM)
    if not os.path.exists(out):
        return cols, None, src, "ngspice wrote nothing"
    try:
        d = np.loadtxt(out)
    except Exception as e:
        return cols, None, src, "unreadable output: %s" % e
    os.remove(out)
    return cols, d, src, None


def excursion(t, v, lo, hi, label, unit="V"):
    """Describe where a signal leaves [lo, hi] -- when, how long, how far.

    Returns (text, is_settling). Splitting those is the whole value: a
    transient the solver produced while settling is not a property of the
    circuit, and reporting the two the same way is how a real finding gets
    lost among artifacts.
    """
    out = (v < lo) | (v > hi)
    if not out.any():
        return None, False
    dt = np.diff(t, prepend=t[0])
    dur = float(dt[out].sum())
    i = int(np.argmax(np.abs(v - np.clip(v, lo, hi))))
    settling = t[i] < SETTLE_T and dur < SETTLE_T
    after = out & (t >= SETTLE_T)
    txt = ("%s reaches %.2f %s at t = %.4g s, outside [%.1f, %.1f] for %.3g s "
           "total (%d of %d samples)"
           % (label, v[i], unit, t[i], lo, hi, dur, int(out.sum()), len(t)))
    if settling:
        txt += " -- SETTLING ARTIFACT: before %.0g s, and the earliest " \
               "measurement window in this project opens at 1 us" % SETTLE_T
    elif after.any():
        j = int(np.argmax(np.abs(np.where(after, v - np.clip(v, lo, hi), 0))))
        txt += "; worst after settling: %.2f %s at t = %.4g s" % (v[j], unit, t[j])
    return txt, settling


def audit(deck):
    cols, d, src, err = run(deck)
    if err:
        return ["COULD NOT AUDIT: %s" % err]
    notes = []
    t = d[:, 0]
    series = {cols[i]: d[:, 2 * i + 1] for i in range(len(cols))
              if 2 * i + 1 < d.shape[1]}

    # ---- finite
    bad = {k: int((~np.isfinite(v)).sum()) for k, v in series.items()
           if not np.isfinite(v).all()}
    if bad:
        notes.append("NOT FINITE: %s" % bad)

    # ---- time axis and completeness
    if not np.all(np.diff(t) > 0):
        notes.append("time axis is not strictly increasing (%d backward steps)"
                     % int((np.diff(t) <= 0).sum()))
    tstop = param(src, "TSTOP")
    if tstop is None:
        m = re.search(r"^\.tran\s+\S+\s+(\S+)", src, re.M)
        if m:
            tstop = param("\n.param X=%s" % m.group(1), "X")
    if tstop and t[-1] < 0.98 * tstop:
        notes.append("TRUNCATED: reached %.4g s of %.4g s (%.1f %%)"
                     % (t[-1], tstop, 100 * t[-1] / tstop))

    # ---- timestep health
    dt = np.diff(t)
    notes.append("%d points, %.4g s, timestep %.3g s min / %.3g s median"
                 % (len(t), t[-1], dt.min(), np.median(dt)))
    if dt.min() < np.median(dt) / 1e4:
        notes.append("solver crawled: smallest step is %.0fx below the median "
                     "-- look there first if a number surprises you"
                     % (np.median(dt) / dt.min()))

    # ---- gate rails
    vneg = param(src, "VNEG", 0.0) or 0.0
    vdrv = param(src, "VDRV", VDRV_RAIL) or VDRV_RAIL
    for name in [k for k in series if "lsg" in k or "hsg" in k or "comp" in k]:
        v = series[name]
        lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
        if "comp" in name:
            continue
        # the high-side gate is referenced to sw, so measure it that way
        ref = series.get("v(sw)") if "hsg" in name else None
        vv = v - ref if ref is not None else v
        lbl = name + (" - v(sw)" if ref is not None else "")
        txt, _ = excursion(t, vv, vneg - 1.0, vdrv + 1.0, lbl)
        if txt:
            notes.append(txt)

    # ---- device rating and switch node
    vbus = param(src, "VBUS") or param(src, "VIN") or 100.0
    for name in [k for k in series if k in ("v(lsd)", "v(hsd)")]:
        txt, _ = excursion(t, series[name], -50.0, VDS_RATING,
                           "%s (vs the %.0f V class rating)" % (name, VDS_RATING))
        if txt:
            notes.append(txt)
    if "v(sw)" in series:
        sw = series["v(sw)"]
        st = t >= SETTLE_T
        notes.append("v(sw) spans %.1f to %.1f V on a %.0f V bus once settled "
                     "(%.0f %% overshoot)"
                     % (float(np.nanmin(sw[st])), float(np.nanmax(sw[st])),
                        vbus, 100 * (np.nanmax(sw[st]) - vbus) / vbus))
        txt, _ = excursion(t, sw, -10.0, 1.6 * vbus, "v(sw)")
        if txt:
            notes.append(txt)

    # ---- currents
    iload = param(src, "ILOAD")
    for name in [k for k in series if k.startswith("i(")]:
        pk = float(np.nanmax(np.abs(series[name])))
        if iload and pk > 20 * iload:
            notes.append("%s peaks at %.1f A against a %.0f A load" %
                         (name, pk, iload))
    return notes


def main():
    print("\n  WHAT NGSPICE ACTUALLY WROTE")
    print("  Every deck run, every column it writes opened and checked.")
    print("  " + "=" * 68)
    report, flagged = [], 0
    for deck in decks():
        print("\n  %s" % deck, flush=True)
        try:
            notes = audit(deck)
        except Exception as e:
            notes = ["COULD NOT AUDIT: %s" % e]
        for n in notes:
            hard = (any(w in n for w in ("NOT FINITE", "TRUNCATED",
                                         "COULD NOT", "not strictly",
                                         "reaches", "peaks at"))
                    and "SETTLING ARTIFACT" not in n)
            if hard:
                flagged += 1
            print("      %s%s" % ("!! " if hard else "   ", n))
        report.append((deck, notes))

    print("\n  " + "=" * 68)
    print("  %d observation(s) worth a second look, across %d decks."
          % (flagged, len(report)))
    print("  Lines marked SETTLING ARTIFACT are not counted: they are the")
    print("  solver's first step under uic, before any measurement window")
    print("  opens. Of what remains, gate-loop ringing past the rail is real")
    print("  and is reported in the deck. The point is that none of it is now")
    print("  UNKNOWN, which is what a .meas scalar leaves you with.")

    with open(os.path.join(RES, "output_audit.txt"), "w") as f:
        f.write("ngspice waveform audit -- what the output actually contains\n")
        f.write("=" * 66 + "\n")
        for deck, notes in report:
            f.write("\n%s\n" % deck)
            for n in notes:
                f.write("    %s\n" % n)
    print("\n  wrote results/output_audit.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
