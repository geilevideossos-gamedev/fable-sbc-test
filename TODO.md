# Progress checklist

Legend: [x] done and verified - [~] done with a documented limitation - [ ] open

## Hardware (`/hardware`)
- [x] Architecture + part selection (CM4 Lite SoM, see DECISIONS.md)
- [x] Schematic generated from code (`hardware/gen/design.py`), 6 sheets
- [x] ERC: 0 errors, 0 warnings (`hardware/outputs/erc.rpt`)
- [x] Netlist cross-check: KiCad netlist == code model (every pin)
- [x] Project footprints (CM4 socket, MGM240P, ADAU7002) generated + cross-checked
- [x] Placement (scripted) and power fan-out (scripted)
- [x] Routing: Freerouting 2.0.1 + scripted patch router / repair loop, USB nets re-routed and length-matched
- [x] DRC: 0 violations, 0 unconnected, 0 parity issues; 5 waived cosmetic checks documented (`hardware/README.md`)
- [x] Gerbers, drill, pick-and-place, BOM (57 lines), schematic PDF, DXF + positions CSV, STEP, 3D renders
- [x] Fab + assembly notes (`hardware/README.md`)
- [~] USB data lines are matched single-ended traces, not coupled pairs; layout is autorouted and not hand-reviewed
- [~] Datasheets could not be opened directly; verification sources per part are listed in DECISIONS.md section 9
- [ ] Build and measure a prototype (nothing has been powered on)

## Enclosure (`/enclosure`)
- [x] Parametric CadQuery model driven by the PCB placement file
- [x] STL + 3MF + STEP export, support-free print orientation
- [x] Interference check PCB assembly vs. printed parts = 0 mm^3
- [x] Renders (closed, open, sections)
- [x] Re-generated for the final PCB placement
- [~] Three part dimensions are assumptions (USB-A overhang, slide switch height, speaker) - test print before volume

## OS (`/os`)
- [x] Board definition (meta, defconfig, kernel fragment, overlay package) for the official HAOS build system
- [x] Device tree overlay - compiles and applies to the real HAOS 18.5 CM4 device tree
- [x] `build-image.sh repack`: flashable `haos_voxhub-cm4-18.5.img.xz` built and verified
- [~] `build-image.sh full`: board accepted by Buildroot; build stops at the first source download (network policy) - documented in `os/README.md`
- [x] os/README.md
- [ ] Boot test on hardware

## Assistant (`/assistant`)
- [x] Home Assistant add-on (wake word -> STT -> Claude tool use -> TTS)
- [x] 86 unit tests passing, ruff clean
- [x] LED names / mute-switch detection aligned with the OS configuration (stock and custom overlay)
- [~] Not built as a Docker image / not run on hardware (not possible in the sandbox)

## Documentation
- [x] DECISIONS.md
- [x] README.md (overview, block diagram, power budget, thermal estimate, build instructions)
- [x] hardware/README.md, enclosure/README.md, os/README.md, assistant/README.md
