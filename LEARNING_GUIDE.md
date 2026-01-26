# Learning Guide: Building the AI News Aggregator Step by Step

This guide will help you understand and build each component of the project.

## 🎯 Project Overview

**What it does:** Automatically collects news from multiple sources, processes them with AI, and sends you a daily email digest.

**The Flow:**
```
1. Scrape → 2. Process → 3. Digest → 4. Email
```

---

## 📚 Part 1: Understanding the Database Layer

### Why we need a database?
We need to store:
- Articles we've scraped (so we don't duplicate)
- Transcripts and markdown content
- AI-generated summaries (digests)

### Key Files:
- `app/database/models.py` - Defines what data we store
- `app/database/connection.py` - Connects to PostgreSQL
- `app/database/repository.py` - Functions to save/retrieve data

### Concepts to understand:

**1. SQLAlchemy Models** (`models.py`)
- Think of these as "blueprints" for database tables
- Each class = one table
- Each attribute = one column

Example:
```python
class YouTubeVideo(Base):
    video_id = Column(String, primary_key=True)  # Unique identifier
    title = Column(String, nullable=False)       # Required field
    transcript = Column(Text, nullable=True)      # Optional field
```

**2. Repository Pattern** (`repository.py`)
- A "middleman" between your code and database
- Instead of writing SQL directly, you call functions like:
  - `create_youtube_video()` - Save a video
  - `get_articles_without_digest()` - Find articles that need summaries

**Why use this pattern?**
- Cleaner code
- Easier to test
- Can swap databases without changing your code

---

## 📚 Part 2: Understanding Scrapers

### What are scrapers?
Programs that automatically fetch content from websites.

### Key Files:
- `app/scrapers/youtube.py` - Gets YouTube videos
- `app/scrapers/openai.py` - Gets OpenAI blog posts
- `app/scrapers/anthropic.py` - Gets Anthropic blog posts

### How YouTube Scraper Works:

1. **RSS Feed** - YouTube provides RSS feeds for channels
   - URL format: `https://www.youtube.com/feeds/videos.xml?channel_id={ID}`
   
2. **Parse Feed** - Use `feedparser` library to read RSS
   - Gets video titles, URLs, publish dates

3. **Get Transcripts** - Use `youtube-transcript-api` library
   - Fetches auto-generated captions
   - Some videos don't have transcripts (returns None)

### Key Concepts:

**Pydantic Models** - Data validation
```python
class ChannelVideo(BaseModel):
    title: str                    # Must be a string
    url: str                      # Must be a string
    transcript: Optional[str]     # Can be string or None
```
- Ensures data is correct before using it
- Catches errors early

**Time Filtering** - Only get recent videos
```python
cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
# Only include videos published after this time
```

---

## 📚 Part 3: Understanding Processing Services

### What is processing?
Converting raw content into usable formats:
- YouTube: Transcripts → Text
- Anthropic: HTML → Markdown

### Key Files:
- `app/services/process_youtube.py` - Fetches missing transcripts
- `app/services/process_anthropic.py` - Converts HTML to markdown

### How Processing Works:

1. **Find unprocessed items**
   ```python
   videos = repo.get_youtube_videos_without_transcript()
   # Gets all videos that don't have transcripts yet
   ```

2. **Process each item**
   ```python
   transcript = scraper.get_transcript(video_id)
   repo.update_youtube_video_transcript(video_id, transcript)
   ```

3. **Handle failures gracefully**
   - Some transcripts aren't available → mark as unavailable
   - Some processing fails → log error, continue with next item

---

## 📚 Part 4: Understanding AI Agents

### What are agents?
AI-powered functions that:
- **Curator Agent**: Decides which articles are interesting
- **Digest Agent**: Creates summaries of articles
- **Email Agent**: Formats and sends the email

### Key Files:
- `app/agent/digest_agent.py` - Creates summaries using OpenAI
- `app/agent/email_agent.py` - Generates email content

### How AI Agents Work:

**1. Digest Agent** - Creates summaries
```python
# Takes article content
# Sends to OpenAI API with a prompt
# Gets back a summary
# Saves summary to database
```

**2. Email Agent** - Formats email
```python
# Gets recent digests from database
# Formats them into HTML email
# Sends via email service
```

**Key Concept: Prompt Engineering**
- The "prompt" is instructions you give to AI
- Better prompts = better results
- Example: "Summarize this article in 3 sentences focusing on key insights"

---

## 📚 Part 5: Understanding the Main Pipeline

### The Orchestrator (`daily_runner.py`)

This is the "conductor" that runs everything in order:

```python
1. run_scrapers()           # Get new articles
2. process_anthropic()      # Convert HTML to markdown
3. process_youtube()        # Get transcripts
4. process_digests()        # Create AI summaries
5. send_digest_email()      # Send email
```

### Error Handling:
- Each step can fail
- We log errors but continue
- Final result shows what succeeded/failed

---

## 🛠️ Building Order (Recommended)

Build in this order to understand dependencies:

1. **Database Layer** (foundation)
   - Models → Connection → Repository

2. **Scrapers** (data collection)
   - YouTube → OpenAI → Anthropic

3. **Processing** (data transformation)
   - Process YouTube → Process Anthropic

4. **Agents** (AI processing)
   - Digest Agent → Email Agent

5. **Pipeline** (orchestration)
   - Runner → Daily Runner → Main

---

## 💡 Key Programming Concepts You'll Learn

1. **Object-Oriented Programming (OOP)**
   - Classes and objects
   - Methods and attributes

2. **Database ORM (Object-Relational Mapping)**
   - SQLAlchemy
   - Models and queries

3. **API Integration**
   - HTTP requests
   - API keys and authentication

4. **Error Handling**
   - Try/except blocks
   - Graceful failures

5. **Environment Variables**
   - `.env` files
   - Keeping secrets safe

6. **Package Management**
   - Dependencies
   - Virtual environments

---

## 🚀 Next Steps

Ready to start building? Let's begin with:

1. **Setting up the project structure**
2. **Understanding the database models**
3. **Building the repository layer**

Which would you like to start with?
