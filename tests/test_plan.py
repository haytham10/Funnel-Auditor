"""The retrieval plan: which rungs a lead has, and which we would not buy.

Run: python -m pytest tests/test_plan.py -q
 or: python tests/test_plan.py

Two things are pinned here and they pull in opposite directions.

**The ladder is now data**, so these tests assert it against the modules that own
its vocabulary — `audit.apify.ACTORS` for the actor keys and `observe.PLATFORMS`
/ `observe.KINDS` for the rest — rather than restating four rungs a fifth time.
That is the whole point of moving it out of prose: a copy nothing checks is what
let the paid rung sit at #1 under a heading that said "cost order".

**And nothing may act on a decline.** A plan is a description. A lead whose every
paid rung points at somebody else's channel still gets a plan, still exits 0, and
is still handed to every stage after this one. That is D21 expressed as an
assertion instead of a paragraph, and exit 1 there is the natural mistake — the
same one `tests/test_resolve.py` pins one stage earlier.
"""

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import observe, plan, resolve


def channel(**overrides) -> resolve.Channel:
    fields = {"platform": "linkedin", "url": "https://linkedin.com/in/nadiakarim",
              "handle": "nadiakarim", "confidence": "confirmed",
              "evidence": "handle 'nadiakarim' contains 'nadia'", "source": "row"}
    fields.update(overrides)
    return resolve.Channel(**fields)


def identity(*channels, **overrides) -> resolve.Identity:
    fields = {"lead_key": "nadia@nadiacoaching.ae", "name": "Nadia Karim",
              "owner_verdict": "confirmed"}
    fields.update(overrides)
    built = resolve.Identity(**fields)
    built.channels = list(channels) or [channel()]
    return built


def fixed_price(actor_key: str, item_count: int):
    """A stub price. Injected exactly as `resolve`'s fetcher is, so no test
    reaches Apify — pricing needs a token and the network, and a suite that
    depends on either fails differently for whoever runs it."""
    return 0.01 * item_count, ""


# ------------------------------------------------------------------ the ladder


def test_every_rung_names_a_real_actor_or_is_free():
    """A rung naming an actor this machine does not have is a rung that cannot
    be walked, and it would look identical to a real one in the plan file."""
    from audit.apify import ACTORS

    for rung in plan.LADDER:
        if rung.actor_key:
            assert rung.actor_key in ACTORS, rung.name


def test_every_rung_speaks_the_observation_vocabulary():
    """Platforms and kinds are `observe`'s, borrowed rather than restated — a
    second vocabulary for the same thing is the drift this move exists to end."""
    for rung in plan.LADDER:
        for platform in rung.platforms:
            assert platform in observe.PLATFORMS, rung.name
        for kind in rung.kinds:
            assert kind in observe.KINDS, rung.name


def test_the_ladder_is_in_cost_order():
    """Free rungs before paid ones. The list once opened with the paid LinkedIn
    rung under a heading that said cost order, which is how a batch reaches for
    LinkedIn before reading an About page it already has on disk."""
    paid = [index for index, rung in enumerate(plan.LADDER) if rung.paid]
    free = [index for index, rung in enumerate(plan.LADDER) if not rung.paid]
    assert max(free) < min(paid)


def test_the_about_rung_offers_the_page_as_well_as_a_framework():
    """F5's narrowing, reversed on batch evidence. `2026-08-01-q1` MISSED three
    leads and all three were `kind: about` observations an independent verifier
    had VERIFIED. What the verifier refuses is the generic, not the location.

    Pinned against `select` rather than restated, so the two cannot drift: the
    rung offers what the ranker will accept."""
    from outbound import select

    about = next(r for r in plan.LADDER if r.name == "about")
    assert about.kinds == ("framework", "about")
    assert all(select.ban_for(observe.Observation(
        lead_key="a@x.ae", platform="site", kind=kind, author="self",
        text=" ".join(["word"] * 40)), today=date(2026, 8, 1)) == ""
        for kind in about.kinds)


def test_the_paid_rungs_carry_the_hook_window_in_their_flags():
    """Two stages asked one LinkedIn profile two different questions: research
    ran `--max 5` with no window, the hook stage ran `--since 3months`. The hook
    stage then "discovered" posts research had never requested — 4 of the 5
    UNOBSERVED in `2026-08-01-q1`, which is the number the flip is gated on.

    `3months` and `"90 days"` are `select.HOOK_RECENCY_DAYS` in each actor's own
    spelling, so they are pinned against it rather than against a memory."""
    from outbound import select

    assert select.HOOK_RECENCY_DAYS == 90
    posts = next(r for r in plan.LADDER if r.name == "li_posts")
    insta = next(r for r in plan.LADDER if r.name == "ig_posts")
    assert "--since 3months" in posts.flags
    assert '--newer-than "90 days"' in insta.flags
    # And the spelling has to be one the actor accepts, or the call errors at
    # the point where the whole stage is already committed.
    from audit import apify

    assert "3months" in apify.LI_POSTED_LIMITS


def test_command_and_flags_travel_together():
    """`apify ig --mode details` reads a bio for the floors and `--mode posts`
    is hook material: one subcommand, two rungs, two windows. A flag set with no
    command to attach to would be checked against both — and a command with no
    flags is config nothing reads, which is how a value goes stale unnoticed."""
    for rung in plan.LADDER:
        assert bool(rung.flags) == bool(rung.command), rung.name


def test_no_rung_claims_to_be_batchable_without_evidence():
    """A `batched` claim is a container-boot estimate that is wrong by the size
    of the batch if it is not true, so each one is pinned to what
    `audit/apify.py` actually does rather than to an assumption.

    `li_profile` batches: its actor's input IS an array of URLs. `li_posts`
    provably cannot — `maxPosts` is a run-wide budget, verified by direct test
    with two target URLs where all ten posts came back from one profile.
    `ig_post` is assumed to share that flaw and says so in its note."""
    from audit import apify
    import inspect

    batchable = {r.name for r in plan.LADDER if r.paid and r.batched}
    assert batchable == {"li_profile"}, batchable
    # The evidence, not a memory of it: one wrapper takes a list of URLs and
    # the other takes exactly one, which is the whole of the claim.
    assert "urls" in inspect.signature(apify.linkedin_profile).parameters
    assert "url" in inspect.signature(apify.linkedin_posts).parameters
    assert "urls" not in inspect.signature(apify.linkedin_posts).parameters


# ------------------------------------------------------------------ the plan


def test_a_linkedin_channel_plans_both_of_its_rungs():
    """LinkedIn is two rungs, not one: a profile scrape and a posts scrape are
    different actors at different prices, one batchable and one provably not.

    Naming only the cheaper would report half of what reaching that channel
    costs — and while LADDER had a single LinkedIn rung, `metrics.rung_of`
    attributed three profile-sourced hooks to the posts rung, in the very number
    that settles F5."""
    built = plan.plan_lead(identity())
    assert [s.rung for s in built.steps] == ["li_profile", "li_posts"]
    assert all(s.decision == "take" for s in built.steps)
    assert all(s.actor_key for s in built.steps), "both rungs are paid"


def test_the_site_rung_appears_only_when_the_caller_has_the_site():
    """An Identity does not carry the lead's own homepage — nothing harvests it
    into a channel list — so it is passed in or it is absent."""
    without = plan.plan_lead(identity())
    assert not any(s.rung == "about" for s in without.steps)

    with_site = plan.plan_lead(identity(), site_url="https://nadiacoaching.ae")
    about = next(s for s in with_site.steps if s.rung == "about")
    assert about.est_cost_usd == 0.0 and not about.actor_key


def test_an_absent_channel_on_a_paid_rung_would_be_declined():
    built = plan.plan_lead(identity(channel(
        platform="instagram", url="https://instagram.com/harrison_intl",
        handle="harrisonintl", confidence="absent",
        evidence="handle 'harrisonintl' contains no part of their name")))
    assert [s.decision for s in built.steps] == ["decline"]
    assert "harrisonintl" in built.steps[0].reason


def test_an_absent_channel_on_a_free_rung_is_not_declined():
    """There is nothing to decline. A decline is about a purchase, and D21 is
    only ever about spend."""
    built = plan.plan_lead(identity(channel(
        platform="youtube", url="https://youtube.com/@harrisonassessments",
        handle="harrisonassessments", confidence="absent",
        evidence="handle contains no part of their name")))
    assert [s.decision for s in built.steps] == ["take"]


def test_unknown_is_never_declined():
    """`resolve`'s rule, one stage over: `unknown` means no tell was available,
    never that the tell said no. Declining it is the false-negative surface R3
    names, and it would be permanent and invisible."""
    built = plan.plan_lead(identity(channel(
        confidence="unknown", handle="", evidence="channel id carries no name")))
    assert {s.decision for s in built.steps} == {"take"}


def test_a_declined_step_is_still_in_the_plan():
    """It binds now (D27), and it is still written down with its URL rather than
    dropped. A decline nobody can read back is a purchase refused for a reason
    that has stopped existing — and `metrics --plan` needs the step to correlate
    against the lead's hook outcome."""
    built = plan.plan_lead(identity(channel(confidence="absent",
                                            evidence="names somebody else")))
    assert built.steps and built.steps[0].url
    assert built.steps[0].decision == "decline"
    assert "names somebody else" in built.steps[0].reason


def test_a_decline_gates_spend_and_never_inclusion():
    """The half of D21 that does not change when the gate turns on. A lead whose
    only paid rung is declined gets a null hook, which is a good answer, and it
    still gets a plan, a row and a Blocker. Nothing here drops anybody."""
    built = plan.plan_lead(identity(channel(confidence="absent",
                                            evidence="names somebody else")))
    assert built.lead_key, "the lead survives its own decline"
    assert built.steps, "and its rungs are still described"
    assert all(s.decision == "decline" for s in built.steps)


def test_a_lead_with_no_channels_still_gets_a_plan():
    """Every lead gets one. A plan is a description, not a gate."""
    built = plan.plan_lead(resolve.Identity(lead_key="x@y.ae", name="Nobody"))
    assert built.lead_key == "x@y.ae"
    assert built.steps == []
    assert built.has_rung is False


def test_the_no_rung_note_says_the_lead_is_still_reachable():
    """A lead with no channel is not unreachable — the podcast rung is a search
    for their name and needs no URL. A bare 'no rung' would read as a lead to
    skip, which is the inclusion gate D21 forbids."""
    built = plan.plan_lead(resolve.Identity(lead_key="x@y.ae"))
    assert any("blind web search" in note for note in built.notes)


# ------------------------------------------------------------------ the price


def test_a_paid_step_is_not_priced_unless_a_price_is_injected():
    """Pricing needs a token and the network. Reporting an unpriced batch as
    $0.0000 would say a batch nobody looked at is free."""
    built = plan.plan_lead(identity())
    assert built.steps[0].est_cost_usd is None
    assert built.steps[0].cost_note == plan.NOT_PRICED


def test_an_injected_price_lands_on_the_step():
    built = plan.plan_lead(identity(), price=fixed_price)
    assert built.steps[0].est_cost_usd == 0.01 * plan.POSTS_PER_LEAD


def test_a_declined_step_keeps_its_price_note():
    """`reason` says why the decision; `cost_note` says why the estimate. The
    first cut sniffed the second out of the first, and a decline overwrote it."""
    built = plan.plan_lead(identity(channel(confidence="absent",
                                            evidence="somebody else")))
    assert built.steps[0].decision == "decline"
    assert built.steps[0].cost_note == plan.NOT_PRICED


def test_apify_price_fails_open_rather_than_raising():
    """A stage that spends nothing must not fail because the billing API did.
    That is `_require_cost_approval`'s own rule one stage earlier."""
    estimate, note = plan.apify_price("not_an_actor", 5)
    assert estimate is None and note


def test_remaining_usd_is_none_when_the_cap_cannot_be_worked_out():
    assert plan.remaining_usd(None) is None
    assert plan.remaining_usd({"limits": {}, "current": {}}) is None
    assert plan.remaining_usd(
        {"limits": {"maxMonthlyUsageUsd": 5}, "current": {"monthlyUsageUsd": 2}}) == 3.0


# ------------------------------------------------------------------ the gate


def test_a_real_plan_validates():
    assert plan.validate(plan.plan_lead(identity())) == []


def test_a_plan_with_no_lead_key_is_caught():
    problems = plan.validate(plan.LeadPlan(steps=[]))
    assert any("lead_key" in p for p in problems)


def test_a_decline_with_no_reason_is_caught():
    """`research`'s rule applied to a purchase: a hard verdict naming nothing
    was reasoned, not checked. A decline gets read later or it is noise."""
    built = plan.LeadPlan(lead_key="a@b.ae", steps=[plan.Step(
        lead_key="a@b.ae", rung="li_posts", platform="linkedin",
        url="https://linkedin.com/in/x", actor_key="li_posts",
        decision="decline", reason="")])
    assert any("names nothing" in p for p in plan.validate(built))


def test_a_step_naming_an_actor_this_machine_does_not_have_is_caught():
    built = plan.LeadPlan(lead_key="a@b.ae", steps=[plan.Step(
        lead_key="a@b.ae", rung="li_posts", platform="linkedin",
        url="https://linkedin.com/in/x", actor_key="li_scraper_9000")])
    assert any("li_scraper_9000" in p for p in plan.validate(built))


def test_a_repeated_rung_on_one_page_is_caught():
    """Two steps for one container boot would double the estimate."""
    step = plan.Step(lead_key="a@b.ae", rung="li_posts", platform="linkedin",
                     url="https://linkedin.com/in/x", actor_key="li_posts")
    built = plan.LeadPlan(lead_key="a@b.ae", steps=[step, step])
    assert any("repeats" in p for p in plan.validate(built))


def test_a_decision_outside_the_enum_is_caught():
    built = plan.LeadPlan(lead_key="a@b.ae", steps=[plan.Step(
        lead_key="a@b.ae", rung="li_posts", platform="linkedin",
        url="https://linkedin.com/in/x", actor_key="li_posts",
        decision="maybe", reason="hmm")])
    assert any("decision" in p for p in plan.validate(built))


# --------------------------------------------------------------- round-tripping


def test_a_plan_survives_json_and_back():
    built = plan.plan_lead(identity(), price=fixed_price)
    restored = plan.load({"plans": [built.to_dict()]})[0]
    assert restored.to_dict() == built.to_dict()


def test_an_unpriced_step_does_not_come_back_as_free():
    """`None` is a real value here — 'we could not price this' must not be
    coerced into the field default, which would read as $0."""
    restored = plan.Step.from_dict({"lead_key": "a@b.ae", "est_cost_usd": None})
    assert restored.est_cost_usd is None


def test_two_runs_over_the_same_identities_are_identical():
    """The plan file is meant to be diffed against the last batch's."""
    identities = [identity()]
    first = plan.plan_all(identities, price=fixed_price)
    second = plan.plan_all(identities, price=fixed_price)
    assert [p.to_dict() for p in first["plans"]] == \
           [p.to_dict() for p in second["plans"]]


# ------------------------------------------------------------------ the report


def test_the_report_leads_with_the_decline_count():
    """At $0.009/lead the money is a rounding error. The number that
    discriminates is the one the next batch correlates against a null hook."""
    result = plan.plan_all([identity(channel(confidence="absent",
                                             evidence="somebody else"))])
    lines = result["report"].splitlines()
    assert "declined 2 paid step(s)" in lines[1]


def test_the_report_says_a_decline_binds_and_what_it_does_not_do():
    """It shipped advisory for two batches and now it binds (D27), so the line
    that used to say nothing acts on this has to say what does — and has to
    keep saying the half that never changes, which is that a decline gates
    spend and never inclusion."""
    report = plan.plan_all([identity()])["report"]
    assert "BINDS" in report
    assert "never inclusion" in report
    assert "metrics --plan" in report, \
        "the gate names its own measurement, or nobody collects it"


def test_an_unpriced_batch_does_not_report_a_dollar_figure():
    result = plan.plan_all([identity()])
    assert "NO ESTIMATE" in result["report"]
    assert "$0.0000" not in result["report"]


# --------------------------------------------------------- the standalone path

if __name__ == "__main__":
    import inspect

    failures = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        if inspect.signature(fn).parameters:
            print(f"SKIP {name} (needs a pytest fixture)")
            continue
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)


# ------------------------------------------------- the address decline (D28b)


def test_a_lead_nothing_can_be_sent_to_declines_its_paid_rungs():
    """The second decline rule, and it exists for the token bill rather than the
    Apify one: q2+q3 spent ~18.6M tokens per shipped email against $1.13 of
    Apify across both batches. Buying a hook for a lead nobody can email spends
    the research, hook, verify and draft passes behind it on nothing."""
    built = plan.plan_lead(identity(channel(confidence="confirmed")),
                           unreachable=True)
    paid = built.paid_steps
    assert paid, "fixture must produce at least one paid rung"
    assert all(s.decision == "decline" for s in paid)
    assert all(plan.ADDRESS_DECLINE in s.reason for s in paid)


def test_the_address_decline_keeps_every_free_rung():
    """A decline is about spend. Free retrieval is not spend, and a lead with no
    address still gets researched — they may yet turn out reachable, and the
    row is still worth having."""
    built = plan.plan_lead(identity(channel()), site_url="https://x.ae",
                           unreachable=True)
    free = [s for s in built.steps if not s.paid]
    assert free
    assert all(s.decision == "take" for s in free)


def test_an_unreachable_lead_still_gets_a_plan_and_still_validates():
    """Spend, never inclusion — the same guarantee the ownership decline makes.
    A plan that vanished would be a drop wearing a gate's clothes."""
    built = plan.plan_lead(identity(channel()), unreachable=True)
    assert built.lead_key
    assert plan.validate(built) == []


def test_plan_all_matches_unreachable_on_lead_key_or_name():
    """`email-find` keys its output by lead_key when the row had one and by
    name when it did not — an intake file carries both, a hand-run single lead
    carries only the name."""
    ident = identity(channel())
    by_key = plan.plan_all([ident], unreachable={ident.lead_key})["plans"][0]
    by_name = plan.plan_all([ident], unreachable={ident.name})["plans"][0]
    assert by_key.would_decline
    assert by_name.would_decline


def test_no_addresses_file_declines_nothing():
    """The default path is unchanged: without `--addresses` nothing here knows
    anything about reachability and every rung stays taken."""
    built = plan.plan_all([identity(channel())])["plans"][0]
    assert built.would_decline == []


def test_the_report_counts_the_two_decline_rules_apart():
    """One total would have reported the first live run of the address rule —
    every declined step declined on address — as ownership declines, which is
    the opposite diagnosis and has the opposite fix."""
    ident = identity(channel(confidence="absent", evidence="handle names somebody else"))
    other = identity(channel(), lead_key="b@b.ae", name="Other Person")
    text = plan.plan_all([ident, other], unreachable={"b@b.ae"})["report"]
    assert "on ownership" in text
    assert "on address" in text
    assert "saves agent passes rather than scrapes" in text


def test_no_address_declines_means_no_address_line_at_all():
    """A batch where every lead is reachable must not print a zero. `metrics`'
    rule: a count nobody supplied is not a measurement of nothing."""
    text = plan.plan_all([identity(channel())])["report"]
    assert "on address" not in text
