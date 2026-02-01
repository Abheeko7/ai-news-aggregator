# Render Blueprint Requirements - Quick Reference

Use this checklist before creating your Render blueprint instance.

---

## 📋 What You Need Before Starting

### 1. GitHub
- [ ] Repository pushed to GitHub
- [ ] **Branch: `deployment`** (Render will deploy from this branch)
- [ ] All deployment files committed (render.yaml, requirements.txt, app/api.py, run_api.py, RENDER_DEPLOYMENT_GUIDE.md)

### 2. Render Account
- [ ] Account created at https://render.com
- [ ] GitHub connected (Render Dashboard → Account Settings → Connect GitHub)

### 3. Credentials to Have Ready
| Credential | Where to Get It | Used For |
|------------|-----------------|----------|
| **GEMINI_API_KEY** | https://aistudio.google.com/apikey | AI summarization |
| **MY_EMAIL** | Your Gmail address | Receives newsletters |
| **APP_PASSWORD** | Google Account → Security → 2-Step Verification → App passwords | Sending emails |

---

## 🔧 What the Blueprint Creates (FREE ONLY - NO PAYMENT)

| Resource | Type | Plan | Cost |
|----------|------|------|------|
| ai-news-aggregator-db | PostgreSQL | free | $0 |
| ai-news-api | Web Service | free | $0 |

**Newsletter trigger:** GitHub Actions (free) — see GITHUB_ACTIONS_SETUP.md. No Render cron job = no charges.

---

## 📝 Environment Variables (Render will prompt you)

### Web Service (ai-news-api) ONLY
| Variable | Required | Action |
|----------|----------|--------|
| CRON_SECRET | No | Leave empty (or set + add to GitHub secrets for protection) |
| GEMINI_API_KEY | **Yes** | Paste your key |
| MY_EMAIL | **Yes** | Your email |
| APP_PASSWORD | **Yes** | Gmail app password |

**DATABASE_URL** is set automatically by Render — you don't enter it.

---

## 🚀 Blueprint Creation Steps

1. Render Dashboard → **New +** → **Blueprint**
2. Select repo: **ai-news-aggregator**
3. Select branch: **deployment**
4. Review configuration → Enter env vars when prompted
5. Click **Apply**
6. Wait ~5–10 minutes for first deploy

---

## ✅ After Deployment

- **Health check:** `https://your-service.onrender.com/health`
- **Manual trigger:** `curl -X POST https://your-service.onrender.com/trigger-newsletter`
- **Logs:** Render Dashboard → Your Service → Logs
