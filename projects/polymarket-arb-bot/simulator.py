"""
Polymarket Trade Simulator
Paper trading engine for testing arbitrage strategies
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random
import config


@dataclass
class SimulatedTrade:
    id: str
    timestamp: str
    market_question: str
    market_id: str
    condition_id: str
    yes_token_id: str
    no_token_id: str
    yes_price: float
    no_price: float
    total_cost: float
    position_size_usd: float
    yes_shares: float
    no_shares: float
    guaranteed_payout: float
    expected_profit_pct: float
    expected_profit_usd: float
    fee_usd: float
    status: str  # "open", "settled", "expired"
    end_date: Optional[str] = None
    outcome: Optional[str] = None  # "YES" or "NO"
    actual_profit_usd: Optional[float] = None
    settled_at: Optional[str] = None


class TradingSimulator:
    def __init__(self, starting_balance: float = None):
        self.balance = starting_balance or config.STARTING_BALANCE
        self.initial_balance = self.balance
        self.trades: List[SimulatedTrade] = []
        self.trade_counter = 0
        self.trades_file = config.TRADES_FILE
        
        # Load existing trades
        self._load_trades()
    
    def _load_trades(self):
        """Load trades from file"""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get("balance", self.initial_balance)
                    self.initial_balance = data.get("initial_balance", self.initial_balance)
                    self.trade_counter = data.get("trade_counter", 0)
                    self.trades = [SimulatedTrade(**t) for t in data.get("trades", [])]
                    print(f"[Simulator] Loaded {len(self.trades)} trades, balance: ${self.balance:.2f}")
            except Exception as e:
                print(f"[Simulator] Error loading trades: {e}")
    
    def _save_trades(self):
        """Save trades to file"""
        try:
            os.makedirs(os.path.dirname(self.trades_file) or ".", exist_ok=True)
            data = {
                "balance": self.balance,
                "initial_balance": self.initial_balance,
                "trade_counter": self.trade_counter,
                "trades": [asdict(t) for t in self.trades],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open(self.trades_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Simulator] Error saving trades: {e}")
    
    def calculate_arbitrage(self, yes_price: float, no_price: float, 
                           position_size: float, fee_pct: float) -> Dict:
        """
        Calculate arbitrage trade details.
        
        Strategy: Buy equal SHARES of both YES and NO tokens.
        This guarantees that one set of shares pays out $1 each.
        
        Example:
        - YES @ $0.45, NO @ $0.50, total = $0.95
        - Buy 100 shares of each = $45 (YES) + $50 (NO) = $95
        - One outcome wins: 100 * $1 = $100 payout
        - Gross profit: $100 - $95 = $5 (5.26%)
        """
        total_cost_per_pair = yes_price + no_price
        
        if total_cost_per_pair >= 1.0:
            # No arbitrage if total >= 1.0
            return None
        
        # How many complete pairs can we buy?
        # Each pair costs (yes_price + no_price) and pays out $1
        pairs = position_size / total_cost_per_pair
        
        # Calculate costs
        yes_cost = pairs * yes_price
        no_cost = pairs * no_price
        total_invested = yes_cost + no_cost
        
        # Fee is on entry (typically % of investment)
        fee_usd = total_invested * (fee_pct / 100)
        
        # Guaranteed payout: number of pairs * $1
        guaranteed_payout = pairs
        
        # Net profit
        net_profit = guaranteed_payout - total_invested - fee_usd
        net_profit_pct = (net_profit / total_invested) * 100
        
        return {
            "yes_shares": pairs,
            "no_shares": pairs,
            "yes_cost": yes_cost,
            "no_cost": no_cost,
            "total_invested": total_invested,
            "fee_usd": fee_usd,
            "guaranteed_payout": guaranteed_payout,
            "net_profit": net_profit,
            "net_profit_pct": net_profit_pct,
        }
    
    def execute_arbitrage(self, opportunity: Dict, 
                         position_size_usd: float = None) -> Optional[SimulatedTrade]:
        """Simulate executing an arbitrage trade"""
        
        size = position_size_usd or config.MAX_POSITION_SIZE
        size = min(size, self.balance)
        size = min(size, config.MAX_POSITION_SIZE)
        
        if size < config.MIN_POSITION_SIZE:
            print(f"[Simulator] Insufficient balance: ${self.balance:.2f}")
            return None
        
        # Calculate trade details
        calc = self.calculate_arbitrage(
            opportunity["yes_price"],
            opportunity["no_price"],
            size,
            config.TAKER_FEE_PCT
        )
        
        if not calc or calc["net_profit"] <= 0:
            print(f"[Simulator] No arbitrage opportunity (net profit <= 0)")
            return None
        
        # Deduct investment from balance
        self.balance -= calc["total_invested"]
        self.balance -= calc["fee_usd"]
        
        # Create trade record
        self.trade_counter += 1
        trade = SimulatedTrade(
            id=f"SIM-{self.trade_counter:05d}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_question=opportunity["question"],
            market_id=opportunity.get("market_id", ""),
            condition_id=opportunity.get("condition_id", ""),
            yes_token_id=opportunity["yes_token_id"],
            no_token_id=opportunity["no_token_id"],
            yes_price=opportunity["yes_price"],
            no_price=opportunity["no_price"],
            total_cost=opportunity["total_cost"],
            position_size_usd=calc["total_invested"],
            yes_shares=calc["yes_shares"],
            no_shares=calc["no_shares"],
            guaranteed_payout=calc["guaranteed_payout"],
            expected_profit_pct=calc["net_profit_pct"],
            expected_profit_usd=calc["net_profit"],
            fee_usd=calc["fee_usd"],
            status="open",
            end_date=opportunity.get("end_date", "")
        )
        
        self.trades.append(trade)
        self._save_trades()
        
        print(f"[Simulator] Opened {trade.id}:")
        print(f"   Invested: ${calc['total_invested']:.2f} (+ ${calc['fee_usd']:.2f} fee)")
        print(f"   Shares: {calc['yes_shares']:.2f} YES + {calc['no_shares']:.2f} NO")
        print(f"   Guaranteed payout: ${calc['guaranteed_payout']:.2f}")
        print(f"   Expected profit: ${calc['net_profit']:.2f} ({calc['net_profit_pct']:.2f}%)")
        
        return trade
    
    def settle_trade(self, trade_id: str, outcome: str) -> Optional[SimulatedTrade]:
        """
        Settle a trade based on market outcome.
        
        In arbitrage, the outcome doesn't matter - we bought both sides equally.
        We just receive guaranteed_payout.
        """
        trade = None
        for t in self.trades:
            if t.id == trade_id:
                trade = t
                break
        
        if not trade or trade.status != "open":
            return None
        
        # For arbitrage: payout is always the guaranteed amount
        # (equal shares of both outcomes, one wins at $1/share)
        payout = trade.guaranteed_payout
        
        # Calculate actual profit
        actual_profit = payout - trade.position_size_usd - trade.fee_usd
        
        # Add payout to balance
        self.balance += payout
        
        # Update trade
        trade.status = "settled"
        trade.outcome = outcome
        trade.actual_profit_usd = actual_profit
        trade.settled_at = datetime.now(timezone.utc).isoformat()
        
        self._save_trades()
        
        print(f"[Simulator] Settled {trade.id}: {outcome} won")
        print(f"   Payout: ${payout:.2f}, Profit: ${actual_profit:.2f}")
        
        return trade
    
    def auto_settle_expired(self, settle_after_minutes: int = 30):
        """Auto-settle trades that are past their end date or age"""
        now = datetime.now(timezone.utc)
        settled_count = 0
        
        for trade in self.trades:
            if trade.status != "open":
                continue
            
            should_settle = False
            
            # Check if past end date
            if trade.end_date:
                try:
                    end_dt = datetime.fromisoformat(trade.end_date.replace("Z", "+00:00"))
                    if now > end_dt:
                        should_settle = True
                except:
                    pass
            
            # Or if trade is old enough (for testing)
            trade_time = datetime.fromisoformat(trade.timestamp.replace("Z", "+00:00"))
            age_minutes = (now - trade_time).total_seconds() / 60
            if age_minutes > settle_after_minutes:
                should_settle = True
            
            if should_settle:
                # Random outcome (in reality this would come from API)
                outcome = random.choice(["YES", "NO"])
                self.settle_trade(trade.id, outcome)
                settled_count += 1
        
        if settled_count > 0:
            print(f"[Simulator] Auto-settled {settled_count} expired trades")
    
    def get_stats(self) -> Dict:
        """Get trading statistics"""
        open_trades = [t for t in self.trades if t.status == "open"]
        settled_trades = [t for t in self.trades if t.status == "settled"]
        
        total_profit = sum(t.actual_profit_usd or 0 for t in settled_trades)
        total_invested = sum(t.position_size_usd for t in self.trades)
        total_fees = sum(t.fee_usd for t in self.trades)
        open_value = sum(t.position_size_usd for t in open_trades)
        
        win_count = len([t for t in settled_trades if (t.actual_profit_usd or 0) > 0])
        loss_count = len([t for t in settled_trades if (t.actual_profit_usd or 0) <= 0])
        
        roi = ((self.balance - self.initial_balance) / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        
        avg_profit = (total_profit / len(settled_trades)) if settled_trades else 0
        
        return {
            "balance": self.balance,
            "initial_balance": self.initial_balance,
            "available_balance": self.balance,
            "open_positions_value": open_value,
            "total_profit": total_profit,
            "total_fees": total_fees,
            "roi_pct": roi,
            "total_trades": len(self.trades),
            "open_trades": len(open_trades),
            "settled_trades": len(settled_trades),
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": (win_count / len(settled_trades) * 100) if settled_trades else 0,
            "avg_profit_per_trade": avg_profit,
            "total_invested": total_invested,
        }
    
    def print_status(self):
        """Print current status"""
        stats = self.get_stats()
        
        print(f"\n{'═'*55}")
        print(f"  💰 PORTFOLIO STATUS")
        print(f"{'═'*55}")
        print(f"  Balance:        ${stats['balance']:>12,.2f}")
        print(f"  Initial:        ${stats['initial_balance']:>12,.2f}")
        print(f"  P&L:            ${stats['total_profit']:>12,.2f} ({stats['roi_pct']:.2f}%)")
        print(f"  Fees Paid:      ${stats['total_fees']:>12,.2f}")
        print(f"{'─'*55}")
        print(f"  Total Trades:   {stats['total_trades']:>6}")
        print(f"  Open:           {stats['open_trades']:>6}  (${stats['open_positions_value']:,.2f})")
        print(f"  Settled:        {stats['settled_trades']:>6}")
        print(f"  Wins/Losses:    {stats['winning_trades']:>3} / {stats['losing_trades']:<3}")
        print(f"  Win Rate:       {stats['win_rate']:>6.1f}%")
        print(f"  Avg Profit:     ${stats['avg_profit_per_trade']:>12,.2f}")
        print(f"{'═'*55}\n")
    
    def print_open_positions(self):
        """Print open positions"""
        open_trades = [t for t in self.trades if t.status == "open"]
        
        if not open_trades:
            print("[Simulator] No open positions")
            return
        
        print(f"\n📊 OPEN POSITIONS ({len(open_trades)})")
        print("-" * 70)
        
        for trade in open_trades:
            print(f"{trade.id}: {trade.market_question[:50]}...")
            print(f"   Size: ${trade.position_size_usd:.2f}  "
                  f"Shares: {trade.yes_shares:.2f}  "
                  f"Expected: ${trade.expected_profit_usd:.2f} ({trade.expected_profit_pct:.2f}%)")
            if trade.end_date:
                print(f"   Ends: {trade.end_date}")
        print()
    
    def print_trade_history(self, limit: int = 10):
        """Print recent trade history"""
        settled = [t for t in self.trades if t.status == "settled"]
        settled.sort(key=lambda x: x.settled_at or "", reverse=True)
        
        print(f"\n📜 RECENT TRADES (last {limit})")
        print("-" * 70)
        
        for trade in settled[:limit]:
            profit_emoji = "🟢" if (trade.actual_profit_usd or 0) > 0 else "🔴"
            print(f"{profit_emoji} {trade.id}: {trade.outcome} won")
            print(f"   {trade.market_question[:50]}...")
            print(f"   Invested: ${trade.position_size_usd:.2f}  "
                  f"Profit: ${trade.actual_profit_usd:.2f}")
        print()
    
    def reset(self):
        """Reset simulator to starting state"""
        self.balance = config.STARTING_BALANCE
        self.initial_balance = config.STARTING_BALANCE
        self.trades = []
        self.trade_counter = 0
        self._save_trades()
        print(f"[Simulator] Reset complete. Balance: ${self.balance:.2f}")


if __name__ == "__main__":
    sim = TradingSimulator()
    sim.print_status()
    sim.print_open_positions()
    sim.print_trade_history()
