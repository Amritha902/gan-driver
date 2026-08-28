"""
flatten.py -- inline every .include / .lib into one self-contained netlist.

The WebAssembly build of ngspice has no filesystem, so a browser-side run
needs the whole circuit in a single string.  Also strips the .control block
and emits explicit .print lines instead, since the wasm engine returns
vectors rather than writing files.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def inline(path, seen=None, depth=0):
    seen = seen or set()
    if depth > 8:
        raise RuntimeError("include nesting too deep at %s" % path)
    out = []
    base = os.path.dirname(path)
    for line in open(path):
        m = re.match(r'\s*\.(include|lib)\s+"?([^"\s]+)"?\s*(\w*)\s*$', line, re.I)
        if m:
            target = m.group(2)
            p = target if os.path.isabs(target) else os.path.normpath(os.path.join(base, target))
            if not os.path.exists(p):
                out.append("* [flatten] MISSING: %s\n" % target)
                continue
            if p in seen:
                out.append("* [flatten] already inlined: %s\n" % target)
                continue
            seen.add(p)
            out.append("* ---- begin %s ----\n" % os.path.basename(p))
            body = inline(p, seen, depth + 1)
            # a .lib file wraps content in .lib <name> ... .endl; keep the body
            out.append(body)
            out.append("* ---- end %s ----\n" % os.path.basename(p))
        else:
            out.append(line)
    return "".join(out)


def for_wasm(path, tstop=None, probes=("v(sw)", "v(lsd)", "v(lsg)", "v(hsg)")):
    s = inline(path)
    s = re.sub(r"(?is)^\.control\b.*?^\.endc\b[^\n]*\n", "", s, flags=re.M)
    s = re.sub(r"\$.*$", "", s, flags=re.M)          # ngspice inline comments
    if tstop:
        s = re.sub(r"(\.tran\s+\S+\s+)\S+", r"\g<1>%s" % tstop, s)
    s = s.replace(".end", ".print tran " + " ".join(probes) + "\n.end")
    return s


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "sim", "dpt.cir")
    tstop = sys.argv[2] if len(sys.argv) > 2 else None
    out = for_wasm(src, tstop)
    dst = os.path.join(ROOT, "results", "dpt_flat.cir")
    open(dst, "w").write(out)
    print("wrote %s (%d lines, %d KB)" % (dst, out.count("\n"), len(out) // 1024))
