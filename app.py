from flask import Flask, jsonify, request
from flask_cors import CORS
import threading, time, json
import websocket

app = Flask(__name__)
CORS(app)

TIMEFRAME = 60  # 1 minute candle

STATE = {}

PAIRS = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD"]

def ema(prev, price, period):
    k = 2 / (period + 1)
    return price * k + prev * (1 - k)

def start_ws(pair):
    def on_message(ws, message):
        data = json.loads(message)
        if data.get("type") != "ticker":
            return

        price = float(data["price"])
        now = int(time.time())

        s = STATE[pair]

        # first tick
        if s["start"] is None:
            s["start"] = now - (now % TIMEFRAME)
            s["candle"] = {
                "time": s["start"],
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }
            s["ema9"] = price
            s["ema21"] = price
            return

        # new candle
        if now >= s["start"] + TIMEFRAME:
            s["start"] += TIMEFRAME
            s["candle"] = {
                "time": s["start"],
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

        c = s["candle"]
        c["close"] = price
        if price > c["high"]:
            c["high"] = price
        if price < c["low"]:
            c["low"] = price

        s["ema9"] = ema(s["ema9"], price, 9)
        s["ema21"] = ema(s["ema21"], price, 21)

    def on_open(ws):
        ws.send(json.dumps({
            "type": "subscribe",
            "channels": [{
                "name": "ticker",
                "product_ids": [pair]
            }]
        }))

    ws = websocket.WebSocketApp(
        "wss://ws-feed.exchange.coinbase.com",
        on_open=on_open,
        on_message=on_message
    )

    ws.run_forever()

def init_pair(pair):
    STATE[pair] = {
        "start": None,
        "candle": None,
        "ema9": None,
        "ema21": None
    }
    threading.Thread(target=start_ws, args=(pair,), daemon=True).start()

for p in PAIRS:
    init_pair(p)

@app.route("/live")
def live():
    pair = request.args.get("pair", "BTC-USD")

    if pair not in STATE:
        return jsonify({"error": "pair not supported"})

    s = STATE[pair]
    c = s["candle"]

    if c is None:
        return jsonify({"status": "waiting"})

    body = abs(c["close"] - c["open"])
    rng = c["high"] - c["low"]
    strength = round((body / rng) * 100, 2) if rng != 0 else 0

    trend = "SIDEWAYS"
    if s["ema9"] > s["ema21"]:
        trend = "BULL"
    elif s["ema9"] < s["ema21"]:
        trend = "BEAR"

    highlight = strength >= 70 and trend != "SIDEWAYS"

    return jsonify({
        "time": c["time"],
        "open": round(c["open"], 2),
        "high": round(c["high"], 2),
        "low": round(c["low"], 2),
        "close": round(c["close"], 2),
        "ema9": round(s["ema9"], 2),
        "ema21": round(s["ema21"], 2),
        "trend": trend,
        "strength": strength,
        "highlight": highlight
    })

@app.route("/")
def root():
    return jsonify({"status": "backend running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
