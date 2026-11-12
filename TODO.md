# Progress checklist

Legend: [x] done and verified - [~] done with a documented limitation - [ ] open

## Two devices: hub and satellite (fourth session, 2026-11-12)

Rules: PCB, BOM and JLCPCB order package unchanged; only software, documentation and the shopping list change.

Assistant architecture
- [x] Decision: Home Assistant's Assist pipeline with the official Anthropic integration for both devices; the
      VoxHub Assistant add-on is not extended (DECISIONS.md S-1 to S-5)
- [x] Exposure guard for locks and alarm panels (`assistant/voxhub_satellite/app/voxhub_satellite/guard.py`), also
      reading every script's configuration; unit tests against a fake Home Assistant websocket
- [x] Hub add-on "VoxHub Satellite": launcher, LED / mute bridge, guard; Linux Voice Assistant on 127.0.0.1 only;
      51 unit tests; image built from the official LVA image and run in a container against PulseAudio and a real
      ESPHome API client (7 / 7 checks, gain unchanged after a restart)
- [x] Assistant documentation (add-on DOCS.md, `assistant/README.md`)
- [~] Not run on Home Assistant OS or on the board (no hardware): Supervisor audio, LEDs, mute switch, discovery

Satellite image (`/os/satellite`)
- [x] Build script for a Raspberry Pi OS Lite 64-bit image with LVA, the VoxHub overlay block, LEDs / mute,
      Wi-Fi and hub address at build time, discovery, automatic security updates; checks of the finished image
- [x] Runtime test of a built image (`test-satellite-image.sh`): PipeWire, launcher, LVA and the bridge inside the
      emulated image, driven by an ESPHome API client; 7 / 7 on the first build's image
- [ ] Image built once with all checks passing, runtime test on that image, `lva-constraints.txt` committed,
      `os/README.md` section "Satellite image: verification"
- [ ] Boot on the board (no hardware)

Zigbee radio
- [x] `tools/flash_zigbee.sh --role hub|satellite` (coordinator / router 20250403), router check over the
      programmed ranges, `--rejoin` (refused without router firmware), refusal on Home Assistant OS, local copies
- [x] Radio simulator (writes its NV area like the real firmware) and test runner (`tools/test/`)
- [ ] Router firmware on real hardware (no board exists)

Shopping list and documentation
- [x] `fab/SHOPPING_LIST.md`, section 8: satellite variant (CM4101000 1 GB, Reichelt.at 50.82 EUR; 32 GB card) and
      combined basket hub + satellite, two parcels to Austria, 286.90 EUR (prices read 2026-11-12)
- [x] `fab/ASSEMBLY_AND_TEST.md`, chapter 7: hub / satellite setup, pairing, room assignment, Zigbee router, tests
      from both rooms, results table, troubleshooting
- [x] README.md, os/README.md, os/satellite/README.md, assistant/README.md updated
- [x] Independent review (three reviewers): 4 high, 7 medium, 13 low findings, all fixed or documented
      (DECISIONS.md S-33 to S-40)

## Revision A2: orderable at JLCPCB (third session, 2026-11-12)

Parts
- [x] Every BOM line looked up live in JLCPCB's assembly library and at LCSC: LCSC number, library type, stock, price
      (`hardware/gen/sourcing_jlc.json`, `hardware/outputs/bom.csv`); DigiKey columns kept as the second source
- [x] Out-of-stock and thin parts replaced without lowering a rating: radio module (MGM240P -> RF-BM-2652P2), inductor,
      polymer capacitors, 22 uF and 1 uF capacitors, crystal + load capacitors, Zener, status LEDs, resistors
- [x] LMR33640ADDAR, TPS2553DBVR, 2N7002, 10 uF X7R 1206, 220 nF C10: in stock at JLCPCB under the same part number
- [~] Three lines below 200 pieces at JLCPCB with no better-stocked equal part: ADAU7002ACBZ-R7 (104), 61400826021 (116),
      RF-BM-2652P2 (126) - reserve them first (`fab/ORDER_GUIDE.md`)
- [~] Radio module rated -40..+85 C (the MGM240P was +105 C): no stocked module reaches 105 C
- [x] Extended parts named with the reason (DECISIONS.md A2-9); in Standard PCBA they cost the same as Basic parts
- [x] Nine data sheets requested again from the manufacturers: two served (Hirose), seven still refuse scripts and
      were read from distributor copies; differences noted (DECISIONS.md, A2 log)

Layout
- [x] PGND of the buck tied to the exposed pad on the component side, own ground vias for PGND and every input / output capacitor
- [x] Feed from the load switch and the VBUS necks widened to 1.2 - 1.6 mm; every high-current path measured by
      `gen/check_power.py` (`hardware/outputs/power_paths.txt`), gate in the build
- [x] No via in or touching a lead pad (U1 pin 19 and U10 pin 7 fixed by rule, not by hand)
- [x] URL text clear of C17; silkscreen legends placed by a search; all silkscreen checks are errors: 0 overlaps
- [x] USB: upstream pair routed as a real coupled pair (0.14 / 0.16 mm); downstream lines kept as matched 45 ohm lines,
      with the reason (DECISIONS.md A2-22); skew 0.00 / 0.00 / 0.00 mm, no vias, no stubs
- [x] Stack-up JLC04161H-3313 (offered by JLCPCB at no charge); width and gap from JLCPCB's impedance calculator:
      89.96 ohm differential (`hardware/outputs/usb_impedance.txt`)
- [x] ERC 0 / DRC 0 with JLCPCB's design rules (`gen/project_settings.json`, `hardware/voxhub.kicad_dru`)
- [x] Found on the way: Hirose's restricted strips at the CM4 sockets kept free of foreign copper (gate
      `gen/check_df40.py`), 81 % paste aperture on the socket pads, boot-strap pull-up 2.2k
- [x] Found by the review: hub decoupling at the pins, crystal lines, antenna pocket keep-out, no via in a pad (gate
      `gen/check_vias.py`), no 20 V test pads, copper 0.45 mm from the edge
- [x] Independent review of the changed areas, round 1: six reviewers, no high finding, 10 medium and 30 low, all
      fixed or accepted with a reason (DECISIONS.md A2-36 to A2-48)
- [x] Review round 2 (last round): all fixes confirmed by the reviewers' own measurements; no high or medium finding;
      the new low findings fixed or accepted with a reason (DECISIONS.md A2-49 to A2-54)

JLCPCB order package (`/fab`)
- [x] `fab/jlcpcb/gerbers.zip`, `bom_jlcpcb.csv` (one row per LCSC number), `cpl_jlcpcb.csv`; rotations fitted to JLCPCB's
      own footprints and listed per part in `placement_report.csv` (135 of 136 placements; the last is the hand-soldered
      USB-A); confirmed by an independent re-computation in the review
- [x] Everything machine- or hand-assembled by JLCPCB: SW1 and the three status LEDs on side B (Standard PCBA, both
      sides), J6 and J7 as hand-soldered THT parts, no reverse-mount parts left
- [x] `fab/ORDER_GUIDE.md`: every option of the order form, remarks to paste, placement check, cost estimate
- [x] `fab/SHOPPING_LIST.md`: EU shops, article numbers, prices, baskets with shipping to Austria
- [x] `fab/ASSEMBLY_AND_TEST.md`: print settings, bring-up tests, assembly, radio flashing
- [x] `tools/flash_zigbee.sh`: one command flashes the Zigbee coordinator firmware from the CM4 (ROM serial boot
      loader, JTAG fallback)
- [~] the flashing script ran end to end against a simulated radio only (author's runs and the reviewer's 20 cases)
- [~] JLCPCB's pages behind the login (BOM / CPL matching, placement preview, final price) could not be opened; the
      guide describes them from JLCPCB's help articles

Final outputs
- [x] Gerbers, drill, BOM, CPL, STEP, renders regenerated from the final board
- [x] Enclosure regenerated: speaker pocket for the Adafruit 3351 (JST-PH plug, no soldering), 14 x 14 x 7 mm heat sink
- [~] Showcase video and exploded still NOT re-rendered for A2 (skipped on the owner's decision); they show revision
      A1. `media/build_showcase.sh` renders them from the A2 files when wanted (about 3 hours)

## Hardware (`/hardware`), revision A1 (history)
- [x] Architecture + part selection (CM4 Lite SoM, see DECISIONS.md)
- [x] Schematic generated from code (`hardware/gen/design.py`), 6 sheets
- [x] ERC: 0 errors, 0 warnings (`hardware/outputs/erc.rpt`)
- [x] Netlist cross-check: 151 components / 99 nets, schematic parity 0 issues
- [x] Project footprints (CM4 socket, MGM240P, ADAU7002) generated + cross-checked
- [x] Placement (scripted; the buck power stage and the USB ESD parts are placed by hand) and power fan-out (scripted)
- [x] Routing: Freerouting 2.0.1 + scripted patch router / repair loop (new autorouter session after the review fixes)
- [x] DRC: 0 violations, 0 unconnected, 0 parity issues; 5 waived cosmetic checks (10 warnings) documented (`hardware/README.md`)
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
      hand-reviewed. Buck: power stage placed by hand, input capacitors in one pour with VIN, but the feed from the
      load switch to that pour is a single 0.4 mm track (19 mm, two vias) - widen before production
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
- [x] **`build-image.sh full` ran to the end** (host build, ninth attempt): `haos_voxhub-cm4-18.5-full.img.xz` (317 MiB)
      and the OTA bundle built; image inspected (partitions, `voxhub.dtbo` applies, kernel modules, containers).
      Where and why attempts 1-8 stopped is in `os/README.md`
- [~] the Docker path of the full build (HAOS builder container) was not run in the sandbox
- [ ] Boot test on hardware

## Showcase (`/media`)
- [x] STEP -> GLB conversion, board textures from KiCad plots, Blender scene / animation script
- [x] `voxhub_showcase.mp4` (H.264, 1920 x 1080, 60 fps, 21 s, 1260 frames, BT.709) + `voxhub_exploded.png` rendered
      (Blender 4.5.16 headless, Cycles CPU, 3 h 10 min) and checked frame by frame on a contact sheet
- [x] Build script hardened after the review: tool check up front, Blender exit code, complete-frame check, colour tags
- [x] `voxhub_exploded.png` re-rendered from the final board (after the USB / buck layout fixes)
- [x] `voxhub_showcase.mp4` re-rendered from the final board: the 866 frames that show the PCB (150-1015) are new, the
      394 closed-device frames are kept (printed parts unchanged); probed (1260 frames, 60 fps, 21 s, BT.709), checked on a
      contact sheet and for a jump at the two joins (none)

## Assistant (`/assistant`)
- [x] Home Assistant add-on (wake word -> STT -> Claude tool use -> TTS)
- [x] 86 unit tests passing, ruff clean
- [x] LED names / mute-switch detection aligned with the OS configuration (stock and custom overlay)
- [~] Not built as a Docker image / not run on hardware

## Review (second session)
- [x] Independent review of all revision A1 deliverables: 5 reviewers + 5 verifiers, 51 findings, 48 confirmed
- [x] All confirmed findings fixed or documented (DECISIONS.md log no. 17-27); the USB result was re-verified with the
      reviewers' own scripts on the new board
- [x] Second round on the fixes (4 re-checkers + 4 verifiers): 47 of 48 fixed and one partly, USB confirmed a third time, 17 new findings
      confirmed and fixed - the one that mattered: the buck input capacitor C8 had lost its pour (log no. 28, 29)

- [x] Third, focused round on the power-stage change (3 + 3): split pour gone, USB confirmed with a fourth parser,
      12 low findings - texts and scripts fixed, board items documented (log no. 30)
- [x] Before a production spin: tie PGND to the exposed pad / own vias, widen the 0.4 mm feed from the load switch
      and the VBUS necks, move two fan-out vias out of QFN lead pads (U1 pin 19, U10 pin 7), move the URL text clear
      of C17 - all done in revision A2 (above)

## Documentation
- [x] DECISIONS.md (decision log of revision A1, datasheet verification table, sourcing decisions, open items)
- [x] README.md (overview, block diagram, power budget, thermal estimate, cost summary, build instructions)
- [x] hardware/README.md, enclosure/README.md, os/README.md, assistant/README.md, media/README.md
