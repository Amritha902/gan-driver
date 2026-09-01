// ---------------------------------------------------------------------------
// dead_time_gen.v -- complementary outputs with a RUNTIME-PROGRAMMABLE dead time
//
// This module is the point of the whole controller.
//
// The study behind this project searched a 720-point control word exhaustively
// at four operating corners and asked which fields are worth adapting to the
// operating point. The answer (FINDINGS.md section 17, paper Table IV):
//
//     dead time ............ 5.45 %   <- worth scheduling
//     gate off-bias ........ 2.55 %
//     pull-down strength ... 2.03 %
//     high-side pull-down .. 0.97 %
//     pull-up strength ..... 0.00 %   <- NOT worth scheduling
//     Miller clamp ......... 0.00 %   (always on is always right)
//
// So dead time gets a live register the controller can rewrite every cycle,
// and the drive-strength fields are strapped at configuration time. Building
// fast reload paths for the other fields would be hardware paying for nothing.
//
// Timing: on any edge of pwm_in, BOTH outputs are driven low for dt_cycles,
// then the newly-selected side is driven high. Both-low is the safe state -
// it is a dead time, not a shoot-through window. dt_cycles is sampled at the
// start of each dead time, so a mid-flight update cannot shorten an interval
// that has already begun.
// ---------------------------------------------------------------------------
`default_nettype none

module dead_time_gen #(
    parameter integer DTW = 8            // dead-time counter width
) (
    input  wire            clk,
    input  wire            rst_n,
    input  wire            pwm_in,       // 1 = want high side on
    input  wire [DTW-1:0]  dt_cycles,    // dead time, in clk cycles
    output reg             hs_on,
    output reg             ls_on,
    output wire            in_dead_time
);
    localparam [1:0] S_LS = 2'd0, S_DEAD = 2'd1, S_HS = 2'd2;

    reg [1:0]     state;
    reg [DTW-1:0] cnt;
    reg           pwm_q;      // pwm_in, registered - the edge detector
    reg           target;     // which side to energise after this dead time

    assign in_dead_time = (state == S_DEAD);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state  <= S_DEAD;
            cnt    <= {DTW{1'b0}};
            pwm_q  <= 1'b0;
            target <= 1'b0;
            hs_on  <= 1'b0;
            ls_on  <= 1'b0;
        end else begin
            pwm_q <= pwm_in;

            case (state)
                S_LS, S_HS: begin
                    if (pwm_in != pwm_q) begin        // commanded edge
                        hs_on  <= 1'b0;
                        ls_on  <= 1'b0;
                        target <= pwm_in;
                        cnt    <= dt_cycles;          // sampled once, here
                        state  <= S_DEAD;
                    end
                end

                S_DEAD: begin
                    if (cnt == {DTW{1'b0}}) begin
                        hs_on <=  target;
                        ls_on <= ~target;
                        state <= target ? S_HS : S_LS;
                    end else begin
                        cnt <= cnt - 1'b1;
                    end
                end

                default: state <= S_DEAD;
            endcase
        end
    end
endmodule

`default_nettype wire
