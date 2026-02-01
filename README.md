# 🤖 AI News Aggregator

An intelligent, automated news aggregation system that collects AI-related content from multiple sources, processes it with AI, and delivers a curated daily newsletter directly to your inbox.

## 📖 What is This Project?

**AI News Aggregator** is a Python-based automation system that:
- **Scrapes** AI news from top sources (YouTube channels, OpenAI blog, Anthropic research, Formula 1 AI content)
- **Processes** content using AI to extract transcripts, convert markdown, and generate summaries
- **Curates** the most relevant articles using AI-powered ranking
- **Delivers** a beautifully formatted daily email digest with featured articles and additional links

Perfect for staying up-to-date with the latest developments in AI without manually checking multiple sources every day.

---

## 🎯 What Does This Project Do?

### Core Functionality

1. **Multi-Source Content Collection**
   - 🎬 **YouTube**: Scrapes videos from configured AI-focused channels
   - 🤖 **OpenAI**: Fetches blog posts and announcements from OpenAI
   - 🧠 **Anthropic**: Collects research papers and engineering updates from Anthropic
   - 🏎️ **Formula 1**: Gathers AI-related Formula 1 content

2. **Intelligent Content Processing**
   - Extracts and processes YouTube video transcripts
   - Converts Anthropic markdown articles to readable format
   - Stores all content in PostgreSQL database for efficient retrieval

3. **AI-Powered Summarization**
   - Uses Google Gemini API to generate concise, informative summaries
   - Creates compelling titles and 2-3 sentence summaries for featured articles
   - Focuses on actionable insights and key implications

4. **Smart Curation & Ranking**
   - AI-powered curator ranks articles by relevance and importance
   - Selects top articles from each source for featured section
   - Includes additional links grouped by source

5. **Automated Email Delivery**
   - Generates beautifully formatted HTML email newsletters
   - Includes personalized introduction using AI
   - Sends daily digest to your email address

---

## 🔄 Project Flow

### Daily Pipeline Execution

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY PIPELINE                            │
└─────────────────────────────────────────────────────────────┘

Step 0: 🗑️  Cleanup
├─ Deletes data older than 7 days
└─ Keeps database size manageable

Step 1: 📡 Scraping
├─ YouTube: Fetch latest videos from configured channels
├─ OpenAI: Get recent blog posts from RSS feed
├─ Anthropic: Collect articles from research/engineering feeds
└─ Formula 1: Gather AI-related F1 content

Step 2: 📄 Processing
├─ Anthropic: Convert markdown articles to readable format
└─ YouTube: Extract and process video transcripts

Step 3: 🤖 AI Digests
├─ Select top 1 article from each source (past 24 hours)
├─ Generate AI summaries using Gemini API
└─ Create compelling titles and summaries

Step 4: 📧 Newsletter Generation
├─ Rank articles by relevance (AI-powered curator)
├─ Generate personalized email introduction
├─ Format featured articles with AI summaries
├─ Add additional links grouped by source
└─ Send beautiful HTML email to MY_EMAIL

┌─────────────────────────────────────────────────────────────┐
│                    RESULT                                    │
└─────────────────────────────────────────────────────────────┘
📬 Daily email digest delivered to your inbox!
```

### Newsletter Format

Each email includes:

- **🎬 YOUTUBE** - Featured video with AI-generated summary
- **🤖 OPENAI** - Featured blog post with AI summary
- **🧠 ANTHROPIC** - Featured research/update with AI summary
- **🏎️ F1** - Featured Formula 1 AI content with summary
- **📚 MORE ARTICLES** - Additional links organized by source

---

## 🏗️ Architecture

### Technology Stack

- **Language**: Python 3.12+
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **AI API**: Google Gemini (for summaries and curation)
- **Email**: SMTP (Gmail)
- **Web Framework**: Flask (for API endpoints)
- **Scraping**: RSS feeds, YouTube API, feedparser

### Key Components

```
app/
├── scrapers/          # Content scrapers for each source
│   ├── youtube.py
│   ├── openai.py
│   ├── anthropic.py
│   └── formula1.py
├── services/          # Processing services
│   ├── process_anthropic.py
│   ├── process_youtube.py
│   ├── process_digest.py
│   └── process_email.py
├── agent/             # AI agents
│   ├── digest_agent.py    # Generates summaries
│   ├── curator_agent.py    # Ranks articles
│   └── email_agent.py      # Creates email content
├── database/          # Database layer
│   ├── models.py          # SQLAlchemy models
│   ├── repository.py      # Data access layer
│   └── connection.py      # Database connection
└── daily_runner.py    # Main pipeline orchestrator
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL database
- Google Gemini API key
- Gmail account with app password

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-news-aggregator.git
   cd ai-news-aggregator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or using uv
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp app/example.env .env
   # Edit .env with your credentials
   ```

4. **Configure database**
   ```bash
   # Start PostgreSQL (using Docker)
   cd docker && docker-compose up -d && cd ..
   
   # Create tables
   python app/database/create_tables.py
   ```

5. **Run the pipeline**
   ```bash
   python main.py
   ```

---

## 📊 Features

- ✅ **Automated Daily Execution** - Runs automatically via cron job
- ✅ **Multi-Source Aggregation** - Collects from 4+ sources
- ✅ **AI-Powered Summaries** - Uses Gemini for intelligent summarization
- ✅ **Smart Curation** - AI ranks articles by relevance
- ✅ **Beautiful Email Format** - Professional HTML newsletter design
- ✅ **Data Retention** - Automatically cleans up old data (7-day retention)
- ✅ **API Endpoints** - Flask API for manual triggers and health checks
- ✅ **Error Handling** - Robust error handling and logging

---

## 🔧 Configuration

Key configuration options (in `app/api_config.py`):

- `SCRAPE_HOURS`: How far back to scrape (default: 168 hours / 7 days)
- `NEWSLETTER_HOURS`: Articles to include in newsletter (default: 24 hours)
- `DATA_RETENTION_HOURS`: How long to keep data (default: 168 hours / 7 days)
- `TOP_PER_SOURCE`: Featured articles per source (default: 1)
- `ADDITIONAL_LINKS_PER_SOURCE`: Extra links per source (default: 5)

---

## 📝 Environment Variables

Required environment variables:

```env
# AI API
GEMINI_API_KEY=your_gemini_api_key

# Email Configuration (Resend for Render; Gmail SMTP for local)
MY_EMAIL=your_email@gmail.com
RESEND_API_KEY=re_xxx    # From resend.com/api-keys (required on Render)
FROM_EMAIL=onboarding@resend.dev
# APP_PASSWORD=xxx       # Optional: Gmail app password for local SMTP

# Database (local development)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_news_aggregator

# Or use DATABASE_URL for cloud deployment
# DATABASE_URL=postgresql://user:password@host:port/database
```

---

## 🌐 Deployment

The project includes deployment configuration for **Render**:

- **Database**: PostgreSQL (free tier)
- **Web Service**: Flask API with `/health` and `/trigger-newsletter` endpoints
- **Cron Job**: Automated daily execution

See `RENDER_DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

---

## 📈 API Usage

The system uses approximately **5 API calls per run**:
- 4 calls for AI digests (1 per source)
- 1 call for email introduction/curation

This keeps costs low while providing intelligent summarization.

---

## 🗺️ Roadmap & Future Plans

### Current Status
✅ **Phase 1: Core Functionality** - Complete
- Multi-source content aggregation
- AI-powered summarization
- Automated email delivery
- Local development setup

### Next Steps

**🚀 Phase 2: Deployment** (In Progress)
- Cloud deployment on Render
- Production-ready infrastructure
- Automated daily execution via cron jobs
- API endpoints for manual triggers

**👥 Phase 3: Multi-Subscriber Support** (Planned)
- User subscription management system
- Customizable newsletter preferences
- **Source Selection**: Subscribers can choose which sources they want (YouTube, OpenAI, Anthropic, F1)
- **Content Filtering**: Options to filter by topics, keywords, or categories
- **Delivery Frequency**: Choose daily, weekly, or custom schedules
- **Personalization**: AI-powered content recommendations based on reading preferences
- Unsubscribe management and email preferences

---

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

---

## 📄 License

This project is open source and available for educational purposes.

---

## 🙏 Acknowledgments

- **Google Gemini** for AI summarization
- **OpenAI, Anthropic** for providing RSS feeds
- **YouTube** for video content
- **PostgreSQL** for reliable data storage

---

**Built with ❤️ using Python and AI**
