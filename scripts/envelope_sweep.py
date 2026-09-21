# -*- coding: utf-8 -*-
"""envelope_sweep.py -- the converter measured across the whole 50-200 V
envelope its own architecture slide claims, not just at 100 V.

    python3 scripts/envelope_sweep.py

WHY THIS EXISTS
  Every converter-level number in this project was taken at 100 V. The
  720-word, 36-corner study is on sim/dpt.cir, which is a double-pulse deck
  with no decoupling network -- so it could not have caught, and did not
  catch, the undamped decoupling branch that made sim/buck.cir shoot through
  at 200 V (see scripts/decoupling_damping.py).

  Spot-checking three bus voltages found that defect. Spot-checking is not a
  study. This sweeps the converter over bus AND load and reports every
  parameter at every point, so the envelope claim is measured rather than
  assumed.

THE GRID
  bus   50, 100, 150, 200 V   -- the full stated range
  load  2 A and 10 A          -- the ends of the stated current range

  RLOAD is solved per point so the load current is the one asked for:
  RLOAD = D*VIN / I. Without that, a fixed 10 ohm load means the current
  rides the bus voltage and bus and load are not separable.

TWO RUNS PER POINT, SAME REASON AS panel_metrics.py
  Averaged power needs many whole cycles; a sub-nanosecond edge needs a
  0.02 ns step. One transient cannot do both.
    POWER  150 cycles at the deck's 0.2 ns -> efficiency, device dissipation
    EDGE   3 cycles at 0.02 ns             -> peak, overshoot, gate margin,
                                              latency, edge time
  Both start settled, so neither measures the start-up ramp.

THE SAFETY COLUMN IS THE POINT
  margin_V is the threshold minus the highest the low-side gate reaches
  WHILE THE HIGH SIDE IS CONDUCTING. Positive means the off device stayed
  off. Negative means shoot-through. Measuring the low-side gate over the
  whole cycle instead would report +5 V every time -- that is the gate
  legitimately on during its own on-time, and it hides exactly the failure
  this sweep exists to find.

  vth moves with temperature as 1.4 - 0.0015*(Tj-25); this sweep is at the
  netlist's TJ so vth is 1.4 V throughout.

CHECKPOINTED
  Results append to results/envelope_sweep.csv as each point lands. A
  container restart costs the point in flight, not the sweep.
"""
import os, re, sys, csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel_metrics as pm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")
CSV  = os.path.join(RES, "envelope_sweep.csv")

BUSES = (50, 100, 150, 200)
LOADS = (2, 10)
VTH   = 1.4
D     = 0.5
RATING = 200.0            # EPC2010C-class, per models/egan.lib

COLS = ["vin", "iload", "rload", "peak_V", "ov_pct", "gate_V", "margin_V",
        "latency_ns", "trans_ns", "eff_pct", "p_dev_W", "safe"]


def deck(vin, iload, kind):
    t = pm.build("gan_ours", kind)
    t = re.sub(r"^\.param VIN\s*=.*$", ".param VIN=%d" % vin, t, flags=re.M)
    # solve the load resistance so the CURRENT is what the grid asks for
    rload = D * vin / float(iload)
    t = re.sub(r"^\.param RLOAD\s*=.*$", ".param RLOAD=%.4f" % rload, t, flags=re.M)
    return t, rload


def edge_point(vin, iload):
    t, rload = deck(vin, iload, "edge")
    t = t.replace("wrdata EDGEOUT v(pwmhs) v(sw)",
                  "wrdata EDGEOUT v(pwmhs) v(sw) v(lsg)")
    tag = "env_%d_%d" % (vin, iload)
    dat = "/tmp/%s.dat" % tag
    pm.ngspice(t, tag, dat=dat)
    if not os.path.exists(dat):
        return None, rload
    d = np.loadtxt(dat)
    # wrdata writes a time column before every variable: [t,pwm,t,sw,t,lsg]
    tt, pwm, sw, lsg = d[:, 0], d[:, 1], d[:, 3], d[:, 5]
    m = tt > 2e-6                      # past the first settling edge
    tt, pwm, sw, lsg = tt[m], pwm[m], sw[m], lsg[m]
    os.remove(dat)
    if len(tt) < 100:
        return None, rload

    peak = float(sw.max())
    on = sw > 0.5 * vin                # high side conducting
    gate = float(lsg[on].max()) if on.any() else float("nan")

    e = pm.edge_metrics_from(tt, pwm, sw, vin) if hasattr(pm, "edge_metrics_from") else None
    lat = trans = None
    starts = [i for i in range(1, len(pwm)) if pwm[i-1] < 0.5 <= pwm[i]]
    if len(starts) >= 2:
        i0 = starts[1]
        t_cmd = pm.cross(tt[i0-2:i0+2], pwm[i0-2:i0+2], 0.5)
        w = (tt >= tt[i0]) & (tt <= tt[i0] + 0.25 * 2e-6)
        twv, vwv = tt[w], sw[w]
        if len(twv) > 20 and t_cmd:
            t50 = pm.cross(twv, vwv, 0.50 * vin)
            t10 = pm.cross(twv, vwv, 0.10 * vin)
            t90 = pm.cross(twv, vwv, 0.90 * vin)
            lat = (t50 - t_cmd) * 1e9 if t50 else None
            trans = (t90 - t10) * 1e9 if (t10 and t90) else None

    return {"peak_V": peak, "ov_pct": (peak - vin) / vin * 100.0,
            "gate_V": gate, "margin_V": VTH - gate,
            "latency_ns": lat, "trans_ns": trans}, rload


def power_point(vin, iload):
    t, _ = deck(vin, iload, "power")
    out = pm.ngspice(t, "envp_%d_%d" % (vin, iload))
    g = pm.grab(out, ["p_in", "p_out", "p_hs", "p_ls"])
    if not g["p_in"]:
        return None
    return {"eff_pct": g["p_out"] / g["p_in"] * 100.0,
            "p_dev_W": (g["p_hs"] or 0) + (g["p_ls"] or 0)}


def main():
    done = set()
    if os.path.exists(CSV):
        with open(CSV) as fh:
            for r in csv.DictReader(fh):
                done.add((int(r["vin"]), int(r["iload"])))
        print("  resuming: %d point(s) already measured" % len(done))
    else:
        with open(CSV, "w", newline="") as fh:
            csv.writer(fh).writerow(COLS)

    for vin in BUSES:
        for iload in LOADS:
            if (vin, iload) in done:
                continue
            sys.stdout.write("  %3d V %2d A  edge ... " % (vin, iload))
            sys.stdout.flush()
            e, rload = edge_point(vin, iload)
            if e is None:
                print("NO WAVEFORM"); continue
            sys.stdout.write("power ... "); sys.stdout.flush()
            p = power_point(vin, iload) or {}
            row = {"vin": vin, "iload": iload, "rload": round(rload, 3)}
            row.update(e); row.update(p)
            row["safe"] = ("SHOOT-THROUGH" if row["margin_V"] < 0 else
                           "OVER-RATING" if row["peak_V"] > RATING else "ok")
            with open(CSV, "a", newline="") as fh:
                csv.writer(fh).writerow([row.get(c) for c in COLS])
            print("%s  peak %.1f V  margin %+.2f V" %
                  (row["safe"], row["peak_V"], row["margin_V"]))
    report()


def report():
    rows = list(csv.DictReader(open(CSV)))
    L = ["", "  CONVERTER ENVELOPE SWEEP -- sim/buck.cir over its stated range",
         "  50-200 V bus, 2-10 A load, 500 kHz, 3 nH loop, damped decoupling.",
         "  Device is EPC2010C-class: 200 V rated. vth = 1.4 V.",
         "  margin = vth minus the low-side gate WHILE the high side conducts.",
         "  " + "-" * 92,
         "  %-6s %-6s %-8s %-9s %-9s %-9s %-9s %-8s %-8s %s"
         % ("bus", "load", "Rload", "peak", "overshoot", "gate", "margin",
            "eff", "P_dev", "verdict")]

    def f(r, k, fmt, suff=""):
        v = r.get(k)
        try:
            return (fmt % float(v)) + suff
        except (TypeError, ValueError):
            return "n/a"

    for r in rows:
        L.append("  %-6s %-6s %-8s %-9s %-9s %-9s %-9s %-8s %-8s %s"
                 % (r["vin"] + "V", r["iload"] + "A", f(r, "rload", "%.1f", "Ω"),
                    f(r, "peak_V", "%.1f", "V"), f(r, "ov_pct", "%.1f", "%"),
                    f(r, "gate_V", "%.2f", "V"), f(r, "margin_V", "%+.2f", "V"),
                    f(r, "eff_pct", "%.2f", "%"), f(r, "p_dev_W", "%.2f", "W"),
                    r["safe"]))
    L.append("  " + "-" * 92)
    bad = [r for r in rows if r["safe"] != "ok"]
    if bad:
        L.append("  %d of %d points NOT safe:" % (len(bad), len(rows)))
        for r in bad:
            L.append("    %s V / %s A -- %s" % (r["vin"], r["iload"], r["safe"]))
    else:
        L.append("  All %d points: the off device stays off and the switch node"
                 % len(rows))
        L.append("  stays inside the 200 V device rating. The 50-200 V envelope")
        L.append("  on the architecture slide is measured, not assumed.")
    L.append("")
    txt = "\n".join(L)
    print(txt)
    open(os.path.join(RES, "envelope_sweep.txt"), "w").write(txt + "\n")
    print("  written: results/envelope_sweep.txt and .csv")


if __name__ == "__main__":
    print("\n  CONVERTER ENVELOPE SWEEP -- %d bus x %d load points"
          % (len(BUSES), len(LOADS)))
    main()
