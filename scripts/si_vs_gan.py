# -*- coding: utf-8 -*-
"""si_vs_gan.py -- silicon MOSFET vs GaN HEMT in the SAME buck converter.

    python3 scripts/si_vs_gan.py

WHY
  The reviewer asked for a silicon-vs-GaN comparison on the converter.
  This is that comparison, and it is a power measurement: how much does
  each technology waste, converting the same 100 V into the same 50 V at
  the same 5 A?

METHOD
  sim/buck.cir is the converter, used for both runs. The ONLY differences
  between the two decks are the ones that are real differences between the
  technologies:

    device model    EGAN (models/egan.lib)   vs  SIMOS (models/simosfet.lib)
    gate drive      5 V                      vs  10 V

  Each device is driven at its own rated gate voltage, which is the only
  fair way to run it -- a silicon MOSFET at 5 V would be barely enhanced
  and would lose on a technicality rather than on physics. Everything else
  -- bus voltage, duty, switching frequency, output filter, load, dead
  time, segmented driver, power-loop parasitics, solver options -- is
  byte-identical.

  The two devices are matched on Rds(on): 25.0 mOhm GaN against 24.0 mOhm
  Si, both at their own rated drive. Conduction loss is therefore roughly
  equal by construction, and what the comparison exposes is everything
  else: switching loss, gate-drive loss, and the reverse recovery of the
  silicon body diode that GaN does not have.

MEASUREMENT
  The output starts at its steady-state value so the converter is settled
  from t=0, and averages are taken over the last 20 switching cycles.
    P_in   = VIN * average supply current
    P_out  = average of v(out) * i(load)
    loss   = P_in - P_out
    eff    = P_out / P_in
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
SRC  = open(os.path.join(SIM, "buck.cir")).read()

NCYC_MEAS = 20          # cycles averaged over, at the end of the run


def make(device):
    """device: 'gan' or 'si'."""
    t = SRC
    if device == "si":
        t = t.replace(".include ../models/egan.lib",
                      ".include ../models/simosfet.lib")
        # Si is specified at Vgs = 10 V; GaN at 5 V. Drive each at its own.
        t = re.sub(r"^\.param VDRV=.*$", ".param VDRV=10", t, flags=re.M)
        # Swap the two power devices. The model's own defaults carry the
        # silicon threshold and transconductance, so the temperature-scaled
        # GaN params are dropped rather than silently applied to silicon.
        t = t.replace("Xhs    hsd hsg sw EGAN params: vth={VTH_T} bh={BH_T}",
                      "Xhs    hsd hsg sw SIMOS")
        t = t.replace("Xls    lsd lsg 0  EGAN params: vth={VTH_T} bh={BH_T}",
                      "Xls    lsd lsg 0  SIMOS")
    # Start settled: the loss measurement wants steady state, not the
    # start-up transient the stock deck deliberately shows.
    t = t.replace(".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)=0",
                  ".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)={VO}")
    # ngspice's `let` will not expand {PARAM} the way the netlist body does,
    # so the averaging window is computed here and written in as literals.
    fsw  = float(re.search(r"^\.param FSW=(\S+)", t, re.M).group(1).rstrip("k")) * 1e3
    ncyc = float(re.search(r"^\.param NCYC\s*=\s*(\S+)", t, re.M).group(1))
    vin  = float(re.search(r"^\.param VIN=(\S+)", t, re.M).group(1))
    tstop = ncyc / fsw
    tm0   = tstop - NCYC_MEAS / fsw
    meas = (
        "\n"
        "let pin  = %g * i(vsin)\n"
        "let pout = v(out) * i(vsout)\n"
        "meas tran pin_avg  AVG pin    from=%.12g to=%.12g\n"
        "meas tran pout_avg AVG pout   from=%.12g to=%.12g\n"
        "meas tran vout_avg AVG v(out) from=%.12g to=%.12g\n"
        "quit" % (vin, tm0, tstop, tm0, tstop, tm0, tstop))
    t = t.replace("\nquit", meas, 1)
    return t


def run(tag, deck):
    p = os.path.join("/tmp", "buck_" + tag + ".cir")
    open(p, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True,
                       timeout=3600, cwd=SIM)
    out = {}
    for k in ("pin_avg", "pout_avg", "vout_avg"):
        m = re.search(r"^%s\s*=\s*([-\d.e+]+)" % k, r.stdout, re.M)
        out[k] = float(m.group(1)) if m else None
    err = [l for l in (r.stdout + r.stderr).splitlines()
           if re.search(r"error|singular|aborted", l, re.I)][:2]
    return out, err


def main():
    print("\n  SILICON MOSFET vs GaN HEMT -- same buck converter")
    print("  100 V -> 50 V, 500 kHz, 10 ohm load. sim/buck.cir, identical")
    print("  except the device model and its rated gate drive.")
    print("  Rds(on) matched: 25.0 mOhm GaN / 24.0 mOhm Si.")
    print("  " + "-" * 68)
    print("  %-10s %9s %9s %9s %8s %9s"
          % ("", "P_in", "P_out", "loss", "eff", "V_out"))

    res = {}
    for tag, label in (("gan", "GaN HEMT"), ("si", "Si MOSFET")):
        o, err = run(tag, make(tag))
        if o["pin_avg"] is None:
            print("  %-10s   FAILED  %s" % (label, err[0][:40] if err else ""))
            continue
        pin, pout = abs(o["pin_avg"]), abs(o["pout_avg"])
        loss = pin - pout
        eff = pout / pin if pin else 0
        res[tag] = (pin, pout, loss, eff)
        print("  %-10s %8.2f W %8.2f W %8.2f W %7.2f %% %8.2f V"
              % (label, pin, pout, loss, 100 * eff, o["vout_avg"]))

    if "gan" in res and "si" in res:
        (_, pg, lg, eg), (_, ps, ls, es) = res["gan"], res["si"]
        print("  " + "-" * 68)
        print("  GaN wastes %.2f W less: %.2f W against %.2f W, a %.0f %% reduction"
              % (ls - lg, lg, ls, 100 * (ls - lg) / ls if ls else 0))
        print("  Efficiency %.2f %% against %.2f %%, worth %.2f points"
              % (100 * eg, 100 * es, 100 * (eg - es)))
        print("  Loss per watt delivered: %.2f %% against %.2f %%"
              % (100 * lg / pg, 100 * ls / ps))
        print()
        print("  NOTE, and say this if asked: the two do NOT deliver identical")
        print("  output power, because GaN's third-quadrant drop during dead time")
        print("  is larger than a silicon body-diode drop -- GaN has no body diode,")
        print("  so reverse conduction costs Vth + |Voff| + I*Rds(on) instead of one")
        print("  diode drop. That is a genuine GaN disadvantage and it is why V_out")
        print("  differs. Efficiency is a ratio so it stays a fair comparison, and")
        print("  'loss per watt delivered' above normalises it explicitly.")


if __name__ == "__main__":
    main()
