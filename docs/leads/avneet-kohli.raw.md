<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39f382c8-4585-81c6-a7b1-c4cf53682ea8
Fetched: 2026-07-25T13:42:35Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Avneet Kohli is a solo Business Coach / Founder Advisor based in Abu Dhabi (also spends time in Mumbai), running her own site on Wix. She positions as a "Venture Catalyst, UAE Market Enabler, Business Coach for Women Founders" with a 1:1 Business Advisory & Coaching offer (Calendly booking) plus a paid product, the Life Planner (a self-guided planning toolkit, real price \$30.22 via Stripe, ships to the UAE). 22,748 LinkedIn followers, posted within the last week of qualifying — active. ICF-credentialed, solo operator throughout the funnel. Warm thread as of 2026-07-20 — she's replying same-day and asked directly what Haytham does.
## Funnel Walk
Re-walked 2026-07-20 (prompted by her reply "Ive fixed most of it" — confirming what actually changed before any further touch):
Stop 1 (Bio/Homepage): The header/top-nav logo (the one flagged in Touch 2) now correctly links home — fixed. But the site's separate FOOTER logo (bottom of every homepage view, and of [https://www.avneetkohli.com/blank](https://www.avneetkohli.com/blank) itself) still links to [https://www.avneetkohli.com/blank](https://www.avneetkohli.com/blank), the same orphaned old-design duplicate of the whole site — same defect class, different element, still live.
Stop 3 (Offer/Sales — lifeplanner): RESOLVED. All three order buttons ("ORDER MY COPY" x2, "ORDER A COPY" x1) now route to live Stripe checkout links ([buy.stripe.com](http://buy.stripe.com)); the old Wix test-SKU checkout page ([https://www.avneetkohli.com/product-page/test](https://www.avneetkohli.com/product-page/test)) now returns a hard 404. The AED 9.00 test-SKU issue flagged in Touch 1 no longer exists.
Contact page: unchanged — the visible email link still reads "[ak@avneetkohli.com](mailto:info@avneetkohli.com)" but its mailto target is still "[info@avneetkohli.com](mailto:info@avneetkohli.com)" — still live, still unused as a touch.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 3 of 3 required images confirmed read
- Pasted evidence: none — crawl-only re-walk (homepage, lifeplanner, contact, 2026-07-20)
- Machine flags rejected in the vision pass: none rejected
## Gates
Gate 0: Pass — unchanged since original walk (UAE-based, 22,748 LinkedIn followers clears the audience floor, funnel confirmed live with a working Stripe checkout, and she's actively replying same-day, well inside the activity floor).
Gate 1: Pass — unchanged, solo operator throughout ("I'll get back to you personally," personal replies from her own inbox).
## Lane + Finding
Lane 1: Felt leak — still holds after the re-walk. Two open items survive both filters: the still-broken contact email mismatch (bank #3) and a newly-confirmed footer-logo instance of the /blank link (bank #4). The Touch 1 and Touch 2 findings are both resolved (see Findings Bank).
Strongest open finding: the contact page's displayed email address doesn't match its mailto target — a message sent to the address she shows goes to a different inbox than the one she's replying from.
Innocent explanation: an old alias that probably never got updated when she switched to replying from her personal inbound address.
## Findings Bank
1. RESOLVED (was USED-T1) — Two of three "order" buttons on the Life Planner sales page ([https://www.avneetkohli.com/lifeplanner](https://www.avneetkohli.com/lifeplanner)) routed to a live Wix checkout showing a test SKU at AED 9.00 instead of the real product. Re-walked 2026-07-20: all three buttons now route to real Stripe checkout links and the old test-SKU page 404s. No longer an open finding — do not reuse as a touch carrier.
2. RESOLVED, header only (was USED-T2) — The header logo now correctly links home. The site's separate footer logo still links to /blank — same defect class, different element, tracked fresh as #4 below.
3. UNUSED \| Contact page email link displays [ak@avneetkohli.com](mailto:info@avneetkohli.com) but its mailto target is [info@avneetkohli.com](mailto:info@avneetkohli.com) — confirmed still live 2026-07-20 — innocent: an old alias that probably never got updated when she switched to a personal inbound address.
4. UNUSED \| NEW, confirmed 2026-07-20 — the site's footer logo (present on every homepage view and on /blank itself, distinct from the header logo fixed after Touch 2) still links to [https://www.avneetkohli.com/blank](https://www.avneetkohli.com/blank), the same orphaned old-design duplicate — innocent: likely the same leftover rebuild link, just missed on the second element when the header one got fixed.
## Loom Skeleton
- Show: The footer logo at the bottom of [https://www.avneetkohli.com/](https://www.avneetkohli.com/) (still pointing to /blank) and the contact page's email link at [https://www.avneetkohli.com/contact](https://www.avneetkohli.com/contact) (still mismatched).
- Fix: Point the footer logo home the same way the header logo already got fixed; make the visible contact email match its mailto target.
- Done state: Every logo on the site, header and footer, goes home, and the contact email link goes where it visibly says it goes.
## SMYKM Hook
SMYKM hook: Her show "Forward with Avneet Kohli" just ran an episode with Meeta Gupta (Moolah) unpacking the money blindspots that quietly shape founders' decisions — WORK — source: [https://www.linkedin.com/posts/avneet-kohli_some-of-the-biggest-financial-challenges-activity-7481321066058141697-70Pp](https://www.linkedin.com/posts/avneet-kohli_some-of-the-biggest-financial-challenges-activity-7481321066058141697-70Pp)
## Email Thread Log
\[2026-07-17\] — Touch #1 — Subject: "Meeta Gupta on Forward" — Sent
Hey Avneet
Meeta Gupta is on the next episode of Forward, going into the money
calls founders make without realizing they're making them.
I went through the Life Planner page after that. It has three order
buttons. Two of them do not open the real checkout, they open a Wix
test link, Life Planner Test, priced at AED 9, instead of the actual
\$30.22 product. Only the top button routes correctly.
Someone who clicks either of the other two pays nine dirhams for a
leftover placeholder instead of the real thing.
Looks like a test link that never got swapped out when the page went
live, easy thing to miss.
Have you caught this already, or is it news to you?
Haytham
Reply: No reply
Next: Touch 2 due 2026-07-20
\[2026-07-20\] — Touch #2 — Subject: "Meeta Gupta on Forward" — Sent
Hey Avneet
One more from the same look around.
Your logo up in the corner, the one people click to get home, actually
lands them on an old duplicate version of the whole site instead of
your real homepage. So a click everyone makes on instinct quietly
drops them onto a page you probably forgot was still live.
Almost always a leftover from a rebuild that never got unlinked.
Is that old version meant to still be up, or is it safe to point the
logo back home?
Haytham
Reply: Dear Haytham,
Thank you so much for bringing this to my attention.
Ive fixed most of it. Incase anything else stands out let me know.
Do drop me a line to understand what your work/business is about.
Were you looking to pick up a copy of the Life Planner?
Regards,
Next: Turn-two artifact due — she asked directly what the work is about and floated buying the Life Planner
\[2026-07-20\] — Touch #3 — Subject: "Meeta Gupta on Forward" — Sent
Hey Avneet
That was quick, good to know it's sorted.
To answer your question, I wasn't after the Life Planner. I do the small stuff on the back end for coaches, the pages and the details that quietly cost trust and revenue while you're focused on the actual work, and yours was one I stopped to look at properly.
Want me to record a quick walkthrough of what else I'd tighten while I'm in there? Easier to show than explain.
Haytham
Reply: Yes sure, pls share your work profile.
My current website is built on Wix. Which other platforms do you work with?
Pls advise on costs for branding and landing pages.
Regards,
Avneet
Next: Re-walk complete 2026-07-20 — held for Haytham's next move, no draft queued yet
\[2026-07-20\] — Touch #4 — Subject: "Meeta Gupta on Forward" — Sent
Hey Avneet
Happy to. Here's my site, [https://gethaytham.com](https://gethaytham.com), it's the clearest picture of how I work and what I've built and fixed for people.
On platforms, yours is on Wix and I work in Wix too, so nothing has to move if you don't want it to. When a brand outgrows Wix I build cleaner custom pages that load faster and bend to whatever you need, and honestly, going by what you've built with Encubay and the rooms you're in, you're closer to that line than most.
On cost, branding and pages can mean a quick tidy or a full rebuild, and the number swings a lot depending on which. So before I put a figure on it, I'd rather not guess: what were you expecting something like this to run?
Once I know roughly where your head's at, I'll come back with a real number, and if it's worth a proper conversation we'll find twenty minutes.
Haytham
Reply: Hi Haytham,
Do you mainly work on landing pages and automations?
How about email lifecycle marketing?
Attached is a brief. Im not looking to setup a full fledged CRM. I have data that sits across multiple sheets. I want to segment about 9000 contacts and run a few campaigns with test messaging.
Pls share a costing for a landing page and email marketing.
Do you do logos and branding as well?
Where are you based?
\[attachment: Upwork Brief.pdf\]
Next: She dodged the discovery question — no number, more scope questions instead. Held for Haytham's next move.
\[2026-07-20\] — Touch #5 — Subject: "Meeta Gupta on Forward" — Sent
Hey Avneet
Went through everything you sent. Here's what each piece would cost, so you can see exactly what you're paying for.
Cleaning up your contact list, all 9,000 of them, checking each one is real and getting rid of duplicates: 4,500 AED.
Setting up a simple CRM with proper segments and tags, since you don't need a full build: 3,500 to 5,000 AED.
The Sandbox emails, written and segmented so the right message goes to the right people: 4,500 to 6,000 AED.
A simple dashboard so you can see who opened, who clicked, and who's worth a real conversation: 2,500 AED.
Logo and branding work, if you want that too: 2,500 to 4,000 AED.
First thing I'd do is the contact list. That price is fixed. Once I'm in there and see what shape it's really in, I'll tell you straight, and if it's in better shape than we think, the later numbers go down, not up.
I'm based in Casablanca, Morocco, and I work remote. Here's my site, [https://gethaytham.com](https://gethaytham.com), and here's my Upwork page too, [https://www.upwork.com/freelancers/~0153ea40ea67165be2](https://www.upwork.com/freelancers/~0153ea40ea67165be2), so you can see how past work went.
Easier to walk through the numbers and your actual data on a quick call than keep going back and forth over email. Free Tuesday or Wednesday this week, either work for you?
Haytham
Reply: No reply
Next: Custom project quote (Retainer) — contact list 4,500 AED fixed, CRM/segmentation 3,500-5,000, Sandbox emails 4,500-6,000, dashboard 2,500, branding 2,500-4,000. Call ask for Tue 07-21 or Wed 07-22. Follow up 2026-07-23 if no reply.
\[2026-07-25\] — Touch #6 — Subject: "Meeta Gupta on Forward" — Sent (Inbox 2)
Hey Avneet
Circling back since Tuesday and Wednesday came and went. Happy to find a fresh slot this week, twenty minutes to walk through the list cleanup and go from there.
Haytham
Reply: No reply yet
Next: Awaiting reply or a call-slot pick.
## Price Discovery
Question sent: 2026-07-20 (flip shape — she asked for cost first; promised the real number once she answers)
Their answer (VERBATIM): "Do you mainly work on landing pages and automations? How about email lifecycle marketing? Attached is a brief. Im not looking to setup a full fledged CRM. I have data that sits across multiple sheets. I want to segment about 9000 contacts and run a few campaigns with test messaging. Pls share a costing for a landing page and email marketing. Do you do logos and branding as well? Where are you based?" (also attached a file titled "Upwork Brief.pdf" — not opened/read, flagged for Haytham)
Anchor: Refused to name — she answered with more scoping questions instead of a number or a stated obstacle