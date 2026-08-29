"""
emi_sweep.py -- what happens to the scheduling ceiling when the objective
                actually prices EMI?

Section III.E of the paper states a limitation rather than a result: pull-up
drive strength is worth 0.00 % under a loss-and-overshoot cost, but it swings
turn-on dV/dt by 42 % and turn-on ringing energy by 128 %, so an EMI-driven
design might schedule it after all.  That is testable, and this closes it.

Runs the SAME full 720-word grid at the SAME two corners as the robustness
study, but records three extra turn-on measures alongside the frozen metrics:

    E_osc_on    30-500 MHz band energy of V_DS through the turn-on event
    dvdt_pk     peak |dV/dt| of the switch node        <- a PEAK measure
    dvdt_1090   10-90 % average slew of the switch node <- an INTERVAL measure

Both slew measures are kept on purpose.  This project has already shown that
peaks of a ringing node do not converge with timestep while integrals do, so
dvdt_pk is reported but is not the measure any conclusion rests on; dvdt_1090
is the one that should survive a timestep refinement.  scripts/emi_converge.py
checks exactly that.

gansim.metrics() is called unmodified on the same raw waveform, so every
standard column here is identical in definition to every earlier sweep.
"""
import csv, itertools, os, sys, time
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from sweep import GRID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "emi_sweep.csv")
CORNERS = [(100, 10, 25), (200, 2, 125)]          # same pair as robust.py


def emi_metrics(d, p):
    """Turn-on EMI measures.  Window follows DT, unlike the frozen E_osc,
    which windows turn-off and is blind to pull-up by construction."""
    t, sw, vds = d[:, 0], d[:, 1], d[:, 3]
    vbus = float(p["VBUS"])
    T4 = gansim.T3 + gansim._sec(p["DT"])         # low-side turn-ON

    # --- band energy, 30-500 MHz, through the turn-on event -----------
    w = (t >= T4) & (t <= T4 + 300e-9)
    if w.sum() < 32:
        return dict(E_osc_on=float("nan"), dvdt_pk=float("nan"),
                    dvdt_1090=float("nan"))
    ts, y = t[w], vds[w] - vds[w].mean()
    n = 4096
    yu = np.interp(np.linspace(ts[0], ts[-1], n), ts, y)
    fs = (n - 1.0) / (ts[-1] - ts[0])
    Y  = np.abs(np.fft.rfft(yu)) ** 2
    fr = np.fft.rfftfreq(n, 1.0 / fs)
    e_osc_on = float(Y[(fr >= 30e6) & (fr <= 500e6)].sum() / n ** 2)

    # --- slew of the switch node: it falls VBUS -> 0 at low-side turn-on
    k = (t >= T4) & (t <= T4 + 40e-9)
    tk, sk = t[k], sw[k]
    dvdt_pk = float(np.abs(np.gradient(sk, tk)).max() / 1e9) if k.sum() > 4 else float("nan")

    def first_cross(level):
        """first time the falling node passes below `level`"""
        below = np.nonzero(sk < level)[0]
        if not len(below) or below[0] == 0:
            return None
        i = below[0]
        y0, y1 = sk[i - 1], sk[i]
        if y0 == y1:
            return float(tk[i])
        return float(tk[i - 1] + (tk[i] - tk[i - 1]) * (y0 - level) / (y0 - y1))

    t90, t10 = first_cross(0.9 * vbus), first_cross(0.1 * vbus)
    dvdt_1090 = (0.8 * vbus / (t10 - t90) / 1e9) if (t90 and t10 and t10 > t90) \
                else float("nan")
    return dict(E_osc_on=e_osc_on, dvdt_pk=dvdt_pk, dvdt_1090=dvdt_1090)


def job(a):
    w, vb, il, tj = a
    kw = dict(w); kw.update(VBUS=vb, ILOAD=il, TJ=tj)
    try:
        d, p = gansim.run_raw(cir="ideal", **kw)
    except Exception:
        return None
    if d is None or d.size < 1000:
        return None
    try:
        m = gansim.metrics(d, p)
    except Exception:
        return None
    m.update(emi_metrics(d, p))
    m.update({k: v for k, v in p.items()})
    m["corner"] = "%dV_%dA_%dC" % (vb, il, tj)
    return m


def main():
    keys  = list(GRID)
    words = [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]
    jobs  = [(w, vb, il, tj) for (vb, il, tj) in CORNERS for w in words]
    print("words: %d   corners: %d   -> %d transients"
          % (len(words), len(CORNERS), len(jobs)), flush=True)

    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=8), 1):
            if r is None:
                bad += 1
            else:
                rows.append(r)
            if n % 200 == 0:
                el = time.time() - t0
                print("  %5d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el * (len(jobs) - n) / n, bad), flush=True)
            # checkpoint: robust.py held everything to the end, which risks
            # losing an hour of work to one crash.  Do not repeat that.
            if n % 500 == 0 and rows:
                _write(rows, OUT + ".part")

    if not rows:
        print("no rows -- aborting"); return
    _write(rows, OUT)
    if os.path.exists(OUT + ".part"):
        os.remove(OUT + ".part")
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


def _write(rows, path):
    cols = list(rows[0])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
