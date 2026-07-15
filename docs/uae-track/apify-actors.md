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

## The actor set (vetted — do not expand casually)

| Command | Actor | What it's for |
| --- | --- | --- |
| `apify li-posts <url>` | harvestapi/linkedin-profile-posts | recent LinkedIn posts (text + date, no cookies) — **where LinkedIn hooks live** |
| `apify li-profile <url>` | harvestapi/linkedin-profile-scraper | headline / about / experience; `--email` mode finds an address |
| `apify ig <url>` | apify/instagram-scraper | IG recent posts w/ captions (`--mode details` for bio/followers) |
| `apify ig-post <url>` | apify/instagram-scraper | full detail on one IG post (caption + top comments) |
| `apify verify-email <addr…>` | account56/email-verifier | confirm an address before it enters the CRM |
| `apify search "<q>"` | apify/google-search-scraper | Google SERP (`--site`, `--country`, `--pages`) |
| `apify actors "<q>"` | (Store search) | discover/compare actors — **no token needed** |

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
batch can burn through it fast. The response includes `pct_of_usd_cap`
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
- **Search:** tight scoped queries, low `--pages`.

## Where the machine uses it

- **`haytham-hook-finder`** — LinkedIn + Instagram hook evidence (Step 1).
  The primary consumer. Podcasts/YouTube/About stay on Firecrawl.
- **`email-check` WARN → verify** — when `main.py email-check` returns WARN
  (unverifiable MX / role account), `apify verify-email <addr>` is the
  confirm step before the address enters the CRM or a send queue.
- **No-email leads** — find-then-verify: `apify search` /
  `apify li-profile --email` to surface a founder-direct address, then
  `apify verify-email` to confirm it before it's logged. `email-verifier`
  only *checks* an address; it does not *find* one.

## Examples

```
# LinkedIn recent posts for a hook (posts-first)
python main.py apify li-posts "https://ae.linkedin.com/in/anacaragea" --max 5

# LinkedIn About/career story, only if posts were thin
python main.py apify li-profile "https://ae.linkedin.com/in/douglambert..."

# Find an address for a no-email lead, then confirm it
python main.py apify li-profile "<profile url>" --email
python main.py apify verify-email "found@lead.com"

# IG recent posts with captions, last 60 days
python main.py apify ig "https://www.instagram.com/<handle>/" --newer-than "60 days"

# Compare actors for a new need (no token needed)
python main.py apify actors "instagram profile scraper"
```
