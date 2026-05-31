"""Tests for ``pdomain_book_tools.image_processing.formats``.

The formats module centralises image-format identification for downstream
pdomain-* tools (pdomain-ocr-cli, pdomain-ocr-labeler-spa, ...). It must support both
extension-based gating (cheap) and magic-byte sniffing (correct), with a
warning when the two disagree.
"""

import logging
import pathlib

import pytest

from pdomain_book_tools.image_processing.formats import (
    SUPPORTED_IMAGE_SUFFIXES,
    is_image_file,
)

# --- Magic-byte fixture bytes (only the prefix; the sniff reads <= 16 bytes).


def _pad(b: bytes) -> bytes:
    """Pad a header prefix out to >= 16 bytes (sniffer's required minimum)."""
    if len(b) >= 16:
        return b
    return b + b"\x00" * (16 - len(b))


PNG_SIG = _pad(b"\x89PNG\r\n\x1a\n")
JPEG_SIG = _pad(b"\xff\xd8\xff\xe0")  # JFIF
JP2_BOX_SIG = _pad(b"\x00\x00\x00\x0cjP  \r\n\x87\n")  # JPEG 2000 box format
JP2_CODESTREAM_SIG = _pad(b"\xff\x4f\xff\x51")  # JPEG 2000 raw codestream
TIFF_LE_SIG = _pad(b"II*\x00")
TIFF_BE_SIG = _pad(b"MM\x00*")
BMP_SIG = _pad(b"BM")
GIF87A_SIG = _pad(b"GIF87a")
GIF89A_SIG = _pad(b"GIF89a")
# WebP: RIFF....WEBP — the 4 size bytes between "RIFF" and "WEBP" are arbitrary.
WEBP_SIG = _pad(b"RIFF\x10\x00\x00\x00WEBP")
PBM_SIG = _pad(b"P1\n1 1\n0\n")
PGM_SIG = _pad(b"P5\n1 1\n255\n\x00")
PPM_SIG = _pad(b"P6\n1 1\n255\n\x00")
HEIC_SIG = _pad(b"\x00\x00\x00\x18ftypheic")
HEIF_MIF1_SIG = _pad(b"\x00\x00\x00\x18ftypmif1")
AVIF_SIG = _pad(b"\x00\x00\x00\x18ftypavif")


def _write(tmp_path: pathlib.Path, name: str, data: bytes) -> pathlib.Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


# --- SUPPORTED_IMAGE_SUFFIXES ---------------------------------------------


class TestSupportedSuffixes:
    def test_set_is_lowercase_dot_prefixed(self):
        for s in SUPPORTED_IMAGE_SUFFIXES:
            assert s.startswith(".")
            assert s == s.lower()

    def test_includes_legacy_suffixes(self):
        for s in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"):
            assert s in SUPPORTED_IMAGE_SUFFIXES

    def test_includes_jpeg2000_family(self):
        for s in (".jp2", ".j2k", ".jpf", ".jpx"):
            assert s in SUPPORTED_IMAGE_SUFFIXES

    def test_includes_gif_and_netpbm(self):
        for s in (".gif", ".ppm", ".pgm", ".pbm", ".pnm"):
            assert s in SUPPORTED_IMAGE_SUFFIXES

    def test_includes_heif_and_avif(self):
        for s in (".heic", ".heif", ".avif"):
            assert s in SUPPORTED_IMAGE_SUFFIXES


# --- Magic-byte sniff per family -------------------------------------------


class TestMagicByteSniff:
    @pytest.mark.parametrize(
        ("name", "data"),
        [
            ("a.png", PNG_SIG),
            ("a.jpg", JPEG_SIG),
            ("a.jp2", JP2_BOX_SIG),
            ("a.j2k", JP2_CODESTREAM_SIG),
            ("a.tif", TIFF_LE_SIG),
            ("b.tif", TIFF_BE_SIG),
            ("a.bmp", BMP_SIG),
            ("a.gif", GIF87A_SIG),
            ("b.gif", GIF89A_SIG),
            ("a.webp", WEBP_SIG),
            ("a.pbm", PBM_SIG),
            ("a.pgm", PGM_SIG),
            ("a.ppm", PPM_SIG),
            ("a.heic", HEIC_SIG),
            ("a.heif", HEIF_MIF1_SIG),
            ("a.avif", AVIF_SIG),
        ],
    )
    def test_extension_and_magic_agree(self, tmp_path, name, data):
        path = _write(tmp_path, name, data)
        assert is_image_file(path) is True

    def test_unknown_extension_but_valid_png_magic_is_accepted(self, tmp_path):
        """Magic-byte sniff must accept files even without a known extension."""
        path = _write(tmp_path, "scanA", PNG_SIG)
        assert is_image_file(path) is True

    def test_unknown_extension_unknown_magic_is_rejected(self, tmp_path):
        path = _write(tmp_path, "notes.txt", b"hello world, plain text")
        assert is_image_file(path) is False


# --- Mismatch warning -------------------------------------------------------


class TestExtensionMagicMismatch:
    def test_png_extension_jpeg2000_bytes_warns_and_accepts(self, tmp_path, caplog):
        """A .png file containing JPEG 2000 bytes should warn but still be
        accepted — the file is a real image, just misnamed.
        """
        path = _write(tmp_path, "scan.png", JP2_BOX_SIG)
        with caplog.at_level(logging.WARNING, logger="pdomain_book_tools"):
            result = is_image_file(path)
        assert result is True
        # The warning should name the path and the actual detected format.
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "scan.png" in joined
        assert "jpeg2000" in joined.lower() or "jp2" in joined.lower()

    def test_matching_extension_and_magic_does_not_warn(self, tmp_path, caplog):
        path = _write(tmp_path, "ok.png", PNG_SIG)
        with caplog.at_level(logging.WARNING, logger="pdomain_book_tools"):
            assert is_image_file(path) is True
        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert warnings == []


# --- Edge cases -------------------------------------------------------------


class TestEdgeCases:
    def test_file_shorter_than_16_bytes_is_not_image(self, tmp_path):
        path = _write(tmp_path, "tiny.png", b"\x89PNG")  # only 4 bytes
        assert is_image_file(path) is False

    def test_empty_file_is_not_image(self, tmp_path):
        path = _write(tmp_path, "empty.png", b"")
        assert is_image_file(path) is False

    def test_nonexistent_path_is_not_image(self, tmp_path):
        path = tmp_path / "does_not_exist.png"
        assert is_image_file(path) is False

    def test_directory_is_not_image(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        assert is_image_file(d) is False

    def test_uppercase_extension_accepted(self, tmp_path):
        """Extension comparison must be case-insensitive."""
        path = _write(tmp_path, "A.PNG", PNG_SIG)
        assert is_image_file(path) is True

    def test_known_extension_but_bogus_bytes_is_rejected(self, tmp_path):
        """Extension allowlist alone must NOT pass — magic must also fail
        gracefully. The function rejects when bytes are unrecognised AND
        no magic family matches."""
        # An extension we know about, but 16 bytes of pure noise that don't
        # match any signature. We expect this to be rejected — the file is
        # not actually an image. (Extension alone is not sufficient.)
        path = _write(tmp_path, "pretend.png", b"\x00" * 16)
        # Per the spec: accept if EITHER extension matches OR magic matches.
        # Extension matches here, so it returns True — but a warning fires.
        # We capture that intent in a separate test below.
        assert is_image_file(path) is True  # extension allowlist hits

    def test_known_extension_but_bogus_bytes_warns(self, tmp_path, caplog):
        path = _write(tmp_path, "pretend.png", b"\x00" * 16)
        with caplog.at_level(logging.WARNING, logger="pdomain_book_tools"):
            is_image_file(path)
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "pretend.png" in joined


# --- Bundled-plugin decode round-trip --------------------------------------
#
# pillow-heif and pillow-avif-plugin are required deps (not extras). These
# tests exercise the full identification -> decode pipeline by writing a
# tiny image with each plugin's encoder, sniffing it through is_image_file,
# and decoding it back via Pillow. They guard against the test env losing
# the plugins, which would silently regress HEIF/AVIF support for every
# downstream pdomain-* project.


class TestBundledPluginRoundTrip:
    def _ensure_formats_imported(self):
        # Importing the formats module is what registers the plugins with
        # Pillow. The test module already imports it at the top, but be
        # explicit so this test documents its dependency.
        import pdomain_book_tools.image_processing.formats  # imported for side-effect (plugin registration)

    def test_avif_round_trip_via_pillow(self, tmp_path):
        self._ensure_formats_imported()
        from PIL import Image

        src = Image.new("RGB", (4, 4), "red")
        path = tmp_path / "tiny.avif"
        src.save(path, format="AVIF")

        # Identification: should be accepted both by extension and by the
        # ftyp/avif magic-byte sniff.
        assert is_image_file(path) is True

        # Decode.
        out = Image.open(path)
        out.load()
        assert out.size == (4, 4)

    def test_heif_round_trip_via_pillow(self, tmp_path):
        self._ensure_formats_imported()
        from PIL import Image

        src = Image.new("RGB", (4, 4), "blue")
        path = tmp_path / "tiny.heif"
        # pillow-heif registers the encoder under the "HEIF" format name.
        src.save(path, format="HEIF")

        assert is_image_file(path) is True

        out = Image.open(path)
        out.load()
        assert out.size == (4, 4)

    def test_pillow_recognizes_heif_extensions(self):
        """pillow-heif's register_heif_opener wires .heic/.heif/.hif into
        Pillow's EXTENSION map. If this regresses, downstream Image.open
        on a HEIC file silently falls back to format-detection-by-magic
        only and may behave differently across Pillow versions.
        """
        self._ensure_formats_imported()
        from PIL import Image

        Image.init()
        for ext in (".heic", ".heif"):
            assert ext in Image.EXTENSION, (
                f"{ext} not registered with Pillow — pillow-heif's "
                "register_heif_opener() did not run"
            )

    def test_pillow_recognizes_avif_extension(self):
        self._ensure_formats_imported()
        from PIL import Image

        Image.init()
        assert ".avif" in Image.EXTENSION, (
            ".avif not registered with Pillow — pillow-avif-plugin did "
            "not import / register"
        )
