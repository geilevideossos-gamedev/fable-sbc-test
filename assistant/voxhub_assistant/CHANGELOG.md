# Changelog

## 0.1.1

- The capture path removes a constant level from the microphone signal before the gain
  is applied (DC blocker: a one-pole high-pass with a 12.7 Hz corner at 16 kHz, -0.05 dB
  at 100 Hz). The microphones of VoxHub hardware revision A3 (Infineon IM72D128V01) put a
  constant level of typically -40 dBFS on the right channel. Without the filter the
  energy-based end-pointing cannot tell that level from speech: it finds no request, or
  no end of a request. No option has to be set; other microphones are not affected.

## 0.1.0

- Initial release.
- Voice loop: wake word (Wyoming openWakeWord add-on or in-process openWakeWord),
  energy-based end-pointing, Whisper STT and Piper TTS over Wyoming.
- Claude (Anthropic Messages API) with streaming, sentence-by-sentence TTS, prompt
  caching and Home Assistant tools (search entities, get state, call service, weather
  forecast) guarded by allow/deny lists.
- Optional VoxHub status LEDs and hardware mute switch support.
