#!/usr/bin/env python3
"""
Cross-Platform Arbitrage Scanner
Compares prices between Polymarket and Kalshi

⚠️ CRITICAL: For arbitrage to work, markets must be IDENTICAL - same event,
same resolution criteria, same date. This scanner uses strict matching.
"""

import requests
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Set
from difflib import SequenceMatcher


class CrossPlatformScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ArbBot/1.0",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        })
    
    def get_polymarket_markets(self, limit: int = 200) -> List[Dict]:
        """Fetch active markets from Polymarket"""
        try:
            resp = self.session.get(
                "https://gamma-api.polymarket.com/markets",
                params={
                    "active": "true",
                    "closed": "false", 
                    "limit": limit,
                    "order": "volume24hr",
                    "ascending": "false"
                },
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Polymarket] Error: {e}")
            return []
    
    def get_kalshi_markets(self, limit: int = 200) -> List[Dict]:
        """Fetch markets from Kalshi with prices"""
        try:
            all_markets = []
            cursor = None
            
            while len(all_markets) < limit:
                params = {
                    "limit": 100,
                    "status": "open",
                    "with_nested_markets": "true"
                }
                if cursor:
                    params["cursor"] = cursor
                
                resp = self.session.get(
                    "https://api.elections.kalshi.com/trade-api/v2/events",
                    params=params,
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                events = data.get("events", [])
                
                for event in events:
                    event_title = event.get("title", "")
                    for m in event.get("markets", []):
                        title = m.get("title") or m.get("subtitle") or event_title
                        yes_ask = (m.get("yes_ask") or 0) / 100
                        no_ask = (m.get("no_ask") or 0) / 100
                        liquidity = (m.get("liquidity") or 0) / 100
                        
                        if liquidity > 50:
                            all_markets.append({
                                "ticker": m.get("ticker"),
                                "title": title,
                                "event": event_title,
                                "yes_ask": yes_ask,
                                "no_ask": no_ask,
                                "liquidity": liquidity,
                            })
                
                cursor = data.get("cursor")
                if not cursor or not events:
                    break
            
            return all_markets[:limit]
        except Exception as e:
            print(f"[Kalshi] Error: {e}")
            return []
    
    def extract_key_entities(self, text: str) -> Set[str]:
        """Extract key entities (names, dates, numbers) from text"""
        text = text.lower()
        entities = set()
        
        # Extract names (capitalized words in original)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.update(n.lower() for n in names)
        
        # Extract numbers and dates
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?%?\b', text)
        entities.update(numbers)
        
        # Extract dollar amounts
        dollars = re.findall(r'\$[\d,]+(?:\.\d+)?[kmb]?', text)
        entities.update(dollars)
        
        # Extract dates
        dates = re.findall(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s*\d{1,2}(?:,?\s*\d{4})?\b', text)
        entities.update(dates)
        
        # Extract years
        years = re.findall(r'\b20\d{2}\b', text)
        entities.update(years)
        
        # Key topic words
        topics = ['bitcoin', 'btc', 'ethereum', 'eth', 'trump', 'biden', 'fed', 'shutdown',
                 'election', 'president', 'prime minister', 'war', 'ukraine', 'russia',
                 'china', 'israel', 'iran', 'pope', 'fed chair', 'interest rate']
        for topic in topics:
            if topic in text:
                entities.add(topic)
        
        return entities
    
    def strict_match_score(self, text1: str, text2: str) -> float:
        """
        Calculate strict match score based on:
        1. Key entity overlap (must share most entities)
        2. Text similarity
        """
        t1 = text1.lower()
        t2 = text2.lower()
        
        # Extract entities
        ent1 = self.extract_key_entities(text1)
        ent2 = self.extract_key_entities(text2)
        
        if not ent1 or not ent2:
            return 0.0
        
        # Entity overlap (Jaccard)
        overlap = len(ent1 & ent2)
        union = len(ent1 | ent2)
        entity_score = overlap / union if union > 0 else 0
        
        # Must have significant entity overlap
        if entity_score < 0.3:
            return 0.0
        
        # Text similarity
        text_score = SequenceMatcher(None, t1, t2).ratio()
        
        # Combined score (entities are more important)
        return (entity_score * 0.7) + (text_score * 0.3)
    
    def find_identical_markets(self, poly_markets: List[Dict], 
                               kalshi_markets: List[Dict],
                               min_score: float = 0.65) -> List[Dict]:
        """Find markets that are likely IDENTICAL (same event)"""
        matches = []
        
        for pm in poly_markets:
            poly_q = pm.get("question", "")
            if not poly_q:
                continue
            
            # Parse Polymarket prices
            try:
                prices = json.loads(pm.get("outcomePrices", "[]"))
                if len(prices) != 2:
                    continue
                poly_yes = float(prices[0])
                poly_no = float(prices[1])
                if poly_yes == 0 and poly_no == 0:
                    continue
            except:
                continue
            
            # Find best Kalshi match with strict matching
            best_match = None
            best_score = 0
            
            for km in kalshi_markets:
                # Use BOTH event title and market title for matching
                kalshi_text = f"{km['event']} {km['title']}"
                
                score = self.strict_match_score(poly_q, kalshi_text)
                if score > best_score and score >= min_score:
                    best_score = score
                    best_match = km
            
            if best_match:
                matches.append({
                    "match_score": best_score,
                    "polymarket": {
                        "question": poly_q,
                        "yes": poly_yes,
                        "no": poly_no,
                        "volume": float(pm.get("volume24hr", 0) or 0),
                    },
                    "kalshi": {
                        "title": best_match["title"],
                        "event": best_match["event"],
                        "yes_ask": best_match["yes_ask"],
                        "no_ask": best_match["no_ask"],
                        "liquidity": best_match["liquidity"],
                    }
                })
        
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
    
    def calculate_arbitrage(self, match: Dict) -> Dict:
        """Calculate potential arbitrage"""
        p = match["polymarket"]
        k = match["kalshi"]
        
        # Option 1: Kalshi YES + Polymarket NO
        opt1_cost = k["yes_ask"] + p["no"]
        opt1_profit = ((1.0 - opt1_cost) / opt1_cost * 100) if 0 < opt1_cost < 1 else -100
        
        # Option 2: Polymarket YES + Kalshi NO
        opt2_cost = p["yes"] + k["no_ask"]
        opt2_profit = ((1.0 - opt2_cost) / opt2_cost * 100) if 0 < opt2_cost < 1 else -100
        
        if opt1_profit > opt2_profit:
            best = {
                "strategy": "Buy YES@Kalshi + NO@Polymarket",
                "total_cost": opt1_cost,
                "gross_profit_pct": opt1_profit,
            }
        else:
            best = {
                "strategy": "Buy YES@Polymarket + NO@Kalshi", 
                "total_cost": opt2_cost,
                "gross_profit_pct": opt2_profit,
            }
        
        best["net_profit_pct"] = best["gross_profit_pct"] - 3.0  # ~3% total fees
        return best
    
    def scan(self, min_score: float = 0.65) -> List[Dict]:
        """Run cross-platform scan with strict matching"""
        print(f"[Scanner] Fetching Polymarket markets...")
        poly_markets = self.get_polymarket_markets(300)
        print(f"[Scanner] Found {len(poly_markets)} Polymarket markets")
        
        print(f"[Scanner] Fetching Kalshi markets...")
        kalshi_markets = self.get_kalshi_markets(500)
        print(f"[Scanner] Found {len(kalshi_markets)} Kalshi markets")
        
        print(f"[Scanner] Finding identical markets (min {min_score:.0%} match score)...")
        matches = self.find_identical_markets(poly_markets, kalshi_markets, min_score)
        print(f"[Scanner] Found {len(matches)} potential identical markets")
        
        for match in matches:
            match["arbitrage"] = self.calculate_arbitrage(match)
        
        matches.sort(key=lambda x: x["arbitrage"]["net_profit_pct"], reverse=True)
        return matches


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║         CROSS-PLATFORM ARBITRAGE SCANNER                              ║
║         Polymarket <-> Kalshi                                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  ⚠️  IMPORTANT: True arbitrage requires IDENTICAL markets.            ║
║                                                                       ║
║  In practice, Polymarket and Kalshi have almost no overlap:           ║
║    • Polymarket: Crypto, sports betting, viral events                 ║
║    • Kalshi: US politics, economics, entertainment dates              ║
║                                                                       ║
║  This scanner shows SIMILAR markets, but similarity ≠ identical.      ║
║  Manual verification required before any cross-platform trade.        ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    scanner = CrossPlatformScanner()
    matches = scanner.scan(min_score=0.60)
    
    print(f"\n{'═'*75}")
    print(f"  IDENTICAL MARKETS FOUND: {len(matches)}")
    print(f"{'═'*75}\n")
    
    if not matches:
        print("  No identical markets found between platforms.")
        print("  This is expected - Polymarket and Kalshi have different market focuses:")
        print("    • Polymarket: Crypto, politics, sports")
        print("    • Kalshi: Politics, economics, entertainment, weather")
        print("\n  True cross-platform arbitrage is rare because:")
        print("    1. Markets are usually platform-exclusive")
        print("    2. Even similar markets have different resolution criteria")
        print("    3. Timing and settlement rules differ")
        return
    
    for i, m in enumerate(matches[:15]):
        p = m["polymarket"]
        k = m["kalshi"]
        arb = m["arbitrage"]
        score = m["match_score"]
        
        net = arb["net_profit_pct"]
        marker = "✅" if net > 0 else "⚠️"
        
        print(f"{marker} Match Score: {score:.0%}")
        print(f"├─ Polymarket: {p['question'][:60]}...")
        print(f"│  YES: ${p['yes']:.4f}  NO: ${p['no']:.4f}")
        print(f"├─ Kalshi: {k['title'][:60]}...")
        print(f"│  YES: ${k['yes_ask']:.4f}  NO: ${k['no_ask']:.4f}")
        print(f"└─ {arb['strategy']}")
        print(f"   Total: ${arb['total_cost']:.4f}  Net: {net:.2f}%")
        print()
    
    # Summary
    profitable = [m for m in matches if m["arbitrage"]["net_profit_pct"] > 0]
    print(f"{'═'*75}")
    print(f"  Identical markets: {len(matches)}")
    print(f"  Profitable: {len(profitable)}")


if __name__ == "__main__":
    main()
