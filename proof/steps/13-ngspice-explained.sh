#!/bin/zsh
# STEP 13 -- ngspice, with what it did written on the screen.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 13  ngspice on screen: what it solved, and what it means%f"
print -P "%F{cyan}================================================================%f"
echo "ngspice has no window of its own. This runs it and then opens one,"
echo "so the result can be read rather than just printed."
echo
python3 scripts/ngspice_explained.py
