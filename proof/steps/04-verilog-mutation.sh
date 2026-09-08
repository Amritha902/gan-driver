#!/bin/zsh
# STEP 4 -- deliberately break the design and prove the test catches it.
cd ~/gan-driver/rtl
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 4  Mutation test: break it on purpose, watch it fail%f"
print -P "%F{cyan}================================================================%f"
echo "A test that never fails proves nothing. So we inject a real bug --"
echo "the low-side pull-up driven unconditionally, i.e. shoot-through --"
echo "and check the SAME testbench catches it."
echo
sh mutate.sh
