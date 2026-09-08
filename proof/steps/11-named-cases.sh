#!/bin/zsh
# STEP 11 -- the named cases, each its own ngspice run.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 11  Specific cases, run one at a time%f"
print -P "%F{cyan}================================================================%f"
echo "Not 'we searched 720 settings' -- named cases, each its own run,"
echo "each printing its own result, so any single line can be checked."
echo
python3 scripts/cases.py
