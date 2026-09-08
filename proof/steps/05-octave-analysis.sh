#!/bin/zsh
# STEP 5 -- the MATLAB analysis, re-run in Octave on the stored CSVs.
cd ~/gan-driver/results
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 5  The MATLAB analysis, re-run live in GNU Octave%f"
print -P "%F{cyan}================================================================%f"
echo "script : results/gan_master.m   (the same file runs in MATLAB Online)"
echo "tool   : $(octave --version 2>/dev/null | head -1)"
echo "inputs : the stored sweep CSVs -- no simulation, pure re-analysis"
echo
octave --no-gui --quiet gan_master.m 2>&1 | head -60
