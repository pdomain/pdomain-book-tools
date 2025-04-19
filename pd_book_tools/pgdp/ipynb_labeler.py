import base64
import pathlib
from logging import getLogger

import cv2
import numpy as np
import torch
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from IPython.display import display
from ipywidgets import HTML, BoundedIntText, Button, HBox, Image, Tab, VBox

from pd_book_tools.ocr.block import Block
from pd_book_tools.ocr.word import Word

from ..ocr.document import Document
from ..ocr.page import Page
from .pgdp_results import PGDPExport, PGDPPage

# Configure logging
logger = getLogger(__name__)


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

    page_indexby_name: dict
    page_indexby_nbr: dict

    ocr_models: dict
    main_ocr_predictor: ocr_predictor

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

        self.editor_mismatched_vbox_save_button = Button(description="Save Validations")
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

        self.editor_tab = Tab(
            [
                self.editor_ocr_text_vbox,
                self.editor_p3_text_vbox,
                self.editor_mismatched_vbox,
            ]
        )
        self.editor_tab.titles = ["OCR", "PGDP P3", "Mismatches"]

        self.editor_vbox = VBox(
            [
                self.editor_tab,
            ]
        )

        self.main_hbox = HBox(
            [
                self.image_vbox,
                self.editor_vbox,
            ]
        )

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
        source_path: pathlib.Path,
        output_path: pathlib.Path,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
        start_page_name="",
        start_page_idx=0,
    ):
        self.pgdp_export = pgdp_export
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

    @classmethod
    def _encode_bgr_image_as_png(cls, bgr_image: np.ndarray):
        """Encodes a BGR image as a PNG buffer."""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode(".png", rgb_image)
        return buffer

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
            encoded_img = self._encode_bgr_image_as_png(word_img)
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
                image_line.insert(word[0] + 1, (None, "&nbsp;" * len(word[1])))
                gt_text = f"<span style='color: red;'>{word[1]}</span>"
                gt_line.insert(word[0] + 1, gt_text)

        return ocr_line, gt_line, image_line

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
        self.update_mismatched_text()
        # self.editor_ocr_text_vbox.children = []

        # words: list[list[Word]] = [line.items for line in self.current_ocr_page.lines]

        # poor_match_lines = []

        # for word_list in words:
        #     poor_match_words = []
        #     for word in word_list:
        #         if "match_score" not in word.ground_truth_match_keys:
        #             poor_match_words.append(word)
        #             continue
        #         if word.ground_truth_match_keys["match_score"] != 100:
        #             poor_match_words.append(word)
        #     poor_match_lines.append(poor_match_words)

        # self.editor_ocr_text_vbox.children = [
        #     HTML(
        #         f"<div style='font-family:{self.monospace_font_name}; font-size: 12px;'>OCR: {word.text} | GT: {word.ground_truth_text}</div>"
        #     )
        #     for line in poor_match_lines
        #     for word in line
        # ]

    def refresh_ui(self):
        self.update_header_elements()
        self.run_ocr()
        self.update_images()
        self.update_text()

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
                "width": ocr_page.cv2_numpy_page_image.shape[1],
                "height": ocr_page.cv2_numpy_page_image.shape[0],
                "page_image": self._encode_bgr_image_as_png(
                    ocr_page.cv2_numpy_page_image
                ),
                "ocr_image_bounding_box": self._encode_bgr_image_as_png(
                    ocr_page.cv2_numpy_page_image_word_with_bboxes
                ),
                "ocr_image_mismatches": self._encode_bgr_image_as_png(
                    ocr_page.cv2_numpy_page_image_matched_word_with_colors
                ),
                "ocr_image_lines_bounding_box": self._encode_bgr_image_as_png(
                    ocr_page.cv2_numpy_page_image_line_with_bboxes
                ),
                "ocr_image_pgh_bounding_box": self._encode_bgr_image_as_png(
                    ocr_page.cv2_numpy_page_image_paragraph_with_bboxes
                ),
            }

    def display(self):
        # Inject custom CSS for the Jupyter environment monospacing the fonts
        display(self.overall_vbox)
