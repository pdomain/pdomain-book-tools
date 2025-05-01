import base64
import pathlib
from enum import Enum
from logging import DEBUG as logging_DEBUG
from logging import getLogger

import cv2
import numpy as np
import torch
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from IPython.display import display
from ipywidgets import (
    HTML,
    BoundedIntText,
    Button,
    # GridBox,
    HBox,
    Image,
    Layout,
    RadioButtons,
    Tab,
    VBox,
)

from ..geometry.bounding_box import BoundingBox
from ..image_processing.cv2_processing.encoding import encode_bgr_image_as_png
from ..ocr.block import Block
from ..ocr.document import Document
from ..ocr.image_utilities import get_cropped_image
from ..ocr.page import Page
from ..ocr.word import Word
from .pgdp_results import PGDPExport, PGDPPage

# Configure logging
logger = getLogger(__name__)
ui_logger = getLogger(__name__ + ".UI")


def get_html_string_from_cropped_image(img: np.ndarray, bounding_box: BoundingBox):
    # Encode the cropped image as PNG
    _, _, data_src_string = get_cropped_image(img, bounding_box)
    img_html_string: str = (
        f'<img style="height: 14px; padding: 2px; border: 1px solid black;" src="{data_src_string}"/>'
    )
    return img_html_string


def get_html_widget_from_cropped_image(img: np.ndarray, bounding_box: BoundingBox):
    img_html_string: str = get_html_string_from_cropped_image(img, bounding_box)
    html_widget = HTML(img_html_string)
    return html_widget


no_padding_margin = Layout(padding="0px", margin="0px", flex="1 1 auto")


class LineMatching(Enum):
    SHOW_EXACT_MATCHES = 1
    SHOW_ONLY_MISMATCHES = 2


class IpynbPageEditor:
    """
    UI for adding/removing lines within in a page
    """

    line_matching_configuration: LineMatching.SHOW_EXACT_MATCHES

    _current_pgdp_page: PGDPPage
    _current_ocr_page: Page

    refresh_image_callable: callable = None

    def _observe_show_exact_line_matches(self, change=None):
        new = self.show_exact_line_matches_radiobuttons.value
        if self.show_exact_line_matches == new:
            # do nothing
            return
        self.line_matching_configuration = new
        self.rebuild_content_ui()

    editor_line_matching_vbox_header: VBox
    editor_line_matching_vbox_header_buttons: HBox
    show_exact_line_matches_radiobuttons: RadioButtons
    editor_line_matching_vbox_content: VBox
    editor_line_matching_vbox_footer: VBox

    editor_line_matching_vbox: VBox

    monospace_font_name: str
    monospace_font_path: pathlib.Path

    def init_font(
        self,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
    ):
        self.monospace_font_name = monospace_font_name
        if isinstance(monospace_font_path, str):
            monospace_font_path = pathlib.Path(monospace_font_path)
        self.monospace_font_path = monospace_font_path.resolve()

    def init_header_ui(self):
        self.editor_line_matching_vbox_header = VBox()
        self.editor_line_matching_vbox_header.layout = no_padding_margin

        self.editor_line_matching_vbox_header_buttons = HBox()
        self.editor_line_matching_vbox_header_buttons.layout = no_padding_margin

        # Create radio button in header for exact matches
        self.show_exact_line_matches_radiobuttons = RadioButtons(
            options={
                "Show Exact Matches": LineMatching.SHOW_EXACT_MATCHES,
                "Show Only Mismatches": LineMatching.SHOW_ONLY_MISMATCHES,
            },
            value=LineMatching.SHOW_ONLY_MISMATCHES,
            description="",
            disabled=False,
            orientation="horizontal",
            layout=Layout(width="max-content"),
        )
        self.show_exact_line_matches_radiobuttons.observe(
            handler=self._observe_show_exact_line_matches,
        )

        self.editor_line_matching_vbox_header_buttons.children = [
            Button(description="Show Exact Matches"),
            Button(description="Show Only Mismatches"),
        ]

        editor_line_matching_vbox_header_children = [
            HTML(
                f"<span style='font-family:{self.monospace_font_name}; font-size: 12px;'>Page-Level Cleanup</span>"
            ),
            self.show_exact_line_matches_radiobuttons,
        ]
        if ui_logger.level == logging_DEBUG:
            editor_line_matching_vbox_header_children.insert(
                index=0, obj=HTML("<div>DebugMode</div>")
            )

        self.editor_line_matching_vbox_header.children = (
            editor_line_matching_vbox_header_children
        )

    def init_footer_ui(self):
        pass

    def init_ui(self):
        self.editor_line_matching_vbox_header = VBox()
        self.editor_line_matching_vbox_header.layout = no_padding_margin
        self.init_header_ui()
        self.editor_line_matching_vbox_footer = VBox()
        self.editor_line_matching_vbox_footer.layout = no_padding_margin
        self.init_footer_ui()
        self.editor_line_matching_vbox_content = VBox()
        self.editor_line_matching_vbox_content.layout = no_padding_margin
        self.rebuild_content_ui()

        self.editor_line_matching_vbox = VBox(
            [
                self.editor_line_matching_vbox_header,
                self.editor_line_matching_vbox_content,
                self.editor_line_matching_vbox_footer,
            ]
        )
        self.editor_line_matching_vbox.layout = no_padding_margin

    def __init__(
        self,
        current_pgdp_page: PGDPPage,
        current_ocr_page: Page,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
        refresh_image_callable: callable = None,
    ):
        self.line_matching_configuration = LineMatching.SHOW_ONLY_MISMATCHES
        self.show_exact_line_matches = False
        self._current_pgdp_page = current_pgdp_page
        self._current_ocr_page = current_ocr_page
        self.init_font(monospace_font_name, monospace_font_path)
        self.init_ui()
        self.refresh_image_callable = refresh_image_callable

    def update_line_matches(self, current_pgdp_page: PGDPPage, current_ocr_page: Page):
        self._current_pgdp_page = current_pgdp_page
        self._current_ocr_page = current_ocr_page
        self.rebuild_content_ui()

    def rebuild_content_ui(self):
        # Clear the current content
        self.editor_line_matching_vbox_content.children = []

        if self._current_ocr_page is None:
            return

        boxes = []
        for line in self._current_ocr_page.lines:
            if (
                line.ground_truth_exact_match
                and self.line_matching_configuration
                == LineMatching.SHOW_ONLY_MISMATCHES
            ):
                # Skip exact matches
                continue
            # Create a new GridBox for each line
            box = self.get_ui_for_line(line)
            boxes.append(box)

        # Add the GridBox to the editor
        self.editor_line_matching_vbox_content.children = boxes

    def get_ui_for_line(self, line: Block):
        # Each Line is a Box Of:
        # <Line Image>
        # OCR Line Text
        # GT Line Text
        # Buttons: <Copy OCR to GT> <Edit All Words> <Delete Line>
        # <Image 1> <Image 2> <Image 3> etc
        # <OCR Word 1> <OCR Word 2> <OCR Word 3> etc
        # <GT Word 1> <GT Word 2> <GT Word 3> etc
        # Buttons for words: <Edit Word> <Delete Word> <Split Word> <Merge Left> <Merge Right>

        GridVBox = VBox()

        LineImageHBox = HBox()
        cropped_line_image_html = get_html_widget_from_cropped_image(
            self._current_ocr_page.cv2_numpy_page_image, line.bounding_box
        )
        LineImageHBox.children = [cropped_line_image_html]
        LineImageHBox.layout = Layout(width="100%")

        linecolor = ""
        if line.ground_truth_exact_match:
            linecolor = "color: lightgray;"

        OcrTextHBox = HBox()
        OcrTextHBox.children = [
            HTML(
                f"<span style='{linecolor} font-family:{self.monospace_font_name}; font-size: 12px;'>{line.text}</span>"
            )
        ]

        GTTextHBox = HBox()

        def get_gt_text_html():
            return [
                HTML(
                    f"<span style='{linecolor} font-family:{self.monospace_font_name}; font-size: 12px;'>{line.ground_truth_text}</span>"
                )
            ]

        GTTextHBox.children = get_gt_text_html()

        # Add buttons for line actions
        # <Copy OCR to GT> <Edit All Words> <Delete Line>
        CopyOCRToGTButton = Button(description="Copy OCR to GT")

        def copy_ocr_to_gt(event=None):
            # Copy the OCR text to the GT text
            for word in line.items:
                word.ground_truth_text = word.text
            GTTextHBox.children = get_gt_text_html()

        CopyOCRToGTButton.on_click(copy_ocr_to_gt)

        EditAllWordsButton = Button(description="Edit All Words")

        def edit_all_words(event=None):
            pass

        EditAllWordsButton.on_click(edit_all_words)

        DeleteLineButton = Button(description="Delete Line")

        def delete_line(event=None):
            # Delete the line from the OCR page
            self._current_ocr_page.remove_line_if_exists(line)
            self._current_ocr_page.remove_empty_items()
            GridVBox.children = []
            GridVBox.layout = Layout(display="none")
            if self.refresh_image_callable:
                self.refresh_image_callable()
            # Refresh the UI
            # self.rebuild_content_ui()

        DeleteLineButton.on_click(delete_line)

        ButtonsHBox = HBox(
            [
                CopyOCRToGTButton,
                EditAllWordsButton,
                DeleteLineButton,
            ]
        )

        layout1 = Layout(
            margin="0px",
            padding="0px",
            width="100%",
            border="1px solid black",
            flex="0",
        )
        LineImageHBox.layout = layout1
        OcrTextHBox.layout = layout1
        GTTextHBox.layout = layout1
        ButtonsHBox.layout = layout1

        GridVBox.children = [
            LineImageHBox,
            OcrTextHBox,
            GTTextHBox,
            ButtonsHBox,
        ]
        GridVBox.layout = Layout(
            margin="0px 0px 5px 5px",
            padding="0px",
            width="96%",
            border="3px solid red",
            flex="0",
        )
        return GridVBox


class IpynbLineEditor:
    """
    UI for editing an individual line of text
    """

    pass


class IpynbLabeler:
    _current_page_idx = 0
    _total_pages = 0

    current_page_name = ""
    go_to_page_idx = 0

    overall_vbox: VBox

    # Header
    prev_button: Button
    next_button: Button
    current_page_idx_display: HTML
    current_page_name_display: HTML
    go_to_page_button: Button
    go_to_page_textbox: BoundedIntText
    header_hbox: HBox

    # Main Section Layout: Image to left, 'Editor' to Right
    main_hbox = HBox

    image_vbox = VBox
    editor_vbox = VBox

    # Left - Image Tabs
    image_tab: Tab
    plain_image_vbox: VBox
    ocr_image_pgh_bounding_box_vbox: VBox
    ocr_image_lines_bounding_box_vbox: VBox
    ocr_image_bounding_box_vbox: VBox
    ocr_image_mismatches_vbox: VBox

    plain_image: Image
    ocr_image_pgh_bounding_box: Image
    ocr_image_lines_bounding_box: Image
    ocr_image_bounding_box: Image
    ocr_image_mismatches: Image

    # Right - Editor Tabs
    editor_tab: Tab
    editor_ocr_text_vbox: VBox
    editor_p3_text_vbox: VBox

    matched_ocr_pages = {}

    monospace_font_name: str
    monospace_font_path: str

    pgdp_export: PGDPExport
    training_set_output_path: pathlib.Path

    page_indexby_name: dict
    page_indexby_nbr: dict

    ocr_models: dict
    main_ocr_predictor: ocr_predictor

    page_editor: IpynbPageEditor

    def init_font(
        self,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
    ):
        self.monospace_font_name = monospace_font_name
        if isinstance(monospace_font_path, str):
            monospace_font_path = pathlib.Path(monospace_font_path)
        self.monospace_font_path = monospace_font_path.resolve()

    def init_header_ui(self):
        self.prev_button = Button(description="Previous")
        self.next_button = Button(description="Next")
        self.current_page_idx_display = HTML("")
        self.current_page_name_display = HTML("")
        self.go_to_page_button = Button(description="Go to Page #")
        self.go_to_page_textbox = BoundedIntText()

        self.header_hbox = HBox(
            [
                self.prev_button,
                self.current_page_idx_display,
                self.current_page_name_display,
                self.next_button,
                self.go_to_page_button,
                self.go_to_page_textbox,
            ]
        )

        self.prev_button.on_click(self.prev_page)
        self.next_button.on_click(self.next_page)
        self.go_to_page_button.on_click(self.go_to_page)

    def init_main_ui(self):
        self.plain_image = Image()
        self.plain_image.width = 400
        self.plain_image_vbox = VBox([self.plain_image])

        self.ocr_image_pgh_bounding_box = Image()
        self.ocr_image_pgh_bounding_box.width = 400
        self.ocr_image_pgh_bounding_box_vbox = VBox([self.ocr_image_pgh_bounding_box])

        self.ocr_image_lines_bounding_box = Image()
        self.ocr_image_lines_bounding_box.width = 400
        self.ocr_image_lines_bounding_box_vbox = VBox(
            [self.ocr_image_lines_bounding_box]
        )

        self.ocr_image_bounding_box = Image()
        self.ocr_image_bounding_box.width = 400
        self.ocr_image_bounding_box_vbox = VBox([self.ocr_image_bounding_box])

        self.ocr_image_mismatches = Image()
        self.ocr_image_mismatches.width = 400
        self.ocr_image_mismatches_vbox = VBox([self.ocr_image_mismatches])

        self.image_tab = Tab(
            [
                self.plain_image_vbox,
                self.ocr_image_pgh_bounding_box_vbox,
                self.ocr_image_lines_bounding_box_vbox,
                self.ocr_image_bounding_box_vbox,
                self.ocr_image_mismatches_vbox,
            ]
        )
        self.image_tab.titles = [
            "Original",
            "Pgh BBoxes",
            "Line BBoxes",
            "Word BBoxes",
            "Mismatches",
        ]

        self.image_vbox = VBox(
            [
                self.image_tab,
            ]
        )

        self.editor_ocr_text_vbox = VBox()
        self.editor_p3_text_vbox = VBox()

        self.editor_mismatched_vbox_text = VBox()

        self.editor_mismatched_vbox_save_button = Button(
            description="Export Page Validations"
        )
        self.editor_mismatched_vbox_save_button.on_click(self.save_validations_button)

        self.editor_mismatched_vbox_buttons = VBox(
            [
                self.editor_mismatched_vbox_save_button,
            ]
        )

        self.editor_mismatched_vbox = VBox(
            [
                self.editor_mismatched_vbox_text,
                self.editor_mismatched_vbox_buttons,
            ]
        )

        self.editor_line_matching_vbox_content = VBox()

        try:
            current_pgdp_page = self.current_pgdp_page
        except KeyError:
            current_pgdp_page = None
        try:
            current_ocr_page = self.current_ocr_page
        except KeyError:
            current_ocr_page = None

        def refresh_image_callable():
            self.current_ocr_page.refresh_page_images()
            self.update_images()

        self.page_editor = IpynbPageEditor(
            current_pgdp_page,
            current_ocr_page,
            self.monospace_font_name,
            self.monospace_font_path,
            refresh_image_callable=refresh_image_callable,
        )

        self.editor_line_matching_vbox = self.page_editor.editor_line_matching_vbox

        self.editor_tab = Tab(
            [
                self.editor_ocr_text_vbox,
                self.editor_p3_text_vbox,
                self.editor_line_matching_vbox,
                self.editor_mismatched_vbox,
            ]
        )
        self.editor_tab.titles = ["OCR", "PGDP P3", "Line Matching", "Mismatches"]

        self.editor_vbox = VBox(
            [
                self.editor_tab,
            ]
        )
        self.editor_tab.Layout = Layout(width="100%", flex="1 1 auto")

        self.main_hbox = HBox(
            [
                self.image_vbox,
                self.editor_vbox,
            ]
        )
        self.main_hbox.layout = Layout(width="100%", flex="1 1 auto")

    def init_footer_ui(self):
        self.reset_ocr_button = Button(description="Reset Page OCR")

        self.footer_hbox = HBox(
            [
                self.reset_ocr_button,
            ]
        )

        def reset_ocr(event=None):
            # Reset the OCR for the current page
            self.run_ocr(force_refresh_ocr=True)
            self.refresh_ui()

        self.reset_ocr_button.on_click(reset_ocr)

    def init_ocr(self):
        # Check if GPU is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using {device} for OCR")

        self.ocr_models = {
            ("db_resnet50", "crnn_vgg16_bn"): ocr_predictor(
                "db_resnet50",
                "crnn_vgg16_bn",
                pretrained=True,
                assume_straight_pages=True,
                disable_crop_orientation=True,
            ).to(device),
        }

        self.main_ocr_predictor = self.ocr_models[("db_resnet50", "crnn_vgg16_bn")]

    def __init__(
        self,
        pgdp_export: PGDPExport,
        training_set_output_path: pathlib.Path | str,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
        start_page_name="",
        start_page_idx=0,
    ):
        self.pgdp_export = pgdp_export

        if isinstance(training_set_output_path, str):
            training_set_output_path = pathlib.Path(training_set_output_path)
        self.training_set_output_path = training_set_output_path
        if not self.training_set_output_path.exists():
            self.training_set_output_path.mkdir(parents=True, exist_ok=True)

        self.page_indexby_name = {
            item.png_file: i for i, item in enumerate(self.pgdp_export.pages)
        }
        self.page_indexby_nbr = {
            i: item.png_file for i, item in enumerate(self.pgdp_export.pages)
        }

        self._total_pages = len(self.pgdp_export.pages) - 1

        if start_page_name:
            new_idx = self.page_indexby_name.get(start_page_name, -1)
            if new_idx > 0 and new_idx < len(self.total_pages):
                self._current_page_idx = start_page_idx
        elif start_page_idx > 0 and start_page_idx < self.total_pages:
            self._current_page_idx = start_page_idx

        self.init_ocr()
        self.init_font(monospace_font_name, monospace_font_path)
        self.init_header_ui()
        self.init_main_ui()
        self.init_footer_ui()

        self.overall_vbox = VBox(
            [
                HTML(f"<style>{self._jupyter_css()}</style>"),
                self.header_hbox,
                self.main_hbox,
                self.footer_hbox,
            ]
        )

        self.refresh_ui()
        self.display()

    @property
    def current_page_idx(self):
        return self._current_page_idx

    @current_page_idx.setter
    def current_page_idx(self, value):
        self._current_page_idx = value
        self.current_page_name = pathlib.Path(self.current_pgdp_page.png_file).stem
        self.refresh_ui()

    @property
    def total_pages(self):
        return self._total_pages

    @total_pages.setter
    def total_pages(self, value):
        self._total_pages = value
        self.go_to_page_textbox.max = value
        self.refresh_ui()

    @property
    def current_pgdp_page(self) -> PGDPPage:
        return self.pgdp_export.pages[self.current_page_idx]

    @property
    def current_ocr_page(self) -> Page:
        return self.matched_ocr_pages[self.current_page_idx]["page"]

    def _jupyter_css(self):
        # Inject custom CSS for the Jupyter environment
        css = f"""
        @font-face {{
            font-family: '{self.monospace_font_name}';
            src: url('{self.monospace_font_path}') format('truetype');
        }}

        input, textarea {{
            font-family: '{self.monospace_font_name}', monospace !important;
            font-size: 12px !important;
        }}
        """
        logger.debug("Custom CSS:\n" + css)
        return css

    def update_header_elements(self):
        self.current_page_idx_display.value = f" #{self.current_page_idx} "
        self.current_page_name_display.value = f" Page: {self.current_page_name} "
        self.go_to_page_textbox.min = 0
        self.go_to_page_textbox.max = self.total_pages
        self.go_to_page_textbox.value = self.current_page_idx

    def update_images(self):
        self.reload_page_images_ui()

        w = self.matched_ocr_pages[self.current_page_idx]["width"]
        h = self.matched_ocr_pages[self.current_page_idx]["height"]
        h = int((w / self.matched_ocr_pages[self.current_page_idx]["width"]) * h)
        w = min(400, w)
        self.plain_image.value = self.matched_ocr_pages[self.current_page_idx][
            "page_image"
        ]
        self.plain_image.width = w
        self.plain_image.height = h

        self.ocr_image_pgh_bounding_box.value = self.matched_ocr_pages[
            self.current_page_idx
        ]["ocr_image_pgh_bounding_box"]
        self.ocr_image_pgh_bounding_box.width = w
        self.ocr_image_pgh_bounding_box.height = h

        self.ocr_image_lines_bounding_box.value = self.matched_ocr_pages[
            self.current_page_idx
        ]["ocr_image_lines_bounding_box"]
        self.ocr_image_lines_bounding_box.width = w
        self.ocr_image_lines_bounding_box.height = h

        self.ocr_image_bounding_box.value = self.matched_ocr_pages[
            self.current_page_idx
        ]["ocr_image_bounding_box"]
        self.ocr_image_bounding_box.width = w
        self.ocr_image_bounding_box.height = h

        self.ocr_image_mismatches.value = self.matched_ocr_pages[self.current_page_idx][
            "ocr_image_mismatches"
        ]
        self.ocr_image_mismatches.width = w
        self.ocr_image_mismatches.height = h

    def update_pgdp_text(self):
        html_lines = [
            f"""
            <tr>
                <td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>{line_idx}</span></td>
                <td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>{line}</span></td>
            </tr>
            """
            for line_idx, line in self.current_pgdp_page.processed_lines
        ]
        html_lines.insert(
            0,
            "<div style='width: 800px; height: 600px; border: 1px solid; overflow: scroll; resize: both'><table>",
        )
        html_lines.append("</div></table>")
        self.editor_p3_text_vbox.children = [
            HTML("\n".join(html_lines)),
        ]

    def update_ocr_text(self):
        logger.debug("Current OCR Text:\n" + self.current_ocr_page.text)
        html_lines = [
            f"""
            <tr>
                <td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>{line_idx}</span></td>
                <td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>{line}</span></td>
            </tr>
            """
            for line_idx, line in enumerate(
                self.current_ocr_page.text.splitlines(keepends=True)
            )
        ]
        html_lines.insert(
            0,
            "<div style='width: 800px; height: 600px; border: 1px solid; overflow: scroll; resize: both'><table>",
        )
        html_lines.append("</div></table>")
        self.editor_ocr_text_vbox.children = [
            HTML("\n".join(html_lines)),
        ]

    def update_line_matches(self):
        pass
        # For each line, display a Grid Layout:

    def get_line_matched_text_image(self, line: Block):
        img = self.current_ocr_page.cv2_numpy_page_image
        h, w = img.shape[:2]
        matches = []
        w: Word
        for _, word in enumerate(line.items):
            gt_text = word.ground_truth_text or ""
            ocr_text = word.text or ""
            logger.debug(f"Word: {ocr_text} | {gt_text}")

            html_widget = get_html_widget_from_cropped_image(img, word.bounding_box)
            matches.append(
                (
                    word.bounding_box.scale(w, h).to_ltrb(),
                    word.ground_truth_text,
                    word.text,
                    html_widget,
                )
            )

    def get_mismatched_text_html_for_line(self, line: Block):
        ocr_line = []
        gt_line = []
        image_line = []
        img = self.current_ocr_page.cv2_numpy_page_image
        h, w = img.shape[:2]
        w: Word
        for _, word in enumerate(line.items):
            gt_text = word.ground_truth_text or ""
            ocr_text = word.text or ""
            logger.debug(f"Word: {ocr_text} | {gt_text}")

            # Get the bounding box of the word
            x1, y1, x2, y2 = word.bounding_box.scale(w, h).to_ltrb()
            # Crop the image to the bounding box
            word_img = img[y1:y2, x1:x2]
            # Encode the cropped image as PNG
            encoded_img = encode_bgr_image_as_png(word_img)
            encoded_string = base64.b64encode(encoded_img).decode("utf-8")
            # logger.debug("Encoded image string: {}".format(encoded_string))
            html = '<img style="height: 14px; padding: 2px; border: 1px solid black;" src="data:image/png;base64,{}"/>'.format(
                encoded_string
            )
            # Append the encoded image to the list
            image_line.append((encoded_img, html))

            if "match_score" not in word.ground_truth_match_keys or (
                word.ground_truth_match_keys["match_score"] == 0 and gt_text == ""
            ):
                gt_text = "&nbsp;" * len(ocr_text)
                ocr_text = f"<span style='color: red;'>{ocr_text}</span>"
            elif word.ground_truth_match_keys["match_score"] == 100:
                gt_text = f"<span style='color: lightgray;'>{gt_text}</span>"
                ocr_text = f"<span style='color: lightgray;'>{ocr_text}</span>"
            else:
                # pad ocr or gt text to be same length
                if len(ocr_text) > len(gt_text):
                    gt_text = gt_text + ("&nbsp;" * (len(ocr_text) - len(gt_text)))
                else:
                    ocr_text = ocr_text + ("&nbsp;" * (len(gt_text) - len(ocr_text)))
                gt_text = f"<span style='color: blue;'>{gt_text}</span>"
                ocr_text = f"<span style='color: blue;'>{ocr_text}</span>"
            ocr_line.append(ocr_text)
            gt_line.append(gt_text)
        # Insert "unmatched" ground truth words
        if line.unmatched_ground_truth_words:
            # Insert unmatched ground truth words in reverse order
            # to avoid messing up the indices of the already inserted words
            # (since we are inserting into the same list)
            for word in reversed(line.unmatched_ground_truth_words):
                # Insert into both arrays at the correct point
                ocr_text = "&nbsp;" * len(word[1])
                ocr_line.insert(word[0] + 1, "&nbsp;" * len(word[1]))
                image_line.insert(word[0] + 1, "&nbsp;" * len(word[1]))
                gt_text = f"<span style='color: red;'>{word[1]}</span>"
                gt_line.insert(word[0] + 1, gt_text)

        return ocr_line, gt_line, image_line

    def get_editor_for_line(self, line: Block):
        pass
        # html = []
        # ipywidgets = []
        # g: GridBox = GridBox(
        #     children=ipywidgets, layout={"grid_template_columns": "auto auto"}
        # )

    def update_mismatched_text(self):
        lines_with_mismatches = []
        for line_idx, line in enumerate(self.current_ocr_page.lines):
            # lines_with_mismatches.append((line_idx, line))
            for w in line.items:
                if (
                    "match_score" not in w.ground_truth_match_keys
                    or w.ground_truth_match_keys["match_score"] != 100
                    or not w.ground_truth_text
                ) and "validated" not in w.ground_truth_match_keys:
                    lines_with_mismatches.append((line_idx, line))
                    break

        html = []
        html.append(
            "<div style='width: 800px; height: 600px; border: 1px solid; overflow: scroll; resize: both'>"
        )

        # <th style='background-color: white'><td>&nbsp;<td></th>
        html_table_start = "<table>"
        html_tr_start = "<tr style='background-color: white'>"
        html_tr_end = "</tr>"
        html_table_end = "</table>"
        td_style = f"style='border: 1px solid gray; font-family:{self.monospace_font_name}; font-size: 12px;'"

        line: Block
        for _, line in lines_with_mismatches:
            ocr_line, gt_line, image_line = self.get_mismatched_text_html_for_line(line)
            image_html = [html for _, html in image_line]

            image_line_str = (
                f"<td {td_style}>" + f"</td><td {td_style}>".join(image_html) + "</td>"
            )
            ocr_line_str = (
                f"<td {td_style}>" + f"</td><td {td_style}>".join(ocr_line) + "</td>"
            )
            gt_line_str = (
                f"<td {td_style}>" + f"</td><td {td_style}>".join(gt_line) + "</td>"
            )

            html.append(html_table_start)

            html.append(html_tr_start)
            html.append(
                f"<td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>BBox</span></td>"
            )
            html.append(f"{image_line_str}")
            html.append(html_tr_end)

            html.append(html_tr_start)
            html.append(
                f"<td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>OCR:</span></td>"
            )
            html.append(f"{ocr_line_str}")
            html.append(html_tr_end)

            html.append(html_tr_start)
            html.append(
                f"<td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>GT:</span></td>"
            )
            html.append(f"{gt_line_str}")

            html.append(html_table_end)

        html.append(html_table_start)
        html.append(html_tr_start)
        html.append("<td>Unmatched GT Lines:</td>")
        for unmatched in self.current_ocr_page.unmatched_ground_truth_lines:
            gt_line_idx = unmatched[0]
            gt_line = unmatched[1]
            gt_line_str = (
                f"<td {td_style}>" + f"</td><td {td_style}>".join(gt_line) + "</td>"
            )
            html.append(html_tr_start)
            html.append(
                f"<td><span style='font-family:{self.monospace_font_name}; font-size: 12px;'>Unmatched line at index {gt_line_idx}</span></td>"
            )
            html.append(f"{gt_line_str}")
            html.append(html_tr_end)
        html.append(html_table_end)

        html.append("</div>")

        self.editor_mismatched_vbox_text.children = [
            HTML("\n".join(html)),
        ]

    def update_text(self):
        self.update_ocr_text()
        self.update_pgdp_text()
        self.page_editor.update_line_matches(
            self.current_pgdp_page, self.current_ocr_page
        )
        # self.update_line_matches()
        # self.update_mismatched_text()

    def refresh_ui(self):
        self.update_header_elements()
        self.run_ocr()
        self.update_images()
        self.update_text()

    def save_validations_button(self, event=None):
        # Save the current page
        prefix = self.pgdp_export.project_id + "_" + str(self.current_page_idx)
        self.current_ocr_page.convert_to_training_set(
            output_path=self.training_set_output_path,
            prefix=prefix,
        )

    # Navigation Buttons
    def prev_page(self, event=None):
        if self.current_page_idx >= 1:
            self.current_page_idx -= 1
            self.refresh_ui()

    def next_page(self, event=None):
        if self.current_page_idx < self.total_pages:
            self.current_page_idx += 1
            self.refresh_ui()

    def go_to_page(self, event=None):
        go_to_page_idx = self.go_to_page_textbox.value
        if go_to_page_idx < self.total_pages and go_to_page_idx >= 0:
            self.current_page_idx = go_to_page_idx
            self.refresh_ui()

    def reload_page_images_ui(self):
        ocr_page: Page = self.matched_ocr_pages[self.current_page_idx]["page"]
        self.matched_ocr_pages[self.current_page_idx] = {
            **self.matched_ocr_pages[self.current_page_idx],
            "width": ocr_page.cv2_numpy_page_image.shape[1],
            "height": ocr_page.cv2_numpy_page_image.shape[0],
            "page_image": encode_bgr_image_as_png(ocr_page.cv2_numpy_page_image),
            "ocr_image_bounding_box": encode_bgr_image_as_png(
                ocr_page.cv2_numpy_page_image_word_with_bboxes
            ),
            "ocr_image_mismatches": encode_bgr_image_as_png(
                ocr_page.cv2_numpy_page_image_matched_word_with_colors
            ),
            "ocr_image_lines_bounding_box": encode_bgr_image_as_png(
                ocr_page.cv2_numpy_page_image_line_with_bboxes
            ),
            "ocr_image_pgh_bounding_box": encode_bgr_image_as_png(
                ocr_page.cv2_numpy_page_image_paragraph_with_bboxes
            ),
        }

    def run_ocr(self, force_refresh_ocr=False):
        """Run OCR or get cached or new matched OCR page and update
        docTR_ocr_cv2_image runs multiple models on the image and returns a list of results.
        """
        if (
            self.current_page_idx not in self.matched_ocr_pages.keys()
            or force_refresh_ocr
        ):
            source_image = self.current_pgdp_page.png_full_path

            doctr_image = DocumentFile.from_images(source_image)
            doctr_result = self.main_ocr_predictor(doctr_image)
            docTR_output = doctr_result.export()

            ocr_doc = Document.from_doctr_output(docTR_output, source_image)
            # Always 1 page per OCR in this case
            ocr_page: Page = ocr_doc.pages[0]
            ocr_page.cv2_numpy_page_image = cv2.imread(source_image)
            ocr_page.refine_bounding_boxes()
            ocr_page.reorganize_page()
            ocr_page.add_ground_truth(self.current_pgdp_page.processed_page_text)

            self.matched_ocr_pages[self.current_page_idx] = {
                "page": ocr_page,
            }

    def display(self):
        # Inject custom CSS for the Jupyter environment monospacing the fonts
        display(self.overall_vbox)
