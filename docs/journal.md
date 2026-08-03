## 2026-08-03 (the orchestrator share) — narration was 7%, and the rule chased it

Haytham: now go after the orchestrator share. It is 75% of the bill and the
last three entries kept deferring it.

**The diagnosis in `CLAUDE.md` was right about the total and wrong about the
target.** It said two-thirds of what is re-read each turn is the orchestrator's
own writing, which is true, and drew from it: never narrate per lead. Measured
on this session's own transcript:

| block | ~tokens | share |
|---|---|---|
| thinking | 76,841 | **34.3%** |
| tool_result | 68,676 | 30.6% |
| tool_use (the model's OWN calls) | 63,002 | 28.1% |
| text (prose to the operator) | 15,214 | **6.8%** |

Narration is the smallest of the four. A rule aimed at it is aimed at 7% of the
context, and the two blocks nobody was looking at are 62%.

`tool_use` being that large is the surprise worth naming: **a heredoc, a `Write`
payload or a long `python3 -` script sits in the context for the rest of the
run**, exactly like a tool result does. Writing a file is not a free action.

### `cache_read` is a sum, and that is the whole cost model

`cache_read` is the sum of the context over every turn. So it falls with a
smaller context *and* with fewer turns, and it rises **quadratically** when a run
gets longer and chattier at once. Halving per-turn output and halving turn count
are the same size of win, and they multiply.

This session: 230 requests, ~224K context, **53.0M tokens, $37.36** — and it ran
**zero subagents**. That is a pure orchestrator specimen, and it cost more than
q1, q2 and q3's entire Apify bills multiplied by twenty.

### What shipped

**`usage` now prints the block profile.** Characters rather than tokens, and it
says so — the transcript carries no per-block token count and a tokeniser here
would be a second estimate dressed as a measurement. Main thread only: a
subagent's context dies with it and is already reported per agent. A profile of
nothing prints no section rather than a row of zeroes, which is `metrics`' rule
about a count nobody supplied.

**`research-worker` writes its own slice and replies with one line.** The skill
used to say workers write nothing and then validate `work/research-<slice>.json`
— so the array came back through the orchestrator's context and was copied to
disk by hand, paying for it twice and leaving the run unresumable. A research
object carries verbatim observation text at roughly a thousand tokens per lead;
a slice of ten is ten thousand tokens held for **every remaining turn**.
`collect research` has always built `researched.json` from those files.

`hook-worker` gets the same treatment. `draft-worker` already had it and its
reasoning is the one both now quote.

**`CLAUDE.md`'s rule is rewritten** around the measurement instead of the
inference, and keeps the narration advice with its real weight attached.

### What is not fixed

Thinking is 34% and nothing here can shorten it directly — it falls with fewer
turns, or with a lower reasoning effort on mechanical stages, and neither is a
change this repo can make on its own behalf. The honest position is that the
measurement now exists, two of the four blocks have a mechanical fix, and the
largest one is a judgement call the next batch will have to test.

**No batch has run since any of this.** `metrics --written` reads
`tokens_per_email` out of the usage artifact and that is the control number.
Nothing here is proven until a real batch produces one to compare.

