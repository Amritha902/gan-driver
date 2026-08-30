# -*- coding: utf-8 -*-
"""Content for the Review-1 deck. Every number here is produced by a script in
gan-driver/scripts/ and recorded in results/FINDINGS.md."""

B = True   # bold

SLIDE4 = [
    ([("Problem Statement:", B)], 0),
    ([("In a GaN half-bridge the dV/dt of one device couples through C", False), ("GD", False),
      (" into the gate of the device meant to be off. With a threshold near 1.4 V the spurious "
       "pulse can exceed it and turn that device partially on — shoot-through, extra loss, and at "
       "worst destruction.", False)], 1),
    ([("Background & Significance:", B)], 0),
    ([("GaN half-bridges are the switching core of EV and HEV traction inverters, on-board "
       "chargers and high-density server supplies, where the whole reason to choose GaN is to "
       "switch faster — which is exactly what makes this failure mode worse.", False)], 1),
    ([("Negative off-bias is uniquely expensive on GaN: with no body diode the reverse drop is V",
       False), ("th", False), (" + I·R + |V", False), ("GS,off", False),
      ("|, so each volt of margin is paid for again across the dead time.", False)], 1),
    ([("Existing Solutions:", B)], 0),
    ([("Active gate drivers with segmented drive strength, Miller clamps, programmable dead time "
       "and negative off-bias [1]–[4]. Closed-loop designs adapt to the operating point and report "
       "large gains — 30.5 % less overshoot, 75 % less turn-off loss — against a conventional "
       "driver [5]–[7].", False)], 1),
    ([("Limitations / Research Gap:", B)], 0),
    ([("That comparison conflates ", False), ("choosing better fixed settings", B), (" with ", False),
      ("adapting settings per operating point", B),
      (". Only the second needs sensing, a lookup table and a controller — the hardware cost that "
       "justifies the architecture. No published work isolates them, so the value of adaptation "
       "has never been measured.", False)], 1),
]

SLIDE6 = [
    ([("Proposed Solution:", B)], 0),
    ([("A segmented GaN gate driver with a 720-point control word: 8 pull-up slices, 8 pull-down "
       "slices, dead time 5–35 ns, an active Miller clamp, and a selectable off-bias rail "
       "(0 / −2 V).", False)], 1),
    ([("The contribution is to ", False), ("separate the two claims by exhaustive search", B),
      (": sweep the full word at every corner, so each per-corner optimum is a true optimum and not "
       "the best of a shortlist, then compare against the best single fixed word. That difference "
       "is the value of adaptation, and nothing else.", False)], 1),
    ([("Methodology / Approach:", B)], 0),
    ([("Double-pulse test in ngspice with a behavioural eGaN model from datasheet quantities. Its "
       "channel is symmetric by design, so the third-quadrant penalty of negative bias emerges "
       "from device physics rather than being added by hand.", False)], 1),
    ([("Eight metrics per run — three energies, overshoot, settling, oscillation energy, spurious "
       "gate voltage, crosstalk margin — frozen in one extractor early, so no later sweep becomes "
       "incomparable.", False)], 1),
    ([("Every reported quantity must be flat across a 5× timestep range. Enforced, not assumed: it "
       "has twice rejected a number that had already reached a draft.", False)], 1),
    ([("Project Scope:", B)], 0),
    ([("In scope: ", B), ("driver architecture, control-word optimisation, transistor-level output "
       "stage in SKY130. ", False), ("Out of scope: ", B),
      ("GaN device fabrication, closed-loop sensing hardware, PCB build.", False)], 1),
]

SLIDE7 = [
    ([("Work completed so far (≈ 50 %):", B)], 0),
    ([("Crosstalk reproduced and fixed. ", B),
      ("Fastest drive, no clamp: spurious gate peak 1.65 V against a 1.4 V threshold — false "
       "turn-on. Clamp on with −2 V off-bias: −1.18 V, a 2.58 V margin.", False)], 1),
    ([("Full exhaustive search. ", B),
      ("720 control words at each of four corners (50–200 V, 2–10 A, 25–125 °C) "
       "= 2,880 transients, plus 1,511 over a 36-point operating grid.", False)], 1),
    ([("Robustness study. ", B),
      ("21,600 further transients perturbing five device-model parameters, one failure.", False)], 1),
    ([("Ports generated and re-simulated. ", B),
      ("LTspice-dialect, Spectre and browser-WASM decks each reproduce 122.4 V / 5.00 V / 1.65 V "
       "on re-simulation. LTspice and Spectre themselves are not yet run — no installation "
       "available — so those two are faithful ports, not cross-simulator agreement.", False)], 1),
    ([("Nearly 26,000 transient simulations in total; a 28-section written record; a full manuscript draft.",
       False)], 1),
    ([("Timeline & milestones to Review-III:", B)], 0),
    ([("Review-II: ", B), ("transistor-level output stage in Cadence with a 5 V-capable PDK; "
      "re-run the ceiling on real devices; hardware-in-the-loop plan.", False)], 1),
    ([("Review-III: ", B), ("half-bridge measured at one corner; manuscript submitted.", False)], 1),
    ([("Tools & technologies:", B)], 0),
    ([("ngspice 42 (all sweeps) · LTspice · Cadence Spectre / OCEAN · SKY130 PDK "
       "(BSIM4) · Python / NumPy / Matplotlib · MATLAB Online (independent cross-check) "
       "· Git", False)], 1),
]
