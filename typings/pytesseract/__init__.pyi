"""Local type stub for ``pytesseract``.

``pytesseract`` ships no ``py.typed`` marker (see
``.venv/lib/python3.13/site-packages/pytesseract``). This stub covers only
the API surface this repo calls (grepped from
``pdomain_book_tools/ocr/cv2_tesseract.py`` and
``pdomain_book_tools/ocr/document.py``): the ``Output`` string-constant
namespace, ``image_to_data``/``image_to_string`` (overloaded on
``output_type`` to mirror the runtime dict-dispatch in
``pytesseract.pytesseract.image_to_data``/``image_to_string``), and
``get_tesseract_version``.
"""

from os import PathLike
from typing import Final, Literal, TypeAlias, overload

import numpy as np
import numpy.typing as npt
from packaging.version import Version
from pandas import DataFrame
from PIL.Image import Image

ImageLike: TypeAlias = str | PathLike[str] | Image | npt.NDArray[np.generic]

class Output:
    BYTES: Final = "bytes"
    DATAFRAME: Final = "data.frame"
    DICT: Final = "dict"
    STRING: Final = "string"

@overload
def image_to_data(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    *,
    output_type: Literal["data.frame"],
    timeout: int = 0,
) -> DataFrame: ...
@overload
def image_to_data(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    *,
    output_type: Literal["bytes"],
    timeout: int = 0,
) -> bytes: ...
@overload
def image_to_data(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    *,
    output_type: Literal["dict"],
    timeout: int = 0,
) -> dict[str, object]: ...
@overload
def image_to_data(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    # Matches the real pytesseract default (``output_type=Output.STRING``).
    output_type: Literal["string"] = "string",
    timeout: int = 0,
) -> str: ...
@overload
def image_to_string(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    *,
    output_type: Literal["bytes"],
    timeout: int = 0,
) -> bytes: ...
@overload
def image_to_string(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    *,
    output_type: Literal["dict"],
    timeout: int = 0,
) -> dict[str, str]: ...
@overload
def image_to_string(
    image: ImageLike,
    lang: str | None = None,
    config: str = "",
    nice: int = 0,
    # Matches the real pytesseract default (``output_type=Output.STRING``).
    output_type: Literal["string"] = "string",
    timeout: int = 0,
) -> str: ...
def get_tesseract_version(cached: bool = False) -> Version: ...
