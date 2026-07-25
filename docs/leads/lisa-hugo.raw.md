<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39f382c8-4585-81fa-bfd9-d2a50b1001ec
Fetched: 2026-07-25T13:40:53Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Re-audit & Finding Correction (2026-07-17)
Changelog: the original "404 at checkout" finding is RETRACTED, and the sections below now carry the corrected finding. The 404 was a www-only technicality: the newest-post teaser resolves HTTP 200 on the apex host (`lisahugo.com`) in normal navigation, and only a hand-forced `www` spelling of the blog-post URL returns 404. Lisa checked from the apex side and pushed back correctly.
Re-audit ran across three surfaces (funnel deep-walk, Instagram, LinkedIn) on the apex host; every candidate below was curl/grep-verified. Money path and LinkedIn both came back CLEAN (see Evidence). New lead finding = the podcast episode mislabel (Lane + Finding); the IG YouTube dead button and the unconfirmed footer link are banked for the Loom.
## Overview
Lisa Hugo — Dubai-based executive communication / public speaking coach (Leadership), trading as Audacia Marketing Management LLC on GoHighLevel (GHL). Author of "Voice of Influence" (\$17 front-end book) and host of the "Impact Through Voice" podcast (160,000+ downloads). Offer ladder: \$17 book → two free-masterclass webinar funnels (/iai-webinar-registration, /evm-optin) → self-paced courses (Voice of Success \$497, anchored against a \$10,000+ VIP program) → 1:1 / group coaching → client-portal community. 20,000+ email list. Corporate roster referenced: KPMG, Oliver Wyman, DHL, Emirates, Siemens Healthineers. Active — blog updated July 14, 2026 (2 days before this walk).
## Funnel Walk
- Stop 1 (Home / entry) — clean hub with a clear CTA hierarchy (free masterclass, book, About); narrows well, no leak.
- Stop 2 (Freebie) — two live webinar opt-ins (/iai-webinar-registration, /evm-optin), both capture email, evergreen countdowns, real testimonials — functioning.
- Stop 3 (Offer / sales) — \$17 book sales page (/voice-of-influence) shows \$47 struck to \$17 with the correct "Voice of Influence" testimonials rendered; course hub (/training, /online-trainings) is a real paid ladder (Voice of Success \$497 vs a \$10,000+ VIP program). The "GET STARTED" / "LEARN MORE" course buttons DO resolve to `/vos-page` and `/swnf-page` (both 200, complete sales pages) — the earlier "unresolved via cta-probe" note was a false alarm.
- Stop 4 (Checkout, /voi-checkout) — the two-step order form (name/email/phone → payment) functions cleanly, live Stripe. CORRECTED 2026-07-17: the "featured story" card for her newest post that the original walk flagged as a 404 actually resolves HTTP 200 on the apex host; the 404 only appears if the URL is hand-forced to the `www` host. Retracted as a leak — the checkout path is clean.
- Stop 5 (Audience ownership) — owns a 20,000+ email list, a 160K-download podcast, and a multi-page opt-in system — not dependent on rented reach.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 15 of 15 required images confirmed read.
- RETRACTED (was the 2026-07-16 orchestrator "confirmed the leak" line): that verification was run against the `www` host, where the teaser 404s. On the apex host the same teaser returns HTTP 200 in normal navigation, so the "404 at checkout" leak does not hold. Do not reuse.
- Re-audit 2026-07-17 (apex host, curl/grep-verified):
	- Podcast episode mislabel (LEAD finding): `/71` `/70` `/69` all render the show-notes header "ShowNotes for Episode 68"; `/65` correctly reads "Episode 65". Only the three newest episodes are wrong.
	- IG bio-link dead YouTube button: on `lisa-hugo.com/link-bio` the "Lisa Hugo Marketing" button points to `@lisahugomarketingl`, which returns YouTube 404; the correct `@lisahugomarketing` returns 200.
	- Footer "Podcast" link (UNCONFIRMED): a dead `#` self-anchor exists on apex pages, but each page also carries a working `/podcast` link and which anchor sits in the footer is unconfirmed.
	- Money path CLEAN: the \$17 book "INSTANT DOWNLOAD" button opens a working two-step order form with live Stripe; the \$497 course pages (`/vos-page`, `/swnf-page`) return 200; all internal nav, city, and `/resources/*` pages return 200; webinar countdowns are evergreen, not stale.
	- LinkedIn CLEAN: her "Executive Communication in the Middle East" series drives to a shortlink resolving to a complete live guide; every CTA on it returns 200.
- Machine flags rejected: the \$17 book-page template junk ("Big Fat Hooks" / lorem-ipsum) is hidden DOM that never renders to a visitor (this was the exact trap the original finding fell into); an About bio photo blank on webinar screenshots is a lazy-load capture artifact (the image URLs return HTTP 200).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai; "Dubai's Leading Executive Communication Coach"); real reachable paid funnel (\$17 book checkout + \$497 courses + coaching, none login-walled); activity fresh (blog Jul 14 2026); audience 20,000+ email + 160K+ podcast downloads.
Gate 1: Pass — solo operator; own face and voice throughout ("Message From Lisa", "1:1 Coaching With Lisa"); Audacia Marketing Management LLC is her own company, not a gatekeeper.
## Lane + Finding
- Lane 1: Felt leak.
- Strongest finding (bank #1, re-audit 2026-07-17): on her podcast, the three most recent episodes (`/71`, `/70`, `/69`) all render their show-notes header as "ShowNotes for Episode 68." Episode 68 and older are numbered correctly; only the newest three are wrong. Her podcast is her flagship trust asset (160K+ downloads); a new listener who opens the latest episode to decide whether to subscribe sees the notes stamped with the wrong number, so the freshest content on the asset she is known for looks copy-pasted.
- Innocent explanation: episode 68's page was duplicated as the template for 69/70/71 and the show-notes number was never updated.
- (Superseded) The original Lane 1 finding was the "404 at checkout" blog-post card; retracted 2026-07-17 as a www-only technicality (apex resolves 200). See Re-audit note.
## Findings Bank
1. USED-T1 (RETRACTED 2026-07-17) — Original "404 at checkout" finding is INVALID: www-only technicality; the teaser resolves 200 on the apex host in normal navigation, only a hand-forced `www` URL 404s. Lisa pushed back correctly. Do not reuse.
2. USED-T2 (spent 2026-07-17, turn-two) — Podcast: the three newest episodes (`/71`, `/70`, `/69`) all render the show-notes header "ShowNotes for Episode 68"; ep 68 and older are correct. Freshest content on her flagship asset looks copy-pasted. Innocent: ep 68 page duplicated as the template for 69/70/71, number never updated.
3. UNUSED — IG bio link (`lisa-hugo.com/link-bio`): the "Lisa Hugo Marketing" YouTube button points to `@lisahugomarketingl` (stray trailing "l") which 404s; the correct `@lisahugomarketing` is live. Innocent: a typo when the button was set up.
4. UNUSED (unconfirmed) — Sitewide footer "Podcast" link renders as a dead `#` self-anchor on apex pages; each page also has a working `/podcast` link and which anchor sits in the footer is unconfirmed. Verify DOM position before using.
## Loom Skeleton
- Show: open her podcast, click into the newest episode (`/71`), scroll to the show-notes header reading "ShowNotes for Episode 68"; repeat on `/70` and `/69`; contrast with `/65` which reads correctly. Then (optional) open her Instagram bio link and tap the "Lisa Hugo Marketing" YouTube button to the 404.
- Fix: update the show-notes header number on episodes 69/70/71 (they inherited "68" from a duplicated template); correct the trailing "l" on the `@lisahugomarketingl` YouTube button on the link-in-bio page.
- Done state: her newest episodes carry their own numbers so the freshest content looks maintained, and the bio-link YouTube button reaches her actual channel.
## SMYKM Hook
SMYKM hook (USED, Touch 1): her current LinkedIn series on executive presence in the Middle East - the line that how you respond to the first cup of Arabic coffee can set the tone for the whole relationship, because in GCC business the relationship IS the business - WORK - source: [https://www.linkedin.com/posts/lisa-hugo_executive-communication-in-the-middle-east-activity-7483431276889137152-CAlq](https://www.linkedin.com/posts/lisa-hugo_executive-communication-in-the-middle-east-activity-7483431276889137152-CAlq) (posted 2026-07-16)
Fresh hook candidates (re-audit 2026-07-17, UNUSED, for future touches — all real and cited):
- The Vinh Giang clip she sat on for months because she was self-conscious about how she showed up (dead phone battery, felt unprepared), then released for his "voice as an 88-key instrument" idea that mirrors her own teaching. Source: [IG](https://www.instagram.com/p/Daf1fLIju6O/) / [LinkedIn](https://www.linkedin.com/posts/lisa-hugo_earlier-this-year-i-had-the-opportunity-activity-7480288296053510144-94za), 2026-07-07.
- Conditioning her two daughters that filler words were "almost as bad as a swear word," now credits it for them being confident speakers. Source: [IG](https://www.instagram.com/p/DaSH27Mlm_E/), 2026-07-02.
- Her 57th birthday post / going public about her age ("Fifty is the new thirty"). Source: [IG](https://www.instagram.com/p/DaXcsv_u1Tc/), 2026-07-04.
## Email Thread Log
\[2026-07-17\] — Touch #1 — Subject: "the first cup of coffee" — Sent
Hey Lisa
Your posts this week on reading the room in the Gulf, the part about
the first cup of coffee mattering more than the pitch, most
communication coaches never clock that. You have actually lived it.
Which is why I went through your site, and one thing is worth a
mention. Your newest piece on developing an executive voice sits on
your homepage and again on the checkout page for your book. Both links
open a page that just says 404, not found.
So someone on your book page, card half entered, clicks your freshest
thinking and lands on a dead end. Right at the moment they had decided
to trust you.
Is the post still being set up, or did the link just not get pointed
at the new page?
Haytham
Reply: \[2026-07-17\] Lisa Hugo replied: "Hey Haytham, Thanks for the heads up and for reading the posts. Glad that resonated. That's brutal about the 404s. I need to check on that immediately. I think the link got pointed wrong when we updated the site structure. I will get that fixed ASAP. Thanks, Lisa"
Reply: \[2026-07-17\] Lisa Hugo replied again (\~5 min after the first): "Hey Haytham, I just checked and don't encounter any issues. I assume you mean the blog in the footer on each page? All working perfectly for us. Lisa"
\[2026-07-17\] — Touch #2 (turn-two, warm) — Subject: "Re: the first cup of coffee" — Sent
Hey Lisa
Fair enough, you were right. I had you on the www spelling, and for anyone landing the normal way it redirects and opens fine. My miss, not yours.
So I went back and looked properly this time, and here is one that is real. On your podcast, the three most recent episodes all have their notes headed "Episode 68," the newest one included. The older episodes are numbered correctly, it is just the last three that got stamped with the wrong number.
Your show is the first thing a lot of people meet you through. Someone opens your latest episode to decide whether to subscribe, and the notes look copied from an older one. Small thing, but it sits on the freshest content on the asset you are known for.
I do the behind the scenes side for coaches, the pages and the small things that quietly chip at trust while you stay focused on the actual work. Found a couple more while I was in there. Want me to record a quick walkthrough showing them? Easier to show than explain.
Haytham
Reply: No reply
Next: Warm turn-two sent 2026-07-17. If she replies: Loom (podcast fix + the IG YouTube button; confirm the footer link first if using it), then the price-discovery question before any number. If no reply, warm bump \~2026-07-20.
\[2026-07-25\] — Touch #4 — Subject: "Re: the first cup of coffee" — Sent (Inbox 2)
Hey Lisa
Still keen to record that walkthrough for you, just need a yes.
Haytham
Reply: No reply yet
Next: Awaiting a yes on the Loom offer.
## Price Discovery