# GitHub Actions Setup (Free Newsletter Trigger)

This guide sets up **free** automated daily newsletters using GitHub Actions + Render. **No payment or card required.**

---

## Overview

| Component | Cost |
|-----------|------|
| Render database | **FREE** |
| Render web service | **FREE** |
| GitHub Actions | **FREE** |
| **Total** | **$0** |

**About payment:** Render may ask for a card for account verification. With this setup (database + web service only, no cron job), you use **only free tier** services. Render does not charge for free tier. To be safe: do not add any paid services, and you can remove your card from Render billing settings after verification if you prefer.

---

## Part 1: Render Setup (What to Fill In)

### Step 1: Create Blueprint on Render

1. Go to https://render.com
2. Click **New +** → **Blueprint**
3. Connect GitHub → Select repo **ai-news-aggregator**
4. Select branch: **deployment**
5. Render will detect `render.yaml`

### Step 2: What Render Will Create (ALL FREE)

- **Create database ai-news-aggregator-db** (free)
- **Create web service ai-news-api** (free)
- **NO cron job** (removed to avoid payment)

### Step 3: Environment Variables to Fill (Render will prompt you)

You'll see a "Specified configurations" screen. Fill in **only** for the **web service (ai-news-api)**:

| Variable | Required | What to Enter | Example |
|----------|----------|---------------|---------|
| **CRON_SECRET** | No | Leave **empty** or generate a secret (see below) | *(leave blank)* |
| **GEMINI_API_KEY** | **Yes** | Your Google Gemini API key | `AIza...` |
| **MY_EMAIL** | **Yes** | Email that receives newsletters | `you@gmail.com` |
| **APP_PASSWORD** | **Yes** | Gmail app password | `abcd efgh ijkl mnop` |

**DATABASE_URL** is set automatically — do not enter it.

### Step 4: Skip or Ignore Cron Job Section

If you see a cron job section asking for env vars — **it should not appear** since we removed it from the blueprint. If you see it from a previous blueprint, you can delete the cron job from the Render dashboard after creation.

### Step 5: Apply and Deploy

1. Click **Apply** or **Create Blueprint**
2. Wait 5–10 minutes for the first deploy
3. Note your web service URL: `https://ai-news-api-xxxx.onrender.com` (or similar)

---

## Part 2: GitHub Actions Setup

### Step 1: Add GitHub Secrets

1. Go to your repo: `https://github.com/Abheeko7/ai-news-aggregator`
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Required |
|-------------|-------|----------|
| **RENDER_SERVICE_URL** | Your Render web service URL (no trailing slash) | **Yes** |
| **CRON_SECRET** | Same value as Render's CRON_SECRET, or leave empty | No |

**RENDER_SERVICE_URL example:** `https://ai-news-api-xxxx.onrender.com`

- Get it from: Render Dashboard → ai-news-api → copy the URL at the top
- Do NOT include `/trigger-newsletter` — just the base URL
- Do NOT add a trailing slash

**CRON_SECRET (optional):** If you left it empty in Render, leave this empty or don't create it. If you set it in Render, create the same secret here.

### Step 2: Push Workflow to Repository

The workflow file `.github/workflows/newsletter.yml` must be in your repo. If you've committed it to the `deployment` branch, you're good.

**Important:** For scheduled runs (`cron`), GitHub Actions uses the workflow from your **default branch** (usually `main`). If your default is `main`, merge the `deployment` branch into `main` so the workflow file is there, or change your default branch to `deployment`. Manual "Run workflow" works from any branch that has the file.

### Step 3: Verify Workflow

1. Go to your repo → **Actions** tab
2. You should see "Daily Newsletter Trigger" workflow
3. Click **Run workflow** (manual trigger) to test
4. Check the run logs — it should POST to your Render URL and show success

---

## Part 3: Testing

### Test Render Directly

```bash
curl -X POST https://YOUR-SERVICE.onrender.com/trigger-newsletter
```

Replace `YOUR-SERVICE` with your actual Render service name.

### Test GitHub Actions

1. **Actions** tab → **Daily Newsletter Trigger** → **Run workflow**
2. Click the run to see logs
3. You should see: `✅ Newsletter pipeline triggered successfully!`
4. Check your email for the newsletter

---

## Schedule

The workflow runs:
- **Automatically:** Every day at 8:00 AM UTC
- **Manually:** Actions tab → Run workflow

---

## Troubleshooting

### "RENDER_SERVICE_URL is empty"
- Add the secret in GitHub: Settings → Secrets → Actions
- Use the full URL: `https://ai-news-api-xxxx.onrender.com`
- No trailing slash

### "401 Unauthorized"
- If you set CRON_SECRET in Render, you must set the **same** value in GitHub secrets
- If you want no protection, leave CRON_SECRET empty in both places

### "Connection refused" or timeout
- Render free tier spins down after ~15 min of inactivity
- First request may take 30–60 seconds to "wake up" the service
- The workflow may need to wait longer on first run — check Render logs

### Workflow not appearing
- Ensure `.github/workflows/newsletter.yml` is committed and pushed
- Check you're on the correct branch
- GitHub may need a few minutes to detect new workflows

---

## Summary Checklist

**Render:**
- [ ] Blueprint created with `deployment` branch
- [ ] Only database + web service (no cron job)
- [ ] GEMINI_API_KEY, MY_EMAIL, APP_PASSWORD filled in
- [ ] CRON_SECRET left empty (or set if you want protection)
- [ ] Service URL copied for GitHub

**GitHub:**
- [ ] RENDER_SERVICE_URL secret added
- [ ] CRON_SECRET secret added (only if you set it in Render)
- [ ] Workflow file committed to repo
- [ ] Manual test run successful
