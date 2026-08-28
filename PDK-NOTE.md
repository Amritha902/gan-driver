# The SKY130 PDK is deliberately not committed

`pdk/` is 19 MB of third-party Apache-2.0 files from
google/skywater-pdk-libs-sky130_fd_pr. Fetch it with:

    git clone --depth 1 --filter=blob:none --no-checkout \
        https://github.com/google/skywater-pdk-libs-sky130_fd_pr.git pdk-src
    cd pdk-src
    git sparse-checkout init --cone
    git sparse-checkout set models cells/nfet_g5v0d10v5 cells/pfet_g5v0d10v5
    git checkout

then copy `cells/` and `models/` into `gan-driver/pdk/` alongside
`sky130_5v.lib` (which is ours and IS committed).
