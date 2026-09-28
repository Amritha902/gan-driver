# Review-II speech script — 32 slides, ~10 minutes

Timings are the budget, not a target to hit exactly. Total ≈ 9 min 30 s,
which leaves slack in a 10-minute slot because you will talk faster than this
reads. **Slides 8, 14 and 23 are the ones that matter.** If you are running
out of time, cut 16 and 22, never those three.

Numbers in **bold** were re-verified by running the script that produces them.

---

## 1–3 — Title, signature, agenda (30 s)

Do not read these. Get the signed title slide on screen, say the project name
once, and move.

> "This is a segmented gate driver for GaN HEMTs. The question the project
> asks is how much of an active gate driver's benefit actually needs the
> adaptive hardware everyone builds for it."

---

## 4, 9, 19 — Section dividers (2 s each)

Dark slides: **The problem · What we built · What we found.**
Say the settings on the slide and move on. They break the deck into three
acts; they are not content.

---

## 5 — Problem statement (45 s)

> "In a GaN half-bridge, when the bottom device turns on the switch node
> slews in a few nanoseconds. That dV/dt drives current through the top
> device's gate–drain capacitance and lifts its gate. If it passes the
> threshold — **1.4 V** on our device — the top device partially turns on
> while the bottom one is already on. That's false turn-on, and it's a
> shoot-through path."
>
> "The easy fix is to slow the switching down. That works, and it throws away
> the switching-loss advantage you bought GaN for. So the real question isn't
> how to stop false turn-on. It's how to stop it while keeping the speed."

If asked why energy storage: the bidirectional half-bridge is the core of a
storage converter, its losses are paid twice — once charging, once
discharging — and its operating range is wide enough that one fixed gate
setting is provably not optimal everywhere.

---

## 6 — The base paper (30 s)

> "Thirteen references, grouped by what the driver *does*, not by date. Three
> clusters choose a setting or regulate it in analogue. Only cluster D makes
> the setting a digital code — and that's what makes an exhaustive search
> possible at all. That's where we sit."

---

## 7 — The closest published drivers (40 s)

Walk the columns once, then stop on the last one.

> "Title, author, what each paper set out to do, and then the column that
> matters: the gap we found in it and the part of that gap we fill."
>
> "[10] is the closest published driver architecturally — a segmented driver
> for e-mode GaN, seven slices, pattern timing half a nanosecond to five. But
> it's an ASIC with a fixed pattern set. It doesn't ask what the pattern space
> is worth."

If asked why a SiC paper is the base: because the method is the ancestor. A
gate waveform chosen by a multibit digital code — that's the idea we take to
GaN, where the device has no body diode and the trade changes.

---

## NEW — GaN against silicon, measured (45 s) — **panel asked for this**

The first Review-1 comment. Answer it with the table, not with adjectives.

> "Same converter, same driver, same on-resistance class — only the device
> changes. Latency from PWM to switch node: 2.8 nanoseconds on GaN, 17.6 on
> silicon. The edge itself, 0.8 against 6.7. Power in the devices, 2.6 watts
> against 8.6. Gate drive, 35 milliwatts against 1.5 watts — forty times.
> Efficiency, 97.4 against 95.1."

Then take the losing row yourself, before anyone asks.

> "And the row where silicon wins. It doesn't overshoot; we do — 18 per cent
> against minus 1.5. That isn't something we missed. Silicon's edge is nine
> times slower, and that slowness is exactly what costs it six watts. Speed
> and device stress are the same knob. Picking GaN is picking to manage the
> stress, and this deck is how we manage it."

If asked why the two are driven at different gate voltages: each at its own
rated drive, 5 V and 10 V. A silicon MOSFET at 5 V is barely enhanced and
would lose on a technicality instead of on physics.

---

## 8 — THE GAP (60 s) — **core slide, do not rush**

> "Every active gate driver paper reports one number: the improvement over a
> conventional driver. That number bundles two completely different things."
>
> "Effect one: choosing a better fixed setting. You do it once, at design
> time. It costs nothing at run time — no sensor, no ADC, no lookup table."
>
> "Effect two: adapting that setting as load, bus voltage and temperature
> move. *This* is the one that needs the sensing hardware the whole
> architecture is sold on."
>
> "Nobody separates them. Not because it isn't interesting, but because
> separating them needs an exhaustive search of the setting at every
> operating point, and nobody has run one. That's the gap. And it matters because only
> effect two justifies the hardware — so if it's small, the field is paying
> for something a design-time choice already gives you."

---

## NEW — The goal, and whether this serves it (45 s) — **core slide**

> "Before the aim, the goal, because everything else serves it. Build a
> synchronous buck converter for an energy-storage system out of GaN HEMTs, and
> make it work at the switching speed GaN is bought for."
>
> "Why GaN: same converter, same job, only the device swapped — at 500 kilohertz
> GaN wastes 6.2 watts against silicon's 12.6, and the lead widens to
> seventy-eight percent at a megahertz and ninety percent at light load. It
> never turns back."
>
> "What GaN costs you: the same speed that wins is what breaks it. The device
> that is supposed to be off gets pushed to 1.65 volts against a 1.4 volt
> threshold. That is a shoot-through."
>
> "What we build about it: the segmented driver, with the clamp and the minus
> two volt rail. Minus 0.249 volts of margin becomes plus 2.576."
>
> "One thing before the results, because it gets asked. The title says
> converter and most of what follows is a gate driver. Those are one claim.
> The converter is what we are building; the driver is the one part of it we
> redesigned, because on GaN that is the part that decides whether the
> converter is buildable at the speed the device is bought for. Ours runs —
> 97.7 percent efficient. What a textbook buck converter will not do is
> survive its own switching edges at 500 kilohertz against a 1.4 volt
> threshold. Every number in this deck is measured on the converter."

---

## 10 — Proposed solution and aim (40 s)

Open with the aim. The examiner is listening for it.

> "The aim is to measure how much of an active gate driver's benefit actually
> requires per-operating-point adaptation, and how much comes from simply
> choosing a better fixed setting."
>
> "The driver has six things you can set. We make all six a digital word —
> 720 of them — and we search every one at every operating point. Not a shortlist.
> That's what makes each per-operating-point optimum a true optimum."

---

## 11 — How it works, one use case (30 s)  — **new, use it**

The slide that makes the project legible to someone seeing it cold. Walk the
top row, then the bottom row. Do not read the boxes.

> "One case: a storage converter, load falling from ten amps to two as the
> pack fills. The top row is what the controller decides — and the only live
> decision is that shaded diamond, one comparator picking between two dead
> times. Everything else is fixed at power-up at power-up. The bottom row is what the
> circuit then does: the switch node falls, that dV/dt pushes charge into the
> off device's gate, and either it crosses 1.4 volts or it does not. Ours does
> not, by 2.58 volts."

---

## 12–13 — Architecture and circuit (45 s)

Slide 9 left to right in one sentence, then stop on the dashed block.

> "PWM in, the FPGA holds the setting, the setting sets the segmented output
> stage, that drives the half-bridge. Everything solid is configured once at
> power-up. The dashed block — sensing, ADC, lookup table — is the adaptive
> machinery, and this whole project is a measurement of what that one block
> buys."

Slide 10 is the real circuit.

> "Every element here is in sim/dpt.cir. Eight pull-up slices, eight
> pull-down, the active Miller clamp, the off-bias mux. C_GD on Q2, in red, is
> the crosstalk path."

---

## 14 — WE IMPLEMENTED THE BASE PAPER (60 s) — **core slide**

This is the slide that separates you from a literature review. Be fair to
them; the comparison is stronger when you are.

> "Citing a base paper isn't a comparison, so we built theirs. Their driver is
> a segmented output stage on the same device we use — seven slices brought in
> as a timed pattern across the switching edge, the pattern selected by one
> bias resistor. No Miller clamp, no negative rail, because those are ours. We
> ran it inside our own testbench, byte-identical except for the driver."
>
> "Their approach works. **Plus 0.407 volts** of margin — their pattern alone
> clears the threshold. And it beats our own constant code, which
> false-turns-on at **minus 0.249**. So their contribution is real and we
> reproduce it."
>
> "And we quote them at their *best*. Their pattern has two controls, and we
> searched their own stated range to find the setting that suits them most.
> Across that range they run from plus 0.407 down to minus 0.278 — so which
> setting you hand them decides how far ahead we look. We handed them the best
> one."
>
> "Our Miller clamp gets **plus 0.570** — only marginally past them. The
> clamp alone is not the story. It's the negative off-bias that does the work:
> **plus 2.576 volts**, about **6.3 times** their best margin."

If asked what's genuinely new: not the segmented stage or the pattern, those
are theirs. Ours is the two actuators they don't have, every field made
programmable from an FPGA where theirs is an ASIC with a fixed pattern set,
and the exhaustive search that lets us price adaptation — which their paper
cannot do.

---
## NEW — The architecture, end to end (40 s) — **after Vivado**

> "One more thing we had to fix, and it was in our own work rather than in the
> literature. The controller was verified in Icarus. The power stage was
> verified in ngspice. The two never touched. The FPGA emits eight
> thermometer-coded wires per bank; the SPICE driver took an integer. A bug in
> the decoder would have passed the Verilog bench and stayed invisible in every
> figure ngspice produced."
>
> "So we made them meet. A new testbench reproduces the double-pulse schedule at
> the real 200 megahertz clock, and its waveform dump becomes sixteen sources —
> one per wire — into the SPICE driver. Same deck, same devices, same
> measurement. Only the slice selection changes."
>
> "Margins agree to eighty-one millivolts, and that difference is timing, not
> encoding. And it found a real bug: the dead time is dt_cycles plus one, times
> five nanoseconds. Fifteen nanoseconds is two cycles, not three. Anyone who
> mapped our swept grid onto hardware by dividing by the clock period would have
> built a driver one cycle slow at every operating point — and neither half of
> the verification could have caught that alone."

*If asked why it matters:* it is the difference between a design that has been
verified and one whose two halves have each been verified against a different
assumption.

---

## NEW — The two architectures, side by side (50 s) — **panel asked for this**

Two slides, same grid, same block positions. Let the diagram do the work.

> "This is Zhang's driver. Seven slices in two stages, and the pattern across
> the edge is chosen by one bias resistor, fixed at design time. Two slots on
> this diagram are empty, and that's why I'm showing it: no active clamp, no
> negative off rail."

Then the next slide, same layout.

> "Same grid, same positions — so what changed is what you can see. The
> output stage is theirs. The three green blocks are ours. Instead of a
> resistor, seg_gate_ctrl.v on an FPGA: six fields, 720 words, re-writable at
> run time. And the two empty slots fill — the active Miller clamp, and the
> switchable minus two volt rail."

The sentence to land:

> "Their drive strength is decided before the chip exists and can never
> change. Ours is a register write. That's what made a 720-word sweep
> possible at all — and a resistor could never have told us that re-tuning
> is worth only 2.6 per cent."

---

## NEW — Theirs and ours on six parameters (50 s) — **panel asked for this**

Same converter, same GaN device, same output stage. Only the control swaps.

> "Latency 2.8 against 4.0 nanoseconds. The edge 0.8 against 2.1 — two and a
> half times faster. Power in the devices 2.6 watts against 2.9."

Do not stop there. Two rows go against us and they are the credible part.

> "Two rows go the other way. We spend thirteen per cent more gate power, and
> we overshoot 18 per cent where they overshoot 3. Both for the same reason:
> we switch faster. What that buys is the next slide — their crosstalk
> margin is plus 0.4 volts, ours is plus 2.6."

If asked whether the comparison is fair: their pattern step is a delayed copy
of their own PWM, so it lands the same distance after turn-on every cycle,
which is what their one-knob scheme does. Same devices, same parasitics, same
solver options. The only thing that differs is the control.

---

## NEW — The two architectures side by side (45 s)

Put it up, then be quiet for two seconds. It is a slide people read.

> "Six rows, the same rows on both sides. Their control source is one bias
> resistor, fixed at fabrication. Ours is an FPGA — six fields, 720 words,
> written at run time. Their drive strength is seven slices split two and
> five; ours is eight and eight, thermometer coded."

> "Then the row that is the whole point. Off-state hold: they have none. We
> have an active Miller clamp. And their off rail is tied to its reference;
> ours selects minus two volts."

> "The power stage row is identical, deliberately. Same device, same
> converter, same output stage. Only the control differs — which is why the
> numbers underneath attribute to the control and to nothing else."

Read the red line out loud. Do not let them find it.

> "And where it costs us: thirteen per cent more gate power, and eighteen per
> cent overshoot against their three."

If asked whether the diagram matches the code: every count on it is parsed
from models/zhangdrv.lib and models/segdrv.lib at build time. Change either
library and the figure changes with it.

---

## NEW — The circuit as ngspice reports it (30 s)

> "A drawing is what somebody believes the circuit is. This is what was
> actually solved — ngspice's own listing, the circuit as it parsed it."

> "rpu1 through rpu8, rpd1 through rpd8: the sixteen slices, each switched in
> by that conditional — runit if the control word asks for it, one gigaohm if
> it does not. rclk is the Miller clamp. That is the contribution as netlist,
> rather than as a box with '8 slices' written in it."

> "And rdec is one ohm, the damped value."

If asked why not a schematic: ngspice has no schematic plotting, it is a
simulator. There are KiCad sheets and a draw.io file in the repository for
the drawn version; this slide is the authoritative one.

---

## NEW — The converter across its envelope (45 s) — **core slide**

> "Every converter number in this project used to be taken at one hundred
> volts. This is all eight bus and load points."

> "The margin column is the answer: threshold minus the highest the off gate
> reaches while the other device is conducting. Positive at every point, plus
> 2.14 volts at the worst. The off device stays off across the range."

Now take the two red rows before anyone asks.

> "At a two hundred volt bus the peak exceeds the device rating. That is not
> the driver failing — the overshoot there is the smallest in the whole
> sweep, three and four per cent. It is that a two-hundred-volt-rated part
> cannot run a two hundred volt bus, because any overshoot at all then
> exceeds the rating. So the envelope is fifty to one hundred and fifty volts
> on this device. Two hundred needs a higher-rated part, not a different
> driver."

If asked how it was found: we ran it, and the first attempt shoot-throughed
at 464 V with 112 A through a 10 A load. The cause was a bus decoupling
branch we had added ourselves to cure a different problem, left undamped.
Damping it fixed the 200 V case and improved every metric at 100 V too.

---

## NEW — Head to head with the base paper (60 s) — **core slide**

> "Same deck, same GaN, same power loop, same parasitics. Only the driver is
> swapped. We hold one fixed word at all four corners — because our own result
> says a fixed word is the deliverable, so we hold ourselves to it. They are
> re-optimised at every corner, which is more freedom than their own design
> has: their paper sets one bias resistor once."
>
> "Even so we lead at all four: five and a half times at the mildest corner,
> twelve point four at the hottest. And look at the direction — their margin
> falls from half a volt to a hundred and eighty millivolts as it gets hot;
> ours barely moves. A clamp does not care how hot the device is."
>
> "The part I would want a reviewer to notice is the switch-node slew. Their
> scheme reduces crosstalk by slowing the edge — sixty-seven to a hundred volts
> per nanosecond. Ours runs a hundred to a hundred and seventy-five, about
> twice as fast, and still wins by a factor of several. **The margin is not
> bought with switching speed.**"
>
> "It is not free. Our turn-on energy is higher at three of four corners —
> that's the minus two volt rail deepening GaN's dead-time drop, a penalty we
> already measure at one to three percent of total loss. And their driver is
> one resistor against our clamp, negative supply and twenty LUTs. For a
> converter that never leaves one operating point, theirs may be the right
> engineering."

*Say this before anyone asks:* this is our implementation of their described
scheme in our testbench. Their netlist is not published. It is not 6.3× their
measured result and we do not claim it is.

---

## NEW — Closing the loop (50 s)

> "Everything up to here was measured open loop — the duty ratio was a
> parameter and nothing moved while we measured. Right instrument for a
> switching edge, wrong description of a converter: a storage system's pack
> voltage sags all day and the load steps whenever something turns on."
>
> "So we closed it, around the same power stage and the same drivers, and then
> disturbed it on purpose. Fifty point zero one volts, fifty point zero zero
> after a two-times load step, fifty point zero one after the input goes from a
> hundred to a hundred and twenty. Worst error one hundredth of a percent.
> The open-loop converter walks to sixty volts on that line step, because
> V-out equals D times V-in and nothing in it knows V-in moved."
>
> "Two compensators did not work before this one did. The first period-doubled
> — a four microsecond triangle on a two microsecond switching period. And a
> proper type-two cannot do this job at all: one zero cannot beat the output
> LC's minus one-eighty. Type three adds the second zero, which is exactly the
> missing phase."

*If asked about phase margin:* we do not claim one. It needs an AC analysis
about a periodic operating point, which ngspice cannot do on a switching deck.
What is shown is weaker: one fixed set of values, stable through both
disturbances. And the K-factor design was four times out on gain — we scaled
it empirically and measured each step, and that is on the slide.

---

## NEW — Does the result depend on the model? (55 s) — **core slide**

> "Every margin in this deck was measured with an output stage whose slices are
> ideal switches. Ten milliohms on, a gigaohm off, no gate charge, no
> threshold. Fair for comparing control words. Not a driver anyone can build."
>
> "So we rebuilt the same output stage in real SKY130 five-volt transistors and
> ran it again. The architecture survives — the constant word still fails, the
> clamp still beats no clamp, clamp plus negative bias still beats clamp
> alone."
>
> "**But the reason it survives changes, and I want to correct our own
> headline.** On real devices the clamp alone gives thirty-one millivolts. Not
> half a volt — thirty-one millivolts, at one corner, with nothing left for
> temperature or a worse layout. That is not a fix. The minus two volt off-bias
> is the fix, and the clamp is what makes the off-bias hold."
>
> "The ideal switch was flattering the clamp, because it pulls the gate down
> through ten milliohms while a real NMOS pulls it through a channel that has
> to be turned on first."

> "And we did the same thing to the device's capacitance — junction diodes
> against a charge formulation. The ordering survives that too. But the
> no-clamp row changes sign: minus 0.249 volts with diodes, plus 0.115 with
> charge. The two laws differ under forward bias, and the aggressor is
> forward-biased through its own turn-on, so it slews differently."
>
> "So I want to be precise: **'the constant word causes false turn-on' is
> model-dependent.** It is not a measurement. And that is an argument for the
> design rather than against it — the shipped configuration is safe under all
> four models we tried, with over two volts of room in each. It is the only
> one whose verdict survives changing an assumption underneath it."

*Limits to say yourself:* the predrivers in that stage are still behavioural,
and there is no equivalent check on the GaN side — no open PDK ships a 200 V
GaN HEMT, so that one model is still what everything rests on.

---

## NEW — The hardware, costed (45 s)

This is the answer to "why is there no hardware". Do not apologise; answer.

> "Three tiers. One, the FPGA on a real board — days; the constraints file
> already targets the part, and it shows the slices toggling and the dead
> time sweeping on silicon. Two, a GaN half-bridge evaluation board at
> forty-eight volts, two to four weeks — that is the one that matters,
> because it measures the off device's gate during the other one's turn-on,
> which is our central claim. Three, our own eight-slice stage on a custom
> board: months, Review-III."

Then the part that shows the thinking rather than the wanting.

> "Our edge is 0.78 nanoseconds. Seeing it needs about 450 megahertz of scope
> bandwidth at minimum, realistically a gigahertz. And a ten-to-one probe with
> a ground clip carries roughly ten nanohenries in its ground lead, which
> manufactures ringing that is not in the circuit — a GaN gate has to be
> probed with a short pigtail or coax, or the trace shows the probe rather
> than the converter."

> "And one fact: no commercial IC implements an eight-slice independently
> controllable segmented driver. Tier three is eight single-channel drivers
> in parallel, enabled per slice, summed through eight ohms — which is
> exactly what our model file already describes."

---

## NEW — Does the architecture close the gaps? (50 s) — **core slide**

> "This is the slide that answers whether the project serves its purpose. Six
> gaps in the published work, down the left. What our architecture does about
> each. And the evidence, with the script that produces it."
>
> "Five are closed. The sixth — does a fitted schedule generalise to an
> operating point it was not fitted on — we answered in the negative: the
> comparator is worse than the fixed word on three of four held-out corners.
> That is a result, not a failure, and it is the honest one."
>
> "The seventh row is the one that is open. All of this is simulation. No
> silicon has been measured. That is Review-III, and the title of this project
> says 'simulation study' for that reason."

---

## 15 — Work completed, 90 % (30 s)

> "Ninety percent, and it is counted rather than asserted — twelve blocks with
> a weight each, ten finished, the weights on the slide so you can argue with
> them."
>
> "The problem is reproduced and fixed. The full search is done: 720 settings at
> four operating points, about 34,600 simulation runs across every study."
>
> "The remaining ten percent is place-and-route on a chosen board, and a
> hardware half-bridge on a bench. No amount of further simulating delivers
> either. The architecture is finished; the measurement of it on real silicon
> is not."

---

## 16 — Where we are, and what is next (20 s) — *cut this first if short on time*

> "ngspice for the simulation, LTspice for the portable schematic, Icarus for
> the RTL, Yosys for synthesis, MATLAB for the analysis. Cadence is Review-II
> and needs remote access — that's the ask."

---

## 17 — FPGA controller (35 s)

> "Three modules emitting exactly the setting the SPICE model consumes.
> Dead time gets a live register; drive strength is fixed at power-up — that's the
> study's own result built into the hardware."
>
> "Eight properties, all passing. And we mutation-tested it: inject a real
> shoot-through bug and the bench catches it 221 times. A passing test doesn't
> prove much; a test that can fail does."
>
> "And it has been through Vivado. 2024.1.2, on an Artix-7 xc7a35t:
> **20 LUTs and 20 flip-flops**, a tenth of a percent of the part.
> Register-to-register timing closes at **200 MHz with 1.996 nanoseconds of
> slack** — and 200 MHz is the requirement, because the dead-time grid starts
> at 5 ns and 100 MHz cannot express it."
>
> "The report also says thirty-four endpoints fail. Those are all
> clock-to-output-pin, against a placeholder four-nanosecond I/O constraint we
> wrote before we knew the board. The output buffer alone is 3.49 ns. The
> logic on that path is 0.3 ns. It is an I/O budgeting question, not a design
> that misses its clock."
>
> "The Vivado export is written too — top level, timing constraints and a
> build script, with its own bench passing under Icarus. Not yet run: Vivado
> is Windows and Linux only, so that is a Review-II item."

**If the panel opens the timing report and reads "Timing constraints are not
met":** agree, then separate the two numbers before they do.

- The **intra-clock** table is the design: `clk_200`, WNS **1.996 ns**, zero
  failing endpoints out of 25. Hold and pulse-width also met. The controller
  runs at 200 MHz.
- The **34 failures are all in path group `**default**`** — register to output
  *pin*. The constraint is `set_max_delay 4.000`, which we wrote as a
  placeholder in the XDC and labelled as one. The worst path spends 3.49 ns in
  the LVCMOS33 output buffer and 2.92 ns on clock insertion, because the clock
  was fed straight from a pin with no MMCM to compensate it. Actual logic:
  0.295 ns.
- The fix is stated in `rtl/vivado/VIVADO-TODO.md` and was written before the
  run: drive `clk_200` from a Clocking Wizard MMCM, and set a real output
  constraint once the board is known.

Do not claim timing is met outright, and do not concede the design misses its
clock. Both would be wrong.

**Both designs are now in Vivado**, so the cost of programmability is vendor
numbers, not an estimate: **33 LUTs fully programmable against 20 fixed at power-up** --
strapping saves 13 LUTs and 10 flip-flops, 39 % of the logic, for the 2.6 % of
baseline that adaptation buys. The older yosys pair (53 vs 27) is superseded;
same direction, but the honest reduction is 39 %, not 49 %.

---

## 18 — Vivado on screen (30 s)

Two slides, one point: the FPGA half is real, and here is the tool saying so.

> "Twenty LUTs and twenty flip-flops on an Artix-7 — a tenth of a percent of
> the part. Register-to-register timing closes at 200 megahertz with 1.996
> nanoseconds spare. Synthesised again with every field left programmable it
> is thirty-three LUTs, so fixing the setting at power-up — which is this study's own
> result built into the hardware — saves 39 % of the logic."

**If asked about "Timing constraints are not met":** see the note under slide 19.
Internal timing is met; the 34 failures are clock-to-pin against a placeholder
I/O constraint.

---

## 20 — Result 1, crosstalk (30 s)

> "Fastest drive, no clamp: the gate that should be OFF reaches **1.65 V** against a 1.4 V threshold.
> That's the failure. Clamp on with −2 V off-bias: **−1.18 V**, a **2.58 V**
> margin."

---

## 21 — Result 2, what re-tuning is worth (45 s)

> "Full search at every operating point. The most that re-tuning per operating point can gain is
> **3.5 %** against the best single fixed setting. And it isn't spread out —
> three operating points lose one to four percent, one loses **12.7**. It's carried by
> the dead time, and the dead time by one light-load operating point. Freeze pull-up
> drive strength and it costs **zero** — and drive strength is what the
> published papers actually re-tune."
>
> "And 3.5 % is the generous figure. On the denser 36-point operating grid a
> fixed setting loses only **2.0 %**. We quote the larger one because it is the
> number that argues against our own conclusion."

**If asked which number is right:** both, for different questions. 3.5 % is the most
that can be gained across four deliberately spread operating points — the widest spacing we test.
2.0 % is what a real converter sees sweeping a dense grid. Reproduce either
with `scripts/ceiling.py` and `scripts/lut.py`. Quoting only the smaller one
would be self-serving; quoting only the larger one hides that the effect is
even weaker in practice.

---
## 22 — MATLAB (25 s) — *cut second if short*

> "720 settings, **504 of them safe**, seven settings on the trade-off curve. The objectives
> genuinely conflict — you cannot minimise loss, overshoot and crosstalk
> margin together."

---


## 23 — Result 3, the split (45 s) — **core slide**

> "Here's the split nobody separates. Choosing a better fixed setting: **26.5 %**
> of baseline. Adapting it per operating point on top of that: **2.6 %**. So
> adaptation is **8.9 %** of the total gain — the other 86.6 % needs no
> sensing, no ADC, no lookup table."
>
> "And one comparator — a threshold on bus voltage — takes 47 % of even that
> 3.9. So a full sense-plus-ADC-plus-lookup-table system is left justifying
> **4.7 %**."
>
> "Two comparators reach 61 %, which brings it down to 3.7. We report the
> one-comparator number because the corner worth isolating shares its bus
> voltage, its load and its temperature with other corners — so a single
> threshold cannot select it, however much we would like to quote 3.7."

If asked why not just quote 3.7: because it is not one comparator, and saying
"one comparator" when it takes two is the kind of thing that gets found.

Say plainly: this is a negative result about the adaptive premise, and it is
the contribution.

---

## 24 — Result 4, loop inductance (25 s)

> "Adaptive control pays only below about **2.5 nH** of loop inductance. Above
> that a fixed setting is nearly as good. And loop inductance is board layout,
> not the transistor."

---

## 24b — THEIRS, THEN OURS (1 min 20 s for the pair)

Two films, 35 s each, played back to back. Do not talk over either. One line
before the first, one line between them, one line after the second.

Before the first:

> "This is the base paper's driver, in KiCad, then in the simulator, then its
> output. Their own best setting at this corner."

Between them:

> "Same bench, same corner, same axes. Only the driver changes."

After the second:

> "Their gate gets to **0.407 V** of the threshold. Ours stops **2.576 V**
> short of it."

**The one thing to say if anyone squints at the two plots.** Say it without
being asked, because it is the thing that makes the pair mean anything:

> "Both plots are on fixed axes — set in the script, not autoscaled. If they
> were autoscaled they would look equally dramatic and tell you nothing."

**If they ask why theirs is not simply failing.** It is not, at this corner,
and do not overclaim. Theirs stays under the threshold at 100 V and 25 °C.
The gap opens where it matters: at 200 V and 125 °C theirs has 0.181 V and
ours 2.251 V, which is the four-corner table two slides later.

## 25 — DEMO (1 min 40 s)

The film runs **99 s** and is four things: the circuit, the tools, the output,
and the comparison. Play it and stay quiet — it carries its own captions,
so nothing needs saying over it. One sentence going in, one coming out.

Going in:

> "This is what we built, what we built it with, what came out, and how it
> compares to the paper we started from. One script makes all of it — it
> reads both netlists off disk and runs the simulator three times while the
> film is being built."

The four parts:

1. **The implementation** — KiCad itself, on screen, with the sheet open.
   The converter, then our driver in to the active Miller clamp, then the base
   paper's driver in the same application: fourteen columns instead of eight,
   no clamp branch, VN tied to the local reference.
2. **The software** — KiCad drew the sheets; ngspice-42 ran them. The device
   model, our driver and theirs are all named, then the simulator's own output.
3. **The output** — the switch-node edge and the gate it lifts, with the
   threshold, the peak and the margin arrowed on the plot. Then the converter
   delivering power, arrowed the same way.
4. **Theirs and ours** — both drivers on the same bench at the same corner,
   overlaid, then the margin at four corners and what the change costs.

**If they ask whether the schematics were drawn by hand.** No, and that is the
point: `scripts/kicad_schematic.py`, `kicad_driver_sheet.py` and
`kicad_basepaper_sheet.py` generate the `.kicad_sch` files from `sim/buck.cir`,
`models/segdrv.lib` and `models/zhangdrv.lib`. A hand-drawn sheet would still
show RDEC at 20 mOhm. KiCad then opens and renders them, which is what the film
captures.

**If they point at the switch symbol and say "that is a MOSFET".** They are
right about the symbol and it does not affect the result. Say it in this order,
and do not get defensive — the sheet already says it in its own note, which is
on screen in the film:

> "KiCad ships no GaN HEMT symbol, so the sheet uses an n-channel enhancement
> MOSFET symbol — the same substitution EPC make in their own datasheets. The
> symbol is a drawing convention. What is simulated is `models/egan.lib`, which
> has **no body diode**: reverse conduction during dead time costs
> V_th + |V_off| + I·R_ds(on), not one diode drop."

That distinction is not cosmetic, and it is worth saying why: the absence of a
body diode is what makes the −2 V off rail cost something. A silicon part
would freewheel through its body diode at about 0.7 V; this one drops
V_th + |V_off| + I·R_ds(on) instead, which is why dropping the off rail from
0 V to −2 V costs the converter 0.24 efficiency points. The symbol is
borrowed; the physics in the model is not.


Coming out:

> "Their driver leaves **0.407 V** of margin below the threshold. Ours leaves
> **2.576 V**. Same netlist, same device, same corner — the only thing swapped
> is the driver. Across four corners that ratio runs from 5.5 to 12.4 times,
> and the latency and device dissipation both come down as well."

**If they ask whether their driver was set up to lose.** It was not, and say
so plainly: `scripts/headtohead.py` searched both of their controls at every
corner, and the film runs their driver at the setting that search found best
FOR THEM — read out of `results/headtohead.txt`, not chosen by us. Their own
paper offers one bias resistor set once at design time, so this gives them a
per-corner freedom the published design does not have.

**If it will not play**, `github.com/Amritha902/gan-driver` has the file and
`python3 scripts/demo_review2.py` rebuilds it. Do not debug in the room — go
to slide 15 and offer to run the simulation live instead, which is stronger
than the film anyway.

---

## 25b — OR WE CAN RUN IT NOW (20 s, or 30 s if they say yes)

This slide exists to be offered, not read. Say it and then stop talking.

> "Everything you have just seen was recorded. If you would rather not take a
> recording's word for it, I can run the same two simulations on this machine
> now — it takes about ten seconds."

**If they say yes.** `bash proof/LIVE-SIM.sh` from the repository root. It
prints what it measures beside what the slide claims, then opens the
waveforms. Say one sentence while it runs:

> "Two runs of the same circuit file. The only things changing between them
> are the Miller clamp and the off rail — everything else is held."

Then read the two rows off the screen and stop. **1.649 V** against the
deck's 1.65, **2.576 V** margin against the deck's 2.576.

**If they say no**, you have still made the offer, which is most of the value.

**If it will not start**, do not debug. The left-hand pane on this slide is a
recording of the same command, made on a machine where it did run, with the
real pauses in it -- ngspice takes about two seconds per transient and the
recording does not hide that. Play it and say so:

> "That is the same command, recorded. The pauses are ngspice solving."

Then move on. A presenter who reaches for a terminal twice has lost the room.

**Do not** run it if the machine is not the one you tested on. Check ngspice
is on PATH before the review; the script checks too, and fails politely, but
not in front of a panel.

---

## 25c — OR RUN THE CONVERTER (20 s, or 40 s if they say yes)

25b runs the double-pulse bench: one switching edge, which is where the
crosstalk result is measured. A bench is not a converter — it never delivers
power to a load — and a reviewer who has followed this far will ask whether
the thing actually works. This is the answer, and it also runs live.

> "That was the test bench. If you want to see the converter itself, I can
> run it now — 100 volts in, 48.5 out, 236 watts into a 10 ohm load, for 150
> switching cycles. About twenty seconds."

**If they say yes.** `bash proof/LIVE-BUCK.sh` from the repository root. It
runs the shipped word, then the same converter with the fix switched off,
and prints both beside what the slides claim. One sentence while it solves:

> "Same devices, same drivers, same netlist as the bench. Now switching
> continuously into an output filter, which is the part a bench cannot show."

Then read the table: **48.50 V** out at **236.26 W**, **97.49 %** efficient,
every row marked *match*. The waveform it opens has four panels — the output
starting up and settling, the switch node chopping at 500 kHz, the gate drive
with the −2 V rail visible under it, and the inductor current triangle,
2.25 A of ripple on 4.87 A.

**The question this invites, and the answer.** The second run — clamp off,
0 V rail — comes out *more* efficient: 97.73 % against 97.49 %. Say it before
they do.

> "Yes. The safety costs 0.24 points, about 0.57 watts. That is the trade,
> and it is the reason the double-pulse result matters: without it you are
> paying nothing and getting a device that turns on when it should not."

If pressed on where the 0.57 W goes, about 0.22 W of it is arithmetic you can
do at the board: GaN has no body diode, so during dead time the off device
conducts in its third quadrant at V_th + |V_off| + I·R_ds(on). Dropping the
off rail from 0 V to −2 V adds 2 V to that, for the 45 ns of dead time in
every 2 µs period, at 4.87 A — 2 × 4.87 × 45/2000 = 0.22 W. The rest is the
clamp's own switching and the edge it changes. Do not claim more than that;
the measured figure is 0.57 W and only part of it is accounted for.

**The overshoot number.** The screen says 15.1 %. The GaN-versus-silicon
table says 17.9 %. Same operating point, different instrument, and the script
says so on screen: `panel_metrics.py` re-runs three settled cycles at a
0.02 ns step to resolve the edge, where this run uses the sweep's 0.2 ns step.
If they catch it, you have already answered it.

**If it will not start**, `results/buck_recording.mp4` is the same command
recorded, with the real fifteen-second pause in it. Same rule as 25b: play it,
say what it is, move on.

**Before the review**, `bash proof/PREFLIGHT.sh` rehearses both scripts and
fails if either measures something the slides do not say.

---

## 26 — Conclusion and next steps (40 s)

> "Choosing the setting well matters enormously — roughly fivefold in
> switching energy. Adapting it does not: 2.6 %, and one comparator takes most
> of that."
>
> "Stated positively, and this is the deliverable: use the recommended fixed
> word with a light-load comparator, and the full adaptive system is left
> justifying 3.4 % of the achievable gain."
>
> "What it does not support: no silicon has been measured, and one device
> model underlies everything. Review-II is the transistor-level output stage
> in Cadence — and sub-nanosecond dead-time control needs silicon, not fabric:
> the 2025 driver we cite reaches 0.19 ns where a 200 MHz FPGA grid is 5 ns.
> That's why we need Cadence access."

---

## 27–29 — References, thanks (10 s)

> "Thirty references, against a minimum of eight to ten. All thirty are
> verified against the publisher record — authors, volume, issue and pages
> resolved by DOI, not typed in. Thank you."

If asked how they are organised: four clusters by what the driver *does*,
not by date. A–C choose or regulate the setting in analogue; only D makes it
a digital code, which is what makes an exhaustive search possible.

---

# Likely questions

**"Show me the Miller clamp in the schematic."**
sim/dpt.cir with models/segdrv.lib — `Sclk out nclk clk ref SWP` with
`Rclk nclk vn 0.5`, a half-ohm switch from the off device's gate to the
negative rail, timed separately from the pull-down. It clamps to the negative
rail, not the source — clamping to source would fight the −2 V bias. Do not
open the .asc sheets for this; they're teaching drawings and don't have it.

**"Did you actually implement the base paper or just cite it?"**
Implemented. models/zhangdrv.lib, run in our own testbench with only the
driver swapped, and there is a slide for it. Their approach works — +0.407 V
at their best setting — and beats our own constant code, which fails at
−0.249 V. We searched their own parameter range to quote them at their best
rather than at a setting we chose for them.

**"Isn't 8.9 % an artefact of your cost function?"**
Partly, and we quantified it rather than defending it. Over 106 overshoot
weights the fixed setting is worth 23 to 29 per cent and adaptation 1.3 to 6.4.
The number moves; the ordering doesn't. The fixed setting wins at every weight
we tested, out to five, which is already an extreme price on overshoot.

**"Slide 19 says 3.5 %, slide 22 says nominal 5.95. Which is it?"**
Both, for different searches. 5.2 is the four-operating point search — that's the
headline. 5.95 is the nominal of the perturbation study, a two-operating point search
on its own sweep, so its absolute value isn't comparable; its "vs nom." column
is. Same cost weight in both. And 3.5 % against the best fixed setting is the
same thing as 2.6 % of baseline: 3.9 divided by 74.9.

**"Is this simulated or measured?"**
Entirely simulation, in ngspice, with a behavioural GaN model validated
against datasheet values — R_DS(on) 26.0 mΩ against a 25 mΩ target. Hardware
is the next phase. Say it plainly; it's a Review-II project and the hardware is Review-III.

**"Why not just slow it down?"**
That's the trivial fix and it discards the switching-loss benefit of GaN. The
trade-off curve on slide 18 shows loss, overshoot and crosstalk margin cannot be
minimised together.

**"Did Cadence actually run?"**
No, and the deck says so. Everything is ngspice. For LTspice open
sim/dpt.cir — that's the complete model and it carries the clamp.

**"Your dead-time number depends on which operating points you pick."**
Yes, and we found that ourselves. It's one light-load operating point: drop
50 V / 2 A / 25 °C and freezing dead time costs 0.00 per cent instead of 5.45.
The leave-one-out table is in FINDINGS.md section 32.

**"How do we know the numbers are right?"**
Ten wrong numbers were caught by our own convergence and resampling checks
before any reached the report. And the MATLAB analysis is an independent
reimplementation of the Python — it reproduces 3.5 %, 25.1, 3.9 and 13.4 to
the decimal.
