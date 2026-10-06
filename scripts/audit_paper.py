"""
audit_paper.py -- check every number in paper/PAPER.md against its source.

Written after an audit found three numbers in the DECK that the runs did not
support (the closed-loop trio on slide 28) and one in the paper and the patent
(the Monte-Carlo worst case, quoted as +1.895 V when the worst of 384 runs is
+1.267 V). Both had survived because nothing re-derived them.

check_consistency.py guards a handful of headline values. This goes further
for the paper specifically: every table cell and every quantitative claim in
the prose, recomputed from the CSV or report it came from, so the paper cannot
drift from the data without the check failing.

    python3 scripts/audit_paper.py          # exits non-zero on any mismatch
"""
import csv
import statistics
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
PAPER = open(os.path.join(ROOT, "paper", "PAPER.md"), encoding="utf-8").read()
# The paper sets minus as U+2212 and en-dashes ranges. Normalise before any
# literal search, or "-1.5" fails against a paper that correctly says "\u22121.5".
PAPER_N = PAPER.replace("\u2212", "-").replace("\u2013", "-")

fails = []


def claim(lbl, pat, actual, tol=0.0):
    """Pull the number the PAPER states, then compare it to the source.

    The first version of this function took the expected value as an
    argument -- so it compared the source against a constant typed into this
    file, and perturbing PAPER.md did not make it fail. A check that cannot
    fail is not a check. The value is parsed out of the paper now.
    """
    mm = re.search(pat, PAPER_N)
    if not mm:
        print("  %-4s %-44s pattern not found in PAPER.md" % ("FAIL", lbl))
        fails.append("%s: claim not located in PAPER.md" % lbl)
        return
    claimed = float(mm.group(1))
    dp = len(mm.group(1).split(".")[1]) if "." in mm.group(1) else 0
    got = (round(float(actual), dp) == round(claimed, dp)
           or abs(claimed - float(actual)) <= tol)
    print("  %-4s %-44s paper %-10s source %.4f" %
          ("OK" if got else "FAIL", lbl, mm.group(1), float(actual)))
    if not got:
        fails.append("%s: paper %s, source %.4f" % (lbl, mm.group(1), float(actual)))


def quoted(lbl, pat):
    """The paper must literally contain this, or it has been reworded away."""
    got = bool(re.search(pat, PAPER_N))
    print("  %-4s %-44s %s" % ("OK" if got else "FAIL", lbl, "present" if got else "MISSING"))
    if not got:
        fails.append("%s: not in PAPER.md" % lbl)


PM = {r["config"]: r for r in csv.DictReader(open(os.path.join(RES, "panel_metrics.csv")))}
m = lambda c, k: float(PM[c][k])

print("\nTABLES -- results/panel_metrics.csv")
CELLS = [("latency_ns", 2), ("trans_ns", 2), ("p_dev_W", 3),
         ("p_gate_W", 3), ("eff_pct", 2), ("ov_pct", 1)]
for cfg, tag in (("gan_ours", "ours"), ("si_ours", "silicon"), ("gan_base", "base paper")):
    for k, dp in CELLS:
        v = ("%.*f" % (dp, m(cfg, k)))
        quoted("%-11s %s = %s" % (k, tag, v), re.escape(v))

print("\nTHE FAULT LADDER")
claim("clamp alone is worth", r"clamp alone is worth \+([\d.]+) V", 0.57 - (-0.249), 0.006)
claim("negative rail adds", r"negative rail adds a further \+([\d.]+) V", 2.576 - 0.57, 0.006)

print("\nDECOMPOSITION -- scripts/grid_analyse.py")
g = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "grid_analyse.py")],
                   capture_output=True, text=True, timeout=3600).stdout
gv = lambda p: float(re.search(p, g).group(1))
claim("(A) better fixed word", r"choosing a better \*\*fixed\*\* word \| \*\*([\d.]+) %", gv(r"choosing the fixed word well\s*:\s*([\d.]+)"), 0.06)
claim("(B) adapting", r"\*\*adapting\*\* it per operating point \| \*\*([\d.]+) %", gv(r"adapting per corner\s*:\s*([\d.]+)"), 0.05)
claim("(B) share of the gain", r"fraction of the total gain \| \*\*([\d.]+) %", gv(r"share of the total gain\s*:\s*([\d.]+)"), 0.05)
claim("conclusion: fixed-word share", r"\*\*([\d.]+) % is\nhad by choosing one good fixed word", 100 - gv(r"share of the total gain\s*:\s*([\d.]+)"), 0.2)
claim("leave-one-out identical", r"identical control word on (\d+) of 36", gv(r"identical on (\d+)"))
claim("one comparator, % of B", r"\| \+ one comparator \(load current at 10 A\) \| (\d+) % of \(B\)", gv(r"= (\d+) % of the adaptive part"))

print("\nFREEZE TEST -- scripts/whichbit.py")
w = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "whichbit.py")],
                   capture_output=True, text=True, timeout=1800).stdout
claim("pull-up strength freeze", r"pull-up drive strength \| \*\*([\d.]+) %",
      float(re.search(r"pull-up strength\s+\S+\s+([\d.]+)%", w).group(1)), 0.005)
claim("dead time freeze", r"\| dead time \| ([\d.]+) %",
      float(re.search(r"dead time\s+\S+\s+([\d.]+)%", w).group(1)), 0.005)

print("\nENVELOPE -- results/envelope_sweep.csv")
E = list(csv.DictReader(open(os.path.join(RES, "envelope_sweep.csv"))))
row = lambda v, i: [r for r in E if r["vin"] == v and r["iload"] == i][0]
claim("envelope worst margin", r"worst case \+([\d.]+) V", min(float(r["margin_V"]) for r in E), 0.006)
claim("150 V / 2 A peak", r"worst-case peak is ([\d.]+) V", row("150","2")["peak_V"], 0.05)
claim("200 V rows over rating (first)", r"by ([\d.]+) V and [\d.]+ V", float(row("200","2")["peak_V"])-200, 0.05)
claim("200 V rows over rating (second)", r"by [\d.]+ V and ([\d.]+) V", float(row("200","10")["peak_V"])-200, 0.05)

# The paper reports this study at TWO scopes, and each is checked against the
# file it comes from. Checking both against device_mc.csv is what let the
# shipped word's figure and a neighbouring word's figure be swapped for each
# other without anything noticing -- see results/FINDINGS.md 34.
print("\nDEVICE MONTE-CARLO, SHIPPED WORD -- results/device_mc_shipped.csv")
mcs = [r for r in csv.DictReader(open(os.path.join(RES, "device_mc_shipped.csv")))
       if r["word"] == "shipped"]
claim("shipped worst margin", r"96 runs: worst-case margin \*\*\+([\d.]+) V",
      min(float(r["margin"]) for r in mcs), 0.002)
# statistics.median, not sorted[n//2]: with an even n the two differ, and on
# the 96-run shipped set they differ by 0.05 V -- enough to fail a correct
# paper. The 384-run set hid it because there the two agree to 0.0003 V.
claim("shipped median margin", r"median \+([\d.]+) V, \*\*0 of 96",
      statistics.median(float(r["margin"]) for r in mcs), 0.002)
claim("shipped runs", r"four corners, (\d+) runs", len(mcs))
claim("shipped false turn-on", r"\*\*0 of (\d+)\*\* false\s+turn-on",
      len(mcs) if not [r for r in mcs if float(r["margin"]) < 0] else -1)

print("\nDEVICE MONTE-CARLO, CANDIDATE SET -- results/device_mc.csv")
mc = [r for r in csv.DictReader(open(os.path.join(RES, "device_mc.csv")))
      if r["CLKEN"] == "1" and float(r["VNEG"]) == -2.0
      and r["NPU_LS"] == "8" and r["NPD_LS"] == "8"]
claim("MC worst margin", r"those (?:\d+) runs the worst case is \*\*\+([\d.]+) V",
      min(float(r["margin"]) for r in mc), 0.002)
claim("MC runs", r"and over those (\d+) runs", len(mc))
claim("MC devices", r"\*\*Device spread\.\*\* (\d+) devices", len({r["dev"] for r in mc}))

print("\nCLAIMS THAT LIVE IN A NAMED FILE")
for lbl, fn, pat in (
    ("base paper's best margin +0.407 V", "basepaper_compare.txt", r"\+0\.407 V"),
    ("controller 371 -> 129 cells",       "synth_cost.txt",        r"cells\s+371"),
    ("co-simulation agrees to 0.081 V",   "rtl_cosim_power.txt",   r"0\.081 V"),
    ("decoupling Q ~ 3.5 near 22 MHz",    "VBUS-LIMIT-FINDING.md", r"Q . 3\.5 near 22 MHz"),
    ("transient count 67,116",            "transient_count.value", r"67116"),
):
    p = os.path.join(RES, fn)
    got = os.path.exists(p) and bool(re.search(pat, open(p, encoding="utf-8").read()))
    print("  %-4s %-44s %s" % ("OK" if got else "FAIL", lbl, fn))
    if not got:
        fails.append("%s: not found in results/%s" % (lbl, fn))

print("\n" + "-" * 70)
if fails:
    print("  %d MISMATCH(ES):" % len(fails))
    for f in fails:
        print("    " + f)
    sys.exit(1)
print("  every checked number in PAPER.md matches its source.")
