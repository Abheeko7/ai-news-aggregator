# Render Cron Job Setup Plan

**Goal:** Run the newsletter pipeline entirely on Render using a cron job. No GitHub Actions needed.

---

## Overview

| Component | What it does | Cost |
|-----------|--------------|------|
| **PostgreSQL** | Stores articles, digests, subscribers | Free (or keep current) |
| **Web Service** (optional) | `/health`, manual trigger | Free or $7/mo |
| **Cron Job** | Runs pipeline daily (scrape → digest → send) | **$1/month minimum** |

**Estimated total:** ~$1–8/month (cron minimum + optional web service)

---

## What You Need

### 1. Render Account
- Hobby plan: $0 + compute
- Professional: $19/user + compute (if you need team features)
- **Cron jobs work on Hobby** — you don't need Professional for cron

### 2. Environment Variables
- `DATABASE_URL` (from Postgres)
- `GEMINI_API_KEY`
- `MY_EMAIL`
- `APP_PASSWORD` (Gmail App Password — required for sending to multiple users)
- `SUBSCRIBERS_CSV_URL` (Google Sheet CSV)
- `CRON_SECRET` (optional)

---

## Step-by-Step Setup

### Step 1: Create the Cron Job on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Select your project (or create one)
3. Click **New +** → **Cron Job**
4. Connect your GitHub repo (same as your web service)
5. Choose branch: `deployment` or `main`

### Step 2: Configure the Cron Job

| Field | Value |
|-------|-------|
| **Name** | `ai-news-newsletter` |
| **Schedule** | `0 8 * * *` (daily at 8:00 AM UTC) — change as needed |
| **Command** | `python -m app.daily_runner` |
| **Build Command** | `pip install -r requirements.txt` |
| **Instance Type** | Starter (512 MB) — $0.00016/min |

### Step 3: Set Environment Variables

Add the same env vars as your web service:

- `DATABASE_URL` — from your Postgres (use "Add from Database" or paste)
- `GEMINI_API_KEY`
- `MY_EMAIL`
- `APP_PASSWORD` — Gmail App Password (Google Account → Security → App passwords)
- `SUBSCRIBERS_CSV_URL`

**Tip:** Use **Environment Groups** to share vars across Web Service + Cron Job.

### Step 4: Save & Deploy

1. Click **Create Cron Job**
2. Render will build and run on the schedule
3. Test: click **Trigger Run** to run once manually

---

## Cron Schedule Examples (UTC)

| You want | Cron expression |
|----------|-----------------|
| Daily at 8 AM UTC | `0 8 * * *` |
| Daily at 12:30 AM UTC | `30 0 * * *` |
| Daily at 6 PM UTC | `0 18 * * *` |
| Twice daily (8 AM & 8 PM) | `0 8,20 * * *` |

**Convert to your timezone:** [crontab.guru](https://crontab.guru) — e.g. 8 AM PST = 4 PM UTC → `0 16 * * *`

---

## Do You Still Need the Web Service?

| Keep Web Service? | When |
|-------------------|------|
| **Yes** | You want `/health`, `/trigger-newsletter` for manual runs, or `/import-subscribers` |
| **No** | Cron runs everything; you only need the cron job + Postgres |

**Recommendation:** Keep the web service on Free tier if you want manual triggers. Otherwise, you can remove it.

---

## Do You Still Need GitHub Actions?

**No.** The Render cron job replaces the GitHub Actions workflow.

You can:
1. Delete or disable the `.github/workflows/newsletter.yml` workflow
2. Remove `RENDER_SERVICE_URL` and `CRON_SECRET` from GitHub secrets (optional)

---

## Costs Summary

| Item | Cost |
|------|------|
| Cron Job (Starter) | $1/month minimum (runs ~2 min/day ≈ 60 min/month → ~$0.01 compute, but $1 min) |
| Web Service (Free) | $0 |
| Postgres (Free) | $0 |
| **Total** | **~$1/month** |

If you use Professional plan ($19/user), that's extra. Cron jobs work fine on Hobby.

---

## Checklist

- [ ] Create Cron Job in Render Dashboard
- [ ] Set repo + branch
- [ ] Schedule: `0 8 * * *` (or your preferred time)
- [ ] Command: `python -m app.daily_runner`
- [ ] Add all env vars (DATABASE_URL, GEMINI_API_KEY, MY_EMAIL, APP_PASSWORD, SUBSCRIBERS_CSV_URL)
- [ ] Trigger Run once to test
- [ ] GitHub Actions workflow already disabled (newsletter.yml removed)

---

## Troubleshooting

**Cron job fails?**
- Check **Logs** tab on the cron job page
- Ensure DATABASE_URL is correct (same Postgres as web service)
- Ensure APP_PASSWORD (Gmail) is set

**Emails not sending to subscribers?**
- Verify APP_PASSWORD is a Gmail App Password (not your regular password)
- Generate at: Google Account → Security → 2-Step Verification → App passwords

**Cron runs but no emails?**
- Check Render cron logs for errors
- Verify SUBSCRIBERS_CSV_URL is set and accessible
