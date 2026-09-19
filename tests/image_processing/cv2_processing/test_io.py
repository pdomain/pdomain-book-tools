"""Tests for cv2_processing.io module."""

import pathlib

import numpy as np
import pytest

pytest.importorskip("cv2")

from pdomain_book_tools.image_processing.cv2_processing.io import (
    read_image,
    write_jpg,
    write_png,
)

pillow_heif = pytest.importorskip("pillow_heif")


class TestReadWritePng:
    def test_write_then_read_png(self, tmp_path: pathlib.Path) -> None:
        # Build a simple BGR image
        img = np.zeros((10, 12, 3), dtype=np.uint8)
        img[2:8, 2:10] = [40, 80, 120]
        out_path = pathlib.Path(tmp_path / "test.png")

        write_png(img, out_path)
        assert out_path.exists()
        assert out_path.stat().st_size > 0

        loaded = read_image(out_path)
        assert loaded is not None
        assert loaded.shape == img.shape
        np.testing.assert_array_equal(loaded, img)


class TestReadImageFailures:
    """Regression coverage for M-05.

    Pre-fix ``read_image`` returned ``cv2.imread``'s ``None`` sentinel
    silently, so downstream code (e.g. ``rescale_image`` doing
    ``img.shape[:2]``) crashed with a confusing ``AttributeError`` that
    didn't name the offending path. Post-fix it raises an explicit,
    path-naming exception.
    """

    def test_missing_file_raises_file_not_found(self, tmp_path: pathlib.Path) -> None:
        missing = pathlib.Path(tmp_path / "does_not_exist.png")
        with pytest.raises(FileNotFoundError, match=str(missing.resolve())):
            read_image(missing)

    def test_corrupt_file_raises_value_error(self, tmp_path: pathlib.Path) -> None:
        # An existing but undecodeable file: cv2.imread returns None, not raises.
        corrupt = pathlib.Path(tmp_path / "corrupt.png")
        corrupt.write_bytes(b"this is not a valid PNG payload")
        with pytest.raises(ValueError, match=str(corrupt.resolve())):
            read_image(corrupt)


class TestWriteJpg:
    def test_write_jpg_creates_file(self, tmp_path: pathlib.Path) -> None:
        img = np.zeros((20, 20, 3), dtype=np.uint8)
        img[:, :] = [120, 80, 40]
        out_path = pathlib.Path(tmp_path / "test.jpg")

        write_jpg(img, out_path, quality=80)
        assert out_path.exists()
        assert out_path.stat().st_size > 0

        loaded = read_image(out_path)
        assert loaded is not None
        assert loaded.shape == img.shape


class TestWriteFailures:
    """Regression coverage for the image-io write-failure issue.

    Pre-fix, ``write_jpg``/``write_png`` discarded ``cv2.imwrite``'s boolean
    success return, so a full disk, a read-only directory, or a bad path
    reported success (returned ``None`` normally) while writing nothing to
    disk. Post-fix, a failed write raises a path-naming ``ValueError``.
    """

    def test_write_jpg_to_missing_directory_raises(
        self, tmp_path: pathlib.Path
    ) -> None:
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out_path = tmp_path / "no_such_dir" / "test.jpg"

        with pytest.raises(ValueError, match=str(out_path.resolve())):
            write_jpg(img, out_path)

        assert not out_path.exists()

    def test_write_png_to_missing_directory_raises(
        self, tmp_path: pathlib.Path
    ) -> None:
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out_path = tmp_path / "no_such_dir" / "test.png"

        with pytest.raises(ValueError, match=str(out_path.resolve())):
            write_png(img, out_path)

        assert not out_path.exists()


class TestReadImageHeif:
    """Regression coverage for the HEIF/AVIF identify-then-fail-to-load issue.

    ``formats.SUPPORTED_IMAGE_SUFFIXES`` claims HEIF support, but pre-fix
    ``read_image`` only tried ``cv2.imread``, which cannot decode HEIF and
    returns ``None``, so a real HEIC file raised ``ValueError`` even though
    it identifies as a supported image. Post-fix, ``read_image`` falls back
    to Pillow (via the ``pillow-heif`` opener registered in
    ``formats.py``) and returns a BGR array, matching cv2's channel order.
    """

    def test_heic_round_trips_with_correct_channel_order(
        self, tmp_path: pathlib.Path
    ) -> None:
        from PIL import Image

        pillow_heif.register_heif_opener()

        # Known-colour halves in RGB: left red, right blue.
        rgb = np.zeros((32, 32, 3), dtype=np.uint8)
        rgb[:, :16] = [255, 0, 0]
        rgb[:, 16:] = [0, 0, 255]

        heic_path = tmp_path / "photo.heic"
        Image.fromarray(rgb, mode="RGB").save(heic_path, format="HEIF")

        loaded = read_image(heic_path)

        assert loaded.shape == rgb.shape
        # cv2 convention is BGR: red pixels (RGB 255,0,0) must come back as
        # BGR (0,0,255), and blue pixels (RGB 0,0,255) as BGR (255,0,0). A
        # fallback that forgot the RGB->BGR swap would fail this assertion
        # even though the image "loaded".
        left_bgr = loaded[16, 4]
        right_bgr = loaded[16, 20]
        assert int(left_bgr[2]) > int(left_bgr[0])  # left half: red channel dominant
        assert int(right_bgr[0]) > int(
            right_bgr[2]
        )  # right half: blue channel dominant
