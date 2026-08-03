"""Attach a corpus somebody else retrieved to the list you are actually running.

D32: an Instagram dump is evidence, not a source list. Run as the list itself it
converted 0.8% of raw rows against 25-45% for the queue CSVs, because on
Instagram owning a domain is anti-correlated with being our ICP and 74% of the
coaches had no address anywhere. Its hooks, though, were the best on record.

So the dump wants to be attached to a list that arrives reachable — and until
this module it could not be. `ig-intake` keys every observation by the IG lead's
own `fetch.lead_key`, which is `slug|site_url`, and a queue CSV's row for the
same human has a different site and therefore a different key. Two files about
one coach, joining on nothing.

**The join is by handle first and by name second, and never by guess.** A
handle is the strong tell: the lead's own `instagram_url` is a claim about which
account is theirs, and `resolve.handle_of` already knows how to read one. A name
is the weak tell, and it is exactly where the machine's worst failure lives —
`matt.wright@gmail.com` verified clean for a stranger on 2026-08-03, and a
stranger's *posts* would be worse than a stranger's mailbox, because they
produce a hook that is verified, quotable, dated, and about somebody else.

**So an ambiguous name attaches nothing and says so.** Two leads matching one
corpus entry, or two corpus entries matching one lead, is not a tie to break. It
is the one shape where being wrong is silent all the way to the reader.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from audit.email_check import name_tokens
from outbound.fetch import lead_key
from outbound.observe import Observation
from outbound.resolve import handle_of, handle_matches


@dataclass
class Attached:
    """The re-keyed corpus, and everything that did not join."""

    observations: list = field(default_factory=list)
    matched: dict = field(default_factory=dict)      # lead_key -> how it matched
    unmatched_leads: list = field(default_factory=list)
    unused_pools: list = field(default_factory=list)
    ambiguous: list = field(default_factory=list)

    @property
    def leads_matched(self) -> int:
        return len(self.matched)


def _handle_of_lead(lead) -> str:
    return handle_of(getattr(lead, "instagram_url", "") or "", "instagram")


def _pool_handles(observations: list) -> dict:
    """corpus `lead_key` -> the Instagram handle its observations come from.

    Read off the observation URLs rather than off the key, because the key is
    `slug|site_url` and the slug is a folded display name — which is the weak
    tell wearing the strong tell's clothes.
    """
    handles: dict[str, str] = {}
    for obs in observations:
        if handles.get(obs.lead_key):
            continue
        handle = handle_of(obs.url or "", "instagram")
        # A post URL is /p/<shortcode>, which carries no handle. A profile URL
        # is /<handle>. Both are in a dump, so the first one that answers wins.
        if handle and handle not in ("p", "reel", "reels", "tv", "stories"):
            handles[obs.lead_key] = handle
    return handles


def attach(leads: list, observations: list) -> Attached:
    """Re-key `observations` onto `leads`, by handle then by name.

    Returns everything: what joined, what did not, and every ambiguity, because
    a corpus that silently attached to 3 of 40 leads looks exactly like a corpus
    that attached to all of them if only the total is printed.
    """
    result = Attached()
    pools: dict[str, list] = {}
    for obs in observations or []:
        pools.setdefault(obs.lead_key, []).append(obs)
    handles = _pool_handles(observations or [])

    claimed: dict[str, list] = {}          # corpus key -> the leads claiming it
    plan: list[tuple] = []

    for lead in leads or []:
        key = lead_key(lead)
        own_handle = _handle_of_lead(lead)
        hits = [pool_key for pool_key, handle in handles.items()
                if own_handle and handle == own_handle]
        how = "handle"
        if not hits:
            tokens = name_tokens(getattr(lead, "name", "") or "", min_len=3)
            # **Every token, not any.** `handle_matches` answers "does this
            # handle carry part of the name", which is right for the advisory
            # note it was written for and far too loose for moving evidence
            # between humans: "fenton" is in "mariafenton", so Jack Fenton was
            # handed Maria Fenton's posts on the first live run of this module.
            # A surname in common is the exact shape of the failure that put
            # matt.wright@gmail.com in front of a stranger on 2026-08-03.
            hits = [pool_key for pool_key, handle in handles.items()
                    if tokens and all(handle_matches(handle, [t])
                                      for t in tokens)]
            how = "name"
        if not hits:
            result.unmatched_leads.append(getattr(lead, "name", "") or key)
            continue
        if len(hits) > 1:
            # Two accounts answer to this lead. Attaching either is a coin flip
            # whose wrong side is a hook about a stranger.
            result.ambiguous.append(
                f"{getattr(lead, 'name', '') or key}: {len(hits)} corpus "
                f"entries match on {how} ({', '.join(handles[h] for h in hits)})"
                f" — attached nothing")
            continue
        plan.append((lead, key, hits[0], how))
        claimed.setdefault(hits[0], []).append(getattr(lead, "name", "") or key)

    for lead, key, pool_key, how in plan:
        others = claimed.get(pool_key, [])
        if len(others) > 1:
            # The mirror ambiguity: one account, two leads claiming it. Found
            # by name matching two coaches who share a surname.
            result.ambiguous.append(
                f"{handles.get(pool_key, pool_key)}: claimed by {len(others)} "
                f"leads ({', '.join(others)}) — attached to none of them")
            continue
        for obs in pools.get(pool_key, []):
            moved = Observation.from_dict(
                {**obs.to_dict(), "lead_key": key, "obs_id": ""})
            result.observations.append(moved)
        result.matched[key] = how

    used = {pool_key for _, _, pool_key, _ in plan}
    for pool_key in pools:
        if pool_key not in used:
            result.unused_pools.append(handles.get(pool_key, pool_key))
    return result


def report(result: Attached, *, total_leads: int, expect: int | None = None) -> str:
    """Coverage, and every ambiguity in full.

    `collect`'s rule: a count of what was found is not a count of what should
    exist, so the denominator is always printed.
    """
    by_handle = sum(1 for how in result.matched.values() if how == "handle")
    lines = [f"CORPUS ATTACH: {result.leads_matched}/{total_leads} lead(s) "
             f"matched, {len(result.observations)} observation(s) attached "
             f"({by_handle} by handle, "
             f"{result.leads_matched - by_handle} by name)"]
    if result.ambiguous:
        lines.append(f"  AMBIGUOUS {len(result.ambiguous)} — attached nothing, "
                     f"because a stranger's posts make a hook that is verified, "
                     f"dated and about somebody else:")
        lines.extend(f"    {a}" for a in result.ambiguous)
    if result.unused_pools:
        lines.append(f"  {len(result.unused_pools)} corpus entry(s) matched no "
                     f"lead on this list, which is normal when the dump is "
                     f"wider than the batch")
    if result.unmatched_leads:
        lines.append(f"  {len(result.unmatched_leads)} lead(s) got no corpus — "
                     f"they research exactly as they did before")
    if expect is not None and result.leads_matched < expect:
        lines.append(f"  SHORT expected at least {expect} matched lead(s), "
                     f"got {result.leads_matched}")
    return "\n".join(lines)


def short(result: Attached, expect: int | None) -> bool:
    return expect is not None and result.leads_matched < expect
