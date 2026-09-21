# -*- coding: utf-8 -*-
"""panel_metrics.py -- the two comparisons the Review-1 panel asked for,
on the parameters they named, measured in ngspice.

    python3 scripts/panel_metrics.py

WHAT THE PANEL ASKED FOR, IN THEIR WORDS
  1. "show why you are choosing GaN for this problem statement instead of
     regular silicon" -- with numbers, latency and power among them.
  2. "I implemented theirs, I got this. I implemented mine, I got this" --
     again latency and the power the devices consume, plus further
     parameters related to the topic.

  So this produces two tables with the same six columns, and every number
  in both comes from an ngspice transient on sim/buck.cir -- the converter,
  not a driver on its own. Nothing here is hand-computed or quoted from a
  datasheet.

THE THREE CONFIGURATIONS
  gan_ours   EGAN  + segdrv.lib   (ours: clamp on, -2 V off rail, 5 V drive)
  si_ours    SIMOS + segdrv.lib   (same driver, silicon device, 10 V drive)
  gan_base   EGAN  + zhangdrv.lib (base paper's driver: one-knob pattern,
                                   no clamp, no negative rail)

  Table A is gan_ours vs si_ours   -- device technology changes, driver does not.
  Table B is gan_ours vs gan_base  -- driver changes, device does not.
  Each table therefore isolates exactly one variable, which is the only way
  the numbers attribute to anything.

TWO RUNS PER CONFIGURATION, AND WHY
  Averaged power and a sub-nanosecond edge cannot come off the same
  transient. Power wants many whole cycles; a timestep fine enough to
  resolve a 2 ns edge over 150 cycles is 7.5 M points per node.

    POWER run  150 cycles, the deck's own 0.2 ns step. Efficiency, device
               dissipation and gate-drive power, averaged by ngspice's own
               time-weighted `meas AVG` over the last 20 whole cycles.
    EDGE run   3 cycles from a settled start at 0.02 ns with a 0.05 ns
               ceiling -- the same resolution the double-pulse deck uses.
               Latency, transition time, dv/dt and overshoot.

  Both runs start settled (output capacitor and inductor initialised to
  their steady-state energy), so neither is measuring the start-up ramp.

THE SIX PARAMETERS
  latency_ns   command to power. From v(pwmhs) crossing 0.5 to v(sw)
               crossing 50 % of the bus, on a mid-run turn-on edge. This is
               the number a controller designer needs: how long after the
               PWM says "on" does the switch node actually move.
  trans_ns     v(sw) 10 % to 90 % of the bus. How long the edge itself
               takes once it starts, which is a different question from
               latency and is what sets the switching loss.
  p_dev_W      dissipation in the two power devices, v*i integrated across
               each device's own current sense and time-averaged. This is
               "power consumed by the devices" as asked -- not total
               converter loss, which also contains the filter and the ESR.
  p_gate_W     power delivered by the two gate-drive supplies. Small, and
               it is the price of driving hard; it belongs next to p_dev_W
               or the comparison flatters whoever switches slowest.
  eff_pct      converter efficiency, P_out / P_in.
  ov_pct       peak v(sw) above the bus, as a percentage of the bus. The
               stress the device has to survive, and the reason a faster
               edge is not automatically a better one.

  Latency and dv/dt are reported from the waveform by centred difference
  and by interpolated level crossing, never by `meas ... WHEN`, which
  reports the first crossing of a ringing node and quantises the answer to
  the timestep. That mistake produced 3333 V/ns on a 100 V bus earlier in
  this project.
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
RES  = os.path.join(ROOT, "results")
SRC  = open(os.path.join(SIM, "buck.cir")).read()

VIN   = 100.0
FSW   = 500e3
TSW   = 1.0 / FSW
NMEAS = 20           # whole cycles the power averages run over


def settled(t):
    """Start the converter at its steady-state operating point.

    Every reactive element has to be initialised, not just the output node:
    `out` hangs off the capacitor through the ESR, so a .ic on it alone is
    overridden by the capacitor's own IC=0 and the run charges from zero.
    """
    t = t.replace(".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)=0",
                  ".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)={VO}")
    t = t.replace("Lo     sw  nlo {LOUT} IC=0",
                  "Lo     sw  nlo {LOUT} IC={IO}")
    t = t.replace("Co     nc  0   {COUT} IC=0",
                  "Co     nc  0   {COUT} IC={VO}")
    return t


def silicon(t):
    """Swap both power devices for the silicon MOSFET, at its rated drive.

    A silicon MOSFET at 5 V would be barely enhanced and would lose on a
    technicality rather than on physics, so each device is driven at the
    gate voltage its own datasheet specifies. The GaN temperature-scaled
    params are dropped rather than silently applied to silicon.
    """
    t = t.replace(".include ../models/egan.lib", ".include ../models/simosfet.lib")
    t = re.sub(r"^\.param VDRV=.*$", ".param VDRV=10", t, flags=re.M)
    t = t.replace("Xhs    hsd hsg sw EGAN params: vth={VTH_T} bh={BH_T}",
                  "Xhs    hsd hsg sw SIMOS")
    t = t.replace("Xls    lsd lsg 0  EGAN params: vth={VTH_T} bh={BH_T}",
                  "Xls    lsd lsg 0  SIMOS")
    return t


def basepaper(t, nseg=2, tstep="4n"):
    """Swap our driver for the base paper's, in the same converter.

    The pattern step is a delayed copy of each side's own PWM rather than a
    free-running source, so the step lands TSTEP after that side's turn-on
    on every cycle, which is what their one-knob pattern does. Their design
    has no clamp pin and ties the off rail to its local reference, so
    CLKEN and VNEG go with it.
    """
    t = t.replace(".include ../models/segdrv.lib", ".include ../models/zhangdrv.lib")
    t = t.replace(".param VBUS=", ".param TSTEP=%s NSEG=%d\n.param VBUS=" % (tstep, nseg), 1)
    if ".param TSTEP=" not in t:
        t = re.sub(r"^\.param VIN=.*$",
                   ".param TSTEP=%s NSEG=%d\n.param VIN=100" % (tstep, nseg),
                   t, flags=re.M)
    t = re.sub(r"^\.param VNEG=.*$", ".param VNEG=0", t, flags=re.M)

    t = t.replace(
        "Blsclk lsclk 0 V = {CLKEN*(1-v(pwmls))}      $ clamp holds the gate down when off\n"
        "Xdrvls lspu lspd lsclk lsg lsvp lsvn 0 SEGDRV\n"
        "+      params: npu={NPU_LS} npd={NPD_LS} runit={RUNIT} rclamp=0.5",
        "Vsegls lsseg 0 PULSE(0 1 {TLSD+TSTEP} {TR} {TR} {TLS} {TSW})\n"
        "Xdrvls lspu lspd lsseg lsg lsvp lsvn 0 ZHANGDRV\n"
        "+      params: nseg={NSEG} runit={RUNIT}")
    t = t.replace(
        "Bhsclk hsclkl sw V = {CLKEN*(1-v(pwmhs))}\n"
        "Xdrvhs hspu hspd hsclkl hsg hsvp hsvn sw SEGDRV\n"
        "+      params: npu={NPU_HS} npd={NPD_HS} runit={RUNIT} rclamp=0.5",
        "Vseghs segh 0 PULSE(0 1 {TSTEP} {TR} {TR} {TON} {TSW})\n"
        "Bseghs hsseg sw V = {v(segh)}\n"
        "Xdrvhs hspu hspd hsseg hsg hsvp hsvn sw ZHANGDRV\n"
        "+      params: nseg={NSEG} runit={RUNIT}")
    return t


def ours(t):
    """Our shipped word: clamp engaged, -2 V off rail."""
    t = re.sub(r"^\.param CLKEN=.*$", ".param CLKEN=1", t, flags=re.M)
    t = re.sub(r"^\.param VNEG=.*$",  ".param VNEG=-2", t, flags=re.M)
    return t


def build(cfg, kind):
    t = settled(SRC)
    if cfg == "si_ours":
        t = ours(silicon(t))
    elif cfg == "gan_base":
        t = basepaper(t)
    else:
        t = ours(t)

    if kind == "power":
        t0, t1 = (150 - NMEAS) * TSW, 150 * TSW
        meas = """
let phs = v(hsd,sw)*i(vshs)
let pls = v(lsd)*i(vsls)
let pgl = -i(vlsvp)*v(lsvp)
let pgh = -i(vhsvp)*(v(hsvp)-v(sw))
let pin = v(vin)*i(vsin)
let pout = v(out)*i(vsout)
meas tran p_hs  AVG phs  from=%.9g to=%.9g
meas tran p_ls  AVG pls  from=%.9g to=%.9g
meas tran p_gl  AVG pgl  from=%.9g to=%.9g
meas tran p_gh  AVG pgh  from=%.9g to=%.9g
meas tran p_in  AVG pin  from=%.9g to=%.9g
meas tran p_out AVG pout from=%.9g to=%.9g
quit""" % ((t0, t1) * 6)
        t = t.replace("wrdata buck.dat v(vin) i(vsin) v(sw) v(out) i(vsout) v(lsg) v(hsg)\nquit",
                      meas.strip())
    else:
        # three cycles from settled, at double-pulse resolution
        # buck.cir writes ".param NCYC  = 150" with padding, so the pattern
        # has to allow whitespace around the "=". Without \s* this silently
        # matched nothing and every "3-cycle" edge run was the full 150
        # cycles at a 0.02 ns step: 6.1 M samples, 390 MB, ~20 minutes each.
        t = re.sub(r"^\.param NCYC\s*=.*$", ".param NCYC=3", t, flags=re.M)
        t = t.replace(".tran 0.2n {TSTOP} 0 2n uic",
                      ".tran 0.02n {TSTOP} 0 0.05n uic")
        t = t.replace("wrdata buck.dat v(vin) i(vsin) v(sw) v(out) i(vsout) v(lsg) v(hsg)",
                      "wrdata EDGEOUT v(pwmhs) v(sw)")
    return t


def ngspice(text, tag, dat=None):
    path = "/tmp/pm_%s.cir" % tag
    if dat:
        text = text.replace("EDGEOUT", dat)
    open(path, "w").write(text)
    r = subprocess.run(["ngspice", "-b", path], capture_output=True,
                       text=True, timeout=3600, cwd=SIM)
    return r.stdout + r.stderr


def grab(out, keys):
    g = {}
    for k in keys:
        m = re.search(r"^%s\s*=\s*([-\d.eE+]+)" % k, out, re.M)
        g[k] = float(m.group(1)) if m else None
    return g


def cross(t, v, level, rising=True):
    """First crossing of `level`, linearly interpolated between samples.

    Interpolated rather than nearest-sample: at 0.02 ns steps on a 2 ns
    edge, nearest-sample quantises latency into 10 buckets and two
    configurations that genuinely differ by 0.3 ns can report identical.
    """
    for i in range(1, len(v)):
        a, b = v[i - 1], v[i]
        if (rising and a < level <= b) or (not rising and a > level >= b):
            if b == a:
                return t[i]
            return t[i - 1] + (level - a) * (t[i] - t[i - 1]) / (b - a)
    return None


def edge_metrics(path, vin):
    """Latency, transition time, peak dv/dt and overshoot on one turn-on.

    Taken from the SECOND turn-on in the window, not the first: the first
    edge after a settled start still carries the initial-condition step in
    the gate loop, and reads about 0.4 ns fast.
    """
    d = np.loadtxt(path)
    # wrdata emits a time column before EVERY variable, so the layout is
    # [t, v1, t, v2, ...] and variable i lives at column 2i+1. Reading
    # column 2 as v(sw) gets you the time axis, which looks like a switch
    # node that never leaves zero: latency n/a and overshoot -100 %.
    t, pwm, sw = d[:, 0], d[:, 1], d[:, 3]

    starts = []
    for i in range(1, len(pwm)):
        if pwm[i - 1] < 0.5 <= pwm[i]:
            starts.append(i)
    if len(starts) < 2:
        return None
    i0 = starts[1]
    t_cmd = cross(t[i0 - 2:i0 + 2], pwm[i0 - 2:i0 + 2], 0.5)

    w = (t >= t[i0]) & (t <= t[i0] + 0.25 * TSW)
    tw, vw = t[w], sw[w]
    if len(tw) < 20:
        return None

    t50 = cross(tw, vw, 0.50 * vin)
    t10 = cross(tw, vw, 0.10 * vin)
    t90 = cross(tw, vw, 0.90 * vin)

    k = max(2, int(0.2e-9 / np.median(np.diff(tw))))
    dv = (vw[k:] - vw[:-k]) / (tw[k:] - tw[:-k])

    return {
        "latency_ns": (t50 - t_cmd) * 1e9 if (t50 and t_cmd) else None,
        "trans_ns":   (t90 - t10) * 1e9 if (t10 and t90) else None,
        "dvdt":       float(np.abs(dv).max()) / 1e9,
        "ov_pct":     (float(vw.max()) - vin) / vin * 100.0,
    }


CONFIGS = [("gan_ours", "GaN HEMT + our driver"),
           ("si_ours",  "Si MOSFET + our driver"),
           ("gan_base", "GaN HEMT + base-paper driver")]


def main():
    res = {}
    for cfg, label in CONFIGS:
        sys.stdout.write("  %-9s power run ... " % cfg); sys.stdout.flush()
        out = ngspice(build(cfg, "power"), cfg + "_p")
        g = grab(out, ["p_hs", "p_ls", "p_gl", "p_gh", "p_in", "p_out"])
        if g["p_in"] is None:
            print("NO MEASUREMENT")
            print(out[-1500:])
            res[cfg] = None
            continue
        sys.stdout.write("ok, edge run ... "); sys.stdout.flush()
        dat = "/tmp/pm_%s_edge.dat" % cfg
        out2 = ngspice(build(cfg, "edge"), cfg + "_e", dat=dat)
        if not os.path.exists(dat):
            print("NO WAVEFORM")
            print(out2[-1500:])
            res[cfg] = None
            continue
        e = edge_metrics(dat, VIN)
        try:
            os.remove(dat)          # ~390 MB each; three of these fill a disk
        except OSError:
            pass
        print("ok")
        r = dict(g)
        r.update(e or {})
        r["p_dev_W"]  = (g["p_hs"] or 0) + (g["p_ls"] or 0)
        r["p_gate_W"] = (g["p_gl"] or 0) + (g["p_gh"] or 0)
        r["eff_pct"]  = g["p_out"] / g["p_in"] * 100.0 if g["p_in"] else None
        r["label"]    = label
        res[cfg] = r
    return res


COLS = [("latency_ns", "latency", "ns",   "%8.2f"),
        ("trans_ns",   "edge",    "ns",   "%8.2f"),
        ("p_dev_W",    "P_device", "W",   "%8.3f"),
        ("p_gate_W",   "P_gate",  "W",    "%8.3f"),
        ("eff_pct",    "eff",     "%",    "%8.2f"),
        ("ov_pct",     "overshoot", "%",  "%8.1f")]


def table(res, a, b, title, note):
    L = []
    L.append("")
    L.append("  " + title)
    L.append("  " + note)
    L.append("  " + "-" * 78)
    L.append("  %-30s" % "" + "".join("%9s" % c[1] for c in COLS))
    L.append("  %-30s" % "" + "".join("%9s" % c[2] for c in COLS))
    for cfg in (a, b):
        r = res.get(cfg)
        if not r:
            L.append("  %-30s   (no measurement)" % cfg)
            continue
        L.append("  %-30s" % r["label"] +
                 "".join((c[3] % r[c[0]]) if r.get(c[0]) is not None else "      n/a"
                         for c in COLS))
    ra, rb = res.get(a), res.get(b)
    if ra and rb:
        L.append("  " + "-" * 78)
        L.append("  %-30s" % "difference" +
                 "".join((c[3] % (ra[c[0]] - rb[c[0]]))
                         if (ra.get(c[0]) is not None and rb.get(c[0]) is not None)
                         else "      n/a" for c in COLS))
    return L


if __name__ == "__main__":
    print("\n  PANEL METRICS -- six parameters, both comparisons, all from ngspice")
    print("  sim/buck.cir, 100 V -> 50 V, 500 kHz, 10 ohm. One variable per table.")
    print("  " + "-" * 78)
    res = main()

    out = []
    out.append("\n  PANEL METRICS -- the two comparisons, on six measured parameters")
    out.append("  Source: sim/buck.cir through ngspice. 100 V -> 50 V, 500 kHz,")
    out.append("  10 ohm load, 3 nH power loop. Power averaged over the last 20 of")
    out.append("  150 cycles; latency and edge from a 3-cycle run at 0.02 ns.")
    out += table(res, "gan_ours", "si_ours",
                 "TABLE A -- why GaN and not silicon",
                 "Same converter, same driver, same 25 mOhm class. Device swapped.")
    out += table(res, "gan_ours", "gan_base",
                 "TABLE B -- our driver against the base paper's",
                 "Same converter, same GaN device, same output stage. Control swapped.")
    out.append("")
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(RES, "panel_metrics.txt"), "w").write(txt + "\n")

    import csv
    with open(os.path.join(RES, "panel_metrics.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["config", "label"] + [c[0] for c in COLS])
        for cfg, _ in CONFIGS:
            r = res.get(cfg)
            if r:
                w.writerow([cfg, r["label"]] + [r.get(c[0]) for c in COLS])
    print("  written: results/panel_metrics.txt and .csv")
