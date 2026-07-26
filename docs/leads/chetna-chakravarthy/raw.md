<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39f382c8-4585-817a-afb1-e41e7a5969c1
Fetched: 2026-07-25T13:39:57Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Chetna Chakravarthy, solo Life/Mindset (relationship) coach, Dubai-based (confirmed via her own Instagram bio/reels — "I am Chetna, a Relationship & Life Coach based in Dubai" — and a third-party press feature at [siyahi.in](http://siyahi.in) describing her as "Dubai-based"). WordPress site ([chetnachakravarthy.com](http://chetnachakravarthy.com)). Main offers: three 1:1 coaching programs (Positive Action, Realign Chakras, Positive Circle — 6-12 sessions each) plus a small e-course library. 27,300 Instagram followers (@positivityangel), active podcast (Say NO To Drama) and YouTube channel (A Different Angle with Chetna).
## Funnel Walk
Stop 1 (Bio — [chetnachakravarthy.com](http://chetnachakravarthy.com)): Clean bio page, links to Programs and E-Courses, embedded IG/YouTube/Spotify widgets, no owned email capture anywhere.
Stop 3 (Offer — /programs/): Three 1:1 programs described in full sales copy — no price shown for any of them. "1:1 coaching has limited availability. Join the waitlist" — the waitlist button links straight to her Instagram profile, not a capture form.
Stop 3 (Offer — /programs/, CTA check): Every SIGN UP and CONSULT CALL button on all three programs (`<a href="https://chetnachakravarthy.com/programs/">`) points back at the same /programs/ page — confirmed in raw HTML and visually on both desktop and mobile screenshots. Clicking either just reloads the page.
Stop 3 (Offer — /e-course/): Four e-course tiles in a carousel; three (Learn to Manifest, Money Mindset Video Course, Vision Board) have the same self-referencing SIGN UP pattern. Only "Life by Design" resolves to a real subpage.
Stop 4 (Checkout — /courses/life-by-design/): Real, working LearnDash course page — visible price (\$50.00/month for 12 months), a "Take this Course" button that posts to a real registration form, and a Stripe payment script loaded on the page. Also contains a plain-text Calendly link for paid 1:1 consults ([calendly.com/positivityangel/60min](http://calendly.com/positivityangel/60min)), not linked from anywhere else on the site.
Extra stop (Contact — /contact/, found via nav, not in the original crawl scope but fetched and vision-confirmed because of what it showed): The page's contact form itself is broken — visitors see "Error: Contact form not found" instead of a form. Location line reads "Mumbai, India" (stale — her current, current-dated marketing is unanimous that she's Dubai-based). A real email address is listed alongside the broken form: [chetna@circleofpositivity.com](mailto:chetna@circleofpositivity.com).
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none attached — crawl-only walk
- Machine flags rejected in the vision pass: 0 — none rejected (the packet's own checks didn't catch the self-referencing SIGN UP/CONSULT CALL links or the contact-form error at all; both are vision-only catches, not resurrected machine flags)
## Gates
Gate 0: Pass — UAE-based (Dubai, confirmed via her own IG bio/reels + a third-party press bio, both current — outweighs one stale "Mumbai, India" line on an unmaintained contact page); funnel floor confirmed real and reachable (Life by Design is a genuine priced, Stripe-backed course, not vapor); audience 27,300 (floor 1,500); activity confirmed pre-flight (active podcast + YouTube).
Gate 1: Pass — solo operator throughout; first person "I" copy on Life by Design page ("Chetna, for a session... schedule using this link"), no team/agency signals anywhere in the crawl.
## Lane + Finding
Lane 1: Felt leak — a confirmed, vision-verified broken conversion path on the flagship offer.
Strongest finding: her own Contact page shows visitors a raw plugin error ("Error: Contact form not found") instead of a working way to message her — and separately, every SIGN UP/CONSULT CALL button on her three paid 1:1 programs loops back to the same page instead of going anywhere.
Innocent explanation: a form plugin was likely deactivated or its shortcode broke during a site update, and the /programs/ buttons look like placeholder links that were never swapped for the real checkout/booking URLs before the page went live — nobody's fault, just never caught because Instagram DMs and the listed email still work as a fallback.
## Findings Bank
1. Her own Contact page ("Reach Out") shows a raw plugin error instead of a working contact form — the one page built for reaching her doesn't work — innocent: a deactivated/misconfigured form plugin, likely missed since IG DM and email still work as fallbacks.
2. All three flagship 1:1 programs (Positive Action, Realign Chakras, Positive Circle) have SIGN UP and CONSULT CALL buttons that link back to the same /programs/ page — confirmed on desktop and mobile — innocent: placeholder links never swapped for real checkout/Calendly URLs before publishing.
3. The one working CTA on that same page, "Join the Waitlist," routes to her Instagram profile instead of an owned capture form — every high-intent 1:1 lead lands in IG DMs, not a list she owns — innocent: a deliberate stopgap while 1:1 spots are full, not built out as a real waitlist yet.
4. No price shown anywhere for the three 1:1 programs — a ready buyer has nothing to anchor on before hitting a dead sign-up button — innocent: pricing likely handled manually via consult call, just never posted.
5. Three of four E-Course tiles (Learn to Manifest, Money Mindset Video Course, Vision Board) carry the same self-referencing SIGN UP loop — only "Life by Design" resolves to a real \$50/month checkout — innocent: same placeholder-link pattern as the programs page, probably from the same site build/update.
## Loom Skeleton
- Show: [chetnachakravarthy.com/contact/](http://chetnachakravarthy.com/contact/) — the "Reach Out" page, live in browser, scrolled to the orange contact box showing the red error.
- Fix: reconnect or replace the contact form shortcode in the WordPress page editor (Contact Form 7 / WPForms-style fix, no code) — a 10-15 minute admin-panel job.
- Done state: a visitor types name, email, and message and sees a "message sent" confirmation instead of the red error box.
## SMYKM Hook
SMYKM hook: her post from 4 hours ago on managers rippling either "clarity and safety" or "anxiety and panic" onto their teams, coining the phrase "the panic dumper" — WORK — source: [https://www.linkedin.com/posts/chetna-chakravarthy_workplacewellness-badbosses-relationshipcoach-activity-7483475581511221249-R-q5](https://www.linkedin.com/posts/chetna-chakravarthy_workplacewellness-badbosses-relationshipcoach-activity-7483475581511221249-R-q5)
## Email Thread Log
\[2026-07-17\] — Touch #1 — Subject: "the panic dumper" — Sent
Hey Chetna
The panic dumper piece you posted today is exactly the kind of
workplace pattern most coaches talk around instead of naming directly.
Clarity and safety versus anxiety and panic, from the manager down, is
a real distinction.
So I went to actually book a session off the back of that kind of insight.
Every one of your three main programs, Positive Action, Realign
Chakras, Positive Circle, sends you back to the same programs page
instead of a booking or checkout. Your contact page returns a flat
error instead of a form.
Someone convinced by a post like today's has no real way through, on
desktop or on the phone.
Is that a site update in progress, or has it been sitting like that a while?
Haytham
Reply: No reply
\[2026-07-18\] — DUPLICATE of Touch #1 — Subject: "the panic dumper" — Sent (Inbox 1, in error)
Same subject and body as the 2026-07-17 Touch 1 above, sent again today from Inbox 1 instead of her assigned Inbox 2 — looks like a leftover draft went out by mistake. She has now received this exact email twice, one day apart, from two different domains. Not logged as Touch 2 — no new content, Touch # stays 1.
Next: real Touch 2 still due 2026-07-20 from Inbox 2, must carry a NEW finding (bank #2, #3, #4, or #5 all UNUSED).
## Price Discovery
