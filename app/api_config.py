"""
API Rate Limit Configuration
============================
Configure these settings based on your Gemini API free tier limits.

This module is imported by:
- app/services/process_digest.py
- app/services/process_curator.py
- app/services/process_email.py
- app/daily_runner.py
"""

# =============================================================================
# API LIMITS
# =============================================================================

# Daily API request limit (Gemini free tier)
DAILY_API_LIMIT = 15

# =============================================================================
# DATA RETENTION CONFIGURATION
# =============================================================================

# How long to keep data in the database (in hours)
# 168 hours = 7 days
# Data older than this will be automatically deleted during pipeline runs
DATA_RETENTION_HOURS = 168

# =============================================================================
# SCRAPING CONFIGURATION
# =============================================================================

# How far back to scrape articles (in hours)
# 24 hours = daily newsletter with past day's content
SCRAPE_HOURS = 24

# =============================================================================
# NEWSLETTER CONFIGURATION
# =============================================================================

# Only include articles from the last N hours in the newsletter
# 24 hours = past day's content
NEWSLETTER_HOURS = 24

# Fallback: when no fresh content in NEWSLETTER_HOURS, look back this far for latest available
# 168 hours = 7 days - ensures we always show something even when sources have no new posts
NEWSLETTER_LOOKBACK_HOURS = 168

# TOP article from EACH SOURCE gets AI-generated summary
# 1 from YouTube + 1 from OpenAI + 1 from Anthropic + 1 from F1 = 4 API calls
TOP_PER_SOURCE = 1

# Number of sources
NUM_SOURCES = 4  # YouTube, OpenAI, Anthropic, F1

# Total featured articles with AI summaries
TOTAL_FEATURED = TOP_PER_SOURCE * NUM_SOURCES  # = 4

# Additional articles shown as links only (no API calls)
# These appear below the featured articles as "More Articles"
ADDITIONAL_LINKS_PER_SOURCE = 3


# =============================================================================
# API CALLS BREAKDOWN
# =============================================================================
# 
# Per pipeline run:
# - DigestAgent: TOTAL_FEATURED calls (1 per source × 4 sources) = 4 calls
# - CuratorAgent: 1 call (ranks featured articles)
# - EmailAgent: 1 call (generates email intro)
# 
# Total per run = TOTAL_FEATURED + 2 = 6 API calls
# 
# With DAILY_API_LIMIT = 15:
# Possible runs per day = 15 / 6 = 2 runs
# =============================================================================


def get_estimated_calls() -> int:
    """Calculate estimated API calls per pipeline run."""
    return TOTAL_FEATURED + 2  # digest + curator + email


def get_runs_per_day() -> int:
    """Calculate how many pipeline runs possible per day."""
    return DAILY_API_LIMIT // get_estimated_calls()


def print_config():
    """Print current API configuration."""
    print("\n" + "=" * 50)
    print("API CONFIGURATION")
    print("=" * 50)
    print(f"Data retention:         {DATA_RETENTION_HOURS} hours ({DATA_RETENTION_HOURS // 24} days)")
    print(f"Daily API limit:        {DAILY_API_LIMIT} requests")
    scrape_desc = f"{SCRAPE_HOURS // 24} day" if SCRAPE_HOURS >= 24 else f"{SCRAPE_HOURS} hours"
    print(f"Scrape period:          {SCRAPE_HOURS} hours ({scrape_desc})")
    print(f"Newsletter period:      {NEWSLETTER_HOURS} hours (1 day)")
    print(f"Featured per source:    {TOP_PER_SOURCE}")
    print(f"Total featured (AI):    {TOTAL_FEATURED} (1 per source)")
    print(f"Additional links/src:   {ADDITIONAL_LINKS_PER_SOURCE}")
    print(f"API calls per run:      {get_estimated_calls()}")
    print(f"Possible runs/day:      {get_runs_per_day()}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print_config()
