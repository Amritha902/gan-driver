// M4.1 — operating-point quantiser
//
// Bins (v_dc, i_load, t_j) into a flat region index for the Pareto table.
// Runs in the outer loop (~1 kHz); nothing here is on the switching-cycle path.
//
// Boundaries are registers, not parameters, so the region map can be retuned
// after the M2 sweep without resynthesis.

`default_nettype none

module quantiser #(
    parameter integer ADC_W    = 12,
    parameter integer N_V      = 3,   // bins per axis
    parameter integer N_I      = 3,
    parameter integer N_T      = 3,
    parameter integer REGION_W = 5    // ceil(log2(N_V*N_I*N_T)) = 5 for 27
) (
    input  wire                 clk,
    input  wire                 rst_n,

    input  wire [ADC_W-1:0]     v_dc,
    input  wire [ADC_W-1:0]     i_load,
    input  wire [ADC_W-1:0]     t_j,
    input  wire                 valid,

    // bin upper edges, loaded at init; [N-2] boundaries for N bins
    input  wire [ADC_W-1:0]     bnd_v [0:N_V-2],
    input  wire [ADC_W-1:0]     bnd_i [0:N_I-2],
    input  wire [ADC_W-1:0]     bnd_t [0:N_T-2],

    output reg  [REGION_W-1:0]  region,
    output reg                  region_valid
);

    function automatic [1:0] bin3 (input [ADC_W-1:0] x,
                                   input [ADC_W-1:0] b0,
                                   input [ADC_W-1:0] b1);
        begin
            if      (x < b0) bin3 = 2'd0;
            else if (x < b1) bin3 = 2'd1;
            else             bin3 = 2'd2;
        end
    endfunction

    wire [1:0] bv = bin3(v_dc,   bnd_v[0], bnd_v[1]);
    wire [1:0] bi = bin3(i_load, bnd_i[0], bnd_i[1]);
    wire [1:0] bt = bin3(t_j,    bnd_t[0], bnd_t[1]);

    // flat index = ((bv * N_I) + bi) * N_T + bt
    wire [REGION_W-1:0] flat = ((bv * N_I) + bi) * N_T + bt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            region       <= '0;
            region_valid <= 1'b0;
        end else begin
            region_valid <= valid;
            if (valid) region <= flat;
        end
    end

endmodule

`default_nettype wire
