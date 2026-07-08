# Pipeline Schema + Page Body Format

## Pipeline database

Data source ID: `c6209e29-55ef-4781-b735-73b2a254e34f`

## Properties reference

The user fills manually (already set when the skill runs): Contact Name, Email, Site URL, Profile URL.

The skill fills everything else from the walk observations and screenshots:

| Property | Type | What to set |
|---|---|---|
| Business Name | text | Brand name if different from person name. Extract from bio, site header, or handle. |
| Niche | multi_select | One or more of: Conscious Parenting, Gentle Parenting, Sleep, Screen Time, Faith-based, Special Needs, Postpartum, Educator, Mom Mental Health, Other |
| Followers | number | IG follower count if visible in screenshots or notes. Leave blank if not visible. |
| Platform | select | Kajabi, Skool, Shopify, Teachable, Thinkific, Podia, Squarespace, WordPress, GHL, Other, Unknown. Infer from page design, URL, or checkout style. |
| Main Offer | text | One line. Primary paid product + price if known. |
| Source | select | Lateral Discovery, Hashtag, Podcast, Google Search, Comments, Referral, Directory, Other. Set from context if known, otherwise leave blank. |
| Tier | select | Tier 1: Start here (committed buyer + felt leak, real audience), Tier 2: Qualify first (committed but no leak or smaller signal), Tier 3: Long play (warm-up only, no near-term close), Tier 4: Skip (hobbyist/gatekeeper) |
| Notes | text | One line. Strongest finding or one-line flag. Full detail goes in the body. |
| Lane | select | "Lane 1: Felt leak" / "Lane 2: No leak" / "Lane 3: Skip" |
| Finding Type | select | "No opt-in capture" / "Weak/no nurture sequence" / "Broken checkout" / "No order bump/upsell" / "Weak sales page" / "No launch system" / "Dead/stale element" / "Other". Prefer "Dead/stale element" for time-bound breakage (stale dates, empty calendars, dead links, expired events, placeholders) — most warm repliers to date live in that category. |
| Status | select | "Audit Ready" if Lane 1 or 2. "Disqualified" if Lane 3. |
| Est. Value | select | $300-600, $1.2k-2.5k, $2k-3.5k/mo, Retainer, Unknown. Infer from offer type and scope. |

Sequence, Touch #, Last Contacted, Next Action, Lost Reason — leave blank. Those are set by the email skill and the user during outreach.

## Page body structure (exact format, always in this order)

Every lead page body follows this structure. Write it fresh — don't append to existing content unless a walk is already there and you're adding the email thread log.

---

```
## Overview
One short paragraph. Name, business, niche, platform, main offer. Human context that doesn't fit in a field.

## Funnel Walk
One line per stop where something was found or ruled out. Skip clean, unremarkable stops.
Format: Stop X — [what's there] — [what it means]

## Evidence
Two lines, always present (added Jul 2026 for the automated runs):
- IG evidence: [N screenshots read from page attachments / pasted in chat] OR "none — site-only walk".
- Machine flags rejected in the vision pass: [N — one-word reason each] OR "none rejected".

## Gate 1
Solo-operator signals or gatekeeper flags. One to two lines.

## Lane + Opening Angle
Three lines max.
- Lane verdict + one-phrase reason.
- The opening angle (Lane 1) or warm-up/ask-the-number entry (Lane 2). Omit entirely if Lane 3.
- Innocent explanation (Lane 1, required): the plausible non-blame reason for the finding, one phrase. Feeds the either/or closing question in the email.
- SMYKM hook on its own line if found, labeled with type: WORK / LIFE / METRIC.

## Email Thread Log
(Leave this section blank on a fresh walk — the email skill and the user fill it in after sends.)
```

---

## Real example (Ghadir Salah Aldine — Lane 1)

```
## Overview
Ghadir Salah Aldine (@coach_ghadirsalahaldine). Parent Coach ICF-ACC, Family & Educational Consultant, NLP Practitioner, Behavior Modification specialist. 54.8K followers, 1,282 posts. Arabic-speaking audience. Helped 500+ families. Runs her own inbox — replies manually.

## Funnel Walk
Stop 1 (Bio): one Linktree link.
Stop 2 (Linktree): single link "Online Consultation Form" plus social icons. No freebie, no resources, nothing else.
Stop 3 (Jotform): full intake form. Fields: full name (prefix/first/middle/last), birth date, gender, full home address, mobile, email, occupation, appointment booking with calendar, main problem, contributing factors, free-text question, signature, CAPTCHA. No price anywhere. No paid offer visible anywhere in the funnel.

## Gate 1
ICF-ACC certified, NLP practitioner, 1,282 posts, 500+ families in bio. Solo operator — own face, own kids, replies manually. No team signals.

## Lane + Opening Angle
Lane 1 — felt friction leak. 54.8K parents trust her enough to click. The one path to reach her is a form that asks for home address and a signature before they've spoken to her. Most close the tab. She never hears from them.
SMYKM hook: birthday post (Jun 14) — Hello 35, a new chapter is beginning — two cakes photo. Used the new chapter framing as the natural transition into the finding.

## Email Thread Log
(empty — filled after sends)
```

---

## Real example (Catherine Divaris — Lane 2)

```
## Overview
Catherine Divaris (@catherinedivaris), "The Maternal Arc | Mom Potential." 10.7K, mid-size, runs her own inbox. Niche: nervous-system / mental-load for moms, neuroscience-backed. 15+ years mental health and OT background. IVF twin mom. Strong consistent content engine.

## Funnel Walk
Stan store (stan.store/mompotential) well built: multiple free lead magnets (Nervous System Checklist, Mental Load Reset, Loving Kindness script, Holiday Calm guide) + workshop waitlist with email capture + paid offers ($11 Holiday Calm Playbook, 1:1 Capacity Call). Organized free to paid ladder.
1:1 booking page (Capacity Call): only 2 available slots showing in June (24 and 25). Reads as almost fully booked from the outside. Unconfirmed whether intentional or stale calendar.

## Gate 1
Runs own inbox. Replies personally to comments. ✅

## Lane + Opening Angle
Lane 2 — no felt structural leak. Strong funnel, strong buyer profile. Opened on the booking scarcity observation as a specific, checkable question.
Opening angle: her 1:1 booking page only shows 2 slots left in June — from the outside it looks almost fully booked. Not asserting a leak, asking whether it's intentional or stale.

## Email Thread Log
(empty — filled after sends)
```

---

## Writing rules for the page body

- Stop-by-stop format: "Stop X (Name): [what's there] — [what it means]." Skip stops that were clean and unremarkable.
- Lane verdict in one phrase. Opening angle in one to two sentences max.
- SMYKM hook on its own line if found. Label it clearly.
- No editorializing, no hedging, no "it might be worth considering." State what's there and what it means.
- The Email Thread Log section is always left blank by this skill. The user fills it in after sends.
