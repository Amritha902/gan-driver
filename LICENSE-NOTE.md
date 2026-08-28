# Third-party content

`cells/` and `models/` in this directory are from
**google/skywater-pdk-libs-sky130_fd_pr**, licensed **Apache-2.0**
(Copyright 2020 The SkyWater PDK Authors). Only the two 5 V I/O devices used
by this project were checked out; the upstream headers are unmodified.

`sky130_5v.lib` is our own wrapper. See its header for the one substantive
choice made: the `*_slope_spectre` mismatch multipliers are set to 0, which
is what a nominal (non-Monte-Carlo) tt run means.
