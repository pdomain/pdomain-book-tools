from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest

from pdomain_book_tools.pgdp.f2.project_rules import (
    ProjectRule,
    ProjectRuleRegistry,
)
from pdomain_book_tools.typography.labels import StyleLabel

if TYPE_CHECKING:
    from typing import Literal


def test_rule_lookup_requires_matching_project_and_comments_hash() -> None:
    comments = b"Use <u> for printed underlining."
    rule = ProjectRule(
        project_id="project-1",
        project_comments_sha256=hashlib.sha256(comments).hexdigest(),
        tag_name="u",
        label=StyleLabel.UNDERLINE,
        rule_ref="project-1/u/v1",
    )
    registry = ProjectRuleRegistry((rule,))

    assert registry.resolve("project-1", comments, "u") == rule
    assert registry.resolve("project-1", b"different comments", "u") is None
    assert registry.resolve("project-2", comments, "u") is None


def test_rule_registry_does_not_promote_undefined_font_changes() -> None:
    registry = ProjectRuleRegistry()

    assert registry.resolve("project-1", b"comments", "f") is None


@pytest.mark.parametrize(
    ("tag_name", "label"),
    [
        ("u", StyleLabel.ITALIC),
        ("f", StyleLabel.UNDERLINE),
        ("f", StyleLabel.BOLD),
    ],
)
def test_rule_rejects_a_label_not_approved_for_the_tag(
    tag_name: Literal["f", "u"], label: StyleLabel
) -> None:
    with pytest.raises(ValueError, match="label"):
        ProjectRule(
            project_id="project-1",
            project_comments_sha256="a" * 64,
            tag_name=tag_name,
            label=label,
            rule_ref="project-1/rule/v1",
        )
