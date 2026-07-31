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
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["OUTBOUND_COPY_SOURCE"] = "csv"

from outbound import anchors  # noqa: E402

anchors.reset_cache()
