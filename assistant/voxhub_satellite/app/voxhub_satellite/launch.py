from __future__ import annotations

import argparse
import logging
import math
import os
import re
import shlex
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, fields
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

LVA_DIR = Path(os.environ.get("VOXHUB_LVA_DIR", "/app"))
CARD_PATTERNS = ("soc_sound", "googlevoicehat", "voicehat", "voxhub")
WAKE_WORD = re.compile(r"^[a-z0-9_.-]+$")

Runner = Callable[[Sequence[str]], str]


@dataclass
class Settings:
    name: str = "VoxHub"
    wake_word: str = "okay_nabu"
    mic_gain: float = 4.0
    mic_auto_gain: int = 0
    mic_noise_suppression: int = 0
    volume_percent: int = 100
    port: int = 6053
    peripheral_port: int = 6055
    preferences_file: str = "/data/preferences.json"
    download_dir: str = "/data/downloads"
    input_device: str = ""
    output_device: str = ""
    thinking_sound: bool = False
    debug: bool = False
    extra: list[str] = field(default_factory=list)

    def validate(self) -> Settings:
        self.name = self.name.strip() or "VoxHub"
        if not WAKE_WORD.match(self.wake_word):
            raise ValueError(f"invalid wake word id: {self.wake_word!r}")
        if not 0.1 <= self.mic_gain <= 16:
            raise ValueError("mic_gain must be between 0.1 and 16")
        if not 0 <= self.mic_auto_gain <= 31:
            raise ValueError("mic_auto_gain must be between 0 and 31")
        if not 0 <= self.mic_noise_suppression <= 4:
            raise ValueError("mic_noise_suppression must be between 0 and 4")
        if not 1 <= self.volume_percent <= 150:
            raise ValueError("volume_percent must be between 1 and 150")
        return self


def run_command(argv: Sequence[str]) -> str:
    result = subprocess.run(list(argv), capture_output=True, text=True, timeout=15, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{argv[0]} failed: {result.stderr.strip() or result.returncode}")
    return result.stdout


def list_names(output: str) -> list[str]:
    names = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip():
            names.append(parts[1].strip())
    return names


def pick(names: Iterable[str], kind: str) -> str:
    candidates = [name for name in names if not name.endswith(".monitor")]
    for pattern in CARD_PATTERNS:
        for name in candidates:
            if pattern in name.lower():
                return name
    found = ", ".join(candidates) or "none"
    raise LookupError(f"no {kind} of the VoxHub sound card (googlevoicehat) found among: {found}")


def find_devices(runner: Runner = run_command) -> tuple[str, str]:
    source = pick(list_names(runner(["pactl", "list", "short", "sources"])), "microphone source")
    sink = pick(list_names(runner(["pactl", "list", "short", "sinks"])), "speaker sink")
    return source, sink


def wait_for_audio(runner: Runner = run_command, attempts: int = 60, delay: float = 1.0) -> tuple[str, str]:
    error: Exception | None = None
    for _ in range(attempts):
        try:
            return find_devices(runner)
        except (RuntimeError, LookupError, OSError, subprocess.TimeoutExpired) as err:
            error = err
            time.sleep(delay)
    raise RuntimeError(f"the sound card did not appear in the audio server: {error}")


def gain_db(factor: float) -> str:
    return f"{20 * math.log10(factor):+.2f}dB"


def apply_levels(settings: Settings, source: str, sink: str, runner: Runner = run_command) -> None:
    runner(["pactl", "set-source-volume", source, gain_db(settings.mic_gain)])
    runner(["pactl", "set-sink-volume", sink, f"{settings.volume_percent}%"])
    for command in (["pactl", "set-source-mute", source, "0"], ["pactl", "set-sink-mute", sink, "0"]):
        try:
            runner(command)
        except RuntimeError as err:
            _LOGGER.debug("%s", err)


def lva_command(settings: Settings, source: str, sink: str, python: str = "") -> list[str]:
    argv = [
        python or str(LVA_DIR / ".venv" / "bin" / "python3"),
        "-m",
        "linux_voice_assistant",
        "--name",
        settings.name,
        "--wake-model",
        settings.wake_word,
        "--audio-input-device",
        source,
        "--audio-output-device",
        f"pulse/{sink}",
        "--audio-input-channels",
        "1",
        "--mic-volume",
        "100",
        "--port",
        str(settings.port),
        "--peripheral-host",
        "127.0.0.1",
        "--peripheral-port",
        str(settings.peripheral_port),
        "--preferences-file",
        settings.preferences_file,
        "--download-dir",
        settings.download_dir,
    ]
    if settings.mic_auto_gain:
        argv += ["--mic-auto-gain", str(settings.mic_auto_gain)]
    if settings.mic_noise_suppression:
        argv += ["--mic-noise-suppression", str(settings.mic_noise_suppression)]
    if settings.thinking_sound:
        argv.append("--enable-thinking-sound")
    if settings.debug:
        argv.append("--debug")
    return argv + list(settings.extra)


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        parts = shlex.split(value) if value.strip() else [""]
        values[key.strip()] = parts[0] if parts else ""
    return values


ENV_KEYS = {
    "VOXHUB_NAME": "name",
    "VOXHUB_WAKE_WORD": "wake_word",
    "VOXHUB_MIC_GAIN": "mic_gain",
    "VOXHUB_MIC_AUTO_GAIN": "mic_auto_gain",
    "VOXHUB_MIC_NOISE_SUPPRESSION": "mic_noise_suppression",
    "VOXHUB_VOLUME_PERCENT": "volume_percent",
    "VOXHUB_PREFERENCES_FILE": "preferences_file",
    "VOXHUB_DOWNLOAD_DIR": "download_dir",
    "VOXHUB_THINKING_SOUND": "thinking_sound",
    "VOXHUB_DEBUG": "debug",
}


def settings_from_env(values: dict[str, str]) -> Settings:
    settings = Settings()
    types = {item.name: item.type for item in fields(Settings)}
    for key, attribute in ENV_KEYS.items():
        if key not in values or values[key] == "":
            continue
        raw = values[key]
        kind = types[attribute]
        if kind in ("bool", bool):
            setattr(settings, attribute, raw.strip().lower() in ("1", "true", "yes", "on"))
        elif kind in ("int", int):
            setattr(settings, attribute, int(raw))
        elif kind in ("float", float):
            setattr(settings, attribute, float(raw))
        else:
            setattr(settings, attribute, raw)
    return settings.validate()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voxhub-lva")
    parser.add_argument("--env-file", default="/etc/voxhub/satellite.env")
    parser.add_argument("--python", default="")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = settings_from_env(read_env_file(Path(args.env_file)))
    source, sink = wait_for_audio()
    apply_levels(settings, source, sink)
    command = lva_command(settings, source, sink, args.python)
    _LOGGER.info("Microphone %s, speaker %s, starting: %s", source, sink, shlex.join(command))
    if args.print:
        print(shlex.join(command))
        return 0
    os.chdir(LVA_DIR)
    os.execv(command[0], command)
    return 1


if __name__ == "__main__":
    sys.exit(main())
