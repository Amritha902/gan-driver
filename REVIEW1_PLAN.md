# Review 1 — what to have ready

**Team:** Sanjay Kumar 23BEC1447 · Aamir Abdullah 23BPS1197 · Amritha S 23BEC1368
**Guide:** Dr. Bindu

Zeroth review sold the *idea*. Review 1 has to show the idea **survives contact with a
simulator**. Four things, in priority order. If you only get the first two, you are still fine.

---

## The four deliverables

### 1. The base paper reproduced — **non-negotiable**

One overlay plot: your simulated ZVS boundary on top of the boundary from Shi 2020, at the same
operating conditions. Match within a few per cent.

This is the single most important slide in Review 1. It answers "do you actually understand the
paper you are building on?" before anyone asks. If you cannot reproduce it, say so and show what
diverges — that is still a result, and hiding it is worse.

### 2. A working loss and soft-switching model

- C_oss(v) extracted from the GaN device model
- Dead-time-corrected soft-switching criterion implemented as code
- Loss model: conduction, switching, reverse conduction during dead-time, transformer copper
- Validated against simulation at ~5 operating points, within roughly 2 %

### 3. First sweep result — **this is the one that matters scientifically**

Sweep the grid and answer RQ2:

> **Does the best dead-time actually change as the duty cycles, phase shift and load change?**

Produce one plot: optimal t_dead against load, with a curve per phase-shift setting. If the
curves separate, N1 holds and you have a project. If they lie on top of each other, N1 is weak —
**report it in Review 1**, do not sit on it until the final review.

### 4. RTL skeleton simulating in Vivado

Not the full policy engine. Just:

- `quantiser.v` — already written, reuse unchanged
- `pareto_table.v` — BRAM inferred, loaded with `$readmemh` from a *synthetic* table
- A testbench showing the right entry comes out for a given operating point
- One utilisation report, even if the design is trivial

The point is to prove the Vivado half is real and not a promise.

---

## Suggested split

| Who | Owns |
|---|---|
| Sanjay | Deliverable 1 — build the converter in ADS, reproduce the base-paper figure |
| Aamir | Deliverable 2 — device extraction, loss and soft-switching model in Python |
| Amritha | Deliverable 4 — Vivado RTL and testbench; also runs the sweep for 3 once 1 and 2 land |

Deliverable 3 depends on 1 and 2, so it is the last to start and the first to be cut if time runs
out. Do not let it be cut — it is the scientific core. Cut scope from 4 instead.

---

## Also do, and it is quick

**Resolve the 25 partial citations.** Title, authors and venue are confirmed; volume and page
numbers are not. VIT has IEEE Xplore — this is an afternoon of work for one person and it removes
the easiest possible criticism.

---

## Tools

### Already installed on this machine

Python 3.14 with NumPy, pandas, Matplotlib, SciPy. That covers the sweep scripts, the loss model
and every plot in deliverables 2 and 3.

### You must install these yourselves

| Tool | Notes |
|---|---|
| **Keysight ADS + PEPro** | Licensed. Check the VIT lab first — PEPro is a separate add-on to ADS and the EM extraction depends on it. Confirm access **this week**; if it is not available, deliverable 1 stalls. |
| **Xilinx Vivado ML Edition** | Free, no licence needed for Zynq-7000. Large download (~100 GB installed) — start it overnight. Choose the Zynq-7000 device family during install to cut the size. |
| **GaN device model** | Vendor SPICE model — GaN Systems GS66508B or EPC. Free from the manufacturer. Needed before anything in deliverable 2 works. |

### Free fallback if ADS access is delayed

**LTspice** — free, installs in minutes, will simulate a DAB and give you C_oss(v) and a
double-pulse test. It cannot do the EM inductance extraction, so you would assume a lumped L_k and
note it as a limitation. Better than losing three weeks waiting for a licence.

---

## Order of work this week

1. **Confirm ADS + PEPro access at VIT.** Everything in deliverable 1 waits on this. Do it first,
   today, and have the LTspice fallback ready if the answer is no.
2. Start the Vivado download in the background — it takes hours.
3. Download the GaN vendor model.
4. Read Shi 2020 properly, together. All three of you. You cannot reproduce a figure you have not
   read.
5. Build the DAB and reproduce the figure.

---

## What Review 1 is actually judged on

Not how much you built. Whether the claim from the zeroth review is still standing, and whether
you can show evidence either way. A Review 1 that says *"we tested RQ2 and the coupling is weaker
than expected, here is the data, here is how the scope changes"* is a **stronger** review than one
that shows four half-finished modules and no result.
