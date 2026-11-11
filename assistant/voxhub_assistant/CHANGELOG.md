# Changelog

## 0.1.0

- Initial release.
- Voice loop: wake word (Wyoming openWakeWord add-on or in-process openWakeWord),
  energy-based end-pointing, Whisper STT and Piper TTS over Wyoming.
- Claude (Anthropic Messages API) with streaming, sentence-by-sentence TTS, prompt
  caching and Home Assistant tools (search entities, get state, call service, weather
  forecast) guarded by allow/deny lists.
- Optional VoxHub status LEDs and hardware mute switch support.
