#!/usr/bin/env python3
"""M2 — characterisation sweep.

Generates one Spectre netlist per grid point, runs it, extracts the seven metrics,
and appends a row to data/characterisation.csv.

That CSV is the only interface between the Cadence track and the Vivado track.
Nothing downstream reads Spectre output directly.

Usage:
    python3 scripts/sweep.py --dry-run          # print the grid, run nothing
    python3 scripts/sweep.py --limit 4          # smoke test
    python3 scripts/sweep.py                    # full grid
"""
import argparse
import csv
import itertools
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "cadence" / "dpt_gan.scs"
OUTCSV = ROOT / "data" / "characterisation.csv"
WORK = ROOT / "data" / "runs"

# ------------------------------------------------------------------ the grid
# Keep this small until M1 proves the driver works. Widen once it does.
GRID = {
    "VDC":       [200, 300, 400],        # V
    "ITARGET":   [5, 10, 20],            # A
    "TJ":        [25, 75, 125],          # degC
    "STRENGTH":  [0, 1, 2, 3],           # N-bit pull-up/pull-down code
    "TDEAD":     [10e-9, 20e-9, 40e-9],  # s
    "TCLAMP":    [0, 5e-9, 10e-9],       # s, clamp assert delay after edge
}

FIELDS = ["VDC", "ITARGET", "TJ", "STRENGTH", "TDEAD", "TCLAMP",
          "vgs_peak", "vgs_undershoot", "vds_overshoot",
          "e_on", "e_off", "crosstalk_margin", "t_commutation"]


def points():
    keys = list(GRID)
    for combo in itertools.product(*(GRID[k] for k in keys)):
        yield dict(zip(keys, combo))


def netlist_for(pt, path):
    """Write a netlist with this point's parameters overridden."""
    src = TEMPLATE.read_text()
    inject = "\n".join(f"parameters {k}={v}" for k, v in pt.items()
                       if k in ("VDC", "ITARGET"))
    # STRENGTH / TDEAD / TCLAMP map onto the segmented driver once M1 exists.
    inject += (f"\nparameters STRENGTH={pt['STRENGTH']}"
               f"\nparameters TDEAD={pt['TDEAD']}"
               f"\nparameters TCLAMP={pt['TCLAMP']}"
               f"\nparameters TJ={pt['TJ']}")
    src = src.replace("// ---------------------------------------------------------------- power stage",
                      inject + "\n\n// ------------------------------- power stage")
    path.write_text(src)


def run(path):
    return subprocess.run(["spectre", str(path), "-format", "psfascii",
                           "-raw", str(path.parent / "psf")],
                          capture_output=True, text=True)


def extract(rawdir):
    """Parse the PSF output.

    NOT IMPLEMENTED until M0 passes and the real signal names are known — the
    node names depend on the vendor model's terminal order. Filling this in with
    guessed names would silently produce a CSV of wrong numbers, which is worse
    than an empty one.
    """
    raise NotImplementedError(
        "Implement after M0: read node names from the converged run first.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    pts = list(points())
    if a.limit:
        pts = pts[:a.limit]
    print(f"{len(pts)} grid points "
          f"({' x '.join(str(len(v)) for v in GRID.values())})")
    if a.dry_run:
        for p in pts[:10]:
            print("  ", p)
        if len(pts) > 10:
            print(f"   ... {len(pts)-10} more")
        return

    WORK.mkdir(parents=True, exist_ok=True)
    OUTCSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTCSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for i, pt in enumerate(pts):
            d = WORK / f"pt{i:05d}"
            d.mkdir(exist_ok=True)
            nl = d / "dpt.scs"
            netlist_for(pt, nl)
            r = run(nl)
            if r.returncode != 0:
                print(f"  pt{i:05d} FAILED\n{r.stderr[-400:]}")
                continue
            w.writerow({**pt, **extract(d / "psf")})
            fh.flush()
            print(f"  pt{i:05d} ok")


if __name__ == "__main__":
    main()
