# Polymarket Arbitrage Bot

A paper trading bot for monitoring and simulating arbitrage opportunities on Polymarket.

## ⚠️ Important: Market Efficiency

**Polymarket is a highly efficient market.** In our testing:
- All markets have YES + NO prices that sum to exactly 1.00
- No direct "Dutch book" arbitrage opportunities exist
- This is expected behavior for a mature prediction market

### Where arbitrage CAN exist:

1. **Cross-Platform Arbitrage**: Price differences between Polymarket and other prediction markets (Kalshi, PredictIt, Manifold)
2. **Timing Arbitrage**: Brief price dislocations during high-volatility events
3. **Information Edge**: Acting faster than the market on breaking news
4. **Fee Arbitrage**: If you have reduced fees (maker vs taker)

## Features

- 📊 Real-time market scanning via Polymarket APIs
- 🎯 Crypto market filtering (BTC, ETH, SOL)
- 💰 Paper trading simulation with P&L tracking
- 📈 Profit/loss calculation with fee consideration
- 🔄 Continuous monitoring mode

## Installation

```bash
cd ~/clawd/projects/polymarket-arb-bot
pip install requests --break-system-packages
```

## Usage

### Scan for opportunities
```bash
python bot.py scan                    # Scan once, show all markets
python bot.py scan --crypto           # Only crypto markets
python bot.py scan --min-profit 0.5   # Show markets with >0.5% potential
python bot.py scan --verify           # Verify live orderbook prices
```

### Run continuous monitoring
```bash
python bot.py run                     # Monitor mode (no execution)
python bot.py run --execute           # Auto-execute profitable trades
python bot.py run --crypto --execute  # Focus on crypto markets
```

### Portfolio management
```bash
python bot.py status                  # Show portfolio status
python bot.py history                 # Show trade history
python bot.py reset                   # Reset to starting balance
```

## Configuration

Edit `config.py`:

```python
MIN_PROFIT_PCT = 0.5          # Minimum profit after fees
TAKER_FEE_PCT = 2.0           # Fee assumption
MAX_POSITION_SIZE = 100       # Max USD per trade
STARTING_BALANCE = 10000      # Simulation starting balance
```

## How Arbitrage Would Work

If a market ever had YES + NO < 1.0:

```
Market: "Will X happen?"
YES price: $0.45 (ask)
NO price:  $0.50 (ask)
Total:     $0.95

Buy $100 of each:
- YES: 222.22 shares ($0.45 × 222.22 = $100)
- NO:  200.00 shares ($0.50 × 200.00 = $100)
- Total invested: $200

Outcome (one MUST win):
- If YES wins: 222.22 × $1 = $222.22
- If NO wins:  200.00 × $1 = $200.00

Guaranteed profit: $200.00 - $200.00 = $0 to $22.22
(Depends on which side wins)
```

For TRUE arbitrage, you'd buy equal SHARES (not equal USD):
```
Buy 100 shares of each @ total cost of $95
Guaranteed payout: $100 (one side wins)
Gross profit: $5 (5.26%)
Net profit after 2% fee: ~$3 (3.16%)
```

## API Endpoints

- **Gamma API**: `https://gamma-api.polymarket.com` - Market metadata
- **CLOB API**: `https://clob.polymarket.com` - Live orderbooks, trading

## Files

```
polymarket-arb-bot/
├── bot.py          # Main entry point
├── scanner.py      # Market scanning logic
├── simulator.py    # Paper trading engine
├── config.py       # Configuration
├── trades.json     # Trade history (auto-created)
└── README.md       # This file
```

## Cross-Platform Scanning

The bot includes a cross-platform scanner comparing Polymarket and Kalshi:

```bash
python bot.py cross          # Scan both platforms for similar markets
python cross_platform.py     # Run standalone cross-platform scanner
```

**⚠️ Important findings:**
- Polymarket and Kalshi have almost NO identical markets
- Similar question text ≠ identical market (different resolution criteria)
- True cross-platform arbitrage is extremely rare between these platforms
- The scanner shows similar markets, but manual verification is required

## Future Improvements

- [ ] Add PredictIt comparison (more market overlap potential)
- [ ] WebSocket for real-time price updates
- [ ] Discord/Telegram alerts for opportunities
- [ ] Historical data analysis
- [ ] Real trading via py-clob-client

## Disclaimer

This is for educational purposes only. Paper trading simulation does not guarantee real trading performance. Always do your own research before risking real capital.
