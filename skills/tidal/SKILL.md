---
name: tidal
description: Control TIDAL music streaming - browse favorites, get recommendations, manage playlists.
homepage: https://tidal.com
metadata:
  clawdbot:
    emoji: "🎵"
    requires:
      bins: ["uv"]
---

# TIDAL Skill

Control your TIDAL account: browse favorites, get personalized recommendations, create and manage playlists.

## Setup

First time setup requires authentication:

```bash
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py login
```

This opens a browser for TIDAL OAuth login. Session is saved to `~/.clawdbot/tidal-session.json`.

## Commands

All commands use `uv run --with tidalapi` to handle dependencies automatically.

### Authentication

```bash
# Login (opens browser)
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py login

# Check auth status
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py status
```

### Favorites

```bash
# Get favorite tracks (default 20)
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py favorites

# Get more favorites
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py favorites --limit 50
```

### Recommendations

```bash
# Get recommendations based on favorites
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py recommend

# Recommendations from specific track IDs  
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py recommend --tracks 12345678 87654321

# More recommendations per seed track
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py recommend --limit 30
```

### Playlists

```bash
# List all playlists
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py playlists

# Get tracks from a playlist
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py playlist-tracks <playlist_id>

# Create a playlist
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py create-playlist "My Playlist" --tracks 123 456 789 --description "Created by Clawdbot"

# Delete a playlist
cd ~/clawd/skills/tidal && uv run --with tidalapi tidal-cli.py delete-playlist <playlist_id>
```

## Output Format

All commands output JSON for easy parsing. Example:

```json
{
  "status": "success",
  "tracks": [
    {
      "id": "12345678",
      "title": "Song Name",
      "artist": "Artist Name", 
      "album": "Album Name",
      "duration": 245,
      "url": "https://tidal.com/browse/track/12345678"
    }
  ]
}
```

## Tips

- Use `--limit` to control how many results you get
- Track IDs can be found in URLs or from other commands
- Recommendations work best with 5-20 seed tracks
- The session persists across restarts (stored in ~/.clawdbot/)
