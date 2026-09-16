# -*- coding: utf-8 -*-
"""device_mc.py -- does the result survive DEVICE-TO-DEVICE variation?

    python3 scripts/device_mc.py            # run / resume
    python3 scripts/device_mc.py --analyse  # report on what exists

THE GAP THIS CLOSES
robust.py already perturbs device parameters ONE AT A TIME: Vth high, then
Vth low, then Cgs high, and so on. That answers "is the ceiling sensitive to
each parameter separately". It cannot answer the question a manufacturer
actually faces, which is what happens when every parameter is off nominal AT
ONCE, in whatever combination the process hands you.

Until now every headline number in this project rested on one device: a
single nominal egan.lib. The deck says so under its own limits. This samples
devices jointly and asks whether the conclusions hold across the population.

WHAT IS SAMPLED, AND ON WHAT AUTHORITY
Four terminal parameters, jointly and independently, each truncated Gaussian:

    vth   1.4  V     threshold
    bh    5.55       transconductance
    cgs   350 pF     input capacitance
    CJO   150 pF     zero-bias C_gd -- the crosstalk path itself

Sigma is set so that +-3 sigma reproduces the bounds robust.py already uses
for its one-at-a-time cases (e.g. Vth 1.12-1.68), and samples are truncated
there. That keeps this study on the same footing as the existing one instead
of inventing a new spread. Loop inductance is NOT varied: it is board layout,
not the device, and lloop_sweep.py already owns it.

Independence is an assumption and a conservative one for this purpose:
real process variation correlates Vth with transconductance, which would
narrow the spread rather than widen it.

WHAT IS MEASURED PER DEVICE
  margin_shipped   crosstalk margin of the shipped word, worst over corners.
                   Negative anywhere = that device false-turns-on. A safety
                   claim, so the worst case is the only one that matters.
  A, B             the decomposition, recomputed on that device.

WORD SET
Evaluating 720 words x 4 corners per device is 2,880 transients per sample,
which is not affordable for a population. This uses a fixed candidate set:
every word that is optimal at some corner on the nominal device, the shipped
word, the conventional word, plus a stratified sample of the grid. The set is
identical for every device, so devices are compared like with like. A subset
can only raise the best fixed word's cost, which deflates (A) and inflates
(B): the ordering test is therefore conservative, handicapping the claim it
checks. These figures are not comparable to the deck's 25.1 / 3.9, which are
full-grid, and the report says so.
"""
import csv, gzip, itertools, json, os, random, re, subprocess, sys, tempfile, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "device_mc.csv")
CKPT = os.path.join(ROOT, "results", "device_mc.ckpt.json")

N_DEVICES = 24
SEED      = 20260916
W_OV      = 0.05
VTH_NOM   = 1.4

# nominal, low, high  -- low/high are robust.py's one-at-a-time bounds, used
# here as +-3 sigma and as truncation limits.
SPREAD = {
    "vth":  (1.4,   1.12,  1.68),
    "bh":   (5.55,  3.9,   7.2),
    "cgs":  (350.0, 245.0, 455.0),   # pF
    "CJO":  (150.0, 75.0,  225.0),   # pF
}

CORNERS = [(50, 2, 25), (100, 10, 25), (200, 10, 125), (200, 2, 125)]

SHIPPED      = dict(NPU_LS=8, NPD_LS=8, NPD_HS=1, DT="25n", CLKEN=1, VNEG=-2)
CONVENTIONAL = dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=0, VNEG=0)


def candidate_words(n_extra=34):
    """Same set for every device, so devices are comparable."""
    grid = dict(NPU_LS=[1, 2, 3, 4, 6, 8], NPD_LS=[2, 8], NPD_HS=[1, 4, 8],
                DT=["5n", "10n", "15n", "25n", "35n"], CLKEN=[0, 1], VNEG=[0, -2])
    keys = list(grid)
    allw = [dict(zip(keys, v)) for v in itertools.product(*(grid[k] for k in keys))]
    rng = random.Random(SEED)
    # Stratify on the two fields the study says matter: dead time and off-bias.
    buckets = {}
    for w in allw:
        buckets.setdefault((w["DT"], w["VNEG"]), []).append(w)
    picked, keyring = [], sorted(buckets)
    i = 0
    while len(picked) < n_extra:
        b = buckets[keyring[i % len(keyring)]]
        w = rng.choice(b)
        if w not in picked:
            picked.append(w)
        i += 1
    out = [SHIPPED, CONVENTIONAL] + picked
    seen, uniq = set(), []
    for w in out:
        k = tuple(sorted(w.items()))
        if k not in seen:
            seen.add(k); uniq.append(w)
    return uniq


def sample_devices(n):
    rng = random.Random(SEED)
    devs = []
    for i in range(n):
        d = {"dev": i}
        for k, (nom, lo, hi) in SPREAD.items():
            sigma = (hi - nom) / 3.0
            while True:
                v = rng.gauss(nom, sigma)
                if lo <= v <= hi:
                    break
            d[k] = v
        devs.append(d)
    return devs


BASE = None


def build_base():
    global BASE
    src = open(os.path.join(ROOT, "sim", "dpt.cir")).read()
    for lib in ("egan.lib", "segdrv.lib"):
        p = os.path.join(ROOT, "models", lib)
        src = src.replace(".include ../models/%s" % lib, open(p).read())
    BASE = src


def job(a):
    dev, word, (vb, il, tj) = a
    src = BASE
    subs = {"vth=1.4": "vth=%.5f" % dev["vth"],
            "bh=5.55": "bh=%.5f" % dev["bh"],
            "cgs=350p": "cgs=%.3fp" % dev["cgs"],
            "CJO=150p": "CJO=%.3fp" % dev["CJO"]}
    for old, new in subs.items():
        if old not in src:
            return {"dev": dev["dev"], "error": "no substitution %r" % old}
        src = src.replace(old, new)
    p = dict(gansim.DEFAULTS)
    p.update(word); p.update(VBUS=vb, ILOAD=il, TJ=tj)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in p.items())
    src = re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                 lambda m: m.group(1) + block + "\n" + m.group(2), src)
    d = tempfile.mkdtemp(prefix="mc_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=300)
        f = os.path.join(d, "out.dat")
        # A deck that fails to load its models still exits zero and writes a
        # stub out.dat. gansim.run guards on size for exactly that reason;
        # without this guard every row comes back blank and the run looks fine.
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return {"dev": dev["dev"], "error": "no/short out.dat"}
        import numpy as np
        m = gansim.metrics(np.loadtxt(f), p)
        row = {"dev": dev["dev"], "VBUS": vb, "ILOAD": il, "TJ": tj}
        row.update({k: word[k] for k in word})
        for k in ("E_tot", "ov_pct", "margin", "Vgs_spur_hs"):
            row[k] = m.get(k)
        return row
    except Exception as e:
        return {"dev": dev["dev"], "error": repr(e)[:90]}
    finally:
        import shutil; shutil.rmtree(d, ignore_errors=True)


def main():
    build_base()
    devs  = sample_devices(N_DEVICES)
    words = candidate_words()
    done = set()
    rows = []
    if os.path.exists(OUT):
        with open(OUT) as f:
            for r in csv.DictReader(f):
                rows.append(r); done.add(int(r["dev"]))
    print("devices %d (%d already done), words %d, corners %d"
          % (len(devs), len(done), len(words), len(CORNERS)), flush=True)
    todo = [d for d in devs if d["dev"] not in done]
    if not todo:
        print("nothing to do"); return
    t0 = time.time()
    fields = ["dev", "VBUS", "ILOAD", "TJ", "NPU_LS", "NPD_LS", "NPD_HS",
              "DT", "CLKEN", "VNEG", "E_tot", "ov_pct", "margin", "Vgs_spur_hs"]
    new = not os.path.exists(OUT)
    fh = open(OUT, "a", newline="")
    wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    if new:
        wr.writeheader()
    for di, dev in enumerate(todo):
        jobs = [(dev, w, c) for w in words for c in CORNERS]
        bad = 0
        with Pool(4) as pool:
            for r in pool.imap_unordered(job, jobs, chunksize=4):
                if "error" in r:
                    bad += 1; continue
                wr.writerow(r)
        fh.flush()
        el = time.time() - t0
        print("  device %2d/%2d done  failed=%d  %.0fs elapsed  eta %.0fs"
              % (di + 1, len(todo), bad, el, el / (di + 1) * (len(todo) - di - 1)),
              flush=True)
        json.dump({"done": di + 1}, open(CKPT, "w"))
    fh.close()
    print("wrote %s" % OUT)


if __name__ == "__main__":
    if "--analyse" in sys.argv:
        import device_mc_analyse  # noqa
    else:
        main()
