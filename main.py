from app.daily_runner import run_daily_pipeline


def main():
    """
    Run the daily newsletter pipeline.
    
    Configuration is now managed via app/api_config.py:
    - SCRAPE_HOURS: How far back to scrape (default: 24 hours)
    - NEWSLETTER_HOURS: Articles to include in newsletter (default: 24 hours)
    - DATA_RETENTION_HOURS: How long to keep data (default: 168 hours / 7 days)
    """
    return run_daily_pipeline()


if __name__ == "__main__":
    result = main()
    exit(0 if result["success"] else 1)

