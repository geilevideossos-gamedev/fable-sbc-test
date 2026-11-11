# Hardware: VoxHub CM4 carrier, revision A

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
| `gen/parts.py`, `gen/sourcing.py`, `gen/make_bom.py` | part catalogue, sourcing data, BOM generator |
| `gen/make_footprints.py`, `gen/make_3dmodels.py` | project footprints and stand-in models |
| `gen/build_pcb.py` | placement, power fan-out, DSN export, import, patch router, repair, pours |
| `gen/postroute.sh` | iterate DRC -> repair -> patch until clean, then USB pair re-route |
| `gen/routed/voxhub.ses` | autorouter session (Freerouting 2.0.1) the committed board was built from |
| `gen/placement.json` | final part positions (also drives the enclosure model) |
| `outputs/` | everything a fab / assembler needs (below) |

### `outputs/`

| File | Purpose |
|---|---|
| `voxhub_schematic.pdf` | schematic, 6 pages |
| `erc.rpt`, `drc.rpt` | kicad-cli reports: **0 ERC violations, 0 DRC violations, 0 unconnected, 0 parity issues** |
| `drc_waived_checks_enabled.rpt` | the same DRC with the waived checks switched on (10 warnings, explained below) |
| `gerbers/` + `voxhub_gerbers.zip` | Gerber X2: F/In1/In2/B copper, mask, paste, silk, Edge.Cuts; Excellon PTH + NPTH drill, drill maps, job file |
| `voxhub_pos.csv` | pick-and-place (both sides, DNP parts excluded) |
| `bom.csv` | PCB assembly BOM: MPN, manufacturer, distributor PN, qty, unit price, lifecycle, second source |
| `bom_system.csv` | module, speaker, heat sink, screws, SD card ... |
| `voxhub_outline.dxf` | mechanical outline: board edge, mounting holes, CM4 holes/outline, microphone ports, LED slots, connector envelopes, courtyards |
| `mechanical_positions.csv` | the same positions as numbers |
| `voxhub_pcb.step` | 3D model of the assembled board |
| `pcb_layers/voxhub.pdf` | layer plots |
| `render_top.png`, `render_bottom.png`, `render_iso.png` | kicad-cli 3D renders |
| `routing_stats.txt` | track / via counts, USB pair lengths and skew |

![top](outputs/render_top.png)

## Rebuilding

```bash
docker pull kicad/kicad:9.0                # KiCad 9.0.9 was used
wget -P hardware https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar
SKIP_ROUTE=1 hardware/build.sh all         # schematic -> ERC -> netlist -> place -> import -> patch -> DRC -> outputs
hardware/build.sh all                      # same, but re-runs the autorouter first (Java >= 21)
```

`SKIP_ROUTE=1` re-uses the committed autorouter session and reproduces the committed board exactly (the patch
router is deterministic). Re-running Freerouting gives a different but equivalent starting point.

How the board is produced:

1. `design.py` writes the schematic; `kicad-cli sch erc` must pass; the KiCad netlist is compared pin by pin with the code model.
2. `build_pcb.py place`: fixed positions for connectors/ICs/mechanics + a greedy "nearest free spot to the pad it talks to" placer
   for passives; outline; keep-outs; scripted fan-out of every GND / +5V pad to the inner planes; fixed escape pattern for the WLCSP.
3. Freerouting 2.0.1 routes the signals on F.Cu / B.Cu (planes are declared as power layers).
4. `build_pcb.py finish`: import, widen necked tracks to 0.1 mm, GND and +5V planes, GND pours on both outer layers.
5. `postroute.sh`: the patch router (A* on a 0.05 mm grid with rip-up) joins whatever is still open and a DRC-driven repair
   removes offending copper, until `kicad-cli pcb drc` is clean; then the six USB data nets are ripped up and re-routed as
   short 0.2 mm traces (several net orders are tried, the best-matched clean result is kept).
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
| Via-in-pad | only in the exposed pads of U1, U4, U10 (thermal/ground vias, 0.3 mm, tented on B) - no filling required |
| Slots | 3 non-plated slots 1.8 x 2.4 mm (reverse-mount LEDs), 2 NPTH 0.8 mm (microphone ports), 4 NPTH 2.7 mm, 4 NPTH 3.7 mm (spacers) |
| Finish | **ENIG** (0.4 mm pitch WLCSP and mezzanine connectors) |
| Mask / silk | any colour; silkscreen is clipped by the mask openings (Gerbers are plotted with `--subtract-soldermask`) |
| Copper to board edge | >= 0.35 mm for routed copper (edge connectors' own pads excepted) |
| Keep-outs | no copper on any layer under the MGM240P antenna (19.6..28.4 x 69.2..74) and under the CM4 antenna corner (90..100 x 35..47) |
| Impedance control | not required if the stack-up above is used; otherwise specify 90 ohm differential for nets `USB*` on F.Cu/B.Cu |
| Panel | fiducials FID1-3 are on the board; add rails + tooling holes as your assembler requires (edge connectors overhang the rear edge by up to 2.5 mm) |

## Assembly notes

- **Side F (component side, "top" in the files)**: all SMT parts. **Side B**: only SW1 (mute slide switch) - place in a second
  pass or hand-solder (6 gull-wing pads).
- THT parts: J6 (stacked USB-A), J7 (JST-PH) - selective/hand solder from side B. J5 (debug header) is **DNP**; C12 (feed-forward
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

1. Without CM4: apply a 9 V-capable PD source. Expect VBUS = 9 V (TP1), VBUS_SW = 9 V (TP2), +5V = 5.10 V +-2 % (TP3),
   green PWR LED on, red PD-FAULT LED off. With a 5 V-only source: TP2 = 0 V, red LED on, no 5 V.
2. Fit the CM4 (+3V3 on TP4 = 3.3 V), boot the test image, check: both USB-A ports enumerate a high-speed device,
   `arecord`/`aplay` loopback through the googlevoicehat card, both microphones (left/right channel), mute switch (red LED on,
   capture goes silent), green/blue LEDs via `/sys/class/leds`, `i2cdetect -y 1` shows 0x08.
3. Flash the radio: the MGM240P ships with a serial bootloader only. Program the EmberZNet NCP (or OpenThread RCP) firmware
   through the Tag-Connect pads J8, or in-system from the CM4 (SWDIO = GPIO22, SWCLK = GPIO23, nRESET = GPIO24; openocd
   `bcm2835gpio` or `linuxgpiod` driver). UART: 115200 baud on `/dev/ttyAMA1`, TX = PA05, RX = PA06, optional RTS/CTS = PA08/PA07,
   bootloader strap = PC00 (GPIO25, active low).

## DRC: waived checks

`outputs/drc.rpt` is clean with the following five checks set to "ignore" in the project
(`gen/project_settings.json`). `outputs/drc_waived_checks_enabled.rpt` shows what they would report: 10 warnings, 0 errors.

| Check | Count | Why it is waived |
|---|---|---|
| `silk_edge_clearance` | 4 | Library silkscreen of the edge connectors (USB-C, USB-A, microSD) reaches the board edge by design; it is cut off at the outline. |
| `silk_over_copper` | 2 | Library silkscreen lines over exposed pads; the Gerbers are plotted with silkscreen subtracted from mask openings, so nothing is printed on pads. |
| `silk_overlap` | 2 | Overlapping silkscreen of neighbouring parts (cosmetic). Reference designators are on the F.Fab layer, not on silk. |
| `footprint_type_mismatch` | 1 | U2 uses KiCad's `...HSOP-8-1EP..._ThermalVias` footprint: an SMD part whose exposed pad contains plated thermal vias, which KiCad classifies as "through hole". Intentional. |
| `lib_footprint_mismatch` | 1 | The board copies of the footprints point their 3D models to `hardware/3dmodels` instead of the KiCad installation, so they differ from the library by design (the KiCad Docker image ships without 3D models). |

Board rules deliberately relaxed from KiCad's defaults (all within standard 4-layer fab capability): minimum hole 0.2 mm,
copper-to-edge 0.17 mm (the KiCad reverse-mount LED land pattern has its own pads 0.175 mm from its slot), minimum track 0.1 mm,
thermal relief spokes >= 1.

## Known limitations (read before ordering)

- **Autorouted.** The layout is electrically complete and rule-clean, but it is not hand-optimised: return paths, loop areas of the
  buck converter and analogue-quality details were not reviewed by a human layout engineer. The buck's input/output capacitors and
  inductor are adjacent to the IC and tied together with pours and plane vias, which covers the essentials.
- **USB 2.0 pairs are loosely coupled, not true differential pairs** (see stack-up note). Lengths and skew are listed in
  `outputs/routing_stats.txt`: 16-32 mm long, intra-pair skew 1.2 mm (upstream), 4.6 mm (port 1) and 2.4 mm (port 2), i.e. at most
  ~30 ps against a 2083 ps bit time. The usual layout guideline is <= 3.8 mm (150 mil), which port 1 misses slightly. Expect them to
  work at high speed, but verify with a USB 2.0 high-speed device and, ideally, an eye-diagram test on the first prototypes.
- SD card lines are 58-72 mm long with up to 13 mm mismatch: fine for 50 MHz high-speed mode; UHS-I SDR104 is not guaranteed.
- Mechanical dimensions of three parts (USB-A overhang, slide switch height, speaker) and the CM4 antenna corner are assumptions -
  see DECISIONS.md "Open items".
- No hardware has been built or measured.
