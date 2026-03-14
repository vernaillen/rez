#!/bin/bash
# X Monitor for @wpnuxt — searches for relevant headless WordPress + Vue/Nuxt tweets
# Read-only: no posting, only monitoring
set -e

export AUTH_TOKEN="${AUTH_TOKEN:-$(grep X_WPNUXT_AUTH_TOKEN ~/clawd/.env | cut -d= -f2)}"
export CT0="${CT0:-$(grep X_WPNUXT_CT0 ~/clawd/.env | cut -d= -f2)}"

# Verify auth is available
if [ -z "$AUTH_TOKEN" ] || [ -z "$CT0" ]; then
  echo "ERROR: X auth not configured. Set AUTH_TOKEN/CT0 or X_WPNUXT_AUTH_TOKEN/X_WPNUXT_CT0 in .env"
  exit 1
fi

SEARCHES=(
  '"headless wordpress" (vue OR nuxt OR nuxtjs)'
  '"wp headless" (vue OR nuxt)'
  '"wordpress api" (vue OR nuxt) -plugin'
  '"wpgraphql" OR "wp graphql" (nuxt OR vue)'
  '"wordpress" "nuxt 4"'
  '"wordpress" "vue" "headless" -theme -flavor'
  'wpnuxt -from:vernaillen -from:wpnuxt'
)

SEEN_FILE=~/clawd/memory/x-monitor-wpnuxt-seen.txt
touch "$SEEN_FILE"

ALL_RESULTS=""

for query in "${SEARCHES[@]}"; do
  RESULTS=$(bird search "$query" -n 5 2>/dev/null || true)
  if [ -n "$RESULTS" ]; then
    ALL_RESULTS+="$RESULTS"$'\n'
  fi
  sleep 2  # rate limit
done

# Extract unique tweet URLs, filter out already seen and own tweets
echo "$ALL_RESULTS" | grep -oP 'https://x\.com/\S+' | sort -u | while read -r url; do
  # Skip own tweets
  if echo "$url" | grep -q "/wpnuxt/\|/vernaillen/"; then
    continue
  fi
  # Skip already seen
  if grep -qF "$url" "$SEEN_FILE"; then
    continue
  fi
  # Mark as seen
  echo "$url" >> "$SEEN_FILE"
  # Output the tweet
  TWEET=$(bird read "$url" 2>/dev/null || echo "Could not fetch: $url")
  echo "---NEW_TWEET---"
  echo "$TWEET"
  echo "$url"
done
