"""
Gate 0 floor evaluation — the machine-checkable half.

UAE track (Jul 13, 2026 — see docs/uae-track/03-targeting-and-sourcing.md).
All five Gate 0 checks must be true; any hard fail = Disqualified:
- UAE-based:       physically in the UAE, not just serving the region
- Funnel floor:    a live sales page, checkout, course, or paid digital offer
- Activity floor:  posted, emailed, or launched something in the last 30 days
- Audience floor:  1,500+ on their largest owned or social channel
- Price floor:     a live program at AED 5,000+ (added 2026-07-28)

A crawler can settle the funnel-existence question and take audience size
as input. UAE residency and activity need a web search + judgment — those
come back as NEEDS_REVIEW for the Claude layer, never guessed here.

WHY THE PRICE FLOOR EXISTS (2026-07-28). The market study's purchasing-power
indicator is a measured FAIL: ICF puts average coach revenue at $49,283/yr and
most UAE coaches sit under the AED 375,000 VAT line. The old response to that
was to price The First Five low enough for a broke market to afford, which is
solving a targeting problem with a discount. The floor is the other answer:
write to the half of the market that can pay. A coach with an AED 8,000 program
closing one in four takes AED 2,000 per call taken and pays 900 for it; a coach
with an AED 800 program cannot make that arithmetic work at ANY price we could
charge, so a reply from her was never revenue.

The floor is on her HIGHEST live program, not her cheapest thing. A coach with
a AED 299 workshop and AED 6,600 1:1 containers passes on the containers.
"""

import re
from dataclasses import dataclass, field

AUDIENCE_FLOOR = 1500
ACTIVITY_WINDOW_DAYS = 30

# The lead's top live program must be worth at least this much for the per-call
# economics to work for HER, which is the only reason she would ever pay.
PROGRAM_PRICE_FLOOR_AED = 5000

# AED is HARD-PEGGED to USD at 3.6725 by the UAE central bank — that is not an
# estimate and does not move. Everything else floats, so it gets a plausible
# band instead of a point rate (see to_aed_band).
PEG_USD_AED = 3.6725

# Wide, deliberately pessimistic/optimistic bands for floating currencies. They
# are not exchange rates and must never be used to quote or report a number —
# they exist ONLY so the floor can be settled when a price is unambiguous at
# every rate in the band (GBP 8,999 clears at any of them; GBP 200 fails at any
# of them). Anything landing inside the band goes to NEEDS_REVIEW for a human
# or an agent with a live rate.
_FX_BANDS_AED = {
    "AED": (1.0, 1.0),
    "USD": (PEG_USD_AED, PEG_USD_AED),
    "GBP": (3.8, 5.4),
    "EUR": (3.2, 4.6),
    "SAR": (0.9, 1.1),
    "INR": (0.035, 0.055),
}


def to_aed_band(amount: float, currency: str) -> tuple[float, float] | None:
    """Convert a price to a (low, high) AED band, or None for a currency we
    have no band for. A point value comes back as (x, x) for the pegged pair.

    Returning a band rather than a number is the honest shape: the only
    question this module asks of a price is which side of AED 5,000 it is on,
    and for most prices every plausible rate agrees.
    """
    band = _FX_BANDS_AED.get((currency or "").strip().upper())
    if band is None:
        return None
    return (amount * band[0], amount * band[1])

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
    top_program_price: float | None = None,
    top_program_currency: str = "AED",
    price_evidence: str = "",
) -> FloorResult:
    """top_program_price is the HIGHEST-priced live program found on the walk,
    in top_program_currency. Leave it None when the walk could not see a price
    at all (48 of 122 walked leads show none) — that is NEEDS_REVIEW, never a
    guess and never a silent pass.
    """
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

    # --- Price floor: can the per-call economics work for HER? ---
    if top_program_price is None:
        msg = (
            f"No confirmed program price. UAE floor is AED {PROGRAM_PRICE_FLOOR_AED:,} on her "
            "HIGHEST live program (not her cheapest workshop or digital product). 48 of 122 "
            "walked leads show no visible price — settle it from a checkout, an application "
            "page, a rate card, or a directory listing before promoting."
        )
        if price_evidence:
            msg += f" {price_evidence[:200]}"
        result.verdicts.append(FloorVerdict("price_floor", NEEDS_REVIEW, msg))
    else:
        band = to_aed_band(top_program_price, top_program_currency)
        cur = (top_program_currency or "").strip().upper()
        detail = f"{cur} {top_program_price:,.0f}"
        if price_evidence:
            detail += f" ({price_evidence[:120]})"
        if band is None:
            result.verdicts.append(FloorVerdict(
                "price_floor", NEEDS_REVIEW,
                f"{detail} — no conversion band for currency {cur!r}. Convert to AED by hand "
                f"with a live rate and re-run; the floor is AED {PROGRAM_PRICE_FLOOR_AED:,}.",
            ))
        elif band[0] >= PROGRAM_PRICE_FLOOR_AED:
            result.verdicts.append(FloorVerdict(
                "price_floor", PASS,
                f"{detail} = AED {band[0]:,.0f}+ — clears the AED "
                f"{PROGRAM_PRICE_FLOOR_AED:,} floor at every rate in the band",
            ))
        elif band[1] < PROGRAM_PRICE_FLOOR_AED:
            result.verdicts.append(FloorVerdict(
                "price_floor", FAIL,
                f"{detail} = at most AED {band[1]:,.0f} — under the AED "
                f"{PROGRAM_PRICE_FLOOR_AED:,} floor at every rate in the band. She cannot make "
                "AED 900/call work at any price we could charge. Gate 0 fail unless a HIGHER "
                "live program exists that the walk missed.",
            ))
        else:
            result.verdicts.append(FloorVerdict(
                "price_floor", NEEDS_REVIEW,
                f"{detail} = AED {band[0]:,.0f}–{band[1]:,.0f}, which straddles the AED "
                f"{PROGRAM_PRICE_FLOOR_AED:,} floor. The band is deliberately wide and is not "
                "an exchange rate — settle this one with a live rate, by hand.",
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


# ---------------------------------------------------------------------------
# Feeding the price floor from the walk's own scraped prices
# ---------------------------------------------------------------------------

_PRICE_TOKEN_RE = re.compile(
    r"^(?:(?P<sym>[$£€])|(?P<code1>USD|AED|GBP|EUR)\s?)?"
    r"(?P<num>[\d,]+(?:\.\d{1,2})?)"
    r"\s?(?P<code2>AED|USD)?$"
)
_SYMBOL_CCY = {"$": "USD", "£": "GBP", "€": "EUR"}


def parse_price_token(raw: str) -> tuple[float, str] | None:
    """"AED 6,600" / "$8,999" / "1500 AED" → (6600.0, "AED"). None if the
    token has no currency we can name — an unlabelled number is not a price,
    and "2026" and "1,500" are all over a coaching site."""
    m = _PRICE_TOKEN_RE.match((raw or "").strip())
    if not m:
        return None
    ccy = (
        _SYMBOL_CCY.get(m.group("sym") or "")
        or m.group("code1")
        or m.group("code2")
    )
    if not ccy:
        return None
    try:
        return float(m.group("num").replace(",", "")), ccy.upper()
    except ValueError:
        return None


def price_floor_input(pages: list[tuple[str, list[str]]]) -> dict:
    """Turn the walk's scraped price tokens into evaluate_floors() kwargs —
    but ONLY ever upward.

    `pages` is [(url, [price_token, ...]), ...] for the lead's OWN pages
    (external and errored pages filtered out by the caller).

    The asymmetry is deliberate and load-bearing. Confirming a rich lead
    automatically is safe: if the highest price on her site clears AED 5,000 at
    every rate in the band, no scraper noise makes that wrong in the direction
    that matters. Auto-KILLING on a scraped maximum is NOT safe — a coach whose
    site shows a AED 299 workshop may sell AED 20,000 1:1 by application,
    off-page, and a Gate 0 hard fail is permanent. So a below-floor maximum is
    reported as evidence and left at NEEDS_REVIEW for the qualifier to settle
    against a rate card, an application page, or a directory listing.
    """
    best_aed_low: float | None = None
    best: tuple[float, str, str] | None = None    # (amount, currency, url)
    for url, tokens in pages:
        for tok in tokens:
            parsed = parse_price_token(tok)
            if not parsed:
                continue
            amount, ccy = parsed
            band = to_aed_band(amount, ccy)
            if band is None:
                continue
            if best_aed_low is None or band[0] > best_aed_low:
                best_aed_low, best = band[0], (amount, ccy, url)

    if best is None or best_aed_low is None:
        return {}

    amount, ccy, url = best
    if best_aed_low >= PROGRAM_PRICE_FLOOR_AED:
        return {
            "top_program_price": amount,
            "top_program_currency": ccy,
            "price_evidence": f"scraped from {url}",
        }
    return {
        "price_evidence": (
            f"highest price seen on the walk: {ccy} {amount:,.0f} on {url} — below the "
            "floor, but a scraped maximum is NOT proof of her top program "
            "(application-only 1:1 work is routinely off-page). Confirm by hand "
            "before killing."
        )
    }
