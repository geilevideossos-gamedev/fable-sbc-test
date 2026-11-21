#!/usr/bin/env python3
"""Generate the project footprint library (voxhub.pretty), KiCad 10 format.

* every footprint of gen/stock/stock.pretty (the KiCad 9.0.9 library footprints revision A2 was designed with), three of them with LAND_FIXES
* CM4_J1/J2_DF40C-100DS : KiCad's Hirose DF40C-100DS land pattern, pads renumbered to the
  CM4 datasheet numbering (J2 = pins 101..200) so schematic pin numbers equal module pin numbers; paste aperture
  0.17 x 0.67 mm = 81 % of the land (Hirose: 80 % at a 0.12 mm stencil).
* RFstar_RF-BM-2652P2    : 30-pad land pattern of the RF-star hardware data sheet V1.1 (fig. 4); pad positions
  equal the JLCPCB / EasyEDA footprint of LCSC C5440064 to 0.01 mm.
* ADAU7002 WLCSP-8       : 2x4 balls, 0.4 mm pitch, per ADAU7002 datasheet Rev. B fig. 22.
"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import uid, natural
from sexpr import dump, Sym as S

STOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock", "stock.pretty")
BASE = "Hirose_DF40C-100DS-0.4V_2x50_P0.4mm"
out = sys.argv[1] if len(sys.argv) > 1 else "../voxhub.pretty"
os.makedirs(out, exist_ok=True)
for old in glob.glob(os.path.join(out, "*.kicad_mod")):
    os.remove(old)
LAND_FIXES = {
    "Mounting_Wuerth_WA-SMSI-M2.5_H1.5mm_9774015151": [
        ('\t\t(at 2.425 0)\n\t\t(size 1.15 1.15)\n', '\t\t(at 2.425 0)\n\t\t(size 0.642 0.642)\n', 1),
        ('\t\t\t\t(end 0 0)\n\t\t\t\t(width 1.15)\n', '\t\t\t\t(end 0.125 0)\n\t\t\t\t(width 0.9)\n', 1),
        ('\t\t\t(gr_arc\n\t\t\t\t(start -0.250195 1.279127)\n\t\t\t\t(mid 0.289914 0.289914)\n\t\t\t\t(end 1.279127 -0.250195)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start -0.34334 1.279127)\n\t\t\t\t(mid 0.225488 0.225488)\n\t\t\t\t(end 1.279127 -0.34334)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start -0.436309 1.279127)\n\t\t\t\t(mid 0.161063 0.161063)\n\t\t\t\t(end 1.279127 -0.436309)\n\t\t\t\t(width 0.2)\n\t\t\t)\n',
         '\t\t\t(gr_arc\n\t\t\t\t(start -0.505369 1.279127)\n\t\t\t\t(mid 0.113137 0.113137)\n\t\t\t\t(end 1.279127 -0.505369)\n\t\t\t\t(width 0.2)\n\t\t\t)\n', 1),
        ('\t\t\t\t(start 1.279127 -0.250195)\n\t\t\t\t(end 1.279127 -1.083663)\n', '\t\t\t\t(start 1.279127 -0.505369)\n\t\t\t\t(end 1.279127 -1.083663)\n', 1),
        ('\t\t\t\t(start -0.250195 1.279127)\n\t\t\t\t(end -1.083663 1.279127)\n', '\t\t\t\t(start -0.505369 1.279127)\n\t\t\t\t(end -1.083663 1.279127)\n', 1),
        ('\t\t\t(gr_arc\n\t\t\t\t(start 1.279127 0.250195)\n\t\t\t\t(mid 0.289914 -0.289914)\n\t\t\t\t(end -0.250195 -1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start 1.279127 0.34334)\n\t\t\t\t(mid 0.225488 -0.225488)\n\t\t\t\t(end -0.34334 -1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start 1.279127 0.436309)\n\t\t\t\t(mid 0.161063 -0.161063)\n\t\t\t\t(end -0.436309 -1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n',
         '\t\t\t(gr_arc\n\t\t\t\t(start 1.279127 0.505369)\n\t\t\t\t(mid 0.113137 -0.113137)\n\t\t\t\t(end -0.505369 -1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n', 1),
        ('\t\t\t\t(start -0.250195 -1.279127)\n\t\t\t\t(end -1.083663 -1.279127)\n', '\t\t\t\t(start -0.505369 -1.279127)\n\t\t\t\t(end -1.083663 -1.279127)\n', 1),
        ('\t\t\t\t(start 1.279127 0.250195)\n\t\t\t\t(end 1.279127 1.083663)\n', '\t\t\t\t(start 1.279127 0.505369)\n\t\t\t\t(end 1.279127 1.083663)\n', 1),
        ('\t\t\t(gr_arc\n\t\t\t\t(start -1.279127 -0.250195)\n\t\t\t\t(mid -0.289914 0.289914)\n\t\t\t\t(end 0.250195 1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start -1.279127 -0.34334)\n\t\t\t\t(mid -0.225488 0.225488)\n\t\t\t\t(end 0.34334 1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start -1.279127 -0.436309)\n\t\t\t\t(mid -0.161063 0.161063)\n\t\t\t\t(end 0.436309 1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n',
         '\t\t\t(gr_arc\n\t\t\t\t(start -1.279127 -0.505369)\n\t\t\t\t(mid -0.113137 0.113137)\n\t\t\t\t(end 0.505369 1.279127)\n\t\t\t\t(width 0.2)\n\t\t\t)\n', 1),
        ('\t\t\t\t(start 0.250195 1.279127)\n\t\t\t\t(end 1.083663 1.279127)\n', '\t\t\t\t(start 0.505369 1.279127)\n\t\t\t\t(end 1.083663 1.279127)\n', 1),
        ('\t\t\t\t(start -1.279127 -0.250195)\n\t\t\t\t(end -1.279127 -1.083663)\n', '\t\t\t\t(start -1.279127 -0.505369)\n\t\t\t\t(end -1.279127 -1.083663)\n', 1),
        ('\t\t\t(gr_arc\n\t\t\t\t(start 0.250195 -1.279127)\n\t\t\t\t(mid -0.289914 -0.289914)\n\t\t\t\t(end -1.279127 0.250195)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start 0.34334 -1.279127)\n\t\t\t\t(mid -0.225488 -0.225488)\n\t\t\t\t(end -1.279127 0.34334)\n\t\t\t\t(width 0.2)\n\t\t\t)\n'
         '\t\t\t(gr_arc\n\t\t\t\t(start 0.436309 -1.279127)\n\t\t\t\t(mid -0.161063 -0.161063)\n\t\t\t\t(end -1.279127 0.436309)\n\t\t\t\t(width 0.2)\n\t\t\t)\n',
         '\t\t\t(gr_arc\n\t\t\t\t(start 0.505369 -1.279127)\n\t\t\t\t(mid -0.113137 -0.113137)\n\t\t\t\t(end -1.279127 0.505369)\n\t\t\t\t(width 0.2)\n\t\t\t)\n', 1),
        ('\t\t\t\t(start -1.279127 0.250195)\n\t\t\t\t(end -1.279127 1.083663)\n', '\t\t\t\t(start -1.279127 0.505369)\n\t\t\t\t(end -1.279127 1.083663)\n', 1),
        ('\t\t\t\t(start 0.250195 -1.279127)\n\t\t\t\t(end 1.083663 -1.279127)\n', '\t\t\t\t(start 0.505369 -1.279127)\n\t\t\t\t(end 1.083663 -1.279127)\n', 1)],
    "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal": [
        ('\t\t(at -3.2 -3.68)\n\t\t(size 0.6 1.15)\n', '\t\t(at -3.2 -3.68)\n\t\t(size 0.6 1.11)\n', 2),
        ('\t\t(at 3.2 -3.68)\n\t\t(size 0.6 1.15)\n', '\t\t(at 3.2 -3.68)\n\t\t(size 0.6 1.11)\n', 2)],
    "Infineon_PG-LLGA-5-1": [
        ('\t\t\t\t(end 0.81 0.81)\n\t\t\t\t(width 0.46)\n', '\t\t\t\t(end 0.825 0.81)\n\t\t\t\t(width 0.43)\n', 1),
        ('(xy 0.213282 -0.2003) (xy 0.21259 -0.122267)\n\t\t\t\t\t(xy 0.2 0) (xy 0.21259 0.122267) (xy 0.213282 0.2003) (xy 0.184059 0.272658) (xy 0.12937 0.328325)\n\t\t\t\t\t(xy 0.057542 0.358826)',
         '(xy 0.207596 -0.214378)\n\t\t\t\t\t(xy 0.183219 -0.12838) (xy 0.17 0) (xy 0.183219 0.12838) (xy 0.207596 0.214378) (xy 0.184059 0.272658)\n\t\t\t\t\t(xy 0.12937 0.328325) (xy 0.057542 0.358826)', 1),
        ('(xy 0.280106 0.084557) (xy 0.212181 0.122975) (xy 0.1 0.173205) (xy 0.000409 0.245242)\n\t\t\t\t\t(xy -0.066824 0.284857)',
         '(xy 0.289291 0.072804) (xy 0.202846 0.094644) (xy 0.085082 0.147357) (xy -0.019477 0.222959)\n\t\t\t\t\t(xy -0.081686 0.286948)', 1),
        ('(xy -0.066846 -0.284852) (xy 0.000389 -0.245242) (xy 0.099986 -0.173213) (xy 0.212171 -0.122991)\n\t\t\t\t\t(xy 0.280099 -0.084579)',
         '(xy -0.081677 -0.286937) (xy -0.019489 -0.222969) (xy 0.085067 -0.147365) (xy 0.202832 -0.094648)\n\t\t\t\t\t(xy 0.289305 -0.072801)', 1),
        ('(xy 0.066824 0.284857) (xy -0.000409 0.245242) (xy -0.1 0.173205) (xy -0.212181 0.122975)\n\t\t\t\t\t(xy -0.280106 0.084557)',
         '(xy 0.081686 0.286948) (xy 0.019477 0.222959) (xy -0.085082 0.147357) (xy -0.202846 0.094644)\n\t\t\t\t\t(xy -0.289291 0.072804)', 1),
        ('(xy -0.280106 -0.084555) (xy -0.212182 -0.122973)\n\t\t\t\t\t(xy -0.100002 -0.173204) (xy -0.000411 -0.245242) (xy 0.066822 -0.284858)',
         '(xy -0.289289 -0.072804) (xy -0.202848 -0.094643)\n\t\t\t\t\t(xy -0.085084 -0.147356) (xy 0.019476 -0.222958) (xy 0.081688 -0.286949)', 1),
        ('(xy -0.213282 0.2003) (xy -0.21259 0.122267)\n\t\t\t\t\t(xy -0.2 0) (xy -0.21259 -0.122267) (xy -0.213282 -0.2003) (xy -0.184059 -0.272658) (xy -0.12937 -0.328325)\n\t\t\t\t\t(xy -0.057542 -0.358826)',
         '(xy -0.207596 0.214378)\n\t\t\t\t\t(xy -0.183219 0.12838) (xy -0.17 0) (xy -0.183219 -0.12838) (xy -0.207596 -0.214378) (xy -0.184059 -0.272658)\n\t\t\t\t\t(xy -0.12937 -0.328325) (xy -0.057542 -0.358826)', 1)],
}
for f in sorted(glob.glob(os.path.join(STOCK, "*.kicad_mod"))):
    base = os.path.basename(f)[:-len(".kicad_mod")]
    if base == BASE:
        continue
    t = open(f).read()
    for old, new, count in LAND_FIXES.get(base, ()):
        assert t.count(old) == count, (base, old, t.count(old))
        t = t.replace(old, new)
    open(os.path.join(out, base + ".kicad_mod"), "w").write(t)

src = open(os.path.join(STOCK, BASE + ".kicad_mod")).read()
for name, off in (("CM4_J1_DF40C-100DS", 0), ("CM4_J2_DF40C-100DS", 100)):
    t = src.replace('(footprint "%s"' % BASE, '(footprint "%s"' % name)
    t = re.sub(r'\(pad "(\d+)"', lambda m: '(pad "%d"' % (int(m.group(1)) + off), t)
    t, n_paste = re.subn(r'(\t\t\(roundrect_rratio 0\.25\)\n)', r'\1\t\t(solder_paste_margin -0.015)\n', t)
    assert n_paste == 100, n_paste
    t = t.replace('(descr "', '(descr "CM4 socket, pads numbered %d-%d (CM4 datasheet numbering). ' % (off + 1, off + 100), 1)
    t = re.sub(r'\(uuid "([0-9a-f-]+)"\)', lambda m: '(uuid "%s")' % uid(name, m.group(1)), t)
    open(os.path.join(out, name + ".kicad_mod"), "w").write(t)

LAYER_ORDER = {"F.SilkS": 5, "F.CrtYd": 31, "F.Fab": 35}
SHAPE_ORDER = {"fp_line": 0, "fp_circle": 3}

class Footprint:
    def __init__(self, name, descr, ry):
        self.name, self.descr, self.ry = name, descr, ry
        self.shapes, self.pads, self.model = [], [], None

    def line(self, x1, y1, x2, y2, layer, w=0.1):
        self.shapes.append(("fp_line", layer, round(x1, 6), round(y1, 6), round(x2, 6), round(y2, 6), w))

    def rect(self, x1, y1, x2, y2, layer, w=0.1):
        self.line(x1, y1, x2, y1, layer, w); self.line(x2, y1, x2, y2, layer, w)
        self.line(x2, y2, x1, y2, layer, w); self.line(x1, y2, x1, y1, layer, w)

    def dot(self, x, y, r, layer, w):
        self.shapes.append(("fp_circle", layer, round(x, 6), round(y, 6), round(x + r, 6), round(y, 6), w))

    def pad(self, num, shape, x, y, sx, sy, *extra):
        self.pads.append((str(num), shape, round(x, 6), round(y, 6), sx, sy, extra))

    def write(self, path):
        def prop(key, value, y, layer, size, thick=None, hide=False):
            font = [S("font"), [S("size"), size, size]] + ([[S("thickness"), thick]] if thick else [])
            return [S("property"), key, value, [S("at"), 0, y, 0], [S("layer"), layer]] + ([[S("hide"), S("yes")]] if hide else []) + \
                   [[S("uuid"), uid(self.name, "property", key)], [S("effects"), font]]
        t = [S("footprint"), self.name, [S("version"), 20260206], [S("generator"), "pcbnew"], [S("generator_version"), "10.0"],
             [S("layer"), "F.Cu"], [S("descr"), self.descr],
             prop("Reference", "REF**", -self.ry, "F.SilkS", 0.8, 0.12), prop("Value", self.name, self.ry, "F.Fab", 0.8, 0.12),
             prop("Datasheet", "", 0, "F.Fab", 1.27, hide=True), prop("Description", "", 0, "F.Fab", 1.27, hide=True),
             [S("attr"), S("smd")], [S("duplicate_pad_numbers_are_jumpers"), S("no")]]
        for s in sorted(self.shapes, key=lambda s: (LAYER_ORDER[s[1]], SHAPE_ORDER[s[0]]) + s[2:]):
            kind, layer, x1, y1, x2, y2, w = s
            t.append([S(kind), [S("center" if kind == "fp_circle" else "start"), x1, y1], [S("end"), x2, y2],
                      [S("stroke"), [S("width"), w], [S("type"), S("solid")]]] + ([[S("fill"), S("yes")]] if kind == "fp_circle" else []) +
                     [[S("layer"), layer], [S("uuid"), uid(self.name, *s)]])
        for num, shape, x, y, sx, sy, extra in sorted(self.pads, key=lambda p: (natural(p[0]), p[2], p[3])):
            t.append([S("pad"), num, S("smd"), S(shape), [S("at"), x, y], [S("size"), sx, sy], [S("layers"), "F.Cu", "F.Mask", "F.Paste"]] +
                     [[S(k), v] for k, v in extra] + [[S("uuid"), uid(self.name, "pad", num)]])
        t.append([S("embedded_fonts"), S("no")])
        t.append([S("model"), self.model] + [[S(k), [S("xyz"), v, v, v]] for k, v in (("offset", 0), ("scale", 1), ("rotate", 0))])
        open(path, "w").write(dump(t))

n = "RFstar_RF-BM-2652P2"
f = Footprint(n, "RF-star RF-BM-2652P2 (TI CC2652P) module, 16.5x30.0mm, 30 castellated pads P1.27mm; PCB antenna at the -y end (RF-star hardware data sheet V1.1 fig. 4)", 16.3)
pads = [(i + 1, -8.2, -3.01 + i * 1.27) for i in range(14)] + [(15 + i, 8.2, 13.50 - i * 1.27) for i in range(14)] + [(29, 8.2, -7.21), (30, 8.2, -8.48)]
for num, x, y in pads:
    f.pad(num, "roundrect", x, y, 2.0, 0.9, ("roundrect_rratio", 0.2))
f.rect(-8.25, -15.0, 8.25, 15.0, "F.Fab"); f.line(-8.25, -9.0, 8.25, -9.0, "F.Fab"); f.rect(-9.45, -15.25, 9.45, 15.25, "F.CrtYd", 0.05)
f.line(-8.4, 14.2, -8.4, 15.15, "F.SilkS", 0.12); f.line(-8.4, 15.15, 8.4, 15.15, "F.SilkS", 0.12); f.line(8.4, 15.15, 8.4, 14.2, "F.SilkS", 0.12)
f.line(-8.4, -3.75, -8.4, -9.0, "F.SilkS", 0.12)
f.dot(-9.75, -3.01, 0.15, "F.SilkS", 0.2)
f.model = "${KIPRJMOD}/3dmodels/RF-BM-2652P2.step"
f.write(os.path.join(out, n + ".kicad_mod"))

# ---- ADAU7002 --------------------------------------------------------------
n = "ADAU7002_WLCSP-8_0.76x1.56mm_P0.4mm"
f = Footprint(n, "Analog Devices ADAU7002 WLCSP-8 (CB-8-13), 0.76x1.56mm, 2x4 balls, 0.4mm pitch, NSMD pads", 1.9)
for r, row in enumerate("ABCD"):
    for c in (1, 2):
        f.pad("%s%d" % (row, c), "circle", -0.2 + (c - 1) * 0.4, -0.6 + r * 0.4, 0.22, 0.22, ("solder_mask_margin", 0.03), ("solder_paste_margin", -0.005))
f.rect(-0.38, -0.78, 0.38, 0.78, "F.Fab"); f.rect(-0.65, -1.05, 0.65, 1.05, "F.CrtYd", 0.05)
f.dot(-0.75, -0.9, 0.07, "F.SilkS", 0.12)
f.model = "${KIPRJMOD}/3dmodels/ADAU7002.step"
f.write(os.path.join(out, n + ".kicad_mod"))
print("footprints written to", out)
