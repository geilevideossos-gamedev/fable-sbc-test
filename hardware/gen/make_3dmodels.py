#!/usr/bin/env python3
"""Stand-in STEP models for parts whose model is missing from the KiCad 3D library (or which are project
specific).  Outer dimensions are the body envelopes from the manufacturer drawings; the models are written as
coloured STEP assemblies (one named solid per material) so that renders can tell metal from plastic.
usage: make_3dmodels.py <hardware/3dmodels>"""
import os, sys
import cadquery as cq

def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def cbox(w, d, h, z0=0.0, x=0.0, y=0.0):
    return box(x - w / 2, y - d / 2, z0, x + w / 2, y + d / 2, z0 + h)

def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))

BLACK, SILVER, GOLD = (0.045, 0.045, 0.05), (0.80, 0.80, 0.82), (0.86, 0.68, 0.26)
GREEN, WHITE, GREY, ALU = (0.03, 0.30, 0.14), (0.92, 0.92, 0.90), (0.22, 0.22, 0.24), (0.76, 0.77, 0.79)

def usb_a():
    # Wurth 61400826021: shell 13.1 x 17.0, height 15.34 (flange lip to 15.95); two ports with plastic tongues
    shell = (box(-3.75, -15.61, 0, 10.75, 1.39, 15.6)
             .cut(box(-2.75, -15.7, 1.35, 9.75, -5.5, 6.5)).cut(box(-2.75, -15.7, 8.75, 9.75, -5.5, 13.9)))
    tongues = box(-2.25, -14.6, 3.45, 9.25, -5.5, 5.3).union(box(-2.25, -14.6, 10.85, 9.25, -5.5, 12.7))
    contacts = cq.Workplane("XY")
    for z in (3.44, 10.84):
        for i in range(4):
            contacts = contacts.union(box(-0.5 + i * 2.5 - 0.5, -14.2, z - 0.05, -0.5 + i * 2.5 + 0.5, -8.0, z))
    return [("shell", shell, SILVER), ("tongues", tongues, BLACK), ("contacts", contacts, GOLD)]

def cm4():
    # CM4 Lite wireless (datasheet fig. 4): 55 x 40 x 1.2 mm on a 1.5 mm stack, SoC centre 31.99 / 16.98 mm from the
    # antenna-end / pin-101 edges, 14 x 14 x 6 mm heat sink.  Origin = module centre, z = 0 = carrier surface,
    # +x = antenna end, +y = pins 101-200 side.
    pcb = cbox(55.0, 40.0, 1.2, 1.5).edges("|Z").fillet(3.0)
    for sx in (-24.0, 24.0):
        for sy in (-16.5, 16.5):
            pcb = pcb.cut(cyl(sx, sy, 1.4, 2.8, 2.7))
    plugs = cbox(22.6, 2.0, 1.1, 0.4, 2.5, 17.0).union(cbox(22.6, 2.0, 1.1, 0.4, 2.5, -17.0))
    sx, sy = -4.5, 3.0
    soc = cbox(15.0, 15.0, 0.6, 2.7, sx, sy).union(cbox(12.5, 12.5, 1.8, 3.3, sx, sy).edges("|Z").fillet(1.0))
    hs = cbox(14.0, 14.0, 1.6, 5.1, sx, sy)
    for i in range(7):
        hs = hs.union(cbox(1.0, 14.0, 4.4, 6.7, sx - 6.5 + i * 13.0 / 6, sy))
    chips = (cbox(10.0, 14.5, 1.0, 2.7, -19.0, 3.0)            # LPDDR4
             .union(cbox(5.0, 5.0, 0.9, 2.7, 8.0, -9.5))       # PMIC
             .union(cbox(6.0, 6.0, 0.9, 2.7, -19.5, -12.5))    # Ethernet PHY
             .union(cbox(3.0, 3.0, 0.8, 2.7, 0.5, -12.0)))
    can = cbox(12.5, 10.5, 1.7, 2.7, 13.5, 8.0).edges("|Z").fillet(0.6)      # wireless module shield
    ufl = cyl(23.3, 14.0, 2.7, 3.9, 2.0).union(cbox(2.6, 2.6, 0.5, 2.7, 23.3, 14.0))
    ant = box(21.6, -9.2, 2.7, 26.9, 1.2, 2.74).cut(box(22.6, -8.2, 2.6, 25.9, 0.2, 2.8))    # antenna trace (fig. 4 cut-out)
    return [("pcb", pcb, GREEN), ("plugs", plugs, GREY), ("soc", soc, SILVER), ("heatsink", hs, ALU),
            ("chips", chips, BLACK), ("shield", can, SILVER), ("ufl", ufl, GOLD), ("antenna", ant, GOLD)]

def slide_switch():
    # C&K JS202011JCQN: body 9.0 x 3.6 x 3.5, actuator 1.5 x 1.5 x 2.0 (2 mm travel), J-bend terminals
    frame = cbox(9.0, 3.6, 2.6, 0.9)
    base = cbox(8.5, 3.4, 0.9, 0.0)
    act = box(-1.75, -0.75, 3.5, -0.25, 0.75, 5.5)
    pins = cq.Workplane("XY")
    for x in (-2.5, 0.0, 2.5):
        for y in (-1.6, 1.6):
            pins = pins.union(cbox(0.6, 0.9, 0.5, 0.0, x, y * 1.15))
    return [("frame", frame, SILVER), ("base", base, BLACK), ("actuator", act, BLACK), ("pins", pins, SILVER)]

def rf_bm_2652p2():
    pcb = cbox(16.5, 30.0, 0.8)
    can = box(-7.2, -13.6, 0.8, 7.2, 5.0, 2.25).edges("|Z").fillet(0.5)
    ant = box(-7.0, 9.6, 0.8, 7.0, 14.4, 0.84).cut(box(-6.0, 10.6, 0.7, 6.0, 13.4, 0.9))
    return [("pcb", pcb, GREEN), ("shield", can, SILVER), ("antenna", ant, GOLD)]

def simple(solid, colour):
    return [("body", solid, colour)]

# name -> list of (part name, solid, colour)   (KiCad model frame: X right, Y = -footprint Y, Z up, origin = footprint origin)
M = {
    "Connector_USB.3dshapes/USB_A_Wuerth_61400826021_Horizontal_Stacked": usb_a(),
    "Button_Switch_SMD.3dshapes/SW_DPDT_CK_JS202011JCQN": slide_switch(),
    "Inductor_SMD.3dshapes/L_Bourns_SRP7028A_7.3x6.6mm": [("body", cbox(7.3, 6.6, 2.75, 0.05).edges("|Z").fillet(0.8), GREY),
                                                           ("pads", cbox(1.4, 3.2, 0.3, 0.0, -3.0, 0).union(cbox(1.4, 3.2, 0.3, 0.0, 3.0, 0)), SILVER)],
    "Package_DFN_QFN.3dshapes/QFN-24-1EP_4x4mm_P0.5mm_EP2.75x2.75mm": simple(cbox(4.0, 4.0, 0.6), BLACK),
    "Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm": simple(cbox(3.0, 3.0, 0.75), BLACK),
    "Package_SO.3dshapes/HTSOP-8-1EP_3.9x4.9mm_Pitch1.27mm": [("body", cbox(3.9, 4.9, 1.5, 0.1), BLACK), ("leads", cbox(6.0, 4.3, 0.25), SILVER)],
    "Sensor_Audio.3dshapes/Infineon_PG-LLGA-5-1": [("lid", cbox(4.0, 3.0, 0.95, 0.25), SILVER), ("base", cbox(4.0, 3.0, 0.25), GREEN)],
    "RF-BM-2652P2": rf_bm_2652p2(),
    "ADAU7002": simple(cbox(0.76, 1.56, 0.5), BLACK),
    "RaspberryPi_CM4_with_heatsink": cm4(),
}
out = sys.argv[1]
for name, parts in M.items():
    path = os.path.join(out, name + ".step")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    asm = cq.Assembly(name=os.path.basename(name))
    for pname, solid, col in parts:
        asm.add(solid, name=pname, color=cq.Color(*col))
    asm.export(path) if hasattr(asm, "export") else asm.save(path)
print("stand-in models:", len(M))
