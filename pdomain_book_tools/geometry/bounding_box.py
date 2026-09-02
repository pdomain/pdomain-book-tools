"""Re-export of :class:`BoundingBox`, moved to ``pdomain-book-contracts``.

``BoundingBox`` is a pure-Python value type with no imaging-stack
dependency, so it now lives in
``pdomain_book_contracts.geometry.bounding_box``. This module keeps the
old import path (``pdomain_book_tools.geometry.bounding_box``) working for
existing callers.

``BoundingBox.refine()``, ``.crop_bottom()``, and ``.crop_top()`` are
back-compat wrappers that dispatch through a provider registry (see
``pdomain_book_contracts.geometry.bounding_box.register_image_ops``).
:mod:`pdomain_book_tools.geometry.image_ops` registers itself as that
provider at its own import time — that free-function implementation stays
in this package, since ``pdomain-book-contracts`` must not depend on cv2.
Callers of the wrapper methods must import ``image_ops`` (directly or
transitively) first, or the methods raise ``ImageOpsUnavailableError``.

``_BoundingBoxDict`` is re-exported too: it is underscore-prefixed (an
implementation detail, not part of the documented public API), but existing
tests import it directly from this module path, so it moves with
``BoundingBox``.
"""

from __future__ import annotations

from pdomain_book_contracts.geometry.bounding_box import (
    BoundingBox,
    _BoundingBoxDict,  # pyright: ignore[reportPrivateUsage]
)

__all__ = ["BoundingBox", "_BoundingBoxDict"]
