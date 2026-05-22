"""Tests for the shared SPDX license allowlist module.

``pd_book_tools.licenses`` is the single source of truth for SPDX license
identifier validation across the ``pd-*`` repos. These tests pin the
public API (``SPDX_VALID_IDS`` and ``is_valid_spdx_id``) and confirm the
vendored JSON data file ships and loads.
"""

from __future__ import annotations

import importlib.resources

from pd_book_tools.licenses import SPDX_VALID_IDS, is_valid_spdx_id


def test_spdx_valid_ids_is_nonempty_frozenset_of_str():
    assert isinstance(SPDX_VALID_IDS, frozenset)
    assert len(SPDX_VALID_IDS) > 0
    assert all(isinstance(item, str) for item in SPDX_VALID_IDS)


def test_known_good_ids_present():
    for spdx_id in (
        "Apache-2.0",
        "MIT",
        "CC0-1.0",
        "OFL-1.1",
        "GPL-3.0-or-later",
        "Unlicense",
    ):
        assert spdx_id in SPDX_VALID_IDS, spdx_id


def test_is_valid_spdx_id_accepts_valid_ids():
    assert is_valid_spdx_id("Apache-2.0")
    assert is_valid_spdx_id("MIT")
    assert is_valid_spdx_id("CC0-1.0")
    assert is_valid_spdx_id("OFL-1.1")


def test_is_valid_spdx_id_rejects_invalid_ids():
    assert not is_valid_spdx_id("not-a-license")
    assert not is_valid_spdx_id("")
    assert not is_valid_spdx_id("  ")


def test_is_valid_spdx_id_is_case_sensitive():
    # SPDX identifiers are case-sensitive; the lowercase form is invalid.
    assert is_valid_spdx_id("Apache-2.0")
    assert not is_valid_spdx_id("apache-2.0")
    assert not is_valid_spdx_id("APACHE-2.0")


def test_is_valid_spdx_id_handles_non_str_input():
    # Signature says str, but defensive callers may pass anything;
    # must return False rather than raise.
    assert not is_valid_spdx_id(None)  # type: ignore[arg-type]
    assert not is_valid_spdx_id(123)  # type: ignore[arg-type]
    assert not is_valid_spdx_id(["MIT"])  # type: ignore[arg-type]


def test_vendored_json_data_file_loadable():
    resource = importlib.resources.files("pd_book_tools.data").joinpath(
        "spdx_licenses.json"
    )
    assert resource.is_file()
    text = resource.read_text(encoding="utf-8")
    assert '"licenses"' in text
    assert '"licenseId"' in text


def test_vendored_spdx_data_has_third_party_attribution():
    """The vendored SPDX data ships an adjacent third-party notice naming
    its upstream source and license, so redistributors can trace it."""
    notice = importlib.resources.files("pd_book_tools.data").joinpath(
        "THIRD-PARTY-NOTICES.md"
    )
    assert notice.is_file()
    text = notice.read_text(encoding="utf-8")
    # Must name the upstream project, its repository, and the data license.
    assert "license-list-data" in text
    assert "spdx/license-list-data" in text
    assert "CC0-1.0" in text
    # Must reference the specific vendored file.
    assert "spdx_licenses.json" in text
