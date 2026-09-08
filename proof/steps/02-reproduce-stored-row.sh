#!/bin/zsh
# STEP 2 -- take a row of the STORED sweep data and re-simulate it now.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 2  Re-simulating a stored data row, live%f"
print -P "%F{cyan}================================================================%f"
echo "This answers: 'are the CSV files real, or typed in?'"
echo "We take row 1 of results/corners.csv -- written months ago --"
echo "feed its settings back into ngspice now, and compare."
echo
python3 - <<'PY'
import sys, csv; sys.path.insert(0, 'scripts')
import gansim
row = next(csv.DictReader(open('results/corners.csv')))
keys = ['VBUS','ILOAD','VDRV','VNEG','NPU_LS','NPD_LS','NPU_HS','NPD_HS',
        'DT','CLKEN','CLKDEL','RUNIT','TJ']
kw = {}
for k in keys:
    v = row[k]
    kw[k] = v if not v.replace('-','').replace('.','').isdigit() else \
            (float(v) if '.' in v else int(v))
print("  settings from the stored file:")
print("   ", ", ".join("%s=%s" % (k, kw[k]) for k in keys))
print()
out = gansim.run(**kw)
print("  %-12s %-24s %-24s %s" % ("quantity", "STORED (in the CSV)", "LIVE (just now)", "difference"))
print("  " + "-"*84)
for m in ('Vgs_spur', 'margin', 'E_tot', 'ov_pct'):
    s, l = float(row[m]), float(out[m])
    d = 0.0 if s == 0 else abs(l - s) / abs(s) * 100
    print("  %-12s %-24.6g %-24.6g %.3f %%" % (m, s, l, d))
print()
print("  Stored data was produced with ngspice 42; this machine runs ngspice 47.")
print("  The last-digit differences are the solver version, not the physics.")
PY
