# 🧠 Tiered Memory System

A lightweight, zero-infrastructure approach to AI agent memory — inspired by [OpenViking](https://github.com/volcengine/OpenViking), implemented with plain markdown files.

## The Problem

AI agents forget everything between sessions. Loading all context every time wastes tokens and money. Traditional RAG needs vector databases, embedding models, and servers.

## The Solution: L0 / L1 / L2

Three tiers of context, loaded on demand:

| Tier | Purpose | Size | When to load |
|------|---------|------|-------------|
| **L0** | One-liner index | ~100 tokens each | Always (startup) |
| **L1** | Topic summaries | ~2K tokens each | When topic is relevant |
| **L2** | Full details | Unlimited | Only when specifics are needed |

## How It Works

```
memory/
├── INDEX.md              ← L0: global index, always loaded (~200 tokens)
├── infra/
│   ├── .index            ← L0: "VPS, Tailscale, cron jobs, security"
│   └── README.md         ← L1: key details, loaded when relevant
├── portfolio/
│   ├── .index            ← L0: "Crypto + ETF holdings, alerts active"
│   ├── README.md         ← L1: holdings, strategy, alerts
│   └── trades.md         ← L2: full transaction history
├── preferences.md        ← L1: small topic, no folder needed
└── YYYY-MM-DD.md         ← L2: daily logs (raw notes)
```

### Startup Protocol

1. Read `INDEX.md` (L0) — ~200 tokens, gives overview of everything
2. Based on context, read relevant L1 files — only what's needed
3. Access L2 files only for specific questions

### Result

~90% token reduction at startup compared to loading everything. No vector DB. No embedding model. No server. Just smart file organization.

## Guidelines

- **Small topics** → single `.md` file (acts as L1)
- **Large topics** → folder with `.index` (L0) + `README.md` (L1) + detail files (L2)
- **Daily logs** → `YYYY-MM-DD.md` files (L2), raw notes of what happened
- **Curate regularly** → review daily logs, distill insights into L1 summaries
- **Keep L0 tiny** → one line per topic, enough to decide "do I need more?"

## Example INDEX.md

```markdown
# 📇 Memory Index (L0)

- **infra/** — VPS setup, networking, cron jobs, security
- **portfolio/** — Crypto and ETF holdings, alerts, trade history
- **twitter.md** — Social media accounts and posting strategy
- **preferences.md** — Personal preferences and communication style
```

## Example .index

```
VPS hosting, Tailscale mesh network, 20 cron jobs, nightly security audit
```

## Why Not OpenViking?

OpenViking requires Python, Go, C++, a VLM model, an embedding model, and a running server. This approach gives you the same mental model with zero dependencies — just markdown files and a smart loading protocol.

The pattern matters more than the tooling.
