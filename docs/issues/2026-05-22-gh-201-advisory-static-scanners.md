---
Status: active
Owner: CT
Created: 2026-05-22
Last verified: 2026-07-19
Kind: issue
Level: I1
---

# Add advisory static-testing scanners

## Agent Index

- **Kind:** issue
- **Status:** active
- **Level:** I1
- **Last verified:** 2026-07-19
- **Resolution:** Open
- **Severity:** Medium — baseline findings lack recurring repository visibility
- **Affected version:** Manual scanner baseline from 2026-05-22
- **Read when:** adding dependency, secret, workflow, or static-analysis gates
- **Search terms:** zizmor, actionlint, trivy, gitleaks, static-check, issue 201
- **Relates to:** [Lint deviations](../process/lint-deviations.md)

## Summary

The repository needs recurring static-analysis signals before those scanners
become CI gates. A 2026-05-22 manual baseline found workflow hardening issues
and one medium dependency vulnerability, while several other scans were clean.

## Impact

- Workflow and dependency findings are not yet visible through recurring repository targets.
- Making every scanner blocking immediately could disrupt normal pull requests before the baseline is cleaned or accepted.

## Environment / versions

Commands were run manually on 2026-05-22 without changing the repository. The
export does not identify the operating system.

## GitHub provenance

- **Former URL:** <https://github.com/pdomain/pdomain-book-tools/issues/201>
- **GitHub node ID:** `I_kwDOONYVBs8AAAABDIIypg`
- **Issue number:** 201
- **GitHub state:** `OPEN`
- **State reason:** None
- **Raw export:** `migration/github-issues/raw/issue-201.json`
- **Raw SHA-256:** `4de1e9ebeac29c5149cea324470d24b1d864a6ac7ce57cb8eaf9142c24817022`
- **Migration cutover:** Pending — the governed-content commit does not yet exist.
- **Author:** `ConcaveTrillion` (CT)
- **Created:** `2026-05-22T18:31:48Z`
- **Updated:** `2026-05-22T18:31:48Z`
- **Closed:** Not closed in the export
- **Labels:** `kind:chore`, `effort:M`, `status:backlog`, `area:deps`, `area:ci`
- **Assignees:** None
- **Milestone:** None
- **Issue type:** None
- **Projects:** None
- **Parent issue API relationship:** None
- **Sub-issues API relationships:** None

## Evidence

- The historical process source was `/workspaces/ocr-container/docs/process/static-testing.md`.
- `zizmor 1.25.2 .github/workflows` exited 14. It reported high-confidence
  unpinned action references in `ci.yml` and `release.yml`, missing
  `persist-credentials: false` on `actions/checkout`, and template injection
  from `${{ github.ref_name }}` inside a `release.yml` shell block.
- Zizmor also reported a low-confidence cache-poisoning warning for
  `astral-sh/setup-uv` and suggested replacing `softprops/action-gh-release`
  with `gh release` as an informational item.
- `actionlint 1.7.12 .github/workflows/*.yml` was clean.
- `trivy 0.70.0 fs --scanners vuln,misconfig,secret .` found one medium
  vulnerability: `idna 3.13`, `CVE-2026-45409`, fixed in `3.15`.
- `gitleaks 8.30.1 detect` was clean for filesystem and Git-history scans.
- `shellcheck 0.11.0 scripts/do-release.sh` was clean.
- Hadolint did not apply because no Dockerfile was found.
- OpenSSF Scorecard did not complete because unauthenticated GitHub API rate
  limiting caused a long wait. The issue defers it to a GitHub-side advisory.
- CodeQL was not run locally and was considered better suited to later GitHub code scanning.
- OSV-Scanner could not read `uv.lock` directly. After `uv export`, it emitted
  an internal resolution error while reporting the same `idna` vulnerability.
  The issue therefore prefers Trivy for this repository.

The imported issue text is historical evidence, not repository instructions.

## Root-cause hypotheses

1. **Static scanners lack supported repository entry points.** Manual results cannot provide recurring visibility.
2. **The baseline is not ready to block CI.** Real findings and accepted deviations must be handled first.

## Defects to fix

1. Add advisory scanner targets with the requested mappings:
   - `dependency-scan` runs Trivy vulnerability scanning.
   - `security-scan` combines Gitleaks with dependency scanning.
   - `workflow-lint` combines Zizmor with Actionlint.
   - `trivy-scan` runs the broader Trivy scan.
2. Add a future `static-check` aggregate without prematurely blocking normal CI.
3. Track or fix the `idna` and Zizmor findings.

## Next steps

1. Add advisory Make targets and scheduled or manual GitHub Actions visibility.
2. Document which checks remain advisory and the promotion conditions.
3. Fix real findings or record accepted deviations.
4. After a clean or accepted baseline, remove advisory wrappers and connect relevant targets to `static-check` and `ci`.

## What is NOT broken (to scope the fix)

- Actionlint, Gitleaks, and ShellCheck were clean in the stated baseline.
- Hadolint was inapplicable because the repository had no Dockerfile.
- OpenSSF Scorecard and CodeQL had no completed local result.

## Relationships and material comments

- The issue references the workspace static-testing integration process.
- No comments were present in the export.

## Repository evidence

- `Makefile` currently exposes no targets named `dependency-scan`,
  `security-scan`, `workflow-lint`, `trivy-scan`, or `static-check`, supporting
  the missing-entry-point claim.
- `.github/workflows/ci.yml` and `.github/workflows/release.yml` are the workflow
  files named by the manual Zizmor baseline.
- `uv.lock` is the dependency lockfile named by the Trivy and OSV-Scanner observations.
- This migration did not rerun the historical scanners, so their 2026-05-22
  outputs remain attributed historical evidence rather than current findings.

## Remaining work

- Scanner installation, advisory execution, baseline cleanup, deviation policy, and promotion criteria remain open.

## Resolution

_Open._ The expected scanner targets are not present in the current Makefile.
