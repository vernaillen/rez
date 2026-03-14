#!/bin/bash
# Wrapper script to load env and start Discord bot

cd /home/wouter/clawd

# Export all env vars from .env
set -a
source /home/wouter/clawd/.env
set +a

exec python3 /home/wouter/clawd/scripts/discord-voice-bot.py
