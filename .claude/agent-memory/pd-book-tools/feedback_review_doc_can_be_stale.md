---
name: Review docs can be stale; verify the bug actually exists in current code first
description: Per-bug /loop iterations must run grep/Read against the current source before writing the fix; docs/review/bugs-*.md was authored May 2026 and some items were already fixed in older commits
type: feedback
---

# Review docs can be stale; verify the bug exists first

Before treating a `docs/review/bugs-*.md` item as a real bug to fix:

1. Grep for the symptom (e.g. missing `def`, called name, regex pattern) in the production source the doc cites.
2. If the bug is not present, run `git log -S '<symbol>' -- <path>` to find when/how the issue was actually fixed (or never existed).

**Why:** H-04 in bugs-high.md claimed `Page.recompute_bounding_box` was undefined, but the method had existed since commit `2248366` (April 2025) — the review (May 2026) missed it. Blindly applying the "fix" would have either no-op'd or duplicated existing code.

**How to apply:** When running the /loop bug-fix workflow on this repo, treat step 1 ("verify bug present") as load-bearing, not a formality. If the bug is already fixed in current code, the iteration becomes a regression-lock test plus a doc mark explaining the staleness — not a no-op. Reference the prior fix's sha in the doc mark and commit body so future readers understand the chain.
