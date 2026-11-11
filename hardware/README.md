# Hardware: VoxHub CM4 carrier, revision A1

KiCad 9 project, **generated entirely from code** (`gen/`). Do not edit the `.kicad_sch` / `.kicad_pcb` files
by hand - change the generator and run `./build.sh`.

## Contents

| Path | What |
|---|---|
| `voxhub.kicad_pro`, `voxhub.kicad_sch` + 5 sub-sheets, `voxhub.kicad_pcb` | the KiCad project |
| `voxhub.kicad_sym`, `voxhub.pretty/` | project symbol / footprint libraries (generated) |
| `3dmodels/` | STEP models used by the footprints (KiCad library copies + simple stand-ins) |
| `gen/design.py` | **the circuit**: every part, value and net |
| `gen/kisch.py`, `gen/sexpr.py` | schematic writer |
| `gen/parts.py`, `gen/sourcing.py`, `gen/sourcing_live.json`, `gen/make_bom.py` | part catalogue, second sources, live distributor data (DigiKey, 2026-11-11), BOM generator |
| `gen/make_footprints.py`, `gen/make_3dmodels.py` | project footprints and coloured stand-in models |
| `gen/build_pcb.py` | placement, power fan-out, DSN export, import, patch router, repair, USB length matching, pours |
| `gen/postroute.sh` | iterate DRC -> repair -> patch until clean, then USB pair re-route + serpentine matching |
| `gen/routed/voxhub.ses` | autorouter session (Freerouting 2.0.1) the committed board was built from |
| `gen/placement.json` | final part positions (also drives the enclosure model) |
| `outputs/` | everything a fab / assembler needs (below) |

### `outputs/`

| File | Purpose |
|---|---|
| `voxhub_schematic.pdf` | schematic, 6 pages |
| `erc.rpt`, `drc.rpt` | kicad-cli reports: **0 ERC violations, 0 DRC violations, 0 unconnected, 0 parity issues** |
| `drc_waived_checks_enabled.rpt` | the same DRC with the waived checks switched on (9 warnings, explained below) |
| `gerbers/` + `voxhub_gerbers.zip` | Gerber X2: F/In1/In2/B copper, mask, paste, silk, Edge.Cuts; Excellon PTH + NPTH drill, drill maps, job file |
| `voxhub_pos.csv` | pick-and-place (both sides, DNP parts excluded) |
| `bom.csv` | PCB assembly BOM: MPN, manufacturer, DigiKey PN / status / stock / price at 1 and 100 (live, 2026-11-11), Mouser PN (not live), second source |
| `bom_system.csv` | module, speaker, heat sink, screws, SD card ... |
| `voxhub_outline.dxf` | mechanical outline: board edge, mounting holes, CM4 holes/outline, microphone ports, LED slots, connector envelopes, courtyards |
| `mechanical_positions.csv` | the same positions as numbers |
| `voxhub_pcb.step` | 3D model of the assembled board |
| `pcb_layers/voxhub.pdf` | layer plots |
| `render_top.png`, `render_bottom.png`, `render_iso.png` | kicad-cli 3D renders |
| `routing_stats.txt` | track / via counts; USB pairs: pad-to-pad length and skew (with 1.5 mm per via and with vias counted as 0), the pads each line runs through, copper that is not on that path; SD / I2S / PDM lengths |

![top](outputs/render_top.png)

## Rebuilding

```bash
docker pull kicad/kicad:9.0                # KiCad 9.0.9 was used
wget -P hardware https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar
SKIP_ROUTE=1 hardware/build.sh all         # schematic -> ERC -> netlist -> place -> import -> patch -> DRC -> outputs
hardware/build.sh all                      # same, but re-runs the autorouter first (Java >= 21)
```

`SKIP_ROUTE=1` re-uses the committed autorouter session and reproduces the committed board exactly (the patch
router is deterministic). Freerouting 2.0.1 with one thread produced the same session in every run here, but that is not
guaranteed on another machine or JRE. Two quirks the build works around: it sometimes exits with an empty session file
after routing (the build starts it up to three times and checks the file), and it keeps a `freerouting.json` in the
temp directory (each run gets its own).

How the board is produced:

1. `design.py` writes the schematic; `kicad-cli sch erc` must pass; the KiCad netlist is compared pin by pin with the code model.
2. `build_pcb.py place`: fixed positions for connectors/ICs/mechanics + a greedy "nearest free spot to the pad it talks to" placer
   for passives; outline; keep-outs; scripted fan-out of every GND / +5V pad to the inner planes; fixed escape pattern for the WLCSP.
3. Freerouting 2.0.1 routes the signals on F.Cu / B.Cu (planes are declared as power layers).
4. `build_pcb.py finish`: import, widen necked tracks to 0.1 mm, discard whatever the autorouter drew for the six USB
   data nets, add the locked flow-through links under the two USB ESD parts, GND and +5V planes, GND pours on both outer layers.
5. `postroute.sh`: the patch router (A* on a 0.05 mm grid with rip-up) joins whatever is still open - the USB data nets
   first, as 0.2 mm traces laid pad to pad (hub pin -> ESD pad -> link -> ESD pad -> connector pin; a USB line may not
   touch its own copper, change layer only as a last resort, and is never ripped up by another net) - and a DRC-driven
   repair removes offending copper, until `kicad-cli pcb drc` is clean. Then the USB nets are laid again in up to six
   different net orders; after each, the shorter line of every pair gets serpentine bumps until the pad-to-pad lengths
   agree. The best variant is kept (worst of: skew, skew with vias counted as 0, copper off the path); the step fails if
   no variant is DRC-clean with every pair within 3.8 mm.
6. `build_pcb.py pours`: local copper pours for VBUS, VBUS_SW, the buck switch node, the buck output and USB VBUS.

## Fabrication notes

| Parameter | Value |
|---|---|
| Size | 100.0 x 74.0 mm, 3 mm corner radius, 1.6 mm, FR-4 Tg >= 150 |
| Layers | 4: F.Cu signal + GND pour / In1.Cu GND plane / In2.Cu +5 V plane / B.Cu signal + GND pour |
| Copper | 35 um (1 oz) outer, 17.5-35 um inner |
| Stack-up | **prepreg F.Cu-In1.Cu 0.10 mm** (e.g. JLCPCB JLC04161H-3313 or any "2313/3313 outer prepreg" stack-up). The USB 2.0 data lines are 0.2 mm wide, i.e. about 45 ohm single-ended over the plane -> ~90 ohm differential (loosely coupled). With a 0.2 mm prepreg (7628 stack-up) they would be ~70 ohm - ask for the thin outer prepreg. |
| Min. track / space | 0.10 mm / 0.12 mm (router targets: 0.15 / 0.13 mm; 0.12 mm tracks only where the patch router needed them) |
| Vias | through, 0.5 mm pad / 0.25 mm drill (signal) and 0.6 / 0.3 mm (power); tented both sides |
| Min. drill | 0.25 mm; min. hole-to-hole 0.25 mm |
| Via-in-pad | only in the exposed pads of U1, U2, U4, U10 (thermal/ground vias, 0.3 mm, tented on B; the eight under U2 are part of the KiCad footprint) - no filling required |
| Slots / NPTH | 3 non-plated slots 1.8 x 2.4 mm (reverse-mount LEDs), **4 plated slots 0.6 mm wide** (1.4 and 1.7 mm long, shell stakes of the USB-C connector J1), NPTH: 2 x 0.8 mm (microphone ports), 2 x 0.65 mm (J1 locating pegs), 3 x 0.99 mm (Tag-Connect J8), 4 x 2.7 mm (mounting), 4 x 3.7 mm (spacers) |
| Finish | **ENIG** (0.4 mm pitch WLCSP and mezzanine connectors) |
| Mask / silk | any colour; silkscreen is clipped by the mask openings (Gerbers are plotted with `--subtract-soldermask`) |
| Copper to board edge | >= 0.35 mm for routed copper (edge connectors' own pads excepted) |
| Keep-outs | no copper on any layer under the MGM240P antenna (19.6..28.4 x 69.2..74, Silicon Labs datasheet) and under the CM4 antenna (91..100 x 44.5..59.5: the 6.5 x 11 mm "Wireless Cutout" of CM4 datasheet fig. 4 enlarged to the recommended 8 x 15 mm and out to the board edge) |
| Impedance control | not required if the stack-up above is used; otherwise specify 90 ohm differential for nets `USB*` on F.Cu/B.Cu |
| Panel | fiducials FID1-3 are on the board; add rails + tooling holes as your assembler requires (edge connectors overhang the rear edge by up to 2.5 mm) |

## Assembly notes

- **Side F (component side, "top" in the files)**: all SMT parts. **Side B**: only SW1 (mute slide switch) - place in a second
  pass (6 J-bend terminals folded under the body edge: reflow preferred, hand soldering needs a fine tip).
- THT parts: J6 (stacked USB-A), J7 (JST-PH) - selective/hand solder from side B. J5 (debug header) is **DNP**; C13 (feed-forward
  capacitor) is **DNP**.
- U9 ADAU7002: WLCSP-8, 0.4 mm pitch, NSMD pads 0.22 mm. Use a 0.10 mm stencil, type 4 paste; X-ray or electrical test.
- U11 MGM240P and J2/J3 (0.4 mm mezzanine sockets): reflow only, no hand soldering. J2/J3 must be placed with the pick-and-place
  centroid of each connector (they define the CM4 position together with the four SMT spacers H5-H8).
- MK1/MK2 (bottom-port MEMS microphones): **no washing / no ultrasonic cleaning** after reflow, do not pick up with a nozzle over
  the port side, keep the 0.8 mm PCB port holes free of flux and conformal coating.
- D7-D9 are reverse-mount LEDs: they sit on side F and emit through the PCB slot towards side B.
- H5-H8: Wurth 9774015151R SMT spacers (reflow). The CM4 is then fixed with 4 x M2.5 x 5 mm screws.
- Polarised parts: C38, C41 (polymer tantalum), D1 (TVS, cathode to VBUS), D5 (zener, cathode to VBUS), LEDs.
- JP1 (solder jumper, open by default): close only to force the CM4 into USB boot (not needed for the Lite module).
- Pick-and-place file: KiCad coordinates in mm (board origin at X = 100, Y = 60 on the KiCad page; Y is negated in the file as usual),
  rotations as KiCad exports them - check the first article for the usual per-package rotation offsets of your assembler.

### Programming and test (per board)

1. Without CM4: apply a 9 V-capable PD source. Expect VBUS = 9 V (TP1), VBUS_SW = 9 V (TP2), +5V = 5.02 V nominal, accept
   4.86 .. 5.23 V without load (Vref +-1.5 %, 1 % resistors, up to +2.5 % at no load) (TP3),
   green PWR LED on, red PD-FAULT LED off. With a 5 V-only source: TP2 = 0 V, red LED on, no 5 V.
2. Fit the CM4 (+3V3 on TP4 = 3.3 V), boot the test image, check: both USB-A ports enumerate a high-speed device,
   `arecord`/`aplay` loopback through the googlevoicehat card, both microphones (left/right channel), mute switch (red LED on,
   capture goes silent), green/blue LEDs via `/sys/class/leds`, `i2cdetect -y 1` shows 0x08.
3. Flash the radio: the MGM240P ships with a serial bootloader only. Program the EmberZNet NCP (or OpenThread RCP) firmware
   through the Tag-Connect pads J8, or in-system from the CM4 (SWDIO = GPIO22, SWCLK = GPIO23; openocd `bcm2835gpio` or
   `linuxgpiod` driver). **Reset is active high on the CM4 side:** GPIO24 high pulls the module's RESETn low through Q4
   (open drain); leave GPIO24 low or floating to run. In openocd (0.12 or newer) that is `adapter gpio srst 24 -active-high` together
   with `reset_config srst_only srst_push_pull`: GPIO24 only drives the gate of Q4, the open-drain behaviour at RESETn
   comes from Q4 (with `srst_open_drain` openocd would never drive the pin high, so reset would never be asserted). Or
   toggle GPIO24 from the flashing script; J8 pin 3 is the module's RESETn itself.
   UART: 115200 baud on `/dev/ttyAMA4` (UART4 keeps its number on the HAOS 18.5 kernel), TX = PA05, RX = PA06, RTS = PA07, CTS = PA08 (the Silicon Labs reference
   assignment, datasheet fig. 5.1), bootloader strap = PC00 (GPIO25, active low).

## DRC: waived checks

`outputs/drc.rpt` is clean with the following five checks set to "ignore" in the project
(`gen/project_settings.json`). `outputs/drc_waived_checks_enabled.rpt` shows what they would report: 9 warnings, 0 errors.

| Check | Count | Why it is waived |
|---|---|---|
| `silk_edge_clearance` | 4 | Library silkscreen of the edge connectors (USB-C, USB-A, microSD) reaches the board edge by design; it is cut off at the outline. |
| `silk_over_copper` | 2 | Library silkscreen lines over exposed pads; the Gerbers are plotted with silkscreen subtracted from mask openings, so nothing is printed on pads. |
| `silk_overlap` | 1 | Overlapping silkscreen of neighbouring parts (cosmetic). Reference designators are on the F.Fab layer, not on silk. |
| `footprint_type_mismatch` | 1 | U2 uses KiCad's `...HSOP-8-1EP..._ThermalVias` footprint: an SMD part whose exposed pad contains plated thermal vias, which KiCad classifies as "through hole". Intentional. |
| `lib_footprint_mismatch` | 1 | Only J1 (USB-C) is reported: its board copy differs from the library footprint in the layer set of the two NPTH locating-peg pads (library F&B.Cu, board *.Cu). Pad size equals drill size, so no copper is affected. (The 3D model paths rewritten to `hardware/3dmodels` are not what this check reports.) |

Board rules deliberately relaxed from KiCad's defaults (all within standard 4-layer fab capability): minimum hole 0.2 mm,
copper-to-edge 0.17 mm (the KiCad reverse-mount LED land pattern has its own pads 0.175 mm from its slot), minimum track 0.1 mm,
thermal relief spokes >= 1.

## Known limitations (read before ordering)

- **Autorouted.** The layout is electrically complete and rule-clean, but it is not hand-optimised: return paths, loop areas of the
  buck converter and analogue-quality details were not reviewed by a human layout engineer. Buck power stage: the 220 nF
  high-frequency bypass C10 and the VCC capacitor C11 have fixed positions directly at the regulator pins (1.8 mm centre to
  centre); everything else is placed by the automatic placer and tied in with pours and plane vias - bulk input capacitors
  C8 / C9 3.5 .. 7.4 mm from VIN / PGND, boot capacitor C12 4 .. 6 mm from BOOT / SW. Review the hot loop before a production spin.
- **USB 2.0 pairs are loosely coupled, not true differential pairs** (see stack-up note), but they are length matched and
  free of stubs. `outputs/routing_stats.txt`: pad-to-pad length (hub pin to connector pin) 30.99 / 30.99 mm upstream,
  11.21 / 11.21 mm port 1, 15.17 / 15.17 mm port 2, i.e. an intra-pair skew of 0.00 mm on all three pairs against the usual
  3.8 mm (150 mil) guideline. All six lines stay on F.Cu, none has a via. Every downstream line runs hub pin -> ESD pad
  (row facing the hub) -> locked link under the USBLC6-2SC6 -> ESD pad (row facing the connector) -> connector pin; the
  copper that is not on that path is at most 0.05 mm (track ends inside pads). The numbers come from a copper graph that
  joins tracks wherever they touch and were confirmed by an independent re-computation (DECISIONS.md section 6a).
  Still verify with a USB 2.0 high-speed device and, ideally, an eye-diagram test on the first prototypes.
- SD card lines are 57-93 mm long with up to 36 mm mismatch: fine for 50 MHz high-speed mode (about 240 ps against a 20 ns
  period); UHS-I SDR104 is not guaranteed.
- Mechanical dimensions were checked against the manufacturer drawings (DECISIONS.md section 9); two of them (USB-A flange
  lip, speaker terminal position) are scaled from the drawing rather than dimensioned.
- Five lines of the BOM were at 0 stock at DigiKey on the day of the check: LMR33640ADDAR, CL31A226KOHNNNE (22 uF) and
  2N7002,215 have no in-stock drop-in with equal ratings; TPS2553DBVR is available as the DBVT reel; CL31B106KBHNNNE
  (10 uF X7R) only as a 2,000-piece Marketplace item. See the cost summary in the top-level README and DECISIONS.md
  section 10.
- No hardware has been built or measured.
