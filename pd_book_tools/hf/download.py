"""Low-level Hugging Face Hub download primitive.

A thin wrapper around :func:`huggingface_hub.hf_hub_download` that:

- Emits a single user-friendly ``Downloading X from Y`` log line on cold cache
  (silent on warm cache).
- Suppresses HF Hub's unauthenticated-requests advisory (public model
  downloads intentionally support anonymous access; the warning is noise).
- Best-effort fetches optional sidecar files (``.arch``, ``.vocab``) when
  configured.

Higher-level resolution helpers (:func:`resolve_ocr_models`, etc.) live in
:mod:`pd_book_tools.hf.models` and are re-exported from
:mod:`pd_book_tools.hf`.
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path, PurePosixPath

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override  # pyright: ignore[reportUnreachable]

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def suppress_hf_unauth_warning():
    """Filter HF Hub's "unauthenticated requests" advisory only.

    Public model downloads intentionally support anonymous access, so the
    warning is noise for the common path. Other HF Hub warnings still
    surface.
    """

    class _Filter(logging.Filter):
        @override
        def filter(self, record: logging.LogRecord) -> bool:
            msg = record.getMessage().lower()
            return not ("unauthenticated requests" in msg and "hf hub" in msg)

    target = logging.getLogger("huggingface_hub.utils._http")
    f = _Filter()
    target.addFilter(f)
    try:
        yield
    finally:
        target.removeFilter(f)


def hf_download(
    repo_id: str,
    filename: str,
    revision: str | None = None,
    sidecars: tuple[str, ...] = (),
) -> Path:
    """Download ``filename`` from ``repo_id`` and return its cached local path.

    On a cold cache, emits a single ``Downloading X from Y`` line via the
    ``pd_book_tools.hf.download`` logger. On a warm cache, no extra output.

    ``sidecars`` is a best-effort sibling-extension fetch — e.g. passing
    ``(".arch", ".vocab")`` for an OCR ``.pt`` checkpoint pulls
    ``checkpoint.arch`` / ``checkpoint.vocab`` if present in the repo and
    silently skips when they are not. Use only for file types that
    conventionally carry sidecars; layout files don't.

    Raises :class:`ImportError` if ``huggingface_hub`` is not installed.
    """
    from huggingface_hub import (
        hf_hub_download,  # pyright: ignore[reportUnknownVariableType]
    )

    try:
        from huggingface_hub import _CACHED_NO_EXIST, try_to_load_from_cache

        cached = try_to_load_from_cache(
            repo_id=repo_id, filename=filename, revision=revision
        )
        already_cached = cached is not None and cached is not _CACHED_NO_EXIST
    except Exception:  # older / future hub versions: assume cold to be safe
        already_cached = False

    if not already_cached:
        logger.info(
            "Downloading %s from %s (revision=%s)",
            filename,
            repo_id,
            revision or "latest",
        )

    with suppress_hf_unauth_warning():
        local = hf_hub_download(repo_id=repo_id, filename=filename, revision=revision)

    if sidecars:
        try:
            # huggingface_hub>=0.22 moved exceptions to .errors; fall back for older
            from huggingface_hub.errors import (
                EntryNotFoundError as _HFNotFound,
            )
        except ImportError:
            try:
                from huggingface_hub.utils import (
                    EntryNotFoundError as _HFNotFound,  # pyright: ignore[reportPrivateImportUsage]
                )
            except ImportError:
                _HFNotFound = Exception  # type: ignore[assignment,misc]
        for ext in sidecars:
            # Use PurePosixPath because HF Hub filenames are POSIX-style
            # repo paths regardless of host OS. The previous
            # ``filename.rsplit(".", 1)[0] + ext`` split on the rightmost
            # dot in the entire path, which is wrong when the filename
            # has no extension but a parent directory contains a dot
            # (e.g. ``"my.dir/weights"`` → ``"my.arch"`` instead of
            # ``"my.dir/weights.arch"``). PurePosixPath.with_suffix
            # correctly replaces (or attaches) only the file's extension.
            p = PurePosixPath(filename)
            sidecar = str(p.with_suffix(ext))
            try:
                with suppress_hf_unauth_warning():
                    _ = hf_hub_download(
                        repo_id=repo_id, filename=sidecar, revision=revision
                    )
            except _HFNotFound:
                pass

    return Path(local)


__all__ = ["hf_download", "suppress_hf_unauth_warning"]
