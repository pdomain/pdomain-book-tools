import pathlib
from enum import Enum
from logging import getLogger

from ipywidgets import HTML, Button, HBox
from ipywidgets import Image as ipywidgets_Image  # GridBox,
from ipywidgets import Layout, VBox

from pd_book_tools.utility.ipynb_widgets import (
    get_formatted_text_html_span,
    get_html_string_from_image_src,
    get_html_widget_from_cropped_image,
)

from ..ocr.block import Block
from ..ocr.image_utilities import get_cropped_word_image
from ..ocr.page import Page
from ..ocr.word import Word
from .pgdp_results import PGDPPage

# Configure logging
logger = getLogger(__name__)
ui_logger = getLogger(__name__ + ".UI")


class EditorTaskType(Enum):
    NONE = 0
    SPLIT = 1
    EDITBBOX = 2


class IpynbLineEditor:
    """
    UI editing a single line
    """

    _current_pgdp_page: PGDPPage
    _current_ocr_page: Page
    _current_ocr_line: Block
    line_matches: list[dict]
    page_change_callback: callable

    monospace_font_name: str

    GridVBox: VBox
    line_image: ipywidgets_Image
    LineImageHBox: HBox
    OcrLineTextHBox: HBox
    GTLineTextHBox: HBox
    LineActionButtonsHBox: HBox
    WordMatchingTableHBox: HBox
    WordMatchingTableVBoxes: list[VBox]
    TaskHBox: HBox

    task_type: EditorTaskType = EditorTaskType.NONE
    split_task_match_idx: int = -1

    basic_box_layout = Layout(
        margin="0px",
        padding="0px",
        width="100%",
        border="1px solid black",
        flex="0",
    )

    overall_layout = Layout(
        margin="0px 0px 5px 5px",
        padding="0px",
        width="98%",
        border="3px solid red",
        flex="0",
    )

    def init_font(
        self,
        monospace_font_name: str,
        monospace_font_path: pathlib.Path | str,
    ):
        self.monospace_font_name = monospace_font_name
        if isinstance(monospace_font_path, str):
            monospace_font_path = pathlib.Path(monospace_font_path)
        self.monospace_font_path = monospace_font_path.resolve()

    def __init__(
        self,
        page: Page,
        pgdp_page: PGDPPage,
        line: Block,
        page_change_callback: callable = None,
    ):
        self.GridVBox = VBox()
        self.GridVBox.children = []
        self.GridVBox.layout = self.overall_layout

        self._current_ocr_page = page
        self._current_pgdp_page = pgdp_page
        self._current_ocr_line = line
        self.line_matches = []
        self.page_change_callback = page_change_callback

        self.redraw_ui()

    def redraw_ui(self):
        self.calculate_line_matches()

        self.draw_ui_fullline_image_hbox()
        self.draw_ui_fullline_ocr_text_hbox()
        self.draw_ui_fullline_gt_text_hbox()
        self.draw_ui_line_actions_hbox()
        self.draw_ui_word_matching_table()
        self.draw_ui_active_task()

        self.rebuild_gridbox_children()

    def rebuild_gridbox_children(self):
        # Rebuild the GridVBox children
        self.GridVBox.children = []
        self.GridVBox.children = [
            self.LineImageHBox,
            self.OcrLineTextHBox,
            self.GTLineTextHBox,
            self.LineActionButtonsHBox,
            self.WordMatchingTableHBox,
            self.TaskHBox,
        ]

    def draw_ui_fullline_image_hbox(self):
        self.LineImageHBox = HBox()
        self.LineImageHBox.layout = self.basic_box_layout
        cropped_line_image_html = get_html_widget_from_cropped_image(
            self._current_ocr_page.cv2_numpy_page_image,
            self._current_ocr_line.bounding_box,
        )
        self.LineImageHBox.children = [cropped_line_image_html]

    def draw_ui_fullline_ocr_text_hbox(self):
        self.OcrLineTextHBox = HBox()
        self.OcrLineTextHBox.layout = self.basic_box_layout
        if self._current_ocr_line.ground_truth_exact_match:
            linecolor_css = "lightgray"
        else:
            linecolor_css = "unset"

        self.OcrLineTextHBox.children = [
            get_formatted_text_html_span(
                linecolor_css=linecolor_css, text=self._current_ocr_line.text
            )
        ]

    def draw_ui_fullline_gt_text_hbox(self):
        self.GTLineTextHBox = HBox()
        self.GTLineTextHBox.layout = self.basic_box_layout
        if self._current_ocr_line.ground_truth_exact_match:
            linecolor_css = "lightgray"
        else:
            linecolor_css = "unset"

        self.GTLineTextHBox.children = [
            get_formatted_text_html_span(
                linecolor_css=linecolor_css,
                text=self._current_ocr_line.ground_truth_text,
            )
        ]

    def draw_ui_line_actions_hbox(self):
        CopyOCRToGTButton = Button(description="Copy Line to GT")
        CopyOCRToGTButton.on_click(self.copy_ocr_to_gt)

        DeleteLineButton = Button(description="Copy Line to GT")
        DeleteLineButton.on_click(self.delete_line)

        self.LineActionButtonsHBox = HBox()
        self.LineActionButtonsHBox.layout = self.basic_box_layout
        self.LineActionButtonsHBox.children = [
            CopyOCRToGTButton,
            DeleteLineButton,
        ]

    def draw_ui_active_task(self):
        # TODO
        pass

    def create_ui_word_match_widgets(self):
        match_VBox = VBox()

        image_HBox = HBox()
        ocr_HBox = HBox()
        gt_HBox = HBox()
        action_buttons_HBox = HBox()

        match_VBox.children = [
            image_HBox,
            ocr_HBox,
            gt_HBox,
            action_buttons_HBox,
        ]

        self.WordMatchingTableVBoxes.append(match_VBox)

    def load_word_match_image(self, match):
        image_HBox = self.WordMatchingTableVBoxes[match["idx"]].children[0]
        image_HBox.children = [
            HTML(match["img_tag_text"]),
        ]

    def load_word_match_text(self, match):
        # Set the word match text
        ocr_HBox = self.WordMatchingTableVBoxes[match["idx"]].children[1]
        gt_HBox = self.WordMatchingTableVBoxes[match["idx"]].children[2]

        ocr_HBox.children = [
            get_formatted_text_html_span(
                linecolor_css=match["ocr_text_color"],
                text=match["ocr_text"],
            )
        ]
        # TODO make this a editable text box
        gt_HBox.children = [
            get_formatted_text_html_span(
                linecolor_css=match["gt_text_color"],
                text=match["gt_text"],
            )
        ]

    def load_word_action_buttons(self, match):
        action_buttons_HBox = self.WordMatchingTableVBoxes[match["idx"]].children[3]
        action_buttons_HBox.children = []

        if self.task_type != EditorTaskType.NONE:
            # If an editor task is active, don't display action buttons
            return

        delete_button = Button(
            description="X",
            layout=Layout(width="16px", padding="0px", margin="0px"),
        )
        action_buttons_HBox.children.append(delete_button)
        # TODO add delete match action
        # delete_button.on_click(lambda _: self.delete_match(match))

        word = match["word"]
        if word:
            if not word.ground_truth_exact_match:
                if match["word_idx"] > 0:
                    ml_button = Button(
                        description="ML",
                        layout=Layout(width="22px", padding="0px", margin="0px"),
                    )
                    ml_button.on_click(lambda _: self.merge_left(match))
                    action_buttons_HBox.children.append(ml_button)

                if match["word_idx"] < len(self._current_ocr_line.items) - 1:
                    mr_button = Button(
                        description="MR",
                        layout=Layout(width="22px", padding="0px", margin="0px"),
                    )
                    mr_button.on_click(lambda _: self.merge_right(match))
                    action_buttons_HBox.children.append(mr_button)

            edit_bbox_button = Button(
                description="EB",
                layout=Layout(width="22px", padding="0px", margin="0px"),
            )
            # TODO add edit bbox action
            # edit_bbox_button.on_click(lambda _: self.start_edit_bbox_task(match))
            action_buttons_HBox.children.append(edit_bbox_button)

            split_button = Button(
                description="SP",
                layout=Layout(width="22px", padding="0px", margin="0px"),
            )
            # TODO add split action
            # split_button.on_click(lambda _: self.start_split_task(match))
            action_buttons_HBox.children.append(split_button)

    def load_word_match_widgets(self, match):
        self.load_word_match_image(match)
        self.load_word_match_text(match)
        self.load_word_action_buttons(match)

    def draw_ui_word_matching_table(self):
        self.WordMatchingTableHBox = HBox()
        self.WordMatchingTableVBoxes = []

        for match in self.line_matches:
            self.create_ui_word_match_widgets()
            self.load_word_match_widgets(match)

        self.WordMatchingTableHBox.children = [
            match_vbox for match_vbox in self.WordMatchingTableVBoxes
        ]

    ####################################################################
    # ACTIONS
    ####################################################################

    def copy_ocr_to_gt(self, event=None):
        # Copy all of the the OCR text into the GT text
        word: Word
        for word in self._current_ocr_line.items:
            word.ground_truth_text = word.text

        # Redraw the UI after update
        self.redraw_ui()

    def delete_line(self, event=None):
        # Delete the line from the OCR page
        self._current_ocr_page.remove_line_if_exists(self._current_ocr_line)
        self._current_ocr_page.remove_empty_items()
        self.GridVBox.children = []
        self.GridVBox.layout = Layout(display="none")
        if self.page_change_callback:
            self.page_change_callback()

    def merge_left(self, match):
        word: Word = match["word"]
        word_idx = match["word_idx"]
        # Merge the word with the previous word
        if word_idx > 0:
            prev_word: Word = self._current_ocr_line.items[word_idx - 1]
            prev_word.merge(word)
            self._current_ocr_line.remove_item(word)
            self.redraw_ui()
            if self.page_change_callback:
                self.page_change_callback()

    def merge_right(self, match):
        word: Word = match["word"]
        word_idx = match["word_idx"]
        # Merge the word with the next word
        if word_idx < len(self._current_ocr_line.items) - 1:
            next_word: Word = self._current_ocr_line.items[word_idx + 1]
            word.merge(next_word)
            self._current_ocr_line.remove_item(next_word)
            self.redraw_ui()
            if self.page_change_callback:
                self.page_change_callback()

    def calculate_line_matches(self):
        matches = []

        logger.debug(
            f"Calculating match components for line: {self._current_ocr_line.text[0:20]}..."
        )

        word: Word
        for word_idx, word in enumerate(self._current_ocr_line.items):
            gt_text = word.ground_truth_text or ""
            ocr_text = word.text or ""
            logger.debug(f"Word: {ocr_text} | {gt_text}")

            ocr_text_color = "lightgray"
            gt_text_color = "lightgray"

            img_ndarray, _, _, data_src_string = get_cropped_word_image(
                img=self._current_ocr_page.cv2_numpy_page_image,
                bounding_box=word.bounding_box,
            )

            # Encode the cropped image as PNG and get a <img> tag string
            img_tag_text = get_html_string_from_image_src(
                data_src_string=data_src_string
            )

            if "match_score" not in word.ground_truth_match_keys or (
                word.ground_truth_match_keys["match_score"] == 0 and gt_text == ""
            ):
                ocr_text_color = "red"
            else:
                ocr_text_color = "blue"
                gt_text_color = "blue"

            match = {
                "word_idx": word_idx,
                "word": word,
                "img_ndarray": img_ndarray,
                "img_tag_text": img_tag_text,
                "ocr_text": ocr_text,
                "gt_text": gt_text,
                "ocr_text_color": ocr_text_color,
                "gt_text_color": gt_text_color,
            }

            matches.append(match)

        # Insert "unmatched" ground truth words
        if self._current_ocr_line.unmatched_ground_truth_words:
            # Insert unmatched ground truth words in reverse order
            # to avoid messing up the indices of the already inserted words
            # (since we are inserting into the same list)
            for unmatched_words in reversed(
                self._current_ocr_line.unmatched_ground_truth_words
            ):
                unmatched_gt_word_idx = unmatched_words[0]
                unmatched_gt_word = unmatched_words[1]

                match = {
                    "word_idx": unmatched_gt_word_idx + 1,
                    "word": None,
                    "img_ndarray": None,
                    "img_tag_text": None,
                    "ocr_text": "",
                    "gt_text": unmatched_gt_word,
                    "ocr_text_color": "red",
                    "gt_text_color": "red",
                }

                matches.insert(unmatched_gt_word_idx + 1, match)

        # add an indexer to matches
        for idx, match in enumerate(matches):
            match["idx"] = idx

        self.line_matches = matches
