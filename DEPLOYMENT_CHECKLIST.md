# Deployment Checklist

Use this to verify both branches and Render are set up correctly.

---

## Branch Overview

| Branch | Purpose | Contains |
|--------|---------|----------|
| **main** | GitHub Actions workflow, docs | `.github/workflows/newsletter.yml` |
| **deployment** | Render deployment | `app/api.py`, `run_api.py`, `render.yaml`, `requirements.txt`, all app code |

**Render deploys from `deployment`**. GitHub Actions runs from `main`.

---

## Subscribers Not Populating? Troubleshooting

### 1. Verify SUBSCRIBERS_CSV_URL on Render

- Render Dashboard → your service → **Environment**
- `SUBSCRIBERS_CSV_URL` must be set to your **published** CSV URL
- Format: `https://docs.google.com/spreadsheets/d/XXX/export?format=csv&gid=YYY`
- Get it: Sheet → File → Share → Publish to web → select **Subscribers** sheet → CSV → Copy link

### 2. Publish the Correct Sheet

- You must publish the **Subscribers** sheet (not Form responses 1)
- Subscribers has: `email`, `preferred_name`, `youtube`, `openai`, `anthropic`, `f1`
- Form responses has: `Timestamp`, `Email`, `Preferred Name`, `Topics` — import supports both formats

### 3. Check Render Logs

- After a pipeline run, check Render Logs
- Look for: `[0.5/6] 📥 Importing subscribers...`
- Look for: `CSV columns: [...]` — confirms fetch worked
- Look for: `Imported: X` or `Updated: X`

### 4. Test CSV URL

- Open `SUBSCRIBERS_CSV_URL` in a browser
- You should see CSV with headers and data rows
- If you see HTML or an error, the URL is wrong

### 5. Manual Import (Debug)

- Call `GET /import-subscribers` on your Render service
- If `CRON_SECRET` is set, add header: `X-Cron-Secret: <your-secret>`
- Response shows: `imported`, `updated`, `skipped`, `errors`
- If `imported`/`updated` are 0 and `skipped` equals row count, column names may not match

---

## Cold Start (Render Asleep)

The workflow includes a **wake-up step**:
1. GET `/health` to trigger cold start
2. Wait 90 seconds for service to wake
3. POST `/trigger-newsletter`
4. Retry up to 3 times with 45s between attempts

If the scheduled run time varies, the 90s wait should handle most cold starts.

---

## Branch Sync (Clean Deployment)

**Goal:** `main` has workflow + docs; `deployment` has API + app code. Both in sync.

```bash
# 1. Commit your changes on main
git add .github/workflows/newsletter.yml app/services/import_subscribers.py app/api.py DEPLOYMENT_CHECKLIST.md
git commit -m "feat: wake-up for cold start, import improvements, /import-subscribers debug endpoint"

# 2. Push main (fix divergence if needed)
git push origin main
# If divergent: git pull --rebase origin main && git push origin main
# Or: git push --force-with-lease origin main  # only if you're sure

# 3. Merge main into deployment and push
git checkout deployment
git merge main -m "Merge main: workflow, import, checklist"
git push origin deployment

# 4. Switch back to main
git checkout main
```

Render redeploys when `deployment` is pushed. GitHub Actions runs from `main`.

---

## Quick Sync Check

```bash
git log origin/deployment --oneline -1
git log origin/main --oneline -1
```

Both should have recent commits. Deployment should include the API and import code.
