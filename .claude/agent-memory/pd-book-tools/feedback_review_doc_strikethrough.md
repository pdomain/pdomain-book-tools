---
name: Mark fixed bugs in docs/review/bugs-*.md
description: When a /loop iteration fixes a bug listed in docs/review/bugs-*.md, follow the strikethrough+[FIXED in <sha>] convention as a small follow-up commit so the review index stays in sync with reality.
type: feedback
---

# Mark fixed bugs in docs/review/bugs-*.md

When a /loop iteration fixes a bug listed in `docs/review/bugs-*.md`, update the review index in a small follow-up commit. The pattern, set by H-01..H-03 in `bugs-high.md`:

`## [FIXED in <short-sha>] ~~H-XX — original heading text~~`

**Why:** Review docs are the canonical index of remaining work for the loop. If they aren't kept in sync, the loop loses track of what's actually outstanding and may re-investigate already-fixed bugs.

**How to apply:**

1. Fix the bug, commit code+test (`fix(<module>): ...` referencing the review ID in the body).
2. Edit `docs/review/bugs-*.md` to strike through the fixed entry's heading and prepend `[FIXED in <short-sha>]`.
3. Commit as `docs(review): mark H-XX fixed in <sha>`.
4. If the markdownlint pre-commit hook complains, run `uv run pre-commit run markdownlint-cli2-fix --hook-stage manual --files docs/review/*.md` to auto-fix, then re-stage.

Leave *truly unrelated* uncommitted changes alone (e.g. modified-but-unstaged `docs/ROADMAP.md`).
