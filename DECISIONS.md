# Design decisions

Every non-obvious choice, with the reasoning behind it. Newest constraints first, then by subsystem.
"Verified" means checked against a primary source that was reachable from the build sandbox;
anything that could not be verified is called out in [Open items](#open-items--things-a-human-must-re-check).

## 0. Constraints of the environment this was designed in

The work was done in a network-restricted sandbox. These blocks shaped several decisions:

| Blocked | Consequence | Next-best option used |
|---|---|---|
| KiCad PPA (`ppa.launchpadcontent.net`), `downloads.kicad.org`; Ubuntu 24.04 only ships KiCad 7 | no native KiCad >= 8 | KiCad **9.0.9** from the official Docker image `kicad/kicad:9.0`, pulled through `mirror.gcr.io` (Docker Hub itself was rate-limited, GHCR blob host blocked). All `kicad-cli`/`pcbnew` steps run in that container. |
| Manufacturer sites (ti.com, infineon.com, st.com, raspberrypi.com datasheets, ...) | datasheets could not be opened directly | Pin-outs and land patterns taken from the KiCad 9 standard libraries (which cite the datasheets), from datasheet PDFs/text mirrored in public GitHub repos, from open hardware reference designs (official CM4IO KiCad library, SparkFun Thing Plus Matter, DNMS), and from web-search summaries. Each fact is tagged with its source in section 9. |
| Distributor sites (digikey.com, mouser.com, arrow.com), Octopart | no live stock/price lookup | Web-search snapshots of distributor listings (undated, sometimes conflicting). Lifecycle status is reliable; stock and price are indicative only - re-check before ordering. |
| `sources.buildroot.net`, `kernel.org`, `gnu.org`, `deb.debian.org`, ... | a from-source HAOS/Buildroot build cannot download its ~400 source tarballs | The default image is produced by repacking the **official** HAOS release (GitHub release assets were reachable). The from-source path is implemented and was run until its first blocked download - see `os/README.md`. |
| KiCad 3D model library is not in the Docker image | no models for renders | Individual STEP files fetched from `gitlab.com/kicad/libraries/kicad-packages3D`; a few are missing upstream and are replaced by simple CadQuery stand-ins. |

## 1. Architecture: SoM instead of a discrete SoC

**Raspberry Pi Compute Module 4 Lite, wireless (CM4104000, 4 GB)** on a custom carrier.

- Home Assistant OS has an official `rpi4-64` board target that boots unmodified on a CM4, so the SD image
  comes from the official HAOS release/build system - no port. (The CM4 is also what Home Assistant Yellow uses.)
- The module already contains the hard parts: BCM2711, LPDDR4, PMIC, and a certified
  2.4/5 GHz 802.11ac + Bluetooth 5.0 radio with antenna. A discrete BCM2711/RK3566 design would need
  0.4 mm BGA fan-out, DDR4 routing and RF certification - not something to generate from scripts and call manufacturable.
- "Lite" (no eMMC) because the requirement is microSD storage; the carrier provides the socket.
- Second sources: any CM4 Lite wireless variant is a drop-in (CM4102000 2 GB, CM4108000 8 GB).
  The CM5 uses the same connectors but a different HAOS target (`rpi5-64`), 5 V/5 A supply and
  different USB pins, so it is **not** a drop-in for this carrier.
- Production lifetime: Raspberry Pi commits to CM4 production until at least January 2034.

Rejected: Home Assistant Green SoC (RK3566, needs full DDR/PMIC design), ODROID modules (no HAOS SoM target),
CM5 (higher power, would need 5 V/5 A and has no advantage for a cloud-LLM voice box).

## 2. Power

- **USB-C PD sink: Infineon CYPD3177 (EZ-PD BCR)**. Fully autonomous, configured by resistor straps - no
  firmware and no NVM programming step in production (an STUSB4500 would boot at 5 V until its NVM is
  programmed; FUSB302 needs a host MCU that is not powered yet).
- **Negotiated voltage: 9 V minimum, 20 V maximum, 2 A minimum.** Peak load on the 5 V rail is ~3.3 A = 16.8 W,
  i.e. 18.3 W at the connector (see power budget in README). 5 V/3 A (15 W) is not enough, so 5 V is excluded;
  9 V/2 A = 18 W is the smallest PDO that works, and practically every >= 20 W PD charger offers it. The BCR picks
  the highest voltage in the window that satisfies the current.
- **Load switch**: AO3401A P-FET, gate driven by the BCR's `VBUS_FET_EN` (active-low, slew-controlled driver that
  swings 0..VBUS) through a 100k/150k divider so |Vgs| = 0.4 x VBUS (3.6 V at 9 V, 8.4 V at 21 V; the part allows 12 V),
  plus a 10 V zener for transients. The first schematic revision had an N-FET inverter here - wrong polarity,
  caught when the datasheet facts were cross-checked. A single FET is enough: the board is sink-only.
- If the charger cannot meet the request the BCR stays at 5 V, raises FAULT (red LED) and never closes the
  switch; additionally the buck's EN divider puts its UVLO at 7.0 V, so nothing downstream starts at vSafe5V.
- **5 V rail: TI LMR33640ADDA** (36 V, 4 A, 400 kHz, HSOIC-8 PowerPAD), set to 5.1 V to absorb drops on the way to
  USB VBUS and the CM4. 6.8 uH (Bourns SRP7028A, Isat 8 A), 4 x 22 uF out, 2 x 10 uF/50 V in.
  36 V rating leaves margin over 20 V + TVS clamp. Internally compensated -> few parts.
- **3.3 V**: taken from the CM4's own 3.3 V output (600 mA budget, ~375 mA worst case used), exactly as the
  official CM4IO board does. This removes a regulator and all power-sequencing/back-powering questions.
- TVS SMBJ22A on VBUS, 24 V ESD diodes on CC1/CC2.

## 3. USB

- The CM4 exposes one USB 2.0 port -> **Microchip USB2514B** hub (the same hub the CM4IO uses).
  Ports 1-2 go to a stacked dual USB-A connector; ports 3-4 are disabled by strapping D+/D- to 3.3 V.
- Per-port power: **TPS2553** (EN active high from the hub's PRTPWR, FAULT to OCS_N), limit 1.3 A typ.,
  100 uF polymer + 100 nF per port, **USBLC6-2SC6** ESD arrays.
- No external EEPROM: internal default configuration via CFG_SEL straps (self-powered, individual port power).

## 4. Audio

- **Microphones: 2 x Infineon IM69D130 (PDM) -> ADI ADAU7002 (PDM-to-I2S) -> CM4 I2S.**
  The first choice was the I2S-output TDK ICS-43434, but sourcing showed the whole I2S MEMS category is being
  discontinued (ICS-43434: last-time-buy passed; SPH0645LM4H: obsolete; CMM-4030D-261-I2S: obsolete; TDK T5848 is
  1.8 V-only with a different pin-out). PDM microphones are the actively produced mainstream, and the ADAU7002
  turns the pair into a standard stereo I2S stream at 3.3 V with zero configuration.
  Drop-in microphone alternates: IM69D120 (same package/pin-out).
- **Amplifier: MAX98357A** (I2S in, filterless class D, 3.2 W / 4 ohm at 5 V) to a 2-pin JST-PH header.
- **Linux side needs no custom driver**: wiring matches the Google voiceHAT (BCLK GPIO18, LRCLK GPIO19,
  data-in GPIO20, data-out GPIO21, amp SD_MODE GPIO16), so the stock `googlevoicehat-soundcard` overlay gives one
  full-duplex ALSA card. Verified present (overlay + kernel modules) in the real HAOS 18.5 rpi4-64 image.
- **Hardware mute**: DPDT slide switch on the top face. Pole A lights a red LED, pole B physically disconnects the
  converter's data line from the CM4 (and grounds the CM4 input). Software cannot override it. Cutting the
  microphone supply instead was rejected: the I2S/PDM clocks would back-power the microphones through their ESD diodes.
- No acoustic echo cancellation (would need an XMOS-class DSP). The assistant is half-duplex instead.
- Microphone spacing ~105 mm (diagonal), bottom-port through the PCB, 7.6 mm acoustic path.

## 5. Zigbee / Thread radio (nice-to-have, included)

- **Silicon Labs MGM240PB32VNA3** (EFR32MG24, +20 dBm, built-in antenna, pre-certified). EFR32 NCPs are the
  best-supported coordinators in Home Assistant (ZHA "EZSP", same family as Connect ZBT-2), and the module also
  runs OpenThread RCP firmware.
- UART4 on GPIO8-11 with RTS/CTS (`dtoverlay=uart4,ctsrts` -> `/dev/ttyAMA1`); TX=PA05, RX=PA06 match the existing
  community firmware builds for this module; reset on GPIO24, bootloader strap PC00 on GPIO25, both with 10k pull-ups
  (the SoC pulls GPIO9-27 low at boot, which would otherwise hold the radio in reset).
- SWD is routed to a Tag-Connect footprint *and* to GPIO22/23 so the CM4 can flash the radio in-system (openocd bit-bang).
- The module ships with a UART bootloader but no Zigbee application: flashing NCP firmware is a production step (see hardware/README).

## 6. Mechanical concept

- PCB 100 x 74 mm, 4 layers, 1.6 mm. All connectors on the rear edge.
- The PCB hangs **component side down** under the top cover. That gives the bottom-port microphones a short path to
  the top surface, lets reverse-mount LEDs shine through the board to the cover, puts the mute slider on top, and lets
  the whole shell print upside down without supports.
- Speaker (40 mm, 4 ohm, 3 W) sits next to the PCB, fires upwards, and is clamped by a pedestal on the base plate.
- CM4 antenna end at the board edge, copper keep-out under the antenna corner; MGM240P at the front edge with the
  keep-out used by SparkFun's reference layout.
- No Ethernet, HDMI, camera, PCIe: not required; leaving them out keeps the board routable on two signal layers.
  Consequence: first-boot network setup is done by pre-seeding Wi-Fi credentials into the image (`os/build-image.sh --wifi-ssid`).
- No fan: 14 x 14 x 6 mm heat sink on the SoC plus vents; see thermal estimate in README.
- User button dropped (wake word + mute switch cover the UI); debug UART header footprint is DNP.

## 6a. PCB implementation (how a board gets routed without a GUI)

- 4 layers: F.Cu / GND plane / +5 V plane / B.Cu. +3V3 is routed (<= 0.5 A, widely distributed).
- **Placement by script**: fixed positions for connectors, ICs and mechanics; passives are placed greedily next to the pad they
  connect to (decoupling capacitors are spread over the supply pins of their IC). The first, tighter placement (0.15 mm between
  courtyards) left no routing channels; 0.45 mm plus a 0.6 mm halo around ICs made the board routable.
- **Power fan-out by script** before autorouting: every GND / +5 V SMD pad gets a stub + via to its plane; CM4 socket power pins use vias
  on the connector centre line so that the outside of both pad rows stays free for signal escape; the 0.4 mm WLCSP gets a fixed escape pattern.
- **Autorouter: Freerouting 2.0.1.** v2.5.0 was tried first: it honours a pass limit but did not converge on this board (30-80
  open connections, oscillating). v2.0.1 leaves 4-5 connections open and stops by itself; it ignores `--router.max_passes`, so it is
  not used with a tight placement where it never terminates. v1.9.0 needs a display (no headless JRE support).
- **Patch router + DRC-driven repair** (in `gen/build_pcb.py`): completes the remaining connections with A* and rip-up, and removes
  anything KiCad's DRC objects to, iterating until `kicad-cli pcb drc` reports nothing. KiCad's DRC is the only judge.
- **USB**: the hub is rotated so that its downstream pins face the USB-A connector and its upstream pins face the CM4. The six data
  nets are re-routed after everything else as short 0.2 mm traces (about 45 ohm over a 0.1 mm prepreg -> ~90 ohm uncoupled differential).
  True coupled-pair routing was not attempted: the pin order at the CM4 socket would force a polarity crossover, and a scripted
  pair router with via swaps was out of proportion for 16-32 mm of USB 2.0.
- Two pcbnew scripting pitfalls that cost time and are worth knowing: `BOARD.Save()` rewrites the `.kicad_pro` with default design
  rules (the build restores `gen/project_settings.json` after every save), and KiCad orders tracks by random UUID on save, which made
  the patch router non-deterministic until tracks were sorted canonically.
- The mute switch SW1 (C&K JS202011JCQN, vertical actuator) sits on the side facing the top cover; it replaced the side-actuated
  PCM12 that went end-of-life.

## 7. Operating system

- **Board ID stays `rpi4-64`.** HAOS OTA bundles are matched by board ID; a private board ID would cut the device
  off from official updates.
- HAOS's update hook deletes `/overlays/*` on the boot partition at every OS update but preserves `config.txt`.
  Therefore the default image uses **only stock overlays** (`googlevoicehat-soundcard`, `uart4`, `gpio-led`, `gpio-key`)
  configured from `config.txt` - it survives updates. The hardware pin assignment was chosen to make that possible.
- A proper single overlay (`os/overlay/voxhub-overlay.dts`) plus a Buildroot board definition is provided for
  from-source builds; it was compiled and applied against the real `bcm2711-rpi-cm4.dtb` of HAOS 18.5.

## 8. Voice assistant

- Self-contained Home Assistant add-on (`assistant/voxhub_assistant`): wake word (openWakeWord via Wyoming) ->
  VAD -> STT (Whisper add-on via Wyoming) -> Claude Messages API with tool use against the Home Assistant API ->
  TTS (Piper add-on via Wyoming) -> speaker. Only text is sent to Anthropic; audio stays on the device.
- Default model `claude-haiku-5-5` (latency), selectable `claude-sonnet-5-5` / `claude-opus-5-5`.
- Dangerous domains (`lock`, `alarm_control_panel`) are never controllable by default.

## 9. Footprint / pin-out verification sources

| Part | Symbol / pin-out source | Footprint source | Status |
|---|---|---|---|
| CM4 socket (2 x DF40C-100DS) | Official Raspberry Pi CM4IO KiCad library (pin names for all 200 pins compared programmatically) | KiCad `Hirose_DF40C-100DS-0.4V_2x50_P0.4mm`; connector spacing/pin-1 position from the official CM4IO footprint | verified |
| CYPD3177 | KiCad `Interface_USB:CYPD3177-24LQ`; strap table, FET-driver polarity from datasheet text | KiCad QFN-24 4x4 EP2.75 | verified (strap ladder: medium confidence) |
| LMR33640ADDA | KiCad symbol + datasheet values (Vref 1.0 V, EN 1.231 V) | KiCad `Texas_HSOP-8-1EP...ThermalVias` | verified |
| USB2514B | KiCad symbol; strap/decoupling from DS00001692E text | KiCad QFN-36 6x6 EP3.7 | verified |
| TPS2553 | datasheet SLVS841F text (pins 1 IN, 2 GND, 3 EN, 4 FAULT, 5 ILIM, 6 OUT); same as AP2553 in CM4IO library | KiCad SOT-23-6 | verified |
| MAX98357A | KiCad `Audio:MAX98357A` | KiCad TQFN-16 3x3 | verified |
| ADAU7002 | datasheet Rev. B PDF (found in the DNMS open hardware repo) - ball map and CONFIG table read directly | generated: 2x4 balls, 0.4 mm pitch; agrees with two independent footprints | verified |
| IM69D130 | KiCad `Sensor_Audio:IM69D130` | KiCad `Infineon_PG-LLGA-5-1` (includes the 0.8 mm port hole) | verified via library |
| MGM240P | Ultra Librarian symbol + SparkFun Thing Plus Matter schematic | generated; identical pad geometry in three independent footprints (SparkFun, Ultra Librarian, sivakov512) | verified |
| USB-C USB4105-GF-A, USB-A 61400826021, DM3AT-SF-PEJM5, JS202011JCQN, JST PH, SOT/0402/... | KiCad standard symbols | KiCad standard footprints named after the exact MPN | verified via library |

## Open items - things a human must re-check

These could not be closed from inside the sandbox and are deliberately not hidden:

1. **CM4 antenna corner.** The keep-out is placed at the corner derived from the CM4IO pin geometry (pin-199 end, J2 side).
   The CM4 mechanical drawing could not be opened; confirm against the datasheet figure and move the keep-out if needed.
2. **CYPD3177 behaviour when the best in-range PDO has too little current** (fall back to a lower voltage vs. flag
   mismatch) is not stated verbatim in the retrievable text - bench-test with a 20 W, 30 W and 65 W charger.
3. **LMR33640 5 V/400 kHz reference table row** (L and Cout) was not retrievable; 6.8 uH / 88 uF was chosen from the ripple
   equations (1.4 A p-p at 20 V in).
4. **Mechanical dimensions not confirmed against drawings**: Wurth 61400826021 overhang beyond the PCB edge (2.5 mm assumed),
   JS202011JCQN body/actuator height (3.5 + 2.0 mm assumed), speaker CMS-4017-34SP frame details. The enclosure is
   parametric - adjust the constants at the top of `enclosure/voxhub_enclosure.py`.
5. **MGM240P antenna keep-out dimensions** come from SparkFun's layout, not from the Silicon Labs figure.
6. **USB 2.0 data lines are matched single-ended 0.2 mm traces, not coupled pairs** (skew 1.2 / 4.6 / 2.4 mm, see hardware/README
   "Known limitations"). The 90 ohm target depends on the 0.10 mm outer prepreg called out in the fab notes; measure on the first prototypes.
7. Stock and prices are web-search snapshots, not live quotes.
8. Nothing here has been powered on. Treat revision A as a prototype spin.
