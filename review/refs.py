# -*- coding: utf-8 -*-
"""The literature survey.

VERIFICATION STATUS, stated precisely because it differs between the two sets.

  [1]-[3]  Verified against the publisher record earlier in this project:
           title, author list, volume, issue, pages and year all confirmed.

  [4]-[8]  Title, journal-vs-conference and IEEE Xplore document ID confirmed
           from search results. Volume, issue, pages and author list COULD NOT
           be confirmed from this environment: ieeexplore.ieee.org, doi.org,
           api.crossref.org, api.openalex.org, api.semanticscholar.org,
           link.springer.com, mdpi.com, researchgate.net and par.nsf.gov are
           every one blocked by the network egress proxy. Those fields are
           therefore left as XX and must be completed from Xplore's "Cite This"
           button, which takes one click on the VIT network.

           They are NOT invented. An unverified number in a citation is the
           same class of error this project spent a week removing from its own
           results.
"""

# (num, authors, title, venue, method, finding, xplore_id, verified)
REFS = [
 (1, "Zhang, Wang, Tolbert & Blalock (2014)",
  "Active Gate Driver for Crosstalk Suppression of SiC Devices in a Phase-Leg Configuration",
  "IEEE Trans. Power Electron., 29(4), 1986–1997",
  "Two gate-assist circuits on a SiC MOSFET phase leg; suppresses the spurious gate pulse",
  "Up to 17 % less turn-on loss. SiC has a body diode, so the third-quadrant cost of negative off-bias — the GaN-specific trade — never arises.",
  "6531666", True),
 (2, "Xie, Wang, Tang, Yang & Chen (2017)",
  "An Analytical Model for False Turn-On Evaluation of High-Voltage Enhancement-Mode GaN Transistor in Bridge-Leg Configuration",
  "IEEE Trans. Power Electron., 32(8), 6416–6433",
  "Closed-form model of the crosstalk loop for e-mode GaN; predicts the spurious gate peak",
  "Models the mechanism accurately but does not optimise a driver against it, and never asks whether settings must adapt per operating point.",
  "7854840", True),
 (3, "Reusch & Strydom (2014)",
  "Understanding the Effect of PCB Layout on Circuit Performance in a High-Frequency Gallium-Nitride-Based Point of Load Converter",
  "IEEE Trans. Power Electron., 29(4), 2008–2015",
  "Measures a GaN converter across deliberately varied board layouts",
  "Loop inductance is set by layout, not by the device. Our robustness study finds the scheduling ceiling depends on exactly this parameter: 13.5 % at 1.5 nH against 0.6 % at 4.5 nH.",
  "6531683", True),
 (4, "IEEE Trans. Power Electron. (journal)",
  "Crosstalk Suppression Method for GaN-Based Bridge Configuration Using Negative Voltage Self-Recovery Gate Drive",
  "IEEE Xplore doc. 9573371 — vol./pp. XX",
  "RC-diode divider generates negative V_GS; antiparallel diode gives a low-impedance Miller path",
  "Suppresses positive and negative crosstalk together. Treats the negative rail as always beneficial; our freeze test finds off-bias worth 2.55 % to schedule, and nothing at a 1 V guard band.",
  "9573371", False),
 (5, "IEEE journal (SiC active gate driver)",
  "A Novel Control Strategy for Optimal Tradeoff between Overshoot and Switching Loss Based on Double Closed-Loop Self-Regulating Active Gate Driver",
  "IEEE Xplore doc. 10553383 — vol./pp. XX",
  "Weight-based closed-loop control balancing overshoot against turn-off loss per operating condition",
  "Reports 30.5 % less overshoot and 75 % less turn-off loss. Optimises the same two objectives as our cost function, but never bounds what the adaptation itself is worth against a fixed setting.",
  "10553383", False),
 (6, "IEEE journal (SiC active gate driver)",
  "A Self-Regulating Active Gate Driver of Voltage Overshoot Suppression for SiC MOSFETs Under Variable Load Current Conditions",
  "IEEE Xplore doc. 10964227 — vol./pp. XX",
  "Gate drive self-regulates as load current varies",
  "Adaptation to the operating point is the premise, not a tested hypothesis. This is precisely the claim our exhaustive search isolates and measures at 5.2 %.",
  "10964227", False),
 (7, "IEEE journal (SiC gate driver IC)",
  "Universal Active Gate Driver IC With Closed-Loop Timing Control and Gate-Sensing Technique for Silicon Carbide Power Devices",
  "IEEE Xplore doc. 10813402 — vol./pp. XX",
  "Integrated driver with closed-loop timing and on-chip gate sensing",
  "The sensing and control hardware that per-operating-point scheduling requires. Our result bounds the benefit that hardware can deliver on this architecture at a few per cent.",
  "10813402", False),
 (8, "IEEE journal (GaN integrated driver)",
  "An Integrated Driver With Dual-Edge Adaptive Dead-Time Control for GaN-Based Synchronous Buck Converter",
  "IEEE Xplore doc. 10664041 — vol./pp. XX",
  "Dual-edge adaptive dead-time control; sub-1 ns dead times across a 0.2–2 A range",
  "Adapts the one field our freeze test says actually carries the benefit — dead time, 5.45 % of the cost, 4.6× the next field. Direct independent support for the paper's central recommendation.",
  "10664041", False),
]
