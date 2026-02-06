# Sending to Multiple Subscribers (Resend)

When sending the newsletter to multiple subscribers, two issues can occur. Here's how to fix them.

---

## 1. "You can only send testing emails to your own email address"

**Cause:** Resend's `onboarding@resend.dev` domain only allows sending to your verified email (MY_EMAIL). Other recipients are rejected.

**Fix:** Verify your own domain at [resend.com/domains](https://resend.com/domains), then use an address on that domain as the sender.

### Steps

1. Go to [resend.com/domains](https://resend.com/domains)
2. Add your domain (e.g. `yourdomain.com`)
3. Add the DNS records Resend provides (SPF, DKIM)
4. Wait for verification
5. Set in `.env` and Render:
   ```
   FROM_EMAIL=newsletter@yourdomain.com
   ```

Once verified, you can send to any subscriber.

---

## 2. "Too many requests. You can only make 2 requests per second"

**Cause:** Resend rate limits to 2 requests/second. Sending to multiple subscribers quickly triggers this.

**Fix:** The pipeline now adds a 0.6 second delay between each email, keeping you under the limit. No action needed.

If you hit limits with many subscribers, consider:
- Increasing the delay in `app/services/process_email.py` (e.g. `time.sleep(1.0)`)
- Using Resend's batch API (if available on your plan)

---

## Summary

| Issue | Solution |
|-------|----------|
| Can't send to other emails | Verify a domain and set `FROM_EMAIL=newsletter@yourdomain.com` |
| Rate limit (2 req/s) | Delay already added; increase if needed |
