from flask import Flask, jsonify, request
from flask_cors import CORS
import websocket, json, threading, time, math

app = Flask(__name__)
CORS(app)

TF = 60  # 1m
STATE = {}  # per pair state

def ema(prev, price, period):
    k = 2 / (period + 1)
    return price * k + prev * (1 - k)

def ws_runner(pair):
    def on_message(ws, msg):
        data = json.loads(msg)
        if data.get("type") != "ticker":
            return

        price = float(data["price"])
        now = int(time.time())
        s = STATE[pair]

        if s["start"] is None:
            s["start"] = now - (now % TF)
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
        if now >= s["start"] + TF:
            s["start"] += TF
            s["candle"] = {
                "time": s["start"],
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

        c = s["candle"]
        c["close"] = price
        c["high"] = max(c["high"], price)
        c["low"] = min(c["low"], price)

        s["ema9"] = ema(s["ema9"], price, 9)
        s["ema21"] = ema(s["ema21"], price, 21)

    ws = websocket.WebSocketApp(
        "wss://ws-feed.exchange.coinbase.com",
        on_message=on_message
    )

    ws.on_open = lambda ws: ws.send(json.dumps({
        "type": "subscribe",
        "channels": [{"name": "ticker", "product_ids": [pair]}]
    }))

    ws.run_forever()

def start_pair(pair):
    STATE[pair] = {
        "start": None,
        "candle": None,
        "ema9": None,
        "ema21": None
    }
    threading.Thread(target=ws_runner, args=(pair,), daemon=True).start()

for p in ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD"]:
    start_pair(p)

@app.route("/live")
def live():
    pair = request.args.get("pair", "BTC-USD")
    s = STATE.get(pair)

    if not s or not s["candle"]:
        return jsonify({"status": "waiting"})

    c = s["candle"]
    body = abs(c["close"] - c["open"])
    rng = c["high"] - c["low"]
    strength = round((body / rng) * 100, 2) if rng else 0

    trend = "SIDEWAYS"
    if s["ema9"] > s["ema21"]:
        trend = "BULL"
    elif s["ema9"] < s["ema21"]:
        trend = "BEAR"

    highlight = strength > 70 and trend != "SIDEWAYS"

    return jsonify({
        "time": c["time"],
        "open": c["open"],
        "high": c["high"],
        "low": c["low"],
        "close": c["close"],
        "ema9": round(s["ema9"], 2),
        "ema21": round(s["ema21"], 2),
        "trend": trend,
        "strength": strength,
        "highlight": highlight
    })

if __name__ == "__main__":
    app.run()

