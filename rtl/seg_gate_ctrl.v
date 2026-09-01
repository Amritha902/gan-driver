// ---------------------------------------------------------------------------
// seg_gate_ctrl.v -- FPGA-side controller for the segmented GaN gate driver
//
// Emits exactly the control word the SPICE model consumes, so an FPGA driving
// real hardware and the ngspice sweep are running the same configuration:
//
//   field      bits  range        SPICE .param   worth scheduling?
//   ---------  ----  -----------  -------------  -----------------
//   NPU_LS      4    0..8         NPU_LS         0.00 %  - strap it
//   NPD_LS      4    0..8         NPD_LS         2.03 %
//   NPD_HS      4    0..8         NPD_HS         0.97 %
//   DT          8    cycles       DT             5.45 %  <- LIVE
//   CLKEN       1    0/1          CLKEN          0.00 %  - always 1
//   VNEG        1    0/1          VNEG (0/-2 V)  2.55 %
//
// The grid swept in simulation was NPU in {1,2,3,4,6,8}, NPD_LS in {2,8},
// NPD_HS in {1,4,8}, DT in {5,10,15,25,35} ns, CLKEN in {0,1}, VNEG in
// {0,-2} = 720 words. This module accepts the full 0..8 range on each slice
// count; the swept grid is a subset.
//
// STRUCTURE. cfg_* are strapped through a single-cycle load (cfg_we) and are
// not expected to change in flight. dt_cycles has its own port and may be
// rewritten every cycle - that is the one field the study found worth
// adapting to the operating point.
//
// SAFETY. Slice enables are gated by the dead-time state, so during a dead
// time every pull-up and pull-down slice on both sides is off and the gates
// are held by their clamps. The high-side and low-side pull-ups can never be
// asserted simultaneously: they are driven from hs_on / ls_on, which
// dead_time_gen guarantees are never both high.
//
// MILLER CLAMP. clkEN=1 holds the clamp on whenever that side is off, which
// is what the sweep found optimal at every corner (freezing it costs 0.00 %).
// clkEN=0 disables it entirely and exists only to reproduce the unclamped
// baseline the study compares against.
// ---------------------------------------------------------------------------
`default_nettype none

module seg_gate_ctrl #(
    parameter integer NSLICE = 8,        // slices per bank
    parameter integer DTW    = 8         // dead-time counter width
) (
    input  wire              clk,
    input  wire              rst_n,

    input  wire              pwm_in,     // 1 = command high side on
    input  wire [DTW-1:0]    dt_cycles,  // LIVE: dead time in clk cycles

    // strapped configuration, latched on cfg_we
    input  wire              cfg_we,
    input  wire [3:0]        cfg_npu_ls,
    input  wire [3:0]        cfg_npd_ls,
    input  wire [3:0]        cfg_npu_hs,
    input  wire [3:0]        cfg_npd_hs,
    input  wire              cfg_clken,  // 1 = active Miller clamp enabled
    input  wire              cfg_vneg,   // 1 = select the -2 V off-bias rail

    // low-side driver
    output wire [NSLICE-1:0] ls_pu,
    output wire [NSLICE-1:0] ls_pd,
    output wire              ls_clamp,
    // high-side driver
    output wire [NSLICE-1:0] hs_pu,
    output wire [NSLICE-1:0] hs_pd,
    output wire              hs_clamp,
    // rail select, common to both sides
    output wire              vneg_sel,
    output wire              dead_time_active
);
    // ---- strapped config -------------------------------------------------
    reg [3:0] npu_ls, npd_ls, npu_hs, npd_hs;
    reg       clken, vneg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset to the SAFEST word, not the fastest: weakest pull-up,
            // strongest pull-down, clamp on, negative rail selected. A driver
            // that comes out of reset at full drive into an unknown bus is how
            // devices die.
            npu_ls <= 4'd0;  npd_ls <= 4'd8;
            npu_hs <= 4'd0;  npd_hs <= 4'd8;
            clken  <= 1'b1;  vneg   <= 1'b1;
        end else if (cfg_we) begin
            npu_ls <= cfg_npu_ls;  npd_ls <= cfg_npd_ls;
            npu_hs <= cfg_npu_hs;  npd_hs <= cfg_npd_hs;
            clken  <= cfg_clken;   vneg   <= cfg_vneg;
        end
    end

    assign vneg_sel = vneg;

    // ---- dead-time generator --------------------------------------------
    wire hs_on, ls_on, in_dt;

    dead_time_gen #(.DTW(DTW)) u_dt (
        .clk(clk), .rst_n(rst_n),
        .pwm_in(pwm_in), .dt_cycles(dt_cycles),
        .hs_on(hs_on), .ls_on(ls_on), .in_dead_time(in_dt)
    );

    assign dead_time_active = in_dt;

    // ---- thermometer decode ---------------------------------------------
    wire [NSLICE-1:0] pu_ls_v, pd_ls_v, pu_hs_v, pd_hs_v;

    thermo_decode #(.N(NSLICE)) u_pu_ls (.code(npu_ls), .en(pu_ls_v));
    thermo_decode #(.N(NSLICE)) u_pd_ls (.code(npd_ls), .en(pd_ls_v));
    thermo_decode #(.N(NSLICE)) u_pu_hs (.code(npu_hs), .en(pu_hs_v));
    thermo_decode #(.N(NSLICE)) u_pd_hs (.code(npd_hs), .en(pd_hs_v));

    // ---- output gating ---------------------------------------------------
    // During a dead time nothing is driven: both banks off, both clamps on
    // (when enabled). That is the state the third-quadrant conduction penalty
    // is paid in, and it is why dead time is the field worth scheduling.
    assign ls_pu = (ls_on && !in_dt) ? pu_ls_v : {NSLICE{1'b0}};
    assign ls_pd = (!ls_on || in_dt) ? pd_ls_v : {NSLICE{1'b0}};
    assign hs_pu = (hs_on && !in_dt) ? pu_hs_v : {NSLICE{1'b0}};
    assign hs_pd = (!hs_on || in_dt) ? pd_hs_v : {NSLICE{1'b0}};

    assign ls_clamp = clken && (!ls_on || in_dt);
    assign hs_clamp = clken && (!hs_on || in_dt);
endmodule

`default_nettype wire
