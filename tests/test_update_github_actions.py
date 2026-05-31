"""Tests for scripts/update_github_actions.py (pdomain action-pin refresher)."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from scripts import update_github_actions as uga


def _runner(responses: dict[str, object]):
    """Return a fake gh runner that returns canned JSON responses."""

    def run(command: list[str]) -> subprocess.CompletedProcess[str]:
        endpoint = command[2]  # gh api <endpoint>
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps(responses[endpoint]), stderr=""
        )

    return run


def test_gh_json_parses_response() -> None:
    runner = _runner({"repos/actions/checkout/releases/latest": {"tag_name": "v4.2.2"}})
    result = uga.gh_json("repos/actions/checkout/releases/latest", runner=runner)
    assert result == {"tag_name": "v4.2.2"}


def test_latest_release_lightweight_tag() -> None:
    sha = "a" * 40
    runner = _runner(
        {
            "repos/actions/checkout/releases/latest": {"tag_name": "v4.2.2"},
            "repos/actions/checkout/git/ref/tags/v4.2.2": {
                "object": {"sha": sha, "type": "commit"}
            },
        }
    )
    release = uga.latest_release("actions/checkout", runner=runner)
    assert release == uga.ActionRelease(tag="v4.2.2", sha=sha)


def test_latest_release_annotated_tag() -> None:
    tag_sha = "b" * 40
    commit_sha = "c" * 40
    runner = _runner(
        {
            "repos/astral-sh/setup-uv/releases/latest": {"tag_name": "v8.1.0"},
            "repos/astral-sh/setup-uv/git/ref/tags/v8.1.0": {
                "object": {"sha": tag_sha, "type": "tag"}
            },
            f"repos/astral-sh/setup-uv/git/tags/{tag_sha}": {
                "object": {"sha": commit_sha}
            },
        }
    )
    release = uga.latest_release("astral-sh/setup-uv", runner=runner)
    assert release == uga.ActionRelease(tag="v8.1.0", sha=commit_sha)


def test_update_workflow_refs_rewrites_sha(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    old_sha = "o" * 40
    wf.write_text(f"steps:\n  - uses: actions/checkout@{old_sha}  # v4\n")
    new_sha = "n" * 40
    releases = {"actions/checkout": uga.ActionRelease(tag="v4.2.2", sha=new_sha)}
    changed = uga.update_workflow_refs(wf, releases=releases)
    assert changed is True
    assert new_sha in wf.read_text()
    assert old_sha not in wf.read_text()


def test_update_workflow_refs_no_change(tmp_path: Path) -> None:
    sha = "a" * 40
    wf = tmp_path / "ci.yml"
    wf.write_text(f"steps:\n  - uses: actions/checkout@{sha}  # v4\n")
    releases = {"actions/checkout": uga.ActionRelease(tag="v4.2.2", sha=sha)}
    changed = uga.update_workflow_refs(wf, releases=releases)
    assert changed is False


def test_update_workflow_refs_ignores_unmanaged(tmp_path: Path) -> None:
    wf = tmp_path / "ci.yml"
    original = "steps:\n  - uses: some-org/unknown-action@deadbeef\n"
    wf.write_text(original)
    changed = uga.update_workflow_refs(wf, releases={})
    assert changed is False
    assert wf.read_text() == original


def test_update_github_actions_returns_changed_paths(tmp_path: Path) -> None:
    wf_dir = tmp_path
    old_sha = "o" * 40
    new_sha = "n" * 40
    (wf_dir / "ci.yml").write_text(
        f"steps:\n  - uses: actions/checkout@{old_sha}  # v4\n"
    )
    (wf_dir / "release.yml").write_text("steps:\n  - run: echo hello\n")

    responses: dict[str, object] = {
        "repos/actions/checkout/releases/latest": {"tag_name": "v4.2.2"},
        "repos/actions/checkout/git/ref/tags/v4.2.2": {
            "object": {"sha": new_sha, "type": "commit"}
        },
    }
    for action in uga.MANAGED_ACTIONS:
        if action == "actions/checkout":
            continue
        responses[f"repos/{action}/releases/latest"] = {"tag_name": "v1.0.0"}
        responses[f"repos/{action}/git/ref/tags/v1.0.0"] = {
            "object": {"sha": "x" * 40, "type": "commit"}
        }

    changed = uga.update_github_actions(workflow_dir=wf_dir, runner=_runner(responses))
    assert len(changed) == 1
    assert changed[0] == wf_dir / "ci.yml"
