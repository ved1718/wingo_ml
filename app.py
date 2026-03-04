from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from predictor import predict_next
from scraper import fetch_wingo_history

app = Flask(__name__)
DEFAULT_URL = "https://goaok.bet/#/saasLottery/WinGo?gameCode=WinGo_1M&lottery=WinGo"


@app.get("/")
def home():
    return render_template("index.html", default_url=DEFAULT_URL)


@app.post("/api/predict")
def predict_api():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url") or DEFAULT_URL
    limit = int(payload.get("limit", 50))

    try:
        history = fetch_wingo_history(url=url, limit=limit)
        prediction = predict_next(history)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify(
        {
            "ok": True,
            "history": history,
            "prediction": {
                "next_color": {
                    "label": prediction.next_color.label,
                    "probability": round(prediction.next_color.probability, 4),
                },
                "next_size": {
                    "label": prediction.next_size.label,
                    "probability": round(prediction.next_size.probability, 4),
                },
                "samples_used": prediction.samples_used,
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
