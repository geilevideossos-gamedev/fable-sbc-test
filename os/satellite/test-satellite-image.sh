#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
IMAGE="${1:-}"
HOST_PYTHON="${VOXHUB_TEST_PYTHON:-python3}"
WORK=""
ROOT=""
LOOP=""
PASSED=0
FAILED=0

log() {
    printf '\033[1m[voxhub-satellite-test]\033[0m %s\n' "$*"
}

fail() {
    printf '\nERROR: %s\n' "$*" >&2
    exit 1
}

check() {
    if eval "$2"; then
        PASSED=$((PASSED + 1))
        printf '  ok    %s\n' "$1"
    else
        FAILED=$((FAILED + 1))
        printf '  FAIL  %s\n' "$1"
    fi
}

stop_processes() {
    local pid
    [ -n "$ROOT" ] || return 0
    for pid in $(ls /proc | grep -E '^[0-9]+$'); do
        if [ "$(readlink "/proc/$pid/root" 2>/dev/null)" = "$ROOT" ]; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    sleep 2
    for pid in $(ls /proc | grep -E '^[0-9]+$'); do
        if [ "$(readlink "/proc/$pid/root" 2>/dev/null)" = "$ROOT" ]; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
}

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    stop_processes
    if [ -n "$ROOT" ]; then
        local mountpoint
        for mountpoint in tmp run sys proc dev/pts dev ""; do
            umount -l "$ROOT/$mountpoint" 2>/dev/null || true
        done
    fi
    if [ -n "$LOOP" ]; then
        partx -d "$LOOP" 2>/dev/null || true
        losetup -d "$LOOP" 2>/dev/null || true
    fi
    if [ -n "$WORK" ] && [ "${KEEP:-0}" != 1 ]; then
        rm -rf "$WORK"
    fi
    exit "$status"
}

in_root() {
    chroot "$ROOT" /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root "$@"
}

as_voxhub() {
    chroot --userspec=1000:1000 "$ROOT" /usr/bin/env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/home/voxhub \
        XDG_RUNTIME_DIR=/run/user/1000 PULSE_SERVER=unix:/run/user/1000/pulse/native "$@"
}

wait_for() {
    local file="$1" pattern="$2" seconds="$3"
    local waited=0
    until grep -q -E "$pattern" "$file" 2>/dev/null; do
        sleep 2
        waited=$((waited + 2))
        [ "$waited" -lt "$seconds" ] || return 1
    done
}

[ -n "$IMAGE" ] && [ -s "$IMAGE" ] || fail "usage: sudo $0 os/output/voxhub-satellite-....img.xz"
[ "$(id -u)" -eq 0 ] || fail "run as root (loop device, mounts, chroot)"
if [ "$(uname -m)" != "aarch64" ]; then
    [ -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ] || fail "aarch64 emulation missing (sudo apt install qemu-user-static binfmt-support)"
fi
"$HOST_PYTHON" -c 'import aioesphomeapi' 2>/dev/null ||
    fail "$HOST_PYTHON cannot import aioesphomeapi: pip install aioesphomeapi==45.3.1 (or set VOXHUB_TEST_PYTHON)"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-satellite-test.XXXXXX")"
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

log "copying the image (the test writes into the copy only)"
case "$IMAGE" in
    *.xz) xz -dc -T0 "$IMAGE" >"$WORK/test.img" ;;
    *) cp --sparse=always "$IMAGE" "$WORK/test.img" ;;
esac
LOOP="$(losetup -f --show "$WORK/test.img")"
partx -a "$LOOP" 2>/dev/null || true
[ -b "${LOOP}p2" ] || fail "no root partition in $IMAGE"
ROOT="$WORK/root"
mkdir -p "$ROOT"
mount "${LOOP}p2" "$ROOT"
mount --bind /dev "$ROOT/dev"
mount --bind /dev/pts "$ROOT/dev/pts"
mount -t proc proc "$ROOT/proc"
mount -t sysfs sysfs "$ROOT/sys"
mount -t tmpfs tmpfs "$ROOT/run"
mount -t tmpfs tmpfs "$ROOT/tmp"
install -d -m 700 -o 1000 -g 1000 "$ROOT/run/user/1000"
install -d -o 1000 -g 1000 "$ROOT/var/lib/voxhub"
mkdir -p "$ROOT/tmp/leds/voxhub-green" "$ROOT/tmp/leds/voxhub-blue" "$ROOT/tmp/emu"
echo 0 >"$ROOT/tmp/leds/voxhub-green/brightness"
echo 0 >"$ROOT/tmp/leds/voxhub-blue/brightness"
cat >"$ROOT/tmp/emu/sitecustomize.py" <<'PYTHON'
import errno
import socket

_setsockopt = socket.socket.setsockopt


def setsockopt(self, *args):
    try:
        return _setsockopt(self, *args)
    except OSError as err:
        if err.errno == errno.ENOPROTOOPT:
            return None
        raise


socket.socket.setsockopt = setsockopt
PYTHON
NAME="$(sed -n "s/^VOXHUB_NAME='\(.*\)'$/\1/p" "$ROOT/etc/voxhub/satellite.env")"
GAIN="$(sed -n 's/^VOXHUB_MIC_GAIN=//p' "$ROOT/etc/voxhub/satellite.env")"
EXPECTED_DB="$(python3 -c "import math, sys; print(f'{20 * math.log10(float(sys.argv[1])):.2f} dB')" "$GAIN")"

log "starting PipeWire, PipeWire-Pulse and WirePlumber as user voxhub (emulated)"
cat >"$ROOT/tmp/audio.sh" <<'SHELL'
cd /tmp
pipewire >/tmp/pipewire.log 2>&1 &
sleep 4
wireplumber >/tmp/wireplumber.log 2>&1 &
pipewire-pulse >/tmp/pipewire-pulse.log 2>&1 &
for _ in $(seq 1 30); do
    pactl info >/dev/null 2>&1 && break
    sleep 1
done
pactl load-module module-null-sink sink_name=alsa_output.platform-soc_sound.stereo-fallback >/dev/null
pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=alsa_input.platform-soc_sound.stereo-fallback >/dev/null
SHELL
as_voxhub bash /tmp/audio.sh
check "PipeWire answers to pactl inside the image" 'as_voxhub pactl info >"$WORK/pactl-info.txt" 2>&1 && grep -q "Server Name: PulseAudio (on PipeWire" "$WORK/pactl-info.txt"'

log "starting voxhub-lva (launcher -> Linux Voice Assistant) and voxhub-peripherals as the units do"
(as_voxhub PYTHONPATH=/opt/voxhub:/tmp/emu VOXHUB_LVA_DIR=/opt/linux-voice-assistant sh -c \
    'cd /opt/linux-voice-assistant && exec .venv/bin/python3 -m voxhub_satellite.launch --env-file /etc/voxhub/satellite.env --python /opt/linux-voice-assistant/.venv/bin/python3' \
    >"$WORK/voxhub-lva.log" 2>&1 &)
(in_root PYTHONPATH=/opt/voxhub VOXHUB_LED_ROOT=/tmp/leds /opt/linux-voice-assistant/.venv/bin/python3 -m voxhub_satellite.peripherals \
    >"$WORK/voxhub-peripherals.log" 2>&1 &)
check "launcher picks the googlevoicehat source and sink" 'wait_for "$WORK/voxhub-lva.log" "Microphone alsa_input.platform-soc_sound.stereo-fallback, speaker alsa_output.platform-soc_sound.stereo-fallback" 300'
check "Linux Voice Assistant starts its ESPHome API server" 'wait_for "$WORK/voxhub-lva.log" "Server started \(host=" 600'
check "bridge connects to the peripheral API" 'wait_for "$WORK/voxhub-peripherals.log" "Connected to the voice satellite" 120'
check "microphone gain $EXPECTED_DB on the source" 'as_voxhub pactl get-source-volume alsa_input.platform-soc_sound.stereo-fallback | grep -q "$EXPECTED_DB"'
ADDRESS="$(sed -n 's/.*Server started (host=\([0-9.]*\), port=6053).*/\1/p' "$WORK/voxhub-lva.log" | head -n 1)"
log "ESPHome API client on the host -> $ADDRESS:6053 (like Home Assistant)"
check "ESPHome API: device \"$NAME\", entities, LEDs follow connect / mute / unmute / disconnect" \
    '"$HOST_PYTHON" "$REPO/assistant/tests/container/esphome_client.py" "$ADDRESS" "$ROOT/tmp/leds" "$NAME" | tee "$WORK/esphome.txt" | sed "s/^/        /"; grep -q "7 of 7 checks passed" "$WORK/esphome.txt"'
if command -v nft >/dev/null 2>&1; then
    in_root env PYTHONPATH=/opt/voxhub /opt/linux-voice-assistant/.venv/bin/python3 -c \
        'from voxhub_satellite.hubwatch import ruleset; print(ruleset()); print("add element inet voxhub hub4 { 192.0.2.10 }")' >"$WORK/rules.nft"
    check "firewall ruleset of voxhub-hubwatch accepted by nft (check mode, nothing loaded)" 'nft -c -f "$WORK/rules.nft"'
fi
mkdir -p "$REPO/os/output/satellite-checks"
cp "$WORK/voxhub-lva.log" "$WORK/voxhub-peripherals.log" "$WORK/esphome.txt" "$REPO/os/output/satellite-checks/" 2>/dev/null || true
printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
