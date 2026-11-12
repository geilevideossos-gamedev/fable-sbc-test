import json

import pytest
import yaml

from voxhub_satellite.__main__ import Options
from voxhub_satellite.hubwatch import HubWatch, ruleset, set_hub_addresses
from voxhub_satellite.launch import (
    Settings,
    apply_levels,
    find_devices,
    gain_db,
    list_names,
    lva_command,
    pick,
    read_env_file,
    settings_from_env,
    wait_for_audio,
)

SOURCES = (
    "0\talsa_output.platform-soc_sound.stereo-fallback.monitor\tPipeWire\ts32le 2ch 48000Hz\tSUSPENDED\n"
    "1\talsa_input.platform-soc_sound.stereo-fallback\tPipeWire\ts32le 2ch 48000Hz\tSUSPENDED\n"
    "2\talsa_input.platform-fe00b840.mailbox.stereo-fallback\tPipeWire\ts16le 2ch 48000Hz\tSUSPENDED\n"
)
SINKS = (
    "0\talsa_output.platform-fef00700.hdmi.hdmi-stereo\tPipeWire\ts32le 2ch 48000Hz\tSUSPENDED\n"
    "1\talsa_output.platform-soc_sound.stereo-fallback\tPipeWire\ts32le 2ch 48000Hz\tSUSPENDED\n"
)


class Pactl:
    def __init__(self, sources=SOURCES, sinks=SINKS, fail=0):
        self.sources = sources
        self.sinks = sinks
        self.fail = fail
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        if self.fail:
            self.fail -= 1
            raise RuntimeError("pactl failed: Connection refused")
        if argv[:4] == ["pactl", "list", "short", "sources"]:
            return self.sources
        if argv[:4] == ["pactl", "list", "short", "sinks"]:
            return self.sinks
        return ""


def test_device_detection():
    assert list_names(SOURCES)[1] == "alsa_input.platform-soc_sound.stereo-fallback"
    assert find_devices(Pactl()) == (
        "alsa_input.platform-soc_sound.stereo-fallback",
        "alsa_output.platform-soc_sound.stereo-fallback",
    )
    with pytest.raises(LookupError, match="googlevoicehat"):
        pick(["alsa_input.usb-mic"], "microphone source")


def test_wait_for_audio_retries(monkeypatch):
    monkeypatch.setattr("voxhub_satellite.launch.time.sleep", lambda seconds: None)
    pactl = Pactl(fail=3)
    assert wait_for_audio(pactl)[0].startswith("alsa_input.platform-soc_sound")
    with pytest.raises(RuntimeError, match="did not appear"):
        wait_for_audio(Pactl(sources="", sinks=""), attempts=2)


def test_levels():
    pactl = Pactl()
    apply_levels(Settings(mic_gain=4.0, volume_percent=90), "src", "snk", pactl)
    assert ["pactl", "set-source-volume", "src", "+12.04dB"] in pactl.calls
    assert gain_db(1.0) == "+0.00dB" and gain_db(0.5) == "-6.02dB"
    assert ["pactl", "set-sink-volume", "snk", "90%"] in pactl.calls


def test_lva_command():
    settings = Settings(name="VoxHub Downstairs", wake_word="hey_jarvis", mic_auto_gain=10, debug=True)
    argv = lva_command(settings, "src", "snk", "/venv/python")
    assert argv[:3] == ["/venv/python", "-m", "linux_voice_assistant"]
    pairs = dict(zip(argv[3::2], argv[4::2], strict=False))
    assert pairs["--name"] == "VoxHub Downstairs"
    assert pairs["--wake-model"] == "hey_jarvis"
    assert pairs["--audio-input-device"] == "src"
    assert pairs["--audio-output-device"] == "pulse/snk"
    assert pairs["--audio-input-channels"] == "1"
    assert pairs["--mic-volume"] == "100"
    assert pairs["--peripheral-host"] == "127.0.0.1"
    assert "--mic-auto-gain" in argv and "--debug" in argv
    assert "--mic-noise-suppression" not in argv


@pytest.mark.parametrize(
    "change",
    [{"wake_word": "Okay Nabu"}, {"mic_gain": 50}, {"mic_auto_gain": 40}, {"mic_noise_suppression": 9}],
)
def test_settings_validation(change):
    with pytest.raises(ValueError):
        Settings(**change).validate()


def test_env_file(tmp_path):
    path = tmp_path / "satellite.env"
    path.write_text(
        "VOXHUB_NAME='VoxHub Downstairs'\n"
        "VOXHUB_HUB=192.168.1.10\n"
        "VOXHUB_MIC_GAIN=6\n"
        "VOXHUB_THINKING_SOUND=yes\n"
        "VOXHUB_WAKE_WORD=\n"
        "# a line that is skipped\n"
        "garbage\n"
    )
    values = read_env_file(path)
    assert values["VOXHUB_NAME"] == "VoxHub Downstairs"
    settings = settings_from_env(values)
    assert settings.name == "VoxHub Downstairs"
    assert settings.mic_gain == 6.0
    assert settings.thinking_sound is True
    assert settings.wake_word == "okay_nabu"


def test_addon_options_match_config():
    with open("voxhub_satellite/config.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    options = Options.parse(config["options"])
    assert options.settings.name == config["options"]["name"]
    assert options.protected_domains == ["lock", "alarm_control_panel"]
    assert set(config["options"]) <= set(config["schema"])
    assert config["host_network"] is True and config["audio"] is True
    assert config["homeassistant_api"] is True
    with open("voxhub_satellite/translations/en.yaml", encoding="utf-8") as handle:
        translations = yaml.safe_load(handle)
    assert set(config["schema"]) == set(translations["configuration"])


def test_addon_options_defaults_and_guard_off():
    options = Options.parse({})
    assert options.settings.name == "VoxHub Hub"
    assert options.guard is True
    assert options.protected_domains == ["lock", "alarm_control_panel"]
    assert Options.parse({"guard": False, "protected_domains": []}).protected_domains == []


def test_addon_options_file(tmp_path):
    path = tmp_path / "options.json"
    path.write_text(json.dumps({"name": "Hub", "wake_word": "alexa", "log_level": "debug"}))
    options = Options.load(path)
    assert options.settings.wake_word == "alexa" and options.settings.debug
    path.write_text("[]")
    with pytest.raises(ValueError):
        Options.load(path)


def test_firewall_ruleset():
    text = ruleset()
    assert "tcp dport 6053 ip saddr @hub4 accept" in text
    assert "tcp dport 6053 drop" in text
    assert 'tcp dport 6055 iifname != "lo" drop' in text


class Nft:
    def __init__(self):
        self.calls = []

    def __call__(self, argv, stdin=""):
        self.calls.append((list(argv), stdin))
        if argv[:2] == ["delete", "table"]:
            raise RuntimeError("no such table")


def test_hub_watch(tmp_path):
    nft = Nft()
    answers = iter([True, True, False])
    watch = HubWatch(
        "homeassistant.local",
        runner=nft,
        resolver=lambda host: ["192.168.1.10"],
        prober=lambda url: next(answers),
        status_file=tmp_path / "hub.json",
    )
    watch.start()
    watch.step()
    watch.step()
    watch.step()
    assert nft.calls[1][0] == ["-f", "-"] and "hub4" in nft.calls[1][1]
    adds = [call for call, _ in nft.calls if call[:2] == ["add", "element"]]
    assert adds == [["add", "element", "inet", "voxhub", "hub4", "{ 192.168.1.10 }"]]
    assert json.loads((tmp_path / "hub.json").read_text())["reachable"] is False


def test_hub_watch_without_firewall(tmp_path):
    nft = Nft()
    watch = HubWatch("10.0.0.2", firewall=False, runner=nft, prober=lambda url: True, status_file=None)
    watch.start()
    watch.step()
    assert nft.calls == []
    assert watch.addresses == ["10.0.0.2"] and watch.reachable


def test_set_hub_addresses_empty():
    nft = Nft()
    set_hub_addresses([], nft)
    assert nft.calls == [(["flush", "set", "inet", "voxhub", "hub4"], "")]
