#!/bin/zsh
# ---------------------------------------------------------------------------
# RUN-LIVE.sh -- run the whole project in front of someone, live.
#
# Eleven steps. Each one starts a real tool on this machine and prints the
# number that is on the slide. Nothing is read from a saved file except the
# sweep data, and step 2 re-simulates a row of that data to show it is real.
#
#     cd ~/GAN_MAIN/PROOF && zsh RUN-LIVE.sh
#
# Press RETURN between steps. Total run time is about two minutes.
# ---------------------------------------------------------------------------
cd "$(dirname "$0")"
mkdir -p logs

STEPS=(
  "steps/01-ngspice-crosstalk.sh"
  "steps/02-reproduce-stored-row.sh"
  "steps/03-verilog-testbench.sh"
  "steps/04-verilog-mutation.sh"
  "steps/05-octave-analysis.sh"
  "steps/06-ceiling-result2.sh"
  "steps/07-split-result3.sh"
  "steps/08-loop-inductance-result4.sh"
  "steps/09-show-waveforms.sh"
  "steps/10-converter-power.sh"
  "steps/11-named-cases.sh"
)

print -P "\n%F{yellow}GaN segmented gate driver -- live verification%f"
print -P "%F{yellow}$(date '+%Y-%m-%d %H:%M')   $(hostname)%f\n"
echo "Eleven steps. Every number on the slides is produced here, now."
echo "Press RETURN to start each one, Ctrl-C to stop."
read

for s in $STEPS; do
  clear
  zsh "$s" 2>&1 | tee "logs/$(basename $s .sh).log"
  print -P "\n%F{yellow}---- press RETURN for the next step ----%f"
  read
done

clear
print -P "%F{green}All eleven steps done. Logs are in PROOF/logs/.%f"
