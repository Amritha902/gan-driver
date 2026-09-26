# Invention disclosure — working draft

**Title (working):** Segmented gate driver for GaN half-bridges with strapped
drive-strength and single-sensor dead-time scheduling

Sanjay Kumar · Aamir Abdullah · Amritha S · Dr. Bindu
School of Electronics Engineering (SENSE), VIT Chennai

> **Read this section first.** This is a disclosure draft for discussion with
> the institute's IP cell, not a filing. Sections 1–7 are what an attorney
> needs. Section 8 is the part most disclosures leave out and the part that
> decides whether filing is worth the money — an honest account of what is
> probably not patentable here and why.

---

## 1. Field

Gate-drive circuits for enhancement-mode GaN HEMTs in half-bridge power
converters, specifically the suppression of C_GD-coupled false turn-on
(crosstalk) during the complementary device's switching transition.

## 2. Problem

An E-mode GaN HEMT has a low gate threshold (≈1.4 V) and no body diode. The
complementary device's switching edge couples through drain-gate capacitance
into the gate of the device that should be off. In a 100 V / 500 kHz
converter with 3 nH of loop inductance we measure the off gate reaching
**1.65 V against a 1.4 V threshold** — a shoot-through.

Existing segmented drivers address this by making the drive strength
programmable, so the edge can be slowed. Slowing the edge costs switching
loss, and programmability costs a sense chain, a converter and a lookup
table.

## 3. Prior art known to us

- Zhang, Yu, Leng, Cui, Deng, Ng, *A Segmented Gate Driver for E-mode GaN
  HEMTs with Simple Driving Strength Pattern Control*, IEEE ISPSD 2020,
  pp. 102–105. Seven slices, two-stage pattern, pattern selected by **one
  external bias resistor fixed at design time**. No active clamp, no negative
  off rail.
- Wang *et al.*, high-frequency three-level gate drive (2024).
- Wang *et al.*, integrated suppression of gate-source and drain-source
  coupling (2024).
- Cai, Ye, Lv, Chen, hybrid adaptive dead time with peak-current control
  (2026).

Active Miller clamps and negative off-bias rails are both **individually well
known and widely commercialised**. This is stated plainly here because it is
the central obstacle to a claim (see §8).

## 4. What we built

1. An 8+8-slice thermometer-coded segmented output stage.
2. Six independently programmable fields — high- and low-side pull-up and
   pull-down strength, dead time, active Miller clamp enable, off-rail select
   (0 V / −2 V) — giving a **720-word** control space.
3. An FPGA controller (`seg_gate_ctrl.v`) emitting the word; 20 LUTs / 20 FF
   on an Artix-7, 200 MHz register-to-register with 1.996 ns slack.
4. An exhaustive characterisation: 720 words × 36 operating points, 66,924
   transients.

## 5. The finding the claims would rest on

Decomposing the achievable gain:

| | share of baseline |
|---|---|
| choosing a better **fixed** word | **26.5 %** |
| **adapting** the word per operating point | **2.6 %** |
| adaptation as a share of total gain | **8.9 %** |
| ceiling on any scheduling scheme | 3.5 % |

One comparator on **load current** captures 47 % of the adaptive part; two
capture 61 %. Strapping the word instead of keeping six fields live saves
**65 % of the controller logic** (371 → 129 cells).

Leave-one-corner-out returns the **identical** control word on 36 of 36
corners.

## 6. Candidate claims, strongest first

**Claim A (method).** A method of configuring a segmented GaN gate driver in
which drive-strength fields are fixed at commissioning from an exhaustive
characterisation, and **only dead time** is scheduled at run time from a
single load-current comparator — the drive-strength segmentation being
retained for edge shaping but not scheduled.

*Why this is the strongest:* it is the counter-intuitive part. The field
everyone schedules (drive strength) is the one we measure as worth **0.00 %**
to freeze; the field worth scheduling is dead time, and only because of the
light-load corner.

**Claim B (system).** A driver combining a thermometer-coded segmented output
stage, an active Miller clamp and a switchable negative off rail, in which
the clamp and rail carry the crosstalk margin and the segmentation is
strapped — with the specific measured allocation (clamp worth 9.7–12.2 %,
drive-strength segmentation worth 0.00 % when frozen).

**Claim C (commissioning process).** A process for deriving the strapped word
by exhaustive search with leave-one-corner-out validation, producing a
controller of bounded size.

## 7. Evidence supporting the claims

All reproducible from the repository; `results/RESULTS-SUMMARY.txt` names the
generating script for every number.

- 66,924 transients, 36 operating points, ngspice 42
- device Monte-Carlo, 24 jointly varied devices: worst margin +1.895 V, 0/24
  false turn-on
- SKY130 transistor-level output stage: sign and ordering survive
- converter envelope sweep, 8 bus × load points: margin +2.14 to +2.61 V
- RTL synthesised in Vivado 2024.1 with timing met

## 8. Honest assessment of patentability

An attorney will ask these. Better to have answers.

**The components are not novel.** Segmented output stages, active Miller
clamps and negative off-bias rails are all known and commercial. A claim on
any combination of them will face obviousness. Claim B is therefore weak on
its own.

**The novelty, if any, is the negative result.** "Do not schedule drive
strength; schedule only dead time, from one comparator" is a specific,
non-obvious, counter-intuitive teaching that runs against the direction of
the cited prior art. That makes Claim A the one worth pursuing.

**But a measurement is not an invention.** The finding is a characterisation
result. It supports a *method* claim only insofar as the method — strap these
fields, schedule that one, from this sensor — is itself claimed as a
configuration procedure. Whether that clears the bar is a question for
counsel, not for us.

**It is entirely simulation.** No hardware has been measured. For a filing
that asserts specific quantitative advantages this is a real exposure, and
the quantities are also model-dependent: §V-B of the paper records that the
sign of the headline fault changes with the device model's capacitance law.

**Our honest recommendation:** publish the paper first. The finding's value
is as a design rule the field should know, and the strongest version of
Claim A would be materially better supported by one measured hardware edge.
If the institute wants a filing regardless, file on Claim A alone, narrowly,
and do not assert the component combination.

## 9. Disclosure status

> **This section previously read "Not disclosed publicly. The repository is
> private." That is false, and it is the premise the filing advice below used
> to rest on. Raise this with the IP cell before anything else in this
> document is acted on.**

**The repository is public.** `github.com/Amritha902/gan-driver` reports
`"visibility": "public"` on the GitHub API. It was created on 2 September
2026 and contains the full method, the model files, the complete results and
a draft of the paper. GitHub does not expose when a repository's visibility
last changed, so the date public disclosure began cannot be established from
the repository itself — only that it is public now.

A public repository describing the invention is a public disclosure. What
that costs depends on jurisdiction, and none of the following is legal
advice — it is the set of questions to put to counsel:

- **India** (Patents Act 1970, ss. 29–34): the grace provisions are narrow
  and specific. General prior publication is not among them.
- **EPO**: absolute novelty. There is no general grace period.
- **US** (35 U.S.C. §102(b)(1)): a one-year grace period runs from the
  inventor's own disclosure, so a US filing may still be available if the
  disclosure date is within a year — which makes establishing that date the
  first practical task.

No conference submission has been made. That is no longer the operative
question: **the repository, not the paper, is the disclosure that matters,
and it is already out.** The remaining decisions are whether a filing is
still available in any jurisdiction the institute cares about, and whether
to make the repository private now — which does not undo a disclosure, but
does stop it widening.

This does not change §8's recommendation to publish rather than file. It
changes the reason: publishing first is no longer a choice being made, it is
a description of what has already happened.
