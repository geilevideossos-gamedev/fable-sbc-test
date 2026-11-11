# Design decisions

Every non-obvious choice, with the reasoning behind it. Newest constraints first, then by subsystem.
"Verified against datasheet" means checked against the manufacturer document named in [section 9](#9-footprint--pin-out-verification-against-the-datasheets);
anything that could not be verified is called out in [Open items](#open-items--things-a-human-must-re-check).

## Revision A1 (second session, 2026-11-11): decision log

The first session worked without access to manufacturer and distributor sites. The second session re-checked the
design against the real datasheets and drawings, fixed what the check found and closed the open items.
Every change, with its reason:

| # | Decision | Why |
|---|---|---|
| 1 | **CM4 antenna keep-out moved** from x 90..100 / y 35..47 to x 91..100 / y 44.5..59.5 (all layers) | CM4 datasheet fig. 4: the 6.5 x 11 mm "Wireless Cutout" sits on the short edge at the pin 99/199 end, 10.5..21.5 mm from the long edge of the pin 1-100 connector = board x 92.5..99, y 46.5..57.5. The old keep-out was on the right edge but in the wrong half, so all four layers had copper under the antenna. New area = the datasheet's "ideally 8 x 15 mm", extended to the board edge. |
| 2 | **Buck feedback 24.3k -> 24.9k** (5.02 V nominal instead of 5.12 V) | 24.9k is the value of the TI table for 5 V. With 24.3k the tolerance corners (Vref +-1.5 %, 2 x 1 % resistors) reach 5.28 V, above the CM4 limit of 5.25 V. |
| 3 | **Buck input bypass 100 nF -> 220 nF / 50 V / X7R**; **input capacitors X5R -> X7R**; inductor and output capacitors unchanged | LMR33640 datasheet (SNVSB99C) table for 5 V / 400 kHz: L = 6.8 uH, COUT = 4 x 22 uF (min. 3 x 22 uF), RFBB = 24.9k, CIN = 10 uF + 220 nF; "The 220 nF must also be rated at 50 V with an X7R dielectric", CIN "10-uF, 50-V, X7R (or better)". L and COUT of revision A were already the table values. |
| 4 | **1 uF capacitors 0402 X5R -> 0603 X7R** (buck VCC, CYPD3177 VDDD and VCCD); **second 100 nF on VDDD** | The 0402 X5R part keeps about 0.3 uF at 5 V and 0.5 uF at 3.3 V (Samsung DC-bias curve); CYPD3177 needs >= 0.8 uF on VDDD and specifies 1 uF + 2 x 100 nF there. |
| 5 | **USB2514B RESET_N driven by the CM4 (nEXTRST, pin 100)**; 10k / 100 nF RC reset removed | The RC reset only meets the hub's reset timing if 3.3 V rises within 400 us, which the CM4 does not guarantee. nEXTRST is low during reset and goes high when the SoC boots; the official CM4IO board does the same. |
| 6 | **MGM240P flow control swapped: PA07 = RTS -> GPIO10 (CTS4), PA08 = CTS <- GPIO11 (RTS4)** | MGM240P datasheet fig. 5.1 (UART NCP configuration). Revision A had the two outputs driving each other with the reference pin assignment. |
| 7 | **MGM240P RESETn: pull-up and capacitor removed, open-drain N-FET (2N7002) added**; GPIO24 is now active HIGH (high = radio in reset), 100k gate pull-down | Datasheet pin table: "An external pull-up is not recommended ... it is required to only drive this pin low during reset". A push-pull GPIO plus pull-up violates that; without the pull-up the SoC's boot-time pull-down would hold the pin at about 0.9 V. |
| 8 | **USB pairs: flow-through ESD links, pad-to-pad length measurement, serpentine matching** (details in 6a) | The requested <= 3.8 mm skew. The old number (sum of all track segments) also counted stubs: measured pad to pad, revision A was at 1.2 / 2.5 / 6.1 mm, not 1.2 / 4.6 / 2.4 mm. |
| 9 | **Enclosure**: USB-C window 12.4 x 6.3 -> 13.4 x 7.5 mm, USB-A window 15.2 x 16.5 -> 15.6 x 17.0 mm, microSD window shifted 0.425 mm, mute dish 16 x 10 x 1.4 mm, 1 mm relief (dia 35.6) in front of the speaker cone, locating ring 40.8 mm, pedestal ring 13..21 mm | Manufacturer drawings (section 9): the USB-C shell ends flush with the PCB edge, so the plug overmould has to enter the wall; the USB-A flange lip reaches 15.95 mm; the speaker needs >= 0.8 mm in front of the diaphragm and has a dia 23 yoke; frame tolerance +-0.3 mm. GAP_TOP, DEPTH, overhang 2.5 mm and the speaker size were confirmed. |
| 10 | **Part swaps** (same footprint, equal or better ratings, cheaper or in stock) - list in section 10 | Live DigiKey check of every BOM line. |
| 11 | **LMR33640ADDAR, 22 uF 1206, 2N7002, TPS2553DBVR kept although out of stock at DigiKey** | No in-stock part with equal or better ratings and the same footprint exists (section 10). Flagged in the BOM instead of silently downgrading. |
| 12 | **Stand-in 3D models rewritten as coloured STEP assemblies** (CM4 with heat sink, stacked USB-A, slide switch, radio module, ...) | KiCad's STEP export drops colours and the old stand-ins were single boxes; the showcase render and the KiCad renders need to tell metal from plastic. Envelopes follow the drawings. |
| 13 | **OS full build runs on the host as an unprivileged user; github.com "archive" sources are fetched with git** (`VOXHUB_GITHUB_VIA_GIT=1`) | HAOS's `scripts/enter.sh` and Buildroot refuse to run as root; this environment's egress proxy answers 403 to `github.com/<owner>/<repo>/archive/...` while git access to the same public repositories is allowed. Buildroot still checks every tarball against its hash. Details in os/README.md. |
| 14 | **Showcase animation rendered with Cycles on the CPU at 4 samples + OpenImageDenoise, 21 s** | No GPU in the build machine: EEVEE through software OpenGL needs about 100 s per frame, Cycles about 15 s with these settings. Details in media/README.md. |
| 15 | **Mouser data is not live** | mouser.com answers every automated request with HTTP 503 (bot protection) and no API key was available; evading the protection was not attempted. The BOM carries DigiKey live data plus clearly marked search-snippet values for Mouser. |
| 16 | **OS full build restarted after a self-inflicted stop (attempt 5)**; the four affected Buildroot packages are rebuilt, nothing is patched | Attempt 4 stopped after 3 h at `libblockdev` with `libtool: error: '.../build/util-linux-2.40.4/libuuid.la' is not a valid libtool archive`. Cause: the disk-space helper of this session (outside the repository) had emptied the build directories of finished packages, but the staging `libfdisk.la` / `libmount.la` (and `libdns.la`, `libgnutlsxx.la`) refer back into them. Rewriting the `.la` files would have hidden the mistake in a non-standard build tree, so the directories of `util-linux`, `host-util-linux`, `gnutls` and `dhcp` were deleted (Buildroot rebuilds them) and the helper now skips every directory that a libtool archive points to and anything below 150 MB. The run log is in os/README.md. |

## 0. Constraints of the environment this was designed in

The first session ran in a network-restricted sandbox. These blocks shaped several decisions (the table is kept as a
record; the second session had general internet access and re-did the checks, see the log above and section 9):

| Blocked | Consequence | Next-best option used |
|---|---|---|
| KiCad PPA (`ppa.launchpadcontent.net`), `downloads.kicad.org`; Ubuntu 24.04 only ships KiCad 7 | no native KiCad >= 8 | KiCad **9.0.9** from the official Docker image `kicad/kicad:9.0`, pulled through `mirror.gcr.io` (Docker Hub itself was rate-limited, GHCR blob host blocked). All `kicad-cli`/`pcbnew` steps run in that container. |
| Manufacturer sites (ti.com, infineon.com, st.com, raspberrypi.com datasheets, ...) | datasheets could not be opened directly | Pin-outs and land patterns taken from the KiCad 9 standard libraries (which cite the datasheets), from datasheet PDFs/text mirrored in public GitHub repos, from open hardware reference designs (official CM4IO KiCad library, SparkFun Thing Plus Matter, DNMS), and from web-search summaries. Each fact is tagged with its source in section 9. |
| Distributor sites (digikey.com, mouser.com, arrow.com), Octopart | no live stock/price lookup | Web-search snapshots of distributor listings (undated, sometimes conflicting). Lifecycle status is reliable; stock and price are indicative only - re-check before ordering. |
| `sources.buildroot.net`, `kernel.org`, `gnu.org`, `deb.debian.org`, ... | a from-source HAOS/Buildroot build cannot download its ~400 source tarballs | The default image is produced by repacking the **official** HAOS release (GitHub release assets were reachable). The from-source path is implemented and was run until its first blocked download - see `os/README.md`. |
| KiCad 3D model library is not in the Docker image | no models for renders | Individual STEP files fetched from `gitlab.com/kicad/libraries/kicad-packages3D`; a few are missing upstream and are replaced by simple CadQuery stand-ins. |

What was still blocked in the second session (2026-11-11):

| Blocked | Consequence | What was done |
|---|---|---|
| mouser.com (HTTP 503 for every automated request), octopart / trustedparts / findchips (403) | no live Mouser stock or prices | DigiKey is live for every line; Mouser part numbers and figures come from search-engine snippets and are marked "NOT live" in the BOM. A Mouser API key would close this. |
| silabs.com, hirose.com, the Littelfuse-hosted C&K data sheet, analog.com land-pattern document (403 / unreachable) | four documents could not be read from the manufacturer's own server | the manufacturer's PDF was read from a mirror (SparkFun, distributor document servers); revision and mirror URL are listed per part in section 9 |
| `github.com/<owner>/<repo>/archive/...` tarballs (403 from the egress proxy; git access to the same repositories works) | 37 source packages of the HAOS build cannot be downloaded the normal way | `os/build-image.sh` fetches them with git when `VOXHUB_GITHUB_VIA_GIT=1` (section 7) |
| no GPU, 4 CPU cores, 30 GB disk | render time and OS build are the bottlenecks | Cycles at 4 samples + denoiser for the animation; build directories of finished Buildroot packages are pruned during the OS build |

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
  9 V/2 A = 18 W is the smallest PDO that works, and practically every >= 20 W PD charger offers it.
  **PDO selection (verified):** the BCR walks through the source PDOs from the highest voltage down and takes the first
  one inside VBUS_MIN..VBUS_MAX that offers at least ISNK_COARSE + ISNK_FINE (CY4533 kit guide 002-25263 *B, section
  "PDO selection"; datasheet 002-25383 *C section 4.1). A 30 W charger with 20 V / 1.5 A, 15 V / 2 A, 9 V / 3 A therefore
  ends up at 15 V. If no PDO qualifies it requests 5 V / 900 mA with the capability-mismatch flag, drives FAULT high
  and leaves VBUS_FET_EN off. The four strap dividers (5.1k / 1k, 0 ohm to VDDD, 5.1k / 2.4k, 0 ohm to GND) are exactly
  the datasheet table rows for 9 V, 20 V, 2 A and +0 mA.
- **Load switch**: AO3401A P-FET, gate driven by the BCR's `VBUS_FET_EN` (active-low, slew-controlled driver that
  swings 0..VBUS) through a 100k/150k divider so |Vgs| = 0.4 x VBUS (3.6 V at 9 V, 8.4 V at 21 V; the part allows 12 V),
  plus a 10 V zener for transients. The first schematic revision had an N-FET inverter here - wrong polarity,
  caught when the datasheet facts were cross-checked. A single FET is enough: the board is sink-only.
- If the charger cannot meet the request the BCR stays at 5 V, raises FAULT (red LED) and never closes the
  switch; additionally the buck's EN divider puts its UVLO at 7.0 V, so nothing downstream starts at vSafe5V.
- **5 V rail: TI LMR33640ADDA** (36 V, 4 A, 400 kHz, HSOIC-8 PowerPAD). All external parts are the values of the
  datasheet table for 5 V / 400 kHz: 6.8 uH (Bourns SRP7028A-6R8M, Isat 8 A, Irms 4.5 A, 54/60 mOhm), 4 x 22 uF out
  (the table's typical value; minimum 3 x 22 uF), 100k / 24.9k feedback (5.02 V), 2 x 10 uF / 50 V X7R + 220 nF / 50 V
  X7R in, 100 nF boot, 1 uF VCC. Inductor ripple 0.81 A p-p at 9 V in, 1.40 A at 20 V; peak inductor current at 4 A
  load 4.7 A, well below Isat. EN divider 470k / 100k: on at 7.02 V, off at 6.45 V.
  36 V rating leaves margin over 20 V + TVS clamp. Internally compensated -> few parts.
  Revision A was set to 5.1 V "to absorb drops"; that put the tolerance corners above the CM4's 5.25 V limit (see log no. 2).
- **3.3 V**: taken from the CM4's own 3.3 V output (600 mA budget, ~375 mA worst case used), exactly as the
  official CM4IO board does. This removes a regulator and all power-sequencing/back-powering questions.
- TVS SMBJ22A on VBUS, 24 V ESD diodes on CC1/CC2. Known margin: at its full rated surge (16.9 A) the SMBJ22A clamps
  at 35.5 V - below the LMR33640's 38 V, but above the 30 V absolute maximum of the CYPD3177 and the AO3401A. Hot-plug
  ringing is far below that current, so this is accepted for revision A; TI TVS2200DRVR would be the tighter clamp
  (different footprint).

## 3. USB

- The CM4 exposes one USB 2.0 port -> **Microchip USB2514B** hub (the same hub the CM4IO uses).
  Ports 1-2 go to a stacked dual USB-A connector; ports 3-4 are disabled by strapping D+/D- to 3.3 V.
- Per-port power: **TPS2553** (EN active high from the hub's PRTPWR, FAULT to OCS_N), limit 1.3 A typ.,
  100 uF polymer + 100 nF per port, **USBLC6-2SC6** ESD arrays.
- No external EEPROM: internal default configuration via CFG_SEL straps (self-powered, individual port power).
- RESET_N comes from the CM4's nEXTRST output (as on the CM4IO board): the hub stays in reset until the SoC runs.
- Current limits with the verified TPS2553 equation: 20k -> 1215 / 1295 / 1375 mA (min / typ / max) per USB-A port,
  49.9k -> 490 / 520 / 550 mA for the microSD supply.

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
- UART4 on GPIO8-11 with RTS/CTS (`dtoverlay=uart4,ctsrts` -> `/dev/ttyAMA1`); pin assignment as in the datasheet's
  NCP reference diagram (fig. 5.1): TX = PA05, RX = PA06, RTS = PA07 (-> GPIO10 / CTS4), CTS = PA08 (<- GPIO11 / RTS4).
- Reset: GPIO24 drives an open-drain 2N7002 on RESETn (**GPIO24 high = radio held in reset**). The module's reset pin has
  its own pull-up and must only ever be pulled low, so there is no external pull-up and no capacitor on it. The SoC's
  boot-time pull-down on GPIO24 plus a 100k gate resistor keep the FET off, i.e. the radio runs by default.
- Bootloader strap PC00 on GPIO25 with a 10k pull-up (the SoC pulls GPIO9-27 low at boot, which would otherwise start
  the bootloader).
- SWD is routed to a Tag-Connect footprint *and* to GPIO22/23 so the CM4 can flash the radio in-system (openocd bit-bang).
- The module ships with a UART bootloader but no Zigbee application: flashing NCP firmware is a production step (see hardware/README).

## 6. Mechanical concept

- PCB 100 x 74 mm, 4 layers, 1.6 mm. All connectors on the rear edge.
- The PCB hangs **component side down** under the top cover. That gives the bottom-port microphones a short path to
  the top surface, lets reverse-mount LEDs shine through the board to the cover, puts the mute slider on top, and lets
  the whole shell print upside down without supports.
- Speaker (40 mm, 4 ohm, 3 W) sits next to the PCB, fires upwards, and is clamped by a pedestal on the base plate.
- CM4 antenna end at the board edge (1 mm from it), copper keep-out on all layers under the antenna as drawn in the
  CM4 datasheet (log no. 1); no enclosure screw or other metal within 10 mm of it except the module's own mounting screw.
  MGM240P at the front edge; its keep-out (module x -4.4..4.4, y -7.5..-2.7 = board 19.6..28.4 x 69.2..74.0) matches the
  Silicon Labs datasheet exactly.
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
  nets are re-routed after everything else as 0.2 mm traces (about 45 ohm over a 0.1 mm prepreg -> ~90 ohm uncoupled differential).
  True coupled-pair routing was not attempted: the pin order at the CM4 socket would force a polarity crossover, and a scripted
  pair router with via swaps was out of proportion for a few centimetres of USB 2.0.
- **USB length matching (revision A1)**, all in `gen/build_pcb.py`:
  1. *Flow-through ESD links.* Each USBLC6-2SC6 has two pads per line (1+6, 3+4). They are joined by a locked straight track under
     the package (ST's flow-through layout), and the router is only allowed to connect hub pin and connector pin to **different**
     ESD pads, pad to pad. The line therefore runs connector -> ESD pad -> link -> other ESD pad -> hub without any stub.
  2. *Electrical length.* `usb_report()` builds the copper graph of each net and measures the shortest path from the hub pin to the
     connector pin, counting 1.5 mm per via. The old statistic (sum of all segments) is still printed as "copper-diff".
  3. *Serpentines.* `tune_usb()` adds 45-degree-mitred meander bumps (0.6 mm pitch = 3 x track width, amplitude 0.3..3 mm) to the
     shorter line of each pair, only where the copper keeps 0.17 mm to everything else, until the path lengths agree.
  4. `postroute.sh` tries several net orders; a variant is accepted only if KiCad's DRC is clean again after tuning and both
     numbers (pad-to-pad skew and copper difference) are below 3.8 mm.

  Result (`hardware/outputs/routing_stats.txt`): upstream 33.62 / 33.62 mm, port 1 27.55 / 28.90 mm, port 2 25.41 / 25.41 mm
  -> skew 0.00 / 1.35 / 0.00 mm; copper difference 1.86 / 0.56 / 0.39 mm. Port 1 is not matched to zero because the area
  between hub, ESD device and connector has no room for the last 1.35 mm of meander at the required clearance - still
  well inside the 3.8 mm guideline (about 9 ps). The price of the stub-free topology is length: the port lines are
  25-29 mm instead of 16-24 mm, and port 2 has 4 vias on one line and none on the other.
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
- **Full build (second session).** `build-image.sh full` now refuses to run as root (HAOS's `enter.sh` and Buildroot do
  too), points Buildroot's download and ccache directories away from `/cache` (they only exist inside the HAOS builder
  container) and can fetch GitHub "archive" sources with git (`VOXHUB_GITHUB_VIA_GIT=1`): every such tarball that
  Buildroot's own mirror does not have is produced with `git fetch --depth 1` + `git archive | gzip -n`, which is
  byte-identical to GitHub's tarball, and handed to Buildroot as `BR2_PRIMARY_SITE`. Buildroot's hash check stays in force.
  How far the build got in this environment is documented in os/README.md.
- The radio's reset line is active high since revision A1 (GPIO24 high = reset); nothing in the OS configuration
  drives it, the flashing instructions in hardware/README.md were updated.

## 8. Voice assistant

- Self-contained Home Assistant add-on (`assistant/voxhub_assistant`): wake word (openWakeWord via Wyoming) ->
  VAD -> STT (Whisper add-on via Wyoming) -> Claude Messages API with tool use against the Home Assistant API ->
  TTS (Piper add-on via Wyoming) -> speaker. Only text is sent to Anthropic; audio stays on the device.
- Default model `claude-haiku-5-5` (latency), selectable `claude-sonnet-5-5` / `claude-opus-5-5`.
- Dangerous domains (`lock`, `alarm_control_panel`) are never controllable by default.

## 9. Footprint / pin-out verification against the datasheets

Checked on 2026-11-11 against the manufacturer documents below (pin-out against the pin table, footprint against the
recommended land pattern or package drawing, strap / component values against the application section). Where the
manufacturer's own server refused the download, the same manufacturer PDF was read from a mirror; that is stated.
"Deviation" rows say what was found and what was done about it.

| Part | Source (revision) | Status |
|---|---|---|
| Raspberry Pi CM4 (pin-out, mechanics, antenna) | https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf (Release 4, 30/06/2026); official CM4IO KiCad files https://datasheets.raspberrypi.com/cm4io/CM4IO-KiCAD.zip | **verified against datasheet** - 200 / 200 pin names (five spelling-only differences), all used nets, socket spacing, module outline, H5-H8, viewing side (all 200 pads coincide with the official CM4IO footprint). **Deviation found and fixed:** antenna keep-out was in the wrong half of the edge (log no. 1). |
| CM4 socket Hirose DF40C-100DS-0.4V(51) | Hirose DF40 catalogue, edition 2013.11, via mirror https://cdn-shop.adafruit.com/product-files/2227/ed_DF40_20140305-337786.pdf (hirose.com not reachable) | **verified against datasheet** - land pattern, 1.5 mm mated height, 1.5 mm spacer. Note: the inward power stubs cross Hirose's "layout prohibited area" between the pad rows exactly as on the official CM4IO board. |
| CYPD3177-24LQXQ | https://www.infineon.com/assets/row/public/documents/24/49/infineon-cypd3177-24lqxq-datasheet-en.pdf (002-25383 Rev. *C, 2024-09-18); kit guide 002-25263 Rev. *B https://www.infineon.com/assets/row/public/documents/24/44/infineon-cy4533-ez-pd-barrel-connector-replacement-evk-guide-usermanual-en.pdf | **verified against datasheet** - pin-out, QFN-24 land pattern, active-low P-FET driver, FLIP 49.9k, I2C 0x08, unused pins, all four strap dividers = table values, PDO selection algorithm. **Deviation found and fixed:** VDDD decoupling (1 uF X7R 0603 + 2 x 100 nF instead of 1 uF X5R 0402 + 100 nF). Note: the single-FET gate network differs from the two-FET reference circuit - measure VGS at 9 V and 20 V on the prototype. |
| LMR33640ADDA | https://www.ti.com/lit/ds/symlink/lmr33640.pdf (SNVSB99C, rev. November 2020) | **verified against datasheet** - pin-out, HSOIC-8 PowerPAD land pattern, "A" = 400 kHz / 4 A, EN thresholds (UVLO 7.02 V / 6.45 V), CBOOT, CVCC; L = 6.8 uH and COUT = 4 x 22 uF are the table row for 5 V / 400 kHz. **Deviations found and fixed:** RFBB 24.3k -> 24.9k, CHF 100 nF -> 220 nF X7R, CIN X5R -> X7R (log no. 2, 3). |
| Bourns SRP7028A-6R8M | https://www.bourns.com/docs/Product-Datasheets/SRP7028A.pdf | **verified against datasheet** - 6.8 uH, Isat 8 A, Irms 4.5 A, DCR 54 typ / 60 max mOhm, footprint. |
| USB2514B-I/M2 | https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/USB251xB-xBi-Data-Sheet-DS00001692.pdf (DS00001692E) | **verified against datasheet** - pin-out, CFG_SEL = 00, NON_REM, port disable by 10k to 3.3 V, PRTPWR / OCS polarity, VBUS_DET, RBIAS 12k 1 %, 24 MHz crystal + load capacitors, filter capacitors. **Deviation found and fixed:** RESET_N (log no. 5). Accepted: the KiCad QFN-36 pads are 0.825 mm long, Microchip recommends 0.90 mm (79 % of the terminal is covered; pitch, exposed pad and numbering match). |
| TPS2553DBV | https://www.ti.com/lit/ds/symlink/tps2553.pdf (SLVS841G, October 2026) | **verified against datasheet** - pin-out, active-high EN, open-drain FAULT, 2.5-6.5 V input, ILIM equation (20k -> 1.215 / 1.295 / 1.375 A, 49.9k -> 0.49 / 0.52 / 0.55 A). |
| MAX98357AETE+ | Maxim 19-6779 Rev 7 (original PDF via https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf), cross-checked with Rev 13 | **verified against datasheet** - TQFN-16 pin-out, SD_MODE at 3.3 V = left channel, GAIN_SLOT open = 9 dB, 2.5-5.5 V, package outline. The separate land-pattern document 90-0031 could not be retrieved. |
| ADAU7002ACBZ | ADI ADAU7002 Rev. C (11/2019), original PDF via mirror https://cdn.eicom.ru/media/PDF/2429992.pdf | **verified against datasheet** - ball map, CONFIG = IOVDD -> I2S, 1.62-3.6 V, BCLK = 64 fs, 0.4 mm ball grid. The datasheet gives no land pattern (pad diameter 0.22 mm stays an IPC choice). |
| IM69D130 | https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf (V1.0, 2017-12-19) | **verified against datasheet** - pins, SELECT (GND = left, VDD = right at the ADAU7002), 1.62-3.6 V, 3.072 MHz clock, land pattern with the 0.8 mm port hole. Note: 70 C ambient limit at 3.3 V. |
| MGM240PB32VNA | Silicon Labs MGM240P data sheet Rev. 1.0 (original PDF via https://cdn.sparkfun.com/assets/1/4/5/e/5/MGM240P-Datasheet.pdf; silabs.com refuses automated downloads, Rev. 1.2 not retrievable) | **verified against datasheet** - pin-out, land pattern (36 / 36 pads), RFOUT open for the built-in antenna, antenna keep-out, no external decoupling required. **Deviations found and fixed:** RTS / CTS swapped, RESETn pull-up (log no. 6, 7). |
| USB-C GCT USB4105-GF-A | https://gct.co/files/drawings/usb4105.pdf (Rev. B4) | **verified against datasheet** - footprint, shell 8.94 x 7.35 x 3.31 mm, shell flush with the PCB edge. |
| USB-A Wurth 61400826021 | https://www.we-online.com/components/products/datasheet/61400826021.pdf (Rev. 001.001, 2025-09-11) | **verified against datasheet** - footprint and drills, shell height 15.34 mm, flange 14.5 x 15.5 mm with lips at 0.45 / 15.95 mm, 2.5 mm overhang beyond the PCB edge. |
| microSD Hirose DM3AT-SF-PEJM5 | Hirose drawing EDC-325165-40-00 for the (40) variant, via mirror https://static.chipdip.ru/lib/504/DOC014504844.pdf (hirose.com not reachable) | **verified against datasheet** - footprint, body 13.85 x 15.95 x 1.68 mm, card positions (locked: 1.6 mm behind the enclosure face). |
| C&K JS202011JCQN | C&K "JS series" data sheet, edition 22 Sep 2022, via mirror https://static.chipdip.ru/lib/994/DOC043994900.pdf (the current Littelfuse-hosted edition refuses downloads) | **verified against datasheet** - land pattern, body 9.0 x 3.6 x 3.5 (3.6) mm, actuator 1.5 x 1.5 x 2.0 mm, 2 mm travel. The drawing has no body tolerances. |
| JST B2B-PH-K-S | https://www.jst-mfg.com/product/pdf/eng/ePH.pdf | **verified against datasheet** - footprint, 6.0 mm height. |
| Wurth 9774015151R | https://www.we-online.com/components/products/datasheet/9774015151R.pdf (Rev. 001.002) | **verified against datasheet** - land pattern, 1.5 mm height, M2.5 thread (2.9 mm long). |
| AO3401A | https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf (Rev 3.1) | **verified against datasheet** - SOT-23 G / S / D = 1 / 2 / 3, VDS -30 V, VGS +-12 V. |
| USBLC6-2SC6 | ST USBLC6-2 data sheet Rev 3 (2008) via mirror https://pccomponents.com/datasheets/ST_MI-USBLC62SC6.pdf | **verified against datasheet** (old revision) - pins 1 + 6 and 3 + 4 are one line each, 5 = VBUS, 2 = GND. |
| SMBJ22A | Littelfuse SMBJ series data sheet (rev. 2020-06-03, mirror on e2e.ti.com) | **verified against datasheet** - 22 V stand-off, 24.4-26.9 V breakdown, 35.5 V clamp at 16.9 A (margin note in section 2). |
| MM3Z10V / SZMM3Z10VT1G | https://www.onsemi.com/pdf/datasheet/mm3z2v4t1-d.pdf (Rev. 15) | **verified against datasheet** |
| Speaker Same Sky CMS-4017-34SP | https://www.sameskydevices.com/product/resource/cms-4017-34sp.pdf (rev 1.02) | **verified against datasheet** - dia 40 +-0.3 x 17.5 +-0.3 mm, yoke dia 23, 4 ohm, 3 W, baffle opening dia 35.6 with >= 0.8 mm in front of the diaphragm. |
| Heat sink Same Sky HSB03-141406 | https://www.sameskydevices.com/product/resource/hsb03-141406.pdf (rev 1.03) | **verified against datasheet** - 14 x 14 x 6 mm. |
| Crystal Epson TSX-3225 24.0000MF18X-C0 | Epson TSX-3225 specification (pad assignment only seen in distributor copies of the Epson sheet) | pads 1 / 3 = crystal, 2 / 4 = GND as on the footprint; CL 18 pF. **Not verified against an Epson-hosted document** - compare with the reel label / Epson sheet before assembly. |
| Passives, LEDs (0402 / 0603 / 1206 / SOD-323 / SMB / reverse-mount 1206) | KiCad standard footprints named after the package | standard IPC land patterns; values and ratings checked on the DigiKey product pages (section 10). |

## 10. Sourcing (live check 2026-11-11)

Every BOM line was looked up on its DigiKey product page (status, stock, price at 1 and 100 pieces); the raw data is in
`hardware/gen/sourcing_live.json` and ends up in `hardware/outputs/bom.csv`. Rule for swaps: same footprint, every
rating equal or better, lifecycle Active - and either cheaper or in stock where the old part was not.

| Line | Old part | New part | Reason (USD at 100 pcs, DigiKey) |
|---|---|---|---|
| 24 MHz crystal | Abracon ABM8-24.000MHZ-B2-T (0.53) | Epson TSX-3225 24.0000MF18X-C0 (0.30) | cheaper; 10 / 10 ppm instead of 20 / 20 ppm, same 18 pF load, same pads |
| 10k 1 % 0402 (13 x) | Yageo RC0402FR-0710KL (0.0108) | Walsin WR04X1002FTL (0.0061) | cheaper, identical ratings |
| 100k 1 % 0402 (13 x) | Yageo RC0402FR-07100KL (0.0108) | Stackpole RMCF0402FT100K (0.0091) | cheaper, identical ratings |
| 49.9k 1 % 0402 | Yageo RC0402FR-0749K9L (0 in stock) | Stackpole RMCF0402FT49K9 (0.0096) | in stock and cheaper |
| 24.9k 1 % 0402 | (new value, was 24.3k) | Stackpole RMCF0402FT24K9 (0.0091) | value change (log no. 2) |
| 1 uF 50 V X5R 0603 | Samsung CL10A105KB8NNNC (0 in stock) | TDK C1608X5R1H105K080AB (0.058) | in stock, identical ratings |
| 100 nF 50 V X7R 0603 | Samsung CL10B104KB8NNNC (0 in stock) | KEMET C0603C104K5RACTU (0.046) | in stock, identical ratings |
| 4.7 uF X5R 0603 | Samsung CL10A475KO8NNNC 16 V (0 in stock) | TDK C1608X5R1E475K080AC 25 V (0.091) | in stock, higher voltage rating |
| 1 uF 16 V | Samsung CL05A105KO5NNNC X5R 0402 | TDK C1608X7R1C105K080AC X7R 0603 (0.041) | datasheet finding (log no. 4): footprint changes on purpose |
| 10 uF 50 V 1206 | Samsung CL31A106KBHNNNE X5R | Samsung CL31B106KBHNNNE X7R (0.168) | datasheet finding (log no. 3); 0 in stock at DigiKey, alternates in the BOM |
| 220 nF 50 V X7R 0603 | (new) | Murata GRM188R71H224KAC4D (0.052) | datasheet finding (log no. 3) |
| 10 V zener SOD-323 | onsemi MM3Z10VT1G (0 in stock) | onsemi SZMM3Z10VT1G (0.109) | same die, AEC-Q101 grade, in stock |

Not swapped although a cheaper or in-stock candidate exists, because a rating would go down:

- **2N7002,215** (0 in stock): 2N7002BK,215 is in stock and 0.3 cent dearer, but VGS is +-20 V instead of +-30 V.
- **22 uF 16 V X5R 1206, CL31A226KOHNNNE** (0 in stock): the TDK part in stock is +-20 % instead of +-10 %, the Samsung
  part in stock is only 0.85 mm thick (worse DC bias).
- **TPS2553DBVR** (0 in stock until mid-December): AP22653W6-7 is a third of the price but only rated 3.0-5.5 V and
  Diodes AP2553W6-7 is NRND. TPS2553DBVT is the same die on a small reel (in stock, +0.16 USD each).
- **0603 green LED**: Kingbright APT1608CGCK is 2.7 cents cheaper but has a narrower viewing angle.
- **LMR33640ADDAR** (0 in stock, 26 weeks): no pin-compatible 4 A / 400 kHz part exists; the 1 MHz version
  LMR33640DDDAR is in stock and would need L1 = 3.3 uH (same footprint) - documented as plan B, not applied.

Cost per unit (DigiKey, 2026-11-11): see the cost summary in README.md.

## 11. Showcase animation (`/media`)

- Source geometry is only what the repository already contains as STEP: the KiCad board export
  (`hardware/outputs/voxhub_pcb.step`, placement of every part), the part models in `hardware/3dmodels` and the
  enclosure assembly (`enclosure/voxhub_assembly.step`). `step_to_glb.py` converts them with OpenCascade (XCAF reader ->
  glTF writer), keeping names and colours; Blender has no STEP importer of its own.
- KiCad's STEP export drops the colours of the part models. The Blender script therefore takes position and reference
  designator of each part from the board export and the coloured geometry from the part's own STEP model.
- The board surface (copper, solder mask, pads, silkscreen) is a texture composed from KiCad layer plots
  (`make_pcb_texture.py`); the STEP board is a plain slab.
- Choreography: the device is assembled upside down in reality (the PCB hangs under the top plate), so after the base
  plate has dropped away the upper half turns over and the PCB lifts out upwards, component side visible.
- Renderer: Cycles on the CPU, 4 samples per pixel + OpenImageDenoise, fixed noise seed, 3 bounces. EEVEE was tried
  first; without a GPU it runs through Mesa's software rasteriser and needs about 100 s per frame.
- The title is a text object parented to the camera (rendered, not composited), so the Blender script alone
  reproduces the video frame by frame.

## Open items - things a human must re-check

Closed in the second session (kept here so the history is visible):

1. ~~CM4 antenna corner~~ - checked against CM4 datasheet fig. 4, keep-out moved (log no. 1).
2. ~~CYPD3177 behaviour when the best in-range PDO has too little current~~ - it falls through to the next lower
   in-range PDO; no PDO at all -> 5 V, FAULT, switch off (section 2). A bench test with a 20 W, 30 W and 65 W charger is
   still part of bring-up, but the behaviour is no longer an unknown.
3. ~~LMR33640 5 V / 400 kHz table row~~ - 6.8 uH / 4 x 22 uF / 24.9k / 10 uF + 220 nF (log no. 2, 3).
4. ~~Mechanical dimensions~~ - Wurth 61400826021, JS202011JCQN and the speaker checked against the drawings, enclosure
   updated (log no. 9).
5. ~~MGM240P antenna keep-out~~ - identical to the Silicon Labs figure.
6. ~~USB skew~~ - all pairs matched, see hardware/outputs/routing_stats.txt.
7. ~~Stock and prices~~ - DigiKey is live. **Mouser is not** (see below).

Still open:

1. **Mouser stock and prices are not live** (bot protection, no API key). Re-check the Mouser column of the BOM by hand.
2. **Stock risks:** LMR33640ADDAR (0 at DigiKey, 26 weeks), MGM240PB32VNA3 (71 pieces, 30 weeks), CL31B106KBHNNNE and
   CL31A226KOHNNNE (0 at DigiKey), CM4104000 (576 pieces, 95 USD, purchase limit). Order these first or use the
   alternates named in the BOM.
3. **Documents read from mirrors** (manufacturer server refused the download): MGM240P Rev. 1.0 (Rev. 1.2 exists),
   Hirose DF40 and DM3AT, C&K JS (2022 edition), ADAU7002, MAX98357A Rev 7 / 13 (Rev 16 exists), USBLC6-2 (2008
   revision), SMBJ. Pin-outs and land patterns do not change between such revisions, but compare once with the current
   sheets. The Epson crystal's pad assignment was only seen in distributor copies.
4. **Dimensions scaled from drawings, not dimensioned:** USB-A flange lip (0.45 / 15.95 mm), speaker terminal position
   and yoke edge; the C&K drawing gives no body tolerance. A test print is still the first step.
5. **USB 2.0 data lines are matched single-ended 0.2 mm traces, not coupled pairs.** The 90 ohm target depends on the
   0.10 mm outer prepreg called out in the fab notes; measure on the first prototypes.
6. **Firmware consequences of revision A1:** the radio reset is active high on GPIO24, and RTS / CTS follow the Silicon
   Labs reference assignment (PA07 / PA08) - use an NCP / RCP build with that pin-out.
7. Nothing here has been powered on. Treat revision A1 as a prototype spin.
