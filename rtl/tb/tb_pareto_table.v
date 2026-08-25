`timescale 1ns/1ps
//
// Testbench for pareto_table.v
//
// Expected values are recomputed here from the same formulas used by
// scripts/gen_synthetic_table.py, but written out independently in Verilog. If the
// packing in the RTL and the packing in the generator ever disagree, this fails —
// which is the whole point, since a silent field-offset mismatch would corrupt every
// control word the modulator ever sees.

module tb_pareto_table;

  localparam integer REGION_W = 5, PT_W = 3;
  localparam integer D_W = 10, PHI_W = 11, TD_W = 8, MET_W = 10;
  localparam integer N_REGIONS = 27;

  reg clk = 0, en = 0;
  reg [REGION_W-1:0] region = 0;
  reg [PT_W-1:0]     point  = 0;

  wire [D_W-1:0]          d1, d2;
  wire signed [PHI_W-1:0] phi;
  wire [TD_W-1:0]         t_dead;
  wire [MET_W-1:0]        m_loss, m_irms, m_zvs;
  wire                    valid;

  integer fails = 0;
  integer r, p;
  integer prev_loss, prev_irms, prev_td;

  pareto_table #(.REGION_W(REGION_W), .PT_W(PT_W), .D_W(D_W), .PHI_W(PHI_W),
                 .TD_W(TD_W), .MET_W(MET_W),
                 .INIT_FILE("data/pareto_table.mem"))
    dut (.clk(clk), .en(en), .region(region), .point(point),
         .d1(d1), .d2(d2), .phi(phi), .t_dead(t_dead),
         .m_loss(m_loss), .m_irms(m_irms), .m_zvs(m_zvs), .valid(valid));

  always #5 clk = ~clk;

  // --- expected values, mirroring gen_synthetic_table.py ---
  function integer clipw(input integer x, input integer w);
    begin
      if (x < 0)                  clipw = 0;
      else if (x > (1<<w)-1)      clipw = (1<<w)-1;
      else                        clipw = x;
    end
  endfunction
  function integer e_d1(input integer rg, input integer pt);
    begin e_d1 = clipw(512 + 40*((rg/9)-1) - 6*pt, D_W); end
  endfunction
  function integer e_d2(input integer rg, input integer pt);
    begin e_d2 = clipw(512 - 30*((rg/9)-1) + 4*pt, D_W); end
  endfunction
  function integer e_phi(input integer rg, input integer pt);
    begin e_phi = 60 + 90*((rg/3)%3) + 14*pt; end
  endfunction
  function integer e_td(input integer rg, input integer pt);
    begin e_td = clipw(24 + 6*((rg/3)%3) + 3*(rg%3) + 2*pt, TD_W); end
  endfunction
  function integer e_loss(input integer rg, input integer pt);
    begin e_loss = clipw(300 + 55*pt + 30*((rg/3)%3) + 12*(rg%3), MET_W); end
  endfunction
  function integer e_irms(input integer rg, input integer pt);
    begin e_irms = clipw(900 - 70*pt + 40*((rg/3)%3), MET_W); end
  endfunction

  task read(input integer rg, input integer pt);
    begin
      @(negedge clk); region = rg[REGION_W-1:0]; point = pt[PT_W-1:0]; en = 1;
      @(negedge clk); en = 0;
      @(posedge clk); #1;
    end
  endtask

  task chk(input [200:0] nm, input integer got, input integer exp);
    begin
      if (got !== exp) begin
        $display("  FAIL %0s: got %0d expected %0d", nm, got, exp);
        fails = fails + 1;
      end
    end
  endtask

  initial begin
    $display("tb_pareto_table");

    // ---- 1. every region and point unpacks to the expected fields ----
    for (r = 0; r < N_REGIONS; r = r + 1)
      for (p = 0; p < (1<<PT_W); p = p + 1) begin
        read(r, p);
        chk("d1",     d1,     e_d1(r,p));
        chk("d2",     d2,     e_d2(r,p));
        chk("phi",    phi,    e_phi(r,p));
        chk("t_dead", t_dead, e_td(r,p));
        chk("m_loss", m_loss, e_loss(r,p));
        chk("m_irms", m_irms, e_irms(r,p));
      end
    $display("  field unpack over %0d regions x %0d points: %0s",
             N_REGIONS, 1<<PT_W, fails==0 ? "PASS" : "FAIL");

    // ---- 2. the front is a real trade-off: loss up, current down ----
    read(13, 0); prev_loss = m_loss; prev_irms = m_irms;
    for (p = 1; p < (1<<PT_W); p = p + 1) begin
      read(13, p);
      if (!(m_loss > prev_loss)) begin
        $display("  FAIL front: loss not rising at pt %0d", p); fails = fails + 1;
      end
      if (!(m_irms < prev_irms)) begin
        $display("  FAIL front: irms not falling at pt %0d", p); fails = fails + 1;
      end
      prev_loss = m_loss; prev_irms = m_irms;
    end
    $display("  monotonic trade-off along the front: %0s", fails==0 ? "PASS" : "FAIL");

    // ---- 3. dead-time actually varies with region — the path that matters ----
    read(0, 0);  prev_td = t_dead;
    read(26, 0);
    if (t_dead == prev_td) begin
      $display("  FAIL t_dead identical across regions 0 and 26 (%0d)", t_dead);
      fails = fails + 1;
    end else
      $display("  t_dead varies across regions: %0d -> %0d  PASS", prev_td, t_dead);

    // ---- 4. read latency is exactly one cycle, and valid tracks en ----
    @(negedge clk); region = 5; point = 2; en = 1;
    @(posedge clk); #1;
    if (valid !== 1'b1) begin $display("  FAIL valid not high one cycle after en"); fails = fails + 1; end
    @(negedge clk); en = 0;
    @(posedge clk); #1;
    if (valid !== 1'b0) begin $display("  FAIL valid not low one cycle after en drops"); fails = fails + 1; end
    $display("  one-cycle latency and valid pipelining: %0s", fails==0 ? "PASS" : "FAIL");

    // ---- 5. an unused address reads as zeros, not X ----
    read(30, 0);
    if (^{d1,d2,t_dead,m_loss,m_irms,m_zvs} === 1'bx) begin
      $display("  FAIL unused entry reads X"); fails = fails + 1;
    end else if (d1 !== 0 || m_loss !== 0) begin
      $display("  FAIL unused entry not zeroed (d1=%0d loss=%0d)", d1, m_loss); fails = fails + 1;
    end else
      $display("  unused entry reads clean zeros: PASS");

    // ---- 6. reverse power flow: phi must come back negative ----
    read(N_REGIONS, 0);
    if (phi !== -300) begin
      $display("  FAIL reverse flow: phi = %0d, expected -300", phi); fails = fails + 1;
    end else begin
      read(N_REGIONS, 3);
      if (phi !== -330) begin
        $display("  FAIL reverse flow: phi = %0d at pt 3, expected -330", phi); fails = fails + 1;
      end else
        $display("  signed phi for reverse power flow: -300 / -330  PASS");
    end

    if (fails == 0) $display("ALL PASS");
    else            $display("%0d FAILURE(S)", fails);
    $finish;
  end

endmodule
