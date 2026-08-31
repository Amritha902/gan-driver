#!/bin/sh
# Rebuild ~/GaN-Project.zip, the folder that goes on the Windows laptop.
# Reproducible: everything is copied from the working tree, nothing is
# edited in place inside the zip.
set -e
SRC="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$HOME/GaN-Project.zip}"
STAGE="$(mktemp -d)"
D="$STAGE/GaN-Project"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$D"/1-LTSPICE "$D"/2-FIGURES "$D"/3-MATLAB "$D"/4-RESULTS \
         "$D"/5-SOURCE "$D"/6-VIDEO "$D"/7-CADENCE "$D"/8-PAPER

cp "$SRC"/ltspice/*.cir                    "$D"/1-LTSPICE/
cp "$SRC"/ltspice/*.lib                    "$D"/1-LTSPICE/
cp "$SRC"/ltspice/README-LTSPICE.txt       "$D"/1-LTSPICE/README.txt
cp "$SRC"/results/fig*.png                 "$D"/2-FIGURES/
cp "$SRC"/results/pareto_matlab.png "$SRC"/results/crosstalk_model_matlab.png "$D"/2-FIGURES/
cp "$SRC"/results/*.m "$SRC"/results/sweep_matlab.csv "$SRC"/results/README-MATLAB.txt "$D"/3-MATLAB/
cp "$SRC"/results/FINDINGS.md              "$D"/4-RESULTS/
for f in sweep_nominal corners full_corners sky130_drive_strength robust emi_sweep; do
    [ -f "$SRC/results/$f.csv" ] && cp "$SRC/results/$f.csv" "$D"/4-RESULTS/
done
for f in "$SRC"/results/*.log; do [ -f "$f" ] && cp "$f" "$D"/4-RESULTS/; done
# Ship only the two videos whose every frame still reproduces.
#   pipeline_demo_review1.mp4  trimmed at 17.5 s: the original closed on
#       "the Miller clamp buys 14.7 %", the superseded 36-corner figure.
#   scope_demo_review1.mp4     trimmed from 12.9 s: the original opened with
#       13 s of blank white, 40 % of its length.
#   research_demo.mp4          NOT SHIPPED. Its closing caption says the
#       benefit "collapses to one bit - the off-bias rail", which the freeze
#       test corrected to dead time, and its body shows decompose.py's old
#       hardcoded "price of crosstalk safety 0%", corrected to 0.04%. Two
#       stale claims in a 14 s clip; the untrimmed originals stay in the repo
#       under results/ for the record.
cp "$SRC"/results/pipeline_demo_review1.mp4 "$D"/6-VIDEO/
cp "$SRC"/results/scope_demo_review1.mp4    "$D"/6-VIDEO/
cp "$SRC"/cadence/*                        "$D"/7-CADENCE/
cp "$SRC"/results/paper_draft.html         "$D"/8-PAPER/paper.html
cp "$SRC"/results/paper_fig*.png           "$D"/8-PAPER/

# 5-SOURCE: the runnable project, minus caches and raw waveform dumps
for d in models sim scripts; do
    [ -d "$SRC/$d" ] && cp -r "$SRC/$d" "$D"/5-SOURCE/
done
# The SKY130 PDK is ~18 MB of vendor files and is not ours to redistribute.
# Ship only the small extracted 5 V corner library the netlists actually
# .lib, plus the note saying where the full PDK comes from.
cp "$SRC"/pdk/sky130_5v.lib "$SRC"/pdk/LICENSE-NOTE.md "$D"/5-SOURCE/ 2>/dev/null || true
cp "$SRC"/README.md "$D"/5-SOURCE/ 2>/dev/null || true
find "$D"/5-SOURCE -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$D"/5-SOURCE -name '*.dat' -delete 2>/dev/null || true

cp "$SRC"/results/START-HERE.txt "$D"/START-HERE.txt

rm -f "$OUT"
(cd "$STAGE" && zip -qr "$OUT" GaN-Project)
echo "built $OUT"
unzip -l "$OUT" | tail -1
