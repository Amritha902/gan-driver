#!/bin/zsh
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 6  RESULT 2 -- what re-tuning is worth (the 5.2 %%)%f"
print -P "%F{cyan}================================================================%f"
echo "script : scripts/ceiling.py     input: results/full_corners.csv"
echo "This is the number on the Result 2 slide and the bar chart."
echo
python3 scripts/ceiling.py 2>&1 | tail -14
