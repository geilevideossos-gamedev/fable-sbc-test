# Satellite image: the second VoxHub board without its own Home Assistant

The second board is the **satellite** of the two-device system. It runs no Home Assistant. It gives the hub its
wake word, microphones, speaker, mute switch and LEDs over Wi-Fi, and its radio runs the Zigbee router firmware
that extends the hub's Zigbee network. The hardware is identical to the hub (revision A2); only the SD card differs.

```
os/satellite/
├── build-satellite-image.sh     builds the flashable SD card image (run as root on Linux)
├── lva-constraints.txt          exact Python package versions of the first verified build
└── rootfs/                      files copied into the image
    ├── etc/systemd/system/      voxhub-lva, voxhub-peripherals, voxhub-hubwatch
    ├── etc/wireplumber/         keeps the googlevoicehat card at 48 kHz and awake
    ├── etc/apt/apt.conf.d/      automatic security updates
    ├── etc/systemd/journald.conf.d/  journal limited to 64 MB
    └── usr/local/bin/voxhub-status   status report on the device
```

## Build

```bash
sudo apt install git curl xz-utils fdisk parted e2fsprogs openssl python3 device-tree-compiler qemu-user-static binfmt-support
sudo os/satellite/build-satellite-image.sh \
    --wifi-ssid 'NAME OF YOUR WIFI' --wifi-psk 'PASSWORD OF YOUR WIFI' --wifi-country AT \
    --hub 192.168.1.10 --room 'Downstairs' --password 'password for the user voxhub'
```

- `--hub` is the address of the hub. Use its fixed IP address (give the hub a DHCP reservation in the router);
  a name such as `homeassistant.local` also works, the satellite resolves it again every minute.
- `--room` names the device in Home Assistant ("VoxHub Downstairs"). The room itself is assigned in Home
  Assistant (`fab/ASSEMBLY_AND_TEST.md`, chapter 7).
- Without `--password` a random password is printed at the end. `--ssh-key FILE` adds a public key.
- Other options: `--help`.
- Result: `os/output/voxhub-satellite-2026-10-06-lva1.1.18.img.xz` plus `.sha256` and the list of the Python packages
  inside (`.packages.txt`). Write it with Raspberry Pi Imager ("Use custom") or
  `xz -dc <file> | sudo dd of=/dev/sdX bs=4M conv=fsync`. If Imager offers to apply its own settings, decline:
  the image does not use them.
- Duration: about 25 minutes on an x86 PC with 4 cores (the packages are installed into the image in emulation);
  disk: about 10 GB in the work directory.

The script needs root (loop devices, mounts, chroot). On an x86 machine the aarch64 programs of the image run
through `qemu-user-static` and `binfmt_misc`; the script stops with a clear message if that is missing.

## What is in the image

| Part | Content |
|---|---|
| Base | Raspberry Pi OS Lite 64-bit `2026-10-06-raspios-trixie-arm64-lite` (Debian 13), SHA256 checked |
| Board configuration | the same `config.txt` block as the hub (`os/config/config-voxhub.txt`): USB host, sound card `googlevoicehat-soundcard`, UART4 for the radio, LEDs on GPIO5 / GPIO6, mute switch on GPIO27, I2C1 |
| Satellite | Linux Voice Assistant 1.1.18 (git tag `v1.1.18`, commit `b55d36af`) in `/opt/linux-voice-assistant/.venv`, PipeWire as sound server of the user `voxhub`, microWakeWord "Okay Nabu" (default) |
| `voxhub-lva.service` | finds the googlevoicehat source and sink, sets the microphone gain (default +12 dB), starts Linux Voice Assistant as user `voxhub` with the ESPHome API on port 6053 and the peripheral API on 127.0.0.1:6055 |
| `voxhub-peripherals.service` | status LEDs and mute switch (same code and LED meanings as the hub add-on) |
| `voxhub-hubwatch.service` | firewall: port 6053 only from the hub, port 6055 only local; checks that Home Assistant answers at `http://<hub>:8123` (answers are played from there) |
| Settings | `/etc/voxhub/satellite.env` (name, room, hub, wake word, microphone gain); Wi-Fi in `/etc/NetworkManager/system-connections/voxhub-wifi.nmconnection` |
| Updates | `unattended-upgrades` daily for Debian, Debian security and the Raspberry Pi archive (kernel, firmware); reboot at 04:30 when an update needs it |
| Radio | `voxhub-flash-zigbee` (= `tools/flash_zigbee.sh`; picks the role `satellite` by itself) with the router firmware and cc2538-bsl stored in the image, so flashing needs no internet |
| Access | user `voxhub` (sudo), SSH on; host keys are generated at the first boot; cloud-init and the first-boot user dialog are switched off |
| Discovery | Linux Voice Assistant announces itself by zeroconf (`_esphomelib._tcp`); Home Assistant shows it as a discovered ESPHome device |

Why each of these choices: `DECISIONS.md`, section "Two devices: hub and satellite", entries S-6 to S-11 and S-19 ff.

## On the device

```bash
ssh voxhub@voxhub-satellite.local
sudo voxhub-status                              # services, hub, firewall, sound card, LEDs, last log lines
sudo voxhub-flash-zigbee --role satellite       # Zigbee router firmware (once)
journalctl -u voxhub-lva -f                     # follow Linux Voice Assistant
sudo nano /etc/voxhub/satellite.env             # change hub address, wake word, gain; then: sudo systemctl restart voxhub-lva voxhub-hubwatch
```

## Verification

The build ends with checks of the finished image (`--no-verify` skips them). What they cover and what the
first build printed is listed in `os/README.md`, section "Satellite image: verification".
