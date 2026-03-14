#!/bin/bash
# Simple Notion CLI using curl
# Usage: notion-cli.sh <command> [args]

set -e

# Load API key from .env if not set
if [ -z "$NOTION_API_KEY" ]; then
  if [ -f ~/clawd/.env ]; then
    export $(grep -v '^#' ~/clawd/.env | grep NOTION_API_KEY | xargs)
  fi
fi

if [ -z "$NOTION_API_KEY" ]; then
  echo '{"error": "NOTION_API_KEY not set"}' >&2
  exit 1
fi

API="https://api.notion.com/v1"
HEADERS=(
  -H "Authorization: Bearer $NOTION_API_KEY"
  -H "Content-Type: application/json"
  -H "Notion-Version: 2022-06-28"
)

cmd="$1"
shift || true

case "$cmd" in
  page)
    subcmd="$1"
    shift || true
    case "$subcmd" in
      get)
        page_id="$1"
        curl -sS "${HEADERS[@]}" "$API/pages/$page_id"
        ;;
      update)
        page_id="$1"
        props="$2"
        curl -sS "${HEADERS[@]}" -X PATCH "$API/pages/$page_id" -d "$props"
        ;;
      *)
        echo '{"error": "Unknown page subcommand. Use: get, update"}' >&2
        exit 1
        ;;
    esac
    ;;
  db)
    subcmd="$1"
    shift || true
    case "$subcmd" in
      get)
        db_id="$1"
        curl -sS "${HEADERS[@]}" "$API/databases/$db_id"
        ;;
      query)
        db_id="$1"
        filter="${2:-{}}"
        curl -sS "${HEADERS[@]}" -X POST "$API/databases/$db_id/query" -d "$filter"
        ;;
      *)
        echo '{"error": "Unknown db subcommand. Use: get, query"}' >&2
        exit 1
        ;;
    esac
    ;;
  search)
    query="$1"
    curl -sS "${HEADERS[@]}" -X POST "$API/search" -d "{\"query\": \"$query\"}"
    ;;
  *)
    echo "Usage: notion-cli.sh <command> [args]"
    echo "Commands:"
    echo "  page get <id>         - Get a page"
    echo "  page update <id> <json> - Update page properties"
    echo "  db get <id>           - Get database schema"
    echo "  db query <id> [json]  - Query database"
    echo "  search <query>        - Search all content"
    exit 1
    ;;
esac
