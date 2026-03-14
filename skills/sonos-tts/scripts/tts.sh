#!/bin/bash
# Sonos TTS Announcement Script
# Run on raspberrypi to speak through Sonos

TTS_SERVER="http://10.0.2.122:8767"
SONOS_SPEAKER="Sonos Zitkamer"

text="$*"

if [ -z "$text" ]; then
    echo '{"error": "Usage: tts.sh <message>"}'
    exit 1
fi

# Get audio URL from Piper TTS server
audio_url=$(curl -s -X POST "$TTS_SERVER/speak" -d "$text")

if [ -z "$audio_url" ]; then
    echo '{"error": "TTS server failed to generate audio"}'
    exit 1
fi

# Play on Sonos
sonos play-uri "$audio_url" --name "$SONOS_SPEAKER" 2>/dev/null

echo "{\"status\": \"announced\", \"message\": \"$text\", \"audio_url\": \"$audio_url\"}"
