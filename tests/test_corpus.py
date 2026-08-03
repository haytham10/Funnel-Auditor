"""Attaching somebody else's retrieval to the list you are running.

Run: python -m pytest tests/test_corpus.py -q
 or: python tests/test_corpus.py

D32 made this necessary: an Instagram dump is evidence and not a source list, so
its corpus has to join to a list intaken from somewhere else. The keys do not
match — `fetch.lead_key` is `slug|site_url` and the same coach has a different
site on a queue CSV — so the join is by handle, then by name.

**The tests that matter are the refusals.** A stranger's mailbox verified clean
on the last list; a stranger's *posts* are worse, because they produce a hook
that is verified, dated, quotable and about somebody else, and every mechanical
gate in this machine passes it. So an ambiguous match must attach nothing, in
both directions: two accounts answering to one lead, and two leads claiming one
account.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

from outbound import corpus, observe                           # noqa: E402
from outbound.fetch import lead_key                            # noqa: E402
from outbound.normalize import Lead                            # noqa: E402


def _lead(name="Maria Fenton", handle="mariafenton__", site="https://mf.com"):
    return Lead(name=name, slug=name.lower().replace(" ", "-"), site_url=site,
                instagram_url=f"https://www.instagram.com/{handle}")


def _pool(key="ig-maria|", handle="mariafenton__", n=2):
    out = [observe.Observation(
        lead_key=key, platform="instagram",
        url=f"https://www.instagram.com/{handle}", fetched_at="2026-08-02T12:00:00Z",
        author="self", kind="bio", text="Coach in Dubai",
        retrieved_by="apify:ig_profile")]
    for i in range(n):
        out.append(observe.Observation(
            lead_key=key, platform="instagram",
            url=f"https://www.instagram.com/p/POST{i}/",
            fetched_at="2026-08-02T12:00:00Z", published_at="2026-07-30",
            author="self", kind="post", text=f"caption {i}",
            retrieved_by="apify:ig_profile"))
    return out


def test_the_corpus_is_rekeyed_onto_the_list_being_run():
    """The whole point: two files about one coach that joined on nothing."""
    lead = _lead()
    result = corpus.attach([lead], _pool())
    assert result.leads_matched == 1
    assert result.matched[lead_key(lead)] == "handle"
    assert {o.lead_key for o in result.observations} == {lead_key(lead)}
    assert len(result.observations) == 3


def test_the_rekeyed_observations_still_pass_the_schema():
    """A re-keyed record is a record. If moving it breaks the gate, the corpus
    is unusable by every stage that reads one."""
    result = corpus.attach([_lead()], _pool())
    assert not observe.validate_all(result.observations)


def test_the_obs_id_is_regenerated_because_the_key_changed():
    """`make_id` hashes the lead_key. Keeping the old id would claim two
    different observations are the same record."""
    before = _pool()
    result = corpus.attach([_lead()], before)
    assert {o.obs_id for o in result.observations}.isdisjoint(
        {observe.make_id(o) for o in before})
    assert all(o.obs_id == observe.make_id(o) for o in result.observations)


def test_the_handle_is_tried_before_the_name():
    """A handle is the lead's own claim about which account is theirs. A name is
    the weak tell and it is where the stranger failures live."""
    lead = _lead(name="Maria Fenton", handle="mfcoaching")
    pools = _pool(key="a|", handle="mfcoaching") + _pool(key="b|", handle="mariafenton")
    result = corpus.attach([lead], pools)
    assert result.matched[lead_key(lead)] == "handle"
    assert all(o.url.endswith(("mfcoaching", "POST0/", "POST1/"))
               for o in result.observations if o.kind == "bio")


def test_a_lead_with_no_handle_can_still_match_on_name():
    lead = Lead(name="Maria Fenton", slug="maria-fenton")
    result = corpus.attach([lead], _pool(handle="mariafenton"))
    assert result.matched[lead_key(lead)] == "name"


def test_two_accounts_answering_to_one_lead_attach_nothing():
    """Not a tie to break. A hook from the wrong account is verified, dated,
    quotable and about a stranger."""
    lead = Lead(name="Maria Fenton", slug="maria-fenton")
    pools = _pool(key="a|", handle="mariafenton") + _pool(key="b|", handle="mariafentoncoach")
    result = corpus.attach([lead], pools)
    assert result.observations == []
    assert result.leads_matched == 0
    assert result.ambiguous and "attached nothing" in result.ambiguous[0]


def test_a_shared_surname_does_not_move_one_coachs_posts_to_another():
    """`handle_matches` is any-token, which is right for the advisory note it
    was written for. On this module's first live run it handed Jack Fenton all
    of Maria Fenton's posts, because "fenton" is in "mariafenton"."""
    maria = Lead(name="Maria Fenton", slug="maria-fenton")
    jack = Lead(name="Jack Fenton", slug="jack-fenton")
    result = corpus.attach([maria, jack], _pool(handle="mariafenton"))
    assert result.matched == {lead_key(maria): "name"}
    assert result.unmatched_leads == ["Jack Fenton"]


def test_two_leads_of_the_same_name_claiming_one_account_attach_nothing():
    """The mirror ambiguity, and the one all-token matching cannot rule out:
    two different coaches really are called this."""
    a = Lead(name="Sarah Khan", slug="sarah-khan", site_url="https://a.com")
    b = Lead(name="Sarah Khan", slug="sarah-khan", site_url="https://b.com")
    result = corpus.attach([a, b], _pool(handle="sarahkhan"))
    assert result.observations == []
    assert result.ambiguous and "attached to none of them" in result.ambiguous[0]


def test_a_lead_with_no_corpus_is_reported_not_dropped():
    """It researches exactly as it did before. Nothing here gates inclusion."""
    result = corpus.attach([_lead(name="Nobody Here", handle="nobodyhere")],
                           _pool(handle="mariafenton__"))
    assert result.leads_matched == 0
    assert result.unmatched_leads == ["Nobody Here"]


def test_a_wider_dump_than_the_batch_is_normal_and_named():
    result = corpus.attach([_lead()],
                           _pool() + _pool(key="other|", handle="someoneelse"))
    assert result.leads_matched == 1
    assert result.unused_pools == ["someoneelse"]


def test_the_report_always_prints_the_denominator():
    """`collect`'s rule: a count of what was found is not a count of what
    should exist."""
    result = corpus.attach([_lead(), _lead(name="Nobody", handle="nobody")],
                           _pool())
    text = corpus.report(result, total_leads=2)
    assert "1/2 lead(s) matched" in text


def test_expect_is_the_only_thing_that_can_fail_this_stage():
    result = corpus.attach([_lead()], _pool())
    assert not corpus.short(result, 1)
    assert corpus.short(result, 2)
    assert not corpus.short(result, None)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
