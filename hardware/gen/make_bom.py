#!/usr/bin/env python3
"""Create the purchasing BOM (CSV) from the generated design model + sourcing data.

usage: make_bom.py <model_netlist.json> <out_dir>
Writes  bom.csv        - PCB assembly BOM grouped by MPN: LCSC number, JLCPCB library type, JLCPCB / LCSC stock and
                         JLCPCB prices (live, sourcing_jlc.json), DigiKey second source (sourcing_live.json)
        bom_system.csv - everything else needed for one unit (module, speaker, screws, ...)
"""
import csv, json, re, sys, os
from collections import OrderedDict
import sourcing

def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def money(v):
    """Unit price with up to four decimals (at least two), so that quantity x unit price reproduces the extended price."""
    if v is None: return ""
    s = "%.4f" % v
    return s[:-2] if s.endswith("00") else s.rstrip("0")

def jlc(mpn):
    d = sourcing.PARTS_JLC.get(mpn)
    if d is None or "jlc_stock" not in d:
        raise SystemExit("no JLCPCB sourcing data for %s - add it to sourcing_jlc.json and run jlc_lookup.py refresh" % mpn)
    return d

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
    date_j, date_d = sourcing.JLC["checked"], sourcing.LIVE["checked"]
    hdr = ["Item", "Qty", "References", "Value", "Description", "Footprint", "Manufacturer", "MPN", "DNP",
           "LCSC Part #", "JLCPCB type", "JLCPCB stock", "LCSC stock", "JLCPCB USD @1", "JLCPCB USD @10", "JLCPCB USD @100",
           "Ext. USD @1", "Ext. USD @100", "Assembly", "DigiKey MPN (second source)", "DigiKey PN", "DigiKey status", "DigiKey stock",
           "DigiKey USD @1", "DigiKey USD @100", "Other second sources", "Sourcing note (JLCPCB/LCSC checked %s, DigiKey %s)" % (date_j, date_d)]
    rows, t1, t100, thin, types = [], 0.0, 0.0, [], {}
    for i, ((mpn, dnp), g) in enumerate(groups.items(), 1):
        d = jlc(mpn); sec, note = sourcing.second(mpn)
        p1, p10, p100 = d["jlc_p1"], d["jlc_p10"], d["jlc_p100"]
        n = 0 if dnp else len(g["refs"])
        t1 += p1 * n; t100 += p100 * n
        if not dnp:
            types[d["jlc_type"]] = types.get(d["jlc_type"], 0) + 1
            if d["jlc_stock"] < 200:
                thin.append("%s (%d)" % (mpn, d["jlc_stock"]))
        alt, dk = sourcing.digikey(mpn)
        if dk is None:
            dkrow = ["", "", "not carried / not looked up", "", "", ""]
        else:
            stock = "not shown" if dk["digikey_stock"] is None else dk["digikey_stock"]
            dkrow = [alt, dk["digikey_pn"], dk["digikey_status"], stock, money(dk["digikey_p1"]),
                     money(dk["digikey_p100"] if dk["digikey_p100"] is not None else dk["digikey_p1"])]
        rows.append([i, len(g["refs"]), " ".join(g["refs"]), g["value"], g["f"].get("PartDescription", ""), g["fp"].split(":")[1],
                     g["f"]["Manufacturer"], mpn, "DNP" if dnp else "", d["lcsc"], d["jlc_type"], d["jlc_stock"],
                     "" if d.get("lcsc_stock") is None else d["lcsc_stock"], money(p1), money(p10), money(p100),
                     "%.2f" % (p1 * n), "%.2f" % (p100 * n), d.get("assembly_process") or ""] + dkrow + [sec, note])
    with open(os.path.join(out, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
        w.writerow([]); w.writerow(["", "", "", "", "PCB assembly parts total per board (JLCPCB prices, excl. PCB, assembly fees and DNP parts)"] + [""] * 11
                                   + ["%.2f" % t1, "%.2f" % t100])
    rows2, s1, s100 = [], 0.0, 0.0
    for i, (item, qty, desc, mfr, mpn) in enumerate(sourcing.EXTRA, 1):
        d = sourcing.PARTS_LIVE.get(mpn)
        sec, note = sourcing.EXTRA_SECOND.get(mpn) or sourcing.second(mpn)
        if d is not None and d.get("digikey_p1") is not None:
            p1 = d["digikey_p1"]; p100 = d["digikey_p100"] if d["digikey_p100"] is not None else p1
            row = [d["digikey_pn"], d["digikey_status"], d["digikey_stock"], money(p1), money(p100)]
        else:
            p1 = p100 = sourcing.ESTIMATES.get(mpn, sourcing.GENERIC_PRICE)
            row = ["", "not a distributor item", "", "~" + money(p1), "~" + money(p100)]
            sec = sec or "any equivalent"; note = note or "hardware-store item, price is an estimate"
        s1 += p1 * qty; s100 += p100 * qty
        rows2.append([i, qty, item, desc, mfr, mpn] + row + ["%.2f" % (p1 * qty), "%.2f" % (p100 * qty), sec, note])
    with open(os.path.join(out, "bom_system.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Item", "Qty", "Function", "Description", "Manufacturer", "MPN", "DigiKey PN", "DigiKey status", "DigiKey stock",
                    "Unit USD @1", "Unit USD @100", "Ext. USD @1", "Ext. USD @100", "Second source",
                    "Sourcing note (DigiKey checked %s; EU shops and prices: fab/SHOPPING_LIST.md)" % date_d])
        w.writerows(rows2)
        w.writerow([]); w.writerow(["", "", "", "System parts total per unit", "", "", "", "", "", "", "", "%.2f" % s1, "%.2f" % s100])
    summary = dict(checked_jlcpcb=date_j, checked_digikey=date_d, lines=len(rows), placements=sum(r[1] for r in rows if r[8] != "DNP"),
                   pcb_parts_usd_1=round(t1, 2), pcb_parts_usd_100=round(t100, 2), system_usd_1=round(s1, 2), system_usd_100=round(s100, 2),
                   library_types=types, below_200_at_jlcpcb=thin)
    json.dump(summary, open(os.path.join(out, "bom_summary.json"), "w"), indent=1)
    print("BOM: %(lines)d lines, %(placements)d placements; PCB parts $%(pcb_parts_usd_1).2f @1 / $%(pcb_parts_usd_100).2f @100 (JLCPCB); "
          "system items $%(system_usd_1).2f @1 / $%(system_usd_100).2f @100" % summary)
    print("JLCPCB library types:", types, "| below 200 pieces:", thin or "none")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
