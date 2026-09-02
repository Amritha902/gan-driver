"""
summary.py -- every headline number in one place, each with its source script.

Written so that nothing in the deck or the paper is a figure someone has to
take on trust: each line names the script that regenerates it. If a number
here disagrees with a slide, the slide is wrong.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROWS = [
 ("THE PROBLEM", None, None),
 ("Spurious gate peak, fastest drive, no clamp", "1.65 V vs 1.40 V threshold", "gansim.py"),
 ("Same word, Miller clamp on", "0.83 V  (margin +0.57 V)", "gansim.py"),
 ("Clamp on + −2 V off-bias", "−1.18 V  (margin +2.58 V)", "gansim.py"),
 ("Feasible words at the nominal corner", "504 of 720  (70 %)", "gan_analysis.m"),

 ("THE SEARCH", None, None),
 ("Control-word space, searched in full", "720 words × 4 corners", "sweep.py, corners.py"),
 ("Transient simulations, all studies", "34,622", "row count, all result CSVs"),
 ("Switching-energy spread across the word", "up to 483 %", "figures.py"),

 ("WHAT ADAPTATION IS WORTH", None, None),
 ("(A) choosing a better fixed word", "25.1 % of baseline", "novelty.py"),
 ("(B) adapting it per operating point", "3.9 % of baseline", "novelty.py"),
 ("adaptation as a share of the total gain", "13.4 %", "novelty.py"),
 ("captured by ONE comparator (K = 2)", "72 % of (B)", "howmanywords.py"),
 ("left for a full sense + ADC + LUT", "3.7 % of the total gain", "novelty.py"),
 ("words needed for the full benefit", "3 of 4  (K = 4 adds nothing)", "howmanywords.py"),

 ("WHAT THE ADAPTIVE HARDWARE COSTS", None, None),
 ("controller, all six fields live", "371 cells / 32 FF", "synth_cost.sh"),
 ("controller, word strapped + 1 comparator", "129 cells / 24 FF", "synth_cost.sh"),
 ("logic saved by strapping the word", "65 %", "synth_cost.sh"),

 ("WHICH FIELD, AND WHAT IT COSTS", None, None),
 ("dead time, frozen  (four corners)", "5.45 %  (8.92 % at a 1 V guard)", "whichbit.py"),
 ("dead time, frozen  (without the light-load corner)", "0.00 %", "FINDINGS.md §32"),
 ("pull-up drive strength, frozen", "0.00 %", "whichbit.py"),
 ("active Miller clamp, worth", "9.7 – 12.2 %", "clampvalue.py"),
 ("price of crosstalk safety", "≤ 0.04 % of switching energy", "safety_price.py"),

 ("WHERE THE ANSWER CHANGES", None, None),
 ("ceiling across every device perturbation", "4.3 – 7.7 %", "robust_analyse.py"),
 ("ceiling vs power-loop inductance", "13.5 % @1.5 nH → 0.6 % @4.5 nH", "lloop_analyse.py"),
 ("band where adaptive control pays (not a single crossover)", "≲ 2.5 nH", "lloop_analyse.py"),
 ("words feasible at both corners, 1.0 nH vs 4.5 nH", "165 vs 484", "lloop_analyse.py"),

 ("VERIFICATION", None, None),
 ("timestep refinement every number survives", "25×", "metric_converge.py"),
 ("drain overshoot drift over that range", "1.14 %", "metric_converge.py"),
 ("spurious gate peak drift", "0.04 %", "metric_converge.py"),
 ("feasibility verdicts flipped by refinement", "0 of 80", "verdict_stability.py"),
 ("RTL properties asserted, all passing", "8", "seg_gate_ctrl_tb.v"),
 ("wrong numbers caught by these checks", "10", "FINDINGS.md §24–32"),
]


def main():
    w = max(len(a) for a, b, c in ROWS if b)
    print("=" * (w + 46))
    print("  RESULTS SUMMARY   —   every number, and what regenerates it")
    print("=" * (w + 46))
    for label, val, src in ROWS:
        if val is None:
            print("\n  " + label); print("  " + "─" * (w + 42)); continue
        print("  %-*s  %-30s %s" % (w, label, val, src))
    print("=" * (w + 46))
    print("  Anything here that disagrees with a slide means the slide is wrong.")


if __name__ == "__main__":
    main()
