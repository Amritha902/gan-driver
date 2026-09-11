`timescale 1ps/1ps
//=====================================================================
// seg_gate_ctrl_dpt_tb.v -- drive the controller the way the CONVERTER
// does, so its output can be played into the SPICE power stage.
//
// WHY A SECOND TESTBENCH
// seg_gate_ctrl_tb.v is a unit test. It sweeps the control word to prove
// the thermometer decoder is right, and it is good at that. But its
// stimulus has nothing to do with a switching converter: it visits
// configurations like npu_ls = 0, where the pull-up bank is empty and,
// with the low side commanded on, neither bank drives the gate. Played
// into a real power stage that leaves the gate on 1 GOhm while 100 V
// slews past it, and the node integrates to kilovolts. The simulator is
// right; the question is meaningless.
//
// This bench asks the meaningful question instead. It reproduces
// sim/dpt.cir's double-pulse schedule exactly, at the real 200 MHz FPGA
// clock, with the shipped control word:
//
//     t < 1.000 us   low side ON, high side off      pwm_in = 0
//     t = 1.000 us   pwm_in rises -> dead time -> high side on at T2
//     t = 2.000 us   pwm_in falls -> dead time -> low side on at T4
//     t = 3.000 us   end
//
// T4 is where the crosstalk number every result in this project reports
// is measured: the low side turns on hard, the switch node slews, and
// charge couples into the high-side gate through C_GD.
//
// DEAD TIME, AND AN OFF-BY-ONE WORTH KNOWING. dpt.cir uses DT = 15 ns.
// The obvious mapping at 200 MHz is 15/5 = 3 cycles. That is WRONG: it
// gives 20 ns. dead_time_gen loads cnt <= dt_cycles and then counts down
// THROUGH zero, so it spends dt_cycles + 1 clocks in S_DEAD. Measured on
// this bench:
//
//     dt_cycles = 1 -> 10 ns     dt_cycles = 3 -> 20 ns
//     dt_cycles = 2 -> 15 ns     dt_cycles = 4 -> 25 ns
//
// So dead time = (dt_cycles + 1) x 5 ns, and dpt.cir's 15 ns is
// dt_cycles = 2. Anyone mapping the swept DT grid onto the hardware by
// dividing by the clock period builds a driver that is one cycle slow at
// every point. This is exactly the kind of mismatch co-simulating the two
// halves is for -- neither the Icarus bench nor the SPICE sweep could see
// it alone.
//
// The RTL's own generator makes the T2 and T4 edges here; the bench only
// commands the edge. The dead time in the SPICE run is therefore the one
// the hardware actually produces, not one a testbench drew.
//
// CLAMP. Selectable with +clken=0/1 so the co-simulation can run both.
// With the clamp off the gate is held only by the pull-down bank, which
// during dead time is exactly what the project claims is not enough;
// with it on the gate is clamped. Running both is the demonstration.
//
//     iverilog -g2012 -o tb seg_gate_ctrl_dpt_tb.v seg_gate_ctrl.v \
//              dead_time_gen.v thermo_decode.v
//     vvp tb +clken=1
//=====================================================================
module seg_gate_ctrl_dpt_tb;

    // 200 MHz -> 5 ns period -> 2500 ps half period
    localparam integer HALF   = 2500;
    localparam integer DTCYC  = 2;          // -> 15 ns, matching dpt.cir's DT

    // SETTLE WINDOW, AND WHY THE SCHEDULE IS OFFSET BY IT.
    // The RTL needs a few clocks to leave reset and load its control word,
    // and until it does it commands neither device on. Start the SPICE run
    // at that instant and the power stage sees both GaN devices off with
    // 10 A already in the load inductor: SW slews to the rail, rings, and
    // couples ~59 V into the low-side gate through C_GD. That is a true
    // answer to a question nobody asks -- no converter is energised while
    // its controller is held in reset.
    //
    // So the whole double pulse is pushed out by TSET, and rtl_cosim.py
    // subtracts TSET again when it turns the VCD into PWL sources. The
    // reset then happens before SPICE t = 0, the low side is already fully
    // on at t = 0 exactly as dpt.cir's own stimulus has it, and T1/T3 land
    // on 1.000 us and 2.000 us as the deck's .param block expects.
    //
    // TSET is 5 clock periods, so every edge stays clock-aligned.
    localparam integer TSET   = 25_000;     // 25 ns = 5 cycles

    // dpt.cir's schedule, in ps, offset by TSET
    localparam integer T1     = TSET + 1_000_000;  // low side commanded off
    localparam integer T3     = TSET + 2_000_000;  // high side commanded off
    localparam integer TSTOP  = TSET + 3_000_000;

    reg         clk   = 1'b0;
    reg         rst_n = 1'b0;
    reg         pwm   = 1'b0;
    reg         cfg_we = 1'b0;
    reg  [7:0]  dt     = DTCYC;
    reg  [3:0]  npu_ls = 4'd8, npd_ls = 4'd8, npu_hs = 4'd8, npd_hs = 4'd8;
    reg         clken  = 1'b1;
    reg         vneg   = 1'b1;

    wire [7:0]  ls_pu, ls_pd, hs_pu, hs_pd;
    wire        ls_clamp, hs_clamp, vneg_sel, in_dt;

    seg_gate_ctrl #(.NSLICE(8), .DTW(8)) dut (
        .clk(clk), .rst_n(rst_n),
        .pwm_in(pwm), .dt_cycles(dt),
        .cfg_we(cfg_we),
        .cfg_npu_ls(npu_ls), .cfg_npd_ls(npd_ls),
        .cfg_npu_hs(npu_hs), .cfg_npd_hs(npd_hs),
        .cfg_clken(clken),   .cfg_vneg(vneg),
        .ls_pu(ls_pu), .ls_pd(ls_pd), .ls_clamp(ls_clamp),
        .hs_pu(hs_pu), .hs_pd(hs_pd), .hs_clamp(hs_clamp),
        .vneg_sel(vneg_sel), .dead_time_active(in_dt)
    );

    always #HALF clk = ~clk;

    integer clken_arg;
    integer saw_dt;

    initial begin
        saw_dt = 0;
        // clamp is selectable so the co-simulation can run it both ways
        if (!$value$plusargs("clken=%d", clken_arg)) clken_arg = 1;
        clken = clken_arg[0];

        $dumpfile("seg_gate_ctrl_dpt.vcd");
        $dumpvars(0, seg_gate_ctrl_dpt_tb);

        // hold reset a few cycles; the RTL comes up in its safe word
        repeat (4) @(posedge clk);
        rst_n = 1'b1;

        // strap the shipped control word: full drive both banks, clamp per
        // plusarg, negative off-bias rail selected
        @(posedge clk);
        cfg_we = 1'b1;
        @(posedge clk);
        cfg_we = 1'b0;

        // --- dpt.cir's double pulse -----------------------------------
        // Absolute times, not clock counts: T1 and T3 must land where
        // dpt.cir puts them. Both are exact multiples of the 5 ns clock
        // (200 and 400 cycles), so the edges are still clock-aligned.
        //
        // pwm_in rises at T1; the RTL inserts its own dead time, so the
        // high side comes on at T1 + 15 ns, which is dpt.cir's T2. It
        // falls at T3, so the low side comes on at T3 + 15 ns == T4 --
        // the hard turn-on the crosstalk margin is measured across.
        #(T1 - $time) pwm = 1'b1;
        #(T3 - T1)    pwm = 1'b0;
        #(TSTOP - T3);

        $display("seg_gate_ctrl double-pulse bench");
        $display("  clamp enabled      : %0d", clken);
        $display("  dead-time cycles   : %0d  (%0d ns at 200 MHz)", dt, (dt+1)*5);
        $display("  dead time observed : %0s", saw_dt ? "yes" : "NO -- check dt_cycles");
        $display("  VCD                : seg_gate_ctrl_dpt.vcd");
        if (saw_dt) $display("\n  BENCH OK");
        else        $display("\n  BENCH PROBLEM: no dead time asserted");
        $finish;
    end

    // dead time must actually happen, or the co-simulation is meaningless
    always @(posedge clk) if (in_dt) saw_dt = 1;

    // and both devices must never be commanded on together, ever
    always @(posedge clk) begin
        if (rst_n && (|ls_pu) && (|hs_pu)) begin
            $display("FATAL: both banks pulling up at %0t -- shoot-through", $time);
            $finish;
        end
    end

endmodule
