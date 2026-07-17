# Apify actor layer — the no-login third-party fetch path

Firecrawl (the primary fetcher) hard-refuses LinkedIn and does not do
authenticated Instagram. Those two login-walled platforms carry the best
SMYKM hook evidence, so without a fetch path they're invisible. This layer
is that path: read-only public data through vetted Apify actors that take a
username or URL and need no account — exactly what the hard rules allow
(`read-only public data pulled through a no-login third-party tool ... is
allowed for enrichment and SMYKM hook-finding, Instagram the same as
LinkedIn`). It never logs in and never acts as Haytham anywhere.

Code: `audit/apify.py`. CLI: `python main.py apify …`. It prints JSON to
stdout, the same shape the rest of the machine's commands use, so skills
consume it by shelling out.

**Email verification and Google-footprint sourcing no longer default to
this layer (2026-07-17).** The free plan's small monthly USD cap kept
getting hit, and the paid tier that unlocks Store-actor access (the
`li-posts`/`li-profile`/`ig` actors below are all Store actors) starts at
$29/month — Apify's own $1/month Creator Plan doesn't help here, since it
explicitly blocks Store-actor access and only allows Apify's own
"universal" actors or actors you build yourself. So instead of buying more
Apify headroom, the two consumers that don't strictly need Apify moved off
it:

- **Email verification** now defaults to **ZeroBounce** (`audit/
  email_verifier.py`, `python main.py email-verify`/`email-enrich`) — its
  free tier is 100 verification credits/month, no card, credits don't
  expire. Reads `ZEROBOUNCE_API_KEY` from the environment.
- **Google-footprint sourcing** now defaults to **Firecrawl search**
  feeding a fetch-agnostic classifier (`audit/footprint.py`, `python
  main.py classify-footprint`) instead of Apify's google-search-scraper —
  Firecrawl is already connected and paid for in this environment, so this
  costs nothing extra.

`apify.verify_emails` / `apify.google_search` / `apify.footprint_search`
are all still fully wired, untouched — nothing was removed, only the
*default* changed. This keeps the whole free-tier monthly cap available
for the one thing with no substitute: LinkedIn and Instagram.

**Switching email verification back to Apify (once there's Apify budget
again) is a one-line env var, no code change:** set
`EMAIL_VERIFY_PROVIDER=apify` and `main.py email-verify`/`email-enrich`
go straight back to `apify.verify_emails`/MillionVerifier — see
`_email_verifier()` in `main.py`. Unset (or `zerobounce`, the default)
keeps ZeroBounce.

For Google-footprint sourcing there's no env var needed at all: `apify
footprint <platform>` and `apify search` were never touched and work
exactly as before — switching back is just telling `source-leads` to
reach for those instead of `firecrawl_search` + `classify-footprint`.

## The token

The layer reads **`APIFY_TOKEN`** (or `APIFY_API_TOKEN`) from the
environment. It lives as an **environment secret on the runner**, never in
code or the repo. Actor discovery (`apify actors <query>`) hits the public
Store and needs no token; every actor *run* does. A missing token fails
closed with a clear message (`{"error": "APIFY_TOKEN is not set …"}`,
exit 1) — never a silent skip, never a guess.

To set it: add `APIFY_TOKEN` as an environment secret on the Claude Code
environment (Settings → environment). Once set, every `apify` run command
works with no further wiring.

## The ZeroBounce key (email verification's default path)

`main.py email-verify` and `main.py email-enrich` read **`ZEROBOUNCE_API_KEY`**
from the environment (`audit/email_verifier.py`) — same rule as
`APIFY_TOKEN`: an environment secret on the runner, never in code. Sign up
at zerobounce.net for the free tier (100 verification credits/month, no
credit card, credits don't expire) — that comfortably covers this system's
real volume without touching Apify's cap. A missing key fails closed
(`EMAIL VERIFY: WARN` / `EMAIL ENRICH: HOLD` — inconclusive, never a
silent pass), same contract as a missing `APIFY_TOKEN`.

To set it: add `ZEROBOUNCE_API_KEY` as an environment secret on the Claude
Code environment (Settings → environment).

## The actor set (vetted — do not expand casually)

| Command | Actor | What it's for |
| --- | --- | --- |
| `apify li-posts <url>` | harvestapi/linkedin-profile-posts | recent LinkedIn posts (text + date, no cookies) — **where LinkedIn hooks live** |
| `apify li-profile <url>` | apimaestro/linkedin-profile-detail | headline / about / experience; `--email` mode finds an address |
| `apify ig <url>` | apify/instagram-scraper | IG recent posts w/ captions (`--mode details` for bio/followers) |
| `apify ig-post <url>` | apify/instagram-scraper | full detail on one IG post (caption + top comments) |
| `apify verify-email <addr…>` | account56/email-verifier | *manual fallback only* — default is now `main.py email-verify` (ZeroBounce, `audit/email_verifier.py`) |
| `apify search "<q>"` / `apify footprint <platform>` | apify/google-search-scraper | *manual fallback only* — default is now `main.py classify-footprint` fed by `firecrawl_search` (`audit/footprint.py`) |
| `apify actors "<q>"` | (Store search) | discover/compare actors — **no token needed** |

Only the LinkedIn and Instagram rows are the default path a skill reaches
for. `verify-email`/`search`/`footprint` still run exactly as documented
below, kept for when ZeroBounce or Firecrawl search is itself unavailable.

**`li-profile` switched vendors 2026-07-16, `li-posts` did not.** A batch
hit a hard wall mid-run on harvestapi's PROFILE actor specifically:
harvestapi's backend enforces its own ~20-runs/month quota on that actor,
separate from and invisible to Apify's own billing/limits API (`apify
limits` read 49% of the $5 USD cap at the time — the harvestapi cap is
vendor-side, not an Apify account limit). `li-profile` now runs on
**apimaestro/linkedin-profile-detail** instead — a different vendor/backend,
still pay-per-event pricing, no known run-count cap as of this writing.
`li-posts` stays on **harvestapi/linkedin-profile-posts**: that actor isn't
subject to the cap and runs roughly 2.5x cheaper per post than apimaestro's
equivalent (confirmed by comparing per-run costs in the Apify console after
a brief mis-swap of both actors together the same day) — don't move it to
apimaestro without re-confirming the cap actually applies to posts, not
just profiles.

Everything web-fetchable (podcasts, YouTube, About pages, funnel walks,
checkout probes) stays on **Firecrawl** — cheaper and already connected.
Adding actors is surface area and cost, not capability. If a new need is
genuinely web-unreachable, add it here deliberately, not by reflex.

## Check the quota once, not per lead

`python main.py apify limits` — no token cost, no actor run. Prints
current usage vs. plan limits (`GET /v2/users/me/limits`). The free/starter
tier caps on a small **monthly USD budget**
(`current.monthlyUsageUsd` / `limits.maxMonthlyUsageUsd`), not a
per-actor credit count, so a handful of LinkedIn/IG lookups across a
batch can burn through it fast — LinkedIn/Instagram are the only regular
consumers of this budget now that email verification and Google-footprint
sourcing default elsewhere (see above), so this check is really "is there
room for this batch's hook-finding." The response includes `pct_of_usd_cap`
and `near_cap` (`true` at ≥90%) for a quick read.

**batch-audit checks this once, up front**, before spawning any
lead-processor agents — if `near_cap` is true, every agent gets told to
skip Apify for the run instead of each one separately discovering an
exhausted quota by running into it (which is exactly what happened Jul
15, 2026: several agents in the same evening-prep batch each burned tool
calls hitting the same dead quota one actor call at a time). Any
solo-invoked lead-processor or hook-finder run should do the same check
first rather than assume the quota is open.

## Cost discipline (Instagram and the email-search mode are the pricey ones)

- **LinkedIn: posts-first.** `li-posts` is where a recent-post hook comes
  from. Only reach for `li-profile` when you actually need the About/career
  story and the site didn't already give it. Never both by default.
- **Instagram:** `apify ig <url> --newer-than "60 days"` with a small
  `--limit`; only `ig-post` on a specific post that looks like a hook and
  needs its full detail. Output is trimmed to useful fields by default
  (`--raw` bypasses).
- **Email:** `li-profile --email` uses the $10/1k email-search mode vs
  $4/1k plain — only pass it when actually hunting an address. Never
  re-verify an address already MX-confirmed by `main.py email-check`.
  Deliverability *confirmation* itself no longer runs here by default —
  see `main.py email-verify` (ZeroBounce, no Apify cost at all).
- **Search / footprint:** the Google-footprint channel defaults to
  `firecrawl_search` + `main.py classify-footprint` now (no Apify cost).
  `apify search` / `apify footprint <platform>` remain available — tight
  scoped queries, low `--pages` — as a manual fallback only.

## Where the machine uses it

- **`haytham-hook-finder`** — LinkedIn + Instagram hook evidence (Step 1).
  The primary consumer. Podcasts/YouTube/About stay on Firecrawl.
- **`source-leads` Google footprint channel** — worked hard, not as a
  fallback (2026-07-16), and off Apify entirely since 2026-07-17. Run TWO
  `firecrawl_search` queries per platform: the **subdomain** shape
  (`site:mykajabi.com coach Dubai`, free-tier coaches) and the
  **footer-signature** shape (`"powered by kajabi" coach Dubai`,
  un-site-scoped, which catches custom-domain coaches the subdomain query
  is blind to — that's how achievher.com, a real Dubai coach on a custom
  domain, surfaced), save both hit lists to JSON, then run `python main.py
  classify-footprint <platform> --subdomain-hits <file> --marker-hits
  <file> --geo <emirate>` (`audit/footprint.py`) to dedupe by host, drop
  the platform's own site and social posts, and tag each hit `foundVia`.
  Platforms: kajabi/teachable/thinkific/podia/systeme/kartra/skool; rotate
  `--geo` across Dubai/Abu Dhabi/Sharjah/UAE. The wider footer-signature
  net needs UAE + solo confirmation before logging. `apify footprint
  <platform>` (the original Apify-fetched path) remains a fallback if
  Firecrawl search is itself unavailable.
- **`email-check` WARN → verify** — when `main.py email-check` returns WARN
  (unverifiable MX / role account), `main.py email-verify <addr>`
  (ZeroBounce) is the confirm step before the address enters the CRM or a
  send queue. `apify verify-email <addr>` remains a manual fallback.
- **No-email leads** — find-then-verify: `apify search` /
  `apify li-profile --email` to surface a founder-direct address, then
  `main.py email-verify` to confirm it before it's logged. Verification
  only *checks* an address; it does not *find* one.
- **No-email leads, nominative fallback** — when nothing surfaces above,
  `python main.py email-enrich "<name>" <Site URL>` derives name-based
  candidates against the lead's OWN branded domain (jane@, jane.doe@, jdoe@…)
  and verifies them all in ONE batched ZeroBounce call, adopting at most
  one deliverable address. It never guesses on a free-provider domain
  (gmail/outlook/…), and never auto-adopts on a catch-all domain (every guess
  returns `catch_all`/`catch-all` → WARN → HOLD, so no specific mailbox is
  confirmable). A `PASS` line is by construction an `EMAIL VERIFY: PASS` on
  the adopted address. See `audit/email_enrich.py`, `audit/email_verifier.py`.

## Examples

```
# LinkedIn recent posts for a hook (posts-first)
python main.py apify li-posts "https://ae.linkedin.com/in/anacaragea" --max 5

# LinkedIn About/career story, only if posts were thin
python main.py apify li-profile "https://ae.linkedin.com/in/douglambert..."

# Find an address for a no-email lead, then confirm it (ZeroBounce, no Apify cost)
python main.py apify li-profile "<profile url>" --email
python main.py email-verify "found@lead.com"

# No address surfaced anywhere → nominative fallback (name + own domain)
python main.py email-enrich "Jane Doe" "https://janedoe.com"

# IG recent posts with captions, last 60 days
python main.py apify ig "https://www.instagram.com/<handle>/" --newer-than "60 days"

# Compare actors for a new need (no token needed)
python main.py apify actors "instagram profile scraper"

# Google-footprint sourcing (Firecrawl-fed, no Apify cost) — after saving
# firecrawl_search results for both shapes to JSON files:
python main.py classify-footprint kajabi --subdomain-hits sub.json \
    --marker-hits marker.json --geo Dubai
```
