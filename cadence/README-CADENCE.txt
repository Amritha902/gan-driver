CADENCE / SPECTRE FILES
=======================

WHAT IS HERE

  dpt_spectre.scs            The full double-pulse testbench, ready to run.
                             Self-contained: device model, driver and
                             testbench all inlined. Needs NO PDK.

  segdrv_pdk_template.scs    The segmented driver output stage with device
                             names as placeholders, for when you want the
                             driver in real transistors from your lab's PDK.

  sweep.ocn                  OCEAN script reproducing the 720-point control
                             word sweep from inside ADE.

START HERE

  Run dpt_spectre.scs first. It needs nothing from the PDK and should
  reproduce these three numbers:

      gate on-state at 0.9 us ...........  5.00 V
      peak V(lsd) after 1 us ............  122.4 V
      peak V(hsg)-V(sw), 2.015-2.10 us ..  1.65 V   (threshold is 1.40 V)

  The third being above the fourth is the false turn-on the project is
  about. If Spectre gives you different numbers, the port is wrong and I
  want to know -- do not build on top of it.

HONESTY ABOUT WHAT IS AND IS NOT TESTED

  TESTED:   the SPICE body of dpt_spectre.scs was extracted after
            generation and re-simulated in ngspice 42. It reproduces
            5.00 / 122.4 / 1.65 exactly.

  UNTESTED: Spectre itself. There was no Cadence installation available.
            Everything used is ordinary SPICE3 (.param, .subckt, .model D,
            .model SW, B-sources, .func) inside a `simulator lang=spice`
            block, which is the standard way to reuse a SPICE deck in
            Spectre -- but standard is not the same as verified.

  UNTESTED: sweep.ocn. The OCEAN syntax is written from the documented
            forms; check the first few sweep points against
            results/sweep_nominal.csv before running all 720.

WHY THERE IS NO GaN DEVICE IN THE PDK

  There is not one, in any PDK. GaN power devices are discrete parts from
  EPC, Infineon and GaN Systems; they exist as vendor SPICE subcircuits,
  not as PDK cells. The model here is behavioural, written from datasheet
  quantities, and travels with the netlist. That is why dpt_spectre.scs
  needs no PDK at all.

  The PDK is only needed for the DRIVER -- and only if you want it in real
  transistors rather than the behavioural switches. That is what
  segdrv_pdk_template.scs is for.

A BUG THAT BIT THIS FILE THREE TIMES

  The first line of a SPICE deck is the TITLE and is silently consumed.
  Put anything above it -- a header comment, a `simulator lang` directive --
  and the title drops into the body, where it parses as a component and
  Spectre/ngspice reports "could not find a valid modelname". The title
  line in these files is commented out for exactly this reason. If you
  concatenate these decks with anything else, check that first line.
