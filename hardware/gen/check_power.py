#!/usr/bin/env python3
import sys, math
import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

PATHS = [
    ("VBUS", "J1.A9", "D1.1", 0.6, 1.65, "left VBUS contact pair to the bar (limited by the 0.6 mm connector pad)"),
    ("VBUS", "J1.A4", "D1.1", 0.6, 1.65, "right VBUS contact pair to the bar (limited by the 0.6 mm connector pad)"),
    ("VBUS", "D1.1", "C1.1", 1.6, 3.3, "VBUS bar, TVS to the bypass capacitors"),
    ("VBUS", "D1.1", "Q1.2", 1.2, 3.3, "VBUS bar to the load switch source"),
    ("VBUS_SW", "Q1.3", "C8.1", 1.2, 3.3, "load switch drain to the buck input capacitors"),
    ("VBUS_SW", "C8.1", "C9.1", 1.6, 3.3, "between the two 10 uF input capacitors"),
    ("VBUS_SW", "C9.1", "U2.2", 0.59, 3.0, "input capacitors to the VIN pin, RMS at 9 V in (limited by the 0.6 mm pin pad)"),
    ("BUCK_SW", "U2.8", "L1.1", 0.55, 4.0, "switch pin to the inductor (limited by the 0.6 mm pin pad)"),
    ("+5V", "L1.2", "C14.1", 1.6, 4.0, "inductor to the first output capacitor column"),
    ("+5V", "L1.2", "C17.1", 1.6, 2.0, "inductor to the second output capacitor column"),
    ("GND", "U2.1", "U2.9", 0.5, 3.5, "PGND pin to the exposed pad on the front layer, RMS at 20 V in (limited by the pin pad)"),
    ("GND", "U2.1", "C10.2", 0.5, 3.5, "PGND pin to the 220 nF bypass capacitor (carries the high-frequency part only)"),
    ("USB1_VBUS", "U5.6", "J6.1", 0.6, 1.3, "port 1 current-limit switch to the connector"),
    ("USB2_VBUS", "U6.6", "J6.5", 0.6, 1.3, "port 2 current-limit switch to the connector"),
]

def ipc2221(width_mm, rise_k, oz=1.0):
    area = (width_mm / 0.0254) * (1.378 * oz)
    return 0.048 * rise_k ** 0.44 * area ** 0.725

def pad_shape(pad, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(ps, layer, 0, 2000, pcbnew.ERROR_INSIDE)
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append(Polygon([(pcbnew.ToMM(o.CPoint(k).x), pcbnew.ToMM(o.CPoint(k).y)) for k in range(o.PointCount())]))
    return unary_union(out)

def net_copper(board, net, layer):
    shapes = []
    for tr in board.GetTracks():
        if tr.GetNetname() != net:
            continue
        if tr.Type() == pcbnew.PCB_VIA_T:
            q = tr.GetPosition()
            shapes.append(Point(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)).buffer(pcbnew.ToMM(tr.GetWidth(layer)) / 2, 16))
        elif tr.GetLayer() == layer:
            a, e = tr.GetStart(), tr.GetEnd()
            w = pcbnew.ToMM(tr.GetWidth())
            p1, p2 = (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
            shapes.append(Point(p1).buffer(w / 2, 16) if p1 == p2 else LineString([p1, p2]).buffer(w / 2, 16))
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != net or not z.IsOnLayer(layer):
            continue
        ps = z.GetFilledPolysList(layer)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            shell = [(pcbnew.ToMM(o.CPoint(k).x), pcbnew.ToMM(o.CPoint(k).y)) for k in range(o.PointCount())]
            holes = []
            for h in range(ps.HoleCount(i)):
                ho = ps.Hole(i, h)
                holes.append([(pcbnew.ToMM(ho.CPoint(k).x), pcbnew.ToMM(ho.CPoint(k).y)) for k in range(ho.PointCount())])
            if len(shell) >= 3:
                shapes.append(Polygon(shell, holes).buffer(0))
    return unary_union(shapes) if shapes else Polygon()

def find_pad(board, name, net):
    ref, num = name.split(".")
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        return None
    best = None
    for p in fp.Pads():
        if p.GetNumber() == num and p.GetNetname() == net and p.IsOnLayer(pcbnew.F_Cu):
            b = p.GetBoundingBox()
            area = b.GetWidth() * b.GetHeight()
            if best is None or area > best[0]:
                best = (area, p)
    return best[1] if best else None

def connected(copper, pa, pb, width):
    core = copper.buffer(-(width / 2 - 0.004), 16).buffer(width / 2 - 0.004, 16) if width > 0.01 else copper
    whole = unary_union([core, pa, pb])
    parts = list(whole.geoms) if whole.geom_type == "MultiPolygon" else [whole]
    ca, cb = pa.representative_point(), pb.representative_point()
    for g in parts:
        if g.buffer(1e-6).contains(ca) and g.buffer(1e-6).contains(cb):
            return True
    return False

def bottleneck(copper, pa, pb):
    if not connected(copper, pa, pb, 0.0):
        return None
    lo, hi = 0.05, 4.0
    if connected(copper, pa, pb, hi):
        return hi
    for _ in range(14):
        mid = (lo + hi) / 2
        if connected(copper, pa, pb, mid):
            lo = mid
        else:
            hi = mid
    return lo

def main(pcb, out=None):
    board = pcbnew.LoadBoard(pcb)
    cache, lines, bad = {}, [], 0
    lines.append("Narrowest front-layer copper on the high-current paths (probe width that still passes from pad to pad)")
    lines.append("need mm = the width the path was designed with; a path fails when the copper found is narrower than that.")
    lines.append("I(10K), I(20K) = IPC-2221 current of an outer-layer track of the neck width for 10 K / 20 K rise, for comparison with")
    lines.append("the load: every neck below 1.2 mm is the pad of a connector contact or of a regulator pin and shorter than 0.7 mm.")
    lines.append("%-10s %-8s %-8s %9s %9s %9s %11s %11s  %s" % ("net", "from", "to", "neck mm", "need mm", "load A", "I(10K) A", "I(20K) A", "path"))
    for net, a, b, need, load, text in PATHS:
        pa, pb = find_pad(board, a, net), find_pad(board, b, net)
        if pa is None or pb is None:
            lines.append("%-10s %-8s %-8s %9s %9.2f %9.2f %11s %11s  %s" % (net, a, b, "no pad", need, load, "-", "-", text)); bad += 1
            continue
        if net not in cache:
            cache[net] = net_copper(board, net, pcbnew.F_Cu)
        w = bottleneck(cache[net], pad_shape(pa, pcbnew.F_Cu), pad_shape(pb, pcbnew.F_Cu))
        if w is None:
            lines.append("%-10s %-8s %-8s %9s %9.2f %9.2f %11s %11s  %s" % (net, a, b, "open", need, load, "-", "-", text)); bad += 1
            continue
        ok = w + 0.02 >= need
        if not ok:
            bad += 1
        lines.append("%-10s %-8s %-8s %9.2f %9.2f %9.2f %11.2f %11.2f  %s%s" % (net, a, b, w, need, load, ipc2221(w, 10), ipc2221(w, 20), text, "" if ok else "   <-- TOO NARROW"))
    for net in ("+5V", "GND"):
        n = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net)
        lines.append("vias of %s into its plane: %d" % (net, n))
    lines.append("result: %s" % ("all paths are as wide as designed" if not bad else "%d path(s) narrower than designed" % bad))
    txt = "\n".join(lines) + "\n"
    if out:
        open(out, "w").write(txt)
    sys.stdout.write(txt)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
