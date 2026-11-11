#!/usr/bin/env python3
"""Generate the project footprint library (voxhub.pretty).

* CM4_J1/J2_DF40C-100DS : KiCad's Hirose DF40C-100DS land pattern, pads renumbered to the
  CM4 datasheet numbering (J2 = pins 101..200) so schematic pin numbers equal module pin numbers.
* SiliconLabs_MGM240P    : 36-pad land pattern; cross-checked against three independent
  footprints (SparkFun Thing Plus Matter, Ultra Librarian export, sivakov512/kicad-library).
* ADAU7002 WLCSP-8       : 2x4 balls, 0.4 mm pitch, per ADAU7002 datasheet Rev. B fig. 22.
"""
import os, re, sys
FP = os.environ.get("KICAD_FP_DIR", "/usr/share/kicad/footprints")
out = sys.argv[1] if len(sys.argv) > 1 else "../voxhub.pretty"
os.makedirs(out, exist_ok=True)

src = open(os.path.join(FP, "Connector_Hirose_DF40.pretty", "Hirose_DF40C-100DS-0.4V_2x50_P0.4mm.kicad_mod")).read()
for name, off in (("CM4_J1_DF40C-100DS", 0), ("CM4_J2_DF40C-100DS", 100)):
    t = src.replace('(footprint "Hirose_DF40C-100DS-0.4V_2x50_P0.4mm"', '(footprint "%s"' % name)
    t = re.sub(r'\(pad "(\d+)"', lambda m: '(pad "%d"' % (int(m.group(1)) + off), t)
    t = t.replace('(descr "', '(descr "CM4 socket, pads numbered %d-%d (CM4 datasheet numbering). ' % (off + 1, off + 100), 1)
    open(os.path.join(out, name + ".kicad_mod"), "w").write(t)

def header(name, descr, attr="smd"):
    return f'''(footprint "{name}"
\t(version 20241229)
\t(generator "voxhub_gen")
\t(layer "F.Cu")
\t(descr "{descr}")
\t(property "Reference" "REF**" (at 0 -{{ry}} 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
\t(property "Value" "{name}" (at 0 {{ry}} 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
\t(attr {attr})
'''
def line(x1, y1, x2, y2, layer, w=0.1):
    return f'\t(fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'
def rect(x1, y1, x2, y2, layer, w=0.1):
    return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)

# ---- MGM240P ---------------------------------------------------------------
t = header("SiliconLabs_MGM240P", "Silicon Labs MGM240P module, 12.9x15.0mm, 36 castellated pads P1.0mm; antenna along the pad-free (top) edge").format(ry=9.2)
pads = []
for i in range(14): pads.append((i + 1, -5.65, -6.8 + i, 2.4, 0.6))
for i in range(8): pads.append((15 + i, -3.5 + i, 6.7, 0.6, 2.4))
for i in range(14): pads.append((23 + i, 5.65, 6.2 - i, 2.4, 0.6))
for n, x, y, w, h in pads:
    t += f'\t(pad "{n}" smd roundrect (at {x:.3f} {y:.3f}) (size {w} {h}) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))\n'
t += rect(-6.45, -7.5, 6.45, 7.5, "F.Fab") + rect(-7.1, -7.75, 7.1, 8.15, "F.CrtYd", 0.05)
t += line(-6.6, -7.65, 6.6, -7.65, "F.SilkS", 0.12) + line(-6.6, -7.65, -6.6, -7.3, "F.SilkS", 0.12) + line(6.6, -7.65, 6.6, -7.3, "F.SilkS", 0.12)
t += line(-6.6, 7.65, -4.1, 7.65, "F.SilkS", 0.12) + line(6.6, 7.65, 4.1, 7.65, "F.SilkS", 0.12)
t += '\t(fp_circle (center -7.5 -6.8) (end -7.35 -6.8) (stroke (width 0.2) (type solid)) (fill yes) (layer "F.SilkS"))\n'
t += '\t(model "${KIPRJMOD}/3dmodels/MGM240P.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n)\n'
open(os.path.join(out, "SiliconLabs_MGM240P.kicad_mod"), "w").write(t)

# ---- ADAU7002 --------------------------------------------------------------
n = "ADAU7002_WLCSP-8_0.76x1.56mm_P0.4mm"
t = header(n, "Analog Devices ADAU7002 WLCSP-8 (CB-8-13), 0.76x1.56mm, 2x4 balls, 0.4mm pitch, NSMD pads").format(ry=1.9)
for r, row in enumerate("ABCD"):
    for c in (1, 2):
        t += (f'\t(pad "{row}{c}" smd circle (at {-0.2 + (c - 1) * 0.4:.3f} {-0.6 + r * 0.4:.3f}) (size 0.22 0.22) '
              f'(layers "F.Cu" "F.Mask" "F.Paste") (solder_mask_margin 0.03) (solder_paste_margin -0.005))\n')
t += rect(-0.38, -0.78, 0.38, 0.78, "F.Fab") + rect(-0.65, -1.05, 0.65, 1.05, "F.CrtYd", 0.05)
t += '\t(fp_circle (center -0.75 -0.9) (end -0.68 -0.9) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))\n'
t += '\t(model "${KIPRJMOD}/3dmodels/ADAU7002.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n)\n'
open(os.path.join(out, n + ".kicad_mod"), "w").write(t)
print("footprints written to", out)
