# Progress checklist

Legend: [x] done and verified - [~] done with a documented limitation - [ ] open

## Hardware (`/hardware`), revision A1
- [x] Architecture + part selection (CM4 Lite SoM, see DECISIONS.md)
- [x] Schematic generated from code (`hardware/gen/design.py`), 6 sheets
- [x] ERC: 0 errors, 0 warnings (`hardware/outputs/erc.rpt`)
- [x] Netlist cross-check: 151 components / 99 nets, schematic parity 0 issues
- [x] Project footprints (CM4 socket, MGM240P, ADAU7002) generated + cross-checked
- [x] Placement (scripted) and power fan-out (scripted)
- [x] Routing: Freerouting 2.0.1 + scripted patch router / repair loop (new autorouter session after the review fixes)
- [x] DRC: 0 violations, 0 unconnected, 0 parity issues; 5 waived cosmetic checks documented (`hardware/README.md`)
- [x] **USB 2.0 pairs length matched**: flow-through ESD parts (one pad row to the hub, one to the connector), strict
      pad-to-pad routing, serpentines on the shorter line; pad-to-pad skew 0.00 / 0.00 / 0.00 mm (limit 3.8 mm), no vias,
      no stubs - `hardware/outputs/routing_stats.txt`; confirmed by an independent re-computation
  - [x] the first A1 result (0.00 / 1.35 / 0.00) was wrong for port 2 (really 4.9 mm): measurement and layout redone
- [x] **Every IC, module, connector and electromechanical part verified against its datasheet** - DECISIONS.md section 9
      lists source, revision and result per part (25 rows; crystal and 2N7002 added after the review)
  - [~] generic passives, diodes, LEDs, pin header, Tag-Connect pads: KiCad standard footprints, no manufacturer document read
  - [x] CM4 antenna position (datasheet fig. 4): keep-out was in the wrong half, moved to x 91..100 / y 44.5..59.5
  - [x] LMR33640 5 V / 400 kHz table: L 6.8 uH and COUT 4 x 22 uF confirmed; RFBB 24.9k, CIN X7R + 220 nF X7R fixed
  - [x] CYPD3177: strap dividers = datasheet table values; PDO selection behaviour documented; VDDD decoupling fixed
  - [x] MGM240P: antenna keep-out confirmed; RTS / CTS swapped and RESETn driver changed to open drain
  - [x] USB2514B: RESET_N now driven by the CM4 (nEXTRST) as on the CM4IO board
- [x] Gerbers, drill, pick-and-place, BOM (58 lines), schematic PDF, DXF + positions CSV, STEP, 3D renders
- [x] Fab + assembly notes (`hardware/README.md`)
- [x] **Sourcing: every BOM line looked up live at DigiKey** (status, stock, price at 1 and 100); swaps applied where a
      part with the same footprint and equal or better ratings is cheaper or in stock; cost summary in README.md
- [~] One line (220 nF, C10) has status, price and lead time but no stock figure on its DigiKey page
- [~] Mouser: not live - mouser.com blocks automated access; 19 part numbers are search snippets, 18 are only built from
      Mouser's prefix scheme (never seen on the site), 21 lines have none - each BOM line says which
- [~] Five lines at 0 stock at DigiKey: LMR33640ADDAR, 22 uF 1206 and 2N7002 have no in-stock drop-in with equal ratings;
      TPS2553DBVR is in stock as the DBVT reel; the 10 uF X7R 1206 only as a 2,000-piece Marketplace item.
      Thin: MGM240PB32VNA3 (71 pieces). Alternates are named in the BOM
- [~] USB data lines are matched single-ended traces, not coupled pairs; the layout is autorouted and not
      hand-reviewed (buck: only the 220 nF bypass and the VCC capacitor are placed by hand at the regulator pins)
- [~] Nine data sheets were read from mirrors because the manufacturer's server refused the download (listed in
      DECISIONS.md "Open items")
- [ ] Build and measure a prototype (nothing has been powered on)

## Enclosure (`/enclosure`)
- [x] Parametric CadQuery model driven by the PCB placement file
- [x] **Part dimensions from the manufacturer drawings** (Wurth 61400826021, C&K JS202011JCQN, CMS-4017-34SP, USB4105,
      DM3AT, CM4): USB-C / USB-A windows enlarged, speaker relief + ring + pedestal, mute dish, microSD window
- [x] STL + 3MF + STEP export regenerated, support-free print orientation
- [x] Interference check PCB assembly vs. printed parts = 0 mm^3
- [x] Renders regenerated (closed, open, sections)
- [~] Two dimensions are scaled from drawings (USB-A flange lip, speaker terminals) - test print before volume

## OS (`/os`)
- [x] Board definition (meta, defconfig, kernel fragment, overlay package) for the official HAOS build system
- [x] Device tree overlay - compiles and applies to the real HAOS 18.5 CM4 device tree
- [x] `build-image.sh repack`: flashable `haos_voxhub-cm4-18.5.img.xz` built and verified
- [x] `build-image.sh full`: non-root check, host-build cache directories, git fallback for GitHub tarballs,
      optional Go module proxy, host-libyaml on hosts with libyaml-dev
- [~] `build-image.sh full` run: attempt 9 IN PROGRESS at the time of this commit (attempts 1-8: where and why each
      stopped is in `os/README.md`; all 218 packages are built, the image assembly steps remain)
- [ ] Boot test on hardware

## Showcase (`/media`)
- [x] STEP -> GLB conversion, board textures from KiCad plots, Blender scene / animation script
- [x] `voxhub_showcase.mp4` (H.264, 1920 x 1080, 60 fps, 21 s, 1260 frames, BT.709) + `voxhub_exploded.png` rendered
      (Blender 4.5.16 headless, Cycles CPU, 3 h 10 min) and checked frame by frame on a contact sheet
- [x] Build script hardened after the review: tool check up front, Blender exit code, complete-frame check, colour tags
- [x] `voxhub_exploded.png` re-rendered from the final board (after the USB / buck layout fixes)
- [~] `voxhub_showcase.mp4` still shows the board as it was before those fixes (19 small parts moved, tracks changed -
      not discernible at video scale); the 866 frames that show the PCB are being re-rendered at the time of this commit

## Assistant (`/assistant`)
- [x] Home Assistant add-on (wake word -> STT -> Claude tool use -> TTS)
- [x] 86 unit tests passing, ruff clean
- [x] LED names / mute-switch detection aligned with the OS configuration (stock and custom overlay)
- [~] Not built as a Docker image / not run on hardware

## Review (second session)
- [x] Independent review of all revision A1 deliverables: 5 reviewers + 5 verifiers, 51 findings, 47 confirmed
- [x] All confirmed findings fixed or documented (DECISIONS.md log no. 17-25); the USB result was re-verified with the
      reviewers' own scripts on the new board

## Documentation
- [x] DECISIONS.md (decision log of revision A1, datasheet verification table, sourcing decisions, open items)
- [x] README.md (overview, block diagram, power budget, thermal estimate, cost summary, build instructions)
- [x] hardware/README.md, enclosure/README.md, os/README.md, assistant/README.md, media/README.md
