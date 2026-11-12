#!/usr/bin/env bash
set -euo pipefail

RADIO_PORT="${VOXHUB_RADIO_PORT:-/dev/ttyAMA4}"
UART4_SYSFS_DEVICE="/sys/devices/platform/soc/fe201800.serial"
GPIO_CHIP_LABEL="pinctrl-bcm2711"
GPIO_RESET=24
GPIO_BOOT=25
CONTAINER_IMAGE="${VOXHUB_CONTAINER_IMAGE:-debian:bookworm-slim}"
CONTAINER_OPTIONS="${VOXHUB_CONTAINER_OPTIONS:-}"
SERIAL_BAUD_RATES=(500000 115200)

ZIGBEE_NAME="CC1352P2_CC2652P_launchpad_coordinator_20250321"
ZIGBEE_REVISION="20250321"
ZIGBEE_HEX_SHA256="c2d3a05fe7146b6d57424571629f6efd9166395202babb86639849e9af31a1ff"
ZIGBEE_SOURCES=(
    "https://raw.githubusercontent.com/Koenkk/Z-Stack-firmware/5e4db67e550d41ea6dc6cd86ceeb04d82ffe1bfb/coordinator/Z-Stack_3.x.0/bin/${ZIGBEE_NAME}.zip"
    "e9e256e3615937267ae3d8c60641bb7deca904a506711afa7c6247df2cb84883"
    "https://github.com/Koenkk/Z-Stack-firmware/releases/download/Z-Stack_3.x.0_coordinator_20250321/${ZIGBEE_NAME}.zip"
    "66f5d3d20c2ca5375133da6a47b959525e39d707736a4d1b01b44bd95b04273a"
)

THREAD_NAME="CC1352P2_CC2652P_launchpad_ot_rcp_2025_3_1"
THREAD_VERSION_MARKER="Koenkk-2025.3.1"
THREAD_HEX_SHA256="75330d9294629feb72d401a2ec73f8a886f822d1de2b74a513758e19494f7e9f"
THREAD_SOURCES=(
    "https://github.com/Koenkk/OpenThread-TexasInstruments-firmware/releases/download/2025.3.1/${THREAD_NAME}.zip"
    "5858a338f4d82e11a269410a9917561e91a5130fe3d6207dfc7066b0ed9e7e1d"
)

BSL_SOURCES=(
    "https://raw.githubusercontent.com/JelmerT/cc2538-bsl/28cce9749bfb73c50363ded01bd8001b1639d9fb/cc2538_bsl/cc2538_bsl.py"
    "392cf987b8f741401547dc0faa8f43af085b3e4378facfafaecdfd19ea6503f3"
)

FIRMWARE_KIND="zigbee"
METHOD="auto"
DRY_RUN=0
FORCE=0
PROBE_ONLY=0
IN_CONTAINER=0
USE_CONTAINER=0
WORK_DIR=""
FIRMWARE_HEX=""
PROBE_RESULT=""
GPIO_BACKEND=""
GPIO_CHIP=""
GPIO_TOUCHED=0
declare -A GPIO_HOLDER_PIDS=()
ORIGINAL_ARGUMENTS=("$@")
SCRIPT_PATH="${BASH_SOURCE[0]:-}"

say() {
    printf '%s\n' "$*"
}

step() {
    printf '\n==> %s\n' "$*"
}

fail() {
    printf '\nERROR: %s\n' "$*" >&2
    exit 1
}

show_help() {
    cat <<'HELP'
flash_zigbee.sh - write firmware to the VoxHub radio module (RF-BM-2652P2, TI CC2652P)

Usage:
  sudo bash flash_zigbee.sh [options]

Firmware:
  --zigbee            Z-Stack coordinator 20250321 for ZHA / Zigbee2MQTT (default)
  --thread            OpenThread RCP 2025.3.1 for the OpenThread Border Router

Options:
  --method METHOD     auto (default): serial bootloader first, JTAG if it does not answer
                      serial: serial bootloader only
                      jtag: OpenOCD bit-bang JTAG only (erases the whole chip first)
  --port PATH         serial port of the radio (default /dev/ttyAMA4)
  --force             write even if the wanted firmware already answers
  --probe-only        only report which firmware answers on the serial port
  --container         run inside a Debian container even if this system has apt-get
  --dry-run           show every step, download and check the files, touch no hardware
  --help              this text

Board wiring used: UART4 on GPIO8/9, GPIO24 high = radio in reset, GPIO25 low at
reset = ROM bootloader, JTAG TMS GPIO22, TCK GPIO23, TDO GPIO17, TDI GPIO7.
HELP
}

parse_arguments() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --zigbee) FIRMWARE_KIND="zigbee" ;;
            --thread) FIRMWARE_KIND="thread" ;;
            --method)
                [ "$#" -ge 2 ] || fail "--method needs a value: auto, serial or jtag"
                METHOD="$2"
                shift
                ;;
            --port)
                [ "$#" -ge 2 ] || fail "--port needs a value, for example /dev/ttyAMA4"
                RADIO_PORT="$2"
                shift
                ;;
            --force) FORCE=1 ;;
            --probe-only) PROBE_ONLY=1 ;;
            --container) USE_CONTAINER=1 ;;
            --in-container) IN_CONTAINER=1 ;;
            --dry-run) DRY_RUN=1 ;;
            --help | -h)
                show_help
                exit 0
                ;;
            *) fail "Unknown option: $1 (see --help)" ;;
        esac
        shift
    done
    case "$METHOD" in
        auto | serial | jtag) ;;
        *) fail "--method must be auto, serial or jtag" ;;
    esac
}

select_firmware() {
    if [ "$FIRMWARE_KIND" = "zigbee" ]; then
        FIRMWARE_NAME="$ZIGBEE_NAME"
        FIRMWARE_HEX_SHA256="$ZIGBEE_HEX_SHA256"
        FIRMWARE_SOURCES=("${ZIGBEE_SOURCES[@]}")
        FIRMWARE_PROTOCOL="znp"
        FIRMWARE_TITLE="Zigbee coordinator (Z-Stack $ZIGBEE_REVISION)"
    else
        FIRMWARE_NAME="$THREAD_NAME"
        FIRMWARE_HEX_SHA256="$THREAD_HEX_SHA256"
        FIRMWARE_SOURCES=("${THREAD_SOURCES[@]}")
        FIRMWARE_PROTOCOL="spinel"
        FIRMWARE_TITLE="OpenThread RCP 2025.3.1"
    fi
}

port_is_url() {
    case "$RADIO_PORT" in
        *://*) return 0 ;;
        *) return 1 ;;
    esac
}

running_on_home_assistant_os() {
    command -v ha >/dev/null 2>&1 || [ -n "${SUPERVISOR_TOKEN:-}" ]
}

docker_is_usable() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

require_root() {
    if [ "$DRY_RUN" -eq 0 ] && [ "$(id -u)" -ne 0 ]; then
        fail "Please run this script as root: sudo bash flash_zigbee.sh"
    fi
}

continue_inside_container() {
    step "Starting a temporary $CONTAINER_IMAGE container that has access to the serial port and the GPIOs"
    [ -f "$SCRIPT_PATH" ] || fail "Save this script to a file first and start it with: bash flash_zigbee.sh"
    local options=()
    if [ -n "$CONTAINER_OPTIONS" ]; then
        read -r -a options <<<"$CONTAINER_OPTIONS"
    fi
    local forwarded=()
    local argument
    for argument in ${ORIGINAL_ARGUMENTS[@]+"${ORIGINAL_ARGUMENTS[@]}"}; do
        [ "$argument" = "--container" ] || forwarded+=("$argument")
    done
    docker run --rm --interactive --privileged --pid=host --network=host \
        --volume /dev:/dev \
        --env "VOXHUB_RADIO_PORT=$RADIO_PORT" \
        --env "VOXHUB_GPIO_SIM_DIR=${VOXHUB_GPIO_SIM_DIR:-}" \
        ${options[@]+"${options[@]}"} \
        "$CONTAINER_IMAGE" \
        bash -c 'cat > /tmp/flash_zigbee.sh && exec bash /tmp/flash_zigbee.sh "$@" < /dev/null' \
        flash_zigbee --in-container ${forwarded[@]+"${forwarded[@]}"} <"$SCRIPT_PATH"
}

choose_where_to_run() {
    if [ "$IN_CONTAINER" -eq 1 ]; then
        say "Running inside the temporary container."
        return 0
    fi
    if [ "$USE_CONTAINER" -eq 0 ] && command -v apt-get >/dev/null 2>&1; then
        say "Running directly on this system (apt-get is available)."
        return 0
    fi
    if docker_is_usable; then
        continue_inside_container
        exit $?
    fi
    if running_on_home_assistant_os; then
        fail "This looks like Home Assistant OS, but the docker command does not work here.
Open the app 'Advanced SSH & Web Terminal', switch 'Protection mode' OFF on its Info tab,
restart the app and run this script again."
    fi
    fail "Neither apt-get nor a usable docker command was found. Use Raspberry Pi OS Lite (64-bit)
or the Home Assistant app 'Advanced SSH & Web Terminal' with protection mode off."
}

basic_tools_are_missing() {
    command -v python3 >/dev/null 2>&1 || return 0
    python3 -c 'import serial, intelhex' >/dev/null 2>&1 || return 0
    command -v sha256sum >/dev/null 2>&1 || return 0
    if [ -z "${VOXHUB_GPIO_SIM_DIR:-}" ]; then
        command -v pinctrl >/dev/null 2>&1 || command -v gpioset >/dev/null 2>&1 || return 0
    fi
    return 1
}

install_packages() {
    command -v apt-get >/dev/null 2>&1 || fail "Cannot install $* because apt-get is missing."
    say "Installing: $*"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update || fail "apt-get update failed. Is the network connection up?"
    apt-get install --yes --no-install-recommends "$@" || fail "apt-get could not install: $*"
}

install_basic_tools() {
    step "Checking the tools this script needs"
    if [ "$DRY_RUN" -eq 1 ]; then
        command -v python3 >/dev/null 2>&1 || fail "The dry run needs python3 to unpack and check the firmware."
        say "  [dry-run] would install with apt-get if missing: python3 python3-serial python3-intelhex gpiod curl ca-certificates"
        return 0
    fi
    if basic_tools_are_missing; then
        install_packages python3 python3-serial python3-intelhex gpiod curl ca-certificates
    fi
    python3 -c 'import serial, intelhex' || fail "The Python modules serial and intelhex are still missing."
    say "python3, pyserial and intelhex are present."
}

prepare_work_dir() {
    WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-radio.XXXXXX")"
}

remove_work_dir_and_release_gpios() {
    local status=$?
    trap - EXIT INT TERM
    if [ "$GPIO_TOUCHED" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
        gpio_release "$GPIO_RESET" pull-down || true
        gpio_release "$GPIO_BOOT" pull-up || true
    fi
    if [ -n "$WORK_DIR" ] && [ -d "$WORK_DIR" ]; then
        rm -rf "$WORK_DIR"
    fi
    exit "$status"
}

download_file() {
    local url="$1" destination="$2"
    if command -v curl >/dev/null 2>&1; then
        curl --fail --silent --show-error --location --retry 3 --output "$destination" "$url"
    elif command -v wget >/dev/null 2>&1; then
        wget --quiet --tries=3 --output-document="$destination" "$url"
    else
        python3 -c 'import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])' "$url" "$destination"
    fi
}

file_sha256() {
    sha256sum "$1" | cut -d ' ' -f 1
}

download_verified() {
    local destination="$1" description="$2"
    shift 2
    local url expected actual
    while [ "$#" -ge 2 ]; do
        url="$1"
        expected="$2"
        shift 2
        say "  from $url"
        if download_file "$url" "$destination.part"; then
            actual="$(file_sha256 "$destination.part")"
            if [ "$actual" = "$expected" ]; then
                mv "$destination.part" "$destination"
                say "  SHA256 matches: $actual"
                return 0
            fi
            say "  SHA256 does not match (got $actual, expected $expected) - trying the next source"
        else
            say "  download failed - trying the next source"
        fi
    done
    fail "Could not download $description with the expected checksum. Nothing was written to the radio."
}

write_helper_programs() {
    cat >"$WORK_DIR/inspect_image.py" <<'PYTHON'
import struct
import sys

FLASH_END = 0x58000
BL_CONFIG = 0x57FD8
IMAGE_VALID_CONF = 0x57FEC
EXPECTED_BOOT_PIN = int(sys.argv[2])


def read_intel_hex(path):
    memory = {}
    base = 0
    with open(path, "r", encoding="ascii") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            raw = bytes.fromhex(line[1:])
            if line[0] != ":" or sum(raw) & 0xFF:
                raise SystemExit("The firmware file is damaged in line %d." % number)
            count, offset, kind = raw[0], (raw[1] << 8) | raw[2], raw[3]
            data = raw[4:4 + count]
            if kind == 0:
                for index, value in enumerate(data):
                    memory[base + offset + index] = value
            elif kind == 2:
                base = ((data[0] << 8) | data[1]) << 4
            elif kind == 4:
                base = ((data[0] << 8) | data[1]) << 16
            elif kind == 1:
                break
    return memory


def word(memory, address):
    return struct.unpack("<I", bytes(memory.get(address + i, 0xFF) for i in range(4)))[0]


memory = read_intel_hex(sys.argv[1])
end = max(memory) + 1
config = word(memory, BL_CONFIG)
raw = " ".join("%02X" % memory.get(BL_CONFIG + i, 0xFF) for i in range(4))
bootloader_enable = config >> 24
level = (config >> 16) & 1
pin = (config >> 8) & 0xFF
backdoor_enable = config & 0xFF
print("  image ends at 0x%X (%d KiB flash, CC2652P / CC1352P layout)" % (end, end // 1024))
print("  CCFG BL_CONFIG at 0x%X: bytes %s" % (BL_CONFIG, raw))
print("    ROM bootloader enable 0x%02X, backdoor enable 0x%02X, pin DIO%d, active %s"
      % (bootloader_enable, backdoor_enable, pin, "high" if level else "low"))
problems = []
if end != FLASH_END:
    problems.append("the image is not for a chip with 352 KiB flash")
if bootloader_enable != 0xC5 or backdoor_enable != 0xC5:
    problems.append("the serial bootloader backdoor is not enabled")
if pin != EXPECTED_BOOT_PIN or level != 0:
    problems.append("the backdoor is not on DIO%d active low" % EXPECTED_BOOT_PIN)
if word(memory, IMAGE_VALID_CONF) != 0:
    problems.append("the image is not marked as valid")
if problems:
    raise SystemExit("REFUSED: " + "; ".join(problems) + ".")
print("  OK: this image keeps the serial bootloader reachable through DIO%d (GPIO25)." % pin)
PYTHON

    cat >"$WORK_DIR/unpack_firmware.py" <<'PYTHON'
import sys
import zipfile

archive, member, destination = sys.argv[1:4]
with zipfile.ZipFile(archive) as bundle:
    with bundle.open(member) as source, open(destination, "wb") as target:
        target.write(source.read())
PYTHON

    cat >"$WORK_DIR/probe_radio.py" <<'PYTHON'
import struct
import sys
import time

import serial

PORT = sys.argv[1]
WANTED = sys.argv[2]
ATTEMPTS = int(sys.argv[3])


def open_port(baud):
    port = serial.serial_for_url(PORT, do_not_open=True)
    port.baudrate = baud
    port.timeout = 0.1
    port.open()
    return port


def znp_frame(command0, command1, data=b""):
    body = bytes([len(data), command0, command1]) + data
    checksum = 0
    for value in body:
        checksum ^= value
    return b"\xFE" + body + bytes([checksum])


def znp_frames(buffer):
    frames = []
    while True:
        start = buffer.find(b"\xFE")
        if start < 0:
            del buffer[:]
            return frames
        del buffer[:start]
        if len(buffer) < 5 or len(buffer) < buffer[1] + 5:
            return frames
        length = buffer[1]
        frame = bytes(buffer[1:length + 5])
        checksum = 0
        for value in frame[:-1]:
            checksum ^= value
        if checksum != frame[-1]:
            del buffer[:1]
            continue
        frames.append((frame[1], frame[2], frame[3:-1]))
        del buffer[:length + 5]


def znp_request(port, command0, command1, wait=1.5):
    port.reset_input_buffer()
    port.write(znp_frame(command0, command1))
    deadline = time.monotonic() + wait
    buffer = bytearray()
    while time.monotonic() < deadline:
        buffer += port.read(64)
        for answer0, answer1, data in znp_frames(buffer):
            if answer0 == (command0 | 0x40) and answer1 == command1:
                return data
    return None


def probe_znp():
    port = open_port(115200)
    try:
        if znp_request(port, 0x21, 0x01) is None:
            return None
        version = znp_request(port, 0x21, 0x02)
        if version is None or len(version) < 9:
            return "znp revision=unknown"
        revision = struct.unpack("<I", version[5:9])[0]
        return "znp revision=%d release=%d.%d.%d product=%d transport=%d" % (
            revision, version[2], version[3], version[4], version[1], version[0])
    finally:
        port.close()


def hdlc_checksum(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


def hdlc_encode(payload):
    crc = hdlc_checksum(payload)
    out = bytearray([0x7E])
    for value in bytes(payload) + bytes([crc & 0xFF, crc >> 8]):
        if value in (0x7E, 0x7D, 0x11, 0x13, 0xF8):
            out += bytes([0x7D, value ^ 0x20])
        else:
            out.append(value)
    out.append(0x7E)
    return bytes(out)


def hdlc_frames(buffer):
    frames = []
    while buffer.count(0x7E) >= 2:
        del buffer[:buffer.find(b"\x7E")]
        end = buffer.find(b"\x7E", 1)
        chunk = bytes(buffer[1:end])
        del buffer[:end]
        decoded = bytearray()
        escape = False
        for value in chunk:
            if escape:
                decoded.append(value ^ 0x20)
                escape = False
            elif value == 0x7D:
                escape = True
            else:
                decoded.append(value)
        if len(decoded) >= 5 and hdlc_checksum(decoded[:-2]) == (decoded[-2] | (decoded[-1] << 8)):
            frames.append(bytes(decoded[:-2]))
    return frames


def probe_spinel():
    port = open_port(460800)
    try:
        port.reset_input_buffer()
        port.write(hdlc_encode(bytes([0x81, 0x02, 0x02])))
        deadline = time.monotonic() + 1.5
        buffer = bytearray()
        while time.monotonic() < deadline:
            buffer += port.read(64)
            for frame in hdlc_frames(buffer):
                if len(frame) > 3 and frame[1] == 0x06 and frame[2] == 0x02:
                    text = frame[3:].split(b"\x00")[0].decode("utf-8", "replace")
                    return "spinel version=%s" % text
        return None
    finally:
        port.close()


def probe_once():
    order = [probe_znp, probe_spinel] if WANTED != "spinel" else [probe_spinel, probe_znp]
    for probe in order:
        try:
            answer = probe()
        except serial.SerialException as error:
            raise SystemExit("PORT-ERROR %s" % error)
        if answer:
            return answer
    return None


answer = None
for attempt in range(ATTEMPTS):
    answer = probe_once()
    if answer and (WANTED == "any" or answer.startswith(WANTED)):
        break
    time.sleep(1.0)
print("RESULT %s" % (answer or "none"))
if WANTED != "any" and not (answer or "").startswith(WANTED):
    sys.exit(3)
PYTHON

    cat >"$WORK_DIR/voxhub-cc2652-jtag.cfg" <<'OPENOCD'
if {![info exists VOXHUB_GPIO_CHIP]} {
    set VOXHUB_GPIO_CHIP 0
}

adapter driver linuxgpiod
adapter gpio tck 23 -chip $VOXHUB_GPIO_CHIP
adapter gpio tms 22 -chip $VOXHUB_GPIO_CHIP
adapter gpio tdi 7 -chip $VOXHUB_GPIO_CHIP
adapter gpio tdo 17 -chip $VOXHUB_GPIO_CHIP
transport select jtag
adapter speed 100
reset_config none
foreach voxhub_server {gdb tcl telnet} {
    if {[llength [info commands $voxhub_server]]} {
        $voxhub_server port disabled
    } else {
        ${voxhub_server}_port disabled
    }
}

if {[catch {find target/ti_cc26x2.cfg} voxhub_target_config]} {
    set voxhub_target_config [find target/ti/cc26x2.cfg]
}
source $voxhub_target_config

proc voxhub_halt_radio {} {
    if {[catch {reset halt}]} {
        reset
        halt
    }
    catch {mww 0x40080C00 0x1ACCE551}
    catch {mww 0x40080418 0x00000100}
}

proc voxhub_jtag_flash {image} {
    init
    voxhub_halt_radio
    flash probe 0
    echo "VOXHUB: erasing the whole flash"
    flash erase_sector 0 0 last
    echo "VOXHUB: writing $image"
    flash write_image $image
    echo "VOXHUB: verifying"
    verify_image $image
    echo "VOXHUB_JTAG_FLASH_VERIFIED"
    reset run
    shutdown
}
OPENOCD
}

fetch_downloads() {
    step "Downloading the flashing tool and the firmware ($FIRMWARE_TITLE)"
    say "cc2538-bsl (TI serial bootloader tool, pinned commit 28cce97):"
    download_verified "$WORK_DIR/cc2538_bsl.py" "cc2538-bsl" "${BSL_SOURCES[@]}"
    say "$FIRMWARE_NAME.zip:"
    download_verified "$WORK_DIR/firmware.zip" "the firmware archive" "${FIRMWARE_SOURCES[@]}"
    FIRMWARE_HEX="$WORK_DIR/$FIRMWARE_NAME.hex"
    python3 "$WORK_DIR/unpack_firmware.py" "$WORK_DIR/firmware.zip" "$FIRMWARE_NAME.hex" "$FIRMWARE_HEX" ||
        fail "The firmware archive does not contain $FIRMWARE_NAME.hex."
    local actual
    actual="$(file_sha256 "$FIRMWARE_HEX")"
    [ "$actual" = "$FIRMWARE_HEX_SHA256" ] ||
        fail "The unpacked firmware has an unexpected SHA256 ($actual). Nothing was written to the radio."
    say "$FIRMWARE_NAME.hex SHA256 matches: $actual"
}

inspect_firmware() {
    step "Checking that the firmware keeps the bootloader backdoor on DIO15"
    python3 "$WORK_DIR/inspect_image.py" "$FIRMWARE_HEX" 15 ||
        fail "The firmware image failed the safety check. Nothing was written to the radio."
}

find_uart4_device() {
    local name
    [ -d "$UART4_SYSFS_DEVICE" ] || return 1
    name="$(find "$UART4_SYSFS_DEVICE" -maxdepth 5 -name 'ttyAMA*' 2>/dev/null | head -n 1)"
    [ -n "$name" ] || return 1
    name="/dev/$(basename "$name")"
    [ -c "$name" ] || return 1
    printf '%s\n' "$name"
}

locate_radio_port() {
    step "Looking for the radio's serial port"
    if port_is_url || [ "$DRY_RUN" -eq 1 ]; then
        say "Using $RADIO_PORT"
        return 0
    fi
    local found
    if [ ! -c "$RADIO_PORT" ] && found="$(find_uart4_device)"; then
        say "$RADIO_PORT does not exist, but UART4 is present as $found - using that."
        RADIO_PORT="$found"
    fi
    if [ ! -c "$RADIO_PORT" ] && command -v dtoverlay >/dev/null 2>&1; then
        say "UART4 is not enabled yet - loading the uart4 overlay for this session."
        dtoverlay uart4 || true
        sleep 1
        if found="$(find_uart4_device)"; then
            RADIO_PORT="$found"
        fi
    fi
    [ -c "$RADIO_PORT" ] || fail "The serial port $RADIO_PORT does not exist.
Add the line 'dtoverlay=uart4' to config.txt on the boot partition
(Raspberry Pi OS: /boot/firmware/config.txt), reboot and run this script again."
    say "Using $RADIO_PORT"
}

refuse_if_port_is_busy() {
    port_is_url && return 0
    [ "$DRY_RUN" -eq 1 ] && return 0
    local real users pid
    real="$(readlink -f "$RADIO_PORT")"
    users="$(find /proc/[0-9]*/fd -maxdepth 1 -lname "$real" 2>/dev/null | cut -d / -f 3 | sort -u || true)"
    [ -n "$users" ] || return 0
    say "The serial port $RADIO_PORT is in use by:"
    while IFS= read -r pid; do
        say "  process $pid: $(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | cut -c 1-100)"
    done <<<"$users"
    fail "Free the port first, then run this script again:
  - ZHA: Settings -> Devices & services -> Zigbee Home Automation -> three dots -> Disable
  - Zigbee2MQTT or OpenThread Border Router: stop the app
Enable or start it again when this script has finished."
}

select_gpio_backend() {
    step "Selecting how to drive GPIO$GPIO_RESET (reset) and GPIO$GPIO_BOOT (bootloader strap)"
    if [ "$DRY_RUN" -eq 1 ]; then
        GPIO_BACKEND="dry-run"
    elif [ -n "${VOXHUB_GPIO_SIM_DIR:-}" ]; then
        GPIO_BACKEND="simulation"
    elif command -v pinctrl >/dev/null 2>&1 && pinctrl get "$GPIO_BOOT" >/dev/null 2>&1; then
        GPIO_BACKEND="pinctrl"
    elif command -v gpioset >/dev/null 2>&1 && command -v gpiodetect >/dev/null 2>&1; then
        GPIO_CHIP="$(gpiodetect | awk -v label="[$GPIO_CHIP_LABEL]" '$2 == label { print $1; exit }')"
        [ -n "$GPIO_CHIP" ] || fail "No GPIO controller named $GPIO_CHIP_LABEL was found. Is this a Compute Module 4?"
        case "$(gpioset --version | head -n 1)" in
            *" v1."*) GPIO_BACKEND="gpioset-v1" ;;
            *) GPIO_BACKEND="gpioset-v2" ;;
        esac
    else
        fail "Neither pinctrl nor gpioset is available to drive the GPIOs."
    fi
    say "GPIO method: $GPIO_BACKEND ${GPIO_CHIP:+on $GPIO_CHIP}"
}

pause() {
    if [ "$DRY_RUN" -eq 0 ]; then
        sleep "$1"
    fi
}

stop_gpio_holder() {
    local line="$1"
    local pid="${GPIO_HOLDER_PIDS[$line]:-}"
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        unset "GPIO_HOLDER_PIDS[$line]"
    fi
}

start_gpio_holder() {
    local line="$1" value="$2"
    stop_gpio_holder "$line"
    if [ "$GPIO_BACKEND" = "gpioset-v1" ]; then
        gpioset --mode=signal "$GPIO_CHIP" "$line=$value" &
    else
        gpioset --chip "$GPIO_CHIP" "$line=$value" &
    fi
    GPIO_HOLDER_PIDS[$line]=$!
    sleep 0.2
    if ! kill -0 "${GPIO_HOLDER_PIDS[$line]}" 2>/dev/null; then
        unset "GPIO_HOLDER_PIDS[$line]"
        fail "Could not drive GPIO$line. Another program or driver is using this line."
    fi
}

gpio_drive() {
    local line="$1" value="$2"
    GPIO_TOUCHED=1
    case "$GPIO_BACKEND" in
        dry-run) say "  [dry-run] would drive GPIO$line to $value" ;;
        simulation) printf '%s\n' "$value" >"$VOXHUB_GPIO_SIM_DIR/gpio$line" ;;
        pinctrl)
            if [ "$value" -eq 1 ]; then
                pinctrl set "$line" op dh
            else
                pinctrl set "$line" op dl
            fi
            ;;
        *) start_gpio_holder "$line" "$value" ;;
    esac
}

gpio_release() {
    local line="$1" bias="$2"
    case "$GPIO_BACKEND" in
        dry-run) say "  [dry-run] would release GPIO$line (input, $bias)" ;;
        simulation)
            if [ "$bias" = "pull-up" ]; then
                printf '1\n' >"$VOXHUB_GPIO_SIM_DIR/gpio$line"
            else
                printf '0\n' >"$VOXHUB_GPIO_SIM_DIR/gpio$line"
            fi
            ;;
        pinctrl)
            if [ "$bias" = "pull-up" ]; then
                pinctrl set "$line" ip pu
            else
                pinctrl set "$line" ip pd
            fi
            ;;
        gpioset-v1)
            stop_gpio_holder "$line"
            gpioget --bias="$bias" "$GPIO_CHIP" "$line" >/dev/null 2>&1 ||
                gpioget "$GPIO_CHIP" "$line" >/dev/null 2>&1 || true
            ;;
        gpioset-v2)
            stop_gpio_holder "$line"
            gpioget --chip "$GPIO_CHIP" --bias "$bias" "$line" >/dev/null 2>&1 ||
                gpioget --chip "$GPIO_CHIP" "$line" >/dev/null 2>&1 || true
            ;;
        *) ;;
    esac
}

gpio_level() {
    local line="$1"
    case "$GPIO_BACKEND" in
        simulation) cat "$VOXHUB_GPIO_SIM_DIR/gpio$line" ;;
        pinctrl) pinctrl lev "$line" ;;
        gpioset-v1) gpioget "$GPIO_CHIP" "$line" ;;
        gpioset-v2) gpioget --chip "$GPIO_CHIP" --numeric "$line" ;;
        *) printf '?\n' ;;
    esac
}

radio_enter_bootloader() {
    say "Resetting the radio with the bootloader strap held low (GPIO$GPIO_BOOT low, GPIO$GPIO_RESET high, then released)."
    gpio_drive "$GPIO_BOOT" 0
    gpio_drive "$GPIO_RESET" 1
    pause 0.3
    gpio_release "$GPIO_RESET" pull-down
    pause 0.5
    gpio_release "$GPIO_BOOT" pull-up
    pause 0.2
}

radio_restart() {
    say "Restarting the radio normally (strap released, reset pulse on GPIO$GPIO_RESET)."
    gpio_release "$GPIO_BOOT" pull-up
    pause 0.2
    gpio_drive "$GPIO_RESET" 1
    pause 0.3
    gpio_release "$GPIO_RESET" pull-down
    pause 2
    local level
    level="$(gpio_level "$GPIO_BOOT" 2>/dev/null || printf '?\n')"
    if [ "$level" = "0" ]; then
        say "WARNING: GPIO$GPIO_BOOT reads low although it is released. The radio will stay in its bootloader."
        say "         Check the 10k pull-up on the ZB_BOOT net."
    fi
}

probe_radio() {
    local wanted="$1" attempts="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        say "  [dry-run] would ask the radio on $RADIO_PORT which firmware it runs (looking for: $wanted)"
        PROBE_RESULT="RESULT dry-run"
        return 0
    fi
    local status=0
    PROBE_RESULT="$(python3 "$WORK_DIR/probe_radio.py" "$RADIO_PORT" "$wanted" "$attempts" 2>&1)" || status=$?
    PROBE_RESULT="$(printf '%s\n' "$PROBE_RESULT" | tail -n 1)"
    return "$status"
}

describe_probe_result() {
    case "$PROBE_RESULT" in
        "RESULT znp "*) say "The radio answers as a Zigbee coordinator (Z-Stack ZNP, 115200 baud): ${PROBE_RESULT#RESULT znp }" ;;
        "RESULT spinel "*) say "The radio answers as an OpenThread RCP (460800 baud): ${PROBE_RESULT#RESULT spinel }" ;;
        "RESULT none") say "The radio does not answer as Z-Stack (115200 baud) or as OpenThread RCP (460800 baud)." ;;
        "RESULT dry-run") ;;
        *) say "Probe output: $PROBE_RESULT" ;;
    esac
}

report_current_firmware() {
    step "Asking the radio which firmware it runs now"
    probe_radio any 1 || true
    describe_probe_result
}

wanted_firmware_is_already_there() {
    case "$FIRMWARE_KIND:$PROBE_RESULT" in
        "zigbee:RESULT znp revision=$ZIGBEE_REVISION "*) return 0 ;;
        "thread:RESULT spinel "*"$THREAD_VERSION_MARKER"*) return 0 ;;
        *) return 1 ;;
    esac
}

flash_over_serial() {
    step "Writing the firmware through the ROM serial bootloader"
    local baud status log="$WORK_DIR/cc2538-bsl.log"
    for baud in "${SERIAL_BAUD_RATES[@]}"; do
        radio_enter_bootloader
        say "Running: python3 cc2538_bsl.py -p $RADIO_PORT -b $baud -e -w -v $FIRMWARE_NAME.hex"
        if [ "$DRY_RUN" -eq 1 ]; then
            say "  [dry-run] nothing is written"
            return 0
        fi
        status=0
        python3 "$WORK_DIR/cc2538_bsl.py" -p "$RADIO_PORT" -b "$baud" -e -w -v "$FIRMWARE_HEX" 2>&1 |
            tee "$log" || status=$?
        if [ "$status" -eq 0 ] && grep -q 'Verified (match' "$log"; then
            say "The bootloader confirmed the checksum of the written image."
            return 0
        fi
        if grep -q "Timeout waiting for ACK/NACK after 'Synch" "$log"; then
            say "The bootloader did not answer at $baud baud."
        else
            say "cc2538-bsl stopped with an error at $baud baud."
        fi
    done
    return 1
}

gpio_chip_number() {
    local name=""
    if command -v gpiodetect >/dev/null 2>&1; then
        name="$(gpiodetect 2>/dev/null | awk -v label="[$GPIO_CHIP_LABEL]" '$2 == label { print $1; exit }')"
    fi
    name="${name#gpiochip}"
    printf '%s\n' "${name:-0}"
}

flash_over_jtag() {
    step "Writing the firmware through JTAG (OpenOCD bit-bang on GPIO22, 23, 7 and 17)"
    local chip log="$WORK_DIR/openocd.log" status=0
    if [ "$DRY_RUN" -eq 1 ]; then
        say "  [dry-run] would run: openocd -c 'set VOXHUB_GPIO_CHIP 0' -f voxhub-cc2652-jtag.cfg -c 'voxhub_jtag_flash $FIRMWARE_NAME.hex'"
        return 0
    fi
    if ! command -v openocd >/dev/null 2>&1; then
        install_packages openocd gpiod
    fi
    if ! openocd -c "adapter list" -c "shutdown" 2>&1 | grep -q 'linuxgpiod'; then
        say "This OpenOCD build has no linuxgpiod driver (plain Debian 13 packages it that way)."
        say "Use Raspberry Pi OS, or run this script with --container to use the Debian 12 build."
        return 1
    fi
    gpio_release "$GPIO_BOOT" pull-up
    gpio_drive "$GPIO_RESET" 1
    sleep 0.3
    gpio_release "$GPIO_RESET" pull-down
    sleep 0.5
    chip="$(gpio_chip_number)"
    say "Running: openocd -c 'set VOXHUB_GPIO_CHIP $chip' -f voxhub-cc2652-jtag.cfg -c 'voxhub_jtag_flash $FIRMWARE_NAME.hex'"
    openocd -c "set VOXHUB_GPIO_CHIP $chip" -f "$WORK_DIR/voxhub-cc2652-jtag.cfg" \
        -c "voxhub_jtag_flash $FIRMWARE_HEX" 2>&1 | tee "$log" || status=$?
    if [ "$status" -eq 0 ] && grep -q 'VOXHUB_JTAG_FLASH_VERIFIED' "$log"; then
        say "OpenOCD wrote and verified the image."
        return 0
    fi
    say "OpenOCD did not finish (exit status $status)."
    if grep -q -i 'all ones\|all zeroes\|scan chain interrogation failed' "$log"; then
        say "The chip did not answer on JTAG: check TMS (GPIO22), TCK (GPIO23), TDO (GPIO17) and TDI (GPIO7)."
    fi
    return 1
}

write_firmware() {
    case "$METHOD" in
        serial)
            flash_over_serial || fail "The serial bootloader did not accept the firmware.
Run the script again with '--method jtag' to erase and write the chip through JTAG."
            ;;
        jtag)
            flash_over_jtag || fail "JTAG flashing failed. The radio was not programmed."
            ;;
        *)
            if ! flash_over_serial; then
                say ""
                say "The serial bootloader is not reachable. This happens when the module was delivered"
                say "with a firmware that has no backdoor on DIO15. Falling back to JTAG."
                flash_over_jtag || fail "Neither the serial bootloader nor JTAG could program the radio.
If JTAG reported a locked debug port, the chip needs a TI XDS110 probe on the Tag-Connect pads (J8)."
            fi
            ;;
    esac
}

confirm_new_firmware() {
    step "Starting the new firmware and checking that it answers"
    radio_restart
    if probe_radio "$FIRMWARE_PROTOCOL" 8; then
        describe_probe_result
        return 0
    fi
    describe_probe_result
    fail "The firmware was written and verified, but it does not answer on $RADIO_PORT.
Check the UART wiring (GPIO8 -> DIO12, GPIO9 <- DIO13) and that nothing else uses the port."
}

print_next_steps() {
    step "Done"
    if [ "$DRY_RUN" -eq 1 ]; then
        say "Dry run finished. No GPIO was driven and nothing was written to the radio."
        return 0
    fi
    if [ "$FIRMWARE_KIND" = "zigbee" ]; then
        cat <<NEXT
SUCCESS: the radio runs the Zigbee coordinator firmware $ZIGBEE_REVISION.

Home Assistant ZHA:
  Settings -> Devices & services -> Add integration -> Zigbee Home Automation
  Radio type: ZNP (Texas Instruments Z-Stack)   Serial device path: $RADIO_PORT
  Port speed: 115200                            Data flow control: none

Zigbee2MQTT (configuration.yaml):
  serial:
    port: $RADIO_PORT
    adapter: zstack
NEXT
    else
        cat <<NEXT
SUCCESS: the radio runs the OpenThread RCP firmware 2025.3.1.

Home Assistant OpenThread Border Router app:
  Device: $RADIO_PORT   Baudrate: 460800   Hardware flow control: off
NEXT
    fi
}

main() {
    parse_arguments "$@"
    select_firmware
    require_root
    choose_where_to_run
    trap remove_work_dir_and_release_gpios EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    install_basic_tools
    prepare_work_dir
    write_helper_programs
    fetch_downloads
    inspect_firmware
    locate_radio_port
    refuse_if_port_is_busy
    select_gpio_backend
    report_current_firmware
    if [ "$PROBE_ONLY" -eq 1 ]; then
        exit 0
    fi
    if [ "$FORCE" -eq 0 ] && wanted_firmware_is_already_there; then
        say "The wanted firmware is already installed. Use --force to write it again."
        print_next_steps
        exit 0
    fi
    write_firmware
    confirm_new_firmware
    print_next_steps
}

main "$@"
