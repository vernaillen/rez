---
name: sonos-tts
description: Text-to-speech announcements through Sonos speakers. Use when asked to announce something, speak a message, say something out loud, or send a voice notification to Wouter.
metadata:
  clawdbot:
    emoji: "🔊"
---

# Sonos TTS Announcements

Speak messages through Sonos speakers using Piper TTS.

## Setup

- **TTS Server:** Piper on ubuntu (10.0.2.122:8767)
- **Voice:** British English (alba-medium)
- **Speaker:** Sonos Zitkamer

## Usage

```bash
ssh raspberrypi '~/clawd/skills/sonos-tts/scripts/tts.sh "Your message here"'
```

## Examples

```bash
# Simple announcement
tts.sh "Dinner is ready"

# Reminder
tts.sh "Wouter, your meeting starts in 5 minutes"

# Weather update
tts.sh "Good morning! It's 18 degrees and sunny today"
```

## Notes

- Piper TTS runs on ubuntu, audio plays on Sonos
- Keep messages concise for best results
- British English voice (alba-medium)
