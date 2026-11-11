"""Add-on configuration: parsed from /data/options.json (written by the Supervisor)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

OPTIONS_PATH = Path("/data/options.json")

# Fast and cheap: the right default for a low-latency voice loop.
DEFAULT_MODEL = "claude-haiku-5-5"
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
WAKE_ENGINES = ("wyoming", "local")

DEFAULT_EXPOSED_DOMAINS = [
    "light", "switch", "fan", "cover", "climate", "media_player", "scene", "script",
    "sensor", "binary_sensor", "weather", "input_boolean", "input_number", "input_select",
    "vacuum", "humidifier", "person", "sun", "lock",
]  # fmt: skip
DEFAULT_ALLOWED_SERVICE_DOMAINS = [
    "light", "switch", "fan", "cover", "climate", "media_player", "scene", "script",
    "input_boolean", "input_number", "input_select", "vacuum", "humidifier",
]  # fmt: skip
DEFAULT_DENIED_SERVICE_DOMAINS = [
    "lock", "alarm_control_panel", "homeassistant", "hassio", "shell_command",
    "python_script", "pyscript", "backup", "recorder", "system_log", "persistent_notification",
]  # fmt: skip


class ConfigError(ValueError):
    """Raised for invalid add-on options."""


@dataclass
class Config:
    # Claude
    anthropic_api_key: str = field(default="", repr=False)  # never logged
    model: str = DEFAULT_MODEL
    custom_model: str = ""  # overrides `model` when set
    effort: str = "low"
    max_tokens: int = 2048
    request_timeout: float = 30.0
    assistant_name: str = "Jarvis"
    language: str = "en"
    system_prompt_extra: str = ""
    conversation_timeout: float = 300.0
    max_history_turns: int = 6
    # Wake word
    wake_word_engine: str = "wyoming"
    wake_word: str = "hey_jarvis"
    wake_word_uri: str = "tcp://core-openwakeword:10400"
    wake_word_threshold: float = 0.5
    wake_sound: bool = True
    # Speech services
    stt_uri: str = "tcp://core-whisper:10300"
    tts_uri: str = "tcp://core-piper:10200"
    tts_voice: str = ""
    # Audio
    input_device: str = ""
    output_device: str = ""
    mic_command: str = ""
    speaker_command: str = ""
    mic_gain: float = 1.0
    volume: float = 0.7
    # End-pointing
    silence_seconds: float = 0.8
    max_utterance_seconds: float = 15.0
    no_speech_timeout: float = 6.0
    vad_sensitivity: float = 2.5
    follow_up: bool = False
    follow_up_seconds: float = 5.0
    # Home Assistant access
    exposed_domains: list[str] = field(default_factory=lambda: list(DEFAULT_EXPOSED_DOMAINS))
    allowed_service_domains: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_SERVICE_DOMAINS))
    denied_service_domains: list[str] = field(default_factory=lambda: list(DEFAULT_DENIED_SERVICE_DOMAINS))
    # Hardware extras (fail-soft)
    leds: bool = True
    mute_switch: bool = True
    log_level: str = "info"

    @property
    def effective_model(self) -> str:
        return self.custom_model.strip() or self.model

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> Config:
        """Build a Config from the Supervisor options dict. Unknown keys are ignored."""
        cfg = cls()
        for f in fields(cls):
            if f.name not in options or options[f.name] is None:
                continue
            default = getattr(cfg, f.name)
            setattr(cfg, f.name, _coerce(f.name, options[f.name], default))
        cfg.validate()
        return cfg

    @classmethod
    def load(cls, path: Path = OPTIONS_PATH) -> Config:
        try:
            options = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            options = {}
        except json.JSONDecodeError as err:
            raise ConfigError(f"{path} is not valid JSON: {err}") from err
        if not isinstance(options, dict):
            raise ConfigError(f"{path} must contain a JSON object")
        return cls.from_options(options)

    def validate(self) -> None:
        if self.effort not in EFFORT_LEVELS:
            raise ConfigError(f"effort must be one of {EFFORT_LEVELS}")
        if self.wake_word_engine not in WAKE_ENGINES:
            raise ConfigError(f"wake_word_engine must be one of {WAKE_ENGINES}")
        _check_range("volume", self.volume, 0.0, 1.0)
        _check_range("mic_gain", self.mic_gain, 0.1, 64.0)
        _check_range("wake_word_threshold", self.wake_word_threshold, 0.05, 1.0)
        _check_range("silence_seconds", self.silence_seconds, 0.2, 5.0)
        _check_range("max_utterance_seconds", self.max_utterance_seconds, 2.0, 60.0)
        _check_range("vad_sensitivity", self.vad_sensitivity, 1.1, 20.0)
        _check_range("max_tokens", self.max_tokens, 256, 32000)
        _check_range("max_history_turns", self.max_history_turns, 0, 50)
        if not any(d.strip() for d in self.exposed_domains):
            self.exposed_domains = list(DEFAULT_EXPOSED_DOMAINS)
        for name in ("exposed_domains", "allowed_service_domains", "denied_service_domains"):
            setattr(self, name, sorted({d.strip().lower() for d in getattr(self, name) if d.strip()}))

    def require_api_key(self) -> None:
        if not self.anthropic_api_key.strip():
            raise ConfigError("anthropic_api_key is not set in the add-on configuration")


def _coerce(name: str, value: Any, default: Any) -> Any:
    try:
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        if isinstance(default, int):
            return int(value)
        if isinstance(default, float):
            return float(value)
        if isinstance(default, list):
            if isinstance(value, str):
                value = value.split(",")
            return [str(v) for v in value]
        return str(value)
    except (TypeError, ValueError) as err:
        raise ConfigError(f"invalid value for {name}: {value!r}") from err


def _check_range(name: str, value: float, low: float, high: float) -> None:
    if not low <= value <= high:
        raise ConfigError(f"{name} must be between {low} and {high} (got {value})")
