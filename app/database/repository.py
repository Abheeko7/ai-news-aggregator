from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.orm import Session
from .models import YouTubeVideo, OpenAIArticle, AnthropicArticle, F1Article, Digest
from .connection import get_session

logger = logging.getLogger(__name__)


class Repository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def create_youtube_video(self, video_id: str, title: str, url: str, channel_id: str, 
                            published_at: datetime, description: str = "", transcript: Optional[str] = None) -> Optional[YouTubeVideo]:
        existing = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if existing:
            return None
        video = YouTubeVideo(
            video_id=video_id,
            title=title,
            url=url,
            channel_id=channel_id,
            published_at=published_at,
            description=description,
            transcript=transcript
        )
        self.session.add(video)
        self.session.commit()
        return video
    
    def create_openai_article(self, guid: str, title: str, url: str, published_at: datetime,
                              description: str = "", category: Optional[str] = None) -> Optional[OpenAIArticle]:
        existing = self.session.query(OpenAIArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = OpenAIArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category
        )
        self.session.add(article)
        self.session.commit()
        return article
    
    def create_anthropic_article(self, guid: str, title: str, url: str, published_at: datetime,
                                description: str = "", category: Optional[str] = None) -> Optional[AnthropicArticle]:
        existing = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
        if existing:
            return None
        article = AnthropicArticle(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            category=category
        )
        self.session.add(article)
        self.session.commit()
        return article
    
    def bulk_create_youtube_videos(self, videos: List[dict]) -> int:
        new_videos = []
        for v in videos:
            existing = self.session.query(YouTubeVideo).filter_by(video_id=v["video_id"]).first()
            if not existing:
                new_videos.append(YouTubeVideo(
                    video_id=v["video_id"],
                    title=v["title"],
                    url=v["url"],
                    channel_id=v.get("channel_id", ""),
                    published_at=v["published_at"],
                    description=v.get("description", ""),
                    transcript=v.get("transcript")
                ))
        if new_videos:
            self.session.add_all(new_videos)
            self.session.commit()
        return len(new_videos)
    
    def bulk_create_openai_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = self.session.query(OpenAIArticle).filter_by(guid=a["guid"]).first()
            if not existing:
                new_articles.append(OpenAIArticle(
                    guid=a["guid"],
                    title=a["title"],
                    url=a["url"],
                    published_at=a["published_at"],
                    description=a.get("description", ""),
                    category=a.get("category")
                ))
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)
    
    def bulk_create_anthropic_articles(self, articles: List[dict]) -> int:
        new_articles = []
        for a in articles:
            existing = self.session.query(AnthropicArticle).filter_by(guid=a["guid"]).first()
            if not existing:
                new_articles.append(AnthropicArticle(
                    guid=a["guid"],
                    title=a["title"],
                    url=a["url"],
                    published_at=a["published_at"],
                    description=a.get("description", ""),
                    category=a.get("category")
                ))
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)
    
    # =========================================================================
    # F1 ARTICLE METHODS
    # =========================================================================
    
    def create_f1_article(self, guid: str, title: str, url: str, published_at: datetime,
                          description: str = "", author: Optional[str] = None) -> Optional[F1Article]:
        """
        Create a new F1 article (deduplicates by GUID).
        
        Note: F1 RSS feed doesn't have publication dates, so published_at
        is the time we first scraped the article.
        """
        existing = self.session.query(F1Article).filter_by(guid=guid).first()
        if existing:
            return None  # Already exists, skip (deduplication)
        article = F1Article(
            guid=guid,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            author=author
        )
        self.session.add(article)
        self.session.commit()
        return article
    
    def bulk_create_f1_articles(self, articles: List[dict]) -> int:
        """
        Bulk create F1 articles (deduplicates by GUID).
        
        Returns the number of NEW articles added (existing ones are skipped).
        """
        new_articles = []
        for a in articles:
            existing = self.session.query(F1Article).filter_by(guid=a["guid"]).first()
            if not existing:
                new_articles.append(F1Article(
                    guid=a["guid"],
                    title=a["title"],
                    url=a["url"],
                    published_at=a["published_at"],
                    description=a.get("description", ""),
                    author=a.get("author")
                ))
        if new_articles:
            self.session.add_all(new_articles)
            self.session.commit()
        return len(new_articles)
    
    def get_f1_articles(self, hours: int = 168, limit: Optional[int] = None) -> List[F1Article]:
        """Get F1 articles from the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = self.session.query(F1Article).filter(
            F1Article.published_at >= cutoff_time
        ).order_by(F1Article.published_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_anthropic_articles_without_markdown(self, limit: Optional[int] = None) -> List[AnthropicArticle]:
        query = self.session.query(AnthropicArticle).filter(AnthropicArticle.markdown.is_(None))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update_anthropic_article_markdown(self, guid: str, markdown: str) -> bool:
        article = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
        if article:
            article.markdown = markdown
            self.session.commit()
            return True
        return False
    
    def get_youtube_videos_without_transcript(self, limit: Optional[int] = None) -> List[YouTubeVideo]:
        query = self.session.query(YouTubeVideo).filter(YouTubeVideo.transcript.is_(None))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update_youtube_video_transcript(self, video_id: str, transcript: str) -> bool:
        video = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
        if video:
            video.transcript = transcript
            self.session.commit()
            return True
        return False
    
    def get_articles_without_digest(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        articles = []
        seen_ids = set()
        
        digests = self.session.query(Digest).all()
        for d in digests:
            seen_ids.add(f"{d.article_type}:{d.article_id}")
        
        youtube_videos = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.transcript.isnot(None),
            YouTubeVideo.transcript != "__UNAVAILABLE__"
        ).all()
        for video in youtube_videos:
            key = f"youtube:{video.video_id}"
            if key not in seen_ids:
                articles.append({
                    "type": "youtube",
                    "id": video.video_id,
                    "title": video.title,
                    "url": video.url,
                    "content": video.transcript or video.description or "",
                    "published_at": video.published_at
                })
        
        openai_articles = self.session.query(OpenAIArticle).all()
        for article in openai_articles:
            key = f"openai:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "openai",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.description or "",
                    "published_at": article.published_at
                })
        
        anthropic_articles = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.markdown.isnot(None)
        ).all()
        for article in anthropic_articles:
            key = f"anthropic:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "anthropic",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.markdown or article.description or "",
                    "published_at": article.published_at
                })
        
        if limit:
            articles = articles[:limit]
        
        return articles
    
    def create_digest(self, article_type: str, article_id: str, url: str, title: str, summary: str, published_at: Optional[datetime] = None) -> Optional[Digest]:
        digest_id = f"{article_type}:{article_id}"
        existing = self.session.query(Digest).filter_by(id=digest_id).first()
        if existing:
            return None
        
        if published_at:
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            created_at = published_at
        else:
            created_at = datetime.now(timezone.utc)
        
        digest = Digest(
            id=digest_id,
            article_type=article_type,
            article_id=article_id,
            url=url,
            title=title,
            summary=summary,
            created_at=created_at
        )
        self.session.add(digest)
        self.session.commit()
        return digest
    
    def get_recent_digests(self, hours: int = 168) -> List[Dict[str, Any]]:  # 168 hours = 7 days
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        digests = self.session.query(Digest).filter(
            Digest.created_at >= cutoff_time
        ).order_by(Digest.created_at.desc()).all()
        
        return [
            {
                "id": d.id,
                "article_type": d.article_type,
                "article_id": d.article_id,
                "url": d.url,
                "title": d.title,
                "summary": d.summary,
                "created_at": d.created_at
            }
            for d in digests
        ]
    
    def get_recent_articles_for_newsletter(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get all articles from the past N hours for newsletter generation.
        Returns articles sorted by published_at (newest first).
        Includes both articles with and without digests.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles = []
        
        # Get existing digests for lookup
        digests_map = {}
        digests = self.session.query(Digest).all()
        for d in digests:
            digests_map[d.id] = {"title": d.title, "summary": d.summary}
        
        # YouTube videos with transcripts
        youtube_videos = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at >= cutoff_time,
            YouTubeVideo.transcript.isnot(None),
            YouTubeVideo.transcript != "__UNAVAILABLE__"
        ).order_by(YouTubeVideo.published_at.desc()).all()
        
        for video in youtube_videos:
            digest_id = f"youtube:{video.video_id}"
            digest_info = digests_map.get(digest_id, {})
            articles.append({
                "type": "youtube",
                "id": video.video_id,
                "title": video.title,
                "url": video.url,
                "content": video.transcript or video.description or "",
                "published_at": video.published_at,
                "has_digest": digest_id in digests_map,
                "digest_title": digest_info.get("title"),
                "digest_summary": digest_info.get("summary")
            })
        
        # OpenAI articles
        openai_articles = self.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at >= cutoff_time
        ).order_by(OpenAIArticle.published_at.desc()).all()
        
        for article in openai_articles:
            digest_id = f"openai:{article.guid}"
            digest_info = digests_map.get(digest_id, {})
            articles.append({
                "type": "openai",
                "id": article.guid,
                "title": article.title,
                "url": article.url,
                "content": article.description or "",
                "published_at": article.published_at,
                "has_digest": digest_id in digests_map,
                "digest_title": digest_info.get("title"),
                "digest_summary": digest_info.get("summary")
            })
        
        # Anthropic articles with markdown
        anthropic_articles = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at >= cutoff_time,
            AnthropicArticle.markdown.isnot(None)
        ).order_by(AnthropicArticle.published_at.desc()).all()
        
        for article in anthropic_articles:
            digest_id = f"anthropic:{article.guid}"
            digest_info = digests_map.get(digest_id, {})
            articles.append({
                "type": "anthropic",
                "id": article.guid,
                "title": article.title,
                "url": article.url,
                "content": article.markdown or article.description or "",
                "published_at": article.published_at,
                "has_digest": digest_id in digests_map,
                "digest_title": digest_info.get("title"),
                "digest_summary": digest_info.get("summary")
            })
        
        # Sort by published_at descending
        articles.sort(key=lambda x: x["published_at"], reverse=True)
        
        return articles
    
    def get_top_article_per_source(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """
        Get the TOP 1 article from each source (YouTube, OpenAI, Anthropic, F1) from the past N hours.
        Returns articles that don't have digests yet.
        
        Returns:
            dict with keys 'youtube', 'openai', 'anthropic', 'f1', each containing the top article or None
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = {"youtube": None, "openai": None, "anthropic": None, "f1": None}
        
        # Get existing digest IDs
        seen_ids = set()
        digests = self.session.query(Digest).all()
        for d in digests:
            seen_ids.add(f"{d.article_type}:{d.article_id}")
        
        # Top YouTube video (newest first, with transcript)
        youtube_video = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at >= cutoff_time,
            YouTubeVideo.transcript.isnot(None),
            YouTubeVideo.transcript != "__UNAVAILABLE__"
        ).order_by(YouTubeVideo.published_at.desc()).first()
        
        if youtube_video and f"youtube:{youtube_video.video_id}" not in seen_ids:
            result["youtube"] = {
                "type": "youtube",
                "id": youtube_video.video_id,
                "title": youtube_video.title,
                "url": youtube_video.url,
                "content": youtube_video.transcript or youtube_video.description or "",
                "published_at": youtube_video.published_at
            }
        
        # Top OpenAI article (newest first)
        openai_article = self.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at >= cutoff_time
        ).order_by(OpenAIArticle.published_at.desc()).first()
        
        if openai_article and f"openai:{openai_article.guid}" not in seen_ids:
            result["openai"] = {
                "type": "openai",
                "id": openai_article.guid,
                "title": openai_article.title,
                "url": openai_article.url,
                "content": openai_article.description or "",
                "published_at": openai_article.published_at
            }
        
        # Top Anthropic article (newest first, with markdown)
        anthropic_article = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at >= cutoff_time,
            AnthropicArticle.markdown.isnot(None)
        ).order_by(AnthropicArticle.published_at.desc()).first()
        
        if anthropic_article and f"anthropic:{anthropic_article.guid}" not in seen_ids:
            result["anthropic"] = {
                "type": "anthropic",
                "id": anthropic_article.guid,
                "title": anthropic_article.title,
                "url": anthropic_article.url,
                "content": anthropic_article.markdown or anthropic_article.description or "",
                "published_at": anthropic_article.published_at
            }
        
        # Top F1 article (newest first)
        f1_article = self.session.query(F1Article).filter(
            F1Article.published_at >= cutoff_time
        ).order_by(F1Article.published_at.desc()).first()
        
        if f1_article and f"f1:{f1_article.guid}" not in seen_ids:
            result["f1"] = {
                "type": "f1",
                "id": f1_article.guid,
                "title": f1_article.title,
                "url": f1_article.url,
                "content": f1_article.description or "",
                "published_at": f1_article.published_at
            }
        
        return result
    
    def get_additional_articles_per_source(self, hours: int = 24, limit_per_source: int = 3, 
                                           exclude_ids: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get additional articles from each source (excluding featured ones).
        These are shown as links in the newsletter.
        
        Args:
            hours: How far back to look
            limit_per_source: Max articles per source
            exclude_ids: List of article IDs to exclude (format: "type:id")
        
        Returns:
            dict with keys 'youtube', 'openai', 'anthropic', 'f1', each containing list of articles
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        exclude_ids = exclude_ids or []
        result = {"youtube": [], "openai": [], "anthropic": [], "f1": []}
        
        # YouTube videos
        youtube_videos = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at >= cutoff_time
        ).order_by(YouTubeVideo.published_at.desc()).limit(limit_per_source + 5).all()
        
        for video in youtube_videos:
            if f"youtube:{video.video_id}" not in exclude_ids and len(result["youtube"]) < limit_per_source:
                result["youtube"].append({
                    "type": "youtube",
                    "id": video.video_id,
                    "title": video.title,
                    "url": video.url,
                    "published_at": video.published_at
                })
        
        # OpenAI articles
        openai_articles = self.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at >= cutoff_time
        ).order_by(OpenAIArticle.published_at.desc()).limit(limit_per_source + 5).all()
        
        for article in openai_articles:
            if f"openai:{article.guid}" not in exclude_ids and len(result["openai"]) < limit_per_source:
                result["openai"].append({
                    "type": "openai",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at
                })
        
        # Anthropic articles
        anthropic_articles = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at >= cutoff_time
        ).order_by(AnthropicArticle.published_at.desc()).limit(limit_per_source + 5).all()
        
        for article in anthropic_articles:
            if f"anthropic:{article.guid}" not in exclude_ids and len(result["anthropic"]) < limit_per_source:
                result["anthropic"].append({
                    "type": "anthropic",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at
                })
        
        # F1 articles
        f1_articles = self.session.query(F1Article).filter(
            F1Article.published_at >= cutoff_time
        ).order_by(F1Article.published_at.desc()).limit(limit_per_source + 5).all()
        
        for article in f1_articles:
            if f"f1:{article.guid}" not in exclude_ids and len(result["f1"]) < limit_per_source:
                result["f1"].append({
                    "type": "f1",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at
                })
        
        return result

    def get_articles_without_digest_recent(self, hours: int = 24, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get articles from the past N hours that don't have digests yet.
        Used to generate digests only for recent content.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles = []
        seen_ids = set()
        
        # Get existing digest IDs
        digests = self.session.query(Digest).all()
        for d in digests:
            seen_ids.add(f"{d.article_type}:{d.article_id}")
        
        # YouTube videos
        youtube_videos = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at >= cutoff_time,
            YouTubeVideo.transcript.isnot(None),
            YouTubeVideo.transcript != "__UNAVAILABLE__"
        ).order_by(YouTubeVideo.published_at.desc()).all()
        
        for video in youtube_videos:
            key = f"youtube:{video.video_id}"
            if key not in seen_ids:
                articles.append({
                    "type": "youtube",
                    "id": video.video_id,
                    "title": video.title,
                    "url": video.url,
                    "content": video.transcript or video.description or "",
                    "published_at": video.published_at
                })
        
        # OpenAI articles
        openai_articles = self.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at >= cutoff_time
        ).order_by(OpenAIArticle.published_at.desc()).all()
        
        for article in openai_articles:
            key = f"openai:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "openai",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.description or "",
                    "published_at": article.published_at
                })
        
        # Anthropic articles
        anthropic_articles = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at >= cutoff_time,
            AnthropicArticle.markdown.isnot(None)
        ).order_by(AnthropicArticle.published_at.desc()).all()
        
        for article in anthropic_articles:
            key = f"anthropic:{article.guid}"
            if key not in seen_ids:
                articles.append({
                    "type": "anthropic",
                    "id": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "content": article.markdown or article.description or "",
                    "published_at": article.published_at
                })
        
        # Sort by published_at descending
        articles.sort(key=lambda x: x["published_at"], reverse=True)
        
        if limit:
            articles = articles[:limit]
        
        return articles
    
    # =========================================================================
    # DATA CLEANUP METHODS
    # =========================================================================
    
    def cleanup_old_youtube_videos(self, retention_hours: int = 168) -> int:
        """
        Delete YouTube videos older than retention_hours.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        
        # Get IDs of videos to delete
        old_videos = self.session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at < cutoff_time
        ).all()
        
        count = len(old_videos)
        
        if count > 0:
            # Delete associated digests first
            for video in old_videos:
                self.session.query(Digest).filter(
                    Digest.article_type == "youtube",
                    Digest.article_id == video.video_id
                ).delete()
            
            # Delete the videos
            self.session.query(YouTubeVideo).filter(
                YouTubeVideo.published_at < cutoff_time
            ).delete()
            
            self.session.commit()
            logger.info(f"Deleted {count} old YouTube videos (older than {retention_hours}h)")
        
        return count
    
    def cleanup_old_openai_articles(self, retention_hours: int = 168) -> int:
        """
        Delete OpenAI articles older than retention_hours.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        
        # Get articles to delete
        old_articles = self.session.query(OpenAIArticle).filter(
            OpenAIArticle.published_at < cutoff_time
        ).all()
        
        count = len(old_articles)
        
        if count > 0:
            # Delete associated digests first
            for article in old_articles:
                self.session.query(Digest).filter(
                    Digest.article_type == "openai",
                    Digest.article_id == article.guid
                ).delete()
            
            # Delete the articles
            self.session.query(OpenAIArticle).filter(
                OpenAIArticle.published_at < cutoff_time
            ).delete()
            
            self.session.commit()
            logger.info(f"Deleted {count} old OpenAI articles (older than {retention_hours}h)")
        
        return count
    
    def cleanup_old_anthropic_articles(self, retention_hours: int = 168) -> int:
        """
        Delete Anthropic articles older than retention_hours.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        
        # Get articles to delete
        old_articles = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.published_at < cutoff_time
        ).all()
        
        count = len(old_articles)
        
        if count > 0:
            # Delete associated digests first
            for article in old_articles:
                self.session.query(Digest).filter(
                    Digest.article_type == "anthropic",
                    Digest.article_id == article.guid
                ).delete()
            
            # Delete the articles
            self.session.query(AnthropicArticle).filter(
                AnthropicArticle.published_at < cutoff_time
            ).delete()
            
            self.session.commit()
            logger.info(f"Deleted {count} old Anthropic articles (older than {retention_hours}h)")
        
        return count
    
    def cleanup_old_f1_articles(self, retention_hours: int = 168) -> int:
        """
        Delete F1 articles older than retention_hours.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        
        # Get articles to delete
        old_articles = self.session.query(F1Article).filter(
            F1Article.published_at < cutoff_time
        ).all()
        
        count = len(old_articles)
        
        if count > 0:
            # Delete associated digests first
            for article in old_articles:
                self.session.query(Digest).filter(
                    Digest.article_type == "f1",
                    Digest.article_id == article.guid
                ).delete()
            
            # Delete the articles
            self.session.query(F1Article).filter(
                F1Article.published_at < cutoff_time
            ).delete()
            
            self.session.commit()
            logger.info(f"Deleted {count} old F1 articles (older than {retention_hours}h)")
        
        return count
    
    def cleanup_orphan_digests(self, retention_hours: int = 168) -> int:
        """
        Delete digests older than retention_hours that don't have associated articles.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            Number of records deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        
        count = self.session.query(Digest).filter(
            Digest.created_at < cutoff_time
        ).delete()
        
        if count > 0:
            self.session.commit()
            logger.info(f"Deleted {count} old digests (older than {retention_hours}h)")
        
        return count
    
    def cleanup_all_old_data(self, retention_hours: int = 168) -> Dict[str, int]:
        """
        Delete all data older than retention_hours from all tables.
        
        This is the main cleanup method that should be called during pipeline runs.
        
        Args:
            retention_hours: Keep data from the last N hours (default: 168 = 7 days)
        
        Returns:
            dict with count of deleted records per table
        """
        logger.info(f"\n🗑️  CLEANING UP OLD DATA (older than {retention_hours}h / {retention_hours // 24} days)")
        
        results = {
            "youtube": self.cleanup_old_youtube_videos(retention_hours),
            "openai": self.cleanup_old_openai_articles(retention_hours),
            "anthropic": self.cleanup_old_anthropic_articles(retention_hours),
            "f1": self.cleanup_old_f1_articles(retention_hours),
            "digests": self.cleanup_orphan_digests(retention_hours)
        }
        
        total = sum(results.values())
        
        if total > 0:
            logger.info(f"   Total deleted: {total} records")
            logger.info(f"   YouTube: {results['youtube']}, OpenAI: {results['openai']}, "
                       f"Anthropic: {results['anthropic']}, F1: {results['f1']}, Digests: {results['digests']}")
        else:
            logger.info("   No old data to clean up")
        
        return results
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get current record counts for all tables.
        
        Returns:
            dict with record counts per table
        """
        return {
            "youtube_videos": self.session.query(YouTubeVideo).count(),
            "openai_articles": self.session.query(OpenAIArticle).count(),
            "anthropic_articles": self.session.query(AnthropicArticle).count(),
            "f1_articles": self.session.query(F1Article).count(),
            "digests": self.session.query(Digest).count()
        }

