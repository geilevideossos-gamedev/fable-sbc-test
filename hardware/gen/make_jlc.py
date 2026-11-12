#!/usr/bin/env python3
import csv, json, math, os, re, sys
import pcbnew

def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c + p[1] * s, -p[0] * s + p[1] * c)

def place(e, deg, bottom):
    return rot((-e[0], e[1]), -deg) if bottom else rot(e, deg)

def board_pads(fp):
    f = pcbnew.ToMM
    groups = {}
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.GetNumber():
            continue
        if not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)):
            continue
        b = p.GetBoundingBox()
        groups.setdefault(p.GetNumber(), []).append((f(b.GetWidth()) * f(b.GetHeight()), f(b.GetLeft() + b.GetRight()) / 2, f(b.GetTop() + b.GetBottom()) / 2))
    out, multi = {}, set()
    for num, lst in groups.items():
        a = max(lst)
        big = [g for g in lst if g[0] > 0.6 * a[0]]
        if len(big) > 1:
            multi.add(num)
        out[num] = (sum(g[1] for g in big) / len(big), sum(g[2] for g in big) / len(big))
    return out, multi

def easyeda_pads(rec):
    groups = {}
    for num, x, y, w, h in rec["pads"]:
        groups.setdefault(str(num), []).append((x, y))
    multi = {n for n, l in groups.items() if len(l) > 1}
    return {n: (sum(q[0] for q in l) / len(l), sum(q[1] for q in l) / len(l)) for n, l in groups.items()}, multi

SYMMETRIC_PARTS = {"CM4_J1_DF40C-100DS", "CM4_J2_DF40C-100DS", "SW_DPDT_CK_JS202011JCQN"}
PLUS = {"+", "A", "ANODE", "P", "POSITIVE"}
MINUS = {"-", "K", "C", "CATHODE", "N", "NEGATIVE"}

def polarity_swap(kind, rec):
    names = {n: str(v).strip().upper() for n, v in (rec.get("pins") or {}).items()}
    if kind is None or "1" not in names or "2" not in names:
        return None
    e1 = "plus" if names["1"] in PLUS else ("minus" if names["1"] in MINUS else None)
    e2 = "plus" if names["2"] in PLUS else ("minus" if names["2"] in MINUS else None)
    if (e1 is None or e2 is None or e1 == e2) and rec.get("plus_pin") in ("1", "2"):
        e1, e2 = ("plus", "minus") if rec["plus_pin"] == "1" else ("minus", "plus")
    if e1 is None or e2 is None or e1 == e2:
        return None
    k1 = "minus" if kind == "diode" else "plus"
    return e1 != k1

def fit_numbered(kp, ep, bottom, base, mapping):
    out = []
    for d in (0, 90, 180, 270):
        ang = (base + d) % 360
        tr = [(k, place(ep[e], ang, bottom)) for k, e in mapping]
        tx = sum(kp[k][0] - t[0] for k, t in tr) / len(tr)
        ty = sum(kp[k][1] - t[1] for k, t in tr) / len(tr)
        res = max(math.hypot(kp[k][0] - t[0] - tx, kp[k][1] - t[1] - ty) for k, t in tr)
        out.append((res, ang, tx, ty))
    out.sort()
    return out

def fit_geometric(kp, ep, bottom, base):
    kpts, epts = list(kp.values()), list(ep.values())
    out = []
    for d in (0, 90, 180, 270):
        ang = (base + d) % 360
        tr = [place(e, ang, bottom) for e in epts]
        best = None
        for t0 in tr[:6]:
            for k0 in kpts:
                tx, ty = k0[0] - t0[0], k0[1] - t0[1]
                for _ in range(3):
                    pairs = []
                    for t in tr:
                        k = min(kpts, key=lambda k_: math.hypot(k_[0] - t[0] - tx, k_[1] - t[1] - ty))
                        dd = math.hypot(k[0] - t[0] - tx, k[1] - t[1] - ty)
                        if dd <= 0.45:
                            pairs.append((k, t))
                    if len(pairs) < 2:
                        break
                    tx = sum(k[0] - t[0] for k, t in pairs) / len(pairs)
                    ty = sum(k[1] - t[1] for k, t in pairs) / len(pairs)
                if len(pairs) < 2:
                    continue
                res = max(math.hypot(k[0] - t[0] - tx, k[1] - t[1] - ty) for k, t in pairs)
                hit = len({k for k, t in pairs})
                key = (-hit, res)
                if best is None or key < best[0]:
                    best = (key, res, tx, ty, hit)
        if best is None:
            out.append((9.9, ang, 0.0, 0.0)); continue
        missing = min(len(kpts), len(epts)) - best[4]
        out.append((best[1] + 0.5 * max(0, missing - max(1, int(0.3 * min(len(kpts), len(epts))))), ang, best[2], best[3]))
    out.sort()
    return out

def solve(fp, rec, kind):
    bottom = fp.IsFlipped()
    base = round(fp.GetOrientationDegrees()) % 360
    (kp, kmulti), (ep, emulti) = board_pads(fp), easyeda_pads(rec)
    common = sorted(set(kp) & set(ep))
    single = [n for n in common if n not in kmulti and n not in emulti]
    note, method, cands = "", "", None
    two_pin = len(kp) == 2 and len(ep) == 2
    if len(kp) == 1 or len(ep) == 1:
        k0, e0 = next(iter(kp.values())), place(next(iter(ep.values())), base, bottom)
        return dict(rotation=base, x=k0[0] - e0[0], y=k0[1] - e0[1], residual=0.0, method="single pad", note="", pads=(len(kp), len(ep)), two_pin=False)
    if two_pin and common == ["1", "2"]:
        swap = polarity_swap(kind, rec)
        mapping = [("1", "2"), ("2", "1")] if swap else [("1", "1"), ("2", "2")]
        cands = fit_numbered(kp, ep, bottom, base, mapping)
        method = "pad numbers" + ("" if kind is None else (", terminals swapped by pin name" if swap else (", pin names agree" if swap is False else ", pin names not conclusive")))
        if kind is not None and swap is None:
            note = "polarised part: the JLCPCB symbol does not name its terminals - check the polarity mark in the preview"
        cands = [cands[0]]
    else:
        if len(single) >= 3 or (len(single) >= 2 and len(single) >= 0.8 * min(len(kp), len(ep))):
            c1 = fit_numbered(kp, ep, bottom, base, [(n, n) for n in single])
            if c1[0][0] <= 0.6:
                cands, method = c1, "pad numbers"
        if cands is None:
            cands, method = fit_geometric(kp, ep, bottom, base), "pad geometry"
    res, ang, tx, ty = cands[0]
    ties = [c for c in cands[1:] if c[0] < res + 0.08]
    if ties:
        if "1" in kp and "1" in ep:
            def pin1(c):
                t = place(ep["1"], c[1], bottom)
                return math.hypot(kp["1"][0] - t[0] - c[2], kp["1"][1] - t[1] - c[3])
            pool = sorted([cands[0]] + ties, key=pin1)
            res, ang, tx, ty = pool[0]
            method += ", pin 1"
            if pin1(pool[0]) > 0.6:
                res, ang, tx, ty = min([cands[0]] + ties, key=lambda c: (c[1] - base) % 360)
                note = "pad pattern is rotation-symmetric and the JLCPCB pad numbering differs"
        else:
            res, ang, tx, ty = min([cands[0]] + ties, key=lambda c: (c[1] - base) % 360)
            note = "pad pattern is rotation-symmetric"
        if note and str(fp.GetFPID().GetLibItemName()) in SYMMETRIC_PARTS:
            method += ", symmetric part"
            note = ""
    return dict(rotation=ang % 360, x=tx, y=ty, residual=res, method=method, note=note, pads=(len(kp), len(ep)), two_pin=two_pin)

def main(pcb, sourcing_path, fp_path, out):
    board = pcbnew.LoadBoard(pcb)
    src = json.load(open(sourcing_path))["parts"]
    fps_db = json.load(open(fp_path)) if os.path.exists(fp_path) else {}
    f = pcbnew.ToMM
    os.makedirs(out, exist_ok=True)
    rows, report, groups, problems = [], [], {}, []
    for fp in sorted(board.GetFootprints(), key=lambda q: natural(q.GetReference())):
        ref = fp.GetReference()
        mpn = fp.GetFieldText("MPN") if fp.HasFieldByName("MPN") else ""
        if not mpn or fp.IsDNP() or (fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM):
            continue
        part = src.get(mpn)
        if part is None or not part.get("lcsc"):
            problems.append("%s: no LCSC number for %s" % (ref, mpn)); continue
        lcsc = part["lcsc"]
        name = str(fp.GetFPID().GetLibItemName())
        groups.setdefault((lcsc, fp.GetValue(), name, mpn), []).append(ref)
        side = "Bottom" if fp.IsFlipped() else "Top"
        q = fp.GetPosition()
        krot = round(fp.GetOrientationDegrees()) % 360
        rec = fps_db.get(lcsc)
        kind = "diode" if (ref[0] == "D" or name.startswith("LED_")) else ("cap" if name.startswith("CP_") else None)
        if rec and rec.get("pads"):
            s = solve(fp, rec, kind)
            x, y, ang = s["x"], s["y"], s["rotation"]
            limit = 0.7 if s["two_pin"] else 0.35
            status = "MISMATCH" if s["residual"] > max(limit, 0.6) else ("check" if (s["residual"] > limit or s["note"]) else "ok")
            if status == "MISMATCH":
                problems.append("%s (%s, %s): pads of the JLCPCB footprint do not fit the board footprint (%.2f mm)" % (ref, mpn, lcsc, s["residual"]))
            report.append((ref, mpn, lcsc, name, side, krot, ang, (ang - (krot if side == "Top" else (180 - krot))) % 360,
                           f(q.x), -f(q.y), x, -y, s["residual"], s["method"], "%d/%d" % s["pads"], status, s["note"]))
        else:
            x, y = f(q.x), f(q.y)
            bb = [p.GetPosition() for p in fp.Pads() if p.GetNumber()]
            if bb:
                x = (min(f(p.x) for p in bb) + max(f(p.x) for p in bb)) / 2
                y = (min(f(p.y) for p in bb) + max(f(p.y) for p in bb)) / 2
            ang = krot if side == "Top" else (180 - krot) % 360
            report.append((ref, mpn, lcsc, name, side, krot, ang, 0, f(q.x), -f(q.y), x, -y, float("nan"), "no JLCPCB footprint record", "-", "check",
                           "placed by the centre of its pads with KiCad's angle: confirm in the placement preview"))
        rows.append((ref, "%.4fmm" % x, "%.4fmm" % -y, side, "%g" % ang))
    with open(os.path.join(out, "cpl_jlcpcb.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]); w.writerows(rows)
    with open(os.path.join(out, "bom_jlcpcb.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (lcsc, value, name, mpn), refs in sorted(groups.items(), key=lambda kv: natural(kv[1][0])):
            comment = mpn if value in mpn or mpn in value else "%s %s" % (value, mpn)
            w.writerow([comment, ",".join(refs), name, lcsc])
    with open(os.path.join(out, "placement_report.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "MPN", "LCSC", "KiCad footprint", "Side", "KiCad rotation", "JLCPCB rotation", "Offset vs. plain KiCad export",
                    "KiCad X", "KiCad Y", "JLCPCB X", "JLCPCB Y", "Worst pad mismatch mm", "Matched by", "Pads board/JLCPCB", "Status", "Note"])
        for r in report:
            w.writerow([("%.3f" % v) if isinstance(v, float) else v for v in r])
    n_ok = sum(1 for r in report if r[15] == "ok"); n_chk = sum(1 for r in report if r[15] == "check"); n_bad = sum(1 for r in report if r[15] == "MISMATCH")
    print("JLCPCB files: %d BOM lines, %d placements (%d top, %d bottom); rotation fit: %d ok, %d to check, %d mismatch" % (
        len(groups), len(rows), sum(1 for r in rows if r[3] == "Top"), sum(1 for r in rows if r[3] == "Bottom"), n_ok, n_chk, n_bad))
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
