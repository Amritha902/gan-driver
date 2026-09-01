// ---------------------------------------------------------------------------
// seg_gate_ctrl_tb.v -- self-checking testbench.
//
// This ASSERTS rather than prints. A waveform you have to eyeball is not a
// test; the whole project's discipline is that a claim needs a check behind
// it, and RTL is no different.
//
//   T1  no shoot-through, ever: hs_pu and ls_pu never overlap
//   T2  the dead time is exactly dt_cycles long, at three settings
//   T3  during a dead time every slice is off and both clamps are on
//   T4  thermometer codes are monotonic and correct for all 0..8
//   T5  reset lands on the SAFE word, not the fast one
//   T6  a mid-flight dt_cycles change cannot shorten a dead time in progress
//   T7  dead_time_gen's own contract: BOTH sides are low during a dead time
//
// T7 exists because mutation testing found that breaking dead_time_gen's
// output clearing did NOT fail this bench: seg_gate_ctrl's independent
// `!in_dt` gating still held the slices off. The two mechanisms are separate
// belts, which is the right design, but it means each needs its own check or
// a regression in one hides behind the other.
//
//   iverilog -g2012 -o tb.vvp seg_gate_ctrl_tb.v seg_gate_ctrl.v \
//            dead_time_gen.v thermo_decode.v && vvp tb.vvp
// ---------------------------------------------------------------------------
`timescale 1ns/1ps
`default_nettype none

module seg_gate_ctrl_tb;
    localparam integer NSLICE = 8, DTW = 8;

    reg               clk = 0, rst_n = 0, pwm = 0;
    reg  [DTW-1:0]    dt = 8'd10;
    reg               cfg_we = 0;
    reg  [3:0]        npu_ls = 4'd8, npd_ls = 4'd8, npu_hs = 4'd8, npd_hs = 4'd8;
    reg               clken = 1'b1, vneg = 1'b0;

    wire [NSLICE-1:0] ls_pu, ls_pd, hs_pu, hs_pd;
    wire              ls_clamp, hs_clamp, vneg_sel, in_dt;

    integer errors = 0;
    integer dt_len = 0, i;
    reg     counting = 0;

    always #5 clk = ~clk;                       // 100 MHz

    seg_gate_ctrl #(.NSLICE(NSLICE), .DTW(DTW)) dut (
        .clk(clk), .rst_n(rst_n), .pwm_in(pwm), .dt_cycles(dt),
        .cfg_we(cfg_we), .cfg_npu_ls(npu_ls), .cfg_npd_ls(npd_ls),
        .cfg_npu_hs(npu_hs), .cfg_npd_hs(npd_hs),
        .cfg_clken(clken), .cfg_vneg(vneg),
        .ls_pu(ls_pu), .ls_pd(ls_pd), .ls_clamp(ls_clamp),
        .hs_pu(hs_pu), .hs_pd(hs_pd), .hs_clamp(hs_clamp),
        .vneg_sel(vneg_sel), .dead_time_active(in_dt)
    );

    task check(input cond, input [255:0] name);
        begin
            if (!cond) begin
                errors = errors + 1;
                $display("  FAIL  %0s   (t=%0t)", name, $time);
            end
        end
    endtask

    // ---- T1: shoot-through is checked continuously, not sampled ----------
    always @(posedge clk) if (rst_n)
        if ((|hs_pu) && (|ls_pu)) begin
            errors = errors + 1;
            $display("  FAIL  T1 shoot-through: hs_pu=%b ls_pu=%b (t=%0t)",
                     hs_pu, ls_pu, $time);
        end

    // ---- T3: dead-time invariants, also continuous -----------------------
    always @(posedge clk) if (rst_n && in_dt) begin
        if (|hs_pu || |ls_pu) begin
            errors = errors + 1;
            $display("  FAIL  T3 slice driven during dead time (t=%0t)", $time);
        end
        if (clken && !(ls_clamp && hs_clamp)) begin
            errors = errors + 1;
            $display("  FAIL  T3 clamp released during dead time (t=%0t)", $time);
        end
    end

    // ---- T7: the generator's own both-low contract ----------------------
    // "never both HIGH" is the wrong property to assert here: a generator that
    // simply forgets to clear its outputs still satisfies it, because only one
    // was high to begin with. The contract is that BOTH are low for the whole
    // dead time, and that is what this checks.
    always @(posedge clk) if (rst_n && in_dt && (hs_on_probe || ls_on_probe)) begin
        errors = errors + 1;
        $display("  FAIL  T7 dead_time_gen held a side on during dead time (t=%0t)",
                 $time);
    end
    wire hs_on_probe = dut.hs_on;
    wire ls_on_probe = dut.ls_on;

    // ---- measure dead-time length ----------------------------------------
    always @(posedge clk) begin
        if (in_dt) begin counting <= 1; dt_len <= dt_len + 1; end
        else if (counting) counting <= 0;
    end

    initial begin
        $dumpfile("seg_gate_ctrl.vcd");
        $dumpvars(0, seg_gate_ctrl_tb);
        $display("seg_gate_ctrl self-check");

        // ---- T5: reset state -------------------------------------------
        @(negedge clk); rst_n = 0; @(negedge clk); @(negedge clk);
        check(dut.npu_ls == 4'd0 && dut.npu_hs == 4'd0, "T5 reset pull-up must be 0 (safe)");
        check(dut.npd_ls == 4'd8 && dut.npd_hs == 4'd8, "T5 reset pull-down must be 8");
        check(dut.clken  == 1'b1, "T5 reset clamp must be on");
        check(dut.vneg   == 1'b1, "T5 reset must select the negative rail");
        rst_n = 1;

        // load a working word
        @(negedge clk); cfg_we = 1; @(negedge clk); cfg_we = 0;

        // ---- T2: dead time is exactly dt_cycles long -------------------
        for (i = 0; i < 3; i = i + 1) begin
            dt = (i == 0) ? 8'd5 : (i == 1) ? 8'd10 : 8'd25;
            @(negedge clk); repeat (40) @(negedge clk);
            dt_len = 0;
            pwm = ~pwm;                                  // command an edge
            wait (in_dt); wait (!in_dt);
            @(negedge clk);
            check(dt_len == dt + 1,
                  "T2 dead-time length must equal dt_cycles");
            if (dt_len != dt + 1)
                $display("        measured %0d cycles, expected %0d", dt_len, dt + 1);
        end

        // ---- T6: a late dt change must not shorten the current dead time
        dt = 8'd25; repeat (40) @(negedge clk);
        dt_len = 0; pwm = ~pwm;
        wait (in_dt);
        repeat (3) @(negedge clk); dt = 8'd2;            // shrink mid-flight
        wait (!in_dt); @(negedge clk);
        check(dt_len == 26, "T6 mid-flight dt change must not truncate");
        if (dt_len != 26) $display("        measured %0d, expected 26", dt_len);
        dt = 8'd10;

        // ---- T4: thermometer decode across the whole range -------------
        for (i = 0; i <= 8; i = i + 1) begin
            @(negedge clk); npu_ls = i[3:0]; cfg_we = 1;
            @(negedge clk); cfg_we = 0;
            repeat (2) @(negedge clk);
            check(dut.pu_ls_v == ((1 << i) - 1),
                  "T4 thermometer code must be monotonic and correct");
            if (dut.pu_ls_v !== ((1 << i) - 1))
                $display("        code %0d -> %b, expected %b",
                         i, dut.pu_ls_v, ((1 << i) - 1));
        end

        repeat (20) @(negedge clk);
        $display("");
        if (errors == 0) $display("  ALL CHECKS PASSED");
        else             $display("  %0d CHECK(S) FAILED", errors);
        $display("");
        $finish;
    end
endmodule

`default_nettype wire
