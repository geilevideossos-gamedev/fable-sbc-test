# Operating system: Home Assistant OS for VoxHub CM4

The carrier is electrically a Raspberry Pi CM4 board, so it runs the **official HAOS `rpi4-64` target**.
Everything board-specific is expressed in `config.txt` (stock Raspberry Pi overlays) or, for from-source
builds, in one extra device tree overlay.

```
os/
├── build-image.sh                 one script, two modes (repack | full)
├── config/config-voxhub.txt       block appended to config.txt (stock overlays only, OTA-safe)
├── overlay/voxhub-overlay.dts     single custom overlay (audio, LEDs, mute switch, UART4, I2C1)
├── board/voxhub/meta              HAOS board metadata (BOARD_ID stays rpi4-64)
├── board/voxhub/kernel.config     kernel config fragment (driver guard)
├── board/voxhub_defconfig         Buildroot defconfig as generated from rpi4_64_defconfig (HAOS 18.5)
├── package/voxhub-overlay/        Buildroot package that builds voxhub.dtbo with host-dtc
└── full-build-attempt.log         log of the from-source build attempt in the sandbox
```

## Quick start (recommended): repack the latest official release

```bash
sudo apt install git curl xz-utils fdisk mtools device-tree-compiler
./os/build-image.sh repack --wifi-ssid "MyWifi" --wifi-psk "secret" --wifi-country DE
```

What it does (no root, no loop devices, ~2 minutes):

1. finds the newest stable HAOS tag (`git ls-remote`, tags of the form `MAJOR.MINOR`), or uses `--version`;
2. downloads `haos_rpi4-64-<ver>.img.xz` from the official GitHub release and checks the archive;
3. edits the FAT boot partition in place with mtools: appends `config/config-voxhub.txt` to `config.txt`,
   checks that every referenced stock overlay exists in that release, compiles `voxhub-overlay.dts` and
   test-applies it to the release's `bcm2711-rpi-cm4.dtb` (`fdtoverlay`);
4. optionally writes a NetworkManager Wi-Fi profile to `CONFIG/network/` on the boot partition (HAOS imports
   it on first boot - the board has no Ethernet or HDMI) and sets the Wi-Fi regulatory domain;
5. writes `os/output/haos_voxhub-cm4-<ver>.img.xz` + `.sha256`.

Flash with Raspberry Pi Imager / balenaEtcher or
`xz -dc os/output/haos_voxhub-cm4-18.5.img.xz | sudo dd of=/dev/sdX bs=4M conv=fsync`.

### Why stock overlays?

HAOS updates the boot partition with this hook (`buildroot-external/ota/rauc-hook`):
`rm -f /mnt/boot/overlays/*`, copy the new files, **restore `*.txt`**. A custom `.dtbo` would vanish with
the first OS update, while `config.txt` survives. The hardware was therefore wired so that stock overlays
describe it completely:

| Function | config.txt | Result |
|---|---|---|
| USB hub / USB-A | `otg_mode=1` (in `[cm4]`) | xHCI host on the CM4 USB2 pins |
| Microphones + speaker | `dtoverlay=googlevoicehat-soundcard` | ALSA card `sndrpigooglevoi`, capture + playback, amp enable on GPIO16 |
| Zigbee radio | `dtoverlay=uart4,ctsrts` | `/dev/ttyAMA1` on GPIO8-11 |
| Status LEDs | `dtoverlay=gpio-led,gpio=5,label=voxhub-green` (and GPIO6 blue) | `/sys/class/leds/voxhub-green`, `voxhub-blue` |
| Mute switch sense | `dtoverlay=gpio-key,gpio=27,keycode=248,...` | input event `KEY_MICMUTE` while muted |
| PD controller status | `dtparam=i2c_arm=on` | CYPD3177 at 0x08 on `i2c-1` |

Because the board ID is still `rpi4-64`, the device keeps receiving the official OTA updates
("pulls the latest HAOS") after the first boot, too.

`--custom-overlay` uses `dtoverlay=voxhub` instead (nicer names, mute as a real `EV_SW` switch) - only do
this if you manage updates yourself.

## From source: official HAOS build system + `voxhub` board

```bash
./os/build-image.sh full                      # regular user + Docker: uses the HAOS builder container (scripts/enter.sh)
VOXHUB_NO_DOCKER=1 ./os/build-image.sh full   # build directly on a Debian / Ubuntu host
VOXHUB_NO_DOCKER=1 VOXHUB_GITHUB_VIA_GIT=1 ./os/build-image.sh full   # ... on a network that blocks GitHub tarball URLs
```

The full build must run as a **regular user** with sudo and Docker access - HAOS's `enter.sh` and several Buildroot
host packages refuse to run as root, and the script checks for it. Host builds need the tools of the HAOS builder
image (`make gcc g++ bc cpio rsync unzip wget curl file perl patch bzip2 xz jq skopeo sudo docker qemu-img pigz zip
automake help2man makeinfo flock python3`; the script lists what is missing), plus Docker and loop devices for the very
last step (the Supervisor containers are imported into the data partition with docker-in-docker).

On a host build the script points Buildroot's download directory and ccache to `os/output/cache/` (the HAOS defconfig
uses `/cache`, which only exists inside the builder container).

`VOXHUB_GITHUB_VIA_GIT=1` is for networks whose proxy refuses `https://github.com/<owner>/<repo>/archive/...`
downloads while git access to the same public repositories works. Before the build starts, the script asks Buildroot
for the complete download list (`make show-info`), and for every GitHub "archive" source that Buildroot's own mirror
(sources.buildroot.net) does not carry it runs `git fetch --depth 1` and `git archive | gzip -n` into
`os/output/cache/github-mirror/`, which is then used as `BR2_PRIMARY_SITE`. Buildroot verifies each of these files
against its `.hash` file like any other download (the git-made tarballs are byte-identical to GitHub's).

The script clones `home-assistant/operating-system` at the latest release tag (with the Buildroot
submodule) and adds, without modifying any upstream file except one `source` line in `Config.in`:

- `buildroot-external/board/raspberrypi/voxhub/` - copy of `rpi4-64` + our `meta`, `kernel.config`, `config.txt`;
- `buildroot-external/package/voxhub-overlay/` - builds `voxhub.dtbo`; the shared Raspberry Pi
  `haos-hook.sh` copies every `*.dtbo` from the images directory to `/overlays`;
- `buildroot-external/configs/voxhub_defconfig` - **derived with `sed` from the upstream `rpi4_64_defconfig`**
  at build time (board directory, extra kernel fragment, CM4-only DTB, `BR2_PACKAGE_VOXHUB_OVERLAY=y`), so it
  follows upstream kernel/firmware bumps automatically. A copy generated against HAOS 18.5 is checked in
  as `board/voxhub_defconfig`.

Then `make voxhub` produces `haos_rpi4-64-<ver>.img.xz` (copied to `os/output/haos_voxhub-cm4-<ver>-full.img.xz`).
Requirements: 30-40 GB disk, 8 GB RAM, 1-3 hours on a 16-core machine (see the measured numbers below for 4 cores).

## Verification status

| Check | Result |
|---|---|
| `build-image.sh repack` executed end to end | **OK** - `haos_voxhub-cm4-18.5.img.xz` (310 MB) produced in 93 s; GPT verified with `sgdisk -v`, 8 partitions intact, `config.txt` contains the VoxHub block |
| Stock overlays referenced exist in HAOS 18.5 | **OK** - `googlevoicehat-soundcard`, `uart4`, `gpio-led`, `gpio-key` found in `/overlays` of the release image |
| Kernel drivers present in HAOS 18.5 (rootfs extracted from the image, kernel 6.18.59-haos-raspi) | **OK** - `snd-soc-rpi-simple-soundcard` (contains `googlevoicehat,googlevoicehat-soundcard`), `snd-soc-googlevoicehat-codec`, `snd-soc-bcm2835-i2s`, `gpio_keys` modules; `leds-gpio`, `xhci`, `dwc2` built in |
| `googlevoicehat-soundcard.dtbo` decompiled | **OK** - `sdmode-gpios = <&gpio 16 0>`, matches the schematic |
| `voxhub-overlay.dts` compiles (`dtc -@`) and applies to the real `bcm2711-rpi-cm4.dtb` (`fdtoverlay`) | **OK** |
| `voxhub_defconfig` accepted by Buildroot (`make voxhub_defconfig`) | **OK** - `.config` written, `BR2_PACKAGE_VOXHUB_OVERLAY=y` |
| Full from-source build | **FAILED in the sandbox, as expected** - see below |
| Boot on hardware | not done (no hardware) |

### Where and why the full build fails here

The build was started on the sandbox host (`VOXHUB_NO_DOCKER=1`; the HAOS builder container cannot be
built because `deb.debian.org` is blocked). It passes configuration and the first host package, then stops
at the **first source tarball download**:

```
>>> host-pkgconf 2.3.0 Downloading
wget ... 'https://distfiles.ariadne.space/pkgconf/pkgconf-2.3.0.tar.xz'
Proxy tunneling failed: Forbidden   Unable to establish SSL connection.
wget ... 'https://sources.buildroot.net/pkgconf/pkgconf-2.3.0.tar.xz'
Proxy tunneling failed: Forbidden   Unable to establish SSL connection.
make[1]: *** [package/pkg-generic.mk:179: .../host-pkgconf-2.3.0/.stamp_downloaded] Error 1
```

Cause: the sandbox's egress proxy only allows a small set of hosts; neither the upstream tarball hosts
(ariadne.space, kernel.org, gnu.org, ...) nor Buildroot's mirror `sources.buildroot.net` are reachable.
Nothing in the board definition is involved. The full log tail is in `full-build-attempt.log`.
On a machine with normal internet access the same command proceeds; it has **not** been run to completion,
so treat the from-source path as unverified beyond the configuration stage.

## First boot

1. Flash the image, insert the card, plug in a USB-C PD charger (>= 20 W, 9 V capable). Green PWR LED on;
   red PD-FAULT LED means the charger offers no 9-20 V profile.
2. Wait ~5 minutes on first boot, open `http://homeassistant.local:8123`.
3. Settings -> System -> Hardware should list the `sndrpigooglevoi` sound card and `/dev/ttyAMA1`.
4. Continue with `assistant/README.md`.
