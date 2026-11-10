# Progress checklist

Legend: [x] done and verified - [~] done with a documented limitation - [ ] open

## Hardware (`/hardware`)
- [x] Architecture + part selection (CM4 Lite SoM, see DECISIONS.md)
- [x] Schematic generated from code (`hardware/gen/design.py`), 6 sheets
- [x] ERC: 0 errors, 0 warnings (`hardware/outputs/erc.rpt`)
- [x] Netlist cross-check: KiCad netlist == code model (every pin)
- [x] Project footprints (CM4 socket, MGM240P, ADAU7002) generated + cross-checked
- [x] Placement (scripted) and power fan-out (scripted)
- [ ] Routing (Freerouting) - in progress
- [ ] DRC: 0 errors, waivers documented
- [ ] Gerbers, drill, pick-and-place, BOM, schematic PDF, DXF, STEP, renders
- [ ] Fab + assembly notes (`hardware/README.md`)

## Enclosure (`/enclosure`)
- [x] Parametric CadQuery model driven by the PCB placement file
- [x] STL + 3MF + STEP export, support-free print orientation
- [x] Interference check PCB assembly vs. printed parts = 0 mm^3
- [x] Renders (closed, open, sections)
- [ ] Re-run after final PCB placement

## OS (`/os`)
- [x] Board definition (meta, defconfig, kernel fragment, overlay package) for the official HAOS build system
- [x] Device tree overlay - compiles and applies to the real HAOS 18.5 CM4 device tree
- [x] `build-image.sh repack`: flashable `haos_voxhub-cm4-18.5.img.xz` built and verified
- [~] `build-image.sh full`: board accepted by Buildroot; build stops at the first source download (network policy) - documented in `os/README.md`
- [ ] os/README.md

## Assistant (`/assistant`)
- [x] Home Assistant add-on (wake word -> STT -> Claude tool use -> TTS)
- [x] 86 unit tests passing, ruff clean
- [~] Not built as a Docker image / not run on hardware (not possible in the sandbox)

## Documentation
- [x] DECISIONS.md
- [ ] README.md (overview, block diagram, power budget, thermal estimate, build instructions)
