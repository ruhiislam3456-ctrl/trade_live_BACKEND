from flask import Flask, jsonify, request
from flask_cors import CORS
import websocket
import threading
import json
import time
import collections

app = Flask(__name__)
CORS(app)

# =========================
# GLOBAL STATE
# =========================
STATE = {}
HISTORY = collections.defaultdict(list)

# =========================
# COINBASE WEBSOCKET
# =========================
def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") != "ticker":
        return

    symbol = data["product_id"]
    price = float(data["price"])
    ts = int(time.time())
    candle_time = ts - (ts % 60)

    candle = STATE.get(symbol)

    if candle is None or candle["time"] != candle_time:
        candle = {
            "time": candle_time,
            "open": price,
            "high": price,
            "low": price,
            "close": price
        }
        STATE[symbol] = candle
    else:
        candle["high"] = max(candle["high"], price)
        candle["low"] = min(candle["low"], price)
        candle["close"] = price

    prices = HISTORY[symbol]
    prices.append(price)
    if len(prices) > 100:
        prices.pop(0)

    def ema(period):
        if len(prices) < period:
            return None
        k = 2 / (period + 1)
        e = prices[0]
        for p in prices[1:]:
            e = p * k + e * (1 - k)
        return round(e, 2)

    candle["ema9"] = ema(9)
    candle["ema21"] = ema(21)

    if candle["ema9"] and candle["ema21"]:
        candle["trend"] = "BULLISH" if candle["ema9"] > candle["ema21"] else "BEARISH"
    else:
        candle["trend"] = "WAIT"


def ws_thread():
    ws = websocket.WebSocketApp(
        "wss://ws-feed.exchange.coinbase.com",
        on_message=on_message
    )

    sub = {
        "type": "subscribe",
        "channels": [{
            "name": "ticker",
            "product_ids": [
                "BTC-USD", "ETH-USD", "BNB-USD",
                "SOL-USD", "XRP-USD", "ADA-USD"
            ]
        }]
    }

    ws.on_open = lambda ws: ws.send(json.dumps(sub))
    ws.run_forever()


threading.Thread(target=ws_thread, daemon=True).start()

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return jsonify({"status": "live backend running"})

@app.route("/live")
def live():
    symbol = request.args.get("symbol", "BTC-USD")
    c = STATE.get(symbol)
    if not c:
        return jsonify([])
    return jsonify([c])

@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
