#!/usr/bin/env python3
"""outbound/main.py — the test-scale Smartlead pipeline.

WHAT THIS IS
    A second, parallel path alongside the Gmail one. It takes a hand-sourced
    lead list, enriches each row, assembles the five email fields from the four
    copy CSVs in `data/`, and writes a Smartlead-ready upload file.

        leads/raw.csv → enrich → verify-hook → assemble → export
                                                        → preview

WHY IT EXISTS SEPARATELY
    The Gmail path's whole value is its gates — Finding Verified, Email
    Verified, per-inbox ceilings, the Sunday pause. Every one of those is
    meaningless when Smartlead owns sending and the campaign is a one-shot
    ~120-lead test. Wiring the two together would either drag those gates
    somewhere they cannot be enforced, or weaken them where they are. So this
    is a disposable sibling, not an extension.

WHAT IT DELIBERATELY DOES NOT DO
    No CRM, no Notion, no Airtable. No sending — Smartlead sends. No follow-ups
    (touch 2 and 3 come later). No warm-reply handling — a reply is a human job
    and stays in Gmail. No dedupe against history. No config layer, no
    scheduler. Built for 120 rows, not 10,000. It imports nothing from
    `audit/` and modifies nothing outside `outbound/`.

    It also does not lint the copy in `data/`. Those four CSVs ARE the copy,
    verbatim; they are the place to change it.

THE ONE STRUCTURAL DECISION
    Stage 3 (`assemble`) is pure Python with ZERO model calls. A bad email has
    to be a data bug someone can fix in a CSV, not a model that had an off day.
    Stages 1 and 2 do need a model, and Python cannot make a model pass, so
    they split the way `main.py ingest` already splits in this repo: the
    command prints a work packet, the agent does the research, and `--write`
    merges validated results back. Idempotency falls out of that for free — a
    row that already carries a verdict is never re-emitted, so a re-run never
    re-scrapes.

EXIT CODES
    0  success (including an empty work packet — nothing to do is not a failure)
    1  validation rejected the input file, or a stage was run out of order
    2  bad usage / a required file is missing

Stdlib only, on purpose: this must import on a machine with no Playwright, no
Pillow and no Firecrawl, exactly like `audit.crm_gate` does today.
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LEADS_DIR = BASE_DIR / "leads"

RAW_CSV = LEADS_DIR / "raw.csv"
ENRICHED_CSV = LEADS_DIR / "enriched.csv"
SMARTLEAD_CSV = LEADS_DIR / "smartlead.csv"
PREVIEW_TXT = LEADS_DIR / "preview.txt"

# --- schema ----------------------------------------------------------------
# One stable column order, written the same way every time, so a git diff of
# enriched.csv shows what actually changed instead of a reshuffle.

RAW_COLUMNS = ["name", "email", "site_url", "profile_url", "source"]

ENRICH_COLUMNS = [
    "uae_based", "active_30d", "solo", "coach_type", "top_program_price_aed",
    "runs_certification", "audience_size", "subject", "hook",
    "hook_source_url", "drop_reason",
]

VERIFY_COLUMNS = ["hook_verify_failed"]

ASSEMBLE_COLUMNS = ["cold_read", "identity", "offer", "cta"]

ENRICHED_COLUMNS = RAW_COLUMNS + ENRICH_COLUMNS + VERIFY_COLUMNS + ASSEMBLE_COLUMNS

EXPORT_COLUMNS = [
    "email", "firstName", "subject", "hook",
    "cold_read", "identity", "offer", "cta",
]

# The three hard gates. A clear "no" drops the row; "unclear" passes.
GATES = ["uae_based", "active_30d", "solo"]
GATE_VALUES = {"yes", "no", "unclear"}

COACH_TYPES = [
    "Business", "Leadership", "Life", "Mindset",
    "Career", "Health", "Fitness", "Other",
]

# Fields an enrich result may set. `drop_reason` is absent on purpose: it is
# derived from the gates by this module, not asserted by the agent.
ENRICH_RESULT_FIELDS = [
    "email", "uae_based", "active_30d", "solo", "coach_type",
    "top_program_price_aed", "runs_certification", "audience_size",
    "subject", "hook", "hook_source_url",
]

SUBJECT_MAX_WORDS = 7          # "under 8 words"
END_PUNCTUATION = ".!?,;:"

# The two cold-read skip rules, by id.
CERT_SKIP_ID = "mindset-cert-flood"
REACH_SKIP_ID = "mindset-reach-without-buyers"
REACH_MIN_AUDIENCE = 20_000

PS_LINE = "ps: If this isn't for you, tell me and I'll leave it there."
SIGN_OFF = "Haytham"

# The order the email's body blocks appear in, and the order `assemble` draws
# them. Both are load-bearing: changing the draw order changes every email in
# the campaign, because the RNG is a single seeded stream per lead.
BODY_BLOCKS = ["hook", "cold_read", "identity", "offer", "cta"]


# --- csv helpers -----------------------------------------------------------

def read_csv(path):
    """Read a CSV into a list of dicts, with every value stripped and None
    normalised to "". Returns [] when the file does not exist."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(fh)
        ]


def write_csv(path, rows, columns):
    """Write rows with exactly `columns`, in order. Every value is coerced to a
    string, so an absent or None field lands as "" and never as the literal
    "None" — which is the one thing that would quietly poison a Smartlead
    upload."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: _as_text(row.get(c)) for c in columns})


def _as_text(value):
    return "" if value is None else str(value)


def norm_email(value):
    return (value or "").strip().lower()


def parse_int(value):
    """Lenient integer parse for the two numeric enrichment fields. Returns
    None for blank or non-numeric, which both skip rules treat as 'unknown'."""
    text = (value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def is_yes(value):
    return (value or "").strip().lower() == "yes"


def first_name(name):
    parts = (name or "").strip().split()
    return parts[0] if parts else ""


# --- the working file ------------------------------------------------------

def load_leads():
    """Build the working row set: raw.csv order, with any values already in
    enriched.csv merged on top, keyed on the normalised email.

    Rows that exist in enriched.csv but no longer in raw.csv are kept at the
    end rather than dropped — losing work already paid for is worse than a
    stale row someone can delete by hand."""
    raw = read_csv(RAW_CSV)
    enriched = {norm_email(r.get("email")): r for r in read_csv(ENRICHED_CSV)}

    rows, seen = [], set()
    for r in raw:
        key = norm_email(r.get("email"))
        merged = {c: "" for c in ENRICHED_COLUMNS}
        merged.update(enriched.get(key, {}))
        # raw.csv is authoritative for its own columns — a corrected name or
        # URL there should win over the copy frozen into enriched.csv.
        for c in RAW_COLUMNS:
            if r.get(c):
                merged[c] = r[c]
        rows.append({c: merged.get(c, "") for c in ENRICHED_COLUMNS})
        seen.add(key)

    for key, r in enriched.items():
        if key not in seen:
            rows.append({c: r.get(c, "") for c in ENRICHED_COLUMNS})

    return rows


def save_leads(rows):
    write_csv(ENRICHED_CSV, rows, ENRICHED_COLUMNS)


def has_verdict(row):
    """A row has a verdict once all three gates are answered. That is what
    makes `enrich` idempotent: re-running never re-scrapes a settled row."""
    return all((row.get(g) or "").strip() for g in GATES)


def derive_drop_reason(row):
    """drop_reason is computed, never asserted. A clear 'no' on any gate drops
    the row; 'unclear' passes."""
    failed = [g for g in GATES if (row.get(g) or "").strip().lower() == "no"]
    return "gate: " + ", ".join(f"{g}=no" for g in failed) if failed else ""


def is_dropped(row):
    return bool((row.get("drop_reason") or "").strip())


# --- data files ------------------------------------------------------------

def load_copy():
    """Load the four copy CSVs. These are the campaign's copy verbatim —
    nothing here rewrites or lints them."""
    return {
        "cold_reads": read_csv(DATA_DIR / "cold_reads.csv"),
        "identity": read_csv(DATA_DIR / "identity.csv"),
        "offer": read_csv(DATA_DIR / "offer.csv"),
        "cta": read_csv(DATA_DIR / "cta.csv"),
    }


def parse_roll_range(text):
    """'1-55' → (1, 55). Ranges are read from the CSV and never hardcoded, so
    a reweight of offer.csv or cta.csv stays a data edit."""
    lo, _, hi = (text or "").partition("-")
    return int(lo.strip()), int(hi.strip())


# --- assembly (pure, no model calls) ---------------------------------------

def seeded_rng(email):
    """One deterministic RNG per lead, seeded on a stable hash of the email so
    a re-run produces the identical email and the export always matches the
    log.

    sha256, never the builtin hash(): hash() is salted per process by
    PYTHONHASHSEED, which would make 'reproducible' quietly false between
    runs."""
    digest = hashlib.sha256(norm_email(email).encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def eligible_cold_reads(cold_reads, coach_type, runs_certification, audience_size):
    """Rows matching the lead's coach_type plus the General rows, minus the two
    skip rules.

    Note a coach_type of 'Other' (or blank) matches no specific rows, so it
    falls through to General only — which is why General exists."""
    eligible = []
    for row in cold_reads:
        row_type = (row.get("coach_type") or "").strip()
        if row_type != "General" and row_type != (coach_type or "").strip():
            continue
        if row.get("id") == CERT_SKIP_ID and is_yes(runs_certification):
            continue
        if row.get("id") == REACH_SKIP_ID:
            size = parse_int(audience_size)
            if size is None or size < REACH_MIN_AUDIENCE:
                continue
        eligible.append(row)
    return eligible


def eligible_identities(identities, coach_type):
    """Rows matching coach_type, plus the 'Any' fallback row."""
    wanted = (coach_type or "").strip()
    return [
        row for row in identities
        if (row.get("coach_type") or "").strip() in (wanted, "Any")
    ]


def pick(rows, rng):
    """Uniform pick over an ordered list. Written as an explicit randrange
    rather than rng.choice so the draw is obviously one call against the
    stream — the sequence of draws is what makes assembly reproducible."""
    if not rows:
        return None
    return rows[rng.randrange(len(rows))]


def weighted_pick(rows, roll):
    """Take the row whose roll_1_100 range contains the roll."""
    for row in rows:
        lo, hi = parse_roll_range(row.get("roll_1_100"))
        if lo <= roll <= hi:
            return row
    return None


def assemble_row(row, copy):
    """Return the four assembled columns for one lead.

    The draw order — cold_read, identity, offer, cta — is fixed and
    load-bearing. All four come off a single seeded stream, so reordering them
    changes every email in the campaign.

    `cold_read` is the picked row's cold_read_text ONLY. cost_line_pairs_with
    is deliberately unused: the export is eight columns and the template has
    one slot for the beat, so the cost line stays in the CSV as reference
    data."""
    rng = seeded_rng(row.get("email"))

    cold_reads = eligible_cold_reads(
        copy["cold_reads"],
        row.get("coach_type"),
        row.get("runs_certification"),
        row.get("audience_size"),
    )
    cold_read = pick(cold_reads, rng)
    identity = pick(eligible_identities(copy["identity"], row.get("coach_type")), rng)
    offer = weighted_pick(copy["offer"], rng.randint(1, 100))
    cta = weighted_pick(copy["cta"], rng.randint(1, 100))

    return {
        "cold_read": (cold_read or {}).get("cold_read_text", ""),
        "identity": (identity or {}).get("line", ""),
        "offer": (offer or {}).get("line", ""),
        "cta": (cta or {}).get("line", ""),
    }


# --- rendering -------------------------------------------------------------

def render_email(row):
    """Render one assembled lead as the full email.

    Blocks are joined with a blank line and empty ones are dropped BEFORE the
    join, so an empty hook collapses its paragraph entirely instead of leaving
    a double blank line."""
    blocks = [f"Hey {first_name(row.get('name'))},"]
    blocks += [
        text for text in ((row.get(k) or "").strip() for k in BODY_BLOCKS) if text
    ]
    blocks += [SIGN_OFF, PS_LINE]
    subject = (row.get("subject") or "").strip()
    header = f"Subject: {subject}" if subject else "Subject:"
    return f"{header}\n\n" + "\n\n".join(blocks)


# --- stage 1: enrich -------------------------------------------------------

ENRICH_CONTRACT = {
    "uae_based": "yes | no | unclear. Hard gate — a clear 'no' drops the row.",
    "active_30d": "yes | no | unclear. Hard gate — a clear 'no' drops the row.",
    "solo": "yes | no | unclear. Hard gate — a clear 'no' drops the row.",
    "coach_type": " | ".join(COACH_TYPES) + ". Required unless a gate is 'no'.",
    "top_program_price_aed": "number or blank. Captured, never gated on.",
    "runs_certification": "yes | no. Used by one cold-read skip rule.",
    "audience_size": "number or blank.",
    "subject": (
        "SMYKM hook. Under 8 words, sentence case, no end punctuation. "
        "Leave blank if no real hook was found."
    ),
    "hook": "One or two sentences elaborating the subject. Blank if none found.",
    "hook_source_url": "Required whenever hook is non-empty.",
    "_rules": [
        "'unclear' passes the gates. Only a clear 'no' drops a row.",
        "Hooks come from real public evidence only — the person's own framework "
        "name, a phrase from their content, a recent post, a talk they gave. "
        "It has to be something only this person would recognise.",
        "NEVER invent a hook. If nothing real is found, leave subject, hook and "
        "hook_source_url empty and move on. An empty hook is an acceptable "
        "outcome and the email still works without it. A fabricated hook is not "
        "recoverable, because it gets caught on the call.",
        "drop_reason is derived by the pipeline from the gates. Do not set it.",
    ],
}


def build_enrich_packet(rows):
    pending = [
        {c: row.get(c, "") for c in RAW_COLUMNS}
        for row in rows if not has_verdict(row)
    ]
    return {
        "stage": "enrich",
        "pending_count": len(pending),
        "total_rows": len(rows),
        "fields": ENRICH_CONTRACT,
        "pending": pending,
    }


def validate_enrich_results(rows, results):
    """Check every result before a single value is written. Returns
    (updates_by_email, errors, warnings).

    This rejects the whole file rather than writing the good rows and
    complaining about the rest — a half-applied enrich is worse than none,
    because the rows that silently did not land still look settled."""
    by_email = {norm_email(r.get("email")): r for r in rows}
    updates, errors, warnings = {}, [], []

    for i, result in enumerate(results):
        where = f"result {i}"
        if not isinstance(result, dict):
            errors.append(f"{where}: not an object")
            continue

        key = norm_email(result.get("email"))
        where = f"{where} ({key or 'no email'})"
        if not key:
            errors.append(f"{where}: missing 'email'")
            continue
        if key not in by_email:
            errors.append(f"{where}: no such lead in {ENRICHED_CSV.name}")
            continue
        if key in updates:
            errors.append(f"{where}: duplicate result for the same lead")
            continue

        unknown = sorted(set(result) - set(ENRICH_RESULT_FIELDS))
        if unknown:
            errors.append(f"{where}: unknown field(s) {', '.join(unknown)}")
            continue

        clean, row_errors, row_warnings = _validate_enrich_row(result, where)
        errors.extend(row_errors)
        warnings.extend(row_warnings)
        if not row_errors:
            updates[key] = clean

    return updates, errors, warnings


def _validate_enrich_row(result, where):
    clean, errors, warnings = {}, [], []

    for gate in GATES:
        value = (result.get(gate) or "").strip().lower()
        if value not in GATE_VALUES:
            errors.append(f"{where}: {gate} must be yes/no/unclear, got '{value}'")
        clean[gate] = value

    dropped = any(clean.get(g) == "no" for g in GATES)

    coach_type = (result.get("coach_type") or "").strip()
    if coach_type and coach_type not in COACH_TYPES:
        errors.append(
            f"{where}: coach_type '{coach_type}' not one of {', '.join(COACH_TYPES)}"
        )
    elif not coach_type and not dropped:
        errors.append(f"{where}: coach_type is required on a surviving row")
    clean["coach_type"] = coach_type

    cert = (result.get("runs_certification") or "").strip().lower()
    if cert and cert not in {"yes", "no"}:
        errors.append(f"{where}: runs_certification must be yes/no or blank")
    clean["runs_certification"] = cert

    for field in ("top_program_price_aed", "audience_size"):
        raw = (result.get(field) or "").strip()
        parsed = parse_int(raw)
        if raw and parsed is None:
            errors.append(f"{where}: {field} must be a number or blank, got '{raw}'")
        clean[field] = "" if parsed is None else str(parsed)

    hook = (result.get("hook") or "").strip()
    source = (result.get("hook_source_url") or "").strip()
    if hook and not source:
        errors.append(f"{where}: hook is set but hook_source_url is empty")
    clean["hook"] = hook
    clean["hook_source_url"] = source

    subject = (result.get("subject") or "").strip()
    if subject:
        words = subject.split()
        if len(words) > SUBJECT_MAX_WORDS:
            errors.append(
                f"{where}: subject is {len(words)} words, must be under "
                f"{SUBJECT_MAX_WORDS + 1}"
            )
        if subject[-1] in END_PUNCTUATION:
            errors.append(f"{where}: subject ends in punctuation ('{subject[-1]}')")
        letters = [c for c in subject if c.isalpha()]
        if letters and all(c.isupper() for c in letters):
            errors.append(f"{where}: subject is all caps, must be sentence case")
        elif len(words) >= 3 and all(w[:1].isupper() for w in words if w[:1].isalpha()):
            # A warning, not an error: a real framework or brand name can
            # legitimately capitalise every word, and blocking those would cost
            # more good hooks than it saves bad ones.
            warnings.append(f"{where}: subject looks like Title Case, not sentence case")
    clean["subject"] = subject

    return clean, errors, warnings


def apply_enrich(rows, updates):
    for row in rows:
        update = updates.get(norm_email(row.get("email")))
        if not update:
            continue
        row.update(update)
        row["drop_reason"] = derive_drop_reason(row)
    return rows


# --- stage 2: verify-hook --------------------------------------------------

def rows_with_hooks(rows):
    return [r for r in rows if (r.get("hook") or "").strip()]


def build_verify_packet(rows):
    pending = [
        {
            "email": row.get("email", ""),
            "name": row.get("name", ""),
            "subject": row.get("subject", ""),
            "hook": row.get("hook", ""),
            "hook_source_url": row.get("hook_source_url", ""),
        }
        for row in rows_with_hooks(rows)
    ]
    return {
        "stage": "verify-hook",
        "pending_count": len(pending),
        "fields": {
            "email": "the lead this verdict is for",
            "verified": (
                "true | false. Refetch hook_source_url and confirm the hook is "
                "actually supported by what is there. On false the pipeline "
                "clears subject, hook and hook_source_url."
            ),
        },
        "pending": pending,
    }


def validate_verify_results(rows, results):
    hooked = {norm_email(r.get("email")) for r in rows_with_hooks(rows)}
    verdicts, errors = {}, []

    for i, result in enumerate(results):
        where = f"result {i}"
        if not isinstance(result, dict):
            errors.append(f"{where}: not an object")
            continue
        key = norm_email(result.get("email"))
        where = f"{where} ({key or 'no email'})"
        if not key:
            errors.append(f"{where}: missing 'email'")
            continue
        if key not in hooked:
            errors.append(f"{where}: that lead has no hook to verify")
            continue
        if not isinstance(result.get("verified"), bool):
            errors.append(f"{where}: 'verified' must be true or false")
            continue
        verdicts[key] = result["verified"]

    return verdicts, errors


def apply_verify(rows, verdicts):
    cleared = 0
    for row in rows:
        verdict = verdicts.get(norm_email(row.get("email")))
        if verdict is None or verdict:
            continue
        row["subject"] = ""
        row["hook"] = ""
        row["hook_source_url"] = ""
        row["hook_verify_failed"] = "yes"
        cleared += 1
    return cleared


def no_hook_rate(rows):
    """The share of exportable rows running on the weaker four-beat email.

    Measured over rows that survived the gates, because a dropped row never
    ships and would only flatter the number."""
    live = [r for r in rows if not is_dropped(r)]
    without = [r for r in live if not (r.get("hook") or "").strip()]
    return len(without), len(live)


# --- commands --------------------------------------------------------------

def cmd_enrich(args) -> int:
    rows = load_leads()
    if not rows:
        print(f"No leads. Fill {RAW_CSV} first.", file=sys.stderr)
        return 2

    if not args.write:
        print(json.dumps(build_enrich_packet(rows), indent=2, ensure_ascii=False))
        return 0

    results = _load_results(args.write)
    if results is None:
        return 2

    updates, errors, warnings = validate_enrich_results(rows, results)
    for warning in warnings:
        print(f"warn: {warning}", file=sys.stderr)
    if errors:
        print(f"ENRICH WRITE REJECTED — {len(errors)} problem(s), nothing written:",
              file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    apply_enrich(rows, updates)
    save_leads(rows)

    dropped = [r for r in rows if is_dropped(r)]
    print(f"ENRICH: wrote {len(updates)} row(s) to {ENRICHED_CSV.name}; "
          f"{len(dropped)} dropped by a gate, {len(rows) - len(dropped)} live")
    for row in dropped:
        print(f"  dropped {row.get('email')} — {row.get('drop_reason')}")
    return 0


def cmd_verify_hook(args) -> int:
    rows = load_leads()
    if not rows:
        print(f"No leads. Fill {RAW_CSV} first.", file=sys.stderr)
        return 2

    if not args.write:
        print(json.dumps(build_verify_packet(rows), indent=2, ensure_ascii=False))
        return 0

    results = _load_results(args.write)
    if results is None:
        return 2

    verdicts, errors = validate_verify_results(rows, results)
    if errors:
        print(f"VERIFY WRITE REJECTED — {len(errors)} problem(s), nothing written:",
              file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    cleared = apply_verify(rows, verdicts)
    save_leads(rows)

    without, live = no_hook_rate(rows)
    share = (100.0 * without / live) if live else 0.0
    print(f"VERIFY-HOOK: {len(verdicts)} checked, {cleared} cleared as unsupported")
    print(f"NO-HOOK RATE: {without}/{live} live rows ({share:.1f}%) "
          f"will run on the four-beat email")
    return 0


def cmd_assemble(args) -> int:
    rows = load_leads()
    if not rows:
        print(f"No leads. Fill {RAW_CSV} first.", file=sys.stderr)
        return 2

    copy = load_copy()
    missing = [name for name, data in copy.items() if not data]
    if missing:
        print(f"Missing or empty copy file(s) in {DATA_DIR}: {', '.join(missing)}",
              file=sys.stderr)
        return 2

    assembled, skipped, incomplete = 0, 0, []
    for row in rows:
        if is_dropped(row):
            # Clear any columns assembled before the row was dropped, so the
            # file never carries copy for a lead that will not ship.
            row.update({c: "" for c in ASSEMBLE_COLUMNS})
            skipped += 1
            continue
        if not has_verdict(row):
            incomplete.append(row.get("email", ""))
            continue
        row.update(assemble_row(row, copy))
        assembled += 1

    if incomplete:
        print(f"ASSEMBLE REJECTED — {len(incomplete)} row(s) have no enrich verdict "
              f"yet; run `enrich` first:", file=sys.stderr)
        for email in incomplete:
            print(f"  {email}", file=sys.stderr)
        return 1

    save_leads(rows)
    print(f"ASSEMBLE: {assembled} row(s) assembled, {skipped} dropped row(s) skipped")
    return 0


def cmd_export(args) -> int:
    rows = load_leads()
    live = [r for r in rows if not is_dropped(r)]
    if not live:
        print("Nothing to export — every row is dropped or the list is empty.",
              file=sys.stderr)
        return 2

    unassembled = [r.get("email", "") for r in live if not (r.get("cold_read") or "").strip()]
    if unassembled:
        print(f"EXPORT REJECTED — {len(unassembled)} row(s) not assembled; "
              f"run `assemble` first:", file=sys.stderr)
        for email in unassembled:
            print(f"  {email}", file=sys.stderr)
        return 1

    out = []
    for row in live:
        record = {c: (row.get(c) or "") for c in EXPORT_COLUMNS}
        record["firstName"] = first_name(row.get("name"))
        out.append(record)

    write_csv(SMARTLEAD_CSV, out, EXPORT_COLUMNS)
    no_hook = sum(1 for r in out if not r["hook"])
    print(f"EXPORT: {len(out)} row(s) → {SMARTLEAD_CSV} "
          f"({len(rows) - len(out)} dropped, {no_hook} without a hook)")
    return 0


def cmd_preview(args) -> int:
    rows = [r for r in load_leads() if not is_dropped(r)]
    rows = [r for r in rows if (r.get("cold_read") or "").strip()][: args.n]
    if not rows:
        print("Nothing to preview — run `assemble` first.", file=sys.stderr)
        return 2

    separator = "\n\n" + ("-" * 72) + "\n\n"
    body = separator.join(render_email(r) for r in rows)
    PREVIEW_TXT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_TXT.write_text(body + "\n", encoding="utf-8")
    print(f"PREVIEW: {len(rows)} email(s) → {PREVIEW_TXT}")
    return 0


def _load_results(path):
    """Read a results file. Accepts either a bare list or {'results': [...]}."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"No such file: {path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        print(f"{path} is not valid JSON: {exc}", file=sys.stderr)
        return None

    if isinstance(payload, dict):
        payload = payload.get("results")
    if not isinstance(payload, list):
        print(f"{path} must be a JSON list of results, or an object with a "
              f"'results' list.", file=sys.stderr)
        return None
    return payload


# --- cli -------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="outbound",
        description="Test-scale Smartlead pipeline: raw leads in, upload CSV out.",
    )
    sub = parser.add_subparsers(dest="command")

    p_enrich = sub.add_parser(
        "enrich",
        help="print the work packet of un-enriched leads, or merge results with --write",
    )
    p_enrich.add_argument(
        "--write", metavar="RESULTS.JSON",
        help="merge enrichment results back into enriched.csv (validated; "
             "rejects the whole file rather than writing bad rows)",
    )
    p_enrich.set_defaults(func=cmd_enrich)

    p_verify = sub.add_parser(
        "verify-hook",
        help="print the hooks needing a refetch, or merge verdicts with --write",
    )
    p_verify.add_argument(
        "--write", metavar="RESULTS.JSON",
        help="merge {email, verified} verdicts; clears unsupported hooks and "
             "prints the resulting no-hook rate",
    )
    p_verify.set_defaults(func=cmd_verify_hook)

    p_assemble = sub.add_parser(
        "assemble",
        help="pure-Python assembly of cold_read / identity / offer / cta (no model calls)",
    )
    p_assemble.set_defaults(func=cmd_assemble)

    p_export = sub.add_parser("export", help="write leads/smartlead.csv")
    p_export.set_defaults(func=cmd_export)

    p_preview = sub.add_parser(
        "preview", help="render the first N assembled emails to leads/preview.txt")
    p_preview.add_argument("-n", type=int, default=10, help="how many (default 10)")
    p_preview.set_defaults(func=cmd_preview)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        sys.exit(2)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
