"""Centralised image-format identification for pd-* tools.

Downstream pd-* projects (``pd-ocr-cli``, ``pd-ocr-labeler``, ...) repeatedly
re-implemented "is this file an image?" checks that were extension-only and
incomplete (notably missing JPEG 2000, which OpenCV decodes natively via
``libopenjp2``). This module is the single source of truth for that question.

Two layers of identification:

1.  An **extension allowlist** (:data:`SUPPORTED_IMAGE_SUFFIXES`) covering
    everything cv2 + Pillow can decode out of the box, including the
    HEIF / AVIF families (Pillow plugins are bundled as required deps).
2.  A **magic-byte sniff** that reads the first 16 bytes of the file and
    matches against known image signatures.

:func:`is_image_file` accepts a file when EITHER check matches. When the
extension and the sniffed format **disagree** (e.g. a file named ``.png``
that contains JPEG 2000 bytes), we log a WARNING naming the path and the
detected format, but still return ``True`` — the file is a real image, just
mislabelled. Decoding is handled elsewhere (cv2 / Pillow); this module's
job is identification, not loading.

Side effect on import
---------------------

Importing this module registers ``pillow-heif`` and ``pillow-avif-plugin``
with Pillow so that ``PIL.Image.open`` can subsequently decode HEIF/HEIC
and AVIF files. This is the single, documented place where that side
effect lives — downstream code does not need to (and should not) do the
registration itself. Both plugins are required dependencies of
``pd-book-tools``; if they are missing the import falls back gracefully
and emits a debug log, but identification (the magic-byte sniff) still
works regardless.
"""

from __future__ import annotations

import logging
import pathlib

logger = logging.getLogger(__name__)


# --- Pillow plugin registration --------------------------------------------
#
# pillow-heif and pillow-avif-plugin both register decoders with Pillow at
# import time. We do that exactly once here, on import of this module, so
# that downstream callers get HEIF/AVIF decode support transparently via
# Pillow's normal Image.open path. Both packages are declared as required
# deps in pyproject.toml, but we still guard the imports so a partial /
# broken install of pd-book-tools does not blow up at import time — the
# magic-byte sniff continues to work even if decode would later fail.

try:
    import pillow_heif as _pillow_heif  # pyright: ignore[reportMissingTypeStubs]

    _pillow_heif.register_heif_opener()  # pyright: ignore[reportUnknownMemberType]
except Exception as _heif_exc:  # pragma: no cover - import-time guard
    logger.debug(
        "pillow-heif not available; HEIF/HEIC decode will fail. (%s)",
        _heif_exc,
    )

try:
    import pillow_avif as _pillow_avif  # pyright: ignore[reportMissingTypeStubs]  # import for side-effect (plugin registration)
except Exception as _avif_exc:  # pragma: no cover - import-time guard
    logger.debug(
        "pillow-avif-plugin not available; AVIF decode will fail. (%s)",
        _avif_exc,
    )


# Default-supported suffixes. These are the formats cv2 + Pillow can decode
# on a stock install of pd-book-tools. HEIF/HEIC and AVIF support is wired
# in via pillow-heif and pillow-avif-plugin, both declared as required
# deps in pyproject.toml and registered with Pillow at the top of this
# module.
SUPPORTED_IMAGE_SUFFIXES: frozenset[str] = frozenset(
    {
        # PNG / JPEG / TIFF / BMP / WebP — the historical pd-ocr-cli set.
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
        # JPEG 2000 family — decoded by OpenCV's bundled libopenjp2.
        ".jp2",
        ".j2k",
        ".jpf",
        ".jpx",
        # GIF — Pillow decodes; cv2 only decodes the first frame.
        ".gif",
        # NetPBM family.
        ".ppm",
        ".pgm",
        ".pbm",
        ".pnm",
        # HEIF / AVIF — Pillow plugins are bundled as required deps and
        # registered at the top of this module.
        ".heic",
        ".heif",
        ".avif",
    }
)


# --- Magic-byte signatures --------------------------------------------------
#
# Each entry maps an offset-keyed prefix match to a short format name. We
# only read the first 16 bytes of the file, so every signature here must
# fit inside that window.
#
# The table is intentionally a list of (offset, prefix, format_name) tuples
# rather than a dict because some formats (WebP, ftyp-based HEIF/AVIF)
# require matching at a non-zero offset.

_MAGIC_BYTES: list[tuple[int, bytes, str]] = [
    (0, b"\x89PNG\r\n\x1a\n", "png"),
    (0, b"\xff\xd8\xff", "jpeg"),
    # JPEG 2000 box format (typical .jp2 / .jpf / .jpx).
    (0, b"\x00\x00\x00\x0cjP  \r\n\x87\n", "jpeg2000"),
    # JPEG 2000 raw codestream (.j2k).
    (0, b"\xff\x4f\xff\x51", "jpeg2000"),
    (0, b"II*\x00", "tiff"),
    (0, b"MM\x00*", "tiff"),
    (0, b"BM", "bmp"),
    (0, b"GIF87a", "gif"),
    (0, b"GIF89a", "gif"),
    # NetPBM ASCII / raw markers (P1..P6). Match the marker plus the
    # required following whitespace byte to avoid colliding with text
    # files that happen to start with "P1".
    (0, b"P1\n", "netpbm"),
    (0, b"P1 ", "netpbm"),
    (0, b"P1\r", "netpbm"),
    (0, b"P1\t", "netpbm"),
    (0, b"P2\n", "netpbm"),
    (0, b"P2 ", "netpbm"),
    (0, b"P2\r", "netpbm"),
    (0, b"P2\t", "netpbm"),
    (0, b"P3\n", "netpbm"),
    (0, b"P3 ", "netpbm"),
    (0, b"P3\r", "netpbm"),
    (0, b"P3\t", "netpbm"),
    (0, b"P4\n", "netpbm"),
    (0, b"P4 ", "netpbm"),
    (0, b"P4\r", "netpbm"),
    (0, b"P4\t", "netpbm"),
    (0, b"P5\n", "netpbm"),
    (0, b"P5 ", "netpbm"),
    (0, b"P5\r", "netpbm"),
    (0, b"P5\t", "netpbm"),
    (0, b"P6\n", "netpbm"),
    (0, b"P6 ", "netpbm"),
    (0, b"P6\r", "netpbm"),
    (0, b"P6\t", "netpbm"),
]

# WebP is RIFF...WEBP — a 4-byte size field separates them, so we check
# both prefixes individually below.
_WEBP_RIFF = b"RIFF"
_WEBP_TAG = b"WEBP"

# HEIF / AVIF use the ISO base-media ftyp box. Brand starts at offset 8.
_HEIF_BRANDS = frozenset(
    {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"}
)
_AVIF_BRANDS = frozenset({b"avif", b"avis"})


def _sniff_format(head: bytes) -> str | None:
    """Return a short format name for ``head`` (first <= 16 bytes), or None."""
    if len(head) < 16:
        return None

    for offset, prefix, name in _MAGIC_BYTES:
        end = offset + len(prefix)
        if end <= len(head) and head[offset:end] == prefix:
            return name

    # WebP: "RIFF" at 0, "WEBP" at 8.
    if head[0:4] == _WEBP_RIFF and head[8:12] == _WEBP_TAG:
        return "webp"

    # HEIF / AVIF: ISO BMFF "ftyp" box at offset 4, brand at offset 8.
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in _AVIF_BRANDS:
            return "avif"
        if brand in _HEIF_BRANDS:
            return "heif"

    return None


def is_image_file(path: pathlib.Path) -> bool:
    """Return True if ``path`` looks like an image file.

    Acceptance is the **union** of the extension allowlist and the
    magic-byte sniff: either signal is enough. When both fire but
    disagree (extension says PNG, bytes say JPEG 2000), a WARNING is
    logged and the file is still accepted — the user is told their file
    is misnamed but the pipeline does not reject real image data.

    Files shorter than 16 bytes are never accepted (no format we care
    about fits in less than 16 bytes of header).
    """
    try:
        path = pathlib.Path(path)
    except TypeError:
        return False

    suffix = path.suffix.lower()
    extension_match = suffix in SUPPORTED_IMAGE_SUFFIXES

    # Try to read the head. If the file is missing, a directory, or
    # unreadable, we fall back to extension-only — but per spec, files
    # shorter than 16 bytes are not images, and we treat read failures
    # the same way.
    head: bytes = b""
    try:
        with path.open("rb") as fh:
            head = fh.read(16)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
        return False

    if len(head) < 16:
        return False

    sniffed = _sniff_format(head)

    if sniffed is not None and extension_match:
        # Both fired. Check for disagreement.
        if not _suffix_matches_format(suffix, sniffed):
            logger.warning(
                "Image file %s has extension %s but its bytes look like %s; accepting anyway (file is likely misnamed).",
                path,
                suffix,
                sniffed,
            )
        return True

    if sniffed is not None:
        return True

    if extension_match:
        # Extension passes but sniff didn't recognise the bytes. Warn the
        # user — the file may be corrupt or in a sub-format we don't know.
        logger.warning(
            "Image file %s has known extension %s but its first 16 bytes do not match any known image signature; accepting on extension alone (decode may fail).",
            path,
            suffix,
        )
        return True

    return False


# Map sniffed format name -> the suffix family that should produce it.
# Used only by the mismatch warning to decide whether to fire.
_FORMAT_TO_SUFFIXES: dict[str, frozenset[str]] = {
    "png": frozenset({".png"}),
    "jpeg": frozenset({".jpg", ".jpeg"}),
    "jpeg2000": frozenset({".jp2", ".j2k", ".jpf", ".jpx"}),
    "tiff": frozenset({".tif", ".tiff"}),
    "bmp": frozenset({".bmp"}),
    "gif": frozenset({".gif"}),
    "webp": frozenset({".webp"}),
    "netpbm": frozenset({".ppm", ".pgm", ".pbm", ".pnm"}),
    "heif": frozenset({".heic", ".heif"}),
    "avif": frozenset({".avif"}),
}


def _suffix_matches_format(suffix: str, sniffed: str) -> bool:
    expected = _FORMAT_TO_SUFFIXES.get(sniffed)
    if expected is None:
        # Unknown sniffed format — be conservative, don't warn.
        return True
    return suffix in expected
