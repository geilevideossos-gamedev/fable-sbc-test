#!/usr/bin/env python3
"""Simple stand-in STEP models for parts whose model is missing from the KiCad 3D library
(or which are project specific).  Dimensions are body envelopes - good enough for renders
and for the enclosure fit check.  usage: make_3dmodels.py <hardware/3dmodels>"""
import os, sys
import cadquery as cq

def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def cbox(w, d, h, z0=0.0):
    return box(-w / 2, -d / 2, z0, w / 2, d / 2, z0 + h)

# name -> solid (KiCad model frame: X right, Y = -footprint Y, Z up, origin = footprint origin)
M = {
    "Connector_USB.3dshapes/USB_A_Wuerth_61400826021_Horizontal_Stacked": box(-3.75, -15.61, 0, 10.75, 1.39, 15.7)
        .cut(box(-2.6, -15.7, 1.2, 9.6, -6.0, 6.6)).cut(box(-2.6, -15.7, 8.6, 9.6, -6.0, 14.0))
        .union(box(-2.0, -15.0, 3.2, 9.0, -6.0, 4.9)).union(box(-2.0, -15.0, 10.6, 9.0, -6.0, 12.3)),
    "Button_Switch_SMD.3dshapes/SW_DPDT_CK_JS202011JCQN": cbox(9.0, 3.6, 3.5).union(box(-2.0, -0.75, 3.5, 0.0, 0.75, 5.5)),
    "Inductor_SMD.3dshapes/L_Bourns_SRP7028A_7.3x6.6mm": cbox(7.3, 6.6, 2.8).edges("|Z").fillet(0.8),
    "LED_SMD.3dshapes/LED_1206_3216Metric_ReverseMount": cbox(3.2, 1.6, 0.7),
    "Package_DFN_QFN.3dshapes/QFN-24-1EP_4x4mm_P0.5mm_EP2.75x2.75mm": cbox(4.0, 4.0, 0.6),
    "Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm": cbox(3.0, 3.0, 0.75),
    "Package_SO.3dshapes/HTSOP-8-1EP_3.9x4.9mm_Pitch1.27mm": cbox(3.9, 4.9, 1.5, 0.1).union(cbox(6.0, 4.3, 0.25)),
    "Sensor_Audio.3dshapes/Infineon_PG-LLGA-5-1": cbox(4.0, 3.0, 1.2),
    "MGM240P": cbox(12.9, 15.0, 0.8).union(box(-6.0, -7.0, 0.8, 6.0, 2.5, 2.2)),
    "ADAU7002": cbox(0.76, 1.56, 0.5),
    # CM4 module incl. 14x14x6 heat sink, origin = module centre, z = 0 at the carrier surface (1.5 mm stack)
    "RaspberryPi_CM4_with_heatsink": cbox(55.0, 40.0, 1.2, 1.5).edges("|Z").fillet(3.0)
        .union(cbox(15.0, 15.0, 2.4, 2.7)).union(cbox(14.0, 14.0, 6.0, 5.1))
        .union(box(-24.0, -14.0, 2.7, -12.0, 2.0, 4.5)).union(box(12.0, -12.0, 2.7, 22.0, -2.0, 3.9)),
}
out = sys.argv[1]
for name, solid in M.items():
    path = os.path.join(out, name + ".step")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cq.exporters.export(solid, path)
print("stand-in models:", len(M))
