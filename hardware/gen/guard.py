#!/usr/bin/env python3
import glob, hashlib, os, re, sys

MANIFEST = os.path.join("gen", "generated.sha256")
PROJECT, BOARD, PRETTY = "voxhub.kicad_pro", "voxhub.kicad_pcb", "voxhub.pretty/"

def touched(name, groups):
    return name == PROJECT or ("pcb" if name == BOARD else "sch") in groups

def digest(path):
    return hashlib.sha256(open(path, "rb").read().replace(b"\r\n", b"\n")).hexdigest()

def footprints(hw):
    return sorted(PRETTY + os.path.basename(f) for f in glob.glob(os.path.join(hw, "voxhub.pretty", "*.kicad_mod")))

def written(hw, grp):
    names = [BOARD, PROJECT]
    if grp == "sch":
        root = os.path.join(hw, "voxhub.kicad_sch")
        text = open(root, encoding="utf-8").read() if os.path.exists(root) else ""
        sheets = sorted(set(re.findall(r'\(property "Sheetfile" "([^"]+)"', text)))
        names = ["voxhub.kicad_sch"] + sheets + ["voxhub.kicad_sym", PROJECT] + footprints(hw)
    return [name for name in names if os.path.exists(os.path.join(hw, name))]

def load(hw):
    try:
        lines = open(os.path.join(hw, MANIFEST), encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return {}
    return {name: h for h, name in (line.split("  ", 1) for line in lines if line.strip())}

def save(hw, entries):
    with open(os.path.join(hw, MANIFEST), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join("%s  %s\n" % (entries[name], name) for name in sorted(entries)))

def edited(hw, entries, groups):
    found = []
    for name in sorted(entries):
        if touched(name, groups):
            path = os.path.join(hw, name)
            if not os.path.exists(path):
                found.append(("deleted", name))
            elif digest(path) != entries[name]:
                found.append(("changed", name))
    if "sch" in groups and any(name.startswith(PRETTY) for name in entries):
        found += [("added", name) for name in footprints(hw) if name not in entries]
    return sorted(found, key=lambda f: f[1])

def main():
    cmd, hw, groups = sys.argv[1], sys.argv[2], sys.argv[3:]
    entries = load(hw)
    if cmd == "record":
        entries = {name: h for name, h in entries.items() if not touched(name, groups)}
        for grp in groups:
            for name in written(hw, grp):
                entries[name] = digest(os.path.join(hw, name))
        save(hw, entries)
        return 0
    found = edited(hw, entries, groups)
    overwrite = os.environ.get("OVERWRITE", "0") == "1"
    if found:
        out = sys.stdout if overwrite else sys.stderr
        print("generated files that differ from what the last build step wrote (edited in KiCad or by hand, or a build was interrupted):", file=out)
        for what, name in found:
            print("  %-8s %s" % (what, name), file=out)
        if not overwrite:
            print("Nothing was written. Either run\n"
                  "  hardware/build.sh outputs\n"
                  "to produce the fabrication files from the project as it is now (the manual edits are kept), or set\n"
                  "  OVERWRITE=1\n"
                  "for this build step to discard the manual edits and regenerate these files from hardware/gen.", file=sys.stderr)
            return 1
        print("OVERWRITE=1: the manual edits are discarded, the files are regenerated", file=out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
