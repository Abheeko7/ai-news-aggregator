# Resend Email API - Next Steps

Render's free tier blocks outbound SMTP, causing `[Errno 101] Network is unreachable` when sending email. Use **Resend** (HTTP-based) instead.

---

## What Will Change

| Current | After Resend |
|---------|--------------|
| Gmail SMTP (smtplib) | Resend HTTP API |
| MY_EMAIL + APP_PASSWORD | RESEND_API_KEY + FROM_EMAIL |
| Blocked on Render free tier | Works on Render free tier |

---

## Implementation Steps

1. **Sign up for Resend** (free tier: 3,000 emails/month)
   - https://resend.com/signup
   - Verify your domain (or use Resend's test domain for development)

2. **Get API key**
   - Resend Dashboard → API Keys → Create API Key
   - Copy the key (starts with `re_`)

3. **Code changes**
   - Add `resend` to requirements.txt
   - Update `app/services/email_service.py` to use Resend API instead of SMTP
   - Support both: `EMAIL_PROVIDER=resend` (new) or `smtp` (for local dev)
   - New env vars: `RESEND_API_KEY`, `FROM_EMAIL` (e.g. `newsletter@yourdomain.com` or Resend's onboarding domain)

4. **Render env vars**
   - Remove or keep `APP_PASSWORD` (unused with Resend)
   - Add `RESEND_API_KEY`
   - Add `FROM_EMAIL` (verified sender in Resend)
   - Keep `MY_EMAIL` (recipient)

5. **Update example.env and docs**
   - Document new variables
   - Update GITHUB_ACTIONS_SETUP, RENDER_DEPLOYMENT_GUIDE

---

## Resend Free Tier

- 3,000 emails/month
- 100 emails/day
- Can use Resend's onboarding domain (e.g. `onboarding@resend.dev`) for testing before adding your own domain

---

## Ready to Implement?

Switch to Agent mode and say: "Implement Resend for email sending" to have the code changes made automatically.
