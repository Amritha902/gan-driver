# Documentation map

There are 33 documents in this repository and 34 result transcripts. This page
says which one answers which question, so nobody has to open them in turn.

**If you read one file:** `PROJECT-CLOSURE.md` — what the project is, what it
found, and what it is not allowed to claim.
**If a number is in dispute:** `results/RESULTS-SUMMARY.txt` — it names the
script that regenerates every figure, and it wins over any prose, this page
included.

---

## Start here

| Question | File |
|---|---|
| What is this project and what did it conclude? | `PROJECT-CLOSURE.md` |
| What does the repository contain, in one screen? | `README.md` |
| I am presenting this tomorrow and need to understand it | `GUIDE.md` |
| Where does *this specific number* come from? | `results/RESULTS-SUMMARY.txt` |
| I am picking this up on my own laptop | `HANDOFF.md` |

## The science

| Question | File |
|---|---|
| The result written as a paper | `paper/PAPER.md` |
| Is any of it patentable, honestly assessed? | `paper/PATENT-DISCLOSURE.md` |
| What we did, in the order we did it | `review/METHODOLOGY.md` |
| Everything found along the way, including what was wrong — §24–34 are the eleven self-caught errors | `results/FINDINGS.md` |
| The 200 V overshoot that turned out to be an undamped decoupling network | `results/VBUS-LIMIT-FINDING.md` |
| Which references are verified, which are blank, and why | `review/CITATIONS-STATUS.md` |

## Evidence that it runs

| Question | File |
|---|---|
| Every deck and script, executed, including what failed | `RUN-LOG.md` |
| A live walkthrough with commands and screenshots | `proof/WHERE-EVERY-NUMBER-COMES-FROM.md`, `proof/README-FIRST.txt` |
| Run the headline simulation in front of someone | `proof/LIVE-SIM.sh`, `proof/LIVE-BUCK.sh`, `proof/DEMO.sh` |
| Reproduce the analysis outside Python | `results/gan_master.m`, `results/README-MATLAB.txt` |

## The review

| Question | File |
|---|---|
| What to say, slide by slide (**current**) | `review/SPEECH-REVIEW2.md` |
| Every figure in the deck, explained | `review/FIGURES-EXPLAINED.md` |
| Likely questions from the guide, with answers | `review/BINDU-QUESTIONS.md` |
| A hostile examiner's thirty minutes | `review/MOCK-VIVA.md`, `review/VIVA-REHEARSAL.md` |
| An examiner's report on the deck itself | `review/JUDGE.md` |
| Mail to the guide | `review/EMAIL-TO-GUIDE.md` |
| Superseded speech scripts, kept as history | `review/SPEECH-SCRIPT.md`, `review/SPEECH-10-MINUTES.md`, `review/SPEECH-SIMPLE.md` |

A file whose opening lines say **SUPERSEDED** is kept deliberately and is
skipped by the automated checks: its numbers are allowed to be the old ones,
because its own banner tells a reader not to present from it.

## Building and checking

| Question | File |
|---|---|
| Rebuild all three decks, in the one order that works | `review/BUILD-DECK.sh` |
| Does the deck still agree with the summary, the speech and the files? | `review/check_consistency.py` |
| Is a retired number still shipping anywhere? | `review/check_stale.py` |
| Are retired slides still readable inside the `.pptx`? | `review/check_package.py` |
| Does every number in the paper still match its CSV? | `scripts/audit_paper.py` |
| How many transients were really run? | `scripts/count_transients.py` |

Three decks are produced: `GaN_Review2_PRESENT.pptx` (25 slides, the one to
present), `GaN_Review2_BACKUP.pptx` (91 slides, the backup with everything),
and `Review2_GaN_Segmented_Gate_Driver.pptx` (the full master the passes work
on).

## Hardware-adjacent tracks

| Question | File |
|---|---|
| Schematics as drawn, not as netlists | `kicad/README-KICAD.md`, `implementation/README.md` |
| LTspice decks, and the logs proving they ran | `ltspice/*.asc`, `ltspice/*.log` |
| FPGA export, and the steps not yet taken | `rtl/vivado/README-VIVADO.txt`, `rtl/vivado/VIVADO-TODO.md` |
| Spectre deck — written, **never executed** | `cadence/README-CADENCE.txt` |
| Why the SKY130 PDK is not committed, and how to fetch it | `PDK-NOTE.md`, `LICENSE-NOTE.md` |

## The next phase

`dab/` is a separate project — a GaN DAB converter for battery energy storage,
with a different base paper (Shi *et al.*, 2020). Read `dab/PROPOSAL.md` for
what it is, `dab/MILESTONES.md` for the blocking gate at the top of it, and
`dab/REVIEW1_PLAN.md` for its deliverables. Do not quote any number from
`dab/` — its two data sources say in their own headers that they are
placeholders.
