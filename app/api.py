"""
Flask API for triggering the newsletter pipeline on Render.

Endpoints:
- GET /health — Health check (for Render).
- POST /trigger-newsletter — Run the full pipeline (scrape → process → send).
  Returns 202 immediately; pipeline runs in background (avoids 502 timeout).
  Optional X-Cron-Secret header when CRON_SECRET is set.
"""

import threading
from flask import Flask, request, jsonify
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route("/health")
def health():
    """Health check for Render."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


def _run_pipeline_background():
    """Run the full pipeline in a background thread (avoids HTTP timeout)."""
    try:
        from app.daily_runner import run_daily_pipeline
        run_daily_pipeline()
    except Exception as e:
        import logging
        logging.error(f"Background pipeline failed: {e}")


@app.route("/trigger-newsletter", methods=["POST"])
def trigger_newsletter():
    """
    Start the newsletter pipeline in the background and return immediately.
    Returns 202 Accepted to avoid 502 timeout (pipeline can take 5-10+ min).
    """
    cron_secret = os.getenv("CRON_SECRET")
    if cron_secret:
        provided = request.headers.get("X-Cron-Secret")
        if request.is_json:
            provided = provided or request.json.get("secret")
        if provided != cron_secret:
            return jsonify({"error": "Unauthorized"}), 401

    thread = threading.Thread(target=_run_pipeline_background, daemon=True)
    thread.start()
    return jsonify({
        "success": True,
        "message": "Pipeline started in background",
        "status": "accepted",
    }), 202


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
