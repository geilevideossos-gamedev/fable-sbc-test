#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../flash_zigbee.sh"
SIM="$HERE/radio_sim.py"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-flash-tests.XXXXXX")"
PASSED=0
FAILED=0
SIM_PID=""

cleanup() {
    [ -n "$SIM_PID" ] && kill "$SIM_PID" 2>/dev/null
    [ "${KEEP:-0}" = 1 ] || rm -rf "$WORK"
}
trap cleanup EXIT

source <(sed -n '/^ZIGBEE_NAME=/,/^)$/p; /^ROUTER_NAME=/,/^)$/p; /^THREAD_NAME=/,/^)$/p' "$SCRIPT")

fetch_image() {
    local name="$1" hex_sha="$2" url="$3" zip_sha="$4"
    curl -fsSL --retry 3 -o "$WORK/$name.zip" "$url" || return 1
    [ "$(sha256sum "$WORK/$name.zip" | cut -d ' ' -f 1)" = "$zip_sha" ] || return 1
    python3 -c 'import sys, zipfile; z = zipfile.ZipFile(sys.argv[1]); open(sys.argv[3], "wb").write(z.read(sys.argv[2]))' \
        "$WORK/$name.zip" "$name.hex" "$WORK/$name.hex" || return 1
    [ "$(sha256sum "$WORK/$name.hex" | cut -d ' ' -f 1)" = "$hex_sha" ]
}

fetch_image "$ZIGBEE_NAME" "$ZIGBEE_HEX_SHA256" "${ZIGBEE_SOURCES[0]}" "${ZIGBEE_SOURCES[1]}" || { echo "cannot fetch $ZIGBEE_NAME"; exit 2; }
fetch_image "$ROUTER_NAME" "$ROUTER_HEX_SHA256" "${ROUTER_SOURCES[0]}" "${ROUTER_SOURCES[1]}" || { echo "cannot fetch $ROUTER_NAME"; exit 2; }
fetch_image "$THREAD_NAME" "$THREAD_HEX_SHA256" "${THREAD_SOURCES[0]}" "${THREAD_SOURCES[1]}" || { echo "cannot fetch $THREAD_NAME"; exit 2; }

start_sim() {
    local initial="$1"
    [ -n "$SIM_PID" ] && kill "$SIM_PID" 2>/dev/null
    rm -rf "$WORK/gpio" "$WORK/port" "$WORK/state.json"
    mkdir -p "$WORK/gpio"
    python3 "$SIM" --gpio-dir "$WORK/gpio" --port-file "$WORK/port" --state-file "$WORK/state.json" \
        --image "coordinator=$WORK/$ZIGBEE_NAME.hex" --image "router=$WORK/$ROUTER_NAME.hex" \
        --image "thread=$WORK/$THREAD_NAME.hex" --initial "$initial" 2>>"$WORK/sim.log" &
    SIM_PID=$!
    local tries=0
    until [ -s "$WORK/port" ] && [ -s "$WORK/state.json" ]; do
        sleep 0.1
        tries=$((tries + 1))
        [ "$tries" -lt 100 ] || { echo "simulator did not start"; exit 2; }
    done
}

run_script() {
    local log="$1"
    shift
    VOXHUB_GPIO_SIM_DIR="$WORK/gpio" VOXHUB_RADIO_PORT="$(cat "$WORK/port")" \
        VOXHUB_SATELLITE_MARKER="${MARKER:-$WORK/no-marker}" \
        timeout 900 bash "$SCRIPT" "$@" >"$log" 2>&1
}

state() {
    python3 -c 'import json, sys; s = json.load(open(sys.argv[1])); print(s[sys.argv[2]] if sys.argv[2] != "writes" else sum(e in ("bank-erase", "write", "sector-erase") for e in s["events"]))' "$WORK/state.json" "$1"
}

has_event() {
    python3 -c 'import json, sys; sys.exit(0 if sys.argv[2] in json.load(open(sys.argv[1]))["events"] else 1)' "$WORK/state.json" "$1"
}

check() {
    local name="$1" condition="$2"
    if eval "$condition"; then
        PASSED=$((PASSED + 1))
        printf 'PASS  %s\n' "$name"
    else
        FAILED=$((FAILED + 1))
        printf 'FAIL  %s  (%s)\n' "$name" "$condition"
    fi
}

case_run() {
    local id="$1" initial="$2"
    shift 2
    start_sim "$initial"
    LOG="$WORK/$id.log"
    STATUS=0
    run_script "$LOG" "$@" || STATUS=$?
    sleep 0.3
}

case_run hub-blank blank --role hub
check "hub, blank radio: exit 0" '[ "$STATUS" -eq 0 ]'
check "hub, blank radio: coordinator in flash" '[ "$(state firmware)" = coordinator ]'
check "hub, blank radio: SUCCESS line" 'grep -q "^SUCCESS: the radio runs the Zigbee coordinator firmware 20250321." "$LOG"'
check "hub, blank radio: role line" 'grep -q "^Role: hub (option)" "$LOG"'

case_run hub-installed coordinator
check "hub default role, coordinator installed: exit 0" '[ "$STATUS" -eq 0 ]'
check "hub default role: role line" 'grep -q "^Role: hub (default)" "$LOG"'
check "hub, coordinator installed: nothing written" '[ "$(state writes)" -eq 0 ]'
check "hub, coordinator installed: already installed" 'grep -q "The wanted firmware is already installed" "$LOG"'

case_run sat-blank blank --role satellite
check "satellite, blank radio: exit 0" '[ "$STATUS" -eq 0 ]'
check "satellite, blank radio: router in flash" '[ "$(state firmware)" = router ]'
check "satellite, blank radio: firmware running" '[ "$(state mode)" = firmware:router ]'
check "satellite, blank radio: SUCCESS line" 'grep -q "^SUCCESS: the radio runs the Zigbee router firmware 20250403 (role: satellite)." "$LOG"'
check "satellite, blank radio: silent after start" 'grep -q "The radio is silent on the serial port, as expected" "$LOG"'
check "satellite, blank radio: checksum confirmed" 'grep -q "Verified (match" "$LOG"'

case_run sat-installed router --role satellite
check "satellite, router installed: exit 0" '[ "$STATUS" -eq 0 ]'
check "satellite, router installed: nothing written" '[ "$(state writes)" -eq 0 ]'
check "satellite, router installed: bootloader compared" 'grep -q "The flash holds exactly $ROUTER_NAME." "$LOG"'
check "satellite, router installed: already installed" 'grep -q "The wanted firmware is already installed" "$LOG"'
check "satellite, router installed: radio runs again" '[ "$(state mode)" = firmware:router ]'

case_run sat-over-coordinator coordinator --role satellite
check "satellite over coordinator: exit 0" '[ "$STATUS" -eq 0 ]'
check "satellite over coordinator: router in flash" '[ "$(state firmware)" = router ]'

MARKER="$WORK/satellite.env"
touch "$MARKER"
case_run sat-auto blank
check "auto role on the satellite image: exit 0" '[ "$STATUS" -eq 0 ]'
check "auto role on the satellite image: role line" 'grep -q "^Role: satellite (this system is a VoxHub satellite" "$LOG"'
check "auto role on the satellite image: router in flash" '[ "$(state firmware)" = router ]'
unset MARKER

case_run sat-rejoin router --role satellite --rejoin
check "rejoin: exit 0" '[ "$STATUS" -eq 0 ]'
check "rejoin: button click seen by the radio" 'has_event router-button'
check "rejoin: nothing written" '[ "$(state writes)" -eq 0 ]'
check "rejoin: radio runs the router again" '[ "$(state mode)" = firmware:router ]'

case_run sat-rejoin-coordinator coordinator --role satellite --rejoin
check "rejoin on a coordinator: refused" '[ "$STATUS" -ne 0 ] && grep -q "it does not run the router firmware" "$LOG"'
check "rejoin on a coordinator: no click" '! has_event router-button'

case_run sat-thread blank --role satellite --thread
check "satellite + thread: refused" '[ "$STATUS" -ne 0 ] && grep -q "only for the hub" "$LOG"'

case_run hub-rejoin coordinator --role hub --rejoin
check "hub + rejoin: refused" '[ "$STATUS" -ne 0 ] && grep -q "only works with the router firmware" "$LOG"'

case_run bad-role blank --role kitchen
check "unknown role: refused" '[ "$STATUS" -ne 0 ] && grep -q "must be hub or satellite" "$LOG"'

start_sim coordinator
LOG="$WORK/guard.log"
STATUS=0
SUPERVISOR_TOKEN=test run_script "$LOG" --role satellite || STATUS=$?
check "router on Home Assistant OS: refused" '[ "$STATUS" -ne 0 ] && grep -q "This system runs Home Assistant OS, so it is the hub" "$LOG"'
check "router on Home Assistant OS: radio untouched" '[ "$(state firmware)" = coordinator ] && [ "$(state writes)" -eq 0 ]'
LOG="$WORK/guard-force.log"
STATUS=0
SUPERVISOR_TOKEN=test run_script "$LOG" --role satellite --force || STATUS=$?
check "router on Home Assistant OS with --force: written" '[ "$STATUS" -eq 0 ] && [ "$(state firmware)" = router ]'

case_run sat-force router --role satellite --force
check "satellite --force over router: rewritten" '[ "$STATUS" -eq 0 ] && [ "$(state writes)" -gt 0 ] && [ "$(state firmware)" = router ]'

case_run sat-dry blank --role satellite --dry-run
check "satellite dry run: exit 0" '[ "$STATUS" -eq 0 ]'
check "satellite dry run: final line" 'grep -q "Dry run finished. No GPIO was driven and nothing was written to the radio." "$LOG"'
check "satellite dry run: radio untouched" '[ "$(state writes)" -eq 0 ] && [ "$(cat "$WORK/gpio/gpio25")" = 1 ] && [ "$(cat "$WORK/gpio/gpio24")" = 0 ]'
check "satellite dry run: router hex checked" 'grep -q "$ROUTER_NAME.hex SHA256 matches: $ROUTER_HEX_SHA256" "$LOG"'
check "satellite dry run: backdoor checked" 'grep -q "OK: this image keeps the serial bootloader reachable through DIO15" "$LOG"'

case_run sat-probe router --role satellite --probe-only
check "probe-only on a router: exit 0" '[ "$STATUS" -eq 0 ]'
check "probe-only on a router: hint" 'grep -q "A Zigbee router firmware is silent on the serial port" "$LOG"'
check "probe-only on a router: nothing written" '[ "$(state writes)" -eq 0 ]'

case_run hub-thread blank --role hub --thread
check "hub thread: exit 0" '[ "$STATUS" -eq 0 ]'
check "hub thread: RCP in flash" '[ "$(state firmware)" = thread ]'
check "hub thread: SUCCESS line" 'grep -q "^SUCCESS: the radio runs the OpenThread RCP firmware 2025.3.1." "$LOG"'

case_run hub-over-router router --role hub
check "hub over router: coordinator in flash" '[ "$STATUS" -eq 0 ] && [ "$(state firmware)" = coordinator ]'

mkdir -p "$WORK/cache"
cp "$WORK/$ROUTER_NAME.zip" "$WORK/cache/${ROUTER_SOURCES[1]}"
start_sim blank
LOG="$WORK/cache.log"
STATUS=0
VOXHUB_RADIO_CACHE="$WORK/cache" run_script "$LOG" --role satellite --dry-run || STATUS=$?
check "local firmware copy: used" '[ "$STATUS" -eq 0 ] && grep -q "from the local copy $WORK/cache/${ROUTER_SOURCES[1]}" "$LOG"'
printf 'corrupt\n' >"$WORK/cache/${ROUTER_SOURCES[1]}"
LOG="$WORK/cache-corrupt.log"
STATUS=0
VOXHUB_RADIO_CACHE="$WORK/cache" run_script "$LOG" --role satellite --dry-run || STATUS=$?
check "local firmware copy: a damaged copy is ignored" '[ "$STATUS" -eq 0 ] && ! grep -q "from the local copy" "$LOG" && grep -q "$ROUTER_HEX_SHA256" "$LOG"'

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
