// M4.2 — Pareto table
//
// Holds, for every operating region, a short list of non-dominated control settings
// produced by the offline sweep (M2) and the Pareto extraction (M3).
//
//   address = { region, point }
//
// Each entry carries the control word the modulator needs and the three metrics the
// mode arbiter compares when it picks a point on the front.
//
// Inferred as block RAM: the output is registered and there is no reset on the read
// path, which is what Vivado requires to map this to a BRAM rather than to LUTs.
// One cycle of read latency; `valid` is pipelined to match.
//
// Word layout, MSB first — must match scripts/gen_synthetic_table.py exactly:
//
//   [68:59] m_zvs    soft-switching margin, normalised   (10 b)
//   [58:49] m_irms   RMS current stress, normalised      (10 b)
//   [48:39] m_loss   total loss, normalised              (10 b)
//   [38:31] t_dead   dead-time, in fine-timing steps     ( 8 b)
//   [30:20] phi      outer phase shift, signed           (11 b)
//   [19:10] d2       secondary duty cycle                (10 b)
//   [ 9: 0] d1       primary duty cycle                  (10 b)

`default_nettype none

module pareto_table #(
    parameter integer REGION_W  = 5,     // 27 regions needs 5 bits
    parameter integer PT_W      = 3,     // 8 Pareto points per region
    parameter integer D_W       = 10,
    parameter integer PHI_W     = 11,    // signed: negative = reverse power flow
    parameter integer TD_W      = 8,
    parameter integer MET_W     = 10,
    parameter         INIT_FILE = "pareto_table.mem"
) (
    input  wire                    clk,
    input  wire                    en,
    input  wire [REGION_W-1:0]     region,
    input  wire [PT_W-1:0]         point,

    output reg  [D_W-1:0]          d1,
    output reg  [D_W-1:0]          d2,
    output reg  signed [PHI_W-1:0] phi,
    output reg  [TD_W-1:0]         t_dead,

    output reg  [MET_W-1:0]        m_loss,
    output reg  [MET_W-1:0]        m_irms,
    output reg  [MET_W-1:0]        m_zvs,
    output reg                     valid
);

    localparam integer ADDR_W = REGION_W + PT_W;
    localparam integer DEPTH  = 1 << ADDR_W;
    localparam integer WORD_W = 2*D_W + PHI_W + TD_W + 3*MET_W;   // 69 bits

    // field offsets, low to high
    localparam integer O_D1   = 0;
    localparam integer O_D2   = O_D1   + D_W;
    localparam integer O_PHI  = O_D2   + D_W;
    localparam integer O_TD   = O_PHI  + PHI_W;
    localparam integer O_LOSS = O_TD   + TD_W;
    localparam integer O_IRMS = O_LOSS + MET_W;
    localparam integer O_ZVS  = O_IRMS + MET_W;

    (* ram_style = "block" *)
    reg [WORD_W-1:0] mem [0:DEPTH-1];

    integer k;
    initial begin
        // Zero first so an entry the sweep never filled reads as zeros rather than X,
        // which keeps the arbiter's comparisons defined during simulation.
        for (k = 0; k < DEPTH; k = k + 1) mem[k] = {WORD_W{1'b0}};
        if (INIT_FILE != "") $readmemh(INIT_FILE, mem);
    end

    wire [ADDR_W-1:0] addr = {region, point};
    reg  [WORD_W-1:0] q;

    always @(posedge clk) begin
        if (en) q <= mem[addr];
        valid <= en;
    end

    // Unpack. Combinational off the registered word, so the BRAM output register
    // is the only thing between address and data.
    always @(*) begin
        d1     = q[O_D1   +: D_W];
        d2     = q[O_D2   +: D_W];
        phi    = q[O_PHI  +: PHI_W];
        t_dead = q[O_TD   +: TD_W];
        m_loss = q[O_LOSS +: MET_W];
        m_irms = q[O_IRMS +: MET_W];
        m_zvs  = q[O_ZVS  +: MET_W];
    end

endmodule

`default_nettype wire
