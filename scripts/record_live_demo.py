"""
record_live_demo.py -- record the LIVE demo actually running.

Slide 14 offers to run the simulation in the room. That offer needs a
fallback, because a laptop in a review room is not a controlled environment:
if the live run does not start, the presenter should have a recording of the
SAME command working rather than a different artefact to explain.

results/demo_full.mp4 is not that. It is a five-act film with typed-on code
and rendered terminal panes -- an explanation of the project. This is a
screen recording of one command: what proof/LIVE-SIM.sh prints, in the order
it prints it, at the speed it prints it.

The timing is real. Output lines are captured with the wall-clock time they
were emitted, and the recording replays them at those times -- including the
3.7 s pause while ngspice solves, which is the part a sceptic is watching
for. Nothing is sped up.

    python3 scripts/record_live_demo.py

Writes results/live_demo_recording.mp4.
"""
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "live_demo_recording.mp4")

W, H, FPS = 1600, 900, 25
BG, INK, DIM = (12, 12, 12), (232, 232, 228), (128, 128, 122)
GRN, RED, YEL, BLU = (94, 200, 130), (224, 90, 90), (222, 180, 90), (110, 160, 235)
PAD, LH = 56, 30


def mono(px, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf"
              % ("-Bold" if bold else ""),
              "/usr/share/fonts/truetype/liberation/LiberationMono-%s.ttf"
              % ("Bold" if bold else "Regular")):
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


F, FB = mono(21), mono(21, True)


def colour_for(line):
    s = line.strip()
    if "SHOOT-THROUGH" in s or s.startswith("(a)"):
        return RED if "SHOOT" in s else YEL
    if "SAFE" in s or s.startswith("(b)"):
        return GRN if "SAFE" in s else YEL
    if s.startswith("---") or s.startswith("machine") or s.startswith("spice") \
       or s.startswith("circuit") or s.startswith("changing"):
        return DIM
    if "on the slide" in s or "this run" in s:
        return BLU
    return INK


def capture():
    """Run the demo, keeping each line with the second it appeared."""
    print("  running the live demo and timing its output ...")
    t0 = time.time()
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "live_demo.py")],
                         cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1,
                         env=dict(os.environ, NO_COLOR="1", PYTHONUNBUFFERED="1"))
    lines = []
    for ln in p.stdout:
        lines.append((time.time() - t0, ln.rstrip("\n")))
        print("    %6.2fs  %s" % lines[-1])
    p.wait()
    return lines, time.time() - t0


def frames_for(lines, total):
    """One frame per tick; a line appears on the frame its timestamp falls in."""
    head = mono(26, True)
    n = int((total + 3.0) * FPS)                 # 3 s hold on the finished screen
    out = []
    for k in range(n):
        t = k / float(FPS)
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        d.text((PAD, 26), "$ bash proof/LIVE-SIM.sh", font=head, fill=GRN)
        d.text((W - PAD - 190, 32), "%5.1f s" % min(t, total), font=F, fill=DIM)
        y = 82
        for ts, ln in lines:
            if ts > t:
                break
            if y > H - PAD:
                break
            d.text((PAD, y), ln[:104], font=FB if "SHOOT" in ln or "SAFE" in ln else F,
                   fill=colour_for(ln))
            y += LH
        # a cursor while the run is still going
        if t < total and int(t * 2) % 2 == 0:
            d.rectangle([PAD, y + 6, PAD + 11, y + 22], fill=DIM)
        out.append(im)
    return out


def plot_frames(secs=5.0):
    """End on the waveform the run just drew."""
    p = os.path.join(RES, "live_run.png")
    if not os.path.exists(p):
        return []
    im = Image.open(p).convert("RGB")
    sc = min((W - 2 * PAD) / im.width, (H - 2 * PAD) / im.height)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), BG)
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    return [canvas] * int(secs * FPS)


def encode(frames, path):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
           "-movflags", "+faststart", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in frames:
        p.stdin.write(np.asarray(f, dtype=np.uint8).tobytes())
    p.stdin.close()
    return p.wait()


def main():
    lines, total = capture()
    if not lines:
        raise SystemExit("the demo produced no output")
    fr = frames_for(lines, total) + plot_frames()
    print("  %d frames, %.1f s at %d fps (the run itself took %.1f s)"
          % (len(fr), len(fr) / float(FPS), FPS, total))
    rc = encode(fr, OUT)
    print("  %s: %s (%.1f MB)" % ("written" if rc == 0 else "ffmpeg FAILED",
                                  OUT, os.path.getsize(OUT) / 1e6 if rc == 0 else 0))
    return rc


if __name__ == "__main__":
    sys.exit(main())
