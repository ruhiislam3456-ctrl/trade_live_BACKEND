from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"status": "backend running"})

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/data")
def data():
    symbol = request.args.get("symbol", "BTC-USD")
    tf = request.args.get("tf", "1m")

    tf_map = {
        "1m": 60,
        "5m": 300
    }

    granularity = tf_map.get(tf, 60)

    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": granularity}

    r = requests.get(url)
    if r.status_code != 200:
        return jsonify([])

    raw = r.json()

    candles = []
    for c in reversed(raw):
        candles.append({
            "time": int(c[0]),
            "low": float(c[1]),
            "high": float(c[2]),
            "open": float(c[3]),
            "close": float(c[4])
        })

    return jsonify(candles)

if __name__ == "__main__":
    app.run()
