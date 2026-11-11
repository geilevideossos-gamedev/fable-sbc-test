# Enclosure

Parametric CadQuery model of the VoxHub CM4 case: `voxhub_enclosure.py`.

| File | Purpose |
|---|---|
| `voxhub_enclosure.py` | the model; all dimensions are constants at the top, PCB-dependent positions come from `../hardware/gen/placement.json` |
| `voxhub_shell.{stl,3mf,step}` | top + walls, **already oriented for printing** (top face on the bed) |
| `voxhub_base.{stl,3mf,step}` | bottom plate, oriented for printing (outside face on the bed) |
| `voxhub_assembly.step` | shell + base + PCB assembly stand-in + speaker, for checking in any CAD tool |
| `render.py`, `renders/` | off-screen renders (closed, open, cross-sections, transparent top view) |

![rear](renders/enclosure_rear.png)
![open](renders/enclosure_open_bottom.png)

## Concept

- Outer size **158.8 x 79.2 x 28.0 mm**, 2.0 mm walls, 5 mm corner radius.
- The PCB hangs **component side down** on four bosses under the top plate (4 mm gap); the CM4 and its heat sink
  face the vented base. The speaker sits beside the PCB and fires upwards through a hexagonal grille.
- Features that line up with the PCB (all taken from the placement file):
  - rear wall windows: USB-C (13.4 x 7.5 - the plug overmould enters the wall), stacked USB-A (15.6 x 17.0),
    microSD (14.0 x 7.2 including the finger notch, centred on the card, not on the socket body);
  - two microphone chimneys: 5 mm tube from the top plate down to the PCB, 1.5 mm bore, total acoustic path
    1.6 (PCB) + 4.0 + 2.0 = 7.6 mm;
  - three LED light pipes above the reverse-mount LEDs, closed by a 0.4 mm skin that acts as a diffuser;
  - slot (6.4 x 2.6 mm) + finger dish (16 x 10 x 1.4 mm) for the mute slider (SW1 is on the PCB side that faces the top);
    the slider stands 0.9..1.0 mm proud of the dish floor and stays 0.4..0.5 mm below the outer surface;
  - four PCB bosses (2.1 mm pilot for 2.5 mm thread-forming screws) and four base posts;
  - speaker locating ring (40.8 mm for the 40 +-0.3 mm frame) + grille with a 1 mm deep, 35.6 mm wide relief in front of
    the cone (the speaker's mounting notice asks for at least 0.8 mm); a 13..21 mm ring pedestal on the base clamps the
    23 mm yoke through a foam pad;
  - vents: base slots under the CM4 and the power stage, wall slots next to the CM4.

## Printing (Bambu Lab X1 / P1 / A1, 0.4 mm nozzle)

| Setting | Value |
|---|---|
| Material | PETG or PLA (PETG recommended: the buck area reaches ~60 C) |
| Layer height | 0.2 mm, first layer 0.2 mm |
| Walls / top-bottom | 3 walls, 4 top/bottom layers, 15 % gyroid |
| Supports | **none** |
| Orientation | as exported: shell upside down (smooth top from the PEI plate), base flat |
| Bed | both parts fit a 256 x 256 mm plate together |

Why no supports are needed: every boss, post, chimney and light pipe grows straight up from the top plate; the rear
connector windows are closed rectangles whose top edge is a bridge of at most 15.6 mm; the mute dish is a 1.4 mm deep,
10 mm wide recess in the first layers (bridged); the speaker relief is an open pocket on the inside; grille and vent holes are vertical. The LED windows keep a 0.4 mm skin
(two layers) - use a light filament colour or print the first two layers in translucent material if the LEDs
should be clearly visible.

## Assembly

1. Stick 0.5 mm foam rings (5 mm OD / 2 mm ID) on the two microphone chimneys (acoustic seal).
2. Fit the CM4 on the carrier (4 x M2.5 x 5 into the SMT spacers), stick the heat sink on the SoC, insert the SD card.
3. Solder 80 mm leads to the speaker, crimp/plug the JST-PH housing; drop the speaker into its ring (cone down in
   print orientation, i.e. facing the grille).
4. Lay the PCB on the four bosses (component side towards you), make sure the mute slider enters its slot, fasten with
   4 x 2.5 x 6 mm thread-forming screws. Plug the speaker into J7.
5. Put the foam pad on the base pedestal, close the base, fasten with 4 x 2.5 x 8 mm screws, stick on the feet.

## Verification

- `voxhub_enclosure.py` intersects the PCB, the component keep-in solids (connectors, CM4 + heat sink, inductor,
  radio module, headers, mute switch) and the speaker with both printed parts and prints the interference volume:
  **0.000 mm^3** for all six pairs.
- `renders/fit_top_transparent.png`, `section_cm4.png` and `section_front_row.png` show the PCB inside the shell.

## Dimensions checked against the manufacturer drawings

Revision A assumed three part dimensions; they were checked against the drawings on 2026-11-11 (sources in
DECISIONS.md section 9) and the constants at the top of `voxhub_enclosure.py` were updated:

| Part | Drawing says | Model |
|---|---|---|
| Wurth 61400826021 (stacked USB-A) | shell 13.1 x 17.0 mm, 15.34 mm high; front flange 14.5 +-0.2 x 15.5 +-0.2 with lips 0.45 and 15.95 mm above the PCB; front face 2.5 mm beyond the PCB edge | overhang 2.5 mm confirmed; window 15.6 x 17.0 mm (was 15.2 x 16.5); 2.4 mm left to the base at maximum material |
| GCT USB4105-GF-A (USB-C) | shell 8.94 x 3.31 mm, ends flush with the PCB edge, i.e. 2.6 mm inside the wall | window 13.4 x 7.5 mm so that a 12.35 x 6.5 mm plug overmould can enter (was 12.4 x 6.3) |
| C&K JS202011JCQN (mute switch) | body 9.0 x 3.6 x 3.5 mm, actuator 1.5 x 1.5 mm, 2.0 mm high, 2 mm travel | `GAP_TOP` = 4.0 mm confirmed; dish 16 x 10 x 1.4 mm |
| Same Sky CMS-4017-34SP (speaker) | dia 40 +-0.3, depth 17.5 +-0.3, yoke dia 23, baffle opening dia 35.6 with >= 0.8 mm free in front of the diaphragm | ring 40.8 mm, relief 35.6 x 1.0 mm, pedestal 13..21 mm; terminals sit 4..8.8 mm behind the flange, clear of the 3 mm ring |
| Hirose DM3AT (microSD) | card centre 0.425 mm off the body centre; locked card 1.6 mm behind the outer wall face | window shifted by 0.425 mm; eject = push the card in by 0.8 mm with a fingernail |
| CM4 + heat sink | SoC 2.378 +-0.11 mm, centre 31.99 / 16.98 mm from the module edges; 1.5 mm stack | heat sink position corrected in the fit model; 6.7 mm left under the heat sink |

Still to be measured on real parts: the USB-A flange lips were scaled from the drawing (not dimensioned), and the C&K
drawing has no body tolerance. A first test print for fit is still the right next step.
