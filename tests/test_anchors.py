"""The anchor draw and the fact table.

Run: python -m pytest tests/test_anchors.py -q
 or: python tests/test_anchors.py

Determinism is the load-bearing property here. The old assembler documented
seeding on sha256 rather than the builtin hash() because hash() is salted per
process, which would make every rebuild draw different lines — so "the same
batch" would never be the same batch and no A/B result would mean anything.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import anchors

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- determinism


def test_the_same_address_draws_the_same_lines():
    first = anchors.draw("sarah@example.ae", coach_type="Health",
                         sells_to="individuals")
    second = anchors.draw("sarah@example.ae", coach_type="Health",
                          sells_to="individuals")
    assert first.identity.id == second.identity.id
    assert first.offer.id == second.offer.id
    assert first.cta.id == second.cta.id


def test_case_and_whitespace_do_not_change_the_draw():
    assert (anchors.seed("Sarah@Example.AE ") == anchors.seed("sarah@example.ae"))


def test_the_seed_survives_a_separate_process():
    """The whole reason for sha256 over hash(). If this test ever fails,
    reproducibility is a lie everywhere else in the machine."""
    code = ("import sys; sys.path.insert(0, %r); "
            "from outbound import anchors; "
            "print(anchors.seed('sarah@example.ae'))" % str(ROOT))
    runs = {
        subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True).stdout.strip()
        for _ in range(3)
    }
    assert len(runs) == 1
    assert runs.pop() == str(anchors.seed("sarah@example.ae"))


def test_different_addresses_draw_differently():
    ids = {anchors.draw(f"coach{i}@example.ae", coach_type="Life",
                        sells_to="individuals").identity.id
           for i in range(30)}
    assert len(ids) > 1


# ------------------------------------------------------------------ the match


def test_an_exact_segment_line_can_be_drawn():
    drawn = [anchors.draw(f"c{i}@example.ae", coach_type="Career",
                          sells_to="individuals").identity
             for i in range(40)]
    assert any(line.meta.get("coach_type") == "Career" for line in drawn)


def test_generic_lines_still_appear_for_a_matched_segment():
    """70/30, so a segment never reads as one repeated sentence."""
    drawn = [anchors.draw(f"c{i}@example.ae", coach_type="Career",
                          sells_to="individuals").identity
             for i in range(60)]
    generic = [l for l in drawn if l.meta.get("coach_type") == "Any"]
    assert generic, "no generic line ever drawn — the 70/30 mix is broken"


def test_an_unknown_segment_falls_back_to_generic():
    anchor = anchors.draw("x@example.ae", coach_type="", sells_to="")
    assert anchor.identity.meta.get("coach_type") == "Any"
    assert anchor.segment == ""


def test_a_corporate_lead_can_draw_a_corporate_line():
    drawn = {anchors.draw(f"c{i}@example.ae", coach_type="Executive",
                          sells_to="corporates").identity.meta.get("sells_to")
             for i in range(40)}
    assert "corporates" in drawn


def test_the_single_lead_draw_lands_inside_the_declared_share():
    """Ranges are derived from weights now, so they are contiguous by
    construction and there is nothing left to hand-maintain."""
    bank = anchors.CopyBank.load()
    per_line = anchors.shares(bank.offer)
    for i in range(50):
        email = f"c{i}@example.ae"
        line = anchors.draw_weighted(bank.offer, email, "offer")
        roll = ((anchors.seed(email, "offer") % 10_000) + 1) / 10_000
        cumulative = 0.0
        for candidate in bank.offer:
            cumulative += per_line[candidate.id]
            if candidate.id == line.id:
                break
        assert roll <= cumulative + 1e-9, (email, line.id)


# --------------------------------------------------------------- the fact table


def test_the_fact_table_is_internally_consistent():
    """The aggregate lines claim 67 meetings, 30 clients and AED 416,000.
    If the per-segment rows stop summing to those, an aggregate line is a lie."""
    facts = anchors.load_facts()
    assert facts.total_meetings == 67
    assert facts.total_clients == 30
    assert facts.total_aed == 416_000
    assert facts.total_sent == 2_091


def test_aggregate_rounds_aed_down_not_up():
    facts = anchors.load_facts()
    assert 400_000 in facts.aggregate_numbers()
    assert 500_000 not in facts.aggregate_numbers()


def test_a_segment_licenses_only_its_own_numbers():
    facts = anchors.load_facts()
    health = anchors.allowed_numbers(facts, "Health")
    assert 78_000 in health
    assert 120_000 not in health, "a Business number leaked into a Health lead"


def test_periods_license_their_exact_equivalents():
    assert anchors.period_numbers("6 weeks") == {6, 42}
    assert anchors.period_numbers("60 days") == {60, 2}
    assert anchors.period_numbers("2 months") == {2, 60}


def test_periods_do_not_license_approximations():
    """45 days is 6.4 weeks. Rounding that to 6 would license a number the
    data does not support."""
    assert anchors.period_numbers("45 days") == {45}


def test_offer_numbers_are_allowed_for_every_lead():
    facts = anchors.load_facts()
    for segment in ("Health", "Business", ""):
        allowed = anchors.allowed_numbers(facts, segment)
        assert {10, 15, 40}.issubset(allowed)


def test_every_hand_written_line_survives_the_linter():
    """The files themselves have to obey the rules the linter enforces. A
    hand-written line carrying an invented number, or attributing one segment's
    result to another, would fail every email that drew it."""
    from outbound import lint
    facts = anchors.load_facts()
    widened = anchors.all_numbers(facts)
    bank = anchors.CopyBank.load()
    problems = []
    for beat in (bank.identity, bank.offer, bank.cta, bank.ps):
        for line in beat:
            for message in (lint.check_numbers(line.line, widened)
                            + lint.check_attribution(line.line, facts)):
                problems.append(f"{line.id}: {message}")
    assert not problems, "hand-written lines the linter rejects: " + "; ".join(problems)


def test_a_relabelled_line_would_be_caught():
    """Guards the guard: if check_attribution stops matching, this fails."""
    from outbound import lint
    facts = anchors.load_facts()
    bad = "A health coach in Dubai closed AED 120,000 last quarter."
    assert lint.check_attribution(bad, facts)


# ------------------------------------------------------------- batch behaviour


def test_batch_shares_add_up():
    drawn = [anchors.draw(f"c{i}@example.ae", coach_type="Life",
                          sells_to="individuals") for i in range(20)]
    shares = anchors.batch_shares(drawn)
    for beat, per_line in shares.items():
        assert abs(sum(per_line.values()) - 1.0) < 0.01, beat


def test_a_real_batch_stays_under_the_repetition_cap():
    """Three of five beats come from a pool of twelve sentences. On the last
    batch of ten the top line took 50%; the cap is 35%."""
    from outbound.lint import FIXED_LINE_SHARE_CAP
    drawn = [anchors.draw(f"coach{i}@somewhere{i}.ae", coach_type="Life",
                          sells_to="individuals") for i in range(60)]
    shares = anchors.batch_shares(drawn)
    over = {beat: dict(list(lines.items())[:1])
            for beat, lines in shares.items()
            if next(iter(lines.values())) > FIXED_LINE_SHARE_CAP}
    assert not over, f"beats over the {FIXED_LINE_SHARE_CAP:.0%} cap: {over}"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)


# ------------------------------------------------ the generic pool's audience


def test_an_individuals_seller_is_never_handed_corporate_proof():
    """The generic pool used to take every `Any` line regardless of audience,
    so "I get coaches in front of the people who actually hold the budget"
    could land on a health coach whose buyer is one person paying for themselves.
    The identity beat's whole job is a matching reference group."""
    bank = anchors.CopyBank.from_csv()
    for coach_type in ("Health", "Life", "Mindset", "Fitness", "Career"):
        _, generic = anchors._identity_pools(bank.identity, coach_type, "individuals")
        assert generic, coach_type
        for line in generic:
            assert line.meta.get("sells_to") in ("any", ""), \
                f"{coach_type}: {line.id} is {line.meta.get('sells_to')}-facing"


def test_a_corporate_seller_can_draw_corporate_proof():
    bank = anchors.CopyBank.from_csv()
    _, generic = anchors._identity_pools(bank.identity, "Leadership", "corporates")
    assert any(l.meta.get("sells_to") == "corporates" for l in generic)
    assert any(l.meta.get("sells_to") in ("any", "") for l in generic)


def test_an_unknown_audience_draws_only_neutral_proof():
    """Guessing the reference group is exactly what an empty `sells_to` exists
    to avoid, so it must not be guessed here either."""
    bank = anchors.CopyBank.from_csv()
    _, generic = anchors._identity_pools(bank.identity, "Life", "")
    assert generic
    for line in generic:
        assert line.meta.get("sells_to") in ("any", ""), line.id


def test_no_lead_in_a_mixed_batch_gets_the_other_audiences_proof():
    """End to end through the real allocator, on a batch carrying both
    audiences and nine segments."""
    bank = anchors.CopyBank.from_csv()
    segments = ["Health", "Leadership", "Executive", "Life", "Career",
                "Business", "Mindset", "", "Fitness"]
    audiences = ["individuals", "corporates", ""]
    by_id = {l.id: l for l in bank.identity}
    for n in (11, 30, 90):
        leads = [{"email": f"l{i}@x.ae", "coach_type": segments[i % len(segments)],
                  "sells_to": audiences[i % 3]} for i in range(n)]
        dealt = anchors.deal_batch(leads, bank=bank)
        for lead in leads:
            drawn = by_id[dealt[lead["email"]].identity.id]
            flavour = drawn.meta.get("sells_to")
            if flavour in ("any", ""):
                continue
            assert lead["sells_to"] == flavour, (
                f"n={n}: a {lead['sells_to'] or 'unknown'}-audience lead drew "
                f"{drawn.id}, which is {flavour}-facing")


def test_the_corporate_generic_pool_is_deep_enough_to_hold_its_share():
    """Two lines cannot cover a pool under a 35% cap; three can."""
    from outbound import lint
    bank = anchors.CopyBank.from_csv()
    _, generic = anchors._identity_pools(bank.identity, "", "corporates")
    corporate = [l for l in generic if l.meta.get("sells_to") == "corporates"]
    assert len(corporate) >= int(1 / lint.FIXED_LINE_SHARE_CAP) + 1, \
        [l.id for l in corporate]


# ---------------------------------------------------------------- the claim
#
# An identity line's WORDS are the drafter's to write; its CLAIM is not. These
# pin the second half of that sentence.


def test_every_identity_line_declares_a_claim():
    """A line with no Claim is a line whose figures nothing checks — which is
    the state `id-fit-2` shipped a wrong period in for a month."""
    bank = anchors.CopyBank.from_csv()
    missing = [l.id for l in bank.identity if not (l.meta.get("claim") or "").strip()]
    assert not missing, missing


def test_every_live_claim_resolves_against_the_fact_table():
    bank = anchors.CopyBank.from_csv()
    facts = anchors.load_facts()
    for line in bank.identity:
        assert anchors.claim_for(line, facts) is not None, line.id


def test_a_claim_resolves_to_its_own_results_row():
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Business:meetings,period,clients"}), facts)
    assert spec.figures == {"meetings": 12, "period": "60 days", "clients": 5}
    assert spec.city == "Dubai"
    assert spec.names_segment is True


def test_a_widened_claim_uses_a_rows_figures_without_naming_it():
    # Six live `Any`-typed lines do exactly this. It is the one thing `shape`
    # had no vocabulary for and the reason the Claim column exists.
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Health:meetings,clients|widened"}), facts)
    assert spec.figures == {"meetings": 9, "clients": 6}
    assert spec.names_segment is False


def test_an_aggregate_claim_cites_no_row_and_cannot_be_widened():
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "aggregate:total_meetings,practices"}), facts)
    assert spec.figures == {"total_meetings": 67, "practices": 8}
    assert spec.names_segment is False
    try:
        anchors.parse_claim("aggregate:total_meetings|widened")
    except anchors.ClaimError:
        pass
    else:
        raise AssertionError("an aggregate names no segment, so widening is meaningless")


def _rejects(raw, fragment):
    facts = anchors.load_facts()
    try:
        anchors.claim_for(anchors.Line("x", "", {"claim": raw}), facts)
    except anchors.ClaimError as exc:
        assert fragment in str(exc), f"{raw}: {exc}"
        return
    raise AssertionError(f"{raw!r} should not have parsed")


def test_a_claim_naming_an_unknown_column_is_an_error():
    _rejects("Business:revenue", "is not a column")


def test_a_claim_naming_a_segment_with_no_row_is_an_error():
    _rejects("Nowhere:meetings", "has no row in results.csv")


def test_a_claim_with_no_columns_is_an_error():
    _rejects("Business:", "names a row but no columns")


def test_a_qualifier_no_column_backs_is_an_error():
    # The whole point. "all with prospects ready to say yes" describes prospect
    # intent, and nothing in this operation measures that.
    _rejects("Business:meetings+ready-to-say-yes", "not backed by a column")


def test_a_qualifier_the_row_contradicts_is_an_error():
    # `id-lead-4` asserted a corporate decision-maker about the Leadership row,
    # whose buyer is an individual. Same defect as a flourish, less obvious.
    _rejects("Leadership:meetings+budget-holder", "sells_to == 'corporates'")


def test_a_column_the_row_never_measured_cannot_be_claimed():
    # Blank is "nobody measured this", not zero. Only Life and Mindset carry a
    # first_client_days; claiming it anywhere else would be inventing a result.
    _rejects("Business:first_client_days", "has no first_client_days recorded")


def test_a_claim_licenses_its_own_figures_and_nothing_else():
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Fitness:aed_closed,close_period"}), facts)
    licensed = spec.numbers()
    assert 36000 in licensed and 36 in licensed   # the k form
    assert 45 in licensed                         # close_period, in days
    # Deliberately NOT unioned with OFFER_NUMBERS. `id-fit-2` shipped "in 6
    # weeks" against a 45-day close_period for a month, passing only because
    # 6 sits in the offer set.
    assert 6 not in licensed
    assert 10 not in licensed and 15 not in licensed


def test_a_period_is_licensed_in_both_of_its_exact_units():
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Business:period"}), facts)
    assert {60, 2} <= spec.numbers()   # 60 days is 2 months, same fact


def test_a_first_meeting_is_licensed_in_the_week_it_fell_in():
    # "inside a week" for day 7, "week 2" for day 10. The ceiling is exact
    # under the "inside" framing, not the rounding this module refuses.
    facts = anchors.load_facts()
    lead = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Leadership:first_meeting_days"}), facts)
    assert {7, 1} <= lead.numbers()
    biz = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Business:first_meeting_days"}), facts)
    assert {10, 2} <= biz.numbers()


def test_a_still_working_flag_is_not_a_number():
    facts = anchors.load_facts()
    spec = anchors.claim_for(
        anchors.Line("x", "", {"claim": "Fitness:meetings,still_working"}), facts)
    assert spec.figures["still_working"] is True
    assert spec.numbers() == {7}      # the meetings, and no stray 1 from a bool


def test_the_column_vocabulary_comes_from_the_fact_table():
    """Hand-listing it would let a new results.csv column go uncitable, and a
    typo in a Claim go unnoticed."""
    for column in ("meetings", "period", "clients", "aed_closed", "city",
                   "still_working", "first_client_days"):
        assert column in anchors.CLAIM_COLUMNS
    assert "segment" not in anchors.CLAIM_COLUMNS
