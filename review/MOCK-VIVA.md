# Mock viva — the presentation, then thirty minutes of a hostile examiner

Run against the shipping deck on 29.09.2026. Both live commands were actually
executed; the terminal output below is real, pasted from the run, not typed.

The examiner here is **fictional** — an external examiner invented to be as
hard on this project as anyone could reasonably be. She is not Dr. Bindu and
nothing here should be read as words your guide said or would say.

Where the student loses, it says so. That is the point of the exercise: the
questions you cannot answer tonight are the only ones worth working on.

---

> **Superseded in part.** Everything the examiner attacked has since been built into the deck — slides 4, 19, 20, 28, 29, 30 and 31 exist because of this transcript. Read it for the questions, not for the state of the deck. One number in it was also wrong: the clamp-only case is +0.570 V of margin, not +0.83 V, which is that case's gate peak.


# PART 1 — The presentation (14 min)

**[1 · Title]**

Good morning. Our project is a GaN based synchronous buck converter, and the
part we designed is the gate driver inside it. A buck converter takes a DC
voltage and gives a lower DC voltage — ours takes 100 V in and gives 48.50 V
out.

**[2 · Problem]**

A half-bridge is two transistors in series across the supply. Exactly one is
on at a time. If both are ever on together, the supply is shorted through
them.

GaN is used because it switches very fast. That is the whole reason to choose
it, and it is also what causes our problem. When the bottom device turns on,
the midpoint voltage collapses in about three nanoseconds. There is a small
capacitance inside the top device, between drain and gate. A fast voltage
change across a capacitor pushes current through it, and that current goes
into the gate that is supposed to be held off.

We measured that gate. It reaches 1.65 V. The device turns on at 1.4 V. So
the device that should be off turns on.

Solutions exist — drive in steps, clamp the gate, adjust dead time, hold the
gate negative — and they report large gains. But they report them as one
number. Our gap: those gains mix picking one good setting once, and changing
the setting while the converter runs. Only the second needs a sensor, a
lookup table and a controller. Nobody separates them, so nobody knows whether
that hardware is worth building.

**[3 · Aim]**

One question: how much of a gate driver's benefit actually needs live
re-tuning, and how much comes from choosing one good setting and leaving it.

**[4–5 · Architecture and converter]**

PWM in, an FPGA controller holding the control word, the segmented driver
shaping the edge, the half-bridge driving the load. The control word is set
at power-up and never changed — no sensor, no lookup table in that path. The
converter delivers 48.50 V at 236.26 W, 97.49 % efficient.

**[6–7 · What is ours]**

The base paper is Zhang et al., ISPSD 2020. The command is theirs, the power
stage is theirs, and segmenting the output stage is theirs — we do not claim
it. Three blocks are added: a digital control word in place of one analogue
bias resistor, an always-on active Miller clamp, and an off rail selectable
to −2 V. Clamp alone is worth +0.82 V of margin, rail alone +2.01 V;
together −0.249 V becomes +2.576 V against their +0.407 V.

**[9 · Mechanism]**

The switch node falls from 106 V and at its steepest that edge is 124 V/ns.
That rate times C_GD is a current with nowhere to go but the top gate. The
gate has three paths holding it down: the pull-down slices, the Miller clamp
with its own half-ohm path timed to the other device's edge, and the off rail
setting where the gate starts. The rail moves the starting point; the clamp
shortens the lift. Two mechanisms, so they add.

**[16 · Method]**

Every comparison is the same file with one thing changed. Same netlist byte
for byte, same device model, same parasitics, same operating point, same
solver. And we give their driver a freedom its own paper does not have: we
search both its controls at every corner and run it at whatever wins. Ours
runs one fixed word everywhere.

**[21–23 · Results]**

Without the clamp the off gate rests near zero, is lifted 1.643 V and peaks
at 1.649 V — past threshold, false turn-on. With clamp and −2 V rail it rests
at −1.941 V, is lifted only 0.765 V, peaks at −1.176 V. No turn-on.

Across four corners their best margin falls +0.503 → +0.181 V; ours goes
+2.757 → +2.251 V. And their scheme buys margin by slowing the edge, 67–103
V/ns; ours runs 101–175 V/ns, about twice as fast, and still wins. The margin
is not paid for with switching speed.

**[24 · What is left]** Place-and-route, and a hardware half-bridge. Thank you.

---

# PART 2 — Thirty minutes with the examiner

**EXAMINER: Prof. Kalyani Raghavan** (external, fictional)
**CANDIDATE: the project team**

---

## 0:00 — She does not start with a compliment

**EX:** Before anything else. You have shown me one number, 2.576 volts, on
one slide, from one simulator, running one device model that you wrote
yourself. Why should I treat that as a result and not as arithmetic you
performed on your own assumptions?

**CAND:** Because it is not the only model we ran it on. The same comparison
is on real SKY130 transistors and on a charge-based capacitance model, and
the shipped configuration is safe under all four.

**EX:** All four. Then show me all four, not the one that flatters you.

**CAND:** No-clamp, clamp-only, clamp-plus-rail. Behavioural model: −0.249,
+0.570, +2.576 volts. SKY130 transistors: −0.563, +0.031, +2.032. Charge-based
capacitance: +0.115, +0.800, +2.710.

**EX:** Stop. Read me the third one again.

**CAND:** Plus 0.115 volts.

**EX:** Positive. So on that model there is no fault at all. The thing your
entire project exists to fix does not happen. Your problem statement is a
property of your model.

**CAND:** The *sign* of the no-clamp case is model-dependent, yes, and that is
stated in our results summary in those words. What is not model-dependent is
the shipped configuration: it is safe under all four, with margin between
2.0 and 2.7 volts. The fault's existence at the margin is uncertain; the
fix's sufficiency is not.

**EX:** That is a much smaller claim than the one on your slide, which says
"false turn-on" in red capitals.

**CAND:** It is a smaller claim, and the slide should carry it. That is fair.

> **Where the candidate lost ground.** She is right. Slide 21 asserts the
> fault flatly. Say the model-dependence *before* she finds it — "on our
> device model it crosses; on a charge-based model it does not, and the fix
> holds on all of them" — and it becomes rigour instead of a concession.

---

## 0:06 — The headline result

**EX:** Your contribution, you say, is separating what re-tuning is worth.
What is the number?

**CAND:** Choosing a better fixed word is worth 26.5 %. Adapting it per
operating point adds 2.6 % — about 8.9 % of the total gain. The ceiling on
any scheduling scheme is 3.5 %.

**EX:** And your conclusion from that is that the adaptive hardware is not
worth building.

**CAND:** Our conclusion is that it buys the small share, and that is now a
decision on evidence rather than assumption.

**EX:** Over what range of power-loop inductance?

**CAND:** Three nanohenries.

**EX:** One value. And if I build the board badly?

**CAND:** The ceiling goes from 13.5 % at 1.5 nH to 0.6 % at 4.5 nH.

**EX:** So say it out loud. At 1.5 nanohenries, adaptation is worth *four
times* what your headline says, and your conclusion reverses. Your entire
finding is a statement about layout quality, not about gate drivers. Why is
that not the title of your project?

**CAND:** Because the band where it matters is below about 2.5 nH, and 3 nH
is what a realistic layout of this converter gives —

**EX:** "Realistic" according to whom? You have not built a board. You have
no layout. You told me yourself place-and-route is future work. You are
defending your choice of the one parameter your conclusion is most sensitive
to by appealing to a board that does not exist.

**CAND:** That is correct and I cannot answer it from measurement. What I can
say is that the sensitivity is measured, published in the deck, and the
direction is the honest one — we are reporting the case where our own
headline is *least* impressive.

> **This is the strongest attack in the viva and it lands.** There is no
> winning answer tonight. The recoverable position is to reach it first:
> present the 13.5 %-to-0.6 % sweep as a finding, not a caveat. "Our result
> is conditional on loop inductance, we quantified the condition, and below
> 2.5 nH the opposite conclusion holds" is a defensible thesis. Waiting to be
> dragged there is not.

---

## 0:13 — She asks for the demo

**EX:** You claim every number regenerates. Run something. Now.

**CAND:** `bash proof/LIVE-SIM.sh`

```
  GaN half-bridge -- crosstalk, simulated live
  ----------------------------------------------------------------
  machine  vm        2026-09-29 16:10:22
  spice    ngspice-42 : Circuit level simulation program
  circuit  sim/dpt.cir          device  models/egan.lib
  changing ONLY  CLKEN (clamp)  and  VNEG (off rail)

  (a) fastest drive, no clamp, 0 V off rail ...
      OFF-device gate reaches  +1.6488 V   against a 1.400 V threshold
      margin -0.2488 V     false_turn_on = 1   SHOOT-THROUGH

  (b) same circuit, clamp on, -2 V off rail ...
      OFF-device gate reaches  -1.1759 V
      margin +2.5759 V     false_turn_on = 0   SAFE

  ----------------------------------------------------------------
                             on the slide     this run
  OFF gate, no clamp  [V]            1.65       1.6488
  margin, shipped     [V]           2.576       2.5759
  ----------------------------------------------------------------
  two ngspice transients, 5.0 s wall clock on this machine
```

**EX:** Five seconds. So the entire evidentiary basis of this project is five
seconds of computation.

**CAND:** That is the double-pulse test. The converter is a separate run.

**EX:** Run it.

**CAND:** `bash proof/LIVE-BUCK.sh`

```
  (a) shipped word: clamp on, -2 V off rail, 8 slices ...
      in     100.00 V  x  2.4233 A  =   242.33 W
      out     48.50 V  x  4.8691 A  =   236.26 W
      efficiency  97.49 %        loss 6.071 W
      switch node peaks at 115.1 V on a 100 V bus  (15.1 % overshoot)

  (b) same converter, clamp off, 0 V off rail ...
      efficiency  97.73 %        loss 5.502 W
      the crosstalk fix costs 0.24 efficiency points (0.570 W more loss)

                                 on the slide     this run
  output voltage      [V]               48.50      48.4967   match
  output power        [W]              236.26     236.2580   match
  efficiency          [%]               97.49      97.4945   match
  switch-node peak    [V]              115.07     115.0671   match

  note: the GaN-vs-Si table says 17.9 % for this overshoot, not 15.1 %.
```

**EX:** Your own script just told me one of your slides disagrees with it.

**CAND:** It did, and it told you why in the next line: the table re-runs
three settled cycles at a 0.02 nanosecond step to resolve the edge; this run
uses the sweep's 0.2 nanosecond step. Same operating point, ten times the
time resolution. The script prints the discrepancy rather than hiding it
because we would rather you hear it from us.

**EX:** Then which is the number?

**CAND:** 17.9 %, the resolved one. And it is checked: refining the timestep
25× moves the drain overshoot by 1.14 % and the gate peak by 0.04 %, and
flips zero of eighty feasibility verdicts.

> **Won.** A script that volunteers its own inconsistency, with the reason and
> a convergence study behind it, is worth more than a script that agrees with
> everything. Let her find it — then have the answer ready in one breath.

---

## 0:19 — The comparison

**EX:** You claim six times the margin of the base paper. You did not run the
base paper. You ran your reimplementation of a description.

**CAND:** Correct, and it is on the slide in those words: their netlist is
not published, the ratio is against our reimplementation, and it is not a
claim against their measured result.

**EX:** Convenient. You built their circuit, so you chose how good it is.

**CAND:** Which is why we gave it an advantage its own paper does not have.
Their scheme sets one bias resistor once at design time. We search both of
their controls at every corner and run theirs at whatever wins, while ours
runs one fixed word everywhere. Every methodological choice we made runs
against us.

**EX:** Then why is your first table column identical to your second at three
of four corners? Either your search is broken or the column is decorative.

**CAND:** Neither — their built setting happens to be the search optimum at
three corners. It differs at the mildest: 0.338 against 0.503 volts. The
lead text says so.

**EX:** It says so *now*.

**CAND:** It does. It was wrong until this week, and it was our own
consistency checker that did not catch it, because the wrong number was a
real number from the same file — just the wrong column. The checker now binds
each column to its own series.

> **Neutral-to-won.** Admitting a caught error, naming the mechanism that let
> it through, and showing the guard that closes it reads as engineering
> maturity. Do not volunteer this one unprompted — but do not flinch.

---

## 0:24 — The cost side

**EX:** What does your fix cost the converter?

**CAND:** 0.24 efficiency points. 0.570 watts, of which about 0.22 is
third-quadrant conduction — GaN has no body diode, so during dead time the
device conducts in reverse and pays the threshold plus the off-bias we
applied. The rest is the clamp's own switching.

**EX:** And overshoot?

**CAND:** The −2 V rail takes the switch node from 106 V to 118 V on a 100 V
bus.

**EX:** Eleven points of extra overshoot on a 200-volt-rated device, to fix a
fault that on one of your four models does not occur. Is that engineering, or
is it a solution looking for a problem?

**CAND:** On a 200 V part, 118 V is 59 % of rating, so it is not a stress
problem at this bus. And at a 200 V bus we found something worse and fixed
it: the decoupling branch undamped gave 464 volts and 112 amps of
shoot-through — 132 % overshoot. Damped, 208 volts, 4.1 %. That was found by
opening a waveform, not by reading a scalar.

**EX:** So your own converter had a catastrophic failure mode that your
metrics did not report.

**CAND:** Yes. That is why we now open waveforms.

---

## 0:28 — The close

**EX:** Three things I am not satisfied with. You have not built anything.
Your fault's existence depends on your model. And your headline conclusion
inverts inside the range of layout inductance a student's first board would
land in. What do you say?

**CAND:** That all three are true, that the first and third are on the
next-steps slide, and that the second should be on the results slide and will
be. The measured half-bridge is the whole of the remaining risk and we have
never said otherwise.

**EX:** Then you know what your Review-III is. Not more simulation. A board,
a probe, and that inductance measured rather than assumed.

---

# What to fix before tomorrow

Three of these are twenty-minute jobs and buy back most of what was lost.

1. **Say the model-dependence before she finds it.** One line on slide 21 or
   in the mouth: "on our device model the gate crosses threshold; on a
   charge-based capacitance model it does not — the fix holds on all four
   models we tried." Turns the worst hit into a strength.

2. **Own the inductance sensitivity as a finding.** Have the sentence ready:
   "our result is conditional on power-loop inductance — we measured the
   condition, and below about 2.5 nH the opposite conclusion holds." Say it
   while pointing at your own number, not hers.

3. **Know the 17.9 % versus 15.1 % answer cold.** Two instruments, ten times
   the time resolution, convergence study behind it. One breath.

4. **Do not oversell the ratio.** "Six times our reimplementation of their
   described scheme" — say the whole phrase every time, even when it is
   clumsy. The moment you shorten it to "six times the base paper" you have
   made a claim you cannot support.

5. **Have one number you do not know.** 25,911 of 25,920 transients
   completed. Nine did not. If asked why, the answer tonight is "I would have
   to look" — so look, or be ready to say it plainly. Inventing a reason is
   the only unrecoverable move in a viva.
