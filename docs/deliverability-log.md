# Deliverability log — one inbox (haytham@auto-mate.one)

The evidence file behind every send-cap ramp decision. `python main.py
send-cap set 25|30` is Haytham's call, and this log is what "deliverability
actually held" means: 7+ days at the current step with no unexplained
bounces, no spam-folder reports, test scores steady, reply rate not
cratering.

**Who writes here:** uae-tick appends a dated line whenever it detects a
bounce (mailer-daemon), a spam mention in a reply, or a day over the
ceiling — in the same run it detects them. Haytham appends test scores
(MailGenius, mail-tester, etc.) whenever he runs them. Newest entries at
the top.

Entry format, one line each:

```
YYYY-MM-DD — [bounce|spam-flag|test-score|over-ceiling|note] — detail
```

---

## Log

- 2026-07-14 — bounce — shelley@shelleybosworthofficial.com (UAE lead
  Shelley Bosworth, Touch 1) hard-bounced (address not found). Cause was a
  wrong-address guess, not domain reputation: a corrected resend to
  shelley@shelleybosworthcoaching.com delivered the same minute and is the
  address logged in the CRM. This is the double-send the email-check gate
  now prevents. Not a reputation signal for the 07-21 ramp check.
- 2026-07-14 — test-score — MailGenius + mail-tester + cyberpersons +
  mailchecker seed sends went out (6 test messages in the sent log,
  15:32-16:00 UTC). Scores not yet recorded — Haytham to fill in.
- 2026-07-14 — note — Ramp step 1 (20/day) started. Baseline for the
  2026-07-21 ramp-eligibility check.
- 2026-07-13 — note — Historical context: 23 sends on 07-13 and 21 real +
  6 test on 07-14 (over the new 20 ceiling; predates the ceiling being
  enforced). 19 parenting bumps went out in a two-minute burst on 07-13 —
  the pattern the pacing rule (max 10 per sitting, spread through the day)
  and the parenting 5/day leash now prohibit.
