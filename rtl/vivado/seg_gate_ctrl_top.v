// ---------------------------------------------------------------------------
// seg_gate_ctrl_top.v -- synthesis top level for Xilinx Vivado
//
// Wraps seg_gate_ctrl and hard-codes the configuration the exhaustive search
// selected, so the FPGA emits the same control word the ngspice study used.
//
// WHY THIS SHAPE
// The study's result is that only ONE field is worth scheduling: dead time,
// and only at light load (freezing it costs 5.45 % over four corners, but
// 0.00 % once the 50 V / 2 A corner is dropped -- three corners want 5 ns,
// one wants 15 ns). Every other field is strapped, because freezing pull-up
// drive strength costs 0.00 % and the clamp is optimal always-on.
//
// So the adaptive hardware here is ONE comparator input, not a sense + ADC +
// lookup table. That is the project's finding expressed as RTL.
//
// CLOCK REQUIREMENT -- read this before choosing a board.
// dt_cycles counts clk cycles, and the swept dead-time grid is 5..35 ns.
// A 100 MHz board clock has 10 ns granularity and CANNOT express 5 ns.
// This top level therefore requires a 200 MHz clock (5 ns/cycle):
//     5 ns -> 1 cycle, 10 -> 2, 15 -> 3, 25 -> 5, 35 -> 7.
// Generate it from the board's 100 MHz oscillator with a Clocking Wizard
// (MMCM) instance; it is left out of this file so the RTL stays portable and
// simulator-clean. On Artix-7 (-1 speed grade) 200 MHz is attainable for
// logic this small, but check the timing report -- do not assume it.
// ---------------------------------------------------------------------------
`default_nettype none

module seg_gate_ctrl_top #(
    parameter integer NSLICE      = 8,
    parameter integer DTW         = 8,
    // dead time in 5 ns clock cycles. The generator produces dt_cycles+1
    // cycles of dead time (property T6 in the bench measures dt_len == dt+1),
    // so these are one less than the intended cycle count.
    parameter [DTW-1:0] DT_HEAVY  = 8'd0,   // -> 1 cycle  =  5 ns
    parameter [DTW-1:0] DT_LIGHT  = 8'd2,   // -> 3 cycles = 15 ns
    // strapped control word: clamp on, negative rail on, drive strengths from
    // the best fixed word found at every corner.
    parameter [3:0] CFG_NPU_LS    = 4'd8,
    parameter [3:0] CFG_NPD_LS    = 4'd8,
    parameter [3:0] CFG_NPU_HS    = 4'd8,
    parameter [3:0] CFG_NPD_HS    = 4'd1,
    parameter       CFG_CLKEN     = 1'b1,
    parameter       CFG_VNEG      = 1'b1
) (
    input  wire              clk_200,     // 200 MHz, 5 ns period
    input  wire              rst_n,
    input  wire              pwm_in,
    input  wire              light_load,  // the single comparator
    output wire [NSLICE-1:0] ls_pu,
    output wire [NSLICE-1:0] ls_pd,
    output wire              ls_clamp,
    output wire [NSLICE-1:0] hs_pu,
    output wire [NSLICE-1:0] hs_pd,
    output wire              hs_clamp,
    output wire              vneg_sel,
    output wire              dead_time_active
);
    // ---- synchronise the asynchronous inputs ------------------------------
    // pwm_in and light_load arrive from off-chip. Two flops each; without this
    // a metastable pwm_in can violate the dead-time guarantee.
    reg [1:0] pwm_sync, ll_sync;
    always @(posedge clk_200 or negedge rst_n)
        if (!rst_n) begin pwm_sync <= 2'b00; ll_sync <= 2'b00; end
        else        begin pwm_sync <= {pwm_sync[0], pwm_in};
                          ll_sync  <= {ll_sync[0],  light_load}; end

    // ---- one-shot config load after reset ---------------------------------
    // seg_gate_ctrl comes out of reset at the SAFEST word (weakest pull-up).
    // Pulse cfg_we once to strap the studied word.
    reg cfg_done, cfg_we;
    always @(posedge clk_200 or negedge rst_n)
        if (!rst_n) begin cfg_done <= 1'b0; cfg_we <= 1'b0; end
        else if (!cfg_done) begin cfg_done <= 1'b1; cfg_we <= 1'b1; end
        else cfg_we <= 1'b0;

    // ---- the only scheduled field -----------------------------------------
    wire [DTW-1:0] dt_cycles = ll_sync[1] ? DT_LIGHT : DT_HEAVY;

    seg_gate_ctrl #(.NSLICE(NSLICE), .DTW(DTW)) u_ctrl (
        .clk(clk_200), .rst_n(rst_n),
        .pwm_in(pwm_sync[1]), .dt_cycles(dt_cycles),
        .cfg_we(cfg_we),
        .cfg_npu_ls(CFG_NPU_LS), .cfg_npd_ls(CFG_NPD_LS),
        .cfg_npu_hs(CFG_NPU_HS), .cfg_npd_hs(CFG_NPD_HS),
        .cfg_clken(CFG_CLKEN),   .cfg_vneg(CFG_VNEG),
        .ls_pu(ls_pu), .ls_pd(ls_pd), .ls_clamp(ls_clamp),
        .hs_pu(hs_pu), .hs_pd(hs_pd), .hs_clamp(hs_clamp),
        .vneg_sel(vneg_sel), .dead_time_active(dead_time_active)
    );
endmodule
`default_nettype wire
