# Changelog

## 0.1.1

- The capture path removes a constant level from the microphone signal before the gain
  is applied (DC blocker: a one-pole high-pass with a 12.7 Hz corner at 16 kHz, -0.05 dB
  at 100 Hz). The microphones of VoxHub hardware revision A3 (Infineon IM72D128V01) put a
  constant level of typically -40 dBFS on the right channel. Without the filter the
  energy-based end-pointing cannot tell that level from speech: version 0.1.0 found no
  request and went back to idle after the time-out (log line "No speech heard"). No
  option has to be set; other microphones are not affected.
- The filter works on buffers of any length (in blocks of at most 4096 samples) and
  rejects a pole outside 0..1. The gain is applied before the single rounding to 16 bit.
- Tests cover the filter, the microphone reader and the pipeline with a constant level.
- The default of **Microphone gain** is 32 instead of 1: the end-pointing counts speech
  only above 120 counts after the gain, and speech of 60 dBSPL at the VoxHub microphones
  is about 7.3 counts rms before it, so with a gain of 1 to 8 the add-on heard the wake
  word and then logged "No speech heard" or cut the request short. The value is
  calculated and simulated, not measured on a board; with another microphone start at 1.
  An installation that was configured with an earlier version may keep its stored value:
  check that **Microphone gain** shows 32 on the Configuration tab.

## 0.1.0

- Initial release.
- Voice loop: wake word (Wyoming openWakeWord add-on or in-process openWakeWord),
  energy-based end-pointing, Whisper STT and Piper TTS over Wyoming.
- Claude (Anthropic Messages API) with streaming, sentence-by-sentence TTS, prompt
  caching and Home Assistant tools (search entities, get state, call service, weather
  forecast) guarded by allow/deny lists.
- Optional VoxHub status LEDs and hardware mute switch support.
