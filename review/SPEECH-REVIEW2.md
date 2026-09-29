# Review-II — what to say, slide by slide

**GaN Based Synchronous Buck Converter with an Improved Gate Driver**
Sanjay Kumar 23BEC1447 · Aamir Abdullah 23BPS1197 · Amritha S 23BEC1368
Guide: Dr. Bindu — SENSE, VIT Chennai · Review-II, 30.09.2026

34 slides. **Total 21 min 10 s of speaking.** Bracketed times are cumulative:
if the clock is past one, you are behind. Everything in **bold** is a number
you commit to out loud — each one is on the slide behind you, so you are
never quoting something the examiner cannot see.

**Speaker split** — swap it if you like, but decide before you walk in, and
whoever is not speaking watches the clock and the laptop.

| Slides | Who | What they own |
|---|---|---|
| 1–10 | Amritha | the problem, the scope, the aim, the mechanism |
| 11–22 | Sanjay | implementation, baseline, method, validation, the two runs |
| 23–34 | Aamir | demonstration, results, cost, conclusions |

**The five slides that decide the review are 4, 10, 19, 28 and 30** — the
scope box, the mechanism, the three device models, the loop-inductance
result and the conclusions. If you are running out of time, cut 9, 13 and
14. Never cut those five.

**If the slot is 15 minutes, not 20.** The full script runs 21:10. Cut
these five sections, in this order, and it comes to 18:35. Every one of
them repeats something another slide already shows, so no step in the
argument is lost. Leave the slides in the deck and arrow past them.

| cut | section | why it is safe to drop |
|---|---|---|
| 30 s | 6 · Converter Under Simulation | the converter is on the architecture block diagram already |
| 40 s | 8 · Novelty at Circuit Level | the novelty table makes the same point in words |
| 20 s | 9 · Gate Driver Schematics in KiCad | the same two sheets the previous slide already crops from |
| 35 s | 11–13 · Implementation, three sheets | three schematics the panel can read off the screen unaided |
| 30 s | 16–17 · The two files we wrote | source listings; the block diagram already carries the idea |

Never cut 4, 10, 19, 28 or 30 to make time. Cut these instead.

**If the slot is 15 minutes.** The five above are not enough — they leave 18:35. These four more bring it to 15:55, and unlike the first five they do cost something, so drop them only if the clock forces it.

| cut | section | what it costs you |
|---|---|---|
| 50 s | Demonstration | the recorded film; the LIVE run on 24 shows the same thing, happening |
| 30 s | Six-Parameter Comparison | GaN-against-silicon; the review is about the driver, not the device |
| 35 s | Segmented Driver: Block Structure | slide 16's source listing carries the same structure |
| 45 s | Baseline Reimplementation | the methodology slide already says the search is given to them |

Below about 15 minutes, stop cutting and talk faster: the argument does not survive losing another slide.

**Slides 4, 19, 20, 28, 29, 30 and 31 are new since the mock viva.** They
exist because a hostile examiner landed four attacks on evidence this
project already had and was not showing. Say these slides confidently:
each one is a weakness turned into a stated result.

**Do not read the captions aloud.** They are there so the examiner can check
you afterwards. Say the sentences below and point at the picture.

---

## 1 · Title — 20 s  *(0:20)*
> Good morning. Our project is a **GaN** based synchronous buck converter,
> and the part we designed is the gate driver inside it.

> A buck converter takes a DC voltage and gives a lower DC voltage. Ours
> takes **100 V** in and gives **48.50 V** out.

Get the signed slide on screen first. Do not read the registration numbers.

---

## 2 · Problem Statement & Background — 60 s  *(1:20)*
Start from the device, not from the literature.

> A half-bridge is two transistors in series across the supply. The rule is
> simple: exactly one of them is on at a time. If both are ever on together,
> the supply is shorted through them.

> GaN transistors are used because they switch very fast. That is the whole
> reason to choose GaN — and it is also what causes our problem.

> When the bottom device turns on, the voltage at the midpoint collapses in
> about three nanoseconds. There is a small capacitance inside the top
> device, between its drain and its gate. A fast voltage change across a
> capacitor pushes a current through it, and that current goes straight into
> the gate that is supposed to be held off.

> We measured that gate. It rises to **1.65 V**. The device turns on at
> **1.4 V**. So the device that should be off turns on. That is the fault.

> Solutions exist in the literature — drive in steps, clamp the gate, adjust
> the dead time, hold the gate negative. They report large gains. But they
> report them as one number.

> Our gap is this. Those gains mix two different things: picking one good
> setting once, and changing the setting while the converter is running. Only
> the second one needs a sensor, a lookup table and a controller. Nobody
> separates them, so nobody knows whether that hardware is worth building.

---


## 3 · Aim and Approach — 45 s  *(2:05)*
> So our aim is one question: how much of a gate driver's benefit actually
> needs the driver to re-tune itself while the converter runs, and how much
> you get from choosing one good setting and leaving it alone.

> To answer it we needed a driver whose every setting we could change and
> measure. That is the segmented driver: eight pull-up steps, eight
> pull-down steps, an adjustable dead time, a Miller clamp, and an off rail
> we can take to minus two volts.

> Four steps. Build the converter and check it actually converts. Recreate
> the fault. Fix it one change at a time, so each fix is measured on its own
> run. Then ask whether one fixed setting is enough.

---

## 4 · Scope of the Claim — 45 s  *(2:50)*
**Do not skip this slide to save time.** Most of what an examiner wants to
attack is answered here, by you, before they ask.

> Before the results, what we are and are not claiming.

> We claim three things. A fixed clamp and a negative off-bias raise the
> simulated gate margin on every device model we ran. Runtime adaptation adds
> a further benefit whose size depends strongly on power-loop inductance, and
> we measure that dependence. And the comparison is against our own
> implementation of the published baseline.

> We do not claim experimental validation — nothing has been built. We do
> not claim to reproduce the original authors' measured results; their netlist
> is not published. We do not claim false turn-on is universal. And we do not
> claim a universally optimal setting: the best word moves with the operating
> point, and how much it moves is our result.

---

## 5 · System Architecture — 40 s  *(3:30)*
Point along the arrows, left to right. Do not read the boxes.

> One signal path. A PWM command comes in. The FPGA controller holds the
> control word — that word is what sets the driver's strength. The segmented
> driver shapes the switching edge. The half-bridge drives the load.

> The block in green is what this project designs. It is drawn once and
> placed twice, once for each gate.

> Two things to notice. The control word is set at power-up and never
> changed — there is no sensor and no lookup table in this path. And the red
> arrow is the fault: the switching edge coupling back into the gate that
> should stay off.

---

## 6 · Converter Under Simulation — 30 s  *(4:00)*
> This is the converter itself, and it is drawn from the netlist we simulate,
> so every value on this sheet is the value that ran.

> A hundred volts in on the left, the two GaN devices in the middle, the
> filter and a ten ohm load on the right. It delivers **48.50 V** at
> **236.26 W**, **97.49 %** efficient. The converter works before we start
> arguing about the driver.

---

## 7 · Novelty: Three Added Blocks — 50 s  *(4:50)*
This is the slide that answers "what is actually yours". Be precise, and be
honest about what is not yours.

> The base paper is Zhang and others, ISPSD 2020. This table is their design
> against ours, and only the shaded rows differ.

> The command is theirs. The power stage is theirs. The idea of segmenting
> the output stage is theirs — we are not claiming that.

> Three blocks are added. One: the drive strength is a digital control word
> written by the FPGA, where they use one analogue bias resistor fixed at
> fabrication. Two: an always-on active Miller clamp, which they do not have.
> Three: an off rail selectable to minus two volts, where theirs is tied to
> zero.

> The last row is what those three are worth at our headline operating point.
> Their crosstalk margin is **0.407 V**. Ours is **2.576 V**. From one fixed
> setting.

---

## 8 · Novelty at Circuit Level — 40 s  *(5:30)*
> Same claim, now at circuit level. The converter is on top with the two
> gates ringed — that is what a gate driver drives. Underneath is what sits
> behind those gates, theirs on the left and ours on the right.

> Both of our additions are established practice, and we cite the papers.
> What is new is not the idea of a clamp or a negative rail. It is that the
> base paper has neither, and that we measure what each one is worth on this
> converter.

> The clamp alone is worth **0.82 V** of margin. The rail alone is worth
> **2.01 V**. Together, minus **0.249 V** becomes **2.576 V**.

---

## 9 · Gate Driver Schematics in KiCad — 20 s  *(5:50)*
Cut this slide if you are behind. One sentence otherwise.

> The same two sheets, whole, at the same scale, so you can see nothing has
> been cropped out. These are screen captures of KiCad, not redrawings.

---

## 10 · Crosstalk Mechanism at Device Level — 55 s  *(6:45)*
**This is the slide that shows you understand the physics.** Slow down.

> On the left is the mechanism. The bottom device turns on, the switch node
> falls from **106 V**, and at its steepest that edge is **124 V/ns**. That
> rate of change, times the drain-gate capacitance, is a current — and it has
> nowhere to go except into the gate of the top device.

> On the right is what the driver does about it. The gate node has three
> paths to hold it down. The pull-down slices — the more you turn on, the
> harder the gate is held. The Miller clamp — its own switch and a half-ohm
> path, opened exactly when the other device switches. And the off rail,
> which sets where the gate starts from.

> The important point is that the clamp and the rail are not the same fix.
> The rail moves where the gate starts. The clamp shortens how far it gets
> lifted. Two different mechanisms, so they add instead of overlapping. That
> is why the numbers on the last slide added up.

---

## 11–13 · Implementation, three sheets — 35 s total  *(7:20)*
Sanjay takes over. One sentence each, do not dwell.

> **(10)** This is the converter as an actual KiCad sheet, drawn from the
> netlist, with the two gate drivers as sub-sheets of this page.

> **(11)** This is our driver. Eight pull-up slices, eight pull-down, the
> Miller clamp on the right, the off rail selectable to minus two volts.

> **(12)** And this is the base paper's driver, rebuilt by us in the same
> testbench: seven slices per bank in two stages, one bias resistor, no
> clamp, off rail tied to reference.

---

## 14 · Baseline Reimplementation — 45 s  *(8:05)*
> A word on how we built their driver, because the whole comparison rests on
> it.

> From the paper: a segmented output stage on E-mode GaN, seven slices a bank,
> two-stage engagement, pattern timing in the nought-point-five to five
> nanosecond range, and one external bias resistor selecting the pattern. That
> last one is their contribution — it is the word "Simple" in their title.

> What we had to decide. Slice resistance and device sizing we matched to
> ours, so this compares architectures and not silicon area. And the bias
> setting: their paper fixes it once at design time, but we search both of
> their controls at every corner and run theirs at whatever wins.

> That is more freedom than their design actually has, and we gave it to them
> deliberately. Every methodological choice here runs against us.

---

## 15 · Segmented Driver: Block Structure — 35 s  *(8:40)*
> Here is how a slice works, because the whole study turns on it.

> Each slice is one switch and one resistor. The control word decides whether
> that resistor is eight ohms and in circuit, or one gigaohm and effectively
> out. So drive strength is just how many of the eight parallel paths are
> live — that is all "segmented" means.

> On the right, the clamp: its own switch, half an ohm to the bottom rail,
> and that rail itself selectable to minus two volts.

---

## 16–17 · The two files we wrote — 30 s total  *(9:10)*
> **(14)** This is the actual SPICE source of that output stage, at its real
> line numbers. The clamp is deliberately not one of the slices — it has its
> own switch and its own timing, because it has to hold the gate down while
> the *other* device is switching.

> **(15)** And this is the GaN device model. Vendor models are LTspice-only
> and do not port, so this is written from the EPC2010C datasheet. One
> consequence matters: GaN has no body diode, so reverse conduction costs
> extra, and that is exactly what the minus two volt rail has to pay for in
> dead time. We are not hiding that — it is the cost side of our own result.

---

## 18 · Methodology — 40 s  *(9:50)*
**If you are asked one methodology question, it is this slide.**

> Every comparison in this deck is the same file with one thing changed.

> Held identical: the netlist, byte for byte — not a copy, the same file. The
> device model on both sides. The parasitics. The operating point. The
> solver settings.

> The one thing that moves is named in the right-hand column. For theirs
> against ours, only the driver subcircuit is swapped.

> And we give their driver an advantage it does not have in its own paper: we
> search both of its controls at every operating point and run it at whatever
> setting wins. Ours runs one fixed word everywhere. So any difference left
> is the driver, and it is the comparison that flatters them.

---

## 19 · Model Validation: Three Device Models — 60 s  *(10:50)*
**This is the slide that answers "why should I trust your simulation".**
Point at the last column, not the first.

> Three independent device models: our behavioural model with diode junction
> capacitances, real SKY130 transistors, and the same behavioural model with
> a charge-based capacitance instead of diodes.

> Read the first column. Minus **0.249**, minus **0.563**, plus **0.115**. The
> sign changes. On the charge-based model the off gate never reaches
> threshold, so on that model the fault does not occur at all. We are telling
> you that, because it is true and because it bounds what we claim.

> Now read the last column, which is the configuration we ship. Plus
> **2.576**, plus **2.032**, plus **2.710**. Positive on every model. And the
> ordering of the three configurations is identical under all three.

> So the existence of the fault at the margin is model-dependent. The
> sufficiency of the fix is not. The second is the claim this project makes.

---

## 20 · Numerical Reliability — 50 s  *(11:40)*
> Two questions this answers. Are these numbers physics or solver settings,
> and where is every run.

> We re-ran one word at five timesteps spanning twenty-five times. The
> crosstalk margin the whole result rests on moves **0.14** percent over that
> range. The spurious gate peak moves **0.04** percent. No feasibility verdict
> changes — zero of eighty flip.

> And the grid. Twenty-five thousand nine hundred and eleven completed runs of
> twenty-five thousand nine hundred and twenty. Nine did not complete, and we
> went and found out why rather than rounding the number up. All nine fail
> again when re-run, so they are reproducible, not flaky. All nine abort with
> the same ngspice transient convergence failure at the high-side gate node.
> And all nine are half-fixed settings — clamp without the rail, or rail
> without the clamp. None of them is the configuration we ship.

> One more thing so you hear it from us: switch-node overshoot appears as
> **17.9** percent in our tables and **15.1** percent in the live script. Same
> operating point, ten times the time resolution. The tables quote the finer
> one.

---

## 21–22 · The two runs — 45 s total  *(12:25)*
These slides carry video. Click, let it run, talk over it.

> **(17)** Their driver, in our testbench. The gate that should stay off
> peaks at **0.993 V** against a **1.400 V** threshold. That is **0.407 V**
> of margin — it does not fail, but that is what it has left.

> **(18)** The same sequence, our driver. The gate peaks at minus
> **1.176 V** — **2.576 V** of margin, six times theirs. Same axes, fixed in
> the script, so the two pictures are directly comparable. And this is one
> fixed control word, the same one used at every corner in the study.

---

## 23 · Demonstration — 50 s  *(13:15)*
Aamir takes over. Play the film and narrate only the parts it is showing.

> This is the whole thing end to end. The circuit as its KiCad sheet, the
> tools named and versioned, then their driver and ours on the same bench at
> a hundred volts and ten amps.

> Theirs peaks **0.993 V**, short of the threshold. Ours peaks minus
> **1.176 V**, well clear. And the converter it drives is regulating at
> **48.50 V**, **236.26 W**, **97.49 %** efficient.

> Every number on that screen was computed while the film was being built,
> not typed into a caption.

---

## 24 · Live Simulation — 70 s  *(14:25)*
**This is the slide she asked for. Run it live.** Terminal ready
beforehand, in the repository, font already large.

> I will run it now rather than show you a recording.

Type and run:

```
bash proof/LIVE-SIM.sh
```

While it runs — it takes about ten seconds:

> It is running two transients of one circuit file. Between the two runs,
> exactly two things change: the Miller clamp is enabled, and the gate off
> rail is moved. Nothing else.

When the numbers print:

> There it is. It prints what it just measured next to what our slides claim.
> The off gate reaches **1.649 V** against the **1.65** on our slide, and the
> margin is **2.576 V** against the **2.576** on our slide. Then it draws the
> two waveforms those runs produced.

If it fails to run, say this and move on — do not debug in front of her:

> The recorded run of the same command is on the slide behind me, and the
> script is in the repository.

**If she asks to see the converter itself running, not just the gate** —
there is a second command, about twenty-three seconds:

```
bash proof/LIVE-BUCK.sh
```

> This one runs the whole converter rather than the gate. It prints the
> output voltage, the power and the efficiency it just measured beside what
> our slides claim — **48.50 V**, **236.26 W**, **97.49 %** — and it also
> prices the fix: the crosstalk fix costs about a quarter of an efficiency
> point.

Do not run both unprompted. Slide 20 is the one you owe her; this is the
answer to a follow-up.

---

## 25 · Crosstalk: Fault and Mitigation — 55 s  *(15:20)*
**The result slide.** Point at the four panels in order.

> Two runs, four panels. Top row is the cause, bottom row is the effect.

> Top: the switch node falls, and at its steepest it is **124 V/ns**. That is
> the aggressor, and it is identical in both runs.

> Bottom left, the gate with no clamp and a zero volt off rail. It starts at
> about zero, gets lifted **1.643 V**, and peaks at **1.649 V** — past the
> **1.4 V** threshold. False turn-on.

> Bottom right, same run with the clamp on and the rail at minus two volts.
> It starts at minus **1.941 V**, is lifted only **0.765 V**, and peaks at
> minus **1.176 V**. No false turn-on.

> And you can read both fixes off this picture separately. The rail moved
> where the gate starts. The clamp cut the lift from **1.643 V** to
> **0.765 V**. That is the two mechanisms, measured separately, on one slide.

---

## 26 · Six-Parameter Comparison — 30 s  *(15:50)*
> Silicon, then the base paper, then ours — same converter, same device class.

> Latency goes **17.55** nanoseconds, to **4.04**, to **2.78**. Device power
> goes **8.60 W**, to **2.93**, to **2.60**.

> Be careful how you read that: the device swap accounts for most of it and
> the control swap for the rest. We are not claiming the whole ratio.

> Overshoot is the one row that runs the other way, and it runs that way for
> the same reason the other five do not: silicon does not overshoot because
> its edge is nine times slower — and that slowness is exactly what costs it
> six watts. Speed and device stress are the same knob.

---

## 27 · Comparison with the Base Paper — 70 s  *(17:00)*
**The slide the review turns on.** Do not rush the last paragraph.

> Four operating corners, mildest to hottest. Same netlist, same devices, only
> the driver swapped.

> Their driver as their paper builds it, then their driver re-tuned at every
> corner — which is more freedom than their design actually has, because
> their scheme sets one bias resistor once. Then ours, at one fixed word.

> Two things matter here, and neither is the ratio.

> First, the gap widens under stress. Their best margin falls from
> **0.503 V** at the mildest corner to **0.181 V** at the hottest. Ours goes
> **2.757 V** to **2.251 V**. They degrade exactly where it matters, because
> a clamp does not care how hot the device is. The worst corner is what a
> converter has to survive, and that is **0.181 V** against **2.251 V**.

> Second — and this is the part we would defend hardest — their scheme buys
> its margin by slowing the edge down, sixty-seven to a hundred and three
> volts per nanosecond. Ours runs a hundred and one to a hundred and
> seventy-five — about twice as fast — and still wins by a factor of several.
> The margin is not paid for with switching speed. That is the useful form of
> the result.

> And what it costs us. Our turn-on energy is higher at three of the four
> corners, because the negative rail deepens GaN's reverse drop in dead time
> — we measure that at one to three and a half percent of total loss. Their
> driver needs one resistor; ours needs a clamp device, a negative supply and
> twenty LUTs. For a converter that never leaves one operating point, theirs
> may well be the right engineering.

> One more thing we have to say plainly. Their netlist is not published, so
> this is our implementation of their described scheme, in our testbench. The
> ratio is against that reimplementation. It is not a claim against their
> measured result.

---

## 28 · When Runtime Adaptation Is Worth Building — 65 s  *(18:05)*
**Say this as a finding, not as a caveat.** It is the most interesting
result in the project.

> Our headline says adaptation adds two-point-six percent. That number is
> conditional, and this slide is the condition.

> On the x-axis, power-loop inductance — which is board layout, not the
> transistor. On the y-axis, the ceiling on what any scheduling scheme could
> return. At one-point-five nanohenries it is **13.5** percent. At
> four-point-five it is **0.55** percent.

> So the question "is adaptive gate control worth a sensor, a lookup table and
> a controller" is not a property of the gate driver at all. It is a property
> of the board the gate driver sits on. Below about two-and-a-half
> nanohenries, yes. Above it, no.

> Two honesties about this picture. The series is not monotonic in that band,
> which is why we plot eight points and not a curve. And three nanohenries is
> our nominal simulation condition — it is not a measured layout, and we
> have not built a board to measure it on.

---

## 29 · The Cost of the Fix — 45 s  *(18:50)*
> What the margin is paid for with, in one table.

> It buys plus **2.825** volts of gate margin. It costs **0.24** points of
> converter efficiency, **0.570** watts of loss, and twelve volts of extra
> switch-node peak.

> About **0.22** watts of that loss is third-quadrant conduction. GaN has no
> body diode, so in dead time the device conducts in reverse at threshold plus
> whatever off-bias you applied — the negative rail that buys us margin
> is paid for right there.

> And the stress: a hundred and eighteen volts on a two-hundred-volt part is
> fifty-nine percent of rating, so it is a real cost but not the binding
> constraint at this bus.

---

## 30 · Conclusions — 55 s  *(19:45)*
> Five conclusions.

> One. A clamp with a negative off rail raises the simulated gate margin on
> all three models.

> Two. Choosing one good fixed word is worth **26.5** percent. Re-tuning it
> while running adds **2.6** percent more — about **8.9** percent of the
> total gain — at our nominal three nanohenry loop.

> Three, and this is the one we would defend hardest: that answer is
> conditional. Whether adaptive gate control earns its hardware is decided by
> board layout, not by the driver.

> Four. It is a trade, not a free win, and slide twenty-nine is the bill.

> Five. Simulation only. Nothing has been built, and the comparison is against
> our own implementation of the published baseline.

---

## 31 · What Would Overturn This Result — 40 s  *(20:25)*
> And the conditions under which we would have to revise all of that.

> A measured gate waveform that does not reproduce our simulated transient.
> An extracted loop inductance below two-and-a-half nanohenries — then
> adaptation is worth several times what we report and the recommendation
> inverts. Package parasitics that change the Miller current path. Or the
> original authors publishing a netlist that outperforms our implementation of
> their scheme, in which case every ratio in this deck needs recomputing.

> We would rather state those ourselves than be shown them.

---

## 32 · Next Steps — 30 s  *(20:55)*
> What is left is bench work, not more simulation.

> Place-and-route on a chosen board. Synthesis is done; it stops there
> because the pin constraints are placeholders, and doing it properly means
> driving the two hundred megahertz clock from a clock manager rather than
> off a pin.

> And a hardware half-bridge, measured. That is the whole of the remaining
> risk, and we will say it plainly: everything in this deck is a simulation
> of a converter that has not been built, resting on one behavioural GaN
> model.

---

## 33 · References and close — 15 s  *(21:10)*
> These are the papers this design engages with directly; number ten is the
> base paper, and it is the one we reimplemented and measured against.

> Everything in this deck — the netlists, the models, the scripts, the
> figures — runs on request from the repository on the last slide. Thank you.

---

# If she asks

Short answers. Say the sentence, stop, and let her ask the next one.

**"So what is actually your contribution?"**
> Three blocks the base paper does not have — a digital control word, an
> always-on Miller clamp, and a selectable negative off rail — and a measured
> answer to a question the field states as one number: what re-tuning is
> worth on its own.

**"And what is that answer?"**
> Choosing a better fixed word is worth **26.5 %**. Adapting it per operating
> point adds **2.6 %** — about **8.9 %** of the total gain. The absolute
> ceiling on any scheduling scheme is **3.5 %**. So the sensor, the ADC and
> the lookup table are buying the small share, and that is a design decision
> we can now make on evidence.

**"Why should I believe the numbers?"**
> Every one of them is regenerated by a named script, the summary file says
> which script produces which number, and a checker fails the build if a
> slide and the data disagree. The command on slide twenty re-derives two of
> them in ten seconds.

**"Is the clamp your idea?"**
> No, and we say so on the slide. Miller clamps and negative off-bias are
> established practice and we cite four papers. What is ours is that the base
> paper has neither, and that we measure what each is worth here.

**"Have you built it?"**
> No. It is simulated, in ngspice, on one behavioural GaN model written from
> the EPC2010C datasheet. That is the largest limitation in the project, it
> is on slide twenty-four, and a measured half-bridge is the next step.

**"Why is your turn-on energy worse?"**
> Because GaN has no body diode. During dead time the device conducts in
> reverse, and that costs the threshold plus whatever off-bias you applied.
> The negative rail that buys us crosstalk margin is paid for there. We
> measure it at one to three and a half percent of total loss.

**"Why ngspice and not a commercial tool?"**
> Everything here is open source, so there is nothing in the project anyone
> needs a licence to reproduce. We cross-checked the same circuit in LTspice.

**"How does the FPGA fit in?"**
> The controller is written, verified and synthesised, and its output drives
> the SPICE power stage directly. On the real part it is twenty LUTs and
> twenty flip-flops. It is not placed and routed — that is on the next-steps
> slide.

---

# Before you walk in

- [ ] Slide 1 signed by Dr. Bindu and scanned back in as slide 1.
- [ ] `bash proof/PREFLIGHT.sh` run on the presentation laptop, green.
      It rehearses both live commands and prints READY at the end.
- [ ] Terminal open in the repository, font size up, slide 20 rehearsed once.
- [ ] Videos on slides 17, 18, 19 and 20 play — open the .pptx, not the PDF.
- [ ] The PDF on a pen drive as the fallback.
- [ ] One rehearsal against a clock. Aim to finish at 14:00, not 14:25.
