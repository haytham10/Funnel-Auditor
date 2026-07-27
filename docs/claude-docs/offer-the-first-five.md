# The First Five — Offer Spec
 
_Decided 2026-07-27 by Haytham. Supersedes the funnel-fix offer (`docs/uae-track/02-the-offer-gso-v2.md`), the 48-Hour Leak Fix, Track A ($200/735 AED) and Track B ($700/2,575 AED). Those are retired. Evidence base: `claude/uae-market-study-2026-07.md`._
 
## Why the old offer was retired
 
Not because the machine failed. Because the thing it sold could not be sold.
 
- **Leads fix findings themselves.** 4 of 9 engaged leads consumed the finding and left. Avneet: *"Ive fixed most of it. Incase anything else stands out let me know."* Rita fixed her booking flow and swapped to Calendly. The repo's own verdict: *"the finding is small enough that naming it IS fixing it."* Shallow findings are valued in `walk.md` at "~$0 as a standalone sale."
- **A third of findings did not survive contact.** 3–4 of 9 engaged leads had the finding fail under scrutiny. All carried `Finding Verified = YES`. The vision gate passed all of them.
- **Nothing ever died on price.** 3 price-discovery answers, all `Refused to name`, two of three asked us for a number instead.
- **Coaches have teams, and the gate leaks.** 30 leads killed on Gate 1. Donna Brown *passed* Gate 1 and then declined with "Im very happy with my team." Lisa Hugo passed, declined on an in-house team, and turned out to be on GHL via a white-label agency.
- **Zero revenue across 589 leads and three tracks.** 373 UAE + 194 parenting + 22 legacy. 0 calls, 0 closes, 0 AED.
The mechanical cause of 0 calls from 9 replies, per the Saraev comparison: *"A question-shaped CTA is optimised for reply rate and structurally cannot produce a booking. You are getting exactly what you asked for: 9% replies and zero calls."*
 
## The market
 
UAE solo coaches and practitioners with a live paid offer at AED 1,500+ and a calendar to fill. Scope decision: **widen inside UAE first** — work the Instagram vein (best yield at 50% DQ, second-least worked at 20 rows), attempt Arabic-language sourcing (never tried), and revisit the 1,500 audience floor (killed 47 leads).
 
## The dream outcome
 
**Qualified discovery calls on your calendar every week, from people who already know what you charge — without posting, DMing, or chasing anyone.**
 
Not leads. Not a funnel. The thing 46 of 122 walked leads built their entire business entry around and then left empty.
 
## The stack
 
| Problem it kills | Component | Value |
|---|---|---|
| "I don't know who to target" | **The Client Mirror** — ICP built backwards from their own best-paying clients | AED 1,800 |
| "I don't have their details" | **The Named List** — verified, deliverable, gate-checked contacts | AED 2,400 |
| "You'll burn my domain" | **The Clean Domain Shield** — separate sending domain, warmed, SPF/DKIM/DMARC. Their main domain untouched | AED 3,000 |
| "I hate sounding salesy" | **The Written Opener** — every message built on something real about that specific person | AED 3,600 |
| "I'll get tire-kickers" | **The Price-First Filter** — prospects told what they charge before a call is booked | AED 1,200 |
| "They book and don't show" | **The Show-Up System** — confirmation and reminder sequence | AED 1,200 |
| "Agencies take my money and go dark" | **The Weekly Read** — what went out, what replied, what booked, what's changing | AED 900 |
| **Stacked value** | | **AED 14,100** |
 
## The price
 
**AED 1,500 setup, credited back against the first three calls. Then AED 600 per qualified call that actually happens.**
 
No retainer. No contract. No minimum term. Billing starts at call four.
 
Comparison the prospect makes for themselves: appointment-setting agencies charge **AED 7,300–22,000/month whether they deliver or not.** Coach economics: median UAE program AED 1,831, serious tier AED 5,000–18,400. A coach closing one in four AED 5,000 programs makes AED 1,250 per call taken, and pays 600.
 
**Price holds until two clients are delivered.** Same discipline as before: raise in stages, never discount, add value instead.
 
## Guarantees — stacked
 
**① The No-Show, No-Charge Guarantee**
> "You are billed only for calls where a real, qualified person actually shows up. Cancellations, no-shows and time-wasters are on me, not you."
 
**② Five or Free**
> "I'll put five qualified calls on your calendar in your first 30 days. If I don't, the setup fee comes back and you keep everything I built — the domain, the warmed inboxes, the list, the copy, all of it."
 
Type 4 (performance/implied) stacked with type 2 (conditional). This is deliberate: with zero case studies, perceived likelihood is the binding constraint, and a performance structure makes it nearly irrelevant. Max downside per failed client: AED 1,500 refunded plus one month of send capacity.
 
## Scarcity and urgency — both honest
 
**"I run four of these at a time."** Arithmetic, not tactics: each client needs its own sending domain, its own slice of the 50/day ceiling, and every opener is written by hand. State the real number; it doubles as proof this isn't spray-and-pray.
 
Rolling slot urgency: next onboarding date, real, honoured.
 
## The name
 
**"The First Five — 30 Days to a Booked Calendar, for UAE Coaches"**
 
Alternates to test: **"Five Calls, Thirty Days"** · **"The Booked Week."**
 
## What must change in the machine
 
1. **The CTA becomes a call ask with specific times.** This is the single mechanical cause of 0/9. Two files still define the close as a question: `gate.md:38` and `haytham-email-draft/SKILL.md:189`. Reword both or the gate reverts the fix on the next draft.
2. **Add the identity beat.** Lucia and Lee both read Haytham as a prospective coaching client. Two of nine failures caused by an absent sentence. Precedent exists at `examples.md:323` (Emily Ray).
3. **The finding stops being the product and becomes the credibility line only.** Available today with no new proof: "I go through coaching sites here for a living, about a hundred and twenty this year."
4. **Use the Peace Within Home result.** $8,123 single launch, +93% over prior, 6.6% conversion, $522 from one order bump at 1 in 4 buyers. It sits in `audit/evidence.py` and has never appeared in a cold email.
5. **H3a is blocking.** No lead carries a `verified:` tag; a missing tag hard-fails the staleness gate exactly like an old date, so every existing live row fails on its next send. Fix before any sending resumes.
## The two open risks, stated plainly
 
**The delivery math is unproven.** At 15 sends/day and a 7.4% touch-1 reply rate, a month for one client is ~450 sends → ~33 replies → unknown calls. Reply-to-call has been 0 of 9. Five calls in 30 days needs roughly one reply in seven to book. Plausible — the CTA has never once asked for a call — but it is a bet, and Five or Free means Haytham carries it.
 
**No call has ever been booked, for anyone.** Mitigation chosen: run both at once. Repoint the machine at Haytham's own pipeline with the new call-asking CTA while pitching the offer to the six live warm threads. Same machine, two purposes. The moment his own calendar has calls on it, the proof asset exists.
 
## Live threads to re-pitch on this offer
 
| Lead | Audience | Status |
|---|---|---|
| Dina Taji | 114,000 | Replied same morning, engaged, Touch 2 sent |
| William Brown | 57,928 | Replied same day, Touch 5 |
| Rita Baki | 26,000 | Offer Sent, 3,200 AED quote outstanding on work she has since done herself — must be re-scoped |
| Avneet Kohli | 22,748 | Offer Sent, Touch 7, has a written brief and a defined job |
| Lee Harris | 3,782 | Touch 4 |
| Lucia Csobonyei | 1,700 | Replied "I don't understand what are you referring to" — unanswered |
