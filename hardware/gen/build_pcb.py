#!/usr/bin/env python3
"""Build voxhub.kicad_pcb from the schematic netlist (run inside KiCad's python).

  build_pcb.py place   <netlist> <outdir>   -> placed, unrouted board + voxhub.dsn
  build_pcb.py finish  <outdir>             -> imports voxhub.ses, pours zones, saves

Placement = a table of fixed positions (connectors, ICs, mechanics) plus a greedy
"nearest free spot to the pad it talks to" placer for the small parts.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from sexpr import parse, find, first

MM = pcbnew.FromMM
W, H = 100.0, 74.0            # board size
OX, OY = 100.0, 60.0          # board origin on the KiCad page
SYS_FP = "/usr/share/kicad/footprints"
POWER = ("GND", "+5V", "+3V3")

# ref -> (x, y, rot, side)  [board coordinates, mm, origin = rear-left corner, F.Cu view]
CM4_X0, CM4_Y0 = 95.5, 64.5   # CM4 mounting hole nearest front-right; module spans x 44..99, y 28..68
FIXED = {
    "J1": (13.0, 3.67, 180, "F"),      # USB-C PD input (rear edge)
    "J6": (38.75, 13.11, 180, "F"),    # stacked USB-A (rear edge)
    "J4": (56.0, 8.7, 180, "F"),       # microSD (rear edge; shield pads end 0.37 mm inside the edge)
    "U1": (13.0, 14.0, 0, "F"), "Q1": (23.5, 9.5, 90, "F"),
    "U2": (8.5, 25.5, 90, "F"), "L1": (9.0, 36.0, 0, "F"),
    "U4": (33.5, 26.5, 270, "F"), "U7": (32.0, 18.6, 0, "F"), "U8": (38.2, 18.6, 0, "F"),
    "U5": (45.8, 4.0, 90, "F"), "U6": (45.8, 10.5, 90, "F"),
    "U3": (68.5, 9.0, 0, "F"),
    "J2": (74.0, 64.96, 0, "F"), "J3": (74.0, 31.04, 0, "F"),
    "H5": (95.5, 64.5, 0, "F"), "H6": (95.5, 31.5, 0, "F"), "H7": (47.5, 64.5, 0, "F"), "H8": (47.5, 31.5, 0, "F"),
    "H1": (3.5, 3.5, 0, "F"), "H2": (96.5, 3.5, 0, "F"), "H3": (3.5, 70.5, 0, "F"), "H4": (97.0, 70.8, 0, "F"),
    "U9": (40.0, 61.0, 0, "F"), "MK1": (9.5, 70.2, 0, "F"), "MK2": (92.0, 10.0, 0, "F"),
    "U10": (9.0, 49.0, 0, "F"), "J7": (4.2, 58.5, 90, "F"),
    "U11": (24.0, 66.5, 180, "F"), "J8": (36.5, 46.0, 0, "F"),
    "SW1": (33.5, 54.0, 0, "B"),
    "J5": (80.0, 21.5, 90, "F"),
    "FID1": (22.0, 2.0, 0, "F"), "FID2": (31.0, 44.0, 0, "F"), "FID3": (2.0, 40.0, 0, "F"),
}
ANCHOR_PTS = {"TPZONE": (84.0, 12.0), "UI": (38.0, 66.0), "CM4CAP": (80.0, 71.0)}
# keep-out rectangles for the automatic placer (x1, y1, x2, y2)
NOGO_F = [(43.6, 27.6, 99.4, 68.4),          # under the CM4 module
          (19.3, 58.0, 28.7, 64.2)]          # MGM240P antenna clearance (handled as rule area too)
HOLES = [(3.5, 3.5), (96.5, 3.5), (3.5, 70.5), (97.0, 70.8)]

def write_project(outdir):
    """pcbnew's Save() rewrites voxhub.kicad_pro with default rules - put ours back."""
    import shutil
    shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_settings.json"),
                    os.path.join(outdir, "voxhub.kicad_pro"))

def sorted_tracks(board):
    """Tracks/vias in a canonical order.  KiCad orders items by their (random) UUIDs when saving, so
    without this the patch router would see a different order - and take different decisions - on every run."""
    def key(tr):
        if tr.Type() == pcbnew.PCB_VIA_T:
            q = tr.GetPosition(); return (tr.GetNetname(), 1, 0, q.x, q.y, q.x, q.y, tr.GetWidth(pcbnew.F_Cu))
        a, e = tr.GetStart(), tr.GetEnd()
        if (a.x, a.y) > (e.x, e.y): a, e = e, a
        return (tr.GetNetname(), 0, tr.GetLayer(), a.x, a.y, e.x, e.y, tr.GetWidth())
    return sorted(board.GetTracks(), key=key)

def sorted_fps(board):
    return sorted(board.GetFootprints(), key=lambda fp: fp.GetReference())

def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

def load_netlist(path):
    t = parse(open(path).read())
    comps = {}
    for c in find(first(t, "components"), "comp"):
        ref = first(c, "ref")[1]
        props = {}
        for p in find(c, "property"):
            nm = first(p, "name"); vl = first(p, "value")
            if nm: props[nm[1]] = vl[1] if vl and len(vl) > 1 else ""
        fields = {}
        for f in find(first(c, "fields", []), "field"):
            nm = first(f, "name")
            if nm: fields[nm[1]] = f[2] if len(f) > 2 and not isinstance(f[2], list) else ""
        sp = first(c, "sheetpath")
        comps[ref] = dict(ref=ref, value=first(c, "value")[1], footprint=first(c, "footprint")[1],
                          tstamp=first(c, "tstamps")[1], sheet_tstamps=first(sp, "tstamps")[1],
                          sheet_name=first(sp, "names")[1], props=props, fields=fields, pins={})
    for n in find(first(t, "nets"), "net"):
        name = first(n, "name")[1]
        for nd in find(n, "node"):
            comps[first(nd, "ref")[1]]["pins"][first(nd, "pin")[1]] = name
    return comps

def crt_bbox(fp):
    """Courtyard bounding box (mm, board coords); falls back to pads."""
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            b = g.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        for p in fp.Pads():
            b = p.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        b = fp.GetBoundingBox(False)
        xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    f = pcbnew.ToMM
    return (f(min(xs)) - OX, f(min(ys)) - OY, f(max(xs)) - OX, f(max(ys)) - OY)

def overlap(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])

def place(netlist, outdir):
    comps = load_netlist(netlist)
    model = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_netlist.json")))
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    board.SetFileName(os.path.join(outdir, "voxhub.kicad_pcb"))
    nets = {}
    def net(name):
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni); nets[name] = ni
        return nets[name]
    fps = {}
    for ref in sorted(comps):
        c = comps[ref]
        lib, name = c["footprint"].split(":")
        libdir = os.path.join(outdir, "voxhub.pretty") if lib == "voxhub" else os.path.join(SYS_FP, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, name)
        if fp is None:
            raise RuntimeError("footprint not found: " + c["footprint"])
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref); fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["sheet_tstamps"].rstrip("/") + "/" + c["tstamp"]))
        fp.SetSheetname(c["sheet_name"]); fp.SetSheetfile(c["props"].get("Sheetfile", ""))
        for k in ("MPN", "Manufacturer", "PartDescription"):
            v = c["fields"].get(k) or model.get(ref, {}).get("fields", {}).get(k, "")
            if v:
                fp.SetField(k, v)
                fp.GetFieldByName(k).SetVisible(False)
        m = model.get(ref, {})
        if m.get("dnp"):
            fp.SetDNP(True)
        attrs = fp.GetAttributes()
        if not m.get("in_bom", True):
            attrs |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        fp.SetAttributes(attrs)
        for pad in fp.Pads():
            n = c["pins"].get(pad.GetNumber())
            if n and pad.GetNumber():
                pad.SetNet(net(n))
        # 3D models: use the copies / stand-ins shipped in hardware/3dmodels (the KiCad docker image has none)
        mdls = [m_ for m_ in fp.Models()]
        fp.Models().clear()
        for mdl in mdls:               # (Models() hands out copies - rebuild the list)
            fn = mdl.m_Filename.replace("${KICAD9_3DMODEL_DIR}/", "").replace(".wrl", ".step")
            if not fn.startswith("${KIPRJMOD}"):
                mdl.m_Filename = "${KIPRJMOD}/3dmodels/" + fn
            fp.Models().push_back(mdl)
        if ref == "J2":      # the CM4 itself (module + heat sink) rides on its socket footprint
            m3 = pcbnew.FP_3DMODEL()
            m3.m_Filename = "${KIPRJMOD}/3dmodels/RaspberryPi_CM4_with_heatsink.step"
            m3.m_Offset = pcbnew.VECTOR3D(71.5 - 74.0, 64.96 - 48.0, 0.0)
            fp.Models().push_back(m3)
        fp.Reference().SetVisible(True)
        fp.Reference().SetLayer(pcbnew.F_Fab)
        for fld in (fp.Reference(), fp.Value()):
            fld.SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7))); fld.SetTextThickness(MM(0.1))
        board.Add(fp)
        fps[ref] = fp

    def put(ref, x, y, rot, side):
        fp = fps[ref]
        if side == "B" and not fp.IsFlipped():
            fp.SetPosition(P(x, y))
            fp.Flip(P(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)

    placed = {"F": [], "B": []}       # courtyard boxes
    def commit(ref, side):
        bb = crt_bbox(fps[ref])
        tht = any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in fps[ref].Pads())
        if ref[0] == "U" or ref in ("Q1", "L1", "Y1"):       # leave a routing channel around ICs
            g_ = 1.3 if ref == "U9" else 0.6                 # (the WLCSP needs room for its escape pattern)
            bb = (bb[0] - g_, bb[1] - g_, bb[2] + g_, bb[3] + g_)
        placed[side].append(bb)
        if tht and ref not in ("MK1", "MK2") and not ref.startswith("D"):
            placed["B" if side == "F" else "F"].append(bb)

    for ref, m in model.items():
        if m.get("pos"):
            FIXED[ref] = tuple(m["pos"])
    for ref, (x, y, rot, side) in FIXED.items():
        put(ref, x, y, rot, side); commit(ref, side)

    def padpos(ref, netname=None):
        out = []
        for p in fps[ref].Pads():
            if netname is None or p.GetNetname() == netname:
                q = p.GetPosition()
                out.append((pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY, p))
        return out

    done = set(FIXED)
    used_pwr = {}
    todo = [r for r in comps if r not in done]
    def prio(r):
        c = comps[r]
        sig = [n for n in c["pins"].values() if n not in POWER]
        big = crt_bbox(fps[r]); area = (big[2] - big[0]) * (big[3] - big[1])
        return (0 if r[0] in "QYL" else 1, -area if area > 6 else 0, 0 if sig else 1, r)
    # ICs' own decoupling first is handled by the per-pad balancing below
    for ref in sorted(todo, key=prio):
        c = comps[ref]; m = model.get(ref, {})
        near = m.get("near")
        mynets = list(dict.fromkeys(c["pins"].values()))
        sig = [n for n in mynets if n not in POWER and not n.startswith("unconnected")]
        target = None; tnet = None
        if near in fps and near in done:
            for n in sig:
                pp = padpos(near, n)
                if pp:
                    target = pp[0][:2]; tnet = n; break
            if target is None:
                for n in [x for x in mynets if x in ("+5V", "+3V3")] + [x for x in mynets if x == "GND"]:
                    pp = padpos(near, n)
                    if pp:
                        pp.sort(key=lambda q: used_pwr.get((near, q[2].GetNumber()), 0))
                        used_pwr[(near, pp[0][2].GetNumber())] = used_pwr.get((near, pp[0][2].GetNumber()), 0) + 1
                        target = pp[0][:2]; tnet = n; break
            if target is None:
                q = fps[near].GetPosition(); target = (pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY)
        elif near in ANCHOR_PTS:
            target = ANCHOR_PTS[near]
        if target is None or (tnet is None and sig):
            # any already placed pad on one of my signal nets
            best = None
            for n in sig:
                for r2 in done:
                    for q in padpos(r2, n):
                        dd = 0 if target is None else math.hypot(q[0] - target[0], q[1] - target[1])
                        if best is None or dd < best[0]:
                            best = (dd, q[:2], n)
            if best and (target is None or best[0] < 12):
                target, tnet = best[1], best[2]
        if target is None:
            target = (50.0, 20.0)
        fp = fps[ref]
        found = None
        offs = sorted(((dx * 0.4, dy * 0.4) for dx in range(-70, 71) for dy in range(-70, 71)),
                      key=lambda o: o[0] ** 2 + o[1] ** 2)
        for dx, dy in offs:
            x, y = round(target[0] + dx, 2), round(target[1] + dy, 2)
            if not (1.0 < x < W - 1.0 and 1.0 < y < H - 1.0):
                continue
            cand = None
            for rot in (0, 90, 180, 270):
                put(ref, x, y, rot, "F")
                bb = crt_bbox(fp)
                if bb[0] < 0.6 or bb[1] < 0.6 or bb[2] > W - 0.6 or bb[3] > H - 0.6:
                    continue
                if any(overlap(bb, b, 0.45) for b in placed["F"]) or any(overlap(bb, b) for b in NOGO_F):
                    continue
                if any(overlap(bb, (hx - 3.3, hy - 3.3, hx + 3.3, hy + 3.3)) for hx, hy in HOLES):
                    continue
                cost = 0.0
                if tnet:
                    pp = padpos(ref, tnet)
                    if pp:
                        cost = min(math.hypot(q[0] - target[0], q[1] - target[1]) for q in pp)
                if cand is None or cost < cand[0]:
                    cand = (cost, rot)
            if cand:
                found = (x, y, cand[1]); break
        if not found:
            raise RuntimeError("no room for " + ref)
        put(ref, found[0], found[1], found[2], "F"); commit(ref, "F"); done.add(ref)

    # ---- board outline (3 mm corner radius) ---------------------------------
    r = 3.0
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetWidth(MM(0.1)); board.Add(s)
    def arc(cx, cy, sx, sy, ang):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        s.SetWidth(MM(0.1)); board.Add(s)
    seg(r, 0, W - r, 0); seg(W, r, W, H - r); seg(W - r, H, r, H); seg(0, H - r, 0, r)
    arc(r, r, 0, r, 90); arc(W - r, r, W - r, 0, 90); arc(W - r, H - r, W, H - r, 90); arc(r, H - r, r, H, 90)
    def text(s, x, y, layer, size=1.0, rot=0):
        tx = pcbnew.PCB_TEXT(board); tx.SetText(s); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
        tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); tx.SetTextThickness(MM(size * 0.15))
        tx.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        if layer == pcbnew.B_SilkS: tx.SetMirrored(True)
        board.Add(tx)
    text("VoxHub CM4  rev A", 22.0, 41.0, pcbnew.F_SilkS, 1.2)
    text("github.com/geilevideossos-gamedev/fable-sbc-test", 22.0, 43.2, pcbnew.F_SilkS, 0.6)
    text("SPK", 8.6, 58.5, pcbnew.F_SilkS, 0.8, 90)
    text("GND TX RX", 80.0, 18.6, pcbnew.F_SilkS, 0.7)
    text("USB-C PD 9-20V", 13.0, 9.2, pcbnew.F_SilkS, 0.6)
    text("VoxHub CM4 rev A - this side faces the top cover", 60.0, 50.0, pcbnew.B_SilkS, 1.0)
    text("MUTE", 33.5, 57.0, pcbnew.B_SilkS, 0.8)
    # ---- mechanical drawing layer (exported to DXF): holes, ports, connector envelopes -----
    mech = [("feature", "ref", "x_mm", "y_mm", "detail")]
    def circle(x, y, d):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.Dwgs_User)
        s.SetCenter(P(x, y)); s.SetEnd(P(x + d / 2, y)); s.SetWidth(MM(0.1)); board.Add(s)
    def boxd(bb):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(pcbnew.Dwgs_User)
        s.SetStart(P(bb[0], bb[1])); s.SetEnd(P(bb[2], bb[3])); s.SetWidth(MM(0.1)); board.Add(s)
    fmm = pcbnew.ToMM
    for ref in sorted(fps):
        fp = fps[ref]; q = fp.GetPosition(); x, y = fmm(q.x) - OX, fmm(q.y) - OY
        if ref in ("H1", "H2", "H3", "H4"):
            circle(x, y, 2.7); text(ref, x, y - 2.2, pcbnew.Dwgs_User, 0.8); mech.append(("PCB mounting hole", ref, x, y, "2.7 mm NPTH (M2.5)"))
        elif ref in ("H5", "H6", "H7", "H8"):
            circle(x, y, 2.7); circle(x, y, 5.1); mech.append(("CM4 spacer", ref, x, y, "M2.5 SMT spacer, 1.5 mm high, hole 3.7 mm"))
        elif ref in ("J1", "J4", "J6", "J7", "J5", "SW1", "U11"):
            bb = crt_bbox(fp); boxd(bb); text(ref, (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, pcbnew.Dwgs_User, 0.8)
            mech.append(("connector/part envelope", ref, x, y, "courtyard %.2f,%.2f .. %.2f,%.2f; side %s" % (bb[0], bb[1], bb[2], bb[3], "B" if fp.IsFlipped() else "F")))
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and (ref.startswith("MK") or ref.startswith("D")):
                pq = pad.GetPosition(); px, py = fmm(pq.x) - OX, fmm(pq.y) - OY
                if ref.startswith("MK"):
                    circle(px, py, 0.8); circle(px, py, 5.0); mech.append(("microphone port", ref, px, py, "0.8 mm hole through PCB, sound enters from the side opposite the components"))
                else:
                    circle(px, py, 3.0); mech.append(("LED light slot", ref, px, py, "1.8 x 2.4 mm slot, reverse-mount LED shines to the side opposite the components"))
    boxd((CM4_X0 - 51.5, CM4_Y0 - 36.5, CM4_X0 + 3.5, CM4_Y0 + 3.5)); text("CM4 module outline", 71.5, 48.0, pcbnew.Dwgs_User, 1.2)
    mech.append(("CM4 module outline", "J2/J3", 71.5, 48.0, "55 x 40 mm, x 44..99, y 28..68, 1.5 mm above the PCB"))
    mech.append(("board outline", "-", 0.0, 0.0, "100 x 74 mm, origin = rear-left corner seen from the component side, 3 mm corner radius; KiCad page offset %.0f/%.0f mm" % (OX, OY)))
    import csv as _csv
    os.makedirs(os.path.join(outdir, "outputs"), exist_ok=True)
    with open(os.path.join(outdir, "outputs", "mechanical_positions.csv"), "w", newline="") as fh:
        w_ = _csv.writer(fh)
        for row in mech:
            w_.writerow([("%.3f" % v) if isinstance(v, float) else v for v in row])
    add_rule_areas(board)
    fanout(board)
    board.BuildConnectivity()
    board.Save(board.GetFileName()); write_project(outdir)
    json.dump({r: [round(pcbnew.ToMM(f.GetPosition().x) - OX, 3), round(pcbnew.ToMM(f.GetPosition().y) - OY, 3),
                   f.GetOrientationDegrees(), "B" if f.IsFlipped() else "F"] for r, f in fps.items()},
              open(os.path.join(outdir, "gen", "placement.json"), "w"), indent=0, sort_keys=True)
    print("placed", len(fps), "footprints")


# ---------------------------------------------------------------------------------------
# Power fan-out: every SMD pad on a plane net (GND -> In1, +5V -> In2) gets a short stub and
# a via (or shares a neighbour's via).  Done before autorouting so the router only has to
# deal with signals; the stubs/vias are locked and exported as fixed wiring.
# ---------------------------------------------------------------------------------------
PLANE_NETS = ("GND", "+5V")

def _pt_rect(px, py, r):
    dx = max(r[0] - px, 0.0, px - r[2]); dy = max(r[1] - py, 0.0, py - r[3])
    return math.hypot(dx, dy)

def _seg_rect(x1, y1, x2, y2, r):
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.05) + 1)
    return min(_pt_rect(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n, r) for i in range(n + 1))

def fanout(board):
    f = pcbnew.ToMM
    pads = []      # (net, layers 'F'/'B'/'*', bbox, pad)
    for fp in sorted_fps(board):
        for p in fp.Pads():
            b = p.GetBoundingBox()
            bb = (f(b.GetLeft()) - OX, f(b.GetTop()) - OY, f(b.GetRight()) - OX, f(b.GetBottom()) - OY)
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            if not th and not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)):
                continue                                       # paste-only apertures
            lay = "*" if th else ("F" if p.IsOnLayer(pcbnew.F_Cu) else "B")
            pads.append((p.GetNetname(), lay, bb, p))
    kos = board_keepouts(board)
    vias = []      # (net, x, y, dia)
    segs = []      # (net, layer, x1, y1, x2, y2, w)
    stats = dict(center=0, shared=0, new=0, failed=[])

    def via_ok(net, x, y, dia, own):
        if not (0.7 < x < W - 0.7 and 0.7 < y < H - 0.7):
            return False
        if any(k[0] - dia / 2 - 0.1 < x < k[2] + dia / 2 + 0.1 and k[1] - dia / 2 - 0.1 < y < k[3] + dia / 2 + 0.1 for k in kos):
            return False
        for n2, lay, bb, p in pads:
            if p is own:
                continue
            if abs((bb[0] + bb[2]) / 2 - x) > 6 or abs((bb[1] + bb[3]) / 2 - y) > 6:
                continue
            d = _pt_rect(x, y, bb) - dia / 2
            if n2 == net and lay != "*":
                if d < -dia * 0.25:        # do not sit half on a neighbouring same-net pad
                    return False
                continue
            if d < (0.25 if lay == "*" else 0.2):
                return False
        for n2, vx, vy, vd in vias:
            dd = math.hypot(vx - x, vy - y)
            if dd < (0.62 if n2 == net else (vd + dia) / 2 + 0.2):
                return False
        for n2, lay, x1, y1, x2, y2, w in segs:
            if n2 != net and _seg_rect(x1, y1, x2, y2, (x, y, x, y)) < dia / 2 + w / 2 + 0.15:
                return False
        return True

    def seg_ok(net, lay, x1, y1, x2, y2, w, own):
        if any(_seg_rect(x1, y1, x2, y2, k) < w / 2 + 0.1 and _pt_rect(x1, y1, k) > 0.05 for k in kos):
            return False
        for n2, l2, bb, p in pads:
            if p is own or n2 == net:
                continue
            if l2 not in ("*", lay):
                continue
            if abs((bb[0] + bb[2]) / 2 - x1) > 8 or abs((bb[1] + bb[3]) / 2 - y1) > 8:
                continue
            if _seg_rect(x1, y1, x2, y2, bb) < w / 2 + 0.15:
                return False
        for n2, vx, vy, vd in vias:
            if n2 != net and _seg_rect(x1, y1, x2, y2, (vx, vy, vx, vy)) < vd / 2 + w / 2 + 0.15:
                return False
        for n2, l2, a1, b1, a2, b2, w2 in segs:
            if n2 == net or l2 != lay:
                continue
            n = max(2, int(math.hypot(a2 - a1, b2 - b1) / 0.1) + 1)
            if min(_seg_rect(x1, y1, x2, y2, (a1 + (a2 - a1) * i / n,) * 1 + (b1 + (b2 - b1) * i / n,) +
                             (a1 + (a2 - a1) * i / n, b1 + (b2 - b1) * i / n)) for i in range(n + 1)) < (w + w2) / 2 + 0.15:
                return False
        return True

    for fp in sorted_fps(board):
        if fp.GetReference() != "U9":
            continue
        q0 = fp.GetPosition(); ux, uy = f(q0.x) - OX, f(q0.y) - OY
        esc = {"A1": [(-0.7, -0.6), (-1.2, -1.1)], "B1": [(-1.2, -0.2)], "C1": [(-1.5, 0.2)], "D1": [(-0.7, 0.6), (-1.2, 1.1)],
               "A2": [(0.7, -0.6), (1.2, -1.1)], "B2": [(1.0, -0.2)], "C2": [(1.5, 0.2)], "D2": [(0.7, 0.6), (1.2, 1.1)]}
        for pad in fp.Pads():
            if pad.GetNumber() not in esc:
                continue
            qp = pad.GetPosition(); last = (f(qp.x) - OX, f(qp.y) - OY)
            for ex, ey in esc[pad.GetNumber()]:
                segs.append((pad.GetNetname(), "F", last[0], last[1], ux + ex, uy + ey, 0.15)); last = (ux + ex, uy + ey)
            if pad.GetNetname() in PLANE_NETS:
                vias.append((pad.GetNetname(), last[0], last[1], 0.5))
    todo = [q for q in pads if q[0] in PLANE_NETS and q[1] in ("F", "B") and q[3].GetParentFootprint().GetReference() != "U9"]
    todo.sort(key=lambda q: (q[2][2] - q[2][0]) * (q[2][3] - q[2][1]))      # tightest pads first
    for net, lay, bb, p in todo:
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        w_, h_ = bb[2] - bb[0], bb[3] - bb[1]
        small = min(w_, h_) < 0.35
        dia, drill, tw = (0.5, 0.25, min(0.2, min(w_, h_))) if small else (0.6, 0.3, min(0.4, max(0.2, min(w_, h_) * 0.8)))
        fpr = p.GetParentFootprint()
        is_ep = fpr.GetReference().startswith("U") and p.GetNumber() == max(
            (q.GetNumber() for q in fpr.Pads() if q.GetNumber().isdigit()), key=int, default="")
        if is_ep and w_ * h_ >= 1.4:
            # large pad (exposed pad, bulk cap, inductor): via(s) in the pad
            n_v = 1 if w_ * h_ < 6 else 2
            for k in range(n_v):
                ox = (k - (n_v - 1) / 2) * min(1.2, w_ / 3) if w_ >= h_ else 0.0
                oy = (k - (n_v - 1) / 2) * min(1.2, h_ / 3) if h_ > w_ else 0.0
                if via_ok(net, cx + ox, cy + oy, 0.6, p):
                    vias.append((net, cx + ox, cy + oy, 0.6))
            stats["center"] += 1
            continue
        best = None
        if fpr.GetReference() in ("J2", "J3"):
            q0 = fpr.GetPosition(); ccy = f(q0.y) - OY
            for dxv in (0.0, 0.2, -0.2, 0.4, -0.4, 0.6, -0.6):
                for n2, vx, vy, vd in vias:
                    if n2 == net and abs(vy - ccy) < 0.01 and abs(vx - (cx + dxv)) < 0.01 and seg_ok(net, lay, cx, cy, vx, vy, tw, p):
                        best = (0.0, vx, vy, None); break
                if best: break
                if via_ok(net, cx + dxv, ccy, 0.5, p) and seg_ok(net, lay, cx, cy, cx + dxv, ccy, tw, p):
                    best = (0.0, cx + dxv, ccy, 0.5); break
        # 1) share an existing via of the same net
        for n2, vx, vy, vd in (vias if best is None else []):
            if n2 == net and math.hypot(vx - cx, vy - cy) < 2.2 and seg_ok(net, lay, cx, cy, vx, vy, tw, p):
                d = math.hypot(vx - cx, vy - cy)
                if best is None or d < best[0]:
                    best = (d, vx, vy, None)
        if best is None:
            # 2) new via: scan outwards
            rmin = max(w_, h_) / 2 + dia / 2 + 0.12 if not small else min(w_, h_) / 2 + 0.2
            for r in [rmin + 0.2 * i for i in range(0, 30)]:
                for a in range(0, 360, 15):
                    x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
                    if via_ok(net, x, y, dia, p) and seg_ok(net, lay, cx, cy, x, y, tw, p):
                        # prefer leaving a fine-pitch pad along its long axis
                        pen = 0.0
                        if small:
                            pen = abs(math.sin(math.radians(a))) if w_ > h_ else abs(math.cos(math.radians(a)))
                        if best is None or r + pen < best[0]:
                            best = (r + pen, x, y, dia)
                if best is not None:
                    break
        if best is None:
            stats["failed"].append("%s.%s(%s)" % (p.GetParentFootprint().GetReference(), p.GetNumber(), net))
            continue
        _, x, y, vd = best
        if vd:
            vias.append((net, x, y, vd)); stats["new"] += 1
        else:
            stats["shared"] += 1
        segs.append((net, lay, cx, cy, x, y, tw))

    for net, x, y, dia in vias:
        v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetWidth(pcbnew.F_Cu, MM(dia)) if hasattr(v, "SetWidth") else None
        v.SetDrill(MM(0.3 if dia >= 0.6 else 0.25)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(board.GetNetcodeFromNetname(net)); v.SetLocked(True)
        board.Add(v)
    for net, lay, x1, y1, x2, y2, w in segs:
        s = pcbnew.PCB_TRACK(board); s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetWidth(MM(w))
        s.SetLayer(pcbnew.F_Cu if lay == "F" else pcbnew.B_Cu); s.SetNetCode(board.GetNetcodeFromNetname(net)); s.SetLocked(True)
        board.Add(s)
    print("fanout: %d pads, %d vias (%d in-pad groups, %d shared stubs), failed: %s" %
          (len(todo), len(vias), stats["center"], stats["shared"], stats["failed"]))

def poly_zone(board, pts, layers, netname=None, keepout=False, name="", prio=0, clearance=0.25, minw=0.2):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(l)
    z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(MM(OX + x), MM(OY + y))
    z.SetZoneName(name)
    if keepout:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    else:
        z.SetNetCode(board.GetNetcodeFromNetname(netname))
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clearance)); z.SetMinThickness(MM(minw))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
    return z

ALL_CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
def rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def add_rule_areas(board):
    f = pcbnew.ToMM
    # MGM240P antenna clearance: no copper on any layer (footprint-local x -4.4..4.4, y -7.5..-2.7, module rotated 180)
    poly_zone(board, rect(19.6, 69.2, 28.4, 74.0), ALL_CU, keepout=True, name="KO_ZIGBEE_ANT")
    # CM4 on-board WiFi/BT antenna corner: no copper on any layer (>= 6.5 x 11 mm per CM4 datasheet)
    poly_zone(board, rect(90.0, 35.0, 100.0, 47.0), ALL_CU, keepout=True, name="KO_CM4_ANT")
    # keep routed copper 0.35 mm away from the board edge (pads of edge connectors are still allowed)
    e = 0.35
    for i, r_ in enumerate((rect(0, 0, W, e), rect(0, H - e, W, H), rect(0, 0, e, H), rect(W - e, 0, W, H))):
        poly_zone(board, r_, ALL_CU, keepout=True, name="KO_EDGE%d" % i)
    for fp in sorted_fps(board):
        ref = fp.GetReference()
        q = fp.GetPosition(); x, y = f(q.x) - OX, f(q.y) - OY
        if ref.startswith("FID"):          # fiducial: 2 mm mask opening must stay free of other copper
            poly_zone(board, rect(x - 1.2, y - 1.2, x + 1.2, y + 1.2), (pcbnew.F_Cu,), keepout=True, name="KO_" + ref)
        for pad in fp.Pads():              # non-plated slots/holes inside parts (LED light slots, mic ports)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and (ref.startswith("D") or ref.startswith("MK")):
                b = pad.GetBoundingBox()
                poly_zone(board, rect(f(b.GetLeft()) - OX - 0.3, f(b.GetTop()) - OY - 0.3, f(b.GetRight()) - OX + 0.3, f(b.GetBottom()) - OY + 0.3),
                          ALL_CU, keepout=True, name="KO_HOLE_" + ref)

def board_keepouts(board):
    f = pcbnew.ToMM
    out = []
    for z in list(board.Zones()) + [z for fp in sorted_fps(board) for z in fp.Zones()]:
        if z.GetIsRuleArea():
            b = z.GetBoundingBox()
            out.append((f(b.GetLeft()) - OX, f(b.GetTop()) - OY, f(b.GetRight()) - OX, f(b.GetBottom()) - OY))
    return out

def add_planes(board):
    full = rect(0, 0, W, H)
    poly_zone(board, full, (pcbnew.In1_Cu,), "GND", name="GND_PLANE")
    poly_zone(board, full, (pcbnew.In2_Cu,), "+5V", name="5V_PLANE")
    poly_zone(board, full, (pcbnew.F_Cu,), "GND", name="GND_F")
    poly_zone(board, full, (pcbnew.B_Cu,), "GND", name="GND_B")

def finish(outdir):
    board = pcbnew.LoadBoard(os.path.join(outdir, "voxhub.kicad_pcb"))
    ses = os.path.join(outdir, "gen", "work", "voxhub.ses")
    if os.path.exists(ses):
        ok = pcbnew.ImportSpecctraSES(board, ses)
        print("SES import:", ok)
    tracks = sorted_tracks(board); _KEEP.append(tracks)
    for tr in tracks:
        if tr.Type() != pcbnew.PCB_VIA_T and tr.GetWidth() < MM(0.1):
            tr.SetWidth(MM(0.1))
        if tr.IsLocked() and tr.GetNetname() not in PLANE_NETS:
            tr.SetLocked(False)
    print("dangling items removed:", cleanup(board, tracks))
    if not [z for z in board.Zones() if not z.GetIsRuleArea()]:
        add_planes(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    board.Save(board.GetFileName()); write_project(outdir)
    print("unconnected:", board.GetConnectivity().GetUnconnectedCount(True))


# ---------------------------------------------------------------------------------------
# Local copper pours for the high-current nets (convex hull of the net's pads on F.Cu).
# ---------------------------------------------------------------------------------------
def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]

POUR_NETS = ("VBUS", "VBUS_SW", "BUCK_SW", "USB1_VBUS", "USB2_VBUS")

def add_power_pours(board):
    f = pcbnew.ToMM
    corners = {}
    def add(net, pad):
        b = pad.GetBoundingBox()
        x0, y0, x1, y1 = f(b.GetLeft()) - OX, f(b.GetTop()) - OY, f(b.GetRight()) - OX, f(b.GetBottom()) - OY
        corners.setdefault(net, []).extend([(x0 - 0.3, y0 - 0.3), (x1 + 0.3, y0 - 0.3), (x1 + 0.3, y1 + 0.3), (x0 - 0.3, y1 + 0.3)])
    l1 = None
    for fp in sorted_fps(board):
        if fp.GetReference() == "L1":
            q = fp.GetPosition(); l1 = (f(q.x) - OX, f(q.y) - OY)
    for fp in sorted_fps(board):
        for pad in fp.Pads():
            n = pad.GetNetname()
            if not pad.IsOnLayer(pcbnew.F_Cu):
                continue
            if n in POUR_NETS:
                add(n, pad)
            elif n == "+5V" and l1:        # buck output: tie inductor, output caps and their plane vias together
                q = pad.GetPosition()
                if math.hypot(f(q.x) - OX - l1[0], f(q.y) - OY - l1[1]) < 13.0 and fp.GetReference()[0] in "LC":
                    add("+5V", pad)
    for i, (net, pts) in enumerate(sorted(corners.items())):
        h = [(min(max(x, 0.5), W - 0.5), min(max(y, 0.5), H - 0.5)) for x, y in _hull(pts)]
        if len(h) >= 3:
            z = poly_zone(board, h, (pcbnew.F_Cu,), net, name="POUR_" + net, prio=5 + i, clearance=0.2)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

# ---------------------------------------------------------------------------------------
# Patch router: completes whatever the autorouter left open.  For every net it computes the
# connected components (pads / tracks / vias; plane nets are joined through their vias) and
# joins them one by one with an A* search on a 0.05 mm grid (two layers, obstacles inflated
# by clearance).  If no free path exists it may rip up other routed tracks; the nets it
# breaks are re-joined in a later iteration.
# ---------------------------------------------------------------------------------------
def _geom(board, tracks):
    f = pcbnew.ToMM
    pads = []
    for fp in sorted_fps(board):
        for p in fp.Pads():
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            if not th and not (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)):
                continue
            b = p.GetBoundingBox(); q = p.GetPosition()
            pads.append(dict(net=p.GetNetname(), lay="*" if th else ("F" if p.IsOnLayer(pcbnew.F_Cu) else "B"),
                             bb=(f(b.GetLeft()) - OX, f(b.GetTop()) - OY, f(b.GetRight()) - OX, f(b.GetBottom()) - OY),
                             x=f(q.x) - OX, y=f(q.y) - OY, npth=p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH,
                             name=fp.GetReference() + "." + p.GetNumber()))
    items = []
    for i, tr in enumerate(tracks):
        if tr is None:
            continue
        fixed = tr.IsLocked() or tr.GetNetname() in PLANE_NETS
        if tr.Type() == pcbnew.PCB_VIA_T:
            q = tr.GetPosition()
            items.append(dict(i=i, kind="via", net=tr.GetNetname(), x=f(q.x) - OX, y=f(q.y) - OY, r=f(tr.GetWidth(pcbnew.F_Cu)) / 2, fixed=fixed))
        else:
            a, e = tr.GetStart(), tr.GetEnd()
            lay = "F" if tr.GetLayer() == pcbnew.F_Cu else ("B" if tr.GetLayer() == pcbnew.B_Cu else "?")
            items.append(dict(i=i, kind="seg", net=tr.GetNetname(), x1=f(a.x) - OX, y1=f(a.y) - OY, x2=f(e.x) - OX, y2=f(e.y) - OY,
                              hw=f(tr.GetWidth()) / 2, lay=lay, fixed=fixed))
    return pads, items

def _pt_seg(x, y, o):
    dx, dy = o["x2"] - o["x1"], o["y2"] - o["y1"]; L2 = dx * dx + dy * dy
    tt = 0.0 if L2 == 0 else min(1.0, max(0.0, ((x - o["x1"]) * dx + (y - o["y1"]) * dy) / L2))
    return math.hypot(x - (o["x1"] + tt * dx), y - (o["y1"] + tt * dy))

def _components(net, pads, items):
    """Union-find over the pads / segments / vias of one net.  Returns list of components,
    each a dict(pads=[...], pts=[(x, y, lay)...])."""
    np_ = [p for p in pads if p["net"] == net and not p["npth"]]
    ni = [o for o in items if o["net"] == net]
    n = len(np_) + len(ni)
    par = list(range(n))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    def uni(a, b): par[find(a)] = find(b)
    T = 0.005
    def inpad(p, x, y, lay): return p["lay"] in ("*", lay) and p["bb"][0] - T <= x <= p["bb"][2] + T and p["bb"][1] - T <= y <= p["bb"][3] + T
    plane = None
    for k, o in enumerate(ni):
        ko = len(np_) + k
        ends = [(o["x"], o["y"], "F"), (o["x"], o["y"], "B")] if o["kind"] == "via" else [(o["x1"], o["y1"], o["lay"]), (o["x2"], o["y2"], o["lay"])]
        for (x, y, lay) in ends:
            for j, p in enumerate(np_):
                if inpad(p, x, y, lay): uni(ko, j)
            for k2, o2 in enumerate(ni):
                if k2 == k: continue
                if o2["kind"] == "via":
                    if math.hypot(o2["x"] - x, o2["y"] - y) <= o2["r"] + T: uni(ko, len(np_) + k2)
                elif o2["lay"] == lay and _pt_seg(x, y, o2) <= o2["hw"] + T:
                    uni(ko, len(np_) + k2)
        if net in PLANE_NETS and o["kind"] == "via":       # all vias of a plane net meet in the plane
            if plane is None: plane = ko
            else: uni(ko, plane)
    if net in PLANE_NETS:
        for j, p in enumerate(np_):
            if p["lay"] == "*":
                if plane is None: plane = j
                else: uni(j, plane)
    comps = {}
    for j, p in enumerate(np_):
        c = comps.setdefault(find(j), dict(pads=[], pts=[], plane=False))
        c["pads"].append(p)
        for lay in (("F", "B") if p["lay"] == "*" else (p["lay"],)):
            c["pts"].append((p["x"], p["y"], lay))
    for k, o in enumerate(ni):
        r = find(len(np_) + k)
        if r not in comps: continue          # stray copper without a pad (cleanup removes it)
        c = comps[r]
        if o["kind"] == "via": c["pts"] += [(o["x"], o["y"], "F"), (o["x"], o["y"], "B")]
        else: c["pts"] += [(o["x1"], o["y1"], o["lay"]), (o["x2"], o["y2"], o["lay"])]
    if plane is not None and find(plane) in comps:
        comps[find(plane)]["plane"] = True
    return list(comps.values())

def patch(outdir, report=None, max_jobs=400, reroute=()):
    import heapq
    import numpy as np
    board = pcbnew.LoadBoard(os.path.join(outdir, "voxhub.kicad_pcb"))
    tracks = sorted_tracks(board); _KEEP.append(tracks)
    if reroute:          # rip the given nets completely; they are then re-joined below by shortest paths
        n_rip = 0
        for i_, tr in enumerate(tracks):
            if tr is not None and tr.GetNetname() in reroute and not tr.IsLocked():
                board.Remove(tr); _KEEP.append(tr); tracks[i_] = None; n_rip += 1
        print("  ripped %d items of %s for re-routing" % (n_rip, list(reroute)))
    cleanup(board, tracks)
    kos = board_keepouts(board)
    G = 0.05; VR = 0.25
    nets = sorted({p.GetNetname() for fp in sorted_fps(board) for p in fp.Pads() if p.GetNetname() and not p.GetNetname().startswith("unconnected-")})
    queue = [n_ for n_ in reroute if n_ in nets] + [n_ for n_ in nets if n_ not in reroute]
    usb = set(NETCLASSES["USB"][2])
    stats = dict(joined=0, failed=[], ripped=0)
    tries = {}
    jobs = 0
    protect = {}      # track index -> job number until which it may not be ripped up (stops A-rips-B-rips-A loops)
    while queue and jobs < max_jobs:
        net = queue.pop(0)
        pads, items = _geom(board, tracks)
        comps = _components(net, pads, items)
        if len(comps) < 2:
            continue
        jobs += 1
        # join the component with the fewest pads to its nearest neighbour
        comps.sort(key=lambda c: (c["plane"], len(c["pads"])))
        A = comps[0]
        def cdist(c):
            return min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in A["pts"][:60] for b in c["pts"][:400])
        Bc = min(comps[1:], key=cdist)
        ap = A["pts"]
        # goals: the points of B closest to A (bounded), sources: all points of A
        bp = sorted(Bc["pts"], key=lambda b: min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in ap[:60]))[:40]
        power = net in NETCLASSES["Power"][2]
        done = False
        # (track width, clearance used for the search); the last entry is the tightest the board rules allow
        if net in usb:      # USB 2.0 data: 0.2 mm (about 45 ohm to the plane 0.1 mm below), stay on one layer if at all possible
            variants = ((0.2, 0.16), (0.2, 0.13))
        elif power:
            variants = ((0.3, 0.18), (0.15, 0.18), (0.12, 0.165))
        else:
            variants = ((0.15, 0.15), (0.12, 0.13))
        via_cost = 400 if net in usb else 50
        for width, clr in variants:
            xs = [q[0] for q in ap + bp]; ys = [q[1] for q in ap + bp]
            m = 4.0 + 2.0 * tries.get(net, 0)
            x0, y0, x1, y1 = max(0.4, min(xs) - m), max(0.4, min(ys) - m), min(W - 0.4, max(xs) + m), min(H - 0.4, max(ys) + m)
            nx, ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
            XX, YY = np.meshgrid(x0 + np.arange(nx) * G, y0 + np.arange(ny) * G, indexing="ij")
            hard = [np.zeros((nx, ny), bool), np.zeros((nx, ny), bool)]
            hardv = np.zeros((nx, ny), bool)
            soft = [np.zeros((nx, ny), bool), np.zeros((nx, ny), bool)]
            softv = np.zeros((nx, ny), bool)
            free = [np.zeros((nx, ny), bool), np.zeros((nx, ny), bool)]
            absh = [np.zeros((nx, ny), bool), np.zeros((nx, ny), bool)]     # holes / keep-outs: never passable, even inside our own pad
            LI = {"F": 0, "B": 1}
            def box_idx(bx0, by0, bx1, by1):
                i0, i1 = max(0, int(math.ceil((bx0 - x0) / G))), min(nx, int(math.floor((bx1 - x0) / G)) + 1)
                j0, j1 = max(0, int(math.ceil((by0 - y0) / G))), min(ny, int(math.floor((by1 - y0) / G)) + 1)
                if i1 <= i0 or j1 <= j0:
                    return 0, 0, 0, 0            # empty (never let a negative stop index wrap around)
                return i0, i1, j0, j1
            for pd in pads:
                bb = pd["bb"]
                if bb[2] < x0 - 1 or bb[0] > x1 + 1 or bb[3] < y0 - 1 or bb[1] > y1 + 1: continue
                lays = (0, 1) if pd["lay"] == "*" else (LI[pd["lay"]],)
                if pd["net"] == net and not pd["npth"]:
                    i0, i1, j0, j1 = box_idx(*bb)
                    for L in lays: free[L][i0:i1, j0:j1] = True
                    if pd["lay"] != "*":                                  # no via in / half on our own SMD pad
                        i0, i1, j0, j1 = box_idx(bb[0] - VR, bb[1] - VR, bb[2] + VR, bb[3] + VR); hardv[i0:i1, j0:j1] = True
                    continue
                mrg = (0.3 if pd["npth"] else clr) + width / 2
                i0, i1, j0, j1 = box_idx(bb[0] - mrg, bb[1] - mrg, bb[2] + mrg, bb[3] + mrg)
                for L in lays: hard[L][i0:i1, j0:j1] = True
                if pd["npth"]:
                    for L in lays: absh[L][i0:i1, j0:j1] = True
                mv = (0.3 if pd["npth"] else 0.2) + VR
                i0, i1, j0, j1 = box_idx(bb[0] - mv, bb[1] - mv, bb[2] + mv, bb[3] + mv); hardv[i0:i1, j0:j1] = True
            for k in kos:
                i0, i1, j0, j1 = box_idx(k[0] - width / 2, k[1] - width / 2, k[2] + width / 2, k[3] + width / 2)
                hard[0][i0:i1, j0:j1] = True; hard[1][i0:i1, j0:j1] = True
                absh[0][i0:i1, j0:j1] = True; absh[1][i0:i1, j0:j1] = True
                i0, i1, j0, j1 = box_idx(k[0] - VR, k[1] - VR, k[2] + VR, k[3] + VR); hardv[i0:i1, j0:j1] = True
            for o in items:
                if o["kind"] == "via": ax, ay, bx, by, hw, lays = o["x"], o["y"], o["x"], o["y"], o["r"], (0, 1)
                else:
                    if o["lay"] not in LI: continue
                    ax, ay, bx, by, hw, lays = o["x1"], o["y1"], o["x2"], o["y2"], o["hw"], (LI[o["lay"]],)
                rr = hw + 0.2 + VR + 0.05
                if max(ax, bx) < x0 - rr or min(ax, bx) > x1 + rr or max(ay, by) < y0 - rr or min(ay, by) > y1 + rr: continue
                i0, i1, j0, j1 = box_idx(min(ax, bx) - rr, min(ay, by) - rr, max(ax, bx) + rr, max(ay, by) + rr)
                if i0 >= i1 or j0 >= j1: continue
                X_, Y_ = XX[i0:i1, j0:j1], YY[i0:i1, j0:j1]
                dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
                tt = np.clip(((X_ - ax) * dx + (Y_ - ay) * dy) / L2, 0, 1) if L2 > 0 else 0.0
                dist = np.hypot(X_ - (ax + tt * dx), Y_ - (ay + tt * dy))
                if o["net"] == net:
                    if o["kind"] == "via": hardv[i0:i1, j0:j1] |= dist < 0.62      # hole-to-hole for same-net vias
                    for L in lays: free[L][i0:i1, j0:j1] |= dist <= max(0.0, hw - width / 2)
                    continue
                tgt, tgtv = (hard, hardv) if (o["fixed"] or protect.get(o["i"], 0) > jobs) else (soft, softv)
                for L in lays: tgt[L][i0:i1, j0:j1] |= dist < hw + clr + width / 2
                tgtv[i0:i1, j0:j1] |= dist < hw + 0.2 + VR
            edge = 0.36 + width / 2
            em = (XX < edge) | (XX > W - edge) | (YY < edge) | (YY > H - edge)
            for L in (0, 1): hard[L] |= em & ~free[L]
            hardv |= (XX < 0.75) | (XX > W - 0.75) | (YY < 0.75) | (YY > H - 0.75)
            def cell(x, y): return (min(nx - 1, max(0, int(round((x - x0) / G)))), min(ny - 1, max(0, int(round((y - y0) / G)))))
            starts = {cell(q[0], q[1]) + (LI[q[2]],): q for q in ap if q[2] in LI}
            goals = {cell(q[0], q[1]) + (LI[q[2]],): q for q in bp if q[2] in LI}
            gl = list(goals)
            for (cx_, cy_, cl_) in list(starts) + gl: free[cl_][cx_, cy_] = True
            for L in (0, 1):
                keep = np.zeros((nx, ny), bool)
                for (cx_, cy_, cl_) in list(starts) + gl:
                    if cl_ == L: keep[cx_, cy_] = True
                free[L] &= ~absh[L] | keep
                hard[L] |= absh[L] & ~keep
            def h(c):
                return min(max(abs(c[0] - g[0]), abs(c[1] - g[1])) + 0.414 * min(abs(c[0] - g[0]), abs(c[1] - g[1])) for g in gl)
            found = None
            for ripup in (False, True):
                openh = [(1.5 * h(s), 0.0, s, None) for s in starts]; heapq.heapify(openh)
                came = {}; best = {}; it = 0
                while openh and it < 3000000:
                    _, gsc, c, par_ = heapq.heappop(openh); it += 1
                    if c in came: continue
                    came[c] = par_
                    if c in goals: found = c; break
                    cx, cy, cl = c
                    hd, sf, fr = hard[cl], soft[cl], free[cl]
                    for dx, dy, cost in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)):
                        ux, uy = cx + dx, cy + dy
                        if not (0 <= ux < nx and 0 <= uy < ny): continue
                        if not fr[ux, uy]:
                            if hd[ux, uy]: continue
                            if sf[ux, uy]:
                                if not ripup: continue
                                cost += 40
                        n2 = (ux, uy, cl); g2 = gsc + cost
                        if n2 not in came and g2 < best.get(n2, 1e18):
                            best[n2] = g2; heapq.heappush(openh, (g2 + 1.5 * h(n2), g2, n2, c))
                    if not hardv[cx, cy] and not hard[1 - cl][cx, cy] and not (hard[cl][cx, cy] and not free[cl][cx, cy]):
                        vc = via_cost
                        if softv[cx, cy] or soft[0][cx, cy] or soft[1][cx, cy]:
                            vc = via_cost + 200 if ripup else None
                        if vc is not None:
                            n2 = (cx, cy, 1 - cl); g2 = gsc + vc
                            if n2 not in came and g2 < best.get(n2, 1e18):
                                best[n2] = g2; heapq.heappush(openh, (g2 + 1.5 * h(n2), g2, n2, c))
                if found: break
            if not found:
                print("    no path for %s (w %.2f): searched %d cells, window %dx%d, starts %s goals %s" % (
                    net, width, len(came), nx, ny, [(round(q[0], 2), round(q[1], 2), q[2]) for q in list(starts.values())[:3]],
                    [(round(q[0], 2), round(q[1], 2), q[2]) for q in list(goals.values())[:3]]))
                continue
            path = []; c = found
            while c is not None: path.append(c); c = came[c]
            path.reverse()
            # string pulling: replace stair-steps by straight segments where the straight line is free
            def los(a, b):
                (ax, ay, al), (bx, by, bl) = a, b
                n = max(1, int(max(abs(bx - ax), abs(by - ay)) * 3))
                hd, sf, fr = hard[al], soft[al], free[al]
                for k in range(n + 1):
                    ix, iy = int(round(ax + (bx - ax) * k / n)), int(round(ay + (by - ay) * k / n))
                    if not fr[ix, iy] and (hd[ix, iy] or sf[ix, iy]): return False
                return True
            sm = [path[0]]; i = 0
            while i < len(path) - 1:
                j = i + 1
                if path[j][2] == path[i][2]:
                    k = j
                    while k + 1 < len(path) and path[k + 1][2] == path[i][2] and k - i < 400:
                        k += 1
                        if los(path[i], path[k]): j = k
                sm.append(path[j]); i = j
            pts = [(x0 + c[0] * G, y0 + c[1] * G, c[2]) for c in sm]
            s_exact, g_exact = starts[path[0]], goals[found]
            if os.environ.get("PATCH_DEBUG"):
                print("    DEBUG", net, "start", s_exact, "goal", g_exact, "cells", len(path), "sm", [(round(x0 + c[0] * G, 2), round(y0 + c[1] * G, 2), c[2]) for c in sm])
            pts = [(s_exact[0], s_exact[1], pts[0][2])] + pts + [(g_exact[0], g_exact[1], pts[-1][2])]
            # victims: every rippable item the new copper comes too close to (exact geometry)
            dense = [(x0 + c[0] * G, y0 + c[1] * G, c[2]) for c in path]
            newv = [pts[k] for k in range(1, len(pts)) if pts[k][2] != pts[k - 1][2]]
            victims, bad = [], False
            for o in items:
                if o["net"] == net: continue
                hit = False
                if o["kind"] == "via":
                    for (px_, py_, pl_) in dense:
                        if not free[pl_][cell(px_, py_)] and math.hypot(o["x"] - px_, o["y"] - py_) < o["r"] + clr + width / 2 - 0.03: hit = True; break
                    if not hit and any(math.hypot(o["x"] - v[0], o["y"] - v[1]) < o["r"] + VR + 0.18 for v in newv): hit = True
                else:
                    if o["lay"] not in LI: continue
                    if max(o["x1"], o["x2"]) < x0 or min(o["x1"], o["x2"]) > x1 or max(o["y1"], o["y2"]) < y0 or min(o["y1"], o["y2"]) > y1: continue
                    li = LI[o["lay"]]
                    for (px_, py_, pl_) in dense:
                        if pl_ == li and not free[pl_][cell(px_, py_)] and _pt_seg(px_, py_, o) < o["hw"] + clr + width / 2 - 0.03: hit = True; break
                    if not hit and any(_pt_seg(v[0], v[1], o) < o["hw"] + VR + 0.18 for v in newv): hit = True
                if hit:
                    if o["fixed"] or protect.get(o["i"], 0) > jobs: bad = True; break
                    victims.append(o)
            if bad:
                continue
            for o in victims:
                board.Remove(tracks[o["i"]]); _KEEP.append(tracks[o["i"]]); tracks[o["i"]] = None
            code = board.GetNetcodeFromNetname(net)
            n_before = len(tracks)
            for a, b_ in zip(pts, pts[1:]):
                if a[2] != b_[2]:
                    v = pcbnew.PCB_VIA(board); v.SetPosition(P(a[0], a[1])); v.SetWidth(pcbnew.F_Cu, MM(0.5)); v.SetDrill(MM(0.25))
                    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code); board.Add(v); tracks.append(v)
                elif math.hypot(a[0] - b_[0], a[1] - b_[1]) > 1e-6:
                    s = pcbnew.PCB_TRACK(board); s.SetStart(P(a[0], a[1])); s.SetEnd(P(b_[0], b_[1])); s.SetWidth(MM(width))
                    s.SetLayer(pcbnew.F_Cu if a[2] == 0 else pcbnew.B_Cu); s.SetNetCode(code); board.Add(s); tracks.append(s)
            if victims:
                for ti in range(n_before, len(tracks)): protect[ti] = jobs + 12
            stats["joined"] += 1; stats["ripped"] += len(victims)
            vn = sorted({o["net"] for o in victims})
            print("  joined %-12s %s -> %s  (%d segments, w %.2f%s)" % (net, A["pads"][0]["name"], Bc["pads"][0]["name"] if Bc["pads"] else "?",
                  len(pts) - 1, width, (", ripped %d of %s" % (len(victims), vn)) if victims else ""))
            if victims:
                cleanup(board, tracks)
                for v_ in vn:
                    if v_ not in queue: queue.append(v_)
            done = True
            break
        if done:
            queue.insert(0, net)        # the net may have more components
        else:
            tries[net] = tries.get(net, 0) + 1
            if tries[net] < 3: queue.append(net)
            else:
                stats["failed"].append(net); print("  FAILED", net, A["pads"][0]["name"])
    rm = cleanup(board, tracks)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    board.Save(board.GetFileName()); write_project(outdir)
    print("patch: joined %d, ripped %d, failed %s, dangling removed %d; KiCad unconnected: %d" % (
        stats["joined"], stats["ripped"], sorted(set(stats["failed"])), rm, board.GetConnectivity().GetUnconnectedCount(True)))

_KEEP = []   # keep removed SWIG wrappers alive (their destruction confuses pcbnew's type map)

def cleanup(board, tracks):
    """Remove dangling track stubs and vias (left over by the autorouter or by rip-up).
    Works on plain Python copies of the geometry and deletes the board items in one go.
    `tracks` is the caller's list of track objects (None entries = already removed)."""
    f = pcbnew.ToMM
    pads = {}
    for fp in sorted_fps(board):
        for p in fp.Pads():
            if p.GetNetname():
                b = p.GetBoundingBox()
                th = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                lay = "*" if th else ("F" if p.IsOnLayer(pcbnew.F_Cu) else "B")
                pads.setdefault(p.GetNetname(), []).append((f(b.GetLeft()), f(b.GetTop()), f(b.GetRight()), f(b.GetBottom()), lay))
    items = {}     # net -> list of dicts
    for tr in tracks:
        if tr is None: continue
        d = dict(obj=tr, locked=tr.IsLocked(), alive=True)
        if tr.Type() == pcbnew.PCB_VIA_T:
            q = tr.GetPosition()
            d.update(kind="via", x=f(q.x), y=f(q.y), r=f(tr.GetWidth(pcbnew.F_Cu)) / 2)
        else:
            a, e = tr.GetStart(), tr.GetEnd()
            d.update(kind="seg", x1=f(a.x), y1=f(a.y), x2=f(e.x), y2=f(e.y), hw=f(tr.GetWidth()) / 2,
                     lay="F" if tr.GetLayer() == pcbnew.F_Cu else "B")
        items.setdefault(tr.GetNetname(), []).append(d)
    dead = []
    trimmed = [0]
    ox_ = oy_ = 0.0      # geometry here is in absolute KiCad coordinates
    for net, its in items.items():
        def touches(x, y, lay, me):
            for bb in pads.get(net, ()):
                if bb[4] in ("*", lay) and bb[0] - 0.02 <= x <= bb[2] + 0.02 and bb[1] - 0.02 <= y <= bb[3] + 0.02:
                    return True
            for o in its:
                if o is me or not o["alive"]:
                    continue
                if o["kind"] == "via":
                    if math.hypot(o["x"] - x, o["y"] - y) <= o["r"] + 0.01:
                        return True
                elif o["lay"] == lay:
                    if abs((o["x1"] + o["x2"]) / 2 - x) > abs(o["x2"] - o["x1"]) / 2 + 0.5 or abs((o["y1"] + o["y2"]) / 2 - y) > abs(o["y2"] - o["y1"]) / 2 + 0.5:
                        continue
                    dx, dy = o["x2"] - o["x1"], o["y2"] - o["y1"]; L2 = dx * dx + dy * dy
                    tt = 0.0 if L2 == 0 else min(1.0, max(0.0, ((x - o["x1"]) * dx + (y - o["y1"]) * dy) / L2))
                    if math.hypot(x - (o["x1"] + tt * dx), y - (o["y1"] + tt * dy)) <= o["hw"] + 0.02:
                        return True
            return False
        def junction(o, fx, fy, cx_, cy_):
            """Farthest point (from the connected end cx_,cy_) at which another item of the net meets segment o."""
            best = None
            for q in its:
                if q is o or not q["alive"]: continue
                cand = [(q["x"], q["y"])] if q["kind"] == "via" else ([(q["x1"], q["y1"]), (q["x2"], q["y2"])] if q["lay"] == o["lay"] else [])
                for (px, py) in cand:
                    if _pt_seg(px, py, o) <= 0.01:
                        d_ = math.hypot(px - cx_, py - cy_)
                        if d_ > 0.02 and (best is None or d_ > best[0]): best = (d_, px, py)
            return best
        changed = True
        while changed:
            changed = False
            for o in its:
                if not o["alive"] or o["locked"]:
                    continue
                if o["kind"] == "seg":
                    t1, t2 = touches(o["x1"], o["y1"], o["lay"], o), touches(o["x2"], o["y2"], o["lay"], o)
                    if t1 != t2:      # exactly one free end: try to trim back to the last junction
                        j = junction(o, 0, 0, o["x1"], o["y1"]) if t1 else junction(o, 0, 0, o["x2"], o["y2"])
                        if j is not None:
                            if t1:
                                o["x2"], o["y2"] = j[1], j[2]; o["obj"].SetEnd(pcbnew.VECTOR2I(MM(j[1] + ox_), MM(j[2] + oy_)))
                            else:
                                o["x1"], o["y1"] = j[1], j[2]; o["obj"].SetStart(pcbnew.VECTOR2I(MM(j[1] + ox_), MM(j[2] + oy_)))
                            trimmed[0] += 1; changed = True
                            continue
                    bad = not t1 or not t2
                else:
                    bad = net not in PLANE_NETS and not (touches(o["x"], o["y"], "F", o) and touches(o["x"], o["y"], "B", o))
                if bad:
                    o["alive"] = False; dead.append(o["obj"]); changed = True
    for o in dead:
        board.Remove(o); _KEEP.append(o)
        for i_, x_ in enumerate(tracks):
            if x_ is o: tracks[i_] = None
    return len(dead)


def repair(outdir, report):
    """DRC-driven repair: delete (unlocked) routed items that take part in an error; the
    affected connections are re-routed by the next patch round."""
    import re
    board = pcbnew.LoadBoard(os.path.join(outdir, "voxhub.kicad_pcb"))
    f = pcbnew.ToMM
    tracks = sorted_tracks(board); _KEEP.append(tracks)
    txt = open(report).read()
    kinds = ("clearance", "shorting_items", "tracks_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance",
             "track_dangling", "via_dangling", "items_not_allowed", "solder_mask_bridge", "track_width")
    gone = set()
    def find(desc, x, y):
        m = re.match(r"(Track|Via) \[([^\]]+)\]", desc)
        if not m: return None
        best = None
        for i, tr in enumerate(tracks):
            if tr is None or i in gone or tr.GetNetname() != m.group(2): continue
            isvia = tr.Type() == pcbnew.PCB_VIA_T
            if isvia != (m.group(1) == "Via"): continue
            if isvia:
                q = tr.GetPosition(); d = math.hypot(f(q.x) - x, f(q.y) - y)
            else:
                a, e = tr.GetStart(), tr.GetEnd()
                d = _seg_rect(f(a.x), f(a.y), f(e.x), f(e.y), (x, y, x, y))
            if best is None or d < best[0]: best = (d, i)
        return best[1] if best and best[0] < 0.6 else None
    n = 0
    for blk in re.split(r"\n(?=\[)", txt):
        m = re.match(r"\[(\w+)\]", blk)
        if not m or m.group(1) not in kinds: continue
        its = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)", blk)
        cands = []
        for x, y, desc in its:
            i = find(desc, float(x), float(y))
            if i is not None and not tracks[i].IsLocked() and tracks[i].GetNetname() not in PLANE_NETS:
                cands.append(i)
        if cands:
            i = cands[-1]
            board.Remove(tracks[i]); _KEEP.append(tracks[i]); gone.add(i); tracks[i] = None; n += 1
    rm = cleanup(board, tracks)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
    board.Save(board.GetFileName()); write_project(outdir)
    print("repair: removed %d offending items + %d dangling; unconnected now: %d" % (n, rm, board.GetConnectivity().GetUnconnectedCount(True)))

# net classes for the autorouter (the same numbers are in voxhub.kicad_pro for KiCad's DRC)
NETCLASSES = {
    "Power": (400, 150, ["VBUS", "VBUS_SW", "BUCK_SW", "USB1_VBUS", "USB2_VBUS", "SD_VDD", "SPK_P", "SPK_N"]),
    "P3V3": (250, 130, ["+3V3"]),
    "USB": (200, 130, ["USB_UP_P", "USB_UP_N", "USB1_P", "USB1_N", "USB2_P", "USB2_N"]),
}
DEFAULT_RULE = (150, 130)

def dsn_netclasses(s):
    import re
    s = s.replace("(rule\n      (width 200)\n      (clearance 200)\n      (clearance 50 (type smd_smd))",
                  "(rule\n      (width %d)\n      (clearance %d)\n      (clearance 50 (type smd_smd))" % DEFAULT_RULE)
    a = s.index("    (class kicad_default")
    b = s.index("  (wiring", a)
    block = s[a:b]
    special = {n for _, _, nets in NETCLASSES.values() for n in nets}
    head, tail = block.split("(circuit", 1)
    toks = re.findall(r'"[^"]*"|\S+', head)[2:]
    keep = [x for x in toks if x not in special]
    out = "    (class kicad_default " + " ".join(keep) + "\n      (circuit\n        (use_via \"Via[0-3]_500:250_um\")\n      )\n"
    out += "      (rule\n        (width %d)\n        (clearance %d)\n      )\n    )\n" % DEFAULT_RULE
    for name, (w, c, nets) in NETCLASSES.items():
        out += "    (class %s %s\n      (circuit\n        (use_via \"Via[0-3]_%s_um\")\n      )\n" % (
            name, " ".join(nets), "600:300" if name == "Power" else "500:250")
        out += "      (rule\n        (width %d)\n        (clearance %d)\n      )\n    )\n" % (w, c)
    return s[:a] + out + "  )\n" + s[b:]

if __name__ == "__main__":
    if sys.argv[1] == "place":
        place(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "dsn":
        b = pcbnew.LoadBoard(os.path.join(sys.argv[2], "voxhub.kicad_pcb"))
        os.makedirs(os.path.join(sys.argv[2], "gen", "work"), exist_ok=True)
        if "--planes" in sys.argv:
            poly_zone(b, rect(0, 0, W, H), (pcbnew.In1_Cu,), "GND", name="GND_PLANE")
            poly_zone(b, rect(0, 0, W, H), (pcbnew.In2_Cu,), "+5V", name="5V_PLANE")
        dsn = os.path.join(sys.argv[2], "gen", "work", "voxhub.dsn")
        print("DSN export:", pcbnew.ExportSpecctraDSN(b, dsn))
        s = open(dsn).read()
        s = dsn_netclasses(s)
        for lay in ("In1.Cu", "In2.Cu"):       # planes: keep the router off these layers
            s = s.replace("(layer %s\n      (type signal)" % lay, "(layer %s\n      (type power)" % lay)
        open(dsn, "w").write(s)
    elif sys.argv[1] == "pours":       # last step: local pours for the high-current nets (routing is complete by then)
        outdir = sys.argv[2]
        b = pcbnew.LoadBoard(os.path.join(outdir, "voxhub.kicad_pcb"))
        add_power_pours(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
        b.Save(b.GetFileName()); write_project(outdir)
        print("pours added; unconnected:", b.GetConnectivity().GetUnconnectedCount(True))
    elif sys.argv[1] == "repair":
        repair(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "patch":
        rr = ()
        if "--reroute-usb" in sys.argv:
            u = list(NETCLASSES["USB"][2])          # UP_P, UP_N, 1_P, 1_N, 2_P, 2_N
            variant = int(sys.argv[sys.argv.index("--variant") + 1]) if "--variant" in sys.argv else 0
            orders = [u, [u[1], u[0], u[3], u[2], u[5], u[4]], u[2:] + u[:2], list(reversed(u)), [u[4], u[5], u[2], u[3], u[0], u[1]], [u[3], u[2], u[5], u[4], u[1], u[0]]]
            rr = tuple(orders[variant % len(orders)])
        patch(sys.argv[2], reroute=rr)
    elif sys.argv[1] == "stats":
        b = pcbnew.LoadBoard(os.path.join(sys.argv[2], "voxhub.kicad_pcb"))
        L, V = {}, {}
        ntr = nvia = 0
        for tr in b.GetTracks():
            n_ = tr.GetNetname()
            if tr.Type() == pcbnew.PCB_VIA_T: V[n_] = V.get(n_, 0) + 1; nvia += 1
            else: L[n_] = L.get(n_, 0.0) + pcbnew.ToMM(tr.GetLength()); ntr += 1
        print("track segments: %d, vias: %d (GND %d, +5V %d)" % (ntr, nvia, V.get("GND", 0), V.get("+5V", 0)))
        for a_, c_ in (("USB_UP_P", "USB_UP_N"), ("USB1_P", "USB1_N"), ("USB2_P", "USB2_N")):
            print("%-9s %6.2f mm (%d vias)   %-9s %6.2f mm (%d vias)   skew %.2f mm" % (
                a_, L.get(a_, 0), V.get(a_, 0), c_, L.get(c_, 0), V.get(c_, 0), abs(L.get(a_, 0) - L.get(c_, 0))))
        for n_ in ("SD_CLK", "SD_CMD", "SD_DAT0", "SD_DAT1", "SD_DAT2", "SD_DAT3", "I2S_BCLK", "PDM_CLK_M"):
            print("%-9s %6.1f mm (%d vias)" % (n_, L.get(n_, 0), V.get(n_, 0)))
    else:
        finish(sys.argv[2])
