# VoxHub Assistant

A Claude-based voice assistant for the VoxHub CM4 hub. Say the wake word, ask a question
or give a command, and the hub answers through its speaker and controls your Home
Assistant devices.

## Before you start

Install and start these official add-ons from the add-on store:

- **Whisper** (speech-to-text). On a CM4 choose the `tiny-int8` or `base-int8` model.
- **Piper** (text-to-speech).
- **openWakeWord** (wake word detection).

You also need an Anthropic API key from <https://console.anthropic.com>.

## Setup

1. Open the **Configuration** tab and paste your key into **Anthropic API key**.
2. In the **Audio** card choose the microphone and the speaker.
3. Save, then start the add-on and open the **Log** tab.
4. Say "Hey Jarvis". After the beep, speak your request.

On the VoxHub, set **Microphone gain** to about 4 to 8, because the I2S microphones are
quiet. For the status LEDs and the mute switch, switch **Protection mode** off on the
Info tab; this is optional.

## Things to try

- "Turn on the kitchen light."
- "Set the living room to 21 degrees."
- "Is the garage door open?"
- "What's the weather tomorrow?"
- "What time is it?"

## What Claude is allowed to do

- **Read:** entities whose domain is listed in *Readable entity domains*.
- **Control:** services in *Allowed service domains*, on entities of those domains.
- **Never:** anything in *Denied service domains*. By default this includes door locks
  and alarm panels. The deny-list always wins.

Garage doors and gates are `cover` entities and are allowed by default. Remove `cover`
from the allow-list if you do not want them voice controlled.

## Choosing a model

- `claude-haiku-5-5` (default): fastest and cheapest, well suited to voice.
- `claude-sonnet-5-5`: more capable, slower.
- `claude-opus-5-5`: most capable of the three, slowest and most expensive.

Keep **Effort** at `low` for quick answers.

## Wake words

With the default engine (`wyoming`), any model known to the openWakeWord add-on works:
`hey_jarvis`, `ok_nabu`, `alexa`, `hey_mycroft`, `hey_rhasspy`. For a custom model, put
the `.tflite` file into `/share/openwakeword` and enter its file name without extension.

With the `local` engine, enter a bundled model name or a full path such as
`/share/openwakeword/my_word.onnx`.

## Using arecord/aplay instead of PulseAudio tools

```yaml
mic_command: "arecord -q -D default -r 16000 -c 1 -f S16_LE -t raw"
speaker_command: "aplay -q -D default -r {rate} -c {channels} -f S16_LE -t raw"
```

## Status LEDs

| LEDs | Meaning |
|---|---|
| Green | Idle, waiting for the wake word |
| Blue | Listening |
| Blue blinking | Thinking |
| Green and blue | Speaking |
| Red (hardware) | Microphones muted by the slide switch |

## Privacy

Audio never leaves the device. The text of what you say after the wake word, and the
device names and states Claude looks up, are sent to the Anthropic API.

## Troubleshooting

See the project README (`assistant/README.md`) for audio device selection, microphone
gain, latency and other troubleshooting.
