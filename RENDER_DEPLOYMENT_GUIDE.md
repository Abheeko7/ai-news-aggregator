# Render Deployment Guide - Step by Step

This guide walks you through deploying the AI News Aggregator on Render using the Blueprint.

## 📋 Prerequisites

Before starting, make sure you have:

1. ✅ **GitHub account** with your repository pushed
2. ✅ **Render account** (sign up at https://render.com)
3. ✅ **Gmail App Password** (for sending emails)
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate an app password for "Mail"
4. ✅ **Google Gemini API Key**
   - Get it from https://aistudio.google.com/apikey

---

## 🚀 Step-by-Step Deployment

### Step 1: Push Your Code to GitHub

Make sure your `deployment` branch is pushed to GitHub:

```bash
git add .
git commit -m "Add Render deployment files"
git push origin deployment
```

Verify the branch exists at: `https://github.com/YOUR_USERNAME/ai-news-aggregator/tree/deployment`

---

### Step 2: Create Render Account & Connect GitHub

1. Go to **https://render.com** and sign up/login
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Select your repository: **`ai-news-aggregator`**
5. Select branch: **`deployment`**
6. Render will detect `render.yaml` automatically

---

### Step 3: Configure Environment Variables

When Render shows the "Specified configurations" screen, you'll need to set these values:

#### For Web Service (`ai-news-api`):

| Variable | Required | What to Enter |
|----------|----------|---------------|
| `CRON_SECRET` | **No** | Leave **empty** if using only Render cron. Otherwise, generate: `openssl rand -hex 24` |
| `GEMINI_API_KEY` | **Yes** | Your Google Gemini API key |
| `MY_EMAIL` | **Yes** | Email address that receives newsletters (e.g., `yourname@gmail.com`) |
| `APP_PASSWORD` | **Yes** | Gmail app password (16 characters, e.g., `abcd efgh ijkl mnop`) |

#### For Cron Job (`ai-news-daily-pipeline`):

| Variable | Required | What to Enter |
|----------|----------|---------------|
| `GEMINI_API_KEY` | **Yes** | Same as web service |
| `MY_EMAIL` | **Yes** | Same as web service |
| `APP_PASSWORD` | **Yes** | Same as web service |

**Note:** `DATABASE_URL` is automatically set by Render - you don't need to enter it manually.

---

### Step 4: Review & Deploy

1. Review the configuration:
   - ✅ Database: `ai-news-aggregator-db` (free tier)
   - ✅ Web service: `ai-news-api` (free tier)
   - ✅ Cron job: `ai-news-daily-pipeline` (starter plan - **$7/month**)

2. Click **"Apply"** or **"Create Blueprint"**

3. Render will start creating resources:
   - Database creation (~2 minutes)
   - Web service build & deploy (~5-10 minutes)
   - Cron job setup (~2 minutes)

---

### Step 5: Wait for Deployment

Watch the deployment logs:

1. **Database** should show ✅ "Create database ai-news-aggregator-db"
2. **Web service** will build (installing dependencies, creating tables)
3. **Cron job** will be configured

**Expected build output:**
```
pip install -r requirements.txt
python app/database/create_tables.py
Tables created successfully
```

---

### Step 6: Test the Deployment

#### Test Web Service Health Check:

Visit: `https://ai-news-api.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T..."
}
```

#### Test Manual Newsletter Trigger:

```bash
curl -X POST https://ai-news-api.onrender.com/trigger-newsletter
```

Or if you set `CRON_SECRET`:
```bash
curl -X POST https://ai-news-api.onrender.com/trigger-newsletter \
  -H "X-Cron-Secret: your-secret-here"
```

#### Test Cron Job Manually:

1. Go to Render Dashboard → **Cron Jobs** → `ai-news-daily-pipeline`
2. Click **"Trigger Run"** to run it immediately
3. Check logs to see the pipeline execution

---

## 📧 Step 7: Verify Email Delivery

After the cron runs (or manual trigger):

1. Check your email inbox (`MY_EMAIL`)
2. Check spam folder if not found
3. You should receive a newsletter with:
   - Featured articles (1 per source with AI summaries)
   - Additional links grouped by source

---

## 🔧 Troubleshooting

### Issue: Build fails with "Module not found"

**Solution:** Check `requirements.txt` includes all dependencies. The file should have `flask` and `google-genai`.

### Issue: Database connection error

**Solution:** 
- Verify `DATABASE_URL` is set automatically (from database)
- Check database is created and running
- Ensure `app/database/connection.py` supports `DATABASE_URL`

### Issue: Email not sending

**Solution:**
- Verify `MY_EMAIL` and `APP_PASSWORD` are correct
- Check `APP_PASSWORD` is a Gmail app password (16 chars, not your regular password)
- Check Render logs for SMTP errors

### Issue: Cron job not running

**Solution:**
- Verify cron job is on **starter plan** (paid) - free tier doesn't support cron
- Check schedule: `0 8 * * *` means 8:00 AM UTC daily
- Manually trigger a run to test

### Issue: API returns 401 Unauthorized

**Solution:**
- If you set `CRON_SECRET`, include it in the `X-Cron-Secret` header
- Or leave `CRON_SECRET` empty if you don't need protection

---

## 📊 What Gets Created

| Resource | Type | Plan | Purpose |
|----------|------|------|---------|
| `ai-news-aggregator-db` | PostgreSQL | Free | Stores articles, digests |
| `ai-news-api` | Web Service | Free | `/health`, `/trigger-newsletter` endpoints |
| `ai-news-daily-pipeline` | Cron Job | Starter ($7/mo) | Runs `main.py` daily at 8 AM UTC |

---

## 💰 Cost Estimate

- **Database (free tier):** $0/month
- **Web service (free tier):** $0/month (spins down after inactivity)
- **Cron job (starter):** **$7/month** (minimum)

**Total: ~$7/month** (plus any API usage costs for Gemini)

---

## 🔄 Updating Deployment

To update your deployment:

1. Make changes to your code
2. Commit and push to `deployment` branch:
   ```bash
   git add .
   git commit -m "Update code"
   git push origin deployment
   ```
3. Render will automatically detect changes and redeploy

---

## 📝 Environment Variables Reference

### Required for Both Services:

- `GEMINI_API_KEY` - Google Gemini API key
- `MY_EMAIL` - Email address to receive newsletters
- `APP_PASSWORD` - Gmail app password

### Web Service Only:

- `CRON_SECRET` - Optional secret to protect `/trigger-newsletter`

### Auto-Set by Render:

- `DATABASE_URL` - PostgreSQL connection string (from database)
- `PORT` - Web service port (default: 5000)
- `PYTHON_VERSION` - Python version (3.12.3)

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Database created successfully
- [ ] Web service is running (`/health` returns 200)
- [ ] Cron job is scheduled (shows next run time)
- [ ] Manual trigger works (`/trigger-newsletter`)
- [ ] Email received successfully
- [ ] Cron job runs automatically (check logs after scheduled time)

---

## 🆘 Need Help?

- **Render Docs:** https://render.com/docs
- **Render Support:** https://render.com/support
- **Check Logs:** Render Dashboard → Your Service → Logs

---

**🎉 Congratulations!** Your AI News Aggregator is now deployed on Render!
