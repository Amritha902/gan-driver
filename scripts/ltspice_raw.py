"""
ltspice_raw.py -- read an LTspice binary .raw file.

Needed because the annotated figures have to be drawn from LTspice's OWN
output, not from an ngspice re-run that happens to agree. The point of the
figure is that a second simulator produced it.

LTspice writes a text header, then "Binary:\n", then interleaved samples. In a
real transient the time column is a float64 and every other column a float32,
so the stride is 8 + 4*(nvars-1) -- but some builds write everything as
float64, so the stride is worked out from the file size rather than assumed.
"""
import numpy as np


def read(path):
    with open(path, "rb") as f:
        blob = f.read()
    # LTspice on macOS writes the header as UTF-16LE, so the ASCII search for
    # "Binary:" misses entirely and every later offset is wrong. Try both.
    for tag, enc in ((u"Binary:\n".encode("utf-16-le"), "utf-16-le"),
                     (b"Binary:\n", "latin-1")):
        i = blob.find(tag)
        if i != -1:
            header = blob[:i].decode(enc, errors="ignore")
            data = blob[i + len(tag):]
            break
    else:
        raise ValueError("no Binary: marker in %s" % path)

    names, nvars, npts = [], 0, 0
    in_vars = False
    for line in header.splitlines():
        s = line.strip()
        if s.lower().startswith("no. variables:"):
            nvars = int(s.split(":")[1])
        elif s.lower().startswith("no. points:"):
            npts = int(s.split(":")[1])
        elif s.lower().startswith("variables:"):
            in_vars = True
        elif s.lower().startswith("binary"):
            in_vars = False
        elif in_vars and s:
            parts = s.split()
            if len(parts) >= 2 and parts[0].isdigit():
                names.append(parts[1])

    stride = len(data) // npts
    mixed = 8 + 4 * (nvars - 1)
    out = {}
    if stride == mixed:
        rec = np.dtype([("time", "<f8")] +
                       [("v%d" % k, "<f4") for k in range(nvars - 1)])
        arr = np.frombuffer(data[:npts * stride], dtype=rec, count=npts)
        out[names[0]] = np.abs(arr["time"])      # LTspice can sign-flip time
        for k in range(nvars - 1):
            out[names[k + 1]] = arr["v%d" % k].astype(float)
    else:
        arr = np.frombuffer(data[:npts * nvars * 8], dtype="<f8").reshape(npts, nvars)
        out[names[0]] = np.abs(arr[:, 0])
        for k in range(1, nvars):
            out[names[k]] = arr[:, k]
    return out


if __name__ == "__main__":
    import sys
    d = read(sys.argv[1])
    print("%d variables, %d points" % (len(d), len(list(d.values())[0])))
    for k in list(d)[:12]:
        print("  ", k)
