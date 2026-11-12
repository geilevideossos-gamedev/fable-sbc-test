#!/usr/bin/env python3
import json, sys, time, urllib.request, urllib.parse, datetime

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SEARCH = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
DETAIL = "https://cart.jlcpcb.com/shoppingCart/smtGood/getComponentDetail?componentCode=%s"
LCSC = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=%s"
EASYEDA = "https://easyeda.com/api/products/%s/components?version=6.4.19.5"

def _get(url, body=None, tries=4):
    hdr = {"User-Agent": UA, "Accept": "application/json", "Referer": "https://jlcpcb.com/parts", "Origin": "https://jlcpcb.com"}
    data = None
    if body is not None:
        data = json.dumps(body).encode(); hdr["Content-Type"] = "application/json"
    err = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdr), timeout=40) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    raise RuntimeError("%s: %s" % (url, err))

def _price(prices, qty):
    best = None
    for p in prices or []:
        if p["startNumber"] <= qty and (p["endNumber"] == -1 or qty <= p["endNumber"]):
            best = p["productPrice"]
    if best is None and prices:
        best = sorted(prices, key=lambda p: p["startNumber"])[0]["productPrice"]
    return best

def _kind(c):
    if c.get("componentLibraryType") == "base": return "Basic"
    if c.get("preferredComponentFlag"): return "Preferred Extended"
    return "Extended"

def search(keyword, size=25, page=1, extra=None):
    body = {"keyword": keyword, "currentPage": page, "pageSize": size}
    if extra: body.update(extra)
    d = _get(SEARCH, body)
    out = []
    for c in ((d.get("data") or {}).get("componentPageInfo") or {}).get("list") or []:
        out.append(dict(code=c["componentCode"], mpn=c["componentModelEn"], brand=c["componentBrandEn"], kind=_kind(c),
                        stock=c["stockCount"], price1=_price(c.get("componentPrices"), 1), price100=_price(c.get("componentPrices"), 100),
                        package=c.get("componentSpecificationEn"), descr=c.get("describe"), category=c.get("componentTypeEn"),
                        datasheet=c.get("dataManualUrl")))
    return out

def detail(code):
    d = (_get(DETAIL % code).get("data")) or {}
    if not d:
        return None
    lc = {}
    try:
        lc = (_get(LCSC % code, tries=2).get("result")) or {}
    except Exception:
        lc = {}
    kind = "Basic" if d.get("componentLibraryType") == "base" else "Extended"
    return dict(code=d["componentCode"], mpn=d["componentModelEn"], brand=d["componentBrandEn"], kind=kind,
                jlc_stock=d.get("stockCount"), price1=_price(d.get("prices"), 1), price10=_price(d.get("prices"), 10),
                price100=_price(d.get("prices"), 100), package=d.get("componentSpecificationEn"), descr=d.get("describe"),
                assembly_process=d.get("assemblyProcess"), assembly_mode=d.get("assemblyMode"), xray=bool(d.get("xrayFlag")),
                fixture=bool(d.get("fixtureFlag")), special_fee=d.get("specialComponentFee") or 0.0,
                min_order=d.get("leastNumber"), status=d.get("componentStatus"), datasheet=d.get("dataManualUrl"),
                attributes={a["attribute_name_en"]: a["attribute_value_name"] for a in d.get("attributes") or []},
                lcsc_stock=lc.get("stockNumber"), lcsc_url="https://www.lcsc.com/product-detail/%s.html" % code,
                jlc_url="https://jlcpcb.com/partdetail/%s" % code)

def footprint(code):
    d = _get(EASYEDA % code, tries=3)
    res = d.get("result")
    if not res or not res.get("packageDetail"):
        return None
    ds = res["packageDetail"]["dataStr"]
    hx, hy = float(ds["head"]["x"]), float(ds["head"]["y"])
    pads = []
    for sh in ds["shape"]:
        if sh.startswith("PAD~"):
            f = sh.split("~")
            pads.append([f[8], round((float(f[2]) - hx) * 0.254, 4), round((float(f[3]) - hy) * 0.254, 4),
                         round(float(f[4]) * 0.254, 4), round(float(f[5]) * 0.254, 4)])
    pins, pin_xy, hor, ver = {}, {}, [], []
    for sh in res["dataStr"]["shape"]:
        if sh.startswith("P~"):
            seg = sh.split("^^")
            try:
                head = seg[0].split("~")
                pins[head[3]] = seg[3].split("~")[4]
                pin_xy[head[3]] = (float(head[4]), float(head[5]))
            except (IndexError, ValueError):
                pass
        elif sh.startswith("PL~"):
            try:
                x1, y1, x2, y2 = [float(v) for v in sh.split("~")[1].split(" ")[:4]]
            except ValueError:
                continue
            if abs(y1 - y2) < 0.01 and 1.0 <= abs(x1 - x2) <= 6.0:
                hor.append(((x1 + x2) / 2, y1))
            elif abs(x1 - x2) < 0.01 and 1.0 <= abs(y1 - y2) <= 6.0:
                ver.append((x1, (y1 + y2) / 2))
    plus_pin = None
    crosses = [h for h in hor for v in ver if abs(h[0] - v[0]) < 0.6 and abs(h[1] - v[1]) < 0.6]
    if len(crosses) == 1 and len(pin_xy) == 2:
        cx, cy = crosses[0]
        plus_pin = min(pin_xy, key=lambda n: (pin_xy[n][0] - cx) ** 2 + (pin_xy[n][1] - cy) ** 2)
    return dict(title=res.get("title"), package=res["packageDetail"].get("title"), pads=pads, pins=pins, plus_pin=plus_pin)

USAGE = """jlc_lookup.py search <keyword> ...
jlc_lookup.py code <C number> ...
jlc_lookup.py refresh <sourcing_jlc.json>
jlc_lookup.py footprints <sourcing_jlc.json> <jlc_footprints.json>"""

def main(argv):
    if len(argv) < 2:
        print(USAGE); return 2
    if argv[0] == "search":
        for kw in argv[1:]:
            print("== %s" % kw)
            for c in search(kw):
                print("  %-10s %-9s stock %-8s %-8s %-28s %-22s %-16s %s" % (c["code"], c["kind"].replace("Preferred Extended", "Preferred"),
                      c["stock"], c["price1"], c["mpn"][:28], (c["brand"] or "")[:22], (c["package"] or "")[:16], (c["descr"] or "")[:110]))
    elif argv[0] == "code":
        for code in argv[1:]:
            print(json.dumps(detail(code), indent=1, ensure_ascii=False))
    elif argv[0] == "refresh":
        db = json.load(open(argv[1]))
        for key, p in sorted(db["parts"].items()):
            d = detail(p["lcsc"])
            if d is None:
                print("NOT FOUND", key, p["lcsc"]); continue
            pref = any(c["code"] == p["lcsc"] and c["kind"] == "Preferred Extended" for c in search(p["lcsc"], size=5))
            p.update(jlc_stock=d["jlc_stock"], lcsc_stock=d["lcsc_stock"], jlc_p1=d["price1"], jlc_p10=d["price10"], jlc_p100=d["price100"],
                     jlc_type="Preferred Extended" if (pref and d["kind"] != "Basic") else d["kind"], jlc_mpn=d["mpn"], jlc_brand=d["brand"],
                     jlc_package=d["package"], assembly_process=d["assembly_process"], assembly_mode=d["assembly_mode"],
                     xray=d["xray"], special_fee=d["special_fee"], min_order=d["min_order"])
            print("%-28s %-10s %-18s JLC %-8s LCSC %-8s %s" % (key[:28], p["lcsc"], p["jlc_type"], p["jlc_stock"], p["lcsc_stock"], p["jlc_p10"]))
        db["checked"] = datetime.date.today().isoformat()
        json.dump(db, open(argv[1], "w"), indent=1, sort_keys=True, ensure_ascii=False)
    elif argv[0] == "footprints":
        db = json.load(open(argv[1]))
        out = {}
        for key, p in sorted(db["parts"].items()):
            fp = footprint(p["lcsc"])
            if fp is None:
                print("no JLCPCB / EasyEDA footprint for %s (%s)" % (p["lcsc"], key)); continue
            out[p["lcsc"]] = fp
            print("%-10s %-28s %-44s %d pads" % (p["lcsc"], key[:28], (fp["package"] or "")[:44], len(fp["pads"])))
        json.dump(out, open(argv[2], "w"), indent=0, sort_keys=True, ensure_ascii=False)
    else:
        print(USAGE); return 2
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
