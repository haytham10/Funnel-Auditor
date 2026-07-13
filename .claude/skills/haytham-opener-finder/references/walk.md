# The 5-Stop Funnel Walk

## The master principle (memorize this)

A leak is any point where attention the coach already earned fails to convert toward money she can see — AND she'd feel the cost if you named it.

If something fits this and isn't listed below, it's still a leak. If it doesn't fit, it's not, however "improvable" it looks. The list below is illustrations under the principle, not the whole universe.

## Tier system

- **Tier A** — Critical. Blocks conversion entirely. Provably broken. Opener-grade on its own.
- **Tier B** — Strong. Real money leaking. Requires some framing but the cost is real and felt.
- **Tier C** — Soft. Technically suboptimal, low felt cost. Rarely a Lane 1 opener. Needs the sting test to survive.

---

## Stop 1 — The bio link

**Question:** Tap it. One clear next step, or a pile of choices / dead end?

Principle: the first click should narrow toward a single action.

Known patterns:
- 404 / error → Tier A (Layal, Latisha)
- Linktree 4-5 near-equal links, no "start here" → Tier C (Emily, Latisha)
- Drops onto bare checkout, no sales page → Tier B (Kathleen)
- Homepage leads with a contact form, not the offer → Tier C (Rania)
- Catch-all: anything that makes the first click harder instead of narrowing it (splash, interstitial, login, "choose your path" with no default)

**Verify rule:** always check incognito or logged-out. A "broken" thing might only be broken for you. Hard 404 ("file does not exist") = genuinely dead, openable. Permission wall ("you need access") = works fine for her audience, NOT openable.

---

## Stop 2 — The freebie

**Question:** Can a stranger get something free right now, and does it ask for an email?

Principle: a free taste should be reachable AND capture a contact.

Known patterns:
- No freebie at all, everything goes to paid/booking → Tier C (vitamin trap — only a leak if framed as felt cost)
- Freebie buried (only on Linktree, not in bio) → Tier C (Maysaa)
- Only a sample locked behind paid signup → Tier B (Katie)
- Freebie delivers with NO email capture → Tier B
- Comment-for-freebie flow → CAUTION: don't assert broken off one test. Check if delivery is automated or manual (see manual-delivery rule below)
- Freebie lands on a raw Google Drive PDF with no email capture anywhere → Tier A (Dr. Alex)
- Catch-all: any free→contact step that's missing, hidden, or one-directional

**Manual-delivery rule:** before opening on "your freebie didn't arrive," check whether delivery is automated or manual. A solo coach often DMs manually. Look at her replies to OTHER commenters — instant auto-DM = automated (a real miss); hand-typed personal replies = manual (your test just hasn't arrived yet). Never open on a manual-delivery "miss."

**Ghost test (run when possible):** opt in to their freebie from a real email, wait 48 hours. If you receive nothing after initial delivery, or only a single generic email with no follow-up, the backend is dark. Frame as felt cost: "downloaded your guide two days ago — noticed I haven't heard anything since. are you running a follow-up sequence, or is that still on the list?" Never lead with "you need an email sequence" (mechanism).

---

## Stop 3 — The offer / sales page

**Question:** In 10 seconds, can I tell what the paid thing is, the price, and why I'd want it?

Principle: confusion at the buy moment is the most expensive leak — it kills people who were ready.

Known patterns:
- Price shown contradictory ways (multiple prices, inconsistent) → Tier B, strong (Rania)
- Price hidden entirely → Tier B (Rachel)
- 4-5 near-equal offers, no flagship → Tier C (Emily)
- Wall of text, no hierarchy → soft, usually a shrug — hold unless cost can be made felt
- Sales page kick-off date stale (passed date still showing) → Tier B (Pam — moms who get sold hit a passed date, feel they missed it, close the tab)
- Catch-all: anything that makes "what do I buy and why" take longer than ~10 seconds

---

## Stop 4 — The checkout

**Question:** If I tried to pay now, would anything stop me?

Principle: the path from "I want it" to "I paid" must be unbroken.

Known patterns:
- Checkout errors → Tier A (Suzanne)
- Form doesn't submit → Tier A (Tammy)
- Bio link lands on a login wall, not a buyable page → Tier A (Suzanne)
- Bare Kajabi checkout, no order bump → Tier B. Stock Kajabi checkout is cold and clinical — no social proof, no guarantee, no order bump. Adding a $17-27 companion product at checkout is the easiest revenue lift with zero extra marketing. Real receipt: PWH $522 from one order bump. Openable on any Kajabi coach whose checkout is bare. Frame as missed revenue at the highest-intent moment.
- Catch-all: anything between decision and payment that adds friction or fails (forced account creation, broken payment, redirect loop)

**Intake form friction (new pattern):** a Jotform or intake form that asks for full name, birth date, home address, and signature before the person has spoken to the coach is friction filtering parents out before she hears from them. Not a broken checkout, but a felt barrier at the highest-intent moment (Ghadir — 54.8K followers, single Jotform with home address + signature required).

---

## Stop 5 — Do they OWN the audience?

**Question:** If Instagram vanished tomorrow, could they still reach these people?

Principle: attention reachable only through a platform they don't control is rented. Frame as felt loss, NEVER "you need a list."

Known patterns:
- No capture anywhere → Tier C, needs felt-cost framing (Kristy — "you have 49K followers and own none of them")
- Traffic routes to affiliate links, her audience's money goes elsewhere → Tier B (Kristy)
- Entire business runs through IG DMs with no backup → Tier B (Sidra — "we thought we were being clever, we were not")
- Podcast page empty (active sends people there, nothing is there) → Tier B (Adrienne)
- Podcast listeners with no bridge to paid programs → Tier B (Darlynn — 26K listeners, toolkit last page sends back to podcast only)
- Catch-all: anywhere audience or revenue leaves to a third party she doesn't own

---

## Patterns that look like leaks but aren't

- Permission wall on a link ("you need access") — works fine for her audience, just not for you
- Comment-for-freebie that hasn't arrived yet (could be manual delivery)
- Calendar showing limited slots (could be intentional scarcity, not a broken calendar — ask)
- Stan store with no freebie (may be intentional model — check for paid ladder before flagging)
- Strong funnel with no email list but a working paid-call model (email list is a vitamin here)
- **A single screenshot's broken-image icon is not proof of a broken site** (added Jul 13, 2026, after a false Lane 1 finding on Jen Lumanlan). Lazy-load image widgets (e.g. Ontraport's `opt-lazy-img`, and similar patterns on other builders) swap `data-src` into `src` on a JS/scroll trigger — if the screenshot is captured before that swap finishes, it catches a transient placeholder, not a real defect. Before calling a broken image a finding: fetch the image URL directly (`curl -o /dev/null -w "%{http_code}"`) or re-capture the screenshot; if the URL loads fine, the finding is dead.
- **A machine "dead link" claim needs a live re-check, not just a screenshot glance** (added Jul 13, 2026, after a false Lane 1 finding on Crystal Haitsma). `audit/checks/links.py` used to only retry a failed HEAD request with GET on 403/405/429/999, never on a bare 404 — but redirect/proxy endpoints (Kajabi's `resource_redirect/*` confirmed, likely others) commonly 404 a bare HEAD while resolving 200 on GET. Fixed in the checker (now retries GET on 404 too), but treat any "dead link" list as a candidate, not a fact, until you've independently confirmed at least one with a live GET (`curl -I` then `curl -L` on the same URL) — a screenshot alone can't confirm a link is dead, only that a page loaded.

---

## The two filters (run on every flagged finding)

**Sting test:** would she FEEL this as a lost cost, or shrug? Lynsey's strong hero image, Cassie's whole funnel — those are shrugs. A technically suboptimal thing that runs fine for her audience is not an opener.

**Vitamin filter:** FELT COST (money or attention leaking now) or a MECHANISM she lacks ("you need an email list")? Mechanisms don't convert cold. Reframe as felt loss if possible. "You have no email capture" = mechanism. "You have 54K parents who click and you have no way to reach them again" = felt cost.

A finding that fails either filter is Lane 2 territory at best.
