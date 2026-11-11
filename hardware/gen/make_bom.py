#!/usr/bin/env python3
"""Create the purchasing BOM (CSV) from the generated design model + sourcing table.

usage: make_bom.py <model_netlist.json> <out_dir>
Writes  bom.csv        - PCB assembly BOM grouped by MPN
        bom_system.csv - everything else needed for one unit (module, speaker, screws, ...)
"""
import csv, json, re, sys, os
from collections import OrderedDict
import sourcing

def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def main(model_path, out):
    model = json.load(open(model_path))
    groups = OrderedDict()
    for ref in sorted(model, key=natural):
        c = model[ref]
        f = c["fields"]
        if not c.get("in_bom", True) or not f.get("MPN"):
            continue
        key = (f["MPN"], bool(c.get("dnp")))
        g = groups.setdefault(key, dict(refs=[], value=c["value"], fp=c["footprint"], f=f))
        g["refs"].append(ref)
    hdr = ["Item", "Qty", "References", "Value", "Description", "Footprint", "Manufacturer", "MPN", "DNP",
           "Distributor", "Distributor PN", "Alt. distributor PN (Mouser)", "Unit price USD (qty 1)", "Ext. price USD",
           "Lifecycle", "Second source", "Sourcing note"]
    rows, total = [], 0.0
    for i, ((mpn, dnp), g) in enumerate(groups.items(), 1):
        s = sourcing.S.get(mpn)
        if s is None and mpn.startswith("RC0402FR-07"):
            s = sourcing.RES
        if s is None:
            raise SystemExit("no sourcing data for " + mpn)
        price = float(s[2].lstrip("~"))
        ext = 0.0 if dnp else price * len(g["refs"])
        total += ext
        rows.append([i, len(g["refs"]), " ".join(g["refs"]), g["value"], g["f"].get("PartDescription", ""), g["fp"].split(":")[1],
                     g["f"]["Manufacturer"], mpn, "DNP" if dnp else "", "DigiKey", s[0], s[1], s[2], "%.2f" % ext, s[3], s[4], s[5]])
    with open(os.path.join(out, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
        w.writerow([]); w.writerow(["", "", "", "", "PCB assembly parts total (qty 1 prices, excl. PCB)", "", "", "", "", "", "", "", "", "%.2f" % total])
    rows2, total2 = [], 0.0
    for i, (item, qty, desc, mfr, mpn) in enumerate(sourcing.EXTRA, 1):
        s = sourcing.SX.get(mpn) or sourcing.S.get(mpn) or ("n/v", "n/v", "~0.10", "generic", "any equivalent", "hardware-store item")
        price = float(s[2].lstrip("~")); total2 += price * qty
        rows2.append([i, qty, item, desc, mfr, mpn, "DigiKey", s[0], s[1], s[2], "%.2f" % (price * qty), s[3], s[4], s[5]])
    with open(os.path.join(out, "bom_system.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Item", "Qty", "Function", "Description", "Manufacturer", "MPN", "Distributor", "Distributor PN",
                    "Alt. distributor PN (Mouser)", "Unit price USD (qty 1)", "Ext. price USD", "Lifecycle", "Second source", "Sourcing note"])
        w.writerows(rows2)
        w.writerow([]); w.writerow(["", "", "", "System parts total", "", "", "", "", "", "", "%.2f" % total2])
    print("BOM: %d lines, %d placements, parts total $%.2f; system items $%.2f" %
          (len(rows), sum(r[1] for r in rows if r[8] != "DNP"), total, total2))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
