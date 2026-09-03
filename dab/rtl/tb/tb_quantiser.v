`timescale 1ns/1ps
module tb_quantiser;
  localparam ADC_W=12, REGION_W=5;
  reg clk=0, rst_n=0, valid=0;
  reg  [ADC_W-1:0] v_dc, i_load, t_j;
  reg  [ADC_W-1:0] bnd_v [0:1], bnd_i [0:1], bnd_t [0:1];
  wire [REGION_W-1:0] region;
  wire region_valid;

  quantiser u (.clk(clk), .rst_n(rst_n), .v_dc(v_dc), .i_load(i_load), .t_j(t_j),
               .valid(valid), .bnd_v(bnd_v), .bnd_i(bnd_i), .bnd_t(bnd_t),
               .region(region), .region_valid(region_valid));

  always #5 clk = ~clk;

  integer fails = 0;

  task shot(input [ADC_W-1:0] v, input [ADC_W-1:0] i, input [ADC_W-1:0] t,
            input [REGION_W-1:0] expect_r);
    begin
      @(negedge clk); v_dc=v; i_load=i; t_j=t; valid=1;
      @(negedge clk); valid=0;
      @(posedge clk); #1;
      if (region === expect_r)
        $display("  PASS  v=%0d i=%0d t=%0d -> region %0d", v, i, t, region);
      else begin
        $display("  FAIL  v=%0d i=%0d t=%0d -> region %0d (expected %0d)",
                 v, i, t, region, expect_r);
        fails = fails + 1;
      end
    end
  endtask

  initial begin
    bnd_v[0]=1365; bnd_v[1]=2730;   // three bins per axis over a 12-bit ADC
    bnd_i[0]=1365; bnd_i[1]=2730;
    bnd_t[0]=1365; bnd_t[1]=2730;
    repeat(2) @(negedge clk); rst_n=1;

    $display("tb_quantiser: region = ((bv*3)+bi)*3 + bt");
    shot(  100,  100,  100,  0);   // low,  low,  low
    shot( 4000,  100,  100, 18);   // high, low,  low
    shot(  100, 4000,  100,  6);   // low,  high, low
    shot(  100,  100, 4000,  2);   // low,  low,  high
    shot( 4000, 4000, 4000, 26);   // high,high, high
    shot( 2000, 2000, 2000, 13);   // mid, mid, mid

    if (fails==0) $display("ALL PASS"); else $display("%0d FAILURE(S)", fails);
    $finish;
  end
endmodule
