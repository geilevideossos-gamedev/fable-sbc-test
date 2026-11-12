#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

BASE_NAME="2026-10-06-raspios-trixie-arm64-lite"
BASE_URL="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-10-06/${BASE_NAME}.img.xz"
BASE_SHA256="483db18a48da399b5b7022ffae9a07bc6d99daab30e593aedac09b69ff422843"
LVA_REPO="https://github.com/OHF-Voice/linux-voice-assistant.git"
LVA_TAG="v1.1.18"
LVA_VERSION="1.1.18"
LVA_COMMIT="b55d36af522c263eeed4e023d6ebf30da47e4710"
GROW_MIB=1536
WAKE_WORDS="okay_nabu hey_jarvis alexa hey_mycroft hey_luna hey_morgan hey_home_assistant okay_computer choo_choo_homie"
PACKAGES=(
    pipewire pipewire-pulse wireplumber pipewire-alsa pulseaudio-utils libmpv2 libpulse0 alsa-utils
    python3-venv nftables unattended-upgrades python3-serial python3-intelhex gpiod
    libnss-mdns avahi-daemon ca-certificates curl
)

WIFI_SSID=""
WIFI_PSK=""
WIFI_COUNTRY="AT"
HUB=""
HUB_PORT=8123
ROOM=""
NAME=""
HOST_NAME="voxhub-satellite"
PASSWORD=""
SSH_KEY_FILE=""
WAKE_WORD="okay_nabu"
MIC_GAIN="4"
TIMEZONE="Europe/Vienna"
FIREWALL=1
BASE_IMAGE=""
OUT="$REPO/os/output"
KEEP=0
VERIFY=1
COMPRESS=1

WORK=""
ROOT=""
BOOT_MODE=""
BINFMT_FLAGS=""
LOOP=""
MOUNTED=()
GENERATED_PASSWORD=0

log() {
    printf '\033[1m[voxhub-satellite]\033[0m %s\n' "$*"
}

fail() {
    printf '\nERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'HELP'
build-satellite-image.sh - flashable SD card image for the VoxHub satellite (second board)

Raspberry Pi OS Lite 64-bit (Debian 13) with Linux Voice Assistant 1.1.18, the VoxHub
sound card / LED / mute / radio configuration of the hub, LED and mute-switch bridge,
firewall for the hub, automatic security updates and the Zigbee flashing tool.

Usage (as root, on Linux; aarch64 binaries run through qemu-user-static / binfmt_misc):
  sudo os/satellite/build-satellite-image.sh --wifi-ssid NAME --wifi-psk PASSWORD --hub ADDRESS [options]

Required:
  --wifi-ssid NAME        Wi-Fi network (WPA2 personal)
  --wifi-psk PASSWORD     Wi-Fi password, 8 to 63 characters
  --hub ADDRESS           IP address (recommended, fixed by a DHCP reservation) or host name of the hub

Options:
  --room ROOM             room of the satellite; the device is called "VoxHub ROOM" (default: "VoxHub Satellite")
  --name NAME             device name in Home Assistant (overrides --room for the name)
  --hostname NAME         host name (default voxhub-satellite)
  --wifi-country CC       Wi-Fi country (default AT)
  --hub-port PORT         port of Home Assistant on the hub (default 8123)
  --password PASSWORD     password of the user "voxhub" (default: a random one, printed at the end)
  --ssh-key FILE          public key for SSH logins of the user "voxhub"
  --wake-word ID          okay_nabu (default), hey_jarvis, alexa, hey_mycroft, hey_luna, hey_morgan,
                          hey_home_assistant, okay_computer, choo_choo_homie
  --mic-gain FACTOR       software microphone gain (default 4 = +12 dB)
  --timezone ZONE         time zone (default Europe/Vienna)
  --no-firewall           do not restrict port 6053 to the hub
  --base-image FILE       use this ${BASE_NAME}.img.xz instead of downloading it
  --out DIR               output directory (default os/output)
  --no-verify             skip the checks of the finished image
  --no-compress           keep the uncompressed .img
  --keep-work             keep the work directory
  --help                  this text

Environment: HTTPS_PROXY and SSL_CERT_FILE (or VOXHUB_CA_CERT) are used for the downloads inside
the image while it is built, for networks that only allow a TLS-intercepting proxy.
HELP
}

parse_arguments() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --wifi-ssid) WIFI_SSID="${2-}"; shift ;;
            --wifi-psk) WIFI_PSK="${2-}"; shift ;;
            --wifi-country) WIFI_COUNTRY="${2-}"; shift ;;
            --hub) HUB="${2-}"; shift ;;
            --hub-port) HUB_PORT="${2-}"; shift ;;
            --room) ROOM="${2-}"; shift ;;
            --name) NAME="${2-}"; shift ;;
            --hostname) HOST_NAME="${2-}"; shift ;;
            --password) PASSWORD="${2-}"; shift ;;
            --ssh-key) SSH_KEY_FILE="${2-}"; shift ;;
            --wake-word) WAKE_WORD="${2-}"; shift ;;
            --mic-gain) MIC_GAIN="${2-}"; shift ;;
            --timezone) TIMEZONE="${2-}"; shift ;;
            --no-firewall) FIREWALL=0 ;;
            --base-image) BASE_IMAGE="${2-}"; shift ;;
            --out) OUT="${2-}"; shift ;;
            --no-verify) VERIFY=0 ;;
            --no-compress) COMPRESS=0 ;;
            --keep-work) KEEP=1 ;;
            -h | --help) usage; exit 0 ;;
            *) fail "unknown argument: $1 (see --help)" ;;
        esac
        shift
    done
}

validate() {
    [ -n "$WIFI_SSID" ] || fail "--wifi-ssid is required (the board has no Ethernet)"
    [ "${#WIFI_SSID}" -le 32 ] || fail "--wifi-ssid is longer than 32 characters"
    [ "${#WIFI_PSK}" -ge 8 ] && [ "${#WIFI_PSK}" -le 63 ] || fail "--wifi-psk must have 8 to 63 characters (WPA2)"
    case "$WIFI_SSID$WIFI_PSK" in
        *$'\n'* | *$'\r'*) fail "the Wi-Fi name and password must not contain line breaks" ;;
    esac
    [[ "$WIFI_COUNTRY" =~ ^[A-Z]{2}$ ]] || fail "--wifi-country must be two capital letters, for example AT"
    [ -n "$HUB" ] || fail "--hub is required: the IP address or host name of the hub (Home Assistant)"
    [[ "$HUB" =~ ^[A-Za-z0-9.-]+$ ]] || fail "--hub must be an IPv4 address or a host name (Linux Voice Assistant uses IPv4)"
    [[ "$HUB_PORT" =~ ^[0-9]+$ ]] && [ "$HUB_PORT" -ge 1 ] && [ "$HUB_PORT" -le 65535 ] || fail "--hub-port must be a port number"
    [[ "$HOST_NAME" =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$ ]] || fail "--hostname: lower-case letters, digits and hyphens"
    case " $WAKE_WORDS " in
        *" $WAKE_WORD "*) ;;
        *) fail "--wake-word must be one of: $WAKE_WORDS" ;;
    esac
    [[ "$MIC_GAIN" =~ ^[0-9]+([.][0-9]+)?$ ]] || fail "--mic-gain must be a number, for example 4"
    awk -v g="$MIC_GAIN" 'BEGIN { exit !(g >= 0.1 && g <= 16) }' || fail "--mic-gain must be between 0.1 and 16"
    if [ -z "$NAME" ]; then
        if [ -n "$ROOM" ]; then
            NAME="VoxHub $ROOM"
        else
            NAME="VoxHub Satellite"
        fi
    fi
    case "$NAME$ROOM" in
        *"'"* | *'"'* | *'\'* | *'$'* | *'`'* | *$'\n'*) fail "--name and --room must not contain quotes, backslashes, \$, \` or line breaks" ;;
    esac
    [ -z "$SSH_KEY_FILE" ] || [ -s "$SSH_KEY_FILE" ] || fail "--ssh-key: $SSH_KEY_FILE is missing or empty"
    [ -z "$BASE_IMAGE" ] || [ -s "$BASE_IMAGE" ] || fail "--base-image: $BASE_IMAGE is missing"
    [ "$(id -u)" -eq 0 ] || fail "run as root (loop devices, mounts and chroot): sudo $0 ..."
}

need() {
    local tool
    for tool in "$@"; do
        command -v "$tool" >/dev/null 2>&1 || fail "missing tool: $tool"
    done
}

check_host() {
    need xz sfdisk losetup partx mount umount chroot git curl sha256sum e2fsck resize2fs openssl python3 truncate partprobe
    if [ "$VERIFY" -eq 1 ]; then
        need dtc fdtoverlay
    fi
    if [ "$(uname -m)" != "aarch64" ]; then
        if [ ! -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ] && [ -f /usr/lib/binfmt.d/qemu-aarch64.conf ]; then
            [ -e /proc/sys/fs/binfmt_misc/register ] || mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc 2>/dev/null || true
            if [ -w /proc/sys/fs/binfmt_misc/register ]; then
                log "registering the aarch64 emulation (binfmt_misc, /usr/lib/binfmt.d/qemu-aarch64.conf)"
                cat /usr/lib/binfmt.d/qemu-aarch64.conf >/proc/sys/fs/binfmt_misc/register || true
            fi
        fi
        if [ ! -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ]; then
            fail "aarch64 programs cannot run on this machine. Install the emulation, for example
  sudo apt install qemu-user-static binfmt-support
and run the script again."
        fi
        grep -q '^enabled' /proc/sys/fs/binfmt_misc/qemu-aarch64 || fail "binfmt_misc entry qemu-aarch64 is disabled"
        BINFMT_FLAGS="$(sed -n 's/^flags: //p' /proc/sys/fs/binfmt_misc/qemu-aarch64)"
    fi
}

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    local index
    for ((index = ${#MOUNTED[@]} - 1; index >= 0; index--)); do
        umount -l "${MOUNTED[$index]}" 2>/dev/null || true
    done
    if [ -n "$LOOP" ]; then
        partx -d "$LOOP" 2>/dev/null || true
        losetup -d "$LOOP" 2>/dev/null || true
    fi
    if [ -n "$WORK" ] && [ "$KEEP" -eq 0 ]; then
        rm -rf "$WORK"
    elif [ -n "$WORK" ]; then
        log "work directory kept: $WORK"
    fi
    exit "$status"
}

mount_at() {
    mount "$@"
    MOUNTED+=("${!#}")
}

flash_script_values() {
    sed -n '/^ROUTER_NAME=/,/^)$/p; /^BSL_SOURCES=/,/^)$/p' "$REPO/tools/flash_zigbee.sh"
}

fetch_base_image() {
    local cache="$OUT/.cache"
    mkdir -p "$cache"
    if [ -z "$BASE_IMAGE" ]; then
        BASE_IMAGE="$cache/${BASE_NAME}.img.xz"
        if [ ! -s "$BASE_IMAGE" ]; then
            log "downloading $BASE_URL"
            curl -fL --retry 4 --retry-delay 3 -o "$BASE_IMAGE.part" "$BASE_URL"
            mv "$BASE_IMAGE.part" "$BASE_IMAGE"
        fi
    fi
    log "checking ${BASE_IMAGE##*/}"
    [ "$(sha256sum "$BASE_IMAGE" | cut -d ' ' -f 1)" = "$BASE_SHA256" ] ||
        fail "$BASE_IMAGE does not have the SHA256 $BASE_SHA256 of $BASE_NAME"
}

prepare_image() {
    IMG="$WORK/voxhub-satellite.img"
    log "unpacking"
    xz -dc -T0 "$BASE_IMAGE" >"$IMG"
    log "adding $GROW_MIB MiB to the root partition"
    truncate -s "+${GROW_MIB}M" "$IMG"
    echo ", +" | sfdisk --no-reread --no-tell-kernel -q -N 2 "$IMG"
    LOOP="$(losetup -f --show -P "$IMG")"
    partprobe "$LOOP" 2>/dev/null || true
    [ -b "${LOOP}p2" ] || partx -a "$LOOP" 2>/dev/null || true
    [ -b "${LOOP}p2" ] || fail "the partitions of $IMG did not appear as ${LOOP}p1 / ${LOOP}p2"
    e2fsck -p -f "${LOOP}p2" >/dev/null || [ "$?" -le 1 ] || fail "e2fsck found errors in the root file system"
    resize2fs -p "${LOOP}p2" >/dev/null
    ROOT="$WORK/root"
    mkdir -p "$ROOT"
    mount_at "${LOOP}p2" "$ROOT"
    if mount -t vfat "${LOOP}p1" "$ROOT/boot/firmware" 2>/dev/null; then
        MOUNTED+=("$ROOT/boot/firmware")
        BOOT_MODE="mount"
    else
        need mcopy mmd mdel
        BOOT_MODE="mtools"
        log "this kernel cannot mount FAT: the boot partition is copied out with mtools and written back"
        MTOOLS_SKIP_CHECK=1 mcopy -s -p -n -i "${LOOP}p1" '::*' "$ROOT/boot/firmware/"
        boot_checksums >"$WORK/boot-before.sha256"
    fi
    [ -f "$ROOT/boot/firmware/config.txt" ] || fail "no config.txt on the boot partition"
}

boot_checksums() {
    (cd "$ROOT/boot/firmware" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum)
}

write_back_boot() {
    [ "$BOOT_MODE" = "mtools" ] || return 0
    boot_checksums >"$WORK/boot-after.sha256"
    local path count=0
    while IFS= read -r path; do
        path="${path#./}"
        MTOOLS_SKIP_CHECK=1 mmd -D s -i "${LOOP}p1" "::$(dirname "/$path")" 2>/dev/null || true
        MTOOLS_SKIP_CHECK=1 mcopy -o -p -i "${LOOP}p1" "$ROOT/boot/firmware/$path" "::/$path"
        count=$((count + 1))
    done < <(LC_ALL=C comm -13 <(LC_ALL=C sort "$WORK/boot-before.sha256") <(LC_ALL=C sort "$WORK/boot-after.sha256") | sed 's/^[0-9a-f]*  //')
    while IFS= read -r path; do
        path="${path#./}"
        [ -e "$ROOT/boot/firmware/$path" ] && continue
        MTOOLS_SKIP_CHECK=1 mdel -i "${LOOP}p1" "::/$path"
        count=$((count + 1))
    done < <(LC_ALL=C comm -23 <(LC_ALL=C sort "$WORK/boot-before.sha256") <(LC_ALL=C sort "$WORK/boot-after.sha256") | sed 's/^[0-9a-f]*  //')
    log "boot partition: $count file(s) written back"
    find "$ROOT/boot/firmware" -mindepth 1 -delete
}

enter_chroot() {
    mount_at --bind /dev "$ROOT/dev"
    mount_at --bind /dev/pts "$ROOT/dev/pts"
    mount_at -t proc proc "$ROOT/proc"
    mount_at -t sysfs sysfs "$ROOT/sys"
    mount_at -t tmpfs tmpfs "$ROOT/run"
    mount_at -t tmpfs tmpfs "$ROOT/tmp"
    if [ "$(uname -m)" != "aarch64" ] && [[ "${BINFMT_FLAGS:-}" != *F* ]]; then
        cp "$(command -v qemu-aarch64-static)" "$ROOT/usr/bin/qemu-aarch64-static"
    fi
    cp --remove-destination /etc/resolv.conf "$ROOT/etc/resolv.conf.voxhub-build"
    if [ -L "$ROOT/etc/resolv.conf" ] || [ -e "$ROOT/etc/resolv.conf" ]; then
        mv "$ROOT/etc/resolv.conf" "$ROOT/etc/resolv.conf.voxhub-orig"
    fi
    mv "$ROOT/etc/resolv.conf.voxhub-build" "$ROOT/etc/resolv.conf"
    printf '#!/bin/sh\nexit 101\n' >"$ROOT/usr/sbin/policy-rc.d"
    chmod 755 "$ROOT/usr/sbin/policy-rc.d"
    local ca="${VOXHUB_CA_CERT:-${SSL_CERT_FILE:-}}"
    if [ -n "${HTTPS_PROXY:-${https_proxy:-}}" ]; then
        printf 'Acquire::https::Proxy "%s";\n' "${HTTPS_PROXY:-${https_proxy:-}}" >"$ROOT/etc/apt/apt.conf.d/99voxhub-build"
    fi
    if [ -n "$ca" ] && [ -s "$ca" ]; then
        cp "$ca" "$ROOT/tmp/voxhub-build-ca.crt"
        printf 'Acquire::https::CAInfo "/tmp/voxhub-build-ca.crt";\n' >>"$ROOT/etc/apt/apt.conf.d/99voxhub-build"
    fi
}

in_root() {
    local ca_env=()
    if [ -f "$ROOT/tmp/voxhub-build-ca.crt" ]; then
        ca_env=(SSL_CERT_FILE=/tmp/voxhub-build-ca.crt PIP_CERT=/tmp/voxhub-build-ca.crt)
    fi
    chroot "$ROOT" /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root \
        LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive PIP_CONFIG_FILE=/dev/null HTTPS_PROXY="${HTTPS_PROXY:-${https_proxy:-}}" \
        https_proxy="${HTTPS_PROXY:-${https_proxy:-}}" "${ca_env[@]}" "$@"
}

leave_chroot() {
    rm -f "$ROOT/usr/sbin/policy-rc.d" "$ROOT/etc/apt/apt.conf.d/99voxhub-build" "$ROOT/usr/bin/qemu-aarch64-static"
    rm -f "$ROOT/etc/resolv.conf"
    if [ -L "$ROOT/etc/resolv.conf.voxhub-orig" ] || [ -e "$ROOT/etc/resolv.conf.voxhub-orig" ]; then
        mv "$ROOT/etc/resolv.conf.voxhub-orig" "$ROOT/etc/resolv.conf"
    fi
    local mountpoint
    for mountpoint in tmp run sys proc dev/pts dev; do
        umount "$ROOT/$mountpoint"
    done
    MOUNTED=("$ROOT")
    if [ "$BOOT_MODE" = "mount" ]; then
        MOUNTED+=("$ROOT/boot/firmware")
    fi
}

install_packages() {
    log "switching the package sources to https"
    sed -i 's|http://deb.debian.org/|https://deb.debian.org/|g; s|http://archive.raspberrypi.com/|https://archive.raspberrypi.com/|g' \
        "$ROOT"/etc/apt/sources.list.d/*.sources
    if [ -f "$ROOT/etc/apt/sources.list" ]; then
        sed -i 's|http://deb.debian.org/|https://deb.debian.org/|g; s|http://archive.raspberrypi.com/|https://archive.raspberrypi.com/|g' \
            "$ROOT/etc/apt/sources.list"
    fi
    log "installing packages (emulated, takes a while): ${PACKAGES[*]}"
    in_root apt-get update
    in_root apt-get install -y --no-install-recommends "${PACKAGES[@]}"
    in_root apt-get clean
}

install_lva() {
    local lva="$ROOT/opt/linux-voice-assistant"
    log "Linux Voice Assistant $LVA_TAG"
    rm -rf "$lva"
    git clone -q --depth 1 --branch "$LVA_TAG" "$LVA_REPO" "$lva"
    [ "$(git -C "$lva" rev-parse HEAD)" = "$LVA_COMMIT" ] || fail "$LVA_TAG is not commit $LVA_COMMIT"
    printf '%s\n' "$LVA_VERSION" >"$lva/version.txt"
    printf '%s\n' "$LVA_COMMIT" >"$lva/version_githash.txt"
    local constraints=()
    if [ -s "$HERE/lva-constraints.txt" ]; then
        cp "$HERE/lva-constraints.txt" "$ROOT/tmp/lva-constraints.txt"
        constraints=(-c /tmp/lva-constraints.txt)
    fi
    in_root python3 -m venv /opt/linux-voice-assistant/.venv
    in_root env SETUPTOOLS_SCM_PRETEND_VERSION="$LVA_VERSION" /opt/linux-voice-assistant/.venv/bin/pip install \
        --no-cache-dir --disable-pip-version-check --prefer-binary "${constraints[@]}" \
        -e /opt/linux-voice-assistant
    in_root /opt/linux-voice-assistant/.venv/bin/pip freeze --disable-pip-version-check --exclude-editable \
        >"$ROOT/opt/linux-voice-assistant/voxhub-freeze.txt" 2>"$WORK/pip-freeze.err"
    cp "$ROOT/opt/linux-voice-assistant/voxhub-freeze.txt" "$WORK/lva-freeze.txt"
}

install_voxhub() {
    log "VoxHub bridge, launcher, hub watch, flashing tool"
    mkdir -p "$ROOT/opt/voxhub" "$ROOT/etc/voxhub" "$ROOT/usr/local/share/voxhub/radio"
    rm -rf "$ROOT/opt/voxhub/voxhub_satellite"
    cp -r "$REPO/assistant/voxhub_satellite/app/voxhub_satellite" "$ROOT/opt/voxhub/voxhub_satellite"
    find "$ROOT/opt/voxhub" -name __pycache__ -prune -exec rm -rf {} +
    cp -r "$HERE/rootfs/." "$ROOT/"
    install -m 755 "$REPO/tools/flash_zigbee.sh" "$ROOT/usr/local/sbin/voxhub-flash-zigbee"
    local ROUTER_NAME="" ROUTER_SOURCES=() BSL_SOURCES=()
    eval "$(flash_script_values)"
    local url sha
    for pair in "${ROUTER_SOURCES[0]} ${ROUTER_SOURCES[1]}" "${BSL_SOURCES[0]} ${BSL_SOURCES[1]}"; do
        url="${pair% *}"
        sha="${pair##* }"
        curl -fsSL --retry 3 -o "$WORK/download" "$url"
        [ "$(sha256sum "$WORK/download" | cut -d ' ' -f 1)" = "$sha" ] || fail "checksum of $url does not match"
        install -m 644 "$WORK/download" "$ROOT/usr/local/share/voxhub/radio/$sha"
    done
    log "  radio files for offline flashing: $ROUTER_NAME, cc2538-bsl"
}

write_settings() {
    log "settings: name '$NAME', hub $HUB:$HUB_PORT, wake word $WAKE_WORD, Wi-Fi '$WIFI_SSID' ($WIFI_COUNTRY)"
    cat >"$ROOT/etc/voxhub/satellite.env" <<EOF
VOXHUB_NAME='$NAME'
VOXHUB_ROOM='$ROOM'
VOXHUB_HUB='$HUB'
VOXHUB_HUB_PORT=$HUB_PORT
VOXHUB_WAKE_WORD=$WAKE_WORD
VOXHUB_MIC_GAIN=$MIC_GAIN
VOXHUB_FIREWALL=$FIREWALL
VOXHUB_PREFERENCES_FILE=/var/lib/voxhub/preferences.json
VOXHUB_DOWNLOAD_DIR=/var/lib/voxhub/downloads
EOF
    chmod 644 "$ROOT/etc/voxhub/satellite.env"
    local connection="$ROOT/etc/NetworkManager/system-connections/voxhub-wifi.nmconnection"
    python3 - "$connection" "$WIFI_SSID" "$WIFI_PSK" "$(python3 -c 'import uuid; print(uuid.uuid4())')" <<'PYTHON'
import sys

path, ssid, psk, uuid = sys.argv[1:5]
lines = [
    "[connection]", "id=voxhub-wifi", f"uuid={uuid}", "type=wifi", "autoconnect=true", "",
    "[wifi]", "mode=infrastructure", f"ssid={ssid}", "",
    "[wifi-security]", "auth-alg=open", "key-mgmt=wpa-psk", f"psk={psk}", "",
    "[ipv4]", "method=auto", "", "[ipv6]", "addr-gen-mode=default", "method=auto", "",
]
with open(path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
PYTHON
    chmod 600 "$connection"
    sed -i 's/^WirelessEnabled=.*/WirelessEnabled=true/' "$ROOT/var/lib/NetworkManager/NetworkManager.state"
    local cmdline="$ROOT/boot/firmware/cmdline.txt"
    sed -i -e 's/\s*cfg80211.ieee80211_regdom=\S*//' -e "s/\$/ cfg80211.ieee80211_regdom=$WIFI_COUNTRY/" "$cmdline"
    printf '%s\n' "$HOST_NAME" >"$ROOT/etc/hostname"
    sed -i "s/^127\.0\.1\.1\s.*/127.0.1.1\t$HOST_NAME/" "$ROOT/etc/hosts"
    [ -e "$ROOT/usr/share/zoneinfo/$TIMEZONE" ] || fail "unknown time zone $TIMEZONE"
    ln -sf "/usr/share/zoneinfo/$TIMEZONE" "$ROOT/etc/localtime"
    printf '%s\n' "$TIMEZONE" >"$ROOT/etc/timezone"
    if ! grep -q "^# ---- VoxHub CM4 carrier" "$ROOT/boot/firmware/config.txt"; then
        printf '\n' >>"$ROOT/boot/firmware/config.txt"
        cat "$REPO/os/config/config-voxhub.txt" >>"$ROOT/boot/firmware/config.txt"
    fi
}

configure_system() {
    log "user voxhub, SSH, services"
    if [ -z "$PASSWORD" ]; then
        PASSWORD="$(python3 -c 'import secrets, string; a = string.ascii_letters + string.digits; print("".join(secrets.choice(a) for _ in range(14)))')"
        GENERATED_PASSWORD=1
    fi
    local hash first
    hash="$(printf '%s' "$PASSWORD" | openssl passwd -6 -stdin)"
    first="$(awk -F: '$3 == 1000 { print $1 }' "$ROOT/etc/passwd")"
    [ -n "$first" ] || fail "the base image has no user with uid 1000"
    in_root /usr/lib/userconf-pi/userconf "$first" voxhub "$hash"
    grep -q '^voxhub:x:1000:1000:' "$ROOT/etc/passwd" || fail "renaming $first to voxhub failed"
    in_root usermod -aG audio,video,gpio,input,dialout,sudo,adm voxhub
    if [ -n "$SSH_KEY_FILE" ]; then
        install -d -m 700 -o 1000 -g 1000 "$ROOT/home/voxhub/.ssh"
        install -m 600 -o 1000 -g 1000 "$SSH_KEY_FILE" "$ROOT/home/voxhub/.ssh/authorized_keys"
    fi
    mkdir -p "$ROOT/var/lib/systemd/linger"
    touch "$ROOT/var/lib/systemd/linger/voxhub"
    mkdir -p "$ROOT/etc/cloud"
    touch "$ROOT/etc/cloud/cloud-init.disabled"
    rm -f "$ROOT"/etc/ssh/ssh_host_*_key*
    in_root systemctl enable ssh regenerate_ssh_host_keys voxhub-lva voxhub-peripherals voxhub-hubwatch
    in_root systemctl --global enable pipewire.socket pipewire-pulse.socket wireplumber.service
    in_root systemctl disable userconfig 2>/dev/null || true
    in_root systemctl disable cloud-init-local cloud-init-main cloud-init-network cloud-config cloud-final 2>/dev/null || true
}

verify_image() {
    log "verifying the image"
    local problems=0 boot="$ROOT/boot/firmware" overlay
    check() {
        if eval "$2"; then
            printf '  ok    %s\n' "$1"
        else
            printf '  FAIL  %s\n' "$1"
            problems=$((problems + 1))
        fi
    }
    check "config.txt carries the VoxHub block of the hub" 'grep -q "^dtoverlay=googlevoicehat-soundcard" "$boot/config.txt" && grep -q "^dtoverlay=uart4" "$boot/config.txt"'
    for overlay in $(grep -oE '^dtoverlay=[a-z0-9-]+' "$REPO/os/config/config-voxhub.txt" | cut -d= -f2 | sort -u); do
        check "stock overlay $overlay.dtbo present" '[ -f "$boot/overlays/$overlay.dtbo" ]'
    done
    dtc -@ -q -I dts -O dtb -W no-unit_address_vs_reg -o "$WORK/voxhub.dtbo" "$REPO/os/overlay/voxhub-overlay.dts"
    check "VoxHub overlay applies to bcm2711-rpi-cm4.dtb of this image" 'fdtoverlay -i "$boot/bcm2711-rpi-cm4.dtb" -o "$WORK/merged.dtb" "$WORK/voxhub.dtbo"'
    check "Wi-Fi country $WIFI_COUNTRY on the kernel command line" 'grep -q "cfg80211.ieee80211_regdom=$WIFI_COUNTRY" "$boot/cmdline.txt"'
    check "Wi-Fi connection file, mode 600" '[ "$(stat -c %a "$ROOT/etc/NetworkManager/system-connections/voxhub-wifi.nmconnection")" = 600 ]'
    check "Wi-Fi radio enabled for NetworkManager" 'grep -q "^WirelessEnabled=true" "$ROOT/var/lib/NetworkManager/NetworkManager.state"'
    check "user voxhub (uid 1000) with a password" 'grep -q "^voxhub:x:1000:1000:" "$ROOT/etc/passwd" && grep -q "^voxhub:[$]6[$]" "$ROOT/etc/shadow"'
    check "user voxhub lingers (PipeWire without login)" '[ -f "$ROOT/var/lib/systemd/linger/voxhub" ]'
    check "first-boot user dialog off" '! [ -L "$ROOT/etc/systemd/system/multi-user.target.wants/userconfig.service" ]'
    check "cloud-init off" '[ -f "$ROOT/etc/cloud/cloud-init.disabled" ]'
    check "no SSH host keys in the image (generated on first boot)" '! ls "$ROOT"/etc/ssh/ssh_host_*_key >/dev/null 2>&1'
    for unit in ssh voxhub-lva voxhub-peripherals voxhub-hubwatch; do
        check "service $unit enabled" '[ -L "$ROOT/etc/systemd/system/multi-user.target.wants/$unit.service" ]'
    done
    check "PipeWire user units enabled" '[ -L "$ROOT/etc/systemd/user/sockets.target.wants/pipewire-pulse.socket" ] && [ -L "$ROOT/etc/systemd/user/pipewire.service.wants/wireplumber.service" ]'
    check "unattended-upgrades enabled, VoxHub origins" '[ -L "$ROOT/etc/systemd/system/multi-user.target.wants/unattended-upgrades.service" ] && grep -q "Raspberry Pi Foundation" "$ROOT/etc/apt/apt.conf.d/52voxhub-unattended-upgrades"'
    check "Linux Voice Assistant $LVA_VERSION at $LVA_COMMIT" '[ "$(cat "$ROOT/opt/linux-voice-assistant/version.txt")" = "$LVA_VERSION" ] && [ "$(git -C "$ROOT/opt/linux-voice-assistant" rev-parse HEAD)" = "$LVA_COMMIT" ]'
    mkdir -p "$ROOT/tmp/voxhub-stub/soundcard"
    printf 'def __getattr__(name):\n    return type(name, (), {})\n' >"$ROOT/tmp/voxhub-stub/soundcard/__init__.py"
    check "Linux Voice Assistant loads its libraries and parses its options (emulated, sound server stubbed)" 'in_root env PYTHONPATH=/tmp/voxhub-stub sh -c "cd /opt/linux-voice-assistant && .venv/bin/python3 -m linux_voice_assistant --help" >"$WORK/lva-help.txt" 2>&1 && grep -q -- "--peripheral-port" "$WORK/lva-help.txt"'
    check "libmpv, numpy, microWakeWord, ESPHome API library load (emulated)" 'in_root sh -c "cd /opt/linux-voice-assistant && .venv/bin/python3 -c \"import mpv, numpy, pymicro_wakeword, aioesphomeapi, zeroconf, webrtc_noise_gain\"" >"$WORK/lva-imports.txt" 2>&1'
    check "VoxHub modules import with the LVA interpreter (emulated)" 'in_root env PYTHONPATH=/opt/voxhub /opt/linux-voice-assistant/.venv/bin/python3 -c "import voxhub_satellite.launch, voxhub_satellite.peripherals, voxhub_satellite.hubwatch, websockets"'
    check "launcher reads the settings (emulated)" 'in_root env PYTHONPATH=/opt/voxhub /opt/linux-voice-assistant/.venv/bin/python3 -c "from pathlib import Path; from voxhub_satellite.launch import read_env_file, settings_from_env; s = settings_from_env(read_env_file(Path(\"/etc/voxhub/satellite.env\"))); assert s.name == \"$NAME\" and s.wake_word == \"$WAKE_WORD\""'
    check "wake word model $WAKE_WORD present" '[ -f "$ROOT/opt/linux-voice-assistant/wakewords/$WAKE_WORD.tflite" ]'
    check "automatic updates: Debian, Debian-Security and Raspberry Pi archive allowed, daily timers on" 'in_root apt-config dump >"$WORK/uu.txt" 2>&1 && grep -q "Origins-Pattern:: \"origin=Raspberry Pi Foundation,codename=\${distro_codename},label=Raspberry Pi Foundation\"" "$WORK/uu.txt" && grep -q "label=Debian-Security" "$WORK/uu.txt" && grep -q "Automatic-Reboot \"true\"" "$WORK/uu.txt" && [ -L "$ROOT/etc/systemd/system/timers.target.wants/apt-daily-upgrade.timer" ]'
    check "router firmware and cc2538-bsl for offline flashing" '[ "$(ls "$ROOT/usr/local/share/voxhub/radio" | wc -l)" -eq 2 ]'
    check "flashing tool: role satellite detected, local firmware used (dry run, emulated)" 'in_root bash /usr/local/sbin/voxhub-flash-zigbee --dry-run >"$WORK/flash.txt" 2>&1 && grep -q "^Role: satellite (this system is a VoxHub satellite" "$WORK/flash.txt" && grep -q "from the local copy" "$WORK/flash.txt" && grep -q "Dry run finished" "$WORK/flash.txt"'
    check "machine-id empty: first boot generates the SSH host keys" '[ ! -s "$ROOT/etc/machine-id" ] || grep -qx uninitialized "$ROOT/etc/machine-id"'
    check "systemd accepts the VoxHub units (emulated)" 'in_root systemd-analyze verify /etc/systemd/system/voxhub-lva.service /etc/systemd/system/voxhub-peripherals.service /etc/systemd/system/voxhub-hubwatch.service >"$WORK/units.txt" 2>&1 || ! grep -v -E "Failed to (connect|create)|bus|Cannot (find|open)" "$WORK/units.txt" | grep -q .'
    mkdir -p "$OUT/satellite-checks"
    cp "$WORK/lva-help.txt" "$WORK/uu.txt" "$WORK/units.txt" "$WORK/flash.txt" "$OUT/satellite-checks/" 2>/dev/null || true
    [ "$problems" -eq 0 ] || fail "$problems check(s) of the image failed"
    log "all checks passed"
}

finish_image() {
    in_root apt-get clean
    rm -rf "$ROOT/var/lib/apt/lists/"* "$ROOT/root/.cache" "$ROOT/tmp/"*
    find "$ROOT/var/log" -type f -name '*.log' -exec truncate -s 0 {} +
}

unmount_image() {
    sync
    if [ "$BOOT_MODE" = "mount" ]; then
        umount "$ROOT/boot/firmware"
    else
        write_back_boot
    fi
    umount "$ROOT"
    MOUNTED=()
    e2fsck -p -f "${LOOP}p2" >/dev/null || [ "$?" -le 1 ] || fail "e2fsck found errors after the build"
    partx -d "$LOOP" 2>/dev/null || true
    losetup -d "$LOOP"
    LOOP=""
}

publish() {
    local stem="voxhub-satellite-${BASE_NAME%%-raspios*}-lva${LVA_VERSION}"
    mkdir -p "$OUT"
    cp "$WORK/lva-freeze.txt" "$OUT/$stem.packages.txt"
    if [ "$COMPRESS" -eq 1 ]; then
        log "compressing (xz)"
        xz -T0 -6 -c "$IMG" >"$OUT/$stem.img.xz"
        (cd "$OUT" && sha256sum "$stem.img.xz" >"$stem.img.xz.sha256")
        FINAL="$OUT/$stem.img.xz"
    else
        mv "$IMG" "$OUT/$stem.img"
        (cd "$OUT" && sha256sum "$stem.img" >"$stem.img.sha256")
        FINAL="$OUT/$stem.img"
    fi
}

main() {
    parse_arguments "$@"
    validate
    check_host
    mkdir -p "$OUT"
    OUT="$(cd "$OUT" && pwd)"
    WORK="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-satellite.XXXXXX")"
    trap cleanup EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    fetch_base_image
    prepare_image
    enter_chroot
    install_packages
    install_lva
    install_voxhub
    write_settings
    configure_system
    if [ "$VERIFY" -eq 1 ]; then
        verify_image
    fi
    finish_image
    leave_chroot
    unmount_image
    publish
    log "done: $FINAL"
    log "write it to the microSD card with Raspberry Pi Imager (\"Use custom\") or:"
    log "  xz -dc $FINAL | sudo dd of=/dev/sdX bs=4M conv=fsync"
    if [ "$GENERATED_PASSWORD" -eq 1 ]; then
        log "user voxhub, password (write it down, it is not stored anywhere else): $PASSWORD"
    fi
    log "first boot: about 2 minutes; then Home Assistant shows the discovered ESPHome device \"$NAME\""
}

main "$@"
