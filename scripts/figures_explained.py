# -*- coding: utf-8 -*-
"""figures_explained.py -- one page per figure, generated from the deck.

    python3 scripts/figures_explained.py

WHY THIS IS GENERATED AND NOT WRITTEN BY HAND
  A document that explains the figures has to agree with the figures. Written
  by hand it agrees on the day it is written and drifts from then on -- a
  figure gets renumbered, a caption gets rewritten, a slide moves, and the
  explanation quietly describes a deck that no longer exists.

  So the scaffolding -- which figure, what number, what slide, what its caption
  says, where it came from -- is read out of the .pptx every time this runs.
  Only the explanation itself is written by hand, keyed by the image filename,
  and a figure with no entry is listed as missing rather than skipped.

WHAT EACH ENTRY ANSWERS
  WHAT IT IS       the one sentence to open with
  WHAT TO LOOK AT  where the eye should go, in order
  WHAT IS ODD      the thing a sharp reviewer will point at, answered before
                   they ask. Every figure that has one gets one; where there
                   is nothing odd, it says so rather than inventing something.
  IF THEY ASK      the question and the answer
"""
import hashlib, glob, io, os, sys
from pptx import Presentation
from pptx.util import Inches

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "review", "Review2_GaN_Segmented_Gate_Driver.pptx")
OUT  = os.path.join(ROOT, "review", "FIGURES-EXPLAINED.md")

E = {}

E["fig_gan_1.png"] = dict(
    what="A side-by-side of silicon MOSFET against GaN HEMT on the four "
         "properties that decide switching behaviour.",
    look="The threshold row and the gate-drain capacitance row. Those two "
         "numbers are the whole reason this project exists.",
    odd="It is a DRAWING. The numbers on it are datasheet-class values for "
        "an EPC2010C-class part, typed in, not measured by us. The caption "
        "says so.",
    ask=("\"Where did these device numbers come from?\" — models/egan.lib, "
         "and they are datasheet-class rather than transcribed. The "
         "qualitative argument does not depend on the third digit."))

E["fig_si_vs_gan.png"] = dict(
    what="The same buck converter run twice, once with a GaN HEMT and once "
         "with a silicon MOSFET, swept over switching frequency.",
    look="The gap between the two curves, and that it WIDENS to the right. "
         "That widening is the argument for GaN, not the single number at "
         "500 kHz.",
    odd="R_DS(on) is matched by construction — 25.0 mΩ GaN against "
        "24.0 mΩ Si, each at its own rated gate drive — so conduction "
        "loss is equal on purpose and everything you see is switching, gate "
        "drive, and the body-diode recovery GaN does not have.",
    ask=("\"Is this a fair comparison?\" — it is deliberately rigged to be "
         "fair on conduction loss, which is the only way the switching "
         "difference is visible. The silicon model is datasheet-CLASS for a "
         "200 V / 24 mΩ part, not transcribed, and that is an open item."))

E["fig_gan_2.png"] = dict(
    what="The three GaN device properties that cause crosstalk, and what each "
         "does in a half-bridge.",
    look="The chain: low threshold, high C_GD, no body diode.",
    odd="Drawn, not measured. It explains the mechanism; it is not evidence "
        "of it. The evidence is the waveform two slides later.",
    ask=("\"No body diode — is that good or bad?\" — both. No reverse "
         "recovery, but the dead-time reverse drop is V_th + |V_off| + "
         "I·R_DS(on), which is why our −2 V rail costs turn-on "
         "energy. Measured at 1.0–3.4 % of total loss."))

E["fig_headtohead.png"] = dict(
    what="Crosstalk margin at four operating corners, base paper against "
         "ours.",
    look="Left to right on each pair; then top to bottom — their bars "
         "SHRINK as the corner gets hotter and ours barely move.",
    odd="We are held to ONE fixed control word at all four corners and they "
        "are re-optimised at every corner, which is more freedom than their "
        "own design has (one bias resistor, set once). That handicap is "
        "deliberate and it is ours.",
    ask=("\"Is this 12× their published result?\" — NO, and the caption "
         "says so. models/zhangdrv.lib is our implementation of their "
         "DESCRIBED scheme; their netlist is not published. It is 12× that "
         "implementation in our testbench with our parasitics."))

E["fig_closedloop.png"] = dict(
    what="The regulated converter through a 2× load step and a "
         "100 → 120 V line step, against the same converter open loop.",
    look="The blue line is flat. That is the result. Then the orange one, "
         "which dips 6 V on the load step and settles 8 V high after the "
         "line step because nothing in it knows the input moved.",
    odd="The window starts at 780 µs, not zero. The open-loop run has no "
        "soft start BY CONSTRUCTION — its control node is frozen from t=0 "
        "— so it slams to the rail and rings for 200 µs. That is an "
        "artifact of how the comparison is built, not a property of open-loop "
        "control, and showing it would bury the two disturbances.",
    ask=("\"What is the phase margin?\" — we do not claim one. It needs an "
         "AC analysis about a periodic operating point, which ngspice cannot "
         "do on a switching deck. What is shown is weaker and is stated as "
         "such: one fixed set of component values, stable through both "
         "disturbances."))

E["fig_modeldep.png"] = dict(
    what="The three headline configurations, each run on three different "
         "models: ideal switches, real SKY130 transistors, and a charge-based "
         "capacitance instead of junction diodes.",
    look="The right-hand group — all three bars well above zero. Then the "
        "left-hand group, where two bars are below zero and one is above.",
    odd="The left group CHANGES SIGN between models. That is the finding, not "
        "a defect: those configurations sit closest to zero, and the two "
        "capacitance laws differ by more than their distance from it. So "
        "“the constant word causes false turn-on” is model-dependent.",
    ask=("\"Then which model is right?\" — they answer different questions. "
         "Under reverse bias, where the victim sits, both agree. Under "
         "forward bias a SPICE diode applies its FC extrapolation and the "
         "behavioural form saturates — and the AGGRESSOR is forward-biased "
         "through its own turn-on. The shipped design is safe under all of "
         "them with over 2 V of room, which is the argument for building it."))

E["fig_converter.png"] = dict(
    what="sim/buck.cir running: the converter charging its own output up and "
         "settling, 100 V in to 48.6 V out.",
    look="The output rising and settling, and the switch node chopping.",
    odd="THE SWITCH NODE REACHES 168 V ON A 100 V BUS — 68 % overshoot, "
        "which is 84 % of the modelled device's 200 V rating. The "
        "double-pulse deck only reaches 122 V. Found by "
        "scripts/output_audit.py, which opens the waveform rather than "
        "trusting the .meas scalars, and it is a real reliability observation "
        "rather than a solver artifact.",
    ask=("\"Is the device safe at 168 V?\" — on a 200 V part, with 16 % "
         "margin, in simulation, with a 3 nH loop inductance we chose. On "
         "hardware the layout decides it. This is one of the reasons the "
         "project says a bench measurement is the honest next step."))

E["fig_cases.png"] = dict(
    what="The 13 named runs: the fix built one change at a time, then a "
         "dead-time sweep at two operating points.",
    look="Part 1 left to right — each bar is one change, measured on its "
         "own run rather than all at once. Part 2 is where the light-load "
         "answer differs from the full-load one.",
    odd="Nothing. This is the most boring figure in the deck and that is the "
        "point: one change, one run, one number.",
    ask=("\"Why measure them separately?\" — because a combined result "
         "cannot tell you which change did the work, and the whole project is "
         "about attributing benefit."))

E["fig1_crosstalk.png"] = dict(
    what="The gate-source voltage of the off-state device across the "
         "switching edge, with and without the fix.",
    look="The peak against the threshold line. That crossing is the fault.",
    odd="The low-side gate rings to 8.23 V on a 5 V rail in the first "
        "nanoseconds of the run. That is the solver settling from "
        "inconsistent initial conditions under uic — one burst, before "
        "5 ns, and every measurement window in the project opens at 1 µs. "
        "scripts/output_audit.py reports it with its time and duration so it "
        "cannot be mistaken for a result.",
    ask=("\"Your gate goes to 8 V, is the driver broken?\" — no: that is a "
         "start-up artifact at t < 5 ns, outside every measurement window. "
         "The audit script prints exactly when and for how long."))

E["fig_buck_tradeoff.png"] = dict(
    what="Power lost and peak switch-node voltage against the same driver "
         "setting, on the running converter.",
    look="The two curves move in OPPOSITE directions. That is the trade-off "
         "the whole control word exists to navigate.",
    odd="Two quantities with different units, so they are on separate panels "
        "rather than a dual axis. A dual axis here would let the crossing "
        "point be placed anywhere by choosing the scales.",
    ask=("\"Which end should you pick?\" — that is the project's question, "
         "and the answer is the fixed word plus at most one comparator."))

E["paper_fig2_ceiling.png"] = dict(
    what="The ceiling on operating-point scheduling: the best any adaptive "
         "controller could do, against the best fixed word.",
    look="The gap. It is 5.2 %, and that is the CEILING, not an achieved "
         "figure.",
    odd="It is an upper bound computed with an oracle that knows the corner "
        "in advance. No real controller reaches it. That is the honest way to "
        "bound the question.",
    ask=("\"So adaptive control is worthless?\" — no: worth 3.9 % of "
         "baseline, of which one comparator takes 46 %. The claim is about "
         "how much hardware it justifies, not whether it does anything."))

E["fig_lloop.png"] = dict(
    what="The ceiling against power-loop inductance.",
    look="Where the curve crosses into irrelevance — around 2.5 nH.",
    odd="This is the figure that says WHEN our own conclusion stops holding. "
        "Below ~2.5 nH of loop inductance re-tuning pays; above it, it does "
        "not.",
    ask=("\"What is your loop inductance?\" — 3 nH, chosen, not measured, "
         "and stated. The conclusion is on the side of the boundary where "
         "re-tuning pays little."))

E["fig_rtl_waveform.png"] = dict(
    what="The Icarus Verilog VCD of seg_gate_ctrl.v — the controller's own "
         "output, not a simulation of the circuit.",
    look="The thermometer-coded banks, and the dead-time gap where neither "
         "side is driven.",
    odd="This is the only figure in the deck from a DIGITAL simulator. It is "
        "what the FPGA emits; scripts/rtl_cosim.py is what plays it into the "
        "SPICE power stage.",
    ask=("\"Does the RTL match what you simulated in SPICE?\" — checked, "
         "and it found a bug: dead time is (dt_cycles + 1) × 5 ns, so 15 ns "
         "is 2 cycles and not 3."))

E["fig_circuit_ltspice.png"] = dict(
    what="The converter as a drawn schematic, in LTspice.",
    look="The two yellow blocks — those are the segmented gate drivers, the "
         "part this project designs. Everything else is the power stage.",
    odd="It is a DRAWING that also runs: LTspice gives 48.84 V against "
        "ngspice's 48.56 V on the same circuit. Two independent simulators "
        "agreeing to 0.6 % is the reason to show it.",
    ask=("\"Which simulator do your numbers come from?\" — ngspice, every "
         "one. LTspice is a cross-check and the schematic is for reading."))

E["fig_segdrv_inside.png"] = dict(
    what="What is inside models/segdrv.lib, drawn as a schematic.",
    look="Eight pull-up slices, eight pull-down slices, and the clamp on its "
         "own 0.5 Ω path.",
    odd="In the ideal-switch model these are switches with a series "
        "resistance. scripts/silicon_check.py rebuilds the same stage in real "
        "SKY130 transistors, and the clamp-alone result drops from +0.57 V to "
        "+0.03 V.",
    ask=("\"Can this be fabricated?\" — the output stage, yes, and it has "
         "been rebuilt in a real PDK. The predrivers are still behavioural."))

E["fig_ltspice_annotated.png"] = dict(
    what="The same crosstalk result, produced in LTspice on the drawn "
         "schematic instead of in ngspice on the netlist.",
    look="That the shape matches the ngspice figure.",
    odd="The three .asc sheets do NOT contain the Miller clamp — only the "
        ".cir files do. Their labels say so. Do not present the .asc sheets "
        "as evidence of the clamp.",
    ask=("\"Why two simulators?\" — one produces the numbers, the other "
         "checks the model is not an ngspice artifact."))

E["fig_flow.png"] = dict(
    what="One switching edge followed from the controller's decision to the "
         "circuit's response.",
    look="The shaded diamond — it is the only thing decided at run time.",
    odd="Drawn. It is the reading aid for everything after it.",
    ask=("\"What actually changes while it runs?\" — only that diamond, and "
         "measuring what it is worth is the project's question."))

E["fig_netlist.png"] = dict(
    what="The power stage of sim/buck.cir, set in type.",
    look="That it is a NETLIST. ngspice is not given a schematic.",
    odd="Neither a diagram nor tool output — it is the project's own file, "
        "typeset, and it has its own provenance category for that reason.",
    ask=("\"Is the schematic the same circuit as the netlist?\" — yes, and "
         "they simulate to 48.84 V against 48.56 V in two different tools."))

for k, what in (
    ("fig_settings.png", "The six fields of the control word and the values "
                         "swept over each — 6×2×3×5×2×2 = 720."),
    ("fig_input.png", "What an operating point is: bus voltage, load current, "
                      "junction temperature."),
    ("fig_output.png", "What is actually measured out of every run."),
    ("fig_margin.png", "What crosstalk margin means, defined once."),
    ("fig_method.png", "The method, in the order it was carried out."),
    ("fig_howrun.png", "One ngspice run end to end: the parameters, the "
                       "command, what the simulator wrote, the window."),
    ("fig_tools.png", "Which tool did what."),
    ("fig_architecture.png", "What talks to what, left to right."),
):
    E[k] = dict(what=what,
                look="The labels. This is a reading aid, not a result.",
                odd="It is DRAWN. Every number on it is quoted from the script "
                    "named on the slide; none of it is simulator output, and "
                    "the caption says so.",
                ask=("\"Is this a result?\" — no. It explains what the "
                     "results are made of. The evidence is in the figures "
                     "stamped SIMULATED IN NGSPICE."))

# 17-converter-power.png is no longer in this list. It used to be a hand
# capture of a terminal, which made it good evidence and impossible to
# maintain: when bucksim's off rail was corrected to the -2 V the project
# ships, the screenshot kept showing the old efficiency next to a caption
# carrying the new one. scripts/converter_capture.py now renders the
# script's real stdout, so it is the tool's own output but reproducible --
# and describing it as an unedited desktop capture would no longer be true.
E["17-converter-power.png"] = dict(
    what="scripts/bucksim.py's own output, rendered rather than screenshotted.",
    look="The numbers as the script printed them. Read those, not ones from memory.",
    odd="Nothing is plotted or redrawn. It is regenerated by "
        "scripts/converter_capture.py, so it cannot drift from the script the "
        "way a screenshot can, and did.",
    ask=("\"Can you run this now?\" - yes, and the image is the result of "
         "running it."))

for k, tool in (("01-ngspice-crosstalk.png", "ngspice"),
                ("18-named-cases.png", "ngspice"),
                ("12-result2-ceiling.png", "ngspice"),
                ("13-result3-split.png", "ngspice"),
                ("03-verilog-8-properties.png", "Icarus Verilog"),
                ("11-vivado-synthesis-console.png", "Vivado"),
                ("vivado_console.png", "Vivado"),
                ("vivado_simulation.png", "Vivado")):
    E[k] = dict(
        what="A capture of %s's own terminal, unedited." % tool,
        look="The numbers on the screen. Read those, not ones from memory.",
        odd="Nothing is plotted or redrawn here. A number typed onto a slide "
            "and a number lifted out of the tool's own output are not the "
            "same evidence, and this slide is the second one.",
        ask=("\"Can you run this now?\" — yes. The command is on the "
             "screen and the repository is on the laptop."))


def main():
    p = Presentation(DECK)
    known = {}
    for pat in ("results/**/*.png", "review/*.png"):
        for f in glob.glob(os.path.join(ROOT, pat), recursive=True):
            known[hashlib.sha1(open(f, "rb").read()).hexdigest()] = \
                os.path.basename(f)

    def title_of(sl):
        for sh in sl.shapes:
            if sh.has_text_frame and sh.width \
               and abs(sh.width - Inches(10.5)) < Inches(0.3) \
               and sh.top is not None and sh.top < Inches(1.0):
                return sh.text_frame.text.strip()
        return "(untitled)"

    rows, missing = [], []
    for i, sl in enumerate(p.slides, 1):
        pics = [sh for sh in sl.shapes
                if sh.shape_type is not None and "PICTURE" in str(sh.shape_type)
                and sh.width and sh.width > Inches(2.5)]
        if not pics:
            continue
        # Caption candidates: any text box under the picture band. Most
        # slides have exactly one, starting "Fig. n". The Vivado slide has
        # TWO pictures and two captions and neither starts with "Fig.", so a
        # single-caption assumption gave both of its figures the number "?".
        # Prefer real "Fig. n" captions. Falling back to any text box under
        # the picture band grabs the slide's body text on slides that have
        # both, which cost the FPGA slide its figure number.
        caps = [sh for sh in sl.shapes
                if sh.has_text_frame
                and sh.text_frame.text.strip().startswith("Fig.")]
        if not caps:
            caps = [sh for sh in sl.shapes
                    if sh.has_text_frame and sh.text_frame.text.strip()
                    and sh.top is not None and sh.top > Inches(1.15)
                    and sh.width and sh.width > Inches(2.0)
                    and len(sh.text_frame.text.split()) < 60]

        def caption_for(pic):
            """The caption whose horizontal centre is nearest this picture."""
            if not caps:
                return ""
            pc = (pic.left or 0) + (pic.width or 0) / 2
            best = min(caps, key=lambda c: abs((c.left or 0) + (c.width or 0) / 2 - pc))
            return " ".join(best.text_frame.text.split())

        for pic in pics:
            name = known.get(hashlib.sha1(pic.image.blob).hexdigest())
            if name is None:
                missing.append((i, "unidentified image"))
                continue
            if name not in E:
                missing.append((i, name))
                continue
            side = ""
            if len(pics) > 1:
                side = " (left)" if pic.left < max(q.left for q in pics) \
                       else " (right)"
            rows.append((i, title_of(sl) + side, name, caption_for(pic),
                         E[name]))

    out = [u"# Every figure in the deck, explained",
           u"",
           u"Generated by `scripts/figures_explained.py` from the deck itself, "
           u"so the figure numbers, captions and sources below cannot drift "
           u"from the slides. Re-run it after any deck rebuild.",
           u"",
           u"Each figure's caption already carries its SOURCE — whether it "
           u"is simulator output or a drawing. This document adds the part a "
           u"caption has no room for: what to look at, what is odd about it, "
           u"and the question to be ready for.",
           u"",
           u"**%d figures.** Figure numbers are the deck's own. The demo "
           u"video carries a figure number but is not a picture, so its "
           u"number does not appear here \u2014 that gap is expected."
           % len(rows), u"", u"---", u""]
    for i, title, name, cap, e in rows:
        # A figure with no "Fig. n" caption is still a figure. Name it by its
        # slide rather than printing "Fig. ?", which reads like a bug.
        head = (u"Fig. %s — %s" % (cap.split()[1].rstrip("."), title)
                if cap.startswith("Fig.") else u"Slide %d — %s" % (i, title))
        out += [u"## %s" % head,
                u"",
                u"*Slide %d · `results/%s`*" % (i, name), u"",
                u"**What it is.** %s" % e["what"], u"",
                u"**What to look at.** %s" % e["look"], u"",
                u"**What is odd about it.** %s" % e["odd"], u"",
                u"**If they ask.** %s" % e["ask"], u"",
                u"<details><summary>the caption as printed on the slide</summary>",
                u"", u"> %s" % cap, u"", u"</details>", u"", u"---", u""]
    if missing:
        out += [u"## Figures with no entry", u"",
                u"These are in the deck and have no explanation written. That "
                u"is a gap, listed rather than hidden:", u""]
        out += [u"- slide %d: `%s`" % m for m in missing]
        out += [u""]
    io.open(OUT, "w", encoding="utf-8").write(u"\n".join(out))
    print("  wrote review/FIGURES-EXPLAINED.md: %d figures explained, %d "
          "with no entry" % (len(rows), len(missing)))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
