"""
Database Cleanup Utility
========================
Deletes data older than the retention period from all tables.

This is automatically run as part of the daily pipeline,
but can also be run independently if needed.

Usage:
    python -m app.services.cleanup_database

Options:
    --hours N    Override retention hours (default: 168 = 7 days)
    --dry-run    Show what would be deleted without actually deleting
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.repository import Repository
from app.api_config import DATA_RETENTION_HOURS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def show_old_data_stats(repo: Repository, retention_hours: int) -> dict:
    """Show statistics about data that would be deleted."""
    from app.database.models import YouTubeVideo, OpenAIArticle, AnthropicArticle, Digest
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
    
    stats = {
        "youtube": repo.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at < cutoff_time
        ).count(),
        "openai": repo.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at < cutoff_time
        ).count(),
        "anthropic": repo.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at < cutoff_time
        ).count(),
        "digests": repo.session.query(Digest).filter(
            Digest.created_at < cutoff_time
        ).count()
    }
    
    return stats


def run_cleanup(retention_hours: int = None, dry_run: bool = False) -> dict:
    """
    Run database cleanup.
    
    Args:
        retention_hours: Keep data from the last N hours
        dry_run: If True, only show what would be deleted
    
    Returns:
        dict with cleanup results
    """
    if retention_hours is None:
        retention_hours = DATA_RETENTION_HOURS
    
    repo = Repository()
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
    
    print("\n" + "=" * 60)
    print("🗑️  DATABASE CLEANUP UTILITY")
    print("=" * 60)
    print(f"\nRetention period: {retention_hours} hours ({retention_hours // 24} days)")
    print(f"Cutoff date:      {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Mode:             {'DRY RUN (no changes)' if dry_run else 'LIVE (will delete)'}")
    
    # Get current database stats
    current_stats = repo.get_database_stats()
    print(f"\n📊 Current Database:")
    print(f"   YouTube videos:     {current_stats['youtube_videos']}")
    print(f"   OpenAI articles:    {current_stats['openai_articles']}")
    print(f"   Anthropic articles: {current_stats['anthropic_articles']}")
    print(f"   Digests:            {current_stats['digests']}")
    print(f"   Total:              {sum(current_stats.values())}")
    
    # Get stats for old data
    old_stats = show_old_data_stats(repo, retention_hours)
    total_old = sum(old_stats.values())
    
    print(f"\n🗑️  Data to Delete (older than {retention_hours}h):")
    print(f"   YouTube videos:     {old_stats['youtube']}")
    print(f"   OpenAI articles:    {old_stats['openai']}")
    print(f"   Anthropic articles: {old_stats['anthropic']}")
    print(f"   Digests:            {old_stats['digests']}")
    print(f"   Total:              {total_old}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN - No data was deleted")
        return {"dry_run": True, "would_delete": old_stats}
    
    if total_old == 0:
        print(f"\n✓ No old data to clean up")
        return {"deleted": old_stats}
    
    # Confirm deletion
    print(f"\n⚠️  This will permanently delete {total_old} records!")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return {"cancelled": True}
    
    # Run cleanup
    print("\nDeleting old data...")
    result = repo.cleanup_all_old_data(retention_hours=retention_hours)
    
    # Show final stats
    final_stats = repo.get_database_stats()
    print(f"\n✅ Cleanup complete!")
    print(f"\n📊 Database After Cleanup:")
    print(f"   YouTube videos:     {final_stats['youtube_videos']}")
    print(f"   OpenAI articles:    {final_stats['openai_articles']}")
    print(f"   Anthropic articles: {final_stats['anthropic_articles']}")
    print(f"   Digests:            {final_stats['digests']}")
    print(f"   Total:              {sum(final_stats.values())}")
    
    return {"deleted": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database cleanup utility")
    parser.add_argument("--hours", type=int, default=DATA_RETENTION_HOURS,
                       help=f"Retention hours (default: {DATA_RETENTION_HOURS})")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted without deleting")
    
    args = parser.parse_args()
    
    run_cleanup(retention_hours=args.hours, dry_run=args.dry_run)
