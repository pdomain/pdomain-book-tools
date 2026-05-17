import warnings

from ipywidgets import HTML, HBox
from numpy import ndarray

from pd_book_tools.geometry.bounding_box import BoundingBox
from pd_book_tools.ocr.image_utilities import (
    get_cropped_encoded_image,
    get_encoded_image,
)

# TODO move those image utilities to a more appropriate location


def get_html_styled_span(item: str = "", css_style: str = "") -> HTML:
    return HTML(f"<span {css_style}>{item}</span>")


def get_formatted_text_html_span(
    linecolor_css: str = "unset",
    font_family_css: str = "unset",
    font_size_css: str = "unset",
    text: str = "",
    additional_css: str = "",
) -> HTML:
    return HTML(
        f"<span style='color:{linecolor_css}; font-family:{font_family_css}; font-size: {font_size_css}; {additional_css}'>{text if text else ''}</span>"
    )


def get_hbox_widget_for_colored_text(linecolor_css, text: str):
    text_hbox = HBox()
    text_hbox.children = [
        get_formatted_text_html_span(linecolor_css=linecolor_css, text=text)
    ]
    return text_hbox


def get_html_string_from_image_src(
    data_src_string: str,
    height: str = "",
    width: str = "",
    padding: str = "",
    border: str = "",
):
    # Encode the image as PNG
    img_html_string: str = (
        f'<img style="{height} {width} {padding} {border}" src="{data_src_string}"/>'
    )
    return img_html_string


def get_html_string_from_image(
    img: ndarray,
    height: str = "",
    width: str = "",
    padding: str = "",
    border: str = "",
):
    # Encode the image as PNG
    _, _, data_src_string = get_encoded_image(img)
    return get_html_string_from_image_src(
        data_src_string, height, width, padding, border
    )


def get_html_string_from_cropped_image(
    img: ndarray,
    bounding_box: BoundingBox,
    height: str = "",
    width: str = "",
    padding: str = "",
    border: str = "",
):
    # Encode the cropped image as PNG
    _, _, _, data_src_string = get_cropped_encoded_image(img, bounding_box)
    return get_html_string_from_image_src(
        data_src_string, height, width, padding, border
    )


def get_html_widget_from_cropped_image(img: ndarray, bounding_box: BoundingBox):
    img_html_string: str = get_html_string_from_cropped_image(img, bounding_box)
    return HTML(img_html_string)


def get_hbox_widget_for_cropped_image(
    img: ndarray | BoundingBox,
    bounding_box: BoundingBox | ndarray,
):
    """Wrap the cropped-image HTML widget in an :class:`HBox`.

    Canonical signature: ``(img, bounding_box)`` — matches every other
    function in this module. The legacy reversed order
    ``(bounding_box, img)`` is detected at runtime and accepted with a
    :class:`DeprecationWarning`; callers should swap argument order.
    """
    # Detect legacy (bounding_box, img) order. ndarray vs BoundingBox is
    # a clean type discriminator — they never overlap.
    if isinstance(img, BoundingBox) and isinstance(bounding_box, ndarray):
        warnings.warn(
            "get_hbox_widget_for_cropped_image(bounding_box, img) is deprecated; "
            "pass arguments in (img, bounding_box) order to match the rest of "
            "the ipynb_widgets API.",
            DeprecationWarning,
            stacklevel=2,
        )
        img, bounding_box = bounding_box, img
    image_hbox = HBox()
    image_hbox.children = [get_html_widget_from_cropped_image(img, bounding_box)]  # pyright: ignore[reportArgumentType]  # swap of (bounding_box, img) → (img, bounding_box) is handled by isinstance guard above
    return image_hbox
