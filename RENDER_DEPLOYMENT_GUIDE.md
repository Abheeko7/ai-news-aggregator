# Render Deployment Guide - Step by Step

This guide walks you through deploying the AI News Aggregator on Render using the Blueprint.

## 📋 Prerequisites

Before starting, make sure you have:

1. ✅ **GitHub account** with your repository pushed
2. ✅ **Render account** (sign up at https://render.com)
3. ✅ **Resend API Key** (for sending emails on Render — SMTP is blocked on free tier)
   - Sign up at https://resend.com
   - Create API key at https://resend.com/api-keys
   - Use `onboarding@resend.dev` as sender for testing (or verify your domain)
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

#### For Web Service (`ai-news-api`) — only service that needs env vars:

| Variable | Required | What to Enter |
|----------|----------|---------------|
| `CRON_SECRET` | **No** | Leave **empty** (or set + add to GitHub secrets; see GITHUB_ACTIONS_SETUP.md) |
| `GEMINI_API_KEY` | **Yes** | Your Google Gemini API key |
| `MY_EMAIL` | **Yes** | Email address that receives newsletters (e.g., `yourname@gmail.com`) |
| `RESEND_API_KEY` | **Yes** | Resend API key (from https://resend.com/api-keys) |
| `FROM_EMAIL` | **No** | Sender email; default `onboarding@resend.dev` for testing |

**Note:** `DATABASE_URL` is automatically set by Render. **No cron job** — newsletter is triggered by GitHub Actions (free). See GITHUB_ACTIONS_SETUP.md. Resend is required on Render (Gmail SMTP is blocked on free tier).

---

### Step 4: Review & Deploy

1. Review the configuration (all FREE — no payment):
   - ✅ Database: `ai-news-aggregator-db` (free tier)
   - ✅ Web service: `ai-news-api` (free tier)
   - ❌ No cron job (use GitHub Actions instead — see GITHUB_ACTIONS_SETUP.md)

2. Click **"Apply"** or **"Create Blueprint"**

3. Render will start creating resources:
   - Database creation (~2 minutes)
   - Web service build & deploy (~5-10 minutes)

---

### Step 5: Wait for Deployment

Watch the deployment logs:

1. **Database** should show ✅ "Create database ai-news-aggregator-db"
2. **Web service** will build (installing dependencies, creating tables)

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

#### Test via GitHub Actions:

1. Go to your repo → **Actions** → **Daily Newsletter Trigger**
2. Click **Run workflow** to trigger immediately
3. Check logs — see GITHUB_ACTIONS_SETUP.md for full setup

---

## 📧 Step 7: Verify Email Delivery

After triggering (manual curl or GitHub Actions):

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
- Verify `MY_EMAIL` and `RESEND_API_KEY` are set in Render
- Ensure `FROM_EMAIL` is valid (use `onboarding@resend.dev` for testing)
- Check Render logs for Resend API errors

### Issue: Newsletter not triggering automatically

**Solution:**
- Use GitHub Actions (free) — see GITHUB_ACTIONS_SETUP.md
- Ensure RENDER_SERVICE_URL secret is set in GitHub
- For scheduled runs, workflow must be on default branch (main)

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

**Newsletter trigger:** GitHub Actions (free) — see GITHUB_ACTIONS_SETUP.md

---

## 💰 Cost Estimate

- **Database (free tier):** $0/month
- **Web service (free tier):** $0/month (spins down after inactivity)
- **GitHub Actions:** $0/month

**Total: $0/month** (plus any API usage costs for Gemini)

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

### Required for Web Service:

- `GEMINI_API_KEY` - Google Gemini API key
- `MY_EMAIL` - Email address to receive newsletters
- `RESEND_API_KEY` - Resend API key (required on Render; SMTP blocked on free tier)

### Optional:

- `FROM_EMAIL` - Sender email; defaults to `onboarding@resend.dev`
- `CRON_SECRET` - Secret to protect `/trigger-newsletter` (when using GitHub Actions)

### Auto-Set by Render:

- `DATABASE_URL` - PostgreSQL connection string (from database)
- `PORT` - Web service port (default: 5000)
- `PYTHON_VERSION` - Python version (3.12.3)

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Database created successfully
- [ ] Web service is running (`/health` returns 200)
- [ ] RESEND_API_KEY and MY_EMAIL set in Render
- [ ] GitHub Actions workflow set up (RENDER_SERVICE_URL secret)
- [ ] Manual trigger works (`/trigger-newsletter` or Run workflow)
- [ ] Email received successfully

---

## 🆘 Need Help?

- **Render Docs:** https://render.com/docs
- **Render Support:** https://render.com/support
- **Check Logs:** Render Dashboard → Your Service → Logs

---

**🎉 Congratulations!** Your AI News Aggregator is now deployed on Render!
