# VoxHub CM4 - a Home Assistant voice hub with Claude inside

A single-board computer for home automation that runs **Home Assistant OS** and works as a
**Claude-based voice assistant**: it listens for a wake word, transcribes the request locally, lets Claude
answer and control the home through tool use, and speaks the reply.

Everything in this repository is generated from code - schematic, PCB, enclosure, OS image and add-on.

| | |
|---|---|
| ![PCB render](hardware/outputs/render_iso.png) | ![Enclosure](enclosure/renders/enclosure_rear.png) |
| carrier with CM4 + heat sink (component side) | enclosure, rear view: USB-C PD in, 2 x USB-A, microSD |

**Showcase animation:** [`media/voxhub_showcase.mp4`](media/voxhub_showcase.mp4) (1080p60, 21 s: closed device, exploded
view, orbit, reassembly, turntable) - rendered with Blender from the STEP files of this repository, see [`media/`](media/README.md).

![exploded view](media/voxhub_exploded.png)

> **Status: revision A1, design complete and checked against the datasheets, not yet built.** ERC and DRC pass, every
> IC, module, connector and electromechanical part was verified against its manufacturer data sheet (generic passives and
> LEDs use KiCad standard footprints), every BOM line was looked up live at DigiKey, the OS image builds and the
> add-on's test-suite passes - but no hardware exists yet. Read [DECISIONS.md](DECISIONS.md) (decision log and
> "Open items") before ordering boards. Progress is tracked in [TODO.md](TODO.md).

## System overview

| Function | Implementation |
|---|---|
| Compute | Raspberry Pi **Compute Module 4 Lite, wireless** (BCM2711 4x A72, 4 GB) - official HAOS target `rpi4-64` |
| Wi-Fi / Bluetooth | on the CM4: 2.4 + 5 GHz 802.11ac, Bluetooth 5.0 |
| Storage | microSD (push-push socket, card power switched by the module) |
| USB | 2 x USB-A 2.0 host (stacked), USB2514B hub, 1.3 A current-limited per port, ESD protected |
| Microphones | 2 x Infineon IM69D130 PDM MEMS (bottom port), ADAU7002 PDM-to-I2S, hardware mute switch |
| Speaker | MAX98357A I2S class-D, 3.2 W into 4 ohm, JST-PH header, 40 mm speaker in the enclosure |
| Zigbee / Thread | Silicon Labs MGM240P (EFR32MG24, +20 dBm) on UART4, flashable in-system |
| Power | USB-C PD sink (CYPD3177): negotiates 9-20 V, then 5 V / 4 A buck (LMR33640) |
| UI | green + blue status LEDs, red mute LED (hard-wired), mute slider on top |
| PCB | 100 x 74 mm, 4 layers, 1.6 mm, parts on one side + one switch on the other |
| Enclosure | 158.8 x 79.2 x 28 mm, two printed parts, no supports |

### Block diagram

```mermaid
flowchart LR
    PD[USB-C PD charger<br/>9-20 V] --> J1[USB-C<br/>receptacle]
    J1 -->|VBUS| BCR[CYPD3177<br/>PD sink controller]
    J1 -->|VBUS| Q1[P-FET<br/>load switch]
    BCR -->|gate| Q1
    Q1 -->|VBUS_SW| BUCK[LMR33640<br/>5 V / 4 A buck]
    BUCK -->|+5V| CM4
    BUCK -->|+5V| SW[2 x TPS2553<br/>port switches]
    BUCK -->|+5V| AMP[MAX98357A<br/>class-D amp]

    subgraph CM4[Raspberry Pi CM4 Lite wireless]
        SOC[BCM2711 + RAM]
        WIFI[Wi-Fi 2.4/5 GHz + BT 5.0]
    end
    CM4 -->|+3V3, 600 mA| LOADS[hub, SD, radio, mics]

    CM4 <-->|SDIO| SD[microSD]
    CM4 <-->|USB 2.0, nEXTRST| HUB[USB2514B hub]
    HUB <--> USBA[2 x USB-A]
    SW -->|VBUS 1.3 A| USBA

    MIC[2 x IM69D130<br/>PDM mics] -->|PDM| ADAU[ADAU7002<br/>PDM to I2S]
    ADAU -->|I2S data| MUTE{{mute switch}}
    MUTE -->|GPIO20| CM4
    CM4 -->|I2S GPIO18/19/21| AMP
    AMP --> SPK[speaker 4 ohm / 3 W]

    CM4 <-->|UART4 + RTS/CTS<br/>SWD, reset| ZB[MGM240P<br/>Zigbee / Thread]
    CM4 -->|GPIO5/6| LED[status LEDs]
    CM4 <-->|I2C1| BCR
```

### Voice pipeline

```mermaid
flowchart LR
    M[microphones] --> W[wake word<br/>openWakeWord] --> V[VAD<br/>end of speech] --> S[STT<br/>Whisper, local]
    S -->|text| C[Claude Messages API<br/>tool use]
    C <-->|get state / call service| HA[Home Assistant Core API]
    C -->|text, sentence by sentence| T[TTS<br/>Piper, local] --> P[speaker]
```

Only the transcribed text (plus tool results) leaves the device.

### GPIO map (CM4)

| GPIO | Function | Notes |
|---|---|---|
| 2 / 3 | I2C1 SDA / SCL | CYPD3177 PD controller (HPI, 0x08) |
| 5 / 6 | LED green / blue enable | active high, N-FET drivers, 10k pull-downs |
| 8 / 9 / 10 / 11 | UART4 TX / RX / CTS / RTS | Zigbee module PA06 (RX) / PA05 (TX) / PA07 (RTS) / PA08 (CTS) - the Silicon Labs reference pin-out |
| 14 / 15 | UART0 TX / RX | debug header (DNP) |
| 16 | amplifier SD_MODE | high = on (left channel) |
| 18 / 19 / 20 / 21 | I2S BCLK / LRCLK / DIN / DOUT | DIN passes through the mute switch |
| 22 / 23 | SWDIO / SWCLK of the radio | in-system flashing |
| 24 / 25 | radio reset / bootloader strap | GPIO24 **high = reset** (open-drain FET on RESETn, 100k pull-down); GPIO25 low = bootloader (10k pull-up) |
| 27 | mute sense | high = muted |

## Power budget

5 V rail (buck output 5.02 V nominal, 4.86 .. 5.17 V over tolerance: Vref +-1.5 %, two 1 % resistors), worst case =
everything at its maximum simultaneously:

| Load | Typical | Peak | Basis |
|---|---|---|---|
| CM4 (SoC, RAM, Wi-Fi) | 3.5 W | 7.0 W | CM4 datasheet: 1.4 A typical maximum at 5 V |
| 3.3 V loads via the CM4 regulator (hub 70/150 mA, microSD 50/200 mA, radio 10/160 mA, mics + converter 3 mA, LEDs 5 mA) | 0.14 A -> 0.5 W | 0.52 A -> 1.9 W | 3.3 V budget 600 mA; 90 % converter efficiency |
| USB-A ports | 0.5 W | 5.0 W | 2 x 500 mA (hardware limit 1.3 A per port) |
| Speaker amplifier | 0.3 W | 3.6 W | 3.2 W output at 90 % efficiency; speech averages far less |
| LEDs, pull-ups | 0.05 W | 0.1 W | |
| **5 V rail total** | **4.9 W (0.98 A)** | **17.6 W (3.5 A)** | buck rated 4 A |
| Buck + switch losses | 0.5 W | 1.9 W | 92 % at 9 V in, P-FET 70 mOhm, inductor 60 mOhm |
| **At the USB-C connector** | **5.4 W** | **19.5 W** | 9 V: 0.6 A typ / 2.17 A peak - 20 V: 0.27 A typ / 0.98 A peak |

- The PD controller requests **>= 2 A at 9-20 V** (18 W at 9 V). Realistic operation (no bus-powered disks, speech
  rather than sine waves) stays below 12 W. The theoretical simultaneous peak of 19.5 W exceeds an 18 W contract by 8 %:
  use a **27 W or larger** charger (9 V/3 A, or anything offering 12/15/20 V at >= 2 A) if both USB ports feed
  500 mA devices.
- 3.3 V budget: 520 mA peak of the 600 mA the CM4 can supply.
- Chargers without a 9-20 V PD profile are rejected safely: the load switch stays open, the buck stays in UVLO (< 7 V)
  and the red PD-FAULT LED lights.

## Thermal estimate (SoC)

Assumptions: 25 C room, module mounted component-side down in the vented enclosure, 14 x 14 x 6 mm heat sink on the BCM2711
(36 K/W on its own in free convection), heat also spreading through the module PCB and the two mezzanine connectors.
Effective module-level thermal resistance derived from published CM4 measurements (bare module on the IO board:
~25 K rise idle at ~2 W, ~55-60 K at full load): about **12 K/W bare, ~9.5-10 K/W with the heat sink in this enclosure**.

| Operating point | Module power | Estimated SoC temperature | Comment |
|---|---|---|---|
| Idle (HAOS, add-ons idle) | 2.0 W | 25 + 2.0 x 10 = **45 C** | |
| Voice assistant active (wake word on one core, Whisper bursts) | 3.5 W | **60 C** | normal operation |
| All four cores loaded continuously | 6.5 W | 90 C -> **throttles at 80 C** | firmware limits to roughly 5.5 W; only during updates / long local STT |

Conclusion: fine without a fan for the intended workload (LLM in the cloud). For sustained local inference fit the taller
15 x 15 x 9.5 mm heat sink (there are 12.9 mm between the SoC and the base plate, so about 3 mm stay free under it) or add a 30 mm fan to the base vents.
Other parts at peak load: buck IC ~1.1 W (junction about +45 K), inductor 0.7 W, P-FET 0.33 W - all uncritical.
These are estimates, not measurements - verify with `vcgencmd measure_temp` on the first prototype.

## Repository layout

| Path | Contents |
|---|---|
| [`hardware/`](hardware/README.md) | KiCad 9 project (generated), generator scripts, schematic PDF, BOM, Gerbers, drill, pick-and-place, DXF, renders, fab + assembly notes |
| [`enclosure/`](enclosure/README.md) | parametric CadQuery source, STL / 3MF / STEP, renders |
| [`os/`](os/README.md) | HAOS board definition, device tree overlay, `build-image.sh` |
| [`assistant/`](assistant/README.md) | Home Assistant add-on: wake word -> STT -> Claude -> TTS |
| [`media/`](media/README.md) | showcase animation (MP4), still of the exploded view, Blender script and helpers |
| [`DECISIONS.md`](DECISIONS.md) | every design decision with its reasoning, the datasheet verification table, sourcing decisions, open items |
| [`TODO.md`](TODO.md) | progress checklist |

## How to build everything

Prerequisites: Linux, Docker, Python >= 3.10, Java >= 21 (only for re-running the autorouter).

```bash
# 1. Hardware: schematic -> ERC -> netlist -> placement -> autoroute -> DRC -> fabrication outputs
docker pull kicad/kicad:9.0
SKIP_ROUTE=1 hardware/build.sh all      # re-uses the checked-in autorouter session (reproduces the committed board, ~5 min)
# to autoroute again: wget -P hardware https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar
#                     hardware/build.sh all

# 2. Enclosure: STL / 3MF / STEP + renders
pip install cadquery
python3 enclosure/voxhub_enclosure.py enclosure
xvfb-run -a python3 enclosure/render.py

# 3. OS image (latest official HAOS + VoxHub configuration)
sudo apt install git curl xz-utils fdisk mtools device-tree-compiler
os/build-image.sh repack --wifi-ssid "MyWifi" --wifi-psk "secret"
#    -> os/output/haos_voxhub-cm4-<version>.img.xz

# 4. Assistant add-on: tests
pip install -r assistant/requirements-dev.txt
(cd assistant && python3 -m pytest -q)

# 5. Showcase animation (Blender 4.2 - 4.5, headless; a little over 3 hours on 4 CPU cores)
pip install cadquery pymupdf pillow numpy && sudo apt install ffmpeg
BLENDER=/path/to/blender media/build_showcase.sh
```

Then: order the PCB (see `hardware/README.md`), print `enclosure/voxhub_shell.3mf` and `voxhub_base.3mf`, flash the image,
add this repository as an add-on repository in Home Assistant and install **VoxHub Assistant** (`assistant/README.md`).

## Cost summary

Unit cost of the purchased parts, DigiKey prices of 2026-11-11 (USD, without tax, shipping, PCB and printed parts).
Line by line: [`hardware/outputs/bom.csv`](hardware/outputs/bom.csv) and [`bom_system.csv`](hardware/outputs/bom_system.csv).

| Group | Lines | Placements | 1 unit | per unit at 100 |
|---|---|---|---|---|
| ICs and radio module (MGM240P alone: 11.47 / 8.45) | 8 | 11 | 30.77 | 20.54 |
| Connectors, slide switch, SMT spacers | 7 | 11 | 16.84 | 12.49 |
| Inductor, crystal, microphones | 3 | 4 | 6.79 | 4.17 |
| Capacitors | 11 | 49 | 11.01 | 3.67 |
| Diodes, LEDs, transistors | 10 | 14 | 4.64 | 2.43 |
| Resistors | 17 | 46 | 4.74 | 0.40 |
| **PCB assembly parts** | **56 (+2 DNP)** | **135** | **74.79** | **43.71** |
| Raspberry Pi CM4 Lite 4 GB wireless (CM4104000) | | | 95.00 | 95.00 |
| Speaker, heat sink, speaker lead | | | 8.83 | 5.45 |
| microSD card, screws, foam, feet (estimates) | | | 10.70 | 10.70 |
| **Complete unit, parts only** | | | **189.32** | **154.86** |

- The compute module is now half of the bill: DigiKey lists the CM4104000 at 95 USD (purchase limit, no backorders);
  the first session's snapshot said 55 USD. A CM4102000 (2 GB) is a drop-in if price matters more than RAM.
- Swaps that came out of the live check (same footprint, equal or better ratings): Epson instead of Abracon crystal
  (-0.24 USD at 100), Walsin / Stackpole instead of Yageo for the 10k, 100k and 49.9k resistors (-0.08), in-stock
  TDK / KEMET / onsemi parts for four lines that were out of stock (+0.30). The datasheet findings add about 0.12 USD net
  (X7R capacitors, one FET, minus the removed reset parts). Net effect on the board: about +0.11 USD at 100 pieces.
- **Out of stock at DigiKey on the day of the check** (all Active): LMR33640ADDAR (26 weeks), 2N7002,215 and
  CL31A226KOHNNNE (22 uF) - no in-stock drop-in with equal ratings exists; TPS2553DBVR (due mid-December) - the identical
  device is in stock as the DBVT reel (+0.16 USD each); CL31B106KBHNNNE (10 uF X7R) - an equal part ships only as a
  2,000-piece Marketplace item. For the 220 nF capacitor C10 (GRM188R71H224KAC4D, Active, 17 weeks lead time) DigiKey
  shows no stock figure. Thin: MGM240PB32VNA3 (71). The BOM names alternates for each; details in
  [DECISIONS.md, section 10](DECISIONS.md#10-sourcing-live-check-2026-11-11).
- **Mouser:** mouser.com blocks automated access, so the Mouser column of the BOM is **not live**: 19 part numbers and figures
  come from search-engine snippets, 18 part numbers are only built from Mouser's prefix scheme or carried over from the
  first session (each line says which), 21 lines have none.

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| ERC (kicad-cli 9.0.9) | 0 errors, 0 warnings | `hardware/outputs/erc.rpt` |
| Netlist equals the code model | 151 components / 99 nets; schematic parity 0 issues | `hardware/gen/model_netlist.json`, `hardware/outputs/drc.rpt` |
| DRC with schematic parity (kicad-cli 9.0.9) | 0 violations, 0 unconnected pads, 0 parity issues; 5 cosmetic checks waived (9 warnings, each explained in `hardware/README.md`) | `hardware/outputs/drc.rpt`, `drc_waived_checks_enabled.rpt` |
| USB 2.0 pair matching | pad-to-pad skew 0.00 / 0.00 / 0.00 mm (upstream / port 1 / port 2), limit 3.8 mm; no vias, no stubs; re-computed independently after the first A1 figure for port 2 turned out to be wrong (real: 4.9 mm) | `hardware/outputs/routing_stats.txt`, DECISIONS.md section 6a |
| Parts vs. datasheets | 26 rows: 25 "verified against datasheet" with source (nine of them read from mirrors of the manufacturer PDF), 1 row of generic passives / standard footprints not individually verified; 7 deviations found and fixed | `DECISIONS.md` section 9 and decision log |
| PCB render | kicad-cli 3D renders | `hardware/outputs/render_*.png` |
| Enclosure fit | part dimensions from the manufacturer drawings; 0 mm^3 interference PCB assembly vs. printed parts | `enclosure/voxhub_enclosure.py`, `enclosure/README.md` |
| Power budget / thermal estimate | above | |
| Sourcing | every BOM line Active and looked up live at DigiKey (status, stock, price at 1 and 100; no stock figure shown for one line, C10); Mouser not live | `hardware/outputs/bom.csv`, `hardware/gen/sourcing_live.json` |
| OS image | repack image built from HAOS 18.5 and verified; from-source build: see `os/README.md` | `os/README.md` |
| Assistant | 86 unit tests pass | `assistant/tests/` |

## License

See [LICENSE](LICENSE). KiCad library parts (symbols, footprints, 3D models under `hardware/3dmodels`) are
CC-BY-SA 4.0 with the KiCad library exception.
