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
#                     (regular user with sudo + Docker, or VOXHUB_NO_DOCKER=1 on a Buildroot-capable
#                     host; ~30 GB disk; 1-3 h on a fast machine, much longer on 4 cores).
#
# Options:
#   --version X.Y       HAOS version (default: latest stable release tag)
#   --out DIR           output directory (default: os/output)
#   --wifi-ssid NAME --wifi-psk PASS [--wifi-country CC]
#                       pre-seed a NetworkManager Wi-Fi profile (the board has no Ethernet/HDMI)
#   --custom-overlay    (repack) also use os/overlay/voxhub-overlay.dts instead of stock overlays.
#                       NOTE: HAOS deletes /overlays/* on OS updates -> not OTA-safe.
#   --keep-work         keep the work directory
#
# Environment (full mode): VOXHUB_NO_DOCKER=1       build on the host instead of in the HAOS builder container
#                          VOXHUB_GITHUB_VIA_GIT=1  fetch github.com "archive" sources with git (for networks
#                                                   that block those tarball URLs); host builds only
#                          VOXHUB_GOPROXY=URL       Go module proxy for the Go packages, e.g. https://proxy.golang.org
#                                                   (Buildroot fetches every module from its own host otherwise)
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
        -h|--help) sed -n '2,27p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

# HAOS (scripts/enter.sh) and several Buildroot host packages refuse to build as root.  Checked before anything is
# created, so that a first attempt with sudo does not leave a root-owned source tree behind.
if [ "${MODE}" = full ] && [ "$(id -u)" = 0 ]; then
    echo "the full build must run as a regular user (with sudo and docker access), not as root" >&2; exit 1
fi

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
OUT="$(cd "${OUT}" && pwd)"       # Buildroot runs in another directory: every path derived from OUT must be absolute
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

# ---------------------------------------------------------------- github archives via git
# Some networks (corporate proxies, CI sandboxes) refuse https://github.com/<owner>/<repo>/archive/...
# tarball downloads although plain git access to the same public repositories works.  With
# VOXHUB_GITHUB_VIA_GIT=1 every such source that Buildroot's own mirror (sources.buildroot.net) does not
# carry is fetched with a shallow "git fetch" and packed with "git archive | gzip -n" (byte-identical to
# the GitHub tarball) into a local directory that is handed to Buildroot as BR2_PRIMARY_SITE.
# Buildroot still verifies each file against its .hash file, so a wrong tarball cannot slip in.
github_via_git() {      # $1 = HAOS source tree, $2 = mirror directory
    local src="$1" mirror="$2" info tmp dir file url rest owner repo ref spec want got pfx ok failed=""
    need jq curl gzip sha256sum
    info="$(mktemp)"; tmp="$(mktemp -d)"
    make -s -C "${src}/buildroot" O="${src}/output" BR2_EXTERNAL="${src}/buildroot-external" show-info > "${info}"
    jq -r '[.[] | (.dl_dir // .name) as $d | (.downloads // [])[]
            | (.uris[] | select(test("github\\.com/[^/]+/[^/]+/archive"))) as $u
            | [$d, .source, ($u | sub("^[^+]*\\+"; ""))] | @tsv] | unique[]' "${info}" > "${tmp}/list"
    while IFS=$'\t' read -r dir file url; do
        if [ -s "${BR2_DL_DIR}/${dir}/${file}" ] || [ -s "${mirror}/${dir}/${file}" ]; then continue; fi
        if curl -sfIL -o /dev/null "https://sources.buildroot.net/${dir}/${file}"; then continue; fi   # backup mirror has it
        rest="${url#https://github.com/}"; owner="${rest%%/*}"; rest="${rest#*/}"; repo="${rest%%/*}"
        ref="${rest#*/archive}"; ref="${ref#/}"; [ -n "${ref}" ] || ref="${file%.tar.gz}"
        if [[ "${ref}" =~ ^[0-9a-f]{40}$ ]]; then spec="${ref}"; else spec="refs/tags/${ref}"; fi
        log "git: ${owner}/${repo} @ ${ref} -> ${dir}/${file}"
        rm -rf "${tmp}/g"; git init -q "${tmp}/g"
        git -C "${tmp}/g" fetch -q --depth 1 "https://github.com/${owner}/${repo}.git" "${spec}" \
            || { echo "git fetch failed for ${owner}/${repo} ${ref}" >&2; failed="${failed} ${dir}/${file}(fetch)"; continue; }
        mkdir -p "${mirror}/${dir}"
        # expected hash (if the package has one for exactly this file; vendored -go/-cargo tarballs are
        # produced and checked by Buildroot's post-processing step instead)
        want="$(grep -rhs --include='*.hash' -F "  ${file}" "${src}/buildroot" "${src}/buildroot-external" \
                | awk -v f="${file}" '$1 == "sha256" && $3 == f { print $2; exit }' || true)"
        case "${file}" in *-go[0-9]*.tar.gz|*-cargo[0-9]*.tar.gz) want="" ;; esac
        ok=0
        for pfx in "${repo}-${ref#v}" "${repo}-${ref}"; do      # GitHub drops a leading "v" of the tag
            pfx="${pfx//\//-}"
            # written under a temporary name: an interrupted or mismatching tarball must never look finished
            git -C "${tmp}/g" archive --format=tar --prefix="${pfx}/" FETCH_HEAD | gzip -n > "${mirror}/${dir}/${file}.part"
            got="$(sha256sum "${mirror}/${dir}/${file}.part" | cut -d' ' -f1)"
            if [ -z "${want}" ] || [ "${got}" = "${want}" ]; then ok=1; break; fi
        done
        if [ "${ok}" = 1 ]; then
            mv "${mirror}/${dir}/${file}.part" "${mirror}/${dir}/${file}"
        else
            rm -f "${mirror}/${dir}/${file}.part"
            echo "${file}: sha256 ${got} differs from the expected ${want}" >&2; failed="${failed} ${dir}/${file}(hash)"
        fi
    done < "${tmp}/list"
    rm -rf "${tmp}" "${info}"
    if [ -n "${failed}" ]; then     # stop now instead of hours into the build at the first of these packages
        echo "could not prepare these GitHub sources:${failed}" >&2; exit 1
    fi
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

    # Buildroot vendors the Go modules of its Go packages with GOPROXY=direct, i.e. from each module's own host
    # (gopkg.in, golang.org, github.com, ...).  Where one of those cannot be reached a module proxy does the job; go.sum
    # and Buildroot's hash of the vendored tarball are checked exactly as before.
    if [ -n "${VOXHUB_GOPROXY:-}" ]; then
        sed -i "s|GOPROXY=[^ ]* \\\\$|GOPROXY=${VOXHUB_GOPROXY} \\\\|" "${src}/buildroot/package/pkg-golang.mk"
        grep -q "GOPROXY=${VOXHUB_GOPROXY} " "${src}/buildroot/package/pkg-golang.mk" \
            || { echo "could not set the Go module proxy in buildroot/package/pkg-golang.mk" >&2; exit 1; }
    fi
    log "building (this takes a long time)"
    if command -v docker >/dev/null && docker info >/dev/null 2>&1 && [ -z "${VOXHUB_NO_DOCKER:-}" ]; then
        (cd "${src}" && ./scripts/enter.sh make voxhub)
    else
        log "building directly on the host (VOXHUB_NO_DOCKER set or Docker not usable)"
        # the tools the HAOS builder container provides; docker + sudo + loop devices are still
        # needed at the very end (data partition: the Supervisor containers are imported with docker-in-docker)
        need make gcc g++ bc cpio rsync unzip wget curl file perl patch bzip2 xz jq skopeo sudo docker \
             qemu-img pigz zip automake help2man makeinfo flock python3
        # The HAOS scripts expect the source tree at /build (where the builder container mounts it): the RAUC signing key
        # and certificate are generated and read as /build/key.pem and /build/cert.pem (scripts/rauc.sh, genimage/*.cfg).
        # On the host they go to the root of the cloned tree instead, which is the same place.
        { grep -rlE '/build/(key|cert)\.pem' "${ext}/scripts" "${ext}/genimage" 2>/dev/null || true; } | while read -r f; do
            sed -i -E "s|/build/(key\|cert)\.pem|${src}/\1.pem|g" "${f}"
        done
        # the HAOS defconfig points the download dir and ccache at /cache (a volume of the builder container)
        export BR2_DL_DIR="${BR2_DL_DIR:-${OUT}/cache/dl}" BR_CACHE_DIR="${BR_CACHE_DIR:-${OUT}/cache/cc}"
        mkdir -p "${BR2_DL_DIR}" "${BR_CACHE_DIR}"
        (cd "${src}" && make voxhub-config)
        if [ -n "${VOXHUB_GITHUB_VIA_GIT:-}" ]; then
            local mirror="${OUT}/cache/github-mirror"; mkdir -p "${mirror}"
            github_via_git "${src}" "${mirror}"
            echo "BR2_PRIMARY_SITE=\"file://${mirror}\"" >> "${ext}/configs/voxhub_defconfig"
        fi
        # U-Boot's dtc enables YAML output when it finds /usr/include/yaml.h on the build host (Buildroot passes
        # PKG_CONFIG_SYSROOT_DIR=/) and then asks Buildroot's own pkg-config for the library.  On a host with libyaml-dev
        # installed the header is found and the library is not ("undefined reference to yaml_emitter_emit").  The HAOS
        # builder container has no libyaml-dev; on such a host build Buildroot's host-libyaml first so that both exist.
        if [ -e /usr/include/yaml.h ]; then
            log "libyaml-dev is installed on this host: building host-libyaml first (U-Boot's dtc would not link otherwise)"
            make -C "${src}/buildroot" O="${src}/output" BR2_EXTERNAL="${src}/buildroot-external" host-libyaml
        fi
        (cd "${src}" && make voxhub)
    fi
    local built
    built="$(ls "${src}"/output/images/haos_rpi4-64-*.img.xz 2>/dev/null | head -n1)"
    [ -n "${built}" ] || { echo "build finished but no image was found" >&2; exit 1; }
    cp "${built}" "${OUT}/haos_voxhub-cm4-${VERSION}-full.img.xz"
    (cd "${OUT}" && sha256sum "haos_voxhub-cm4-${VERSION}-full.img.xz" > "haos_voxhub-cm4-${VERSION}-full.img.xz.sha256")
    log "done: ${OUT}/haos_voxhub-cm4-${VERSION}-full.img.xz"
}

"${MODE}"
