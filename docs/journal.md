## 2026-08-03 (email-find) — the SERP actor comes back, for a job that did not exist

Haytham: you never use `apify/google-search-scraper`, it is cheap, it has an AI
Overview add-on that usually gives a definitive result on whether an address
exists, go look at pricing, input and output and find a way to include it.

A SERP actor was retired 2026-08-01 for duplicating the agent's own free
WebSearch. That retirement was about **sourcing**, where `audit/footprint.py`
still says the free path does the work, and none of that is restored. This is
**address retrieval**, which was not a stage then, and the previous entry
measured the free path failing at it: the agent's WebSearch is US-geo'd with no
country control, returns a summariser's paraphrase instead of results, and
answered three of five UAE-coach queries with the wrong person.

### What it costs

**Pay per event, not per compute-second**, which quietly inverts this repo's
batching rule. BRONZE: `actor-start` $0.001 once per run, `search-page-scraped`
$0.0025 per page, `ai-overview-scraped` $0.002 per query. Batching saves the
start fee and nothing else — still worth doing, but the container-boot economics
that dominate for the Instagram and LinkedIn actors do not apply here and
`audit/apify.py` said the opposite in a docstring above the map.

Measured on the first probe: **$0.0235 for 5 leads, $0.0047 each.** The 73
actionable rows of the current list would be $0.34.

The actor also prices `lead-scraped` ($0.005, returns a work email, phone, title
and LinkedIn from a found domain) and `lead-email-verified` ($0.004, and **not
charged on catch-all, unknown or error** — which is most of this market).
Deliberately NOT wired: Haytham chose the SERP half only, and those two overlap
`email-enrich` and the `email` verifier that already exist.

### What shipped

`serp` in `ACTORS`, `apify.google_search` as the fetch, and
**`audit/email_find.py`** for everything done with the results. The module
fetches nothing, which is `footprint.py`'s property and the reason its own fetch
layer could be retired as a deletion rather than a rewrite. `main.py email-find`
takes `--leads` and batches every query into one run, correlating on the query
text rather than position because the actor returns records in an order matching
nothing.

**An organic result is a citation; an AI Overview is a claim.** FOUND carries a
re-fetchable URL. CLAIMED means only the overview said so — confirm on its cited
page or drop, never adopt. That verdict exists because the first probe produced
`support@fitbridge.ae` for a lead, attributed to a page that says `info@`, for a
mailbox that does not exist. `email-verify` caught it as a hard bounce.

### Three revisions of one rule, each paid for by a live false positive

1. **No corroboration at all.** The first live run reported FOUND on four of
   five leads, every one a stranger's address: an Egyptian pharmaceutical
   panel, a fitness LLC on another continent, a Dubai clinic's appointments
   desk, and a different man named Spencer. Each was the only address on its
   page, so ranking floated it to the top of the one verdict a caller acts on.
2. **"The page names them in full."** Re-admitted `andrea@fitqtllc.org` off an
   Instagram reel that genuinely is about Jeff Maingi. A page being about
   somebody corroborates the PAGE, never an address printed on it —
   collaborators, sponsors and commenters all leave addresses on a person's own
   page.
3. **The page must also be that address's own organisation's page.** How
   `info@whiteantlergroup.com` qualifies — cited on a page titled "White Antler
   Group LLC" whose snippet reads "Click here to view Sandra Spencer's profile"
   — at a moment when that domain was not yet known to be hers. All seven known
   cases now sort correctly, 3 kept and 4 dropped.

Uncorroborated addresses are counted in the report and kept out of the candidate
list. A dropped address must stay visible: the filter is a heuristic and the
count is the only way anybody notices it going wrong.

Also fixed: `jendemel@icloud.com.If` — AI Overview prose runs sentences together
and the address regex read `.If` as Iceland's TLD, producing a real-looking
address that goes to the verifier and returns a hard bounce. A trailing label in
Title Case is the tell, and it is clean: real TLDs are all-lower or all-upper.

### Two things measured that argue against trusting this stage yet

**ABSENT is not reliable, and that is the opposite of what it was added for.**
Lana Ave came back ABSENT on two separate runs — "not listed in public
registries or her verified social media profiles" — while `lana@lanawl.com` sits
on the homepage of `lanawl.com`. Sandra Spencer came back ABSENT once with
`info@whiteantlergroup.com` live on a LinkedIn company page. The verdict is
advisory and gates spend rather than inclusion, so a false one costs an address
and never a lead, but **it should not be believed at anything like the rate its
wording implies.**

**The SERP is not deterministic and query wording decides the yield.** The
hand-written queries on the first probe found four addresses. Auto-built queries
over the same five leads found zero to two, varying between runs of the same
command. Adding the lead's known domain to the query is the single biggest
lever — a coach's address is indexed beside their business name far more often
than beside their positioning line — and it is exactly what an Instagram-list
row does not carry.

So the stage is real and the cost is trivial, and **the FOUND rate is unknown**.
The next thing worth doing is running it over a proper slice and counting, not
believing this entry's five.

