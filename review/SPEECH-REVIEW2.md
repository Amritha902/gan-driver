# Review-II — what to say, slide by slide

**GaN Based Synchronous Buck Converter with an Improved Gate Driver**
Sanjay Kumar 23BEC1447 · Aamir Abdullah 23BPS1197 · Amritha S 23BEC1368
Guide: Dr. Bindu — SENSE, VIT Chennai · Review-II, 30.09.2026

25 slides. **Total 14 min 20 s of speaking.** Bracketed times are cumulative:
if the clock is past one, you are behind. Everything in **bold** is a number
you say out loud, and every one of them is on the slide behind you.

| Slides | Who |
|---|---|
| 1–7 | Amritha — problem, aim, architecture, mechanism |
| 8–16 | Sanjay — schematics, method, validation, the two runs |
| 17–25 | Aamir — live demo, results, cost, conclusions |

**The four that decide the review: 4, 13, 20 and 22** — the architecture, the
three device models, the loop-inductance result, and the conclusions. If you
run short, cut 6, 9 and 10. Never cut those four.

**Do not read the captions aloud.** They are there so the panel can check you
afterwards. Say the lines below and point at the picture.

---

## 1 · Title — 25 s  *(0:25)*

Get the signed slide up first. Do not read the registration numbers.

> Good morning. Our project is a **GaN** synchronous buck converter, and the
> part we designed is the gate driver inside it. It takes **100 V** in and
> gives **48.50 V** out.

> One thing before any result: the size of the fault we study depends on the
> device model. On one of our three models the off-state gate never crosses
> threshold at all. So we do not claim the fault is universal — we claim our
> fix holds on every model we tried.

---

## 2 · Problem Statement & Background — 55 s  *(1:20)*

> A half-bridge is two transistors in series across the supply. Exactly one
> is on at a time. If both are ever on, the supply is shorted through them.

> GaN is used because it switches fast. That is the reason to choose it, and
> it is also what causes our problem. When the bottom device turns on, the
> midpoint collapses in about three nanoseconds. A small capacitance inside
> the top device, between drain and gate, turns that fast change into a
> current — and it goes into the gate that is meant to stay off.

> We measured it. **1.65 V**. The device turns on at **1.4 V**.

> Fixes exist in the literature. But they report their gains as one number,
> and that number mixes two different things: picking one good setting, and
> changing the setting while the converter runs. Only the second needs a
> sensor, a lookup table and a controller. That is our gap.

---

## 3 · Aim and Approach — 40 s  *(2:00)*

> So our aim is one question: how much benefit does runtime adaptation add
> beyond a fixed setting, and under what conditions is it worth the hardware?

> Four steps. Build the converter and check it converts. Recreate the fault.
> Fix it one change at a time, each measured on its own run. Then ask whether
> one fixed setting is enough.

> Two tools. **ngspice** runs every simulation. **KiCad** draws every
> schematic, from the same netlist ngspice runs — so the picture and the
> simulation cannot drift apart.

---

## 4 · System Architecture — 45 s  *(2:45)*

Point along it. Do not read the boxes.

> A PWM command comes in. The FPGA holds the control word — six fields, which
> is **720** possible words. The segmented driver shapes the switching edge.
> The half-bridge drives the filter and the load.

> The green block is what this project designs, and this is what is inside
> it: eight pull-up segments, eight pull-down, an always-on Miller clamp, and
> a mux that selects the off rail at zero or minus two volts.

> Two things to notice. The word is set at power-up and never changed — no
> sensor, no lookup table in this path. And the red arrow is the fault:
> the switching edge coupling back into the gate that should stay off.

---

## 5 · Novelty: Three Added Blocks — 40 s  *(3:25)*

> The base paper is Zhang and others, ISPSD 2020. Only the shaded rows differ.

> The command is theirs. The power stage is theirs. Segmenting the output
> stage is theirs — we do not claim it.

> Three blocks are added: a digital control word where they use one analogue
> bias resistor, an always-on Miller clamp they do not have, and an off rail
> selectable to minus two volts where theirs is tied to zero.

> At our headline corner that takes the crosstalk margin from **0.407 V** to
> **2.576 V**, from one fixed setting.

---

## 6 · Novelty at Circuit Level — 30 s  *(3:55)*

> The same claim at circuit level: the converter on top with the two gates
> ringed, theirs below left, ours below right.

> Both of our additions are established practice and we cite the papers. What
> is new is that the base paper has neither, and that we measure what each
> is worth here: the clamp **0.82 V**, the rail **2.01 V**.

---

## 7 · Crosstalk Mechanism at Device Level — 50 s  *(4:45)*

**Slow down — this is where you show you understand the physics.**

> Left, the mechanism. The bottom device turns on, the switch node falls from
> **106 V**, and at its steepest that edge is **124 V/ns**. That rate times
> the drain-gate capacitance is a current with nowhere to go but the top gate.

> Right, what the driver does about it. Three paths hold that gate down: the
> pull-down segments, the Miller clamp with its own half-ohm path timed to
> the other device's edge, and the off rail that sets where the gate starts.

> The important point is that the clamp and the rail are not the same fix.
> The rail moves where the gate starts; the clamp shortens how far it gets
> lifted. Two mechanisms, so they add rather than overlap.

---

## 8–10 · The three schematics — 30 s total  *(5:15)*

One sentence each. Do not dwell — they are there to be looked at.

> **(8)** The converter as an actual KiCad sheet, drawn from the netlist, with
> the two gate drivers as sub-sheets of this page.

> **(9)** Our driver: eight pull-up segments, eight pull-down, the Miller
> clamp on the right, the off rail selectable to minus two volts.

> **(10)** The base paper's driver, rebuilt by us in the same testbench:
> seven segments per bank in two stages, one bias resistor, no clamp.

---

## 11 · Segmented Driver: SPICE Implementation — 25 s  *(5:40)*

> This is the actual source of that output stage, at its real line numbers.

> Each segment is one switch and one resistor: in circuit when the control
> word reaches it, one gigaohm when it does not. The clamp is deliberately
> not one of the segments — it has its own switch and its own timing, because
> it must hold the gate down while the *other* device is switching.

---

## 12 · Methodology — 40 s  *(6:20)*

**If you get one methodology question, it is this slide.**

> Every comparison in this deck is the same file with one thing changed.

> Held identical: the netlist, byte for byte — the same file, not a copy. The
> device model. The parasitics. The operating point. The solver settings.

> What changes is named in the right column. For theirs against ours, only
> the driver subcircuit is swapped.

> And we give their driver an advantage its own paper does not have: we
> search both of its controls at every corner and run it at whatever wins,
> while ours runs one fixed word everywhere. Every choice here runs against
> us.

---

## 13 · Model Validation: Three Device Models — 50 s  *(7:10)*

**This answers "why should I trust your simulation".** Point at the last
column, not the first.

> Three independent device models: our behavioural model, real SKY130
> transistors, and the same model with a charge-based capacitance.

> Read the first column. Minus **0.249**, minus **0.563**, plus **0.115**.
> The sign changes. On the third model the gate never reaches threshold, so
> the fault does not occur at all. We are telling you that, because it is
> true and it bounds what we claim.

> Now the last column — the configuration we ship. Plus **2.576**, plus
> **2.032**, plus **2.710**. Positive on every model, same ordering on every
> model.

> So the existence of the fault is model-dependent. The sufficiency of the
> fix is not. The second is our claim.

---

## 14 · Numerical Reliability — 40 s  *(7:50)*

> Two questions this answers: are these numbers physics or solver settings,
> and where is every run.

> Left, total switching energy against timestep, over a twenty-five times
> range. Right, every metric as a percentage of its own converged value.
> Flat is the result: the margin moves **0.14** percent, the gate peak
> **0.04** percent, and no feasibility verdict changes.

> On the grid: **25,911** completed runs of 25,920. Nine did not, and we went
> and found out why. All nine fail again on a re-run, all nine are the same
> ngspice convergence failure at the high-side gate, and all nine are
> half-fixed settings — clamp without the rail, or rail without the clamp.
> None is the configuration we ship.

---

## 15–16 · The two runs — 60 s total  *(8:50)*

These carry video. Click, let it run, talk over it.

> **(15)** Their driver in our testbench. The gate that should stay off peaks
> at **0.993 V** against a **1.400 V** threshold — **0.407 V** of margin.

> **(16)** The same sequence, our driver. It peaks at minus **1.176 V** —
> **2.576 V** of margin, six times theirs. Same axes, fixed in the script, so
> the two pictures are directly comparable. And this is one fixed control
> word, the same one used at every corner in the study.

---

## 17 · Live Simulation — 60 s  *(9:50)*

**Run it. Terminal open in the repository beforehand, font already large.**

> I will run it now rather than show a recording.

```
bash proof/LIVE-SIM.sh
```

While it runs, about ten seconds:

> Two transients of one circuit file. Between them, exactly two things
> change: the Miller clamp is enabled, and the gate off rail is moved.

When the numbers print:

> It prints what it just measured next to what our slides claim. The off gate
> reaches **1.649 V** against the **1.65** on our slide, and the margin is
> **2.576 V**. Then it draws the two waveforms.

If it fails, say this and move on — do not debug in front of the panel:

> The recorded run is on the slide behind me and the script is in the
> repository.

If asked to see the converter itself, there is a second command, about
twenty-three seconds: `bash proof/LIVE-BUCK.sh` — it prints **48.50 V**,
**236.26 W**, **97.49 %**.

---

## 18 · Crosstalk: Fault and Mitigation — 45 s  *(10:35)*

Point at the four panels in order.

> Two runs, four panels. Top row the cause, bottom row the effect.

> Top: the switch node falls, at its steepest **124 V/ns**. Identical in both
> runs.

> Bottom left, no clamp and a zero-volt off rail: the gate starts near zero,
> is lifted **1.643 V**, peaks at **1.649 V** — past the **1.4 V** threshold.

> Bottom right, same run with the clamp on and the rail at minus two volts:
> it starts at minus **1.941 V**, is lifted only **0.765 V**, peaks at minus
> **1.176 V**.

> You can read both fixes off this one picture. The rail moved the start; the
> clamp cut the lift from **1.643** to **0.765**.

---

## 19 · Comparison with the Base Paper — 55 s  *(11:30)*

**The slide the review turns on.**

> Four corners, mildest to hottest. Only the driver changes.

> Two things matter here, and neither is the ratio.

> First, the gap widens under stress. Their best margin falls **0.503** to
> **0.181 V**; ours goes **2.757** to **2.251 V**. They degrade exactly where
> it matters, because a clamp does not care how hot the device is.

> Second — and this is what we would defend hardest — their scheme buys its
> margin by slowing the edge down. Ours runs about twice as fast and still
> wins by a factor of several. The margin is not paid for with switching
> speed.

> And the bottom line: their netlist is not published, so every ratio here is
> against our implementation of their scheme, not their measured result.

---

## 20 · When Runtime Adaptation Is Worth Building — 50 s  *(12:20)*

**Say this as a finding, not as an apology.**

> Our headline says adaptation adds two-point-six percent. That is
> conditional, and this is the condition.

> X-axis, power-loop inductance — which is board layout, not the transistor.
> Y-axis, the ceiling on what any scheduling scheme could return. At
> one-point-five nanohenries it is **13.5** percent. At four-point-five it is
> **0.55** percent.

> So "is adaptive gate control worth a sensor, a lookup table and a
> controller" is not a property of the driver at all. It is a property of the
> board it sits on. Below about two-and-a-half nanohenries, yes. Above, no.

> Two honesties: the series is not monotonic in that band, which is why we
> plot eight points and not a curve — and three nanohenries is our nominal
> condition, not a measured layout.

---

## 21 · The Cost of the Fix — 35 s  *(12:55)*

> What the margin is paid for with.

> It buys **2.825 V** of gate margin. It costs **0.24** points of efficiency,
> **0.570 W** of loss, and twelve volts of extra switch-node peak.

> About **0.22 W** of that loss is third-quadrant conduction — GaN has no
> body diode, so in dead time it conducts in reverse and pays the threshold
> plus whatever off-bias we applied. The rail that buys us margin is paid for
> right there.

---

## 22 · Conclusions — 45 s  *(13:40)*

> Six, quickly.

> One: the clamp with a negative off rail raises the gate margin on all three
> models. Two: a good fixed word is worth **26.5** percent; re-tuning while
> running adds **2.6** percent more. Three, and the one we would defend
> hardest: that answer is conditional — board layout decides it, not the
> driver. Four: it is a trade, and slide twenty-one is the bill. Five:
> simulation only, nothing built. Six: a measured waveform that does not
> match ours, or a loop inductance below two-and-a-half nanohenries, would
> change conclusion three.

---

## 23 · Next Steps — 25 s  *(14:05)*

> What remains is bench work, not more simulation. Place-and-route on a
> chosen board — synthesis is done, the pin constraints are placeholders. And
> a hardware half-bridge, measured. That is the whole of the remaining risk.

---

## 24–25 · References and close — 15 s  *(14:20)*

> These are the papers this design engages with; number ten is the base
> paper, the one we reimplemented and measured against.

> Everything in this deck runs on request from the repository. Thank you.

---

# If she asks

**"What is actually your contribution?"**
> Three blocks the base paper does not have — a digital control word, an
> always-on clamp, a selectable negative off rail — and a measured answer to
> a question the field reports as one number: what re-tuning is worth alone.

**"And the answer?"**
> A better fixed word is worth **26.5 %**. Adapting per operating point adds
> **2.6 %** — about **8.9 %** of the gain. The ceiling on any scheduling
> scheme is **3.5 %**. So the sensor and the lookup table buy the small share.

**"Why should I believe the numbers?"**
> Every one regenerates from a named script, and a checker fails the build if
> a slide and the data disagree. The command on slide 17 re-derives two of
> them in ten seconds.

**"Is the clamp your idea?"**
> No, and the slide says so. Clamps and negative off-bias are established
> practice; we cite four papers. What is ours is that the base paper has
> neither, and that we measure what each is worth here.

**"Have you built it?"**
> No. Simulated in ngspice on one behavioural GaN model written from the
> EPC2010C datasheet. That is the largest limitation, it is on slide 23, and
> a measured half-bridge is the next step.

**"Why is your turn-on energy worse?"**
> GaN has no body diode. In dead time the device conducts in reverse and pays
> the threshold plus the off-bias. The rail that buys crosstalk margin is
> paid for there — we measure it at 1 to 3.4 % of total loss.

**"Why ngspice and KiCad?"**
> Both are open source, so nothing here needs a licence to reproduce. KiCad
> draws every schematic from the same netlist ngspice runs, so the picture
> and the simulation cannot drift apart.

---

# Before you walk in

- [ ] Slide 1 signed by Dr. Bindu and scanned back in as slide 1.
- [ ] `bash proof/PREFLIGHT.sh` on the presentation laptop — it rehearses both
      live commands and prints READY.
- [ ] Terminal open in the repository, font size up, slide 17 rehearsed once.
- [ ] Videos on slides 15, 16 and 17 play — open the .pptx, not the PDF.
- [ ] The PDF on a pen drive as the fallback.
