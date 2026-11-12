import math

USB_W = 0.14
USB_GAP = 0.16
USB_SE_W = 0.185
STACKUP = dict(name="JLC04161H-3313", finish="ENIG", outer_cu=0.035, inner_cu=0.0152,
               prepreg=("3313 RC57%", 0.0994, 4.1), core=("FR4 TG155", 1.265, 4.42), mask=0.015)
USB_NETS = ("USB_UP_P", "USB_UP_N", "USB1_P", "USB1_N", "USB2_P", "USB2_N")
VIA_POWER = 0.6
VIA_SIGNAL = 0.5
MIN_POWER_WIDTH = {"VBUS": 1.6, "VBUS_SW": 1.6, "BUCK_SW": 1.6, "+5V": 1.6}


def _length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _offset(pts, d):
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - p[0], pts[1][1] - p[1]
        elif i == n - 1:
            dx, dy = p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]
        else:
            ax, ay = p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - p[0], pts[i + 1][1] - p[1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            ax, ay, bx, by = ax / la, ay / la, bx / lb, by / lb
            nax, nay, nbx, nby = -ay, ax, -by, bx
            mx, my = nax + nbx, nay + nby
            lm = math.hypot(mx, my)
            mx, my = mx / lm, my / lm
            k = d / (mx * nax + my * nay)
            out.append((p[0] + mx * k, p[1] + my * k))
            continue
        l = math.hypot(dx, dy)
        out.append((p[0] - dy / l * d, p[1] + dx / l * d))
    return out


def _bump(pts, seg, start, amp, flat, side):
    a, b = pts[seg], pts[seg + 1]
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / l, (b[1] - a[1]) / l
    nx, ny = -uy * side, ux * side
    def at(t, d):
        return (a[0] + ux * t + nx * d, a[1] + uy * t + ny * d)
    return pts[:seg + 1] + [at(start, 0), at(start + amp, amp), at(start + amp + flat, amp), at(start + 2 * amp + flat, 0)] + pts[seg + 1:]


def plan(pp):
    tracks, vias, usb, reserve = [], [], [], []

    def t(net, pts, w, lay="F", dst=None):
        for a, b in zip(pts, pts[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6:
                (tracks if dst is None else dst).append((net, lay, a[0], a[1], b[0], b[1], w))

    def v(net, x, y, dia=VIA_POWER):
        vias.append((net, x, y, dia))

    def gnd_vias(pad, spots, w=0.8):
        for (x, y) in spots:
            t("GND", [pad, (x, y)], w)
            v("GND", x, y)

    a9, a4 = pp("J1", "A9"), pp("J1", "A4")
    d1k, q1s = pp("D1", "1"), pp("Q1", "2")
    ybar = d1k[1]
    c1p = pp("C1", "1")
    t("VBUS", [a9, (a9[0], ybar)], 0.6)
    t("VBUS", [a4, (a4[0], ybar)], 0.6)
    t("VBUS", [d1k, (c1p[0], ybar)], MIN_POWER_WIDTH["VBUS"])
    t("VBUS", [(q1s[0], ybar), q1s], 1.2)
    for ref in ("C1", "C2", "R9", "C7", "D5"):
        p = pp(ref, "1")
        t("VBUS", [(p[0], ybar), p], 0.5)

    cc1, cc2 = pp("J1", "A5"), pp("J1", "B5")
    yv = cc1[1] + 1.4
    t("CC1", [cc1, (cc1[0], cc1[1] + 0.65), (cc1[0] - 0.25, yv)], 0.2)
    v("CC1", cc1[0] - 0.25, yv, VIA_SIGNAL)
    t("CC2", [cc2, (cc2[0], cc2[1] + 0.65), (cc2[0] + 0.25, yv)], 0.2)
    v("CC2", cc2[0] + 0.25, yv, VIA_SIGNAL)
    g_r, g_l = pp("J1", "A1"), pp("J1", "A12")
    t("GND", [g_r, (g_r[0] + 0.85, g_r[1])], 0.4)
    t("GND", [g_l, (g_l[0] - 0.85, g_l[1])], 0.4)

    q1d, c8, c9, c10, vin = pp("Q1", "3"), pp("C8", "1"), pp("C9", "1"), pp("C10", "1"), pp("U2", "2")
    t("VBUS_SW", [q1d, (q1d[0], q1d[1] + 1.8)], 1.2)
    t("VBUS_SW", [(q1d[0], q1d[1] + 1.6), (q1d[0], c8[1])], MIN_POWER_WIDTH["VBUS_SW"])
    t("VBUS_SW", [c8, c9], MIN_POWER_WIDTH["VBUS_SW"])
    t("VBUS_SW", [(c10[0], c8[1]), c10], 0.9)
    t("VBUS_SW", [c10, (vin[0], c10[1] + 0.6), vin], 0.6)

    pg, c10g, c9g, c8g = pp("U2", "1"), pp("C10", "2"), pp("C9", "2"), pp("C8", "2")
    t("GND", [pg, (pg[0], pg[1] + 1.8)], 0.55)
    t("GND", [c10g, pg], 0.5)
    gnd_vias(c10g, [(c10g[0] + 1.2, c10g[1])], 0.6)
    gnd_vias(pg, [(pg[0] + 1.1, pg[1])], 0.5)
    gnd_vias(c9g, [(c9g[0], c9g[1] + 1.7), (c9g[0] + 1.1, c9g[1] + 1.2)])
    gnd_vias(c8g, [(c8g[0], c8g[1] + 1.7), (c8g[0] - 1.3, c8g[1])])
    d1a = pp("D1", "2")
    gnd_vias(d1a, [(d1a[0] - 1.0, d1a[1] + 2.0), (d1a[0] + 1.0, d1a[1] + 2.0)])
    for ref in ("C1", "C2"):
        p = pp(ref, "2")
        gnd_vias(p, [(p[0], p[1] + 1.25)], 0.6)

    sw, l1a, c12b = pp("U2", "8"), pp("L1", "1"), pp("C12", "2")
    swx, swy = sw[0] + 0.5, sw[1] + 1.35
    t("BUCK_SW", [sw, (sw[0], swy - 0.3), (swx, swy)], 0.55)
    t("BUCK_SW", [(swx, swy), (swx, l1a[1] - 1.0)], MIN_POWER_WIDTH["BUCK_SW"])
    t("BUCK_SW", [c12b, (swx, c12b[1])], 0.5)
    t("BUCK_BOOT", [pp("U2", "7"), pp("C12", "1")], 0.3)
    t("BUCK_VCC", [pp("U2", "6"), pp("C11", "1")], 0.3)
    c11g = pp("C11", "2")
    gnd_vias(c11g, [(c11g[0] - 1.1, c11g[1])], 0.5)

    l1b = pp("L1", "2")
    c14, c15, c16, c17 = pp("C14", "1"), pp("C15", "1"), pp("C16", "1"), pp("C17", "1")
    ylink = c14[1] - 2.1
    t("+5V", [l1b, (c14[0] + 0.3, ylink), c14, c16], 1.6)
    t("+5V", [(c14[0] + 0.3, ylink), (c15[0], ylink), c15, c17], MIN_POWER_WIDTH["+5V"])
    for x in (c14[0] + 1.6, c14[0] + 3.0, c15[0]):
        v("+5V", x, ylink)
    for y in (c14[1], (c14[1] + c16[1]) / 2, c16[1]):
        t("+5V", [(c14[0], y), (c14[0] - 1.45, y)], 1.0)
        v("+5V", c14[0] - 1.45, y)
    c14g, c15g, c16g, c17g = pp("C14", "2"), pp("C15", "2"), pp("C16", "2"), pp("C17", "2")
    t("GND", [c14g, c16g, (c16g[0], c16g[1] + 1.8), (c16g[0] - 1.1, c16g[1] + 1.8)], 1.0)
    v("GND", c16g[0], c16g[1] + 1.8)
    v("GND", c16g[0] - 1.1, c16g[1] + 1.8)
    t("GND", [c15g, c17g, (c17g[0], c17g[1] + 1.8)], 1.0)
    v("GND", c17g[0], c17g[1] + 1.8)
    gnd_vias(c15g, [(c15g[0] + 1.3, c15g[1])])
    gnd_vias(c17g, [(c17g[0] + 1.3, c17g[1])])

    j61, j65 = pp("J6", "1"), pp("J6", "5")
    o1, o2 = pp("U5", "6"), pp("U6", "6")
    ych = (j61[1] + j65[1]) / 2 - 1.18
    t("USB1_VBUS", [o1, (o1[0] - 1.0, ych), (j61[0] + 1.85, ych), (j61[0] + 0.45, j61[1] - 0.5), j61], 0.8)
    t("USB2_VBUS", [o2, (o2[0] - 1.3, o2[1] + 1.3), (j65[0] + 1.3, o2[1] + 1.3), (j65[0], o2[1] + 2.6), j65], 0.8)
    for ref in ("U5", "U6"):
        vin5 = pp(ref, "1")
        t("+5V", [vin5, (vin5[0], vin5[1] + 1.36), (vin5[0] - 0.8, vin5[1] + 1.36)], 0.6)
        v("+5V", vin5[0], vin5[1] + 1.36)
        v("+5V", vin5[0] - 0.8, vin5[1] + 1.36)

    lines = {n: [] for n in USB_NETS}
    width = {n: (USB_W if n.startswith("USB_UP") else USB_SE_W) for n in USB_NETS}

    def balance(pair, comp):
        np_, nn_ = pair
        skew = sum(_length(l) for l in lines[np_]) - sum(_length(l) for l in lines[nn_])
        if abs(skew) < 0.02:
            return
        short = nn_ if skew > 0 else np_
        if short not in comp:
            raise RuntimeError("USB pair %s/%s: %s is %.2f mm short and has no compensation slot" % (np_, nn_, short, abs(skew)))
        idx, seg, start, flat, side = comp[short]
        amp = abs(skew) / (2 * (math.sqrt(2) - 1))
        lines[short][idx] = _bump(lines[short][idx], seg, start, amp, flat, side)

    hp, hn, sp, sn = pp("U4", "31"), pp("U4", "30"), pp("J3", "105"), pp("J3", "103")
    pitch = USB_W + USB_GAP
    yc = (hp[1] + hn[1]) / 2
    x0 = hp[0] + 0.6
    xs = (sp[0] + sn[0]) / 2
    ya = sp[1] - 2.0
    r = 0.4
    xt = xs - r - 3.4 - (ya - yc)
    centre = [(x0, yc), (xt, yc), (xt + (ya - yc), ya), (xs - r, ya), (xs, ya + r), (xs, sp[1] - 0.95)]
    sgn = 1 if hp[1] < hn[1] else -1
    lines["USB_UP_P"].append([hp, (x0 - 0.15, hp[1])] + _offset(centre, -sgn * pitch / 2) + [(sp[0], sp[1] - 0.75), sp])
    lines["USB_UP_N"].append([hn, (x0 - 0.15, hn[1])] + _offset(centre, sgn * pitch / 2) + [(sn[0], sn[1] - 0.75), sn])
    balance(("USB_UP_P", "USB_UP_N"), {"USB_UP_N": (0, 4, 0.5, 0.3, sgn), "USB_UP_P": (0, 4, 0.5, 0.3, -sgn)})
    reserve.append((xt + (ya - yc) + 0.2, ya - 0.6, xs - r, ya + 1.6))

    def link(net, a, b):
        t(net, [a, b], USB_SE_W)

    for port, esd in ((1, "U7"), (2, "U8")):
        npin, ppin = ("1", "2") if port == 1 else ("3", "4")
        hubp, hubn = pp("U4", ppin), pp("U4", npin)
        e4, e6, e3, e1, e5 = pp(esd, "4"), pp(esd, "6"), pp(esd, "3"), pp(esd, "1"), pp(esd, "5")
        for net, hub, pad in (("USB%d_P" % port, hubp, e4), ("USB%d_N" % port, hubn, e6)):
            dx = abs(pad[0] - hub[0])
            y_turn = pad[1] + 0.8 + dx
            lines[net].append([hub, (hub[0], y_turn), (pad[0], y_turn - dx), pad])
        link("USB%d_P" % port, e4, e3)
        link("USB%d_N" % port, e6, e1)
        xv, yv5 = (e5[0], e5[1] + 1.02) if port == 1 else (e5[0] + 0.35, e5[1] + 1.26)
        t("USB%d_VBUS" % port, [e5, (xv, yv5)], 0.3)
        v("USB%d_VBUS" % port, xv, yv5, VIA_SIGNAL)
    j3, j2 = pp("J6", "3"), pp("J6", "2")
    u73, u71 = pp("U7", "3"), pp("U7", "1")
    for net, a, b in (("USB1_P", u73, j3), ("USB1_N", u71, j2)):
        dx = abs(a[0] - b[0])
        lines[net].append([a, (a[0], a[1] - 1.2), (b[0], a[1] - 1.2 - dx), b])
    balance(("USB1_P", "USB1_N"), {})
    j7, j6, j4 = pp("J6", "7"), pp("J6", "6"), pp("J6", "4")
    u83, u81 = pp("U8", "3"), pp("U8", "1")
    gx = j4[0] + 0.75 + 0.2 + USB_SE_W / 2
    xn = gx + USB_SE_W + 0.15
    ye = (j7[1] + j3[1]) / 2
    y83, y81 = u83[1] - 1.06, u81[1] - 0.75
    lines["USB2_P"].append([u83, (u83[0], y83), (gx, y83 - (gx - u83[0])), (gx, ye + 0.65), (j7[0], ye + 0.65 - (j7[0] - gx)), j7])
    lines["USB2_N"].append([u81, (u81[0], y81), (xn, y81 - abs(xn - u81[0])), (xn, ye + 0.8), (xn + 0.8, ye), (j6[0] - 0.75, ye), (j6[0], ye - 0.75), j6])
    balance(("USB2_P", "USB2_N"), {"USB2_P": (0, 1, 1.4, 0.3, -1)})
    reserve.append((31.0, 20.9, 32.6, 22.7))
    hub = pp("U4", "37")
    ch = 3.1875
    p5, p10, p23, p29, p36 = (pp("U4", n) for n in ("5", "10", "23", "29", "36"))
    t("+3V3", [p5, (p5[0], hub[1] - ch + 1.0), (hub[0] - ch + 1.0, hub[1] - ch + 1.0), (p10[0] + 0.54, p10[1]), p10], 0.2)
    t("+3V3", [p10, pp("C30", "1")], 0.25)
    t("+3V3", [p23, (p23[0], hub[1] + ch - 1.0), (hub[0] + ch - 1.0, hub[1] + ch - 1.0), (hub[0] + ch - 1.0, p29[1] + 0.25),
               (p29[0] - 0.5, p29[1]), p29], 0.2)
    c34 = pp("C34", "1")
    t("+3V3", [p29, (p29[0] + 0.6, p29[1]), (c34[0] - 0.2, c34[1]), c34], 0.25)
    c35 = pp("C35", "1")
    t("+3V3", [p36, (c35[0] - 0.4, p36[1]), (c35[0], p36[1] - 0.4), c35], 0.25)
    xi, xo, y1, y3 = pp("U4", "33"), pp("U4", "32"), pp("Y1", "1"), pp("Y1", "3")
    ymid = (y1[1] + y3[1]) / 2
    t("HUB_XO", [xo, (y3[0] - 1.0, xo[1]), (y3[0] - 1.0 + (xo[1] - y3[1]), y3[1]), y3], 0.15)
    t("HUB_XI", [xi, (y3[0] - 2.0, xi[1]), (y3[0] - 2.0 + (xi[1] - ymid), ymid), (y1[0] - 0.85, ymid), (y1[0] - 0.4, ymid - 0.45), y1], 0.15)
    c26, c27 = pp("C26", "1"), pp("C27", "1")
    t("HUB_XI", [y1, c26], 0.15)
    yb = y3[1] + 0.9
    t("HUB_XO", [y3, (y3[0] + 0.9, yb), (c27[0] - 0.77, yb), (c27[0] - 0.77 + (yb - c27[1]), c27[1]), c27], 0.15)
    for net in USB_NETS:
        for l in lines[net]:
            t(net, l, width[net], dst=usb)
    return dict(tracks=tracks, vias=vias, usb=usb, reserve=reserve)


def boxes(p):
    out = []
    for (net, lay, x1, y1, x2, y2, w) in p["tracks"] + p["usb"]:
        if lay != "F":
            continue
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.6))
        for i in range(n):
            ax, ay = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
            bx, by = x1 + (x2 - x1) * (i + 1) / n, y1 + (y2 - y1) * (i + 1) / n
            g = w / 2 + 0.12
            out.append((min(ax, bx) - g, min(ay, by) - g, max(ax, bx) + g, max(ay, by) + g))
    for (net, x, y, dia) in p["vias"]:
        g = dia / 2 + 0.12
        out.append((x - g, y - g, x + g, y + g))
    out.extend(p["reserve"])
    return out
