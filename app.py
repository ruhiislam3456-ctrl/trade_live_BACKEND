from flask import Flask, jsonify, request
from flask_cors import CORS
from market import get_candles

app = Flask(__name__)
CORS(app)

@app.route("/data")
def data():
    symbol = request.args.get("symbol", "BTC-USD")
    tf = int(request.args.get("tf", "60"))
    return jsonify(get_candles(symbol, tf))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)