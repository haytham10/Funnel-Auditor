<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-811e-a51d-fa28af068987
Fetched: 2026-07-25T13:41:16Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Shankar V Jayaraman — leadership / performance coach for 35-55 year old professionals, based in Dubai, UAE. Solo operator (TEDx speaker coach, ex-HCL, Amazon bestselling author of "Profit Through People", founder of "Legacy Mentors Hub"). Site [coachshankar.com](http://coachshankar.com) is a custom Lovable-built React site; courses/memberships run on a TagMango white-label platform ([learn.legacymentorshub.com](http://learn.legacymentorshub.com)). Main offer: flagship 12-week 1:1 "Success Alignment Framework" plus free Clarity/Discovery calls and a paid ₹4,999 Strategy Session, all booked through a single call-booking link. Freebie: "Profit Through People" ebook. Audience active on LinkedIn + Instagram (@shankarslens); hard follower count not retrievable.
## Funnel Walk
- Stop 1 (Bio/Home) — hero + 4 near-equal nav destinations, "Book Free Clarity Call" primary CTA — ambiguous first click, but a clear call-booking intent.
- Stop 2 (Freebie) — /learn + home opt-in for "Profit Through People" ebook and "Leading Inside Out" newsletter — email captured before delivery, working.
- Stop 3 (Offer/Sales) — /work-with-me: flagship Success Alignment Framework (no price shown), Clarity Call (free), Discovery Call (free), Strategy Session (₹4,999). Every offer's CTA is "Book a Call"/"Book Now".
- Stop 4 (Checkout/Booking) — EVERY booking CTA site-wide points to [https://booking.legacymentoshub.com/shankarjayaraman/meeting](https://booking.legacymentoshub.com/shankarjayaraman/meeting), which FAILS DNS resolution (domain does not resolve; confirmed twice via Firecrawl). No alternate booking widget, phone, or contact form. The call-booking path is dead on every page.
- Stop 5 (Audience ownership) — owns email capture (ebook + newsletter) and a TagMango members platform — not fully dependent on rented reach.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none — crawl-only walk (no images attached to the Notion page, no chat screenshots).
- Machine flags rejected in the vision pass: none rejected — the "coming soon / placeholder" availability flags on /learn were all visually confirmed as real live placeholder content, not misfires.
## Gates
Gate 0: Pass — UAE base confirmed (Dubai on site footer, LinkedIn location Dubai/دبي, TEDxJumeirahBeachPark). Funnel present (sales page + paid Strategy Session + TagMango course/membership platform). Activity floor met (Instagram @shankarslens posts through 17 Jun 2026 and a 27-28 Jun 2026 event, within 30 days; regular cadence Feb-Jun 2026). Audience floor (1,500+): not confirmed by a hard count — LinkedIn (TEDx speaker coach, ex-HCL) is the largest owned channel and the basis; Instagram engagement looked thin (a Jun reel showed 6 likes). Resting Pass on the LinkedIn/TEDx professional signal — flagged for manual confirmation.
Gate 1: Pass — solo operator; his name is the brand, he coaches 1:1, no team gatekeeper visible.
## Lane + Finding
- Lane 1: Felt leak — a live, costing-money breakage in the primary conversion path.
- Strongest finding (bank #1): Every "Book a Call" / "Book Now" / "Book Free Clarity Call" button across the whole site (home, work-with-me, about, header + footer of every page) points to [booking.legacymentoshub.com](http://booking.legacymentoshub.com), and that domain fails DNS — it doesn't exist. So the only route to becoming a client (free calls, the paid Strategy Session, and the entry point to the flagship program) dead-ends in a browser error on every page. The buttons look perfectly normal; only the destination is broken.
- Innocent explanation: the brand name is spelled two different ways — the working LMS lives on legacymento**r**[shub.com](http://shub.com) (with the "r"), but his own About-page timeline reads "Launched Legacy **Mentos** Hub" (no "r"), and the booking subdomain was pointed at the missing-"r" spelling ([legacymentoshub.com](http://legacymentoshub.com)), which was never registered. A one-letter typo in a subdomain he never clicks himself.
## Findings Bank
1. Every call-booking CTA site-wide dead-ends at [booking.legacymentoshub.com](http://booking.legacymentoshub.com) (DNS failure) — free calls, the ₹4,999 Strategy Session, and the flagship program entry all lose the visitor at the click — innocent: brand spelled "Mentos" (no r) on his own timeline vs the working "Mentors" (with r) domain; booking subdomain typed with the wrong spelling.
2. The /learn content hub ships live placeholder scaffolding to visitors — four blog cards all read "Upload cover / Coming soon — title placeholder" and the Podcast block is "Coming Soon" — innocent: content section published before it was filled; the CMS default placeholders were never swapped out.
3. The /work-with-me sales page shows a live empty "Upload Webinar Poster" dashed placeholder box directly under the webinar registration form — innocent: an admin upload slot left exposed on the public page when the webinar section shipped without a poster.
4. The footer "LinkedIn" link on every page points to bare [linkedin.com](http://linkedin.com) (LinkedIn home), not his profile — a dead-end social link site-wide — innocent: placeholder href never replaced with his real profile URL when the footer was built.
## SMYKM Hook
SMYKM hook: Your post this week on getting coached by Dr. John Demartini and Jack Canfield's team — the line "some rooms give you information, some rooms quietly expand your identity" — LIFE — source: [https://www.linkedin.com/posts/shankarslens_balance-globalmentorship-leadershipcoaching-activity-7482353870640386048-YhQY](https://www.linkedin.com/posts/shankarslens_balance-globalmentorship-leadershipcoaching-activity-7482353870640386048-YhQY)
## Email Thread Log
2026-07-16 — Touch #1 — Subject: "the room with demartini and canfield" — Sent
Hey Shankar
Getting in the room with Demartini and Jack Canfield's people, and coming out focused on how they carried themselves more than what they said, tells me something about how you take this work. You went to raise your own standard, not to collect another name.
Which is why I'd want to know about this one. Every Book a Call button on your site points to [booking.legacymentoshub.com](http://booking.legacymentoshub.com), and that address doesn't resolve, it just loads a browser error. The free clarity call or the paid strategy session, same dead link behind both.
So someone who reads all this and decides you're the coach for them clicks to book, and lands on an error page instead of your calendar.
I think it's a one letter thing. Your own timeline spells it Mentos, the working platform is Mentors with the r, and the booking link points at the spelling that was never registered.
Worth a look before the next person tries to book?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question — this lead has no unused bank finding left after Touch 2, so Touch 3 must use the Loom offer or a disambiguating question)
2026-07-19 — Touch #2 — Subject: "the room with demartini and canfield" — Sent
Hey Shankar
One more thing I noticed while I was in there.
Your learn page, the essays and the podcast, is still sitting in placeholder mode. The blog cards read "coming soon, title placeholder" and the podcast section just says coming soon.
So someone who likes what you say and clicks through to go deeper lands on a page that looks half built, and quietly decides you're not really active here.
Is that section still being put together, or did it just never get switched on?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question — this lead has no unused bank finding left after Touch 2, so Touch 3 must use the Loom offer or a disambiguating question)
## Price Discovery
