---
name: feedly
description: Fetch and summarize Feedly RSS feed articles. Use when asked about news feeds, Feedly summaries, morning briefings from Feedly, or checking new articles from subscribed feeds.
---

# Feedly Skill

Fetch articles from Feedly API and produce summaries.

## Setup

Requires `FEEDLY_TOKEN` in `~/clawd/.env`.

Get token: Go to https://feedly.com/v3/auth/dev (personal) or https://feedly.com/i/team/api (enterprise).

## Usage

### Fetch new articles

```bash
export $(grep FEEDLY_TOKEN ~/clawd/.env | xargs)
bash ~/clawd/skills/feedly/scripts/feedly.sh [categories|feeds|articles [streamId] [hours]]
```

Commands:
- `categories` — list all categories
- `feeds` — list all subscriptions
- `articles [streamId] [hours]` — fetch articles from a stream (default: all, last 24h)
  - streamId can be a category id or feed id
  - Use `user/-/category/global.all` for all feeds

### Morning summary workflow

1. Run `articles` for last 24h
2. Summarize output: group by category, highlight most interesting
3. Keep summary concise: title + source + 1-line summary per article
4. Max 15-20 articles; prioritize by engagement/relevance

### Token refresh

If 401 errors occur, token is expired. Ask user to regenerate at feedly.com/v3/auth/dev.
