from typing import Optional, List, Dict, Any
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agent.digest_agent import DigestAgent
from app.database.repository import Repository
from app.api_config import TOP_PER_SOURCE, NEWSLETTER_HOURS, TOTAL_FEATURED

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def process_digests_per_source(hours: int = None) -> dict:
    """
    Process TOP 1 article from EACH SOURCE and generate AI digests.
    
    This processes:
    - 1 YouTube video (newest from past 24 hours)
    - 1 OpenAI article (newest from past 24 hours)
    - 1 Anthropic article (newest from past 24 hours)
    - 1 F1 article (newest from past 24 hours)
    
    Total: 4 API calls (one per source)
    
    Args:
        hours: How far back to look for articles. Defaults to NEWSLETTER_HOURS (24).
    
    Returns:
        dict with results per source and overall stats
    """
    agent = DigestAgent()
    repo = Repository()
    
    if hours is None:
        hours = NEWSLETTER_HOURS
    
    logger.info(f"\n📰 CREATING DIGESTS (Top 1 from each source)")
    logger.info(f"   Period: Last {hours} hours")
    logger.info(f"   Sources: YouTube, OpenAI, Anthropic, F1")
    logger.info(f"   ⚠️  API calls: {TOTAL_FEATURED} (1 per source)\n")
    
    # Get top article from each source
    top_articles = repo.get_top_article_per_source(hours=hours)
    
    results = {
        "youtube": {"found": False, "processed": False, "article": None},
        "openai": {"found": False, "processed": False, "article": None},
        "anthropic": {"found": False, "processed": False, "article": None},
        "f1": {"found": False, "processed": False, "article": None},
        "total_found": 0,
        "total_processed": 0,
        "total_failed": 0
    }
    
    for source in ["youtube", "openai", "anthropic", "f1"]:
        article = top_articles.get(source)
        
        if article:
            results[source]["found"] = True
            results["total_found"] += 1
            
            article_title = article["title"][:50] + "..." if len(article["title"]) > 50 else article["title"]
            logger.info(f"🎯 [{source.upper()}] {article_title}")
            
            try:
                digest_result = agent.generate_digest(
                    title=article["title"],
                    content=article["content"],
                    article_type=source
                )
                
                if digest_result:
                    repo.create_digest(
                        article_type=source,
                        article_id=article["id"],
                        url=article["url"],
                        title=digest_result.title,
                        summary=digest_result.summary,
                        published_at=article.get("published_at")
                    )
                    results[source]["processed"] = True
                    results[source]["article"] = {
                        "id": article["id"],
                        "title": digest_result.title,
                        "summary": digest_result.summary,
                        "url": article["url"]
                    }
                    results["total_processed"] += 1
                    logger.info(f"   ✓ Digest created")
                else:
                    results["total_failed"] += 1
                    logger.warning(f"   ✗ Failed to generate digest")
                    
            except Exception as e:
                results["total_failed"] += 1
                logger.error(f"   ✗ Error: {e}")
        else:
            logger.info(f"⚪ [{source.upper()}] No new articles found")
    
    logger.info(f"\n📊 Summary: {results['total_processed']} digests created, "
                f"{results['total_failed']} failed, "
                f"{TOTAL_FEATURED - results['total_found']} sources had no new articles")
    
    return results


# Keep old function for backward compatibility
def process_digests(hours: int = None, limit: int = None) -> dict:
    """Backward compatible wrapper."""
    result = process_digests_per_source(hours=hours)
    return {
        "total": result["total_found"],
        "processed": result["total_processed"],
        "failed": result["total_failed"]
    }


if __name__ == "__main__":
    print(f"\n📊 Configuration:")
    print(f"   Period: {NEWSLETTER_HOURS} hours")
    print(f"   Top per source: {TOP_PER_SOURCE}")
    print(f"   Total API calls: {TOTAL_FEATURED}\n")
    
    result = process_digests_per_source()
    
    print(f"\n📝 Results:")
    for source in ["youtube", "openai", "anthropic", "f1"]:
        status = "✓" if result[source]["processed"] else ("⚪" if not result[source]["found"] else "✗")
        print(f"   {status} {source.upper()}: {'Created' if result[source]['processed'] else 'Skipped'}")
    print(f"\n   Total: {result['total_processed']}/{result['total_found']} processed")
