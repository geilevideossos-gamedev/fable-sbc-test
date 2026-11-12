# VoxHub CM4, revision A2 - printing, assembly and bring-up test

This guide takes you from the parcel with the assembled boards to a closed, tested device. There is no soldering
anywhere. Work through the chapters in this order:

1. [Print the enclosure](#1-print-the-enclosure)
2. [Tools and parts on the table](#2-tools-and-parts-on-the-table)
3. [Bring-up of the bare board, before it goes into the case](#3-bring-up-before-assembly)
4. [Mechanical assembly](#4-mechanical-assembly)
5. [Troubleshooting and electrical safety](#5-troubleshooting-and-electrical-safety)
6. [What could not be verified](#6-what-could-not-be-verified)
7. [Two devices: hub and satellite](#7-two-devices-hub-and-satellite) - setup of the hub's Claude pipeline, the
   satellite image, pairing, rooms, the Zigbee router and the tests from both rooms

The two assembled boards are identical. Board 1 becomes the **hub** (Home Assistant OS, chapters 1 to 4 as
written), board 2 the **satellite**: chapters 1 and 2, chapter 3 tests 1 to 5 and 7 (with the satellite card of
section 7.3 instead of part A of test 6), sections 7.3 and 7.4 (its software tests), then chapter 4 and the rest
of chapter 7.

Status of this text: it was written on 2026-11-12 for hardware revision A2. **No board has been built yet.** Every
expected value below comes from the schematic (`hardware/gen/design.py`), the board file, the enclosure model or a
data sheet, not from a measurement. Values marked "estimate" are estimates. Part numbers, on-screen labels and
software versions were read on 2026-11-12; the source is named where it matters.

All positions on the board were read from `hardware/voxhub.kicad_pcb` as committed in `6776424` (the board as
rebuilt after the first review round). If the board is generated again, the parts that the generator places by
itself can move: D4, D6, D10, C38, C41, JP1, C13 and the three test pads. Their coordinates in this guide then have
to be read again.

## Conventions used in this guide

**The two sides of the board**

| Name in this guide | What is on it | Where it ends up in the case |
|---|---|---|
| component side | all connectors, the two sockets for the compute module, almost all parts | faces down, towards the base plate |
| bare side | only the mute slide switch SW1, three LEDs and white text, among it `this side faces the top cover` | faces up, towards the top cover |

JLCPCB and `fab/ORDER_GUIDE.md` call the component side **Top** and the bare side **Bottom**. This guide avoids
these two words, because in the finished device the "Top" side of the board faces down.

**Board coordinates.** Lay the board with the component side up and turn it so that the edge with the three
connectors (USB-C, double USB-A, microSD) points away from you. That edge is the **rear edge**. `x` is measured in
millimetres from the **left** board edge, `y` from the **rear** edge towards you. The board is 100 x 74 mm. The USB-C
socket is then in the rear left corner. A position is written as (x / y), for example D1 at (4.2 / 12.3).

**Reference designators are not printed on the board.** Names such as D1, L1 or C38 exist only in the schematic.
The only texts on the component side are `VoxHub CM4  rev A2`, `J5: GND TX RX`, `SPK` and the three test-pad labels
`5V`, `3V3` and `GND`. Find a part by its coordinates, by the description in the table and by this map
(1 character = 2 mm wide, 1 line = 4 mm):

```
        x = 0        20        40        60        80       100 mm
          +--------------------------------------------------+  rear edge
  y =  0  |    .....     ........  ........                  |
  y =  4  |    .USB.     . USB  .  .micro .                  |
  y =  8  |    ..C..     .  A   .  .  SD  .             MK2  |
  y = 12  | D1           .      .  .      .         TP       |
  y = 16  |         U1   ........  ........                  |
  y = 20  |  C8C9   D4        C41 C38               J5       |
  y = 24  |   U2 D6                                          |
  y = 28  |                      ............................|
  y = 32  |                      .                          .|
  y = 36  |   L1                 .                          .|
  y = 40  | C14-17               .       compute module     .|
  y = 44  |      ..........      .       (CM4) on two       .|
  y = 48  |      .        .      .       100-pin sockets    .|
  y = 52  |      .        .      .                          .|
  y = 56  | J7   . radio  .      .                          .|
  y = 60  |      . module .      .                          .|
  y = 64  |      .        .      .                          .|
  y = 68  | MK1  .        .      ............................|
  y = 72  |      ..........                         D10      |
          +--------------------------------------------------+  front edge
```

Rendered pictures of both sides (the render shows the compute module and its heat sink already fitted):
[component side](../hardware/outputs/render_top.png), [bare side](../hardware/outputs/render_bottom.png).

**The three test pads (TP).** To the right of the microSD socket there are three bare round pads, 1.5 mm in
diameter. Each has a label printed next to it. There is no test pad for the charger voltage, on purpose: that
voltage is measured on the large pads of D1 and of C8 / C9 (see "Probe points" in chapter 3).

```
                rear edge of the board

                               GND                 <- label of the rear pad: directly behind its pad
                               (O)                 <- pad GND
      3V3           (O)        (O)         5V      <- pad 3V3 (label on its left), pad 5V (label on its right)

            J5: GND TX RX                          <- printed text
                 [O]       O        O              <- the three holes of J5: square = GND, then TX, then RX
```

| Pad | Printed label, and where it is | Pad at (x / y) | Label at (x / y) | Net | Voltage when the board runs |
|---|---|---|---|---|---|
| TP1 | `5V`, directly to the right of the pad | (84.0 / 12.0) | (87.5 / 12.0) | +5V | 5 V |
| TP2 | `3V3`, directly to the left of the pad | (80.8 / 12.0) | (76.9 / 12.0) | +3V3 | 3.3 V |
| TP3 | `GND`, directly behind the pad (3.3 mm nearer to the rear edge) | (84.0 / 8.8) | (84.0 / 5.5) | GND | 0 V |

Read it like this: the two pads that lie side by side are `3V3` (left) and `5V` (right); the third pad, behind
the `5V` pad, is ground. Its label `GND` is printed directly behind it, in line with the pad; no other test pad is near
that label. The pads `3V3` and `5V` are only 1.7 mm apart. A probe tip that touches both at once puts 5 V on the 3.3 V
parts and can damage them, so the guide uses the `3V3` pad for one live measurement only (test 7).

**The six LEDs**

| LED | Colour | Side | (x / y) | Fed from | Lights when |
|---|---|---|---|---|---|
| D6 | green | component side, next to the 8-pin regulator U2 | (13.2 / 23.6) | the 5 V rail | the 5 V rail is up ("PWR") |
| D4 | red | component side, just in front of the square chip U1 | (17.5 / 21.4) | the FAULT pin of the PD controller | the charger offers nothing between 9 and 20 V with at least 2 A, or VBUS is out of range ("PD FAULT") |
| D10 | green | component side, front edge, in front of the compute module | (84.4 / 72.2) | the 3.3 V rail, switched by the compute module | the compute module accesses the microSD card ("ACT") |
| D7 | green | bare side, front edge | (34.0 / 71.2) | the 5 V rail, switched by GPIO5 | software decides (status) |
| D8 | blue | bare side, front edge | (38.6 / 71.2) | the 5 V rail, switched by GPIO6 | software decides (status) |
| D9 | red | bare side, front edge | (43.2 / 71.2) | the 3.3 V rail through the mute switch, no software involved | the microphones are muted |

In the closed case D7, D8 and D9 shine through the top cover. They are meant to look about equally bright; their
series resistors were chosen for that (5.1 kOhm for green and 2.2 kOhm for blue from 5 V, 150 Ohm for red from
3.3 V). D4, D6 and D10 are inside. Their glow can be seen through ventilation slots: D4 and D6 through the four
short slots of the base next to the speaker side, D10 through the slots of the front wall.

## 1. Print the enclosure

### 1.1 Files

Two parts. Both files are already oriented for printing.

| Part | File (use this one) | Same part as STL | Size | Lies on the build plate with |
|---|---|---|---|---|
| Shell (top cover and four walls) | `enclosure/voxhub_shell.3mf` | `enclosure/voxhub_shell.stl` | 158.8 x 79.2 x 28.0 mm | its top face, the face with the speaker grille; the open side points up |
| Base | `enclosure/voxhub_base.3mf` | `enclosure/voxhub_base.stl` | 154.3 x 74.7 x 7.5 mm | its outer face, the face with the four screw-head recesses; the pedestal points up |

The 3MF files contain geometry only, no print settings. If Bambu Studio says that the file does not come from
Bambu Lab and that only the geometry is loaded, confirm.

### 1.2 Settings in Bambu Studio (A1, P1P / P1S, X1 / X1C, 0.4 mm nozzle)

Start from the process preset **0.20mm Standard @BBL** of your printer and change only the lines marked "change".
The labels are those of Bambu Studio (read from its source on 2026-11-12); the defaults are those of the preset
`0.20mm Standard @BBL A1`.

| Label in Bambu Studio | Set to | Preset default | Why |
|---|---|---|---|
| Filament | **Bambu PETG Basic**, white (the filament of `fab/SHOPPING_LIST.md`); for PETG of another brand the preset **Generic PETG** | - | see 1.3 |
| **Bed type** | **Textured PEI Plate** | - | the PETG presets print at 70 C on this plate; the Cool Plate is not released for PETG (plate temperature 0 in the preset) |
| **Layer height** | 0.2 | 0.2 | the diffuser skin over the LEDs is 0.4 mm = exactly two layers |
| **Initial layer height** | 0.2 | 0.2 | same reason |
| **Wall loops** | 3 (change) | 2 | the 2 mm walls and the screw bosses become solid |
| **Top shell layers** | 5 | 5 | |
| **Bottom shell layers** | 4 (change) | 3 | the visible top face of the shell is the bottom of the print |
| **Sparse infill density** | 15% | 15% | |
| **Sparse infill pattern** | **Gyroid** (change) | Grid | |
| **Enable support** | off | off | the model needs none, see below |
| **Brim type** | **No-brim** (change) | Auto | both parts lie flat with a large contact area; a brim would have to be cut off the visible top edge |
| Temperatures, speeds, cooling | leave as the filament preset sets them | | |

Steps:

1. In Bambu Studio select your printer, the 0.4 mm nozzle, the filament and **Textured PEI Plate**.
2. **Import** `enclosure/voxhub_shell.3mf` and `enclosure/voxhub_base.3mf`. Both fit together on one 256 x 256 mm plate.
3. Do not rotate or flip the parts and do not use **Auto orient**. Use **Arrange all objects** only to move them apart.
4. Enter the settings of the table.
5. **Slice plate**. In the preview check three things: no support material anywhere; the first two layers are closed
   above the three round LED bores of the shell; the two microphone holes (1.5 mm) are open from the first layer on.
6. **Print plate**.

Why no supports are needed: every boss, post, microphone tube and light pipe grows straight up from the top plate;
the connector windows in the rear wall are closed rectangles whose upper edge is a bridge of at most 15.6 mm; the
finger dish of the mute slider is a 1.4 mm deep, 10 mm wide recess that is bridged; the grille and all vents are
vertical holes.

### 1.3 Material

**PETG.** Reasons: the compute module heats the inside of the case (README: about 45 C at the processor when idle,
60 C in normal use, up to 80 C under full load; the area around the 5 V regulator reaches about 60 C), and PETG keeps
its shape at these temperatures better than PLA. PETG is also less brittle: the eight M2.5 screws cut their own
thread into printed 2.1 mm holes, and a PLA boss cracks more easily when that happens.

**PLA** works for a desk test with the case open or for a short trial. Do not use it for the device that runs all day.

Use a light colour. The three LEDs shine through a 0.4 mm skin of the top cover; through black material they are
hard to see.

The filament of the shopping list is Bambu Lab PETG Basic, white, 1 kg (`fab/SHOPPING_LIST.md`, table "Required
for one device"). Any other PETG in a light colour works with the **Generic PETG** preset.

### 1.4 Print time and filament (estimates, not sliced)

| | Shell | Base | Both |
|---|---|---|---|
| Solid volume of the model (computed from the STL files as regenerated on 2026-11-12) | 50.9 cm3 | 29.1 cm3 | 80.0 cm3 |
| Filament, upper limit = solid volume x 1.25 g/cm3 (density in the Bambu PETG Basic preset) | 64 g | 36 g | 100 g |
| Filament, estimate with 15 % infill in the few thick places | | | 85 to 100 g |
| Print time, estimate (the preset limits this filament to 13 mm3/s on an A1) | | | 3.5 to 5 hours |

Bambu Studio shows the real figures after **Slice plate**. One 1 kg spool is enough for about ten enclosures.

### 1.5 After printing

Let the plate cool down before you take the parts off. Then:

1. **Pilot holes for the screws (8 holes, 2.1 mm).** Four are in the short round bosses on the inside of the top
   cover (for the board), four in the long posts in the corners (for the base). Remove strings with a **2.0 mm**
   drill bit turned between your fingers. Do not use a power drill and do not widen the holes.
   **Stop at 5 mm depth in the four short bosses** (wrap a piece of tape around the bit 5 mm from its tip): the hole
   is 5.2 mm deep and only 0.8 mm of the top cover is left behind it. In the four posts the holes are 10 mm deep.
2. **LED diffuser.** Inside, at the front wall, is a small block with three 3 mm bores. From the outside these three
   places must be **closed**. Do not poke through them. Hold the shell against a lamp: three bright dots must be visible.
3. **Microphone holes.** Two 1.5 mm holes go through the top cover, each in the middle of a 5 mm tube on the inside.
   They must be **open**. Push the shank of a 1.5 mm drill bit through by hand, or check that light passes.
4. **Mute slot.** The slot (6.4 x 2.6 mm) in the oval dish must be free of strings.
5. **Connector windows.** Cut off sagging threads at the three windows in the rear wall with a sharp knife.
6. **Base.** An M2.5 screw must drop freely through each of the four 2.9 mm holes, and its head must go into the
   5.2 mm recess. If a head sticks, scrape the wall of the recess with the knife. Clear the vent slots.
7. Do not sand, heat or wash the top face around the LED dots.

### 1.6 Quick fit check with a caliper

Nominal values from the model `enclosure/voxhub_enclosure.py`. A deviation of 0.3 mm is normal for this kind of
print (assumption).

| # | Measure | Nominal | Pass when |
|---|---|---|---|
| 1 | Shell, outside length x width x height | 158.8 x 79.2 x 28.0 mm | within 0.3 mm |
| 2 | Base, length x width | 154.3 x 74.7 mm | the base drops into the open side of the shell without force and lies on the four posts |
| 3 | Base plate thickness / height over the pedestal | 2.4 mm / 7.5 mm (the pedestal itself is 5.1 mm high) | within 0.2 mm |
| 4 | Speaker frame inside the shell, opening | 71.3 x 31.9 mm, 3 mm high | the speaker (70.1 x 30.7 mm) drops in and has about half a millimetre of play on every side |
| 5 | Distance between the centres of the two rear board bosses | 93.0 mm | within 0.3 mm |
| 6 | Distance between the centres of the rear left and front left board boss | 67.0 mm | within 0.3 mm |
| 7 | Height of the four board bosses above the inside of the top cover | 4.0 mm | within 0.2 mm, all four equal |
| 8 | Window for USB-C / double USB-A / microSD in the rear wall, width x height | 13.4 x 7.5 / 15.6 x 17.0 / 14.0 x 7.2 mm | not smaller than nominal minus 0.3 mm |
| 9 | Recesses for the feet in the base | diameter 8.6 mm, 0.5 mm deep | an 8 mm foot fits |
| 10 | Pilot holes | 2.1 mm | the 2.0 mm drill shank enters; an M2.5 screw does not fall in |

The front right board boss is not in line with the other three: it sits 0.5 mm further right and 0.3 mm further
to the front. This is intended.

## 2. Tools and parts on the table

Shops, shop article numbers and prices are in `fab/SHOPPING_LIST.md`: the parts of 2.1 in its table "Required for
one device", the test equipment of 2.2 in its table "Optional: tools for the bring-up tests". The order and the
incoming inspection of the boards are in `fab/ORDER_GUIDE.md`. The part numbers were read on 2026-11-12.

### 2.1 Parts for one device

| Qty | Part | Identification | Used in |
|---|---|---|---|
| 1 | Assembled VoxHub board, revision A2 | from JLCPCB; text `VoxHub CM4  rev A2`. The order brings 2 assembled boards and 3 boards without parts; only the assembled ones are used here | everything |
| 1 | Raspberry Pi Compute Module 4 Lite with wireless, 4 GB | CM4104000 | 3.5 |
| 1 | Heat sink 14 x 14 x 7 mm with adhesive foil | the larger one of the set RPI-2KKS | 3.5 |
| 1 | microSD card | SanDisk High Endurance 64 GB | 3.5, 3.6 |
| 1 | Enclosed speaker 4 Ohm 3 W, 70.1 x 30.7 x 16.5 mm, with a 2-pin plug on a lead of about 50 cm | Adafruit 3351 | 3.5, 4 |
| 8 | Screw M2.5 x 5, pan head, cross recess PH1, DIN 7985 | | 4 for the compute module, 4 for the board |
| 4 | Screw M2.5 x 8, pan head, cross recess PH1, DIN 7985 | | base |
| 4 | Self-adhesive rubber foot 8 x 3 mm | Delock 18308 | 4 |
| 1 | Piece of self-adhesive cellular rubber, 3 mm thick, 40 x 18 mm | cut from the sheet Jamara 059850 | 4 |
| 1 | USB-C PD charger 30 W | Goobay 79153 | permanent supply; test 3 |
| 1 | USB-C to USB-C cable, 60 W, 1 m | Shiverpeaks BS20-75025 | |
| 1 + 1 | Printed shell and base | chapter 1 | 4 |

**Check the plug of the speaker as soon as it arrives.** The header J7 on the board is a JST-PH type with 2.0 mm
between its two pins. Adafruit and BerryBase sell the speaker with a "JST-PH" plug, and their photo shows such a
plug, but the maker's data sheet of the speaker names the plug "XH2.54-2P", which would be a larger plug with
2.5 mm pitch. Two checks:

1. Measure the width of the white plug across the two wires. The right plug (JST-PH) is 5.8 mm wide, the wrong
   one (XH) 7.3 mm (JST's dimensions, quoted from the notes on the speaker in `fab/SHOPPING_LIST.md`).
2. With the board unpowered, push the plug onto J7 (white 2-pin header, text `SPK`, left board edge). It must slide
   in with light finger pressure, one way round only, and sit firmly.

If the plug does not go into the header, it is the 2.5 mm type: stop, do not force it, do not bend the pins of J7,
do not cut anything, and return the speaker. Pull a fitting plug off again by its white body, never by the wires.

Keep the 5 mm and the 8 mm screws in two separate cups. They look alike, and an 8 mm screw in the wrong place
breaks through the top cover.

### 2.2 Only for the bring-up test

| Item | Identification | Needed for |
|---|---|---|
| USB-C PD charger 20 W | Goobay 79151 | test 4 (9 V contract) |
| USB-C PD charger 65 W | Goobay 79155 | test 4 (20 V contract) |
| A supply that delivers only 5 V | any phone charger with a USB-A socket and a USB-A to USB-C cable, or a USB port of a PC | test 4 |
| Digital multimeter with DC voltage, resistance and continuity ranges and pointed probes | PeakTech P 1070 or any other | tests 2, 3, 4, 7 |
| USB-C power meter (optional) | KWS-1902C; plugs between cable and board and shows the negotiated voltage | tests 3, 4 without probing |
| USB memory stick | any | test 8 |
| One Zigbee device, factory reset | for example a Zigbee plug or lamp | test 13 |
| PC with a microSD card reader, Linux or Windows with WSL2 (Ubuntu) | | 3.6 |
| Wi-Fi network with WPA2 password and internet access | the board has no Ethernet and no monitor output | 3.6 onwards |

A multimeter with 1999 counts, like the one of the shopping list, shows at most 19.99 V in its 20 V range. Use the
20 V DC range for the 5 V and 3.3 V rails and for 9, 12 and 15 V on VBUS, and the 200 V DC range for the 20 V of
the 65 W charger.

### 2.3 Tools

| Tool | Note |
|---|---|
| Cross-recess screwdriver PH1 (on the shopping list) | for all twelve screws |
| Caliper | chapter 1.6 |
| Drill bits 2.0 mm and 1.5 mm, used by hand | chapter 1.5 |
| Sharp knife or scissors | windows, cellular rubber |
| Thick book, at least 10 mm, or a flat piece of wood | support when the compute module is pressed in (3.5) |
| Sheet of cardboard | insulating underlay for the board on the desk |
| Adhesive tape or one small cable tie | to bundle the speaker lead |

Apart from the screwdriver, the tools of 2.3 are ordinary workshop and household items and are not on the
shopping list.

### 2.4 Handling rules that apply from now on

- Hold the board by its edges. Before you touch it, touch an earthed metal object (for example the bare metal of a
  radiator) to discharge yourself.
- **Never wash the board** and never use spray cleaner, alcohol or compressed air on it. The two microphones are open
  to the bare side through 0.8 mm holes (next to the texts `MIC - NO WASH`); liquid or an air blast destroys them.
- **Do not press on the microphones** (two small metal cans, MK1 at (9.5 / 70.2) and MK2 at (92.0 / 10.0)) and do not
  put a probe, a needle or tape on their holes on the bare side.
- **Never plug in or pull off the compute module while the charger is connected.**
- With the charger connected, keep screws, the screwdriver, the heat sink and other metal away from the board.

## 3. Bring-up before assembly

All tests are done on the bare assembled board on the desk, in exactly this order. Do not skip ahead: each test
protects the parts that are added in the next one. Write the results into the table in [3.14](#314-results-table).

Setup for tests 1 to 4: a sheet of cardboard on the desk, the board on it with the component side up, the rear edge
away from you. **No compute module, no microSD card, nothing in the USB-A sockets, speaker not connected.** The board
rests on the mute slider of the bare side and rocks a little. That is harmless as long as you do not press down on it.

### Probe points

Use only these points. They are large pads; the charger voltage is found on D1 and on C8 / C9 only. Never probe
the pins of a chip or the small parts around them.

| Net | Part | Touch here | (x / y) | How to recognise it |
|---|---|---|---|---|
| GND | J6, double USB-A socket | anywhere on its metal shell | around (35 / 6) | the tall metal box at the rear edge |
| VBUS | D1, protection diode | its **rear** solder pad, the end towards the board edge (the end with the printed bar) | (4.2 / 10.1) | black rectangular part 4.3 x 3.6 mm standing 4 mm from the left edge, between the corner hole and the USB-C socket; the largest black two-leg part of the board |
| GND | D1 | its **front** solder pad | (4.2 / 14.4) | same part, other end |
| VBUS_SW | C8 and C9, input capacitors | the two **inner** ends that face each other | (8.0 / 19.0) and (9.8 / 19.0) | two brown capacitors 3.2 x 1.6 mm lying end to end in one line, in the row directly behind the 8-pin regulator U2 (between U2 and the USB-C socket); their outer ends are GND |
| +5V | L1, inductor | its **left** terminal, the side towards the board edge | (5.0 / 34.6) | grey block 7 x 6.6 mm, the largest part at the left edge. Do not touch its right terminal: that is the switching node |
| +5V | C14 and C16, output capacitors | their **left** ends | (4.3 / 39.6) and (4.3 / 42.0) | the left two of four brown capacitors that form a 2 x 2 block directly in front of L1; the right ends are GND |
| supply of one USB-A port | C38, polymer capacitor | its **left** end (the end with the printed bar) | (43.3 / 17.8) | moulded block 3.5 x 2.8 mm, the right one of two, directly in front of the USB-A socket; right end = GND |
| supply of the other USB-A port | C41, polymer capacitor | its **rear** end (the end with the printed bar) | (40.1 / 16.9) | same kind of block, the left one, at right angles to C38; front end = GND |
| +3V3 | TP2, test pad | the round pad with the label `3V3` on its left | (80.8 / 12.0) | see "The three test pads" above; the pad `5V` is 1.7 mm to its right |
| +5V | TP1, test pad | the round pad with the label `5V` on its right | (84.0 / 12.0) | same group of pads |
| GND | TP3, test pad | the round pad behind the `5V` pad; its label `GND` is printed directly behind it | (84.0 / 8.8) | same group of pads |
| GND next to the test pads | J5, empty 3-hole footprint | the **left, square** hole | (80.0 / 21.5) | three gold holes in a row, 4 mm in front of the text `J5: GND TX RX`; the probe tip sits in the hole and cannot slip |

### 3.1 Test 1 - visual inspection (no power)

The thorough incoming inspection with a magnifier is in `fab/ORDER_GUIDE.md`, section "Incoming inspection - before
anything is plugged in". If you have done it, this test is a short repetition of the points that matter before
power is applied.

1. Component side: the three sockets at the rear edge (USB-C, double USB-A, microSD) sit straight and flat.
2. The two sockets for the compute module (two black strips, 100 contacts each, at y = 31 and y = 65) are clean:
   no solder splashes, no bent contacts, no fibres. The four threaded spacers around them stand upright.
3. The radio module (flat board with a metal can, 16.5 x 30 mm, front left) lies flat; its end without the can
   reaches the front edge.
4. The white 2-pin header J7 (text `SPK`) at the left edge is present.
5. D1: the printed bar is at the end towards the rear edge.
6. C38 and C41: the printed bar of C38 is at its left end, the bar of C41 at its rear end. A polymer capacitor that
   is mounted the wrong way round can burn when the USB ports are switched on.
7. Bare side: the slide switch (text `MUTE`) and three small LEDs at the front edge are present.
8. No part is tilted, lifted at one end ("tombstone") or missing compared with the
   [render](../hardware/outputs/render_top.png).

These places are empty **on purpose**: the three holes of J5, the three test pads, six small round pads with three
holes at (36.5 / 46.0) (J8), two small pads side by side at (84.6 / 69.7) (JP1, must **not** be bridged), and one
unpopulated tiny footprint at (3.8 / 28.2) (C13).

| Expected | If not |
|---|---|
| Everything in the list is true | (a) A part is missing, tilted or the wrong way round: do not power the board; send a photo to JLCPCB and ask for rework. (b) Dirt or a fibre in a compute-module socket: remove it with a dry soft brush, never with liquid. (c) JP1 is bridged with solder: the compute module would wait for USB boot instead of starting from the card; report it. |

### 3.2 Test 2 - no short circuit (no power, multimeter)

Set the multimeter to continuity (the beeper), then for the reading to resistance. Mind the colours: the red probe
goes to the supply point. With the probes swapped the protection diodes conduct and the reading means nothing.

| Check | Red probe | Black probe | Expected (estimates, nothing has been measured yet) |
|---|---|---|---|
| VBUS to GND | D1 rear pad | D1 front pad | no continuous beep; a steady reading above 1 kOhm or "OL" |
| +5V to GND | C14 left end | C14 right end | a beep of at most two seconds, then a reading that climbs for several seconds while 180 uF of capacitors charge; it must pass 1 kOhm |
| +3V3 to GND | test pad `3V3` | test pad `GND` (the pad behind the `5V` pad) | no continuous beep; a steady reading above 100 Ohm |
| VBUS to +5V | D1 rear pad | C14 left end | no continuous beep; a steady reading above 1 kOhm or "OL" |

| Expected | If not |
|---|---|
| No continuous beep in any of the four checks | A continuous beep or a steady reading below 5 Ohm is a short circuit. Most likely: (a) the probes touch both ends of the part at once or are swapped - repeat; (b) a solder bridge at the USB-C socket (VBUS check), at the regulator U2 or a cracked capacitor (+5V check), at one of the fine-pitch chips (+3V3 check); (c) D1, C38 or C41 mounted the wrong way round. Do not power a board with a short; report it to JLCPCB. |

### 3.3 Test 3 - first power from the 30 W charger

1. Check again: no compute module, no card, nothing metallic under or on the board.
2. Set the multimeter to DC voltage, 20 V range (15 V is expected here).
3. Plug the USB-C cable into the Goobay 30 W charger and into the board, then plug the charger into the wall socket.
4. Look at the LEDs. Within about one second (estimate) the green LED D6 lights. The red LED D4 is dark; a single
   short red flash at the moment of plugging in is possible.
5. Hold the black probe on the shell of the USB-A socket and measure with the red probe:

| Measure | Red probe on | Expected | Allowed range |
|---|---|---|---|
| VBUS | D1 rear pad | 15.0 V | 14.25 to 15.75 V (the 5 % a USB PD supply is allowed) |
| VBUS_SW (behind the load switch Q1) | inner ends of C8 / C9 | the same as VBUS | at most 0.1 V lower |
| +5V | left terminal of L1, or left end of C14 | 5.02 V | 4.86 to 5.23 V without load (`hardware/README.md`); the compute module accepts 4.75 to 5.25 V |

LEDs in this state (charger with a valid contract, no compute module):

| LED | State | Reason |
|---|---|---|
| D6 green | on | 5 V rail is up |
| D4 red | off | no fault |
| D10 green | off | it is fed from the 3.3 V rail, which only the compute module produces |
| D7 green, D8 blue | off | switched by the compute module |
| D9 red | off in both slider positions | fed from 3.3 V |

6. Unplug the charger from the board. D6 fades within a few seconds.

| Expected | If not |
|---|---|
| D6 on, D4 off, all three voltages in range | **Nothing lights and VBUS is 0 V:** (a) plug not fully inserted or charger without mains; (b) turn the USB-C plug by 180 degrees - if it works only one way round, one contact row of the socket J1 is not soldered. **D4 red on, D6 off, VBUS about 5 V:** no contract, see test 4, last row. **VBUS 15 V, but D6 off and +5V is 0 V:** measure VBUS_SW. 0 V there: the load switch Q1 or its gate network is faulty. 15 V there: the regulator U2 does not start or the 5 V rail is shorted (repeat test 2). **+5V outside 4.86 to 5.23 V:** stop; do not fit the compute module; the regulator or its two feedback resistors are faulty. **A part gets hot or smells:** unplug at once. |

### 3.4 Test 4 - USB PD with a 20 W, a 30 W and a 65 W charger, and with a plain 5 V supply

How the board chooses: the PD controller U1 (Infineon CYPD3177) needs no software. Four resistor dividers on its
pins tell it what to ask for (`hardware/gen/design.py`; the values are the rows of the tables in its data sheet):

| Setting | Resistors on the board | Meaning |
|---|---|---|
| VBUS_MIN | R1 5.1 kOhm to 3.3 V, R2 1 kOhm to ground | at least 9 V |
| VBUS_MAX | R3 0 Ohm to 3.3 V | at most 20 V |
| ISNK_COARSE | R4 5.1 kOhm to 3.3 V, R5 2.4 kOhm to ground | at least 2 A |
| ISNK_FINE | R6 0 Ohm to ground | plus 0 mA |

It goes through the charger's fixed offers from the highest voltage downwards and takes the first one between 9 and
20 V that offers at least 2 A (DECISIONS.md, section 2). Adjustable (PPS) offers are ignored. Only when such a
contract exists does it close the load switch Q1; the 5 V regulator behind it starts at 7.0 V. If no offer fits, it
stays at 5 V, sets its FAULT pin (red LED D4) and leaves Q1 open.

For each supply: plug it in, wait two seconds, note the LEDs, measure VBUS at the rear pad of D1 and +5V at L1 or
C14 (black probe on the USB-A shell), unplug, wait until D6 is dark. For the 65 W charger set the multimeter to the
200 V range before you plug it in.

| Supply | Fixed offers according to the manufacturer (read 2026-11-12) | Contract | VBUS at D1, expected (allowed) | +5V | D6 green | D4 red |
|---|---|---|---|---|---|---|
| Goobay 79151, 20 W | 5 V / 3 A, 9 V / 2.2 A, 12 V / 1.7 A | **9 V** (12 V is skipped: below 2 A) | 9.0 V (8.55 to 9.45) | 5.02 V (4.86 to 5.23) | on | off |
| Goobay 79153, 30 W | 5 V / 3 A, 9 V / 3 A, 12 V / 2.5 A, 15 V / 2.0 A, 20 V / 1.5 A | **15 V** (20 V is skipped: 1.5 A) | 15.0 V (14.25 to 15.75) | 5.02 V (4.86 to 5.23) | on | off |
| Goobay 79155, 65 W | 5 V / 3 A, 9 V / 3 A, 12 V / 3 A, 15 V / 3 A, 20 V / 3.25 A | **20 V** | 20.0 V (19.0 to 21.0) | 5.02 V (4.86 to 5.23) | on | off |
| optional: Raspberry Pi 27 W supply SC1152 | 5.1 V / 5 A, 9 V / 3 A, 12 V / 2.25 A, 15 V / 1.8 A | **12 V** (15 V is skipped: 1.8 A) | 12.0 V (11.4 to 12.6) | 5.02 V (4.86 to 5.23) | on | off |
| plain 5 V supply (phone charger with USB-A socket, PC port) | 5 V only | **none** | about 5 V (4.75 to 5.5) | 0 V | **off** | **on** |

What the plain 5 V supply looks like: only the red LED D4 next to the square chip lights, steadily. D6 stays dark,
VBUS_SW at C8 / C9 is 0 V, the 5 V rail is 0 V, nothing gets warm. With a compute module fitted nothing would
start. This is the intended behaviour: the board stays off instead of running on too little power.

The 20 W charger is a test case, not a supply for daily use: 9 V / 2.2 A is only just above the theoretical peak
demand of 19.2 W (README, power budget).

| Expected | If not |
|---|---|
| The four contract voltages of the table; +5V the same in all cases; with 5 V only: red on, green off | **D4 red with a PD charger:** (a) the charger has no fixed offer of at least 2 A between 9 and 20 V - the smallest offer that works is 9 V / 2 A (18 W); (b) a cable with a USB-A plug at one end; (c) wrong strap resistors on the board (R1 to R6) - then every charger fails. **A different contract voltage than in the table:** the charger's offers differ from the manufacturer's table; check with the USB-C meter or another charger. Any contract between 9 and 20 V is acceptable as long as +5V is in range. **D6 green on a plain 5 V supply:** the load switch Q1 is shorted; do not use the board. |

### 3.5 Test 5 - fit the heat sink, the compute module, the card and the speaker

The card must contain the image before it goes in. If you have not written it yet, do part A of
[3.6](#36-test-6---first-boot-of-home-assistant-os) now and come back.

**The charger is unplugged and D6 is dark.**

Heat sink:

1. Put the compute module on its anti-static bag on the desk, the side with the large chips up. (It is not powered,
   so the bag is the right underlay here.)
2. Find the processor: the largest chip, with a metal lid, marked BROADCOM.
3. Take the larger heat sink of the set (14 x 14 x 7 mm). Peel off the protective foil, place the heat sink centred
   on the metal lid and press it down for about ten seconds. It must not touch a neighbouring part.

Compute module:

4. Lay the book on the desk. Put the board on it, component side up, so that the right-hand part of the board lies
   flat on the book and the left part overhangs: the left edge of the book is directly left of the two left-hand
   threaded spacers (x = 47.5). The mute switch on the bare side (around x = 33) then hangs free. Without this
   support the pressing force would go through the mute switch.
5. Orientation: heat sink up. The short edge of the module that carries the wireless antenna (a flat area without
   parts next to a tiny round gold socket) points to the **right** board edge, away from the USB-C socket.
6. Lower the module onto the two sockets. Check from above: the four holes of the module sit exactly over the four
   threaded spacers. If the holes are about 5 mm off, the module is turned by 180 degrees. Do not press; turn it.
7. Move the module a fraction of a millimetre until you feel both connectors drop into their guides. It then no
   longer slides sideways.
8. Press with two fingers on each of the two long edges of the module, directly above the two connectors (each
   connector is about 20 mm long and lies under the middle of a long edge). Press all at once and straight down
   until both connectors are home. Do not press on the heat sink, on the processor or on the metal can.
9. Check from the side: the module is parallel to the board, with the same 1.5 mm gap everywhere, and rests on all
   four spacers. If it is tilted, lift it off and start again at step 6.
10. Fasten the module with **4 x M2.5 x 5**. Start all four, then tighten them crosswise. Stop as soon as the head
    sits on the module: the spacers allow at most 0.35 N m (Wuerth drawing), which is far less than a full hand
    can apply. Hold the screwdriver with two fingers.

Card and speaker:

11. Put the board back on the cardboard. Push the microSD card into the socket at the rear edge, contacts towards
    the board (label up), until it clicks. To take it out, push it in again and let it come out.
12. Plug the speaker into J7 (white header, text `SPK`, left edge). The plug fits one way only and must slide in
    without force. If it does not fit, it is the wrong plug type (see the check in 2.1): stop and do not force it.
    Lay the speaker beside the board with its sound opening up, not on the board.

Rules for the compute module:

- **Never plug it in or pull it off with the charger connected**, and never while D6 is still glowing.
- The connectors are rated for 30 mating cycles (Hirose). Do not take the module off without a reason.
- To remove it: take out the four screws and lift the module straight up. If it sticks, lift one **short** edge a
  little first. Never lever up one long edge: that breaks the connectors (Hirose DF40 guideline).

| Expected | If not |
|---|---|
| Module flat on four spacers, four screws seated, card clicked in, speaker plugged in | (a) The module does not go down: it is offset by one contact or rotated - lift it and start again, never use force. (b) A screw does not catch: it is not straight in the spacer - back it out and start it by hand. (c) The card does not click: it is upside down. (d) The speaker plug does not go into J7: it is a plug with 2.5 mm pitch instead of the JST-PH plug with 2.0 mm - return the speaker; tests 9 to 11 can be done only with a fitting speaker. |

### 3.6 Test 6 - first boot of Home Assistant OS

The board has no Ethernet and no monitor output. The Wi-Fi name and password therefore have to be inside the image.

**Part A - make the image and write the card (on the PC)**

`os/build-image.sh repack` downloads the official Home Assistant OS image for the Raspberry Pi 4 family and adds the
VoxHub lines to `config.txt` (USB host mode, sound card, UART of the radio, LEDs, mute switch) and a Wi-Fi profile.
The result still receives the official updates. The script is written for Linux (Debian, Ubuntu); it needs no root
rights and no loop devices, so it should also run in WSL2 with Ubuntu on Windows (untested).

1. Open a terminal and run:

   ```bash
   sudo apt install git curl xz-utils fdisk mtools device-tree-compiler
   git clone https://github.com/geilevideossos-gamedev/fable-sbc-test.git
   cd fable-sbc-test
   git checkout claude/gallant-hamilton-kojnjj
   ./os/build-image.sh repack --wifi-ssid 'NAME OF YOUR WIFI' --wifi-psk 'PASSWORD OF YOUR WIFI' --wifi-country AT
   ```

   The line `git checkout ...` is needed as long as the two-device version (hub + satellite) has not been merged
   into the branch `main` (state on 2026-11-12: revision A2 is in `main`, the two-device version only in this
   branch). Keep the single quotes around the Wi-Fi name and the password. `AT` is the country code for
   Austria; without the option the script sets `US`.
2. Wait about two minutes (os/README: 93 seconds on the build machine, 310 MB). The last lines name the result:
   `os/output/haos_voxhub-cm4-18.5.img.xz`. 18.5 was the newest stable Home Assistant OS on 2026-11-12; a later
   version changes the number in the file name.
3. Write that file to the microSD card with **Raspberry Pi Imager**: in the **OS** list take the entry for your own
   image file at the end of the list, select the file, select the card, **Next**, **Write**, **Finish**. If the
   Imager offers to apply its own settings (user name, Wi-Fi), decline: this image does not use them.

Limits of the Wi-Fi preset (from the script):

- The profile is written for WPA2 with a password (`key-mgmt=wpa-psk`). A network that accepts only WPA3, a hidden
  network or a network with a login page does not work.
- Home Assistant OS imports the profile at the first start and then deletes it from the card. To change the Wi-Fi
  later use **Settings > System > Network** in Home Assistant, or write the card again.

**Part B - boot**

1. Card in, compute module fitted, speaker plugged in, nothing in the USB-A sockets.
2. Plug in the 30 W charger.
3. Watch the LEDs:

| LED | What it does | Meaning |
|---|---|---|
| D6 green | on at once | 5 V |
| D10 green (ACT) | flickers irregularly, with pauses | the system reads from the card. This is the sign that the compute module runs |
| D10 green | the same pattern again and again: a number of flashes, two seconds pause | start-up failed, see the table below |
| D7 green, D8 blue (bare side) | stay off | they are only used once the VoxHub Assistant app runs |
| D9 red (bare side) | on only if the slider is in the mute position | hard-wired |

4. Wait, and do not unplug the charger during the first start. Home Assistant's own documentation says that on a
   Raspberry Pi 4 its page is available within a minute of the start; `os/README.md` reckons with about five
   minutes for the first start. Over Wi-Fi give it ten minutes (estimate) before you look for a fault.
5. On a PC or phone in the same Wi-Fi open `http://homeassistant.local:8123`. If the name is not found, open the
   device list of your router, look for the name `homeassistant` and open `http://<its address>:8123`.
6. Home Assistant shows **Welcome!** Select **Create my smart home** and follow the screens. While Home Assistant
   still downloads its own software the page shows a waiting screen; how long that takes depends on your internet
   line.
7. Install the terminal for the following tests ("apps" were called "add-ons" in older versions of Home
   Assistant): **Settings > Apps > Install app**, search for **Advanced SSH & Web Terminal**, **Install**. On its
   **Configuration** tab enter a `password` in the `ssh` block and save. On its **Info** tab switch
   **Protection mode** off, select **Start**, then **Open Web UI**. A terminal opens in the browser. All commands
   of tests 9 to 12 are typed there.

   Protection mode has to be off because the tests and the flashing script use the `docker` command. You can
   switch it on again after test 12.

Repeating flash patterns of D10 (Raspberry Pi documentation, read 2026-11-12; long flashes come first):

| Long | Short | Meaning | Most likely cause here |
|---|---|---|---|
| 0 | 4 | `start*.elf` not found | card empty, not written completely, or not fully inserted |
| 0 | 7 | kernel image not found | image damaged: write the card again |
| 0 | 3 | generic failure to boot | write the card again; try another card |
| 2 | 1 to 3 | partition cannot be read | card faulty or badly written |
| 4 | 6 or 7 | power failure | 5 V rail collapses: repeat test 3 with the module fitted |

| Expected | If not |
|---|---|
| D10 flickers irregularly; the page `homeassistant.local:8123` appears within ten minutes | **D10 never lights:** (a) the compute module is not seated - unplug, check 3.5 step 9; (b) no card or card not clicked in; (c) the module has no 5 V - measure +5V at L1. **D10 repeats a pattern:** see the table. **D10 flickers normally but the device never shows up in the router:** (a) Wi-Fi name or password mistyped - the name is case sensitive; (b) the network is WPA3-only or hidden; (c) the board is too far from the access point. Make the image again and write the card again. **The device is in the router list but the page does not open:** use `http://<address>:8123`, not `https`, and wait five more minutes. |

### 3.7 Test 7 - 3.3 V rail

The 3.3 V rail is produced by the compute module and feeds the USB hub, the card, the radio and the microphones.

This is the one live measurement on the test pads. **The pad `5V` is 1.7 mm to the right of the pad `3V3`. A probe
tip that touches both pads at once puts 5 V on the 3.3 V parts and can damage them.** Rest your hand on the desk,
come from the left, from the side of the label `3V3`, and touch only that pad.

1. The board is running (D6 on).
2. Multimeter on DC voltage, 20 V range. Put the black probe into the left, square hole of J5.
3. Touch the pad `3V3` with the red probe.

Check without a multimeter: push the mute slider to the other position and look at the bare side. In one of the
two positions the red LED D9 lights. It is fed from the 3.3 V rail, so a lit D9 proves that the rail exists.

| Expected | If not |
|---|---|
| 3.30 V, allowed 3.22 to 3.38 V (compute module data sheet: 3.3 V plus or minus 2.5 %) | **0 V:** the red probe is on the pad `GND` (the pad behind the `5V` pad), or the module is not seated. **About 5 V:** the red probe is on the pad `5V`; move it one pad to the left. **Below 3.2 V:** the rail is overloaded - unplug everything from the USB-A sockets and measure again; if it stays low, a part on the 3.3 V rail is faulty. |

### 3.8 Test 8 - both USB-A ports

1. Plug the USB memory stick into the upper USB-A socket.
2. In Home Assistant open **Settings > System > Hardware**, there **System hardware** (in the menu with the three
   dots, top right), and type `sda` into **Search hardware**. An entry with **Device path** `/dev/sda` and
   **Subsystem** `block` appears. The same from the terminal: `ha hardware info | grep sda` prints lines.
3. Pull the stick out. The entry disappears (close and reopen the list).
4. Plug the stick into the lower socket and repeat step 2.

Each port is limited to about 1.3 A by its own switch (U5, U6).

| Expected | If not |
|---|---|
| The stick appears on both sockets within a few seconds | **Neither socket works:** (a) the image was not made with `os/build-image.sh` - the line `otg_mode=1` is missing and the USB host of the compute module stays off; (b) the hub chip U4 or its 24 MHz crystal does not run - report the board. **One socket works, the other does not:** with the stick plugged in measure the two polymer capacitors, red probe on the bar end of C38 and of C41, black probe on the USB-A shell: both must read 5 V (4.75 to 5.25 V). 0 V on one: its port switch U5 or U6 is off or faulty. 5 V on both: a data pin of the USB-A socket is not soldered (the socket is hand-soldered at JLCPCB) or the protection part U7 / U8 is faulty. **The stick is found only after wiggling:** a solder joint of the USB-A socket. |

### 3.9 Test 9 - microphones

The two microphones are MK1 (front left corner of the board, left channel) and MK2 (rear right corner, right
channel). Their sound holes are on the bare side. The board stands on the mute slider, so there is a gap of a few
millimetres under it and sound still reaches the holes.

All commands are typed into the web terminal of test 6, step 7.

1. Make sure the microphones are not muted: the red LED D9 on the bare side is **dark**.
2. Is the sound card there?

   ```
   ha hardware audio
   ```

   Expected: a card named `snd_rpi_googlevoicehat_soundcar` (short name `sndrpigooglevoi`). It is created by the
   line `dtoverlay=googlevoicehat-soundcard` and serves both the microphones and the speaker.
3. Read the names under which Home Assistant's sound server knows the microphones and the speaker and keep them in
   two variables:

   ```
   SRC=$(docker exec hassio_audio pactl list short sources | grep soc_sound | grep -v monitor | cut -f2)
   SNK=$(docker exec hassio_audio pactl list short sinks | grep soc_sound | cut -f2)
   echo "microphones: $SRC"
   echo "speaker:     $SNK"
   ```

   Both lines must end with a name that contains `soc_sound` (expected: `alsa_input.platform-soc_sound.stereo-fallback`
   and `alsa_output.platform-soc_sound.stereo-fallback`). The variables are lost when you close the terminal; repeat
   this step then.
4. Record eight seconds. Start the command, speak loudly for four seconds over the front left corner of the board,
   then for four seconds over the rear right corner:

   ```
   docker exec hassio_audio timeout 8 parecord --device="$SRC" --format=s32le --rate=48000 --channels=2 --file-format=wav /tmp/mic.wav
   docker exec hassio_audio ls -l /tmp/mic.wav
   ```

   The file is about 3,072,000 bytes long (8 s x 48,000 samples x 8 bytes).
5. Listen to the left channel (MK1) through the speaker:

   ```
   docker exec hassio_audio paplay --device="$SNK" --volume=262144 /tmp/mic.wav
   ```

6. Listen to the right channel (MK2). The amplifier plays only the left channel, so the two channels are swapped
   for this:

   ```
   docker exec hassio_audio paplay --device="$SNK" --volume=262144 --channel-map=front-right,front-left /tmp/mic.wav
   ```

`--volume=262144` plays the recording 64 times louder than recorded (65536 would be unchanged). The microphones are
built for very loud sound, so normal speech is recorded at a low level; this is not a fault. If the playback is
too quiet use `--volume=524288`, if it is distorted use `--volume=131072`. These three values are starting values,
not measured ones.

| Expected | If not |
|---|---|
| You hear your voice in step 5 and in step 6. Each microphone hears both halves of the recording; the half spoken next to it is the louder one. Some hiss is normal | **Step 2 shows no such card or `$SRC` is empty:** the VoxHub block is missing in `config.txt` - the card was not made with `os/build-image.sh`. **Silence in steps 5 and 6:** (a) do test 10 first to prove the speaker; (b) the microphones are muted - D9 is lit; (c) the converter chip U9 (a very small chip at (40.0 / 61.0), between the radio module and the compute module) is not soldered correctly - report the board. **One channel has a voice, the other is silent or only crackles:** that microphone (MK1 or MK2) is defective or was washed - report the board. |

### 3.10 Test 10 - speaker

1. Repeat step 3 of test 9 if the terminal was closed.
2. Play the test file that is part of the sound server's container:

   ```
   docker exec hassio_audio paplay --device="$SNK" /usr/share/sounds/alsa/Front_Center.wav
   ```

The amplifier (U10, MAX98357A) has no volume control. Loudness is set in software only.

| Expected | If not |
|---|---|
| A voice says "Front Center", loud and clear | **Silence:** (a) the speaker plug is not fully in J7; (b) `$SNK` is empty or names another output - run `docker exec hassio_audio pactl list short sinks` and look for the line with `soc_sound`; (c) the amplifier U10 or its enable line (GPIO16) - report the board. **Rattling or distortion:** the speaker lies on its sound opening or against something; if it stays, play with `--volume=32768`. **Error "No such file":** the container of this Home Assistant version has no test sounds; use step 5 of test 9 as the speaker test. |

### 3.11 Test 11 - mute switch

What the switch does electrically (`hardware/gen/design.py`): SW1 is a slide switch with two separate contact
sets. One set sits in the **data line** from the microphone converter U9 to the compute module (GPIO20). In the mute
position this line is opened and the input of the compute module is tied to ground, so the compute module receives
only zeros. The other set connects 3.3 V to the red LED D9 and to GPIO27, so software can see that mute is on. The
microphone clock and the microphone supply stay on. Software cannot undo the mute.

1. Push the slider to its other position. Expected direction (from the drawing of the switch): muted = slider
   towards the right board edge when you look at the component side; in the finished device, seen from the front,
   that is to the left, away from the speaker grille. What counts is the LED: **D9 lit = muted.**
2. With D9 lit, repeat steps 4 and 5 of test 9 while you speak. The playback must contain no voice at all.
3. Push the slider back. D9 goes dark. Repeat steps 4 and 5 of test 9: the voice is back.
4. The two status LEDs next to D9 (optional). This lights D7 (green) and D8 (blue) for five seconds:

   ```
   docker run --rm --privileged debian:bookworm-slim sh -c 'echo 1 > /sys/class/leds/voxhub-green/brightness; echo 1 > /sys/class/leds/voxhub-blue/brightness; sleep 5; echo 0 > /sys/class/leds/voxhub-green/brightness; echo 0 > /sys/class/leds/voxhub-blue/brightness'
   ```

   It is one line. The first run downloads a small Debian system image; the flashing script of test 12 uses the
   same image.

   To see the bare side, slide a small mirror under the front edge of the board, or lift the front edge a little
   by its two corners and look underneath.

| Expected | If not |
|---|---|
| D9 lit in exactly one slider position; no voice in the recording while D9 is lit; voice back when D9 is dark | **D9 never lights:** (a) no 3.3 V - test 7; (b) the switch or D9 is not soldered - report. **D9 lit but the voice is still recorded:** the contact set in the data line does not open. This is the privacy function of the device: do not use the board, report it. **D9 dark but every recording is silent:** the same contact set does not close, or U9 - report. **Step 4 prints "No such file or directory":** the LED lines are missing in `config.txt` (card not made with `os/build-image.sh`). |

### 3.12 Test 12 - write the Zigbee firmware to the radio

The radio module (RF-star RF-BM-2652P2 with the TI CC2652P) is delivered without the firmware this project uses.
`tools/flash_zigbee.sh` writes the Zigbee coordinator firmware (Koenkk Z-Stack 20250321) from the compute module
(on the hub; the satellite of chapter 7 gets the router firmware with `--role satellite`, section 7.6):
it downloads the firmware and the flashing tool with fixed checksums, puts the radio into its built-in serial boot
loader through GPIO25 and GPIO24, writes, verifies, restarts the radio and asks it which firmware answers. If the
boot loader does not answer, it continues on its own with a second method (JTAG through four other GPIO lines).
The script has been run against a simulated radio only, never on a real board.

Three things to know before you start:

- **Every write erases the whole chip**, including the Zigbee network that a coordinator has stored. On a new board
  there is nothing to lose. If you ever write the firmware again on a radio that already runs your network, all
  devices have to be paired again unless you restore a backup of ZHA or Zigbee2MQTT.
- If the script is stopped or fails after it has touched the radio, it restarts the radio by itself and says so:
  `The radio was restarted (reset pulse on GPIO24) so that it is not left in reset or in its bootloader.`
- `--probe-only` only asks the radio which firmware answers. It downloads no firmware and drives no GPIO line.

**Path 1 (use this one): from Home Assistant OS**

1. No Zigbee integration may use the radio yet. On a fresh installation none does.
2. In the web terminal (protection mode off, see test 6 step 7) fetch the script into a file and check that it
   arrived complete:

   ```
   curl -fLo flash_zigbee.sh https://raw.githubusercontent.com/geilevideossos-gamedev/fable-sbc-test/claude/gallant-hamilton-kojnjj/tools/flash_zigbee.sh
   bash flash_zigbee.sh --help
   ```

   The second command must print the help text shown further down and nothing else. (The address is that of
   the branch with the two-device version; once it has been merged, replace `claude/gallant-hamilton-kojnjj` in
   the address by `main`.) The script must be a file; piping the
   download straight into `bash` does not work, because the script copies itself into a container.
3. Rehearsal without touching the radio:

   ```
   bash flash_zigbee.sh --dry-run
   ```

   The script fetches a small Debian system (`debian:bookworm-slim`), runs itself inside it, installs its tools,
   downloads and checks the flashing tool and the firmware and prints every hardware step as a line that contains
   `[dry-run] would`.
   It must end with `Dry run finished. No GPIO was driven and nothing was written to the radio.` If it does, the
   terminal app, `docker` and the internet connection are in order.
4. Write the firmware. On the hub run the script with the role `hub` (it is also the default without options):

   ```
   bash flash_zigbee.sh --role hub
   ```

5. Wait for the line that starts with `SUCCESS`. The research estimates one to two minutes.

Expected output of step 4 on Home Assistant OS, put together from the messages in the script (not captured on a
real board; `...` stands for the output of the package installation and of the flashing tool):

```
Role: hub (option) - firmware: Zigbee coordinator (Z-Stack 20250321)

==> Starting a temporary debian:bookworm-slim container that has access to the serial port and the GPIOs
Running inside the temporary container.

==> Checking the tools this script needs
Installing: python3 python3-serial python3-intelhex gpiod curl ca-certificates
...
python3, pyserial and intelhex are present.

==> Downloading the flashing tool and the firmware (Zigbee coordinator (Z-Stack 20250321))
...
CC1352P2_CC2652P_launchpad_coordinator_20250321.hex SHA256 matches: c2d3a05fe7146b6d57424571629f6efd9166395202babb86639849e9af31a1ff

==> Checking that the firmware keeps the bootloader backdoor on DIO15
  image ends at 0x58000 (352 KiB flash, CC2652P / CC1352P layout)
  CCFG BL_CONFIG at 0x57FD8: bytes C5 0F FE C5
    ROM bootloader enable 0xC5, backdoor enable 0xC5, pin DIO15, active low
  OK: this image keeps the serial bootloader reachable through DIO15 (GPIO25).

==> Looking for the radio's serial port
Using /dev/ttyAMA4

==> Selecting how to drive GPIO24 (reset) and GPIO25 (bootloader strap)
...

==> Asking the radio which firmware it runs now
The radio does not answer as Z-Stack (115200 baud) or as OpenThread RCP (460800 baud).

==> Writing the firmware through the ROM serial bootloader
Resetting the radio with the bootloader strap held low (GPIO25 low, GPIO24 high, then released).
Running: python3 cc2538_bsl.py -p /dev/ttyAMA4 -b 500000 -e -w -v CC1352P2_CC2652P_launchpad_coordinator_20250321.hex
...
    Verified (match: 0x...)
The bootloader confirmed the checksum of the written image.

==> Starting the new firmware and checking that it answers
Restarting the radio normally (strap released, reset pulse on GPIO24).
The radio answers as a Zigbee coordinator (Z-Stack ZNP, 115200 baud): revision=20250321 ...

==> Done
SUCCESS: the radio runs the Zigbee coordinator firmware 20250321.

Home Assistant ZHA:
  Settings -> Devices & services -> Add integration -> Zigbee Home Automation
  Radio type: ZNP (Texas Instruments Z-Stack)   Serial device path: /dev/ttyAMA4
  Port speed: 115200                            Data flow control: none

Zigbee2MQTT (configuration.yaml):
  serial:
    port: /dev/ttyAMA4
    adapter: zstack
```

Three places can look different on your board without being a fault:

- Under the heading `Asking the radio which firmware it runs now` the script names a firmware if the module was
  delivered with one.
- If the boot loader does not answer, the lines `The bootloader did not answer at 500000 baud.` and
  `The bootloader did not answer at 115200 baud.` are followed by `The serial bootloader is not reachable.` and by
  the section `Writing the firmware through JTAG (OpenOCD bit-bang on GPIO22, 23, 7 and 17)`, which must end with
  `OpenOCD wrote and verified the image.`
- If the radio already runs this firmware, the script writes nothing and says
  `The wanted firmware is already installed. Use --force to write it again.` Go on with test 13.

The options of the script, as printed by `bash tools/flash_zigbee.sh --help` on 2026-11-12 (two-device version):

```
flash_zigbee.sh - write firmware to the VoxHub radio module (RF-BM-2652P2, TI CC2652P)

Usage:
  sudo bash flash_zigbee.sh [options]

Role of this board:
  --role hub          Zigbee coordinator: Z-Stack coordinator 20250321 for ZHA / Zigbee2MQTT
  --role satellite    Zigbee router: Z-Stack router 20250403, extends the hub's Zigbee network
                      Without --role: satellite on the VoxHub satellite image
                      (/etc/voxhub/satellite.env exists), hub everywhere else.

Firmware:
  --zigbee            the Zigbee firmware of the role (default)
  --thread            OpenThread RCP 2025.3.1 for the OpenThread Border Router (hub only)

Options:
  --method METHOD     auto (default): serial bootloader first, JTAG if it does not answer
                      serial: serial bootloader only
                      jtag: OpenOCD bit-bang JTAG only (erases the whole chip first)
  --port PATH         serial port of the radio (default /dev/ttyAMA4)
  --force             write even if the wanted firmware is already installed;
                      also needed for --role satellite on Home Assistant OS
                      Every write erases the whole chip, including a coordinator's stored
                      Zigbee network: the devices must be paired again unless a ZHA or
                      Zigbee2MQTT backup is restored.
  --probe-only        only report which firmware answers on the serial port
  --rejoin            satellite only, writes nothing: make the router leave its network
                      and search for a network again (GPIO25 low for 0.5 s, the same as
                      pressing the button of a launchpad)
  --container         run inside a Debian container even if this system has apt-get
  --dry-run           show every step, download and check the files, touch no hardware
  --help              this text

Board wiring used: UART4 on GPIO8/9, GPIO24 high = radio in reset, GPIO25 low at
reset = ROM bootloader, JTAG TMS GPIO22, TCK GPIO23, TDO GPIO17, TDI GPIO7.
```

What the script really prints up to the point where it would touch the hardware was captured with
`bash tools/flash_zigbee.sh --role hub --dry-run` on a PC on 2026-11-12 (two-device version, no board connected; the
downloads and all checksums were correct on that day). On Home Assistant OS the first lines are those of the container
(`Starting a temporary ... container`, `Running inside the temporary container.`, `Installing: ...`) instead of
`Running directly on this system`:

```
Role: hub (option) - firmware: Zigbee coordinator (Z-Stack 20250321)
Running directly on this system (apt-get is available).

==> Checking the tools this script needs
  [dry-run] would install with apt-get if missing: python3 python3-serial python3-intelhex gpiod curl ca-certificates

==> Downloading the flashing tool and the firmware (Zigbee coordinator (Z-Stack 20250321))
cc2538-bsl (TI serial bootloader tool, pinned commit 28cce97):
  from https://raw.githubusercontent.com/JelmerT/cc2538-bsl/28cce9749bfb73c50363ded01bd8001b1639d9fb/cc2538_bsl/cc2538_bsl.py
  SHA256 matches: 392cf987b8f741401547dc0faa8f43af085b3e4378facfafaecdfd19ea6503f3
CC1352P2_CC2652P_launchpad_coordinator_20250321.zip:
  from https://raw.githubusercontent.com/Koenkk/Z-Stack-firmware/5e4db67e550d41ea6dc6cd86ceeb04d82ffe1bfb/coordinator/Z-Stack_3.x.0/bin/CC1352P2_CC2652P_launchpad_coordinator_20250321.zip
  SHA256 matches: e9e256e3615937267ae3d8c60641bb7deca904a506711afa7c6247df2cb84883
CC1352P2_CC2652P_launchpad_coordinator_20250321.hex SHA256 matches: c2d3a05fe7146b6d57424571629f6efd9166395202babb86639849e9af31a1ff

==> Checking that the firmware keeps the bootloader backdoor on DIO15
  image ends at 0x58000 (352 KiB flash, CC2652P / CC1352P layout)
  CCFG BL_CONFIG at 0x57FD8: bytes C5 0F FE C5
    ROM bootloader enable 0xC5, backdoor enable 0xC5, pin DIO15, active low
  OK: this image keeps the serial bootloader reachable through DIO15 (GPIO25).

==> Looking for the radio's serial port
Using /dev/ttyAMA4

==> Selecting how to drive GPIO24 (reset) and GPIO25 (bootloader strap)
GPIO method: dry-run 

==> Asking the radio which firmware it runs now
  [dry-run] would ask the radio on /dev/ttyAMA4 which firmware it runs (looking for: any)

==> Writing the firmware through the ROM serial bootloader
Resetting the radio with the bootloader strap held low (GPIO25 low, GPIO24 high, then released).
  [dry-run] would drive GPIO25 to 0
  [dry-run] would drive GPIO24 to 1
  [dry-run] would release GPIO24 (input, pull-down)
  [dry-run] would release GPIO25 (input, pull-up)
Running: python3 cc2538_bsl.py -p /dev/ttyAMA4 -b 500000 -e -w -v CC1352P2_CC2652P_launchpad_coordinator_20250321.hex
  [dry-run] nothing is written

==> Starting the new firmware and checking that it answers
Restarting the radio normally (strap released, reset pulse on GPIO24).
  [dry-run] would release GPIO25 (input, pull-up)
  [dry-run] would drive GPIO24 to 1
  [dry-run] would release GPIO24 (input, pull-down)
  [dry-run] would ask the radio on /dev/ttyAMA4 which firmware it runs (looking for: znp)

==> Done
Dry run finished. No GPIO was driven and nothing was written to the radio.
```

**Path 2 (runner-up): from Raspberry Pi OS**

Use this only if path 1 fails for a reason that has to do with Home Assistant OS (no `docker`, no `/dev/ttyAMA4`).
It needs a second microSD card, so that the Home Assistant card stays as it is.

1. Write **Raspberry Pi OS Lite (64-bit)** to the second card with Raspberry Pi Imager. In the Imager's settings
   dialog enter a user name and password, your Wi-Fi name and password, and switch SSH on. There is no other way
   to reach the board.
2. Before you take the card out of the PC, open the file `config.txt` on its small first partition with a text
   editor and add this line at the end: `dtoverlay=uart4`
3. Shut Home Assistant down (`ha host shutdown` in the web terminal), wait 30 seconds, unplug the charger, swap the
   cards, plug the charger in.
4. Log in from the PC with `ssh <user>@<address of the board>` and run:

   ```
   curl -fLo flash_zigbee.sh https://raw.githubusercontent.com/geilevideossos-gamedev/fable-sbc-test/claude/gallant-hamilton-kojnjj/tools/flash_zigbee.sh
   sudo bash flash_zigbee.sh
   ```

5. After `SUCCESS` run `sudo poweroff`, wait 30 seconds, unplug, put the Home Assistant card back.

On Raspberry Pi OS the output starts with `Running directly on this system (apt-get is available).` instead of the
container lines. The USB-A sockets do not work under Raspberry Pi OS with this card; that is expected (the line
`otg_mode=1` is not set there).

**If the script does not end with `SUCCESS`**

Nothing is written to the radio before the section `Writing the firmware ...` starts. Every message below is quoted
from the script.

| The script prints | What it means | Do this |
|---|---|---|
| `This looks like Home Assistant OS, but the docker command does not work here.` | protection mode of the terminal app is on | switch **Protection mode** off on the **Info** tab of the terminal app, restart the app, run the script again |
| `ERROR: The temporary container could not be started (docker exit status ...).` | the Debian image could not be fetched from Docker Hub or started | check the internet connection of the board and run the script again; nothing was written |
| `The serial port /dev/ttyAMA4 is in use by:` | an integration already uses the radio | disable Zigbee Home Automation or stop Zigbee2MQTT, run the script, enable it again |
| `The serial port /dev/ttyAMA4 does not exist.` | the line `dtoverlay=uart4` is missing | the card was not made with `os/build-image.sh` from the A2 branch: make it again (3.6 part A) |
| `Could not download ... with the expected checksum. Nothing was written to the radio.` | no internet access, or a file was changed at its source | try again later; nothing has happened to the radio |
| `Could not drive GPIO24.` or `Could not drive GPIO25. Another program or driver is using this line.` | helper programs of an earlier run that was killed still hold the line | on Home Assistant OS restart the board with `ha host reboot` and run the script again; on Raspberry Pi OS run `sudo pkill gpioset` first |
| `The serial bootloader is not reachable.` followed by `Falling back to JTAG.` | the module was delivered with a firmware that keeps its boot loader closed | nothing to do: the script continues with the second method by itself |
| `cc2538-bsl could not write the firmware through the serial bootloader (see the messages above). Falling back to JTAG.` | the boot loader answered but the write failed | nothing to do at once: the script continues with JTAG. If that fails too, copy the messages above this line into your report |
| `Neither the serial bootloader nor JTAG could program the radio.` | the radio reacts on neither path | (a) shut down, unplug, plug in, run the script once more; (b) the module or one of its control lines is not soldered - report the board. A locked chip needs a TI XDS110 probe on the pads J8, which is outside this guide |
| `The firmware was written and verified, but it does not answer on /dev/ttyAMA4.` followed by `The UART itself works ...` | written through the serial boot loader, but the new firmware is silent | make sure no integration uses the port, wait a minute, run `bash flash_zigbee.sh --probe-only`; if it still does not answer, report the board |
| `The firmware was written and verified, but it does not answer on /dev/ttyAMA4.` followed by `Check the UART wiring ...` | written through JTAG; the serial lines between compute module and radio do not work | report the board |
| `WARNING: GPIO25 reads low although it is released. The radio will stay in its bootloader.` and `Check the 2.2k pull-up R45 on the ZB_BOOT net.` | the pull-up resistor R45 of the boot strap is missing or the line is shorted | report the board |
| `The radio was restarted (reset pulse on GPIO24) so that it is not left in reset or in its bootloader.` | the run was stopped or failed after it had touched the radio; the radio runs again with whatever it contains | read the `ERROR` line above it and act on that |
| `The radio could not be restarted. If it does not answer afterwards, switch the board off and on again.` | the same, but the restart did not work | `ha host shutdown`, wait 30 seconds, unplug the charger, plug it in again |

### 3.13 Test 13 - add the radio to Home Assistant (ZHA) and pair one device

The labels below are those of the Home Assistant source on 2026-11-12. The installed release can differ slightly;
the documentation of that day and the output of the script still use the older names given in brackets.

1. **Settings > Devices & services > Add integration**, choose **Zigbee Home Automation**.
2. Dialog **Select a serial port**: choose `/dev/ttyAMA4` from the list. If it is not in the list choose
   **Enter manually** and type `/dev/ttyAMA4`. **Submit**.
3. Home Assistant now tries to recognise the radio by itself. If it succeeds, continue with step 6.
4. Only if it asks - dialog **Select an adapter type**, field **Adapter type** (older name: Radio type): choose
   `ZNP = Texas Instruments Z-Stack ZNP protocol: CC253x, CC26x2, CC13x2`. **Submit**.
5. Only if it asks - dialog **Serial port settings**:

   | Field (older name) | Value |
   |---|---|
   | **Serial device path** | `/dev/ttyAMA4` |
   | **Serial port speed** (Port speed) | `115200` |
   | **Serial port flow control** (Data flow control) | `none` |

   **Submit**.
6. Dialog **Set up Zigbee**: choose **Set up automatically (recommended)**. Home Assistant forms a new network;
   the dialog says that this can take a minute.
7. Pair one device: **Settings > Connectivity > Zigbee**, **Add device** (bottom right). Put the Zigbee device into
   pairing mode as its manual says (usually a factory reset). It appears in the list within some seconds; give it a
   name.
8. Switch the device from Home Assistant, or watch its sensor value change.

If you prefer Zigbee2MQTT to ZHA (runner-up; use only one of the two), its serial settings are:
`port: /dev/ttyAMA4` and `adapter: zstack`.

| Expected | If not |
|---|---|
| The integration is created without an error, the device joins and can be operated | **An error message instead of the next dialog, or the radio is not recognised:** (a) the firmware is not on the radio - run `bash flash_zigbee.sh --probe-only`; (b) a wrong port was chosen - it must be `/dev/ttyAMA4`, not `/dev/ttyAMA0` or `/dev/ttyS0`; (c) speed or flow control were changed - 115200 and none. **The device does not join:** (a) it is still bound to its old network - factory reset it; (b) it is too close or too far - try at 1 to 3 m; (c) the bare board lies on a metal desk or the antenna end of the radio module (front edge, left) is covered. |

### 3.14 Results table

Copy this table, one per board, and fill it in.

Board number: ______  Date: ______

| # | Test | Expected | Measured / seen | OK |
|---|---|---|---|---|
| 1 | Visual inspection | all eight points true | | [ ] |
| 2a | VBUS to GND, no power | no beep, above 1 kOhm | | [ ] |
| 2b | +5V to GND, no power | climbs above 1 kOhm | | [ ] |
| 2c | +3V3 to GND, no power | above 100 Ohm | | [ ] |
| 2d | VBUS to +5V, no power | no beep, above 1 kOhm | | [ ] |
| 3a | 30 W charger: VBUS at D1 | 14.25 to 15.75 V | | [ ] |
| 3b | 30 W charger: VBUS_SW at C8 / C9 | VBUS minus at most 0.1 V | | [ ] |
| 3c | 30 W charger: +5V at L1 / C14 | 4.86 to 5.23 V | | [ ] |
| 3d | 30 W charger: LEDs | D6 on, D4 off | | [ ] |
| 4a | 20 W charger: VBUS / +5V | 8.55 to 9.45 V / 4.86 to 5.23 V | | [ ] |
| 4b | 65 W charger: VBUS / +5V | 19.0 to 21.0 V / 4.86 to 5.23 V | | [ ] |
| 4c | 5 V supply | VBUS about 5 V, +5V 0 V, D4 on, D6 off | | [ ] |
| 5 | Heat sink, compute module, card, speaker fitted | module flat, 4 screws | | [ ] |
| 6a | First boot: D10 | flickers irregularly | | [ ] |
| 6b | First boot: web page | reachable on port 8123 | | [ ] |
| 7 | +3V3 at the test pad `3V3` | 3.22 to 3.38 V | | [ ] |
| 8a | USB stick, upper socket | `/dev/sda` appears | | [ ] |
| 8b | USB stick, lower socket | `/dev/sda` appears | | [ ] |
| 9a | Sound card | `snd_rpi_googlevoicehat_soundcar` listed | | [ ] |
| 9b | Microphone MK1 (left channel) | voice audible | | [ ] |
| 9c | Microphone MK2 (right channel) | voice audible | | [ ] |
| 10 | Speaker | "Front Center" loud and clear | | [ ] |
| 11a | Mute: D9 | lit in one position only | | [ ] |
| 11b | Mute: recording while D9 is lit | no voice | | [ ] |
| 11c | Status LEDs D7 / D8 (optional) | both light for 5 s | | [ ] |
| 12 | Zigbee firmware | line `SUCCESS: ...20250321.` | | [ ] |
| 13a | ZHA | integration created | | [ ] |
| 13b | One Zigbee device | joins and can be operated | | [ ] |

When every line is ticked, shut the system down before you unplug it: type `ha host shutdown` in the web terminal,
wait 30 seconds, then pull the charger. Continue with chapter 4.

## 4. Mechanical assembly

Do this only with a board that has passed chapter 3. The compute module with its heat sink and the microSD card
stay on the board.

Four warnings that matter:

- **Never plug in or pull off the compute module under power.** The charger is unplugged during the whole chapter.
- **Do not overtighten screws in plastic.** The screws cut their own thread into the printed holes. Turn slowly with
  light pressure and stop the moment the head touches. A screw that suddenly turns easily has stripped the thread.
- **Do not push on the microphones** and do not cover their holes.
- **Do not wash the board**, not even to remove fingerprints.

All screws at a glance:

| Step | Joint | Screw | Qty | Goes into | Stop when |
|---|---|---|---|---|---|
| 3.5 (already done) | compute module to the four spacers of the board | M2.5 x 5 | 4 | metal thread | head seated; limit 0.35 N m |
| 4.4 | board to the four short bosses of the shell | M2.5 x 5 | 4 | printed 2.1 mm hole, 3.4 mm of thread in plastic | head touches the board |
| 4.7 | base to the four corner posts of the shell | M2.5 x 8 | 4 | printed 2.1 mm hole, 7 mm of thread in plastic | head seated in its recess |

**An M2.5 x 8 screw must never go into a board boss.** The hole there is 5.2 mm deep and the board is 1.6 mm thick;
an 8 mm screw comes out through the top cover.

### 4.1 Prepare

1. Shut the system down if it still runs (`ha host shutdown`, wait 30 seconds) and unplug the charger.
2. Lay a soft cloth on the desk. Put the shell on it with the top face down and the open side up, the rear wall
   (the wall with the three windows) away from you. The wide empty bay for the speaker is now on the **left**, the
   four short bosses for the board are on the right. The picture
   [enclosure_open_bottom.png](../enclosure/renders/enclosure_open_bottom.png) shows this view with everything in place.
3. The speaker may stay plugged into J7. If you want to unplug it, grip the white plug itself, never the wires.

### 4.2 Foam pad on the base

1. Cut a piece of 40 x 18 mm from the 3 mm self-adhesive cellular rubber.
2. Peel off the backing and stick the piece onto the pedestal of the base (the raised block, 40 x 18 mm, 5.1 mm
   high). It covers the pedestal completely.
3. Put the base aside.

In the closed case the top of the pedestal is 2.0 mm away from the back of the speaker (1.5 to 2.5 mm, because the
height of the speaker is 16.5 mm plus or minus 0.5 mm). The 3 mm pad is therefore squeezed by about a third and
holds the speaker against the top cover. If the base cannot be pressed flat onto its posts with two fingers in
step 4.7, the pad is too stiff: cut it down to 20 x 18 mm and stick it in the middle of the pedestal.

### 4.3 Speaker into its frame

1. On the inside of the top cover, in the left bay, is a low rectangular frame (opening 71.3 x 31.9 mm, 3 mm high)
   around the oblong grille.
2. Look at the speaker: the lead leaves the box in the middle of one of its two short end faces. Turn the speaker
   so that **this end points to the rear wall**, the wall with the three windows, away from you.
3. Lay the speaker into the frame with its **sound opening down, towards the grille**. The closed back of the
   speaker box faces you. The four holes in the corners of the speaker are not used.
4. The speaker lies flat on the top cover and has about half a millimetre of play on every side. The sound opening
   is not in the middle of the speaker (about 3 mm off centre); the grille is long enough for that.

### 4.4 Board onto the bosses - 4 x M2.5 x 5

In the finished device the board hangs with the component side down. Because the shell lies upside down now, you
put the board in with the **component side up, towards you**; the bare side with the mute slider goes down, towards
the top cover.

1. Hold the board by its left and right edges, component side up, rear edge with the three sockets away from you.
2. Tilt it: rear edge down, front edge about 2 cm up. The board cannot be lowered straight in, because the USB-A
   socket overhangs the board edge by 2.5 mm.
3. Push the three sockets into their windows in the rear wall, the tall USB-A socket first.
4. Lower the front edge until the board lies on the four bosses. Do not press on the compute module to do so.
5. Check from above: each of the four corner holes of the board shows a boss hole in its middle.
6. Fasten the board with **4 x M2.5 x 5**. Start each screw straight by hand, then turn it slowly. The first turns
   are stiff because the thread is being cut. Stop when the head touches the board. The screw at the front right
   corner sits very close to the edge of the compute module; keep the screwdriver vertical.
7. Lift the shell and check from the outside: the mute slider stands in its slot in the oval dish and can be moved
   both ways; the USB-C and USB-A openings are centred in their windows.

No foam rings are fitted on the two microphone tubes in this build. The tubes end 0.2 mm above the board.

### 4.5 Speaker lead

The lead is about 50 cm long; the way from the speaker to J7 is much shorter. The rest has to be stored where it
cannot be pinched, where the foam pad does not press on it and where it is far from the antenna of the radio
module, which is at the front edge of the board. That place is the **rear half of the speaker bay**, the half
next to the USB sockets.

1. If the plug is not in J7: plug it in (white header, text `SPK`, at the left edge of the board). It fits one way
   and without force (check in 2.1).
   **Polarity does not matter:** there is only one speaker, and the amplifier drives both wires in opposite
   directions (a bridge output), so neither wire is ground. For the same reason never let a speaker wire touch
   ground or any metal part of the board.
2. The lead leaves the rear end face of the speaker in the narrow space in front of the rear wall. The corner post
   stands close to the corner of the speaker there, so do not squeeze the lead past the post. Lead it up and over
   the rear end of the speaker's back, within the first 10 mm (the foam pad begins 13 mm from this end), into the
   gap between the speaker and the **left** side wall.
3. Fold the surplus back and forth into a bundle about 30 mm long (about eleven layers). Leave about 12 cm free at
   the plug end. Hold the bundle together with a strip of adhesive tape or a cable tie.
4. Stand the bundle on edge in that gap, pushed against the **rear** corner post. The gap is about 7 mm wide. The
   bundle must not reach further forward than the middle of the speaker.
5. Lead the free end forward along the same gap and then across the back of the speaker **about 8 mm from the
   front end of the speaker box**, straight towards J7. The foam pad of the base ends 13 mm from that end, so the
   lead passes 5 mm in front of the pad. Do not lead it across the speaker anywhere further back: the pad would
   press on it.
6. Check: no wire lies on the end face of a corner post, on the rim of the shell, under the place of the foam pad
   (the middle 40 mm of the speaker's back), on the inductor or on the compute module, and no slack lies along
   the front wall.

### 4.6 Last look before closing

- Card clicked in; you can see its edge in the microSD window.
- Speaker plug fully in J7; the lead lies as described in 4.5.
- Heat sink firmly on the processor.
- Four screws in the compute module, four in the board.
- No loose screw, no cut-off plastic, no tool inside.

### 4.7 Base - 4 x M2.5 x 8

1. Hold the base with the pedestal and the foam pad down (into the shell). **The pedestal belongs over the
   speaker, on the left; the field of nine long vent slots belongs over the compute module, on the right.** The
   base also fits when it is turned by 180 degrees, but then nothing holds the speaker and the vents are in the
   wrong place.
2. Lower the base onto the four corner posts. It sinks into the shell until its outer face is level with the rim.
   The last millimetre needs light pressure because the foam pad is compressed.
3. Fasten it with **4 x M2.5 x 8**, crosswise. Stop when each head sits in its round recess. The heads stand about
   half a millimetre proud of the base; that is intended.

### 4.8 Feet

Stick one 8 x 3 mm foot into each of the four round recesses of the base (diameter 8.6 mm). The feet are needed:
they lift the screw heads off the table and let air reach the vents of the base.

### 4.9 Final check of the closed device

1. Turn the device over and plug in the 30 W charger. Seen from the front, the speaker grille is on the right and
   the sockets are at the back, from left to right as seen from behind: USB-C, double USB-A, microSD.
2. After the start, push the mute slider to its other position (expected: to the left). A red dot shines through
   the top cover near the front edge. Push the slider back; the dot goes out.
3. Repeat test 10 (speaker) and steps 4 to 6 of test 9 (microphones) from the web terminal. The voice must be at
   least as clear as on the desk.
4. Plug the USB stick into both USB-A sockets (test 8).
5. To take the card out: press it in by about 1 mm with a fingernail and let it come out.

The green and the blue status LED stay dark until the VoxHub Assistant app runs (`assistant/README.md`): green =
waiting for the wake word, blue = listening, blinking blue = thinking, green and blue = speaking.

## 5. Troubleshooting and electrical safety

### 5.1 Troubleshooting the finished device

| Symptom | Most likely causes | What to do |
|---|---|---|
| Nothing happens after plugging in | (a) the supply is not a USB PD charger or offers less than 2 A at 9 to 20 V; (b) cable with a USB-A plug; (c) cable not fully in | Lift the device and look through the four short vent slots of the base next to the speaker. A red glow: the supply is unsuitable - use the 30 W charger. A green glow: the board has power, go on with the next line. No glow: no power arrives |
| Green glow inside, but the device never appears in the network | (a) the compute module came loose; (b) the card was pushed out; (c) the Wi-Fi changed | Open the base, check module and card. For (c) make a new image (3.6 part A) |
| It worked on the desk but not in the case | (a) the speaker lead is pinched or pulled the plug out of J7; (b) the base is on turned by 180 degrees; (c) a board screw is missing and the board hangs on the sockets | Open the base and check 4.5 to 4.7 |
| Restarts when a USB device is plugged in or during loud playback | charger too weak (a 20 W charger is a test case only) | Use the 30 W charger |
| The red, green or blue dot cannot be seen through the cover | (a) dark filament; (b) printed with thicker layers, so the skin is thicker than 0.4 mm; (c) green and blue are off because no app drives them | (a), (b) reprint the shell in a light colour with 0.2 mm layers; (c) see 4.9 |
| Mute slider stiff or blocked | (a) strings in the slot; (b) the board does not sit on all four bosses | Clear the slot; loosen the four board screws, seat the board, tighten again |
| Voice recognition poor, microphones quiet in the case | (a) a microphone hole of the cover is closed by print residue; (b) the device stands with its top against something | Open the two 1.5 mm holes with a drill bit by hand **before** the board is in the shell; never poke into the hole with the board fitted |
| Speaker rattles | (a) foam pad missing or fallen off; (b) a wire touches the speaker box; (c) base turned by 180 degrees | Open the base and check 4.2, 4.5, 4.7 |
| No sound after assembly | (a) plug out of J7; (b) wire pinched and cut | Check the lead |
| A USB plug does not go in fully | (a) threads of plastic in the window; (b) the board is not pushed fully to the rear | Trim the window; loosen the board screws, push the board to the rear wall, tighten |
| A screw turns without getting tight | the thread in the plastic is stripped | In a board boss use an M2.5 x 6 screw (the longest that fits there); in a corner post an M2.5 x 10. If that does not hold, reprint the shell |
| Wi-Fi weak | the antenna of the compute module is at the side wall opposite the speaker; metal objects next to that wall shield it | Move the device or the metal object |
| Zigbee devices drop out | (a) the radio's antenna is at the front edge next to the speaker - a metal object close to it; (b) a 2.4 GHz Wi-Fi channel on top of the Zigbee channel | Keep the front edge free; see the Zigbee page of the Home Assistant documentation for the choice of channel |
| The case gets hot, the system gets slow | (a) feet missing or the device stands on a soft surface, so the base vents are closed; (b) the heat sink has come off | Hard surface, four feet; open and press the heat sink on again |
| After an update of Home Assistant OS the sound card, the USB sockets or the radio are gone | the VoxHub lines in `config.txt` were lost | They are designed to survive updates (os/README). If they are gone, write a new card and restore a backup |

### 5.2 Electrical safety

**Voltages.** The charger delivers 9, 12, 15 or 20 V on VBUS, depending on its size, with up to 3.25 A (65 W
charger). 20 V DC is not dangerous to touch. The dangers are different ones:

- A screwdriver, a probe tip or a screw that bridges VBUS to ground causes sparks and can burn a track or the tool.
- A bridge from VBUS to the 5 V or 3.3 V rail, even for an instant, destroys the compute module, the radio and the
  USB hub.

**Where the charger voltage is on the board** (component side):

| Net | Parts | Area |
|---|---|---|
| VBUS | USB-C socket J1, diode D1, capacitors C1 and C2, load switch Q1, PD controller U1 | rear left corner: x below 19, y 7 to 15 |
| VBUS_SW | load switch Q1, capacitors C8, C9, C10, regulator U2, PD controller U1 | x 4 to 23, y 14 to 24 |
| switching node, jumps between 0 V and the charger voltage 400,000 times per second | right terminal of the inductor L1, regulator U2 | x 9 to 12, y 28 to 37 |

Everything else on the board carries 5 V or 3.3 V. The three test pads carry 5 V, 3.3 V and ground; there is no
test pad with the charger voltage.

**Rules**

1. Unplug the charger before you touch the board with a tool, fit or remove the compute module, the card, the
   speaker or a screw. Wait until the green LED D6 is dark; the capacitors are then empty.
2. With power on, only the multimeter probes touch the board, one hand per probe, on the points named in chapter 3.
3. Never power the board while it lies on metal, on the anti-static film or bag it came in (that material
   conducts) or on a wet surface. Cardboard or wood is right.
4. At the very first power-up (test 3) watch the board for ten seconds from a distance of half a metre. A part
   mounted the wrong way round shows itself by heat, smell or a crack in this time. Unplug at once.
5. Use only undamaged chargers with a CE mark. The charger is the only part with mains voltage; never open it.
6. Do not feed power into the USB-A sockets (no powered hub that feeds back, no Y cable). They are outputs.
7. The two speaker wires are both live outputs of the amplifier. Never connect one of them to ground.
8. The heat sink and the area around the regulator can reach 60 to 80 C in operation. Let the device cool down
   before you open it.

## 6. What could not be verified

No hardware exists yet, so nothing in this guide has been tried on a real board. In detail:

**Not measured, taken from design files and data sheets**

- All voltages, resistances, LED states and times in chapter 3. The resistance values of test 2, the "one second"
  in test 3, the ten minutes in test 6 and the playback volumes in test 9 are estimates.
- The positions of parts were read from the board file of commit `6776424`. They have to be read again if the
  board is generated again (see the note at the top).
- The allowed ranges for VBUS (5 % around the contract voltage; 4.75 to 5.5 V without a contract) are the general
  USB limits, not values from the project's research notes.
- The rule by which the PD controller picks an offer (highest voltage first) is taken from DECISIONS.md, section 2.
  The CYPD3177 data sheet read on 2026-11-12 (LCSC copy, 002-25383 Rev. *B) confirms the resistor settings and the
  behaviour of the FAULT pin, but does not describe the order.
- The offers of the chargers are manufacturer data, not measurements. The tables of the Apple 20 W and the Anker
  A2337 charger could not be verified and are not used here.
- Which microphone is the left and which the right channel, and the direction of the mute slider, are derived
  from the schematic and from the drawing of the switch.
- That the glow of D4, D6 and D10 can be seen through the vent slots follows from the model only.

**Software**

- `tools/flash_zigbee.sh` has only been run against a simulated radio: the GPIO timing, the real boot loader, the
  answer of the real firmware, the JTAG fallback and the access to `docker`, `/dev/ttyAMA4` and the GPIO lines from
  the terminal app of Home Assistant OS are untested. It is not known whether RF-star delivers the module empty or
  with a firmware; that decides whether the first write goes through the serial boot loader or through JTAG.
- That `--dry-run` works inside the container of Home Assistant OS, that `--probe-only` touches no GPIO line and
  that a stopped run restarts the radio was read from the revised script (commit `6776424`) and, according to
  DECISIONS.md, tried against the simulator; none of it was tried on Home Assistant OS.
- The Home Assistant OS image made by `os/build-image.sh repack` was built and inspected (os/README), never booted.
  The import of the Wi-Fi profile was read from the source of Home Assistant OS; Wi-Fi names or passwords with
  unusual characters, the use under WSL2 and the duration of the first start over Wi-Fi are untested.
- The commands of tests 9 to 11 rely on the contents of Home Assistant's sound container (checked in its source on
  2026-11-12: PulseAudio 17.0, `alsa-utils` with the test sounds) and on the name pattern `soc_sound` from
  `assistant/README.md`. The exact device names and the behaviour of `--volume` above 65536 are unverified.
- The Home Assistant labels were read from the development source on 2026-11-12, not from an installed release.
  Where exactly **System hardware** is opened, and whether `/dev/ttyAMA4` is offered in the port list of ZHA, is
  not known.
- The labels of Raspberry Pi Imager for a custom image file and for Raspberry Pi OS Lite were not re-read on
  2026-11-12.

**Printing and mechanics**

- Print time and filament are estimates from the volume of the models; nothing was sliced.
- No test print exists. Whether an M2.5 machine screw holds in the printed 2.1 mm holes in PETG, and how much force
  a 40 x 18 mm pad of 3 mm cellular rubber needs to be squeezed from 3 mm to 2 mm, is untested.
- **The plug of the speaker.** The dimensions of the Adafruit 3351 come from its maker's data sheet (C5282-001,
  read on 2026-11-12: 70.11 x 30.72 mm, 16.5 mm high, lead 500 mm of AWG 26 wire leaving one short end). That sheet
  names the plug "XH2.54-2P"; Adafruit and BerryBase sell the speaker with a JST-PH plug of 2.0 mm pitch, which is
  what J7 needs. Which plug is really fitted is known only when the speaker is on the table (check in 2.1).
- Whether the folded bundle of the lead fits into the 7 mm gap beside the speaker has not been tried.
- The lips of the USB-A socket flange are scaled from the drawing rather than dimensioned, and the drawing of the
  mute switch gives no tolerance for its body (enclosure/README.md).
- The Bambu Lab EU store could not be read on 2026-11-12 (research notes). The filament named here is the one
  `fab/SHOPPING_LIST.md` found in stock at Reichelt.at.
- No foam rings for the microphone tubes are used, because no shop that was searched sells 0.5 mm foam; the
  acoustic effect of leaving them out is untested.

**Two-device system (chapter 7)**

- Nothing of chapter 7 has run on a board or on Home Assistant OS. What was run in the build environment on
  2026-11-12: the satellite image build with its checks (`os/README.md`, section "Satellite image: verification"),
  the hub add-on in a container against a PulseAudio container and a real ESPHome API client (7 checks), the unit
  tests of the add-on, and `tools/flash_zigbee.sh` against a simulated radio in both roles (51 checks).
- The Home Assistant labels of section 7.2 were read from the source (core 2026.11.1, frontend development branch),
  not from an installed release; the names of the discovered devices, the success dialog with the area field and
  the debug view are described from the source and the documentation.
- The satellite downloads each answer from the hub's web server. That the answers of both devices are always
  played on the device that asked follows from Home Assistant's source (one pipeline per satellite); it was not
  observed with two real devices, and neither was the handling of a wake word heard by both devices (R11).
- That the router firmware joins the hub, that `--rejoin` makes it leave and search again, and that ground-floor
  devices pick it as their parent are taken from Koenkk's firmware sources and the Zigbee standard behaviour.
- RAM and CPU load of the satellite on the 1 GB module, the wake word reliability with the VoxHub microphones and
  the microphone gain of +12 dB are not measured.
- The first boot of the satellite image (Wi-Fi, SSH host keys, user `voxhub`, PipeWire under the lingering user,
  the order of the services) was checked in the image, not on a running board.

## 7. Two devices: hub and satellite

Both assembled boards of the JLCPCB order are identical. They get two roles:

| | Device 1: **hub** | Device 2: **satellite** |
|---|---|---|
| Where | your room, upstairs | your mother's room, downstairs |
| SD card | Home Assistant OS (`os/build-image.sh`, test 6) | VoxHub satellite image (`os/satellite/build-satellite-image.sh`, section 7.3) |
| Home Assistant | yes: the one Home Assistant of the house | no |
| Voice | VoxHub Satellite add-on: wake word, microphones, speaker, LEDs, mute switch | the same satellite software (Linux Voice Assistant 1.1.18) as a system service |
| Understanding, answers | Whisper, Claude (Anthropic integration), Piper - for **both** devices | nothing: it sends the request to the hub and plays the answer |
| Zigbee radio | coordinator (`--role hub`, test 12) | router (`--role satellite`, section 7.6) |
| Compute module | CM4104000 (4 GB) | CM4101000 (1 GB) is enough (`fab/SHOPPING_LIST.md`, section 8) |

```
   upstairs: hub                                     downstairs: satellite
   ┌──────────────────────────────┐   Wi-Fi          ┌──────────────────────────────┐
   │ Home Assistant OS            │◄────────────────►│ Raspberry Pi OS Lite         │
   │  Whisper ─ Claude ─ Piper    │ ESPHome API 6053 │  Linux Voice Assistant       │
   │  VoxHub Satellite add-on     │ answers via 8123 │  LEDs, mute switch           │
   │  ZHA: Zigbee coordinator     │                  │  Zigbee router (radio only)  │
   └──────────────┬───────────────┘                  └──────────────┬───────────────┘
                  │            Zigbee mesh (2.4 GHz)                │
                  └─────────────── devices upstairs ── devices downstairs
```

The request always goes through Claude: wake word on the device that heard it, speech to text on the hub,
Claude with the area of that device, text to speech on the hub, answer on the speaker of the device that heard it.
Why it is built like this: `DECISIONS.md`, section "Two devices: hub and satellite" (S-1 to S-40).

Work through the sections in this order. The hub has to be finished (chapter 3 complete, test 13 passed) before
the satellite is paired.

### 7.1 Before you start

- Both boards went through chapter 3 tests 1 to 5 and 7 (power, compute module, 3.3 V); for the satellite board
  test 5 uses the card of section 7.3, not the Home Assistant OS card. The satellite does tests 6 and 8 to 11 in
  their satellite form in section 7.4 (S6, S8 to S11) before it goes into its case, and test 12 as the router in
  section 7.6; test 13 does not apply to it. The hub did all tests as written.
- An Anthropic API key (console.anthropic.com, "API Keys"). The key is entered once, on the hub.
- The hub has a **fixed IP address**: in your router's DHCP settings give the device `homeassistant` a reservation
  (every router names this differently: "address reservation", "static lease", "always assign this address").
  Write the address down, for example `192.168.1.10`. The satellite is built with it and its firewall only lets
  that address in.
- Areas in Home Assistant: **Settings > Areas, labels & zones**, create one area per room, for example "Upstairs
  room" and "Mother's room" (optionally on floors "Upstairs" and "Ground floor"), and put the lights and devices of
  each room into its area. Claude uses the area of the device that heard the request.

### 7.2 Hub: the Claude pipeline and the VoxHub Satellite add-on

The labels are those of the Home Assistant source on 2026-11-12 (core 2026.11.1, frontend development branch); the
installed release can differ slightly. "Apps" were called "add-ons" in older versions.

1. **Home Assistant URL.** **Settings > System > Network**, section **Home Assistant URL**, field **Local network**:
   switch **Automatic** off and enter `http://192.168.1.10:8123` (your hub's address). The satellites download every
   spoken answer from this address; with a name such as `homeassistant.local` it would depend on name resolution.
2. **Speech services.** **Settings > Apps > Install app**: install and start **Whisper** and **Piper**.
   - Whisper: on the **Configuration** tab choose the model `tiny-int8` (fastest on a CM4) or `base-int8` (better)
     and the language you speak (`de` for German, `en` for English).
   - Piper: choose a voice, for example `de_DE-thorsten-medium` or `en_US-lessac-medium`.
   - **Settings > Devices & services** shows both as discovered **Wyoming Protocol** services: **Add** each.
   - openWakeWord is not needed: the wake word runs on each device.
3. **Claude.** **Settings > Devices & services > Add integration**, search **Anthropic**, enter the API key.
   The integration creates a conversation agent "Claude conversation". Open it (**Anthropic** > the three dots of
   "Claude conversation" > **Reconfigure**) and set:

   | Field | Value |
   |---|---|
   | **Instructions** | the text below |
   | **AI tools** | **Device control** only. Never tick **Home Assistant**: that API reaches everything and bypasses the exposure settings. |
   | **Recommended model settings** | on (Claude Haiku 5.5, effort low: fastest). Switch it off to pick `claude-sonnet-5-5` or `claude-opus-5-5` and the effort. |

   Instructions for the VoxHub (they replace the default text; Home Assistant adds the room of the device and the
   list of your devices by itself):

   ```
   You are the voice assistant of this home. You speak through small loudspeakers in two rooms.
   Keep answers short and conversational, usually one or two sentences. No markdown, lists, emoji or URLs:
   everything you write is read aloud. Say numbers, units and times the way a person would say them.
   Reply in the language the user speaks.
   Speech recognition makes mistakes: go with the most sensible interpretation, ask one short question only if
   the request is truly unclear.
   Do the action instead of describing it, then confirm in a few words. Only say something happened if the tool
   call succeeded.
   Never lock, unlock, arm or disarm anything. If asked, say that this has to be done in the Home Assistant app.
   ```

4. **Pipeline.** **Settings > Voice assistants > Add assistant**:

   | Field | Value |
   |---|---|
   | **Name** | `VoxHub Claude` |
   | **Language** | the language you speak |
   | **Conversation agent** | Claude conversation |
   | **Prefer handling commands locally** | **off** - otherwise Home Assistant's own agent answers simple commands and Claude never sees them |
   | **Speech-to-text** | faster-whisper, same language |
   | **Text-to-speech** | piper, **Voice** as chosen in step 2 |
   | **Wake word engine** | leave empty: the devices detect the wake word themselves |

   **Create**, then make it the preferred assistant (star in the list of assistants).
5. **What Claude may control.** **Settings > Voice assistants**, tab **Expose**: expose the lights, switches,
   covers, climate and media players Claude should control. Locks and alarm panels stay unexposed - Home
   Assistant does not expose them by default, and the VoxHub exposure guard (step 7) keeps them that way.
6. **Stop the old assistant.** If the **VoxHub Assistant** app runs, stop it and switch **Start on boot** off. It
   uses the same microphones and LEDs.
7. **VoxHub Satellite app.** **Settings > Apps > Install app**, three dots > **Repositories**:
   add `https://github.com/geilevideossos-gamedev/fable-sbc-test#claude/gallant-hamilton-kojnjj`. The part after
   `#` is the branch with the two-device version; as long as it is not merged into `main`, the address without it
   offers only VoxHub Assistant (if you added the repository before without `#...`, remove it and add it again).
   Install **VoxHub Satellite**. The first install builds the app on the hub (several minutes).
   - **Configuration** tab: **Device name** `VoxHub Upstairs` (the room of the hub). Keep the other defaults:
     **Exposure guard** on, **Protected domains** `lock` and `alarm_control_panel`, **Microphone gain** 4.
   - **Info** tab: **Protection mode** off (needed for the LEDs and the mute switch), **Start on boot** on,
     **Start**.
   - **Log** tab, expected lines: `Microphone alsa_input...soc_sound...`, `Exposure guard on: alarm_control_panel,
     lock are never exposed to Assist`, `Server started (host=127.0.0.1, port=6053)` (the hub's satellite only listens on the hub itself), `Connected to the voice
     satellite at ws://127.0.0.1:6055`. The green LED blinks slowly: the satellite is not paired yet.
8. **Pair the hub's own satellite.** **Settings > Devices & services**: under **Discovered**, **ESPHome** offers
   "VoxHub Upstairs" (or `lva-<12 hex digits>`). **Add**, **Submit**; in the success dialog choose the **Area**
   of the hub's room. The green LED now stays on.
9. On the new device page (**Settings > Devices & services > ESPHome > VoxHub Upstairs**): **Assistant** =
   `VoxHub Claude`, **Wake word** = `Okay Nabu` (or another one). Check that the device page shows the **Area**.

| Expected | If not |
|---|---|
| ESPHome device "VoxHub Upstairs" in the area of the hub's room, green LED on, "Okay Nabu, what time is it?" is answered from the hub's speaker | **No discovered device:** **Settings > Devices & services > Add integration > ESPHome**, host `127.0.0.1`, port 6053. **The log says "the sound card did not appear":** the VoxHub block is missing in `config.txt` (test 9 fails as well). **No LEDs:** protection mode is still on; the log says `LED feedback disabled`. **The answer is spoken by Home Assistant's own agent ("Turned on the light") instead of Claude:** "Prefer handling commands locally" is on, or the device uses another assistant. |

### 7.3 Satellite: build and write the SD card

On a Linux PC (Debian / Ubuntu; WSL2 with Ubuntu should work but is untested):

```bash
sudo apt install git curl xz-utils fdisk parted e2fsprogs openssl python3 device-tree-compiler qemu-user-static binfmt-support
git clone https://github.com/geilevideossos-gamedev/fable-sbc-test.git
cd fable-sbc-test
sudo os/satellite/build-satellite-image.sh --wifi-ssid 'NAME OF YOUR WIFI' --wifi-psk 'PASSWORD OF YOUR WIFI' \
    --wifi-country AT --hub 192.168.1.10 --room "Downstairs" --password 'A PASSWORD FOR THE SATELLITE'
```

- `--hub` is the fixed address of the hub from section 7.1. `--room` gives the device its name ("VoxHub
  Downstairs"). The room itself is assigned in Home Assistant in section 7.5.
- The same branch as for the Home Assistant OS image applies: as long as this work is not merged into `main`, run
  `git checkout claude/gallant-hamilton-kojnjj` after `cd fable-sbc-test`.
- The script runs about 25 minutes (packages are installed into the image in emulation) and ends with
  `[voxhub-satellite] all checks passed` and `done: .../os/output/voxhub-satellite-2026-10-06-lva1.1.18.img.xz`.
- Write the file to a microSD card with Raspberry Pi Imager: **Choose OS > Use custom**, the `.img.xz` file, the
  card, **Next**. Decline **OS customisation**: the image does not use it.

The Wi-Fi preset has the same limits as the hub's: WPA2 with a password, no hidden network, no login page.

### 7.4 Satellite: first boot and bring-up (replaces tests 6 and 8 to 11 for this board)

Card in, compute module (1 GB) fitted, speaker plugged in, 30 W charger.

**Test S6 - first boot**

1. Plug in the charger. D6 (5 V) at once, D10 (card activity) flickers.
2. After about two minutes the green status LED D7 **blinks slowly** (one second on, one second off): Linux
   Voice Assistant runs and waits for Home Assistant.
3. From the PC: `ssh voxhub@voxhub-satellite.local` (or the address your router lists for `voxhub-satellite`), the
   password of `--password`. Then:

   ```bash
   sudo voxhub-status
   ```

   Expected: `voxhub-lva active`, `voxhub-peripherals active`, `voxhub-hubwatch active`, `NetworkManager active`,
   `ssh active`; under **Hub** `"reachable": true`; under **Firewall** `tcp dport 6053 ip saddr @hub4 accept` and
   `elements = { 192.168.1.10 }`; under **Sound card** a source and a sink with `soc_sound` in the name; LEDs
   `voxhub-green` / `voxhub-blue` present.

| Expected | If not |
|---|---|
| green LED blinks slowly, `voxhub-status` as above | **Never on the network:** Wi-Fi name or password wrong, WPA3-only network, or too far from the access point: build the image again. **`"reachable": false`:** the hub's address in `--hub` is wrong or the hub is off; edit `VOXHUB_HUB` in `/etc/voxhub/satellite.env` and run `sudo systemctl restart voxhub-hubwatch voxhub-lva`. **No `soc_sound` source:** the VoxHub block is missing in `/boot/firmware/config.txt` - the card was not made with the satellite script. **LED dark:** `journalctl -u voxhub-peripherals -n 20`. |

**Test S8 - USB-A ports (optional on the satellite).** Plug the USB stick into each socket in turn and run
`lsblk`; `sda` appears. Same faults as test 8.

**Test S9 - microphones.** Over SSH, as the user `voxhub`:

```bash
SRC=$(pactl list short sources | grep soc_sound | grep -v monitor | cut -f2)
SNK=$(pactl list short sinks | grep soc_sound | cut -f2)
parecord --device="$SRC" --file-format=wav --channels=2 /tmp/mic.wav & sleep 8; kill %1
paplay --device="$SNK" --volume=164619 /tmp/mic.wav
paplay --device="$SNK" --volume=164619 --channel-map=front-right,front-left /tmp/mic.wav
```

Speak during the eight seconds, first over the front left corner (MK1), then over the rear right corner (MK2).
The first `paplay` plays MK1 (left channel), the second MK2 (the channels swapped, as in test 9). The recording
already contains the +12 dB of the satellite's microphone gain; `--volume=164619` adds 24 dB, so it plays about as
loud as test 9. Expected and faults: as test 9.

**Test S10 - speaker.**

```bash
paplay --device="$SNK" /usr/share/sounds/alsa/Front_Center.wav
```

A voice says "Front Center". Faults: as test 10.

**Test S11 - mute switch.** Push the slider to the mute position: D9 (red) on. Repeat test S9: silence. Push it
back: D9 off, voice back. The status LEDs are tested in section 7.8 (they need the hub).

### 7.5 Pair the satellite with the hub and give it its room

1. With the satellite running, open **Settings > Devices & services** on the hub. **Discovered** shows a second
   **ESPHome** device, "VoxHub Downstairs" or `lva-<12 hex digits>`. **Add**, **Submit**.
2. In the success dialog choose the **Area** "Mother's room". If you skipped it: device page > pencil icon >
   **Area**.
3. Device page: **Assistant** = `VoxHub Claude`, **Wake word** = `Okay Nabu`.
4. The satellite's green LED stops blinking and stays on.
5. Room check, from each room: "Okay Nabu, which room are you in?" The hub answers with the hub's area, the
   satellite with "Mother's room". Home Assistant tells Claude for every request: *You are in area Mother's room
   and all generic commands like 'turn on the lights' should target this area.*

| Expected | If not |
|---|---|
| Second ESPHome device in "Mother's room", green LED steady, the room answer is right on both devices | **Not discovered:** add it by hand: **Add integration > ESPHome**, host = the satellite's address, port 6053. **"Connection refused" or timeout although the satellite runs:** the satellite's firewall does not know the hub's current address (`sudo voxhub-status`, section **Firewall**); fix `VOXHUB_HUB` (section 7.4, test S6). **Claude asks which room you mean:** the device has no area. **Wrong room:** the area is set on the wrong device; the area of the *device* counts, not the one of its entities. |

### 7.6 Zigbee router on the satellite

The hub's radio is the coordinator (test 12, `--role hub`). The satellite's radio becomes a router: it forwards
messages for the Zigbee devices on the ground floor. Do not add a Zigbee integration on the satellite - it has no
Home Assistant, and a second coordinator would form a second, separate network.

1. Write the router firmware. On the satellite (SSH):

   ```bash
   sudo voxhub-flash-zigbee --role satellite
   ```

   The firmware and the flashing tool are stored in the image, so no internet is needed. The script prints
   `Role: satellite (option) - firmware: Zigbee router (Z-Stack 20250403)` and ends with
   `SUCCESS: the radio runs the Zigbee router firmware 20250403 (role: satellite).` Before that, instead of the
   coordinator's "The radio answers as a Zigbee coordinator", it prints `The radio is silent on the serial port,
   as expected: the router firmware has no serial interface.` and `The bootloader confirmed the checksum of the
   written image.` Run once more, it says `The flash holds exactly CC1352P2_CC2652P_launchpad_router_20250403.`
   and writes nothing.
2. The router searches for a network **once**, right after it starts. So open the hub's network first: on the
   hub, **Settings > Devices & services > Zigbee Home Automation > Add device**, and leave the page open.
3. Within the next minute, on the satellite:

   ```bash
   sudo voxhub-flash-zigbee --role satellite --rejoin
   ```

   This presses the router's button electrically (GPIO25 low for half a second): it leaves any old network and
   searches again.
4. On the hub's page the device **TexasInstruments ti.router** appears. Name it "Zigbee router Mother's room" and
   give it the area "Mother's room".
5. Check the mesh: **Settings > Devices & services > Zigbee Home Automation > Configure**, tab **Visualization**
   (network map): a line between the coordinator and the router. Pair one Zigbee device on the ground floor (in
   the mother's room) and look at the map again: it hangs on the router, not directly on the coordinator. Mains
   powered devices route themselves too; battery devices pick the best parent when they join.

| Expected | If not |
|---|---|
| `SUCCESS ... router firmware 20250403 (role: satellite)`; "TexasInstruments ti.router" in ZHA; a ground-floor device routes through it | **The router does not appear:** the hub's "Add device" page was not open when the router searched: open it, run `--rejoin` again. Distance: at the first join keep the satellite within a few rooms of the hub; afterwards the router can be moved. **The script refuses with "This system runs Home Assistant OS, so it is the hub":** you are on the hub - use `--role hub` there. **Other messages:** the table at the end of test 12 applies to the satellite as well. |

To take the router out of the network later: remove it in ZHA (it resets itself and searches once more) or run
`--rejoin` while the hub does not accept new devices.

### 7.7 Exposure guard check

1. If you have a lock (or an alarm panel) in Home Assistant: **Settings > Voice assistants > Expose**, **Expose
   entities**, select the lock, **Expose**.
2. Within a few seconds it disappears from the list again, a notification "VoxHub: removed from the voice
   assistant" appears, and the VoxHub Satellite log says `Exposure guard: lock.<name> is no longer exposed to Assist
   (lock entities are never available to the voice assistant)`.
3. Without a lock: create a scene that contains any lock or alarm entity, or skip this check. A scene of lights only
   stays exposed.

### 7.8 Tests from both rooms

Two people help: one in each room. "Wake word" is "Okay Nabu" unless you changed it. Use your own device and room
names.

| # | Room | Say / do | Expected |
|---|---|---|---|
| R1 | hub room | wake word | blue LED on the hub only, short sound from the hub; the satellite stays green |
| R2 | hub room | "which room are you in?" | blue blinking while Claude thinks, green + blue while it speaks; answer names the hub's room, from the hub's speaker only |
| R3 | mother's room | wake word, "which room are you in?" | the same on the satellite, answer "Mother's room", from the satellite's speaker only |
| R4 | hub room | "turn on the light" | the light(s) of the hub's area go on, none downstairs |
| R5 | mother's room | "turn on the light" | the light(s) of "Mother's room" go on, none upstairs |
| R6 | mother's room | "turn off the light in the <hub's room>" | the named room wins over the device's room |
| R7 | both | "unlock the front door" (or any lock) | Claude declines; nothing unlocks; with no lock exposed it says it cannot do that |
| R8 | mother's room | slider to mute, then the wake word | red LED on, green and blue off; no reaction; on the hub the satellite's **Mute** switch shows on. Slider back: green on, wake word works |
| R9 | hub room | the same with the hub's slider | the same on the hub |
| R10 | mother's room | "set a timer for one minute" | after a minute the satellite rings (green and blue alternating) until you say "stop" |
| R11 | both, at the same time | both people say the wake word | each device answers its own person, or Home Assistant drops one of two detections of the same voice (`duplicate_wake_up_detected`) - never an answer in the wrong room |
| R12 | hub | **Settings > Voice assistants > VoxHub Claude**, three dots > **Debug**: the last runs of both devices | each run shows Conversation agent "Claude conversation" and the device that started it; no run handled locally |
| R13 | satellite | pull the hub's charger for a minute, then plug it in again | the satellite's green LED blinks slowly while the hub is away, steady again a few minutes after the hub is back |
| R14 | satellite | `systemctl list-timers 'apt-daily*'` and `sudo unattended-upgrade --dry-run -v` over SSH | both timers listed; the dry run prints "Allowed origins are: ..." with Debian, Debian-Security and Raspberry Pi Foundation, then the packages it would upgrade, and ends without an error |
| R15 | mother's room | a Zigbee device near the satellite | operable from Home Assistant; in the network map it is connected through the router |

### 7.9 Results table, two-device system

| # | Test | Expected | Seen | OK |
|---|---|---|---|---|
| 7.2 | Hub satellite paired, area set, assistant VoxHub Claude | green LED steady | | [ ] |
| S6 | Satellite first boot, `voxhub-status` | services active, hub reachable, firewall with the hub's address | | [ ] |
| S9 | Satellite microphones MK1 / MK2 | voice audible | | [ ] |
| S10 | Satellite speaker | "Front Center" | | [ ] |
| S11 | Satellite mute switch | silent while D9 is lit | | [ ] |
| 7.5 | Satellite paired, area "Mother's room" | green LED steady, room answer right | | [ ] |
| 7.6 | Router firmware, join | `SUCCESS ... 20250403`, "TexasInstruments ti.router" in ZHA | | [ ] |
| 7.7 | Exposure guard | an exposed lock is un-exposed again | | [ ] |
| R1-R15 | Tests from both rooms | as in 7.8 | | [ ] |

### 7.10 Troubleshooting the two-device system

| Symptom | Cause and fix |
|---|---|
| The satellite hears the wake word (blue), then nothing is said | The satellite cannot download the answer from the hub. `sudo voxhub-status`, section **Hub**: `reachable` must be `true`; **Settings > System > Network > Local network** on the hub must be `http://<hub address>:8123` (section 7.2 step 1). `journalctl -u voxhub-lva -n 30` shows the URL it tried. |
| Fast blinking of green and blue | The request failed in the pipeline (no internet for Claude, Whisper or Piper stopped, API key rejected). Look at the pipeline debug view (R12) and at the logs of Whisper and Piper. |
| Answers come from Home Assistant's own agent, short and fixed | "Prefer handling commands locally" is on, or the device page names another assistant. |
| The satellite answers, but Claude does not know the room | The satellite device has no area (section 7.5). |
| The wake word is not heard well | Raise the microphone gain: on the hub the option **Microphone gain** (e.g. 6), on the satellite `VOXHUB_MIC_GAIN=6` in `/etc/voxhub/satellite.env` and `sudo systemctl restart voxhub-lva`. Too much gain makes loud speech clip. **Wake word 1 Sensitivity** on the device page changes the threshold. |
| After a new Home Assistant address the satellite is "unavailable" | Its firewall still has the old address: `VOXHUB_HUB` in `/etc/voxhub/satellite.env`, then `sudo systemctl restart voxhub-hubwatch voxhub-lva`. |
| Changes of the satellite configuration | `sudo nano /etc/voxhub/satellite.env` (name, hub address, microphone gain), then `sudo systemctl restart voxhub-lva voxhub-hubwatch`. The wake word is chosen on the device page in Home Assistant (**Wake word**; `VOXHUB_WAKE_WORD` only sets the first one), the room is the device's **Area** (section 7.5; `VOXHUB_ROOM` is only a note). Wi-Fi: `sudo nmtui`. |
