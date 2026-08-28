"""
make_scope_data.py -- decimate real simulation runs into JSON for the
browser scope.

Min/max decimation, not resampling: each output bucket keeps both the
minimum and maximum of the samples it covers, so narrow spikes survive.
Plain interpolation would erase exactly the features worth looking at.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIGS = [
    ("baseline", "Fastest driver, no clamp",
     dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, CLKEN=0, VNEG=0, DT="15n")),
    ("clamp", "Miller clamp on",
     dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, CLKEN=1, VNEG=0, DT="15n")),
    ("clamp_neg", "Clamp + −2 V off-bias",
     dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, CLKEN=1, VNEG=-2, DT="15n")),
    ("slow", "Slowest pull-up (code 1)",
     dict(NPU_LS=1, NPD_LS=8, NPD_HS=8, CLKEN=0, VNEG=0, DT="15n")),
    ("shootthru", "Weak pull-down, 5 ns dead time",
     dict(NPU_LS=8, NPD_LS=2, NPD_HS=8, CLKEN=0, VNEG=0, DT="5n")),
]

NBUCKET = 1100


def minmax(t, y, n=NBUCKET):
    """Bucketed min/max decimation, returned as an interleaved trace."""
    idx = np.linspace(0, len(t), n + 1).astype(int)
    ts, ys = [], []
    for a, b in zip(idx[:-1], idx[1:]):
        if b <= a:
            continue
        seg = y[a:b]
        lo, hi = seg.argmin(), seg.argmax()
        for k in sorted((lo, hi)):
            ts.append(float(t[a + k])); ys.append(float(seg[k]))
    return ts, ys


def main():
    out = {"vth": 1.4, "configs": []}
    for key, label, cfg in CONFIGS:
        d, p = gansim.run_raw(**cfg)
        m = gansim.run(**cfg)
        t = d[:, 0]; sw = d[:, 1]; vds = d[:, 3]
        vgs_ls = d[:, 5]; hsg = d[:, 7]; i_ls = d[:, 11]
        vgs_hs = hsg - sw
        sig = {}
        base_t = None
        for name, y in (("sw", sw), ("vds_ls", vds), ("vgs_ls", vgs_ls),
                        ("vgs_hs", vgs_hs), ("i_ls", i_ls)):
            ts, ys = minmax(t, y)
            if base_t is None:
                base_t = [round(v * 1e9, 4) for v in ts]      # ns
            sig[name] = [round(v, 3) for v in ys]
        dt_ns = gansim._sec(cfg["DT"]) * 1e9
        out["configs"].append(dict(
            key=key, label=label, t=base_t, sig=sig,
            dt_ns=dt_ns,
            events=dict(t1=1000.0, t2=1000.0 + dt_ns, t3=2000.0,
                        t4=2000.0 + dt_ns),
            metrics=dict(spur=round(m["Vgs_spur"], 3),
                         margin=round(m["margin"], 3),
                         ov=round(m["ov_pct"], 2),
                         e_on=round(m["E_on"] * 1e6, 3),
                         e_off=round(m["E_off"] * 1e6, 3),
                         e_dt=round(m["E_dt"] * 1e6, 3)),
            cfg={k: str(v) for k, v in cfg.items()}))
        print("  %-10s spur=%.2f V margin=%+.2f V  (%d pts)"
              % (key, m["Vgs_spur"], m["margin"], len(base_t)), flush=True)
    f = os.path.join(ROOT, "results", "scope_data.json")
    json.dump(out, open(f, "w"), separators=(",", ":"))
    print("wrote %s (%.0f KB)" % (f, os.path.getsize(f) / 1024))


if __name__ == "__main__":
    main()
