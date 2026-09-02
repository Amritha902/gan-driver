RUNNING THIS IN LTSPICE
=======================

OPEN THESE THREE FILES. They contain the real active Miller clamp.

    A_baseline_FALSE_TURN_ON.cir      no clamp, 0 V off-bias   -> FAILS
    B_miller_clamp_ON.cir             clamp on, 0 V off-bias   -> safe
    C_clamp_and_negative_bias.cir     clamp + -2 V off-bias    -> shipped

HOW
    1. Keep them in this folder, together with egan.lib and segdrv.lib.
    2. LTspice > File > Open. Change the file-type dropdown to "All Files"
       (LTspice hides .cir by default).
    3. Open one of the three and press Run.
    4. Probe  V(hsg,sw)  -- the high-side gate-source voltage. Threshold 1.4 V.
    5. View > SPICE Error Log shows the measured vspur.

WHAT YOU SHOULD SEE  -- verified in ngspice on these exact files, 1 Sep 2026

    A   vspur =  1.649 V   vs 1.4 V threshold  -> FALSE TURN-ON, margin -0.249 V
    B   vspur =  0.830 V                       -> SAFE,          margin +0.570 V
    C   vspur = -1.176 V                       -> SAFE,          margin +2.576 V

If LTspice disagrees with these, the port is wrong -- say so, do not present it.

WHERE THE CLAMP IS
    segdrv.lib:
        Sclk out nclk clk ref SWP     the clamp switch, separately timed
        Rclk nclk vn {rclamp}         0.5 ohm to the NEGATIVE rail
    It clamps to the negative rail, not to the source. That matters: clamping
    to source would fight the -2 V off-bias instead of reinforcing it.

    .param CLKEN=1   engages the clamp
    .param VNEG=-2   selects the negative off-bias rail

THE THREE .asc SCHEMATIC SHEETS
    1_baseline_FALSE_TURN_ON.asc, 2_miller_clamp_on.asc,
    3_clamp_and_negative_bias.asc

    These are simplified DRAWINGS for explaining the crosstalk mechanism.
    They do NOT contain the Miller clamp, and their stimulus does not even
    produce a switching event inside their own measurement window, so their
    .meas returns ~0.02 V rather than the 1.65 V annotated on them. Their
    labels now say this.

    Do not present the .asc sheets as the clamped design. Use the .cir files
    above -- those are the verified model.

CHANGING THE CONTROL WORD
    Edit the PARAM BLOCK near the top of any of the three files:
        NPU_LS NPD_LS NPU_HS NPD_HS   slice counts, 0..8
        DT                            dead time
        CLKEN                         Miller clamp on/off
        VNEG                          off-bias rail, 0 or -2

    Slice enables are baked to literals by scripts/to_ltspice.py so LTspice
    has no ternaries to evaluate. To change npu/npd, re-run:
        python3 scripts/to_ltspice.py --npu 4 --npd 8
