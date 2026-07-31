"""The outbound machine: a raw list of coaches in, an upload file out.

Eight stages, each one a module here, in the order they run:

    normalize  raw CSV row -> Lead, junk domains stripped, platform URLs routed
    dedupe     name/domain BEFORE any paid call, email again AFTER research
    fetch      free local HTTP first, batched Apify only for what that can't read
    qualify    the three floors: UAE-based, coach, active in 30 days
    research   the typed object every worker returns, and its validator
    anchors    the per-lead draw of Haytham's hand-written lines
    lint       the fail-closed checks that make model-written copy safe
    export     leads.csv (assembled subject + body) and preview.txt

Two modules here are checkers rather than stages, and nothing in a batch run
calls them: `copy_sync`, the gate on lines edited in Airtable, and `doc_check`,
the gate on the defining docs in docs/spec/.

This docstring said "Nine stages" over a list of eight until 2026-07-31, which
is the small, ordinary way documentation goes wrong. `doc_check` exists because
the same thing was happening in the docs at a larger scale.

What this package deliberately does NOT do: send anything, walk a funnel, or
score a lead on anything it hasn't got evidence for. Sending belongs to
Smartlead. The audit is dead — see docs/START-HERE.md for why.
"""
