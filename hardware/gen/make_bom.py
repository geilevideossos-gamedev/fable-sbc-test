#!/usr/bin/env python3
"""Create the purchasing BOM (CSV) from the generated design model + sourcing data.

usage: make_bom.py <model_netlist.json> <out_dir>
Writes  bom.csv        - PCB assembly BOM grouped by MPN (DigiKey live data: status, stock, price @1 / @100)
        bom_system.csv - everything else needed for one unit (module, speaker, screws, ...)
"""
import csv, json, re, sys, os
from collections import OrderedDict
import sourcing

def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def money(v):
    return "" if v is None else ("%.4f" % v).rstrip("0").rstrip(".") if v < 0.1 else "%.2f" % v

def live(mpn):
    d = sourcing.PARTS_LIVE.get(mpn)
    if d is None:
        raise SystemExit("no live sourcing data for " + mpn)
    return d

def mouser(d):
    if not d.get("mouser_pn") and d.get("mouser_stock") is None and d.get("mouser_p1") is None:
        return "", "not retrievable (mouser.com blocks automated access)"
    bits = []
    if d.get("mouser_stock") is not None: bits.append("stock %s" % d["mouser_stock"])
    if d.get("mouser_p1") is not None: bits.append("%s USD @1" % money(d["mouser_p1"]))
    if d.get("mouser_p100") is not None: bits.append("%s USD @100" % money(d["mouser_p100"]))
    return d.get("mouser_pn") or "", ("; ".join(bits) + " - " if bits else "") + "search snippet, NOT live"

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
    date = sourcing.LIVE["checked"]
    hdr = ["Item", "Qty", "References", "Value", "Description", "Footprint", "Manufacturer", "MPN", "DNP",
           "DigiKey PN", "DigiKey status", "DigiKey stock", "Unit USD @1", "Unit USD @100", "Ext. USD @1", "Ext. USD @100",
           "Mouser PN", "Mouser data", "Second source", "Sourcing note (checked %s)" % date]
    rows, t1, t100 = [], 0.0, 0.0
    for i, ((mpn, dnp), g) in enumerate(groups.items(), 1):
        d = live(mpn); sec, note = sourcing.second(mpn)
        p1 = d["digikey_p1"]; p100 = d["digikey_p100"] if d["digikey_p100"] is not None else p1
        n = 0 if dnp else len(g["refs"])
        t1 += p1 * n; t100 += p100 * n
        mpn_m, mdata = mouser(d)
        stock = "not shown" if d["digikey_stock"] is None else d["digikey_stock"]
        rows.append([i, len(g["refs"]), " ".join(g["refs"]), g["value"], g["f"].get("PartDescription", ""), g["fp"].split(":")[1],
                     g["f"]["Manufacturer"], mpn, "DNP" if dnp else "", d["digikey_pn"], d["digikey_status"], stock,
                     money(p1), money(p100), "%.2f" % (p1 * n), "%.2f" % (p100 * n), mpn_m, mdata, sec, note])
    with open(os.path.join(out, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
        w.writerow([]); w.writerow(["", "", "", "", "PCB assembly parts total per board (DigiKey, excl. PCB and DNP parts)", "", "", "", "", "", "", "", "", "",
                                    "%.2f" % t1, "%.2f" % t100])
    rows2, s1, s100 = [], 0.0, 0.0
    for i, (item, qty, desc, mfr, mpn) in enumerate(sourcing.EXTRA, 1):
        d = sourcing.PARTS_LIVE.get(mpn)
        sec, note = sourcing.EXTRA_SECOND.get(mpn) or sourcing.second(mpn)
        if d is not None and d.get("digikey_p1") is not None:
            p1 = d["digikey_p1"]; p100 = d["digikey_p100"] if d["digikey_p100"] is not None else p1
            mpn_m, mdata = mouser(d)
            row = [d["digikey_pn"], d["digikey_status"], d["digikey_stock"], money(p1), money(p100)]
        else:
            p1 = p100 = sourcing.ESTIMATES.get(mpn, sourcing.GENERIC_PRICE)
            mpn_m, mdata = "", ""
            row = ["", "not a distributor item", "", "~" + money(p1), "~" + money(p100)]
            sec = sec or "any equivalent"; note = note or "hardware-store item, price is an estimate"
        s1 += p1 * qty; s100 += p100 * qty
        rows2.append([i, qty, item, desc, mfr, mpn] + row + ["%.2f" % (p1 * qty), "%.2f" % (p100 * qty), mpn_m, mdata, sec, note])
    with open(os.path.join(out, "bom_system.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Item", "Qty", "Function", "Description", "Manufacturer", "MPN", "DigiKey PN", "DigiKey status", "DigiKey stock",
                    "Unit USD @1", "Unit USD @100", "Ext. USD @1", "Ext. USD @100", "Mouser PN", "Mouser data", "Second source",
                    "Sourcing note (checked %s)" % date])
        w.writerows(rows2)
        w.writerow([]); w.writerow(["", "", "", "System parts total per unit", "", "", "", "", "", "", "", "%.2f" % s1, "%.2f" % s100])
    summary = dict(checked=date, lines=len(rows), placements=sum(r[1] for r in rows if r[8] != "DNP"),
                   pcb_parts_usd_1=round(t1, 2), pcb_parts_usd_100=round(t100, 2), system_usd_1=round(s1, 2), system_usd_100=round(s100, 2))
    json.dump(summary, open(os.path.join(out, "bom_summary.json"), "w"), indent=1)
    print("BOM: %(lines)d lines, %(placements)d placements; PCB parts $%(pcb_parts_usd_1).2f @1 / $%(pcb_parts_usd_100).2f @100; "
          "system items $%(system_usd_1).2f @1 / $%(system_usd_100).2f @100" % summary)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
