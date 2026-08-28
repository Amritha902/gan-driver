"""
gansim.py -- run one double-pulse simulation and extract the eight metrics.

The metric definitions live HERE and nowhere else.  Freeze them early:
if they drift mid-project every earlier sweep becomes scrap.
"""
import os, re, shutil, subprocess, tempfile
import numpy as np

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIR    = os.path.join(ROOT, "sim", "dpt.cir")
CIRS   = {"ideal": "dpt.cir", "dcload": "dpt_dcload.cir", "sky130": "dpt_sky130.cir", "hybrid": "dpt_hyb_ls_sky130.cir"}
MODELS = os.path.join(ROOT, "models")

DEFAULTS = dict(VBUS=100, ILOAD=10, VDRV=5, VNEG=0,
                NPU_LS=8, NPD_LS=8, NPU_HS=8, NPD_HS=8,
                DT="15n", CLKEN=0, CLKDEL="4n", RUNIT=8, TJ=25)

# fixed by the testbench timeline
T1, T3, VTH_NOM = 1e-6, 2e-6, 1.4


def _netlist(params, cir=None):
    src = open(os.path.join(ROOT, "sim", CIRS.get(cir or "ideal", "dpt.cir"))).read()
    src = src.replace(".include ../models/", ".include %s/" % MODELS)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in params.items())
    return re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                  lambda m: m.group(1) + block + "\n" + m.group(2), src)


def run_raw(**kw):
    """Run one point and return (raw_array, params) -- for waveform plots."""
    cir = kw.pop("cir", None)
    p = dict(DEFAULTS); p.update(kw)
    d = tempfile.mkdtemp(prefix="ganraw_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(_netlist(p, cir))
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=900)
        return np.loadtxt(os.path.join(d, "out.dat")), p
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run(**kw):
    """Run one point.  Returns dict of metrics, or None if the sim failed."""
    cir = kw.pop("cir", None)
    p = dict(DEFAULTS); p.update(kw)
    d = tempfile.mkdtemp(prefix="gan_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(_netlist(p, cir))
        r = subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                           capture_output=True, text=True, timeout=900)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        m = metrics(np.loadtxt(f), p)
        m.update({k: v for k, v in p.items()})
        return m
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _sec(x):
    """'15n' -> 15e-9"""
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    mult = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}
    return float(s[:-1]) * mult[s[-1]] if s[-1] in mult else float(s)


def metrics(d, p):
    t   = d[:, 0]
    sw, vds_ls, vgs_ls = d[:, 1], d[:, 3], d[:, 5]
    hsg, hsd           = d[:, 7], d[:, 9]
    i_ls, i_hs         = d[:, 11], d[:, 13]
    vgs_hs, vds_hs = hsg - sw, hsd - sw

    dt   = _sec(p["DT"])
    vbus = float(p["VBUS"])
    tj   = float(p["TJ"])
    vth  = VTH_NOM - 0.0015 * (tj - 25)      # must match the netlist
    T2, T4 = T1 + dt, T3 + dt

    def win(a, b):
        return (t >= a) & (t <= b)

    def integ(mask, v, i):
        return float(np.trapezoid(v[mask] * i[mask], t[mask]))

    # --- switching energies -----------------------------------------
    # Fixed 60 ns windows.  At very short dead times these legitimately
    # capture shoot-through energy; that is a real cost, not an artefact.
    w_off = win(T1 - 2e-9, T1 + 60e-9)
    w_on  = win(T4 - 2e-9, T4 + 60e-9)
    e_off = integ(w_off, vds_ls, i_ls)
    e_on  = integ(w_on,  vds_ls, i_ls)

    # --- dead-time (3rd-quadrant) loss ------------------------------
    # Load current direction never reverses, so the freewheel path is
    # the HIGH-SIDE device in third quadrant during BOTH dead times.
    e_dt = 0.0
    for a, b in ((T1 + 2e-9, T2), (T3 + 2e-9, T4)):
        if b > a:
            w = win(a, b)
            if w.sum() > 2:
                e_dt += abs(integ(w, vds_hs, i_hs))

    # --- drain overshoot --------------------------------------------
    # TWO windows, because they are two different events and conflating
    # them hides real behaviour:
    #   _off   : T1 -> T2, the low-side turn-off itself
    #   (plain): the whole cycle, i.e. peak device STRESS, which also
    #            catches the spike at the high-side turn-on
    # With ideal switches the turn-off peak dominates (it lands ~6 ns
    # after T1, inside the dead time).  With real SKY130 devices the
    # larger peak lands at the high-side turn-on instead.
    w_off = win(T1, T2)
    v_pk_off = float(vds_ls[w_off].max()) if w_off.sum() > 2 else float("nan")
    w_ov = win(T1, T1 + 200e-9)
    v_pk = float(vds_ls[w_ov].max())
    ov_pct = 100.0 * (v_pk - vbus) / vbus
    ov_pct_off = 100.0 * (v_pk_off - vbus) / vbus

    # --- ringing: settling time and 30-500 MHz oscillation energy ---
    band = 0.05 * vbus
    dev  = np.abs(vds_ls[w_ov] - vbus) > band
    tw   = t[w_ov]
    t_set = float(tw[np.nonzero(dev)[0][-1]] - T1) if dev.any() else 0.0

    w_fft = win(T1, T1 + 300e-9)
    y = vds_ls[w_fft] - vds_ls[w_fft].mean()
    ts = t[w_fft]
    if len(y) > 32:
        yu = np.interp(np.linspace(ts[0], ts[-1], 4096), ts, y)   # uniform grid
        fs = 4095.0 / (ts[-1] - ts[0])
        Y  = np.abs(np.fft.rfft(yu)) ** 2
        fr = np.fft.rfftfreq(4096, 1.0 / fs)
        e_osc = float(Y[(fr >= 30e6) & (fr <= 500e6)].sum() / len(yu) ** 2)
    else:
        e_osc = float("nan")

    # --- crosstalk --------------------------------------------------
    # HS gate is disturbed when the LS turns ON  (T4).
    # LS gate is disturbed when the HS turns ON  (T2).
    sp_hs = float(vgs_hs[win(T4, T4 + 150e-9)].max())
    sp_ls = float(vgs_ls[win(T2, T2 + 150e-9)].max())
    spur  = max(sp_hs, sp_ls)

    return dict(E_on=e_on, E_off=e_off, E_dt=e_dt,
                Vds_pk_off=v_pk_off, ov_pct_off=ov_pct_off,
                E_sw=e_on + e_off, E_tot=e_on + e_off + e_dt,
                Vds_pk=v_pk, ov_pct=ov_pct,
                t_set=t_set, E_osc=e_osc,
                Vgs_spur=spur, Vgs_spur_hs=sp_hs, Vgs_spur_ls=sp_ls,
                margin=vth - spur, false_on=int(spur > vth))


if __name__ == "__main__":
    import json, sys
    kw = dict(a.split("=") for a in sys.argv[1:])
    r = run(**kw)
    if not r:
        print("FAILED"); sys.exit(1)
    for k, v in r.items():
        print("%-14s %s" % (k, ("%.4g" % v) if isinstance(v, float) else v))
