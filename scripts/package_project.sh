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
cp "$SRC"/results/*.mp4                    "$D"/6-VIDEO/
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
