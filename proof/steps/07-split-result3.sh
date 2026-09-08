#!/bin/zsh
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 7  RESULT 3 -- the 25.1 %% / 3.9 %% split%f"
print -P "%F{cyan}================================================================%f"
echo "script : scripts/novelty.py     input: results/full_corners.csv"
echo "(A) picking one good fixed setting   vs   (B) re-tuning it live."
echo
python3 scripts/novelty.py 2>&1 | tail -22
