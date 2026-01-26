# Detailed Explanation of youtube.py
# This file scrapes YouTube videos from channels and gets their transcripts

# ============================================================================
# SECTION 1: IMPORTS - What libraries we're using
# ============================================================================

from datetime import datetime, timedelta, timezone
# datetime - for working with dates and times
# timedelta - for calculating time differences (e.g., "24 hours ago")
# timezone - for handling timezones (UTC)

from typing import List, Optional
# List - type hint for lists (e.g., List[str] means a list of strings)
# Optional - type hint meaning "can be this type OR None" (e.g., Optional[str])

import os
# For reading environment variables (like API keys from .env file)

import feedparser
# Library that reads RSS feeds (YouTube provides RSS feeds for channels)

from pydantic import BaseModel
# Pydantic - library for data validation
# BaseModel - base class for creating data models with automatic validation

from youtube_transcript_api import YouTubeTranscriptApi
# Library that fetches YouTube video transcripts (auto-generated captions)

from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
# Specific error types we might encounter:
# - TranscriptsDisabled: Video has transcripts disabled
# - NoTranscriptFound: No transcript available for this video

from youtube_transcript_api.proxies import WebshareProxyConfig
# Optional: For using proxy servers (if you need to hide your IP)


# ============================================================================
# SECTION 2: DATA MODELS - What data structures we'll use
# ============================================================================

class Transcript(BaseModel):
    """Represents a YouTube video transcript"""
    text: str  # The transcript text (required field)
    
    # Example usage:
    # transcript = Transcript(text="Hello world, this is a video about...")
    # print(transcript.text)  # "Hello world, this is a video about..."


class ChannelVideo(BaseModel):
    """Represents a YouTube video with all its information"""
    title: str                    # Video title (required)
    url: str                      # Full YouTube URL (required)
    video_id: str                 # Unique video ID (required)
    published_at: datetime        # When the video was published (required)
    description: str              # Video description (required)
    transcript: Optional[str] = None  # Transcript text (optional, defaults to None)
    
    # Example usage:
    # video = ChannelVideo(
    #     title="How to Code in Python",
    #     url="https://youtube.com/watch?v=abc123",
    #     video_id="abc123",
    #     published_at=datetime.now(),
    #     description="Learn Python programming"
    # )
    # 
    # Later, we can add transcript:
    # video.transcript = "Hello, welcome to this video..."


# ============================================================================
# SECTION 3: THE MAIN SCRAPER CLASS
# ============================================================================

class YouTubeScraper:
    """
    This class handles all YouTube scraping operations:
    - Getting latest videos from a channel
    - Fetching video transcripts
    """
    
    # ------------------------------------------------------------------------
    # __init__ - Constructor (runs when you create a new YouTubeScraper)
    # ------------------------------------------------------------------------
    def __init__(self):
        """
        Initialize the scraper.
        Sets up the transcript API (with optional proxy support).
        """
        # Start with no proxy
        proxy_config = None
        
        # Check if proxy credentials are in environment variables
        proxy_username = os.getenv("PROXY_USERNAME")  # Get from .env file
        proxy_password = os.getenv("PROXY_PASSWORD")  # Get from .env file
        
        # If proxy credentials exist, set up proxy
        if proxy_username and proxy_password:
            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password
            )
            # Note: Most users won't need proxies - this is optional
        
        # Create the transcript API client
        # This is what we'll use to fetch transcripts
        self.transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        # self.transcript_api is now available to all methods in this class
    
    # ------------------------------------------------------------------------
    # _get_rss_url - Helper method (starts with _ means "private/internal use")
    # ------------------------------------------------------------------------
    def _get_rss_url(self, channel_id: str) -> str:
        """
        Builds the RSS feed URL for a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID (e.g., "UCawZsQWqfGSbCI5yjkdVkTA")
        
        Returns:
            RSS feed URL string
        
        Example:
            Input: "UCawZsQWqfGSbCI5yjkdVkTA"
            Output: "https://www.youtube.com/feeds/videos.xml?channel_id=UCawZsQWqfGSbCI5yjkdVkTA"
        """
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        # f-string: Python's way of inserting variables into strings
        # Equivalent to: "https://..." + channel_id
    
    # ------------------------------------------------------------------------
    # _extract_video_id - Helper method to get video ID from URL
    # ------------------------------------------------------------------------
    def _extract_video_id(self, video_url: str) -> str:
        """
        Extracts the video ID from different YouTube URL formats.
        
        YouTube URLs come in different formats:
        - https://youtube.com/watch?v=VIDEO_ID
        - https://youtube.com/shorts/VIDEO_ID
        - https://youtu.be/VIDEO_ID
        
        This function handles all of them.
        
        Args:
            video_url: Full YouTube URL
        
        Returns:
            Just the video ID (e.g., "jqd6_bbjhS8")
        
        Example:
            Input: "https://youtube.com/watch?v=abc123&t=10s"
            Output: "abc123"
        """
        # Format 1: youtube.com/watch?v=VIDEO_ID
        if "youtube.com/watch?v=" in video_url:
            # Split by "v=", take the part after it
            # Then split by "&" to remove any extra parameters
            return video_url.split("v=")[1].split("&")[0]
            # "https://youtube.com/watch?v=abc123&t=10s"
            # .split("v=") → ["https://youtube.com/watch?", "abc123&t=10s"]
            # [1] → "abc123&t=10s"
            # .split("&") → ["abc123", "t=10s"]
            # [0] → "abc123"
        
        # Format 2: youtube.com/shorts/VIDEO_ID
        if "youtube.com/shorts/" in video_url:
            return video_url.split("shorts/")[1].split("?")[0]
            # Similar logic for shorts URLs
        
        # Format 3: youtu.be/VIDEO_ID
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
            # Similar logic for shortened URLs
        
        # If none of the above, return the URL as-is (fallback)
        return video_url
    
    # ------------------------------------------------------------------------
    # get_transcript - Fetches transcript for a specific video
    # ------------------------------------------------------------------------
    def get_transcript(self, video_id: str) -> Optional[Transcript]:
        """
        Gets the transcript (auto-generated captions) for a YouTube video.
        
        Args:
            video_id: YouTube video ID (e.g., "jqd6_bbjhS8")
        
        Returns:
            Transcript object with the text, OR None if unavailable
        
        Example:
            transcript = scraper.get_transcript("jqd6_bbjhS8")
            if transcript:
                print(transcript.text)  # "Hello, welcome to..."
            else:
                print("No transcript available")
        """
        try:
            # Try to fetch the transcript
            transcript = self.transcript_api.fetch(video_id)
            # This returns a transcript object with snippets (time-stamped text pieces)
            
            # Combine all snippets into one continuous text
            # transcript.snippets is a list of objects, each with a .text property
            # [snippet.text for snippet in transcript.snippets] creates a list of text strings
            # " ".join(...) joins them with spaces
            text = " ".join([snippet.text for snippet in transcript.snippets])
            # Example: ["Hello", "world", "this"] → "Hello world this"
            
            # Return as a Transcript object
            return Transcript(text=text)
        
        except (TranscriptsDisabled, NoTranscriptFound):
            # These are expected errors - some videos just don't have transcripts
            # Not a problem, just return None
            return None
        
        except Exception:
            # Any other unexpected error - also return None
            # This prevents the whole program from crashing
            return None
    
    # ------------------------------------------------------------------------
    # get_latest_videos - Gets recent videos from a channel
    # ------------------------------------------------------------------------
    def get_latest_videos(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        """
        Gets the latest videos from a YouTube channel published within the last N hours.
        
        Args:
            channel_id: YouTube channel ID
            hours: How many hours back to look (default: 24)
        
        Returns:
            List of ChannelVideo objects
        
        Example:
            videos = scraper.get_latest_videos("UCawZsQWqfGSbCI5yjkdVkTA", hours=48)
            for video in videos:
                print(video.title)
        """
        # Step 1: Get the RSS feed URL and parse it
        feed = feedparser.parse(self._get_rss_url(channel_id))
        # feedparser.parse() reads the RSS XML and converts it to Python objects
        # feed.entries is a list of video entries
        
        # Step 2: Check if we got any videos
        if not feed.entries:
            return []  # No videos found, return empty list
        
        # Step 3: Calculate the cutoff time (only videos after this time)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        # datetime.now(timezone.utc) = current time in UTC
        # timedelta(hours=24) = 24 hours
        # So cutoff_time = 24 hours ago
        # Example: If now is 3pm, cutoff_time is 3pm yesterday
        
        videos = []  # List to store our ChannelVideo objects
        
        # Step 4: Loop through each video in the feed
        for entry in feed.entries:
            # Skip YouTube Shorts (we only want regular videos)
            if "/shorts/" in entry.link:
                continue  # Skip this video, go to next one
            
            # Step 5: Parse the published time
            # entry.published_parsed is a tuple like (2024, 1, 15, 10, 30, 0, ...)
            # [:6] takes first 6 elements (year, month, day, hour, minute, second)
            # * unpacks the tuple as arguments to datetime()
            # tzinfo=timezone.utc sets the timezone to UTC
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            # Step 6: Only include videos published after cutoff time
            if published_time >= cutoff_time:
                # Extract video ID from URL
                video_id = self._extract_video_id(entry.link)
                
                # Create a ChannelVideo object and add to list
                videos.append(ChannelVideo(
                    title=entry.title,                    # Video title
                    url=entry.link,                       # Full URL
                    video_id=video_id,                    # Just the ID
                    published_at=published_time,          # When published
                    description=entry.get("summary", "")   # Description (or empty string if missing)
                ))
        
        # Step 7: Return the list of videos
        return videos
    
    # ------------------------------------------------------------------------
    # scrape_channel - Gets videos AND their transcripts
    # ------------------------------------------------------------------------
    def scrape_channel(self, channel_id: str, hours: int = 150) -> list[ChannelVideo]:
        """
        Gets latest videos from a channel AND fetches their transcripts.
        This is a convenience method that combines get_latest_videos() and get_transcript().
        
        Args:
            channel_id: YouTube channel ID
            hours: How many hours back to look (default: 150, which is ~6 days)
        
        Returns:
            List of ChannelVideo objects, each with transcript filled in (if available)
        
        Note: This can be slow because it fetches transcripts for every video.
        The main pipeline uses get_latest_videos() first, then processes transcripts separately.
        """
        # Step 1: Get the latest videos (without transcripts yet)
        videos = self.get_latest_videos(channel_id, hours)
        
        result = []  # List for videos with transcripts
        
        # Step 2: For each video, try to get its transcript
        for video in videos:
            transcript = self.get_transcript(video.video_id)
            # transcript is either a Transcript object or None
            
            # Step 3: Create a copy of the video with transcript added
            # model_copy() creates a copy of the Pydantic model
            # update={...} updates specific fields
            result.append(video.model_copy(update={
                "transcript": transcript.text if transcript else None
            }))
            # If transcript exists, use transcript.text
            # Otherwise, use None
        
        return result


# ============================================================================
# SECTION 4: TEST CODE (runs when you execute this file directly)
# ============================================================================

if __name__ == "__main__":
    # This code only runs if you execute: python youtube.py
    # It doesn't run when you import this file
    
    # Create a scraper instance
    scraper = YouTubeScraper()
    
    # Test: Get transcript for a specific video
    transcript: Transcript = scraper.get_transcript("jqd6_bbjhS8")
    print(transcript.text)
    
    # Test: Get videos from a channel
    channel_videos: List[ChannelVideo] = scraper.scrape_channel(
        "UCn8ujwUInbJkBhffxqAPBVQ",  # Channel ID
        hours=200  # Last 200 hours (~8 days)
    )


# ============================================================================
# HOW IT ALL WORKS TOGETHER
# ============================================================================

"""
WORKFLOW EXAMPLE:

1. Create scraper:
   scraper = YouTubeScraper()

2. Get latest videos from a channel:
   videos = scraper.get_latest_videos("UCawZsQWqfGSbCI5yjkdVkTA", hours=24)
   # Returns list of ChannelVideo objects (without transcripts yet)

3. Later, process transcripts separately (more efficient):
   for video in videos:
       transcript = scraper.get_transcript(video.video_id)
       if transcript:
           # Save transcript to database
           print(f"Got transcript for {video.title}")

WHY THIS DESIGN?

- get_latest_videos() is fast (just reads RSS feed)
- get_transcript() is slower (makes API calls)
- Separating them allows the pipeline to:
  1. Quickly scrape all videos
  2. Save them to database
  3. Process transcripts later (in batches, with retries, etc.)

This is more efficient and resilient than doing everything at once.
"""
