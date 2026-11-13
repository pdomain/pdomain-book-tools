---
Status: built
Owner: CT
Created: 2026-11-13
Last verified: 2026-11-13
Kind: architecture
---

# Image loading and output failures

## Agent Index

- **Kind:** architecture
- **Status:** built
- **Last verified:** 2026-11-13
- **Read when:** loading page images, writing files, encoding PNG buffers, or changing format acceptance.
- **Search terms:** read_image, imwrite, imencode, BGR, RGB, HEIF, AVIF, formats.

Image loading uses OpenCV first and Pillow as a fallback. The image helpers expose decode and output failures rather than returning unusable results.

## Reads return BGR images

`read_image(path)` resolves the path and raises `FileNotFoundError` when it does not exist. If `cv2.imread` returns `None`, Pillow tries the same path, converts to RGB, and then converts RGB to BGR. This preserves the OpenCV channel convention, including HEIF/AVIF fallback reads.

The Pillow helper catches `OSError` and `ValueError`. If neither decoder succeeds, `read_image` raises a path-naming `ValueError`. OpenCV exceptions are not translated by this wrapper. Importing `formats` registers the Pillow HEIF and AVIF openers; unavailable plugins are logged at debug level.

## Writes and encoding check success

`write_jpg` uses JPEG quality 100 by default. `write_png` requests compression level 9. Both resolve the output path, return `None` on success, and raise a path-naming `ValueError` when `cv2.imwrite` returns false. They do not create parent directories or catch OpenCV exceptions.

`encode_bgr_image_as_png` passes BGR input directly to `imencode('.png', ...)`, without a channel swap. It returns the encoded NumPy buffer on success. A false success flag raises `ValueError` with `encode_bgr_image_as_png: cv2.imencode failed to encode the image`. Exceptions raised by OpenCV propagate.

## Identification remains permissive

`formats.is_image_file` accepts either a supported extension or a recognized signature. The file must be readable and provide at least 16 header bytes. A signature/extension mismatch warns and still accepts. A known extension with an unknown signature also warns and accepts. Identification does not guarantee successful decoding.

Strict validation for untrusted inputs remains open in [gh-191](../issues/2026-05-22-gh-191-strict-image-validation.md). It is not the current contract.

## Evidence

- **Code:** `pdomain_book_tools/image_processing/cv2_processing/io.py`, `encoding.py`, and `pdomain_book_tools/image_processing/formats.py`.
- **Tests inspected:** `tests/image_processing/cv2_processing/test_io.py` covers PNG round trips, missing/corrupt input, missing output directories, and HEIC channel order. `test_encoding.py` covers PNG output, BGR round trips, and failed encoding. `tests/image_processing/test_formats.py` covers identification.
- **Commits:** `907d8db` adds fallback reads and failed-write checks; `b1f76b1` adds failed-encode rejection.
- **Verified:** source and tests inspected on 2026-11-13 at `50fcb0e`; no new execution result is claimed here.
