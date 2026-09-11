# -*- coding: utf-8 -*-
"""si_vs_gan_sweep.py -- silicon vs GaN across frequency, load and bus.

    python3 scripts/si_vs_gan_sweep.py            # all three sweeps
    python3 scripts/si_vs_gan_sweep.py freq       # just one

WHY THREE SWEEPS AND NOT ONE NUMBER
  A single operating point proves the two devices differ there. It does not
  say whether the difference is a quirk of that point or a property of the
  technology. These three sweeps answer the three questions a reviewer can
  ask about the headline number:

    FREQUENCY  Does GaN's lead grow with switching frequency?
               It should: switching loss is per-cycle, conduction loss is
               not, so a per-cycle advantage must scale with how often you
               pay it. This is also the sweep that matters commercially --
               switching faster is what shrinks the inductor and the box,
               and GaN's whole reason to exist is that it lets you.

    LOAD       Does the lead survive at light load?
               At light load conduction loss falls away and the fixed
               per-cycle costs dominate, so the gap should WIDEN in
               relative terms even as it narrows in watts. Storage
               converters idle at light load for long stretches, so this
               is the sweep that matters for the application.

    BUS        Does the lead hold across bus voltage?
               Device capacitance is voltage-dependent, so this checks the
               advantage is not an artefact of one bus setting.

  Conduction loss is matched by construction (25.0 mOhm GaN, 24.0 mOhm Si
  at their own rated drive), so anything these sweeps show is switching,
  gate drive or body-diode reverse recovery.

METHOD
  Identical to scripts/si_vs_gan.py: sim/buck.cir for both, the only
  differences the device model and its rated gate voltage. The output
  starts settled and averages are taken over the last NMEAS cycles.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
RES  = os.path.join(ROOT, "results")
SRC  = open(os.path.join(SIM, "buck.cir")).read()

NCYC, NMEAS = 40, 20     # cycles simulated, cycles averaged over


def make(device, ic_vout=None, ic_il=None, tstop=None, tm0=None, **over):
    t = SRC
    if device == "si":
        t = t.replace(".include ../models/egan.lib",
                      ".include ../models/simosfet.lib")
        t = re.sub(r"^\.param VDRV=.*$", ".param VDRV=10", t, flags=re.M)
        t = t.replace("Xhs    hsd hsg sw EGAN params: vth={VTH_T} bh={BH_T}",
                      "Xhs    hsd hsg sw SIMOS")
        t = t.replace("Xls    lsd lsg 0  EGAN params: vth={VTH_T} bh={BH_T}",
                      "Xls    lsd lsg 0  SIMOS")
    for k, v in over.items():
        t = re.sub(r"^\.param %s=.*$" % k, ".param %s=%s" % (k, v), t, flags=re.M)
    t = re.sub(r"^\.param NCYC\s*=.*$", ".param NCYC   = %d" % NCYC, t, flags=re.M)
    # Start in steady state. The stock deck deliberately starts at zero to
    # show the converter charging up; a loss measurement wants the opposite.
    # BOTH storage elements must be initialised -- setting v(out) alone
    # leaves the inductor current ramping from zero, which silently
    # understates P_out and flatters the loss figure.
    #
    # AND the starting values must be the real equilibrium, not the ideal
    # one. D*VIN is the LOSSLESS output; the converter actually settles a
    # volt or so below it, so starting at D*VIN kicks the output LC filter
    # into a ~15.6 kHz ring that takes Q periods to die. Measuring during
    # that ring is measuring the wrong operating point. The caller runs a
    # first pass to find where it really settles and passes the answer back
    # in via ic_vout / ic_il.
    vo_ic = "{VO}" if ic_vout is None else "%.9g" % ic_vout
    il_ic = "{IO}" if ic_il   is None else "%.9g" % ic_il
    # The OUTPUT CAPACITOR is the energy store, and it carries its own
    # IC=0. Setting .ic v(out) alone does nothing useful: `out` is a
    # derived node, tied to the capacitor node through the 0.3 ohm ESR, so
    # the capacitor's own initial condition wins and the converter charges
    # from zero every run. Both reactive elements have to be set.
    t = t.replace(".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)=0",
                  ".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)=" + vo_ic)
    t = t.replace("Lo     sw  nlo {LOUT} IC=0",
                  "Lo     sw  nlo {LOUT} IC=" + il_ic)
    t = t.replace("Co     nc  0   {COUT} IC=0",
                  "Co     nc  0   {COUT} IC=" + vo_ic)

    def pget(name, default):
        m = re.search(r"^\.param %s\s*=\s*(\S+)" % name, t, re.M)
        return m.group(1) if m else default

    def num(s):
        s = s.strip()
        mult = {"meg": 1e6, "k": 1e3, "u": 1e-6, "n": 1e-9, "m": 1e-3}
        for suf, f in sorted(mult.items(), key=lambda x: -len(x[0])):
            if s.lower().endswith(suf):
                return float(s[:-len(suf)]) * f
        return float(s)

    fsw = num(pget("FSW", "500k"))
    vin = num(pget("VIN", "100"))
    if tstop is None:
        tstop = NCYC / fsw
        tm0   = tstop - NMEAS / fsw
    t = re.sub(r"^\.tran .*$", ".tran 0.2n %.12g 0 2n uic" % tstop, t, flags=re.M)
    meas = ("\n"
            "let pin  = %g * i(vsin)\n"
            "let pout = v(out) * i(vsout)\n"
            "meas tran pin_avg  AVG pin     from=%.12g to=%.12g\n"
            "meas tran pout_avg AVG pout    from=%.12g to=%.12g\n"
            "meas tran vout_avg AVG v(out)  from=%.12g to=%.12g\n"
            "meas tran il_avg   AVG i(vsout) from=%.12g to=%.12g\n"
            "quit" % (vin, tm0, tstop, tm0, tstop, tm0, tstop, tm0, tstop))
    return t.replace("\nquit", meas, 1)


def ring_period():
    """Output-filter ring period, which sets how long settling takes."""
    import math
    def num(s):
        mult = {"meg": 1e6, "k": 1e3, "u": 1e-6, "n": 1e-9, "m": 1e-3}
        for suf, f in sorted(mult.items(), key=lambda x: -len(x[0])):
            if s.lower().endswith(suf):
                return float(s[:-len(suf)]) * f
        return float(s)
    l = num(re.search(r"^\.param LOUT=(\S+)", SRC, re.M).group(1))
    c = num(re.search(r"^\.param COUT=(\S+)", SRC, re.M).group(1))
    return 2 * math.pi * math.sqrt(l * c)


def run(tag, deck):
    p = os.path.join("/tmp", "sweep_" + tag + ".cir")
    open(p, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True,
                       timeout=3600, cwd=SIM)
    o = {}
    for k in ("pin_avg", "pout_avg", "vout_avg", "il_avg"):
        m = re.search(r"^%s\s*=\s*([-\d.e+]+)" % k, r.stdout, re.M)
        o[k] = float(m.group(1)) if m else None
    return o


def point(tag, **over):
    """Return (loss, eff, pout) for both devices at one operating point.

    Two passes. Pass 1 runs one full ring period and averages the output
    voltage and inductor current over it -- the mean of a damped ring is a
    good estimate of the asymptote it is heading for, whatever the damping.
    Pass 2 restarts from that estimate, so it begins at the operating point
    instead of ringing towards it, and only then is the loss measured.
    Without this a light-load point would need milliseconds of simulation
    to settle; with it, tens of microseconds suffice.
    """
    tring = ring_period()
    out = {}
    for dev in ("gan", "si"):
        s1 = run("%s_%s_s1" % (dev, tag),
                 make(dev, tstop=1.5 * tring, tm0=0.5 * tring, **over))
        ic_v = s1["vout_avg"]
        ic_i = abs(s1["il_avg"]) if s1["il_avg"] is not None else None
        o = run("%s_%s_s2" % (dev, tag),
                make(dev, ic_vout=ic_v, ic_il=ic_i, **over))
        if o["pin_avg"] is None:
            out[dev] = None
            continue
        pin, pout = abs(o["pin_avg"]), abs(o["pout_avg"])
        out[dev] = (pin - pout, (pout / pin) if pin else 0, pout)
    return out


def table(title, why, unit, points, param, values, fmt="%s"):
    lines = []
    lines.append("")
    lines.append("  " + title)
    lines.append("  " + why)
    lines.append("  " + "-" * 72)
    lines.append("  %-10s %11s %11s %11s %11s %9s"
                 % (unit, "GaN loss", "Si loss", "GaN eff", "Si eff", "GaN wins"))
    for v, res in zip(values, points):
        if res["gan"] is None or res["si"] is None:
            lines.append("  %-10s   FAILED" % (fmt % v))
            continue
        lg, eg, pg = res["gan"]
        ls, es, ps = res["si"]
        win = 100 * (ls - lg) / ls if ls else 0
        lines.append("  %-10s %9.2f W %9.2f W %9.2f %% %9.2f %% %7.0f %%"
                     % (fmt % v, lg, ls, 100 * eg, 100 * es, win))
    return "\n".join(lines)


def sweep_freq():
    vals = ["100k", "250k", "500k", "750k", "1meg"]
    pts = [point("f" + v, FSW=v) for v in vals]
    return table("FREQUENCY SWEEP -- 100 V -> 50 V, 10 ohm load",
                 "switching loss is paid per cycle, so GaN's lead should grow",
                 "f_sw", pts, "FSW", vals)


def sweep_load():
    vals = ["2", "5", "10", "20", "50"]
    pts = [point("r" + v, RLOAD=v) for v in vals]
    return table("LOAD SWEEP -- 100 V -> 50 V, 500 kHz  (higher ohms = lighter load)",
                 "at light load the per-cycle costs dominate, so the gap should widen",
                 "R_load", pts, "RLOAD", vals, "%s ohm")


def sweep_bus():
    vals = ["50", "100", "150", "200"]
    pts = [point("v" + v, VIN=v) for v in vals]
    return table("BUS SWEEP -- 50 % duty, 500 kHz, 10 ohm load",
                 "device capacitance is voltage dependent; check it is not one-point luck",
                 "V_bus", pts, "VIN", vals, "%s V")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    head = ["", "  SILICON MOSFET vs GaN HEMT -- swept",
            "  sim/buck.cir for both. Only the device model and its rated gate",
            "  drive differ (GaN 5 V, Si 10 V). Rds(on) matched 25.0 / 24.0 mOhm,",
            "  so conduction loss is equal by construction and what these sweeps",
            "  show is switching, gate drive and body-diode reverse recovery."]
    out = ["\n".join(head)]
    if which in ("all", "freq"): out.append(sweep_freq())
    if which in ("all", "load"): out.append(sweep_load())
    if which in ("all", "bus"):  out.append(sweep_bus())
    text = "\n".join(out) + "\n"
    print(text)
    if which == "all":
        open(os.path.join(RES, "si_vs_gan_sweep.txt"), "w").write(text)
        print("  -> results/si_vs_gan_sweep.txt\n")


if __name__ == "__main__":
    main()
