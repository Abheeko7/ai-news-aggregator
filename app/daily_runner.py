import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.runner import run_scrapers
from app.services.process_anthropic import process_anthropic_markdown
from app.services.process_youtube import process_youtube_transcripts
from app.services.process_digest import process_digests_per_source
from app.services.process_email import send_newsletter
from app.services.import_subscribers import import_subscribers
from app.database.repository import Repository
from app.api_config import (
    SCRAPE_HOURS, NEWSLETTER_HOURS, TOP_PER_SOURCE, TOTAL_FEATURED,
    ADDITIONAL_LINKS_PER_SOURCE, DAILY_API_LIMIT, DATA_RETENTION_HOURS,
    get_estimated_calls
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_daily_pipeline() -> dict:
    """
    Run the complete daily newsletter pipeline.
    
    Pipeline Steps:
    0. Clean up old data (older than 7 days)
    1. Scrape articles from past week (SCRAPE_HOURS = 168)
    2. Process Anthropic markdown
    3. Process YouTube transcripts  
    4. Create AI digests for TOP 1 article from EACH SOURCE (past 24 hours)
    5. Send newsletter with featured + additional links
    
    Data Retention:
    - Automatically deletes data older than DATA_RETENTION_HOURS (7 days)
    - Keeps database size manageable
    
    Newsletter Format:
    🎬 YOUTUBE - 1 featured article with AI summary
    🤖 OPENAI - 1 featured article with AI summary
    🧠 ANTHROPIC - 1 featured article with AI summary
    📚 MORE ARTICLES - Additional links grouped by source
    
    API Usage:
    - DigestAgent: 3 calls (1 per source)
    - CuratorAgent: 1 call (via EmailAgent)
    - EmailAgent: 1 call
    Total: ~5 API calls per run
    """
    start_time = datetime.now()
    
    logger.info("=" * 60)
    logger.info("🚀 AI NEWS AGGREGATOR - DAILY PIPELINE")
    logger.info("=" * 60)
    
    # Show configuration
    estimated_calls = get_estimated_calls()
    logger.info(f"\n📊 CONFIGURATION:")
    logger.info(f"   Data retention:       {DATA_RETENTION_HOURS} hours ({DATA_RETENTION_HOURS // 24} days)")
    logger.info(f"   Scraping period:      {SCRAPE_HOURS} hours ({SCRAPE_HOURS // 24} days)")
    logger.info(f"   Newsletter period:    {NEWSLETTER_HOURS} hours")
    logger.info(f"   Featured per source:  {TOP_PER_SOURCE}")
    logger.info(f"   Total featured (AI):  {TOTAL_FEATURED}")
    logger.info(f"   Links per source:     {ADDITIONAL_LINKS_PER_SOURCE}")
    logger.info(f"   Daily API limit:      {DAILY_API_LIMIT}")
    logger.info(f"   Est. API calls:       {estimated_calls}")
    logger.info(f"   Remaining after:      ~{DAILY_API_LIMIT - estimated_calls}\n")
    
    results = {
        "start_time": start_time.isoformat(),
        "cleanup": {},
        "scraping": {},
        "processing": {},
        "digests": {},
        "newsletter": {},
        "success": False
    }
    
    repo = Repository()
    
    try:
        # Step 0: Clean up old data
        logger.info("[0/6] 🗑️  Cleaning up old data...")
        
        # Show database stats before cleanup
        stats_before = repo.get_database_stats()
        logger.info(f"      Before: YouTube={stats_before['youtube_videos']}, "
                    f"OpenAI={stats_before['openai_articles']}, "
                    f"Anthropic={stats_before['anthropic_articles']}, "
                    f"F1={stats_before['f1_articles']}, "
                    f"Digests={stats_before['digests']}")
        
        cleanup_result = repo.cleanup_all_old_data(retention_hours=DATA_RETENTION_HOURS)
        results["cleanup"] = cleanup_result

        # Step 0.5: Import subscribers from Google Sheets (if SUBSCRIBERS_CSV_URL is set)
        logger.info("\n[0.5/6] 📥 Importing subscribers from Google Sheets...")
        try:
            import_result = import_subscribers()
            results["import_subscribers"] = import_result
            total_imported = import_result.get("imported", 0) + import_result.get("updated", 0)
            if total_imported > 0:
                logger.info(f"      ✓ Imported/updated {total_imported} subscribers")
            elif import_result.get("errors", 0) > 0:
                logger.warning(f"      ⚠ Import had {import_result['errors']} errors")
            else:
                logger.info(f"      ✓ No new subscribers to import (or SUBSCRIBERS_CSV_URL not set)")
        except Exception as e:
            logger.warning(f"      ⚠ Subscriber import failed (continuing): {e}")
            results["import_subscribers"] = {"error": str(e)}

        # Show database stats after cleanup
        stats_after = repo.get_database_stats()
        logger.info(f"      After:  YouTube={stats_after['youtube_videos']}, "
                    f"OpenAI={stats_after['openai_articles']}, "
                    f"Anthropic={stats_after['anthropic_articles']}, "
                    f"F1={stats_after['f1_articles']}, "
                    f"Digests={stats_after['digests']}")
        
        total_deleted = sum(cleanup_result.values())
        if total_deleted > 0:
            logger.info(f"      ✓ Deleted {total_deleted} old records")
        else:
            logger.info(f"      ✓ No old data to clean up")
        
        # Step 1: Scrape articles (1 week)
        logger.info("\n[1/6] 📡 Scraping articles from sources...")
        scraping_results = run_scrapers(hours=SCRAPE_HOURS)
        results["scraping"] = {
            "youtube": len(scraping_results.get("youtube", [])),
            "openai": len(scraping_results.get("openai", [])),
            "anthropic": len(scraping_results.get("anthropic", [])),
            "f1": len(scraping_results.get("f1", []))
        }
        logger.info(f"      ✓ YouTube: {results['scraping']['youtube']}, "
                    f"OpenAI: {results['scraping']['openai']}, "
                    f"Anthropic: {results['scraping']['anthropic']}, "
                    f"F1: {results['scraping']['f1']}")
        
        # Step 2: Process Anthropic markdown
        logger.info("\n[2/6] 📄 Processing Anthropic markdown...")
        anthropic_result = process_anthropic_markdown()
        results["processing"]["anthropic"] = anthropic_result
        logger.info(f"      ✓ Processed: {anthropic_result['processed']}, "
                    f"Failed: {anthropic_result['failed']}")
        
        # Step 3: Process YouTube transcripts
        logger.info("\n[3/6] 🎬 Processing YouTube transcripts...")
        youtube_result = process_youtube_transcripts()
        results["processing"]["youtube"] = youtube_result
        logger.info(f"      ✓ Processed: {youtube_result['processed']}, "
                    f"Unavailable: {youtube_result['unavailable']}")
        
        # Step 4: Create digests (1 per source from past 24 hours)
        logger.info(f"\n[4/6] 🤖 Creating AI digests (1 per source, last {NEWSLETTER_HOURS}h)...")
        logger.info(f"      ⚠️  API calls: {TOTAL_FEATURED}")
        digest_result = process_digests_per_source(hours=NEWSLETTER_HOURS)
        results["digests"] = {
            "youtube": digest_result["youtube"]["processed"],
            "openai": digest_result["openai"]["processed"],
            "anthropic": digest_result["anthropic"]["processed"],
            "f1": digest_result["f1"]["processed"],
            "total": digest_result["total_processed"]
        }
        logger.info(f"      ✓ Created: {digest_result['total_processed']} digests")
        
        # Step 5: Generate and send newsletter
        logger.info(f"\n[5/6] 📧 Generating and sending newsletter...")
        logger.info(f"      ⚠️  API calls: 2 (curator + email)")
        newsletter_result = send_newsletter(hours=NEWSLETTER_HOURS)
        results["newsletter"] = newsletter_result
        
        if newsletter_result["success"]:
            logger.info(f"      ✓ Newsletter sent!")
            if "sent" in newsletter_result:
                logger.info(f"        Sent: {newsletter_result['sent']}, Skipped: {newsletter_result.get('skipped', 0)}, Errors: {newsletter_result.get('errors', 0)}")
            else:
                logger.info(f"        Featured: {newsletter_result.get('featured_count', 0)}")
                logger.info(f"        Links: {newsletter_result.get('additional_count', 0)}")
            results["success"] = True
        else:
            logger.error(f"      ✗ Failed: {newsletter_result.get('error', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        results["error"] = str(e)
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration
    
    # Final database stats
    final_stats = repo.get_database_stats()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Duration:     {duration:.1f} seconds")
    logger.info(f"Cleanup:      {sum(results['cleanup'].values())} records deleted")
    logger.info(f"Scraped:      {results['scraping']}")
    logger.info(f"Digests:      YouTube={results['digests'].get('youtube', False)}, "
                f"OpenAI={results['digests'].get('openai', False)}, "
                f"Anthropic={results['digests'].get('anthropic', False)}, "
                f"F1={results['digests'].get('f1', False)}")
    logger.info(f"Newsletter:   {'✓ Sent' if results['success'] else '✗ Failed'}")
    logger.info(f"API calls:    ~{TOTAL_FEATURED + 2} (digest + curator + email)")
    logger.info(f"Database:     YouTube={final_stats['youtube_videos']}, "
                f"OpenAI={final_stats['openai_articles']}, "
                f"Anthropic={final_stats['anthropic_articles']}, "
                f"F1={final_stats['f1_articles']}, "
                f"Digests={final_stats['digests']}, "
                f"Subscribers={final_stats.get('subscribers', 0)}")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    result = run_daily_pipeline()
    exit(0 if result["success"] else 1)
