"""Which rungs are populated for this lead, what each would cost, and which
paid ones we would decline.

This is F6 of docs/proposals/2026-08-01-hook-retrieval.md. Where to look for a
hook has never been a code path, a config or a data structure. It is prose, in
`docs/hook-rules.md` and again in `.claude/agents/hook-worker.md`, kept in
agreement by hand — and the agreement has already failed twice, both times
recorded in the file it failed in:

- the **paid** rung sat at #1 under a heading that said "in cost order", which is
  how a batch reaches for LinkedIn before reading an About page already on disk;
- one stage carried **four** recency windows — 30 days in the code, "about 90
  days" in the rules, `--since month` in one agent file, `--newer-than "60 days"`
  in another.

Both are the same failure: a value that four readers may copy has no owner. So
`LADDER` below is the ladder, once, as data. The prose keeps the reasons and
names this module, which is `docs/spec/00-index.md`'s rule applied to the file
that most needed it.

Three consequences fall out of having it typed rather than written down:

- **It becomes per-lead.** Today nothing tells a hook-worker which rungs are even
  populated for its lead; `fetch` prints an `IG` line and that is the entire
  routing layer. A `LeadPlan` says which of the four rungs this particular
  person actually has, before anybody opens a context to go looking.
- **It becomes priced.** The batch budget is currently a *sentence* passed into a
  prompt. Here it is an estimate per step, from the same live lookup the cost
  gate uses.
- **It becomes countable.** Three leads on the first batch walked the full ladder
  and returned nothing. That is the correct answer and it cost three full agent
  passes; nothing knew it had happened.

## It declines nothing, and that is the decision

`resolve` established that an ownership verdict may gate a *purchase* where it
may not gate a *kill* (D21). It did not establish that this verdict predicts
this waste. Nobody has measured whether the leads with no confirmed channel are
the leads that produce no hook — `data/runs/` has never recorded a `li_posts`
fetch at all. If they are the same leads, declining is free. If they are not,
`plan` should not gate on ownership at all, and that is much better learned
before it is built.

So a step whose channel is `absent` gets `decision="decline"` and is **taken
anyway**, because nothing reads this file. Shipping the gate and the measurement
in one commit would have the gate generate the data that judges it.

This needs no decision of its own: D21 already states the posture and already
carries the reversal condition — *"a batch where declining to spend on
low-confidence channels costs more verified hooks than it saves scrapes"*. This
module is the apparatus that measures it, not a new position.

`unknown` is never declined. It means no tell was available, not that the tell
said no, and treating the two alike is the false-negative surface R3 names.

## What it costs to run

Nothing. It fetches no page and runs no actor. The only network call it can make
is the price lookup, which is a read of an actor's public pricing block, and
that **fails open** — an unreadable price yields `est_cost_usd=None`, which is
also what a genuinely compute-billed actor looks like. A stage that spends
nothing must never be able to fail because the billing API was down.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from outbound.observe import PLATFORMS
from outbound.resolve import CONFIDENCE, _default_of

# What a paid rung is assumed to fetch per lead, and therefore what the estimate
# is per lead. `li-posts --max 5` is what both agent files actually pass today.
POSTS_PER_LEAD = 5

# A step is taken unless something says otherwise. `decline` is advisory in the
# strict sense: it is written down and nothing acts on it.
DECISIONS = ("take", "decline")

# The `cost_note` of a paid step nobody asked to price. Distinct from the cost
# gate's own "cannot be priced" reasons, which mean the lookup happened and the
# answer was that there is no per-item price to read.
NOT_PRICED = "not priced — pass --price for a live lookup"


@dataclass(frozen=True)
class Rung:
    """One place a hook can come from, and what reaching it costs.

    Frozen because this is a definition, not a record. A caller that wants a
    different ladder passes one; it does not edit this one in place.
    """

    name: str
    platforms: tuple = ()        # values from observe.PLATFORMS
    actor_key: str = ""          # "" means free; else a key in audit.apify.ACTORS
    kinds: tuple = ()            # the observe.KINDS this rung can produce
    batched: bool = False        # can one actor run serve several leads?
    note: str = ""
    # Flags a call on this rung MUST carry, and the reason this field exists at
    # all. `research-worker` ran `apify li-posts --max 5` with no window while
    # `hook-worker` ran `--since 3months`, so two calls asked one profile two
    # different questions and the hook stage kept "discovering" posts research
    # had simply not requested — 4 of the 5 UNOBSERVED in `2026-08-01-q1`, the
    # number the whole retrieve-once decision is gated on. `doc-check` asserts
    # every doc that names this rung's command carries these.
    flags: tuple = ()
    # How to recognise an invocation of this rung in prose. First element is the
    # subcommand, which only counts when an argument follows it — a doc naming
    # `apify li-posts` to say what it is has recited no flags and needs none.
    # The rest disambiguate, because one subcommand can serve two rungs: `apify
    # ig --mode details` is a bio read for the floors and `--mode posts` is hook
    # material, the same command asking different questions.
    command: tuple = ()

    @property
    def paid(self) -> bool:
        return bool(self.actor_key)


# The ladder, in actual cost order, and this list is the authority on it.
#
# `about` yielded only `framework` until 2026-08-01. That was F5's narrowing,
# and batch `2026-08-01-q1` refuted it: all three of the ranker's MISSED leads
# were `kind: about` observations an independent verifier had VERIFIED, and the
# ban excluding them accounted for 21 of the corpus's 32 rejections. What the
# verifier refuses is the GENERIC, not the location — and a solo coach's own
# About page is where the most specific thing they will ever publish lives.
# `outbound/select.py` ranks `about` last and bans repeated text instead, which
# is the same test settled on evidence rather than on where a page was found.
#
# Neither paid rung is batchable, and the two facts are not equally strong.
LADDER = (
    Rung("about", ("site",), kinds=("framework", "about"),
         note="already read free at tier 0 — nothing to buy. Ranked last, never "
              "declined: the hero section is generic, the founding story is not, "
              "and only reading them tells you which this one is"),
    Rung("podcast", ("podcast", "youtube"), kinds=("episode", "video"),
         note="free: web search for their name plus 'podcast', then fetch the "
              "episode page. The rung that reaches the coaches who do not post"),
    Rung("li_posts", ("linkedin",), actor_key="li_posts", kinds=("post",),
         command=("apify li-posts",), flags=("--max 5", "--since 3months"),
         note="the richest source by a distance, and the most expensive call in "
              "the machine: maxPosts is a run-wide budget, PROVEN by direct "
              "test, so it is one container boot per lead"),
    Rung("ig_posts", ("instagram",), actor_key="ig_post", kinds=("post",),
         command=("apify ig", "--mode posts"),
         flags=('--newer-than "90 days"',),
         note="a real rung, not a last resort — for a coach whose whole presence "
              "is Instagram it is the only one. Batching UNTESTED, assumed to "
              "share li_posts' flaw"),
)

# The window in those flags is `select.HOOK_RECENCY_DAYS`, in each actor's own
# spelling: `3months` is the only value in `audit/apify.py`'s LI_POSTED_LIMITS
# that reaches 90 days, and `--newer-than` takes the number in words. A test
# pins both against that constant so the spellings cannot outlive it.


@dataclass
class Step:
    """One rung, for one lead, with the verdict we would spend against."""

    lead_key: str = ""
    rung: str = ""
    platform: str = ""
    url: str = ""
    actor_key: str = ""              # "" = free
    est_cost_usd: float | None = 0.0  # None = not priced OR unpriceable
    # Why the estimate is what it is, kept apart from `reason` on purpose.
    # "nobody asked for a price" and "this actor cannot be priced" are different
    # answers, and the first version of this sniffed them out of the decision
    # string — which lost the pricing note the moment a step was declined.
    cost_note: str = ""
    confidence: str = "unknown"      # carried off the Channel, never re-derived
    decision: str = "take"           # take | decline — ADVISORY, nothing reads it
    reason: str = ""

    @property
    def paid(self) -> bool:
        return bool(self.actor_key)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            # `est_cost_usd` is the one field where None is a real value, not a
            # missing one: unpriceable is an answer. Coercing it to the default
            # would turn "we could not price this" into "this is free".
            if value is None and key != "est_cost_usd":
                value = _default_of(known[key])
            fields[key] = value
        return cls(**fields)


@dataclass
class LeadPlan:
    """Every rung this lead has, whether or not we would walk it."""

    lead_key: str = ""
    name: str = ""
    steps: list[Step] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LeadPlan":
        known = cls.__dataclass_fields__
        fields = {}
        for key, value in data.items():
            if key not in known:
                continue
            if value is None:
                value = _default_of(known[key])
            fields[key] = value
        steps = fields.pop("steps", None) or []
        lead_plan = cls(**fields)
        lead_plan.steps = [s if isinstance(s, Step) else Step.from_dict(s)
                           for s in steps if isinstance(s, (dict, Step))]
        return lead_plan

    @property
    def paid_steps(self) -> list[Step]:
        return [s for s in self.steps if s.paid]

    @property
    def would_decline(self) -> list[Step]:
        return [s for s in self.steps if s.decision == "decline"]

    @property
    def has_rung(self) -> bool:
        """Is there anywhere at all to look? A lead with no rung is the answer
        that used to cost a full agent pass to reach."""
        return bool(self.steps)


# ------------------------------------------------------------------- pricing


def apify_price(actor_key: str, item_count: int) -> tuple[float | None, str]:
    """The live per-run estimate for a rung, or `(None, reason)`.

    **Fails open, always.** Pricing needs a token, and this stage spends nothing
    — a batch that cannot reach the billing API must still get its plan. That is
    `_require_cost_approval`'s own rule about not failing a call on the
    accounting rather than on the work, one stage earlier, and `ledger`'s rule
    about an observer that can halt what it observes.
    """
    try:
        from audit.apify import ACTORS, estimate_cost_usd

        actor_id = ACTORS.get(actor_key)
        if not actor_id:
            return None, f"{actor_key} is not an actor this machine has"
        return estimate_cost_usd(actor_id, item_count)
    except Exception as exc:                      # noqa: BLE001 — see docstring
        return None, f"price unavailable ({type(exc).__name__})"


def budget_note() -> tuple[dict | None, str]:
    """The batch's Apify cap, read once, or `(None, why not)`.

    Deliberately the same posture as `main._apify_quota_note`: the cap is worth
    printing and is never worth blocking on.
    """
    try:
        from audit.apify import account_limits

        return account_limits(), ""
    except Exception as exc:                      # noqa: BLE001 — fails open
        return None, f"Apify cap unreadable ({type(exc).__name__})"


def remaining_usd(budget: dict | None) -> float | None:
    """What is left of the monthly USD cap, or None if it cannot be worked out.

    `account_limits()` reports a percentage and a `near_cap` flag but no
    remainder, so the subtraction lives here rather than being done twice by two
    readers with two opinions about which key means what.
    """
    if not budget:
        return None
    cap = (budget.get("limits") or {}).get("maxMonthlyUsageUsd")
    used = (budget.get("current") or {}).get("monthlyUsageUsd")
    if cap is None or used is None:
        return None
    try:
        return round(max(0.0, float(cap) - float(used)), 4)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------- planning


def _rung_for(platform: str, ladder: tuple = LADDER) -> Rung | None:
    """The first rung that serves this platform. First, not best: the ladder is
    ordered by cost, so the earliest match is the cheapest way to reach it."""
    for rung in ladder:
        if platform in rung.platforms:
            return rung
    return None


def plan_lead(identity, *, site_url: str = "", ladder: tuple = LADDER,
              price=None) -> LeadPlan:
    """One lead's rungs, priced, with the declines written down and not made.

    `price` is injected rather than imported so a test never touches the network
    and so a caller can plan without a token — the same reason `resolve_lead`
    takes its fetcher by injection. `None` means do not price, which is not the
    same as free: the estimate comes back `None` and says so.
    """
    lead_plan = LeadPlan(lead_key=getattr(identity, "lead_key", "") or "",
                         name=getattr(identity, "name", "") or "")

    # The site rung is not a channel — nothing harvests a lead's own homepage
    # into its own channel list — so it is passed in when the caller has it.
    if site_url:
        rung = _rung_for("site", ladder)
        if rung is not None:
            lead_plan.steps.append(Step(
                lead_key=lead_plan.lead_key, rung=rung.name, platform="site",
                url=site_url, est_cost_usd=0.0,
                confidence=getattr(identity, "owner_verdict", "unknown") or "unknown",
                reason=rung.note))

    for channel in (getattr(identity, "channels", None) or []):
        rung = _rung_for(channel.platform, ladder)
        if rung is None:
            continue

        est: float | None = 0.0
        cost_note = ""
        if rung.paid:
            if price is None:
                est, cost_note = None, NOT_PRICED
            else:
                est, cost_note = price(rung.actor_key, POSTS_PER_LEAD)

        # The whole of the decline rule, and it is one word long. `absent` is
        # the only verdict that means a tell was available and said no; every
        # `unknown` is a channel we simply cannot judge, and declining those
        # would be the false-negative surface R3 names.
        decision, reason = "take", rung.note
        if rung.paid and channel.confidence == "absent":
            decision = "decline"
            reason = (f"would decline: {channel.evidence or 'ownership absent'} "
                      f"(ADVISORY — taken anyway)")

        lead_plan.steps.append(Step(
            lead_key=lead_plan.lead_key, rung=rung.name,
            platform=channel.platform, url=channel.url,
            actor_key=rung.actor_key, est_cost_usd=est, cost_note=cost_note,
            confidence=channel.confidence, decision=decision, reason=reason))

    if not lead_plan.steps:
        # Not "unreachable". Rung 2 is a web search for their name, which needs
        # no channel and no URL — so it is available to every lead and there is
        # nothing to name here. Saying "no rung" without that clause would read
        # as a lead to skip, which is the inclusion gate D21 forbids.
        lead_plan.notes.append(
            "no rung names a page for this lead — free retrieval found no "
            "channel and no site. The podcast rung is still open as a blind "
            "web search; every other rung needs a URL nobody has")
    return lead_plan


def plan_all(identities: list, *, sites: dict | None = None,
             ladder: tuple = LADDER, price=None, budget: dict | None = None) -> dict:
    """Every lead's plan, plus the batch report.

    **Every lead gets one**, including a lead with no rung at all and a lead
    whose every paid rung would be declined. A plan is a description, not a gate
    — the same guarantee `resolve_all` makes one stage earlier.

    `sites` maps `fetch.lead_key` to a site URL, which is the one thing an
    Identity does not carry.
    """
    sites = sites or {}
    plans = [plan_lead(identity,
                       site_url=sites.get(getattr(identity, "lead_key", ""), ""),
                       ladder=ladder, price=price)
             for identity in identities]
    return {"plans": plans, "report": report(plans, budget=budget)}


# ------------------------------------------------------------------- the gate


def validate(lead_plan: LeadPlan) -> list[str]:
    """Schema violations. An empty list means the record is a real one.

    The rule worth naming is the last one: a `decline` with no reason is
    `research`'s rule — a hard verdict naming no source was reasoned rather than
    checked — applied to a purchase. A decline is a claim about a lead, and the
    whole reason this stage exists is that the claim gets read later.
    """
    problems: list[str] = []

    if not lead_plan.lead_key.strip():
        problems.append("no lead_key — without it nothing joins this plan to a "
                        "lead, an identity or a ledger line")

    rung_names = {rung.name for rung in LADDER}
    seen: set[tuple[str, str]] = set()
    for index, step in enumerate(lead_plan.steps):
        where = f"step[{index}]"
        if step.rung not in rung_names:
            problems.append(f"{where} rung={step.rung!r} is not one of "
                            f"{tuple(sorted(rung_names))}")
        if step.platform not in PLATFORMS:
            problems.append(f"{where} platform={step.platform!r} is not one of "
                            f"{PLATFORMS}")
        if step.confidence not in CONFIDENCE:
            problems.append(f"{where} confidence={step.confidence!r} is not one "
                            f"of {CONFIDENCE}")
        if step.decision not in DECISIONS:
            problems.append(f"{where} decision={step.decision!r} is not one of "
                            f"{DECISIONS}")
        if not step.url.strip():
            problems.append(f"{where} has no url — a step names the page it "
                            f"would read")
        elif (step.rung, step.url) in seen:
            problems.append(f"{where} repeats {step.rung} on {step.url} — one "
                            f"step per rung per page, or the estimate "
                            f"double-counts a container boot")
        seen.add((step.rung, step.url))

        if step.actor_key:
            from audit.apify import ACTORS

            if step.actor_key not in ACTORS:
                problems.append(f"{where} names apify:{step.actor_key}, which "
                                f"is not an actor this machine has")
        if step.est_cost_usd is not None and step.est_cost_usd < 0:
            problems.append(f"{where} est_cost_usd must be non-negative or None")
        if step.decision == "decline" and not step.reason.strip():
            problems.append(f"{where} declines with no reason — a verdict that "
                            f"names nothing was reasoned, not checked")
    return problems


def validate_all(plans: list[LeadPlan]) -> list[str]:
    """Every plan's problems, each prefixed with which one it was."""
    problems = []
    for index, lead_plan in enumerate(plans):
        for problem in validate(lead_plan):
            problems.append(f"plan[{index}] {problem}")
    return problems


def load(data) -> list[LeadPlan]:
    """One plan or a list of them, as `resolve` accepts one identity or many."""
    rows = data if isinstance(data, list) else [data]
    if isinstance(data, dict) and "plans" in data:
        rows = data["plans"]
    return [LeadPlan.from_dict(row) for row in rows if isinstance(row, dict)]


def schema_help() -> str:
    """The field list, generated from the dataclasses rather than written down."""
    from dataclasses import fields as dataclass_fields

    rows = [f"    {f.name:20} {getattr(f.type, '__name__', str(f.type))}"
            for f in dataclass_fields(LeadPlan)]
    step_rows = [f"      {f.name:18} {getattr(f.type, '__name__', str(f.type))}"
                 for f in dataclass_fields(Step)]
    return ("  plans, one per lead:\n" + "\n".join(rows)
            + "\n    each step:\n" + "\n".join(step_rows)
            + f"\n  rung is one of {tuple(r.name for r in LADDER)}, in cost order\n"
              f"  platform is one of {PLATFORMS}\n"
              f"  decision is one of {DECISIONS}\n"
              "  a decline needs a reason, and is ADVISORY — nothing acts on it.\n"
              "  est_cost_usd of None means unpriceable, which is not the same "
              "as free.")


def _estimate_line(paid: list, priced: list, not_priced: list,
                   unpriceable: int) -> str:
    """The cost line, which must never print a number nobody computed.

    A batch where every lookup failed and a batch that is genuinely free produce
    the same `sum([])`. Printing `$0.0000` for the first is the accounting
    equivalent of a missing ledger reading as a zero-cost run, and that
    asymmetry is the one thing `ledger` was built to refuse.
    """
    if not paid:
        return "  no paid step in this batch — every rung is free"
    if not priced:
        why = "not priced — pass --price for a live lookup" \
            if len(not_priced) == len(paid) else "no price could be read"
        return f"  {len(paid)} paid step(s), NO ESTIMATE: {why}"
    return (f"  est ${sum(priced):.4f} over {len(priced)} priced step(s)"
            + (f", {len(not_priced)} not priced" if not_priced else "")
            + (f", {unpriceable} unpriceable" if unpriceable else ""))


def report(plans: list[LeadPlan], *, budget: dict | None = None) -> str:
    """The quotable summary, in the shape `resolve.report` already uses."""
    problems = validate_all(plans)
    head = "VALID" if not problems else f"INVALID ({len(problems)})"
    steps = [s for p in plans for s in p.steps]
    paid = [s for s in steps if s.paid]
    declines = [s for s in steps if s.decision == "decline"]
    nowhere = [p for p in plans if not p.has_rung]

    by_platform: dict[str, int] = {}
    for step in declines:
        by_platform[step.platform] = by_platform.get(step.platform, 0) + 1
    breakdown = ", ".join(f"{n} {platform}" for platform, n
                          in sorted(by_platform.items())) or "none"

    priced = [s.est_cost_usd for s in paid if s.est_cost_usd is not None]
    # "We did not look" and "this genuinely cannot be priced" are different
    # answers, and the cost gate already keeps them apart — a compute-billed
    # actor returns None with a reason saying retrying will not help. Collapsing
    # them here would report a batch nobody priced as a batch that costs $0.
    not_priced = [s for s in paid if s.est_cost_usd is None
                  and s.cost_note == NOT_PRICED]
    unpriceable = len(paid) - len(priced) - len(not_priced)

    # The decline count leads and the dollar figure does not, for the same
    # reason `resolve.report` was reordered on 2026-08-01: at $0.009/lead the
    # money is a rounding error, and the number that discriminates is the one
    # the next batch correlates against a null hook.
    lines = [
        f"PLAN: {head}, {len(plans)} lead(s), {len(steps)} step(s) — "
        f"{len(steps) - len(paid)} free, {len(paid)} paid",
        f"  would decline {len(declines)} paid step(s) on ownership: {breakdown}",
        _estimate_line(paid, priced, not_priced, unpriceable),
    ]
    per_lead = sum(1 for s in paid if s.rung == "li_posts")
    if per_lead:
        lines.append(f"  {per_lead} li_posts step(s) are one container boot "
                     f"each — the one actor that provably cannot be batched")
    if budget is not None:
        left = remaining_usd(budget)
        cap = f"${left:.2f} left of the monthly cap" if left is not None \
            else "monthly cap unreadable"
        flag = " NEAR CAP" if budget.get("near_cap") else ""
        lines.append(f"  {cap}{flag}")
    for lead_plan in nowhere:
        lines.append(f"  NO RUNG  {lead_plan.name or '(no name)'} — nowhere to "
                     f"look for a hook")
    for problem in problems:
        lines.append(f"  SCHEMA  {problem}")
    if problems:
        lines.append(schema_help())
    lines.append("  ADVISORY. Nothing declines anything yet, and nothing reads "
                 "this file — the declines are here to be correlated against "
                 "the leads that produced no hook. That is D21's reversal "
                 "condition, and this is the apparatus for it.")
    return "\n".join(lines)
