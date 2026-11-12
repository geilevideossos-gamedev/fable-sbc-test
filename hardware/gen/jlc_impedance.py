#!/usr/bin/env python3
import json, sys, time, urllib.request, uuid, datetime
import prewire

URL = "https://jlcpcb.com/api/jlcTools/impedance/calc"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MIL = 1 / 0.0254
BASE = dict(T1=1.6, CEr=3.8, Er1=4.3, C1=1, C2=0.6, dCalculateMode=3, isLinkComputingMode=False, W2LinkW1Incr=0.5)

def call(mark, arg):
    body = json.dumps({"accessId": str(uuid.uuid4()), "impedance_calc_mark": mark, "paramMd5": "d41d8cd98f00b204e9800998ecf8427e",
                       "impedance_calc_arg": arg, "uuid": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(URL, data=body, headers={"User-Agent": UA, "Content-Type": "application/json",
                                                           "Referer": "https://jlcpcb.com/pcb-impedance-calculator"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                b = json.loads(r.read().decode())["body"]
            if b.get("impedance_calc_status") == 0:
                return b["impedance_calc_result"]
            raise RuntimeError(str(b)[:200])
        except Exception as e:
            err = e; time.sleep(2 * (attempt + 1))
    raise RuntimeError("JLCPCB calculator: %s" % err)

def z_pair(w, s, h):
    a = dict(BASE, H1=round(h * MIL, 4), W1=round(w * MIL, 4), W2=round(w * MIL - 0.5, 4), S1=round(s * MIL, 4), C3=1)
    return call("DiffEdgeCoupledCoatedMicrostrip1B", a)["dImpedance"]

def z_single(w, h):
    a = dict(BASE, H1=round(h * MIL, 4), W1=round(w * MIL, 4), W2=round(w * MIL - 0.5, 4))
    return call("CoatedMicrostrip1B", a)["dImpedance"]

def w_pair(z, s, h):
    a = dict(BASE, H1=round(h * MIL, 4), W1=5.2, W2=4.7, S1=round(s * MIL, 4), C3=1, Zo=z, ZoTol=0.5, MinW2=2, MaxW2=150)
    r = call("W2_DiffEdgeCoupledCoatedMicrostrip1B", a)
    return r["jBackCalc"]["W1"] / MIL, r["dImpedance"]

def w_single(z, h):
    a = dict(BASE, H1=round(h * MIL, 4), W1=8, W2=7.5, Zo=z, ZoTol=0.5, MinW2=2, MaxW2=150)
    r = call("W2_CoatedMicrostrip1B", a)
    return r["jBackCalc"]["W1"] / MIL, r["dImpedance"]

def main(out=None):
    st = prewire.STACKUP
    h = st["prepreg"][1]
    w, s, se = prewire.USB_W, prewire.USB_GAP, prewire.USB_SE_W
    zp, zs = z_pair(w, s, h), z_single(se, h)
    wp, zwp = w_pair(90, s, h)
    ws, zws = w_single(45, h)
    lines = ["USB 2.0 track geometry checked with JLCPCB's impedance calculator (%s, %s)" % (URL, datetime.date.today().isoformat()),
             "stack-up %s: outer layer over %s prepreg, %.4f mm after lamination, reference plane In1.Cu (GND)" % (st["name"], st["prepreg"][0], h),
             "",
             "coupled pair  %.3f mm wide, %.3f mm gap   -> %6.2f ohm differential (target 90, USB 2.0 allows 76.5 .. 103.5)" % (w, s, zp),
             "single track  %.3f mm wide                 -> %6.2f ohm (two uncoupled lines: %.2f ohm differential)" % (se, zs, 2 * zs),
             "",
             "calculator's own width for 90 ohm differential at a %.3f mm gap: %.4f mm (it stops at %.2f ohm)" % (s, wp, zwp),
             "calculator's own width for 45 ohm single ended:                %.4f mm (it stops at %.2f ohm)" % (ws, zws)]
    ok = abs(zp - 90) <= 4.5 and abs(2 * zs - 90) <= 4.5
    lines.append("result: %s" % ("within +-5 % of 90 ohm" if ok else "OUTSIDE +-5 % of 90 ohm"))
    txt = "\n".join(lines) + "\n"
    if out:
        open(out, "w").write(txt)
    sys.stdout.write(txt)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
