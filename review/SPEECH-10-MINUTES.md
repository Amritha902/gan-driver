# Review-I — speech script, 10 minutes

**GaN Based DC–DC Power Converter with an Improved Gate Driver**
Amritha S (23BEC1368) · Sanjay Kumar (23BEC1447) · Aamir Abdullah (23BPS1197)
Guide: Dr. Bindu, SENSE, VIT Chennai

21 slides in 600 seconds. Bracketed times are cumulative — if the clock is
past one, you are behind.

**This is tight.** Twenty-one slides averages 28 seconds each, and there is no
slack in it. Four slides are marked "drop this one first" — cutting all four
buys 110 seconds and the talk still covers every rubric item. Decide before
you start, not halfway through.

The video on slide 10 is two minutes long. Scrub it, or play twenty seconds.
Playing it through costs you the last four slides.

Slides 11 to 17 are screenshots of a tool printing its own output. Say the
number on the screen, not one from memory.

---

## 1 · Title — 15 s  *(0:15)*

Good morning. Our project is a **GaN-based DC-to-DC power converter**, and what
we are contributing is the **gate driver** inside it.

I will show you the converter, then the problem the gate driver solves, then
what we measured — and every result I show is the simulator's own output.

---

## 2 · Problem Statement & Background — 45 s  *(1:00)*

A converter chops a DC voltage with two transistors and filters it back into DC
at a different voltage. Ours uses GaN, because GaN switches in nanoseconds
rather than tens of nanoseconds.

That speed causes the problem. When one transistor switches, the shared node
moves 100 volts in a few nanoseconds. There is an unavoidable capacitance from
that node into the gate of the **other** transistor — the one meant to be off.
The fast change pushes charge through it and lifts that gate.

Our device turns on at **1.4 volts**. We measured that gate reaching
**1.65 volts**. So the device that should be off turns on, both conduct, and
the supply is shorted through them.

---

## 3 · Literature survey — 30 s  *(1:30)*

Five closest papers. The first row is our base paper — **Takayama, Okuda and
Hikihara** — who showed the gate waveform can be set by a digital code instead
of a fixed resistor.

The rest are the active gate drivers that followed, and they report real gains:
thirty per cent less overshoot, seventy-five per cent less turn-off loss.

What they share is that each reports **one number**. That number is doing two
different jobs.

---

## 4 · The gap — 40 s  *(2:10)*

Here are the two jobs.

**One:** pick a better setting and leave it fixed. Costs nothing while running
— no sensor, no ADC, no lookup table.

**Two:** change the setting as load and voltage move. That is what needs the
sensing hardware.

Every paper reports the sum of these and never separates them, because
separating them means running every setting at every operating point.

So the gap is: **nobody has measured what the adaptation is actually worth** —
and only the second one has to be paid for in hardware.

---

## 5 · Aim and approach — 40 s  *(2:50)*

Our aim is that measurement.

The gate driver has six settable fields — how hard it switches on, how hard
off, how firmly the off gate is held, the dead time, a Miller clamp, and a
negative off rail. Those give **720 settings**.

Four steps: build the converter and check it converts; recreate the fault; fix
it one change at a time so each change is measured separately; then ask whether
one fixed setting is enough by running the same driver at different operating
points.

ngspice for the circuit, Vivado for the FPGA.

---

## 6 · System architecture — 30 s  *(3:20)*  ⟵ *drop this one first if you are behind*

Block level, left to right. The PWM command comes in, the FPGA controller
decides the settings, the segmented driver drives the gates, and the power
stage is the GaN half-bridge and the load.

The four blocks in the middle are what we design. The dashed one is the only
part that needs sensing — and measuring what that part is worth is the whole
question.

---

## 7 · How it works — one edge, start to finish — 30 s  *(3:50)*  ⟵ *drop this one first if you are behind*

One switching edge followed through, for a real case: a battery-storage
converter as the load falls from 10 amps to 2.

Top row is what the controller decides. Bottom row is what the circuit then
does. Everything shaded is the only thing decided while running; the rest is
set once at power-up.

---

## 8 · The circuit we simulate — 30 s  *(4:20)*

This is the circuit. 100 volt supply on the left with the stray resistance and
inductance of the power loop, the two GaN transistors in the middle with a
segmented gate driver on each gate, then the output filter and a ten ohm load.

This is the actual file — open it in LTspice and press Run. I have it on the
laptop if you would like to see that.

---

## 9 · How we run ngspice — 40 s  *(5:00)*

This is one run, end to end.

**Step one:** the parameters go into the netlist. Bus 100 volts, load 10 amps,
eight pull-up slices, fifteen nanosecond dead time, clamp off, gate parked at
zero — that is the case that shows the fault.

**Step two:** `ngspice -b dpt.cir`. Twenty picosecond steps over three
microseconds of circuit time. It takes 1.6 seconds.

**Step three:** it writes the raw transient — sixty thousand time points,
fourteen columns. Not a summary; the whole waveform.

**Step four:** the high side is off from two microseconds, the low side turns
on at 2.015, and we take the largest gate voltage over the next 85 nanoseconds.
**+1.6486 volts**, against a threshold of 1.4.

Those four steps run 2,880 times for the search, about 35,000 times in total.

---

## 10 · Demo — the tools running — 25 s  *(5:25)*  ⟵ *drop this one first if you are behind*

This was recorded on the project laptop. It runs the converter in ngspice, the
crosstalk fault and its fix, the cases, the Verilog controller, and then
LTspice opening the schematic and running it.

*(Scrub through it. Do not play all two minutes unless she asks for it — and
if she does, everything in it is also on the next six slides.)*

---

## 11 · Circuit simulation — the converter — 30 s  *(5:55)*

This is the terminal. 100 volts and 2.426 amps in; **48.56 volts and 4.875 amps
out**. 242.63 watts drawn, 236.85 delivered — **97.62 per cent efficient**.

That is the converter working. Everything after this is about the two
transistors inside it.

---

## 12 · Crosstalk simulation — the fault and the fix — 40 s  *(6:35)*

Two runs of the same circuit.

Top line: fastest drive, no clamp, gate at zero. The off gate reaches
**+1.6486 volts**, and the simulator's own flag reads `false_turn_on = 1`.

Bottom line: clamp on, gate at minus two volts. **Minus 1.1757 volts**, margin
**+2.5757**, and the flag reads zero.

Same circuit, same devices. The only difference is two things the gate driver
controls.

---

## 13 · The same result in LTspice — 25 s  *(7:00)*  ⟵ *drop this one first if you are behind*

The same circuit drawn as a schematic and run in a second simulator. LTspice
gets **+1.647556** and **−1.176857 volts**; ngspice got **+1.6486** and
**−1.1757** on the same netlist.

About a millivolt apart. So the result belongs to the circuit, not to the
simulator.

---

## 14 · Driver simulation — case by case — 30 s  *(7:30)*

Thirteen runs. The top half builds the fix one change at a time, so each change
owns a line — the clamp, then the negative rail, then slowing the drive.

The bottom half is the part that matters. Same driver, two operating points,
sweeping only the dead time. At full load the cheapest is **15 nanoseconds**.
At light load it is **5**. Two different numbers — and that gap is the only
thing there is to adapt to.

---

## 15 · What re-tuning is worth — 30 s  *(8:00)*

Of 720 settings, **474 are safe at all four operating points**.

Fixing one setting instead of re-tuning perfectly costs **5.2 per cent at
most** — and it is not spread evenly. Three corners lose one to four per cent.
One loses 12.7.

---

## 16 · The split — the finding — 40 s  *(8:40)*

And this is the answer.

Choosing a fixed setting well: **25.1 per cent**, no hardware. Adapting per
operating point: **3.9**. So adaptation is thirteen per cent of the gain, and
one comparator captures most of that.

Which means the full sensor, ADC and lookup table justify under four per cent.
Our conclusion is that most of what the literature credits to adaptation is
really a design-time choice.

---

## 17 · Vivado output — synthesis — 25 s  *(9:05)*

The controller in hardware. **20 LUTs and 20 flip-flops** strapped, 33 fully
programmable — so programmability costs thirteen LUTs. **200 megahertz is met**
with 1.996 nanoseconds of slack.

---

## 18 · Work completed — 50 % — 20 s  *(9:25)*

The converter is built and converting. The fault is reproduced and fixed. The
named cases have been run. The setting has been measured on the running
converter. The FPGA controller is written, verified and synthesised.

---

## 19 · What is next — 20 s  *(9:45)*

Review-II: close the loop — add feedback so the output holds when the load
changes, then re-run the setting study with it closed.

Review-III: the light-load question — measure what a two-setting controller
actually saves. Same tools.

---

## 20 · References — 8 s  *(9:53)*

Thirty references, publisher-verified. Fifteen here, the rest in the backup
deck.

---

## 21 · Thank you — 7 s  *(10:00)*

Thank you. I have the files on the laptop and can run any of this now.

---

# If she asks

**"Show me it running."**
`2-RUN-IT-LIVE/BUCK_converter.asc` in LTspice → Run → Ctrl+L. Five seconds.
48.84 V and 4.88 A.

**"Is this measured or simulated?"**
Simulated, and the title says so. No hardware has been measured — that is
Review-III.

**"How do I know the numbers are real?"**
Every slide from 7 on is the tool's own terminal, with the machine name and the
timestamp in it. The backup deck has the raw logs, and I can rerun any of it.

**"Why two simulators?"**
ngspice does the study — about 35,000 runs. LTspice draws the same circuit and
re-measures the crosstalk independently. They agree to 0.6 % on the converter
and about a millivolt on the crosstalk.

**"What is a setting / control word?"**
Six fields: 6 × 2 × 3 × 5 × 2 × 2 = 720. Slide in the backup deck.

**"Why GaN?"**
Ten times the breakdown field, so a thinner device for the same voltage, so far
less charge to move and much faster switching. The fault we study is a
consequence of that speed.

**"Your base paper is SiC and yours is GaN — is it really your base paper?"**
Yes, and the difference is the point. What we take is the architecture: a
multibit gate code instead of a fixed resistor. That is device-independent.
Carrying it to GaN is where it has more to do — a GaN gate turns on at 1.4 V
against roughly 2 to 4 for SiC, so there is far less margin, and GaN has no
body diode, so the off gate has to be held down across the whole dead time.
Their paper also has no Miller clamp and no negative rail; both are ours.

**"What is new here?"**
Nobody has separated the design-time gain from the run-time gain, because it
needs an exhaustive search at every operating point. We ran it: 25.1 against
3.9.

**"Why is there no chart of the sweep?"**
Deliberate. Every number in the talk is shown as the simulator printed it. The
charts are in the backup deck if you want them.
