"""Tests for :mod:`pd_book_tools.hf`."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest import mock

import pytest

from pd_book_tools.hf import (
    DEFAULT_DET_FILENAME,
    DEFAULT_HF_REPO,
    DEFAULT_RECO_FILENAME,
    LAYOUT_MODEL_FILES,
    OCR_MODEL_SIDECARS,
    hf_download,
    prefetch_layout_files,
    resolve_layout_source,
    resolve_ocr_models,
    short_revision,
    suppress_hf_unauth_warning,
)
from pd_book_tools.hf import models as hf_models_module


def test_constants_match_canonical_repo_layout():
    assert DEFAULT_HF_REPO == "CT2534/pd-ocr-models"
    assert DEFAULT_DET_FILENAME == "detection/pd-all-detection-model-finetuned.pt"
    assert DEFAULT_RECO_FILENAME == "recognition/pd-all-recognition-model-finetuned.pt"
    assert OCR_MODEL_SIDECARS == (".arch", ".vocab")
    assert LAYOUT_MODEL_FILES == (
        "config.json",
        "preprocessor_config.json",
        "model.safetensors",
    )


def test_short_revision_handles_none_short_long():
    assert short_revision(None) == "latest"
    assert short_revision("") == "latest"
    assert short_revision("abc") == "abc"
    assert short_revision("0123456789abcdef") == "01234567"


def test_suppress_hf_unauth_warning_filters_only_unauth_advisory():
    target_logger = logging.getLogger("huggingface_hub.utils._http")

    with suppress_hf_unauth_warning():
        # The filter should drop the advisory
        record_filtered = logging.LogRecord(
            name="huggingface_hub.utils._http",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="HF Hub: unauthenticated requests will be rate-limited; set HF_TOKEN.",
            args=(),
            exc_info=None,
        )
        # And not unrelated warnings
        record_kept = logging.LogRecord(
            name="huggingface_hub.utils._http",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="some other warning unrelated to auth",
            args=(),
            exc_info=None,
        )
        # Walk through filters attached
        passed_filtered = all(f.filter(record_filtered) for f in target_logger.filters)
        passed_kept = all(f.filter(record_kept) for f in target_logger.filters)
        assert passed_filtered is False
        assert passed_kept is True

    # On exit, no filters should remain installed by us
    assert target_logger.filters == []


def test_hf_download_calls_hf_hub_download_and_returns_path(tmp_path):
    fake_local = tmp_path / "weights.pt"
    fake_local.write_bytes(b"x")

    with mock.patch.dict(
        "sys.modules",
        {
            "huggingface_hub": mock.MagicMock(
                hf_hub_download=mock.MagicMock(return_value=str(fake_local)),
                try_to_load_from_cache=mock.MagicMock(return_value=None),
                _CACHED_NO_EXIST=object(),
            ),
            "huggingface_hub.utils": mock.MagicMock(EntryNotFoundError=Exception),
        },
    ):
        result = hf_download("repo/x", "weights.pt", revision="main")

    assert isinstance(result, Path)
    assert result == fake_local


def test_hf_download_silent_on_warm_cache(caplog, tmp_path):
    fake_local = tmp_path / "weights.pt"
    fake_local.write_bytes(b"x")

    sentinel = object()
    fake_hub = mock.MagicMock(
        hf_hub_download=mock.MagicMock(return_value=str(fake_local)),
        try_to_load_from_cache=mock.MagicMock(return_value=str(fake_local)),
        _CACHED_NO_EXIST=sentinel,
    )
    with (
        caplog.at_level(logging.INFO, logger="pd_book_tools.hf.download"),
        mock.patch.dict(
            "sys.modules",
            {
                "huggingface_hub": fake_hub,
                "huggingface_hub.utils": mock.MagicMock(EntryNotFoundError=Exception),
            },
        ),
    ):
        hf_download("repo/x", "weights.pt")

    cold_lines = [r for r in caplog.records if "Downloading" in r.getMessage()]
    assert cold_lines == []


def test_hf_download_logs_on_cold_cache(caplog, tmp_path):
    fake_local = tmp_path / "weights.pt"
    fake_local.write_bytes(b"x")

    fake_hub = mock.MagicMock(
        hf_hub_download=mock.MagicMock(return_value=str(fake_local)),
        try_to_load_from_cache=mock.MagicMock(return_value=None),
        _CACHED_NO_EXIST=object(),
    )
    with (
        caplog.at_level(logging.INFO, logger="pd_book_tools.hf.download"),
        mock.patch.dict(
            "sys.modules",
            {
                "huggingface_hub": fake_hub,
                "huggingface_hub.utils": mock.MagicMock(EntryNotFoundError=Exception),
            },
        ),
    ):
        hf_download("repo/x", "weights.pt", revision="abc123")

    cold_lines = [r for r in caplog.records if "Downloading" in r.getMessage()]
    assert len(cold_lines) == 1
    assert "weights.pt" in cold_lines[0].getMessage()
    assert "repo/x" in cold_lines[0].getMessage()


def test_hf_download_attempts_sidecars_and_swallows_missing(tmp_path):
    fake_main = tmp_path / "weights.pt"
    fake_main.write_bytes(b"x")

    class _NotFound(Exception):
        pass

    calls: list[str] = []

    def _hub_download(*, repo_id, filename, revision):
        calls.append(filename)
        if filename.endswith(".vocab"):
            raise _NotFound("missing")
        return str(fake_main if filename.endswith(".pt") else fake_main)

    fake_hub = mock.MagicMock(
        hf_hub_download=mock.MagicMock(side_effect=_hub_download),
        try_to_load_from_cache=mock.MagicMock(return_value=str(fake_main)),
        _CACHED_NO_EXIST=object(),
    )
    with mock.patch.dict(
        "sys.modules",
        {
            "huggingface_hub": fake_hub,
            "huggingface_hub.utils": mock.MagicMock(EntryNotFoundError=_NotFound),
        },
    ):
        hf_download("repo/x", "weights.pt", sidecars=(".arch", ".vocab"))

    # Main file plus both sidecars attempted
    assert calls == ["weights.pt", "weights.arch", "weights.vocab"]


def test_resolve_ocr_models_returns_local_paths_when_provided(tmp_path):
    det = tmp_path / "det.pt"
    reco = tmp_path / "reco.pt"
    det.write_bytes(b"x")
    reco.write_bytes(b"x")

    out_det, out_reco = resolve_ocr_models(detection_path=det, recognition_path=reco)
    assert out_det == det
    assert out_reco == reco


def test_resolve_ocr_models_rejects_partial_local():
    with pytest.raises(ValueError):
        resolve_ocr_models(detection_path=Path("/x"), recognition_path=None)


def test_resolve_ocr_models_falls_back_to_hf(monkeypatch, tmp_path):
    det = tmp_path / "det.pt"
    reco = tmp_path / "reco.pt"
    det.write_bytes(b"x")
    reco.write_bytes(b"x")

    seen: list[tuple[str, str]] = []

    def fake_hf_download(repo, filename, revision=None, sidecars=()):
        seen.append((repo, filename))
        return det if "detection" in filename else reco

    # Patch the hf_download symbol that the resolution helpers actually use
    # (imported into the models module at module-load time).
    monkeypatch.setattr(hf_models_module, "hf_download", fake_hf_download)

    out_det, out_reco = resolve_ocr_models(repo="some/repo", revision="rev1")
    assert out_det == det
    assert out_reco == reco
    assert seen == [
        ("some/repo", DEFAULT_DET_FILENAME),
        ("some/repo", DEFAULT_RECO_FILENAME),
    ]


def test_resolve_layout_source_none_returns_empty():
    assert resolve_layout_source("none") == (None, None, "")


def test_resolve_layout_source_none_takes_precedence_over_checkpoint(tmp_path):
    """``layout_model="none"`` must disable layout even when a checkpoint
    path is also supplied. Regression lock for review item H-20: the
    checkpoint branch must never be reached if the caller asked to disable
    layout entirely."""
    ckpt = tmp_path / "model.safetensors"
    ckpt.write_bytes(b"x")
    assert resolve_layout_source("none", layout_checkpoint=str(ckpt)) == (
        None,
        None,
        "",
    )
    # Also covers the "string-checkpoint treated as repo" branch — neither
    # should ever override the disable flag.
    assert resolve_layout_source("none", layout_checkpoint="org/repo-name") == (
        None,
        None,
        "",
    )


def test_resolve_layout_source_contour_takes_precedence_over_checkpoint(tmp_path):
    """Same precedence guarantee for ``layout_model="contour"``."""
    ckpt = tmp_path / "model.safetensors"
    ckpt.write_bytes(b"x")
    repo, rev, desc = resolve_layout_source("contour", layout_checkpoint=str(ckpt))
    assert repo is None
    assert rev is None
    assert "contour" in desc


def test_resolve_layout_source_contour():
    repo, rev, desc = resolve_layout_source("contour")
    assert repo is None
    assert rev is None
    assert "contour" in desc


def test_resolve_layout_source_local_checkpoint(tmp_path):
    ckpt = tmp_path / "model.safetensors"
    ckpt.write_bytes(b"x")
    repo, rev, desc = resolve_layout_source("pp-doclayout", layout_checkpoint=str(ckpt))
    assert repo is None
    assert rev is None
    assert desc == str(ckpt)


def test_resolve_layout_source_string_checkpoint_treated_as_repo():
    repo, rev, desc = resolve_layout_source(
        "pp-doclayout", layout_checkpoint="org/repo-name"
    )
    assert repo == "org/repo-name"
    assert rev is None
    assert "@latest" in desc


def test_prefetch_layout_files_calls_hf_download_per_file(monkeypatch):
    seen: list[tuple[str, str]] = []

    def fake(repo, filename, revision=None, sidecars=()):
        seen.append((repo, filename))
        return Path("/dev/null")

    monkeypatch.setattr(hf_models_module, "hf_download", fake)
    prefetch_layout_files("some/repo", "rev1")
    assert seen == [("some/repo", f) for f in LAYOUT_MODEL_FILES]
