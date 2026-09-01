// Self-check for the Vivado top level: config strapping, the light-load
// dead-time switch, and the shoot-through guarantee through the wrapper.
`timescale 1ns/1ps
module seg_gate_ctrl_top_tb;
    reg clk=0, rst_n=0, pwm=0, ll=0;
    wire [7:0] ls_pu, ls_pd, hs_pu, hs_pd;
    wire ls_clamp, hs_clamp, vneg_sel, dta;
    integer fails=0, dt_len=0;
    reg measuring=0;

    always #2.5 clk = ~clk;              // 200 MHz

    seg_gate_ctrl_top dut(.clk_200(clk), .rst_n(rst_n), .pwm_in(pwm),
        .light_load(ll), .ls_pu(ls_pu), .ls_pd(ls_pd), .ls_clamp(ls_clamp),
        .hs_pu(hs_pu), .hs_pd(hs_pd), .hs_clamp(hs_clamp),
        .vneg_sel(vneg_sel), .dead_time_active(dta));

    task check(input cond, input [255:0] name);
        if (!cond) begin fails=fails+1; $display("  FAIL  %0s (t=%0t)", name, $time); end
    endtask

    // continuous: never drive both pull-up banks
    always @(posedge clk)
        if (rst_n && (|hs_pu) && (|ls_pu)) begin
            fails=fails+1; $display("  FAIL  shoot-through hs_pu=%b ls_pu=%b (t=%0t)", hs_pu, ls_pu, $time);
        end
    // continuous: no slice driven during dead time
    always @(posedge clk)
        if (rst_n && dta && ((|hs_pu)||(|ls_pu))) begin
            fails=fails+1; $display("  FAIL  slice driven in dead time (t=%0t)", $time);
        end

    // measure dead-time length
    always @(posedge clk) if (rst_n) begin
        if (dta) dt_len <= dt_len + 1;
        else if (dt_len != 0) begin measuring <= 1; end
    end

    initial begin
        $display("seg_gate_ctrl_top self-check");
        repeat(4) @(posedge clk); rst_n = 1;
        repeat(4) @(posedge clk);
        check(vneg_sel === 1'b1, "T1 negative rail strapped after cfg load");
        check(dut.u_ctrl.clken === 1'b1, "T2 clamp strapped on");
        check(dut.u_ctrl.npd_hs === 4'd1, "T3 cfg_npd_hs strapped to 1");

        // heavy load: expect 1 cycle of dead time
        ll = 0; dt_len = 0;
        pwm = 1; repeat(20) @(posedge clk);
        pwm = 0; repeat(20) @(posedge clk);
        check(dt_len == 2, "T4 heavy-load dead time = 1 cycle per edge (2 edges)");
        if (dt_len != 2) $display("        measured %0d", dt_len);

        // light load: expect 3 cycles of dead time
        ll = 1; repeat(4) @(posedge clk); dt_len = 0;
        pwm = 1; repeat(20) @(posedge clk);
        pwm = 0; repeat(20) @(posedge clk);
        check(dt_len == 6, "T5 light-load dead time = 3 cycles per edge (2 edges)");
        if (dt_len != 6) $display("        measured %0d", dt_len);

        if (fails == 0) $display("\n  ALL CHECKS PASSED\n");
        else            $display("\n  %0d CHECK(S) FAILED\n", fails);
        $finish;
    end
endmodule
