# Samira Alexander

<!-- airtable-record: TBD -->
> **Site:** https://rapidmindredesign.com/ · **Profile:** https://www.instagram.com/thrivewithsamira/
> **Walked:** 2026-07-17 · **Slug:** `samira-alexander`

---

## Overview

Samira Alexander, Dubai-based RTT hypnotherapist / mindset & anxiety coach (@thrivewithsamira, 14,600 IG followers). Her REAL flagship funnel is Rapid Mind Redesign (rapidmindredesign.com — WordPress/Elementor), an award-winning RTT & Kinesiology practice ("MEA UAE Business Awards — Best Hypnotherapist & Coach 2021, Middle East"). Sees clients face-to-face at the Just Be Holistic Centre, Jumeirah (Dubai) and Changeworks (Abu Dhabi), plus online. Bespoke 30/60/90-day transformation packages (RTT + coaching), pricing discussed on a discovery call → Track B. thrivewithsamiradigital.store (Beacons link-in-bio storefront) is a SECONDARY, peripheral property reselling smaller digital products; it is NOT her real coaching funnel — see the retired finding at the bottom of this doc.

## Funnel Walk

- Stop 1 (Home — rapidmindredesign.com) — hero "I help with overcoming anxiety, abuse incl. narcissistic abuse & addictions." Primary CTA "BOOK MY FREE CONSULTATION NOW" + persistent header "BOOK NOW". Both point to calendly.com/rapid-mind-redesign/assessment.
- Stop 2 (About — /about-samira-alexander) — solo personal brand, RTT-certified (Marisa Peer pioneer group), UAE locations, MEA UAE award. Bottom CTA "Book Your 30 min Consultation Call" → same Calendly link.
- Stop 3 (Work With Me — /the-methods) — the offer page. Signature "Quantum Freedom" program, RTT + Kinesiology + KinesioCoaching. "Pranic Healing Practitioner" is listed as a method in the nav and here, but its content is only "Coming Soon" — a placeholder shipped live in the offer menu.
- Stop 4 (RTT method — /the-methods/rapid-transformational-therapy) — full method + FAQ; packages "discussed during the discovery call." Sole CTA "Book a FREE 30 mins Assessment Call NOW" → same Calendly link.
- Stop 5 (Booking — calendly.com/rapid-mind-redesign/assessment) — THE conversion action. Returns "This Calendly URL is not valid." Desktop AND mobile, on repeat fetches. The Calendly account root (/rapid-mind-redesign) resolves 200, so the account lives but the /assessment event type is gone — every "Book" button on the site dead-ends here.
- Stop 6 (Contact — /contact) — working fallback form (name/phone/email/message + math captcha) + info@rapidmindredesign.com, Dubai & Abu Dhabi addresses. On desktop the page renders with a large empty white gap above the form (half-width hero, then blank) — the backup path looks half-loaded.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none attached — crawl-only re-walk (Firecrawl-primary; some full-HTML stops curl-sandboxed, refetched via Firecrawl)
- **Screenshots:** none promoted yet — see per-finding notes below
- **Machine flags rejected in the vision pass:** none rejected — the dead-booking finding was confirmed by eye on the Calendly screenshot ("This Calendly URL is not valid"), desktop + mobile.

## Gates

- **Gate 0:** Pass — UAE-based (Dubai/Jumeirah "Just Be Holistic Centre" + Abu Dhabi "Changeworks", confirmed on About + Contact addresses); funnel confirmed (live RTT practice, bespoke paid packages, discovery-call offer); 30-day activity (site content modified Jul 2025; IG @thrivewithsamira active Jul 2026); audience 14,600 IG clears the 1,500 floor. (Floors carried from prior qualification; re-walk confirms funnel floor on the real brand.)
- **Gate 1:** Pass — solo personal brand throughout (own face, own story, first-person). No agency/team/gatekeeper. info@ inbox exists but is a solo contact form, not a ticketed desk.
- **Lane:** Lane 1 (felt leak) — the single conversion action on the entire funnel is broken.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — every "Book" CTA site-wide dead-ends on an invalid Calendly link**
Depth: DEEP · Type: Dead booking link on every conversion CTA
Innocent explanation: the Calendly event type was almost certainly renamed, unpublished, or moved when she reorganised her scheduling, and the site's booking buttons still point at the old event slug — a stale link after a scheduling change, not a closed practice (the account root still resolves).
Why it matters: every "Book" CTA on rapidmindredesign.com (header Book Now, hero "Book My Free Consultation Now", About's "Book Your 30 min Consultation Call", RTT's "Book a FREE 30 mins Assessment Call NOW") lands on calendly.com/rapid-mind-redesign/assessment, which shows "This Calendly URL is not valid." Every warm, ready-to-book visitor hits a dead end at the exact moment of intent. Loom framing: click any "Book Now" button to show the Calendly error; the fix is repointing the site's booking buttons to her current live Calendly event (or republishing the /assessment event under the old slug); done state is a visitor clicking "Book" and reaching a working assessment-call calendar with open times.
Evidence: not yet promoted — see [`samira-alexander.raw.md`](./samira-alexander.raw.md) for citation.

**Rank 2 — "Pranic Healing Practitioner" listed live but page only says "Coming Soon"** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: Placeholder offer shipped live in the nav
Innocent explanation: added to the menu when planned, the page just never got filled in.
Why it matters: it's listed as a live method in the Work With Me menu and Methods page, but the page itself is a placeholder — a visitor who clicks through expecting a real offer finds nothing to buy.
Evidence: not yet promoted — see [`samira-alexander.raw.md`](./samira-alexander.raw.md) for citation.

**Rank 3 — Contact page has a large empty white gap above the form on desktop** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: Half-loaded fallback page
Innocent explanation: an Elementor banner/section that didn't populate, easy to miss from the editor view.
Why it matters: it's the fallback path for a visitor who couldn't book, and it looks half-loaded/broken at the exact moment someone is trying a second route in.
Evidence: not yet promoted — see [`samira-alexander.raw.md`](./samira-alexander.raw.md) for citation.

**Retired finding — not part of the current bank, kept for record only**
The secondary Beacons storefront (thrivewithsamiradigital.store) previously carried a finding — "Baxsan Wealth Empire" listed twice on the storefront homepage, once at $297 (affiliate, credited to @baxsan) and once at £230 (her own listing), identical name/image/description. This was on a peripheral affiliate storefront off her RTT/anxiety brand and was demoted/retired in favour of the on-brand dead-booking-link finding above (Rank 1) on her real funnel. Not to be used as an opener.

## SMYKM Hook

SMYKM hook: after ten years working quietly behind the scenes she posted on Jul 17 that it's time to show up, and invited people to come join her on the journey from anxiety to abundance — WORK — source: [https://www.instagram.com/p/Da5Z2TDARyk/](https://www.instagram.com/p/Da5Z2TDARyk/)

(NOTE: REFRESHED 2026-07-19 by haytham-hook-finder. Prior hook was her Jul 6 self-relationship post (real + cited) but it paired loosely with the new dead-booking-link finding. This Jul 17 'now it's time to show up, come join me' post pairs tighter (she is actively inviting people in exactly as the one button that lets them book her lands on a Calendly error) and is fresher. Confirmed against her live IG @thrivewithsamira this session. Prior line kept for record: relationship-with-yourself, Jul 6, [https://www.instagram.com/p/Dac-QORgQKR/](https://www.instagram.com/p/Dac-QORgQKR/).)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
