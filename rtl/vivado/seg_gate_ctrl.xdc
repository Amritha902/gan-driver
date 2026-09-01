# ---------------------------------------------------------------------------
# seg_gate_ctrl.xdc -- timing and I/O constraints
#
# PIN LOCATIONS ARE PLACEHOLDERS. They must be set to your actual board's
# pinout before this will build. The clock constraint below is the part that
# matters and is board-independent.
# ---------------------------------------------------------------------------

# ---- clock -----------------------------------------------------------------
# 200 MHz, 5 ns period. This is a REQUIREMENT, not a preference: the swept
# dead-time grid starts at 5 ns and a 100 MHz clock cannot express it.
# Drive clk_200 from a Clocking Wizard (MMCM) fed by the board oscillator.
create_clock -period 5.000 -name clk_200 [get_ports clk_200]

# pwm_in and light_load are asynchronous to clk_200 and are double-flopped
# inside the top level. Tell the tool not to time the first capture.
set_false_path -from [get_ports pwm_in]
set_false_path -from [get_ports light_load]
set_false_path -from [get_ports rst_n]

# ---- gate-drive outputs ----------------------------------------------------
# These drive the segmented output stage. Skew between slices of the same bank
# directly changes the effective drive strength, so constrain them together.
# Tighten or relax max_delay once the real board delays are known.
set_max_delay 4.000 -to [get_ports {ls_pu[*] ls_pd[*] hs_pu[*] hs_pd[*]}]
set_max_delay 4.000 -to [get_ports {ls_clamp hs_clamp vneg_sel}]

# ---- I/O standard ----------------------------------------------------------
set_property IOSTANDARD LVCMOS33 [get_ports -filter {DIRECTION == IN}]
set_property IOSTANDARD LVCMOS33 [get_ports -filter {DIRECTION == OUT}]

# ---- placeholder pin assignments -------------------------------------------
# EDIT THESE. Example values are for a Digilent Basys-3 (xc7a35tcpg236-1);
# they are here to make the flow runnable, not because they are correct for
# your board or safe to wire to a real gate driver.
# set_property PACKAGE_PIN W5  [get_ports clk_200]
# set_property PACKAGE_PIN U18 [get_ports rst_n]
# set_property PACKAGE_PIN V17 [get_ports pwm_in]
# set_property PACKAGE_PIN V16 [get_ports light_load]
