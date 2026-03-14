---
name: immoweb
description: Monitor Immoweb.be for new property listings with smart matching and full analysis workflow.
homepage: https://immoweb.be
metadata:
  clawdbot:
    emoji: "🏠"
    requires:
      bins: ["uv"]
---

# Immoweb Monitor Skill

Search, monitor, and analyze Immoweb.be property listings. Includes full analysis workflow with:
- Phase 1/2 evaluation against configurable criteria
- Automatic folder creation with ANALYSE.md
- Zaak/privé split estimation
- Comparison to top candidate (configurable)

## Commands

### Search for listings

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py search
```

Options:
- `--postal 9000` — postal code
- `--radius 30` — radius in km (default: 30)
- `--max-price 500000` — max price (default: 500000)
- `--type house` — property type: house, apartment, building
- `--limit 20` — max results to fetch

### Check for NEW listings only

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py check-new
```

### Analyze a property (basic)

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py analyze "https://www.immoweb.be/nl/zoekertje/..."
```

### Full Analysis (creates folder + ANALYSE.md) ⭐

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py analyze-full "https://www.immoweb.be/nl/zoekertje/..."
```

This command:
1. Fetches property details from Immoweb
2. Runs Phase 1 quick checklist (8 must-haves)
3. Runs Phase 2 detailed analysis
4. Estimates zaak/privé split
5. Creates folder in `~/Documents/immo/` with naming: `YYYY-MM-DD_Gemeente_Korte-omschrijving`
6. Generates `ANALYSE.md` with full evaluation

Options:
- `--output-dir /path/to/dir` — custom output directory (default: ~/Documents/immo)

### Mark a property as dismissed

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py dismiss 12345678
```

### List seen/dismissed properties

```bash
cd ~/clawd/skills/immoweb && uv run --with httpx --with beautifulsoup4 immoweb-cli.py list-seen
```

## Configuration

All search criteria are configured in `immoweb-config.json` (same directory as the CLI script). This file is gitignored for privacy.

Example `immoweb-config.json`:

```json
{
  "postal_code": "9000",
  "postal_codes": ["9000", "9100"],
  "radius_km": 30,
  "max_price": 500000,
  "max_price_private": 350000,
  "min_bedrooms": 2,
  "min_living_area": 100,
  "must_have_garden": true,
  "must_have_parking": true,
  "must_be_quiet": true,
  "allow_renovation": false,
  "property_type": "house",
  "min_soundhealing_room": 14,
  "preferred_dance_hall": 60,
  "top_candidate": {
    "name": "My Reference Property",
    "price": 385000,
    "score": 5,
    "features": ["bijgebouw", "rustig", "uitzicht", "tuin"]
  }
}
```

### Scoring

Properties are scored 1-5 stars:
- ⭐⭐⭐⭐⭐ — Excellent (visit immediately)
- ⭐⭐⭐⭐ — Good (definitely visit)
- ⭐⭐⭐ — Acceptable (might visit)
- ⭐⭐ — Mediocre (only if desperate)
- ⭐ — Poor (skip)

Bonus points for:
- Bijgebouw/annexe (practice potential)
- Quiet/rural location
- Move-in ready condition

## Daily Monitoring

Set up automatic daily checks via OpenClaw cron:

```
Check Immoweb for new listings and notify me of any promising properties (score 4+)
```

## VPS Setup (via SOCKS Proxy)

On VPS with datacenter IP, route through Raspberry Pi for residential IP:

### 1. SSH Tunnel Service
The tunnel runs as a systemd user service:
```bash
systemctl --user status immoweb-tunnel.service
```

### 2. Run with proxy
```bash
IMMOWEB_PROXY=socks5://localhost:1080 python3 skills/immoweb/immoweb-cli.py check-new
```

### Environment Variables
- `IMMOWEB_PROXY` or `SOCKS_PROXY` — SOCKS5 proxy URL (e.g., `socks5://localhost:1080`)
