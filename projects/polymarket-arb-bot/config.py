"""
Polymarket Arbitrage Bot - Configuration
"""

import os

# API Endpoints
CLOB_HOST = "https://clob.polymarket.com"
GAMMA_HOST = "https://gamma-api.polymarket.com"
CHAIN_ID = 137  # Polygon Mainnet

# Trading Parameters
MIN_PROFIT_PCT = 0.5          # Minimum profit % to execute (after fees)
TAKER_FEE_PCT = 2.0           # Current taker fee (varies by market type)
MAX_POSITION_SIZE = 100       # Max USD per trade
MIN_POSITION_SIZE = 10        # Min USD per trade

# Simulation Settings
SIMULATION_MODE = True        # True = paper trading, False = real trading
STARTING_BALANCE = 10000      # Starting simulation balance in USD

# Scanner Settings
SCAN_INTERVAL_SECONDS = 30    # How often to scan for opportunities
TARGET_MARKETS = ["BTC", "ETH", "SOL"]  # Crypto assets to track

# File Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TRADES_FILE = os.path.join(PROJECT_DIR, "trades.json")
LOG_FILE = os.path.join(PROJECT_DIR, "arb_bot.log")

# Risk Management
MAX_OPEN_POSITIONS = 20       # Maximum concurrent open positions
MAX_DAILY_TRADES = 100        # Maximum trades per day
MAX_SINGLE_MARKET_EXPOSURE = 500  # Max USD exposure to single market
