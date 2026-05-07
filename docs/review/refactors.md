# Refactor Opportunities

Structural, design, and API improvements that are not bugs but would reduce
maintenance burden, improve correctness guarantees, and make the library easier
to use correctly. Organized roughly by impact.

---

**Status (2026-05-07):** 29 of 30 review-numbered items closed. Closed
items (FIXED / DECLINED / FIXED-with-deprecation) live in
[`archive/refactors.md`](archive/refactors.md). Only one DEFERRED
structural-coupling item remains (R-02). New refactor ideas should be
added here under the next available `R-NN` number; when closed,
**move** the entry into `archive/refactors.md` rather than annotating
it FIXED in place — see [`README.md`](README.md) for the workflow.

---

## [DEFERRED] R-02 — `Page` uses `@dataclass` but also defines a custom `__init__` — pick one

**Deferred:** The pattern is real (custom `__init__` shadows the
generated one and silently relies on class-level annotation defaults to
make `_cv2_numpy_page_image_*` accessible — verified 2026-05 that this
works in practice rather than raising `AttributeError` as the review
claimed; review is partly stale on the symptom).

A behavior-pinning regression test (`tests/test_page_behavior_pin.py`,
landed 2026-05-07 in commit 8dd9e16) pins the observable surface
(constructor signature, all attribute defaults, ``to_dict``
round-trip, ``rotation_applied`` validator). The structural conversion
itself was attempted but reverted on 2026-05-07 because of an
unforeseen InitVar / property name collision:

- Two of the constructor parameters that the custom ``__init__``
  accepts (``items`` and ``cv2_numpy_page_image``) are also names of
  ``@property`` definitions on the class. When declared as
  ``InitVar`` fields with a class-body default of ``None``, the
  ``@property`` descriptors assigned later in the class body
  override the class attribute. Python's ``@dataclass`` decorator
  reads ``getattr(cls, name)`` to determine the default for each
  field at decoration time, so it picks up the property object —
  which then gets passed into ``__post_init__`` as the "default
  value" of the InitVar. Using ``field(default=None)`` did not
  change this behavior (the dataclass machinery still resolves the
  property object as the field's class attribute).
- A clean fix requires renaming the constructor parameters
  (breaking the kwarg contract), or restructuring the property
  layer (e.g. moving the ``items`` getter to a method like
  ``get_items()`` and making ``items`` a plain field), or
  retaining a small custom ``__init__`` shim — all of which defeat
  the spirit of "go full ``@dataclass``."

The cleanest path forward is to redesign Page's properties (drop the
``items`` copy-on-read, fold ``cv2_numpy_page_image`` setter into an
explicit ``set_image()`` method). This is a focused public-API
discussion that's better as its own iteration than tacked on to
R-01/R-03. The behavior-pin test ensures any future attempt has a
safety net.

**File:** `pd_book_tools/ocr/page.py`, lines 57–200

`@dataclass` generates an `__init__` that is immediately superseded by the custom one.
Dataclass `field(default_factory=list, init=False)` declarations like `_items` are
never initialized by the generated `__init__` (which never runs). Image cache fields
(`_cv2_numpy_page_image_*`) are declared as dataclass fields but only set in
`refresh_page_images()`.

**Direction:** convert fully to `@dataclass` (using `__post_init__` for
computed fields) and eliminate the custom `__init__` — but only after
deciding how to handle the property/field name collisions on
``items`` and ``cv2_numpy_page_image``.
