# Chetna Chakravarthy

<!-- airtable-record: TBD -->
> **Site:** https://chetnachakravarthy.com · **Profile:** https://www.instagram.com/positivityangel/
> **Walked:** 2026-07-16 · **Slug:** `chetna-chakravarthy`

---

## Overview

Chetna Chakravarthy, solo Life/Mindset (relationship) coach, Dubai-based (confirmed via her own Instagram bio/reels — "I am Chetna, a Relationship & Life Coach based in Dubai" — and a third-party press feature at siyahi.in describing her as "Dubai-based"). WordPress site (chetnachakravarthy.com). Main offers: three 1:1 coaching programs (Positive Action, Realign Chakras, Positive Circle — 6-12 sessions each) plus a small e-course library. 27,300 Instagram followers (@positivityangel), active podcast (Say NO To Drama) and YouTube channel (A Different Angle with Chetna).

## Funnel Walk

- Stop 1 (Bio — chetnachakravarthy.com) — Clean bio page, links to Programs and E-Courses, embedded IG/YouTube/Spotify widgets, no owned email capture anywhere.
- Stop 3 (Offer — /programs/) — Three 1:1 programs described in full sales copy — no price shown for any of them. "1:1 coaching has limited availability. Join the waitlist" — the waitlist button links straight to her Instagram profile, not a capture form.
- Stop 3 (Offer — /programs/, CTA check) — every SIGN UP and CONSULT CALL button on all three programs (`<a href="https://chetnachakravarthy.com/programs/">`) points back at the same /programs/ page — confirmed in raw HTML and visually on both desktop and mobile screenshots. Clicking either just reloads the page.
- Stop 3 (Offer — /e-course/) — four e-course tiles in a carousel; three (Learn to Manifest, Money Mindset Video Course, Vision Board) have the same self-referencing SIGN UP pattern. Only "Life by Design" resolves to a real subpage.
- Stop 4 (Checkout — /courses/life-by-design/) — real, working LearnDash course page — visible price ($50.00/month for 12 months), a "Take this Course" button that posts to a real registration form, and a Stripe payment script loaded on the page. Also contains a plain-text Calendly link for paid 1:1 consults (calendly.com/positivityangel/60min), not linked from anywhere else on the site.
- Extra stop (Contact — /contact/, found via nav, not in the original crawl scope but fetched and vision-confirmed because of what it showed) — the page's contact form itself is broken — visitors see "Error: Contact form not found" instead of a form. Location line reads "Mumbai, India" (stale — her current, current-dated marketing is unanimous that she's Dubai-based). A real email address is listed alongside the broken form: chetna@circleofpositivity.com.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE-based (Dubai, confirmed via her own IG bio/reels + a third-party press bio, both current — outweighs one stale "Mumbai, India" line on an unmaintained contact page); funnel floor confirmed real and reachable (Life by Design is a genuine priced, Stripe-backed course, not vapor); audience 27,300 (floor 1,500); activity confirmed pre-flight (active podcast + YouTube).
- **Gate 1:** Pass — solo operator throughout; first person "I" copy on the Life by Design page ("Chetna, for a session... schedule using this link"), no team/agency signals anywhere in the crawl.
- **Lane:** Lane 1 (felt leak) — a confirmed, vision-verified broken conversion path on the flagship offer.

## Findings — reasoning

**Rank 1 — Contact page shows a raw plugin error instead of a form**
Depth: not specified in raw archive · Type: broken contact form
Innocent explanation: a deactivated/misconfigured form plugin, likely missed since IG DM and email still work as fallbacks.
Why it matters: her own Contact page ("Reach Out") shows visitors a raw plugin error ("Error: Contact form not found") instead of a working way to message her — the one page built for reaching her doesn't work.
Loom / fix path: show chetnachakravarthy.com/contact/ — the "Reach Out" page, live in browser, scrolled to the orange contact box showing the red error. Fix: reconnect or replace the contact form shortcode in the WordPress page editor (Contact Form 7 / WPForms-style fix, no code) — a 10-15 minute admin-panel job. Done state: a visitor types name, email, and message and sees a "message sent" confirmation instead of the red error box.
Ruled out in the vision pass: none — the packet's own machine checks didn't catch the self-referencing SIGN UP/CONSULT CALL links or the contact-form error at all; both are vision-only catches, not resurrected machine flags.
Evidence: none promoted yet

**Rank 2 — All three flagship 1:1 program buttons loop back to the same page** *(RESERVED — call bait, never emailed)*
Depth: not specified in raw archive · Type: dead CTA / self-referencing link
Innocent explanation: placeholder links never swapped for real checkout/Calendly URLs before publishing.
Why it matters: all three flagship 1:1 programs (Positive Action, Realign Chakras, Positive Circle) have SIGN UP and CONSULT CALL buttons that link back to the same /programs/ page — confirmed on desktop and mobile.
Evidence: none promoted yet

**Rank 3 — The one working CTA routes to Instagram, not an owned list** *(RESERVED — call bait, never emailed)*
Depth: not specified in raw archive · Type: missing owned-list capture
Innocent explanation: a deliberate stopgap while 1:1 spots are full, not built out as a real waitlist yet.
Why it matters: the one working CTA on the programs page, "Join the Waitlist," routes to her Instagram profile instead of an owned capture form — every high-intent 1:1 lead lands in IG DMs, not a list she owns.
Evidence: none promoted yet

**Rank 4 — No price shown for any 1:1 program** *(RESERVED — call bait, never emailed)*
Depth: not specified in raw archive · Type: no price shown
Innocent explanation: pricing likely handled manually via consult call, just never posted.
Why it matters: no price is shown anywhere for the three 1:1 programs — a ready buyer has nothing to anchor on before hitting a dead sign-up button.
Evidence: none promoted yet

**Rank 5 — Three of four e-course tiles carry the same dead-loop pattern** *(RESERVED — call bait, never emailed)*
Depth: not specified in raw archive · Type: dead CTA / self-referencing link
Innocent explanation: same placeholder-link pattern as the programs page, probably from the same site build/update.
Why it matters: three of four e-course tiles (Learn to Manifest, Money Mindset Video Course, Vision Board) carry the same self-referencing SIGN UP loop — only "Life by Design" resolves to a real $50/month checkout.
Evidence: none promoted yet

## SMYKM Hook

`her post from 4 hours ago on managers rippling either "clarity and safety" or "anxiety and panic" onto their teams, coining the phrase "the panic dumper"` — **WORK** — source: https://www.linkedin.com/posts/chetna-chakravarthy_workplacewellness-badbosses-relationshipcoach-activity-7483475581511221249-R-q5

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
