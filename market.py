import requests

def get_candles(symbol="BTC-USD", granularity=60):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": granularity}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    candles = []
    for c in reversed(data):
        candles.append({
            "time": int(c[0]),
            "low": float(c[1]),
            "high": float(c[2]),
            "open": float(c[3]),
            "close": float(c[4])
        })
    return candles