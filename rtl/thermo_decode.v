// ---------------------------------------------------------------------------
// thermo_decode.v -- binary slice count -> thermometer enable vector
//
// The segmented output stage is N discrete slices, not one variable resistor.
// A code of k enables slices 0..k-1, so the drive strength is monotonic in k
// and every code maps 1:1 onto a sized transistor when the stage is redrawn
// in Cadence. models/segdrv.lib does the same thing with
// {runit + (npu>=i ? 0 : 1e9)}; this is the FPGA-side equivalent.
//
// code = 0 disables every slice, which is a legal (and useful) state: it is
// how the driver tri-states during the dead time.
// ---------------------------------------------------------------------------
`default_nettype none

module thermo_decode #(
    parameter integer N = 8              // number of slices
) (
    input  wire [$clog2(N+1)-1:0] code,  // 0..N
    output wire [N-1:0]           en
);
    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_slice
            assign en[i] = (code > i[$clog2(N+1)-1:0]);
        end
    endgenerate
endmodule

`default_nettype wire
