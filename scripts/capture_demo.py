"""
capture_demo.py -- run the real pipeline and record what it actually prints.

The demo video is a replay of THIS capture.  Every line in the video is real
output from a real ngspice run; only the playback pacing is presentational.
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = [
    ("ngspice --version",
     "ngspice --version | head -2", "The simulator. ngspice 42."),
    ("python3 scripts/gansim.py CLKEN=0 VNEG=0",
     "python3 scripts/gansim.py CLKEN=0 VNEG=0 | grep -E 'Vgs_spur|margin|false_on|ov_pct|E_tot'",
     "Fastest driver, no clamp. Watch the margin."),
    ("python3 scripts/gansim.py CLKEN=1 VNEG=0",
     "python3 scripts/gansim.py CLKEN=1 VNEG=0 | grep -E 'Vgs_spur|margin|false_on|ov_pct|E_tot'",
     "Same driver, Miller clamp enabled."),
    ("python3 scripts/ceiling.py 0.05",
     "python3 scripts/ceiling.py 0.05 | tail -14",
     "The headline result: what scheduling can possibly buy."),
]


def main():
    out = []
    for label, cmd, note in STEPS:
        t0 = time.time()
        r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True,
                           text=True, timeout=900)
        dt = time.time() - t0
        lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        out.append(dict(cmd=label, note=note, secs=round(dt, 2), lines=lines))
        print("  %-46s %5.1fs  %2d lines" % (label, dt, len(lines)), flush=True)
    p = os.path.join(ROOT, "results", "demo_capture.json")
    json.dump(out, open(p, "w"), indent=1)
    print("wrote %s" % p)


if __name__ == "__main__":
    main()
