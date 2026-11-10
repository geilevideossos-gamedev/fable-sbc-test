#!/usr/bin/env python3
"""VoxHub CM4 enclosure - parametric CadQuery model.

Two printed parts, both support-free on a Bambu Lab printer (0.4 mm nozzle, 0.2 mm layers):

  shell  top + four walls, printed UPSIDE DOWN (top face on the build plate).  All bosses,
         posts, mic chimneys and LED light pipes grow straight up from the top plate; the
         connector windows in the rear wall are short bridges (<= 15.2 mm).
  base   flat bottom plate with vents, a pedestal that clamps the speaker against the
         grille (through a foam pad) and four countersunk screw holes.  Printed flat.

Coordinate system ("device frame"): X/Y are the PCB coordinates of the KiCad board
(origin = rear-left corner seen from the component side, X to the right, Y towards the
front); Z is up.  The PCB hangs component-side DOWN under the top plate, so its bare side
faces the top (short acoustic path for the bottom-port microphones, LEDs shining upwards,
mute slider reachable from the top).  Z = 0 is the PCB surface facing the top plate.

Everything that depends on the PCB is read from ../hardware/gen/placement.json, which is
written by the PCB generator - regenerate the enclosure after moving parts on the board.

Usage:  python3 voxhub_enclosure.py [outdir]     (writes STL, 3MF, STEP and preview PNGs)
"""
import json, math, os, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
PLACEMENT = json.load(open(os.path.join(HERE, "..", "hardware", "gen", "placement.json")))

# ----------------------------------------------------------------------------- parameters
PCB_W, PCB_H, PCB_T = 100.0, 74.0, 1.6      # must match hardware/gen/build_pcb.py
WALL = 2.0                                   # side wall thickness
TOP_T = 2.0                                  # top plate thickness
BASE_T = 2.4                                 # base plate thickness
GAP_TOP = 4.0                                # PCB bare side -> inside of top plate (fits SW1 body 3.5 mm)
DEPTH = 18.0                                 # PCB component side -> inside of base (USB-A stack is 15.7 mm)
EDGE_GAP = 0.6                               # PCB edge -> inner wall (rear, front)
SPK_BAY = 46.0                               # extra interior width on the left for the speaker
POST_BAY = 7.6                               # extra interior width on the right for the base screw posts
CORNER_R = 5.0                               # outer vertical corner radius
FIT = 0.25                                   # general printing clearance

# speaker: Same Sky CMS-4017-34SP class, 40 mm round frame, 17.5 mm deep, 4 ohm 3 W
SPK_D, SPK_DEPTH = 40.0, 17.5
SPK_GRILLE_D = 34.0
FOAM = 1.5                                   # compressed foam pad between speaker magnet and pedestal

# screws: M2.5 x 6 thread-forming (PCB) and M2.5 x 8 (base); pilot hole for PLA/PETG
PILOT_D, SCREW_CLEAR_D, SCREW_HEAD_D = 2.1, 2.9, 5.2
BOSS_D, POST_D = 6.0, 7.2

# derived Z levels
Z_TOP_IN = GAP_TOP                           # inside of the top plate
Z_TOP_OUT = GAP_TOP + TOP_T
Z_PCB_BOT = -PCB_T                           # component side of the PCB
Z_FLOOR = Z_PCB_BOT - DEPTH                  # inside of the base plate
Z_BOTTOM = Z_FLOOR - BASE_T                  # table

# interior footprint
X0, X1 = -SPK_BAY - EDGE_GAP, PCB_W + EDGE_GAP + POST_BAY
Y0, Y1 = -EDGE_GAP, PCB_H + EDGE_GAP
SPK_X, SPK_Y = -SPK_BAY / 2 - 0.5, PCB_H / 2

def at(ref):
    x, y, rot, side = PLACEMENT[ref]
    return x, y, rot, side

def rot_pt(dx, dy, rot_deg):
    """KiCad footprint-local offset -> board offset (KiCad rotates counter-clockwise, Y down)."""
    a = math.radians(rot_deg)
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)

HOLES = [at(r)[:2] for r in ("H1", "H2", "H3", "H4")]            # PCB mounting holes
MICS = []
for r in ("MK1", "MK2"):                                          # acoustic port = footprint-local (0.68, 0)
    x, y, rot, _ = at(r); dx, dy = rot_pt(0.68, 0.0, rot); MICS.append((x + dx, y + dy))
LEDS = [v[:2] for k, v in sorted(PLACEMENT.items()) if k.startswith("D") and abs(v[1] - 71.2) < 0.01 and 30 < v[0] < 46]
SW = at("SW1")[:2]
POSTS = [(X0 + POST_D / 2 + 0.2, Y0 + POST_D / 2 + 0.2), (X0 + POST_D / 2 + 0.2, Y1 - POST_D / 2 - 0.2),
         (X1 - POST_D / 2 - 0.2, Y0 + POST_D / 2 + 0.2), (X1 - POST_D / 2 - 0.2, Y1 - POST_D / 2 - 0.2)]

# rear-wall windows: (x centre, width, z top, z bottom)  - connector bodies hang below the PCB
USBC_X, USBA_X, SD_X = at("J1")[0], at("J6")[0] - 3.5, at("J4")[0]
WINDOWS = [
    (USBC_X, 12.4, Z_PCB_BOT + 1.3, Z_PCB_BOT - 5.0),     # USB-C: 8.94 x 3.31 shell + plug overmould clearance
    (USBA_X, 15.2, Z_PCB_BOT + 0.3, Z_PCB_BOT - 16.2),    # stacked USB-A: 14.5 x 15.7
    (SD_X, 14.0, Z_PCB_BOT + 0.2, Z_PCB_BOT - 7.0),       # microSD: card 11 x 1 mm, sits ~2 mm behind the outer surface -> finger notch below it
]

def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))

# ----------------------------------------------------------------------------- shell
def make_shell():
    outer = (cq.Workplane("XY").box(X1 - X0 + 2 * WALL, Y1 - Y0 + 2 * WALL, Z_TOP_OUT - Z_BOTTOM, centered=False)
             .translate((X0 - WALL, Y0 - WALL, Z_BOTTOM)).edges("|Z").fillet(CORNER_R)
             .faces(">Z").edges().chamfer(0.8))
    inner = (box(X0, Y0, Z_BOTTOM - 1, X1, Y1, Z_TOP_IN).edges("|Z").fillet(CORNER_R - WALL))
    s = outer.cut(inner)

    # PCB bosses (PCB is screwed against them from below)
    for x, y in HOLES:
        s = s.union(cyl(x, y, 0.0, Z_TOP_IN + 0.01, BOSS_D)).cut(cyl(x, y, -0.1, Z_TOP_IN + TOP_T - 0.8, PILOT_D))
    # base screw posts
    for x, y in POSTS:
        s = s.union(cyl(x, y, Z_FLOOR, Z_TOP_IN + 0.01, POST_D)).cut(cyl(x, y, Z_FLOOR - 0.1, Z_FLOOR + 10.0, PILOT_D))
    # microphone chimneys: 1.5 mm bore, land 0.2 mm above the PCB (closed-cell foam gasket ring recommended)
    for x, y in MICS:
        s = s.union(cyl(x, y, 0.2, Z_TOP_IN + 0.01, 5.0)).cut(cyl(x, y, 0.0, Z_TOP_OUT + 0.1, 1.5))
        s = s.cut(cyl(x, y, Z_TOP_OUT - 0.5, Z_TOP_OUT + 0.1, 2.6))            # small countersink on the outside
    # LED light pipes: tube down to the PCB, 0.4 mm skin left at the top surface acts as diffuser
    if LEDS:
        xs = [p[0] for p in LEDS]; ly = LEDS[0][1]
        s = s.union(box(min(xs) - 2.3, ly - 2.3, 0.3, max(xs) + 2.3, ly + 2.3, Z_TOP_IN + 0.01))
        for x, y in LEDS:
            s = s.cut(cyl(x, y, 0.2, Z_TOP_OUT - 0.4, 3.0))
    # mute slider: slot through the top + finger dish on the outside
    sx, sy = SW
    s = s.cut(box(sx - 3.2, sy - 1.3, Z_TOP_IN - 0.1, sx + 3.2, sy + 1.3, Z_TOP_OUT + 0.1))
    dish = (cq.Workplane("XY").slot2D(15.0, 8.0).extrude(1.2).translate((sx, sy, Z_TOP_OUT - 1.2)))
    s = s.cut(dish)
    # speaker: locating ring + hexagonal grille
    ring = cyl(SPK_X, SPK_Y, Z_TOP_IN - 3.0, Z_TOP_IN + 0.01, SPK_D + 2 * FIT + 3.2).cut(
        cyl(SPK_X, SPK_Y, Z_TOP_IN - 3.1, Z_TOP_IN + 0.1, SPK_D + 2 * FIT))
    s = s.union(ring)
    pitch, hole = 3.4, 2.2
    pts = []
    for i in range(-8, 9):
        for j in range(-8, 9):
            px, py = i * pitch + (j % 2) * pitch / 2, j * pitch * 0.866
            if math.hypot(px, py) <= SPK_GRILLE_D / 2 - hole / 2:
                pts.append((SPK_X + px, SPK_Y + py))
    grille = cq.Workplane("XY").pushPoints(pts).circle(hole / 2).extrude(TOP_T + 0.4).translate((0, 0, Z_TOP_IN - 0.2))
    s = s.cut(grille)
    # rear wall windows
    for xc, w, zt, zb in WINDOWS:
        s = s.cut(box(xc - w / 2, Y0 - WALL - 0.1, zb, xc + w / 2, Y0 + 0.1, zt))
    # ventilation slots: right wall (next to the CM4) and front wall
    for i in range(7):
        y = 22.0 + i * 6.0
        s = s.cut(box(X1 - 0.1, y, Z_FLOOR + 4.0, X1 + WALL + 0.1, y + 2.4, Z_PCB_BOT - 3.0))
    for i in range(8):
        x = 50.0 + i * 6.0
        s = s.cut(box(x, Y1 - 0.1, Z_FLOOR + 4.0, x + 2.4, Y1 + WALL + 0.1, Z_PCB_BOT - 3.0))
    return s

# ----------------------------------------------------------------------------- base
def make_base():
    b = (box(X0 + FIT, Y0 + FIT, Z_BOTTOM, X1 - FIT, Y1 - FIT, Z_FLOOR).edges("|Z").fillet(CORNER_R - WALL - FIT))
    for x, y in POSTS:
        b = b.cut(cyl(x, y, Z_BOTTOM - 0.1, Z_FLOOR + 0.1, SCREW_CLEAR_D))
        b = b.cut(cyl(x, y, Z_BOTTOM - 0.1, Z_BOTTOM + 1.4, SCREW_HEAD_D))     # recess for the pan head
    # speaker pedestal (ring) - presses the magnet towards the grille through a foam pad
    z_spk_back = Z_TOP_IN - SPK_DEPTH
    ped_top = z_spk_back - FOAM
    if ped_top > Z_FLOOR + 0.5:
        b = b.union(cyl(SPK_X, SPK_Y, Z_FLOOR - 0.01, ped_top, 24.0).cut(cyl(SPK_X, SPK_Y, Z_FLOOR, ped_top + 0.1, 19.0)))
    # vents under the CM4 / heat sink and under the power stage
    for i in range(9):
        x = 48.0 + i * 5.6
        b = b.cut(box(x, 32.0, Z_BOTTOM - 0.1, x + 2.4, 64.0, Z_FLOOR + 0.1))
    for i in range(4):
        x = 4.0 + i * 5.6
        b = b.cut(box(x, 20.0, Z_BOTTOM - 0.1, x + 2.4, 42.0, Z_FLOOR + 0.1))
    # bass relief holes behind the speaker
    for a in range(0, 360, 60):
        b = b.cut(cyl(SPK_X + 15.5 * math.cos(math.radians(a)), SPK_Y + 15.5 * math.sin(math.radians(a)),
                      Z_BOTTOM - 0.1, Z_FLOOR + 0.1, 3.0))
    # recesses for four 8 mm stick-on feet
    for x, y in ((X0 + 16, Y0 + 9), (X0 + 16, Y1 - 9), (X1 - 16, Y0 + 9), (X1 - 16, Y1 - 9)):
        b = b.cut(cyl(x, y, Z_BOTTOM - 0.1, Z_BOTTOM + 0.5, 8.6))
    return b

# ----------------------------------------------------------------------------- PCB assembly stand-in
# (reference, body size x, y, height, footprint-local centre offset) - simplified keep-in solids
BODIES = {
    "J1": (8.94, 7.35, 3.31, (0, 0.0)), "J6": (14.5, 17.0, 15.7, (3.5, 7.11)), "J4": (13.85, 15.95, 1.68, (0, 0.25)),
    "L1": (7.3, 6.6, 2.8, (0, 0)), "U11": (12.9, 15.0, 2.2, (0, 0)), "J7": (5.9, 4.5, 6.0, (1.0, -0.5)),
    "J5": (2.54, 7.62, 8.5, (0, 2.54)), "U4": (6, 6, 0.9, (0, 0)), "U2": (4.9, 6.0, 1.7, (0, 0)), "U1": (4, 4, 0.6, (0, 0)),
}
CM4 = dict(x0=44.0, y0=28.0, w=55.0, h=40.0, stack=1.5, pcb=1.2, comp=2.4, hs=(14.0, 14.0, 6.0), soc=(71.5, 48.0))

def make_pcb_assembly():
    pcb = box(0, 0, -PCB_T, PCB_W, PCB_H, 0).edges("|Z").fillet(3.0)
    for x, y in HOLES:
        pcb = pcb.cut(cyl(x, y, -PCB_T - 0.1, 0.1, 2.7))
    parts = cq.Workplane("XY")
    for ref, (bx, by, bh, (ox, oy)) in BODIES.items():
        if ref not in PLACEMENT: continue
        x, y, rot, _ = at(ref)
        dx, dy = rot_pt(ox, oy, rot)
        sx, sy = (bx, by) if int(rot) % 180 == 0 else (by, bx)
        parts = parts.union(box(x + dx - sx / 2, y + dy - sy / 2, Z_PCB_BOT - bh, x + dx + sx / 2, y + dy + sy / 2, Z_PCB_BOT))
    # CM4 module + heat sink, hanging below the carrier
    c = CM4
    z = Z_PCB_BOT - c["stack"]
    parts = parts.union(box(c["x0"], c["y0"], z - c["pcb"], c["x0"] + c["w"], c["y0"] + c["h"], z))
    parts = parts.union(box(c["x0"] + 6, c["y0"] + 4, z - c["pcb"] - c["comp"], c["x0"] + c["w"] - 4, c["y0"] + c["h"] - 4, z - c["pcb"]))
    hx, hy, hh = c["hs"]
    parts = parts.union(box(c["soc"][0] - hx / 2, c["soc"][1] - hy / 2, z - c["pcb"] - c["comp"] - hh,
                            c["soc"][0] + hx / 2, c["soc"][1] + hy / 2, z - c["pcb"] - c["comp"]))
    # mute switch on the top-facing side: body 9 x 3.6 x 3.5, slider 2 x 1.5 x 2
    sx, sy = SW
    parts = parts.union(box(sx - 4.5, sy - 1.8, 0, sx + 4.5, sy + 1.8, 3.5)).union(box(sx - 2.0, sy - 0.75, 3.5, sx, sy + 0.75, 5.5))
    # speaker (frame + magnet)
    spk = cyl(SPK_X, SPK_Y, Z_TOP_IN - 4.0, Z_TOP_IN, SPK_D).union(cyl(SPK_X, SPK_Y, Z_TOP_IN - SPK_DEPTH, Z_TOP_IN - 4.0, 26.0))
    return pcb, parts, spk

def summary():
    return dict(outer_x=round(X1 - X0 + 2 * WALL, 1), outer_y=round(Y1 - Y0 + 2 * WALL, 1), height=round(Z_TOP_OUT - Z_BOTTOM, 1),
                mic_ports=MICS, leds=LEDS, mute=SW, pcb_bosses=HOLES, base_posts=POSTS, speaker=(SPK_X, SPK_Y))

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else HERE
    shell, base = make_shell(), make_base()
    pcb, parts, spk = make_pcb_assembly()
    print(json.dumps(summary()))
    # interference check: PCB assembly vs. printed parts must not intersect
    for name, a in (("pcb", pcb), ("components", parts), ("speaker", spk)):
        for pn, p in (("shell", shell), ("base", base)):
            vol = a.intersect(p).val().Volume() if a.intersect(p).vals() else 0.0
            print("interference %-10s vs %-5s: %.3f mm^3" % (name, pn, vol))
    # print orientation: shell upside down (top on the bed), base as modelled (flat side down)
    shell_print = shell.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_TOP_OUT))
    base_print = base.translate((0, 0, -Z_BOTTOM))
    for name, obj in (("voxhub_shell", shell_print), ("voxhub_base", base_print)):
        cq.exporters.export(obj, os.path.join(out, name + ".stl"), tolerance=0.02, angularTolerance=0.2)
        cq.exporters.export(obj, os.path.join(out, name + ".step"))
        cq.exporters.export(obj, os.path.join(out, name + ".3mf"), tolerance=0.02, angularTolerance=0.2)
    asm = (cq.Assembly().add(shell, name="shell", color=cq.Color(0.85, 0.85, 0.88, 0.35))
           .add(base, name="base", color=cq.Color(0.3, 0.3, 0.32)).add(pcb, name="pcb", color=cq.Color(0.0, 0.45, 0.2))
           .add(parts, name="components", color=cq.Color(0.7, 0.7, 0.72)).add(spk, name="speaker", color=cq.Color(0.15, 0.15, 0.15)))
    asm.save(os.path.join(out, "voxhub_assembly.step"))
