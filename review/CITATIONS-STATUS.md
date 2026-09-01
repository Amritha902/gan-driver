# Citation status — verified 1 Sep 2026

## Why this file exists

The references slide carries a note that 3 of 13 were verified against the
publisher record and 10 were left with blanks rather than guessed values. That
was the right call. This file records what has since been checked, and what
still cannot be checked from here.

## What was verified this round

Bibliographic APIs (Crossref, OpenAlex) and IEEE Xplore itself are **blocked by
the network egress proxy** in this environment, so author lists, volumes and
page ranges still cannot be retrieved automatically. What *can* be done is
confirming each paper is real — that the title and Xplore document ID resolve
to an actual publication and not a fabrication.

| Ref | Status | Evidence |
|---|---|---|
| [1]–[3] | fully verified previously | publisher record |
| [9] base paper | complete (authors, vol, issue, pages, DOI) | doi:10.1002/cta.3136 |
| [8] | DOI present | doi:10.1109/TIA.2024.3454198 |
| [6] | **confirmed real** | Xplore 10964227 resolves to the exact cited title |
| [10] | **confirmed real, content checked** | Xplore 9170108 |
| [13] | **confirmed real, content checked** | Xplore 11146698 |
| [4],[5],[7],[11],[12] | titles + document IDs on record, not re-checked this round | — |

**No fabricated reference was found.** That was the failure mode worth ruling
out, and for every reference checked, the paper exists with the cited title.

## Still to do — needs a browser with institutional access

Open each Xplore document ID below and use "Cite This" → IEEE, then paste the
author list, volume, issue and page range into `refs.py`:

    [4] 9573371   [5] 10553383   [7] 10813402
    [11] 10286072  [12] 10591431  [13] 11146698
    [6] 10964227   [10] 9170108

Fifteen minutes on a campus connection finishes the reference list.

## Two technical facts that came out of verifying these

**[10] is the closest prior art and you should read it before the viva.**
"A Segmented Gate Driver for E-mode GaN HEMTs with Simple Driving Strength
Pattern Control" (Xplore 9170108) is a segmented driver for exactly this device
class: **7 segmented output stages**, gate-drive pattern timing resolution
**0.5 to 5 ns**, and the pattern programmed by a single external bias resistor.

This does NOT collide with the research gap — [10] simplifies *how you program*
the pattern; it does not measure how much of the benefit needs per-operating-
point adaptation versus a better fixed setting. But it is the paper a guide is
most likely to raise, and "we use 8+8 slices where [10] uses 7" is a weak answer
if that is all you can say. The strong answer is that [10] is a driver design
and this is a measurement of what driver adaptivity is worth.

**[13] shows the FPGA route has a resolution ceiling.**
"A High-Efficient GaN Driver With Hybrid Adaptive Dead-Time Control and Peak
Delay Control" (Xplore 11146698) reaches dead times of **0.191–0.360 ns** at
1 MHz in a 0.18 µm BCD process, using coarse digital delay refined by analog
delay.

Our FPGA controller at 200 MHz has 5 ns granularity — roughly **25x coarser**.
That is a real limitation of doing this on an FPGA, and it is an argument FOR
the Cadence phase rather than against the project: sub-nanosecond dead-time
control needs silicon, not fabric. Say it that way if asked.
