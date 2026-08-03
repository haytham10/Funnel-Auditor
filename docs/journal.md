## 2026-08-03 (the address decline) — spend the half cent early, save the agent passes

Haytham, on the SERP rung's cost: I did not mean Apify alone, I meant cost in
general, and what hurt yesterday was the token cost on the two batches.

He is right and the ratio is not close. Measured, `q2`+`q3`: **410.3M tokens
against $1.13 of Apify.** At this session's own blended rate that is roughly
$445 of tokens, so **Apify is about 0.25% of the bill** and every actor
decision in this repo has been an argument about a rounding error. Per shipped
email: ~18.6M tokens, ~$0.014 of Apify.

Two changes, and only the second one matters.

### The AI Overview is off by default

It nearly doubled the per-query price for the `ABSENT` verdict, which the
previous entry measured wrong on two of five leads whose addresses were live on
their own homepages. Measured back to back on the same five leads: **$0.0235
with it, $0.0135 without.** The arithmetic is exact — five pages plus one start
fee, no `ai-overview-scraped` event.

**And the Overview text still comes back free.** The $0.002 buys a specialized
proxy that raises the *probability* of capturing one, not the capture itself. So
`ABSENT` still fires opportunistically at no charge, which is strictly better
than the flag implied in either direction. `--ai-overview` remains for a single
lead where an absence is the actual question.

### `plan --addresses`: the second decline rule

`email-find --out` writes a per-lead verdict; `plan --addresses` reads it and
**declines every paid rung for a lead nothing can be sent to**, keeping every
free one. `email-find` moves out of the late fallback slot and runs at stage
1bb, right after dedupe.

The machine ends at a file of email addresses. A lead with no address produces
no row however good its hook is — and today that is discovered *after* research,
hook, verify and draft have each burned a pass on them. Half a cent spent before
research to avoid one wasted drafting chain pays for itself about four thousand
times.

**It is a measurement, never a prediction.** `reachable: false` means every
cheap path already looked and found nothing: no address on the row, none
harvested from their site, none published anywhere searched. It is emphatically
not the AI Overview's opinion, which is the thing measured unreliable. And it
gates spend and never inclusion — the lead is still researched, still planned,
still holds a row, exactly as D21 requires.

**The report counts the two rules apart**, and that was not cosmetic: the first
live run declined eight steps, seven of them on address, and a single total
reported all eight as ownership declines. Opposite diagnosis, opposite fix.
`ADDRESS_DECLINE` is a constant because one substring of a reason string is now
load-bearing.

### Two bugs the live runs found, both in prose parsing

The AI Overview writes addresses into running text with no separator, and the
address regex reads whatever follows as more domain. `jendemel@icloud.com.If
you...` became `...com.if`, a real-looking address on Iceland's TLD that goes to
the verifier and returns a hard bounce. Fixed by dropping a trailing Title-Case
label — and then **the second shape shipped live for one run anyway**:
`jendemel@icloud.comLocation`, glued straight onto the TLD with no dot at all,
which needs a cut at a lowercase-to-uppercase boundary *inside* the label.
Neither rule alone covers both, and `SITE.COM` must survive both.

### Still unsettled, and it is the thing to measure next

The SERP is not deterministic and the yield swings on query wording. The
hand-written queries found four addresses in five; the auto-built ones have
returned between zero and two across four runs of the same command, and the last
run found nothing for anybody. `email-find`'s FOUND rate remains unknown, and
until it is known **the address decline is only as good as the search under
it** — which is an argument for running it over a real slice and counting, not
for trusting five leads twice.

