import csv, json, os, re, sys

def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def unit_price(part, qty):
    breaks = part.get("jlc_prices") or [[1, part["jlc_p1"]], [10, part["jlc_p10"]], [100, part["jlc_p100"]]]
    price = breaks[0][1]
    for start, value in breaks:
        if qty >= start:
            price = value
    return price

def main(model_path, sourcing_path, out, boards=2):
    boards = int(boards)
    model = json.load(open(model_path))
    src = json.load(open(sourcing_path))
    groups = {}
    for ref in sorted(model, key=natural):
        c = model[ref]
        mpn = c["fields"].get("MPN")
        if not c.get("in_bom", True) or not mpn or c.get("dnp"):
            continue
        groups.setdefault(mpn, []).append(ref)
    rows, sums = [], dict(needed=0.0, minimum=0.0, billed=0.0)
    machine, hand = 0, 0
    for mpn, refs in groups.items():
        part = src["parts"][mpn]
        needed = boards * len(refs)
        minimum = part.get("min_order") or 1
        loss = part.get("loss") or 0
        with_min = max(needed, minimum)
        billed = max(needed + loss, minimum)
        by_hand = part.get("assembly_mode") == "manualWeld" or part.get("assembly_process") == "THT"
        hand += by_hand
        machine += not by_hand
        sums["needed"] += needed * unit_price(part, needed)
        sums["minimum"] += with_min * unit_price(part, with_min)
        sums["billed"] += billed * unit_price(part, billed)
        rows.append([mpn, part["lcsc"], part["jlc_type"], "hand-soldered" if by_hand else "machine", len(refs), needed, minimum, loss, billed,
                     "%.4f" % unit_price(part, billed), "%.2f" % (billed * unit_price(part, billed)), part["jlc_stock"], " ".join(refs)])
    with open(os.path.join(out, "order_cost.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["MPN", "LCSC Part #", "JLCPCB type", "Placed by", "Per board", "Needed for %d boards" % boards, "Minimum quantity", "Loss quantity",
                    "Billed quantity", "Unit USD at the billed quantity", "Line USD", "JLCPCB stock", "References"])
        w.writerows(rows)
    summary = dict(checked_jlcpcb=src["checked"], boards=boards, part_types=len(rows), machine_placed_part_types=machine, hand_soldered_part_types=hand,
                   parts_usd_needed_only=round(sums["needed"], 2), parts_usd_with_minimum=round(sums["minimum"], 2),
                   parts_usd_with_minimum_and_loss=round(sums["billed"], 2),
                   stock_below_twice_the_need=[r[0] for r in rows if r[11] < 2 * r[5]],
                   stock_below_200=["%s (%d)" % (r[0], r[11]) for r in rows if r[11] < 200])
    json.dump(summary, open(os.path.join(out, "order_cost.json"), "w"), indent=1)
    print("order of %(boards)d assembled boards: %(part_types)d part types (%(machine_placed_part_types)d machine-placed, %(hand_soldered_part_types)d hand-soldered); "
          "parts $%(parts_usd_needed_only).2f needed only / $%(parts_usd_with_minimum).2f with minimum quantities / "
          "$%(parts_usd_with_minimum_and_loss).2f with minimum and loss quantities" % summary)
    print("stock below twice the need:", summary["stock_below_twice_the_need"] or "none", "| below 200 pieces:", summary["stock_below_200"] or "none")
    return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
