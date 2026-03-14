#!/usr/bin/env python3
"""
Polymarket Arbitrage Bot
Main entry point for scanning and simulating trades
"""

import time
import argparse
from datetime import datetime, timezone

import config
from scanner import MarketScanner
from simulator import TradingSimulator


class ArbitrageBot:
    def __init__(self):
        self.scanner = MarketScanner()
        self.simulator = TradingSimulator()
        self.running = False
    
    def scan_once(self, execute: bool = False, min_profit: float = None,
                  crypto_only: bool = False, verify_live: bool = False):
        """Scan for opportunities once"""
        min_profit = min_profit if min_profit is not None else config.MIN_PROFIT_PCT
        
        print(f"\n🔍 Scanning at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}...")
        
        opportunities = self.scanner.find_arbitrage_opportunities(
            crypto_only=crypto_only,
            min_volume=0
        )
        
        # Filter by minimum profit
        good_opps = [o for o in opportunities if o["net_profit_pct"] >= min_profit]
        
        if not opportunities:
            print("   No opportunities found")
            return []
        
        # Separate into profitable and not
        profitable = [o for o in opportunities if o["net_profit_pct"] > 0]
        
        print(f"\n📊 Market Analysis:")
        print(f"   Total markets analyzed: {len(opportunities)}")
        print(f"   Profitable (before fees): {len([o for o in opportunities if o['gross_profit_pct'] > 0])}")
        print(f"   Profitable (after {config.TAKER_FEE_PCT}% fee): {len(profitable)}")
        print(f"   Above {min_profit}% threshold: {len(good_opps)}")
        
        if crypto_only:
            crypto_count = len([o for o in opportunities if o["is_crypto"]])
            print(f"   Crypto markets: {crypto_count}")
        
        print(f"\n{'─'*75}")
        print(f"{'OPPORTUNITY':<45} {'YES':>8} {'NO':>8} {'TOTAL':>8} {'NET%':>8}")
        print(f"{'─'*75}")
        
        for i, opp in enumerate(opportunities[:20]):
            profit_marker = "✅" if opp["net_profit_pct"] >= min_profit else ("📈" if opp["net_profit_pct"] > 0 else "  ")
            crypto_tag = f"[{opp['category']}]" if opp['category'] else ""
            
            question = opp['question'][:40] + "..." if len(opp['question']) > 40 else opp['question']
            display = f"{crypto_tag}{question}"[:44]
            
            print(f"{profit_marker} {display:<44} "
                  f"${opp['yes_price']:.4f} "
                  f"${opp['no_price']:.4f} "
                  f"${opp['total_cost']:.4f} "
                  f"{opp['net_profit_pct']:>7.2f}%")
        
        print(f"{'─'*75}")
        
        # Verify live prices for top opportunities if requested
        if verify_live and good_opps:
            print(f"\n🔄 Verifying live prices for top {min(3, len(good_opps))} opportunities...")
            for opp in good_opps[:3]:
                opp = self.scanner.verify_prices_live(opp)
                if opp.get("live_net_profit_pct") is not None:
                    print(f"   {opp['question'][:40]}...")
                    print(f"      Quoted: {opp['net_profit_pct']:.2f}% → Live: {opp['live_net_profit_pct']:.2f}%")
        
        # Execute trades if requested
        if execute and good_opps:
            print(f"\n🚀 Executing {len(good_opps)} trades (simulation)...")
            executed = 0
            for opp in good_opps:
                # Check balance
                if self.simulator.balance < config.MIN_POSITION_SIZE:
                    print(f"   ⚠️  Insufficient balance: ${self.simulator.balance:.2f}")
                    break
                
                trade = self.simulator.execute_arbitrage(opp)
                if trade:
                    executed += 1
            
            print(f"\n   ✅ Executed {executed} trades")
            self.simulator.print_status()
        
        return opportunities
    
    def run_continuous(self, execute: bool = False, min_profit: float = None,
                       crypto_only: bool = False):
        """Run continuous scanning loop"""
        self.running = True
        min_profit = min_profit if min_profit is not None else config.MIN_PROFIT_PCT
        
        print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║             POLYMARKET ARBITRAGE BOT v1.0                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Mode:          {'SIMULATION' if config.SIMULATION_MODE else 'LIVE TRADING':16}                             ║
║  Min Profit:    {min_profit:5.1f}%                                              ║
║  Position Size: ${config.MIN_POSITION_SIZE} - ${config.MAX_POSITION_SIZE:3}                                       ║
║  Fee Rate:      {config.TAKER_FEE_PCT:5.1f}%                                              ║
║  Auto-Execute:  {str(execute):5}                                               ║
║  Crypto Only:   {str(crypto_only):5}                                               ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Press Ctrl+C to stop                                                 ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)
        
        self.simulator.print_status()
        
        scan_count = 0
        
        try:
            while self.running:
                scan_count += 1
                print(f"\n{'═'*75}")
                print(f"  SCAN #{scan_count}")
                print(f"{'═'*75}")
                
                # Auto-settle old trades (for simulation testing)
                self.simulator.auto_settle_expired(settle_after_minutes=30)
                
                # Scan for opportunities
                self.scan_once(
                    execute=execute, 
                    min_profit=min_profit,
                    crypto_only=crypto_only
                )
                
                # Print detailed status every 5 scans
                if scan_count % 5 == 0:
                    self.simulator.print_status()
                    self.simulator.print_open_positions()
                
                # Wait before next scan
                print(f"\n⏳ Next scan in {config.SCAN_INTERVAL_SECONDS} seconds...")
                time.sleep(config.SCAN_INTERVAL_SECONDS)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            self.running = False
        
        # Final status
        print("\n" + "═"*75)
        print("  FINAL STATUS")
        print("═"*75)
        self.simulator.print_status()
        self.simulator.print_open_positions()
        self.simulator.print_trade_history()
    
    def show_status(self):
        """Show current status"""
        self.simulator.print_status()
        self.simulator.print_open_positions()
        self.simulator.print_trade_history(limit=5)
    
    def reset(self):
        """Reset simulator"""
        self.simulator.reset()


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Arbitrage Bot - Find and exploit market inefficiencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot.py scan                    # Scan once, show opportunities
  python bot.py scan --execute          # Scan and execute profitable trades
  python bot.py scan --crypto           # Only show crypto markets
  python bot.py scan --min-profit 1.0   # Lower profit threshold
  python bot.py run --execute           # Run continuously with auto-execution
  python bot.py cross                   # Cross-platform scan (Polymarket vs Kalshi)
  python bot.py status                  # Show portfolio status
  python bot.py reset                   # Reset to starting balance
        """
    )
    
    parser.add_argument("command", choices=["scan", "run", "status", "reset", "history", "cross"],
                       help="Command to execute")
    parser.add_argument("--execute", "-e", action="store_true",
                       help="Execute trades (simulation mode)")
    parser.add_argument("--min-profit", "-m", type=float, default=None,
                       help=f"Minimum profit %% (default: {config.MIN_PROFIT_PCT})")
    parser.add_argument("--crypto", "-c", action="store_true",
                       help="Only show crypto markets")
    parser.add_argument("--verify", "-v", action="store_true",
                       help="Verify live prices via orderbook")
    
    args = parser.parse_args()
    
    bot = ArbitrageBot()
    
    if args.command == "scan":
        bot.scan_once(
            execute=args.execute, 
            min_profit=args.min_profit,
            crypto_only=args.crypto,
            verify_live=args.verify
        )
        
    elif args.command == "run":
        bot.run_continuous(
            execute=args.execute, 
            min_profit=args.min_profit,
            crypto_only=args.crypto
        )
        
    elif args.command == "status":
        bot.show_status()
        
    elif args.command == "history":
        bot.simulator.print_trade_history(limit=20)
        
    elif args.command == "cross":
        # Cross-platform scanning
        from cross_platform import CrossPlatformScanner
        scanner = CrossPlatformScanner()
        
        print("\n🌐 Running cross-platform scan (Polymarket vs Kalshi)...")
        matches = scanner.scan(min_score=0.60)
        
        if not matches:
            print("\n⚠️  No similar markets found.")
            print("   Polymarket and Kalshi have minimal market overlap.")
        else:
            print(f"\n📊 Found {len(matches)} similar markets")
            print("   ⚠️  Verify markets are IDENTICAL before trading!\n")
            
            for m in matches[:10]:
                p = m["polymarket"]
                k = m["kalshi"]
                arb = m["arbitrage"]
                print(f"   {p['question'][:50]}...")
                print(f"   vs {k['title'][:50]}...")
                print(f"   Score: {m['match_score']:.0%}  Net: {arb['net_profit_pct']:.2f}%\n")
        
    elif args.command == "reset":
        confirm = input("Reset all trades and balance? (yes/no): ")
        if confirm.lower() == "yes":
            bot.reset()
        else:
            print("Reset cancelled")


if __name__ == "__main__":
    main()
