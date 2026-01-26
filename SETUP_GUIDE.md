# Step-by-Step Setup Guide for AI News Aggregator

This guide will walk you through building this project from scratch, step by step.

## Prerequisites Checklist

Before we start, you need:

- [ ] **Python 3.12 or higher** (you currently have 3.9.6 - we'll need to upgrade)
- [ ] **PostgreSQL database** (we'll set this up with Docker)
- [ ] **API Keys**:
  - [ ] OpenAI API key
  - [ ] Email credentials (Gmail app password)
- [ ] **Package manager**: `uv` (we'll install this)

---

## Step 1: Install Python 3.12+

**On macOS (using Homebrew):**
```bash
brew install python@3.12
```

**Verify installation:**
```bash
python3.12 --version
```

**Alternative:** If you prefer, you can use `pyenv` to manage multiple Python versions.

---

## Step 2: Install UV Package Manager

UV is a fast Python package manager. Install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with Homebrew:
```bash
brew install uv
```

**Verify:**
```bash
uv --version
```

---

## Step 3: Set Up Project Structure

Create your project directory structure:

```
ai-news-aggregator/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── runner.py
│   ├── daily_runner.py
│   ├── example.env
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── curator_agent.py
│   │   ├── digest_agent.py
│   │   └── email_agent.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── create_tables.py
│   ├── profiles/
│   │   ├── __init__.py
│   │   └── user_profile.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── youtube.py
│   │   ├── openai.py
│   │   └── anthropic.py
│   └── services/
│       ├── __init__.py
│       ├── process_anthropic.py
│       ├── process_curator.py
│       ├── process_digest.py
│       ├── process_email.py
│       └── process_youtube.py
├── docker/
│   └── docker-compose.yml
├── main.py
├── pyproject.toml
└── README.md
```

---

## Step 4: Initialize Project with UV

In your project directory:

```bash
uv init
```

This creates a `pyproject.toml` file. We'll configure it next.

---

## Step 5: Configure Dependencies

Create/update `pyproject.toml` with all required packages (see the existing file for reference).

Then install dependencies:
```bash
uv sync
```

---

## Step 6: Set Up PostgreSQL Database

**Option A: Using Docker (Recommended)**

1. Make sure Docker is installed and running
2. Navigate to the `docker/` directory
3. Run:
```bash
docker-compose up -d
```

This starts PostgreSQL in a container.

**Option B: Local PostgreSQL**

Install PostgreSQL locally and create a database named `ai_news_aggregator`.

---

## Step 7: Configure Environment Variables

1. Copy `app/example.env` to `.env` in the project root
2. Fill in your API keys and credentials:
   - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
   - `MY_EMAIL` - Your email address
   - `APP_PASSWORD` - Gmail app password (if using Gmail)
   - Database credentials (should match docker-compose.yml)

---

## Step 8: Create Database Tables

Run the table creation script:
```bash
python app/database/create_tables.py
```

---

## Step 9: Build Each Component

We'll build the project in this order:

1. **Database Layer** (models, connection, repository)
2. **Scrapers** (YouTube, OpenAI, Anthropic)
3. **Processing Services** (markdown, transcripts)
4. **AI Agents** (curator, digest, email)
5. **Main Pipeline** (daily_runner.py)

---

## Step 10: Test the Pipeline

Run the main script:
```bash
python main.py
```

Or with custom parameters:
```bash
python main.py 24 10  # hours=24, top_n=10
```

---

## Next Steps

Follow along as we build each component. I'll explain:
- What each file does
- How the components connect
- Key concepts you need to understand
- Common pitfalls and how to avoid them

Ready to start? Let me know which step you'd like to begin with!
