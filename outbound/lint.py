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

# Words that give away an operator writing to a civilian.
JARGON = (
    "funnel", "conversion", "convert", "audit", "sequence", "cadence",
    "pipeline", "outreach", "prospecting", "lead magnet", "cold email",
    "optimi", "leverage", "synerg", "touchpoint", "top of funnel",
    "drip", "nurture", "CRM", "ICP", "KPI", "ROI",
)

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
    "ps": [
        ("a costless no", re.compile(
            r"costs? you nothing|fine answer|no hard feelings|nothing to "
            r"unsubscribe|not a list|leave it there|a no here", re.I)),
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


def check_numbers(body: str, allowed: set) -> list[str]:
    """Every digit must be true of some real client result.

    `allowed` is the widened set: every number in the fact table, plus the
    aggregate, plus the offer's own numbers. A year or a time of day is not
    exempt — the email has no business carrying either, so an unexplained
    number is a failure regardless of what it looks like.

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
    """
    from outbound.anchors import allowed_numbers

    problems = []
    for sentence in re.split(r"(?<=[.!?])\s+", body):
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


def check_voice(body: str) -> tuple[list[str], list[str]]:
    failures, warnings = [], []

    if EM_DASH in body:
        failures.append("em-dash present")

    links = bare_links(body)
    if links:
        failures.append(f"bare link or address: {', '.join(links[:3])}")

    lowered = body.lower()
    for word in JARGON:
        if word.lower() in lowered:
            failures.append(f'operator jargon: "{word}"')
    for closer in WEAK_CLOSERS:
        if closer in lowered:
            failures.append(f'weak closer: "{closer}"')

    if not re.search(rf"^\s*{SIGN_OFF}\s*$", body, re.M):
        failures.append(f'no "{SIGN_OFF}" sign-off on its own line')

    for match in _UNSEPARATED.finditer(body):
        failures.append(
            f'unformatted number "{match.group(0)}" reads as a merge field'
        )

    words = len(re.findall(r"\b[\w'-]+\b", body))
    if words < WORD_MIN:
        failures.append(f"{words} words, under {WORD_MIN}")
    elif words > WORD_MAX:
        failures.append(f"{words} words, over {WORD_MAX}")

    if body.count("\n\n") < 3:
        warnings.append("fewer than four paragraphs, beats may have merged")

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if sentences and sum(1 for s in sentences if len(s.split()) > 28):
        warnings.append("a sentence runs past 28 words")

    return failures, warnings


def check_identity_pronouns(identity: str) -> list[str]:
    """A segment line fires across a whole segment, so a gendered pronoun in it
    is wrong about half the time. Use "them"."""
    match = GENDERED.search(identity or "")
    return [f'gendered pronoun "{match.group(0)}" in the identity beat'] if match else []


def check_subject(subject: str) -> list[str]:
    problems = []
    text = (subject or "").strip()
    if not text:
        return ["subject is empty"]
    words = len(text.split())
    if words > 8:
        problems.append(f"subject is {words} words, over 8")
    if EM_DASH in text:
        problems.append("em-dash in subject")
    if text.endswith("?") and words <= 3:
        problems.append("subject is a bare question, reads as a template")
    if text != text.strip() or text.isupper():
        problems.append("subject capitalisation is off")
    return problems


def check_email(*, name: str, subject: str, body: str, beats: dict[str, str],
                allowed_numbers: set, facts=None) -> Result:
    """Everything, for one email. This is the gate `export` refuses to skip.

    `facts` enables the attribution check. It is optional only so a caller can
    lint a body in isolation; omitting it means relabelling goes uncaught, so
    the export path always passes it.
    """
    result = Result(name=name)

    if not body.strip():
        result.failures.append("body is empty")
        return result

    result.failures.extend(check_subject(subject))
    voice_failures, warnings = check_voice(body)
    result.failures.extend(voice_failures)
    result.warnings.extend(warnings)
    result.failures.extend(check_numbers(body, allowed_numbers))
    if facts is not None:
        result.failures.extend(check_attribution(body, facts))
    else:
        result.warnings.append("no fact table passed, relabelling not checked")
    result.failures.extend(check_claims(beats))
    result.failures.extend(check_bridge(beats.get("identity", "")))
    result.failures.extend(check_identity_pronouns(beats.get("identity", "")))

    hook = beats.get("hook", "")
    if not hook.strip():
        result.failures.append("hook beat is missing")
    elif len(hook.split()) > 45:
        result.warnings.append("hook runs long, it should be one or two sentences")

    return result


# ---------------------------------------------------------------- batch checks


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
    repeats = {s for s in subjects if s and subjects.count(s) > 1}
    for subject in repeats:
        result.failures.append(f'subject "{subject}" is reused in this batch')

    return result
