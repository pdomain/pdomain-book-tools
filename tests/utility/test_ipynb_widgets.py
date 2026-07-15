"""Tests for utility.ipynb_widgets module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

pytest.importorskip("ipywidgets")

from pdomain_book_tools.geometry.bounding_box import (
    BoundingBox,  # after importorskip guard
)
from pdomain_book_tools.utility.ipynb_widgets import (
    HTML,
    HBox,
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
    def test_returns_html_widget(self) -> None:
        widget = get_html_styled_span(item="hello", css_style="style='color:red'")
        assert isinstance(widget, HTML)

    def test_default_args(self) -> None:
        widget = get_html_styled_span()
        assert isinstance(widget, HTML)

    def test_nonempty_item_well_formed_html(self) -> None:
        widget = get_html_styled_span(item="hello", css_style="style='color:red'")
        assert widget.value.startswith("<span")
        assert widget.value.endswith("</span>")
        assert "hello" in widget.value
        assert "style='color:red'" in widget.value

    def test_empty_item_well_formed_html(self) -> None:
        widget = get_html_styled_span(item="", css_style="style='color:red'")
        assert widget.value.startswith("<span")
        assert widget.value.endswith("</span>")
        # No stray closing tag without an opener
        assert widget.value.count("<span") == widget.value.count("</span>")

    def test_default_args_well_formed_html(self) -> None:
        widget = get_html_styled_span()
        assert widget.value.startswith("<span")
        assert widget.value.endswith("</span>")


class TestGetFormattedTextHtmlSpan:
    def test_returns_html_widget_with_text(self) -> None:
        widget = get_formatted_text_html_span(
            linecolor_css="red",
            font_family_css="sans",
            font_size_css="12px",
            text="hello",
        )
        assert isinstance(widget, HTML)
        assert "hello" in widget.value
        assert "color:red" in widget.value
        assert "font-family:sans" in widget.value
        assert "font-size: 12px" in widget.value

    def test_empty_text_renders_empty_span(self) -> None:
        widget = get_formatted_text_html_span()
        assert isinstance(widget, HTML)
        assert widget.value.startswith("<span")
        assert widget.value.endswith("</span>")

    def test_additional_css_included(self) -> None:
        widget = get_formatted_text_html_span(
            text="x", additional_css="font-weight:bold;"
        )
        assert "font-weight:bold" in widget.value


class TestGetHboxWidgetForColoredText:
    def test_returns_hbox_with_html_child(self) -> None:
        hbox = get_hbox_widget_for_colored_text("blue", "hello")
        assert isinstance(hbox, HBox)
        assert len(hbox.children) == 1
        child = hbox.children[0]
        assert isinstance(child, HTML)
        assert "hello" in child.value


class TestGetHtmlStringFromImageSrc:
    def test_returns_string_with_data_src(self) -> None:
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

    def test_default_styles_are_empty(self) -> None:
        out = get_html_string_from_image_src("data:image/png;base64,abc")
        assert "data:image/png;base64,abc" in out
        assert out.startswith("<img")


class TestGetHtmlStringFromImage:
    @patch("pdomain_book_tools.utility.ipynb_widgets.get_encoded_image")
    def test_uses_encoded_data_src(self, mock_get_encoded: MagicMock) -> None:
        mock_get_encoded.return_value = (b"x", "b64", "data:image/png;base64,xyz")
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = get_html_string_from_image(img, height="height:10px")
        mock_get_encoded.assert_called_once()
        assert "data:image/png;base64,xyz" in out
        assert "height:10px" in out


class TestGetHtmlStringFromCroppedImage:
    @patch("pdomain_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_uses_cropped_data_src(self, mock_get_cropped: MagicMock) -> None:
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
    @patch("pdomain_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_returns_html_widget(self, mock_get_cropped: MagicMock) -> None:
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,abc",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
        widget = get_html_widget_from_cropped_image(img, bbox)
        assert isinstance(widget, HTML)
        assert "data:image/png;base64,abc" in widget.value


class TestGetHboxWidgetForCroppedImage:
    @patch("pdomain_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_returns_hbox_with_html_child(self, mock_get_cropped: MagicMock) -> None:
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,abc",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
        # Canonical (img, bounding_box) order (R-28 standardization).
        hbox = get_hbox_widget_for_cropped_image(img, bbox)
        assert isinstance(hbox, HBox)
        assert len(hbox.children) == 1
        assert isinstance(hbox.children[0], HTML)

    @patch("pdomain_book_tools.utility.ipynb_widgets.get_cropped_encoded_image")
    def test_legacy_argument_order_emits_deprecation(
        self, mock_get_cropped: MagicMock
    ) -> None:
        # Backward-compat: legacy (bounding_box, img) order still works
        # but raises DeprecationWarning. Detected by type discriminator
        # (BoundingBox vs ndarray).
        mock_get_cropped.return_value = (
            np.zeros((1, 1, 3), dtype=np.uint8),
            b"x",
            "b64",
            "data:image/png;base64,abc",
        )
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = BoundingBox.from_ltrb(0, 0, 1, 1, is_normalized=True)
        with pytest.warns(DeprecationWarning, match="img, bounding_box"):
            hbox = get_hbox_widget_for_cropped_image(bbox, img)
        assert isinstance(hbox, HBox)
