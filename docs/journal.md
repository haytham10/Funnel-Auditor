## 2026-08-07 (pivot) — the org-buyer proposal, and four measurements

Discovery session for the repositioning. Output is a proposal,
`docs/proposals/2026-08-07-org-buyer-pivot.md`, and nothing else — no module,
test or gate moved. A later session turns it into a phased plan.

The shape it argues for: subject and hook dynamic, the whole body static and
hand-written once. That retires `deal`, the `anchors` per-lead draw, the 70/30
exact-match ratio, the repetition caps, `--rebalance-ps`, `copy-usage`, the
Copy Assets bank, and **the entire drafting stage**. `draft-verifier` survives,
rescoped to one question asked against the assembled message.

**Four things were measured rather than assumed, all off data already in
`data/runs/`.** They are the reason the proposal disagrees with the brief in
three places.

- **`sells_to` clears the bar for a fourth floor.** Across 114 real ICF leads:
  25% corporates, 27% individuals, 47% blank. The price floor was retired for
  reading `unclear` on ~94% of the market; 47% is a different animal. But with
  `unclear` passing per D4, ~72% of a list still passes — **it is a negative
  filter, not a targeting mechanism**, and the proposal says so before a batch
  report does.
- **The 12–25 word hook is feasible.** 2,024 sentences across 100 leads'
  shortlists: 52% are 8–19 words, and **94 of 100 leads carry at least one**
  quotable contiguous sentence that fits. The template file's own warning that
  `null_hook_rate` will rise is probably overstated.
- **`WORD_MAX = 95` is now the tightest gate in the machine and it is an
  inherited number**, measured on a five-beat email that no longer exists. At 70
  static words every word above 70 is hook budget. The proposal asks for 105,
  which moves usable sentences from 52% to 69%, and notes that this is the
  cheapest lever on `null_hook_rate` there is — one constant, no agent pass.
- **Four captured fields are dead weight.** `top_program_price_aed` 1.8%
  populated, `runs_certification` 3.5%, `solo` 16%, `audience_size` swinging
  four-fold between two runs of the same source list. No reader for any of them.

Two corrections worth carrying forward. **`outbound/anchors.py` cannot simply be
deleted** — it also owns the fact table and the claim grammar that `lint`,
`export` and `copy_sync` import, which is D11's only enforcement; the extraction
has to come first. And **`lint` does not mostly retire, it splits**: a one-time
check on the template keeps every static-body rule at zero per-email cost, while
a thin per-email lint keeps the handful the hook and subject can break. Two batch
checks have to be *deleted* rather than left, because one template makes them
fire permanently.

The cost target is the part the proposal refuses to oversell. icf1 measured
13.05M tokens per shipped email against a 5M target, with **63.8% of it the
orchestrator** — a bucket that stage deletion only touches indirectly. A
defensible floor is 6–9M, and getting under 5M needs the worker-writes-a-file
protocol `CLAUDE.md` already mandates and icf1 did not hold.

Campaign 1 runs on the executive/leadership slice of the ICF lists already on
disk: 61 leads, 50 after the fourth floor, **39 after the wall**, all reachable.
Sourcing is phase 4 and campaign 2 is the first one the machine sources itself.

Decision numbers above D34 cited in the brief are not real entries — they came
from a summary that renumbered from D34. The log still tops out at D34.

## 2026-08-07 (pivot) — clearing the ground for a repositioning

The `pivot` branch exists to plan a repositioning of the machine. The target
market is narrowing from the general population of UAE coaches to UAE-based
executive and leadership coaches who sell to organizations rather than
individuals — a segment the ICP has captured in `sells_to` and `coach_type`
without ever gating on it. Nothing about what the machine does has changed
yet; this branch is where that gets decided.

All ICF and Instagram batch work is paused pending the pivot plan. The
context that kept every new session opening onto icf1, ig237 and the rest —
prior journal history, the two long retrospectives, and the batch skill's
icf1/ig237-specific playbook — has been cleared or archived so planning
starts from the target market instead of the last batch. No module, test or
gate moved; all of it is recoverable from `outbound` if the plan calls for it.
