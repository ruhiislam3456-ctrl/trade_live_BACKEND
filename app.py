from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)

# ✅ CORS ENABLE (ALL ORIGINS)
CORS(app)

@app.route("/")
def home():
    return "Backend running with CORS"

@app.route("/data")
def data():
    try:
        symbol = request.args.get("symbol", "BTC-USD")
        tf = request.args.get("tf", "1m")

        if tf == "1m":
            granularity = 60
        elif tf == "5m":
            granularity = 300
        else:
            granularity = 60

        url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
        params = {
            "granularity": granularity,
            "limit": 100
        }

        r = requests.get(url, params=params, timeout=10)
        candles = r.json()

        if not isinstance(candles, list):
            return jsonify({"error": candles}), 500

        data = []
        for c in candles[::-1]:
            data.append({
                "time": int(c[0]),
                "open": float(c[3]),
                "high": float(c[2]),
                "low": float(c[1]),
                "close": float(c[4])
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
