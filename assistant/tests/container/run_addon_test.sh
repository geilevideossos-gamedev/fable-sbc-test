#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADDON="$HERE/../../voxhub_satellite"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/voxhub-addon-test.XXXXXX")"
NAME="voxhub-addon-test-$$"
PULSE_IMAGE="${VOXHUB_PULSE_IMAGE:-voxhub-pulse:test}"

cleanup() {
    docker rm -f "$NAME-addon" "$NAME-pulse" >/dev/null 2>&1 || true
    docker network rm "$NAME" >/dev/null 2>&1 || true
    docker volume rm "$NAME-audio" >/dev/null 2>&1 || true
    rm -rf "$WORK"
}
trap cleanup EXIT

if ! docker image inspect "$PULSE_IMAGE" >/dev/null 2>&1; then
    docker build -q -t "$PULSE_IMAGE" "$HERE/pulse" >/dev/null
fi
docker build -q --build-arg BUILD_FROM=ghcr.io/ohf-voice/linux-voice-assistant:1.1.18 \
    --build-arg BUILD_ARCH=amd64 --build-arg BUILD_VERSION=test -t voxhub-satellite:test "$ADDON" >/dev/null
mkdir -p "$WORK/data" "$WORK/leds/voxhub-green" "$WORK/leds/voxhub-blue"
echo 0 >"$WORK/leds/voxhub-green/brightness"
echo 0 >"$WORK/leds/voxhub-blue/brightness"
chmod -R a+rwX "$WORK"
cat >"$WORK/data/options.json" <<'JSON'
{"name": "VoxHub Test", "wake_word": "okay_nabu", "mic_gain": 4.0, "mic_auto_gain": 0, "mic_noise_suppression": 0,
 "volume_percent": 100, "thinking_sound": false, "leds": true, "mute_switch": true, "guard": false,
 "protected_domains": ["lock", "alarm_control_panel"], "guard_interval": 300, "log_level": "info"}
JSON

docker network create "$NAME" >/dev/null
docker volume create "$NAME-audio" >/dev/null
docker run -d --name "$NAME-pulse" --network "$NAME" -v "$NAME-audio:/run/audio" "$PULSE_IMAGE" \
    pulseaudio --daemonize=no --exit-idle-time=-1 --disallow-exit -n --log-target=stderr \
    -L "module-native-protocol-unix socket=/run/audio/pulse.sock auth-anonymous=1" \
    -L "module-null-sink sink_name=alsa_output.platform-soc_sound.stereo-fallback" \
    -L "module-null-source source_name=alsa_input.platform-soc_sound.stereo-fallback" \
    -L "module-null-sink sink_name=alsa_output.platform-fef00700.hdmi.hdmi-stereo" >/dev/null
docker run -d --name "$NAME-addon" --network "$NAME" -v "$NAME-audio:/run/audio" -v "$WORK/data:/data" \
    -v "$WORK/leds:/leds" -e VOXHUB_LED_ROOT=/leds -e PULSE_SERVER=unix:/run/audio/pulse.sock \
    voxhub-satellite:test >/dev/null

for _ in $(seq 1 60); do
    docker logs "$NAME-addon" 2>&1 | grep -q "Connected to the voice satellite" && break
    sleep 1
done
docker logs "$NAME-addon" 2>&1 | sed -n '1,40p'
STATUS=0
docker logs "$NAME-addon" 2>&1 | grep -q "Server started (host=127.0.0.1, port=6053)" || { echo "FAIL  LVA does not listen on 127.0.0.1"; STATUS=1; }
docker run --rm --network "container:$NAME-addon" -v "$HERE/esphome_client.py:/test/esphome_client.py:ro" -v "$WORK/leds:/leds" \
    --entrypoint /app/.venv/bin/python3 voxhub-satellite:test /test/esphome_client.py 127.0.0.1 /leds || STATUS=$?
level() {
    docker exec -e PULSE_SERVER=unix:/run/audio/pulse.sock "$NAME-pulse" pactl get-source-volume alsa_input.platform-soc_sound.stereo-fallback
}
level | grep -q "12.04 dB" || { echo "FAIL  microphone gain after the first start"; STATUS=1; }
docker restart "$NAME-addon" >/dev/null
for _ in $(seq 1 60); do
    [ "$(docker logs "$NAME-addon" 2>&1 | grep -c "Connected to the voice satellite")" -ge 2 ] && break
    sleep 1
done
level | grep -q "12.04 dB" && echo "PASS  microphone gain still +12.04 dB after a restart" || { echo "FAIL  microphone gain changed after a restart"; STATUS=1; }
echo "--- add-on log after the test"
docker logs "$NAME-addon" 2>&1 | tail -n 25
echo "--- levels set by the launcher"
docker exec -e PULSE_SERVER=unix:/run/audio/pulse.sock "$NAME-pulse" pactl get-source-volume alsa_input.platform-soc_sound.stereo-fallback
docker exec -e PULSE_SERVER=unix:/run/audio/pulse.sock "$NAME-pulse" pactl get-sink-volume alsa_output.platform-soc_sound.stereo-fallback
exit "$STATUS"
