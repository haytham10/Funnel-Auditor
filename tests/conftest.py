"""Test-suite defaults.

`OUTBOUND_COPY_SOURCE=csv` pins the copy bank to the committed CSVs for every
test. Two reasons, both learned the hard way in one run:

1. **No network.** Before this, `CopyBank.load()` reached Airtable on every
   call, so the suite made one HTTP request per `draw()` and hung.
2. **No dependence on live data.** A test asserting "a Career lead can draw a
   Career line" would otherwise start failing the moment someone unchecked
   Active on a row in Airtable, which is not a code regression.

The Airtable and snapshot paths are still tested — explicitly, with stubs, in
`test_copy_sync.py`.

`OUTBOUND_LEDGER_ROOT` is the same idea one module over. `batch_fetch` and
every Apify wrapper append to `data/runs/<batch>.jsonl` now, so without this
a test run would write real-looking retrieval lines into the repo's own
ledger — and the first honest cost figure this machine produces would have a
test suite mixed into it. Pointed at a temp directory that goes away with the
process.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["OUTBOUND_COPY_SOURCE"] = "csv"

_ledger_root = tempfile.TemporaryDirectory(prefix="outbound-ledger-")
os.environ["OUTBOUND_LEDGER_ROOT"] = _ledger_root.name

# And no Apify token, so no test anywhere can reach the paid layer. Every Apify
# path is tested against stubs; a token in the environment only ever means the
# suite behaves differently on a developer machine than in CI, which is how a
# real regression in the approval gate passed here and failed there.
for _var in ("APIFY_TOKEN", "APIFY_API_TOKEN"):
    os.environ.pop(_var, None)

from outbound import anchors  # noqa: E402

anchors.reset_cache()
