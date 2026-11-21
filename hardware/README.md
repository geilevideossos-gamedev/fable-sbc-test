# Hardware: VoxHub CM4 carrier, revision A3

KiCad 10 project (native KiCad 10 files, written with KiCad 10.0.8), **generated entirely from code** (`gen/`). The
project opens in KiCad 10 and can be inspected and edited there, but `./build.sh all` writes the schematic, the
project libraries, the board and the project file again: for anything that is to stay, change the generator and run
`./build.sh`. What may be edited by hand and what is overwritten is in
[Opening and editing in KiCad 10](#opening-and-editing-in-kicad-10).

Revision A3 is the revision that is ordered fully assembled from JLCPCB. The order files are in
[`../fab/jlcpcb/`](../fab/jlcpcb), the ordering steps in [`../fab/ORDER_GUIDE.md`](../fab/ORDER_GUIDE.md). Against
revision A2 the placement, the nets and the routing are the same; values, part numbers, two land patterns and the
toolchain changed. What changed and why is in the A3 log at the top of [`../DECISIONS.md`](../DECISIONS.md) (K-1 to
K-10: KiCad 10, C-1 to C-12: fewer part numbers, N-1 to N-6: findings on the existing design, F-1 to F-5: stock
check), what changed from A1 to A2 in its A2 log.

## Opening and editing in KiCad 10

- Open `voxhub.kicad_pro` with KiCad 10. The project is self-contained: its library tables (`sym-lib-table`,
  `fp-lib-table`) name only the project libraries `voxhub.kicad_sym` and `voxhub.pretty`, every symbol and footprint
  link is `voxhub:<name>`, and every 3D model path points into `3dmodels/`. Nothing is taken from the libraries of the
  KiCad installation (DECISIONS.md, K-3). One model file does not exist: the socket footprints of J2 / J3 name
  `3dmodels/Connector_Hirose_DF40.3dshapes/Hirose_DF40C-100DS-0.4V_2x50_P0.4mm.step`, so the 3D viewer draws these two
  sockets without a body.
- The files are native KiCad 10 files (schematic format 20260306, board and footprints 20260206, symbol library
  20251024). Saving them from both KiCad 10 editors left every tracked file byte-identical, with no conversion notice
  (tested on Linux, K-2). Nothing was tested on Windows itself (K-10); at the first start KiCad shows its own setup
  wizard once. `.gitattributes` keeps the KiCad files and the scripts at LF line endings on a Windows checkout, and
  `.gitignore` covers what KiCad creates beside an opened project (K-9).
- **`build.sh all` overwrites**: `voxhub.kicad_sch` and the five sub-sheets, `voxhub.kicad_sym`, `voxhub.pretty/`
  (emptied and written again), `voxhub.kicad_pcb`, `voxhub.kicad_pro` (a copy of `gen/project_settings.json`),
  `gen/model_netlist.json`, `gen/placement.json`, everything in `outputs/` except `usb_impedance.txt`, and
  `../fab/jlcpcb/`. A manual edit of the schematic or the board survives only until the next `build.sh all`.
- **`build.sh outputs` works on the board as it is on disk**: it runs the DRC (with schematic parity against the
  schematic on disk) and writes Gerbers, drill files, positions, renders and the JLCPCB BOM and CPL from that board.
  It does not generate schematic or board. Two things it does not take from a manual edit: it puts
  `gen/project_settings.json` back as `voxhub.kicad_pro`, so board rules, net classes and severities changed in
  KiCad's dialogs are lost unless they are copied into that file, and it writes `outputs/bom.csv` and
  `outputs/order_cost.*` from `gen/model_netlist.json`, the part list of the last generator run.
- Not written by the build and edited by hand: `voxhub.kicad_dru`, the two library tables,
  `gen/project_settings.json`, `gen/stock/`, `3dmodels/` (`gen/make_3dmodels.py` is run by hand).
- The build needs Docker and a Linux shell (`bash`, `python3`, `zip`). On Windows that means WSL or Git Bash with
  Docker Desktop; neither was tested (K-10).
- **Fabrication files must come from `build.sh`, not from KiCad's Plot dialog.** The plot settings stored in the board
  file are KiCad's defaults: no Protel file extensions, solder mask not subtracted from the silkscreen. The build
  passes its own options on the command line (the Gerber and drill options JLCPCB documents).

## Contents

| Path | What |
|---|---|
| `voxhub.kicad_pro`, `voxhub.kicad_sch` + 5 sub-sheets, `voxhub.kicad_pcb` | the KiCad 10 project (generated) |
| `sym-lib-table`, `fp-lib-table` | project library tables: the only libraries are the two below |
| `voxhub.kicad_dru` | JLCPCB limits that KiCad's board setup cannot express (component holes, pad to pad) |
| `voxhub.kicad_sym`, `voxhub.pretty/` | project symbol / footprint libraries (generated). `voxhub.pretty` holds every footprint of the board (33): 29 copied from `gen/stock`, the two CM4 socket footprints derived from the stock Hirose footprint, the radio module and the WLCSP of the PDM converter |
| `3dmodels/` | STEP models used by the footprints (KiCad library copies + simple stand-ins) |
| `build.sh` | the build (see [Rebuilding](#rebuilding)) |
| `docker/Dockerfile` | the build image `voxhub-kicad:10.0`: the official `kicad/kicad:10.0` image plus `python3-numpy` and `python3-shapely` from the Debian packages |
| `gen/design.py` | **the circuit**: every part, value and net |
| `gen/kisch.py`, `gen/sexpr.py` | schematic writer; `sexpr.py` reproduces KiCad 10's own file layout |
| `gen/stock/` | `stock.kicad_sym` (33 symbols) and `stock.pretty` (30 footprints): the KiCad 9.0.9 library parts the board was designed with, stored in KiCad 10 format. The generators read these and not the libraries of the KiCad installation; a part that is not in here must be added before the generator can use it (K-3) |
| `gen/parts.py` | part catalogue: one entry per purchasable part |
| `gen/jlc_lookup.py`, `gen/sourcing_jlc.json`, `gen/jlc_footprints.json` | live lookups in JLCPCB's assembly library and at LCSC; the stored result (LCSC number, library type, stock, prices and price breaks, minimum and loss quantities, date of the reading); JLCPCB's own footprints of every part |
| `gen/sourcing.py`, `gen/sourcing_live.json`, `gen/make_bom.py` | second sources, DigiKey data of 2026-11-11, system parts with their EU shop, BOM generator |
| `gen/order_cost.py` | parts cost of an order of assembled boards with JLCPCB's minimum quantities, loss quantities and price breaks |
| `gen/make_footprints.py`, `gen/make_3dmodels.py` | project footprint library (the copies from `gen/stock` with two corrected land patterns, and the footprints drawn here) and coloured stand-in models |
| `gen/prewire.py` | **hand-designed copper**: PD input, load switch, buck stage, USB port supplies, all six USB data lines; stack-up and USB geometry |
| `gen/build_pcb.py` | placement, silkscreen legends, pre-wired copper, power fan-out, keep-outs, DSN export, import, patch router, repair, USB length measurement |
| `gen/postroute.sh` | iterate DRC -> repair -> patch until no connection is open and no track or via violates a rule |
| `gen/check_power.py`, `gen/check_df40.py`, `gen/check_vias.py` | build gates: narrowest copper of the high-current paths; foreign copper in the CM4 socket strips; vias in or touching a pad |
| `gen/jlc_impedance.py` | asks JLCPCB's impedance calculator for the USB geometry |
| `gen/make_jlc.py` | JLCPCB BOM, CPL and placement report |
| `gen/project_settings.json` | the project file as the build installs it: board rules, net classes, DRC and ERC severities (see [DRC](#drc-rules-severities-and-waived-checks)) |
| `gen/model_netlist.json` | the circuit as data, written by `design.py`: parts, fields and the net of every pin; source of the BOM |
| `gen/routed/voxhub.ses` | autorouter session (Freerouting 2.0.1) the committed board was built from |
| `gen/placement.json` | final part positions (also drives the enclosure model) |
| `outputs/` | reports and fabrication data (below) |

### `outputs/`

| File | Purpose |
|---|---|
| `voxhub_schematic.pdf` | schematic, 6 pages |
| `erc.rpt`, `drc.rpt` | kicad-cli 10.0.8 reports: **0 ERC violations, 0 DRC violations, 0 unconnected, 0 parity issues** |
| `drc_waived_checks_enabled.rpt` | the same DRC with the two waived checks switched on (4 warnings, explained below) |
| `power_paths.txt` | narrowest copper of every high-current path against its requirement |
| `df40_strips.txt` | copper inside Hirose's restricted strips of the CM4 sockets (own net / other net) |
| `via_in_pad.txt` | vias whose land overlaps an SMD pad (allowed only inside the exposed pad of an IC) |
| `usb_impedance.txt` | USB track geometry in JLCPCB's impedance calculator (asked on 2026-11-12; the geometry is unchanged) |
| `routing_stats.txt` | track / via counts; USB lines: pad-to-pad length and skew, the pads each line runs through, copper that is not on that path; SD / I2S / PDM lengths |
| `gerbers/` + `voxhub_gerbers.zip` | Gerbers with Protel extensions: F / In1 / In2 / B copper, mask, paste, silk, Edge.Cuts; Excellon PTH + NPTH drill, drill maps, job file (`../fab/jlcpcb/gerbers.zip` is the same set without maps and job file) |
| `voxhub_pos.csv` | pick-and-place as KiCad exports it (both sides, DNP parts excluded); for JLCPCB use `../fab/jlcpcb/cpl_jlcpcb.csv` |
| `bom.csv`, `bom_summary.json` | PCB assembly BOM, 44 lines + 2 not populated: MPN, LCSC number, JLCPCB library type, JLCPCB and LCSC stock, JLCPCB prices at 1 / 10 / 100 (live, 2026-11-21), DigiKey second source (2026-11-11), other alternates |
| `order_cost.csv`, `order_cost.json` | parts of an order of 2 assembled boards: per part type whether it is placed by machine or by hand, the quantity needed, JLCPCB's minimum and loss quantity, the resulting quantity, its unit price and the line total. Summary: 44 part types (42 machine-placed, 2 hand-soldered); 79.49 USD for the parts needed, 83.02 USD with the minimum quantities, 84.78 USD with minimum and loss quantities (the rounded lines of the CSV add up to 84.76). A calculation from JLCPCB's parts data, not a quote |
| `bom_system.csv` | module, speaker, heat sink, screws, SD card, charger with EU shop and price (read 2026-11-20) |
| `voxhub_outline.dxf`, `mechanical_positions.csv` | mechanical outline: board edge, mounting holes, CM4 holes / outline, microphone ports, connector envelopes |
| `voxhub_pcb.step` | 3D model of the assembled board |
| `pcb_layers/voxhub.pdf` | layer plots |
| `render_top.png`, `render_bottom.png`, `render_iso.png` | kicad-cli 3D renders |

![top](outputs/render_top.png)

## Rebuilding

```bash
SKIP_ROUTE=1 hardware/build.sh all         # schematic -> ERC -> netlist -> place -> import -> patch -> DRC -> outputs -> fab/jlcpcb
                                           # the first run builds the Docker image voxhub-kicad:10.0 (KiCad 10.0.8 was used)
# only for a fresh autoroute (Java >= 21); not run under KiCad 10, see below:
wget -P hardware https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar
hardware/build.sh all                      # same, but runs the autorouter first
```

Single steps: `hardware/build.sh sch | pcb | route | outputs`.

| Environment variable | Meaning |
|---|---|
| `KICAD_IMAGE` | Docker image with KiCad 10, numpy and shapely. Default `voxhub-kicad:10.0`; when the variable is not set and that image does not exist, the build creates it with `docker build -t voxhub-kicad:10.0 hardware/docker`. An image named in the variable is used as it is and never built |
| `KICAD_NATIVE=1` | use `kicad-cli` and `pcbnew` of the host instead of Docker. `kicad-cli version` must report 10.x, otherwise the build stops. The build picks the first of `$KICAD_PYTHON`, `python3`, `python3.13`, `python3.12` that imports `pcbnew`, `numpy` and `shapely`, and takes KiCad's library table templates from `/usr/share/kicad/template/` |
| `FREEROUTING` | path of the Freerouting jar (default `hardware/freerouting-2.0.1.jar`); only read when the autorouter runs |
| `SKIP_ROUTE=1` | re-use the committed autorouter session `gen/routed/voxhub.ses` |

The host needs `bash`, `python3` and `zip` (the BOM and the archives are made on the host; the script checks for `zip`
first), and `docker` unless `KICAD_NATIVE=1` is set. The official KiCad 10 image has the `pcbnew` Python module but
neither numpy nor shapely nor pip, which is why the project image exists (K-1). KiCad 9 is no longer supported: the
generators write KiCad 10 files and use the KiCad 10 API only.

`SKIP_ROUTE=1` re-uses the committed autorouter session and gives the same copper as the committed board (the patch
router is deterministic). The board file and the Gerbers are not byte-identical from run to run, because KiCad
writes items in the order of new random identifiers; the A3 board was compared with the A2 board geometrically (K-7).
A fresh autoroute was not run under KiCad 10 (K-10): KiCad 10 writes the Specctra DSN file differently, so a new
session can differ from the committed one, and a board routed from it would be a new layout that needs the whole
verification again. Under KiCad 9, Freerouting 2.0.1 with one thread produced the same session in every run, which
was not guaranteed on another machine or JRE either. Two quirks the build works around: Freerouting sometimes exits
with an empty session file after routing (the build starts it up to three times and checks the file), and it keeps a
`freerouting.json` in the temp directory (each run gets its own).

Scripts that are run by hand (from `hardware/`):

| Command | What it does |
|---|---|
| `python3 gen/jlc_lookup.py refresh gen/sourcing_jlc.json` | reads every BOM line live from JLCPCB and LCSC and stores stock, library type, prices at 1 / 10 / 100 and all price breaks, minimum order quantity, loss quantity, assembly process and the date of the reading |
| `python3 gen/jlc_lookup.py footprints gen/sourcing_jlc.json gen/jlc_footprints.json` | fetches JLCPCB's footprint of every LCSC part (needed after a part change) |
| `python3 gen/jlc_lookup.py search "<keyword>"`, `... code C12345` | search the assembly library; full record of one part |
| `python3 gen/make_bom.py gen/model_netlist.json outputs` | `bom.csv`, `bom_summary.json`, `bom_system.csv` (run by `build.sh outputs`) |
| `python3 gen/order_cost.py gen/model_netlist.json gen/sourcing_jlc.json outputs 2` | `order_cost.csv` and `order_cost.json` for 2 assembled boards (run by `build.sh outputs`) |
| `python3 gen/jlc_impedance.py outputs/usb_impedance.txt` | USB geometry of `prewire.py` in JLCPCB's impedance calculator |
| `python3 gen/check_power.py voxhub.kicad_pcb outputs/power_paths.txt` | current-path widths (run by `build.sh outputs`; needs `pcbnew` and `shapely`, like the next three) |
| `python3 gen/check_df40.py voxhub.kicad_pcb outputs/df40_strips.txt` | CM4 socket strips (run by `build.sh outputs`) |
| `python3 gen/check_vias.py voxhub.kicad_pcb outputs/via_in_pad.txt` | vias against pads (run by `build.sh outputs`) |
| `python3 gen/make_jlc.py voxhub.kicad_pcb gen/sourcing_jlc.json gen/jlc_footprints.json ../fab/jlcpcb` | JLCPCB BOM, CPL, placement report (run by `build.sh outputs`) |
| `python3 gen/make_3dmodels.py 3dmodels` | coloured stand-in STEP models (needs `cadquery`; not run by the build) |

How the board is produced:

1. `design.py` writes the schematic, the project symbol library (stock symbols come from `gen/stock/stock.kicad_sym`)
   and the circuit as data (`gen/model_netlist.json`); `make_footprints.py` writes `voxhub.pretty` (stock footprints
   from `gen/stock/stock.pretty`); `kicad-cli sch erc` must pass; KiCad's netlist of the schematic is exported and the
   board is built from that netlist. For revision A3 the netlist was compared pin by pin with `model_netlist.json`
   (150 components, 100 nets, 512 connected pins, no difference); this comparison is not a step of `build.sh`.
2. `build_pcb.py place`: fixed positions for connectors / ICs / mechanics and for the hand-placed power stage and USB parts,
   a greedy "nearest free spot to the pad it talks to" placer for the other passives; outline; keep-outs; silkscreen
   legends by an occupancy search; then the **pre-wired copper of `prewire.py`** (locked), the scripted fan-out of the
   remaining GND / +5V pads to the inner planes (never a via in or touching a lead pad), the fixed escape pattern of the
   WLCSP and the keep-out areas in the restricted strips of the CM4 sockets. The USB line lengths are measured and the
   lines locked.
3. Freerouting 2.0.1 routes the remaining signals on F.Cu / B.Cu (planes are declared as power layers; locked copper is fixed wiring).
4. `build_pcb.py finish`: import, track ends that miss the centre of a via of their net by less than 0.001 mm are moved
   onto it (K-5), tracks narrower than 0.1 mm are widened to 0.1 mm, GND and +5V planes, GND pours on both outer layers.
5. `postroute.sh`: the patch router (A* on a 0.05 mm grid with rip-up) joins whatever is still open and a DRC-driven
   repair removes offending tracks and vias, until `kicad-cli pcb drc` shows no open connection and no violation that
   names a track or a via. A violation between pads alone cannot be repaired by this step and is left to the final DRC
   (K-8). Locked copper is never touched.
6. `build.sh outputs`: the DRC gates everything; Gerbers, drill, STEP, renders; `stats` fails if a USB pair is more than
   3.8 mm apart or cannot be measured; `check_power.py`, `check_df40.py` and `check_vias.py` fail on a narrow current
   path, on foreign copper in the socket strips or on a via that touches a lead pad; BOM and order cost; `make_jlc.py`
   fails if a rotation fit does not match.

## Fabrication notes

| Parameter | Value |
|---|---|
| Size | 100.0 x 74.0 mm, 3 mm corner radius, 1.6 mm, FR-4 |
| Layers | 4: F.Cu signal + GND pour / In1.Cu GND plane / In2.Cu +5 V plane / B.Cu signal + GND pour |
| Stack-up | **JLCPCB JLC04161H-3313**: 35 um copper / 0.0994 mm prepreg 3313 / 15.2 um copper / 1.265 mm core / 15.2 um copper / 0.0994 mm prepreg / 35 um copper (written into the board file) |
| USB 2.0 lines | upstream pair 0.14 mm wide, 0.16 mm gap: 89.96 ohm differential in JLCPCB's calculator; downstream lines 0.185 mm: 45.2 ohm each (`outputs/usb_impedance.txt`). With the 7628 default stack-up the same copper would be far off |
| Min. track / space | on the board: 0.12 mm track (patch-router fallback), 0.14 mm USB pair, 0.15 mm signals; net-class clearance 0.12 / 0.15 mm, 0.20 mm for the nets that carry the charger voltage (VBUS, VBUS_SW, PD_GATE, PD_FET_EN). Board rules = JLCPCB limits: 0.09 / 0.09 mm |
| Vias | 286, through, 0.5 mm pad / 0.3 mm drill (signal) and 0.6 / 0.3 mm (power) - JLCPCB's free "0.3 mm / 0.45 mm" class. With the 8 thermal holes of the U2 footprint the board has 294 holes of 0.30 mm |
| Via covering | covered by solder mask on both sides in the Gerbers, except where a via lies in the mask opening of an exposed pad. Order "Epoxy Filled & Capped": the thermal vias inside the exposed pads would otherwise stay open. The free option "Plugged" was worked out for revision A3 and not adopted: JLCPCB never plugs a via in a pad, moving the vias out of the pads makes the regulator and the amplifier hotter (model: +2.9 to +5.5 K at the theoretical peak, +13 K at continuous full power), and the hub and the PD controller would need solder mask strips under their packages (DECISIONS.md, C-11) |
| Via-in-pad | only in exposed pads: U1 (2), U2 (eight, part of the KiCad footprint), U4 (2), U10 (1). No via lies in or touches any other pad (`outputs/via_in_pad.txt`) |
| Plated slots | 4 x 0.6 mm wide (1.4 and 1.7 mm long), shell stakes of the USB-C connector J1 |
| Non-plated holes | 2 x 0.8 mm (microphone ports), 2 x 0.65 mm (J1 locating pegs), 3 x 0.99 mm (Tag-Connect J8), 4 x 2.7 mm (mounting), 4 x 3.7 mm (SMT spacers). No non-plated slots |
| Land patterns corrected in A3 | two, so that no copper is closer than 0.2 mm to a non-plated hole of its own part (K-6): the ring land of the SMT spacers H5-H8 runs from 2.10 to 3.00 mm radius (A2: from 1.85 mm, touching the 3.7 mm hole; now 0.25 mm from it), and the outer contacts A1 / B12 / A12 / B1 of J1 are 1.11 mm long (A2: 1.15 mm; now 0.21 mm from the 0.65 mm peg holes, pad centres unchanged). The spacer keeps 82 % of its land area and its paste apertures. JLCPCB removes copper closer than 0.2 mm to a non-plated hole in its own data preparation, so the delivered boards are the same either way |
| Finish | **ENIG** (0.22 mm pads of the 0.4 mm pitch WLCSP, 0.4 mm pitch mezzanine connectors) |
| Mask / silk | green / white; silkscreen is clipped by the mask openings (`--subtract-soldermask`); smallest text 1.0 mm; revision text "VoxHub CM4  rev A3" on the component side and "VoxHub CM4 rev A3 - this side faces the top cover" on the other |
| Copper to board edge | >= 0.45 mm for tracks, vias and pours, along the straight edges and around the rounded corners (edge connectors' own pads excepted: the shield pads of J4 are 0.37 mm from the rear edge). JLCPCB limits: 0.2 mm at a routed edge, 0.4 mm at a V-cut edge |
| Keep-outs | no copper on any layer under the antenna of the radio module (11.75..31.25 x 68.0..74.0) and under the copper-free pocket beside its open end (21.0..31.25 x 64.0..68.0), and under the CM4 antenna (91..100 x 44.5..59.5: the 6.5 x 11 mm "Wireless Cutout" of CM4 datasheet fig. 4 enlarged to the recommended 8 x 15 mm and out to the board edge); no foreign copper on the component side in the strips 0.75..1.19 mm from the centre line of each CM4 socket; no foreign tracks or vias in the two free channels between the lead ring and the exposed pad of the hub U4 (only GND and the hand-designed 3.3 V links run there) |
| Impedance control | not ordered: the stack-up is specified and the geometry comes from JLCPCB's calculator |
| Panel | fiducials FID1-3 are on the board; JLCPCB adds edge rails and its own fiducials. Ask for the rails on the two 74 mm edges: J6 overhangs the rear 100 mm edge by about 2.5 mm, J1 ends flush with it, the radio module ends flush with the front edge and small parts sit 1 to 2 mm from it |

## Assembly notes

- **Side F (component side, "Top" in the files)**: all other parts. **Side B ("Bottom", faces the top cover of the
  enclosure)**: SW1 (mute slide switch) and the status LEDs D7 (green), D8 (blue), D9 (red).
- THT parts: J6 (stacked USB-A) and J7 (JST-PH, speaker) - JLCPCB solders them by hand. J5 (debug header) and C13
  (feed-forward capacitor) are **not populated** and are in neither the BOM nor the CPL.
- J6 is the Jing Extension 907-112A1022D10200 (C29780026) since revision A3; the Wurth 61400826021 is the alternate.
  The footprint is still the one drawn for the Wurth part: the pins match, the front shell stakes of the Jing part sit
  0.12 mm further forward and clear the smallest drilled hole by 0.08 mm. Its drawing states no temperature range, and
  four of its dimensions are scaled from the drawing, not dimensioned (DECISIONS.md, F-2).
- U4 is ordered as USB2514BT-I/M2 (C510949), the tape-and-reel ordering code of the same device (F-1).
- U9 ADAU7002: WLCSP-8, 0.4 mm pitch, NSMD pads 0.22 mm - X-ray is part of JLCPCB's Standard PCBA for such parts.
- U11 (radio module, MSL 3, at most two reflow passes) and J2 / J3 (0.4 mm mezzanine sockets): reflow only. J2 / J3
  define the CM4 position together with the four SMT spacers H5-H8. The paste layer has 81 % apertures on the socket pads.
- MK1 / MK2 are Infineon IM72D128V01 (C5119248) since revision A3: same footprint and pin-out as the IM69D130V01 of
  A2, which is the alternate (F-3). Bottom-port MEMS microphones: **no washing, no ultrasonic or dry-ice cleaning**
  after reflow; the silkscreen on side B says "MIC - NO WASH" next to both sound holes, and the order remark repeats
  it. C43 / C44 at their supply pins are 1 uF 25 V X5R 0402 (the data sheet of the new microphone asks for 1 uF).
- H5-H8: Wurth 9774015151R SMT spacers (reflow). The CM4 is then fixed with 4 x M2.5 x 5 mm screws.
- LEDs, all Hubei KENTO 0603: red KT-0603R (D4, D9), green KT-0603G (D6, D7, D10), blue KT-0603B (D8). JLCPCB's
  footprint of the red LED (C2286) numbers its pads the other way round (pad 1 = anode); `make_jlc.py` fits it by
  pin name, and the placement report says "terminals swapped by pin name" for D4 and D9 (C-6).
- Polarised parts: C38, C41 (polymer tantalum), D1 (TVS, cathode to VBUS), D5 (Zener, cathode to VBUS), LEDs - all
  checked pad by pad against JLCPCB's footprints in `../fab/jlcpcb/placement_report.csv` (136 of 136 placements "ok").
- JP1 (solder jumper, open by default): only for USB boot of a CM4 with eMMC; never needed with the Lite module.
- Test pads on side F, labelled on the silkscreen: +5V, +3V3, GND (around x 84, y 10 mm from the rear-left corner). There is
  no test pad for the charger voltage on purpose: VBUS is measured on the cathode pad of D1, VBUS_SW on C8 / C9.
- Pick-and-place for JLCPCB: `../fab/jlcpcb/cpl_jlcpcb.csv` (JLCPCB's rotation convention and footprint centres).
  `outputs/voxhub_pos.csv` is the plain KiCad export for any other assembler.

Programming and test of an assembled board: [`../fab/ASSEMBLY_AND_TEST.md`](../fab/ASSEMBLY_AND_TEST.md). The radio
module is flashed from the CM4 with [`../tools/flash_zigbee.sh`](../tools/flash_zigbee.sh) (ROM serial boot loader on
UART4, strap GPIO25, reset GPIO24 - **high = reset**; OpenOCD JTAG on GPIO22 / 23 / 17 / 7 as the fallback,
`../tools/voxhub-cc2652-jtag.cfg`).

## DRC: rules, severities and waived checks

The board rules in `gen/project_settings.json` are JLCPCB's limits as published on 2026-11-12, the net classes are
stricter. `voxhub.kicad_dru` adds what the board setup cannot express:

| Rule | Limit |
|---|---|
| component hole to component hole | 0.45 mm |
| component hole to copper of another net | 0.28 mm (0.30 mm on inner layers) |
| annular ring of component holes | 0.15 mm |
| non-plated hole | >= 0.5 mm |
| pad to pad of different nets | 0.15 mm |
| (board setup) track / space, via pad / drill, via ring, hole to hole, hole to copper, copper to edge | 0.09 / 0.09 mm, 0.45 / 0.3 mm, 0.075 mm, 0.2 mm, 0.2 mm, 0.2 mm |
| (board setup) silkscreen line / text height / distance to pads | 0.15 mm / 1.0 mm / 0.15 mm |

KiCad 10 tests the hole-to-copper limit in both directions of a pad pair, which KiCad 9 did not; the two land patterns
that this brought up were corrected in copper, not waived (fabrication notes above, K-6).

**Severities.** `gen/project_settings.json` gives each of KiCad 10's 62 DRC checks a severity:

| Severity | Checks |
|---|---|
| error: 50 | `annular_width`, `clearance`, `connection_width`, `copper_edge_clearance`, `copper_sliver`, `courtyards_overlap`, `creepage`, `diff_pair_gap_out_of_range`, `diff_pair_uncoupled_length_too_long`, `drill_out_of_range`, `footprint`, `footprint_symbol_field_mismatch`, `hole_clearance`, `hole_to_hole`, `holes_co_located`, `invalid_outline`, `isolated_copper`, `item_on_disabled_layer`, `items_not_allowed`, `length_out_of_range`, `malformed_courtyard`, `microvia_drill_out_of_range`, `missing_tuning_profile`, `npth_inside_courtyard`, `padstack`, `pth_inside_courtyard`, `shorting_items`, `silk_edge_clearance`, `silk_over_copper`, `silk_overlap`, `skew_out_of_range`, `solder_mask_bridge`, `starved_thermal`, `text_height`, `text_on_edge_cuts`, `text_thickness`, `through_hole_pad_without_hole`, `too_many_vias`, `track_angle`, `track_dangling`, `track_not_centered_on_via`, `track_on_post_machined_layer`, `track_segment_length`, `track_width`, `tracks_crossing`, `tuning_profile_track_geometries`, `unconnected_items`, `unresolved_variable`, `via_dangling`, `zones_intersect`. 17 of them are "warning" or "ignore" in a new KiCad 10 project and are raised here; the six checks that are new in KiCad 10 are among the 50 (K-5) |
| warning: 7, KiCad's default | the schematic parity checks `duplicate_footprints`, `extra_footprint`, `missing_footprint`, `net_conflict`, `footprint_symbol_mismatch`, and `mirrored_text_on_front_layer`, `nonmirrored_text_on_back_layer` |
| ignore: 3, KiCad's default | `missing_courtyard`, `footprint_filters_mismatch`, `footprint_type_mismatch` |
| ignore: 2, set by this project (KiCad's default: warning) | `lib_footprint_mismatch`, `lib_footprint_issues` |

The build runs the DRC with `--severity-all --exit-code-violations`: errors and warnings are both written to
`outputs/drc.rpt` and either stops the build, so the seven checks at "warning" gate the build like the errors. The
report shows 0 of both. The ERC is run the same way; of its 47 checks 25 are errors, 18 keep KiCad's default "warning"
and 4 its default "ignore" (`footprint_filter`, `four_way_junction`, `simulation_model_issue`, `single_global_label`);
`outputs/erc.rpt` shows 0 errors and 0 warnings.

**Waived checks.** Two of the five ignored checks compare the board with the project library and with the footprint
type. The build runs the DRC a second time with these two at "warning"; `outputs/drc_waived_checks_enabled.rpt` shows
what they report (4 warnings):

| Check | Count | Why it is waived |
|---|---|---|
| `footprint_type_mismatch` | 1 | U2 uses KiCad's `...HSOP-8-1EP..._ThermalVias` footprint: an SMD part whose exposed pad contains plated thermal vias, which KiCad classifies as "through hole". Intentional |
| `lib_footprint_mismatch` | 3 | J4 and J6: the board copies differ from the footprints in `voxhub.pretty` only in silkscreen that the generator removes at the board edge (J4: 9 of 15 silkscreen items left, J6: 4 of 11); C13 is not populated and has no paste apertures. No copper is affected: size, position and drill of every pad of the three equal the library. J1, which was in this list in A2, no longer differs |

The other three ignored checks are not part of that report. In a run with all five at "warning" on a copy of the A3
board (kicad-cli 10.0.8, 2026-11-21, not a build step) `footprint_filters_mismatch` reported 6 footprints whose name
does not match the footprint filter of their symbol (H5-H8, J5, J7), `missing_courtyard` and `lib_footprint_issues`
reported nothing.

## Known limitations (read before ordering)

- **Signals are autorouted.** Power and USB copper are designed by hand and locked; everything else is electrically
  complete and rule-clean but not hand-optimised.
- **Nothing is measured.** The USB impedance is JLCPCB's calculated value for the specified stack-up, without the paid
  impedance test. Verify with a USB 2.0 high-speed device on both ports.
- **The downstream USB lines are two uncoupled 45 ohm lines per port, not a coupled pair** (10.8 and 16.2 mm long; the
  2.0 mm connector pin pitch and the flow-through ESD parts leave no room for a coupled section worth having). The
  upstream pair is coupled for 90 % of its length (28.6 of 31.8 mm). All six lines: no vias, no stubs, skew 0.00 mm.
- SD card lines are 60-111 mm long with up to 51 mm mismatch: fine for 50 MHz high-speed mode (about 0.35 ns against a
  20 ns period); UHS-I SDR104 is not guaranteed.
- Two BOM lines were below 200 pieces at JLCPCB on 2026-11-21 and have no alternate: ADAU7002ACBZ-R7 (63) and
  RF-BM-2652P2 (126); two boards need 2 of each. Reserve them first - see the order guide (DECISIONS.md, F-4).
- Findings on the existing design that revision A3 documents and does not change (DECISIONS.md, N-1 to N-6):
  - N-1: the input capacitors of the port switches U5 / U6 (C37, C40) are 10.9 and 16.7 mm from the IN pins and the
    current-limit resistors R37 / R39 have 14 and 20 mm of track, where TI asks for "as close as possible" and "as
    short as possible". Assessed as low risk; the current limit can be slightly less accurate than the 1.19 to 1.39 A
    computed.
  - N-2: the theoretical peak load cannot be held continuously inside the closed enclosure. The regulator dissipates
    1.34 W (9 V input) to 1.63 W (20 V input) at 3.45 A; a conduction model gives a junction of about 135 to 145 C at
    50 C around the board (rating 125 C), about 95 to 105 C at the realistic maximum of 12 W and about 76 C at typical
    load. With a charger that only offers 9 V the load switch Q1 is the next hot spot. Model results with an assumed
    cooling coefficient: measure the regulator, the inductor and Q1 on the first board.
  - N-3: the power budget was corrected (`../README.md`): about 19.6 W at the connector at the theoretical peak, 9 %
    above an 18 W contract. The advice is unchanged: a charger of 27 W or more.
  - N-4: at 3.45 A the worst-case inductor peak is 4.51 A against a minimum current limit of 4.8 A; at the regulator's
    rated 4 A it would be 5.06 A. The stage is not a guaranteed 4 A supply at 20 V input.
  - N-5: the hub U4 has two vias in its exposed pad, which is its only ground connection; Microchip asks for "multiple
    vias". Two is the minimum reading of that.
  - N-6: the switch-on surge of the load switch (simulated: 7.2 A with the A2 values at a 20 V contract) is removed in
    A3 by C7 = 100 nF (simulated: 3.3 A). A simulation with the typical curve of the transistor, not a measurement.
- New in revision A3 and not tested on hardware: the microphone with SELECT = VDD (MK2, right channel) puts a
  constant level of typically -40 dBFS into its data (F-3). The VoxHub Assistant add-on removes it since version
  0.1.1; the two-device path (Linux Voice Assistant) behaved the same with and without the level in a simulation (W-1).
- The activity LED D10 runs from 3.3 V through 1k: it lights on every board, but its brightness varies about 10 : 1
  between boards (C-6).
- The project was not opened on Windows, the build was not run under WSL or Git Bash, a fresh autoroute was not run
  under KiCad 10, and the image was not built without the layer cache of the build machine (K-10).
- The plug of the speaker (Adafruit 3351) has to be checked on delivery: the maker's data sheet names an XH 2.5 mm plug, the
  shops sell it with the JST-PH 2.0 mm plug that J7 needs.
- No hardware has been built or measured.
