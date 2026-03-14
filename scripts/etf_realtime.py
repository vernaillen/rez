#!/usr/bin/env python3
"""Fetch real-time ETF prices from JustETF WebSocket API."""
import sys
import json
import asyncio

async def get_etf_price(isin: str, currency: str = "EUR") -> dict:
    """Fetch real-time ETF price from JustETF."""
    try:
        import websockets
    except ImportError:
        raise ImportError("Run with: uv run --with websockets")
    
    url = f"wss://api.mobile.stock-data-subscriptions.justetf.com/?subscription=trend&parameters=isins:{isin}/currency:{currency}/language:en"
    
    async with websockets.connect(url) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        return json.loads(msg)

async def get_multiple_etfs(isins: list[str], currency: str = "EUR") -> list[dict]:
    """Fetch multiple ETFs."""
    results = []
    for isin in isins:
        try:
            data = await get_etf_price(isin, currency)
            results.append({
                'isin': data['isin'],
                'ask': data['ask']['raw'],
                'bid': data['bid']['raw'],
                'mid': data['mid']['raw'],
                'change_pct': data['dtdPrc']['raw'],
                'change_amt': data['dtdAmt']['raw'],
                'spread_pct': data['spreadPrc']['raw'],
                'exchange': data['stockExchange'],
                'timestamp': data['timestamp']
            })
        except Exception as e:
            results.append({'isin': isin, 'error': str(e)})
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: etf_realtime.py <ISIN> [ISIN2] ...")
        print("Example: etf_realtime.py IE0009JOT9U1 IE00B4ND3602")
        sys.exit(1)
    
    isins = sys.argv[1:]
    results = asyncio.run(get_multiple_etfs(isins))
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
