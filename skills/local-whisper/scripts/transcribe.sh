#!/bin/bash
# Local Whisper transcription via whisper-cpp server

set -e

WHISPER_URL="${WHISPER_URL:-http://localhost:8178}"

usage() {
    echo "Usage: $0 <audio-file> [--out <output-file>] [--language <lang>]"
    exit 1
}

[[ -z "$1" ]] && usage

INPUT="$1"
shift

OUTPUT=""
LANGUAGE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out|-o) OUTPUT="$2"; shift 2 ;;
        --language|-l) LANGUAGE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

[[ ! -f "$INPUT" ]] && { echo "Error: File not found: $INPUT" >&2; exit 1; }

# Convert to WAV if needed (whisper-cpp prefers 16kHz mono WAV)
TMPWAV=$(mktemp /tmp/whisper-XXXXXX.wav)
trap "rm -f $TMPWAV" EXIT

ffmpeg -y -i "$INPUT" -ar 16000 -ac 1 "$TMPWAV" 2>/dev/null

# Build curl command
CURL_ARGS=(-s -X POST "${WHISPER_URL}/inference" -F "file=@${TMPWAV}")
[[ -n "$LANGUAGE" ]] && CURL_ARGS+=(-F "language=${LANGUAGE}")

# Get transcription
RESULT=$(curl "${CURL_ARGS[@]}")

# Extract text from JSON response
TEXT=$(echo "$RESULT" | jq -r '.text // empty' 2>/dev/null || echo "$RESULT")

# Trim whitespace
TEXT=$(echo "$TEXT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

if [[ -n "$OUTPUT" ]]; then
    echo "$TEXT" > "$OUTPUT"
    echo "$OUTPUT"
else
    echo "$TEXT"
fi
