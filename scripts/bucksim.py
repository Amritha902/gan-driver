"""
bucksim.py -- run the buck CONVERTER and measure what a converter is judged on.

gansim.py measures one switching edge in a test bench. This measures the
machine that edge is part of: how much power goes in, how much comes out,
what the output voltage is, and how hard the devices are stressed.

Steady state is taken as the last NAVG switching cycles of the run.
"""
import os, re, shutil, subprocess, tempfile
import numpy as np

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIR    = os.path.join(ROOT, "sim", "buck.cir")
MODELS = os.path.join(ROOT, "models")

DEFAULTS = dict(VIN=100, D=0.5, FSW="500k", LOUT="22u", COUT="4.7u", RLOAD=10,
                VDRV=5, VNEG=0, NPU_LS=8, NPD_LS=8, NPU_HS=8, NPD_HS=8,
                DT="15n", CLKEN=1, RUNIT=8, TJ=25, NCYC=150)
NAVG = 10


def _sec(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower()
    mul = {"n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3}
    return float(s[:-1]) * mul[s[-1]] if s[-1] in mul else float(s)


def _netlist(params):
    src = open(CIR).read().replace(".include ../models/", ".include %s/" % MODELS)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in params.items())
    return re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                  lambda m: m.group(1) + block + "\n" + m.group(2), src)


def run_raw(**kw):
    p = dict(DEFAULTS); p.update(kw)
    d = tempfile.mkdtemp(prefix="buck_")
    try:
        open(os.path.join(d, "buck.cir"), "w").write(_netlist(p))
        subprocess.run(["ngspice", "-b", "buck.cir"], cwd=d,
                       capture_output=True, text=True, timeout=900)
        f = os.path.join(d, "buck.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None, p
        return np.loadtxt(f), p
    finally:
        shutil.rmtree(d, ignore_errors=True)


def metrics(d, p):
    t    = d[:, 0]
    vin  = d[:, 1]
    iin  = d[:, 3]
    sw   = d[:, 5]
    vout = d[:, 7]
    iout = d[:, 9]

    tsw = 1.0 / _sec(p["FSW"])
    m = t >= t[-1] - NAVG * tsw                       # steady state
    span = t[m][-1] - t[m][0]

    def avg(y):
        return float(np.trapezoid(y[m], t[m]) / span)

    p_in, p_out = avg(vin * iin), avg(vout * iout)
    return dict(
        Vin=avg(vin), Iin=avg(iin), Pin=p_in,
        Vout=avg(vout), Iout=avg(iout), Pout=p_out,
        eff=100.0 * p_out / p_in if p_in else float("nan"),
        loss=p_in - p_out,
        ripple_mV=float(vout[m].max() - vout[m].min()) * 1e3,
        sw_pk=float(sw[m].max()),
        ov_pct=100.0 * (float(sw[m].max()) - avg(vin)) / avg(vin),
    )


def run(**kw):
    d, p = run_raw(**kw)
    if d is None:
        return None
    out = metrics(d, p)
    out.update({k: v for k, v in p.items()})
    return out


if __name__ == "__main__":
    r = run()
    for k in ("Vin", "Iin", "Pin", "Vout", "Iout", "Pout", "eff", "loss",
              "ripple_mV", "sw_pk", "ov_pct"):
        print("  %-10s %10.3f" % (k, r[k]))
