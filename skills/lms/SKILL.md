---
name: lms
description: Control Logitech Media Server (Squeezebox/LMS) for music playback. Use when asked to play music, control volume, check what's playing, list favorites, or manage the LMS player on raspberrypi. Also supports TTS announcements via Sonos.
metadata:
  clawdbot:
    emoji: "🎶"
---

# LMS (Logitech Media Server) Control

Control the Squeezebox/LMS player on raspberrypi via JSON-RPC API. Also supports TTS announcements through Sonos.

## Setup

LMS runs on raspberrypi (localhost:9000). Player: SqueezeLite with AudioQuest DragonFly Black.

- **Player ID:** `88:a2:9e:58:71:b0`
- **Server:** `localhost:9000` (on raspberrypi)

## Commands

All commands run via SSH to raspberrypi:

```bash
ssh raspberrypi '~/clawd/skills/lms/scripts/lms.sh <command> [args]'
```

### Playback

```bash
# Play/pause/stop
lms.sh play
lms.sh pause
lms.sh stop

# Status (what's playing)
lms.sh status

# Volume (0-100)
lms.sh volume 50
lms.sh volume +10
lms.sh volume -10
```

### Favorites

```bash
# List favorites
lms.sh favorites

# Play a favorite by number (1-indexed)
lms.sh favorite 3
```

### TTS / Announcements

```bash
# Speak through Sonos
lms.sh speak "Hello Wouter, dinner is ready"
```

### Direct API

For advanced queries, use the JSON-RPC API directly:

```bash
ssh raspberrypi 'curl -s "http://localhost:9000/jsonrpc.js" -d "{\"method\":\"slim.request\",\"params\":[\"88:a2:9e:58:71:b0\",[\"status\",\"-\",\"1\"]]}"'
```

## LMS Favorites (Current)

1. VRT Studio Brussel
2. VRT Radio 1
3. Groove Salad
4. Groove Salad Classic
5. Beat Blender
6. One More - Yaeji
7. VRT Studio Brussel Vuurland
8. VRT Studio Brussel UNTZ
9. VRT De Tijdloze
10. VRT Studio Brussel De Jaren Nul
11. Slow-Fi

## Notes

- LMS must be accessed from raspberrypi (local network)
- Use SSH from harmonics-clawd to control
- Player uses AudioQuest DragonFly Black DAC
