"""Re-export of the SPDX license allowlist, moved to ``pdomain-book-contracts``.

``SPDX_VALID_IDS`` and ``is_valid_spdx_id`` are pure-Python (loading only
the vendored SPDX data via ``importlib.resources``) with no imaging-stack
dependency, so they now live in ``pdomain_book_contracts.licensing``,
along with the vendored ``data/spdx_licenses.json`` file and its
third-party attribution notice. This module keeps the old import path
(``pdomain_book_tools.licenses``) working for existing callers.
"""

from __future__ import annotations

from pdomain_book_contracts.licensing import SPDX_VALID_IDS, is_valid_spdx_id

__all__ = ["SPDX_VALID_IDS", "is_valid_spdx_id"]
