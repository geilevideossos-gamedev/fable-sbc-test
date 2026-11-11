import json
from pathlib import Path

import pytest
import yaml

from voxhub_assistant.config import DEFAULT_MODEL, Config, ConfigError

ADDON = Path(__file__).parent.parent / "voxhub_assistant"


def test_defaults():
    cfg = Config.from_options({})
    assert cfg.model == DEFAULT_MODEL == "claude-haiku-5-5"
    assert cfg.effective_model == "claude-haiku-5-5"
    assert cfg.stt_uri == "tcp://core-whisper:10300"
    assert cfg.tts_uri == "tcp://core-piper:10200"
    assert "lock" in cfg.denied_service_domains
    assert "alarm_control_panel" in cfg.denied_service_domains
    assert "lock" not in cfg.allowed_service_domains


def test_coercion_and_unknown_keys():
    cfg = Config.from_options(
        {"volume": "0.5", "follow_up": "true", "max_tokens": "1024", "bogus": 1,
         "allowed_service_domains": [" Light ", "SWITCH", ""], "tts_voice": None}
    )  # fmt: skip
    assert cfg.volume == 0.5
    assert cfg.follow_up is True
    assert cfg.max_tokens == 1024
    assert cfg.allowed_service_domains == ["light", "switch"]
    assert cfg.tts_voice == ""


def test_custom_model_overrides():
    cfg = Config.from_options({"model": "claude-sonnet-5-5", "custom_model": " claude-opus-5-5 "})
    assert cfg.effective_model == "claude-opus-5-5"


def test_empty_exposed_domains_fall_back_to_defaults():
    assert "light" in Config.from_options({"exposed_domains": []}).exposed_domains


@pytest.mark.parametrize(
    "options",
    [{"volume": 1.5}, {"effort": "extreme"}, {"wake_word_engine": "cloud"},
     {"mic_gain": 0}, {"max_tokens": "lots"}],
)  # fmt: skip
def test_invalid_values_rejected(options):
    with pytest.raises(ConfigError):
        Config.from_options(options)


def test_api_key_required_and_not_in_repr():
    cfg = Config.from_options({})
    with pytest.raises(ConfigError):
        cfg.require_api_key()
    cfg = Config.from_options({"anthropic_api_key": "sk-ant-secret"})
    cfg.require_api_key()
    assert "sk-ant-secret" not in repr(cfg)


def test_load_from_file(tmp_path):
    path = tmp_path / "options.json"
    path.write_text(json.dumps({"wake_word": "ok_nabu"}))
    assert Config.load(path).wake_word == "ok_nabu"
    assert Config.load(tmp_path / "missing.json").wake_word == "hey_jarvis"
    path.write_text("{not json")
    with pytest.raises(ConfigError):
        Config.load(path)


def test_addon_config_yaml_is_consistent():
    """config.yaml parses, and its options/schema match what the code understands."""
    addon = yaml.safe_load((ADDON / "config.yaml").read_text())
    assert addon["slug"] == "voxhub_assistant"
    assert set(addon["arch"]) == {"aarch64", "amd64"}
    assert addon["audio"] is True and addon["homeassistant_api"] is True and addon["init"] is False
    known = set(Config.__dataclass_fields__)
    assert set(addon["options"]) <= set(addon["schema"])
    assert set(addon["schema"]) == known
    # The shipped defaults must load, and match the code defaults.
    cfg = Config.from_options(addon["options"])
    default = Config.from_options({})
    assert cfg == default
    translations = yaml.safe_load((ADDON / "translations" / "en.yaml").read_text())
    assert set(translations["configuration"]) == known


def test_other_yaml_files_parse():
    for name in ("build.yaml", "../repository.yaml"):
        assert isinstance(yaml.safe_load((ADDON / name).read_text()), dict)
