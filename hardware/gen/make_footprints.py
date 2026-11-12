#!/usr/bin/env python3
"""Generate the project footprint library (voxhub.pretty).

* CM4_J1/J2_DF40C-100DS : KiCad's Hirose DF40C-100DS land pattern, pads renumbered to the
  CM4 datasheet numbering (J2 = pins 101..200) so schematic pin numbers equal module pin numbers; paste aperture
  0.17 x 0.67 mm = 81 % of the land (Hirose: 80 % at a 0.12 mm stencil).
* RFstar_RF-BM-2652P2    : 30-pad land pattern of the RF-star hardware data sheet V1.1 (fig. 4); pad positions
  equal the JLCPCB / EasyEDA footprint of LCSC C5440064 to 0.01 mm.
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
    t, n_paste = re.subn(r'(\(roundrect_rratio 0\.25\)\n)(\t\))', r'\1\t\t(solder_paste_margin -0.015)\n\2', t)
    assert n_paste == 100, n_paste
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

n = "RFstar_RF-BM-2652P2"
t = header(n, "RF-star RF-BM-2652P2 (TI CC2652P) module, 16.5x30.0mm, 30 castellated pads P1.27mm; PCB antenna at the -y end (RF-star hardware data sheet V1.1 fig. 4)").format(ry=16.3)
pads = [(i + 1, -8.2, -3.01 + i * 1.27) for i in range(14)] + [(15 + i, 8.2, 13.50 - i * 1.27) for i in range(14)] + [(29, 8.2, -7.21), (30, 8.2, -8.48)]
for num, x, y in pads:
    t += f'\t(pad "{num}" smd roundrect (at {x:.3f} {y:.3f}) (size 2.0 0.9) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.2))\n'
t += rect(-8.25, -15.0, 8.25, 15.0, "F.Fab") + line(-8.25, -9.0, 8.25, -9.0, "F.Fab") + rect(-9.45, -15.25, 9.45, 15.25, "F.CrtYd", 0.05)
t += line(-8.4, 14.2, -8.4, 15.15, "F.SilkS", 0.12) + line(-8.4, 15.15, 8.4, 15.15, "F.SilkS", 0.12) + line(8.4, 15.15, 8.4, 14.2, "F.SilkS", 0.12)
t += line(-8.4, -3.75, -8.4, -9.0, "F.SilkS", 0.12)
t += '\t(fp_circle (center -9.75 -3.01) (end -9.6 -3.01) (stroke (width 0.2) (type solid)) (fill yes) (layer "F.SilkS"))\n'
t += '\t(model "${KIPRJMOD}/3dmodels/RF-BM-2652P2.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n)\n'
open(os.path.join(out, n + ".kicad_mod"), "w").write(t)

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
