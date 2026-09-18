# Viva rehearsal

A panel member and the student, arguing. The panel is not being kind. Every
number quoted here is in the repository and every script named produces it.

The point of writing it down is that the questions below are the ones that
actually get asked, and half of them have no comfortable answer. Better to
meet them here.

---

### P: Start with one sentence. What did you contribute?

**S:** Every paper on segmented gate drivers reports one improvement number.
That number mixes two different things: picking a better fixed setting, which
costs nothing at run time, and re-tuning the setting while the converter runs,
which needs a sensor, an ADC and a lookup table. Nobody separates them. I did,
exhaustively, and the split is 26.5 % against 2.6 %.

### P: So your contribution is a ratio.

**S:** My contribution is that the ratio is measurable and that it comes out
lopsided. The adaptive hardware that this whole class of driver is sold on
buys 8.9 % of the total gain.

### P: A negative result.

**S:** Yes. And I'd rather defend a negative result I can reproduce than a
positive one I can't.

### P: That's a nice line. It isn't an answer. A panel marks contribution, and
### "the thing everyone is building isn't worth building" is only a
### contribution if you're right. Convince me you're right.

**S:** Three ways. One: it's exhaustive, not sampled. 720 control words at all
36 operating points, 25,911 transients, no search heuristic that could have
missed the good adaptive words. Two: leave-one-corner-out over 36 folds
returns *exactly the global fixed word* on all 36. Fitting the schedule on 35
corners teaches you nothing about the 36th. Three: it survives the device. 24
devices with threshold, transconductance, C_GS and C_GD varied jointly, and a
better fixed word beats adapting on every one.

### P: Stop there. Your own analysis output says the ordering fails on one of
### 24.

**S:** It did, on the 36-word candidate set. I re-ran device 18 on the full
720-word grid and it flips: (A) 24.7 % against (B) 13.9 %, with 473 words
admissible instead of 22. The method predicted exactly that failure mode — a
subset can only raise the best fixed word's cost, so it deflates (A) and
inflates (B) — and the figure marks device 18 as a resolved artefact rather
than hiding it. `scripts/device_mc_resolve.py` is committed so you can repeat
the check.

### P: Fine. Now the uncomfortable one. You changed your own headline twice
### during this project. The clamp was the fix, then it wasn't. The comparator
### was bus voltage, then it was load current. Why should I believe version
### three?

**S:** You shouldn't believe it because I said it. Both changes came from a
check that could have gone either way, and both are in the run log with the
date.

The clamp one: every margin was measured with ideal switches. I rebuilt the
same output stage in real SKY130 transistors and the clamp alone went from
+0.570 V to +0.031 V. Thirty-one millivolts is not a fix. The −2 V off-bias
is the fix and the clamp is what makes it hold.

The comparator one: the four-corner study said bus voltage at 75 V. On 36
corners it's load current at 10 A. Same 47 %, different sensor. Somebody
building to my old advice would have sensed the wrong quantity.

### P: Both of those are you finding your own mistakes, which is fine. It also
### means the project has been wrong in public twice. What's wrong now that
### you haven't found?

**S:** I don't know, and that's the honest answer. What I can tell you is
where I'd look. The cost function is a choice: switching energy plus 0.05 µJ
per point of overshoot. I've swept the overshoot weight over 106 values and
the ordering holds at every one, but the *magnitudes* move. The device model
is one behavioural form; I've sampled its parameters but not its form. And
the whole study is at 3 nH of loop inductance, which I chose. The lloop sweep
says re-tuning only pays below about 2.5 nH, so I'm on the side of that
boundary where my own conclusion is favoured.

### P: That last one is a real problem. You picked the parasitic that makes
### your answer come out the way it does.

**S:** I picked 3 nH before I knew where the boundary was, and I published the
boundary. If I'd wanted the answer I got I'd have picked 4.5 nH, where
re-tuning is worth 0.6 %. A reviewer who thinks 1.5 nH is realistic should
read my conclusion as much weaker: at 1.5 nH the ceiling is 13.5 %. That's on
the slide.

### P: Let's talk about what you didn't do. There's no hardware.

**S:** None. No board, no scope trace, no measured device.

### P: For a power electronics project.

**S:** Yes. The title says simulation study and the completion slide says 90 %
with the missing 10 % named as place-and-route and a bench. I'm not going to
argue that's as good as hardware, because it isn't.

### P: Then why should this score like a finished project?

**S:** Because the part I did do, I did to a standard the hardware wouldn't
have changed. The controller isn't a block diagram — it's Verilog, eight
properties passing in Icarus, mutation-tested, synthesised in Vivado at
20 LUTs and 20 flip-flops with 200 MHz met and 1.996 ns of slack. And it
isn't verified in a vacuum: `scripts/rtl_cosim.py` plays the RTL's own
waveform dump into the SPICE power stage, one PWL source per thermometer
wire, and the margin agrees with the parameterised driver to 0.081 V.

### P: Why does that matter?

**S:** Because it caught a bug neither half could see alone. The dead-time
generator loads its counter and counts down *through* zero, so the dead time
is (dt_cycles + 1) × 5 ns. Fifteen nanoseconds is two cycles, not three.
Anyone mapping my swept dead-time grid onto hardware by dividing by the clock
period would have built a driver one cycle slow at every operating point.

### P: Good. Now the base paper. You claim 5.5× to 12.4×.

**S:** Against my implementation of their described scheme, in my testbench,
with my parasitics. Their netlist isn't published. It is not 12× their
measured result and the slide says so in those words.

### P: So the comparison is you against yourself.

**S:** It's me against my best reading of them, and I quote them at their
best, not at a setting I picked. Their driver has two controls and I search
both over the range their own paper states, then report their best point.
There's one check on whether the reproduction is real: set their slice count
to seven, which collapses the scheme to a constant code, and it gives
−0.278 V against my own constant-code −0.249 V. Two independent paths to the
same number within 0.03 V.

### P: The title says "GaN Based Synchronous Buck Converter". Most of what
### you've described is a gate driver.

**S:** They're the same claim. The converter is what's being built — it
regulates 50 V through a 2× load step and a 20 % line step at 0.01 % error —
and the gate driver is the one part of it I redesigned, because on GaN that's
the part that decides whether the converter is buildable at the speed the
device is bought for. A silicon buck doesn't need this work; a GaN buck at
500 kHz on a 1.4 V threshold does, which is why the driver is where the
project spends its time. Every number in the deck is measured on the
converter, not on a driver sitting by itself on a bench.

### P: That sounds like a defence of the title rather than an answer.

**S:** It is a defence of the title, and I'll stand on it. The alternative
naming — putting the driver first — would describe the deliverable as a
component and hide what it's a component of. The reason the crosstalk number
matters at all is that it's the thing that stops a converter existing. Take
the converter out of the title and the 1.65 V spike is a curiosity.

### P: What did opening the waveforms get you? You made a lot of noise about
### that.

**S:** Two things. The 168 V one is the real finding: the converter deck had
no bus decoupling at all, so every high-side turn-on pulled its current from
an ideal source through 3 nH, and the switch node hit 168 V on a 100 V bus —
84 % of the device rating. Every `.meas` in that deck was fine. A scalar can't
tell you the waveform behind it is wrong. Adding 100 nF with realistic ESL
brought it to 115 V.

### P: And the second?

**S:** The double-pulse deck writes 4850 V at its first timepoint. One sample,
2 × 10⁻¹³ s, the solver settling from inconsistent initial conditions, gone by
the next step, and outside every measurement window. Nothing reported is
affected. But nobody had ever looked, and "an artefact we characterised" and
"a number we never looked at" are different states to be in.

### P: What's the single weakest thing in this project?

**S:** That it's one model form. I sample the parameters — 24 devices, four
parameters varied together — but if the *shape* of the C(V) law or the channel
equation is wrong, every device I sampled is wrong the same way. I showed the
capacitance formulation matters: swapping junction diodes for a charge
formulation flips the sign of the no-clamp margin, −0.249 V against +0.115 V.
The shipped design survives both. The fault claim doesn't, and I say that on
the slide rather than letting someone find it.

### P: Last question. What would you do with another six months?

**S:** Build it. One board, one half-bridge, the FPGA I've already
synthesised, and measure the crosstalk margin at the four corners. If the
measured margin lands inside the spread of my 24 sampled devices, the
simulation study is validated and the negative result stands on evidence. If
it doesn't, I'd want to know why more than I'd want to be right.

---

## Verdict, written by the panel member

**Would I give this 100?** No, and I'd be suspicious of a panel that did.

**What stops it:**

1. **No measurement.** For a power-electronics capstone this is the
   difference between a study and a result. Everything else is downstream of
   it.
2. **The contribution is a negative result.** It is a real one, honestly
   obtained, and it will read to some markers as "proved the thing isn't
   worth doing" rather than as engineering. That is partly a framing problem
   and partly true.
3. **The title will draw the question.** It names a converter and most of the
   deck is a gate driver. The answer holds — the driver is the part of the
   converter that decides whether it is buildable at speed, and every number
   is measured on the converter — but it has to be volunteered early, on the
   goal slide, not dragged out under questioning.

**What is genuinely above the bar:**

- The method is exhaustive rather than sampled, and the sample size is
  defensible: 25,911 transients across 36 operating points, plus 24 jointly
  varied devices.
- The conclusion is tested against the things that would break it — real
  transistors, a different capacitance formulation, device-to-device spread,
  loop inductance — and the report says which of those it survives and which
  it doesn't.
- The two halves are made to meet. The RTL drives the SPICE power stage and
  that co-simulation caught a real off-by-one.
- Three headline claims were corrected mid-project by checks that could have
  gone the other way, and each correction is dated and reproducible.

**Realistic band: 85–92.** Presented well, with the negative result framed as
the finding rather than as an absence, and with the limits volunteered before
they're asked for, the upper half of that is reachable.

**What would move it to the mid-90s, in order of value:**

1. One measured switching edge on real hardware. Even a single scope trace of
   the crosstalk spike against the simulated one changes the category of the
   work.
2. Say on the goal slide why the title is the converter and the work is the
   driver, before anyone has to ask. It costs two sentences and removes the
   easiest hit on the deck.
3. Lead with the negative result as a design rule — "build the fixed word,
   skip the LUT, and here is the one corner where that costs you 14 %" —
   instead of as a percentage.

**What would not move it at all:** more simulation, more slides, more
polishing of what is already there.
