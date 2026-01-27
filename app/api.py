"""
Flask API for triggering the newsletter pipeline on Render.

Endpoints:
- GET /health — Health check (for Render).
- POST /trigger-newsletter — Run the full pipeline (scrape → process → send to MY_EMAIL).
  Optional X-Cron-Secret header when CRON_SECRET is set.
"""

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


@app.route("/trigger-newsletter", methods=["POST"])
def trigger_newsletter():
    """
    Run the full newsletter pipeline (scrape → process → send to MY_EMAIL).

    Used by Render cron jobs or external cron services.
    When CRON_SECRET is set, require X-Cron-Secret header.
    """
    cron_secret = os.getenv("CRON_SECRET")
    if cron_secret:
        provided = request.headers.get("X-Cron-Secret")
        if request.is_json:
            provided = provided or request.json.get("secret")
        if provided != cron_secret:
            return jsonify({"error": "Unauthorized"}), 401

    try:
        from app.daily_runner import run_daily_pipeline

        result = run_daily_pipeline()
        return jsonify({
            "success": result.get("success", False),
            "message": "Pipeline executed",
            "details": {
                "duration_seconds": result.get("duration_seconds"),
                "newsletter": result.get("newsletter"),
                "scraping": result.get("scraping"),
                "digests": result.get("digests"),
            },
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
