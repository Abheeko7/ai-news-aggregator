# Step-by-Step Tutorial: Building the AI News Aggregator

Follow along as we build each component. I'll explain everything as we go!

---

## 🗄️ STEP 1: Database Models (Understanding the Data Structure)

### What are Database Models?

Think of models as **blueprints** for your data. They define:
- What information you'll store
- What type each piece of information is
- Which fields are required vs optional

### Let's Break Down Each Model:

#### 1. YouTubeVideo Model
```python
class YouTubeVideo(Base):
    video_id = Column(String, primary_key=True)  # Unique ID (like a license plate)
    title = Column(String, nullable=False)       # Video title (required)
    url = Column(String, nullable=False)         # Link to video (required)
    channel_id = Column(String, nullable=False)  # Which channel (required)
    published_at = Column(DateTime, nullable=False)  # When published (required)
    description = Column(Text)                   # Video description (optional)
    transcript = Column(Text, nullable=True)      # Video transcript (optional, added later)
    created_at = Column(DateTime, default=datetime.utcnow)  # When we saved it
```

**Key Concepts:**
- `primary_key=True` - This uniquely identifies each video (no duplicates)
- `nullable=False` - This field MUST have a value
- `nullable=True` - This field can be empty (like transcript, which we get later)
- `default=datetime.utcnow` - Automatically sets current time when created

#### 2. OpenAIArticle Model
```python
class OpenAIArticle(Base):
    guid = Column(String, primary_key=True)      # Unique identifier
    title = Column(String, nullable=False)       # Article title
    url = Column(String, nullable=False)         # Article URL
    description = Column(Text)                   # Article description
    published_at = Column(DateTime, nullable=False)  # Publication date
    category = Column(String, nullable=True)     # Optional category
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Note:** Similar structure to YouTube, but for blog articles.

#### 3. AnthropicArticle Model
```python
class AnthropicArticle(Base):
    # ... similar to OpenAIArticle ...
    markdown = Column(Text, nullable=True)       # Full article content (added later)
```

**Difference:** Has a `markdown` field to store the full article content (we process this later).

#### 4. Digest Model
```python
class Digest(Base):
    id = Column(String, primary_key=True)        # Format: "youtube:video_id"
    article_type = Column(String, nullable=False)  # "youtube", "openai", or "anthropic"
    article_id = Column(String, nullable=False)  # The original article's ID
    url = Column(String, nullable=False)         # Link to original article
    title = Column(String, nullable=False)       # Article title
    summary = Column(Text, nullable=False)       # AI-generated summary
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Purpose:** Stores AI-generated summaries of articles. One digest per article.

---

## 🔌 STEP 2: Database Connection

### What does this do?

Creates a connection to your PostgreSQL database and provides a way to interact with it.

### Key Concepts:

**1. Environment Variables**
```python
user = os.getenv("POSTGRES_USER", "postgres")  # Get from .env, or use "postgres"
```
- Reads settings from `.env` file
- Falls back to defaults if not set

**2. Connection String**
```python
f"postgresql://{user}:{password}@{host}:{port}/{db}"
```
- Format: `postgresql://username:password@host:port/database_name`
- Example: `postgresql://postgres:postgres@localhost:5432/ai_news_aggregator`

**3. SQLAlchemy Engine**
```python
engine = create_engine(get_database_url())
```
- Creates a connection pool (reuses connections efficiently)
- Handles all database communication

**4. Session**
```python
SessionLocal = sessionmaker(bind=engine)
```
- A "session" is like a conversation with the database
- You use it to add, update, or query data
- Must commit changes to save them

---

## 📦 STEP 3: Repository Pattern

### What is a Repository?

A **repository** is a layer between your code and the database. Instead of writing SQL queries everywhere, you call simple functions.

### Why Use This Pattern?

**Without Repository:**
```python
# Scattered SQL everywhere - hard to maintain
session.execute("INSERT INTO youtube_videos ...")
session.execute("SELECT * FROM youtube_videos WHERE ...")
```

**With Repository:**
```python
# Clean, reusable functions
repo.create_youtube_video(...)
repo.get_youtube_videos_without_transcript()
```

### Key Repository Functions:

#### 1. Creating Records
```python
def create_youtube_video(self, video_id, title, url, ...):
    # Check if already exists
    existing = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
    if existing:
        return None  # Already have it, skip
    
    # Create new video
    video = YouTubeVideo(video_id=video_id, title=title, ...)
    self.session.add(video)
    self.session.commit()  # Save to database
    return video
```

**Key Points:**
- `filter_by()` - Finds existing records
- `session.add()` - Adds to session (not saved yet)
- `session.commit()` - Actually saves to database

#### 2. Bulk Operations
```python
def bulk_create_youtube_videos(self, videos: List[dict]):
    new_videos = []
    for v in videos:
        # Check each one
        existing = self.session.query(YouTubeVideo).filter_by(video_id=v["video_id"]).first()
        if not existing:
            new_videos.append(YouTubeVideo(...))
    
    # Add all at once (more efficient)
    if new_videos:
        self.session.add_all(new_videos)
        self.session.commit()
```

**Why bulk?** More efficient than creating one at a time.

#### 3. Querying Records
```python
def get_articles_without_digest(self):
    # Get all digests that exist
    digests = self.session.query(Digest).all()
    seen_ids = set()
    for d in digests:
        seen_ids.add(f"{d.article_type}:{d.article_id}")
    
    # Get articles that don't have digests
    articles = []
    youtube_videos = self.session.query(YouTubeVideo).filter(
        YouTubeVideo.transcript.isnot(None)  # Only videos with transcripts
    ).all()
    
    for video in youtube_videos:
        key = f"youtube:{video.video_id}"
        if key not in seen_ids:  # No digest yet
            articles.append({...})
    
    return articles
```

**Key Query Methods:**
- `.filter()` - Filter results (like WHERE in SQL)
- `.filter_by()` - Simpler filtering by exact match
- `.all()` - Get all results
- `.first()` - Get first result (or None)

---

## 🎬 STEP 4: YouTube Scraper

### How It Works:

1. **Get RSS Feed URL**
   ```python
   def _get_rss_url(self, channel_id: str) -> str:
       return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
   ```
   - YouTube provides RSS feeds for every channel
   - RSS = Really Simple Syndication (XML format with latest content)

2. **Parse RSS Feed**
   ```python
   feed = feedparser.parse(self._get_rss_url(channel_id))
   ```
   - `feedparser` library reads RSS XML
   - Returns structured data (title, link, published date, etc.)

3. **Extract Video ID**
   ```python
   def _extract_video_id(self, video_url: str) -> str:
       if "youtube.com/watch?v=" in video_url:
           return video_url.split("v=")[1].split("&")[0]
   ```
   - YouTube URLs have different formats
   - We extract the unique video ID from any format

4. **Filter by Time**
   ```python
   cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
   if published_time >= cutoff_time:
       # Include this video
   ```
   - Only get videos from last 24 hours (or whatever you specify)

5. **Get Transcripts**
   ```python
   transcript = self.transcript_api.fetch(video_id)
   text = " ".join([snippet.text for snippet in transcript.snippets])
   ```
   - Uses `youtube-transcript-api` library
   - Some videos don't have transcripts → returns None
   - Handles errors gracefully

### Key Concepts:

**Pydantic Models** - Data validation
```python
class ChannelVideo(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: datetime
    description: str
    transcript: Optional[str] = None
```
- Ensures data types are correct
- Validates before using
- Catches errors early

**Error Handling**
```python
try:
    transcript = self.transcript_api.fetch(video_id)
    return Transcript(text=text)
except (TranscriptsDisabled, NoTranscriptFound):
    return None  # Not available, that's okay
except Exception:
    return None  # Something else went wrong, skip it
```
- Some videos don't have transcripts → not an error, just skip
- Other errors → also skip (don't crash the whole process)

---

## 📧 STEP 5: Processing Services

### What is Processing?

Converting raw content into usable formats:
- YouTube: Get transcripts for videos that don't have them yet
- Anthropic: Convert HTML articles to markdown format

### YouTube Processing Flow:

```python
def process_youtube_transcripts():
    repo = Repository()
    scraper = YouTubeScraper()
    
    # 1. Find videos without transcripts
    videos = repo.get_youtube_videos_without_transcript()
    
    # 2. Process each video
    for video in videos:
        transcript = scraper.get_transcript(video.video_id)
        
        if transcript:
            # Save transcript
            repo.update_youtube_video_transcript(video.video_id, transcript.text)
        else:
            # Mark as unavailable
            repo.update_youtube_video_transcript(video.video_id, "__UNAVAILABLE__")
```

**Key Points:**
- Only processes videos that need it (efficient)
- Handles unavailable transcripts gracefully
- Updates database as it goes

### Anthropic Processing Flow:

```python
def process_anthropic_markdown():
    repo = Repository()
    scraper = AnthropicScraper()
    
    # 1. Find articles without markdown
    articles = repo.get_anthropic_articles_without_markdown()
    
    # 2. For each article, fetch and convert to markdown
    for article in articles:
        markdown = scraper.fetch_and_convert_to_markdown(article.url)
        repo.update_anthropic_article_markdown(article.guid, markdown)
```

**Why Markdown?**
- Easier for AI to process
- Cleaner than HTML
- Better for summarization

---

## 🤖 STEP 6: AI Agents

### What are AI Agents?

Functions that use AI (OpenAI API) to:
- Create summaries of articles
- Format email content
- Curate interesting articles

### Digest Agent Flow:

```python
def create_digest(article_content: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create a prompt (instructions for AI)
    prompt = f"""
    Summarize this article in 3-4 sentences.
    Focus on key insights and main points.
    
    Article:
    {article_content}
    """
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract summary
    summary = response.choices[0].message.content
    return summary
```

**Key Concepts:**

**1. Prompts** - Instructions for AI
- Better prompts = better results
- Be specific about what you want
- Include examples if helpful

**2. API Calls**
- Send request to OpenAI
- Wait for response
- Extract the result

**3. Error Handling**
- API can fail (rate limits, network issues)
- Always have fallbacks
- Log errors for debugging

### Email Agent Flow:

```python
def generate_email_content(digests: List[Dict]) -> str:
    # Format digests into HTML email
    html = "<h1>Your Daily AI News Digest</h1>"
    
    for digest in digests:
        html += f"""
        <h2>{digest['title']}</h2>
        <p>{digest['summary']}</p>
        <a href="{digest['url']}">Read more</a>
        """
    
    return html
```

---

## 🎯 STEP 7: Main Pipeline

### The Orchestrator

`daily_runner.py` runs everything in order:

```python
def run_daily_pipeline():
    # Step 1: Scrape new articles
    scraping_results = run_scrapers(hours=24)
    
    # Step 2: Process Anthropic articles (HTML → Markdown)
    process_anthropic_markdown()
    
    # Step 3: Process YouTube videos (get transcripts)
    process_youtube_transcripts()
    
    # Step 4: Create digests (AI summaries)
    process_digests()
    
    # Step 5: Send email
    send_digest_email(hours=24, top_n=10)
```

### Error Handling Strategy:

```python
try:
    # Run pipeline
    results = run_daily_pipeline()
except Exception as e:
    logger.error(f"Pipeline failed: {e}")
    results["success"] = False
    results["error"] = str(e)

# Always log results
logger.info(f"Scraped: {results['scraping']}")
logger.info(f"Processed: {results['processing']}")
```

**Key Points:**
- Each step can fail independently
- Log everything for debugging
- Continue even if one step fails
- Return summary of what worked/failed

---

## 🚀 Next: Let's Start Building!

Ready to code? Let's start with:

1. **Setting up the project structure**
2. **Creating the database models**
3. **Building the connection layer**

Which component would you like to dive deeper into first?
