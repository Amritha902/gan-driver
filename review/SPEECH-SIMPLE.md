# Speech script — 15 slides, 10 minutes

Simple version. Say roughly this. Times are cumulative.

---

**1 · Title — 20 s**

Good morning. Our project is a **GaN synchronous buck converter**, and what we
designed is the **gate driver** inside it.

A buck converter takes a DC voltage and gives a lower DC voltage. Ours takes
100 volts and gives 48.6 volts.

---

**2 · Problem — 50 s   (1:10)**

The converter has two GaN transistors that switch on and off very fast.

When one transistor switches, the voltage between them moves 100 volts in a
few nanoseconds. That fast change pushes charge into the gate of the other
transistor — the one that should be off.

Our transistor turns on at **1.4 volts**. We measured that gate reaching
**1.65 volts**. So it turns on when it should not, both transistors conduct,
and the supply is shorted.

That is the problem the gate driver has to solve.

---

**3 · Literature — 40 s   (1:50)**

These are the five closest published gate drivers. The first row is our
**base paper** — Zhang and others, IEEE ISPSD 2020.

They built a segmented gate driver for GaN transistors: the driver is split
into slices, and how hard it switches is set by a pattern.

The others all report improvements, and each reports one single number.

---

**4 · The gap — 45 s   (2:35)**

That one number is really two different things added together.

One: picking a good setting once and leaving it fixed. This costs nothing.

Two: changing the setting while the converter runs. This needs a sensor, an
ADC and a lookup table — real hardware.

Nobody has separated them. So nobody knows whether that hardware is worth
building. That is our gap.

---

**5 · Aim and approach — 45 s   (3:20)**

Our aim is to measure that.

Our driver has six settings: pull-up slices, pull-down slices, dead time, the
Miller clamp, and the off-bias rail. Together they give **720 settings**.

We did four things. Built the converter and checked it works. Recreated the
fault. Fixed it one change at a time. Then asked whether one fixed setting is
good enough at every operating point.

We used ngspice for the circuit and Vivado for the FPGA.

---

**6 · Architecture — 30 s   (3:50)**

This is the block diagram. The PWM comes in, the FPGA decides the settings,
the segmented driver drives the gates, and the power stage is the GaN
half-bridge and the load.

The four middle blocks are what we designed. Only the dashed one needs
sensing.

---

**7 · Flow chart — 30 s   (4:20)**

This follows one switching edge. The top row is what the controller decides.
The bottom row is what the circuit does.

Only the shaded box is decided while running. Everything else is set once.

---

**8 · The circuit — 35 s   (4:55)**

This is the actual circuit, in LTspice.

On the left, the 100 volt supply. In the middle, the two GaN transistors. The
two yellow blocks are our segmented gate drivers, one on each gate. On the
right, the output filter and a 10 ohm load.

This is a real file. If you like I can open it and run it.

---

**9 · How we run ngspice — 45 s   (5:40)**

This is one simulation, start to finish.

First we set the parameters — 100 volts, 10 amps, eight slices, 15 nanosecond
dead time, clamp off.

Then we run ngspice. It takes about 1.6 seconds.

It writes 60,000 time points. We then measure the highest gate voltage in the
85 nanoseconds after the other device switches. That gives **1.6486 volts**.

We ran those four steps about 35,000 times.

---

**10 · Demo — 25 s   (6:05)**

*(Scrub through the video, do not play it all.)*

This was recorded on the laptop. It shows ngspice running the converter, then
the fault and the fix, then the Verilog controller, then LTspice.

---

**11 · Circuit simulation — 35 s   (6:40)**

This is ngspice printing the converter result.

100 volts and 2.4 amps going in. **48.56 volts and 4.875 amps coming out.**
242 watts in, 237 watts out — **97.6 per cent efficient**.

The converter works.

---

**12 · Crosstalk simulation — 40 s   (7:20)**

Two runs of the same circuit.

Top line: no clamp, gate at 0 volts. The off gate reaches **+1.6486 volts**,
and the simulator flags a false turn-on.

Bottom line: clamp on, gate at minus 2 volts. It reaches **minus 1.1757
volts** — **2.58 volts of margin**, and no false turn-on.

Same circuit. The only difference is our two additions.

---

**13 · Driver simulation — 45 s   (8:05)**

Thirteen runs of the driver.

The top part adds one fix at a time, so you can see what each one does.

The bottom part is the important one. Same driver, two different loads. At
full load the best dead time is **15 nanoseconds**. At light load it is **5**.

They are different. That difference is the only thing worth adapting — and
that is our result: choosing the setting well is worth 25 per cent, changing
it while running adds only 4 per cent more.

---

**14 · Work completed — 30 s   (8:35)**

The converter is built and running. The fault is reproduced and fixed. The
cases have been run. The FPGA controller is written, verified, and
synthesised in Vivado — 20 LUTs, 200 megahertz met.

That is our 50 per cent.

Next: close the feedback loop, then measure the light-load case properly.

---

**15 · References — 20 s   (8:55)**

Thirty references, all checked against the publisher.

Thank you. I have everything on the laptop and can run any of it now.

---

## If she asks

**Show me it running.** Open `BUCK_converter.asc` in LTspice, press Run, then
Ctrl+L. Five seconds. 48.84 V and 4.88 A.

**What is inside the yellow block?** `SEGDRV_inside.asc` — eight pull-up
slices, eight pull-down slices, and the Miller clamp. It runs too.

**Is it measured or simulated?** Simulated. No hardware yet — that is
Review-III.

**Why buck?** Buck means step-down. 100 volts in, 48.6 out.

**Why GaN?** It switches about ten times faster than silicon, so the converter
is smaller and more efficient. The fault we study is caused by that speed.

**Why two simulators?** ngspice does the study. LTspice draws the same circuit
and checks the crosstalk number independently. They agree to 0.6 per cent.
