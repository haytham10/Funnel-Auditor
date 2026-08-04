"""The checks that make a model-written email safe to send.

The drafting model gets real freedom: it authors the hook and it re-voices the
anchor lines so the beats connect. That freedom is only affordable because
everything it could get wrong is mechanically catchable, and caught here before
the email reaches an upload file.

Three families of check:

**Traceability.** Every number in the body must be true of some real client
result (`anchors.all_numbers`), and any number sitting next to a named segment
must belong to that segment (`check_attribution`). These are two different
failures: invention, and relabelling. The client results are real, they come up
on a call, and these coaches compare emails — 7 of 50 survivors on the last list
were the same people arriving from two directories. Either failure is the tell
that the whole email is fabricated, hook included.

**Claim preservation.** The model may re-voice an anchor. It may not quietly
drop what the anchor promised. The offer beat has to still offer ten names; the
close has to still ask for fifteen minutes and still carry the reason only a
conversation can answer. A close that loses its second half is how reply-to-call
went 0-for-9 in the first place.

**Voice.** No em-dashes, no operator jargon, no weak closers, proper sign-off,
second person before the first digit. These were all rules before this module
existed and were enforced by whoever was paying attention.

Batch-level checks run across the whole upload file, because the failure they
catch is invisible one email at a time: three of the five beats are drawn from
a pool of twelve sentences, and two coaches who compare notes currently see the
same offer, close and ps word for word.

Everything fails closed. A check that cannot run is a FAIL, not a pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from audit.draft_lint import bare_links, EM_DASH

WORD_MIN, WORD_MAX = 67, 95
FIXED_LINE_SHARE_CAP = 0.35
BRIDGE_PHRASE_CAP = 0.10
MIN_BATCH_FOR_SHARES = 8

# The hook is the only beat nobody writes in advance, so it is the only one
# that gets squeezed when the four drawn lines are long. Twelve words is a
# short hook but a real one ("Saw your talk on why senior people stall").
MIN_HOOK_WORDS = 12


def word_count(text: str) -> int:
    """The one word counter. Everything that reasons about length uses it.

    There used to be two. This function's rule counts a separated figure as two
    words ("AED 91,500" -> "AED", "91", "500") while `str.split()` counts it as
    one, and the allocator's length guards used `split()` while the check that
    actually rejects an email used this. A guard that counts low fails in the
    shipping direction: it says the combination fits, and the linter then
    refuses the email nobody can shorten. Latent rather than live — every
    current line writes "AED 77k" — but `_UNSEPARATED` below *requires* the
    comma form on any four-digit currency figure, so the trap was armed and
    waiting for the first line that used one.
    """
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def hook_room(beats: dict) -> int:
    """Words left for the hook once the four drawn lines are in place.

    Measured on the assembled body rather than by summing the four lines,
    because the body carries a greeting and a sign-off that the count in
    `check_voice` includes and a sum of lines does not. That gap was three
    words and it was load-bearing: the sync-time guard read the live bank as
    leaving 13 words for a hook when the real figure was 10, under its own
    12-word floor, so the one combination it existed to catch went through and
    would have been rejected downstream as a too-long draft — pointing at the
    hook instead of at the lines that squeezed it.

    Assumes a one-word first name, as the export's own preview does. A
    two-word first name costs one more word than this predicts.
    """
    from outbound.export import assemble_body

    body = assemble_body(
        {beat: beats.get(beat, "") or "" for beat in ("identity", "offer", "cta", "ps")},
        greeting_name="Name")
    return WORD_MAX - word_count(body)

# Words that give away an operator writing to a civilian.
#
# Matched on WORD BOUNDARIES, with an explicit suffix where a stem is meant.
# A raw substring test drops real emails and gives a false reason for it: the
# hook quotes the lead's own words, so "optimism" tripped "optimi", "auditorium"
# and "auditioning" tripped "audit", and "Detroit" tripped "ROI". Each of those
# rejected a whole email and named a jargon word that was never in it, which is
# unfixable by the drafter because the complaint is not true.
JARGON = (
    r"funnels?", r"conversions?", r"converts?", r"converting",
    r"audits?", r"auditing", r"sequences?", r"cadences?",
    r"pipelines?", r"outreach", r"prospecting", r"lead magnets?",
    r"cold emails?", r"optimi[sz]e[ds]?", r"optimi[sz]ing",
    r"optimi[sz]ations?", r"leverage[ds]?", r"leveraging",
    r"synerg(?:y|ies|istic)", r"touchpoints?", r"top of funnel",
    r"drip", r"nurture", r"CRM", r"ICP", r"KPIs?", r"ROI",
)
_JARGON_RE = re.compile(r"\b(?:" + "|".join(JARGON) + r")\b", re.I)

# Closers that hand the reader a free exit and ask for nothing.
WEAK_CLOSERS = (
    "no pressure", "no rush", "whenever timing", "whenever works",
    "if now's not the time", "feel free to ignore", "no worries either way",
    "let me know if", "happy to share more", "just let me know",
)

GENDERED = re.compile(r"\b(her|hers|she|his|him|he)\b", re.I)

SIGN_OFF = "Haytham"

# Claim tokens each beat must still carry after the model has re-voiced it.
# Each entry is (human label, pattern) and ALL must survive.
CLAIM_TOKENS: dict[str, list[tuple[str, re.Pattern]]] = {
    "offer": [
        ("ten names", re.compile(r"\b(10|ten)\b[^.]{0,40}\bnames?\b|\bnames?\b[^.]{0,40}\b(10|ten)\b", re.I)),
        ("already pulled", re.compile(r"\b(already|pulled|found|sitting|got)\b", re.I)),
    ],
    "cta": [
        ("fifteen minutes", re.compile(r"\b(15|fifteen)\b\s*(-|\s)?\s*min", re.I)),
        ("a clock on the deliverable", re.compile(
            r"same day|that day|before the call ends|within a day|inside a day|"
            r"same-day|by tomorrow|the next day", re.I)),
        ("why these ten", re.compile(
            r"why these|not the other|how i picked|ruled the other|"
            r"what ruled|why those", re.I)),
    ],
    # ONE entry, matching either of two moves, because every entry in a beat's
    # list has to match and these are alternatives rather than requirements.
    #
    # It used to name one move, and that is why all four ps lines were the same
    # move: the token permitted nothing else, so `copy_sync.validate` rejected
    # any ps that did not hand back an exit. A bank monotone by accident of a
    # regex reads as a bank monotone by choice, and nobody looking at the four
    # lines could tell which it was.
    #
    # The beat's job is unchanged — make not replying cheap, which is what makes
    # replying honest. What widened is HOW: granting permission to decline is
    # one way, and making the email itself cost nothing to have received is
    # another. Both answer the reader's question. Neither is a promise about
    # what happens next, which matters: Smartlead owns the sequence steps, so a
    # ps promising no follow-up would be false the moment a batch is uploaded.
    "ps": [
        ("a costless no or a costless read", re.compile(
            r"costs? you nothing|fine answer|no hard feelings|nothing to "
            r"unsubscribe|not a list|leave it there|a no here|"
            r"no pitch deck|read your work|before i wrote|before writing", re.I)),
    ],
}

_NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*(?:k\b|%)?", re.I)
# "21st", "3rd", "2nd" — a date reference, not a quantity claimed about a
# client. A hook legitimately citing the date of a post would otherwise fail
# traceability for a number nobody is asserting anything with.
_ORDINAL_RE = re.compile(r"\b\d+(?:st|nd|rd|th)\b", re.I)
_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "ninety": 90, "hundred": 100,
}
_UNSEPARATED = re.compile(r"\b(?:AED|USD|\$)\s*(\d{4,})\b", re.I)


@dataclass
class Result:
    """One email's verdict. `failures` blocks; `warnings` are judgement calls."""
    name: str = ""
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures

    def line(self) -> str:
        head = "PASS" if self.passed else "FAIL"
        detail = ""
        if self.failures:
            detail = " | " + "; ".join(self.failures)
        elif self.warnings:
            detail = " | warn: " + "; ".join(self.warnings)
        return f"LINT {self.name}: {head}{detail}"

    def report(self) -> str:
        lines = [self.line()]
        for failure in self.failures:
            lines.append(f"  FAIL  {failure}")
        for warning in self.warnings:
            lines.append(f"  warn  {warning}")
        return "\n".join(lines)


# A sentence ends at .!? — and the terminator may sit INSIDE a closing quote,
# which is exactly how a hook ends. `re.split(r"(?<=[.!?])\s+", ...)` was
# written twice in this file and both copies got that wrong: a hook ending
# `...airplane mode for ten days."` glued the following greeting or beat onto
# it, so `check_voice` reported a 40-word sentence that nobody had written and
# `check_attribution` looked for a segment noun across two sentences at once.
# Both are false positives that land on the one beat the machine went to the
# most trouble to certify.
# Alternatives rather than `[…]*`, because `re` allows only a fixed-width
# lookbehind and a consuming version would eat the closing quote off the
# sentence it belongs to. Two closers covers `."` and `.")`.
_CLOSER = r"[\"”’')\]]"
_SENTENCE_END = re.compile(
    rf"(?<=[.!?])\s+|(?<=[.!?]{_CLOSER})\s+|(?<=[.!?]{_CLOSER}{_CLOSER})\s+")


def split_sentences(text: str) -> list[str]:
    """One splitter, used everywhere a sentence is the unit.

    Defined once for the reason `audit/draft_lint.py` exists: a rule written
    twice drifts, and these two copies had already drifted into the same bug.
    """
    return [part for part in _SENTENCE_END.split(text or "") if part.strip()]


def numbers_in(text: str) -> list[tuple[str, float]]:
    """Every quantity in the text, as (as-written, value).

    Handles "36,000", "36k", "3.2%", and spelled-out numbers up to a hundred,
    because "ten names" and "10 names" make the same claim and a checker that
    only sees one of them is not a checker.
    """
    found: list[tuple[str, float]] = []
    text = _ORDINAL_RE.sub(" ", text or "")
    for match in _NUMBER_RE.finditer(text):
        raw = match.group(0).strip()
        cleaned = raw.replace(",", "").rstrip("%").strip()
        multiplier = 1
        if cleaned.lower().endswith("k"):
            cleaned = cleaned[:-1].strip()
            multiplier = 1000
        try:
            found.append((raw, float(cleaned) * multiplier))
        except ValueError:
            continue
    for word, value in _WORD_NUMBERS.items():
        if re.search(rf"\b{word}\b", text, re.I):
            found.append((word, float(value)))
    return found


def _licensed(value: float, allowed: set) -> bool:
    allowed_values = {float(n) for n in allowed}
    allowed_values |= {round(v, 1) for v in allowed_values}
    return value in allowed_values or round(value, 1) in allowed_values


def mask_quoted_figures(body: str, hook: str, hook_quote: str) -> str:
    """The body with the hook's quoted figures blanked out, and nothing else.

    Sparing the figure by value would spare it everywhere — the identity beat
    included, which is the one place a relabelled client result actually does
    damage. So the substitution happens inside the hook beat's own text and the
    result is spliced back, and every other check still reads the real body.
    """
    quoted = quoted_numbers(hook, hook_quote)
    if not quoted or hook not in body:
        return body
    masked = hook
    for raw in sorted(quoted, key=len, reverse=True):
        masked = re.sub(rf"(?<!\w){re.escape(raw)}(?!\w)", "#", masked)
    return body.replace(hook, masked, 1)


def quoted_numbers(hook: str, hook_quote: str) -> set:
    """Figures the hook beat took verbatim from the certified quote.

    **Quoting is not claiming**, and until 2026-08-01 this rule could not tell
    the difference. `check_numbers` exists to stop us inventing a client result
    or wearing somebody else's; it has no business deleting "70.3", "2023",
    "11 years" and "27 years" from a hook, because those are the RECIPIENT's
    facts, read off their own page, and the hook beat's entire job is to prove
    we read it.

    Six of twelve drafts in `2026-08-01-q1` had to alter a hook a verifier had
    certified word for word, and both drafters solved the digits by moving them
    into the subject line, which is not digit-checked. That works, and it is
    backwards.

    Narrow on both axes deliberately. A figure qualifies only if it is in the
    hook beat **and** in the certified quote — so a number the drafter added
    while paraphrasing is still caught, and the exemption cannot leak into the
    identity beat, which is where a relabelled client result would actually do
    damage.
    """
    if not (hook or "").strip() or not (hook_quote or "").strip():
        return set()
    cited = {raw.lower() for raw, _ in numbers_in(hook_quote)}
    return {raw for raw, _ in numbers_in(hook) if raw.lower() in cited}


def check_numbers(body: str, allowed: set) -> list[str]:
    """Every digit must be true of some real client result.

    `allowed` is the widened set: every number in the fact table, plus the
    aggregate, plus the offer's own numbers. A year or a time of day is not
    exempt — the email has no business carrying either, so an unexplained
    number is a failure regardless of what it looks like.

    Pass `mask_quoted_figures`' output as `body` to exempt figures the hook beat
    quoted from its certified source. The exemption is a property of *where* the
    figure sits, not of its value, so it is applied to the text rather than
    handed to this function as a set — a set would spare the same digits in the
    identity beat, which is the one place they would do real harm.

    This catches invention. Relabelling is a different failure and is caught by
    `check_attribution`, because a number can be entirely real and still be
    attached to the wrong kind of coach.
    """
    return [
        f'number "{raw}" is not true of any client result (invented)'
        for raw, value in numbers_in(body)
        if not _licensed(value, allowed)
    ]


_SEGMENT_RE = re.compile(
    r"\b(business|leadership|life|mindset|career|health|fitness|executive)\s+coach",
    re.I,
)


def check_attribution(body: str, facts) -> list[str]:
    """A number sitting next to a named segment must belong to that segment.

    This is the rule the fact table exists for. There are three honest ways to
    vary an identity beat — reframe, widen, or cite research — and none of them
    is re-attributing one segment's result to another to make the match look
    tighter. "A health coach in Dubai closed AED 120,000" is a Business number
    wearing a Health label, and it surfaces the moment two coaches compare
    emails or one of them asks about it on a call.

    Checked per sentence, because that is the scope over which a reader
    attaches a number to a noun.

    A quoted figure is exempt here for the same reason it is exempt from
    `check_numbers`, and by the same mechanism: `check_email` hands this the
    masked body. "Your 27 years as a business coach" is their sentence, and
    refusing it would push the drafter into paraphrasing a citation an
    independent verifier certified.
    """
    from outbound.anchors import allowed_numbers

    problems = []
    for sentence in split_sentences(body):
        match = _SEGMENT_RE.search(sentence)
        if not match:
            continue
        segment = match.group(1).capitalize()
        if segment not in facts.results:
            continue
        permitted = allowed_numbers(facts, segment)
        for raw, value in numbers_in(sentence):
            if not _licensed(value, permitted):
                problems.append(
                    f'"{raw}" is attributed to a {segment.lower()} coach but is '
                    f"not that segment's result (relabelled)"
                )
    return problems


_CITY_RE = re.compile(r"\b(dubai|abu dhabi|sharjah|ajman)\b", re.I)

# Spelled-out numbers below this are prose, not claims. "every one with somebody
# who could sign off" and "picked one at a time" both put a bare `one` through
# `numbers_in`, and treating that as a figure would fail three good bank lines.
# Justified from the corpus rather than by taste: every real claim of one in
# this bank is written as a digit ("their first meeting in week 1").
_PROSE_NUMBER_CEILING = 2


def _renderings(column: str, value) -> list[re.Pattern]:
    """Every way an honest sentence may state one column's value.

    This table is where the work of claim-checking actually lives, and its job
    is to be GENEROUS. A rendering it fails to know about is a true sentence
    the gate rejects, and a gate that rejects true sentences teaches drafters
    to route around it — which is worse than the invented number it was built
    to catch.
    """
    if isinstance(value, bool):
        # `still_working`. There is no figure, so this is checked as a phrase.
        return [re.compile(r"still (working|with) (with )?them|working with them (still|now)"
                           r"|and I'm still", re.I)] if value else []

    if isinstance(value, str):
        # A period. The figure must appear NEXT TO ITS UNIT: a bare 2 from "2 of
        # them signed" must not satisfy a 60-day requirement, which is the one
        # way this check could quietly pass a sentence that says nothing.
        patterns = []
        for amount in sorted(_period_amounts(value)):
            n, unit = amount
            patterns.append(re.compile(rf"\b{n}\s*{unit}s?\b", re.I))
            if n == 1:
                # "in a month", "inside a week" — the article form of one.
                patterns.append(re.compile(rf"\b(a|one)\s+{unit}\b", re.I))
        return patterns

    if not isinstance(value, (int, float)):
        return []

    patterns = [re.compile(rf"\b{_with_separators(value)}\b"),
                re.compile(rf"\b{int(value)}\b")]
    word = _NUMBER_WORDS.get(int(value))
    if word:
        patterns.append(re.compile(rf"\b{word}\b", re.I))
    if isinstance(value, int) and value >= 1000 and value % 1000 == 0:
        patterns.append(re.compile(rf"\b{value // 1000}\s*k\b", re.I))
    if column in ("first_meeting_days", "first_client_days") and value > 0:
        # "inside a week" for day 7, "in week 2" for day 10. Exact under the
        # "inside" framing rather than the rounding this module refuses
        # elsewhere: a first meeting on day 10 really did fall inside week 2.
        weeks = -(-int(value) // 7)
        patterns.append(re.compile(rf"\bweek\s*{weeks}\b", re.I))
        if weeks == 1:
            patterns.append(re.compile(r"\b(a|one)\s+week\b", re.I))
    return patterns


def _period_amounts(text: str) -> set[tuple[int, str]]:
    """"60 days" -> {(60, "day"), (2, "month")}. Exact conversions only, the
    same rule `anchors.period_numbers` holds: 60 days is 2 months, 45 days is
    not 6 weeks."""
    out: set[tuple[int, str]] = set()
    for amount, unit in re.findall(r"(\d+)\s*(day|week|month|year)s?", text or "", re.I):
        value, unit = int(amount), unit.lower()
        out.add((value, unit))
        if unit == "day":
            if value % 7 == 0:
                out.add((value // 7, "week"))
            if value % 30 == 0:
                out.add((value // 30, "month"))
        elif unit == "week":
            out.add((value * 7, "day"))
        elif unit == "month":
            out.add((value * 30, "day"))
    return out


def _with_separators(value) -> str:
    return f"{int(value):,}" if isinstance(value, int) else str(value)


_NUMBER_WORDS = {v: k for k, v in _WORD_NUMBERS.items()}


def check_identity_claim(identity: str, claim) -> list[str]:
    """Does the authored identity sentence assert what it was dealt, and
    nothing more?

    The identity beat is the one beat the drafter WRITES rather than re-voices.
    That is not a licence this function grants — `check_bridge` below requires a
    second-person clause before the first digit, and two-thirds of the bank's
    identity lines open on a bare stat, so most leads already get a sentence the
    model composed. What was missing was any check on what that sentence claims,
    and a wrong figure went out under a real segment's name for a month because
    of it.

    So the constraint moved from the words to the claim. This asserts exactly
    four things:

      1. every figure the claim declares is present, in any licensed rendering
      2. the segment noun is there when the claim is scoped to one, and is NOT
         there when the claim is widened
      3. no figure appears that the claim does not license
      4. no fact-table city appears except this claim's own

    And it must NOT assert — this list is the contract with the drafter, and
    breaking it silently re-imposes the verbatim rule by another route:

      - no string similarity to the reference line, and no shared-word floor
      - nothing about word order, clause structure or sentence count
      - not that the reference line's phrasing survives in any form
      - not the period's unit: 60 days and 2 months are the same fact
      - no length constraint beyond the global word budget

    KNOWN LIMIT, stated because a gate that oversells itself is worse than one
    that does not exist: this is set membership, not binding. "2 of them signed"
    against a claim whose clients is 5 passes if 2 is licensed as the period
    figure. Binding a figure to its noun is not mechanically reachable, and
    `check_attribution` has the same limit by design. That is what the cold read
    is for.
    """
    if claim is None:
        return ["identity beat has no claim spec, so its figures are unchecked "
                "(the line is missing its Claim in Copy Assets)"]
    text = identity or ""
    if not text.strip():
        return ["identity beat is missing"]

    problems: list[str] = []

    for column, value in claim.figures.items():
        patterns = _renderings(column, value)
        if not patterns:
            continue
        if not any(p.search(text) for p in patterns):
            shown = value if not isinstance(value, bool) else "still working with them"
            problems.append(
                f'identity beat drops the claim: {column} = {shown} is not in it')

    if claim.names_segment:
        wanted = claim.segment.lower()
        if not re.search(rf"\b{re.escape(wanted)}\s+coach", text, re.I):
            problems.append(
                f'identity beat never says "{wanted} coach", but its claim is '
                f"scoped to that segment")
    elif not claim.aggregate:
        match = _SEGMENT_RE.search(text)
        if match:
            # Not because naming it would be false — these ARE that segment's
            # figures. Because a widened line is drawn from the generic pool and
            # goes to leads of every segment, so a named reference group is a
            # mismatch for most of the people who receive it. That is the whole
            # difference between widening and matching.
            problems.append(
                f'identity beat says "{match.group(1).lower()} coach", but this '
                f"claim is widened: the line is dealt across segments, so naming "
                f"one puts the wrong reference group in front of most readers")

    licensed = claim.numbers()
    for raw, value in numbers_in(text):
        if value < _PROSE_NUMBER_CEILING and not raw[:1].isdigit():
            continue        # bare spelled "one" is prose, see the ceiling above
        if not _licensed(value, licensed):
            problems.append(
                f'identity beat cites "{raw}", which its claim does not license '
                f"(claim is {claim.raw})")

    # Keyed on whether the line DECLARED a city, not on whether its row happens
    # to have one — every row does. Declaring `city` is the line saying "I
    # assert where this happened"; naming one without declaring it is an
    # undeclared claim, and it is invisible to `check_attribution`, which only
    # ever looks at numbers.
    declared_city = "city" in claim.columns
    for city in {m.group(0).title() for m in _CITY_RE.finditer(text)}:
        if declared_city and city.lower() != (claim.city or "").lower():
            problems.append(
                f'identity beat says {city}, but this result happened in '
                f"{claim.city}")
        elif not declared_city:
            problems.append(
                f"identity beat names {city}, which its claim does not assert "
                f"(claim is {claim.raw})")
    return problems


def check_claims(beats: dict[str, str]) -> list[str]:
    """Did re-voicing drop something the anchor promised?"""
    problems = []
    for beat, tokens in CLAIM_TOKENS.items():
        text = beats.get(beat, "")
        if not text.strip():
            problems.append(f"{beat} beat is missing")
            continue
        for label, pattern in tokens:
            if not pattern.search(text):
                problems.append(f"{beat} beat lost its claim: {label}")
    return problems


def check_bridge(identity: str) -> list[str]:
    """A second-person clause must land before the first digit.

    The rule your own analysis proved and the file never enforced: 22 of 31
    identity lines opened on a bare stat, which makes the proof a resume line
    rather than something about the reader. A hook followed by a naked number
    is two unrelated paragraphs.
    """
    if not identity.strip():
        return ["identity beat is missing"]
    match = re.search(r"\d", identity)
    head = identity[: match.start()] if match else identity
    if not re.search(r"\b(you|your|you're|yours)\b", head, re.I):
        if match:
            return ["identity beat reaches a number before it turns to the reader"]
        return ["identity beat never addresses the reader"]
    return []


def check_voice_fragment(text: str) -> list[str]:
    """The voice rules that are about the WORDS, applicable to one beat.

    Split out of `check_voice` so the hook stage can run them on a proposal
    before an independent verifier certifies its exact wording. Six of twelve
    drafts on `2026-08-01-q1` had to alter text a verifier had confirmed word
    for word — an em-dash, spaced hyphens, "touchpoints" — because every one of
    these rules ran three stages after the point where honouring them was free.

    A fragment has no sign-off, no paragraph count and no word budget of its
    own, so those stay in `check_voice`. Nothing is duplicated: that function
    calls this one.
    """
    failures = []

    if EM_DASH in text:
        failures.append("em-dash present")

    links = bare_links(text)
    if links:
        failures.append(f"bare link or address: {', '.join(links[:3])}")

    lowered = text.lower()
    for found in sorted({m.group(0).lower() for m in _JARGON_RE.finditer(text)}):
        failures.append(f'operator jargon: "{found}"')
    for closer in WEAK_CLOSERS:
        if closer in lowered:
            failures.append(f'weak closer: "{closer}"')

    for match in _UNSEPARATED.finditer(text):
        failures.append(
            f'unformatted number "{match.group(0)}" reads as a merge field'
        )

    return failures


def check_voice(body: str) -> tuple[list[str], list[str]]:
    failures, warnings = [], []

    failures.extend(check_voice_fragment(body))

    if not re.search(rf"^\s*{SIGN_OFF}\s*$", body, re.M):
        failures.append(f'no "{SIGN_OFF}" sign-off on its own line')

    words = word_count(body)
    if words < WORD_MIN:
        failures.append(f"{words} words, under {WORD_MIN}")
    elif words > WORD_MAX:
        failures.append(f"{words} words, over {WORD_MAX}")

    if body.count("\n\n") < 3:
        warnings.append("fewer than four paragraphs, beats may have merged")

    sentences = split_sentences(body)
    if sentences and sum(1 for s in sentences if len(s.split()) > 28):
        warnings.append("a sentence runs past 28 words")

    return failures, warnings


def check_identity_pronouns(identity: str) -> list[str]:
    """A segment line fires across a whole segment, so a gendered pronoun in it
    is wrong about half the time. Use "them"."""
    match = GENDERED.search(identity or "")
    return [f'gendered pronoun "{match.group(0)}" in the identity beat'] if match else []


# A figure handed to a pronoun. `mine`, `theirs` and `the ones` can never have
# an antecedent a stranger reaches, because the thing being counted was only
# ever in the reference line the reader never saw. `them` and `those` are
# legitimate when the sentence already named a plural — "12 meetings, 7 of them
# signed" is fine and shipped — so those two are checked against what precedes
# them rather than banned.
_DANGLING_ALWAYS = re.compile(
    r"\b\d[\d,.]*\s*(?:k\b|%)?\s+of\s+(?:mine|theirs|the\s+ones?)\b", re.I)
_DANGLING_IF_BARE = re.compile(
    r"\b\d[\d,.]*\s*(?:k\b|%)?\s+of\s+(?:them|those|these|it)\b", re.I)
# The nouns a figure can be counted in. Deliberately not a vocabulary: any
# plural word, or any of the bank's own singular collectives, counts as an
# antecedent. The check is "was anything named", not "was the right thing named"
# — binding a figure to the correct noun is what `check_identity_claim`'s own
# docstring calls mechanically unreachable, and that is still true.
_PLURAL = re.compile(r"\b\w{3,}s\b", re.I)


def check_dangling_figure(identity: str) -> list[str]:
    """A figure in the identity beat that lost the noun it counts.

    **The failure this exists for, measured three times.** The bank's identity
    lines carry their noun and close on a grounding clause — `30 signed clients
    this year across 8 coaching practices here. That's the whole job.` The
    drafter is licensed to re-voice, replaces the grounding sentence with its
    own opener, and the noun goes out with it: `Who's right for your September
    is my job. 30 of mine signed this year, across 8 practices.`

    The claim survives, so `check_identity_claim` passes it — every licensed
    figure is present. What a stranger reads is a number counting nothing.
    `.claude/agents/draft-worker.md` has named this shape since 2026-08-01 and
    it recurred on q3 and again on `2026-08-03-icf1`, where **ten of thirty
    drafts** carried it and every cold reader stopped on the same words: "'30 of
    mine' has no antecedent a cold reader can resolve."

    Three batches of prose did not fix it, so it is a gate. It is a **FAIL**
    rather than a warning because the cold readers were unanimous, and because
    catching it here costs nothing while catching it at the cold read costs a
    drafting pass and a verifier pass per lead.

    **Scoped narrowly on purpose.** It fires on one shape — a figure handed
    straight to a bare pronoun — and not on the other ways this beat goes flat
    (stacked figures, verbless fragments, a noun-stack where the reference had a
    person). Those are real and they are the cold read's job. A gate that tried
    to judge all of them would refuse good sentences, which is the more
    expensive mistake.
    """
    text = identity or ""
    problems = []
    for match in _DANGLING_ALWAYS.finditer(text):
        problems.append(
            f'identity beat: "{match.group(0)}" counts nothing a reader can '
            f'reach — keep the noun with the figure')
    for match in _DANGLING_IF_BARE.finditer(text):
        # Only the text before it, and only within this sentence: an antecedent
        # in the previous sentence is a different sentence's noun.
        before = re.split(r"[.!?]", text[:match.start()])[-1]
        if not _PLURAL.search(before):
            problems.append(
                f'identity beat: "{match.group(0)}" has no plural noun before '
                f'it in the sentence — keep the noun with the figure')
    return problems


def check_subject(subject: str) -> list[str]:
    problems = []
    raw = subject or ""
    text = raw.strip()
    if not text:
        return ["subject is empty"]
    words = len(text.split())
    if words > 8:
        problems.append(f"subject is {words} words, over 8")
    if EM_DASH in text:
        problems.append("em-dash in subject")
    if text.endswith("?") and words <= 3:
        problems.append("subject is a bare question, reads as a template")
    # `text` was stripped above, so `text != text.strip()` was always False and
    # only the ALL CAPS half of this ever ran. Checked on the raw value instead.
    if raw != raw.strip() or text.isupper():
        problems.append("subject capitalisation is off")
    return problems


# Distinctive phrases that must not appear twice in one email. Two beats can be
# individually fine and still collide once dealt together: `b4-01` says "Not a
# scraped list" and `ps-01` says "not a list", and four lines apart in ninety
# words the same denial twice reads as protesting too much. A cold reader caught
# it on a real draft; nothing mechanical could, because neither line is at fault.
# Matched on word boundaries, for the same reason JARGON is: `"list" in text`
# fires inside realistic, specialist, listen, listing, holistic and enlist. The
# live offer line b4-01 contains "scraped list", so any ps or cta re-voiced with
# one of those ordinary words was rejected — and the stated reason was false, so
# the drafter could not act on it.
_ECHO_PHRASES = (
    r"lists?", r"pitch decks?", r"scraped", r"no hard feelings",
    r"costs? you nothing", r"worth the meeting", r"one at a time",
    # b4-01 "I pulled 10 names for you BEFORE WRITING THIS" against ps-05
    # "I read your work BEFORE I WROTE THIS ONE". Same construction, same
    # position, two sentences apart in a five-sentence email, so the ps reads as
    # a weaker restatement of the offer rather than a last note. Found by a cold
    # read on `2026-08-02-q2`, which named the PAIR rather than the wording:
    # "b4-01 and ps-05 should not be dealt to the same lead". That is exactly
    # what this list is for, and it cost an opus pass to discover because the
    # pattern was not in it.
    r"before (?:writing|I wrote) this",
)

# A readable name for a pattern that is not readable as one. Only needed where
# the regex carries syntax; every other label derives from the pattern itself.
_ECHO_LABELS = {
    r"before (?:writing|I wrote) this": "before writing this",
}
_ECHO_RES = [(p, re.compile(rf"\b{p}\b", re.I)) for p in _ECHO_PHRASES]


def check_echo(beats: dict[str, str]) -> list[str]:
    """A distinctive phrase repeated across two beats of the same email.

    Checked across offer/cta/ps only. The hook and identity beat are authored
    per lead, so a repeat there is the drafter's own doing and the voice rules
    already cover it; these three are drawn from a library, and the collision
    is a property of the PAIR rather than of either line.
    """
    problems = []
    drawn = {b: (beats.get(b) or "") for b in ("offer", "cta", "ps")}
    for phrase, pattern in _ECHO_RES:
        where = [b for b, text in drawn.items() if pattern.search(text)]
        if len(where) > 1:
            label = _ECHO_LABELS.get(
                phrase, phrase.replace(r"s?", "").replace(r"\b", ""))
            problems.append(
                f"the {' and '.join(where)} beats both say {label!r} — "
                f"re-voice one of them"
            )
    return problems


# Function words. A repeat of one of these is not a repeat anybody hears.
_SEAM_STOPWORDS = frozenset("""
a an the and or but if then so as at by for from in into of on to with without
this that these those it its they them their there we us our you your yours
i me my mine he she him his her hers who whom whose which what when where why how
is are was were be been being am do does did done doing have has had having
will would can could shall should may might must
not no nor than too very just also only about over under out up down off again once
all any both each few more most other some such own same one two
i'm i've i'd it's that's what's who's you're you'll you've they're we're
""".split())

# The copy's own subject matter. Two beats of an email about finding a coach
# their next client will both say "coach" and "client", and a rule that treats
# the bank's own vocabulary as a collision is a rule against the copy.
_SEAM_VOCABULARY = frozenset("""
coach coaches coaching client clients meeting meetings name names call calls
sign signs signed signing minute minutes day days week weeks month months year
years work worked working
""".split())


def _seam_words(text: str) -> set[str]:
    """The words in one beat that a reader would notice repeating."""
    return {w for w in re.findall(r"[a-z']+", (text or "").lower())
            if len(w) > 2 and w not in _SEAM_STOPWORDS and w not in _SEAM_VOCABULARY}


# Which beats sit close enough together that a repeated word is audible. The
# identity->offer seam is the one the first real batch tripped over: a line
# ending "...worked with here." landing on one opening "Real people here,".
#
# hook->identity is deliberately NOT here, and that is not an oversight. The
# identity beat opens with a clause that picks the hook back up — that clause is
# the bridge, it is the single most load-bearing rule in the email, and reusing
# a word from the hook is often exactly how it works. A rule against repetition
# across that seam would fight the rule that matters most.
_SEAMS = (("identity", "offer"),)


def check_seam(beats: dict[str, str]) -> list[str]:
    """A distinctive word repeated across the seam between two adjacent beats.

    This is the check the first 155-lead batch went without. Roughly one pair in
    nine of the identity/offer bank repeats a word across that seam, each line
    fine on its own, and nothing saw it until a person read the email — by which
    time the lead had spent its single rewrite pass.

    **It runs on the AUTHORED text, not on the bank pair.** That is the whole
    design, and it is only available because the identity beat is now written
    rather than drawn. A bank pair that would have collided is fine as long as
    the drafter's sentence does not, and the drafter runs this linter on itself
    before returning — so a collision costs it one word in its first pass and
    never reaches the verifier or the rewrite budget.

    It deliberately does NOT run at deal time. `_resolve_echoes` can only swap
    the ps and `_resolve_length` only the cta and ps; identity and offer are
    both pinned, identity by the segment match the 70/30 ratio exists to buy and
    offer because it carries the beat the whole email is for. So a deal-time
    rule on this seam would be a rule with no legal repair, on a fifth of pairs.
    The drafter always has a repair. The allocator does not.
    """
    problems = []
    for first, second in _SEAMS:
        shared = _seam_words(beats.get(first, "")) & _seam_words(beats.get(second, ""))
        for word in sorted(shared):
            problems.append(
                f'the {first} and {second} beats both say "{word}" — they run '
                f"together, so change one of them")
    return problems


def check_ask(cta: str) -> list[str]:
    """The close asks for the meeting. It does not ask whether to ask.

    `cta-04` opens "Worth 15 minutes?" and two independent cold readers said the
    same thing about it: the ask is a question that invites "no", and *"the ask
    itself has become optional, which is the one thing it is not allowed to
    be."* Paired with a ps that offers an out — which is most of the ps bank,
    because lowering the cost of saying no is that beat's whole job — the reader
    gets an exit in the close's first three words and another one at the end.

    Per-line linting cannot see it, because the line is fine in isolation.
    `docs/hook-rules.md` ban #10 already says a question is a dead end that
    looks like success and that the close is where the meeting gets asked for;
    this is that rule applied one beat over.

    **A warning, not a failure.** The line is bank copy Haytham chose, the fix
    is one edit in Airtable, and a check that blocks a real send file over an
    editorial judgement nobody has measured is a check people learn to route
    around. `copy-check` reports it at the source, which is where it can be
    fixed.
    """
    first = (split_sentences(cta) or [""])[0].strip()
    if first.endswith("?"):
        return [f'the close opens on a question ("{first}"), which invites "no" '
                f"— the close is where the meeting is asked for"]
    return []


def check_email(*, name: str, subject: str, body: str, beats: dict[str, str],
                allowed_numbers: set, facts=None, identity_claim=None,
                hook_quote: str = "") -> Result:
    """Everything, for one email. This is the gate `export` refuses to skip.

    `facts` enables the attribution check. It is optional only so a caller can
    lint a body in isolation; omitting it means relabelling goes uncaught, so
    the export path always passes it. `identity_claim` follows the same
    precedent for the same reason, and both say so in a warning rather than
    skipping silently — a check that quietly does not run is worse than one
    that is not there, because the PASS line looks the same either way.
    """
    result = Result(name=name)

    if not body.strip():
        result.failures.append("body is empty")
        return result

    result.failures.extend(check_subject(subject))
    voice_failures, warnings = check_voice(body)
    result.failures.extend(voice_failures)
    result.warnings.extend(warnings)
    # Before check_numbers: this one names the column and the value, where the
    # widened check can only say "not true of any client result". A drafter
    # reading the failure list should see the specific complaint first.
    if identity_claim is not None:
        result.failures.extend(
            check_identity_claim(beats.get("identity", ""), identity_claim))
    else:
        result.warnings.append("no claim spec passed, the identity beat's "
                               "figures are unchecked")
    # Quoting is not claiming. A figure in the hook beat that is also in the
    # certified quote is the recipient's own fact; without this the rule meant
    # to stop us relabelling a client result instead strips the most specific
    # thing a hook can contain. Absent quote means absent exemption, and the
    # warning below says so — the same precedent as `facts` and
    # `identity_claim`, because a check that quietly did not run looks exactly
    # like one that passed.
    traceable = mask_quoted_figures(body, beats.get("hook", ""), hook_quote)
    if not (hook_quote or "").strip() and numbers_in(beats.get("hook", "")):
        result.warnings.append(
            "the hook carries a figure and no certified quote was passed, so "
            "it is being checked as a claim of ours rather than as a quote")
    result.failures.extend(check_numbers(traceable, allowed_numbers))
    if facts is not None:
        result.failures.extend(check_attribution(traceable, facts))
    else:
        result.warnings.append("no fact table passed, relabelling not checked")
    result.failures.extend(check_claims(beats))
    result.failures.extend(check_echo(beats))
    result.failures.extend(check_seam(beats))
    result.failures.extend(check_bridge(beats.get("identity", "")))
    result.failures.extend(check_identity_pronouns(beats.get("identity", "")))
    result.failures.extend(check_dangling_figure(beats.get("identity", "")))
    result.warnings.extend(check_ask(beats.get("cta", "")))

    hook = beats.get("hook", "")
    if not hook.strip():
        result.failures.append("hook beat is missing")
    elif len(hook.split()) > 45:
        result.warnings.append("hook runs long, it should be one or two sentences")

    return result


# ---------------------------------------------------------------- batch checks


# Long enough that a shared run is a phrase somebody chose rather than English
# doing its job. At three, "that you had to" and "and it made me" recur between
# unrelated hooks and the check reports grammar as a template.
TEMPLATE_SHINGLE_WORDS = 4


def _shingles(text: str, size: int) -> set:
    """Every run of `size` words, lowercased and stripped of punctuation.

    Punctuation goes so that "most people think," and "most people think" are
    the same phrase — a template does not stop being one at a comma.
    """
    words = re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower()).split()
    return {" ".join(words[i:i + size]) for i in range(len(words) - size + 1)}


def _opening_shape(body: str, words: int = 4) -> str:
    """The first few words of the hook, past the greeting.

    Taking paragraph one blindly reads "Hey Sarah," for every email, which
    makes every opening look identical and the check therefore useless.
    """
    paragraphs = [p.strip() for p in body.strip().split("\n\n") if p.strip()]
    for paragraph in paragraphs:
        stripped = re.sub(r"^(hey|hi|hello|dear)\b[^,\n]*,?\s*", "",
                          paragraph, flags=re.I).strip()
        if stripped:
            return " ".join(stripped.split()[:words]).lower()
    return ""


def check_batch(emails: list[dict], anchor_shares: dict | None = None) -> Result:
    """Repetition across the upload file.

    Invisible one email at a time, and the reason it matters is that this list
    is built from overlapping directories: duplicates across sources are normal,
    two coaches comparing notes is normal, and the same offer line word for word
    in both their inboxes is the tell.
    """
    result = Result(name=f"batch of {len(emails)}")
    total = len(emails) or 1

    # Below this, a share is noise. With four offer lines and three emails,
    # two drawing the same line is 67% and means nothing — it is the seed, not
    # a copy problem. Enforcing a percentage on a handful of rows would fail
    # every small batch and teach everyone to ignore the check.
    enforce_shares = total >= MIN_BATCH_FOR_SHARES
    record = result.failures.append if enforce_shares else result.warnings.append
    if not enforce_shares:
        result.warnings.append(
            f"batch of {total} is under {MIN_BATCH_FOR_SHARES}, "
            f"repetition reported but not enforced"
        )

    for beat, shares in (anchor_shares or {}).items():
        for line_id, share in shares.items():
            if share > FIXED_LINE_SHARE_CAP:
                record(f"{beat} line {line_id} is {share:.0%} of the batch, "
                       f"cap is {FIXED_LINE_SHARE_CAP:.0%}")

    shapes: dict[str, int] = {}
    for email in emails:
        shape = _opening_shape(email.get("body", ""))
        if shape:
            shapes[shape] = shapes.get(shape, 0) + 1
    for shape, count in shapes.items():
        if count / total > FIXED_LINE_SHARE_CAP and count > 1:
            record(f'{count} of {total} emails open on "{shape}"')

    # The hook is the one beat written per lead, and a phrase two of them share
    # is a template by definition. "Most people [verb]" appeared as the writer's
    # clause in two drafts on `2026-08-01-q1`; each read fine alone, and only a
    # batch-level view can see them together.
    #
    # Four words, because three catches ordinary function-word runs and reports
    # a template that is really grammar. A warning rather than a failure:
    # nobody has measured how often an innocent 4-gram recurs across real hooks,
    # and a batch-blocking gate calibrated on nothing is one people route around.
    hooks = {}
    for index, email in enumerate(emails):
        hook = (email.get("beats") or {}).get("hook", "")
        for shingle in _shingles(hook, TEMPLATE_SHINGLE_WORDS):
            hooks.setdefault(shingle, set()).add(index)
    for shingle, owners in sorted(hooks.items()):
        if len(owners) > 1:
            result.warnings.append(
                f'{len(owners)} hooks share the phrase "{shingle}" — the hook '
                f"is the beat that proves per-lead authorship, so a phrase two "
                f"of them have is a template")

    bridges: dict[str, int] = {}
    for email in emails:
        identity = (email.get("beats") or {}).get("identity", "")
        opening = " ".join(identity.split()[:6]).lower().rstrip(".,")
        if opening:
            bridges[opening] = bridges.get(opening, 0) + 1
    for phrase, count in bridges.items():
        if count / total > BRIDGE_PHRASE_CAP and count > 1:
            result.warnings.append(
                f'{count} of {total} identity beats open "{phrase}"'
            )

    subjects = [e.get("subject", "").strip().lower() for e in emails]
    # Sorted, not set-ordered. The design says a skill quotes the gate's line
    # verbatim; a set iterates in string-hash order, which is randomised per
    # process, so the same failing batch printed its subjects in a different
    # order on every run and no two quotes matched.
    repeats = sorted({s for s in subjects if s and subjects.count(s) > 1})
    for subject in repeats:
        result.failures.append(f'subject "{subject}" is reused in this batch')

    return result
