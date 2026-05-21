#!/usr/bin/env bash
# do-release.sh — pre-flight, bump version, tag, and push.
#
# Computes the next version from the most recent `v*` tag and the chosen
# bump kind (major / minor / patch), then:
#   1. Verifies repo state (clean tree / on default branch / up-to-date
#      with origin).
#   2. Runs the full pre-flight (`make ci-slow`).
#   3. Creates a three-component annotated tag (vMAJOR.MINOR.PATCH).
#   4. Pushes the default branch + tag to origin.
#
# The pushed tag fires .github/workflows/release.yml, which builds the
# wheel + sdist, attests build provenance via Sigstore, publishes a
# GitHub Release with the artifacts attached, and pings pd-index so the
# self-hosted PEP 503 simple index regenerates immediately.
#
# Tag format: always three-component, even for major / minor bumps:
#   - patch from v0.4.2 → v0.4.3
#   - minor from v0.4.2 → v0.5.0
#   - major from v0.4.2 → v1.0.0
# This is the SemVer norm.
#
# Defaults to BUMP=minor.
#
# Branch: defaults to `main` (pd-book-tools' default branch).
#
# Escape hatches:
#   FORCE=1     skip the three repo-state guards (dirty tree / branch /
#               origin sync). The pre-flight still runs.
#   SKIP_PUSH=1 create the tag locally but don't push. Useful for
#               dry-running the version computation.
#
# Usage:
#   BUMP=major|minor|patch scripts/do-release.sh

set -eu

BUMP=${BUMP:-minor}
FORCE=${FORCE:-0}
SKIP_PUSH=${SKIP_PUSH:-0}
RELEASE_BRANCH=${RELEASE_BRANCH:-main}

if [ "$BUMP" != "major" ] && [ "$BUMP" != "minor" ] && [ "$BUMP" != "patch" ]; then
    echo "❌ BUMP must be one of: major, minor, patch (got: $BUMP)" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# Repo-state guards (skippable with FORCE=1)
# ---------------------------------------------------------------------------
if [ "$FORCE" != "1" ]; then
    # Clean working tree
    if [ -n "$(git status --porcelain)" ]; then
        echo "❌ Working tree is dirty. Commit or stash changes first." >&2
        echo "   (Set FORCE=1 to override — pre-flight still runs.)" >&2
        exit 1
    fi

    # On the release branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "$RELEASE_BRANCH" ]; then
        echo "❌ Not on $RELEASE_BRANCH (current branch: $CURRENT_BRANCH)." >&2
        echo "   Switch to $RELEASE_BRANCH before tagging. (Set FORCE=1 to override.)" >&2
        exit 1
    fi

    # Up-to-date with origin/<release branch>
    git fetch origin "$RELEASE_BRANCH" --quiet
    LOCAL=$(git rev-parse "$RELEASE_BRANCH")
    REMOTE=$(git rev-parse "origin/$RELEASE_BRANCH")
    BASE=$(git merge-base "$RELEASE_BRANCH" "origin/$RELEASE_BRANCH")
    if [ "$LOCAL" != "$REMOTE" ]; then
        if [ "$LOCAL" = "$BASE" ]; then
            echo "❌ Local $RELEASE_BRANCH is behind origin/$RELEASE_BRANCH. Pull first." >&2
            echo "   (Set FORCE=1 to override.)" >&2
            exit 1
        elif [ "$REMOTE" = "$BASE" ]; then
            echo "ℹ️  Local $RELEASE_BRANCH is ahead of origin/$RELEASE_BRANCH (will be pushed)."
        else
            echo "❌ $RELEASE_BRANCH and origin/$RELEASE_BRANCH have diverged." >&2
            echo "   (Set FORCE=1 to override.)" >&2
            exit 1
        fi
    fi
else
    echo "⚠️  FORCE=1 — skipping repo-state guards. Pre-flight still runs."
fi

# ---------------------------------------------------------------------------
# Compute next version (always three-component)
# ---------------------------------------------------------------------------
LATEST=$(git tag --list 'v*' --sort=-version:refname | head -1)
if [ -z "$LATEST" ]; then LATEST="v0.0.0"; fi

# Strip leading "v" and split. Accepts v1, v1.2, or v1.2.3 — missing
# components default to 0 so we can normalize legacy two-component tags.
VER_NO_V=${LATEST#v}
MAJOR=$(echo "$VER_NO_V" | awk -F. '{print ($1 == "" ? 0 : $1)}')
MINOR=$(echo "$VER_NO_V" | awk -F. '{print ($2 == "" ? 0 : $2)}')
PATCH=$(echo "$VER_NO_V" | awk -F. '{print ($3 == "" ? 0 : $3)}')

if [ "$BUMP" = "major" ]; then
    MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0
elif [ "$BUMP" = "minor" ]; then
    MINOR=$((MINOR + 1)); PATCH=0
else
    PATCH=$((PATCH + 1))
fi

VERSION="v$MAJOR.$MINOR.$PATCH"

# Refuse to overwrite an existing tag.
if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
    echo "❌ Tag $VERSION already exists. Aborting." >&2
    exit 1
fi

echo "📦 Latest tag: $LATEST"
echo "🎯 Next tag:   $VERSION (bump=$BUMP)"

# ---------------------------------------------------------------------------
# Pre-flight (NEVER skipped, even with FORCE=1)
# ---------------------------------------------------------------------------
echo ""
echo "🚦 Running pre-flight: make ci-slow"
echo "   (This may download the layout/OCR models on first run and take a while.)"
echo ""
if ! make ci-slow; then
    echo "" >&2
    echo "❌ Pre-flight (make ci-slow) failed. No tag created." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Tag (+ push, unless SKIP_PUSH=1)
# ---------------------------------------------------------------------------
echo ""
echo "🏷️  Creating annotated tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"

if [ "$SKIP_PUSH" = "1" ]; then
    echo "ℹ️  SKIP_PUSH=1 — tag created locally but not pushed."
    echo "   To push later: git push origin $RELEASE_BRANCH --follow-tags"
    exit 0
fi

echo "🚀 Pushing $RELEASE_BRANCH + tag to origin..."
git push origin "$RELEASE_BRANCH" --follow-tags

echo ""
echo "✅ Released $VERSION."
echo "   Watch the release workflow: https://github.com/ConcaveTrillion/pd-book-tools/actions"
echo "   Release page (once workflow finishes): https://github.com/ConcaveTrillion/pd-book-tools/releases/tag/$VERSION"
