import json
import pathlib

import regex


def remove_blank_page(text):
    return regex.sub(r"\[Blank Page\]", "", text, flags=regex.DOTALL)


def remove_proofer_notes(text):
    return regex.sub(r"\[\*.*?\]", "", text, flags=regex.DOTALL)


def fix_pgdp_dashes(text):
    text = regex.sub(r"----", "⸺", text, flags=regex.DOTALL)
    text = regex.sub(r"--", "—", text, flags=regex.DOTALL)
    return text


def convert_straight_to_curly_quotes(text):  # Convert double quotes first
    text = regex.sub(r'(?<!\w)"(?=\w)', "“", text)  # Opening double quote
    text = regex.sub(r'"', "”", text)  # Closing double quote

    # Convert single quotes
    text = regex.sub(r"(?<=\s|^)'(?=\w)", "‘", text)  # Opening single quote
    text = regex.sub(
        r"(?<=\w)'(?=\s|$|[.,!?;:)]|\Z)", "’", text
    )  # Closing single quote

    # Handle apostrophes in contractions and possessives
    text = regex.sub(
        r"(?<=\w)'(?=\w)", "’", text
    )  # In the middle of words (e.g., don't → don’t)

    return text


def split_hyphen_asterisk(text):
    return regex.sub(r"-\*(\S+)\n(\S+)", r"-\n\1 \2", text)


def remove_leading_trailing_asterisk(text):
    text = text.strip()
    if text[0:1] == "*":
        text = text[1:]
    if text[-2:] == "-*":
        text = text[:-1]
    return text


def fix_footnotes(text):
    text = regex.sub(r"\[(\d+)\]", r" \1", text)
    return text


def fix_pgdp_diacritics(text):
    text = regex.sub(r"\[=A\]", "Ā", text)
    text = regex.sub(r"\[=E\]", "Ē", text)
    text = regex.sub(r"\[=I\]", "Ī", text)
    text = regex.sub(r"\[=O\]", "Ō", text)
    text = regex.sub(r"\[=U\]", "Ū", text)
    text = regex.sub(r"\[=a\]", "ā", text)
    text = regex.sub(r"\[=e\]", "ē", text)
    text = regex.sub(r"\[=i\]", "ī", text)
    text = regex.sub(r"\[=o\]", "ō", text)
    text = regex.sub(r"\[=u\]", "ū", text)

    text = regex.sub(r"\[:A\]", "Ä", text)
    text = regex.sub(r"\[:E\]", "Ë", text)
    text = regex.sub(r"\[:I\]", "Ï", text)
    text = regex.sub(r"\[:O\]", "Ö", text)
    text = regex.sub(r"\[:U\]", "Ü", text)
    text = regex.sub(r"\[:a\]", "ä", text)
    text = regex.sub(r"\[:e\]", "ë", text)
    text = regex.sub(r"\[:i\]", "ï", text)
    text = regex.sub(r"\[:o\]", "ö", text)
    text = regex.sub(r"\[:u\]", "ü", text)

    text = regex.sub(r"\[.A\]", "Ȧ", text)
    text = regex.sub(r"\[.E\]", "Ė", text)
    text = regex.sub(r"\[.I\]", "İ", text)
    text = regex.sub(r"\[.O\]", "Ȯ", text)
    text = regex.sub(r"\[.C\]", "Ċ", text)
    text = regex.sub(r"\[.G\]", "Ġ", text)
    text = regex.sub(r"\[.Z\]", "Ż", text)
    text = regex.sub(r"\[.a\]", "ȧ", text)
    text = regex.sub(r"\[.e\]", "ė", text)
    text = regex.sub(r"\[.o\]", "ȯ", text)
    text = regex.sub(r"\[.c\]", "ċ", text)
    text = regex.sub(r"\[.g\]", "ġ", text)
    text = regex.sub(r"\[.z\]", "ż", text)

    text = regex.sub(r"\[`A\]", "À", text)
    text = regex.sub(r"\[`E\]", "È", text)
    text = regex.sub(r"\[`I\]", "Ì", text)
    text = regex.sub(r"\[`O\]", "Ò", text)
    text = regex.sub(r"\[`U\]", "Ù", text)
    text = regex.sub(r"\['N\]", "Ǹ", text)
    text = regex.sub(r"\[`a\]", "à", text)
    text = regex.sub(r"\[`e\]", "è", text)
    text = regex.sub(r"\[`i\]", "ì", text)
    text = regex.sub(r"\[`o\]", "ò", text)
    text = regex.sub(r"\[`u\]", "ù", text)
    text = regex.sub(r"\['n\]", "ǹ", text)

    text = regex.sub(r"\['A\]", "Á", text)
    text = regex.sub(r"\['E\]", "É", text)
    text = regex.sub(r"\['I\]", "Í", text)
    text = regex.sub(r"\['O\]", "Ó", text)
    text = regex.sub(r"\['U\]", "Ú", text)
    text = regex.sub(r"\['Y\]", "Ý", text)
    text = regex.sub(r"\['a\]", "á", text)
    text = regex.sub(r"\['e\]", "é", text)
    text = regex.sub(r"\['i\]", "í", text)
    text = regex.sub(r"\['o\]", "ó", text)
    text = regex.sub(r"\['u\]", "ú", text)
    text = regex.sub(r"\['y\]", "ý", text)

    text = regex.sub(r"\[\)A\]", "Ă", text)
    text = regex.sub(r"\[\)E\]", "Ĕ", text)
    text = regex.sub(r"\[\)I\]", "Ĭ", text)
    text = regex.sub(r"\[\)O\]", "Ŏ", text)
    text = regex.sub(r"\[\)U\]", "Ŭ", text)
    text = regex.sub(r"\[\)a\]", "ă", text)
    text = regex.sub(r"\[\)e\]", "ĕ", text)
    text = regex.sub(r"\[\)i\]", "ĭ", text)
    text = regex.sub(r"\[\)o\]", "ŏ", text)
    text = regex.sub(r"\[\)u\]", "ŭ", text)

    text = regex.sub(r"\[c,\]", "ç", text)
    return text


class PGDPPage:
    png_file: str
    png_full_path: pathlib.Path
    original_page_text: str
    original_lines: list
    processed_page_text: str
    processed_lines: list
    processed_words: list

    def __init__(self, png_file: str, page_text: str):
        self.png_file = png_file
        self.original_page_text = page_text
        self.original_lines = page_text.splitlines()
        self.process()

    def process(self):
        text = self.original_page_text
        text = text.replace(
            "\r\n", "\n"
        )  # Convert Windows-style line breaks to Unix-style
        text = remove_proofer_notes(text)
        text = remove_blank_page(text)
        text = fix_pgdp_diacritics(text)
        text = fix_footnotes(text)
        text = split_hyphen_asterisk(text)
        text = fix_pgdp_dashes(text)
        text = remove_leading_trailing_asterisk(text)
        text = convert_straight_to_curly_quotes(text)

        self.processed_page_text = text

        self.processed_lines = [
            (line_idx, line) for line_idx, line in enumerate(text.splitlines())
        ]

        self.processed_words = [
            (line_nbr, word_nbr, word)
            for line_nbr, line in self.processed_lines
            for word_nbr, word in enumerate(line.split())
        ]
        return self


class PGDPExport:
    pages: list[PGDPPage]

    def __init__(self, pages: list[PGDPPage]):
        self.pages = pages

    @classmethod
    def from_json_file(cls, input_file_path: pathlib.Path | str):
        if isinstance(input_file_path, str):
            input_file_path = pathlib.Path(input_file_path)
        if not input_file_path.exists():
            raise FileNotFoundError(f"File not found: {input_file_path}")
        if not input_file_path.is_file():
            raise FileNotFoundError(f"Not a file: {input_file_path}")
        with open(input_file_path.resolve(), "r", encoding="utf-8") as json_file:
            return cls.from_json(json_file.read(), input_file_path.parent)

    @classmethod
    def from_json(cls, json_str: str, path_prefix: pathlib.Path | str):
        pages = json.loads(json_str)
        new_pages = []
        for png_file, page_text in pages.items():
            if isinstance(path_prefix, str):
                path_prefix = pathlib.Path(path_prefix)
            png_full_file_path = pathlib.Path(path_prefix, png_file)
            new_pages.append(PGDPPage(png_full_file_path, page_text))
        return cls(new_pages)
