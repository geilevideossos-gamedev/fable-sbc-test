#!/usr/bin/env python3
import sys
import pcbnew
from shapely.geometry import Point, box

MM = 1e-6


def exposed(pad):
    fp = pad.GetParentFootprint()
    if not fp.GetReference().startswith("U"):
        return False
    nums = [int(p.GetNumber()) for p in fp.Pads() if p.GetNumber().isdigit()]
    return bool(nums) and pad.GetNumber() == str(max(nums))


def main(path, report):
    board = pcbnew.LoadBoard(path)
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            b = p.GetBoundingBox()
            pads.append((p, fp.GetReference(), box(b.GetLeft() * MM, b.GetTop() * MM, b.GetRight() * MM, b.GetBottom() * MM)))
    n_via = n_ep = 0
    bad = []
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        n_via += 1
        c = t.GetPosition()
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            land = Point(c.x * MM, c.y * MM).buffer(t.GetWidth(lay) * MM / 2)
            for p, ref, g in pads:
                if not p.IsOnLayer(lay) or not g.intersects(land) or g.intersection(land).area < 1e-4:
                    continue
                if exposed(p):
                    n_ep += 1
                else:
                    bad.append("  via %s at (%.3f, %.3f) overlaps pad %s.%s (%s)" % (t.GetNetname(), c.x * MM - 100, c.y * MM - 60, ref, p.GetNumber(), p.GetNetname()))
    lines = ["Vias against SMD pads (a via land may only overlap the exposed pad of an IC)",
             "%d vias, %d of them inside exposed pads, %d overlapping another pad" % (n_via, n_ep, len(bad))] + bad
    lines.append("result: %s" % ("no via in or touching a lead pad" if not bad else "%d vias touch a pad" % len(bad)))
    open(report, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
