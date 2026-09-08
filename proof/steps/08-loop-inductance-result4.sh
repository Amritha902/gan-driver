#!/bin/zsh
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 8  RESULT 4 -- board inductance decides it%f"
print -P "%F{cyan}================================================================%f"
echo "script : scripts/lloop_analyse.py    input: results/lloop_sweep.csv"
echo
python3 scripts/lloop_analyse.py 2>&1 | tail -20
