---
name: local-whisper
description: Transcribe audio via local whisper-cpp server (no API costs).
metadata: {"clawdbot":{"emoji":"🎙️","requires":{"bins":["curl","ffmpeg"]}}}
---

# Local Whisper Transcription

Transcribe audio files using the local whisper-cpp server running on port 8178.

## Quick start

```bash
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg
```

Output goes to stdout by default, or use `--out` for a file.

## Usage

```bash
# Basic transcription (stdout)
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg

# Save to file
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg --out /tmp/transcript.txt

# Specify language (optional, auto-detected by default)
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg --language nl
```

## Server

The whisper-server runs at `http://localhost:8178` via LaunchAgent.

Check status:
```bash
curl http://localhost:8178/health
```

Restart if needed:
```bash
launchctl kickstart -k gui/$(id -u)/com.whisper.server
```
