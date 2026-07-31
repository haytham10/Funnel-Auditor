"""The outbound machine: a raw list of coaches in, an upload file out.

Nine stages, each one a module here, in the order they run:

    normalize  raw CSV row -> Lead, junk domains stripped, platform URLs routed
    dedupe     name/domain BEFORE any paid call, email again AFTER research
    fetch      free local HTTP first, batched Apify only for what that can't read
    qualify    the three floors: UAE-based, coach, active in 30 days
    research   the typed object every worker returns, and its validator
    anchors    the per-lead draw of Haytham's hand-written lines
    lint       the fail-closed checks that make model-written copy safe
    export     leads.csv (assembled subject + body) and preview.txt

What this package deliberately does NOT do: send anything, walk a funnel, or
score a lead on anything it hasn't got evidence for. Sending belongs to
Smartlead. The audit is dead — see docs/START-HERE.md for why.
"""
