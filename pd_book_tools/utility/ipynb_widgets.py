from ipywidgets import HTML, HBox
from numpy import ndarray

from pd_book_tools.geometry.bounding_box import BoundingBox

from ..ocr.image_utilities import get_cropped_encoded_image, get_encoded_image


def get_html_styled_span(item: str = "", css_style: str = "") -> HTML:
    return HTML(f"<span {css_style}>" + item if item else "" + "</span>")


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
    text_HBox = HBox()
    text_HBox.children = [
        get_formatted_text_html_span(linecolor_css=linecolor_css, text=text)
    ]
    return text_HBox


def get_html_string_from_image_src(
    data_src_string: str,
    height: str = "height: 14px",
    padding: str = "",
    border: str = "",
):
    # Encode the image as PNG
    img_html_string: str = (
        f'<img style="{height}; {padding}; {border};" src="{data_src_string}"/>'
    )
    return img_html_string


def get_html_string_from_image(
    img: ndarray,
    height: str = "height: 14px",
    padding: str = "",
    border: str = "",
):
    # Encode the image as PNG
    _, _, data_src_string = get_encoded_image(img)
    return get_html_string_from_image_src(data_src_string, height, padding, border)


def get_html_string_from_cropped_image(
    img: ndarray,
    bounding_box: BoundingBox,
    height: str = "height: 14px",
    padding: str = "",
    border: str = "",
):
    # Encode the cropped image as PNG
    _, _, data_src_string = get_cropped_encoded_image(img, bounding_box)
    return get_html_string_from_image_src(data_src_string, height, padding, border)


def get_html_widget_from_cropped_image(img: ndarray, bounding_box: BoundingBox):
    img_html_string: str = get_html_string_from_cropped_image(img, bounding_box)
    html_widget = HTML(img_html_string)
    return html_widget


def get_hbox_widget_for_cropped_image(bounding_box: BoundingBox, img: ndarray):
    ImageHBox = HBox()
    ImageHBox.children = [get_html_widget_from_cropped_image(img, bounding_box)]
    return ImageHBox
