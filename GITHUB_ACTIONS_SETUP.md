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
| **RESEND_API_KEY** | **Yes** | Resend API key (https://resend.com/api-keys) | `re_xxx...` |
| **FROM_EMAIL** | No | Sender email (default: `onboarding@resend.dev`) | `onboarding@resend.dev` |
| **APP_PASSWORD** | No | Gmail app password (only for local SMTP; not used on Render) | *(leave blank)* |

**DATABASE_URL** is set automatically — do not enter it.

**Note:** Resend is used on Render (SMTP is blocked on free tier). For local dev you can use either Resend or Gmail (APP_PASSWORD).

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

### Step 2: Create Workflow File on GitHub

The workflow file must be in your repo. Due to GitHub OAuth limits, you may need to **create it manually**:

1. Go to your repo → **Create new file**
2. Path: `.github/workflows/newsletter.yml`
3. Paste the content from the "Workflow File Content" section at the bottom of this guide
4. Commit to `main` (or your default branch) so scheduled runs work

**Alternative:** If you have `workflow` scope for GitHub, you can push the file from your local `.github/workflows/newsletter.yml`.

**Important:** For scheduled runs (`cron`), GitHub Actions uses the workflow from your **default branch** (usually `main`). Create the file on `main` for scheduled runs to work. Manual "Run workflow" works from any branch.

### Step 3: Verify Workflow

1. Go to your repo → **Actions** tab
2. You should see "Daily Newsletter Trigger" workflow
3. Click **Run workflow** (manual trigger) to test
4. Check the run logs — it should POST to your Render URL and show success

---

## Workflow File Content (Copy for Manual Creation)

If you create `.github/workflows/newsletter.yml` manually on GitHub, use this content:

```yaml
name: Daily Newsletter Trigger

# Triggers the newsletter pipeline daily via Render /trigger-newsletter.
# Uses GitHub Actions (free) instead of Render cron (paid).
# Pipeline: scrape → process → digest → send to MY_EMAIL.

on:
  schedule:
    - cron: '0 8 * * *'   # Daily at 8:00 AM UTC
  workflow_dispatch:       # Manual trigger from GitHub Actions tab

jobs:
  trigger-newsletter:
    runs-on: ubuntu-latest
    name: Trigger Newsletter Pipeline
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Trigger Newsletter Endpoint
        env:
          RENDER_URL: ${{ secrets.RENDER_SERVICE_URL }}
          CRON_SECRET: ${{ secrets.CRON_SECRET }}
        run: |
          echo "🚀 Triggering newsletter pipeline..."
          echo "Service URL: $RENDER_URL"
          
          CURL_CMD="curl -s -w '\n%{http_code}' -X POST '$RENDER_URL/trigger-newsletter' -H 'Content-Type: application/json'"
          if [ -n "$CRON_SECRET" ]; then
            CURL_CMD="$CURL_CMD -H 'X-Cron-Secret: $CRON_SECRET'"
          fi
          
          response=$(eval "$CURL_CMD" || echo "000")
          http_code=$(echo "$response" | tail -n1)
          body=$(echo "$response" | head -n-1)
          
          echo "Response Code: $http_code"
          echo "Response Body: $body"
          
          if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
            echo "✅ Newsletter pipeline triggered successfully!"
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
          else
            echo "❌ Failed to trigger newsletter. HTTP Code: $http_code"
            echo "$body"
            exit 1
          fi
      
      - name: Display Summary
        if: success()
        run: |
          echo "📧 Pipeline completed. Newsletter sent to MY_EMAIL."
          echo "Check Render service logs for details."
```

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
- [ ] GEMINI_API_KEY, MY_EMAIL, RESEND_API_KEY filled in
- [ ] CRON_SECRET left empty (or set if you want protection)
- [ ] Service URL copied for GitHub

**GitHub:**
- [ ] RENDER_SERVICE_URL secret added
- [ ] CRON_SECRET secret added (only if you set it in Render)
- [ ] Workflow file committed to repo
- [ ] Manual test run successful
