"""
Import subscribers from Google Sheets (published as CSV).

The Google Form collects: Email, Preferred Name, Topics (checkboxes).
Apps Script syncs to a Subscribers sheet. Publish that sheet as CSV.
This script fetches the CSV URL and upserts into the subscribers table.

Set SUBSCRIBERS_CSV_URL in .env (from File → Share → Publish to web).
"""

import csv
import io
import logging
import os
from dotenv import load_dotenv
import requests

load_dotenv()

from app.database.repository import Repository
from app.database.models import Subscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_bool(val) -> bool:
    """Parse string to bool (handles true/false, 1/0, yes/no)."""
    if val is None or str(val).strip() == "":
        return True
    s = str(val).lower().strip()
    return s in ("true", "1", "yes", "y")


def import_subscribers(csv_url: str = None) -> dict:
    """
    Fetch CSV from URL and upsert subscribers into the database.

    Expected CSV columns (case-insensitive): email, preferred_name, youtube, openai, anthropic, f1

    Args:
        csv_url: Override URL. Defaults to SUBSCRIBERS_CSV_URL env var.

    Returns:
        dict with imported, updated, skipped, errors counts
    """
    url = csv_url or os.getenv("SUBSCRIBERS_CSV_URL")
    if not url:
        logger.warning("SUBSCRIBERS_CSV_URL not set. Skipping import.")
        return {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

    repo = Repository()
    results = {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch CSV: {e}")
        results["errors"] = 1
        return results

    try:
        content = resp.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        results["errors"] = 1
        return results

    if not rows:
        logger.info("CSV is empty. No subscribers to import.")
        return results

    # Normalize column names (allow email, Email, preferred_name, Preferred Name, etc.)
    def norm_key(k):
        return (k or "").strip().lower().replace(" ", "_").replace("-", "_")

    for row in rows:
        try:
            row_norm = {norm_key(k): v for k, v in row.items()}
            email = (row_norm.get("email") or "").strip()
            if not email or "@" not in email:
                results["skipped"] += 1
                continue

            preferred_name = (row_norm.get("preferred_name") or "there").strip() or "there"
            youtube = _parse_bool(row_norm.get("youtube"))
            openai = _parse_bool(row_norm.get("openai"))
            anthropic = _parse_bool(row_norm.get("anthropic"))
            f1 = _parse_bool(row_norm.get("f1"))

            existing_sub = repo.session.query(Subscriber).filter_by(email=email).first()

            if existing_sub:
                repo.upsert_subscriber(
                    email=email,
                    preferred_name=preferred_name,
                    youtube=youtube,
                    openai=openai,
                    anthropic=anthropic,
                    f1=f1,
                    active=True,
                )
                results["updated"] += 1
                logger.info(f"Updated: {email}")
            else:
                repo.upsert_subscriber(
                    email=email,
                    preferred_name=preferred_name,
                    youtube=youtube,
                    openai=openai,
                    anthropic=anthropic,
                    f1=f1,
                    active=True,
                )
                results["imported"] += 1
                logger.info(f"Imported: {email}")

        except Exception as e:
            results["errors"] += 1
            logger.warning(f"Error processing row {row}: {e}")

    logger.info(
        f"Import complete: {results['imported']} imported, {results['updated']} updated, "
        f"{results['skipped']} skipped, {results['errors']} errors"
    )
    return results


if __name__ == "__main__":
    r = import_subscribers()
    print(f"\n📊 Import results: {r}")
