# Running Vivado in the cloud

Vivado needs **x86-64 Linux or Windows**. A cloud VM gives you that without a lab booking.

## What to rent

| | |
|---|---|
| Instance | AWS `t3.xlarge` / Azure `D4s v5` — 4 vCPU, 16 GB RAM |
| OS | Ubuntu 22.04 LTS, **x86-64** (not ARM — `t4g`/`Dpsv5` will not work) |
| Disk | **150 GB** — Vivado is ~100 GB installed, the installer needs headroom |
| Cost | ~US$0.17/hr. **Stop the instance when idle** — you pay for it running, not for use |

Budget roughly **₹300–500** for all the synthesis this project needs.

## Install

```bash
# on the VM
sudo apt update && sudo apt install -y libtinfo5 libncurses5 libx11-6 xvfb git
```

Vivado ML **Standard** Edition is free and needs no licence for Zynq-7000. Download from
AMD (free account required, ~50 GB), then:

```bash
chmod +x FPGAs_AdaptiveSoCs_Unified_*.bin
./FPGAs_AdaptiveSoCs_Unified_*.bin --nogui --agree XilinxEULA,3rdPartyEULA \
    --edition "Vivado ML Standard" --product Vivado --location /opt/Xilinx
```

**Select only the Zynq-7000 device family during install.** Everything else triples the size.

## Run synthesis headless — no GUI, no X forwarding

```bash
source /opt/Xilinx/Vivado/*/settings64.sh
cd gan-dab-project
vivado -mode batch -source cloud/synth.tcl
```

That writes `cloud/utilisation.rpt` and `cloud/timing.rpt` — the two files Review 1 needs.

## Getting the repo there

```bash
# from your Mac
rsync -av --exclude .git ~/gan-dab-project/ ubuntu@<vm-ip>:~/gan-dab-project/
# afterwards, pull the reports back
rsync -av ubuntu@<vm-ip>:~/gan-dab-project/cloud/*.rpt ~/gan-dab-project/cloud/
```

## Honest comparison

| | Lab PC | Cloud VM |
|---|---|---|
| Setup | 0 — already installed | 2–3 h first time (mostly downloading) |
| Cost | free | ~₹400 |
| ADS as well | yes, if licensed | **no — ADS needs a licence you do not have** |

**Recommendation:** use the lab PC if you can book it, because it also solves ADS. Use the
cloud only for Vivado, and only if lab access is blocking you. The cloud does not solve ADS —
that licence is the real constraint, not the CPU.

---

## Caveat

`synth.tcl` has **not been run** — Vivado does not exist on the Mac it was written on. The
syntax is checked and the commands are standard Vivado, but expect to fix a path the first
time. If `$readmemh` cannot find `pareto_table.mem`, that is the line to look at.
