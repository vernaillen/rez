#!/usr/bin/env bash
# Feedly API CLI
# Usage: feedly.sh [categories|feeds|articles [streamId] [hours]]
# Requires: FEEDLY_TOKEN env var

set -euo pipefail

BASE="https://cloud.feedly.com/v3"
TOKEN="${FEEDLY_TOKEN:?Set FEEDLY_TOKEN}"
AUTH="Authorization: Bearer $TOKEN"

cmd="${1:-articles}"
shift || true

case "$cmd" in
  categories)
    curl -sS -H "$AUTH" "$BASE/categories" | python3 -m json.tool
    ;;

  feeds|subscriptions)
    curl -sS -H "$AUTH" "$BASE/subscriptions" | python3 -c "
import json, sys
subs = json.load(sys.stdin)
for s in sorted(subs, key=lambda x: x.get('categories', [{}])[0].get('label', '') if x.get('categories') else ''):
    cats = ', '.join(c.get('label','') for c in s.get('categories', []))
    print(f\"[{cats}] {s.get('title','')}  ({s['id']})\")" 
    ;;

  articles)
    # Get user ID from profile if needed
    if [[ "${1:-}" == "" || "${1:-}" == *"user/-/"* ]]; then
      USER_ID=$(curl -sS -H "$AUTH" "$BASE/profile" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
      stream_id="${1:-user/$USER_ID/category/global.all}"
      stream_id="${stream_id//user\/-\//user\/$USER_ID\/}"
    else
      stream_id="$1"
    fi
    hours="${2:-24}"
    newer_than=$(python3 -c "import time; print(int((time.time() - $hours*3600) * 1000))")
    
    # URL-encode the stream id
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$stream_id', safe=''))")
    
    curl -sS -H "$AUTH" \
      "$BASE/streams/$encoded/contents?count=100&unreadOnly=true&ranked=newest&newerThan=$newer_than" | \
    python3 -c "
import json, sys, html, re

def strip_html(text):
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()

data = json.load(sys.stdin)
items = data.get('items', [])
if not items:
    print('No new articles.')
    sys.exit(0)

print(f'Found {len(items)} articles:\n')
for i, item in enumerate(items, 1):
    title = item.get('title', 'Untitled')
    origin = item.get('origin', {}).get('title', '')
    cats = ', '.join(c.get('label','') for c in item.get('categories', []))
    url = ''
    for alt in item.get('alternate', []):
        url = alt.get('href', '')
        break
    summary = strip_html(item.get('summary', {}).get('content', ''))[:200]
    engagement = item.get('engagement', '')
    
    print(f'{i}. [{cats}] {title}')
    print(f'   Source: {origin}')
    if engagement:
        print(f'   Engagement: {engagement}')
    if summary:
        print(f'   {summary}')
    if url:
        print(f'   {url}')
    print()
"
    ;;

  *)
    echo "Usage: feedly.sh [categories|feeds|articles [streamId] [hours]]"
    exit 1
    ;;
esac
