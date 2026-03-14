# 🎵 Rez — OpenClaw Personal AI Assistant

My personal AI assistant running on [OpenClaw](https://github.com/openclaw/openclaw), powered by Claude. Runs 24/7 on a €5/month VPS and communicates via Telegram.

## What it does

- ☀️ **Morning briefing** — weather, sleep data (Garmin), calendar, portfolio, horoscope, Notion tasks
- 📊 **Market monitoring** — real-time tracking of crypto (BTC, ETH, TAO, KAS, LTC) and ETFs, with configurable dip alerts
- 📰 **News digest** — daily Feedly RSS summary, filtered and categorized
- 🐦 **X/Twitter** — monitors @wpnuxt mentions, generates post suggestions and engagement targets for @vernaillen
- 🔒 **Nightly security audit** — automated VPS security checks + breach assessment
- 🔮 **Personalized horoscope** — natal chart transit calculations via Swiss Ephemeris (kerykeion)
- 🏠 **Property monitoring** — Immoweb.be listing alerts (Belgium)
- 🎵 **Music control** — Sonos/LMS integration with morning music automation

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Telegram    │────▶│  OpenClaw    │────▶│  Claude   │
│  (channel)   │◀────│  (gateway)   │◀────│  (API)    │
└─────────────┘     └──────┬───────┘     └──────────┘
                           │
                    ┌──────┴───────┐
                    │  ~/clawd     │
                    │  workspace   │
                    ├──────────────┤
                    │ scripts/     │  Custom automation
                    │ skills/      │  OpenClaw skill plugins
                    │ memory/      │  Tiered context (L0/L1/L2)
                    │ projects/    │  Side projects
                    └──────────────┘
```

## Tiered Memory System

Inspired by [OpenViking](https://github.com/volcengine/OpenViking), but implemented with plain markdown files — zero infrastructure.

```
memory/
├── INDEX.md              ← L0: one-liner index (~200 tokens)
├── infra/
│   ├── .index            ← L0: topic one-liner
│   └── README.md         ← L1: VPS, Tailscale, crons, security
├── portfolio/
│   ├── .index            ← L0: topic one-liner
│   ├── README.md         ← L1: holdings, alerts, strategy
│   └── trades.md         ← L2: full transaction history
├── twitter.md            ← L1: X/Twitter setup
├── astrology.md          ← L1: natal chart config
├── preferences.md        ← L1: personal preferences
└── YYYY-MM-DD.md         ← L2: daily logs
```

**Loading protocol:** Start with L0 index (~200 tokens), load L1 topics as needed, access L2 only for specific details. ~90% token reduction at startup vs loading everything.

## Scripts

| Script | Purpose |
|--------|---------|
| `horoscope.py` | Natal chart transit calculations (kerykeion/Swiss Ephemeris) |
| `market-monitor.sh` | Portfolio price checks + threshold alerts |
| `etf_realtime.py` | Real-time ETF pricing via Yahoo Finance |
| `garmin_query.py` | Sleep & stress data from Garmin Connect |
| `security-audit.sh` | VPS security checks (UFW, fail2ban, SSH, ports, disk) |
| `morning-music.sh` | Automated morning playlist via LMS/Sonos |
| `x-monitor-wpnuxt.sh` | Twitter mention monitoring for @wpnuxt |
| `notion-cli.sh` | Notion task database integration |

## Skills

Community and custom [OpenClaw skills](https://clawhub.com):

- **bird** — X/Twitter CLI (read, search, post)
- **feedly** — RSS feed aggregation
- **yahoo-finance-cli** — Stock/crypto market data
- **lms** — Logitech Media Server control
- **sonos-tts** — Text-to-speech via Sonos speakers
- **immoweb** — Belgian property listing monitor
- **local-whisper** — Voice transcription via whisper-cpp
- **youtube-watcher** — YouTube transcript extraction

## Cron Schedule

| Time (CET) | Job |
|------------|-----|
| 07:15 | 🎵 Morning music |
| 07:30 | ☀️ Morning briefing |
| 07:35 | 📰 Feedly digest |
| 07:50 | 🫀 HeartMath reminder |
| 09:00-17:00 | 📊 Market monitors (EU/NYSE open, afternoon, close) |
| 09:00-17:00 | 🔔 Dip alerts (EMIM, ETH, TAO, BTC) |
| 10:00/13:00 | 🐦 X post suggestions + engagement targets |
| 08:00/12:45/18:00 | 👀 @wpnuxt mention monitoring |
| 23:00 | 🔒 Security audit + breach assessment |

## Infrastructure

- **VPS:** Hetzner (€5/mo) running Ubuntu + OpenClaw gateway
- **Network:** Tailscale mesh (VPS + MacBook + Ubuntu + Pi)
- **Security:** UFW firewall, fail2ban, SSH key-only, nightly audits
- **Services:** whisper-cpp (port 8178), Netdata (port 19999)

## Setup

This is a personal workspace — not a generic template. But if you're curious about running a similar setup:

1. Install [OpenClaw](https://docs.openclaw.ai)
2. Configure a Telegram channel
3. Add scripts and skills to your workspace
4. Set up cron jobs for automation

## License

Personal project — not intended for redistribution.
