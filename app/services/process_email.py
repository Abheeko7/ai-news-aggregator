import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from app.agent.email_agent import EmailAgent, EmailIntroduction
from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.email_service import send_email
from app.api_config import (
    NEWSLETTER_HOURS,
    NEWSLETTER_LOOKBACK_HOURS,
    ADDITIONAL_LINKS_PER_SOURCE,
    TOTAL_FEATURED,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Placeholder for multi-user greeting (replaced with subscriber's preferred_name)
GREETING_PLACEHOLDER = "{{NAME}}"


def generate_newsletter_content(
    hours: int = None,
    use_placeholder_greeting: bool = False,
) -> dict:
    """
    Generate newsletter with 1 featured article per source + additional links.
    
    Structure:
    🎬 YOUTUBE - Featured article with AI summary
    📰 OPENAI - Featured article with AI summary  
    🤖 ANTHROPIC - Featured article with AI summary
    🏎️ F1 - Featured article with AI summary
    📚 MORE ARTICLES - Links grouped by source
    
    Args:
        hours: How far back to look. Defaults to NEWSLETTER_HOURS (24).
        use_placeholder_greeting: If True, use {{NAME}} in greeting for multi-user personalization.
    
    Returns:
        dict with featured articles and additional links per source
    """
    if hours is None:
        hours = NEWSLETTER_HOURS
    
    repo = Repository()
    profile = {**USER_PROFILE, "name": GREETING_PLACEHOLDER} if use_placeholder_greeting else USER_PROFILE
    email_agent = EmailAgent(profile)
    
    logger.info(f"\n📧 GENERATING NEWSLETTER CONTENT")
    logger.info(f"   Period: Last {NEWSLETTER_LOOKBACK_HOURS} hours (fallback when no fresh content)")
    logger.info(f"   Featured: 1 per source (with AI digest)")
    logger.info(f"   Additional: {ADDITIONAL_LINKS_PER_SOURCE} links per source\n")
    
    # Get recent digests - use lookback window so we always show latest available (even if older)
    digests = repo.get_recent_digests(hours=NEWSLETTER_LOOKBACK_HOURS)
    
    # Organize digests by source
    featured = {
        "youtube": None,
        "openai": None,
        "anthropic": None,
        "f1": None
    }
    
    for digest in digests:
        source = digest["article_type"]
        if source in featured and featured[source] is None:
            featured[source] = {
                "title": digest["title"],
                "summary": digest["summary"],
                "url": digest["url"],
                "type": source
            }
    
    # Log featured articles found
    featured_count = sum(1 for v in featured.values() if v is not None)
    logger.info(f"   Featured articles found: {featured_count}/{TOTAL_FEATURED}")
    for source, article in featured.items():
        if article:
            logger.info(f"   ✓ {source.upper()}: {article['title'][:40]}...")
        else:
            logger.info(f"   ⚪ {source.upper()}: No digest available")
    
    # Get additional links (excluding featured articles)
    exclude_ids = []
    for digest in digests:
        exclude_ids.append(f"{digest['article_type']}:{digest['article_id']}")
    
    additional = repo.get_additional_articles_per_source(
        hours=NEWSLETTER_LOOKBACK_HOURS,
        limit_per_source=ADDITIONAL_LINKS_PER_SOURCE,
        exclude_ids=exclude_ids
    )
    
    total_additional = sum(len(v) for v in additional.values())
    logger.info(f"   Additional links: {total_additional}")
    
    # Generate email introduction (1 API call)
    logger.info(f"\n🤖 Generating email introduction... (1 API call)")
    featured_list = [a for a in featured.values() if a is not None]
    introduction = email_agent.generate_introduction(featured_list)
    
    return {
        "featured": featured,
        "additional": additional,
        "introduction": introduction,
        "featured_count": featured_count,
        "additional_count": total_additional
    }


def filter_content_for_subscriber(
    content: dict,
    preferences: Dict[str, bool],
) -> dict:
    """
    Filter content by subscriber preferences.
    - Featured (top): Only preferred sources, ordered by preference
    - Additional preferred: More links from preferred topics
    - Additional other: Non-preferred sources as external links only
    """
    sources = ["youtube", "openai", "anthropic", "f1"]
    preferred_sources = [s for s in sources if preferences.get(s, True)]

    # Featured: only preferred sources, in source order (so subscriber's picks appear first)
    featured_preferred = {s: content["featured"].get(s) for s in preferred_sources}
    featured_preferred = {k: v for k, v in featured_preferred.items() if v is not None}

    # Additional from preferred topics ("More from your topics")
    additional_preferred = {s: content["additional"].get(s, []) for s in preferred_sources}
    additional_preferred = {k: v for k, v in additional_preferred.items() if v}

    # Non-preferred as external links only ("Other topics")
    other_sources = [s for s in sources if s not in preferred_sources]
    additional_other = {s: content["additional"].get(s, []) for s in other_sources}
    additional_other = {k: v for k, v in additional_other.items() if v}

    featured_count = len(featured_preferred)
    additional_count = sum(len(v) for v in additional_preferred.values()) + sum(
        len(v) for v in additional_other.values()
    )

    return {
        **content,
        "featured_preferred": featured_preferred,
        "additional_preferred": additional_preferred,
        "additional_other": additional_other,
        "preferred_sources": preferred_sources,
        "featured": featured_preferred,  # Backward compat for intro generation
        "additional": {**additional_preferred, **additional_other},
        "featured_count": featured_count,
        "additional_count": additional_count,
    }


def _personalize_greeting(greeting: str, preferred_name: str) -> str:
    """Replace placeholder with subscriber's preferred name."""
    name = (preferred_name or "there").strip() or "there"
    return greeting.replace(GREETING_PLACEHOLDER, name)


def newsletter_to_html(content: dict, preferred_name: Optional[str] = None) -> str:
    """Convert newsletter content to beautiful HTML email. Use preferred_name for greeting."""
    intro = content.get("introduction")
    featured = content.get("featured_preferred", content.get("featured", {}))
    preferred_sources = content.get("preferred_sources", ["youtube", "openai", "anthropic", "f1"])
    additional_preferred = content.get("additional_preferred", content.get("additional", {}))
    additional_other = content.get("additional_other", {})
    
    greeting = intro.greeting if intro else "Hello!"
    if preferred_name is not None:
        greeting = _personalize_greeting(greeting, preferred_name)
    
    # Source icons and colors
    source_config = {
        "youtube": {"icon": "🎬", "color": "#FF0000", "name": "YouTube"},
        "openai": {"icon": "🤖", "color": "#10A37F", "name": "OpenAI"},
        "anthropic": {"icon": "🧠", "color": "#D97706", "name": "Anthropic"},
        "f1": {"icon": "🏎️", "color": "#E10600", "name": "Formula 1"}
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .greeting {{ 
                font-size: 20px; 
                color: #333; 
                margin-bottom: 10px;
            }}
            .intro {{ 
                color: #666; 
                margin-bottom: 30px;
                line-height: 1.6;
            }}
            .section-title {{
                font-size: 14px;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin: 30px 0 15px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid #eee;
            }}
            .featured-article {{ 
                margin-bottom: 25px; 
                padding: 20px; 
                border-radius: 8px;
                background: #fafafa;
                border-left: 4px solid #ddd;
            }}
            .source-badge {{
                display: inline-block;
                font-size: 12px;
                padding: 4px 10px;
                border-radius: 12px;
                color: white;
                margin-bottom: 10px;
            }}
            .article-title {{ 
                font-size: 17px; 
                font-weight: 600; 
                color: #333; 
                margin-bottom: 10px;
                line-height: 1.4;
            }}
            .article-summary {{ 
                color: #555; 
                line-height: 1.7;
                margin-bottom: 12px;
            }}
            .read-more {{ 
                color: #1a73e8; 
                text-decoration: none;
                font-weight: 500;
            }}
            .more-links {{
                margin-top: 30px;
            }}
            .source-links {{
                margin-bottom: 20px;
            }}
            .source-header {{
                font-size: 13px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .link-item {{ 
                padding: 8px 0; 
                border-bottom: 1px solid #f0f0f0;
            }}
            .link-item a {{ 
                color: #1a73e8; 
                text-decoration: none;
                font-size: 14px;
            }}
            .link-item a:hover {{
                text-decoration: underline;
            }}
            .no-article {{
                color: #999;
                font-style: italic;
                padding: 15px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p class="greeting">{greeting}</p>
            <p class="intro">{intro.introduction if intro else 'Here are your top AI news articles from the past 24 hours.'}</p>
            
            <div class="section-title">🌟 Featured Articles</div>
    """
    
    # Add featured articles: only preferred topics, in preference order (top of newsletter)
    for source in preferred_sources:
        config = source_config[source]
        article = featured.get(source)
        
        if article:
            html += f"""
            <div class="featured-article" style="border-left-color: {config['color']};">
                <span class="source-badge" style="background: {config['color']};">
                    {config['icon']} {config['name']}
                </span>
                <div class="article-title">{article['title']}</div>
                <p class="article-summary">{article['summary']}</p>
                <a class="read-more" href="{article['url']}">Read article →</a>
            </div>
            """
        else:
            html += f"""
            <div class="featured-article" style="border-left-color: #ddd;">
                <span class="source-badge" style="background: #ccc;">
                    {config['icon']} {config['name']}
                </span>
                <p class="no-article">No articles from {config['name']} right now</p>
            </div>
            """
    
    # More from your topics (additional links from preferred sources)
    has_preferred_links = any(links for links in additional_preferred.values())
    if has_preferred_links:
        html += """
            <div class="more-links">
                <div class="section-title">📚 More from Your Topics</div>
        """
        for source in preferred_sources:
            config = source_config[source]
            links = additional_preferred.get(source, [])
            if links:
                html += f"""
                <div class="source-links">
                    <div class="source-header">{config['icon']} {config['name']}</div>
                """
                for link in links:
                    html += f"""
                    <div class="link-item">
                        <a href="{link['url']}">{link['title']}</a>
                    </div>
                    """
                html += "</div>"
        html += "</div>"
    
    # Other topics (non-preferred as external links only)
    has_other_links = any(links for links in additional_other.values())
    if has_other_links:
        html += """
            <div class="more-links">
                <div class="section-title">🔗 Other Topics</div>
        """
        for source in ["youtube", "openai", "anthropic", "f1"]:
            if source in additional_other and additional_other[source]:
                config = source_config[source]
                links = additional_other[source]
                html += f"""
                <div class="source-links">
                    <div class="source-header">{config['icon']} {config['name']}</div>
                """
                for link in links:
                    html += f"""
                    <div class="link-item">
                        <a href="{link['url']}">{link['title']}</a>
                    </div>
                    """
                html += "</div>"
        html += "</div>"
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def newsletter_to_text(content: dict, preferred_name: Optional[str] = None) -> str:
    """Convert newsletter content to plain text format. Use preferred_name for greeting."""
    intro = content.get("introduction")
    featured = content.get("featured_preferred", content.get("featured", {}))
    preferred_sources = content.get("preferred_sources", ["youtube", "openai", "anthropic", "f1"])
    additional_preferred = content.get("additional_preferred", content.get("additional", {}))
    additional_other = content.get("additional_other", {})
    
    greeting = intro.greeting if intro else "Hello!"
    if preferred_name is not None:
        greeting = _personalize_greeting(greeting, preferred_name)
    
    source_icons = {"youtube": "🎬", "openai": "🤖", "anthropic": "🧠", "f1": "🏎️"}
    
    text = f"{greeting}\n\n"
    text += f"{intro.introduction if intro else 'Here are your top AI news articles.'}\n\n"
    
    text += "=" * 50 + "\n"
    text += "🌟 FEATURED ARTICLES\n"
    text += "=" * 50 + "\n\n"
    
    for source in preferred_sources:
        icon = source_icons[source]
        article = featured.get(source)
        
        text += f"{icon} {source.upper()}\n"
        text += "-" * 30 + "\n"
        
        if article:
            text += f"{article['title']}\n\n"
            text += f"{article['summary']}\n\n"
            text += f"🔗 {article['url']}\n\n"
        else:
            text += "No articles right now\n\n"
    
    # More from your topics
    has_preferred = any(links for links in additional_preferred.values())
    if has_preferred:
        text += "=" * 50 + "\n"
        text += "📚 MORE FROM YOUR TOPICS\n"
        text += "=" * 50 + "\n\n"
        for source in preferred_sources:
            icon = source_icons[source]
            links = additional_preferred.get(source, [])
            if links:
                text += f"{icon} {source.upper()}\n"
                for link in links:
                    text += f"  • {link['title']}\n"
                    text += f"    {link['url']}\n"
                text += "\n"
    
    # Other topics (external links)
    has_other = any(links for links in additional_other.values())
    if has_other:
        text += "=" * 50 + "\n"
        text += "🔗 OTHER TOPICS\n"
        text += "=" * 50 + "\n\n"
        for source in ["youtube", "openai", "anthropic", "f1"]:
            if source in additional_other and additional_other[source]:
                icon = source_icons[source]
                links = additional_other[source]
                text += f"{icon} {source.upper()}\n"
                for link in links:
                    text += f"  • {link['title']}\n"
                    text += f"    {link['url']}\n"
                text += "\n"
    
    return text


def send_newsletter(hours: int = None) -> dict:
    """
    Generate and send the newsletter email to all active subscribers.
    If no subscribers, falls back to MY_EMAIL (single-user mode).

    Args:
        hours: How far back to look. Defaults to NEWSLETTER_HOURS (24).

    Returns:
        dict with success status and details
    """
    if hours is None:
        hours = NEWSLETTER_HOURS

    try:
        repo = Repository()
        subscribers = repo.list_active_subscribers()

        if subscribers:
            logger.info(f"\n📧 SENDING NEWSLETTER TO {len(subscribers)} SUBSCRIBERS")
            content = generate_newsletter_content(hours=hours, use_placeholder_greeting=True)
            sent = 0
            skipped = 0
            errors = 0

            for sub in subscribers:
                prefs = {"youtube": sub["youtube"], "openai": sub["openai"], "anthropic": sub["anthropic"], "f1": sub["f1"]}
                filtered = filter_content_for_subscriber(content, prefs)

                if filtered["featured_count"] == 0 and filtered["additional_count"] == 0:
                    logger.info(f"   Skipping {sub['email']}: no content for selected topics")
                    skipped += 1
                    continue

                try:
                    html_content = newsletter_to_html(filtered, preferred_name=sub["preferred_name"])
                    text_content = newsletter_to_text(filtered, preferred_name=sub["preferred_name"])
                    subject = f"AI News Digest - {datetime.now().strftime('%B %d, %Y')}"

                    send_email(
                        subject=subject,
                        body_text=text_content,
                        body_html=html_content,
                        recipients=[sub["email"]],
                    )
                    sent += 1
                    logger.info(f"   ✓ Sent to {sub['email']}")
                    # Small delay between sends to avoid rate limits (Gmail ~500/day; gentle on SMTP).
                    time.sleep(0.6)
                except Exception as e:
                    errors += 1
                    logger.error(f"   ✗ Failed {sub['email']}: {e}")

            return {
                "success": sent > 0,
                "subject": f"AI News Digest - {datetime.now().strftime('%B %d, %Y')}",
                "sent": sent,
                "skipped": skipped,
                "errors": errors,
                "total_subscribers": len(subscribers),
            }
        else:
            # Fallback: single-user mode (MY_EMAIL)
            logger.info(f"\n📧 SENDING NEWSLETTER (single user: MY_EMAIL)")
            logger.info(f"   Expected API calls: 2 (curator + email intro)\n")

            content = generate_newsletter_content(hours=hours, use_placeholder_greeting=False)

            if content["featured_count"] == 0 and content["additional_count"] == 0:
                logger.warning("No content to send")
                return {
                    "success": False,
                    "error": "No articles found for newsletter"
                }

            html_content = newsletter_to_html(content, preferred_name=None)
            text_content = newsletter_to_text(content, preferred_name=None)
            subject = f"AI News Digest - {datetime.now().strftime('%B %d, %Y')}"

            send_email(
                subject=subject,
                body_text=text_content,
                body_html=html_content,
            )

            logger.info(f"\n✅ Newsletter sent!")
            logger.info(f"   Featured: {content['featured_count']} articles")
            logger.info(f"   Additional: {content['additional_count']} links")

            return {
                "success": True,
                "subject": subject,
                "featured_count": content["featured_count"],
                "additional_count": content["additional_count"],
            }

    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Backward compatibility
def send_digest_email(hours: int = None, top_n: int = None) -> dict:
    return send_newsletter(hours=hours)


if __name__ == "__main__":
    print(f"\n📊 Newsletter Configuration:")
    print(f"   Period: {NEWSLETTER_HOURS} hours")
    print(f"   Featured: 1 per source ({TOTAL_FEATURED} total)")
    print(f"   Additional links: {ADDITIONAL_LINKS_PER_SOURCE} per source")
    print(f"   API calls: 2 (curator + email)\n")
    
    result = send_newsletter()
    
    if result["success"]:
        print(f"\n✅ Newsletter Sent!")
        print(f"   Subject: {result['subject']}")
        print(f"   Featured: {result['featured_count']}")
        print(f"   Links: {result['additional_count']}")
    else:
        print(f"\n❌ Error: {result['error']}")
