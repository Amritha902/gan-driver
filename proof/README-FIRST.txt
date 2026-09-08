================================================================================
  GaN-BASED POWER CONVERTER  --  Project-I, Review-I
  Amritha S (23BEC1368) . Sanjay Kumar (23BEC1447) . Aamir Abdullah (23BPS1197)
  Guide: Dr. Bindu, SENSE, VIT Chennai
================================================================================

WHAT THE PROJECT IS

  The project is a GaN-based power converter: 100 V DC in, 48.6 V DC out at
  4.88 A -- 236.9 W into the load from 242.6 W drawn, so 97.6 % efficient.
  Inside it is a GaN half-bridge, two transistors switching 500,000 times a
  second, and the circuit that switches them is the gate driver.
  When one transistor switches, its fast voltage swing pushes charge into the
  gate of the other one -- the one that is supposed to be OFF -- and can turn
  it on by accident, shorting the supply. Gate drivers fix that, and the
  published ones also re-tune themselves while running, which needs a sensor,
  an ADC and a lookup table. We measured how much of the benefit actually
  needs that re-tuning. Most of it does not.

--------------------------------------------------------------------------------
IF YOU ONLY DO ONE THING

  Open Terminal and run:

      cd ~/GAN_MAIN/PROOF
      zsh RUN-LIVE.sh

  Eleven steps, about three minutes. Each one starts a real tool on this
  laptop -- ngspice, Icarus Verilog, GNU Octave -- and prints the number that
  is on the slide. Step 9 opens a window with the waveforms ngspice has just
  produced; step 10 runs the converter and prints power in and power out.

  Nothing in that run is read from the presentation. If a number on a slide is
  wrong, this is where it shows.

--------------------------------------------------------------------------------
IF YOU WANT TO CHECK ONE SPECIFIC NUMBER

  PROOF/WHERE-EVERY-NUMBER-COMES-FROM.md

  Every number on every slide, with the exact command that produces it.

--------------------------------------------------------------------------------
IF YOU JUST WANT TO LOOK

  PROOF/screenshots/     18 screenshots. Terminal output as it happened, with
                         the machine name and time on screen; the Verilog
                         source; the Vivado windows; the waveforms.
  PROOF/logs/            the raw text of each of those runs.

--------------------------------------------------------------------------------
WHAT IS IN EACH FOLDER

  PROOF/                 the live demo, the screenshots, the logs,
                         and the number-by-number map
  1-CIRCUIT-ngspice/     the GaN device model, the gate driver, the converter
                         (sim/buck.cir) and the double-pulse test bench.
                         The converter is where 100 V -> 48.6 V and 97.6 %
                         come from; the bench is where 1.65 V and 2.58 V do.
  2-RTL-verilog/         the FPGA controller: three modules and a
                         self-checking testbench with 8 properties
  3-FPGA-vivado/         the Vivado scripts and the two report files it
                         wrote: 20 LUTs, 20 flip-flops, 200 MHz met
  4-MATLAB/              the .m analysis files and the sweep data they read
  5-RESULTS/             every figure in the deck, and the raw CSV data
  6-PRESENTATION/        the deck (.pptx and .pdf) and the speech script

--------------------------------------------------------------------------------
HONEST LIMITS, STATED BY US

  * Nothing has been measured on real hardware yet. This is a simulation
    study and the title says so. Building and measuring one operating point
    is the Review-III milestone.
  * Everything rests on one GaN device model, built from the datasheet.
  * Vivado has no macOS version. Synthesis was run on a Windows machine by a
    project member; its two report files are included unedited, and the
    screenshots show the tool that wrote them.
  * The stored sweep data was produced with ngspice 42. This laptop runs
    ngspice 47, so a live re-run differs in the last digit -- about 0.1 %.
    Step 2 of the live demo shows exactly that.

--------------------------------------------------------------------------------
EVERYTHING IS ALSO ONLINE

  github.com/Amritha902/gan-driver

  with the full commit history, so the dates on the work are checkable too.

  This folder is a curated copy for reading. The working repository it was
  built from is ~/gan-driver on this laptop, and the demo scripts run there.
================================================================================
