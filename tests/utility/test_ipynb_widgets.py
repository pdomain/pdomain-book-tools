"""Tests for utility.ipynb_widgets module."""

from unittest.mock import patch

import numpy as np
import pytest

ipywidgets = pytest.importorskip("ipywidgets")

from pd_book_tools.geometry.bounding_box import BoundingBox  # noqa: E402
from pd_book_tools.utility.ipynb_widgets import (  # noqa: E402
    get_formatted_text_html_span,
    get_hbox_widget_for_colored_text,
    get_hbox_widget_for_cropped_image,
    get_html_string_from_cropped_image,
    get_html_string_from_image,
    get_html_string_from_image_src,
    get_html_styled_span,
    get_html_widget_from_cropped_image,
)


class TestGetHtmlStyledSpan:
    def test_returns_html_widget(self):
        widget = get_html_styled_span(item="hello", css_style="style='color:red'")
        assert isinstance(widget, ipywidgets.HTML)

    def test_default_args(self):
        widget = get_html_styled_span()
        assert isinstance(widget, ipywidgets.HTML)


class TestGetFormattedTextHtmlSpan:
    def test_returns_html_widget_with_text(self):
        widget = get_formatted_text_html_span(
            linecolor_css="red",
            font_family_css="sans",
            font_size_css="12px",
            text="hello",
        )
        assert isinstance(widget, ipywidgets.HTML)
        assert "hello" in widget.value
        assert "color:red" in widget.value
        assert "font-family:sans" in widget.value
        assert "font-size: 12px" in widget.value

    def test_empty_text_renders_empty_span(self):
        widget = get_formatted_text_html_span()
        assert isinstance(widget, ipywidgets.HTML)
        assert widget.value.startswith("<span")
        assert widget.value.endswith("</span>")

    def test_additional_css_included(self):
        widget = get_formatted_text_html_span(
            text="x", additional_css="font-weight:bold;"
        )
        assert "font-weight:bold" in widget.value


class TestGetHboxWidgetForColoredText:
    def test_returns_hbox_with_html_child(self):
        hbox = get_hbox_widget_for_colored_text("blue", "hello")
        assert isinstance(hbox, ipywidgets.HBox)
        assert len(hbox.children) == 1
        assert isinstance(hbox.children[0], ipywidgets.HTML)
        assert "hello" in hbox.children[0].value


class TestGetHtmlStringFromImageSrc:
    def test_returns_string_with_data_src(self):
        out = get_html_string_from_image_src(
            "data:image/png;base64,xyz",
            height="height:10px",
            width="width:20px",
            padding="padding:1px",
            border="border:1px solid",
        )
        assert "data:image/png;base64,xyz" in out
        assert "height:10px" in out
        assert "width:20px" in out
        assert "padding:1px" in out
        assert "border:1px solid" in out
        assert out.startswith("<img")

    def test_default_styles_are_empty(self):
        out = get_html_string_from_image_src("data:image/png;base64,abc")
        assert "data:image/png;base64,abc" in out
        assert out.startswith("<img")


class TestGetHtmlStringFromImage:
    @patch("pd_book_tools.utility.ipynb_widgets.get_encoded_image")
    def test_uses_encoded_data_src(self, mock_get_encoded):
        mock_get_encoded.return_value = (b"x", "b64", "data:image/png;base64,xyz")
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = get_html_string_from_image(img, height="height:10px")
        mock_get_encoded.assert_called_once()
        assert "data:image/png;base64,xyz" in out
        assert "height:10px" in out


class TestGetHtmlStringFromCroppedImage:
    @patch("pd_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_uses_cropped_data_src(self, mock_get_cropped):
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,cropped",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0.1, 0.1, 0.5, 0.5, is_normalized=True)
        out = get_html_string_from_cropped_image(img, bbox, width="width:5px")
        mock_get_cropped.assert_called_once_with(img, bbox)
        assert "data:image/png;base64,cropped" in out
        assert "width:5px" in out


class TestGetHtmlWidgetFromCroppedImage:
    @patch("pd_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_returns_html_widget(self, mock_get_cropped):
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,abc",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
        widget = get_html_widget_from_cropped_image(img, bbox)
        assert isinstance(widget, ipywidgets.HTML)
        assert "data:image/png;base64,abc" in widget.value


class TestGetHboxWidgetForCroppedImage:
    @patch("pd_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_returns_hbox_with_html_child(self, mock_get_cropped):
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,abc",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
        hbox = get_hbox_widget_for_cropped_image(bbox, img)
        assert isinstance(hbox, ipywidgets.HBox)
        assert len(hbox.children) == 1
        assert isinstance(hbox.children[0], ipywidgets.HTML)
