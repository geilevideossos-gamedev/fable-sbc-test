import glob, hashlib, os, re, sys

MANIFEST = os.path.join("gen", "generated.sha256")
SETTINGS = os.path.join("gen", "project_settings.json")
ROOT, LIBRARY = "voxhub.kicad_sch", "voxhub.kicad_sym"
PROJECT, BOARD, PRETTY = "voxhub.kicad_pro", "voxhub.kicad_pcb", "voxhub.pretty/"
GROUPS = {"sch": ("sheets", "footprints", "project"), "pcb": ("board", "project"),
          "sheets": ("sheets",), "footprints": ("footprints",), "project": ("project",)}
LINE = re.compile(r"[0-9a-f]{64}  \S.*")
FONTS = b"\t(embedded_fonts no)\n)\n"
STEP = "build step "
STEPS = {"sch": "build.sh sch", "pcb": "build.sh pcb or route"}
LATE = "The step was stopped: the files it had already regenerated stay as they are."

def part(name):
    return "project" if name == PROJECT else "board" if name == BOARD else "footprints" if name.startswith(PRETTY) else "sheets"

def digests(path):
    forms = [open(path, "rb").read().replace(b"\r\n", b"\n")]
    if os.path.basename(path) == ROOT and forms[0].endswith(b")\n"):
        forms.append(forms[0][:-len(FONTS)] + b")\n" if forms[0].endswith(FONTS) else forms[0][:-2] + FONTS)
    return [hashlib.sha256(form).hexdigest() for form in forms]

def digest(path):
    return digests(path)[0]

def footprints(hw):
    return sorted(PRETTY + os.path.basename(f) for f in glob.glob(os.path.join(hw, "voxhub.pretty", "*.kicad_mod")))

def sheets(hw):
    root = os.path.join(hw, ROOT)
    if not os.path.exists(root):
        return sorted(os.path.basename(f) for f in glob.glob(os.path.join(hw, "*.kicad_sch"))) + [LIBRARY]
    text = open(root, encoding="utf-8", errors="replace").read()
    return [ROOT] + sorted(set(re.findall(r'\(property "Sheetfile" "([^"]+)"', text))) + [LIBRARY]

def written(hw, prt):
    names = sheets(hw) if prt == "sheets" else footprints(hw) if prt == "footprints" else [PROJECT if prt == "project" else BOARD]
    return [name for name in names if os.path.exists(os.path.join(hw, name))]

def load(hw):
    try:
        lines = open(os.path.join(hw, MANIFEST), encoding="utf-8", errors="replace").read().splitlines()
    except FileNotFoundError:
        return {}, set()
    entries, steps = {}, set()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if not LINE.fullmatch(line):
            sys.exit("%s line %d is not of the form \"<SHA-256 sum>  <file name>\" (64 hex digits, two spaces, name): nothing was written, "
                     "repair the line or restore the file from Git." % (MANIFEST.replace(os.sep, "/"), number))
        if line[66:].startswith(STEP):
            steps.add(line[66 + len(STEP):])
        else:
            entries[line[66:]] = line[:64]
    return entries, steps

def save(hw, entries, steps):
    path = os.path.join(hw, MANIFEST)
    lines = ["%s  %s\n" % (entries[name], name) for name in sorted(entries)] + ["%s  %s%s\n" % (64 * "0", STEP, grp) for grp in sorted(steps)]
    with open(path + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(lines))
    os.replace(path + ".tmp", path)

def edited(hw, entries, parts):
    found = {}
    for name in entries:
        if part(name) in parts:
            path = os.path.join(hw, name)
            if not os.path.exists(path):
                found[name] = "deleted"
            elif entries[name] not in digests(path):
                found[name] = "changed"
    known = any(part(name) == "footprints" for name in entries)
    for prt in parts:
        for name in written(hw, prt):
            if name not in entries:
                found[name] = "added" if prt == "footprints" and known else "not recorded"
    return sorted(found.items())

def record(hw, entries, steps, parts):
    for prt in parts:
        if prt == "project":
            pro, settings = os.path.join(hw, PROJECT), os.path.join(hw, SETTINGS)
            if os.path.exists(pro) and os.path.exists(settings) and digest(pro) == digest(settings):
                entries[PROJECT] = digest(pro)
            continue
        for name in [name for name in entries if part(name) == prt]:
            del entries[name]
        for name in written(hw, prt):
            entries[name] = digest(os.path.join(hw, name))
    save(hw, entries, steps)

def main():
    cmd, hw, groups = sys.argv[1], sys.argv[2], sys.argv[3:]
    parts = sorted(set(prt for grp in groups for prt in GROUPS[grp]))
    entries, steps = load(hw)
    if cmd == "record":
        record(hw, entries, steps, parts)
        return 0
    if cmd == "finish":
        save(hw, entries, steps - set(groups))
        return 0
    locks = sorted(os.path.basename(f) for f in glob.glob(os.path.join(hw, "~*.lck")))
    state = LATE if cmd == "recheck" else "Nothing was written."
    if locks:
        print("KiCad has the project open: lock file%s %s.\n"
              "%s Close KiCad (project manager, schematic editor and board editor) before a generating step\n"
              "(build.sh sch, pcb, route, all); OVERWRITE=1 does not skip this stop. \"hardware/build.sh outputs\" may run while\n"
              "they are open. A lock file left behind by a crash of KiCad or by a killed build can be deleted."
              % ("s" if len(locks) > 1 else "", ", ".join("hardware/" + name for name in locks), state), file=sys.stderr)
        return 1
    found = edited(hw, entries, parts)
    if cmd in ("ready", "start"):
        found += [(STEPS[grp], "unfinished") for grp in groups if grp in steps]
    overwrite = os.environ.get("OVERWRITE", "0") == "1"
    if found:
        out = sys.stdout if overwrite else sys.stderr
        print("generated files that differ from what the last build step wrote (edited in KiCad or by hand, or a build was interrupted):", file=out)
        for name, what in found:
            print("  %-8s %s" % (what, name), file=out)
        if any(what == "not recorded" for name, what in found):
            print("(not recorded: the file exists and %s has no line for it)" % MANIFEST.replace(os.sep, "/"), file=out)
        if any(what == "unfinished" for name, what in found):
            print("(unfinished: the last run of that step was stopped, or one of its generator commands failed, before it had written all its files)", file=out)
        if not overwrite:
            print(state + (" The files listed above were not touched." if cmd == "recheck" else "") + " Either run\n"
                  "  hardware/build.sh outputs\n"
                  "to produce the fabrication files from the project as it is now (the manual edits are kept), or set\n"
                  "  OVERWRITE=1\n"
                  "for this build step to discard the manual edits and regenerate these files from hardware/gen.", file=sys.stderr)
            return 1
        print("OVERWRITE=1: the manual edits are discarded, the files are regenerated", file=out)
    if cmd == "start":
        save(hw, entries, steps | set(groups))
    return 0

if __name__ == "__main__":
    sys.exit(main())
