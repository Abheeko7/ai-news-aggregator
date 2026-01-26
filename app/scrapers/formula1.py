"""
Formula 1 RSS Feed Scraper
==========================
Scrapes the latest F1 news from the official Formula 1 RSS feed.

Note: The F1 RSS feed doesn't include publication dates, so we use
the scrape time as the published_at timestamp. Deduplication is
handled by GUID in the repository layer.
"""

from datetime import datetime, timezone
from typing import List, Optional
import feedparser
from pydantic import BaseModel


class F1Article(BaseModel):
    """Model for a Formula 1 article."""
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    author: Optional[str] = None


class Formula1Scraper:
    """Scraper for the official Formula 1 RSS feed."""
    
    def __init__(self):
        self.rss_url = "https://www.formula1.com/en/latest/all.xml"

    def get_articles(self, hours: int = 168) -> List[F1Article]:
        """
        Fetch articles from the F1 RSS feed.
        
        Note: The F1 feed doesn't have publication dates, so ALL articles
        in the feed are returned with the current timestamp. Deduplication
        by GUID happens in the repository layer to prevent duplicates.
        
        Args:
            hours: Not used for filtering (kept for API consistency)
        
        Returns:
            List of F1Article objects
        """
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            return []
        
        # Current time for articles without dates
        now = datetime.now(timezone.utc)
        articles = []
        
        for entry in feed.entries:
            # Try to get published date (F1 feed doesn't have it, but check anyway)
            published_parsed = getattr(entry, "published_parsed", None)
            
            if published_parsed:
                # If date exists, use it
                published_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            else:
                # No date - use current time (will be deduplicated by GUID)
                published_time = now
            
            # Extract author
            author = entry.get("author", entry.get("dc_creator", "Formula 1"))
            
            articles.append(F1Article(
                title=entry.get("title", ""),
                description=entry.get("summary", entry.get("description", "")),
                url=entry.get("link", ""),
                guid=entry.get("id", entry.get("link", "")),
                published_at=published_time,
                author=author
            ))
        
        return articles


if __name__ == "__main__":
    scraper = Formula1Scraper()
    articles = scraper.get_articles()
    
    print(f"\n🏎️  Found {len(articles)} F1 articles:\n")
    for i, article in enumerate(articles, 1):
        print(f"[{i}] {article.title}")
        print(f"    URL: {article.url}")
        print(f"    Author: {article.author}")
        print()
