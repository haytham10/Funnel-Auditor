# The 5-Stop Funnel Walk — UAE track

## The master principle (memorize this)

A leak is any point where attention the coach already earned fails to convert toward money she can see — AND she'd feel the cost if you named it.

If something fits this and isn't listed below, it's still a leak. If it doesn't fit, it's not, however "improvable" it looks. The list below is illustrations under the principle, not the whole universe.

Named receipts below (Pam, Kathleen, Suzanne, …) come from the parenting pipeline — the market changed, the leak mechanics didn't. They stay because they're real verified instances of each pattern.

## The funnel shapes this market runs on

The parenting pool was almost all link-in-bio → freebie → low-ticket course. UAE business/life/career coaches run three additional shapes, and each has its own characteristic leaks. Walk them with the same 5 stops — the stops map onto every shape:

- **Webinar funnels** (live or evergreen): registration page → confirmation/replay → pitch → offer. Characteristic leaks: stale webinar dates still advertised, registration that confirms but never delivers a link, evergreen replay pages that 404, a pitch offer whose checkout is closed between launches.
- **Call-booking flows**: content → booking page (Calendly/GHL/etc.) → sales call. Characteristic leaks: calendars with zero available slots, intake forms demanding trust the page hasn't earned, booking confirmations that never arrive, a "book a call" button as the ONLY path with no lower-commitment step and no email capture around it.
- **Cohort launches**: waitlist → open cart → cohort. Characteristic leaks: a passed cohort start date still showing, "enrollment closed" with no waitlist capture (the highest-intent visitors bounce with no way to reach them), early-bird pricing whose deadline already passed, cart pages left open with a dead payment link between rounds.

## Tier system (severity — how badly it leaks)

- **Tier A** — Critical. Blocks conversion entirely. Provably broken. Opener-grade on its own.
- **Tier B** — Strong. Real money leaking. Requires some framing but the cost is real and felt.
- **Tier C** — Soft. Technically suboptimal, low felt cost. Rarely a Lane 1 opener. Needs the sting test to survive.

---

## Depth tiers (self-fixability — who can fix it)

Tier A/B/C measures how badly a leak bleeds. **Depth is a second, independent
axis: can the coach fix this herself in five minutes, or does it take
expertise and judgment she'd pay for?** The two axes are orthogonal — a Tier A
dead link is critical AND shallow; a Tier B pricing-architecture leak is
less provable AND deep. Classify every flagged finding on BOTH.

The reason this axis exists: the most falsifiable finding is almost always the
most trivial one, and the coach reads the opener, fixes the small thing herself
for free, and replies "thanks, fixed it" with no reason left to pay. Rita fixed
her booking redirect, Avneet fixed her test-SKU checkout and logo, Lisa said "we
are on fix this." Optimizing openers for the most provable finding optimized
them against revenue. Depth is the correction.

**This is now enforced, not advised (2026-07-27).** `crm-gate send` hard-fails a
touch-1 opener that draws an untagged or SHALLOW bank entry. Depth shipped as
ranking guidance on 2026-07-26 and by the next day the live CRM read 203 of 225
entries with no depth tag at all, 8 of 91 leads with any DEEP finding, and about
a third of openers still self-fixable. Guidance was tried. **Every bank line
needs a DEPTH tag, and the opener has to be DEEP.**

- **Shallow / self-fixable (janitorial).** She fixes it in minutes once it's
  named. Worth ~$0 as a standalone sale — naming it earns the reply, not the
  money. Examples: a dead or broken link, a logo/CTA pointing at the wrong
  page, a test or placeholder SKU left live, a booking form that should be a
  scheduler, a stale cohort/webinar date, a typo, a broken image, **a booking
  widget that publishes no bookable time at all** (a configuration problem —
  see the calendar split below). Most of Stop 1 (entry), Stop 2 delivery misses,
  and Stop 4 (checkout/booking breakage) skew shallow — they're breakage, not
  strategy.
- **Deep / un-self-fixable.** Requires expertise, judgment, or a rebuild she
  can't do from a one-line email. This is what a coach pays to solve. Examples,
  drawn from the deep-audit diagnosis references
  (`haytham-funnel-auditor/references/{copy,offer,structure}-diagnosis.md`):
  - **Pricing/offer architecture** — pricing fragmented across 4 platforms so
    buyers bounce at the seam (Rita); multi-session packages that cost more per
    session than singles (Lucia); a disconnected value ladder or missing
    order-bump economics (offer-diagnosis "Offer Diagnostic Matrix").
  - **No owned audience** — 100% rented on one platform with zero owned capture
    (Lee); the structural version of Stop 5, not the janitorial "add a signup
    box" version.
  - **Product-value leakage** — an entire paid program readable free, so
    there's no reason to buy (William, an £8k course fully readable). See the
    offer-diagnosis value-equation levers.
  - **Awareness / message-market mismatch** — copy pitched at the wrong Schwartz
    awareness stage, Orphan Lead / Excite Void / Dead-End Ascension structural
    gaps (copy- and structure-diagnosis matrices).
  - **An unbooked calendar** — a working scheduler with most of the next month
    still open. She cannot fix this by editing anything; the gap is demand, not
    configuration. See the split below.
  Stop 3 (offer/pricing) and Stop 5 (audience ownership, structural) are where
  deep findings usually live.

### The calendar split (2026-07-27)

"An empty calendar" used to sit in the shallow list. It was two different facts
wearing one label, and only one of them is an opener:

| What you see | What it means | Depth |
|---|---|---|
| Scheduler resolves, publishes **zero** bookable time | a configuration problem she fixes in five minutes | **SHALLOW** — never the opener |
| Scheduler works, **most of the next month is open** | nobody is booking her | **DEEP** — opener-legal |
| Normally busy | not a finding at all | neither — do not bank it |

Settle it with `python main.py calendar-state <booking-url>`, which reads the
same public no-login endpoint her own booking widget calls and returns
`verdict`, `depth`, `open_slots` and `opener_legal`. Quote its literal numbers;
they are the finding. It covers Calendly and Cal.com and returns an explicit
error for anything else — **never infer availability from a screenshot**, since
a booking widget renders after the capture and a working calendar routinely
photographs as blank space (that is exactly what `BOOKING_EMBED_HOSTS` exists to
warn about).

The command raises rather than reporting zero when the API errors. If it errors,
you have no calendar finding — you do not have an empty calendar.

**Depth is independent of provability.** A shallow finding can be Tier A
(provably, visibly broken) and still worth ~$0 to sell. Do not let "most
falsifiable" stand in for "best" — that's exactly the trap. A deep finding that
takes a sentence of framing beats a shallow finding that's a screenshot-proof
slam dunk, because only the deep one survives being handed over.

**Every Lane 1 lead must carry at least one deep finding, held in reserve.** The
opener can be shallow (it earns the reply — the Emily Ray move), but a deep
finding is the reason to get on a call and is never given away in email. If the
walk surfaces no deep finding at all, the lead is low-value: reply-likely,
close-unlikely. Flag it as such (see `SKILL.md` Step 4) rather than pretending a
shallow finding will close. Selection and the reserve mechanic live in
`SKILL.md` Step 4; this file's job is the classification.

---

## Stop 1 — The entry point (homepage, profile link, bio link)

**Question:** Tap it. One clear next step, or a pile of choices / dead end?

Principle: the first click should narrow toward a single action.

Known patterns:
- 404 / error → Tier A (Layal, Latisha)
- Link page with 4-5 near-equal links, no "start here" → Tier C (Emily, Latisha)
- Drops onto bare checkout, no sales page → Tier B (Kathleen)
- Homepage leads with a contact form, not the offer → Tier C (Rania)
- LinkedIn profile link points to a dead or outdated destination while the profile actively promotes a program → Tier B (the profile is doing the earning, the link is doing the losing)
- Catch-all: anything that makes the first click harder instead of narrowing it (splash, interstitial, login, "choose your path" with no default)

**Verify rule:** always check incognito or logged-out. A "broken" thing might only be broken for you. Hard 404 ("file does not exist") = genuinely dead, openable. Permission wall ("you need access") = works fine for her audience, NOT openable.

---

## Stop 2 — The freebie / opt-in

**Question:** Can a stranger get something free right now, and does it ask for an email?

Principle: a free taste should be reachable AND capture a contact.

Known patterns:
- No freebie at all, everything goes to paid/booking → Tier C (vitamin trap — only a leak if framed as felt cost)
- Freebie buried (linked from one old post, not the site) → Tier C (Maysaa)
- Only a sample locked behind paid signup → Tier B (Katie)
- Freebie delivers with NO email capture → Tier B
- Freebie lands on a raw Google Drive PDF with no email capture anywhere → Tier A (Dr. Alex)
- Webinar registration that captures the email but never sends the link/replay → Tier A (verify from a clean state; see manual-delivery rule)
- Catch-all: any free→contact step that's missing, hidden, or one-directional

**Manual-delivery rule:** before opening on "your freebie didn't arrive," check whether delivery is automated or manual. A solo coach often sends things by hand. Look at her replies to OTHER people — instant auto-delivery = automated (a real miss); hand-typed personal replies = manual (your test just hasn't arrived yet). Never open on a manual-delivery "miss."

**Ghost test (run when possible):** opt in to their freebie from a real email, wait 48 hours. If you receive nothing after initial delivery, or only a single generic email with no follow-up, the backend is dark. Frame as felt cost: "downloaded your guide two days ago and noticed I haven't heard anything since — is that on purpose?" Never lead with "you need an email sequence" (mechanism — and "sequence" is banned vocabulary anyway).

---

## Stop 3 — The offer / sales page

**Question:** In 10 seconds, can I tell what the paid thing is, the price, and why I'd want it?

Principle: confusion at the buy moment is the most expensive leak — it kills people who were ready.

Known patterns:
- Price shown contradictory ways (multiple prices, inconsistent) → Tier B, strong (Rania)
- Price hidden entirely → Tier B (Rachel). `Finding Type: No visible pricing`
- 4-5 near-equal offers, no flagship → Tier C (Emily)
- Wall of text, no hierarchy → soft, usually a shrug — hold unless cost can be made felt
- Kick-off / cohort / webinar date stale (passed date still showing) → Tier B (Pam — people who get sold hit a passed date, feel they missed it, close the tab)
- "Enrollment closed" with no waitlist capture → Tier B (highest-intent visitors, zero way to reach them again)
- Early-bird or launch pricing whose deadline already passed, still displayed → Tier B (tells every visitor the page is unattended)
- Catch-all: anything that makes "what do I buy and why" take longer than ~10 seconds

---

## Stop 4 — The checkout / booking

**Question:** If I tried to pay or book right now, would anything stop me?

Principle: the path from "I want it" to "I paid" must be unbroken.

Known patterns:
- Checkout errors → Tier A (Suzanne)
- Form doesn't submit → Tier A (Tammy)
- Entry link lands on a login wall, not a buyable page → Tier A (Suzanne)
- Booking calendar with zero available slots → Tier A if genuinely stuck, but ASK-grade — could be intentional scarcity or a fully-booked month; verify before opening. `Finding Type: Broken booking flow`
- Booking flow that errors, loops, or never confirms → Tier A
- Bare checkout, no order bump → Tier B. A stock platform checkout (Kajabi, Thinkific, GHL alike) is cold and clinical — no social proof, no guarantee, no order bump. Adding a small companion product at checkout is the easiest revenue lift with zero extra marketing. Real receipt: $522 from one order bump. Frame as missed revenue at the highest-intent moment.
- Intake form friction: a form that asks for extensive personal detail (full address, signature, long questionnaires) before the person has ever spoken to the coach → Tier B (a felt barrier at the highest-intent moment — receipt: Ghadir, 54.8K followers behind a single form demanding home address + signature)
- Catch-all: anything between decision and payment that adds friction or fails (forced account creation, broken payment, redirect loop)

---

## Stop 5 — Do they OWN the audience?

**Question:** If the platform vanished tomorrow, could they still reach these people?

Principle: attention reachable only through a platform they don't control is rented. Frame as felt loss, NEVER "you need a list." This system knows the felt version of this loss first-hand: its own sourcing channel was a single platform account, permanently banned.

Known patterns:
- No capture anywhere → Tier C, needs felt-cost framing (Kristy — "49K followers and she owns none of them")
- Traffic routes to affiliate links, her audience's money goes elsewhere → Tier B (Kristy)
- Entire business runs through one platform's DMs/inbox with no backup → Tier B (Sidra)
- Podcast page empty (active show sends people there, nothing is there) → Tier B (Adrienne)
- Podcast or YouTube audience with no bridge to paid programs → Tier B (Darlynn — 26K listeners, toolkit last page sends back to the podcast only)
- LinkedIn-only presence: posts daily to a real following, profile link is the only exit, no capture anywhere on the destination → Tier B when the audience is real (the UAE version of the rented-audience leak)
- Catch-all: anywhere audience or revenue leaves to a third party she doesn't own

---

## Patterns that look like leaks but aren't

- Permission wall on a link ("you need access") — works fine for her audience, just not for you
- A freebie that hasn't arrived yet (could be manual delivery — check first)
- Calendar showing limited slots (could be intentional scarcity, not a broken calendar — ask)
- A booking-only model with a working paid-call business behind it (email list is a vitamin here)
- "Enrollment closed" WITH a working waitlist capture — that's a launch model operating correctly
- A single storefront (Stan-style) with no freebie (may be an intentional model — check for a paid ladder before flagging)
- **A single screenshot's broken-image icon is not proof of a broken site** (added Jul 13, 2026, after a false Lane 1 finding on Jen Lumanlan). Lazy-load image widgets (e.g. Ontraport's `opt-lazy-img`, and similar patterns on other builders) swap `data-src` into `src` on a JS/scroll trigger — if the screenshot is captured before that swap finishes, it catches a transient placeholder, not a real defect. Before calling a broken image a finding: fetch the image URL directly (`curl -o /dev/null -w "%{http_code}"`) or re-capture the screenshot; if the URL loads fine, the finding is dead.
- **A machine "dead link" claim needs a live re-check, not just a screenshot glance** (added Jul 13, 2026, after a false Lane 1 finding on Crystal Haitsma). `audit/checks/links.py` used to only retry a failed HEAD request with GET on 403/405/429/999, never on a bare 404 — but redirect/proxy endpoints (Kajabi's `resource_redirect/*` confirmed, likely others) commonly 404 a bare HEAD while resolving 200 on GET. Fixed in the checker (now retries GET on 404 too), but treat any "dead link" list as a candidate, not a fact, until you've independently confirmed at least one with a live GET (`curl -I` then `curl -L` on the same URL) — a screenshot alone can't confirm a link is dead, only that a page loaded.

---

## The two filters (run on every flagged finding)

**Sting test:** would she FEEL this as a lost cost, or shrug? A technically suboptimal thing that runs fine for her audience is not an opener.

**Vitamin filter:** FELT COST (money or attention leaking now) or a MECHANISM she lacks ("you need an email list")? Mechanisms don't convert cold. Reframe as felt loss if possible. "You have no email capture" = mechanism. "The people who almost bought when your cart was open have no way to hear you open it again" = felt cost.

A finding that fails either filter is Lane 2 territory at best.
