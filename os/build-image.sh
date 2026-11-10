#!/usr/bin/env bash
# Build a flashable Home Assistant OS SD-card image for the VoxHub CM4 carrier.
#
#   os/build-image.sh [repack|full] [options]
#
#   repack (default)  Download the latest official HAOS rpi4-64 release image and add the
#                     VoxHub configuration to its boot partition. Fast (~2 min), no root, no
#                     Docker. The result keeps receiving official OTA updates.
#   full              Clone the official HAOS build system at the latest release tag, add the
#                     "voxhub" board definition from os/board + os/package and build from source
#                     (needs Docker or a Buildroot-capable host, ~30 GB disk, 1-3 h).
#
# Options:
#   --version X.Y       HAOS version (default: latest stable release tag)
#   --out DIR           output directory (default: os/output)
#   --wifi-ssid NAME --wifi-psk PASS [--wifi-country CC]
#                       pre-seed a NetworkManager Wi-Fi profile (the board has no Ethernet/HDMI)
#   --custom-overlay    (repack) also use os/overlay/voxhub-overlay.dts instead of stock overlays.
#                       NOTE: HAOS deletes /overlays/* on OS updates -> not OTA-safe.
#   --keep-work         keep the work directory
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="repack"; VERSION=""; OUT="${HERE}/output"; WIFI_SSID=""; WIFI_PSK=""; WIFI_COUNTRY="US"
CUSTOM_OVERLAY=0; KEEP=0
HAOS_REPO="https://github.com/home-assistant/operating-system"
MARK_BEGIN="# ---- VoxHub CM4 carrier"

while [ $# -gt 0 ]; do
    case "$1" in
        repack|full) MODE="$1" ;;
        --version) VERSION="$2"; shift ;;
        --out) OUT="$2"; shift ;;
        --wifi-ssid) WIFI_SSID="$2"; shift ;;
        --wifi-psk) WIFI_PSK="$2"; shift ;;
        --wifi-country) WIFI_COUNTRY="$2"; shift ;;
        --custom-overlay) CUSTOM_OVERLAY=1 ;;
        --keep-work) KEEP=1 ;;
        -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

need() { for t in "$@"; do command -v "$t" >/dev/null || { echo "missing tool: $t" >&2; exit 1; }; done; }
log() { printf '\033[1m[voxhub-os]\033[0m %s\n' "$*"; }

latest_version() {
    # newest tag of the form MAJOR.MINOR (release candidates / dev tags are skipped)
    git ls-remote --tags --refs "${HAOS_REPO}.git" | sed 's|.*refs/tags/||' \
        | grep -E '^[0-9]+\.[0-9]+$' | sort -V | tail -n1
}

need git
[ -n "${VERSION}" ] || VERSION="$(latest_version)"
[ -n "${VERSION}" ] || { echo "could not determine the latest HAOS version" >&2; exit 1; }
log "Home Assistant OS version: ${VERSION} (mode: ${MODE})"
mkdir -p "${OUT}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-os.XXXXXX")"
cleanup() { [ "${KEEP}" = 1 ] || rm -rf "${WORK}"; }
trap cleanup EXIT

wifi_profile() {
    cat <<EOF
[connection]
id=voxhub-wifi
uuid=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen)
type=wifi

[wifi]
mode=infrastructure
ssid=${WIFI_SSID}

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk=${WIFI_PSK}

[ipv4]
method=auto

[ipv6]
addr-gen-mode=stable-privacy
method=auto
EOF
}

# ------------------------------------------------------------------------------ repack
repack() {
    need curl xz sfdisk mcopy mtype mmd dtc
    local name="haos_rpi4-64-${VERSION}.img"
    local url="${HAOS_REPO}/releases/download/${VERSION}/${name}.xz"
    local cache="${OUT}/.cache"; mkdir -p "${cache}"
    if [ ! -s "${cache}/${name}.xz" ]; then
        log "downloading ${url}"
        curl -fL --retry 4 --retry-delay 2 -o "${cache}/${name}.xz.part" "${url}"
        mv "${cache}/${name}.xz.part" "${cache}/${name}.xz"
    fi
    log "unpacking"
    xz -t "${cache}/${name}.xz"
    xz -dc -T0 "${cache}/${name}.xz" > "${WORK}/${name}"
    local img="${WORK}/${name}"

    # locate the FAT boot partition (GPT name "hassos-boot") - no loop device / root needed
    local start
    start="$(sfdisk -d "${img}" | awk -F'[=,]' '/name="hassos-boot"/ {gsub(/ /,"",$2); print $2}')"
    [ -n "${start}" ] || { echo "hassos-boot partition not found" >&2; exit 1; }
    local boot="${img}@@$((start * 512))"

    log "patching config.txt on the boot partition (offset sector ${start})"
    mtype -i "${boot}" ::config.txt > "${WORK}/config.txt"
    if grep -q "^${MARK_BEGIN}" "${WORK}/config.txt"; then
        log "config.txt already contains the VoxHub block - leaving it alone"
    else
        printf '\n' >> "${WORK}/config.txt"
        if [ "${CUSTOM_OVERLAY}" = 1 ]; then
            {
                echo "${MARK_BEGIN} (custom overlay variant, added by os/build-image.sh) ----"
                printf '[cm4]\notg_mode=1\n[all]\ndtoverlay=voxhub\ndtparam=i2c_arm=on\n# ---- end VoxHub ----\n'
            } >> "${WORK}/config.txt"
        else
            cat "${HERE}/config/config-voxhub.txt" >> "${WORK}/config.txt"
        fi
        mcopy -o -i "${boot}" "${WORK}/config.txt" ::config.txt
    fi

    # sanity: every stock overlay we reference must exist in this release
    for o in $(grep -oE '^dtoverlay=[a-z0-9-]+' "${WORK}/config.txt" | cut -d= -f2 | sort -u); do
        [ "${o}" = voxhub ] && continue
        mdir -i "${boot}" "::overlays/${o}.dtbo" >/dev/null 2>&1 \
            || { echo "overlay ${o}.dtbo missing in HAOS ${VERSION}" >&2; exit 1; }
    done

    # compile our overlay and verify it applies cleanly to the CM4 device tree of this release
    dtc -@ -I dts -O dtb -W no-unit_address_vs_reg -o "${WORK}/voxhub.dtbo" "${HERE}/overlay/voxhub-overlay.dts"
    if command -v fdtoverlay >/dev/null; then
        mcopy -n -i "${boot}" ::bcm2711-rpi-cm4.dtb "${WORK}/cm4.dtb"
        fdtoverlay -i "${WORK}/cm4.dtb" -o "${WORK}/merged.dtb" "${WORK}/voxhub.dtbo"
        log "voxhub.dtbo applies cleanly to bcm2711-rpi-cm4.dtb"
    fi
    if [ "${CUSTOM_OVERLAY}" = 1 ]; then
        mcopy -o -i "${boot}" "${WORK}/voxhub.dtbo" ::overlays/voxhub.dtbo
    fi

    if [ -n "${WIFI_SSID}" ]; then
        log "adding Wi-Fi profile for SSID '${WIFI_SSID}' (CONFIG/network on the boot partition)"
        wifi_profile > "${WORK}/voxhub-wifi"
        mmd -D s -i "${boot}" ::CONFIG 2>/dev/null || true
        mmd -D s -i "${boot}" ::CONFIG/network 2>/dev/null || true
        mcopy -o -i "${boot}" "${WORK}/voxhub-wifi" ::CONFIG/network/voxhub-wifi
        if ! grep -q "cfg80211.ieee80211_regdom" <(mtype -i "${boot}" ::cmdline.txt); then
            mtype -i "${boot}" ::cmdline.txt | tr -d '\n' > "${WORK}/cmdline.txt"
            printf ' cfg80211.ieee80211_regdom=%s\n' "${WIFI_COUNTRY}" >> "${WORK}/cmdline.txt"
            mcopy -o -i "${boot}" "${WORK}/cmdline.txt" ::cmdline.txt
        fi
    fi

    local final="${OUT}/haos_voxhub-cm4-${VERSION}.img.xz"
    log "compressing -> ${final}"
    xz -c -T0 -6 "${img}" > "${final}"
    (cd "${OUT}" && sha256sum "$(basename "${final}")" > "$(basename "${final}").sha256")
    log "done: $(du -h "${final}" | cut -f1)  ${final}"
    log "flash with: xz -dc ${final} | sudo dd of=/dev/sdX bs=4M conv=fsync   (or Raspberry Pi Imager / balenaEtcher)"
}

# -------------------------------------------------------------------------------- full
full() {
    need git make
    local src="${OUT}/haos-src"
    if [ ! -d "${src}/.git" ]; then
        log "cloning ${HAOS_REPO} @ ${VERSION}"
        git clone --depth 1 -b "${VERSION}" --recurse-submodules --shallow-submodules "${HAOS_REPO}.git" "${src}"
    fi
    local ext="${src}/buildroot-external"

    log "installing the voxhub board definition into the HAOS tree"
    # board directory: start from the official rpi4-64 board, override meta / config
    rm -rf "${ext}/board/raspberrypi/voxhub"
    cp -r "${ext}/board/raspberrypi/rpi4-64" "${ext}/board/raspberrypi/voxhub"
    cp "${HERE}/board/voxhub/meta" "${ext}/board/raspberrypi/voxhub/meta"
    cp "${HERE}/board/voxhub/kernel.config" "${ext}/board/raspberrypi/voxhub/kernel.config"
    {
        cat "${ext}/board/raspberrypi/config.txt"
        printf '\n%s (full build, bundled overlay) ----\n' "${MARK_BEGIN}"
        printf '[cm4]\notg_mode=1\n[all]\ndtoverlay=voxhub\ndtparam=i2c_arm=on\n#enable_uart=1\n# ---- end VoxHub ----\n'
    } > "${ext}/board/raspberrypi/voxhub/config.txt"
    # overlay package
    rm -rf "${ext}/package/voxhub-overlay"
    cp -r "${HERE}/package/voxhub-overlay" "${ext}/package/voxhub-overlay"
    mkdir -p "${ext}/package/voxhub-overlay/src"
    cp "${HERE}/overlay/voxhub-overlay.dts" "${ext}/package/voxhub-overlay/src/"
    grep -q voxhub-overlay "${ext}/Config.in" \
        || echo 'source "$BR2_EXTERNAL_HAOS_PATH/package/voxhub-overlay/Config.in"' >> "${ext}/Config.in"
    # defconfig: derived from the official rpi4_64 one at build time, so it tracks upstream
    sed -e 's|board/raspberrypi/rpi4-64 |board/raspberrypi/voxhub |' \
        -e 's|\(BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES=".*\)"|\1 $(BR2_EXTERNAL_HAOS_PATH)/board/raspberrypi/voxhub/kernel.config"|' \
        -e 's|BR2_LINUX_KERNEL_INTREE_DTS_NAME=.*|BR2_LINUX_KERNEL_INTREE_DTS_NAME="broadcom/bcm2711-rpi-cm4"|' \
        "${ext}/configs/rpi4_64_defconfig" > "${ext}/configs/voxhub_defconfig"
    echo 'BR2_PACKAGE_VOXHUB_OVERLAY=y' >> "${ext}/configs/voxhub_defconfig"
    cp "${ext}/configs/voxhub_defconfig" "${HERE}/board/voxhub_defconfig"   # keep a copy for review

    log "building (this takes a long time)"
    if command -v docker >/dev/null && docker info >/dev/null 2>&1 && [ -z "${VOXHUB_NO_DOCKER:-}" ]; then
        (cd "${src}" && ./scripts/enter.sh make voxhub)
    else
        log "Docker not available - building directly on the host"
        (cd "${src}" && make voxhub)
    fi
    local built
    built="$(ls "${src}"/output/images/haos_rpi4-64-*.img.xz 2>/dev/null | head -n1)"
    [ -n "${built}" ] || { echo "build finished but no image was found" >&2; exit 1; }
    cp "${built}" "${OUT}/haos_voxhub-cm4-${VERSION}-full.img.xz"
    log "done: ${OUT}/haos_voxhub-cm4-${VERSION}-full.img.xz"
}

"${MODE}"
