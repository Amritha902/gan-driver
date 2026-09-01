# -*- coding: utf-8 -*-
"""The literature survey — the single source for BOTH the survey tables
(slides 5-6) and the IEEE reference list (slide 16).

=========================  TO FINISH THE CITATIONS  =========================

Five entries need volume, issue, pages, year and the author list. They are
NOT invented here: ieeexplore.ieee.org, doi.org, api.crossref.org,
api.openalex.org, api.semanticscholar.org, link.springer.com, mdpi.com,
researchgate.net, par.nsf.gov, dblp.org, core.ac.uk and ouci.dntb.gov.ua are
every one blocked by this environment's egress policy. On the VIT network
they are one click each.

For each entry below with  done=False :

  1. open  https://ieeexplore.ieee.org/document/<xplore>
  2. press "Cite This", choose IEEE, copy the string
  3. paste it over the  ieee=""  line
  4. replace  authors="..."  with the real author list, e.g. "R. Xie et al. (2017)"
  5. set  done=True

Then run:   python3 build.py

Both the survey table and the reference list regenerate from this file, so
there is exactly one place to edit and no chance of the two disagreeing.
============================================================================
"""

class Ref:
    def __init__(self, n, authors, title, venue, method, finding, xplore="", ieee="",
                 done=False, doi="", year="", base=False, closest=False):
        self.n, self.authors, self.title, self.venue = n, authors, title, venue
        self.method, self.finding, self.xplore = method, finding, xplore
        self.ieee, self.done = ieee, done
        # venue/year/DOI are verifiable without Xplore; author lists and page
        # numbers are not, and are never invented here.
        self.doi, self.year, self.base, self.closest = doi, year, base, closest

    def cite(self):
        """The IEEE-format line for the reference list."""
        if self.done:
            return self.ieee
        bits = []
        if self.authors and self.authors.strip() not in ("", "—"):
            bits.append(self.authors.split(" (")[0] + ",")
        bits.append("“%s,”" % self.title)
        if self.venue: bits.append(self.venue + ",")
        if self.year:  bits.append(str(self.year) + ",")
        if self.doi:   bits.append("doi: %s." % self.doi)
        line = " ".join(bits)
        return line + "  [author list and page range: Xplore “Cite This”]"

    def table_author(self):
        """The slide column. Year is verified; the author list is not, so it
        says so in three words rather than shouting a placeholder."""
        if self.done:
            return self.authors
        if self.authors and self.authors.strip() not in ("", "—"):
            return self.authors          # known — do not print a placeholder
        return ("%s\nauthors: Xplore “Cite This”" % (self.year or "—"))

    def url(self):
        """A link the panel can actually type or click."""
        if self.doi:   return "doi.org/" + self.doi
        if self.xplore: return "ieeexplore.ieee.org/document/" + self.xplore
        return ""

    def table_venue(self):
        v = self.venue or "IEEE"
        u = self.url()
        return "%s\n%s" % (v, u) if u else v


REFS = [
 Ref(1, "Zhang, Wang, Tolbert & Blalock (2014)",
     "Active Gate Driver for Crosstalk Suppression of SiC Devices in a Phase-Leg Configuration",
     "IEEE Trans. Power Electron., 29(4), 1986–1997",
     "Two gate-assist circuits on a SiC MOSFET phase leg; suppresses the spurious gate pulse",
     "Up to 17 % less turn-on loss. SiC has a body diode, so the third-quadrant cost of negative "
     "off-bias — the GaN-specific trade — never arises.",
     xplore="6531666", done=True,
     ieee="Z. Zhang, F. Wang, L. M. Tolbert and B. J. Blalock, “Active Gate Driver for "
          "Crosstalk Suppression of SiC Devices in a Phase-Leg Configuration,” IEEE Trans. "
          "Power Electron., vol. 29, no. 4, pp. 1986–1997, Apr. 2014."),
 Ref(2, "Xie, Wang, Tang, Yang & Chen (2017)",
     "An Analytical Model for False Turn-On Evaluation of High-Voltage Enhancement-Mode GaN "
     "Transistor in Bridge-Leg Configuration",
     "IEEE Trans. Power Electron., 32(8), 6416–6433",
     "Closed-form model of the crosstalk loop for e-mode GaN; predicts the spurious gate peak",
     "Models the mechanism accurately but does not optimise a driver against it, and never asks "
     "whether settings must adapt per operating point.",
     xplore="7854840", done=True,
     ieee="R. Xie, H. Wang, G. Tang, X. Yang and K. J. Chen, “An Analytical Model for False "
          "Turn-On Evaluation of High-Voltage Enhancement-Mode GaN Transistor in Bridge-Leg "
          "Configuration,” IEEE Trans. Power Electron., vol. 32, no. 8, pp. 6416–6433, "
          "Aug. 2017."),
 Ref(3, "Reusch & Strydom (2014)",
     "Understanding the Effect of PCB Layout on Circuit Performance in a High-Frequency "
     "Gallium-Nitride-Based Point of Load Converter",
     "IEEE Trans. Power Electron., 29(4), 2008–2015",
     "Measures a GaN converter across deliberately varied board layouts",
     "Loop inductance is set by layout, not by the device. Our robustness study finds the "
     "scheduling ceiling depends on exactly this parameter: 13.5 % at 1.5 nH against 0.6 % at "
     "4.5 nH.",
     xplore="6531683", done=True,
     ieee="D. Reusch and J. Strydom, “Understanding the Effect of PCB Layout on Circuit "
          "Performance in a High-Frequency Gallium-Nitride-Based Point of Load Converter,” "
          "IEEE Trans. Power Electron., vol. 29, no. 4, pp. 2008–2015, Apr. 2014."),
 Ref(4, "—",
     "Crosstalk Suppression Method for GaN-Based Bridge Configuration Using Negative Voltage "
     "Self-Recovery Gate Drive",
     "IEEE Trans. Power Electron.",
     "RC-diode divider generates negative V_GS; antiparallel diode gives a low-impedance Miller "
     "path",
     "Suppresses positive and negative crosstalk together. Treats the negative rail as always "
     "beneficial; our freeze test finds off-bias worth 2.55 % to schedule, and nothing at a 1 V "
     "guard band.",
     xplore="9573371", year="2021"),
 Ref(5, "—",
     "A Novel Control Strategy for Optimal Tradeoff between Overshoot and Switching Loss Based "
     "on Double Closed-Loop Self-Regulating Active Gate Driver",
     "IEEE journal",
     "Weight-based closed-loop control balancing overshoot against turn-off loss per operating "
     "condition",
     "Reports 30.5 % less overshoot and 75 % less turn-off loss. Optimises the same two "
     "objectives as our cost function, but never bounds what the adaptation itself is worth "
     "against a fixed setting.",
     xplore="10553383", year="2024"),
 Ref(6, "—",
     "A Self-Regulating Active Gate Driver of Voltage Overshoot Suppression for SiC MOSFETs "
     "Under Variable Load Current Conditions",
     "IEEE journal",
     "Gate drive self-regulates as load current varies",
     "Adaptation to the operating point is the premise, not a tested hypothesis. This is "
     "precisely the claim our exhaustive search isolates and measures at 5.2 %.",
     xplore="10964227", year="2025"),
 Ref(7, "—",
     "Universal Active Gate Driver IC With Closed-Loop Timing Control and Gate-Sensing Technique "
     "for Silicon Carbide Power Devices",
     "IEEE journal",
     "Integrated driver with closed-loop timing and on-chip gate sensing",
     "The sensing and control hardware that per-operating-point scheduling requires. Our result "
     "bounds the benefit that hardware can deliver on this architecture at a few per cent.",
     xplore="10813402", year="2025"),
 Ref(8, "—",
     "An Integrated Driver With Dual-Edge Adaptive Dead-Time Control for GaN-Based Synchronous "
     "Buck Converter",
     "IEEE Trans. Ind. Appl., vol. 60",
     "Dual-edge adaptive dead-time control; sub-1 ns dead times across a 0.2–2 A range",
     "Adapts the one field our freeze test says actually carries the benefit — dead time, "
     "5.45 % of the cost, 2.1× the next field — and does it across a 0.2–2 A range, which is "
     "exactly the light-load corner our leave-one-out test shows carries all of it.",
     xplore="10664041", year="2024", doi="10.1109/TIA.2024.3454198"),
 Ref(9, "Takayama & Hikihara (2022)",
     "Digital Active Gate Drive of SiC MOSFETs for Controlling Switching Behavior — "
     "Preparation Toward Universal Digitization of Power Switching",
     "Int. J. Circuit Theory Appl., vol. 50, no. 1, pp. 183–196",
     "A DAC-inspired driver: a multibit gate signal SEQUENCE sets the gate waveform digitally, "
     "so switching behaviour is chosen by a code rather than by a resistor.",
     "THE BASE PAPER. Its multibit gate code is the direct ancestor of our 720-point control "
     "word, and it is digital — implementable on an FPGA — rather than a fixed analogue "
     "network. We replicate its premise on GaN and then ask the question it does not: of the "
     "gain a code buys, how much needs per-operating-point adaptation at all?",
     year="2022", doi="10.1002/cta.3136", base=True),
 Ref(10, "—",
     "A Segmented Gate Driver for E-mode GaN HEMTs with Simple Driving Strength Pattern Control",
     "IEEE conference",
     "Segmented output stage on E-mode GaN with an on-chip pattern generator for drive strength",
     "Architecturally the closest published driver to ours — segmented slices, pattern-selected "
     "strength. It is an ASIC with a fixed pattern set; our contribution is to search the whole "
     "pattern space exhaustively and price what the search actually buys.",
     xplore="9170108", year="2020", closest=True),
 Ref(11, "—",
     "High-Frequency Three-Level Gate Driver for GaN HEMT Bridge Crosstalk Suppression",
     "IEEE journal",
     "Three-level drive; capacitor–diode negative rail with a digitally-clamped zero level, to "
     "5 MHz",
     "Recent, GaN, and on exactly our failure mode. It suppresses crosstalk with added passives; "
     "we get the same protection from the Miller clamp already in the cell and measure its price "
     "at 0.04 %.",
     xplore="10286072", year="2024", closest=True),
 Ref(12, "—",
     "An Integrated Suppression Method of Both Gate-Source Voltage Oscillation and Crosstalk for "
     "GaN HEMT Gate Driver",
     "IEEE journal",
     "One driver addressing gate-source ringing and crosstalk together",
     "Confirms the two effects are coupled, which is why our cost function prices loss and "
     "overshoot jointly rather than optimising either alone.",
     xplore="10591431", year="2024", closest=True),
 Ref(13, "—",
     "A High-Efficient GaN Driver With Hybrid Adaptive Dead-Time Control and Peak Delay Control "
     "for Synchronous Buck Converter",
     "IEEE journal",
     "Hybrid adaptive dead-time plus peak delay control on a GaN synchronous buck",
     "The most recent adaptive dead-time driver we found, and it adapts the one field our "
     "leave-one-out test shows carries the whole benefit — and only at light load.",
     xplore="11146698", year="2025", closest=True),
]

DONE    = [r for r in REFS if r.done]
PENDING = [r for r in REFS if not r.done]
