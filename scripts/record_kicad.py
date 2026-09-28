# -*- coding: utf-8 -*-
"""record_kicad.py -- capture the real KiCad window with a sheet open.

    python3 scripts/record_kicad.py

The demo film used to show a cropped PNG of a KiCad export and a card that
said "KiCad". That answers the question "what drew this?" with an assertion.
This answers it with the application: eeschema is launched on a virtual X
display, the sheet is opened in it, and the screen is captured. What lands in
results/ is a photograph of the program running, toolbars and all.

    results/kicad_buck.png     kicad/gan_buck.kicad_sch open in eeschema
    results/kicad_segdrv.png   kicad/gan_segdrv.kicad_sch open in eeschema

WHY A STILL AND NOT A CLIP
  There is no xdotool, xterm or python-xlib in this container, so nothing can
  drive the GUI once it is up -- no zoom-to-fit, no scrolling, no menu opened
  on camera. A clip of a window that cannot be driven is a still with a
  timestamp on it. The film does its camera moves over these frames instead,
  which is an edit, not a re-enactment: every pixel here came off the X
  server.

WHAT IS SET UP FIRST
  KiCad asks about the global symbol library table on first run and blocks on
  that dialog forever with no way to dismiss it. The stock table is copied
  into the config directory beforehand so the question is never asked, and the
  window is set maximized so it fills the display rather than sitting in a
  1280x720 box in the corner.
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
KI = os.path.join(ROOT, "kicad")
# Shot at 2560x1440 although the film delivers 1600x900. The film pushes
# in on these frames, and a crop taken from a 1600-wide capture is being
# upscaled by three or four times by the time it reaches the Miller
# clamp -- the component labels turn to mush. Capturing half again as
# wide keeps every shot at or near native resolution.
W, H = 2560, 1440
DISPLAY = ":94"
SETTLE = 24.0          # eeschema takes ~20 s to paint on this machine

SHEETS = [("gan_buck.kicad_sch", "kicad_buck.png"),
          ("gan_segdrv.kicad_sch", "kicad_segdrv.png"),
          # The base paper's driver has a sheet of its own, generated from
          # models/zhangdrv.lib the same way ours is generated from
          # models/segdrv.lib. The film compares the two drivers, so it shows
          # both sheets in the same application rather than describing theirs.
          ("gan_zhangdrv.kicad_sch", "kicad_zhangdrv.png")]


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def kicad_config_dir():
    base = os.path.expanduser("~/.config/kicad")
    vers = sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d))) if os.path.isdir(base) else []
    if not vers:
        raise SystemExit("no ~/.config/kicad/<version> -- is KiCad installed?")
    return os.path.join(base, vers[-1])


def prepare():
    """Answer the first-run dialog in advance, and maximise the window."""
    cfg = kicad_config_dir()
    stock = "/usr/share/kicad/template/sym-lib-table"
    dest = os.path.join(cfg, "sym-lib-table")
    if os.path.exists(stock) and not os.path.exists(dest):
        shutil.copyfile(stock, dest)
    fp = os.path.join(cfg, "fp-lib-table")
    if not os.path.exists(fp):
        open(fp, "w").write("(fp_lib_table\n)\n")
    p = os.path.join(cfg, "eeschema.json")
    if os.path.exists(p):
        d = json.load(open(p))
        w = d.setdefault("window", {})
        w.update(maximized=True, pos_x=0, pos_y=0, size_x=W, size_y=H)
        json.dump(d, open(p, "w"), indent=2)
    return cfg


def capture(sheet, out):
    env = dict(os.environ, DISPLAY=DISPLAY)
    x = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "%dx%dx24" % (W, H)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ee = None
    try:
        time.sleep(3)
        ee = subprocess.Popen(["eeschema", os.path.join(KI, sheet)], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(SETTLE)
        rc = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error",
                             "-f", "x11grab", "-video_size", "%dx%d" % (W, H),
                             "-i", DISPLAY, "-frames:v", "1", "-y",
                             os.path.join(RES, out)], env=env).returncode
        if rc != 0 or not os.path.exists(os.path.join(RES, out)):
            raise SystemExit("x11grab failed for %s" % sheet)
    finally:
        for p in (ee, x):
            if p is not None:
                p.terminate()
                try:
                    p.wait(timeout=10)
                except Exception:
                    p.kill()
        # eeschema writes ~<sheet>.lck beside the file it opens and only
        # removes it on a clean quit. Terminating it is not a clean quit, so
        # two lock files were left in kicad/ and staged for commit.
        lck = os.path.join(KI, "~" + sheet + ".lck")
        if os.path.exists(lck):
            os.remove(lck)
    # A window that never painted gives a near-black frame; that would ship as
    # "the software" without anyone noticing until the review.
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(os.path.join(RES, out)).convert("L"))
    if float(a.mean()) < 40:
        raise SystemExit("%s came out almost black -- eeschema did not paint "
                         "within %.0f s" % (out, SETTLE))
    print("  %-22s -> results/%s   (mean luminance %.0f)"
          % (sheet, out, a.mean()))


def main():
    for t in ("Xvfb", "eeschema"):
        if not shutil.which(t):
            raise SystemExit("%s is not on PATH" % t)
    prepare()
    for sheet, out in SHEETS:
        capture(sheet, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
