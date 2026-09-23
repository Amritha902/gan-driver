# What Dr. Bindu is likely to ask, and the answer

Ordered by how likely and how dangerous. The first six are the ones that
decide the review. Each answer is short on purpose — say the sentence, stop,
let them follow up.

---

## The six that matter

### 1. "This is all simulation. Where is the hardware?"

**Don't apologise. Answer with the plan.**

> "None yet, and the deck says so — it's 7 of the 10 points we list as
> outstanding. Three tiers: the FPGA on a real board is days away, the
> constraints file already targets the part. A GaN half-bridge eval board at
> 48 V is the one that matters, two to four weeks, because it measures the off
> device's gate during the other one's turn-on, which is our central claim.
> Our own eight-slice stage is a custom board and that's Review-III."

If pushed on why not sooner — the scope-bandwidth constraint is your friend
here, because it shows you know what the measurement costs:

> "Our edge is 0.78 nanoseconds. Seeing it needs about 450 MHz of scope
> bandwidth minimum, realistically a gigahertz. And a 10:1 probe with a ground
> clip has about 10 nH in its ground lead — it manufactures ringing that isn't
> in the circuit. Done badly, the measurement would be of the probe."

### 2. "So your result is that the thing you built isn't worth building?"

This is the sharpest version of the negative-result question. Do not get
defensive.

> "The segmented output stage is worth building — that's the base paper's and
> it works. What isn't worth building is the machinery to re-tune it at run
> time. 89 % of the available gain comes from choosing one good fixed word.
> The remaining 11 % needs sensing, an ADC, a lookup table and 65 % more
> controller logic, and one comparator recovers about half of it for almost
> nothing. That's a design rule, and it runs against the direction of every
> paper we cite."

### 3. "Why should I believe your implementation of their driver is fair?"

> "Their driver is re-optimised at every corner in our comparison — a freedom
> their own one-resistor design doesn't have, because their resistor is set
> once at design time. We run one fixed word at all four corners. If we still
> lead against the best setting they could possibly have, the lead isn't an
> artefact of how we configured them."

And volunteer the limit before they find it:

> "It's our implementation of their described scheme, not their measured
> silicon. The ISPSD paper is four pages and doesn't give slice sizing — equal
> slices and the nseg split are our inference, and that's stated in the model
> file."

### 4. "Your overshoot is 18 %. The base paper's is 3 %. Explain."

> "Because we switch two and a half times faster — 0.78 nanoseconds against
> 2.06. They reduce crosstalk by slowing the edge; we keep the edge and hold
> the gate down. Of our 18 %, 11.3 points are the −2 V rail, which is what
> buys the crosstalk margin. It's a trade we chose, and we stay inside the
> device rating at every bus voltage in our range."

### 5. "Why is the envelope 50–150 V when GaN parts are rated 200?"

> "Because the part is rated 200 V and we measured 208 V of peak at a 200 V
> bus. That's not the driver failing — the overshoot there is the smallest in
> the whole sweep, 4 %. It's that a 200 V-rated device can't run a 200 V bus,
> since any overshoot at all then exceeds the rating. 200 V operation needs a
> higher-rated part, not a different driver."

### 6. "How do I know any of this is your work?"

The honest and strongest answer is to make something change in front of them.

> "Everything regenerates. The schematics are generated from the netlists —
> change a value in the SPICE deck and re-run the script and the drawing
> changes. The draw.io file opens and edits live. And `results/` has the raw
> ngspice listing, which is the simulator's own output, not a drawing of it."

---

## Technical questions she is likely to ask

**"Why 720 words?"**
Six fields: pull-up and pull-down strength each side, dead time, clamp enable,
off-rail select. 720 is their product.

**"Why 36 operating points?"**
Bus × load × junction temperature across the stated envelope. 36 × 720 =
25,920 intended runs; 25,911 produced a measurement and 9 did not. We report
the 9 rather than back-fill them.

**"Why 3 nH of loop inductance?"**
It's our choice and the conclusion is sensitive to it. We list it as a threat
to validity, not as a result. A looser layout would change the crosstalk story.

**"Why does the low-side gate matter and not the high-side?"**
The high-side turn-on is the hard-switched edge — the switch node swings the
full bus. The low side is the victim of that dv/dt. Measuring the *other* edge
looks clean and hides the failure; that mistake is why our double-pulse deck
didn't catch the 200 V problem.

**"What is the Miller clamp actually doing?"**
Holding the off gate down through 0.5 Ω whenever the device should be off, so
the Miller current from the other device's dv/dt has somewhere to go that
isn't the gate capacitance.

**"Why does GaN need this and silicon doesn't?"**
1.4 V threshold against silicon's 4 V, and an edge nine times faster. Same
Miller current, a quarter of the threshold to cross.

**"Your efficiency gain over the base paper is 0.11 %. Is that significant?"**
No, and we don't claim it. Efficiency was never the claim — crosstalk survival
was: +0.407 V against +2.576 V. The 0.11 % is reported because leaving it out
would be selective.

**"What does the FPGA actually do that a resistor can't?"**
The resistor is set before the chip exists and can never change. The FPGA is a
register write. That's what made a 720-word sweep possible at all — and it's
what let us discover the answer is "don't bother", which a resistor could
never have told us.

---

## The ones that would hurt if unprepared

**"Your Vivado report says timing constraints are not met."**
Get in first if you can.

> "That's 34 register-to-output-pin paths at synthesis, against a placeholder
> 4 ns constraint, before placement, with placeholder pin assignments. The
> logic meets 200 MHz with 1.996 ns of slack. The I/O paths close at
> implementation or the constraint gets set from the real board."

**"Did you check your own numbers?"**
Yes, and we found one wrong.

> "We audited it. The deck claimed 60,533 transient simulations; the true
> figure derived from the result files is 66,924. It was right when it was
> typed and went stale when three more studies were added. The consistency
> check passed it every time because it only compared the number on a slide to
> the same number in a text file — text agreeing with text. That's fixed: the
> count is derived from the data now and a stale one fails the build."

This is a *strength* if you say it first and a disaster if she finds it.

**"Does the result depend on your device model?"**
Partly, and we say so.

> "The ordering survives both capacitance formulations and real transistors.
> One thing doesn't: the sign of the no-clamp row changes between the
> behavioural and charge-based capacitance laws. So 'the constant word causes
> false turn-on' is a statement about the model as much as the device, and
> it's on the slide as a limitation."

---

## If she asks what is next

> "Hardware, and the publish-versus-file decision. The paper and a patent
> disclosure are both drafted. Our own reading is that the components are all
> commercial and the novelty is a negative result, so publishing is the
> stronger route — but that order can't be undone, so it should be decided
> before the paper goes anywhere."

---

## One rule for the whole viva

**Volunteer every weak number before she finds it.** Overshoot, the 0.11 %
efficiency, the 9 failed runs, the stale count, the model dependence, the
absent hardware. A panel that finds a weakness you hid distrusts everything
else on the slide. A panel that hears you name it first believes the rest.
