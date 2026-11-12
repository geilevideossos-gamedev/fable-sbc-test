# Design decisions

Every non-obvious choice, with the reasoning behind it. Newest constraints first, then by subsystem.
"Verified against datasheet" means checked against the manufacturer document named in [section 9](#9-footprint--pin-out-verification-against-the-datasheets);
anything that could not be verified is called out in [Open items](#open-items---things-a-human-must-re-check).

## Two devices: hub and satellite (fourth session, 2026-11-12) - decision log

Goal: one Home Assistant system for the whole house with the two identical A2 boards in two roles. Device 1, the
**hub** (upstairs), runs Home Assistant OS, the Zigbee coordinator and the Claude assistant. Device 2, the
**satellite** (downstairs), has no Home Assistant of its own: it gives the hub its wake word, microphones, speaker,
mute switch and LEDs over Wi-Fi, and its radio runs Zigbee router firmware to extend the mesh to the ground floor.
Rules of the owner: no change to the PCB, the BOM or the JLCPCB order package; only software, documentation and the
shopping list change; no questions; no comments added to code or config files; commit after every milestone.

### Assistant architecture

| # | Decision | Why |
|---|---|---|
| S-1 | **Both devices are Assist voice satellites of the hub; every request goes through Home Assistant's own Assist pipeline with the official Anthropic conversation integration (Claude).** The VoxHub Assistant add-on is not extended to accept satellites; it stays in the repository as the single-device alternative and must not run next to the new hub satellite | Read in the Home Assistant source of release 2026.11.1 (`components/anthropic`, `components/llm`, `components/intent/llm.py`, `components/homeassistant/exposed_entities.py`, `components/esphome/assist_satellite.py`): the integration streams Claude's answer into Piper, executes its tool calls against Home Assistant (intent tools such as HassTurnOn / HassTurnOff / HassLightSet / HassClimateSetTemperature / media / timers / to-do, `GetLiveContext`, every exposed script as a tool; up to 10 rounds), offers the model, effort, thinking and prompt caching, and defaults to `claude-haiku-5-5` at effort `low` - the add-on's own settings. It adds what the add-on cannot do: several satellites, room awareness, timers, announcements, the pipeline debug view and updates by the Home Assistant project. Extending the add-on would have meant writing a second voice server next to the one Home Assistant already has |
| S-2 | **The lock / alarm rule is enforced by a VoxHub exposure guard on the hub**, because Home Assistant itself does not guarantee it. The guard runs in the hub add-on with the Supervisor's admin token, forces "not exposed to Assist" for every `lock.*` and `alarm_control_panel.*` entity and for every exposed scene, group or script that controls one (members in the `entity_id` attribute, script references from `search/related`, followed transitively), at start, after every entity registry change and every 5 minutes, and posts a notification when it had to change something. Protected domains are an option (default: lock, alarm_control_panel) | What Home Assistant guarantees: intent tools only reach exposed entities; locks and alarm panels are not exposed by default; there is no Assist intent for alarms. What it does not: a lock that someone exposes is unlocked by `HassTurnOff` without confirmation; scenes are exposed by default and a scene can unlock a lock or disarm an alarm; exposed scripts are tools that can do anything. The add-on's deny-list was the hard rule; the guard keeps it hard. The guard also reads every script's configuration (`script/config`): any lock or alarm action or entity in it (also through an area, a device or a template) or a call of such a script marks it (S-35). Remaining gap, documented: automations (sentence triggers, or an exposed helper that triggers an unlock) |
| S-3 | **Configuration rules for the Claude agent:** the conversation subentry uses only the "Assist" API (never the admin "Home Assistant" API, whose `call_action` is unrestricted); "Prefer handling commands locally" is off in the VoxHub pipeline; no sentence-trigger automation or intent script touches locks or alarms | With local handling on, Home Assistant's built-in agent answers simple commands before Claude sees them - the owner wants every request to go through Claude. The admin API would bypass exposure entirely. These are settings in the Home Assistant UI, so they are steps in `fab/ASSEMBLY_AND_TEST.md`, not code |
| S-4 | **Room awareness from the satellite's device area.** Each satellite device is assigned to its area (and optionally floor) in Home Assistant; the satellites are named after the room ("VoxHub Upstairs", "VoxHub Downstairs") | For every request the Assist API adds "You are in area <area> (floor <floor>) and all generic commands like 'turn on the lights' should target this area." (`intent/llm.py`, resolved from the request's `device_id`) and passes the area as the preferred area to the intent tools. Without an area Claude is told to ask which room. The area is set on the device, not on the satellite entity |
| S-5 | **Each device answers on its own speaker** | Home Assistant runs one pipeline per satellite and sends the answer only to the satellite that asked. Linux Voice Assistant does not announce the SPEAKER feature, so it receives the answer as a URL and plays it with mpv: the satellite must reach `http://<hub>:8123`. Home Assistant's "Local network" URL is therefore set to the hub's fixed address (DHCP reservation) |

### Satellite software (both devices)

| # | Decision | Why |
|---|---|---|
| S-6 | **Linux Voice Assistant (LVA) 1.1.18 is the satellite software on both boards** (tag `v1.1.18` = commit `b55d36af522c263eeed4e023d6ebf30da47e4710`) | wyoming-satellite, named in the task, is deprecated: its README now says it "has been replaced by Linux Voice Assistant that uses the ESPHome protocol". LVA is the Open Home Foundation's current satellite for Linux, runs microWakeWord locally, and supports timers, announcements, start / continue conversation, a stop word and a peripheral API for LEDs and buttons. Home Assistant discovers it through zeroconf (`_esphomelib._tcp`) and adds it with the ESPHome integration |
| S-7 | **Hub: own add-on "VoxHub Satellite"** (`assistant/voxhub_satellite`), built `FROM ghcr.io/ohf-voice/linux-voice-assistant:1.1.18` (the official multi-arch image), plus the VoxHub launcher, LED / mute bridge and exposure guard. Host network (zeroconf), Linux Voice Assistant bound to **127.0.0.1** (Home Assistant Core shares the host network; its zeroconf discovery accepts the loopback address), `audio: true`, `homeassistant_api: true`, `full_access` only for the LEDs and the switch | The Open Home Foundation's "Assist Satellite" app is not in the official add-on store yet, has no access to `/sys/class/leds` or `/dev/input`, passes its `mic_volume` default 1.0 where LVA expects 1-100, and its discovery step waits on a port LVA never opens. Building on the official LVA image keeps the satellite code identical to the one on device 2 |
| S-8 | **Satellite: LVA from the git tag in a Python virtual environment, PipeWire as sound server under a lingering `voxhub` user, LVA as that user's systemd service; the VoxHub launcher picks the googlevoicehat source and sink by name** | LVA is not on PyPI; every dependency has an aarch64 wheel, so nothing is compiled. LVA captures through PulseAudio (soundcard) and plays through mpv, i.e. it needs PulseAudio or `pipewire-pulse`; the LVA docs prescribe PipeWire with linger on headless systems. A native install needs less RAM than Docker on a 1 GB module |
| S-9 | **Microphone level: the sound server's source volume does the gain (option `mic_gain`, default factor 4 = +12.04 dB, passed to `pactl` as an absolute linear factor, e.g. `4.000000`), LVA's `--mic-volume` is fixed at 100, capture is mono (`--audio-input-channels 1`)** | The PDM microphones deliver speech far below full scale (the add-on recommended a gain of 4 to 8). PulseAudio's percent scale is cubic: "400 %" would be a factor of 64 (+36 dB) - the container test caught the first version doing exactly that; a signed dB value such as "+12.04dB" is a relative change and added 12 dB at every start - found by the review (S-34) LVA's mic volume only attenuates and is reset at every start. With two channels LVA would send the second microphone to Home Assistant as an echo reference, which it is not; with one channel the sound server mixes both microphones |
| S-10 | **LEDs and mute switch through LVA's peripheral WebSocket API** (`voxhub_satellite/bridge.py`): green = idle, blue = listening, blinking blue = thinking, green + blue = speaking, both off = muted (the red LED is wired to the switch), slow green blinking = no connection to Home Assistant, fast blinking of both = pipeline error (2 s), alternating = timer ringing. The hardware switch sends `mute_mic` / `unmute_mic` and is re-asserted after every reconnect and whenever Home Assistant unmutes while the switch is in the mute position | Same LED language as the add-on. LVA has no GPIO input of its own and forgets its mute state at restart and while Home Assistant is disconnected. The switch disconnects the microphone data line in hardware anyway; the bridge only makes Home Assistant and LVA see it, so that no audio is streamed and the device shows as muted |
| S-11 | **The hub's address, set at build time, is the firewall rule of the satellite: port 6053 only accepts the hub, port 6055 (peripheral API) only the satellite itself; `voxhub-hubwatch` re-resolves the address every minute and logs when Home Assistant's web server is not reachable** | LVA's ESPHome API is plain text without password or key, and the newest client on port 6053 receives the microphone audio - anybody in the Wi-Fi could listen in after a wake word. The peripheral API has no authentication either. The hub's web server is also the source of every spoken answer (S-5). On the hub the same port is closed to the network by binding Linux Voice Assistant to 127.0.0.1 (S-7, S-36) |

### Verification of the hub add-on

| # | Decision | Why |
|---|---|---|
| S-18 | **Verification of the hub add-on:** 51 unit tests (guard against a fake Home Assistant websocket, bridge against a fake peripheral API, LEDs on a fake sysfs, mute switch on a pipe, launcher, options against `config.yaml` and the translations) and a container run (`assistant/tests/container/run_addon_test.sh`): the add-on image is built from the official LVA image, started next to a PulseAudio container with sources and sinks named like the googlevoicehat card, and driven by a real ESPHome API client (aioesphomeapi): device info, LVA's entities, LEDs idle / muted / idle / slowly blinking as "Home Assistant" connects, mutes, unmutes and leaves, +12.04 dB on the source, unchanged after a restart, Linux Voice Assistant reachable only on 127.0.0.1 - 7 of 7 client checks plus the gain and loopback checks | No Home Assistant OS, no hardware: the Supervisor's audio, the real sound card, the LEDs and the mute switch on the board are not part of it |

### Zigbee radio

| # | Decision | Why |
|---|---|---|
| S-12 | **`tools/flash_zigbee.sh --role hub` writes the coordinator (Z-Stack 20250321, as before), `--role satellite` the router: Koenkk Z-Stack 3.x.0 router 20250403 for `CC1352P2_CC2652P_launchpad`** (release asset `Z-Stack_3.x.0_router_20250403`, zip SHA256 `86bf0527fbc70b76df9144fcf6b3a80e18d69aa1eb5ab24bc48a2bb9fcdee9c2`, hex SHA256 `47e5043e994f8b540a1e29446b7ec0019de12f7255b7897823fbdd5a4875bb7f`). Without `--role` the script picks `satellite` on the VoxHub satellite image (marker `/etc/voxhub/satellite.env`) and `hub` everywhere else | The launchpad build uses the same RF configuration as the coordinator that runs on the RF-BM-2652P2 (DIO28 / DIO29 RF switch, DIO30, high-power PA, `LAUNCHPAD_CONFIG` in Koenkk's patch) and keeps the boot-loader backdoor on DIO15 active low (`CCFG BL_CONFIG C5 0F FE C5`, checked by the script before every write). It reports itself as `TexasInstruments` / `ti.router`, transmits at 9 dBm and starts network steering once, right after every start without a network: the hub's network has to be open first, then the router is restarted or `--rejoin` is used. Koenkk's router 20250403 and the coordinator 20250321 are built from the same SDK 8.30.01.01 with identical RF, CCFG and driver files |
| S-13 | **The router is verified by the boot loader's CRC32 check**, not by a probe: after writing (`cc2538-bsl -v`), and to find out whether it is already installed by comparing only the ranges the image programs (code 0x00000-0x2FD48, CCFG 0x57FA8-0x58000) in one boot-loader session (`compare_flash.py`, built on cc2538-bsl's classes; S-33). After the restart the script checks that nothing answers as Z-Stack or OpenThread | Koenkk builds the router from TI's `zr_genericapp` with `CUI_DISABLE`: it has no serial interface at all, so the coordinator's ZNP probe cannot work |
| S-14 | **`--role satellite --rejoin`** holds GPIO25 (DIO15) low for 0.5 s while the radio runs | In the router firmware a click on BTN-1 (DIO15) or BTN-2 (DIO14) sends a leave request, clears the network state and restarts - the documented "factory reset" of a Koenkk router. On this board DIO15 is the boot strap line, so the CM4 can press the button; DIO14 is unconnected; the router's sysconfig enables the internal pull-up of both button pins (`Button1/2.gpioPin.pull = "Pull Up"`), so an open DIO14 cannot trigger the reset. Removing the router in ZHA has the same effect (leave, reset after 5 s, one new search) |
| S-15 | **`--role satellite` is refused on Home Assistant OS unless `--force` is given** | Run on the hub by mistake it would replace the coordinator and erase the Zigbee network stored in the radio |
| S-16 | **Optional local copies of the downloads** (`VOXHUB_RADIO_CACHE`, default `/usr/local/share/voxhub/radio`, files named by their SHA256): the satellite image carries cc2538-bsl and the router firmware, so the radio can be flashed without internet | A copy is only used if its checksum matches; otherwise the script downloads as before |
| S-17 | **The flashing script is tested against a radio simulator** (`tools/test/radio_sim.py`, `tools/test/run_flash_tests.sh`): a TCP serial port that implements the CC26xx ROM boot loader commands cc2538-bsl uses (sync, chip id, memory read, bank / sector erase, download, send data, CRC32, reset), Z-Stack's SYS_PING / SYS_VERSION, an OpenThread version answer, a silent router and the router's button; GPIO24 / GPIO25 are read from the script's GPIO simulation files. 54 checks, all passing: both roles, blank / coordinator / router pre-installed (the simulated firmware writes its NV area at its first start), automatic role, rejoin, refusals, dry run, probe-only, Thread, hub over router, local firmware copies | The simulator of revision A2 was not part of the repository. The real cc2538-bsl writes the real images into the simulated flash and checks the CRC, so the address and checksum handling is exercised for real; timing, the real boot loader and the GPIO drivers are not |

### Satellite image (`os/satellite`)

| # | Decision | Why |
|---|---|---|
| S-19 | **Base: Raspberry Pi OS Lite 64-bit `2026-10-06-raspios-trixie-arm64-lite` (Debian 13), pinned by its SHA256** `483db18a48da399b5b7022ffae9a07bc6d99daab30e593aedac09b69ff422843` (downloads.raspberrypi.com) | The current Lite release (Raspberry Pi Imager lists it as "Raspberry Pi OS Lite (64-bit)"). It carries the same Raspberry Pi kernel and the same stock overlays as Home Assistant OS (`googlevoicehat-soundcard`, `uart4`, `gpio-led`, `gpio-key`), so the satellite gets exactly the hub's `config.txt` block (`os/config/config-voxhub.txt`); kernel and firmware updates come from the Raspberry Pi archive. A smaller OS would need its own board support |
| S-20 | **Everything is installed into the image at build time** (loop device, chroot, aarch64 programs through qemu-user-static / binfmt_misc): packages, Linux Voice Assistant, VoxHub code, settings. The first boot needs no internet | The image can be checked before it is written (S-27), and the satellite works on its first start |
| S-21 | **No cloud-init, no first-boot dialog: the image's placeholder user `pi` (uid 1000) is renamed to `voxhub` at build time with Raspberry Pi's own `userconf`**; `cloud-init.disabled`, `userconfig` off, SSH on, host keys generated at the first boot (`regenerate_ssh_host_keys`, machine-id empty) | This Raspberry Pi OS configures the first boot through cloud-init (NoCloud on the boot partition). With an empty user-data its `users_groups` module would create the default user `pi` again next to `voxhub`, and the user dialog would wait on tty8. Doing it in the image is deterministic and is the same rename Raspberry Pi's tools do |
| S-22 | **Wi-Fi: NetworkManager keyfile (mode 600), `cfg80211.ieee80211_regdom=<country>` on the kernel command line, `WirelessEnabled=true`** | The image ships with `WirelessEnabled=false` in NetworkManager's state file: Raspberry Pi OS keeps the radio off until a Wi-Fi country is set. These are the files `raspi-config nonint do_wifi_country` changes; the tool itself would also call `rfkill` on the build machine |
| S-23 | **Package sources switched to https** (deb.debian.org, archive.raspberrypi.com) | Both serve https. The build environment of this session only allows https through a proxy; on a normal network it changes nothing. HTTPS_PROXY and a CA file (SSL_CERT_FILE / VOXHUB_CA_CERT) are passed into the chroot only while it builds |
| S-24 | **Automatic updates: unattended-upgrades daily for Debian, Debian-Security and the Raspberry Pi archive (`origin=Raspberry Pi Foundation`, read from its Release file), automatic reboot at 04:30 when needed.** Linux Voice Assistant is pinned to its git tag, its Python packages to the versions of the verified build (`os/satellite/lva-constraints.txt`); they change only with a new image | The kernel and firmware of Raspberry Pi OS come from the Raspberry Pi archive, so security updates must include it. Debian's own default only covers Debian. Python packages from PyPI have no security channel; pinning keeps the tested combination |
| S-25 | **The boot partition is copied out with mtools and written back when the build machine cannot mount FAT** | This session's kernel has no vfat driver; on a normal Linux PC the partition is mounted. Only changed files are written back |
| S-26 | **The root partition is grown by 1.5 GiB in the image**; Raspberry Pi OS's own `resize` at the first boot still extends it to the card | Room for the packages (PipeWire, mpv, Python venv) during the build |
| S-27 | **The build checks the finished image**: config.txt block, every stock overlay present, the VoxHub overlay applies to the image's `bcm2711-rpi-cm4.dtb`, Wi-Fi files and country, user, linger, cloud-init and dialog off, no SSH host keys, services enabled, PipeWire user units, unattended-upgrades dry run, LVA version and commit, `linux_voice_assistant --help` and the VoxHub modules start in emulation, the launcher reads the settings, wake word model present, offline radio flashing dry run with the role detected, systemd accepts the units | Everything that can be checked without the board |

### Shopping list

| # | Decision | Why |
|---|---|---|
| S-30 | **Satellite module: CM4101000 (CM4 Lite wireless 1 GB) from Reichelt.at, `RPI CM4W 1GBLITE`, 50.82 EUR, in stock** - in the Reichelt.at parcel that carries the hub's parts anyway | Cheapest wireless Lite module that is in stock and delivered to Austria (read 2026-11-12, 12:45-12:56 UTC): BerryBase.at 51.00, Welectron 49.90 + 9.90 shipping (German VAT shown), DigiKey 49.27 + 25.00 shipping, Semaf 35.70 not in stock. Linux Voice Assistant states 512 MB and 1 GHz as its minimum and recommends a Pi Zero 2 W; speech recognition and Claude run on the hub. The 2 GB module (69.00) brings nothing the satellite needs. Not measured on the board |
| S-31 | **Satellite card: SanDisk Ultra 32 GB A1 (BerryBase.at 17.90 EUR) instead of the 64 GB endurance card** | The satellite image needs about 5 GB and the satellite writes little (journal limited to 64 MB, no database); 11.00 EUR less. The endurance card stays the hub's choice (Home Assistant writes around the clock) |
| S-32 | **Combined basket hub + satellite: still two parcels (Reichelt.at + BerryBase.at), 286.90 EUR delivered** (`fab/SHOPPING_LIST.md`, section 8.3), 66.01 EUR less than two hubs; all other lines identical for both devices, including the 30 W charger | The board needs a 9-20 V PD profile with 2 A in either role; one article list keeps the order simple. BerryBase.at stays below its 200 EUR free-shipping line either way. The new section 8 is appended so that the section numbers other documents refer to stay valid |

### Independent review of the two-device work (three reviewers: flashing script, satellite code, documentation)

| # | Finding (severity) | What was done |
|---|---|---|
| S-33 | **Router check would erase the router on every re-run (high).** The first version asked the boot loader for a CRC over the whole flash, which includes the router's NV area (0x50000-0x56000, written by the firmware at its first start), so on hardware it could never match | Only the programmed ranges are compared (S-13). The simulator now writes NV at the first firmware start and ignores that area when it identifies the image; the "router installed: nothing written" test covers the real case. `--rejoin` refuses when the router firmware is not on the chip; the simulator no longer reports a stale button press |
| S-34 | **Microphone gain grew by 12 dB at every start (high):** `pactl set-source-volume +12.04dB` is relative | Absolute linear factor (S-9); the container test restarts the add-on and checks +12.04 dB again |
| S-35 | **Guard missed scripts that call a lock / alarm script (high), and scenes were judged by the scripts that call them (low)** | `script/config` of every script is walked (S-2); scenes use only their entity references |
| S-36 | **Hub port 6053 open to the network (high):** any connection takes over Linux Voice Assistant's audio and makes the hub deaf | Linux Voice Assistant on the hub listens on 127.0.0.1 only (S-7); manual fallback in the guide: ESPHome host `127.0.0.1` |
| S-37 | **Bridge (medium / low):** a switch released while Home Assistant was away left the satellite muted; LEDs kept an old phase after a reconnect; LVA's per-connection `disconnected` was taken as global | The bridge remembers that it muted LVA and unmutes on reconnect; snapshot and `disconnected` reset the phase; after `disconnected` it reconnects to the peripheral API to read the real state |
| S-38 | **Add-on stopped with an empty protected list (medium); IPv6 hub address left the firewall closed (low)** | The guard task only starts with protected domains; the build script accepts IPv4 addresses and host names only, hubwatch logs an error while it has no IPv4 address |
| S-39 | **Documentation (medium / low):** add-on repository without the branch, satellite microphone test played only MK1 at a lower level, `VOXHUB_ROOM` / `VOXHUB_WAKE_WORD` described as changeable, wrong cross references, test counts, quick-start commands, privacy sentence, satellite order of work | All corrected in `fab/ASSEMBLY_AND_TEST.md`, `README.md`, `os/satellite/README.md`, this file and `TODO.md`. The shopping list arithmetic of section 8 was recomputed by the reviewer: all correct |
| S-40 | **Satellite image builder: the first build's own checks failed** (absolute enable symlinks tested with `-e` on the build host, `$` in the shadow regex, LVA `--help` needs a sound server, the unattended-upgrades dry run does not finish in emulation) | Checks fixed; the image is checked again by a separate runtime test (`os/satellite/test-satellite-image.sh`, `os/README.md`) |

## Revision A2 (third session, 2026-11-12): orderable at JLCPCB - decision log

Goal of this revision: the owner orders fully assembled boards from JLCPCB (5 PCBs, 2 assembled, delivery to Austria),
prints the enclosure, plugs in the CM4 and screws the device together - no soldering anywhere. Rules given for the
work: every part in stock at LCSC / JLCPCB, never a lower voltage, current or temperature rating than the A1 part,
Basic or Preferred parts for passives where possible, every "before a production spin" layout item fixed, ERC and DRC
at zero including JLCPCB's rules, at most two review rounds, no questions, no comments added to code or config files.

### Parts

| # | Decision | Why |
|---|---|---|
| A2-1 | **JLCPCB's assembly library is the primary source of every BOM line.** `hardware/gen/jlc_lookup.py refresh` reads LCSC number, library type, JLCPCB stock, LCSC stock and prices live into `gen/sourcing_jlc.json` (last run 2026-11-12); the BOM is built from that file and fails if a line has no live data. The DigiKey data of 2026-11-11 stays in the BOM as the second source; the Mouser columns are gone | "In stock" has to mean "JLCPCB can place it today", and that is only visible in the assembly library, not at a distributor. Mouser was never readable (A1 open item) - a column of guessed part numbers is worse than no column |
| A2-2 | **The five lines A1 reported as out of stock were out of stock at DigiKey, not at JLCPCB.** LMR33640ADDAR (C2836966, 2,490), TPS2553DBVR (C55266, 53,887), 2N7002,215 (C65189, 204,304), the 10 uF 50 V X7R 1206 CL31B106KBHNNNE (C89632, 472,067) and the 220 nF 50 V X7R GRM188R71H224KAC4D (C669503, 4,056) keep their part numbers. The 22 uF 1206 becomes CL31A226KAHNNNE (25 V instead of 16 V, Basic, 2.5 million) | A part that is in stock where the board is assembled needs no substitute; changing the buck regulator or its input capacitors for no reason would only add risk. Footprints and layout of these parts are unchanged |
| A2-3 | **Radio module: Silicon Labs MGM240PB32VNA3 -> RF-star RF-BM-2652P2 (TI CC2652P, +20 dBm, PCB antenna), LCSC C5440064.** New footprint (16.5 x 30 mm, 30 castellated pads, checked pad by pad against RF-star's drawing and against JLCPCB's own footprint), new symbol, antenna keep-out moved, module at the front edge | MGM240PB32VNA3: 0 at JLCPCB and LCSC, the PB22 variant 12 pieces. No EFR32MG24 module with an antenna is stocked. The CC2652P is the other coordinator family Home Assistant supports first-class (ZHA "ZNP", Zigbee2MQTT "zstack", OpenThread RCP) and the RF-BM-2652P2 is the module of the common ZigStar / cod.m / Sonoff-P coordinators, so Koenkk's `CC1352P2_CC2652P_launchpad` firmware runs unchanged |
| A2-4 | **Consequences of the radio change in the circuit:** UART4 TX / RX only (the firmware uses no flow control; CTS / RTS stay wired to DIO18 / DIO19 but are not configured), GPIO25 = boot-loader backdoor DIO15 (active low), reset through the same open-drain 2N7002 (GPIO24 high = reset) with a 100k pull-up, 4-wire JTAG instead of SWD: TMS GPIO22, TCK GPIO23, TDO GPIO17, TDI GPIO7; Tag-Connect J8 carries cJTAG | The CC2652P has a ROM serial boot loader, so the normal flashing path needs no debug probe at all. JTAG from the CM4 is the recovery path for a module delivered with a firmware that has the backdoor disabled |
| A2-5 | **Pull-up on the boot-loader strap: 2.2k instead of 10k** | GPIO25 powers up with the CM4's internal pull-down (33 to 73 kOhm). Against 10k the strap sits at 2.53 to 2.90 V, the CC2652P guarantees a high from 0.8 x VDDS = 2.64 V. With 2.2k the worst case is 3.09 V; the CM4 sinks 1.5 mA when it pulls the strap low |
| A2-6 | **Microphones stay IM69D130V01** (JLCPCB lists it as C536262, 427 in stock). Alternate with the same footprint: IM73D122V01XTMA1 | In stock; no reason to touch the acoustic design. Bottom-port microphones must not be washed: "MIC - NO WASH" is on the silkscreen next to both and in the order remark |
| A2-7 | **ADAU7002ACBZ-R7 is kept although only 104 pieces are in stock** (rule: fewer than 200 = replace) | There is no other PDM-to-I2S converter in the JLCPCB library and I2S-output MEMS microphones in a bottom-port package are end-of-life or not stocked. 104 pieces against a need of 2; the order guide says to buy the part into the JLCPCB parts library before ordering |
| A2-8 | **Stacked USB-A (Wurth 61400826021, 116 pieces) and SMT spacers (Wurth 9774015151R, 230 pieces) are kept.** Checked fallback for the USB-A: Jing Extension 907-112A1022D10200 (C29780026, 2,959 pieces) fits the hole pattern within 0.12 mm and passes the enclosure window | Both are the parts the enclosure and the CM4 stacking height were verified against. Need: 2 and 8 pieces |
| A2-9 | **Passives:** resistors are UNI-ROYAL 0402WGF 1 % (9 Basic values; 150 ohm, 2.4k, 49.9k, 150k, 470k are Preferred Extended; 24.9k - the buck feedback resistor - is Extended). Capacitors are Samsung / Yageo / Murata / Fenghua. Two capacitor lines are Extended on purpose: 1 uF 25 V X7R 0603 (CL10B105KA8NNNC) and 4.7 uF 25 V X5R 0603 (CL10A475KA8NQNC) | The Basic 1 uF 0603 is X5R (lower temperature class than the A1 X7R part), the Basic 4.7 uF 0603 is 16 V (A1: 25 V). "Never downgrade" wins over the fee. In a Standard PCBA order the fee per part type is the same for Basic and Extended anyway (see A2-29) |
| A2-10 | **Inductor: Bourns SRP7028A-6R8M (0 at JLCPCB) -> Sunltech SLO0630H6R8MTT** (6.8 uH, Irms 4.5 A, Isat 8 A, 54 mOhm max, -55..+150 C, 7.1 x 6.6 x 3.0 mm) on the unchanged pads | Same inductance, currents and temperature range, lower DCR. The better-known Vishay IHLP2525CZ-01 is limited to 125 C and would have been a downgrade |
| A2-11 | **Polymer capacitors T520B107M006ATE070 -> T520B107M006ATE040**, Zener SZMM3Z10VT1G -> MM3Z10VT1G, TVS / ESD diodes / USBLC6 as the listings of the original manufacturers | 40 mOhm instead of 70 mOhm, same case and ratings. The AEC-Q101 Zener has no footprint record in JLCPCB's library (the placement preview would be blind); the commercial part is the same die |
| A2-12 | **Status LEDs D7 (green), D8 (blue), D9 (red): ordinary 0603 LEDs on the top-facing side of the board** (KT-0603G, KT-0603B, LTST-C191KRKT) instead of reverse-mount 1206 LEDs shining through slots. Series resistors chosen for similar brightness: green 5.1k and blue 2.2k from 5 V (0.5 and 1 mA), red 150 ohm from 3.3 V (about 9 mA) | The Wurth reverse-mount LEDs are not stocked and JLCPCB's support for reverse-mount parts is marginal. The side of the board that faces the top cover already carries the mute switch, so the second assembly side costs nothing extra. The light pipes of the enclosure are bores at the same positions - an LED on the surface sits inside the same bore. The three NPTH slots are gone |
| A2-13 | **D4 (red, PD fault): Lite-On LTST-C191KRKT instead of the JLCPCB Basic KT-0603R** | The Basic part is rated 25 mA / 40 mW, the A1 part 30 mA / 75 mW |
| A2-14 | **Crystal: Epson TSX-3225 24 MHz CL 18 pF -> YXC X322524MOB4SI, CL 12 pF, +-10 ppm; load capacitors 27 pF -> 15 pF** | The Epson part is not stocked. 2 x (12 pF - about 4.5 pF stray) = 15 pF. Frequency tolerance and temperature range are the same |

### Layout

| # | Decision | Why |
|---|---|---|
| A2-15 | **The power stage and the USB lines are no longer autorouted.** `hardware/gen/prewire.py` holds hand-designed copper as coordinates relative to the pads; `build_pcb.py` lays it locked before the autorouter runs, the autorouter and the repair loop treat it as fixed | Every "before a production spin" item of A1 was a consequence of letting an autorouter decide where current flows. Hand-designed copper is reviewable, reproducible and survives every re-route |
| A2-16 | **PGND of the buck (U2 pin 1) is tied to the exposed pad with a 0.55 mm track on the component side and has its own vias**; C10 (220 nF) connects to PGND with a 0.5 mm track, C8 / C9 / C10 / D1 / C1 / C2 / C11 and the output capacitors each have their own ground vias; 8 ground vias within 6 mm of U2 | A1 left PGND to a thermal spoke of the pour. The hot loop VIN - C10 - PGND is now closed on one layer with defined copper |
| A2-17 | **VBUS and VBUS_SW widened**: connector contacts to a 1.6 mm bar at the TVS, 1.2 mm to the load switch, 1.2 to 1.6 mm from the load switch to the input capacitors, 1.6 mm switch node and 5 V output, 0.8 mm to each USB-A port. `gen/check_power.py` measures the narrowest copper of every high-current path with a morphological opening of the real copper and fails the build below the requirement; result in `hardware/outputs/power_paths.txt` | A1: a 0.4 mm track of 19 mm with two vias carried the whole input current. Requirement = IPC-2221 width for the load current at 20 K rise; the remaining necks are the 0.6 mm pads of the connector and of the regulator themselves |
| A2-18 | **No via inside or touching a lead pad.** The fan-out places a via at least 0.1 mm clear of its own pad and, for fine-pitch leads, only outward of the lead; ground leads next to an exposed pad get a track into the pad instead of a via. Vias inside exposed pads remain (thermal) | A1 had two fan-out vias inside QFN lead pads (U1 pin 19, U10 pin 7) - solder thieves |
| A2-19 | **All via drills 0.3 mm (pads 0.5 and 0.6 mm)** | JLCPCB's free tier is "0.3 mm hole / 0.45 mm pad"; the 0.25 mm drills of A1 fall into a class that can cost 38 USD |
| A2-20 | **Stack-up JLC04161H-3313** (1 oz outer, 0.0994 mm 3313 prepreg, 1.265 mm core with 0.5 oz, mirrored), written into the board file | Free at JLCPCB (the 7628 default would need 0.3 mm wide pairs, 1080 and 2116 cost extra) and thin enough for a 90 ohm pair that fits between 0.4 mm pitch pads |
| A2-21 | **USB geometry from JLCPCB's own impedance calculator: pair 0.14 mm / 0.16 mm gap = 89.96 ohm, single line 0.185 mm = 45.2 ohm** (`gen/jlc_impedance.py` queries the calculator, result in `hardware/outputs/usb_impedance.txt`) | The A1 values (0.17 / 0.16 and 0.20 mm) came from a formula without solder mask and give 82.5 and 43.4 ohm in the calculator. JLCPCB builds to its calculator, so its numbers count |
| A2-22 | **Upstream pair (CM4 to hub, 31.8 mm): a real coupled pair for 90 % of its length (28.6 mm at 0.16 mm gap; the rest is the fan-out at the hub, the compensation bump and the entry into the socket pads), length-matched with a bump on the inner line. Downstream lines (hub - ESD - USB-A, 10.8 and 16.2 mm): two uncoupled 45 ohm lines per port, matched to 0.00 mm** | Feasible where the pins allow it. The USB-A pins are 2.0 mm apart and the SOT-23-6 pads of the flow-through ESD part 1.9 mm, so a downstream pair would be coupled for only a few millimetres between two fan-outs; two matched 45 ohm lines have the same 90 ohm differential impedance and no impedance step at each fan-out. At 480 Mbit/s the bit is 31 cm long on FR-4; a 16 mm run is electrically short. Skew 0.00 mm against a limit of 3.8 mm, no vias, no stubs (`routing_stats.txt`) |
| A2-23 | **JLCPCB's design rules are part of the project:** board rules in `gen/project_settings.json` (track / space 0.09 mm, via 0.45 / 0.3 mm, ring 0.075 mm, hole to hole 0.2 mm, hole to copper 0.2 mm, copper to edge 0.2 mm, silkscreen 0.15 mm line / 1.0 mm height / 0.15 mm to pads) and six custom rules in `hardware/voxhub.kicad_dru` (component hole to component hole 0.45 mm, component hole to copper 0.28 mm and 0.30 mm on inner layers, component hole ring 0.15 mm, non-plated hole 0.5 mm, pad to pad 0.15 mm). Every DRC check that was a warning is an error now; the only waived checks are the two library-comparison checks | "DRC clean" has to mean clean against the factory's limits. The numbers are from JLCPCB's capability page as read on 2026-11-12. The design keeps its own, stricter net-class clearances (0.12 / 0.15 mm) |
| A2-24 | **Hirose's "no pattern other than the same circuit" strips at the CM4 sockets are keep-out areas** (between 0.75 and 1.19 mm from each connector centre line, one area per run of pads that does not use its strip); the fan-out of power pins runs straight through its own strip and jogs only in the centre channel; `gen/check_df40.py` fails the build on foreign copper there (`hardware/outputs/df40_strips.txt`) | Found when the DF40 drawing was read from hirose.com: A1 had three foreign tracks and the ground pour inside these strips. The connector's contact tails rest on the solder mask there |
| A2-25 | **Paste aperture of the DF40 pads 0.17 x 0.67 mm (81 %)** | Hirose: 80 % at a 0.12 mm stencil; too much paste wicks into a 0.4 mm pitch contact. (JLCPCB designs its stencil from its own library unless "user-specified stencil" is ordered - the paste layer documents the intent) |
| A2-26 | **Silkscreen:** legends are placed by an occupancy search (never over pads, vias, holes, other text or the edge), footprint silk closer than 0.3 mm to the edge is trimmed, minimum text height 1.0 mm; `silk_overlap`, `silk_over_copper` and `silk_edge_clearance` are errors. The URL text that sat on C17 is placed by the same search | A1 waived five cosmetic checks (10 warnings). Zero is easier to keep than "ten known ones" |
| A2-27 | **Fabrication outputs in the form JLCPCB documents for KiCad 9:** Protel file extensions, solder mask subtracted from silkscreen, Excellon in mm with decimal zeros, PTH and NPTH in two files, oval holes as routed slots | Removes guessing at the upload step |

### Order package, mechanics, firmware

| # | Decision | Why |
|---|---|---|
| A2-28 | **CPL rotations are computed, not looked up.** `gen/make_jlc.py` fetches JLCPCB's own footprint of every LCSC part (`gen/jlc_footprints.json`), fits its pads onto the board's pads (by pad number, by polarity pin names for two-pin parts, by geometry for symmetric parts) and writes the rotation and the centre offset that make them coincide; top = counter-clockwise seen from the top, bottom = mirrored footprint seen through the board. `fab/jlcpcb/placement_report.csv` lists the fit of every placement | Rotation tables go stale and know nothing about new footprints. 135 of 136 placements fit JLCPCB's footprint with at most 0.36 mm pad offset; the one without a footprint record is the hand-soldered USB-A connector, which only fits one way |
| A2-29 | **Order options** (details and prices in `fab/ORDER_GUIDE.md`): Standard PCBA on both sides, ENIG, stack-up specified, no paid impedance test, vias epoxy filled and capped, edge rails and fiducials by JLCPCB on the two 74 mm edges, "Confirm Parts Placement", Board Cleaning = "Caution for Special Parts" (the microphones must not be washed) | Standard PCBA is the only type that takes a double-sided board and 0.4 mm pitch parts; ENIG is required for the 0.22 mm pads of the WLCSP. In Standard PCBA every part type costs the same feeder fee whether Basic or Extended. The paid +-10 % impedance option (33 USD) adds a test coupon, not a different board. Filled vias (21 USD) keep solder from wicking into the thermal vias of the exposed pads - cheap insurance on a board nobody will rework |
| A2-30 | **Speaker: Adafruit 3351 (enclosed, 3 W 4 ohm, JST-PH plug) instead of the Same Sky CMS-4017-34SP.** The enclosure has a rectangular locating frame (71.3 x 31.9 mm) and an oblong grille instead of the round ring, a flat pedestal with a foam pad under the speaker box, no bass relief holes | The Same Sky speaker has solder terminals; no round 40 mm speaker with a JST-PH plug is sold by any shop that was searched. The enclosed speaker plugs into J7 as delivered |
| A2-31 | **Screws: M2.5 machine screws (8 x M2.5 x 5, 4 x M2.5 x 8) in the 2.1 mm pilot holes; feet 8 mm; heat sink 14 x 14 x 7 mm with adhesive foil** | Thread-forming screws for plastic in 2.5 mm are sold to businesses only. An M2.5 screw forms its thread in a printed 2.1 mm hole. The "SJ5003 class" feet of A1 are 11 mm and do not fit the 8.6 mm recesses |
| A2-32 | **Radio flashing: `tools/flash_zigbee.sh`, one command without arguments.** It downloads Koenkk's Z-Stack coordinator 20250321 (SHA256 pinned), refuses an image without the DIO15 backdoor, enters the ROM boot loader through GPIO25 / GPIO24, writes and verifies with cc2538-bsl, falls back to OpenOCD bit-bang JTAG if the boot loader does not answer, restarts the radio and checks that the firmware answers. `--thread` writes the OpenThread RCP | The owner has no debug probe. On Home Assistant OS the script re-runs itself in a temporary Debian container. Tested against a simulated radio with the real flashing tool; not on hardware |
| A2-33 | **OS configuration: `dtoverlay=uart4` without `ctsrts`; ZHA radio type ZNP, 115200 baud, no flow control** | Follows A2-4 |
| A2-34 | **KiCad 9.0.9 runs natively in this session (`KICAD_NATIVE=1 hardware/build.sh`)**; the Docker path is unchanged. The interpreter must import pcbnew, numpy and shapely | No Docker daemon here. Schematic, placement, routing and all outputs were regenerated from code; a full place + route + output run takes about 6 minutes |
| A2-35 | **"No comments" rule:** new files have no comments or docstrings (usage is in the READMEs); in existing files no comment was added, existing ones were corrected or removed where the code under them changed | The owner's rule for this session |
| A2-53 | **Showcase video and exploded still are not re-rendered for A2; they show revision A1** | The owner decided to skip the three-hour render. The pipeline was checked against the A2 files (model conversion, board textures, test stills of the closed and the exploded device with the enclosed speaker and the new radio module); `media/render_showcase.py` gives the enclosed speaker a plain black plastic material. `media/build_showcase.sh` renders the A2 version when wanted |

### Review round 1: six independent reviewers on the changed areas

Each reviewer got one area, the repository and the research notes, but not the author's conclusions, and had to prove
every finding with its own measurement (own board parsers, own geometry scripts, live lookups, the manufacturers'
documents). Result: **no high finding** (nothing that stops the board from working or from being built), 10 medium,
30 low; every finding was checked against the board before it was acted on.

| # | Area | Finding (severity) | What was done |
|---|---|---|---|
| A2-36 | Power | A locked ground via of C9 sat half inside the 0603 pad C5.2; ground vias placed by the autorouter overlapped the pads of the SMT spacers and of the microphone ground rings (medium) | The via is moved clear of the pad; spacer and microphone rings get a scripted stub and via outside the pad; a same-net via may only overlap the exposed pad of an IC. New build gate `gen/check_vias.py` (`hardware/outputs/via_in_pad.txt`) |
| A2-37 | Power | The test pads for VBUS and VBUS_SW were fed by 0.4 mm tracks of 70 mm across the bottom layer, through the pin field of the hand-soldered USB-A connector and next to the 3.3 V and 5 V test pads (medium) | The two pads are removed: the charger voltage is measured on the large pads of D1 and C8 / C9 (`fab/ASSEMBLY_AND_TEST.md`). The remaining pads (+5V, +3V3, GND) are labelled on the silkscreen. The nets that carry the charger voltage (VBUS, VBUS_SW, PD_GATE, PD_FET_EN) form the net class "HV" with 0.20 mm clearance and 0.25 mm taps into the 0.25 mm pads of the PD controller |
| A2-38 | Power | Thermal pad of the buck regulator connected through thermal-relief spokes; report `power_paths.txt` understated two pin currents and did not say what "requirement" means (low) | Exposed pad, thermal vias and PGND pin are connected solid; the report states the RMS pin currents (3.0 A VIN at 9 V in, 3.5 A PGND at 20 V in), its criterion and the via counts |
| A2-39 | USB | Two of the hub's six 3.3 V pins had their capacitor 16 and 47 mm of track away (medium) | Three capacitors have fixed places at the pins and locked copper: C35 at pin 36, C30 at pin 10 with a link under the package to pin 5, C34 at pin 29 with a link under the package to pin 23 (pin to capacitor at most 4.5 mm) |
| A2-40 | USB | Crystal net XO autorouted as an 18 mm detour with two vias; XI ran beside the upstream pair (low) | The crystal moved 2.2 mm away from the hub; XO goes straight to its pad, XI through the channel between the crystal pads, the load capacitors sit behind the crystal - all locked copper, no vias |
| A2-41 | USB | Wording "coupled over its whole length" (it is 90 %); impedance report gave only the nominal value (low). A via of SD_DAT2 removes 0.4 mm of the reference plane under one line of the upstream pair (low) | Texts corrected; `usb_impedance.txt` also lists the value for the dielectric constant of JLCPCB's stack-up table (91.5 ohm) and the corners for width and prepreg tolerance (79 to 101 ohm, inside the USB window of 76.5 to 103.5). The via case is accepted: a few picoseconds, far below any effect at 480 Mbit/s; the routing is redone anyway |
| A2-42 | Radio | The antenna keep-out covered only the first 6 mm; ground copper lay 1.1 mm from the open end of the module's PCB antenna (medium) | Second keep-out on all layers under the copper-free pocket of the module (board 21.0..31.25 x 64.0..68.0) |
| A2-43 | Radio / LEDs | Green status LED about ten times brighter than the red "muted" LED; decoupling of the radio 6 to 7 mm from its supply pin; two texts (low) | Series resistors 5.1k (green), 2.2k (blue), 150 ohm (red, new BOM line C25082); C49 / C50 fixed next to the supply pin; texts corrected |
| A2-44 | JLCPCB package | Copper 0.35 mm from the board edge, JLCPCB asks for 0.40 mm at V-cut edges; the default edge rails would be scored along the edges with the overhanging USB-A connector and the flush radio module (medium) | Copper keep-out 0.45 mm along the edges, around the rounded corners as well since round 2; the order remark asks for the rails on the two 74 mm edges (cost of the larger panel is in the estimate) |
| A2-45 | JLCPCB package | Three LCSC numbers were on two BOM rows each - JLCPCB un-ticks such rows; BOM comments were not JLCPCB's model names (medium / low) | `make_jlc.py` groups by LCSC number and writes JLCPCB's model name as the comment |
| A2-46 | JLCPCB package | Footprint silkscreen lines 0.12 mm (JLCPCB: 0.15 mm); paste apertures on the unpopulated C13; inner-layer hole clearance not in the rules (low) | All silkscreen graphics widened to 0.15 mm; no paste on unpopulated footprints; sixth custom rule |
| A2-47 | Enclosure | A dimensioned data sheet of the speaker exists (flange 70.11 x 30.72 mm, 16.5 mm high); the pocket had only 0.24 mm side clearance and the shell mesh had two non-manifold edges (medium / low) | Pocket, grille and pedestal follow the data sheet (0.6 mm clearance per side, grille covers the off-centre cone either way round); meshes are watertight; a foot recess no longer cuts into two vent slots; light pipes are taken from D7-D9 by reference |
| A2-48 | Flashing script | `--dry-run` could not work on Home Assistant OS; an aborted run left the radio in its boot loader; JTAG pins stayed driven; misleading messages (medium / low) | Fixed in `tools/flash_zigbee.sh` and re-run against the simulator (cases in `fab/ASSEMBLY_AND_TEST.md`) |

Accepted without change, with the reason: reference designators are not on the silkscreen (the board is too dense; the
CPL carries them and the order remark explains the polarity marks); the mute dish of the enclosure prints as a short
bridge with the switch slot in it (clear the slot after printing); the corner posts of the enclosure stand 0.2 mm from
the walls (cosmetic); the downstream USB lines of port 2 run 2.5 mm at 0.15 mm gap between two connector pins
(78 ohm differential there, electrically short).

### Review round 2 (the last round): re-check of the fixes

The reviewers of round 1 measured their own findings again on the rebuilt board, the regenerated order package, the
regenerated enclosure and the revised script, and looked for anything the fixes had introduced. No high or medium
finding remained; every new low finding that changes copper was fixed, the review stopped after this round as planned.

| # | Area | Result | What was done |
|---|---|---|---|
| A2-49 | Radio / LEDs | All six findings fixed: no copper of any layer within 3.0 mm of the open end of the antenna (was 1.1 mm); LED intensities about 29 / 25 / 25 mcd typical (were 150 / 55 / 12); radio decoupling 1.8 mm from the supply pin; ERC 0, DRC 0, all 512 pins equal to the netlist. New: the microphone clock now runs 1.5 mm beside the feed end of the antenna where ground pour was before (no action) | Stale keep-out row in `hardware/README.md` corrected |
| A2-50 | Enclosure | E1, E2, E4, E5, E7 fixed (pocket clearance 0.59 mm per side, 0.44 mm at maximum size; both meshes watertight; 76 of 89 grille holes over the cone whichever way round; all 154 solids of the board model clear of shell and base). New: the pad was squeezed 41 % instead of 35 % | Foam gap set to 2.0 mm (pedestal 18.5 mm below the top plate, as before the speaker change); heat sink in the 3D model of the CM4 is 7 mm like the part on the shopping list |
| A2-51 | JLCPCB package | J-01 to J-07 fixed: copper 0.450 mm from the straight edges on all four layers, 53 BOM rows for 53 LCSC numbers, every comment equals JLCPCB's model name, no silkscreen stroke below 0.145 mm, no paste on unpopulated parts; all 135 parts with a JLCPCB footprint land pad-on-pad at the CPL angle again; Gerbers identical to a fresh export. New (low): the "GND" label stood diagonal to its test pad and nearer to a 3.3 V capacitor pad | The label is placed directly above its pad. A stray netlist file caused by a path substitution in `build.sh` is removed and the substitution fixed |
| A2-52 | Flashing script | The reviewer applied its own fixes and re-ran 20 cases against the simulator with the real flashing tool: all pass, a successful default run prints exactly what it printed before | - |
| A2-54 | Power / USB | All layout fixes of round 1 confirmed with own measurements: no via in or touching a lead pad, no copper of the charger nets near J6 (smallest clearance of the HV nets 0.20 mm), buck thermal pad and PGND connected solid, every hub supply pin at most 4 mm of track from its capacitor (was 47 mm), crystal lines 9.4 mm without vias, USB skew 0.000 mm, DRC 0. Partly: two report texts (power path header, impedance corners computed with one dielectric constant only); a hardware/README line said 17.5 um inner copper. Not fixed and accepted again: four foreign vias beside the upstream pair (each removes about 0.3 mm of reference plane, about 2.5 ps). New, all low: pours 0.20 mm from the edge at the four rounded corners; autorouted +3V3 and USB_OC1_N copper between the lead ring and the exposed pad of the hub; `check_vias.py` treated the highest-numbered pad of every IC as an exposed pad; a 0.40 mm track ending in a 0.25 mm pad of the amplifier (also 0.25 mm +3V3 tracks into the 0.22 mm balls of U9 and the 0.2 mm socket pads) | Corner keep-outs (0.450 mm everywhere now); the hub's 3.3 V links under the package are hand-designed and locked, the two free channels are keep-outs for the routers; routed track ends are necked to the pad width inside and 0.3 mm around fine pads; `check_vias.py` uses an explicit table of exposed pads and the real pad shapes (a bounding-box check flagged vias beside the round spacer pads; re-tested on the round-1 board, where it finds the same 13 overlaps as the reviewer); texts and the impedance report corrected (corners 79.3 to 103.0 ohm over both dielectric constants, inside 76.5 to 103.5). Board re-routed: placement unchanged, DRC 0, all gates pass |

### Exceptions to the owner's rules (deliberate, each explained above)

- **Below 200 pieces at JLCPCB on 2026-11-12:** ADAU7002ACBZ-R7 (104), 61400826021 (116), RF-BM-2652P2 (126). No better-stocked
  part with equal ratings exists for the first and the third; the second has a checked fallback.
- **Temperature rating of the radio module:** RF-BM-2652P2 -40..+85 C, MGM240PB32VNA3 -40..+105 C. No stocked module
  reaches 105 C. Every other part of the board that limits the range is an 85 C part as well (CM4: -20..+85 C).
- **Extended parts among the passives:** 1 uF 25 V X7R, 4.7 uF 25 V X5R, 24.9k 1 %, and four Preferred Extended resistor
  values - see A2-9.

### Manufacturer data sheets re-read (A1 open item 3)

The nine documents A1 had read from mirrors were requested again from the manufacturers on 2026-11-12 (curl with a
browser user agent, then WebFetch, then alternative official hosts; no headless browser, because the session's
permission system refuses bot-check circumvention).

| Document | Source now | Revision read | Difference that touches the design |
|---|---|---|---|
| Hirose DF40C-100DS-0.4V(51) | hirose.com | catalogue Jan. 2025, drawing EDC3-311352-00, spec rev 3 | land pattern identical; ratings better (50 V, -55 C); the drawing's strip and paste rules led to A2-24 and A2-25 |
| Hirose DM3AT-SF-PEJM5 | hirose.com | current catalogue | none |
| Silicon Labs MGM240P | still refused (HTTP 403); LCSC copy + DigiKey PCN | Rev. 1.0 / PCN for 1.2 | none - and the part is replaced (A2-3). Rev. 1.4 exists and could not be read |
| C&K JS202011JCQN | still refused; LCSC copy (Littelfuse-branded, 09/11/25) | 2025 | none |
| Analog Devices ADAU7002 | still refused; distributor copy | Rev. B | none |
| Analog Devices MAX98357A | still refused; LCSC copy | Rev 13 | none (package outline 21-0136 re-checked against the footprint). Rev 16 exists ("ordering information") and could not be read |
| ST USBLC6-2SC6 | still refused; Farnell / LCSC copy | Rev 5 | none; a newer revision exists on st.com and could not be read |
| Littelfuse SMBJ22A | still refused; distributor copy | current | none |
| Nexperia 2N7002 | still refused; distributor copy | current | none |

Two of nine are now read from the manufacturer's server; seven manufacturers still refuse automated requests, so the
newest revision an authorised distributor serves was used. No revision difference changes a pin-out, a land pattern or
a rating the design relies on. The new parts of A2 were read from the manufacturers directly where they publish
(RF-star hardware data sheet V1.1, TI CC2652P SWRS195C and the CC13x2 / CC26x2 technical reference manual).

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
| 11 | **Five lines kept although out of stock at DigiKey** | LMR33640ADDAR, CL31A226KOHNNNE (22 uF) and 2N7002,215: no in-stock part with equal or better ratings and the same footprint exists. TPS2553DBVR: the identical device is in stock as the DBVT reel (+0.16 USD), the BOM names it. CL31B106KBHNNNE (10 uF X7R): an equal part is only available as a 2,000-piece Marketplace item. Flagged in the BOM instead of silently downgrading (section 10). |
| 12 | **Stand-in 3D models rewritten as coloured STEP assemblies** (CM4 with heat sink, stacked USB-A, slide switch, radio module, ...) | KiCad's STEP export drops colours and the old stand-ins were single boxes; the showcase render and the KiCad renders need to tell metal from plastic. Envelopes follow the drawings. |
| 13 | **OS full build runs on the host as an unprivileged user; github.com "archive" sources are fetched with git** (`VOXHUB_GITHUB_VIA_GIT=1`) | HAOS's `scripts/enter.sh` and Buildroot refuse to run as root; this environment's egress proxy answers 403 to `github.com/<owner>/<repo>/archive/...` while git access to the same public repositories is allowed. Buildroot still checks every tarball against its hash. Details in os/README.md. |
| 14 | **Showcase animation rendered with Cycles on the CPU at 4 samples + OpenImageDenoise, 21 s** | No GPU in the build machine: EEVEE through software OpenGL needs about 100 s per frame, Cycles about 9 s on average with these settings (1260 frames in 3 h 10 min). Details in media/README.md. |
| 15 | **Mouser data is not live** | mouser.com answers every automated request with HTTP 503 (bot protection) and no API key was available; evading the protection was not attempted. The BOM carries DigiKey live data plus clearly marked search-snippet values for Mouser. |
| 16 | **OS full build restarted after a self-inflicted stop (attempt 5)**; the four affected Buildroot packages are rebuilt, nothing is patched | Attempt 4 stopped after 3 h at `libblockdev` with `libtool: error: '.../build/util-linux-2.40.4/libuuid.la' is not a valid libtool archive`. Cause: the disk-space helper of this session (outside the repository) had emptied the build directories of finished packages, but the staging `libfdisk.la` / `libmount.la` (and `libdns.la`, `libgnutlsxx.la`) refer back into them. Rewriting the `.la` files would have hidden the mistake in a non-standard build tree, so the directories of `util-linux`, `host-util-linux`, `gnutls` and `dhcp` were deleted (Buildroot rebuilds them) and the helper now skips every directory that a libtool archive points to and anything below 150 MB. The run log is in os/README.md. |
| 17 | **Independent review of all A1 deliverables before calling them done**: five reviewers (USB lengths re-computed with their own parser, schematic / OS / assistant consistency against the data sheets, BOM and sourcing, documentation and enclosure, build scripts), each finding then attacked by a second agent | 51 findings, 48 confirmed, 3 refuted. The confirmed ones are fixed or, where a fix needs hardware or a production decision, documented (rows 18-24, Open items). The reason for doing it: the first A1 commit claimed a USB result that a plain re-computation disproved. |
| 18 | **USB pairs re-done: ESD parts turned into a flow-through orientation and swapped left / right, strict pad-to-pad router rules, contact-accurate length measurement** (section 6a) | Port 2 was really 4.9 mm off (limit 3.8 mm) although the report said 0.00 mm: the length measurement followed a loop. New result 0.00 / 0.00 / 0.00 mm, 0 vias, no stubs, confirmed by an independent computation. |
| 19 | **C10 (220 nF) and C11 (1 uF VCC) get fixed positions directly at the LMR33640 pins** (1.8 mm, were 8.4 mm and 6 mm away; superseded by the complete hand placement of row 28) | The data sheet demands the 220 nF bypass "as close as possible to the regulator"; the greedy placer had put the larger capacitors first. Review finding. The rest of the power stage is still auto-placed (Open items). |
| 20 | **New autorouter session; Freerouting is started up to three times** and the session file is checked | Freerouting 2.0.1 twice routed the board and then left an empty session file (busy machine; the passes in its log were identical to a good run). `build.sh` used to copy that empty file over the checked-in session. |
| 21 | **Radio UART is `/dev/ttyAMA4`, not `ttyAMA1`**; openocd reset recipe changed to push-pull | The kernel HAOS 18.5 pins has fixed serial aliases (`serial4 = &uart4`). With `srst_open_drain` openocd never drives GPIO24 high, so the active-high reset would never be asserted. Review findings; text only, no hardware change. |
| 22 | **Build scripts fail loudly**: `build.sh outputs` stops on DRC violations and when a USB pair is unmatched or untraceable; `postroute.sh` treats a missing measurement as failed and gives up when the repair loop stops making progress; `os/build-image.sh` checks for root before creating anything, makes `--out` absolute, writes git-made tarballs under a temporary name and aborts before the build when a source could not be fetched or has the wrong hash | Review findings: each of these paths could end "successfully" with a wrong or missing result. |
| 23 | **BOM honesty fixes**: Mouser part numbers that were only built from Mouser's prefix scheme are marked as such (18 of 37); unit prices keep four decimals so that quantity x price reproduces the extended price; the 220 nF line says that DigiKey shows no stock figure; the Cal-Chip alternate is described as what it is (2,000-piece Marketplace minimum); crystal stability figures corrected | Review findings. Totals did not change. |
| 24 | **Section 9 completed**: crystal row verified against the Epson-hosted brief, 2N7002 row added (mirror of the Nexperia sheet), generic passives row now says plainly that no manufacturer document was read | Review finding: README claimed "every row verified" while two rows were not. |
| 25 | **OS host build: Buildroot's `host-libyaml` is built first when the host has `libyaml-dev`** | Attempt 5 of the full build stopped in U-Boot's host dtc: it found the host's `/usr/include/yaml.h` but not the library through Buildroot's pkg-config. Upstream host leak that the HAOS builder container does not have; the script now works around it instead of telling the user to uninstall a package. |
| 26 | **`VOXHUB_GOPROXY`: optional Go module proxy for the OS build** | Attempt 6 stopped at the last Go package: Buildroot fetches Go modules from their own hosts (`GOPROXY=direct`) and gopkg.in is not reachable from this environment. The option rewrites that one setting in the cloned Buildroot tree; integrity checks (go.sum, Buildroot's tarball hash) are unchanged. Opt-in, like the git fallback for GitHub tarballs. |
| 27 | **OS host build: the RAUC signing key paths of the HAOS scripts are redirected from `/build` to the cloned tree**; the disk-space helper of the session is switched off | Attempt 8 stopped in `post-build.sh` (`Can't open "/build/key.pem"`): `/build` only exists inside the HAOS builder container. Attempt 7 had stopped one step earlier because the helper had emptied the python3 build directory that Buildroot needs for the final `.pyc` compilation - the second self-inflicted stop, so the helper went. **Attempt 9 completed**: image and OTA bundle built and inspected (os/README.md). |
| 28 | **Buck power stage placed by hand**: U2 turned by 180 degrees (VIN / PGND towards the PD stage, SW / BOOT / VCC towards the inductor), C10 + C8 + C9 in one pour with the VIN pin, C12 and C11 1.8 mm from BOOT / SW and VCC, inductor under the SW pin, output capacitors below it | The second review round found that the fix of row 19 had a side effect: with the inductor on the VIN side the switch-node track ran between C8 and the regulator, cut C8 off from the VIN pour and left it on a 20 mm long 0.4 mm track round the inductor pad. Placing single parts was treating symptoms; the greedy placer is the wrong tool for a switching converter. USB result unchanged (0.00 mm, no vias), build reproducible. What is still automatic and weak (the 0.4 mm feed from Q1) is listed under Open items. |
| 29 | **Second review round on the fixes** (four re-checkers + four verifiers): 47 of the 48 confirmed findings of round one fixed, one (bom-1) partly - its leftover sentence is among the new findings and is corrected now; the USB result re-computed a third time independently and confirmed; 17 new findings confirmed (one medium: row 28; the rest wording, counts and script robustness), 5 refuted | A fix can introduce the next defect - row 28 is the proof. Fixed in the same pass: the settle loop now gives up on a repeated violation list instead of equal counts and never reads a stale DRC report; `build.sh` checks for `zip`; `build-image.sh` refuses a clone of another HAOS version and Wi-Fi options in full mode; `build_showcase.sh` discards frames rendered from other inputs; counts and dates in the texts corrected. |
| 30 | **Third, focused round on the power-stage change** (three checkers + three verifiers) **- and the decision to stop changing the board**: the split-pour defect is gone, the USB figures were confirmed with a fourth parser, the outputs belong to the committed board; 12 new findings confirmed, all low | What they found on the board is layout polish, not a defect of the prototype: the ground side of the buck is still the scripted fan-out, the VBUS pour has 0.4 mm necks, two fan-out vias lie in QFN lead pads, two silkscreen outlines cross a text. Each further re-spin so far has produced the next finding of the round after it and makes the rendered video stale again, so these are documented with numbers as "before a production spin" instead of being fixed now. The text and script findings (waived-check reasons, via-in-pad note, review counts, fingerprint of the render inputs, two unreachable error messages) are fixed. |
| 31 | **Video re-rendered from the final board - only the 866 frames that show the PCB** (150 to 1015); the 394 closed-device frames of the first render are kept | A full render takes 3 h 10 min, the PCB frames 1 h 54 min. The kept frames cannot differ: shell and base are unchanged (STL byte-identical) and the board is inside the closed case. Checked instead of assumed: five kept frames rendered again from the final board match to within 3 of 255 on single pixels, and there is no jump at the two joins. `build_showcase.sh` itself always renders one consistent set (input fingerprint). |

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
| mouser.com (HTTP 503 for every automated request), octopart / trustedparts / findchips (403) | no live Mouser stock or prices | DigiKey is live for every line; Mouser part numbers and figures come from search-engine snippets, 18 of the 37 part numbers are only built from Mouser's prefix scheme or carried over from the first session - both kinds are marked in the BOM ("NOT live" / "not seen on mouser.com"). A Mouser API key would close this. |
| silabs.com (MGM240P), hirose.com (DF40, DM3AT), littelfuse.com (C&K JS, SMBJ), analog.com (ADAU7002, MAX98357A), st.com (USBLC6-2), nexperia.com (2N7002) - 403 / unreachable | nine documents could not be read from the manufacturer's own server | the manufacturer's PDF was read from a mirror (SparkFun, distributor document servers); revision and mirror URL are listed per part in section 9 |
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
- **Negotiated voltage: 9 V minimum, 20 V maximum, 2 A minimum.** The theoretical simultaneous peak on the 5 V
  rail is ~3.5 A = 17.6 W, i.e. 19.5 W at the connector (power budget in README); realistic operation stays below 12 W.
  5 V/3 A (15 W) is not enough, so 5 V is excluded; 9 V/2 A = 18 W is the smallest PDO that is accepted - it covers
  realistic operation and practically every >= 20 W PD charger offers it, but the theoretical peak is 8 % above it
  (README: use a 27 W charger if both USB ports feed 500 mA devices).
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
  datasheet table for 5 V / 400 kHz: 6.8 uH (Sunltech SLO0630H6R8MTT, Isat 8 A, Irms 4.5 A, 45/54 mOhm; A1: Bourns SRP7028A-6R8M, log A2-10), 4 x 22 uF out
  (the table's typical value; minimum 3 x 22 uF), 100k / 24.9k feedback (5.02 V), 2 x 10 uF / 50 V X7R + 220 nF / 50 V
  X7R in, 100 nF boot, 1 uF VCC. Inductor ripple 0.81 A p-p at 9 V in, 1.40 A at 20 V; peak inductor current at 4 A
  load 4.7 A, well below Isat. EN divider 470k / 100k: on at 7.02 V, off at 6.45 V.
  36 V rating leaves margin over 20 V + TVS clamp. Internally compensated -> few parts.
  Revision A was set to 5.1 V "to absorb drops"; that put the tolerance corners above the CM4's 5.25 V limit (see log no. 2).
- **3.3 V**: taken from the CM4's own 3.3 V output (600 mA budget, ~520 mA worst case used), exactly as the
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
- Data lines (revision A2, log A2-20 to A2-22): stack-up JLC04161H-3313; the upstream pair is a coupled 0.14 / 0.16 mm
  pair (89.96 ohm in JLCPCB's calculator), the downstream lines are two matched 0.185 mm lines per port (45.2 ohm each).
- Hub crystal: 24 MHz, CL 12 pF (YXC X322524MOB4SI) with 2 x 15 pF (log A2-14).

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

- **RF-star RF-BM-2652P2** (TI CC2652P, +20 dBm PA, PCB antenna, 16.5 x 30 mm; revision A2, log A2-3). A1 used the
  Silicon Labs MGM240PB32VNA3, which nobody stocks. CC2652P coordinators are first-class in Home Assistant (ZHA radio
  type "ZNP", Zigbee2MQTT adapter "zstack") and the same module runs an OpenThread RCP.
- UART4 on GPIO8 (TXD4 -> module DIO12 = RX) and GPIO9 (RXD4 <- DIO13 = TX), `dtoverlay=uart4` -> `/dev/ttyAMA4` (the
  Raspberry Pi kernel that HAOS 18.5 pins has fixed serial aliases, `serial4 = &uart4`). No flow control: Koenkk's
  firmware does not use it. GPIO10 / GPIO11 stay wired to DIO18 / DIO19 for a firmware that would.
- Reset: GPIO24 drives an open-drain 2N7002 on the module's RESET pin (**GPIO24 high = radio held in reset**), 100k
  pull-up to 3.3 V on the reset line, 100k gate pull-down. The SoC's boot-time pull-down on GPIO24 keeps the FET off,
  i.e. the radio runs by default.
- Boot-loader backdoor: module DIO15 on GPIO25, active low, 2.2k pull-up (log A2-5). Low while reset is released starts
  the CC2652P ROM serial boot loader on the same UART.
- JTAG: TMS GPIO22, TCK GPIO23, TDO (DIO16) GPIO17, TDI (DIO17) GPIO7 - the recovery path when a module arrives with a
  firmware whose backdoor is disabled (OpenOCD bit-bang, see `tools/voxhub-cc2652-jtag.cfg`). TMS / TCK / reset / TDO
  are also on the Tag-Connect pads J8 for a TI XDS110.
- The module is delivered without the Zigbee firmware this project uses: `tools/flash_zigbee.sh` writes it from the
  CM4 with one command (log A2-32, procedure in `fab/ASSEMBLY_AND_TEST.md`).
- In the EU the 2.4 GHz band is limited to 10 dBm/MHz power spectral density, so a Zigbee coordinator has to run at
  about +10 dBm whatever the module can do; the +20 dBm amplifier is headroom, not range.

## 6. Mechanical concept

- PCB 100 x 74 mm, 4 layers, 1.6 mm. All connectors on the rear edge.
- The PCB hangs **component side down** under the top cover. That gives the bottom-port microphones a short path to
  the top surface, puts the status LEDs and the mute slider on the side that faces the cover, and lets
  the whole shell print upside down without supports.
- Speaker (enclosed, 70 x 30 x 17 mm, 4 ohm, 3 W, JST-PH plug) sits next to the PCB, fires upwards, and is clamped by a
  pedestal on the base plate (log A2-30).
- CM4 antenna end at the board edge (1 mm from it), copper keep-out on all layers under the antenna as drawn in the
  CM4 datasheet (log no. 1); no enclosure screw or other metal within 10 mm of it except the module's own mounting screw.
  Radio module at the front edge with its antenna end on the edge; no copper on any layer under the antenna
  (board 11.75..31.25 x 68.0..74.0, the area RF-star's drawing marks plus a margin).
- No Ethernet, HDMI, camera, PCIe: not required; leaving them out keeps the board routable on two signal layers.
  Consequence: first-boot network setup is done by pre-seeding Wi-Fi credentials into the image (`os/build-image.sh --wifi-ssid`).
- No fan: 14 x 14 x 7 mm heat sink on the SoC plus vents; see thermal estimate in README.
- User button dropped (wake word + mute switch cover the UI); debug UART header footprint is DNP.

## 6a. PCB implementation (how a board gets routed without a GUI)

**Revision A2 in one paragraph** (log A2-15 to A2-27): the flow below is unchanged for the signal nets, but the copper
that carries current or USB data is no longer left to it. `gen/prewire.py` describes the PD input, the load switch,
the buck stage, the two USB port supplies and all six USB data lines as tracks and vias relative to the pads;
`build_pcb.py place` lays them (power locked from the start, the USB lines locked after the length check), the
fan-out, the autorouter and the repair loop route everything else around them. The length measurement of item 4
below still judges the USB lines and still gates the build; the USB router rules, the serpentine tuner and the six
net-order variants of items 3, 5 and 6 are not needed any more (a hand-designed line is matched by construction and
by one explicit compensation bump). A2 result: upstream 31.79 / 31.79 mm as a coupled pair, port 1 10.76 / 10.76 mm,
port 2 16.21 / 16.21 mm, skew 0.00 mm, no vias, off-path copper 0.00 mm.

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
- **USB (revision A1)**: the hub is rotated so that its downstream pins face the USB-A connector and its upstream pins face the CM4. The six data
  nets were re-routed after everything else as 0.2 mm traces. True coupled-pair routing was not attempted in A1; A2 routes the
  upstream pair coupled by hand (the pair enters the CM4 socket pads from the centre channel, so no crossover is needed).
- **USB length matching (revision A1, redone after the review - log no. 18; superseded by the hand-designed lines of A2)**, all in `gen/build_pcb.py`:
  1. *Placement for a flow-through layout.* The two USBLC6-2SC6 sit between hub and connector, turned so that one pad row
     (4, 5, 6) faces the hub and the other (3, 2, 1) the connector, D+ on the left and D- on the right in both rows - the
     same order as the hub pins and the connector pins. Port 2 is on the left, port 1 on the right, like the hub pins.
     No line has to cross another one or change layer. (The first A1 layout had the parts turned by 90 degrees, pad
     columns left / right: whichever line was laid first cut the other one off from its pad.)
  2. *Flow-through ESD links.* The two pads of one line (1+6, 3+4) are joined by a locked straight track under the
     package (ST's flow-through layout). `ESD_ROLE` fixes which pad each side uses: 6 / 4 for the hub, 1 / 3 for the
     connector.
  3. *Router rules for the six data nets* (`patch()`): a line is always laid pad to pad from scratch (left-over copper
     of an earlier attempt is discarded first, the autorouter's USB tracks are discarded in `finish()`); the hub side
     first; the line's own copper and its other ESD pad are obstacles, so it can neither cross itself nor run over a
     pad it does not end on; a lane is kept free next to the ESD pads of the partner line; other tracks are ripped up
     before a layer change is considered; no other net may rip up USB copper. A join that cannot keep these rules
     fails, and the variant is discarded, instead of producing a stub.
  4. *Electrical length.* `usb_report()` builds the copper graph of each net and measures the shortest path from the
     hub pin to the connector pin, 1.5 mm per via. The graph joins copper wherever it really touches (crossing centre
     lines, a track over a pad or through a via land, overlapping track ends), not only at track end points. It also
     reports the skew with vias counted as 0 (the via length is an estimate), the pads the path runs through, and the
     copper of the net that is not on the path ("off-path": stubs, loops).
  5. *Serpentines.* `tune_usb()` adds 45-degree-mitred meander bumps (0.6 mm pitch = 3 x track width, amplitude
     0.3..3 mm) to the shorter line of each pair, only where the copper keeps 0.17 mm to everything else (0.4 mm to
     its own net), until the path lengths agree.
  6. `postroute.sh` tries up to six net orders and keeps the best: the score is the worst of skew, skew with vias
     counted as 0 and off-path copper. A missing measurement counts as failed, and `stats` (called by `build.sh
     outputs`) exits non-zero above 3.8 mm.

  Result of revision A1 (the A2 figures are in the paragraph at the top of this section): upstream 30.96 / 30.96 mm, port 1 11.21 / 11.21 mm, port 2
  15.17 / 15.17 mm -> skew 0.00 / 0.00 / 0.00 mm; all six lines on F.Cu without a single via; path of every
  downstream line: hub pin > ESD pad > ESD pad > connector pin; off-path copper <= 0.05 mm (track ends inside pads).
  Independent re-computations (review scripts with their own board parsers, not in the repository): the first
  reviewer's script gives 30.963 / 30.963, 11.253 / 11.242 and 15.215 / 15.215 mm on the committed board, no crossings,
  no T-junctions, no duplicate USB segments. The second review round wrote a third parser for the board of commit
  81bcdf0 (30.986 / 30.986 mm upstream there). The router session after the power-stage change re-laid the upstream
  pair and moved the port 1 D+ meander by 0.5 mm, so the third round ran that script again on the committed board and
  also wrote a fourth parser: both give 30.963 / 30.963, 11.208 / 11.208, 15.170 / 15.170 mm,
  serpentines not shorted (same-net copper that is more than 1 mm apart along the line stays 0.6 mm apart), smallest
  gap to another net 0.158 mm, D+ / D- not swapped anywhere between hub, ESD parts and connectors.

  *What was wrong before:* the first A1 board reported 0.00 / 1.35 / 0.00 mm. The measurement only joined copper at
  track end points; on port 2 the hub-side track of D- crossed the connector-side track of the same net next to an ESD
  pad, the metric measured the long way round the resulting 4.9 mm loop, and the tuner matched the pair to that wrong
  length. The real skew of port 2 was 4.9 mm, above the 3.8 mm limit, and three of the four downstream lines had stubs
  of 1 .. 2.3 mm. The independent review found it by re-computing the lengths from the board file.
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
  It can also use a Go module proxy (`VOXHUB_GOPROXY`), builds `host-libyaml` first on hosts with `libyaml-dev` and
  redirects the `/build/key.pem` paths of the HAOS scripts on host builds. With these the full build ran to the end in
  this environment (ninth attempt); the run log with every stop and its cause is in os/README.md.
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
| CM4 socket Hirose DF40C-100DS-0.4V(51) | Hirose DF40 catalogue, edition 2013.11, via mirror https://cdn-shop.adafruit.com/product-files/2227/ed_DF40_20140305-337786.pdf; **A2: re-read from hirose.com** (catalogue Jan. 2025, drawing EDC3-311352-00, guideline) - strips and paste aperture now follow it, log A2-24 / A2-25 | **verified against datasheet** - land pattern, 1.5 mm mated height, 1.5 mm spacer. Note: the inward power stubs cross Hirose's "layout prohibited area" between the pad rows exactly as on the official CM4IO board. |
| CYPD3177-24LQXQ | https://www.infineon.com/assets/row/public/documents/24/49/infineon-cypd3177-24lqxq-datasheet-en.pdf (002-25383 Rev. *C, 2024-09-18); kit guide 002-25263 Rev. *B https://www.infineon.com/assets/row/public/documents/24/44/infineon-cy4533-ez-pd-barrel-connector-replacement-evk-guide-usermanual-en.pdf | **verified against datasheet** - pin-out, QFN-24 land pattern, active-low P-FET driver, FLIP 49.9k, I2C 0x08, unused pins, all four strap dividers = table values, PDO selection algorithm. **Deviation found and fixed:** VDDD decoupling (1 uF X7R 0603 + 2 x 100 nF instead of 1 uF X5R 0402 + 100 nF). Note: the single-FET gate network differs from the two-FET reference circuit - measure VGS at 9 V and 20 V on the prototype. |
| LMR33640ADDA | https://www.ti.com/lit/ds/symlink/lmr33640.pdf (SNVSB99C, rev. November 2020) | **verified against datasheet** - pin-out, HSOIC-8 PowerPAD land pattern, "A" = 400 kHz / 4 A, EN thresholds (UVLO 7.02 V / 6.45 V), CBOOT, CVCC; L = 6.8 uH and COUT = 4 x 22 uF are the table row for 5 V / 400 kHz. **Deviations found and fixed:** RFBB 24.3k -> 24.9k, CHF 100 nF -> 220 nF X7R, CIN X5R -> X7R (log no. 2, 3). |
| Bourns SRP7028A-6R8M (A1 only, replaced in A2) | https://www.bourns.com/docs/Product-Datasheets/SRP7028A.pdf (REV. 06/24) | **verified against datasheet** - 6.8 uH, Isat 8 A, Irms 4.5 A, DCR 54 typ / 60 max mOhm, footprint. |
| USB2514B-I/M2 | https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/USB251xB-xBi-Data-Sheet-DS00001692.pdf (DS00001692E) | **verified against datasheet** - pin-out, CFG_SEL = 00, NON_REM, port disable by 10k to 3.3 V, PRTPWR / OCS polarity, VBUS_DET, RBIAS 12k 1 %, 24 MHz crystal + load capacitors, filter capacitors. **Deviation found and fixed:** RESET_N (log no. 5). Accepted: the KiCad QFN-36 pads are 0.825 mm long, Microchip recommends 0.90 mm (79 % of the terminal is covered; pitch, exposed pad and numbering match). |
| TPS2553DBV | https://www.ti.com/lit/ds/symlink/tps2553.pdf (SLVS841G, October 2026) | **verified against datasheet** - pin-out, active-high EN, open-drain FAULT, 2.5-6.5 V input, ILIM equation (20k -> 1.215 / 1.295 / 1.375 A, 49.9k -> 0.49 / 0.52 / 0.55 A). |
| MAX98357AETE+ | Maxim 19-6779 Rev 7 (original PDF via https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf), cross-checked with Rev 13 | **verified against datasheet** - TQFN-16 pin-out, SD_MODE at 3.3 V = left channel, GAIN_SLOT open = 9 dB, 2.5-5.5 V, package outline. The separate land-pattern document 90-0031 could not be retrieved. |
| ADAU7002ACBZ | ADI ADAU7002 Rev. C (11/2019), original PDF via mirror https://cdn.eicom.ru/media/PDF/2429992.pdf | **verified against datasheet** - ball map, CONFIG = IOVDD -> I2S, 1.62-3.6 V, BCLK = 64 fs, 0.4 mm ball grid. The datasheet gives no land pattern (pad diameter 0.22 mm stays an IPC choice). |
| IM69D130 | https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d130-datasheet-en.pdf (V1.0, 2017-12-19) | **verified against datasheet** - pins, SELECT (GND = left, VDD = right at the ADAU7002), 1.62-3.6 V, 3.072 MHz clock, land pattern with the 0.8 mm port hole. Note: 70 C ambient limit at 3.3 V. |
| MGM240PB32VNA (A1 only, replaced in A2) | Silicon Labs MGM240P data sheet Rev. 1.0 (original PDF via https://cdn.sparkfun.com/assets/1/4/5/e/5/MGM240P-Datasheet.pdf; silabs.com refuses automated downloads, Rev. 1.2 not retrievable) | **verified against datasheet** - pin-out, land pattern (36 / 36 pads), RFOUT open for the built-in antenna, antenna keep-out, no external decoupling required. **Deviations found and fixed:** RTS / CTS swapped, RESETn pull-up (log no. 6, 7). |
| USB-C GCT USB4105-GF-A | https://gct.co/files/drawings/usb4105.pdf (Rev. B4) | **verified against datasheet** - footprint, shell 8.94 x 7.35 x 3.31 mm, shell flush with the PCB edge. |
| USB-A Wurth 61400826021 | https://www.we-online.com/components/products/datasheet/61400826021.pdf (Rev. 001.001, 2025-09-11) | **verified against datasheet** - footprint and drills, shell height 15.34 mm, flange 14.5 x 15.5 mm with lips at 0.45 / 15.95 mm, 2.5 mm overhang beyond the PCB edge. |
| microSD Hirose DM3AT-SF-PEJM5 | Hirose drawing EDC-325165-40-00 for the (40) variant, via mirror https://static.chipdip.ru/lib/504/DOC014504844.pdf; **A2: re-read from hirose.com** (drawing EDC-325165-00-00, mark 4, 2024-09-02) - no difference | **verified against datasheet** - footprint, body 13.85 x 15.95 x 1.68 mm, card positions (locked: 1.6 mm behind the enclosure face). |
| C&K JS202011JCQN | C&K "JS series" data sheet, edition 22 Sep 2022, via mirror https://static.chipdip.ru/lib/994/DOC043994900.pdf (the current Littelfuse-hosted edition refuses downloads) | **verified against datasheet** - land pattern, body 9.0 x 3.6 x 3.5 (3.6) mm, actuator 1.5 x 1.5 x 2.0 mm, 2 mm travel. The drawing has no body tolerances. |
| JST B2B-PH-K-S | https://www.jst-mfg.com/product/pdf/eng/ePH.pdf (catalogue page, carries no revision) | **verified against datasheet** - footprint, 6.0 mm height. |
| Wurth 9774015151R | https://www.we-online.com/components/products/datasheet/9774015151R.pdf (Rev. 001.002) | **verified against datasheet** - land pattern, 1.5 mm height, M2.5 thread (2.9 mm long). |
| AO3401A | https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf (Rev 3.1) | **verified against datasheet** - SOT-23 G / S / D = 1 / 2 / 3, VDS -30 V, VGS +-12 V. |
| USBLC6-2SC6 | ST USBLC6-2 data sheet Rev 3 (2008) via mirror https://pccomponents.com/datasheets/ST_MI-USBLC62SC6.pdf | **verified against datasheet** (old revision) - pins 1 + 6 and 3 + 4 are one line each, 5 = VBUS, 2 = GND. |
| SMBJ22A | Littelfuse SMBJ series data sheet, rev. 2020-06-03, via mirror https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/Littelfuse_5F00_TVS_5F00_Diode_5F00_SMBJ_5F00_Datasheet.pdf_2D00_1108540.pdf (littelfuse.com refuses the download) | **verified against datasheet** - 22 V stand-off, 24.4-26.9 V breakdown, 35.5 V clamp at 16.9 A (margin note in section 2). |
| MM3Z10V / SZMM3Z10VT1G | https://www.onsemi.com/pdf/datasheet/mm3z2v4t1-d.pdf (Rev. 15) | **verified against datasheet** |
| Speaker Same Sky CMS-4017-34SP (A1 only, replaced in A2) | https://www.sameskydevices.com/product/resource/cms-4017-34sp.pdf (rev 1.02) | **verified against datasheet** - dia 40 +-0.3 x 17.5 +-0.3 mm, yoke dia 23, 4 ohm, 3 W, baffle opening dia 35.6 with >= 0.8 mm in front of the diaphragm. |
| Heat sink Same Sky HSB03-141406 (A1 only, replaced in A2) | https://www.sameskydevices.com/product/resource/hsb03-141406.pdf (rev 1.03) | **verified against datasheet** - 14 x 14 x 6 mm. |
| Crystal Epson TSX-3225 24.0000MF18X-C0 (A1 only, replaced in A2) | https://download.epsondevice.com/td/pdf/brief/TSX-3225_en.pdf (Epson brief, PDF dated 2025-10-14) | **verified against datasheet** - 3.2 x 2.5 x 0.6 mm, internal connection: #1 / #3 crystal, "#2 and #4 are connected to the cover (Please connect to ground)" as on the footprint; f_tol +-10 ppm, +-10 ppm over -20..+75 C; CL is part of the order code (F18 = 18 pF as in the DigiKey description -> 2 x 27 pF). Recommended land pattern: 2.2 x 1.6 mm between pad centres, pads 1.4 x 1.15 mm. Accepted: KiCad's `Crystal_SMD_3225-4Pin` has 2.2 x 1.7 mm and 1.4 x 1.2 mm pads (0.05 mm per pad). |
| 2N7002,215 (Q2, Q3: LED drivers; Q4: radio reset) | Nexperia 2N7002 product data sheet Rev. 7 (8 September 2011), via mirror https://datasheet.chipsmall.com/2N7002-215/143966.pdf (nexperia.com refuses automated downloads; the product page lists a 2018 edition that could not be retrieved) | **verified against datasheet** (old revision) - SOT23 pinning 1 = G, 2 = S, 3 = D as in `design.py`; VDS 60 V, VGS +-30 V; VGS(th) 1.0 / 2.0 / 2.5 V at 0.25 mA (2.75 V max at -55 C), so the 3.3 V GPIO level turns it on with margin for the 75 uA of the 44k RESETn pull-up and the LED currents; RDSon 5.3 ohm max at 4.5 V. |
| Passives, diodes, LEDs (0402 / 0603 / 1206 chip, EIA-3528 polymer tantalum, SOD-323, SMB, 0603 and reverse-mount 1206 LEDs), 1 x 3 pin header J5 (DNP), Tag-Connect TC2030-NL pads J8, test points, solder jumper | KiCad 9 standard library footprints named after the package - **no manufacturer document was read for these** | **not individually verified:** standard IPC / KiCad land patterns; values, ratings and packages were checked on the DigiKey product pages (section 10); polarity marks (tantalum, diodes, LEDs) follow the KiCad convention pad 1 = cathode / pad 1 = "+" for the tantalum - check on the first article. |

**Parts that are new in revision A2** (checked on 2026-11-12):

| Part | Source (revision) | Status |
|---|---|---|
| RF-star RF-BM-2652P2 | https://www.rfstariot.com hardware data sheet V1.1 (2024-08-23); TI CC2652P data sheet SWRS195C (rev. April 2024) and technical reference manual SWCU185G from ti.com | **verified against datasheet** - module pin to DIO map for every connected pin (UART DIO12 / DIO13, backdoor DIO15, JTAG TMSC / TCKC, TDO DIO16, TDI DIO17, RESET, VCC, GND), 30-pad land pattern (identical to JLCPCB's footprint of C5440064 within 0.01 mm), antenna area. RF-star's table gives the width as 16.4 mm in one place and 16.5 mm in the drawing; the footprint uses 16.5 mm. The module has its own pull-up and capacitor on RESET; MSL 3, at most two reflow passes |
| Sunltech SLO0630H6R8MTT | SLO0630H series data sheet Rev.03 (LCSC C207841) | **verified against datasheet** - 6.8 uH +-20 %, Irms 4.5 A, Isat 8 A, DCR 45 typ / 54 max mOhm, -55..+150 C, 7.1 x 6.6 x 3.0 mm on the pads of the SRP7028A footprint (JLCPCB footprint fit: 0.19 mm) |
| KEMET T520B107M006ATE040 | KEMET T520 series data sheet | **verified against datasheet** - 100 uF 6.3 V, 40 mOhm, 1.8 A ripple, EIA 3528-21, -55..+105 C |
| YXC X322524MOB4SI | YXC X3225 data sheet (LCSC C70590) | **verified against datasheet** - 24 MHz, CL 12 pF, +-10 ppm, +-20 ppm over -40..+85 C, ESR 50 ohm max, pads 1 / 3 crystal, 2 / 4 case |
| LEDs Hubei KENTO KT-0603G / KT-0603B, Lite-On LTST-C191KRKT | manufacturer data sheets (LCSC C12624, C2288, C125099) | **verified against datasheet** - 30 mA continuous, -40..+85 C (Lite-On -55..+85 C), cathode = pad 1 of the JLCPCB footprint = pad 1 of the KiCad footprint (placement report: "pin names agree") |
| onsemi MM3Z10VT1G | https://www.onsemi.com/pdf/datasheet/mm3z2v4t1-d.pdf (same data sheet as the A1 part) | **verified against datasheet** |
| Speaker Adafruit 3351 | maker's data sheet C5282-001 (https://cdn-shop.adafruit.com/product-files/3351/C5282-001_datasheet__1_.pdf, found by the enclosure review): flange 70.11 x 30.72 mm, height 16.5 +-0.5 mm, box 66.1 mm, lead 500 mm | **verified against the data sheet** - frame with 0.6 mm clearance per side, pedestal for 16.5 mm. Open point: the sheet calls the plug "XH2.54-2P" while Adafruit and BerryBase sell it as JST-PH 2.0 mm (photo: PH housing); J7 needs PH - check on delivery |
| Heat sink 14 x 14 x 7 mm (BerryBase RPI-2KKS) | shop page | dimensions from the shop page; 5.7 mm of air remain under it |

## 10. Sourcing (JLCPCB / LCSC live check 2026-11-12; DigiKey 2026-11-11 as the second source)

**Revision A2:** the board is assembled by JLCPCB, so the stock that counts is JLCPCB's assembly library. Every BOM line
was read live from that library and from lcsc.com (`gen/jlc_lookup.py refresh`, raw data in `gen/sourcing_jlc.json`):
55 lines, 136 placements, parts for one board 41.78 USD at JLCPCB's single-piece prices. 16 lines are Basic, 5 Preferred
Extended, 32 Extended (plus 2 lines that are not populated). Three lines are below 200 pieces - ADAU7002ACBZ-R7 (104), 61400826021 (116),
RF-BM-2652P2 (126) - see the exceptions in the A2 log. `hardware/outputs/bom.csv` carries, per line, the LCSC number,
library type, JLCPCB and LCSC stock, JLCPCB prices at 1 / 10 / 100, the DigiKey second source and other alternates.

| Line | A1 part | A2 part (LCSC no., JLCPCB stock 2026-11-12) | Ratings A1 -> A2 |
|---|---|---|---|
| Radio module | Silicon Labs MGM240PB32VNA3 (0) | RF-star RF-BM-2652P2 (C5440064, 126) | +20 dBm both; -40..+105 C -> -40..+85 C (exception) |
| Buck inductor | Bourns SRP7028A-6R8M (0) | Sunltech SLO0630H6R8MTT (C207841, 3,675) | 6.8 uH, 4.5 A / 8 A, 150 C: equal; DCR lower |
| Polymer capacitor 100 uF 6.3 V | KEMET T520B107M006ATE070 (207) | KEMET T520B107M006ATE040 (C116740, 2,409) | ESR 70 -> 40 mOhm |
| 22 uF 1206 | Samsung CL31A226KOHNNNE 16 V | Samsung CL31A226KAHNNNE 25 V (C12891, Basic, 2.5 M) | 16 V -> 25 V |
| 1 uF X7R 0603 | TDK C1608X7R1C105K080AC 16 V | Samsung CL10B105KA8NNNC 25 V (C29936, 4.5 M) | 16 V -> 25 V, X7R kept |
| 4.7 uF 25 V X5R 0603 | TDK C1608X5R1E475K080AC | Samsung CL10A475KA8NQNC (C69335, 746 k) | equal |
| 1 uF 50 V X5R 0603 | TDK C1608X5R1H105K080AB | Samsung CL10A105KB8NNNC (C15849, Basic, 14 M) | equal |
| 100 nF 50 V X7R 0603 | KEMET C0603C104K5RACTU | Yageo CC0603KRX7R9BB104 (C14663, Basic, 36 M) | equal |
| Crystal load capacitors | Samsung CL05C270JB5NNNC 27 pF | Fenghua 0402CG150J500NT 15 pF (C1548, Basic) | value follows the crystal |
| 24 MHz crystal | Epson TSX-3225, CL 18 pF (not stocked) | YXC X322524MOB4SI, CL 12 pF (C70590, 300 k) | +-10 ppm both; -40..+85 C |
| 10 V Zener | onsemi SZMM3Z10VT1G | onsemi MM3Z10VT1G (C39057, 21,866) | same die without AEC-Q101 |
| Status LEDs | Wurth 156120GS / BS / RS75000 reverse mount (0 / not listed / 0) | KT-0603G (C12624), KT-0603B (C2288), LTST-C191KRKT (C125099) | 30 mA each; ordinary 0603 on the other side |
| Red 0603 LED D4 | Wurth 150060RS75000 (3) | Lite-On LTST-C191KRKT (C125099, 383 k) | 30 mA / 75 mW: equal |
| Resistors 0402 1 % | Yageo RC0402FR-07, Walsin, Stackpole | UNI-ROYAL 0402WGF (see log A2-9) | 1 %, 1/16 W, 50 V: equal |

Unchanged part numbers that A1 had flagged for stock (the flag was DigiKey's stock): LMR33640ADDAR (C2836966, 2,490),
TPS2553DBVR (C55266, 53,887), 2N7002,215 (C65189, 204 k), CL31B106KBHNNNE (C89632, 472 k), GRM188R71H224KAC4D (C669503, 4,056).

**Revision A1 text (DigiKey, 2026-11-11) - kept because DigiKey is the second source of every line:**

Every BOM line was looked up on its DigiKey product page (status, stock, price at 1 and 100 pieces; for one line, the
220 nF capacitor C10, DigiKey shows status and price but no stock figure); the raw data is in
`hardware/gen/sourcing_live.json` and ends up in `hardware/outputs/bom.csv`. Rule for swaps: same footprint, every
rating equal or better, lifecycle Active - and either cheaper or in stock where the old part was not.

| Line | Old part | New part | Reason (USD at 100 pcs, DigiKey) |
|---|---|---|---|
| 24 MHz crystal | Abracon ABM8-24.000MHZ-B2-T (0.53) | Epson TSX-3225 24.0000MF18X-C0 (0.30) | cheaper; +-10 ppm tolerance and +-10 ppm over -20..+75 C (Epson brief; DigiKey lists +-18 ppm over -40..85 C) instead of +-20 / +-50 ppm, same 18 pF load, same pads |
| 10k 1 % 0402 (11 x) | Yageo RC0402FR-0710KL (0.0108) | Walsin WR04X1002FTL (0.0061) | cheaper, identical ratings |
| 100k 1 % 0402 (14 x) | Yageo RC0402FR-07100KL (0.0108) | Stackpole RMCF0402FT100K (0.0091) | cheaper, identical ratings |
| 49.9k 1 % 0402 | Yageo RC0402FR-0749K9L (0 in stock) | Stackpole RMCF0402FT49K9 (0.0096) | in stock and cheaper |
| 24.9k 1 % 0402 | (new value, was 24.3k) | Stackpole RMCF0402FT24K9 (0.0091) | value change (log no. 2) |
| 1 uF 50 V X5R 0603 | Samsung CL10A105KB8NNNC (0 in stock) | TDK C1608X5R1H105K080AB (0.058) | in stock, identical ratings |
| 100 nF 50 V X7R 0603 | Samsung CL10B104KB8NNNC (0 in stock) | KEMET C0603C104K5RACTU (0.046) | in stock, identical ratings |
| 4.7 uF X5R 0603 | Samsung CL10A475KO8NNNC 16 V (0 in stock) | TDK C1608X5R1E475K080AC 25 V (0.091) | in stock, higher voltage rating |
| 1 uF 16 V | Samsung CL05A105KO5NNNC X5R 0402 | TDK C1608X7R1C105K080AC X7R 0603 (0.041) | datasheet finding (log no. 4): footprint changes on purpose |
| 10 uF 50 V 1206 | Samsung CL31A106KBHNNNE X5R | Samsung CL31B106KBHNNNE X7R (0.168) | datasheet finding (log no. 3); 0 in stock at DigiKey, see below |
| 220 nF 50 V X7R 0603 | (new) | Murata GRM188R71H224KAC4D (0.052) | datasheet finding (log no. 3); Active, 17 weeks lead time, **the DigiKey page shows no stock figure** (looked up twice) |
| 10 V zener SOD-323 | onsemi MM3Z10VT1G (0 in stock) | onsemi SZMM3Z10VT1G (0.109) | same die, AEC-Q101 grade, in stock |

Not swapped although a cheaper or in-stock candidate exists - because a rating would go down, or (TPS2553) because the
in-stock alternative is the identical device on another reel and only changes the order code, or (10 uF) because the only
equal part in stock is a 2,000-piece Marketplace item:

- **2N7002,215** (0 in stock): 2N7002BK,215 is in stock and 0.3 cent dearer, but VGS is +-20 V instead of +-30 V.
- **22 uF 16 V X5R 1206, CL31A226KOHNNNE** (0 in stock): the TDK part in stock is +-20 % instead of +-10 %, the Samsung
  part in stock is only 0.85 mm thick (worse DC bias).
- **TPS2553DBVR** (0 in stock until mid-December): AP22653W6-7 is a third of the price but only rated 3.0-5.5 V and
  Diodes AP2553W6-7 is NRND. **TPS2553DBVT is the identical device on the 250-piece reel (296-23990-1-ND, 2,503 in
  stock, +0.16 USD each): order that if boards are built before the DBVR reel is back.** The BOM keeps the DBVR order
  code because it is the cheaper one for production.
- **10 uF 50 V X7R 1206, CL31B106KBHNNNE** (0 in stock): the only equal-rating part DigiKey can ship is Cal-Chip
  GMC31X7R106K50NT, a Marketplace item with a 2,000-piece minimum (0.403 USD each, separate shipping) - fine for
  production, useless for prototypes. TDK C3216X7R1H106K160AC is expected in February 2027. For a prototype the X5R part
  of revision A (CL31A106KBHNNNE) can be fitted; it loses more capacitance under bias and at temperature.
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
- Encoding: H.264 High, yuv420p, CRF 17, converted with the BT.709 matrix and tagged as BT.709 limited range. The first
  encode used ffmpeg's defaults (BT.601 matrix, no tags), which HD players decode as BT.709 - the board came out a
  darker green than rendered. Found by the review, re-encoded from the same frames.
- The first render of the video was done before the review fixes; 53 of the 151 footprints have moved since (the buck
  power stage, the two USB ESD parts, small parts around the PD controller and the hub) and the board was re-routed.
  The still image and the 866 frames of the video that show the PCB (frames 150 to 1015: from the moment the device
  lifts off until it is closed again) were rendered again from the final board, 1 h 54 min. The 394 frames before and
  after show only the closed device and were kept: shell and base did not change (the STL files are byte-identical),
  the frame-to-frame difference across the two joins is the same as between their neighbours (no jump), and five of
  the kept frames (75, 1016, 1130, 1200, 1255) rendered again from the final board differ from the kept ones by at
  most 3 of 255 in single pixels. The committed MP4 is the encode of that frame set.
- `build_showcase.sh` checks its tools before the long render, runs Blender with `--python-exit-code` and refuses to
  encode while a frame is missing; a frame only counts as rendered when the PNG is complete (IEND chunk). Blender 5 is
  refused: the script uses the pre-5.0 animation API and was only run with 4.5.16.

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
6. ~~USB skew~~ - all pairs matched to 0.00 mm, stub-free, no vias; verified by an independent re-computation
   (section 6a, log no. 18). The first A1 result was wrong for port 2 (4.9 mm).
7. ~~Stock and prices~~ - DigiKey is live. **Mouser is not** (see below).

Closed in the third session (revision A2):

8. ~~Mouser column~~ - removed; the JLCPCB assembly library is the primary source, DigiKey the second (log A2-1).
9. ~~Stock risks of A1~~ - every line is in stock at JLCPCB (log A2-2, section 10); three thin lines are listed below.
10. ~~USB lines not coupled / impedance from a formula~~ - upstream pair coupled, geometry from JLCPCB's calculator on
    a stack-up JLCPCB offers (log A2-20 to A2-22).
11. ~~Buck layout items "before a production spin"~~ - PGND tie and vias, feed and VBUS widths, vias out of lead pads,
    URL text: all fixed and gated by scripts (log A2-15 to A2-18, A2-26).
12. ~~Firmware consequences of the MGM240P pin-out~~ - the radio is a CC2652P now (log A2-3, A2-4, A2-32).

Still open:

1. **Thin stock at JLCPCB on 2026-11-12:** ADAU7002ACBZ-R7 (104), Wurth 61400826021 (116), RF-BM-2652P2 (126); the CM4
   socket DF40C-100DS-0.4V(51) has 1,106 pieces at JLCPCB and 0 at LCSC (not being restocked there; the (58) reel
   variant C3642394 is the same part). Buy the thin parts into the JLCPCB parts library before ordering
   (`fab/ORDER_GUIDE.md`); the BOM names the alternates.
2. **Documents the manufacturer still does not serve to scripts** (read from authorised distributors instead, table in
   the A2 log): MGM240P (moot), C&K JS, ADAU7002, MAX98357A (Rev 13 read, Rev 16 exists), USBLC6-2 (Rev 5 read),
   SMBJ, 2N7002. Generic passives, diodes, the pin header and the Tag-Connect pads use KiCad standard footprints and
   were not checked against a manufacturer document (last row of the first table in section 9).
3. **Mechanical points to check on real parts:** the plug of the Adafruit 3351 speaker (its data sheet says XH 2.54 mm,
   the shops say JST-PH 2.0 mm; J7 is PH), the USB-A flange lip (0.45 / 15.95 mm, scaled), the C&K body tolerance.
4. **USB impedance is calculated, not measured.** 0.14 / 0.16 mm on JLC04161H-3313 is 89.96 ohm in JLCPCB's calculator;
   JLCPCB's tolerance without the paid impedance option is not stated. The downstream lines are two uncoupled 45 ohm
   lines per port (log A2-22).
5. **The radio flashing script has only met a simulated radio** (`tools/flash_zigbee.sh`; what was and was not tested
   is in `fab/ASSEMBLY_AND_TEST.md`). How RF-star ships the module (blank, or with a firmware whose backdoor is
   disabled) decides whether the first flash goes over the serial boot loader or over JTAG; the script handles both.
6. **JLCPCB's order form behind the login was not reachable** (BOM / CPL upload, parts matching, placement preview,
   final price). Those steps of `fab/ORDER_GUIDE.md` come from JLCPCB's help articles of 2026-11-12, the PCB price and
   the shipping prices from the live form.
7. Nothing here has been powered on. Treat revision A2 as a prototype spin.
