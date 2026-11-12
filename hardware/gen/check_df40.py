#!/usr/bin/env python3
import math, sys
import pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

INNER, OUTER, HALF = 0.75, 1.19, 0.10
MM = 1e-6


def strips(fp):
    a = math.radians(fp.GetOrientationDegrees())
    cx, cy = fp.GetPosition().x * MM, fp.GetPosition().y * MM
    flip = fp.IsFlipped()
    pads = [p for p in fp.Pads() if p.GetNumber()]
    loc = []
    for p in pads:
        dx, dy = p.GetPosition().x * MM - cx, p.GetPosition().y * MM - cy
        lx = dx * math.cos(a) - dy * math.sin(a)
        ly = dx * math.sin(a) + dy * math.cos(a)
        loc.append((p, lx, ly))
    out = []
    for p, lx, ly in loc:
        s = 1 if ly > 0 else -1
        corners = [(lx - HALF, s * INNER), (lx + HALF, s * INNER), (lx + HALF, s * OUTER), (lx - HALF, s * OUTER)]
        world = [(cx + x * math.cos(a) + y * math.sin(a), cy - x * math.sin(a) + y * math.cos(a)) for x, y in corners]
        out.append((p, Polygon(world)))
    return out, (pcbnew.B_Cu if flip else pcbnew.F_Cu)


def main(path, report):
    board = pcbnew.LoadBoard(path)
    lines, bad = [], 0
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        if "DF40C" not in str(fp.GetFPID().GetLibItemName()):
            continue
        zone, layer = strips(fp)
        copper = []
        for t in board.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T:
                c = t.GetPosition()
                copper.append((t.GetNetname(), Point(c.x * MM, c.y * MM).buffer(t.GetWidth(layer) * MM / 2), "via"))
            elif t.GetLayer() == layer:
                s, e = t.GetStart(), t.GetEnd()
                g = LineString([(s.x * MM, s.y * MM), (e.x * MM, e.y * MM)]).buffer(t.GetWidth() * MM / 2)
                copper.append((t.GetNetname(), g, "track %.2f mm" % (t.GetWidth() * MM)))
        for z in board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(layer):
                continue
            polys = z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                o = polys.Outline(i)
                pts = [(o.CPoint(k).x * MM, o.CPoint(k).y * MM) for k in range(o.PointCount())]
                if len(pts) >= 3:
                    holes = []
                    for h in range(polys.HoleCount(i)):
                        ho = polys.Hole(i, h)
                        holes.append([(ho.CPoint(k).x * MM, ho.CPoint(k).y * MM) for k in range(ho.PointCount())])
                    copper.append((z.GetNetname(), Polygon(pts, holes).buffer(0), "zone fill"))
        own = other = 0
        for pad, poly in zone:
            for net, g, what in copper:
                if not g.intersects(poly) or g.intersection(poly).area < 1e-5:
                    continue
                if net == pad.GetNetname():
                    own += 1
                else:
                    other += 1; bad += 1
                    lines.append("  %s pad %s (%s): %s of net %s inside the strip" %
                                 (fp.GetReference(), pad.GetNumber(), pad.GetNetname() or "unconnected", what, net or "no net"))
        lines.insert(len(lines) - other, "%s: %d strips, copper of the pad's own net in %d, copper of another net in %d" %
                     (fp.GetReference(), len(zone), own, other))
    lines.append("result: %s" % ("no foreign copper inside the DF40 strips" if not bad else "%d strip violations" % bad))
    open(report, "w").write("DF40 socket strips between 0.75 mm and 1.19 mm from the connector centre line (Hirose: only the pad's own circuit)\n"
                            + "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
