#!/bin/bash
# Morning wake-up music: Groove Salad on Sonos One with gradual volume fade-in
# Fades from 5 → 16 over 5 minutes
# Runs from VPS via SSH to raspberrypi

SPEAKER="Sonos Zitkamer"
TARGET_VOLUME=16
START_VOLUME=5
FADE_DURATION=300  # 5 minutes in seconds
STEPS=$((TARGET_VOLUME - START_VOLUME))

# Function to send Sonos command via SSH to Pi
sonos_cmd() {
    ssh -o ConnectTimeout=5 raspberrypi "sonos $1 --name \"$SPEAKER\"" 2>/dev/null
}

# Set volume to start level
echo "Setting volume to $START_VOLUME..."
sonos_cmd "volume set $START_VOLUME"

# Start playing Groove Salad
echo "Starting Groove Salad on $SPEAKER..."
sonos_cmd "favorites open \"Groove Salad\""

# Wait a moment for playback to start
sleep 2

# Calculate interval (300s / 11 steps ≈ 27s per step)
INTERVAL=$((FADE_DURATION / STEPS))

# Run the fade-in in background (fully detached with nohup)
nohup bash -c "
    for vol in \$(seq 6 16); do
        sleep $INTERVAL
        ssh -o ConnectTimeout=5 raspberrypi \"sonos volume set \$vol --name '$SPEAKER'\" 2>/dev/null
    done
" >/dev/null 2>&1 &
disown

echo "Fade-in started in background (5→16 over 5 minutes)"
echo "Wake-up initiated! Music playing at volume $START_VOLUME, fading to $TARGET_VOLUME"
