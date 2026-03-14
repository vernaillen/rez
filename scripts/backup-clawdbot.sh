#!/bin/bash
# Backup critical Clawdbot config (excluding sessions/logs)
# Run periodically or before major changes

BACKUP_DIR="$HOME/clawd/backups"
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/clawdbot-config-$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czvf "$BACKUP_FILE" \
    --exclude='*.jsonl' \
    --exclude='*.lock' \
    --exclude='sessions/' \
    -C "$HOME" \
    .clawdbot/clawdbot.json \
    .clawdbot/cron/jobs.json \
    .clawdbot/credentials/ \
    .clawdbot/tidal-session.json \
    2>/dev/null

echo "✅ Backup created: $BACKUP_FILE"
echo "⚠️  Store this somewhere safe (NOT in git - contains secrets!)"
