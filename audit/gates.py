"""
Gate 0 floor evaluation — the machine-checkable half.

UAE track (Jul 13, 2026 — see docs/uae-track/03-targeting-and-sourcing.md).
All four Gate 0 checks must be true; any hard fail = Disqualified:
- UAE-based:       physically in the UAE, not just serving the region
- Funnel floor:    a live sales page, checkout, course, or paid digital offer
- Activity floor:  posted, emailed, or launched something in the last 30 days
- Audience floor:  1,500+ on their largest owned or social channel

A crawler can settle the funnel-existence question and take audience size
as input. UAE residency and activity need a web search + judgment — those
come back as NEEDS_REVIEW for the Claude layer, never guessed here.
"""

from dataclasses import dataclass, field

AUDIENCE_FLOOR = 1500
ACTIVITY_WINDOW_DAYS = 30

PASS, FAIL, NEEDS_REVIEW = "pass", "fail", "needs_review"


@dataclass
class FloorVerdict:
    name: str
    verdict: str          # pass | fail | needs_review
    evidence: str


@dataclass
class FloorResult:
    verdicts: list[FloorVerdict] = field(default_factory=list)

    @property
    def hard_fail(self) -> bool:
        return any(v.verdict == FAIL for v in self.verdicts)

    def as_dict(self) -> dict:
        return {
            "hard_fail": self.hard_fail,
            "floors": [
                {"floor": v.name, "verdict": v.verdict, "evidence": v.evidence}
                for v in self.verdicts
            ],
        }


def evaluate_floors(
    *,
    bio_link_alive: bool,
    bio_link_error: str,
    offer_evidence: list[str],
    email_capture_anywhere: bool,
    followers: int | None = None,
) -> FloorResult:
    result = FloorResult()

    # --- Entry link alive (sourcing gate: dead first click) ---
    if bio_link_alive:
        result.verdicts.append(FloorVerdict("bio_link_alive", PASS, "Entry link loaded"))
    else:
        # A dead entry link is not a disqualifier — it's a Tier A finding candidate.
        result.verdicts.append(FloorVerdict(
            "bio_link_alive", NEEDS_REVIEW,
            f"Entry link failed to load ({bio_link_error[:120]}). Verify logged-out by hand: "
            "hard 404 = Tier A opener candidate, permission wall = not openable.",
        ))

    # --- Funnel floor: a paid offer behind the link (Gate 0 hard requirement) ---
    if offer_evidence:
        result.verdicts.append(FloorVerdict(
            "funnel_floor", PASS, "; ".join(offer_evidence[:3]),
        ))
    else:
        result.verdicts.append(FloorVerdict(
            "funnel_floor", NEEDS_REVIEW,
            "No paid offer or checkout visible from the crawl. Could be login-walled — "
            "confirm by hand before dropping. If genuinely nothing: call-only coach, "
            "nothing to fix, Gate 0 fail → Disqualified.",
        ))

    # --- Audience floor ---
    if followers is None:
        result.verdicts.append(FloorVerdict(
            "audience_floor", NEEDS_REVIEW,
            f"Audience size not supplied. UAE floor is {AUDIENCE_FLOOR:,} on their largest "
            "owned or social channel (a 2K UAE-focused list is worth what 8K is in the US).",
        ))
    elif followers >= AUDIENCE_FLOOR:
        result.verdicts.append(FloorVerdict(
            "audience_floor", PASS, f"{followers:,} on largest channel",
        ))
    else:
        result.verdicts.append(FloorVerdict(
            "audience_floor", FAIL,
            f"{followers:,} — under the {AUDIENCE_FLOOR:,} UAE floor. Gate 0 fail unless "
            "a larger owned channel (list, podcast, community) clears it.",
        ))

    # --- Activity + UAE residency: not machine-checkable ---
    result.verdicts.append(FloorVerdict(
        "activity_floor", NEEDS_REVIEW,
        f"Verify via web search: posted, emailed, or launched something in the last "
        f"{ACTIVITY_WINDOW_DAYS} days. Dormant operators do not buy.",
    ))
    result.verdicts.append(FloorVerdict(
        "uae_based", NEEDS_REVIEW,
        "Verify: physically based in Dubai, Abu Dhabi, Sharjah, or elsewhere in the UAE. "
        "'Serves clients in the region' does not count.",
    ))

    # --- Context signal, not a gate ---
    result.verdicts.append(FloorVerdict(
        "email_capture_anywhere",
        PASS if email_capture_anywhere else NEEDS_REVIEW,
        "Email capture found on at least one crawled page." if email_capture_anywhere
        else "No email capture visible anywhere in the crawl (Stop 5 signal, needs felt-cost framing).",
    ))

    return result
