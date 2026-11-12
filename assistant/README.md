# VoxHub add-ons

This folder is the Home Assistant add-on repository of the VoxHub. It holds two add-ons:

| Add-on | Use it for | What it does |
|---|---|---|
| **VoxHub Satellite** (`voxhub_satellite/`) | **the two-device system (hub + satellite) - the default** | Makes the hub a voice satellite of its own Home Assistant, exactly like the satellite board downstairs: Linux Voice Assistant 1.1.18 (wake word on the device), status LEDs, mute switch. Every request goes through Home Assistant's Assist pipeline with the official Anthropic integration (Claude). It also runs the **exposure guard** that keeps locks and alarm panels away from Assist. |
| **VoxHub Assistant** (`voxhub_assistant/`) | a single VoxHub without the Assist pipeline | The self-contained assistant of revision A1/A2: wake word -> Whisper -> Claude with its own Home Assistant tools -> Piper. It does not serve satellites. Do not run it together with VoxHub Satellite. |

Why the two-device system uses Home Assistant's own pipeline instead of this add-on: `DECISIONS.md`, entries S-1 to
S-5. The satellite board itself runs the same satellite software from an SD card image: `os/satellite/`.

## VoxHub Satellite (hub side of the two-device system)

```
 Hub (Home Assistant OS)                                         Satellite (Raspberry Pi OS Lite)
 ┌────────────────────────────────────────────────────┐        ┌─────────────────────────────────┐
 │ VoxHub Satellite add-on                            │        │ voxhub-lva (Linux Voice Asst.)  │
 │  Linux Voice Assistant 1.1.18 ── ESPHome API :6053 ├──┐  ┌──┤ ESPHome API :6053 (hub only)    │
 │  bridge: LEDs + mute switch (peripheral API :6055) │  │  │  │ voxhub-peripherals: LEDs, mute  │
 │  exposure guard (websocket, admin)                 │  │  │  │ voxhub-hubwatch: firewall       │
 └────────────────────────────────────────────────────┘  │  │  └─────────────────────────────────┘
 Home Assistant Core                                      │  │
  ESPHome integration <───────────────────────────────────┘──┘
  Assist pipeline "VoxHub Claude": Whisper -> Anthropic (Claude, Assist API) -> Piper
  device area of each satellite -> "You are in area ..." in Claude's prompt
```

| Topic | How it works |
|---|---|
| Wake word | microWakeWord in Linux Voice Assistant on each device ("Okay Nabu" by default; it is also trained for German) |
| Speech to text, text to speech | Whisper and Piper add-ons on the hub |
| Conversation | the Anthropic integration (Claude) with the "Assist" API: intent tools, live context, exposed scripts |
| Room | the area of the satellite device in Home Assistant. For every request Claude reads "You are in area X ... generic commands like 'turn on the lights' should target this area." |
| Answer | Home Assistant sends the answer to the satellite that asked; it plays it from `http://<hub>:8123` |
| Locks and alarms | never exposed to Assist: the exposure guard un-exposes `lock.*`, `alarm_control_panel.*` and every scene, group or script that controls one, at start, on every registry change and every 5 minutes |
| LEDs | green = ready, blue = listening, blinking blue = thinking, green + blue = speaking, off = muted, slow green blinking = no connection to Home Assistant |
| Mute switch | cuts the microphone data in hardware; the bridge also mutes the satellite in Home Assistant |

Setup, step by step: `fab/ASSEMBLY_AND_TEST.md`, chapter 7. Options: `voxhub_satellite/DOCS.md`.

Code (`voxhub_satellite/app/voxhub_satellite/`, shared with the satellite image):

| File | Contents |
|---|---|
| `__main__.py` | add-on entry point: options, sound card, Linux Voice Assistant, bridge, guard |
| `launch.py` | finds the googlevoicehat source and sink with `pactl`, sets the microphone gain in dB, builds the Linux Voice Assistant command line; `python -m voxhub_satellite.launch` on the satellite |
| `bridge.py` | LED patterns and mute from the events of Linux Voice Assistant's peripheral WebSocket API |
| `hardware.py` | sysfs LEDs `voxhub-green` / `voxhub-blue`, mute switch input device (`KEY_MICMUTE` or `SW_MUTE_DEVICE`) |
| `guard.py` | the exposure guard (Home Assistant websocket API) |
| `peripherals.py`, `hubwatch.py` | satellite services: LED / mute bridge, firewall for port 6053 and the hub check |

Tests: `pytest` in this folder (unit tests, no hardware), `tests/container/run_addon_test.sh` (builds the add-on
image, runs it next to a PulseAudio container and drives it with a real ESPHome API client: 7 checks).

## VoxHub Assistant (single device)

A Home Assistant OS add-on that turns the VoxHub CM4 hub (or any HAOS machine with a
microphone and a speaker) into a Claude-based voice assistant:

**wake word -> record (VAD end-pointing) -> Whisper -> Claude with Home Assistant tools -> Piper -> speaker**

Wake word detection, speech-to-text and text-to-speech all run locally. Only the
transcribed text (plus tool results) is sent to the Anthropic API.

```
assistant/
├── repository.yaml              add-on repository manifest
├── README.md                    this file
├── pyproject.toml               dev tooling (pytest, ruff)
├── requirements-dev.txt
├── tests/                       pytest suite (no hardware, network or API key needed)
├── voxhub_satellite/            the VoxHub Satellite add-on (two-device system)
└── voxhub_assistant/            the VoxHub Assistant add-on (single device)
    ├── config.yaml              add-on manifest, options and schema
    ├── build.yaml               base images per architecture
    ├── Dockerfile
    ├── run.sh                   entry point (bashio)
    ├── requirements.txt
    ├── requirements-local-wakeword.txt
    ├── DOCS.md  CHANGELOG.md  translations/en.yaml
    └── app/voxhub_assistant/
        ├── __main__.py          wiring and shutdown
        ├── config.py            options parsing and validation
        ├── pipeline.py          the voice loop (state machine)
        ├── audio.py             microphone / speaker (parec, pacat), gain, tones
        ├── vad.py               energy VAD and utterance end-pointing
        ├── wakeword.py          Wyoming and in-process openWakeWord
        ├── wyoming_clients.py   Whisper (STT) and Piper (TTS) clients
        ├── sentences.py         sentence splitting for streaming TTS
        ├── agent.py             Claude streaming tool loop, memory, spoken errors
        ├── tools.py             tool definitions and execution
        ├── ha_client.py         Home Assistant REST client and service policy
        └── leds.py              status LEDs and mute switch (optional)
```

> **Build status:** the Python code is covered by the test suite described below, but the
> Docker image has **not** been built or run in this repository's environment (no
> aarch64 builder, Docker Hub rate limits). Expect to iterate once on the first on-device
> build; see [What has not been verified](#what-has-not-been-verified).

## Architecture

```
                      VoxHub CM4 running Home Assistant OS
 ┌────────────────────────────────────────────────────────────────────────────┐
 │                                                                            │
 │  2x PDM mic→ADAU7002─┐                              ┌──I2S── MAX98357A ──► │ speaker
 │  (googlevoicehat     │                              │        4 ohm / 3 W   │
 │   ALSA card)         ▼                              │                      │
 │              ┌──────────────── hassio_audio (PulseAudio) ───────────────┐  │
 │              │ 48 kHz stereo S32 -> 16 kHz mono S16      resample/upmix │  │
 │              └──────┬──────────────────────────────────────────▲────────┘  │
 │                parec│                                           │pacat     │
 │  ┌──────────────────▼───────────────────────────────────────────┴───────┐  │
 │  │ VoxHub Assistant add-on                                              │  │
 │  │                                                                      │  │
 │  │  Microphone ─► mic gain ─► [IDLE] wake word ──┐                      │  │
 │  │                                               ▼                      │  │
 │  │                            [LISTENING] Endpointer (energy VAD)       │  │
 │  │                                               ▼                      │  │
 │  │                            [THINKING] STT ─► ClaudeAgent ◄─► tools   │  │
 │  │                                               │ text deltas          │  │
 │  │                                               ▼                      │  │
 │  │  Speaker ◄─ volume ◄─ TTS ◄─ SentenceSplitter [SPEAKING]             │  │
 │  │                                                                      │  │
 │  │  LEDs (sysfs) ◄─ state        mute switch (evdev) ─► state           │  │
 │  └───┬───────────────┬───────────────┬──────────────┬───────────────────┘  │
 │      │ Wyoming       │ Wyoming       │ Wyoming      │ HTTP                 │
 │      ▼               ▼               ▼              ▼                      │
 │  openWakeWord     Whisper          Piper       Supervisor proxy            │
 │  add-on :10400    add-on :10300    add-on      http://supervisor/core/api  │
 │                                    :10200      └─► Home Assistant Core     │
 └───────────────────────────────────────────────┬────────────────────────────┘
                                                 │ HTTPS: text only
                                                 ▼
                                       Anthropic Messages API
```

### One turn, step by step

1. **Idle.** `parec` delivers 80 ms chunks of 16 kHz mono audio. They are streamed to the
   wake word engine; the loop also tracks the ambient noise level.
2. **Wake.** On detection a short beep is played and the blue LED turns on.
3. **Listening.** The `Endpointer` waits for speech, then for `silence_seconds` of
   silence (or `max_utterance_seconds`). If nobody speaks within `no_speech_timeout`,
   the loop returns to idle.
4. **Thinking.** The utterance goes to Whisper. The transcript goes to Claude through
   the streaming Messages API. If Claude calls tools, they are executed against Home
   Assistant and the results are sent back until Claude produces its final text.
5. **Speaking.** Text deltas are cut into sentences as they arrive. Each sentence is
   synthesized by Piper while the previous one is playing, so the first sentence is heard
   before Claude has finished writing.
6. **Follow-up (optional).** With `follow_up: true` the add-on listens again for
   `follow_up_seconds` without requiring the wake word.

The hub has no acoustic echo cancellation, so the pipeline is **half-duplex**: whatever
the microphones pick up while the assistant thinks or speaks is discarded before
listening resumes. You cannot interrupt the assistant mid-sentence (barge-in).

## Design decisions

**Audio: `parec`/`pacat` subprocesses against the Supervisor's PulseAudio.** With
`audio: true` the Supervisor injects `PULSE_SERVER` and a client config into the
container; the ALSA device itself belongs to the `hassio_audio` container. Small command
line clients are the most robust option inside an add-on: no native audio library is
loaded into the Python process (so no PortAudio/ALSA wheels to build on aarch64),
PulseAudio does the 48 kHz stereo S32 to 16 kHz mono S16 conversion, the device chosen on
the add-on's *Audio* card is honoured automatically, and a crashed or restarted sound
server only costs a subprocess respawn. This is the same idea as the official Assist
Microphone add-on, which pipes `arecord`/`aplay`; those work here too via `mic_command`
and `speaker_command` (the image ships `alsa-utils` with the ALSA pulse plugin).

**Wake word: the Wyoming openWakeWord add-on by default.** It keeps this image small
(no onnxruntime, tflite or scipy), reuses the add-on you may already run for Assist, and
supports custom models from `/share/openwakeword`. Streaming 32 kB/s of audio over the
internal Docker network is negligible. The in-process engine (`wake_word_engine: local`)
is included for a self-contained setup; its dependencies are installed fail-soft at build
time, which is why the default does not depend on them.

**Voice activity detection: adaptive energy gate.** After a wake word the job is only to
find the end of one utterance. An energy threshold relative to a tracked noise floor does
that with numpy alone, and Whisper tolerates trailing silence.

**Claude: `claude-haiku-5-5` at `effort: low`, streaming, manual tool loop.** Haiku is
the fast, low-cost model, which matters most in a voice loop where every tool call is
another round trip. `claude-sonnet-5-5` and `claude-opus-5-5` are selectable for harder
requests. The request never sets `thinking` (adaptive thinking is the default on all
three and cannot be disabled on Sonnet/Opus 5.5); depth is controlled with
`output_config.effort`, which works unchanged across the three models. The system prompt
and tool list are static and carry one `cache_control` breakpoint; the current time is
put into the user message so it never invalidates the cached prefix.

**Memory: plain text, bounded, with a timeout.** Within a turn, assistant content
(including thinking blocks) is echoed back unchanged as the API requires. Between turns
only the user text and the final reply text are kept, for at most `max_history_turns`
turns and `conversation_timeout` seconds. Dropping old turns therefore never rewrites
history underneath a preserved thinking block.

**Safety: allow-list plus deny-list for service calls.** Claude can read entities in
`exposed_domains` and call services only in `allowed_service_domains`, on explicitly
listed entities of allowed domains. `denied_service_domains` always wins and by default
contains `lock`, `alarm_control_panel` and administrative domains. Calls without a
target entity are rejected.

## Setup on Home Assistant OS

Prerequisite for the VoxHub hardware: the `googlevoicehat-soundcard` overlay must be
enabled in `config.txt` on the HAOS boot partition so the sound card exists (see the
hardware/OS part of this repository).

1. **Install the speech add-ons.** *Settings -> Add-ons -> Add-on store*: install and
   start **Whisper**, **Piper** and **openWakeWord** (official add-ons). On a CM4 use a
   small Whisper model (`tiny-int8` or `base-int8`) and a `low` or `medium` Piper voice.
2. **Add this repository** (pick one):
   - *Add-on store -> ⋮ -> Repositories* and add
     `https://github.com/geilevideossos-gamedev/fable-sbc-test`. The Supervisor expects
     `repository.yaml` in the **root** of the Git repository and then finds add-on
     folders anywhere below it, so a copy of `assistant/repository.yaml` is kept at the
     repository root for this method (it is already there).
   - **Local add-on:** copy the folder `assistant/voxhub_assistant` to `/addons/` on the
     device (Samba or SSH add-on), then *Add-on store -> ⋮ -> Check for updates*. It
     appears under *Local add-ons*.
3. **Install VoxHub Assistant.** The image is built on the device; the first build takes
   several minutes on a CM4.
4. **Configure.** On the *Configuration* tab set `anthropic_api_key` (from
   console.anthropic.com). Optionally choose the model, wake word and Piper voice.
5. **Pick audio devices.** On the same tab, in the *Audio* card, select the VoxHub
   input and output (see [Troubleshooting](#troubleshooting)).
6. **LEDs and mute switch (VoxHub only).** Turn *Protection mode* off on the *Info* tab
   if you want LED feedback. Without it the add-on works, minus the LEDs.
7. **Start and test.** Start the add-on and open the *Log* tab. Say "Hey Jarvis", wait
   for the beep, then "turn on the kitchen light" or "what's the temperature in the
   living room?". The log shows `Wake word detected`, the length of the recording and
   each service call.

## Configuration reference

| Option | Default | Description |
|---|---|---|
| `anthropic_api_key` | *(required)* | Anthropic API key. Never logged. |
| `model` | `claude-haiku-5-5` | `claude-haiku-5-5` (fastest), `claude-sonnet-5-5` or `claude-opus-5-5` (most capable). |
| `custom_model` | | Any other model id; overrides `model`. |
| `effort` | `low` | `low`, `medium`, `high`, `xhigh`, `max`. Higher is slower. |
| `max_tokens` | `2048` | Response limit, thinking included. |
| `request_timeout` | `30` | Seconds per API request (one automatic retry). |
| `assistant_name` | `Jarvis` | Name used in the system prompt. |
| `language` | `en` | Whisper language and default reply language. |
| `system_prompt_extra` | | Extra instructions or household facts. |
| `conversation_timeout` | `300` | Seconds of inactivity before memory is cleared. |
| `max_history_turns` | `6` | Remembered question/answer pairs (0 = none). |
| `wake_word_engine` | `wyoming` | `wyoming` (openWakeWord add-on) or `local` (in-process). |
| `wake_word` | `hey_jarvis` | Model name, or a `.onnx`/`.tflite` path under `/share` for `local`. |
| `wake_word_uri` | `tcp://core-openwakeword:10400` | Wyoming wake word service. |
| `wake_word_threshold` | `0.5` | Threshold for the `local` engine. |
| `wake_sound` | `true` | Beep on wake word. |
| `stt_uri` | `tcp://core-whisper:10300` | Wyoming speech-to-text service. |
| `tts_uri` | `tcp://core-piper:10200` | Wyoming text-to-speech service. |
| `tts_voice` | | Piper voice, e.g. `en_US-lessac-medium`. Empty = Piper's default. |
| `input_device` / `output_device` | | PulseAudio source/sink name. Empty = the add-on's *Audio* selection. |
| `mic_command` / `speaker_command` | | Replace `parec`/`pacat` (see DOCS.md). |
| `mic_gain` | `1.0` | Software microphone gain. Try 4 to 8 on the VoxHub. |
| `volume` | `0.7` | Software speaker volume, 0.0 to 1.0. |
| `silence_seconds` | `0.8` | Silence that ends a request. |
| `max_utterance_seconds` | `15` | Hard limit for one request. |
| `no_speech_timeout` | `6` | Give up if nothing is said after the wake word. |
| `vad_sensitivity` | `2.5` | Speech must be this many times louder than the noise floor. |
| `follow_up` | `false` | Keep listening after an answer. |
| `follow_up_seconds` | `5` | Follow-up window. |
| `exposed_domains` | built-in list | Entity domains Claude may read. |
| `allowed_service_domains` | see `config.yaml` | Domains Claude may control. |
| `denied_service_domains` | `lock`, `alarm_control_panel`, ... | Never controllable; wins over the allow-list. |
| `leds` / `mute_switch` | `true` | VoxHub extras; ignored when absent. |
| `log_level` | `info` | Transcripts appear only at `debug`. |

## Claude's tools

| Tool | What it does |
|---|---|
| `search_entities(query, domain)` | Fuzzy search over exposed entities; returns id, name, area, state. |
| `get_state(entity_id)` | State and attributes of one exposed entity. |
| `call_service(domain, service, entity_id[], data)` | Calls a service after the policy check. |
| `get_weather_forecast(entity_id, type)` | Daily or hourly forecast via `weather.get_forecasts`. |

The current date and time are given to Claude with every request, so time questions need
no tool call.

## The alternative: the Home Assistant native setup (now the default)

Home Assistant can do all of this without this add-on: the official **Anthropic** conversation integration with
the "Assist" API, an **Assist pipeline** with Whisper, Claude and Piper, and a **voice satellite** per room. Since
the VoxHub became a two-device system (hub + satellite) this is the default; the hub runs the **VoxHub Satellite**
add-on described at the top of this file, the satellite board the image of `os/satellite/`.

What the native setup adds: several satellites, room awareness, timers, announcements, the pipeline debug view and
updates maintained by the Home Assistant project. What VoxHub adds on top: the satellite software with LEDs and the
mute switch, the microphone gain for the I2S microphones, and the exposure guard that turns this add-on's
deny-list for locks and alarm panels into a hard rule for Home Assistant's Assist API.

This add-on remains useful for a single VoxHub without an Assist pipeline: one install and one API key, Claude
with its own allow/deny lists for services, sentence-level streaming and half-duplex handling. It filters by domain
instead of using Home Assistant's "exposed entities" setting and does not appear as an Assist device.

## Privacy

- **Stays on the device:** all audio. Wake word detection, Whisper and Piper run locally
  and no audio is uploaded anywhere by this add-on.
- **Sent to Anthropic (HTTPS):** the transcript of what you said after the wake word,
  the system prompt and tool definitions, the short conversation memory, and the results
  of tool calls Claude makes: entity ids, friendly names, areas and states for entities in
  `exposed_domains`. Remove domains from `exposed_domains` to narrow this.
- **Not sent:** your Home Assistant token, the API key (other than as the request's
  authentication), entities outside the exposed domains.
- **Logs:** transcripts are logged only at `debug` level; the API key is never logged.
- How Anthropic handles API data is governed by Anthropic's own terms and privacy policy.

## Latency expectations on a CM4

These are estimates from the component characteristics, not measurements on the VoxHub.

| Stage | Typical |
|---|---|
| Wake word detection to beep | 0.1 to 0.3 s |
| End-pointing (waiting for silence) | `silence_seconds`, 0.8 s by default |
| Whisper `tiny-int8` on a 3 s request | about 1.5 to 3 s (`base-int8`: roughly double) |
| Claude Haiku, first sentence | about 0.5 to 1.5 s, plus about 0.5 to 1.5 s per tool round trip |
| Piper, first sentence (`low`/`medium` voice) | about 0.5 to 1.5 s |
| **End of speech to first audio** | **about 3 to 6 s** for a simple question, 4 to 8 s for device control |

Whisper dominates. To speed things up: use `tiny-int8`, point `stt_uri` at a Whisper
instance on a faster machine, keep `effort: low`, and keep `silence_seconds` short.

## Troubleshooting

**Finding the VoxHub sound card.** The googlevoicehat overlay creates one ALSA card
(`snd_rpi_googlevoicehat_soundcar`). In the add-on's *Audio* card it usually shows up as
a "Built-in Audio" style entry whose PulseAudio name contains `soc_sound`. To see the
exact names run `ha audio info` in the SSH add-on and look at the `input` and `output`
lists. Either select them in the *Audio* card or copy the names into `input_device` /
`output_device`. If the card is missing entirely, the device tree overlay is not loaded.

**The wake word never triggers or Whisper returns nothing.** The PDM MEMS microphones (IM69D130 via ADAU7002)
deliver 24-bit samples in a 32-bit I2S frame, and typical speech sits far below full
scale, so after conversion to 16 bit the signal is quiet. Raise `mic_gain` (4 to 8 is a
normal range for this microphone) and/or the PulseAudio source volume
(`ha audio volume input --index <n> --volume 100`). Set `log_level: debug` to see
transcripts. Too much gain makes loud speech clip and hurts recognition. Also check the
mute slide switch: when it is on, the microphone data line is disconnected from the CM4
(capture is silent; the microphones themselves stay powered) and the red LED is lit.

**Recording stops too early or too late.** Adjust `silence_seconds`. In a noisy room
raise `vad_sensitivity`; if quiet speech is missed, lower it.

**The assistant hears itself / triggers on its own voice.** Lower `volume`. The pipeline
discards microphone audio while speaking, but a very loud reply can still ring in the
room after playback ends.

**No sound.** Check the output selection, `volume`, and that `PULSE_SERVER` is available
(the add-on needs `audio: true`, which is set). The MAX98357A has no mixer control, so
volume is purely the `volume` option.

**"wake word service unavailable" / "speech-to-text unavailable".** The corresponding
add-on is not running or uses a different hostname or port. Hostnames are the add-on
slug with `_` replaced by `-` (`core-whisper`, `core-piper`, `core-openwakeword`).

**LEDs stay dark.** Writing `/sys/class/leds/...` and reading `/dev/input/...` requires
a privileged container: switch *Protection mode* off. The log says so once
(`LED feedback disabled`). LED states: green = idle, blue = listening, blinking blue =
thinking, green + blue = speaking, both off = muted.

**Spoken "my API key was rejected".** Check `anthropic_api_key`. Other spoken errors
cover rate limits, timeouts and missing internet; details are in the add-on log.

**In-process wake word fails.** If the log says `openwakeword is not installed`, the
optional wheels were not available at build time; use `wake_word_engine: wyoming`.

## Development and tests

```bash
cd assistant
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                      # 137 tests (86 VoxHub Assistant, 51 VoxHub Satellite), about 3 s
ruff check . && ruff format --check .
python -m compileall -q voxhub_assistant/app
```

The suite needs no hardware, internet access or API key. The Anthropic client, the Home
Assistant API and the audio devices are replaced by fakes; the Wyoming clients talk to
small fake servers on the loopback interface. It covers the Claude tool loop (tool_use,
tool_result, final text, parallel tools, errors, refusal, truncation, loop bound), the
service allow/deny policy, sentence splitting, VAD end-pointing on synthetic audio,
option parsing including consistency between `config.yaml`, the translations and the
code, and a complete simulated turn through the pipeline.

## What has not been verified

- The Docker image build (both architectures) and a run on real HAOS.
- Behaviour against the live Anthropic API; request shapes follow the current SDK
  (`anthropic` 2.x) but only a scripted fake was exercised.
- The in-process openWakeWord engine with real models (tested with a fake model).
- Whether `full_access` plus disabled protection mode is sufficient for writing the LED
  sysfs files and reading the switch device on HAOS, and the exact PulseAudio device
  names of the googlevoicehat card.
- The latency table above.
