# VoxHub Satellite

Makes the VoxHub hub a voice satellite of its own Home Assistant, exactly like the second VoxHub board
downstairs: wake word on the device, microphones, speaker, status LEDs and the mute switch. The request itself is
answered by the Assist pipeline you choose on the device page - for the VoxHub that is the pipeline with
Claude (Anthropic integration), Whisper and Piper.

The add-on also runs the **exposure guard**: locks, alarm panels and every scene, group or script that controls
one are kept away from Assist, so that Claude can never unlock a door or disarm an alarm.

## Before you start

- Install **Whisper** and **Piper** from the add-on store and start them.
- Add the **Anthropic** integration with your API key and create the pipeline "VoxHub Claude"
  (`fab/ASSEMBLY_AND_TEST.md`, chapter 7).
- Stop the **VoxHub Assistant** add-on if it is installed. Both use the same microphones and LEDs.

## Setup

1. Install the add-on, keep the defaults, and start it.
2. Home Assistant reports a discovered **ESPHome** device named like the option "Device name". Select
   **Add**, then **Submit**.
3. Open the new device, set its **Area** to the room of the hub, and set **Assistant** to "VoxHub Claude".
4. For the LEDs and the mute switch switch **Protection mode** off on the Info tab and restart the add-on.
   Without that the satellite works, minus LEDs and mute reporting.

Say "Okay Nabu" and a request. The wake word can be changed on the device page.

## Options

| Option | Default | Meaning |
|---|---|---|
| Device name | VoxHub Hub | Name of the satellite in Home Assistant. Use the room, for example "VoxHub Upstairs". |
| Wake word | okay_nabu | Wake word at the first start; later it is chosen on the device page. |
| Microphone gain | 4.0 | Software gain of the microphones (4 = +12 dB), 0.1 to 16. See "Microphones". |
| Automatic gain / Noise suppression | 0 / 0 | WebRTC processing of Linux Voice Assistant. See "Microphones". |
| Speaker level | 100 | Level of the speaker output in the sound server. |
| Thinking sound | off | A short sound while Claude thinks. |
| Microphone / Speaker | empty | PulseAudio names; empty = the VoxHub sound card. |
| Status LEDs / Mute switch | on | Need protection mode off. |
| Exposure guard | on | Keeps locks and alarm panels away from Assist. |
| Protected domains | lock, alarm_control_panel | What the guard protects. |
| Guard interval | 300 | Seconds between two full checks (it also reacts to every registry change). |

## Microphones

The two microphones of the VoxHub (Infineon IM72D128V01) are quiet, hence the gain of 4. The one of the right
channel adds a constant level of typically -40 dBFS to its signal. Linux Voice Assistant passes this level on as
long as **Automatic gain** and **Noise suppression** are 0. In a simulation with the test recordings of its wake
word library the level made no difference for speech of 60 dBSPL or more at the microphone. For quieter speech the
wake word was found less often with the level than without it: at 55 dBSPL in 73 % instead of 78 % of the attempts,
at 50 dBSPL in 58 % instead of 62 % (gain 4). Home Assistant's voice detection gave the same result with and
without the level. None of this has been tested on a board. If the wake word is not heard well, raise **Microphone
gain** first (for example to 8; in the simulation that gave 88 % at 55 dBSPL with the level); too much gain makes
loud speech clip.

**Automatic gain** or **Noise suppression** above 0 switch on the WebRTC stage of Linux Voice Assistant. Its
high-pass filter removes the constant level; the stage also changes the sound that goes to speech recognition. In
the simulation automatic gain raised the detection rate (it amplifies by about 7 dB); noise suppression 1 removed
the level but won back only about a third of the lost detections at gains 4 and 8. Neither has been tested on a
board. A value above 0 stays stored in Linux Voice Assistant: to switch the stage off again, set **Mic Auto Gain**
to 0 and **Mic Noise Suppression** to Off on the device page; setting the option back to 0 is not enough.

## LEDs

| LEDs | Meaning |
|---|---|
| green | ready, waiting for the wake word |
| blue | listening |
| blue blinking | Claude is thinking |
| green and blue | speaking |
| both off, red on | muted by the slide switch |
| both off, red off | muted from Home Assistant |
| green blinking slowly | not connected to Home Assistant |
| both blinking fast | the request failed |
| green and blue alternating | a timer is ringing ("stop" ends it) |

## The exposure guard

When the guard un-exposes something it writes a notification and a log line, for example
`Exposure guard: lock.front_door is no longer exposed to Assist (lock entities are never available to the voice
assistant)`. To let the voice assistant control a lock after all, remove `lock` from "Protected domains" - not
recommended.

The guard reads the configuration of every script: a script that calls a lock or alarm action (also through an area,
a device or a template) or that calls such a script is kept unexposed as well.

Not covered by the guard: automations. An automation with a sentence trigger runs before Claude, and an automation
that unlocks or disarms when an exposed switch or helper changes can be started by Claude through that helper. Do not
write such automations, or do not expose their trigger entities.
