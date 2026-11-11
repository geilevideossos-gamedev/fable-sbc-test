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
└── full-build-attempt.log         log excerpts of the from-source build attempts (9 on 2026-11-11, the last one complete)
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
| Zigbee radio | `dtoverlay=uart4,ctsrts` | `/dev/ttyAMA4` on GPIO8-11 (the kernel of HAOS 18.5 has fixed aliases: `serial4 = &uart4`) |
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
VOXHUB_GOPROXY=https://proxy.golang.org ./os/build-image.sh full      # ... where gopkg.in or other Go module hosts are unreachable
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

`VOXHUB_GOPROXY=<url>` is for networks from which the hosts of single Go modules cannot be reached. Buildroot vendors
the modules of its Go packages (tempio, os-agent, ...) with `GOPROXY=direct`, i.e. from each module's own host; with this
option the script puts the given module proxy into `buildroot/package/pkg-golang.mk` of the cloned tree instead. The
modules are still checked against `go.sum`, and the vendored tarball against Buildroot's `.hash` file.

On a host build the script also redirects the RAUC signing key and certificate, which the HAOS scripts expect under
`/build` (the mount point inside the builder container), to the root of the cloned source tree, and it builds Buildroot's `host-libyaml` first if `/usr/include/yaml.h` exists (i.e. `libyaml-dev`
is installed): U-Boot's device tree compiler enables YAML support when it sees that header and would then fail to link,
because Buildroot's pkg-config does not know the host's library. The HAOS builder container has no `libyaml-dev`.

The script clones `home-assistant/operating-system` at the latest release tag (with the Buildroot
submodule) and adds the board definition. The only upstream file this touches is one `source` line in `Config.in`;
host builds and `VOXHUB_GOPROXY` additionally edit the upstream files named above (`scripts/rauc.sh`, `genimage/*.cfg`,
`buildroot/package/pkg-golang.mk`) in the cloned tree, so use a fresh clone if you switch to the Docker path afterwards.
An existing clone is only reused if it is at the requested version. Added:

- `buildroot-external/board/raspberrypi/voxhub/` - copy of `rpi4-64` + our `meta`, `kernel.config`, `config.txt`;
- `buildroot-external/package/voxhub-overlay/` - builds `voxhub.dtbo`; the shared Raspberry Pi
  `haos-hook.sh` copies every `*.dtbo` from the images directory to `/overlays`;
- `buildroot-external/configs/voxhub_defconfig` - **derived with `sed` from the upstream `rpi4_64_defconfig`**
  at build time (board directory, extra kernel fragment, CM4-only DTB, `BR2_PACKAGE_VOXHUB_OVERLAY=y`), so it
  follows upstream kernel/firmware bumps automatically. A copy generated against HAOS 18.5 is checked in
  as `board/voxhub_defconfig`.

Then `make voxhub` produces `haos_rpi4-64-<ver>.img.xz` (copied to `os/output/haos_voxhub-cm4-<ver>-full.img.xz`, with a
`.sha256` file). The `--wifi-*` options only work in repack mode; for a full-build image copy a NetworkManager profile to
`CONFIG/network/` on the boot partition yourself (the board has no Ethernet).
Requirements: 30-40 GB disk, 8 GB RAM, 1-3 hours on a 16-core machine (measured on 4 shared cores: about 6 hours, see below).

## Verification status

| Check | Result |
|---|---|
| `build-image.sh repack` executed end to end | **OK** - `haos_voxhub-cm4-18.5.img.xz` (310 MB) produced in 93 s; GPT verified with `sgdisk -v`, 8 partitions intact, `config.txt` contains the VoxHub block |
| Stock overlays referenced exist in HAOS 18.5 | **OK** - `googlevoicehat-soundcard`, `uart4`, `gpio-led`, `gpio-key` found in `/overlays` of the release image |
| Kernel drivers present in HAOS 18.5 (rootfs extracted from the image, kernel 6.18.59-haos-raspi) | **OK** - `snd-soc-rpi-simple-soundcard` (contains `googlevoicehat,googlevoicehat-soundcard`), `snd-soc-googlevoicehat-codec`, `snd-soc-bcm2835-i2s`, `gpio_keys` modules; `leds-gpio`, `xhci`, `dwc2` built in |
| `googlevoicehat-soundcard.dtbo` decompiled | **OK** - `sdmode-gpios = <&gpio 16 0>`, matches the schematic |
| `voxhub-overlay.dts` compiles (`dtc -@`) and applies to the real `bcm2711-rpi-cm4.dtb` (`fdtoverlay`) | **OK** |
| `voxhub_defconfig` accepted by Buildroot (`make voxhub_defconfig`) | **OK** - `.config` written, `BR2_PACKAGE_VOXHUB_OVERLAY=y` |
| Full from-source build (`build-image.sh full`, host build) | **OK** on the ninth attempt (2026-11-11): `haos_voxhub-cm4-18.5-full.img.xz`, 317 MiB (911 MiB unpacked), plus the OTA bundle `haos_rpi4-64-18.5.raucb` (185 MiB). What stopped attempts 1-8 is in the run log below |
| Full-build image inspected | **OK** - GPT with the 8 HAOS partitions; boot partition: `bcm2711-rpi-cm4.dtb` only, `u-boot.bin`, `config.txt` with the VoxHub block (`dtoverlay=voxhub`, `otg_mode=1`), `overlays/voxhub.dtbo` built by the `voxhub-overlay` package - it applies to the DTB of the same image (`fdtoverlay`) and gives the mute switch, both LEDs, UART4 (`serial4`) and the sound card nodes; root file system (EROFS): `VERSION="18.5 (VoxHub CM4 (RaspberryPi 4 64bit))"`, `VARIANT_ID=rpi4-64`, kernel 6.18.59-haos-raspi with `snd-soc-bcm2835-i2s`, `snd-soc-rpi-simple-soundcard`, `snd-soc-googlevoicehat-codec`, `snd-soc-max98357a`, `snd-soc-adau7002`, `gpio_keys`, `i2c-bcm2835` as modules and `leds-gpio`, `amba-pl011`, `xhci-hcd`, `dwc2` built in; RAUC `compatible=haos-rpi4-64`; data partition with the Supervisor 2026.11.0, CLI, DNS, audio, multicast, observer and landing-page containers |
| Boot on hardware | not done (no hardware) |

### Full build: run log of 2026-11-11

Machine: cloud sandbox, 4 cores, 15 GB RAM, about 40 GB disk allowance, outbound HTTPS through a filtering proxy.
Command (as the unprivileged user `builder`, HAOS 18.5, 218 Buildroot packages):

```bash
CCACHE_DISABLE=1 VOXHUB_NO_DOCKER=1 VOXHUB_GITHUB_VIA_GIT=1 os/build-image.sh full --version 18.5
# from attempt 7 on additionally: VOXHUB_GOPROXY=https://proxy.golang.org
```

| Attempt | Got as far as | Stopped by | What was changed |
|---|---|---|---|
| first session (2026-11-10) | `host-pkgconf 2.3.0 Downloading` | the proxy of that session refused every tarball host (`Proxy tunneling failed: Forbidden`) | nothing - network policy |
| 1 | Buildroot configuration | `mkdir: cannot create directory '/cache'`: the HAOS defconfig keeps downloads and ccache in `/cache`, which only exists inside the HAOS builder container; `scripts/enter.sh` also refuses to run as root | `build-image.sh` exports `BR2_DL_DIR` / `BR_CACHE_DIR` (`os/output/cache/`) on host builds and checks for a non-root user |
| 2 | 231 build steps in 17 min, then `linux-headers` download | `ERROR 403: Forbidden` from the proxy for `https://github.com/raspberrypi/linux/archive/<commit>.tar.gz`. This sandbox refuses every GitHub `/archive/` URL (37 of the 218 sources), while `git fetch` from the same repositories is allowed | new option `VOXHUB_GITHUB_VIA_GIT=1` (see above) |
| 3 | source prefetch | bug in the new prefetch code (a `grep` without match ended the script under `set -o pipefail`) | fixed |
| 4 | 3 h 00 min, 153 of 218 packages installed, stopped in `libblockdev 3.3.1 Building` | `libtool: error: '.../output/build/util-linux-2.40.4/libuuid.la' is not a valid libtool archive`. **Self-inflicted by a disk-space helper of the sandbox session (not part of this repository)**: to stay inside the disk allowance it emptied the build directories of finished packages, but the staging copies of `libfdisk.la` / `libmount.la` (and four more) point back into those build directories | the four affected build directories (`util-linux`, `host-util-linux`, `gnutls`, `dhcp`) were deleted so that Buildroot rebuilds them; the helper now leaves every directory alone that a libtool archive refers to |
| 5 | 2 h 19 min more, 190 of 218 packages installed (kernel 6.18 with the `voxhub` fragment and its out-of-tree modules built), stopped in `uboot 2026.04 Building` | `scripts/dtc/yamltree.o: undefined reference to 'yaml_emitter_emit'` ... `make[4]: *** [scripts/Makefile.host:105: scripts/dtc/dtc] Error 1`. **Host contamination:** U-Boot's dtc enables YAML support when `/usr/include/yaml.h` exists on the build host (Buildroot passes `PKG_CONFIG_SYSROOT_DIR=/`), then asks Buildroot's own pkg-config for the library, which only knows Buildroot's host directory. This sandbox image ships `libyaml-dev`; the HAOS builder container does not | on host builds `build-image.sh` now builds Buildroot's `host-libyaml` first when `/usr/include/yaml.h` exists |
| 6 | 7 min more (U-Boot now builds), 214 of 218 packages installed, stopped in `host-tempio 2026.07.0 Downloading` | `gopkg.in/yaml.v3: unrecognized import path ... https fetch: Get "https://gopkg.in/yaml.v3?go-get=1": net/http: TLS handshake timeout`, then `ERROR 403: Forbidden` for the pre-vendored tarball on GitHub and 404 on Buildroot's mirror. Buildroot vendors Go modules with `GOPROXY=direct`; **gopkg.in cannot be reached from this sandbox** (three plain HTTPS requests timed out as well), while the official module proxy can | new option `VOXHUB_GOPROXY` (see above) |
| 7 | 4 min more: **all 218 packages built and installed** (tempio through the module proxy, the `hassio` data partition with the Supervisor containers, `voxhub-overlay`), stopped in `Finalizing target directory` | `python3.12: can't open file '.../output/build/python3-3.12.15/Lib/compileall.py'`. Self-inflicted again: the disk-space helper of the sandbox session had emptied the python3 build directory in attempt 4, and Buildroot compiles the `.pyc` files from there at the very end | python3 build directory deleted (Buildroot rebuilt it), helper switched off for good |
| 8 | 5 min more: target finalised, root file system overlays copied, stopped in `post-build.sh` | `req: Can't open "/build/key.pem" for writing, No such file or directory`: the HAOS scripts generate and read the RAUC development signing key under `/build`, the mount point of the source tree inside the builder container (`scripts/rauc.sh`, `genimage/image-raucb-*.cfg`) | on host builds `build-image.sh` rewrites these paths to the root of the cloned tree |
| 9 | 5.5 min more: `post-build.sh`, root file system (EROFS), `post-image.sh`, disk image and OTA bundle - **`[voxhub-os] done: os/output/haos_voxhub-cm4-18.5-full.img.xz`, exit 0** | - | - |

None of the eight stops had anything to do with the board definition. Two were network policy of the sandbox (GitHub
tarball URLs, gopkg.in), two were mistakes of the build session itself (the disk-space helper), one a bug in the new
prefetch code, and three are things every **host** build of HAOS runs into because the upstream scripts assume the builder
container: `/cache`, `/build/key.pem`, and a host with `libyaml-dev`. `build-image.sh` now handles all of these, so the
command above runs through in one go on such a machine; attempts 6 to 9 took 4 to 7 minutes each because Buildroot
continues where it stopped. Log excerpts are in `full-build-attempt.log`.

Measured: about 6 hours of wall-clock time over all attempts on 4 cores that were shared with a CPU render for most of
the time (the build ran at low priority), 218 packages, 7 container images. Disk: 13 GB build tree + 3.8 GB download
cache at the end, with 15.7 GB of finished build directories deleted along the way - plan for about 35 GB.

Not done here: the Docker path (`scripts/enter.sh` of HAOS, used when Docker is available and `VOXHUB_NO_DOCKER` is not
set) was not run, because the sandbox session runs as root inside a container; it is HAOS's own unmodified flow. And the
image has not been booted - there is no hardware.

## First boot

1. Flash the image, insert the card, plug in a USB-C PD charger (>= 20 W, 9 V capable). Green PWR LED on;
   red PD-FAULT LED means the charger offers no 9-20 V profile.
2. Wait ~5 minutes on first boot, open `http://homeassistant.local:8123`.
3. Settings -> System -> Hardware should list the `sndrpigooglevoi` sound card and `/dev/ttyAMA4`.
4. Continue with `assistant/README.md`.
