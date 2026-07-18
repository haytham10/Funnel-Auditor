# Deliverability log — per inbox (Inbox 1 = auto-mate.one, Inbox 2 = gethaytham.com)

The evidence file behind every send-cap ramp decision. Each inbox ramps on
its OWN reputation, so every entry names the inbox it concerns. `python
main.py send-cap set 25|30 --inbox "<label>"` is Haytham's call, and this
log is what "THAT inbox's deliverability actually held" means: 7+ days at
its current step with no unexplained bounces, no spam-folder reports, test
scores steady, reply rate not cratering.

**Who writes here:** uae-tick appends a line whenever it detects a bounce
(mailer-daemon), a spam mention in a reply, or an inbox over its ceiling —
in the same run, via `python main.py send-cap log --inbox "<label>" --kind
<kind> --detail "..."` (which enforces the canonical shape). Haytham
appends test scores the same way. Newest entries at the top.

Entry format, one canonical line each (written by `send-cap log`):

```
- YYYY-MM-DD — [Inbox N] — [bounce|spam-flag|test-score|over-ceiling|note] — detail
```

Entries before 2026-07-16 predate the two-inbox split and are Inbox 1
(auto-mate.one) by definition.

---

## Log

- 2026-07-18 — [Inbox 2] — [spam-flag] — Charlotte Verhaert (charlotte@c-coaching.consulting) auto-reply to Touch 1 (07-18, 'your interview with natalia') landed in Haytham's spam folder, not inbox - caught by Haytham manually, missed by the in:inbox reply sweep. Content is a genuine OOO (annual leave until 2026-08-17), not a spam-worthy reply itself, but the misclassification is a real signal worth watching.
- 2026-07-18 — [Inbox 2] — [bounce] — Benjamin Owen (ben@coachbenjaminowen.com) hard-bounced 2026-07-18, Touch 1: 'Address not found' - mailbox does not exist. Address was a pattern-guessed catch-all-domain address, accepted risk by Haytham on 2026-07-17 revival. Row reverted to Qualifying.
- 2026-07-17 — [Inbox 2] — [bounce] — info@williambrown.com (UAE lead William Brown, Touch 1) hard-bounced (mailer-daemon 550 "No mailbox by that name is currently available") despite Email Verified=YES (WARN/inconclusive role-account at verify time). Row reverted to Qualifying; Touch #/Findings Bank not spent.
- 2026-07-17 — [Inbox 1] — [bounce] — neha@bizexconsultancy.com (UAE lead Neha Nimje, Touch 1) hard-bounced (mailer-daemon 550 5.1.1 "No Such User Here") despite Email Verified=YES (WARN/inconclusive catch_all at verify time). Row reverted to Qualifying; Touch #/Findings Bank not spent. Third hard bounce in a week on an address that cleared the gate (Chiara 07-16, Adil 07-16, now Neha 07-17) — worth weighing against the 07-21 Inbox 1 ramp check.
- 2026-07-16 — bounce — chiara@theholisticboutique.com (UAE lead Chiara
  Ghinolfi, Touch 1) hard-bounced (mailer-daemon 550 5.1.1 "Address not
  found") despite email-check PASS at send time. Row reverted to
  Qualifying pending a re-verified or alternate address; Touch #/Findings
  Bank not spent since the message never reached a live inbox. Second
  hard bounce this week on an address that passed email-check — worth
  weighing against the 07-21 ramp check.
- 2026-07-16 — bounce — adil@themancaveproject.com (UAE lead Adil Hussain,
  Touch 1) hard-bounced (mailer-daemon 550 5.1.1 "Address not found")
  despite email-check PASS at send time. Row reverted to Qualifying
  pending a re-verified or alternate address; Touch #/Findings Bank not
  spent.
- 2026-07-16 — note — contact@dubaifrenchtuitions.com (UAE lead Murielle
  Larrière, Touch 1, sent 07-15) is showing a Gmail "Delivery incomplete
  — temporary problem, will retry 47 more hours" notice as of 07-16
  06:00 UTC. Not a hard bounce yet; flagging in case it resolves to one
  before the next tick.
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
