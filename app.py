from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)  # CORS FIX – Netlify / Mobile / Browser সব ঠিক

# -------------------------
# HOME TEST ROUTE
# -------------------------
@app.route("/")
def home():
    return jsonify({"status": "backend running"})


# -------------------------
# FAVICON FIX (OPTIONAL)
# -------------------------
@app.route("/favicon.ico")
def favicon():
    return "", 204


# -------------------------
# LIVE MARKET DATA
# -------------------------
@app.route("/data")
def data():
    symbol = request.args.get("symbol", "BTC-USD")
    tf = request.args.get("tf", "1m")

    # timeframe mapping (seconds)
    tf_map = {
        "1m": 60,
        "5m": 300
    }

    granularity = tf_map.get(tf, 60)

    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {
        "granularity": granularity
    }

    r = requests.get(url, params=params)
    if r.status_code != 200:
        return jsonify([])

    raw = r.json()

    candles = []
    for c in raw[::-1]:  # reverse for chart
        candles.append({
            "time": int(c[0]),
            "low": c[1],
            "high": c[2],
            "open": c[3],
            "close": c[4]
        })

    return jsonify(candles)


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
