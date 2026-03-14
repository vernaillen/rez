#!/bin/bash
# LMS Control Script
# Run on raspberrypi to control Logitech Media Server

PLAYER_ID="88:a2:9e:58:71:b0"
LMS_URL="http://localhost:9000/jsonrpc.js"

lms_cmd() {
    local cmd="$1"
    curl -s "$LMS_URL" -d "{\"method\":\"slim.request\",\"params\":[\"$PLAYER_ID\",[$cmd]]}"
}

case "$1" in
    status)
        result=$(lms_cmd '"status","-","1","tags:a"')
        mode=$(echo "$result" | jq -r '.result.mode')
        title=$(echo "$result" | jq -r '.result.current_title // "Unknown"')
        artist=$(echo "$result" | jq -r '.result.playlist_loop[0].artist // "Unknown"')
        volume=$(echo "$result" | jq -r '.result."mixer volume"')
        echo "{\"status\":\"$mode\",\"title\":\"$title\",\"artist\":\"$artist\",\"volume\":$volume}"
        ;;
    play)
        lms_cmd '"play"' | jq -c '{status: "playing"}'
        ;;
    pause)
        lms_cmd '"pause"' | jq -c '{status: "paused"}'
        ;;
    stop)
        lms_cmd '"stop"' | jq -c '{status: "stopped"}'
        ;;
    volume)
        if [ -z "$2" ]; then
            result=$(lms_cmd '"status"')
            echo "$result" | jq -c '{volume: .result."mixer volume"}'
        elif [[ "$2" =~ ^[+-] ]]; then
            lms_cmd "\"mixer\",\"volume\",\"$2\"" | jq -c "{volume: \"adjusted $2\"}"
        else
            lms_cmd "\"mixer\",\"volume\",\"$2\"" | jq -c "{volume: $2}"
        fi
        ;;
    favorites)
        result=$(lms_cmd '"favorites","items","0","50"')
        echo "$result" | jq '[.result.loop_loop | to_entries[] | {num: (.key + 1), name: .value.name, id: .value.id}]'
        ;;
    favorite)
        if [ -z "$2" ]; then
            echo '{"error": "Usage: lms.sh favorite <number>"}'
            exit 1
        fi
        # Get favorite ID by index (1-indexed)
        idx=$(($2 - 1))
        result=$(lms_cmd '"favorites","items","0","50"')
        fav_id=$(echo "$result" | jq -r ".result.loop_loop[$idx].id")
        fav_name=$(echo "$result" | jq -r ".result.loop_loop[$idx].name")
        if [ "$fav_id" = "null" ]; then
            echo "{\"error\": \"Favorite $2 not found\"}"
            exit 1
        fi
        lms_cmd "\"favorites\",\"playlist\",\"play\",\"item_id:$fav_id\"" > /dev/null
        echo "{\"status\": \"playing\", \"favorite\": \"$fav_name\"}"
        ;;
    search)
        if [ -z "$2" ]; then
            echo '{"error": "Usage: lms.sh search <query>"}'
            exit 1
        fi
        lms_cmd "\"search\",\"0\",\"10\",\"term:$2\"" | jq '.result'
        ;;
    speak)
        shift
        text="$*"
        if [ -z "$text" ]; then
            echo '{"error": "Usage: lms.sh speak <text>"}'
            exit 1
        fi
        # Get audio URL from TTS server
        audio_url=$(curl -s -X POST "http://10.0.2.122:8767/speak" -d "$text")
        if [ -z "$audio_url" ]; then
            echo '{"error": "TTS server failed"}'
            exit 1
        fi
        # Play on Sonos
        sonos play-uri "$audio_url" --name "Sonos Zitkamer" 2>/dev/null
        echo "{\"status\": \"speaking\", \"text\": \"$text\"}"
        ;;
    *)
        echo "LMS Control Script"
        echo "Usage: lms.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  status          - Show current playback status"
        echo "  play            - Resume playback"
        echo "  pause           - Pause playback"
        echo "  stop            - Stop playback"
        echo "  volume [N]      - Get or set volume (0-100, or +/-N)"
        echo "  favorites       - List favorites"
        echo "  favorite <N>    - Play favorite by number"
        echo "  search <query>  - Search library"
        echo "  speak <text>    - Speak text through Sonos (TTS)"
        ;;
esac
