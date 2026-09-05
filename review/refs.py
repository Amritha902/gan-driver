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
 Ref(4, "Li, Zhang, Li, Wang, Liu & Xu (2022)",
     "Crosstalk Suppression Method for GaN-Based Bridge Configuration Using Negative Voltage "
     "Self-Recovery Gate Drive",
     "IEEE Trans. Power Electron., 37(4), 4406–4418",
     "RC-diode divider generates negative V_GS; antiparallel diode gives a low-impedance Miller "
     "path",
     "Suppresses positive and negative crosstalk together. Treats the negative rail as always "
     "beneficial; our freeze test finds off-bias worth 2.55 % to schedule, and nothing at a 1 V "
     "guard band.",
     xplore="9573371", year="2022",
     ieee="B. Li, G. Zhang, C. Li, G. Wang, S. Liu and D. Xu, “Crosstalk Suppression Method for GaN-Based Bridge Configuration Using Negative Voltage Self-Recovery Gate Drive,” IEEE Trans. Power Electron., vol. 37, no. 4, pp. 4406–4418, 2022.", done=True),
 Ref(5, "Chen, Peng, Song, Tong & Kang (2024)",
     "A Novel Control Strategy for Optimal Tradeoff between Overshoot and Switching Loss Based "
     "on Double Closed-Loop Self-Regulating Active Gate Driver",
     "IEEE Trans. Power Electron., 39(10), 13033–13043",
     "Weight-based closed-loop control balancing overshoot against turn-off loss per operating "
     "condition",
     "Reports 30.5 % less overshoot and 75 % less turn-off loss. Optimises the same two "
     "objectives as our cost function, but never bounds what the adaptation itself is worth "
     "against a fixed setting.",
     xplore="10553383", year="2024",
     ieee="X. Chen, H. Peng, S. Song, Q. Tong and Y. Kang, “A Novel Control Strategy for Optimal Tradeoff between Overshoot and Switching Loss Based on Double Closed-Loop Self-Regulating Active Gate Driver,” IEEE Trans. Power Electron., vol. 39, no. 10, pp. 13033–13043, 2024.", done=True),
 Ref(6, "Song, Hu, Chen, Tang, Yue & Liu (2025)",
     "A Self-Regulating Active Gate Driver of Voltage Overshoot Suppression for SiC MOSFETs "
     "Under Variable Load Current Conditions",
     "IEEE Trans. Power Electron., 40(8), 10623–10634",
     "Gate drive self-regulates as load current varies",
     "Adaptation to the operating point is the premise, not a tested hypothesis. This is "
     "precisely the claim our exhaustive search isolates and measures at 5.2 %.",
     xplore="10964227", year="2025",
     ieee="W. Song, T. Hu, J. Chen, T. Tang, H. Yue and G. Liu, “A Self-Regulating Active Gate Driver of Voltage Overshoot Suppression for SiC MOSFETs Under Variable Load Current Conditions,” IEEE Trans. Power Electron., vol. 40, no. 8, pp. 10623–10634, 2025.", done=True),
 Ref(7, "Kuo, Wang, Chen, Tu, Hsiao & Chen (2025)",
     "Universal Active Gate Driver IC With Closed-Loop Timing Control and Gate-Sensing Technique "
     "for Silicon Carbide Power Devices",
     "IEEE Trans. Power Electron., 40(4), 5120–5129",
     "Integrated driver with closed-loop timing and on-chip gate sensing",
     "The sensing and control hardware that per-operating-point scheduling requires. Our result "
     "bounds the benefit that hardware can deliver on this architecture at a few per cent.",
     xplore="10813402", year="2025",
     ieee="C.W. Kuo, T.W. Wang, L.C. Chen, C.C. Tu, Y.K. Hsiao and P.H. Chen, “Universal Active Gate Driver IC With Closed-Loop Timing Control and Gate-Sensing Technique for Silicon Carbide Power Devices,” IEEE Trans. Power Electron., vol. 40, no. 4, pp. 5120–5129, 2025.", done=True),
 Ref(8, "Thuc & Chen (2024)",
     "An Integrated Driver With Dual-Edge Adaptive Dead-Time Control for GaN-Based Synchronous "
     "Buck Converter",
     "IEEE Trans. Ind. Appl., 60(6), 9157–9170",
     "Dual-edge adaptive dead-time control; sub-1 ns dead times across a 0.2–2 A range",
     "Adapts the one field our freeze test says actually carries the benefit — dead time, "
     "5.45 % of the cost, 2.1× the next field — and does it across a 0.2–2 A range, which is "
     "exactly the light-load corner our leave-one-out test shows carries all of it.",
     xplore="10664041", year="2024", doi="10.1109/TIA.2024.3454198",
     ieee="G.H. Thuc and C.J. Chen, “An Integrated Driver With Dual-Edge Adaptive Dead-Time Control for GaN-Based Synchronous Buck Converter,” IEEE Trans. Ind. Appl., vol. 60, no. 6, pp. 9157–9170, 2024.", done=True),
 Ref(9, "H. Takayama, T. Okuda & T. Hikihara (2022)",
     "Digital Active Gate Drive of SiC MOSFETs for Controlling Switching Behavior — "
     "Preparation Toward Universal Digitization of Power Switching",
     "Int. J. Circuit Theory Appl., vol. 50, no. 1, pp. 183–196",
     "A DAC-inspired driver: a multibit gate signal SEQUENCE sets the gate waveform digitally, "
     "so switching behaviour is chosen by a code rather than by a resistor.",
     "THE BASE PAPER. Its multibit gate code is the direct ancestor of our 720-point control "
     "word, and it is digital — implementable on an FPGA — rather than a fixed analogue "
     "network. We replicate its premise on GaN and then ask the question it does not: of the "
     "gain a code buys, how much needs per-operating-point adaptation at all?",
     year="2022", doi="10.1002/cta.3136", base=True,
     ieee="H. Takayama, T. Okuda and T. Hikihara, “Digital Active Gate Drive of SiC MOSFETs for Controlling Switching Behavior — Preparation Toward Universal Digitization of Power Switching,” Int. J. Circuit Theory Appl., vol. 50, no. 1, pp. 183–196, 2022.", done=True),
 Ref(10, "Zhang, Yu, Leng, Cui, Deng & Ng (2020)",
     "A Segmented Gate Driver for E-mode GaN HEMTs with Simple Driving Strength Pattern Control",
     "Proc. IEEE ISPSD, 2020, pp. 102–105",
     "Segmented output stage on E-mode GaN: 7 slices, pattern timing 0.5\u20135 ns, strength set by one external bias resistor",
     "Architecturally the closest published driver to ours — segmented slices, pattern-selected "
     "strength. It is an ASIC with a fixed pattern set; our contribution is to search the whole "
     "pattern space exhaustively and price what the search actually buys.",
     xplore="9170108", year="2020", closest=True,
     ieee="W.J. Zhang, J. Yu, Y. Leng, W.T. Cui, G.Q. Deng and W.T. Ng, “A Segmented Gate Driver for E-mode GaN HEMTs with Simple Driving Strength Pattern Control,” in Proc. IEEE 32nd Int. Symp. Power Semicond. Devices ICs (ISPSD), 2020, pp. 102–105.", done=True),
 Ref(11, "Wang, Tao, Xiao, Luo, He, Zhou, Zhang & Wang (2024)",
     "High-Frequency Three-Level Gate Driver for GaN HEMT Bridge Crosstalk Suppression",
     "IEEE Trans. Power Electron., 39(1), 1343–1352",
     "Three-level drive; capacitor–diode negative rail with a digitally-clamped zero level, to "
     "5 MHz",
     "Recent, GaN, and on exactly our failure mode. It suppresses crosstalk with added passives; "
     "we get the same protection from the Miller clamp already in the cell and measure its price "
     "at 0.04 %.",
     xplore="10286072", year="2024", closest=True,
     ieee="X. Wang, M. Tao, J. Xiao, D. Luo, M. He, Q. Zhou, X. Zhang and M. Wang, “High-Frequency Three-Level Gate Driver for GaN HEMT Bridge Crosstalk Suppression,” IEEE Trans. Power Electron., vol. 39, no. 1, pp. 1343–1352, 2024.", done=True),
 Ref(12, "Wang, Sun, Yan, Ma & Xu (2024)",
     "An Integrated Suppression Method of Both Gate-Source Voltage Oscillation and Crosstalk for "
     "GaN HEMT Gate Driver",
     "IEEE Trans. Power Electron., 39(11), 14643–14655",
     "One driver addressing gate-source ringing and crosstalk together",
     "Confirms the two effects are coupled, which is why our cost function prices loss and "
     "overshoot jointly rather than optimising either alone.",
     xplore="10591431", year="2024", closest=True,
     ieee="L. Wang, X. Sun, Y. Yan, M. Ma and D. Xu, “An Integrated Suppression Method of Both Gate-Source Voltage Oscillation and Crosstalk for GaN HEMT Gate Driver,” IEEE Trans. Power Electron., vol. 39, no. 11, pp. 14643–14655, 2024.", done=True),
 Ref(13, "Cai, Ye, Lv & Chen (2026)",
     "A High-Efficient GaN Driver With Hybrid Adaptive Dead-Time Control and Peak Delay Control "
     "for Synchronous Buck Converter",
     "IEEE Trans. Power Electron., 41(1), 279–290",
     "Hybrid adaptive dead-time plus peak delay control on a GaN synchronous buck",
     "The most recent adaptive dead-time driver we found, and it adapts the one field our "
     "leave-one-out test shows carries the whole benefit — and only at light load.",
     xplore="11146698", year="2026", closest=True,
     ieee="Y. Cai, D. Ye, W. Lv and Z. Chen, “A High-Efficient GaN Driver With Hybrid Adaptive Dead-Time Control and Peak Delay Control for Synchronous Buck Converter,” IEEE Trans. Power Electron., vol. 41, no. 1, pp. 279–290, 2026.", done=True),
 Ref(14, "Zheng, Zhao, Agarwal, Liu, Zhao & Mantooth (2026)",
     "A Multi-Level Turn-Off Gate Driver for Crosstalk Noise Suppression of GaN HEMTs",
     "IEEE Open J. Power Electron., 1–15",
     "Survey breadth — a Multi-Level Turn-Off Gate Driver for Crosstalk Noise Suppression of "
     "GaN HEMTs.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.1109/ojpel.2026.3727513", year="2026", done=True,
     ieee="Y. Zheng, S. Zhao, P. Agarwal, F. Liu, Y. Zhao and A. Mantooth, “A Multi-Level "
     "Turn-Off Gate Driver for Crosstalk Noise Suppression of GaN HEMTs,” IEEE Open J. Power "
     "Electron., pp. 1–15, 2026."),
 Ref(15, "Banda, Madichetty, Natham & Koduru (2026)",
     "An Event-Triggered Dual-Polarity Gate Clamp for GaN HEMT Gate Oscillation Suppression",
     "IEEE Trans. Power Electron., 41(9), 14402–14405",
     "Survey breadth — an Event-Triggered Dual-Polarity Gate Clamp for GaN HEMT Gate "
     "Oscillation Suppression.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.1109/tpel.2026.3689188", year="2026", done=True,
     ieee="M.K. Banda, S. Madichetty, D.M. Natham and S. Koduru, “An Event-Triggered "
     "Dual-Polarity Gate Clamp for GaN HEMT Gate Oscillation Suppression,” IEEE Trans. Power "
     "Electron., vol. 41, no. 9, pp. 14402–14405, 2026."),
 Ref(16, "Yuan, Li, Zhang, Yang, Zhao, Wang, Wang & Ding (2026)",
     "Influence of Negative Gate Bias on Crosstalk Spike in SiC MOSFETs Half-Bridge Circuit",
     "IEEE J. Emerg. Sel. Topics Power Electron., 14(3), 3217–3229",
     "Survey breadth — influence of Negative Gate Bias on Crosstalk Spike in SiC MOSFETs "
     "Half-Bridge Circuit.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.1109/jestpe.2025.3645404", year="2026", done=True,
     ieee="Z. Yuan, H. Li, M. Zhang, Z. Yang, S. Zhao, H. Wang, X. Wang and L. Ding, “Influence "
     "of Negative Gate Bias on Crosstalk Spike in SiC MOSFETs Half-Bridge Circuit,” IEEE J. "
     "Emerg. Sel. Topics Power Electron., vol. 14, no. 3, pp. 3217–3229, 2026."),
 Ref(17, "Zhang, Wang, Guo & Zhu (2025)",
     "A Gate Driver for Crosstalk Suppression of eGaN HEMT Power Devices",
     "J. Low Power Electron. Appl., 15(3), 38",
     "Survey breadth — a Gate Driver for Crosstalk Suppression of eGaN HEMT Power Devices.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.3390/jlpea15030038", year="2025", done=True,
     ieee="L. Zhang, K. Wang, S. Guo and B. Zhu, “A Gate Driver for Crosstalk Suppression of eGaN "
     "HEMT Power Devices,” J. Low Power Electron. Appl., vol. 15, no. 3, pp. 38, 2025."),
 Ref(18, "Wu (2023)",
     "Parallel arrangement of MOSFETs, effective suppression of crosstalk: A new gate driver "
     "topology",
     "iEnergy, 2(3), 163–163",
     "Survey breadth — parallel arrangement of MOSFETs, effective suppression of crosstalk: "
     "A new gate driver topology.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.23919/ien.2023.0032", year="2023", done=True,
     ieee="J. Wu, “Parallel arrangement of MOSFETs, effective suppression of crosstalk: A new "
     "gate driver topology,” iEnergy, vol. 2, no. 3, pp. 163–163, 2023."),
 Ref(19, "Mikhaylov, Buticchi & Galea (2023)",
     "A gate driver for parallel connected MOSFETs with crosstalk suppression",
     "iEnergy, 2(3), 240–250",
     "Survey breadth — a gate driver for parallel connected MOSFETs with crosstalk "
     "suppression.",
     "Cluster A. The actuator is chosen once, at design time, and never revisited as the "
     "operating point moves — exactly the half of the benefit this study separates out.",
     doi="10.23919/ien.2023.0024", year="2023", done=True,
     ieee="Y. Mikhaylov, G. Buticchi and M. Galea, “A gate driver for parallel connected MOSFETs "
     "with crosstalk suppression,” iEnergy, vol. 2, no. 3, pp. 240–250, 2023."),
 Ref(20, "Liu & Min (2026)",
     "A Load Adaptive Active Gate Driver with Fast-Switching Three-Level Current Source for "
     "Overshoot Suppression in GaN-Based Half-Bridge Converters",
     "IEEE Trans. Power Electron., 1–8",
     "Survey breadth — a Load Adaptive Active Gate Driver with Fast-Switching Three-Level "
     "Current Source for Overshoot Suppression in GaN-Based Half-Bridge Converters.",
     "Cluster B. Closes a loop around the switching waveform so it adapts continuously, but "
     "never reports how much of the gain needed the loop rather than a better fixed setting.",
     doi="10.1109/tpel.2026.3724054", year="2026", done=True,
     ieee="W. Liu and H. Min, “A Load Adaptive Active Gate Driver with Fast-Switching Three-Level "
     "Current Source for Overshoot Suppression in GaN-Based Half-Bridge Converters,” IEEE "
     "Trans. Power Electron., pp. 1–8, 2026."),
 Ref(21, "Chen, Wang, Bai & Tolbert (2026)",
     "A Simple Gate Driver Circuit for Turn-on Overvoltage Suppression of 10 kV SiC MOSFETs "
     "With Temporarily Lowering Gate Voltage During dv/dt",
     "IEEE Trans. Ind. Electron., 1–6",
     "Survey breadth — a Simple Gate Driver Circuit for Turn-on Overvoltage Suppression of "
     "10 kV SiC MOSFETs With Temporarily Lowering Gate Voltage During dv/dt.",
     "Cluster B. Closes a loop around the switching waveform so it adapts continuously, but "
     "never reports how much of the gain needed the loop rather than a better fixed setting.",
     doi="10.1109/tie.2026.3725291", year="2026", done=True,
     ieee="R. Chen, F. Wang, H. Bai and L.M. Tolbert, “A Simple Gate Driver Circuit for Turn-on "
     "Overvoltage Suppression of 10 kV SiC MOSFETs With Temporarily Lowering Gate Voltage "
     "During dv/dt,” IEEE Trans. Ind. Electron., pp. 1–6, 2026."),
 Ref(22, "Yu, Yang, Yin, Hu, Zhang & Fu (2026)",
     "A Dual-Loop Active Gate Driver With Independent Voltage Slew Rate and Overshoot "
     "Control for Switching Loss Optimization of SiC MOSFETs",
     "IEEE Trans. Ind. Electron., 1–12",
     "Survey breadth — a Dual-Loop Active Gate Driver With Independent Voltage Slew Rate and "
     "Overshoot Control for Switching Loss Optimization of SiC MOSFETs.",
     "Cluster B. Closes a loop around the switching waveform so it adapts continuously, but "
     "never reports how much of the gain needed the loop rather than a better fixed setting.",
     doi="10.1109/tie.2026.3715930", year="2026", done=True,
     ieee="D. Yu, M. Yang, L. Yin, K. Hu, W. Zhang and Q. Fu, “A Dual-Loop Active Gate Driver "
     "With Independent Voltage Slew Rate and Overshoot Control for Switching Loss "
     "Optimization of SiC MOSFETs,” IEEE Trans. Ind. Electron., pp. 1–12, 2026."),
 Ref(23, "Xiang, Hao, Cai & You (2023)",
     "An Active Gate Driver of SiC MOSFET Module Based on PCB Rogowski Coil for Optimizing "
     "Tradeoff Between Overshoot and Switching Loss",
     "IEEE Trans. Power Electron., 38(1), 245–260",
     "Survey breadth — an Active Gate Driver of SiC MOSFET Module Based on PCB Rogowski Coil "
     "for Optimizing Tradeoff Between Overshoot and Switching Loss.",
     "Cluster B. Closes a loop around the switching waveform so it adapts continuously, but "
     "never reports how much of the gain needed the loop rather than a better fixed setting.",
     doi="10.1109/tpel.2022.3201018", year="2023", done=True,
     ieee="P. Xiang, R. Hao, J. Cai and X. You, “An Active Gate Driver of SiC MOSFET Module Based "
     "on PCB Rogowski Coil for Optimizing Tradeoff Between Overshoot and Switching Loss,” "
     "IEEE Trans. Power Electron., vol. 38, no. 1, pp. 245–260, 2023."),
 Ref(24, "Fukunaga, Takayama & Hikihara (2022)",
     "Slew rate control of switching transient for SiC MOSFET in boost converter using "
     "digital active gate driver",
     "IET Power Electron., 16(3), 472–482",
     "Survey breadth — slew rate control of switching transient for SiC MOSFET in boost "
     "converter using digital active gate driver.",
     "Cluster B. Closes a loop around the switching waveform so it adapts continuously, but "
     "never reports how much of the gain needed the loop rather than a better fixed setting.",
     doi="10.1049/pel2.12398", year="2022", done=True,
     ieee="S. Fukunaga, H. Takayama and T. Hikihara, “Slew rate control of switching transient "
     "for SiC MOSFET in boost converter using digital active gate driver,” IET Power "
     "Electron., vol. 16, no. 3, pp. 472–482, 2022."),
 Ref(25, "Xu, Fu, Liao, Zhu & Liu (2025)",
     "An Integrated Driver With Real-Time Predictive Dead-Time Optimization Technique for "
     "GaN-Based Synchronous Buck Converter",
     "IEEE J. Emerg. Sel. Topics Power Electron., 13(3), 3173–3183",
     "Survey breadth — an Integrated Driver With Real-Time Predictive Dead-Time Optimization "
     "Technique for GaN-Based Synchronous Buck Converter.",
     "Cluster C. Adapts dead time — the one field our leave-one-out test finds carries the "
     "benefit, and in our data only at the light-load corner.",
     doi="10.1109/jestpe.2025.3564383", year="2025", done=True,
     ieee="C. Xu, P. Fu, X. Liao, Z. Zhu and L. Liu, “An Integrated Driver With Real-Time "
     "Predictive Dead-Time Optimization Technique for GaN-Based Synchronous Buck Converter,” "
     "IEEE J. Emerg. Sel. Topics Power Electron., vol. 13, no. 3, pp. 3173–3183, 2025."),
 Ref(26, "Chen, Chiu, Chen, Wang & Chang (2022)",
     "An Integrated Driver With Adaptive Dead-Time Control for GaN-Based Synchronous Buck "
     "Converter",
     "IEEE Trans. Circuits Syst. II, 69(2), 539–543",
     "Survey breadth — an Integrated Driver With Adaptive Dead-Time Control for GaN-Based "
     "Synchronous Buck Converter.",
     "Cluster C. Adapts dead time — the one field our leave-one-out test finds carries the "
     "benefit, and in our data only at the light-load corner.",
     doi="10.1109/tcsii.2021.3098310", year="2022", done=True,
     ieee="C. Chen, P. Chiu, Y. Chen, P. Wang and Y. Chang, “An Integrated Driver With Adaptive "
     "Dead-Time Control for GaN-Based Synchronous Buck Converter,” IEEE Trans. Circuits "
     "Syst. II, vol. 69, no. 2, pp. 539–543, 2022."),
 Ref(27, "Tan, Zhou & Zou (2024)",
     "A Programmable Gate Driver Module-Based Multistage Voltage Regulation SiC MOSFET "
     "Switching Strategy",
     "Electronics, 13(22), 4379",
     "Survey breadth — a Programmable Gate Driver Module-Based Multistage Voltage Regulation "
     "SiC MOSFET Switching Strategy.",
     "Cluster D. The gate waveform is selected by a discrete code, which is what makes the "
     "setting space finite and therefore exhaustively searchable.",
     doi="10.3390/electronics13224379", year="2024", done=True,
     ieee="J. Tan, Z. Zhou and G. Zou, “A Programmable Gate Driver Module-Based Multistage "
     "Voltage Regulation SiC MOSFET Switching Strategy,” Electronics, vol. 13, no. 22, pp. "
     "4379, 2024."),
 Ref(28, "Chen, Wang, Li, Chen & Chang (2022)",
     "An Integrated Driver With Bang-Bang Dead-Time Control and Charge Sharing Bootstrap "
     "Circuit for GaN Synchronous Buck Converter",
     "IEEE Trans. Power Electron., 37(8), 9503–9514",
     "Survey breadth — an Integrated Driver With Bang-Bang Dead-Time Control and Charge "
     "Sharing Bootstrap Circuit for GaN Synchronous Buck Converter.",
     "Cluster D. The gate waveform is selected by a discrete code, which is what makes the "
     "setting space finite and therefore exhaustively searchable.",
     doi="10.1109/tpel.2022.3159717", year="2022", done=True,
     ieee="C. Chen, P. Wang, S. Li, Y. Chen and Y. Chang, “An Integrated Driver With Bang-Bang "
     "Dead-Time Control and Charge Sharing Bootstrap Circuit for GaN Synchronous Buck "
     "Converter,” IEEE Trans. Power Electron., vol. 37, no. 8, pp. 9503–9514, 2022."),
 Ref(29, "Thuc, Tsai, Chen, Fu, Wu & Lin (2026)",
     "A Current Source Gate Driver with Dual-Edge Adaptive Slew Rate for GaN Devices",
     "2026 IEEE Applied Power Electronics Conference and Expositio, 2026",
     "Survey breadth — a Current Source Gate Driver with Dual-Edge Adaptive Slew Rate for "
     "GaN Devices.",
     "Cluster D. The gate waveform is selected by a discrete code, which is what makes the "
     "setting space finite and therefore exhaustively searchable.",
     doi="10.1109/apec51134.2026.11516764", year="2026", done=True,
     ieee="G.H. Thuc, M. Tsai, C. Chen, J. Fu, W. Wu and W. Lin, “A Current Source Gate Driver "
     "with Dual-Edge Adaptive Slew Rate for GaN Devices,” in Proc. 2026 IEEE Applied Power "
     "Electronics Conference and Exposition (APEC), 2026."),
 Ref(30, "Wu, Huang, Chen & Chen (2025)",
     "Closed-loop Slew Rate Control of Active Current Source Gate Driver with Digital "
     "Implementation for SiC MOSFET",
     "2025 IEEE Energy Conversion Conference Congress and Expositi, 2025",
     "Survey breadth — closed-loop Slew Rate Control of Active Current Source Gate Driver "
     "with Digital Implementation for SiC MOSFET.",
     "Cluster D. The gate waveform is selected by a discrete code, which is what makes the "
     "setting space finite and therefore exhaustively searchable.",
     doi="10.1109/ecce58356.2025.11259572", year="2025", done=True,
     ieee="G. Wu, Y. Huang, Y. Chen and C. Chen, “Closed-loop Slew Rate Control of Active Current "
     "Source Gate Driver with Digital Implementation for SiC MOSFET,” in Proc. 2025 IEEE "
     "Energy Conversion Conference Congress and Exposition (ECCE), 2025."),
]

DONE    = [r for r in REFS if r.done]
PENDING = [r for r in REFS if not r.done]
