"""
Polymarket Market Scanner
Fetches and analyzes markets for arbitrage opportunities
"""

import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import config


class MarketScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PolymarketArbBot/1.0",
            "Accept-Encoding": "gzip, deflate",
        })
    
    def get_gamma_markets(self) -> List[Dict]:
        """Fetch all active markets from Gamma API"""
        try:
            url = f"{config.GAMMA_HOST}/markets"
            params = {
                "active": "true",
                "closed": "false",
                "limit": 500,
                "order": "volume24hr",
                "ascending": "false"
            }
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Scanner] Error fetching Gamma markets: {e}")
            return []
    
    def get_clob_markets(self) -> List[Dict]:
        """Fetch markets from CLOB API (has live prices)"""
        try:
            url = f"{config.CLOB_HOST}/sampling-markets"
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[Scanner] Error fetching CLOB markets: {e}")
            return []
    
    def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """Fetch orderbook for a specific token"""
        try:
            url = f"{config.CLOB_HOST}/book"
            params = {"token_id": token_id}
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return None
    
    def get_best_prices(self, token_id: str) -> Dict:
        """Get best bid/ask prices for a token"""
        orderbook = self.get_orderbook(token_id)
        if not orderbook:
            return {"bid": None, "ask": None}
        
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        best_bid = max([float(b["price"]) for b in bids]) if bids else None
        best_ask = min([float(a["price"]) for a in asks]) if asks else None
        
        return {"bid": best_bid, "ask": best_ask}
    
    def parse_prices(self, prices_raw) -> Optional[List[float]]:
        """Parse outcome prices from various formats"""
        try:
            if isinstance(prices_raw, str):
                prices = json.loads(prices_raw)
            else:
                prices = prices_raw
            
            if len(prices) != 2:
                return None
            
            return [float(prices[0]), float(prices[1])]
        except:
            return None
    
    def parse_token_ids(self, tokens_raw) -> Optional[List[str]]:
        """Parse token IDs from various formats"""
        try:
            if isinstance(tokens_raw, str):
                tokens = json.loads(tokens_raw)
            else:
                tokens = tokens_raw
            
            if len(tokens) != 2:
                return None
            
            return [str(tokens[0]), str(tokens[1])]
        except:
            return None
    
    def categorize_market(self, question: str) -> Dict:
        """Categorize a market based on its question"""
        q = question.lower()
        
        # Crypto keywords
        crypto_keywords = {
            "btc": "BTC", "bitcoin": "BTC",
            "eth": "ETH", "ethereum": "ETH",
            "sol": "SOL", "solana": "SOL",
            "crypto": "CRYPTO"
        }
        
        category = None
        for keyword, cat in crypto_keywords.items():
            if keyword in q:
                category = cat
                break
        
        # Check for price prediction
        is_price = any(term in q for term in ["price", "above", "below", "$"])
        
        # Check for short-term
        is_short_term = any(term in q for term in ["hour", "today", "15 min", "minute"])
        
        return {
            "category": category,
            "is_crypto": category is not None,
            "is_price": is_price,
            "is_short_term": is_short_term
        }
    
    def find_arbitrage_opportunities(self, 
                                     crypto_only: bool = False,
                                     min_volume: float = 0) -> List[Dict]:
        """
        Find arbitrage opportunities across all markets.
        
        Arbitrage exists when: YES_price + NO_price < 1.0
        This means you can buy both outcomes for less than $1,
        and one of them MUST pay out $1.
        """
        print(f"[Scanner] Fetching markets...")
        
        # Get markets from Gamma API (has more metadata)
        gamma_markets = self.get_gamma_markets()
        print(f"[Scanner] Found {len(gamma_markets)} Gamma markets")
        
        opportunities = []
        
        for market in gamma_markets:
            # Parse prices
            prices = self.parse_prices(market.get("outcomePrices", ""))
            if not prices:
                continue
            
            yes_price, no_price = prices
            
            # Skip invalid prices
            if yes_price <= 0 or no_price <= 0:
                continue
            if yes_price >= 1 or no_price >= 1:
                continue
            
            # Parse token IDs
            token_ids = self.parse_token_ids(market.get("clobTokenIds", ""))
            if not token_ids:
                continue
            
            # Categorize market
            question = market.get("question", "Unknown")
            cat = self.categorize_market(question)
            
            # Apply filters
            if crypto_only and not cat["is_crypto"]:
                continue
            
            volume_24h = float(market.get("volume24hr", 0) or 0)
            if volume_24h < min_volume:
                continue
            
            # Calculate arbitrage potential
            total_cost = yes_price + no_price
            
            # Gross profit: (1.0 - total_cost) / total_cost * 100
            # If total < 1.0, buying both guarantees profit
            gross_profit_pct = ((1.0 - total_cost) / total_cost) * 100
            
            # Net profit after fees (fees on entry)
            # Fee structure: ~2% taker fee on 15-min, ~1.5% on longer
            fee_pct = config.TAKER_FEE_PCT
            net_profit_pct = gross_profit_pct - fee_pct
            
            # Create opportunity object
            opp = {
                "market_id": market.get("id"),
                "condition_id": market.get("conditionId"),
                "question": question,
                "slug": market.get("slug"),
                "end_date": market.get("endDate", ""),
                "yes_token_id": token_ids[0],
                "no_token_id": token_ids[1],
                "yes_price": yes_price,
                "no_price": no_price,
                "total_cost": total_cost,
                "gross_profit_pct": gross_profit_pct,
                "net_profit_pct": net_profit_pct,
                "volume_24h": volume_24h,
                "liquidity": float(market.get("liquidity", 0) or 0),
                "is_crypto": cat["is_crypto"],
                "is_price": cat["is_price"],
                "category": cat["category"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            opportunities.append(opp)
        
        # Sort by net profit (highest first)
        opportunities.sort(key=lambda x: x["net_profit_pct"], reverse=True)
        
        print(f"[Scanner] Analyzed {len(opportunities)} valid markets")
        
        return opportunities
    
    def find_crypto_price_markets(self) -> List[Dict]:
        """Specifically find crypto price prediction markets"""
        opps = self.find_arbitrage_opportunities(crypto_only=True)
        
        # Further filter for price predictions
        price_markets = [o for o in opps if o["is_price"]]
        
        print(f"[Scanner] Found {len(price_markets)} crypto price prediction markets")
        return price_markets
    
    def verify_prices_live(self, opportunity: Dict) -> Dict:
        """Verify prices are still valid by checking orderbook"""
        yes_prices = self.get_best_prices(opportunity["yes_token_id"])
        no_prices = self.get_best_prices(opportunity["no_token_id"])
        
        opportunity["yes_bid"] = yes_prices["bid"]
        opportunity["yes_ask"] = yes_prices["ask"]
        opportunity["no_bid"] = no_prices["bid"]
        opportunity["no_ask"] = no_prices["ask"]
        
        # Recalculate with actual ask prices (what we'd pay)
        if yes_prices["ask"] and no_prices["ask"]:
            actual_total = yes_prices["ask"] + no_prices["ask"]
            opportunity["live_total_cost"] = actual_total
            opportunity["live_gross_profit_pct"] = ((1.0 - actual_total) / actual_total) * 100
            opportunity["live_net_profit_pct"] = opportunity["live_gross_profit_pct"] - config.TAKER_FEE_PCT
        
        return opportunity


if __name__ == "__main__":
    # Test scanner
    scanner = MarketScanner()
    
    print("\n" + "="*70)
    print("SCANNING ALL MARKETS FOR ARBITRAGE")
    print("="*70 + "\n")
    
    opps = scanner.find_arbitrage_opportunities()
    
    print(f"\n{'='*70}")
    print(f"TOP OPPORTUNITIES (by potential profit)")
    print(f"{'='*70}\n")
    
    for opp in opps[:20]:
        crypto_marker = f"[{opp['category']}]" if opp['is_crypto'] else ""
        profit_marker = "✅" if opp['net_profit_pct'] > config.MIN_PROFIT_PCT else "⚠️"
        
        print(f"{profit_marker} {crypto_marker} {opp['question'][:55]}...")
        print(f"   YES: ${opp['yes_price']:.4f}  NO: ${opp['no_price']:.4f}  Total: ${opp['total_cost']:.4f}")
        print(f"   Gross: {opp['gross_profit_pct']:.2f}%  Net: {opp['net_profit_pct']:.2f}%  Vol: ${opp['volume_24h']:,.0f}")
        print()
    
    # Show crypto-specific
    print(f"\n{'='*70}")
    print(f"CRYPTO MARKETS ONLY")
    print(f"{'='*70}\n")
    
    crypto_opps = [o for o in opps if o["is_crypto"]]
    for opp in crypto_opps[:10]:
        print(f"[{opp['category']}] {opp['question']}")
        print(f"   YES: ${opp['yes_price']:.4f}  NO: ${opp['no_price']:.4f}")
        print(f"   Net Profit: {opp['net_profit_pct']:.2f}%")
        print()
